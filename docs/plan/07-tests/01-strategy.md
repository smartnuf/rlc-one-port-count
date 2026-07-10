# 07-tests / 01 — Test strategy for enumeration

Status: `prog`

## Goal

Build confidence while the enumeration machinery evolves.

## Test layers

1. Unit tests for graph validity checks.
2. Unit tests for edge colouring and R/L/C composition constraints.
3. Canonicalisation tests using hand-known isomorphic examples.
4. Descriptor conversion tests.
5. Golden-count tests for small scopes.
6. Regression tests for known catalogue slices.
7. Slow/full tests for the complete `R <= 3`, `L+C <= 5` scope.

## Done means

- Fast tests run by default.
- Slow enumeration tests are available but clearly marked.
- CI and local commands agree.

## Progress notes

- Fast tests currently cover the phase-1 support census, terminal-pair reversal,
  dangling branch rejection, pendant blob rejection, and positive terminal
  relevance examples.
- CLI tests cover the four surviving subcommands with top-level option
  preservation.
- 2026-07-10: The legacy multiset-bundle counter (`lc` and previously
  `generic` modes, `rice count`, the no-subcommand form) has been removed in
  full (`docs/plan/02-cleanup/02-legacy.md`, following
  `docs/plan/02-cleanup/03-generic-x.md`). Its historical golden tables are
  no longer live regression tests; they are recorded, clearly labelled as
  historical, in `docs/results.md`.
- 2026-07-10: Assigned-support canonicalisation (`tests/test_bundle_labelings.py`),
  local series/parallel reduced-signature normalisation
  (`tests/test_reduced_signatures.py`), and small-slice end-to-end census
  integration (`tests/test_reduced_census.py`) all have substantial test
  coverage now, including all the boundary cases listed in `AGENTS.md`.
  Descriptor conversion tests, and full standard-slice (`R <= 3`, `L+C <= 5`)
  regression tests, have not started — that is the remaining reason this
  strategy stays `prog` rather than `done`.

## Near-term next steps

1. Add descriptor-conversion tests once a descriptor output format exists
   (`docs/plan/09-later/04-descriptors.md`).
2. Add full-standard-slice (`R <= 3`, `L+C <= 5`) regression tests once that
   slice is computed (`docs/plan/05-slices/04-r3-x5.md`).
