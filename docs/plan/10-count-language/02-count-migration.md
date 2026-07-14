<!-- line-length: ignore-next-line -- legacy line pending wrap -->
# PR2 — migrate assignments, assigned supports and reduced networks beneath `rice count`

Status: `done`

## Goal

Add object-language count targets for later stages without changing their
mathematical semantics casually:

- `rice count assignments`
- `rice count assigned-supports`
- `rice count networks`

## Notes

Map existing staged commands to object names:

- staged `rice bundles` -> `rice count assignments`
- staged `rice labelings` -> `rice count assigned-supports`
- staged `rice reduced` -> `rice count networks --relation local-sp`

<!-- line-length: ignore-next-line -- legacy line pending wrap -->
The implementation should reuse PR1 query, profile, grouping, JSON metadata, and
exact bundle-weight foundations.

## Progress notes

<!-- line-length: ignore-next-line -- legacy line pending wrap -->
Implemented in PR2: `rice count assignments`, `rice count assigned-supports`, and `rice count networks --relation local-sp` using `CountQuery`, exact sparse facts, reusable grouping, weighted Burnside assigned-support distributions, and query-aware local-SP network counting. `rice count reductions` was deliberately deferred to PR3 because meaningful reduction analysis needs provenance and fibre data.
