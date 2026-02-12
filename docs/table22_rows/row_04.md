# row_04 (mapped to row_05)

Original table row text (ground truth):

```json
{
  "Table Header": "Recommendations for revascularization in patients with chronic coronary syndrome",
  "Section Header": "Informed and shared decisions",
  "Recommendations": "It is recommended that the decision for revascularization and its modality be patient-centred, considering patient preferences, health literacy, cultural circumstances, and social support. 849-851",
  "input": "the decision for revascularization and its modality ",
  "recommendation": "It is recommended that the decision for revascularization and its modality be patient-centred, considering patient preferences, health literacy, cultural circumstances, and social support",
  "Class a": "I",
  "Level b": "C"
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
    "entity": "revacularization",
    "entity_original": "the decision for revascularization and its modality",
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
    "entity": "patient-centred decision",
    "entity_original": "the decision for revascularization and its modality be patient-centred",
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
    "entity": "patient preferences",
    "entity_original": "the decision for revascularization and its modality consider patient preferences",
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
    "entity": "health literacy",
    "entity_original": "the decision for revascularization and its modality consider health literacy",
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
    "entity": "cultural circumstances",
    "entity_original": "the decision for revascularization and its modality consider cultural circumstances",
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
    "entity": "social support",
    "entity_original": "the decision for revascularization and its modality consider social support",
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
    <td valign="top"><pre>
[
  {
    "entity": "patient preferences",
    "entity_original": "patient preferences",
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
  },
  {
    "entity": "health literacy",
    "entity_original": "health literacy",
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
  },
  {
    "entity": "cultural circumstances",
    "entity_original": "cultural circumstances",
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
  },
  {
    "entity": "social support",
    "entity_original": "social support",
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
  },
  {
    "entity": "revascularization decision",
    "entity_original": "decision for revascularization and its modality",
    "role": "Procedure",
    "operator": "PRESENT",
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
  </tr>
</table>

Mermaid (expected):

```mermaid
graph LR
  subgraph Expected_and_1_AND
    REC[RecommendationNode]
    REC
    ACT1[Procedure: revacularization]
    REC -->|RECOMMENDS_* / CONTRAINDICATES| ACT1
    ACT2[Procedure: patient-centred decision]
    REC -->|RECOMMENDS_* / CONTRAINDICATES| ACT2
    ACT3[Procedure: patient preferences]
    REC -->|RECOMMENDS_* / CONTRAINDICATES| ACT3
    ACT4[Procedure: health literacy]
    REC -->|RECOMMENDS_* / CONTRAINDICATES| ACT4
    ACT5[Procedure: cultural circumstances]
    REC -->|RECOMMENDS_* / CONTRAINDICATES| ACT5
    ACT6[Procedure: social support]
    REC -->|RECOMMENDS_* / CONTRAINDICATES| ACT6
  end
  subgraph Expected_group_1_AND
    REC[RecommendationNode]
    REC
    ACT1[Procedure: revacularization]
    REC -->|RECOMMENDS_* / CONTRAINDICATES| ACT1
    ACT2[Procedure: patient-centred decision]
    REC -->|RECOMMENDS_* / CONTRAINDICATES| ACT2
    ACT3[Procedure: patient preferences]
    REC -->|RECOMMENDS_* / CONTRAINDICATES| ACT3
    ACT4[Procedure: health literacy]
    REC -->|RECOMMENDS_* / CONTRAINDICATES| ACT4
    ACT5[Procedure: cultural circumstances]
    REC -->|RECOMMENDS_* / CONTRAINDICATES| ACT5
    ACT6[Procedure: social support]
    REC -->|RECOMMENDS_* / CONTRAINDICATES| ACT6
  end
```

Mermaid (actual):

```mermaid
graph LR
  subgraph Actual_and_1_AND
    REC[RecommendationNode]
    D1[DecisionNode g1 s1]
    C1[Condition: patient preferences]
    D1 -->|CHECKS_FOR/EVALUATES| C1
    D2[DecisionNode g1 s2]
    C2[Condition: health literacy]
    D2 -->|CHECKS_FOR/EVALUATES| C2
    D3[DecisionNode g1 s3]
    C3[Condition: cultural circumstances]
    D3 -->|CHECKS_FOR/EVALUATES| C3
    D4[DecisionNode g1 s4]
    C4[Condition: social support]
    D4 -->|CHECKS_FOR/EVALUATES| C4
    D1 -->|LEADS_TO| D2
    D2 -->|LEADS_TO| D3
    D3 -->|LEADS_TO| D4
    D4 -->|RESULTS_IN| REC
    ACT1[Procedure: revascularization decision]
    REC -->|RECOMMENDS_* / CONTRAINDICATES| ACT1
  end
  subgraph Actual_group_1_AND
    REC[RecommendationNode]
    REC
    ACT1[Procedure: revascularization decision]
    REC -->|RECOMMENDS_* / CONTRAINDICATES| ACT1
  end
```

Concepts:
- expected: 6
- actual: 5
- matches: 0
- missing: 6
- extra: 5

Missing concepts:
- Procedure: cultural circumstances
- Procedure: health literacy
- Procedure: patient preferences
- Procedure: patient-centred decision
- Procedure: revacularization
- Procedure: social support

Extra concepts:
- Condition: cultural circumstances
- Condition: health literacy
- Condition: patient preferences
- Condition: social support
- Procedure: revascularization decision

Rules (concept + logic fields):
- expected: 6
- actual: 5
- matches: 0
- missing: 6
- extra: 5

Missing rules:
- Procedure: cultural circumstances | class=I | level=C | dir=POSITIVE
- Procedure: health literacy | class=I | level=C | dir=POSITIVE
- Procedure: patient preferences | class=I | level=C | dir=POSITIVE
- Procedure: patient-centred decision | class=I | level=C | dir=POSITIVE
- Procedure: revacularization | op=PRESENT | logic=AND | grp=and_1
- Procedure: social support | class=I | level=C | dir=POSITIVE

Extra rules:
- Condition: cultural circumstances | op=PRESENT | logic=AND | grp=and_1 | class=I | level=C | dir=POSITIVE
- Condition: health literacy | op=PRESENT | logic=AND | grp=and_1 | class=I | level=C | dir=POSITIVE
- Condition: patient preferences | op=PRESENT | logic=AND | grp=and_1 | class=I | level=C | dir=POSITIVE
- Condition: social support | op=PRESENT | logic=AND | grp=and_1 | class=I | level=C | dir=POSITIVE
- Procedure: revascularization decision | op=PRESENT | class=I | level=C | dir=POSITIVE

