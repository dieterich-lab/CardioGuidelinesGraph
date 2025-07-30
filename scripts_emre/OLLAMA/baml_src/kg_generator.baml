

class Sentences {
  sentence string[] @description("a list of simple sentences")
}

class SentenceID {
  id string @description("the ID of the sentence")
  sentence string @description("the simple sentence")
}

class SentencesID {
  sentences SentenceID[] @description("a list of sentences with IDs")
}

class SentenceIDexplanation {
  id string @description("the ID of the sentence")
  sentence string @description("the simple sentence")
  meaning string @description("a text in natural language that explains the meaning of this sentence")
}

class SentencesIDexplanation {
  sentences SentenceIDexplanation[] @description("a list of sentences with IDs and explanations")
}

class SplittedText {
  IF string @description("Conditional statement")
  THEN string @description("Result of the conditional statement")
}

class Operation {
  operation string @description("type of logical operation, either AND, COMPARED TO or INFERS")
  input string @description("all entites that are part of the operation")
  output string @description("all entities that are a result or implication of the operation")
  // confidence ("high" | "low")? @description("if this relation was extracted with high confidence or not")
}

class TripleID {
  id string @description("the ID of the triple")
  head_node_id string @description("the ID of the head node")
  head_node_value string @description("the value of the head node")
  relation string @description("the relation of the head node to the tail node")
  tail_node_id string @description("the ID of the tail node")
  tail_node_value string @description("the value of the tail node")
}

class TriplesID {
  triples TripleID[] @description("a list of triples")
}
class StatementSepID {
  statement_node_ID string @description("the ID of the rdf:statement")
  subject string @description("the tail node value of the triple where rdf:subject is the edge")
  subjectID string @description("the ID of the subject node, if the tail node is an rdf:statement then it also contains the summary")
  predicate string @description("the tail node value of the triple where rdf:predicate is the edge")
  predicateID string @description("the ID of the predicate node")
  object string @description("the tail node value of the triple where rdf:object is the edge, if the head node is an rdf:statement then it also contains the summary")
  objectID string @description("the ID of the object node, if the tail node is an rdf:statement then it also contains the summary")
}

class StatementsSepID {
  statement StatementSepID[] @description("a list of statements")
}
 
class StatementSepIDSummarized {
  statement_node_ID string @description("the ID of the rdf:statement")
  subject string @description("the tail node value of the triple where rdf:subject is the edge")
  subjectID string @description("the ID of the subject node, if the tail node is an rdf:statement then it also contains the summary")
  predicate string @description("the tail node value of the triple where rdf:predicate is the edge")
  predicateID string @description("the ID of the predicate node")
  object string @description("the tail node value of the triple where rdf:object is the edge, if the head node is an rdf:statement then it also contains the summary")
  objectID string @description("the ID of the object node, if the tail node is an rdf:statement then it also contains the summary")
  summary string @description("a text in natural language that summarizes the information and meaning of the rdf:statement")
}

// class StatementSummarized {
//   statement StatementSummarized[] @description("a list of statements")
// }

class Summary {
  summary string @description("a text in natural language that summarizes the information and meaning of the rdf:statement")
}

function SummarizeStatement(input: StatementSepID, subject_summary: Summary, object_summary: Summary) -> Summary {
  client Qwen32b5 
  prompt #"
    Summarize the following statement where subject, predicate and object form a triple.
    subject is related to the object with the relation type being the predicate. the summary should reflect this relationship and the information included in the subject and object.
    {{input}}
    Consider the following summary for the subject :
    {{subject_summary}}
    Consider the following summary for the object :
    {{object_summary}}
    {{ ctx.output_format(prefix="Use the following OUTPUT FORMAT:") }}
  "#
}

