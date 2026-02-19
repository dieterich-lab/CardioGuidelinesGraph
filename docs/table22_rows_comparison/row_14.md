# row_14 (mapped to row_15)

Original table row text (ground truth):

```json
{
  "Recommendations": "Calculation of the STS score is recommended to estimate in-hospital morbidity and 30-day mortality after CABG. 777,862-864",
  "Class a": "I",
  "Level b": "B"
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
        "entity": "cabg",
        "entity_original": "cabg",
        "role": "Procedure",
        "operator": "PRESENT",
        "threshold": null,
        "unit": null,
        "context": null,
        "logic_type": "AND",
        "logic_group": "and_1",
        "strength": null,
        "level": null,
        "direction": null
      }
    ],
    "actions": [
      {
        "entity": "sts score",
        "entity_original": "calculation of the sts score to estimate in-hospital morbidity and 30-day mortality after cabg",
        "role": "ClinicalAction",
        "operator": null,
        "threshold": null,
        "unit": null,
        "context": null,
        "logic_type": null,
        "logic_group": null,
        "strength": "I",
        "level": "B",
        "direction": "POSITIVE"
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
          "entity": "chronic coronary syndrome patients with functionally significant multivessel disease",
          "entity_original": "chronic coronary syndrome patients with functionally significant multivessel disease",
          "role": "Condition",
          "operator": "PRESENT",
          "threshold": null,
          "unit": null,
          "context": null,
          "logic_type": "AND",
          "logic_group": "and_1",
          "strength": "Class IIb",
          "level": "B",
          "direction": "POSITIVE",
          "preferred_term": null,
          "synonyms": [],
          "snomed_id": null,
          "target_label": null,
          "taxonomy_path": [],
          "root_concept_id": null,
          "root_concept_term": null
        },
        {
          "entity": "left ventricular ejection fraction",
          "entity_original": "left ventricular ejection fraction",
          "role": "ClinicalParameter",
          "operator": "<=",
          "threshold": "35",
          "unit": "%",
          "context": null,
          "logic_type": "AND",
          "logic_group": "and_1",
          "strength": "Class IIb",
          "level": "B",
          "direction": "POSITIVE",
          "preferred_term": null,
          "synonyms": [],
          "snomed_id": null,
          "target_label": null,
          "taxonomy_path": [],
          "root_concept_id": null,
          "root_concept_term": null
        },
        {
          "entity": "high surgical risk",
          "entity_original": "high surgical risk or not operable",
          "role": "Condition",
          "operator": "PRESENT",
          "threshold": null,
          "unit": null,
          "context": null,
          "logic_type": "OR",
          "logic_group": "or_1",
          "strength": "Class IIb",
          "level": "B",
          "direction": "POSITIVE",
          "preferred_term": null,
          "synonyms": [],
          "snomed_id": null,
          "target_label": null,
          "taxonomy_path": [],
          "root_concept_id": null,
          "root_concept_term": null
        },
        {
          "entity": "not operable",
          "entity_original": "high surgical risk or not operable",
          "role": "Condition",
          "operator": "PRESENT",
          "threshold": null,
          "unit": null,
          "context": null,
          "logic_type": "OR",
          "logic_group": "or_1",
          "strength": "Class IIb",
          "level": "B",
          "direction": "POSITIVE",
          "preferred_term": null,
          "synonyms": [],
          "snomed_id": null,
          "target_label": null,
          "taxonomy_path": [],
          "root_concept_id": null,
          "root_concept_term": null
        },
        {
          "entity": "chronic coronary syndrome",
          "entity_original": "chronic coronary syndrome (ccs)",
          "role": "Condition",
          "operator": "PRESENT",
          "threshold": null,
          "unit": null,
          "context": null,
          "logic_type": "AND",
          "logic_group": "and_1",
          "strength": "Class IIb",
          "level": "B",
          "direction": "UNKNOWN",
          "preferred_term": null,
          "synonyms": [],
          "snomed_id": null,
          "target_label": null,
          "taxonomy_path": [],
          "root_concept_id": null,
          "root_concept_term": null
        },
        {
          "entity": "multivessel disease",
          "entity_original": "multivessel disease (mvd)",
          "role": "Condition",
          "operator": "PRESENT",
          "threshold": null,
          "unit": null,
          "context": null,
          "logic_type": "AND",
          "logic_group": "and_1",
          "strength": "Class IIb",
          "level": "B",
          "direction": "UNKNOWN",
          "preferred_term": null,
          "synonyms": [],
          "snomed_id": null,
          "target_label": null,
          "taxonomy_path": [],
          "root_concept_id": null,
          "root_concept_term": null
        },
        {
          "entity": "left ventricular ejection fraction",
          "entity_original": "left ventricular ejection fraction (lvef) \u2264 35%",
          "role": "ClinicalParameter",
          "operator": "LE",
          "threshold": "35",
          "unit": "%",
          "context": null,
          "logic_type": "AND",
          "logic_group": "and_1",
          "strength": "Class IIb",
          "level": "B",
          "direction": "UNKNOWN",
          "preferred_term": null,
          "synonyms": [],
          "snomed_id": null,
          "target_label": null,
          "taxonomy_path": [],
          "root_concept_id": null,
          "root_concept_term": null
        },
        {
          "entity": "high surgical risk",
          "entity_original": "high surgical risk",
          "role": "Condition",
          "operator": "PRESENT",
          "threshold": null,
          "unit": null,
          "context": null,
          "logic_type": "AND",
          "logic_group": "and_1",
          "strength": "Class IIb",
          "level": "B",
          "direction": "UNKNOWN",
          "preferred_term": null,
          "synonyms": [],
          "snomed_id": null,
          "target_label": null,
          "taxonomy_path": [],
          "root_concept_id": null,
          "root_concept_term": null
        },
        {
          "entity": "not operable",
          "entity_original": "not operable",
          "role": "Condition",
          "operator": "PRESENT",
          "threshold": null,
          "unit": null,
          "context": null,
          "logic_type": "AND",
          "logic_group": "and_1",
          "strength": "Class IIb",
          "level": "B",
          "direction": "UNKNOWN",
          "preferred_term": null,
          "synonyms": [],
          "snomed_id": null,
          "target_label": null,
          "taxonomy_path": [],
          "root_concept_id": null,
          "root_concept_term": null
        }
      ],
      "actions": [
        {
          "entity": "percutaneous coronary intervention",
          "entity_original": "percutaneous coronary intervention",
          "role": "Procedure",
          "operator": "PRESENT",
          "threshold": null,
          "unit": null,
          "context": null,
          "logic_type": null,
          "logic_group": null,
          "strength": "Class IIb",
          "level": "B",
          "direction": "POSITIVE",
          "preferred_term": null,
          "synonyms": [],
          "snomed_id": null,
          "target_label": null,
          "taxonomy_path": [],
          "root_concept_id": null,
          "root_concept_term": null
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
  ACT1[ClinicalAction: sts score]
  REC -->|RECOMMENDS_USAGE| ACT1
  subgraph Human_and_1_AND
    D_and_1_1[DecisionNode and_1 s1]
    C_and_1_1[Procedure: cabg]
    D_and_1_1 -->|CHECKS_FOR| C_and_1_1
  end
  D_and_1_1 -->|RESULTS_IN condition_met=true| REC
```

