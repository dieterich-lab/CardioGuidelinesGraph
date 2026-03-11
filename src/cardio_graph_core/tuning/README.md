# Table 22 Auto-Tuning (Dev Split)

This module is for **auto-tuning only** (LLM2/LLM3 loop). It runs against the **dev split** of Table 22 and uses finalized manual annotations.

## One command

```bash
cd /home/pwiesenbach/CardioGuidelinesGraph
poetry run python -m cardio_graph_core.tuning.launch_table22_tuning
```

Default behavior:

- Runs `cardio_graph_core.tuning.controller` in live mode (`--dry-run=false`)
- Uses `config/table22/split_v1.json` (dev rows)
- Uses ground truth: `/prj/doctoral_letters/guide/data/evaluation/table_22_manual_1.3.json`
- Uses live extraction+grounding (`g5:11435` by default)
- Disables snapshot mode (`CARDIO_GRAPH_TABLE22_USE_SNAPSHOT=false`)

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
