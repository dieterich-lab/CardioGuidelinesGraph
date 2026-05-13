from __future__ import annotations

import argparse
import json
import os
import re
from typing import Any, Dict, List, Optional
from datetime import datetime
from pathlib import Path
from neo4j import GraphDatabase

try:
    from cardio_graph_core.query.langchain_replacement import SimpleOllamaEmbedder
except Exception:
    SimpleOllamaEmbedder = None


DEFAULT_URI = "bolt://neo4j-dev2.internal:7687"
DEFAULT_USER = "neo4j"
DEFAULT_PASSWORD = "KWCeoHhkJYAiFa3XTZZZLC77bHiZ5xzj"

DEFAULT_HOST = "10.250.135.150:11430"
DEFAULT_MODEL = "mxbai-embed-large:latest"

DEFAULT_EVAL_TERMS = [
    "chronic coronary syndrome",
    "CCS",
    "chronic ischemic heart disease",
    "coronary artery disease",
    "CAD",
    "multivessel disease",
    "multivessel CAD",
    "functionally significant multivessel disease",
    "three-vessel disease",
    "functionally significant three-vessel disease",
    "two-vessel disease",
    "functionally significant two-vessel disease involving the proximal LAD",
    "proximal LAD",
    "left main stem disease",
    "functionally significant left main stem stenosis",
    "LVEF 20%",
    "LVEF = 20%",
    "LVEF ≤ 35%",
    "LVEF > 35%",
    "left ventricular ejection fraction",
    "inoperable",
    "not operable",
    "surgically eligible",
    "high surgical risk",
    "persistent angina",
    "guideline-directed medical therapy",
    "oral anticoagulation",
    "no indication for oral anticoagulation",
    "myocardial revascularization",
    "PCI",
    "percutaneous coronary intervention",
    "CABG",
    "coronary artery bypass grafting",
    "dual antiplatelet therapy",
    "single antiplatelet therapy",
]


def _fmt(value: Any, digits: int = 4) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def _norm_text(s: str) -> str:
    if s is None:
        return ""
    return re.sub(r"\s+", " ", str(s).strip().lower())


