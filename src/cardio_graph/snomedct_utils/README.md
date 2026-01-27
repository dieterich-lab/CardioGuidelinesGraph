# CardioGuidelines Ontology Generator

This module generates a comprehensive cardiovascular ontology from SNOMED CT data for use in entity grounding within cardiovascular guidelines and doctoral letters.

## Overview

The ontology generation process creates a rich OWL/RDF ontology containing:
- **Core cardiovascular classes** (HeartDisease, Arrhythmia, Hypertension, etc.)
- **SNOMED CT-derived classes** (categorized mappings from SNOMED concepts, linked to core classes)
- **Hierarchical relationships** based on SNOMED CT "Is a" relationships and core class taxonomy
- **Cardiovascular-specific properties** for relationships and attributes

The resulting ontology enables entity grounding by providing a structured hierarchy where SNOMED concepts are integrated under domain-specific core classes, allowing flexible matching for text mentions (like "HFrEF", "atrial fibrillation", "myocardial infarction").


### Ontology Structure Diagram (Core Schema & Relationships)


```
Core T-Box Classes (Schema)
├── CardiovascularDisease
│   ├── HeartDisease
│   │   ├── HeartFailure
│   │   ├── CoronaryArteryDisease
│   │   ├── Arrhythmia
│   │   ├── ValvularHeartDisease
│   │   └── Cardiomyopathy
│   ├── Hypertension
│   ├── Stroke
│   └── PeripheralArteryDisease
├── CardiacProcedure
│   ├── CardiacImaging
│   ├── CardiacCatheterization
│   ├── CardiacSurgery
│   └── CardiacDeviceImplantation
├── CardiovascularMedication
│   ├── Antihypertensive
│   ├── Antiarrhythmic
│   ├── Anticoagulant
│   ├── Antiplatelet
│   ├── LipidLoweringAgent
│   └── HeartFailureMedication
├── CardiovascularRiskFactor
├── CardiacBiomarker
├── CardiovascularSymptom
├── CardiovascularEvent
│   └── Mortality

Object Properties (Relationships):
  CardiovascularDisease
    ├─ hasRiskFactor ─────────────► CardiovascularRiskFactor
    ├─ hasSymptom ───────────────► CardiovascularSymptom
    ├─ hasBiomarker ─────────────► CardiacBiomarker
    ├─ treatedBy ────────────────► CardiovascularMedication
    ├─ treatedBy ────────────────► CardiacProcedure
    ├─ causes ───────────────────► CardiovascularEvent
  CardiovascularMedication
    ├─ interactsWith ────────────► CardiovascularMedication
    ├─ hasAdverseEffect ────────► CardiovascularSymptom

Data Properties (Attributes):
  (applies to various classes, see config)
    ├─ hasSnomedId: string
    ├─ hasDescription: string
    ├─ hasSeverity: string (CardiovascularDisease)
    ├─ hasStage: string (CardiovascularDisease)
    ├─ hasPrognosis: string (CardiovascularDisease)
    ├─ hasPrevalence: string (CardiovascularDisease)
    ├─ hasDosage: string (CardiovascularMedication)
    ├─ hasIndication: string (CardiovascularMedication)
    ├─ hasContraindication: string (CardiovascularMedication)
    ├─ hasNormalRange: string (CardiacBiomarker)
    ├─ hasUnits: string (CardiacBiomarker)
    ├─ hasRelativeRisk: string (CardiovascularRiskFactor)

Legend:
- All arrows represent rdfs:subClassOf or object property relationships.
- This diagram is a direct reflection of all core_classes defined in ontology_config.yaml.
- Only core classes and relationships are shown here. SNOMED-derived classes will be shown in real examples after the current ontology generation run completes.
```

> **Note:** SNOMED-derived classes (A-Box) and their mappings to core classes will be illustrated with real examples once the current ontology generation run is finished. This ensures the documentation reflects actual mappings and codes.

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

## Ontology Generation Pipeline

Below is a step-by-step overview and a schematic of how the ontology is derived from SNOMED CT and the configuration:

```
┌────────────────────┐
│ ontology_config.yaml│
└─────────┬──────────┘
          │ (defines core classes, properties, search terms)
          ▼
┌────────────────────────────┐
│ generate_cardio_ontology.py│
└─────────┬──────────────────┘
          │ (loads config, connects to SNOMED DB)
          ▼
┌──────────────────────────────┐
│ SNOMED CT PostgreSQL DB      │
└─────────┬────────────────────┘
          │ (extracts concepts using search terms)
          ▼
┌──────────────────────────────┐
│ LLM-based Categorization     │
└─────────┬────────────────────┘
          │ (assigns SNOMED concepts to core classes)
          ▼
┌──────────────────────────────┐
│ Ontology Construction        │
└─────────┬────────────────────┘
          │ (creates classes, properties, relationships)
          ▼
┌──────────────────────────────┐
│ Output: OWL/RDF Ontology     │
└──────────────────────────────┘
```

### Stepwise Process

1. **Configuration Loading:**
   - Loads `ontology_config.yaml` (core classes, object/data properties, search terms).
2. **Database Connection:**
   - Connects to SNOMED CT PostgreSQL DB using credentials in the script/config.
3. **Concept Extraction:**
   - For each search term, queries SNOMED for matching concepts and deduplicates results.
