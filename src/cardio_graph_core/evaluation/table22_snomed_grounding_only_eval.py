import argparse
import csv
import json
import os
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from typing import Any, Dict, List, Optional, Tuple

from cardio_graph_core.grounding.entity_grounding_service import EntityGroundingService


def _compose_context(row: Dict[str, Any], concept: Dict[str, Any]) -> str:
    parts: List[str] = []
    concept_context = concept.get("context")
    if concept_context:
        parts.append(str(concept_context))
    logic_structured = concept.get("logic_structured")
    if logic_structured:
        parts.append(json.dumps(logic_structured, ensure_ascii=False, sort_keys=True))
    recommendation = row.get("recommendation")
    if recommendation:
        parts.append(str(recommendation))
    return " ".join(part.strip() for part in parts if str(part).strip())


def _extract_standardized_candidates(concept: Dict[str, Any]) -> List[Tuple[str, str]]:
    candidates: List[Tuple[str, str]] = []

    direct_term = str(concept.get("entity_standardized_candidate") or "").strip()
    direct_id = str(concept.get("snomed_id") or "").strip()
    if direct_term and direct_id:
        candidates.append((direct_term, direct_id))

    standardized_list = concept.get("entity_standardized_list") or []
    if isinstance(standardized_list, list):
        for candidate in standardized_list:
            if not isinstance(candidate, dict):
                continue
            cand_term = str(
                candidate.get("entity_standardized_candidate") or ""
            ).strip()
            cand_id = str(candidate.get("snomed_id") or "").strip()
            if cand_term and cand_id:
                candidates.append((cand_term, cand_id))

    return candidates


