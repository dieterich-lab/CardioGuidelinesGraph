from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

from cardio_graph_core.tuning.contracts import (
    ErrorItem,
    Metrics,
    RowErrors,
    ScoreReport,
)

SEMANTIC_REPLACEMENTS = {
    "cabg": "coronary artery bypass graft",
    "pci": "percutaneous coronary intervention",
    "mi": "myocardial infarction",
    "acs": "acute coronary syndrome",
    "dapt": "dual antiplatelet therapy",
    "ccs": "chronic coronary syndrome",
    "pad": "peripheral arterial disease",
}

_LLM_SEMANTIC_CACHE: Dict[Tuple[str, str, str], float] = {}
_LLM_SEMANTIC_CALLS = 0


def _safe_div(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0
    return numerator / denominator


def _concept_key(entry: Dict[str, Any]) -> Tuple[Any, Any]:
    return (entry.get("role"), _canonical_phrase(entry.get("entity")))


def _entry_order_key(entry: Dict[str, Any]) -> Tuple[str, str]:
    return (
        str(entry.get("logic_group") or ""),
        json.dumps(entry, sort_keys=True, default=str),
    )


def _tokenize(text: Any) -> set[str]:
    if text is None:
        return set()
    cleaned = re.sub(r"[^a-z0-9]+", " ", str(text).lower())
    return {token for token in cleaned.split() if token}


def _canonical_phrase(text: Any) -> str:
    if text is None:
        return ""
    normalized = re.sub(r"[^a-z0-9]+", " ", str(text).lower()).strip()
    if not normalized:
        return ""
    for source, target in SEMANTIC_REPLACEMENTS.items():
        normalized = re.sub(rf"\b{re.escape(source)}\b", target, normalized)
    return " ".join(normalized.split())


def _semantic_normalization_enabled() -> bool:
    return (
        os.environ.get("CARDIO_GRAPH_TUNING_ENABLE_SEMANTIC_NORMALIZATION", "true")
        .lower()
        .strip()
        == "true"
    )


def _llm_semantic_match_enabled() -> bool:
    return (
        os.environ.get("CARDIO_GRAPH_TUNING_LLM_SEMANTIC_MATCH", "false")
        .lower()
        .strip()
        == "true"
    )


def _llm_semantic_max_calls() -> int:
    raw = os.environ.get("CARDIO_GRAPH_TUNING_LLM_SEMANTIC_MAX_CALLS", "0")
    try:
        return max(0, int(raw))
    except (TypeError, ValueError):
        return 0


def _llm_semantic_model() -> str:
    return os.environ.get("CARDIO_GRAPH_TUNING_LLM_SEMANTIC_MODEL", "Qwen3next")


def _llm_semantic_node() -> str:
    return os.environ.get("CARDIO_GRAPH_TUNING_LLM_SEMANTIC_NODE", "g5")


def _llm_semantic_port() -> int:
    raw = os.environ.get("CARDIO_GRAPH_TUNING_LLM_SEMANTIC_PORT", "11435")
    try:
        return int(raw)
    except (TypeError, ValueError):
        return 11435


def _llm_semantic_equivalent(expected: str, actual: str, role: str) -> float:
    global _LLM_SEMANTIC_CALLS

    key = (role.lower(), expected.lower(), actual.lower())
    if key in _LLM_SEMANTIC_CACHE:
        return _LLM_SEMANTIC_CACHE[key]

    if not _llm_semantic_match_enabled():
        _LLM_SEMANTIC_CACHE[key] = 0.0
        return 0.0

    max_calls = _llm_semantic_max_calls()
    if max_calls <= 0 or _LLM_SEMANTIC_CALLS >= max_calls:
        _LLM_SEMANTIC_CACHE[key] = 0.0
        return 0.0

    try:
        from cardio_graph_core.extraction.baml_client.sync_client import b
        from cardio_graph_core.extraction.clients import create_client_registry

        registry = create_client_registry(
            _llm_semantic_model(),
            _llm_semantic_node(),
            _llm_semantic_port(),
        )
        prompt = (
            "Decide if two medical concept phrases are semantically equivalent in guideline extraction context.\n"
            f"Role: {role}\n"
            f"Expected phrase: {expected}\n"
            f"Actual phrase: {actual}\n"
            "Answer with YES or NO as the first token. Optionally add one short reason."
        )
        response = b.QuestionWithoutContext(
            prompt,
            baml_options={"client_registry": registry},
        )
        _LLM_SEMANTIC_CALLS += 1
        text = str(getattr(response, "explanation", "")).strip().lower()
        if text.startswith("yes"):
            _LLM_SEMANTIC_CACHE[key] = 1.0
            return 1.0
        _LLM_SEMANTIC_CACHE[key] = 0.0
        return 0.0
    except Exception:
        _LLM_SEMANTIC_CACHE[key] = 0.0
        return 0.0


def _entry_aliases(entry: Dict[str, Any]) -> List[str]:
    candidates: List[str] = []
    for key in ("entity", "entity_original", "preferred_term"):
        value = entry.get(key)
        if value:
            candidates.append(str(value))
    synonyms = entry.get("synonyms") or []
    if isinstance(synonyms, list):
        for synonym in synonyms:
            if synonym:
                candidates.append(str(synonym))

    # Preserve order but deduplicate.
    seen = set()
    ordered = []
    semantic_normalization = _semantic_normalization_enabled()
    for candidate in candidates:
        normalized = candidate.strip().lower()
        if semantic_normalization:
            normalized = _canonical_phrase(normalized)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized if semantic_normalization else candidate)
    return ordered


