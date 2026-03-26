# GT3 Vector Grounding Ablation Schedule

This schedule targets the current 3-table ground truth setup:

- `/prj/doctoral_letters/guide/data/evaluation/table_17_manual_1.3.json`
- `/prj/doctoral_letters/guide/data/evaluation/table_22_manual_1.3.json`
- `/prj/doctoral_letters/guide/data/evaluation/table_8_manual_1.4.json`

Canonical launcher:

- `slurm/gt-eval-vector.sbatch`

## Tracking (automatic)

The launcher already calls:

- `scripts/generate_grounding_progress_report.py`

To refresh all derived reports (milestone + triage) after runs:

```bash
/home/pwiesenbach/CardioGuidelinesGraph/.venv/bin/python scripts/refresh_gt3_vector_tracking.py
```

Generated outputs:

- `docs/generated/grounding/ground_truth_vector_grounding_milestone.md`
- `docs/generated/grounding/ground_truth_vector_grounding_persistent_error_manifest.json`
- `docs/generated/grounding/ground_truth_vector_latest_miss_triage.csv`
- `docs/generated/grounding/ground_truth_vector_latest_miss_triage.md`

## Safe 5-run ablation matrix

Run each arm at least once (preferably 2x for stability). Keep all other knobs unchanged.

### Arm A: Baseline (current default)

```bash
sbatch slurm/gt-eval-vector.sbatch
```

### Arm B: Enable vector context for Procedure

```bash
sbatch --export=ALL,\
CARDIO_GRAPH_GROUNDING_VECTOR_CONTEXT_ENABLED=true,\
CARDIO_GRAPH_GROUNDING_VECTOR_CONTEXT_ALLOWED_ROLES=Procedure,\
CARDIO_GRAPH_GROUNDING_VECTOR_CONTEXT_APPEND_TERM=false,\
CARDIO_GRAPH_GROUNDING_VECTOR_CONTEXT_MAX_TOKENS=8 \
slurm/gt-eval-vector.sbatch
```

### Arm C: Stronger role mismatch penalty

```bash
sbatch --export=ALL,\
CARDIO_GRAPH_GROUNDING_ROLE_MISMATCH_PENALTY=0.07 \
slurm/gt-eval-vector.sbatch
```

### Arm D: Stronger semantic mismatch penalties

```bash
sbatch --export=ALL,\
CARDIO_GRAPH_GROUNDING_ROLE_SEMANTIC_MISMATCH_PENALTY=0.08,\
CARDIO_GRAPH_GROUNDING_ROLE_SEMANTIC_CROSSCLASS_PENALTY=0.03 \
slurm/gt-eval-vector.sbatch
```

### Arm E: Slightly stricter ambiguity backoff

```bash
sbatch --export=ALL,\
CARDIO_GRAPH_GROUNDING_AMBIGUITY_BACKOFF_MAX_DROP=0.04,\
CARDIO_GRAPH_GROUNDING_AMBIGUITY_BACKOFF_MIN_SCORE=0.40 \
slurm/gt-eval-vector.sbatch
```

## Promotion gate (safe)

Promote an arm only if all pass:

1. Overall accuracy improves by >= 0.01 vs latest baseline median.
2. Procedure accuracy improves by >= 0.02.
3. No drop > 0.02 in ClinicalCondition or Medication.
4. Top confusion pair count (latest report) decreases for at least one of:
   - `415070008 -> 713617008`
   - `260678004 -> 440678006`
   - `230165009 -> 1363183004`

## Recommended cadence

1. Submit one arm.
2. Wait for completion.
3. Run `/home/pwiesenbach/CardioGuidelinesGraph/.venv/bin/python scripts/refresh_gt3_vector_tracking.py`.
4. Check leaderboard + latest confusions.
5. Continue with next arm.
