from __future__ import annotations

import json
import random
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import click

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
from cardio_graph_core.tuning.llm_bridge import LLMBridge
from cardio_graph_core.tuning.prompt_optimizer import PromptOptimizer
from cardio_graph_core.tuning.prompt_patcher import apply_prompt_patch, is_patch_safe
from cardio_graph_core.tuning.score_adapter import build_score_report_from_alignment


def _load_split_manifest(path: Path) -> SplitManifest:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return SplitManifest.from_dict(payload)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


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
) -> Tuple[bool, Dict[str, str], Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    rows_dir = out_dir / "rows"
    rows_dir.mkdir(parents=True, exist_ok=True)
    alignment_path = out_dir / "table22_rowwise_alignment.json"

    import os

    env = os.environ.copy()
    env["CARDIO_GRAPH_TABLE22_TARGET_ROWS"] = ",".join(row_ids)
    env["CARDIO_GRAPH_TABLE22_REPORT_MD"] = str(
        out_dir / "table22_rowwise_comparison.md"
    )
    env["CARDIO_GRAPH_TABLE22_REPORT_JSON"] = str(alignment_path)
    env["CARDIO_GRAPH_TABLE22_REPORT_CSV"] = str(
        out_dir / "table22_rowwise_summary.csv"
    )
    env["CARDIO_GRAPH_TABLE22_ROWS_DIR"] = str(rows_dir)
    env["CARDIO_GRAPH_TABLE22_LIVE_LLM"] = "true"
    env["CARDIO_GRAPH_TABLE22_LLM_MODEL"] = model_name
    env["CARDIO_GRAPH_TABLE22_LLM_NODE"] = node
    env["CARDIO_GRAPH_TABLE22_LLM_PORT"] = str(port)
    env["CARDIO_GRAPH_TABLE22_GROUND_AFTER_EXTRACTION"] = (
        "true" if ground_after_extraction else "false"
    )
    env["CARDIO_GRAPH_EXTRACTION_PROMPT_APPENDIX_PATH"] = str(prompt_appendix_path)

    completed = subprocess.run(
        eval_command,
        shell=True,
        env=env,
        cwd=Path(__file__).resolve().parents[3],
        capture_output=True,
        text=True,
    )
    logs = {
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "return_code": str(completed.returncode),
        "split": split_name,
    }
    success = completed.returncode == 0 and alignment_path.exists()
    return success, logs, alignment_path


@click.command()
@click.option(
    "--split-manifest",
    type=click.Path(path_type=Path),
    default=Path("config/table22/split_v1.json"),
    show_default=True,
)
@click.option("--iterations", type=int, default=5, show_default=True)
@click.option("--run-locked-every", type=int, default=3, show_default=True)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    default=Path("docs/table22_tuning_runs/autotune_dryrun"),
    show_default=True,
)
@click.option("--seed", type=int, default=22, show_default=True)
@click.option("--model", default="Qwen30b", show_default=True)
@click.option("--node", default="g5", show_default=True)
@click.option("--port", type=int, default=11435, show_default=True)
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
    default=True,
    show_default=True,
)
@click.option(
    "--eval-command",
    default=(
        "poetry run python -m unittest -v "
        "tests.test_table_22_concept_rules.Table22ConceptRulesTests.test_table_22_rules_match_ground_truth"
    ),
    show_default=True,
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
    model: str,
    node: str,
    port: int,
    llm2_model: str | None,
    llm3_model: str | None,
    ground_after_extraction: bool,
    eval_command: str,
    dry_run: bool,
) -> None:
    manifest = _load_split_manifest(split_manifest)
    rng = random.Random(seed)
    thresholds = GateThresholds()

    llm2 = ErrorAnalyst(
        LLMBridge(
            model_name=llm2_model or model,
            node=node,
            port=port,
        )
    )
    llm3 = PromptOptimizer(
        LLMBridge(
            model_name=llm3_model or model,
            node=node,
            port=port,
        )
    )

    run_tag = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    run_root = output_dir / run_tag
    run_root.mkdir(parents=True, exist_ok=True)
    prompts_dir = run_root / "prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)

    champion_prompt_path = prompts_dir / "prompt_v0.txt"
    champion_prompt_path.write_text("", encoding="utf-8")

    champion_prompt = "prompt_v0"
    champion_dev = _initial_metrics()
    champion_test = _initial_metrics()
    accepted_promotions = 0

    for iteration in range(1, iterations + 1):
        iteration_dir = run_root / f"iter_{iteration:02d}"
        iteration_dir.mkdir(parents=True, exist_ok=True)

        run_id = f"dev_iter_{iteration:02d}"
        challenger_prompt = f"prompt_v{iteration}_candidate"

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
        _write_json(
            iteration_dir / "llm2_debug.json",
            llm2.last_debug or {"status": "missing"},
        )

        patch = llm3.propose_patch(
            base_prompt_version=champion_prompt,
            candidate_prompt_version=challenger_prompt,
            current_prompt_appendix=champion_prompt_path.read_text(encoding="utf-8"),
            analysis=analysis,
            score_report=score_report_champion,
        )
        _write_json(
            iteration_dir / "llm3_debug.json",
            llm3.last_debug or {"status": "missing"},
        )

        safe, reason = is_patch_safe(patch)
        _write_json(
            iteration_dir / "patch_safety.json",
            {"safe": safe, "reason": reason},
        )
        if not safe:
            _write_json(iteration_dir / "error_analysis.json", analysis.to_dict())
            _write_json(iteration_dir / "prompt_patch.json", patch.to_dict())
            _write_json(
                iteration_dir / "iteration_summary.json",
                {
                    "iteration": iteration,
                    "champion_prompt_after_iteration": champion_prompt,
                    "accepted_promotions": accepted_promotions,
                    "promotion_reason": "unsafe_patch",
                    "dev_metrics": champion_dev.to_dict(),
                },
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
                champion_dev,
                rng,
                favor_rule_gain=True,
            )
            score_report = ScoreReport(
                run_id=run_id,
                split="dev",
                prompt_version=challenger_prompt,
                metrics=challenger_dev,
                rows=score_report_champion.rows,
            )
        else:
            challenger_dev_dir = iteration_dir / "challenger_dev"
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
            )
            _write_json(iteration_dir / "challenger_dev_logs.json", challenger_logs)
            score_report = build_score_report_from_alignment(
                alignment_path=challenger_alignment,
                run_id=run_id,
                split="dev",
                prompt_version=challenger_prompt,
                run_success=challenger_ok,
            )
            challenger_dev = score_report.metrics

        dev_decision = evaluate_dev_gates(champion_dev, challenger_dev, thresholds)

        _write_json(
            iteration_dir / "score_report_dev_champion.json",
            score_report_champion.to_dict(),
        )
        _write_json(iteration_dir / "score_report_dev.json", score_report.to_dict())
        _write_json(iteration_dir / "error_analysis.json", analysis.to_dict())
        _write_json(iteration_dir / "prompt_patch.json", patch.to_dict())
        _write_json(iteration_dir / "gate_decision_dev.json", dev_decision.to_dict())

        promotion_reason = "dev_gate_fail"
        if dev_decision.accepted:
            run_locked_checkpoint = (accepted_promotions + 1) % run_locked_every == 0
            if run_locked_checkpoint:
                if dry_run:
                    challenger_test = _simulate_metrics(
                        champion_test,
                        rng,
                        favor_rule_gain=True,
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
                        )
                    )
                    _write_json(
                        iteration_dir / "champion_test_logs.json",
                        champion_test_logs,
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
                        prompt_appendix_path=candidate_prompt_path,
                        eval_command=eval_command,
                        model_name=model,
                        node=node,
                        port=port,
                        ground_after_extraction=ground_after_extraction,
                    )
                    _write_json(
                        iteration_dir / "challenger_test_logs.json",
                        challenger_test_logs,
                    )
                    challenger_test_report = build_score_report_from_alignment(
                        alignment_path=challenger_test_alignment,
                        run_id=f"{run_id}_test_challenger",
                        split="locked_test",
                        prompt_version=challenger_prompt,
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
                    champion_test,
                    challenger_test,
                    thresholds,
                )
                _write_json(
                    iteration_dir / "gate_decision_locked_test.json",
                    test_decision.to_dict(),
                )
                if test_decision.accepted:
                    champion_test = challenger_test
                    champion_dev = challenger_dev
                    champion_prompt = challenger_prompt
                    champion_prompt_path = candidate_prompt_path
                    accepted_promotions += 1
                    promotion_reason = "accepted_with_locked_test"
                else:
                    promotion_reason = "locked_test_regression"
            else:
                champion_dev = challenger_dev
                champion_prompt = challenger_prompt
                champion_prompt_path = candidate_prompt_path
                accepted_promotions += 1
                promotion_reason = "accepted_dev_only"

        summary_payload = {
            "iteration": iteration,
            "champion_prompt_after_iteration": champion_prompt,
            "accepted_promotions": accepted_promotions,
            "promotion_reason": promotion_reason,
            "dev_metrics": champion_dev.to_dict(),
        }
        _write_json(iteration_dir / "iteration_summary.json", summary_payload)

    final_summary = {
        "run_tag": run_tag,
        "split_version": manifest.split_version,
        "iterations": iterations,
        "accepted_promotions": accepted_promotions,
        "final_prompt": champion_prompt,
        "final_dev_metrics": champion_dev.to_dict(),
        "final_locked_test_metrics": champion_test.to_dict(),
        "dry_run": dry_run,
        "config": {
            "model": model,
            "node": node,
            "port": port,
            "llm2_model": llm2_model or model,
            "llm3_model": llm3_model or model,
            "eval_command": eval_command,
            "ground_after_extraction": ground_after_extraction,
        },
    }
    _write_json(run_root / "run_summary.json", final_summary)
    mode = "dryrun" if dry_run else "live"
    click.echo(f"[autotune-{mode}] artifacts written to: {run_root}")


if __name__ == "__main__":
    main()
