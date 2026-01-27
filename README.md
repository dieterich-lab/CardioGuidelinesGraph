

# CardioGuidelinesGraph

<div align="center">
<b>Comprehensive Knowledge Graph Construction and Reasoning for Cardiovascular Guidelines</b><br>
<i>Integrating SNOMED CT, logic, and LLMs for patient-centric clinical decision support</i>
</div>

---

## 🚀 Project Vision

CardioGuidelinesGraph is a research-driven framework to transform cardiovascular guidelines into a computable, queryable, and explainable knowledge graph. It enables:
- **Semantic interoperability** via SNOMED CT integration
- **Logic-aware reasoning** for complex clinical recommendations
- **Patient-specific question answering** and evidence tracing
- **Rapid extension** to new guidelines, domains, and research questions

<details>
<summary><b>Why is this important?</b></summary>

Clinical guidelines are the backbone of evidence-based medicine, but their logic is often buried in prose and tables. CardioGuidelinesGraph makes this knowledge explicit, computable, and accessible for both humans and machines.
</details>

---

---


## 1. High-Level Pipeline

```mermaid
flowchart TD
	A[Guideline Documents (PDF/Markdown)] --> B[Parsing & Chunking]
	B --> C[Statement Extraction & Logic Mapping]
	C --> D[Entity Grounding (NER + SNOMED CT)]
	D --> E[Ontology Construction (OWL/RDF)]
	E --> F[Knowledge Graph Construction (Neo4j)]
	F --> G[Querying & Reasoning]
	G --> H[Patient-Specific Answers & Evidence]
```

---

---


## 2. Architecture & Main Components


### Ontology & Entity Grounding
- <b>Ontology Generator</b> ([snomedct_utils/generate_cardio_ontology.py](src/cardio_graph/snomedct_utils/generate_cardio_ontology.py)): Extracts cardiovascular concepts from SNOMED CT, categorizes them (using LLMs), and builds an OWL ontology.
- <b>Entity Grounding Service</b> ([extraction_utils/entity_grounding_service.py](src/cardio_graph/extraction_utils/entity_grounding_service.py)): Links text mentions to ontology classes using spaCy NER and a Whoosh-based search index.

### Knowledge Extraction & Graph Construction
- <b>Markdown/PDF Parsing</b> ([parsing_utils/](src/cardio_graph/parsing_utils/)): Extracts structured statements and tables from guideline documents.
- <b>Statement Extraction & Embedding</b> ([extraction_utils/](src/cardio_graph/extraction_utils/)): Converts parsed text into logical statements, embeds them, and prepares them for graph construction.
- <b>Graph Construction</b> ([extraction_utils/new_graph_construction.py](src/cardio_graph/extraction_utils/new_graph_construction.py)): Builds the Neo4j knowledge graph, representing statements, entities, and logical junctions.

### Querying & Reasoning
- <b>Query Interpreter</b> ([extraction_utils/query_interpreter.py](src/cardio_graph/extraction_utils/query_interpreter.py)): Accepts natural language or structured queries, extracts relevant subgraphs, and resolves logical junctions to answer clinical questions.
- <b>Logic Handling</b> ([extraction_utils/query_copy.py](src/cardio_graph/extraction_utils/query_copy.py)): Implements logic for traversing AND/OR/NOT nodes and extracting relevant evidence paths.

### Integration & RAG
- <b>RAG Utilities</b> ([rag_utils/](src/cardio_graph/rag_utils/)): Supports retrieval-augmented generation and embedding-based search over the KG.
- <b>Neo4j Utilities</b> ([neo4j_utils/](src/cardio_graph/neo4j_utils/)): Handles Cypher generation, database feeding, and graph utilities.

---


## 3. Detailed Pipeline

