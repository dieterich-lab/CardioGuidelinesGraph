# row_01 (mapped to row_01)

Original table row text (ground truth):

```json
{
  "Recommendations": "It is recommended that patients scheduled for percutaneous or surgical revascularization receive complete information about the benefits, risks, therapeutic consequences, and alternatives to revascularization, as part of shared clinical decision-making. 847,848,857",
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
    "conditions": [
      {
        "entity": "percutaneous revascularization",
        "entity_original": "patients scheduled for percutaneous revascularization",
        "role": "Procedure",
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
</pre></td>
    <td valign="top"><pre>
{
  "rules": [
    {
      "conditions": [
        {
          "entity": "percutaneous revascularization",
          "entity_original": "percutaneous revascularization",
          "role": "Procedure",
          "operator": "PLANNED",
          "threshold": null,
          "unit": null,
          "context": null,
          "logic_type": "OR",
          "logic_group": "or_1",
          "strength": "Unknown",
          "level": "Unknown",
          "direction": null,
          "preferred_term": "Heart revascularization (procedure)",
          "synonyms": [
            "Heart revascularisation",
            "Heart revascularization"
          ],
          "snomed_id": 81266008,
          "target_label": "Procedure",
          "taxonomy_path": [
            {
              "concept_id": "81266008",
              "term": "Heart revascularization (procedure)"
            },
            {
              "concept_id": "31413008",
              "term": "Operative procedure on coronary artery (procedure)"
            },
            {
              "concept_id": "118806004",
              "term": "Procedure on coronary arteries (procedure)"
            },
            {
              "concept_id": "118797008",
              "term": "Procedure on heart (procedure)"
            },
            {
              "concept_id": "118672003",
              "term": "Procedure on cardiovascular system (procedure)"
            },
            {
              "concept_id": "118664000",
              "term": "Procedure on body system (procedure)"
            },
            {
              "concept_id": "362958002",
              "term": "Procedure by site (procedure)"
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
          "root_concept_term": "Procedure (procedure)"
        },
        {
          "entity": "surgical revascularization",
          "entity_original": "surgical revascularization",
          "role": "Procedure",
          "operator": "PLANNED",
          "threshold": null,
          "unit": null,
          "context": null,
          "logic_type": "OR",
          "logic_group": "or_1",
          "strength": "Unknown",
          "level": "Unknown",
          "direction": null,
          "preferred_term": "Bronchial revascularization (procedure)",
          "synonyms": [
            "Bronchial revascularization",
            "Bronchial revascularisation"
          ],
          "snomed_id": 277437006,
          "target_label": "Procedure",
          "taxonomy_path": [
            {
              "concept_id": "277437006",
              "term": "Bronchial revascularization (procedure)"
            },
            {
              "concept_id": "26476002",
              "term": "Operation on bronchus (procedure)"
            },
            {
              "concept_id": "118793007",
              "term": "Procedure on bronchus (procedure)"
            },
            {
              "concept_id": "129254006",
              "term": "Procedure on tracheobronchial tree (procedure)"
            },
            {
              "concept_id": "118717007",
              "term": "Procedure on organ (procedure)"
            },
            {
              "concept_id": "362958002",
              "term": "Procedure by site (procedure)"
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
          "root_concept_term": "Procedure (procedure)"
        }
      ],
      "actions": [
        {
          "entity": "revascularization procedure planned",
          "entity_original": "patients scheduled for percutaneous or surgical revascularization",
          "role": "Procedure",
          "operator": "PLANNED",
          "threshold": null,
          "unit": null,
          "context": null,
          "logic_type": null,
          "logic_group": null,
          "strength": null,
          "level": null,
          "direction": "UNKNOWN",
          "preferred_term": "Limb revascularization (procedure)",
          "synonyms": [
            "Limb revascularisation",
            "Limb revascularization"
          ],
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
          "root_concept_term": "Procedure (procedure)"
        }
      ]
    }
  ]
}
</pre></td>
  </tr>
</table>

Mermaid (Human Annotation):

```mermaid
graph LR
  REC[RecommendationNode]
  ACT1[Procedure: percutaneous revascularization]
  REC -->|RECOMMENDS_PROCEDURE| ACT1
  ACT2[Procedure: surgical revascularization]
  REC -->|RECOMMENDS_PROCEDURE| ACT2
```

Mermaid (LLM Generated):

```mermaid
graph LR
  REC[RecommendationNode]
  ACT1[Procedure: percutaneous revascularization]
  REC -->|RECOMMENDS_PROCEDURE| ACT1
  ACT2[Procedure: revascularization procedure planned]
  REC -->|RECOMMENDS_PROCEDURE| ACT2
  ACT3[Procedure: shared decision-making information provision]
  REC -->|RECOMMENDS_PROCEDURE| ACT3
  ACT4[Procedure: surgical revascularization]
  REC -->|RECOMMENDS_PROCEDURE| ACT4
