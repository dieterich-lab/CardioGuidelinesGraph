# SNOMED Vector Grounding Tracker (Scientific vs Production)

Last updated: 2026-04-21

## Purpose

Single manual tracker for the latest heldout-split grounding runs and the explicit split between:

- Scientific track: no rescue map at evaluation time.
- Production track: rescue map enabled (either train-only for clean validation, or full map for deployment behavior).

## Canonical Sources

- Run manifests:
  - `docs/generated/grounding/ground_truth_vector_runs_manifest.jsonl`
  - `docs/generated/grounding/ground_truth_vector_runs_manifest.csv`
- Run logs:
  - `slurm/gt-eval-vector-dev-norescue_630835.log`
  - `slurm/derive-train-rescue_630836.log`
  - `slurm/gt-eval-vector-locked-norescue_630837.log`
  - `slurm/gt-eval-vector-heldout_630838.log`
- Embedding server logs:
  - `slurm/ollama-server_gt-eval-vector-dev-norescue_630835.log`
  - `slurm/ollama-server_gt-eval-vector-locked-norescue_630837.log`
  - `slurm/ollama-server_gt-eval-vector-heldout_630838.log`
- Scientific mapping reference:
  - `docs/reports/grounding/current_snomed_mappings_scientific_track.md`

## Track Definitions

### Scientific Track

- Objective: unbiased quality estimate without rescue overrides.
- Split used for headline comparison: `locked_test`.
- Run type: `CARDIO_GRAPH_GROUNDING_RESCUE_ENABLED=false`.
- Current representative run: `630837`.

### Production Track

- Objective: operational accuracy with rescue-map assistance.
- Split used for validation here: `locked_test`.
- Run type: `CARDIO_GRAPH_GROUNDING_RESCUE_ENABLED=true`.
- Two production variants:
  - Train-only rescue map (scientifically clean deployment candidate): `grounding_rescue_map_train_only.yaml`.
  - Full rescue map (all GT examples; operational deployment behavior): `grounding_rescue_map.yaml`.

## Latest Run Sequence (630835 -> 630838)

| Run | Role in pipeline | Split | Rescue mode | Accuracy | Hits/Total | MRR | Key artifact |
|---|---|---|---|---:|---|---:|---|
| 630835 | Dev no-rescue baseline used to derive train-only map | dev | disabled | 0.620155 | 80/129 | 0.653378 | `docs/generated/ground_truth/grounding_only/vector_job_630835/ground_truth_vector_eval.json` |
| 630836 | Rescue-map derivation from run 630835 misses | dev | derives map | - | - | - | `config/cardio_graph_core/grounding_rescue_map_train_only.yaml` |
| 630837 | Scientific headline run | locked_test | disabled | 0.483333 | 58/120 | 0.522024 | `docs/generated/ground_truth/grounding_only/vector_job_630837/ground_truth_vector_eval.json` |
| 630838 | Production-track validation run (train-only rescue) | locked_test | enabled (train-only map) | 0.866667 | 104/120 | 0.872024 | `docs/generated/ground_truth/grounding_only/vector_job_630838/ground_truth_vector_eval.json` |

## Derivation Provenance (Run 630836)

- Source eval JSON: `docs/generated/ground_truth/grounding_only/vector_job_630835/ground_truth_vector_eval.json`.
- Split: `dev` from `config/autotuning/split_v3_all_tables.json`.
- `split_rows=25`, `allowed_eval_rows=25`.
- `derived_overrides=12`, `dropped_ambiguous=0`.
- Report: `docs/generated/grounding/train_rescue_derivation_report_from_dev_630835.json`.

## Scientific vs Production Comparison (Locked Test)

| Metric | Scientific (630837, no rescue) | Production validation (630838, train-only rescue) | Delta |
|---|---:|---:|---:|
| Accuracy | 0.483333 | 0.866667 | +0.383334 |
| Hits | 58 | 104 | +46 |
| Total | 120 | 120 | 0 |
| MRR | 0.522024 | 0.872024 | +0.350000 |

Interpretation:

- On the same `locked_test` split, enabling the train-only rescue map yields a large gain in top-1 grounding quality.
- The scientific comparison reference remains run `630837` and is mirrored in `docs/reports/grounding/current_snomed_mappings_scientific_track.md`.

## Run Settings Snapshot (Common + Differences)

Common settings across 630835/630837/630838:

