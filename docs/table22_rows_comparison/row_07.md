# row_07 (mapped to row_07)

Original table row text (ground truth):

```json
{
  "Recommendations": "In CCS patients with LVEF > 35%, myocardial revascularization is recommended, in addition to guideline-directed medical therapy, for patients with functionally significant three-vessel disease to improve long-term survival and to reduce long-term cardiovascular mortality and the risk of spontaneous myocardial infarction. 55,56,317,732-734",
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
        "entity_original": "functionally significant three-vessel disease",
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
        "entity_original": "myocardial revascularization is recommended to improve long-term survival and to reduce long-term cardiovascular mortality and the risk of spontaneous myocardial infarction",
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
      },
      {
        "entity": "guideline-directed medical therapy",
        "entity_original": "guideline-directed medical therapy is recommended to improve long-term survival and to reduce long-term cardiovascular mortality and the risk of spontaneous myocardial infarction",
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
        "entity": "coronary cuff syndrome",
        "entity_original": "ccs patients",
        "role": "Condition",
        "operator": "PRESENT",
        "threshold": null,
        "unit": null,
        "condition_context": null,
        "logic_type": "AND",
        "logic_group": "and_1",
        "strength": "Unknown",
        "level": "Unknown",
        "direction": "UNKNOWN",
        "rule_id": 1,
        "side": "condition",
        "preferred_term": "Coronary artery spasm (disorder)",
        "synonyms": [
          "Coronary artery spasm",
          "Coronary spasm"
        ],
        "snomed_id": 23687008,
        "target_label": "ClinicalCondition",
        "taxonomy_path": [
          {
            "concept_id": "23687008",
            "term": "Coronary artery spasm (disorder)"
          },
          {
            "concept_id": "128527000",
            "term": "Disorder of smooth muscle (disorder)"
          },
          {
            "concept_id": "129565002",
            "term": "Disorder of skeletal AND/OR smooth muscle (disorder)"
          },
          {
            "concept_id": "64572001",
            "term": "Disease (disorder)"
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
        "entity": "left ventricular ejection fraction",
        "entity_original": "lvef > 35%",
        "role": "ClinicalParameter",
        "operator": ">",
        "threshold": "35",
        "unit": "%",
        "condition_context": "left ventricular ejection fraction",
        "logic_type": "AND",
        "logic_group": "and_1",
        "strength": "Unknown",
        "level": "Unknown",
        "direction": "UNKNOWN",
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
        "entity": "three-vessel coronary artery disease",
        "entity_original": "functionally significant three-vessel disease",
        "role": "Condition",
        "operator": "PRESENT",
        "threshold": null,
        "unit": null,
        "condition_context": "functionally significant",
        "logic_type": "AND",
        "logic_group": "and_1",
        "strength": "Unknown",
        "level": "Unknown",
        "direction": "UNKNOWN",
        "rule_id": 1,
        "side": "condition",
        "preferred_term": "Coronary artery spasm (disorder)",
        "synonyms": [
          "Coronary artery spasm",
          "Coronary spasm"
        ],
        "snomed_id": 23687008,
        "target_label": "ClinicalCondition",
        "taxonomy_path": [
          {
            "concept_id": "23687008",
            "term": "Coronary artery spasm (disorder)"
          },
          {
            "concept_id": "128527000",
            "term": "Disorder of smooth muscle (disorder)"
          },
          {
            "concept_id": "129565002",
            "term": "Disorder of skeletal AND/OR smooth muscle (disorder)"
          },
          {
            "concept_id": "106030000",
            "term": "Muscle finding (finding)"
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
        "entity": "left ventricular ejection fraction",
        "entity_original": "lvef > 35%",
        "role": "ClinicalParameter",
        "operator": ">",
        "threshold": "35",
        "unit": "%",
        "condition_context": null,
        "logic_type": null,
        "logic_group": null,
        "strength": "Unknown",
        "level": "Unknown",
        "direction": "UNKNOWN",
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
        "entity": "three-vessel coronary artery disease",
        "entity_original": "functionally significant three-vessel disease",
        "role": "ClinicalParameter",
        "operator": "PRESENT",
        "threshold": null,
        "unit": null,
        "condition_context": "functionally significant",
        "logic_type": null,
        "logic_group": null,
        "strength": "Unknown",
        "level": "Unknown",
        "direction": "UNKNOWN",
        "rule_id": 1,
        "side": "condition",
        "preferred_term": "Coronary artery spasm (disorder)",
        "synonyms": [
          "Coronary artery spasm",
          "Coronary spasm"
        ],
        "snomed_id": 23687008,
        "target_label": "ClinicalCondition",
        "taxonomy_path": [
          {
            "concept_id": "23687008",
            "term": "Coronary artery spasm (disorder)"
          },
          {
            "concept_id": "128527000",
            "term": "Disorder of smooth muscle (disorder)"
          },
          {
            "concept_id": "129565002",
            "term": "Disorder of skeletal AND/OR smooth muscle (disorder)"
          },
          {
            "concept_id": "106030000",
            "term": "Muscle finding (finding)"
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
  ACT2[Procedure: guideline-directed medical therapy]
  REC -->|RECOMMENDS_PROCEDURE| ACT2
  subgraph Human_and_1_AND
    D_and_1_1[DecisionNode and_1 s1]
    C_and_1_1[Condition: ccs]
    D_and_1_1 -->|CHECKS_FOR| C_and_1_1
    D_and_1_2[DecisionNode and_1 s2]
    C_and_1_2[ClinicalParameter: lvef]
    D_and_1_2 -->|EVALUATES| C_and_1_2
    D_and_1_3[DecisionNode and_1 s3]
    C_and_1_3[Condition: functionally significant three-vessel disease]
    D_and_1_3 -->|CHECKS_FOR| C_and_1_3
    D_and_1_1 -->|LEADS_TO condition_met=true| D_and_1_2
    D_and_1_2 -->|LEADS_TO condition_met=true| D_and_1_3
  end
  D_and_1_3 -->|RESULTS_IN condition_met=true| REC
```

