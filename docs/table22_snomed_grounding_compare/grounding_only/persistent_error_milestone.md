# Table22 Vector Grounding Persistent Error Milestone

Runs analyzed: 628305, 628306

Criterion: term-role pairs that missed in at least 2 analyzed runs.

## Latest Run Gate
- Latest run 628306 accuracy: 0.535714 (45/84)
- 0.60 gate: FAILED

## Top Persistent Error Terms

| Rank | Term | Role | Runs Missed | Misses (analyzed runs) | Typical Wrong Prediction IDs | Example Rows |
|---:|---|---|---|---:|---|---|
| 1 | Intracoronary pressure guide wire | Procedure | 628305, 628306 | 6 | 431558000 | t0_row_17, t0_row_18, t0_row_19 |
| 2 | Percutaneous coronary revascularization | Procedure | 628305, 628306 | 6 | 713617008 | t0_row_01, t0_row_11, t0_row_16 |
| 3 | Using decision making strategies | Procedure | 628305, 628306 | 6 | 133920001 | t0_row_01, t0_row_04, t0_row_13 |
| 4 | Coronary artery bypass grafting | Procedure | 628305, 628306 | 4 | 868227005 | t0_row_10, t0_row_14 |
| 5 | Preferences | Procedure | 628305, 628306 | 4 | 1156333005, 223486007 | t0_row_04, t1_row_01 |
| 6 | Atherosclerosis of proximal portion of anterior descending branch of left coronary artery | ClinicalCondition | 628305, 628306 | 2 | 1255265004, 1366498001 | t0_row_08 |
| 7 | High risk | ClinicalCondition | 628305, 628306 | 2 | 161640005 | t0_row_11 |
| 8 | Inoperable | ClinicalCondition | 628305, 628306 | 2 | <empty> | t0_row_11 |
| 9 | Lesion | ClinicalCondition | 628305, 628306 | 2 | 300577008 | t0_row_16 |
| 10 | Medical therapy | ClinicalCondition | 628305, 628306 | 2 | 425914008 | t0_row_12 |
| 11 | Myocardial revascularization | ClinicalCondition | 628305, 628306 | 2 | 57809008 | t0_row_13 |
| 12 | Specialist multidisciplinary team | ClinicalCondition | 628305, 628306 | 2 | 268528005, 268529002 | t0_row_05 |
| 13 | Assessment score | Procedure | 628305, 628306 | 2 | 1003700002 | t0_row_15 |
| 14 | Coronary artery bypass graft | Procedure | 628305, 628306 | 2 | 252427007, 3546002 | t0_row_01 |
| 15 | Coronary artery structure | Procedure | 628305, 628306 | 2 | 294002 | t1_row_01 |

## Role-Level Accuracy Trend

| Run | ClinicalCondition | ClinicalParameter | Procedure | Overall |
|---|---:|---:|---:|---:|
| 628305 | 0.759 | 1.000 | 0.490 | 0.619 |
| 628306 | 0.517 | 1.000 | 0.490 | 0.536 |
