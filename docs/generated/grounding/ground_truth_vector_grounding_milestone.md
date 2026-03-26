# Ground Truth Vector Grounding Persistent Error Milestone

Runs analyzed: 628305, 628306, 628328, 628332, 628342

Criterion: term-role pairs that missed in at least 4 analyzed runs.

## Latest Run Gate
- Latest run 628342 accuracy: 0.517391 (119/230)
- 0.60 gate: FAILED
- Best run in window: 628328 (0.630952, 53/84)
- Best GT3 run in window: 628342 (0.517391, 119/230)

## State Of The Art

- Current SOTA (GT3): run 628342 with accuracy 0.517391 (119/230).
- Latest run under review: 628342 (0.517391, 119/230).
- Delta latest vs SOTA (accuracy): +0.000000.

## Run Leaderboard (Window)

| Rank | Run | Overall | Hits/Total | Procedure | ClinicalCondition | Medication |
|---:|---|---:|---|---:|---:|---:|
| 1 | 628328 | 0.631 | 53/84 | 0.510 | 0.759 | n/a |
| 2 | 628305 | 0.619 | 52/84 | 0.490 | 0.759 | n/a |
| 3 | 628332 | 0.560 | 47/84 | 0.490 | 0.586 | n/a |
| 4 | 628306 | 0.536 | 45/84 | 0.490 | 0.517 | n/a |
| 5 | 628342 | 0.517 | 119/230 | 0.319 | 0.542 | 0.659 |

## Latest Knob Snapshot

- `embedding_model` = `Qwen3embed`
- `embedding_node` = `local`
- `embedding_port` = `11776`
- `model` = `Qwen3next`
- `node` = `g3`
- `port` = `11433`
- `vector_index` = `snomed_term_embeddings_4096`
- `vector_uri` = `bolt://neo4j-dev3.internal:7687`
- `vector_user` = `neo4j`

## Latest Variation vs Previous Run

| Key | Previous | Latest |
|---|---|---|
| embedding_port | 11766 | 11776 |

## Latest Label-Confusion Highlights

| Rank | Role | Gold ID | Pred ID | Count | Example Term Pair | Example Rows |
|---:|---|---|---|---:|---|---|
| 1 | Procedure | 415070008 | 713617008 | 17 | Percutaneous transluminal coronary intervention using imaging guidance with contrast (procedure) -> Percutaneous transluminal revascularization of chronic total occlusion of coronary artery using fluoroscopic guidance with contrast (procedure) | t0_row_01, t0_row_11, t0_row_16 |
| 2 | ClinicalCondition | 260678004 | 440678006 | 13 | Use of anticoagulation (attribute) -> Seen in hospital anticoagulation clinic (finding) | t1_row_01, t1_row_02, t1_row_03 |
| 3 | ClinicalCondition | 230165009 | 1363183004 | 13 | Indication of (contextual qualifier) (qualifier value) -> Pain behavior (finding) | t1_row_01, t1_row_02, t1_row_03 |
| 4 | Medication | 1290126002 | <empty> | 9 | Drug therapy with explicit context (situation) ->  | t0_row_02, t0_row_03, t0_row_04 |
| 5 | Procedure | 275227003 | 64432007 | 8 | Myocardial revascularization (procedure) -> Radioisotope myocardial imaging procedure (procedure) | t0_row_06, t0_row_07, t0_row_08 |
| 6 | ClinicalCondition | 414795007 | 164862008 | 6 | Myocardial ischemia (disorder) -> Electrocardiogram: no myocardial ischemia (finding) | t0_row_01, t0_row_05, t0_row_06 |
| 7 | ClinicalCondition | 371803003 | 50570003 | 4 | Multi vessel coronary artery disease (disorder) -> Aneurysm of coronary vessels (disorder) | t0_row_10, t0_row_11, t0_row_15 |
| 8 | Procedure | 415806002 | 12121000202107 | 3 | Using decision making strategies (finding) -> Evaluation of decision-making capacity (procedure) | t0_row_01, t0_row_04, t0_row_13 |
| 9 | Procedure | 371789009 | 431558000 | 3 | Intracoronary pressure guide wire (physical object) -> Insertion of cardiac pressure wire using fluoroscopic guidance (procedure) | t0_row_17, t0_row_18, t0_row_19 |
| 10 | ClinicalCondition | 1755008 | 164867002 | 3 | Old myocardial infarction (disorder) -> Electrocardiographic old myocardial infarction (finding) | t0_row_01, t0_row_02, t0_row_04 |
| 11 | Procedure | 225773000 | 223486007 | 2 | Preferences (qualifier value) -> Discussion about preferences (procedure) | t0_row_04, t1_row_01 |
| 12 | Procedure | 232717009 | 232719007 | 2 | Coronary artery bypass grafting (procedure) -> Coronary artery bypass graft x 1 (procedure) | t0_row_10, t0_row_14 |

