# 07-tests / 02 — Golden-count tests

Status: `prog`

## Goal

Use stable generated counts to detect accidental changes.

## Initial golden targets

- Very small hand-checkable cases.
- Explicit subset: `R <= 2`, `L+C <= 3`.
- Ladenheim comparison slice: `R <= 3`, `L+C <= 2`, and `R+L+C <= 5`,
  including the `R=3`, `L+C=2` boundary.

## Done means

- Golden counts are stored in machine-readable form.
- Tests fail when counts change unexpectedly.
- There is a documented process for intentionally updating golden counts.

## Progress notes

- Golden tests now exist for the phase-1 support-census table through
  `max_edges=8` and for the current legacy `lc` and `generic` count tables.
- These tests are in source form rather than stored external machine-readable
  artefacts, and reduced-model small-slice/Ladenheim golden outputs have not yet
  been generated.

## Near-term next steps

1. Add golden tests for phase-2 raw simple-bundle leaf assignments.
2. Create a documented update process before moving generated reduced-model
   counts into data files.
3. Add small-slice and Ladenheim-slice golden counts only after the reduced
   distinctness contract is implemented enough to make those counts meaningful.
