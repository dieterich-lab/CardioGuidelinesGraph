# row_13 (mapped to row_14)

Original table row text (ground truth):

```json
{
  "Recommendations": "In patients with complex CAD in whom revascularization is being considered, it is recommended to assess procedural risks and post-procedural outcomes to guide shared clinical decision-making.",
  "Class a": "I",
  "Level b": "C"
}
```

Aligned JSON (expected vs actual):

<table>
  <tr>
    <th align="left">Human Annotation</th>
    <th align="left">LLM Generated</th>
  </tr>
  <tr>
    <td valign="top"><pre>
[
  {
    "conditions": [
      {
        "entity": "coronary artery disease",
        "entity_original": "patients with complex cad",
        "role": "ClinicalCondition",
        "operator": "PRESENT",
        "threshold": null,
        "unit": null,
        "context": null,
        "logic_type": "AND",
        "logic_group": "and_1",
        "strength": null,
        "level": null,
        "direction": null,
        "preferred_term": null,
        "synonyms": [],
        "snomed_id": "53741008",
        "target_label": null,
        "taxonomy_path": [],
        "root_concept_id": null,
        "root_concept_term": null
      },
      {
        "entity": "myocardial revascularization",
        "entity_original": "patients in whom revascularization is being considered",
        "role": "ClinicalCondition",
        "operator": "PRESENT",
        "threshold": null,
        "unit": null,
        "context": null,
        "logic_type": "AND",
        "logic_group": "and_1",
        "strength": null,
        "level": null,
        "direction": null,
        "preferred_term": null,
        "synonyms": [],
        "snomed_id": "275227003",
        "target_label": null,
        "taxonomy_path": [],
        "root_concept_id": null,
        "root_concept_term": null
      }
    ],
    "actions": [
      {
        "entity": "therapeutic evaluation (procedure)",
        "entity_original": "assess procedural risks",
        "role": "Procedure",
        "operator": null,
        "threshold": null,
        "unit": null,
        "context": null,
        "logic_type": null,
        "logic_group": null,
        "strength": "I",
        "level": "C",
        "direction": "POSITIVE",
        "preferred_term": null,
        "synonyms": [],
        "snomed_id": "110463001",
        "target_label": null,
        "taxonomy_path": [],
        "root_concept_id": null,
        "root_concept_term": null
      },
      {
        "entity": "therapeutic evaluation (procedure)",
        "entity_original": "assess post-procedural outcomes",
        "role": "Procedure",
        "operator": null,
        "threshold": null,
        "unit": null,
        "context": null,
        "logic_type": null,
        "logic_group": null,
        "strength": "I",
        "level": "C",
        "direction": "POSITIVE",
        "preferred_term": null,
        "synonyms": [],
        "snomed_id": "110463001",
        "target_label": null,
        "taxonomy_path": [],
        "root_concept_id": null,
        "root_concept_term": null
      },
      {
        "entity": "using decision making strategies",
        "entity_original": "take part in shared clinical decision-making",
        "role": "Procedure",
        "operator": null,
        "threshold": null,
        "unit": null,
        "context": null,
        "logic_type": null,
        "logic_group": null,
        "strength": "I",
        "level": "C",
        "direction": "POSITIVE",
        "preferred_term": null,
        "synonyms": [],
        "snomed_id": "415806002",
        "target_label": null,
        "taxonomy_path": [],
        "root_concept_id": null,
        "root_concept_term": null
      }
    ]
  }
]
</pre></td>
    <td valign="top"><pre>
{
  "rules": [
    {
      "conditions": [
        {
          "entity": "surgically eligible chronic coronary syndrome patients",
          "entity_original": "surgically eligible chronic coronary syndrome (ccs) patients",
          "role": "Condition",
          "operator": "PRESENT",
          "threshold": null,
          "unit": null,
          "context": null,
          "logic_type": "AND",
          "logic_group": "and_1",
          "strength": "Class I",
          "level": "B",
          "direction": "POSITIVE"
        },
        {
          "entity": "multivessel coronary artery disease",
          "entity_original": "multivessel coronary artery disease (cad)",
          "role": "Condition",
          "operator": "PRESENT",
          "threshold": null,
          "unit": null,
          "context": null,
          "logic_type": "AND",
          "logic_group": "and_1",
          "strength": "Class I",
          "level": "B",
          "direction": "POSITIVE"
        },
        {
          "entity": "left ventricular ejection fraction",
          "entity_original": "left ventricular ejection fraction (lvef) \u2264 35%",
          "role": "ClinicalParameter",
          "operator": "<=",
          "threshold": "35",
          "unit": "%",
          "context": null,
          "logic_type": "AND",
          "logic_group": "and_1",
          "strength": "Class I",
          "level": "B",
          "direction": "POSITIVE"
        },
        {
          "entity": "chronic coronary syndrome",
          "entity_original": "surgically eligible chronic coronary syndrome (ccs) patients",
          "role": "Condition",
          "operator": "PRESENT",
          "threshold": null,
          "unit": null,
          "context": null,
          "logic_type": "AND",
          "logic_group": "and_1",
          "strength": "Class I",
          "level": "B",
          "direction": "POSITIVE"
        },
        {
          "entity": "multivessel coronary artery disease",
          "entity_original": "multivessel coronary artery disease (cad)",
          "role": "Condition",
          "operator": "PRESENT",
          "threshold": null,
          "unit": null,
          "context": null,
          "logic_type": "AND",
          "logic_group": "and_1",
          "strength": "Class I",
          "level": "B",
          "direction": "POSITIVE"
        },
        {
          "entity": "left ventricular ejection fraction",
          "entity_original": "left ventricular ejection fraction (lvef) \u2264 35%",
          "role": "ClinicalParameter",
          "operator": "\u2264",
          "threshold": "35",
          "unit": "%",
          "context": null,
          "logic_type": "AND",
          "logic_group": "and_1",
          "strength": "Class I",
          "level": "B",
          "direction": "POSITIVE"
        }
      ],
      "actions": [
        {
          "entity": "coronary artery bypass grafting",
          "entity_original": "myocardial revascularization with coronary artery bypass grafting (cabg)",
          "role": "Procedure",
          "operator": "PRESENT",
          "threshold": null,
          "unit": null,
          "context": null,
          "logic_type": null,
          "logic_group": null,
          "strength": "Class I",
          "level": "B",
          "direction": "POSITIVE"
        }
      ]
    }
  ]
}
</pre></td>
  </tr>
