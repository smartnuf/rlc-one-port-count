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
- Edge-colouring, assigned-support canonicalisation, descriptor conversion, and
  reduced-signature tests have not started, so the strategy remains `prog`.
- 2026-07-10: The legacy multiset-bundle counter (`lc` and previously
  `generic` modes, `rice count`, the no-subcommand form) has been removed in
  full (`docs/plan/02-cleanup/02-legacy.md`, following
  `docs/plan/02-cleanup/03-generic-x.md`). Its historical golden tables are
  no longer live regression tests; they are recorded, clearly labelled as
  historical, in `docs/results.md`.

## Near-term next steps

1. Add phase-2 tests for valid simple primitive bundle assignment totals.
2. Add phase-3 boundary tests from `AGENTS.md` and `docs/model_decisions.md`
   when reduced signatures are introduced.
