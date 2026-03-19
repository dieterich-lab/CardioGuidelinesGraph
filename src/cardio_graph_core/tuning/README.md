# Multi-Table Auto-Tuning (Dev Split)

This package runs the LLM2/LLM3 prompt-optimization loop over a multi-table dev split (Table 22 + optional Table 17/8 rows from manifest).

## Quick start

Run the SLURM launcher:

```bash
cd /home/pwiesenbach/CardioGuidelinesGraph
poetry run python -m cardio_graph_core.tuning.launch_table22_tuning
```

## What the launcher actually does

`launch_table22_tuning` submits one SLURM job (`table22_autotune_dev`) with:

- partition: `small`
- memory: `12G`
- log file: `slurm/run_table22_autotune_dev_<RUN_TAG>.log`
- controller mode: live (`--no-dry-run`)
- controller split: `config/autotuning/split_v1.json`
- eval command: `poetry run python -m cardio_graph_core.tuning.table_multi_dev_eval`
- locked-test cadence: effectively disabled for launcher runs (`--run-locked-every 9999`)

Launcher defaults:

- model/node/port: `Qwen3next @ g5:11435`
- iterations: `5`
- candidates per iter: `3`
- table ids: `0`
- entry threshold: `0.6`
- snapshot mode: `false`
- ground-after-extraction: `false`
- score profile: `tolerant`
- lenient extras: `true`
- semantic normalization: `true`
- benchmark manifest: `config/autotuning/benchmark_manifest_v1.jsonc`
- output root: `docs/table22_tuning_runs/autotune_dev/`

## Controller defaults (if run directly)

`cardio_graph_core.tuning.controller` defaults differ from launcher defaults:

- `--dry-run=true`
- `--run-locked-every=3`
- `--early-stop-patience=2`
- `--ucb-exploration=0.02`
- `--output-dir=docs/table22_tuning_runs/autotune_dryrun`

If you run controller directly, ensure flags/env match your intended live experiment.

## Scoring + matching knobs

The score adapter now uses lexical + token-F1 style similarity with adaptive pair thresholds.

Key env vars:

- `CARDIO_GRAPH_TUNING_SCORE_PROFILE` (default `tolerant`)
- `CARDIO_GRAPH_TUNING_LENIENT_EXTRAS` (default `true`)
- `CARDIO_GRAPH_TUNING_ENABLE_SEMANTIC_NORMALIZATION` (default `true`)
- `CARDIO_GRAPH_TUNING_PAIR_MIN_THRESHOLD` (default `0.50`)

Optional LLM semantic equivalence:

- `CARDIO_GRAPH_TUNING_LLM_SEMANTIC_MATCH=true|false` (default `false`)
- `CARDIO_GRAPH_TUNING_LLM_SEMANTIC_MAX_CALLS` (budget guard; default `0` = disabled)
- `CARDIO_GRAPH_TUNING_LLM_SEMANTIC_MODEL` (default `Qwen3next`)
- `CARDIO_GRAPH_TUNING_LLM_SEMANTIC_NODE` (default `g5`)
- `CARDIO_GRAPH_TUNING_LLM_SEMANTIC_PORT` (default `11435`)

## Gate knobs (promotion acceptance)

Controller gates are env-configurable:

- `CARDIO_GRAPH_TUNING_MIN_RULE_EXACT_GAIN`
- `CARDIO_GRAPH_TUNING_MAX_SECONDARY_DROP`
- `CARDIO_GRAPH_TUNING_MAX_LOCKED_TEST_DROP`
- `CARDIO_GRAPH_TUNING_MIN_LOCKED_OPERATOR_GAIN`
- `CARDIO_GRAPH_TUNING_BOOTSTRAP_RULE_EXACT_FLOOR`
- `CARDIO_GRAPH_TUNING_BOOTSTRAP_MIN_CONCEPT_F1_GAIN`
- `CARDIO_GRAPH_TUNING_BOOTSTRAP_MAX_OPERATOR_DROP`
- `CARDIO_GRAPH_TUNING_BOOTSTRAP_MAX_LOGIC_DROP`
- `CARDIO_GRAPH_TUNING_COLD_START_RULE_EXACT_FLOOR`
- `CARDIO_GRAPH_TUNING_COLD_START_MIN_OPERATOR_GAIN`
- `CARDIO_GRAPH_TUNING_COLD_START_MIN_LOGIC_GAIN`
- `CARDIO_GRAPH_TUNING_COLD_START_MIN_CONCEPT_F1_GAIN`

## Monitor / cancel

After submit:

```bash
squeue -j <JOB_ID>
tail -f slurm/run_table22_autotune_dev_<RUN_TAG>.log
```

Cancel:

```bash
scancel <JOB_ID>
```

## Artifacts

Launcher runs write to:

- `docs/table22_tuning_runs/autotune_dev/<RUN_TAG>/`

Key files:

- `run_summary.json`
- `iter_*/iteration_summary.json`
- `iter_*/score_report_dev_champion.json`
- `iter_*/candidate_ranking.json`
- `iter_*/candidate_*/prompt_patch.json`
- `iter_*/candidate_*/gate_decision_dev.json`

## Scope note

This launcher is dev-focused. Use a separate workflow for final locked-test validation once prompt updates stabilize.
