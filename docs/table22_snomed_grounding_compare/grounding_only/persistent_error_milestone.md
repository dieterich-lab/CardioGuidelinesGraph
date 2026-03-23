# Table22 Vector Grounding Persistent Error Milestone

Runs analyzed: 627166, 627177, 627386

Criterion: term-role pairs that missed in at least 2 analyzed runs.

## Latest Run Gate
- Latest run 627386 accuracy: 0.571429 (48/84)
- 0.60 gate: FAILED

## Top Persistent Error Terms

| Rank | Term | Role | Runs Missed | Misses (analyzed runs) | Typical Wrong Prediction IDs | Example Rows |
|---:|---|---|---|---:|---|---|
| 1 | Intracoronary pressure guide wire | Procedure | 627166, 627177, 627386 | 9 | <empty>, 431558000 | t0_row_17, t0_row_18, t0_row_19 |
| 2 | Percutaneous coronary revascularization | Procedure | 627166, 627177, 627386 | 9 | 713617008 | t0_row_01, t0_row_11, t0_row_16 |
| 3 | Using decision making strategies | Procedure | 627166, 627177, 627386 | 9 | 133920001, 228552002, <empty> | t0_row_01, t0_row_04, t0_row_13 |
| 4 | Preferences | Procedure | 627166, 627177, 627386 | 6 | 223486007 | t0_row_04, t1_row_01 |
| 5 | High risk | ClinicalCondition | 627166, 627177, 627386 | 3 | 455201601000132100 | t0_row_11 |
| 6 | Inoperable | ClinicalCondition | 627166, 627177, 627386 | 3 | <empty> | t0_row_11 |
| 7 | Lesion | ClinicalCondition | 627166, 627177, 627386 | 3 | 300513000 | t0_row_16 |
| 8 | Medical therapy | ClinicalCondition | 627166, 627177, 627386 | 3 | 425914008 | t0_row_12 |
| 9 | Myocardial revascularization | ClinicalCondition | 627166, 627177, 627386 | 3 | 57809008 | t0_row_13 |
| 10 | Specialist multidisciplinary team | ClinicalCondition | 627166, 627177, 627386 | 3 | <empty>, 268528005 | t0_row_05 |
| 11 | Assessment score | Procedure | 627166, 627177, 627386 | 3 | 1003700002 | t0_row_15 |
| 12 | Coronary artery structure | Procedure | 627166, 627177, 627386 | 3 | 294002 | t1_row_01 |
| 13 | Decision making | Procedure | 627166, 627177, 627386 | 3 | 133920001 | t0_row_09 |
| 14 | General characteristic of patient | Procedure | 627166, 627177, 627386 | 3 | 7922000 | t1_row_01 |
| 15 | Health literacy | Procedure | 627166, 627177, 627386 | 3 | 431531000124101 | t0_row_04 |

## Role-Level Accuracy Trend

| Run | ClinicalCondition | ClinicalParameter | Procedure | Overall |
|---|---:|---:|---:|---:|
| 627166 | 0.724 | 1.000 | 0.551 | 0.643 |
| 627177 | 0.793 | 1.000 | 0.408 | 0.583 |
| 627386 | 0.517 | 1.000 | 0.551 | 0.571 |

## 627386 Outcome Summary (with miss concept logging)
- Overall: 0.571429 (48/84), improved vs latest non-vector baseline (0.547619) by +0.023810, but below 0.60 gate.
- Main success vs run 627177: all 7 prior `Myocardial revascularization` misses were recovered (improved 7, regressed 8, net -1).
- Main regression vs run 627177: drop is concentrated in `ClinicalCondition` (0.793 -> 0.517), while `Procedure` recovered to 0.551 (equal to run 627166).
- Main regression vs run 627166: 6 additional misses, all in `ClinicalCondition` distinctions (multi-vessel disease / stenosis / proximal LAD atherosclerosis family).

## Miss-Concept Severity Snapshot (from 627386 MISS lines)
- Clearly wrong/high-priority tuning targets (semantic mismatch):
	- `Multi vessel coronary artery disease` -> `Aneurysm of coronary vessels` (4x)
	- `Triple vessel disease of the heart` -> `Glucocorticoid deficiency with achalasia` (1x)
	- `Lesion` -> `Lesion of penis` (1x)
	- `Procedure` -> `Sano procedure` (1x)
- Tricky near-miss / granularity mismatches (likely close but not exact):
	- `Stenosis of left coronary artery main stem` -> `Stenosis of ostium of left main coronary artery` (2x)
	- `Atherosclerosis of proximal ... LAD` -> `Atherosclerosis of ... LAD` (1x)
	- `Percutaneous coronary revascularization` -> specific CTO fluoroscopic variant (3x)
- Potential annotation/ontology-type tension (role vs SNOMED semantic tag):
	- `Using decision making strategies` gold is `(finding)` while role is `Procedure` (3x unresolved to empty)
	- `Preferences` gold is `(qualifier value)` vs predicted procedural discussion (2x)
	- `Health literacy` gold is `(observable entity)` vs predicted assessment procedure (1x)
	- `Intracoronary pressure guide wire` gold is `(physical object)` under `Procedure` role (3x unresolved to empty)

## Interpretation
- The new logging confirms this is not a single-point failure; we currently have two error classes:
	1) true semantic confusions that need grounding tuning, and
	2) role/semantic-tag tensions where gold labels may be difficult to satisfy with current role constraints.
- Next tuning should prioritize the clearly wrong confusions first (high severity), then decide explicit policy for role/tag tension cases (strict vs permissive matching).

## Top 10 Tune-Now Rules (execution checklist)
1. Block `Multi vessel coronary artery disease` -> `Aneurysm of coronary vessels` (hard negative pair).
2. Block catastrophic off-domain disease confusions (`Triple vessel disease` -> unrelated endocrine/achalasia disorder).
3. Add lexical guard for anatomical specificity (`proximal`, `main stem`, `left main`) to avoid over-general disease picks.
4. Add procedure-vs-finding disambiguation rule for `Using decision making strategies` and related variants.
5. Penalize genital/irrelevant-organ candidates for underspecified terms like `Lesion` when coronary context is present.
6. Add explicit candidate boost for `Intracoronary pressure guide wire` as physical-object concept in cardiology context.
7. Add ambiguity abstain fallback for generic `Procedure` term to avoid random specific procedure IDs.
8. Tighten qualifier/observable vs procedure crossover penalties (`Preferences`, `Health literacy`, `Assessment score`).
9. Add near-duplicate preference logic: keep closer parent/child clinical concept when only one anatomic qualifier differs.
10. Re-run stability gate twice per setting and reject configs with >0.01 variance in overall accuracy.

## Triage Snapshot (627386)
- From `scripts/triage_grounding_misses.py` (without taxonomy distance): 36 misses total.
- Bucket counts: 32 `obvious_tune`, 4 `tricky_near_miss`, 0 automatic `annotation_review` (manual review still needed for role/tag tension cases).

## Why Role Constraints Create Tension (brief)
- Current grounding flow constrains candidates by role (e.g., `Procedure` path), but some gold labels are not procedure-tagged in SNOMED (`finding`, `qualifier value`, `observable entity`, `physical object`).
- This mismatch can force either:
  - wrong in-role procedural predictions, or
  - abstentions (`<empty>`) when valid gold concepts are filtered out by role.
- Net effect: stricter role filtering improves some precision but can suppress true gold IDs when annotation role and ontology semantic tag diverge.
- Practical fix direction: introduce a controlled “cross-tag allowance” for known tension terms (or role-aware soft penalties instead of hard exclusion).
