from __future__ import annotations

from cardio_graph_core.tuning.contracts import PromptPatch


def _normalize_lines(text: str) -> list[str]:
    return [line.rstrip() for line in text.splitlines() if line.strip()]


def apply_prompt_patch(current_text: str, patch: PromptPatch) -> str:
    lines = _normalize_lines(current_text)
    additions: list[str] = []
    for edit in patch.edits:
        additions.extend(_normalize_lines(edit.new))

    unique_additions = [line for line in additions if line not in lines]
    if len(unique_additions) > patch.max_edit_lines:
        unique_additions = unique_additions[: patch.max_edit_lines]

    merged = lines + unique_additions
    return "\n".join(merged).strip() + "\n"


def is_patch_safe(
    patch: PromptPatch, max_global_edit_lines: int = 40
) -> tuple[bool, str]:
    total_lines = 0
    for edit in patch.edits:
        total_lines += len(_normalize_lines(edit.new))
        if edit.zone != "instruction_appendix":
            return False, f"unsupported edit zone: {edit.zone}"
    if total_lines > max_global_edit_lines:
        return False, f"patch too large: {total_lines} lines"
    return True, "ok"