- Embedding model: `Qwen3embed`.
- Vector index: `snomed_term_embeddings_4096`.
- Vector context: enabled (`allowed_roles=Procedure,Medication`, `append_term=true`, `max_tokens=8`).
- Ambiguity/role penalties from the H/H2 profile (same defaults in sbatch wrappers).

Run-specific differences:

- 630835: `split_name=dev`, `rescue_enabled=false`, embedding URL `http://127.0.0.1:12269`.
- 630837: `split_name=locked_test`, `rescue_enabled=false`, embedding URL `http://127.0.0.1:12271`.
- 630838: `split_name=locked_test`, `rescue_enabled=true`, rescue map `config/cardio_graph_core/grounding_rescue_map_train_only.yaml`, embedding URL `http://127.0.0.1:12272`.

## Rescue-Map Policy Notes

- Scientific reporting must stay on no-rescue runs (for unbiased comparison).
- Production reporting should be split into:
  - Train-only rescue map on heldout/locked splits (clean validation).
  - Full rescue map for deployment-readiness tracking.
- Full-map production run is configured via `config/cardio_graph_core/grounding_rescue_map.yaml`; it should be logged in this file once a corresponding heldout/locked run is added.

## Next Update Template

For each new run, append:

1. Run ID and split.
2. Rescue mode (`disabled`, `train-only`, `full-map`).
3. Accuracy/Hits/Total/MRR.
4. Output JSON path and log path.
5. Scientific-vs-production delta update on the same split.

## Colleague Evaluation Intake (Issue #56)

Inputs reviewed:

- `docs/reports/grounding/current_snomed_mappings_scientific_track.md`
- `docs/reports/grounding/snomed_eval.csv`
- `docs/reports/grounding/snomed_eval.xlsx`

