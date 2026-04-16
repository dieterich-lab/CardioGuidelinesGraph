# Ground Truth Vector Grounding Persistent Error Milestone

Runs analyzed: 630501, 630502

Criterion: term-role pairs that missed in at least 2 analyzed runs.

## Latest Run Gate
- Latest run 630502 accuracy: 0.793991 (185/233)
- 0.60 gate: PASSED
- Best run in window: 630501 (0.824034, 192/233)
- Best GT3 run in window: 630501 (0.824034, 192/233)

## State Of The Art

- Current SOTA (GT3): run 630501 with accuracy 0.824034 (192/233).
- Latest run under review: 630502 (0.793991, 185/233).
- Delta latest vs SOTA (accuracy): -0.030043.

## Run Leaderboard (Window)

| Rank | Run | Overall | Hits/Total | Procedure | ClinicalCondition | Medication |
|---:|---|---:|---|---:|---:|---:|
| 1 | 630501 | 0.824 | 192/233 | 0.681 | 0.855 | 0.932 |
| 2 | 630502 | 0.794 | 185/233 | 0.565 | 0.864 | 0.932 |

## Latest Knob Snapshot

- `embedding_model` = `Qwen3embed`
- `embedding_node` = `local`
- `embedding_port` = `11936`
- `knob.ambiguity_confidence_backoff_enabled` = `true`
- `knob.ambiguity_lexical_force_pick` = `0.90`
- `knob.backoff_max_drop` = `0.30`
- `knob.backoff_min_score` = `0.45`
- `knob.embedding_model` = `Qwen3embed`
- `knob.embedding_url` = `http://127.0.0.1:11936`
- `knob.hard_negative_manifest` = ``
- `knob.hard_negative_penalty` = `0.0`
- `knob.role_mismatch_penalty` = `0.05`
- `knob.role_semantic_crossclass_penalty` = `0.02`
- `knob.role_semantic_mismatch_penalty` = `0.06`
- `knob.role_soft_constraints` = `true`
- `knob.role_tension_penalty` = `0.02`
- `knob.vector_context_allowed_roles` = `Procedure,Medication`
- `knob.vector_context_append_term` = `true`
- `knob.vector_context_enabled` = `true`
- `knob.vector_context_max_tokens` = `8`
- `model` = `Qwen3next`
- `node` = `g3`
- `port` = `11433`
- `vector_index` = `snomed_term_embeddings_4096`
- `vector_uri` = `bolt://neo4j-dev3.internal:7687`
- `vector_user` = `neo4j`

## Latest Variation vs Previous Run

| Key | Previous | Latest |
|---|---|---|
| embedding_port | 11935 | 11936 |
| knob.embedding_url | http://127.0.0.1:11935 | http://127.0.0.1:11936 |

## Latest Label-Confusion Highlights

