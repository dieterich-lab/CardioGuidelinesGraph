import os
import pickle
import re
from pathlib import Path

from graph_utils import MyNeo4jGraph

# from langchain_community.graphs import Neo4jGraph


os.environ["NEO4J_URI"] = f"bolt+s://neo4j-wft-inf.dieterichlab.org:7687"
os.environ["NEO4J_USERNAME"] = "neo4j"
os.environ["NEO4J_PASSWORD"] = "KWCeoHhkJYAiFa3XTZZZLC77bHiZ5xzj"

print(f"Connecting to {os.environ['NEO4J_URI']}")
graph = MyNeo4jGraph()

graph.query(
    """
	MATCH (n)
	DETACH DELETE n
	"""
)

graph_documents = list()
task = "guidelines"
graphdoc_pkl_path = f"../outputs/{task}_graph_documents.pkl"

print(f"loading from {graphdoc_pkl_path}")
with open(graphdoc_pkl_path, "rb") as f:
    while 1:
        try:
            graph_documents.append(pickle.load(f))
        except EOFError:
            break

print(len(graph_documents))


# for d in graph_documents:
#     d.source.metadata["id"] = str(d.source.metadata["id"])


source_doc_path = Path("../data/herzinsuffizienz.txt")
source_doc = open(source_doc_path, "r").read().strip()
_pages = re.split(r"Seite\s+(\d+)\n", source_doc)
page_dict = dict()
for i, _ in enumerate(_pages[:-1]):
    if i % 2:
        continue
    page_dict[_pages[i + 1]] = _pages[i]


for graph_doc in graph_documents:
    page = graph_doc.source.metadata["page"]
    graph_doc.source.metadata["page_nr"] = page
    graph_doc.source.metadata["page_content"] = page_dict[page]
    graph_doc.source.metadata.pop("page")

graph.add_graph_documents(graph_documents, include_source=True)
