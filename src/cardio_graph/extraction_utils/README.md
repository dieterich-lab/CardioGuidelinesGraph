## Graph builder: row-level extraction to Neo4j

The main script is:
- /home/pwiesenbach/CardioGuidelinesGraph/src/cardio_graph/extraction_utils/guideline_graph_builder.py

This script takes a single row (or full table), runs multi-pass BAML extraction, grounds concepts, and writes two outputs:
- grounding_index_*.json (concept cache)
- extracted_rules_*.jsonl (logic-preserving rule entries)

### Multi-pass extraction (row-level)

Each table row is formatted as a tagged block:
- [GUIDELINE: <title>]
- [SOURCE_TYPE: table]
- [FOCUS: <pass>]

We run two passes on the same row text:
1) MAIN: full rule extraction (conditions/parameters + actions)
2) POPULATION: population/cohort conditions only (no actions)

The two passes are merged and deduplicated before OR-splitting. This avoids hardcoding while improving recall for population clauses like "In chronic coronary syndrome patients...".

### Expected output structure (JSON)

The tests compare row_10 against a structure-only reference (grounding ignored). The expected JSON lives at:
- /home/pwiesenbach/CardioGuidelinesGraph/tests/expected_row_10_structure.json

Shape (structure-only):

```json
{
  "row_id": "row_10",
  "class": "I",
  "level": "A",
  "recommendation_text": "...",
  "rules": [
    {
      "rule_id": 1,
      "conditions": [
        {
          "entity_original": "CCS",
          "entity_standardized_candidate": "chronic coronary syndrome",
          "role": "Condition",
          "logic_structured": {
            "operator": "PRESENT",
            "threshold": null,
            "unit": null,
            "condition_context": null,
            "logic_type": "AND",
            "logic_group": "and_1"
          }
        }
      ],
      "actions": [
        {
          "entity_original": "myocardial revascularization",
          "entity_standardized_candidate": "myocardial revascularization",
          "role": "Procedure",
          "logic_structured": {
            "strength": "I",
            "level": "A",
            "direction": "POSITIVE"
          }
        }
      ]
    }
  ]
}
```

### How rules map into Neo4j

The loader uses extracted_rules.jsonl to build rule logic. The intended graph structure is:

```mermaid
graph LR
  C1[ClinicalCondition]
  C2[ClinicalParameter]
  C3[ClinicalCondition]
  D1[DecisionNode]
  D2[DecisionNode]
  D3[DecisionNode]
  R[RecommendationNode]
  A[Procedure]

  D1 -->|CHECKS_FOR| C1
  D2 -->|EVALUATES| C2
  D3 -->|CHECKS_FOR| C3

  D1 -->|LEADS_TO| D2
  D2 -->|LEADS_TO| D3
  D3 -->|RESULTS_IN| R

  R -->|RECOMMENDS_PROCEDURE| A
```

Notes:
- Conditions use CHECKS_FOR; clinical parameters use EVALUATES.
- AND logic is represented via LEADS_TO chains.

### Running a single row extraction

The SLURM wrapper for table_000 is intentionally untracked. Run it locally or submit via SLURM in your environment:

```bash
poetry run python /home/pwiesenbach/CardioGuidelinesGraph/src/cardio_graph/extraction_utils/guideline_graph_builder.py \
  --docling-table-json /prj/doctoral_letters/guide/data/guidelines/docling/pdf_pages/_62/tables/table_000.json \
  --docling-table-json /prj/doctoral_letters/guide/data/guidelines/docling/pdf_pages/_63/tables/table_000.json \
  --docling-table-id _62_63/table_000.json \
  --docling-footnotes-path /tmp/docling_table_footnotes.txt \
  --min-match-score 0.6 \
  --guideline-title "2024 ESC Guidelines for the management of chronic coronary syndromes" \
  --index-path /prj/doctoral_letters/guide/data/grounding_index_docling_table_000.json \
  --rules-out-path /prj/doctoral_letters/guide/data/extracted_rules_docling_table_000.jsonl \
  --node g5 \
  --model Qwen30b
```
- [SOURCE_TYPE: text]
- In patients with symptomatic HFrEF and LVEF ≤ 40%, an ACE-Inhibitor is recommended (Class I, Level A) to reduce mortality. However, in patients with a history of Angioedema, ACE-Inhibitors are contraindicated.

**Step 2 — LLM extracts concepts and logic**
- entity_original: "HFrEF"
  - entity_standardized_candidate: "heart failure with reduced ejection fraction"
  - role: Condition
- entity_original: "LVEF"
  - entity_standardized_candidate: "left ventricular ejection fraction"
  - role: ClinicalParameter
  - logic_structured: {"operator": "<=", "value": 40, "unit": "%"}
- entity_original: "ACE-Inhibitor"
  - entity_standardized_candidate: "angiotensin-converting enzyme inhibitor"
  - role: Medication
- entity_original: "Angioedema"
  - entity_standardized_candidate: "angioedema"
  - role: Condition
- rule_id: <unique rule id>
  - logic: "HFrEF AND LVEF <= 40% => recommend ACE-Inhibitor (Class I, Level A)"
  - logic_structured: {"type": "RECOMMENDATION", "class": "I", "level": "A"}
- rule_id: <unique rule id>
  - logic: "History of angioedema => contraindicate ACE-Inhibitor"
  - logic_structured: {"type": "CONTRAINDICATION", "class": "III"}

