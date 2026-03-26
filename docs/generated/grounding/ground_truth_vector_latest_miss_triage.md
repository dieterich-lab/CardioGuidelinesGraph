# Grounding Miss Triage

## Bucket Counts

| Bucket | Count |
|---|---:|
| obvious_tune | 108 |
| tricky_near_miss | 3 |

## Top Obvious Tune Targets

| Row | Role | Source Term | Gold | Pred | Score | Reason |
|---|---|---|---|---|---:|---|
| t0_row_01 | Procedure | Percutaneous coronary revascularization | 415070008 (Percutaneous transluminal coronary intervention using imaging guidance with contrast (procedure)) | 713617008 (Percutaneous transluminal revascularization of chronic total occlusion of coronary artery using fluoroscopic guidance with contrast (procedure)) | 1.000 | low_semantic_overlap |
| t0_row_01 | Procedure | Using decision making strategies | 415806002 (Using decision making strategies (finding)) | 12121000202107 (Evaluation of decision-making capacity (procedure)) | 0.548 | low_semantic_overlap |
| t0_row_03 | Procedure | Treatment plan given | 314705003 (Treatment plan given (finding)) | 55053003 (Prescription of therapeutic regimen (procedure)) | 0.756 | low_semantic_overlap |
| t0_row_04 | Procedure | Using decision making strategies | 415806002 (Using decision making strategies (finding)) | 12121000202107 (Evaluation of decision-making capacity (procedure)) | 0.548 | low_semantic_overlap |
| t0_row_04 | Procedure | Preferences | 225773000 (Preferences (qualifier value)) | 223486007 (Discussion about preferences (procedure)) | 1.000 | high_confidence_semantic_mismatch |
| t0_row_04 | Procedure | Health literacy | 870552008 (Health literacy (observable entity)) | 431531000124101 (Health literacy assessment (procedure)) | 1.000 | high_confidence_semantic_mismatch |
| t0_row_04 | Procedure | Requires culturally responsive service to support health literacy | 1254714002 (Requires culturally responsive service to support health literacy (finding)) | 1156521001 (Education about health service (procedure)) | 0.915 | high_confidence_semantic_mismatch |
| t0_row_06 | Procedure | Myocardial revascularization | 275227003 (Myocardial revascularization (procedure)) | 64432007 (Radioisotope myocardial imaging procedure (procedure)) | 0.932 | low_semantic_overlap |
| t0_row_07 | ClinicalCondition | Triple vessel disease of the heart | 233817007 (Triple vessel disease of the heart (disorder)) | 45414006 (Glucocorticoid deficiency with achalasia (disorder)) | 0.391 | low_semantic_overlap |
| t0_row_07 | Procedure | Myocardial revascularization | 275227003 (Myocardial revascularization (procedure)) | 64432007 (Radioisotope myocardial imaging procedure (procedure)) | 0.932 | low_semantic_overlap |
| t0_row_08 | Procedure | Myocardial revascularization | 275227003 (Myocardial revascularization (procedure)) | 64432007 (Radioisotope myocardial imaging procedure (procedure)) | 0.932 | low_semantic_overlap |
| t0_row_09 | Procedure | Myocardial revascularization | 275227003 (Myocardial revascularization (procedure)) | 64432007 (Radioisotope myocardial imaging procedure (procedure)) | 0.932 | low_semantic_overlap |
| t0_row_10 | ClinicalCondition | Multi vessel coronary artery disease | 371803003 (Multi vessel coronary artery disease (disorder)) | 50570003 (Aneurysm of coronary vessels (disorder)) | 0.554 | low_semantic_overlap |
| t0_row_11 | ClinicalCondition | High risk | 723509005 (High risk (qualifier value)) | 161640005 (At high risk for heart disease (finding)) | 1.000 | high_confidence_semantic_mismatch |
| t0_row_11 | ClinicalCondition | Inoperable | 74778001 (Inoperable (qualifier value)) | <empty> (<empty>) | 0.000 | no_prediction_returned |

## Annotation Review Candidates

| Row | Role | Source Term | Gold | Pred | Hops | Reason |
|---|---|---|---|---|---:|---|
