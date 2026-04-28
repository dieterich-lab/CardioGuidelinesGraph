# SNOMED Vector Grounding Tracker (Scientific vs Production)

Last revised: 2026-04-28

## Purpose

This tracker is the canonical project history for automated SNOMED vector grounding.
It is intentionally ordered **newest first** and preserves the full sequence of:

- pipeline/infrastructure changes,
- scoring and filtering changes,
- evaluation outcomes,
- debugging findings,
- policy decisions.

## General Resources

- Run metrics manifests (authoritative for eval metrics/timestamps):
  - `docs/generated/grounding/ground_truth_vector_runs_manifest.csv`
  - `docs/generated/grounding/ground_truth_vector_runs_manifest.jsonl`
- Eval artifacts:
  - `docs/generated/ground_truth/grounding_only/vector_job_<run_id>/ground_truth_vector_eval.json`
- Slurm logs:
  - `slurm/gt-eval-vector-*.log`
  - `slurm/ollama-server_*.log`
  - `slurm/derive-train-rescue_*.log`
  - `slurm/vector-index-rebuild_*.log`
  - `slurm/cardio-subset-gen.log`
- Scientific mapping reference:
  - `docs/reports/grounding/current_snomed_mappings_scientific_track.md`

## Track Definitions

- Scientific track:
  - no rescue map at evaluation time (`locked-norescue` / `dev-norescue`).
- Production track:
  - rescue-enabled heldout evaluation (`heldout`).
- Notes:
  - `timestamp_utc` below is taken from the manifest rows.
  - non-eval pipeline steps are tracked in local scheduler time from `sacct`.

## Change Timeline (Newest First)

### 2026-04-28: Unified subset-backed hybrid retrieval implemented (vector + lexical in Neo4j)

Implemented changes:

- Lexical grounding can now run against the same cardio-subset Neo4j store used by vector retrieval (no mandatory SNOMED DB lexical dependency).
- Retriever now supports:
  - vector lookup (`db.index.vector.queryNodes`),
  - lexical lookup (`db.index.fulltext.queryNodes`),
  - hybrid merge by `conceptid`.
- Grounding service lexical stage now prefers subset lexical retrieval and only falls back to SNOMED DB lexical search if subset lexical retrieval fails.
- Vector ingest now creates/maintains a fulltext index (`snomed_term_text_idx` by default) on `SnomedTerm.term`.
- Vector ingest stores additional term metadata (`type_id`, `term_type`, `language_code`) to enable future type-aware weighting (preferred/synonym/FSN handling).

Expected effect:

- Better retrieval coherence before reranking (same subset corpus for both channels).
- Reduced lexical/vector candidate disagreement caused by mixed backends.
- Improved recall opportunity for terminology variants through fulltext + vector over the same term nodes.

New runtime flags (defaults shown):

- `CARDIO_GRAPH_GROUNDING_SUBSET_LEXICAL_ENABLED=true`
- `CARDIO_GRAPH_GROUNDING_LEXICAL_TOP_K=80`
- `CARDIO_GRAPH_GROUNDING_FULLTEXT_INDEX=snomed_term_text_idx`
- `CARDIO_GRAPH_GROUNDING_LEXICAL_WEIGHT=0.30`
- `CARDIO_GRAPH_GROUNDING_VECTOR_WEIGHT=0.70`
- `CARDIO_GRAPH_GROUNDING_LEXICAL_CONTEXT_ENABLED=false`
- `CARDIO_GRAPH_GROUNDING_LEXICAL_CONTEXT_ALLOWED_ROLES=Procedure`
- `CARDIO_GRAPH_GROUNDING_LEXICAL_CONTEXT_APPEND_TERM=false`
- `CARDIO_GRAPH_GROUNDING_LEXICAL_CONTEXT_MAX_TOKENS=8`

Matrix extension request (to schedule):

Add context toggle as an explicit experiment dimension for retrieval-time query construction:

