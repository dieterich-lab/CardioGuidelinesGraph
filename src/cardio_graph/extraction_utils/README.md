# Guideline parsing and grounding workflow

This folder contains the parsing, extraction, and grounding pipeline used to turn guideline documents into a SNOMED-backed concept index. The process is deterministic except for the LLM extraction step. This README documents the full workflow, intermediate artifacts, and how to run the pipeline end-to-end.

## Overview

**Goal:** Convert guideline PDFs/markdown into structured text chunks and tables, extract clinical concepts, ground them to SNOMED CT, and build a reusable JSON index.

**Primary outputs:**
- Grounding index: /prj/doctoral_letters/guide/data/grounding_index.json
- Timestamped snapshots: /prj/doctoral_letters/guide/data/grounding_index_YYYYMMDD_HHMMSS.json
- Extracted rules: /prj/doctoral_letters/guide/data/extracted_rules.jsonl
- Chunked guideline text: /prj/doctoral_letters/guide/data/guidelines/markdown/chunks
- Chunked tables: /prj/doctoral_letters/guide/data/guidelines/markdown/chunks/tables

**Why split grounding_index vs extracted_rules?**
- grounding_index.json is the stable SNOMED-backed dictionary for concepts (used across runs and for Neo4j concept nodes).
- extracted_rules.jsonl is the per-chunk, per-mention output that preserves logic and provenance (used to create decision/recommendation nodes and edges).
- This split keeps the reusable concept cache small and deterministic while allowing rule-level logic to evolve independently.

## Intermediate steps and files

1) **Collect guideline PDFs**
- Input: /prj/doctoral_letters/guide/data/guidelines/pdf

2) **Parse PDFs to text / markdown**
- Script: /home/pwiesenbach/CardioGuidelinesGraph/slurm/parse_guidelines_to_text.sh
- Output (examples):
  - /prj/doctoral_letters/guide/data/guidelines/text
  - /prj/doctoral_letters/guide/data/guidelines/markdown

3) **Extract tables and structures**
- Script: /home/pwiesenbach/CardioGuidelinesGraph/slurm/parse_markdown_tables_to_structures.sh
- Script: /home/pwiesenbach/CardioGuidelinesGraph/slurm/parse_structures_from_pdf.sh
- Output:
  - /prj/doctoral_letters/guide/data/guidelines/structures

4) **Chunk guideline markdown into manageable pieces**
- Module: markdown_chunks.py
- Output:
  - /prj/doctoral_letters/guide/data/guidelines/markdown/chunks
  - /prj/doctoral_letters/guide/data/guidelines/markdown/chunks/tables

5) **LLM concept extraction (tagged) + SNOMED grounding**
- Module: entity_grounding_service_new.py
- BAML prompt: /home/pwiesenbach/CardioGuidelinesGraph/src/cardio_graph/baml_src/extract_concepts.baml
- SNOMED schema mapping: /home/pwiesenbach/CardioGuidelinesGraph/src/cardio_graph/snomedct_utils/guideline_graph_schema.yaml
- Abbreviation expansion: /home/pwiesenbach/CardioGuidelinesGraph/src/cardio_graph/snomedct_utils/abbrv.txt

6) **Index creation and caching**
- Output index: /prj/doctoral_letters/guide/data/grounding_index.json
- Output rules (JSONL): /prj/doctoral_letters/guide/data/extracted_rules.jsonl
- The index is keyed by both SNOMED ID and normalized standardized term.
- Noisy lines are filtered prior to extraction, and low-score matches are skipped.

## Example: build the full grounding index

Use the SLURM wrapper:
- /home/pwiesenbach/CardioGuidelinesGraph/slurm/grounding_full_index.sh

Direct run (no SLURM):
- poetry run python /home/pwiesenbach/CardioGuidelinesGraph/src/cardio_graph/extraction_utils/entity_grounding_service_new.py \
  --chunks-dir /prj/doctoral_letters/guide/data/guidelines/markdown/chunks \
  --tables-dir /prj/doctoral_letters/guide/data/guidelines/markdown/chunks/tables \
  --guideline-title "2024 ESC Guidelines for the management of chronic coronary syndromes" \
  --model Qwen17b

Single-sentence example:
- poetry run python /home/pwiesenbach/CardioGuidelinesGraph/src/cardio_graph/extraction_utils/entity_grounding_service_new.py \
  --sentence "MACE was reduced with ACE-I in patients with CAD." \
  --guideline-title "2024 ESC Guidelines for the management of chronic coronary syndromes" \
  --model Qwen17b

## Detailed workflow description

1) **Parse guideline files**
- PDF and markdown are created from raw guideline sources. This step produces cleaned text, sections, and tables.

2) **Chunking**
- Long markdown is segmented into paragraph chunks and table chunks to keep LLM extraction stable and to track provenance.

3) **Tagged extraction**
- Each chunk is wrapped with tags:
  - [GUIDELINE: <title>]
  - [SOURCE_TYPE: text|table]
- The LLM (BAML) extracts:
  - `entity_original`
  - `entity_standardized_candidate`
  - `role` (Condition/Medication/Procedure/ClinicalParameter)
  - `logic` and `logic_structured`

4) **Abbreviation expansion**
- Terms are expanded using abbrv.txt (e.g., MACE ↔ major adverse cardiovascular events) during SNOMED search.

