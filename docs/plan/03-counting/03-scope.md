# 03-counting / 03 — Set enumeration scope: `R <= 3`, `L+C <= 5`

Status: `prog`

## Goal

Set the main enumeration target correctly.

## Correct scope

The planned counting scope is:

```text
R <= 3
L + C <= 5
```

That means up to three resistors and up to five reactive elements in total, where each reactive element is either an inductor or a capacitor.

This is not a request to count separate 3-element and 5-element networks. The `3` and `5` are independent upper bounds on element classes.

## Count grid

The full planned grid is:

```text
R count:      0, 1, 2, 3
L+C count:    0, 1, 2, 3, 4, 5
```

Before including degenerate cases in final tables, decide whether entries with no resistors, no reactive elements, or very small total element counts are useful or should be reported separately.

## Reactive assignments

For each reactive count `N = L+C`, counts may need to be split by `(L, C)` composition:

```text
N = 0: (L=0, C=0)
N = 1: (1,0), (0,1)
N = 2: (2,0), (1,1), (0,2)
...
N = 5: (5,0), (4,1), (3,2), (2,3), (1,4), (0,5)
```

## Done means

- The code accepts the scope as independent bounds on `R` and `L+C`.
- Count tables clearly label rows/columns as `R` and `L+C`.
- Tests cover boundary values, especially `R=3` and `L+C=5`.

## Progress notes

- The `supports`, `bundles`, `labelings`, and `reduced` subcommands each
  accept independent `--max-r` and `--max-reactive` bounds and label the
  reactive column as `L+C`. The legacy count path that previously accepted
  these same bounds under a `--mode lc`/`--mode generic` split has been
  removed in full (`docs/plan/02-cleanup/02-legacy.md`).
- `make check` validates the phase-1/2/3 censuses at the full `R <= 3`,
  `L+C <= 5` scope and the end-to-end reduced-topology census at the small
  golden `R <= 2`, `L+C <= 3` slice. The legacy multiset-bundle totals it used
  to validate are no longer part of `make check`; they are recorded only as
  historical data in `docs/results.md`.
- The support-census command validates support-edge counts through
  `max_edges=8`, which is the support bound for the current full scope.
- The phase-2 `rice bundles` census now uses `--max-r` and `--max-reactive`
  as the normal interface, derives the natural support bound from those budgets,
  and tests the default `R <= 3`, `L+C <= 5` raw assignment-leaf total.

## Near-term next steps

1. Decide how degenerate rows or columns should be reported in reduced-model
   output tables once the full `R <= 3`, `L+C <= 5` reduced-topology census is
   computed (`docs/plan/05-slices/04-r3-x5.md`).
