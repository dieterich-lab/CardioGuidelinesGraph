# row_09 (mapped to row_10)

Original table row text (ground truth):

```json
{}
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
        "entity": "ccs",
        "entity_original": "ccs patient",
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
      },
      {
        "entity": "lvef",
        "entity_original": "lvef \u2264 35%",
        "role": "ClinicalParameter",
        "operator": "\u2264",
        "threshold": "35",
        "unit": "%",
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
        "entity": "revascularization or medical therapy",
        "entity_original": "choose between revascularization or medical therapy alone",
        "role": "Procedure",
        "operator": null,
        "threshold": null,
        "unit": null,
        "condition_context": null,
        "logic_type": null,
        "logic_group": null,
        "strength": "I",
        "level": "C",
        "direction": "POSITIVE"
      },
      {
        "entity": "evaluate coronary anatomy",
        "entity_original": "evaluate coronary anatomy preferably by the heart team",
        "role": "Procedure",
        "operator": null,
        "threshold": null,
        "unit": null,
        "condition_context": null,
        "logic_type": null,
        "logic_group": null,
        "strength": "I",
        "level": "C",
        "direction": "POSITIVE"
      },
      {
        "entity": "evaluate correlation between coronary artery disease and lv dysfunction",
        "entity_original": "evaluate correlation between coronary artery disease and lv dysfunction preferably by the heart team",
        "role": "Procedure",
        "operator": null,
        "threshold": null,
        "unit": null,
        "condition_context": null,
        "logic_type": null,
        "logic_group": null,
        "strength": "I",
        "level": "C",
        "direction": "POSITIVE"
      },
      {
        "entity": "evaluate comorbidities",
        "entity_original": "evaluate comorbidities preferably by the heart team",
        "role": "Procedure",
        "operator": null,
        "threshold": null,
        "unit": null,
        "condition_context": null,
        "logic_type": null,
        "logic_group": null,
        "strength": "I",
        "level": "C",
        "direction": "POSITIVE"
      },
      {
        "entity": "evaluate life expectancy",
        "entity_original": "evaluate life expectancy by the heart team",
        "role": "Procedure",
        "operator": null,
        "threshold": null,
        "unit": null,
        "condition_context": null,
        "logic_type": null,
        "logic_group": null,
        "strength": "I",
        "level": "C",
        "direction": "POSITIVE"
      },
      {
        "entity": "evaluate individual risk-to-benefit ratio",
        "entity_original": "evaluate individual risk-to-benefit ratio by the heart team",
        "role": "Procedure",
        "operator": null,
        "threshold": null,
        "unit": null,
        "condition_context": null,
        "logic_type": null,
        "logic_group": null,
        "strength": "I",
        "level": "C",
        "direction": "POSITIVE"
      },
      {
        "entity": "evaluate patient perspectives",
        "entity_original": "evaluate patient perspectives by the heart team",
        "role": "Procedure",
        "operator": null,
        "threshold": null,
        "unit": null,
        "condition_context": null,
        "logic_type": null,
        "logic_group": null,
        "strength": "I",
        "level": "C",
        "direction": "POSITIVE"
      }
    ]
  }
]
</pre></td>
    <td valign="top"><pre>
[
  {
    "entity": "chronic coronary syndrome",
    "entity_original": "chronic coronary syndrome (ccs) patients",
    "role": "Condition",
    "operator": "PRESENT",
    "threshold": null,
    "unit": null,
    "condition_context": null,
    "logic_type": "AND",
    "logic_group": "and_1",
    "strength": null,
    "level": null,
    "direction": "UNKNOWN"
  },
  {
    "entity": "left ventricular ejection fraction",
    "entity_original": "left ventricular ejection fraction (lvef) > 35%",
    "role": "ClinicalParameter",
    "operator": ">",
    "threshold": "35",
    "unit": "%",
    "condition_context": "chronic coronary syndrome",
    "logic_type": "AND",
    "logic_group": "and_1",
    "strength": null,
    "level": null,
    "direction": "UNKNOWN"
  },
  {
    "entity": "three-vessel disease",
    "entity_original": "functionally significant three-vessel disease",
    "role": "Condition",
    "operator": "PRESENT",
    "threshold": null,
    "unit": null,
    "condition_context": "functionally significant",
    "logic_type": "AND",
    "logic_group": "and_1",
    "strength": null,
    "level": null,
    "direction": "UNKNOWN"
  },
  {
    "entity": "myocardial revascularization",
    "entity_original": "myocardial revascularization",
    "role": "Procedure",
    "operator": null,
    "threshold": null,
    "unit": null,
    "condition_context": null,
    "logic_type": null,
    "logic_group": null,
    "strength": "I",
    "level": "A",
    "direction": "POSITIVE"
  }
]
</pre></td>
  </tr>
</table>

Mermaid (Human Annotation):

```mermaid
graph LR
  REC[RecommendationNode]
  ACT1[Procedure: revascularization or medical therapy]
  REC -->|RECOMMENDS_PROCEDURE| ACT1
  ACT2[Procedure: evaluate coronary anatomy]
  REC -->|RECOMMENDS_PROCEDURE| ACT2
  ACT3[Procedure: evaluate correlation between coronary artery disease and lv dysfunction]
  REC -->|RECOMMENDS_PROCEDURE| ACT3
  ACT4[Procedure: evaluate comorbidities]
  REC -->|RECOMMENDS_PROCEDURE| ACT4
  ACT5[Procedure: evaluate life expectancy]
  REC -->|RECOMMENDS_PROCEDURE| ACT5
  ACT6[Procedure: evaluate individual risk-to-benefit ratio]
  REC -->|RECOMMENDS_PROCEDURE| ACT6
  ACT7[Procedure: evaluate patient perspectives]
  REC -->|RECOMMENDS_PROCEDURE| ACT7
  subgraph Human_and_1_AND
    D_and_1_1[DecisionNode and_1 s1]
    C_and_1_1[Condition: ccs]
    D_and_1_1 -->|CHECKS_FOR| C_and_1_1
    D_and_1_2[DecisionNode and_1 s2]
    C_and_1_2[ClinicalParameter: lvef]
    D_and_1_2 -->|EVALUATES| C_and_1_2
    D_and_1_1 -->|LEADS_TO (condition_met=true)| D_and_1_2
  end
  D_and_1_2 -->|RESULTS_IN (condition_met=true)| REC
