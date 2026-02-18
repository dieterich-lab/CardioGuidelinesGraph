# row_13 (mapped to row_13)

Original table row text (ground truth):

```json
{
  "Recommendations": "In patients with complex CAD in whom revascularization is being considered, it is recommended to assess procedural risks and post-procedural outcomes to guide shared clinical decision-making.",
  "Class a": "I",
  "Level b": "C"
}
```

Aligned JSON (expected vs actual):

<table>
  <tr>
    <th align="left">Human Annotation</th>
    <th align="left">LLM Generated</th>
  </tr>
  <tr>
    <td valign="top"><pre>
[
  {
    "rule_id": 1,
    "conditions": [
      {
        "entity": "complex cad",
        "entity_original": "patients with complex cad",
        "role": "Condition",
        "operator": "PRESENT",
        "threshold": null,
        "unit": null,
        "condition_context": null,
        "logic_type": "AND",
        "logic_group": "and_1",
        "strength": null,
        "level": null,
        "direction": null
      },
      {
        "entity": "revascularization is being considered",
        "entity_original": "patients in whom revascularization is being considered",
        "role": "Condition",
        "operator": "PRESENT",
        "threshold": null,
        "unit": null,
        "condition_context": null,
        "logic_type": "AND",
        "logic_group": "and_1",
        "strength": null,
        "level": null,
        "direction": null
      }
    ],
    "actions": [
      {
        "entity": "procedural risks",
        "entity_original": "assess procedural risks",
        "role": "Procedure",
        "operator": null,
        "threshold": null,
        "unit": null,
        "condition_context": null,
        "logic_type": null,
        "logic_group": null,
        "strength": "I",
        "level": "C",
        "direction": "POSITIVE"
      },
      {
        "entity": "post-procedural outcomes",
        "entity_original": "assess post-procedural outcomes",
        "role": "Procedure",
        "operator": null,
        "threshold": null,
        "unit": null,
        "condition_context": null,
        "logic_type": null,
        "logic_group": null,
        "strength": "I",
        "level": "C",
        "direction": "POSITIVE"
      },
      {
        "entity": "shared clinical decision-making",
        "entity_original": "take part in shared clinical decision-making",
        "role": "Procedure",
        "operator": null,
        "threshold": null,
        "unit": null,
        "condition_context": null,
        "logic_type": null,
        "logic_group": null,
        "strength": "I",
        "level": "C",
        "direction": "POSITIVE"
      }
    ]
  }
]
</pre></td>
    <td valign="top"><pre>
{
  "1": {
    "conditions": [
      {
        "entity": "coronary artery disease, complex",
        "entity_original": "complex cad",
        "role": "ClinicalParameter",
        "operator": "PRESENT",
        "threshold": null,
        "unit": null,
        "condition_context": null,
        "logic_type": null,
        "logic_group": null,
        "strength": "I",
        "level": "C",
        "direction": "POSITIVE",
        "rule_id": 1,
        "side": "condition",
        "preferred_term": null,
        "synonyms": [],
        "snomed_id": null,
        "target_label": "ClinicalParameter",
        "taxonomy_path": [],
        "root_concept_id": null,
        "root_concept_term": null,
        "mapped_target_label": null
      }
    ],
    "actions": [
      {
        "entity": "revascularization procedure",
        "entity_original": "revascularization is being considered",
        "role": "Procedure",
        "operator": "PLANNED",
        "threshold": null,
        "unit": null,
        "condition_context": null,
        "logic_type": null,
        "logic_group": null,
        "strength": "I",
        "level": "C",
        "direction": "POSITIVE",
        "rule_id": 1,
        "side": "action",
        "preferred_term": "Limb revascularization (procedure)",
        "synonyms": [],
        "snomed_id": 233497001,
        "target_label": "Procedure",
        "taxonomy_path": [
          {
            "concept_id": "233497001",
            "term": "Limb revascularization (procedure)"
          },
          {
            "concept_id": "22701007",
            "term": "Operative procedure on artery of extremity (procedure)"
          },
          {
            "concept_id": "363187007",
            "term": "Limb operation (procedure)"
          },
          {
            "concept_id": "387713003",
            "term": "Surgical procedure (procedure)"
          },
          {
            "concept_id": "71388002",
            "term": "Procedure (procedure)"
          }
        ],
        "root_concept_id": "71388002",
        "root_concept_term": "Procedure (procedure)",
        "mapped_target_label": "Procedure"
      },
      {
        "entity": "assessment of procedural risks and outcomes",
        "entity_original": "assess procedural risks and post-procedural outcomes",
        "role": "Procedure",
        "operator": null,
        "threshold": null,
        "unit": null,
        "condition_context": null,
        "logic_type": null,
        "logic_group": null,
        "strength": "I",
        "level": "C",
        "direction": "POSITIVE",
        "rule_id": 1,
        "side": "action",
        "preferred_term": "Assessment using Bakas Caregiving Outcomes Scales (procedure)",
        "synonyms": [
          "Assessment using Bakas Caregiving Outcomes Scales",
          "Assessment using BCOS (Bakas Caregiving Outcomes Scales)"
        ],
        "snomed_id": 865916003,
        "target_label": "Procedure",
        "taxonomy_path": [
          {
            "concept_id": "865916003",
            "term": "Assessment using Bakas Caregiving Outcomes Scales (procedure)"
          },
          {
            "concept_id": "445536008",
            "term": "Assessment using assessment scale (procedure)"
          },
          {
            "concept_id": "386053000",
            "term": "Evaluation procedure (procedure)"
          },
          {
            "concept_id": "128927009",
            "term": "Procedure by method (procedure)"
          },
          {
            "concept_id": "71388002",
            "term": "Procedure (procedure)"
          },
          {
            "concept_id": "138875005",
            "term": "SNOMED CT Concept (SNOMED RT+CTV3)"
          }
        ],
        "root_concept_id": "71388002",
        "root_concept_term": "Procedure (procedure)",
        "mapped_target_label": "Procedure"
      }
    ]
  }
}
</pre></td>
  </tr>
