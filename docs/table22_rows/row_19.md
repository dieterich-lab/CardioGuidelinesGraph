# row_19 (mapped to row_20)

Original table row text (ground truth):

```json
{
  "Recommendations": "\u2022 may be considered at the end of the procedure to identify lesions potentially amenable to treatment with additional PCI. 350,829,831",
  "Class a": "IIb",
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
    "rule_id": 1,
    "conditions": [
      {
        "entity": "revascularization",
        "entity_original": "at the end of the revascularization",
        "role": "Procedure",
        "operator": "PRESENT",
        "threshold": null,
        "unit": null,
        "condition_context": null,
        "logic_type": "AND",
        "logic_group": "and_1",
        "strength": null,
        "level": null,
        "direction": null
      },
      {
        "entity": "chronic coronary syndrome",
        "entity_original": "patients with chronic coronary syndrome",
        "role": "Condition",
        "operator": "PRESENT",
        "threshold": null,
        "unit": null,
        "condition_context": null,
        "logic_type": "AND",
        "logic_group": "and_1",
        "strength": null,
        "level": null,
        "direction": null
      }
    ],
    "actions": [
      {
        "entity": "intracoronary pressure measurement (ffr)",
        "entity_original": "intracoronary pressure measurement (ffr) is recommended to identify lesions potentially amenable to treatment with additional pci",
        "role": "Procedure",
        "operator": null,
        "threshold": null,
        "unit": null,
        "condition_context": null,
        "logic_type": null,
        "logic_group": null,
        "strength": "IIb",
        "level": "B",
        "direction": "POSITIVE"
      },
      {
        "entity": "intracoronary pressure measurement (ifr)",
        "entity_original": "intracoronary pressure measurement (ifr) is recommended to identify lesions potentially amenable to treatment with additional pci",
        "role": "Procedure",
        "operator": null,
        "threshold": null,
        "unit": null,
        "condition_context": null,
        "logic_type": null,
        "logic_group": null,
        "strength": "IIb",
        "level": "B",
        "direction": "POSITIVE"
      },
      {
        "entity": "computation (qfr)",
        "entity_original": "computation (qfr) is recommended to identify lesions potentially amenable to treatment with additional pci",
        "role": "Procedure",
        "operator": null,
        "threshold": null,
        "unit": null,
        "condition_context": null,
        "logic_type": null,
        "logic_group": null,
        "strength": "IIb",
        "level": "B",
        "direction": "POSITIVE"
      }
    ]
  }
]
</pre></td>
    <td valign="top"><pre>
[
  {
    "entity": "society of thoracic surgeons score",
    "entity_original": "calculation of the society of thoracic surgeons score (sts) score",
    "role": "Procedure",
    "operator": "PRESENT",
    "threshold": null,
    "unit": null,
    "condition_context": "after coronary artery bypass grafting",
    "logic_type": null,
    "logic_group": null,
    "strength": "I",
    "level": "B",
    "direction": "POSITIVE"
  },
  {
    "entity": "coronary artery bypass grafting",
    "entity_original": "coronary artery bypass grafting (cabg)",
    "role": "ClinicalParameter",
    "operator": "PRESENT",
    "threshold": null,
    "unit": null,
    "condition_context": "patients undergoing",
    "logic_type": "AND",
    "logic_group": "and_1",
    "strength": "I",
    "level": "B",
    "direction": "POSITIVE"
  },
  {
    "entity": "patients undergoing coronary artery bypass grafting (cabg)",
    "entity_original": "patients undergoing coronary artery bypass grafting (cabg)",
    "role": "Condition",
    "operator": "PRESENT",
    "threshold": null,
    "unit": null,
    "condition_context": "after",
    "logic_type": "AND",
    "logic_group": "and_1",
    "strength": "I",
    "level": "B",
    "direction": "UNKNOWN"
  }
]
</pre></td>
  </tr>
</table>

Mermaid (Human Annotation):

```mermaid
graph LR
  REC[RecommendationNode]
  ACT1[Procedure: intracoronary pressure measurement (ffr)]
  REC -->|RECOMMENDS_PROCEDURE| ACT1
  ACT2[Procedure: intracoronary pressure measurement (ifr)]
  REC -->|RECOMMENDS_PROCEDURE| ACT2
  ACT3[Procedure: computation (qfr)]
  REC -->|RECOMMENDS_PROCEDURE| ACT3
  subgraph Human_and_1_AND
    D_and_1_1[DecisionNode and_1 s1]
    C_and_1_1[Procedure: revascularization]
    D_and_1_1 -->|CHECKS_FOR| C_and_1_1
    D_and_1_2[DecisionNode and_1 s2]
    C_and_1_2[Condition: chronic coronary syndrome]
    D_and_1_2 -->|CHECKS_FOR| C_and_1_2
    D_and_1_1 -->|LEADS_TO (condition_met=true)| D_and_1_2
  end
  D_and_1_2 -->|RESULTS_IN (condition_met=true)| REC
```

Mermaid (LLM Generated):

```mermaid
graph LR
  REC[RecommendationNode]
  ACT1[Procedure: society of thoracic surgeons score]
  REC -->|RECOMMENDS_PROCEDURE| ACT1
  subgraph LLM_and_1_AND
    D_and_1_1[DecisionNode and_1 s1]
    C_and_1_1[ClinicalParameter: coronary artery bypass grafting]
    D_and_1_1 -->|EVALUATES| C_and_1_1
    D_and_1_2[DecisionNode and_1 s2]
    C_and_1_2[Condition: patients undergoing coronary artery bypass grafting (cabg)]
    D_and_1_2 -->|CHECKS_FOR| C_and_1_2
    D_and_1_1 -->|LEADS_TO (condition_met=true)| D_and_1_2
  end
  D_and_1_2 -->|RESULTS_IN (condition_met=true)| REC
```

Concepts:
- expected: 5
- actual: 3
- matches: 0
- missing: 5
- extra: 3

Missing concepts:
- Condition: chronic coronary syndrome
- Procedure: computation (qfr)
- Procedure: intracoronary pressure measurement (ffr)
- Procedure: intracoronary pressure measurement (ifr)
- Procedure: revascularization

Extra concepts:
- ClinicalParameter: coronary artery bypass grafting
- Condition: patients undergoing coronary artery bypass grafting (cabg)
- Procedure: society of thoracic surgeons score

Rules (concept + logic fields):
- expected: 5
- actual: 3
- matches: 0
- missing: 5
- extra: 3

Missing rules:
- Condition: chronic coronary syndrome | op=PRESENT | logic=AND | grp=and_1
- Procedure: computation (qfr) | class=IIb | level=B | dir=POSITIVE
- Procedure: intracoronary pressure measurement (ffr) | class=IIb | level=B | dir=POSITIVE
- Procedure: intracoronary pressure measurement (ifr) | class=IIb | level=B | dir=POSITIVE
- Procedure: revascularization | op=PRESENT | logic=AND | grp=and_1

Extra rules:
- ClinicalParameter: coronary artery bypass grafting | op=PRESENT | ctx=patients undergoing | logic=AND | grp=and_1 | class=I | level=B | dir=POSITIVE
- Condition: patients undergoing coronary artery bypass grafting (cabg) | op=PRESENT | ctx=after | logic=AND | grp=and_1 | class=I | level=B | dir=UNKNOWN
- Procedure: society of thoracic surgeons score | op=PRESENT | ctx=after coronary artery bypass grafting | class=I | level=B | dir=POSITIVE

