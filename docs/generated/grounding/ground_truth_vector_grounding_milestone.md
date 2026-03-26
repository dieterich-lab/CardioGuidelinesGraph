# Ground Truth Vector Grounding Persistent Error Milestone

Runs analyzed: 628306, 628328, 628332

Criterion: term-role pairs that missed in at least 2 analyzed runs.

## Latest Run Gate
- Latest run 628332 accuracy: 0.559524 (47/84)
- 0.60 gate: FAILED

## Top Persistent Error Terms

| Rank | Term | Role | Runs Missed | Misses (analyzed runs) | Typical Wrong Prediction IDs | Example Rows |
|---:|---|---|---|---:|---|---|
| 1 | Intracoronary pressure guide wire | Procedure | 628306, 628328, 628332 | 9 | 431558000, 53178003 | t0_row_17, t0_row_18, t0_row_19 |
| 2 | Percutaneous coronary revascularization | Procedure | 628306, 628328, 628332 | 9 | 713617008 | t0_row_01, t0_row_11, t0_row_16 |
| 3 | Using decision making strategies | Procedure | 628306, 628328, 628332 | 9 | 133920001, 228552002 | t0_row_01, t0_row_04, t0_row_13 |
| 4 | Coronary artery bypass grafting | Procedure | 628306, 628328, 628332 | 6 | 868227005, 232719007 | t0_row_10, t0_row_14 |
| 5 | Preferences | Procedure | 628306, 628328, 628332 | 6 | 223486007 | t0_row_04, t1_row_01 |
| 6 | High risk | ClinicalCondition | 628306, 628328, 628332 | 3 | 161640005 | t0_row_11 |
| 7 | Inoperable | ClinicalCondition | 628306, 628328, 628332 | 3 | <empty> | t0_row_11 |
| 8 | Lesion | ClinicalCondition | 628306, 628328, 628332 | 3 | 300577008 | t0_row_16 |
| 9 | Medical therapy | ClinicalCondition | 628306, 628328, 628332 | 3 | 425914008 | t0_row_12 |
| 10 | Myocardial revascularization | ClinicalCondition | 628306, 628328, 628332 | 3 | 57809008 | t0_row_13 |
| 11 | Specialist multidisciplinary team | ClinicalCondition | 628306, 628328, 628332 | 3 | 268528005, 268529002 | t0_row_05 |
| 12 | Assessment score | Procedure | 628306, 628328, 628332 | 3 | 1003700002 | t0_row_15 |
| 13 | Coronary artery structure | Procedure | 628306, 628328, 628332 | 3 | 294002, 31413008 | t1_row_01 |
| 14 | Decision making | Procedure | 628306, 628328, 628332 | 3 | 133920001 | t0_row_09 |
| 15 | General characteristic of patient | Procedure | 628306, 628328, 628332 | 3 | 7922000, 162673000 | t1_row_01 |

## Role-Level Accuracy Trend

| Run | ClinicalCondition | ClinicalParameter | Procedure | Overall |
|---|---:|---:|---:|---:|
| 628306 | 0.517 | 1.000 | 0.490 | 0.536 |
| 628328 | 0.759 | 1.000 | 0.510 | 0.631 |
| 628332 | 0.586 | 1.000 | 0.490 | 0.560 |
