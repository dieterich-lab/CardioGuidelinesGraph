# Guideline parsing and grounding workflow

This folder contains the parsing, extraction, and grounding pipeline used to turn guideline documents into a SNOMED-backed concept index. The process is deterministic except for the LLM extraction step. This README documents the full workflow, intermediate artifacts, and how to run the pipeline end-to-end.

## Overview

**Goal:** Convert guideline PDFs/markdown into structured text chunks and tables, extract clinical concepts, ground them to SNOMED CT, and build a reusable JSON index.

**Primary outputs:**
- Grounding index: /prj/doctoral_letters/guide/data/grounding_index.json
- Extracted rules: /prj/doctoral_letters/guide/data/extracted_rules.jsonl
- Chunked guideline text: /prj/doctoral_letters/guide/data/guidelines/markdown/chunks
- Chunked tables: /prj/doctoral_letters/guide/data/guidelines/markdown/chunks/tables

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
