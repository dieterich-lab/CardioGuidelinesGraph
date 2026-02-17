<!-- markdownlint-disable MD022 MD032 -->

# Table 22 LLM Tuning Playbook

## 1) Purpose and guardrails

This playbook defines how to tune extraction quality against Table 22 **without overfitting** and with full traceability to the graph schema and graph builder pipeline.

Primary goals:
- Improve concept and rule alignment vs. Table 22 ground truth.
- Keep extraction behavior schema-consistent (single-source-of-truth discipline).
- Separate extraction errors from grounding errors.
- Preserve reproducibility (same inputs, same config, same outputs).

Hard guardrails:
- Table 22 remains the canonical benchmark corpus.
- Prompt/model changes are accepted only if they improve dev and do not regress locked test.
- Every tuning iteration must record: model, prompt version, graph builder settings, and metrics.

---

## 2) Data split (recommended now)

Current table size: 19 rows (`row_01`..`row_19`).

Use a fixed **13/6** split:

### Dev set (13 rows) – for prompt and pipeline iteration
- `row_02`, `row_03`, `row_04`, `row_05`, `row_06`, `row_09`, `row_10`, `row_11`, `row_12`, `row_13`, `row_14`, `row_15`, `row_17`

### Locked test set (6 rows) – no tuning on these rows
- `row_01`, `row_07`, `row_08`, `row_16`, `row_18`, `row_19`

Why this split:
- Keeps high-complexity logic in test (`row_08`, `row_16`, `row_01`).
- Keeps numeric-threshold behavior represented in test (`row_07`, `row_08`).
- Keeps rare recommendation classes in test (`IIa` in `row_18`, `IIb` in `row_19`).
- Still leaves one `IIb` row in dev (`row_11`) so the system can learn class handling.

### When manual annotations mature
Recompute split with stratification over:
- recommendation class/level,
- condition/action counts,
- OR/AND/numeric operator frequency,
- role mix (Condition/ClinicalParameter/Procedure/Medication),
- ambiguity label from human QA.

Then freeze a new versioned split (e.g., `split_v2`).

---

## 3) What to optimize (metrics hierarchy)

Use four metric layers and optimize in this order:

1. **Schema validity (must-pass)**
   - required fields present
   - enum/operator legality
   - side assignment consistency (condition vs action)

2. **Structure quality**
   - rule-level exact match (entity + logic fields)
   - logic-group correctness (`logic_group`, `logic_type`)
   - operator correctness (`PRESENT`, `PLANNED`, `<`, `>=`, etc.)

3. **Semantic extraction quality**
   - concept precision/recall/F1 by role
   - missing vs extra concept counts

4. **Grounding quality (separate track)**
   - grounding hit rate
   - correct target label mapping
   - root-hit correctness

Decision policy:
- Reject any candidate that hurts Layer 1 or causes >1% relative drop in Layer 2 on dev.
- Promote only if Layer 2 improves and Layer 3 does not regress materially.
- Use Layer 4 to tune grounding separately from extraction.

---

## 4) Error taxonomy (row-level labeling)

Annotate every mismatch into one primary class (and optional secondary class):

### A. Segmentation and rule framing
- `A1_split_fail`: one natural rule split into wrong number of rules
- `A2_merge_fail`: multiple rules merged into one
- `A3_side_assignment`: condition/action side misplaced

### B. Concept detection
- `B1_missing_concept`: expected concept absent
- `B2_extra_concept`: hallucinated concept
- `B3_span_normalization`: wrong canonical surface form (`entity` drift)
- `B4_role_misclass`: wrong role label

### C. Logic extraction
- `C1_operator_wrong`: wrong operator (`PLANNED` vs `PRESENT`, etc.)
- `C2_threshold_wrong`: wrong threshold value
- `C3_unit_wrong`: wrong/absent unit
- `C4_context_wrong`: condition context wrong/missing
- `C5_logic_type_wrong`: AND/OR wrong
- `C6_logic_group_wrong`: group linkage wrong

### D. Recommendation attributes
- `D1_class_wrong`: class-of-recommendation mismatch
- `D2_level_wrong`: level-of-evidence mismatch
- `D3_direction_wrong`: polarity mismatch

