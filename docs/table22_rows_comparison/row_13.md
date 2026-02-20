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
    "conditions": [
      {
        "entity": "coronary artery disease",
        "entity_original": "patients with complex cad",
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
        "preferred_term": null,
        "synonyms": [],
        "snomed_id": "53741008",
        "target_label": null,
        "taxonomy_path": [],
        "root_concept_id": null,
        "root_concept_term": null
      },
      {
        "entity": "myocardial revascularization",
        "entity_original": "patients in whom revascularization is being considered",
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
        "preferred_term": null,
        "synonyms": [],
        "snomed_id": "275227003",
        "target_label": null,
        "taxonomy_path": [],
        "root_concept_id": null,
        "root_concept_term": null
      }
    ],
    "actions": [
      {
        "entity": "therapeutic evaluation (procedure)",
        "entity_original": "assess procedural risks",
        "role": "Procedure",
        "operator": null,
        "threshold": null,
        "unit": null,
        "context": null,
        "logic_type": null,
        "logic_group": null,
        "strength": "I",
        "level": "C",
        "direction": "POSITIVE",
        "preferred_term": null,
        "synonyms": [],
        "snomed_id": "110463001",
        "target_label": null,
        "taxonomy_path": [],
        "root_concept_id": null,
        "root_concept_term": null
      },
      {
        "entity": "therapeutic evaluation (procedure)",
        "entity_original": "assess post-procedural outcomes",
        "role": "Procedure",
        "operator": null,
        "threshold": null,
        "unit": null,
        "context": null,
        "logic_type": null,
        "logic_group": null,
        "strength": "I",
        "level": "C",
        "direction": "POSITIVE",
        "preferred_term": null,
        "synonyms": [],
        "snomed_id": "110463001",
        "target_label": null,
        "taxonomy_path": [],
        "root_concept_id": null,
        "root_concept_term": null
      },
      {
        "entity": "using decision making strategies",
        "entity_original": "take part in shared clinical decision-making",
        "role": "Procedure",
        "operator": null,
        "threshold": null,
        "unit": null,
        "context": null,
        "logic_type": null,
        "logic_group": null,
        "strength": "I",
        "level": "C",
        "direction": "POSITIVE",
        "preferred_term": null,
        "synonyms": [],
        "snomed_id": "415806002",
        "target_label": null,
        "taxonomy_path": [],
        "root_concept_id": null,
        "root_concept_term": null
      }
    ]
  }
]
</pre></td>
    <td valign="top"><pre>
{
  "rules": [
    {
      "conditions": [],
      "actions": [
        {
          "entity": "revascularization procedure",
          "entity_original": "revascularization is being considered",
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
  ACT1[Procedure: therapeutic evaluation (procedure)]
  REC -->|RECOMMENDS_PROCEDURE| ACT1
  ACT2[Procedure: therapeutic evaluation (procedure)]
  REC -->|RECOMMENDS_PROCEDURE| ACT2
  ACT3[Procedure: using decision making strategies]
  REC -->|RECOMMENDS_PROCEDURE| ACT3
  subgraph Human_and_1_AND
    D_and_1_1[DecisionNode and_1 s1]
    C_and_1_1[ClinicalCondition: coronary artery disease]
    D_and_1_1 -->|CHECKS_FOR| C_and_1_1
    D_and_1_2[DecisionNode and_1 s2]
    C_and_1_2[ClinicalCondition: myocardial revascularization]
    D_and_1_2 -->|CHECKS_FOR| C_and_1_2
    D_and_1_1 -->|LEADS_TO condition_met=true| D_and_1_2
  end
  D_and_1_2 -->|RESULTS_IN condition_met=true| REC
```

Mermaid (LLM Generated):

```mermaid
graph LR
  REC[RecommendationNode]
  ACT1[Procedure: revascularization procedure]
  REC -->|RECOMMENDS_PROCEDURE| ACT1
```

Grounding summary (optional):

```json
{
  "enabled": true,
  "total_grounded": 1,
  "target_label_counts": {
    "Procedure": 1
  },
  "root_hit_counts": {
    "71388002": 1
  },
  "root_hits": [
    {
      "entity": "Revascularization procedure",
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
    }
  ]
}
```

Concepts:
- expected: 4
- actual: 4
- matches: 0
- missing: 4
- extra: 4

Missing concepts:
- ClinicalCondition: coronary artery disease
- ClinicalCondition: myocardial revascularization
- Procedure: therapeutic evaluation (procedure)
- Procedure: using decision making strategies

Extra concepts:
- ClinicalParameter: complex coronary artery disease
- ClinicalParameter: coronary artery disease, complex
- Procedure: assessment of procedural risks and post-procedural outcomes
- Procedure: revascularization procedure

Rules (concept + logic fields):
- expected: 4
- actual: 4
- matches: 0
- missing: 4
- extra: 4

Missing rules:
- ClinicalCondition: coronary artery disease | op=PRESENT | logic=AND | grp=and_1
- ClinicalCondition: myocardial revascularization | op=PRESENT | logic=AND | grp=and_1
- Procedure: therapeutic evaluation (procedure) | class=I | level=C | dir=POSITIVE
- Procedure: using decision making strategies | class=I | level=C | dir=POSITIVE

Extra rules:
- ClinicalParameter: complex coronary artery disease | op=PRESENT | class=Class I | level=C | dir=POSITIVE
- ClinicalParameter: coronary artery disease, complex | op=PRESENT | class=Class I | level=C | dir=POSITIVE
- Procedure: assessment of procedural risks and post-procedural outcomes | class=Class I | level=C | dir=POSITIVE
- Procedure: revascularization procedure | op=PLANNED | class=Class I | level=C | dir=POSITIVE

