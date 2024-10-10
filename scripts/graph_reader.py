import asyncio
import json
import os
import pickle
import re
from pathlib import Path

from json_repair import repair_json

# from graph_utils import escape_json
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain_core.utils.function_calling import convert_to_openai_tool

# from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_ollama import ChatOllama
from langchain_text_splitters import RecursiveCharacterTextSplitter

# from prompt_utils import create_unstructured_prompt
from structured_classes import TRIPLES_SCHEMA, Router, Triples
from templates import WORKING_TABLE_PROMPT

# model = "mixtral:8x22b"
# model = "mixtral:8x7b"
# model = "mixtral:instruct"
nemo = "mistral-nemo"
llama31 = "llama3.1"
g4 = "10.250.135.153"
g23 = "10.250.135.143"
g5 = "10.250.135.156"
port4 = "11434"
port5 = "11435"
port6 = "11436"
llm = ChatOllama(
    model=nemo,
    base_url=f"http://{g23}:{port6}",
    # format="json",
    temperature=0.1,
    keep_alive="24h",
)

task = "guidelines"

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=100,
    length_function=len,
    is_separator_regex=False,
)

# source_doc_path = Path("../data/herzinsuffizienz.txt")
source_doc_path = Path("../data/seite52/seite52.txt")
chunk_pkl_path = "../outputs/seite52/doc_chunks.pkl"

source_doc = open(source_doc_path, "r").read().strip()
_pages = re.split(r"(Seite\s+\d+\n*)", source_doc)
pages = list()
for i, p in enumerate(_pages[:-1]):
    if i % 2:
        continue
    pages += [_pages[i] + _pages[i + 1]]


f = open(chunk_pkl_path, "wb")
for page_text in pages:
    page_nr = re.search(r".*Seite\s+(\d+)", page_text).groups()[0]
    page_texts = text_splitter.create_documents([page_text])
    for pt in page_texts:
        pickle.dump((pt, (page_text, page_nr)), f)
f.close()

page_texts = list()

with open(chunk_pkl_path, "rb") as f:
    while 1:
        try:
            page_texts.append(pickle.load(f))
        except EOFError:
            break
print(len(page_texts))

# ```
# [
#     Triple(head='ACEi', head_type=<Nodes.medikamente: 'MEDIKAMENTE'>, relation='wurde getestestet gegen', tail='RASi+BB (+MRA)', tail_type=<Nodes.medikamente: 'MEDIKAMENTE'>),
#     Triple(head='ACEi', head_type=<Nodes.medikamente: 'MEDIKAMENTE'>, relation='wirkt sich negativ aus auf', tail='Mortalität', tail_type=<Nodes.krankheit: 'KRANKHEIT'>)
#     Triple(head='ACEi', head_type=<Nodes.medikamente: 'MEDIKAMENTE'>, relation='wirkt sich negativ aus auf', tail='Hospitalisierung', tail_type=<Nodes.krankheitsmanagmement: 'KRANKHEITSMANAGEMENT'>)
# ]
# ```

# Die Tripel sollen aus den folgenden 5 Attributen bestehen:
# *.    head: Beschreibt die Start-Entität
# *.    head_type: Beschreibt den Typ der Start-Entität. Erlaubte Typen sind:
#       KRANKHEIT, ANATOMIE, MEDIKAMENTE, NICHT-MEDIKAMENTÖSE THERAPEUTISCHE MASSNAHMEN, INVASIVE THERAPIEMASSNAHMEN, DIAGNOSTIK, KRANKHEITSMANAGEMENT, PATIENTENMANAGEMENT,
# *.    relation: Beschreibt die Relation zwischen Start-Entität udn Ziel-Entitäts
# *.    tail: Beschreibt die Ziel-Entität
# *.    tail_type: Beschreibt den Typ der Ziel-Entität. Erlaubte Typen sind:
#       KRANKHEIT, ANATOMIE, MEDIKAMENTE, NICHT-MEDIKAMENTÖSE THERAPEUTISCHE MASSNAHMEN, INVASIVE THERAPIEMASSNAHMEN, DIAGNOSTIK, KRANKHEITSMANAGEMENT, PATIENTENMANAGEMENT,

# 4. Die Richtlinie ist auf Deutsch, also antworte auch auf Deutsch.
# 5. Halt Dich genau an das vorgegebene JSON-Schema und extrahiere eine Liste der vorgebenen JSON-Objkete:

# ```
# {schema}
# ```

# Jedes Tripel besteht aus den Einträgen 'head', 'head_type', 'relation', 'tail' und 'tail_type'.

