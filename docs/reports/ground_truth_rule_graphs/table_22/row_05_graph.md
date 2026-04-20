# Ground Truth Rules - Table 22 Row 05

- table: 22
- row: row_05

Recommendation text:

```text
It is recommended that the Heart Team (on site or with a partner institution) develop institutional protocols to implement the appropriate revascularization strategy in accordance with current guidelines.
```

Ground-truth rules:

```json
[
  {
    "conditions": [
      {
        "entity": "the heart team",
        "entity_original": "the heart team",
        "role": "Qualifier Value",
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
        "entity": "develop institutional protocols",
        "entity_original": "develop institutional protocols",
        "role": "Procedure",
        "operator": null,
        "threshold": null,
        "unit": null,
        "context": null,
        "logic_type": null,
        "logic_group": null,
        "strength": "I",
        "level": "C",
        "direction": "POSITIVE",
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
  ACT1[Procedure: develop institutional protocols]
  REC -->|RECOMMENDS_PROCEDURE| ACT1
  subgraph Table22Row05_group_1_AND
    D_group_1_1[DecisionNode group_1 s1]
    C_group_1_1[Qualifier Value: the heart team]
    D_group_1_1 -->|CHECKS_FOR| C_group_1_1
  end
  D_group_1_1 -->|RESULTS_IN condition_met=true| REC
```