function PrimaryTripleExtraction(input: string) -> Triple {
  client Qwen14b4 
  prompt #"
    "Extract from the following text:
    {{input}}
    {{ ctx.output_format(prefix="Use the following OUTPUT FORMAT:") }}
  "#
}
function LogicIdentifier(input: string) -> Operation {
  client Qwen14b4
  prompt #"
    "Extract from the following text:
    {{input}}
    {{ ctx.output_format}}
  "#
}

function SimpleText(input: string) -> SplittedText {
  client Qwen14b4
  prompt #"
    {{input}}
    {{ ctx.output_format}}
  "#
}

function Hypergrapher(input: SentencesIDexplanation) -> TriplesID {
  client Qwen32b5
  prompt #"
    Extract all triples from the following sentences.
    Nested Statements may be represented by using Nodes that represent entire Statements, indexed by the sentence ID
    {{input}}
    {{ ctx.output_format(prefix="Use the following OUTPUT FORMAT:") }}
  "#
}

function EasyFormatting(input: string) -> SentencesID {
  client Qwen32b5
  prompt #"
    "Simplify the following text into a list of simple sentences.
    Each sentence should be a simple statement that can be easily understood.
    All information must be preserved with zero semantic loss
    {{input}}
    {{ ctx.output_format(prefix="Use the following OUTPUT FORMAT:") }}
  "#
}

function FormattedFacts(input: string) -> SentencesID {
  client Qwen32b5
  prompt #"
    "Break down this text into simple and short sentences. 
    Each of these sentences should contain a small amout of the information represented here.
    All the sentences together should represent the same information as the original text without losing any meaning or information

    Example: "a study has shown that Patients with Fever and a recent travel History to Ghana should visit a doctor"
    should be transformed into:
    1. Patients with Fever and a recent travel History to Ghana
    2. These Patients should visit a doctor
    3. This is shown by a study
    {{input}}
    {{ ctx.output_format}}
  "#
}

function PrototypeNester(sentences: SentencesID, original: string) -> SentencesIDexplanation {
  client Qwen32b5
  prompt #"
    "If the follwing sentences contain nested statements, identify the nested statement and represent them in a sequence of sentences that each may reference other sentences in the same list"
    The reference is done by using the sentence ID of the referenced sentence in parentheses.
    everytime there is a sentence with a reference please explain the full sentence in the explanation field.

    Example:
    1. Patients with Fever and a recent travel History to Ghana 
    2. These Patients should visit a doctor
    3. This is recommended by the guidelines
    3. These Patients are at risk of Malaria

    Nested Statements identified and transformed:
    1. Patients with Fever and a recent travel History to Ghana 
    2. (Sentence ID:1) should visit a doctor (meaning: Patients with Fever and a recent travel History to Ghana should visit a doctor)
    3. (Sentence ID:2) is recommended by the guidelines (meaning: The guidelines recommend that patients with Fever and a recent travel History to Ghana should visit a doctor)
    3. (Sentence ID:1) are at risk of Malaria (meaning: Patients with Fever and a recent travel History to Ghana are at risk of Malaria)

    Consider if each sentence represents a full truth, as a false example: "a study has shown that Patients with Fever and a recent travel History to Ghana should visit a doctor"
    1. A study has found a result
    2. (Sentence ID:1) involves Patients with Fever and a recent travel History to Ghana (meaning: The study results involve patients with Fever and a recent travel History to Ghana)
    3. (Sentence ID:2) should visit a doctor (meaning: Patients with Fever and a recent travel History to Ghana should visit a doctor)
    This is wrong because the second sentence does not represent a full truth on its own it is too incomplete since the study encompasses not only the patients but also the fact that they should visit a doctor
    Corrected:
    1. Patients with Fever and a recent travel History to Ghana
    2. (Sentence ID:1) should visit a doctor (meaning: Patients with Fever and a recent travel History to Ghana should visit a doctor)
    3. (Sentence ID:2) is shown by a study (meaning: A study has shown that patients with Fever and a recent travel History to Ghana should visit a doctor)

    You may change the sentences and sentence order in order to get the optimal nesting of statements.

    DO NOT use the Sentence ID references in the explanation field, just use the full sentence spelled out.

    Please apply this method to the following sentences:
    {{sentences}}
    Consider the original text:
    {{original}}

    {{ ctx.output_format(prefix="Use the following OUTPUT FORMAT:") }}
  "#
}




