import pickle
from pathlib import Path

from langchain_community.graphs.graph_document import GraphDocument, Node, Relationship
from langchain_core.runnables import RunnableLambda
from langchain_core.utils.function_calling import convert_to_openai_tool
from langchain_text_splitters import MarkdownTextSplitter

from cardio_graph_core.legacy_graph_pipeline.graph_utils import attempt, parse_msg
from cardio_graph_core.legacy_graph_pipeline.llm import llm
from cardio_graph_core.legacy_graph_pipeline.parser import args
from cardio_graph_core.legacy_graph_pipeline.prompts import (
    hallu_prompt,
    simplify_prompt,
    table_prompt,
    table_routing_prompt,
    text_prompt,
)
from cardio_graph_core.legacy_graph_pipeline.structured_classes import (
    HalluRouter,
    TableRouter,
    Triples,
)

text_splitter = MarkdownTextSplitter(
    chunk_size=1000,
    chunk_overlap=100,
    length_function=len,
    is_separator_regex=False,
)

# source_doc_path = Path("../data/marker/herzinsuffizienz.md")
source_doc_path = Path("../data/marker/tabelle3.md")
# source_doc_path = Path("/home/pwiesenbach/guide/data/llama_parse/seite52/seite52.txt")
# graphdoc_pkl_path = f"../outputs/marker/herzinsuffizienz_graph_documents.pkl"
graphdoc_pkl_path = f"../outputs/tabelle3_graph_documents.pkl"
# graphdoc_pkl_path = f"../outputs/seite52_graph_documents.pkl"


chunks = text_splitter.create_documents([open(source_doc_path, "r").read().strip()])

graph_schema = convert_to_openai_tool(Triples)
graph_llm = llm.with_structured_output(graph_schema, include_raw=True)

table_routing_schema = convert_to_openai_tool(TableRouter)
table_routing_llm = llm.with_structured_output(table_routing_schema, include_raw=True)

hallu_routing_schema = convert_to_openai_tool(HalluRouter)
hallu_routing_llm = llm.with_structured_output(hallu_routing_schema, include_raw=True)

table_chain = table_prompt | graph_llm
text_chain = text_prompt | graph_llm


def route(info):
    try:
        if info["answer"]["parsed"]["decision"] == "nein":
            return text_chain
        else:
            return table_chain
    except:
        if "nein" in info["answer"]["raw"].content.lower():
            return text_chain
        else:
            return table_chain


table_routing_chain = table_routing_prompt | table_routing_llm
table_routed_chain = {
    "answer": table_routing_chain,
    "input": lambda x: x["input"],
} | RunnableLambda(route)

hallu_chain = hallu_prompt | hallu_routing_llm
simplify_chain = simplify_prompt | graph_llm

if not args.dev:
    f = open(graphdoc_pkl_path, "wb")

for i, chunk in enumerate(chunks):
    print(i)
    try:
        routed_msg = attempt(5, 60, table_routed_chain.invoke, {"input": chunk})
        triples = parse_msg(routed_msg, "triples")
        if not triples:
            continue
        # hallu_triples = list()
        # for triple in routed_parsed:
        #     hallu_msg = attempt(5, 60, hallu_chain.invoke, {"input": triple, "text": chunk})
        #     if parse_msg(hallu_msg, "decision") == "nein":
        #         continue
        #     hallu_triples += [triple]
        # if not hallu_triples:
        #     continue
        simple_triples = list()
        for triple in triples:
            simple_msg = attempt(5, 60, simplify_chain.invoke, {"input": triple})
            simple_parsed = parse_msg(simple_msg, "triples")
            if simple_parsed:
                simple_triples += simple_parsed
        triples += simple_triples
        nodes_set = set()
        rels = list()
        for triple in triples:
            n1 = triple["head"]
            n2 = triple["tail"]
            nodes_set.add(n1)
            nodes_set.add(n2)
            rels.append(
                Relationship(
                    source=Node(id=n1), target=Node(id=n2), type=triple["relation"]
                )
            )
        nodes = [Node(id=el) for el in list(nodes_set)]
        graph_doc = GraphDocument(nodes=nodes, relationships=rels, source=chunk)
        if not args.dev:
            pickle.dump(graph_doc, f)
    except Exception as e:
        print(e)
if not args.dev:
    f.close()

print(f"Finished writing graph docs to {graphdoc_pkl_path}.")
