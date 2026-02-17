from __future__ import annotations

from cardio_graph_core.tuning.contracts import ErrorAnalysis, PromptEdit, PromptPatch
from cardio_graph_core.tuning.llm_bridge import LLMBridge

SYSTEM_PROMPT = """
You are LLM3 (prompt optimizer) for extraction autotuning.
Propose a minimal instruction appendix patch that targets the selected error classes.
Return strict JSON with keys:
- instruction_appendix (string)
- rationale (string)
- max_edit_lines (int)
Keep instruction_appendix concise and actionable.
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


class PromptOptimizer:
    def __init__(self, llm_bridge: LLMBridge):
        self.llm_bridge = llm_bridge

    def propose_patch(
        self,
        base_prompt_version: str,
        candidate_prompt_version: str,
        current_prompt_appendix: str,
        analysis: ErrorAnalysis,
    ) -> PromptPatch:
        prompt = (
            f"base_prompt_version={base_prompt_version}\n"
            f"candidate_prompt_version={candidate_prompt_version}\n"
            f"selected_targets={analysis.selected_targets}\n"
            f"top_classes={[entry.to_dict() for entry in analysis.top_classes]}\n"
            f"current_prompt_appendix={current_prompt_appendix!r}\n"
            "Return JSON only."
        )
        instruction_appendix = ""
        rationale = ""
        max_edit_lines = 30
        try:
            payload = self.llm_bridge.generate_json(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=prompt,
                temperature=0.0,
                max_tokens=1200,
            )
            instruction_appendix = str(payload.get("instruction_appendix", "")).strip()
            rationale = str(payload.get("rationale", "")).strip()
            max_edit_lines = int(payload.get("max_edit_lines", 30))
        except Exception:
            instruction_appendix = ""

        if not instruction_appendix:
            instruction_appendix = _fallback_instruction(analysis.selected_targets)
            rationale = (
                "Fallback optimizer instruction (LLM unavailable or invalid JSON)."
            )

        edit = PromptEdit(
            zone="instruction_appendix",
            change_type="append",
            old=current_prompt_appendix,
            new=instruction_appendix,
        )
        return PromptPatch(
            base_prompt_version=base_prompt_version,
            candidate_prompt_version=candidate_prompt_version,
            target_classes=analysis.selected_targets,
            edits=[edit],
            max_edit_lines=max_edit_lines,
            rationale=rationale,
        )
