# row_06 (mapped to row_07)

Original table row text (ground truth):

```json
{
  "Recommendations": "In CCS patients with LVEF > 35%, myocardial revascularization is recommended, in addition to guideline-directed medical therapy, for patients with functionally significant left main stem stenosis to improve survival. 718,719,859,860",
  "Class a": "I",
  "Level b": "A"
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
        "entity_original": "lvef > 35%",
        "role": "ClinicalParameter",
        "operator": ">",
        "threshold": "35",
        "unit": "%",
        "condition_context": null,
        "logic_type": "AND",
        "logic_group": "and_1",
        "strength": null,
        "level": null,
        "direction": null
      },
      {
        "entity": "functionally significant left main stem stenosis",
        "entity_original": "functionally significant left main stem stenosis",
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
        "entity": "myocardial revascularization",
        "entity_original": "myocardial revascularization to improve survival",
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
      },
      {
        "entity": "guideline-directed medical therapy",
        "entity_original": "guideline-directed medical therapy to improve survival",
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
  }
]
</pre></td>
    <td valign="top"><pre>
[
  {
    "entity": "revascularization",
    "entity_original": "revascularization to improve outcomes",
    "role": "Procedure",
    "operator": null,
    "threshold": null,
    "unit": null,
    "condition_context": null,
    "logic_type": null,
    "logic_group": null,
    "strength": null,
    "level": null,
    "direction": "POSITIVE"
  },
  {
    "entity": "age",
    "entity_original": "age",
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
    "entity": "frailty",
    "entity_original": "frailty",
    "role": "Condition",
    "operator": "PRESENT",
    "threshold": null,
    "unit": null,
    "condition_context": null,
    "logic_type": "AND",
    "logic_group": "and_2",
    "strength": null,
    "level": null,
    "direction": "UNKNOWN"
  },
  {
    "entity": "cognitive status",
    "entity_original": "cognitive status",
    "role": "Condition",
    "operator": "PRESENT",
    "threshold": null,
    "unit": null,
    "condition_context": null,
    "logic_type": "AND",
    "logic_group": "and_3",
    "strength": null,
    "level": null,
    "direction": "UNKNOWN"
  },
  {
    "entity": "diabetes",
    "entity_original": "diabetes",
    "role": "Condition",
    "operator": "PRESENT",
    "threshold": null,
    "unit": null,
    "condition_context": null,
    "logic_type": "AND",
    "logic_group": "and_4",
    "strength": null,
    "level": null,
    "direction": "UNKNOWN"
  },
  {
    "entity": "other comorbidities",
    "entity_original": "any other comorbidities",
    "role": "Condition",
    "operator": "PRESENT",
    "threshold": null,
    "unit": null,
    "condition_context": null,
    "logic_type": "AND",
    "logic_group": "and_5",
    "strength": null,
    "level": null,
    "direction": "UNKNOWN"
  },
  {
    "entity": "multivessel disease",
    "entity_original": "multivessel disease",
    "role": "Condition",
    "operator": "PRESENT",
    "threshold": null,
    "unit": null,
    "condition_context": null,
    "logic_type": "AND",
    "logic_group": "and_6",
    "strength": null,
    "level": null,
    "direction": "UNKNOWN"
  },
  {
    "entity": "left main stem involvement",
    "entity_original": "left main stem involvement",
    "role": "Condition",
    "operator": "PRESENT",
    "threshold": null,
    "unit": null,
    "condition_context": null,
    "logic_type": "AND",
    "logic_group": "and_7",
    "strength": null,
    "level": null,
    "direction": "UNKNOWN"
  },
  {
    "entity": "high anatomical complexity",
    "entity_original": "high anatomical complexity",
    "role": "Condition",
    "operator": "PRESENT",
    "threshold": null,
    "unit": null,
    "condition_context": null,
    "logic_type": "AND",
    "logic_group": "and_8",
    "strength": null,
    "level": null,
    "direction": "UNKNOWN"
  },
  {
    "entity": "likelihood of revascularization completeness",
    "entity_original": "likelihood of revascularization completeness",
    "role": "Condition",
    "operator": "PRESENT",
    "threshold": null,
    "unit": null,
    "condition_context": null,
    "logic_type": "AND",
    "logic_group": "and_9",
    "strength": null,
    "level": null,
    "direction": "UNKNOWN"
  },
  {
    "entity": "local expertise",
    "entity_original": "local expertise",
    "role": "Condition",
    "operator": "PRESENT",
    "threshold": null,
    "unit": null,
    "condition_context": null,
    "logic_type": "AND",
    "logic_group": "and_10",
    "strength": null,
    "level": null,
    "direction": "UNKNOWN"
  },
  {
    "entity": "surgical and interventional risk",
    "entity_original": "surgical and interventional risk",
    "role": "Condition",
    "operator": "PRESENT",
    "threshold": null,
    "unit": null,
    "condition_context": null,
    "logic_type": "AND",
    "logic_group": "and_11",
    "strength": null,
    "level": null,
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
  ACT1[Procedure: myocardial revascularization]
  REC -->|RECOMMENDS_PROCEDURE| ACT1
  ACT2[Procedure: guideline-directed medical therapy]
  REC -->|RECOMMENDS_PROCEDURE| ACT2
  subgraph Human_and_1_AND
    D_and_1_1[DecisionNode and_1 s1]
    C_and_1_1[Condition: ccs]
    D_and_1_1 -->|CHECKS_FOR| C_and_1_1
    D_and_1_2[DecisionNode and_1 s2]
    C_and_1_2[ClinicalParameter: lvef]
    D_and_1_2 -->|EVALUATES| C_and_1_2
    D_and_1_3[DecisionNode and_1 s3]
    C_and_1_3[Condition: functionally significant left main stem stenosis]
    D_and_1_3 -->|CHECKS_FOR| C_and_1_3
    D_and_1_1 -->|LEADS_TO condition_met=true| D_and_1_2
    D_and_1_2 -->|LEADS_TO condition_met=true| D_and_1_3
  end
  D_and_1_3 -->|RESULTS_IN condition_met=true| REC
```

