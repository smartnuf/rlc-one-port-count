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
  `max_edges=8`, the phase-2 raw simple-bundle assignment table and
  `1,166,714` leaf total, the phase-3 canonical bundle-labeling table with total `830,094`, and the current legacy `lc` and `generic` count
  tables.
- The reduced-model `R <= 2`, `L+C <= 3` golden output is now stored in `data/counts/small-r2-x3.json` and tested for exact equality against CLI JSON so the documented regeneration command can be diffed without post-processing. The no-argument `rice reduced` path defaults to this fast golden slice. Ladenheim golden outputs have not yet been generated.

## Near-term next steps

1. Add Ladenheim-slice golden counts only after the reduced distinctness contract
   is implemented enough to make those counts meaningful.
2. Keep any future reduced-model golden artifacts regenerable from documented
   commands without manual post-processing.
