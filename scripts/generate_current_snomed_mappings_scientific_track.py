#!/usr/bin/env python3

import argparse
import json
import re
from collections import defaultdict
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


def _norm(text: Any) -> str:
    return " ".join(str(text or "").strip().lower().split())


def _load_strength_indexes(
    annotation_path: Path,
) -> tuple[
    dict[tuple[str, str, str], set[str]],
    dict[tuple[str, str], set[str]],
]:
    payload = json.loads(annotation_path.read_text(encoding="utf-8"))
    by_term_sid_role: dict[tuple[str, str, str], set[str]] = defaultdict(set)
    by_term_sid: dict[tuple[str, str], set[str]] = defaultdict(set)
    for item in payload.get("unique_combinations") or []:
        entity_original = _norm(item.get("entity_original"))
        role = _norm(item.get("role"))
        for candidate in item.get("entity_standardized_list") or []:
            snomed_id = str(candidate.get("snomed_id") or "").strip()
            strength = _norm(candidate.get("match_strenght"))
            if not entity_original or not snomed_id or not strength:
                continue
            by_term_sid_role[(entity_original, snomed_id, role)].add(strength)
            by_term_sid[(entity_original, snomed_id)].add(strength)
    return by_term_sid_role, by_term_sid


def _resolve_strength(
    row: dict[str, Any],
    by_term_sid_role: dict[tuple[str, str, str], set[str]],
    by_term_sid: dict[tuple[str, str], set[str]],
) -> tuple[str, str]:
    term = _norm(row.get("term"))
    gold_snomed_id = str(row.get("gold_snomed_id") or "").strip()
    role = _norm(row.get("role"))

    labels = by_term_sid_role.get((term, gold_snomed_id, role))
    if labels:
        if len(labels) == 1:
            return next(iter(labels)), "term+sid+role"
        return "/".join(sorted(labels)), "ambiguous(term+sid+role)"

    labels = by_term_sid.get((term, gold_snomed_id))
    if labels:
        if len(labels) == 1:
            return next(iter(labels)), "term+sid"
        return "/".join(sorted(labels)), "ambiguous(term+sid)"

    return "", "unresolved"


def _render_markdown(
    payload: dict[str, Any],
    eval_path: Path,
    repo_root: Path,
    annotation_path: Path | None = None,
) -> str:
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

    by_term_sid_role: dict[tuple[str, str, str], set[str]] = {}
    by_term_sid: dict[tuple[str, str], set[str]] = {}
    if annotation_path is not None and annotation_path.exists():
        by_term_sid_role, by_term_sid = _load_strength_indexes(annotation_path)

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
    ]
    if annotation_path is not None:
        lines.append(
            f"- Annotation source (`match_strenght`): `{_relative_path(annotation_path, repo_root)}`"
        )

    lines += [
        "",
        "Columns:",
        "- `row_id`, `side`, `role`, `term`: source concept location and role in GT annotations",
        "- `gold_snomed_id` / `gold_concept_term`: ground truth target",
        "- `gold_match_strength`: confidence/mapping-strength label from annotation (`exact`/`strong`/`weak`)",
        "- `strength_source`: how strength was resolved (`term+sid+role`, `term+sid`, or unresolved/ambiguous)",
        "- `pred_snomed_id` / `pred_concept_term`: system prediction",
        "- `hit`: `1` if prediction matches ground truth else `0`",
        "",
        "| row_id | side | role | term | gold_snomed_id | gold_concept_term | gold_match_strength | strength_source | pred_snomed_id | pred_concept_term | hit |",
        "|---|---|---|---|---:|---|---|---|---:|---|---:|",
    ]

    for row in predictions:
        hit = 1 if row.get("hit") else 0
        strength = ""
        strength_source = ""
        if by_term_sid:
            strength, strength_source = _resolve_strength(
                row,
                by_term_sid_role,
                by_term_sid,
            )
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
                    _safe_cell(strength),
                    _safe_cell(strength_source),
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
    parser.add_argument(
        "--annotation-json",
        type=Path,
        default=Path(
            "/prj/doctoral_letters/guide/data/manual_table_contruction/entity_index/entity_index_grounding_strenght_plus_new_include8.json"
        ),
        help="Optional annotation JSON with `match_strenght` labels.",
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
    annotation_path = args.annotation_json
    if annotation_path is not None and not annotation_path.is_absolute():
        annotation_path = (repo_root / annotation_path).resolve()

    markdown = _render_markdown(payload, eval_path, repo_root, annotation_path)

    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text(markdown, encoding="utf-8")

    run_id = str(eval_path.parent.name).replace("vector_job_", "")
    print(f"selected_eval={eval_path}")
    print(f"selected_run_id={run_id}")
    print(f"output_md={output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
