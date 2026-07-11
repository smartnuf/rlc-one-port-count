# 07-tests / 02 — Golden-count tests

Status: `prog`

## Goal

Use stable generated counts to detect accidental changes.

## Initial golden targets

- Very small hand-checkable cases.
- Explicit subset: `R <= 2`, `L+C <= 3`.
- Ladenheim structural slice: `R+L+C <= 5` and `L+C <= 2`, including the
  four-resistor/one-reactive cases present in the historical 148 starting set.
- Ladenheim 108 comparison budget: `R <= 3`, `L+C <= 2`, and `R+L+C <= 5`.

## Done means

- Golden counts are stored in machine-readable form.
- Tests fail when counts change unexpectedly.
- There is a documented process for intentionally updating golden counts.

## Progress notes

- Golden tests now exist for the phase-1 support-census table through
  `max_edges=8`, the phase-2 raw simple-bundle assignment table and
  `1,166,714` leaf total, and the phase-3 canonical bundle-labeling table with
  total `830,094`. The legacy multiset-bundle counter (both its `lc` and
  previously-removed `generic` modes) has been removed in full
  (`docs/plan/02-cleanup/02-legacy.md`, following
  `docs/plan/02-cleanup/03-generic-x.md`); its historical totals are recorded
  only as a labelled historical citation in `docs/results.md`, not as a live
  golden test.
- The reduced-model `R <= 2`, `L+C <= 3` golden output is now stored in `data/counts/small-r2-x3.json` and tested for exact equality against CLI JSON so the documented regeneration command can be diffed without post-processing. The no-argument `rice reduced` path defaults to this fast golden slice. Ladenheim golden outputs have not yet been generated.

## Near-term next steps

1. Add Ladenheim-slice golden counts only after the 148 structural contract,
   colour-preserving 2-isomorphism signature, and comparison fixtures are
   implemented.
2. Keep any future reduced-model golden artifacts regenerable from documented
   commands without manual post-processing.
