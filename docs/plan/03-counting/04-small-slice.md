# 03-counting / 04 — Implement small explicit subset: `R <= 2`, `L+C <= 3`

Status: `done`

## Goal

<!-- line-length: ignore-next-line -- legacy line pending wrap -->
Create a deliberately smaller subset for early implementation, test speed, and regression coverage.

## Scope

```text
R <= 2
L + C <= 3
```

<!-- line-length: ignore-next-line -- legacy line pending wrap -->
This subset should be treated as an explicit test point inside the larger `R <= 3`, `L+C <= 5` plan.

## Why this subset matters

- It should be small enough for fast local and CI tests.
- It exercises mixed R/L/C assignment without reaching the full search size.
<!-- line-length: ignore-next-line -- legacy line pending wrap -->
- It provides early confidence in graph generation, colouring, canonicalisation, descriptor conversion, and count reporting.

## Done means

- The subset can be generated independently.
- It has stable count outputs.
- Its counts are used as golden regression tests.
- The subset is documented as a test slice, not the final catalogue target.

## Progress notes

<!-- line-length: ignore-next-line -- legacy line pending wrap -->
- Implemented as the first complete reduced-topology golden slice using `rice count networks --profile golden`.
<!-- line-length: ignore-next-line -- legacy line pending wrap -->
- Machine-readable summary: `data/counts/small-r2-x3.json`; human summary: `docs/counts/small-r2-x3.md`.
<!-- line-length: ignore-next-line -- legacy line pending wrap -->
- Exact `(R, L+C)` table is `[[0, 2, 2, 4], [1, 4, 12, 40], [0, 4, 34, 210]]`, cumulative total `313`.
