// Update der Logic Struktur: Wir brauchen Operatoren und Werte!
class LogicStructured {
  // Recommendation details
  strength string? @description("Recommendation strength (e.g., Strong, Weak, Class I)")
  level string? @description("Level of evidence (e.g., A, B, C)")
  direction string @description("POSITIVE, NEGATIVE (Contraindication), or UNKNOWN")
  
  // Decision details (für Bedingungen/Checks)
  operator string? @description("Mathematical operator if present (e.g., <, >, <=, =, PRESENT)")
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

    Output rules MUST be valid JSON and MUST match the OUTPUT FORMAT exactly.
    Do NOT include <think> blocks, explanations, or any text outside the JSON.
    If uncertain, return an empty concepts array rather than any extra text.
    
    Context:
    - [GUIDELINE: ...] tags indicate context.
    - Group related concepts (e.g., a specific condition and its resulting medication) using the same 'rule_id'.
    
    Requirements:
    1. **Grouping**: Assign the same 'rule_id' to all concepts that form a single logical statement (IF X AND Y -> THEN Z). Start at 1 and increment per distinct rule in this sentence.
    2. **Logic**: For thresholds, fill 'operator', 'threshold', and 'unit'. Use operator "PRESENT" when a condition is stated without a numeric threshold.
    3. **Direction**: POSITIVE for recommendations/indications, NEGATIVE for contraindications/avoid. Use UNKNOWN only if there is no action.
    4. **Roles + action**: IF part uses 'Condition' or 'ClinicalParameter'; THEN part uses 'Medication' or 'Procedure'. Include at least one action per rule_id. Never use role 'Recommendation'.
    5. **Strength/level**: Populate logic_structured.strength and logic_structured.level when present.
    6. **SNOMED-style terms**: Output short, specific noun phrases (singular). Avoid full sentences, lists, and parenthetical abbreviations like "(PCI)". If text uses abbreviations, output the expanded clinical term only. Do not emit GuidelineSource/Recommendation nodes.

    Sentence: {{text}}

    {{ ctx.output_format(prefix="Use the following OUTPUT FORMAT:") }}
  "#
}