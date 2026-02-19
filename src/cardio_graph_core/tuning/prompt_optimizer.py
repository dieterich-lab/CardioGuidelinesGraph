from __future__ import annotations

from cardio_graph_core.tuning.contracts import (
    ErrorAnalysis,
    PromptEdit,
    PromptPatch,
    ScoreReport,
)
from cardio_graph_core.tuning.llm_bridge import LLMBridge

SYSTEM_PROMPT = """
You are LLM3 (prompt optimizer) for extraction autotuning.
Propose a minimal prompt appendix patch that targets the selected error classes.
Return strict JSON with keys:
- edits (array of objects with keys: zone, content)
- rationale (string)
- max_edit_lines (int)
Allowed zones: instruction_appendix, rule_structuring, condition_extraction, action_extraction, operator_logic.
Keep edits concise and actionable.
""".strip()


def _fallback_instruction(targets: list[str]) -> str:
    lines = [
        "Prioritize strict IF/THEN separation: conditions on left, actions on right.",
        "Do not infer PLANNED unless explicit scheduling intent is present.",
        "Preserve OR and AND groupings exactly as written in coordinated phrases.",
    ]
    if targets:
        lines.append("Focus classes: " + ", ".join(targets))
    return "\n".join(lines)


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


class PromptOptimizer:
    def __init__(self, llm_bridge: LLMBridge):
        self.llm_bridge = llm_bridge

    def propose_patch(
        self,
        base_prompt_version: str,
        candidate_prompt_version: str,
        current_prompt_appendix: str,
        analysis: ErrorAnalysis,
        score_report: ScoreReport,
    ) -> PromptPatch:
        row_evidence = _row_evidence(score_report)
        prompt = (
            f"base_prompt_version={base_prompt_version}\n"
            f"candidate_prompt_version={candidate_prompt_version}\n"
            f"current_metrics={score_report.metrics.to_dict()}\n"
            f"selected_targets={analysis.selected_targets}\n"
            f"top_classes={[entry.to_dict() for entry in analysis.top_classes]}\n"
            f"row_evidence={row_evidence}\n"
            "Each example includes expected (ground-truth side) and actual (model output side).\n"
            f"current_prompt_appendix={current_prompt_appendix!r}\n"
            "Return JSON only."
        )
        rationale = ""
        max_edit_lines = 30
        edits: list[PromptEdit] = []
        try:
            payload = self.llm_bridge.generate_json(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=prompt,
                temperature=0.0,
                max_tokens=1200,
            )
            rationale = str(payload.get("rationale", "")).strip()
            max_edit_lines = int(payload.get("max_edit_lines", 30))

            raw_edits = payload.get("edits")
            if isinstance(raw_edits, list):
                for item in raw_edits:
                    if not isinstance(item, dict):
                        continue
                    zone = str(item.get("zone", "")).strip() or "instruction_appendix"
                    content = str(item.get("content", "")).strip()
                    if not content:
                        continue
                    edits.append(
                        PromptEdit(
                            zone=zone,
                            change_type="append",
                            old=current_prompt_appendix,
                            new=content,
                        )
                    )

            if not edits:
                legacy_appendix = str(payload.get("instruction_appendix", "")).strip()
                if legacy_appendix:
                    edits.append(
                        PromptEdit(
                            zone="instruction_appendix",
                            change_type="append",
                            old=current_prompt_appendix,
                            new=legacy_appendix,
                        )
                    )
        except Exception:
            edits = []

        if not edits:
            instruction_appendix = _fallback_instruction(analysis.selected_targets)
            rationale = (
                "Fallback optimizer instruction (LLM unavailable or invalid JSON)."
            )
            edits = [
                PromptEdit(
                    zone="instruction_appendix",
                    change_type="append",
                    old=current_prompt_appendix,
                    new=instruction_appendix,
                )
            ]

        return PromptPatch(
            base_prompt_version=base_prompt_version,
            candidate_prompt_version=candidate_prompt_version,
            target_classes=analysis.selected_targets,
            edits=edits,
            max_edit_lines=max_edit_lines,
            rationale=rationale,
        )
