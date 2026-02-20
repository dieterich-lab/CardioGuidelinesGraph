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
Propose a minimal prompt appendix patch that targets the selected error classes and row-level structural mismatches.
Return strict JSON with keys:
- edits (array of objects with keys: zone, content)
- rationale (string)
- max_edit_lines (int)
Allowed zones: instruction_appendix, rule_structuring, condition_extraction, action_extraction, operator_logic.
Keep edits concise and actionable.
Hard constraints:
- Do NOT add illustrative examples, entity lists, or category primers.
- Do NOT restate known ontology categories.
- Every edit must be a transformation rule anchored to observed row evidence (row_id + mismatch type).
- Prioritize exact condition/action separation and operator/logic_group preservation from ground truth.
""".strip()


def _fallback_instruction(targets: list[str]) -> str:
    lines = [
        "Prioritize strict IF/THEN separation: conditions on left, actions on right.",
        "Do not infer PLANNED unless explicit scheduling intent is present.",
        "Preserve OR and AND groupings exactly as written in coordinated phrases.",
        "Do not add category primers or example entities; emit only extraction transformation rules.",
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
            if key not in {"Recommendations", "Recommendation", "recommendation", "Class", "Class a", "Level", "Level b"}
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


class PromptOptimizer:
    def __init__(self, llm_bridge: LLMBridge):
        self.llm_bridge = llm_bridge
        self.last_debug: dict = {}

    def propose_patch(
        self,
        base_prompt_version: str,
        candidate_prompt_version: str,
        current_prompt_appendix: str,
        analysis: ErrorAnalysis,
        score_report: ScoreReport,
        candidate_slot: str | None = None,
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
            "Ground-truth row context includes header/row/footer when available.\n"
            + (
                (
                    "candidate_slot="
                    f"{candidate_slot}. Use a materially distinct strategy from likely prior candidates "
                    "(different failure-mode focus and/or zone emphasis) while staying minimal and safe.\n"
                )
                if candidate_slot
                else ""
            )
            +
            f"current_prompt_appendix={current_prompt_appendix!r}\n"
            "Return JSON only. Keep edits row-anchored and avoid generic guidance."
        )
        rationale = ""
        max_edit_lines = 30
        edits: list[PromptEdit] = []
        llm_error = None
        try:
            payload, llm_debug = self.llm_bridge.generate_json_with_debug(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=prompt,
                temperature=0.0,
                max_tokens=1200,
            )
            self.last_debug = {
                "status": "llm_success",
                "llm": llm_debug,
            }
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
                raw_zone_map = payload.get("zone_edits")
                if isinstance(raw_zone_map, dict):
                    for zone, content in raw_zone_map.items():
                        zone_value = str(zone).strip() or "instruction_appendix"
                        content_value = str(content or "").strip()
                        if not content_value:
                            continue
                        edits.append(
                            PromptEdit(
                                zone=zone_value,
                                change_type="append",
                                old=current_prompt_appendix,
                                new=content_value,
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
        except Exception as exc:
            edits = []
            llm_error = str(exc)
            self.last_debug = {
                "status": "fallback_exception",
                "error": llm_error,
            }

        if not edits:
            instruction_appendix = _fallback_instruction(analysis.selected_targets)
            rationale = (
                "Fallback optimizer instruction (LLM unavailable or invalid JSON)."
            )
            if llm_error:
                rationale += f" cause={llm_error}"
            edits = [
                PromptEdit(
                    zone="instruction_appendix",
                    change_type="append",
                    old=current_prompt_appendix,
                    new=instruction_appendix,
                )
            ]
            if self.last_debug.get("status") == "llm_success":
                self.last_debug["status"] = "fallback_no_valid_edits"

        self.last_debug.setdefault("selected_targets", analysis.selected_targets)
        self.last_debug.setdefault("candidate_prompt_version", candidate_prompt_version)
        self.last_debug.setdefault("edit_count", len(edits))

        return PromptPatch(
            base_prompt_version=base_prompt_version,
            candidate_prompt_version=candidate_prompt_version,
            target_classes=analysis.selected_targets,
            edits=edits,
            max_edit_lines=max_edit_lines,
            rationale=rationale,
        )
