#!/usr/bin/env python3

import json
import subprocess
import sys
from pathlib import Path


def _pick_latest_eval(base_dir: Path) -> Path:
    candidates = []
    for run_dir in sorted(base_dir.glob("vector_job_*")):
        run_id = run_dir.name.replace("vector_job_", "")
        for name in ("ground_truth_vector_eval.json", "vector_eval.json", "eval.json"):
            eval_path = run_dir / name
            if not eval_path.is_file():
                continue
            try:
                payload = json.loads(eval_path.read_text(encoding="utf-8"))
            except Exception:
                continue
            total = int(payload.get("total") or 0)
            if total > 0:
                key = int(run_id) if run_id.isdigit() else -1
                candidates.append((key, eval_path))
            break
    if not candidates:
        raise RuntimeError("No valid grounding eval run found (total > 0)")
    return sorted(candidates, key=lambda item: item[0])[-1][1]


def _run(cmd: list[str], cwd: Path) -> None:
    result = subprocess.run(cmd, cwd=str(cwd), check=False)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed ({result.returncode}): {' '.join(cmd)}")


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    python_bin = root / ".venv" / "bin" / "python"
    if not python_bin.exists():
        print(f"ERROR: Python environment not found at {python_bin}")
        return 2

    base_dir = root / "docs" / "generated" / "ground_truth" / "grounding_only"
    out_dir = root / "docs" / "generated" / "grounding"

    _run(
        [
            str(python_bin),
            str(root / "scripts" / "generate_grounding_progress_report.py"),
            "--base-dir",
            str(base_dir),
            "--latest-n",
            "6",
            "--min-total",
            "1",
            "--manifest-out",
            str(
                out_dir / "ground_truth_vector_grounding_persistent_error_manifest.json"
            ),
            "--milestone-out",
            str(out_dir / "ground_truth_vector_grounding_milestone.md"),
        ],
        cwd=root,
    )

    latest_eval = _pick_latest_eval(base_dir)

    _run(
        [
            str(python_bin),
            str(root / "scripts" / "triage_grounding_misses.py"),
            "--eval-json",
            str(latest_eval),
            "--out-csv",
            str(out_dir / "ground_truth_vector_latest_miss_triage.csv"),
            "--out-md",
            str(out_dir / "ground_truth_vector_latest_miss_triage.md"),
        ],
        cwd=root,
    )

    print("Tracking refreshed")
    print(f"milestone={out_dir / 'ground_truth_vector_grounding_milestone.md'}")
    print(
        "manifest="
        f"{out_dir / 'ground_truth_vector_grounding_persistent_error_manifest.json'}"
    )
    print(f"triage_csv={out_dir / 'ground_truth_vector_latest_miss_triage.csv'}")
    print(f"triage_md={out_dir / 'ground_truth_vector_latest_miss_triage.md'}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as error:
        print(f"ERROR: {error}")
        raise SystemExit(2)
