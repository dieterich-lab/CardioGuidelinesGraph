from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

from cardio_graph_core.tuning.contracts import (
    ErrorItem,
    Metrics,
    RowErrors,
    ScoreReport,
)


def _safe_div(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0
    return numerator / denominator


def _concept_key(entry: Dict[str, Any]) -> Tuple[Any, Any]:
    return (entry.get("role"), entry.get("entity"))


def _entry_order_key(entry: Dict[str, Any]) -> Tuple[str, str]:
    return (
        str(entry.get("logic_group") or ""),
        json.dumps(entry, sort_keys=True, default=str),
    )


def _pair_entries(
    expected_entries: List[Dict[str, Any]],
    actual_entries: List[Dict[str, Any]],
) -> List[Tuple[Dict[str, Any], Dict[str, Any]]]:
    expected_by_concept: Dict[Tuple[Any, Any], List[Dict[str, Any]]] = {}
    actual_by_concept: Dict[Tuple[Any, Any], List[Dict[str, Any]]] = {}

    for entry in expected_entries:
        expected_by_concept.setdefault(_concept_key(entry), []).append(entry)
    for entry in actual_entries:
        actual_by_concept.setdefault(_concept_key(entry), []).append(entry)

    pairs: List[Tuple[Dict[str, Any], Dict[str, Any]]] = []
    for concept in set(expected_by_concept) & set(actual_by_concept):
        expected_list = sorted(expected_by_concept[concept], key=_entry_order_key)
        actual_list = sorted(actual_by_concept[concept], key=_entry_order_key)
        pairs.extend(zip(expected_list, actual_list))
    return pairs


def build_score_report_from_alignment(
    alignment_path: Path,
    run_id: str,
    split: str,
    prompt_version: str,
    run_success: bool,
) -> ScoreReport:
    payload = json.loads(alignment_path.read_text(encoding="utf-8"))
    rows = payload.get("rows", [])

    total_expected_concepts = 0
    total_actual_concepts = 0
    total_concept_matches = 0

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

        expected_concepts = int(concept_summary.get("expected", 0))
        actual_concepts = int(concept_summary.get("actual", 0))
        concept_matches = int(concept_summary.get("matches", 0))

        expected_rules = int(rule_summary.get("expected", 0))
        rule_matches = int(rule_summary.get("matches", 0))

        total_expected_concepts += expected_concepts
        total_actual_concepts += actual_concepts
        total_concept_matches += concept_matches

        total_expected_rules += expected_rules
        total_rule_matches += rule_matches

        expected_entries = list(row.get("expected_entries") or [])
        actual_entries = list(row.get("actual_entries") or [])
        entry_pairs = _pair_entries(expected_entries, actual_entries)

        for expected_entry, actual_entry in entry_pairs:
            total_operator_compared += 1
            if expected_entry.get("operator") == actual_entry.get("operator"):
                total_operator_correct += 1

            total_logic_compared += 1
            if (
                expected_entry.get("logic_type") == actual_entry.get("logic_type")
                and expected_entry.get("logic_group") == actual_entry.get("logic_group")
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
            concept_label = f"{expected_entry.get('role')}: {expected_entry.get('entity')}"

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

            if expected_entry.get("logic_type") != actual_entry.get("logic_type"):
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

            if expected_entry.get("logic_group") != actual_entry.get("logic_group"):
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

    concept_precision = _safe_div(total_concept_matches, total_actual_concepts)
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
