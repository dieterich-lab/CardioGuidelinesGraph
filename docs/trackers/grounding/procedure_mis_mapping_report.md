# Table 22 Procedure Mis-Mapping Report

This manual report tracks **Procedure-role false mappings** by run, listing exact pairs:

- source: `term`, `gold_snomed_id`, `gold_concept_term`
- wrong target: `pred_snomed_id`, `pred_concept_term`

Runs included: **628305, 628306, 628328**.

## Cross-run persistent pairs (present in all 3 runs)

| Count per run | Term | Gold | Wrong prediction |
|---:|---|---|---|
| 3 | Using decision making strategies | 415806002 — Using decision making strategies (finding) | 133920001 — Decision making encouragement (procedure) |
| 3 | Percutaneous coronary revascularization | 415070008 — Percutaneous transluminal coronary intervention using imaging guidance with contrast (procedure) | 713617008 — Percutaneous transluminal revascularization of chronic total occlusion of coronary artery using fluoroscopic guidance with contrast (procedure) |
| 3 | Intracoronary pressure guide wire | 371789009 — Intracoronary pressure guide wire (physical object) | 431558000 — Insertion of cardiac pressure wire using fluoroscopic guidance (procedure) |
| 2 | Preferences | 225773000 — Preferences (qualifier value) | 223486007 — Discussion about preferences (procedure) |
| 2 | Coronary artery bypass grafting | 232717009 — Coronary artery bypass grafting (procedure) | 868227005 — Coronary artery bypass grafting using radial artery graft (procedure) |

## Run 628305 Procedure misses

| Count | Term | Gold (id + name) | Wrong prediction (id + name) |
|---:|---|---|---|
| 3 | Intracoronary pressure guide wire | 371789009 — Intracoronary pressure guide wire (physical object) | 431558000 — Insertion of cardiac pressure wire using fluoroscopic guidance (procedure) |
| 3 | Percutaneous coronary revascularization | 415070008 — Percutaneous transluminal coronary intervention using imaging guidance with contrast (procedure) | 713617008 — Percutaneous transluminal revascularization of chronic total occlusion of coronary artery using fluoroscopic guidance with contrast (procedure) |
| 3 | Using decision making strategies | 415806002 — Using decision making strategies (finding) | 133920001 — Decision making encouragement (procedure) |
| 2 | Coronary artery bypass grafting | 232717009 — Coronary artery bypass grafting (procedure) | 868227005 — Coronary artery bypass grafting using radial artery graft (procedure) |
| 2 | Preferences | 225773000 — Preferences (qualifier value) | 1156333005 — Determination of subject's care preferences (procedure) |
| 1 | Assessment score | 782487009 — Assessment score (observable entity) | 1003700002 — Assessment using Sequential Organ Failure Assessment score (procedure) |
| 1 | Coronary artery bypass graft | 232717009 — Coronary artery bypass grafting (procedure) | 252427007 — Angiography of coronary artery bypass graft (procedure) |
| 1 | Coronary artery structure | 41801008 — Coronary artery structure (body structure) | 294002 — Excisional biopsy of joint structure of spine (procedure) |
| 1 | Decision making | 247583006 — Decision making (observable entity) | 133920001 — Decision making encouragement (procedure) |
| 1 | General characteristic of patient | 363789004 — General characteristic of patient (observable entity) | 7922000 — General treatment (procedure) |
| 1 | Health literacy | 870552008 — Health literacy (observable entity) | 431531000124101 — Health literacy assessment (procedure) |
| 1 | Left ventricular ejection fraction | 250908004 — Left ventricular ejection fraction (observable entity) | 46258004 — Determination of ventricular ejection fraction with probe technique (procedure) |
| 1 | Likely outcome | 410596003 — Likely outcome (qualifier value) | 20481000 — Determination of prognosis (procedure) |
| 1 | Procedure | 71388002 — Procedure (procedure) | 118708007 — Procedure on hand (procedure) |
| 1 | Requires culturally responsive service to support health literacy | 1254714002 — Requires culturally responsive service to support health literacy (finding) | 1156521001 — Education about health service (procedure) |
| 1 | Society of Thoracic Surgeons risk calculator | 448586003 — Society of Thoracic Surgeons risk calculator (assessment scale) | 305296009 — Admission by thoracic surgeon (procedure) |
| 1 | Treatment plan given | 314705003 — Treatment plan given (finding) | 55053003 — Prescription of therapeutic regimen (procedure) |

## Run 628306 Procedure misses

