#!/usr/bin/env python3
"""Summarize two grounding eval runs with stage-trace exports and mismatch analysis.

Given two run IDs (typically scientific no-rescue and production rescue), this script:
1. Loads each run's eval JSON.
2. Exports per-item stage trace CSV/JSON.
3. Writes a compact markdown comparison of key metrics and miss attribution.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


def _eval_path(base_dir: Path, run_id: str) -> Path:
    run_dir = base_dir / f"vector_job_{run_id}"
    for name in ("ground_truth_vector_eval.json", "vector_eval.json", "eval.json"):
        path = run_dir / name
        if path.is_file():
            return path
    raise FileNotFoundError(f"No eval JSON found for run_id={run_id} in {run_dir}")


def _fmt_rank_chain(candidates: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for candidate in candidates:
        rank = candidate.get("rank")
        concept_id = candidate.get("concept_id")
        term = str(candidate.get("term") or "").replace("|", "/")
        final_score = candidate.get("final_score")
        parts.append(f"{rank}:{concept_id}:{term}:{final_score}")
    return " | ".join(parts)


def _build_trace_rows(predictions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for prediction in predictions:
        trace = prediction.get("gt_presence_trace") or {}
        to_gt = prediction.get("candidate_rankings_to_gt") or []
        top10 = prediction.get("candidate_rankings_top10") or []
        rows.append(
            {
                "row_id": prediction.get("row_id"),
                "side": prediction.get("side"),
                "role": prediction.get("role"),
                "term": prediction.get("term"),
                "gold_snomed_id": prediction.get("gold_snomed_id"),
                "gold_concept_term": prediction.get("gold_concept_term"),
                "pred_snomed_id": prediction.get("pred_snomed_id"),
                "pred_concept_term": prediction.get("pred_concept_term"),
                "hit": int(bool(prediction.get("hit"))),
                "gt_rank": prediction.get("gt_rank"),
                "gold_absence_stage": trace.get("gold_absence_stage"),
                "gold_in_initial_results": trace.get("gold_in_initial_results"),
                "gold_in_allowed_domain": trace.get("gold_in_allowed_domain"),
                "gold_in_truncated_set": trace.get("gold_in_truncated_set"),
                "gold_in_final_ranked": trace.get("gold_in_final_ranked"),
                "gold_filter_reasons": ";".join(trace.get("gold_filter_reasons") or []),
                "num_ranked_to_gt": len(to_gt),
                "rank_chain_to_gt": _fmt_rank_chain(to_gt),
                "top10_chain": _fmt_rank_chain(top10),
            }
        )
    return rows


def _write_trace_outputs(
    rows: list[dict[str, Any]], out_csv: Path, out_json: Path
) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = (
        list(rows[0].keys())
        if rows
        else [
            "row_id",
            "side",
            "role",
            "term",
            "gold_snomed_id",
            "gold_concept_term",
            "pred_snomed_id",
            "pred_concept_term",
            "hit",
            "gt_rank",
            "gold_absence_stage",
            "gold_in_initial_results",
            "gold_in_allowed_domain",
            "gold_in_truncated_set",
            "gold_in_final_ranked",
            "gold_filter_reasons",
            "num_ranked_to_gt",
            "rank_chain_to_gt",
            "top10_chain",
        ]
    )

    with out_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(
        json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def _run_summary(payload: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    total = int(payload.get("total") or len(rows))
    hits = int(payload.get("hits") or 0)
    misses = total - hits
    accuracy = float(payload.get("accuracy") or 0.0)
    mrr = float((payload.get("rank_metrics") or {}).get("mrr") or 0.0)

    miss_rows = [row for row in rows if int(row.get("hit") or 0) == 0]
    gt_present_not_top1 = sum(
        1 for row in miss_rows if row.get("gt_rank") not in (None, "", "null")
    )
    gt_absent_final = sum(
        1
        for row in miss_rows
        if str(row.get("gold_in_final_ranked")).lower() not in ("1", "true")
    )

    stage_counter = Counter(
        str(row.get("gold_absence_stage") or "unknown")
        for row in miss_rows
        if str(row.get("gold_in_final_ranked")).lower() not in ("1", "true")
    )
    dominant_absence_stage = (
        stage_counter.most_common(1)[0][0] if stage_counter else "n/a"
    )

    return {
        "label": str(
            (payload.get("config_env") or {}).get(
                "CARDIO_GRAPH_GROUNDING_ABLATION_LABEL"
            )
            or ""
        ),
        "total": total,
        "hits": hits,
        "misses": misses,
        "accuracy": accuracy,
        "mrr": mrr,
        "gt_present_not_top1": gt_present_not_top1,
        "gt_absent_final": gt_absent_final,
        "dominant_absence_stage": dominant_absence_stage,
    }


def _write_markdown(
    out_md: Path,
    scientific_job: str,
    production_job: str,
    scientific: dict[str, Any],
    production: dict[str, Any],
) -> None:
    fixed = scientific["misses"] - production["misses"]

    lines: list[str] = []
    lines.append(f"# Stage Trace Comparison: {scientific_job} vs {production_job}")
    lines.append("")
    lines.append("## Top-line")
    lines.append("")
    lines.append("| Run | Label | Accuracy | Hits/Total | MRR | Misses |")
    lines.append("|---|---|---:|---:|---:|---:|")
    lines.append(
        "| {run} | {label} | {acc:.6f} | {hits}/{total} | {mrr:.6f} | {misses} |".format(
            run=scientific_job,
            label=scientific["label"] or "(unset)",
            acc=scientific["accuracy"],
            hits=scientific["hits"],
            total=scientific["total"],
            mrr=scientific["mrr"],
            misses=scientific["misses"],
        )
    )
    lines.append(
        "| {run} | {label} | {acc:.6f} | {hits}/{total} | {mrr:.6f} | {misses} |".format(
            run=production_job,
            label=production["label"] or "(unset)",
            acc=production["accuracy"],
            hits=production["hits"],
            total=production["total"],
            mrr=production["mrr"],
            misses=production["misses"],
        )
    )
    lines.append("")
    lines.append("## Miss Attribution")
    lines.append("")
    lines.append(
        "| Run | GT present but not top-1 | GT absent from final ranking | Dominant absence stage |"
    )
    lines.append("|---|---:|---:|---|")
    lines.append(
        "| {run} | {present} | {absent} | {stage} |".format(
            run=scientific_job,
            present=scientific["gt_present_not_top1"],
            absent=scientific["gt_absent_final"],
            stage=scientific["dominant_absence_stage"],
        )
    )
    lines.append(
        "| {run} | {present} | {absent} | {stage} |".format(
            run=production_job,
            present=production["gt_present_not_top1"],
            absent=production["gt_absent_final"],
            stage=production["dominant_absence_stage"],
        )
    )
    lines.append("")
    lines.append("## Delta")
    lines.append("")
    lines.append(
        f"- Misses changed by {fixed} (positive means fewer misses in run {production_job} vs {scientific_job})."
    )

    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scientific-job", required=True)
    parser.add_argument("--production-job", required=True)
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=Path("docs/generated/ground_truth/grounding_only"),
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("docs/generated/grounding"),
    )
    args = parser.parse_args()

    sci_eval_path = _eval_path(args.base_dir, args.scientific_job)
    prod_eval_path = _eval_path(args.base_dir, args.production_job)

    sci_payload = json.loads(sci_eval_path.read_text(encoding="utf-8"))
    prod_payload = json.loads(prod_eval_path.read_text(encoding="utf-8"))

    sci_rows = _build_trace_rows(sci_payload.get("predictions") or [])
    prod_rows = _build_trace_rows(prod_payload.get("predictions") or [])

    sci_csv = args.out_dir / f"stage_trace_vector_job_{args.scientific_job}.csv"
    sci_json = args.out_dir / f"stage_trace_vector_job_{args.scientific_job}.json"
    prod_csv = args.out_dir / f"stage_trace_vector_job_{args.production_job}.csv"
    prod_json = args.out_dir / f"stage_trace_vector_job_{args.production_job}.json"

    _write_trace_outputs(sci_rows, sci_csv, sci_json)
    _write_trace_outputs(prod_rows, prod_csv, prod_json)

    sci_summary = _run_summary(sci_payload, sci_rows)
    prod_summary = _run_summary(prod_payload, prod_rows)

    out_md = (
        args.out_dir
        / f"mismatch_analysis_trace_{args.scientific_job}_vs_{args.production_job}.md"
    )
    _write_markdown(
        out_md, args.scientific_job, args.production_job, sci_summary, prod_summary
    )

    print(f"scientific_eval={sci_eval_path}")
    print(f"production_eval={prod_eval_path}")
    print(f"scientific_csv={sci_csv}")
    print(f"production_csv={prod_csv}")
    print(f"summary_md={out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
