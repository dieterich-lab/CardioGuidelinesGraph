#!/usr/bin/env python3
"""
Entity Grounding Service (New Workflow)

- Uses LLM (BAML) to extract and standardize concepts from text.
- Fuzzy searches SNOMED CT database directly for best matching concept.
- Extracts taxonomy path to configured root concepts and maps to T-Box labels.
"""

import json
import logging
import os
import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Dict, List, Optional, Tuple

import click
import yaml

from cardio_graph.extraction_utils.clients import create_client_registry
from cardio_graph.snomedct_utils.snomed_query import SnomedExplorer

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("EntityGroundingService")

IS_A_TYPE_ID = 116680003
DEFAULT_CONFIG_PATH = os.path.join(
    os.path.dirname(__file__), "../snomedct_utils/guideline_graph_schema.yaml"
)
DEFAULT_ABBRV_PATH = os.path.join(
    os.path.dirname(__file__), "../snomedct_utils/abbrv.txt"
)
DEFAULT_INDEX_PATH = "/prj/doctoral_letters/guide/data/grounding_index.json"
DEFAULT_RULES_PATH = "/prj/doctoral_letters/guide/data/extracted_rules.jsonl"
MIN_MATCH_SCORE = 0.7
MIN_TERM_LEN = 3
ALLOWED_ROLES = {
    "Condition",
    "ClinicalParameter",
    "Medication",
    "Procedure",
    "Other",
}
BLOCKED_ROLES = {
    "GuidelineSource",
    "Recommendation",
    "DecisionNode",
    "RecommendationNode",
}
ALWAYS_NOISE_PATTERNS = [
    r"^doi\b",
    r"\bdoi:\b",
    r"\bissn\b",
    r"\bwww\.\b",
    r"\bhttp(s)?://",
    r"^©",
    r"copyright",
    r"all rights reserved",
    r"^downloaded from",
    r"^by guest",
]
HEADER_NOISE_PATTERNS = [
    r"^table\s+\d+",
    r"^figure\s+\d+",
    r"^supplementary",
    r"^european heart journal",
    r"\bguidelines?\b",
    r"^page\s+\d+",
]
STUDY_SOURCE_PATTERNS = [
    r"\btrial\b",
    r"\bstudy\b",
    r"\bmeta-?analysis\b",
    r"\bregistry\b",
    r"\bguidelines?\b",
    r"\brecommendation table\b",
    r"\bevidence table\b",
    r"\btable\s+\d+\b",
    r"\bfigure\s+\d+\b",
    r"\bsection\b",
]


@dataclass
class ExtractedConcept:
    rule_id: Optional[int]
    entity_original: str
    entity_standardized_candidate: str
    role: str
    logic: str
    logic_structured: Dict[str, str]


