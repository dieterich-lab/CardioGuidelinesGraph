import os
import re
import json
from neo4j import GraphDatabase

from datetime import datetime
from collections import defaultdict
from typing import Any, Dict, List
from cardio_graph_core.query.clients import create_client_registry
from cardio_graph_core.query.question import triple_batch
from cardio_graph_core.query.query_helper_functions import (
    entities_to_list,
    decision_main,
    is_negated_text,
)
from cardio_graph_core.query.baml_client.sync_client import b

URI = "bolt://neo4j-dev2.internal:7687"
# AUTH = (os.environ.get("NEO4J_USR"), os.environ.get("NEO4J_PASS"))
AUTH = ("neo4j", "KWCeoHhkJYAiFa3XTZZZLC77bHiZ5xzj")
INDEX_NAME = "node_vector_index"
host = "10.250.135.153:11430"  # gpu g4
model = "Qwen14b"  # gpu g4
node = "g4"


def get_patient_info_from_question(question, cr):
    entities = b.PatientInfoExtractor(question, {"client_registry": cr})
    entity_list = entities_to_list(entities)
    return entity_list


def decompose_entity(entity: str) -> list[str]:
    e = _norm_text(entity)
    out = []

    if "chronic coronary syndrome" in e or "ccs" in e:
        out.append("chronic coronary syndrome")

    if "surgically eligible" in e:
        out.append("surgically eligible")

    if "high surgical risk" in e:
        out.append("high surgical risk")

    if "multivessel" in e or "multi vessel" in e or "multi-vessel" in e:
        out.append("multivessel disease")

    if "three-vessel" in e or "triple vessel" in e:
        out.append("three-vessel disease")

    if "two-vessel" in e:
        out.append("two-vessel disease")

    if "proximal lad" in e:
        out.append("proximal LAD")

    if "left main stem" in e:
        out.append("left main stem disease")

    return list(dict.fromkeys(out or [entity]))


def hybrid_search_input_nodes(entity_list, host, URI=URI, AUTH=AUTH):
    matched_nodes = []
    seen = set()

    for entity in entity_list:
        if is_negated_text(entity):
            print(f"\nSkipping negated entity: {entity}")
            continue
        subqueries = decompose_entity(entity)

        for subq in subqueries:
            print(f"\nSearching for entity: {subq}")

            filtered = (
                decision_main(
                    URI=URI,
                    AUTH=AUTH,
                    entity=subq,
                    host=host,
                )
                or []
            )

            for i, g in enumerate(filtered, start=1):
                entity_name = g.get("entity") or "-"
                standardized = g.get("entity_standardized_candidate") or "-"
                original_examples = (
                    ", ".join(g.get("entity_original_examples", [])) or "-"
                )
                questions = ", ".join(g.get("questions", [])[:5]) or "-"
                contexts = ", ".join(g.get("contexts", [])[:3]) or "-"

                print(f"Plausibility Check {i}:")
                print(f"Entity             : {entity_name}")
                print(f"Original examples  : {original_examples}")
                print(f"Standardized       : {standardized}")
                print(f"Questions          : {questions}")

                found_node = (
                    f"Standardized candidate: {standardized}\n"
                    f"Entity: {entity_name}\n"
                    f"Original examples: {original_examples}\n"
                    f"Questions: {questions}\n"
                    f"Contexts: {contexts}"
                )

                # is_match = b.EntityCorrector(
                #     found_node=found_node,
                #     original=entity,
                # )
                is_match = True
                if is_match:
                    matched_node = (
                        g.get("entity_standardized_candidate")
                        or g.get("entity")
                        or entity
                    )

                    dedup_key = (
                        _norm_text(entity),
                        _norm_text(
                            g.get("entity_standardized_candidate")
                            or g.get("entity")
                            or subq
                        ),
                    )
                    if dedup_key not in seen:
                        matched_nodes.append(
                            {
                                "query_entity": entity,
                                "matched_node": matched_node,
                                "group": g,
                            }
                        )
                        seen.add(dedup_key)

    return matched_nodes


def parse_decision_position(decision_id: str) -> Dict[str, Any]:
    """
    Parse decision_id like:
      table_17_manual_1.3:row_01:rule_01::g2::s2

    Returns:
      {
        "logic_group": "g2",
        "step": 2
      }
    """
    m = re.search(r"::g(?P<group>\d+)::s(?P<step>\d+)$", decision_id or "")
    if not m:
        return {"logic_group": "g0", "step": None}

    return {
        "logic_group": f"g{m.group('group')}",
        "step": int(m.group("step")),
    }


