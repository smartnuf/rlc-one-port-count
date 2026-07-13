# Provisional Python API

The top-level `rice` package exports only the current provisional object-language
counting API and focused local-reduction primitives. The API is not stable.

Counting entry points:

```python
from rice import CountQuery, ComponentConstraints
from rice import support_census, bundle_set_census, assignment_census
from rice import assigned_support_census, network_census
```

Use `CountQuery(profile="main")` for the main `R <= 3`, `L+C <= 5` source slice
and `CountQuery(profile="golden")` for the small committed network slice.
Network censuses require a finite effective support-edge range, which may come
from a finite component budget/profile, `support_edges`, or `max_support_edges`.

Focused local-reduction primitives remain supported provisionally:

```python
from rice import canonical_reduced_signature, ReducedFactor, ReducedSignature
from rice import normalise_series_factor, normalise_parallel_factor
```

Removed staged census wrappers and staged result dataclasses are not part of the
public API. Shared algorithms such as support enumeration, Burnside counting and
local canonical reduction may remain as internal implementation machinery.

Enumeration and provenance entry points are also exported provisionally:

```python
from rice import enum_supports, enum_bundle_types, enum_bundle_sets
from rice import enum_assignments, enum_assigned_supports, enum_networks
from rice import reduction_census
```

The enumeration APIs accept `CountQuery` objects and return immutable record
objects such as `SupportRecord`, `BundleSetRecord`, `AssignmentRecord`,
`AssignedSupportRecord`, and `NetworkRecord`. IDs use a readable prefix plus a
truncated SHA-256 digest of the current canonical representation; this is
repeatable within the current provisional definition but is not a promise of
permanent ID continuity. `enum_assignments`, `enum_assigned_supports`, and
`enum_networks` accept `max_records` and default to 10,000 records.

`reduction_census(query, relation="local-sp")` returns a
`ReductionCensusResult` with pipeline totals, fibre distributions,
source-edge/component transitions, collision summaries, and conservation
diagnostics for the many-to-one maps from assignments to assigned-support
classes to reduced networks.
