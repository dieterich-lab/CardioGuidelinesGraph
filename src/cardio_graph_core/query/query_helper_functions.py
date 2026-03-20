from __future__ import annotations
from typing import Any, Dict, List, Optional
from neo4j import GraphDatabase
from collections import defaultdict
import time, ollama, re
from cardio_graph_core.query.langchain_replacement import SimpleOllamaEmbedder

from neo4j import GraphDatabase
from neo4j_graphrag.embeddings.ollama import OllamaEmbeddings
from neo4j_graphrag.retrievers import VectorRetriever, HybridRetriever
from neo4j_graphrag.generation import GraphRAG
from neo4j_graphrag.llm import OllamaLLM
from neo4j_graphrag.indexes import create_vector_index


def entities_to_list(entities):
    list = []
    for i, t in enumerate(entities.entities, 1):
        list.append(t.entity)
    return list


# ollama_host = "10.250.135.143:11430"


def create_concept_fulltext_index(
    driver,
    index_name: str = "concept_entity_lexical_idx",
    label: str = "Concept",
    properties: Optional[List[str]] = None,
) -> None:
    """
    Create a Neo4j fulltext index over Concept string properties.

    Default:
        - entity_original
        - entity_standardized_candidate
    """
    if properties is None:
        properties = ["entity_original", "entity_standardized_candidate"]

    if not properties:
        raise ValueError("properties must contain at least one property name")

    prop_list = ", ".join(f"n.{p}" for p in properties)

    query = f"""
    CREATE FULLTEXT INDEX {index_name} IF NOT EXISTS
    FOR (n:{label})
    ON EACH [{prop_list}]
    """

    with driver.session() as session:
        session.run(query)


def create_concept_vector_index(
    driver,
    index_name: str = "concept_entity_vector_idx",
    label: str = "Concept",
    embedding_property: str = "embedding_entity_standardized",
    dimensions: int = 1024,
    similarity_fn: str = "cosine",
) -> None:
    """
    Create a Neo4j vector index on Concept embeddings.
    """
    if similarity_fn not in {"cosine", "euclidean"}:
        raise ValueError("similarity_fn must be 'cosine' or 'euclidean'")

    query = f"""
    CREATE VECTOR INDEX {index_name} IF NOT EXISTS
    FOR (n:{label})
    ON (n.{embedding_property})
    OPTIONS {{
      indexConfig: {{
        `vector.dimensions`: {dimensions},
        `vector.similarity_function`: '{similarity_fn}'
      }}
    }}
    """

    with driver.session() as session:
        session.run(query)


def embed_concepts_and_create_indexes(
    uri: str,
    auth: tuple[str, str],
    embedder,
    *,
    dimensions: int = 1024,
    label: str = "Concept",
    source_property: str = "entity_standardized_candidate",
    embedding_property: str = "embedding_entity_standardized",
    fulltext_index_name: str = "concept_entity_lexical_idx",
    vector_index_name: str = "concept_entity_vector_idx",
    similarity_fn: str = "cosine",
) -> None:
    """
    1. Embed all Concept nodes that do not yet have an embedding.
    2. Create a fulltext index on entity_original + entity_standardized_candidate.
    3. Create a vector index on embedding_property.

    By default, embeddings are built from entity_standardized_candidate.
    """
    driver = GraphDatabase.driver(uri, auth=auth)

    try:
        with driver.session() as session:
            result = session.run(
                f"""
                MATCH (n:{label})
                WHERE n.{source_property} IS NOT NULL
                  AND n.{embedding_property} IS NULL
                RETURN elementId(n) AS id,
                       n.snomed_id AS snomed_id,
                       n.{source_property} AS text
                """
            )
            rows = list(result)

            print(f"Found {len(rows)} {label} nodes to embed.")

            for i, row in enumerate(rows, start=1):
                node_id = row["id"]
                snomed_id = row["snomed_id"]
                text = row["text"]

                if not text or not str(text).strip():
                    continue

                vec = embedder.embed_query(text)

                session.run(
                    f"""
                    MATCH (n:{label})
                    WHERE elementId(n) = $id
                    SET n.{embedding_property} = $vec
                    """,
                    {"id": node_id, "vec": vec},
                )

                print(f"Embedded {i}/{len(rows)}: snomed_id={snomed_id}, text={text}")

        create_concept_fulltext_index(
            driver=driver,
            index_name=fulltext_index_name,
            label=label,
            properties=["entity_original", "entity_standardized_candidate"],
        )

        create_concept_vector_index(
            driver=driver,
            index_name=vector_index_name,
            label=label,
            embedding_property=embedding_property,
            dimensions=dimensions,
            similarity_fn=similarity_fn,
        )

        print("Concept embedding + index creation complete.")

    finally:
        driver.close()


