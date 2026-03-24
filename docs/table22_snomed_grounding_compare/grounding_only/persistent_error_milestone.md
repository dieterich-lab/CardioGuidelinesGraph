# Table22 Vector Grounding Persistent Error Milestone

Runs analyzed: 627575, 627576, 627880

Criterion: term-role pairs that missed in at least 2 analyzed runs.

## Latest Run Gate
- Latest run 627880 accuracy: 0.666667 (56/84)
- 0.60 gate: PASSED
- 0.65 gate: PASSED

## Top Persistent Error Terms

| Rank | Term | Role | Runs Missed | Misses (analyzed runs) | Typical Wrong Prediction IDs | Example Rows |
|---:|---|---|---|---:|---|---|
| 1 | Intracoronary pressure guide wire | Procedure | 627575, 627576, 627880 | 9 | <empty>, 431558000 | t0_row_17, t0_row_18, t0_row_19 |
| 2 | Percutaneous coronary revascularization | Procedure | 627575, 627576, 627880 | 9 | 713617008 | t0_row_01, t0_row_11, t0_row_16 |
| 3 | Using decision making strategies | Procedure | 627575, 627576, 627880 | 9 | <empty> | t0_row_01, t0_row_04, t0_row_13 |
| 4 | Preferences | Procedure | 627575, 627576, 627880 | 6 | 223486007 | t0_row_04, t1_row_01 |
| 5 | High risk | ClinicalCondition | 627575, 627576, 627880 | 3 | 455201601000132100 | t0_row_11 |
| 6 | Inoperable | ClinicalCondition | 627575, 627576, 627880 | 3 | <empty> | t0_row_11 |
| 7 | Lesion | ClinicalCondition | 627575, 627576, 627880 | 3 | 300513000 | t0_row_16 |
| 8 | Medical therapy | ClinicalCondition | 627575, 627576, 627880 | 3 | 425914008 | t0_row_12 |
| 9 | Myocardial revascularization | ClinicalCondition | 627575, 627576, 627880 | 3 | 57809008 | t0_row_13 |
| 10 | Specialist multidisciplinary team | ClinicalCondition | 627575, 627576, 627880 | 3 | <empty>, 268528005 | t0_row_05 |
| 11 | Assessment score | Procedure | 627575, 627576, 627880 | 3 | 1003700002 | t0_row_15 |
| 12 | Coronary artery structure | Procedure | 627575, 627576, 627880 | 3 | 294002, 24088005 | t1_row_01 |
| 13 | Decision making | Procedure | 627575, 627576, 627880 | 3 | 133920001 | t0_row_09 |
| 14 | General characteristic of patient | Procedure | 627575, 627576, 627880 | 3 | 162673000, 7922000 | t1_row_01 |
| 15 | Health literacy | Procedure | 627575, 627576, 627880 | 3 | 431531000124101 | t0_row_04 |

## Role-Level Accuracy Trend

| Run | ClinicalCondition | ClinicalParameter | Procedure | Overall |
|---|---:|---:|---:|---:|
| 627575 | 0.724 | 1.000 | 0.551 | 0.643 |
| 627576 | 0.793 | 1.000 | 0.551 | 0.667 |
| 627880 | 0.793 | 1.000 | 0.551 | 0.667 |

## Winning Default Configuration (adopted)
- Best run: 627576 (`softC`), accuracy 0.666667 (56/84).
- Default role-constraint settings now set to this winning profile in SLURM wrappers:
	- `CARDIO_GRAPH_GROUNDING_ROLE_SOFT_CONSTRAINTS=true`
	- `CARDIO_GRAPH_GROUNDING_ROLE_MISMATCH_PENALTY=0.05`
	- `CARDIO_GRAPH_GROUNDING_ROLE_TENSION_PENALTY=0.02`

## Remaining False Mappings in Latest Run (627880)
- Remaining misses: 28/84 (5 no-prediction, 23 wrong-prediction).
- Highest-frequency unresolved pairs:
	- `Percutaneous coronary revascularization` (3x): 415070008 -> 713617008 (procedure-vs-procedure near variant).
	- `Using decision making strategies` (3x): 415806002 -> `<empty>` (finding under procedure role tension).
	- `Intracoronary pressure guide wire` (3x): 371789009 -> `<empty>` or 431558000 (physical-object/procedure role tension).
	- `Preferences` (2x): 225773000 -> 223486007 (qualifier value -> procedure).

## Generalized Failure Analysis (627880)
- Misses are concentrated in `Procedure` role (22/28 = 78.6%), indicating role-conditioning still dominates retrieval behavior.
- Error-mode split:
	- Cross-semantic-tag drift: 19/28 (67.9%), mostly `observable entity -> procedure`, `physical object -> procedure`, and `qualifier value -> procedure`.
	- Abstentions (`<empty>`): 5/28 (17.9%), mainly where gold is `finding` or `qualifier value` under role pressure.
	- Same-tag wrong concept: 4/28 (14.3%), mainly near-neighbor procedure variants.
- Plateau confirmed: run 627880 is identical to 627576 (same total hits and per-role accuracy), so current settings improved stability but not residual error classes.

## Room for Further Improvements (generalized, no hard-coded mappings)
1. Replace fixed role penalties with a learned calibration layer from validation data (optimize tag/role compatibility weights instead of manual constants).
2. Add confidence calibration + abstention backoff: when top candidates are close, prefer a tag-compatible fallback over empty prediction.
3. Introduce two-stage reranking: lexical/vector retrieval first, then semantic-tag and role-consistency rerank (same model, no term-specific rules).
4. Expand candidate diversity before rerank (reduce candidate collapse to procedure-heavy neighbors for action phrases with non-procedure gold tags).
5. Evaluate by error class in CI gate (cross-tag drift, abstain, same-tag-near-miss) so optimization targets are generalized behaviors, not term memorization.
