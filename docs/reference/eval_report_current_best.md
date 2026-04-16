# Ground Truth vs Current Best Mapping Report

This report lists every grounded concept row for the current best completed GT3 run, grouped by table.

- Selected best run: 630501
- Best run accuracy: 0.824034 (192/233)
- Replicate run: 630502
- Replicate accuracy: 0.793991 (185/233)
- MRR (best): 0.825874

Columns:
- row_id, side, role, term: source concept location and role in GT annotations
- gold_snomed_id / gold_concept_term: ground truth SNOMED target
- pred_snomed_id / pred_concept_term: mapping produced by current best system
- hit: whether prediction equals ground truth

## Table 0

| row_id | side | role | term | gold_snomed_id | gold_concept_term | pred_snomed_id | pred_concept_term | hit |
|---|---|---|---|---:|---|---:|---|---:|
| t0_row_01 | action | Medication | Aspirin | 387458008 | Aspirin (substance) | 387458008 | Aspirin (substance) | 1 |
| t0_row_01 | action | Medication | Drug therapy with explicit context | 1290126002 | Drug therapy with explicit context (situation) | 1290126002 | Drug therapy with explicit context (situation) | 1 |
| t0_row_01 | action | Medication | Rivaroxaban | 442031002 | Rivaroxaban (substance) | 442031002 | Rivaroxaban (substance) | 1 |
| t0_row_01 | action | Procedure | Informing patient | 310866003 | Informing patient (procedure) | 310866003 | Informing patient (procedure) | 1 |
| t0_row_01 | action | Procedure | Using decision making strategies | 415806002 | Using decision making strategies (finding) | 133920001 | Decision making encouragement (procedure) | 0 |
| t0_row_01 | condition | ClinicalCondition | Chronic ischemic heart disease | 413838009 | Chronic ischemic heart disease (disorder) | 413838009 | Chronic ischemic heart disease (disorder) | 1 |
| t0_row_01 | condition | ClinicalCondition | Coronary artery disease | 53741008 | Coronary arteriosclerosis (disorder) | 53741008 | Coronary arteriosclerosis (disorder) | 1 |
| t0_row_01 | condition | ClinicalCondition | Finding of increased risk level | 1255670000 | Finding of increased risk level (finding) | 1255670000 | Finding of increased risk level (finding) | 1 |
| t0_row_01 | condition | ClinicalCondition | Myocardial ischemia | 414795007 | Myocardial ischemia (disorder) | 414795007 | Myocardial ischemia (disorder) | 1 |
| t0_row_01 | condition | ClinicalCondition | Old myocardial infarction | 1755008 | Old myocardial infarction (disorder) | 1755008 | Old myocardial infarction (disorder) | 1 |
| t0_row_01 | condition | ClinicalCondition | Peripheral arterial disease | 840580004 | Peripheral arterial disease (disorder) | 840580004 | Peripheral arterial disease (disorder) | 1 |
| t0_row_01 | condition | Procedure | Coronary artery bypass grafting | 232717009 | Coronary artery bypass grafting (procedure) | 232719007 | Coronary artery bypass graft x 1 (procedure) | 0 |
| t0_row_01 | condition | Procedure | Percutaneous coronary revascularization | 415070008 | Percutaneous transluminal coronary intervention using imaging guidance with contrast (procedure) | 415070008 | Percutaneous transluminal coronary intervention using imaging guidance with contrast (procedure) | 1 |
| t0_row_02 | action | Medication | Aspirin | 387458008 | Aspirin (substance) | 387458008 | Aspirin (substance) | 1 |
| t0_row_02 | action | Medication | Clopidogrel | 386952008 | Clopidogrel (substance) | 386952008 | Clopidogrel (substance) | 1 |
| t0_row_02 | action | Procedure | Multidisciplinary meeting | 287051000000107 | Multidisciplinary meeting (procedure) | 287051000000107 | Multidisciplinary meeting (procedure) | 1 |
| t0_row_02 | condition | ClinicalCondition | Chronic ischemic heart disease | 413838009 | Chronic ischemic heart disease (disorder) | 413838009 | Chronic ischemic heart disease (disorder) | 1 |
| t0_row_02 | condition | ClinicalCondition | Disorder of cardiovascular system | 49601007 | Disorder of cardiovascular system (disorder) | 49601007 | Disorder of cardiovascular system (disorder) | 1 |
| t0_row_02 | condition | ClinicalCondition | Myocardial infarction | 22298006 | Myocardial infarction (disorder) | 22298006 | Myocardial infarction (disorder) | 1 |
| t0_row_02 | condition | ClinicalCondition | Old myocardial infarction | 1755008 | Old myocardial infarction (disorder) | 1755008 | Old myocardial infarction (disorder) | 1 |
| t0_row_02 | condition | Medication | Drug therapy with explicit context | 1290126002 | Drug therapy with explicit context (situation) | 1290126002 | Drug therapy with explicit context (situation) | 1 |
| t0_row_02 | condition | Procedure | Percutaneous coronary revascularization | 415070008 | Percutaneous transluminal coronary intervention using imaging guidance with contrast (procedure) | 415070008 | Percutaneous transluminal coronary intervention using imaging guidance with contrast (procedure) | 1 |
| t0_row_03 | action | Medication | Aspirin | 387458008 | Aspirin (substance) | 387458008 | Aspirin (substance) | 1 |
| t0_row_03 | action | Medication | Prasugrel | 443129001 | Prasugrel (substance) | 443129001 | Prasugrel (substance) | 1 |
| t0_row_03 | action | Procedure | Informing patient | 310866003 | Informing patient (procedure) | 310866003 | Informing patient (procedure) | 1 |
| t0_row_03 | condition | ClinicalCondition | Chronic ischemic heart disease | 413838009 | Chronic ischemic heart disease (disorder) | 413838009 | Chronic ischemic heart disease (disorder) | 1 |
| t0_row_03 | condition | ClinicalCondition | Coronary artery bypass grafting | 232717009 | Coronary artery bypass grafting (procedure) | 132091000119104 | Chronic deep venous thrombosis of lower limb due to and following coronary artery bypass grafting (disorder) | 0 |
| t0_row_03 | condition | ClinicalCondition | Myocardial infarction | 22298006 | Myocardial infarction (disorder) | 22298006 | Myocardial infarction (disorder) | 1 |
| t0_row_03 | condition | Medication | Drug therapy with explicit context | 1290126002 | Drug therapy with explicit context (situation) | 1290126002 | Drug therapy with explicit context (situation) | 1 |
| t0_row_03 | condition | Procedure | Percutaneous coronary revascularization | 415070008 | Percutaneous transluminal coronary intervention using imaging guidance with contrast (procedure) | 415070008 | Percutaneous transluminal coronary intervention using imaging guidance with contrast (procedure) | 1 |
| t0_row_03 | condition | Procedure | Treatment plan given | 314705003 | Treatment plan given (finding) | 55053003 | Prescription of therapeutic regimen (procedure) | 0 |
| t0_row_04 | action | Medication | Aspirin | 387458008 | Aspirin (substance) | 387458008 | Aspirin (substance) | 1 |
| t0_row_04 | action | Medication | Ticagrelor | 698805004 | Ticagrelor (substance) | 698805004 | Ticagrelor (substance) | 1 |
| t0_row_04 | action | Procedure | Health literacy | 870552008 | Health literacy (observable entity) | 431531000124101 | Health literacy assessment (procedure) | 0 |
| t0_row_04 | action | Procedure | Preferences | 225773000 | Preferences (qualifier value) | 1156333005 | Determination of subject's care preferences (procedure) | 0 |
| t0_row_04 | action | Procedure | Requires culturally responsive service to support health literacy | 1254714002 | Requires culturally responsive service to support health literacy (finding) | 78823007 | Life support procedure (procedure) | 0 |
| t0_row_04 | action | Procedure | Social support | 315042007 | Social support (regime/therapy) | 315042007 | Social support (regime/therapy) | 1 |
| t0_row_04 | action | Procedure | Using decision making strategies | 415806002 | Using decision making strategies (finding) | 133920001 | Decision making encouragement (procedure) | 0 |
| t0_row_04 | condition | ClinicalCondition | Chronic ischemic heart disease | 413838009 | Chronic ischemic heart disease (disorder) | 413838009 | Chronic ischemic heart disease (disorder) | 1 |
| t0_row_04 | condition | ClinicalCondition | Coronary artery disease | 53741008 | Coronary arteriosclerosis (disorder) | 53741008 | Coronary arteriosclerosis (disorder) | 1 |
| t0_row_04 | condition | ClinicalCondition | Myocardial infarction | 22298006 | Myocardial infarction (disorder) | 22298006 | Myocardial infarction (disorder) | 1 |
| t0_row_04 | condition | ClinicalCondition | Old myocardial infarction | 1755008 | Old myocardial infarction (disorder) | 1755008 | Old myocardial infarction (disorder) | 1 |
| t0_row_04 | condition | Medication | Drug therapy with explicit context | 1290126002 | Drug therapy with explicit context (situation) | 1290126002 | Drug therapy with explicit context (situation) | 1 |
| t0_row_04 | condition | Procedure | Heart revascularization | 81266008 | Heart revascularization (procedure) | 81266008 | Heart revascularization (procedure) | 1 |
| t0_row_04 | condition | Procedure | Repair of coronary artery | 415070008 | Percutaneous transluminal coronary intervention using imaging guidance with contrast (procedure) | 713689002 | Repair of coronary artery (procedure) | 0 |
| t0_row_05 | action | Medication | Substance with platelet aggregation inhibitor mechanism of action | 771452004 | Substance with platelet aggregation inhibitor mechanism of action (substance) | 771452004 | Substance with platelet aggregation inhibitor mechanism of action (substance) | 1 |
| t0_row_05 | action | Procedure | Development of care plan | 399684003 | Development of care plan (procedure) | 399684003 | Development of care plan (procedure) | 1 |
| t0_row_05 | condition | ClinicalCondition | At high risk for bleeding | 711536002 | At high risk for bleeding (finding) | 711536002 | At high risk for bleeding (finding) | 1 |
| t0_row_05 | condition | ClinicalCondition | Chronic ischemic heart disease | 413838009 | Chronic ischemic heart disease (disorder) | 413838009 | Chronic ischemic heart disease (disorder) | 1 |
| t0_row_05 | condition | ClinicalCondition | Finding of increased risk level | 1255670000 | Finding of increased risk level (finding) | 1255670000 | Finding of increased risk level (finding) | 1 |
| t0_row_05 | condition | ClinicalCondition | Myocardial ischemia | 414795007 | Myocardial ischemia (disorder) | 414795007 | Myocardial ischemia (disorder) | 1 |
| t0_row_05 | condition | Qualifier Value | Specialist multidisciplinary team | 408458006 | Specialist multidisciplinary team (qualifier value) | 408458006 | Specialist multidisciplinary team (qualifier value) | 1 |
| t0_row_06 | action | Medication | Ticagrelor | 698805004 | Ticagrelor (substance) | 698805004 | Ticagrelor (substance) | 1 |
| t0_row_06 | action | Procedure | Medical therapy | 243121000 | Medical therapy (procedure) | 243121000 | Medical therapy (procedure) | 1 |
| t0_row_06 | action | Procedure | Myocardial revascularization | 275227003 | Myocardial revascularization (procedure) | 275227003 | Myocardial revascularization (procedure) | 1 |
| t0_row_06 | condition | ClinicalCondition | Acute coronary syndrome | 394659003 | Acute coronary syndrome (disorder) | 413439005 | Acute ischemic heart disease (disorder) | 0 |
| t0_row_06 | condition | ClinicalCondition | At high risk for bleeding | 711536002 | At high risk for bleeding (finding) | 711536002 | At high risk for bleeding (finding) | 1 |
| t0_row_06 | condition | ClinicalCondition | Chronic ischemic heart disease | 413838009 | Chronic ischemic heart disease (disorder) | 413838009 | Chronic ischemic heart disease (disorder) | 1 |
| t0_row_06 | condition | ClinicalCondition | Finding of increased risk level | 1255670000 | Finding of increased risk level (finding) | 1255670000 | Finding of increased risk level (finding) | 1 |
| t0_row_06 | condition | ClinicalCondition | Myocardial ischemia | 414795007 | Myocardial ischemia (disorder) | 414795007 | Myocardial ischemia (disorder) | 1 |
| t0_row_06 | condition | ClinicalCondition | Stenosis of left coronary artery main stem | 876857001 | Stenosis of left coronary artery main stem (disorder) | 876857001 | Stenosis of left coronary artery main stem (disorder) | 1 |
| t0_row_06 | condition | ClinicalParameter | Left ventricular ejection fraction | 250908004 | Left ventricular ejection fraction (observable entity) | 250908004 | Left ventricular ejection fraction (observable entity) | 1 |
| t0_row_06 | condition | Medication | Drug therapy with explicit context | 1290126002 | Drug therapy with explicit context (situation) | 1290126002 | Drug therapy with explicit context (situation) | 1 |
| t0_row_06 | condition | Medication | Ticagrelor | 698805004 | Ticagrelor (substance) | 698805004 | Ticagrelor (substance) | 1 |
| t0_row_06 | condition | Procedure | Percutaneous coronary revascularization | 415070008 | Percutaneous transluminal coronary intervention using imaging guidance with contrast (procedure) | 415070008 | Percutaneous transluminal coronary intervention using imaging guidance with contrast (procedure) | 1 |
| t0_row_07 | action | Procedure | Medical therapy | 243121000 | Medical therapy (procedure) | 243121000 | Medical therapy (procedure) | 1 |
| t0_row_07 | action | Procedure | Myocardial revascularization | 275227003 | Myocardial revascularization (procedure) | 275227003 | Myocardial revascularization (procedure) | 1 |
| t0_row_07 | condition | ClinicalCondition | Chronic ischemic heart disease | 413838009 | Chronic ischemic heart disease (disorder) | 413838009 | Chronic ischemic heart disease (disorder) | 1 |
| t0_row_07 | condition | ClinicalCondition | Triple vessel disease of the heart | 233817007 | Triple vessel disease of the heart (disorder) |  |  | 0 |
| t0_row_07 | condition | ClinicalParameter | Left ventricular ejection fraction | 250908004 | Left ventricular ejection fraction (observable entity) | 250908004 | Left ventricular ejection fraction (observable entity) | 1 |
| t0_row_08 | action | Procedure | Medical therapy | 243121000 | Medical therapy (procedure) | 243121000 | Medical therapy (procedure) | 1 |
| t0_row_08 | action | Procedure | Myocardial revascularization | 275227003 | Myocardial revascularization (procedure) | 275227003 | Myocardial revascularization (procedure) | 1 |
| t0_row_08 | condition | ClinicalCondition | Atherosclerosis of proximal portion of anterior descending branch of left coronary artery | 1366501001 | Atherosclerosis of proximal portion of anterior descending branch of left coronary artery (disorder) | 1366501001 | Atherosclerosis of proximal portion of anterior descending branch of left coronary artery (disorder) | 1 |
| t0_row_08 | condition | ClinicalCondition | Chronic ischemic heart disease | 413838009 | Chronic ischemic heart disease (disorder) | 413838009 | Chronic ischemic heart disease (disorder) | 1 |
| t0_row_08 | condition | ClinicalCondition | Double coronary vessel disease | 194843003 | Double coronary vessel disease (disorder) | 50570003 | Aneurysm of coronary vessels (disorder) | 0 |
| t0_row_08 | condition | ClinicalCondition | Single coronary vessel disease | 194842008 | Single coronary vessel disease (disorder) | 50570003 | Aneurysm of coronary vessels (disorder) | 0 |
| t0_row_08 | condition | ClinicalParameter | Left ventricular ejection fraction | 250908004 | Left ventricular ejection fraction (observable entity) | 250908004 | Left ventricular ejection fraction (observable entity) | 1 |
| t0_row_09 | action | Procedure | Angiography of coronary artery | 33367005 | Angiography of coronary artery (procedure) | 33367005 | Angiography of coronary artery (procedure) | 1 |
| t0_row_09 | action | Procedure | Medical therapy | 243121000 | Medical therapy (procedure) | 243121000 | Medical therapy (procedure) | 1 |
| t0_row_09 | action | Procedure | Myocardial revascularization | 275227003 | Myocardial revascularization (procedure) | 275227003 | Myocardial revascularization (procedure) | 1 |
| t0_row_09 | action | Procedure | Therapeutic evaluation (procedure) | 110463001 | Therapeutic evaluation (procedure) | 110463001 | Therapeutic evaluation (procedure) | 1 |
| t0_row_09 | condition | ClinicalCondition | Chronic ischemic heart disease | 413838009 | Chronic ischemic heart disease (disorder) | 413838009 | Chronic ischemic heart disease (disorder) | 1 |
| t0_row_09 | condition | ClinicalParameter | Left ventricular ejection fraction | 250908004 | Left ventricular ejection fraction (observable entity) | 250908004 | Left ventricular ejection fraction (observable entity) | 1 |
| t0_row_10 | action | Procedure | Coronary artery bypass grafting | 232717009 | Coronary artery bypass grafting (procedure) | 232719007 | Coronary artery bypass graft x 1 (procedure) | 0 |
| t0_row_10 | condition | ClinicalCondition | Chronic ischemic heart disease | 413838009 | Chronic ischemic heart disease (disorder) | 413838009 | Chronic ischemic heart disease (disorder) | 1 |
| t0_row_10 | condition | ClinicalCondition | Medically fit for surgery | 713671003 | Medically fit for surgery (finding) | 713671003 | Medically fit for surgery (finding) | 1 |
| t0_row_10 | condition | ClinicalCondition | Multi vessel coronary artery disease | 371803003 | Multi vessel coronary artery disease (disorder) | 50570003 | Aneurysm of coronary vessels (disorder) | 0 |
| t0_row_10 | condition | ClinicalParameter | Left ventricular ejection fraction | 250908004 | Left ventricular ejection fraction (observable entity) | 250908004 | Left ventricular ejection fraction (observable entity) | 1 |
| t0_row_11 | action | Procedure | Percutaneous coronary revascularization | 415070008 | Percutaneous transluminal coronary intervention using imaging guidance with contrast (procedure) | 415070008 | Percutaneous transluminal coronary intervention using imaging guidance with contrast (procedure) | 1 |
| t0_row_11 | condition | ClinicalCondition | Chronic ischemic heart disease | 413838009 | Chronic ischemic heart disease (disorder) | 413838009 | Chronic ischemic heart disease (disorder) | 1 |
| t0_row_11 | condition | ClinicalCondition | High risk | 723509005 | High risk (qualifier value) | 161640005 | At high risk for heart disease (finding) | 0 |
| t0_row_11 | condition | ClinicalCondition | Inoperable | 74778001 | Inoperable (qualifier value) |  |  | 0 |
| t0_row_11 | condition | ClinicalCondition | Multi vessel coronary artery disease | 371803003 | Multi vessel coronary artery disease (disorder) | 50570003 | Aneurysm of coronary vessels (disorder) | 0 |
| t0_row_11 | condition | ClinicalParameter | Left ventricular ejection fraction | 250908004 | Left ventricular ejection fraction (observable entity) | 250908004 | Left ventricular ejection fraction (observable entity) | 1 |
| t0_row_12 | action | Procedure | Myocardial revascularization | 275227003 | Myocardial revascularization (procedure) | 275227003 | Myocardial revascularization (procedure) | 1 |
| t0_row_12 | condition | ClinicalCondition | Angina pectoris | 194828000 | Angina (disorder) | 194828000 | Angina (disorder) | 1 |
| t0_row_12 | condition | ClinicalCondition | Anginal equivalent | 565394081000119105 | Anginal equivalent (finding) | 565394081000119105 | Anginal equivalent (finding) | 1 |
| t0_row_12 | condition | ClinicalCondition | Chronic ischemic heart disease | 413838009 | Chronic ischemic heart disease (disorder) | 413838009 | Chronic ischemic heart disease (disorder) | 1 |
| t0_row_12 | condition | ClinicalCondition | Medical therapy | 243121000 | Medical therapy (procedure) | 425914008 | Adjustment reaction to medical therapy (disorder) | 0 |
| t0_row_13 | action | Procedure | Therapeutic evaluation (procedure) | 110463001 | Therapeutic evaluation (procedure) | 110463001 | Therapeutic evaluation (procedure) | 1 |
| t0_row_13 | action | Procedure | Using decision making strategies | 415806002 | Using decision making strategies (finding) | 133920001 | Decision making encouragement (procedure) | 0 |
| t0_row_13 | condition | ClinicalCondition | Coronary artery disease | 53741008 | Coronary arteriosclerosis (disorder) | 53741008 | Coronary arteriosclerosis (disorder) | 1 |
| t0_row_13 | condition | ClinicalCondition | Myocardial revascularization | 275227003 | Myocardial revascularization (procedure) | 57809008 | Myocardial disease (disorder) | 0 |
| t0_row_14 | action | Procedure | Society of Thoracic Surgeons risk calculator | 448586003 | Society of Thoracic Surgeons risk calculator (assessment scale) | 763243004 | Assessment using QRISK cardiovascular disease 10 year risk calculator (procedure) | 0 |
| t0_row_14 | condition | Procedure | Coronary artery bypass grafting | 232717009 | Coronary artery bypass grafting (procedure) | 232719007 | Coronary artery bypass graft x 1 (procedure) | 0 |
| t0_row_15 | action | Procedure | Assessment score | 782487009 | Assessment score (observable entity) | 1003700002 | Assessment using Sequential Organ Failure Assessment score (procedure) | 0 |
| t0_row_15 | condition | ClinicalCondition | Multi vessel coronary artery disease | 371803003 | Multi vessel coronary artery disease (disorder) | 50570003 | Aneurysm of coronary vessels (disorder) | 0 |
| t0_row_16 | action | Procedure | Intravascular ultrasound of artery | 241467003 | Intravascular ultrasound of artery (procedure) | 241467003 | Intravascular ultrasound of artery (procedure) | 1 |
| t0_row_16 | action | Procedure | Optical coherence tomography | 392010000 | Optical coherence tomography (procedure) | 392010000 | Optical coherence tomography (procedure) | 1 |
| t0_row_16 | condition | ClinicalCondition | Lesion | 52988006 | Lesion (morphologic abnormality) | 7870007 | Vascular lesion of cord (disorder) | 0 |
| t0_row_16 | condition | ClinicalCondition | Stenosis of left coronary artery main stem | 876857001 | Stenosis of left coronary artery main stem (disorder) | 876857001 | Stenosis of left coronary artery main stem (disorder) | 1 |
| t0_row_16 | condition | Procedure | Percutaneous coronary revascularization | 415070008 | Percutaneous transluminal coronary intervention using imaging guidance with contrast (procedure) | 415070008 | Percutaneous transluminal coronary intervention using imaging guidance with contrast (procedure) | 1 |
| t0_row_17 | action | Procedure | Angiography of coronary artery | 33367005 | Angiography of coronary artery (procedure) | 33367005 | Angiography of coronary artery (procedure) | 1 |
| t0_row_17 | action | Procedure | Intracoronary pressure guide wire | 371789009 | Intracoronary pressure guide wire (physical object) | 431558000 | Insertion of cardiac pressure wire using fluoroscopic guidance (procedure) | 0 |
| t0_row_17 | condition | ClinicalCondition | Multi vessel coronary artery disease | 371803003 | Multi vessel coronary artery disease (disorder) | 50570003 | Aneurysm of coronary vessels (disorder) | 0 |
| t0_row_17 | condition | Procedure | Procedure | 71388002 | Procedure (procedure) | 71388002 | Procedure (procedure) | 1 |
| t0_row_18 | action | Procedure | Angiography of coronary artery | 33367005 | Angiography of coronary artery (procedure) | 33367005 | Angiography of coronary artery (procedure) | 1 |
| t0_row_18 | action | Procedure | Intracoronary pressure guide wire | 371789009 | Intracoronary pressure guide wire (physical object) | 431558000 | Insertion of cardiac pressure wire using fluoroscopic guidance (procedure) | 0 |
| t0_row_18 | condition | ClinicalCondition | Chronic ischemic heart disease | 413838009 | Chronic ischemic heart disease (disorder) | 413838009 | Chronic ischemic heart disease (disorder) | 1 |
| t0_row_18 | condition | Procedure | Myocardial revascularization | 275227003 | Myocardial revascularization (procedure) | 275227003 | Myocardial revascularization (procedure) | 1 |
| t0_row_19 | action | Procedure | Angiography of coronary artery | 33367005 | Angiography of coronary artery (procedure) | 33367005 | Angiography of coronary artery (procedure) | 1 |
| t0_row_19 | action | Procedure | Intracoronary pressure guide wire | 371789009 | Intracoronary pressure guide wire (physical object) | 431558000 | Insertion of cardiac pressure wire using fluoroscopic guidance (procedure) | 0 |
| t0_row_19 | condition | ClinicalCondition | Chronic ischemic heart disease | 413838009 | Chronic ischemic heart disease (disorder) | 413838009 | Chronic ischemic heart disease (disorder) | 1 |
| t0_row_19 | condition | Procedure | Myocardial revascularization | 275227003 | Myocardial revascularization (procedure) | 275227003 | Myocardial revascularization (procedure) | 1 |