def _tokenize(s: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", _norm_text(s))


def escape_lucene(text: str) -> str:
    return re.sub(r'([+\-!(){}\[\]^"~*?:\\/]|&&|\|\|)', r"\\\1", text)


GENERIC_TOKENS = {
    "patient",
    "patients",
    "with",
    "without",
    "and",
    "or",
    "the",
    "a",
    "an",
    "of",
    "for",
    "in",
    "on",
    "to",
    "due",
    "functionally",
    "significant",
}


def build_basic_fulltext_query(query_text: str) -> str:
    """
    Generic Lucene query builder.

    This is deliberately simpler than your guideline-specific builder.
    It lets you test index behavior without too much domain logic.
    """
    q = _norm_text(query_text)
    q_escaped = escape_lucene(q)

    tokens = [t for t in _tokenize(q) if t not in GENERIC_TOKENS]
    tokens = [escape_lucene(t) for t in tokens]

    clauses = [f'"{q_escaped}"^8']

    if tokens:
        clauses.append("(" + " AND ".join(tokens) + ")^4")
        clauses.append("(" + " OR ".join(tokens) + ")^1")

    return " OR ".join(clauses)


def connect(uri: str, user: str, password: str):
    return GraphDatabase.driver(uri, auth=(user, password))


def list_indexes(driver) -> List[Dict[str, Any]]:
    """
    Works on modern Neo4j versions using SHOW INDEXES.
    """
    cypher = """
    SHOW INDEXES
    YIELD name, type, entityType, labelsOrTypes, properties, state, populationPercent, options
    RETURN name, type, entityType, labelsOrTypes, properties, state, populationPercent, options
    ORDER BY type, name
    """

    with driver.session() as session:
        rows = session.run(cypher)
        return [dict(r) for r in rows]


def print_indexes(indexes: List[Dict[str, Any]]) -> None:
    print("\n" + "=" * 120)
    print("NEO4J INDEXES")
    print("=" * 120)

    if not indexes:
        print("No indexes found.")
        return

    for i, idx in enumerate(indexes, start=1):
        print("-" * 120)
        print(f"[{i}] {idx.get('name')}")
        print(f"Type               : {idx.get('type')}")
        print(f"Entity type        : {idx.get('entityType')}")
        print(f"Labels/types       : {idx.get('labelsOrTypes')}")
        print(f"Properties         : {idx.get('properties')}")
        print(f"State              : {idx.get('state')}")
        print(f"Population percent : {idx.get('populationPercent')}")

        options = idx.get("options")
        if options:
            print("Options:")
            print(json.dumps(options, indent=2, ensure_ascii=False))

    print("=" * 120)
    print(f"Total indexes: {len(indexes)}")


def filter_indexes(
    indexes: List[Dict[str, Any]],
    index_type: Optional[str] = None,
    name_contains: Optional[str] = None,
) -> List[Dict[str, Any]]:
    out = indexes

    if index_type:
        wanted = index_type.lower()
        out = [i for i in out if str(i.get("type", "")).lower() == wanted]

    if name_contains:
        needle = name_contains.lower()
        out = [i for i in out if needle in str(i.get("name", "")).lower()]

    return out


def describe_index(driver, index_name: str) -> Optional[Dict[str, Any]]:
    cypher = """
    SHOW INDEXES
    YIELD name, type, entityType, labelsOrTypes, properties, state, populationPercent, options
    WHERE name = $index_name
    RETURN name, type, entityType, labelsOrTypes, properties, state, populationPercent, options
    """

    with driver.session() as session:
        row = session.run(cypher, {"index_name": index_name}).single()

    return dict(row) if row else None


def run_fulltext_query(
    driver,
    index_name: str,
    query_text: str,
    *,
    limit: int = 20,
    min_score: float = 0.0,
    use_basic_query_builder: bool = True,
) -> List[Dict[str, Any]]:
    fulltext_query = (
        build_basic_fulltext_query(query_text)
        if use_basic_query_builder
        else query_text
    )

    cypher = """
        CALL db.index.fulltext.queryNodes($index_name, $fulltext_query)
        YIELD node, score
        WHERE score >= $min_score
        OPTIONAL MATCH (node)-[:CHECKS_FOR|EVALUATES]->(concept)
        RETURN
            elementId(node) AS element_id,
            labels(node) AS labels,
            score,
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
            node.search_aliases AS search_aliases,
            properties(node) AS properties,

            elementId(concept) AS concept_element_id,
            concept.snomed_id AS concept_snomed_id,
            concept.name AS concept_name,
            concept.preferred_term AS concept_preferred_term,
            concept.display_name AS concept_display_name,
            concept.entity AS concept_entity,
            concept.entity_original AS concept_entity_original,
            concept.entity_standardized_candidate AS concept_entity_standardized_candidate,
            concept.target_label AS concept_target_label,
            labels(concept) AS concept_labels
        ORDER BY score DESC
        LIMIT $limit
    """

    with driver.session() as session:
        rows = session.run(
            cypher,
            {
                "index_name": index_name,
                "fulltext_query": fulltext_query,
                "min_score": min_score,
                "limit": limit,
            },
        )
        results = [dict(r) for r in rows]
    idx = describe_index(driver, index_name)
    indexed_properties = idx.get("properties") or []

    for rank, row in enumerate(results, start=1):
        row["rank"] = rank
        row["index_name"] = index_name
        row["index_type"] = "FULLTEXT"
        row["indexed_properties"] = indexed_properties
        row["query_sent_to_index"] = fulltext_query

    return results


def run_vector_query(
    driver,
    index_name: str,
    query_text: str,
    embedder,
    *,
    limit: int = 20,
    min_score: float = 0.0,
) -> List[Dict[str, Any]]:
    if embedder is None:
        raise RuntimeError("Vector query requires an embedder.")

    query_embedding = embedder.embed_query(query_text)

    cypher = """
    CALL db.index.vector.queryNodes($index_name, $limit, $query_embedding)
    YIELD node, score
    WHERE score >= $min_score
    OPTIONAL MATCH (node)-[:CHECKS_FOR|EVALUATES]->(concept)
    RETURN
        elementId(node) AS element_id,
        labels(node) AS labels,
        score,
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
        node.search_aliases AS search_aliases,
        properties(node) AS properties,

        elementId(concept) AS concept_element_id,
        concept.snomed_id AS concept_snomed_id,
        concept.name AS concept_name,
        concept.preferred_term AS concept_preferred_term,
        concept.display_name AS concept_display_name,
        concept.entity AS concept_entity,
        concept.entity_original AS concept_entity_original,
        concept.entity_standardized_candidate AS concept_entity_standardized_candidate,
        concept.target_label AS concept_target_label,
        labels(concept) AS concept_labels
    ORDER BY score DESC
    LIMIT $limit
    """

    with driver.session() as session:
        rows = session.run(
            cypher,
            {
                "index_name": index_name,
                "query_embedding": query_embedding,
                "min_score": min_score,
                "limit": limit,
            },
        )
        results = [dict(r) for r in rows]

    idx = describe_index(driver, index_name)
    indexed_properties = idx.get("properties") or []

    for rank, row in enumerate(results, start=1):
        row["rank"] = rank
        row["index_name"] = index_name
        row["index_type"] = "VECTOR"
        row["indexed_properties"] = indexed_properties
        row["vector_source_property"] = (
            indexed_properties[0] if indexed_properties else None
        )

    return results


def print_hits(results: List[Dict[str, Any]], max_hits: int = 20) -> None:
    if not results:
        print("No hits.")
        return

    print("\n" + "=" * 120)
    print(f"RESULTS: {results[0].get('index_name')} [{results[0].get('index_type')}]")
    print("=" * 120)

    query_sent = results[0].get("query_sent_to_index")
    if query_sent:
        print("Fulltext query sent to index:")
        print(query_sent)
        print("-" * 120)

    for hit in results[:max_hits]:
        print("-" * 120)
        print(
            f"[{hit.get('rank')}] {hit.get('entity_standardized_candidate') or hit.get('entity') or hit.get('question') or '-'}"
        )
        print(f"Score          : {_fmt(hit.get('score'))}")
        print(f"Labels         : {', '.join(hit.get('labels') or [])}")
        print(f"Rule ID        : {hit.get('rule_unique_id') or '-'}")
        print(f"Decision ID    : {hit.get('decision_id') or '-'}")
        print(f"Entity         : {hit.get('entity') or '-'}")
        print(f"Original       : {hit.get('entity_original') or '-'}")
        print(f"Standardized   : {hit.get('entity_standardized_candidate') or '-'}")
        print(f"Question       : {hit.get('question') or '-'}")
        print(f"Context        : {hit.get('context') or '-'}")
        print(f"Operator       : {hit.get('operator') or '-'}")
        print(f"Threshold      : {hit.get('threshold') or '-'}")
        print(f"Unit           : {hit.get('unit') or '-'}")

    if len(results) > max_hits:
        print("-" * 120)
        print(f"... omitted {len(results) - max_hits} additional hits")

    print("=" * 120)
    print(f"Total hits shown/returned: {min(len(results), max_hits)}/{len(results)}")


def evaluate_single_index(
    driver,
    index_name: str,
    query_text: str,
    *,
    embedder=None,
    limit: int = 20,
    min_score: float = 0.0,
    use_basic_query_builder: bool = True,
) -> List[Dict[str, Any]]:
    idx = describe_index(driver, index_name)

    if idx is None:
        raise ValueError(f"Index not found: {index_name}")

    idx_type = str(idx.get("type", "")).upper()

    print("\n" + "#" * 120)
    print(f"QUERY: {query_text}")
    print(f"INDEX: {index_name}")
    print(f"TYPE : {idx_type}")
    print("#" * 120)

    if idx_type == "FULLTEXT":
        results = run_fulltext_query(
            driver,
            index_name,
            query_text,
            limit=limit,
            min_score=min_score,
            use_basic_query_builder=use_basic_query_builder,
        )
    elif idx_type == "VECTOR":
        results = run_vector_query(
            driver,
            index_name,
            query_text,
            embedder,
            limit=limit,
            min_score=min_score,
        )
    else:
        raise ValueError(
            f"Index {index_name!r} has unsupported type {idx_type!r}. "
            "This diagnostic currently supports FULLTEXT and VECTOR indexes."
        )

    print_hits(results, max_hits=limit)
    return results


def evaluate_many_indexes(
    driver,
    query_text: str,
    *,
    index_names: Optional[List[str]] = None,
    index_type: Optional[str] = None,
    name_contains: Optional[str] = None,
    embedder=None,
    limit: int = 20,
    min_score: float = 0.0,
    use_basic_query_builder: bool = True,
) -> Dict[str, List[Dict[str, Any]]]:
    indexes = list_indexes(driver)

    if index_names:
        selected = [i for i in indexes if i.get("name") in set(index_names)]
    else:
        selected = filter_indexes(
            indexes,
            index_type=index_type,
            name_contains=name_contains,
        )

    if not selected:
        print("No matching indexes selected.")
        return {}

    print("\n" + "=" * 120)
    print("SELECTED INDEXES")
    print("=" * 120)
    for idx in selected:
        print(
            f"- {idx.get('name')} [{idx.get('type')}] labels={idx.get('labelsOrTypes')} props={idx.get('properties')} state={idx.get('state')}"
        )

    all_results = {}

    for idx in selected:
        name = idx.get("name")
        idx_type = str(idx.get("type", "")).upper()

        if idx_type not in {"FULLTEXT", "VECTOR"}:
            print(f"\nSkipping unsupported index type: {name} [{idx_type}]")
            continue

        try:
            all_results[name] = evaluate_single_index(
                driver,
                name,
                query_text,
                embedder=embedder,
                limit=limit,
                min_score=min_score,
                use_basic_query_builder=use_basic_query_builder,
            )
        except Exception as e:
            print("\n" + "!" * 120)
            print(f"FAILED INDEX: {name}")
            print(f"ERROR       : {e}")
            print("!" * 120)
            all_results[name] = []

    return all_results


def summarize_cross_index_results(all_results: Dict[str, List[Dict[str, Any]]]) -> None:
    print("\n" + "=" * 120)
    print("CROSS-INDEX SUMMARY")
    print("=" * 120)

    if not all_results:
        print("No results to summarize.")
        return

    for index_name, results in all_results.items():
        if not results:
            print(f"- {index_name}: no hits")
            continue

        top = results[0]
        print(
            f"- {index_name} [{top.get('index_type')}]: "
            f"top_score={_fmt(top.get('score'))}, "
            f"top='{top.get('entity_standardized_candidate') or top.get('entity') or top.get('question') or '-'}', "
            f"hits={len(results)}"
        )

    print("=" * 120)


def load_terms_from_file(path: str) -> List[str]:
    terms = []

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            term = line.strip()
            if not term:
                continue
            if term.startswith("#"):
                continue
            terms.append(term)

    return terms


def compact_hit(hit: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "rank": hit.get("rank"),
        "index_name": hit.get("index_name"),
        "index_type": hit.get("index_type"),
        "score": hit.get("score"),
        "labels": hit.get("labels"),
        "rule_unique_id": hit.get("rule_unique_id"),
        "decision_id": hit.get("decision_id"),
        "entity": hit.get("entity"),
        "entity_original": hit.get("entity_original"),
        "entity_standardized_candidate": hit.get("entity_standardized_candidate"),
        "question": hit.get("question"),
        "context": hit.get("context"),
        "operator": hit.get("operator"),
        "threshold": hit.get("threshold"),
        "unit": hit.get("unit"),
        "vector_source_property": hit.get("vector_source_property"),
        "indexed_properties": hit.get("indexed_properties"),
        "query_sent_to_index": hit.get("query_sent_to_index"),
        "concept_element_id": hit.get("concept_element_id"),
        "concept_snomed_id": hit.get("concept_snomed_id"),
        "concept_name": hit.get("concept_name"),
        "concept_preferred_term": hit.get("concept_preferred_term"),
        "concept_display_name": hit.get("concept_display_name"),
        "concept_entity": hit.get("concept_entity"),
        "concept_entity_original": hit.get("concept_entity_original"),
        "concept_entity_standardized_candidate": hit.get(
            "concept_entity_standardized_candidate"
        ),
        "concept_target_label": hit.get("concept_target_label"),
        "concept_labels": hit.get("concept_labels"),
    }


def run_batch_index_eval(
    driver,
    terms: List[str],
    *,
    index_names: List[str],
    embedder=None,
    limit: int = 10,
    min_score: float = 0.0,
    use_basic_query_builder: bool = True,
) -> Dict[str, Any]:
    """
    Run many terms across many indexes.

    Returns nested structure:
      {
        "terms": [...],
        "indexes": [...],
        "results": {
          term: {
            index_name: [hits...]
          }
        }
      }
    """
    batch_results = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "terms": terms,
        "indexes": index_names,
        "limit": limit,
        "min_score": min_score,
        "use_basic_query_builder": use_basic_query_builder,
        "results": {},
    }

    for term_idx, term in enumerate(terms, start=1):
        print("\n" + "#" * 120)
        print(f"BATCH TERM {term_idx}/{len(terms)}: {term}")
        print("#" * 120)

        term_results = evaluate_many_indexes(
            driver,
            term,
            index_names=index_names,
            embedder=embedder,
            limit=limit,
            min_score=min_score,
            use_basic_query_builder=use_basic_query_builder,
        )

        batch_results["results"][term] = {
            index_name: [compact_hit(h) for h in hits]
            for index_name, hits in term_results.items()
        }

    return batch_results


