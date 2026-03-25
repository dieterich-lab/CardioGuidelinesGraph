# Table22 Grounding Service (Current Runtime)

This document describes how the grounding pipeline runs now, including the exact knobs currently used in production runs.

## Entry Scripts

- General vector entry: `slurm/run_table22_snomed_grounding_only_vector.sh`
- Local-Ollama runner: `slurm/run_table22_snomed_grounding_only_vector_with_local_ollama.sh`

Current behavior:
- The general vector entry is now an alias that executes the local-Ollama runner.
- All vector grounding runs therefore use a local Ollama server on the allocated GPU node.

## SLURM Runtime Configuration

Current job configuration (local runner):
- Partition: `gpu`
- Node constraint: `gpu-g2-1,gpu-g3-1`
- GPU type/count: `gpu:turing:1`
- CPU: `2`
- Memory: `50G`

## End-to-End Pipeline

1. Load secrets (if present) from `~/.config/cardio_graph/secrets.env`.
2. Resolve Neo4j vector password from one of:
   - `CARDIO_GRAPH_GROUNDING_VECTOR_PASSWORD`
   - `CARDIO_GRAPH_GROUNDING_PASSWORD`
   - `CARDIO_GRAPH_NEO4J_PASSWORD`
   - `NEO4J_PASSWORD`
3. Start a local Ollama server on the compute node:
   - `OLLAMA_HOST=127.0.0.1:<dynamic-port>`
   - Port default: `11434 + (SLURM_JOB_ID % 1000)`
4. Wait for Ollama readiness (`/api/tags`).
5. Run grounding eval:
   - Module: `cardio_graph_core.evaluation.table22_snomed_grounding_only_eval`
   - Mode: `vector`
   - Gold: `/prj/doctoral_letters/guide/data/evaluation/table_22_manual_snomed.json`
   - Vector DB: `bolt://neo4j-dev3.internal:7687`
   - Embedding endpoint: local Ollama (`--embedding-node local`, configured port)
6. Write run output:
   - `docs/table22_snomed_grounding_compare/grounding_only/vector_job_<job_id>/vector_eval.json`
7. Regenerate persistent error artifacts:
   - `docs/table22_snomed_grounding_compare/grounding_only/persistent_error_manifest.json`
   - `docs/table22_snomed_grounding_compare/grounding_only/persistent_error_milestone.md`

## Current Tuned Knobs (Script Defaults)

These defaults are exported by the local runner and represent the current frozen baseline:

### Vector + Lexical Fusion
- `CARDIO_GRAPH_GROUNDING_VECTOR_RERANK_WEIGHT=0.03`
- `CARDIO_GRAPH_GROUNDING_VECTOR_BONUS_CAP=0.05`
- `CARDIO_GRAPH_GROUNDING_VECTOR_MIN_LEXICAL_FOR_BONUS=0.90`

### Coverage and Discriminative Penalties
- `CARDIO_GRAPH_GROUNDING_MIN_WEIGHTED_QUERY_COVERAGE=0.45`
- `CARDIO_GRAPH_GROUNDING_LOW_COVERAGE_PENALTY=0.12`
- `CARDIO_GRAPH_GROUNDING_MISSING_DISCRIMINATIVE_PENALTY=0.10`
- `CARDIO_GRAPH_GROUNDING_EXTRA_QUALIFIER_PENALTY=0.10`
- `CARDIO_GRAPH_GROUNDING_GUARDED_FALLBACK_MARGIN=0.015`
- `CARDIO_GRAPH_GROUNDING_MIN_DISCRIMINATIVE_COVERAGE_FOR_TOP=0.60`

### Hard-Negative Control
- `CARDIO_GRAPH_GROUNDING_HARD_NEGATIVE_PENALTY=0.05`
- `CARDIO_GRAPH_GROUNDING_HARD_NEGATIVE_MANIFEST=docs/table22_snomed_grounding_compare/grounding_only/persistent_error_manifest.json`

### Ambiguity Handling
- `CARDIO_GRAPH_GROUNDING_AMBIGUITY_ABSTAIN_MARGIN=0.012`
- `CARDIO_GRAPH_GROUNDING_AMBIGUITY_MIN_COVERAGE=0.55`
- `CARDIO_GRAPH_GROUNDING_AMBIGUITY_CONFIDENCE_BACKOFF_ENABLED=true`
- `CARDIO_GRAPH_GROUNDING_AMBIGUITY_BACKOFF_MAX_DROP=0.05`
- `CARDIO_GRAPH_GROUNDING_AMBIGUITY_BACKOFF_MIN_SCORE=0.35`
- `CARDIO_GRAPH_GROUNDING_AMBIGUITY_LEXICAL_FORCE_PICK=0.90`

### Role Constraints
- `CARDIO_GRAPH_GROUNDING_ROLE_SOFT_CONSTRAINTS=true`
- `CARDIO_GRAPH_GROUNDING_ROLE_MISMATCH_PENALTY=0.05`
- `CARDIO_GRAPH_GROUNDING_ROLE_TENSION_PENALTY=0.02`
- `CARDIO_GRAPH_GROUNDING_ROLE_SEMANTIC_MISMATCH_PENALTY=0.06`
- `CARDIO_GRAPH_GROUNDING_ROLE_SEMANTIC_CROSSCLASS_PENALTY=0.02`

### Context-Aware Vector Query (A/B Switch)
- `CARDIO_GRAPH_GROUNDING_VECTOR_CONTEXT_ENABLED=false` (baseline arm)
- `CARDIO_GRAPH_GROUNDING_VECTOR_CONTEXT_MAX_TOKENS=8`

## Context-Aware Retrieval (Current Implementation)

Implemented in:
- `src/cardio_graph_core/extraction/guideline_graph_builder.py`
- `src/cardio_graph_core/evaluation/table22_snomed_grounding_only_eval.py`

Behavior:
- Eval composes context from concept `context`, `logic_structured`, and row `recommendation`.
- Builder receives `query_context` for each term.
- If `CARDIO_GRAPH_GROUNDING_VECTOR_CONTEXT_ENABLED=true`, additional context-derived vector queries are generated and merged into vector candidates.
- Lexical scoring and all penalties remain unchanged; only candidate retrieval queries are expanded.

## How To Run

Baseline (A):
```bash
sbatch slurm/run_table22_snomed_grounding_only_vector_with_local_ollama.sh
```

Context arm (B):
```bash
sbatch --export=ALL,CARDIO_GRAPH_GROUNDING_VECTOR_CONTEXT_ENABLED=true \
  slurm/run_table22_snomed_grounding_only_vector_with_local_ollama.sh
```

General entry (also local Ollama):
```bash
sbatch slurm/run_table22_snomed_grounding_only_vector.sh
```
