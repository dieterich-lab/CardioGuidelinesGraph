# Neo4j Grounding & Graph Loading

This folder contains the Neo4j-facing scripts used after extraction/grounding to:

1. load grounded concepts and rule structures into the graph,
2. load generated Cypher files directly,
3. build a vector-searchable SNOMED term index for semantic candidate retrieval.

The three scripts are:

- `feedneo4jdb.py`
- `grounding_index_to_neo4j.py`
- `snomed_vector_ingest.py`


## Neo4j instance map (current)

Use this quick mapping to avoid mixing environments:

- `bolt://neo4j-dev3.internal:7687`
   - SNOMED keyword/vector index (semantic candidate retrieval).
   - Used by vector grounding/evaluation and SNOMED embedding ingest.

- `bolt://neo4j-dev2.internal:7687`
   - Manual ground-truth rules graph from the 3 benchmark tables (`table_8_manual_1.3`, `table_17_manual_1.3`, `table_22_manual_1.3`).
   - Validation evidence exists in `docs/dev2_ground_truth_sanity_report.json`.

- `bolt://neo4j-dev4.internal:7687`
   - Automatically generated rules graph (graph builder / graph loading target).
   - Default target used by `feedneo4jdb.py`.

If in doubt, treat dev2 as manual benchmark truth, dev3 as vector retrieval infrastructure, and dev4 as the generated KG target.


## Secrets setup (recommended)

Do not store Neo4j passwords in source files.

Preferred approach:

1. Create a local-only secrets file:

   - `mkdir -p ~/.config/cardio_graph`
   - `chmod 700 ~/.config/cardio_graph`
   - `cat > ~/.config/cardio_graph/secrets.env <<'EOF'`
   - `CARDIO_GRAPH_NEO4J_URI=bolt://neo4j-dev4.internal:7687`
   - `CARDIO_GRAPH_NEO4J_USER=neo4j`
   - `CARDIO_GRAPH_NEO4J_PASSWORD=<your_password_here>`
   - `EOF`
   - `chmod 600 ~/.config/cardio_graph/secrets.env`

2. Run scripts normally. `feedneo4jdb.py` will auto-load this file.

Supported password env vars (priority order in `feedneo4jdb.py`):

- `CARDIO_GRAPH_NEO4J_PASSWORD` (preferred)
- `NEO4J_PASSWORD`
- `CARDIO_GRAPH_GROUNDING_PASSWORD`

Optional override for the secrets file path:

- `CARDIO_GRAPH_SECRETS_ENV_PATH=/custom/path/secrets.env`


## Big picture: how grounding works end-to-end

Grounding is split into two layers:

1. **Candidate generation + matching in extraction**
   - Implemented in `src/cardio_graph_core/extraction/guideline_graph_builder.py`.
   - Produces grounded concepts with fields like `snomed_id`, `preferred_term`, `target_label`, `taxonomy_path`.
   - Uses lexical matching and (optionally) vector-assisted candidate retrieval.

2. **Graph persistence and indexing in Neo4j**
   - Scripts in this directory load the grounded artifacts into Neo4j and optionally prepare vector index nodes.

So the extraction layer decides *what* each concept maps to; Neo4j scripts decide *how* to store and query those mappings efficiently.


## Script 1: `feedneo4jdb.py`

### Purpose
Simple bulk executor for existing Cypher files.

### Input
- Directory with `*_cypher.txt` files (`CYPHER_DIR`).

### What it does
- Connects to Neo4j (`URI`, `AUTH`).
- Iterates over Cypher files.
- Removes comment lines and executes the remaining Cypher text as one query payload.

### When to use
- You already generated Cypher externally and just need to push it into Neo4j.
- Quick replay/reload of prepared graph operations.

### Notes
- It does not perform schema validation or domain-aware grouping; it is a direct executor.


## Script 2: `grounding_index_to_neo4j.py`

### Purpose
Canonical loader for grounded concepts (and optional rule logic) into Neo4j.

### Input
- Grounding index JSON (default: `/prj/doctoral_letters/guide/data/graph/grounding_index.json`).
- Optional rules JSON/JSONL from extraction.
- Graph schema YAML (for contract checks).

### What it does
1. Validates schema contract (required labels and relationship types).
2. Loads grounding entries and groups them by `target_label`.
3. `MERGE`s concept nodes (with `:Concept` plus domain labels).
4. Reconstructs taxonomy edges (`IS_A`) from `taxonomy_path`.
5. Optionally creates decision/recommendation/rule structure from extracted rules.

### Why this is important
- This is the persistence bridge between extraction outputs and the final queryable KG.
- It keeps concept identity anchored by `snomed_id` and preserves taxonomy lineage.


## Script 3: `snomed_vector_ingest.py`

### Purpose
Builds a vector-searchable SNOMED term store in Neo4j for semantic retrieval.

### Input
- SNOMED Postgres (`description` table via `SnomedExplorer`).
- Embedding model endpoint (Ollama).
- Neo4j target (dev3 in current workflow).

### What it does
1. Streams active SNOMED descriptions (optionally language-filtered).
2. Embeds term text in batches.
3. Upserts nodes (default label `SnomedTerm`) with embedding vectors.
4. Creates Neo4j vector index with configured dimension/similarity.
5. Logs throughput + ETA while ingesting.

### Why this exists
Lexical string matching alone misses many clinical paraphrases. A vector index allows semantic nearest-neighbor candidate retrieval against SNOMED terms.


## How these scripts fit together

Typical workflow:

1. **Build/refresh vector term index**
   - Run `snomed_vector_ingest.py` on Neo4j dev3.
   - This prepares semantic candidate retrieval infrastructure.

2. **Run extraction + grounding**
   - `guideline_graph_builder.py` extracts candidates from guideline text.
   - It performs lexical matching and can also query vector candidates.
   - It writes grounded outputs (`grounding_index.json`, rules, etc.).

3. **Load final grounded graph**
   - `grounding_index_to_neo4j.py` loads grounded concepts/rules into the main graph (e.g., dev4).

4. **Optional direct Cypher replay**
   - `feedneo4jdb.py` executes prepared Cypher dumps when needed.


## Important separation of concerns

- **Extraction/grounding logic lives in the builder** (`guideline_graph_builder.py`).
- **Neo4j scripts are persistence/indexing utilities**.

This keeps a single source of truth for mapping decisions while still letting Neo4j provide storage and fast retrieval.


## Practical notes for vector grounding

1. Query and index vectors must have **identical dimensions**.
   - Example: `qwen3-embedding` returns 4096-d vectors.
   - Neo4j vector index must be created with `vector.dimensions = 4096`.

2. You can start with a subset of SNOMED terms, but coverage improves when ingesting all active preferred/synonym-like descriptions.

3. Neo4j vector DB is sufficient for this project’s hybrid retrieval path; no external vector DB is strictly required.


## Operational recommendation

- Use **dev3** for vector index experiments and rebuilds.
- Keep **dev4** as the final graph target for grounded concept/rule graph loads.
- Promote index settings and retrieval weights only after measurable gains in grounding hit quality.
