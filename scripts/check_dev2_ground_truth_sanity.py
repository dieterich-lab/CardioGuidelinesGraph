#!/usr/bin/env python3

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from neo4j import GraphDatabase


def _load_secrets_env() -> None:
    secrets_path = Path(
        os.environ.get(
            "CARDIO_GRAPH_SECRETS_ENV_PATH",
            str(Path.home() / ".config" / "cardio_graph" / "secrets.env"),
        )
    )
    if not secrets_path.is_file():
        return
    for raw_line in secrets_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _resolve_auth(
    cli_user: Optional[str], cli_password: Optional[str]
) -> tuple[str, str]:
    user = cli_user or (
        os.environ.get("CARDIO_GRAPH_GROUNDING_VECTOR_USER")
        or os.environ.get("CARDIO_GRAPH_GROUNDING_USER")
        or os.environ.get("CARDIO_GRAPH_NEO4J_USER")
        or "neo4j"
    )
    password = cli_password or (
        os.environ.get("CARDIO_GRAPH_GROUNDING_VECTOR_PASSWORD")
        or os.environ.get("CARDIO_GRAPH_GROUNDING_PASSWORD")
        or os.environ.get("CARDIO_GRAPH_NEO4J_PASSWORD")
        or os.environ.get("NEO4J_PASSWORD")
        or ""
    )
    if not password:
        raise RuntimeError("Missing Neo4j password in CLI args or environment.")
    return user, password


def _rule_id(source_prefix: str, row_number: int, rule_number: int = 1) -> str:
    return f"{source_prefix}:row_{row_number:02d}:rule_{rule_number:02d}"


def _single_int(session, query: str, **params) -> int:
    return int(session.run(query, **params).single()["c"])


def run_checks(
    uri: str,
    user: str,
    password: str,
    table22_source_prefix: str,
    table22_row_probe: int,
) -> Dict[str, Any]:
    report: Dict[str, Any] = {
        "target_uri": uri,
        "table22_source_prefix": table22_source_prefix,
        "table22_row_probe": table22_row_probe,
        "probe_rule_id": _rule_id(table22_source_prefix, table22_row_probe, 1),
    }

    with GraphDatabase.driver(
        uri, auth=(user, password), connection_timeout=8
    ) as driver:
        driver.verify_connectivity()
        report["reachable"] = True

        with driver.session() as session:
            report["node_counts"] = {
                row["label"]: row["c"]
                for row in session.run(
                    "MATCH (n) UNWIND labels(n) AS label RETURN label, count(*) AS c ORDER BY c DESC"
                )
            }

            report["relationship_counts"] = {
                row["type"]: row["c"]
                for row in session.run(
                    "MATCH ()-[r]->() RETURN type(r) AS type, count(*) AS c ORDER BY c DESC"
                )
            }

            report["recommendations_by_source"] = [
                dict(row)
                for row in session.run(
                    """
                    MATCH (r:RecommendationNode)
                    WITH split(r.rule_unique_id, ':row_')[0] AS source, count(*) AS recommendations
                    RETURN source, recommendations
                    ORDER BY source
                    """
                )
            ]

            report["integrity"] = {
                "recs_without_source": _single_int(
                    session,
                    """
                    MATCH (r:RecommendationNode)
                    WHERE NOT (r)-[:MENTIONED_IN]->(:GuidelineSource)
                    RETURN count(r) AS c
                    """,
                ),
                "recs_without_actions": _single_int(
                    session,
                    """
                    MATCH (r:RecommendationNode)
                    WHERE NOT (r)-[:RECOMMENDS_USAGE|RECOMMENDS_PROCEDURE|CONTRAINDICATES]->()
                    RETURN count(r) AS c
                    """,
                ),
                "recs_without_decision_path": _single_int(
                    session,
                    """
                    MATCH (r:RecommendationNode)
                    WHERE NOT (:DecisionNode)-[:RESULTS_IN]->(r)
                    RETURN count(r) AS c
                    """,
                ),
                "decisions_without_concept_link": _single_int(
                    session,
                    """
                    MATCH (d:DecisionNode)
                    WHERE NOT (d)-[:CHECKS_FOR|EVALUATES]->()
                    RETURN count(d) AS c
                    """,
                ),
            }

            probe_rule_id = report["probe_rule_id"]
            report["probe_rule_exists"] = _single_int(
                session,
                "MATCH (r:RecommendationNode {rule_unique_id: $rule_id}) RETURN count(r) AS c",
                rule_id=probe_rule_id,
            )

            report["probe_rule_bundle"] = [
                dict(row)
                for row in session.run(
                    """
                    MATCH (rec:RecommendationNode {rule_unique_id: $rule_id})
                    OPTIONAL MATCH (src:GuidelineSource)<-[:MENTIONED_IN]-(rec)
                    OPTIONAL MATCH (dec:DecisionNode)-[:RESULTS_IN]->(rec)
                    WITH rec, src, collect(DISTINCT dec) AS decisions
                    OPTIONAL MATCH (dec2:DecisionNode)-[drel:CHECKS_FOR|EVALUATES]->(cond)
                    WHERE dec2 IN decisions
                    WITH rec, src,
                         [d IN decisions | {decision_id: d.decision_id, question: d.question, operator: d.operator, logic_type: d.logic_type}] AS decision_nodes,
                         collect(DISTINCT {rel_type: type(drel), target: coalesce(cond.entity, cond.entity_standardized_candidate, cond.preferred_term, cond.snomed_id), target_labels: labels(cond)}) AS conditions
                    OPTIONAL MATCH (rec)-[arel:RECOMMENDS_USAGE|RECOMMENDS_PROCEDURE|CONTRAINDICATES]->(act)
                    RETURN rec.rule_unique_id AS rule_id,
                           src.source_key AS source_key,
                           rec.strength AS strength,
                           rec.level AS level,
                           rec.direction AS direction,
                           decision_nodes,
                           conditions,
                           collect(DISTINCT {rel_type: type(arel), target: coalesce(act.entity, act.entity_standardized_candidate, act.preferred_term, act.snomed_id), target_labels: labels(act)}) AS actions
                    """,
                    rule_id=probe_rule_id,
                )
            ]

    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--uri", default="bolt://neo4j-dev2.internal:7687")
    parser.add_argument("--user", default=None)
    parser.add_argument("--password", default=None)
    parser.add_argument("--table22-source-prefix", default="table_22_manual_1.3")
    parser.add_argument("--table22-row-probe", type=int, default=3)
    parser.add_argument("--out-json", default=None)
    args = parser.parse_args()

    _load_secrets_env()
    user, password = _resolve_auth(args.user, args.password)

    report = run_checks(
        uri=args.uri,
        user=user,
        password=password,
        table22_source_prefix=args.table22_source_prefix,
        table22_row_probe=args.table22_row_probe,
    )

    if args.out_json:
        out_path = Path(args.out_json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
