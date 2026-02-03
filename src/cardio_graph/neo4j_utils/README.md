# Neo4j grounding loader

This folder contains Neo4j helpers. The main loader for the grounding index is:
- /home/pwiesenbach/CardioGuidelinesGraph/src/cardio_graph/neo4j_utils/grounding_index_to_neo4j.py

## What the loader does

The script populates Neo4j from the grounding index (static SNOMED identity) and, optionally, a rules file (dynamic rule logic). It is designed to avoid rule ID collisions and to preserve SNOMED taxonomy structure via `:IS_A` edges.

## Inputs

1. **Grounding index**
- Default: /prj/doctoral_letters/guide/data/grounding_index.json
- Expected structure: `by_snomed_id` with entries containing
  - `snomed_id` (string/int)
  - `preferred_term`
  - `entity_standardized_candidate`
  - `target_label` (ClinicalCondition, Medication, Procedure, ClinicalParameter, or null)
  - `taxonomy_path` (ordered list of `{concept_id, term}`)

2. **Rules file (optional)**
- JSON or JSONL with per-concept rule context from the extraction run.
- Expected fields per entry:
  - `rule_id`
  - `role` (Condition / ClinicalParameter / Medication / Procedure)
  - `logic_structured` (operator, threshold, unit, condition_context, strength, level, direction)
  - `chunk_id` or `source_id` or `source_context` (used to generate a unique rule key)
  - `snomed_id`, `entity_standardized_candidate`, `target_label`

If no rules file is provided, only concept nodes and taxonomy edges are created.

## How it works (step-by-step)

### 1) Load index
- `_load_grounding_index()` reads the JSON and extracts `by_snomed_id` values.
- `_group_by_label()` groups entries by `target_label` (falls back to `Concept`).

### 2) Merge concept nodes
For each label group, `_merge_concepts()` runs:
- `MERGE (n:Label {snomed_id: ...})`
- Sets `preferred_term`, `standardized`, `target_label`, and adds `:Concept`.

### 3) Build taxonomy hierarchy
Still inside `_merge_concepts()`, the script reads `taxonomy_path` for each entry and creates:
- Generic `:Concept` nodes for each parent if missing
- `(:Concept {child})-[:IS_A]->(:Concept {parent})`

This prevents a flat graph and allows ancestor queries (e.g., “all beta blockers” includes Bisoprolol).

### 4) Create rule logic nodes (optional)
If a rules file is supplied:
- The script groups entries by **unique rule key**: `chunk_id` (or `source_id`/`source_context`) + `rule_id`.
- This avoids collisions across chunks where `rule_id` restarts at 1.

`_create_rule_nodes()` then creates:
- `RecommendationNode` with `rule_unique_id`, plus `class`, `level`, `direction`, and `original_rule_id`.
- `DecisionNode` for Conditions/ClinicalParameters with operator/threshold/unit/context.
- Edges:
  - `(:Concept/ClinicalCondition)-[:HAS_RULE]->(:DecisionNode)`
  - `(:DecisionNode)-[:RESULTS_IN {condition_met:true}]->(:RecommendationNode)`
  - `(:RecommendationNode)-[:RECOMMENDS_USAGE|:CONTRAINDICATES_USAGE]->(:Medication|:Procedure)`

## Usage

- Default (concepts + hierarchy only):
  - `python grounding_index_to_neo4j.py`

- With rules:
  - `python grounding_index_to_neo4j.py --rules-path /path/to/rules.jsonl`

Override connection:
- `--uri`, `--user`, `--password`

## Key design choices

- **Static vs. dynamic data:** The grounding index stores static SNOMED identity. Rule logic is loaded separately to avoid context collisions.
- **Unique rule keys:** `chunk_id` + `rule_id` prevents cross-chunk merging of unrelated rules.
- **Hierarchy edges:** `taxonomy_path` is always applied to preserve SNOMED ancestry for graph queries.

## Common pitfalls

- Missing `taxonomy_path`: graph will be flat. Ensure the index has it.
- Missing `chunk_id` / `source_context`: rules will fall back to `global_<rule_id>` and can collide.
- Rules file must contain `snomed_id` + `target_label` to connect to concept nodes.
