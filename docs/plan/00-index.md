# rlc-oneport-count plan index

This is the top-level plan index. Keep this file short: it should show task structure, status, and links to detail files. Put substantive task descriptions in the linked files.

Status key: `done`, `doing`, `todo`, `blocked`, `later`.

## 01 — Development environment

- `done` [Fix Makefile syntax](01-dev-env/01-make.md)
- `done` [Make Codex use `.venv` explicitly](01-dev-env/02-codex-venv.md)
- `done` [Validate WSL2 Ubuntu path](01-dev-env/03-wsl.md)
- `done` [Run `make setup` and `make test`](01-dev-env/04-make-setup-test.md)
- `todo` [Create Windows/Linux scripts under `scripts/`](01-dev-env/05-scripts.md)
- `todo` [Keep Makefile, scripts, README, and AGENTS.md aligned](01-dev-env/06-contract.md)

## 02 — Cleanup and simplification

- `todo` [Review current implementation before deletion](02-cleanup/01-review.md)
- `todo` [Remove legacy implementation](02-cleanup/02-legacy.md)
- `todo` [Remove generic `X` implementation, tests, and docs](02-cleanup/03-generic-x.md)
- `todo` [Update examples, imports, and public surface](02-cleanup/04-public-api.md)

## 03 — Network enumeration and counts

- `todo` [Explain enumeration motivation](03-counting/01-motivation.md)
- `todo` [Define “distinct network” precisely](03-counting/02-distinct.md)
- `todo` [Set enumeration scope: `R <= 3`, `L+C <= 5`](03-counting/03-scope.md)
- `todo` [Implement small explicit subset: `R <= 2`, `L+C <= 3`](03-counting/04-small-slice.md)
- `todo` [Implement Ladenheim comparison slice: `R <= 3`, `L+C <= 2`, total `<= 5`](03-counting/05-ladenheim.md)
- `todo` [Generate complete counts for the full planned scope](03-counting/06-full-counts.md)
- `todo` [Store count outputs and supporting artefacts](03-counting/07-outputs.md)

## 04 — Test coverage

- `todo` [Set up test strategy for enumeration](04-tests/01-strategy.md)
- `todo` [Add golden-count tests](04-tests/02-golden-counts.md)
- `todo` [Add descriptor and canonicalisation tests](04-tests/03-canon-tests.md)
- `todo` [Add regression tests for removed legacy and generic `X` code](04-tests/04-cleanup-tests.md)
- `todo` [Add CI-friendly validation commands](04-tests/05-ci.md)

## 05 — Documentation

- `todo` [Document developer workflow](05-docs/01-dev-workflow.md)
- `todo` [Document counting methodology](05-docs/02-count-method.md)
- `todo` [Document catalogue comparisons and references](05-docs/03-catalogues.md)
- `todo` [Document known limits and open questions](05-docs/04-open.md)