**Step 3 — Abbreviation expansion and SNOMED search**
- "HFrEF" expands to "heart failure with reduced ejection fraction" for SNOMED search.
- "LVEF" expands to "left ventricular ejection fraction" for SNOMED search.
- "ACE-Inhibitor" expands to "angiotensin-converting enzyme inhibitor" for SNOMED search.
- "Angioedema" is searched directly for SNOMED grounding.

**Step 4 — Outputs written**
- grounding_index.json (concepts grounded as usual)
- extracted_rules.jsonl (rules emitted with references to grounded concepts)

**Mermaid graph (logic + semantics)**

```mermaid
graph TD
    %% --- STYLING ---
    classDef semantic fill:#e1f5fe,stroke:#01579b,stroke-width:2px,color:black;
    classDef parameter fill:#e0f2f1,stroke:#00695c,stroke-width:2px,color:black;
    classDef decision fill:#fff9c4,stroke:#fbc02d,stroke-width:2px,shape:rhombus,color:black;
    classDef recommendation fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px,shape:rect,color:black;
    classDef contraindication fill:#ffcdd2,stroke:#c62828,stroke-width:2px,shape:rect,color:black;
    classDef med fill:#d1c4e9,stroke:#512da8,stroke-width:2px,shape:ellipse,color:black;

    %% --- SEMANTIC LAYER (SNOMED ANCHORS) ---
    S_HFrEF[("HFrEF
    (SNOMED: 703272007)")]:::semantic
    
    S_LVEF[("LVEF
    (SNOMED: 250908004)")]:::parameter
    
    S_Angio[("Angioedema
    (SNOMED: 41291007)")]:::semantic
    
    S_ACE[("ACE Inhibitor
    (SNOMED: 41549008)")]:::med

    %% --- LOGIC LAYER (GUIDELINE RULES) ---
    
    %% Path 1: The Indication (AND Logic via Sequence)
    D_HasHFrEF{{"Check:
    Is Condition Present?"}}:::decision
    
    D_LVEFCheck{{"Check:
    Is LVEF ≤ 40%?"}}:::decision
    
    R_GiveACE["RECOMMENDATION
    Class: I, Level: A
    Type: PRESCRIPTION"]:::recommendation

    %% Path 2: The Contraindication
    D_HasAngio{{"Check:
    Is Condition Present?"}}:::decision
    
    R_NoACE["CONTRAINDICATION
    Class: III
    Type: DO_NOT_USE"]:::contraindication

    %% --- CONNECTIONS ---

    %% 1. Linking Decisions to Semantics (EVALUATES / CHECKS_FOR)
    D_HasHFrEF -->|CHECKS_FOR| S_HFrEF
    D_LVEFCheck -->|EVALUATES| S_LVEF
    D_HasAngio -->|CHECKS_FOR| S_Angio

    %% 2. The Indication Flow (AND Logic)
    %% Start bei HFrEF -> Wenn JA, pruefe LVEF -> Wenn JA, Empfehlung
    D_HasHFrEF -->|Outcome: YES| D_LVEFCheck
    D_LVEFCheck -->|Outcome: YES| R_GiveACE
    
    %% 3. The Contraindication Flow
    D_HasAngio -->|Outcome: YES| R_NoACE

    %% 4. Action Mapping (Targeting the Drug)
    R_GiveACE -->|RECOMMENDS_USAGE| S_ACE
    R_NoACE -->|CONTRAINDICATES| S_ACE

    %% Optional: Show parallelism
    subgraph Guideline_Logic [Guideline Logic Layer]
        direction TB
        D_HasHFrEF
        D_LVEFCheck
        D_HasAngio
        R_GiveACE
        R_NoACE
    end
```

## Mermaid flow chart (full workflow)

```mermaid
flowchart TD
  A[Raw guideline PDFs] --> B[Parse to text and markdown]
  B --> C[Extract structures and tables]
  C --> D[Chunk markdown into text chunks]
  C --> E[Chunk markdown into table chunks]

  D --> F[Tag chunks with GUIDELINE and SOURCE_TYPE]
  E --> F

  F --> G[LLM concept extraction]
  G --> H{Concept list}

  H --> I[Normalize standardized term]
  I --> J[Abbreviation expansion using abbrv.txt]
  J --> K[SNOMED term search]

  K --> L[Score best concept match]
  L --> M{Score >= threshold?}
  M -- No --> N[Skip noisy/low-score concept]
  M -- Yes --> O[Extract SNOMED taxonomy path]

  O --> P[Resolve target_label from schema]
  P --> Q{Target label found?}
  Q -- No and role unknown --> N
  Q -- Yes --> R[Create GroundedConcept]

  R --> S[Write to grounding_index.json]
  S --> T[Cache by SNOMED ID and standardized term]

  T --> U[Repeat for all chunks and tables]
  U --> V[Final grounded index ready for downstream graph ingestion]
```

## Notes and key configuration

- SNOMED mapping rules: /home/pwiesenbach/CardioGuidelinesGraph/src/cardio_graph/snomedct_utils/guideline_graph_schema.yaml
- Abbreviation list: /home/pwiesenbach/CardioGuidelinesGraph/src/cardio_graph/snomedct_utils/abbrv.txt
- LLM model aliases: /home/pwiesenbach/CardioGuidelinesGraph/src/cardio_graph/extraction_utils/clients.py
- Grounding service: /home/pwiesenbach/CardioGuidelinesGraph/src/cardio_graph/extraction_utils/entity_grounding_service_new.py
