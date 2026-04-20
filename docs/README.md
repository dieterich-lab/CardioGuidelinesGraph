# Documentation Layout

This repository separates **manual documentation** from **generated snapshots**.

## Manual docs (authored and tracked)

- `docs/experiments/`: milestone notes, decisions, and experiment tracking.
- `docs/reports/`: stable reference visuals, summaries, and evaluation tables.

Current examples:

- `docs/experiments/grounding/README.md`
- `docs/experiments/autotuning/multi_table.md`
- `docs/experiments/grounding/cardio_subset_tuning.md`
- `docs/experiments/grounding/snomed_vector_grounding_tracks.md`
- `docs/reports/ground_truth_rule_graphs/`

## Generated docs (machine-written snapshots)

- `docs/generated/grounding/`: generated milestone and manifest outputs from vector grounding runs.
- `docs/generated/ground_truth/`: raw run snapshots for ground-truth-based grounding evaluations.

Current generated files:

- `docs/generated/grounding/ground_truth_vector_grounding_milestone.md`
- `docs/generated/grounding/ground_truth_vector_grounding_persistent_error_manifest.json`
- `docs/generated/ground_truth/grounding_only/vector_job_<jobid>/ground_truth_vector_eval.json`

## Large run artifacts (external storage)

Machine-generated run outputs, alignment dumps, and larger evaluation artifacts remain under:

- `/prj/doctoral_letters/guide/data/cardio_guidelines_graph/artifacts/`

Current workflow roots:

- `/prj/doctoral_letters/guide/data/cardio_guidelines_graph/artifacts/grounding/`
- `/prj/doctoral_letters/guide/data/cardio_guidelines_graph/artifacts/rule_alignment/`
