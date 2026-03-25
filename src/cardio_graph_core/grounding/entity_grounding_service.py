from __future__ import annotations

import json
import re
import time
from typing import Any, Dict, List, Optional, Tuple

from cardio_graph_core.extraction.guideline_graph_builder import (
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
    ) -> Tuple[Optional[int], Optional[str], float]:
        b = self.builder
        if not term:
            return None, None, 0.0

        search_start = time.perf_counter()

        stripped_term = re.sub(r"\s*\([^)]*\)\s*", " ", term).strip()
        normalized_term = b._normalize(term)
        paren_tokens = []
        for group in re.findall(r"\(([^)]+)\)", term):
            for token in re.findall(r"[A-Za-z0-9]+", group):
                if token:
                    paren_tokens.append(token)

        normalized_tokens = [
            t
            for t in b._normalize(term).split()
            if len(t) > 2 and t not in STOPWORD_TOKENS
        ]
        important_tokens = b._important_tokens(term)
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

        results = []
        seen = set()
        for t in search_terms:
            if t in seen:
                continue
            seen.add(t)
            cached = b._search_cache.get(t)
            if cached is None:
                explorer = b._ensure_snomed_connected()
                cached = explorer.search_concepts_by_term(t, limit=limit)
                b._search_cache[t] = cached
            results.extend(cached)

        vector_results: List[Dict[str, Any]] = []
        vector_score_by_concept: Dict[int, float] = {}
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
            for context_variant in b._context_query_variants(query_context):
                vector_search_terms.append(context_variant)
                vector_search_terms.append(f"{term} {context_variant}")
            seen_vector_terms = set()
            for vt in vector_search_terms:
                vt = " ".join(str(vt or "").split()).strip()
                vt_key = b._normalize(vt)
                if not vt_key or vt_key in seen_vector_terms:
                    continue
                seen_vector_terms.add(vt_key)
                retrieved, score_map = b._vector_candidates(vt)
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
            important_query_tokens.update(b._important_tokens(q))

        def score_candidates(concept_items_to_score, role_filter):
            candidate_debug_rows: List[Dict[str, Any]] = []
            scored_candidates: List[Dict[str, Any]] = []
            normalized_query_terms = {
                b._normalize(q) for q in query_terms if b._normalize(q)
            }
            normalized_source_term = b._normalize(term)
            is_role_tension_term = normalized_source_term in b.role_tension_terms
            for concept_id, terms in concept_items_to_score:
                role_mismatch = bool(role_filter) and not b._candidate_matches_role(
                    concept_id, role_filter
                )
                if role_mismatch and not b.enable_role_soft_constraints:
                    continue
                preferred = b._get_preferred_term(concept_id)
                candidates = list(terms)
                if preferred:
                    candidates.append(preferred)

                if important_query_tokens:
                    if not any(
                        important_query_tokens & set(b._important_tokens(candidate))
                        for candidate in candidates
                    ):
                        continue

                score = 0.0
                best_candidate_term = None
                best_candidate_overlap = 0.0
                for candidate in candidates:
                    candidate_norm = b._normalize(candidate)
                    candidate_tokens = set(b._important_tokens(candidate))
                    candidate_score = max(
                        (b._score(q, candidate) for q in query_terms if q),
                        default=0.0,
                    )
                    stripped_norm = b._normalize(stripped_term) if stripped_term else ""
                    if stripped_norm and stripped_norm in candidate_norm:
                        candidate_score = candidate_score + 0.05
                    if paren_tokens and any(
                        token.lower() in candidate_norm for token in paren_tokens
                    ):
                        candidate_score = candidate_score + 0.03
                    overlap_ratio = b._token_overlap_ratio(
                        important_query_tokens, candidate
                    )
                    weighted_coverage = b._weighted_query_coverage(
                        important_query_tokens, candidate_tokens
                    )
                    if overlap_ratio:
                        candidate_score = candidate_score + overlap_ratio * 0.08
                    if weighted_coverage:
                        candidate_score = candidate_score + weighted_coverage * 0.10
                    penalty = b._specificity_penalty(
                        important_query_tokens, candidate_tokens
                    )
                    if penalty:
                        candidate_score = max(0.0, candidate_score - penalty)
                    if candidate_score > score:
                        score = candidate_score
                        best_candidate_term = candidate
                        best_candidate_overlap = weighted_coverage

                preferred_overlap = b._token_overlap_ratio(
                    important_query_tokens, preferred or ""
                )
                best_overlap = max(
                    preferred_overlap,
                    best_candidate_overlap,
                )

                discriminative_tokens = b._discriminative_query_tokens(
                    important_query_tokens
                )
                candidate_tokens_for_best = set(
                    b._important_tokens(best_candidate_term or preferred or "")
                )
                discriminative_coverage = 0.0
                if discriminative_tokens:
                    discriminative_coverage = len(
                        discriminative_tokens & candidate_tokens_for_best
                    ) / max(len(discriminative_tokens), 1)
                final_penalty = 0.0
                if (
                    important_query_tokens
                    and best_overlap < b.min_weighted_query_coverage
                ):
                    final_penalty += b.low_coverage_penalty
                if discriminative_tokens and not (
                    discriminative_tokens & candidate_tokens_for_best
                ):
                    final_penalty += b.missing_discriminative_penalty
                extra_qualifier_ratio = b._extra_qualifier_ratio(
                    important_query_tokens, candidate_tokens_for_best
                )
                final_penalty += (
                    extra_qualifier_ratio * b.extra_qualifier_penalty_weight
                )
                final_penalty += b._hard_negative_penalty_for(
                    normalized_source_term,
                    role_filter,
                    concept_id,
                )
                semantic_penalty = b._role_semantic_penalty(role_filter, preferred)
                final_penalty += semantic_penalty
                if role_mismatch:
                    final_penalty += b.role_mismatch_penalty
                if role_mismatch and is_role_tension_term:
                    final_penalty += b.role_tension_penalty

                vector_raw = vector_score_by_concept.get(int(concept_id), 0.0)
                vector_bonus = 0.0
                if score >= b.vector_min_lexical_for_bonus:
                    vector_bonus = min(
                        b.vector_bonus_cap,
                        vector_raw * b.vector_rerank_weight,
                    )
                final_score = min(1.0, max(0.0, score + vector_bonus - final_penalty))

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
                            "vector_raw": round(vector_raw, 6),
                            "vector_bonus": round(vector_bonus, 6),
                            "semantic_penalty": round(semantic_penalty, 6),
                            "role_mismatch": role_mismatch,
                            "final_penalty": round(final_penalty, 6),
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
                    }
                )

            if not scored_candidates:
                return None, None, 0.0

            scored_candidates = sorted(
                scored_candidates,
                key=lambda row: (
                    row["final_score"],
                    row["coverage"],
                    row["lexical"],
                    row["discriminative_coverage"],
                    -row["extra_qualifier_ratio"],
                ),
                reverse=True,
            )

            local_best = scored_candidates[0]
            local_best_id = local_best["concept_id"]
            local_best_term = local_best["term"]
            local_best_score = local_best["final_score"]

            if len(scored_candidates) > 1:
                top_two = sorted(
                    scored_candidates,
                    key=lambda row: row["final_score"],
                    reverse=True,
                )[:2]
                top = top_two[0]
                runner = top_two[1]
                if (
                    b.ambiguity_abstain_margin > 0.0
                    and (top["final_score"] - runner["final_score"])
                    <= b.ambiguity_abstain_margin
                    and top["coverage"] < b.ambiguity_min_coverage
                    and runner["coverage"] < b.ambiguity_min_coverage
                    and top["lexical"] < b.ambiguity_lexical_force_pick
                ):
                    backoff_candidate = None
                    if b.ambiguity_confidence_backoff_enabled:
                        min_backoff_score = max(
                            b.ambiguity_backoff_min_score,
                            top["final_score"] - b.ambiguity_backoff_max_drop,
                        )
                        backoff_pool = [
                            row
                            for row in scored_candidates
                            if row["final_score"] >= min_backoff_score
                        ]
                        if role_filter and b.enable_semantic_tag_filter:
                            role_compatible_pool = [
                                row
                                for row in backoff_pool
                                if b._has_allowed_semantic_tag(
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
                                    row["final_score"],
                                    row["coverage"],
                                    row["lexical"],
                                    row["discriminative_coverage"],
                                    -row["extra_qualifier_ratio"],
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
                    and (top["final_score"] - runner["final_score"])
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

            if b.enable_grounding_candidate_debug and candidate_debug_rows:
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

        if b.off_domain_min_score is not None and role:
            if best_score < b.off_domain_min_score:
                fallback_items = concept_items_all
                if len(fallback_items) > MAX_CONCEPT_CANDIDATES:
                    fallback_items = fallback_items[:MAX_CONCEPT_CANDIDATES]
                off_id, off_term, off_score = score_candidates(fallback_items, None)
                if off_score >= b.off_domain_min_score and off_score > best_score:
                    best_id, best_term, best_score = off_id, off_term, off_score

        if b._has_disallowed_semantic_tag(best_term):
            return None, None, 0.0
        if b.enable_semantic_tag_filter and not b._has_allowed_semantic_tag(
            role, best_term
        ):
            return None, None, 0.0

        _ = time.perf_counter() - search_start

        return best_id, best_term, best_score

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
                    b._important_tokens(
                        concept.entity_standardized_candidate
                        or concept.entity_original
                        or ""
                    )
                )
                if (
                    cache_tokens
                    and b._token_overlap_ratio(cache_tokens, cache_term) < 0.5
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
                target_label = b._resolve_target_label_for_role(
                    concept.role, path_ids
                )
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
        if self.builder.vector_retriever and hasattr(self.builder.vector_retriever, "close"):
            self.builder.vector_retriever.close()
        if self.builder.snomed_explorer and hasattr(self.builder.snomed_explorer, "close"):
            self.builder.snomed_explorer.close()
