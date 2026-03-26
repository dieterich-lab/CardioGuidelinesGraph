#!/usr/bin/env python3

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from cardio_graph_core.common.paths import (
    grounding_manifest_path,
    grounding_runs_dir,
    grounding_tracker_path,
)


def _load_eval(path: Path) -> Dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _run_id_sort_key(run_id: str) -> Tuple[int, str]:
    if run_id.isdigit():
        return (0, f"{int(run_id):012d}")
    return (1, run_id)


def _pick_eval_file(run_dir: Path) -> Optional[Path]:
    preferred = [
        "ground_truth_vector_eval.json",
        "vector_eval.json",
        "eval.json",
    ]
    for name in preferred:
        candidate = run_dir / name
        if candidate.is_file():
            return candidate
    return None


def _collect_run_files(
    base_dir: Path, run_ids: List[str], latest_n: int
) -> List[Tuple[str, Path]]:
    if run_ids:
        pairs = []
        for rid in run_ids:
            run_dirs = [base_dir / f"vector_job_{rid}", base_dir / f"job_{rid}"]
            for run_dir in run_dirs:
                if not run_dir.is_dir():
                    continue
                picked = _pick_eval_file(run_dir)
                if picked is not None:
                    pairs.append((rid, picked))
                    break
        return pairs

    run_dirs = sorted(
        [
            path
            for path in base_dir.iterdir()
            if path.is_dir()
            and (path.name.startswith("vector_job_") or path.name.startswith("job_"))
        ],
        key=lambda path: _run_id_sort_key(
            path.name.replace("vector_job_", "").replace("job_", "")
        ),
    )

    run_to_file: Dict[str, Path] = {}
    for run_dir in run_dirs:
        rid = run_dir.name.replace("vector_job_", "").replace("job_", "")
        picked = _pick_eval_file(run_dir)
        if picked is None:
            continue
        prev = run_to_file.get(rid)
        if prev is None:
            run_to_file[rid] = picked
            continue
        score = {
            "ground_truth_vector_eval.json": 3,
            "vector_eval.json": 2,
            "eval.json": 1,
        }
        if score.get(picked.name, 0) > score.get(prev.name, 0):
            run_to_file[rid] = picked

    pairs = sorted(run_to_file.items(), key=lambda pair: _run_id_sort_key(pair[0]))
    if latest_n > 0:
        pairs = pairs[-latest_n:]
    return pairs


def _extract_settings(data: Dict) -> Dict[str, str]:
    settings = data.get("settings") or {}
    return {k: str(v) for k, v in settings.items()}


def _run_family(data: Dict) -> str:
    gold_paths = data.get("gold_paths") or []
    if isinstance(gold_paths, list) and len(gold_paths) >= 3:
        return "gt3"
    if data.get("gold_path"):
        return "single_table"
    return "unknown"


