# row_11 (mapped to row_12)

Original table row text (ground truth):

```json
{
  "Recommendations": "In selected CCS patients with functionally significant MVD and LVEF \u2264 35% who are at high surgical risk or not operable, PCI may be considered as an alternative to CABG. 526,729",
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
        "entity": "high surgical risk",
        "entity_original": "patient with high surgical risk",
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
        "entity": "not operable",
        "entity_original": "not operable patient",
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
        "entity": "functionally significant mvd",
        "entity_original": "functionally significant mvd",
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
        "entity": "pci",
        "entity_original": "pci may be considered as an alternative to cabg",
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
    "entity": "left ventricular ejection fraction",
    "entity_original": "left ventricular ejection fraction \u2264 35%",
    "role": "ClinicalParameter",
    "operator": "<=",
    "threshold": "35",
    "unit": "%",
    "condition_context": null,
    "logic_type": "AND",
    "logic_group": "and_1",
    "strength": "IIa",
    "level": "B",
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
  ACT1[Procedure: pci]
  REC -->|RECOMMENDS_PROCEDURE| ACT1
  subgraph Human_and_1_AND
    D_and_1_1[DecisionNode and_1 s1]
    C_and_1_1[Condition: ccs]
    D_and_1_1 -->|CHECKS_FOR| C_and_1_1
    D_and_1_2[DecisionNode and_1 s2]
    C_and_1_2[Condition: functionally significant mvd]
    D_and_1_2 -->|CHECKS_FOR| C_and_1_2
    D_and_1_3[DecisionNode and_1 s3]
    C_and_1_3[ClinicalParameter: lvef]
    D_and_1_3 -->|EVALUATES| C_and_1_3
    D_and_1_1 -->|LEADS_TO (condition_met=true)| D_and_1_2
    D_and_1_2 -->|LEADS_TO (condition_met=true)| D_and_1_3
  end
  subgraph Human_or_1_OR
    D_or_1_1[DecisionNode or_1 s1]
    C_or_1_1[Condition: high surgical risk]
    D_or_1_1 -->|CHECKS_FOR| C_or_1_1
    D_or_1_2[DecisionNode or_1 s2]
    C_or_1_2[Condition: not operable]
    D_or_1_2 -->|CHECKS_FOR| C_or_1_2
    D_and_1_3 -->|LEADS_TO (condition_met=true)| D_or_1_1
    D_and_1_3 -->|LEADS_TO (condition_met=true)| D_or_1_2
  end
  D_or_1_1 -->|RESULTS_IN (condition_met=true)| REC
  D_or_1_2 -->|RESULTS_IN (condition_met=true)| REC
```

Mermaid (LLM Generated):

```mermaid
graph LR
  REC[RecommendationNode]
  subgraph LLM_and_1_AND
    D_and_1_1[DecisionNode and_1 s1]
    C_and_1_1[ClinicalParameter: left ventricular ejection fraction]
    D_and_1_1 -->|EVALUATES| C_and_1_1
  end
  D_and_1_1 -->|RESULTS_IN (condition_met=true)| REC
```

Concepts:
- expected: 6
- actual: 1
- matches: 0
- missing: 6
- extra: 1

Missing concepts:
- ClinicalParameter: lvef
- Condition: ccs
- Condition: functionally significant mvd
- Condition: high surgical risk
- Condition: not operable
- Procedure: pci

Extra concepts:
- ClinicalParameter: left ventricular ejection fraction

Rules (concept + logic fields):
- expected: 6
- actual: 1
- matches: 0
- missing: 6
- extra: 1

Missing rules:
- ClinicalParameter: lvef | op=≤ | thr=35 | unit=% | logic=AND | grp=and_1
- Condition: ccs | op=PRESENT | logic=AND | grp=and_1
- Condition: functionally significant mvd | op=PRESENT | logic=AND | grp=and_1
- Condition: high surgical risk | op=PRESENT | logic=OR | grp=or_1
- Condition: not operable | op=PRESENT | logic=OR | grp=or_1
- Procedure: pci | class=IIb | level=B | dir=POSITIVE

Extra rules:
- ClinicalParameter: left ventricular ejection fraction | op=<= | thr=35 | unit=% | logic=AND | grp=and_1 | class=IIa | level=B | dir=POSITIVE

