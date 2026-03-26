# Generated Ground-Truth Evaluation Artifacts

This folder stores machine-generated run outputs for evaluations driven by
ground-truth annotation sets.

Current convention:

- `grounding_only/vector_job_<jobid>/ground_truth_vector_eval.json`: raw vector grounding eval output.

Compatibility note: legacy runs may still contain `vector_eval.json`.

Use this folder for shared evaluation artifacts that are not specific to a
single table name. Keep manual analysis and tracking in `docs/trackers/`.
