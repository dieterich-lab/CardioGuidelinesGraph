# Automated SNOMED Mapping Evaluation Milestone

Canonical tracker note:
- This file is the single source of truth for grounding-eval status, comparisons, and next-step decisions.
- Generated files under `docs/generated/grounding/` are treated as raw artifacts, not decision trackers.

## Update 2026-04-13 (cardio-subset vector DB)

New completed run:
- `630319` (GT3: tables 22/8/17, `233` items)
- overall accuracy: `0.510730` (`119/233`)
- rank metrics: `MRR=0.561925`, `mean_gt_rank=1.2828`, `median_gt_rank=1`

Pre-cardio comparison (same GT3 evaluation family, previous full-space index window):
- Reference pre-cardio run (same `vector_context_enabled=false` profile): `628367`
	- overall: `0.530435` (`122/230`)
	- delta vs new (`630319`): `-0.019705` overall
- Role deltas (`630319 - 628367`):
	- `Procedure`: `+0.159420` (`0.275 -> 0.435`)
	- `ClinicalCondition`: `-0.117842` (`0.654 -> 0.536`)
	- `Medication`: `-0.068182` (`0.523 -> 0.455`)
	- `ClinicalParameter`: `0.000000` (`1.000 -> 1.000`)

Interpretation:
- The cardio-subset run improved Procedure grounding substantially.
- Overall accuracy still trailed the best pre-cardio GT3 run because ClinicalCondition and Medication regressions outweighed Procedure gains.
- This suggests retrieval-space narrowing helped procedure semantics but did not yet resolve condition/medication disambiguation behavior.

Immediate analysis focus for next tuning cycle:
1. Keep cardio-subset index as baseline retrieval space.
2. Target ClinicalCondition confusion pairs (`Use of anticoagulation`, `Indication of`, `Myocardial ischemia`) with stricter role/semantic penalties.
3. Target Medication false-nearest neighbors (`Aspirin -> Aluminium aspirin`, empty fallback on `Drug therapy with explicit context`).

Runs analyzed: 627576, 627880, 628092, 628305, 628306

Criterion: term-role pairs that missed in at least 2 analyzed runs.

## Latest Run Gate

- Latest run 628306 accuracy: 0.535714 (45/84)
- 0.60 gate: FAILED
- Companion run 628305 accuracy: 0.619048 (52/84) -> PASSED 0.60 gate

## Top Persistent Error Terms

Note: table below is the pre-reduced-knob persistent set (runs 627576, 627880, 628092). The latest two runs are summarized in the findings and next-run plan below.

| Rank | Term | Role | Runs Missed | Misses (analyzed runs) | Typical Wrong Prediction IDs | Example Rows |
|---:|---|---|---|---:|---|---|
| 1 | Intracoronary pressure guide wire | Procedure | 627576, 627880, 628092 | 9 | <empty>, 431558000, 53178003 | t0_row_17, t0_row_18, t0_row_19 |
| 2 | Percutaneous coronary revascularization | Procedure | 627576, 627880, 628092 | 9 | 713617008 | t0_row_01, t0_row_11, t0_row_16 |
| 3 | Using decision making strategies | Procedure | 627576, 627880, 628092 | 9 | <empty>, 133920001 | t0_row_01, t0_row_04, t0_row_13 |
| 4 | Preferences | Procedure | 627576, 627880, 628092 | 6 | 223486007 | t0_row_04, t1_row_01 |
| 5 | High risk | ClinicalCondition | 627576, 627880, 628092 | 3 | 455201601000132100 | t0_row_11 |
| 6 | Inoperable | ClinicalCondition | 627576, 627880, 628092 | 3 | <empty> | t0_row_11 |
| 7 | Lesion | ClinicalCondition | 627576, 627880, 628092 | 3 | 300513000 | t0_row_16 |
| 8 | Medical therapy | ClinicalCondition | 627576, 627880, 628092 | 3 | 425914008 | t0_row_12 |
| 9 | Myocardial revascularization | ClinicalCondition | 627576, 627880, 628092 | 3 | 57809008 | t0_row_13 |
| 10 | Specialist multidisciplinary team | ClinicalCondition | 627576, 627880, 628092 | 3 | 268528005, <empty> | t0_row_05 |
| 11 | Assessment score | Procedure | 627576, 627880, 628092 | 3 | 1003700002 | t0_row_15 |
| 12 | Coronary artery structure | Procedure | 627576, 627880, 628092 | 3 | 294002 | t1_row_01 |
| 13 | Decision making | Procedure | 627576, 627880, 628092 | 3 | 133920001 | t0_row_09 |
| 14 | General characteristic of patient | Procedure | 627576, 627880, 628092 | 3 | 7922000, 162673000 | t1_row_01 |
| 15 | Health literacy | Procedure | 627576, 627880, 628092 | 3 | 431531000124101 | t0_row_04 |

