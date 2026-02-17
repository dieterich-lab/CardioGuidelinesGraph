from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

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

        row_errors.append(RowErrors(row_id=str(row.get("row_id")), errors=errors))

    concept_precision = _safe_div(total_concept_matches, total_actual_concepts)
    concept_recall = _safe_div(total_concept_matches, total_expected_concepts)
    concept_f1 = _safe_div(
        2 * concept_precision * concept_recall,
        concept_precision + concept_recall,
    )

    rule_exact_match = _safe_div(total_rule_matches, total_expected_rules)

    metrics = Metrics(
        schema_valid_rate=1.0 if run_success else 0.0,
        rule_exact_match=rule_exact_match,
        operator_accuracy=rule_exact_match,
        logic_group_accuracy=rule_exact_match,
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
