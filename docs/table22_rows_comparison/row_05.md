# row_05 (mapped to row_06)

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
        "entity": "specialist multidisciplinary team",
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
        "direction": null,
        "preferred_term": null,
        "synonyms": [],
        "snomed_id": "408458006",
        "target_label": null,
        "taxonomy_path": [],
        "root_concept_id": null,
        "root_concept_term": null
      }
    ],
    "actions": [
      {
        "entity": "development of care plan",
        "entity_original": "develop institutional protocols",
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
        "snomed_id": "399684003",
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
      "conditions": [
        {
          "entity": "heart team",
          "entity_original": "heart team (on site or with a partner institution)",
          "role": "Condition",
          "operator": "PRESENT",
          "threshold": null,
          "unit": null,
          "context": null,
          "logic_type": "AND",
          "logic_group": "and_1",
          "strength": "Class I",
          "level": "C",
          "direction": "POSITIVE",
          "preferred_term": null,
          "synonyms": [],
          "snomed_id": 368009,
          "target_label": "ClinicalCondition",
          "taxonomy_path": [],
          "root_concept_id": null,
          "root_concept_term": null,
          "mapped_target_label": null
        }
      ],
      "actions": [
        {
          "entity": "revascularization protocol development",
          "entity_original": "develop institutional protocols to implement the appropriate revascularization strategy in accordance with current guidelines",
          "role": "Procedure",
          "operator": null,
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
          "root_concept_term": null,
          "mapped_target_label": null
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
  ACT1[Procedure: development of care plan]
  REC -->|RECOMMENDS_PROCEDURE| ACT1
  subgraph Human_and_1_AND
    D_and_1_1[DecisionNode and_1 s1]
    C_and_1_1[ClinicalCondition: specialist multidisciplinary team]
    D_and_1_1 -->|CHECKS_FOR| C_and_1_1
  end
  D_and_1_1 -->|RESULTS_IN condition_met=true| REC
```

Mermaid (LLM Generated):

```mermaid
graph LR
  REC[RecommendationNode]
  ACT1[Procedure: revascularization protocol development]
  REC -->|RECOMMENDS_PROCEDURE| ACT1
  subgraph LLM_and_1_AND
    D_and_1_1[DecisionNode and_1 s1]
    C_and_1_1[Condition: heart team]
    D_and_1_1 -->|CHECKS_FOR| C_and_1_1
  end
  D_and_1_1 -->|RESULTS_IN condition_met=true| REC
```

Concepts:
- expected: 2
- actual: 2
- matches: 0
- missing: 2
- extra: 2

Missing concepts:
- ClinicalCondition: specialist multidisciplinary team
- Procedure: development of care plan

Extra concepts:
- Condition: heart team
- Procedure: revascularization protocol development

Rules (concept + logic fields):
- expected: 2
- actual: 2
- matches: 0
- missing: 2
- extra: 2

Missing rules:
- ClinicalCondition: specialist multidisciplinary team | op=PRESENT | logic=AND | grp=and_1
- Procedure: development of care plan | class=I | level=C | dir=POSITIVE

Extra rules:
- Condition: heart team | op=PRESENT | logic=AND | grp=and_1 | class=Class I | level=C | dir=POSITIVE
- Procedure: revascularization protocol development | class=Class I | level=C | dir=POSITIVE