5) **SNOMED search and scoring**
- Candidate terms are searched in the SNOMED database.
- The best match is selected by normalized string similarity score.
- Matches below the threshold are skipped.

6) **Taxonomy path and target label**
- The SNOMED is-a path is traversed to a configured root.
- The path determines the `target_label` (ClinicalCondition, Medication, Procedure, ClinicalParameter).

7) **Index write-through**
- Results are saved to grounding_index.json (by SNOMED ID and standardized term).
- Extracted rules are saved to extracted_rules.jsonl (one rule per line, if present in the chunk).
- Subsequent runs reuse cached matches for speed and consistency.

## Upload into Neo4j (concepts + optional rules)

- Loader script: /home/pwiesenbach/CardioGuidelinesGraph/src/cardio_graph/neo4j_utils/grounding_index_to_neo4j.py
- SLURM wrapper: /home/pwiesenbach/CardioGuidelinesGraph/slurm/load_grounding_index_to_neo4j.sh

The loader ingests grounding_index.json as concept nodes, and if extracted_rules.jsonl is present it adds decision/recommendation nodes plus rule edges. By default it targets the Neo4j URI configured in feedneo4jdb.py.

## Example: one sentence to index entry

**Input sentence:**
- "MACE was reduced with ACE-I in patients with CAD."

**Step 1 — Tagged input passed to the LLM**
- [GUIDELINE: 2024 ESC Guidelines for the management of chronic coronary syndromes]
- [SOURCE_TYPE: text]
- MACE was reduced with ACE-I in patients with CAD.

**Step 2 — LLM extracts concepts**
- entity_original: "MACE"
  - entity_standardized_candidate: "major adverse cardiovascular events"
  - role: ClinicalParameter
- entity_original: "ACE-I"
  - entity_standardized_candidate: "angiotensin-converting enzyme inhibitor"
  - role: Medication
- entity_original: "CAD"
  - entity_standardized_candidate: "coronary artery disease"
  - role: Condition

**Step 3 — Abbreviation expansion and SNOMED search**
- "MACE" expands to "major adverse cardiovascular events" for SNOMED search.
- "ACE-I" expands to "angiotensin-converting enzyme inhibitor" for SNOMED search.
- "CAD" expands to "coronary artery disease" for SNOMED search.

**Step 4 — Example grounded entries written to the index (all three terms)**

- grounding_index.json (by standardized term):
  - entity_standardized_candidate: "major adverse cardiovascular events"
  - snomed_id: <resolved SNOMED concept id>
  - preferred_term: <SNOMED preferred term>
  - score: <similarity score>
  - taxonomy_path: [{"concept_id": "...", "term": "..."}, ...]
  - target_label: ClinicalParameter
  - role: ClinicalParameter

- grounding_index.json (by standardized term):
  - entity_standardized_candidate: "angiotensin-converting enzyme inhibitor"
  - snomed_id: <resolved SNOMED concept id>
  - preferred_term: <SNOMED preferred term>
  - score: <similarity score>
  - taxonomy_path: [{"concept_id": "...", "term": "..."}, ...]
  - target_label: Medication
  - role: Medication

- grounding_index.json (by standardized term):
  - entity_standardized_candidate: "coronary artery disease"
  - snomed_id: <resolved SNOMED concept id>
  - preferred_term: <SNOMED preferred term>
  - score: <similarity score>
  - taxonomy_path: [{"concept_id": "...", "term": "..."}, ...]
  - target_label: ClinicalCondition
  - role: Condition

**Impact summary for the three terms**

- MACE → standardized to "major adverse cardiovascular events" and grounded as a ClinicalParameter.
- ACE-I → standardized to "angiotensin-converting enzyme inhibitor" and grounded as a Medication.
- CAD → standardized to "coronary artery disease" and grounded as a ClinicalCondition.

**Mini graph (example triples)**

Below is a minimal graph that links grounded entities using only relations explicitly stated in the same chunk. In this sentence, the only relation supported by the text is the reduction of MACE with ACE-I.

- Asserted triple (within-chunk): (angiotensin-converting enzyme inhibitor) --reducesRiskOf--> (major adverse cardiovascular events)

**Mini graph (Mermaid view)**

```mermaid
graph LR
  CAD["Coronary artery disease\n(ClinicalCondition)"]
  MACE["Major adverse cardiovascular events\n(ClinicalParameter)"]
  ACEI["ACE inhibitor\n(Medication)"]

  ACEI -- reducesRiskOf --> MACE
```

## Example: complex recommendation + contraindication

**Input sentence:**
- "In patients with symptomatic HFrEF and LVEF ≤ 40%, an ACE-Inhibitor is recommended (Class I, Level A) to reduce mortality. However, in patients with a history of Angioedema, ACE-Inhibitors are contraindicated."

**Step 1 — Tagged input passed to the LLM**
- [GUIDELINE: 2024 ESC Guidelines for the management of chronic coronary syndromes]
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

    %% 1. Linking Semantics to Decisions (EVALUATES / CHECKS_FOR)
    S_HFrEF ---|CHECKS_FOR| D_HasHFrEF
    S_LVEF ---|EVALUATES| D_LVEFCheck
    S_Angio ---|CHECKS_FOR| D_HasAngio

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