| Arm | Vector context | Lexical context | Goal |
|---|---|---|---|
| C0 | OFF | OFF | baseline unified hybrid |
| C1 | ON | OFF | isolate vector-context effect |
| C2 | OFF | ON | isolate lexical-context effect |
| C3 | ON | ON | combined context effect |

Recommendation:

- Run this context matrix first on scientific-original (`2a`) and production-original (`2b`) cells, since they are the most sensitive to retrieval recall before reranking.

### 2026-04-27: Report matrix summary (current)

Scope confirmed for reporting:

- Scientific track = no rescue map.
- Production track = rescue-enabled heldout mode.
- Helper meaning:
  - scientific helper = LLM candidate generation on `entity_original`
  - production helper = train-derived rescue map for the chosen term source

Current matrix snapshot:

| Cell | Definition | Run | Hits/Total | Accuracy | MRR | Status |
|---|---|---:|---:|---:|---:|---|
| 1a | Scientific + `entity_standardized_candidate` | `633654` | `109/120` | `0.908333` | `0.913333` | completed |
| 0  | Scientific + `entity_original` (absolute baseline) | `633663` | `33/132` | `0.250000` | `0.304885` | completed |
| 2a | Scientific + `entity_original` + LLM helper | `646306` | `57/132` | `0.431818` | `0.377936` | completed (retry-stabilized) |
| 1b | Production + `entity_standardized_candidate` + standardized rescue map | `633655` | `117/120` | `0.975000` | `0.978472` | completed |
| 2b | Production + `entity_original` + original-derived rescue map | `633686` | `65/132` | `0.492424` | `0.517432` | completed |

Notes:

- Latest scientific helper run (`646306`) completed end-to-end with retry protection enabled for transient empty/non-JSON LLM responses.
- Scientific helper improved substantially over original-only scientific baseline: accuracy `0.250000 -> 0.431818` (`+0.181818`, `+24` hits).
- Prior helper run `643994` remains useful as failure anatomy: many successful candidate calls, then late single-call parse failure (`Prasugrel`).
- Practical interpretation remains unchanged:
  - standardized input is strongly optimistic,
  - original-only no-helper baseline is severely degraded,
  - production rescue on original terms recovers more than scientific helper in this snapshot (`0.492424` vs `0.431818`), while both remain below standardized-track ceilings.

### 2026-04-23: 4-case matrix formalized + dedicated runners

Matrix now treated as first-class:

- Scientific x `entity_standardized_candidate`
- Scientific x `entity_original`
- Production x `entity_standardized_candidate`
- Production x `entity_original`

Implementations added:

- Separate production rescue maps by term source:
  - standardized: `config/cardio_graph_core/grounding_rescue_map_train_only.yaml`
  - original: `config/cardio_graph_core/grounding_rescue_map_train_only_original.yaml`
- New LLM normalization step for scientific-original viability:
  - BAML function `GenerateStandardizedCandidate(concept, role)` in `src/cardio_graph_core/extraction/baml_src/grounding_enrichment.baml`
  - integrated in grounding service behind `CARDIO_GRAPH_GROUNDING_LLM_STANDARDIZE_ORIGINAL_ENABLED`
  - current generation client set to `Qwen30b5` (candidate generation only)
- Dedicated slurm runners created for all four matrix cells:
  - `slurm/gt-eval-vector-locked-norescue-standardized.sbatch`
  - `slurm/gt-eval-vector-locked-norescue-original-hopper.sbatch`
  - `slurm/gt-eval-vector-heldout-trainrescue-standardized.sbatch`
  - `slurm/gt-eval-vector-heldout-trainrescue-original.sbatch`
- Scientific-original runner is pinned to hopper as required (`#SBATCH --gres=gpu:hopper:1`).

Runs launched from this matrix setup:

- Production x original (new original rescue map): `run_id=633686` (running)
- Scientific x original (LLM candidate step enabled): `run_id=633687` (running)

### 2026-04-23: Methodology Correction (short)

