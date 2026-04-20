# Ground Truth Rules - Table 22 Row 04

- table: 22
- row: row_04

Recommendation text:

```text
It is recommended that the decision for revascularization and its modality be patient-centred, considering patient preferences, health literacy, cultural circumstances, and social support
```

Ground-truth rules:

```json
[
  {
    "conditions": [
      {
        "entity": "revascularization and its modality",
        "entity_original": "revascularization and its modality",
        "role": "Procedure",
        "operator": "PRESENT",
        "threshold": null,
        "unit": null,
        "context": null,
        "logic_type": "NULL",
        "logic_group": null,
        "strength": null,
        "level": null,
        "direction": null,
        "_side": "condition"
      }
    ],
    "actions": [
      {
        "entity": "patient-centred decision",
        "entity_original": "patient-centred decision",
        "role": "Procedure",
        "operator": null,
        "threshold": null,
        "unit": null,
        "context": null,
        "logic_type": null,
        "logic_group": null,
        "strength": "I",
        "level": "C",
        "direction": "positive",
        "_side": "action"
      },
      {
        "entity": "the decision for revascularization and its modality consider patient preferences",
        "entity_original": "the decision for revascularization and its modality consider patient preferences",
        "role": "Procedure",
        "operator": null,
        "threshold": null,
        "unit": null,
        "context": null,
        "logic_type": null,
        "logic_group": null,
        "strength": "I",
        "level": "C",
        "direction": "positive",
        "_side": "action"
      },
      {
        "entity": "the decision for revascularization and its modality consider health literacy",
        "entity_original": "the decision for revascularization and its modality consider health literacy",
        "role": "Procedure",
        "operator": null,
        "threshold": null,
        "unit": null,
        "context": null,
        "logic_type": null,
        "logic_group": null,
        "strength": "I",
        "level": "C",
        "direction": "positive",
        "_side": "action"
      },
      {
        "entity": "the decision for revascularization and its modality consider cultural circumstances",
        "entity_original": "the decision for revascularization and its modality consider cultural circumstances",
        "role": "Procedure",
        "operator": null,
        "threshold": null,
        "unit": null,
        "context": null,
        "logic_type": null,
        "logic_group": null,
        "strength": "I",
        "level": "C",
        "direction": "positive",
        "_side": "action"
      },
      {
        "entity": "the decision for revascularization and its modality consider social support",
        "entity_original": "the decision for revascularization and its modality consider social support",
        "role": "Procedure",
        "operator": null,
        "threshold": null,
        "unit": null,
        "context": null,
        "logic_type": null,
        "logic_group": null,
        "strength": "I",
        "level": "C",
        "direction": "positive",
        "_side": "action"
      }
    ]
  }
]
```

Mermaid graph:

```mermaid
graph LR
  REC[RecommendationNode]
  ACT1[Procedure: patient-centred decision]
  REC -->|RECOMMENDS_PROCEDURE| ACT1
  ACT2[Procedure: the decision for revascularization and its modality consider patient preferences]
  REC -->|RECOMMENDS_PROCEDURE| ACT2
  ACT3[Procedure: the decision for revascularization and its modality consider health literacy]
  REC -->|RECOMMENDS_PROCEDURE| ACT3
  ACT4[Procedure: the decision for revascularization and its modality consider cultural circumstances]
  REC -->|RECOMMENDS_PROCEDURE| ACT4
  ACT5[Procedure: the decision for revascularization and its modality consider social support]
  REC -->|RECOMMENDS_PROCEDURE| ACT5
  subgraph Table22Row04_group_1_AND
    D_group_1_1[DecisionNode group_1 s1]
    C_group_1_1[Procedure: revascularization and its modality]
    D_group_1_1 -->|CHECKS_FOR| C_group_1_1
  end
  D_group_1_1 -->|RESULTS_IN condition_met=true| REC
```
