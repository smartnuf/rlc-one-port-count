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
Network censuses require a finite component budget and fail fast otherwise.

Focused local-reduction primitives remain supported provisionally:

```python
from rice import canonical_reduced_signature, ReducedFactor, ReducedSignature
from rice import normalise_series_factor, normalise_parallel_factor
```

Removed staged census wrappers and staged result dataclasses are not part of the
public API. Shared algorithms such as support enumeration, Burnside counting and
local canonical reduction may remain as internal implementation machinery.