Mermaid (LLM Generated):

```mermaid
graph LR
  REC[RecommendationNode]
  ACT1[Procedure: revascularization]
  REC -->|RECOMMENDS_PROCEDURE| ACT1
  subgraph LLM_and_1_AND
    D_and_1_1[DecisionNode and_1 s1]
    C_and_1_1[Condition: age]
    D_and_1_1 -->|CHECKS_FOR| C_and_1_1
  end
  subgraph LLM_and_2_AND
    D_and_2_1[DecisionNode and_2 s1]
    C_and_2_1[Condition: frailty]
    D_and_2_1 -->|CHECKS_FOR| C_and_2_1
    D_and_1_1 -->|LEADS_TO condition_met=true| D_and_2_1
  end
  subgraph LLM_and_3_AND
    D_and_3_1[DecisionNode and_3 s1]
    C_and_3_1[Condition: cognitive status]
    D_and_3_1 -->|CHECKS_FOR| C_and_3_1
    D_and_2_1 -->|LEADS_TO condition_met=true| D_and_3_1
  end
  subgraph LLM_and_4_AND
    D_and_4_1[DecisionNode and_4 s1]
    C_and_4_1[Condition: diabetes]
    D_and_4_1 -->|CHECKS_FOR| C_and_4_1
    D_and_3_1 -->|LEADS_TO condition_met=true| D_and_4_1
  end
  subgraph LLM_and_5_AND
    D_and_5_1[DecisionNode and_5 s1]
    C_and_5_1[Condition: other comorbidities]
    D_and_5_1 -->|CHECKS_FOR| C_and_5_1
    D_and_4_1 -->|LEADS_TO condition_met=true| D_and_5_1
  end
  subgraph LLM_and_6_AND
    D_and_6_1[DecisionNode and_6 s1]
    C_and_6_1[Condition: multivessel disease]
    D_and_6_1 -->|CHECKS_FOR| C_and_6_1
    D_and_5_1 -->|LEADS_TO condition_met=true| D_and_6_1
  end
  subgraph LLM_and_7_AND
    D_and_7_1[DecisionNode and_7 s1]
    C_and_7_1[Condition: left main stem involvement]
    D_and_7_1 -->|CHECKS_FOR| C_and_7_1
    D_and_6_1 -->|LEADS_TO condition_met=true| D_and_7_1
  end
  subgraph LLM_and_8_AND
    D_and_8_1[DecisionNode and_8 s1]
    C_and_8_1[Condition: high anatomical complexity]
    D_and_8_1 -->|CHECKS_FOR| C_and_8_1
    D_and_7_1 -->|LEADS_TO condition_met=true| D_and_8_1
  end
  subgraph LLM_and_9_AND
    D_and_9_1[DecisionNode and_9 s1]
    C_and_9_1[Condition: likelihood of revascularization completeness]
    D_and_9_1 -->|CHECKS_FOR| C_and_9_1
    D_and_8_1 -->|LEADS_TO condition_met=true| D_and_9_1
  end
  subgraph LLM_and_10_AND
    D_and_10_1[DecisionNode and_10 s1]
    C_and_10_1[Condition: local expertise]
    D_and_10_1 -->|CHECKS_FOR| C_and_10_1
    D_and_9_1 -->|LEADS_TO condition_met=true| D_and_10_1
  end
  subgraph LLM_and_11_AND
    D_and_11_1[DecisionNode and_11 s1]
    C_and_11_1[Condition: surgical and interventional risk]
    D_and_11_1 -->|CHECKS_FOR| C_and_11_1
    D_and_10_1 -->|LEADS_TO condition_met=true| D_and_11_1
  end
  D_and_11_1 -->|RESULTS_IN condition_met=true| REC
```

