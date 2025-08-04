function Image2Table(img: image) -> ListOfStructuralData {
  client Qwen25vl32bG5
  prompt #"
    The following image comes from a medical guidelinea about cardiovascular diseases.
    When you don't see a table, you should return an empty list.
    Otherwise, extract all tables either in the form of triples or, if table is too comples and nested, as if-else trees:
    - Some tables may contain multiple rows or columns that stand in semantic relation to each other. Then you have to unroll the table into multiple triples.
    - If the table is nested and complex, you should extract it as an if-else tree.
    - If the head contains multiple head entities, unroll the head into multiple triples.
    - If the tail contains multiple tail entities, unroll the tail into multiple triples.
    - If a head is empty (an empty cell at the beginning of a row), assume that the head is the same as the previous head.
    Keep the information short and concise as it will be later integrated into a medical knowledge graph,but
    also take care that the triples convey the overall meaning of the table.
    {{img}}
    {{ ctx.output_format(prefix="Use the following OUTPUT FORMAT:") }}
  "#
}