def write_batch_report(
    batch_results: Dict[str, Any],
    output_dir: str,
    *,
    report_name: Optional[str] = None,
    top_n: int = 5,
    write_json: bool = True,
) -> Dict[str, str]:
    """
    Write a human-readable .txt report and optionally a .json file.

    This report is concept-aware:
      - Retrieval happens over DecisionNode hits.
      - The report also shows the connected Concept node.
      - Cross-index summaries use the connected Concept as the primary title.
    """
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if report_name is None:
        report_name = f"index_eval_report_{timestamp}"

    txt_path = out_dir / f"{report_name}.txt"
    json_path = out_dir / f"{report_name}.json"

    terms = batch_results.get("terms", [])
    indexes = batch_results.get("indexes", [])
    results = batch_results.get("results", {})

    def _concept_title(hit: Dict[str, Any]) -> str:
        if not hit:
            return "-"

        return (
            hit.get("concept_preferred_term")
            or hit.get("concept_display_name")
            or hit.get("concept_name")
            or hit.get("concept_entity_standardized_candidate")
            or hit.get("concept_entity")
            or hit.get("entity_standardized_candidate")
            or hit.get("entity")
            or hit.get("question")
            or "-"
        )

    def _decision_title(hit: Dict[str, Any]) -> str:
        if not hit:
            return "-"

        return (
            hit.get("entity_standardized_candidate")
            or hit.get("entity")
            or hit.get("question")
            or "-"
        )

    def _join_list(value: Any) -> str:
        if not value:
            return "-"
        if isinstance(value, list):
            return ", ".join(str(x) for x in value if x is not None) or "-"
        return str(value)

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("INDEX EVALUATION REPORT\n")
        f.write("=" * 120 + "\n")
        f.write(f"Created at              : {batch_results.get('created_at')}\n")
        f.write(f"Number of terms         : {len(terms)}\n")
        f.write(f"Number of indexes       : {len(indexes)}\n")
        f.write(f"Limit per index/query   : {batch_results.get('limit')}\n")
        f.write(f"Min score               : {batch_results.get('min_score')}\n")
        f.write(
            f"Use boosted fulltext    : {batch_results.get('use_basic_query_builder')}\n"
        )

        f.write("\nIndexes:\n")
        for idx in indexes:
            f.write(f"  - {idx}\n")

        f.write("\nTerms:\n")
        for term in terms:
            f.write(f"  - {term}\n")

        f.write("\n" + "=" * 120 + "\n")
        f.write("DETAILED RESULTS\n")
        f.write("=" * 120 + "\n")

        for term in terms:
            f.write("\n" + "#" * 120 + "\n")
            f.write(f"TERM: {term}\n")
            f.write("#" * 120 + "\n")

            term_results = results.get(term, {})

            for index_name in indexes:
                hits = term_results.get(index_name, [])

                f.write("\n" + "-" * 120 + "\n")
                f.write(f"INDEX: {index_name}\n")
                f.write("-" * 120 + "\n")

                if not hits:
                    f.write("No hits.\n")
                    continue

                top = hits[0]
                query_sent = top.get("query_sent_to_index")
                if query_sent:
                    f.write(f"Fulltext query sent: {query_sent}\n\n")

                for hit in hits[:top_n]:
                    concept_title = _concept_title(hit)
                    decision_title = _decision_title(hit)

                    f.write(
                        f"[{hit.get('rank')}] "
                        f"score={_fmt(hit.get('score'))} "
                        f"concept={concept_title}\n"
                    )

                    f.write(
                        f"    index_type          : {hit.get('index_type') or '-'}\n"
                    )
                    f.write(
                        f"    indexed_properties  : {_join_list(hit.get('indexed_properties'))}\n"
                    )

                    if hit.get("index_type") == "VECTOR":
                        f.write(
                            f"    vector_property     : "
                            f"{hit.get('vector_source_property') or '-'}\n"
                        )

                    f.write("\n")
                    f.write("    DecisionNode:\n")
                    f.write(
                        f"      labels            : {_join_list(hit.get('labels'))}\n"
                    )
                    f.write(f"      title             : {decision_title}\n")
                    f.write(
                        f"      rule_id           : {hit.get('rule_unique_id') or '-'}\n"
                    )
                    f.write(
                        f"      decision_id       : {hit.get('decision_id') or '-'}\n"
                    )
                    f.write(f"      entity            : {hit.get('entity') or '-'}\n")
                    f.write(
                        f"      entity_original   : {hit.get('entity_original') or '-'}\n"
                    )
                    f.write(
                        f"      standardized      : "
                        f"{hit.get('entity_standardized_candidate') or '-'}\n"
                    )
                    f.write(f"      question          : {hit.get('question') or '-'}\n")
                    f.write(f"      context           : {hit.get('context') or '-'}\n")
                    f.write(
                        f"      condition         : "
                        f"{hit.get('operator') or '-'} "
                        f"{hit.get('threshold') or '-'} "
                        f"{hit.get('unit') or '-'}\n"
                    )

                    f.write("\n")
                    f.write("    Connected Concept:\n")
                    f.write(f"      concept           : {concept_title}\n")
                    f.write(
                        f"      concept_element_id: "
                        f"{hit.get('concept_element_id') or '-'}\n"
                    )
                    f.write(
                        f"      snomed_id         : "
                        f"{hit.get('concept_snomed_id') or '-'}\n"
                    )
                    f.write(
                        f"      preferred_term    : "
                        f"{hit.get('concept_preferred_term') or '-'}\n"
                    )
                    f.write(
                        f"      display_name      : "
                        f"{hit.get('concept_display_name') or '-'}\n"
                    )
                    f.write(
                        f"      concept_name      : "
                        f"{hit.get('concept_name') or '-'}\n"
                    )
                    f.write(
                        f"      concept_entity    : "
                        f"{hit.get('concept_entity') or '-'}\n"
                    )
                    f.write(
                        f"      concept_original  : "
                        f"{hit.get('concept_entity_original') or '-'}\n"
                    )
                    f.write(
                        f"      concept_standard  : "
                        f"{hit.get('concept_entity_standardized_candidate') or '-'}\n"
                    )
                    f.write(
                        f"      target_label      : "
                        f"{hit.get('concept_target_label') or '-'}\n"
                    )
                    f.write(
                        f"      concept_labels    : "
                        f"{_join_list(hit.get('concept_labels'))}\n"
                    )

                    f.write("\n")

        f.write("\n" + "=" * 120 + "\n")
        f.write("CROSS-INDEX TOP-1 SUMMARY\n")
        f.write("=" * 120 + "\n")

        for term in terms:
            f.write("\n" + "-" * 120 + "\n")
            f.write(f"TERM: {term}\n")
            f.write("-" * 120 + "\n")

            term_results = results.get(term, {})

            for index_name in indexes:
                hits = term_results.get(index_name, [])

                if not hits:
                    f.write(f"{index_name}: no hits\n")
                    continue

                top = hits[0]
                concept_title = _concept_title(top)
                decision_title = _decision_title(top)

                f.write(
                    f"{index_name}: "
                    f"score={_fmt(top.get('score'))}, "
                    f"top_concept='{concept_title}', "
                    f"snomed='{top.get('concept_snomed_id') or '-'}', "
                    f"decision_title='{decision_title}', "
                    f"original='{top.get('entity_original') or '-'}', "
                    f"decision_id='{top.get('decision_id') or '-'}'\n"
                )

        f.write("\n" + "=" * 120 + "\n")
        f.write("CROSS-INDEX TOP-1 CONCEPT AGREEMENT\n")
        f.write("=" * 120 + "\n")

        for term in terms:
            term_results = results.get(term, {})

            concept_counter = {}
            no_hit_indexes = []

            for index_name in indexes:
                hits = term_results.get(index_name, [])

                if not hits:
                    no_hit_indexes.append(index_name)
                    continue

                top = hits[0]
                key = top.get("concept_snomed_id") or _concept_title(top) or "-"

                if key not in concept_counter:
                    concept_counter[key] = {
                        "concept": _concept_title(top),
                        "snomed": top.get("concept_snomed_id") or "-",
                        "indexes": [],
                    }

                concept_counter[key]["indexes"].append(index_name)

            f.write("\n" + "-" * 120 + "\n")
            f.write(f"TERM: {term}\n")
            f.write("-" * 120 + "\n")

            if not concept_counter:
                f.write("No indexes returned hits.\n")
            else:
                sorted_concepts = sorted(
                    concept_counter.values(),
                    key=lambda x: (-len(x["indexes"]), x["concept"]),
                )

                for item in sorted_concepts:
                    f.write(
                        f"Concept: {item['concept']} "
                        f"(snomed={item['snomed']}) "
                        f"-> {len(item['indexes'])}/{len(indexes)} indexes\n"
                    )
                    for idx in item["indexes"]:
                        f.write(f"  - {idx}\n")

            if no_hit_indexes:
                f.write("No-hit indexes:\n")
                for idx in no_hit_indexes:
                    f.write(f"  - {idx}\n")

    output_paths = {"txt": str(txt_path)}

    if write_json:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(batch_results, f, indent=2, ensure_ascii=False, default=str)

        output_paths["json"] = str(json_path)

    return output_paths


