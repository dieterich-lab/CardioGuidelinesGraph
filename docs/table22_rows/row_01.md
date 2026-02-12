# row_01 (mapped to row_02)

Aligned JSON (expected vs actual):

<table>
  <tr>
    <th align="left">Expected</th>
    <th align="left">Actual</th>
  </tr>
  <tr>
    <td><pre>
[
  {
    "entity": "benefits of revascularization",
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
    "entity": "percutaneous revascularization",
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
    "entity": "risks of revascularization",
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
    "entity": "shared decision-making",
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
    "entity": "surgical revascularization",
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
    "entity": "therapeutic consequences of revascularization",
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
    "entity": "treatment alternatives of revascularization",
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
</pre></td>
    <td><pre>
[
  {
    "entity": "information about revascularization benefits, risks, and alternatives",
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
    "entity": "patients scheduled for revascularization",
    "role": "Condition",
    "operator": "PRESENT",
    "threshold": null,
    "unit": null,
    "condition_context": "scheduled for",
    "logic_type": "AND",
    "logic_group": "and_1",
    "strength": "I",
    "level": "C",
    "direction": "UNKNOWN"
  },
  {
    "entity": "patients scheduled for revascularization",
    "role": "Condition",
    "operator": "PRESENT",
    "threshold": null,
    "unit": null,
    "condition_context": null,
    "logic_type": "AND",
    "logic_group": "and_1",
    "strength": "I",
    "level": "C",
    "direction": "POSITIVE"
  }
]
</pre></td>
  </tr>
</table>

Mermaid (expected):

```mermaid
graph LR
  subgraph Expected_group_1_AND
    REC[RecommendationNode]
    REC
    ACT1[Procedure: benefits of revascularization]
    REC -->|RECOMMENDS_* / CONTRAINDICATES| ACT1
    ACT2[Procedure: percutaneous revascularization]
    REC -->|RECOMMENDS_* / CONTRAINDICATES| ACT2
    ACT3[Procedure: risks of revascularization]
    REC -->|RECOMMENDS_* / CONTRAINDICATES| ACT3
    ACT4[Procedure: shared decision-making]
    REC -->|RECOMMENDS_* / CONTRAINDICATES| ACT4
    ACT5[Procedure: surgical revascularization]
    REC -->|RECOMMENDS_* / CONTRAINDICATES| ACT5
    ACT6[Procedure: therapeutic consequences of revascularization]
    REC -->|RECOMMENDS_* / CONTRAINDICATES| ACT6
    ACT7[Procedure: treatment alternatives of revascularization]
    REC -->|RECOMMENDS_* / CONTRAINDICATES| ACT7
  end
  subgraph Expected_and_1_AND
    REC[RecommendationNode]
    REC
    ACT1[Procedure: benefits of revascularization]
    REC -->|RECOMMENDS_* / CONTRAINDICATES| ACT1
    ACT2[Procedure: percutaneous revascularization]
    REC -->|RECOMMENDS_* / CONTRAINDICATES| ACT2
    ACT3[Procedure: risks of revascularization]
    REC -->|RECOMMENDS_* / CONTRAINDICATES| ACT3
    ACT4[Procedure: shared decision-making]
    REC -->|RECOMMENDS_* / CONTRAINDICATES| ACT4
    ACT5[Procedure: surgical revascularization]
    REC -->|RECOMMENDS_* / CONTRAINDICATES| ACT5
    ACT6[Procedure: therapeutic consequences of revascularization]
    REC -->|RECOMMENDS_* / CONTRAINDICATES| ACT6
    ACT7[Procedure: treatment alternatives of revascularization]
    REC -->|RECOMMENDS_* / CONTRAINDICATES| ACT7
  end
```

Mermaid (actual):

```mermaid
graph LR
  subgraph Actual_group_1_AND
    REC[RecommendationNode]
    REC
    ACT1[Procedure: information about revascularization benefits, risks, and alternatives]
    REC -->|RECOMMENDS_* / CONTRAINDICATES| ACT1
  end
  subgraph Actual_and_1_AND
    REC[RecommendationNode]
    D1[DecisionNode g1 s1]
    C1[Condition: patients scheduled for revascularization]
    D1 -->|CHECKS_FOR/EVALUATES| C1
    D2[DecisionNode g1 s2]
    C2[Condition: patients scheduled for revascularization]
    D2 -->|CHECKS_FOR/EVALUATES| C2
    D1 -->|LEADS_TO| D2
    D2 -->|RESULTS_IN| REC
    ACT1[Procedure: information about revascularization benefits, risks, and alternatives]
    REC -->|RECOMMENDS_* / CONTRAINDICATES| ACT1
  end
```

Concepts:
- expected: 7
- actual: 2
- matches: 0
- missing: 7
- extra: 2

Missing concepts:
- Procedure: benefits of revascularization
- Procedure: percutaneous revascularization
- Procedure: risks of revascularization
- Procedure: shared decision-making
- Procedure: surgical revascularization
- Procedure: therapeutic consequences of revascularization
- Procedure: treatment alternatives of revascularization

Extra concepts:
- Condition: patients scheduled for revascularization
- Procedure: information about revascularization benefits, risks, and alternatives

Rules (concept + logic fields):
- expected: 7
- actual: 3
- matches: 0
- missing: 7
- extra: 3

Missing rules:
- Procedure: benefits of revascularization | class=I | level=C | dir=POSITIVE
- Procedure: percutaneous revascularization | op=PRESENT | logic=AND | grp=and_1
- Procedure: risks of revascularization | class=I | level=C | dir=POSITIVE
- Procedure: shared decision-making | class=I | level=C | dir=POSITIVE
- Procedure: surgical revascularization | op=PRESENT | logic=AND | grp=and_1
- Procedure: therapeutic consequences of revascularization | class=I | level=C | dir=POSITIVE
- Procedure: treatment alternatives of revascularization | class=I | level=C | dir=POSITIVE

Extra rules:
- Condition: patients scheduled for revascularization | op=PRESENT | ctx=scheduled for | logic=AND | grp=and_1 | class=I | level=C | dir=UNKNOWN
- Condition: patients scheduled for revascularization | op=PRESENT | logic=AND | grp=and_1 | class=I | level=C | dir=POSITIVE
- Procedure: information about revascularization benefits, risks, and alternatives | class=I | level=C | dir=POSITIVE

