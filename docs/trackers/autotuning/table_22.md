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

Root: `autotuning/table_22/cascade_16h/20260311_165230` in the external artifact store

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
- `autotuning/table_22/cascade_16h/20260311_165230/phase_4_locked_checks/prompts/prompt_v2_candidate_01.txt` in the external artifact store

Observed active appendix content in promoted prompt:
- `[condition_extraction] Extract all clinical conditions, parameters, and procedures from text. Capture role, operator, threshold, unit, context, and logical group. Do not omit any concepts.`

## Reporting notes for community updates

When summarizing externally, include:
1. Run ID / phase path.
2. Candidate patch JSON path.
3. Gate decision paths (dev + locked where available).
4. Final promoted prompt path.
5. Before/after key metrics (`rule_exact_match`, `operator_accuracy`, `concept_f1`).

## Grounding selection patch track (2026-03-25)

Goal:
- Reduce persistent Table22 vector grounding misses caused by semantic type drift,
  while preserving already correct mappings.

Evidence snapshot (latest completed run `628273`):
- Overall: `0.666667` (`56/84`).
- Misses: `28`.
- Manual vector probe (`628307`) showed gold concept appears in vector top-25 for
  `26/28` misses (median gold rank `1.0`).
- Implication: retrieval is usually good; post-retrieval selection/reranking is
  the main bottleneck.

Patch components currently implemented (opt-in; default off):
- Vector-rank prior bonus for high-rank vector candidates under lexical floor.
- Near-tie vector-rank rescue promotion rule.
- Evidence-weighted semantic-penalty relief when coverage and vector rank are
  both strong.

Implementation files:
- `src/cardio_graph_core/extraction/guideline_graph_builder.py`
- `src/cardio_graph_core/grounding/entity_grounding_service.py`
- `tests/test_entity_grounding_rank_rescue.py`

Validation status:
- Focused tests pass (`4 passed`) for helper logic and safety guards.

Next decision gate (after reduced-knob runs `628305/628306` complete):
1. Refresh `docs/trackers/grounding/table_22.md` as the single tuning milestone doc.
2. Compare reduced-knob results vs baseline (`627576`, `628273`).
3. If no severe regression, run one A/B with the new patch toggles enabled.
