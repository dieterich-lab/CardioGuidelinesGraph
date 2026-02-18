# row_11 (mapped to row_11)

Original table row text (ground truth):

```json
{
  "Recommendations": "In selected CCS patients with functionally significant MVD and LVEF \u2264 35% who are at high surgical risk or not operable, PCI may be considered as an alternative to CABG. 526,729",
  "Class a": "IIb",
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
        "entity": "high surgical risk",
        "entity_original": "patient with high surgical risk",
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
        "entity": "not operable",
        "entity_original": "not operable patient",
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
        "entity": "functionally significant mvd",
        "entity_original": "functionally significant mvd",
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
        "entity": "pci",
        "entity_original": "pci may be considered as an alternative to cabg",
        "role": "Procedure",
        "operator": null,
        "threshold": null,
        "unit": null,
        "condition_context": null,
        "logic_type": null,
        "logic_group": null,
        "strength": "IIb",
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
        "entity": "myocardial viability defect",
        "entity_original": "functionally significant mvd",
        "role": "ClinicalParameter",
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
        "entity": "left ventricular ejection fraction \u226435%",
        "entity_original": "lvef \u2264 35%",
        "role": "ClinicalParameter",
        "operator": "LE",
        "threshold": "35",
        "unit": "%",
        "condition_context": null,
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
        "entity": "functionally significant mvd",
        "entity_original": "functionally significant mvd",
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
        "entity": "lvef",
        "entity_original": "lvef \u2264 35%",
        "role": "ClinicalParameter",
        "operator": "LE",
        "threshold": "35",
        "unit": "%",
        "condition_context": null,
        "logic_type": "AND",
        "logic_group": "and_1",
        "strength": "Unknown",
        "level": "Unknown",
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
      }
    ],
    "actions": [
      {
        "entity": "percutaneous coronary intervention",
        "entity_original": "pci",
        "role": "Procedure",
        "operator": null,
        "threshold": null,
        "unit": null,
        "condition_context": null,
        "logic_type": null,
        "logic_group": null,
        "strength": "IIb",
        "level": "B",
        "direction": "POSITIVE",
        "rule_id": 1,
        "side": "action",
        "preferred_term": "Percutaneous transluminal coronary intervention using imaging guidance with contrast (procedure)",
        "synonyms": [],
        "snomed_id": 415070008,
        "target_label": "Procedure",
        "taxonomy_path": [
          {
            "concept_id": "415070008",
            "term": "Percutaneous transluminal coronary intervention using imaging guidance with contrast (procedure)"
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
  ACT1[Procedure: pci]
  REC -->|RECOMMENDS_PROCEDURE| ACT1
  subgraph Human_and_1_AND
    D_and_1_1[DecisionNode and_1 s1]
    C_and_1_1[Condition: ccs]
    D_and_1_1 -->|CHECKS_FOR| C_and_1_1
    D_and_1_2[DecisionNode and_1 s2]
    C_and_1_2[Condition: functionally significant mvd]
    D_and_1_2 -->|CHECKS_FOR| C_and_1_2
    D_and_1_3[DecisionNode and_1 s3]
    C_and_1_3[ClinicalParameter: lvef]
    D_and_1_3 -->|EVALUATES| C_and_1_3
    D_and_1_1 -->|LEADS_TO condition_met=true| D_and_1_2
    D_and_1_2 -->|LEADS_TO condition_met=true| D_and_1_3
  end
  subgraph Human_or_1_OR
    D_or_1_1[DecisionNode or_1 s1]
    C_or_1_1[Condition: high surgical risk]
    D_or_1_1 -->|CHECKS_FOR| C_or_1_1
    D_or_1_2[DecisionNode or_1 s2]
    C_or_1_2[Condition: not operable]
    D_or_1_2 -->|CHECKS_FOR| C_or_1_2
    D_and_1_3 -->|LEADS_TO condition_met=true| D_or_1_1
    D_and_1_3 -->|LEADS_TO condition_met=true| D_or_1_2
  end
  D_or_1_1 -->|RESULTS_IN condition_met=true| REC
  D_or_1_2 -->|RESULTS_IN condition_met=true| REC
```

