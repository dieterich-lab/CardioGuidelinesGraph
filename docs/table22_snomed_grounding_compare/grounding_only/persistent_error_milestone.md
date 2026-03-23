# Table22 Vector Grounding Persistent Error Milestone

Runs analyzed: 626561, 626625, 627166, 627177

Criterion: term-role pairs that missed in at least 3 analyzed runs.

## Latest Run Gate
- Latest run 627177 accuracy: 0.583333 (49/84)
- 0.60 gate: FAILED

## Regression 627177 vs 627166
- Net loss: 7 hits (-0.06 overall) all from `Myocardial revascularization` (Procedure) flipping from SNOMED 275227003 to 70627009 across rows t0_row_06, t0_row_07, t0_row_08, t0_row_12, t0_row_18, t0_row_19, t1_row_01; no other regressions.
- Scores stay high (~0.91), but follow-up live checks on 2026-03-23 show 275227003 is present with embedding size 4096 and index `snomed_term_embeddings_4096` is ONLINE.
- Updated hypothesis: this looks like a transient retrieval-path/runtime effect (embedding service/model/runtime state), not a persistent missing-vector defect in the index.

## Live Diagnostic Update (2026-03-23)
- Index health check (dev3): `snomed_term_embeddings_4096` ONLINE; concept 275227003 (`Myocardial revascularisation`) exists and has embedding dim=4096.
- Live text->embedding->vector checks (Qwen3embed endpoint reachable):
	- Query `Myocardial revascularization`: rank1 = 275227003 (score 1.0000), 70627009 absent from top-25.
	- Query `Myocardial revascularisation`: rank1 = 275227003 (score ~1.0000), 70627009 absent from top-25.
	- Query `myocardial revascularization procedure`: rank1 = 275227003 (score 0.9675), 70627009 at rank7 (score 0.9314), so wrong concept does not outrank correct concept.
- Interpretation: current live retrieval does not reproduce the 627177 flip pattern; likely intermittent/non-deterministic behavior around runtime embedding path rather than durable index corruption.

## Immediate Follow-up
- Re-run the exact SLURM script (`slurm/run_table22_snomed_grounding_only_vector.sh`) and compare new predictions against 627177 and 627166 once output JSON is available.
- For each of the 7 previously regressed rows, log top-k candidates and scores during eval-time to capture runtime drift when/if it recurs.

## Improvement Plan (>0.60 to durable >0.65)
- Add deterministic eval tracing for known fragile terms (`Myocardial revascularization`, `Using decision making strategies`, `Preferences`, `Intracoronary pressure guide wire`) including top-k vector candidates and final rerank breakdown.
- Introduce targeted hard-negative constraints for revascularization vs resection confusion and decision-making synonym cluster ambiguity.
- Raise precision for high-risk Procedure terms by increasing discriminative-token penalties when candidates add off-target surgical qualifiers.
- Expand lexical normalization/alias handling for UK/US spellings and procedure suffix variants before reranking.
- Add a stability gate: run vector eval at least 2x per candidate setting and reject configs with high variance even when one run passes 0.60.

## Top Persistent Error Terms

| Rank | Term | Role | Runs Missed | Misses (analyzed runs) | Typical Wrong Prediction IDs | Example Rows |
|---:|---|---|---|---:|---|---|
| 1 | Intracoronary pressure guide wire | Procedure | 626561, 626625, 627166, 627177 | 12 | 431558000, <empty> | t0_row_17, t0_row_18, t0_row_19 |
| 2 | Using decision making strategies | Procedure | 626561, 626625, 627166, 627177 | 12 | 133920001, 228552002 | t0_row_01, t0_row_04, t0_row_13 |
| 3 | Preferences | Procedure | 626561, 626625, 627166, 627177 | 8 | 223486007 | t0_row_04, t1_row_01 |
| 4 | High risk | ClinicalCondition | 626561, 626625, 627166, 627177 | 4 | 455201601000132100, 169948004, 47200007 | t0_row_11 |
| 5 | Inoperable | ClinicalCondition | 626561, 626625, 627166, 627177 | 4 | <empty> | t0_row_11 |
| 6 | Lesion | ClinicalCondition | 626561, 626625, 627166, 627177 | 4 | 300513000, 3548001 | t0_row_16 |
| 7 | Medical therapy | ClinicalCondition | 626561, 626625, 627166, 627177 | 4 | 425914008 | t0_row_12 |
| 8 | Myocardial revascularization | ClinicalCondition | 626561, 626625, 627166, 627177 | 4 | 57809008, 22298006, 1155004 | t0_row_13 |
| 9 | Specialist multidisciplinary team | ClinicalCondition | 626561, 626625, 627166, 627177 | 4 | 408556008, 185580007, 268528005 | t0_row_05 |
| 10 | Assessment score | Procedure | 626561, 626625, 627166, 627177 | 4 | 1003700002, 81375008 | t0_row_15 |
| 11 | Coronary artery structure | Procedure | 626561, 626625, 627166, 627177 | 4 | 294002, 31413008 | t1_row_01 |
| 12 | Decision making | Procedure | 626561, 626625, 627166, 627177 | 4 | 133920001 | t0_row_09 |
| 13 | General characteristic of patient | Procedure | 626561, 626625, 627166, 627177 | 4 | 162673000, 7922000 | t1_row_01 |
| 14 | Health literacy | Procedure | 626561, 626625, 627166, 627177 | 4 | 431531000124101, 430253004 | t0_row_04 |
| 15 | Left ventricular ejection fraction | Procedure | 626561, 626625, 627166, 627177 | 4 | 46258004 | t1_row_01 |

## Role-Level Accuracy Trend

| Run | ClinicalCondition | ClinicalParameter | Procedure | Overall |
|---|---:|---:|---:|---:|
| 626561 | 0.724 | 1.000 | 0.449 | 0.583 |
| 626625 | 0.759 | 1.000 | 0.306 | 0.512 |
| 627166 | 0.724 | 1.000 | 0.551 | 0.643 |
| 627177 | 0.793 | 1.000 | 0.408 | 0.583 |
