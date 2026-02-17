// AUTOTUNING TEMPLATE (LLM2)
// NOTE: This template defines the intended structured contract for error analysis.
// It can be activated after BAML client regeneration.

class AutoTuningErrorClass {
  error_class string
  count int
  confidence float
  root_cause_hypothesis string
}

class AutoTuningErrorAnalysis {
  top_classes AutoTuningErrorClass[]
  selected_targets string[]
}

function AnalyzeTable22Errors(input: string) -> AutoTuningErrorAnalysis {
  client Qwen14b5
  prompt #"
    You are an error analyst for medical extraction autotuning.
    Analyze the deterministic error summary and identify root-cause classes.

    Return ONLY JSON matching the output schema.
    Constraints:
    - selected_targets: max 2 classes
    - confidence in [0.0, 1.0]

    Input:
    {{input}}

    {{ ctx.output_format(prefix="Use the following OUTPUT FORMAT:") }}
  "#
}
