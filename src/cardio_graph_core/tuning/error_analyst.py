from __future__ import annotations

from typing import List

from cardio_graph_core.tuning.contracts import (
    ErrorAnalysis,
    ErrorClassSummary,
    ScoreReport,
)
from cardio_graph_core.tuning.llm_bridge import LLMBridge
from cardio_graph_core.tuning.score_adapter import aggregate_error_counts

SYSTEM_PROMPT = """
You are LLM2 (error analyst) for medical extraction autotuning.
Given deterministic error summaries, identify top root-cause classes.
Return strict JSON object with keys: top_classes, selected_targets.
Each top_classes item: class (string), count (int), confidence (float 0..1), root_cause_hypothesis (string).
selected_targets must contain at most 2 class labels.
""".strip()


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
                }
            )
        evidence.append(
            {
                "row_id": row.row_id,
                "error_count": len(row.errors),
                "class_counts": class_counts,
                "examples": examples,
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
    def __init__(self, llm_bridge: LLMBridge):
        self.llm_bridge = llm_bridge

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
            payload = self.llm_bridge.generate_json(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=prompt,
                temperature=0.0,
                max_tokens=1500,
            )
            top_classes = []
            for item in payload.get("top_classes", [])[:5]:
                top_classes.append(
                    ErrorClassSummary(
                        error_class=str(item.get("class", "UNKNOWN")),
                        count=int(item.get("count", 0)),
                        confidence=float(item.get("confidence", 0.5)),
                        root_cause_hypothesis=str(
                            item.get("root_cause_hypothesis", "")
                        ),
                    )
                )
            selected_targets = [str(x) for x in payload.get("selected_targets", [])][:2]
            if not top_classes:
                return _fallback_analysis(report.run_id, report)
            if not selected_targets:
                selected_targets = [entry.error_class for entry in top_classes[:2]]
            return ErrorAnalysis(
                run_id=report.run_id,
                top_classes=top_classes,
                selected_targets=selected_targets,
            )
        except Exception:
            return _fallback_analysis(report.run_id, report)