</table>

Mermaid (Human Annotation):

```mermaid
graph LR
  REC[RecommendationNode]
  ACT1[Procedure: therapeutic evaluation (procedure)]
  REC -->|RECOMMENDS_PROCEDURE| ACT1
  ACT2[Procedure: therapeutic evaluation (procedure)]
  REC -->|RECOMMENDS_PROCEDURE| ACT2
  ACT3[Procedure: using decision making strategies]
  REC -->|RECOMMENDS_PROCEDURE| ACT3
  subgraph Human_and_1_AND
    D_and_1_1[DecisionNode and_1 s1]
    C_and_1_1[ClinicalCondition: coronary artery disease]
    D_and_1_1 -->|CHECKS_FOR| C_and_1_1
    D_and_1_2[DecisionNode and_1 s2]
    C_and_1_2[ClinicalCondition: myocardial revascularization]
    D_and_1_2 -->|CHECKS_FOR| C_and_1_2
    D_and_1_1 -->|LEADS_TO condition_met=true| D_and_1_2
  end
  D_and_1_2 -->|RESULTS_IN condition_met=true| REC
```

Mermaid (LLM Generated):

```mermaid
graph LR
  REC[RecommendationNode]
  ACT1[Procedure: coronary artery bypass grafting]
  REC -->|RECOMMENDS_PROCEDURE| ACT1
  subgraph LLM_and_1_AND
    D_and_1_1[DecisionNode and_1 s1]
    C_and_1_1[Condition: surgically eligible chronic coronary syndrome patients]
    D_and_1_1 -->|CHECKS_FOR| C_and_1_1
    D_and_1_2[DecisionNode and_1 s2]
    C_and_1_2[Condition: multivessel coronary artery disease]
    D_and_1_2 -->|CHECKS_FOR| C_and_1_2
    D_and_1_3[DecisionNode and_1 s3]
    C_and_1_3[ClinicalParameter: left ventricular ejection fraction]
    D_and_1_3 -->|EVALUATES| C_and_1_3
    D_and_1_4[DecisionNode and_1 s4]
    C_and_1_4[Condition: chronic coronary syndrome]
    D_and_1_4 -->|CHECKS_FOR| C_and_1_4
    D_and_1_5[DecisionNode and_1 s5]
    C_and_1_5[Condition: multivessel coronary artery disease]
    D_and_1_5 -->|CHECKS_FOR| C_and_1_5
    D_and_1_6[DecisionNode and_1 s6]
    C_and_1_6[ClinicalParameter: left ventricular ejection fraction]
    D_and_1_6 -->|EVALUATES| C_and_1_6
    D_and_1_1 -->|LEADS_TO condition_met=true| D_and_1_2
    D_and_1_2 -->|LEADS_TO condition_met=true| D_and_1_3
    D_and_1_3 -->|LEADS_TO condition_met=true| D_and_1_4
    D_and_1_4 -->|LEADS_TO condition_met=true| D_and_1_5
    D_and_1_5 -->|LEADS_TO condition_met=true| D_and_1_6
  end
  D_and_1_6 -->|RESULTS_IN condition_met=true| REC
```

