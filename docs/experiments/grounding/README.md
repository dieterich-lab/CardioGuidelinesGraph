# Automated Vector Grounding Pipeline

This document describes the automated SNOMED CT vector grounding pipeline used in this repository:

- end-to-end flow
- leakage-safe split handling
- Slurm orchestration
- outputs and diagnostics
- all major runtime knobs

## Scope and entry points

Primary evaluator module:

- `cardio_graph_core.evaluation.ground_truth_snomed_grounding_eval`

Primary automation scripts:

- `slurm/gt-eval-vector-dev-norescue.sbatch`
- `slurm/derive-train-rescue-from-dev.sbatch`
- `slurm/gt-eval-vector-locked-norescue.sbatch`
- `slurm/gt-eval-vector-heldout-trainrescue.sbatch`
- `slurm/submit-grounding-probing-matrix.sh`

Core grounding logic and knob defaults:

- `src/cardio_graph_core/extraction/guideline_graph_builder.py`
- `src/cardio_graph_core/grounding/entity_grounding_service.py`

## Pipeline flow

## 1. Build split-filtered ground truth payloads

Each Slurm wrapper:

- loads `config/autotuning/split_v3_all_tables.json`
- resolves split aliases:
  - `dev` or `dev_rows`
  - `locked_test` or `locked_test_rows`
- filters source gold files into per-job artifacts:
  - `docs/generated/ground_truth/splits/vector_job_<jobid>/table_22_<split>.json`
  - `docs/generated/ground_truth/splits/vector_job_<jobid>/table_8_<split>.json`
  - `docs/generated/ground_truth/splits/vector_job_<jobid>/table_17_<split>.json`

This is the first leakage guardrail: evaluation always runs on explicit split-filtered snapshots.

## 2. Start per-job local embedding server

Wrappers start `ollama serve` on a job-specific local port:

- `OLLAMA_PORT=11434 + (SLURM_JOB_ID % 1000)` unless overridden
- `OLLAMA_HOST=127.0.0.1:<port>`
- `CARDIO_GRAPH_GROUNDING_EMBEDDING_URL=http://127.0.0.1:<port>`

This isolates embedding serving per Slurm job and avoids shared-process coupling.

## 3. Run evaluator in vector mode

Each wrapper calls:

```bash
poetry run python -m cardio_graph_core.evaluation.ground_truth_snomed_grounding_eval \
  --mode vector \
  --gold-path <split-filtered table_22> \
  --gold-path <split-filtered table_8> \
  --gold-path <split-filtered table_17> \
  --model Qwen3next \
  --node g3 \
  --port 11433 \
  --vector-uri bolt://neo4j-dev3.internal:7687 \
  --vector-user neo4j \
  --vector-index snomed_term_embeddings_4096 \
  --embedding-model Qwen3embed \
  --embedding-node local \
  --embedding-port <OLLAMA_PORT> \
  --run-manifest-jsonl docs/generated/grounding/ground_truth_vector_runs_manifest.jsonl \
  --run-manifest-csv docs/generated/grounding/ground_truth_vector_runs_manifest.csv \
  --output-json docs/generated/ground_truth/grounding_only/vector_job_<jobid>/ground_truth_vector_eval.json
```

The evaluator writes:

- per-item predictions with ranked candidates
- rank metrics (MRR, hit@k, precision@k, GT-rank stats)
- `config_env` snapshot (grounding, Ollama, Slurm vars, with secret redaction)
- optional debug probe CSV/JSON artifacts

## 4. Derive train-only rescue map (optional, leakage-safe production track)

`slurm/derive-train-rescue-from-dev.sbatch` uses a dev-only eval output and creates:

- `config/cardio_graph_core/grounding_rescue_map_train_only.yaml`
- `docs/generated/grounding/train_rescue_derivation_report_from_dev_<jobid>.json`

Derivation script:

- reads misses only
- keeps only rows that belong to selected split (`--split-name dev`)
- emits deterministic `term+role -> concept_id` overrides
- defaults to unambiguous mappings only