Mermaid (LLM Generated):

```mermaid
graph LR
  REC[RecommendationNode]
  ACT1[Procedure: percutaneous coronary intervention]
  REC -->|RECOMMENDS_PROCEDURE| ACT1
  subgraph LLM_and_1_AND
    D_and_1_1[DecisionNode and_1 s1]
    C_and_1_1[Condition: ccs patients]
    D_and_1_1 -->|CHECKS_FOR| C_and_1_1
    D_and_1_2[DecisionNode and_1 s2]
    C_and_1_2[Condition: functionally significant mvd]
    D_and_1_2 -->|CHECKS_FOR| C_and_1_2
    D_and_1_3[DecisionNode and_1 s3]
    C_and_1_3[ClinicalParameter: left ventricular ejection fraction ≤35%]
    D_and_1_3 -->|EVALUATES| C_and_1_3
    D_and_1_4[DecisionNode and_1 s4]
    C_and_1_4[ClinicalParameter: lvef]
    D_and_1_4 -->|EVALUATES| C_and_1_4
    D_and_1_5[DecisionNode and_1 s5]
    C_and_1_5[ClinicalParameter: myocardial viability defect]
    D_and_1_5 -->|EVALUATES| C_and_1_5
    D_and_1_1 -->|LEADS_TO condition_met=true| D_and_1_2
    D_and_1_2 -->|LEADS_TO condition_met=true| D_and_1_3
    D_and_1_3 -->|LEADS_TO condition_met=true| D_and_1_4
    D_and_1_4 -->|LEADS_TO condition_met=true| D_and_1_5
  end
  subgraph LLM_or_1_OR
    D_or_1_1[DecisionNode or_1 s1]
    C_or_1_1[ClinicalParameter: high surgical risk]
    D_or_1_1 -->|EVALUATES| C_or_1_1
    D_or_1_2[DecisionNode or_1 s2]
    C_or_1_2[Condition: high surgical risk]
    D_or_1_2 -->|CHECKS_FOR| C_or_1_2
    D_or_1_3[DecisionNode or_1 s3]
    C_or_1_3[ClinicalParameter: not operable]
    D_or_1_3 -->|EVALUATES| C_or_1_3
    D_or_1_4[DecisionNode or_1 s4]
    C_or_1_4[Condition: not operable]
    D_or_1_4 -->|CHECKS_FOR| C_or_1_4
    D_and_1_5 -->|LEADS_TO condition_met=true| D_or_1_1
    D_and_1_5 -->|LEADS_TO condition_met=true| D_or_1_2
    D_and_1_5 -->|LEADS_TO condition_met=true| D_or_1_3
    D_and_1_5 -->|LEADS_TO condition_met=true| D_or_1_4
  end
  D_or_1_1 -->|RESULTS_IN condition_met=true| REC
  D_or_1_2 -->|RESULTS_IN condition_met=true| REC
  D_or_1_3 -->|RESULTS_IN condition_met=true| REC
  D_or_1_4 -->|RESULTS_IN condition_met=true| REC
```

Grounding summary (optional):