</table>

Mermaid (Human Annotation):

```mermaid
graph LR
  REC[RecommendationNode]
  ACT1[Procedure: procedural risks]
  REC -->|RECOMMENDS_PROCEDURE| ACT1
  ACT2[Procedure: post-procedural outcomes]
  REC -->|RECOMMENDS_PROCEDURE| ACT2
  ACT3[Procedure: shared clinical decision-making]
  REC -->|RECOMMENDS_PROCEDURE| ACT3
  subgraph Human_and_1_AND
    D_and_1_1[DecisionNode and_1 s1]
    C_and_1_1[Condition: complex cad]
    D_and_1_1 -->|CHECKS_FOR| C_and_1_1
    D_and_1_2[DecisionNode and_1 s2]
    C_and_1_2[Condition: revascularization is being considered]
    D_and_1_2 -->|CHECKS_FOR| C_and_1_2
    D_and_1_1 -->|LEADS_TO condition_met=true| D_and_1_2
  end
  D_and_1_2 -->|RESULTS_IN condition_met=true| REC
```

Mermaid (LLM Generated):

```mermaid
graph LR
  REC[RecommendationNode]
  ACT1[Procedure: assessment of procedural risks and outcomes]
  REC -->|RECOMMENDS_PROCEDURE| ACT1
  ACT2[Procedure: revascularization procedure]
  REC -->|RECOMMENDS_PROCEDURE| ACT2
  subgraph LLM_group_1_AND
    D_group_1_1[DecisionNode group_1 s1]
    C_group_1_1[ClinicalParameter: coronary artery disease, complex]
    D_group_1_1 -->|EVALUATES| C_group_1_1
  end
  D_group_1_1 -->|RESULTS_IN condition_met=true| REC
```

Grounding summary (optional):

