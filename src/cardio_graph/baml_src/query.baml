
class Interpretation {
  text string @description("a text in natural language that interprets the Knowledge graph to answer the question and explains what was used to answer the question")
}

class Explanation {
  explanation string @description("a text in natural language that is the answer to the question")
}

class Entity {
  entity string @description("one entity of a sentence")
}

class Entities {
  entities Entity[] @description("a list of entities")
}

class Statement {
  statement_node string @description("the ID + rdf:statement")
  subject string @description("the ID and tail node value of the triple where rdf:subject is the edge")
  predicate string @description("the ID and tail node value of the triple where rdf:predicate is the edge")
  object string @description("the ID and tail node value of the triple where rdf:object is the edge")
}

class Statements {
  statement Statement[] @description("a list of statements")
}

class Triple {
  head_node_id string @description("the ID of the head node")
  head_node_value string @description("the value of the head node")
  relation string @description("the relation of the head node to the tail node")
  tail_node_id string @description("the ID of the tail node")
  tail_node_value string @description("the value of the tail node")
}

class Triples {
  triples Triple[] @description("a list of triples")
}

class Node {
  id string @description("the ID of the node")
  value string @description("the value of the node")
}

class Nodes {
  nodes Node[] @description("a list of nodes")
}

class ANDStatement {
  statement Node @description("a statement that is a conjunction of other statements")
  met_conditions Nodes @description("a list of conditions that are met by this statement")
  unmet_conditions Nodes @description("a list of conditions that are not met by this statement")
  output Triples @description("a list of output triples that are affected by this statement")
}


class ANDStatements {
  and_statements ANDStatement[] @description("a list of AND statements")
}

function EntityExtractor(input: string) -> Entities {
  client Qwen14b4
  prompt #"
    Identify and extract all entities from the following text:
    {{input}}
    {{ ctx.output_format(prefix="Use the following OUTPUT FORMAT:") }}
  "#
}

function EntityCorrector(nodes: string, prompt_entities: Entities) -> Entities {
  client Qwen14b4
  prompt #"
    Check if the extracted Nodes are sematically matching the entities extracted from the text.:
    Nodes:
    {{nodes}}

    Entities from text:
    {{prompt_entities}}

    Remove the Nodes that do not match the entities in meaning and output the remaining Nodes
    {{ ctx.output_format(prefix="Use the following OUTPUT FORMAT:") }}
  "#
}


function Interpreter(input: Triples, prompt: string, statements: Statements, logic: ANDStatements) -> Interpretation {
  client Qwen14b4
  prompt #"
    {{prompt}}
    DO NOT use any information that is not in the input or statements to answer the question.
    {{input}}
    consider the following interpretation of the rdf:statement nodes:
    {{statements}}
    consider the following AND statements where if all condition are met the output is true:
    {{logic}}
    {{ ctx.output_format}}
  "#
}


function QuestionWithoutContext(prompt: string) -> Explanation {
  client Qwen14b4
  prompt #"
    {{prompt}}
    {{ ctx.output_format}}
  "#
}


function Easy(input: string) -> string {
  client Qwen30b4
  prompt #"

    According to the ISCHEMIA trial:
    Answer the quesion on whether an invasive or a conservative strategy is better for CCS Patients, tell me which end points are affected
    Give the exact answer to the question, and then give the reasoning behind it.
    {{ ctx.output_format}}
  "#
}

function SubgraphInterpreter(text: string, Statements: string) -> Interpretation {
  client GemmaG2 
  prompt #"
    "Interpret the following Knowledgegraph, where the relations are in the following notation: (head ID,"/", head value,"--", edge, "-->",tail ID,"/", tail value):
    {{text}}
    "Consider the explanations for the rdf:statement nodes"





    Identify Nodes with the value rdf:statement and find their rdf:subject, rdf:predicate and rdf:object.
    Interpret what each rdf:statement node represents in natural language.

    {{ ctx.output_format(prefix="Use the following OUTPUT FORMAT:") }}
  "#
}

function UnReificator(input: Triples) -> Statements {
  client Qwen14b4
  prompt #"
    For each Triple where head_node_value is "rdf:Statement", identify all Triple entries that have the same head_node_id. From these, extract the tail_node_id and tail_node_value for each of the following relation values: "rdf:subject", "rdf:predicate", and "rdf:object". Then, for each group, construct a Statement object where:
    statement_node is the head_node_id concatenated with "rdf:statement"
    subject is the tail_node_id concatenated with the tail_node_value where relation is "rdf:subject"
    predicate is the tail_node_id concatenated with the tail_node_value where relation is "rdf:predicate"
    object is the tail_node_id concatenated with the tail_node_value where relation is "rdf:object"
    {{input}}
    {{ ctx.output_format(prefix="Only use the following OUTPUT FORMAT:")}}
  "#
}