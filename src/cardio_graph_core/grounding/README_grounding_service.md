# Table22 Grounding Service (Current Runtime)

This document describes how the grounding pipeline runs now, including the
runtime defaults and the simplification policy for upcoming runs.

## Entry Scripts

- Canonical ground-truth vector run: `slurm/gt-eval-vector.sbatch`
- Ground-truth 3-table ablation alias: `slurm/gt3-eval-vector-ablation.sbatch`
- Ground-truth 3-table compatibility alias: `slurm/gt3-eval-vector-ablation-compat.sbatch`

Current behavior:
- Canonical runs use `gt-eval-vector.sbatch`.
- Ablation wrappers are explicitly separated under `ablation-*.sbatch`.
- All vector grounding runs use a local Ollama server on the allocated GPU node.

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
3. Start local Ollama on the compute node:
   - `OLLAMA_HOST=127.0.0.1:<dynamic-port>`
   - Port default: `11434 + (SLURM_JOB_ID % 1000)`
4. Wait for Ollama readiness (`/api/tags`).
5. Run grounding eval:
   - Module: `cardio_graph_core.evaluation.ground_truth_snomed_grounding_eval`
   - Mode: `vector`
   - Gold:
     `/prj/doctoral_letters/guide/data/evaluation/table_22_manual_snomed.json`
   - Vector DB: `bolt://neo4j-dev3.internal:7687`
   - Embedding endpoint: local Ollama (`--embedding-node local`)
6. Write run output:
   - `/prj/doctoral_letters/guide/data/cardio_guidelines_graph/artifacts/grounding/table_22/vector/runs/job_<job_id>/eval.json`
7. Regenerate persistent error artifacts:
   - `/prj/doctoral_letters/guide/data/cardio_guidelines_graph/artifacts/grounding/table_22/vector/persistent_error_manifest.json`
   - `docs/trackers/grounding/snomed_mapping_eval.md`

## Runtime Knobs (Default Behavior)

The local-Ollama runner exports the defaults below. They are grouped by intent
so it is clear which knobs are core logic and which are high overfit risk.

### Core Controls (Keep On)

| Knob | Default | Why it exists | If you increase it | If you decrease it |
|---|---:|---|---|---|
| `CARDIO_GRAPH_GROUNDING_VECTOR_RERANK_WEIGHT` | `0.03` | Adds vector evidence to lexical ranking. | More vector influence. | More lexical dominance. |
| `CARDIO_GRAPH_GROUNDING_VECTOR_BONUS_CAP` | `0.05` | Prevents vector score from overpowering lexical score. | Vector can move rank more. | Vector impact is tightly bounded. |
| `CARDIO_GRAPH_GROUNDING_VECTOR_MIN_LEXICAL_FOR_BONUS` | `0.90` | Requires strong lexical match before vector bonus. | Stricter lexical gate. | Vector helps earlier. |
| `CARDIO_GRAPH_GROUNDING_MIN_WEIGHTED_QUERY_COVERAGE` | `0.45` | Coverage floor before low-coverage penalty. | Harder for partial matches. | More permissive to partial matches. |
| `CARDIO_GRAPH_GROUNDING_LOW_COVERAGE_PENALTY` | `0.12` | Penalizes generic/under-covered candidates. | Stronger punishment. | Weaker punishment. |
| `CARDIO_GRAPH_GROUNDING_MISSING_DISCRIMINATIVE_PENALTY` | `0.10` | Penalizes missing key discriminative tokens. | More anti-generic pressure. | Allows broader substitutions. |
| `CARDIO_GRAPH_GROUNDING_EXTRA_QUALIFIER_PENALTY` | `0.10` | Penalizes over-qualified labels not in query. | Fewer over-specific picks. | More over-specific picks. |
| `CARDIO_GRAPH_GROUNDING_ROLE_SOFT_CONSTRAINTS` | `true` | Role mismatch is penalized, not hard rejected. | n/a | n/a |
| `CARDIO_GRAPH_GROUNDING_ROLE_MISMATCH_PENALTY` | `0.05` | Penalizes role-incompatible concepts. | Stricter role fit. | Looser role fit. |
| `CARDIO_GRAPH_GROUNDING_ROLE_SEMANTIC_MISMATCH_PENALTY` | `0.06` | Penalizes semantic class mismatch. | Stricter semantic role match. | Looser semantic role match. |
| `CARDIO_GRAPH_GROUNDING_ROLE_SEMANTIC_CROSSCLASS_PENALTY` | `0.02` | Softer penalty for allowed cross-class cases. | Less tolerance for cross-class. | More tolerance for cross-class. |
| `CARDIO_GRAPH_GROUNDING_VECTOR_CONTEXT_ENABLED` | `false` | A/B switch for context-expanded vector queries. | n/a | n/a |
| `CARDIO_GRAPH_GROUNDING_VECTOR_CONTEXT_ALLOWED_ROLES` | `Procedure` | Restricts context-expanded queries to selected roles. | Broader role coverage (higher drift risk). | Narrower, safer scope. |
| `CARDIO_GRAPH_GROUNDING_VECTOR_CONTEXT_APPEND_TERM` | `false` | If true, also queries `term + context` strings. | More aggressive retrieval expansion. | More conservative retrieval expansion. |
| `CARDIO_GRAPH_GROUNDING_VECTOR_CONTEXT_MAX_TOKENS` | `8` | Limits query-context length. | Longer context variants. | Shorter context variants. |

