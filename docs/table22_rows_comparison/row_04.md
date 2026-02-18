# row_04 (mapped to row_04)

Original table row text (ground truth):

```json
{
  "Recommendations": "It is recommended that the decision for revascularization and its modality be patient-centred, considering patient preferences, health literacy, cultural circumstances, and social support. 849-851",
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
        "entity": "revacularization",
        "entity_original": "the decision for revascularization and its modality",
        "role": "Procedure",
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
        "entity": "patient-centred decision",
        "entity_original": "the decision for revascularization and its modality be patient-centred",
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
        "entity": "patient preferences",
        "entity_original": "the decision for revascularization and its modality consider patient preferences",
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
        "entity": "health literacy",
        "entity_original": "the decision for revascularization and its modality consider health literacy",
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
        "entity": "cultural circumstances",
        "entity_original": "the decision for revascularization and its modality consider cultural circumstances",
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
        "entity": "social support",
        "entity_original": "the decision for revascularization and its modality consider social support",
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
        "entity": "patient preference",
        "entity_original": "patient preferences",
        "role": "ClinicalParameter",
        "operator": "PRESENT",
        "threshold": null,
        "unit": null,
        "condition_context": null,
        "logic_type": null,
        "logic_group": null,
        "strength": "Unknown",
        "level": "Unknown",
        "direction": "UNKNOWN",
        "rule_id": 1,
        "side": "condition",
        "preferred_term": "Hand preference (observable entity)",
        "synonyms": [
          "Hand preference"
        ],
        "snomed_id": 246559009,
        "target_label": "ClinicalParameter",
        "taxonomy_path": [
          {
            "concept_id": "246559009",
            "term": "Hand preference (observable entity)"
          },
          {
            "concept_id": "363823006",
            "term": "Cerebral dominance observable (observable entity)"
          },
          {
            "concept_id": "363822001",
            "term": "Brain observable (observable entity)"
          },
          {
            "concept_id": "363821008",
            "term": "Central nervous system observable (observable entity)"
          },
          {
            "concept_id": "363820009",
            "term": "Neurological observable (observable entity)"
          },
          {
            "concept_id": "363788007",
            "term": "Clinical history/examination observable (observable entity)"
          },
          {
            "concept_id": "363787002",
            "term": "Observable entity (observable entity)"
          },
          {
            "concept_id": "138875005",
            "term": "SNOMED CT Concept (SNOMED RT+CTV3)"
          }
        ],
        "root_concept_id": "363787002",
        "root_concept_term": "Observable entity (observable entity)",
        "mapped_target_label": "ClinicalParameter"
      },
      {
        "entity": "health literacy",
        "entity_original": "health literacy",
        "role": "ClinicalParameter",
        "operator": "PRESENT",
        "threshold": null,
        "unit": null,
        "condition_context": null,
        "logic_type": null,
        "logic_group": null,
        "strength": "Unknown",
        "level": "Unknown",
        "direction": "UNKNOWN",
        "rule_id": 1,
        "side": "condition",
        "preferred_term": "Health literacy (observable entity)",
        "synonyms": [
          "Health literacy"
        ],
        "snomed_id": 870552008,
        "target_label": "ClinicalParameter",
        "taxonomy_path": [
          {
            "concept_id": "870552008",
            "term": "Health literacy (observable entity)"
          },
          {
            "concept_id": "246464006",
            "term": "Function (observable entity)"
          },
          {
            "concept_id": "363787002",
            "term": "Observable entity (observable entity)"
          },
          {
            "concept_id": "138875005",
            "term": "SNOMED CT Concept (SNOMED RT+CTV3)"
          }
        ],
        "root_concept_id": "363787002",
        "root_concept_term": "Observable entity (observable entity)",
        "mapped_target_label": "ClinicalParameter"
      },
      {
        "entity": "cultural circumstance",
        "entity_original": "cultural circumstances",
        "role": "ClinicalParameter",
        "operator": "PRESENT",
        "threshold": null,
        "unit": null,
        "condition_context": null,
        "logic_type": null,
        "logic_group": null,
        "strength": "Unknown",
        "level": "Unknown",
        "direction": "UNKNOWN",
        "rule_id": 1,
        "side": "condition",
        "preferred_term": "Cultural barrier status (observable entity)",
        "synonyms": [
          "Cultural barrier status"
        ],
        "snomed_id": 425271000,
        "target_label": "ClinicalParameter",
        "taxonomy_path": [
          {
            "concept_id": "425271000",
            "term": "Cultural barrier status (observable entity)"
          },
          {
            "concept_id": "363910003",
            "term": "Characteristic of psychosocial functioning (observable entity)"
          },
          {
            "concept_id": "3850002",
            "term": "Psychological function (observable entity)"
          },
          {
            "concept_id": "285231000",
            "term": "Mental function (observable entity)"
          },
          {
            "concept_id": "18373002",
            "term": "Nervous system function (observable entity)"
          },
          {
            "concept_id": "246464006",
            "term": "Function (observable entity)"
          },
          {
            "concept_id": "363787002",
            "term": "Observable entity (observable entity)"
          },
          {
            "concept_id": "138875005",
            "term": "SNOMED CT Concept (SNOMED RT+CTV3)"
          }
        ],
        "root_concept_id": "363787002",
        "root_concept_term": "Observable entity (observable entity)",
        "mapped_target_label": "ClinicalParameter"
      },
      {
        "entity": "social support",
        "entity_original": "social support",
        "role": "ClinicalParameter",
        "operator": "PRESENT",
        "threshold": null,
        "unit": null,
        "condition_context": null,
        "logic_type": null,
        "logic_group": null,
        "strength": "Unknown",
        "level": "Unknown",
        "direction": "UNKNOWN",
        "rule_id": 1,
        "side": "condition",
        "preferred_term": "Social support status (observable entity)",
        "synonyms": [
          "Social support status"
        ],
        "snomed_id": 405076007,
        "target_label": "ClinicalParameter",
        "taxonomy_path": [
          {
            "concept_id": "405076007",
            "term": "Social support status (observable entity)"
          },
          {
            "concept_id": "302160007",
            "term": "Household, family and support network detail (observable entity)"
          },
          {
            "concept_id": "160476009",
            "term": "Social / personal history observable (observable entity)"
          },
          {
            "concept_id": "363787002",
            "term": "Observable entity (observable entity)"
          },
          {
            "concept_id": "138875005",
            "term": "SNOMED CT Concept (SNOMED RT+CTV3)"
          }
        ],
        "root_concept_id": "363787002",
        "root_concept_term": "Observable entity (observable entity)",
        "mapped_target_label": "ClinicalParameter"
      },
      {
        "entity": "cultural circumstances",
        "entity_original": "cultural circumstances",
        "role": "ClinicalParameter",
        "operator": "PRESENT",
        "threshold": null,
        "unit": null,
        "condition_context": null,
        "logic_type": null,
        "logic_group": null,
        "strength": "Unknown",
        "level": "Unknown",
        "direction": "UNKNOWN",
        "rule_id": 1,
        "side": "condition",
        "preferred_term": "Financial circumstances (observable entity)",
        "synonyms": [
          "Economic circumstances",
          "Financial circumstances",
          "Financial status"
        ],
        "snomed_id": 224164009,
        "target_label": "ClinicalParameter",
        "taxonomy_path": [
          {
            "concept_id": "224164009",
            "term": "Financial circumstances (observable entity)"
          },
          {
            "concept_id": "302148006",
            "term": "Legal, financial, employment and socioeconomic history detail (observable entity)"
          },
          {
            "concept_id": "160476009",
            "term": "Social / personal history observable (observable entity)"
          },
          {
            "concept_id": "363787002",
            "term": "Observable entity (observable entity)"
          },
          {
            "concept_id": "138875005",
            "term": "SNOMED CT Concept (SNOMED RT+CTV3)"
          }
        ],
        "root_concept_id": "363787002",
        "root_concept_term": "Observable entity (observable entity)",
        "mapped_target_label": "ClinicalParameter"
      }
    ],
    "actions": [
      {
        "entity": "revascularization decision",
        "entity_original": "decision for revascularization and its modality",
        "role": "Procedure",
        "operator": null,
        "threshold": null,
        "unit": null,
        "condition_context": null,
        "logic_type": null,
        "logic_group": null,
        "strength": "I",
        "level": null,
        "direction": "POSITIVE",
        "rule_id": 1,
        "side": "action",
        "preferred_term": "Revascularization of toe (procedure)",
        "synonyms": [
          "Revascularisation of toe",
          "Revascularization of toe"
        ],
        "snomed_id": 233508000,
        "target_label": "Procedure",
        "taxonomy_path": [
          {
            "concept_id": "233508000",
            "term": "Revascularization of toe (procedure)"
          },
          {
            "concept_id": "233507005",
            "term": "Revascularization of foot (procedure)"
          },
          {
            "concept_id": "61661004",
            "term": "Operative procedure on foot (procedure)"
          },
          {
            "concept_id": "118716003",
            "term": "Procedure on foot (procedure)"
          },
          {
            "concept_id": "118710009",
            "term": "Procedure on lower extremity (procedure)"
          },
          {
            "concept_id": "118949002",
            "term": "Procedure on extremity (procedure)"
          },
          {
            "concept_id": "771329004",
            "term": "Procedure on body region (procedure)"
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
  ACT1[Procedure: patient-centred decision]
  REC -->|RECOMMENDS_PROCEDURE| ACT1
  ACT2[Procedure: patient preferences]
  REC -->|RECOMMENDS_PROCEDURE| ACT2
  ACT3[Procedure: health literacy]
  REC -->|RECOMMENDS_PROCEDURE| ACT3
  ACT4[Procedure: cultural circumstances]
  REC -->|RECOMMENDS_PROCEDURE| ACT4
  ACT5[Procedure: social support]
  REC -->|RECOMMENDS_PROCEDURE| ACT5
  subgraph Human_and_1_AND
    D_and_1_1[DecisionNode and_1 s1]
    C_and_1_1[Procedure: revacularization]
    D_and_1_1 -->|CHECKS_FOR| C_and_1_1
  end
  D_and_1_1 -->|RESULTS_IN condition_met=true| REC
```

