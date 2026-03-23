# Grounding Miss Triage

## Bucket Counts

| Bucket | Count |
|---|---:|
| obvious_tune | 32 |
| tricky_near_miss | 4 |

## Top Obvious Tune Targets

| Row | Role | Source Term | Gold | Pred | Score | Reason |
|---|---|---|---|---|---:|---|
| t0_row_01 | Procedure | Percutaneous coronary revascularization | 415070008 (Percutaneous transluminal coronary intervention using imaging guidance with contrast (procedure)) | 713617008 (Percutaneous transluminal revascularization of chronic total occlusion of coronary artery using fluoroscopic guidance with contrast (procedure)) | 1.000 | low_semantic_overlap |
| t0_row_01 | Procedure | Using decision making strategies | 415806002 (Using decision making strategies (finding)) | <empty> (<empty>) | 0.000 | no_prediction_returned |
| t0_row_03 | Procedure | Treatment plan given | 314705003 (Treatment plan given (finding)) | 55053003 (Prescription of therapeutic regimen (procedure)) | 0.756 | low_semantic_overlap |
| t0_row_04 | Procedure | Using decision making strategies | 415806002 (Using decision making strategies (finding)) | <empty> (<empty>) | 0.000 | no_prediction_returned |
| t0_row_04 | Procedure | Preferences | 225773000 (Preferences (qualifier value)) | 223486007 (Discussion about preferences (procedure)) | 1.000 | high_confidence_semantic_mismatch |
| t0_row_04 | Procedure | Health literacy | 870552008 (Health literacy (observable entity)) | 431531000124101 (Health literacy assessment (procedure)) | 1.000 | high_confidence_semantic_mismatch |
| t0_row_04 | Procedure | Requires culturally responsive service to support health literacy | 1254714002 (Requires culturally responsive service to support health literacy (finding)) | <empty> (<empty>) | 0.000 | no_prediction_returned |
| t0_row_05 | ClinicalCondition | Specialist multidisciplinary team | 408458006 (Specialist multidisciplinary team (qualifier value)) | <empty> (<empty>) | 0.000 | no_prediction_returned |
| t0_row_07 | ClinicalCondition | Triple vessel disease of the heart | 233817007 (Triple vessel disease of the heart (disorder)) | 45414006 (Glucocorticoid deficiency with achalasia (disorder)) | 0.391 | low_semantic_overlap |
| t0_row_09 | Procedure | Decision making | 247583006 (Decision making (observable entity)) | 133920001 (Decision making encouragement (procedure)) | 1.000 | high_confidence_semantic_mismatch |
| t0_row_10 | ClinicalCondition | Multi vessel coronary artery disease | 371803003 (Multi vessel coronary artery disease (disorder)) | 50570003 (Aneurysm of coronary vessels (disorder)) | 0.554 | low_semantic_overlap |
| t0_row_11 | ClinicalCondition | High risk | 723509005 (High risk (qualifier value)) | 455201601000132100 (At high risk for fall (finding)) | 1.000 | high_confidence_semantic_mismatch |
| t0_row_11 | ClinicalCondition | Inoperable | 74778001 (Inoperable (qualifier value)) | <empty> (<empty>) | -1.000 | no_prediction_returned |
| t0_row_11 | ClinicalCondition | Multi vessel coronary artery disease | 371803003 (Multi vessel coronary artery disease (disorder)) | 50570003 (Aneurysm of coronary vessels (disorder)) | 0.554 | low_semantic_overlap |
| t0_row_11 | Procedure | Percutaneous coronary revascularization | 415070008 (Percutaneous transluminal coronary intervention using imaging guidance with contrast (procedure)) | 713617008 (Percutaneous transluminal revascularization of chronic total occlusion of coronary artery using fluoroscopic guidance with contrast (procedure)) | 1.000 | low_semantic_overlap |

## Annotation Review Candidates

| Row | Role | Source Term | Gold | Pred | Hops | Reason |
|---|---|---|---|---|---:|---|
