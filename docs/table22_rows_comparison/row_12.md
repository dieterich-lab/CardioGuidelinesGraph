# row_12 (mapped to row_12)

Original table row text (ground truth):

```json
{
  "Recommendations": "In CCS patients with persistent angina or anginal equivalent, despite guideline-directed medical treatment, myocardial revascularization of functionally significant obstructive CAD is recommended to improve symptoms. 50,321,402,732,734,757",
  "Class a": "I",
  "Level b": "A"
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
        "entity": "ccs",
        "entity_original": "ccs patient",
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
        "entity": "persistent angina",
        "entity_original": "persistent angina",
        "role": "Condition",
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
        "entity": "anginal equivalent",
        "entity_original": "anginal equivalent",
        "role": "Condition",
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
        "entity": "despite guideline-directed medical treatment",
        "entity_original": "despite guideline-directed medical treatment",
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
        "entity": "myocardial revascularization",
        "entity_original": "myocardial revascularization of functionally significant obstructive cad is recommended to improve symptoms",
        "role": "Procedure",
        "operator": null,
        "threshold": null,
        "unit": null,
        "condition_context": null,
        "logic_type": null,
        "logic_group": null,
        "strength": "I",
        "level": "A",
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
        "entity": "angina pectoris",
        "entity_original": "persistent angina or anginal equivalent",
        "role": "Condition",
        "operator": "PRESENT",
        "threshold": null,
        "unit": null,
        "condition_context": "persistent",
        "logic_type": null,
        "logic_group": null,
        "strength": "I",
        "level": "A",
        "direction": "POSITIVE",
        "rule_id": 1,
        "side": "condition",
        "preferred_term": "Angina pectoris (disorder)",
        "synonyms": [],
        "snomed_id": 17828002,
        "target_label": "ClinicalCondition",
        "taxonomy_path": [
          {
            "concept_id": "17828002",
            "term": "Angina pectoris (disorder)"
          }
        ],
        "root_concept_id": null,
        "root_concept_term": null,
        "mapped_target_label": null
      },
      {
        "entity": "angina pectoris",
        "entity_original": "persistent angina or anginal equivalent",
        "role": "ClinicalParameter",
        "operator": "PRESENT",
        "threshold": null,
        "unit": null,
        "condition_context": "persistent",
        "logic_type": null,
        "logic_group": null,
        "strength": "I",
        "level": "A",
        "direction": "UNKNOWN",
        "rule_id": 1,
        "side": "condition",
        "preferred_term": "Angina pectoris (disorder)",
        "synonyms": [],
        "snomed_id": 17828002,
        "target_label": "ClinicalCondition",
        "taxonomy_path": [
          {
            "concept_id": "17828002",
            "term": "Angina pectoris (disorder)"
          }
        ],
        "root_concept_id": null,
        "root_concept_term": null,
        "mapped_target_label": null
      }
    ],
    "actions": [
      {
        "entity": "myocardial revascularization",
        "entity_original": "myocardial revascularization of functionally significant obstructive cad",
        "role": "Procedure",
        "operator": "PRESENT",
        "threshold": null,
        "unit": null,
        "condition_context": null,
        "logic_type": null,
        "logic_group": null,
        "strength": "I",
        "level": "A",
        "direction": "POSITIVE",
        "rule_id": 1,
        "side": "action",
        "preferred_term": "Myocardial revascularization (procedure)",
        "synonyms": [],
        "snomed_id": 275227003,
        "target_label": "Procedure",
        "taxonomy_path": [
          {
            "concept_id": "275227003",
            "term": "Myocardial revascularization (procedure)"
          },
          {
            "concept_id": "81266008",
            "term": "Heart revascularization (procedure)"
          },
          {
            "concept_id": "31413008",
            "term": "Operative procedure on coronary artery (procedure)"
          },
          {
            "concept_id": "38629001",
            "term": "Operative procedure on the arteries of the thorax and abdomen (procedure)"
          },
          {
            "concept_id": "74943008",
            "term": "Operation on trunk (procedure)"
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
  ACT1[Procedure: myocardial revascularization]
  REC -->|RECOMMENDS_PROCEDURE| ACT1
  subgraph Human_and_1_AND
    D_and_1_1[DecisionNode and_1 s1]
    C_and_1_1[Condition: ccs]
    D_and_1_1 -->|CHECKS_FOR| C_and_1_1
    D_and_1_2[DecisionNode and_1 s2]
    C_and_1_2[Condition: despite guideline-directed medical treatment]
    D_and_1_2 -->|CHECKS_FOR| C_and_1_2
    D_and_1_1 -->|LEADS_TO condition_met=true| D_and_1_2
  end
  subgraph Human_or_1_OR
    D_or_1_1[DecisionNode or_1 s1]
    C_or_1_1[Condition: persistent angina]
    D_or_1_1 -->|CHECKS_FOR| C_or_1_1
    D_or_1_2[DecisionNode or_1 s2]
    C_or_1_2[Condition: anginal equivalent]
    D_or_1_2 -->|CHECKS_FOR| C_or_1_2
    D_and_1_2 -->|LEADS_TO condition_met=true| D_or_1_1
    D_and_1_2 -->|LEADS_TO condition_met=true| D_or_1_2
  end
  D_or_1_1 -->|RESULTS_IN condition_met=true| REC
  D_or_1_2 -->|RESULTS_IN condition_met=true| REC
```

