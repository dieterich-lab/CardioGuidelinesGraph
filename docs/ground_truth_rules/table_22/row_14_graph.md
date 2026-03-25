# Ground Truth Rules - Table 22 Row 14

- table: 22
- row: row_14

Recommendation text:

```text
Calculation of the STS score is recommended to estimate in-hospital morbidity and 30-day mortality after CABG
```

Ground-truth rules:

```json
[
  {
    "conditions": [
      {
        "entity": "cabg",
        "entity_original": "cabg",
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
        "entity": "calculation of the sts score",
        "entity_original": "calculation of the sts score",
        "role": "Procedure",
        "operator": null,
        "threshold": null,
        "unit": null,
        "context": null,
        "logic_type": null,
        "logic_group": null,
        "strength": "I",
        "level": "B",
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
  ACT1[Procedure: calculation of the sts score]
  REC -->|RECOMMENDS_PROCEDURE| ACT1
  subgraph Table22Row14_group_1_AND
    D_group_1_1[DecisionNode group_1 s1]
    C_group_1_1[Procedure: cabg]
    D_group_1_1 -->|CHECKS_FOR| C_group_1_1
  end
  D_group_1_1 -->|RESULTS_IN condition_met=true| REC
```
