// SINGLE SOURCE OF TRUTH:
// - Canonical schema contract lives in:
//   config/cardio_graph_core/guideline_graph_schema.yaml
// - This BAML file is the extraction SUBSET of that contract.
// - Grounding-only fields like snomed_id, preferred_term, synonyms are added after extraction.

// [BEGIN SCHEMA_BAML_TYPE_CONTRACT]
// Auto-generated from guideline_graph_schema.yaml via schema_contract_sync.py
// Do not edit manually.
class LogicStructured {
  // Recommendation details
  strength string? @description("Recommendation strength (e.g., Strong, Weak, Class I)")
  level string? @description("Level of evidence (e.g., A, B, C)")
  direction string @description("Recommendation direction (<, >, =, POSITIVE, NEGATIVE)")

  // Decision details (fuer Bedingungen/Checks)
  operator string? @description("Comparison/presence operator (e.g., <, >, =, PRESENT, ABSENT)")
  threshold string? @description("Numeric threshold value (e.g., 40, 120/80)")
  unit string? @description("Unit of measurement (e.g., %, mmHg, mg)")

  // Temporal/Conditional context
  context string? @description("Additional context (e.g., 'history of', 'acute', 'chronic')")
}

class ExtractedConcept {
  entity_original string
  entity_standardized_candidate string
  role string
  logic string
  logic_structured LogicStructured
}

class ExtractConceptsResult {
  concepts ExtractedConcept[]
}

// Draft v2: explicit input/output separation to remove ambiguity.
class RuleLogicV2 {
  operator string? @description("Operator for input conditions (e.g., <, >, =, PRESENT, ABSENT)")
  threshold string? @description("Numeric threshold value (e.g., 40, 120/80)")
  unit string? @description("Unit of measurement (e.g., %, mmHg, mg)")
  context string? @description("Additional context (e.g., 'history of', 'acute', 'chronic')")
  logic_type string? @description("AND, OR, or SINGLE within a group")
  logic_group string? @description("Group name for inputs that are evaluated together (e.g., and_1, or_1)")
}

class RuleConditionV2 {
  entity_original string
  entity_standardized_candidate string
  role string @description("ClinicalCondition, ClinicalParameter, Procedure")
  logic RuleLogicV2
}

class RuleRecommendationV2 {
  strength string? @description("Recommendation strength (e.g., Class I, Class IIa)")
  level string? @description("Level of evidence (e.g., A, B, C)")
  direction string @description("Recommendation direction (<, >, =, POSITIVE, NEGATIVE)")
}

class RuleActionV2 {
  entity_original string
  entity_standardized_candidate string
  role string @description("Medication or Procedure")
  context string? @description("Short action context span (e.g., indication, temporal clause, qualifier)")
  recommendation RuleRecommendationV2
}

class ExtractedRuleV2 {
  conditions RuleConditionV2[]
  actions RuleActionV2[]
}

class ExtractRulesResultV2 {
  rules ExtractedRuleV2[]
}
// [END SCHEMA_BAML_TYPE_CONTRACT]

