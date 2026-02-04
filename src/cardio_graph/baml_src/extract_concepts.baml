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
  client Qwen8bG4_37
  prompt #"
    You are a medical guideline extraction expert. 
    Analyze the text and extract logical rules consisting of Conditions and Actions.
    
    Context:
    - [GUIDELINE: ...] tags indicate context.
    - Group related concepts (e.g., a specific condition and its resulting medication) using the same 'rule_id'.
    
     Requirements:
     1. **Grouping**: Assign the same 'rule_id' to all concepts that form a single logical statement (IF X AND Y -> THEN Z). Start at 1 and increment per distinct rule in this sentence.
     2. **Logic Details**: For 'ClinicalParameter' or conditions with thresholds (e.g. 'LVEF < 40%'), accurately fill 'operator', 'threshold', and 'unit' in logic_structured. Use operator "PRESENT" if a condition is stated as present/absent without a numeric threshold.
     3. **Direction**: Set logic_structured.direction based on the statement:
       - POSITIVE for recommendations/indications/should use.
       - NEGATIVE for contraindications/avoid/do not use.
       - UNKNOWN if no action is stated (pure background/outcome reporting).
     4. **Roles**:
       - Use 'Condition' or 'ClinicalParameter' for the IF part.
       - Use 'Medication' or 'Procedure' for the THEN part.
     5. **Recommendation strength/evidence**: If the text includes class/level (e.g., Class I, Level B), populate logic_structured.strength and logic_structured.level.
     6. **Standardization**: Map entities to their canonical clinical name.
     7. **Exclude sources**: Do not emit GuidelineSource/Recommendation nodes; only clinical entities and actions.

    Sentence: {{text}}

    {{ ctx.output_format(prefix="Use the following OUTPUT FORMAT:") }}
  "#
}