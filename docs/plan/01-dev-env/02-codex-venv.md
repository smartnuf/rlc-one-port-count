# 01-dev-env / 02 — Make Codex use `.venv` explicitly

Status: `done`

## Goal

<!-- line-length: ignore-next-line -- legacy line pending wrap -->
Stop Codex and humans from accidentally installing or testing with system Python.

## Requirements

- `AGENTS.md` must tell agents to use `.venv` explicitly.
- Setup and maintenance commands must use `.venv` paths.
- No test or install command should depend on an activated shell environment.

## Done means

- Codex has exact commands to run.
<!-- line-length: ignore-next-line -- legacy line pending wrap -->
- The documented commands use `.venv/bin/python` on Linux/WSL and `.venv\Scripts\python.exe` on Windows.
- There is no instruction to use bare `pip`.

## Progress notes

- 2026-07-11: Codex setup and maintenance now prepare `.venv` and run only a
<!-- line-length: ignore-next-line -- legacy line pending wrap -->
  short import/version smoke test. Setup records a cache-local fingerprint under
  `.venv/`; maintenance compares that fingerprint and skips editable-install
  refreshes when Python/package inputs are unchanged.