def hybrid_search_concepts(
    driver,
    embedder,
    query_text: str,
    *,
    vector_index_name: str = "concept_entity_vector_idx",
    fulltext_index_name: str = "concept_entity_lexical_idx",
    top_k_vector: int = 15,
    top_k_fulltext: int = 15,
    min_vector_score: float = 0.70,
    min_fulltext_score: float = 0.0,
    final_limit: int = 20,
):
    query_embedding = embedder.embed_query(query_text)

    cypher = """
    CALL {
        CALL db.index.fulltext.queryNodes($fulltext_index_name, $query_text)
        YIELD node, score
        WHERE score >= $min_fulltext_score
        RETURN
            coalesce(node.snomed_id, elementId(node)) AS cid,
            node,
            score AS lexical_score,
            null AS vector_score
        LIMIT $top_k_fulltext

        UNION

        CALL db.index.vector.queryNodes($vector_index_name, $top_k_vector, $query_embedding)
        YIELD node, score
        WHERE score >= $min_vector_score
        RETURN
            coalesce(node.snomed_id, elementId(node)) AS cid,
            node,
            null AS lexical_score,
            score AS vector_score
    }
    WITH cid, node,
         max(lexical_score) AS lexical_score,
         max(vector_score) AS vector_score
    WITH cid, node, lexical_score, vector_score,
         CASE
             WHEN lexical_score IS NOT NULL AND vector_score IS NOT NULL THEN "both"
             WHEN lexical_score IS NOT NULL THEN "lexical"
             ELSE "vector"
         END AS hit_source
    RETURN
        cid,
        node.snomed_id AS snomed_id,
        node.entity AS entity,
        node.entity_original AS entity_original,
        node.entity_standardized_candidate AS entity_standardized_candidate,
        node.preferred_term AS preferred_term,
        node.name AS name,
        node.target_label AS target_label,
        labels(node) AS labels,
        lexical_score,
        vector_score,
        hit_source
    ORDER BY
        CASE hit_source
            WHEN "both" THEN 0
            WHEN "lexical" THEN 1
            ELSE 2
        END,
        lexical_score DESC,
        vector_score DESC
    LIMIT $final_limit
    """

    with driver.session() as session:
        result = session.run(
            cypher,
            {
                "query_text": query_text,
                "query_embedding": query_embedding,
                "vector_index_name": vector_index_name,
                "fulltext_index_name": fulltext_index_name,
                "top_k_vector": top_k_vector,
                "top_k_fulltext": top_k_fulltext,
                "min_vector_score": min_vector_score,
                "min_fulltext_score": min_fulltext_score,
                "final_limit": final_limit,
            },
        )
        return [dict(record) for record in result]