Mermaid (LLM Generated):

```mermaid
graph LR
  REC[RecommendationNode]
  ACT1[Procedure: percutaneous coronary intervention]
  REC -->|RECOMMENDS_PROCEDURE| ACT1
  subgraph LLM_and_1_AND
    D_and_1_1[DecisionNode and_1 s1]
    C_and_1_1[Condition: chronic coronary syndrome patients with functionally significant multivessel disease]
    D_and_1_1 -->|CHECKS_FOR| C_and_1_1
    D_and_1_2[DecisionNode and_1 s2]
    C_and_1_2[ClinicalParameter: left ventricular ejection fraction]
    D_and_1_2 -->|EVALUATES| C_and_1_2
    D_and_1_3[DecisionNode and_1 s3]
    C_and_1_3[Condition: chronic coronary syndrome]
    D_and_1_3 -->|CHECKS_FOR| C_and_1_3
    D_and_1_4[DecisionNode and_1 s4]
    C_and_1_4[Condition: multivessel disease]
    D_and_1_4 -->|CHECKS_FOR| C_and_1_4
    D_and_1_5[DecisionNode and_1 s5]
    C_and_1_5[ClinicalParameter: left ventricular ejection fraction]
    D_and_1_5 -->|EVALUATES| C_and_1_5
    D_and_1_6[DecisionNode and_1 s6]
    C_and_1_6[Condition: high surgical risk]
    D_and_1_6 -->|CHECKS_FOR| C_and_1_6
    D_and_1_7[DecisionNode and_1 s7]
    C_and_1_7[Condition: not operable]
    D_and_1_7 -->|CHECKS_FOR| C_and_1_7
    D_and_1_1 -->|LEADS_TO condition_met=true| D_and_1_2
    D_and_1_2 -->|LEADS_TO condition_met=true| D_and_1_3
    D_and_1_3 -->|LEADS_TO condition_met=true| D_and_1_4
    D_and_1_4 -->|LEADS_TO condition_met=true| D_and_1_5
    D_and_1_5 -->|LEADS_TO condition_met=true| D_and_1_6
    D_and_1_6 -->|LEADS_TO condition_met=true| D_and_1_7
  end
  subgraph LLM_or_1_OR
    D_or_1_1[DecisionNode or_1 s1]
    C_or_1_1[Condition: high surgical risk]
    D_or_1_1 -->|CHECKS_FOR| C_or_1_1
    D_or_1_2[DecisionNode or_1 s2]
    C_or_1_2[Condition: not operable]
    D_or_1_2 -->|CHECKS_FOR| C_or_1_2
    D_and_1_7 -->|LEADS_TO condition_met=true| D_or_1_1
    D_and_1_7 -->|LEADS_TO condition_met=true| D_or_1_2
  end
  D_or_1_1 -->|RESULTS_IN condition_met=true| REC
  D_or_1_2 -->|RESULTS_IN condition_met=true| REC
```