Mermaid (LLM Generated):

```mermaid
graph LR
  REC[RecommendationNode]
  ACT1[Procedure: myocardial revascularization]
  REC -->|RECOMMENDS_PROCEDURE| ACT1
  subgraph LLM_group_1_AND
    D_group_1_1[DecisionNode group_1 s1]
    C_group_1_1[ClinicalParameter: chronic coronary syndrome]
    D_group_1_1 -->|EVALUATES| C_group_1_1
    D_group_1_2[DecisionNode group_1 s2]
    C_group_1_2[ClinicalParameter: left ventricular ejection fraction]
    D_group_1_2 -->|EVALUATES| C_group_1_2
    D_group_1_3[DecisionNode group_1 s3]
    C_group_1_3[ClinicalParameter: three-vessel coronary artery disease]
    D_group_1_3 -->|EVALUATES| C_group_1_3
    D_group_1_1 -->|LEADS_TO condition_met=true| D_group_1_2
    D_group_1_2 -->|LEADS_TO condition_met=true| D_group_1_3
  end
  subgraph LLM_and_1_AND
    D_and_1_1[DecisionNode and_1 s1]
    C_and_1_1[Condition: coronary cuff syndrome]
    D_and_1_1 -->|CHECKS_FOR| C_and_1_1
    D_and_1_2[DecisionNode and_1 s2]
    C_and_1_2[ClinicalParameter: left ventricular ejection fraction]
    D_and_1_2 -->|EVALUATES| C_and_1_2
    D_and_1_3[DecisionNode and_1 s3]
    C_and_1_3[Condition: three-vessel coronary artery disease]
    D_and_1_3 -->|CHECKS_FOR| C_and_1_3
    D_group_1_3 -->|LEADS_TO condition_met=true| D_and_1_1
    D_and_1_1 -->|LEADS_TO condition_met=true| D_and_1_2
    D_and_1_2 -->|LEADS_TO condition_met=true| D_and_1_3
  end
  D_and_1_3 -->|RESULTS_IN condition_met=true| REC
```

Grounding summary (optional):

