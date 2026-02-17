<!-- markdownlint-disable MD022 MD032 -->

# Table 22 Autotuning Controller (Draft v0.1)

## 1. Scope

This draft defines a constrained autotuning loop for Table 22 where:
- LLM1 performs extraction,
- deterministic scoring computes errors vs. ground truth,
- LLM2 analyzes failure patterns,
- LLM3 proposes prompt edits,
- a controller accepts/rejects edits based on hard gates.

Goal: automate prompt evolution while preserving reproducibility and preventing overfitting.

Non-goals (for v0.1):
- no model-weight fine-tuning,
- no arbitrary file edits,
- no direct test-set optimization.

---

## 2. Roles and components

### LLM1: Extractor
Responsibilities:
- run current extraction prompt and pipeline,
- produce row-level outputs for selected split,
- keep extraction deterministic as far as possible (fixed config).

Inputs:
- prompt candidate,
- split rows,
- extraction config.

Outputs:
- standard rowwise artifacts already produced by your harness.

### Deterministic Scorer (must not be LLM)
Responsibilities:
- compare outputs to Table 22 ground truth,
- compute fixed metrics,
- emit normalized error objects.

Why deterministic:
- prevents judge drift,
- enables reproducible acceptance criteria.

### LLM2: Error Analyst
Responsibilities:
- consume deterministic error objects,
- cluster failures into taxonomy classes,
- identify top root causes and confidence.

Outputs:
- ranked error classes,
- suggested tuning targets (max 1–2 per iteration).

### LLM3: Prompt Optimizer
Responsibilities:
- propose minimal prompt patch targeting selected error classes,
- return structured patch proposal with rationale.

Constraint:
- may edit only explicit prompt-editable zones.

### Controller
Responsibilities:
- orchestrate loop,
- enforce gates,
- maintain champion/challenger prompts,
- log every decision with metrics and artifact pointers.

---

## 3. State machine

States:
1. `BASELINE`
2. `RUN_DEV`
3. `SCORE_DEV`
4. `ANALYZE_ERRORS`
5. `PROPOSE_PATCH`
6. `APPLY_PATCH_SANDBOX`
7. `RUN_DEV_CHALLENGER`
8. `COMPARE_DEV`
9. `RUN_LOCKED_TEST_CHECKPOINT` (periodic)
10. `PROMOTE_OR_REJECT`
11. `STOP`

Transitions:
- `BASELINE -> RUN_DEV`: initialize champion prompt.
- `COMPARE_DEV -> PROPOSE_PATCH`: if gate fail but budget remains.
- `COMPARE_DEV -> RUN_LOCKED_TEST_CHECKPOINT`: if dev improves and checkpoint cadence met.
- `RUN_LOCKED_TEST_CHECKPOINT -> PROMOTE_OR_REJECT`: test guard outcome.
- `PROMOTE_OR_REJECT -> RUN_DEV`: next iteration.
- any state -> `STOP`: when stop criteria satisfied.

---

## 4. Contracts (JSON)

### 4.1 Deterministic score output (`score_report.json`)

```json
{
  "run_id": "dev_20260217_170100",
  "split": "dev",
  "prompt_version": "prompt_v3",
  "metrics": {
    "schema_valid_rate": 1.0,
    "rule_exact_match": 0.42,
    "operator_accuracy": 0.61,
    "logic_group_accuracy": 0.54,
    "concept_precision": 0.73,
    "concept_recall": 0.68,
    "concept_f1": 0.70,
    "grounding_hit_rate": 0.79
  },
  "rows": [
    {
      "row_id": "row_08",
      "errors": [
        {
          "class": "C6_logic_group_wrong",
          "severity": "major",
          "expected": "or_1",
          "actual": "group_1"
        }
      ]
    }
  ]
}
```

### 4.2 LLM2 analysis output (`error_analysis.json`)

```json
{
  "run_id": "dev_20260217_170100",
  "top_classes": [
    {
      "class": "C1_operator_wrong",
      "count": 19,
      "confidence": 0.88,
      "root_cause_hypothesis": "scheduled phrases mapped to PLANNED too aggressively"
    },
    {
      "class": "C6_logic_group_wrong",
      "count": 14,
      "confidence": 0.81,
      "root_cause_hypothesis": "insufficient grouping instruction priority"
    }
  ],
  "selected_targets": ["C1_operator_wrong", "C6_logic_group_wrong"]
}
```

### 4.3 LLM3 patch proposal (`prompt_patch.json`)

```json
{
  "base_prompt_version": "prompt_v3",
  "candidate_prompt_version": "prompt_v4_candidate1",
  "target_classes": ["C1_operator_wrong", "C6_logic_group_wrong"],
  "edits": [
    {
      "zone": "operator_resolution_rules",
      "change_type": "replace",
      "old": "...",
      "new": "..."
    },
    {
      "zone": "logic_grouping_rules",
      "change_type": "append",
      "old": "",
      "new": "..."
    }
  ],
  "max_edit_lines": 30,
  "rationale": "tighten operator precedence and explicit OR grouping behavior"
}
```

---

## 5. Editable surface and safety policy

Only editable by LLM3:
- prompt text zone in extraction prompt file,
- optional prompt examples block,
- priority/rule ordering inside prompt.

