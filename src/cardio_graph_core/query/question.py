patient_cases_t8 = [
    # Rule 1 (OR split into two patients)
    "Patient with CAD and an myocardial ischemia and Finding of increased risk level",
    "Patient with symptomatic peripheral arterial disease and an myocardial ischemia and finding of increased risk level",
    # Rule 2
    "Patient with chronic coronary syndrome, prior myocardial infarction, and who has tolerated DAPT for 1 year",
    # Rule 3
    "Patient with chronic coronary syndrome, prior myocardial infarction, PCI, and who has tolerated DAPT for 1 year",
    # Rule 4
    "Patient with chronic coronary syndrome,  myocardial infarction, and who has tolerated DAPT for 1 year",
]

patient_cases_t22_1 = [
    # Table 0, Rule 1 (OR split into two patients)
    "Patient scheduled for PCI",
    "Patient scheduled for CABG",
    # Table 0, Rule 2
    "Patient with a complex disorder of the cardiovascular system",
    # Table 0, Rule 3
    "Patient for whom a Heart Team treatment proposal has been made",
    # Table 0, Rule 4
    "Patient for whom the decision for Heart revascularization is being made",
    # Table 0, Rule 5
    "Patient discussed by the Heart Team regarding treatement strategy",
]
patient_cases_t22_2 = [
    # Table 0, Rule 6
    "Patient with chronic coronary syndrome, LVEF = 40%%, and functionally significant left main stem stenosis",
    # Table 0, Rule 7
    "Patient with chronic coronary syndrome, LVEF = 40%%, and functionally significant three-vessel disease",
    # Table 0, Rule 8 (OR split into two patients)
    "Patient with chronic coronary syndrome, LVEF = 40%%, and functionally significant single-vessel disease involving the proximal LAD",
    "Patient with chronic coronary syndrome,LVEF = 40%%, and functionally significant two-vessel disease involving the proximal LAD",
    # Table 0, Rule 9
    "Patient with chronic coronary syndrome and LVEF = 30%",
    # Table 0, Rule 10
    "Surgically eligible patient with chronic coronary syndrome, multivessel coronary artery disease, and LVEF = 30%%",
]
patient_cases_t22_3 = [
    # Table 0, Rule 11 (OR split into two patients)
    "Patient with chronic coronary syndrome, functionally significant multivessel disease, LVEF = 30%%, and high surgical risk",
    "Patient with chronic coronary syndrome, functionally significant multivessel disease, LVEF = 20%%, and who is inoperable",
    # Table 0, Rule 12 (OR split into two patients)
    "Patient with chronic coronary syndrome and persistent angina despite guideline-directed medical treatment",
    "Patient with chronic coronary syndrome and an anginal equivalent despite guideline-directed medical treatment",
    # Table 0, Rule 13
    "Patient with complex coronary artery disease in whom myocardial revascularization is being considered",
    # Table 0, Rule 14
    "Patient undergoing coronary artery bypass grafting",
    # Table 0, Rule 15
    "Patient with multivessel obstructive coronary artery disease",
]
patient_cases_t22_4 = [
    # Table 0, Rule 16 (OR split into four patients)
    "Patient undergoing PCI for anatomically complex lesions",
    "Patient undergoing PCI for left main stem lesions",
    "Patient undergoing PCI for true bifurcation lesions",
    "Patient undergoing PCI for long lesions",
    # Table 0, Rule 17
    "Patient with multivessel disease undergoing a cardiovascular intervention",
    # Table 0, Rule 18
    "Patient with chronic coronary syndrome at the end of revascularization",
    # Table 0, Rule 19
    "Patient with chronic coronary syndrome at the end of revascularization",
    # Table 1, Rule 1
    "Patient with chronic coronary syndrome where intervention is being considered",
]