def _iter_tables(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    tables = payload.get("tables")
    if isinstance(tables, list) and tables:
        return [table for table in tables if isinstance(table, dict)]
    if payload.get("data") is not None:
        return [payload]
    return []


def _read_gold_items(
    gold_paths: List[Path], deduplicate: bool = True
) -> List[Dict[str, str]]:
    items: List[Dict[str, str]] = []

    for gold_path in gold_paths:
        payload = json.loads(gold_path.read_text(encoding="utf-8"))
        tables = _iter_tables(payload)

        for table in tables:
            table_id = table.get("table_id", "0")
            for row_idx, row in enumerate(table.get("data") or [], start=1):
                row_id = f"t{table_id}_row_{row_idx:02d}"
                for rule in row.get("rules") or []:
                    for side_name, side_value in (
                        ("condition", "conditions"),
                        ("action", "actions"),
                    ):
                        for concept in rule.get(side_value) or []:
                            role = (concept.get("role") or "").strip()
                            if not role:
                                continue
                            candidates = _extract_standardized_candidates(concept)
                            if not candidates:
                                fallback_term = (
                                    concept.get("entity_standardized_candidate")
                                    or concept.get("entity_original")
                                    or ""
                                ).strip()
                                fallback_id = str(
                                    concept.get("snomed_id") or ""
                                ).strip()
                                if fallback_term and fallback_id:
                                    candidates = [(fallback_term, fallback_id)]
                            for term, gold_snomed_id in candidates:
                                items.append(
                                    {
                                        "row_id": row_id,
                                        "side": side_name,
                                        "term": term,
                                        "role": role,
                                        "gold_snomed_id": gold_snomed_id,
                                        "context": _compose_context(row, concept),
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

    from cardio_graph_core.extraction.guideline_graph_builder import (
        GuidelineGraphBuilder,
    )

    builder = GuidelineGraphBuilder(model=model, node=node, port=port)
    service = EntityGroundingService(builder)
    role_total = Counter()
    role_hits = Counter()
    predictions: List[Dict[str, Any]] = []
    debug_rows: List[Dict[str, Any]] = []
    concept_term_cache: Dict[int, str] = {}
    rank_cutoffs = (1, 3, 5, 10)
    hit_at_k_counts = {k: 0 for k in rank_cutoffs}
    precision_at_k_sums = {k: 0.0 for k in rank_cutoffs}
    gt_ranks: List[int] = []
    gt_found_count = 0

    def _resolve_concept_term(concept_id_value: str) -> str:
        if not concept_id_value:
            return ""
        try:
            concept_id_int = int(concept_id_value)
        except (TypeError, ValueError):
            return ""
        if concept_id_int in concept_term_cache:
            return concept_term_cache[concept_id_int]
        concept_term = service.get_concept_term(concept_id_int) or ""
        concept_term_cache[concept_id_int] = concept_term
        return concept_term

    for item in items:
        concept_id, preferred_term, score, ranked_candidates = service.ground_entity(
            item["term"],
            item["role"],
            query_context=item.get("context") or "",
            return_ranked=True,
        )
        pred_snomed_id = "" if concept_id is None else str(concept_id)
        hit = pred_snomed_id == item["gold_snomed_id"]
        try:
            gold_snomed_id_int = int(item["gold_snomed_id"])
        except (TypeError, ValueError):
            gold_snomed_id_int = None

        gt_rank = None
        for candidate in ranked_candidates:
            if candidate.get("concept_id") == gold_snomed_id_int:
                gt_rank = int(candidate.get("rank") or 0) or None
                break

        pred_rank = None
        pred_candidate: Optional[Dict[str, Any]] = None
        gt_candidate: Optional[Dict[str, Any]] = None
        for candidate in ranked_candidates:
            if concept_id is not None and candidate.get("concept_id") == concept_id:
                pred_rank = int(candidate.get("rank") or 0) or None
                pred_candidate = candidate
            if candidate.get("concept_id") == gold_snomed_id_int:
                gt_candidate = candidate

        top_candidate = ranked_candidates[0] if ranked_candidates else None
        runner_candidate = ranked_candidates[1] if len(ranked_candidates) > 1 else None
        top_score = (
            float(top_candidate.get("final_score") or 0.0) if top_candidate else 0.0
        )
        runner_score = (
            float(runner_candidate.get("final_score") or 0.0)
            if runner_candidate
            else None
        )
        score_gap_top_runner = (
            (top_score - runner_score) if runner_score is not None else None
        )

        pred_final_score = (
            float(pred_candidate.get("final_score") or 0.0)
            if pred_candidate is not None
            else 0.0
        )
        gt_final_score = (
            float(gt_candidate.get("final_score") or 0.0)
            if gt_candidate is not None
            else None
        )
        score_delta_pred_vs_gt = (
            (pred_final_score - gt_final_score) if gt_final_score is not None else None
        )

        debug_rows.append(
            {
                "row_id": item["row_id"],
                "side": item["side"],
                "role": item["role"],
                "term": item["term"],
                "gold_snomed_id": item["gold_snomed_id"],
                "pred_snomed_id": pred_snomed_id,
                "hit": hit,
                "gt_rank": gt_rank,
                "pred_rank": pred_rank,
                "num_ranked_candidates": len(ranked_candidates),
                "top1_concept_id": (
                    top_candidate.get("concept_id") if top_candidate else None
                ),
                "top1_term": top_candidate.get("term") if top_candidate else None,
                "top1_final_score": top_score,
                "top2_concept_id": (
                    runner_candidate.get("concept_id") if runner_candidate else None
                ),
                "top2_term": runner_candidate.get("term") if runner_candidate else None,
                "top2_final_score": runner_score,
                "score_gap_top1_top2": score_gap_top_runner,
                "pred_final_score": pred_final_score,
                "gt_final_score": gt_final_score,
                "score_delta_pred_vs_gt": score_delta_pred_vs_gt,
                "near_tie_top1_top2": (
                    score_gap_top_runner is not None and score_gap_top_runner <= 0.01
                ),
                "pred_lexical": (
                    pred_candidate.get("lexical") if pred_candidate else None
                ),
                "pred_coverage": (
                    pred_candidate.get("coverage") if pred_candidate else None
                ),
                "pred_discriminative_coverage": (
                    pred_candidate.get("discriminative_coverage")
                    if pred_candidate
                    else None
                ),
                "pred_vector_rank": (
                    pred_candidate.get("vector_rank") if pred_candidate else None
                ),
                "pred_vector_raw": (
                    pred_candidate.get("vector_raw") if pred_candidate else None
                ),
                "pred_vector_bonus": (
                    pred_candidate.get("vector_bonus") if pred_candidate else None
                ),
                "pred_final_penalty": (
                    pred_candidate.get("final_penalty") if pred_candidate else None
                ),
                "pred_semantic_penalty": (
                    pred_candidate.get("semantic_penalty") if pred_candidate else None
                ),
                "pred_role_mismatch_penalty": (
                    pred_candidate.get("role_mismatch_penalty")
                    if pred_candidate
                    else None
                ),
                "pred_role_tension_penalty": (
                    pred_candidate.get("role_tension_penalty")
                    if pred_candidate
                    else None
                ),
                "pred_low_coverage_penalty": (
                    pred_candidate.get("low_coverage_penalty")
                    if pred_candidate
                    else None
                ),
                "pred_missing_discriminative_penalty": (
                    pred_candidate.get("missing_discriminative_penalty")
                    if pred_candidate
                    else None
                ),
                "pred_extra_qualifier_penalty": (
                    pred_candidate.get("extra_qualifier_penalty")
                    if pred_candidate
                    else None
                ),
                "pred_hard_negative_penalty": (
                    pred_candidate.get("hard_negative_penalty")
                    if pred_candidate
                    else None
                ),
                "gt_lexical": gt_candidate.get("lexical") if gt_candidate else None,
                "gt_coverage": gt_candidate.get("coverage") if gt_candidate else None,
                "gt_discriminative_coverage": (
                    gt_candidate.get("discriminative_coverage")
                    if gt_candidate
                    else None
                ),
                "gt_vector_rank": (
                    gt_candidate.get("vector_rank") if gt_candidate else None
                ),
                "gt_vector_raw": (
                    gt_candidate.get("vector_raw") if gt_candidate else None
                ),
                "gt_vector_bonus": (
                    gt_candidate.get("vector_bonus") if gt_candidate else None
                ),
                "gt_final_penalty": (
                    gt_candidate.get("final_penalty") if gt_candidate else None
                ),
                "gt_semantic_penalty": (
                    gt_candidate.get("semantic_penalty") if gt_candidate else None
                ),
                "gt_role_mismatch_penalty": (
                    gt_candidate.get("role_mismatch_penalty") if gt_candidate else None
                ),
                "gt_role_tension_penalty": (
                    gt_candidate.get("role_tension_penalty") if gt_candidate else None
                ),
                "gt_low_coverage_penalty": (
                    gt_candidate.get("low_coverage_penalty") if gt_candidate else None
                ),
                "gt_missing_discriminative_penalty": (
                    gt_candidate.get("missing_discriminative_penalty")
                    if gt_candidate
                    else None
                ),
                "gt_extra_qualifier_penalty": (
                    gt_candidate.get("extra_qualifier_penalty")
                    if gt_candidate
                    else None
                ),
                "gt_hard_negative_penalty": (
                    gt_candidate.get("hard_negative_penalty") if gt_candidate else None
                ),
                "gt_present_in_ranked": gt_candidate is not None,
            }
        )

        if gt_rank is not None:
            gt_ranks.append(gt_rank)
            gt_found_count += 1
        for k in rank_cutoffs:
            if gt_rank is not None and gt_rank <= k:
                hit_at_k_counts[k] += 1
                precision_at_k_sums[k] += 1.0 / float(k)
        gold_concept_term = _resolve_concept_term(item["gold_snomed_id"])
        pred_concept_term = _resolve_concept_term(pred_snomed_id)
        if not pred_concept_term and preferred_term:
            pred_concept_term = preferred_term
        role_total[item["role"]] += 1
        if hit:
            role_hits[item["role"]] += 1
        predictions.append(
            {
                **item,
                "pred_snomed_id": pred_snomed_id,
                "pred_preferred_term": preferred_term,
                "gold_concept_term": gold_concept_term,
                "pred_concept_term": pred_concept_term,
                "pred_score": score,
                "gt_rank": gt_rank,
                "candidate_rankings_top10": [
                    {
                        "rank": int(candidate.get("rank") or 0),
                        "concept_id": candidate.get("concept_id"),
                        "term": candidate.get("term"),
                        "final_score": candidate.get("final_score"),
                        "lexical": candidate.get("lexical"),
                        "coverage": candidate.get("coverage"),
                        "discriminative_coverage": candidate.get(
                            "discriminative_coverage"
                        ),
                        "vector_raw": candidate.get("vector_raw"),
                        "vector_bonus": candidate.get("vector_bonus"),
                        "vector_rank": candidate.get("vector_rank"),
                        "semantic_penalty": candidate.get("semantic_penalty"),
                        "final_penalty": candidate.get("final_penalty"),
                        "role_mismatch_penalty": candidate.get("role_mismatch_penalty"),
                        "role_tension_penalty": candidate.get("role_tension_penalty"),
                        "low_coverage_penalty": candidate.get("low_coverage_penalty"),
                        "missing_discriminative_penalty": candidate.get(
                            "missing_discriminative_penalty"
                        ),
                        "extra_qualifier_penalty": candidate.get(
                            "extra_qualifier_penalty"
                        ),
                        "hard_negative_penalty": candidate.get("hard_negative_penalty"),
                    }
                    for candidate in ranked_candidates[:10]
                ],
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

    total_queries = float(total) if total else 1.0
    reciprocal_rank_sum = sum((1.0 / float(r)) for r in gt_ranks if r and r > 0)
    rank_metrics = {
        "gt_found_count": gt_found_count,
        "gt_found_rate": (gt_found_count / total_queries) if total else 0.0,
        "mean_gt_rank": (sum(gt_ranks) / float(len(gt_ranks))) if gt_ranks else None,
        "median_gt_rank": median(gt_ranks) if gt_ranks else None,
        "mrr": (reciprocal_rank_sum / total_queries) if total else 0.0,
        "hit_rate_at_k": {
            str(k): (hit_at_k_counts[k] / total_queries) if total else 0.0
            for k in rank_cutoffs
        },
        "precision_at_k": {
            str(k): (precision_at_k_sums[k] / total_queries) if total else 0.0
            for k in rank_cutoffs
        },
    }

    service.close()

    return {
        "mode": mode,
        "total": total,
        "hits": hits,
        "accuracy": accuracy,
        "per_role": per_role,
        "rank_metrics": rank_metrics,
        "predictions": predictions,
        "debug_rows": debug_rows,
    }


def _build_debug_json_rows(output: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows_by_key = {
        _prediction_key(row): row for row in (output.get("predictions") or [])
    }
    compact_rows: List[Dict[str, Any]] = []
    for debug_row in output.get("debug_rows") or []:
        key = (
            str(debug_row.get("row_id") or ""),
            str(debug_row.get("side") or ""),
            str(debug_row.get("role") or ""),
            str(debug_row.get("term") or ""),
            str(debug_row.get("gold_snomed_id") or ""),
        )
        pred = rows_by_key.get(key) or {}
        top10 = pred.get("candidate_rankings_top10") or []
        compact_rows.append(
            {
                **debug_row,
                "candidate_rankings_top10": top10,
            }
        )
    return compact_rows


def _write_debug_artifacts(
    output: Dict[str, Any],
    output_json: Path,
    debug_csv_path: Optional[Path],
    debug_json_path: Optional[Path],
) -> Tuple[Optional[Path], Optional[Path]]:
    if debug_csv_path is None:
        debug_csv_path = output_json.with_name(f"{output_json.stem}_debug_probe.csv")
    if debug_json_path is None:
        debug_json_path = output_json.with_name(f"{output_json.stem}_debug_probe.json")

    debug_rows = output.get("debug_rows") or []
    if not debug_rows:
        return None, None

    debug_csv_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(debug_rows[0].keys())
    with debug_csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(debug_rows)

    debug_json_rows = _build_debug_json_rows(output)
    payload = {
        "run_id": os.getenv("SLURM_JOB_ID", "local"),
        "mode": output.get("mode"),
        "total": output.get("total"),
        "hits": output.get("hits"),
        "accuracy": output.get("accuracy"),
        "rank_metrics": output.get("rank_metrics"),
        "rows": debug_json_rows,
    }
    debug_json_path.parent.mkdir(parents=True, exist_ok=True)
    debug_json_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return debug_csv_path, debug_json_path


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
        dest="gold_paths",
        type=Path,
        action="append",
        default=[],
        help="Path to a ground-truth annotation JSON file. Repeat for multiple files.",
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
    parser.add_argument("--embedding-node", default="local")
    parser.add_argument("--embedding-port", type=int, default=None)
    parser.add_argument(
        "--run-manifest-jsonl",
        type=Path,
        default=None,
        help="Optional JSONL file to append compact run summaries for parameter sweeps.",
    )
    parser.add_argument(
        "--run-manifest-csv",
        type=Path,
        default=None,
        help="Optional CSV file to append compact run summaries for parameter sweeps.",
    )
    parser.add_argument(
        "--debug-csv",
        type=Path,
        default=None,
        help="Optional CSV path for per-term probing diagnostics (GT rank and score decomposition).",
    )
    parser.add_argument(
        "--debug-json",
        type=Path,
        default=None,
        help="Optional JSON path for per-term probing diagnostics (includes top candidate traces).",
    )
    return parser


def _resolve_embedding_port(cli_port: int | None) -> int:
    if cli_port is not None:
        return int(cli_port)

    for key in (
        "CARDIO_GRAPH_GROUNDING_EMBEDDING_PORT",
        "OLLAMA_PORT",
    ):
        raw = (os.environ.get(key) or "").strip()
        if raw.isdigit():
            return int(raw)

    host = (os.environ.get("OLLAMA_HOST") or "").strip()
    if host:
        # Supports forms like "127.0.0.1:11434" and "http://127.0.0.1:11434".
        match = re.search(r":(\d+)$", host)
        if match:
            return int(match.group(1))

    return 11434


def _capture_config_env() -> Dict[str, str]:
    prefixes = (
        "CARDIO_GRAPH_GROUNDING_",
        "OLLAMA_",
        "SLURM_",
    )
    redaction_markers = ("PASSWORD", "SECRET", "TOKEN", "API_KEY")
    captured: Dict[str, str] = {}
    for key, value in os.environ.items():
        if not key.startswith(prefixes):
            continue
        if any(marker in key for marker in redaction_markers):
            captured[key] = "<redacted>"
        else:
            captured[key] = value
    return dict(sorted(captured.items()))


def _build_compact_manifest_row(
    output: Dict[str, Any], output_json_path: Path
) -> Dict[str, Any]:
    rank_metrics = output.get("rank_metrics") or {}
    hit_at_k = rank_metrics.get("hit_rate_at_k") or {}
    precision_at_k = rank_metrics.get("precision_at_k") or {}
    settings = output.get("settings") or {}
    config_env = output.get("config_env") or {}
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "run_id": os.getenv("SLURM_JOB_ID", "local"),
        "mode": output.get("mode"),
        "accuracy": output.get("accuracy"),
        "hits": output.get("hits"),
        "total": output.get("total"),
        "mrr": rank_metrics.get("mrr"),
        "mean_gt_rank": rank_metrics.get("mean_gt_rank"),
        "median_gt_rank": rank_metrics.get("median_gt_rank"),
        "hit_at_1": hit_at_k.get("1"),
        "hit_at_3": hit_at_k.get("3"),
        "hit_at_5": hit_at_k.get("5"),
        "hit_at_10": hit_at_k.get("10"),
        "precision_at_1": precision_at_k.get("1"),
        "precision_at_3": precision_at_k.get("3"),
        "precision_at_5": precision_at_k.get("5"),
        "precision_at_10": precision_at_k.get("10"),
        "model": settings.get("model"),
        "node": settings.get("node"),
        "port": settings.get("port"),
        "vector_index": settings.get("vector_index"),
        "embedding_model": settings.get("embedding_model"),
        "gold_paths": "|".join(output.get("gold_paths") or []),
        "hard_negative_penalty": config_env.get(
            "CARDIO_GRAPH_GROUNDING_HARD_NEGATIVE_PENALTY"
        ),
        "vector_context_enabled": config_env.get(
            "CARDIO_GRAPH_GROUNDING_VECTOR_CONTEXT_ENABLED"
        ),
        "output_json": str(output_json_path),
    }


def _append_manifest_rows(
    jsonl_path: Path | None,
    csv_path: Path | None,
    row: Dict[str, Any],
) -> None:
    if jsonl_path is not None:
        jsonl_path.parent.mkdir(parents=True, exist_ok=True)
        with jsonl_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    if csv_path is not None:
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = list(row.keys())
        csv_exists = csv_path.exists() and csv_path.stat().st_size > 0
        with csv_path.open("a", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            if not csv_exists:
                writer.writeheader()
            writer.writerow(row)


def main() -> int:
    args = _build_parser().parse_args()

    if not args.gold_paths:
        args.gold_paths = [
            Path("/prj/doctoral_letters/guide/data/evaluation/table_22_manual_1.3.json")
        ]

    embedding_port = _resolve_embedding_port(args.embedding_port)

    os.environ["CARDIO_GRAPH_GROUNDING_VECTOR_URI"] = args.vector_uri
    os.environ["CARDIO_GRAPH_GROUNDING_VECTOR_USER"] = args.vector_user
    os.environ["CARDIO_GRAPH_GROUNDING_VECTOR_INDEX"] = args.vector_index
    os.environ["CARDIO_GRAPH_GROUNDING_EMBEDDING_MODEL"] = args.embedding_model
    os.environ["CARDIO_GRAPH_GROUNDING_EMBEDDING_NODE"] = args.embedding_node
    os.environ["CARDIO_GRAPH_GROUNDING_EMBEDDING_PORT"] = str(embedding_port)

    if args.embedding_node.strip().lower() == "local":
        os.environ.setdefault("OLLAMA_HOST", f"127.0.0.1:{embedding_port}")

    items = _read_gold_items(
        gold_paths=args.gold_paths,
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
        "gold_path": str(args.gold_paths[0]),
        "gold_paths": [str(path) for path in args.gold_paths],
        "deduplicated": not args.no_deduplicate,
        "config_env": _capture_config_env(),
        "settings": {
            "model": args.model,
            "node": args.node,
            "port": args.port,
            "vector_uri": args.vector_uri,
            "vector_user": args.vector_user,
            "vector_index": args.vector_index,
            "embedding_model": args.embedding_model,
            "embedding_node": args.embedding_node,
            "embedding_port": embedding_port,
        },
        **result,
    }

    if args.compare_with is not None and args.compare_with.exists():
        output["comparison"] = _compare_results(output, args.compare_with)

    manifest_row = _build_compact_manifest_row(output, args.output_json)
    _append_manifest_rows(
        jsonl_path=args.run_manifest_jsonl,
        csv_path=args.run_manifest_csv,
        row=manifest_row,
    )

    debug_csv_path, debug_json_path = _write_debug_artifacts(
        output=output,
        output_json=args.output_json,
        debug_csv_path=args.debug_csv,
        debug_json_path=args.debug_json,
    )

    if debug_csv_path is not None:
        output["debug_probe_csv"] = str(debug_csv_path)
    if debug_json_path is not None:
        output["debug_probe_json"] = str(debug_json_path)

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")

    print(f"mode={output['mode']}")
    print("gold_paths=" + ", ".join(output.get("gold_paths", [])))
    print(f"gold_items={output['total']}")
    print(f"hits={output['hits']}")
    print(f"accuracy={output['accuracy']:.6f}")
    print(f"output_json={args.output_json}")
    if debug_csv_path is not None:
        print(f"debug_probe_csv={debug_csv_path}")
    if debug_json_path is not None:
        print(f"debug_probe_json={debug_json_path}")
    if args.run_manifest_jsonl is not None:
        print(f"run_manifest_jsonl={args.run_manifest_jsonl}")
    if args.run_manifest_csv is not None:
        print(f"run_manifest_csv={args.run_manifest_csv}")
    rank_metrics = output.get("rank_metrics") or {}
    if rank_metrics:
        print(
            "rank_metrics="
            f"mrr={float(rank_metrics.get('mrr') or 0.0):.6f} "
            f"mean_gt_rank={rank_metrics.get('mean_gt_rank')} "
            f"median_gt_rank={rank_metrics.get('median_gt_rank')} "
            f"hit@1={float((rank_metrics.get('hit_rate_at_k') or {}).get('1') or 0.0):.6f} "
            f"hit@3={float((rank_metrics.get('hit_rate_at_k') or {}).get('3') or 0.0):.6f} "
            f"hit@5={float((rank_metrics.get('hit_rate_at_k') or {}).get('5') or 0.0):.6f}"
        )
    misses = [row for row in output.get("predictions", []) if not row.get("hit")]
    print(f"misses={len(misses)}")
    for row in misses:
        row_id = row.get("row_id", "")
        side = row.get("side", "")
        role = row.get("role", "")
        term = row.get("term", "")
        gold_id = row.get("gold_snomed_id", "")
        gold_term = row.get("gold_concept_term", "")
        pred_id = row.get("pred_snomed_id", "") or "<empty>"
        pred_term = row.get("pred_concept_term", "") or "<empty>"
        score = float(row.get("pred_score") or 0.0)
        print(
            "MISS "
            f"row={row_id} side={side} role={role} term={term!r} "
            f"gold={gold_id} ({gold_term}) pred={pred_id} ({pred_term}) "
            f"score={score:.6f}"
        )
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
