# Table22 Vector Grounding Persistent Error Milestone

Runs analyzed: 626561, 626625, 627166

Criterion: term-role pairs that missed in at least 2 analyzed runs.

## Latest Run Gate
- Latest run 627166 accuracy: 0.642857 (54/84)
- 0.60 gate: PASSED

## Top Persistent Error Terms

| Rank | Term | Role | Runs Missed | Misses (analyzed runs) | Typical Wrong Prediction IDs | Example Rows |
|---:|---|---|---|---:|---|---|
| 1 | Intracoronary pressure guide wire | Procedure | 626561, 626625, 627166 | 9 | 431558000 | t0_row_17, t0_row_18, t0_row_19 |
| 2 | Using decision making strategies | Procedure | 626561, 626625, 627166 | 9 | 133920001 | t0_row_01, t0_row_04, t0_row_13 |
| 3 | Preferences | Procedure | 626561, 626625, 627166 | 6 | 223486007 | t0_row_04, t1_row_01 |
| 4 | High risk | ClinicalCondition | 626561, 626625, 627166 | 3 | 169948004, 47200007, 455201601000132100 | t0_row_11 |
| 5 | Inoperable | ClinicalCondition | 626561, 626625, 627166 | 3 | <empty> | t0_row_11 |
| 6 | Lesion | ClinicalCondition | 626561, 626625, 627166 | 3 | 300513000, 3548001 | t0_row_16 |
| 7 | Medical therapy | ClinicalCondition | 626561, 626625, 627166 | 3 | 425914008 | t0_row_12 |
| 8 | Myocardial revascularization | ClinicalCondition | 626561, 626625, 627166 | 3 | 22298006, 1155004, 57809008 | t0_row_13 |
| 9 | Specialist multidisciplinary team | ClinicalCondition | 626561, 626625, 627166 | 3 | 408556008, 185580007, 268528005 | t0_row_05 |
| 10 | Assessment score | Procedure | 626561, 626625, 627166 | 3 | 1003700002, 81375008 | t0_row_15 |
| 11 | Coronary artery structure | Procedure | 626561, 626625, 627166 | 3 | 294002, 31413008 | t1_row_01 |
| 12 | Decision making | Procedure | 626561, 626625, 627166 | 3 | 133920001 | t0_row_09 |
| 13 | General characteristic of patient | Procedure | 626561, 626625, 627166 | 3 | 162673000, 7922000 | t1_row_01 |
| 14 | Health literacy | Procedure | 626561, 626625, 627166 | 3 | 431531000124101, 430253004 | t0_row_04 |
| 15 | Left ventricular ejection fraction | Procedure | 626561, 626625, 627166 | 3 | 46258004 | t1_row_01 |

## Role-Level Accuracy Trend

| Run | ClinicalCondition | ClinicalParameter | Procedure | Overall |
|---|---:|---:|---:|---:|
| 626561 | 0.724 | 1.000 | 0.449 | 0.583 |
| 626625 | 0.759 | 1.000 | 0.306 | 0.512 |
| 627166 | 0.724 | 1.000 | 0.551 | 0.643 |