```json
{
  "enabled": true,
  "total_grounded": 5,
  "target_label_counts": {
    "ClinicalParameter": 3,
    "Procedure": 1,
    "ClinicalCondition": 1
  },
  "root_hit_counts": {
    "363787002": 2,
    "71388002": 1
  },
  "root_hits": [
    {
      "entity": "Myocardial viability defect",
      "entity_original": "functionally significant MVD",
      "role": "ClinicalParameter",
      "preferred_term": null,
      "synonyms": [],
      "snomed_id": null,
      "target_label": "ClinicalParameter",
      "taxonomy_path": [],
      "root_hit": null
    },
    {
      "entity": "Left ventricular ejection fraction \u226435%",
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
    },
    {
      "entity": "Percutaneous coronary intervention",
      "entity_original": "PCI",
      "role": "Procedure",
      "preferred_term": "Percutaneous transluminal coronary intervention using imaging guidance with contrast (procedure)",
      "synonyms": [],
      "snomed_id": 415070008,
      "target_label": "Procedure",
      "taxonomy_path": [
        {
          "concept_id": "415070008",
          "term": "Percutaneous transluminal coronary intervention using imaging guidance with contrast (procedure)"
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
        }
      ],
      "root_hit": {
        "root_concept_id": "71388002",
        "root_concept_term": "Procedure (procedure)",
        "mapped_target_label": "Procedure"
      }
    },
    {
      "entity": "functionally significant MVD",
      "entity_original": "functionally significant MVD",
      "role": "Condition",
      "preferred_term": null,
      "synonyms": [],
      "snomed_id": null,
      "target_label": "ClinicalCondition",
      "taxonomy_path": [],
      "root_hit": null
    },
    {
      "entity": "LVEF",
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
    }
  ]
}
```

Concepts:
- expected: 6
- actual: 10
- matches: 4
- missing: 2
- extra: 6

Missing concepts:
- Condition: ccs
- Procedure: pci

Extra concepts:
- ClinicalParameter: high surgical risk
- ClinicalParameter: left ventricular ejection fraction ≤35%
- ClinicalParameter: myocardial viability defect
- ClinicalParameter: not operable
- Condition: ccs patients
- Procedure: percutaneous coronary intervention

Rules (concept + logic fields):
- expected: 6
- actual: 10
- matches: 0
- missing: 6
- extra: 10

Missing rules:
- ClinicalParameter: lvef | op=≤ | thr=35 | unit=% | logic=AND | grp=and_1
- Condition: ccs | op=PRESENT | logic=AND | grp=and_1
- Condition: functionally significant mvd | op=PRESENT | logic=AND | grp=and_1
- Condition: high surgical risk | op=PRESENT | logic=OR | grp=or_1
- Condition: not operable | op=PRESENT | logic=OR | grp=or_1
- Procedure: pci | class=IIb | level=B | dir=POSITIVE

Extra rules:
- ClinicalParameter: high surgical risk | op=PRESENT | logic=OR | grp=or_1 | class=Unknown | level=Unknown | dir=UNKNOWN
- ClinicalParameter: left ventricular ejection fraction ≤35% | op=LE | thr=35 | unit=% | logic=AND | grp=and_1 | class=Unknown | level=Unknown | dir=UNKNOWN
- ClinicalParameter: lvef | op=LE | thr=35 | unit=% | logic=AND | grp=and_1 | class=Unknown | level=Unknown | dir=UNKNOWN
- ClinicalParameter: myocardial viability defect | op=PRESENT | ctx=functionally significant | logic=AND | grp=and_1 | class=Unknown | level=Unknown | dir=UNKNOWN
- ClinicalParameter: not operable | op=PRESENT | logic=OR | grp=or_1 | class=Unknown | level=Unknown | dir=UNKNOWN
- Condition: ccs patients | op=PRESENT | logic=AND | grp=and_1 | class=Unknown | level=Unknown | dir=UNKNOWN
- Condition: functionally significant mvd | op=PRESENT | logic=AND | grp=and_1 | class=Unknown | level=Unknown | dir=UNKNOWN
- Condition: high surgical risk | op=PRESENT | logic=OR | grp=or_1 | class=Unknown | level=Unknown | dir=UNKNOWN
- Condition: not operable | op=PRESENT | logic=OR | grp=or_1 | class=Unknown | level=Unknown | dir=UNKNOWN
- Procedure: percutaneous coronary intervention | class=IIb | level=B | dir=POSITIVE

