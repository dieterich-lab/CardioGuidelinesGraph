# Ground Truth Rules - Table 22 Row 15

- table: 22
- row: row_15

Recommendation text:

```text
calculation of the SYNTAX score is recommended to assess the anatomical complexity of disease
```

Ground-truth rules:

```json
[
  {
    "conditions": [
      {
        "entity": "patients with multivessel obstructive cad",
        "entity_original": "patients with multivessel obstructive cad",
        "role": "ClinicalCondition",
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
        "entity": "calculation of the syntax score is recommended to assess the anatomical complexity of disease",
        "entity_original": "calculation of the syntax score is recommended to assess the anatomical complexity of disease",
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
  ACT1[Procedure: calculation of the syntax score is recommended to assess the anatomical complexity of disease]
  REC -->|RECOMMENDS_PROCEDURE| ACT1
  subgraph Table22Row15_group_1_AND
    D_group_1_1[DecisionNode group_1 s1]
    C_group_1_1[ClinicalCondition: patients with multivessel obstructive cad]
    D_group_1_1 -->|CHECKS_FOR| C_group_1_1
  end
  D_group_1_1 -->|RESULTS_IN condition_met=true| REC
```
