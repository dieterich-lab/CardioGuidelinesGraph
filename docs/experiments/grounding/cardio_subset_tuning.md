# Cardio Subset Tuning Tracker

## Goal
Track all tuning decisions for SNOMED cardiology subset generation until grounding quality is stable enough for production use.

## Scope
- Generator: `generate-cardio-subset`
- Slurm launcher: `slurm/generate-cardio-subset.sbatch`
- Artifacts:
  - `/prj/doctoral_letters/guide/data/ontologies/cardio_subset_concept_ids.json`
  - `/prj/doctoral_letters/guide/data/ontologies/cardio_subset_candidates.json`

## Fixed Decisions (Current)
- Seed mode: `both` (lexical terms + GT seeds from table 22/17/8)
- Expansion depths: `parent=0`, `child=1`
- Rationale: parent expansion introduced broad ontology drift/noise; child-only preserved GT coverage while keeping specificity high.

## Historical Notes
- 2026-04-09: pruned noisy lexical terms from config (`cardiac`, `failure`, `pericard`, `pacemaker`, `transplant`, `depression`, `death`, `ESC`, `AF`) via commit `ecab2c6`.
- 2026-04-10: baseline 200-sample audit created in `docs/experiments/grounding/cardio_subset_sample_audit_200.json` before recall recovery.
  - Proxy sensitivity: `0.85`
  - Proxy specificity: `0.97`
  - Gold coverage (T22/T17/T8): `69/69`.
  - Main FN cluster: myocarditis/pericarditis variants and valvular variants.
- 2026-04-10: post-recall-recovery run completed and same 200-sample audit repeated.
  - Proxy sensitivity: `0.98`
  - Proxy specificity: `0.97`
  - Gold coverage (T22/T17/T8): `69/69`.
  - Net effect: substantial recall gain with no observed specificity loss in the same audit setup.

## Active Tuning Cycle
### Cycle 2026-04-10-A
- Change type: controlled recall recovery (lexical seed additions)
- Added seed terms:
  - `pericarditis`
  - `myocarditis`
  - `aortic stenosis`
  - `mitral regurgitation`
  - `papillary muscle`
  - `supravalvar`
- Guardrails:
  - keep `parent=0`, `child=1`
  - no change to GT seed paths
  - re-run 200-sample audit after generation

## Run Log
| Date | Run trigger | Key params | Result | Notes |
|---|---|---|---|---|
| 2026-04-10 | `slurm/generate-cardio-subset.sbatch` | `seed_mode=both parent=0 child=1` | completed (job `629771`) | subset size `19,218`; seed term IDs `10,699`; GT coverage `69/69 (100%)` |

## Decision
- **Keep** the added recall-recovery seeds for now.
- Reason: proxy sensitivity improved from `0.85` to `0.98`, while proxy specificity stayed at `0.97` and GT coverage remained `100%`.

## Next Update Checklist
1. Validate whether the improved subset translates into better grounding precision in the downstream vector/graph-construction pipeline.
2. If off-domain grounding errors rise, inspect whether `papillary muscle` / `supravalvar` introduced noisy neighborhoods.
3. Otherwise keep this subset as the new working baseline and continue tracking only downstream impact.
4. Add one larger audit sample later (e.g. 500) if we want tighter confidence on specificity stability.
