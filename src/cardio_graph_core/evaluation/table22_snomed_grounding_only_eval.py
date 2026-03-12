import argparse
import json
import os
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Tuple

from cardio_graph_core.extraction.guideline_graph_builder import GuidelineGraphBuilder


def _read_gold_items(gold_path: Path, deduplicate: bool = True) -> List[Dict[str, str]]:
    payload = json.loads(gold_path.read_text(encoding="utf-8"))
    tables = payload.get("tables") or []
    items: List[Dict[str, str]] = []

    for table in tables:
        table_id = table.get("table_id")
        for row_idx, row in enumerate(table.get("data") or [], start=1):
            row_id = f"t{table_id}_row_{row_idx:02d}"
            for rule in row.get("rules") or []:
                for side_name, side_value in (
                    ("condition", "conditions"),
                    ("action", "actions"),
                ):
                    for concept in rule.get(side_value) or []:
                        term = (
                            concept.get("entity_standardized_candidate")
                            or concept.get("entity_original")
                            or ""
                        ).strip()
                        role = (concept.get("role") or "").strip()
                        gold_snomed_id = str(concept.get("snomed_id") or "").strip()
                        if not term or not role or not gold_snomed_id:
                            continue
                        items.append(
                            {
                                "row_id": row_id,
                                "side": side_name,
                                "term": term,
                                "role": role,
                                "gold_snomed_id": gold_snomed_id,
                            }
                        )

    if not deduplicate:
        return items

    seen = set()
    deduped: List[Dict[str, str]] = []
    for item in items:
        key = (
            item["row_id"],
            item["side"],
            item["role"].strip().lower(),
            item["term"].strip().lower(),
            item["gold_snomed_id"],
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def _evaluate(
    items: List[Dict[str, str]], mode: str, model: str, node: str, port: int
) -> Dict[str, Any]:
    os.environ["CARDIO_GRAPH_GROUNDING_ENABLE_VECTOR"] = (
        "true" if mode == "vector" else "false"
    )

    builder = GuidelineGraphBuilder(model=model, node=node, port=port)
    role_total = Counter()
    role_hits = Counter()
    predictions: List[Dict[str, Any]] = []

    for item in items:
        concept_id, preferred_term, score = builder._search_best_concept(
            item["term"], item["role"]
        )
        pred_snomed_id = "" if concept_id is None else str(concept_id)
        hit = pred_snomed_id == item["gold_snomed_id"]
        role_total[item["role"]] += 1
        if hit:
            role_hits[item["role"]] += 1
        predictions.append(
            {
                **item,
                "pred_snomed_id": pred_snomed_id,
                "pred_preferred_term": preferred_term,
                "pred_score": score,
                "hit": hit,
            }
        )

    total = len(predictions)
    hits = sum(1 for row in predictions if row["hit"])
    accuracy = (hits / total) if total else 0.0

    per_role = {
        role: {
            "n": role_total[role],
            "hits": role_hits[role],
            "accuracy": (
                (role_hits[role] / role_total[role]) if role_total[role] else 0.0
            ),
        }
        for role in sorted(role_total)
    }

    if builder.vector_retriever:
        builder.vector_retriever.close()
    if builder.snomed_explorer:
        builder.snomed_explorer.close()

    return {
        "mode": mode,
        "total": total,
        "hits": hits,
        "accuracy": accuracy,
        "per_role": per_role,
        "predictions": predictions,
    }


def _prediction_key(row: Dict[str, Any]) -> Tuple[str, str, str, str, str]:
    return (
        str(row.get("row_id") or ""),
        str(row.get("side") or ""),
        str(row.get("role") or ""),
        str(row.get("term") or ""),
        str(row.get("gold_snomed_id") or ""),
    )


def _compare_results(current: Dict[str, Any], baseline_path: Path) -> Dict[str, Any]:
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    baseline_predictions = baseline.get("predictions") or []
    current_predictions = current.get("predictions") or []

    base_map = {_prediction_key(row): row for row in baseline_predictions}
    curr_map = {_prediction_key(row): row for row in current_predictions}

    improved = []
    regressed = []

    for key, base_row in base_map.items():
        curr_row = curr_map.get(key)
        if not curr_row:
            continue
        base_hit = bool(base_row.get("hit"))
        curr_hit = bool(curr_row.get("hit"))

        if (not base_hit) and curr_hit:
            improved.append(
                {
                    "row_id": curr_row.get("row_id"),
                    "term": curr_row.get("term"),
                    "role": curr_row.get("role"),
                    "gold_snomed_id": curr_row.get("gold_snomed_id"),
                    "baseline_pred_snomed_id": base_row.get("pred_snomed_id"),
                    "current_pred_snomed_id": curr_row.get("pred_snomed_id"),
                }
            )
        elif base_hit and (not curr_hit):
            regressed.append(
                {
                    "row_id": curr_row.get("row_id"),
                    "term": curr_row.get("term"),
                    "role": curr_row.get("role"),
                    "gold_snomed_id": curr_row.get("gold_snomed_id"),
                    "baseline_pred_snomed_id": base_row.get("pred_snomed_id"),
                    "current_pred_snomed_id": curr_row.get("pred_snomed_id"),
                }
            )

    return {
        "baseline_path": str(baseline_path),
        "baseline_mode": baseline.get("mode"),
        "baseline_accuracy": baseline.get("accuracy"),
        "current_mode": current.get("mode"),
        "current_accuracy": current.get("accuracy"),
        "delta_accuracy": float(current.get("accuracy") or 0.0)
        - float(baseline.get("accuracy") or 0.0),
        "improved_count": len(improved),
        "regressed_count": len(regressed),
        "improved_examples": improved[:50],
        "regressed_examples": regressed[:50],
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--gold-path",
        type=Path,
        default=Path(
            "/prj/doctoral_letters/guide/data/evaluation/table_22_manual_snomed.json"
        ),
    )
    parser.add_argument("--mode", choices=("non-vector", "vector"), required=True)
    parser.add_argument("--model", default="Qwen3next")
    parser.add_argument("--node", default="g5")
    parser.add_argument("--port", type=int, default=11435)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--no-deduplicate", action="store_true")
    parser.add_argument("--compare-with", type=Path, default=None)
    parser.add_argument("--vector-uri", default="bolt://neo4j-dev3.internal:7687")
    parser.add_argument("--vector-user", default="neo4j")
    parser.add_argument("--vector-index", default="snomed_term_embeddings_4096")
    parser.add_argument("--embedding-model", default="Qwen3embed")
    parser.add_argument("--embedding-node", default="g4")
    parser.add_argument("--embedding-port", default="11434")
    return parser


def main() -> int:
    args = _build_parser().parse_args()

    os.environ["CARDIO_GRAPH_GROUNDING_VECTOR_URI"] = args.vector_uri
    os.environ["CARDIO_GRAPH_GROUNDING_VECTOR_USER"] = args.vector_user
    os.environ["CARDIO_GRAPH_GROUNDING_VECTOR_INDEX"] = args.vector_index
    os.environ["CARDIO_GRAPH_GROUNDING_EMBEDDING_MODEL"] = args.embedding_model
    os.environ["CARDIO_GRAPH_GROUNDING_EMBEDDING_NODE"] = args.embedding_node
    os.environ["CARDIO_GRAPH_GROUNDING_EMBEDDING_PORT"] = str(args.embedding_port)

    items = _read_gold_items(
        gold_path=args.gold_path,
        deduplicate=not args.no_deduplicate,
    )
    mode = "vector" if args.mode == "vector" else "non_vector"

    result = _evaluate(
        items=items,
        mode=mode,
        model=args.model,
        node=args.node,
        port=args.port,
    )

    output = {
        "gold_path": str(args.gold_path),
        "deduplicated": not args.no_deduplicate,
        "settings": {
            "model": args.model,
            "node": args.node,
            "port": args.port,
            "vector_uri": args.vector_uri,
            "vector_user": args.vector_user,
            "vector_index": args.vector_index,
            "embedding_model": args.embedding_model,
            "embedding_node": args.embedding_node,
            "embedding_port": args.embedding_port,
        },
        **result,
    }

    if args.compare_with is not None and args.compare_with.exists():
        output["comparison"] = _compare_results(output, args.compare_with)

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")

    print(f"mode={output['mode']}")
    print(f"gold_items={output['total']}")
    print(f"hits={output['hits']}")
    print(f"accuracy={output['accuracy']:.6f}")
    print(f"output_json={args.output_json}")
    if output.get("comparison"):
        comp = output["comparison"]
        print(f"baseline={comp['baseline_mode']} {comp['baseline_accuracy']:.6f}")
        print(f"delta_accuracy={comp['delta_accuracy']:.6f}")
        print(
            "improved={} regressed={}".format(
                comp["improved_count"], comp["regressed_count"]
            )
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
