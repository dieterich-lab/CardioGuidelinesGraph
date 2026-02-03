#!/usr/bin/env python3
"""
Load grounding_index.json into Neo4j and (optionally) create rule logic nodes.

- Concept nodes are MERGED by snomed_id and labeled by target_label.
- Rule/decision/recommendation nodes are created only if a rules file is provided.
"""

import json
import os
from collections import defaultdict
from typing import Any, Dict, Iterable, List, Optional

import click
from neo4j import GraphDatabase

from cardio_graph.neo4j_utils.feedneo4jdb import AUTH as DEFAULT_AUTH
from cardio_graph.neo4j_utils.feedneo4jdb import URI as DEFAULT_URI


def _load_grounding_index(index_path: str) -> List[Dict[str, Any]]:
    with open(index_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    entries = list(data.get("by_snomed_id", {}).values())
    return entries


def _load_rules(rules_path: str) -> List[Dict[str, Any]]:
    if not rules_path:
        return []
    if rules_path.endswith(".jsonl"):
        rows = []
        with open(rules_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rows.append(json.loads(line))
        return rows
    with open(rules_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _group_by_label(entries: Iterable[Dict[str, Any]]) -> Dict[str, List[Dict]]:
    grouped: Dict[str, List[Dict]] = defaultdict(list)
    for entry in entries:
        label = entry.get("target_label") or "Concept"
        grouped[label].append(entry)
    return grouped


def _merge_concepts(session, label: str, rows: List[Dict[str, Any]]) -> None:
    query = f"""
    UNWIND $rows AS row
    MERGE (n:`{label}` {{snomed_id: row.snomed_id}})
    SET n.preferred_term = row.preferred_term,
        n.standardized = row.entity_standardized_candidate,
        n.target_label = row.target_label
    SET n:Concept
    """
    session.run(query, rows=rows)

    for row in rows:
        path = row.get("taxonomy_path") or []
        if len(path) < 2:
            continue
        for i in range(len(path) - 1):
            child = path[i]
            parent = path[i + 1]
            session.run(
                """
                MERGE (c:Concept {snomed_id: $child_id})
                ON CREATE SET c.preferred_term = $child_term
                MERGE (p:Concept {snomed_id: $parent_id})
                ON CREATE SET p.preferred_term = $parent_term
                MERGE (c)-[:IS_A]->(p)
                """,
                child_id=str(child.get("concept_id")),
                child_term=child.get("term"),
                parent_id=str(parent.get("concept_id")),
                parent_term=parent.get("term"),
            )


def _create_rule_nodes(
    session, grouped_rules: Dict[str, List[Dict[str, Any]]]
) -> None:
    for rule_key, concepts in grouped_rules.items():
        rec_props = _infer_recommendation_props(concepts)
        source_info = concepts[0].get("source_context") or concepts[0].get(
            "chunk_id"
        ) or "Unknown Source"
        original_rule_id = concepts[0].get("rule_id")
        session.run(
            """
            MERGE (rec:RecommendationNode {rule_unique_id: $rule_key})
            SET rec.class = $class,
                rec.level = $level,
                rec.direction = $direction,
                rec.original_rule_id = $orig_rule_id,
                rec.source = $source
            """,
            rule_key=str(rule_key),
            orig_rule_id=original_rule_id,
            source=source_info,
            **rec_props,
        )

        for concept in concepts:
            role = (concept.get("role") or "").strip()
            logic_structured = concept.get("logic_structured") or {}
            snomed_id = concept.get("snomed_id")
            target_label = concept.get("target_label") or "Concept"

            if role in {"Condition", "ClinicalParameter"}:
                session.run(
                    f"""
                    MERGE (c:`{target_label}` {{snomed_id: $snomed_id}})
                    MERGE (dec:DecisionNode {{rule_unique_id: $rule_key, concept: $concept}})
                    SET dec.operator = $operator,
                        dec.threshold = $threshold,
                        dec.unit = $unit,
                        dec.condition_context = $condition_context
                    MERGE (c)-[:HAS_RULE]->(dec)
                    MERGE (dec)-[:RESULTS_IN {{condition_met: true}}]->(rec)
                    """,
                    snomed_id=snomed_id,
                    rule_key=str(rule_key),
                    concept=concept.get("entity_standardized_candidate"),
                    operator=logic_structured.get("operator"),
                    threshold=logic_structured.get("threshold"),
                    unit=logic_structured.get("unit"),
                    condition_context=logic_structured.get("condition_context"),
                )

            if role in {"Medication", "Procedure"}:
                relation = _recommendation_relation(logic_structured)
                session.run(
                    f"""
                    MERGE (a:`{target_label}` {{snomed_id: $snomed_id}})
                    MERGE (rec:RecommendationNode {{rule_unique_id: $rule_key}})
                    MERGE (rec)-[r:{relation}]->(a)
                    """,
                    snomed_id=snomed_id,
                    rule_key=str(rule_key),
                )


def _infer_recommendation_props(
    concepts: List[Dict[str, Any]],
) -> Dict[str, Optional[str]]:
    for concept in concepts:
        logic_structured = concept.get("logic_structured") or {}
        strength = logic_structured.get("strength")
        level = logic_structured.get("level")
        direction = logic_structured.get("direction")
        if strength or level or direction:
            return {
                "class": strength,
                "level": level,
                "direction": direction,
            }
    return {"class": None, "level": None, "direction": None}


def _recommendation_relation(logic_structured: Dict[str, Any]) -> str:
    direction = (logic_structured.get("direction") or "").upper()
    if direction in {"NEGATIVE", "CONTRAINDICATED"}:
        return "CONTRAINDICATES_USAGE"
    return "RECOMMENDS_USAGE"


@click.command()
@click.option(
    "--index-path",
    default="/prj/doctoral_letters/guide/data/grounding_index.json",
    show_default=True,
    help="Path to grounding_index.json",
)
@click.option(
    "--rules-path",
    default=None,
    help="Optional JSON or JSONL with per-concept rule_id/logic_structured",
)
@click.option("--uri", default=DEFAULT_URI, show_default=True, help="Neo4j URI")
@click.option("--user", default=DEFAULT_AUTH[0], show_default=True, help="Neo4j user")
@click.option(
    "--password", default=DEFAULT_AUTH[1], show_default=True, help="Neo4j password"
)
def main(
    index_path: str, rules_path: Optional[str], uri: str, user: str, password: str
) -> None:
    if not os.path.exists(index_path):
        raise FileNotFoundError(f"Grounding index not found: {index_path}")

    entries = _load_grounding_index(index_path)
    grouped = _group_by_label(entries)
    rules = _load_rules(rules_path) if rules_path else []

    with GraphDatabase.driver(uri, auth=(user, password)) as driver:
        driver.verify_connectivity()
        with driver.session() as session:
            for label, rows in grouped.items():
                _merge_concepts(session, label, rows)

            if rules:
                grouped_rules: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
                for item in rules:
                    rule_id = item.get("rule_id")
                    if rule_id is None:
                        continue
                    chunk_id = (
                        item.get("chunk_id")
                        or item.get("source_id")
                        or item.get("source_context")
                        or "global"
                    )
                    unique_key = f"{chunk_id}_{rule_id}"
                    grouped_rules[unique_key].append(item)
                _create_rule_nodes(session, grouped_rules)


if __name__ == "__main__":
    main()