def pretty_print_concept_hits(results, max_text_len=120, show_rank=True):
    """
    Pretty-print results returned by hybrid_search_concepts().

    Expected input:
        results = [
            {
                'cid': ...,
                'snomed_id': ...,
                'entity': ...,
                'entity_original': ...,
                'entity_standardized_candidate': ...,
                'preferred_term': ...,
                'name': ...,
                'target_label': ...,
                'labels': [...],
                'lexical_score': ...,
                'vector_score': ...,
                'hit_source': 'lexical' | 'vector' | 'both'
            },
            ...
        ]
    """
    if not results:
        print("No results found.")
        return

    def _fmt_text(value):
        if value is None:
            return "-"
        value = str(value).strip()
        if not value:
            return "-"
        if len(value) > max_text_len:
            return value[: max_text_len - 3] + "..."
        return value

    def _fmt_score(value):
        if value is None:
            return "-"
        try:
            return f"{float(value):.4f}"
        except (TypeError, ValueError):
            return str(value)

    for i, hit in enumerate(results, start=1):
        rank_prefix = f"[{i}] " if show_rank else ""
        print("=" * 80)
        print(
            f"{rank_prefix}{_fmt_text(hit.get('entity_standardized_candidate') or hit.get('entity'))}"
        )
        print("-" * 80)
        print(f"SNOMED ID      : {_fmt_text(hit.get('snomed_id'))}")
        print(f"Entity         : {_fmt_text(hit.get('entity'))}")
        print(f"Original       : {_fmt_text(hit.get('entity_original'))}")
        print(f"Standardized   : {_fmt_text(hit.get('entity_standardized_candidate'))}")
        print(f"Preferred term : {_fmt_text(hit.get('preferred_term'))}")
        print(f"Name           : {_fmt_text(hit.get('name'))}")
        print(f"Target label   : {_fmt_text(hit.get('target_label'))}")
        print(f"Labels         : {_fmt_text(', '.join(hit.get('labels', [])))}")
        print(f"Hit source     : {_fmt_text(hit.get('hit_source'))}")
        print(f"Lexical score  : {_fmt_score(hit.get('lexical_score'))}")
        print(f"Vector score   : {_fmt_score(hit.get('vector_score'))}")
    print("=" * 80)
    print(f"Total hits: {len(results)}")


def create_decisionnode_fulltext_index(
    driver,
    index_name: str = "decisionnode_entity_lexical_idx",
    label: str = "DecisionNode",
    properties: Optional[List[str]] = None,
) -> None:
    """
    Create a Neo4j fulltext index over DecisionNode string properties.

    Default:
        - entity_original
        - entity_standardized_candidate
    """
    if properties is None:
        properties = ["entity_original", "entity_standardized_candidate"]

    if not properties:
        raise ValueError("properties must contain at least one property name")

    prop_list = ", ".join(f"n.{p}" for p in properties)

    query = f"""
    CREATE FULLTEXT INDEX {index_name} IF NOT EXISTS
    FOR (n:{label})
    ON EACH [{prop_list}]
    """

    with driver.session() as session:
        session.run(query)


def create_decisionnode_vector_index(
    driver,
    index_name: str = "decisionnode_entity_vector_idx",
    label: str = "DecisionNode",
    embedding_property: str = "embedding_entity_standardized",
    dimensions: int = 1024,
    similarity_fn: str = "cosine",
) -> None:
    """
    Create a Neo4j vector index on DecisionNode embeddings.
    """
    if similarity_fn not in {"cosine", "euclidean"}:
        raise ValueError("similarity_fn must be 'cosine' or 'euclidean'")

    query = f"""
    CREATE VECTOR INDEX {index_name} IF NOT EXISTS
    FOR (n:{label})
    ON (n.{embedding_property})
    OPTIONS {{
      indexConfig: {{
        `vector.dimensions`: {dimensions},
        `vector.similarity_function`: '{similarity_fn}'
      }}
    }}
    """

    with driver.session() as session:
        session.run(query)


def embed_decisionnodes_and_create_indexes(
    uri: str,
    auth: tuple[str, str],
    embedder,
    *,
    dimensions: int = 1024,
    label: str = "DecisionNode",
    source_property: str = "entity_standardized_candidate",
    embedding_property: str = "embedding_entity_standardized",
    fulltext_index_name: str = "decisionnode_entity_lexical_idx",
    vector_index_name: str = "decisionnode_entity_vector_idx",
    similarity_fn: str = "cosine",
) -> None:
    """
    1. Embed all DecisionNode nodes that do not yet have an embedding.
    2. Create a fulltext index on entity_original + entity_standardized_candidate.
    3. Create a vector index on embedding_property.

    By default, embeddings are built from entity_standardized_candidate.
    """
    driver = GraphDatabase.driver(uri, auth=auth)

    try:
        with driver.session() as session:
            result = session.run(
                f"""
                MATCH (n:{label})
                WHERE n.{source_property} IS NOT NULL
                  AND n.{embedding_property} IS NULL
                RETURN elementId(n) AS id,
                       n.rule_unique_id AS rule_unique_id,
                       n.decision_id AS decision_id,
                       n.{source_property} AS text
                """
            )
            rows = list(result)

            print(f"Found {len(rows)} {label} nodes to embed.")

            for i, row in enumerate(rows, start=1):
                node_id = row["id"]
                rule_unique_id = row["rule_unique_id"]
                decision_id = row["decision_id"]
                text = row["text"]

                if not text or not str(text).strip():
                    continue

                vec = embedder.embed_query(text)

                session.run(
                    f"""
                    MATCH (n:{label})
                    WHERE elementId(n) = $id
                    SET n.{embedding_property} = $vec
                    """,
                    {"id": node_id, "vec": vec},
                )

                print(
                    f"Embedded {i}/{len(rows)}: "
                    f"rule={rule_unique_id}, decision={decision_id}, text={text}"
                )

        create_decisionnode_fulltext_index(
            driver=driver,
            index_name=fulltext_index_name,
            label=label,
            properties=["entity_original", "entity_standardized_candidate"],
        )

        create_decisionnode_vector_index(
            driver=driver,
            index_name=vector_index_name,
            label=label,
            embedding_property=embedding_property,
            dimensions=dimensions,
            similarity_fn=similarity_fn,
        )

        print("DecisionNode embedding + index creation complete.")

    finally:
        driver.close()


