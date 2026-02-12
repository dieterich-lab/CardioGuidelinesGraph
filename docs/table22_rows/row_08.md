# row_08 (mapped to row_09)

Original table row text (ground truth):

```json
{
  "Table Header": "Recommendations for revascularization in patients with chronic coronary syndrome",
  "Section Header": "Revascularization to improve outcomes",
  "Sub Header": "In chronic coronary syndrome patients with left ventricular ejection fraction > 35%",
  "Recommendations": "In CCS patients with LVEF > 35%, myocardial revascularization is recommended, in addition to guideline-directed medical therapy, for patients with functionally significant single- or two-vessel disease involving the proximal LAD, to reduce long-term cardiovascular mortality",
  "input": "CCS patients with LVEF > 35%, with functionally significant single- or two-vessel disease involving the proximal LAD",
  "recommendation": "myocardial revascularization is recommended, in addition to guideline-directed medical therapy to reduce long-term cardiovascular mortality",
  "Class a": "I",
  "Level b": "B"
}
```

Aligned JSON (expected vs actual):

<table>
  <tr>
    <th align="left">Expected</th>
    <th align="left">Actual</th>
  </tr>
  <tr>
    <td valign="top"><pre>
[
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
    "entity": "functionally significant three-vessel disease",
    "entity_original": "functionally significant single-vessel disease involving the proximal lad",
    "role": "Condition",
    "operator": "PRESENT",
    "threshold": null,
    "unit": null,
    "condition_context": null,
    "logic_type": "OR",
    "logic_group": "or_1",
    "strength": null,
    "level": null,
    "direction": null
  },
  {
    "entity": "functionally significant three-vessel disease",
    "entity_original": "functionally significant two-vessel disease involving the proximal lad",
    "role": "Condition",
    "operator": "PRESENT",
    "threshold": null,
    "unit": null,
    "condition_context": null,
    "logic_type": "OR",
    "logic_group": "or_1",
    "strength": null,
    "level": null,
    "direction": null
  },
  {
    "entity": "myocardial revascularization",
    "entity_original": "myocardial revascularization to reduce long-term cardiovascular mortality",
    "role": "Procedure",
    "operator": null,
    "threshold": null,
    "unit": null,
    "condition_context": null,
    "logic_type": null,
    "logic_group": null,
    "strength": "I",
    "level": "B",
    "direction": "POSITIVE"
  },
  {
    "entity": "guideline-directed medical therapy",
    "entity_original": "guideline-directed medical therapy to reduce long-term cardiovascular mortality",
    "role": "Procedure",
    "operator": null,
    "threshold": null,
    "unit": null,
    "condition_context": null,
    "logic_type": null,
    "logic_group": null,
    "strength": "I",
    "level": "B",
    "direction": "POSITIVE"
  }
]
</pre></td>
    <td valign="top"><pre>
[
  {
    "entity": "chronic coronary syndrome patients",
    "entity_original": "chronic coronary syndrome (ccs) patients",
    "role": "Condition",
    "operator": "PRESENT",
    "threshold": null,
    "unit": null,
    "condition_context": null,
    "logic_type": "AND",
    "logic_group": "and_1",
    "strength": "I",
    "level": "A",
    "direction": "POSITIVE"
  },
  {
    "entity": "left ventricular ejection fraction > 35%",
    "entity_original": "left ventricular ejection fraction (lvef) > 35%",
    "role": "ClinicalParameter",
    "operator": ">",
    "threshold": "35",
    "unit": "%",
    "condition_context": null,
    "logic_type": "AND",
    "logic_group": "and_1",
    "strength": "I",
    "level": "A",
    "direction": "POSITIVE"
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
  },
  {
    "entity": "chronic coronary syndrome",
    "entity_original": "chronic coronary syndrome (ccs) patients",
    "role": "Condition",
    "operator": "PRESENT",
    "threshold": null,
    "unit": null,
    "condition_context": "patients",
    "logic_type": "AND",
    "logic_group": "and_1",
    "strength": "I",
    "level": "A",
    "direction": "POSITIVE"
  },
  {
    "entity": "left ventricular ejection fraction",
    "entity_original": "left ventricular ejection fraction (lvef) > 35%",
    "role": "ClinicalParameter",
    "operator": ">",
    "threshold": "35",
    "unit": "%",
    "condition_context": null,
    "logic_type": "AND",
    "logic_group": "and_1",
    "strength": "I",
    "level": "A",
    "direction": "POSITIVE"
  }
]
</pre></td>
  </tr>
</table>

Mermaid (expected):