## Role-Level Accuracy Trend

| Run | ClinicalCondition | ClinicalParameter | Procedure | Overall |
|---|---:|---:|---:|---:|
| 627576 | 0.793 | 1.000 | 0.551 | 0.667 |
| 627880 | 0.793 | 1.000 | 0.551 | 0.667 |
| 628092 | 0.759 | 1.000 | 0.347 | 0.536 |
| 628305 | 0.759 | 1.000 | 0.490 | 0.619 |
| 628306 | 0.517 | 1.000 | 0.490 | 0.536 |

## Latest Findings (2026-03-25)

- Current best still remains 627576/627880 (overall 0.667).
- Run 628305 recovered from 0.536 to 0.619 (+7 hits; 45 -> 52) and passed the 0.60 gate.
- Run 628306 regressed back to 0.536 (45/84), with Procedure unchanged vs 628305 (0.490) but a sharp ClinicalCondition drop (0.759 -> 0.517).
- Miss overlap between 628305 and 628306 is high (27 shared misses), indicating the core Procedure miss set remains mostly stable.
- New misses in 628306 are dominated by ClinicalCondition confusions (for example multivessel CAD and left main stem stenosis mappings), suggesting instability in condition-side disambiguation rather than a broad retrieval outage.

Generated milestone/manifest snapshots are written to `docs/generated/grounding/`.
Raw shared ground-truth evaluation runs are stored under
`docs/generated/ground_truth/grounding_only/`.

## Frozen Baseline Knobs (A Arm)

These are now fixed as script defaults in both vector wrappers and represent Arm A:

- `CARDIO_GRAPH_GROUNDING_VECTOR_RERANK_WEIGHT=0.03`
- `CARDIO_GRAPH_GROUNDING_VECTOR_BONUS_CAP=0.05`
- `CARDIO_GRAPH_GROUNDING_VECTOR_MIN_LEXICAL_FOR_BONUS=0.90`
- `CARDIO_GRAPH_GROUNDING_MIN_WEIGHTED_QUERY_COVERAGE=0.45`
- `CARDIO_GRAPH_GROUNDING_LOW_COVERAGE_PENALTY=0.12`
- `CARDIO_GRAPH_GROUNDING_MISSING_DISCRIMINATIVE_PENALTY=0.10`
- `CARDIO_GRAPH_GROUNDING_EXTRA_QUALIFIER_PENALTY=0.10`
- `CARDIO_GRAPH_GROUNDING_GUARDED_FALLBACK_MARGIN=0.015`
- `CARDIO_GRAPH_GROUNDING_MIN_DISCRIMINATIVE_COVERAGE_FOR_TOP=0.60`
- `CARDIO_GRAPH_GROUNDING_HARD_NEGATIVE_PENALTY=0.0`
- `CARDIO_GRAPH_GROUNDING_AMBIGUITY_ABSTAIN_MARGIN=0.012`
- `CARDIO_GRAPH_GROUNDING_AMBIGUITY_MIN_COVERAGE=0.55`
- `CARDIO_GRAPH_GROUNDING_AMBIGUITY_CONFIDENCE_BACKOFF_ENABLED=true`
- `CARDIO_GRAPH_GROUNDING_AMBIGUITY_BACKOFF_MAX_DROP=0.05`
- `CARDIO_GRAPH_GROUNDING_AMBIGUITY_BACKOFF_MIN_SCORE=0.35`
- `CARDIO_GRAPH_GROUNDING_ROLE_SOFT_CONSTRAINTS=true`
- `CARDIO_GRAPH_GROUNDING_ROLE_MISMATCH_PENALTY=0.05`
- `CARDIO_GRAPH_GROUNDING_ROLE_TENSION_PENALTY=0.02`
- `CARDIO_GRAPH_GROUNDING_ROLE_SEMANTIC_MISMATCH_PENALTY=0.06`
- `CARDIO_GRAPH_GROUNDING_ROLE_SEMANTIC_CROSSCLASS_PENALTY=0.02`
- `CARDIO_GRAPH_GROUNDING_AMBIGUITY_LEXICAL_FORCE_PICK=0.90`
- `CARDIO_GRAPH_GROUNDING_VECTOR_CONTEXT_ENABLED=false`
- `CARDIO_GRAPH_GROUNDING_VECTOR_CONTEXT_ALLOWED_ROLES=Procedure`
- `CARDIO_GRAPH_GROUNDING_VECTOR_CONTEXT_APPEND_TERM=false`
- `CARDIO_GRAPH_GROUNDING_VECTOR_CONTEXT_MAX_TOKENS=8`

