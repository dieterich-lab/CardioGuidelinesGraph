# Cardio Subset from SNOMED: Exact Build Procedure

This document describes exactly how the cardiology SNOMED subset was established in this repository.

## Scope

This is the build process for the two subset artifacts:
- /prj/doctoral_letters/guide/data/ontologies/cardio_subset_concept_ids.json
- /prj/doctoral_letters/guide/data/ontologies/cardio_subset_candidates.json

Source-of-truth implementation:
- src/cardio_graph_core/snomedct/generate_cardio_ontology.py
- slurm/generate-cardio-subset.sbatch
- config/cardio_graph_core/ontology_config.yaml
- docs/experiments/grounding/cardio_subset_tuning.md

## Established Baseline (Current)

The currently established subset was built with:
- seed_mode = both
- expand_parent_depth = 0
- expand_child_depth = 1
- limit_per_term = 500
- global_limit = 20000

Rationale and run log are tracked in:
- docs/experiments/grounding/cardio_subset_tuning.md

Important interpretation:
- The subset is not leaf-only.
- The subset is not a single fixed ontology level.
- It is a mixed-hierarchy set: seed concepts plus one child expansion layer, with no parent expansion in the current baseline.

## Exact Input Sources

## 1. Lexical seed terms
Loaded from:
- config/cardio_graph_core/ontology_config.yaml

Field:
- cardiovascular_search_terms

## 2. Gold seed files
Loaded from:
- config/cardio_graph_core/ontology_config.yaml (gold_seed_paths)
- optionally overridden with repeated --gold-path arguments

Current default GT sources:
- /prj/doctoral_letters/guide/data/evaluation/table_22_manual_1.3.json
- /prj/doctoral_letters/guide/data/evaluation/table_17_manual_1.3.json
- /prj/doctoral_letters/guide/data/evaluation/table_8_manual_1.4.json

Gold ID extraction logic:
- Walk nested JSON recursively.
- Any key containing snomed (case-insensitive) is treated as a candidate SNOMED field.
- Numeric SNOMED-like values are coerced to integer concept IDs and included in the gold seed set.

## Exact Algorithm (Execution Order)

## Step 1: Build seed IDs from term search
For each configured search term, query SNOMED description/concept tables:

- Match: description.term ILIKE %search_term%
- Constraints: description.active = true and concept.active = true
- Select: DISTINCT conceptid
- Per-term cap: limit_per_term
- Global cap: global_limit across all terms

This yields:
- term_seed_ids
- matched_search_terms per concept

## Step 2: Build seed IDs from gold annotations
Collect SNOMED IDs from GT JSON files as described above.

This yields:
- gold_ids

## Step 3: Merge seed sources by seed_mode
- terms: use only term_seed_ids
- gold: use only gold_ids
- both: union(term_seed_ids, gold_ids)

Source tags applied:
- seed_terms for lexical seeds
- seed_gold for GT seeds

## Step 4: Expand through IS_A graph
Expansion uses SNOMED relationship type:
- IS_A typeid = 116680003

Parent expansion query direction:
- from sourceid in frontier, read destinationid as parents

Child expansion query direction:
- from destinationid in frontier, read sourceid as children

Depth behavior:
- parent expansion from depth 1..expand_parent_depth
- child expansion from depth 1..expand_child_depth

Current established baseline:
- expand_parent_depth = 0
- expand_child_depth = 1

Tagging during expansion:
- expand_parent_dN for parent-derived concepts
- expand_child_dN for child-derived concepts

After iterative expansion, direct parent/child adjacency is enriched for all selected concept IDs.

## Step 5: Build concept metadata for candidates artifact
For each selected concept ID:
- fetch descriptions
- fetch preferred term
- detect FSN
- collect synonym terms (excluding duplicate/preferred duplicates)
- parse semantic_tag from trailing parenthetical of FSN or preferred term
- include source tags and IS_A adjacency lists

Grounding-relevant fields are explicitly written in the candidates payload.

## Step 6: Compute gold coverage
Coverage is computed against gold_ids:
- covered = selected_ids intersection gold_ids
- missing = gold_ids minus selected_ids
- coverage ratio = covered / gold_total

## Step 7: Write output artifacts
Two JSON files are written:

## A. subset_concept_ids
Contains:
- generated_at
- config_path
- seed_mode
- seed_terms_count
- seed_gold_count
- expand_parent_depth
- expand_child_depth
- count
- concept_ids
- gold_coverage
- gold_paths

