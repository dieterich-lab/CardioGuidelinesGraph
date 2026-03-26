# Ground Truth Rules - Table 22 Row 03

- table: 22
- row: row_03

Recommendation text:

```text
It is recommended to communicate the proposal of the Heart Team in a balanced way using language that the patient can understand.
```

Ground-truth rules:

```json
[
  {
    "conditions": [
      {
        "entity": "proposal",
        "entity_original": "proposal",
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
        "entity": "communicate",
        "entity_original": "communicate",
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
  ACT1[Procedure: communicate]
  REC -->|RECOMMENDS_PROCEDURE| ACT1
  subgraph Table22Row03_group_1_AND
    D_group_1_1[DecisionNode group_1 s1]
    C_group_1_1[Procedure: proposal]
    D_group_1_1 -->|CHECKS_FOR| C_group_1_1
  end
  D_group_1_1 -->|RESULTS_IN condition_met=true| REC
```
