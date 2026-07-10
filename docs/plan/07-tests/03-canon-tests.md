# 07-tests / 03 — Descriptor and canonicalisation tests

Status: `prog`

## Goal

Ensure duplicate rejection and descriptor production are trustworthy.

## Tasks

- Test canonicalisation under internal node renaming and terminal-pair reversal.
- Test simple primitive bundle-label preservation.
- Test series/parallel normalisation where applicable.
- Test bridge/non-series-parallel examples separately.
- Test that descriptor output is stable.

## Done means

- Equivalent networks collapse to the same canonical representative where intended.
- Non-equivalent networks do not collapse accidentally.
- Descriptor output is deterministic.


## Progress notes

- Added focused phase-3 assigned-support canonicalisation tests covering single-edge supports, terminal-path reversal, asymmetric terminal-labelled supports, exclusion of automorphisms that do not preserve the terminal set, explicit terminal-swapping automorphisms, budget accounting over edge cycles, and brute-force cross-checks for small supports.
- Added focused local series/parallel reduction tests for primitive duplicate
  merging, compound duplicate preservation, terminal reversal, internal node
  renaming, series arms inside parallel networks, repeated reduction,
  non-series-parallel bridge/core stability, non-collision examples, mixed-type
  hashable node labels on the reduced-signature validation path, duplicate
  oriented assignment-key rejection, recursive caller-supplied ReducedFactor
  validation/normalisation, and malformed or terminal-irrelevant input
  rejection.
- 2026-07-10: Full census integration is implemented and tested
  (`tests/test_reduced_census.py`) for the committed small golden slice
  `R <= 2`, `L+C <= 3`, including determinism, no-duplicate-signature checks,
  and API/CLI/committed-JSON agreement. Extending that integration test
  coverage to the full standard `R <= 3`, `L+C <= 5` slice, and
  descriptor-output tests, remain future work
  (`docs/plan/05-slices/04-r3-x5.md`, `docs/plan/09-later/04-descriptors.md`).
