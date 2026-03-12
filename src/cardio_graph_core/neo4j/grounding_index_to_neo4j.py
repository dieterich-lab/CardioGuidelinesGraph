#!/usr/bin/env python3
"""
Load grounding_index.json into Neo4j and (optionally) create rule logic nodes.

- Concept nodes are MERGED by snomed_id and labeled by target_label.
- Rule/decision/recommendation nodes are created only if a rules file is provided.
"""

import json
import os
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import click
import yaml
from neo4j import GraphDatabase

from cardio_graph_core.neo4j.feedneo4jdb import DEFAULT_URI, DEFAULT_USER
from cardio_graph_core.snomedct.snomed_query import SnomedExplorer

DEFAULT_INDEX_PATH = "/prj/doctoral_letters/guide/data/graph/grounding_index.json"
DEFAULT_RULES_PATH = "/prj/doctoral_letters/guide/data/graph/extracted_rules.jsonl"
DEFAULT_SCHEMA_PATH = str(
    Path(__file__).resolve().parents[3]
    / "config"
    / "cardio_graph_core"
    / "guideline_graph_schema.yaml"
)

REQUIRED_NODE_LABELS = {
    "ClinicalCondition",
    "Medication",
    "ClinicalParameter",
    "Procedure",
    "GuidelineSource",
    "DecisionNode",
    "RecommendationNode",
}

REQUIRED_RELATIONSHIP_TYPES = {
    "EVALUATES",
    "CHECKS_FOR",
    "LEADS_TO",
    "RESULTS_IN",
    "RECOMMENDS_USAGE",
    "CONTRAINDICATES",
    "RECOMMENDS_PROCEDURE",
    "MENTIONED_IN",
}