Mermaid (LLM Generated):

```mermaid
graph LR
  REC[RecommendationNode]
  ACT1[Procedure: revascularization decision]
  REC -->|RECOMMENDS_PROCEDURE| ACT1
  subgraph LLM_group_1_AND
    D_group_1_1[DecisionNode group_1 s1]
    C_group_1_1[ClinicalParameter: cultural circumstance]
    D_group_1_1 -->|EVALUATES| C_group_1_1
    D_group_1_2[DecisionNode group_1 s2]
    C_group_1_2[ClinicalParameter: cultural circumstances]
    D_group_1_2 -->|EVALUATES| C_group_1_2
    D_group_1_3[DecisionNode group_1 s3]
    C_group_1_3[ClinicalParameter: health literacy]
    D_group_1_3 -->|EVALUATES| C_group_1_3
    D_group_1_4[DecisionNode group_1 s4]
    C_group_1_4[ClinicalParameter: patient preference]
    D_group_1_4 -->|EVALUATES| C_group_1_4
    D_group_1_5[DecisionNode group_1 s5]
    C_group_1_5[ClinicalParameter: social support]
    D_group_1_5 -->|EVALUATES| C_group_1_5
    D_group_1_1 -->|LEADS_TO condition_met=true| D_group_1_2
    D_group_1_2 -->|LEADS_TO condition_met=true| D_group_1_3
    D_group_1_3 -->|LEADS_TO condition_met=true| D_group_1_4
    D_group_1_4 -->|LEADS_TO condition_met=true| D_group_1_5
  end
  D_group_1_5 -->|RESULTS_IN condition_met=true| REC
```