Concepts:
- expected: 5
- actual: 12
- matches: 0
- missing: 5
- extra: 12

Missing concepts:
- ClinicalParameter: lvef
- Condition: ccs
- Condition: functionally significant left main stem stenosis
- Procedure: guideline-directed medical therapy
- Procedure: myocardial revascularization

Extra concepts:
- Condition: age
- Condition: cognitive status
- Condition: diabetes
- Condition: frailty
- Condition: high anatomical complexity
- Condition: left main stem involvement
- Condition: likelihood of revascularization completeness
- Condition: local expertise
- Condition: multivessel disease
- Condition: other comorbidities
- Condition: surgical and interventional risk
- Procedure: revascularization

Rules (concept + logic fields):
- expected: 5
- actual: 12
- matches: 0
- missing: 5
- extra: 12

Missing rules:
- ClinicalParameter: lvef | op=> | thr=35 | unit=% | logic=AND | grp=and_1
- Condition: ccs | op=PRESENT | logic=AND | grp=and_1
- Condition: functionally significant left main stem stenosis | op=PRESENT | logic=AND | grp=and_1
- Procedure: guideline-directed medical therapy | class=I | level=A | dir=POSITIVE
- Procedure: myocardial revascularization | class=I | level=A | dir=POSITIVE

Extra rules:
- Condition: age | op=PRESENT | logic=AND | grp=and_1 | dir=UNKNOWN
- Condition: cognitive status | op=PRESENT | logic=AND | grp=and_3 | dir=UNKNOWN
- Condition: diabetes | op=PRESENT | logic=AND | grp=and_4 | dir=UNKNOWN
- Condition: frailty | op=PRESENT | logic=AND | grp=and_2 | dir=UNKNOWN
- Condition: high anatomical complexity | op=PRESENT | logic=AND | grp=and_8 | dir=UNKNOWN
- Condition: left main stem involvement | op=PRESENT | logic=AND | grp=and_7 | dir=UNKNOWN
- Condition: likelihood of revascularization completeness | op=PRESENT | logic=AND | grp=and_9 | dir=UNKNOWN
- Condition: local expertise | op=PRESENT | logic=AND | grp=and_10 | dir=UNKNOWN
- Condition: multivessel disease | op=PRESENT | logic=AND | grp=and_6 | dir=UNKNOWN
- Condition: other comorbidities | op=PRESENT | logic=AND | grp=and_5 | dir=UNKNOWN
- Condition: surgical and interventional risk | op=PRESENT | logic=AND | grp=and_11 | dir=UNKNOWN
- Procedure: revascularization | dir=POSITIVE

