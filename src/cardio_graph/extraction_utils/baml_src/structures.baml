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

class Coverage {
  true_positives int @description("A true positive is when the model correctly predicts a positive case")
  false_positives int @description("a false positive is when it incorrectly predicts a positive case (when it's actually negative)")
  true_negatives int @description("a true negative is when it correctly predicts a negative case")
  false_negatives int @description("a false negative is when it incorrectly predicts a negative case (when it's actually positive)")
  precision float @description("Precision measures the accuracy of positive predictions. It answers the question: 'Of all the instances predicted as positive, how many were actually positive?'")
  recall float @description("(also known as sensitivity) measures the model's ability to find all positive instances. It answers the question: 'Of all the actual positive instances, how many were correctly identified?' ")
  accuracy float @description("Measures the overall correctness of the model's predictions, calculated as the ratio of correctly classified instances to the total number of instances")
  f1 float @description("F1-score is the harmonic mean of precision and recall. It provides a balanced measure that considers both false positives and false negatives, making it useful when there's a trade-off between precision and recall")
  overall_judgement string @description("A qualitative judgement of the overall quality of the baml json compared to the docling json. It can be 'good', 'bad' or 'neutral'.")
  reasoning string @description("A brief explanation of the reasoning behind the overall judgement.")
  missing_information string[] @description("A list of missing information in the baml json compared to the docling json. It should be a comma-separated list of missing information.")
}

function TableEvaluation(docling_json: string, baml_json: string) -> Coverage {
  client Qwen32b5_35
  prompt #"
    You are given to sets of json files that extracted information from a table in a medical guideline about cardiovascular diseases.
    1) The first one is from the "docling" libraray and contains the extracted information in a structured format.
    2) The second one is from the "baml" library and contains the same information but in a more semantic format, namely in the form of triples.
    We will consider the first (docling) json as ground truth.
    You have to judge the quality of the second (baml) json based on the first (docling) json.

    {{docling_json}}
    {{baml_json}}
    {{ ctx.output_format(prefix="Use the following OUTPUT FORMAT:") }}
  "#
}