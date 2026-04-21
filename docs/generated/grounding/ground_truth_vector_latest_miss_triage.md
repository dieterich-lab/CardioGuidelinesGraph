# Grounding Miss Triage

## Bucket Counts

| Bucket | Count |
|---|---:|
| tricky_near_miss | 5 |
| obvious_tune | 4 |
| annotation_review | 3 |

## Top Obvious Tune Targets

| Row | Role | Source Term | Gold | Pred | Score | Reason |
|---|---|---|---|---|---:|---|
| t0_row_01 | Procedure | Coronary artery bypass grafting | 232717009 (Coronary artery bypass grafting (procedure)) | 698378009 (Coronary artery bypass graft operation planned (situation)) | 1.000 | high_confidence_semantic_mismatch |
| t0_row_01 | ClinicalCondition | Myocardial ischemia | 414795007 (Myocardial ischemia (disorder)) | 32598000 (Acute ischemic heart disease (disorder)) | 1.000 | high_confidence_semantic_mismatch |
| t0_row_03 | ClinicalCondition | Myocardial ischemia | 414795007 (Myocardial ischemia (disorder)) | 32598000 (Acute ischemic heart disease (disorder)) | 1.000 | high_confidence_semantic_mismatch |
| t1_row_01 | ClinicalCondition | Myocardial ischemia | 414795007 (Myocardial ischemia (disorder)) | 32598000 (Acute ischemic heart disease (disorder)) | 1.000 | high_confidence_semantic_mismatch |

## Annotation Review Candidates

| Row | Role | Source Term | Gold | Pred | Hops | Reason |
|---|---|---|---|---|---:|---|
| t0_row_01 | Procedure | Informing patient | 310866003 (Informing patient (procedure)) | 148292006 (Informing patient (procedure)) |  | same_normalized_concept_text_different_id |
| t1_row_06 | Medication | Indication of | 230165009 (Indication of (contextual qualifier) (qualifier value)) | 39816005 (Indication of (contextual qualifier) (qualifier value)) |  | same_normalized_concept_text_different_id |
| t1_row_07 | Procedure | Coronary artery bypass graft | 232717009 (Coronary artery bypass grafting (procedure)) | 149173009 (Coronary artery bypass grafting (procedure)) |  | same_normalized_concept_text_different_id |
