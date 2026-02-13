# Rule JSON v2 (explicit inputs/outputs)

Goal: remove ambiguity by separating rule left side (inputs/eligibility) from right side (outputs/actions).

## Format

```json
{
  "rule_id": 1,
  "conditions": [
    {
      "entity": "percutaneous revascularization",
      "entity_original": "patients scheduled for percutaneous revascularization",
      "role": "Procedure",
      "logic": {
        "operator": "PLANNED",
        "threshold": null,
        "unit": null,
        "condition_context": "scheduled for",
        "logic_type": "AND",
        "logic_group": "and_1"
      }
    },
    {
      "entity": "surgical revascularization",
      "entity_original": "patients scheduled for surgical revascularization",
      "role": "Procedure",
      "logic": {
        "operator": "PLANNED",
        "threshold": null,
        "unit": null,
        "condition_context": "scheduled for",
        "logic_type": "AND",
        "logic_group": "and_1"
      }
    }
  ],
  "actions": [
    {
      "entity": "benefits of revascularization",
      "entity_original": "provide information about benefits of revascularization",
      "role": "Procedure",
      "recommendation": {
        "strength": "I",
        "level": "C",
        "direction": "POSITIVE"
      }
    }
  ]
}
```

Notes:
- Conditions contain logic (operator, threshold, logic_type/group). Actions contain recommendation (class/level/direction).
- Procedures can appear in conditions when they are eligibility conditions (e.g., scheduled/planned procedures).
- Use operator "PLANNED" for procedures that are not yet executed.

## Mapping from current format

- Old: list of mixed items with role/logic_structured.
- New: split into conditions and actions.
  - Conditions: items with conditional meaning (eligibility, state, parameter, planned procedure).
  - Actions: items that are recommendations/actions.
- Keep rule_id grouping exactly as before.

## LLM prompt requirements (summary)

- Always output rules with explicit conditions and actions.
- Never mix conditions and actions in the same list.
- Conditions must include logic (operator/threshold/unit/logic_type/logic_group).
- Actions must include recommendation (strength/level/direction) and no logic fields.
- Use operator "PLANNED" when a procedure is scheduled or planned.
- Use operator "PRESENT" for non-numeric conditions.
