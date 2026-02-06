import requests
from neo4j import GraphDatabase
from typing import List, Optional
from dataclasses import dataclass

# custom Document class to mimic functions from langchains community, ollama and neo4j vector store
# used instead of importing langchain packages directly because of dependency issues


@dataclass
class Document:
    page_content: str
    metadata: dict


class Neo4jGraph:
    def __init__(self, uri, user, password, database="neo4j"):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.database = database

    def query(self, cypher: str, params: dict | None = None):
        with self.driver.session(database=self.database) as session:
            result = session.run(cypher, params or {})
            return [record.data() for record in result]

    def close(self):
        self.driver.close()


class Neo4jHybridVectorStore:
    def __init__(
        self,
        url: str,
        username: str,
        password: str,
        embedding,  # LangChain-style embedding object
        index_name: str,
        node_label: str,
        text_node_property: str,
        search_type: str = "hybrid",
        text_index: str = "node_text_index",
    ):
        self.driver = GraphDatabase.driver(url, auth=(username, password))
        self.embedding_model = embedding
        self.vector_index = index_name
        self.text_index = text_index
        self.node_label = node_label
        self.text_property = text_node_property
        self.search_type = search_type

    def get_relevant_documents(self, query: str):
        results = self.similarity_search_with_score(query, k=5)
        return [doc for doc, _ in results]

    def similarity_search_with_score(self, query: str, k: int = 5):
        # 1️⃣ Create embedding (LangChain-compatible)
        embedding: List[float] = self.embedding_model.embed_query(query)

        # 2️⃣ Hybrid or vector-only search
        if self.search_type == "hybrid":
            cypher = f"""
            CALL {{
                CALL db.index.vector.queryNodes(
                    $vector_index, $k, $embedding
                )
                YIELD node, score
                RETURN node, score * 0.7 AS score

                UNION ALL

                CALL db.index.fulltext.queryNodes(
                    $text_index, $query, {{limit: $k}}
                )
                YIELD node, score
                RETURN node, score * 0.3 AS score
            }}
            WITH node, sum(score) AS score
            RETURN node.{self.text_property} AS text, score
            ORDER BY score DESC
            LIMIT $k
            """
            params = {
                "vector_index": self.vector_index,
                "text_index": self.text_index,
                "embedding": embedding,
                "query": query,
                "k": k,
            }
        else:
            cypher = f"""
            CALL db.index.vector.queryNodes(
                $vector_index, $k, $embedding
            )
            YIELD node, score
            RETURN node.{self.text_property} AS text, score
            ORDER BY score DESC
            LIMIT $k
            """
            params = {
                "vector_index": self.vector_index,
                "embedding": embedding,
                "k": k,
            }

        # 3️⃣ Execute
        with self.driver.session() as session:
            result = session.run(cypher, params)
            return [
                (
                    Document(
                        page_content=r["text"],
                        metadata={"score": r["score"]},
                    ),
                    r["score"],
                )
                for r in result
            ]

    def close(self):
        self.driver.close()


class ChatOllama:
    def __init__(self, model: str, base_url: str = "http://localhost:11434"):
        if not base_url.startswith(("http://", "https://")):
            base_url = "http://" + base_url
        self.model = model
        self.base_url = base_url

    def invoke(self, messages: list[dict]) -> str:
        r = requests.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "messages": messages,
                "stream": False,
            },
            timeout=120,
        )
        r.raise_for_status()
        return r.json()["message"]["content"]


class OllamaEmbeddings:
    def __init__(
        self,
        model: str,
        base_url: str = "http://localhost:11434",
        timeout: int = 60,
    ):
        if not base_url.startswith(("http://", "https://")):
            base_url = "http://" + base_url

        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _embed(self, prompt: str) -> List[float]:
        r = requests.post(
            f"{self.base_url}/api/embeddings",
            json={
                "model": self.model,
                "prompt": prompt,
            },
            timeout=self.timeout,
        )
        r.raise_for_status()
        return r.json()["embedding"]

    def embed_query(self, text: str) -> List[float]:
        return self._embed(text)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._embed(text) for text in texts]


class SimpleRetrievalQA:
    """
    Exact behavioral replacement for:
    RetrievalQA.from_chain_type(
        llm=chat,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
    )
    """

    def __init__(self, *, llm, retriever):
        self.llm = llm
        self.retriever = retriever

    def invoke(self, inputs: dict) -> dict:
        # LangChain-compatible entrypoint
        return self.__call__(inputs)

    def __call__(self, inputs: dict) -> dict:
        """
        Expects:
            {"query": "<question>"}

        Returns:
            {
                "result": "<answer>",
                "source_documents": [Document, ...]
            }
        """
        question = inputs["query"]

        # 1) Retrieve documents
        documents = self.retriever.get_relevant_documents(question)

        # 2) Stuff documents (LangChain behavior)
        context = "\n\n".join(doc.page_content for doc in documents)

        # 3) Prompt (semantic equivalent of RetrievalQA)
        prompt = f"""Use the following context to answer the question.
If you do not know the answer based on the context, say so.

Context:
{context}

Question:
{question}

Answer:"""

        # 4) Call LLM
        answer = self.llm.invoke(
            [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ]
        )

        return {
            "result": answer,
            "source_documents": documents,
        }
