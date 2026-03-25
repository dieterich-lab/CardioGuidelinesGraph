#!/usr/bin/env python3

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Dict, List, Tuple

from cardio_graph_core.common.paths import (
    grounding_manifest_path,
    grounding_runs_dir,
    grounding_tracker_path,
)


def _load_eval(path: Path) -> Dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _collect_run_files(
    base_dir: Path, run_ids: List[str], latest_n: int
) -> List[Tuple[str, Path]]:
    if run_ids:
        pairs = []
        for rid in run_ids:
            candidates = [
                base_dir / f"job_{rid}" / "eval.json",
                base_dir / f"vector_job_{rid}" / "vector_eval.json",
            ]
            for fp in candidates:
                if fp.is_file():
                    pairs.append((rid, fp))
                    break
        return pairs

    candidates = sorted(base_dir.glob("job_*/eval.json"))
    if not candidates:
        candidates = sorted(base_dir.glob("vector_job_*/vector_eval.json"))
    if latest_n > 0:
        candidates = candidates[-latest_n:]
    pairs = []
    for fp in candidates:
        rid = fp.parent.name.replace("vector_job_", "").replace("job_", "")
        pairs.append((rid, fp))
    return pairs


def _build_outputs(run_pairs: List[Tuple[str, Path]]) -> Tuple[Dict, str]:
    runs = [rid for rid, _ in run_pairs]

    agg = {}
    for rid, fp in run_pairs:
        data = _load_eval(fp)
        for p in data.get("predictions", []):
            term = (p.get("term") or "").strip()
            if not term:
                continue
            role = p.get("role") or "UNKNOWN"
            hit = bool(p.get("hit"))
            key = (term, role)
            if key not in agg:
                agg[key] = {
                    "term": term,
                    "role": role,
                    "misses": 0,
                    "total": 0,
                    "runs_missed": set(),
                    "gold_ids": Counter(),
                    "pred_ids": Counter(),
                    "example_rows": Counter(),
                }
            row = agg[key]
            row["total"] += 1
            if not hit:
                row["misses"] += 1
                row["runs_missed"].add(rid)
                gid = (p.get("gold_snomed_id") or "").strip()
                pid = (p.get("pred_snomed_id") or "").strip() or "<empty>"
                rid_row = p.get("row_id") or ""
                if gid:
                    row["gold_ids"][gid] += 1
                row["pred_ids"][pid] += 1
                if rid_row:
                    row["example_rows"][rid_row] += 1

    persistent = []
    threshold = max(2, len(runs) - 1) if len(runs) >= 3 else max(1, len(runs))
    for row in agg.values():
        if len(row["runs_missed"]) >= threshold:
            persistent.append(row)

    persistent.sort(
        key=lambda x: (-len(x["runs_missed"]), -x["misses"], x["role"], x["term"])
    )
    top = persistent[:15]

    latest_id, latest_path = run_pairs[-1]
    latest = _load_eval(latest_path)

    manifest = {
        "analysis_scope": {
            "run_ids": runs,
            "criterion": f"term-role pairs with misses in at least {threshold} runs",
            "generated_from": [str(fp) for _, fp in run_pairs],
        },
        "top_persistent_errors": [],
        "latest_role_accuracy": latest.get("per_role", {}),
    }

    for row in top:
        manifest["top_persistent_errors"].append(
            {
                "term": row["term"],
                "role": row["role"],
                "runs_missed_count": len(row["runs_missed"]),
                "runs_missed": sorted(row["runs_missed"]),
                "misses_total": row["misses"],
                "observations_total": row["total"],
                "gold_snomed_ids": dict(row["gold_ids"].most_common(3)),
                "predicted_snomed_ids_on_miss": dict(row["pred_ids"].most_common(5)),
                "example_rows": [k for k, _ in row["example_rows"].most_common(3)],
            }
        )

    lines = []
    lines.append("# Table22 Vector Grounding Persistent Error Milestone")
    lines.append("")
    lines.append("Runs analyzed: " + ", ".join(runs))
    lines.append("")
    lines.append(
        "Criterion: term-role pairs that missed in at least "
        + str(threshold)
        + " analyzed runs."
    )
    lines.append("")
    lines.append("## Latest Run Gate")
    lines.append(
        f"- Latest run {latest_id} accuracy: {latest.get('accuracy', 0.0):.6f} "
        f"({latest.get('hits', 0)}/{latest.get('total', 0)})"
    )
    lines.append(
        f"- 0.60 gate: {'PASSED' if float(latest.get('accuracy', 0.0)) >= 0.60 else 'FAILED'}"
    )
    lines.append("")
    lines.append("## Top Persistent Error Terms")
    lines.append("")
    lines.append(
        "| Rank | Term | Role | Runs Missed | Misses (analyzed runs) | Typical Wrong Prediction IDs | Example Rows |"
    )
    lines.append("|---:|---|---|---|---:|---|---|")
    for idx, row in enumerate(manifest["top_persistent_errors"], start=1):
        preds = ", ".join(list(row["predicted_snomed_ids_on_miss"].keys())[:3])
        ex = ", ".join(row["example_rows"][:3])
        runs_m = ", ".join(row["runs_missed"])
        lines.append(
            f"| {idx} | {row['term']} | {row['role']} | {runs_m} | {row['misses_total']} | {preds} | {ex} |"
        )

    lines.append("")
    lines.append("## Role-Level Accuracy Trend")
    lines.append("")
    lines.append(
        "| Run | ClinicalCondition | ClinicalParameter | Procedure | Overall |"
    )
    lines.append("|---|---:|---:|---:|---:|")
    for rid, fp in run_pairs:
        data = _load_eval(fp)
        per_role = data.get("per_role", {})
        cc = per_role.get("ClinicalCondition", {}).get("accuracy", 0.0)
        cp = per_role.get("ClinicalParameter", {}).get("accuracy", 0.0)
        pr = per_role.get("Procedure", {}).get("accuracy", 0.0)
        ov = data.get("accuracy", 0.0)
        lines.append(f"| {rid} | {cc:.3f} | {cp:.3f} | {pr:.3f} | {ov:.3f} |")

    markdown = "\n".join(lines) + "\n"
    return manifest, markdown


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--base-dir",
        default=str(grounding_runs_dir("table_22", "vector")),
        help="Directory containing job_<id>/eval.json artifacts",
    )
    parser.add_argument(
        "--run-id",
        action="append",
        default=[],
        help="Specific run id to include (can be repeated)",
    )
    parser.add_argument(
        "--latest-n",
        type=int,
        default=3,
        help="Use latest N runs when --run-id is not provided",
    )
    parser.add_argument(
        "--manifest-out",
        default=str(grounding_manifest_path("table_22", "vector")),
        help="Output path for machine-readable manifest",
    )
    parser.add_argument(
        "--milestone-out",
        default=str(grounding_tracker_path("table_22")),
        help="Output path for markdown milestone report",
    )
    args = parser.parse_args()

    base_dir = Path(args.base_dir)
    run_pairs = _collect_run_files(base_dir, args.run_id, args.latest_n)
    if len(run_pairs) < 2:
        print("ERROR: Need at least 2 vector_eval.json runs to build milestone report")
        return 2

    manifest, markdown = _build_outputs(run_pairs)

    manifest_path = Path(args.manifest_out)
    milestone_path = Path(args.milestone_out)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    milestone_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    milestone_path.write_text(markdown, encoding="utf-8")

    print(f"Wrote manifest: {manifest_path}")
    print(f"Wrote milestone: {milestone_path}")
    print("Runs included:", ", ".join(manifest["analysis_scope"]["run_ids"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