- Important finding: our GT grounding evaluation fed `entity_standardized_candidate` as the query term by default (optimistic setting).
- This can overestimate real-world performance, because deployment input is usually extractor raw text (`entity_original`).
- Corrective action implemented: evaluator now supports explicit term source switching (`standardized` vs `original`).
- Strict replay launched with original-only queries:
  - Scientific no-rescue: `run_id=633663`
  - Production heldout train-rescue: `run_id=633664`
- These runs are in progress and will be treated as the realism baseline once complete.

### 2026-04-23: LH3 PCI/Indication tuning runs completed (633654/633655)

Reviewed logs/artifacts:

- `slurm/gt-eval-vector-locked-norescue_633654.log`
- `slurm/gt-eval-vector-heldout_633655.log`
- `docs/generated/ground_truth/grounding_only/vector_job_633654/ground_truth_vector_eval.json`
- `docs/generated/ground_truth/grounding_only/vector_job_633655/ground_truth_vector_eval.json`

Confirmed outcomes:

- Scientific `633654`: accuracy `0.908333` (`109/120`), MRR `0.913333`, misses `11`
- Production `633655`: accuracy `0.975000` (`117/120`), MRR `0.978472`, misses `3`

Delta vs prior LH pair (`633138`/`633139`):

- Scientific improved: `0.866667 -> 0.908333` (`+0.041667`, `104/120 -> 109/120`)
- Production slight regression: `0.983333 -> 0.975000` (`-0.008333`, `118/120 -> 117/120`)

Residual miss families after LH3:

- Scientific still dominated by PCI variant decision (`415070008` vs `713617008`, 8 repeats).
- Scientific residuals: CABG granularity, one `Indication of` drift, one proton-pump-inhibitor abstraction.
- Production residuals: CABG granularity, one `General characteristic of patient` qualifier variant, one rivaroxaban abstraction.

Interpretation:

- Scientific track crossed 90% on locked test without rescue and improved substantially.
- Production remains very strong, with a small drop concentrated in one additional miss.

### 2026-04-23: LH results review + next targeted runs planned

Reviewed logs:

- `slurm/gt-eval-vector-locked-norescue_633138.log`
- `slurm/gt-eval-vector-heldout_633139.log`

Confirmed outcomes:

- Scientific `633138`: accuracy `0.866667` (`104/120`), MRR `0.881389`, misses `16`
- Production `633139`: accuracy `0.983333` (`118/120`), MRR `0.984722`, misses `2`

Residual miss clusters after LH:

- Scientific: PCI variant tie (`415070008` vs angioplasty variant `41339005`) recurring.
- Scientific: `Indication of` contextual qualifier (`230165009`) drifting to finding (`408343002`).
- Production: single CABG granularity over-specificity.
- Production: `Rivaroxaban` substance vs therapy procedure abstraction.

Planned next runs (submitted):

1. `LH3A_SCI_PCI_INDICATION_FIX` (scientific no-rescue) -> `run_id=633654`
2. `LH3B_PROD_PCI_INDICATION_FIX` (production heldout train-rescue) -> `run_id=633655`

### 2026-04-22: Low-hanging-fruit (LH1/LH2) replay chain completed successfully

Pipeline chain completion (scheduler):

- `633136` `cardio-subset-gen` COMPLETED (`14:56:04 -> 16:38:56`, `01:42:52`)
- `633137` `vector-index-rebuild` COMPLETED (`16:38:57 -> 17:44:15`, `01:05:18`)
- `633138` `gt-eval-vector-locked-norescue` COMPLETED (`17:44:15 -> 18:24:24`, `00:40:09`)
- `633139` `gt-eval-vector-heldout` COMPLETED (`17:44:15 -> 18:20:08`, `00:35:53`)

LH run outcomes (manifest):

- Scientific `633138`: accuracy `0.866667` (`104/120`), MRR `0.881389`
- Production `633139`: accuracy `0.983333` (`118/120`), MRR `0.984722`

Interpretation:

