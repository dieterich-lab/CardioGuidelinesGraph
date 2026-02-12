# row_18 (mapped to row_19)

Original table row text (ground truth):

```json
{
  "Table Header": "Recommendations for revascularization in patients with chronic coronary syndrome",
  "Section Header": "Assessment of procedural risks and post-procedural outcomes",
  "Sub Header": "Intracoronary pressure measurement (FFR or iFR) or computation (QFR) :",
  "Recommendations": "\u2022 should be considered at the end of the procedure to identify patients at high risk of persistent angina and subsequent clinical events; 828,830,831,868",
  "input": "at the end of the revascularization in patients with chronic coronary syndrome",
  "recommendation": "Intracoronary pressure measurement (FFR or iFR) or computation (QFR) should be considered at the end of the procedure to identify patients at high risk of persistent angina and subsequent clinical events",
  "Class a": "IIa",
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
  },
  {
    "entity": "computation (qfr)",
    "entity_original": "computation (qfr) is recommended to identify patients at high risk of persistent angina and subsequent clinical events",
    "role": "Procedure",
    "operator": null,
    "threshold": null,
    "unit": null,
    "condition_context": null,
    "logic_type": null,
    "logic_group": null,
    "strength": "IIa",
    "level": "B",
    "direction": "POSITIVE"
  },
  {
    "entity": "intracoronary pressure measurement (ffr)",
    "entity_original": "intracoronary pressure measurement (ffr) is recommended to identify patients at high risk of persistent angina and subsequent clinical events",
    "role": "Procedure",
    "operator": null,
    "threshold": null,
    "unit": null,
    "condition_context": null,
    "logic_type": null,
    "logic_group": null,
    "strength": "IIa",
    "level": "B",
    "direction": "POSITIVE"
  },
  {
    "entity": "intracoronary pressure measurement (ifr)",
    "entity_original": "intracoronary pressure measurement (ifr) is recommended to identify patients at high risk of persistent angina and subsequent clinical events",
    "role": "Procedure",
    "operator": null,
    "threshold": null,
    "unit": null,
    "condition_context": null,
    "logic_type": null,
    "logic_group": null,
    "strength": "IIa",
    "level": "B",
    "direction": "POSITIVE"
  },
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
  }
]
</pre></td>
    <td valign="top"><pre>
[
  {
    "entity": "assess procedural risks and post-procedural outcomes",
    "entity_original": "assess procedural risks and post-procedural outcomes",
    "role": "Procedure",
    "operator": null,
    "threshold": null,
    "unit": null,
    "condition_context": "to guide shared clinical decision-making",
    "logic_type": null,
    "logic_group": null,
    "strength": "I",
    "level": "C",
    "direction": "POSITIVE"
  },
  {
    "entity": "complex coronary artery disease",
    "entity_original": "complex coronary artery disease (cad)",
    "role": "Condition",
    "operator": "PRESENT",
    "threshold": null,
    "unit": null,
    "condition_context": "in whom revascularization is being considered",
    "logic_type": "AND",
    "logic_group": "and_1",
    "strength": "I",
    "level": "C",
    "direction": "POSITIVE"
  },
  {
    "entity": "complex coronary artery disease",
    "entity_original": "complex coronary artery disease (cad) in whom revascularization is being considered",
    "role": "Condition",
    "operator": "PRESENT",
    "threshold": null,
    "unit": null,
    "condition_context": "revascularization considered",
    "logic_type": "AND",
    "logic_group": "and_1",
    "strength": "I",
    "level": "C",
    "direction": "UNKNOWN"
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
    C1[Condition: chronic coronary syndrome]
    D1 -->|CHECKS_FOR/EVALUATES| C1
    D1 -->|RESULTS_IN| REC
    ACT1[Procedure: computation (qfr)]
    REC -->|RECOMMENDS_* / CONTRAINDICATES| ACT1
    ACT2[Procedure: intracoronary pressure measurement (ffr)]
    REC -->|RECOMMENDS_* / CONTRAINDICATES| ACT2
    ACT3[Procedure: intracoronary pressure measurement (ifr)]
    REC -->|RECOMMENDS_* / CONTRAINDICATES| ACT3
    ACT4[Procedure: revascularization]
    REC -->|RECOMMENDS_* / CONTRAINDICATES| ACT4
  end
  subgraph Expected_group_1_AND
    REC[RecommendationNode]
    REC
    ACT1[Procedure: computation (qfr)]
    REC -->|RECOMMENDS_* / CONTRAINDICATES| ACT1
    ACT2[Procedure: intracoronary pressure measurement (ffr)]
    REC -->|RECOMMENDS_* / CONTRAINDICATES| ACT2
    ACT3[Procedure: intracoronary pressure measurement (ifr)]
    REC -->|RECOMMENDS_* / CONTRAINDICATES| ACT3
    ACT4[Procedure: revascularization]
    REC -->|RECOMMENDS_* / CONTRAINDICATES| ACT4
  end
```

Mermaid (actual):

```mermaid
graph LR
  subgraph Actual_group_1_AND
    REC[RecommendationNode]
    REC
    ACT1[Procedure: assess procedural risks and post-procedural outcomes]
    REC -->|RECOMMENDS_* / CONTRAINDICATES| ACT1
  end
  subgraph Actual_and_1_AND
    REC[RecommendationNode]
    D1[DecisionNode g1 s1]
    C1[Condition: complex coronary artery disease]
    D1 -->|CHECKS_FOR/EVALUATES| C1
    D2[DecisionNode g1 s2]
    C2[Condition: complex coronary artery disease]
    D2 -->|CHECKS_FOR/EVALUATES| C2
    D1 -->|LEADS_TO| D2
    D2 -->|RESULTS_IN| REC
    ACT1[Procedure: assess procedural risks and post-procedural outcomes]
    REC -->|RECOMMENDS_* / CONTRAINDICATES| ACT1
  end
```

Concepts:
- expected: 5
- actual: 2
- matches: 0
- missing: 5
- extra: 2

Missing concepts:
- Condition: chronic coronary syndrome
- Procedure: computation (qfr)
- Procedure: intracoronary pressure measurement (ffr)
- Procedure: intracoronary pressure measurement (ifr)
- Procedure: revascularization

Extra concepts:
- Condition: complex coronary artery disease
- Procedure: assess procedural risks and post-procedural outcomes

Rules (concept + logic fields):
- expected: 5
- actual: 3
- matches: 0
- missing: 5
- extra: 3

Missing rules:
- Condition: chronic coronary syndrome | op=PRESENT | logic=AND | grp=and_1
- Procedure: computation (qfr) | class=IIa | level=B | dir=POSITIVE
- Procedure: intracoronary pressure measurement (ffr) | class=IIa | level=B | dir=POSITIVE
- Procedure: intracoronary pressure measurement (ifr) | class=IIa | level=B | dir=POSITIVE
- Procedure: revascularization | op=PRESENT | logic=AND | grp=and_1

Extra rules:
- Condition: complex coronary artery disease | op=PRESENT | ctx=in whom revascularization is being considered | logic=AND | grp=and_1 | class=I | level=C | dir=POSITIVE
- Condition: complex coronary artery disease | op=PRESENT | ctx=revascularization considered | logic=AND | grp=and_1 | class=I | level=C | dir=UNKNOWN
- Procedure: assess procedural risks and post-procedural outcomes | ctx=to guide shared clinical decision-making | class=I | level=C | dir=POSITIVE

