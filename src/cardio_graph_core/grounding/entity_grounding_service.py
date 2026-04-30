from __future__ import annotations

import json
import os
import re
import time
import unicodedata
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Tuple

from cardio_graph_core.extraction.guideline_graph_builder import (
    ALLOWED_SEMANTIC_TAGS_BY_ROLE,
    DISALLOWED_SEMANTIC_TAGS,
    GENERIC_CONCEPT_TOKENS,
    MAX_CONCEPT_CANDIDATES,
    MAX_QUERY_TOKENS,
    STOPWORD_TOKENS,
    GroundedConcept,
    logger,
)


class EntityGroundingService:
    """Dedicated grounding service operating on a GuidelineGraphBuilder instance."""

    def __init__(self, builder: Any):
        self.builder = builder
        self._standardized_candidate_cache: Dict[Tuple[str, str], str] = {}

    def _llm_standardized_candidate(self, term: str, role: Optional[str]) -> str:
        b = self.builder
        if not term:
            return term
        enabled = os.environ.get(
            "CARDIO_GRAPH_GROUNDING_LLM_STANDARDIZE_ORIGINAL_ENABLED", "true"
        ).strip().lower() in {"1", "true", "yes", "on"}
        strict_mode = os.environ.get(
            "CARDIO_GRAPH_GROUNDING_LLM_STANDARDIZE_ORIGINAL_STRICT", "false"
        ).strip().lower() in {"1", "true", "yes", "on"}
        retry_attempts_raw = os.environ.get(
            "CARDIO_GRAPH_GROUNDING_LLM_STANDARDIZE_ORIGINAL_RETRIES", "2"
        )
        retry_attempts = max(1, int(retry_attempts_raw))
        retry_temperature_raw = os.environ.get(
            "CARDIO_GRAPH_GROUNDING_LLM_STANDARDIZE_ORIGINAL_RETRY_TEMPERATURE",
            "0.2",
        )
        retry_temperature = float(retry_temperature_raw)
        term_source = (
            os.environ.get("CARDIO_GRAPH_GROUNDING_TERM_SOURCE", "standardized")
            .strip()
            .lower()
        )
        if not enabled or term_source != "original":
            return term

        role_key = (role or "").strip()
        cache_key = (self._normalize(term), role_key)
        cached = self._standardized_candidate_cache.get(cache_key)
        if cached is not None:
            return cached or term

        standardized = term
        errors: List[str] = []
        try:
            from baml_py import ClientRegistry

            from cardio_graph_core.extraction.baml_client.sync_client import (
                b as baml_sync,
            )
            from cardio_graph_core.extraction.clients import (
                resolve_ollama_base_url,
                resolve_ollama_model_name,
            )

            base_options = (
                {"client_registry": b.client_registry}
                if getattr(b, "client_registry", None) is not None
                else None
            )

            retry_options = None
            llm_model = os.environ.get("CARDIO_GRAPH_GROUNDING_LLM_MODEL", "").strip()
            llm_node = os.environ.get("CARDIO_GRAPH_GROUNDING_LLM_NODE", "").strip()
            llm_port_raw = os.environ.get("CARDIO_GRAPH_GROUNDING_LLM_PORT", "").strip()
            if llm_model and llm_node and llm_port_raw:
                try:
                    llm_port = int(llm_port_raw)
                    retry_client = f"{llm_model}_retry_temp"
                    retry_registry = ClientRegistry()
                    retry_registry.add_llm_client(
                        name=retry_client,
                        provider="openai-generic",
                        options={
                            "base_url": resolve_ollama_base_url(llm_node, llm_port),
                            "model": resolve_ollama_model_name(llm_model),
                            "max_tokens": 10000,
                            "temperature": retry_temperature,
                            "format": "json",
                            "timeout": 600,
                            "request_timeout": 600,
                        },
                    )
                    retry_registry.set_primary(retry_client)
                    retry_options = {
                        "client_registry": retry_registry,
                        "client": retry_client,
                    }
                except Exception:
                    retry_options = None

            for attempt_idx in range(retry_attempts):
                use_retry_profile = attempt_idx > 0 and retry_options is not None
                baml_options = retry_options if use_retry_profile else base_options
                try:
                    result = (
                        baml_sync.GenerateStandardizedCandidate(
                            concept=term,
                            role=role_key,
                            baml_options=baml_options,
                        )
                        if baml_options is not None
                        else baml_sync.GenerateStandardizedCandidate(
                            concept=term,
                            role=role_key,
                        )
                    )
                    candidate = (
                        getattr(result, "entity_standardized_candidate", None)
                        if result is not None
                        else None
                    )
                    standardized = str(candidate).strip() if candidate else ""
                    if standardized:
                        break
                    raise RuntimeError(
                        "Empty standardized candidate returned by LLM "
                        f"for term='{term}' role='{role_key}'"
                    )
                except Exception as exc:
                    errors.append(f"attempt={attempt_idx + 1}: {exc}")
                    if attempt_idx + 1 < retry_attempts:
                        logger.warning(
                            "LLM standardized candidate retry %d/%d term='%s' role='%s'",
                            attempt_idx + 1,
                            retry_attempts,
                            term,
                            role_key,
                        )
                    else:
                        raise
        except Exception as exc:
            if strict_mode:
                raise
            logger.debug(
                "LLM standardized candidate generation failed term='%s' role='%s': %s | retries=%s",
                term,
                role_key,
                exc,
                "; ".join(errors) if errors else "none",
            )

        self._standardized_candidate_cache[cache_key] = standardized
        return standardized or term

    def _normalize(self, text: str) -> str:
        text = (text or "").strip().lower()
        text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
        text = re.sub(r"[^a-z0-9\s\-/()]+", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def _normalize_token(self, token: str) -> str:
        token = self._normalize(token)
        if token.endswith("ies") and len(token) > 4:
            token = token[:-3] + "y"
        elif token.endswith("es") and len(token) > 4 and not token.endswith("ses"):
            token = token[:-2]
        elif token.endswith("s") and len(token) > 3 and not token.endswith("ss"):
            token = token[:-1]
        if token.endswith("ing") and len(token) > 6:
            token = token[:-3]
        elif token.endswith("ed") and len(token) > 5:
            token = token[:-2]
        return token

    def _important_tokens(self, text: str) -> List[str]:
        tokens = re.findall(r"[a-z0-9]+", self._normalize(text))
        normalized_tokens = [self._normalize_token(t) for t in tokens]
        return [t for t in normalized_tokens if len(t) > 2 and t not in STOPWORD_TOKENS]

    def _build_context_query_variants(
        self,
        context: Any,
        role: Optional[str],
        enabled: bool,
        allowed_roles: set[str],
        max_tokens: int,
    ) -> List[str]:
        if context is None or not enabled:
            return []
        role_key = (role or "").strip().lower()
        if allowed_roles and role_key not in allowed_roles:
            return []
        if isinstance(context, (dict, list)):
            raw_context = json.dumps(context, ensure_ascii=False, sort_keys=True)
        else:
            raw_context = str(context)
        cleaned_context = re.sub(r"\s+", " ", raw_context).strip()
        if not cleaned_context:
            return []
        context_tokens = self._important_tokens(cleaned_context)
        if not context_tokens:
            return []
        max_tokens = max(2, max_tokens)
        variants: List[str] = [" ".join(context_tokens[:max_tokens])]
        if len(context_tokens) > max_tokens:
            variants.append(" ".join(context_tokens[-max_tokens:]))
        for fragment in re.split(r"[;|,.]", cleaned_context):
            fragment_tokens = self._important_tokens(fragment)
            if 2 <= len(fragment_tokens) <= max_tokens:
                variants.append(" ".join(fragment_tokens))
        deduped: List[str] = []
        seen = set()
        for variant in variants:
            key = self._normalize(variant)
            if not key or key in seen:
                continue
            seen.add(key)
            deduped.append(variant)
            if len(deduped) >= 3:
                break
        return deduped

    def _context_query_variants(self, context: Any, role: Optional[str]) -> List[str]:
        b = self.builder
        return self._build_context_query_variants(
            context=context,
            role=role,
            enabled=b.enable_vector_context_query,
            allowed_roles=b.vector_context_allowed_roles,
            max_tokens=b.vector_context_max_tokens,
        )

    def _lexical_context_query_variants(
        self, context: Any, role: Optional[str]
    ) -> List[str]:
        b = self.builder
        return self._build_context_query_variants(
            context=context,
            role=role,
            enabled=getattr(b, "enable_lexical_context_query", False),
            allowed_roles=getattr(b, "lexical_context_allowed_roles", set()),
            max_tokens=getattr(b, "lexical_context_max_tokens", 8),
        )

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

    def _semantic_tag(self, term: Optional[str]) -> str:
        if not term:
            return ""
        match = re.search(r"\(([^)]+)\)\s*$", term)
        if not match:
            return ""
        return match.group(1).strip().lower()

    def _role_semantic_penalty(self, role: Optional[str], term: Optional[str]) -> float:
        b = self.builder
        if not role or not term:
            return 0.0
        allowed = ALLOWED_SEMANTIC_TAGS_BY_ROLE.get(role)
        if not allowed:
            return 0.0
        tag = self._semantic_tag(term)
        if not tag:
            return 0.0
        if tag in allowed:
            return 0.0
        crossclass_tags = {
            "finding",
            "observable entity",
            "qualifier value",
            "physical object",
            "assessment scale",
            "body structure",
        }
        if tag in crossclass_tags:
            return b.role_semantic_crossclass_penalty
        return b.role_semantic_mismatch_penalty

    def _has_planning_intent(self, term: str, query_context: Any) -> bool:
        planning_tokens = {
            "plan",
            "planned",
            "planning",
            "schedule",
            "scheduled",
            "intended",
            "intent",
            "elective",
        }
        haystacks = [self._normalize(term)]
        if query_context is not None:
            if isinstance(query_context, (dict, list)):
                haystacks.append(
                    self._normalize(
                        json.dumps(query_context, ensure_ascii=False, sort_keys=True)
                    )
                )
            else:
                haystacks.append(self._normalize(str(query_context)))
        return any(
            token in hs.split() for hs in haystacks if hs for token in planning_tokens
        )

    def _procedure_situation_penalty(
        self,
        role: Optional[str],
        preferred_term: Optional[str],
        source_term: str,
        query_context: Any,
    ) -> float:
        if role != "Procedure":
            return 0.0
        if self._semantic_tag(preferred_term) != "situation":
            return 0.0
        if self._has_planning_intent(source_term, query_context):
            return 0.0
        return float(
            getattr(
                self.builder,
                "procedure_situation_without_intent_penalty",
                0.06,
            )
        )

    def _medication_salt_form_penalty(
        self,
        role: Optional[str],
        source_term: str,
        candidate_term: Optional[str],
    ) -> float:
        if role != "Medication" or not candidate_term:
            return 0.0
        query_tokens = set(self._important_tokens(source_term))
        if not query_tokens:
            return 0.0
        qualifier_tokens = self._medication_qualifier_tokens()
        if query_tokens & qualifier_tokens:
            return 0.0
        candidate_tokens = set(self._important_tokens(candidate_term))
        extra_qualifiers = qualifier_tokens & (candidate_tokens - query_tokens)
        if not extra_qualifiers:
            return 0.0
        per_token_penalty = float(
            getattr(self.builder, "medication_salt_form_penalty", 0.03)
        )
        return min(0.12, per_token_penalty * float(len(extra_qualifiers)))

    def _medication_qualifier_tokens(self) -> set[str]:
        return {
            "besilate",
            "hydrochloride",
            "hydrobromide",
            "succinate",
            "phosphate",
            "acetate",
            "nitrate",
            "sulfate",
            "maleate",
            "mesylate",
            "tablet",
            "capsule",
            "release",
            "milligram",
        }

    def _has_medication_therapy_intent(self, term: str, query_context: Any) -> bool:
        cue_tokens = set(
            getattr(
                self.builder,
                "medication_therapy_cue_tokens",
                {"therapy", "treatment", "regimen", "management"},
            )
        )
        if not cue_tokens:
            return False
        haystacks = [self._normalize(term)]
        if query_context is not None:
            if isinstance(query_context, (dict, list)):
                haystacks.append(
                    self._normalize(
                        json.dumps(query_context, ensure_ascii=False, sort_keys=True)
                    )
                )
            else:
                haystacks.append(self._normalize(str(query_context)))
        for hs in haystacks:
            if not hs:
                continue
            tokens = set(self._important_tokens(hs))
            if tokens & cue_tokens:
                return True
        return False

    def _medication_abstraction_penalty(
        self,
        role: Optional[str],
        source_term: str,
        candidate_term: Optional[str],
        query_context: Any,
    ) -> float:
        if role != "Medication" or not candidate_term:
            return 0.0
        if self._has_medication_therapy_intent(source_term, query_context):
            return 0.0
        candidate_tokens = set(self._important_tokens(candidate_term))
        semantic_tag = self._semantic_tag(candidate_term)
        abstraction_tags = {
            "procedure",
            "finding",
            "situation",
            "observable entity",
            "qualifier value",
        }
        penalty = 0.0
        if semantic_tag in abstraction_tags:
            penalty += float(
                getattr(
                    self.builder,
                    "medication_non_substance_semantic_penalty",
                    0.07,
                )
            )
        cue_tokens = set(
            getattr(
                self.builder,
                "medication_therapy_cue_tokens",
                {"therapy", "treatment", "regimen", "management"},
            )
        )
        if candidate_tokens & cue_tokens:
            penalty += float(
                getattr(self.builder, "medication_therapy_context_penalty", 0.04)
            )
        max_penalty = float(
            getattr(self.builder, "medication_max_abstraction_penalty", 0.16)
        )
        return min(max_penalty, penalty)

    def _medication_base_preference_score(
        self,
        role: Optional[str],
        source_term: str,
        candidate_term: Optional[str],
        query_context: Any,
    ) -> float:
        if role != "Medication" or not candidate_term:
            return 0.0
        if self._has_medication_therapy_intent(source_term, query_context):
            return 0.0
        candidate_tokens = set(self._important_tokens(candidate_term))
        cue_tokens = set(
            getattr(
                self.builder,
                "medication_therapy_cue_tokens",
                {"therapy", "treatment", "regimen", "management"},
            )
        )
        if candidate_tokens & cue_tokens:
            return 0.0
        semantic_tag = self._semantic_tag(candidate_term)
        preferred_tags = {
            "substance",
            "product",
            "medicinal product",
            "clinical drug",
            "pharmaceutical / biologic product",
        }
        if semantic_tag not in preferred_tags:
            return 0.0
        query_tokens = set(self._important_tokens(source_term))
        extra_qualifiers = self._medication_qualifier_tokens() & (
            candidate_tokens - query_tokens
        )
        return 0.85 if extra_qualifiers else 1.0

    def _pci_angioplasty_variant_penalty(
        self,
        role: Optional[str],
        source_term: str,
        candidate_term: Optional[str],
    ) -> float:
        if role != "Procedure" or not candidate_term:
            return 0.0
        normalized_source = self._normalize(source_term)
        if "percutaneous coronary revascularization" not in normalized_source:
            return 0.0
        candidate_norm = self._normalize(candidate_term)
        # Prefer intervention/revascularization variants over angioplasty-only variants.
        if "angioplasty" in candidate_norm:
            return float(getattr(self.builder, "pci_angioplasty_variant_penalty", 0.08))
        # Penalize chronic-total-occlusion sub-variants when the source query is generic.
        if (
            (
                "chronic total occlusion" in candidate_norm
                or "total occlusion" in candidate_norm
            )
            and "occlusion" not in normalized_source
            and "chronic" not in normalized_source
        ):
            return float(getattr(self.builder, "pci_cto_variant_penalty", 0.08))
        return 0.0

    def _procedure_count_overspec_penalty(
        self,
        role: Optional[str],
        source_term: str,
        candidate_term: Optional[str],
    ) -> float:
        # Simplification experiment: disable specialized count-overspec heuristic
        # and rely on generic extra-qualifier penalties.
        return 0.0

    def _indication_context_penalty(
        self,
        role: Optional[str],
        source_term: str,
        candidate_term: Optional[str],
    ) -> float:
        if role != "ClinicalCondition" or not candidate_term:
            return 0.0
        normalized_source = self._normalize(source_term)
        if not normalized_source.startswith("indication of"):
            return 0.0
        candidate_tag = self._semantic_tag(candidate_term)
        if candidate_tag != "finding":
            return 0.0
        return float(getattr(self.builder, "indication_finding_penalty", 0.10))

    def _indication_context_preference_score(
        self,
        role: Optional[str],
        source_term: str,
        candidate_term: Optional[str],
    ) -> float:
        if role != "ClinicalCondition" or not candidate_term:
            return 0.0
        normalized_source = self._normalize(source_term)
        if not normalized_source.startswith("indication of"):
            return 0.0
        candidate_tag = self._semantic_tag(candidate_term)
        candidate_norm = self._normalize(candidate_term)
        if candidate_tag == "qualifier value" and "indication of" in candidate_norm:
            return float(getattr(self.builder, "indication_qualifier_preference", 1.0))
        return 0.0

    def _normalized_head_term_match(
        self, source_term: str, candidate_term: str
    ) -> float:
        query_tokens = self._important_tokens(source_term)
        candidate_tokens = self._important_tokens(candidate_term)
        if not query_tokens or not candidate_tokens:
            return 0.0
        q_head = query_tokens[0]
        c_head = candidate_tokens[0]
        if q_head == c_head:
            return 1.0
        if q_head in candidate_tokens:
            return 0.85
        return SequenceMatcher(None, q_head, c_head).ratio() * 0.5

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
        q_chars = set(re.findall(r"....", f" {q} "))
        c_chars = set(re.findall(r"....", f" {c} "))
        char_jaccard = 0.0
        if q_chars and c_chars:
            char_jaccard = len(q_chars & c_chars) / len(q_chars | c_chars)
        coverage = self._weighted_query_coverage(q_tokens, c_tokens)
        combined = (
            0.40 * coverage
            + 0.22 * token_jaccard
            + 0.18 * seq
            + 0.10 * partial
            + 0.10 * char_jaccard
        )
        return min(1.0, max(combined, coverage, token_jaccard, char_jaccard))

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

    def _extra_qualifier_ratio(
        self, query_tokens: set[str], candidate_tokens: set[str]
    ) -> float:
        if not candidate_tokens:
            return 0.0
        discriminative_candidate_tokens = {
            token
            for token in candidate_tokens
            if token not in GENERIC_CONCEPT_TOKENS and len(token) >= 5
        }
        if not discriminative_candidate_tokens:
            return 0.0
        extra = discriminative_candidate_tokens - query_tokens
        return len(extra) / max(len(discriminative_candidate_tokens), 1)

    def _modifier_tokens(self, tokens: set[str]) -> set[str]:
        if not tokens:
            return set()
        explicit = {
            "single",
            "double",
            "triple",
            "quadruple",
            "multiple",
            "multi",
            "first",
            "second",
            "third",
            "fourth",
            "fifth",
            "left",
            "right",
            "bilateral",
            "unilateral",
            "proximal",
            "distal",
            "mid",
            "middle",
            "upper",
            "lower",
            "anterior",
            "posterior",
            "medial",
            "lateral",
        }
        out: set[str] = set()
        for token in tokens:
            if token in explicit:
                out.add(token)
                continue
            if re.fullmatch(r"x\d+", token):
                out.add(token)
                continue
            if token.isdigit():
                out.add(token)
                continue
        return out

    def _unmatched_modifier_penalty(
        self, query_tokens: set[str], candidate_tokens: set[str]
    ) -> Tuple[int, float]:
        b = self.builder
        query_modifiers = self._modifier_tokens(query_tokens)
        candidate_modifiers = self._modifier_tokens(candidate_tokens)
        unmatched = candidate_modifiers - query_modifiers
        unmatched_count = len(unmatched)
        if unmatched_count <= 0:
            return 0, 0.0
        penalty = min(
            b.unmatched_modifier_penalty_cap,
            unmatched_count * b.unmatched_modifier_penalty_weight,
        )
        return unmatched_count, penalty

    def _vector_candidates(
        self, term: str
    ) -> Tuple[List[Dict[str, Any]], Dict[int, float], Dict[int, int]]:
        b = self.builder
        if not b.enable_vector_grounding or not b.vector_retriever:
            return [], {}, {}
        try:
            candidates = b.vector_retriever.retrieve(term, top_k=b.vector_top_k)
        except Exception as exc:
            logger.warning("Vector retrieval failed for '%s': %s", term, exc)
            return [], {}, {}

        vector_score_by_concept: Dict[int, float] = {}
        vector_rank_by_concept: Dict[int, int] = {}
        for rank_index, row in enumerate(candidates, start=1):
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
            prior_rank = vector_rank_by_concept.get(concept_id)
            if prior_rank is None or rank_index < prior_rank:
                vector_rank_by_concept[concept_id] = rank_index
        return candidates, vector_score_by_concept, vector_rank_by_concept

    def _effective_semantic_penalty(
        self,
        base_penalty: float,
        weighted_coverage: float,
        vector_rank: Optional[int],
    ) -> float:
        b = self.builder
        if base_penalty <= 0.0:
            return 0.0
        if not b.semantic_penalty_evidence_relief_enabled:
            return base_penalty
        if weighted_coverage < b.semantic_penalty_evidence_min_coverage:
            return base_penalty
        if (
            vector_rank is None
            or vector_rank > b.semantic_penalty_evidence_max_vector_rank
        ):
            return base_penalty
        scale = min(1.0, max(0.0, b.semantic_penalty_evidence_scale))
        return base_penalty * scale

    def _should_vector_rank_promote(
        self, top: Dict[str, Any], runner: Dict[str, Any]
    ) -> bool:
        b = self.builder
        if not b.vector_rank_rescue_enabled:
            return False
        top_score = float(top.get("raw_final_score", top.get("final_score", 0.0)))
        runner_score = float(
            runner.get("raw_final_score", runner.get("final_score", 0.0))
        )
        score_gap = top_score - runner_score
        if score_gap < 0.0 or score_gap > b.vector_rank_rescue_margin:
            return False
        runner_rank = runner.get("vector_rank")
        if runner_rank is None or runner_rank > b.vector_rank_rescue_max_rank:
            return False
        top_rank = top.get("vector_rank")
        if top_rank is not None and runner_rank >= top_rank:
            return False
        if min(top_score, runner_score) < b.vector_rank_rescue_min_final_score:
            return False
        if float(runner.get("coverage", 0.0)) < b.vector_rank_rescue_min_coverage:
            return False
        lexical_gap = float(top.get("lexical", 0.0)) - float(runner.get("lexical", 0.0))
        vector_raw_advantage = float(runner.get("vector_raw", 0.0)) - float(
            top.get("vector_raw", 0.0)
        )
        qualifier_advantage = float(top.get("extra_qualifier_ratio", 0.0)) - float(
            runner.get("extra_qualifier_ratio", 0.0)
        )
        if vector_raw_advantage < b.vector_rank_rescue_min_vector_raw_advantage and (
            qualifier_advantage < b.vector_rank_rescue_min_qualifier_advantage
        ):
            return False
        if (
            lexical_gap > b.vector_rank_rescue_max_lexical_gap
            and vector_raw_advantage < b.vector_rank_rescue_min_vector_raw_advantage
        ):
            return False
        if int(runner.get("unmatched_modifier_count", 0)) > int(
            top.get("unmatched_modifier_count", 0)
        ):
            return False
        return True

    def _should_prefer_lower_qualifier_tie(
        self, top: Dict[str, Any], runner: Dict[str, Any]
    ) -> bool:
        b = self.builder
        if not b.qualifier_tie_prefer_enabled:
            return False
        top_score = float(top.get("raw_final_score", top.get("final_score", 0.0)))
        runner_score = float(
            runner.get("raw_final_score", runner.get("final_score", 0.0))
        )
        score_gap = top_score - runner_score
        if score_gap < 0.0 or score_gap > b.qualifier_tie_prefer_margin:
            return False
        qualifier_delta = float(top.get("extra_qualifier_ratio", 0.0)) - float(
            runner.get("extra_qualifier_ratio", 0.0)
        )
        if qualifier_delta < b.qualifier_tie_prefer_min_qualifier_delta:
            return False
        vector_raw_advantage = float(runner.get("vector_raw", 0.0)) - float(
            top.get("vector_raw", 0.0)
        )
        if vector_raw_advantage < b.qualifier_tie_prefer_min_vector_raw_advantage:
            return False
        lexical_gap = float(top.get("lexical", 0.0)) - float(runner.get("lexical", 0.0))
        if lexical_gap > b.qualifier_tie_prefer_max_lexical_gap:
            return False
        if int(runner.get("unmatched_modifier_count", 0)) > int(
            top.get("unmatched_modifier_count", 0)
        ):
            return False
        return True

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

    def _hard_negative_penalty_for(
        self, term: str, role: Optional[str], concept_id: int
    ) -> float:
        b = self.builder
        if b.hard_negative_penalty <= 0.0:
            return 0.0
        normalized_term = self._normalize(term)
        role_key = (role or "").strip()
        if not normalized_term or not role_key:
            return 0.0
        blocked = b.hard_negative_map.get((normalized_term, role_key), set())
        if concept_id in blocked:
            return b.hard_negative_penalty
        return 0.0

    def _build_context_hint(self, concept: Any) -> str:
        context_hint = ""
        if getattr(concept, "logic_structured", None):
            context_hint = json.dumps(
                concept.logic_structured,
                ensure_ascii=False,
                sort_keys=True,
            )
        if getattr(concept, "logic", None):
            context_hint = f"{context_hint} {concept.logic}".strip()
        return context_hint

    def ground_entity(
        self,
        term: str,
        role: Optional[str],
        query_context: Any = None,
        limit: int = 100,
        gold_concept_id: Optional[int] = None,
        return_ranked: bool = False,
    ) -> Any:
        b = self.builder

        def _return_result(
            best_id: Optional[int],
            best_term: Optional[str],
            best_score: float,
            ranked_candidates: Optional[List[Dict[str, Any]]] = None,
            diagnostics: Optional[Dict[str, Any]] = None,
        ):
            if return_ranked:
                return (
                    best_id,
                    best_term,
                    best_score,
                    ranked_candidates or [],
                    diagnostics or {},
                )
            return best_id, best_term, best_score

        if not term:
            return _return_result(None, None, 0.0, [])

        term = self._llm_standardized_candidate(term, role)

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
            expanded_terms = b._expand_term(term)
            expanded_terms.extend(b._expand_term_variants(term))
            search_terms.extend(b._query_variants(term))
            search_terms.extend(expanded_terms)
            search_terms.extend(normalized_tokens)
            if stripped_term and stripped_term != term:
                search_terms.extend(b._query_variants(stripped_term))
                search_terms.extend(b._expand_term(stripped_term))
            if paren_tokens:
                search_terms.extend(paren_tokens)

        if "coronary syndrome" in normalized_term:
            ischemic_variant = normalized_term.replace(
                "coronary syndrome", "ischemic heart disease"
            )
            search_terms.append(ischemic_variant)

        if not search_terms:
            search_terms = [term]

        trace_enabled = (
            os.environ.get("CARDIO_GRAPH_GROUNDING_STAGE_TRACE_ENABLED", "false")
            or "false"
        ).strip().lower() in {"1", "true", "yes", "on"}
        gold_presence_trace: Dict[str, Any] = {
            "gold_concept_id": gold_concept_id,
            "trace_enabled": trace_enabled,
            "gold_in_initial_results": None,
            "gold_in_allowed_domain": None,
            "gold_in_truncated_set": None,
            "gold_filter_reasons": [],
            "gold_in_final_ranked": None,
            "gold_rank_final": None,
            "gold_absence_stage": None,
        }

        rescue_concept_id = b._grounding_rescue_override(term, role)
        if rescue_concept_id is not None:
            rescue_term = b._get_preferred_term(rescue_concept_id)
            if rescue_term:
                rescue_candidates = [
                    {
                        "concept_id": rescue_concept_id,
                        "term": rescue_term,
                        "final_score": 1.0,
                        "coverage": 1.0,
                        "lexical": 1.0,
                        "discriminative_coverage": 1.0,
                        "extra_qualifier_ratio": 0.0,
                        "vector_rank": 1,
                        "rank": 1,
                        "rescue_override": True,
                    }
                ]
                logger.info(
                    "Grounding rescue override term='%s' role='%s' -> %s (%s)",
                    term,
                    role or "",
                    rescue_concept_id,
                    rescue_term,
                )
                return _return_result(
                    rescue_concept_id,
                    rescue_term,
                    1.0,
                    rescue_candidates,
                    {
                        "gold_concept_id": gold_concept_id,
                        "trace_enabled": trace_enabled,
                        "gold_absence_stage": "rescue_override",
                    },
                )

        results = []
        seen = set()
        lexical_terms = list(search_terms)
        for context_variant in self._lexical_context_query_variants(
            query_context, role
        ):
            lexical_terms.append(context_variant)
            if getattr(b, "lexical_context_append_term", False):
                lexical_terms.append(f"{term} {context_variant}")

        use_subset_lexical = bool(
            getattr(b, "enable_subset_lexical_grounding", False)
            and getattr(b, "vector_retriever", None)
        )

        for t in lexical_terms:
            if t in seen:
                continue
            seen.add(t)
            cached = b._search_cache.get(t)
            if cached is None:
                if use_subset_lexical:
                    try:
                        cached = b.vector_retriever.retrieve_lexical(
                            t,
                            top_k=getattr(b, "lexical_top_k", 80),
                        )
                    except Exception as exc:
                        logger.warning(
                            "Subset lexical retrieval failed for '%s' (no DB fallback): %s",
                            t,
                            exc,
                        )
                        cached = []
                else:
                    explorer = b._ensure_snomed_connected()
                    cached = explorer.search_concepts_by_term(t, limit=limit)
                b._search_cache[t] = cached
            results.extend(cached)

        vector_results: List[Dict[str, Any]] = []
        vector_score_by_concept: Dict[int, float] = {}
        vector_rank_by_concept: Dict[int, int] = {}
        if b.enable_vector_grounding and b.vector_retriever:
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
            for context_variant in self._context_query_variants(query_context, role):
                vector_search_terms.append(context_variant)
                if b.vector_context_append_term:
                    vector_search_terms.append(f"{term} {context_variant}")
            seen_vector_terms = set()
            for vt in vector_search_terms:
                vt = " ".join(str(vt or "").split()).strip()
                vt_key = self._normalize(vt)
                if not vt_key or vt_key in seen_vector_terms:
                    continue
                seen_vector_terms.add(vt_key)
                retrieved, score_map, rank_map = self._vector_candidates(vt)
                vector_results.extend(retrieved)
                for concept_id, vector_score in score_map.items():
                    prev = vector_score_by_concept.get(concept_id, 0.0)
                    vector_score_by_concept[concept_id] = max(prev, vector_score)
                for concept_id, vector_rank in rank_map.items():
                    prev_rank = vector_rank_by_concept.get(concept_id)
                    if prev_rank is None or vector_rank < prev_rank:
                        vector_rank_by_concept[concept_id] = vector_rank

        results.extend(vector_results)

        if not results:
            if trace_enabled and gold_concept_id is not None:
                gold_presence_trace["gold_in_initial_results"] = False
                gold_presence_trace["gold_in_allowed_domain"] = False
                gold_presence_trace["gold_in_truncated_set"] = False
                gold_presence_trace["gold_absence_stage"] = "not_retrieved"
            return _return_result(None, None, 0.0, [], gold_presence_trace)

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
        if b.enable_domain_filter and role:
            allowed_roots = b._allowed_root_concepts_for_role(role)
            if allowed_roots:
                concept_items_allowed = [
                    (concept_id, terms)
                    for concept_id, terms in concept_items_all
                    if b._concept_in_allowed_roots(concept_id, allowed_roots)
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

        if trace_enabled and gold_concept_id is not None:
            gold_presence_trace["gold_in_initial_results"] = any(
                concept_id == gold_concept_id for concept_id, _ in concept_items_all
            )
            gold_presence_trace["gold_in_allowed_domain"] = any(
                concept_id == gold_concept_id for concept_id, _ in concept_items_allowed
            )
            gold_presence_trace["gold_in_truncated_set"] = any(
                concept_id == gold_concept_id for concept_id, _ in concept_items
            )

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
            candidate_debug_rows: List[Dict[str, Any]] = []
            scored_candidates: List[Dict[str, Any]] = []
            gold_filter_reasons: List[str] = []
            normalized_query_terms = {
                self._normalize(q) for q in query_terms if self._normalize(q)
            }
            normalized_source_term = self._normalize(term)
            is_role_tension_term = normalized_source_term in b.role_tension_terms
            for concept_id, terms in concept_items_to_score:
                role_mismatch = bool(role_filter) and not b._candidate_matches_role(
                    concept_id, role_filter
                )
                if role_mismatch and not b.enable_role_soft_constraints:
                    if (
                        trace_enabled
                        and gold_concept_id is not None
                        and concept_id == gold_concept_id
                    ):
                        gold_filter_reasons.append("role_mismatch_hard_filter")
                    continue
                preferred = b._get_preferred_term(concept_id)
                candidates = list(terms)
                if preferred:
                    candidates.append(preferred)

                if important_query_tokens:
                    if not any(
                        important_query_tokens & set(self._important_tokens(candidate))
                        for candidate in candidates
                    ):
                        if (
                            trace_enabled
                            and gold_concept_id is not None
                            and concept_id == gold_concept_id
                        ):
                            gold_filter_reasons.append("token_overlap_filter")
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
                        candidate_score = candidate_score + 0.05
                    if paren_tokens and any(
                        token.lower() in candidate_norm for token in paren_tokens
                    ):
                        candidate_score = candidate_score + 0.03
                    overlap_ratio = self._token_overlap_ratio(
                        important_query_tokens, candidate
                    )
                    weighted_coverage = self._weighted_query_coverage(
                        important_query_tokens, candidate_tokens
                    )
                    if overlap_ratio:
                        candidate_score = candidate_score + overlap_ratio * 0.08
                    if weighted_coverage:
                        candidate_score = candidate_score + weighted_coverage * 0.10
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
                discriminative_coverage = 0.0
                if discriminative_tokens:
                    discriminative_coverage = len(
                        discriminative_tokens & candidate_tokens_for_best
                    ) / max(len(discriminative_tokens), 1)
                final_penalty = 0.0
                low_coverage_penalty = 0.0
                if (
                    important_query_tokens
                    and best_overlap < b.min_weighted_query_coverage
                ):
                    low_coverage_penalty = b.low_coverage_penalty
                    final_penalty += low_coverage_penalty
                missing_discriminative_penalty = 0.0
                if discriminative_tokens and not (
                    discriminative_tokens & candidate_tokens_for_best
                ):
                    missing_discriminative_penalty = b.missing_discriminative_penalty
                    final_penalty += missing_discriminative_penalty
                extra_qualifier_ratio = self._extra_qualifier_ratio(
                    important_query_tokens, candidate_tokens_for_best
                )
                extra_qualifier_penalty = (
                    extra_qualifier_ratio * b.extra_qualifier_penalty_weight
                )
                final_penalty += extra_qualifier_penalty
                unmatched_modifier_count, unmatched_modifier_penalty = (
                    self._unmatched_modifier_penalty(
                        important_query_tokens,
                        candidate_tokens_for_best,
                    )
                )
                final_penalty += unmatched_modifier_penalty
                hard_negative_penalty = self._hard_negative_penalty_for(
                    normalized_source_term,
                    role_filter,
                    concept_id,
                )
                final_penalty += hard_negative_penalty
                base_semantic_penalty = self._role_semantic_penalty(
                    role_filter, preferred
                )
                role_mismatch_penalty = 0.0
                if role_mismatch:
                    role_mismatch_penalty = b.role_mismatch_penalty
                    final_penalty += role_mismatch_penalty
                role_tension_penalty = 0.0
                if role_mismatch and is_role_tension_term:
                    role_tension_penalty = b.role_tension_penalty
                    final_penalty += role_tension_penalty
                procedure_situation_penalty = self._procedure_situation_penalty(
                    role_filter,
                    preferred,
                    term,
                    query_context,
                )
                final_penalty += procedure_situation_penalty
                medication_salt_form_penalty = self._medication_salt_form_penalty(
                    role_filter,
                    term,
                    preferred,
                )
                final_penalty += medication_salt_form_penalty
                medication_abstraction_penalty = self._medication_abstraction_penalty(
                    role_filter,
                    term,
                    preferred,
                    query_context,
                )
                final_penalty += medication_abstraction_penalty
                pci_angioplasty_penalty = self._pci_angioplasty_variant_penalty(
                    role_filter,
                    term,
                    preferred,
                )
                final_penalty += pci_angioplasty_penalty
                procedure_count_overspec_penalty = (
                    self._procedure_count_overspec_penalty(
                        role_filter,
                        term,
                        preferred,
                    )
                )
                final_penalty += procedure_count_overspec_penalty
                indication_context_penalty = self._indication_context_penalty(
                    role_filter,
                    term,
                    preferred,
                )
                final_penalty += indication_context_penalty

                vector_raw = vector_score_by_concept.get(int(concept_id), 0.0)
                vector_rank = vector_rank_by_concept.get(int(concept_id))
                vector_bonus = 0.0
                if score >= b.vector_min_lexical_for_bonus:
                    vector_bonus = min(
                        b.vector_bonus_cap,
                        vector_raw * b.vector_rerank_weight,
                    )
                if (
                    b.vector_rank_prior_enabled
                    and vector_rank is not None
                    and vector_rank <= b.vector_rank_prior_top_k
                    and score >= b.vector_rank_prior_lexical_floor
                ):
                    rank_weight = (b.vector_rank_prior_top_k - vector_rank + 1) / max(
                        float(b.vector_rank_prior_top_k), 1.0
                    )
                    vector_bonus += b.vector_rank_prior_bonus * rank_weight
                semantic_penalty = self._effective_semantic_penalty(
                    base_semantic_penalty,
                    best_overlap,
                    vector_rank,
                )
                final_penalty += semantic_penalty
                normalized_head_match = self._normalized_head_term_match(
                    term,
                    preferred or "",
                )
                medication_base_preference = self._medication_base_preference_score(
                    role_filter,
                    term,
                    preferred,
                    query_context,
                )
                indication_context_preference = (
                    self._indication_context_preference_score(
                        role_filter,
                        term,
                        preferred,
                    )
                )
                raw_final_score = score + vector_bonus - final_penalty
                final_score = min(1.0, max(0.0, raw_final_score))

                if b.enable_grounding_candidate_debug:
                    candidate_debug_rows.append(
                        {
                            "concept_id": concept_id,
                            "term": preferred,
                            "lexical": round(score, 6),
                            "coverage": round(best_overlap, 6),
                            "discriminative_coverage": round(
                                discriminative_coverage, 6
                            ),
                            "extra_qualifier_ratio": round(extra_qualifier_ratio, 6),
                            "unmatched_modifier_count": unmatched_modifier_count,
                            "unmatched_modifier_penalty": round(
                                unmatched_modifier_penalty,
                                6,
                            ),
                            "vector_raw": round(vector_raw, 6),
                            "vector_rank": vector_rank,
                            "vector_bonus": round(vector_bonus, 6),
                            "semantic_penalty": round(semantic_penalty, 6),
                            "procedure_situation_penalty": round(
                                procedure_situation_penalty, 6
                            ),
                            "medication_salt_form_penalty": round(
                                medication_salt_form_penalty, 6
                            ),
                            "medication_abstraction_penalty": round(
                                medication_abstraction_penalty,
                                6,
                            ),
                            "pci_angioplasty_penalty": round(
                                pci_angioplasty_penalty,
                                6,
                            ),
                            "procedure_count_overspec_penalty": round(
                                procedure_count_overspec_penalty,
                                6,
                            ),
                            "indication_context_penalty": round(
                                indication_context_penalty,
                                6,
                            ),
                            "normalized_head_match": round(
                                normalized_head_match,
                                6,
                            ),
                            "medication_base_preference": round(
                                medication_base_preference,
                                6,
                            ),
                            "indication_context_preference": round(
                                indication_context_preference,
                                6,
                            ),
                            "role_mismatch": role_mismatch,
                            "final_penalty": round(final_penalty, 6),
                            "raw_final_score": round(raw_final_score, 6),
                            "final_score": round(final_score, 6),
                        }
                    )

                scored_candidates.append(
                    {
                        "concept_id": concept_id,
                        "term": preferred,
                        "final_score": final_score,
                        "coverage": best_overlap,
                        "lexical": score,
                        "discriminative_coverage": discriminative_coverage,
                        "extra_qualifier_ratio": extra_qualifier_ratio,
                        "unmatched_modifier_count": unmatched_modifier_count,
                        "unmatched_modifier_penalty": unmatched_modifier_penalty,
                        "extra_qualifier_penalty": extra_qualifier_penalty,
                        "low_coverage_penalty": low_coverage_penalty,
                        "missing_discriminative_penalty": missing_discriminative_penalty,
                        "hard_negative_penalty": hard_negative_penalty,
                        "role_mismatch_penalty": role_mismatch_penalty,
                        "role_tension_penalty": role_tension_penalty,
                        "procedure_situation_penalty": procedure_situation_penalty,
                        "medication_salt_form_penalty": medication_salt_form_penalty,
                        "medication_abstraction_penalty": medication_abstraction_penalty,
                        "pci_angioplasty_penalty": pci_angioplasty_penalty,
                        "procedure_count_overspec_penalty": procedure_count_overspec_penalty,
                        "indication_context_penalty": indication_context_penalty,
                        "base_semantic_penalty": base_semantic_penalty,
                        "semantic_penalty": semantic_penalty,
                        "vector_rank": vector_rank,
                        "vector_raw": vector_raw,
                        "vector_bonus": vector_bonus,
                        "raw_final_score": raw_final_score,
                        "final_penalty": final_penalty,
                        "normalized_head_match": normalized_head_match,
                        "medication_base_preference": medication_base_preference,
                        "indication_context_preference": indication_context_preference,
                        "role_mismatch": role_mismatch,
                        "term_length": len(self._important_tokens(preferred or "")),
                    }
                )

            if not scored_candidates:
                return None, None, 0.0, [], {"gold_filter_reasons": gold_filter_reasons}

            scored_candidates = sorted(
                scored_candidates,
                key=lambda row: (
                    -row.get("raw_final_score", row["final_score"]),
                    -row.get("indication_context_preference", 0.0),
                    -row.get("medication_base_preference", 0.0),
                    -row.get("normalized_head_match", 0.0),
                    row.get("unmatched_modifier_count", 0),
                    row["extra_qualifier_ratio"],
                    -row["coverage"],
                    -row["lexical"],
                    -row["discriminative_coverage"],
                    row.get("term_length", 0),
                    int(row["concept_id"]),
                ),
            )

            for idx, row in enumerate(scored_candidates, start=1):
                row["rank"] = idx

            local_best = scored_candidates[0]
            local_best_id = local_best["concept_id"]
            local_best_term = local_best["term"]
            local_best_score = local_best["final_score"]

            if len(scored_candidates) > 1:
                top_two = sorted(
                    scored_candidates,
                    key=lambda row: row.get("raw_final_score", row["final_score"]),
                    reverse=True,
                )[:2]
                top = top_two[0]
                runner = top_two[1]
                if (
                    b.ambiguity_abstain_margin > 0.0
                    and (
                        top.get("raw_final_score", top["final_score"])
                        - runner.get("raw_final_score", runner["final_score"])
                    )
                    <= b.ambiguity_abstain_margin
                    and top["coverage"] < b.ambiguity_min_coverage
                    and runner["coverage"] < b.ambiguity_min_coverage
                    and top["lexical"] < b.ambiguity_lexical_force_pick
                ):
                    backoff_candidate = None
                    if b.ambiguity_confidence_backoff_enabled:
                        min_backoff_score = max(
                            b.ambiguity_backoff_min_score,
                            top.get("raw_final_score", top["final_score"])
                            - b.ambiguity_backoff_max_drop,
                        )
                        backoff_pool = [
                            row
                            for row in scored_candidates
                            if row.get("raw_final_score", row["final_score"])
                            >= min_backoff_score
                        ]
                        if role_filter and b.enable_semantic_tag_filter:
                            role_compatible_pool = [
                                row
                                for row in backoff_pool
                                if self._has_allowed_semantic_tag(
                                    role_filter,
                                    row.get("term"),
                                )
                            ]
                            if role_compatible_pool:
                                backoff_pool = role_compatible_pool

                        if backoff_pool:
                            backoff_candidate = max(
                                backoff_pool,
                                key=lambda row: (
                                    row.get("raw_final_score", row["final_score"]),
                                    row.get("normalized_head_match", 0.0),
                                    -row.get("unmatched_modifier_count", 0),
                                    -row["extra_qualifier_ratio"],
                                    row["coverage"],
                                    row["lexical"],
                                    row["discriminative_coverage"],
                                ),
                            )

                    if backoff_candidate is None:
                        local_best_id = None
                        local_best_term = None
                        local_best_score = 0.0
                    else:
                        local_best_id = backoff_candidate["concept_id"]
                        local_best_term = backoff_candidate["term"]
                        local_best_score = backoff_candidate["final_score"]
                if (
                    local_best_id is not None
                    and (
                        top.get("raw_final_score", top["final_score"])
                        - runner.get("raw_final_score", runner["final_score"])
                    )
                    <= b.guarded_fallback_margin
                    and top["discriminative_coverage"]
                    < b.min_discriminative_coverage_for_top
                    and runner["discriminative_coverage"]
                    > top["discriminative_coverage"]
                    and runner["coverage"] >= top["coverage"]
                ):
                    local_best_id = runner["concept_id"]
                    local_best_term = runner["term"]
                    local_best_score = runner["final_score"]
                if (
                    local_best_id is not None
                    and self._should_prefer_lower_qualifier_tie(top, runner)
                ):
                    local_best_id = runner["concept_id"]
                    local_best_term = runner["term"]
                    local_best_score = runner["final_score"]
                if local_best_id is not None and self._should_vector_rank_promote(
                    top, runner
                ):
                    local_best_id = runner["concept_id"]
                    local_best_term = runner["term"]
                    local_best_score = runner["final_score"]

            if b.enable_grounding_candidate_debug and candidate_debug_rows:
                top_rows = sorted(
                    candidate_debug_rows,
                    key=lambda row: row.get("raw_final_score", row["final_score"]),
                    reverse=True,
                )[:5]
                logger.info(
                    "Grounding top candidates term='%s' role='%s': %s",
                    term,
                    role_filter or "ANY",
                    top_rows,
                )
            return (
                local_best_id,
                local_best_term,
                local_best_score,
                scored_candidates,
                {"gold_filter_reasons": gold_filter_reasons},
            )

        (
            best_id,
            best_term,
            best_score,
            ranked_candidates,
            scoring_trace,
        ) = score_candidates(concept_items, role)
        if trace_enabled:
            gold_presence_trace["gold_filter_reasons"] = list(
                (scoring_trace or {}).get("gold_filter_reasons") or []
            )

        if b.off_domain_min_score is not None and role:
            if best_score < b.off_domain_min_score:
                fallback_items = concept_items_all
                if len(fallback_items) > MAX_CONCEPT_CANDIDATES:
                    fallback_items = fallback_items[:MAX_CONCEPT_CANDIDATES]
                (
                    off_id,
                    off_term,
                    off_score,
                    off_ranked,
                    _off_trace,
                ) = score_candidates(fallback_items, None)
                if off_score >= b.off_domain_min_score and off_score > best_score:
                    best_id, best_term, best_score, ranked_candidates = (
                        off_id,
                        off_term,
                        off_score,
                        off_ranked,
                    )

        if self._has_disallowed_semantic_tag(best_term):
            if trace_enabled and gold_concept_id is not None:
                gold_presence_trace["gold_absence_stage"] = (
                    "prediction_blocked_disallowed_semantic_tag"
                )
            return _return_result(
                None, None, 0.0, ranked_candidates, gold_presence_trace
            )
        if b.enable_semantic_tag_filter and not self._has_allowed_semantic_tag(
            role, best_term
        ):
            if trace_enabled and gold_concept_id is not None:
                gold_presence_trace["gold_absence_stage"] = (
                    "prediction_blocked_semantic_tag_filter"
                )
            return _return_result(
                None, None, 0.0, ranked_candidates, gold_presence_trace
            )

        if trace_enabled and gold_concept_id is not None:
            gold_candidate = None
            for candidate in ranked_candidates:
                if candidate.get("concept_id") == gold_concept_id:
                    gold_candidate = candidate
                    break
            gold_presence_trace["gold_in_final_ranked"] = gold_candidate is not None
            gold_presence_trace["gold_rank_final"] = (
                int(gold_candidate.get("rank") or 0) or None
                if gold_candidate is not None
                else None
            )
            if gold_candidate is None:
                if not gold_presence_trace.get("gold_in_initial_results"):
                    gold_presence_trace["gold_absence_stage"] = "not_retrieved"
                elif not gold_presence_trace.get("gold_in_allowed_domain"):
                    gold_presence_trace["gold_absence_stage"] = (
                        "filtered_by_domain_roots"
                    )
                elif not gold_presence_trace.get("gold_in_truncated_set"):
                    gold_presence_trace["gold_absence_stage"] = (
                        "truncated_before_scoring"
                    )
                elif gold_presence_trace.get("gold_filter_reasons"):
                    gold_presence_trace["gold_absence_stage"] = "filtered_pre_score"
                else:
                    gold_presence_trace["gold_absence_stage"] = (
                        "lost_during_scoring_or_ranking"
                    )
            else:
                gold_presence_trace["gold_absence_stage"] = "ranked"

        _ = time.perf_counter() - search_start
        return _return_result(
            best_id,
            best_term,
            best_score,
            ranked_candidates,
            gold_presence_trace,
        )

    def ground_extracted_concepts(self, extracted: List[Any]) -> List[GroundedConcept]:
        b = self.builder
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
                        target_label=b._fallback_target_label_for_role("Other"),
                    )
                )
                continue
            cached = b.index.lookup(concept.entity_standardized_candidate)
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
                    fallback_label = b._fallback_target_label_for_role(concept.role)
                    if fallback_label:
                        cached["target_label"] = fallback_label
                if b._should_skip_concept(
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
            concept_id, preferred_term, score = self.ground_entity(
                search_term,
                concept.role,
                query_context=self._build_context_hint(concept),
            )
            path_ids = b._get_taxonomy_path_cached(concept_id)
            target_label = b._resolve_target_label(path_ids)
            if target_label is None and concept.role:
                target_label = b._resolve_target_label_for_role(concept.role, path_ids)
            if target_label is None and concept.role and len(path_ids) <= 1:
                target_label = b._fallback_target_label_for_role(concept.role)
            taxonomy_path = b._format_taxonomy_path(path_ids)
            alt_names: List[str] = []

            if concept_id is None or score < b.min_match_score:
                concept_id = None
                preferred_term = None
                score = 0.0
                path_ids = []
                taxonomy_path = []
                alt_names = []
                target_label = b._fallback_target_label_for_role(concept.role)
            else:
                alt_names = b._get_alt_names(concept_id, preferred_term)

            if b._should_skip_concept(
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

            b.index.add(
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

        b.index.save()
        b._log_grounded_concepts(grounded)
        return grounded

    def get_concept_term(self, concept_id_value: Any) -> str:
        if not concept_id_value:
            return ""
        try:
            concept_id_int = int(concept_id_value)
        except (TypeError, ValueError):
            return ""
        return self.builder._get_preferred_term(concept_id_int) or ""

    def close(self) -> None:
        if self.builder.vector_retriever and hasattr(
            self.builder.vector_retriever, "close"
        ):
            self.builder.vector_retriever.close()
        if self.builder.snomed_explorer and hasattr(
            self.builder.snomed_explorer, "close"
        ):
            self.builder.snomed_explorer.close()
