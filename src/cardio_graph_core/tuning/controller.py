from __future__ import annotations

import json
import math
import os
import random
import re
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple

import click

from cardio_graph_core.common.paths import autotuning_dry_run_dir
from cardio_graph_core.tuning.contracts import (
    ErrorItem,
    Metrics,
    RowErrors,
    ScoreReport,
    SplitManifest,
)
from cardio_graph_core.tuning.error_analyst import ErrorAnalyst
from cardio_graph_core.tuning.gates import (
    GateThresholds,
    evaluate_dev_gates,
    evaluate_locked_test_gate,
)
from cardio_graph_core.tuning.prompt_optimizer import PromptOptimizer
from cardio_graph_core.tuning.prompt_patcher import apply_prompt_patch, is_patch_safe
from cardio_graph_core.tuning.score_adapter import build_score_report_from_alignment

DEFAULT_GRAPH_DIR = "/prj/doctoral_letters/guide/data/graph"
DEFAULT_GROUND_TRUTH_PATH = (
    "/prj/doctoral_letters/guide/data/evaluation/table_22_manual_1.3.json"
)
DEFAULT_RULES_PATH = (
    "/prj/doctoral_letters/guide/data/graph/"
    "extracted_rules_docling_table_000_whole_grid_score0.6_df1_tag0_off0.jsonl"
)
DEFAULT_CHAT_TUNING_MODEL = "Qwen30b"


def _load_split_manifest(path: Path) -> SplitManifest:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return SplitManifest.from_dict(payload)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _write_run_summary(
    run_root: Path,
    run_tag: str,
    manifest: SplitManifest,
    iterations: int,
    iterations_executed: int,
    accepted_promotions: int,
    champion_prompt: str,
    champion_dev: Metrics,
    champion_test: Metrics,
    dry_run: bool,
    config_payload: Dict[str, object],
) -> None:
    payload = {
        "run_tag": run_tag,
        "split_version": manifest.split_version,
        "iterations": iterations,
        "iterations_executed": iterations_executed,
        "accepted_promotions": accepted_promotions,
        "final_prompt": champion_prompt,
        "final_dev_metrics": champion_dev.to_dict(),
        "final_locked_test_metrics": champion_test.to_dict(),
        "dry_run": dry_run,
        "config": config_payload,
    }
    _write_json(run_root / "run_summary.json", payload)


def _simulate_error_rows(row_ids: List[str], rng: random.Random) -> List[RowErrors]:
    candidate_classes = [
        "B1_missing_concept",
        "B2_extra_concept",
        "C1_operator_wrong",
        "C5_logic_type_wrong",
        "C6_logic_group_wrong",
    ]
    rows: List[RowErrors] = []
    for row_id in row_ids:
        error_count = rng.randint(0, 2)
        row_errors: List[ErrorItem] = []
        for _ in range(error_count):
            error_class = rng.choice(candidate_classes)
            row_errors.append(
                ErrorItem(
                    error_class=error_class,
                    severity="major",
                    expected="ground_truth",
                    actual="llm_output",
                )
            )
        rows.append(RowErrors(row_id=row_id, errors=row_errors))
    return rows


def _simulate_metrics(
    base: Metrics,
    rng: random.Random,
    favor_rule_gain: bool,
) -> Metrics:
    rule_gain = (
        rng.uniform(0.002, 0.018) if favor_rule_gain else rng.uniform(-0.01, 0.01)
    )
    operator_delta = rng.uniform(-0.01, 0.012)
    logic_group_delta = rng.uniform(-0.01, 0.012)
    concept_f1_delta = rng.uniform(-0.01, 0.01)

    def bounded(value: float) -> float:
        return max(0.0, min(1.0, value))

    return Metrics(
        schema_valid_rate=1.0,
        rule_exact_match=bounded(base.rule_exact_match + rule_gain),
        operator_accuracy=bounded(base.operator_accuracy + operator_delta),
        logic_group_accuracy=bounded(base.logic_group_accuracy + logic_group_delta),
        concept_precision=bounded(base.concept_precision + rng.uniform(-0.01, 0.01)),
        concept_recall=bounded(base.concept_recall + rng.uniform(-0.01, 0.01)),
        concept_f1=bounded(base.concept_f1 + concept_f1_delta),
        grounding_hit_rate=bounded(base.grounding_hit_rate + rng.uniform(-0.01, 0.01)),
    )


def _initial_metrics() -> Metrics:
    return Metrics(
        schema_valid_rate=1.0,
        rule_exact_match=0.40,
        operator_accuracy=0.60,
        logic_group_accuracy=0.55,
        concept_precision=0.72,
        concept_recall=0.67,
        concept_f1=0.69,
        grounding_hit_rate=0.78,
    )