# Jedes extrahierte Tripel muss muss immer aus den folgenden Einträge bestehen:
# 1. head: Beschreibt die Start-Entität.
# 2. head_type: Beschreibt den Typ der Start-Entität. Erlaubte Einträge sind: KRANKHEIT, ANATOMIE, MEDIKAMENTE, NICHT-MEDIKAMENTÖSE THERAPEUTISCHE MASSNAHMEN, INVASIVE THERAPIEMASSNAHMEN, DIAGNOSTIK, KRANKHEITSMANAGEMENT, PATIENTENMANAGEMENT,
# 3. relation: Beschreibt die Relation zwischen Start-Entität und Ziel-Entität und darf ein beliebiger Freitext passend zum Input sein.
# 4. tail: Beschreibt die Ziel-Entität.
# 5. head_type: Beschreibt den Typ der Ziel-Entität. Erlaubte Einträge sind: KRANKHEIT, ANATOMIE, MEDIKAMENTE, NICHT-MEDIKAMENTÖSE THERAPEUTISCHE MASSNAHMEN, INVASIVE THERAPIEMASSNAHMEN, DIAGNOSTIK, KRANKHEITSMANAGEMENT, PATIENTENMANAGEMENT,


# Beispiel einer Markdown-Tabelle:
# #####
# |Substanzklasse|getestet gegen/im Vergleich zu|Mortalität, Hospitalisierungen|
# |---|---|---|
# |ACEi|Placebo|↓|

# ```
# [
#     head='ACEi', relation='wurde getestestet gegen', tail='Placebo'),
#     head='ACEi', relation='wirkt sich negativ aus auf', tail='Mortalität')
#     head='ACEi', relation='wirkt sich negativ aus auf', tail='Hospitalisierung')
# ]
# ```

construction_system = """
Du bist ein spezialisierter Arzt, der medizinische Informationen in Form von Tripeln aus den Markdown-Tabellen 
einer klinischen Richtlinie über Herzinssufizienz extrahiert. 
Jedes extrahierte Tripel muss immer aus den folgenden drei Einträgen bestehen:
1. head: Beschreibt die Start-Entität.
2. relation: Beschreibt die Relation zwischen Start-Entität und Ziel-Entität und darf ein beliebiger Freitext passend zum Input sein.
3. tail: Beschreibt die Ziel-Entität.

WICHTIG: 
* Extrahiere für jeden Tabelleneintrag ein eigenes Tripel. Lasse keine Zeile und keine Spalte aus!
* Wenn es sich bei dem Input um keine Tabelle handelt, dann gib eine leere Liste!
* Füge keine eigenen Inhalte ein!
"""

graph_human = (
    "Extrahiere nun Tripel aus dem folgenden Input in dem vorgegebenen Format: {input}"
)

graph_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            construction_system,
        ),
        (
            "human",
            graph_human,
        ),
    ]
)

routing_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Du bist ein Assistent, der Texte klassifizieren kann. Basierend auf dem Inhalt, entscheide ob der folgende Input eine Markdown-Tabelle ist oder Fließtext.",
        ),
        (
            "human",
            "Antworte nun 'ja', wenn es sich ume eine Markdown-Tabelle handelt, und 'nein' falls icht. Benutze ausschließlich das vorgegebene Format! Input: {input}",
        ),
    ]
)
routing_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Handelt es sich bei dem folgenden Input um eine Tabelle?",
        ),
        (
            "human",
            "Benutze ausschließlich das vorgegebene Format! Input: {input}",
        ),
    ]
)


# dict_schema = convert_to_openai_tool(TRIPLES_SCHEMA)
graph_schema = convert_to_openai_tool(Triples)
routing_schema = convert_to_openai_tool(Router)
graph_llm = llm.with_structured_output(graph_schema, include_raw=True)
routing_llm = llm.with_structured_output(routing_schema, include_raw=True)

graph_chain = graph_prompt | graph_llm
routing_chain = routing_prompt | routing_llm

graphdoc_pkl_path = f"../outputs/seite52/{task}_graph_documents.pkl"
# graphdoc_pkl_path = f"../outputs/{task}_graph_documents.pkl"

f = open(graphdoc_pkl_path, "wb")


async def extract():
    tasks = [
        asyncio.create_task(graph_chain.ainvoke({"input": page_text.page_content}))
        for page_text, _ in page_texts
    ]
    results = await asyncio.gather(*tasks)
    return results


def route(info):
    if info["answer"]["parsed"]["decision"] == "nein":
        return None
    else:
        return graph_chain


routed_chain = {
    "answer": routing_chain,
    "input": lambda x: x["input"],
} | RunnableLambda(route)


for i, (page_text, page_infos) in enumerate(page_texts):
    page, page_nr = page_infos
    print(i, page_nr)
    try:
        msg = routed_chain.invoke(
            {
                "input": page_text.page_content,
            }
        )
        # msg = graph_chain.invoke(
        #     {
        #         "input": page_text.page_content,
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

    except Exception as e:
        print(e)


# results = asyncio.run(extract())
# print(results)