Not editable by LLM3:
- scorer logic,
- split assignments,
- locked-test row list,
- acceptance thresholds,
- graph schema contract.

Safety checks before any run:
- patch parses,
- changed lines <= `max_edit_lines`,
- no changes outside allowed zones.

---

## 6. Acceptance gates (champion vs challenger)

Let champion metrics be `M_c`, challenger metrics be `M_n`.

Primary objective:
- maximize `rule_exact_match` on dev.

Hard must-pass:
- `schema_valid_rate_n == 1.0`,
- `rule_exact_match_n >= rule_exact_match_c + 0.005` (absolute),
- no regression > 0.01 absolute on each of:
  - `operator_accuracy`,
  - `logic_group_accuracy`,
  - `concept_f1`.

Checkpoint gate (every 3 accepted dev promotions):
- run locked test,
- reject promotion if locked test `rule_exact_match` decreases > 0.01 absolute.

Tie-break:
- prefer lower variance across rows (smaller std of row match scores).

---

## 7. Loop cadence and budgets

Recommended defaults:
- max iterations per session: 20,
- max accepted promotions per day: 6,
- locked-test checkpoint cadence: every 3 accepted promotions,
- target classes per iteration: max 2,
- early stop when no accepted promotion in last 5 iterations.

---

## 8. Overfitting controls

- Keep locked test immutable.
- Never feed locked-test row-level failures into LLM3 patch generation.
- Run occasional “holdout stress check” using selected difficult rows not targeted in current iteration.
- Preserve full audit trail for each accepted and rejected challenger.

Audit record fields:
- iteration id,
- base and candidate prompt version,
- target classes,
- metric deltas,
- gate outcome,
- artifact paths,
- commit SHA (if promoted).

---

## 9. Practical integration with current repo

Existing assets to reuse:
- split manifest: `config/table22/split_v1.json`,
- playbook taxonomy/templates in `docs/table22_tuning_templates/`,
- existing Table22 unittest runner and slurm submission pattern,
- rowwise artifacts (`summary.csv`, `alignment.json`, row markdown files).

Recommended new modules (next step):
- `src/cardio_graph_core/tuning/controller.py`
- `src/cardio_graph_core/tuning/contracts.py`
- `src/cardio_graph_core/tuning/gates.py`
- `src/cardio_graph_core/tuning/prompt_patcher.py`
- `src/cardio_graph_core/tuning/score_adapter.py`

Recommended run CLI:
- `poetry run python -m cardio_graph_core.tuning.controller --split dev --budget 20`

---

## 10. Minimal algorithm (pseudo)

```text
champion = load_prompt("prompt_v0")
best = evaluate(champion, split="dev")

for i in range(max_iters):
  errors = deterministic_score(best.artifacts)
  analysis = llm2_analyze(errors)
  targets = pick_top_classes(analysis, k=2)

  patch = llm3_propose_patch(champion, targets)
  if not patch_is_safe(patch):
    log_reject("unsafe_patch")
    continue

  challenger = apply_patch_in_sandbox(champion, patch)
  result_dev = evaluate(challenger, split="dev")

  if passes_dev_gates(best.metrics, result_dev.metrics):
    if should_run_locked_test_checkpoint():
      result_test = evaluate(challenger, split="locked_test")
      if not passes_test_gates(result_test):
        log_reject("test_regression")
        continue

    champion = challenger
    best = result_dev
    log_promote()
  else:
    log_reject("dev_gate_fail")

  if early_stop_condition_met():
    break
```

---

## 11. Open decisions for you

1. Which model should play LLM2 and LLM3?
   - same model family as extractor for consistency, or stronger critic model.

2. How strict should the primary improvement threshold be?
   - default in this draft: +0.005 absolute rule exact match.

3. Do we allow automatic commits for promoted prompts?
   - recommended: yes, but behind `--auto-commit` flag.

4. Should grounding be included in acceptance gates now?
   - recommended: track but do not gate until extraction stabilizes.

---

## 12. Suggested immediate implementation plan

Phase 1 (1–2 days):
- implement deterministic score adapter + JSON contracts,
- implement gate evaluator,
- implement prompt patch apply/check in sandbox.

Phase 2 (2–4 days):
- integrate LLM2/LLM3 calls,
- add controller CLI with full loop and logging.

Phase 3 (1–2 days):
- add checkpoint runner for locked test,
- add promotion registry + optional auto-commit.

---

## 13. Scaffold status and run command

Initial scaffold modules now exist:

- `src/cardio_graph_core/tuning/contracts.py`
- `src/cardio_graph_core/tuning/gates.py`
- `src/cardio_graph_core/tuning/controller.py`

Run dry-run controller:

```bash
poetry run python -m cardio_graph_core.tuning.controller \
  --split-manifest config/table22/split_v1.json \
  --iterations 5 \
  --run-locked-every 3 \
  --output-dir docs/table22_tuning_runs/autotune_dryrun \
  --dry-run
```

Expected output:

- per-iteration artifacts under `docs/table22_tuning_runs/autotune_dryrun/<timestamp>/iter_XX/`
- final summary at `.../run_summary.json`

<!-- markdownlint-enable MD022 MD032 -->
