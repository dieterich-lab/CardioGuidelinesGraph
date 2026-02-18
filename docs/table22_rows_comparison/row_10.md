# row_10 (mapped to row_10)

Original table row text (ground truth):

```json
{
  "Recommendations": "In surgically eligible CCS patients with multivessel CAD and LVEF \u2264 35%, myocardial revascularization with CABG is recommended over medical therapy alone to improve long-term survival. 53,54,749,861",
  "Class a": "I",
  "Level b": "B"
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
        "entity": "surgically eligible",
        "entity_original": "surgically eligible patient",
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
        "entity": "multivessel cad",
        "entity_original": "multivessel cad",
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
        "entity": "lvef",
        "entity_original": "lvef \u2264 35%",
        "role": "ClinicalParameter",
        "operator": "\u2264",
        "threshold": "35",
        "unit": "%",
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
        "entity": "cabg",
        "entity_original": "myocardial revascularization with cabg over medical therapy alone to improve long-term survival",
        "role": "Procedure",
        "operator": null,
        "threshold": null,
        "unit": null,
        "condition_context": null,
        "logic_type": null,
        "logic_group": null,
        "strength": "I",
        "level": "B",
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
        "entity": "surgically eligible ccs patients",
        "entity_original": "surgically eligible ccs patients",
        "role": "Condition",
        "operator": "PRESENT",
        "threshold": null,
        "unit": null,
        "condition_context": null,
        "logic_type": null,
        "logic_group": null,
        "strength": null,
        "level": null,
        "direction": "UNKNOWN",
        "rule_id": 1,
        "side": "condition",
        "preferred_term": null,
        "synonyms": [],
        "snomed_id": null,
        "target_label": "ClinicalCondition",
        "taxonomy_path": [],
        "root_concept_id": null,
        "root_concept_term": null,
        "mapped_target_label": null
      },
      {
        "entity": "multivessel cad",
        "entity_original": "multivessel cad",
        "role": "ClinicalParameter",
        "operator": "PRESENT",
        "threshold": null,
        "unit": null,
        "condition_context": null,
        "logic_type": null,
        "logic_group": null,
        "strength": null,
        "level": null,
        "direction": "UNKNOWN",
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
      },
      {
        "entity": "lvef \u2264 35%",
        "entity_original": "lvef \u2264 35%",
        "role": "ClinicalParameter",
        "operator": "\u2264",
        "threshold": "35",
        "unit": "%",
        "condition_context": null,
        "logic_type": null,
        "logic_group": null,
        "strength": null,
        "level": null,
        "direction": "UNKNOWN",
        "rule_id": 1,
        "side": "condition",
        "preferred_term": "Left ventricular ejection fraction (observable entity)",
        "synonyms": [
          "Left ventricular ejection fraction",
          "LVEF - Left ventricular ejection fraction"
        ],
        "snomed_id": 250908004,
        "target_label": "ClinicalParameter",
        "taxonomy_path": [
          {
            "concept_id": "250908004",
            "term": "Left ventricular ejection fraction (observable entity)"
          },
          {
            "concept_id": "250907009",
            "term": "Left ventricular function (observable entity)"
          },
          {
            "concept_id": "86185002",
            "term": "Cardiac function (observable entity)"
          },
          {
            "concept_id": "70337006",
            "term": "Cardiovascular function (observable entity)"
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
        "entity": "surgically eligible patient with coronary circulation syndrome",
        "entity_original": "surgically eligible ccs patients",
        "role": "ClinicalParameter",
        "operator": "PRESENT",
        "threshold": null,
        "unit": null,
        "condition_context": "surgically eligible",
        "logic_type": null,
        "logic_group": null,
        "strength": "I",
        "level": "B",
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
      },
      {
        "entity": "multivessel coronary artery disease",
        "entity_original": "multivessel cad",
        "role": "ClinicalParameter",
        "operator": "PRESENT",
        "threshold": null,
        "unit": null,
        "condition_context": "multivessel",
        "logic_type": null,
        "logic_group": null,
        "strength": "I",
        "level": "B",
        "direction": "POSITIVE",
        "rule_id": 1,
        "side": "condition",
        "preferred_term": "Coronary artery disease (disorder)",
        "synonyms": [],
        "snomed_id": 8957000,
        "target_label": "ClinicalCondition",
        "taxonomy_path": [
          {
            "concept_id": "8957000",
            "term": "Coronary artery disease (disorder)"
          }
        ],
        "root_concept_id": null,
        "root_concept_term": null,
        "mapped_target_label": null
      },
      {
        "entity": "left ventricular ejection fraction",
        "entity_original": "lvef \u2264 35%",
        "role": "ClinicalParameter",
        "operator": "LE",
        "threshold": "35",
        "unit": "%",
        "condition_context": "left ventricular ejection fraction",
        "logic_type": null,
        "logic_group": null,
        "strength": "I",
        "level": "B",
        "direction": "POSITIVE",
        "rule_id": 1,
        "side": "condition",
        "preferred_term": "Left ventricular ejection fraction (observable entity)",
        "synonyms": [],
        "snomed_id": 250908004,
        "target_label": "ClinicalParameter",
        "taxonomy_path": [
          {
            "concept_id": "250908004",
            "term": "Left ventricular ejection fraction (observable entity)"
          },
          {
            "concept_id": "70822001",
            "term": "Cardiac ejection fraction, function (observable entity)"
          },
          {
            "concept_id": "86185002",
            "term": "Cardiac function (observable entity)"
          },
          {
            "concept_id": "70337006",
            "term": "Cardiovascular function (observable entity)"
          },
          {
            "concept_id": "246464006",
            "term": "Function (observable entity)"
          },
          {
            "concept_id": "363787002",
            "term": "Observable entity (observable entity)"
          }
        ],
        "root_concept_id": "363787002",
        "root_concept_term": "Observable entity (observable entity)",
        "mapped_target_label": "ClinicalParameter"
      }
    ],
    "actions": [
      {
        "entity": "myocardial revascularization with cabg",
        "entity_original": "myocardial revascularization with cabg",
        "role": "Procedure",
        "operator": null,
        "threshold": null,
        "unit": null,
        "condition_context": null,
        "logic_type": null,
        "logic_group": null,
        "strength": "I",
        "level": "B",
        "direction": "POSITIVE",
        "rule_id": 1,
        "side": "action",
        "preferred_term": "Coronary artery bypass grafting (procedure)",
        "synonyms": [
          "Coronary artery bypass graft",
          "CABG - Coronary artery bypass graft",
          "CBG - Coronary bypass graft",
          "Coronary artery bypass grafting",
          "Coronary artery bypass graft operations",
          "CAG - Coronary artery graft"
        ],
        "snomed_id": 232717009,
        "target_label": "Procedure",
        "taxonomy_path": [
          {
            "concept_id": "232717009",
            "term": "Coronary artery bypass grafting (procedure)"
          },
          {
            "concept_id": "116360008",
            "term": "Arterial bypass graft (procedure)"
          },
          {
            "concept_id": "23075000",
            "term": "Creation of vascular bypass (procedure)"
          },
          {
            "concept_id": "48537004",
            "term": "Bypass graft (procedure)"
          },
          {
            "concept_id": "78817002",
            "term": "Construction of anastomosis (procedure)"
          },
          {
            "concept_id": "410614008",
            "term": "Construction (procedure)"
          },
          {
            "concept_id": "4365001",
            "term": "Surgical repair (procedure)"
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
  ACT1[Procedure: cabg]
  REC -->|RECOMMENDS_PROCEDURE| ACT1
  subgraph Human_and_1_AND
    D_and_1_1[DecisionNode and_1 s1]
    C_and_1_1[Condition: ccs]
    D_and_1_1 -->|CHECKS_FOR| C_and_1_1
    D_and_1_2[DecisionNode and_1 s2]
    C_and_1_2[Condition: surgically eligible]
    D_and_1_2 -->|CHECKS_FOR| C_and_1_2
    D_and_1_3[DecisionNode and_1 s3]
    C_and_1_3[Condition: multivessel cad]
    D_and_1_3 -->|CHECKS_FOR| C_and_1_3
    D_and_1_4[DecisionNode and_1 s4]
    C_and_1_4[ClinicalParameter: lvef]
    D_and_1_4 -->|EVALUATES| C_and_1_4
    D_and_1_1 -->|LEADS_TO condition_met=true| D_and_1_2
    D_and_1_2 -->|LEADS_TO condition_met=true| D_and_1_3
    D_and_1_3 -->|LEADS_TO condition_met=true| D_and_1_4
  end
  D_and_1_4 -->|RESULTS_IN condition_met=true| REC
```

