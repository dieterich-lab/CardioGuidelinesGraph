from neo4j import GraphDatabase
from neo4j_graphrag.embeddings.ollama import OllamaEmbeddings
from neo4j_graphrag.retrievers import VectorRetriever, HybridRetriever
from neo4j_graphrag.generation import GraphRAG
from neo4j_graphrag.llm import OllamaLLM
from neo4j_graphrag.indexes import create_vector_index

URI = "bolt://neo4j-dev2.internal:7687"
AUTH = ("neo4j", "KWCeoHhkJYAiFa3XTZZZLC77bHiZ5xzj")
#ollama_host = "10.250.135.143:11430"
INDEX_NAME = "ixname"
ollama_host_llm = "10.250.135.153:11430"
DIMENSION=1536

driver = GraphDatabase.driver(URI, auth=AUTH)
embedder = OllamaEmbeddings(model="mxbai-embed-large:335m", host = ollama_host_llm)

# Assume embedder is properly configured to produce 1536-dim vectors
with driver.session() as session:
    result = session.run("""
    MATCH (n:Node)
    WHERE NOT exists(n.embedding)
    RETURN id(n) AS id, n.value AS value
    """)
    for record in result:
        node_id = record["id"]
        text = record["value"]
        vec = embedder.embed_query(text)
        session.run("""
        MATCH (n)
        WHERE id(n) = $id
        SET n.embedding = $vec
        """, {"id": node_id, "vec": vec})


create_vector_index(
    driver,
    INDEX_NAME,
    label="Node",
    embedding_property="embedding",
    dimensions=DIMENSION,
    similarity_fn="euclidean",
)


print(f"Vector index '{INDEX_NAME}' created successfully.")

vec = embedder.embed_query("angina pectoris")
print(len(vec))


# retriever = VectorRetriever(
#     driver,
#     index_name=INDEX_NAME,
#     embedder=embedder,
#     return_properties=["value"],
# )

retriever = HybridRetriever(
    driver,
    vector_index_name=INDEX_NAME,
    fulltext_index_name="value",
    embedder=embedder,
    return_properties=["value"],
)

query_text = "What can you tell me about angina-health?"
#retriever_result = retriever.search(query_text=query_text, top_k=3)
llm = OllamaLLM(model_name="qwen3:latest", host=ollama_host_llm)
rag = GraphRAG(retriever=retriever, llm=llm)

# response = rag.search(query_text=query_text, retriever_config={"top_k": 5})
# print(response.answer)

results = retriever.search(query_text=query_text, top_k=3)
print(results)

