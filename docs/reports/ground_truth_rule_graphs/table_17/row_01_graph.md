# Ground Truth Rules - Table 17 Row 01

- table: 17
- row: row_01

Recommendation text:

```text
aspirin 75–100 mg daily is recommended lifelong after an initial period of DAPT
```

Ground-truth rules:

```json
[
  {
    "conditions": [
      {
        "entity": "ccs",
        "entity_original": "ccs",
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
      },
      {
        "entity": "prior mi",
        "entity_original": "prior mi",
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
        "entity": "pci",
        "entity_original": "pci",
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
        "entity": "aspirin",
        "entity_original": "aspirin",
        "role": "Medication",
        "operator": "PRESENT",
        "threshold": null,
        "unit": null,
        "context": null,
        "logic_type": "AND",
        "logic_group": "and_1",
        "strength": "I",
        "level": "A",
        "direction": "POSITIVE",
        "_side": "action"
      },
      {
        "entity": "dapt",
        "entity_original": "dapt",
        "role": "Medication",
        "operator": "PRESENT",
        "threshold": null,
        "unit": null,
        "context": null,
        "logic_type": "AND",
        "logic_group": "and_1",
        "strength": "I",
        "level": "A",
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
  ACT1[Medication: aspirin]
  REC -->|RECOMMENDS_USAGE| ACT1
  ACT2[Medication: dapt]
  REC -->|RECOMMENDS_USAGE| ACT2
  subgraph Table17Row01_and_1_AND
    D_and_1_1[DecisionNode and_1 s1]
    C_and_1_1[ClinicalCondition: ccs]
    D_and_1_1 -->|CHECKS_FOR| C_and_1_1
  end
  subgraph Table17Row01_or_1_OR
    D_or_1_1[DecisionNode or_1 s1]
    C_or_1_1[ClinicalCondition: prior mi]
    D_or_1_1 -->|CHECKS_FOR| C_or_1_1
    D_or_1_2[DecisionNode or_1 s2]
    C_or_1_2[Procedure: pci]
    D_or_1_2 -->|CHECKS_FOR| C_or_1_2
    D_and_1_1 -->|LEADS_TO condition_met=true| D_or_1_1
    D_and_1_1 -->|LEADS_TO condition_met=true| D_or_1_2
  end
  D_or_1_1 -->|RESULTS_IN condition_met=true| REC
  D_or_1_2 -->|RESULTS_IN condition_met=true| REC
```