```json
{
  "enabled": true,
  "total_grounded": 3,
  "target_label_counts": {
    "ClinicalParameter": 1,
    "Procedure": 2
  },
  "root_hit_counts": {
    "71388002": 2
  },
  "root_hits": [
    {
      "entity": "Coronary Artery Disease, Complex",
      "entity_original": "complex CAD",
      "role": "ClinicalParameter",
      "preferred_term": null,
      "synonyms": [],
      "snomed_id": null,
      "target_label": "ClinicalParameter",
      "taxonomy_path": [],
      "root_hit": null
    },
    {
      "entity": "Revascularization Procedure",
      "entity_original": "revascularization is being considered",
      "role": "Procedure",
      "preferred_term": "Limb revascularization (procedure)",
      "synonyms": [],
      "snomed_id": 233497001,
      "target_label": "Procedure",
      "taxonomy_path": [
        {
          "concept_id": "233497001",
          "term": "Limb revascularization (procedure)"
        },
        {
          "concept_id": "22701007",
          "term": "Operative procedure on artery of extremity (procedure)"
        },
        {
          "concept_id": "363187007",
          "term": "Limb operation (procedure)"
        },
        {
          "concept_id": "387713003",
          "term": "Surgical procedure (procedure)"
        },
        {
          "concept_id": "71388002",
          "term": "Procedure (procedure)"
        }
      ],
      "root_hit": {
        "root_concept_id": "71388002",
        "root_concept_term": "Procedure (procedure)",
        "mapped_target_label": "Procedure"
      }
    },
    {
      "entity": "Assessment of Procedural Risks and Outcomes",
      "entity_original": "assess procedural risks and post-procedural outcomes",
      "role": "Procedure",
      "preferred_term": "Assessment using Bakas Caregiving Outcomes Scales (procedure)",
      "synonyms": [
        "Assessment using Bakas Caregiving Outcomes Scales",
        "Assessment using BCOS (Bakas Caregiving Outcomes Scales)"
      ],
      "snomed_id": 865916003,
      "target_label": "Procedure",
      "taxonomy_path": [
        {
          "concept_id": "865916003",
          "term": "Assessment using Bakas Caregiving Outcomes Scales (procedure)"
        },
        {
          "concept_id": "445536008",
          "term": "Assessment using assessment scale (procedure)"
        },
        {
          "concept_id": "386053000",
          "term": "Evaluation procedure (procedure)"
        },
        {
          "concept_id": "128927009",
          "term": "Procedure by method (procedure)"
        },
        {
          "concept_id": "71388002",
          "term": "Procedure (procedure)"
        },
        {
          "concept_id": "138875005",
          "term": "SNOMED CT Concept (SNOMED RT+CTV3)"
        }
      ],
      "root_hit": {
        "root_concept_id": "71388002",
        "root_concept_term": "Procedure (procedure)",
        "mapped_target_label": "Procedure"
      }
    }
  ]
}
```

Concepts:
- expected: 5
- actual: 3
- matches: 0
- missing: 5
- extra: 3

Missing concepts:
- Condition: complex cad
- Condition: revascularization is being considered
- Procedure: post-procedural outcomes
- Procedure: procedural risks
- Procedure: shared clinical decision-making

Extra concepts:
- ClinicalParameter: coronary artery disease, complex
- Procedure: assessment of procedural risks and outcomes
- Procedure: revascularization procedure

Rules (concept + logic fields):
- expected: 5
- actual: 3
- matches: 0
- missing: 5
- extra: 3

Missing rules:
- Condition: complex cad | op=PRESENT | logic=AND | grp=and_1
- Condition: revascularization is being considered | op=PRESENT | logic=AND | grp=and_1
- Procedure: post-procedural outcomes | class=I | level=C | dir=POSITIVE
- Procedure: procedural risks | class=I | level=C | dir=POSITIVE
- Procedure: shared clinical decision-making | class=I | level=C | dir=POSITIVE

Extra rules:
- ClinicalParameter: coronary artery disease, complex | op=PRESENT | class=I | level=C | dir=POSITIVE
- Procedure: assessment of procedural risks and outcomes | class=I | level=C | dir=POSITIVE
- Procedure: revascularization procedure | op=PLANNED | class=I | level=C | dir=POSITIVE

