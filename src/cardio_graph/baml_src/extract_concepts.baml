class LogicStructured {
  strength string @description("Recommendation strength (e.g., Strong, Weak, Unknown)")
  class string @description("Guideline class of recommendation (e.g., I, IIa, IIb, III, Unknown)")
  level string @description("Level of evidence (e.g., A, B, C, Unknown)")
  direction string @description("POSITIVE, NEGATIVE, CONTRAINDICATED, or UNKNOWN")
}

class ExtractedConcept {
  entity_original string @description("The exact mention as it appears in the text")
  entity_standardized_candidate string @description("A normalized, canonical candidate string for SNOMED lookup")
  role string @description("Role in the guideline statement (e.g., Recommendation, Condition, Parameter, Procedure, Medication)")
  logic string @description("Logical context for the entity (e.g., condition, threshold, negation, recommendation strength)")
  logic_structured LogicStructured @description("Structured logic for recommendation strength and direction")
}

class ExtractConceptsResult {
  concepts ExtractedConcept[] @description("List of extracted concepts with standardized candidates and logic")
}

function ExtractConcepts(text: string) -> ExtractConceptsResult {
  client Qwen8bG4_37
  prompt #"
    You are a medical guideline extraction assistant. Given a single sentence, extract key medical concepts.
    Requirements:
    - Extract entities and normalize them into a standardized SNOMED candidate string.
    - Provide a role for each entity (Recommendation, Condition, Medication, Procedure, ClinicalParameter, GuidelineSource, DecisionNode, RecommendationNode, or Other).
    - Provide a short logic description that captures qualifiers, thresholds, negations, or recommendation strength.
    - Always provide logic_structured. If unknown, set fields to "Unknown" and direction to "UNKNOWN".
    - Return an empty list if no medical concepts are present.

    Sentence: {{text}}

    {{ ctx.output_format(prefix="Use the following OUTPUT FORMAT:") }}
  "#
}
