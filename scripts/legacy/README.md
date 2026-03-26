# Legacy Scripts

Legacy one-off scripts live here.

Purpose:

- historical graph extraction experiments
- ad hoc import/parsing utilities
- scripts with hardcoded assumptions or environment-specific behavior

Policy:

- do not add reusable library code here
- reusable helpers belong under `src/cardio_graph_core/legacy_graph_pipeline/`
- new maintained CLIs belong in `scripts/`

These files are intentionally quarantined because they are not production-grade entrypoints.
