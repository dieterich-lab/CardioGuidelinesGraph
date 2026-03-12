# Multi-Table Auto-Tuning (Dev Split)

This module is for **auto-tuning only** (LLM2/LLM3 loop). It runs against a benchmark set that can include Table 22, Table 17, and Table 8.

## One command

```bash
cd /home/pwiesenbach/CardioGuidelinesGraph
poetry run python -m cardio_graph_core.tuning.launch_table22_tuning
```

Default behavior:

- Runs `cardio_graph_core.tuning.controller` in live mode (`--dry-run=false`)
- Uses `config/autotuning/split_v1.json` for row split control
- Uses benchmark manifest: `config/autotuning/benchmark_manifest_v1.jsonc`
- Uses multi-table eval wrapper: `cardio_graph_core.tuning.table_multi_dev_eval`
- Uses live extraction+grounding (`g5:11435` by default)
- Disables snapshot mode (`CARDIO_GRAPH_TABLE22_USE_SNAPSHOT=false`)
- Uses tolerant scoring profile by default (`CARDIO_GRAPH_TUNING_SCORE_PROFILE=tolerant`)
- Enables semantic alias normalization by default (`CARDIO_GRAPH_TUNING_ENABLE_SEMANTIC_NORMALIZATION=true`)

Optional semantic LLM matching (for phrase-equivalent variants beyond hardcoded aliases):

- `CARDIO_GRAPH_TUNING_LLM_SEMANTIC_MATCH=true`
- `CARDIO_GRAPH_TUNING_LLM_SEMANTIC_MAX_CALLS=50` (budget guard)
- `CARDIO_GRAPH_TUNING_LLM_SEMANTIC_MODEL=Qwen3next`
- `CARDIO_GRAPH_TUNING_LLM_SEMANTIC_NODE=g5`
- `CARDIO_GRAPH_TUNING_LLM_SEMANTIC_PORT=11435`

## Benchmark manifest

`config/autotuning/benchmark_manifest_v1.jsonc` contains one entry per table with:

- `ground_truth_path`
- `table_clean_path`
- `table_ids`
- `dev_rows` and `locked_test_rows` (optional per benchmark)

Set `CARDIO_GRAPH_TUNING_BENCHMARK_MANIFEST` to override this file.

## Monitor

The launcher prints job id + log path. Then use:

```bash
squeue -j <JOB_ID>
tail -f slurm/run_table22_autotune_dev_<RUN_TAG>.log
```

Cancel if needed:

```bash
scancel <JOB_ID>
```

## Outputs

Artifacts are written under:

- `docs/table22_tuning_runs/autotune_dev/<RUN_TAG>/`

Most important files:

- `run_summary.json`
- `iter_*/iteration_summary.json`
- `iter_*/score_report_dev_champion.json`
- `iter_*/candidate_*/prompt_patch.json`

## Later test evaluation

This launcher is intentionally dev-only.
After prompt selection is stable, run a separate locked-test evaluation workflow.
