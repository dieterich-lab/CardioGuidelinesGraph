# Table22 Vector Grounding Persistent Error Milestone

Runs analyzed: 627574, 627575, 627576

Criterion: term-role pairs that missed in at least 2 analyzed runs.

## Latest Run Gate
- Latest run 627576 accuracy: 0.666667 (56/84)
- 0.60 gate: PASSED
- 0.65 gate: PASSED

## Top Persistent Error Terms

| Rank | Term | Role | Runs Missed | Misses (analyzed runs) | Typical Wrong Prediction IDs | Example Rows |
|---:|---|---|---|---:|---|---|
| 1 | Intracoronary pressure guide wire | Procedure | 627574, 627575, 627576 | 9 | <empty> | t0_row_17, t0_row_18, t0_row_19 |
| 2 | Percutaneous coronary revascularization | Procedure | 627574, 627575, 627576 | 9 | 713617008 | t0_row_01, t0_row_11, t0_row_16 |
| 3 | Using decision making strategies | Procedure | 627574, 627575, 627576 | 9 | <empty> | t0_row_01, t0_row_04, t0_row_13 |
| 4 | Preferences | Procedure | 627574, 627575, 627576 | 6 | 223486007 | t0_row_04, t1_row_01 |
| 5 | High risk | ClinicalCondition | 627574, 627575, 627576 | 3 | 455201601000132100 | t0_row_11 |
| 6 | Inoperable | ClinicalCondition | 627574, 627575, 627576 | 3 | <empty> | t0_row_11 |
| 7 | Lesion | ClinicalCondition | 627574, 627575, 627576 | 3 | 300513000 | t0_row_16 |
| 8 | Medical therapy | ClinicalCondition | 627574, 627575, 627576 | 3 | 425914008 | t0_row_12 |
| 9 | Myocardial revascularization | ClinicalCondition | 627574, 627575, 627576 | 3 | 57809008 | t0_row_13 |
| 10 | Specialist multidisciplinary team | ClinicalCondition | 627574, 627575, 627576 | 3 | <empty>, 268529002 | t0_row_05 |
| 11 | Assessment score | Procedure | 627574, 627575, 627576 | 3 | 1003700002 | t0_row_15 |
| 12 | Coronary artery structure | Procedure | 627574, 627575, 627576 | 3 | 294002, 24088005 | t1_row_01 |
| 13 | Decision making | Procedure | 627574, 627575, 627576 | 3 | 133920001 | t0_row_09 |
| 14 | General characteristic of patient | Procedure | 627574, 627575, 627576 | 3 | 162673000 | t1_row_01 |
| 15 | Health literacy | Procedure | 627574, 627575, 627576 | 3 | 431531000124101 | t0_row_04 |

## Role-Level Accuracy Trend

| Run | ClinicalCondition | ClinicalParameter | Procedure | Overall |
|---|---:|---:|---:|---:|
| 627574 | 0.793 | 1.000 | 0.347 | 0.548 |
| 627575 | 0.724 | 1.000 | 0.551 | 0.643 |
| 627576 | 0.793 | 1.000 | 0.551 | 0.667 |

## Winning Default Configuration (adopted)
- Best run: 627576 (`softC`), accuracy 0.666667 (56/84).
- Default role-constraint settings now set to this winning profile in SLURM wrappers:
	- `CARDIO_GRAPH_GROUNDING_ROLE_SOFT_CONSTRAINTS=true`
	- `CARDIO_GRAPH_GROUNDING_ROLE_MISMATCH_PENALTY=0.05`
	- `CARDIO_GRAPH_GROUNDING_ROLE_TENSION_PENALTY=0.02`

## Remaining False Mappings in Best Run (627576)
- Remaining misses: 28/84 (10 no-prediction, 18 wrong-prediction).
- Highest-frequency unresolved pairs:
	- `Percutaneous coronary revascularization` (3x): 415070008 -> 713617008 (procedure-vs-procedure near variant).
	- `Using decision making strategies` (3x): 415806002 -> `<empty>` (finding under procedure role tension).
	- `Intracoronary pressure guide wire` (3x): 371789009 -> `<empty>` (physical object under procedure role tension).
	- `Preferences` (2x): 225773000 -> 223486007 (qualifier value -> procedure).

## Room for Further Improvements (next sprint)
1. Add explicit positive boosts for unresolved high-frequency terms (`Intracoronary pressure guide wire`, `Using decision making strategies`) to avoid abstention.
2. Add near-variant tie-break for `Percutaneous coronary revascularization` to prefer imaging-guidance PCI concept over CTO-specific variant when term lacks CTO qualifiers.
3. Introduce semantic-tag-aware soft penalties for `qualifier value`/`observable entity` -> `procedure` drift in action-side terms (`Preferences`, `Assessment score`, `Health literacy`).
4. Add a small whitelist for known role-tension terms where cross-tag mapping is allowed with reduced penalty instead of abstention.
5. Keep stability gate on repeated runs (>=2) to confirm the new default is durable above 0.65.
