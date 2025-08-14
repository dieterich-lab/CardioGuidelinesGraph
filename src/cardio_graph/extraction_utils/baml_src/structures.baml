class IfElseTree {
  if_else_tree string @description("String representation of a flowchart as if-else tree")
}

class SemanticTriple {
  head_node_value string @description("the value of the head node")
  relation string @description("the relation of the head node to the tail node")
  tail_node_value string @description("the value of the tail node")
}

class ListOfStructuralData {
  list (IfElseTree | SemanticTriple)[] @description("A list of if-else-trees and/or semantic triples extracted from the image")
}

function Image2Structure(img: image) -> ListOfStructuralData {
  client Qwen25vl32bG5
  prompt #"
    The following image comes from a medical guideline about cardiovascular diseases.
    If you detect a table:
    Extract it in the form of triples or, if the table is too complex and nested, as if-else trees:
    - Some tables may contain multiple rows or columns that stand in semantic relation to each other. Then you have to unroll the table into multiple triples.
    - If the table is nested and complex, you should extract it as an if-else tree.
    - If the head contains multiple head entities, unroll the head into multiple triples.
    - If the tail contains multiple tail entities, unroll the tail into multiple triples.
    - If a head is empty (an empty cell at the beginning of a row), assume that the head is the same as the previous head.
    If you detect a figure:
    - If you find isolated information, extract it as semantic triple.
    - If you identify a flow chart or a decision tree convert it into a string representation of an if-else tree.
    Keep the information short and concise as it will be later integrated into a medical knowledge graph.
    IMPORTANT: To convey the overall meaning of the structures, you can also incorporate information from the caption.
    {{img}}
    {{ ctx.output_format(prefix="Use the following OUTPUT FORMAT:") }}
  "#
}

function Markdown2Structure(markdown: string) -> ListOfStructuralData {
  client Qwen32b5_35
  prompt #"
    The following markdown document comes from a medical guideline about cardiovascular diseases.
    If you detect a table:
    Extract it in the form of triples or, if the table is too complex and nested, as if-else trees:
    - Some tables may contain multiple rows or columns that stand in semantic relation to each other. Then you have to unroll the table into multiple triples.
    - If the table is nested and complex, you should extract it as an if-else tree.
    - If the head contains multiple head entities, unroll the head into multiple triples.
    - If the tail contains multiple tail entities, unroll the tail into multiple triples.
    - If a head is empty (an empty cell at the beginning of a row), assume that the head is the same as the previous head.
    If you detect a figure:
    - If you find isolated information, extract it as semantic triple
    - If you identify a flow chart or a decision tree convert it into a string representation of an if-else tree.
    Keep the information short and concise as it will be later integrated into a medical knowledge graph.
    IMPORTANT: To convey the overall meaning of the structures, you can also incorporate information from the caption.
    {{markdown}}
    {{ ctx.output_format(prefix="Use the following OUTPUT FORMAT:") }}
  "#
}