function ExtractConcepts(text: string) -> ExtractConceptsResult {
  client Qwen14b5
  prompt #"
    You are a medical guideline extraction expert. 
    Analyze the text and extract logical rules consisting of Conditions and Actions.

    IMPORTANT WORKFLOW:
    - If the input contains a [DRAFT_RULES]...[/DRAFT_RULES] block, treat it as a first-pass draft.
    - In that case, perform a second-pass correction: keep correct draft items, fix wrong items, and add missing items from the sentence.
    - The sentence text is the final source of truth; do not copy draft errors.

    Output rules MUST be valid JSON and MUST match the OUTPUT FORMAT exactly.
    Do NOT include <think> blocks, explanations, or any text outside the JSON.
    If uncertain, return an empty concepts array rather than any extra text.
    
    Context:
    - [GUIDELINE: ...] tags indicate context.
    - [FOCUS: MAIN] means extract full rules (conditions/parameters + actions).
    - [FOCUS: POPULATION] means extract only population/eligibility conditions or parameters; do NOT output actions.
    - Group related concepts by keeping coherent IF-side and THEN-side extraction per sentence.
    
    Requirements:
    1. **Grouping**: Keep IF-side concepts and THEN-side concepts coherent per sentence.
     2. **Logic**: For thresholds, fill 'operator', 'threshold', and 'unit'.
       [BEGIN SCHEMA_OPERATOR_PROMPT]
       Use operator values from: <, >, =, PRESENT, ABSENT.
       [END SCHEMA_OPERATOR_PROMPT]
       - Populate `logic_structured.context` with concise local qualifiers when present (e.g., "despite medical therapy", "to improve survival", "history of", "in selected patients").
     3. **Direction**:
       [BEGIN SCHEMA_DIRECTION_USE_PROMPT]
       Use one of <, >, =, POSITIVE, NEGATIVE.
       [END SCHEMA_DIRECTION_USE_PROMPT]
     4. **Roles + action**: IF part uses 'ClinicalCondition' or 'ClinicalParameter'; THEN part uses 'Medication' or 'Procedure'.
       - If [FOCUS: MAIN], include at least one action when recommendation text exists. Never use role 'Recommendation'.
       - If [FOCUS: POPULATION], output ONLY population/eligibility conditions or parameters; no actions. Always return at least one population condition when such a cohort is stated.
       - Treat comparative qualification clauses (e.g., "when A and B have the same recommendation level") as context unless they define an independent, clinically actionable eligibility predicate.
       - Do NOT create extra Procedure conditions from such qualification clauses; keep the primary cohort/clinical condition as the explicit condition.
     5. **Strength/level**: Populate logic_structured.strength and logic_structured.level when present.
       - For class strength, always output "Class I", "Class IIa", "Class IIb", or "Class III" (add the "Class" prefix if only a Roman numeral is shown).
     6. **SNOMED-style terms**: Output short, specific noun phrases (singular). Avoid full sentences, lists, and parenthetical abbreviations like "(PCI)". If text uses abbreviations, output the expanded clinical term only. Do not emit GuidelineSource/Recommendation nodes.
       - Do not combine multiple distinct conditions into a single entity. Emit one concept per condition or parameter.
     7. **Population conditions**: If the sentence specifies a patient population or cohort (e.g., chronic disease state, eligibility criteria, or subgroup), include it as a Condition in the IF part. This should be captured even if it is not a numeric parameter.
       - Example forms to capture (generalized): "In [population] patients...", "Among patients with [condition]...", "Eligible [subgroup] patients...".

    Sentence: {{text}}

    {{ ctx.output_format(prefix="Use the following OUTPUT FORMAT:") }}
  "#
}

function ExtractRulesV2(text: string) -> ExtractRulesResultV2 {
  client Qwen14b5
  prompt #"
    You are a medical guideline extraction expert.
    Extract rules with an explicit left/right split: conditions (eligibility/inputs) and actions (recommended outputs).

    Output MUST be valid JSON and MUST match the OUTPUT FORMAT exactly.
    Do NOT include <think> blocks, explanations, or any text outside the JSON.
    If uncertain, return an empty rules array rather than any extra text.

    Core requirement: NEVER mix conditions and actions in the same list.
    - Conditions: inputs/eligibility (conditions, parameters, or planned procedures) that define WHEN a rule applies.
    - Actions: recommendations or interventions that are advised when conditions are met.

    Context:
    - [GUIDELINE: ...] tags indicate source context.
    - [FOCUS: MAIN] means extract full rules (conditions + actions).
    - [FOCUS: POPULATION] means extract ONLY population/eligibility conditions; actions must be empty.

    Rules:
     1. Grouping: Keep each rule internally coherent with matching conditions and actions.
    2. Conditions:
       - Use role ClinicalCondition or ClinicalParameter for clinical states/measurements.
       - Use role Procedure if the procedure is an eligibility condition (e.g., planned or scheduled procedure).
      [BEGIN SCHEMA_OPERATOR_PROMPT_RULES]
      Use operator values from: <, >, =, PRESENT, ABSENT.
      [END SCHEMA_OPERATOR_PROMPT_RULES]
       - Do not materialize recommendation-comparison qualifiers (e.g., "same recommendation level") as standalone conditions unless an explicit measurable criterion is stated.
       - If there is one main cohort condition and additional qualifier text, keep one main condition and place qualifiers in context rather than adding extra condition nodes.
    3. Actions:
       - Use role Medication or Procedure.
       - Populate action `context` with a short indication/qualifier phrase when present in the sentence.
       - Populate recommendation.strength/level/direction when present.
      [BEGIN SCHEMA_DIRECTION_PROMPT_RULES]
      Direction must be one of <, >, =, POSITIVE, NEGATIVE.
      [END SCHEMA_DIRECTION_PROMPT_RULES]
       - For class strength, always output "Class I", "Class IIa", "Class IIb", or "Class III".
     4. Logic groups:
       - Use logic_type and logic_group for conditions only.
       - logic_type must be AND, OR, or SINGLE.
       - Do not set logic fields on actions.
    5. SNOMED-style terms:
       - Output short, specific noun phrases (singular). Avoid full sentences and lists.
       - Do not combine multiple distinct conditions into a single entity.
     6. Focus-specific constraints:
       - If [FOCUS: MAIN], each rule must include at least one action.
       - If [FOCUS: POPULATION], actions MUST be an empty array and output only eligibility/population conditions.

    Sentence: {{text}}

    {{ ctx.output_format(prefix="Use the following OUTPUT FORMAT:") }}
  "#
}