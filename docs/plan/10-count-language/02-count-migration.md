# PR2 — migrate assignments, assigned supports and reduced networks beneath `rice count`

Status: `todo`

## Goal

Add object-language count targets for later stages without changing their
mathematical semantics casually:

- `rice count assignments`
- `rice count assigned-supports`
- `rice count networks`
- `rice count reductions`

## Notes

Map existing staged commands to object names:

- current `rice bundles` -> future `rice count assignments`
- current `rice labelings` -> future `rice count assigned-supports`
- current `rice reduced` -> future `rice count networks --relation local-sp`

The implementation should reuse PR1 query, profile, grouping, JSON metadata, and
exact bundle-weight foundations.
