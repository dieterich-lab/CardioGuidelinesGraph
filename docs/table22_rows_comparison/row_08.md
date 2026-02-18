# row_08 (mapped to row_08)

Original table row text (ground truth):

```json
{
  "Recommendations": "In CCS patients with LVEF > 35%, myocardial revascularization is recommended, in addition to guideline-directed medical therapy, for patients with functionally significant single- or two-vessel disease involving the proximal LAD, to reduce long-term cardiovascular mortality",
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
        "entity": "lvef",
        "entity_original": "lvef > 35%",
        "role": "ClinicalParameter",
        "operator": ">",
        "threshold": "35",
        "unit": "%",
        "condition_context": null,
        "logic_type": "AND",
        "logic_group": "and_1",
        "strength": null,
        "level": null,
        "direction": null
      },
      {
        "entity": "functionally significant three-vessel disease",
        "entity_original": "functionally significant single-vessel disease involving the proximal lad",
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
        "entity": "functionally significant three-vessel disease",
        "entity_original": "functionally significant two-vessel disease involving the proximal lad",
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
      }
    ],
    "actions": [
      {
        "entity": "myocardial revascularization",
        "entity_original": "myocardial revascularization to reduce long-term cardiovascular mortality",
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
      },
      {
        "entity": "guideline-directed medical therapy",
        "entity_original": "guideline-directed medical therapy to reduce long-term cardiovascular mortality",
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
        "entity": "left ventricular ejection fraction",
        "entity_original": "lvef > 35%",
        "role": "ClinicalParameter",
        "operator": ">",
        "threshold": "35",
        "unit": "%",
        "condition_context": null,
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
      },
      {
        "entity": "proximal left anterior descending artery disease",
        "entity_original": "functionally significant single- or two-vessel disease involving the proximal lad",
        "role": "ClinicalParameter",
        "operator": "PRESENT",
        "threshold": null,
        "unit": null,
        "condition_context": "functionally significant",
        "logic_type": null,
        "logic_group": null,
        "strength": "I",
        "level": "B",
        "direction": "POSITIVE",
        "rule_id": 1,
        "side": "condition",
        "preferred_term": "Left anterior descending coronary artery thrombosis (disorder)",
        "synonyms": [
          "Left anterior descending coronary artery thrombosis"
        ],
        "snomed_id": 28248000,
        "target_label": "ClinicalCondition",
        "taxonomy_path": [
          {
            "concept_id": "28248000",
            "term": "Left anterior descending coronary artery thrombosis (disorder)"
          },
          {
            "concept_id": "398274000",
            "term": "Coronary artery thrombosis (disorder)"
          },
          {
            "concept_id": "65198009",
            "term": "Arterial thrombosis (disorder)"
          },
          {
            "concept_id": "359557001",
            "term": "Disorder of artery (disorder)"
          },
          {
            "concept_id": "27550009",
            "term": "Disorder of blood vessel (disorder)"
          },
          {
            "concept_id": "19660004",
            "term": "Disorder of soft tissue (disorder)"
          },
          {
            "concept_id": "248402002",
            "term": "General finding of soft tissue (finding)"
          },
          {
            "concept_id": "404684003",
            "term": "Clinical finding (finding)"
          },
          {
            "concept_id": "138875005",
            "term": "SNOMED CT Concept (SNOMED RT+CTV3)"
          }
        ],
        "root_concept_id": "404684003",
        "root_concept_term": "Clinical finding (finding)",
        "mapped_target_label": "ClinicalCondition"
      },
      {
        "entity": "lvef",
        "entity_original": "lvef > 35%",
        "role": "ClinicalParameter",
        "operator": ">",
        "threshold": "35",
        "unit": "%",
        "condition_context": null,
        "logic_type": null,
        "logic_group": null,
        "strength": "I",
        "level": "B",
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
        "entity": "functionally significant single",
        "entity_original": "functionally significant single- or two-vessel disease involving the proximal lad",
        "role": "ClinicalParameter",
        "operator": "PRESENT",
        "threshold": null,
        "unit": null,
        "condition_context": null,
        "logic_type": "OR",
        "logic_group": "or_1",
        "strength": "I",
        "level": "B",
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
        "entity": "two-vessel disease involving proximal lad",
        "entity_original": "functionally significant single- or two-vessel disease involving the proximal lad",
        "role": "ClinicalParameter",
        "operator": "PRESENT",
        "threshold": null,
        "unit": null,
        "condition_context": null,
        "logic_type": "OR",
        "logic_group": "or_1",
        "strength": "I",
        "level": "B",
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
      }
    ],
    "actions": [
      {
        "entity": "myocardial revascularization",
        "entity_original": "myocardial revascularization",
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
  ACT2[Procedure: guideline-directed medical therapy]
  REC -->|RECOMMENDS_PROCEDURE| ACT2
  subgraph Human_and_1_AND
    D_and_1_1[DecisionNode and_1 s1]
    C_and_1_1[Condition: ccs]
    D_and_1_1 -->|CHECKS_FOR| C_and_1_1
    D_and_1_2[DecisionNode and_1 s2]
    C_and_1_2[ClinicalParameter: lvef]
    D_and_1_2 -->|EVALUATES| C_and_1_2
    D_and_1_1 -->|LEADS_TO condition_met=true| D_and_1_2
  end
  subgraph Human_or_1_OR
    D_or_1_1[DecisionNode or_1 s1]
    C_or_1_1[Condition: functionally significant three-vessel disease]
    D_or_1_1 -->|CHECKS_FOR| C_or_1_1
    D_or_1_2[DecisionNode or_1 s2]
    C_or_1_2[Condition: functionally significant three-vessel disease]
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
    C_group_1_1[Condition: ccs patients]
    D_group_1_1 -->|CHECKS_FOR| C_group_1_1
    D_group_1_2[DecisionNode group_1 s2]
    C_group_1_2[Condition: chronic coronary syndrome]
    D_group_1_2 -->|CHECKS_FOR| C_group_1_2
    D_group_1_3[DecisionNode group_1 s3]
    C_group_1_3[ClinicalParameter: left ventricular ejection fraction]
    D_group_1_3 -->|EVALUATES| C_group_1_3
    D_group_1_4[DecisionNode group_1 s4]
    C_group_1_4[ClinicalParameter: lvef]
    D_group_1_4 -->|EVALUATES| C_group_1_4
    D_group_1_5[DecisionNode group_1 s5]
    C_group_1_5[ClinicalParameter: proximal left anterior descending artery disease]
    D_group_1_5 -->|EVALUATES| C_group_1_5
    D_group_1_1 -->|LEADS_TO condition_met=true| D_group_1_2
    D_group_1_2 -->|LEADS_TO condition_met=true| D_group_1_3
    D_group_1_3 -->|LEADS_TO condition_met=true| D_group_1_4
    D_group_1_4 -->|LEADS_TO condition_met=true| D_group_1_5
  end
  subgraph LLM_or_1_OR
    D_or_1_1[DecisionNode or_1 s1]
    C_or_1_1[ClinicalParameter: functionally significant single]
    D_or_1_1 -->|EVALUATES| C_or_1_1
    D_or_1_2[DecisionNode or_1 s2]
    C_or_1_2[ClinicalParameter: two-vessel disease involving proximal lad]
    D_or_1_2 -->|EVALUATES| C_or_1_2
    D_group_1_5 -->|LEADS_TO condition_met=true| D_or_1_1
    D_group_1_5 -->|LEADS_TO condition_met=true| D_or_1_2
  end
  D_or_1_1 -->|RESULTS_IN condition_met=true| REC
  D_or_1_2 -->|RESULTS_IN condition_met=true| REC
```