Mermaid (LLM Generated):

```mermaid
graph LR
  REC[RecommendationNode]
  ACT1[Procedure: myocardial revascularization]
  REC -->|RECOMMENDS_PROCEDURE| ACT1
  subgraph LLM_group_1_AND
    D_group_1_1[DecisionNode group_1 s1]
    C_group_1_1[ClinicalParameter: angina pectoris]
    D_group_1_1 -->|EVALUATES| C_group_1_1
    D_group_1_2[DecisionNode group_1 s2]
    C_group_1_2[Condition: angina pectoris]
    D_group_1_2 -->|CHECKS_FOR| C_group_1_2
    D_group_1_3[DecisionNode group_1 s3]
    C_group_1_3[ClinicalParameter: chronic coronary syndrome]
    D_group_1_3 -->|EVALUATES| C_group_1_3
    D_group_1_4[DecisionNode group_1 s4]
    C_group_1_4[ClinicalParameter: guideline-directed medical therapy]
    D_group_1_4 -->|EVALUATES| C_group_1_4
    D_group_1_5[DecisionNode group_1 s5]
    C_group_1_5[ClinicalParameter: guideline-directed medical treatment]
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
  "total_grounded": 3,
  "target_label_counts": {
    "ClinicalCondition": 2,
    "Procedure": 1
  },
  "root_hit_counts": {
    "71388002": 1
  },
  "root_hits": [
    {
      "entity": "Angina Pectoris",
      "entity_original": "persistent angina or anginal equivalent",
      "role": "Condition",
      "preferred_term": "Angina pectoris (disorder)",
      "synonyms": [],
      "snomed_id": 17828002,
      "target_label": "ClinicalCondition",
      "taxonomy_path": [
        {
          "concept_id": "17828002",
          "term": "Angina pectoris (disorder)"
        }
      ],
      "root_hit": null
    },
    {
      "entity": "Myocardial Revascularization",
      "entity_original": "myocardial revascularization of functionally significant obstructive CAD",
      "role": "Procedure",
      "preferred_term": "Myocardial revascularization (procedure)",
      "synonyms": [],
      "snomed_id": 275227003,
      "target_label": "Procedure",
      "taxonomy_path": [
        {
          "concept_id": "275227003",
          "term": "Myocardial revascularization (procedure)"
        },
        {
          "concept_id": "81266008",
          "term": "Heart revascularization (procedure)"
        },
        {
          "concept_id": "31413008",
          "term": "Operative procedure on coronary artery (procedure)"
        },
        {
          "concept_id": "38629001",
          "term": "Operative procedure on the arteries of the thorax and abdomen (procedure)"
        },
        {
          "concept_id": "74943008",
          "term": "Operation on trunk (procedure)"
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
      "entity": "Angina pectoris",
      "entity_original": "persistent angina or anginal equivalent",
      "role": "ClinicalParameter",
      "preferred_term": "Angina pectoris (disorder)",
      "synonyms": [],
      "snomed_id": 17828002,
      "target_label": "ClinicalCondition",
      "taxonomy_path": [
        {
          "concept_id": "17828002",
          "term": "Angina pectoris (disorder)"
        }
      ],
      "root_hit": null
    }
  ]
}
```

Concepts:
- expected: 5
- actual: 6
- matches: 1
- missing: 4
- extra: 5

Missing concepts:
- Condition: anginal equivalent
- Condition: ccs
- Condition: despite guideline-directed medical treatment
- Condition: persistent angina

Extra concepts:
- ClinicalParameter: angina pectoris
- ClinicalParameter: chronic coronary syndrome
- ClinicalParameter: guideline-directed medical therapy
- ClinicalParameter: guideline-directed medical treatment
- Condition: angina pectoris

Rules (concept + logic fields):
- expected: 5
- actual: 6
- matches: 0
- missing: 5
- extra: 6

Missing rules:
- Condition: anginal equivalent | op=PRESENT | logic=OR | grp=or_1
- Condition: ccs | op=PRESENT | logic=AND | grp=and_1
- Condition: despite guideline-directed medical treatment | op=PRESENT | logic=AND | grp=and_1
- Condition: persistent angina | op=PRESENT | logic=OR | grp=or_1
- Procedure: myocardial revascularization | class=I | level=A | dir=POSITIVE

Extra rules:
- ClinicalParameter: angina pectoris | op=PRESENT | ctx=persistent | class=I | level=A | dir=UNKNOWN
- ClinicalParameter: chronic coronary syndrome | op=PRESENT | class=I | level=A | dir=POSITIVE
- ClinicalParameter: guideline-directed medical therapy | op=PRESENT | class=I | level=A | dir=UNKNOWN
- ClinicalParameter: guideline-directed medical treatment | op=PRESENT | class=I | level=A | dir=POSITIVE
- Condition: angina pectoris | op=PRESENT | ctx=persistent | class=I | level=A | dir=POSITIVE
- Procedure: myocardial revascularization | op=PRESENT | class=I | level=A | dir=POSITIVE

