import argparse
import pickle
import re
from pathlib import Path

from json_repair import repair_json
from langchain_community.graphs.graph_document import GraphDocument, Node, Relationship

# from graph_utils import escape_json
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain_core.utils.function_calling import convert_to_openai_tool

# from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_ollama import ChatOllama
from langchain_text_splitters import MarkdownTextSplitter

# from prompt_utils import create_unstructured_prompt
from structured_classes import MedicRouter, TableRouter, Triples
from templates import WORKING_TABLE_PROMPT
from utils import Timeout

parser = argparse.ArgumentParser()
parser.add_argument(
    "--dev",
    action="store_true",
)
parser.add_argument(
    "--model", choices=["nemo", "mixtral_big", "mixtral_small", "v03"], default="nemo"
)
args = parser.parse_args()
model_dict = {
    "nemo": "mistral-nemo",
    "mixtral_big": "mixtral:8x22b",
    "mixtral_small": "mixtral:8x7b",
    "v03": "mistral:v0.3",
}
model = model_dict[args.model]

g4 = "10.250.135.153"
g2 = "10.250.135.143"
g5 = "10.250.135.156"
port34 = "11434"
port35 = "11435"
port36 = "11436"
PORT = port35
llm = ChatOllama(
    model=model,
    base_url=f"http://{g4}:{PORT}",
    temperature=0.0,
    keep_alive="24h",
)

text_splitter = MarkdownTextSplitter(
    chunk_size=1000,
    chunk_overlap=100,
    length_function=len,
    is_separator_regex=False,
)

# source_doc_path = Path("../data/marker/herzinsuffizienz.md")
source_doc_path = Path("../data/marker/tabelle3.md")
# graphdoc_pkl_path = f"../outputs/marker/herzinsuffizienz_graph_documents.pkl"
graphdoc_pkl_path = f"../outputs/tabelle3_graph_documents.pkl"


chunks = text_splitter.create_documents([open(source_doc_path, "r").read().strip()])

graph_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            WORKING_TABLE_PROMPT,
        ),
        (
            "human",
            "Extrahiere nun Tripel aus dem folgenden Input in dem vorgegebenen Format: {input}",
        ),
    ]
)


table_routing_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
            Bitte sage mir, ob es sich im folgenden Text eine Tabelle oder Auflistung befindet.
            """,
        ),
        (
            "human",
            "Benute für Deine Antwort das vorgebene Format. Input: {input}",
        ),
    ]
)

medic_routing_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
            Du bist ein Assistent zum Erkennen von medizinischen Inhalten.
            """,
        ),
        (
            "human",
            "Befindet sich in der folgenden Tabelle Inhalte zur medizinischen Behandlung von Patienten? Benutze ausschließlich das vorgegebene Format! Input: {input}",
        ),
    ]
)


graph_schema = convert_to_openai_tool(Triples)
table_routing_schema = convert_to_openai_tool(TableRouter)
medic_routing_schema = convert_to_openai_tool(MedicRouter)
graph_llm = llm.with_structured_output(graph_schema, include_raw=True)
table_routing_llm = llm.with_structured_output(table_routing_schema, include_raw=True)
medic_routing_llm = llm.with_structured_output(medic_routing_schema, include_raw=True)

graph_chain = graph_prompt | graph_llm
table_routing_chain = table_routing_prompt | table_routing_llm
medic_routing_chain = medic_routing_prompt | medic_routing_llm


def route(info):
    try:
        if info["answer"]["parsed"]["decision"] == "nein":
            return None
        else:
            return graph_chain
    except:
        if "nein" in info["answer"]["raw"].content.lower():
            return None
        else:
            return graph_chain


def table_route(info):
    try:
        if info["answer"]["parsed"]["decision"] == "nein":
            return None
        else:
            return medic_routed_chain
    except:
        if "nein" in info["answer"]["raw"].content.lower():
            return None
        else:
            return medic_routed_chain


table_routed_chain = {
    "answer": table_routing_chain,
    "input": lambda x: x["input"],
} | RunnableLambda(route)

medic_routed_chain = {
    "answer": medic_routing_chain,
    "input": lambda x: x["input"],
} | RunnableLambda(route)

medic_table_routed_chain = {
    "answer": table_routing_chain,
    "input": lambda x: x["input"],
} | RunnableLambda(table_route)


if not args.dev:
    f = open(graphdoc_pkl_path, "wb")

for i, chunk in enumerate(chunks):
    # for i, (doc, page_nrs) in enumerate(docs):
    print(i)
    c = 0
    try:
        # while c < 5:
        #     try:
        #         with Timeout(60):
        #             msg = table_routed_chain.invoke(
        #                 {
        #                     "input": doc.page_content,
        #                 }
        #             )
        #             break
        #     except Timeout.Timeout:
        #         print("Timeout")
        #         c += 1
        msg = table_routed_chain.invoke(
            {
                "input": chunk,
                # "input": doc.page_content,
            }
        )
        # msg = medic_table_routed_chain.invoke(
        #     {
        #         "input": doc.page_content,
        #     }
        # )
        if msg is None:
            parsed = []
        else:
            parsed = msg["parsed"]
            if parsed is None:
                _parsed = repair_json(msg["raw"].content, return_objects=True)
                for p in _parsed:
                    if not isinstance(p, dict):
                        continue
                    if "triples" in p:
                        parsed = [t for t in p["triples"] if len(t) == 3]
                        break
                    for k, v in p.items():
                        if "triples" in v:
                            parsed = [t for t in v["triples"] if len(t) == 3]
                            break
            else:
                parsed = msg["parsed"]["triples"]

        if not parsed:
            continue
        nodes_set = set()
        rels = list()
        for triple in parsed:
            n1 = triple[0]
            n2 = triple[2]
            nodes_set.add(n1)
            nodes_set.add(n2)
            rels.append(
                Relationship(source=Node(id=n1), target=Node(id=n2), type=triple[1])
            )
        nodes = [Node(id=el) for el in list(nodes_set)]
        graph_doc = GraphDocument(nodes=nodes, relationships=rels, source=chunk)
        # graph_doc.source.metadata["pages"] = page_nrs
        pickle.dump(graph_doc, f)
    except Exception as e:
        print(e)

if not args.dev:
    f.close()

print(f"Finished writing graph docs to {graphdoc_pkl_path}.")
