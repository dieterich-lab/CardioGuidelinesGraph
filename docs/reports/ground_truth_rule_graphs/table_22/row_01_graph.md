# Ground Truth Rules - Table 22 Row 01

- table: 22
- row: row_01

Recommendation text:

```text
patients receive complete information about the benefits, risks, therapeutic consequences, and alternatives to revascularization, as part of shared clinical decision-making.
```

Ground-truth rules:

```json
[
  {
    "conditions": [
      {
        "entity": "percutaneous revascularization",
        "entity_original": "percutaneous revascularization",
        "role": "Procedure",
        "operator": "PRESENT",
        "threshold": null,
        "unit": null,
        "context": null,
        "logic_type": "OR",
        "logic_group": "or_1",
        "strength": null,
        "level": null,
        "direction": null,
        "_side": "condition"
      },
      {
        "entity": "surgical revascularization",
        "entity_original": "surgical revascularization",
        "role": "Procedure",
        "operator": "PRESENT",
        "threshold": null,
        "unit": null,
        "context": null,
        "logic_type": "OR",
        "logic_group": "or_1",
        "strength": null,
        "level": null,
        "direction": null,
        "_side": "condition"
      }
    ],
    "actions": [
      {
        "entity": "provide information",
        "entity_original": "provide information",
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
      },
      {
        "entity": "shared clinical decision-making",
        "entity_original": "shared clinical decision-making",
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
  ACT1[Procedure: provide information]
  REC -->|RECOMMENDS_PROCEDURE| ACT1
  ACT2[Procedure: shared clinical decision-making]
  REC -->|RECOMMENDS_PROCEDURE| ACT2
  subgraph Table22Row01_or_1_OR
    D_or_1_1[DecisionNode or_1 s1]
    C_or_1_1[Procedure: percutaneous revascularization]
    D_or_1_1 -->|CHECKS_FOR| C_or_1_1
    D_or_1_2[DecisionNode or_1 s2]
    C_or_1_2[Procedure: surgical revascularization]
    D_or_1_2 -->|CHECKS_FOR| C_or_1_2
  end
  D_or_1_1 -->|RESULTS_IN condition_met=true| REC
  D_or_1_2 -->|RESULTS_IN condition_met=true| REC
```
