#!/usr/bin/env python3

import argparse
import json
import re
from pathlib import Path
from typing import Any


def _run_id_key(path: Path) -> int:
    match = re.search(r"(\d+)", path.parent.name)
    if not match:
        return -1
    return int(match.group(1))


def _is_scientific_track(payload: dict[str, Any]) -> bool:
    config_env = payload.get("config_env") or {}
    label = str(config_env.get("CARDIO_GRAPH_GROUNDING_ABLATION_LABEL") or "")
    rescue_map = str(config_env.get("CARDIO_GRAPH_GROUNDING_RESCUE_MAP_PATH") or "")
    if "NO_RESCUE" in label.upper():
        return True
    return rescue_map.strip() == ""


def _find_latest_scientific_eval(base_dir: Path) -> Path:
    candidates = sorted(
        base_dir.glob("vector_job_*/ground_truth_vector_eval.json"),
        key=_run_id_key,
    )
    scientific: list[Path] = []
    for candidate in candidates:
        payload = json.loads(candidate.read_text(encoding="utf-8"))
        if _is_scientific_track(payload):
            scientific.append(candidate)
    if not scientific:
        raise SystemExit(
            "No scientific-track eval JSON found under grounding_only artifacts."
        )
    return scientific[-1]


def _safe_cell(value: Any) -> str:
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", " ").strip()


def _relative_path(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _render_markdown(payload: dict[str, Any], eval_path: Path, repo_root: Path) -> str:
    predictions = payload.get("predictions") or []
    predictions = sorted(
        predictions,
        key=lambda row: (
            str(row.get("row_id") or ""),
            str(row.get("side") or ""),
            str(row.get("role") or ""),
            str(row.get("term") or ""),
            str(row.get("gold_snomed_id") or ""),
        ),
    )

    run_id = str(eval_path.parent.name).replace("vector_job_", "")
    accuracy = float(payload.get("accuracy") or 0.0)
    hits = int(payload.get("hits") or 0)
    total = int(payload.get("total") or 0)
    rank_metrics = payload.get("rank_metrics") or {}
    mrr = float(rank_metrics.get("mrr") or 0.0)

    lines = [
        "# Current SNOMED Mappings (Scientific Track)",
        "",
        "Canonical reference for colleague review of current system mappings under the scientific (no-rescue) protocol.",
        "",
        f"- Selected run: `{run_id}` (latest scientific locked_test, no rescue)",
        f"- Accuracy: `{accuracy:.6f}` (`{hits}/{total}`)",
        f"- MRR: `{mrr:.6f}`",
        f"- Source JSON: `{_relative_path(eval_path, repo_root)}`",
        "- Selection rule: latest `vector_job_*` eval with `CARDIO_GRAPH_GROUNDING_ABLATION_LABEL` containing `NO_RESCUE` or unset `CARDIO_GRAPH_GROUNDING_RESCUE_MAP_PATH`.",
        "",
        "Columns:",
        "- `row_id`, `side`, `role`, `term`: source concept location and role in GT annotations",
        "- `gold_snomed_id` / `gold_concept_term`: ground truth target",
        "- `pred_snomed_id` / `pred_concept_term`: system prediction",
        "- `hit`: `1` if prediction matches ground truth else `0`",
        "",
        "| row_id | side | role | term | gold_snomed_id | gold_concept_term | pred_snomed_id | pred_concept_term | hit |",
        "|---|---|---|---|---:|---|---:|---|---:|",
    ]

    for row in predictions:
        hit = 1 if row.get("hit") else 0
        lines.append(
            "| "
            + " | ".join(
                [
                    _safe_cell(row.get("row_id")),
                    _safe_cell(row.get("side")),
                    _safe_cell(row.get("role")),
                    _safe_cell(row.get("term")),
                    _safe_cell(row.get("gold_snomed_id")),
                    _safe_cell(row.get("gold_concept_term")),
                    _safe_cell(row.get("pred_snomed_id")),
                    _safe_cell(row.get("pred_concept_term")),
                    str(hit),
                ]
            )
            + " |"
        )

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Regenerate current scientific-track SNOMED mapping markdown."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root path.",
    )
    parser.add_argument(
        "--eval-json",
        type=Path,
        default=None,
        help="Optional explicit eval JSON path. If omitted, auto-select latest scientific run.",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path(
            "docs/reports/grounding/current_snomed_mappings_scientific_track.md"
        ),
        help="Output markdown path, relative to repo root unless absolute.",
    )
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    output_md = args.output_md
    if not output_md.is_absolute():
        output_md = (repo_root / output_md).resolve()

    if args.eval_json is not None:
        eval_path = args.eval_json.resolve()
    else:
        base_dir = repo_root / "docs/generated/ground_truth/grounding_only"
        eval_path = _find_latest_scientific_eval(base_dir)

    payload = json.loads(eval_path.read_text(encoding="utf-8"))
    markdown = _render_markdown(payload, eval_path, repo_root)

    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text(markdown, encoding="utf-8")

    run_id = str(eval_path.parent.name).replace("vector_job_", "")
    print(f"selected_eval={eval_path}")
    print(f"selected_run_id={run_id}")
    print(f"output_md={output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