def hybrid_search_decisionnodes(
    driver,
    embedder,
    query_text: str,
    *,
    vector_index_name: str = "decisionnode_entity_vector_idx",
    fulltext_index_name: str = "decisionnode_entity_lexical_idx",
    top_k_vector: int = 15,
    top_k_fulltext: int = 15,
    min_vector_score: float = 0.70,
    min_fulltext_score: float = 0.0,
    final_limit: int = 20,
) -> List[Dict[str, Any]]:
    """
    Hybrid search over DecisionNode using:
      - lexical search on entity_original + entity_standardized_candidate
      - vector search on embedding_entity_standardized

    Returns deduplicated DecisionNode hits.
    """
    query_embedding = embedder.embed_query(query_text)

    cypher = """
    CALL {
        CALL db.index.fulltext.queryNodes($fulltext_index_name, $query_text)
        YIELD node, score
        WHERE score >= $min_fulltext_score
        RETURN
            coalesce(node.decision_id, elementId(node)) AS did,
            node,
            score AS lexical_score,
            null AS vector_score
        LIMIT $top_k_fulltext

        UNION

        CALL db.index.vector.queryNodes($vector_index_name, $top_k_vector, $query_embedding)
        YIELD node, score
        WHERE score >= $min_vector_score
        RETURN
            coalesce(node.decision_id, elementId(node)) AS did,
            node,
            null AS lexical_score,
            score AS vector_score
    }
    WITH did, node,
         max(lexical_score) AS lexical_score,
         max(vector_score) AS vector_score
    WITH did, node, lexical_score, vector_score,
         CASE
             WHEN lexical_score IS NOT NULL AND vector_score IS NOT NULL THEN "both"
             WHEN lexical_score IS NOT NULL THEN "lexical"
             ELSE "vector"
         END AS hit_source
    RETURN
        did,
        node.rule_unique_id AS rule_unique_id,
        node.decision_id AS decision_id,
        node.entity AS entity,
        node.entity_original AS entity_original,
        node.entity_standardized_candidate AS entity_standardized_candidate,
        node.question AS question,
        node.context AS context,
        node.operator AS operator,
        node.threshold AS threshold,
        node.unit AS unit,
        node.logic_type AS logic_type,
        labels(node) AS labels,
        lexical_score,
        vector_score,
        hit_source
    ORDER BY
        CASE hit_source
            WHEN "both" THEN 0
            WHEN "lexical" THEN 1
            ELSE 2
        END,
        lexical_score DESC,
        vector_score DESC
    LIMIT $final_limit
    """

    with driver.session() as session:
        result = session.run(
            cypher,
            {
                "query_text": query_text,
                "query_embedding": query_embedding,
                "vector_index_name": vector_index_name,
                "fulltext_index_name": fulltext_index_name,
                "top_k_vector": top_k_vector,
                "top_k_fulltext": top_k_fulltext,
                "min_vector_score": min_vector_score,
                "min_fulltext_score": min_fulltext_score,
                "final_limit": final_limit,
            },
        )
        return [dict(record) for record in result]


