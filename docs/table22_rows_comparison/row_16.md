# row_16 (mapped to row_16)

Original table row text (ground truth):

```json
{
  "Recommendations": "Intracoronary imaging guidance by IVUS or OCTis recommended when performing PCI on anatomically complex lesions, in particular left main stem, true bifurcations, and long lesions. 866,337,810,840,841",
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
    "conditions": [
      {
        "entity": "percutaneous coronary revascularization",
        "entity_original": "pci",
        "role": "Procedure",
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
        "snomed_id": "415070008",
        "target_label": null,
        "taxonomy_path": [],
        "root_concept_id": null,
        "root_concept_term": null
      },
      {
        "entity": "lesion",
        "entity_original": "anatomically complex lesions",
        "role": "ClinicalCondition",
        "operator": "PRESENT",
        "threshold": null,
        "unit": null,
        "context": null,
        "logic_type": "OR",
        "logic_group": "or_1",
        "strength": null,
        "level": null,
        "direction": null,
        "preferred_term": null,
        "synonyms": [],
        "snomed_id": "52988006",
        "target_label": null,
        "taxonomy_path": [],
        "root_concept_id": null,
        "root_concept_term": null
      },
      {
        "entity": "stenosis of left coronary artery main stem",
        "entity_original": "left main stem lesions",
        "role": "ClinicalCondition",
        "operator": "PRESENT",
        "threshold": null,
        "unit": null,
        "context": null,
        "logic_type": "OR",
        "logic_group": "or_1",
        "strength": null,
        "level": null,
        "direction": null,
        "preferred_term": null,
        "synonyms": [],
        "snomed_id": "876857001",
        "target_label": null,
        "taxonomy_path": [],
        "root_concept_id": null,
        "root_concept_term": null
      },
      {
        "entity": "lesion",
        "entity_original": "true bifurcations lesions",
        "role": "ClinicalCondition",
        "operator": "PRESENT",
        "threshold": null,
        "unit": null,
        "context": null,
        "logic_type": "OR",
        "logic_group": "or_1",
        "strength": null,
        "level": null,
        "direction": null,
        "preferred_term": null,
        "synonyms": [],
        "snomed_id": "52988006",
        "target_label": null,
        "taxonomy_path": [],
        "root_concept_id": null,
        "root_concept_term": null
      },
      {
        "entity": "lesion",
        "entity_original": "long lesions",
        "role": "ClinicalCondition",
        "operator": "PRESENT",
        "threshold": null,
        "unit": null,
        "context": null,
        "logic_type": "OR",
        "logic_group": "or_1",
        "strength": null,
        "level": null,
        "direction": null,
        "preferred_term": null,
        "synonyms": [],
        "snomed_id": "52988006",
        "target_label": null,
        "taxonomy_path": [],
        "root_concept_id": null,
        "root_concept_term": null
      }
    ],
    "actions": [
      {
        "entity": "intravascular ultrasound of artery",
        "entity_original": "intracoronary imaging guidance by ivus recommended",
        "role": "Procedure",
        "operator": null,
        "threshold": null,
        "unit": null,
        "context": null,
        "logic_type": null,
        "logic_group": null,
        "strength": "I",
        "level": "A",
        "direction": "POSITIVE",
        "preferred_term": null,
        "synonyms": [],
        "snomed_id": "241467003",
        "target_label": null,
        "taxonomy_path": [],
        "root_concept_id": null,
        "root_concept_term": null
      },
      {
        "entity": "optical coherence tomography",
        "entity_original": "intracoronary imaging guidance by octis recommended",
        "role": "Procedure",
        "operator": null,
        "threshold": null,
        "unit": null,
        "context": null,
        "logic_type": null,
        "logic_group": null,
        "strength": "I",
        "level": "A",
        "direction": "POSITIVE",
        "preferred_term": null,
        "synonyms": [],
        "snomed_id": "392010000",
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
          "entity": "percutaneous coronary intervention",
          "entity_original": "pci",
          "role": "Procedure",
          "operator": "PLANNED",
          "threshold": null,
          "unit": null,
          "context": null,
          "logic_type": null,
          "logic_group": null,
          "strength": "Unknown",
          "level": "Unknown",
          "direction": null,
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
          "root_concept_term": "Procedure (procedure)"
        },
        {
          "entity": "anatomically complex lesion",
          "entity_original": "anatomically complex lesions",
          "role": "Condition",
          "operator": "PRESENT",
          "threshold": null,
          "unit": null,
          "context": null,
          "logic_type": null,
          "logic_group": null,
          "strength": "Unknown",
          "level": "Unknown",
          "direction": null,
          "preferred_term": "Lumbosacral plexus lesion (disorder)",
          "synonyms": [
            "Lumbosacral plexus lesion"
          ],
          "snomed_id": 4062006,
          "target_label": "ClinicalCondition",
          "taxonomy_path": [
            {
              "concept_id": "4062006",
              "term": "Lumbosacral plexus lesion (disorder)"
            },
            {
              "concept_id": "239953001",
              "term": "Lesion of soft tissue (disorder)"
            },
            {
              "concept_id": "19660004",
              "term": "Disorder of soft tissue (disorder)"
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
          "root_concept_term": "Clinical finding (finding)"
        }
      ],
      "actions": [
        {
          "entity": "intracoronary ultrasound or optical coherence tomography",
          "entity_original": "intracoronary imaging guidance by ivus or oct",
          "role": "Procedure",
          "operator": null,
          "threshold": null,
          "unit": null,
          "context": null,
          "logic_type": null,
          "logic_group": null,
          "strength": "Class I",
          "level": "A",
          "direction": "POSITIVE",
          "preferred_term": "Intravascular optical coherence tomography of coronary vessel (procedure)",
          "synonyms": [
            "Intravascular imaging of coronary vessel by optical coherence tomography",
            "Intravascular optical coherence tomography of coronary vessel",
            "Intravascular OCT (optical coherence tomography) of coronary vessel"
          ],
          "snomed_id": 698254001,
          "target_label": "Procedure",
          "taxonomy_path": [
            {
              "concept_id": "698254001",
              "term": "Intravascular optical coherence tomography of coronary vessel (procedure)"
            },
            {
              "concept_id": "46377000",
              "term": "Cardiac tomography (procedure)"
            },
            {
              "concept_id": "169037009",
              "term": "Tomography - chest (procedure)"
            },
            {
              "concept_id": "413815006",
              "term": "Chest imaging (procedure)"
            },
            {
              "concept_id": "363679005",
              "term": "Imaging (procedure)"
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
  ACT1[Procedure: intravascular ultrasound of artery]
  REC -->|RECOMMENDS_PROCEDURE| ACT1
  ACT2[Procedure: optical coherence tomography]
  REC -->|RECOMMENDS_PROCEDURE| ACT2
  subgraph Human_and_1_AND
    D_and_1_1[DecisionNode and_1 s1]
    C_and_1_1[Procedure: percutaneous coronary revascularization]
    D_and_1_1 -->|CHECKS_FOR| C_and_1_1
  end
  subgraph Human_or_1_OR
    D_or_1_1[DecisionNode or_1 s1]
    C_or_1_1[ClinicalCondition: lesion]
    D_or_1_1 -->|CHECKS_FOR| C_or_1_1
    D_or_1_2[DecisionNode or_1 s2]
    C_or_1_2[ClinicalCondition: stenosis of left coronary artery main stem]
    D_or_1_2 -->|CHECKS_FOR| C_or_1_2
    D_or_1_3[DecisionNode or_1 s3]
    C_or_1_3[ClinicalCondition: lesion]
    D_or_1_3 -->|CHECKS_FOR| C_or_1_3
    D_or_1_4[DecisionNode or_1 s4]
    C_or_1_4[ClinicalCondition: lesion]
    D_or_1_4 -->|CHECKS_FOR| C_or_1_4
    D_and_1_1 -->|LEADS_TO condition_met=true| D_or_1_1
    D_and_1_1 -->|LEADS_TO condition_met=true| D_or_1_2
    D_and_1_1 -->|LEADS_TO condition_met=true| D_or_1_3
    D_and_1_1 -->|LEADS_TO condition_met=true| D_or_1_4
  end
  D_or_1_1 -->|RESULTS_IN condition_met=true| REC
  D_or_1_2 -->|RESULTS_IN condition_met=true| REC
  D_or_1_3 -->|RESULTS_IN condition_met=true| REC
  D_or_1_4 -->|RESULTS_IN condition_met=true| REC
```

