# Tests: Table 22 Row-by-Row Comparison Artifacts

This README focuses on:

- `tests/test_table_22_concept_rules.py`

The test generates markdown comparison artifacts per row (`row_01.md`, ...), plus summary JSON/CSV.

## What it generates

Output files:

- `table22_rowwise_comparison.md`
- `table22_rowwise_alignment.json`
- `table22_rowwise_summary.csv`
- `rows/row_XX.md` (one file per row)

Default output directory is `docs/table22_rows_comparison/` unless overridden by env vars.

## Two run modes

### 1) Snapshot mode (reuse existing LLM side)

Use this when you already have a previous alignment JSON and want to regenerate markdown artifacts quickly.

Required env:

- `CARDIO_GRAPH_TABLE22_USE_SNAPSHOT=true`
- `CARDIO_GRAPH_TABLE22_LLM_SNAPSHOT=<path to table22_rowwise_alignment.json>`

Optional:

- `CARDIO_GRAPH_TABLE22_GROUND_TRUTH_PATH` to control left-side human annotations.

### 2) Live mode (fresh LLM extraction + fresh grounding)

Use this for new extraction/grounding runs.

Required env:

- `CARDIO_GRAPH_TABLE22_LIVE_LLM=true`
- `CARDIO_GRAPH_TABLE22_GROUND_AFTER_EXTRACTION=true`
- `CARDIO_GRAPH_TABLE22_USE_SNAPSHOT=false`

Typical LLM endpoint settings:

- `CARDIO_GRAPH_TABLE22_LLM_MODEL=Qwen30b`
- `CARDIO_GRAPH_TABLE22_LLM_NODE=g5`
- `CARDIO_GRAPH_TABLE22_LLM_PORT=11435`

Ground truth path (finalized manual annotations):

- `CARDIO_GRAPH_TABLE22_GROUND_TRUTH_PATH=/prj/doctoral_letters/guide/data/evaluation/table_22_manual_snomed.json`

## Minimal commands

From repository root:

```bash
cd /home/pwiesenbach/CardioGuidelinesGraph
```

Live run example:

```bash
export CARDIO_GRAPH_TABLE22_GROUND_TRUTH_PATH=/prj/doctoral_letters/guide/data/evaluation/table_22_manual_snomed.json
export CARDIO_GRAPH_TABLE22_LIVE_LLM=true
export CARDIO_GRAPH_TABLE22_GROUND_AFTER_EXTRACTION=true
export CARDIO_GRAPH_TABLE22_USE_SNAPSHOT=false
export CARDIO_GRAPH_TABLE22_LLM_MODEL=Qwen30b
export CARDIO_GRAPH_TABLE22_LLM_NODE=g5
export CARDIO_GRAPH_TABLE22_LLM_PORT=11435

poetry run python -m unittest -v tests.test_table_22_concept_rules.Table22ConceptRulesTests.test_table_22_rules_match_ground_truth
```

Snapshot run example:

```bash
export CARDIO_GRAPH_TABLE22_USE_SNAPSHOT=true
export CARDIO_GRAPH_TABLE22_LLM_SNAPSHOT=/home/pwiesenbach/CardioGuidelinesGraph/docs/table22_rows_comparison/table22_rowwise_alignment.json

poetry run python -m unittest -v tests.test_table_22_concept_rules.Table22ConceptRulesTests.test_table_22_rules_match_ground_truth
```

## Commit-safe SLURM launcher (for colleagues)

Because `slurm/` is ignored, use this tracked launcher instead:

```bash
cd /home/pwiesenbach/CardioGuidelinesGraph
poetry run python -m cardio_graph_core.tuning.launch_table22_concept_rules
```

It submits a SLURM job equivalent to `slurm/run_table22_concept_rules_tests.sh` with:

- live LLM extraction,
- fresh grounding,
- snapshot mode disabled,
- default output in `docs/table22_rows_comparison/`.

Optional overrides:

```bash
poetry run python -m cardio_graph_core.tuning.launch_table22_concept_rules \
	--node g5 --port 11435 --model Qwen30b \
	--target-rows row_01,row_02 \
	--out-dir /home/pwiesenbach/CardioGuidelinesGraph/docs/table22_rows_comparison
```

## Useful optional env vars

- `CARDIO_GRAPH_TABLE22_TARGET_ROWS=row_01,row_02,...` to limit rows
- `CARDIO_GRAPH_TABLE22_SKIP_ROWS=row_01,...` to skip rows
- `CARDIO_GRAPH_TABLE22_REPORT_MD=<path>`
- `CARDIO_GRAPH_TABLE22_REPORT_JSON=<path>`
- `CARDIO_GRAPH_TABLE22_REPORT_CSV=<path>`
- `CARDIO_GRAPH_TABLE22_ROWS_DIR=<path>`

## Quick validation checklist

After a run, verify:

1. `table22_rowwise_summary.csv` exists and has all expected rows.
2. `rows/row_XX.md` includes both Human Annotation and LLM Generated sections.
3. In live grounding mode, check `snomed_id` and `taxonomy_path` presence in row markdowns and alignment JSON.