## B. subset_candidates
Contains:
- generated_at
- config_path
- seed_mode
- count
- items (rich concept metadata)
- notes.grounding_relevant_fields

## Exact Run Path in This Repository

Primary launcher:
- slurm/generate-cardio-subset.sbatch

That launcher executes:
- poetry run generate-cardio-subset with env-configurable arguments

Defaults in launcher:
- CONFIG_PATH=/home/pwiesenbach/CardioGuidelinesGraph/config/cardio_graph_core/ontology_config.yaml
- SUBSET_IDS_OUT=/prj/doctoral_letters/guide/data/ontologies/cardio_subset_concept_ids.json
- SUBSET_CANDIDATES_OUT=/prj/doctoral_letters/guide/data/ontologies/cardio_subset_candidates.json
- LIMIT_PER_TERM=500
- GLOBAL_LIMIT=20000
- SEED_MODE=both
- EXPAND_PARENT_DEPTH=0
- EXPAND_CHILD_DEPTH=1

## Reproduction Commands

Run through Slurm with established baseline:

```bash
cd /home/pwiesenbach/CardioGuidelinesGraph
sbatch slurm/generate-cardio-subset.sbatch
```

Run with explicit overrides (equivalent values):

```bash
cd /home/pwiesenbach/CardioGuidelinesGraph
SEED_MODE=both \
EXPAND_PARENT_DEPTH=0 \
EXPAND_CHILD_DEPTH=1 \
LIMIT_PER_TERM=500 \
GLOBAL_LIMIT=20000 \
sbatch slurm/generate-cardio-subset.sbatch
```

Run directly without Slurm:

```bash
cd /home/pwiesenbach/CardioGuidelinesGraph
poetry run generate-cardio-subset \
  --config-path /home/pwiesenbach/CardioGuidelinesGraph/config/cardio_graph_core/ontology_config.yaml \
  --seed-mode both \
  --expand-parent-depth 0 \
  --expand-child-depth 1 \
  --limit-per-term 500 \
  --global-limit 20000 \
  --subset-concept-ids-out /prj/doctoral_letters/guide/data/ontologies/cardio_subset_concept_ids.json \
  --subset-candidates-out /prj/doctoral_letters/guide/data/ontologies/cardio_subset_candidates.json
```

## Verification Checklist

After generation, verify:
- Job log reports generation complete.
- Both output files exist and are non-empty.
- subset_concept_ids JSON reports:
  - seed_mode = both
  - expand_parent_depth = 0
  - expand_child_depth = 1
- gold_coverage.coverage is acceptable for the current cycle target (see tuning tracker).

Historical reference run (from tracker):
- 2026-04-10, job 629771, subset size 19218, GT coverage 69/69.

## Measured GT ID Presence in Vector DB Scope

Measurement date:
- 2026-04-20

Definition used for this check:
- Vector DB scope is the subset concept ID list used by vector ingest via --subset-concept-ids-path.
- Scope file: /prj/doctoral_letters/guide/data/ontologies/cardio_subset_concept_ids.json

GT sources measured:
- /prj/doctoral_letters/guide/data/evaluation/table_22_manual_1.3.json
- /prj/doctoral_letters/guide/data/evaluation/table_17_manual_1.3.json
- /prj/doctoral_letters/guide/data/evaluation/table_8_manual_1.4.json

Extraction method:
- Same recursive SNOMED-ID extraction rule as the subset generator: traverse nested JSON, read keys containing snomed, coerce numeric SNOMED-like values to integer concept IDs.

Results:
- Subset concept IDs available for ingest: 19218
- Table 22 GT IDs: 43 total, 43 in vector DB scope, 0 missing, 100.00% coverage
- Table 17 GT IDs: 30 total, 30 in vector DB scope, 0 missing, 100.00% coverage
- Table 8 GT IDs: 13 total, 13 in vector DB scope, 0 missing, 100.00% coverage
- Union across all three tables: 70 unique GT IDs total, 70 in vector DB scope, 0 missing, 100.00% coverage

Interpretation:
- For the current subset artifact, there is no GT concept-ID loss in the SNOMED -> Subset step for the three measured tables.
- This supports the claim that current mapping performance is not limited by overly strict pre-emptive filtering at the concept-ID scope stage.

## Relationship to Vector Ingest

Subset generation is upstream.
When vector ingest is run with --subset-concept-ids-path, only those concept IDs are ingested for embedding/index construction.

Therefore, the hierarchy policy for grounding index scope is determined here (seed composition + expansion depths).
