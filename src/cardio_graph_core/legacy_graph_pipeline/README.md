# Legacy Graph Pipeline

Legacy graph pipeline support modules.

This package contains reusable helper modules that were previously stored directly in `scripts/`.

Rules:

- keep reusable Python modules here, not in `scripts/`
- keep `scripts/` limited to thin runnable entrypoints
- prefer package-relative imports inside this package

Status:

- retained for backwards compatibility with older experimental graph extraction workflows
- not part of the main cardio graph production pipeline