function BreakDown(input: SentencesID) -> SentencesID {
  client Qwen32b5
  prompt #"
    "Break down all given sentences in simpler statements if possible, you may reference information in other sentences using These This etc.
    Example:
    1. Patients with Fever and a recent travel History to Ghana should visit a doctor
    2. This is recommended by the guidelines
    3. These Patients are at risk of Malaria
    Broken down:
    1. Patients with Fever and a recent travel History to Ghana
    2. These Patients should visit a doctor
    3. This is recommended by the guidelines
    3. These Patients are at risk of Malaria

    ONLY SEPARATE THE SENTENCES IF THe INFORMATION CAN BE VIEWED SEPARATELY

    Example:
    1. A study found that Patients with Fever and a recent travel History to Ghana should visit a doctor

    Broken Down:
    1. A study found that Patients with Fever and a recent travel History to Ghana
    2. These Patients should visit a doctor

    {{input}}
    {{ ctx.output_format(prefix="Use the following OUTPUT FORMAT:") }}
  "#
}

function NestingStatements(input: SentencesID) -> SentencesID {
  client Qwen14b4
  prompt #"

    Break down all given sentences in simpler statements if possible, and then Identify and extract all nested statements
    Example:
    1. Patients with Fever and a recent travel History to Ghana should visit a doctor
    2. This is recommended by the guidelines
    3. These Patients are at risk of Malaria
    Broken down:
    1. Patients with Fever and a recent travel History to Ghana 
    2. These Patients should visit a doctor
    3. This is recommended by the guidelines
    3. These Patients are at risk of Malaria
    Nested Statements identified and transformed:
    1. Patients with Fever and a recent travel History to Ghana 
    2. (Sentence ID:1) should visit a doctor
    3. (Sentence ID:2) is recommended by the guidelines
    3. (Sentence ID:1) are at risk of Malaria

    {{input}}
    {{ ctx.output_format(prefix="Use the following OUTPUT FORMAT:") }}
  "#
}

function GraphConstructor(input: string) -> TriplesID {
  client Qwen14b4
  prompt #"
  ## 1. Overview
  You are a top-tier algorithm designed for extracting information in structured formats to build a knowledge graph.
  Try to capture as much information from the text as possible without sacrificing accuracy. Do not add any information that is not explicitly mentioned in the text.
  - **Nodes** represent entities and concepts.
  - The aim is to achieve simplicity and clarity in the knowledge graph, making it
  accessible for a vast audience.
  ## 2. Labeling Nodes
  - **Consistency**: Ensure you use available types for node labels.
  Ensure you use basic or elementary types for node labels.
  - For example, when you identify an entity representing a person, always label it as **'person'**. Avoid using more specific terms like 'mathematician' or 'scientist'.- **Node IDs**: Never utilize integers as node IDs. Node IDs should be names or human-readable identifiers found in the text.
  - **Relationships** represent connections between entities or concepts.
  Ensure consistency and generality in relationship types when constructing knowledge graphs. Instead of using specific and momentary types such as 'BECAME_PROFESSOR', use more general and timeless relationship types like 'PROFESSOR'. Make sure to use general and timeless relationship types!
  ## 3. Logical operations
  - **Identify when a logical conclusion depends of the simultaneous occurence of multiple Nodes**: For example if a sentence states "Patients with Fever and a recent travel History to Ghana should visit a doctor ", the knowledge graph should reflect that both conditions are necessary to conclude the presence of Malaria by including a Node with the label AND which represents all Inputs and individual Nodes for each Input which are connected to the AND-Node via a part_of relation.  
  "Patients with Fever and a recent travel History to Ghana" -"should_visit"-> "doctor"
  "Fever"-"part_of"-> "Patients with Fever and a recent travel History to Ghana"
  "recent travel History to Ghana"-"part_of"-> "Patients with Fever and a recent travel History to Ghana"
  ## 4. Nested Statements
  - **prioritize perfect representation of information**: When presented with nested statements you can use a triple ID as a subject or object in a different triple to represent the nested statement.
  -Example: Recent studies have shown that Fever and a recent travel History to Ghana indicate Malaria.
  "Fever and a recent travel History to Ghana" -"indicates"-> "Malaria" (TripleID:1)
  "recent studies"-"show"-> TripleID:1
  ## 5. Coreference Resolution
  - **Maintain Entity Consistency**: When extracting entities, it's vital to ensure consistency.
  If an entity, such as "John Doe", is mentioned multiple times in the text but is referred to by different names or pronouns (e.g., "Joe", "he"),always use the most complete identifier for that entity throughout the knowledge graph. In this example, use "John Doe" as the entity ID.
  Remember, the knowledge graph should be coherent and easily understandable, so maintaining consistency in entity references is crucial.
  ## 6. Strict Compliance
  Adhere to the rules strictly. Non-compliance will result in termination.

    {{input}}
    {{ ctx.output_format(prefix="Use the following OUTPUT FORMAT:") }}
  "#
}

