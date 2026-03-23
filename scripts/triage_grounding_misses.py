#!/usr/bin/env python3

import argparse
import csv
import json
import os
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from neo4j import GraphDatabase
except Exception:
    GraphDatabase = None


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", (text or "").lower())).strip()


def _tokens(text: str) -> set[str]:
    normalized = _normalize(text)
    return {token for token in normalized.split() if len(token) > 2}


def _token_jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _contains_relation(a: str, b: str) -> bool:
    if not a or not b:
        return False
    return a in b or b in a


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_password() -> str:
    for key in (
        "CARDIO_GRAPH_GROUNDING_VECTOR_PASSWORD",
        "CARDIO_GRAPH_GROUNDING_PASSWORD",
        "CARDIO_GRAPH_NEO4J_PASSWORD",
        "NEO4J_PASSWORD",
    ):
        value = os.environ.get(key)
        if value:
            return value
    secrets_path = Path(
        os.environ.get(
            "CARDIO_GRAPH_SECRETS_ENV_PATH",
            str(Path.home() / ".config/cardio_graph/secrets.env"),
        )
    )
    if not secrets_path.exists():
        return ""
    secrets: Dict[str, str] = {}
    for line in secrets_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        secrets[key.strip()] = value.strip()
    for key in (
        "CARDIO_GRAPH_GROUNDING_VECTOR_PASSWORD",
        "CARDIO_GRAPH_GROUNDING_PASSWORD",
        "CARDIO_GRAPH_NEO4J_PASSWORD",
        "NEO4J_PASSWORD",
    ):
        value = secrets.get(key)
        if value:
            return value
    return ""


def _taxonomy_distance(
    neo4j_driver: Any, gold_id: str, pred_id: str, max_hops: int
) -> Optional[int]:
    if not neo4j_driver:
        return None
    try:
        gid = int(gold_id)
        pid = int(pred_id)
    except (TypeError, ValueError):
        return None
    if gid == pid:
        return 0

    bounded_hops = max(1, min(int(max_hops), 8))
    query = f"""
    MATCH (g:SnomedTerm {{concept_id:$gold}}), (p:SnomedTerm {{concept_id:$pred}})
    OPTIONAL MATCH path = shortestPath((g)-[:IS_A*..{bounded_hops}]-(p))
    RETURN CASE WHEN path IS NULL THEN NULL ELSE length(path) END AS hops
    """
    with neo4j_driver.session() as session:
        row = session.run(query, gold=gid, pred=pid).single()
        if not row:
            return None
        hops = row.get("hops")
        if hops is None:
            return None
        return int(hops)


def _classify_miss(
    gold_id: str,
    gold_term: str,
    pred_id: str,
    pred_term: str,
    score: float,
    taxonomy_hops: Optional[int],
) -> Tuple[str, str, str]:
    if not pred_id or pred_id == "<empty>":
        return (
            "obvious_tune",
            "no_prediction_returned",
            "tune_retrieval_or_rerank",
        )

    g_norm = _normalize(gold_term)
    p_norm = _normalize(pred_term)
    g_tokens = _tokens(gold_term)
    p_tokens = _tokens(pred_term)
    jaccard = _token_jaccard(g_tokens, p_tokens)

    if g_norm and p_norm and g_norm == p_norm and gold_id != pred_id:
        return (
            "annotation_review",
            "same_normalized_concept_text_different_id",
            "review_gold_annotation_or_accept_equivalent",
        )

    if taxonomy_hops is not None and taxonomy_hops <= 2 and jaccard >= 0.35:
        return (
            "tricky_near_miss",
            f"taxonomy_close_hops_{taxonomy_hops}",
            "consider_soft_accept_or_refine_granularity_rules",
        )

    if jaccard >= 0.65 or _contains_relation(g_norm, p_norm):
        return (
            "tricky_near_miss",
            "high_lexical_overlap",
            "tune_disambiguation_and_role_specific_penalties",
        )

    if score >= 0.9 and jaccard < 0.35:
        return (
            "obvious_tune",
            "high_confidence_semantic_mismatch",
            "add_hard_negative_and_penalty_for_confuser",
        )

    return (
        "obvious_tune",
        "low_semantic_overlap",
        "tune_candidate_generation_or_constraints",
    )