Mermaid (LLM Generated):

```mermaid
graph LR
  REC[RecommendationNode]
  ACT1[Procedure: myocardial revascularization with cabg]
  REC -->|RECOMMENDS_PROCEDURE| ACT1
  subgraph LLM_group_1_AND
    D_group_1_1[DecisionNode group_1 s1]
    C_group_1_1[ClinicalParameter: left ventricular ejection fraction]
    D_group_1_1 -->|EVALUATES| C_group_1_1
    D_group_1_2[DecisionNode group_1 s2]
    C_group_1_2[ClinicalParameter: lvef ≤ 35%]
    D_group_1_2 -->|EVALUATES| C_group_1_2
    D_group_1_3[DecisionNode group_1 s3]
    C_group_1_3[ClinicalParameter: multivessel cad]
    D_group_1_3 -->|EVALUATES| C_group_1_3
    D_group_1_4[DecisionNode group_1 s4]
    C_group_1_4[ClinicalParameter: multivessel coronary artery disease]
    D_group_1_4 -->|EVALUATES| C_group_1_4
    D_group_1_5[DecisionNode group_1 s5]
    C_group_1_5[Condition: surgically eligible ccs patients]
    D_group_1_5 -->|CHECKS_FOR| C_group_1_5
    D_group_1_6[DecisionNode group_1 s6]
    C_group_1_6[ClinicalParameter: surgically eligible patient with coronary circulation syndrome]
    D_group_1_6 -->|EVALUATES| C_group_1_6
    D_group_1_1 -->|LEADS_TO condition_met=true| D_group_1_2
    D_group_1_2 -->|LEADS_TO condition_met=true| D_group_1_3
    D_group_1_3 -->|LEADS_TO condition_met=true| D_group_1_4
    D_group_1_4 -->|LEADS_TO condition_met=true| D_group_1_5
    D_group_1_5 -->|LEADS_TO condition_met=true| D_group_1_6
  end
  D_group_1_6 -->|RESULTS_IN condition_met=true| REC
```

