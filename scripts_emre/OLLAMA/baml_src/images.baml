
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

function Image2Tree(img: image) -> ListOfStructuralData {
  client Qwen25vl32bG5 
  // client Qwen25vl72bG5 
  // client Llava34bG5
  // client GemmaG5
  prompt #"
    The following image comes from a medical guidelinea about cardiovascular diseases.
    Extract all structural information:
    - If you find isolated information, extract it as semantic triple
    - if you identify a flow chart it into a string representation of an if-else tree.
    {{img}}
    {{ ctx.output_format(prefix="Use the following OUTPUT FORMAT:") }}
  "#
}