# Tests Overview

This folder contains three test suites:

- Logic group expansion: tests/test_logic_groups.py
  - Verifies that an OR condition is split into two concepts and assigned an OR logic group.
  - Unit-only (no Neo4j).

- Grounding false-match safeguards: tests/test_grounding_false_matches.py
  - Uses a fake SNOMED explorer to ensure confusing terms are rejected and remain unmapped.
  - Unit-only (no Neo4j).

- Row 10 graph validation: tests/test_row_10_graph.py
  - Verifies that row_10 from the curated recommendation table (table_000) is present in Neo4j
    with the expected DecisionNode and RecommendationNode structure.
  - Requires the Neo4j database to be loaded with the curated table outputs.

## Running tests

- All tests:
  - poetry run python -m unittest discover -s tests -p "test_*.py"

- Row 10 graph only:
  - poetry run python -m unittest tests.test_row_10_graph

- SLURM wrapper for row_10:
  - sbatch slurm/run_row10_tests.sh

## Row 10 manual Cypher checks

Use the queries below to manually reproduce the row_10 expectations.

Rule key:
- _62_63/table_000.json:row_10::1

Concept IDs:
- three-vessel disease: 6121001 (ClinicalCondition)
- LVEF: 250908004 (ClinicalParameter)
- myocardial revascularization: 275227003 (Procedure)

### Recommendation node exists and has class/level

```cypher
MATCH (rec:RecommendationNode {rule_unique_id: "_62_63/table_000.json:row_10::1"})
RETURN rec.class, rec.level, rec.direction, rec.rule_unique_id;
```

### Decision nodes exist (expected 2)

```cypher
MATCH (dec:DecisionNode {rule_unique_id: "_62_63/table_000.json:row_10::1"})
RETURN count(dec) AS decision_count;
```

### Decision nodes link to the condition concepts

```cypher
MATCH (dec:DecisionNode {rule_unique_id: "_62_63/table_000.json:row_10::1"})
-[:CHECKS_FOR|EVALUATES]->(c:Concept)
RETURN DISTINCT c.snomed_id AS snomed_id, labels(c) AS labels;
```

### Recommendation links to the action (procedure)

```cypher
MATCH (rec:RecommendationNode {rule_unique_id: "_62_63/table_000.json:row_10::1"})
-[:RECOMMENDS_PROCEDURE]->(a:Concept)
RETURN DISTINCT a.snomed_id AS snomed_id, labels(a) AS labels;
```

### Decisions reach the recommendation (direct or via LEADS_TO chain)

```cypher
MATCH (dec:DecisionNode {rule_unique_id: "_62_63/table_000.json:row_10::1"})
MATCH (rec:RecommendationNode {rule_unique_id: "_62_63/table_000.json:row_10::1"})
WHERE (dec)-[:RESULTS_IN]->(rec)
   OR (dec)-[:LEADS_TO*1..]->(:DecisionNode)-[:RESULTS_IN]->(rec)
RETURN DISTINCT dec.decision_id AS decision_id;
```

### Label checks for row_10 concepts

```cypher
UNWIND ["6121001", "250908004"] AS cid
MATCH (c:Concept {snomed_id: cid})
RETURN cid AS snomed_id, labels(c) AS labels;
```

```cypher
MATCH (c:Concept:Procedure {snomed_id: "275227003"})
RETURN count(c) AS procedure_count;
```