Grounding summary (optional):

```json
{
  "enabled": true,
  "total_grounded": 7,
  "target_label_counts": {
    "ClinicalCondition": 2,
    "ClinicalParameter": 4,
    "Procedure": 1
  },
  "root_hit_counts": {
    "363787002": 2,
    "71388002": 1
  },
  "root_hits": [
    {
      "entity": "surgically eligible CCS patients",
      "entity_original": "surgically eligible CCS patients",
      "role": "Condition",
      "preferred_term": null,
      "synonyms": [],
      "snomed_id": null,
      "target_label": "ClinicalCondition",
      "taxonomy_path": [],
      "root_hit": null
    },
    {
      "entity": "multivessel CAD",
      "entity_original": "multivessel CAD",
      "role": "ClinicalParameter",
      "preferred_term": null,
      "synonyms": [],
      "snomed_id": null,
      "target_label": "ClinicalParameter",
      "taxonomy_path": [],
      "root_hit": null
    },
    {
      "entity": "LVEF \u2264 35%",
      "entity_original": "LVEF \u2264 35%",
      "role": "ClinicalParameter",
      "preferred_term": "Left ventricular ejection fraction (observable entity)",
      "synonyms": [
        "Left ventricular ejection fraction",
        "LVEF - Left ventricular ejection fraction"
      ],
      "snomed_id": 250908004,
      "target_label": "ClinicalParameter",
      "taxonomy_path": [
        {
          "concept_id": "250908004",
          "term": "Left ventricular ejection fraction (observable entity)"
        },
        {
          "concept_id": "250907009",
          "term": "Left ventricular function (observable entity)"
        },
        {
          "concept_id": "86185002",
          "term": "Cardiac function (observable entity)"
        },
        {
          "concept_id": "70337006",
          "term": "Cardiovascular function (observable entity)"
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
      "entity": "myocardial revascularization with CABG",
      "entity_original": "myocardial revascularization with CABG",
      "role": "Procedure",
      "preferred_term": "Coronary artery bypass grafting (procedure)",
      "synonyms": [
        "Coronary artery bypass graft",
        "CABG - Coronary artery bypass graft",
        "CBG - Coronary bypass graft",
        "Coronary artery bypass grafting",
        "Coronary artery bypass graft operations",
        "CAG - Coronary artery graft"
      ],
      "snomed_id": 232717009,
      "target_label": "Procedure",
      "taxonomy_path": [
        {
          "concept_id": "232717009",
          "term": "Coronary artery bypass grafting (procedure)"
        },
        {
          "concept_id": "116360008",
          "term": "Arterial bypass graft (procedure)"
        },
        {
          "concept_id": "23075000",
          "term": "Creation of vascular bypass (procedure)"
        },
        {
          "concept_id": "48537004",
          "term": "Bypass graft (procedure)"
        },
        {
          "concept_id": "78817002",
          "term": "Construction of anastomosis (procedure)"
        },
        {
          "concept_id": "410614008",
          "term": "Construction (procedure)"
        },
        {
          "concept_id": "4365001",
          "term": "Surgical repair (procedure)"
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
      "entity": "Surgically eligible patient with coronary circulation syndrome",
      "entity_original": "surgically eligible CCS patients",
      "role": "ClinicalParameter",
      "preferred_term": null,
      "synonyms": [],
      "snomed_id": null,
      "target_label": "ClinicalParameter",
      "taxonomy_path": [],
      "root_hit": null
    },
    {
      "entity": "Multivessel coronary artery disease",
      "entity_original": "multivessel CAD",
      "role": "ClinicalParameter",
      "preferred_term": "Coronary artery disease (disorder)",
      "synonyms": [],
      "snomed_id": 8957000,
      "target_label": "ClinicalCondition",
      "taxonomy_path": [
        {
          "concept_id": "8957000",
          "term": "Coronary artery disease (disorder)"
        }
      ],
      "root_hit": null
    },
    {
      "entity": "Left ventricular ejection fraction",
      "entity_original": "LVEF \u2264 35%",
      "role": "ClinicalParameter",
      "preferred_term": "Left ventricular ejection fraction (observable entity)",
      "synonyms": [],
      "snomed_id": 250908004,
      "target_label": "ClinicalParameter",
      "taxonomy_path": [
        {
          "concept_id": "250908004",
          "term": "Left ventricular ejection fraction (observable entity)"
        },
        {
          "concept_id": "70822001",
          "term": "Cardiac ejection fraction, function (observable entity)"
        },
        {
          "concept_id": "86185002",
          "term": "Cardiac function (observable entity)"
        },
        {
          "concept_id": "70337006",
          "term": "Cardiovascular function (observable entity)"
        },
        {
          "concept_id": "246464006",
          "term": "Function (observable entity)"
        },
        {
          "concept_id": "363787002",
          "term": "Observable entity (observable entity)"
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
- expected: 5
- actual: 7
- matches: 0
- missing: 5
- extra: 7

Missing concepts:
- ClinicalParameter: lvef
- Condition: ccs
- Condition: multivessel cad
- Condition: surgically eligible
- Procedure: cabg

Extra concepts:
- ClinicalParameter: left ventricular ejection fraction
- ClinicalParameter: lvef ≤ 35%
- ClinicalParameter: multivessel cad
- ClinicalParameter: multivessel coronary artery disease
- ClinicalParameter: surgically eligible patient with coronary circulation syndrome
- Condition: surgically eligible ccs patients
- Procedure: myocardial revascularization with cabg

Rules (concept + logic fields):
- expected: 5
- actual: 7
- matches: 0
- missing: 5
- extra: 7

Missing rules:
- ClinicalParameter: lvef | op=≤ | thr=35 | unit=% | logic=AND | grp=and_1
- Condition: ccs | op=PRESENT | logic=AND | grp=and_1
- Condition: multivessel cad | op=PRESENT | logic=AND | grp=and_1
- Condition: surgically eligible | op=PRESENT | logic=AND | grp=and_1
- Procedure: cabg | class=I | level=B | dir=POSITIVE

Extra rules:
- ClinicalParameter: left ventricular ejection fraction | op=LE | thr=35 | unit=% | ctx=left ventricular ejection fraction | class=I | level=B | dir=POSITIVE
- ClinicalParameter: lvef ≤ 35% | op=≤ | thr=35 | unit=% | dir=UNKNOWN
- ClinicalParameter: multivessel cad | op=PRESENT | dir=UNKNOWN
- ClinicalParameter: multivessel coronary artery disease | op=PRESENT | ctx=multivessel | class=I | level=B | dir=POSITIVE
- ClinicalParameter: surgically eligible patient with coronary circulation syndrome | op=PRESENT | ctx=surgically eligible | class=I | level=B | dir=POSITIVE
- Condition: surgically eligible ccs patients | op=PRESENT | dir=UNKNOWN
- Procedure: myocardial revascularization with cabg | class=I | level=B | dir=POSITIVE