Grounding summary (optional):

```json
{
  "enabled": true,
  "total_grounded": 6,
  "target_label_counts": {
    "ClinicalParameter": 4,
    "ClinicalCondition": 1,
    "Procedure": 1
  },
  "root_hit_counts": {
    "363787002": 2,
    "404684003": 1,
    "71388002": 1
  },
  "root_hits": [
    {
      "entity": "Left Ventricular Ejection Fraction",
      "entity_original": "LVEF > 35%",
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
    },
    {
      "entity": "Proximal Left Anterior Descending Artery Disease",
      "entity_original": "functionally significant single- or two-vessel disease involving the proximal LAD",
      "role": "ClinicalParameter",
      "preferred_term": "Left anterior descending coronary artery thrombosis (disorder)",
      "synonyms": [
        "Left anterior descending coronary artery thrombosis"
      ],
      "snomed_id": 28248000,
      "target_label": "ClinicalCondition",
      "taxonomy_path": [
        {
          "concept_id": "28248000",
          "term": "Left anterior descending coronary artery thrombosis (disorder)"
        },
        {
          "concept_id": "398274000",
          "term": "Coronary artery thrombosis (disorder)"
        },
        {
          "concept_id": "65198009",
          "term": "Arterial thrombosis (disorder)"
        },
        {
          "concept_id": "359557001",
          "term": "Disorder of artery (disorder)"
        },
        {
          "concept_id": "27550009",
          "term": "Disorder of blood vessel (disorder)"
        },
        {
          "concept_id": "19660004",
          "term": "Disorder of soft tissue (disorder)"
        },
        {
          "concept_id": "248402002",
          "term": "General finding of soft tissue (finding)"
        },
        {
          "concept_id": "404684003",
          "term": "Clinical finding (finding)"
        },
        {
          "concept_id": "138875005",
          "term": "SNOMED CT Concept (SNOMED RT+CTV3)"
        }
      ],
      "root_hit": {
        "root_concept_id": "404684003",
        "root_concept_term": "Clinical finding (finding)",
        "mapped_target_label": "ClinicalCondition"
      }
    },
    {
      "entity": "Myocardial Revascularization",
      "entity_original": "myocardial revascularization",
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
      "entity": "LVEF",
      "entity_original": "LVEF > 35%",
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
      "entity": "functionally significant single",
      "entity_original": "functionally significant single- or two-vessel disease involving the proximal LAD",
      "role": "ClinicalParameter",
      "preferred_term": null,
      "synonyms": [],
      "snomed_id": null,
      "target_label": "ClinicalParameter",
      "taxonomy_path": [],
      "root_hit": null
    },
    {
      "entity": "two-vessel disease involving proximal LAD",
      "entity_original": "functionally significant single- or two-vessel disease involving the proximal LAD",
      "role": "ClinicalParameter",
      "preferred_term": null,
      "synonyms": [],
      "snomed_id": null,
      "target_label": "ClinicalParameter",
      "taxonomy_path": [],
      "root_hit": null
    }
  ]
}
```