def _format_summary_table(rows: List[Dict[str, Any]]) -> str:
    lines: List[str] = []
    lines.append("# Grounding Miss Triage")
    lines.append("")
    lines.append("## Bucket Counts")
    lines.append("")
    bucket_counter = Counter(row["triage_bucket"] for row in rows)
    lines.append("| Bucket | Count |")
    lines.append("|---|---:|")
    for bucket, count in bucket_counter.most_common():
        lines.append(f"| {bucket} | {count} |")

    lines.append("")
    lines.append("## Top Obvious Tune Targets")
    lines.append("")
    lines.append("| Row | Role | Source Term | Gold | Pred | Score | Reason |")
    lines.append("|---|---|---|---|---|---:|---|")
    obvious = [row for row in rows if row["triage_bucket"] == "obvious_tune"]
    for row in obvious[:15]:
        lines.append(
            "| {row_id} | {role} | {term} | {gold_id} ({gold_term}) | {pred_id} ({pred_term}) | {score:.3f} | {reason} |".format(
                row_id=row.get("row_id", ""),
                role=row.get("role", ""),
                term=row.get("term", ""),
                gold_id=row.get("gold_snomed_id", ""),
                gold_term=row.get("gold_concept_term", ""),
                pred_id=row.get("pred_snomed_id", "") or "<empty>",
                pred_term=row.get("pred_concept_term", "") or "<empty>",
                score=float(row.get("pred_score") or 0.0),
                reason=row.get("triage_reason", ""),
            )
        )

    lines.append("")
    lines.append("## Annotation Review Candidates")
    lines.append("")
    lines.append("| Row | Role | Source Term | Gold | Pred | Hops | Reason |")
    lines.append("|---|---|---|---|---|---:|---|")
    review = [row for row in rows if row["triage_bucket"] == "annotation_review"]
    for row in review[:15]:
        hops = row.get("taxonomy_hops")
        hops_text = "" if hops is None else str(hops)
        lines.append(
            "| {row_id} | {role} | {term} | {gold_id} ({gold_term}) | {pred_id} ({pred_term}) | {hops} | {reason} |".format(
                row_id=row.get("row_id", ""),
                role=row.get("role", ""),
                term=row.get("term", ""),
                gold_id=row.get("gold_snomed_id", ""),
                gold_term=row.get("gold_concept_term", ""),
                pred_id=row.get("pred_snomed_id", "") or "<empty>",
                pred_term=row.get("pred_concept_term", "") or "<empty>",
                hops=hops_text,
                reason=row.get("triage_reason", ""),
            )
        )

    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--eval-json", required=True, type=Path)
    parser.add_argument("--out-csv", required=True, type=Path)
    parser.add_argument("--out-md", required=True, type=Path)
    parser.add_argument("--with-taxonomy", action="store_true")
    parser.add_argument("--max-taxonomy-hops", type=int, default=3)
    parser.add_argument("--neo4j-uri", default="bolt://neo4j-dev3.internal:7687")
    parser.add_argument("--neo4j-user", default="neo4j")
    args = parser.parse_args()

    payload = _load_json(args.eval_json)
    misses = [row for row in (payload.get("predictions") or []) if not row.get("hit")]

    neo4j_driver = None
    if args.with_taxonomy and GraphDatabase is not None:
        password = _load_password()
        if password:
            neo4j_driver = GraphDatabase.driver(
                args.neo4j_uri, auth=(args.neo4j_user, password), encrypted=False
            )

    triaged_rows: List[Dict[str, Any]] = []
    for row in misses:
        gold_id = str(row.get("gold_snomed_id") or "")
        pred_id = str(row.get("pred_snomed_id") or "")
        gold_term = str(row.get("gold_concept_term") or "")
        pred_term = str(
            row.get("pred_concept_term") or row.get("pred_preferred_term") or ""
        )
        score = float(row.get("pred_score") or 0.0)

        taxonomy_hops = None
        if neo4j_driver and gold_id and pred_id:
            taxonomy_hops = _taxonomy_distance(
                neo4j_driver=neo4j_driver,
                gold_id=gold_id,
                pred_id=pred_id,
                max_hops=args.max_taxonomy_hops,
            )

        bucket, reason, action = _classify_miss(
            gold_id=gold_id,
            gold_term=gold_term,
            pred_id=pred_id,
            pred_term=pred_term,
            score=score,
            taxonomy_hops=taxonomy_hops,
        )

        triaged = dict(row)
        triaged["pred_concept_term"] = pred_term
        triaged["taxonomy_hops"] = taxonomy_hops
        triaged["triage_bucket"] = bucket
        triaged["triage_reason"] = reason
        triaged["suggested_action"] = action
        triaged_rows.append(triaged)

    if neo4j_driver:
        neo4j_driver.close()

    args.out_csv.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "row_id",
        "side",
        "role",
        "term",
        "gold_snomed_id",
        "gold_concept_term",
        "pred_snomed_id",
        "pred_concept_term",
        "pred_score",
        "taxonomy_hops",
        "triage_bucket",
        "triage_reason",
        "suggested_action",
    ]

    with args.out_csv.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in triaged_rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})

    report = _format_summary_table(triaged_rows)
    args.out_md.write_text(report, encoding="utf-8")

    bucket_counter = Counter(row["triage_bucket"] for row in triaged_rows)
    print(f"eval_json={args.eval_json}")
    print(f"misses={len(triaged_rows)}")
    print("bucket_counts=" + json.dumps(bucket_counter, sort_keys=True))
    print(f"out_csv={args.out_csv}")
    print(f"out_md={args.out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
