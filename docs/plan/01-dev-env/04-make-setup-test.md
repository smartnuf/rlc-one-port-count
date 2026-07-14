# 01-dev-env / 04 — Run `make setup` and `make test`

Status: `done`

## Goal

Prove that the Makefile development path works end to end in WSL2/Linux.

## Tasks

1. Run `make setup` from a clean checkout.
2. Confirm `.venv` is created.
3. Confirm dependencies are installed into `.venv`.
4. Run `make test`.
5. Record any failures with enough detail for Codex to act.

## Validation commands

```bash
make setup
.venv/bin/python --version
.venv/bin/python -m pip list
make test
```

## Done means

- `make setup` completes successfully.
- `make test` runs tests through `.venv`.
<!-- line-length: ignore-next-line -- legacy line pending wrap -->
- Any remaining failures are genuine code/test failures, not environment failures.