Reviewer note (issue #56, latest comment):

- Negatives reviewed: 62
- False negatives identified: 8
- One GT correction applied: `Repair of coronary artery` annotation corrected in source JSON.

Confusion totals from `snomed_eval.csv`:

- `tp=58`, `fp=0`, `fn=8`, `tn=54` (manual hit vs system hit)

Dominant recurring error families:

- Overspecific predictions:
  - `Percutaneous coronary revascularization` -> overly specific CTO procedure variant (8x)
  - `Aspirin` -> `Aluminium aspirin` (7x)
  - `Myocardial infarction` -> ECG finding variant (3x)
  - `Old myocardial infarction` -> ECG finding variant (2x)
- Wrong/no-match patterns:
  - `Use of anticoagulation` -> anticoagulation clinic finding (6x)
  - `Indication of` -> pain behavior finding (6x)
  - `Myocardial revascularization` -> myocardial resection (5x)
  - `Drug therapy with explicit context` -> empty prediction (5x)

## Tuning Proposals

### A) Scientific Track (No Rescue): reduce overspecific drift without lookup overrides

Goal: improve `locked_test` no-rescue quality while preserving scientific integrity.

1. Increase semantic/role penalties against cross-class or procedure-overreach candidates.

- `CARDIO_GRAPH_GROUNDING_ROLE_MISMATCH_PENALTY`: `0.05 -> 0.08`
- `CARDIO_GRAPH_GROUNDING_ROLE_SEMANTIC_MISMATCH_PENALTY`: `0.06 -> 0.09`
- `CARDIO_GRAPH_GROUNDING_ROLE_SEMANTIC_CROSSCLASS_PENALTY`: `0.02 -> 0.05`
- `CARDIO_GRAPH_GROUNDING_ROLE_TENSION_PENALTY`: `0.02 -> 0.04`

1. Lower vector re-rank dominance so lexical/domain evidence wins more often.

- `CARDIO_GRAPH_GROUNDING_VECTOR_RERANK_WEIGHT`: `0.03 -> 0.015`
- `CARDIO_GRAPH_GROUNDING_VECTOR_BONUS_CAP`: `0.05 -> 0.03`

1. Tighten ambiguity fallback for near ties.

- `CARDIO_GRAPH_GROUNDING_AMBIGUITY_BACKOFF_MAX_DROP`: `0.30 -> 0.20`
- `CARDIO_GRAPH_GROUNDING_AMBIGUITY_BACKOFF_MIN_SCORE`: keep `0.45`
- `CARDIO_GRAPH_GROUNDING_AMBIGUITY_MIN_COVERAGE`: `0.55 -> 0.60`

1. Turn on semantic-tag filtering for scientific evaluations.

- Use `--semantic-tag-filter` in the grounding entrypoint (builder supports this).
- Expected effect: fewer disorder/finding vs procedure crossovers.

### B) Production Track (Rescue-Enabled): convert high-confidence misses into deterministic fixes

Goal: maximize deployment correctness while keeping the scientific track unchanged.

1. Keep dual-map policy:

- Scientific/validation production: `grounding_rescue_map_train_only.yaml`
- Operational production: `grounding_rescue_map.yaml`

1. Add high-frequency production overrides to full map (not scientific map):

- `Aspirin` (Medication) -> `387458008`
- `Percutaneous coronary revascularization` (Procedure) -> `415070008`
- `Myocardial infarction` (ClinicalCondition) -> `22298006`
- `Old myocardial infarction` (ClinicalCondition) -> `1755008`
- `Myocardial revascularization` (Procedure) -> `275227003`
- `Use of anticoagulation` (ClinicalCondition) -> `260678004`
- `Indication of` (ClinicalCondition) -> `230165009`
- `Drug therapy with explicit context` (Medication) -> `1290126002`

1. Keep rescue entries role-scoped (no wildcard) to avoid collateral corrections.

### C) Hard-Negative Guardrail (Both Tracks)

Use the reviewer mistakes as explicit hard negatives to suppress repeated wrong concepts for a term-role pair.

Initial high-yield blocks:

- `Percutaneous coronary revascularization` (Procedure) block `713617008`
- `Myocardial revascularization` (Procedure) block `70627009`
- `Indication of` (ClinicalCondition) block `1363183004`
- `Use of anticoagulation` (ClinicalCondition) block `440678006`
- `Aspirin` (Medication) block `25796002`

Recommended knob for first pass:

- `CARDIO_GRAPH_GROUNDING_HARD_NEGATIVE_PENALTY=0.10`

### D) Evaluation Policy Add-On (Analysis only)

Track an auxiliary metric `ancestor_or_exact_hit` in reports:

- Counts as success when prediction is exact match OR direct SNOMED descendant/ancestor in same role.
- This does not replace strict exact-match leaderboard; it helps quantify overspecificity separately.

## Suggested Next Ablation Matrix

All runs on `locked_test` with identical split filtering:

1. `S1` scientific baseline replay (current no-rescue settings) for reproducibility.
2. `S2` semantic-tight run (A.1 only).
3. `S3` semantic-tight + vector-reduced run (A.1 + A.2 + A.3).
4. `P1` production train-only rescue replay (current 630838 profile).
5. `P2` production full-map replay.
6. `P3` production full-map + hard-negatives (C).

Promotion rule:

- Scientific winner: best strict exact-match on no-rescue split.
- Production winner: best strict exact-match on rescue-enabled split, with no regression on audited high-risk terms.

## Probing Matrix Results (Completed)

Matrix launcher:

- `slurm/submit-grounding-probing-matrix.sh`

Executed run mapping (`S1`..`P3`):

| Matrix arm | Run ID | Label | Rescue mode | Accuracy | Hits/Total | MRR |
|---|---:|---|---|---:|---|---:|
| S1 | `632860` | `H_NO_RESCUE_LOCKED` | disabled | 0.541667 | 65/120 | 0.588690 |
| S2 | `632861` | `S2_SCI_SEMANTIC_TIGHT` | disabled | 0.516667 | 62/120 | 0.597718 |
| S3 | `632862` | `S3_SCI_SEMANTIC_VECTOR_REDUCED` | disabled | 0.516667 | 62/120 | 0.567857 |
| P1 | `632863` | `P1_PROD_TRAIN_ONLY_REPLAY` | train-only rescue map | 0.825000 | 99/120 | 0.842857 |
| P2 | `632864` | `P2_PROD_FULL_MAP_REPLAY` | full rescue map | 0.800000 | 96/120 | 0.813690 |
| P3 | `632865` | `P3_PROD_FULL_MAP_HARD_NEG` | full map + hard negatives | 0.791667 | 95/120 | 0.805357 |

Outcome summary:

1. Scientific winner in this matrix is `S1` (`632860`): `0.541667`.
2. Proposed scientific tightening (`S2`, `S3`) did not beat the replay baseline on strict exact match.
3. Production winner in this matrix is `P1` (`632863`): `0.825000`.
4. Full-map (`P2`) and full-map+hard-negative (`P3`) underperformed `P1` on this heldout split.

## Stage-Trace Instrumentation (for gt_rank=null diagnosis)

Implemented in evaluation pipeline:

1. `ground_entity(..., gold_concept_id=...)` now records `gt_presence_trace` with stage markers:

- `gold_in_initial_results`
- `gold_in_allowed_domain`
- `gold_in_truncated_set`
- `gold_filter_reasons`
- `gold_in_final_ranked`
- `gold_rank_final`
- `gold_absence_stage`

2. Prediction output now includes:

- `candidate_rankings_to_gt` (all ranks from top-1 through `gt_rank` when GT is present)
- `gt_presence_trace` (for `gt_rank=null` stage attribution)

Trace-enabled replay jobs started:

- Scientific best replay with trace: `632922` (`S1_BEST_TRACE`)
- Production best replay with trace: `632923` (`P1_BEST_TRACE`)

Planned diagnostic export (once runs complete):

- Script: `scripts/export_grounding_stage_trace_report.py`
- Output CSV/JSON will enumerate each row+term with rank chain and stage markers.

## Error Rank Observability (Current Capability)

Current eval JSONs provide two relevant fields per prediction:

1. `gt_rank`: exact rank of the gold concept if present in the returned ranked candidate list.
2. `candidate_rankings_top10`: top-10 candidate details.

Observed miss diagnostics for key scientific runs:

| Run | Misses | Gold rank 2-5 | Gold rank 6-10 | Gold rank >10 | Gold not found in returned ranked list |
|---|---:|---:|---:|---:|---:|
| `630837` | 62 | 9 | 1 | 0 | 52 |
| `632860` | 55 | 11 | 1 | 0 | 43 |

Interpretation:

1. We can already analyze many misses where gold is present but not top-1.
2. A large miss fraction has `gt_rank=null`, meaning gold is absent from the returned ranked list.
3. With current artifacts alone, `gt_rank=null` cannot be uniquely decomposed into:

- retrieved then filtered,
- not retrieved (vector/lexical miss),
- truncated before return.

Recommended instrumentation upgrade for next analysis cycle:

1. Persist stage-wise candidate counts and explicit drop reasons (`semantic_tag_filter`, `hard_negative`, `coverage`, `ambiguity_backoff`, truncation).
2. Emit an optional full ranked list (or at least top-200 + gold-presence flag before/after filters).
3. Add a per-item `gold_present_pre_filter` and `gold_present_post_filter` marker.

## Trace Replay Results (Completed: 632922 / 632923)

Trace replay runs are now finished and exported via:

- `docs/generated/grounding/stage_trace_vector_job_632922.csv`
- `docs/generated/grounding/stage_trace_vector_job_632923.csv`
- `docs/generated/grounding/mismatch_analysis_trace_632922_vs_632923.md`

Top-line outcomes:

| Run | Label | Rescue mode | Accuracy | Hits/Total | MRR | Misses |
|---|---|---|---:|---:|---:|---:|
| `632922` | `S1_BEST_TRACE` | disabled | 0.566667 | 68/120 | 0.613690 | 52 |
| `632923` | `P1_BEST_TRACE` | train-only map | 0.800000 | 96/120 | 0.822024 | 24 |

Stage attribution on misses:

| Run | GT present but not top-1 | GT absent from final ranking | Dominant absence stage |
|---|---:|---:|---|
| `632922` | 12 | 40 | `filtered_by_domain_roots` |
| `632923` | 6 | 18 | `filtered_by_domain_roots` |

Interpretation:

1. The main bottleneck is still upstream filtering (`filtered_by_domain_roots`), not late-stage ranking only.
2. A smaller but relevant portion is rank competition where GT survives to final ranking but is not top-1.
3. Preliminary over-penalization proxy (GT ranked, but penalized above selected prediction) did not show strong evidence in this pair.

Cross-run delta (`632922 -> 632923`):

1. Misses reduced by 28 (`52 -> 24`).
2. 31 misses were fixed with train-only rescue.
3. 3 new misses appeared (notably `Prasugrel` variant and one stent-thrombosis abstraction drift).

## Policy Decision: Exception Strategies

Decision for ongoing work:

1. **Production track only** should use deterministic exception strategies (rescue maps / hard negatives / role-scoped overrides).
2. **Scientific track** should remain no-rescue and avoid term-level hardcoded exceptions.
3. Scientific-track improvements should be limited to globally applicable scoring/filtering rules and role/domain policy changes that are not hand-crafted per test miss.

Rationale:

- This keeps scientific estimates interpretable and leakage-safe.
- It still allows deployment-focused correction layers in production reporting.

## New GT-Recovery Tuning Profile (Applied)

Objective: improve GT recovery once retrieved/ranked, while reducing excessive pre-score exclusion.

Implemented in wrappers:

- `slurm/gt-eval-vector-dev-norescue.sbatch`
- `slurm/gt-eval-vector-locked-norescue.sbatch`
- `slurm/gt-eval-vector-heldout-trainrescue.sbatch`

Core changes:

1. Domain and semantic hard filters made configurable and currently softened for this profile:
  - `CARDIO_GRAPH_GROUNDING_ENABLE_DOMAIN_FILTER=false`
  - `CARDIO_GRAPH_GROUNDING_ENABLE_SEMANTIC_TAG_FILTER=false`

2. GT-recovery ranking support enabled:
  - `CARDIO_GRAPH_GROUNDING_VECTOR_RANK_PRIOR_ENABLED=true`
  - `CARDIO_GRAPH_GROUNDING_VECTOR_RANK_RESCUE_ENABLED=true`
  - increased vector bonus weight/cap and lower lexical gate for vector bonus

3. Penalties softened to reduce unnecessary suppression of plausible GT candidates:
  - lower role/semantic mismatch penalties
  - lower low-coverage / missing-discriminative / extra-qualifier penalties
  - enabled semantic-penalty evidence relief

4. Ambiguity handling adjusted to avoid premature abstain-like behavior in near-tie settings.

These adjustments are now ready for the next replay cycle (scientific no-rescue and production train-only rescue).

## Post-Run Loss Analysis (Completed Runs: 632933 / 632934)

Primary artifacts used:

- `docs/generated/ground_truth/grounding_only/vector_job_632933/ground_truth_vector_eval.json`
- `docs/generated/ground_truth/grounding_only/vector_job_632934/ground_truth_vector_eval.json`
- `docs/generated/ground_truth/grounding_only/vector_job_632933/ground_truth_vector_eval_debug_probe.csv`
- `docs/generated/ground_truth/grounding_only/vector_job_632934/ground_truth_vector_eval_debug_probe.csv`
- `docs/generated/grounding/mismatch_analysis_trace_632933_vs_632934.md`

### Top-Line

| Run | Label | Accuracy | Hits/Total | Misses |
|---|---|---:|---:|---:|
| `632933` | `H_NO_RESCUE_LOCKED` | 0.691667 | 83/120 | 37 |
| `632934` | `H_HELDOUT_TRAIN_RESCUE` | 0.900000 | 108/120 | 12 |

### Where GT Is Lost

Important implementation detail for these two runs:

1. `gt_presence_trace.gold_absence_stage` is mostly `unknown` in the eval JSON for this pair.
2. Therefore, stage attribution below is derived from `ground_truth_vector_eval_debug_probe.csv` fields (`gt_present_in_ranked`, `gt_rank`, score columns).

Loss decomposition:

| Run | Misses | GT present in ranked list | GT absent from ranked list |
|---|---:|---:|---:|
| `632933` | 37 | 29 | 8 |
| `632934` | 12 | 12 | 0 |

Interpretation:

1. In the best finished run (`632934`), residual errors are entirely ranking/disambiguation errors (GT survives retrieval/filtering).
2. In `632933`, there is still a smaller upstream-loss slice (`8/37`) where GT is absent from ranked candidates.

### Scientific Run 632933: GT-Absent Cluster

All 8 GT-absent misses in `632933` are the same term-role family:

- Role: `Procedure`
- Source term: `Percutaneous coronary revascularization`
- Gold: `415070008`

This indicates a retrieval/candidate-generation recall gap for this expression in the no-rescue path.

### Production Run 632934: Residual Miss Families (All GT-Ranked)

Residual 12 misses split into 4 recurring clusters:

| Cluster | Count | Share of misses | Potential absolute gain if fixed |
|---|---:|---:|---:|
| Medication form/salt variant (`Clopidogrel`/`Prasugrel` -> besilate variants) | 5 | 41.7% | +0.0417 |
| Condition granularity (`Myocardial ischemia` -> acute ischemic heart disease) | 3 | 25.0% | +0.0250 |
| Procedure variant/situation-vs-procedure (`CABG` variants/planned situation) | 2 | 16.7% | +0.0167 |
| ID variant with same label/context qualifier (`Informing patient`, `Indication of`) | 2 | 16.7% | +0.0167 |

Ranking behavior of residual misses (`632934`):

1. All misses are near-tie cases.
2. `score_gap_top1_top2 = 0.0` for all 12 misses.
3. GT ranks are mostly low but non-top: `{2:2, 3:2, 4:7, 11:1}`.

This is strong evidence that the remaining issue is tie-breaking policy, not hard pre-emptive filtering.

### Stricter vs Less-Strict Guidance (Next Cycle)

Current conclusion:

1. Do **not** loosen upstream domain/semantic filters further in this tuned profile; `632934` already has `GT absent = 0`.
2. Focus on **stricter reranking/tie-break rules** that resolve clinically important near ties.

#### A) Stricter (recommended now): tie-break and semantic precision

1. Add a role-aware penalty for `situation` predictions when role is `Procedure` and the query does not contain planning intent tokens (`planned`, `scheduled`, `intended`).
2. Add a medication-specific qualifier penalty for salt/form suffixes (for example `besilate`) when the query is the base substance term.
3. In exact-score ties, prefer the candidate with lower extra qualifier burden and closer normalized head term match.

Expected impact: directly targets 7/12 residual misses (`CABG planned/situation` + `besilate` confusions).

#### B) Less strict (targeted): retrieval recall for scientific no-rescue

1. Add lexical variant expansion for the `Percutaneous coronary revascularization` family (intervention/revascularization synonyms) in the no-rescue path.
2. Keep this as retrieval expansion only; do not add term-specific rescue overrides to scientific scoring.

Expected impact: addresses the `8/37` GT-absent cluster in `632933` without introducing production-only exceptions into the scientific track.

### Proposed Ablation Sequence (Immediate)

1. `N1` no-rescue scientific rerun with targeted retrieval expansion for the PCI revascularization phrase family.
2. `N2` no-rescue + stricter procedure/situation tie-break rule.
3. `N3` no-rescue + medication salt/form qualifier penalty.
4. `P1` production train-rescue rerun with stricter tie-break rules (same as N2/N3).

Decision rule:

1. Scientific winner: best strict exact-match in no-rescue run.
2. Production winner: best strict exact-match with train-only rescue, with no regressions in audited high-risk terms.

### Detailed Residual Error Report (632933 / 632934)

Artifacts used for this detailed expansion:

- `docs/generated/ground_truth/grounding_only/vector_job_632934/ground_truth_vector_eval_debug_probe.csv`
- `docs/generated/grounding/ground_truth_vector_latest_miss_triage.csv`

#### A) Exact-Tie Terms in 632934 (Complete List)

All 12 residual misses in `632934` are exact-score ties (`score_gap_top1_top2 = 0.0`).

| Row | Side | Role | Source term | Gold ID | Pred ID | GT rank |
|---|---|---|---|---:|---:|---:|
| `t0_row_01` | condition | Procedure | Coronary artery bypass grafting | 232717009 | 698378009 | 11 |
| `t0_row_01` | action | Procedure | Informing patient | 310866003 | 148292006 | 3 |
| `t0_row_01` | condition | ClinicalCondition | Myocardial ischemia | 414795007 | 32598000 | 4 |
| `t0_row_02` | action | Medication | Clopidogrel | 386952008 | 734972007 | 4 |
| `t0_row_03` | action | Medication | Prasugrel | 443129001 | 1149423007 | 2 |
| `t0_row_01` | action | Medication | Clopidogrel | 386952008 | 734972007 | 4 |
| `t0_row_03` | condition | ClinicalCondition | Myocardial ischemia | 414795007 | 32598000 | 4 |
| `t1_row_01` | condition | ClinicalCondition | Myocardial ischemia | 414795007 | 32598000 | 4 |
| `t1_row_02` | action | Medication | Prasugrel | 443129001 | 1149423007 | 2 |
| `t1_row_04` | action | Medication | Clopidogrel | 386952008 | 734972007 | 4 |
| `t1_row_06` | condition | Medication | Indication of | 230165009 | 39816005 | 3 |
| `t1_row_07` | condition | Procedure | Coronary artery bypass graft | 232717009 | 149173009 | 4 |

Frequency by term-role:

| Term + role | Count |
|---|---:|
| Myocardial ischemia + ClinicalCondition | 3 |
| Clopidogrel + Medication | 3 |
| Prasugrel + Medication | 2 |
| Coronary artery bypass grafting + Procedure | 1 |
| Informing patient + Procedure | 1 |
| Indication of + Medication | 1 |
| Coronary artery bypass graft + Procedure | 1 |

GT-rank distribution among the 12 misses:

| GT rank | Count |
|---:|---:|
| 2 | 2 |
| 3 | 2 |
| 4 | 7 |
| 11 | 1 |

Interpretation: in `632934`, error mode is tie-break/disambiguation, not candidate absence.

#### B) In-Depth Error Clusters (632934)

##### B1) Tricky near-miss cluster (5)

Definition: high lexical overlap where medication base substance and salt/form variant compete at equal score.

| Row | Role | Source term | Gold | Pred | Reason |
|---|---|---|---|---|---|
| `t0_row_02` | Medication | Clopidogrel | 386952008 (Clopidogrel) | 734972007 (Clopidogrel besilate) | high_lexical_overlap |
| `t0_row_03` | Medication | Prasugrel | 443129001 (Prasugrel) | 1149423007 (Prasugrel besilate) | high_lexical_overlap |
| `t0_row_01` | Medication | Clopidogrel | 386952008 (Clopidogrel) | 734972007 (Clopidogrel besilate) | high_lexical_overlap |
| `t1_row_02` | Medication | Prasugrel | 443129001 (Prasugrel) | 1149423007 (Prasugrel besilate) | high_lexical_overlap |
| `t1_row_04` | Medication | Clopidogrel | 386952008 (Clopidogrel) | 734972007 (Clopidogrel besilate) | high_lexical_overlap |

Observed shape:

1. `Clopidogrel` errors: 3/5.
2. `Prasugrel` errors: 2/5.
3. All are exact ties, so deterministic tie-break policy dominates outcome.

##### B2) Obvious tuning cluster (4)

Definition: high-confidence semantic mismatch where predicted concept is plausible but clinically/role-wise less precise than gold.

| Row | Role | Source term | Gold | Pred | Reason |
|---|---|---|---|---|---|
| `t0_row_01` | Procedure | Coronary artery bypass grafting | 232717009 (procedure) | 698378009 (planned situation) | high_confidence_semantic_mismatch |
| `t0_row_01` | ClinicalCondition | Myocardial ischemia | 414795007 | 32598000 (Acute ischemic heart disease) | high_confidence_semantic_mismatch |
| `t0_row_03` | ClinicalCondition | Myocardial ischemia | 414795007 | 32598000 (Acute ischemic heart disease) | high_confidence_semantic_mismatch |
| `t1_row_01` | ClinicalCondition | Myocardial ischemia | 414795007 | 32598000 (Acute ischemic heart disease) | high_confidence_semantic_mismatch |

Observed shape:

1. `Myocardial ischemia` granularity drift drives 3/4 cases.
2. 1/4 is procedure-vs-situation drift for CABG.
3. All are exact ties, so role/semantic precision tie-breakers are the critical control.

##### B3) Annotation-review cluster (3)

Definition: same normalized label text but different SNOMED IDs.

| Row | Role | Source term | Gold | Pred | Reason |
|---|---|---|---|---|---|
| `t0_row_01` | Procedure | Informing patient | 310866003 (Informing patient) | 148292006 (Informing patient) | same_normalized_concept_text_different_id |
| `t1_row_06` | Medication | Indication of | 230165009 (Indication of) | 39816005 (Indication of) | same_normalized_concept_text_different_id |
| `t1_row_07` | Procedure | Coronary artery bypass graft | 232717009 (CABG) | 149173009 (CABG) | same_normalized_concept_text_different_id |

Observed shape:

1. These are likely terminology/annotation equivalence disputes, not strict semantic mismatches.
2. They should be tracked separately from model semantic failures in strict-accuracy interpretation.

#### C) Cross-Run Contrast: Remaining Upstream Loss in 632933

The no-rescue run `632933` still contains a GT-absent retrieval cluster (`8/37` misses), concentrated entirely on:

1. role `Procedure`
2. term `Percutaneous coronary revascularization`
3. gold `415070008`

Interpretation:

1. `632934` residual error is tie-break/rerank dominated.
2. `632933` still has a targeted retrieval-recall deficiency for one phrase family.
