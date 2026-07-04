# 04-tests / 03 — Descriptor and canonicalisation tests

Status: `todo`

## Goal

Ensure duplicate rejection and descriptor production are trustworthy.

## Tasks

- Test canonicalisation under internal node renaming and terminal-pair reversal.
- Test simple primitive bundle-label preservation.
- Test series/parallel normalisation where applicable.
- Test bridge/non-series-parallel examples separately.
- Test that descriptor output is stable.

## Done means

- Equivalent networks collapse to the same canonical representative where intended.
- Non-equivalent networks do not collapse accidentally.
- Descriptor output is deterministic.
