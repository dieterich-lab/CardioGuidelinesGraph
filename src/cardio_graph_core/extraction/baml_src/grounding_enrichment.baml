class ConceptSynonymsResult {
  synonyms string[] @description("Up to 10 concise biomedical synonym variants for the input concept")
}

class StandardizedCandidateResult {
  entity_standardized_candidate string @description("Single normalized SNOMED-style candidate term")
}

function GenerateConceptSynonyms(concept: string, role: string) -> ConceptSynonymsResult {
  client Qwen32b5_36
  prompt #"
    You are a biomedical terminology assistant.
    Generate concise synonym variants for a SNOMED-like concept term to improve lexical retrieval.

    Constraints:
    - Return ONLY JSON in the required output format.
    - Provide at most 10 synonyms.
    - Keep entries short noun phrases, not sentences.
    - Include common spelling/wording variants and clinically equivalent forms.
    - Exclude unrelated broader/narrower concepts.
    - Exclude dosage, stage, severity, or temporal qualifiers unless intrinsic to the concept.
    - Exclude duplicates and the exact original concept string.
    - Keep language in English medical terminology.

    Concept: {{concept}}
    Role: {{role}}

    {{ ctx.output_format(prefix="Use the following OUTPUT FORMAT:") }}
  "#
}

function GenerateStandardizedCandidate(concept: string, role: string) -> StandardizedCandidateResult {
  client Qwen30b5
  prompt #"
    You are a biomedical terminology normalization assistant.
    Produce exactly one standardized SNOMED-style candidate term for the input concept.

    Constraints:
    - Return ONLY JSON in the required output format.
    - Output one concise noun phrase in English medical terminology.
    - Keep clinically faithful to the input concept and role.
    - Expand abbreviations where possible (e.g., CCS, CAD, PCI, DAPT).
    - Remove contextual filler and sentence-like phrasing.
    - Avoid dosage, stage, severity, or temporal qualifiers unless intrinsic.
    - Do not return multiple options or lists.

    Concept: {{concept}}
    Role: {{role}}

    {{ ctx.output_format(prefix="Use the following OUTPUT FORMAT:") }}
  "#
}