patient_cases_t17_1 = [
    # Table 0, Rule 1 (OR split into two patients)
    "Patient with chronic coronary syndrome and prior myocardial infarction",
    "Patient with chronic coronary syndrome and PCI",
    # Table 0, Rule 2 (OR split into two patients)
    "Patient with chronic coronary syndrome and prior myocardial infarction",
    "Patient with chronic coronary syndrome and PCI",
    # Table 0, Rule 3
    "Patient with chronic coronary syndrome after coronary artery bypass grafting",
    # Table 0, Rule 4
    "Patient with chronic coronary syndrome, no prior myocardial infarction, no prior coronary revascularization, and significant obstructive CAD",
    # Table 0, Rule 5
    "Patient with chronic coronary syndrome, Myocardial ischaemia, finding of increased risk level, and no high bleeding risk",
]
patient_cases_t17_2 = [
    # Table 0, Rule 6 (OR split into two patients)
    "Patient with chronic coronary syndrome, after PCI, initially treated with  DAPT including ticagrelor, at high ischaemic risk, and no high bleeding risk",
    "Stabilized post-acute coronary syndrome patient, after PCI, initially treated with  DAPT including ticagrelor, at high ischaemic risk, and no high bleeding risk",
    # Table 1, Rule 1
    "Patient with chronic coronary syndrome, (no indication for oral anticoagulation), and after PCI",
    # Table 1, Rule 2
    "Patient with chronic coronary syndrome, (no indication for oral anticoagulation), PCI, high bleeding risk, and no high ischaemic risk",
    # Table 1, Rule 3
    "Patient with chronic coronary syndrome, (no indication for oral anticoagulation), PCI, no high bleeding risk, and no high ischaemic risk",
    # Table 1, Rule 4
    "Patient with chronic coronary syndrome, (no indication for oral anticoagulation), and undergoing high thrombotic risk coronary stenting with a high risk finding",
    # Table 1, Rule 5
    "Patient with chronic coronary syndrome and a long-term indication for oral anticoagulation",
]
patient_cases_t17_3 = [
    # Table 1, Rule 6
    "Patient with chronic coronary syndrome, an indication for oral anticoagulation, and status post percutaneous coronary intervention",
    # Table 1, Rule 7
    "Patient with chronic coronary syndrome, an indication for oral anticoagulation, and status post percutaneous coronary intervention",
    # Table 1, Rule 8
    "Patient with chronic coronary syndrome, an indication for oral anticoagulation, and after uncomplicated PCI",
    # Table 1, Rule 9 (OR split into two patients)
    "Patient with chronic coronary syndrome, an indication for oral anticoagulation, after PCI, high bleeding risk, and high ischaemic risk",
    "Patient with chronic coronary syndrome, an indication for oral anticoagulation, after PCI, high bleeding risk, and anatomical or procedural characteristics judged to outweigh the bleeding risk",
    # Table 1, Rule 10 (OR split into two patients)
    "Patient with chronic coronary syndrome, an indication for oral anticoagulation, after PCI, high bleeding risk, and concern for ischaemic stroke risk",
    "Patient with chronic coronary syndrome, an indication for oral anticoagulation, after PCI, high bleeding risk, and concern for stent thrombosis risk",
]
patient_cases_t17_4 = [
    # Table 1, Rule 11
    "Patient with chronic coronary syndrome, an indication for oral anticoagulation, and status post percutaneous coronary intervention",
    # Table 1, Rule 12
    "Patient with chronic coronary syndrome, an indication for oral anticoagulation, after PCI, with an indication for vitamin K antagonist therapy, and receiving single or DAPT",
    # Table 1, Rule 13
    "Patient with chronic coronary syndrome, an indication for oral anticoagulation, and status post percutaneous coronary intervention",
    # Table 1, Rule 14
    "Patient with chronic coronary syndrome after coronary artery bypass grafting",
    # Table 1, Rule 15
    "Patient with chronic coronary syndrome after coronary artery bypass grafting",
    # Table 1, Rule 16
    "Patient with chronic coronary syndrome and increased risk of gastrointestinal hemorrhage",
    # Table 1, Rule 17
    "Patient with chronic coronary syndrome receiving a single antithrombotic agent",
]

wrong_cases = [
    # Table 0, Rule 7
    "Patient with chronic coronary syndrome, LVEF = 40%%, and functionally significant three-vessel disease",
    # Table 0, Rule 8 (OR split into two patients)
    "Patient with chronic coronary syndrome, LVEF = 40%%, and functionally significant single-vessel disease involving the proximal LAD",
    "Patient with chronic coronary syndrome,LVEF = 40%%, and functionally significant two-vessel disease involving the proximal LAD",
    # Table 0, Rule 11 (OR split into two patients)
    "Patient with chronic coronary syndrome, functionally significant multivessel disease, LVEF = 30%%, and high surgical risk",
    "Patient with chronic coronary syndrome, functionally significant multivessel disease, LVEF = 20%%, and who is inoperable",
    # Table 0, Rule 17
    "Patient with multivessel disease undergoing a cardiovascular intervention",
    # Table 1, Rule 1
    "Patient with chronic coronary syndrome where intervention is being considered",
]

wrong_cases_2 = []

triple_batch = [
    patient_cases_t8,
    patient_cases_t17_1,
    patient_cases_t17_2,
    patient_cases_t17_3,
    patient_cases_t17_4,
    patient_cases_t22_1,
    patient_cases_t22_2,
    patient_cases_t22_3,
    patient_cases_t22_4,
    wrong_cases,
]

base_batch = [
    patient_cases_t8,
    patient_cases_t17_1,
    patient_cases_t17_2,
    patient_cases_t17_3,
    patient_cases_t17_4,
    patient_cases_t22_1,
    patient_cases_t22_2,
    patient_cases_t22_3,
    patient_cases_t22_4,
]