Concepts:
- expected: 4
- actual: 5
- matches: 0
- missing: 4
- extra: 5

Missing concepts:
- ClinicalCondition: coronary artery disease
- ClinicalCondition: myocardial revascularization
- Procedure: therapeutic evaluation (procedure)
- Procedure: using decision making strategies

Extra concepts:
- ClinicalParameter: left ventricular ejection fraction
- Condition: chronic coronary syndrome
- Condition: multivessel coronary artery disease
- Condition: surgically eligible chronic coronary syndrome patients
- Procedure: coronary artery bypass grafting

Rules (concept + logic fields):
- expected: 4
- actual: 6
- matches: 0
- missing: 4
- extra: 6

Missing rules:
- ClinicalCondition: coronary artery disease | op=PRESENT | logic=AND | grp=and_1
- ClinicalCondition: myocardial revascularization | op=PRESENT | logic=AND | grp=and_1
- Procedure: therapeutic evaluation (procedure) | class=I | level=C | dir=POSITIVE
- Procedure: using decision making strategies | class=I | level=C | dir=POSITIVE

Extra rules:
- ClinicalParameter: left ventricular ejection fraction | op=<= | thr=35 | unit=% | logic=AND | grp=and_1 | class=Class I | level=B | dir=POSITIVE
- ClinicalParameter: left ventricular ejection fraction | op=≤ | thr=35 | unit=% | logic=AND | grp=and_1 | class=Class I | level=B | dir=POSITIVE
- Condition: chronic coronary syndrome | op=PRESENT | logic=AND | grp=and_1 | class=Class I | level=B | dir=POSITIVE
- Condition: multivessel coronary artery disease | op=PRESENT | logic=AND | grp=and_1 | class=Class I | level=B | dir=POSITIVE
- Condition: surgically eligible chronic coronary syndrome patients | op=PRESENT | logic=AND | grp=and_1 | class=Class I | level=B | dir=POSITIVE
- Procedure: coronary artery bypass grafting | op=PRESENT | class=Class I | level=B | dir=POSITIVE