- This is the strongest completed pair in the current tracker window.
- Compared to the already-improved active-only pair (`632982` / `632983`):
  - scientific gained `+0.075000` accuracy (`0.791667 -> 0.866667`)
  - production gained `+0.066667` accuracy (`0.916667 -> 0.983333`)

### 2026-04-22: Active-only alignment breakthrough (lexical + vector consistency)

Key change set:

- active-only consistency enforced across both retrieval paths:
  - subset generation active-filter,
  - vector ingest active concepts,
  - lexical SNOMED queries active concepts.

Representative replay pair:

- Scientific `632982` vs prior `632971`: `0.791667` vs `0.691667` (`+0.100000`)
- Production `632983` vs prior `632972`: `0.916667` vs `0.816667` (`+0.100000`)

Primary finding:

- inactive/legacy concept contamination stopped being a dominant failure source.
- residual misses shifted to medication abstraction/tie-break and small procedure granularity cases.

### 2026-04-21: GT-recovery profile replays and operational reliability incidents

Runs:

- Scientific `632955`: accuracy `0.683333` (`82/120`), MRR `0.738883`
- Production `632956`: accuracy `0.808333` (`97/120`), MRR `0.846458`

Operational incident:

- `632960` vector-index-rebuild FAILED immediately (`ExitCode=2:0`), later addressed in subsequent chain hardening.

### 2026-04-21: Detailed loss diagnostics for `632933` / `632934`

Key diagnostic conclusion:

- production residual misses were predominantly tie-break/disambiguation (`GT present, not top-1`), not retrieval absence.
- scientific still had a targeted GT-absent cluster for `Percutaneous coronary revascularization` in no-rescue mode.

### 2026-04-20: Trace and probing analyses established policy split

Trace pair:

- Scientific trace `632922`: accuracy `0.566667`
- Production trace `632923`: accuracy `0.800000`

Additional pair:

- Scientific `632933`: `0.691667`
- Production `632934`: `0.900000`

Policy crystallized:

- production track may use deterministic exception strategies.
- scientific track remains no-rescue and avoids term-specific hand-crafted exceptions.

### 2026-04-17: Probing matrix

Matrix arms and outcomes:

- Scientific: `632860`/`632861`/`632862` (`0.541667`, `0.516667`, `0.516667`)
- Production: `632863`/`632864`/`632865` (`0.825000`, `0.800000`, `0.791667`)

Finding:

- in that phase, production train-only replay outperformed full-map variants on locked split.

### 2026-04-15: Initial tracked scientific/production baseline sequence

- `630835` dev no-rescue baseline
- `630836` train-rescue derivation step (non-eval)
- `630837` scientific locked_test headline
- `630838` production train-rescue locked_test validation

### 2026-04-14: Early all-table pilot runs

- `630501`, `630502` on broader all-table setup before later locked/dev split focus.

## Chronological Run Ledger (Newest First)