This is the second leakage guardrail: rescue map derivation can be constrained to train/dev rows.

## 5. Run probing matrix (scientific vs production)

`slurm/submit-grounding-probing-matrix.sh` submits a dependency chain:

- `S1`: no-rescue scientific baseline
- `S2`: semantic-tight scientific
- `S3`: semantic-tight + vector-reduced + ambiguity-tight scientific
- `P1`: train-only rescue production replay
- `P2`: full-map rescue production replay
- `P3`: full-map rescue + hard-negatives production

Matrix metadata is carried in `CARDIO_GRAPH_GROUNDING_ABLATION_LABEL`.

## 6. Export stage-trace diagnostics (optional)

If stage trace is enabled, each prediction includes `gt_presence_trace` and ranking chains.
`scripts/export_grounding_stage_trace_report.py` converts these to tabular diagnostics:

- stage where GT was lost (`gold_absence_stage`)
- whether GT survived domain filter/truncation/final ranking
- chain to GT rank and top-10 chain

## Knob precedence and effective defaults

Knob resolution order:

1. Explicit env var provided at submission/runtime.
2. Wrapper default (`${VAR:-default}`) if present.
3. Engine default in `GuidelineGraphBuilder` / evaluator.

Important consequence:

- documented defaults in code are global engine defaults
- the Slurm wrappers intentionally override many of them for the current validated H/H2 profile

## Full knob reference

The table below lists the key runtime knobs used by automated vector grounding.

### A) Core vector backend

| Env var | Meaning | Typical/Default |
|---|---|---|
| `CARDIO_GRAPH_GROUNDING_ENABLE_VECTOR` | Enable vector retrieval+rereanking. | Evaluator sets `true` in vector mode; engine default `false`. |
| `CARDIO_GRAPH_GROUNDING_VECTOR_URI` | Neo4j Bolt URI for vector index. | `bolt://neo4j-dev3.internal:7687` |
| `CARDIO_GRAPH_GROUNDING_VECTOR_USER` | Neo4j user. | `neo4j` |
| `CARDIO_GRAPH_GROUNDING_VECTOR_PASSWORD` | Neo4j password. | Required; wrappers fail fast if missing. |
| `CARDIO_GRAPH_GROUNDING_VECTOR_INDEX` | Vector index name. | Engine default `snomed_term_embeddings`; wrappers pass `snomed_term_embeddings_4096`. |
| `CARDIO_GRAPH_GROUNDING_VECTOR_TOP_K` | Vector retrieval depth. | Engine default `40`. |
| `CARDIO_GRAPH_GROUNDING_EMBEDDING_MODEL` | Embedding model name. | `Qwen3embed` |
| `CARDIO_GRAPH_GROUNDING_EMBEDDING_URL` | Embedding server URL. | Built from local Ollama host/port in wrappers. |
| `CARDIO_GRAPH_GROUNDING_EMBEDDING_PORT` | Embedding port. | Resolved from CLI/env; wrapper usually equals `OLLAMA_PORT`. |
| `CARDIO_GRAPH_GROUNDING_EMBEDDING_NODE` | Embedding host node key. | Usually `local` in wrapper runs. |
| `CARDIO_GRAPH_GROUNDING_EMBEDDING_TIMEOUT` | Embedding request timeout (seconds). | Engine default `20`. |

### B) Vector contribution and rank priors

