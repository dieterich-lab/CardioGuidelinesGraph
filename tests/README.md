# Tests

This directory now contains only test modules.

## Scope

- Unit tests for schema/type contract sync and alignment logic.
- Unit tests for tuning gates and scoring profiles.
- Focused grounding helper tests.
- Integration tests that validate graph/grounding behavior when external dependencies are available.

## Run tests

From repository root:

```bash
cd /home/pwiesenbach/CardioGuidelinesGraph
poetry run pytest tests
```

## Evaluation workflows moved out of tests

Artifact-generating table22 evaluation flows were moved to non-test locations:

- row-wise rule alignment evaluator:
  - `src/cardio_graph_core/evaluation/table22_rule_alignment_eval.py`
- tuning/dev entrypoint that invokes the evaluator:
  - `src/cardio_graph_core/tuning/table22_dev_eval.py`
- single-row report helper:
  - `scripts/evaluate_table22_single_row.py`

Use those modules/scripts directly for evaluation/report generation instead of invoking test files.