## Near-Hardcoded Knob Analysis

Current runtime behavior is effectively controlled by launcher defaults in [slurm/gt-eval-vector.sbatch](slurm/gt-eval-vector.sbatch), even though each variable can still be overridden via `--export`.

Near-hardcoded in practice (defaulted every run unless explicitly overridden):

- Vector rerank and lexical gate trio: `VECTOR_RERANK_WEIGHT`, `VECTOR_BONUS_CAP`, `VECTOR_MIN_LEXICAL_FOR_BONUS`.
- Coverage and qualifier penalties: `MIN_WEIGHTED_QUERY_COVERAGE`, `LOW_COVERAGE_PENALTY`, `MISSING_DISCRIMINATIVE_PENALTY`, `EXTRA_QUALIFIER_PENALTY`.
- Ambiguity bundle: `AMBIGUITY_ABSTAIN_MARGIN`, `AMBIGUITY_MIN_COVERAGE`, `AMBIGUITY_CONFIDENCE_BACKOFF_ENABLED`, `AMBIGUITY_BACKOFF_MAX_DROP`, `AMBIGUITY_BACKOFF_MIN_SCORE`, `AMBIGUITY_LEXICAL_FORCE_PICK`.
- Role penalties: `ROLE_MISMATCH_PENALTY`, `ROLE_TENSION_PENALTY`, `ROLE_SEMANTIC_MISMATCH_PENALTY`, `ROLE_SEMANTIC_CROSSCLASS_PENALTY`.

Not hardcoded (already safely off by default):

- `CARDIO_GRAPH_GROUNDING_HARD_NEGATIVE_PENALTY=0.0`
- `CARDIO_GRAPH_GROUNDING_HARD_NEGATIVE_MANIFEST` empty

Decision from latest evidence:

- Reduced-knob variants (628305/628306) are not promoted over the stable baseline (627576/627880 at 0.667).
- Context-sensitive search proceeds only as controlled A/B against frozen baseline and now uses a conservative scope (`Procedure` only, no `term + context` concatenation by default).

## A/B Experiment Definition

- Arm A (baseline): frozen knobs above, context vector query disabled.
- Arm B (context-aware): identical knobs, enable context query via `CARDIO_GRAPH_GROUNDING_VECTOR_CONTEXT_ENABLED=true`.
- Success criteria: non-negative overall delta vs Arm A and Procedure accuracy improvement without large ClinicalCondition regressions.

## Prospected Next Runs

- Re-run Arm A once (same settings as 628305) as a reproducibility check; only promote if overall remains >= 0.60 and ClinicalCondition >= 0.70.
- Run Arm B once with context enabled and all other knobs frozen; compare directly against Arm A on the same node/model window.
- If Arm B improves Procedure without ClinicalCondition collapse, run one confirmation replicate before promoting.
- Keep a focused error watchlist for recurring Procedure misses: Intracoronary pressure guide wire, Percutaneous coronary revascularization, Using decision making strategies.
- If ClinicalCondition drift reappears, test a stricter condition-side disambiguation variant before changing retrieval settings.