| Env var | Meaning | Engine default | Wrapper baseline |
|---|---|---:|---:|
| `CARDIO_GRAPH_GROUNDING_VECTOR_RERANK_WEIGHT` | Multiplier for vector score bonus. | 0.10 | 0.03 |
| `CARDIO_GRAPH_GROUNDING_VECTOR_BONUS_CAP` | Max vector bonus. | 0.12 | 0.05 |
| `CARDIO_GRAPH_GROUNDING_VECTOR_MIN_LEXICAL_FOR_BONUS` | Lexical floor before vector bonus applies. | 0.70 | 0.90 |
| `CARDIO_GRAPH_GROUNDING_VECTOR_TIE_EPSILON` | Tie epsilon helper. | 0.002 | (engine default) |
| `CARDIO_GRAPH_GROUNDING_VECTOR_RANK_PRIOR_ENABLED` | Enable rank-prior boost. | false | usually false |
| `CARDIO_GRAPH_GROUNDING_VECTOR_RANK_PRIOR_TOP_K` | Rank-prior scope. | 3 | 3 |
| `CARDIO_GRAPH_GROUNDING_VECTOR_RANK_PRIOR_BONUS` | Max rank-prior bonus. | 0.03 | 0.03 |
| `CARDIO_GRAPH_GROUNDING_VECTOR_RANK_PRIOR_LEXICAL_FLOOR` | Lexical floor for rank-prior. | 0.55 | 0.55 |
| `CARDIO_GRAPH_GROUNDING_VECTOR_RANK_RESCUE_ENABLED` | Enable near-tie vector-rank promotion. | false | usually false |
| `CARDIO_GRAPH_GROUNDING_VECTOR_RANK_RESCUE_MARGIN` | Max final-score gap for promotion. | 0.015 | 0.015 |
| `CARDIO_GRAPH_GROUNDING_VECTOR_RANK_RESCUE_MAX_RANK` | Runner rank threshold. | 3 | 3 |
| `CARDIO_GRAPH_GROUNDING_VECTOR_RANK_RESCUE_MIN_COVERAGE` | Coverage floor for promotion. | 0.70 | 0.70 |

### C) Context-aware vector query expansion

| Env var | Meaning | Engine default | Wrapper baseline |
|---|---|---:|---:|
| `CARDIO_GRAPH_GROUNDING_VECTOR_CONTEXT_ENABLED` | Include structured/text context variants in vector search terms. | false | true |
| `CARDIO_GRAPH_GROUNDING_VECTOR_CONTEXT_ALLOWED_ROLES` | Roles eligible for context expansion. | `Procedure` | `Procedure,Medication` |
| `CARDIO_GRAPH_GROUNDING_VECTOR_CONTEXT_APPEND_TERM` | Also submit `<term> + <context fragment>` variants. | false | true |
| `CARDIO_GRAPH_GROUNDING_VECTOR_CONTEXT_MAX_TOKENS` | Per-context variant token budget. | 8 | 8 |

### D) Coverage and specificity penalties

| Env var | Meaning | Engine default | Wrapper baseline |
|---|---|---:|---:|
| `CARDIO_GRAPH_GROUNDING_MIN_WEIGHTED_QUERY_COVERAGE` | Minimum weighted token coverage before penalty. | 0.45 | 0.45 |
| `CARDIO_GRAPH_GROUNDING_LOW_COVERAGE_PENALTY` | Penalty for low weighted coverage. | 0.12 | 0.12 |
| `CARDIO_GRAPH_GROUNDING_MISSING_DISCRIMINATIVE_PENALTY` | Penalty if discriminative tokens are absent. | 0.10 | 0.10 |
| `CARDIO_GRAPH_GROUNDING_EXTRA_QUALIFIER_PENALTY` | Weight penalizing extra qualifiers in candidate terms. | 0.10 | 0.10 |
| `CARDIO_GRAPH_GROUNDING_GUARDED_FALLBACK_MARGIN` | Margin for guarded fallback to more discriminative runner. | 0.015 | 0.015 |
| `CARDIO_GRAPH_GROUNDING_MIN_DISCRIMINATIVE_COVERAGE_FOR_TOP` | Discriminative-coverage floor for top candidate. | 0.60 | 0.60 |

### E) Ambiguity handling