@dataclass
class GroundedConcept:
    rule_id: Optional[int]
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
        abbrv_path: str = DEFAULT_ABBRV_PATH,
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
        self.abbreviations = self._load_abbreviations(abbrv_path)

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

    def _load_abbreviations(self, abbrv_path: str) -> Dict[str, List[str]]:
        mapping: Dict[str, List[str]] = {}
        if not abbrv_path or not os.path.exists(abbrv_path):
            return mapping
        with open(abbrv_path, "r", encoding="utf-8") as f:
            raw = f.read().strip()
        if not raw:
            return mapping
        entries = [e.strip() for e in raw.split(";") if e.strip()]
        for entry in entries:
            entry = entry.strip().rstrip(".")
            if "," not in entry:
                continue
            abbrv, expansion = entry.split(",", 1)
            abbrv = " ".join(abbrv.strip().split())
            expansion = " ".join(expansion.strip().split())
            if not abbrv or not expansion:
                continue
            abbrv_key = self._normalize(abbrv)
            expansion_key = self._normalize(expansion)
            mapping.setdefault(abbrv_key, [])
            if expansion not in mapping[abbrv_key]:
                mapping[abbrv_key].append(expansion)
            mapping.setdefault(expansion_key, [])
            if abbrv not in mapping[expansion_key]:
                mapping[expansion_key].append(abbrv)
        return mapping

    def _expand_term(self, term: str) -> List[str]:
        if not term:
            return []
        key = self._normalize(term)
        return self.abbreviations.get(key, [])

    def _score(self, query: str, candidate: str) -> float:
        q = self._normalize(query)
        c = self._normalize(candidate)
        if not q or not c:
            return 0.0
        if q == c:
            return 1.0
        return SequenceMatcher(None, q, c).ratio()

    def _is_noise_phrase(self, text: str) -> bool:
        if not text:
            return True
        normalized = self._normalize(text)
        if len(normalized) < MIN_TERM_LEN:
            return True
        if all(ch.isdigit() or ch in {"-", "/"} for ch in normalized):
            return True
        for pattern in ALWAYS_NOISE_PATTERNS:
            if re.search(pattern, normalized, flags=re.IGNORECASE):
                return True
        if len(normalized) < 80:
            for pattern in HEADER_NOISE_PATTERNS:
                if re.search(pattern, normalized, flags=re.IGNORECASE):
                    return True
        return False

    def _filter_text_block(self, text: str) -> str:
        if not text:
            return ""
        kept_lines = []
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if self._is_noise_phrase(line):
                continue
            kept_lines.append(line)
        return "\n".join(kept_lines)

    def _should_skip_concept(
        self,
        concept: ExtractedConcept,
        score: float,
        target_label: Optional[str],
        has_clinical_anchor: bool,
    ) -> bool:
        if self._is_noise_phrase(concept.entity_standardized_candidate):
            return True
        if self._is_blocked_role(concept):
            return True
        if self._is_study_or_source_term(concept):
            return True
        if concept.role == "Other" and not self._should_keep_other(
            concept, target_label
        ):
            return True
        if self._is_statistic_term(concept) and not has_clinical_anchor:
            return True
        if score < MIN_MATCH_SCORE:
            return True
        if target_label is None and concept.role not in ALLOWED_ROLES:
            return True
        return False

    def _is_blocked_role(self, concept: ExtractedConcept) -> bool:
        return (concept.role or "").strip() in BLOCKED_ROLES

    def _is_study_or_source_term(self, concept: ExtractedConcept) -> bool:
        text = (
            f"{concept.entity_original} {concept.entity_standardized_candidate}".lower()
        )
        return any(re.search(pattern, text) for pattern in STUDY_SOURCE_PATTERNS)

    def _should_keep_other(
        self, concept: ExtractedConcept, target_label: Optional[str]
    ) -> bool:
        return target_label == "ClinicalCondition"

    def _is_statistic_term(self, concept: ExtractedConcept) -> bool:
        text = (
            f"{concept.entity_original} {concept.entity_standardized_candidate}".lower()
        )
        stat_patterns = [
            r"\bhazard ratio\b",
            r"\bhr\b",
            r"\bp-?value\b",
            r"\bconfidence interval\b",
            r"\bci\b",
            r"\bp\s*=\s*\d",
        ]
        return any(re.search(pattern, text) for pattern in stat_patterns)

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
        search_terms.extend(self._expand_term(term))
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

    def _serialize_baml_result(self, result) -> Dict:
        if hasattr(result, "model_dump"):
            return result.model_dump()
        if hasattr(result, "dict"):
            return result.dict()
        if hasattr(result, "json"):
            try:
                return json.loads(result.json())
            except Exception:
                return {"raw": result.json()}
        return {"raw": str(result)}

    def extract_concepts(
        self, sentence: str, source_type: str, guideline_title: str
    ) -> List[ExtractedConcept]:
        from cardio_graph.baml_client.sync_client import b

        baml_options = {"client_registry": self.client_registry}
        os.environ["BAML_LOG"] = "OFF"
        tagged_text = (
            f"[GUIDELINE: {guideline_title}] "
            f"[SOURCE_TYPE: {source_type}]\n{sentence}"
        )
        result = b.ExtractConcepts(tagged_text, baml_options=baml_options)
        parsed_payload = self._serialize_baml_result(result)
        logger.info("---Parsed Response (class ExtractConceptsResult)---")
        logger.info(json.dumps(parsed_payload, ensure_ascii=False, indent=2))

        concepts = []
        for concept in result.concepts or []:
            logic_structured = {
                "strength": "Unknown",
                "level": "Unknown",
                "direction": "UNKNOWN",
                "operator": None,
                "threshold": None,
                "unit": None,
                "condition_context": None,
            }
            if getattr(concept, "logic_structured", None):
                logic_structured.update(concept.logic_structured.model_dump())
            concepts.append(
                ExtractedConcept(
                    rule_id=getattr(concept, "rule_id", None),
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
        filtered_sentence = self._filter_text_block(sentence)
        if not filtered_sentence:
            return []
        extracted = self.extract_concepts(
            filtered_sentence, source_type, guideline_title
        )
        grounded: List[GroundedConcept] = []
        has_clinical_anchor = any(
            c.role in {"Condition", "Medication", "Procedure"} for c in extracted
        )

        for concept in extracted:
            cached = self.index.lookup(concept.entity_standardized_candidate)
            if cached:
                if cached.get("target_label") is None and concept.role:
                    fallback_label = self._fallback_target_label_for_role(concept.role)
                    if fallback_label:
                        cached["target_label"] = fallback_label
                if self._should_skip_concept(
                    concept,
                    cached.get("score", 1.0),
                    cached.get("target_label"),
                    has_clinical_anchor,
                ):
                    continue
                grounded.append(
                    GroundedConcept(
                        rule_id=concept.rule_id,
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
            if target_label is None and concept.role and len(path_ids) <= 1:
                target_label = self._fallback_target_label_for_role(concept.role)
            taxonomy_path = self._format_taxonomy_path(path_ids)

            if self._should_skip_concept(
                concept, score, target_label, has_clinical_anchor
            ):
                continue

            grounded_concept = GroundedConcept(
                rule_id=concept.rule_id,
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
                }
            )

        self.index.save()
        return grounded

    def build_index_from_dirs(
        self,
        chunks_dir: Optional[str],
        tables_dir: Optional[str],
        guideline_title: str,
        rules_out_path: Optional[str] = None,
    ) -> None:
        rules_file = None
        if rules_out_path:
            os.makedirs(os.path.dirname(rules_out_path), exist_ok=True)
            rules_file = open(rules_out_path, "w", encoding="utf-8")
        if chunks_dir:
            chunk_files = [
                f for f in sorted(os.listdir(chunks_dir)) if f.endswith(".md")
            ]
            total_chunks = len(chunk_files)
            for idx, filename in enumerate(chunk_files, start=1):
                path = os.path.join(chunks_dir, filename)
                with open(path, "r", encoding="utf-8") as f:
                    text = f.read().strip()
                if not text:
                    continue
                grounded = self.ground_sentence(
                    text, source_type="text", guideline_title=guideline_title
                )
                self._log_grounded_summary(
                    chunk_id=filename,
                    source_type="text",
                    grounded=grounded,
                    index=idx,
                    total=total_chunks,
                )
                if rules_file:
                    self._write_rules_entries(
                        rules_file,
                        grounded,
                        chunk_id=filename,
                        source_context=path,
                        source_type="text",
                        guideline_title=guideline_title,
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
                grounded = self.ground_sentence(
                    text, source_type="table", guideline_title=guideline_title
                )
                self._log_grounded_summary(
                    chunk_id=filename,
                    source_type="table",
                    grounded=grounded,
                )
                if rules_file:
                    self._write_rules_entries(
                        rules_file,
                        grounded,
                        chunk_id=filename,
                        source_context=path,
                        source_type="table",
                        guideline_title=guideline_title,
                    )
        if rules_file:
            rules_file.close()

    def _log_grounded_summary(
        self,
        chunk_id: str,
        source_type: str,
        grounded: List[GroundedConcept],
        index: Optional[int] = None,
        total: Optional[int] = None,
    ) -> None:
        if not grounded:
            logger.info("Chunk %s (%s): grounded 0 concepts", chunk_id, source_type)
            return
        if index is not None and total is not None:
            logger.info(
                "Chunk %d/%d %s (%s): grounded %d concepts",
                index,
                total,
                chunk_id,
                source_type,
                len(grounded),
            )
        else:
            logger.info(
                "Chunk %s (%s): grounded %d concepts",
                chunk_id,
                source_type,
                len(grounded),
            )
        for concept in grounded:
            logger.info(
                "  - %s | role=%s | snomed_id=%s | target_label=%s",
                concept.entity_standardized_candidate,
                concept.role,
                concept.snomed_id,
                concept.target_label,
            )

    def _write_rules_entries(
        self,
        fh,
        grounded: List[GroundedConcept],
        chunk_id: str,
        source_context: str,
        source_type: str,
        guideline_title: str,
    ) -> None:
        for concept in grounded:
            entry = {
                "entity_standardized_candidate": concept.entity_standardized_candidate,
                "snomed_id": concept.snomed_id,
                "role": concept.role,
                "target_label": concept.target_label,
                "logic_structured": concept.logic_structured,
                "rule_id": concept.rule_id,
                "chunk_id": chunk_id,
                "source_context": source_context,
                "source_type": source_type,
                "guideline_title": guideline_title,
            }
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def _resolve_target_label_for_role(
        self, role: str, path_ids: List[int]
    ) -> Optional[str]:
        role_map = {
            "Condition": "ClinicalCondition",
            "ClinicalParameter": "ClinicalParameter",
            "Medication": "Medication",
            "Procedure": "Procedure",
            "Other": "ClinicalCondition",
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

    def _fallback_target_label_for_role(self, role: str) -> Optional[str]:
        role_map = {
            "Condition": "ClinicalCondition",
            "ClinicalParameter": "ClinicalParameter",
            "Medication": "Medication",
            "Procedure": "Procedure",
            "Other": "ClinicalCondition",
        }
        return role_map.get(role)


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
    "--rules-out-path",
    default=DEFAULT_RULES_PATH,
    help="Path to write extracted rules as JSONL (optional)",
)
@click.option(
    "--abbrv-path",
    default=DEFAULT_ABBRV_PATH,
    help="Path to abbreviation list (abbrv, expansion; ...) ",
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
    abbrv_path: str,
    rules_out_path: Optional[str],
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
        abbrv_path=abbrv_path,
    )
    if chunks_dir or tables_dir:
        service.build_index_from_dirs(
            chunks_dir,
            tables_dir,
            guideline_title,
            rules_out_path=rules_out_path,
        )
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
        click.echo(f"Rule ID: {r.rule_id}")
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
