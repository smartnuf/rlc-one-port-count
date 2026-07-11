# Python API

This document is the concise reference for the supported top-level `rice`
Python API — every name in `rice.__all__`, grouped by role. It does not
duplicate the full methodology; see the normative model documents linked from
each section for the underlying rules.

Everything documented here is importable directly from the top-level
package:

```python
from rice import support_census, reduced_topology_census  # etc.
```

A few additional non-underscore helpers exist inside `rice.core` (graph
generation, automorphisms, terminal-relevance checks, and similar
combinatorial infrastructure). They are internal implementation detail used
to build the objects below, are not exported from the top-level package, and
are not part of the supported API. Import from `rice`, not `rice.core`.

All examples below use very small budgets so they run in well under a
second.

## 1. Support census

Enumerates connected unlabelled simple support graphs, unordered
terminal-pair orbits, and terminal-relevant two-terminal supports, before any
component labels are assigned. See
[`docs/support_graph_enumeration.md`](support_graph_enumeration.md) for the
full contract (terminal relevance, rejection-not-pruning, expected census
tables).

### `support_census(max_edges: int = 8) -> SupportCensusResult`

- **Role**: phase-1 census. The structural foundation every later stage
  builds on.
- **Output kind**: raw counts of basic/labelled/terminal-relevant support
  graphs — no component assignment has happened yet.
- **Limits**: `max_edges` must be at least 1.

```python
from rice import support_census

result = support_census(max_edges=3)
print(result.relevant_by_edges)   # {1: 1, 2: 1, 3: 2}
print(result.relevant_total)      # 4
```

### `SupportCensusResult`

Fields: `max_edges: int`, `basic_by_edges: dict[int, int]`,
`terminal_labelings_by_edges: dict[int, int]`,
`relevant_by_edges: dict[int, int]`.

Properties: `basic_total`, `terminal_labelings_total`, `relevant_total` (each
sums the corresponding `*_by_edges` dict).

- `basic_by_edges`: connected unlabelled simple graphs, before terminal
  choice.
- `terminal_labelings_by_edges`: unordered terminal-pair orbits under each
  support graph's automorphism group (no terminal-relevance filter applied).
- `relevant_by_edges`: the subset of those that pass the terminal-relevance
  test (every support edge lies on at least one simple terminal-to-terminal
  path).

## 2. Primitive bundles and raw assignment census

Assigns only the seven simple primitive bundles to terminal-relevant support
edges, subject to a global `R` / `L+C` budget. Series spans and reduced
signatures are intentionally outside this stage. See
[`docs/bundles_and_multiedges.md`](bundles_and_multiedges.md) and
[`docs/model_decisions.md`](model_decisions.md) for the bundle contract.

### `SimplePrimitiveBundle`

A dataclass pairing a bundle label with its component-budget weight.
Fields: `label: str`, `r_count: int`, `reactive_count: int`.

### `SIMPLE_PRIMITIVE_BUNDLES: tuple[SimplePrimitiveBundle, ...]`

The fixed sequence of the seven allowed bundles: `R`, `L`, `C`, `R||L`,
`R||C`, `L||C`, `R||L||C`. Repeated same-type primitives such as `R||R` are
never generated.

```python
from rice import SimplePrimitiveBundle, SIMPLE_PRIMITIVE_BUNDLES

assert all(isinstance(b, SimplePrimitiveBundle) for b in SIMPLE_PRIMITIVE_BUNDLES)
print([b.label for b in SIMPLE_PRIMITIVE_BUNDLES])
# ['R', 'L', 'C', 'R||L', 'R||C', 'L||C', 'R||L||C']
```

### `simple_bundle_assignment_census(max_r: int = 3, max_reactive: int = 5, max_edges: int | None = None) -> BundleAssignmentCensusResult`

- **Role**: phase-2 census.
- **Output kind**: raw leaves — no automorphism quotienting, no
  reduced-signature merging.
- **Limits**: `max_r`/`max_reactive` must be non-negative; `max_edges`
  defaults to `max_r + max_reactive` and cannot exceed it.

```python
from rice import simple_bundle_assignment_census

result = simple_bundle_assignment_census(max_r=1, max_reactive=1)
print(result.leaf_assignments_total)       # 9
print(result.leaf_assignments_by_edges)    # {1: 5, 2: 4}
```

### `BundleAssignmentCensusResult`

Fields: `max_r`, `max_reactive`, `max_edges`,
`relevant_supports_by_edges: dict[int, int]`,
`assignments_per_support_by_edges: dict[int, int]`,
`leaf_assignments_by_edges: dict[int, int]`.

Properties: `relevant_supports_total`, `leaf_assignments_total`.

## 3. Labeling-orbit census

Quotients the phase-2 raw assignments by support automorphisms that
preserve the unordered terminal pair (including terminal reversal). This
removes assigned-support graph isomorphism only — no local series-span
reduction, no reduced signatures.

