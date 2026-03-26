# Ground Truth Rules - Table 8 Row 01

- table: 8
- row: row_01

Recommendation text:

```text
Rivaroxaban 2.5 mg b.i.d. Co-administered with aspirin 100 mg o.d.
```

Ground-truth rules:

```json
[
  {
    "conditions": [
      {
        "entity": "cad",
        "entity_original": "cad",
        "role": "ClinicalCondition",
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
        "entity": "pad",
        "entity_original": "pad",
        "role": "ClinicalCondition",
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
        "entity": "high risk of ischaemic events",
        "entity_original": "high risk of ischaemic events",
        "role": "ClinicalCondition",
        "operator": "PRESENT",
        "threshold": null,
        "unit": null,
        "context": null,
        "logic_type": "AND",
        "logic_group": "and_1",
        "strength": null,
        "level": null,
        "direction": null,
        "_side": "condition"
      }
    ],
    "actions": [
      {
        "entity": "rivaroxaban",
        "entity_original": "rivaroxaban",
        "role": "Medication",
        "operator": "PRESENT",
        "threshold": null,
        "unit": null,
        "context": null,
        "logic_type": "AND",
        "logic_group": "and_1",
        "strength": null,
        "level": null,
        "direction": "POSITIVE",
        "_side": "action"
      },
      {
        "entity": "aspirin",
        "entity_original": "aspirin",
        "role": "Medication",
        "operator": "PRESENT",
        "threshold": null,
        "unit": null,
        "context": null,
        "logic_type": "AND",
        "logic_group": "and_1",
        "strength": null,
        "level": null,
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
  ACT1[Medication: rivaroxaban]
  REC -->|RECOMMENDS_USAGE| ACT1
  ACT2[Medication: aspirin]
  REC -->|RECOMMENDS_USAGE| ACT2
  subgraph Table8Row01_or_1_OR
    D_or_1_1[DecisionNode or_1 s1]
    C_or_1_1[ClinicalCondition: cad]
    D_or_1_1 -->|CHECKS_FOR| C_or_1_1
    D_or_1_2[DecisionNode or_1 s2]
    C_or_1_2[ClinicalCondition: pad]
    D_or_1_2 -->|CHECKS_FOR| C_or_1_2
  end
  subgraph Table8Row01_and_1_AND
    D_and_1_1[DecisionNode and_1 s1]
    C_and_1_1[ClinicalCondition: high risk of ischaemic events]
    D_and_1_1 -->|CHECKS_FOR| C_and_1_1
    D_or_1_1 -->|LEADS_TO condition_met=true| D_and_1_1
    D_or_1_2 -->|LEADS_TO condition_met=true| D_and_1_1
  end
  D_and_1_1 -->|RESULTS_IN condition_met=true| REC
```