def _entry_similarity(expected: Dict[str, Any], actual: Dict[str, Any]) -> float:
    if expected.get("role") != actual.get("role"):
        return 0.0
    best = 0.0
    for expected_alias in _entry_aliases(expected):
        expected_tokens = _tokenize(expected_alias)
        if not expected_tokens:
            continue
        for actual_alias in _entry_aliases(actual):
            actual_tokens = _tokenize(actual_alias)
            if not actual_tokens:
                continue
            overlap = expected_tokens.intersection(actual_tokens)
            coverage = len(overlap) / len(expected_tokens)
            if coverage > best:
                best = coverage
            if coverage >= 0.55:
                # Good enough lexical overlap; skip expensive LLM call.
                continue
            llm_score = _llm_semantic_equivalent(
                expected_alias,
                actual_alias,
                str(expected.get("role") or ""),
            )
            if llm_score > best:
                best = llm_score
    return best


def _rule_fields_match(expected: Dict[str, Any], actual: Dict[str, Any]) -> bool:
    comparable_keys = (
        "operator",
        "threshold",
        "unit",
        "context",
        "logic_type",
        "logic_group",
        "strength",
        "level",
        "direction",
    )
    return all(expected.get(key) == actual.get(key) for key in comparable_keys)


def _entry_side(entry: Dict[str, Any]) -> str | None:
    role_name = str(entry.get("role") or "").strip()
    if role_name in {"ClinicalCondition", "ClinicalParameter", "Condition"}:
        return "condition"
    if role_name in {"Procedure", "Medication", "ClinicalAction"}:
        logic_type = str(entry.get("logic_type") or "").strip()
        logic_group = str(entry.get("logic_group") or "").strip()
        if logic_type or logic_group:
            return "condition"
        return "action"
    return None


def _side_counts(entries: List[Dict[str, Any]]) -> Dict[str, int]:
    counts: Dict[str, int] = {"condition": 0, "action": 0}
    for entry in entries:
        side = _entry_side(entry)
        if side in counts:
            counts[side] += 1
    return counts


def _ignore_logic_fields_for_pair(
    expected_entry: Dict[str, Any],
    actual_entry: Dict[str, Any],
    expected_counts: Dict[str, int],
    actual_counts: Dict[str, int],
) -> bool:
    expected_side = _entry_side(expected_entry)
    actual_side = _entry_side(actual_entry)

    expected_singleton = (
        expected_side is not None and expected_counts.get(expected_side, 0) <= 1
    )
    actual_singleton = (
        actual_side is not None and actual_counts.get(actual_side, 0) <= 1
    )
    return expected_singleton or actual_singleton


def _rule_fields_match_for_pair(
    expected: Dict[str, Any],
    actual: Dict[str, Any],
    ignore_logic_fields: bool,
) -> bool:
    comparable_keys = [
        "operator",
        "threshold",
        "unit",
        "context",
        "strength",
        "level",
        "direction",
    ]
    if not ignore_logic_fields:
        comparable_keys.extend(["logic_type", "logic_group"])
    return all(expected.get(key) == actual.get(key) for key in comparable_keys)


def _pair_entries(
    expected_entries: List[Dict[str, Any]],
    actual_entries: List[Dict[str, Any]],
    threshold: float = 0.6,
) -> List[Tuple[Dict[str, Any], Dict[str, Any]]]:
    # Greedy one-to-one matching by highest semantic overlap.
    remaining_actual = sorted(actual_entries, key=_entry_order_key)
    pairs: List[Tuple[Dict[str, Any], Dict[str, Any]]] = []
    for expected_entry in sorted(expected_entries, key=_entry_order_key):
        best_index = -1
        best_similarity = 0.0
        for index, actual_entry in enumerate(remaining_actual):
            similarity = _entry_similarity(expected_entry, actual_entry)
            if similarity > best_similarity:
                best_similarity = similarity
                best_index = index
        if best_index >= 0 and best_similarity >= threshold:
            pairs.append((expected_entry, remaining_actual.pop(best_index)))
    return pairs


