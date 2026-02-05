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
from cardio_graph.snomedct_utils.snomed_query import SnomedExplorer


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


def _add_snomed_hierarchy(session, entries: List[Dict[str, Any]]) -> None:
    """Add SNOMED CT IS_A relationships for concepts in the index."""
    explorer = SnomedExplorer()
    IS_A_TYPE_ID = 116680003
    snomed_ids = {str(entry["snomed_id"]) for entry in entries if entry.get("snomed_id")}
    
    for snomed_id in snomed_ids:
        try:
            relationships = explorer.get_relationships(int(snomed_id))
            for rel in relationships:
                rel_type = rel.get("typeid") or rel.get("typeId")
                dest_id = rel.get("destinationid") or rel.get("destinationId")
                if rel_type == IS_A_TYPE_ID and dest_id is not None:
                    session.run(
                        """
                        MERGE (c:Concept {snomed_id: $child_id})
                        MERGE (p:Concept {snomed_id: $parent_id})
                        MERGE (c)-[:IS_A]->(p)
                        """,
                        child_id=snomed_id,
                        parent_id=str(dest_id),
                    )
        except Exception as e:
            print(f"Error adding hierarchy for {snomed_id}: {e}")


def _create_rule_nodes(session, grouped_rules: Dict[str, List[Dict[str, Any]]]) -> None:
    for rule_key, concepts in grouped_rules.items():
        rec_props = _infer_recommendation_props(concepts)
        source_info = (
            concepts[0].get("source_context")
            or concepts[0].get("chunk_id")
            or "Unknown Source"
        )
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
            concept_name = concept.get("entity_standardized_candidate") or concept.get(
                "entity_original"
            )
            entity_original = concept.get("entity_original")

            if role in {"Condition", "ClinicalParameter"}:
                if snomed_id:
                    session.run(
                        f"""
                        MERGE (c:`{target_label}` {{snomed_id: $snomed_id}})
                        MERGE (dec:DecisionNode {{rule_unique_id: $rule_key, concept: $concept}})
                        SET dec.operator = $operator,
                            dec.threshold = $threshold,
                            dec.unit = $unit,
                            dec.condition_context = $condition_context,
                            dec.entity_original = $entity_original
                        MERGE (c)-[:HAS_RULE]->(dec)
                        MERGE (dec)-[:RESULTS_IN {{condition_met: true}}]->(rec)
                        """,
                        snomed_id=snomed_id,
                        rule_key=str(rule_key),
                        concept=concept_name,
                        entity_original=entity_original,
                        operator=logic_structured.get("operator"),
                        threshold=logic_structured.get("threshold"),
                        unit=logic_structured.get("unit"),
                        condition_context=logic_structured.get("condition_context"),
                    )
                else:
                    session.run(
                        """
                        MERGE (u:UnresolvedConcept {name: $name, target_label: $target_label})
                        SET u.entity_original = $entity_original
                        MERGE (dec:DecisionNode {rule_unique_id: $rule_key, concept: $concept})
                        SET dec.operator = $operator,
                            dec.threshold = $threshold,
                            dec.unit = $unit,
                            dec.condition_context = $condition_context,
                            dec.entity_original = $entity_original
                        MERGE (u)-[:HAS_RULE]->(dec)
                        MERGE (dec)-[:RESULTS_IN {condition_met: true}]->(rec)
                        """,
                        name=concept_name,
                        target_label=target_label,
                        entity_original=entity_original,
                        rule_key=str(rule_key),
                        concept=concept_name,
                        operator=logic_structured.get("operator"),
                        threshold=logic_structured.get("threshold"),
                        unit=logic_structured.get("unit"),
                        condition_context=logic_structured.get("condition_context"),
                    )

            if role in {"Medication", "Procedure"}:
                relation = _recommendation_relation(logic_structured)
                if snomed_id:
                    session.run(
                        f"""
                        MERGE (a:`{target_label}` {{snomed_id: $snomed_id}})
                        MERGE (rec:RecommendationNode {{rule_unique_id: $rule_key}})
                        MERGE (rec)-[r:{relation}]->(a)
                        """,
                        snomed_id=snomed_id,
                        rule_key=str(rule_key),
                    )
                else:
                    session.run(
                        f"""
                        MERGE (u:UnresolvedConcept {{name: $name, target_label: $target_label}})
                        SET u.entity_original = $entity_original
                        MERGE (rec:RecommendationNode {{rule_unique_id: $rule_key}})
                        MERGE (rec)-[r:{relation}]->(u)
                        """,
                        name=concept_name,
                        target_label=target_label,
                        entity_original=entity_original,
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
        condition_concepts = []
        action_concepts = []
        for concept in concepts:
            role = (concept.get("role") or "").strip()
            if role in {"Condition", "ClinicalParameter"}:
                condition_concepts.append(concept)
            elif role in {"Medication", "Procedure"}:
                action_concepts.append(concept)

        or_groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for concept in condition_concepts:
            logic_structured = concept.get("logic_structured") or {}
            group = logic_structured.get("logic_group")
            if group:
                or_groups[group].append(concept)

        if or_groups:
            condition_groups = list(or_groups.values())
            group_mode = "OR"
        else:
            condition_groups = [condition_concepts] if condition_concepts else []
            group_mode = "AND"

        for group_index, group in enumerate(condition_groups, start=1):
            previous_decision = None
            for step_index, concept in enumerate(group, start=1):
                role = (concept.get("role") or "").strip()
                logic_structured = concept.get("logic_structured") or {}
                snomed_id = concept.get("snomed_id")
                target_label = concept.get("target_label") or "Concept"
                concept_name = concept.get("entity_standardized_candidate") or concept.get(
                    "entity_original"
                )
                entity_original = concept.get("entity_original")
                logic_type = "SINGLE"
                if len(group) > 1:
                    logic_type = "AND"
                if group_mode == "OR":
                    logic_type = "OR"

                decision_id = f"{rule_key}::g{group_index}::s{step_index}"

                if snomed_id:
                    relation = "CHECKS_FOR" if role == "Condition" else "EVALUATES"
                    session.run(
                        f"""
                        MERGE (c:`{target_label}` {{snomed_id: $snomed_id}})
                        MERGE (dec:DecisionNode {{rule_unique_id: $rule_key, decision_id: $decision_id}})
                        SET dec.concept = $concept,
                            dec.operator = $operator,
                            dec.threshold = $threshold,
                            dec.unit = $unit,
                            dec.condition_context = $condition_context,
                            dec.entity_original = $entity_original,
                            dec.logic_type = $logic_type
                        MERGE (dec)-[r:{relation}]->(c)
                        """,
                        snomed_id=snomed_id,
                        rule_key=str(rule_key),
                        decision_id=decision_id,
                        concept=concept_name,
                        operator=logic_structured.get("operator"),
                        threshold=logic_structured.get("threshold"),
                        unit=logic_structured.get("unit"),
                        condition_context=logic_structured.get("condition_context"),
                        entity_original=entity_original,
                        logic_type=logic_type,
                    )
                else:
                    relation = "CHECKS_FOR" if role == "Condition" else "EVALUATES"
                    session.run(
                        f"""
                        MERGE (u:UnresolvedConcept {{name: $name, target_label: $target_label}})
                        SET u.entity_original = $entity_original
                        MERGE (dec:DecisionNode {{rule_unique_id: $rule_key, decision_id: $decision_id}})
                        SET dec.concept = $concept,
                            dec.operator = $operator,
                            dec.threshold = $threshold,
                            dec.unit = $unit,
                            dec.condition_context = $condition_context,
                            dec.entity_original = $entity_original,
                            dec.logic_type = $logic_type
                        MERGE (dec)-[r:{relation}]->(u)
                        """,
                        name=concept_name,
                        target_label=target_label,
                        entity_original=entity_original,
                        rule_key=str(rule_key),
                        decision_id=decision_id,
                        concept=concept_name,
                        operator=logic_structured.get("operator"),
                        threshold=logic_structured.get("threshold"),
                        unit=logic_structured.get("unit"),
                        condition_context=logic_structured.get("condition_context"),
                        logic_type=logic_type,
                    )

                if previous_decision:
                    session.run(
                        """
                        MATCH (prev:DecisionNode {rule_unique_id: $rule_key, decision_id: $prev_id})
                        MATCH (curr:DecisionNode {rule_unique_id: $rule_key, decision_id: $curr_id})
                        MERGE (prev)-[:LEADS_TO {condition_met: true}]->(curr)
                        """,
                        rule_key=str(rule_key),
                        prev_id=previous_decision,
                        curr_id=decision_id,
                    )

                previous_decision = decision_id

            if previous_decision:
                session.run(
                    """
                    MATCH (dec:DecisionNode {rule_unique_id: $rule_key, decision_id: $decision_id})
                    MATCH (rec:RecommendationNode {rule_unique_id: $rule_key})
                    MERGE (dec)-[:RESULTS_IN {condition_met: true}]->(rec)
                    """,
                    rule_key=str(rule_key),
                    decision_id=previous_decision,
                )

        for concept in action_concepts:
            logic_structured = concept.get("logic_structured") or {}
            snomed_id = concept.get("snomed_id")
            target_label = concept.get("target_label") or "Concept"
            concept_name = concept.get("entity_standardized_candidate") or concept.get(
                "entity_original"
            )
            entity_original = concept.get("entity_original")
            relation = _recommendation_relation(logic_structured)
            if snomed_id:
                session.run(
                    f"""
                    MERGE (a:`{target_label}` {{snomed_id: $snomed_id}})
                    MERGE (rec:RecommendationNode {{rule_unique_id: $rule_key}})
                    MERGE (rec)-[r:{relation}]->(a)
                    """,
                    snomed_id=snomed_id,
                    rule_key=str(rule_key),
                )
            else:
                session.run(
                    f"""
                    MERGE (u:UnresolvedConcept {{name: $name, target_label: $target_label}})
                    SET u.entity_original = $entity_original
                    MERGE (rec:RecommendationNode {{rule_unique_id: $rule_key}})
                    MERGE (rec)-[r:{relation}]->(u)
                    """,
                    name=concept_name,
                    target_label=target_label,
                    entity_original=entity_original,
                    rule_key=str(rule_key),
                )
