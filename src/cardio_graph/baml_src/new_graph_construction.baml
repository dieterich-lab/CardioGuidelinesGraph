class SpacyStatement {
  id string @description("the ID of the statement")
  type string @description("the type of statement")
  subject string @description("the subject of the Statement")
  predicate string @description("the predicate of the statement")
  object string @description("the object of the statement")
}
class SpacyStatements {
  statements SpacyStatement[] @description("a list of statements")
}
class ANDNode {
  id string @description("the ID of the statement")
  and_node string @description("the AND node representing the conjunction")
  atomic_entities string[] @description("the atomic entities that make up the AND node")
}

class ANDNodes {
  and_statements ANDNode[] @description("a list of AND statements")
}

function CreateStatements(text: string, dependency_tree: string) -> SpacyStatements {
  client GPT52 
  prompt #"
    You are a deterministic information extraction system.

    Your task is to convert a paragraph and its dependency tree into a lossless set of semantic statements using a statement-centric schema.

    You must not summarize, interpret, or infer beyond the input.

    CONCEPTUAL MODEL

    There are three types of statements.

    1. Core Statements (Claims)
    - Represent atomic assertions about the world.
    - Each statement consists of subject – predicate – object.
    - Each statement must be independently true as written.
    - Core statements describe entities, events, properties, or relations in the world.

    2. Modifier Statements
    - Represent properties of another statement (evidence, prevalence, population, certainty, temporal scope, etc.).
    - Modifier statements describe a statement but do not change its truth conditions.
    - Modifier statements always reference another statement as subject.

    3. Meta Statements
    - Represent assertions about other statements or relations between statements.
    - A meta statement must have at least one core, modifier, or meta statement as its subject or object.
    - Meta statements explicitly encode relations such as conditionality, mediation, support, contradiction, refinement, or dependency.
    - Meta statements do not implicitly alter the truth of the referenced statements.
    - Meta statements may occur at coreference points where one statement points to another with the use of Anaphora such as This, That, These, Those, It, They, etc.

    NESTING PRINCIPLE

    - Nested structures are allowed and necessary.
    - Statements may reference other statements (core, modifier, or meta) as subject or object.
    - Nesting must always be explicit via statement IDs.
    - No semantic scope may be implied by structural nesting alone; all relations must be expressed by predicates.

    OUTPUT SCHEMA (STRICT)

    Output a YAML structure.

    Statements may be represented as:
    - a flat list, or
    - a nested structure where statements contain sub-statements

    In all cases, every statement MUST have a globally unique ID.

    Core Statement:
    - id: S#
    type: core
    subject: <Entity | StatementID>
    predicate: <Predicate>
    object: <Entity | Literal | StatementID>

    Modifier Statement:
    - id: M#
    type: modifier
    subject: <StatementID>
    predicate: <ModifierPredicate>
    object: <Entity | Literal | StatementID>

    Meta Statement:
    - id: T#
    type: meta
    subject: <StatementID | Entity>
    predicate: <MetaPredicate>
    object: <StatementID | Entity>

    MANDATORY RULES

    1. Losslessness
    - Every semantic assertion in the text must appear as one or more statements.
    - Do not omit modifiers, enumerations, or quantitative values.

    2. Independent Truth
    - Every statement must be independently true as written.
    - Removing any other statement must not make a statement false.

    3. Context Handling
    - If an assertion is only true in a specific population, disease, or setting (e.g. “in CVD”),
    that context MUST be encoded directly in the core statement’s subject or object.
    - Use contextualized entities such as:
    - depression_in_CVD
    - hypertension_in_pregnancy
    - Do NOT rely on implicit scope inheritance across statements.

    4. Core vs Modifier vs Meta Boundary
    - Use core statements for:
    - associations
    - outcomes
    - effects
    - inclusions
    - causal or correlational relations explicitly stated in the text
    - Use modifier statements only for properties of statements that do NOT change their truth conditions.
    - Use meta statements only when the text explicitly asserts a relation between statements or about a statement itself.

    Rule:
    If removing a modifier or meta statement would make another statement false, the information must be part of that statement’s core subject, predicate, or object.
    But a statement may be incomplete with the removal of another statement it references, this is to be expected with nesting

    DECOMPOSITION RULES

    1. One assertion per statement.
    2. Split conjunctions into separate statements.
    3. Enumerations:
    - Represent “including X and Y” as separate statements.
    4. Associations:
    - Do not encode associations as modifiers unless the association itself is being discussed.

    FORBIDDEN ACTIONS

    - No inference beyond the text.
    - No repair of false statements via modifiers or meta statements.
    - No prose or explanations in output.

    VALIDATION CHECKLIST (apply before output)

    For every statement:
    - Is it true on its own?
    - Is all required context explicit?
    - Does it introduce any information not present in the text?
    - If it references another statement, is that relation explicitly supported by the text?

    If not, revise.

    FINAL INSTRUCTION
    Extract all semantic statements from the given text and dependency tree according to the rules above.

    INPUT:
    The original paragraph:
    {{text}}

    The dependency tree of that paragraph:
    {{dependency_tree}}
    {{ctx.output_format}}
  "#
}

