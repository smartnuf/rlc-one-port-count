# 08-docs / 01 — Document developer workflow

Status: `todo`

## Goal

Make the development workflow easy to follow.

## Required sections

- WSL2/Linux setup.
- Windows PowerShell setup.
- Codex instructions.
- Test commands.
- Slow/full enumeration commands.
- Cleaning and rebuilding `.venv`.

## Done means

- README and AGENTS.md are consistent.
- New contributors do not need to infer the workflow.

## Progress notes

- 2026-07-09: Documented CLI argument-placement expectations in `AGENTS.md`,
  README examples, and support-census docs. Future argument-parsing changes
  should verify both top-level and subcommand help before handoff.

- 2026-07-10: Documented exact long-option parsing, zero-budget census
  boundary behaviour, and the tested `networkx>=3.2` dependency floor.

## Progress notes

- 2026-07-11: Documented change-aware validation in README and AGENTS.md,
<!-- line-length: ignore-next-line -- legacy line pending wrap -->
  including lightweight documentation validation, full-validation escalation for
<!-- line-length: ignore-next-line -- legacy line pending wrap -->
  unknown/tooling changes, and the rule not to duplicate checks already included
  in `make check`.
