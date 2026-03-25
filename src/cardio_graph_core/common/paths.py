from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DOCS_ROOT = PROJECT_ROOT / "docs"
DEFAULT_EXTERNAL_DATA_ROOT = Path("/prj/doctoral_letters/guide/data")


def external_data_root() -> Path:
    override = os.environ.get("CARDIO_GRAPH_EXTERNAL_DATA_ROOT", "").strip()
    if override:
        return Path(override)
    return DEFAULT_EXTERNAL_DATA_ROOT


def artifact_root() -> Path:
    override = os.environ.get("CARDIO_GRAPH_ARTIFACTS_DIR", "").strip()
    if override:
        return Path(override)
    return external_data_root() / "cardio_guidelines_graph" / "artifacts"


def trackers_root() -> Path:
    return DOCS_ROOT / "trackers"


def tracker_doc_path(workflow: str, table_key: str) -> Path:
    return trackers_root() / workflow / f"{table_key}.md"


def grounding_tracker_path(table_key: str = "table_22") -> Path:
    return tracker_doc_path("grounding", table_key)


def autotuning_tracker_path(table_key: str = "table_22") -> Path:
    return tracker_doc_path("autotuning", table_key)


def reference_root() -> Path:
    return DOCS_ROOT / "reference"


def ground_truth_rule_graphs_root() -> Path:
    return reference_root() / "ground_truth_rule_graphs"


def ground_truth_rule_graph_dir(table_key: str = "table_22") -> Path:
    return ground_truth_rule_graphs_root() / table_key


def rule_alignment_dir(table_key: str = "table_22") -> Path:
    return artifact_root() / "rule_alignment" / table_key


def rule_alignment_rows_dir(table_key: str = "table_22") -> Path:
    return rule_alignment_dir(table_key) / "rows"


def rule_alignment_report_md_path(table_key: str = "table_22") -> Path:
    return rule_alignment_dir(table_key) / "overview.md"


def rule_alignment_report_json_path(table_key: str = "table_22") -> Path:
    return rule_alignment_dir(table_key) / "alignment.json"


def rule_alignment_report_csv_path(table_key: str = "table_22") -> Path:
    return rule_alignment_dir(table_key) / "summary.csv"


def grounding_mode_dir(table_key: str = "table_22", mode: str = "vector") -> Path:
    return artifact_root() / "grounding" / table_key / mode


def grounding_runs_dir(table_key: str = "table_22", mode: str = "vector") -> Path:
    return grounding_mode_dir(table_key, mode) / "runs"


def grounding_run_dir(
    job_id: str | int, table_key: str = "table_22", mode: str = "vector"
) -> Path:
    return grounding_runs_dir(table_key, mode) / f"job_{job_id}"


def grounding_eval_path(
    job_id: str | int, table_key: str = "table_22", mode: str = "vector"
) -> Path:
    return grounding_run_dir(job_id, table_key, mode) / "eval.json"


def grounding_manifest_path(table_key: str = "table_22", mode: str = "vector") -> Path:
    return grounding_mode_dir(table_key, mode) / "persistent_error_manifest.json"


def grounding_legacy_milestone_path(
    table_key: str = "table_22", mode: str = "vector"
) -> Path:
    return grounding_mode_dir(table_key, mode) / "persistent_error_milestone.md"


def autotuning_root(table_key: str = "table_22") -> Path:
    return artifact_root() / "autotuning" / table_key


def autotuning_dev_dir(table_key: str = "table_22") -> Path:
    return autotuning_root(table_key) / "dev"


def autotuning_dry_run_dir(table_key: str = "table_22") -> Path:
    return autotuning_root(table_key) / "dry_run"
