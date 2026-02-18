#!/usr/bin/env python3
"""
Guideline Graph Builder

- Uses LLM (BAML) to extract and standardize concepts from text.
- Fuzzy searches SNOMED CT database directly for best matching concept.
- Extracts taxonomy path to configured root concepts and maps to T-Box labels.
- Builds index + rules outputs for graph construction.
"""

import json
import logging
import os
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import click
import yaml

from cardio_graph_core.extraction.clients import create_client_registry
from cardio_graph_core.snomedct.snomed_query import SnomedExplorer

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True,
)
logger = logging.getLogger("GuidelineGraphBuilder")

IS_A_TYPE_ID = 116680003
DEFAULT_CONFIG_PATH = os.path.join(
    Path(__file__).resolve().parents[3],
    "config",
    "cardio_graph_core",
    "guideline_graph_schema.yaml",
)
DEFAULT_ABBRV_PATH = os.path.join(
    Path(__file__).resolve().parents[3],
    "config",
    "cardio_graph_core",
    "abbrv.txt",
)
DEFAULT_INDEX_PATH = "/prj/doctoral_letters/guide/data/graph/grounding_index.json"
DEFAULT_RULES_PATH = "/prj/doctoral_letters/guide/data/graph/extracted_rules.jsonl"
DEFAULT_MIN_MATCH_SCORE = 0.6
MIN_TERM_LEN = 3
MAX_QUERY_TOKENS = 6
MAX_CONCEPT_CANDIDATES = 200
STOPWORD_TOKENS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "chronic",
    "complex",
    "consultation",
    "disease",
    "disorder",
    "for",
    "from",
    "in",
    "is",
    "of",
    "on",
    "or",
    "procedure",
    "syndrome",
    "team",
    "the",
    "to",
    "with",
}
DISALLOWED_SEMANTIC_TAGS = {
    "occupation",
    "ethnic group finding",
    "qualifier value",
    "event",
}
ALLOWED_SEMANTIC_TAGS_BY_ROLE = {
    "ClinicalCondition": {"disorder", "finding"},
    "ClinicalParameter": {"observable entity"},
    "Medication": {"substance", "product"},
    "Procedure": {"procedure"},
}
ALLOWED_ROLES = {
    "ClinicalCondition",
    "ClinicalParameter",
    "Medication",
    "Procedure",
    "Other",
}
BLOCKED_ROLES = {
    "GuidelineSource",
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
    r"\bguidelinesource\b",
    r"\bguideline source\b",
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
    r"\bguidelinesource\b",
    r"\bguideline source\b",
]


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
    alt_names: List[str]
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

    def save_as(self, index_path: str) -> None:
        if not index_path:
            return
        os.makedirs(os.path.dirname(index_path), exist_ok=True)
        data = {
            "by_snomed_id": self.by_snomed_id,
            "by_standardized": self.by_standardized,
        }
        with open(index_path, "w", encoding="utf-8") as f:
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


