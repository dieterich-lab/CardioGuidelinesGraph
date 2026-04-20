# Grounding Pipeline (Conceptual Overview)

This document explains the grounding algorithm.

## Goal

Given a clinical phrase and its semantic role (for example, condition, procedure, or medication), the system chooses the most plausible SNOMED CT concept.

Formally, for each mention $m$ with role $r$, grounding selects:

$$
\hat{c} = \arg\max_{c \in C(m)} S(c \mid m, r, x)
$$

where:

- $C(m)$ is the candidate set
- $x$ is optional context
- $S$ is a composite score balancing evidence and penalties

## End-to-End Algorithm

## 1. Input normalization and query expansion

The input phrase is normalized (case, punctuation, morphology), then expanded into multiple query variants.

Typical variants include:

- original phrase
- simplified phrase (for long or parenthetical forms)
- lexical variants and abbreviations
- context-informed variants (when context is available and useful)

Purpose:

- improve recall at candidate retrieval
- preserve clinically relevant tokens
- reduce brittleness to surface form changes

## 2. Candidate retrieval

Candidates are gathered from two complementary channels:

- lexical retrieval: candidates matching string/token structure
- semantic retrieval: candidates near the mention in representation space

The two channels are merged into one candidate pool before ranking.

## 3. Role-aware and domain-aware filtering

Before detailed ranking, candidates are constrained by medical plausibility rules.

Key filters:

- domain-root compatibility: keep concepts in the expected ontology region for the role (example: for a Procedure mention, prioritize candidates that live in procedural branches of the ontology rather than condition-only branches)
- semantic-tag compatibility: discourage or exclude incompatible semantic classes (example: if the mention is a medication, concepts tagged like finding or body structure should be strongly down-weighted or rejected)
- minimum token-overlap sanity checks: remove candidates with no meaningful lexical overlap (example: a candidate that shares only very generic words like heart or disease but misses the core phrase content is filtered out)

### Where this filter information comes from

- Semantic tag source:
  - The tag is read from the SNOMED preferred term string, typically in the trailing parenthetical form, for example `myocardial infarction (disorder)`.
  - Conceptually, the algorithm extracts the part in parentheses and uses it as the candidate semantic class.

- Domain-root source:
  - Each clinical role (for example, Procedure, Medication, ClinicalCondition) is associated with one or more SNOMED root regions.
  - A candidate is considered domain-compatible when its taxonomy ancestry intersects with the allowed root region for that role.

- Why both are used:
  - Semantic tags provide a local class check at the concept-name level.
  - Domain-root checks provide a structural ontology-level check.
  - Together, they reduce both obvious class mismatches and deeper hierarchy mismatches.

This stage controls gross category errors (for example, selecting a finding where a procedure is expected).

## 4. Evidence scoring per candidate

Each remaining candidate receives evidence from multiple signals:

- lexical similarity (example: `myocardial infarction` should score closer to concepts explicitly containing `myocardial infarction` than to loosely related findings)
- weighted token coverage (example: for `percutaneous coronary revascularization`, a candidate covering all three core tokens should outrank one matching only `coronary`)
- discriminative token coverage (rare or highly informative tokens; example: tokens like `supravalvar` or `papillary` should strongly favor candidates that contain them)
- semantic retrieval support (example: paraphrases such as `heart attack` can still support `myocardial infarction` even when literal token overlap is incomplete)

These components produce a base plausibility estimate.

## 5. Structured penalties

The model then applies penalties for known failure modes.

Major penalty families:

- role mismatch penalty
- semantic-class mismatch penalty
- low-coverage penalty
- missing-discriminative-token penalty (example: if the query includes `supravalvar` but the candidate omits it, confidence drops)
- overspecificity/extra-qualifier penalty (example: penalize choosing a very specific subtype when the mention is broad, such as mapping a general revascularization phrase to a narrow procedural variant)
- hard-negative penalty for repeatedly wrong concept choices

Conceptually:

$$
S(c) = E(c) + V(c) - P(c)
$$

with:

- $E(c)$ lexical and coverage evidence
- $V(c)$ semantic/vector support bonus
- $P(c)$ sum of penalties

## 6. Tie handling and ambiguity control

When top candidates are very close, the system applies guarded rules rather than always taking top-1 blindly.

Typical ambiguity logic:

- abstain or back off when confidence is low and near-ties exist
- prefer candidates with better discriminative coverage under small score gaps (example: if two candidates are nearly tied, prefer the one that preserves the key distinguishing token from the query)
- allow conservative reranking only in narrowly defined near-tie conditions

This reduces unstable picks caused by superficial score noise.

## 7. Optional deterministic rescue layer

A separate override layer can map specific term+role pairs to fixed concepts.

Important principle:

- scientific evaluation and production optimization are treated as separate tracks
- overrides are used for operational stability, not to inflate unbiased scientific estimates

## 8. Final output

For each mention, the system returns:

- predicted concept (or abstain)
- confidence score
- ranked alternatives
- diagnostic traces explaining where evidence or filtering changed the outcome

## Why this pipeline is structured this way

The design addresses three common grounding tensions:

- Recall vs precision:
  - broad retrieval increases coverage, while filtering and penalties recover precision.
- Semantic flexibility vs ontological validity:
  - semantic similarity helps with paraphrases, while role/domain constraints preserve clinical correctness.
- Determinism vs adaptability:
  - deterministic rescue can stabilize recurrent errors, while the core scorer remains general.

## Typical error classes (and corresponding controls)

- Overspecific prediction:
  - controlled by extra-qualifier and discriminative-coverage logic.
- Cross-role/cross-class prediction:
  - controlled by role and semantic-tag penalties or filters.
- Near-tie instability:
  - controlled by ambiguity backoff and guarded reranking.
- Recurrent known confusions:
  - controlled by hard negatives or deterministic overrides.

## Evaluation philosophy

Evaluation emphasizes exact concept correctness while also tracking rank-sensitive behavior.

Common quality views:

- top-1 exact accuracy
- hit@k
- mean reciprocal rank
- GT-rank diagnostics (where the gold concept appears in the candidate list)
- stage-level diagnostics (where gold concepts are filtered or lost)

To prevent leakage, model development and policy derivation are separated from locked evaluation.

## Summary

At a high level, grounding is a constrained ranking problem:

1. retrieve broadly
2. filter clinically implausible candidates
3. rank with multi-signal evidence
4. penalize known failure patterns
5. resolve ambiguity conservatively
6. optionally apply deterministic corrections in a separate production track

This yields a system that is both semantically flexible and clinically disciplined.