| Count | Term | Gold (id + name) | Wrong prediction (id + name) |
|---:|---|---|---|
| 3 | Intracoronary pressure guide wire | 371789009 — Intracoronary pressure guide wire (physical object) | 431558000 — Insertion of cardiac pressure wire using fluoroscopic guidance (procedure) |
| 3 | Percutaneous coronary revascularization | 415070008 — Percutaneous transluminal coronary intervention using imaging guidance with contrast (procedure) | 713617008 — Percutaneous transluminal revascularization of chronic total occlusion of coronary artery using fluoroscopic guidance with contrast (procedure) |
| 3 | Using decision making strategies | 415806002 — Using decision making strategies (finding) | 133920001 — Decision making encouragement (procedure) |
| 2 | Coronary artery bypass grafting | 232717009 — Coronary artery bypass grafting (procedure) | 868227005 — Coronary artery bypass grafting using radial artery graft (procedure) |
| 2 | Preferences | 225773000 — Preferences (qualifier value) | 223486007 — Discussion about preferences (procedure) |
| 1 | Assessment score | 782487009 — Assessment score (observable entity) | 1003700002 — Assessment using Sequential Organ Failure Assessment score (procedure) |
| 1 | Coronary artery bypass graft | 232717009 — Coronary artery bypass grafting (procedure) | 3546002 — Aortocoronary artery bypass graft with saphenous vein graft (procedure) |
| 1 | Coronary artery structure | 41801008 — Coronary artery structure (body structure) | 294002 — Excisional biopsy of joint structure of spine (procedure) |
| 1 | Decision making | 247583006 — Decision making (observable entity) | 133920001 — Decision making encouragement (procedure) |
| 1 | General characteristic of patient | 363789004 — General characteristic of patient (observable entity) | 7922000 — General treatment (procedure) |
| 1 | Health literacy | 870552008 — Health literacy (observable entity) | 431531000124101 — Health literacy assessment (procedure) |
| 1 | Left ventricular ejection fraction | 250908004 — Left ventricular ejection fraction (observable entity) | 46258004 — Determination of ventricular ejection fraction with probe technique (procedure) |
| 1 | Likely outcome | 410596003 — Likely outcome (qualifier value) | 20481000 — Determination of prognosis (procedure) |
| 1 | Procedure | 71388002 — Procedure (procedure) | 118708007 — Procedure on hand (procedure) |
| 1 | Requires culturally responsive service to support health literacy | 1254714002 — Requires culturally responsive service to support health literacy (finding) | 1156521001 — Education about health service (procedure) |
| 1 | Society of Thoracic Surgeons risk calculator | 448586003 — Society of Thoracic Surgeons risk calculator (assessment scale) | 305296009 — Admission by thoracic surgeon (procedure) |
| 1 | Treatment plan given | 314705003 — Treatment plan given (finding) | 55053003 — Prescription of therapeutic regimen (procedure) |

## Run 628328 Procedure misses

| Count | Term | Gold (id + name) | Wrong prediction (id + name) |
|---:|---|---|---|
| 3 | Intracoronary pressure guide wire | 371789009 — Intracoronary pressure guide wire (physical object) | 431558000 — Insertion of cardiac pressure wire using fluoroscopic guidance (procedure) |
| 3 | Percutaneous coronary revascularization | 415070008 — Percutaneous transluminal coronary intervention using imaging guidance with contrast (procedure) | 713617008 — Percutaneous transluminal revascularization of chronic total occlusion of coronary artery using fluoroscopic guidance with contrast (procedure) |
| 3 | Using decision making strategies | 415806002 — Using decision making strategies (finding) | 133920001 — Decision making encouragement (procedure) |
| 2 | Coronary artery bypass grafting | 232717009 — Coronary artery bypass grafting (procedure) | 232719007 — Coronary artery bypass graft x 1 (procedure) |
| 2 | Preferences | 225773000 — Preferences (qualifier value) | 223486007 — Discussion about preferences (procedure) |
| 1 | Assessment score | 782487009 — Assessment score (observable entity) | 1003700002 — Assessment using Sequential Organ Failure Assessment score (procedure) |
| 1 | Coronary artery structure | 41801008 — Coronary artery structure (body structure) | 294002 — Excisional biopsy of joint structure of spine (procedure) |
| 1 | Decision making | 247583006 — Decision making (observable entity) | 133920001 — Decision making encouragement (procedure) |
| 1 | General characteristic of patient | 363789004 — General characteristic of patient (observable entity) | 7922000 — General treatment (procedure) |
| 1 | Health literacy | 870552008 — Health literacy (observable entity) | 431531000124101 — Health literacy assessment (procedure) |
| 1 | Left ventricular ejection fraction | 250908004 — Left ventricular ejection fraction (observable entity) | 46258004 — Determination of ventricular ejection fraction with probe technique (procedure) |
| 1 | Likely outcome | 410596003 — Likely outcome (qualifier value) | 67407003 — Determination of outcome (procedure) |
| 1 | Procedure | 71388002 — Procedure (procedure) | 118708007 — Procedure on hand (procedure) |
| 1 | Requires culturally responsive service to support health literacy | 1254714002 — Requires culturally responsive service to support health literacy (finding) | 1156521001 — Education about health service (procedure) |
| 1 | Society of Thoracic Surgeons risk calculator | 448586003 — Society of Thoracic Surgeons risk calculator (assessment scale) | 305296009 — Admission by thoracic surgeon (procedure) |
| 1 | Treatment plan given | 314705003 — Treatment plan given (finding) | 55053003 — Prescription of therapeutic regimen (procedure) |