def pretty_print_decisionnode_hits(results, max_text_len=140, show_rank=True):
    """
    Pretty-print results returned by hybrid_search_decisionnodes().
    """
    if not results:
        print("No results found.")
        return

    def _fmt_text(value):
        if value is None:
            return "-"
        value = str(value).strip()
        if not value:
            return "-"
        if len(value) > max_text_len:
            return value[: max_text_len - 3] + "..."
        return value

    def _fmt_score(value):
        if value is None:
            return "-"
        try:
            return f"{float(value):.4f}"
        except (TypeError, ValueError):
            return str(value)

    for i, hit in enumerate(results, start=1):
        rank_prefix = f"[{i}] " if show_rank else ""
        print("=" * 100)
        print(
            f"{rank_prefix}{_fmt_text(hit.get('entity_standardized_candidate') or hit.get('entity') or hit.get('question'))}"
        )
        print("-" * 100)
        print(f"Rule ID         : {_fmt_text(hit.get('rule_unique_id'))}")
        print(f"Decision ID     : {_fmt_text(hit.get('decision_id'))}")
        print(f"Question        : {_fmt_text(hit.get('question'))}")
        print(f"Entity          : {_fmt_text(hit.get('entity'))}")
        print(f"Original        : {_fmt_text(hit.get('entity_original'))}")
        print(
            f"Standardized    : {_fmt_text(hit.get('entity_standardized_candidate'))}"
        )
        print(f"Context         : {_fmt_text(hit.get('context'))}")
        print(f"Operator        : {_fmt_text(hit.get('operator'))}")
        print(f"Threshold       : {_fmt_text(hit.get('threshold'))}")
        print(f"Unit            : {_fmt_text(hit.get('unit'))}")
        print(f"Logic type      : {_fmt_text(hit.get('logic_type'))}")
        print(f"Labels          : {_fmt_text(', '.join(hit.get('labels', [])))}")
        print(f"Hit source      : {_fmt_text(hit.get('hit_source'))}")
        print(f"Lexical score   : {_fmt_score(hit.get('lexical_score'))}")
        print(f"Vector score    : {_fmt_score(hit.get('vector_score'))}")
    print("=" * 100)
    print(f"Total hits: {len(results)}")


def collapse_decisionnode_hits(results):
    """
    Collapse DecisionNode hits only by entity_standardized_candidate.

    This preserves all rule_ids and decision_ids, but groups everything under
    the same standardized entity together.
    """
    grouped = {}

    for hit in results:
        key = hit.get("entity_standardized_candidate")

        if key is None:
            key = hit.get("entity")

        if key not in grouped:
            grouped[key] = {
                "entity": hit.get("entity"),
                "entity_original_examples": set(),
                "entity_standardized_candidate": hit.get(
                    "entity_standardized_candidate"
                ),
                "questions": set(),
                "contexts": set(),
                "operators": set(),
                "thresholds": set(),
                "units": set(),
                "logic_types": set(),
                "hit_sources": set(),
                "labels_examples": set(hit.get("labels", [])),
                "max_lexical_score": None,
                "max_vector_score": None,
                "decision_ids": [],
                "rule_ids": [],
                "raw_hits": [],
            }

        g = grouped[key]

        if hit.get("entity_original") is not None:
            g["entity_original_examples"].add(hit.get("entity_original"))

        if hit.get("question") is not None:
            g["questions"].add(hit.get("question"))

        if hit.get("context") is not None:
            g["contexts"].add(hit.get("context"))

        if hit.get("operator") is not None:
            g["operators"].add(hit.get("operator"))

        if hit.get("threshold") is not None:
            g["thresholds"].add(hit.get("threshold"))

        if hit.get("unit") is not None:
            g["units"].add(hit.get("unit"))

        if hit.get("logic_type") is not None:
            g["logic_types"].add(hit.get("logic_type"))

        if hit.get("hit_source") is not None:
            g["hit_sources"].add(hit.get("hit_source"))

        lex = hit.get("lexical_score")
        vec = hit.get("vector_score")

        if lex is not None:
            if g["max_lexical_score"] is None or lex > g["max_lexical_score"]:
                g["max_lexical_score"] = lex

        if vec is not None:
            if g["max_vector_score"] is None or vec > g["max_vector_score"]:
                g["max_vector_score"] = vec

        if hit.get("decision_id") not in g["decision_ids"]:
            g["decision_ids"].append(hit.get("decision_id"))

        if hit.get("rule_unique_id") not in g["rule_ids"]:
            g["rule_ids"].append(hit.get("rule_unique_id"))

        g["raw_hits"].append(hit)

    collapsed = []
    for group in grouped.values():
        group["entity_original_examples"] = sorted(group["entity_original_examples"])
        group["questions"] = sorted(group["questions"])
        group["contexts"] = sorted(group["contexts"])
        group["operators"] = sorted(group["operators"])
        group["thresholds"] = sorted(group["thresholds"], key=lambda x: str(x))
        group["units"] = sorted(group["units"])
        group["logic_types"] = sorted(group["logic_types"])
        group["hit_sources"] = sorted(group["hit_sources"])
        group["rule_count"] = len(group["rule_ids"])
        group["decision_count"] = len(group["decision_ids"])
        collapsed.append(group)

    collapsed.sort(
        key=lambda x: (
            -(x["max_lexical_score"] if x["max_lexical_score"] is not None else -1),
            -(x["max_vector_score"] if x["max_vector_score"] is not None else -1),
            -x["rule_count"],
        )
    )

    return collapsed