## Top Persistent Error Terms

| Rank | Term | Role | Runs Missed | Misses (analyzed runs) | Typical Wrong Prediction IDs | Example Rows |
|---:|---|---|---|---:|---|---|
| 1 | Percutaneous coronary revascularization | Procedure | 628305, 628306, 628328, 628332, 628342 | 29 | 713617008 | t0_row_01, t0_row_11, t0_row_16 |
| 2 | Intracoronary pressure guide wire | Procedure | 628305, 628306, 628328, 628332, 628342 | 15 | 431558000, 53178003 | t0_row_17, t0_row_18, t0_row_19 |
| 3 | Using decision making strategies | Procedure | 628305, 628306, 628328, 628332, 628342 | 15 | 133920001, 228552002, 12121000202107 | t0_row_01, t0_row_04, t0_row_13 |
| 4 | Coronary artery bypass grafting | Procedure | 628305, 628306, 628328, 628332, 628342 | 10 | 868227005, 232719007 | t0_row_10, t0_row_14 |
| 5 | Preferences | Procedure | 628305, 628306, 628328, 628332, 628342 | 10 | 223486007, 1156333005 | t0_row_04, t1_row_01 |
| 6 | High risk | ClinicalCondition | 628305, 628306, 628328, 628332, 628342 | 5 | 161640005 | t0_row_11 |
| 7 | Inoperable | ClinicalCondition | 628305, 628306, 628328, 628332, 628342 | 5 | <empty> | t0_row_11 |
| 8 | Lesion | ClinicalCondition | 628305, 628306, 628328, 628332, 628342 | 5 | 300577008 | t0_row_16 |
| 9 | Medical therapy | ClinicalCondition | 628305, 628306, 628328, 628332, 628342 | 5 | 425914008 | t0_row_12 |
| 10 | Myocardial revascularization | ClinicalCondition | 628305, 628306, 628328, 628332, 628342 | 5 | 57809008 | t0_row_13 |
| 11 | Assessment score | Procedure | 628305, 628306, 628328, 628332, 628342 | 5 | 1003700002 | t0_row_15 |
| 12 | Coronary artery structure | Procedure | 628305, 628306, 628328, 628332, 628342 | 5 | 294002, 31413008 | t1_row_01 |
| 13 | General characteristic of patient | Procedure | 628305, 628306, 628328, 628332, 628342 | 5 | 7922000, 162673000 | t1_row_01 |
| 14 | Health literacy | Procedure | 628305, 628306, 628328, 628332, 628342 | 5 | 431531000124101 | t0_row_04 |
| 15 | Left ventricular ejection fraction | Procedure | 628305, 628306, 628328, 628332, 628342 | 5 | 46258004 | t1_row_01 |

## Role-Level Accuracy Trend

| Run | ClinicalCondition | ClinicalParameter | Medication | Procedure | Qualifier Value | string | Overall |
|---|---:|---:|---:|---:|---:|---:|---:|
| 628305 | 0.759 | 1.000 | n/a | 0.490 | n/a | n/a | 0.619 |
| 628306 | 0.517 | 1.000 | n/a | 0.490 | n/a | n/a | 0.536 |
| 628328 | 0.759 | 1.000 | n/a | 0.510 | n/a | n/a | 0.631 |
| 628332 | 0.586 | 1.000 | n/a | 0.490 | n/a | n/a | 0.560 |
| 628342 | 0.542 | 1.000 | 0.659 | 0.319 | 1.000 | 1.000 | 0.517 |
