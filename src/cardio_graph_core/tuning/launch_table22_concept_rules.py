from __future__ import annotations

import argparse
import os
import re
import shlex
import subprocess
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SLURM_DIR = PROJECT_ROOT / "slurm"


def _submit(
    run_tag: str,
    model: str,
    node: str,
    port: int,
    target_rows: str,
    out_dir: Path,
) -> tuple[int, Path]:
    log_path = SLURM_DIR / f"run_table22_concept_rules_{run_tag}.log"

    env_vars = {
        "PYTHONPATH": str(PROJECT_ROOT / "src"),
        "CARDIO_GRAPH_GRAPH_DIR": os.environ.get(
            "CARDIO_GRAPH_GRAPH_DIR", "/prj/doctoral_letters/guide/data/graph"
        ),
        "CARDIO_GRAPH_TABLE22_GROUND_TRUTH_PATH": os.environ.get(
            "CARDIO_GRAPH_TABLE22_GROUND_TRUTH_PATH",
            "/prj/doctoral_letters/guide/data/evaluation/table_22_manual_1.3.json",
        ),
        "CARDIO_GRAPH_TABLE22_RULES_PATH": os.environ.get(
            "CARDIO_GRAPH_TABLE22_RULES_PATH",
            "/prj/doctoral_letters/guide/data/graph/extracted_rules_docling_table_000_whole_grid_score0.6_df1_tag0_off0.jsonl",
        ),
        "CARDIO_GRAPH_TABLE22_TABLE_IDS": os.environ.get(
            "CARDIO_GRAPH_TABLE22_TABLE_IDS", "0"
        ),
        "CARDIO_GRAPH_TABLE22_ENTRY_MATCH_THRESHOLD": os.environ.get(
            "CARDIO_GRAPH_TABLE22_ENTRY_MATCH_THRESHOLD", "0.6"
        ),
        "CARDIO_GRAPH_TABLE22_TARGET_ROWS": target_rows,
        "CARDIO_GRAPH_TABLE22_SKIP_ROWS": "",
        "CARDIO_GRAPH_TABLE22_LIVE_LLM": "true",
        "CARDIO_GRAPH_TABLE22_LLM_MODEL": model,
        "CARDIO_GRAPH_TABLE22_LLM_NODE": node,
        "CARDIO_GRAPH_TABLE22_LLM_PORT": str(port),
        "CARDIO_GRAPH_TABLE22_GROUND_AFTER_EXTRACTION": os.environ.get(
            "CARDIO_GRAPH_TABLE22_GROUND_AFTER_EXTRACTION", "false"
        ),
        "CARDIO_GRAPH_TABLE22_USE_SNAPSHOT": "false",
        "CARDIO_GRAPH_TABLE22_ROWS_DIR": str(out_dir),
        "CARDIO_GRAPH_TABLE22_REPORT_MD": str(
            out_dir / "table22_rowwise_comparison.md"
        ),
        "CARDIO_GRAPH_TABLE22_REPORT_JSON": str(
            out_dir / "table22_rowwise_alignment.json"
        ),
        "CARDIO_GRAPH_TABLE22_REPORT_CSV": str(out_dir / "table22_rowwise_summary.csv"),
    }

    export_cmd = " ".join(
        f"{key}={shlex.quote(value)}" for key, value in env_vars.items()
    )

    eval_cmd = "poetry run python -m cardio_graph_core.tuning.table22_dev_eval"

    wrapped = (
        f"cd {shlex.quote(str(PROJECT_ROOT))} && "
        f"mkdir -p {shlex.quote(str(out_dir))} && "
        f"rm -f {shlex.quote(str(out_dir / 'row_*.md'))} && "
        f"rm -f {shlex.quote(str(out_dir / 'table22_rowwise_comparison.md'))} && "
        f"rm -f {shlex.quote(str(out_dir / 'table22_rowwise_alignment.json'))} && "
        f"rm -f {shlex.quote(str(out_dir / 'table22_rowwise_summary.csv'))} && "
        f"export {export_cmd} && "
        f"echo '[table22-concept-rules] run_tag={run_tag}' && "
        f"echo '[table22-concept-rules] out_dir={out_dir}' && "
        f"{eval_cmd}"
    )

    result = subprocess.run(
        [
            "sbatch",
            "--job-name",
            "table22_eval",
            "--partition",
            "small",
            "--mem",
            "4G",
            "--output",
            str(log_path),
            "--wrap",
            wrapped,
        ],
        cwd=str(PROJECT_ROOT),
        check=True,
        capture_output=True,
        text=True,
    )

    output = (result.stdout or "").strip()
    print(output)
    match = re.search(r"Submitted batch job\s+(\d+)", output)
    if not match:
        raise RuntimeError(f"Could not parse SLURM job id from output: {output!r}")
    return int(match.group(1)), log_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Submit Table 22 concept-rules markdown generation (live LLM + live grounding)."
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("CARDIO_GRAPH_TABLE22_LLM_MODEL", "Qwen3next"),
    )
    parser.add_argument(
        "--node",
        default=os.environ.get("CARDIO_GRAPH_TABLE22_LLM_NODE", "g5"),
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("CARDIO_GRAPH_TABLE22_LLM_PORT", "11435")),
    )
    parser.add_argument(
        "--target-rows",
        default=os.environ.get("CARDIO_GRAPH_TABLE22_TARGET_ROWS", ""),
        help="Comma-separated rows. Empty means all rows.",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path(
            os.environ.get(
                "CARDIO_GRAPH_TABLE22_ROWS_DIR",
                PROJECT_ROOT / "docs" / "table22_rows_comparison",
            )
        ),
    )
    args = parser.parse_args()

    run_tag = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    job_id, log_path = _submit(
        run_tag=run_tag,
        model=args.model,
        node=args.node,
        port=args.port,
        target_rows=args.target_rows,
        out_dir=args.out_dir,
    )

    print(f"\n[table22-concept-rules] run_tag={run_tag} job_id={job_id}")
    print(f"[table22-concept-rules] log={log_path}")
    print("[table22-concept-rules] monitor:")
    print(f"  squeue -j {job_id}")
    print(f"  tail -f {log_path}")


if __name__ == "__main__":
    main()
