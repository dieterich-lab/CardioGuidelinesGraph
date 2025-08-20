class Concept {
  term string @description("The main term or label of the SNOMED concept")
  description string? @description("Optional: a longer description or definition of the concept")
}

class CategorizationResult {
  categories string[] @description("List of ontology categories assigned to the concept")
  reasoning string @description("Short explanation for the categorization")
}

function CategorizeConcept(concept: Concept, ontology_categories: string[]) -> CategorizationResult {
  client Qwen32b5_35
  prompt #"
    You are a medical ontology expert. Given the following SNOMED CT concept, assign it to one or more categories from the provided ontology category list.
    - Use your medical knowledge and the concept's term and description.
    - Only use categories from the provided list.
    - If the concept fits multiple categories, list all relevant ones.
    - If none fit, return an empty list.
    - Provide a brief reasoning for your choices.

    Concept term: {{concept.term}}
    Concept description: {{concept.description}}
    Ontology categories: {{ontology_categories | join(', ')}}

    {{ ctx.output_format(prefix="Use the following OUTPUT FORMAT:") }}
  "#
}