### `simple_bundle_labeling_census(max_r: int = 3, max_reactive: int = 5, max_edges: int | None = None) -> BundleLabelingCensusResult`

- **Role**: phase-3 census.
- **Output kind**: orbit-quotiented (Burnside's lemma over terminal-set-
  preserving support automorphisms), not yet reduced.
- **Limits**: same as `simple_bundle_assignment_census`.

```python
from rice import simple_bundle_labeling_census

result = simple_bundle_labeling_census(max_r=1, max_reactive=1)
print(result.canonical_labeling_orbits_total)     # 7
print(result.canonical_labeling_orbits_by_edges)  # {1: 5, 2: 2}
```

### `BundleLabelingCensusResult`

Fields: `max_r`, `max_reactive`, `max_edges`,
`relevant_supports_by_edges: dict[int, int]`,
`raw_leaf_assignments_by_edges: dict[int, int]`,
`canonical_labeling_orbits_by_edges: dict[int, int]`.

Properties: `relevant_supports_total`, `raw_leaf_assignments_total`,
`canonical_labeling_orbits_total`.

### `simple_bundle_labeling_orbit_count(graph, terminals, max_r=3, max_reactive=5, graph_automorphisms=None) -> int`

The single-support building block behind `simple_bundle_labeling_census`:
counts canonical simple-bundle labelings of one two-terminal support graph
under its terminal-set-preserving automorphisms. Useful for testing or
inspecting one support in isolation; pass a NetworkX `Graph`, a `(source,
target)` terminal pair, and optionally a precomputed automorphism list to
avoid recomputing it.

## 4. Reduced factors and signatures

Local series/parallel reduction and canonical signatures for one already
assigned two-terminal network. This is where `R||R -> R`, series commutation,
and the distinction between series and parallel composition are applied.
See [`docs/model_decisions.md`](model_decisions.md) for the full reduction
contract (what merges, what does not, and what is out of scope such as
Y-Delta transforms or rational-impedance equality).

### `ReducedFactor`

Immutable recursive factor: `kind` (`"primitive"`, `"series"`, or
`"parallel"`) and `value` (a primitive name `"R"`/`"L"`/`"C"`, or a tuple of
operand `ReducedFactor`s). Directly constructing a `ReducedFactor` does
**not** canonicalise it — pass it through `normalise_reduced_factor` (or one
of the functions below) first.

### `ReducedSignature`

Canonical reduced-topology signature for one assigned two-terminal graph.
Field: `serialization: tuple[tuple[int, int, ReducedFactor], ...]`. Two
signatures compare equal iff the underlying topologies are equivalent under
the documented reduction rules (internal node renaming, terminal reversal,
series/parallel commutation, primitive singleton merging).

### `primitive_factor(name: str) -> ReducedFactor`

Builds a canonical primitive factor for `"R"`, `"L"`, or `"C"`; raises
`ValueError` for anything else.

### `normalise_series_factor(factors) -> ReducedFactor` / `normalise_parallel_factor(factors) -> ReducedFactor`

Build an unordered, flattened series/parallel composition from an iterable
of factors, merging duplicate primitive singleton operands (`R--R -> R`,
`R||R -> R`) but preserving repeated compound operands
(`(R--L)||(R--L)` stays as-is).

### `normalise_reduced_factor(factor: ReducedFactor) -> ReducedFactor`

The general recursive validation and canonicalisation entry point for a
caller-constructed `ReducedFactor` tree of any shape: recursively normalises
every nested composition, flattens nested compositions of the same kind,
sorts operands into a stable order, and merges duplicate primitive
singletons — all the way down. Use this (rather than manually rebuilding a
tree) whenever you assemble a `ReducedFactor` by hand instead of via
`factor_from_simple_primitive_bundle`.

### `factor_from_simple_primitive_bundle(bundle: str | SimplePrimitiveBundle | ReducedFactor) -> ReducedFactor`

Converts one bundle/factor input into a validated canonical factor. String
and `SimplePrimitiveBundle` inputs (e.g. `"R||L"`) are parsed as simple
primitive bundle labels; `ReducedFactor` inputs are recursively validated and
normalised via `normalise_reduced_factor`.

```python
from rice import (
    ReducedFactor,
    primitive_factor,
    normalise_series_factor,
    normalise_parallel_factor,
    normalise_reduced_factor,
    factor_from_simple_primitive_bundle,
)

r, l = primitive_factor("R"), primitive_factor("L")

series = normalise_series_factor([r, l])
print(series.stable_string())              # 'L--R'

parallel_dup = normalise_parallel_factor([r, r])
print(parallel_dup.stable_string())        # 'R'  (R||R collapses to R)

bundle_factor = factor_from_simple_primitive_bundle("R||L")
print(bundle_factor.stable_string())       # 'L||R'

messy = ReducedFactor("parallel", (ReducedFactor("parallel", (r, r)), l))
clean = normalise_reduced_factor(messy)
print(clean.stable_string())               # 'L||R'
assert clean == bundle_factor
```

