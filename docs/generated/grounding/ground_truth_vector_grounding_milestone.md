# Ground Truth Vector Grounding Persistent Error Milestone

Runs analyzed: 632865, 632922, 632923, 632932, 632933, 632934

Criterion: term-role pairs that missed in at least 5 analyzed runs.

## Latest Run Gate
- Latest run 632934 accuracy: 0.900000 (108/120)
- 0.60 gate: PASSED
- Best run in window: 632934 (0.900000, 108/120)
- Best GT3 run in window: 632934 (0.900000, 108/120)

## State Of The Art

- Current SOTA (GT3): run 632934 with accuracy 0.900000 (108/120).
- Latest run under review: 632934 (0.900000, 108/120).
- Delta latest vs SOTA (accuracy): +0.000000.

## Run Leaderboard (Window)

| Rank | Run | Overall | Hits/Total | Procedure | ClinicalCondition | Medication |
|---:|---|---:|---|---:|---:|---:|
| 1 | 632934 | 0.900 | 108/120 | 0.909 | 0.943 | 0.800 |
| 2 | 632923 | 0.800 | 96/120 | 0.758 | 0.811 | 0.800 |
| 3 | 632865 | 0.792 | 95/120 | 0.697 | 0.774 | 0.900 |
| 4 | 632933 | 0.692 | 83/120 | 0.667 | 0.528 | 0.967 |
| 5 | 632932 | 0.581 | 75/129 | 0.600 | 0.453 | 0.792 |
| 6 | 632922 | 0.567 | 68/120 | 0.455 | 0.547 | 0.667 |

## Latest Knob Snapshot

- `embedding_model` = `Qwen3embed`
- `embedding_node` = `local`
- `embedding_port` = `12368`
- `model` = `Qwen3next`
- `node` = `g3`
- `port` = `11433`
- `vector_index` = `snomed_term_embeddings_4096`
- `vector_uri` = `bolt://neo4j-dev3.internal:7687`
- `vector_user` = `neo4j`

## Latest Variation vs Previous Run

| Key | Previous | Latest |
|---|---|---|
| embedding_port | 12367 | 12368 |

## Latest Label-Confusion Highlights

| Rank | Role | Gold ID | Pred ID | Count | Example Term Pair | Example Rows |
|---:|---|---|---|---:|---|---|
| 1 | ClinicalCondition | 414795007 | 32598000 | 3 | Myocardial ischemia (disorder) -> Acute ischemic heart disease (disorder) | t0_row_01, t0_row_03, t1_row_01 |
| 2 | Medication | 386952008 | 734972007 | 3 | Clopidogrel (substance) -> Clopidogrel besilate (substance) | t0_row_02, t0_row_01, t1_row_04 |
| 3 | Medication | 443129001 | 1149423007 | 2 | Prasugrel (substance) -> Prasugrel besilate (substance) | t0_row_03, t1_row_02 |
| 4 | Procedure | 232717009 | 698378009 | 1 | Coronary artery bypass grafting (procedure) -> Coronary artery bypass graft operation planned (situation) | t0_row_01 |
| 5 | Procedure | 310866003 | 148292006 | 1 | Informing patient (procedure) -> Informing patient (procedure) | t0_row_01 |
| 6 | Medication | 230165009 | 39816005 | 1 | Indication of (contextual qualifier) (qualifier value) -> Indication of (contextual qualifier) (qualifier value) | t1_row_06 |
| 7 | Procedure | 232717009 | 149173009 | 1 | Coronary artery bypass grafting (procedure) -> Coronary artery bypass grafting (procedure) | t1_row_07 |

## Top Persistent Error Terms

| Rank | Term | Role | Runs Missed | Misses (analyzed runs) | Typical Wrong Prediction IDs | Example Rows |
|---:|---|---|---|---:|---|---|
| 1 | Myocardial ischemia | ClinicalCondition | 632865, 632922, 632923, 632932, 632933, 632934 | 19 | 164862008, 32598000, 41702007 | t0_row_01, t0_row_03, t1_row_01 |
| 2 | Coronary artery bypass grafting | Procedure | 632865, 632922, 632923, 632932, 632933, 632934 | 7 | 698378009, 232722009, 232719007 | t0_row_01, t0_row_07, t0_row_11 |
| 3 | Indication of | Medication | 632865, 632922, 632923, 632933, 632934 | 5 | <empty>, 39816005 | t1_row_06 |

## Role-Level Accuracy Trend

| Run | ClinicalCondition | ClinicalParameter | Medication | Procedure | Qualifier Value | string | Overall |
|---|---:|---:|---:|---:|---:|---:|---:|
| 632865 | 0.774 | 1.000 | 0.900 | 0.697 | n/a | 1.000 | 0.792 |
| 632922 | 0.547 | 1.000 | 0.667 | 0.455 | n/a | 1.000 | 0.567 |
| 632923 | 0.811 | 1.000 | 0.800 | 0.758 | n/a | 1.000 | 0.800 |
| 632932 | 0.453 | 1.000 | 0.792 | 0.600 | 1.000 | 1.000 | 0.581 |
| 632933 | 0.528 | 1.000 | 0.967 | 0.667 | n/a | 1.000 | 0.692 |
| 632934 | 0.943 | 1.000 | 0.800 | 0.909 | n/a | 1.000 | 0.900 |
