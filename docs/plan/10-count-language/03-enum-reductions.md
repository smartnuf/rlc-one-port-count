# PR3 — enumeration and reduction mapping/analysis

Status: `done`

## Goal

Introduce the planned enumeration language and reduction-analysis reports, including `rice count reductions`:

- `rice enum supports`
- `rice enum bundle-types`
- `rice enum bundle-sets`
- `rice enum assignments`
- `rice enum assigned-supports`
- `rice enum networks`

`reductions` analysis should describe many-to-one mappings from raw assignments
to assigned-support classes to reduced networks, including fibre-size
distributions, source-to-reduced edge transitions, component-count transitions,
and collision analysis.

## Boundary note

PR2 intentionally did not add a superficial `rice count reductions` command. PR3 remains responsible for source-to-reduced provenance, fibre-size distributions, component/source-edge transitions, collision analysis, and `rice enum ...` catalogue commands.


## PR3 completion notes

Implemented all six `rice enum` targets, provisional stable IDs, guarded assignment/assigned-support/network enumeration, and `rice count reductions` provenance reports with fibre distributions, source-edge transitions, component transitions, collision summaries, and golden conservation checks. Remaining limitations are intentional non-goals: no rational immittance equality, 2-isomorphism, star-delta transforms, descriptor conversion, database storage, or full main-slice network catalogue.


- 2026-07-12: Addressed PR review feedback by making `--max-records` reject non-positive values at CLI/API boundaries and by tightening provisional enumeration helper signatures/imports.