Grounding summary (optional):

```json
{
  "enabled": true,
  "total_grounded": 6,
  "target_label_counts": {
    "ClinicalParameter": 5,
    "Procedure": 1
  },
  "root_hit_counts": {
    "363787002": 5,
    "71388002": 1
  },
  "root_hits": [
    {
      "entity": "Patient preference",
      "entity_original": "patient preferences",
      "role": "ClinicalParameter",
      "preferred_term": "Hand preference (observable entity)",
      "synonyms": [
        "Hand preference"
      ],
      "snomed_id": 246559009,
      "target_label": "ClinicalParameter",
      "taxonomy_path": [
        {
          "concept_id": "246559009",
          "term": "Hand preference (observable entity)"
        },
        {
          "concept_id": "363823006",
          "term": "Cerebral dominance observable (observable entity)"
        },
        {
          "concept_id": "363822001",
          "term": "Brain observable (observable entity)"
        },
        {
          "concept_id": "363821008",
          "term": "Central nervous system observable (observable entity)"
        },
        {
          "concept_id": "363820009",
          "term": "Neurological observable (observable entity)"
        },
        {
          "concept_id": "363788007",
          "term": "Clinical history/examination observable (observable entity)"
        },
        {
          "concept_id": "363787002",
          "term": "Observable entity (observable entity)"
        },
        {
          "concept_id": "138875005",
          "term": "SNOMED CT Concept (SNOMED RT+CTV3)"
        }
      ],
      "root_hit": {
        "root_concept_id": "363787002",
        "root_concept_term": "Observable entity (observable entity)",
        "mapped_target_label": "ClinicalParameter"
      }
    },
    {
      "entity": "Health literacy",
      "entity_original": "health literacy",
      "role": "ClinicalParameter",
      "preferred_term": "Health literacy (observable entity)",
      "synonyms": [
        "Health literacy"
      ],
      "snomed_id": 870552008,
      "target_label": "ClinicalParameter",
      "taxonomy_path": [
        {
          "concept_id": "870552008",
          "term": "Health literacy (observable entity)"
        },
        {
          "concept_id": "246464006",
          "term": "Function (observable entity)"
        },
        {
          "concept_id": "363787002",
          "term": "Observable entity (observable entity)"
        },
        {
          "concept_id": "138875005",
          "term": "SNOMED CT Concept (SNOMED RT+CTV3)"
        }
      ],
      "root_hit": {
        "root_concept_id": "363787002",
        "root_concept_term": "Observable entity (observable entity)",
        "mapped_target_label": "ClinicalParameter"
      }
    },
    {
      "entity": "Cultural circumstance",
      "entity_original": "cultural circumstances",
      "role": "ClinicalParameter",
      "preferred_term": "Cultural barrier status (observable entity)",
      "synonyms": [
        "Cultural barrier status"
      ],
      "snomed_id": 425271000,
      "target_label": "ClinicalParameter",
      "taxonomy_path": [
        {
          "concept_id": "425271000",
          "term": "Cultural barrier status (observable entity)"
        },
        {
          "concept_id": "363910003",
          "term": "Characteristic of psychosocial functioning (observable entity)"
        },
        {
          "concept_id": "3850002",
          "term": "Psychological function (observable entity)"
        },
        {
          "concept_id": "285231000",
          "term": "Mental function (observable entity)"
        },
        {
          "concept_id": "18373002",
          "term": "Nervous system function (observable entity)"
        },
        {
          "concept_id": "246464006",
          "term": "Function (observable entity)"
        },
        {
          "concept_id": "363787002",
          "term": "Observable entity (observable entity)"
        },
        {
          "concept_id": "138875005",
          "term": "SNOMED CT Concept (SNOMED RT+CTV3)"
        }
      ],
      "root_hit": {
        "root_concept_id": "363787002",
        "root_concept_term": "Observable entity (observable entity)",
        "mapped_target_label": "ClinicalParameter"
      }
    },
    {
      "entity": "Social support",
      "entity_original": "social support",
      "role": "ClinicalParameter",
      "preferred_term": "Social support status (observable entity)",
      "synonyms": [
        "Social support status"
      ],
      "snomed_id": 405076007,
      "target_label": "ClinicalParameter",
      "taxonomy_path": [
        {
          "concept_id": "405076007",
          "term": "Social support status (observable entity)"
        },
        {
          "concept_id": "302160007",
          "term": "Household, family and support network detail (observable entity)"
        },
        {
          "concept_id": "160476009",
          "term": "Social / personal history observable (observable entity)"
        },
        {
          "concept_id": "363787002",
          "term": "Observable entity (observable entity)"
        },
        {
          "concept_id": "138875005",
          "term": "SNOMED CT Concept (SNOMED RT+CTV3)"
        }
      ],
      "root_hit": {
        "root_concept_id": "363787002",
        "root_concept_term": "Observable entity (observable entity)",
        "mapped_target_label": "ClinicalParameter"
      }
    },
    {
      "entity": "Revascularization decision",
      "entity_original": "decision for revascularization and its modality",
      "role": "Procedure",
      "preferred_term": "Revascularization of toe (procedure)",
      "synonyms": [
        "Revascularisation of toe",
        "Revascularization of toe"
      ],
      "snomed_id": 233508000,
      "target_label": "Procedure",
      "taxonomy_path": [
        {
          "concept_id": "233508000",
          "term": "Revascularization of toe (procedure)"
        },
        {
          "concept_id": "233507005",
          "term": "Revascularization of foot (procedure)"
        },
        {
          "concept_id": "61661004",
          "term": "Operative procedure on foot (procedure)"
        },
        {
          "concept_id": "118716003",
          "term": "Procedure on foot (procedure)"
        },
        {
          "concept_id": "118710009",
          "term": "Procedure on lower extremity (procedure)"
        },
        {
          "concept_id": "118949002",
          "term": "Procedure on extremity (procedure)"
        },
        {
          "concept_id": "771329004",
          "term": "Procedure on body region (procedure)"
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
      "entity": "Cultural circumstances",
      "entity_original": "cultural circumstances",
      "role": "ClinicalParameter",
      "preferred_term": "Financial circumstances (observable entity)",
      "synonyms": [
        "Economic circumstances",
        "Financial circumstances",
        "Financial status"
      ],
      "snomed_id": 224164009,
      "target_label": "ClinicalParameter",
      "taxonomy_path": [
        {
          "concept_id": "224164009",
          "term": "Financial circumstances (observable entity)"
        },
        {
          "concept_id": "302148006",
          "term": "Legal, financial, employment and socioeconomic history detail (observable entity)"
        },
        {
          "concept_id": "160476009",
          "term": "Social / personal history observable (observable entity)"
        },
        {
          "concept_id": "363787002",
          "term": "Observable entity (observable entity)"
        },
        {
          "concept_id": "138875005",
          "term": "SNOMED CT Concept (SNOMED RT+CTV3)"
        }
      ],
      "root_hit": {
        "root_concept_id": "363787002",
        "root_concept_term": "Observable entity (observable entity)",
        "mapped_target_label": "ClinicalParameter"
      }
    }
  ]
}
```