| timestamp_utc | run_id | split | track | accuracy | hits/total | mrr | artifact |
|---|---:|---|---|---:|---|---:|---|
| 2026-04-23T09:55:00.219744+00:00 | 633654 | locked_test | scientific | 0.908333 | 109/120 | 0.913333 | `docs/generated/ground_truth/grounding_only/vector_job_633654/ground_truth_vector_eval.json` |
| 2026-04-23T09:51:07.616376+00:00 | 633655 | locked_test | production | 0.975000 | 117/120 | 0.978472 | `docs/generated/ground_truth/grounding_only/vector_job_633655/ground_truth_vector_eval.json` |
| 2026-04-22T16:24:24.065082+00:00 | 633138 | locked_test | scientific | 0.866667 | 104/120 | 0.881389 | `docs/generated/ground_truth/grounding_only/vector_job_633138/ground_truth_vector_eval.json` |
| 2026-04-22T16:20:07.258508+00:00 | 633139 | locked_test | production | 0.983333 | 118/120 | 0.984722 | `docs/generated/ground_truth/grounding_only/vector_job_633139/ground_truth_vector_eval.json` |
| 2026-04-22T11:50:16.300712+00:00 | 632982 | locked_test | scientific | 0.791667 | 95/120 | 0.806389 | `docs/generated/ground_truth/grounding_only/vector_job_632982/ground_truth_vector_eval.json` |
| 2026-04-22T11:45:42.328598+00:00 | 632983 | locked_test | production | 0.916667 | 110/120 | 0.936806 | `docs/generated/ground_truth/grounding_only/vector_job_632983/ground_truth_vector_eval.json` |
| 2026-04-22T10:45:54.999302+00:00 | 632971 | locked_test | scientific | 0.691667 | 83/120 | 0.739855 | `docs/generated/ground_truth/grounding_only/vector_job_632971/ground_truth_vector_eval.json` |
| 2026-04-22T10:41:29.504951+00:00 | 632972 | locked_test | production | 0.816667 | 98/120 | 0.832222 | `docs/generated/ground_truth/grounding_only/vector_job_632972/ground_truth_vector_eval.json` |
| 2026-04-21T11:53:26.541065+00:00 | 632955 | locked_test | scientific | 0.683333 | 82/120 | 0.738883 | `docs/generated/ground_truth/grounding_only/vector_job_632955/ground_truth_vector_eval.json` |
| 2026-04-21T11:48:50.168025+00:00 | 632956 | locked_test | production | 0.808333 | 97/120 | 0.846458 | `docs/generated/ground_truth/grounding_only/vector_job_632956/ground_truth_vector_eval.json` |
| 2026-04-20T14:28:26.885284+00:00 | 632932 | dev | scientific | 0.581395 | 75/129 | 0.650184 | `docs/generated/ground_truth/grounding_only/vector_job_632932/ground_truth_vector_eval.json` |
| 2026-04-20T14:26:40.906666+00:00 | 632933 | locked_test | scientific | 0.691667 | 83/120 | 0.692958 | `docs/generated/ground_truth/grounding_only/vector_job_632933/ground_truth_vector_eval.json` |
| 2026-04-20T14:20:51.754681+00:00 | 632934 | locked_test | production | 0.900000 | 108/120 | 0.854230 | `docs/generated/ground_truth/grounding_only/vector_job_632934/ground_truth_vector_eval.json` |
| 2026-04-20T12:46:34.644076+00:00 | 632922 | locked_test | scientific | 0.566667 | 68/120 | 0.613690 | `docs/generated/ground_truth/grounding_only/vector_job_632922/ground_truth_vector_eval.json` |
| 2026-04-20T12:36:07.857263+00:00 | 632923 | locked_test | production | 0.800000 | 96/120 | 0.822024 | `docs/generated/ground_truth/grounding_only/vector_job_632923/ground_truth_vector_eval.json` |
| 2026-04-17T22:56:08.486060+00:00 | 632865 | locked_test | production | 0.791667 | 95/120 | 0.805357 | `docs/generated/ground_truth/grounding_only/vector_job_632865/ground_truth_vector_eval.json` |
| 2026-04-17T21:39:44.403175+00:00 | 632864 | locked_test | production | 0.800000 | 96/120 | 0.813690 | `docs/generated/ground_truth/grounding_only/vector_job_632864/ground_truth_vector_eval.json` |
| 2026-04-17T20:24:47.031145+00:00 | 632863 | locked_test | production | 0.825000 | 99/120 | 0.842857 | `docs/generated/ground_truth/grounding_only/vector_job_632863/ground_truth_vector_eval.json` |
| 2026-04-17T19:11:50.279672+00:00 | 632862 | locked_test | scientific | 0.516667 | 62/120 | 0.567857 | `docs/generated/ground_truth/grounding_only/vector_job_632862/ground_truth_vector_eval.json` |
| 2026-04-17T17:46:47.392017+00:00 | 632861 | locked_test | scientific | 0.516667 | 62/120 | 0.597718 | `docs/generated/ground_truth/grounding_only/vector_job_632861/ground_truth_vector_eval.json` |
| 2026-04-17T16:23:22.620224+00:00 | 632860 | locked_test | scientific | 0.541667 | 65/120 | 0.588690 | `docs/generated/ground_truth/grounding_only/vector_job_632860/ground_truth_vector_eval.json` |
| 2026-04-15T18:58:36.420287+00:00 | 630838 | locked_test | production | 0.866667 | 104/120 | 0.872024 | `docs/generated/ground_truth/grounding_only/vector_job_630838/ground_truth_vector_eval.json` |
| 2026-04-15T17:47:37.974180+00:00 | 630837 | locked_test | scientific | 0.483333 | 58/120 | 0.522024 | `docs/generated/ground_truth/grounding_only/vector_job_630837/ground_truth_vector_eval.json` |
| 2026-04-15T17:44:25.178160+00:00 | 630835 | dev | scientific | 0.620155 | 80/129 | 0.653378 | `docs/generated/ground_truth/grounding_only/vector_job_630835/ground_truth_vector_eval.json` |
| 2026-04-14T17:58:01.602841+00:00 | 630502 | all_tables | pilot | 0.793991 | 185/233 | 0.810852 | `docs/generated/ground_truth/grounding_only/vector_job_630502/ground_truth_vector_eval.json` |
| 2026-04-14T17:57:58.831106+00:00 | 630501 | all_tables | pilot | 0.824034 | 192/233 | 0.825874 | `docs/generated/ground_truth/grounding_only/vector_job_630501/ground_truth_vector_eval.json` |