class GuidelineGraphBuilder:
    def __init__(
        self,
        config_path: str = DEFAULT_CONFIG_PATH,
        model: str = "Qwen8b",
        node: str = "g4",
        port: Optional[int] = None,
        index_path: str = DEFAULT_INDEX_PATH,
        abbrv_path: str = DEFAULT_ABBRV_PATH,
        min_match_score: float = DEFAULT_MIN_MATCH_SCORE,
        enable_domain_filter: bool = True,
        enable_semantic_tag_filter: bool = False,
        off_domain_min_score: Optional[float] = None,
    ):
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found at: {config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

        self.mapping_rules = self.config.get("snomed_mapping", {}).get(
            "mapping_rules", []
        )
        extraction_contract = self.config.get("extraction_contract", {}) or {}
        condition_logic_fields = set(
            (extraction_contract.get("condition_logic_fields") or {}).keys()
        )
        recommendation_fields = set(
            (extraction_contract.get("recommendation_fields") or {}).keys()
        )
        self._allowed_logic_structured_keys = (
            condition_logic_fields | recommendation_fields
        )
        self.root_concepts = self._collect_root_concepts(self.mapping_rules)

        self.client_registry = create_client_registry(model, node, port)

        self.snomed_explorer = SnomedExplorer()
        self.snomed_explorer.connect()

        self._preferred_term_cache: Dict[int, str] = {}
        self._alt_names_cache: Dict[int, List[str]] = {}
        self._taxonomy_path_cache: Dict[int, List[int]] = {}
        self._relationships_cache: Dict[int, List[Dict[str, Any]]] = {}
        self._search_cache: Dict[str, List[Dict[str, Any]]] = {}
        self._allowed_root_concepts_by_label: Dict[str, set] = {}
        for rule in self.mapping_rules:
            label = rule.get("target_label")
            if not label:
                continue
            roots = set()
            for root in rule.get("root_concepts", []) or []:
                try:
                    roots.add(int(root))
                except (TypeError, ValueError):
                    continue
            if roots:
                self._allowed_root_concepts_by_label.setdefault(label, set()).update(
                    roots
                )
        self.index = ConceptIndex(index_path=index_path)
        self.abbreviations = self._load_abbreviations(abbrv_path)
        self.min_match_score = min_match_score
        self.enable_domain_filter = enable_domain_filter
        self.enable_semantic_tag_filter = enable_semantic_tag_filter
        self.off_domain_min_score = off_domain_min_score

    def _collect_root_concepts(self, mapping_rules: List[Dict]) -> List[int]:
        roots = []
        for rule in mapping_rules:
            for root in rule.get("root_concepts", []) or []:
                try:
                    roots.append(int(root))
                except (TypeError, ValueError):
                    continue
        return list(sorted(set(roots)))

    def _filter_logic_structured(
        self, logic_structured: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        payload = dict(logic_structured or {})
        if not self._allowed_logic_structured_keys:
            return payload
        return {
            key: value
            for key, value in payload.items()
            if key in self._allowed_logic_structured_keys
        }

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

    def _expand_term_variants(self, term: str) -> List[str]:
        if not term:
            return []
        variants = set()
        tokens = re.findall(r"[A-Za-z0-9]+", term)
        for token in tokens:
            expansions = self._expand_term(token)
            for expansion in expansions:
                pattern = re.compile(rf"\b{re.escape(token)}\b", re.IGNORECASE)
                variant = pattern.sub(expansion, term)
                variants.add(variant)
        return list(variants)

    def _important_tokens(self, text: str) -> List[str]:
        tokens = re.findall(r"[a-z0-9]+", self._normalize(text))
        return [t for t in tokens if len(t) > 2 and t not in STOPWORD_TOKENS]

    def _has_disallowed_semantic_tag(self, term: Optional[str]) -> bool:
        if not term:
            return False
        match = re.search(r"\(([^)]+)\)\s*$", term)
        if not match:
            return False
        tag = match.group(1).strip().lower()
        return tag in DISALLOWED_SEMANTIC_TAGS

    def _has_allowed_semantic_tag(
        self, role: Optional[str], term: Optional[str]
    ) -> bool:
        if not role or not term:
            return True
        allowed = ALLOWED_SEMANTIC_TAGS_BY_ROLE.get(role)
        if not allowed:
            return True
        match = re.search(r"\(([^)]+)\)\s*$", term)
        if not match:
            return False
        tag = match.group(1).strip().lower()
        return tag in allowed

    def _score(self, query: str, candidate: str) -> float:
        q = self._normalize(query)
        c = self._normalize(candidate)
        if not q or not c:
            return 0.0
        if q == c:
            return 1.0
        return SequenceMatcher(None, q, c).ratio()

    def _token_overlap_ratio(self, tokens: set, term: Optional[str]) -> float:
        if not tokens or not term:
            return 0.0
        term_tokens = set(self._important_tokens(term))
        if not term_tokens:
            return 0.0
        return len(tokens & term_tokens) / max(len(tokens), 1)

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
        allow_unmapped: bool = False,
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
        if score < self.min_match_score and not allow_unmapped:
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

    def _get_alt_names(
        self, concept_id: int, preferred_term: Optional[str]
    ) -> List[str]:
        if concept_id in self._alt_names_cache:
            return self._alt_names_cache[concept_id]
        descriptions = self.snomed_explorer.get_descriptions_for_concept(concept_id)
        seen = set()
        alt_names: List[str] = []
        normalized_preferred = self._normalize(preferred_term or "")
        for description in descriptions:
            term = (description.get("term") or "").strip()
            if not term:
                continue
            normalized_term = self._normalize(term)
            if normalized_preferred and normalized_term == normalized_preferred:
                continue
            if normalized_term in seen:
                continue
            seen.add(normalized_term)
            alt_names.append(term)
        self._alt_names_cache[concept_id] = alt_names
        return alt_names

    def _search_best_concept(
        self, term: str, role: Optional[str], limit: int = 100
    ) -> Tuple[Optional[int], Optional[str], float]:
        if not term:
            return None, None, 0.0

        search_start = time.perf_counter()

        stripped_term = re.sub(r"\s*\([^)]*\)\s*", " ", term).strip()
        normalized_term = self._normalize(term)
        paren_tokens = []
        for group in re.findall(r"\(([^)]+)\)", term):
            for token in re.findall(r"[A-Za-z0-9]+", group):
                if token:
                    paren_tokens.append(token)

        normalized_tokens = [
            t
            for t in self._normalize(term).split()
            if len(t) > 2 and t not in STOPWORD_TOKENS
        ]
        important_tokens = self._important_tokens(term)
        use_short_query = len(normalized_tokens) > MAX_QUERY_TOKENS

        search_terms: List[str] = []
        expanded_terms: List[str] = []
        if use_short_query:
            tokens = important_tokens[:MAX_QUERY_TOKENS]
            for token in paren_tokens:
                if token not in tokens:
                    tokens.append(token)
            condensed = " ".join(tokens)
            if condensed:
                search_terms.append(condensed)
            search_terms.extend(tokens)
            logger.info(
                "Grounding short-query tokens for '%s': %s",
                term,
                tokens,
            )
        else:
            expanded_terms = self._expand_term(term)
            expanded_terms.extend(self._expand_term_variants(term))
            search_terms.append(term)
            search_terms.extend(expanded_terms)
            search_terms.extend(normalized_tokens)
            if stripped_term and stripped_term != term:
                search_terms.append(stripped_term)
                search_terms.extend(self._expand_term(stripped_term))
            if paren_tokens:
                search_terms.extend(paren_tokens)

        if "coronary syndrome" in normalized_term:
            ischemic_variant = normalized_term.replace(
                "coronary syndrome", "ischemic heart disease"
            )
            search_terms.append(ischemic_variant)

        if not search_terms:
            search_terms = [term]

        results = []
        seen = set()
        for t in search_terms:
            if t in seen:
                continue
            seen.add(t)
            cached = self._search_cache.get(t)
            if cached is None:
                cached = self.snomed_explorer.search_concepts_by_term(t, limit=limit)
                self._search_cache[t] = cached
            results.extend(cached)

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

        concept_items_all = list(concept_terms.items())
        concept_items_allowed = concept_items_all
        if self.enable_domain_filter and role:
            allowed_roots = self._allowed_root_concepts_for_role(role)
            if allowed_roots:
                concept_items_allowed = [
                    (concept_id, terms)
                    for concept_id, terms in concept_items_all
                    if self._concept_in_allowed_roots(concept_id, allowed_roots)
                ]
        concept_items = concept_items_allowed
        if len(concept_items) > MAX_CONCEPT_CANDIDATES:
            logger.info(
                "Truncating concept candidates from %d to %d for '%s'",
                len(concept_items),
                MAX_CONCEPT_CANDIDATES,
                term,
            )
            concept_items = concept_items[:MAX_CONCEPT_CANDIDATES]

        if use_short_query:
            query_terms = tokens
        else:
            query_terms = [term] + expanded_terms
            if stripped_term and stripped_term != term:
                query_terms.append(stripped_term)
            if paren_tokens:
                query_terms.extend(paren_tokens)
            if "coronary syndrome" in normalized_term:
                query_terms.append(ischemic_variant)
        if not query_terms:
            query_terms = [term]

        important_query_tokens = set()
        for q in query_terms:
            important_query_tokens.update(self._important_tokens(q))

        def score_candidates(concept_items_to_score, role_filter):
            local_best_id = None
            local_best_term = None
            local_best_score = 0.0
            for concept_id, terms in concept_items_to_score:
                if role_filter and not self._candidate_matches_role(
                    concept_id, role_filter
                ):
                    continue
                preferred = self._get_preferred_term(concept_id)
                candidates = list(terms)
                if preferred:
                    candidates.append(preferred)

                if important_query_tokens:
                    if not any(
                        important_query_tokens & set(self._important_tokens(candidate))
                        for candidate in candidates
                    ):
                        continue

                score = 0.0
                best_candidate_term = None
                for candidate in candidates:
                    candidate_norm = self._normalize(candidate)
                    candidate_score = max(
                        (self._score(q, candidate) for q in query_terms if q),
                        default=0.0,
                    )
                    stripped_norm = (
                        self._normalize(stripped_term) if stripped_term else ""
                    )
                    if stripped_norm and stripped_norm in candidate_norm:
                        candidate_score = min(1.0, candidate_score + 0.05)
                    if paren_tokens and any(
                        token.lower() in candidate_norm for token in paren_tokens
                    ):
                        candidate_score = min(1.0, candidate_score + 0.03)
                    overlap_ratio = self._token_overlap_ratio(
                        important_query_tokens, candidate
                    )
                    if overlap_ratio:
                        candidate_score = min(
                            1.0, candidate_score + overlap_ratio * 0.1
                        )
                    if candidate_score > score:
                        score = candidate_score
                        best_candidate_term = candidate

                preferred_overlap = self._token_overlap_ratio(
                    important_query_tokens, preferred or ""
                )
                if preferred and important_query_tokens:
                    if preferred_overlap < 0.5:
                        continue

                if score > local_best_score:
                    local_best_score = score
                    local_best_id = concept_id
                    local_best_term = preferred or best_candidate_term
            return local_best_id, local_best_term, local_best_score

        best_id, best_term, best_score = score_candidates(concept_items, role)

        if self.off_domain_min_score is not None and role:
            if best_score < self.off_domain_min_score:
                fallback_items = concept_items_all
                if len(fallback_items) > MAX_CONCEPT_CANDIDATES:
                    fallback_items = fallback_items[:MAX_CONCEPT_CANDIDATES]
                off_id, off_term, off_score = score_candidates(fallback_items, None)
                if off_score >= self.off_domain_min_score and off_score > best_score:
                    best_id, best_term, best_score = off_id, off_term, off_score

        if self._has_disallowed_semantic_tag(best_term):
            return None, None, 0.0
        if self.enable_semantic_tag_filter and not self._has_allowed_semantic_tag(
            role, best_term
        ):
            return None, None, 0.0

        _ = time.perf_counter() - search_start

        return best_id, best_term, best_score

    def _get_taxonomy_path_cached(self, concept_id: Optional[int]) -> List[int]:
        if concept_id is None:
            return []
        if concept_id in self._taxonomy_path_cache:
            return self._taxonomy_path_cache[concept_id]
        path = self._extract_taxonomy_path(concept_id)
        self._taxonomy_path_cache[concept_id] = path
        return path

    def _candidate_matches_role(self, concept_id: int, role: Optional[str]) -> bool:
        if not role:
            return True
        if not self.enable_domain_filter:
            return True
        allowed_roots = self._allowed_root_concepts_for_role(role)
        if not allowed_roots:
            return True
        return self._concept_in_allowed_roots(concept_id, allowed_roots)

    def _concept_in_allowed_roots(self, concept_id: int, allowed_roots: set) -> bool:
        if not allowed_roots:
            return True
        path_ids = self._get_taxonomy_path_cached(concept_id)
        return bool(set(path_ids) & allowed_roots)

    def _get_parents(self, concept_id: int) -> List[int]:
        cached = self._relationships_cache.get(concept_id)
        if cached is None:
            cached = self.snomed_explorer.get_relationships(concept_id)
            self._relationships_cache[concept_id] = cached
        relationships = cached
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

    def _extract_taxonomy_path(self, concept_id: int, max_depth: int = 10) -> List[int]:
        if concept_id is None:
            return []

        def traverse_up(current: int, path: List[int], depth: int) -> List[int]:
            if depth >= max_depth or current in path:
                return path
            path = path + [current]
            parents = self._get_parents(current)
            if not parents:
                return path
            # Since it's a taxonomy, take the first parent for the path, but to get full, perhaps collect all
            # For simplicity, follow one path
            return traverse_up(parents[0], path, depth + 1)

        return traverse_up(concept_id, [], 0)

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

    def _expand_abbreviations_in_text(self, text: str) -> str:
        replacements = {
            "LVEF": "left ventricular ejection fraction (LVEF)",
            "CCS": "chronic coronary syndrome (CCS)",
            "CAD": "coronary artery disease (CAD)",
            "CABG": "coronary artery bypass grafting (CABG)",
            "PCI": "percutaneous coronary intervention (PCI)",
            "LAD": "left anterior descending artery (LAD)",
            "MVD": "multivessel disease (MVD)",
            "FFR": "fractional flow reserve (FFR)",
            "IFR": "instantaneous wave-free ratio (iFR)",
            "QFR": "quantitative flow ratio (QFR)",
            "IVUS": "intravascular ultrasound (IVUS)",
            "OCT": "optical coherence tomography (OCT)",
            "STS": "society of thoracic surgeons score (STS)",
            "SYNTAX": "SYNTAX score (SYNTAX)",
        }
        updated = text
        for abbr, expansion in replacements.items():
            updated = re.sub(rf"\b{re.escape(abbr)}\b", expansion, updated)
        return updated

    def _format_docling_table_rows(
        self, table_jsons: List[Dict], footnotes: Optional[str] = None
    ) -> List[Tuple[str, str]]:
        rows: List[Dict] = []
        for table_json in table_jsons:
            rows.extend(table_json.get("data", []) or [])
        header = "Columns: Recommendations | Class | Level"
        footnotes_block = None
        if footnotes:
            footnotes_block = "DOC_FOOTNOTES:\n" + footnotes.strip()
        formatted_rows: List[Tuple[str, str]] = []
        for idx, row in enumerate(rows, start=1):
            recommendation = (row.get("Recommendations") or "").strip()
            cls = (row.get("Class") or "").strip()
            level = (row.get("Level") or "").strip()
            if not recommendation and not cls and not level:
                continue
            recommendation = self._expand_abbreviations_in_text(recommendation)
            parts = []
            if recommendation:
                parts.append(f"Recommendation: {recommendation}")
            if cls:
                parts.append(f"Class: {cls}")
            if level:
                parts.append(f"Level: {level}")
            body_lines = [
                "DOC_SOURCE: docling_json",
                "DOC_FORMAT: docling_json",
                header,
                "",
                " | ".join(parts),
            ]
            if footnotes_block:
                body_lines.extend(["", footnotes_block])
            row_text = "\n".join(
                [line for line in body_lines if line is not None]
            ).strip()
            formatted_rows.append((f"row_{idx:02d}", row_text))
        return formatted_rows

    def _format_docling_table_full(
        self, table_jsons: List[Dict], footnotes: Optional[str] = None
    ) -> str:
        rows: List[Dict] = []
        for table_json in table_jsons:
            rows.extend(table_json.get("data", []) or [])
        header = "Columns: Recommendations | Class | Level"
        row_lines: List[str] = []
        for idx, row in enumerate(rows, start=1):
            recommendation = (row.get("Recommendations") or "").strip()
            cls = (row.get("Class") or "").strip()
            level = (row.get("Level") or "").strip()
            if not recommendation and not cls and not level:
                continue
            recommendation = self._expand_abbreviations_in_text(recommendation)
            parts = []
            if recommendation:
                parts.append(f"Recommendation: {recommendation}")
            if cls:
                parts.append(f"Class: {cls}")
            if level:
                parts.append(f"Level: {level}")
            row_lines.append(f"Row {idx:02d}: " + " | ".join(parts))
        body_lines = [
            "DOC_SOURCE: docling_json",
            "DOC_FORMAT: docling_json",
            header,
            "",
            "DOC_ROWS:",
        ]
        body_lines.extend(row_lines)
        if footnotes:
            body_lines.extend(["", "DOC_FOOTNOTES:", footnotes.strip()])
        return "\n".join([line for line in body_lines if line is not None]).strip()

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

    def _log_extracted_concepts(self, extracted: List[ExtractedConcept]) -> None:
        return

    def _log_grounded_concepts(self, grounded: List[GroundedConcept]) -> None:
        return

    def _load_prompt_appendix(self) -> str:
        appendix_inline = (
            os.environ.get("CARDIO_GRAPH_EXTRACTION_PROMPT_APPENDIX", "") or ""
        ).strip()
        appendix_path = (
            os.environ.get("CARDIO_GRAPH_EXTRACTION_PROMPT_APPENDIX_PATH", "") or ""
        ).strip()
        appendix_file = ""
        if appendix_path and os.path.isfile(appendix_path):
            try:
                appendix_file = Path(appendix_path).read_text(encoding="utf-8").strip()
            except Exception:
                appendix_file = ""
        if appendix_inline and appendix_file:
            return appendix_file + "\n" + appendix_inline
        return appendix_file or appendix_inline

    def extract_concepts(
        self,
        sentence: str,
        source_type: str,
        guideline_title: str,
        focus: Optional[str] = None,
    ) -> List[ExtractedConcept]:
        from cardio_graph_core.extraction.baml_client.sync_client import b

        baml_options = {"client_registry": self.client_registry}
        os.environ["BAML_LOG"] = "OFF"
        focus_tag = f"[FOCUS: {focus}] " if focus else ""
        prompt_appendix = self._load_prompt_appendix()
        appendix_block = (
            f"[TUNING_APPENDIX]\n{prompt_appendix}\n[/TUNING_APPENDIX]\n"
            if prompt_appendix
            else ""
        )
        tagged_text = (
            f"{appendix_block}"
            f"{focus_tag}[GUIDELINE: {guideline_title}] "
            f"[SOURCE_TYPE: {source_type}]\n{sentence}"
        )
        incremental_review_enabled = (
            os.environ.get("CARDIO_GRAPH_ENABLE_INCREMENTAL_REVIEW", "1") or "1"
        ).strip().lower() not in {"0", "false", "no", "off"}
        concepts: List[ExtractedConcept] = []

        def _default_logic_structured() -> Dict[str, Optional[str]]:
            return {
                "strength": "Unknown",
                "level": "Unknown",
                "direction": None,
                "operator": None,
                "threshold": None,
                "unit": None,
                "context": None,
                "logic_type": None,
                "logic_group": None,
            }

        def _concepts_from_extract_concepts_result(
            result_obj: Any,
        ) -> List[ExtractedConcept]:
            parsed: List[ExtractedConcept] = []
            for concept in getattr(result_obj, "concepts", []) or []:
                logic_structured = _default_logic_structured()
                if getattr(concept, "logic_structured", None):
                    logic_structured.update(concept.logic_structured.model_dump())
                logic_structured = self._filter_logic_structured(logic_structured)
                parsed.append(
                    ExtractedConcept(
                        entity_original=concept.entity_original,
                        entity_standardized_candidate=concept.entity_standardized_candidate,
                        role=concept.role,
                        logic=concept.logic,
                        logic_structured=logic_structured,
                    )
                )
            return parsed

        try:
            rules_result = b.ExtractRulesV2(tagged_text, baml_options=baml_options)
            rules_serialized = self._serialize_baml_result(rules_result)
            for rule in getattr(rules_result, "rules", []) or []:
                for condition in getattr(rule, "conditions", []) or []:
                    logic_structured = _default_logic_structured()
                    logic = getattr(condition, "logic", None)
                    if logic is not None:
                        logic_structured.update(logic.model_dump())
                    logic_structured = self._filter_logic_structured(logic_structured)
                    concepts.append(
                        ExtractedConcept(
                            entity_original=condition.entity_original,
                            entity_standardized_candidate=condition.entity_standardized_candidate,
                            role=condition.role,
                            logic="condition",
                            logic_structured=logic_structured,
                        )
                    )
                for action in getattr(rule, "actions", []) or []:
                    logic_structured = _default_logic_structured()
                    recommendation = getattr(action, "recommendation", None)
                    if recommendation is not None:
                        logic_structured.update(recommendation.model_dump())
                    logic_structured = self._filter_logic_structured(logic_structured)
                    concepts.append(
                        ExtractedConcept(
                            entity_original=action.entity_original,
                            entity_standardized_candidate=action.entity_standardized_candidate,
                            role=action.role,
                            logic="action",
                            logic_structured=logic_structured,
                        )
                    )
            if concepts:
                if incremental_review_enabled:
                    try:
                        draft_rules_json = json.dumps(
                            rules_serialized, ensure_ascii=False, sort_keys=True
                        )
                        review_input = (
                            f"[DRAFT_RULES]\n{draft_rules_json}\n[/DRAFT_RULES]\n"
                            f"{tagged_text}"
                        )
                        reviewed_result = b.ExtractConcepts(
                            review_input, baml_options=baml_options
                        )
                        _ = self._serialize_baml_result(reviewed_result)
                        reviewed_concepts = _concepts_from_extract_concepts_result(
                            reviewed_result
                        )
                        if reviewed_concepts:
                            return reviewed_concepts
                    except Exception as exc:
                        logger.warning(
                            "Incremental review pass failed; using first-pass rules. Error: %s",
                            exc,
                        )
                return concepts
        except Exception as exc:
            logger.warning(
                "BAML ExtractRulesV2 failed; falling back to ExtractConcepts. Error: %s",
                exc,
            )

        try:
            result = b.ExtractConcepts(tagged_text, baml_options=baml_options)
        except Exception as exc:
            logger.warning(
                "BAML extraction failed; skipping sentence. Error: %s",
                exc,
            )
            return []
        _ = self._serialize_baml_result(result)
        return _concepts_from_extract_concepts_result(result)

    def _merge_extracted_concepts(
        self, primary: List[ExtractedConcept], secondary: List[ExtractedConcept]
    ) -> List[ExtractedConcept]:
        merged: List[ExtractedConcept] = []
        seen = set()

        def concept_key(
            concept: ExtractedConcept,
        ) -> Tuple[str, str, str, str, str, str]:
            logic = concept.logic_structured or {}
            return (
                self._normalize(concept.entity_standardized_candidate or ""),
                (concept.role or "").strip(),
                str(logic.get("operator") or ""),
                str(logic.get("threshold") or ""),
                str(logic.get("unit") or ""),
                str(logic.get("context") or ""),
            )

        for concept in primary + secondary:
            key = concept_key(concept)
            if key in seen:
                continue
            seen.add(key)
            merged.append(concept)
        return merged

    def _drop_redundant_compound_conditions(
        self, concepts: List[ExtractedConcept]
    ) -> List[ExtractedConcept]:
        def is_condition(concept: ExtractedConcept) -> bool:
            role = (concept.role or "").strip()
            side = (concept.logic or "").strip().lower()
            return (
                role in {"ClinicalCondition", "ClinicalParameter"}
                or side == "condition"
            )

        condition_concepts = [c for c in concepts if is_condition(c)]
        if not condition_concepts:
            return concepts

        normalized_conditions = [
            self._normalize(c.entity_standardized_candidate or c.entity_original or "")
            for c in condition_concepts
        ]

        filtered: List[ExtractedConcept] = []
        for concept in concepts:
            role = (concept.role or "").strip()
            if not is_condition(concept):
                filtered.append(concept)
                continue
            name = concept.entity_standardized_candidate or concept.entity_original
            normalized = self._normalize(name or "")
            if "," not in normalized and " and " not in normalized:
                filtered.append(concept)
                continue
            parts = [
                part.strip()
                for part in re.split(r"\s*,\s*|\s+and\s+", normalized)
                if part.strip()
            ]
            if len(parts) < 2:
                filtered.append(concept)
                continue
            matches = 0
            for other in normalized_conditions:
                if other == normalized:
                    continue
                if any(part in other for part in parts):
                    matches += 1
            if matches >= 2:
                continue
            filtered.append(concept)

        return filtered

    def _explode_or_conditions(
        self, concepts: List[ExtractedConcept]
    ) -> List[ExtractedConcept]:
        expanded: List[ExtractedConcept] = []
        for concept in concepts:
            side = (concept.logic or "").strip().lower()
            if (concept.role or "").strip() not in {
                "ClinicalCondition",
                "ClinicalParameter",
            } and side != "condition":
                expanded.append(concept)
                continue
            text = concept.entity_standardized_candidate or concept.entity_original
            if not text:
                expanded.append(concept)
                continue
            if " or " not in text.lower():
                expanded.append(concept)
                continue
            parts = [
                part.strip() for part in re.split(r"\bor\b", text, flags=re.IGNORECASE)
            ]
            parts = [part for part in parts if part]
            if len(parts) < 2:
                expanded.append(concept)
                continue
            for idx, part in enumerate(parts, start=1):
                logic_structured = dict(concept.logic_structured or {})
                logic_structured["logic_type"] = "OR"
                logic_structured["logic_group"] = "or_1"
                logic_structured = self._filter_logic_structured(logic_structured)
                expanded.append(
                    ExtractedConcept(
                        entity_original=concept.entity_original,
                        entity_standardized_candidate=part,
                        role=concept.role,
                        logic=concept.logic,
                        logic_structured=logic_structured,
                    )
                )
        return expanded

    def extract_and_ground(
        self, sentence: str, source_type: str, guideline_title: str
    ) -> Tuple[List[ExtractedConcept], List[GroundedConcept]]:
        if "DOC_FORMAT: docling_json" in (sentence or ""):
            filtered_sentence = (sentence or "").strip()
        else:
            filtered_sentence = self._filter_text_block(sentence)
        if not filtered_sentence:
            return [], []
        extracted_main = self.extract_concepts(
            filtered_sentence, source_type, guideline_title, focus="MAIN"
        )
        extracted_population = self.extract_concepts(
            filtered_sentence, source_type, guideline_title, focus="POPULATION"
        )
        extracted = self._merge_extracted_concepts(extracted_main, extracted_population)
        extracted = self._explode_or_conditions(extracted)
        extracted = self._drop_redundant_compound_conditions(extracted)
        self._log_extracted_concepts(extracted)
        grounded: List[GroundedConcept] = []
        has_clinical_anchor = any(
            c.role in {"ClinicalCondition", "Medication", "Procedure"}
            for c in extracted
        )

        for concept in extracted:
            if (concept.role or "").strip() == "Recommendation":
                concept.role = "ClinicalCondition"
            if (concept.role or "").strip() == "Other":
                grounded.append(
                    GroundedConcept(
                        entity_original=concept.entity_original,
                        entity_standardized_candidate=concept.entity_standardized_candidate,
                        role=concept.role,
                        logic=concept.logic,
                        logic_structured=concept.logic_structured,
                        snomed_id=None,
                        preferred_term=None,
                        alt_names=[],
                        score=0.0,
                        taxonomy_path=[],
                        target_label=self._fallback_target_label_for_role("Other"),
                    )
                )
                continue
            cached = self.index.lookup(concept.entity_standardized_candidate)
            if cached:
                cache_term = cached.get("preferred_term") or cached.get(
                    "entity_standardized_candidate"
                )
                cache_tokens = set(
                    self._important_tokens(
                        concept.entity_standardized_candidate
                        or concept.entity_original
                        or ""
                    )
                )
                if (
                    cache_tokens
                    and self._token_overlap_ratio(cache_tokens, cache_term) < 0.5
                ):
                    cached = None
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
                        entity_original=concept.entity_original,
                        entity_standardized_candidate=concept.entity_standardized_candidate,
                        role=concept.role,
                        logic=concept.logic,
                        logic_structured=concept.logic_structured,
                        snomed_id=cached.get("snomed_id"),
                        preferred_term=cached.get("preferred_term"),
                        alt_names=cached.get("alt_names", []),
                        score=cached.get("score", 1.0),
                        taxonomy_path=cached.get("taxonomy_path", []),
                        target_label=cached.get("target_label"),
                    )
                )
                continue
            search_term = concept.entity_standardized_candidate
            if search_term and "scheduled" in search_term.lower():
                search_term = re.sub(
                    r"\bscheduled\b", "", search_term, flags=re.IGNORECASE
                ).strip()
            concept_id, preferred_term, score = self._search_best_concept(
                search_term, concept.role
            )
            path_ids = self._get_taxonomy_path_cached(concept_id)
            target_label = self._resolve_target_label(path_ids)
            if target_label is None and concept.role:
                target_label = self._resolve_target_label_for_role(
                    concept.role, path_ids
                )
            if target_label is None and concept.role and len(path_ids) <= 1:
                target_label = self._fallback_target_label_for_role(concept.role)
            taxonomy_path = self._format_taxonomy_path(path_ids)
            alt_names: List[str] = []

            if concept_id is None or score < self.min_match_score:
                concept_id = None
                preferred_term = None
                score = 0.0
                path_ids = []
                taxonomy_path = []
                alt_names = []
                target_label = self._fallback_target_label_for_role(concept.role)
            else:
                alt_names = self._get_alt_names(concept_id, preferred_term)

            if self._should_skip_concept(
                concept, score, target_label, has_clinical_anchor, allow_unmapped=True
            ):
                continue

            grounded_concept = GroundedConcept(
                entity_original=concept.entity_original,
                entity_standardized_candidate=concept.entity_standardized_candidate,
                role=concept.role,
                logic=concept.logic,
                logic_structured=concept.logic_structured,
                snomed_id=concept_id,
                preferred_term=preferred_term,
                alt_names=alt_names,
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
                    "alt_names": alt_names,
                    "score": score,
                    "taxonomy_path": taxonomy_path,
                    "target_label": target_label,
                }
            )
            logger.info(
                "Index output entry: %s",
                json.dumps(
                    {
                        "entity_standardized_candidate": concept.entity_standardized_candidate,
                        "snomed_id": concept_id,
                        "preferred_term": preferred_term,
                        "alt_names": alt_names,
                        "score": score,
                        "taxonomy_path": taxonomy_path,
                        "target_label": target_label,
                    }
                ),
            )

        self.index.save()
        self._log_grounded_concepts(grounded)
        return extracted, grounded

    def ground_sentence(
        self, sentence: str, source_type: str, guideline_title: str
    ) -> List[GroundedConcept]:
        _, grounded = self.extract_and_ground(sentence, source_type, guideline_title)
        return grounded

    def build_index_from_dirs(
        self,
        chunks_dir: Optional[str],
        tables_dir: Optional[str],
        guideline_title: str,
        rules_out_path: Optional[str] = None,
    ) -> None:
        run_started_at = datetime.now().strftime("%Y%m%d_%H%M%S")
        timestamped_index_path = None
        if self.index.index_path:
            base, ext = os.path.splitext(self.index.index_path)
            timestamped_index_path = f"{base}_{run_started_at}{ext or '.json'}"
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
                extracted, grounded = self.extract_and_ground(
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
                    self._write_rules_entries_from_extracted(
                        rules_file,
                        extracted,
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
                extracted, grounded = self.extract_and_ground(
                    text, source_type="table", guideline_title=guideline_title
                )
                self._log_grounded_summary(
                    chunk_id=filename,
                    source_type="table",
                    grounded=grounded,
                )
                if rules_file:
                    self._write_rules_entries_from_extracted(
                        rules_file,
                        extracted,
                        chunk_id=filename,
                        source_context=path,
                        source_type="table",
                        guideline_title=guideline_title,
                    )
        if rules_file:
            rules_file.close()
        if timestamped_index_path:
            self.index.save_as(timestamped_index_path)

    def build_index_from_docling_tables(
        self,
        docling_table_jsons: List[str],
        guideline_title: str,
        rules_out_path: Optional[str] = None,
        table_id: Optional[str] = None,
        footnotes: Optional[str] = None,
        whole_table: bool = False,
    ) -> None:
        run_started_at = datetime.now().strftime("%Y%m%d_%H%M%S")
        timestamped_index_path = None
        if self.index.index_path:
            base, ext = os.path.splitext(self.index.index_path)
            timestamped_index_path = f"{base}_{run_started_at}{ext or '.json'}"

        rules_file = None
        if rules_out_path:
            os.makedirs(os.path.dirname(rules_out_path), exist_ok=True)
            rules_file = open(rules_out_path, "w", encoding="utf-8")

        table_jsons: List[Dict] = []
        for table_json_path in docling_table_jsons:
            with open(table_json_path, "r", encoding="utf-8") as f:
                table_jsons.append(json.load(f))

        logger.info("Docling table inputs: %s", ";".join(docling_table_jsons))
        logger.info("Docling table header: Columns: Recommendations | Class | Level")
        # Footnotes content is large and not logged.

        if whole_table:
            table_text = self._format_docling_table_full(
                table_jsons, footnotes=footnotes
            )
            if table_id:
                table_text = f"DOC_TABLE: {table_id}\n" + table_text
            chunk_label = f"{table_id}:whole" if table_id else "docling_table_whole"
            extracted, grounded = self.extract_and_ground(
                table_text, source_type="table", guideline_title=guideline_title
            )
            self._log_grounded_summary(
                chunk_id=chunk_label,
                source_type="table",
                grounded=grounded,
            )
            if rules_file:
                self._write_rules_entries_from_extracted(
                    rules_file,
                    extracted,
                    chunk_id=chunk_label,
                    source_context=";".join(docling_table_jsons),
                    source_type="table",
                    guideline_title=guideline_title,
                )
        else:
            rows = self._format_docling_table_rows(table_jsons, footnotes=footnotes)
            for row_id, row_text in rows:
                if table_id:
                    row_text = f"DOC_TABLE: {table_id}\nDOC_ROW: {row_id}\n" + row_text
                chunk_label = f"{table_id}:{row_id}" if table_id else row_id
                logger.info("Docling table row input %s", chunk_label)
                extracted, grounded = self.extract_and_ground(
                    row_text, source_type="table", guideline_title=guideline_title
                )
                self._log_grounded_summary(
                    chunk_id=chunk_label,
                    source_type="table",
                    grounded=grounded,
                )
                if rules_file:
                    self._write_rules_entries_from_extracted(
                        rules_file,
                        extracted,
                        chunk_id=chunk_label,
                        source_context=";".join(docling_table_jsons),
                        source_type="table",
                        guideline_title=guideline_title,
                    )
        if rules_file:
            rules_file.close()
        if timestamped_index_path:
            self.index.save_as(timestamped_index_path)

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
        # Per-concept grounded logs removed to reduce noise.

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
            logic_structured = dict(concept.logic_structured or {})
            logic_structured = self._filter_logic_structured(logic_structured)
            if (concept.role or "").strip() in {
                "ClinicalCondition",
                "ClinicalParameter",
            } and not logic_structured.get("logic_type"):
                logic_structured["logic_type"] = "AND"
            if (concept.role or "").strip() in {
                "ClinicalCondition",
                "ClinicalParameter",
            } and not logic_structured.get("logic_group"):
                logic_structured["logic_group"] = "and_1"
            entry = {
                "entity_standardized_candidate": concept.entity_standardized_candidate,
                "snomed_id": concept.snomed_id,
                "role": concept.role,
                "target_label": concept.target_label,
                "logic_structured": logic_structured,
                "chunk_id": chunk_id,
                "source_context": source_context,
                "source_type": source_type,
                "guideline_title": guideline_title,
            }
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def _write_rules_entries_from_extracted(
        self,
        fh,
        extracted: List[ExtractedConcept],
        chunk_id: str,
        source_context: str,
        source_type: str,
        guideline_title: str,
    ) -> None:
        for concept in extracted:
            cached = self.index.lookup(concept.entity_standardized_candidate)
            snomed_id = cached.get("snomed_id") if cached else None
            target_label = None
            if cached:
                target_label = cached.get("target_label")
            if not target_label:
                target_label = self._fallback_target_label_for_role(concept.role)
            role = concept.role
            if target_label == "ClinicalParameter":
                role = "ClinicalParameter"
            logic_structured = dict(concept.logic_structured or {})
            logic_structured = self._filter_logic_structured(logic_structured)
            if (role or "").strip() in {
                "ClinicalCondition",
                "ClinicalParameter",
            } and not logic_structured.get("logic_type"):
                logic_structured["logic_type"] = "AND"
            if (role or "").strip() in {
                "ClinicalCondition",
                "ClinicalParameter",
            } and not logic_structured.get("logic_group"):
                logic_structured["logic_group"] = "and_1"
            entry = {
                "entity_original": concept.entity_original,
                "entity_standardized_candidate": concept.entity_standardized_candidate,
                "snomed_id": snomed_id,
                "role": role,
                "target_label": target_label,
                "logic_structured": logic_structured,
                "chunk_id": chunk_id,
                "source_context": source_context,
                "source_type": source_type,
                "guideline_title": guideline_title,
            }
            # Detailed rules entry logs removed to reduce noise.
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def _resolve_target_label_for_role(
        self, role: str, path_ids: List[int]
    ) -> Optional[str]:
        role_map = {
            "ClinicalCondition": "ClinicalCondition",
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

    def _allowed_root_concepts_for_role(self, role: str) -> set:
        role_map = {
            "ClinicalCondition": "ClinicalCondition",
            "ClinicalParameter": "ClinicalParameter",
            "Medication": "Medication",
            "Procedure": "Procedure",
            "Other": "ClinicalCondition",
        }
        label = role_map.get(role)
        if not label:
            return set()
        return set(self._allowed_root_concepts_by_label.get(label, set()))

    def _fallback_target_label_for_role(self, role: str) -> Optional[str]:
        role_map = {
            "ClinicalCondition": "ClinicalCondition",
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
    "--docling-table-json",
    multiple=True,
    help="Path(s) to docling table JSON file(s) (table_*.json)",
)
@click.option(
    "--docling-table-id",
    default=None,
    help="Optional table identifier for docling JSON provenance",
)
@click.option(
    "--docling-footnotes",
    default=None,
    help="Optional footnotes text appended to each row",
)
@click.option(
    "--docling-footnotes-path",
    default=None,
    help="Path to a file containing footnotes text",
)
@click.option(
    "--docling-whole-table/--no-docling-whole-table",
    default=False,
    help="Process docling table as a single combined input instead of per row",
)
@click.option(
    "--min-match-score",
    default=DEFAULT_MIN_MATCH_SCORE,
    show_default=True,
    type=float,
    help="Minimum similarity score for SNOMED grounding",
)
@click.option(
    "--domain-filter/--no-domain-filter",
    default=True,
    show_default=True,
    help="Filter candidate SNOMED concepts by allowed domain roots",
)
@click.option(
    "--semantic-tag-filter/--no-semantic-tag-filter",
    default=False,
    show_default=True,
    help="Filter candidate SNOMED concepts by allowed semantic tags",
)
@click.option(
    "--off-domain-min-score",
    default=None,
    type=float,
    help="Allow off-domain candidates if score meets this threshold",
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
    docling_table_json: Tuple[str, ...],
    docling_table_id: Optional[str],
    docling_footnotes: Optional[str],
    docling_footnotes_path: Optional[str],
    docling_whole_table: bool,
    min_match_score: float,
    domain_filter: bool,
    semantic_tag_filter: bool,
    off_domain_min_score: Optional[float],
    guideline_title: str,
    model: str,
    node: str,
    port: Optional[int],
):
    service = GuidelineGraphBuilder(
        config_path=config_path,
        model=model,
        node=node,
        port=port,
        index_path=index_path,
        abbrv_path=abbrv_path,
        min_match_score=min_match_score,
        enable_domain_filter=domain_filter,
        enable_semantic_tag_filter=semantic_tag_filter,
        off_domain_min_score=off_domain_min_score,
    )
    footnotes = docling_footnotes
    if docling_footnotes_path:
        with open(docling_footnotes_path, "r", encoding="utf-8") as f:
            footnotes = f.read().strip()
    if docling_table_json:
        service.build_index_from_docling_tables(
            list(docling_table_json),
            guideline_title,
            rules_out_path=rules_out_path,
            table_id=docling_table_id,
            footnotes=footnotes,
            whole_table=docling_whole_table,
        )
        return
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
