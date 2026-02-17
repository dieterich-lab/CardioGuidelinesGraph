// SINGLE SOURCE OF TRUTH:
// - Canonical schema contract lives in:
//   config/cardio_graph_core/guideline_graph_schema.yaml (extraction_contract section)
// - This BAML file is the extraction SUBSET of that contract.
// - Grounding-only fields like snomed_id, preferred_term, synonyms are added after extraction.

// Update der Logic Struktur: Wir brauchen Operatoren und Werte!
class LogicStructured {
  // Recommendation details
  strength string? @description("Recommendation strength (e.g., Strong, Weak, Class I)")
  level string? @description("Level of evidence (e.g., A, B, C)")
  direction string @description("POSITIVE, NEGATIVE (Contraindication), or UNKNOWN")
  
  // Decision details (für Bedingungen/Checks)
  operator string? @description("Mathematical operator if present (e.g., <, >, <=, =, PRESENT, ABSENT, PLANNED)")
  threshold string? @description("Numeric threshold value (e.g., 40, 120/80)")
  unit string? @description("Unit of measurement (e.g., %, mmHg, mg)")
  
  // Temporal/Conditional context
  condition_context string? @description("Additional context (e.g., 'history of', 'acute', 'chronic')")
}

class ExtractedConcept {
  // Wir fügen eine ID hinzu, um Konzepte zu gruppieren
  rule_id int @description("Integer ID to group concepts that belong to the same logical rule (IF condition THEN action). Start at 1 per sentence and increment for each distinct rule.")
  
  entity_original string
  entity_standardized_candidate string
  role string 
  logic string
  logic_structured LogicStructured
}

class ExtractConceptsResult {
  concepts ExtractedConcept[] 
}

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
    - Group related concepts (e.g., a specific condition and its resulting medication) using the same 'rule_id'.
    
    Requirements:
    1. **Grouping**: Assign the same 'rule_id' to all concepts that form a single logical statement (IF X AND Y -> THEN Z). Start at 1 and increment per distinct rule in this sentence.
    2. **Logic**: For thresholds, fill 'operator', 'threshold', and 'unit'. Use operator "PRESENT" when a condition is stated without a numeric threshold. Use "PLANNED" for procedures that are scheduled but not yet executed (e.g., "scheduled for PCI").
    3. **Direction**: POSITIVE for recommendations/indications, NEGATIVE for contraindications/avoid. Use UNKNOWN only if there is no action.
     4. **Roles + action**: IF part uses 'Condition' or 'ClinicalParameter'; THEN part uses 'Medication' or 'Procedure'.
       - If [FOCUS: MAIN], include at least one action per rule_id. Never use role 'Recommendation'.
       - If [FOCUS: POPULATION], output ONLY population/eligibility conditions or parameters; no actions. Always return at least one population condition when such a cohort is stated.
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

// Draft v2: explicit input/output separation to remove ambiguity.
class RuleLogicV2 {
  operator string? @description("Operator for input conditions (e.g., <, >, <=, =, PRESENT, ABSENT, PLANNED)")
  threshold string? @description("Numeric threshold value (e.g., 40, 120/80)")
  unit string? @description("Unit of measurement (e.g., %, mmHg, mg)")
  condition_context string? @description("Additional context (e.g., 'history of', 'acute', 'chronic')")
  logic_type string? @description("AND or OR within a group")
  logic_group string? @description("Group name for inputs that are evaluated together (e.g., and_1, or_1)")
}

class RuleConditionV2 {
  entity_original string
  entity_standardized_candidate string
  role string @description("Condition, ClinicalParameter, Procedure")
  logic RuleLogicV2
}

class RuleRecommendationV2 {
  strength string? @description("Recommendation strength (e.g., Class I, Class IIa)")
  level string? @description("Level of evidence (e.g., A, B, C)")
  direction string @description("POSITIVE, NEGATIVE (Contraindication), or UNKNOWN")
}

class RuleActionV2 {
  entity_original string
  entity_standardized_candidate string
  role string @description("Medication or Procedure")
  recommendation RuleRecommendationV2
}

class ExtractedRuleV2 {
  rule_id int @description("Integer ID to group inputs/outputs that belong to the same logical rule.")
  conditions RuleConditionV2[]
  actions RuleActionV2[]
}

class ExtractRulesResultV2 {
  rules ExtractedRuleV2[]
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
    1. Grouping: Assign the same rule_id to all conditions/actions that form a single logical statement (IF X AND Y -> THEN Z). Start at 1 and increment per distinct rule in this sentence.
    2. Conditions:
       - Use role Condition or ClinicalParameter for clinical states/measurements.
       - Use role Procedure if the procedure is an eligibility condition (e.g., planned or scheduled procedure).
       - Use operator PRESENT for stated conditions without numeric thresholds.
       - Use operator PLANNED when the procedure is scheduled/planned but not executed (e.g., "scheduled for PCI").
    3. Actions:
       - Use role Medication or Procedure.
       - Populate recommendation.strength/level/direction when present.
       - Direction must be POSITIVE, NEGATIVE, or UNKNOWN.
       - For class strength, always output "Class I", "Class IIa", "Class IIb", or "Class III".
     4. Logic groups:
       - Use logic_type and logic_group for conditions only.
       - Do not set logic fields on actions.
    5. SNOMED-style terms:
       - Output short, specific noun phrases (singular). Avoid full sentences and lists.
       - Do not combine multiple distinct conditions into a single entity.
     6. Focus-specific constraints:
       - If [FOCUS: MAIN], each rule should include at least one action unless the sentence contains no recommendation.
       - If [FOCUS: POPULATION], actions MUST be an empty array and output only eligibility/population conditions.

    Sentence: {{text}}

    {{ ctx.output_format(prefix="Use the following OUTPUT FORMAT:") }}
  "#
}