```mermaid
flowchart TD
  A1[Load ontology_config.yaml] --> A2[Connect to SNOMED CT DB]
  A2 --> A3[Extract concepts using search terms]
  A3 --> A4[LLM-based categorization]
  A4 --> A5[Build OWL/RDF ontology]
  A5 --> B3
  B1[Parse guidelines (PDF/MD)] --> B2[Extract statements/tables]
  B2 --> B3[Ground entities to ontology]
  B3 --> B4[Map logic (AND/OR/NOT)]
  B4 --> B5[Build Neo4j graph]
  B5 --> C2
  C1[User/system query] --> C2[Subgraph extraction]
  C2 --> C3[Logic resolution]
  C3 --> C4[Answer + evidence]
```

---

---


## 4. Example Use Cases & Research Scenarios


- **Patient-Specific Recommendations**: “Should a patient with HFrEF and diabetes receive a beta blocker?”
- **Guideline Comparison**: “What are the differences in antiplatelet therapy recommendations between ESC and ACC/AHA guidelines?”
- **Evidence Tracing**: “Show all evidence supporting CABG in patients with left main disease.”
- **Logic Pathways**: “What logical conditions must be met for PCI to be recommended in NSTEMI?”
- **Ontology Auditing**: “Which SNOMED CT concepts are not mapped to any core class?”

---


## 5. File & Module Structure

- `src/cardio_graph/snomedct_utils/`: Ontology generation, SNOMED CT integration.
- `src/cardio_graph/extraction_utils/`: Entity grounding, statement extraction, graph construction, querying.
- `src/cardio_graph/parsing_utils/`: Markdown/PDF parsing.
- `src/cardio_graph/neo4j_utils/`: Neo4j database utilities.
- `src/cardio_graph/rag_utils/`: Retrieval-augmented generation and embedding search.

---


## 6. Getting Started

This project uses Poetry for dependency management. Before using any scripts, set up your environment:

```bash
# Install project with dependencies
poetry install

# Activate the virtual environment
poetry shell

# Download the spaCy model for Named Entity Recognition
poetry run python -m spacy download en_core_web_sm

# Download the scispaCy biomedical models for sentence splitting and entity grounding
poetry run pip install https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.5.4/en_core_sci_lg-0.5.4.tar.gz
poetry run pip install https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.5.4/en_ner_bc5cdr_md-0.5.4.tar.gz
```

---


## 7. Advanced Topics & Extensibility

- **Extending the Ontology**: Add new classes or properties in `ontology_config.yaml`.
- **Custom Query Logic**: Implement new logic in `query_copy.py` or `query_interpreter.py`.
- **Integration with LLMs**: Use BAML and Ollama for advanced categorization and reasoning.

---


## 8. Glossary & References

**Glossary**

- **Ontology**: A formal representation of knowledge as a set of concepts and relationships.
- **SNOMED CT**: A comprehensive clinical terminology standard for health data.
- **Entity Grounding**: Linking text mentions to canonical ontology concepts.
- **Logic Junctions**: Logical operators (AND/OR/NOT) used to combine clinical statements.
- **RAG (Retrieval-Augmented Generation)**: Combining retrieval from a knowledge base with generative models for answering queries.
- **Neo4j**: A graph database platform used for storing and querying the knowledge graph.

---


- See the submodule READMEs (e.g., [`src/cardio_graph/snomedct_utils/README.md`](src/cardio_graph/snomedct_utils/README.md)) for detailed documentation on ontology generation and SNOMED CT integration.
- Example queries and advanced usage: see [`src/cardio_graph/extraction_utils/query_interpreter.py`](src/cardio_graph/extraction_utils/query_interpreter.py) and [`src/cardio_graph/extraction_utils/query_copy.py`](src/cardio_graph/extraction_utils/query_copy.py).

---

## 9. How to Contribute

We welcome contributions from the research and clinical informatics community! Please:
- Open issues for bugs, feature requests, or questions
- Submit pull requests for improvements or new modules
- Add tests and documentation for new features

---

<div align="center">
<b>CardioGuidelinesGraph: Making Clinical Knowledge Computable</b>
</div>