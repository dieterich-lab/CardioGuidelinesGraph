# row_17 (mapped to row_17)

Original table row text (ground truth):

```json
{
  "Recommendations": "\u2022 is recommended to guide lesion selection for intervention in patients with multivessel disease; 308,826,866,867",
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
        "entity": "intervention",
        "entity_original": "intervention",
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
      },
      {
        "entity": "multivessel disease",
        "entity_original": "patients with multivessel disease",
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
        "entity": "intracoronary pressure measurement (ffr)",
        "entity_original": "intracoronary pressure measurement (ffr) is recommended to guide lesion selection for intervention",
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
        "entity": "intracoronary pressure measurement (ifr)",
        "entity_original": "intracoronary pressure measurement (ifr) is recommended to guide lesion selection for intervention",
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
        "entity": "computation (qfr)",
        "entity_original": "computation (qfr) is recommended to guide lesion selection for intervention",
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
        "entity": "multivessel coronary artery disease",
        "entity_original": "multivessel disease",
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
      }
    ],
    "actions": [
      {
        "entity": "guide lesion selection for intervention",
        "entity_original": "guide lesion selection for intervention",
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
}
</pre></td>
  </tr>
</table>

Mermaid (Human Annotation):

```mermaid
graph LR
  REC[RecommendationNode]
  ACT1[Procedure: intracoronary pressure measurement (ffr)]
  REC -->|RECOMMENDS_PROCEDURE| ACT1
  ACT2[Procedure: intracoronary pressure measurement (ifr)]
  REC -->|RECOMMENDS_PROCEDURE| ACT2
  ACT3[Procedure: computation (qfr)]
  REC -->|RECOMMENDS_PROCEDURE| ACT3
  subgraph Human_and_1_AND
    D_and_1_1[DecisionNode and_1 s1]
    C_and_1_1[Procedure: intervention]
    D_and_1_1 -->|CHECKS_FOR| C_and_1_1
    D_and_1_2[DecisionNode and_1 s2]
    C_and_1_2[Condition: multivessel disease]
    D_and_1_2 -->|CHECKS_FOR| C_and_1_2
    D_and_1_1 -->|LEADS_TO condition_met=true| D_and_1_2
  end
  D_and_1_2 -->|RESULTS_IN condition_met=true| REC
```

Mermaid (LLM Generated):

```mermaid
graph LR
  REC[RecommendationNode]
  ACT1[Procedure: guide lesion selection for intervention]
  REC -->|RECOMMENDS_PROCEDURE| ACT1
  subgraph LLM_group_1_AND
    D_group_1_1[DecisionNode group_1 s1]
    C_group_1_1[ClinicalParameter: multivessel coronary artery disease]
    D_group_1_1 -->|EVALUATES| C_group_1_1
    D_group_1_2[DecisionNode group_1 s2]
    C_group_1_2[ClinicalParameter: multivessel disease]
    D_group_1_2 -->|EVALUATES| C_group_1_2
    D_group_1_1 -->|LEADS_TO condition_met=true| D_group_1_2
  end
  D_group_1_2 -->|RESULTS_IN condition_met=true| REC
```

Grounding summary (optional):

```json
{
  "enabled": true,
  "total_grounded": 2,
  "target_label_counts": {
    "ClinicalCondition": 1,
    "Procedure": 1
  },
  "root_hit_counts": {},
  "root_hits": [
    {
      "entity": "Multivessel coronary artery disease",
      "entity_original": "multivessel disease",
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
      "entity": "Guide lesion selection for intervention",
      "entity_original": "guide lesion selection for intervention",
      "role": "Procedure",
      "preferred_term": null,
      "synonyms": [],
      "snomed_id": null,
      "target_label": "Procedure",
      "taxonomy_path": [],
      "root_hit": null
    }
  ]
}
```

Concepts:
- expected: 5
- actual: 3
- matches: 0
- missing: 5
- extra: 3

Missing concepts:
- Condition: multivessel disease
- Procedure: computation (qfr)
- Procedure: intervention
- Procedure: intracoronary pressure measurement (ffr)
- Procedure: intracoronary pressure measurement (ifr)

Extra concepts:
- ClinicalParameter: multivessel coronary artery disease
- ClinicalParameter: multivessel disease
- Procedure: guide lesion selection for intervention

Rules (concept + logic fields):
- expected: 5
- actual: 3
- matches: 0
- missing: 5
- extra: 3

Missing rules:
- Condition: multivessel disease | op=PRESENT | logic=AND | grp=and_1
- Procedure: computation (qfr) | class=I | level=A | dir=POSITIVE
- Procedure: intervention | op=PRESENT | logic=AND | grp=and_1
- Procedure: intracoronary pressure measurement (ffr) | class=I | level=A | dir=POSITIVE
- Procedure: intracoronary pressure measurement (ifr) | class=I | level=A | dir=POSITIVE

Extra rules:
- ClinicalParameter: multivessel coronary artery disease | op=PRESENT | class=Unknown | level=Unknown | dir=UNKNOWN
- ClinicalParameter: multivessel disease | op=PRESENT | class=I | level=A | dir=POSITIVE
- Procedure: guide lesion selection for intervention | class=I | level=A | dir=POSITIVE