def _find_log_for_run(slurm_log_dir: Optional[Path], run_id: str) -> Optional[Path]:
    if slurm_log_dir is None or not slurm_log_dir.exists():
        return None
    candidates = [
        slurm_log_dir / f"gt-eval-vector_{run_id}.log",
        slurm_log_dir / f"log_gt_eval_vector_{run_id}.log",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    fallback = sorted(slurm_log_dir.glob(f"*_{run_id}.log"))
    return fallback[-1] if fallback else None


def _parse_kv_line(text: str) -> Dict[str, str]:
    pattern = r'([A-Za-z0-9_]+)=((?:"[^"]*")|(?:\'[^\']*\')|[^\s]+)'
    result: Dict[str, str] = {}
    for key, value in re.findall(pattern, text):
        clean = value.strip().strip('"').strip("'")
        result[key] = clean
    return result


def _extract_knob_snapshot_from_log(log_path: Optional[Path]) -> Dict[str, str]:
    if log_path is None:
        return {}
    tracked_keys = {
        "hard_negative_penalty",
        "hard_negative_manifest",
        "role_soft_constraints",
        "role_mismatch_penalty",
        "role_tension_penalty",
        "role_semantic_mismatch_penalty",
        "role_semantic_crossclass_penalty",
        "ambiguity_lexical_force_pick",
        "ambiguity_confidence_backoff_enabled",
        "backoff_max_drop",
        "backoff_min_score",
        "vector_context_enabled",
        "vector_context_allowed_roles",
        "vector_context_append_term",
        "vector_context_max_tokens",
        "embedding_model",
        "embedding_url",
        "embedding_port",
    }
    snapshot: Dict[str, str] = {}
    for line in log_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if "[gt-local-ollama]" not in line and "[gt-load]" not in line:
            continue
        for key, value in _parse_kv_line(line).items():
            if key in tracked_keys:
                snapshot[key] = value
    return snapshot


def _build_confusions(data: Dict, top_n: int = 12) -> List[Dict]:
    misses = [row for row in (data.get("predictions") or []) if not row.get("hit")]
    grouped: Dict[Tuple[str, str, str], Dict] = {}
    for row in misses:
        role = str(row.get("role") or "UNKNOWN")
        gold_id = str(row.get("gold_snomed_id") or "<empty>")
        pred_id = str(row.get("pred_snomed_id") or "<empty>")
        key = (role, gold_id, pred_id)
        if key not in grouped:
            grouped[key] = {
                "role": role,
                "gold_snomed_id": gold_id,
                "pred_snomed_id": pred_id,
                "gold_term": str(row.get("gold_concept_term") or ""),
                "pred_term": str(
                    row.get("pred_concept_term") or row.get("pred_preferred_term") or ""
                ),
                "count": 0,
                "example_rows": Counter(),
            }
        grouped[key]["count"] += 1
        rid = str(row.get("row_id") or "")
        if rid:
            grouped[key]["example_rows"][rid] += 1

    confusions = sorted(grouped.values(), key=lambda item: -item["count"])[:top_n]
    for item in confusions:
        item["example_rows"] = [
            row_id for row_id, _ in item["example_rows"].most_common(3)
        ]
    return confusions


def _format_float(value: Optional[float]) -> str:
    if value is None:
        return "n/a"
    return f"{float(value):.3f}"


def _build_outputs(
    run_pairs: List[Tuple[str, Path]],
    slurm_log_dir: Optional[Path],
    latest_gate: float,
) -> Tuple[Dict, str]:
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

    run_summaries = []
    for rid, fp in run_pairs:
        run_data = _load_eval(fp)
        per_role = run_data.get("per_role") or {}
        run_log = _find_log_for_run(slurm_log_dir, rid)
        knob_snapshot = _extract_knob_snapshot_from_log(run_log)
        run_summaries.append(
            {
                "run_id": rid,
                "file": str(fp),
                "family": _run_family(run_data),
                "total": int(run_data.get("total") or 0),
                "hits": int(run_data.get("hits") or 0),
                "accuracy": float(run_data.get("accuracy") or 0.0),
                "per_role": {
                    role: float((vals or {}).get("accuracy") or 0.0)
                    for role, vals in per_role.items()
                },
                "settings": _extract_settings(run_data),
                "knob_snapshot": knob_snapshot,
                "log_path": str(run_log) if run_log else None,
            }
        )

    leaderboard = sorted(
        run_summaries, key=lambda row: (-row["accuracy"], row["run_id"])
    )
    best_run = leaderboard[0] if leaderboard else None
    gt3_runs = [row for row in run_summaries if row.get("family") == "gt3"]
    gt3_leaderboard = sorted(
        gt3_runs, key=lambda row: (-row["accuracy"], row["run_id"])
    )
    best_gt3_run = gt3_leaderboard[0] if gt3_leaderboard else None

    latest_summary = next(item for item in run_summaries if item["run_id"] == latest_id)
    previous_summary = run_summaries[-2] if len(run_summaries) >= 2 else None

    latest_snapshot = dict(latest_summary.get("settings") or {})
    for key, value in (latest_summary.get("knob_snapshot") or {}).items():
        latest_snapshot[f"knob.{key}"] = value

    variation_rows = []
    if previous_summary is not None:
        previous_snapshot = dict(previous_summary.get("settings") or {})
        for key, value in (previous_summary.get("knob_snapshot") or {}).items():
            previous_snapshot[f"knob.{key}"] = value
        all_keys = sorted(set(latest_snapshot.keys()) | set(previous_snapshot.keys()))
        for key in all_keys:
            prev = previous_snapshot.get(key)
            curr = latest_snapshot.get(key)
            if prev != curr:
                variation_rows.append(
                    {
                        "key": key,
                        "previous": prev,
                        "latest": curr,
                    }
                )

    latest_confusions = _build_confusions(latest, top_n=12)

    manifest = {
        "analysis_scope": {
            "run_ids": runs,
            "criterion": f"term-role pairs with misses in at least {threshold} runs",
            "generated_from": [str(fp) for _, fp in run_pairs],
        },
        "latest_gate": latest_gate,
        "run_leaderboard": leaderboard,
        "best_run": best_run,
        "best_gt3_run": best_gt3_run,
        "latest_run": latest_summary,
        "latest_variations_vs_previous": variation_rows,
        "latest_confusions": latest_confusions,
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
    lines.append("# Ground Truth Vector Grounding Persistent Error Milestone")
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
        f"- {latest_gate:.2f} gate: {'PASSED' if float(latest.get('accuracy', 0.0)) >= latest_gate else 'FAILED'}"
    )
    if best_run:
        lines.append(
            f"- Best run in window: {best_run['run_id']} ({best_run['accuracy']:.6f}, {best_run['hits']}/{best_run['total']})"
        )
    if best_gt3_run:
        lines.append(
            f"- Best GT3 run in window: {best_gt3_run['run_id']} ({best_gt3_run['accuracy']:.6f}, {best_gt3_run['hits']}/{best_gt3_run['total']})"
        )
    lines.append("")
    lines.append("## State Of The Art")
    lines.append("")
    if best_gt3_run:
        lines.append(
            f"- Current SOTA (GT3): run {best_gt3_run['run_id']} with accuracy {best_gt3_run['accuracy']:.6f} ({best_gt3_run['hits']}/{best_gt3_run['total']})."
        )
    elif best_run:
        lines.append(
            f"- Current SOTA (window fallback): run {best_run['run_id']} with accuracy {best_run['accuracy']:.6f} ({best_run['hits']}/{best_run['total']})."
        )
    else:
        lines.append("- No valid run available for SOTA statement.")
    lines.append(
        f"- Latest run under review: {latest_summary['run_id']} ({latest_summary['accuracy']:.6f}, {latest_summary['hits']}/{latest_summary['total']})."
    )
    lines.append(
        f"- Delta latest vs SOTA (accuracy): {(float(latest_summary['accuracy']) - float((best_gt3_run or best_run or latest_summary)['accuracy'])):+.6f}."
    )
    lines.append("")
    lines.append("## Run Leaderboard (Window)")
    lines.append("")
    lines.append(
        "| Rank | Run | Overall | Hits/Total | Procedure | ClinicalCondition | Medication |"
    )
    lines.append("|---:|---|---:|---|---:|---:|---:|")
    for rank, row in enumerate(leaderboard[:10], start=1):
        per_role = row.get("per_role") or {}
        lines.append(
            "| {rank} | {run} | {overall:.3f} | {hits}/{total} | {proc} | {cc} | {med} |".format(
                rank=rank,
                run=row["run_id"],
                overall=float(row["accuracy"]),
                hits=row["hits"],
                total=row["total"],
                proc=_format_float(per_role.get("Procedure")),
                cc=_format_float(per_role.get("ClinicalCondition")),
                med=_format_float(per_role.get("Medication")),
            )
        )

    lines.append("")
    lines.append("## Latest Knob Snapshot")
    lines.append("")
    if latest_snapshot:
        for key in sorted(latest_snapshot.keys()):
            lines.append(f"- `{key}` = `{latest_snapshot[key]}`")
    else:
        lines.append("- No knob snapshot found in logs; only eval metrics available.")

    lines.append("")
    lines.append("## Latest Variation vs Previous Run")
    lines.append("")
    if variation_rows:
        lines.append("| Key | Previous | Latest |")
        lines.append("|---|---|---|")
        for row in variation_rows[:30]:
            prev = "" if row["previous"] is None else str(row["previous"])
            curr = "" if row["latest"] is None else str(row["latest"])
            lines.append(f"| {row['key']} | {prev} | {curr} |")
    else:
        lines.append("- No detected setting/knob differences vs previous run.")

    lines.append("")
    lines.append("## Latest Label-Confusion Highlights")
    lines.append("")
    if latest_confusions:
        lines.append(
            "| Rank | Role | Gold ID | Pred ID | Count | Example Term Pair | Example Rows |"
        )
        lines.append("|---:|---|---|---|---:|---|---|")
        for idx, row in enumerate(latest_confusions, start=1):
            term_pair = f"{row['gold_term']} -> {row['pred_term']}"
            ex_rows = ", ".join(row["example_rows"]) if row.get("example_rows") else ""
            lines.append(
                f"| {idx} | {row['role']} | {row['gold_snomed_id']} | {row['pred_snomed_id']} | {row['count']} | {term_pair} | {ex_rows} |"
            )
    else:
        lines.append("- No misses in latest run.")

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
    all_roles = sorted(
        {
            role
            for _, fp in run_pairs
            for role in (_load_eval(fp).get("per_role") or {}).keys()
        }
    )
    preferred = ["ClinicalCondition", "ClinicalParameter", "Medication", "Procedure"]
    ordered_roles = [role for role in preferred if role in all_roles] + [
        role for role in all_roles if role not in preferred
    ]
    header = "| Run | " + " | ".join(ordered_roles) + " | Overall |"
    divider = "|---|" + "|".join(["---:" for _ in ordered_roles]) + "|---:|"
    lines.append(header)
    lines.append(divider)
    for rid, fp in run_pairs:
        data = _load_eval(fp)
        per_role = data.get("per_role", {})
        ov = data.get("accuracy", 0.0)
        role_values = [
            _format_float((per_role.get(role) or {}).get("accuracy"))
            for role in ordered_roles
        ]
        lines.append(f"| {rid} | " + " | ".join(role_values) + f" | {float(ov):.3f} |")

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
        "--min-total",
        type=int,
        default=1,
        help="Minimum total predictions required for a run to be included",
    )
    parser.add_argument(
        "--latest-gate",
        type=float,
        default=0.60,
        help="Accuracy gate threshold for latest run",
    )
    parser.add_argument(
        "--slurm-log-dir",
        default="/home/pwiesenbach/CardioGuidelinesGraph/slurm",
        help="Directory with slurm run logs for knob snapshot extraction",
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
    if args.min_total > 0:
        filtered_pairs = []
        for rid, fp in run_pairs:
            payload = _load_eval(fp)
            if int(payload.get("total") or 0) >= int(args.min_total):
                filtered_pairs.append((rid, fp))
        run_pairs = filtered_pairs
    if len(run_pairs) < 2:
        print(
            "ERROR: Need at least 2 grounding evaluation runs to build milestone report"
        )
        return 2

    slurm_log_dir = Path(args.slurm_log_dir) if args.slurm_log_dir else None
    manifest, markdown = _build_outputs(
        run_pairs=run_pairs,
        slurm_log_dir=slurm_log_dir,
        latest_gate=float(args.latest_gate),
    )

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
