#!/usr/bin/env python3
"""
Entity Grounding Service (New Workflow)

- Uses LLM (BAML) to extract and standardize concepts from text.
- Fuzzy searches SNOMED CT database directly for best matching concept.
- Extracts taxonomy path to configured root concepts and maps to T-Box labels.
"""

import json
import os
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Dict, List, Optional, Tuple

import click
import yaml

from cardio_graph.extraction_utils.clients import create_client_registry
from cardio_graph.snomedct_utils.snomed_query import SnomedExplorer

IS_A_TYPE_ID = 116680003
DEFAULT_CONFIG_PATH = os.path.join(
    os.path.dirname(__file__), "../snomedct_utils/guideline_graph_schema.yaml"
)
DEFAULT_INDEX_PATH = "/prj/doctoral_letters/guide/data/grounding_index.json"


@dataclass
class ExtractedConcept:
    entity_original: str
    entity_standardized_candidate: str
    role: str
    logic: str
    logic_structured: Dict[str, str]


@dataclass
class GroundedConcept:
    entity_original: str
    entity_standardized_candidate: str
    role: str
    logic: str
    logic_structured: Dict[str, str]
    snomed_id: Optional[int]
    preferred_term: Optional[str]
    score: float
    taxonomy_path: List[Dict[str, str]]
    target_label: Optional[str]


