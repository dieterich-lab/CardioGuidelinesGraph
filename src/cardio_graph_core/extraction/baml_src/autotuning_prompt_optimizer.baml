// AUTOTUNING TEMPLATE (LLM3)
// NOTE: This template defines the intended structured contract for prompt optimization.
// It can be activated after BAML client regeneration.

class AutoTuningPromptPatch {
  instruction_appendix string
  rationale string
  max_edit_lines int
}

function ProposeTable22PromptPatch(input: string) -> AutoTuningPromptPatch {
  client Qwen14b5
  prompt #"
    You are a prompt optimizer for medical extraction autotuning.
    Given top error classes and current prompt appendix, propose a minimal instruction appendix patch.

    Return ONLY JSON matching the output schema.
    Constraints:
    - Keep instruction_appendix concise.
    - max_edit_lines should be <= 30.

    Input:
    {{input}}

    {{ ctx.output_format(prefix="Use the following OUTPUT FORMAT:") }}
  "#
}
