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
- 2026-04-10: 200-sample audit created in `docs/trackers/grounding/cardio_subset_sample_audit_200.json`.
  - Proxy sensitivity: `0.85`
  - Proxy specificity: `0.97`
  - Gold coverage (T22/T17/T8): `69/69`.
  - Main FN cluster: myocarditis/pericarditis variants and valvular variants.

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
| 2026-04-10 | `slurm/generate-cardio-subset.sbatch` | `seed_mode=both parent=0 child=1` | running (job `629771`) | cycle 2026-04-10-A |

## Next Update Checklist
1. Record Slurm job ID and completion state.
2. Capture subset size and GT coverage from log.
3. Re-run 200-sample audit and compare metrics deltas.
4. Decide keep/revert/adjust seed terms.
