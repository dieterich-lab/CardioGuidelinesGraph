# Ground Truth Rules - Table 22 Row 16

- table: 22
- row: row_16

Recommendation text:

```text
Intracoronary imaging guidance by IVUS or OCTis recommended
```

Ground-truth rules:

```json
[
  {
    "conditions": [
      {
        "entity": "pci",
        "entity_original": "pci",
        "role": "Procedure",
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
        "entity": "anatomically complex lesions",
        "entity_original": "anatomically complex lesions",
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
        "entity": "left main stem lesions",
        "entity_original": "left main stem lesions",
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
        "entity": "true bifurcations lesions",
        "entity_original": "true bifurcations lesions",
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
        "entity": "long lesions",
        "entity_original": "long lesions",
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
      }
    ],
    "actions": [
      {
        "entity": "intracoronary imaging guidance by ivus recommended",
        "entity_original": "intracoronary imaging guidance by ivus recommended",
        "role": "Procedure",
        "operator": null,
        "threshold": null,
        "unit": null,
        "context": null,
        "logic_type": null,
        "logic_group": null,
        "strength": "I",
        "level": "A",
        "direction": "POSITIVE",
        "_side": "action"
      },
      {
        "entity": "intracoronary imaging guidance by octis recommended",
        "entity_original": "intracoronary imaging guidance by octis recommended",
        "role": "Procedure",
        "operator": null,
        "threshold": null,
        "unit": null,
        "context": null,
        "logic_type": null,
        "logic_group": null,
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
  ACT1[Procedure: intracoronary imaging guidance by ivus recommended]
  REC -->|RECOMMENDS_PROCEDURE| ACT1
  ACT2[Procedure: intracoronary imaging guidance by octis recommended]
  REC -->|RECOMMENDS_PROCEDURE| ACT2
  subgraph Table22Row16_and_1_AND
    D_and_1_1[DecisionNode and_1 s1]
    C_and_1_1[Procedure: pci]
    D_and_1_1 -->|CHECKS_FOR| C_and_1_1
  end
  subgraph Table22Row16_or_1_OR
    D_or_1_1[DecisionNode or_1 s1]
    C_or_1_1[ClinicalCondition: anatomically complex lesions]
    D_or_1_1 -->|CHECKS_FOR| C_or_1_1
    D_or_1_2[DecisionNode or_1 s2]
    C_or_1_2[ClinicalCondition: left main stem lesions]
    D_or_1_2 -->|CHECKS_FOR| C_or_1_2
    D_or_1_3[DecisionNode or_1 s3]
    C_or_1_3[ClinicalCondition: true bifurcations lesions]
    D_or_1_3 -->|CHECKS_FOR| C_or_1_3
    D_or_1_4[DecisionNode or_1 s4]
    C_or_1_4[ClinicalCondition: long lesions]
    D_or_1_4 -->|CHECKS_FOR| C_or_1_4
    D_and_1_1 -->|LEADS_TO condition_met=true| D_or_1_1
    D_and_1_1 -->|LEADS_TO condition_met=true| D_or_1_2
    D_and_1_1 -->|LEADS_TO condition_met=true| D_or_1_3
    D_and_1_1 -->|LEADS_TO condition_met=true| D_or_1_4
  end
  D_or_1_1 -->|RESULTS_IN condition_met=true| REC
  D_or_1_2 -->|RESULTS_IN condition_met=true| REC
  D_or_1_3 -->|RESULTS_IN condition_met=true| REC
  D_or_1_4 -->|RESULTS_IN condition_met=true| REC
```