def pretty_print_collapsed(collapsed, max_ids=10, max_examples=10):
    if not collapsed:
        print("No collapsed hits found.")
        return

    for i, hit in enumerate(collapsed, start=1):
        print("=" * 100)
        print(f"[{i}] {hit.get('entity_standardized_candidate') or '-'}")
        print("-" * 100)
        print(f"Entity                : {hit.get('entity') or '-'}")
        print(
            f"Original examples     : {', '.join(hit.get('entity_original_examples', [])[:max_examples]) or '-'}"
        )
        print(
            f"Questions             : {', '.join(hit.get('questions', [])[:max_examples]) or '-'}"
        )
        print(
            f"Contexts              : {', '.join(hit.get('contexts', [])[:max_examples]) or '-'}"
        )
        print(f"Operators             : {', '.join(hit.get('operators', [])) or '-'}")
        print(
            f"Thresholds            : {', '.join(map(str, hit.get('thresholds', []))) or '-'}"
        )
        print(f"Units                 : {', '.join(hit.get('units', [])) or '-'}")
        print(f"Logic types           : {', '.join(hit.get('logic_types', [])) or '-'}")
        print(f"Hit sources           : {', '.join(hit.get('hit_sources', [])) or '-'}")
        print(
            f"Max lexical score     : {hit.get('max_lexical_score') if hit.get('max_lexical_score') is not None else '-'}"
        )
        print(
            f"Max vector score      : {hit.get('max_vector_score') if hit.get('max_vector_score') is not None else '-'}"
        )
        print(f"Rule count            : {hit.get('rule_count')}")
        print(f"Decision count        : {hit.get('decision_count')}")

        print("Rule IDs:")
        for rid in hit.get("rule_ids", [])[:max_ids]:
            print(f"  - {rid}")
        if len(hit.get("rule_ids", [])) > max_ids:
            print(f"  ... (+{len(hit['rule_ids']) - max_ids} more)")

        print("Decision IDs:")
        for did in hit.get("decision_ids", [])[:max_ids]:
            print(f"  - {did}")
        if len(hit.get("decision_ids", [])) > max_ids:
            print(f"  ... (+{len(hit['decision_ids']) - max_ids} more)")

    print("=" * 100)
    print(f"Total standardized groups: {len(collapsed)}")


def _norm_text(s: str) -> str:
    if s is None:
        return ""
    s = str(s).strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s


def filter_grounded_groups(query_text, collapsed_groups, min_vector_score=0.82):
    """
    Filter collapsed DecisionNode groups for concept grounding.

    Strategy:
    1. exact lexical match on entity_original_examples / entity / standardized candidate
    2. otherwise keep lexical/both hits only
    3. otherwise fall back to strong vector hits
    """
    q = _norm_text(query_text)

    if not collapsed_groups:
        return []

    # 1) exact lexical match
    exact_matches = []
    for g in collapsed_groups:
        originals = [_norm_text(x) for x in g.get("entity_original_examples", [])]
        entity = _norm_text(g.get("entity"))
        standardized = _norm_text(g.get("entity_standardized_candidate"))

        if q in originals or q == entity or q == standardized:
            exact_matches.append(g)

    if exact_matches:
        return exact_matches

    # 2) lexical-supported matches
    lexical_supported = []
    for g in collapsed_groups:
        hit_sources = set(g.get("hit_sources", []))
        if "lexical" in hit_sources or "both" in hit_sources:
            lexical_supported.append(g)

    if lexical_supported:
        return lexical_supported

    # 3) vector fallback
    vector_supported = []
    for g in collapsed_groups:
        score = g.get("max_vector_score")
        if score is not None and score >= min_vector_score:
            vector_supported.append(g)

    return vector_supported