## Table 1

| row_id | side | role | term | gold_snomed_id | gold_concept_term | pred_snomed_id | pred_concept_term | hit |
|---|---|---|---|---:|---|---:|---|---:|
| t1_row_01 | action | Medication | Aspirin | 387458008 | Aspirin (substance) | 387458008 | Aspirin (substance) | 1 |
| t1_row_01 | action | Medication | Clopidogrel | 386952008 | Clopidogrel (substance) | 386952008 | Clopidogrel (substance) | 1 |
| t1_row_01 | action | Procedure | Coronary artery structure | 41801008 | Coronary artery structure (body structure) | 294002 | Excisional biopsy of joint structure of spine (procedure) | 0 |
| t1_row_01 | action | Procedure | General characteristic of patient | 363789004 | General characteristic of patient (observable entity) | 7922000 | General treatment (procedure) | 0 |
| t1_row_01 | action | Procedure | Left ventricular ejection fraction | 250908004 | Left ventricular ejection fraction (observable entity) | 46258004 | Determination of ventricular ejection fraction with probe technique (procedure) | 0 |
| t1_row_01 | action | Procedure | Likely outcome | 410596003 | Likely outcome (qualifier value) | 20481000 | Determination of prognosis (procedure) | 0 |
| t1_row_01 | action | Procedure | Preferences | 225773000 | Preferences (qualifier value) | 1156333005 | Determination of subject's care preferences (procedure) | 0 |
| t1_row_01 | condition | ClinicalCondition | Chronic ischemic heart disease | 413838009 | Chronic ischemic heart disease (disorder) | 413838009 | Chronic ischemic heart disease (disorder) | 1 |
| t1_row_01 | condition | ClinicalCondition | Indication of | 230165009 | Indication of (contextual qualifier) (qualifier value) | 230165009 | Indication of (contextual qualifier) (qualifier value) | 1 |
| t1_row_01 | condition | ClinicalCondition | Use of anticoagulation | 260678004 | Use of anticoagulation (attribute) | 260678004 | Use of anticoagulation (attribute) | 1 |
| t1_row_01 | condition | Procedure | Myocardial revascularization | 275227003 | Myocardial revascularization (procedure) | 275227003 | Myocardial revascularization (procedure) | 1 |
| t1_row_01 | condition | Procedure | Percutaneous coronary revascularization | 415070008 | Percutaneous transluminal coronary intervention using imaging guidance with contrast (procedure) | 415070008 | Percutaneous transluminal coronary intervention using imaging guidance with contrast (procedure) | 1 |
| t1_row_02 | action | Medication | Drug therapy with explicit context | 1290126002 | Drug therapy with explicit context (situation) | 1290126002 | Drug therapy with explicit context (situation) | 1 |
| t1_row_02 | action | Medication | Platelet aggregation inhibitor therapy | 840595002 | Platelet aggregation inhibitor therapy (procedure) | 840595002 | Platelet aggregation inhibitor therapy (procedure) | 1 |
| t1_row_02 | condition | ClinicalCondition | At high risk for bleeding | 711536002 | At high risk for bleeding (finding) | 711536002 | At high risk for bleeding (finding) | 1 |
| t1_row_02 | condition | ClinicalCondition | Chronic ischemic heart disease | 413838009 | Chronic ischemic heart disease (disorder) | 413838009 | Chronic ischemic heart disease (disorder) | 1 |
| t1_row_02 | condition | ClinicalCondition | Finding of increased risk level | 1255670000 | Finding of increased risk level (finding) | 1255670000 | Finding of increased risk level (finding) | 1 |
| t1_row_02 | condition | ClinicalCondition | Indication of | 230165009 | Indication of (contextual qualifier) (qualifier value) | 230165009 | Indication of (contextual qualifier) (qualifier value) | 1 |
| t1_row_02 | condition | ClinicalCondition | Myocardial ischemia | 414795007 | Myocardial ischemia (disorder) | 414795007 | Myocardial ischemia (disorder) | 1 |
| t1_row_02 | condition | ClinicalCondition | Use of anticoagulation | 260678004 | Use of anticoagulation (attribute) | 260678004 | Use of anticoagulation (attribute) | 1 |
| t1_row_02 | condition | Procedure | Percutaneous coronary revascularization | 415070008 | Percutaneous transluminal coronary intervention using imaging guidance with contrast (procedure) | 415070008 | Percutaneous transluminal coronary intervention using imaging guidance with contrast (procedure) | 1 |
| t1_row_03 | action | Medication | Drug therapy with explicit context | 1290126002 | Drug therapy with explicit context (situation) | 1290126002 | Drug therapy with explicit context (situation) | 1 |
| t1_row_03 | condition | ClinicalCondition | At high risk for bleeding | 711536002 | At high risk for bleeding (finding) | 711536002 | At high risk for bleeding (finding) | 1 |
| t1_row_03 | condition | ClinicalCondition | Chronic ischemic heart disease | 413838009 | Chronic ischemic heart disease (disorder) | 413838009 | Chronic ischemic heart disease (disorder) | 1 |
| t1_row_03 | condition | ClinicalCondition | Finding of increased risk level | 1255670000 | Finding of increased risk level (finding) | 1255670000 | Finding of increased risk level (finding) | 1 |
| t1_row_03 | condition | ClinicalCondition | Indication of | 230165009 | Indication of (contextual qualifier) (qualifier value) | 230165009 | Indication of (contextual qualifier) (qualifier value) | 1 |
| t1_row_03 | condition | ClinicalCondition | Myocardial ischemia | 414795007 | Myocardial ischemia (disorder) | 414795007 | Myocardial ischemia (disorder) | 1 |
| t1_row_03 | condition | ClinicalCondition | Use of anticoagulation | 260678004 | Use of anticoagulation (attribute) | 260678004 | Use of anticoagulation (attribute) | 1 |
| t1_row_03 | condition | Procedure | Percutaneous coronary revascularization | 415070008 | Percutaneous transluminal coronary intervention using imaging guidance with contrast (procedure) | 415070008 | Percutaneous transluminal coronary intervention using imaging guidance with contrast (procedure) | 1 |
| t1_row_04 | action | Medication | Prasugrel | 443129001 | Prasugrel (substance) | 443129001 | Prasugrel (substance) | 1 |
| t1_row_04 | action | Medication | Ticagrelor | 698805004 | Ticagrelor (substance) | 698805004 | Ticagrelor (substance) | 1 |
| t1_row_04 | condition | ClinicalCondition | Chronic ischemic heart disease | 413838009 | Chronic ischemic heart disease (disorder) | 413838009 | Chronic ischemic heart disease (disorder) | 1 |
| t1_row_04 | condition | ClinicalCondition | Indication of | 230165009 | Indication of (contextual qualifier) (qualifier value) | 230165009 | Indication of (contextual qualifier) (qualifier value) | 1 |
| t1_row_04 | condition | ClinicalCondition | Use of anticoagulation | 260678004 | Use of anticoagulation (attribute) | 260678004 | Use of anticoagulation (attribute) | 1 |
| t1_row_04 | condition | Procedure | Finding of increased risk level | 1255670000 | Finding of increased risk level (finding) | 48696000 | Provocative test for increased intraocular pressure for glaucoma (procedure) | 0 |
| t1_row_04 | condition | Procedure | Placement of stent in coronary artery | 36969009 | Placement of stent in coronary artery (procedure) | 36969009 | Placement of stent in coronary artery (procedure) | 1 |
| t1_row_05 | action | Medication | Direct acting anticoagulant | 372636002 | Direct acting anticoagulant (substance) | 372636002 | Direct acting anticoagulant (substance) | 1 |
| t1_row_05 | action | Medication | Indirect acting anticoagulant | 419847008 | Indirect acting anticoagulant (substance) | 419847008 | Indirect acting anticoagulant (substance) | 1 |
| t1_row_05 | condition | ClinicalCondition | Chronic ischemic heart disease | 413838009 | Chronic ischemic heart disease (disorder) | 413838009 | Chronic ischemic heart disease (disorder) | 1 |
| t1_row_05 | condition | ClinicalCondition | Indication of | 230165009 | Indication of (contextual qualifier) (qualifier value) | 230165009 | Indication of (contextual qualifier) (qualifier value) | 1 |
| t1_row_05 | condition | ClinicalCondition | Use of anticoagulation | 260678004 | Use of anticoagulation (attribute) | 260678004 | Use of anticoagulation (attribute) | 1 |
| t1_row_06 | action | Medication | Aspirin | 387458008 | Aspirin (substance) | 387458008 | Aspirin (substance) | 1 |
| t1_row_06 | condition | ClinicalCondition | Chronic ischemic heart disease | 413838009 | Chronic ischemic heart disease (disorder) | 413838009 | Chronic ischemic heart disease (disorder) | 1 |
| t1_row_06 | condition | ClinicalCondition | Indication of | 230165009 | Indication of (contextual qualifier) (qualifier value) | 230165009 | Indication of (contextual qualifier) (qualifier value) | 1 |
| t1_row_06 | condition | ClinicalCondition | Use of anticoagulation | 260678004 | Use of anticoagulation (attribute) | 260678004 | Use of anticoagulation (attribute) | 1 |
| t1_row_06 | condition | Procedure | Percutaneous coronary revascularization | 415070008 | Percutaneous transluminal coronary intervention using imaging guidance with contrast (procedure) | 415070008 | Percutaneous transluminal coronary intervention using imaging guidance with contrast (procedure) | 1 |
| t1_row_07 | action | Medication | Direct acting anticoagulant | 372636002 | Direct acting anticoagulant (substance) | 372636002 | Direct acting anticoagulant (substance) | 1 |
| t1_row_07 | condition | ClinicalCondition | Chronic ischemic heart disease | 413838009 | Chronic ischemic heart disease (disorder) | 413838009 | Chronic ischemic heart disease (disorder) | 1 |
| t1_row_07 | condition | ClinicalCondition | Indication of | 230165009 | Indication of (contextual qualifier) (qualifier value) | 230165009 | Indication of (contextual qualifier) (qualifier value) | 1 |
| t1_row_07 | condition | ClinicalCondition | Use of anticoagulation | 260678004 | Use of anticoagulation (attribute) | 260678004 | Use of anticoagulation (attribute) | 1 |
| t1_row_07 | condition | Procedure | Percutaneous coronary revascularization | 415070008 | Percutaneous transluminal coronary intervention using imaging guidance with contrast (procedure) | 415070008 | Percutaneous transluminal coronary intervention using imaging guidance with contrast (procedure) | 1 |
| t1_row_08 | action | Medication | Aspirin | 387458008 | Aspirin (substance) | 387458008 | Aspirin (substance) | 1 |
| t1_row_08 | action | Medication | Clopidogrel | 386952008 | Clopidogrel (substance) | 386952008 | Clopidogrel (substance) | 1 |
| t1_row_08 | action | Medication | Oral | 738956005 | Oral (intended site) | 13790009 | Product containing iron in oral dose form (medicinal product form) | 0 |
| t1_row_08 | action | Medication | Use of anticoagulation | 260678004 | Use of anticoagulation (attribute) |  |  | 0 |
| t1_row_08 | condition | ClinicalCondition | Chronic ischemic heart disease | 413838009 | Chronic ischemic heart disease (disorder) | 413838009 | Chronic ischemic heart disease (disorder) | 1 |
| t1_row_08 | condition | ClinicalCondition | Indication of | 230165009 | Indication of (contextual qualifier) (qualifier value) | 230165009 | Indication of (contextual qualifier) (qualifier value) | 1 |
| t1_row_08 | condition | ClinicalCondition | Use of anticoagulation | 260678004 | Use of anticoagulation (attribute) | 260678004 | Use of anticoagulation (attribute) | 1 |
| t1_row_08 | condition | Procedure | Percutaneous coronary revascularization | 415070008 | Percutaneous transluminal coronary intervention using imaging guidance with contrast (procedure) | 415070008 | Percutaneous transluminal coronary intervention using imaging guidance with contrast (procedure) | 1 |
| t1_row_09 | action | Medication | Aspirin | 387458008 | Aspirin (substance) | 387458008 | Aspirin (substance) | 1 |
| t1_row_09 | condition | ClinicalCondition | At high risk for bleeding | 711536002 | At high risk for bleeding (finding) | 711536002 | At high risk for bleeding (finding) | 1 |
| t1_row_09 | condition | ClinicalCondition | Chronic ischemic heart disease | 413838009 | Chronic ischemic heart disease (disorder) | 413838009 | Chronic ischemic heart disease (disorder) | 1 |
| t1_row_09 | condition | ClinicalCondition | Coronary artery structure | 41801008 | Coronary artery structure (body structure) | 53741008 | Coronary arteriosclerosis (disorder) | 0 |
| t1_row_09 | condition | ClinicalCondition | Finding of increased risk level | 1255670000 | Finding of increased risk level (finding) | 1255670000 | Finding of increased risk level (finding) | 1 |
| t1_row_09 | condition | ClinicalCondition | Indication of | 230165009 | Indication of (contextual qualifier) (qualifier value) | 230165009 | Indication of (contextual qualifier) (qualifier value) | 1 |
| t1_row_09 | condition | ClinicalCondition | Myocardial ischemia | 414795007 | Myocardial ischemia (disorder) | 414795007 | Myocardial ischemia (disorder) | 1 |
| t1_row_09 | condition | ClinicalCondition | Use of anticoagulation | 260678004 | Use of anticoagulation (attribute) | 260678004 | Use of anticoagulation (attribute) | 1 |
| t1_row_09 | condition | Procedure | Percutaneous coronary revascularization | 415070008 | Percutaneous transluminal coronary intervention using imaging guidance with contrast (procedure) | 415070008 | Percutaneous transluminal coronary intervention using imaging guidance with contrast (procedure) | 1 |
| t1_row_10 | action | Medication | Rivaroxaban | 442031002 | Rivaroxaban (substance) | 442031002 | Rivaroxaban (substance) | 1 |
| t1_row_10 | condition | ClinicalCondition | At high risk for bleeding | 711536002 | At high risk for bleeding (finding) | 711536002 | At high risk for bleeding (finding) | 1 |
| t1_row_10 | condition | ClinicalCondition | Chronic ischemic heart disease | 413838009 | Chronic ischemic heart disease (disorder) | 413838009 | Chronic ischemic heart disease (disorder) | 1 |
| t1_row_10 | condition | ClinicalCondition | Coronary artery stent thrombosis | 421327009 | Coronary artery stent thrombosis (disorder) | 398274000 | Coronary artery thrombosis (disorder) | 0 |
| t1_row_10 | condition | ClinicalCondition | Finding of increased risk level | 1255670000 | Finding of increased risk level (finding) | 1255670000 | Finding of increased risk level (finding) | 1 |
| t1_row_10 | condition | ClinicalCondition | Indication of | 230165009 | Indication of (contextual qualifier) (qualifier value) | 230165009 | Indication of (contextual qualifier) (qualifier value) | 1 |
| t1_row_10 | condition | ClinicalCondition | Ischemic stroke | 422504002 | Ischemic stroke (disorder) | 422504002 | Ischemic stroke (disorder) | 1 |
| t1_row_10 | condition | ClinicalCondition | Use of anticoagulation | 260678004 | Use of anticoagulation (attribute) | 260678004 | Use of anticoagulation (attribute) | 1 |
| t1_row_10 | condition | Procedure | Percutaneous coronary revascularization | 415070008 | Percutaneous transluminal coronary intervention using imaging guidance with contrast (procedure) | 415070008 | Percutaneous transluminal coronary intervention using imaging guidance with contrast (procedure) | 1 |
| t1_row_11 | action | string | Dabigatran | 698871007 | Dabigatran (substance) | 698871007 | Dabigatran (substance) | 1 |
| t1_row_11 | condition | ClinicalCondition | Chronic ischemic heart disease | 413838009 | Chronic ischemic heart disease (disorder) | 413838009 | Chronic ischemic heart disease (disorder) | 1 |
| t1_row_11 | condition | ClinicalCondition | Indication of | 230165009 | Indication of (contextual qualifier) (qualifier value) | 230165009 | Indication of (contextual qualifier) (qualifier value) | 1 |
| t1_row_11 | condition | ClinicalCondition | Use of anticoagulation | 260678004 | Use of anticoagulation (attribute) | 260678004 | Use of anticoagulation (attribute) | 1 |
| t1_row_11 | condition | Procedure | Percutaneous coronary revascularization | 415070008 | Percutaneous transluminal coronary intervention using imaging guidance with contrast (procedure) | 415070008 | Percutaneous transluminal coronary intervention using imaging guidance with contrast (procedure) | 1 |
| t1_row_12 | action | Medication | Indirect acting anticoagulant | 419847008 | Indirect acting anticoagulant (substance) | 419847008 | Indirect acting anticoagulant (substance) | 1 |
| t1_row_12 | condition | ClinicalCondition | Chronic ischemic heart disease | 413838009 | Chronic ischemic heart disease (disorder) | 413838009 | Chronic ischemic heart disease (disorder) | 1 |
| t1_row_12 | condition | ClinicalCondition | Indication of | 230165009 | Indication of (contextual qualifier) (qualifier value) | 230165009 | Indication of (contextual qualifier) (qualifier value) | 1 |
| t1_row_12 | condition | ClinicalCondition | Use of anticoagulation | 260678004 | Use of anticoagulation (attribute) | 260678004 | Use of anticoagulation (attribute) | 1 |
| t1_row_12 | condition | Medication | Drug therapy with explicit context | 1290126002 | Drug therapy with explicit context (situation) | 1290126002 | Drug therapy with explicit context (situation) | 1 |
| t1_row_12 | condition | Medication | Indication of | 230165009 | Indication of (contextual qualifier) (qualifier value) |  |  | 0 |
| t1_row_12 | condition | Medication | Indirect acting anticoagulant | 419847008 | Indirect acting anticoagulant (substance) | 419847008 | Indirect acting anticoagulant (substance) | 1 |
| t1_row_12 | condition | Procedure | Percutaneous coronary revascularization | 415070008 | Percutaneous transluminal coronary intervention using imaging guidance with contrast (procedure) | 415070008 | Percutaneous transluminal coronary intervention using imaging guidance with contrast (procedure) | 1 |
| t1_row_13 | action | Medication | Prasugrel | 443129001 | Prasugrel (substance) | 443129001 | Prasugrel (substance) | 1 |
| t1_row_13 | action | Medication | Ticagrelor | 698805004 | Ticagrelor (substance) | 698805004 | Ticagrelor (substance) | 1 |
| t1_row_13 | condition | ClinicalCondition | Chronic ischemic heart disease | 413838009 | Chronic ischemic heart disease (disorder) | 413838009 | Chronic ischemic heart disease (disorder) | 1 |
| t1_row_13 | condition | ClinicalCondition | Indication of | 230165009 | Indication of (contextual qualifier) (qualifier value) | 230165009 | Indication of (contextual qualifier) (qualifier value) | 1 |
| t1_row_13 | condition | ClinicalCondition | Use of anticoagulation | 260678004 | Use of anticoagulation (attribute) | 260678004 | Use of anticoagulation (attribute) | 1 |
| t1_row_13 | condition | Procedure | Percutaneous coronary revascularization | 415070008 | Percutaneous transluminal coronary intervention using imaging guidance with contrast (procedure) | 415070008 | Percutaneous transluminal coronary intervention using imaging guidance with contrast (procedure) | 1 |
| t1_row_14 | action | Medication | Aspirin | 387458008 | Aspirin (substance) | 387458008 | Aspirin (substance) | 1 |
| t1_row_14 | condition | ClinicalCondition | Chronic ischemic heart disease | 413838009 | Chronic ischemic heart disease (disorder) | 413838009 | Chronic ischemic heart disease (disorder) | 1 |
| t1_row_14 | condition | Procedure | Coronary artery bypass graft | 232717009 | Coronary artery bypass grafting (procedure) | 232717009 | Coronary artery bypass grafting (procedure) | 1 |
| t1_row_15 | action | Medication | Drug therapy with explicit context | 1290126002 | Drug therapy with explicit context (situation) | 1290126002 | Drug therapy with explicit context (situation) | 1 |
| t1_row_15 | condition | ClinicalCondition | Chronic ischemic heart disease | 413838009 | Chronic ischemic heart disease (disorder) | 413838009 | Chronic ischemic heart disease (disorder) | 1 |
| t1_row_15 | condition | Procedure | Coronary artery bypass graft | 232717009 | Coronary artery bypass grafting (procedure) | 232717009 | Coronary artery bypass grafting (procedure) | 1 |
| t1_row_16 | action | Medication | Proton pump inhibitor | 734582004 | Hydrogen/potassium adenosine triphosphatase enzyme system inhibitor (disposition) | 734582004 | Hydrogen/potassium adenosine triphosphatase enzyme system inhibitor (disposition) | 1 |
| t1_row_16 | condition | ClinicalCondition | Chronic ischemic heart disease | 413838009 | Chronic ischemic heart disease (disorder) | 413838009 | Chronic ischemic heart disease (disorder) | 1 |
| t1_row_16 | condition | string | Finding of increased risk level | 1255670000 | Finding of increased risk level (finding) | 1255670000 | Finding of increased risk level (finding) | 1 |
| t1_row_16 | condition | string | Gastrointestinal hemorrhage | 74474003 | Gastrointestinal hemorrhage (disorder) | 74474003 | Gastrointestinal hemorrhage (disorder) | 1 |
| t1_row_17 | action | Medication | Proton pump inhibitor | 734582004 | Hydrogen/potassium adenosine triphosphatase enzyme system inhibitor (disposition) | 734582004 | Hydrogen/potassium adenosine triphosphatase enzyme system inhibitor (disposition) | 1 |
| t1_row_17 | condition | ClinicalCondition | Chronic ischemic heart disease | 413838009 | Chronic ischemic heart disease (disorder) | 413838009 | Chronic ischemic heart disease (disorder) | 1 |
| t1_row_17 | condition | Medication | Substance with platelet aggregation inhibitor mechanism of action | 771452004 | Substance with platelet aggregation inhibitor mechanism of action (substance) | 771452004 | Substance with platelet aggregation inhibitor mechanism of action (substance) | 1 |

