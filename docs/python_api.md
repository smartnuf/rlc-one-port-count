# Provisional Python API

RICE's Python API mirrors the provisional object-language CLI.  It is intended
for small finite slices, notebooks, and regression scripts; names, JSON shapes,
record IDs, and signature strings remain provisional until a versioned API is
announced.  See the [counting language](counting_language.md),
[README glossary](../README.md#command-map-and-glossary), and [mathematical model](model_decisions.md) for the
terms used below.

## Public surface at a glance

`rice.__all__` is grouped into these intentional categories:

- **Query/configuration types and constants**: `CountQuery`,
  `ComponentConstraints`, `IntegerRange`, `COUNT_PROFILES`,
  `SIMPLE_PRIMITIVE_BUNDLES`, `SimplePrimitiveBundle`.
- **Count functions and result/fact types**: `support_census`,
  `bundle_set_census`, `assignment_census`, `assigned_support_census`,
  `network_census`, `reduction_census`, plus their result/fact dataclasses.
- **Enumeration functions and record types**: `enum_supports`,
  `enum_bundle_types`, `enum_bundle_sets`, `enum_assignments`,
  `enum_assigned_supports`, `enum_networks`, and `*Record` dataclasses.
- **Reduction helpers and model facts**: `BundleSet`, `ReducedFactor`,
  `ReducedSignature`, `primitive_factor`, `normalise_series_factor`,
  `normalise_parallel_factor`, `normalise_reduced_factor`,
  `factor_from_simple_primitive_bundle`, `canonical_reduced_signature`,
  `reduced_signature_component_counts`, `iter_bundle_sets`.
- **Relations**: `NetworkRelation`, `LOCAL_SP_RELATION`,
  `validate_network_relation`.

The historical staged wrappers (`count_networks`, `CountResult`, old bundle
labeling census classes, and similar compatibility names) are intentionally not
exported.

## Minimal count example

```python
from rice import CountQuery, network_census

query = CountQuery(profile="golden")
result = network_census(query)

print(result.total)
print(result.records[0])
print(result.matrix())
```

Expected access pattern:

```text
313
{'r': 0, 'lc': 1, 'networks': 2}
((0, 2, 2, 4), (1, 4, 12, 40), (0, 4, 34, 210))
```

`result.facts` contains exact reduced `(R, L, C)` cells, `result.records`
contains grouped rows, and `result.diagnostics` contains source-stage totals
such as raw assignments and assigned-support classes.

## Minimal enumeration example

```python
from rice import ComponentConstraints, CountQuery, enum_networks

query = CountQuery(component_constraints=ComponentConstraints(max_r=1, max_lc=1))
records = enum_networks(query, max_records=100)

print(len(records))
print(records[0].network_id.startswith("network-"))
print(records[0].canonical_signature)
```

Expected output:

```text
7
True
0-1:C
```

Enumeration records are frozen dataclasses, but records that expose NetworkX
implementation state do so defensively: `SupportRecord.graph` returns a copy,
and `SupportRecord.automorphisms` returns read-only mapping proxies. Treat all
record IDs and signature strings as provisional.

## Profiles and defaults

There is **no default profile**. A `CountQuery()` with no component bounds and no
support-edge maximum is unbounded for object-language counts and raises
`ValueError` when evaluated. Named profiles are exact component inequalities:

| Profile | Bounds |
| --- | --- |
| `golden` | `R <= 2`, `L+C <= 3` |
| `main` | `R <= 3`, `L+C <= 5` |
| `ladenheim-structural-region` | `R+L+C <= 5`, `L+C <= 2` |
| `ladenheim-108-region` | `R+L+C <= 5`, `R <= 3`, `L+C <= 2` |

```python
from rice import COUNT_PROFILES, CountQuery

print(sorted(COUNT_PROFILES))
print(CountQuery(profile="main").effective_support_edge_range().to_json())
```

Expected output:

```text
['golden', 'ladenheim-108-region', 'ladenheim-structural-region', 'main']
{'min': 1, 'max': 8}
```

A profile is mutually exclusive with explicit `component_constraints`.

## Constructing queries

Use `ComponentConstraints` for component budgets:

```python
from rice import ComponentConstraints, CountQuery

query = CountQuery(
    component_constraints=ComponentConstraints(max_r=2, max_lc=3),
    min_support_edges=2,
    max_support_edges=4,
)
print(query.requested_support_edge_range().to_json())
print(query.effective_support_edge_range().to_json())
```

Expected output:

```text
{'min': 2, 'max': 4}
{'min': 2, 'max': 4}
```

Use an exact support-edge count with `support_edges`:

```python
from rice import ComponentConstraints, CountQuery, assignment_census

query = CountQuery(
    component_constraints=ComponentConstraints(max_r=1, max_lc=1),
    support_edges=2,
)
print(assignment_census(query).raw_assignments_total)
```

Expected output:

```text
4
```

`support_edges` is mutually exclusive with `min_support_edges` and
`max_support_edges`.

## Grouping examples

Source-stage counts can group by `support-edges`, `r`, `l`, `c`, `lc`, `rlc`, or
`none`:

```python
from rice import CountQuery, assignment_census

result = assignment_census(CountQuery(profile="golden"), group_by=("r", "lc"))
print(result.records[:3])
```

Network counts group by reduced component dimensions only: `r`, `l`, `c`, `lc`,
`rlc`, or `none`.

```python
from rice import CountQuery, network_census

result = network_census(CountQuery(profile="golden"), group_by=("none",))
print(result.records)
```

Expected output:

```text
[{'networks': 313}]
```

## Relations and `max_records`

The only implemented relation is `local-sp`:

```python
from rice import LOCAL_SP_RELATION, validate_network_relation

relation = validate_network_relation("local-sp")
print(relation == LOCAL_SP_RELATION)
print(relation.definition)
```

Expected output:

```text
True
canonical-reduced-topology-local-series-parallel-v1
```

Catalogue-producing enumeration functions default to `max_records=10000`.
Raise the limit explicitly only when you intend to materialize a larger
catalogue:

```python
from rice import ComponentConstraints, CountQuery, enum_assignments

query = CountQuery(component_constraints=ComponentConstraints(max_r=1, max_lc=1))
print(len(enum_assignments(query, max_records=20)))
```

Expected output:

```text
9
```

## Navigating results, facts, and records

Important field meanings:

- `source_support_edges` is the number of source support edges before local-SP
  reduction.
- `r`, `l`, and `c` are exact source component counts in assignment and
  assigned-support facts/records, but reduced counts in network facts/records.
- `raw_assignments` and `raw_assignment_count` count unquotiented source
  placements.
- `orbit_size` is the size of an assigned-support automorphism orbit represented
  by one canonical record.
- `relation.definition` is the precise provisional relation definition.
- `*_id` fields are deterministic provisional IDs, not permanent catalogue
  numbers.
- Provenance collections such as `assignment_ids`, `assigned_support_ids`,
  `support_ids`, and `source_component_tuples` explain which source records
  reduce to a later object.

```python
from rice import ComponentConstraints, CountQuery, enum_assigned_supports

query = CountQuery(component_constraints=ComponentConstraints(max_r=1, max_lc=1))
record = enum_assigned_supports(query, max_records=20)[0]
print(record.source_support_edges, record.r, record.l, record.c)
print(record.orbit_size, record.raw_assignment_count)
```

## JSON conversion

All public results and records provide `to_json()` methods composed of JSON-like
Python dictionaries/lists/scalars:

```python
from rice import CountQuery, network_census

payload = network_census(CountQuery(profile="golden"), group_by=("none",)).to_json()
print(payload["object"])
print(payload["totals"])
```

Expected output:

```text
networks
{'networks': 313}
```

## Failure and size guards

Unbounded queries fail when evaluated:

```python
from rice import CountQuery, network_census

try:
    network_census(CountQuery())
except ValueError as exc:
    print("finite maximum" in str(exc))
```

Expected output:

```text
True
```

Invalid groupings and relations fail early:

```python
from rice import CountQuery, network_census

try:
    network_census(CountQuery(profile="golden"), group_by=("support-edges",))
except ValueError as exc:
    print("grouping" in str(exc))
```

Expected output:

```text
True
```

Enumeration guards prevent accidental large catalogues:

```python
from rice import CountQuery, enum_assignments

try:
    enum_assignments(CountQuery(profile="golden"), max_records=1)
except ValueError as exc:
    print("max-records" in str(exc))
```

Expected output:

```text
True
```

## `support_census(max_edges=8)` versus query-based counts

`support_census(max_edges=8)` is the phase-1 support-graph milestone API.  Its
default `8` reproduces the documented support census for the main source budget
`R <= 3`, `L+C <= 5`, because that budget has at most eight source components
and therefore at most eight source support edges.  It stops before bundle
inventories, assignments, assigned-support orbits, and reduced signatures.

The query-based object-language API (`assignment_census`, `network_census`,
`enum_networks`, and friends) expresses component budgets, support-edge ranges,
grouping, relations, and record guards.  Use `support_census` when you want only
the support-stage graph census; use `CountQuery`-based functions for the full
RLC object language.
