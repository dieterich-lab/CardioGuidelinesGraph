import os
import pickle

from cardio_graph_core.legacy_graph_pipeline.graph_utils import MyNeo4jGraph

# from langchain_community.graphs import Neo4jGraph


os.environ["NEO4J_URI"] = f"bolt+s://neo4j-dev1.dieterichlab.org:7687"
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

task = "guidelines"

graph_documents = list()

graphdoc_pkl_path = f"../outputs/{task}_graph_documents.pkl"
print(f"loading from {graphdoc_pkl_path}")
with open(graphdoc_pkl_path, "rb") as f:
    while 1:
        try:
            graph_documents.append(pickle.load(f))
        except EOFError:
            break

print(len(graph_documents))

graph.add_graph_documents(graph_documents, include_source=True)

print("Finish.")