```json
{
  "enabled": true,
  "total_grounded": 6,
  "target_label_counts": {
    "ClinicalCondition": 3,
    "ClinicalParameter": 2,
    "Procedure": 1
  },
  "root_hit_counts": {
    "404684003": 3,
    "363787002": 2,
    "71388002": 1
  },
  "root_hits": [
    {
      "entity": "Coronary Cuff Syndrome",
      "entity_original": "CCS patients",
      "role": "Condition",
      "preferred_term": "Coronary artery spasm (disorder)",
      "synonyms": [
        "Coronary artery spasm",
        "Coronary spasm"
      ],
      "snomed_id": 23687008,
      "target_label": "ClinicalCondition",
      "taxonomy_path": [
        {
          "concept_id": "23687008",
          "term": "Coronary artery spasm (disorder)"
        },
        {
          "concept_id": "128527000",
          "term": "Disorder of smooth muscle (disorder)"
        },
        {
          "concept_id": "129565002",
          "term": "Disorder of skeletal AND/OR smooth muscle (disorder)"
        },
        {
          "concept_id": "64572001",
          "term": "Disease (disorder)"
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
      "entity": "Three-Vessel Coronary Artery Disease",
      "entity_original": "functionally significant three-vessel disease",
      "role": "Condition",
      "preferred_term": "Coronary artery spasm (disorder)",
      "synonyms": [
        "Coronary artery spasm",
        "Coronary spasm"
      ],
      "snomed_id": 23687008,
      "target_label": "ClinicalCondition",
      "taxonomy_path": [
        {
          "concept_id": "23687008",
          "term": "Coronary artery spasm (disorder)"
        },
        {
          "concept_id": "128527000",
          "term": "Disorder of smooth muscle (disorder)"
        },
        {
          "concept_id": "129565002",
          "term": "Disorder of skeletal AND/OR smooth muscle (disorder)"
        },
        {
          "concept_id": "106030000",
          "term": "Muscle finding (finding)"
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
      "entity": "Three-Vessel Coronary Artery Disease",
      "entity_original": "functionally significant three-vessel disease",
      "role": "ClinicalParameter",
      "preferred_term": "Coronary artery spasm (disorder)",
      "synonyms": [
        "Coronary artery spasm",
        "Coronary spasm"
      ],
      "snomed_id": 23687008,
      "target_label": "ClinicalCondition",
      "taxonomy_path": [
        {
          "concept_id": "23687008",
          "term": "Coronary artery spasm (disorder)"
        },
        {
          "concept_id": "128527000",
          "term": "Disorder of smooth muscle (disorder)"
        },
        {
          "concept_id": "129565002",
          "term": "Disorder of skeletal AND/OR smooth muscle (disorder)"
        },
        {
          "concept_id": "106030000",
          "term": "Muscle finding (finding)"
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
- ClinicalParameter: lvef
- Condition: ccs
- Condition: functionally significant three-vessel disease
- Procedure: guideline-directed medical therapy

Extra concepts:
- ClinicalParameter: chronic coronary syndrome
- ClinicalParameter: left ventricular ejection fraction
- ClinicalParameter: three-vessel coronary artery disease
- Condition: coronary cuff syndrome
- Condition: three-vessel coronary artery disease

Rules (concept + logic fields):
- expected: 5
- actual: 7
- matches: 1
- missing: 4
- extra: 6

Missing rules:
- ClinicalParameter: lvef | op=> | thr=35 | unit=% | logic=AND | grp=and_1
- Condition: ccs | op=PRESENT | logic=AND | grp=and_1
- Condition: functionally significant three-vessel disease | op=PRESENT | logic=AND | grp=and_1
- Procedure: guideline-directed medical therapy | class=I | level=A | dir=POSITIVE

Extra rules:
- ClinicalParameter: chronic coronary syndrome | op=PRESENT | class=Unknown | level=Unknown | dir=UNKNOWN
- ClinicalParameter: left ventricular ejection fraction | op=> | thr=35 | unit=% | ctx=left ventricular ejection fraction | logic=AND | grp=and_1 | class=Unknown | level=Unknown | dir=UNKNOWN
- ClinicalParameter: left ventricular ejection fraction | op=> | thr=35 | unit=% | class=Unknown | level=Unknown | dir=UNKNOWN
- ClinicalParameter: three-vessel coronary artery disease | op=PRESENT | ctx=functionally significant | class=Unknown | level=Unknown | dir=UNKNOWN
- Condition: coronary cuff syndrome | op=PRESENT | logic=AND | grp=and_1 | class=Unknown | level=Unknown | dir=UNKNOWN
- Condition: three-vessel coronary artery disease | op=PRESENT | ctx=functionally significant | logic=AND | grp=and_1 | class=Unknown | level=Unknown | dir=UNKNOWN