Mermaid (LLM Generated):

```mermaid
graph LR
  REC[RecommendationNode]
  ACT1[Procedure: intracoronary ultrasound or optical coherence tomography]
  REC -->|RECOMMENDS_PROCEDURE| ACT1
  subgraph LLM_group_1_AND
    D_group_1_1[DecisionNode group_1 s1]
    C_group_1_1[Procedure: percutaneous coronary intervention]
    D_group_1_1 -->|CHECKS_FOR| C_group_1_1
    D_group_1_2[DecisionNode group_1 s2]
    C_group_1_2[Condition: anatomically complex lesion]
    D_group_1_2 -->|CHECKS_FOR| C_group_1_2
    D_group_1_1 -->|LEADS_TO condition_met=true| D_group_1_2
  end
  D_group_1_2 -->|RESULTS_IN condition_met=true| REC
```

Grounding summary (optional):

```json
{
  "enabled": true,
  "total_grounded": 3,
  "target_label_counts": {
    "Procedure": 2,
    "ClinicalCondition": 1
  },
  "root_hit_counts": {
    "71388002": 2,
    "404684003": 1
  },
  "root_hits": [
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
      "entity": "Intracoronary ultrasound or optical coherence tomography",
      "entity_original": "Intracoronary imaging guidance by IVUS or OCT",
      "role": "Procedure",
      "preferred_term": "Intravascular optical coherence tomography of coronary vessel (procedure)",
      "synonyms": [
        "Intravascular imaging of coronary vessel by optical coherence tomography",
        "Intravascular optical coherence tomography of coronary vessel",
        "Intravascular OCT (optical coherence tomography) of coronary vessel"
      ],
      "snomed_id": 698254001,
      "target_label": "Procedure",
      "taxonomy_path": [
        {
          "concept_id": "698254001",
          "term": "Intravascular optical coherence tomography of coronary vessel (procedure)"
        },
        {
          "concept_id": "46377000",
          "term": "Cardiac tomography (procedure)"
        },
        {
          "concept_id": "169037009",
          "term": "Tomography - chest (procedure)"
        },
        {
          "concept_id": "413815006",
          "term": "Chest imaging (procedure)"
        },
        {
          "concept_id": "363679005",
          "term": "Imaging (procedure)"
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
      "entity": "Anatomically complex lesion",
      "entity_original": "anatomically complex lesions",
      "role": "Condition",
      "preferred_term": "Lumbosacral plexus lesion (disorder)",
      "synonyms": [
        "Lumbosacral plexus lesion"
      ],
      "snomed_id": 4062006,
      "target_label": "ClinicalCondition",
      "taxonomy_path": [
        {
          "concept_id": "4062006",
          "term": "Lumbosacral plexus lesion (disorder)"
        },
        {
          "concept_id": "239953001",
          "term": "Lesion of soft tissue (disorder)"
        },
        {
          "concept_id": "19660004",
          "term": "Disorder of soft tissue (disorder)"
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
    }
  ]
}
```

