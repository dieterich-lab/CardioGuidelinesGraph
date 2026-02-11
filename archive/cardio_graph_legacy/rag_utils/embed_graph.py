import time, ollama
from neo4j import GraphDatabase
from neo4j_graphrag.embeddings.ollama import OllamaEmbeddings
from neo4j_graphrag.retrievers import VectorRetriever, HybridRetriever
from neo4j_graphrag.generation import GraphRAG
from neo4j_graphrag.llm import OllamaLLM
from neo4j_graphrag.indexes import create_vector_index

URI = "bolt://neo4j-dev2.internal:7687"
AUTH = ("neo4j", "KWCeoHhkJYAiFa3XTZZZLC77bHiZ5xzj")
# ollama_host = "10.250.135.143:11430"
INDEX_NAME = "ixname"
ollama_host_ip = "10.250.135.153:11430"
DIMENSION = 1536


class SimpleOllamaEmbedder:
    def __init__(self, model: str, host: str):
        # host must include scheme for Client()
        if not host.startswith("http://") and not host.startswith("https://"):
            host = f"http://{host}"
        self.model = model
        self.client = ollama.Client(host=host)

    def embed_query(self, text: str, **kwargs):
        # 0.1.9 client uses .embeddings(..., prompt=...)
        resp = self.client.embeddings(model=self.model, prompt=text, **kwargs)

        # Handle both old/new response shapes
        if isinstance(resp, dict):
            vec = resp.get("embedding")
            if vec is None:
                embs = resp.get("embeddings") or []
                vec = embs[0] if embs else None
        else:
            vec = getattr(resp, "embedding", None)
            if vec is None:
                embs = getattr(resp, "embeddings", [])
                vec = embs[0] if embs else None

        if not isinstance(vec, list):
            raise RuntimeError(
                "Failed to retrieve embedding vector from Ollama response."
            )
        return vec


def embed_neo4j_graph(URI, AUTH, ollama_host_ip, DIMENSION, INDEX_NAME):
    """
    Embeds all nodes with the Label Node in the Neo4j graph that do not have an embedding yet.
    """
    start = time.time()
    print("starting embedding process...")
    driver = GraphDatabase.driver(URI, auth=AUTH)
    embedder = SimpleOllamaEmbedder(
        model="mxbai-embed-large:latest", host=ollama_host_ip
    )
    print("Ollama embedder initialized.", time.time() - start)
    # Assume embedder is properly configured to produce 1536-dim vectors
    with driver.session() as session:
        result = session.run(
            """
        MATCH (n)
        WHERE n:Node OR n:NODE OR n:AND
        WITH n
        WHERE n.embedding IS NULL
        RETURN elementId(n) AS id, n.value AS value
        """
        )
        results_list = list(result)
        print(f"Found {len(results_list)} nodes to embed.", time.time() - start)
        total = len(results_list)
        for i, record in enumerate(results_list, 1):
            node_id = record["id"]
            text = record["value"]
            print(f"Embedding node ID {node_id} with value: {text}")
            begin_embed_time = time.time()
            vec = embedder.embed_query(text)
            session.run(
                """
            MATCH (n)
            WHERE elementId(n) = $id
            SET n.embedding = $vec
            """,
                {"id": node_id, "vec": vec},
            )
            print(f"\rProgress: {i}/{total} ({i/total*100:.1f}%)", end=" ")
            print(
                f"Node ID {node_id} embedded in {time.time() - begin_embed_time} seconds."
            )
    print("query complete, creating vector index...", time.time() - start)
    create_vector_index(
        driver,
        INDEX_NAME,
        label="Node",
        embedding_property="embedding",
        dimensions=DIMENSION,
        similarity_fn="euclidean",
    )
    print(f"Vector index '{INDEX_NAME}' created successfully.", time.time() - start)


def test_hybrid_search(URI, AUTH, ollama_host_ip, INDEX_NAME):
    driver = GraphDatabase.driver(URI, auth=AUTH)
    embedder = OllamaEmbeddings(model="mxbai-embed-large:335m", host=ollama_host_ip)
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
    # retriever_result = retriever.search(query_text=query_text, top_k=3)
    llm = OllamaLLM(model_name="qwen3:latest", host=ollama_host_ip)
    rag = GraphRAG(retriever=retriever, llm=llm)

    # response = rag.search(query_text=query_text, retriever_config={"top_k": 5})
    # print(response.answer)

    results = retriever.search(query_text=query_text, top_k=3)
    print(results)


if __name__ == "__main__":
    embed_neo4j_graph(
        URI="bolt://neo4j-dev3.internal:7687",
        AUTH=("neo4j", "KWCeoHhkJYAiFa3XTZZZLC77bHiZ5xzj"),
        ollama_host_ip="10.250.135.153:11430",
        DIMENSION=1024,
        INDEX_NAME="embed_dev1",
    )