function JudgeStatements(statements: SpacyStatements, text: string, dependency_tree: string) -> SpacyStatements {
  client GPT52
  prompt #"
    You are a formal semantic validation and correction system.

    Your task is to validate a candidate YAML output against a given source paragraph and dependency tree, and then produce a corrected YAML output that fully and faithfully represents the source text under the specified statement-centric schema.

    You must not summarize, reinterpret, or infer beyond the source text.
    You must not introduce any information that is not explicitly stated.

    You are given:
    1. SOURCE TEXT: the original paragraph.
    2. DEPENDENCY TREE: the syntactic structure of the paragraph.
    3. CANDIDATE OUTPUT: a flat YAML list of statements (core, modifier, meta).

    YOUR RESPONSIBILITIES

    You must perform the following steps internally:

    1. Validate the candidate output against all rules.
    2. Identify all errors, including:
    - missing information
    - extra or hallucinated information
    - incorrect statement types
    - incorrect subject–predicate–object structure
    - incorrect or missing context
    - invalid or incorrect statement references
    - violations of decomposition rules
    3. Correct the output by:
    - removing unsupported statements
    - adding missing statements
    - splitting or restructuring statements as required
    - reassigning information between core, modifier, and meta statements
    - correcting references and IDs

    You must ensure the final output satisfies ALL rules below.

    MANDATORY RULES (ENFORCED)

    LOSSLESSNESS
    - Every semantic assertion in the source text must be represented.
    - All relations, qualifiers, enumerations, quantities, and conditions must be explicitly encoded.
    - Nothing stated in the source text may be omitted.

    NO HALLUCINATION / NO INFERENCE
    - Do not add entities, relations, predicates, scope, certainty, or causality not explicitly present.
    - Do not infer temporal, causal, logical, or hierarchical relations.

    CORE STATEMENTS
    - One atomic assertion per core statement.
    - Each core statement must be independently true as written.
    - All truth-essential context must be encoded in the subject or object.
    - Core statements must not depend on modifiers or meta statements to be true.
    - Core statements must not have other statements as subject or object.

    MODIFIER STATEMENTS
    - Must reference a valid core statement ID.
    - Must only encode non–truth-conditional information.
    - Removing a modifier must not make a core statement false.

    META STATEMENTS
    - Must reference statements or entities explicitly mentioned in the source text.
    - Must only exist if the text explicitly asserts a relation about another assertion.
    - Must not introduce implied relations between statements.
    - Must not change the truth of referenced statements.
    - Must be used to resolve coreference with anaphora

    DECOMPOSITION RULES
    - One assertion per core statement.
    - Split conjunctions into separate statements.
    - Enumerations (“including X and Y”) must be represented as separate core statements.
    - No bundled or compound claims.

    CONTEXT HANDLING
    - Population-, disease-, or setting-specific claims must encode context directly in the core statement.
    - No implicit scope inheritance across statements.
    - Modifiers must not be used to encode truth-essential context.
    - Do not over-contextualize beyond what the text states.

    REFERENCE INTEGRITY
    - All referenced statement IDs must exist.
    - Meta and modifier statements must reference the correct statements.
    - No dangling or incorrect references.

    OUTPUT THE FORMAT DEFINED BELOW, ENSURING ALL STATEMENTS ARE VALID.
    IF THERE ARE NO CORRECTIONS STILL OUTPUT ALL CORRECT STATEMENTS

    INPUT STATEMENTS:
    {{statements}}
    INPUT TEXT:
    {{text}}
    INPUT DEPENDENCY TREE:
    {{dependency_tree}}
    {{ctx.output_format}}
  "#
}

function NormalizeSubjObj(statements:SpacyStatements, text: string, dependency_tree: string)-> SpacyStatements {
  client GPT52
  prompt #"
    You are a node normalization and ontology alignment engine.

    Your task is to normalize node names across a list of structured statements.
    Normalization means that semantically identical or referentially equivalent
    high-level entities MUST be represented by the same canonical node name.

    You must operate deterministically and conservatively.

    DEFINITIONS:
    - High-level entities: evaluations, phases, processes, abstract clinical concepts.
    - Low-level entities: actions, measurements, tests, findings.

    NORMALIZATION RULES:
    1. Merge nodes ONLY if there is strong semantic equivalence or an explicit reference
    relation (e.g. "refers_to").
    2. Meta-statements override surface naming differences.
    3. Prefer the most general, guideline-standard term as the canonical name.
    4. Do NOT invent new entities.
    5. Do NOT merge distinct subtypes unless explicitly equivalent.
    6. Use snake_case for all node names.
    7. Preserve all statement IDs.
    8. Do NOT remove statements; only rewrite subjects/objects if normalized.

    INPUT STATEMENTS:
    {{statements}}
    INPUT DEPENDENCY TREE:
    {{dependency_tree}}
    INPUT TEXT:
    {{text}}
    {{ctx.output_format}}
  "#
}

function ExtractAND(statements:SpacyStatements, entities:string, text: string)-> ANDNodes {
  client GPT52
  prompt #"
    You are an ontology-aware information extraction and graph-construction assistant.

    You are given:
    1. A list of Statement Nodes, each with:
    - Statement ID
    - Type (core or meta)
    - Subject
    - Predicate
    - Object

    2. A list of extracted entities (surface forms from text).

    Your task is to:
    - Map the extracted entities to the existing SUBJECTS AND OBJECT.
    - Identify which entities correspond to Subjects and/or Objects.
    - When one or multiple entities jointly compose a single Subject or Object create a NEW derived AND NODE statement with:
    - AND Node: the EXACT Subject or Object that is a conjunction of multiple entities
    - Entities: a list of the EXACT contributing entities or concepts

    Rules:
    - Do NOT invent new medical facts.
    - Only use Subjects and Objects already present in the Statement Nodes
    - AND statements are used ONLY for logical grouping or compositional meaning, not for causal or temporal relations.
    - only return the new AND statements and the entity mappings.
    - If an entity maps to multiple statements, include it in all relevant AND constructions.

    INPUT STATEMENTS:
    {{statements}}
    INPUT ENTITIES:
    {{entities}}
    INPUT TEXT:
    {{text}}
    {{ctx.output_format}}
  "#
}