function A(input: string) -> Sentences {
  client Qwen14b4
  prompt #"
    "Break this sentence into the smallest number of simple sentences, each expressing only one idea."    
    {{input}}
    {{ ctx.output_format}}
  "#
}
function B(input: string) -> Sentences {
  client Qwen14b4
  prompt #"
    "Unwind all nested clauses and embedded phrases. Output a flat sequence of atomic sentences."
    {{input}}
    {{ ctx.output_format}}
  "#
}
function C(input: string) -> Sentences {
  client Qwen14b4
  prompt #"
    "Rewrite the following sentence without using 'and', 'but', or any coordinating conjunctions. Each new sentence should contain a single thought."
    {{input}}
    {{ ctx.output_format}}
  "#
}
function D(input: string) -> Sentences {
  client Qwen14b4
  prompt #"
    "Decompose this sentence so that each resulting sentence has one subject, one verb, and one object or complement."
    {{input}}
    {{ ctx.output_format}}
  "#
}
function E(input: string) -> Sentences {
  client Qwen14b4
  prompt #"
    "Simplify this sentence by removing all subordinate clauses. Replace them with standalone sentences."
    {{input}}
    {{ ctx.output_format}}
  "#
}
function F(input: string) -> Sentences {
  client Qwen14b4
  prompt #"
    "Rewrite this text so that every sentence expresses only one fact or claim. Do not combine ideas in the same sentence."
    {{input}}
    {{ ctx.output_format}}
  "#
}
function G(input: string) -> Sentences {
  client Qwen14b4
  prompt #"
    "Convert this into a list of simple declarative statements. Each statement must be syntactically minimal and semantically isolated."
    {{input}}
    {{ ctx.output_format}}
  "#
}
function H(input: string) -> Sentences {
  client Qwen14b4
  prompt #"
    "Split compound and complex sentences into multiple basic sentences with no embedded or coordinated structures."
    {{input}}
    {{ ctx.output_format}}
  "#
}
function I(input: string) -> Sentences {
  client Qwen14b4
  prompt #"
    "Transform this passage into a sequence of elementary assertions that a machine could easily parse."
    {{input}}
    {{ ctx.output_format}}
  "#
}
function J(input: string) -> Sentences {
  client Qwen14b4
  prompt #"
    "Flatten this sentence. No passive voice, no relative clauses, no conjunctions. Only basic active-voice statements."
    {{input}}
    {{ ctx.output_format}}
  "#
}