def make_embedder(model: str, host: str):
    if SimpleOllamaEmbedder is None:
        raise RuntimeError(
            "Could not import SimpleOllamaEmbedder. "
            "Vector index testing will not work from this script."
        )

    return SimpleOllamaEmbedder(
        model=model,
        host=host,
    )


def main():
    parser = argparse.ArgumentParser(
        description="Inspect Neo4j indexes and test fulltext/vector retrieval performance."
    )

    parser.add_argument("--uri", default=DEFAULT_URI)
    parser.add_argument("--user", default=DEFAULT_USER)
    parser.add_argument("--password", default=DEFAULT_PASSWORD)

    parser.add_argument(
        "--list",
        action="store_true",
        help="List all Neo4j indexes and exit.",
    )

    parser.add_argument(
        "--query",
        type=str,
        default=None,
        help="Query string to test against indexes.",
    )

    parser.add_argument(
        "--index",
        action="append",
        default=None,
        help="Specific index name to test. Can be used multiple times.",
    )

    parser.add_argument(
        "--type",
        choices=["FULLTEXT", "VECTOR"],
        default=None,
        help="Only test indexes of this type.",
    )

    parser.add_argument(
        "--name-contains",
        type=str,
        default=None,
        help="Only test indexes whose name contains this substring.",
    )

    parser.add_argument(
        "--batch",
        action="store_true",
        help="Run batch evaluation over many terms and save a report.",
    )

    parser.add_argument(
        "--terms-file",
        type=str,
        default=None,
        help="Optional text file with one query term per line.",
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default="/home/ecalik/cgg_working_dir/CardioGuidelinesGraph/outputs/index_eval",
        help="Directory where batch reports are saved.",
    )

    parser.add_argument(
        "--report-name",
        type=str,
        default=None,
        help="Optional base filename for the report, without extension.",
    )

    parser.add_argument(
        "--top-n-report",
        type=int,
        default=5,
        help="Number of hits per index/query to include in the text report.",
    )

    parser.add_argument(
        "--raw-fulltext",
        action="store_true",
        help="Send fulltext query directly without boosted query expansion.",
    )

    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--min-score", type=float, default=0.0)

    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--model", default=DEFAULT_MODEL)

    args = parser.parse_args()

    driver = connect(args.uri, args.user, args.password)

    try:
        if args.list:
            indexes = list_indexes(driver)
            print_indexes(indexes)
            return

        needs_embedder = False

        if args.index:
            indexes = list_indexes(driver)
            index_map = {i.get("name"): i for i in indexes}

            for name in args.index:
                idx = index_map.get(name)
                if idx and str(idx.get("type", "")).upper() == "VECTOR":
                    needs_embedder = True

        elif args.type == "VECTOR":
            needs_embedder = True

        elif args.type is None:
            # If testing all indexes, create embedder so vector indexes can also run.
            # In batch mode, this is also safe if mixed indexes are passed.
            needs_embedder = True

        embedder = make_embedder(args.model, args.host) if needs_embedder else None

        # Batch mode does not require --query.
        if args.batch:
            terms = (
                load_terms_from_file(args.terms_file)
                if args.terms_file
                else DEFAULT_EVAL_TERMS
            )

            if not args.index:
                raise ValueError(
                    "Batch mode requires at least one --index argument. "
                    "Pass the indexes you want to compare."
                )

            batch_results = run_batch_index_eval(
                driver,
                terms,
                index_names=args.index,
                embedder=embedder,
                limit=args.limit,
                min_score=args.min_score,
                use_basic_query_builder=not args.raw_fulltext,
            )

            paths = write_batch_report(
                batch_results,
                output_dir=args.output_dir,
                report_name=args.report_name,
                top_n=args.top_n_report,
                write_json=True,
            )

            print("\nSaved batch reports:")
            for kind, path in paths.items():
                print(f"  {kind}: {path}")

            return

        # Single-query mode requires --query.
        if not args.query:
            print(
                "No --query provided. Use --list to inspect indexes, "
                "--batch to run batch evaluation, or --query to test retrieval."
            )
            return

        results = evaluate_many_indexes(
            driver,
            args.query,
            index_names=args.index,
            index_type=args.type,
            name_contains=args.name_contains,
            embedder=embedder,
            limit=args.limit,
            min_score=args.min_score,
            use_basic_query_builder=not args.raw_fulltext,
        )

        summarize_cross_index_results(results)

    finally:
        driver.close()


if __name__ == "__main__":
    main()
