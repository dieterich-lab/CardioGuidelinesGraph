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
  rule_id int @description("Integer ID to group concepts that belong to the same logical rule (IF condition THEN action). Reset for new sentences.")
  
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
  client Qwen8bG4_37
  prompt #"
    You are a medical guideline extraction expert. 
    Analyze the text and extract logical rules consisting of Conditions and Actions.
    
    Context:
    - [GUIDELINE: ...] tags indicate context.
    - Group related concepts (e.g., a specific condition and its resulting medication) using the same 'rule_id'.
    
    Requirements:
    1. **Grouping**: Assign the same 'rule_id' to all concepts that form a single logical statement (IF X AND Y -> THEN Z).
    2. **Logic Details**: For 'ClinicalParameter' or conditions with thresholds (e.g. 'LVEF < 40%'), accurately fill 'operator', 'threshold', and 'unit' in logic_structured.
    3. **Roles**: 
       - Use 'Condition' or 'ClinicalParameter' for the IF part.
       - Use 'Medication' or 'Procedure' for the THEN part.
    4. **Standardization**: Map entities to their canonical clinical name.

    Sentence: {{text}}

    {{ ctx.output_format(prefix="Use the following OUTPUT FORMAT:") }}
  "#
}