Concepts:
- expected: 6
- actual: 6
- matches: 0
- missing: 6
- extra: 6

Missing concepts:
- Procedure: cultural circumstances
- Procedure: health literacy
- Procedure: patient preferences
- Procedure: patient-centred decision
- Procedure: revacularization
- Procedure: social support

Extra concepts:
- ClinicalParameter: cultural circumstance
- ClinicalParameter: cultural circumstances
- ClinicalParameter: health literacy
- ClinicalParameter: patient preference
- ClinicalParameter: social support
- Procedure: revascularization decision

Rules (concept + logic fields):
- expected: 6
- actual: 6
- matches: 0
- missing: 6
- extra: 6

Missing rules:
- Procedure: cultural circumstances | class=I | level=C | dir=POSITIVE
- Procedure: health literacy | class=I | level=C | dir=POSITIVE
- Procedure: patient preferences | class=I | level=C | dir=POSITIVE
- Procedure: patient-centred decision | class=I | level=C | dir=POSITIVE
- Procedure: revacularization | op=PRESENT | logic=AND | grp=and_1
- Procedure: social support | class=I | level=C | dir=POSITIVE

Extra rules:
- ClinicalParameter: cultural circumstance | op=PRESENT | class=Unknown | level=Unknown | dir=UNKNOWN
- ClinicalParameter: cultural circumstances | op=PRESENT | class=Unknown | level=Unknown | dir=UNKNOWN
- ClinicalParameter: health literacy | op=PRESENT | class=Unknown | level=Unknown | dir=UNKNOWN
- ClinicalParameter: patient preference | op=PRESENT | class=Unknown | level=Unknown | dir=UNKNOWN
- ClinicalParameter: social support | op=PRESENT | class=Unknown | level=Unknown | dir=UNKNOWN
- Procedure: revascularization decision | class=I | dir=POSITIVE