### E. Grounding and taxonomy
- `E1_grounding_miss`: no SNOMED grounding
- `E2_grounding_wrong_concept`: wrong concept chosen
- `E3_target_label_wrong`: mapped label mismatch
- `E4_taxonomy_root_wrong`: wrong root hit/path

### F. Schema and contract
- `F1_missing_required_field`
- `F2_invalid_enum_or_type`
- `F3_single_source_drift` (prompt/output no longer aligned with extraction contract)

Use this taxonomy in a running sheet and aggregate per iteration.

---

## 5) Recommended pipeline shape (for tuning)

Use deterministic multi-pass extraction before any agenting:

1. **Pass 1: Rule skeleton**
   - identify rule count
   - assign condition/action buckets
   - assign rule IDs

2. **Pass 2: Structured filling**
   - fill entity, role, operator/threshold/unit/context, logic fields, class/level/direction

3. **Pass 3: Deterministic validation/repair**
   - enforce schema contract and enums
   - repair only contract-level defects (no free semantic rewrite)

4. **Pass 4: SNOMED grounding (separate stage)**
   - run grounding after extraction
   - report grounding metrics separately

Why not “full agenting” now:
- lower reproducibility,
- harder attribution of improvements,
- higher variance in benchmark runs.

Add agenting only after extraction behavior is stable and test performance plateaus.

---

## 6) Prompt tuning protocol (anti-overfit)

For each iteration `k`:

1. Run full dev set.
2. Aggregate error counts by taxonomy class.
3. Select top 1–2 error classes only.
4. Apply minimal prompt/schema instruction changes targeting those classes.
5. Re-run full dev set.
6. If improved, checkpoint as `prompt_v{k+1}`.
7. Every 3 dev iterations, run locked test once.

Rules:
- Do not write row-specific prompt exceptions.
- Do not tune based on one row anecdote; require repeated class-level signal.
- Keep a changelog entry explaining hypothesis and observed effect.

---

## 7) Graph builder integration checklist

Use graph builder artifacts as first-class tuning evidence:

- Extraction output (`actual_entries`) for logic metrics.
- Display output (`actual_entries_display`) for per-rule debugging.
- Grounding summary for SNOMED-specific diagnostics.
- Rowwise CSV/JSON reports for trend tracking across iterations.

Per run, persist:
- model/node/port,
- extraction toggles (`LIVE_LLM`, grounding toggle),
- prompt version ID,
- schema contract version,
- git commit SHA.

Suggested run modes:
- **Dev mode**: only dev row IDs, frequent iterations.
- **Eval mode**: locked test IDs only, no prompt edits between runs.
- **Release mode**: full 19 rows for final benchmark snapshot.

---

## 8) Promotion criteria (when to move to next phase)

Move from prompt-tuning to model/architecture tuning only when:
- Dev rule-exact-match plateaus across 3 consecutive iterations.
- Locked test does not improve for 2 checkpoints.
- Remaining failures are concentrated in semantic ambiguity classes (`B3`, `C4`, `E2`) rather than contract failures.

At that point, consider:
- small supervised fine-tuning set (from manual annotations),
- constrained decoding strategies,
- retrieval augmentation for ontology disambiguation,
- optional agentic adjudication pass (kept outside benchmark core).

---

## 9) Manual-annotation integration plan

As manual annotations progress:

1. Add confidence and ambiguity tags per row/rule.
2. Reweight dev loss/priority by ambiguity.
3. Reserve highest-agreement rows for locked test.
4. Use lower-agreement rows as dev stress cases.
5. Rebaseline all metrics when annotation version increments.

Versioning recommendation:
- `table22_annotations_vX`
- `table22_split_vX`
- `prompt_vX`
- `pipeline_vX`

---

## 10) Implementation map (already established)

The following artifacts implement this playbook directly:

- Split manifest: `config/table22/split_v1.json`
- Error labeling template: `docs/table22_tuning_templates/error_taxonomy_template.csv`
- Iteration log template: `docs/table22_tuning_templates/iteration_log_template.md`

Execution uses the existing tracked runner:

- `slurm/run_table22_concept_rules_tests.sh`

Run-time behavior is controlled via env vars:

- `CARDIO_GRAPH_TABLE22_TARGET_ROWS`
- `CARDIO_GRAPH_TABLE22_RUN_TAG`
- `CARDIO_GRAPH_TABLE22_REPORT_MD`
- `CARDIO_GRAPH_TABLE22_REPORT_JSON`
- `CARDIO_GRAPH_TABLE22_REPORT_CSV`
- `CARDIO_GRAPH_TABLE22_ROWS_DIR`

Example output paths:
- `docs/table22_tuning_runs/dev/<RUN_TAG>/table22_rowwise_summary.csv`
- `docs/table22_tuning_runs/test/<RUN_TAG>/table22_rowwise_alignment.json`
- `docs/table22_tuning_runs/full/<RUN_TAG>/rows/row_XX.md`

## 11) Run commands

Submit dev iteration:

```bash
RUN_TAG=dev_$(date +%Y%m%d_%H%M%S)
OUT=docs/table22_tuning_runs/dev/$RUN_TAG
mkdir -p "$OUT/rows"
CARDIO_GRAPH_TABLE22_TARGET_ROWS="row_02,row_03,row_04,row_05,row_06,row_09,row_10,row_11,row_12,row_13,row_14,row_15,row_17" \
CARDIO_GRAPH_TABLE22_REPORT_MD="$OUT/table22_rowwise_comparison.md" \
CARDIO_GRAPH_TABLE22_REPORT_JSON="$OUT/table22_rowwise_alignment.json" \
CARDIO_GRAPH_TABLE22_REPORT_CSV="$OUT/table22_rowwise_summary.csv" \
CARDIO_GRAPH_TABLE22_ROWS_DIR="$OUT/rows" \
sbatch slurm/run_table22_concept_rules_tests.sh
```

Submit locked test checkpoint:

```bash
RUN_TAG=test_$(date +%Y%m%d_%H%M%S)
OUT=docs/table22_tuning_runs/test/$RUN_TAG
mkdir -p "$OUT/rows"
CARDIO_GRAPH_TABLE22_TARGET_ROWS="row_01,row_07,row_08,row_16,row_18,row_19" \
CARDIO_GRAPH_TABLE22_REPORT_MD="$OUT/table22_rowwise_comparison.md" \
CARDIO_GRAPH_TABLE22_REPORT_JSON="$OUT/table22_rowwise_alignment.json" \
CARDIO_GRAPH_TABLE22_REPORT_CSV="$OUT/table22_rowwise_summary.csv" \
CARDIO_GRAPH_TABLE22_ROWS_DIR="$OUT/rows" \
sbatch slurm/run_table22_concept_rules_tests.sh
```

Submit full benchmark snapshot:

```bash
RUN_TAG=full_$(date +%Y%m%d_%H%M%S)
OUT=docs/table22_tuning_runs/full/$RUN_TAG
mkdir -p "$OUT/rows"
CARDIO_GRAPH_TABLE22_TARGET_ROWS=' ' \
CARDIO_GRAPH_TABLE22_REPORT_MD="$OUT/table22_rowwise_comparison.md" \
CARDIO_GRAPH_TABLE22_REPORT_JSON="$OUT/table22_rowwise_alignment.json" \
CARDIO_GRAPH_TABLE22_REPORT_CSV="$OUT/table22_rowwise_summary.csv" \
CARDIO_GRAPH_TABLE22_ROWS_DIR="$OUT/rows" \
sbatch slurm/run_table22_concept_rules_tests.sh
```

Override defaults when needed (example):

```bash
CARDIO_GRAPH_TABLE22_LLM_MODEL=Qwen72b \
CARDIO_GRAPH_TABLE22_TARGET_ROWS="row_02,row_03,row_04,row_05,row_06,row_09,row_10,row_11,row_12,row_13,row_14,row_15,row_17" \
sbatch slurm/run_table22_concept_rules_tests.sh
```

## 12) Immediate operating loop

1. Run dev (command above with dev row list).
2. Label top errors using `docs/table22_tuning_templates/error_taxonomy_template.csv`.
3. Update prompt/pipeline for top 1–2 error classes.
4. Log changes in `docs/table22_tuning_templates/iteration_log_template.md`.
5. Every third dev iteration, run locked test.
6. Promote only on non-regressive locked-test checkpoints.

<!-- markdownlint-enable MD022 MD032 -->