```

Grounding summary (optional):

```json
{
  "enabled": true,
  "total_grounded": 3,
  "target_label_counts": {
    "Procedure": 3
  },
  "root_hit_counts": {
    "71388002": 3
  },
  "root_hits": [
    {
      "entity": "Revascularization procedure PLANNED",
      "entity_original": "patients scheduled for percutaneous or surgical revascularization",
      "role": "Procedure",
      "preferred_term": "Limb revascularization (procedure)",
      "synonyms": [
        "Limb revascularisation",
        "Limb revascularization"
      ],
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
    },
    {
      "entity": "Percutaneous revascularization",
      "entity_original": "percutaneous revascularization",
      "role": "Procedure",
      "preferred_term": "Heart revascularization (procedure)",
      "synonyms": [
        "Heart revascularisation",
        "Heart revascularization"
      ],
      "snomed_id": 81266008,
      "target_label": "Procedure",
      "taxonomy_path": [
        {
          "concept_id": "81266008",
          "term": "Heart revascularization (procedure)"
        },
        {
          "concept_id": "31413008",
          "term": "Operative procedure on coronary artery (procedure)"
        },
        {
          "concept_id": "118806004",
          "term": "Procedure on coronary arteries (procedure)"
        },
        {
          "concept_id": "118797008",
          "term": "Procedure on heart (procedure)"
        },
        {
          "concept_id": "118672003",
          "term": "Procedure on cardiovascular system (procedure)"
        },
        {
          "concept_id": "118664000",
          "term": "Procedure on body system (procedure)"
        },
        {
          "concept_id": "362958002",
          "term": "Procedure by site (procedure)"
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
    },
    {
      "entity": "Surgical revascularization",
      "entity_original": "surgical revascularization",
      "role": "Procedure",
      "preferred_term": "Bronchial revascularization (procedure)",
      "synonyms": [
        "Bronchial revascularization",
        "Bronchial revascularisation"
      ],
      "snomed_id": 277437006,
      "target_label": "Procedure",
      "taxonomy_path": [
        {
          "concept_id": "277437006",
          "term": "Bronchial revascularization (procedure)"
        },
        {
          "concept_id": "26476002",
          "term": "Operation on bronchus (procedure)"
        },
        {
          "concept_id": "118793007",
          "term": "Procedure on bronchus (procedure)"
        },
        {
          "concept_id": "129254006",
          "term": "Procedure on tracheobronchial tree (procedure)"
        },
        {
          "concept_id": "118717007",
          "term": "Procedure on organ (procedure)"
        },
        {
          "concept_id": "362958002",
          "term": "Procedure by site (procedure)"
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
- expected: 7
- actual: 4
- matches: 2
- missing: 5
- extra: 2

Missing concepts:
- ClinicalAction: benefits of revascularization
- ClinicalAction: risks of revascularization
- ClinicalAction: shared decision-making
- ClinicalAction: therapeutic consequences of revascularization
- ClinicalAction: treatment alternatives of revascularization

Extra concepts:
- Procedure: revascularization procedure planned
- Procedure: shared decision-making information provision

Rules (concept + logic fields):
- expected: 7
- actual: 4
- matches: 0
- missing: 7
- extra: 4

Missing rules:
- ClinicalAction: benefits of revascularization | class=I | level=C | dir=POSITIVE
- ClinicalAction: risks of revascularization | class=I | level=C | dir=POSITIVE
- ClinicalAction: shared decision-making | class=I | level=C | dir=POSITIVE
- ClinicalAction: therapeutic consequences of revascularization | class=I | level=C | dir=POSITIVE
- ClinicalAction: treatment alternatives of revascularization | class=I | level=C | dir=POSITIVE
- Procedure: percutaneous revascularization | op=PRESENT | logic=OR | grp=or_1
- Procedure: surgical revascularization | op=PRESENT | logic=OR | grp=or_1

Extra rules:
- Procedure: percutaneous revascularization | op=PLANNED | logic=OR | grp=or_1 | class=Unknown | level=Unknown
- Procedure: revascularization procedure planned | op=PLANNED | dir=UNKNOWN
- Procedure: shared decision-making information provision | class=Class I | level=C | dir=POSITIVE
- Procedure: surgical revascularization | op=PLANNED | logic=OR | grp=or_1 | class=Unknown | level=Unknown

