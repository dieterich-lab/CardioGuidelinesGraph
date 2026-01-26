# CardioGuidelines Ontology Generator

This module generates a comprehensive cardiovascular ontology from SNOMED CT data for use in entity grounding within cardiovascular guidelines and doctoral letters.

## Overview

The ontology generation process creates a rich OWL/RDF ontology containing:
- **Core cardiovascular classes** (HeartDisease, Arrhythmia, Hypertension, etc.)
- **SNOMED CT-derived classes** (direct mappings from SNOMED concepts)
- **Hierarchical relationships** based on SNOMED CT "Is a" relationships
- **Cardiovascular-specific properties** for relationships and attributes

The resulting ontology enables entity grounding by providing classes that text mentions (like "HFrEF", "atrial fibrillation", "myocardial infarction") can be linked to.

## Architecture

### Key Components

1. **`ontology_config.yaml`** - Configuration file defining search terms, classes, and properties
2. **`generate_cardio_ontology.py`** - Main ontology generation script
3. **`snomed_query.py`** - SNOMED CT database interface
4. **`models.py`** - SQLAlchemy models for SNOMED CT database tables

## Detailed Ontology Generation Process

### Step 1: Configuration Loading

The process begins by loading `ontology_config.yaml`, which contains:

```yaml
# Broad search terms for extracting cardiovascular concepts from SNOMED CT
cardiovascular_search_terms:
  - "heart"
  - "cardiac"
  - "HFrEF"
  - "ejection fraction"
  # ... 65+ additional terms

# Core ontology schema (T-Box)
core_classes:
  - name: CardiovascularDisease
    description: Diseases affecting the heart and blood vessels.
  - name: HeartDisease
    description: Diseases of the heart.
    subclass_of: CardiovascularDisease
  # ... additional core classes

# Object properties (relationships)
core_properties:
  - name: hasRiskFactor
    domain: CardiovascularDisease
    range: CardiovascularRiskFactor
  # ... additional properties

# Data properties (attributes)
data_properties:
  - name: hasSeverity
    domain: CardiovascularDisease
    range: string
  # ... additional attributes
```

### Step 2: Database Connection

The generator connects to the SNOMED CT PostgreSQL database:

```python
self.snomed_explorer = SnomedExplorer(
    host="snomed-ct2.internal",
    port="5432",
    user="readonly",
    database="snomed",
    sslmode="verify-full"
)
```

### Step 3: Concept Extraction

For each search term in `cardiovascular_search_terms`, the system queries SNOMED CT:

```sql
-- Example query for term "heart"
SELECT DISTINCT c.id, c.term, c.active
FROM snap_concept c
JOIN snap_description d ON c.id = d.conceptid
WHERE d.term ILIKE '%heart%'
  AND d.active = 1
  AND c.active = 1
LIMIT 500
```

**Key Details:**
- Uses full-text search with ILIKE for case-insensitive matching
- Limits results per term to prevent overwhelming the database
- Deduplicates concepts by ID across all search terms
- Extracts ~1000 unique cardiovascular concepts

### Step 4: Ontology Schema Initialization

Creates the core ontology structure from `core_classes`, `core_properties`, and `data_properties`:

```python
# Initialize core classes
for class_entry in config["core_classes"]:
    class_uri = self.cgo[class_entry["name"]]
    self.g.add((class_uri, RDF.type, OWL.Class))
    self.g.add((class_uri, RDFS.label, Literal(class_entry["name"])))

# Initialize properties
for prop_entry in config["core_properties"]:
    prop_uri = self.cgo[prop_entry["name"]]
    self.g.add((prop_uri, RDF.type, OWL.ObjectProperty))
    # Add domain, range, labels, etc.
```

### Step 5: SNOMED Concept Class Creation

For each extracted SNOMED concept, creates an ontology class:

```python
# Fetch preferred term from SNOMED descriptions
preferred_term = self.snomed_explorer.get_preferred_term(concept_id)

# Create OWL class
concept_uri = self.snomed[str(concept_id)]
self.g.add((concept_uri, RDF.type, OWL.Class))
self.g.add((concept_uri, RDFS.label, Literal(preferred_term)))
self.g.add((concept_uri, self.cgo["hasSnomedId"], Literal(str(concept_id))))
```

**Example Transformations:**
- SNOMED Concept ID `84114007` → Class `Heart failure`
- SNOMED Concept ID `42343007` → Class `Congestive heart failure`

### Step 6: Hierarchy Creation

Establishes subclass relationships using SNOMED CT "Is a" relationships:

```python
# Query SNOMED relationships
outgoing_relationships = self.snomed_explorer.get_outgoing_relationships_in_batch(concept_ids)

# Create ontology hierarchy
for concept_id, relationships in outgoing_relationships.items():
    for rel in relationships:
        if rel["typeId"] == 116680003:  # "Is a" relationship
            parent_uri = snomed_classes[rel["destinationId"]]
            child_uri = snomed_classes[concept_id]
            self.g.add((child_uri, RDFS.subClassOf, parent_uri))
```

