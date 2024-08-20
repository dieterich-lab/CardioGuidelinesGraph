import os
import pickle

from graph_utils import MyNeo4jGraph

# from langchain_community.graphs import Neo4jGraph

# task = "ppi"
task = "trans"

task_dict = {"ppi": "linda-llm", "trans": "linda-llm-dev"}

os.environ["NEO4J_URI"] = f"bolt+s://{task_dict[task]}.dieterichlab.org:7687"
os.environ["NEO4J_USERNAME"] = "neo4j"
os.environ["NEO4J_PASSWORD"] = "KWCeoHhkJYAiFa3XTZZZLC77bHiZ5xzj"

# graph = Neo4jGraph()
print(f"Connecting to {os.environ['NEO4J_URI']}")
graph = MyNeo4jGraph()

graph.query(
    """
	MATCH (n)
	DETACH DELETE n
	"""
)

graph_documents = list()
graphdoc_pkl_path = (
    f"/home/pwiesenbach/LINDA_LLM/outputs/graph_docs/{task}_graph_documents.pkl"
)
print(f"loading from {graphdoc_pkl_path}")
with open(graphdoc_pkl_path, "rb") as f:
    while 1:
        try:
            graph_documents.append(pickle.load(f))
        except EOFError:
            break

print(len(graph_documents))


for d in graph_documents:
    d.source.metadata["id"] = str(d.source.metadata["id"])

graph.add_graph_documents(graph_documents, include_source=True)
