import json
import os
import pickle
import re
from pathlib import Path

from graph_utils import escape_json
from langchain_core.prompts import ChatPromptTemplate
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter
from llm import llm
from prompt_utils import create_unstructured_prompt
from templates import (
    GUIDELINES_BASESTRINGPARTS_JSON,
    GUIDELINES_EXAMPLES,
    NODES,
    TEMPLATE,
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

examples = escape_json(json.dumps(eval(f"{task.upper()}_EXAMPLES")))
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            eval(f"{task.upper()}_BASESTRINGPARTS_JSON")[0]
            + TEMPLATE.format(
                node_labels=NODES,
                # examples="",
                examples=examples,
                format_instructions="",
                input="",
            ),
        ),
        ("human", "{input}"),
    ]
)
chain = prompt | llm

# prompt = create_unstructured_prompt(
#     template=TEMPLATE,
#     base_string_parts=eval(f"{task.upper()}_BASESTRINGPARTS_JSON"),
#     examples=eval(f"{task.upper()}_EXAMPLES"),
#     node_labels=NODES,
# )
# llm_transformer = LLMGraphTransformer(
#     llm=llm,
#     allowed_nodes=NODES,
#     strict_mode=True,
#     prompt=prompt,
# )

graphdoc_pkl_path = f"../outputs/seite52/{task}_graph_documents.pkl"
# graphdoc_pkl_path = f"../outputs/{task}_graph_documents.pkl"

f = open(graphdoc_pkl_path, "wb")
for i, (page_text, page_infos) in enumerate(page_texts):
    page, page_nr = page_infos
    print(i, page_nr)
    try:
        ai_msg = chain.invoke(
            {
                "input": page_text.page_content,
            }
        )
        # graph_doc = llm_transformer.convert_to_graph_documents([page_text])
        # graph_doc[0].source.metadata["page_nr"] = str(page_nr)
        # graph_doc[0].source.metadata["page_content"] = str(page)
        # graph_doc[0].source.metadata["id"] = str(page_nr)
        pass
        # pickle.dump(graph_doc[0], f)
    except Exception as e:
        print(e)
