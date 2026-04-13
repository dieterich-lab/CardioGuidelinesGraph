# Multi-Table Autotuning Patch Adoptions

This tracker records prompt patch candidates produced by autotuning runs and which candidates were promoted to champion baseline.

## Scope

- Active scope is multi-table extraction tuning (tables 22, 17, 8).
- Main run script: `slurm/run-autotune-multitable-dev.sbatch`.
- Active manifests/splits live under `config/autotuning/`.

## Why "second candidate" matters

So far, only two candidates have ever been promoted to champion baseline in this tracker lineage:

1. `prompt_v2_candidate_01` from run `20260311_165230` (Table 22-era run with locked-test acceptance).
2. `prompt_v1_candidate_02` from run `20260410_132051` (first multi-table run).

This means the latest run did not just produce another trial patch. It produced only the second promotion event overall, which is a relatively rare outcome under the current gates.

## Promoted Candidate Ledger

| Date | Run Tag | Scope | Promoted Prompt | Promotion Basis |
|---|---|---|---|---|
| 2026-03-11 | `20260311_165230` | Table 22-focused | `prompt_v2_candidate_01` | accepted with locked-test checks |
| 2026-04-10 | `20260410_132051` | Multi-table (22/17/8) | `prompt_v1_candidate_02` | accepted on dev gate, then remained champion |

## Latest Run Summary (2026-04-10 / run_tag=20260410_132051)

Artifact root:
- `/prj/doctoral_letters/guide/data/cardio_guidelines_graph/artifacts/autotuning/multi_table/dev/`

Execution summary:
- Job: `630004` (completed).
- Iterations configured/executed: `5/3`.
- Candidates evaluated: `9` (`3` per executed iteration).
- Accepted promotions: `1`.
- Early stop reason: no promotion for `2` consecutive iterations.
- Final champion: `prompt_v1_candidate_02`.

Final dev metrics:
- `schema_valid_rate`: `1.0000`
- `rule_exact_match`: `0.1712`
- `operator_accuracy`: `0.7879`
- `logic_group_accuracy`: `0.6304`
- `concept_f1`: `0.7299`
- `grounding_hit_rate`: `0.0000`

Final locked test metrics:
- `rule_exact_match`: `0.4000`
- `concept_f1`: `0.6900`
- `grounding_hit_rate`: `0.7800`

## Operational Run Log (multi-table launcher)

| Date | Job ID | Script | Manifest | Split | Status | Notes |
|---|---|---|---|---|---|---|
| 2026-04-10 | `629998` | `slurm/run-autotune-multitable-dev.sbatch` | `benchmark_manifest_v3.jsonc` | `split_v3_all_tables.json` | superseded | variant before in-job local Ollama startup |
| 2026-04-10 | `630001` | `slurm/run-autotune-multitable-dev.sbatch` | `benchmark_manifest_v3.jsonc` | `split_v3_all_tables.json` | cancelled | aborted on undersized node |
| 2026-04-10 | `630004` | `slurm/run-autotune-multitable-dev.sbatch` | `benchmark_manifest_v3.jsonc` | `split_v3_all_tables.json` | completed | final successful multi-table run (`run_tag=20260410_132051`) |

## Candidate 2 details (the newly promoted one)

Source:
- `iter_01/candidate_ranking.json`

Selected candidate:
- `candidate_index=2`
- `prompt_name=prompt_v1_candidate_02`
- Zones touched: `action_extraction`, `condition_extraction`, `operator_logic`

Measured deltas vs prior champion in iter_01:
- `rule_exact_match`: `+0.1081`
- `logic_group_accuracy`: `+0.2554`
- `concept_f1`: `+0.0303`
- `operator_accuracy`: `-0.0024` (small regression, still within acceptance gates)

Interpretation:
- Promotion was driven primarily by large gains in rule and logic-group correctness, with a minor operator tradeoff.

## Leakage control policy

- For runs with `CARDIO_GRAPH_ENABLE_FEWSHOT_EXAMPLES=true`, exemplar rows are excluded from both dev and locked test.
- Current leakage-safe manifest: `config/autotuning/benchmark_manifest_v3.jsonc`.
- Excluded exemplar rows:
  - `table17`: `t0_row_01`
  - `table8`: `row_01`

## Historical run notes (Table 22 era)

Legacy run:
- `cascade_16h / 20260311_165230` (external artifact store root `autotuning/table_22/cascade_16h/20260311_165230`).

Historical details kept here for continuity only; active tuning decisions now use the multi-table artifacts listed above.

## Reporting checklist

When summarizing externally, include:

1. Run tag and artifact root.
2. Candidate patch/ranking artifact path.
3. Gate decisions across iterations.
4. Final promoted prompt and whether promotion count changed.
5. Before/after key metrics (`rule_exact_match`, `operator_accuracy`, `concept_f1`).