```mermaid
graph LR
  subgraph Expected_and_1_AND
    REC[RecommendationNode]
    D1[DecisionNode g1 s1]
    C1[Condition: ccs]
    D1 -->|CHECKS_FOR/EVALUATES| C1
    D2[DecisionNode g1 s2]
    C2[ClinicalParameter: lvef]
    D2 -->|CHECKS_FOR/EVALUATES| C2
    D1 -->|LEADS_TO| D2
    D2 -->|RESULTS_IN| REC
    ACT1[Procedure: myocardial revascularization]
    REC -->|RECOMMENDS_* / CONTRAINDICATES| ACT1
    ACT2[Procedure: guideline-directed medical therapy]
    REC -->|RECOMMENDS_* / CONTRAINDICATES| ACT2
  end
  subgraph Expected_or_1_OR
    REC[RecommendationNode]
    D1[DecisionNode g1 s1]
    C1[Condition: functionally significant three-vessel disease]
    D1 -->|CHECKS_FOR/EVALUATES| C1
    D2[DecisionNode g1 s2]
    C2[Condition: functionally significant three-vessel disease]
    D2 -->|CHECKS_FOR/EVALUATES| C2
    D1 -->|RESULTS_IN| REC
    D2 -->|RESULTS_IN| REC
    ACT1[Procedure: myocardial revascularization]
    REC -->|RECOMMENDS_* / CONTRAINDICATES| ACT1
    ACT2[Procedure: guideline-directed medical therapy]
    REC -->|RECOMMENDS_* / CONTRAINDICATES| ACT2
  end
  subgraph Expected_group_1_AND
    REC[RecommendationNode]
    REC
    ACT1[Procedure: myocardial revascularization]
    REC -->|RECOMMENDS_* / CONTRAINDICATES| ACT1
    ACT2[Procedure: guideline-directed medical therapy]
    REC -->|RECOMMENDS_* / CONTRAINDICATES| ACT2
  end
```

Mermaid (actual):

```mermaid
graph LR
  subgraph Actual_and_1_AND
    REC[RecommendationNode]
    D1[DecisionNode g1 s1]
    C1[Condition: chronic coronary syndrome patients]
    D1 -->|CHECKS_FOR/EVALUATES| C1
    D2[DecisionNode g1 s2]
    C2[ClinicalParameter: left ventricular ejection fraction > 35%]
    D2 -->|CHECKS_FOR/EVALUATES| C2
    D3[DecisionNode g1 s3]
    C3[Condition: chronic coronary syndrome]
    D3 -->|CHECKS_FOR/EVALUATES| C3
    D4[DecisionNode g1 s4]
    C4[ClinicalParameter: left ventricular ejection fraction]
    D4 -->|CHECKS_FOR/EVALUATES| C4
    D1 -->|LEADS_TO| D2
    D2 -->|LEADS_TO| D3
    D3 -->|LEADS_TO| D4
    D4 -->|RESULTS_IN| REC
    ACT1[Procedure: myocardial revascularization]
    REC -->|RECOMMENDS_* / CONTRAINDICATES| ACT1
  end
  subgraph Actual_group_1_AND
    REC[RecommendationNode]
    REC
    ACT1[Procedure: myocardial revascularization]
    REC -->|RECOMMENDS_* / CONTRAINDICATES| ACT1
  end
```

Concepts:
- expected: 5
- actual: 5
- matches: 1
- missing: 4
- extra: 4

Missing concepts:
- ClinicalParameter: lvef
- Condition: ccs
- Condition: functionally significant three-vessel disease
- Procedure: guideline-directed medical therapy

Extra concepts:
- ClinicalParameter: left ventricular ejection fraction
- ClinicalParameter: left ventricular ejection fraction > 35%
- Condition: chronic coronary syndrome
- Condition: chronic coronary syndrome patients

Rules (concept + logic fields):
- expected: 5
- actual: 5
- matches: 0
- missing: 5
- extra: 5

Missing rules:
- ClinicalParameter: lvef | op=> | thr=35 | unit=% | logic=AND | grp=and_1
- Condition: ccs | op=PRESENT | logic=AND | grp=and_1
- Condition: functionally significant three-vessel disease | op=PRESENT | logic=OR | grp=or_1
- Procedure: guideline-directed medical therapy | class=I | level=B | dir=POSITIVE
- Procedure: myocardial revascularization | class=I | level=B | dir=POSITIVE

Extra rules:
- ClinicalParameter: left ventricular ejection fraction > 35% | op=> | thr=35 | unit=% | logic=AND | grp=and_1 | class=I | level=A | dir=POSITIVE
- ClinicalParameter: left ventricular ejection fraction | op=> | thr=35 | unit=% | logic=AND | grp=and_1 | class=I | level=A | dir=POSITIVE
- Condition: chronic coronary syndrome patients | op=PRESENT | logic=AND | grp=and_1 | class=I | level=A | dir=POSITIVE
- Condition: chronic coronary syndrome | op=PRESENT | ctx=patients | logic=AND | grp=and_1 | class=I | level=A | dir=POSITIVE
- Procedure: myocardial revascularization | class=I | level=A | dir=POSITIVE