| Env var | Meaning | Engine default | Wrapper baseline |
|---|---|---:|---:|
| `CARDIO_GRAPH_GROUNDING_AMBIGUITY_ABSTAIN_MARGIN` | Near-tie margin where abstain/backoff logic can trigger. | 0.0 | 0.012 |
| `CARDIO_GRAPH_GROUNDING_AMBIGUITY_MIN_COVERAGE` | Coverage threshold used in ambiguity checks. | 0.55 | 0.55 |
| `CARDIO_GRAPH_GROUNDING_AMBIGUITY_LEXICAL_FORCE_PICK` | Lexical threshold above which forced pick still occurs. | 0.90 | 0.90 |
| `CARDIO_GRAPH_GROUNDING_AMBIGUITY_CONFIDENCE_BACKOFF_ENABLED` | Enables confidence-based backoff candidate search. | true | true |
| `CARDIO_GRAPH_GROUNDING_AMBIGUITY_BACKOFF_MAX_DROP` | Max score drop from top allowed during backoff. | 0.05 | 0.30 |
| `CARDIO_GRAPH_GROUNDING_AMBIGUITY_BACKOFF_MIN_SCORE` | Absolute minimum score eligible for backoff candidate. | 0.35 | 0.45 |

### F) Role and semantic penalties

| Env var | Meaning | Engine default | Wrapper baseline |
|---|---|---:|---:|
| `CARDIO_GRAPH_GROUNDING_ROLE_SOFT_CONSTRAINTS` | Soft-penalize role mismatch instead of hard-filtering mismatches. | false | true |
| `CARDIO_GRAPH_GROUNDING_ROLE_MISMATCH_PENALTY` | Penalty when candidate role does not align. | 0.08 | 0.05 |
| `CARDIO_GRAPH_GROUNDING_ROLE_TENSION_PENALTY` | Extra mismatch penalty for configured tension terms. | 0.03 | 0.02 |
| `CARDIO_GRAPH_GROUNDING_ROLE_TENSION_TERMS` | CSV list of high-risk terms for extra role tension penalty. | Engine default list | wrapper leaves default |
| `CARDIO_GRAPH_GROUNDING_ROLE_SEMANTIC_MISMATCH_PENALTY` | Penalty for semantic-tag mismatch. | 0.06 | 0.06 |
| `CARDIO_GRAPH_GROUNDING_ROLE_SEMANTIC_CROSSCLASS_PENALTY` | Penalty for stronger cross-class semantic mismatch. | 0.02 | 0.02 |
| `CARDIO_GRAPH_GROUNDING_SEMANTIC_PENALTY_EVIDENCE_RELIEF_ENABLED` | Reduce semantic penalty when lexical/coverage/vector evidence is strong. | false | usually false |
| `CARDIO_GRAPH_GROUNDING_SEMANTIC_PENALTY_EVIDENCE_MIN_COVERAGE` | Coverage floor for evidence relief. | 0.75 | 0.75 |
| `CARDIO_GRAPH_GROUNDING_SEMANTIC_PENALTY_EVIDENCE_MAX_VECTOR_RANK` | Max vector rank for evidence relief. | 3 | 3 |
| `CARDIO_GRAPH_GROUNDING_SEMANTIC_PENALTY_EVIDENCE_SCALE` | Multiplicative scale when relief applies. | 0.5 | 0.5 |

### G) Hard negatives

| Env var | Meaning | Engine default | Wrapper baseline |
|---|---|---:|---:|
| `CARDIO_GRAPH_GROUNDING_HARD_NEGATIVE_PENALTY` | Penalty if candidate concept is blocked for term-role. | 0.05 | 0.0 (baseline), 0.10 in P3 |
| `CARDIO_GRAPH_GROUNDING_HARD_NEGATIVE_MANIFEST` | JSON manifest containing blocked concept IDs per term-role. | default manifest path | optional override in matrix |

### H) Rescue overrides

| Env var | Meaning | Typical value |
|---|---|---|
| `CARDIO_GRAPH_GROUNDING_RESCUE_ENABLED` | Enable deterministic rescue overrides. | `false` (scientific), `true` (production) |
| `CARDIO_GRAPH_GROUNDING_RESCUE_MAP_PATH` | YAML map path for term-role overrides. | `.../grounding_rescue_map_train_only.yaml` or full map |

