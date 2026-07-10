# 01-dev-env / 05 — Create scripts under `scripts/`

Status: `done`

## Goal

Make Windows-native development first-class without requiring `make`.

## Proposed script set

```text
scripts/
  setup.ps1
  test.ps1
  lint.ps1
  check.ps1
  clean.ps1
  setup.sh
  test.sh
  lint.sh
  check.sh
  clean.sh
```

## Requirements

- PowerShell scripts are the canonical Windows-native path.
- Shell scripts are the non-Make Linux/macOS/WSL path.
- Scripts must use `.venv` explicitly.
- Scripts must print the Python executable they use.
- Scripts must fail clearly if run from the wrong directory.

## Done means

- Windows users can run `./scripts/setup.ps1` and `./scripts/test.ps1` without installing Make.
- Linux/WSL users can run `./scripts/setup.sh` and `./scripts/test.sh` without Make.
- Make targets can delegate to these scripts where practical.

## Progress notes

- Bash/Linux/WSL scripts have been added: `setup.sh`, `test.sh`, `lint.sh`,
  `check.sh`, and `clean.sh`.
- The Bash scripts validate that they are run from the repository root, use the
  repository-local `.venv` explicitly, and print the Python executable in use.
- The Makefile delegates `setup`, `test`, `lint`, `check`, and `clean` to the
  Bash scripts while keeping the existing named validation targets available.
- Native PowerShell scripts have been added: `setup.ps1`, `test.ps1`,
  `lint.ps1`, `check.ps1`, and `clean.ps1`, plus a private `_common.ps1`
  helper for root validation, venv lookup, checked command invocation, and safe
  cleanup path resolution.
- The PowerShell scripts were parsed with the native PowerShell parser, checked
  from the wrong directory, and executed from a clean native Windows setup path:
  `clean.ps1`, `setup.ps1`, `test.ps1`, `lint.ps1`, and `check.ps1`.
- Repeated `setup.ps1` and repeated `clean.ps1` were verified, followed by
  recreating the final `.venv` with `setup.ps1` and rerunning `test.ps1`.

- 2026-07-10: Hardened setup and cleanup scripts after PR review: Bash scripts
  avoid Bash-4-only helpers such as `mapfile`, setup probes require working
  `venv` support before selecting Python, Windows setup accepts forward-compatible
  `py -3` launcher runtimes, and Windows cleanup skips directory reparse points
  before recursion. Added regression coverage for script parsing and selection
  behavior.
- 2026-07-10: Kept Bash syntax coverage runnable through a Windows WSL Bash
  launcher by passing repository-relative POSIX paths, while restricting the
  isolated-POSIX-environment setup test to pytest sessions running on POSIX.