### `canonical_reduced_signature(graph, terminals, edge_assignments) -> ReducedSignature`

- **Role**: reduces one already-assigned two-terminal support (a NetworkX
  `Graph`, a `(source, target)` terminal pair, and a `{edge: bundle_or_
  factor}` mapping) and returns its canonical `ReducedSignature`.
- **Output kind**: fully reduced — the final per-network signature.
- Raises `ValueError` for malformed or terminal-irrelevant input rather than
  silently pruning it (consistent with the support-census rejection rule).

```python
import networkx as nx
from rice import canonical_reduced_signature

graph = nx.Graph([(0, 1), (1, 2)])
signature = canonical_reduced_signature(graph, (0, 2), {(0, 1): "R", (1, 2): "L"})
print(signature.stable_string())           # '0-1:L--R'

# Terminal reversal gives the identical signature:
assert canonical_reduced_signature(graph, (2, 0), {(0, 1): "R", (1, 2): "L"}) == signature
```

### `reduced_signature_component_counts(signature: ReducedSignature) -> tuple[int, int, int]`

Returns the exact primitive `(R, L, C)` counts present in a reduced
signature — used to bucket signatures into an `(r, l+c)` census table.

## 5. End-to-end reduced-topology enumeration

Combines every earlier stage: enumerates supports, assigns budgeted bundles,
canonicalises each into a `ReducedSignature`, and deduplicates. This is the
only stage whose count is the final reduced-topology total.

### `reduced_topology_census(max_r: int = 2, max_reactive: int = 3, max_edges: int | None = None) -> ReducedTopologyCensusResult`

- **Role**: the full reduced-topology census for one budget slice.
- **Output kind**: fully reduced and deduplicated — the final count.
- **Non-goal / limit**: computed and committed today only for the small
  golden slice `R <= 2`, `L+C <= 3` (the function's own defaults). Running it
  against the full `R <= 3`, `L+C <= 5` project slice is unimplemented as a
  *committed result* (the function itself has no scope restriction, but that
  larger run is expensive and tracked separately as remaining work; see
  `docs/plan/05-slices/04-r3-x5.md`).

```python
from rice import reduced_topology_census

result = reduced_topology_census(max_r=1, max_reactive=1)
print(result.exact_table)   # ((0, 2), (1, 4))
print(result.total)         # 7
print(result.canonical_signatures)
# ('0-1:C', '0-1:C--R', '0-1:C||R', '0-1:L', '0-1:L--R', '0-1:L||R', '0-1:R')
```

### `ReducedTopologyCensusResult`

Fields: `max_r`, `max_reactive`, `max_edges`,
`exact_table: tuple[tuple[int, ...], ...]` (indexed `exact_table[r][x]` where
`x = L+C`), `canonical_signatures: tuple[str, ...]`,
`raw_leaf_assignments_total: int`, `canonical_labeling_orbits_total: int`.

Property: `total` (sum of `exact_table`). Method: `as_markdown_table()`.

### `iter_reduced_topology_signatures(max_r: int = 3, max_reactive: int = 5, max_edges: int | None = None)`

Generator form of the same enumeration; yields unique canonical
`ReducedSignature` objects deterministically (sorted by stable string) for a
budget slice, without building the full census table. `reduced_topology_census`
is built on top of this.

## What this API does not do

The reduced model is not a full electrical-equivalence solver. None of the
functions above attempt Y-Delta transforms, bridge-balance simplifications,
duality, Foster/Cauer equivalence, or algebraic equality of rational
driving-point impedances. See `docs/model_decisions.md` for the full list of
out-of-scope transforms.

## CLI equivalents

Each census function has a matching CLI subcommand that prints the same data
as markdown or JSON: `rice supports`, `rice bundles`, `rice labelings`,
`rice reduced`. See the README's "Use" section for CLI examples.

## Count-language API foundations

The supported public API now includes:

- `IntegerRange` for inclusive requested/effective integer ranges;
- `ComponentConstraints` for intersecting `R`, `L`, `C`, `L+C`, and `R+L+C`
  upper bounds;
- `CountQuery` for profile expansion, finite-query validation, and effective
  source support-edge range resolution;
- `BundleSet` for multiset inventories of the seven simple primitive bundle
  types;
- `BundleSetCensusResult`, `iter_bundle_sets(...)`, and
  `bundle_set_census(...)` for exact bundle-set facts and grouped summaries;
- `COUNT_PROFILES` for `golden`, `main`, `ladenheim-structural-region`, and
  `ladenheim-108-region`.

`SimplePrimitiveBundle` retains `reactive_count == l_count + c_count` and now
also exposes exact `l_count` and `c_count` weights.
