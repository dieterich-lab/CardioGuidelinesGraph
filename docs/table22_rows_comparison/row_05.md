# row_05 (mapped to row_05)

Original table row text (ground truth):

```json
{
  "Recommendations": "It is recommended that the Heart Team (on site or with a partner institution) develop institutional protocols to implement the appropriate revascularization strategy in accordance with current guidelines. 855,856,858",
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
        "entity": "heart team",
        "entity_original": "the heart team",
        "role": "ClinicalCondition",
        "operator": "PRESENT",
        "threshold": null,
        "unit": null,
        "context": null,
        "logic_type": "AND",
        "logic_group": "and_1",
        "strength": null,
        "level": null,
        "direction": null
      }
    ],
    "actions": [
      {
        "entity": "protocols for revascularization",
        "entity_original": "develop institutional protocols to implement the appropriate revascularization strategy in accordance with current guidelines",
        "role": "string",
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
          "entity": "heart team",
          "entity_original": "heart team (on site or with a partner institution)",
          "role": "Procedure",
          "operator": "PRESENT",
          "threshold": null,
          "unit": null,
          "context": null,
          "logic_type": null,
          "logic_group": null,
          "strength": "Unknown",
          "level": "Unknown",
          "direction": null,
          "preferred_term": "Open heart surgery (procedure)",
          "synonyms": [
            "Open heart surgery"
          ],
          "snomed_id": 2598006,
          "target_label": "Procedure",
          "taxonomy_path": [
            {
              "concept_id": "2598006",
              "term": "Open heart surgery (procedure)"
            },
            {
              "concept_id": "64915003",
              "term": "Operation on heart (procedure)"
            },
            {
              "concept_id": "386765006",
              "term": "Operation on mediastinum (procedure)"
            },
            {
              "concept_id": "118696008",
              "term": "Procedure on mediastinum (procedure)"
            },
            {
              "concept_id": "118695007",
              "term": "Procedure on thorax (procedure)"
            },
            {
              "concept_id": "118694006",
              "term": "Procedure on trunk (procedure)"
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
          "root_concept_term": "Procedure (procedure)"
        }
      ],
      "actions": [
        {
          "entity": "heart team on site or with partner institution",
          "entity_original": "heart team (on site or with a partner institution)",
          "role": "Procedure",
          "operator": "PLANNED",
          "threshold": null,
          "unit": null,
          "context": null,
          "logic_type": null,
          "logic_group": null,
          "strength": "Class I",
          "level": "C",
          "direction": "POSITIVE",
          "preferred_term": null,
          "synonyms": [],
          "snomed_id": null,
          "target_label": "Procedure",
          "taxonomy_path": [],
          "root_concept_id": null,
          "root_concept_term": null
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
  subgraph Human_and_1_AND
    D_and_1_1[DecisionNode and_1 s1]
    C_and_1_1[ClinicalCondition: heart team]
    D_and_1_1 -->|CHECKS_FOR| C_and_1_1
  end
  D_and_1_1 -->|RESULTS_IN condition_met=true| REC
```

Mermaid (LLM Generated):

```mermaid
graph LR
  REC[RecommendationNode]
  ACT1[Procedure: develop institutional protocols for revascularization strategy]
  REC -->|RECOMMENDS_PROCEDURE| ACT1
  ACT2[Procedure: heart team]
  REC -->|RECOMMENDS_PROCEDURE| ACT2
  ACT3[Procedure: heart team on site or with partner institution]
  REC -->|RECOMMENDS_PROCEDURE| ACT3
```

Grounding summary (optional):

```json
{
  "enabled": true,
  "total_grounded": 2,
  "target_label_counts": {
    "Procedure": 2
  },
  "root_hit_counts": {
    "71388002": 1
  },
  "root_hits": [
    {
      "entity": "Heart Team on site or with partner institution",
      "entity_original": "Heart Team (on site or with a partner institution)",
      "role": "Procedure",
      "preferred_term": null,
      "synonyms": [],
      "snomed_id": null,
      "target_label": "Procedure",
      "taxonomy_path": [],
      "root_hit": null
    },
    {
      "entity": "Heart Team",
      "entity_original": "Heart Team (on site or with a partner institution)",
      "role": "Procedure",
      "preferred_term": "Open heart surgery (procedure)",
      "synonyms": [
        "Open heart surgery"
      ],
      "snomed_id": 2598006,
      "target_label": "Procedure",
      "taxonomy_path": [
        {
          "concept_id": "2598006",
          "term": "Open heart surgery (procedure)"
        },
        {
          "concept_id": "64915003",
          "term": "Operation on heart (procedure)"
        },
        {
          "concept_id": "386765006",
          "term": "Operation on mediastinum (procedure)"
        },
        {
          "concept_id": "118696008",
          "term": "Procedure on mediastinum (procedure)"
        },
        {
          "concept_id": "118695007",
          "term": "Procedure on thorax (procedure)"
        },
        {
          "concept_id": "118694006",
          "term": "Procedure on trunk (procedure)"
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
    }
  ]
}
```

Concepts:
- expected: 2
- actual: 3
- matches: 0
- missing: 2
- extra: 3

Missing concepts:
- ClinicalCondition: heart team
- string: protocols for revascularization

Extra concepts:
- Procedure: develop institutional protocols for revascularization strategy
- Procedure: heart team
- Procedure: heart team on site or with partner institution

Rules (concept + logic fields):
- expected: 2
- actual: 3
- matches: 0
- missing: 2
- extra: 3

Missing rules:
- ClinicalCondition: heart team | op=PRESENT | logic=AND | grp=and_1
- string: protocols for revascularization | class=I | level=C | dir=POSITIVE

Extra rules:
- Procedure: develop institutional protocols for revascularization strategy | class=Class I | level=C | dir=POSITIVE
- Procedure: heart team on site or with partner institution | op=PLANNED | class=Class I | level=C | dir=POSITIVE
- Procedure: heart team | op=PRESENT | class=Unknown | level=Unknown

