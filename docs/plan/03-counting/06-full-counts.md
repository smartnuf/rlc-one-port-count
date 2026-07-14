# 03-counting / 06 — Generate complete counts for full planned scope

Status: `todo`

## Goal

Generate complete, reproducible counts for the main scope:

```text
R <= 3
L + C <= 5
```

## Tasks

- Generate graph candidates.
- Assign R/L/C edge types subject to the scope.
- Canonicalise candidates.
<!-- line-length: ignore-next-line -- legacy line pending wrap -->
- Reject invalid or reducible candidates according to the documented definition.
<!-- line-length: ignore-next-line -- legacy line pending wrap -->
- Convert accepted candidates to repository-supported descriptors where possible.
- Count failures separately where descriptor conversion is not yet supported.
- Produce summary tables.

## Output tables

At minimum, produce tables by:

- `R` count;
- `L+C` count;
- `(L, C)` composition;
- descriptor-representable versus not-yet-representable;
- accepted versus rejected reason.

## Done means

- Counts are reproducible from a clean checkout.
- Outputs are stored in a predictable location.
- Tests check at least the small subset and the Ladenheim comparison slice.