```

Mermaid (LLM Generated):

```mermaid
graph LR
  REC[RecommendationNode]
  ACT1[Procedure: myocardial revascularization]
  REC -->|RECOMMENDS_PROCEDURE| ACT1
  subgraph LLM_and_1_AND
    D_and_1_1[DecisionNode and_1 s1]
    C_and_1_1[Condition: chronic coronary syndrome]
    D_and_1_1 -->|CHECKS_FOR| C_and_1_1
    D_and_1_2[DecisionNode and_1 s2]
    C_and_1_2[ClinicalParameter: left ventricular ejection fraction]
    D_and_1_2 -->|EVALUATES| C_and_1_2
    D_and_1_3[DecisionNode and_1 s3]
    C_and_1_3[Condition: three-vessel disease]
    D_and_1_3 -->|CHECKS_FOR| C_and_1_3
    D_and_1_1 -->|LEADS_TO (condition_met=true)| D_and_1_2
    D_and_1_2 -->|LEADS_TO (condition_met=true)| D_and_1_3
  end
  D_and_1_3 -->|RESULTS_IN (condition_met=true)| REC
```

Concepts:
- expected: 9
- actual: 4
- matches: 0
- missing: 9
- extra: 4

Missing concepts:
- ClinicalParameter: lvef
- Condition: ccs
- Procedure: evaluate comorbidities
- Procedure: evaluate coronary anatomy
- Procedure: evaluate correlation between coronary artery disease and lv dysfunction
- Procedure: evaluate individual risk-to-benefit ratio
- Procedure: evaluate life expectancy
- Procedure: evaluate patient perspectives
- Procedure: revascularization or medical therapy

Extra concepts:
- ClinicalParameter: left ventricular ejection fraction
- Condition: chronic coronary syndrome
- Condition: three-vessel disease
- Procedure: myocardial revascularization

Rules (concept + logic fields):
- expected: 9
- actual: 4
- matches: 0
- missing: 9
- extra: 4

Missing rules:
- ClinicalParameter: lvef | op=≤ | thr=35 | unit=% | logic=AND | grp=and_1
- Condition: ccs | op=PRESENT | logic=AND | grp=and_1
- Procedure: evaluate comorbidities | class=I | level=C | dir=POSITIVE
- Procedure: evaluate coronary anatomy | class=I | level=C | dir=POSITIVE
- Procedure: evaluate correlation between coronary artery disease and lv dysfunction | class=I | level=C | dir=POSITIVE
- Procedure: evaluate individual risk-to-benefit ratio | class=I | level=C | dir=POSITIVE
- Procedure: evaluate life expectancy | class=I | level=C | dir=POSITIVE
- Procedure: evaluate patient perspectives | class=I | level=C | dir=POSITIVE
- Procedure: revascularization or medical therapy | class=I | level=C | dir=POSITIVE

Extra rules:
- ClinicalParameter: left ventricular ejection fraction | op=> | thr=35 | unit=% | ctx=chronic coronary syndrome | logic=AND | grp=and_1 | dir=UNKNOWN
- Condition: chronic coronary syndrome | op=PRESENT | logic=AND | grp=and_1 | dir=UNKNOWN
- Condition: three-vessel disease | op=PRESENT | ctx=functionally significant | logic=AND | grp=and_1 | dir=UNKNOWN
- Procedure: myocardial revascularization | class=I | level=A | dir=POSITIVE

