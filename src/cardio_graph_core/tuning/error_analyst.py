from __future__ import annotations

from typing import List

from cardio_graph_core.extraction.clients import create_client_registry
from cardio_graph_core.tuning.contracts import (
    ErrorAnalysis,
    ErrorClassSummary,
    ScoreReport,
)
from cardio_graph_core.tuning.score_adapter import aggregate_error_counts


def _row_evidence(
    report: ScoreReport, max_rows: int = 5, max_errors: int = 4
) -> list[dict]:
    ranked_rows = sorted(report.rows, key=lambda row: len(row.errors), reverse=True)
    evidence = []
    for row in ranked_rows[:max_rows]:
        class_counts: dict[str, int] = {}
        examples = []
        for error in row.errors[:max_errors]:
            class_counts[error.error_class] = class_counts.get(error.error_class, 0) + 1
            examples.append(
                {
                    "class": error.error_class,
                    "expected": error.expected,
                    "actual": error.actual,
                    "severity": error.severity,
                    "details": error.details,
                }
            )

        ground_truth_text = row.row_context.get("ground_truth_text") or {}
        row_text = (
            ground_truth_text.get("Recommendations")
            or ground_truth_text.get("Recommendation")
            or ground_truth_text.get("recommendation")
            or ""
        )
        header = {
            key: value
            for key, value in ground_truth_text.items()
            if key
            not in {
                "Recommendations",
                "Recommendation",
                "recommendation",
                "Class",
                "Class a",
                "Level",
                "Level b",
            }
        }
        footer = {
            key: ground_truth_text.get(key)
            for key in ("Class", "Class a", "Level", "Level b")
            if ground_truth_text.get(key) is not None
        }

        evidence.append(
            {
                "row_id": row.row_id,
                "error_count": len(row.errors),
                "class_counts": class_counts,
                "examples": examples,
                "header": header,
                "row": row_text,
                "footer": footer,
                "ground_truth": ground_truth_text,
                "expected_entries_display": row.row_context.get(
                    "expected_entries_display"
                ),
                "actual_entries_display": row.row_context.get("actual_entries_display"),
                "concept_summary": row.row_context.get("concept_summary"),
                "rule_summary": row.row_context.get("rule_summary"),
            }
        )
    return evidence


def _fallback_analysis(run_id: str, report: ScoreReport) -> ErrorAnalysis:
    counts = aggregate_error_counts(report)
    top = list(counts.items())[:2]
    top_classes: List[ErrorClassSummary] = []
    for error_class, count in top:
        top_classes.append(
            ErrorClassSummary(
                error_class=error_class,
                count=count,
                confidence=0.6,
                root_cause_hypothesis="Heuristic fallback from deterministic counts",
            )
        )
    return ErrorAnalysis(
        run_id=run_id,
        top_classes=top_classes,
        selected_targets=[item.error_class for item in top_classes],
    )


class ErrorAnalyst:
    def __init__(self, model_name: str, node: str, port: int):
        self.client_registry = create_client_registry(model_name, node, port)
        self.last_debug: dict = {}

    def analyze(self, report: ScoreReport) -> ErrorAnalysis:
        counts = aggregate_error_counts(report)
        row_evidence = _row_evidence(report)
        prompt = (
            f"run_id={report.run_id}\n"
            f"split={report.split}\n"
            f"metrics={report.metrics.to_dict()}\n"
            f"error_counts={counts}\n"
            f"row_evidence={row_evidence}\n"
            "Each example includes expected (ground-truth side) and actual (model output side).\n"
            "Return top classes and selected targets only as JSON."
        )
        try:
            from cardio_graph_core.extraction.baml_client.sync_client import b

            payload = b.AnalyzeTable22Errors(
                prompt,
                baml_options={"client_registry": self.client_registry},
            )
            self.last_debug = {
                "status": "baml_success",
            }
            top_classes = []
            for item in (getattr(payload, "top_classes", None) or [])[:5]:
                top_classes.append(
                    ErrorClassSummary(
                        error_class=str(
                            getattr(item, "error_class", None)
                            or getattr(item, "class", "UNKNOWN")
                        ),
                        count=int(getattr(item, "count", 0)),
                        confidence=float(getattr(item, "confidence", 0.5)),
                        root_cause_hypothesis=str(
                            getattr(item, "root_cause_hypothesis", "")
                        ),
                    )
                )
            selected_targets = [
                str(x) for x in (getattr(payload, "selected_targets", None) or [])
            ][:2]
            if not top_classes:
                self.last_debug["status"] = "fallback_empty_top_classes"
                return _fallback_analysis(report.run_id, report)
            if not selected_targets:
                selected_targets = [entry.error_class for entry in top_classes[:2]]
            return ErrorAnalysis(
                run_id=report.run_id,
                top_classes=top_classes,
                selected_targets=selected_targets,
            )
        except Exception as exc:
            self.last_debug = {
                "status": "fallback_exception",
                "error": str(exc),
            }
            return _fallback_analysis(report.run_id, report)
