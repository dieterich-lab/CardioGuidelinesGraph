from __future__ import annotations

import logging
import re
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
    fulltext_index_name: str = "snomed_term_text_idx"
    top_k: int = 40
    lexical_top_k: int = 80
    lexical_weight: float = 0.30
    vector_weight: float = 0.70
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

    @staticmethod
    def _extract_concept_id(node: Any) -> int | None:
        concept_id = None
        for concept_key in ("concept_id", "snomed_id", "conceptId", "id"):
            try:
                concept_id = node.get(concept_key)
            except Exception:
                concept_id = None
            if concept_id is not None:
                break
        if concept_id is None:
            return None
        try:
            return int(concept_id)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _extract_term(node: Any) -> str:
        for term_key in (
            "term",
            "preferred_term",
            "name",
            "label",
            "entity_standardized_candidate",
        ):
            try:
                candidate = node.get(term_key)
            except Exception:
                candidate = None
            if candidate:
                return str(candidate)
        return ""

    @staticmethod
    def _sanitize_fulltext_query(query_text: str) -> str:
        """Sanitize free text for Lucene query parser used by Neo4j fulltext index."""
        text = str(query_text or "").strip()
        if not text:
            return ""
        # Replace slash-like separators and other Lucene operators with spaces.
        text = text.replace("/", " ")
        text = text.replace("\\", " ")
        text = re.sub(r"\bAND\b|\bOR\b|\bNOT\b", " ", text, flags=re.IGNORECASE)
        # Remove remaining Lucene special characters that can trigger parser failures.
        text = re.sub(r"[+\-!(){}\[\]^\"~*?:|&]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def retrieve_vector(
        self, term: str, top_k: int | None = None
    ) -> List[Dict[str, Any]]:
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
                concept_id = self._extract_concept_id(node)
                if concept_id is None:
                    continue
                out.append(
                    {
                        "conceptid": concept_id,
                        "term": self._extract_term(node),
                        "vector_score": float(row.get("score") or 0.0),
                        "lexical_score": 0.0,
                    }
                )
            return out

    def retrieve_lexical(
        self, query_text: str, top_k: int | None = None
    ) -> List[Dict[str, Any]]:
        if not query_text:
            return []

        safe_query_text = self._sanitize_fulltext_query(query_text)
        if not safe_query_text:
            return []

        k = int(top_k or self.config.lexical_top_k)
        query = """
        CALL db.index.fulltext.queryNodes($index_name, $query_text, {limit: $k})
        YIELD node, score
        RETURN node, score
        """

        with self.driver.session() as session:
            rows = session.run(
                query,
                index_name=self.config.fulltext_index_name,
                query_text=safe_query_text,
                k=k,
            )

            out: List[Dict[str, Any]] = []
            for row in rows:
                node = row.get("node") or {}
                concept_id = self._extract_concept_id(node)
                if concept_id is None:
                    continue
                out.append(
                    {
                        "conceptid": concept_id,
                        "term": self._extract_term(node),
                        "vector_score": 0.0,
                        "lexical_score": float(row.get("score") or 0.0),
                    }
                )
            return out

    def retrieve(self, term: str, top_k: int | None = None) -> List[Dict[str, Any]]:
        """Hybrid retrieval combining vector and lexical channels by concept id."""
        if not term:
            return []

        vector_hits = self.retrieve_vector(term, top_k=top_k)
        lexical_hits = self.retrieve_lexical(term, top_k=self.config.lexical_top_k)

        merged: Dict[int, Dict[str, Any]] = {}
        for hit in vector_hits + lexical_hits:
            concept_id = int(hit["conceptid"])
            row = merged.setdefault(
                concept_id,
                {
                    "conceptid": concept_id,
                    "term": hit.get("term") or "",
                    "vector_score": 0.0,
                    "lexical_score": 0.0,
                    "hybrid_score": 0.0,
                },
            )
            if hit.get("term") and not row.get("term"):
                row["term"] = hit["term"]
            row["vector_score"] = max(
                float(row.get("vector_score") or 0.0),
                float(hit.get("vector_score") or 0.0),
            )
            row["lexical_score"] = max(
                float(row.get("lexical_score") or 0.0),
                float(hit.get("lexical_score") or 0.0),
            )

        if not merged:
            return []

        max_lexical = max(float(v["lexical_score"]) for v in merged.values())
        max_lexical = max(max_lexical, 1e-9)
        for row in merged.values():
            lexical_norm = float(row["lexical_score"]) / max_lexical
            row["hybrid_score"] = (
                self.config.vector_weight * float(row["vector_score"])
                + self.config.lexical_weight * lexical_norm
            )

        return sorted(
            merged.values(),
            key=lambda r: (
                float(r.get("hybrid_score") or 0.0),
                float(r.get("vector_score") or 0.0),
                float(r.get("lexical_score") or 0.0),
            ),
            reverse=True,
        )