Concepts:
- expected: 5
- actual: 9
- matches: 0
- missing: 5
- extra: 9

Missing concepts:
- ClinicalCondition: lesion
- ClinicalCondition: stenosis of left coronary artery main stem
- Procedure: intravascular ultrasound of artery
- Procedure: optical coherence tomography
- Procedure: percutaneous coronary revascularization

Extra concepts:
- ClinicalParameter: left main stem lesion
- ClinicalParameter: long coronary lesion
- ClinicalParameter: true coronary bifurcation
- Condition: anatomically complex lesion
- Condition: left main stem lesion
- Condition: long lesion
- Condition: true bifurcation lesion
- Procedure: intracoronary ultrasound or optical coherence tomography
- Procedure: percutaneous coronary intervention

Rules (concept + logic fields):
- expected: 5
- actual: 9
- matches: 0
- missing: 5
- extra: 9

Missing rules:
- ClinicalCondition: lesion | op=PRESENT | logic=OR | grp=or_1
- ClinicalCondition: stenosis of left coronary artery main stem | op=PRESENT | logic=OR | grp=or_1
- Procedure: intravascular ultrasound of artery | class=I | level=A | dir=POSITIVE
- Procedure: optical coherence tomography | class=I | level=A | dir=POSITIVE
- Procedure: percutaneous coronary revascularization | op=PRESENT | logic=AND | grp=and_1

Extra rules:
- ClinicalParameter: left main stem lesion | op=PRESENT | class=Unknown | level=Unknown
- ClinicalParameter: long coronary lesion | op=PRESENT | class=Unknown | level=Unknown
- ClinicalParameter: true coronary bifurcation | op=PRESENT | class=Unknown | level=Unknown
- Condition: anatomically complex lesion | op=PRESENT | class=Unknown | level=Unknown
- Condition: left main stem lesion | op=PRESENT | class=Unknown | level=Unknown
- Condition: long lesion | op=PRESENT | class=Unknown | level=Unknown
- Condition: true bifurcation lesion | op=PRESENT | class=Unknown | level=Unknown
- Procedure: intracoronary ultrasound or optical coherence tomography | class=Class I | level=A | dir=POSITIVE
- Procedure: percutaneous coronary intervention | op=PLANNED | class=Unknown | level=Unknown