| Rank | Role | Gold ID | Pred ID | Count | Example Term Pair | Example Rows |
|---:|---|---|---|---:|---|---|
| 1 | Procedure | 275227003 | 64432007 | 8 | Myocardial revascularization (procedure) -> Radioisotope myocardial imaging procedure (procedure) | t0_row_06, t0_row_07, t0_row_08 |
| 2 | ClinicalCondition | 414795007 | 164862008 | 6 | Myocardial ischemia (disorder) -> Electrocardiogram: no myocardial ischemia (finding) | t0_row_01, t0_row_05, t0_row_06 |
| 3 | Procedure | 232717009 | 232719007 | 3 | Coronary artery bypass grafting (procedure) -> Coronary artery bypass graft x 1 (procedure) | t0_row_01, t0_row_10, t0_row_14 |
| 4 | Procedure | 415806002 | 133920001 | 3 | Using decision making strategies (finding) -> Decision making encouragement (procedure) | t0_row_01, t0_row_04, t0_row_13 |
| 5 | Procedure | 371789009 | 431558000 | 3 | Intracoronary pressure guide wire (physical object) -> Insertion of cardiac pressure wire using fluoroscopic guidance (procedure) | t0_row_17, t0_row_18, t0_row_19 |
| 6 | Procedure | 225773000 | 223486007 | 2 | Preferences (qualifier value) -> Discussion about preferences (procedure) | t0_row_04, t1_row_01 |
| 7 | Procedure | 314705003 | 55053003 | 1 | Treatment plan given (finding) -> Prescription of therapeutic regimen (procedure) | t0_row_03 |
| 8 | Procedure | 870552008 | 431531000124101 | 1 | Health literacy (observable entity) -> Health literacy assessment (procedure) | t0_row_04 |
| 9 | Procedure | 1254714002 | 78823007 | 1 | Requires culturally responsive service to support health literacy (finding) -> Life support procedure (procedure) | t0_row_04 |
| 10 | ClinicalCondition | 723509005 | 161640005 | 1 | High risk (qualifier value) -> At high risk for heart disease (finding) | t0_row_11 |
| 11 | ClinicalCondition | 74778001 | <empty> | 1 | Inoperable (qualifier value) ->  | t0_row_11 |
| 12 | ClinicalCondition | 243121000 | 425914008 | 1 | Medical therapy (procedure) -> Adjustment reaction to medical therapy (disorder) | t0_row_12 |

## Top Persistent Error Terms

| Rank | Term | Role | Runs Missed | Misses (analyzed runs) | Typical Wrong Prediction IDs | Example Rows |
|---:|---|---|---|---:|---|---|
| 1 | Coronary artery bypass grafting | Procedure | 630501, 630502 | 6 | 232719007 | t0_row_01, t0_row_10, t0_row_14 |
| 2 | Intracoronary pressure guide wire | Procedure | 630501, 630502 | 6 | 431558000 | t0_row_17, t0_row_18, t0_row_19 |
| 3 | Using decision making strategies | Procedure | 630501, 630502 | 6 | 133920001 | t0_row_01, t0_row_04, t0_row_13 |
| 4 | Preferences | Procedure | 630501, 630502 | 4 | 1156333005, 223486007 | t0_row_04, t1_row_01 |
| 5 | Acute coronary syndrome | ClinicalCondition | 630501, 630502 | 2 | 413439005 | t0_row_06 |
| 6 | Coronary artery bypass grafting | ClinicalCondition | 630501, 630502 | 2 | 132091000119104 | t0_row_03 |
| 7 | Coronary artery structure | ClinicalCondition | 630501, 630502 | 2 | 53741008 | t1_row_09 |
| 8 | High risk | ClinicalCondition | 630501, 630502 | 2 | 161640005 | t0_row_11 |
| 9 | Inoperable | ClinicalCondition | 630501, 630502 | 2 | <empty> | t0_row_11 |
| 10 | Lesion | ClinicalCondition | 630501, 630502 | 2 | 7870007 | t0_row_16 |
| 11 | Medical therapy | ClinicalCondition | 630501, 630502 | 2 | 425914008 | t0_row_12 |
| 12 | Myocardial revascularization | ClinicalCondition | 630501, 630502 | 2 | 57809008 | t0_row_13 |
| 13 | Indication of | Medication | 630501, 630502 | 2 | <empty> | t1_row_12 |
| 14 | Oral | Medication | 630501, 630502 | 2 | 13790009 | t1_row_08 |
| 15 | Use of anticoagulation | Medication | 630501, 630502 | 2 | <empty> | t1_row_08 |

## Role-Level Accuracy Trend

| Run | ClinicalCondition | ClinicalParameter | Medication | Procedure | Qualifier Value | string | Overall |
|---|---:|---:|---:|---:|---:|---:|---:|
| 630501 | 0.855 | 1.000 | 0.932 | 0.681 | 1.000 | 1.000 | 0.824 |
| 630502 | 0.864 | 1.000 | 0.932 | 0.565 | 1.000 | 1.000 | 0.794 |
