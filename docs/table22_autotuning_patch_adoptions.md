# Table 22 Autotuning Patch Adoptions

This file records prompt patch candidates produced by autotuning runs and whether they were adopted.

## Config location update

- Active autotuning manifests/splits now live under: `config/autotuning/`
- Legacy `config/table22/` remains for backward compatibility during transition.

## Leakage control policy

- For runs with `CARDIO_GRAPH_ENABLE_FEWSHOT_EXAMPLES=true`, exemplar rows are excluded from both dev and locked test.
- Current leakage-safe manifest: `config/autotuning/benchmark_manifest_v3.jsonc`.
- Excluded exemplar rows:
  - `table17`: `t0_row_01`
  - `table8`: `row_01`

## Run: cascade_16h / 20260311_165230

Root: `docs/table22_tuning_runs/cascade_16h/20260311_165230`

### Phase 1 smoke (`phase_1_smoke_1x1`)

- Candidate: `iter_01/candidate_01`
- Source patch: `phase_1_smoke_1x1/iter_01/candidate_01/prompt_patch.json`
- Proposed edit:
  - `[condition_extraction]` Ensure ClinicalCondition operator is `PRESENT` unless negated.
- Gate outcome: accepted on dev-only smoke.
- Adoption status: **not promoted to final baseline** (smoke-only and weak rule_exact_match).

### Phase 4 locked checks (`phase_4_locked_checks`)

- Candidate: `iter_02/candidate_01`
- Source patch: `phase_4_locked_checks/iter_02/candidate_01/prompt_patch.json`
- Proposed edits:
  - `[condition_extraction]` "Extract all clinical conditions, parameters, and procedures from text. Capture role, operator, threshold, unit, context, and logical group. Do not omit any concepts."
  - `[action_extraction]` "Extract all procedures as actions with strength, level, direction, and context. Capture all actions even if part of a phrase."
- Gate outcome: accepted on dev and locked test (`promotion_reason=accepted_with_locked_test`).
- Adoption status: **adopted as tuned baseline for follow-up runs** via `prompt_v2_candidate_01`.

## Current promoted prompt delta

Promoted prompt file:
- `docs/table22_tuning_runs/cascade_16h/20260311_165230/phase_4_locked_checks/prompts/prompt_v2_candidate_01.txt`

Observed active appendix content in promoted prompt:
- `[condition_extraction] Extract all clinical conditions, parameters, and procedures from text. Capture role, operator, threshold, unit, context, and logical group. Do not omit any concepts.`

## Reporting notes for community updates

When summarizing externally, include:
1. Run ID / phase path.
2. Candidate patch JSON path.
3. Gate decision paths (dev + locked where available).
4. Final promoted prompt path.
5. Before/after key metrics (`rule_exact_match`, `operator_accuracy`, `concept_f1`).
