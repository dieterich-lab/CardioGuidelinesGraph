# row_01

## Ground Truth

```json
{
  "rules": [
    {
      "conditions": [
        {
          "entity": "percutaneous revascularization",
          "entity_original": "patients scheduled for percutaneous revascularization",
          "role": "Procedure",
          "side": "condition",
          "operator": "PRESENT",
          "threshold": null,
          "unit": null,
          "context": null,
          "logic_type": "OR",
          "logic_group": "or_1",
          "strength": null,
          "level": null,
          "direction": null
        },
        {
          "entity": "surgical revascularization",
          "entity_original": "patients scheduled for surgical revascularization",
          "role": "Procedure",
          "side": "condition",
          "operator": "PRESENT",
          "threshold": null,
          "unit": null,
          "context": null,
          "logic_type": "OR",
          "logic_group": "or_1",
          "strength": null,
          "level": null,
          "direction": null
        }
      ],
      "actions": [
        {
          "entity": "benefits of revascularization",
          "entity_original": "provide information about benefits of revascularization",
          "role": "ClinicalAction",
          "side": "action",
          "operator": null,
          "threshold": null,
          "unit": null,
          "context": null,
          "logic_type": null,
          "logic_group": null,
          "strength": "I",
          "level": "C",
          "direction": "POSITIVE"
        },
        {
          "entity": "risks of revascularization",
          "entity_original": "provide information about risks of revascularization",
          "role": "ClinicalAction",
          "side": "action",
          "operator": null,
          "threshold": null,
          "unit": null,
          "context": null,
          "logic_type": null,
          "logic_group": null,
          "strength": "I",
          "level": "C",
          "direction": "POSITIVE"
        },
        {
          "entity": "therapeutic consequences of revascularization",
          "entity_original": "receive information about therapeutic consequences of revascularization",
          "role": "ClinicalAction",
          "side": "action",
          "operator": null,
          "threshold": null,
          "unit": null,
          "context": null,
          "logic_type": null,
          "logic_group": null,
          "strength": "I",
          "level": "C",
          "direction": "POSITIVE"
        },
        {
          "entity": "treatment alternatives of revascularization",
          "entity_original": "provide information about treatment alternatives of revascularization",
          "role": "ClinicalAction",
          "side": "action",
          "operator": null,
          "threshold": null,
          "unit": null,
          "context": null,
          "logic_type": null,
          "logic_group": null,
          "strength": "I",
          "level": "C",
          "direction": "POSITIVE"
        },
        {
          "entity": "shared decision-making",
          "entity_original": "take part in shared clinical decision-making",
          "role": "ClinicalAction",
          "side": "action",
          "operator": null,
          "threshold": null,
          "unit": null,
          "context": null,
          "logic_type": null,
          "logic_group": null,
          "strength": "I",
          "level": "C",
          "direction": "POSITIVE"
        }
      ]
    }
  ]
}
```

## Extracted

```json
{
  "rules": [
    {
      "conditions": [],
      "actions": [
        {
          "entity": "scheduled for percutaneous or surgical revascularization",
          "entity_original": "patients scheduled for percutaneous or surgical revascularization",
          "role": "Procedure",
          "side": "action",
          "operator": "PLANNED",
          "threshold": null,
          "unit": null,
          "context": null,
          "logic_type": null,
          "logic_group": null,
          "strength": "Class I",
          "level": "C",
          "direction": "POSITIVE"
        },
        {
          "entity": "provide complete information about benefits, risks, therapeutic consequences, and alternatives to revascularization as part of shared clinical decision-making",
          "entity_original": "patients receive complete information about the benefits, risks, therapeutic consequences, and alternatives to revascularization, as part of shared clinical decision-making",
          "role": "Procedure",
          "side": "action",
          "operator": null,
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
```

## Mermaid

```mermaid
graph TD
C0["percutaneous revascularization"]
C1["surgical revascularization"]
A2["benefits of revascularization"]
A3["risks of revascularization"]
A4["therapeutic consequences of revascularization"]
A5["treatment alternatives of revascularization"]
A6["shared decision-making"]
A7["scheduled for percutaneous or surgical revascularization"]
A8["provide complete information about benefits, risks, therapeutic consequences, and alternatives to revascularization as part of shared clinical decision-making"]
C0 --> A2
C0 --> A3
C0 --> A4
C0 --> A5
C0 --> A6
C0 --> A7
C0 --> A8
C1 --> A2
C1 --> A3
C1 --> A4
C1 --> A5
C1 --> A6
C1 --> A7
C1 --> A8
```

Match Score: 0.29
