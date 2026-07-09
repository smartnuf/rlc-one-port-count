# 08-docs / 02 — Document counting methodology

Status: `prog`

## Goal

Explain how counts are generated and what they mean.

## Required content

- Scope definition using `R` and `L+C` bounds.
- Definition of distinctness.
- Generation method.
- Rejection rules.
- Canonicalisation method.
- Descriptor conversion method.
- Output table interpretation.

## Done means

- A reader can reproduce the counts.
- The limits of the method are clear.

## Progress notes

- The repository now has normative model docs for the intended reduced model and
  support-census phase, plus docs that label the current multiset-bundle counter
  as legacy.
- `docs/results.md`, `docs/computation.md`, and the README record both the
  legacy count results and the phase-1 support-census target table.
- Full reduced counting methodology is not complete because phase-2 bundle
  assignment, reduced signatures, descriptor conversion, and final output table
  interpretation are still pending.

## Near-term next steps

1. Update method documentation when phase-2 simple bundle assignment is added.
2. Add reduced-signature methodology only after implementation and tests exist.
3. Keep legacy and reduced-model result tables clearly separated.
