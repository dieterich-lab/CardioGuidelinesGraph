# Utility Scripts

This directory contains utility and testing scripts for the CardioGuidelinesGraph project.

## Scripts

### `analyze_ontology.py`
Analyzes the generated ontology file and provides statistics and insights.

### `debug_descriptions.py`
Debug script for investigating issues with SNOMED CT description retrieval.

### `inspect_snomed_descriptions.py`
Script to inspect SNOMED CT descriptions for specific concepts, useful for debugging entity grounding issues.

### `test_grounding_recall.py`
Simple test script to verify that the entity grounding service is working correctly.

## Usage

Most scripts can be run directly with Python:

```bash
cd /path/to/CardioGuidelinesGraph
python tools/script_name.py
```

Some scripts may require the virtual environment to be activated:

```bash
source .venv/bin/activate
python tools/script_name.py
```