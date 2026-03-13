from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List

import requests
from neo4j import GraphDatabase

from cardio_graph_core.extraction.clients import ollama_models

logger = logging.getLogger("GuidelineGraphBuilder")


@dataclass
class VectorRetrieverConfig:
    uri: str
    user: str
    password: str
    index_name: str
    embedding_url: str
    embedding_model: str
    top_k: int = 40
    timeout_seconds: int = 20


class Neo4jVectorCandidateRetriever:
    def __init__(self, config: VectorRetrieverConfig):
        self.config = config
        self.driver = GraphDatabase.driver(
            self.config.uri,
            auth=(self.config.user, self.config.password),
        )

    def close(self) -> None:
        try:
            self.driver.close()
        except Exception:
            pass

    def _embed(self, text: str) -> List[float]:
        model_name = ollama_models.get(
            self.config.embedding_model, self.config.embedding_model
        )
        payload = {
            "model": model_name,
            "prompt": text,
        }
        response = requests.post(
            f"{self.config.embedding_url.rstrip('/')}/api/embeddings",
            json=payload,
            timeout=self.config.timeout_seconds,
        )
        response.raise_for_status()
        body = response.json()
        embedding = body.get("embedding")
        if not isinstance(embedding, list) or not embedding:
            raise ValueError("Missing or invalid embedding payload from Ollama")
        return embedding

    def retrieve(self, term: str, top_k: int | None = None) -> List[Dict[str, Any]]:
        if not term:
            return []

        k = int(top_k or self.config.top_k)
        embedding = self._embed(term)

        query = """
        CALL db.index.vector.queryNodes($index_name, $k, $embedding)
        YIELD node, score
        RETURN node, score
        """

        with self.driver.session() as session:
            rows = session.run(
                query,
                index_name=self.config.index_name,
                k=k,
                embedding=embedding,
            )

            out: List[Dict[str, Any]] = []
            for row in rows:
                node = row.get("node") or {}
                concept_id = None
                for concept_key in ("concept_id", "snomed_id", "conceptId", "id"):
                    try:
                        concept_id = node.get(concept_key)
                    except Exception:
                        concept_id = None
                    if concept_id is not None:
                        break
                if concept_id is None:
                    continue
                try:
                    concept_id = int(concept_id)
                except (TypeError, ValueError):
                    continue

                term_value = ""
                for term_key in ("term", "preferred_term", "name", "label"):
                    try:
                        candidate = node.get(term_key)
                    except Exception:
                        candidate = None
                    if candidate:
                        term_value = str(candidate)
                        break

                out.append(
                    {
                        "conceptid": concept_id,
                        "term": term_value,
                        "vector_score": float(row.get("score") or 0.0),
                    }
                )
            return out