def fetch_rule_subgraphs(
    driver, matched_nodes: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    matched_nodes is expected to come from your first hybrid search step, e.g.
    [
        {
            "query_entity": "PCI",
            "matched_node": "Percutaneous coronary revascularization",
            "group": {...collapsed decision group...}
        },
        ...
    ]
    """
    rule_ids = sorted(
        {
            rid
            for item in matched_nodes
            for rid in item.get("group", {}).get("rule_ids", [])
            if rid
        }
    )

    if not rule_ids:
        return []

    cypher = """
    UNWIND $rule_ids AS rid

    CALL {
        WITH rid
        MATCH (d:DecisionNode {rule_unique_id: rid})
        OPTIONAL MATCH (d)-[cond_rel:CHECKS_FOR|EVALUATES]->(c)
        RETURN collect(DISTINCT {
            decision_id: d.decision_id,
            rule_unique_id: d.rule_unique_id,
            question: d.question,
            operator: d.operator,
            threshold: d.threshold,
            unit: d.unit,
            context: d.context,
            entity: d.entity,
            entity_original: d.entity_original,
            entity_standardized_candidate: d.entity_standardized_candidate,
            logic_type: d.logic_type,
            concept_rel_type: CASE WHEN cond_rel IS NULL THEN NULL ELSE type(cond_rel) END,
            concept: CASE
                WHEN c IS NULL THEN NULL
                ELSE {
                    snomed_id: c.snomed_id,
                    name: coalesce(c.preferred_term, c.entity_standardized_candidate, c.name, c.entity),
                    entity: c.entity,
                    entity_original: c.entity_original,
                    entity_standardized_candidate: c.entity_standardized_candidate,
                    target_label: c.target_label,
                    labels: labels(c)
                }
            END
        }) AS decisions
    }

    CALL {
        WITH rid
        MATCH (d1:DecisionNode {rule_unique_id: rid})-[r:LEADS_TO]->(d2:DecisionNode {rule_unique_id: rid})
        RETURN collect(DISTINCT {
            from_decision_id: d1.decision_id,
            to_decision_id: d2.decision_id,
            condition_met: r.condition_met
        }) AS decision_edges
    }

    CALL {
        WITH rid
        MATCH (d:DecisionNode {rule_unique_id: rid})-[r:RESULTS_IN]->(rec:RecommendationNode {rule_unique_id: rid})
        OPTIONAL MATCH (rec)-[:MENTIONED_IN]->(src:GuidelineSource)
        RETURN collect(DISTINCT {
            from_decision_id: d.decision_id,
            condition_met: r.condition_met,
            recommendation: {
                rule_unique_id: rec.rule_unique_id,
                strength: rec.strength,
                level: rec.level,
                direction: rec.direction,
                full_text: rec.full_text,
                recommendation_type: rec.recommendation_type,
                source: rec.source
            },
            source: CASE
                WHEN src IS NULL THEN NULL
                ELSE {
                    source_key: src.source_key,
                    title: src.title,
                    year: src.year,
                    section: src.section
                }
            END
        }) AS recommendation_links
    }

    CALL {
        WITH rid
        MATCH (rec:RecommendationNode {rule_unique_id: rid})-[act:RECOMMENDS_USAGE|RECOMMENDS_PROCEDURE|CONTRAINDICATES]->(a)
        RETURN collect(DISTINCT {
            relation_type: type(act),
            context: act.context,
            logic_type: act.logic_type,
            logic_group: act.logic_group,
            action_order: act.action_order,
            action_concept: {
                snomed_id: a.snomed_id,
                name: coalesce(a.preferred_term, a.entity_standardized_candidate, a.name, a.entity),
                entity: a.entity,
                entity_original: a.entity_original,
                entity_standardized_candidate: a.entity_standardized_candidate,
                target_label: a.target_label,
                labels: labels(a)
            }
        }) AS actions
    }

    RETURN
        rid AS rule_unique_id,
        decisions,
        decision_edges,
        recommendation_links,
        actions
    """

    with driver.session() as session:
        rows = session.run(cypher, {"rule_ids": rule_ids})
        rules = [dict(r) for r in rows]

    # enrich decisions with parsed logic_group / step
    for rule in rules:
        for d in rule["decisions"]:
            pos = parse_decision_position(d["decision_id"])
            d["logic_group"] = pos["logic_group"]
            d["step"] = pos["step"]

    return rules


def _norm_text(s: str) -> str:
    if s is None:
        return ""
    return re.sub(r"\s+", " ", str(s).strip().lower())


def build_evidence_index(
    step0_evidence: List[Dict[str, Any]],
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Index evidence by standardized_concept.
    """
    idx = defaultdict(list)
    for ev in step0_evidence:
        key = _norm_text(ev.get("standardized_concept"))
        if key:
            idx[key].append(ev)
    return dict(idx)


def _to_float(x):
    if x is None:
        return None
    try:
        return float(str(x).replace(",", "."))
    except Exception:
        return None


def compare_numeric(patient_value, operator, threshold):
    if patient_value is None or threshold is None or operator is None:
        return False

    if operator == ">":
        return patient_value > threshold
    if operator == ">=":
        return patient_value >= threshold
    if operator == "<":
        return patient_value < threshold
    if operator == "<=":
        return patient_value <= threshold
    if operator in {"=", "=="}:
        return patient_value == threshold
    if operator in {"!=", "<>"}:
        return patient_value != threshold

    return False


def units_compatible(patient_unit, rule_unit):
    """
    Minimal first version.
    Later you can add conversions, e.g. mg <-> g, mmol/L <-> mg/dL.
    """
    if not rule_unit and not patient_unit:
        return True
    if not rule_unit:
        return True
    if not patient_unit:
        return False
    return _norm_text(patient_unit) == _norm_text(rule_unit)


def _to_float(x):
    if x is None:
        return None
    try:
        return float(str(x).replace(",", ".").strip())
    except Exception:
        return None


def normalize_operator(op: str) -> str:
    if op is None:
        return ""

    op = str(op).strip()

    mapping = {
        "≤": "<=",
        "≥": ">=",
        "=": "==",
        "==": "==",
        "!=": "!=",
        "<>": "!=",
        "<": "<",
        ">": ">",
        "<=": "<=",
        ">=": ">=",
        "PRESENT": "PRESENT",
        "ABSENT": "ABSENT",
    }

    upper = op.upper()
    if upper in {"PRESENT", "ABSENT"}:
        return upper

    return mapping.get(op, op)


def units_compatible(patient_unit, rule_unit):
    if not rule_unit and not patient_unit:
        return True
    if not rule_unit:
        return True
    if not patient_unit:
        return False
    return _norm_text(patient_unit) == _norm_text(rule_unit)


def compare_numeric(patient_value, operator, threshold):
    operator = normalize_operator(operator)

    if patient_value is None or threshold is None or not operator:
        return False

    if operator == ">":
        return patient_value > threshold
    if operator == ">=":
        return patient_value >= threshold
    if operator == "<":
        return patient_value < threshold
    if operator == "<=":
        return patient_value <= threshold
    if operator == "==":
        return patient_value == threshold
    if operator == "!=":
        return patient_value != threshold

    return False


def evaluate_decision_node(decision, evidence_index):
    concept_name = (
        decision.get("concept", {}).get("entity_standardized_candidate")
        or decision.get("entity_standardized_candidate")
        or decision.get("concept", {}).get("entity")
        or decision.get("entity")
    )
    concept_key = _norm_text(concept_name)

    raw_operator = decision.get("operator")
    operator = normalize_operator(raw_operator)
    threshold = _to_float(decision.get("threshold"))
    rule_unit = decision.get("unit")

    candidate_evidence = evidence_index.get(concept_key, [])

    result = {
        "decision_id": decision.get("decision_id"),
        "rule_unique_id": decision.get("rule_unique_id"),
        "logic_group": decision.get("logic_group"),
        "step": decision.get("step"),
        "logic_type": decision.get("logic_type"),
        "concept": concept_name,
        "context": decision.get("context"),
        "operator": raw_operator,
        "threshold": decision.get("threshold"),
        "unit": decision.get("unit"),
        "truth": False,
        "matched_evidence": [],
        "reason": None,
    }

    # 1) pure presence / absence
    if operator == "PRESENT":
        result["truth"] = len(candidate_evidence) > 0
        result["matched_evidence"] = candidate_evidence
        result["reason"] = (
            "concept present in step 0 evidence"
            if result["truth"]
            else "concept not present in step 0 evidence"
        )
        return result

    if operator == "ABSENT":
        result["truth"] = len(candidate_evidence) == 0
        result["reason"] = (
            "concept absent from step 0 evidence"
            if result["truth"]
            else "concept was retrieved in step 0 evidence"
        )
        return result

    # 2) numeric comparison
    numeric_ops = {">", ">=", "<", "<=", "==", "!="}
    looks_numeric = (
        operator in numeric_ops or threshold is not None or rule_unit is not None
    )

    if looks_numeric:
        matched = []
        for ev in candidate_evidence:
            if ev.get("present") is False:
                continue

            patient_value = _to_float(ev.get("value"))
            patient_unit = ev.get("unit")

            if patient_value is None:
                continue

            if not units_compatible(patient_unit, rule_unit):
                continue

            if compare_numeric(patient_value, operator, threshold):
                matched.append(ev)

        result["truth"] = len(matched) > 0
        result["matched_evidence"] = matched

        if matched:
            result["reason"] = "numeric comparison satisfied"
        else:
            result["reason"] = (
                f"numeric comparison not satisfied "
                f"(operator={operator}, threshold={threshold}, unit={rule_unit or '-'})"
            )

        return result

    # 3) no fallback-to-presence for numeric-like nodes
    result["truth"] = len(candidate_evidence) > 0
    result["matched_evidence"] = candidate_evidence
    result["reason"] = "fallback presence evaluation for non-numeric node"
    return result


def evaluate_rule(
    rule_bundle: Dict[str, Any], step0_evidence: List[Dict[str, Any]]
) -> Dict[str, Any]:
    evidence_index = build_evidence_index(step0_evidence)

    evaluated_decisions = [
        evaluate_decision_node(d, evidence_index)
        for d in rule_bundle.get("decisions", [])
    ]

    groups = defaultdict(list)
    for d in evaluated_decisions:
        groups[d["logic_group"]].append(d)

    group_results = []
    for group_id, nodes in sorted(groups.items()):
        and_nodes = [n for n in nodes if (n.get("logic_type") or "").upper() == "AND"]
        or_nodes = [n for n in nodes if (n.get("logic_type") or "").upper() == "OR"]
        null_nodes = [
            n for n in nodes if (n.get("logic_type") or "").upper() not in {"AND", "OR"}
        ]

        and_ok = all(n["truth"] for n in and_nodes) if and_nodes else True
        or_ok = any(n["truth"] for n in or_nodes) if or_nodes else True
        null_ok = all(n["truth"] for n in null_nodes) if null_nodes else True

        group_true = and_ok and or_ok and null_ok

        group_results.append(
            {
                "logic_group": group_id,
                "group_true": group_true,
                "and_nodes": and_nodes,
                "or_nodes": or_nodes,
                "null_nodes": null_nodes,
            }
        )

    rule_true = all(g["group_true"] for g in group_results) if group_results else False

    rec_links = rule_bundle.get("recommendation_links", [])
    recommendation = rec_links[0]["recommendation"] if rec_links else None
    source = rec_links[0]["source"] if rec_links else None

    fulfilled = [d for d in evaluated_decisions if d["truth"]]
    unfulfilled = [d for d in evaluated_decisions if not d["truth"]]

    return {
        "rule_unique_id": rule_bundle.get("rule_unique_id"),
        "rule_true": rule_true,
        "recommendation": recommendation,
        "source": source,
        "actions": rule_bundle.get("actions", []),
        "evaluated_decisions": evaluated_decisions,
        "group_results": group_results,
        "fulfilled_conditions": fulfilled,
        "unfulfilled_conditions": unfulfilled,
    }


def summarize_rule_evaluation(rule_result: Dict[str, Any]) -> None:
    print("=" * 100)
    print(f"RULE: {rule_result.get('rule_unique_id')}")
    print(f"RULE TRUE: {rule_result.get('rule_true')}")

    rec = rule_result.get("recommendation") or {}
    print(f"Recommendation type : {rec.get('recommendation_type') or '-'}")
    print(f"Direction           : {rec.get('direction') or '-'}")
    print(f"Strength            : {rec.get('strength') or '-'}")
    print(f"Level               : {rec.get('level') or '-'}")
    print(f"Full text           : {rec.get('full_text') or '-'}")

    src = rule_result.get("source") or {}
    if src:
        print(
            f"Source              : {src.get('title') or '-'} ({src.get('year') or '-'})"
        )
        print(f"Section             : {src.get('section') or '-'}")

    print("\nActions:")
    for a in sorted(
        rule_result.get("actions", []),
        key=lambda x: (x.get("action_order") is None, x.get("action_order")),
    ):
        concept = a.get("action_concept", {})
        action_name = (
            concept.get("entity_original")
            or concept.get("entity_standardized_candidate")
            or concept.get("entity")
            or concept.get("name")
            or "-"
        )
        print(
            f"  - {a.get('relation_type')}: {action_name} "
            f"(context={a.get('context') or '-'}, "
            f"logic_type={a.get('logic_type') or '-'}, "
            f"logic_group={a.get('logic_group') or '-'}, "
            f"action_order={a.get('action_order')})"
        )

    print("\nFulfilled conditions:")
    for d in rule_result.get("fulfilled_conditions", []):
        print(
            f"  + {d.get('concept') or '-'} "
            f"[operator={d.get('operator') or '-'}, "
            f"context={d.get('context') or '-'}, "
            f"group={d.get('logic_group') or '-'}, "
            f"step={d.get('step') or '-'}] "
            f"-> {d.get('reason')}"
        )

    print("\nUnfulfilled conditions:")
    for d in rule_result.get("unfulfilled_conditions", []):
        print(
            f"  - {d.get('concept') or '-'} "
            f"[operator={d.get('operator') or '-'}, "
            f"context={d.get('context') or '-'}, "
            f"group={d.get('logic_group') or '-'}, "
            f"step={d.get('step') or '-'}] "
            f"-> {d.get('reason')}"
        )

    print("\nGroup results:")
    for g in rule_result.get("group_results", []):
        print(f"  * {g['logic_group']}: {g['group_true']}")


def retrieve_and_evaluate_rules(driver, matched_nodes, step0_evidence):
    rule_bundles = fetch_rule_subgraphs(driver, matched_nodes)

    results = []
    for rule in rule_bundles:
        evaluated = evaluate_rule(rule, step0_evidence)
        results.append(evaluated)

    return results


def build_step0_evidence_from_matches(matched_nodes):
    """
    Convert first-stage grounded patient concept matches into machine-readable evidence.
    Later enrich numeric mentions via BAML.
    """
    evidence = []

    for item in matched_nodes:
        original_entity = item.get("query_entity")
        group = item.get("group", {})

        standardized = group.get("entity_standardized_candidate") or group.get("entity")

        evidence.append(
            {
                "original_text": original_entity,
                "standardized_concept": standardized,
                "present": True,
                "value": None,
                "unit": None,
                "comparator": None,
            }
        )

    return evidence


def _safe_get(obj, key, default=None):
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def serialize_group_for_baml(group: Dict[str, Any], max_raw_hits: int = 8) -> str:
    """
    Compact text representation of a matched decision-node group for BAML.
    """
    lines = []
    lines.append(f"Entity: {group.get('entity') or '-'}")
    lines.append(f"Standardized: {group.get('entity_standardized_candidate') or '-'}")
    lines.append(
        f"Original examples: {', '.join(group.get('entity_original_examples', [])) or '-'}"
    )
    lines.append(f"Contexts: {', '.join(group.get('contexts', [])) or '-'}")
    lines.append(f"Operators: {', '.join(group.get('operators', [])) or '-'}")
    lines.append(
        f"Thresholds: {', '.join(map(str, group.get('thresholds', []))) or '-'}"
    )
    lines.append(f"Units: {', '.join(group.get('units', [])) or '-'}")
    lines.append(f"Logic types: {', '.join(group.get('logic_types', [])) or '-'}")
    lines.append(f"Rule count: {group.get('rule_count') or 0}")
    lines.append(f"Decision count: {group.get('decision_count') or 0}")

    raw_hits = group.get("raw_hits", [])[:max_raw_hits]
    if raw_hits:
        lines.append("Sample decision hits:")
        for hit in raw_hits:
            lines.append(
                "  - "
                f"decision_id={hit.get('decision_id')}, "
                f"operator={hit.get('operator')}, "
                f"threshold={hit.get('threshold')}, "
                f"unit={hit.get('unit')}, "
                f"context={hit.get('context')}, "
                f"logic_type={hit.get('logic_type')}, "
                f"question={hit.get('question')}"
            )

    return "\n".join(lines)


def build_step0_evidence_from_matches(
    matched_nodes: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    step0_evidence = []

    for item in matched_nodes:
        original_entity = item.get("query_entity")
        matched_node = item.get("matched_node")
        group = item.get("group", {})

        if is_negated_text(original_entity):
            print(f"Skipping negated matched node for: {original_entity}")
            continue

        found_decision_nodes = serialize_group_for_baml(group)

        try:
            structured = b.PatientEvidenceFormatter(
                original_entity=original_entity,
                found_decision_nodes=found_decision_nodes,
            )

            assertion = _safe_get(structured, "assertion", "AFFIRMED")
            present = _safe_get(structured, "present", True)

            if str(assertion).upper() == "NEGATED" or present is False:
                print(f"Dropping negated evidence: {original_entity}")
                continue

            evidence = {
                "original_text": _safe_get(
                    structured, "original_text", original_entity
                ),
                "standardized_concept": _safe_get(
                    structured, "standardized_concept", matched_node
                ),
                "present": True,
                "value": _safe_get(structured, "value"),
                "unit": _safe_get(structured, "unit"),
                "comparator": _safe_get(structured, "comparator"),
                "query_entity": original_entity,
                "matched_node": matched_node,
            }
        except Exception as e:
            print(
                f"PatientEvidenceFormatter failed for '{original_entity}', using fallback: {e}"
            )
            evidence = {
                "original_text": original_entity,
                "standardized_concept": matched_node,
                "present": True,
                "value": None,
                "unit": None,
                "comparator": None,
                "query_entity": original_entity,
                "matched_node": matched_node,
            }

        step0_evidence.append(evidence)

    return step0_evidence


def print_step0_evidence(step0_evidence: List[Dict[str, Any]]) -> None:
    print("\n" + "=" * 100)
    print("STEP 0 PATIENT EVIDENCE")
    print("=" * 100)
    for i, ev in enumerate(step0_evidence, start=1):
        print(f"[{i}] {ev.get('original_text') or '-'}")
        print(f"    standardized_concept : {ev.get('standardized_concept') or '-'}")
        print(f"    present              : {ev.get('present')}")
        print(f"    comparator           : {ev.get('comparator') or '-'}")
        print(f"    value                : {ev.get('value') or '-'}")
        print(f"    unit                 : {ev.get('unit') or '-'}")
    print("=" * 100)


def print_matched_nodes(matched_nodes: List[Dict[str, Any]]) -> None:
    print("\n" + "=" * 100)
    print("MATCHED INPUT NODES")
    print("=" * 100)
    for i, item in enumerate(matched_nodes, start=1):
        group = item.get("group", {})
        print(f"[{i}] Query Entity   : {item.get('query_entity') or '-'}")
        print(f"    Matched Node  : {item.get('matched_node') or '-'}")
        print(f"    Rule count    : {group.get('rule_count') or 0}")
        print(f"    Decision count: {group.get('decision_count') or 0}")
        print(f"    Contexts      : {', '.join(group.get('contexts', [])) or '-'}")
    print("=" * 100)


def main(
    question: str,
    URI,
    AUTH,
    host: str = "http://localhost:11434",
):
    """
    End-to-end pipeline:
      1. extract patient entities from question
      2. ground them via hybrid decision-node retrieval
      3. build step-0 patient evidence
      4. fetch full rule subgraphs by rule_unique_id
      5. evaluate each rule against step-0 evidence
      6. print fulfilled recommendations

    Returns a dict with all intermediate artifacts.
    """
    print("\n" + "=" * 100)
    print("QUESTION")
    print("=" * 100)
    print(question)

    # 1) extract patient-side entities
    extracted = b.PatientInfoExtractor(input=question)
    entity_list = entities_to_list(extracted)

    print("\n" + "=" * 100)
    print("EXTRACTED PATIENT ENTITIES")
    print("=" * 100)
    for i, ent in enumerate(entity_list, start=1):
        print(f"[{i}] {ent}")

    if not entity_list:
        print("No entities extracted.")
        return {
            "question": question,
            "extracted_entities": [],
            "matched_nodes": [],
            "step0_evidence": [],
            "rule_bundles": [],
            "rule_evaluations": [],
            "true_rules": [],
        }

    # 2) ground entities to decision-node anchor groups
    matched_nodes = hybrid_search_input_nodes(
        entity_list=entity_list,
        host=host,
        URI=URI,
        AUTH=AUTH,
    )

    print_matched_nodes(matched_nodes)

    if not matched_nodes:
        print("No grounded decision-node matches found.")
        return {
            "question": question,
            "extracted_entities": entity_list,
            "matched_nodes": [],
            "step0_evidence": [],
            "rule_bundles": [],
            "rule_evaluations": [],
            "true_rules": [],
        }

    # 3) convert matched patient entities into structured step-0 evidence
    step0_evidence = build_step0_evidence_from_matches(matched_nodes)
    print_step0_evidence(step0_evidence)

    # 4) fetch all rule subgraphs connected to the matched rules
    driver = GraphDatabase.driver(URI, auth=AUTH)
    try:
        rule_bundles = fetch_rule_subgraphs(driver, matched_nodes)

        print("\n" + "=" * 100)
        print("RETRIEVED RULE SUBGRAPHS")
        print("=" * 100)
        print(f"Total rules retrieved: {len(rule_bundles)}")

        # 5) evaluate rules
        rule_evaluations = []
        for rule_bundle in rule_bundles:
            result = evaluate_rule(rule_bundle, step0_evidence)
            rule_evaluations.append(result)

        # optional ranking: true rules first, then by strength of fulfilled conditions
        rule_evaluations.sort(
            key=lambda x: (
                not x.get("rule_true", False),
                -len(x.get("fulfilled_conditions", [])),
                len(x.get("unfulfilled_conditions", [])),
            )
        )

        true_rules = [r for r in rule_evaluations if r.get("rule_true")]

        print("\n" + "=" * 100)
        print("TRUE RULES / RECOMMENDATIONS")
        print("=" * 100)
        if not true_rules:
            print("No rule evaluated to TRUE.")
        else:
            for r in true_rules:
                summarize_rule_evaluation(r)

        print("\n" + "=" * 100)
        print("ALL RULE EVALUATIONS")
        print("=" * 100)
        for r in rule_evaluations:
            summarize_rule_evaluation(r)

        return {
            "question": question,
            "extracted_entities": entity_list,
            "matched_nodes": matched_nodes,
            "step0_evidence": step0_evidence,
            "rule_bundles": rule_bundles,
            "rule_evaluations": rule_evaluations,
            "true_rules": true_rules,
        }

    finally:
        driver.close()


def _write_rule_block(f, rule, idx):
    rec = rule.get("recommendation") or {}
    src = rule.get("source") or {}
    actions = rule.get("actions", [])
    fulfilled = rule.get("fulfilled_conditions", [])
    unfulfilled = rule.get("unfulfilled_conditions", [])
    groups = rule.get("group_results", [])

    f.write("=" * 100 + "\n")
    f.write(f"TRUE RULE #{idx}\n")
    f.write("=" * 100 + "\n")
    f.write(f"Rule ID              : {rule.get('rule_unique_id') or '-'}\n")
    f.write(f"Rule True            : {rule.get('rule_true')}\n")
    f.write(f"Recommendation Type  : {rec.get('recommendation_type') or '-'}\n")
    f.write(f"Direction            : {rec.get('direction') or '-'}\n")
    f.write(f"Strength             : {rec.get('strength') or '-'}\n")
    f.write(f"Level                : {rec.get('level') or '-'}\n")
    f.write(f"Full Text            : {rec.get('full_text') or '-'}\n")
    f.write(f"Source Title         : {src.get('title') or '-'}\n")
    f.write(f"Source Year          : {src.get('year') or '-'}\n")
    f.write(f"Source Section       : {src.get('section') or '-'}\n")

    f.write("\nActions:\n")
    if actions:
        for a in sorted(
            actions,
            key=lambda x: (x.get("action_order") is None, x.get("action_order")),
        ):
            concept = a.get("action_concept", {}) or {}
            action_name = (
                concept.get("entity_original")
                or concept.get("entity_standardized_candidate")
                or concept.get("entity")
                or concept.get("name")
                or "-"
            )
            f.write(
                f"  - {a.get('relation_type') or '-'}: {action_name} "
                f"(context={a.get('context') or '-'}, "
                f"logic_type={a.get('logic_type') or '-'}, "
                f"logic_group={a.get('logic_group') or '-'}, "
                f"action_order={a.get('action_order')})\n"
            )
    else:
        f.write("  - none\n")

    f.write("\nFulfilled conditions:\n")
    if fulfilled:
        for d in fulfilled:
            f.write(
                f"  + {d.get('concept') or '-'} "
                f"[operator={d.get('operator') or '-'}, "
                f"threshold={d.get('threshold') or '-'}, "
                f"unit={d.get('unit') or '-'}, "
                f"context={d.get('context') or '-'}, "
                f"group={d.get('logic_group') or '-'}, "
                f"step={d.get('step') or '-'}] "
                f"-> {d.get('reason') or '-'}\n"
            )
    else:
        f.write("  - none\n")

    f.write("\nUnfulfilled conditions:\n")
    if unfulfilled:
        for d in unfulfilled:
            f.write(
                f"  - {d.get('concept') or '-'} "
                f"[operator={d.get('operator') or '-'}, "
                f"threshold={d.get('threshold') or '-'}, "
                f"unit={d.get('unit') or '-'}, "
                f"context={d.get('context') or '-'}, "
                f"group={d.get('logic_group') or '-'}, "
                f"step={d.get('step') or '-'}] "
                f"-> {d.get('reason') or '-'}\n"
            )
    else:
        f.write("  - none\n")

    f.write("\nGroup results:\n")
    if groups:
        for g in groups:
            f.write(f"  * {g.get('logic_group') or '-'} -> {g.get('group_true')}\n")
    else:
        f.write("  - none\n")

    f.write("\n")


def _write_question_result(f, question, result, question_idx):
    f.write("\n" + "#" * 100 + "\n")
    f.write(f"TEST CASE #{question_idx}\n")
    f.write("#" * 100 + "\n")
    f.write(f"Question: {question}\n\n")

    extracted = result.get("extracted_entities", [])
    matched = result.get("matched_nodes", [])
    evidence = result.get("step0_evidence", [])
    true_rules = result.get("true_rules", [])
    all_rules = result.get("rule_evaluations", [])

    f.write(f"Extracted entities ({len(extracted)}):\n")
    for ent in extracted:
        f.write(f"  - {ent}\n")

    f.write(f"\nMatched nodes ({len(matched)}):\n")
    if matched:
        for m in matched:
            f.write(
                f"  - query='{m.get('query_entity') or '-'}' "
                f"-> matched='{m.get('matched_node') or '-'}'\n"
            )
    else:
        f.write("  - none\n")

    f.write(f"\nStep 0 evidence ({len(evidence)}):\n")
    if evidence:
        for ev in evidence:
            f.write(
                f"  - original='{ev.get('original_text') or '-'}', "
                f"standardized='{ev.get('standardized_concept') or '-'}', "
                f"present={ev.get('present')}, "
                f"comparator={ev.get('comparator') or '-'}, "
                f"value={ev.get('value') if ev.get('value') is not None else '-'}, "
                f"unit={ev.get('unit') or '-'}\n"
            )
    else:
        f.write("  - none\n")

    f.write(f"\nSummary:\n")
    f.write(f"  Retrieved rules     : {len(all_rules)}\n")
    f.write(f"  True rules          : {len(true_rules)}\n")

    if true_rules:
        f.write("\nTRUE RULE DETAILS\n")
        for idx, rule in enumerate(true_rules, start=1):
            _write_rule_block(f, rule, idx)
    else:
        f.write("\nNo rule evaluated to TRUE for this question.\n")


def test_battery(
    test_inputs,
    URI,
    AUTH,
    host,
    output_path="test_battery_results.txt",
):
    """
    Runs all test questions through the pipeline and writes a human-readable report to a txt file.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    all_results = []

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("GUIDELINE REASONING TEST BATTERY REPORT\n")
        f.write("=" * 100 + "\n")
        f.write(f"Created: {timestamp}\n")
        f.write(f"Number of test questions: {len(test_inputs)}\n")
        f.write("=" * 100 + "\n")

        for question_idx, question in enumerate(test_inputs, start=1):
            print("\n" + "#" * 100)
            print(f"TEST QUESTION #{question_idx}: {question}")
            print("#" * 100)

            try:
                result = main(
                    URI=URI,
                    AUTH=AUTH,
                    question=question,
                    host=host,
                )

                all_results.append(
                    {
                        "question": question,
                        "success": True,
                        "result": result,
                    }
                )

                _write_question_result(f, question, result, question_idx)

            except Exception as e:
                all_results.append(
                    {
                        "question": question,
                        "success": False,
                        "error": str(e),
                    }
                )

                f.write("\n" + "#" * 100 + "\n")
                f.write(f"TEST CASE #{question_idx}\n")
                f.write("#" * 100 + "\n")
                f.write(f"Question: {question}\n\n")
                f.write("ERROR:\n")
                f.write(f"{e}\n")

        # overall summary
        success_count = sum(1 for r in all_results if r["success"])
        fail_count = len(all_results) - success_count
        total_true_rules = sum(
            len(r["result"].get("true_rules", [])) for r in all_results if r["success"]
        )

        f.write("\n" + "=" * 100 + "\n")
        f.write("OVERALL SUMMARY\n")
        f.write("=" * 100 + "\n")
        f.write(f"Successful runs      : {success_count}\n")
        f.write(f"Failed runs          : {fail_count}\n")
        f.write(f"Total true rules     : {total_true_rules}\n")

    print(f"\nSaved test battery report to: {output_path}")
    return all_results


test_inputs = [
    "what should we do for a ccs patient with lvef 40%% and functionally significant left main stem stenosis?",
    "what is recommended for a ccs patient with lvef 50%% and functionally significant three-vessel disease?",
    "what should we recommend for a ccs patient with lvef 45%% and functionally significant two-vessel disease involving the proximal lad?",
    "what should we do for a ccs patient with lvef 30%?",
    "what is recommended for a surgically eligible ccs patient with multivessel cad and lvef 30%?",
    "what can be considered for a ccs patient with functionally significant multivessel disease, lvef 35%, and high surgical risk?",
    "what should we do for a ccs patient with persistent angina despite guideline-directed medical therapy?",
    "what is recommended when pci is being performed on anatomically complex lesions such as left main stem disease?",
    "what should we measure for a patient undergoing intervention with multivessel disease?",
    "what is recommended at the end of myocardial revascularization in a patient with chronic coronary syndrome?",
]
q4 = [
    "what is recommended at the end of myocardial revascularization in a patient with chronic coronary syndrome and no indication for oral anticoagulation?"
]
# test_inputs = ["what should we do with a ccs patient with has had an MI?"]
if __name__ == "__main__":
    # cr = create_client_registry(model_name=model, node=node, port=30)
    # entity_list = get_patient_info_from_question(
    #     "Patient with chronic coronary syndrome, prior myocardial infarction, and who has tolerated dual antiplatelet therapy for 1 year",
    #     cr,
    # )
    # print(entity_list)
    # matched = hybrid_search_input_nodes(entity_list, host, URI=URI, AUTH=AUTH)
    # print("\nMatched Nodes:")
    # for match in matched:
    #     print(f"Query Entity: {match['query_entity']}")
    #     print(f"Matched Node: {match['matched_node']}")
    #     print(f"Group Info: {match['group']}")
    #     print("-" * 60)
    # result = main(
    #     URI=URI,
    #     AUTH=AUTH,
    #     question="what should we do with a ccs patient with has had an MI?",
    #     host=host,
    # )
    # for rule in result["true_rules"]:
    #     summarize_rule_evaluation(rule)
    # results = test_battery(
    #     test_inputs=triple_batch[2],
    #     URI=URI,
    #     AUTH=AUTH,
    #     host=host,
    #     output_path="/prj/doctoral_letters/guide/data/query_test_output/table_17_b2_redo.txt",
    # )
    decision_main(
        URI=URI,
        entity="dual antiplatelet therapy",
        AUTH=("neo4j", "KWCeoHhkJYAiFa3XTZZZLC77bHiZ5xzj"),
        host="10.250.135.153:11430",
    )
    # num = 0
    # for batch in triple_batch:
    #     num += 1
    #     batch_name = f"batch_{num}"
    #     result = test_battery(
    #         test_inputs=batch,
    #         URI=URI,
    #         AUTH=AUTH,
    #         host=host,
    #         output_path=f"/prj/doctoral_letters/guide/data/query_test_output/{batch_name}.txt",
    #     )
