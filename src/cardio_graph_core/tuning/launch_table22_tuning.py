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
DEFAULT_GROUND_TRUTH = (
    "/prj/doctoral_letters/guide/data/evaluation/table_22_manual_1.3.json"
)


def _submit(
    run_tag: str,
    model: str,
    node: str,
    port: int,
    iterations: int,
    candidates_per_iter: int,
) -> tuple[int, Path]:
    log_path = SLURM_DIR / f"run_table22_autotune_dev_{run_tag}.log"

    out_root = Path(
        os.environ.get(
            "CARDIO_GRAPH_TABLE22_AUTOTUNE_OUT_DIR",
            PROJECT_ROOT / "docs" / "table22_tuning_runs" / "autotune_dev",
        )
    )

    env_vars = {
        "PYTHONPATH": str(PROJECT_ROOT / "src"),
        "CARDIO_GRAPH_GRAPH_DIR": os.environ.get(
            "CARDIO_GRAPH_GRAPH_DIR", "/prj/doctoral_letters/guide/data/graph"
        ),
        "CARDIO_GRAPH_TABLE22_GROUND_TRUTH_PATH": os.environ.get(
            "CARDIO_GRAPH_TABLE22_GROUND_TRUTH_PATH", DEFAULT_GROUND_TRUTH
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
        "CARDIO_GRAPH_TABLE22_SKIP_ROWS": "",
        "CARDIO_GRAPH_TABLE22_LIVE_LLM": "true",
        "CARDIO_GRAPH_TABLE22_LLM_MODEL": model,
        "CARDIO_GRAPH_TABLE22_LLM_NODE": node,
        "CARDIO_GRAPH_TABLE22_LLM_PORT": str(port),
        "CARDIO_GRAPH_TABLE22_GROUND_AFTER_EXTRACTION": os.environ.get(
            "CARDIO_GRAPH_TABLE22_GROUND_AFTER_EXTRACTION", "false"
        ),
        "CARDIO_GRAPH_TUNING_LENIENT_EXTRAS": os.environ.get(
            "CARDIO_GRAPH_TUNING_LENIENT_EXTRAS", "true"
        ),
        "CARDIO_GRAPH_TABLE22_USE_SNAPSHOT": "false",
    }
    ground_after_extraction = (
        env_vars["CARDIO_GRAPH_TABLE22_GROUND_AFTER_EXTRACTION"].lower() == "true"
    )
    ground_flag = (
        "--ground-after-extraction"
        if ground_after_extraction
        else "--no-ground-after-extraction"
    )

    export_cmd = " ".join(
        f"{key}={shlex.quote(value)}" for key, value in env_vars.items()
    )
    eval_cmd = (
        "poetry run python -m cardio_graph_core.tuning.controller "
        "--no-dry-run "
        f"--iterations {iterations} "
        f"--candidates-per-iter {candidates_per_iter} "
        "--run-locked-every 9999 "
        "--split-manifest config/table22/split_v1.json "
        f"--output-dir {shlex.quote(str(out_root))} "
        f"--model {shlex.quote(model)} "
        f"--node {shlex.quote(node)} "
        f"--port {port} "
        f"{ground_flag} "
        "--no-stream-eval-logs "
        "--eval-command 'poetry run python -m cardio_graph_core.tuning.table22_dev_eval'"
    )
    wrapped = (
        f"cd {shlex.quote(str(PROJECT_ROOT))} && "
        f"export {export_cmd} && "
        f"echo '[table22-autotune-dev] run_tag={run_tag}' && "
        f"echo '[table22-autotune-dev] out_root={out_root}' && "
        f"{eval_cmd}"
    )

    result = subprocess.run(
        [
            "sbatch",
            "--job-name",
            "table22_autotune_dev",
            "--partition",
            "small",
            "--mem",
            "12G",
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


def _print_follow_up(run_tag: str, job_id: int, log_path: Path) -> None:
    print(f"\n[table22-tuning] mode=autotune-dev run_tag={run_tag} job_id={job_id}")
    print(f"[table22-tuning] log={log_path}")
    print("[table22-tuning] monitor:")
    print(f"  squeue -j {job_id}")
    print(f"  tail -f {log_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Submit one dev-focused Table 22 autotuning run via SLURM (commit-safe launcher)."
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("CARDIO_GRAPH_TABLE22_LLM_MODEL", "Qwen3next"),
    )
    parser.add_argument(
        "--node", default=os.environ.get("CARDIO_GRAPH_TABLE22_LLM_NODE", "g5")
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("CARDIO_GRAPH_TABLE22_LLM_PORT", "11435")),
    )
    parser.add_argument("--iterations", type=int, default=5)
    parser.add_argument("--candidates-per-iter", type=int, default=3)
    args = parser.parse_args()

    run_tag = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    job_id, log_path = _submit(
        run_tag=run_tag,
        model=args.model,
        node=args.node,
        port=args.port,
        iterations=args.iterations,
        candidates_per_iter=args.candidates_per_iter,
    )
    _print_follow_up(run_tag, job_id, log_path)


if __name__ == "__main__":
    main()
