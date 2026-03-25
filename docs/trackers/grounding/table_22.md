# Table22 Vector Grounding Persistent Error Milestone

Runs analyzed: 627576, 627880, 628092

Criterion: term-role pairs that missed in at least 2 analyzed runs.

## Latest Run Gate
- Latest run 628092 accuracy: 0.535714 (45/84)
- 0.60 gate: FAILED

## Top Persistent Error Terms

| Rank | Term | Role | Runs Missed | Misses (analyzed runs) | Typical Wrong Prediction IDs | Example Rows |
|---:|---|---|---|---:|---|---|
| 1 | Intracoronary pressure guide wire | Procedure | 627576, 627880, 628092 | 9 | <empty>, 431558000, 53178003 | t0_row_17, t0_row_18, t0_row_19 |
| 2 | Percutaneous coronary revascularization | Procedure | 627576, 627880, 628092 | 9 | 713617008 | t0_row_01, t0_row_11, t0_row_16 |
| 3 | Using decision making strategies | Procedure | 627576, 627880, 628092 | 9 | <empty>, 133920001 | t0_row_01, t0_row_04, t0_row_13 |
| 4 | Preferences | Procedure | 627576, 627880, 628092 | 6 | 223486007 | t0_row_04, t1_row_01 |
| 5 | High risk | ClinicalCondition | 627576, 627880, 628092 | 3 | 455201601000132100 | t0_row_11 |
| 6 | Inoperable | ClinicalCondition | 627576, 627880, 628092 | 3 | <empty> | t0_row_11 |
| 7 | Lesion | ClinicalCondition | 627576, 627880, 628092 | 3 | 300513000 | t0_row_16 |
| 8 | Medical therapy | ClinicalCondition | 627576, 627880, 628092 | 3 | 425914008 | t0_row_12 |
| 9 | Myocardial revascularization | ClinicalCondition | 627576, 627880, 628092 | 3 | 57809008 | t0_row_13 |
| 10 | Specialist multidisciplinary team | ClinicalCondition | 627576, 627880, 628092 | 3 | 268528005, <empty> | t0_row_05 |
| 11 | Assessment score | Procedure | 627576, 627880, 628092 | 3 | 1003700002 | t0_row_15 |
| 12 | Coronary artery structure | Procedure | 627576, 627880, 628092 | 3 | 294002 | t1_row_01 |
| 13 | Decision making | Procedure | 627576, 627880, 628092 | 3 | 133920001 | t0_row_09 |
| 14 | General characteristic of patient | Procedure | 627576, 627880, 628092 | 3 | 7922000, 162673000 | t1_row_01 |
| 15 | Health literacy | Procedure | 627576, 627880, 628092 | 3 | 431531000124101 | t0_row_04 |

## Role-Level Accuracy Trend

| Run | ClinicalCondition | ClinicalParameter | Procedure | Overall |
|---|---:|---:|---:|---:|
| 627576 | 0.793 | 1.000 | 0.551 | 0.667 |
| 627880 | 0.793 | 1.000 | 0.551 | 0.667 |
| 628092 | 0.759 | 1.000 | 0.347 | 0.536 |

## Latest Findings (2026-03-25)

- Current best remains tied at runs 627576 and 627880 (overall 0.667).
- Latest local-ollama run 628092 regressed to 0.536, driven mainly by Procedure collapse (0.551 -> 0.347).
- Infrastructure looked healthy during 628092 (embedding endpoint active), so this appears to be scoring/retrieval behavior rather than service failure.

## Frozen Baseline Knobs (A Arm)

These are now fixed as script defaults in both vector wrappers and represent Arm A:

- `CARDIO_GRAPH_GROUNDING_VECTOR_RERANK_WEIGHT=0.03`
- `CARDIO_GRAPH_GROUNDING_VECTOR_BONUS_CAP=0.05`
- `CARDIO_GRAPH_GROUNDING_VECTOR_MIN_LEXICAL_FOR_BONUS=0.90`
- `CARDIO_GRAPH_GROUNDING_MIN_WEIGHTED_QUERY_COVERAGE=0.45`
- `CARDIO_GRAPH_GROUNDING_LOW_COVERAGE_PENALTY=0.12`
- `CARDIO_GRAPH_GROUNDING_MISSING_DISCRIMINATIVE_PENALTY=0.10`
- `CARDIO_GRAPH_GROUNDING_EXTRA_QUALIFIER_PENALTY=0.10`
- `CARDIO_GRAPH_GROUNDING_GUARDED_FALLBACK_MARGIN=0.015`
- `CARDIO_GRAPH_GROUNDING_MIN_DISCRIMINATIVE_COVERAGE_FOR_TOP=0.60`
- `CARDIO_GRAPH_GROUNDING_HARD_NEGATIVE_PENALTY=0.05`
- `CARDIO_GRAPH_GROUNDING_AMBIGUITY_ABSTAIN_MARGIN=0.012`
- `CARDIO_GRAPH_GROUNDING_AMBIGUITY_MIN_COVERAGE=0.55`
- `CARDIO_GRAPH_GROUNDING_AMBIGUITY_CONFIDENCE_BACKOFF_ENABLED=true`
- `CARDIO_GRAPH_GROUNDING_AMBIGUITY_BACKOFF_MAX_DROP=0.05`
- `CARDIO_GRAPH_GROUNDING_AMBIGUITY_BACKOFF_MIN_SCORE=0.35`
- `CARDIO_GRAPH_GROUNDING_ROLE_SOFT_CONSTRAINTS=true`
- `CARDIO_GRAPH_GROUNDING_ROLE_MISMATCH_PENALTY=0.05`
- `CARDIO_GRAPH_GROUNDING_ROLE_TENSION_PENALTY=0.02`
- `CARDIO_GRAPH_GROUNDING_ROLE_SEMANTIC_MISMATCH_PENALTY=0.06`
- `CARDIO_GRAPH_GROUNDING_ROLE_SEMANTIC_CROSSCLASS_PENALTY=0.02`
- `CARDIO_GRAPH_GROUNDING_AMBIGUITY_LEXICAL_FORCE_PICK=0.90`
- `CARDIO_GRAPH_GROUNDING_VECTOR_CONTEXT_ENABLED=false`
- `CARDIO_GRAPH_GROUNDING_VECTOR_CONTEXT_MAX_TOKENS=8`

## A/B Experiment Definition

- Arm A (baseline): frozen knobs above, context vector query disabled.
- Arm B (context-aware): identical knobs, enable context query via `CARDIO_GRAPH_GROUNDING_VECTOR_CONTEXT_ENABLED=true`.
- Success criteria: non-negative overall delta vs Arm A and Procedure accuracy improvement without large ClinicalCondition regressions.
