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
    "rule_id": 1,
    "conditions": [
      {
        "entity": "percutaneous revascularization",
        "entity_original": "patients scheduled for percutaneous revascularization",
        "role": "Procedure",
        "operator": "PRESENT",
        "threshold": null,
        "unit": null,
        "condition_context": null,
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
        "condition_context": null,
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
        "entity": "risks of revascularization",
        "entity_original": "provide information about risks of revascularization",
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
        "entity": "therapeutic consequences of revascularization",
        "entity_original": "receive information about therapeutic consequences of revascularization",
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
        "entity": "treatment alternatives of revascularization",
        "entity_original": "provide information about treatment alternatives of revascularization",
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
        "entity": "shared decision-making",
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
        "entity": "percutaneous revascularization",
        "entity_original": "scheduled for percutaneous or surgical revascularization",
        "role": "Procedure",
        "operator": "PLANNED",
        "threshold": null,
        "unit": null,
        "condition_context": "scheduled",
        "logic_type": "OR",
        "logic_group": "or_1",
        "strength": "Unknown",
        "level": "Unknown",
        "direction": "UNKNOWN",
        "rule_id": 1,
        "side": "condition",
        "name": "Heart revascularization (procedure)",
        "preferred_term": "Heart revascularization (procedure)",
        "synonyms": [
          "Heart revascularisation",
          "Heart revascularization"
        ],
        "alt_names": [
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
        "root_concept_term": "Procedure (procedure)",
        "mapped_target_label": "Procedure"
      },
      {
        "entity": "surgical revascularization",
        "entity_original": "scheduled for percutaneous or surgical revascularization",
        "role": "Procedure",
        "operator": "PLANNED",
        "threshold": null,
        "unit": null,
        "condition_context": "scheduled",
        "logic_type": "OR",
        "logic_group": "or_1",
        "strength": "Unknown",
        "level": "Unknown",
        "direction": "UNKNOWN",
        "rule_id": 1,
        "side": "condition",
        "name": "Bronchial revascularization (procedure)",
        "preferred_term": "Bronchial revascularization (procedure)",
        "synonyms": [
          "Bronchial revascularization",
          "Bronchial revascularisation"
        ],
        "alt_names": [
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
        "root_concept_term": "Procedure (procedure)",
        "mapped_target_label": "Procedure"
      },
      {
        "entity": "revascularization procedure",
        "entity_original": "percutaneous or surgical revascularization",
        "role": "Procedure",
        "operator": "PLANNED",
        "threshold": null,
        "unit": null,
        "condition_context": "scheduled",
        "logic_type": null,
        "logic_group": null,
        "strength": "Unknown",
        "level": "Unknown",
        "direction": "UNKNOWN",
        "rule_id": 1,
        "side": "condition",
        "name": "Limb revascularization (procedure)",
        "preferred_term": "Limb revascularization (procedure)",
        "synonyms": [],
        "alt_names": [],
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
      }
    ],
    "actions": [
      {
        "entity": "shared clinical decision-making",
        "entity_original": "complete information about the benefits, risks, therapeutic consequences, and alternatives to revascularization",
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
        "name": "Evaluation of decision-making capacity (procedure)",
        "preferred_term": "Evaluation of decision-making capacity (procedure)",
        "synonyms": [
          "Evaluation of decision-making capacity"
        ],
        "alt_names": [
          "Evaluation of decision-making capacity"
        ],
        "snomed_id": 12121000202107,
        "target_label": "Procedure",
        "taxonomy_path": [
          {
            "concept_id": "12121000202107",
            "term": "Evaluation of decision-making capacity (procedure)"
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
      },
      {
        "entity": "shared decision-making information",
        "entity_original": "complete information about the benefits, risks, therapeutic consequences, and alternatives to revascularization",
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
        "name": "Evaluation of decision-making capacity (procedure)",
        "preferred_term": "Evaluation of decision-making capacity (procedure)",
        "synonyms": [
          "Evaluation of decision-making capacity"
        ],
        "alt_names": [
          "Evaluation of decision-making capacity"
        ],
        "snomed_id": 12121000202107,
        "target_label": "Procedure",
        "taxonomy_path": [
          {
            "concept_id": "12121000202107",
            "term": "Evaluation of decision-making capacity (procedure)"
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
  ACT1[Procedure: benefits of revascularization]
  REC -->|RECOMMENDS_PROCEDURE| ACT1
  ACT2[Procedure: risks of revascularization]
  REC -->|RECOMMENDS_PROCEDURE| ACT2
  ACT3[Procedure: therapeutic consequences of revascularization]
  REC -->|RECOMMENDS_PROCEDURE| ACT3
  ACT4[Procedure: treatment alternatives of revascularization]
  REC -->|RECOMMENDS_PROCEDURE| ACT4
  ACT5[Procedure: shared decision-making]
  REC -->|RECOMMENDS_PROCEDURE| ACT5
  subgraph Human_or_1_OR
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

Mermaid (LLM Generated):

```mermaid
graph LR
  REC[RecommendationNode]
  ACT1[Procedure: shared clinical decision-making]
  REC -->|RECOMMENDS_PROCEDURE| ACT1
  ACT2[Procedure: shared decision-making information]
  REC -->|RECOMMENDS_PROCEDURE| ACT2
  subgraph LLM_or_1_OR
    D_or_1_1[DecisionNode or_1 s1]
    C_or_1_1[Procedure: percutaneous revascularization]
    D_or_1_1 -->|CHECKS_FOR| C_or_1_1
    D_or_1_2[DecisionNode or_1 s2]
    C_or_1_2[Procedure: surgical revascularization]
    D_or_1_2 -->|CHECKS_FOR| C_or_1_2
  end
  subgraph LLM_group_1_AND
    D_group_1_1[DecisionNode group_1 s1]
    C_group_1_1[Procedure: revascularization procedure]
    D_group_1_1 -->|CHECKS_FOR| C_group_1_1
    D_or_1_1 -->|LEADS_TO condition_met=true| D_group_1_1
    D_or_1_2 -->|LEADS_TO condition_met=true| D_group_1_1
  end
  D_group_1_1 -->|RESULTS_IN condition_met=true| REC
```

Grounding summary (optional):

```json
{
  "enabled": true,
  "total_grounded": 5,
  "target_label_counts": {
    "Procedure": 5
  },
  "root_hit_counts": {
    "71388002": 5
  },
  "root_hits": [
    {
      "entity": "percutaneous revascularization",
      "entity_original": "scheduled for percutaneous or surgical revascularization",
      "role": "Procedure",
      "name": "Heart revascularization (procedure)",
      "preferred_term": "Heart revascularization (procedure)",
      "synonyms": [
        "Heart revascularisation",
        "Heart revascularization"
      ],
      "alt_names": [
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
      "entity": "surgical revascularization",
      "entity_original": "scheduled for percutaneous or surgical revascularization",
      "role": "Procedure",
      "name": "Bronchial revascularization (procedure)",
      "preferred_term": "Bronchial revascularization (procedure)",
      "synonyms": [
        "Bronchial revascularization",
        "Bronchial revascularisation"
      ],
      "alt_names": [
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
    },
    {
      "entity": "shared clinical decision-making",
      "entity_original": "complete information about the benefits, risks, therapeutic consequences, and alternatives to revascularization",
      "role": "Procedure",
      "name": "Evaluation of decision-making capacity (procedure)",
      "preferred_term": "Evaluation of decision-making capacity (procedure)",
      "synonyms": [
        "Evaluation of decision-making capacity"
      ],
      "alt_names": [
        "Evaluation of decision-making capacity"
      ],
      "snomed_id": 12121000202107,
      "target_label": "Procedure",
      "taxonomy_path": [
        {
          "concept_id": "12121000202107",
          "term": "Evaluation of decision-making capacity (procedure)"
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
    },
    {
      "entity": "Revascularization procedure",
      "entity_original": "percutaneous or surgical revascularization",
      "role": "Procedure",
      "name": "Limb revascularization (procedure)",
      "preferred_term": "Limb revascularization (procedure)",
      "synonyms": [],
      "alt_names": [],
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
      "entity": "Shared decision-making information",
      "entity_original": "complete information about the benefits, risks, therapeutic consequences, and alternatives to revascularization",
      "role": "Procedure",
      "name": "Evaluation of decision-making capacity (procedure)",
      "preferred_term": "Evaluation of decision-making capacity (procedure)",
      "synonyms": [
        "Evaluation of decision-making capacity"
      ],
      "alt_names": [
        "Evaluation of decision-making capacity"
      ],
      "snomed_id": 12121000202107,
      "target_label": "Procedure",
      "taxonomy_path": [
        {
          "concept_id": "12121000202107",
          "term": "Evaluation of decision-making capacity (procedure)"
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
- expected: 7
- actual: 5
- matches: 2
- missing: 5
- extra: 3

Missing concepts:
- Procedure: benefits of revascularization
- Procedure: risks of revascularization
- Procedure: shared decision-making
- Procedure: therapeutic consequences of revascularization
- Procedure: treatment alternatives of revascularization

Extra concepts:
- Procedure: revascularization procedure
- Procedure: shared clinical decision-making
- Procedure: shared decision-making information

Rules (concept + logic fields):
- expected: 7
- actual: 5
- matches: 0
- missing: 7
- extra: 5

Missing rules:
- Procedure: benefits of revascularization | class=I | level=C | dir=POSITIVE
- Procedure: percutaneous revascularization | op=PRESENT | logic=OR | grp=or_1
- Procedure: risks of revascularization | class=I | level=C | dir=POSITIVE
- Procedure: shared decision-making | class=I | level=C | dir=POSITIVE
- Procedure: surgical revascularization | op=PRESENT | logic=OR | grp=or_1
- Procedure: therapeutic consequences of revascularization | class=I | level=C | dir=POSITIVE
- Procedure: treatment alternatives of revascularization | class=I | level=C | dir=POSITIVE

Extra rules:
- Procedure: percutaneous revascularization | op=PLANNED | ctx=scheduled | logic=OR | grp=or_1 | class=Unknown | level=Unknown | dir=UNKNOWN
- Procedure: revascularization procedure | op=PLANNED | ctx=scheduled | class=Unknown | level=Unknown | dir=UNKNOWN
- Procedure: shared clinical decision-making | class=I | level=C | dir=POSITIVE
- Procedure: shared decision-making information | class=I | level=C | dir=POSITIVE
- Procedure: surgical revascularization | op=PLANNED | ctx=scheduled | logic=OR | grp=or_1 | class=Unknown | level=Unknown | dir=UNKNOWN

