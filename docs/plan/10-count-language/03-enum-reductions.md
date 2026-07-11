# PR3 — enumeration and reduction mapping/analysis

Status: `todo`

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
