// AUTOTUNING TEMPLATE (LLM3)
// NOTE: This template defines the intended structured contract for prompt optimization.
// It can be activated after BAML client regeneration.

class AutoTuningPromptPatch {
  edits AutoTuningPromptEdit[]
  rationale string
  max_edit_lines int
  instruction_appendix string?
}

class AutoTuningPromptEdit {
  zone string
  content string
}

function ProposeTable22PromptPatch(input: string) -> AutoTuningPromptPatch {
  client Qwen14b5
  prompt #"
    You are a prompt optimizer for medical extraction autotuning.
    Given top error classes and current prompt appendix, propose a minimal prompt patch.

    Return ONLY JSON matching the output schema.
    Constraints:
    - Return `edits` as a list of objects: {zone, content}.
    - Allowed zones: instruction_appendix, rule_structuring, condition_extraction, action_extraction, operator_logic.
    - Keep each edit concise and generally applicable across rows.
    - DO NOT mention row IDs, table IDs, candidate IDs, iteration IDs, or copied table-specific snippets.
    - Avoid phrases like "row_11", "table 22", "candidate_01", "iter_02", or "in this row".
    - max_edit_lines should be <= 30.
    - If no good edit is possible, return `edits` as an empty array.
    - `instruction_appendix` is optional legacy compatibility output.

    Input:
    {{input}}

    {{ ctx.output_format(prefix="Use the following OUTPUT FORMAT:") }}
  "#
}
