# 01-dev-env / 01 — Fix Makefile syntax

Status: `done`

## Goal

<!-- line-length: ignore-next-line -- legacy line pending wrap -->
Make the Makefile parse and run at least far enough for its targets to be tested.

## Background

<!-- line-length: ignore-next-line -- legacy line pending wrap -->
`make test` previously failed immediately with a `missing separator` error. That typically means a recipe line used spaces instead of a tab, or that a line continuation was malformed.

## Done means

- `make` can parse the Makefile.
- `make help`, if present, works.
- `make test` no longer fails before invoking the intended test command.
