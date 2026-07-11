# PR1 — counting-language foundations and bundle-set census

Status: `done`

## Goal

Introduce the object-oriented counting-language foundation while preserving the
existing staged commands. This PR implements only:

- `rice count supports`
- `rice count bundle-types`
- `rice count bundle-sets`

It also defines shared component constraints, finite-query resolution, source
support-edge ranges, named profiles, exact bundle weights, bundle-set multiset
census results, JSON report metadata, and Python API exports.

## Notes

- `bundle-sets` are inventories/multisets of the seven simple primitive bundle
  types; multiplicity across different support edges is valid and distinct from
  repeated same-type primitives inside one bundle.
- Component constraints intersect by logical AND. They constrain compatible
  bundle inventories for `count supports`; they do not component-label support
  graphs. Broad total caps such as `max_rlc` are tightened by any finite
  per-type totals implied by `max_r` plus `max_lc` or `max_r` plus separate
  `max_l`/`max_c` bounds before deriving the effective source-edge cap.
- Public `BundleSet` construction validates the seven primitive-bundle
  multiplicity slots before exposing component counts, JSON, or raw placement
  counts. Effective source support-edge caps use the tightest total-component
  upper bound implied by all supplied component constraints.
- A supports or bundle-sets query must have a finite effective source-edge cap
  from an exact/ranged edge option, a finite component region, or a named finite
  profile.
- `BundleSet` validates that public API callers provide exactly one
  non-negative multiplicity for each simple primitive bundle type before any
  component counts, placement counts, or JSON records are derived.
- The current staged commands remain compatibility interfaces: `supports`,
  `bundles`, `labelings`, and `reduced`.

## Validation

Implemented with focused API and CLI tests plus the repository validation
commands recorded in the PR summary.
