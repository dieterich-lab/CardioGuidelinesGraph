# Current SNOMED Mappings (Scientific Track)

Canonical reference for colleague review of current system mappings under the scientific (no-rescue) protocol.

- Selected run: `630837` (locked_test, no rescue)
- Accuracy: `0.483333` (`58/120`)
- MRR: `0.522024`
- Source JSON: `docs/generated/ground_truth/grounding_only/vector_job_630837/ground_truth_vector_eval.json`
- Validation note: no newer scientific locked_test run exists in `docs/generated/grounding/ground_truth_vector_runs_manifest.jsonl` as of 2026-04-16.

Columns:
- `row_id`, `side`, `role`, `term`: source concept location and role in GT annotations
- `gold_snomed_id` / `gold_concept_term`: ground truth target
- `pred_snomed_id` / `pred_concept_term`: system prediction
- `hit`: `1` if prediction matches ground truth else `0`

| row_id | side | role | term | gold_snomed_id | gold_concept_term | pred_snomed_id | pred_concept_term | hit |
|---|---|---|---|---:|---|---:|---|---:|
| t0_row_01 | action | Medication | Aspirin | 387458008 | Aspirin (substance) | 25796002 | Aluminium aspirin (substance) | 0 |
| t0_row_01 | action | Medication | Clopidogrel | 386952008 | Clopidogrel (substance) | 386952008 | Clopidogrel (substance) | 1 |
| t0_row_01 | action | Medication | Rivaroxaban | 442031002 | Rivaroxaban (substance) | 442031002 | Rivaroxaban (substance) | 1 |
| t0_row_01 | action | Procedure | Informing patient | 310866003 | Informing patient (procedure) | 310866003 | Informing patient (procedure) | 1 |
| t0_row_01 | action | Procedure | Using decision making strategies | 415806002 | Using decision making strategies (finding) | 133920001 | Decision making encouragement (procedure) | 0 |
| t0_row_01 | condition | ClinicalCondition | Chronic ischemic heart disease | 413838009 | Chronic ischemic heart disease (disorder) | 413838009 | Chronic ischemic heart disease (disorder) | 1 |
| t0_row_01 | condition | ClinicalCondition | Coronary artery disease | 53741008 | Coronary arteriosclerosis (disorder) | 53741008 | Coronary arteriosclerosis (disorder) | 1 |
| t0_row_01 | condition | ClinicalCondition | Finding of increased risk level | 1255670000 | Finding of increased risk level (finding) | 1255670000 | Finding of increased risk level (finding) | 1 |
| t0_row_01 | condition | ClinicalCondition | Myocardial ischemia | 414795007 | Myocardial ischemia (disorder) | 414795007 | Myocardial ischemia (disorder) | 1 |
| t0_row_01 | condition | ClinicalCondition | Old myocardial infarction | 1755008 | Old myocardial infarction (disorder) | 164867002 | Electrocardiographic old myocardial infarction (finding) | 0 |
| t0_row_01 | condition | ClinicalCondition | Peripheral arterial disease | 840580004 | Peripheral arterial disease (disorder) | 840580004 | Peripheral arterial disease (disorder) | 1 |
| t0_row_01 | condition | Procedure | Coronary artery bypass grafting | 232717009 | Coronary artery bypass grafting (procedure) | 232719007 | Coronary artery bypass graft x 1 (procedure) | 0 |
| t0_row_01 | condition | Procedure | Percutaneous coronary revascularization | 415070008 | Percutaneous transluminal coronary intervention using imaging guidance with contrast (procedure) | 713617008 | Percutaneous transluminal revascularization of chronic total occlusion of coronary artery using fluoroscopic guidance with contrast (procedure) | 0 |
| t0_row_02 | action | Medication | Aspirin | 387458008 | Aspirin (substance) | 25796002 | Aluminium aspirin (substance) | 0 |
| t0_row_02 | action | Medication | Clopidogrel | 386952008 | Clopidogrel (substance) | 386952008 | Clopidogrel (substance) | 1 |
| t0_row_02 | action | Procedure | Medical therapy | 243121000 | Medical therapy (procedure) | 243121000 | Medical therapy (procedure) | 1 |
| t0_row_02 | action | Procedure | Myocardial revascularization | 275227003 | Myocardial revascularization (procedure) | 70627009 | Myocardial resection (procedure) | 0 |
| t0_row_02 | condition | ClinicalCondition | Chronic ischemic heart disease | 413838009 | Chronic ischemic heart disease (disorder) | 413838009 | Chronic ischemic heart disease (disorder) | 1 |
| t0_row_02 | condition | ClinicalCondition | Coronary artery disease | 53741008 | Coronary arteriosclerosis (disorder) | 53741008 | Coronary arteriosclerosis (disorder) | 1 |
| t0_row_02 | condition | ClinicalCondition | Myocardial infarction | 22298006 | Myocardial infarction (disorder) | 164865005 | Electrocardiographic myocardial infarction (finding) | 0 |
| t0_row_02 | condition | ClinicalCondition | Old myocardial infarction | 1755008 | Old myocardial infarction (disorder) | 164867002 | Electrocardiographic old myocardial infarction (finding) | 0 |
| t0_row_02 | condition | ClinicalCondition | Triple vessel disease of the heart | 233817007 | Triple vessel disease of the heart (disorder) | 233817007 | Triple vessel disease of the heart (disorder) | 1 |
| t0_row_02 | condition | ClinicalParameter | Left ventricular ejection fraction | 250908004 | Left ventricular ejection fraction (observable entity) | 250908004 | Left ventricular ejection fraction (observable entity) | 1 |
| t0_row_02 | condition | Medication | Drug therapy with explicit context | 1290126002 | Drug therapy with explicit context (situation) |  |  | 0 |
| t0_row_02 | condition | Procedure | Repair of coronary artery | 415070008 | Percutaneous transluminal coronary intervention using imaging guidance with contrast (procedure) | 713689002 | Repair of coronary artery (procedure) | 0 |
| t0_row_03 | action | Medication | Aspirin | 387458008 | Aspirin (substance) | 25796002 | Aluminium aspirin (substance) | 0 |
| t0_row_03 | action | Medication | Prasugrel | 443129001 | Prasugrel (substance) | 443129001 | Prasugrel (substance) | 1 |
| t0_row_03 | action | Medication | Ticagrelor | 698805004 | Ticagrelor (substance) | 698805004 | Ticagrelor (substance) | 1 |
| t0_row_03 | action | Procedure | Medical therapy | 243121000 | Medical therapy (procedure) | 243121000 | Medical therapy (procedure) | 1 |
| t0_row_03 | action | Procedure | Myocardial revascularization | 275227003 | Myocardial revascularization (procedure) | 70627009 | Myocardial resection (procedure) | 0 |
| t0_row_03 | condition | ClinicalCondition | Acute coronary syndrome | 394659003 | Acute coronary syndrome (disorder) | 413439005 | Acute ischemic heart disease (disorder) | 0 |
| t0_row_03 | condition | ClinicalCondition | At high risk for bleeding | 711536002 | At high risk for bleeding (finding) | 711536002 | At high risk for bleeding (finding) | 1 |
| t0_row_03 | condition | ClinicalCondition | Atherosclerosis of proximal portion of anterior descending branch of left coronary artery | 1366501001 | Atherosclerosis of proximal portion of anterior descending branch of left coronary artery (disorder) | 1366498001 | Atherosclerosis of anterior descending branch of left coronary artery (disorder) | 0 |
| t0_row_03 | condition | ClinicalCondition | Chronic ischemic heart disease | 413838009 | Chronic ischemic heart disease (disorder) | 413838009 | Chronic ischemic heart disease (disorder) | 1 |
| t0_row_03 | condition | ClinicalCondition | Double coronary vessel disease | 194843003 | Double coronary vessel disease (disorder) | 194843003 | Double coronary vessel disease (disorder) | 1 |
| t0_row_03 | condition | ClinicalCondition | Finding of increased risk level | 1255670000 | Finding of increased risk level (finding) | 1255670000 | Finding of increased risk level (finding) | 1 |
| t0_row_03 | condition | ClinicalCondition | Myocardial infarction | 22298006 | Myocardial infarction (disorder) | 164865005 | Electrocardiographic myocardial infarction (finding) | 0 |
| t0_row_03 | condition | ClinicalCondition | Myocardial ischemia | 414795007 | Myocardial ischemia (disorder) | 414795007 | Myocardial ischemia (disorder) | 1 |
| t0_row_03 | condition | ClinicalCondition | Single coronary vessel disease | 194842008 | Single coronary vessel disease (disorder) | 194842008 | Single coronary vessel disease (disorder) | 1 |
| t0_row_03 | condition | ClinicalParameter | Left ventricular ejection fraction | 250908004 | Left ventricular ejection fraction (observable entity) | 250908004 | Left ventricular ejection fraction (observable entity) | 1 |
| t0_row_03 | condition | Medication | Drug therapy with explicit context | 1290126002 | Drug therapy with explicit context (situation) |  |  | 0 |
| t0_row_03 | condition | Medication | Ticagrelor | 698805004 | Ticagrelor (substance) | 698805004 | Ticagrelor (substance) | 1 |
| t0_row_03 | condition | Procedure | Percutaneous coronary revascularization | 415070008 | Percutaneous transluminal coronary intervention using imaging guidance with contrast (procedure) | 713617008 | Percutaneous transluminal revascularization of chronic total occlusion of coronary artery using fluoroscopic guidance with contrast (procedure) | 0 |
| t0_row_04 | action | Medication | Aspirin | 387458008 | Aspirin (substance) | 25796002 | Aluminium aspirin (substance) | 0 |
| t0_row_04 | action | Medication | Ticagrelor | 698805004 | Ticagrelor (substance) | 698805004 | Ticagrelor (substance) | 1 |
| t0_row_04 | action | Procedure | Intravascular ultrasound of artery | 241467003 | Intravascular ultrasound of artery (procedure) | 241467003 | Intravascular ultrasound of artery (procedure) | 1 |
| t0_row_04 | action | Procedure | Optical coherence tomography | 392010000 | Optical coherence tomography (procedure) | 392010000 | Optical coherence tomography (procedure) | 1 |
| t0_row_04 | condition | ClinicalCondition | Chronic ischemic heart disease | 413838009 | Chronic ischemic heart disease (disorder) | 413838009 | Chronic ischemic heart disease (disorder) | 1 |
| t0_row_04 | condition | ClinicalCondition | Lesion | 52988006 | Lesion (morphologic abnormality) | 7870007 | Vascular lesion of cord (disorder) | 0 |
| t0_row_04 | condition | ClinicalCondition | Myocardial infarction | 22298006 | Myocardial infarction (disorder) | 164865005 | Electrocardiographic myocardial infarction (finding) | 0 |
| t0_row_04 | condition | ClinicalCondition | Stenosis of left coronary artery main stem | 876857001 | Stenosis of left coronary artery main stem (disorder) | 876857001 | Stenosis of left coronary artery main stem (disorder) | 1 |
| t0_row_04 | condition | Medication | Drug therapy with explicit context | 1290126002 | Drug therapy with explicit context (situation) |  |  | 0 |
| t0_row_04 | condition | Procedure | Percutaneous coronary revascularization | 415070008 | Percutaneous transluminal coronary intervention using imaging guidance with contrast (procedure) | 713617008 | Percutaneous transluminal revascularization of chronic total occlusion of coronary artery using fluoroscopic guidance with contrast (procedure) | 0 |
| t0_row_05 | action | Procedure | Angiography of coronary artery | 33367005 | Angiography of coronary artery (procedure) | 33367005 | Angiography of coronary artery (procedure) | 1 |
| t0_row_05 | action | Procedure | Intracoronary pressure guide wire | 371789009 | Intracoronary pressure guide wire (physical object) | 431558000 | Insertion of cardiac pressure wire using fluoroscopic guidance (procedure) | 0 |
| t0_row_05 | condition | ClinicalCondition | Chronic ischemic heart disease | 413838009 | Chronic ischemic heart disease (disorder) | 413838009 | Chronic ischemic heart disease (disorder) | 1 |
| t0_row_05 | condition | Procedure | Myocardial revascularization | 275227003 | Myocardial revascularization (procedure) | 70627009 | Myocardial resection (procedure) | 0 |
| t0_row_06 | action | Procedure | Angiography of coronary artery | 33367005 | Angiography of coronary artery (procedure) | 33367005 | Angiography of coronary artery (procedure) | 1 |
| t0_row_06 | action | Procedure | Intracoronary pressure guide wire | 371789009 | Intracoronary pressure guide wire (physical object) | 431558000 | Insertion of cardiac pressure wire using fluoroscopic guidance (procedure) | 0 |
| t0_row_06 | condition | ClinicalCondition | Chronic ischemic heart disease | 413838009 | Chronic ischemic heart disease (disorder) | 413838009 | Chronic ischemic heart disease (disorder) | 1 |
| t0_row_06 | condition | Procedure | Myocardial revascularization | 275227003 | Myocardial revascularization (procedure) | 70627009 | Myocardial resection (procedure) | 0 |
| t1_row_01 | action | Medication | Drug therapy with explicit context | 1290126002 | Drug therapy with explicit context (situation) |  |  | 0 |
| t1_row_01 | action | Medication | Platelet aggregation inhibitor therapy | 840595002 | Platelet aggregation inhibitor therapy (procedure) | 771452004 | Substance with platelet aggregation inhibitor mechanism of action (substance) | 0 |
| t1_row_01 | action | Procedure | Coronary artery structure | 41801008 | Coronary artery structure (body structure) | 294002 | Excisional biopsy of joint structure of spine (procedure) | 0 |
| t1_row_01 | action | Procedure | General characteristic of patient | 363789004 | General characteristic of patient (observable entity) | 7922000 | General treatment (procedure) | 0 |
| t1_row_01 | action | Procedure | Left ventricular ejection fraction | 250908004 | Left ventricular ejection fraction (observable entity) | 46258004 | Determination of ventricular ejection fraction with probe technique (procedure) | 0 |
| t1_row_01 | action | Procedure | Likely outcome | 410596003 | Likely outcome (qualifier value) | 20481000 | Determination of prognosis (procedure) | 0 |
| t1_row_01 | action | Procedure | Preferences | 225773000 | Preferences (qualifier value) | 1156333005 | Determination of subject's care preferences (procedure) | 0 |
| t1_row_01 | condition | ClinicalCondition | At high risk for bleeding | 711536002 | At high risk for bleeding (finding) | 711536002 | At high risk for bleeding (finding) | 1 |
| t1_row_01 | condition | ClinicalCondition | Chronic ischemic heart disease | 413838009 | Chronic ischemic heart disease (disorder) | 413838009 | Chronic ischemic heart disease (disorder) | 1 |
| t1_row_01 | condition | ClinicalCondition | Finding of increased risk level | 1255670000 | Finding of increased risk level (finding) | 1255670000 | Finding of increased risk level (finding) | 1 |
| t1_row_01 | condition | ClinicalCondition | Indication of | 230165009 | Indication of (contextual qualifier) (qualifier value) | 1363183004 | Pain behavior (finding) | 0 |
| t1_row_01 | condition | ClinicalCondition | Myocardial ischemia | 414795007 | Myocardial ischemia (disorder) | 414795007 | Myocardial ischemia (disorder) | 1 |
| t1_row_01 | condition | ClinicalCondition | Use of anticoagulation | 260678004 | Use of anticoagulation (attribute) | 440678006 | Seen in hospital anticoagulation clinic (finding) | 0 |
| t1_row_01 | condition | Procedure | Myocardial revascularization | 275227003 | Myocardial revascularization (procedure) | 70627009 | Myocardial resection (procedure) | 0 |
| t1_row_01 | condition | Procedure | Percutaneous coronary revascularization | 415070008 | Percutaneous transluminal coronary intervention using imaging guidance with contrast (procedure) | 713617008 | Percutaneous transluminal revascularization of chronic total occlusion of coronary artery using fluoroscopic guidance with contrast (procedure) | 0 |
| t1_row_02 | action | Medication | Prasugrel | 443129001 | Prasugrel (substance) | 443129001 | Prasugrel (substance) | 1 |
| t1_row_02 | action | Medication | Ticagrelor | 698805004 | Ticagrelor (substance) | 698805004 | Ticagrelor (substance) | 1 |
| t1_row_02 | condition | ClinicalCondition | Chronic ischemic heart disease | 413838009 | Chronic ischemic heart disease (disorder) | 413838009 | Chronic ischemic heart disease (disorder) | 1 |
| t1_row_02 | condition | ClinicalCondition | Indication of | 230165009 | Indication of (contextual qualifier) (qualifier value) | 1363183004 | Pain behavior (finding) | 0 |
| t1_row_02 | condition | ClinicalCondition | Use of anticoagulation | 260678004 | Use of anticoagulation (attribute) | 440678006 | Seen in hospital anticoagulation clinic (finding) | 0 |
| t1_row_02 | condition | Procedure | Finding of increased risk level | 1255670000 | Finding of increased risk level (finding) | 48696000 | Provocative test for increased intraocular pressure for glaucoma (procedure) | 0 |
| t1_row_02 | condition | Procedure | Placement of stent in coronary artery | 36969009 | Placement of stent in coronary artery (procedure) | 36969009 | Placement of stent in coronary artery (procedure) | 1 |
| t1_row_03 | action | Medication | Aspirin | 387458008 | Aspirin (substance) | 25796002 | Aluminium aspirin (substance) | 0 |
| t1_row_03 | condition | ClinicalCondition | Chronic ischemic heart disease | 413838009 | Chronic ischemic heart disease (disorder) | 413838009 | Chronic ischemic heart disease (disorder) | 1 |
| t1_row_03 | condition | ClinicalCondition | Indication of | 230165009 | Indication of (contextual qualifier) (qualifier value) | 1363183004 | Pain behavior (finding) | 0 |
| t1_row_03 | condition | ClinicalCondition | Use of anticoagulation | 260678004 | Use of anticoagulation (attribute) | 440678006 | Seen in hospital anticoagulation clinic (finding) | 0 |
| t1_row_03 | condition | Procedure | Percutaneous coronary revascularization | 415070008 | Percutaneous transluminal coronary intervention using imaging guidance with contrast (procedure) | 713617008 | Percutaneous transluminal revascularization of chronic total occlusion of coronary artery using fluoroscopic guidance with contrast (procedure) | 0 |
| t1_row_04 | action | Medication | Aspirin | 387458008 | Aspirin (substance) | 25796002 | Aluminium aspirin (substance) | 0 |
| t1_row_04 | action | Medication | Clopidogrel | 386952008 | Clopidogrel (substance) | 386952008 | Clopidogrel (substance) | 1 |
| t1_row_04 | action | Medication | Oral | 738956005 | Oral (intended site) | 13790009 | Product containing iron in oral dose form (medicinal product form) | 0 |
| t1_row_04 | action | Medication | Use of anticoagulation | 260678004 | Use of anticoagulation (attribute) |  |  | 0 |
| t1_row_04 | condition | ClinicalCondition | Chronic ischemic heart disease | 413838009 | Chronic ischemic heart disease (disorder) | 413838009 | Chronic ischemic heart disease (disorder) | 1 |
| t1_row_04 | condition | ClinicalCondition | Indication of | 230165009 | Indication of (contextual qualifier) (qualifier value) | 1363183004 | Pain behavior (finding) | 0 |
| t1_row_04 | condition | ClinicalCondition | Use of anticoagulation | 260678004 | Use of anticoagulation (attribute) | 440678006 | Seen in hospital anticoagulation clinic (finding) | 0 |
| t1_row_04 | condition | Procedure | Percutaneous coronary revascularization | 415070008 | Percutaneous transluminal coronary intervention using imaging guidance with contrast (procedure) | 713617008 | Percutaneous transluminal revascularization of chronic total occlusion of coronary artery using fluoroscopic guidance with contrast (procedure) | 0 |
| t1_row_05 | action | Medication | Rivaroxaban | 442031002 | Rivaroxaban (substance) | 442031002 | Rivaroxaban (substance) | 1 |
| t1_row_05 | condition | ClinicalCondition | At high risk for bleeding | 711536002 | At high risk for bleeding (finding) | 711536002 | At high risk for bleeding (finding) | 1 |
| t1_row_05 | condition | ClinicalCondition | Chronic ischemic heart disease | 413838009 | Chronic ischemic heart disease (disorder) | 413838009 | Chronic ischemic heart disease (disorder) | 1 |
| t1_row_05 | condition | ClinicalCondition | Coronary artery stent thrombosis | 421327009 | Coronary artery stent thrombosis (disorder) | 421327009 | Coronary artery stent thrombosis (disorder) | 1 |
| t1_row_05 | condition | ClinicalCondition | Finding of increased risk level | 1255670000 | Finding of increased risk level (finding) | 1255670000 | Finding of increased risk level (finding) | 1 |
| t1_row_05 | condition | ClinicalCondition | Indication of | 230165009 | Indication of (contextual qualifier) (qualifier value) | 1363183004 | Pain behavior (finding) | 0 |
| t1_row_05 | condition | ClinicalCondition | Ischemic stroke | 422504002 | Ischemic stroke (disorder) | 422504002 | Ischemic stroke (disorder) | 1 |
| t1_row_05 | condition | ClinicalCondition | Use of anticoagulation | 260678004 | Use of anticoagulation (attribute) | 440678006 | Seen in hospital anticoagulation clinic (finding) | 0 |
| t1_row_05 | condition | Procedure | Percutaneous coronary revascularization | 415070008 | Percutaneous transluminal coronary intervention using imaging guidance with contrast (procedure) | 713617008 | Percutaneous transluminal revascularization of chronic total occlusion of coronary artery using fluoroscopic guidance with contrast (procedure) | 0 |
| t1_row_06 | action | Medication | Indirect acting anticoagulant | 419847008 | Indirect acting anticoagulant (substance) | 419847008 | Indirect acting anticoagulant (substance) | 1 |
| t1_row_06 | condition | ClinicalCondition | Chronic ischemic heart disease | 413838009 | Chronic ischemic heart disease (disorder) | 413838009 | Chronic ischemic heart disease (disorder) | 1 |
| t1_row_06 | condition | ClinicalCondition | Indication of | 230165009 | Indication of (contextual qualifier) (qualifier value) | 1363183004 | Pain behavior (finding) | 0 |
| t1_row_06 | condition | ClinicalCondition | Use of anticoagulation | 260678004 | Use of anticoagulation (attribute) | 440678006 | Seen in hospital anticoagulation clinic (finding) | 0 |
| t1_row_06 | condition | Medication | Drug therapy with explicit context | 1290126002 | Drug therapy with explicit context (situation) |  |  | 0 |
| t1_row_06 | condition | Medication | Indication of | 230165009 | Indication of (contextual qualifier) (qualifier value) |  |  | 0 |
| t1_row_06 | condition | Medication | Indirect acting anticoagulant | 419847008 | Indirect acting anticoagulant (substance) | 419847008 | Indirect acting anticoagulant (substance) | 1 |
| t1_row_06 | condition | Procedure | Percutaneous coronary revascularization | 415070008 | Percutaneous transluminal coronary intervention using imaging guidance with contrast (procedure) | 713617008 | Percutaneous transluminal revascularization of chronic total occlusion of coronary artery using fluoroscopic guidance with contrast (procedure) | 0 |
| t1_row_07 | action | Medication | Aspirin | 387458008 | Aspirin (substance) | 25796002 | Aluminium aspirin (substance) | 0 |
| t1_row_07 | condition | ClinicalCondition | Chronic ischemic heart disease | 413838009 | Chronic ischemic heart disease (disorder) | 413838009 | Chronic ischemic heart disease (disorder) | 1 |
| t1_row_07 | condition | Procedure | Coronary artery bypass graft | 232717009 | Coronary artery bypass grafting (procedure) | 232717009 | Coronary artery bypass grafting (procedure) | 1 |
| t1_row_08 | action | Medication | Proton pump inhibitor | 734582004 | Hydrogen/potassium adenosine triphosphatase enzyme system inhibitor (disposition) | 372525000 | Substance with hydrogen/potassium adenosine triphosphatase enzyme system inhibitor mechanism of action (substance) | 0 |
| t1_row_08 | condition | ClinicalCondition | Chronic ischemic heart disease | 413838009 | Chronic ischemic heart disease (disorder) | 413838009 | Chronic ischemic heart disease (disorder) | 1 |
| t1_row_08 | condition | string | Finding of increased risk level | 1255670000 | Finding of increased risk level (finding) | 1255670000 | Finding of increased risk level (finding) | 1 |
| t1_row_08 | condition | string | Gastrointestinal hemorrhage | 74474003 | Gastrointestinal hemorrhage (disorder) | 155837004 | Gastrointestinal haemorrhage (disorder) | 0 |