def build_score_report_from_alignment(
    alignment_path: Path,
    run_id: str,
    split: str,
    prompt_version: str,
    run_success: bool,
) -> ScoreReport:
    score_profile = (
        os.environ.get("CARDIO_GRAPH_TUNING_SCORE_PROFILE", "tolerant").lower().strip()
    )
    lenient_extras = (
        os.environ.get("CARDIO_GRAPH_TUNING_LENIENT_EXTRAS", "true").lower() == "true"
    )
    strict_extras = (score_profile == "strict") or (not lenient_extras)
    extra_concept_weight = float(
        os.environ.get(
            "CARDIO_GRAPH_TUNING_EXTRA_CONCEPT_WEIGHT",
            "1.0" if strict_extras else "0.25",
        )
    )
    extra_and_concept_weight = float(
        os.environ.get(
            "CARDIO_GRAPH_TUNING_EXTRA_AND_CONCEPT_WEIGHT",
            "1.0" if strict_extras else "0.10",
        )
    )

    payload = json.loads(alignment_path.read_text(encoding="utf-8"))
    rows = payload.get("rows", [])

    total_expected_concepts = 0
    total_actual_concepts = 0
    total_concept_matches = 0
    total_weighted_extra_concepts = 0.0

    total_expected_rules = 0
    total_rule_matches = 0

    total_operator_compared = 0
    total_operator_correct = 0
    total_logic_compared = 0
    total_logic_correct = 0

    total_grounded = 0
    total_groundable = 0

    row_errors: List[RowErrors] = []

    for row in rows:
        concept_summary = row.get("concept_summary", {})
        rule_summary = row.get("rule_summary", {})

        expected_entries = list(row.get("expected_entries") or [])
        actual_entries = list(row.get("actual_entries") or [])
        entry_pairs = _pair_entries(expected_entries, actual_entries)
        expected_counts = _side_counts(expected_entries)
        actual_counts = _side_counts(actual_entries)

        expected_concepts = len(expected_entries)
        actual_concepts = len(actual_entries)
        concept_matches = len(entry_pairs)

        expected_rules = len(expected_entries)
        rule_matches = 0
        for expected_entry, actual_entry in entry_pairs:
            ignore_logic_fields = _ignore_logic_fields_for_pair(
                expected_entry,
                actual_entry,
                expected_counts,
                actual_counts,
            )
            if _rule_fields_match_for_pair(
                expected_entry,
                actual_entry,
                ignore_logic_fields=ignore_logic_fields,
            ):
                rule_matches += 1

        total_expected_concepts += expected_concepts
        total_actual_concepts += actual_concepts
        total_concept_matches += concept_matches

        unmatched_actual_entries = list(actual_entries)
        for _, matched_actual in entry_pairs:
            try:
                unmatched_actual_entries.remove(matched_actual)
            except ValueError:
                pass
        weighted_extras = 0.0
        for extra_entry in unmatched_actual_entries:
            logic_type = str(extra_entry.get("logic_type") or "").upper()
            logic_group = str(extra_entry.get("logic_group") or "").lower()
            role = str(extra_entry.get("role") or "")
            is_condition_like = role in {
                "ClinicalCondition",
                "ClinicalParameter",
                "Condition",
            }
            if is_condition_like and (
                logic_type == "AND" or logic_group.startswith("and")
            ):
                weighted_extras += extra_and_concept_weight
            else:
                weighted_extras += extra_concept_weight
        total_weighted_extra_concepts += weighted_extras

        total_expected_rules += expected_rules
        total_rule_matches += rule_matches

        for expected_entry, actual_entry in entry_pairs:
            total_operator_compared += 1
            if expected_entry.get("operator") == actual_entry.get("operator"):
                total_operator_correct += 1

            ignore_logic_fields = _ignore_logic_fields_for_pair(
                expected_entry,
                actual_entry,
                expected_counts,
                actual_counts,
            )

            if not ignore_logic_fields:
                total_logic_compared += 1
                if expected_entry.get("logic_type") == actual_entry.get(
                    "logic_type"
                ) and expected_entry.get("logic_group") == actual_entry.get(
                    "logic_group"
                ):
                    total_logic_correct += 1

        grounding_summary = row.get("grounding_summary") or {}
        total_grounded += int(grounding_summary.get("total_grounded", 0) or 0)
        total_groundable += actual_concepts

        errors: List[ErrorItem] = []
        for item in row.get("concept_missing", []) or []:
            errors.append(
                ErrorItem(
                    error_class="B1_missing_concept",
                    severity="major",
                    expected=str(item),
                    actual=None,
                )
            )
        if strict_extras:
            for item in row.get("concept_extra", []) or []:
                errors.append(
                    ErrorItem(
                        error_class="B2_extra_concept",
                        severity="major",
                        expected=None,
                        actual=str(item),
                    )
                )
        for item in row.get("rule_missing", []) or []:
            errors.append(
                ErrorItem(
                    error_class="RULE_MISSING",
                    severity="major",
                    expected=str(item),
                    actual=None,
                )
            )
        if strict_extras:
            for item in row.get("rule_extra", []) or []:
                errors.append(
                    ErrorItem(
                        error_class="RULE_EXTRA",
                        severity="major",
                        expected=None,
                        actual=str(item),
                    )
                )

        for expected_entry, actual_entry in entry_pairs:
            concept_label = (
                f"{expected_entry.get('role')}: {expected_entry.get('entity')}"
            )
            ignore_logic_fields = _ignore_logic_fields_for_pair(
                expected_entry,
                actual_entry,
                expected_counts,
                actual_counts,
            )

            if expected_entry.get("operator") != actual_entry.get("operator"):
                errors.append(
                    ErrorItem(
                        error_class="C1_operator_wrong",
                        severity="major",
                        expected=str(expected_entry.get("operator")),
                        actual=str(actual_entry.get("operator")),
                        details={
                            "concept": concept_label,
                            "expected_entry": expected_entry,
                            "actual_entry": actual_entry,
                        },
                    )
                )

            if not ignore_logic_fields and expected_entry.get(
                "logic_type"
            ) != actual_entry.get("logic_type"):
                errors.append(
                    ErrorItem(
                        error_class="C5_logic_type_wrong",
                        severity="major",
                        expected=str(expected_entry.get("logic_type")),
                        actual=str(actual_entry.get("logic_type")),
                        details={
                            "concept": concept_label,
                            "expected_entry": expected_entry,
                            "actual_entry": actual_entry,
                        },
                    )
                )

            if not ignore_logic_fields and expected_entry.get(
                "logic_group"
            ) != actual_entry.get("logic_group"):
                errors.append(
                    ErrorItem(
                        error_class="C6_logic_group_wrong",
                        severity="major",
                        expected=str(expected_entry.get("logic_group")),
                        actual=str(actual_entry.get("logic_group")),
                        details={
                            "concept": concept_label,
                            "expected_entry": expected_entry,
                            "actual_entry": actual_entry,
                        },
                    )
                )

        row_errors.append(
            RowErrors(
                row_id=str(row.get("row_id")),
                errors=errors,
                row_context={
                    "ground_truth_text": row.get("ground_truth_text") or {},
                    "expected_entries_display": row.get("expected_entries_display"),
                    "actual_entries_display": row.get("actual_entries_display"),
                    "concept_summary": concept_summary,
                    "rule_summary": rule_summary,
                },
            )
        )

    precision_denominator = total_concept_matches + total_weighted_extra_concepts
    if strict_extras:
        precision_denominator = total_actual_concepts
    concept_precision = _safe_div(total_concept_matches, precision_denominator)
    concept_recall = _safe_div(total_concept_matches, total_expected_concepts)
    concept_f1 = _safe_div(
        2 * concept_precision * concept_recall,
        concept_precision + concept_recall,
    )

    rule_exact_match = _safe_div(total_rule_matches, total_expected_rules)
    operator_accuracy = _safe_div(total_operator_correct, total_operator_compared)
    logic_group_accuracy = _safe_div(total_logic_correct, total_logic_compared)

    metrics = Metrics(
        schema_valid_rate=1.0 if run_success else 0.0,
        rule_exact_match=rule_exact_match,
        operator_accuracy=operator_accuracy,
        logic_group_accuracy=logic_group_accuracy,
        concept_precision=concept_precision,
        concept_recall=concept_recall,
        concept_f1=concept_f1,
        grounding_hit_rate=_safe_div(total_grounded, total_groundable),
    )
    return ScoreReport(
        run_id=run_id,
        split=split,
        prompt_version=prompt_version,
        metrics=metrics,
        rows=row_errors,
    )


def aggregate_error_counts(report: ScoreReport) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for row in report.rows:
        for error in row.errors:
            counts[error.error_class] = counts.get(error.error_class, 0) + 1
    return dict(sorted(counts.items(), key=lambda kv: kv[1], reverse=True))