### I) Run metadata and diagnostics

| Env var | Meaning |
|---|---|
| `CARDIO_GRAPH_GROUNDING_ABLATION_LABEL` | Label carried in run environment/logs for experiment traceability. |
| `CARDIO_GRAPH_GROUNDING_DEBUG_TOP_CANDIDATES` | Log top candidate decomposition rows during grounding. |
| `CARDIO_GRAPH_GROUNDING_STAGE_TRACE_ENABLED` | Enable stage-level GT presence diagnostics in evaluator outputs. |

### J) Split and infrastructure knobs used by wrappers

| Env var | Meaning |
|---|---|
| `CARDIO_GRAPH_GROUNDING_SPLIT_FILE` | Split definition JSON path (default `config/autotuning/split_v3_all_tables.json`). |
| `CARDIO_GRAPH_GROUNDING_SPLIT_NAME` | Selected split (used by heldout wrapper; default `locked_test`). |
| `CARDIO_GRAPH_SECRETS_ENV_PATH` | Optional env file for secrets. |
| `OLLAMA_PORT`, `OLLAMA_HOST`, `OLLAMA_KEEP_ALIVE`, `OLLAMA_TIMEOUT` | Per-job local embedding server controls. |

## Automation recipes

## A) Scientific baseline (locked_test, no rescue)

```bash
sbatch slurm/gt-eval-vector-locked-norescue.sbatch
```

## B) Dev baseline for deriving train-only rescue map

```bash
DEV_JOB_ID=$(sbatch --parsable slurm/gt-eval-vector-dev-norescue.sbatch)
sbatch --dependency=afterok:${DEV_JOB_ID} --export=ALL,DEV_JOB_ID=${DEV_JOB_ID} \
  slurm/derive-train-rescue-from-dev.sbatch
```

## C) Production validation with train-only rescue

```bash
sbatch slurm/gt-eval-vector-heldout-trainrescue.sbatch
```

## D) Full probing matrix

```bash
bash slurm/submit-grounding-probing-matrix.sh
```

## Outputs and where to look

Main outputs:

- `docs/generated/ground_truth/grounding_only/vector_job_<jobid>/ground_truth_vector_eval.json`
- `docs/generated/grounding/ground_truth_vector_runs_manifest.jsonl`
- `docs/generated/grounding/ground_truth_vector_runs_manifest.csv`

Support artifacts:

- split snapshots: `docs/generated/ground_truth/splits/vector_job_<jobid>/...`
- Ollama logs: `slurm/ollama-server_<jobname>_<jobid>.log`
- Slurm logs: `slurm/<jobname>_<jobid>.log`
- rescue derivation reports: `docs/generated/grounding/train_rescue_derivation_report_from_dev_<jobid>.json`

Optional diagnostics:

- debug probes: `<eval_json_stem>_debug_probe.csv` and `<eval_json_stem>_debug_probe.json`
- stage trace export via `scripts/export_grounding_stage_trace_report.py`

## Troubleshooting quick checks

- Missing Neo4j password:
  - set `CARDIO_GRAPH_GROUNDING_VECTOR_PASSWORD` (or one of accepted fallbacks in wrapper).
- Ollama not found on node:
  - wrapper exits early; verify `ollama` availability in job environment.
- Split not found:
  - confirm split keys in `config/autotuning/split_v3_all_tables.json`.
- Rescue map expected but missing:
  - heldout rescue wrapper checks `CARDIO_GRAPH_GROUNDING_RESCUE_MAP_PATH` exists.

## Recommended policy usage

- Scientific reporting:
  - run no-rescue (`CARDIO_GRAPH_GROUNDING_RESCUE_ENABLED=false`) on locked split.
- Production reporting:
  - validate with train-only rescue map first.
  - evaluate full map and hard-negative variants separately.
- Keep scientific and production tracks separate in conclusions.