Concepts:
- expected: 2
- actual: 7
- matches: 0
- missing: 2
- extra: 7

Missing concepts:
- ClinicalAction: sts score
- Procedure: cabg

Extra concepts:
- ClinicalParameter: left ventricular ejection fraction
- Condition: chronic coronary syndrome
- Condition: chronic coronary syndrome patients with functionally significant multivessel disease
- Condition: high surgical risk
- Condition: multivessel disease
- Condition: not operable
- Procedure: percutaneous coronary intervention

Rules (concept + logic fields):
- expected: 2
- actual: 10
- matches: 0
- missing: 2
- extra: 10

Missing rules:
- ClinicalAction: sts score | class=I | level=B | dir=POSITIVE
- Procedure: cabg | op=PRESENT | logic=AND | grp=and_1

Extra rules:
- ClinicalParameter: left ventricular ejection fraction | op=<= | thr=35 | unit=% | logic=AND | grp=and_1 | class=Class IIb | level=B | dir=POSITIVE
- ClinicalParameter: left ventricular ejection fraction | op=LE | thr=35 | unit=% | logic=AND | grp=and_1 | class=Class IIb | level=B | dir=UNKNOWN
- Condition: chronic coronary syndrome patients with functionally significant multivessel disease | op=PRESENT | logic=AND | grp=and_1 | class=Class IIb | level=B | dir=POSITIVE
- Condition: chronic coronary syndrome | op=PRESENT | logic=AND | grp=and_1 | class=Class IIb | level=B | dir=UNKNOWN
- Condition: high surgical risk | op=PRESENT | logic=AND | grp=and_1 | class=Class IIb | level=B | dir=UNKNOWN
- Condition: high surgical risk | op=PRESENT | logic=OR | grp=or_1 | class=Class IIb | level=B | dir=POSITIVE
- Condition: multivessel disease | op=PRESENT | logic=AND | grp=and_1 | class=Class IIb | level=B | dir=UNKNOWN
- Condition: not operable | op=PRESENT | logic=AND | grp=and_1 | class=Class IIb | level=B | dir=UNKNOWN
- Condition: not operable | op=PRESENT | logic=OR | grp=or_1 | class=Class IIb | level=B | dir=POSITIVE
- Procedure: percutaneous coronary intervention | op=PRESENT | class=Class IIb | level=B | dir=POSITIVE
