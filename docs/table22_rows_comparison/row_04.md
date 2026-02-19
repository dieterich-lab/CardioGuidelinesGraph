# row_04 (mapped to row_05)

Original table row text (ground truth):

```json
{
  "Recommendations": "It is recommended that the decision for revascularization and its modality be patient-centred, considering patient preferences, health literacy, cultural circumstances, and social support. 849-851",
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
        "entity": "revacularization",
        "entity_original": "the decision for revascularization and its modality",
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
        "entity": "patient-centred decision",
        "entity_original": "the decision for revascularization and its modality be patient-centred",
        "role": "ClinicalAction",
        "operator": null,
        "threshold": null,
        "unit": null,
        "context": null,
        "logic_type": null,
        "logic_group": null,
        "strength": "I",
        "level": "C",
        "direction": "positive"
      },
      {
        "entity": "patient preferences",
        "entity_original": "the decision for revascularization and its modality consider patient preferences",
        "role": "ClinicalAction",
        "operator": null,
        "threshold": null,
        "unit": null,
        "context": null,
        "logic_type": null,
        "logic_group": null,
        "strength": "I",
        "level": "C",
        "direction": "positive"
      },
      {
        "entity": "health literacy",
        "entity_original": "the decision for revascularization and its modality consider health literacy",
        "role": "ClinicalAction",
        "operator": null,
        "threshold": null,
        "unit": null,
        "context": null,
        "logic_type": null,
        "logic_group": null,
        "strength": "I",
        "level": "C",
        "direction": "positive"
      },
      {
        "entity": "cultural circumstances",
        "entity_original": "the decision for revascularization and its modality consider cultural circumstances",
        "role": "ClinicalAction",
        "operator": null,
        "threshold": null,
        "unit": null,
        "context": null,
        "logic_type": null,
        "logic_group": null,
        "strength": "I",
        "level": "C",
        "direction": "positive"
      },
      {
        "entity": "social support",
        "entity_original": "the decision for revascularization and its modality consider social support",
        "role": "ClinicalAction",
        "operator": null,
        "threshold": null,
        "unit": null,
        "context": null,
        "logic_type": null,
        "logic_group": null,
        "strength": "I",
        "level": "C",
        "direction": "positive"
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
          "entity": "patient preferences",
          "entity_original": "patient preferences",
          "role": "Condition",
          "operator": "PRESENT",
          "threshold": null,
          "unit": null,
          "context": null,
          "logic_type": "AND",
          "logic_group": "and_1",
          "strength": "Class I",
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
          "context": null,
          "logic_type": "AND",
          "logic_group": "and_1",
          "strength": "Class I",
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
          "context": null,
          "logic_type": "AND",
          "logic_group": "and_1",
          "strength": "Class I",
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
          "context": null,
          "logic_type": "AND",
          "logic_group": "and_1",
          "strength": "Class I",
          "level": "C",
          "direction": "POSITIVE"
        }
      ],
      "actions": [
        {
          "entity": "revascularization decision",
          "entity_original": "decision for revascularization and its modality",
          "role": "Procedure",
          "operator": "PRESENT",
          "threshold": null,
          "unit": null,
          "context": null,
          "logic_type": null,
          "logic_group": null,
          "strength": "Class I",
          "level": "C",
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
  ACT1[ClinicalAction: patient-centred decision]
  REC -->|RECOMMENDS_USAGE| ACT1
  ACT2[ClinicalAction: patient preferences]
  REC -->|RECOMMENDS_USAGE| ACT2
  ACT3[ClinicalAction: health literacy]
  REC -->|RECOMMENDS_USAGE| ACT3
  ACT4[ClinicalAction: cultural circumstances]
  REC -->|RECOMMENDS_USAGE| ACT4
  ACT5[ClinicalAction: social support]
  REC -->|RECOMMENDS_USAGE| ACT5
  subgraph Human_and_1_AND
    D_and_1_1[DecisionNode and_1 s1]
    C_and_1_1[Procedure: revacularization]
    D_and_1_1 -->|CHECKS_FOR| C_and_1_1
  end
  D_and_1_1 -->|RESULTS_IN condition_met=true| REC
```

Mermaid (LLM Generated):

```mermaid
graph LR
  REC[RecommendationNode]
  ACT1[Procedure: revascularization decision]
  REC -->|RECOMMENDS_PROCEDURE| ACT1
  subgraph LLM_and_1_AND
    D_and_1_1[DecisionNode and_1 s1]
    C_and_1_1[Condition: patient preferences]
    D_and_1_1 -->|CHECKS_FOR| C_and_1_1
    D_and_1_2[DecisionNode and_1 s2]
    C_and_1_2[Condition: health literacy]
    D_and_1_2 -->|CHECKS_FOR| C_and_1_2
    D_and_1_3[DecisionNode and_1 s3]
    C_and_1_3[Condition: cultural circumstances]
    D_and_1_3 -->|CHECKS_FOR| C_and_1_3
    D_and_1_4[DecisionNode and_1 s4]
    C_and_1_4[Condition: social support]
    D_and_1_4 -->|CHECKS_FOR| C_and_1_4
    D_and_1_1 -->|LEADS_TO condition_met=true| D_and_1_2
    D_and_1_2 -->|LEADS_TO condition_met=true| D_and_1_3
    D_and_1_3 -->|LEADS_TO condition_met=true| D_and_1_4
  end
  D_and_1_4 -->|RESULTS_IN condition_met=true| REC
```

Concepts:
- expected: 6
- actual: 5
- matches: 0
- missing: 6
- extra: 5

Missing concepts:
- ClinicalAction: cultural circumstances
- ClinicalAction: health literacy
- ClinicalAction: patient preferences
- ClinicalAction: patient-centred decision
- ClinicalAction: social support
- Procedure: revacularization

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
- ClinicalAction: cultural circumstances | class=I | level=C | dir=positive
- ClinicalAction: health literacy | class=I | level=C | dir=positive
- ClinicalAction: patient preferences | class=I | level=C | dir=positive
- ClinicalAction: patient-centred decision | class=I | level=C | dir=positive
- ClinicalAction: social support | class=I | level=C | dir=positive
- Procedure: revacularization | op=PRESENT | logic=AND | grp=and_1

Extra rules:
- Condition: cultural circumstances | op=PRESENT | logic=AND | grp=and_1 | class=Class I | level=C | dir=POSITIVE
- Condition: health literacy | op=PRESENT | logic=AND | grp=and_1 | class=Class I | level=C | dir=POSITIVE
- Condition: patient preferences | op=PRESENT | logic=AND | grp=and_1 | class=Class I | level=C | dir=POSITIVE
- Condition: social support | op=PRESENT | logic=AND | grp=and_1 | class=Class I | level=C | dir=POSITIVE
- Procedure: revascularization decision | op=PRESENT | class=Class I | level=C | dir=POSITIVE