Concepts:
- expected: 5
- actual: 8
- matches: 2
- missing: 3
- extra: 6

Missing concepts:
- Condition: ccs
- Condition: functionally significant three-vessel disease
- Procedure: guideline-directed medical therapy

Extra concepts:
- ClinicalParameter: functionally significant single
- ClinicalParameter: left ventricular ejection fraction
- ClinicalParameter: proximal left anterior descending artery disease
- ClinicalParameter: two-vessel disease involving proximal lad
- Condition: ccs patients
- Condition: chronic coronary syndrome

Rules (concept + logic fields):
- expected: 5
- actual: 8
- matches: 1
- missing: 4
- extra: 7

Missing rules:
- ClinicalParameter: lvef | op=> | thr=35 | unit=% | logic=AND | grp=and_1
- Condition: ccs | op=PRESENT | logic=AND | grp=and_1
- Condition: functionally significant three-vessel disease | op=PRESENT | logic=OR | grp=or_1
- Procedure: guideline-directed medical therapy | class=I | level=B | dir=POSITIVE

Extra rules:
- ClinicalParameter: functionally significant single | op=PRESENT | logic=OR | grp=or_1 | class=I | level=B | dir=UNKNOWN
- ClinicalParameter: left ventricular ejection fraction | op=> | thr=35 | unit=% | class=I | level=B | dir=POSITIVE
- ClinicalParameter: lvef | op=> | thr=35 | unit=% | class=I | level=B | dir=UNKNOWN
- ClinicalParameter: proximal left anterior descending artery disease | op=PRESENT | ctx=functionally significant | class=I | level=B | dir=POSITIVE
- ClinicalParameter: two-vessel disease involving proximal lad | op=PRESENT | logic=OR | grp=or_1 | class=I | level=B | dir=UNKNOWN
- Condition: ccs patients | op=PRESENT | class=I | level=B | dir=UNKNOWN
- Condition: chronic coronary syndrome | op=PRESENT | class=I | level=B | dir=POSITIVE