def _load_graph_schema(schema_path: str) -> Dict[str, Any]:
    with open(schema_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _validate_graph_schema_contract(
    schema: Dict[str, Any], strict: bool = True
) -> None:
    nodes = schema.get("nodes", []) or []
    relationships = schema.get("relationships", []) or []
    node_labels = {node.get("label") for node in nodes if node.get("label")}
    relationship_types = {rel.get("type") for rel in relationships if rel.get("type")}

    missing_labels = sorted(REQUIRED_NODE_LABELS - node_labels)
    missing_relationships = sorted(REQUIRED_RELATIONSHIP_TYPES - relationship_types)
    problems: List[str] = []
    if missing_labels:
        problems.append("Missing node labels in schema: " + ", ".join(missing_labels))
    if missing_relationships:
        problems.append(
            "Missing relationship types in schema: " + ", ".join(missing_relationships)
        )

    if not strict:
        if problems:
            click.echo("Schema warnings:")
            for message in problems:
                click.echo(f"- {message}")
        return

    if problems:
        raise click.ClickException("; ".join(problems))


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
        n.entity = row.entity,
        n.entity_original = row.entity_original,
        n.entity_standardized_candidate = row.entity_standardized_candidate,
        n.target_label = row.target_label,
        n.synonyms = row.synonyms,
        n.drug_class = row.drug_class,
        n.unit = row.unit
    SET n:Concept
    """
    normalized_rows = []
    for row in rows:
        snomed_id = row.get("snomed_id")
        if snomed_id is None:
            continue
        normalized = dict(row)
        normalized["snomed_id"] = str(snomed_id)
        normalized["entity"] = (
            normalized.get("entity")
            or normalized.get("entity_standardized_candidate")
            or normalized.get("preferred_term")
            or normalized.get("entity_original")
        )
        normalized["synonyms"] = (
            normalized.get("synonyms") or normalized.get("alt_names") or []
        )
        normalized["drug_class"] = normalized.get("drug_class")
        normalized["unit"] = normalized.get("unit")
        normalized_rows.append(normalized)

    session.run(query, rows=normalized_rows)

    for row in normalized_rows:
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
    snomed_ids = {
        str(entry["snomed_id"]) for entry in entries if entry.get("snomed_id")
    }

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
                        child_id=str(snomed_id),
                        parent_id=str(dest_id),
                    )
        except Exception as e:
            print(f"Error adding hierarchy for {snomed_id}: {e}")


def _group_rules(
    rules: Iterable[Dict[str, Any]],
) -> Dict[str, List[Dict[str, Any]]]:
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for concept in rules:
        source_key = (
            concept.get("chunk_id")
            or concept.get("source_id")
            or concept.get("source_context")
            or "global"
        )
        rule_key = str(source_key)
        grouped[rule_key].append(concept)
    return grouped


def _extract_concept_fields(concept: Dict[str, Any]) -> Dict[str, Optional[str]]:
    standardized = concept.get("entity_standardized_candidate")
    original = concept.get("entity_original")
    entity = standardized or original
    return {
        "entity": entity,
        "entity_original": original,
        "entity_standardized_candidate": standardized,
    }


def _extract_decision_context(concept: Dict[str, Any]) -> Optional[str]:
    logic_structured = concept.get("logic_structured") or {}
    for candidate in (
        logic_structured.get("context"),
        concept.get("source_context"),
        concept.get("chunk_id"),
    ):
        if candidate is None:
            continue
        value = str(candidate).strip()
        if value:
            return value
    return None


def _infer_year(source_text: Optional[str]) -> Optional[int]:
    if not source_text:
        return None
    match = re.search(r"\b(19|20)\d{2}\b", source_text)
    if not match:
        return None
    try:
        return int(match.group(0))
    except ValueError:
        return None


def _merge_guideline_source(
    session, rule_key: str, concepts: List[Dict[str, Any]]
) -> None:
    first = concepts[0] if concepts else {}
    title = first.get("guideline_title")
    section = first.get("chunk_id") or first.get("source_context") or "Unknown Section"
    source_key = first.get("source_context") or section
    year = _infer_year(title) or _infer_year(source_key)
    session.run(
        """
        MERGE (src:GuidelineSource {source_key: $source_key})
        SET src.title = $title,
            src.year = $year,
            src.section = $section
        MERGE (rec:RecommendationNode {rule_unique_id: $rule_key})
        MERGE (rec)-[:MENTIONED_IN]->(src)
        """,
        source_key=str(source_key),
        title=title,
        year=year,
        section=section,
        rule_key=str(rule_key),
    )


def _create_rule_nodes(session, grouped_rules: Dict[str, List[Dict[str, Any]]]) -> None:
    for rule_key, concepts in grouped_rules.items():
        rec_props = _infer_recommendation_props(concepts)
        source_info = (
            concepts[0].get("source_context")
            or concepts[0].get("chunk_id")
            or "Unknown Source"
        )
        session.run(
            """
            MERGE (rec:RecommendationNode {rule_unique_id: $rule_key})
            SET rec.strength = $strength,
                rec.level = $level,
                rec.direction = $direction,
                rec.full_text = $full_text,
                rec.recommendation_type = $recommendation_type,
                rec.source = $source
            """,
            rule_key=str(rule_key),
            source=source_info,
            **rec_props,
        )
        _merge_guideline_source(session, rule_key, concepts)

        condition_concepts = []
        action_concepts = []
        for concept in concepts:
            role = (concept.get("role") or "").strip()
            side = (concept.get("logic") or "").strip().lower()

            is_condition = (
                role in {"ClinicalCondition", "ClinicalParameter"}
                or side == "condition"
            )
            is_action = role in {"Medication", "Procedure"} or side == "action"

            if is_condition:
                condition_concepts.append(concept)
            elif is_action:
                action_concepts.append(concept)

        ordered_groups: List[Dict[str, Any]] = []
        group_index: Dict[Tuple[str, str], int] = {}
        for concept in condition_concepts:
            logic_structured = concept.get("logic_structured") or {}
            logic_type = (logic_structured.get("logic_type") or "AND").upper()
            group_key = (
                logic_structured.get("logic_group")
                or f"{logic_type.lower()}_{rule_key}"
            )
            key = (group_key, logic_type)
            if key not in group_index:
                group_index[key] = len(ordered_groups)
                ordered_groups.append(
                    {
                        "group_key": group_key,
                        "logic_type": logic_type,
                        "concepts": [],
                    }
                )
            ordered_groups[group_index[key]]["concepts"].append(concept)

        previous_decisions: List[str] = []
        for group_idx, group in enumerate(ordered_groups, start=1):
            logic_type = group["logic_type"]
            concepts_group = group["concepts"]
            if logic_type == "OR":
                new_decisions: List[str] = []
                for step_index, concept in enumerate(concepts_group, start=1):
                    role = (concept.get("role") or "").strip()
                    logic_structured = concept.get("logic_structured") or {}
                    context_value = _extract_decision_context(concept)
                    concept_fields = _extract_concept_fields(concept)
                    snomed_id = concept.get("snomed_id")
                    target_label = concept.get("target_label") or "Concept"
                    concept_name = concept_fields["entity"]
                    entity_original = concept_fields["entity_original"]
                    entity_standardized_candidate = concept_fields[
                        "entity_standardized_candidate"
                    ]
                    decision_id = f"{rule_key}::g{group_idx}::s{step_index}"
                    relation = (
                        "CHECKS_FOR" if role == "ClinicalCondition" else "EVALUATES"
                    )

                    if snomed_id:
                        session.run(
                            f"""
                            MERGE (c:`{target_label}` {{snomed_id: $snomed_id}})
                            SET c.entity = $entity,
                                c.entity_original = $entity_original,
                                c.entity_standardized_candidate = $entity_standardized_candidate,
                                c.name = coalesce(c.name, $entity)
                            MERGE (dec:DecisionNode {{rule_unique_id: $rule_key, decision_id: $decision_id}})
                            SET dec.question = $question,
                                dec.operator = $operator,
                                dec.threshold = $threshold,
                                dec.unit = $unit,
                                dec.context = $context,
                                dec.entity = $entity,
                                dec.entity_original = $entity_original,
                                dec.entity_standardized_candidate = $entity_standardized_candidate,
                                dec.logic_type = $logic_type
                            MERGE (dec)-[r:{relation}]->(c)
                            """,
                            snomed_id=str(snomed_id),
                            rule_key=str(rule_key),
                            decision_id=decision_id,
                            question=concept_name,
                            operator=logic_structured.get("operator"),
                            threshold=logic_structured.get("threshold"),
                            unit=logic_structured.get("unit"),
                            context=context_value,
                            entity=concept_name,
                            entity_original=entity_original,
                            entity_standardized_candidate=entity_standardized_candidate,
                            logic_type=logic_type,
                        )
                    else:
                        session.run(
                            f"""
                            MERGE (u:UnresolvedConcept {{name: $name, target_label: $target_label}})
                            SET u.entity = $entity,
                                u.entity_original = $entity_original,
                                u.entity_standardized_candidate = $entity_standardized_candidate
                            MERGE (dec:DecisionNode {{rule_unique_id: $rule_key, decision_id: $decision_id}})
                            SET dec.question = $question,
                                dec.operator = $operator,
                                dec.threshold = $threshold,
                                dec.unit = $unit,
                                dec.context = $context,
                                dec.entity = $entity,
                                dec.entity_original = $entity_original,
                                dec.entity_standardized_candidate = $entity_standardized_candidate,
                                dec.logic_type = $logic_type
                            MERGE (dec)-[r:{relation}]->(u)
                            """,
                            name=concept_name,
                            target_label=target_label,
                            entity=concept_name,
                            entity_original=entity_original,
                            entity_standardized_candidate=entity_standardized_candidate,
                            rule_key=str(rule_key),
                            decision_id=decision_id,
                            question=concept_name,
                            operator=logic_structured.get("operator"),
                            threshold=logic_structured.get("threshold"),
                            unit=logic_structured.get("unit"),
                            context=context_value,
                            logic_type=logic_type,
                        )

                    if previous_decisions:
                        for prev_id in previous_decisions:
                            session.run(
                                """
                                MATCH (prev:DecisionNode {rule_unique_id: $rule_key, decision_id: $prev_id})
                                MATCH (curr:DecisionNode {rule_unique_id: $rule_key, decision_id: $curr_id})
                                MERGE (prev)-[:LEADS_TO {condition_met: true}]->(curr)
                                """,
                                rule_key=str(rule_key),
                                prev_id=prev_id,
                                curr_id=decision_id,
                            )

                    new_decisions.append(decision_id)

                previous_decisions = new_decisions
                continue

            previous_decision = None
            for step_index, concept in enumerate(concepts_group, start=1):
                role = (concept.get("role") or "").strip()
                logic_structured = concept.get("logic_structured") or {}
                context_value = _extract_decision_context(concept)
                concept_fields = _extract_concept_fields(concept)
                snomed_id = concept.get("snomed_id")
                target_label = concept.get("target_label") or "Concept"
                concept_name = concept_fields["entity"]
                entity_original = concept_fields["entity_original"]
                entity_standardized_candidate = concept_fields[
                    "entity_standardized_candidate"
                ]
                decision_id = f"{rule_key}::g{group_idx}::s{step_index}"
                relation = "CHECKS_FOR" if role == "ClinicalCondition" else "EVALUATES"

                if snomed_id:
                    session.run(
                        f"""
                        MERGE (c:`{target_label}` {{snomed_id: $snomed_id}})
                        SET c.entity = $entity,
                            c.entity_original = $entity_original,
                            c.entity_standardized_candidate = $entity_standardized_candidate,
                            c.name = coalesce(c.name, $entity)
                        MERGE (dec:DecisionNode {{rule_unique_id: $rule_key, decision_id: $decision_id}})
                        SET dec.question = $question,
                            dec.operator = $operator,
                            dec.threshold = $threshold,
                            dec.unit = $unit,
                            dec.context = $context,
                            dec.entity = $entity,
                            dec.entity_original = $entity_original,
                            dec.entity_standardized_candidate = $entity_standardized_candidate,
                            dec.logic_type = $logic_type
                        MERGE (dec)-[r:{relation}]->(c)
                        """,
                        snomed_id=str(snomed_id),
                        rule_key=str(rule_key),
                        decision_id=decision_id,
                        question=concept_name,
                        operator=logic_structured.get("operator"),
                        threshold=logic_structured.get("threshold"),
                        unit=logic_structured.get("unit"),
                        context=context_value,
                        entity=concept_name,
                        entity_original=entity_original,
                        entity_standardized_candidate=entity_standardized_candidate,
                        logic_type=logic_type,
                    )
                else:
                    session.run(
                        f"""
                        MERGE (u:UnresolvedConcept {{name: $name, target_label: $target_label}})
                        SET u.entity = $entity,
                            u.entity_original = $entity_original,
                            u.entity_standardized_candidate = $entity_standardized_candidate
                        MERGE (dec:DecisionNode {{rule_unique_id: $rule_key, decision_id: $decision_id}})
                        SET dec.question = $question,
                            dec.operator = $operator,
                            dec.threshold = $threshold,
                            dec.unit = $unit,
                            dec.context = $context,
                            dec.entity = $entity,
                            dec.entity_original = $entity_original,
                            dec.entity_standardized_candidate = $entity_standardized_candidate,
                            dec.logic_type = $logic_type
                        MERGE (dec)-[r:{relation}]->(u)
                        """,
                        name=concept_name,
                        target_label=target_label,
                        entity=concept_name,
                        entity_original=entity_original,
                        entity_standardized_candidate=entity_standardized_candidate,
                        rule_key=str(rule_key),
                        decision_id=decision_id,
                        question=concept_name,
                        operator=logic_structured.get("operator"),
                        threshold=logic_structured.get("threshold"),
                        unit=logic_structured.get("unit"),
                        context=context_value,
                        logic_type=logic_type,
                    )

                if previous_decisions and step_index == 1:
                    for prev_id in previous_decisions:
                        session.run(
                            """
                            MATCH (prev:DecisionNode {rule_unique_id: $rule_key, decision_id: $prev_id})
                            MATCH (curr:DecisionNode {rule_unique_id: $rule_key, decision_id: $curr_id})
                            MERGE (prev)-[:LEADS_TO {condition_met: true}]->(curr)
                            """,
                            rule_key=str(rule_key),
                            prev_id=prev_id,
                            curr_id=decision_id,
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

            previous_decisions = [previous_decision] if previous_decision else []

        if previous_decisions:
            for prev_id in previous_decisions:
                session.run(
                    """
                    MATCH (dec:DecisionNode {rule_unique_id: $rule_key, decision_id: $decision_id})
                    MATCH (rec:RecommendationNode {rule_unique_id: $rule_key})
                    MERGE (dec)-[:RESULTS_IN {condition_met: true}]->(rec)
                    """,
                    rule_key=str(rule_key),
                    decision_id=prev_id,
                )

        for concept in action_concepts:
            logic_structured = concept.get("logic_structured") or {}
            concept_fields = _extract_concept_fields(concept)
            snomed_id = concept.get("snomed_id")
            target_label = concept.get("target_label") or "Concept"
            concept_name = concept_fields["entity"]
            entity_original = concept_fields["entity_original"]
            entity_standardized_candidate = concept_fields[
                "entity_standardized_candidate"
            ]
            relation = _recommendation_relation(logic_structured, concept.get("role"))
            if snomed_id:
                session.run(
                    f"""
                    MERGE (a:`{target_label}` {{snomed_id: $snomed_id}})
                    SET a.entity = $entity,
                        a.entity_original = $entity_original,
                        a.entity_standardized_candidate = $entity_standardized_candidate,
                        a.name = coalesce(a.name, $entity)
                    MERGE (rec:RecommendationNode {{rule_unique_id: $rule_key}})
                    MERGE (rec)-[r:{relation}]->(a)
                    """,
                    snomed_id=str(snomed_id),
                    entity=concept_name,
                    entity_original=entity_original,
                    entity_standardized_candidate=entity_standardized_candidate,
                    rule_key=str(rule_key),
                )
            else:
                session.run(
                    f"""
                    MERGE (u:UnresolvedConcept {{name: $name, target_label: $target_label}})
                    SET u.entity = $entity,
                        u.entity_original = $entity_original,
                        u.entity_standardized_candidate = $entity_standardized_candidate
                    MERGE (rec:RecommendationNode {{rule_unique_id: $rule_key}})
                    MERGE (rec)-[r:{relation}]->(u)
                    """,
                    name=concept_name,
                    target_label=target_label,
                    entity=concept_name,
                    entity_original=entity_original,
                    entity_standardized_candidate=entity_standardized_candidate,
                    rule_key=str(rule_key),
                )


def _infer_recommendation_props(
    concepts: List[Dict[str, Any]],
) -> Dict[str, Optional[str]]:
    def _normalize_value(value: Optional[str]) -> Optional[str]:
        if value in {None, "", "Unknown", "UNKNOWN"}:
            return None
        return value

    def _extract_props(concept: Dict[str, Any]) -> Dict[str, Optional[str]]:
        logic_structured = concept.get("logic_structured") or {}
        strength = _normalize_value(
            logic_structured.get("strength") or concept.get("strength")
        )
        level = _normalize_value(logic_structured.get("level") or concept.get("level"))
        direction = _normalize_value(
            logic_structured.get("direction") or concept.get("direction")
        )
        role = (concept.get("role") or "").strip()
        recommendation_type = None
        if role == "Medication":
            recommendation_type = "PRESCRIPTION"
        elif role == "Procedure":
            recommendation_type = "DIAGNOSIS"
        full_text = _normalize_value(concept.get("source_context"))
        if strength or level or direction:
            return {
                "strength": strength,
                "level": level,
                "direction": direction,
                "recommendation_type": recommendation_type,
                "full_text": full_text,
            }
        return {}

    action_roles = {"Medication", "Procedure"}
    for concept in concepts:
        role = (concept.get("role") or "").strip()
        if role not in action_roles:
            continue
        props = _extract_props(concept)
        if props:
            return props

    for concept in concepts:
        props = _extract_props(concept)
        if props:
            return props

    fallback_full_text = None
    if concepts:
        fallback_full_text = _normalize_value(concepts[0].get("source_context"))

    return {
        "strength": None,
        "level": None,
        "direction": None,
        "recommendation_type": None,
        "full_text": fallback_full_text,
    }


def _recommendation_relation(
    logic_structured: Dict[str, Any], role: Optional[str]
) -> str:
    direction = (logic_structured.get("direction") or "").strip().upper()
    is_negative = direction == "NEGATIVE"
    role = (role or "").strip()
    if is_negative:
        return "CONTRAINDICATES"
    if role == "Procedure":
        return "RECOMMENDS_PROCEDURE"
    return "RECOMMENDS_USAGE"


@click.command()
@click.option(
    "--index-path",
    default=DEFAULT_INDEX_PATH,
    show_default=True,
    help="Path to grounding_index.json",
)
@click.option(
    "--rules-path",
    default=DEFAULT_RULES_PATH,
    show_default=True,
    help="Path to extracted rules JSON/JSONL (optional)",
)
@click.option(
    "--uri",
    default=DEFAULT_URI,
    show_default=True,
    help="Neo4j bolt URI",
)
@click.option(
    "--user",
    default=DEFAULT_USER,
    show_default=True,
    help="Neo4j username",
)
@click.option(
    "--password",
    default="",
    show_default=False,
    help="Neo4j password",
)
@click.option(
    "--clear-graph/--no-clear-graph",
    default=False,
    show_default=True,
    help="Delete all existing nodes and relationships before loading",
)
@click.option(
    "--add-snomed-hierarchy/--no-add-snomed-hierarchy",
    default=False,
    show_default=True,
    help="Add SNOMED IS_A relationships for concept nodes",
)
@click.option(
    "--schema-path",
    default=DEFAULT_SCHEMA_PATH,
    show_default=True,
    help="Path to guideline graph schema YAML",
)
@click.option(
    "--strict-schema/--no-strict-schema",
    default=True,
    show_default=True,
    help="Fail fast when schema contract is incomplete",
)
def main(
    index_path: str,
    rules_path: Optional[str],
    uri: str,
    user: str,
    password: str,
    clear_graph: bool,
    add_snomed_hierarchy: bool,
    schema_path: str,
    strict_schema: bool,
) -> None:
    schema = _load_graph_schema(schema_path)
    _validate_graph_schema_contract(schema, strict=strict_schema)

    entries = _load_grounding_index(index_path)
    rules = _load_rules(rules_path) if rules_path and os.path.exists(rules_path) else []

    with GraphDatabase.driver(uri, auth=(user, password)) as driver:
        driver.verify_connectivity()
        with driver.session() as session:
            if clear_graph:
                session.run("MATCH (n) DETACH DELETE n")
            grouped = _group_by_label(entries)
            for label, rows in grouped.items():
                _merge_concepts(session, label, rows)
            if add_snomed_hierarchy:
                _add_snomed_hierarchy(session, entries)
            if rules:
                grouped_rules = _group_rules(rules)
                _create_rule_nodes(session, grouped_rules)


if __name__ == "__main__":
    main()