### High-Risk Controls (Overfit-Prone)

These can improve one benchmark split, but they are the first candidates to
disable when seeking a cleaner generalizable policy.

| Knob | Current default | Risk | Next-runs policy |
|---|---:|---|---|
| `CARDIO_GRAPH_GROUNDING_HARD_NEGATIVE_PENALTY` | `0.0` | Can memorize persistent benchmark mistakes. | Keep off unless ablation proves robust gain. |
| `CARDIO_GRAPH_GROUNDING_HARD_NEGATIVE_MANIFEST` | `""` | Dataset-specific negative list can hard-code behavior. | Keep empty by default. |
| `CARDIO_GRAPH_GROUNDING_ROLE_TENSION_PENALTY` | `0.02` | Manual high-risk term lists can overfit. | Candidate for ablation after context test. |
| `CARDIO_GRAPH_GROUNDING_GUARDED_FALLBACK_MARGIN` | `0.015` | Tie-break heuristics may over-tune to current set. | Candidate for ablation after context test. |
| `CARDIO_GRAPH_GROUNDING_MIN_DISCRIMINATIVE_COVERAGE_FOR_TOP` | `0.60` | Coupled with guarded fallback behavior. | Candidate for ablation after context test. |
| `CARDIO_GRAPH_GROUNDING_AMBIGUITY_*` backoff tuple | mixed | Many interacting thresholds raise tuning complexity. | Candidate for grouped ablation. |

## Simplification Direction (Explicit)

Immediate policy for upcoming runs:

1. Keep hard-negative controls disabled by default.
2. Run baseline/context A/B with only core controls active.
3. Treat role-tension, guarded-fallback, and ambiguity-backoff as optional
   add-ons that must re-earn inclusion via repeated gains.

Reduction protocol after context A/B:

1. Freeze best context setting (`CARDIO_GRAPH_GROUNDING_VECTOR_CONTEXT_ENABLED`
   and `CARDIO_GRAPH_GROUNDING_VECTOR_CONTEXT_MAX_TOKENS`).
2. Run one clean ablation with all high-risk groups disabled.
3. Compare overall and per-role deltas (especially Procedure and
   ClinicalCondition).
4. Re-introduce at most one high-risk group at a time, and keep it only if the
   gain repeats across at least two independent runs.

## Context-Aware Retrieval (Current Implementation)

Implemented in:
- `src/cardio_graph_core/grounding/entity_grounding_service.py`
- `src/cardio_graph_core/extraction/guideline_graph_builder.py`
- `src/cardio_graph_core/evaluation/ground_truth_snomed_grounding_eval.py`

Behavior:
- Eval composes context from concept `context`, `logic_structured`, and row
  `recommendation`.
- Builder receives `query_context` for each term.
- If `CARDIO_GRAPH_GROUNDING_VECTOR_CONTEXT_ENABLED=true`, additional
  context-derived vector queries are generated and merged into vector
  candidates.
- Lexical scoring and penalties remain unchanged; only retrieval queries are
  expanded.

## How To Run

Baseline (A):

```bash
sbatch slurm/gt-eval-vector.sbatch
```

Context arm (B):

```bash
sbatch --export=ALL,CARDIO_GRAPH_GROUNDING_VECTOR_CONTEXT_ENABLED=true \
   slurm/gt-eval-vector.sbatch
```

Table22 ablation entry:

```bash
sbatch slurm/gt3-eval-vector-ablation.sbatch
```