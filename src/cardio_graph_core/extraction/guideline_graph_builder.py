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
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import click
import yaml

from cardio_graph_core.extraction.clients import create_client_registry, ip_dict
from cardio_graph_core.extraction.vector_candidate_retriever import (
    Neo4jVectorCandidateRetriever,
    VectorRetrieverConfig,
)
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
GENERIC_CONCEPT_TOKENS = {
    "clinical",
    "condition",
    "disease",
    "disorder",
    "heart",
    "coronary",
    "artery",
    "therapy",
    "medical",
    "procedure",
    "patient",
    "risk",
    "syndrome",
    "revascularization",
    "intervention",
}
DISALLOWED_SEMANTIC_TAGS = {
    "occupation",
    "ethnic group finding",
    "event",
}
ALLOWED_SEMANTIC_TAGS_BY_ROLE = {
    "ClinicalCondition": {"disorder", "finding"},
    "ClinicalParameter": {"observable entity"},
    "Medication": {"substance", "product"},
    "Procedure": {"procedure"},
    "Qualifier Value": {"qualifier value"},
}
ALLOWED_ROLES = {
    "ClinicalCondition",
    "ClinicalParameter",
    "Medication",
    "Procedure",
    "Qualifier Value",
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

FEWSHOT_EXAMPLES_TABLE17_TABLE8_V1 = """
[FEWSHOT_EXAMPLES]
Purpose: Demonstrate robust left/right rule structure, junction handling, and concise clinical concept representation.

Example 1 (Table17-style, cohort + OR junction + single action):
Input sentence:
"In chronic coronary syndrome patients with prior myocardial infarction or remote percutaneous coronary intervention, aspirin 75-100 mg daily is recommended lifelong."

Expected structure (pattern-level):
- conditions:
    - role: ClinicalCondition, entity: chronic coronary syndrome, operator: PRESENT, logic_type: AND, logic_group: and_1
    - role: ClinicalCondition, entity: prior myocardial infarction, operator: PRESENT, logic_type: OR, logic_group: or_1
    - role: Procedure, entity: percutaneous coronary intervention, context: remote, operator: PRESENT, logic_type: OR, logic_group: or_1
- actions:
    - role: Medication, entity: aspirin, context: 75-100 mg daily lifelong, strength: Class I, level: A, direction: POSITIVE

Example 2 (Table8-style, OR+AND cohort + dual action):
Input sentence:
"In patients with chronic coronary disease or symptomatic peripheral arterial disease at high ischaemic risk, rivaroxaban 2.5 mg twice daily plus aspirin 100 mg once daily should be used."

Expected structure (pattern-level):
- conditions:
    - role: ClinicalCondition, entity: chronic coronary disease, operator: PRESENT, logic_type: OR, logic_group: or_1
    - role: ClinicalCondition, entity: symptomatic peripheral arterial disease, operator: PRESENT, logic_type: OR, logic_group: or_1
    - role: ClinicalCondition, entity: high ischaemic risk, operator: PRESENT, logic_type: AND, logic_group: and_1
- actions:
    - role: Medication, entity: rivaroxaban, context: 2.5 mg twice daily, direction: POSITIVE
    - role: Medication, entity: aspirin, context: 100 mg once daily, direction: POSITIVE

Hard constraints illustrated by both examples:
- MAIN focus must contain at least one condition and one action.
- Do not output action-only rules.
- Keep eligibility/cohort phrase on the left side; keep intervention on the right side.
[/FEWSHOT_EXAMPLES]
""".strip()


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
        nodes = self.config.get("nodes") or []

        def _node_attr_names(label: str) -> set:
            for node in nodes:
                if (node.get("label") or "").strip() != label:
                    continue
                attrs = node.get("attributes") or []
                return {
                    (attr.get("name") or "").strip()
                    for attr in attrs
                    if (attr.get("name") or "").strip()
                }
            return set()

        def _node_attr_allowed(label: str, attr_name: str) -> set:
            for node in nodes:
                if (node.get("label") or "").strip() != label:
                    continue
                attrs = node.get("attributes") or []
                for attr in attrs:
                    if (attr.get("name") or "").strip() != attr_name:
                        continue
                    allowed = attr.get("allowed") or []
                    return {
                        str(value).strip()
                        for value in allowed
                        if value is not None and str(value).strip()
                    }
            return set()

        decision_attr_names = _node_attr_names("DecisionNode")
        recommendation_attr_names = _node_attr_names("RecommendationNode")
        extraction_logic_keys = {
            "operator",
            "threshold",
            "unit",
            "context",
            "logic_type",
            "logic_group",
            "strength",
            "level",
            "direction",
        }
        profile_allowed_logic_keys = (
            {"logic_group"} | decision_attr_names | recommendation_attr_names
        )
        derived_allowed_logic_keys = extraction_logic_keys & profile_allowed_logic_keys
        self._allowed_logic_structured_keys = (
            derived_allowed_logic_keys or extraction_logic_keys
        )
        self._allowed_operator_values = _node_attr_allowed("DecisionNode", "operator")
        self._allowed_logic_type_values = _node_attr_allowed(
            "DecisionNode", "logic_type"
        )
        self._allowed_direction_values = _node_attr_allowed(
            "RecommendationNode", "direction"
        )
        self._allowed_strength_values = _node_attr_allowed(
            "RecommendationNode", "strength"
        )
        self._allowed_level_values = _node_attr_allowed("RecommendationNode", "level")
        self.root_concepts = self._collect_root_concepts(self.mapping_rules)

        self.client_registry = create_client_registry(model, node, port)

        # Establish SNOMED connectivity lazily so extraction-only flows can run
        # without paying grounding setup cost.
        self.snomed_explorer: Optional[SnomedExplorer] = None

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
        self.enable_vector_grounding = (
            os.environ.get("CARDIO_GRAPH_GROUNDING_ENABLE_VECTOR", "false") or "false"
        ).strip().lower() in {"1", "true", "yes", "on"}
        self.vector_top_k = int(
            os.environ.get("CARDIO_GRAPH_GROUNDING_VECTOR_TOP_K", "40") or "40"
        )
        self.vector_rerank_weight = float(
            os.environ.get("CARDIO_GRAPH_GROUNDING_VECTOR_RERANK_WEIGHT", "0.10")
            or "0.10"
        )
        self.vector_min_lexical_for_bonus = float(
            os.environ.get(
                "CARDIO_GRAPH_GROUNDING_VECTOR_MIN_LEXICAL_FOR_BONUS", "0.70"
            )
            or "0.70"
        )
        self.vector_bonus_cap = float(
            os.environ.get("CARDIO_GRAPH_GROUNDING_VECTOR_BONUS_CAP", "0.12") or "0.12"
        )
        self.vector_tie_epsilon = float(
            os.environ.get("CARDIO_GRAPH_GROUNDING_VECTOR_TIE_EPSILON", "0.002")
            or "0.002"
        )
        self.min_weighted_query_coverage = float(
            os.environ.get("CARDIO_GRAPH_GROUNDING_MIN_WEIGHTED_QUERY_COVERAGE", "0.45")
            or "0.45"
        )
        self.low_coverage_penalty = float(
            os.environ.get("CARDIO_GRAPH_GROUNDING_LOW_COVERAGE_PENALTY", "0.12")
            or "0.12"
        )
        self.missing_discriminative_penalty = float(
            os.environ.get(
                "CARDIO_GRAPH_GROUNDING_MISSING_DISCRIMINATIVE_PENALTY", "0.10"
            )
            or "0.10"
        )
        self.enable_grounding_candidate_debug = (
            os.environ.get("CARDIO_GRAPH_GROUNDING_DEBUG_TOP_CANDIDATES", "false")
            or "false"
        ).strip().lower() in {"1", "true", "yes", "on"}
        self.vector_retriever: Optional[Neo4jVectorCandidateRetriever] = None
        if self.enable_vector_grounding:
            try:
                embedding_node = (
                    os.environ.get("CARDIO_GRAPH_GROUNDING_EMBEDDING_NODE", "g4")
                    or "g4"
                ).strip()
                embedding_port = int(
                    os.environ.get("CARDIO_GRAPH_GROUNDING_EMBEDDING_PORT", "11434")
                    or "11434"
                )
                default_embedding_url = f"http://{ip_dict.get(embedding_node, embedding_node)}:{embedding_port}"
                vector_config = VectorRetrieverConfig(
                    uri=(
                        os.environ.get(
                            "CARDIO_GRAPH_GROUNDING_VECTOR_URI",
                            "bolt://neo4j-dev3.internal:7687",
                        )
                        or "bolt://neo4j-dev3.internal:7687"
                    ).strip(),
                    user=(
                        os.environ.get("CARDIO_GRAPH_GROUNDING_VECTOR_USER", "neo4j")
                        or "neo4j"
                    ).strip(),
                    password=(
                        os.environ.get("CARDIO_GRAPH_GROUNDING_VECTOR_PASSWORD", "")
                        or ""
                    ).strip(),
                    index_name=(
                        os.environ.get(
                            "CARDIO_GRAPH_GROUNDING_VECTOR_INDEX",
                            "snomed_term_embeddings",
                        )
                        or "snomed_term_embeddings"
                    ).strip(),
                    embedding_url=(
                        os.environ.get(
                            "CARDIO_GRAPH_GROUNDING_EMBEDDING_URL",
                            default_embedding_url,
                        )
                        or default_embedding_url
                    ).strip(),
                    embedding_model=(
                        os.environ.get(
                            "CARDIO_GRAPH_GROUNDING_EMBEDDING_MODEL", "Qwen3embed"
                        )
                        or "Qwen3embed"
                    ).strip(),
                    top_k=self.vector_top_k,
                    timeout_seconds=int(
                        os.environ.get("CARDIO_GRAPH_GROUNDING_EMBEDDING_TIMEOUT", "20")
                        or "20"
                    ),
                )
                if vector_config.embedding_model:
                    self.vector_retriever = Neo4jVectorCandidateRetriever(vector_config)
                    logger.info(
                        "Vector grounding enabled (index=%s, top_k=%d)",
                        vector_config.index_name,
                        self.vector_top_k,
                    )
                else:
                    logger.warning(
                        "Vector grounding enabled but no embedding model set; disabling vector retrieval"
                    )
                    self.enable_vector_grounding = False
            except Exception as exc:
                logger.warning(
                    "Failed to initialize vector grounding retriever: %s", exc
                )
                self.enable_vector_grounding = False

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
        filtered = {
            key: value
            for key, value in payload.items()
            if key in self._allowed_logic_structured_keys
        }

        filtered["operator"] = self._normalize_enum_value(
            filtered.get("operator"), self._allowed_operator_values
        )
        filtered["logic_type"] = self._normalize_enum_value(
            filtered.get("logic_type"), self._allowed_logic_type_values
        )
        filtered["direction"] = self._normalize_enum_value(
            filtered.get("direction"), self._allowed_direction_values
        )
        filtered["strength"] = self._normalize_strength_value(
            filtered.get("strength"), self._allowed_strength_values
        )
        filtered["level"] = self._normalize_enum_value(
            filtered.get("level"), self._allowed_level_values
        )
        return filtered

    def _normalize_enum_value(self, value: Any, allowed_values: set) -> Optional[str]:
        if not allowed_values:
            text = (str(value or "") or "").strip()
            return text or None
        text = (str(value or "") or "").strip()
        if not text:
            return None
        if text in allowed_values:
            return text
        upper = text.upper()
        if upper in allowed_values:
            return upper
        return None

    def _normalize_strength_value(
        self, value: Any, allowed_values: set
    ) -> Optional[str]:
        text = (str(value or "") or "").strip()
        if not text:
            return None
        direct = self._normalize_enum_value(text, allowed_values)
        if direct is not None:
            return direct

        if text.lower().startswith("class "):
            suffix = text.split(" ", 1)[1].strip()
            candidate = f"Class {suffix}"
            direct = self._normalize_enum_value(candidate, allowed_values)
            if direct is not None:
                return direct

        prefixed = f"Class {text}"
        direct = self._normalize_enum_value(prefixed, allowed_values)
        if direct is not None:
            return direct

        return None

    def _normalize_extracted_role(self, role: Any) -> Optional[str]:
        text = (str(role or "") or "").strip()
        if not text:
            return None
        if text in ALLOWED_ROLES:
            return text
        if text in BLOCKED_ROLES:
            return None
        normalized_map = {
            "clinicalcondition": "ClinicalCondition",
            "clinicalparameter": "ClinicalParameter",
            "medication": "Medication",
            "procedure": "Procedure",
            "qualifiervalue": "Qualifier Value",
            "other": "Other",
        }
        return normalized_map.get(text.replace(" ", "").lower())

    def _is_nonempty_concept(self, concept: Any) -> bool:
        if concept is None:
            return False
        entity_original = (getattr(concept, "entity_original", None) or "").strip()
        entity_standardized = (
            getattr(concept, "entity_standardized_candidate", None) or ""
        ).strip()
        role = (getattr(concept, "role", None) or "").strip()
        if role.lower() == "string":
            return False
        return bool(role and (entity_original or entity_standardized))

    def _ensure_snomed_connected(self) -> SnomedExplorer:
        if self.snomed_explorer is None:
            self.snomed_explorer = SnomedExplorer()
            self.snomed_explorer.connect()
        return self.snomed_explorer

    def _is_population_focus(self, focus: Optional[str]) -> bool:
        return (focus or "").strip().upper() == "POPULATION"

    def _require_both_sides_for_main(self) -> bool:
        return os.environ.get(
            "CARDIO_GRAPH_REQUIRE_BOTH_SIDES_MAIN", "true"
        ).strip().lower() not in {"0", "false", "no", "off"}

    def _concept_side(self, concept: Any) -> Optional[str]:
        raw_logic = (getattr(concept, "logic", None) or "").strip().lower()
        if raw_logic in {"condition", "action"}:
            return raw_logic
        role = (getattr(concept, "role", None) or "").strip()
        if role in {"ClinicalCondition", "ClinicalParameter", "Qualifier Value"}:
            return "condition"
        if role in {"Medication", "Procedure"}:
            return "action"
        return None

    def _validate_extracted_concepts(
        self, concepts: List[ExtractedConcept], focus: Optional[str]
    ) -> List[ExtractedConcept]:
        if not concepts:
            return []
        is_population_focus = self._is_population_focus(focus)

        condition_concepts = [
            concept
            for concept in concepts
            if self._is_nonempty_concept(concept)
            and self._concept_side(concept) == "condition"
        ]
        action_concepts = [
            concept
            for concept in concepts
            if self._is_nonempty_concept(concept)
            and self._concept_side(concept) == "action"
        ]

        if is_population_focus:
            return condition_concepts

        if self._require_both_sides_for_main():
            if not condition_concepts or not action_concepts:
                return []

        return condition_concepts + action_concepts

    def _validate_extracted_rules(
        self, rules: List[Any], focus: Optional[str]
    ) -> List[Any]:
        valid_rules: List[Any] = []
        is_population_focus = self._is_population_focus(focus)
        require_both_sides_main = self._require_both_sides_for_main()

        for rule in rules or []:
            conditions = [
                condition
                for condition in (getattr(rule, "conditions", []) or [])
                if self._is_nonempty_concept(condition)
            ]
            actions = [
                action
                for action in (getattr(rule, "actions", []) or [])
                if self._is_nonempty_concept(action)
            ]

            if not conditions and not actions:
                continue

            if is_population_focus:
                if not conditions:
                    continue
            elif require_both_sides_main:
                if not conditions or not actions:
                    continue

            valid_rules.append(rule)
        return valid_rules

    def _normalize(self, text: str) -> str:
        normalized = unicodedata.normalize("NFKD", str(text or ""))
        normalized = normalized.encode("ascii", "ignore").decode("ascii")
        normalized = normalized.lower()
        normalized = re.sub(r"[/_\-]", " ", normalized)
        normalized = re.sub(r"[^a-z0-9()%\s]", " ", normalized)
        return " ".join(normalized.strip().split())

    def _normalize_token(self, token: str) -> str:
        token = self._normalize(token)
        if len(token) <= 4:
            return token
        if token.endswith("ies") and len(token) > 5:
            return token[:-3] + "y"
        if (
            token.endswith("es")
            and len(token) > 5
            and token.endswith(("ches", "shes", "xes", "zes", "oes", "sses"))
        ):
            return token[:-2]
        if token.endswith("s") and len(token) > 4:
            return token[:-1]
        return token

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

    def _query_variants(self, term: str) -> List[str]:
        variants = []

        def add(value: str) -> None:
            value = " ".join(str(value or "").strip().split())
            if value:
                variants.append(value)

        add(term)
        stripped = re.sub(r"\s*\([^)]*\)\s*", " ", term).strip()
        add(stripped)

        normalized = self._normalize(term)
        add(normalized)

        de_prefixed = re.sub(
            r"^(patients?|subjects?)\s+(scheduled\s+for|with|having)\s+",
            "",
            normalized,
            flags=re.IGNORECASE,
        ).strip()
        add(de_prefixed)
        add(re.sub(r"\bpatients?\b", "", normalized, flags=re.IGNORECASE).strip())

        tokenized = [self._normalize_token(t) for t in normalized.split()]
        add(" ".join([t for t in tokenized if t]))

        seen = set()
        deduped = []
        for variant in variants:
            key = self._normalize(variant)
            if not key or key in seen:
                continue
            seen.add(key)
            deduped.append(variant)
        return deduped

    def _important_tokens(self, text: str) -> List[str]:
        tokens = re.findall(r"[a-z0-9]+", self._normalize(text))
        normalized_tokens = [self._normalize_token(t) for t in tokens]
        return [t for t in normalized_tokens if len(t) > 2 and t not in STOPWORD_TOKENS]

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
        seq = SequenceMatcher(None, q, c).ratio()
        partial = 0.0
        if q in c or c in q:
            partial = min(len(q), len(c)) / max(len(q), len(c))
        q_tokens = set(self._important_tokens(q))
        c_tokens = set(self._important_tokens(c))
        token_jaccard = 0.0
        if q_tokens and c_tokens:
            token_jaccard = len(q_tokens & c_tokens) / len(q_tokens | c_tokens)
        coverage = self._weighted_query_coverage(q_tokens, c_tokens)
        combined = 0.45 * coverage + 0.25 * token_jaccard + 0.20 * seq + 0.10 * partial
        return min(1.0, max(combined, coverage, token_jaccard))

    def _token_weight(self, token: str) -> float:
        if not token:
            return 0.0
        if token in GENERIC_CONCEPT_TOKENS:
            return 0.35
        return min(1.5, 0.8 + (len(token) / 12.0))

    def _weighted_query_coverage(
        self, query_tokens: set[str], candidate_tokens: set[str]
    ) -> float:
        if not query_tokens:
            return 0.0
        denom = sum(self._token_weight(token) for token in query_tokens)
        if denom <= 0:
            return 0.0
        numer = sum(
            self._token_weight(token)
            for token in query_tokens
            if token in candidate_tokens
        )
        return numer / denom

    def _discriminative_query_tokens(self, query_tokens: set[str]) -> set[str]:
        return {
            token
            for token in query_tokens
            if token not in GENERIC_CONCEPT_TOKENS and len(token) >= 5
        }

    def _vector_candidates(
        self, term: str
    ) -> Tuple[List[Dict[str, Any]], Dict[int, float]]:
        if not self.enable_vector_grounding or not self.vector_retriever:
            return [], {}
        try:
            candidates = self.vector_retriever.retrieve(term, top_k=self.vector_top_k)
        except Exception as exc:
            logger.warning("Vector retrieval failed for '%s': %s", term, exc)
            return [], {}

        vector_score_by_concept: Dict[int, float] = {}
        for row in candidates:
            concept_id = row.get("conceptid")
            if concept_id is None:
                continue
            try:
                concept_id = int(concept_id)
            except (TypeError, ValueError):
                continue
            row_score = float(row.get("vector_score") or 0.0)
            if concept_id not in vector_score_by_concept:
                vector_score_by_concept[concept_id] = row_score
            else:
                vector_score_by_concept[concept_id] = max(
                    vector_score_by_concept[concept_id], row_score
                )
        return candidates, vector_score_by_concept

    def _token_overlap_ratio(self, tokens: set, term: Optional[str]) -> float:
        if not tokens or not term:
            return 0.0
        term_tokens = set(self._important_tokens(term))
        if not term_tokens:
            return 0.0
        return len(tokens & term_tokens) / max(len(tokens), 1)

    def _specificity_penalty(self, query_tokens: set, candidate_tokens: set) -> float:
        if not query_tokens or not candidate_tokens:
            return 0.0

        penalty = 0.0
        contradictions = (
            ("multi", "single"),
            ("single", "multi"),
            ("triple", "single"),
            ("left", "right"),
            ("right", "left"),
            ("proximal", "distal"),
            ("distal", "proximal"),
        )
        for expected, conflicting in contradictions:
            if expected in query_tokens and conflicting in candidate_tokens:
                penalty += 0.08

        has_coronary_artery_query = {"coronary", "artery"}.issubset(query_tokens)
        has_bypass_graft_candidate = (
            "bypass" in candidate_tokens or "graft" in candidate_tokens
        )
        if (
            has_coronary_artery_query
            and "bypass" not in query_tokens
            and "graft" not in query_tokens
            and has_bypass_graft_candidate
        ):
            penalty += 0.10

        return min(0.25, penalty)

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
        explorer = self._ensure_snomed_connected()
        term = explorer.get_preferred_term(concept_id)
        if term:
            self._preferred_term_cache[concept_id] = term
        return term

    def _get_alt_names(
        self, concept_id: int, preferred_term: Optional[str]
    ) -> List[str]:
        if concept_id in self._alt_names_cache:
            return self._alt_names_cache[concept_id]
        explorer = self._ensure_snomed_connected()
        descriptions = explorer.get_descriptions_for_concept(concept_id)
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
            search_terms.extend(self._query_variants(term))
            search_terms.extend(expanded_terms)
            search_terms.extend(normalized_tokens)
            if stripped_term and stripped_term != term:
                search_terms.extend(self._query_variants(stripped_term))
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
                explorer = self._ensure_snomed_connected()
                cached = explorer.search_concepts_by_term(t, limit=limit)
                self._search_cache[t] = cached
            results.extend(cached)

        vector_results: List[Dict[str, Any]] = []
        vector_score_by_concept: Dict[int, float] = {}
        if self.enable_vector_grounding and self.vector_retriever:
            vector_search_terms = [term]
            if stripped_term and stripped_term != term:
                vector_search_terms.append(stripped_term)
            compact_tokens = important_tokens[:MAX_QUERY_TOKENS]
            if compact_tokens:
                vector_search_terms.append(" ".join(compact_tokens))
            if len(important_tokens) > MAX_QUERY_TOKENS:
                vector_search_terms.append(
                    " ".join(important_tokens[-MAX_QUERY_TOKENS:])
                )
            for vt in vector_search_terms:
                retrieved, score_map = self._vector_candidates(vt)
                vector_results.extend(retrieved)
                for concept_id, vector_score in score_map.items():
                    prev = vector_score_by_concept.get(concept_id, 0.0)
                    vector_score_by_concept[concept_id] = max(prev, vector_score)

        results.extend(vector_results)

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
            local_best_score = -1.0
            local_best_lexical = -1.0
            local_best_overlap = -1.0
            candidate_debug_rows: List[Dict[str, Any]] = []
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
                best_candidate_overlap = 0.0
                for candidate in candidates:
                    candidate_norm = self._normalize(candidate)
                    candidate_tokens = set(self._important_tokens(candidate))
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
                    weighted_coverage = self._weighted_query_coverage(
                        important_query_tokens, candidate_tokens
                    )
                    if overlap_ratio:
                        candidate_score = min(
                            1.0, candidate_score + overlap_ratio * 0.08
                        )
                    if weighted_coverage:
                        candidate_score = min(
                            1.0, candidate_score + weighted_coverage * 0.10
                        )
                    penalty = self._specificity_penalty(
                        important_query_tokens, candidate_tokens
                    )
                    if penalty:
                        candidate_score = max(0.0, candidate_score - penalty)
                    if candidate_score > score:
                        score = candidate_score
                        best_candidate_term = candidate
                        best_candidate_overlap = weighted_coverage

                preferred_overlap = self._token_overlap_ratio(
                    important_query_tokens, preferred or ""
                )
                best_overlap = max(
                    preferred_overlap,
                    best_candidate_overlap,
                )

                discriminative_tokens = self._discriminative_query_tokens(
                    important_query_tokens
                )
                candidate_tokens_for_best = set(
                    self._important_tokens(best_candidate_term or preferred or "")
                )
                final_penalty = 0.0
                if (
                    important_query_tokens
                    and best_overlap < self.min_weighted_query_coverage
                ):
                    final_penalty += self.low_coverage_penalty
                if discriminative_tokens and not (
                    discriminative_tokens & candidate_tokens_for_best
                ):
                    final_penalty += self.missing_discriminative_penalty

                vector_raw = vector_score_by_concept.get(int(concept_id), 0.0)
                vector_bonus = 0.0
                if score >= self.vector_min_lexical_for_bonus:
                    vector_bonus = min(
                        self.vector_bonus_cap,
                        vector_raw * self.vector_rerank_weight,
                    )
                final_score = min(1.0, max(0.0, score + vector_bonus - final_penalty))

                if self.enable_grounding_candidate_debug:
                    candidate_debug_rows.append(
                        {
                            "concept_id": concept_id,
                            "preferred": preferred,
                            "best_candidate_term": best_candidate_term,
                            "lexical": round(score, 6),
                            "vector_raw": round(vector_raw, 6),
                            "vector_bonus": round(vector_bonus, 6),
                            "coverage": round(best_overlap, 6),
                            "final_penalty": round(final_penalty, 6),
                            "final_score": round(final_score, 6),
                        }
                    )

                better_final = final_score > (
                    local_best_score + self.vector_tie_epsilon
                )
                tied_final = (
                    abs(final_score - local_best_score) <= self.vector_tie_epsilon
                )
                better_lexical = score > local_best_lexical
                better_overlap = preferred_overlap > local_best_overlap

                if better_final or (tied_final and (better_lexical or better_overlap)):
                    local_best_score = final_score
                    local_best_lexical = score
                    local_best_overlap = best_overlap
                    local_best_id = concept_id
                    local_best_term = preferred or best_candidate_term

            if self.enable_grounding_candidate_debug and candidate_debug_rows:
                top_rows = sorted(
                    candidate_debug_rows,
                    key=lambda row: row["final_score"],
                    reverse=True,
                )[:5]
                logger.info(
                    "Grounding top candidates term='%s' role='%s': %s",
                    term,
                    role_filter or "ANY",
                    top_rows,
                )
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
            explorer = self._ensure_snomed_connected()
            cached = explorer.get_relationships(concept_id)
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
            appendix = appendix_file + "\n" + appendix_inline
        else:
            appendix = appendix_file or appendix_inline

        enable_fewshot = os.environ.get(
            "CARDIO_GRAPH_ENABLE_FEWSHOT_EXAMPLES", "false"
        ).strip().lower() in {"1", "true", "yes", "on"}
        if not enable_fewshot:
            return appendix

        fewshot_set = (
            os.environ.get("CARDIO_GRAPH_FEWSHOT_EXAMPLE_SET", "table17_table8_v1")
            .strip()
            .lower()
        )
        fewshot_appendix = ""
        if fewshot_set == "table17_table8_v1":
            fewshot_appendix = FEWSHOT_EXAMPLES_TABLE17_TABLE8_V1

        if not fewshot_appendix:
            return appendix
        if appendix:
            return fewshot_appendix + "\n" + appendix
        return fewshot_appendix

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
                        role=self._normalize_extracted_role(concept.role) or "Other",
                        logic=concept.logic,
                        logic_structured=logic_structured,
                    )
                )
            return parsed

        try:
            rules_result = b.ExtractRulesV2(tagged_text, baml_options=baml_options)
            rules_serialized = self._serialize_baml_result(rules_result)
            valid_rules = self._validate_extracted_rules(
                getattr(rules_result, "rules", []) or [], focus=focus
            )
            for rule in valid_rules:
                for condition in getattr(rule, "conditions", []) or []:
                    if not self._is_nonempty_concept(condition):
                        continue
                    normalized_role = self._normalize_extracted_role(
                        getattr(condition, "role", None)
                    )
                    if normalized_role not in {
                        "ClinicalCondition",
                        "ClinicalParameter",
                        "Procedure",
                        "Qualifier Value",
                    }:
                        continue
                    logic_structured = _default_logic_structured()
                    logic = getattr(condition, "logic", None)
                    if logic is not None:
                        logic_structured.update(logic.model_dump())
                    logic_structured = self._filter_logic_structured(logic_structured)
                    concepts.append(
                        ExtractedConcept(
                            entity_original=condition.entity_original,
                            entity_standardized_candidate=condition.entity_standardized_candidate,
                            role=normalized_role,
                            logic="condition",
                            logic_structured=logic_structured,
                        )
                    )
                for action in getattr(rule, "actions", []) or []:
                    if not self._is_nonempty_concept(action):
                        continue
                    normalized_role = self._normalize_extracted_role(
                        getattr(action, "role", None)
                    )
                    if normalized_role not in {"Medication", "Procedure"}:
                        continue
                    logic_structured = _default_logic_structured()
                    recommendation = getattr(action, "recommendation", None)
                    if recommendation is not None:
                        logic_structured.update(recommendation.model_dump())
                    logic_structured = self._filter_logic_structured(logic_structured)
                    concepts.append(
                        ExtractedConcept(
                            entity_original=action.entity_original,
                            entity_standardized_candidate=action.entity_standardized_candidate,
                            role=normalized_role,
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
                        validated_reviewed = self._validate_extracted_concepts(
                            reviewed_concepts, focus=focus
                        )
                        if validated_reviewed:
                            return validated_reviewed
                    except Exception as exc:
                        logger.warning(
                            "Incremental review pass failed; using first-pass rules. Error: %s",
                            exc,
                        )
                validated_first_pass = self._validate_extracted_concepts(
                    concepts, focus=focus
                )
                if validated_first_pass:
                    return validated_first_pass
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
        fallback_concepts = _concepts_from_extract_concepts_result(result)
        return self._validate_extracted_concepts(fallback_concepts, focus=focus)

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
                role in {"ClinicalCondition", "ClinicalParameter", "Qualifier Value"}
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
