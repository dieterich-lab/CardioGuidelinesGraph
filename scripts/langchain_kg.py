import json
import os
import pickle
from pathlib import Path

from langchain_community.graphs import Neo4jGraph
from prompt_utils import create_unstructured_prompt
from templates import TEMPLATE

os.environ["NEO4J_URI"] = "bolt+s://linda-llm-dev.dieterichlab.org:7687"
os.environ["NEO4J_USERNAME"] = "neo4j"
os.environ["NEO4J_PASSWORD"] = "KWCeoHhkJYAiFa3XTZZZLC77bHiZ5xzj"


task = "guidelines"

graph = Neo4jGraph()

from langchain_community.llms import Ollama

# model = "mixtral:8x22b"
model = "mixtral:8x7b"
llm = Ollama(model=model, base_url="http://10.250.135.153:11434")


from langchain_experimental.graph_transformers import LLMGraphTransformer

llm_transformer = LLMGraphTransformer(llm=llm)


from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=100,
    length_function=len,
    is_separator_regex=False,
)
# paper_dict = dict()
paper_paths = [Path("../data/herzinsuffizienz.txt")]

paper_pkl_path = "../outputs/paper_chunks/paper_chunks.pkl"
# paper_dict_path = "../outputs/paper_dict.pkl"

f = open(paper_pkl_path, "wb")
for i, x in enumerate(paper_paths):
    print(i, x)
    # paper_dict[i] = str(x)
    text = open(x, "r").read().strip()
    if text:
        texts = text_splitter.create_documents([text])
        for t in texts:
            pickle.dump(t, f)
            # pickle.dump((t, i), f)
f.close()

# with open(paper_dict_path, "w") as f:
#     json.dump(paper_dict, f, indent=4)

# with open(paper_dict_path, "r") as f:
#     paper_dict = json.load(f)
#     paper_dict = {int(k): v for k, v in paper_dict.items()}

documents = list()
with open(paper_pkl_path, "rb") as f:
    while 1:
        try:
            documents.append(pickle.load(f))
        except EOFError:
            break
print(len(documents))

prompt = create_unstructured_prompt(
    template=TEMPLATE,
    base_string_parts=eval(f"{task.upper()}_BASESTRINGPARTS"),
    examples=eval(f"{task.upper()}_EXAMPLES"),
    node_labels=["PROTEIN"],
    rel_types=["INTERACTS_WITH"],
)

llm_transformer = LLMGraphTransformer(
    llm=llm,
    allowed_nodes=["Protein"],
    allowed_relationships=["INTERACTS_WITH"],
    strict_mode=True,
    prompt=prompt,
)

graphdoc_pkl_path = (
    f"/beegfs/prj/LINDA_LLM/outputs/graph_docs/{task}_graph_documents.pkl"
)

graph_documents = list()
f = open(graphdoc_pkl_path, "wb")
for i, (doc, id) in enumerate(documents):
    print(i, id)
    try:
        graph_doc = llm_transformer.convert_to_graph_documents([doc])
        # graph_doc[0].source.metadata["source"] = paper_dict[id]
        graph_doc[0].source.metadata["id"] = str(id)
        pickle.dump(graph_doc[0], f)
    except Exception as e:
        print(e)
f.close()