class ConceptIndex:
    def __init__(self, index_path: str = DEFAULT_INDEX_PATH):
        self.index_path = index_path
        self.by_snomed_id: Dict[str, Dict] = {}
        self.by_standardized: Dict[str, Dict] = {}
        self._load()

    def _normalize(self, text: str) -> str:
        return " ".join(text.lower().strip().split())

    def _load(self) -> None:
        if not self.index_path or not os.path.exists(self.index_path):
            return
        try:
            with open(self.index_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.by_snomed_id = data.get("by_snomed_id", {})
            self.by_standardized = data.get("by_standardized", {})
        except Exception:
            self.by_snomed_id = {}
            self.by_standardized = {}

    def save(self) -> None:
        if not self.index_path:
            return
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        data = {
            "by_snomed_id": self.by_snomed_id,
            "by_standardized": self.by_standardized,
        }
        with open(self.index_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def lookup(self, standardized_name: str) -> Optional[Dict]:
        key = self._normalize(standardized_name)
        return self.by_standardized.get(key)

    def add(self, entry: Dict) -> None:
        snomed_id = entry.get("snomed_id")
        standardized = entry.get("entity_standardized_candidate")
        if snomed_id is not None:
            self.by_snomed_id[str(snomed_id)] = entry
        if standardized:
            self.by_standardized[self._normalize(standardized)] = entry


class EntityGroundingServiceNew:
    def __init__(
        self,
        config_path: str = DEFAULT_CONFIG_PATH,
        model: str = "Qwen8b",
        node: str = "g4",
        port: Optional[int] = None,
        index_path: str = DEFAULT_INDEX_PATH,
    ):
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found at: {config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

        self.mapping_rules = self.config.get("snomed_mapping", {}).get(
            "mapping_rules", []
        )
        self.root_concepts = self._collect_root_concepts(self.mapping_rules)

        self.client_registry = create_client_registry(model, node, port)

        self.snomed_explorer = SnomedExplorer()
        self.snomed_explorer.connect()

        self._preferred_term_cache: Dict[int, str] = {}
        self.index = ConceptIndex(index_path=index_path)

    def _collect_root_concepts(self, mapping_rules: List[Dict]) -> List[int]:
        roots = []
        for rule in mapping_rules:
            for root in rule.get("root_concepts", []) or []:
                try:
                    roots.append(int(root))
                except (TypeError, ValueError):
                    continue
        return list(sorted(set(roots)))

    def _normalize(self, text: str) -> str:
        return " ".join(text.lower().strip().split())

    def _score(self, query: str, candidate: str) -> float:
        q = self._normalize(query)
        c = self._normalize(candidate)
        if not q or not c:
            return 0.0
        if q == c:
            return 1.0
        return SequenceMatcher(None, q, c).ratio()

    def _get_preferred_term(self, concept_id: int) -> Optional[str]:
        if concept_id in self._preferred_term_cache:
            return self._preferred_term_cache[concept_id]
        term = self.snomed_explorer.get_preferred_term(concept_id)
        if term:
            self._preferred_term_cache[concept_id] = term
        return term

    def _search_best_concept(
        self, term: str, limit: int = 100
    ) -> Tuple[Optional[int], Optional[str], float]:
        if not term:
            return None, None, 0.0

        search_terms = [term]
        tokens = [t for t in self._normalize(term).split() if len(t) > 2]
        search_terms.extend(tokens)

        results = []
        seen = set()
        for t in search_terms:
            if t in seen:
                continue
            seen.add(t)
            results.extend(self.snomed_explorer.search_concepts_by_term(t, limit=limit))

        if not results:
            return None, None, 0.0

        concept_terms: Dict[int, List[str]] = {}
        for r in results:
            concept_id = r.get("conceptid") or r.get("conceptId")
            term_value = r.get("term") or ""
            if concept_id is None:
                continue
            try:
                concept_id = int(concept_id)
            except (TypeError, ValueError):
                continue
            concept_terms.setdefault(concept_id, []).append(term_value)

        best_id = None
        best_term = None
        best_score = 0.0

        for concept_id, terms in concept_terms.items():
            preferred = self._get_preferred_term(concept_id)
            candidates = list(terms)
            if preferred:
                candidates.append(preferred)

            score = 0.0
            best_candidate_term = None
            for candidate in candidates:
                candidate_score = self._score(term, candidate)
                if candidate_score > score:
                    score = candidate_score
                    best_candidate_term = candidate

            if score > best_score:
                best_score = score
                best_id = concept_id
                best_term = preferred or best_candidate_term

        return best_id, best_term, best_score

    def _get_parents(self, concept_id: int) -> List[int]:
        relationships = self.snomed_explorer.get_relationships(concept_id)
        parents = []
        for rel in relationships:
            rel_type = rel.get("typeid") or rel.get("typeId")
            dest_id = rel.get("destinationid") or rel.get("destinationId")
            if rel_type == IS_A_TYPE_ID and dest_id is not None:
                try:
                    parents.append(int(dest_id))
                except (TypeError, ValueError):
                    continue
        return parents

    def _extract_taxonomy_path(self, concept_id: int) -> List[int]:
        if concept_id is None:
            return []

        target_roots = set(self.root_concepts)
        visited = set([concept_id])
        queue: List[Tuple[int, List[int]]] = [(concept_id, [concept_id])]
        best_path: List[int] = [concept_id]

        while queue:
            current, path = queue.pop(0)
            if current in target_roots:
                return path

            if len(path) > len(best_path):
                best_path = path

            parents = self._get_parents(current)
            if not parents and len(path) > len(best_path):
                best_path = path

            for parent in parents:
                if parent in visited:
                    continue
                visited.add(parent)
                queue.append((parent, path + [parent]))

        return best_path

    def _resolve_target_label(self, path_ids: List[int]) -> Optional[str]:
        if not path_ids:
            return None
        path_set = set(path_ids)
        for rule in self.mapping_rules:
            roots = set()
            for root in rule.get("root_concepts", []) or []:
                try:
                    roots.add(int(root))
                except (TypeError, ValueError):
                    continue
            if roots & path_set:
                return rule.get("target_label")
        return None

    def _format_taxonomy_path(self, path_ids: List[int]) -> List[Dict[str, str]]:
        formatted = []
        for cid in path_ids:
            term = self._get_preferred_term(cid) or str(cid)
            formatted.append({"concept_id": str(cid), "term": term})
        return formatted

    def extract_concepts(
        self, sentence: str, source_type: str, guideline_title: str
    ) -> List[ExtractedConcept]:
        from cardio_graph.baml_client.sync_client import b

        baml_options = {"client_registry": self.client_registry}
        tagged_text = (
            f"[GUIDELINE: {guideline_title}] "
            f"[SOURCE_TYPE: {source_type}]\n{sentence}"
        )
        result = b.ExtractConcepts(tagged_text, baml_options=baml_options)

        concepts = []
        for concept in result.concepts or []:
            logic_structured = {
                "strength": "Unknown",
                "class": "Unknown",
                "level": "Unknown",
                "direction": "UNKNOWN",
            }
            if getattr(concept, "logic_structured", None):
                logic_structured.update(concept.logic_structured.model_dump())
            concepts.append(
                ExtractedConcept(
                    entity_original=concept.entity_original,
                    entity_standardized_candidate=concept.entity_standardized_candidate,
                    role=concept.role,
                    logic=concept.logic,
                    logic_structured=logic_structured,
                )
            )
        return concepts

    def ground_sentence(
        self, sentence: str, source_type: str, guideline_title: str
    ) -> List[GroundedConcept]:
        extracted = self.extract_concepts(sentence, source_type, guideline_title)
        grounded: List[GroundedConcept] = []

        for concept in extracted:
            cached = self.index.lookup(concept.entity_standardized_candidate)
            if cached:
                if cached.get("logic_structured") is None:
                    cached["logic_structured"] = concept.logic_structured
                self.index.add(cached)
                grounded.append(
                    GroundedConcept(
                        entity_original=concept.entity_original,
                        entity_standardized_candidate=concept.entity_standardized_candidate,
                        role=concept.role,
                        logic=concept.logic,
                        logic_structured=concept.logic_structured,
                        snomed_id=cached.get("snomed_id"),
                        preferred_term=cached.get("preferred_term"),
                        score=cached.get("score", 1.0),
                        taxonomy_path=cached.get("taxonomy_path", []),
                        target_label=cached.get("target_label"),
                    )
                )
                continue
            concept_id, preferred_term, score = self._search_best_concept(
                concept.entity_standardized_candidate
            )
            path_ids = self._extract_taxonomy_path(concept_id)
            target_label = self._resolve_target_label(path_ids)
            if target_label is None and concept.role:
                target_label = self._resolve_target_label_for_role(
                    concept.role, path_ids
                )
            taxonomy_path = self._format_taxonomy_path(path_ids)

            grounded_concept = GroundedConcept(
                entity_original=concept.entity_original,
                entity_standardized_candidate=concept.entity_standardized_candidate,
                role=concept.role,
                logic=concept.logic,
                logic_structured=concept.logic_structured,
                snomed_id=concept_id,
                preferred_term=preferred_term,
                score=score,
                taxonomy_path=taxonomy_path,
                target_label=target_label,
            )
            grounded.append(grounded_concept)

            self.index.add(
                {
                    "entity_standardized_candidate": concept.entity_standardized_candidate,
                    "snomed_id": concept_id,
                    "preferred_term": preferred_term,
                    "score": score,
                    "taxonomy_path": taxonomy_path,
                    "target_label": target_label,
                    "logic_structured": concept.logic_structured,
                }
            )

        self.index.save()
        return grounded

    def build_index_from_dirs(
        self,
        chunks_dir: Optional[str],
        tables_dir: Optional[str],
        guideline_title: str,
    ) -> None:
        if chunks_dir:
            for filename in sorted(os.listdir(chunks_dir)):
                if not filename.endswith(".md"):
                    continue
                path = os.path.join(chunks_dir, filename)
                with open(path, "r", encoding="utf-8") as f:
                    text = f.read().strip()
                if not text:
                    continue
                self.ground_sentence(
                    text, source_type="text", guideline_title=guideline_title
                )

        if tables_dir:
            for filename in sorted(os.listdir(tables_dir)):
                if not filename.endswith(".md"):
                    continue
                path = os.path.join(tables_dir, filename)
                with open(path, "r", encoding="utf-8") as f:
                    text = f.read().strip()
                if not text:
                    continue
                self.ground_sentence(
                    text, source_type="table", guideline_title=guideline_title
                )

    def _resolve_target_label_for_role(
        self, role: str, path_ids: List[int]
    ) -> Optional[str]:
        role_map = {
            "Condition": "ClinicalCondition",
            "ClinicalParameter": "ClinicalParameter",
            "Medication": "Medication",
            "Procedure": "Procedure",
        }
        mapped_label = role_map.get(role)
        if not mapped_label:
            return None
        for rule in self.mapping_rules:
            if rule.get("target_label") != mapped_label:
                continue
            roots = set()
            for root in rule.get("root_concepts", []) or []:
                try:
                    roots.add(int(root))
                except (TypeError, ValueError):
                    continue
            if roots & set(path_ids):
                return mapped_label
        return None


@click.command()
@click.option(
    "--sentence",
    default=None,
    help="Single sentence to ground (omit when using chunks/tables)",
)
@click.option(
    "--config-path",
    default=DEFAULT_CONFIG_PATH,
    help="Path to guideline_graph_schema.yaml",
)
@click.option(
    "--index-path",
    default=DEFAULT_INDEX_PATH,
    help="Path to the JSON grounding index file",
)
@click.option(
    "--chunks-dir",
    default=None,
    help="Directory containing guideline text chunks (.md)",
)
@click.option(
    "--tables-dir",
    default=None,
    help="Directory containing guideline table chunks (.md)",
)
@click.option(
    "--guideline-title",
    default="2024 ESC Guidelines for the management of chronic coronary syndromes",
    help="Guideline title for extraction context",
)
@click.option("--model", default="Qwen8b", help="LLM model name")
@click.option("--node", default="g4", help="Ollama node")
@click.option("--port", type=int, help="Custom Ollama port")
def main(
    sentence: Optional[str],
    config_path: str,
    index_path: str,
    chunks_dir: Optional[str],
    tables_dir: Optional[str],
    guideline_title: str,
    model: str,
    node: str,
    port: Optional[int],
):
    service = EntityGroundingServiceNew(
        config_path=config_path,
        model=model,
        node=node,
        port=port,
        index_path=index_path,
    )
    if chunks_dir or tables_dir:
        service.build_index_from_dirs(chunks_dir, tables_dir, guideline_title)
        return
    if not sentence:
        raise click.UsageError(
            "Provide --sentence or use --chunks-dir/--tables-dir for batch processing."
        )

    results = service.ground_sentence(
        sentence, source_type="text", guideline_title=guideline_title
    )

    for r in results:
        click.echo("---")
        click.echo(f"Entity: {r.entity_original}")
        click.echo(f"Standardized: {r.entity_standardized_candidate}")
        click.echo(f"Role: {r.role}")
        click.echo(f"Logic: {r.logic}")
        if r.logic_structured:
            click.echo(f"Logic structured: {r.logic_structured}")
        click.echo(f"SNOMED ID: {r.snomed_id}")
        click.echo(f"Preferred term: {r.preferred_term}")
        click.echo(f"Score: {r.score:.3f}")
        click.echo(f"Target label: {r.target_label}")
        click.echo("Taxonomy path:")
        for p in r.taxonomy_path:
            click.echo(f"  - {p['term']} ({p['concept_id']})")


if __name__ == "__main__":
    main()