## Overnight Ablation Chain (2026-04-13)

Reference baseline run (A):
- `630319` (completed prior to the chain)

Sequential queue submitted via Slurm dependency (`afterok`) using `slurm/gt-eval-vector.sbatch`:

| Arm | Job ID | Dependency | Log file | Status/Result |
|---|---:|---|---|---|
| B | `630455` | none | `slurm/gt-eval-B_630455.log` | pending update |
| C | `630456` | `afterok:630455` | `slurm/gt-eval-C_630456.log` | pending update |
| D | `630457` | `afterok:630456` | `slurm/gt-eval-D_630457.log` | pending update |
| E | `630458` | `afterok:630457` | `slurm/gt-eval-E_630458.log` | pending update |
| F | `630459` | `afterok:630458` | `slurm/gt-eval-F_630459.log` | pending update |
| G | `630460` | `afterok:630459` | `slurm/gt-eval-G_630460.log` | pending update |

Exact knob overrides per arm (`sbatch --export=ALL,...`):

Arm B (stronger semantic-role penalties):
- `CARDIO_GRAPH_GROUNDING_ROLE_MISMATCH_PENALTY=0.08`
- `CARDIO_GRAPH_GROUNDING_ROLE_TENSION_PENALTY=0.03`
- `CARDIO_GRAPH_GROUNDING_ROLE_SEMANTIC_MISMATCH_PENALTY=0.10`
- `CARDIO_GRAPH_GROUNDING_ROLE_SEMANTIC_CROSSCLASS_PENALTY=0.04`

Arm C (lexical-first medication precision guard):
- `CARDIO_GRAPH_GROUNDING_VECTOR_RERANK_WEIGHT=0.02`
- `CARDIO_GRAPH_GROUNDING_VECTOR_BONUS_CAP=0.03`
- `CARDIO_GRAPH_GROUNDING_VECTOR_MIN_LEXICAL_FOR_BONUS=0.94`
- `CARDIO_GRAPH_GROUNDING_AMBIGUITY_LEXICAL_FORCE_PICK=0.94`

Arm D (stronger over-qualification/discriminative penalties):
- `CARDIO_GRAPH_GROUNDING_EXTRA_QUALIFIER_PENALTY=0.16`
- `CARDIO_GRAPH_GROUNDING_MISSING_DISCRIMINATIVE_PENALTY=0.14`
- `CARDIO_GRAPH_GROUNDING_MIN_DISCRIMINATIVE_COVERAGE_FOR_TOP=0.70`

Arm E (condition disambiguation via stricter coverage/fallback):
- `CARDIO_GRAPH_GROUNDING_MIN_WEIGHTED_QUERY_COVERAGE=0.55`
- `CARDIO_GRAPH_GROUNDING_LOW_COVERAGE_PENALTY=0.16`
- `CARDIO_GRAPH_GROUNDING_GUARDED_FALLBACK_MARGIN=0.025`

Arm F (tighter ambiguity handling):
- `CARDIO_GRAPH_GROUNDING_AMBIGUITY_ABSTAIN_MARGIN=0.025`
- `CARDIO_GRAPH_GROUNDING_AMBIGUITY_MIN_COVERAGE=0.65`
- `CARDIO_GRAPH_GROUNDING_AMBIGUITY_BACKOFF_MAX_DROP=0.08`
- `CARDIO_GRAPH_GROUNDING_AMBIGUITY_BACKOFF_MIN_SCORE=0.45`

Arm G (controlled context-aware vector expansion):
- `CARDIO_GRAPH_GROUNDING_VECTOR_CONTEXT_ENABLED=true`
- `CARDIO_GRAPH_GROUNDING_VECTOR_CONTEXT_ALLOWED_ROLES=Procedure:ClinicalCondition`
- `CARDIO_GRAPH_GROUNDING_VECTOR_CONTEXT_APPEND_TERM=true`
- `CARDIO_GRAPH_GROUNDING_VECTOR_CONTEXT_MAX_TOKENS=10`

Traceability note:
- The per-job log headers print many active knobs, and this section is the canonical record of the exact submitted override set.