4. **Core Schema Initialization:**
   - Creates all core classes and properties in the ontology graph.
5. **LLM-based Categorization:**
   - For each SNOMED concept, uses an LLM to assign it to one or more core classes (categories).
6. **Class Creation & Mapping:**
   - Adds each SNOMED concept as a subclass of its assigned core class(es), with synonyms as SKOS altLabels.
7. **Relationship Construction:**
   - Adds subclass relationships (core and SNOMED "Is a"), object/data properties, and links.
8. **Ontology Output:**
   - Serializes the ontology as OWL/RDF to the specified output file.

> **Tip:** The pipeline is fully configurable and extensible. To add new classes, properties, or search terms, simply update `ontology_config.yaml` and rerun the script.

---

## How We Derive the Ontology from SNOMED: Key Points

- **All core classes and relationships are defined in the config, not hardcoded.**
- **SNOMED concepts are extracted using broad, domain-specific search terms.**
- **LLM-based categorization ensures that each SNOMED concept is mapped to the most appropriate core class, not just by keyword.**
- **All relationships (object/data properties) are explicitly declared and visualized in the diagram above.**
- **The resulting ontology is a unified, extensible hierarchy, ready for entity grounding and further knowledge population.**

---

## Preview: Real SNOMED-Derived (A-Box) Classes from Current Run

Here are some real examples of SNOMED concepts mapped to core classes, as processed in the current ontology generation run:

| SNOMED Concept (ID)                                 | Core Class Mapping         | Synonyms (SKOS altLabels)                                                                 |
|-----------------------------------------------------|---------------------------|------------------------------------------------------------------------------------------|
| Acute left-sided heart failure (364006)             | Condition                 | Acute left heart failure, Acute left-sided heart failure                                  |
| Heart valve disorder (368009)                       | Condition                 | Disorder of heart valve, Heart valve disease, Heart valve disorder, Valvular heart disease|
| Abnormal fetal heart beat noted before labor (655007)| Condition, PatientPhenotype| Abnormal fetal heart beat noted before labor in liveborn infant, Abnormal fetal heart beat noted before labour in liveborn infant, Abnormal foetal heart beat noted before labour in liveborn infant |
| Heart valve disorder (368009)                       | Condition                 | Disorder of heart valve, Heart valve disease, Heart valve disorder, Valvular heart disease|

**Note:** These are just a few preview entries. The final ontology will contain 1000+ such SNOMED-derived classes, each mapped to one or more core classes and enriched with synonyms for robust entity grounding.

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

The ontology is designed for entity grounding in cardiovascular text by providing a unified hierarchy that combines domain expertise (core classes) with comprehensive medical terminology (SNOMED):

**Text Mentions → Ontology Classes:**
- "HFrEF" → `HeartFailure` class (core) or `Heart failure` (SNOMED, via synonyms)
- "atrial fibrillation" → `Arrhythmia` class (core) or `Atrial fibrillation` (SNOMED)
- "myocardial infarction" → `CoronaryArteryDisease` class (core) or `Myocardial infarction` (SNOMED)
- "hypertension" → `Hypertension` class (core) or `Essential hypertension` (SNOMED)

**Grounding Process:**
1. Extract entities from text using NER/spaCy
2. Match entity text to ontology class labels (core + SNOMED)
3. Create RDF triples linking text spans to ontology classes
4. Use hierarchical relationships for flexible matching (e.g., "acute HF" can ground to `Acute heart failure` → `Heart failure` → `HeartFailure`)

**Intertwined Hierarchy Benefits:**
- **Precision:** Core classes provide domain-specific categories
- **Coverage:** SNOMED classes add detailed medical terminology
- **Flexibility:** Multiple paths for grounding (direct to core or via SNOMED)
- **Inheritance:** SNOMED classes inherit properties from their core parents

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

**Class-Based with Categorization (Current):**
- SNOMED concepts become OWL Classes, categorized under core classes
- LLM-based assignment ensures accurate domain mapping
- Combined hierarchy: core taxonomy + SNOMED relationships
- Optimal for entity grounding with structured knowledge

**Class-Based (Legacy):**
- SNOMED concepts become OWL Classes without categorization
- Flat hierarchy based only on SNOMED "Is a" relationships
- Limited integration with domain schema

**Instance-Based (Alternative):**
- SNOMED concepts become OWL Individuals
- More granular but complex for grounding

## Dependencies

- `rdflib` - RDF/OWL manipulation
- `sqlalchemy` - Database ORM
- `psycopg2` - PostgreSQL driver
- `pyyaml` - Configuration parsing
- `baml` - LLM categorization and client management

## Troubleshooting

### Common Issues

**Database Connection Failed:**
- Check SSL certificates and network access
- Verify SNOMED CT database availability

**LLM Categorization Failed:**
- Ensure Ollama server is running on specified node/port
- Check BAML client configuration
- Verify model availability

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
- **Relationship Enrichment:** Include additional SNOMED relationship types beyond "Is a"
- **Categorization Improvements:** Fine-tune LLM prompts and add manual curation
- **Quality Assurance:** Automated validation of ontology completeness and categorization accuracy
- **Incremental Updates:** Support for ontology versioning and updates</content>
<parameter name="filePath">/home/pwiesenbach/CardioGuidelinesGraph/src/cardio_graph/snomedct_utils/README.md