**Result:** Creates a hierarchical ontology where specific concepts are subclasses of more general ones.

## Usage

### Command Line

```bash
# Generate ontology (class-based modeling)
python -m cardio_graph.snomedct_utils.generate_cardio_ontology \
    --modeling-approach class \
    --output /path/to/output.owl

# With debug mode (limited search terms)
python -m cardio_graph.snomedct_utils.generate_cardio_ontology \
    --debug \
    --modeling-approach class
```

### SLURM Batch Job

```bash
# Submit to compute cluster
sbatch slurm/generate_ontology.sh
```

### Python API

```python
from cardio_graph.snomedct_utils.generate_cardio_ontology import CardioOntologyGenerator

generator = CardioOntologyGenerator(
    output_path="cardio_ontology_class.owl",
    modeling_approach="class",  # "class" or "instance"
    debug_mode=False
)

success = generator.generate_ontology()
```

## Output Statistics

### Current Ontology (January 2026)

- **Core Classes:** 27 cardiovascular domain classes
- **SNOMED-Derived Classes:** 1000+ direct mappings from SNOMED CT
- **Object Properties:** 8 cardiovascular-specific relationships
- **Data Properties:** 12 cardiovascular-specific attributes
- **RDF Triples:** 3204 total
- **File Size:** ~207KB

### Example Classes

**Core Classes:**
- `CardiovascularDisease`
- `HeartDisease` (subclass of CardiovascularDisease)
- `HeartFailure` (subclass of HeartDisease)
- `Arrhythmia` (subclass of HeartDisease)
- `Hypertension` (subclass of CardiovascularDisease)

**SNOMED-Derived Classes:**
- `Acute left-sided congestive heart failure`
- `Chronic right-sided heart failure`
- `High output heart failure`
- `Cardiac ejection fraction, function`
- `Myocardial imaging for infarct with ejection fraction`

## File Locations

### Generated Ontology
```
/prj/doctoral_letters/guide/data/ontologies/cardio_ontology_class.owl
```

### Configuration
```
src/cardio_graph/snomedct_utils/ontology_config.yaml
```

### Generation Scripts
```
src/cardio_graph/snomedct_utils/generate_cardio_ontology.py
slurm/generate_ontology.sh
```

### Logs
```
slurm/generate_ontology_simple.txt
```

## Entity Grounding Integration

The ontology is designed for entity grounding in cardiovascular text:

**Text Mentions → Ontology Classes:**
- "HFrEF" → `HeartFailure` class
- "atrial fibrillation" → `Arrhythmia` class
- "myocardial infarction" → `CoronaryArteryDisease` class
- "hypertension" → `Hypertension` class

**Grounding Process:**
1. Extract entities from text using NER/spaCy
2. Match entity text to ontology class labels
3. Create RDF triples linking text spans to ontology classes
4. Use hierarchical relationships for flexible matching

## Technical Details

### Database Schema

The system queries multiple SNOMED CT tables:
- `snap_concept` - Concept definitions
- `snap_description` - Term descriptions
- `snap_relationship` - Concept relationships

### Performance

- **Database Queries:** ~70 search terms × 500 concepts each = ~35K queries
- **Processing Time:** ~10-15 minutes on SLURM compute nodes
- **Memory Usage:** ~500MB peak during relationship processing

### Modeling Approaches

**Class-Based (Current):**
- SNOMED concepts become OWL Classes
- Direct grounding targets
- Hierarchical relationships via `rdfs:subClassOf`

**Instance-Based (Alternative):**
- SNOMED concepts become OWL Individuals
- More granular but complex for grounding

## Dependencies

- `rdflib` - RDF/OWL manipulation
- `sqlalchemy` - Database ORM
- `psycopg2` - PostgreSQL driver
- `pyyaml` - Configuration parsing
- `baml` - LLM categorization (optional)

## Troubleshooting

### Common Issues

**Database Connection Failed:**
- Check SSL certificates and network access
- Verify SNOMED CT database availability

**Empty Ontology:**
- Check search terms in config
- Verify database contains expected concepts

**Memory Issues:**
- Reduce search limits in debug mode
- Process in smaller batches

### Debug Mode

Enable debug mode for development:
```bash
python -m cardio_graph.snomedct_utils.generate_cardio_ontology --debug
```

Limits searches to 5 terms × 50 concepts for faster iteration.

## Future Enhancements

- **Expanded Search Terms:** Add more clinical acronyms and synonyms
- **Relationship Enrichment:** Include additional SNOMED relationship types
- **Quality Assurance:** Automated validation of ontology completeness
- **Incremental Updates:** Support for ontology versioning and updates</content>
<parameter name="filePath">/home/pwiesenbach/CardioGuidelinesGraph/src/cardio_graph/snomedct_utils/README.md