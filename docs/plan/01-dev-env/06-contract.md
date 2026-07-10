# 01-dev-env / 06 — Align Makefile, scripts, README, and AGENTS.md

Status: `done`

## Goal

Ensure there is one development contract, not several subtly different ones.

## Required contract

- Linux/WSL/Codex: `make setup`, `make test`, `make check` may be used.
- Windows PowerShell: `./scripts/setup.ps1`, `./scripts/test.ps1`, `./scripts/check.ps1` must be available and must not depend on Make.
- All paths use `.venv` explicitly.
- README and AGENTS.md must agree.

## Done means

- A fresh contributor can follow README.
- Codex can follow AGENTS.md.
- Both paths run equivalent commands.

## Progress notes

- The Linux/WSL Make path and Bash script path are aligned: Make delegates
  setup, test, lint, check, and clean to `scripts/*.sh`.
- README and AGENTS.md document the non-Make Bash path and require explicit
  `.venv/bin/python` usage on Linux/WSL.
- Native PowerShell scripts now provide the Windows path without Make, Bash,
  WSL, or activation, using `.venv\Scripts\python.exe` explicitly.
- README and AGENTS.md document the native PowerShell commands and the same
  check ordering as `scripts/check.sh`: lint, tests, support census, bundle
  assignment census, labeling census, legacy LC count, and legacy generic count.
- Evidence: the native Windows PowerShell path successfully ran `setup.ps1`,
  `test.ps1`, `lint.ps1`, and the complete `check.ps1` validation sequence.

- 2026-07-10: Hardened setup and cleanup scripts after PR review: Bash scripts
  avoid Bash-4-only helpers such as `mapfile`, setup probes require working
  `venv` support before selecting Python, Windows setup accepts forward-compatible
  `py -3` launcher runtimes, and Windows cleanup skips directory reparse points
  before recursion. Added regression coverage for script parsing and selection
  behavior.

- 2026-07-10: Removed generic-`X` support (`docs/plan/02-cleanup/03-generic-x.md`).
  `legacy-generic` is no longer a Make target and no longer appears in
  `scripts/check.sh` or `scripts/check.ps1`; both scripts and the Makefile
  still run the same reduced sequence: lint, tests, support census, bundle
  assignment census, labeling census, and `legacy-count`/`legacy lc count`.
  The Linux/Bash/Make path and the native PowerShell path remain equivalent
  after this removal — both dropped the same generic invocation and kept
  every other stage identical. Re-ran `make check` (via `./scripts/check.sh`)
  successfully after the change; `scripts/check.ps1` was inspected line by
  line for exact parity with `scripts/check.sh` but was not executed, since
  no Windows/PowerShell environment was available in this session (see
  `docs/plan/02-cleanup/03-generic-x.md` progress notes for the full
  validation record).
