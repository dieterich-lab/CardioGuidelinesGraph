# Documentation Layout

This repository keeps only durable, human-facing material in `docs/`.

## Stable docs in repo

- `docs/trackers/`: milestone and decision logs that should stay versioned.
- `docs/reference/`: visual or explanatory reference material that is useful to browse in Git.

Current examples:

- `docs/trackers/autotuning/table_22.md`
- `docs/trackers/grounding/table_22.md`
- `docs/reference/ground_truth_rule_graphs/`

## Generated artifacts outside repo

Machine-generated run outputs, alignment dumps, and evaluation manifests belong under:

- `/prj/doctoral_letters/guide/data/cardio_guidelines_graph/artifacts/`

Current workflow roots:

- `/prj/doctoral_letters/guide/data/cardio_guidelines_graph/artifacts/grounding/`
- `/prj/doctoral_letters/guide/data/cardio_guidelines_graph/artifacts/rule_alignment/`

This keeps `docs/` publishable and reviewable while still giving long-lived artifacts a stable shared location.