# SNOMED Vector Grounding Tracker (Scientific vs Production)

Last updated: 2026-04-17

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
  - `docs/reference/grounding/current_snomed_mappings_scientific_track.md`

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
- The scientific comparison reference remains run `630837` and is mirrored in `docs/reference/grounding/current_snomed_mappings_scientific_track.md`.

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
- `docs/reference/grounding/current_snomed_mappings_scientific_track.md`
- `docs/reference/grounding/snomed_eval.csv`
- `docs/reference/grounding/snomed_eval.xlsx`

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

2. Lower vector re-rank dominance so lexical/domain evidence wins more often.
  - `CARDIO_GRAPH_GROUNDING_VECTOR_RERANK_WEIGHT`: `0.03 -> 0.015`
  - `CARDIO_GRAPH_GROUNDING_VECTOR_BONUS_CAP`: `0.05 -> 0.03`

3. Tighten ambiguity fallback for near ties.
  - `CARDIO_GRAPH_GROUNDING_AMBIGUITY_BACKOFF_MAX_DROP`: `0.30 -> 0.20`
  - `CARDIO_GRAPH_GROUNDING_AMBIGUITY_BACKOFF_MIN_SCORE`: keep `0.45`
  - `CARDIO_GRAPH_GROUNDING_AMBIGUITY_MIN_COVERAGE`: `0.55 -> 0.60`

4. Turn on semantic-tag filtering for scientific evaluations.
  - Use `--semantic-tag-filter` in the grounding entrypoint (builder supports this).
  - Expected effect: fewer disorder/finding vs procedure crossovers.

### B) Production Track (Rescue-Enabled): convert high-confidence misses into deterministic fixes
Goal: maximize deployment correctness while keeping the scientific track unchanged.

1. Keep dual-map policy:
  - Scientific/validation production: `grounding_rescue_map_train_only.yaml`
  - Operational production: `grounding_rescue_map.yaml`

2. Add high-frequency production overrides to full map (not scientific map):
  - `Aspirin` (Medication) -> `387458008`
  - `Percutaneous coronary revascularization` (Procedure) -> `415070008`
  - `Myocardial infarction` (ClinicalCondition) -> `22298006`
  - `Old myocardial infarction` (ClinicalCondition) -> `1755008`
  - `Myocardial revascularization` (Procedure) -> `275227003`
  - `Use of anticoagulation` (ClinicalCondition) -> `260678004`
  - `Indication of` (ClinicalCondition) -> `230165009`
  - `Drug therapy with explicit context` (Medication) -> `1290126002`

3. Keep rescue entries role-scoped (no wildcard) to avoid collateral corrections.

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
