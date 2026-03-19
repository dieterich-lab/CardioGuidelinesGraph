# SNOMED Grounding Evaluation (Table 22)

This module evaluates concept-to-SNOMED grounding quality against:

- `/prj/doctoral_letters/guide/data/evaluation/table_22_manual_snomed.json`

Evaluator entrypoint:

- `cardio_graph_core.evaluation.table22_snomed_grounding_only_eval`

## What it does

For each gold concept item (condition/action), it runs grounding via `GuidelineGraphBuilder._search_best_concept`, then reports:

- total hits / total items / accuracy
- per-role accuracy (`ClinicalCondition`, `ClinicalParameter`, `Procedure`, ...)
- full per-item predictions
- optional comparison against a baseline JSON (`--compare-with`)

## Run directly (CLI)

From repo root:

```bash
cd /home/pwiesenbach/CardioGuidelinesGraph
```

### 1) Non-vector baseline

```bash
poetry run python -m cardio_graph_core.evaluation.table22_snomed_grounding_only_eval \
  --mode non-vector \
  --gold-path /prj/doctoral_letters/guide/data/evaluation/table_22_manual_snomed.json \
  --model Qwen3next \
  --node g3 \
  --port 11433 \
  --vector-uri bolt://neo4j-dev3.internal:7687 \
  --vector-user neo4j \
  --vector-index snomed_term_embeddings_4096 \
  --embedding-model Qwen3embed \
  --embedding-node g4 \
  --embedding-port 11434 \
  --output-json docs/table22_snomed_grounding_compare/grounding_only/nonvector_local/nonvector_eval.json
```

### 2) Vector run (compared to baseline)

```bash
poetry run python -m cardio_graph_core.evaluation.table22_snomed_grounding_only_eval \
  --mode vector \
  --gold-path /prj/doctoral_letters/guide/data/evaluation/table_22_manual_snomed.json \
  --model Qwen3next \
  --node g3 \
  --port 11433 \
  --vector-uri bolt://neo4j-dev3.internal:7687 \
  --vector-user neo4j \
  --vector-index snomed_term_embeddings_4096 \
  --embedding-model Qwen3embed \
  --embedding-node g4 \
  --embedding-port 11434 \
  --output-json docs/table22_snomed_grounding_compare/grounding_only/vector_local/vector_eval.json \
  --compare-with docs/table22_snomed_grounding_compare/grounding_only/nonvector_local/nonvector_eval.json
```

## SLURM launcher (vector)

Current launcher script:

- `slurm/run_table22_snomed_grounding_only_vector.sh`

Submit:

```bash
sbatch slurm/run_table22_snomed_grounding_only_vector.sh
```

Monitor:

```bash
squeue -j <JOB_ID>
tail -f slurm/run_table22_snomed_grounding_only_vector.log
```

Output artifact:

- `docs/table22_snomed_grounding_compare/grounding_only/vector_job_<JOB_ID>/vector_eval.json`

The script auto-detects the latest `nonvector_eval.json` in `docs/table22_snomed_grounding_compare/grounding_only/` and passes it to `--compare-with` when found.

## Important grounding env knobs

These are read by `GuidelineGraphBuilder` and can be set before running:

- `CARDIO_GRAPH_GROUNDING_ENABLE_VECTOR` (`true|false`)
- `CARDIO_GRAPH_GROUNDING_VECTOR_TOP_K` (default `40`)
- `CARDIO_GRAPH_GROUNDING_VECTOR_RERANK_WEIGHT` (default `0.10`)
- `CARDIO_GRAPH_GROUNDING_VECTOR_BONUS_CAP` (default `0.12`)
- `CARDIO_GRAPH_GROUNDING_VECTOR_MIN_LEXICAL_FOR_BONUS` (default `0.70`)
- `CARDIO_GRAPH_GROUNDING_VECTOR_TIE_EPSILON` (default `0.002`)

New ranking controls:

- `CARDIO_GRAPH_GROUNDING_MIN_WEIGHTED_QUERY_COVERAGE` (default `0.45`)
- `CARDIO_GRAPH_GROUNDING_LOW_COVERAGE_PENALTY` (default `0.12`)
- `CARDIO_GRAPH_GROUNDING_MISSING_DISCRIMINATIVE_PENALTY` (default `0.10`)
- `CARDIO_GRAPH_GROUNDING_DEBUG_TOP_CANDIDATES` (`true|false`, default `false`)

When `CARDIO_GRAPH_GROUNDING_DEBUG_TOP_CANDIDATES=true`, logs include top candidate breakdowns (lexical/vector/coverage/penalty/final score).

## Notes

- `--mode non-vector` still sets vector connection settings in output metadata; vector retrieval is disabled by mode.
- There is no dedicated non-vector SLURM launcher script currently; use the direct CLI command above (or clone the vector script and switch `--mode`).