def _norm_text(s: str) -> str:
    if s is None:
        return ""
    return re.sub(r"\s+", " ", str(s).strip().lower())


def _tokenize(s: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", _norm_text(s))


def filter_grounded_groups_strict_short_query(
    query_text, collapsed_groups, min_vector_score=0.82
):
    q = _norm_text(query_text)
    q_tokens = set(_tokenize(query_text))

    if len(q) <= 5:
        kept = []
        for g in collapsed_groups:
            originals = [_norm_text(x) for x in g.get("entity_original_examples", [])]

            for orig in originals:
                orig_tokens = set(_tokenize(orig))

                # exact string match
                if q == orig:
                    kept.append(g)
                    break

                # token-level match, e.g. MI -> prior MI
                if q in orig_tokens or q_tokens.issubset(orig_tokens):
                    kept.append(g)
                    break

        return kept

    return filter_grounded_groups(
        query_text, collapsed_groups, min_vector_score=min_vector_score
    )


def pretty_print_filtered_groups(groups):
    if not groups:
        print("No grounded groups remained after filtering.")
        return

    for i, g in enumerate(groups, start=1):
        print("=" * 100)
        print(f"[{i}] {g.get('entity_standardized_candidate') or '-'}")
        print("-" * 100)
        print(f"Entity             : {g.get('entity') or '-'}")
        print(
            f"Original examples  : {', '.join(g.get('entity_original_examples', [])) or '-'}"
        )
        print(f"Hit sources        : {', '.join(g.get('hit_sources', [])) or '-'}")
        print(
            f"Max lexical score  : {g.get('max_lexical_score') if g.get('max_lexical_score') is not None else '-'}"
        )
        print(
            f"Max vector score   : {g.get('max_vector_score') if g.get('max_vector_score') is not None else '-'}"
        )
        print(f"Rule count         : {g.get('rule_count')}")
        print(f"Decision count     : {g.get('decision_count')}")
    print("=" * 100)


def decision_main(
    URI,
    AUTH,
    entity,
    model="mxbai-embed-large:latest",
    host="http://localhost:11434",
    embed=False,
):

    embedder = SimpleOllamaEmbedder(
        model=model,
        host=host,
    )
    if embed:
        embed_decisionnodes_and_create_indexes(
            uri=URI,
            auth=AUTH,
            embedder=embedder,
            dimensions=1024,
            source_property="entity_standardized_candidate",
            embedding_property="embedding_entity_standardized",
        )

    driver = GraphDatabase.driver(URI, auth=AUTH)

    results = hybrid_search_decisionnodes(
        driver=driver,
        embedder=embedder,
        query_text=entity,
        top_k_vector=100,
        top_k_fulltext=100,
        min_vector_score=0.8,
        min_fulltext_score=0.0,
        final_limit=200,
    )

    pretty_print_decisionnode_hits(results)
    collapsed = collapse_decisionnode_hits(results)
    filtered = filter_grounded_groups_strict_short_query(entity, collapsed)

    pretty_print_filtered_groups(filtered)

    driver.close()
    return filtered


def main(URI, AUTH, model="mxbai-embed-large:latest", host="http://localhost:11434"):

    embedder = SimpleOllamaEmbedder(
        model,
        host,
    )

    # embed_concepts_and_create_indexes(
    #     uri=URI,
    #     auth=AUTH,
    #     embedder=embedder,
    #     dimensions=1024,
    # )

    driver = GraphDatabase.driver(URI, auth=AUTH)

    results = hybrid_search_concepts(
        driver=driver,
        embedder=embedder,
        query_text=" CCS",
        top_k_vector=100,
        top_k_fulltext=100,
        min_vector_score=0.70,
        min_fulltext_score=0.0,
        final_limit=200,
    )
    pretty_print_concept_hits(results)

    driver.close()
    return
