from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def _load_manifest(path: Path) -> dict:
    if not path.is_file():
        return {"benchmarks": []}
    return json.loads(path.read_text(encoding="utf-8"))


def _target_rows_for_split(benchmark: dict, split_name: str) -> str:
    if split_name == "locked_test":
        rows = benchmark.get("locked_test_rows") or []
    else:
        rows = benchmark.get("dev_rows") or []
    if not rows:
        return ""
    return ",".join(str(row) for row in rows)


def _run_single_benchmark(
    benchmark: dict,
    split_name: str,
    benchmark_out_dir: Path,
) -> tuple[int, Path]:
    env = os.environ.copy()
    env["CARDIO_GRAPH_TABLE22_GROUND_TRUTH_PATH"] = str(
        benchmark.get(
            "ground_truth_path", env.get("CARDIO_GRAPH_TABLE22_GROUND_TRUTH_PATH", "")
        )
    )
    env["CARDIO_GRAPH_TABLE_CLEAN_PATH"] = str(
        benchmark.get("table_clean_path", env.get("CARDIO_GRAPH_TABLE_CLEAN_PATH", ""))
    )
    env["CARDIO_GRAPH_TABLE22_TABLE_IDS"] = str(
        benchmark.get("table_ids", env.get("CARDIO_GRAPH_TABLE22_TABLE_IDS", "0"))
    )
    env["CARDIO_GRAPH_TABLE22_TARGET_ROWS"] = _target_rows_for_split(
        benchmark, split_name
    )

    benchmark_out_dir.mkdir(parents=True, exist_ok=True)
    benchmark_json = benchmark_out_dir / "table22_rowwise_alignment.json"
    benchmark_md = benchmark_out_dir / "table22_rowwise_comparison.md"
    benchmark_csv = benchmark_out_dir / "table22_rowwise_summary.csv"
    env["CARDIO_GRAPH_TABLE22_REPORT_JSON"] = str(benchmark_json)
    env["CARDIO_GRAPH_TABLE22_REPORT_MD"] = str(benchmark_md)
    env["CARDIO_GRAPH_TABLE22_REPORT_CSV"] = str(benchmark_csv)
    env["CARDIO_GRAPH_TABLE22_ROWS_DIR"] = str(benchmark_out_dir / "rows")

    command = [
        sys.executable,
        "-m",
        "cardio_graph_core.tuning.table22_dev_eval",
    ]
    process = subprocess.run(
        command,
        cwd=str(PROJECT_ROOT),
        env=env,
        capture_output=True,
        text=True,
    )

    # Forward concise benchmark-level output for traceability.
    name = benchmark.get("name", "unknown")
    print(
        f"[table22-dev-eval] benchmark={name} split={split_name} rc={process.returncode}"
    )
    if process.stdout.strip():
        print(process.stdout.strip())
    if process.stderr.strip():
        print(process.stderr.strip())

    return process.returncode, benchmark_json


def main() -> int:
    split_name = os.environ.get("CARDIO_GRAPH_TUNING_SPLIT_NAME", "dev")
    manifest_path = Path(
        os.environ.get(
            "CARDIO_GRAPH_TUNING_BENCHMARK_MANIFEST",
            PROJECT_ROOT / "config" / "autotuning" / "benchmark_manifest_v1.jsonc",
        )
    )

    report_json = Path(os.environ["CARDIO_GRAPH_TABLE22_REPORT_JSON"])
    report_md = Path(os.environ["CARDIO_GRAPH_TABLE22_REPORT_MD"])
    report_csv = Path(os.environ["CARDIO_GRAPH_TABLE22_REPORT_CSV"])

    manifest = _load_manifest(manifest_path)
    benchmarks = manifest.get("benchmarks") or []
    if not benchmarks:
        # Fallback: preserve legacy behavior.
        from cardio_graph_core.tuning.table22_dev_eval import main as single_main

        return single_main()

    combined_rows = []
    benchmark_meta = []
    failed = False

    root = report_json.parent / "_benchmarks"
    root.mkdir(parents=True, exist_ok=True)

    print("[table22-dev-eval] start")
    for benchmark in benchmarks:
        name = str(benchmark.get("name", "unknown"))
        rc, benchmark_json = _run_single_benchmark(
            benchmark=benchmark,
            split_name=split_name,
            benchmark_out_dir=root / name,
        )
        payload = {"rows": []}
        if benchmark_json.is_file():
            payload = json.loads(benchmark_json.read_text(encoding="utf-8"))

        rows = payload.get("rows") or []
        for row in rows:
            row_copy = dict(row)
            row_id = str(row_copy.get("row_id", ""))
            row_copy["row_id"] = f"{name}:{row_id}" if row_id else name
            row_copy["benchmark"] = name
            combined_rows.append(row_copy)

        benchmark_meta.append(
            {
                "name": name,
                "return_code": rc,
                "rows": len(rows),
                "alignment": str(benchmark_json),
            }
        )
        if rc != 0:
            failed = True

    report_json.parent.mkdir(parents=True, exist_ok=True)
    report_json.write_text(
        json.dumps(
            {
                "split": split_name,
                "manifest": str(manifest_path),
                "benchmarks": benchmark_meta,
                "rows": combined_rows,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    report_md.write_text(
        "# Multi-table evaluation summary\n\n"
        + f"Split: {split_name}\n\n"
        + f"Manifest: {manifest_path}\n\n"
        + "| Benchmark | Return code | Rows |\n"
        + "|---|---:|---:|\n"
        + "\n".join(
            f"| {item['name']} | {item['return_code']} | {item['rows']} |"
            for item in benchmark_meta
        )
        + "\n",
        encoding="utf-8",
    )

    report_csv.write_text(
        "benchmark,return_code,rows\n"
        + "\n".join(
            f"{item['name']},{item['return_code']},{item['rows']}"
            for item in benchmark_meta
        )
        + "\n",
        encoding="utf-8",
    )

    if failed:
        print("[table22-dev-eval] failed error=one_or_more_benchmarks_failed")
        return 1

    print(
        "[table22-dev-eval] done "
        f"rows={len(combined_rows)} benchmarks={len(benchmark_meta)}"
    )
    print(
        "[table22-dev-eval] artifacts "
        f"md={report_md} json={report_json} csv={report_csv}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