## Non-Eval Pipeline Ledger (Newest First)

| timestamp_local | job_id | job_name | state | elapsed | note |
|---|---:|---|---|---|---|
| 2026-04-22T16:38:57 -> 2026-04-22T17:44:15 | 633137 | vector-index-rebuild | COMPLETED | 01:05:18 | active-only subset ingest refresh |
| 2026-04-22T14:56:04 -> 2026-04-22T16:38:56 | 633136 | cardio-subset-gen | COMPLETED | 01:42:52 | subset regeneration for LH chain |
| 2026-04-21T17:02:05 -> 2026-04-21T17:02:05 | 632960 | vector-index-rebuild | FAILED | 00:00:00 | early rebuild failure (resolved in later chain) |
| 2026-04-15T19:44:26 -> 2026-04-15T19:44:31 | 630836 | derive-train-rescue | COMPLETED | 00:00:05 | train-only rescue map derivation |

## Recovered Detailed Artifact Map

These files carry the detailed intermediate analyses that were accumulated across the last ~10 days and are intentionally preserved in this timeline context:

- `docs/generated/grounding/mismatch_analysis_trace_632922_vs_632923.md`
- `docs/generated/grounding/mismatch_analysis_trace_632933_vs_632934.md`
- `docs/generated/grounding/stage_trace_vector_job_632922.csv`
- `docs/generated/grounding/stage_trace_vector_job_632923.csv`
- `docs/generated/ground_truth/grounding_only/vector_job_632933/ground_truth_vector_eval_debug_probe.csv`
- `docs/generated/ground_truth/grounding_only/vector_job_632934/ground_truth_vector_eval_debug_probe.csv`

## Preserved Key Findings Across Phases

1. End-to-end active-only alignment (subset + ingest + lexical) was a major inflection point.
2. Post-alignment residuals shifted from inactive-ID contamination to tie-break/semantic disambiguation.
3. Trace instrumentation showed substantial miss mass from domain filtering in earlier phases.
4. Production exception strategy and scientific no-rescue purity were kept explicitly separated by policy.
5. Current best split pair is `633654` (scientific best) and `633139` (production best), showing distinct scientific/production optima.

## Update Rule

For every future experiment, append at the top (newest-first) with:

1. what changed (scoring/filtering/index/subset),
2. exact run IDs and timestamps,
3. scientific + production metrics,
4. interpretation of error-family shift,
5. links to artifacts/logs.