def _candidate_utility(deltas: Dict[str, float]) -> float:
    return (
        3.0 * deltas.get("rule_exact_match", 0.0)
        + 1.0 * deltas.get("operator_accuracy", 0.0)
        + 1.0 * deltas.get("logic_group_accuracy", 0.0)
        + 1.0 * deltas.get("concept_f1", 0.0)
    )


def _patch_zones(patch) -> Set[str]:
    return {edit.zone for edit in patch.edits if edit.zone}


def _ucb_bonus(
    zones: Set[str],
    zone_stats: Dict[str, Dict[str, float]],
    total_zone_uses: int,
    exploration_weight: float,
) -> float:
    if not zones:
        return 0.0
    terms = []
    for zone in zones:
        usage = int(zone_stats.get(zone, {}).get("uses", 0))
        bonus = math.sqrt(math.log(total_zone_uses + 2.0) / (usage + 1.0))
        terms.append(bonus)
    return exploration_weight * (sum(terms) / len(terms))


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name, str(default))
    try:
        return float(raw)
    except (TypeError, ValueError):
        return default


def _run_evaluation(
    split_name: str,
    row_ids: List[str],
    out_dir: Path,
    prompt_appendix_path: Path,
    eval_command: str,
    model_name: str,
    node: str,
    port: int,
    ground_after_extraction: bool,
    stream_eval_logs: bool,
    graph_dir: str,
    ground_truth_path: str,
    rules_path: str,
    table_ids: str,
    entry_match_threshold: float,
    skip_rows: str,
    live_llm: bool,
    use_snapshot: bool,
    benchmark_manifest: str | None,
) -> Tuple[bool, Dict[str, str], Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    rows_dir = out_dir / "rows"
    rows_dir.mkdir(parents=True, exist_ok=True)
    alignment_path = out_dir / "alignment.json"

    import os

    env = os.environ.copy()
    env["CARDIO_GRAPH_GRAPH_DIR"] = graph_dir
    env["CARDIO_GRAPH_TABLE22_GROUND_TRUTH_PATH"] = ground_truth_path
    env["CARDIO_GRAPH_TABLE22_RULES_PATH"] = rules_path
    env["CARDIO_GRAPH_TABLE22_TABLE_IDS"] = table_ids
    env["CARDIO_GRAPH_TABLE22_ENTRY_MATCH_THRESHOLD"] = str(entry_match_threshold)
    env["CARDIO_GRAPH_TABLE22_SKIP_ROWS"] = skip_rows
    env["CARDIO_GRAPH_TABLE22_TARGET_ROWS"] = ",".join(row_ids)
    env["CARDIO_GRAPH_TABLE22_REPORT_MD"] = str(out_dir / "overview.md")
    env["CARDIO_GRAPH_TABLE22_REPORT_JSON"] = str(alignment_path)
    env["CARDIO_GRAPH_TABLE22_REPORT_CSV"] = str(out_dir / "summary.csv")
    env["CARDIO_GRAPH_TABLE22_ROWS_DIR"] = str(rows_dir)
    env["CARDIO_GRAPH_TABLE22_LIVE_LLM"] = "true" if live_llm else "false"
    env["CARDIO_GRAPH_TABLE22_LLM_MODEL"] = model_name
    env["CARDIO_GRAPH_TABLE22_LLM_NODE"] = node
    env["CARDIO_GRAPH_TABLE22_LLM_PORT"] = str(port)
    env["CARDIO_GRAPH_TABLE22_USE_SNAPSHOT"] = "true" if use_snapshot else "false"
    env["CARDIO_GRAPH_TABLE22_GROUND_AFTER_EXTRACTION"] = (
        "true" if ground_after_extraction else "false"
    )
    env["CARDIO_GRAPH_EXTRACTION_PROMPT_APPENDIX_PATH"] = str(prompt_appendix_path)
    env["CARDIO_GRAPH_TUNING_SPLIT_NAME"] = split_name
    if benchmark_manifest:
        env["CARDIO_GRAPH_TUNING_BENCHMARK_MANIFEST"] = benchmark_manifest

    click.echo(
        "[autotune] eval_start "
        f"split={split_name} rows={len(row_ids)} model={model_name} node={node}:{port} "
        f"prompt={prompt_appendix_path.name} out_dir={out_dir}"
    )

    eval_start = time.time()
    process = subprocess.Popen(
        eval_command,
        shell=True,
        env=env,
        cwd=Path(__file__).resolve().parents[3],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    output_lines: List[str] = []
    if process.stdout is not None:
        for line in process.stdout:
            clean = line.rstrip("\n")
            output_lines.append(clean)
            if clean.strip() and stream_eval_logs:
                click.echo(f"[eval:{split_name}] {clean}")

    completed_return_code = process.wait()
    combined_output = "\n".join(output_lines)
    duration = time.time() - eval_start
    if not stream_eval_logs:
        marker_done = bool(re.search(r"\[table22-dev-eval\]\s+done", combined_output))
        marker_failed = bool(
            re.search(r"\[table22-dev-eval\]\s+failed", combined_output)
        )
        marker_skipped = bool(
            re.search(r"\[table22-dev-eval\]\s+skipped", combined_output)
        )
        click.echo(
            "[autotune] eval_stream_summary "
            f"split={split_name} lines={len(output_lines)} rc={completed_return_code} "
            f"marker_done={marker_done} marker_failed={marker_failed} marker_skipped={marker_skipped} "
            f"wall_s={duration:.1f}"
        )
    logs = {
        "stdout": combined_output,
        "stderr": "",
        "return_code": str(completed_return_code),
        "split": split_name,
    }
    success = completed_return_code == 0 and alignment_path.exists()
    click.echo(
        "[autotune] eval_done "
        f"split={split_name} rc={completed_return_code} alignment_exists={alignment_path.exists()}"
    )
    return success, logs, alignment_path


@click.command()
@click.option(
    "--split-manifest",
    type=click.Path(path_type=Path),
    default=Path("config/autotuning/split_v1.json"),
    show_default=True,
)
@click.option("--iterations", type=int, default=5, show_default=True)
@click.option("--run-locked-every", type=int, default=3, show_default=True)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    default=autotuning_dry_run_dir("table_22"),
    show_default=True,
)
@click.option("--seed", type=int, default=22, show_default=True)
@click.option("--candidates-per-iter", type=int, default=3, show_default=True)
@click.option("--early-stop-patience", type=int, default=2, show_default=True)
@click.option("--ucb-exploration", type=float, default=0.02, show_default=True)
@click.option("--model", default="Qwen3next", show_default=True)
@click.option("--node", default="g5", show_default=True)
@click.option("--port", type=int, default=11435, show_default=True)
@click.option("--graph-dir", default=DEFAULT_GRAPH_DIR, show_default=True)
@click.option(
    "--ground-truth-path", default=DEFAULT_GROUND_TRUTH_PATH, show_default=True
)
@click.option("--rules-path", default=DEFAULT_RULES_PATH, show_default=True)
@click.option("--table-ids", default="0", show_default=True)
@click.option("--entry-match-threshold", type=float, default=0.6, show_default=True)
@click.option("--skip-rows", default="", show_default=True)
@click.option("--live-llm/--no-live-llm", default=True, show_default=True)
@click.option("--use-snapshot/--no-use-snapshot", default=False, show_default=True)
@click.option(
    "--llm2-model",
    default=None,
    help="Override model for LLM2 analyst (defaults to --model).",
)
@click.option(
    "--llm3-model",
    default=None,
    help="Override model for LLM3 optimizer (defaults to --model).",
)
@click.option(
    "--ground-after-extraction/--no-ground-after-extraction",
    default=False,
    show_default=True,
)
@click.option(
    "--eval-command",
    default=("poetry run python -m cardio_graph_core.tuning.table_multi_dev_eval"),
    show_default=True,
)
@click.option(
    "--benchmark-manifest",
    type=click.Path(path_type=Path),
    default=Path("config/autotuning/benchmark_manifest_v1.jsonc"),
    show_default=True,
)
@click.option(
    "--stream-eval-logs/--no-stream-eval-logs",
    default=False,
    show_default=True,
    help="Stream full evaluator stdout into autotune log.",
)
@click.option(
    "--initial-prompt-appendix",
    type=click.Path(path_type=Path),
    default=None,
    help=(
        "Optional path to initial tuning appendix text. "
        "If omitted, controller starts from an empty appendix."
    ),
)
@click.option(
    "--dry-run/--no-dry-run",
    default=True,
    show_default=True,
    help="Dry-run simulates extraction/scoring; no-dry-run executes full extraction loop.",
)
def main(
    split_manifest: Path,
    iterations: int,
    run_locked_every: int,
    output_dir: Path,
    seed: int,
    candidates_per_iter: int,
    early_stop_patience: int,
    ucb_exploration: float,
    model: str,
    node: str,
    port: int,
    graph_dir: str,
    ground_truth_path: str,
    rules_path: str,
    table_ids: str,
    entry_match_threshold: float,
    skip_rows: str,
    live_llm: bool,
    use_snapshot: bool,
    llm2_model: str | None,
    llm3_model: str | None,
    ground_after_extraction: bool,
    eval_command: str,
    benchmark_manifest: Path,
    stream_eval_logs: bool,
    initial_prompt_appendix: Path | None,
    dry_run: bool,
) -> None:
    if candidates_per_iter <= 0:
        raise click.ClickException("candidates_per_iter must be > 0")
    manifest = _load_split_manifest(split_manifest)
    resolved_benchmark_manifest = None
    if benchmark_manifest and benchmark_manifest.is_file():
        resolved_benchmark_manifest = str(benchmark_manifest)
    elif manifest.benchmark_manifest:
        candidate_manifest = Path(manifest.benchmark_manifest)
        if candidate_manifest.is_file():
            resolved_benchmark_manifest = str(candidate_manifest)

    rng = random.Random(seed)
    thresholds = GateThresholds(
        min_rule_exact_gain=_env_float(
            "CARDIO_GRAPH_TUNING_MIN_RULE_EXACT_GAIN", 0.005
        ),
        max_secondary_drop=_env_float("CARDIO_GRAPH_TUNING_MAX_SECONDARY_DROP", 0.01),
        max_locked_test_drop=_env_float(
            "CARDIO_GRAPH_TUNING_MAX_LOCKED_TEST_DROP", 0.01
        ),
        min_locked_test_operator_gain=_env_float(
            "CARDIO_GRAPH_TUNING_MIN_LOCKED_OPERATOR_GAIN", 0.0
        ),
        bootstrap_rule_exact_floor=_env_float(
            "CARDIO_GRAPH_TUNING_BOOTSTRAP_RULE_EXACT_FLOOR", 0.05
        ),
        bootstrap_min_concept_f1_gain=_env_float(
            "CARDIO_GRAPH_TUNING_BOOTSTRAP_MIN_CONCEPT_F1_GAIN", 0.03
        ),
        bootstrap_max_operator_drop=_env_float(
            "CARDIO_GRAPH_TUNING_BOOTSTRAP_MAX_OPERATOR_DROP", 0.005
        ),
        bootstrap_max_logic_drop=_env_float(
            "CARDIO_GRAPH_TUNING_BOOTSTRAP_MAX_LOGIC_DROP", 0.005
        ),
        cold_start_rule_exact_floor=_env_float(
            "CARDIO_GRAPH_TUNING_COLD_START_RULE_EXACT_FLOOR", 0.01
        ),
        cold_start_min_operator_gain=_env_float(
            "CARDIO_GRAPH_TUNING_COLD_START_MIN_OPERATOR_GAIN", 0.10
        ),
        cold_start_min_logic_gain=_env_float(
            "CARDIO_GRAPH_TUNING_COLD_START_MIN_LOGIC_GAIN", 0.10
        ),
        cold_start_min_concept_f1_gain=_env_float(
            "CARDIO_GRAPH_TUNING_COLD_START_MIN_CONCEPT_F1_GAIN", 0.01
        ),
    )

    model_lower = model.lower()
    effective_llm2_model = llm2_model or model
    effective_llm3_model = llm3_model or model
    if "embed" in model_lower:
        if llm2_model is None:
            effective_llm2_model = DEFAULT_CHAT_TUNING_MODEL
        if llm3_model is None:
            effective_llm3_model = DEFAULT_CHAT_TUNING_MODEL

    llm2 = ErrorAnalyst(model_name=effective_llm2_model, node=node, port=port)
    llm3 = PromptOptimizer(model_name=effective_llm3_model, node=node, port=port)

    run_tag = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    run_root = output_dir
    if run_root.exists():
        shutil.rmtree(run_root)
    run_root.mkdir(parents=True, exist_ok=True)
    prompts_dir = run_root / "prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)

    champion_prompt_path = prompts_dir / "prompt_v0.txt"
    initial_prompt_text = ""
    initial_prompt_source = "empty"

    if initial_prompt_appendix and initial_prompt_appendix.is_file():
        initial_prompt_text = initial_prompt_appendix.read_text(encoding="utf-8")
        initial_prompt_source = str(initial_prompt_appendix)
    else:
        env_initial_prompt = (
            os.environ.get("CARDIO_GRAPH_TUNING_INITIAL_PROMPT_APPENDIX_PATH", "") or ""
        ).strip()
        if env_initial_prompt:
            env_path = Path(env_initial_prompt)
            if env_path.is_file():
                initial_prompt_text = env_path.read_text(encoding="utf-8")
                initial_prompt_source = env_initial_prompt

    champion_prompt_path.write_text(initial_prompt_text, encoding="utf-8")

    champion_prompt = "prompt_v0"
    champion_dev = _initial_metrics()
    champion_test = _initial_metrics()
    accepted_promotions = 0
    consecutive_no_promotion = 0
    zone_stats: Dict[str, Dict[str, float]] = {}
    total_zone_uses = 0
    iterations_executed = 0

    click.echo(
        "[autotune] start "
        f"run_tag={run_tag} dry_run={dry_run} iterations={iterations} run_locked_every={run_locked_every} "
        f"candidates_per_iter={candidates_per_iter} early_stop_patience={early_stop_patience}"
    )
    click.echo(
        "[autotune] initial_prompt "
        f"source={initial_prompt_source} lines={len(initial_prompt_text.splitlines())}"
    )
    click.echo(
        "[autotune] models "
        f"extractor={model}@{node}:{port} llm2={effective_llm2_model} llm3={effective_llm3_model}"
    )
    click.echo(
        "[autotune] data "
        f"graph_dir={graph_dir} table_ids={table_ids} entry_threshold={entry_match_threshold} "
        f"skip_rows={skip_rows or '-'} snapshot={use_snapshot}"
    )
    click.echo(
        "[autotune] splits "
        f"dev_rows={manifest.dev_rows} locked_test_rows={manifest.locked_test_rows}"
    )
    click.echo(f"[autotune] run_root={run_root}")

    summary_config_payload = {
        "model": model,
        "node": node,
        "port": port,
        "graph_dir": graph_dir,
        "ground_truth_path": ground_truth_path,
        "rules_path": rules_path,
        "table_ids": table_ids,
        "entry_match_threshold": entry_match_threshold,
        "skip_rows": skip_rows,
        "live_llm": live_llm,
        "use_snapshot": use_snapshot,
        "llm2_model": llm2_model or model,
        "llm3_model": llm3_model or model,
        "eval_command": eval_command,
        "benchmark_manifest": resolved_benchmark_manifest,
        "ground_after_extraction": ground_after_extraction,
        "candidates_per_iter": candidates_per_iter,
        "early_stop_patience": early_stop_patience,
        "ucb_exploration": ucb_exploration,
    }
    _write_run_summary(
        run_root=run_root,
        run_tag=run_tag,
        manifest=manifest,
        iterations=iterations,
        iterations_executed=0,
        accepted_promotions=accepted_promotions,
        champion_prompt=champion_prompt,
        champion_dev=champion_dev,
        champion_test=champion_test,
        dry_run=dry_run,
        config_payload=summary_config_payload,
    )

    for iteration in range(1, iterations + 1):
        iterations_executed = iteration
        iteration_dir = run_root / f"iter_{iteration:02d}"
        iteration_dir.mkdir(parents=True, exist_ok=True)

        run_id = f"dev_iter_{iteration:02d}"
        click.echo(
            "[autotune] iteration_start "
            f"iteration={iteration}/{iterations} champion={champion_prompt}"
        )

        if dry_run:
            simulated_rows = _simulate_error_rows(manifest.dev_rows, rng)
            score_report_champion = ScoreReport(
                run_id=f"{run_id}_champion",
                split="dev",
                prompt_version=champion_prompt,
                metrics=champion_dev,
                rows=simulated_rows,
            )
        else:
            champion_dev_dir = iteration_dir / "champion_dev"
            champion_ok, champion_logs, champion_alignment = _run_evaluation(
                split_name="dev",
                row_ids=manifest.dev_rows,
                out_dir=champion_dev_dir,
                prompt_appendix_path=champion_prompt_path,
                eval_command=eval_command,
                model_name=model,
                node=node,
                port=port,
                ground_after_extraction=ground_after_extraction,
                stream_eval_logs=stream_eval_logs,
                graph_dir=graph_dir,
                ground_truth_path=ground_truth_path,
                rules_path=rules_path,
                table_ids=table_ids,
                entry_match_threshold=entry_match_threshold,
                skip_rows=skip_rows,
                live_llm=live_llm,
                use_snapshot=use_snapshot,
                benchmark_manifest=resolved_benchmark_manifest,
            )
            _write_json(iteration_dir / "champion_dev_logs.json", champion_logs)
            score_report_champion = build_score_report_from_alignment(
                alignment_path=champion_alignment,
                run_id=f"{run_id}_champion",
                split="dev",
                prompt_version=champion_prompt,
                run_success=champion_ok,
            )
            champion_dev = score_report_champion.metrics

        analysis = llm2.analyze(score_report_champion)
        click.echo(
            "[autotune] llm2_done "
            f"iteration={iteration} targets={analysis.selected_targets} "
            f"status={llm2.last_debug.get('status', 'unknown')}"
        )
        _write_json(
            iteration_dir / "llm2_debug.json", llm2.last_debug or {"status": "missing"}
        )
        _write_json(
            iteration_dir / "score_report_dev_champion.json",
            score_report_champion.to_dict(),
        )
        _write_json(iteration_dir / "error_analysis.json", analysis.to_dict())

        accepted_candidates: List[dict] = []
        all_candidates: List[dict] = []
        for candidate_index in range(1, candidates_per_iter + 1):
            challenger_prompt = f"prompt_v{iteration}_candidate_{candidate_index:02d}"
            candidate_dir = iteration_dir / f"candidate_{candidate_index:02d}"
            candidate_dir.mkdir(parents=True, exist_ok=True)
            click.echo(
                "[autotune] candidate_start "
                f"iteration={iteration} candidate={candidate_index}/{candidates_per_iter} "
                f"name={challenger_prompt}"
            )

            patch = llm3.propose_patch(
                base_prompt_version=champion_prompt,
                candidate_prompt_version=challenger_prompt,
                current_prompt_appendix=champion_prompt_path.read_text(
                    encoding="utf-8"
                ),
                analysis=analysis,
                score_report=score_report_champion,
                candidate_slot=f"{candidate_index}/{candidates_per_iter}",
            )
            _write_json(
                candidate_dir / "llm3_debug.json",
                llm3.last_debug or {"status": "missing"},
            )
            _write_json(candidate_dir / "prompt_patch.json", patch.to_dict())

            safe, reason = is_patch_safe(patch)
            _write_json(
                candidate_dir / "patch_safety.json", {"safe": safe, "reason": reason}
            )
            if not safe:
                click.echo(
                    "[autotune] patch_rejected "
                    f"iteration={iteration} candidate={candidate_index} reason={reason}"
                )
                continue

            candidate_prompt_path = prompts_dir / f"{challenger_prompt}.txt"
            candidate_prompt_text = apply_prompt_patch(
                champion_prompt_path.read_text(encoding="utf-8"),
                patch,
            )
            candidate_prompt_path.write_text(candidate_prompt_text, encoding="utf-8")

            if dry_run:
                challenger_dev = _simulate_metrics(
                    champion_dev, rng, favor_rule_gain=True
                )
                score_report = ScoreReport(
                    run_id=f"{run_id}_cand_{candidate_index:02d}",
                    split="dev",
                    prompt_version=challenger_prompt,
                    metrics=challenger_dev,
                    rows=score_report_champion.rows,
                )
            else:
                challenger_dev_dir = candidate_dir / "challenger_dev"
                challenger_ok, challenger_logs, challenger_alignment = _run_evaluation(
                    split_name="dev",
                    row_ids=manifest.dev_rows,
                    out_dir=challenger_dev_dir,
                    prompt_appendix_path=candidate_prompt_path,
                    eval_command=eval_command,
                    model_name=model,
                    node=node,
                    port=port,
                    ground_after_extraction=ground_after_extraction,
                    stream_eval_logs=stream_eval_logs,
                    graph_dir=graph_dir,
                    ground_truth_path=ground_truth_path,
                    rules_path=rules_path,
                    table_ids=table_ids,
                    entry_match_threshold=entry_match_threshold,
                    skip_rows=skip_rows,
                    live_llm=live_llm,
                    use_snapshot=use_snapshot,
                    benchmark_manifest=resolved_benchmark_manifest,
                )
                _write_json(candidate_dir / "challenger_dev_logs.json", challenger_logs)
                score_report = build_score_report_from_alignment(
                    alignment_path=challenger_alignment,
                    run_id=f"{run_id}_cand_{candidate_index:02d}",
                    split="dev",
                    prompt_version=challenger_prompt,
                    run_success=challenger_ok,
                )
                challenger_dev = score_report.metrics

            dev_decision = evaluate_dev_gates(champion_dev, challenger_dev, thresholds)
            _write_json(candidate_dir / "score_report_dev.json", score_report.to_dict())
            _write_json(
                candidate_dir / "gate_decision_dev.json", dev_decision.to_dict()
            )

            base_utility = _candidate_utility(dev_decision.deltas)
            zones = _patch_zones(patch)
            ucb_bonus = _ucb_bonus(
                zones=zones,
                zone_stats=zone_stats,
                total_zone_uses=total_zone_uses,
                exploration_weight=ucb_exploration,
            )
            ranking_score = base_utility + ucb_bonus

            click.echo(
                "[autotune] dev_gate "
                f"iteration={iteration} candidate={candidate_index} accepted={dev_decision.accepted} "
                f"score={ranking_score:.4f} base={base_utility:.4f} ucb_bonus={ucb_bonus:.4f}"
            )
            candidate_record = {
                "candidate_index": candidate_index,
                "prompt_name": challenger_prompt,
                "prompt_path": candidate_prompt_path,
                "metrics": challenger_dev,
                "dev_decision": dev_decision,
                "zones": zones,
                "ranking_score": ranking_score,
                "base_utility": base_utility,
            }
            all_candidates.append(candidate_record)
            if dev_decision.accepted:
                accepted_candidates.append(candidate_record)

        ranked_all_candidates = sorted(
            all_candidates,
            key=lambda item: (
                item["ranking_score"],
                item["dev_decision"].deltas.get("rule_exact_match", 0.0),
                item["dev_decision"].deltas.get("concept_f1", 0.0),
            ),
            reverse=True,
        )
        _write_json(
            iteration_dir / "candidate_ranking.json",
            {
                "selected_candidate": (
                    next(
                        (
                            item["candidate_index"]
                            for item in ranked_all_candidates
                            if item["dev_decision"].accepted
                        ),
                        None,
                    )
                ),
                "accepted_candidates": [
                    {
                        "candidate_index": item["candidate_index"],
                        "prompt_name": item["prompt_name"],
                        "ranking_score": item["ranking_score"],
                        "base_utility": item["base_utility"],
                        "zones": sorted(item["zones"]),
                        "deltas": item["dev_decision"].deltas,
                    }
                    for item in ranked_all_candidates
                    if item["dev_decision"].accepted
                ],
                "all_candidates": [
                    {
                        "candidate_index": item["candidate_index"],
                        "prompt_name": item["prompt_name"],
                        "accepted": item["dev_decision"].accepted,
                        "reasons": item["dev_decision"].reasons,
                        "ranking_score": item["ranking_score"],
                        "base_utility": item["base_utility"],
                        "zones": sorted(item["zones"]),
                        "deltas": item["dev_decision"].deltas,
                        "metrics": item["metrics"].to_dict(),
                    }
                    for item in ranked_all_candidates
                ],
            },
        )

        promotion_reason = "dev_gate_fail"
        selected_candidate = None
        if accepted_candidates:
            accepted_candidates = sorted(
                accepted_candidates,
                key=lambda item: (
                    item["ranking_score"],
                    item["dev_decision"].deltas.get("rule_exact_match", 0.0),
                    item["dev_decision"].deltas.get("concept_f1", 0.0),
                ),
                reverse=True,
            )
            selected_candidate = accepted_candidates[0]

            run_locked_checkpoint = (accepted_promotions + 1) % run_locked_every == 0
            if run_locked_checkpoint:
                if dry_run:
                    challenger_test = _simulate_metrics(
                        champion_test, rng, favor_rule_gain=True
                    )
                else:
                    champion_test_dir = iteration_dir / "champion_test"
                    champion_test_ok, champion_test_logs, champion_test_alignment = (
                        _run_evaluation(
                            split_name="locked_test",
                            row_ids=manifest.locked_test_rows,
                            out_dir=champion_test_dir,
                            prompt_appendix_path=champion_prompt_path,
                            eval_command=eval_command,
                            model_name=model,
                            node=node,
                            port=port,
                            ground_after_extraction=ground_after_extraction,
                            stream_eval_logs=stream_eval_logs,
                            graph_dir=graph_dir,
                            ground_truth_path=ground_truth_path,
                            rules_path=rules_path,
                            table_ids=table_ids,
                            entry_match_threshold=entry_match_threshold,
                            skip_rows=skip_rows,
                            live_llm=live_llm,
                            use_snapshot=use_snapshot,
                            benchmark_manifest=resolved_benchmark_manifest,
                        )
                    )
                    _write_json(
                        iteration_dir / "champion_test_logs.json", champion_test_logs
                    )
                    champion_test_report = build_score_report_from_alignment(
                        alignment_path=champion_test_alignment,
                        run_id=f"{run_id}_test_champion",
                        split="locked_test",
                        prompt_version=champion_prompt,
                        run_success=champion_test_ok,
                    )
                    champion_test = champion_test_report.metrics

                    challenger_test_dir = iteration_dir / "challenger_test"
                    (
                        challenger_test_ok,
                        challenger_test_logs,
                        challenger_test_alignment,
                    ) = _run_evaluation(
                        split_name="locked_test",
                        row_ids=manifest.locked_test_rows,
                        out_dir=challenger_test_dir,
                        prompt_appendix_path=selected_candidate["prompt_path"],
                        eval_command=eval_command,
                        model_name=model,
                        node=node,
                        port=port,
                        ground_after_extraction=ground_after_extraction,
                        stream_eval_logs=stream_eval_logs,
                        graph_dir=graph_dir,
                        ground_truth_path=ground_truth_path,
                        rules_path=rules_path,
                        table_ids=table_ids,
                        entry_match_threshold=entry_match_threshold,
                        skip_rows=skip_rows,
                        live_llm=live_llm,
                        use_snapshot=use_snapshot,
                        benchmark_manifest=resolved_benchmark_manifest,
                    )
                    _write_json(
                        iteration_dir / "challenger_test_logs.json",
                        challenger_test_logs,
                    )
                    challenger_test_report = build_score_report_from_alignment(
                        alignment_path=challenger_test_alignment,
                        run_id=f"{run_id}_test_challenger",
                        split="locked_test",
                        prompt_version=selected_candidate["prompt_name"],
                        run_success=challenger_test_ok,
                    )
                    challenger_test = challenger_test_report.metrics
                    _write_json(
                        iteration_dir / "score_report_locked_test_champion.json",
                        champion_test_report.to_dict(),
                    )
                    _write_json(
                        iteration_dir / "score_report_locked_test_challenger.json",
                        challenger_test_report.to_dict(),
                    )

                test_decision = evaluate_locked_test_gate(
                    champion_test, challenger_test, thresholds
                )
                _write_json(
                    iteration_dir / "gate_decision_locked_test.json",
                    test_decision.to_dict(),
                )
                if test_decision.accepted:
                    champion_test = challenger_test
                    champion_dev = selected_candidate["metrics"]
                    champion_prompt = selected_candidate["prompt_name"]
                    champion_prompt_path = selected_candidate["prompt_path"]
                    accepted_promotions += 1
                    for zone in selected_candidate["zones"]:
                        entry = zone_stats.setdefault(
                            zone, {"uses": 0.0, "utility_sum": 0.0}
                        )
                        entry["uses"] += 1.0
                        entry["utility_sum"] += selected_candidate["base_utility"]
                    total_zone_uses += len(selected_candidate["zones"])
                    promotion_reason = "accepted_with_locked_test"
                else:
                    promotion_reason = "locked_test_regression"
            else:
                champion_dev = selected_candidate["metrics"]
                champion_prompt = selected_candidate["prompt_name"]
                champion_prompt_path = selected_candidate["prompt_path"]
                accepted_promotions += 1
                for zone in selected_candidate["zones"]:
                    entry = zone_stats.setdefault(
                        zone, {"uses": 0.0, "utility_sum": 0.0}
                    )
                    entry["uses"] += 1.0
                    entry["utility_sum"] += selected_candidate["base_utility"]
                total_zone_uses += len(selected_candidate["zones"])
                promotion_reason = "accepted_dev_only"

        if promotion_reason.startswith("accepted"):
            consecutive_no_promotion = 0
        else:
            consecutive_no_promotion += 1

        summary_payload = {
            "iteration": iteration,
            "champion_prompt_after_iteration": champion_prompt,
            "accepted_promotions": accepted_promotions,
            "promotion_reason": promotion_reason,
            "evaluated_candidates": candidates_per_iter,
            "accepted_candidates": len(accepted_candidates),
            "selected_candidate": (
                selected_candidate["candidate_index"] if selected_candidate else None
            ),
            "consecutive_no_promotion": consecutive_no_promotion,
            "dev_metrics": champion_dev.to_dict(),
        }
        _write_json(iteration_dir / "iteration_summary.json", summary_payload)
        _write_run_summary(
            run_root=run_root,
            run_tag=run_tag,
            manifest=manifest,
            iterations=iterations,
            iterations_executed=iterations_executed,
            accepted_promotions=accepted_promotions,
            champion_prompt=champion_prompt,
            champion_dev=champion_dev,
            champion_test=champion_test,
            dry_run=dry_run,
            config_payload=summary_config_payload,
        )
        click.echo(
            "[autotune] iteration_done "
            f"iteration={iteration} promotion_reason={promotion_reason} "
            f"champion_now={champion_prompt} accepted_promotions={accepted_promotions}"
        )

        if (
            early_stop_patience > 0
            and consecutive_no_promotion >= early_stop_patience
            and iteration < iterations
        ):
            click.echo(
                "[autotune] early_stop "
                f"iteration={iteration} reason=no_promotion_for_{consecutive_no_promotion}_iterations"
            )
            break

    _write_run_summary(
        run_root=run_root,
        run_tag=run_tag,
        manifest=manifest,
        iterations=iterations,
        iterations_executed=iterations_executed,
        accepted_promotions=accepted_promotions,
        champion_prompt=champion_prompt,
        champion_dev=champion_dev,
        champion_test=champion_test,
        dry_run=dry_run,
        config_payload=summary_config_payload,
    )
    mode = "dryrun" if dry_run else "live"
    run_success = accepted_promotions > 0
    click.echo(
        "[autotune] finished "
        f"run_tag={run_tag} accepted_promotions={accepted_promotions} final_prompt={champion_prompt}"
    )
    click.echo(
        "[autotune] outcome "
        f"success={run_success} iterations_executed={iterations_executed} "
        f"final_rule_exact_match={champion_dev.rule_exact_match:.3f}"
    )
    click.echo(f"[autotune-{mode}] artifacts written to: {run_root}")


if __name__ == "__main__":
    main()
