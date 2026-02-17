from __future__ import annotations

import json
import random
from datetime import datetime
from pathlib import Path
from typing import List

import click

from cardio_graph_core.tuning.contracts import (
    ErrorAnalysis,
    ErrorClassSummary,
    ErrorItem,
    Metrics,
    PromptEdit,
    PromptPatch,
    RowErrors,
    ScoreReport,
    SplitManifest,
)
from cardio_graph_core.tuning.gates import (
    GateThresholds,
    evaluate_dev_gates,
    evaluate_locked_test_gate,
)


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


def _build_error_analysis(run_id: str) -> ErrorAnalysis:
    top_classes = [
        ErrorClassSummary(
            error_class="C1_operator_wrong",
            count=19,
            confidence=0.87,
            root_cause_hypothesis="scheduled context over-mapped to PLANNED",
        ),
        ErrorClassSummary(
            error_class="C6_logic_group_wrong",
            count=13,
            confidence=0.81,
            root_cause_hypothesis="grouping precedence too weakly specified",
        ),
    ]
    return ErrorAnalysis(
        run_id=run_id,
        top_classes=top_classes,
        selected_targets=[summary.error_class for summary in top_classes],
    )


def _build_prompt_patch(
    base_prompt_version: str,
    candidate_prompt_version: str,
    targets: List[str],
) -> PromptPatch:
    edits = [
        PromptEdit(
            zone="operator_resolution_rules",
            change_type="append",
            old="",
            new="When text indicates scheduling context only, do not force PLANNED unless explicit plan phrasing appears.",
        ),
        PromptEdit(
            zone="logic_grouping_rules",
            change_type="append",
            old="",
            new="Preserve OR groups explicitly when conjunctions/disjunctions appear in coordinated mentions.",
        ),
    ]
    return PromptPatch(
        base_prompt_version=base_prompt_version,
        candidate_prompt_version=candidate_prompt_version,
        target_classes=targets,
        edits=edits,
        max_edit_lines=30,
        rationale="Target top error classes with minimal rule-clarification edits.",
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
@click.option(
    "--dry-run/--no-dry-run",
    default=True,
    show_default=True,
    help="Dry-run uses simulated LLM/scorer outputs and only writes controller artifacts.",
)
def main(
    split_manifest: Path,
    iterations: int,
    run_locked_every: int,
    output_dir: Path,
    seed: int,
    dry_run: bool,
) -> None:
    if not dry_run:
        raise click.ClickException(
            "Only --dry-run mode is implemented in scaffold v0.1"
        )

    manifest = _load_split_manifest(split_manifest)
    rng = random.Random(seed)
    thresholds = GateThresholds()

    run_tag = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    run_root = output_dir / run_tag
    run_root.mkdir(parents=True, exist_ok=True)

    champion_prompt = "prompt_v0"
    champion_dev = _initial_metrics()
    champion_test = _initial_metrics()
    accepted_promotions = 0

    for iteration in range(1, iterations + 1):
        iteration_dir = run_root / f"iter_{iteration:02d}"
        iteration_dir.mkdir(parents=True, exist_ok=True)

        run_id = f"dev_iter_{iteration:02d}"
        simulated_rows = _simulate_error_rows(manifest.dev_rows, rng)
        analysis = _build_error_analysis(run_id)
        challenger_prompt = f"prompt_v{iteration}_candidate"
        patch = _build_prompt_patch(
            base_prompt_version=champion_prompt,
            candidate_prompt_version=challenger_prompt,
            targets=analysis.selected_targets,
        )

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
            rows=simulated_rows,
        )
        dev_decision = evaluate_dev_gates(champion_dev, challenger_dev, thresholds)

        _write_json(iteration_dir / "score_report_dev.json", score_report.to_dict())
        _write_json(iteration_dir / "error_analysis.json", analysis.to_dict())
        _write_json(iteration_dir / "prompt_patch.json", patch.to_dict())
        _write_json(iteration_dir / "gate_decision_dev.json", dev_decision.to_dict())

        promotion_reason = "dev_gate_fail"
        if dev_decision.accepted:
            run_locked_checkpoint = (accepted_promotions + 1) % run_locked_every == 0
            if run_locked_checkpoint:
                challenger_test = _simulate_metrics(
                    champion_test,
                    rng,
                    favor_rule_gain=True,
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
                    accepted_promotions += 1
                    promotion_reason = "accepted_with_locked_test"
                else:
                    promotion_reason = "locked_test_regression"
            else:
                champion_dev = challenger_dev
                champion_prompt = challenger_prompt
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
    }
    _write_json(run_root / "run_summary.json", final_summary)
    click.echo(f"[autotune-dryrun] artifacts written to: {run_root}")


if __name__ == "__main__":
    main()
