# Grid Search Proxy Assessment

This summary compares the row-wise baseline with all 24 grid runs.
Metrics are computed directly from the slurm logs.

## Baseline (row-wise)

- mapped_rate: 0.556 | mismatch_rate: 0.171 | median_score: 0.841 | unique_concepts: 37 | total: 81

## Top performers by mapped rate

Ordered by mapped_rate desc, mismatch_rate asc, median_score desc.

- score0.6_df0_tag0_off0: mapped 0.605, mismatch 0.182, median 0.846, concepts 36, total 81
- score0.6_df1_tag0_off0: mapped 0.558, mismatch 0.000, median 0.745, concepts 35, total 77
- score0.6_df0_tag0_off1: mapped 0.550, mismatch 0.200, median 0.844, concepts 35, total 80
- score0.6_df1_tag1_off1: mapped 0.545, mismatch 0.000, median 0.742, concepts 34, total 77
- score0.6_df1_tag0_off1: mapped 0.533, mismatch 0.000, median 0.765, concepts 32, total 75

## Top performers by mismatch rate

Ordered by mismatch_rate asc, mapped_rate desc, median_score desc.

- score0.6_df1_tag0_off0: mismatch 0.000, mapped 0.558, median 0.745, concepts 35, total 77
- score0.6_df1_tag1_off1: mismatch 0.000, mapped 0.545, median 0.742, concepts 34, total 77
- score0.6_df1_tag0_off1: mismatch 0.000, mapped 0.533, median 0.765, concepts 32, total 75
- score0.6_df1_tag1_off0: mismatch 0.000, mapped 0.486, median 0.762, concepts 28, total 72
- score0.7_df1_tag0_off0: mismatch 0.000, mapped 0.358, median 0.952, concepts 23, total 81

## Default click parameters

- score0.6_df1_tag0_off1: mapped 0.533, mismatch 0.000, median 0.765, concepts 32, total 75

## Spot-check (mismatch examples)

Examples are parsed from mismatched FSN tags for each run.

### score0.6_df0_tag0_off0

- entity: Patients scheduled for revascularization | role: Condition | tag: procedure | preferred_term: Grafting of heart for revascularization (procedure) | score: 0.832608695652174
- entity: Patients scheduled for revascularization | role: Condition | tag: procedure | preferred_term: Grafting of heart for revascularization (procedure) | score: 0.832608695652174
- entity: Patient communication of Heart Team recommendations | role: Procedure | tag: physical object | preferred_term: Keeping communication aid by patient (physical object) | score: 0.6017241379310345
- entity: Social support | role: Procedure | tag: regime/therapy | preferred_term: Social support (regime/therapy) | score: 1.0
- entity: Local Expertise | role: Condition | tag: product | preferred_term: Local anti-infective (product) | score: 0.6951612903225807

### score0.6_df1_tag0_off0

- No mismatches captured in first 5 samples.

### score0.6_df0_tag0_off1

- entity: Patients scheduled for revascularization | role: Condition | tag: procedure | preferred_term: Grafting of heart for revascularization (procedure) | score: 0.832608695652174
- entity: Patients scheduled for revascularization | role: Condition | tag: procedure | preferred_term: Grafting of heart for revascularization (procedure) | score: 0.832608695652174
- entity: Patient communication of Heart Team recommendations | role: Procedure | tag: physical object | preferred_term: Keeping communication aid by patient (physical object) | score: 0.6017241379310345
- entity: Social support | role: Procedure | tag: regime/therapy | preferred_term: Social support (regime/therapy) | score: 1.0
- entity: Local Expertise | role: Condition | tag: product | preferred_term: Local anti-infective (product) | score: 0.6951612903225807

## CSV output

- docs/grid_search_summary.csv
