import asyncio
import json
import os
import pickle
import re
from pathlib import Path

from json_repair import repair_json
from langchain_community.graphs.graph_document import GraphDocument, Node, Relationship
from langchain_core.documents import Document

# from graph_utils import escape_json
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain_core.utils.function_calling import convert_to_openai_tool

# from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_ollama import ChatOllama
from langchain_text_splitters import (
    MarkdownTextSplitter,
    RecursiveCharacterTextSplitter,
)

# from prompt_utils import create_unstructured_prompt
from structured_classes import MedicRouter, TableRouter, Triples
from templates import WORKING_TABLE_PROMPT

# model = "mixtral:8x22b"
# model = "mixtral:8x7b"
# model = "mixtral:instruct"
nemo = "mistral-nemo"
llama31 = "llama3.1"
g4 = "10.250.135.153"
g23 = "10.250.135.143"
g5 = "10.250.135.156"
port34 = "11434"
port35 = "11435"
port36 = "11436"
llm = ChatOllama(
    model=nemo,
    base_url=f"http://{g4}:{port36}",
    temperature=0.0,
    keep_alive="24h",
)

task = "guidelines"

text_splitter = MarkdownTextSplitter(
    chunk_size=1000,
    chunk_overlap=100,
    length_function=len,
    is_separator_regex=False,
)

source_doc_path = Path("../data/herzinsuffizienz.txt")
# source_doc_path = Path("../data/seite52/seite52.txt")
doc_pkl_path = "../outputs/doc_chunks.pkl"
# chunk_pkl_path = "../outputs/seite52/doc_chunks.pkl"

source_doc = open(source_doc_path, "r").read().strip()

# f = open(doc_pkl_path, "wb")
# docs = text_splitter.create_documents([source_doc])
# page_nrs = [1]
# for pt in docs:
#     _page_nrs = re.findall(r"Seite\s+(\d+)", pt.page_content)
#     if not page_nrs:
#         page_nrs = _page_nrs
#     pickle.dump((pt, page_nrs), f)
# f.close()

docs = list()

with open(doc_pkl_path, "rb") as f:
    while 1:
        try:
            docs.append(pickle.load(f))
        except EOFError:
            break
print(len(docs))

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
            Du bist ein Assistent zum Erkennen von Markdown-Tabellen.
            """,
        ),
        (
            "human",
            "Handelt es sich bei dem folgenden Input um eine Markdown-Tabelle? Benutze ausschließlich das vorgegebene Format! Input: {input}",
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

# graphdoc_pkl_path = f"../outputs/seite52/{task}_graph_documents.pkl"
graphdoc_pkl_path = f"../outputs/{task}_graph_documents.pkl"


async def extract():
    tasks = [
        asyncio.create_task(graph_chain.ainvoke({"input": page_text.page_content}))
        for page_text, _ in docs
    ]
    results = await asyncio.gather(*tasks)
    return results


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


f = open(graphdoc_pkl_path, "wb")
for i, (doc, page_nrs) in enumerate(docs):
    try:
        msg = table_routed_chain.invoke(
            {
                "input": doc.page_content,
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
                    parsed = [t for t in p["triples"] if len(t) == 3]
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
        graph_doc = GraphDocument(nodes=nodes, relationships=rels, source=doc)
        graph_doc.source.metadata["pages"] = page_nrs
        pickle.dump(graph_doc, f)
    except Exception as e:
        print(e)

f.close()


# results = asyncio.run(extract())
# print(results)
