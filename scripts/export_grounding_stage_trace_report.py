#!/usr/bin/env python3
"""Export per-item grounding stage diagnostics from eval JSON.

This script converts prediction-level diagnostics into CSV/JSON for failure analysis.
It expects eval JSON produced by ground_truth_snomed_grounding_eval_core.py with
`gt_presence_trace` and `candidate_rankings_to_gt` fields.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, List


def _fmt_rank_chain(candidates: List[Dict[str, Any]]) -> str:
    parts: List[str] = []
    for c in candidates:
        rank = c.get("rank")
        cid = c.get("concept_id")
        term = str(c.get("term") or "").replace("|", "/")
        score = c.get("final_score")
        parts.append(f"{rank}:{cid}:{term}:{score}")
    return " | ".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--eval-json", type=Path, required=True)
    parser.add_argument("--out-csv", type=Path, required=True)
    parser.add_argument("--out-json", type=Path, default=None)
    args = parser.parse_args()

    payload = json.loads(args.eval_json.read_text(encoding="utf-8"))
    predictions = payload.get("predictions") or []

    rows: List[Dict[str, Any]] = []
    for p in predictions:
        trace = p.get("gt_presence_trace") or {}
        to_gt = p.get("candidate_rankings_to_gt") or []
        top10 = p.get("candidate_rankings_top10") or []
        rows.append(
            {
                "row_id": p.get("row_id"),
                "side": p.get("side"),
                "role": p.get("role"),
                "term": p.get("term"),
                "gold_snomed_id": p.get("gold_snomed_id"),
                "gold_concept_term": p.get("gold_concept_term"),
                "pred_snomed_id": p.get("pred_snomed_id"),
                "pred_concept_term": p.get("pred_concept_term"),
                "hit": int(bool(p.get("hit"))),
                "gt_rank": p.get("gt_rank"),
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

    args.out_csv.parent.mkdir(parents=True, exist_ok=True)
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
    with args.out_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    if args.out_json is not None:
        args.out_json.parent.mkdir(parents=True, exist_ok=True)
        args.out_json.write_text(
            json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    print(f"rows={len(rows)}")
    print(f"out_csv={args.out_csv}")
    if args.out_json is not None:
        print(f"out_json={args.out_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
