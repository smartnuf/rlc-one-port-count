"""Enumerate small two-terminal RLC one-port support graphs and networks.

The public provisional counting API is query based: support, bundle-set,
assignment, assigned-support, and network censuses are expressed through
object-language functions such as :func:`assignment_census`,
:func:`assigned_support_census`, and :func:`network_census`. Focused local
series/parallel reduction helpers such as :func:`canonical_reduced_signature`
remain public model primitives. Older staged census wrappers are retained only
as private implementation/test machinery where their algorithms are still
useful.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from itertools import combinations, permutations, product
from typing import DefaultDict, Iterable, Literal

import networkx as nx
from networkx.algorithms import isomorphism as iso


@dataclass(frozen=True)
class SupportCensusResult:
    """Support-graph census for the phase-1 reduced-model milestone.

    Counts are keyed by support-edge count. ``basic_by_edges`` counts
    connected unlabelled simple graphs before terminal choice,
    ``terminal_labelings_by_edges`` counts unordered terminal-pair orbits under
    each support graph's automorphism group, and ``relevant_by_edges`` counts
    the terminal-labelled graphs whose every edge lies on a simple path between
    the terminals.
    """

    max_edges: int
    basic_by_edges: dict[int, int]
    terminal_labelings_by_edges: dict[int, int]
    relevant_by_edges: dict[int, int]

    @property
    def basic_total(self) -> int:
        return sum(self.basic_by_edges.values())

    @property
    def terminal_labelings_total(self) -> int:
        return sum(self.terminal_labelings_by_edges.values())

    @property
    def relevant_total(self) -> int:
        return sum(self.relevant_by_edges.values())


@dataclass(frozen=True)
class SimplePrimitiveBundle:
    """A reduced-model primitive bundle label and exact component weights.

    ``reactive_count`` remains the public ``L+C`` weight.  When callers use the
    historical three-argument construction style, exact ``l_count`` and
    ``c_count`` weights are inferred from the validated bundle label.
    """

    label: str
    r_count: int
    reactive_count: int
    l_count: int | None = None
    c_count: int | None = None

    def __post_init__(self) -> None:
        pieces = tuple(self.label.split("||"))
        if not pieces or any(piece not in {"R", "L", "C"} for piece in pieces):
            raise ValueError(f"unknown simple primitive bundle {self.label!r}")
        if len(set(pieces)) != len(pieces):
            raise ValueError(f"simple primitive bundle repeats a primitive type: {self.label!r}")
        inferred_r = 1 if "R" in pieces else 0
        inferred_l = 1 if "L" in pieces else 0
        inferred_c = 1 if "C" in pieces else 0
        inferred_x = inferred_l + inferred_c
        l_count = inferred_l if self.l_count is None else self.l_count
        c_count = inferred_c if self.c_count is None else self.c_count
        if (self.r_count, self.reactive_count, l_count, c_count) != (
            inferred_r,
            inferred_x,
            inferred_l,
            inferred_c,
        ):
            raise ValueError(f"component weights do not match bundle label {self.label!r}")
        object.__setattr__(self, "l_count", l_count)
        object.__setattr__(self, "c_count", c_count)


SIMPLE_PRIMITIVE_BUNDLES: tuple[SimplePrimitiveBundle, ...] = (
    SimplePrimitiveBundle("R", 1, 0, 0, 0),
    SimplePrimitiveBundle("L", 0, 1, 1, 0),
    SimplePrimitiveBundle("C", 0, 1, 0, 1),
    SimplePrimitiveBundle("R||L", 1, 1, 1, 0),
    SimplePrimitiveBundle("R||C", 1, 1, 0, 1),
    SimplePrimitiveBundle("L||C", 0, 2, 1, 1),
    SimplePrimitiveBundle("R||L||C", 1, 2, 1, 1),
)


@dataclass(frozen=True)
class IntegerRange:
    """Inclusive integer range, with ``None`` denoting an open side."""

    minimum: int | None = None
    maximum: int | None = None

    def __post_init__(self) -> None:
        if self.minimum is not None and self.minimum < 0:
            raise ValueError("range minimum must be non-negative")
        if self.maximum is not None and self.maximum < 0:
            raise ValueError("range maximum must be non-negative")
        # Empty effective intersections such as requested edge 2 with a
        # component-derived maximum of 1 are valid finite queries.

    def to_json(self) -> dict[str, int | None]:
        return {"min": self.minimum, "max": self.maximum}


@dataclass(frozen=True)
class ComponentConstraints:
    """Intersecting upper bounds on exact ``(R,L,C)`` component counts."""

    max_rlc: int | None = None
    max_r: int | None = None
    max_l: int | None = None
    max_c: int | None = None
    max_lc: int | None = None

    def __post_init__(self) -> None:
        for name, value in self.to_json().items():
            if value is not None and value < 0:
                raise ValueError(f"{name} must be non-negative")

    def to_json(self) -> dict[str, int | None]:
        return {
            "max_rlc": self.max_rlc,
            "max_r": self.max_r,
            "max_l": self.max_l,
            "max_c": self.max_c,
            "max_lc": self.max_lc,
        }

    def accepts(self, r: int, l: int, c: int) -> bool:
        return (
            (self.max_rlc is None or r + l + c <= self.max_rlc)
            and (self.max_r is None or r <= self.max_r)
            and (self.max_l is None or l <= self.max_l)
            and (self.max_c is None or c <= self.max_c)
            and (self.max_lc is None or l + c <= self.max_lc)
        )

    def max_total_components(self) -> int | None:
        upper_bounds = []
        if self.max_rlc is not None:
            upper_bounds.append(self.max_rlc)
        r_bound = self.max_r
        lc_bound = self.max_lc
        if lc_bound is None and self.max_l is not None and self.max_c is not None:
            lc_bound = self.max_l + self.max_c
        if r_bound is not None and lc_bound is not None:
            upper_bounds.append(r_bound + lc_bound)
        if self.max_l is not None and self.max_c is not None and r_bound is not None:
            upper_bounds.append(r_bound + self.max_l + self.max_c)
        if upper_bounds:
            return min(upper_bounds)
        return None


COUNT_PROFILES: dict[str, ComponentConstraints] = {
    "golden": ComponentConstraints(max_r=2, max_lc=3),
    "main": ComponentConstraints(max_r=3, max_lc=5),
    "ladenheim-structural-region": ComponentConstraints(max_rlc=5, max_lc=2),
    "ladenheim-108-region": ComponentConstraints(max_rlc=5, max_r=3, max_lc=2),
}


@dataclass(frozen=True)
class CountQuery:
    """Shared finite counting query for source support-edge objects."""

    component_constraints: ComponentConstraints = ComponentConstraints()
    support_edges: int | None = None
    min_support_edges: int | None = None
    max_support_edges: int | None = None
    profile: str | None = None

    def __post_init__(self) -> None:
        if self.profile is not None:
            if self.profile not in COUNT_PROFILES:
                raise ValueError(f"unknown profile {self.profile!r}")
            if self.component_constraints != ComponentConstraints():
                raise ValueError("profile is mutually exclusive with explicit component constraints")
            object.__setattr__(self, "component_constraints", COUNT_PROFILES[self.profile])
        if self.support_edges is not None:
            if self.support_edges <= 0:
                raise ValueError("support_edges must be a positive integer")
            if self.min_support_edges is not None or self.max_support_edges is not None:
                raise ValueError("support_edges is mutually exclusive with min/max support edges")
        for name in ("min_support_edges", "max_support_edges"):
            value = getattr(self, name)
            if value is not None and value <= 0:
                raise ValueError(f"{name} must be a positive integer")
        if (
            self.min_support_edges is not None
            and self.max_support_edges is not None
            and self.min_support_edges > self.max_support_edges
        ):
            raise ValueError("min_support_edges cannot exceed max_support_edges")

    def component_max_edges(self) -> int | None:
        return self.component_constraints.max_total_components()

    def effective_support_edge_range(self) -> IntegerRange:
        if self.support_edges is not None:
            requested_min = requested_max = self.support_edges
        else:
            requested_min = self.min_support_edges or 1
            requested_max = self.max_support_edges
        component_max = self.component_max_edges()
        if requested_max is None:
            if component_max is None:
                raise ValueError("query has no finite maximum support-edge count; add --max-rlc, a finite component profile, --support-edges, or --max-support-edges")
            effective_max = component_max
        elif component_max is None:
            effective_max = requested_max
        else:
            effective_max = min(requested_max, component_max)
        return IntegerRange(requested_min, effective_max)

    def requested_support_edge_range(self) -> IntegerRange:
        if self.support_edges is not None:
            return IntegerRange(self.support_edges, self.support_edges)
        return IntegerRange(self.min_support_edges or 1, self.max_support_edges)

    def accepts_components(self, r: int, l: int, c: int) -> bool:
        return self.component_constraints.accepts(r, l, c)

    def to_json(self) -> dict[str, object]:
        return {
            "profile": self.profile,
            "component_constraints": self.component_constraints.to_json(),
            "requested_support_edges": self.requested_support_edge_range().to_json(),
            "effective_support_edges": self.effective_support_edge_range().to_json(),
        }


@dataclass(frozen=True)
class BundleSet:
    """A multiset inventory of simple primitive bundle types."""

    multiplicities: tuple[int, ...]

    def __post_init__(self) -> None:
        if len(self.multiplicities) != len(SIMPLE_PRIMITIVE_BUNDLES):
            raise ValueError(
                "multiplicities must include one entry per simple primitive bundle type"
            )
        for index, value in enumerate(self.multiplicities):
            if not isinstance(value, int):
                raise ValueError(f"multiplicities[{index}] must be integers")
            if value < 0:
                raise ValueError(f"multiplicities[{index}] must be non-negative")

    @property
    def source_support_edges(self) -> int:
        return sum(self.multiplicities)

    @property
    def r_count(self) -> int:
        return sum(n * b.r_count for n, b in zip(self.multiplicities, SIMPLE_PRIMITIVE_BUNDLES))

    @property
    def l_count(self) -> int:
        return sum(n * int(b.l_count) for n, b in zip(self.multiplicities, SIMPLE_PRIMITIVE_BUNDLES))

    @property
    def c_count(self) -> int:
        return sum(n * int(b.c_count) for n, b in zip(self.multiplicities, SIMPLE_PRIMITIVE_BUNDLES))

    @property
    def lc_count(self) -> int:
        return self.l_count + self.c_count

    @property
    def rlc_count(self) -> int:
        return self.r_count + self.lc_count

    @property
    def raw_placement_count(self) -> int:
        from math import factorial
        total = factorial(self.source_support_edges)
        for n in self.multiplicities:
            total //= factorial(n)
        return total

    def to_json(self) -> dict[str, object]:
        return {
            "multiplicities": dict(zip((b.label for b in SIMPLE_PRIMITIVE_BUNDLES), self.multiplicities)),
            "source_support_edges": self.source_support_edges,
            "r": self.r_count,
            "l": self.l_count,
            "c": self.c_count,
            "lc": self.lc_count,
            "rlc": self.rlc_count,
            "raw_placements": self.raw_placement_count,
        }


@dataclass(frozen=True)
class BundleSetCensusResult:
    query: CountQuery
    group_by: tuple[str, ...]
    records: tuple[dict[str, int], ...]
    bundle_sets: tuple[BundleSet, ...]

    @property
    def distinct_bundle_sets_total(self) -> int:
        return len(self.bundle_sets)

    @property
    def raw_placements_total(self) -> int:
        return sum(bs.raw_placement_count for bs in self.bundle_sets)

    def to_json(self) -> dict[str, object]:
        return {
            "format_version": 1,
            "object": "bundle-sets",
            "query": self.query.to_json(),
            "group_by": list(self.group_by),
            "records": list(self.records),
            "totals": {
                "distinct_bundle_sets": self.distinct_bundle_sets_total,
                "raw_placements": self.raw_placements_total,
            },
        }


def _multiplicity_tuples(total: int, parts: int) -> Iterable[tuple[int, ...]]:
    if parts == 1:
        yield (total,)
        return
    for n in range(total + 1):
        for rest in _multiplicity_tuples(total - n, parts - 1):
            yield (n,) + rest


def iter_bundle_sets(query: CountQuery) -> Iterable[BundleSet]:
    edge_range = query.effective_support_edge_range()
    if edge_range.maximum is None or edge_range.minimum is None or edge_range.minimum > edge_range.maximum:
        return
    for edge_count in range(edge_range.minimum, edge_range.maximum + 1):
        for multiplicities in _multiplicity_tuples(edge_count, len(SIMPLE_PRIMITIVE_BUNDLES)):
            bundle_set = BundleSet(multiplicities)
            if query.accepts_components(bundle_set.r_count, bundle_set.l_count, bundle_set.c_count):
                yield bundle_set


def bundle_set_census(query: CountQuery, group_by: tuple[str, ...] = ("support-edges",)) -> BundleSetCensusResult:
    allowed = {"support-edges", "r", "l", "c", "lc", "rlc"}
    if group_by == ("none",):
        dims: tuple[str, ...] = ()
    else:
        if any(dim not in allowed for dim in group_by):
            raise ValueError("unsupported bundle-set grouping dimension")
        dims = group_by
    bundle_sets = tuple(iter_bundle_sets(query))
    grouped: DefaultDict[tuple[int, ...], list[BundleSet]] = defaultdict(list)
    def value(bs: BundleSet, dim: str) -> int:
        return {
            "support-edges": bs.source_support_edges,
            "r": bs.r_count,
            "l": bs.l_count,
            "c": bs.c_count,
            "lc": bs.lc_count,
            "rlc": bs.rlc_count,
        }[dim]
    for bs in bundle_sets:
        grouped[tuple(value(bs, dim) for dim in dims)].append(bs)
    records = []
    for key in sorted(grouped):
        row = {dim: key[i] for i, dim in enumerate(dims)}
        row["distinct_bundle_sets"] = len(grouped[key])
        row["raw_placements"] = sum(bs.raw_placement_count for bs in grouped[key])
        records.append(row)
    if not dims and not records:
        records.append({"distinct_bundle_sets": 0, "raw_placements": 0})
    return BundleSetCensusResult(query, dims, tuple(records), bundle_sets)




# Shared exact grouping/projection helpers for object-language count results.
_GROUPING_DIMS = {"support-edges", "r", "l", "c", "lc", "rlc"}
_COMPONENT_GROUPING_DIMS = {"r", "l", "c", "lc", "rlc"}


def _normalise_group_by(group_by: tuple[str, ...], allowed: set[str], object_name: str) -> tuple[str, ...]:
    if group_by == ("none",):
        return ()
    seen: set[str] = set()
    dims: list[str] = []
    for dim in group_by:
        if dim not in allowed:
            raise ValueError(f"unsupported {object_name} grouping dimension: {dim}")
        if dim in seen:
            raise ValueError(f"duplicate {object_name} grouping dimension: {dim}")
        seen.add(dim)
        dims.append(dim)
    return tuple(dims)


def _fact_value(fact: object, dim: str) -> int:
    if dim == "support-edges":
        return getattr(fact, "source_support_edges")
    if dim == "r":
        return getattr(fact, "r")
    if dim == "l":
        return getattr(fact, "l")
    if dim == "c":
        return getattr(fact, "c")
    if dim == "lc":
        return getattr(fact, "l") + getattr(fact, "c")
    if dim == "rlc":
        return getattr(fact, "r") + getattr(fact, "l") + getattr(fact, "c")
    raise KeyError(dim)


@dataclass(frozen=True)
class AssignmentFact:
    source_support_edges: int
    r: int
    l: int
    c: int
    relevant_supports: int
    distinct_bundle_sets: int
    assignments_per_support: int

    @property
    def raw_assignments(self) -> int:
        return self.relevant_supports * self.assignments_per_support

    def to_json(self) -> dict[str, int]:
        return {
            "source_support_edges": self.source_support_edges,
            "r": self.r,
            "l": self.l,
            "c": self.c,
            "lc": self.l + self.c,
            "rlc": self.r + self.l + self.c,
            "relevant_supports": self.relevant_supports,
            "distinct_bundle_sets": self.distinct_bundle_sets,
            "assignments_per_support": self.assignments_per_support,
            "raw_assignments": self.raw_assignments,
        }


@dataclass(frozen=True)
class AssignmentCensusResult:
    query: CountQuery
    group_by: tuple[str, ...]
    records: tuple[dict[str, int | str], ...]
    facts: tuple[AssignmentFact, ...]

    @property
    def raw_assignments_total(self) -> int:
        return sum(f.raw_assignments for f in self.facts)

    @property
    def distinct_bundle_sets_total(self) -> int:
        return sum(f.distinct_bundle_sets for f in self.facts)

    @property
    def relevant_supports_total(self) -> int:
        return sum({f.source_support_edges: f.relevant_supports for f in self.facts}.values())

    def to_json(self) -> dict[str, object]:
        return {
            "format_version": 1,
            "object": "assignments",
            "query": self.query.to_json(),
            "group_by": list(self.group_by),
            "records": list(self.records),
            "facts": [f.to_json() for f in self.facts],
            "totals": {
                "distinct_bundle_sets": self.distinct_bundle_sets_total,
                "raw_assignments": self.raw_assignments_total,
            },
        }


@dataclass(frozen=True)
class AssignedSupportFact:
    source_support_edges: int
    r: int
    l: int
    c: int
    relevant_supports: int
    raw_assignments: int
    assigned_support_classes: int

    def to_json(self) -> dict[str, int]:
        return {
            "source_support_edges": self.source_support_edges,
            "r": self.r,
            "l": self.l,
            "c": self.c,
            "lc": self.l + self.c,
            "rlc": self.r + self.l + self.c,
            "relevant_supports": self.relevant_supports,
            "raw_assignments": self.raw_assignments,
            "assigned_support_classes": self.assigned_support_classes,
        }


@dataclass(frozen=True)
class AssignedSupportCensusResult:
    query: CountQuery
    group_by: tuple[str, ...]
    records: tuple[dict[str, int], ...]
    facts: tuple[AssignedSupportFact, ...]

    @property
    def raw_assignments_total(self) -> int:
        return sum(f.raw_assignments for f in self.facts)

    @property
    def assigned_support_classes_total(self) -> int:
        return sum(f.assigned_support_classes for f in self.facts)

    def to_json(self) -> dict[str, object]:
        return {
            "format_version": 1,
            "object": "assigned-supports",
            "query": self.query.to_json(),
            "group_by": list(self.group_by),
            "records": list(self.records),
            "facts": [f.to_json() for f in self.facts],
            "totals": {
                "raw_assignments": self.raw_assignments_total,
                "assigned_support_classes": self.assigned_support_classes_total,
            },
        }


@dataclass(frozen=True)
class NetworkRelation:
    name: str
    definition: str
    description: str


LOCAL_SP_RELATION = NetworkRelation(
    name="local-sp",
    definition="canonical-reduced-topology-local-series-parallel-v1",
    description=(
        "internal node renaming, terminal reversal, local commutative series/parallel "
        "normalisation, and duplicate primitive singleton merging; not rational immittance equivalence"
    ),
)
NETWORK_RELATIONS = {LOCAL_SP_RELATION.name: LOCAL_SP_RELATION}


def validate_network_relation(relation: str | NetworkRelation = "local-sp") -> NetworkRelation:
    if isinstance(relation, NetworkRelation):
        relation = relation.name
    try:
        return NETWORK_RELATIONS[relation]
    except KeyError as exc:
        raise ValueError(f"unknown network relation {relation!r}") from exc


@dataclass(frozen=True)
class NetworkFact:
    r: int
    l: int
    c: int
    networks: int

    def to_json(self) -> dict[str, int]:
        return {"r": self.r, "l": self.l, "c": self.c, "lc": self.l + self.c, "rlc": self.r + self.l + self.c, "networks": self.networks}


@dataclass(frozen=True)
class NetworkCensusResult:
    query: CountQuery
    relation: NetworkRelation
    group_by: tuple[str, ...]
    records: tuple[dict[str, int], ...]
    facts: tuple[NetworkFact, ...]
    diagnostics: dict[str, int]

    @property
    def total(self) -> int:
        return sum(f.networks for f in self.facts)

    def matrix(self) -> tuple[tuple[int, ...], ...]:
        max_r = max((f.r for f in self.facts), default=0)
        max_lc = max((f.l + f.c for f in self.facts), default=0)
        counts: Counter[tuple[int, int]] = Counter()
        for f in self.facts:
            counts[(f.r, f.l + f.c)] += f.networks
        return tuple(tuple(counts.get((r, x), 0) for x in range(max_lc + 1)) for r in range(max_r + 1))

    def as_markdown_table(self) -> str:
        table = self.matrix()
        max_lc = len(table[0]) - 1 if table else 0
        headers = ["R \\ L+C"] + [str(x) for x in range(max_lc + 1)] + ["Row total"]
        lines = ["| " + " | ".join(headers) + " |", "|" + "---:|" * len(headers)]
        for r, row in enumerate(table):
            lines.append("| " + " | ".join([str(r), *(str(v) for v in row), str(sum(row))]) + " |")
        return "\n".join(lines)

    def to_json(self) -> dict[str, object]:
        return {
            "format_version": 1,
            "object": "networks",
            "query": self.query.to_json(),
            "relation": self.relation.name,
            "definition": self.relation.definition,
            "group_by": list(self.group_by),
            "records": list(self.records),
            "facts": [f.to_json() for f in self.facts],
            "totals": {"networks": self.total},
            "diagnostics": self.diagnostics,
        }




def _assignment_facts(query: CountQuery) -> tuple[AssignmentFact, ...]:
    edge_range = query.effective_support_edge_range()
    if edge_range.maximum is None or (edge_range.minimum or 1) > edge_range.maximum:
        return ()
    max_edges = edge_range.maximum
    supports = support_census(max_edges=max_edges).relevant_by_edges if max_edges >= 1 else {}
    grouped: DefaultDict[tuple[int, int, int, int], list[BundleSet]] = defaultdict(list)
    for bs in iter_bundle_sets(query):
        grouped[(bs.source_support_edges, bs.r_count, bs.l_count, bs.c_count)].append(bs)
    facts=[]
    for (e,r,l,c), sets in sorted(grouped.items()):
        facts.append(AssignmentFact(e,r,l,c,supports.get(e,0),len(sets),sum(bs.raw_placement_count for bs in sets)))
    return tuple(facts)


def _group_assignment_facts(facts: tuple[AssignmentFact, ...], dims: tuple[str, ...]) -> tuple[dict[str, int | str], ...]:
    grouped: DefaultDict[tuple[int, ...], list[AssignmentFact]] = defaultdict(list)
    for fact in facts:
        grouped[tuple(_fact_value(fact, d) for d in dims)].append(fact)
    records=[]
    for key in sorted(grouped):
        bucket=grouped[key]
        row: dict[str,int|str]={d:key[i] for i,d in enumerate(dims)}
        row["distinct_bundle_sets"]=sum(f.distinct_bundle_sets for f in bucket)
        row["raw_assignments"]=sum(f.raw_assignments for f in bucket)
        if dims == ("support-edges",):
            row["relevant_supports"]=bucket[0].relevant_supports if bucket else 0
            row["assignments_per_support"]=sum(f.assignments_per_support for f in bucket)
        records.append(row)
    if not dims:
        records=[{"distinct_bundle_sets":sum(f.distinct_bundle_sets for f in facts),"raw_assignments":sum(f.raw_assignments for f in facts)}]
    return tuple(records)


def assignment_census(query: CountQuery, group_by: tuple[str, ...] = ("support-edges",)) -> AssignmentCensusResult:
    dims=_normalise_group_by(group_by,_GROUPING_DIMS,"assignment")
    facts=_assignment_facts(query)
    return AssignmentCensusResult(query,dims,_group_assignment_facts(facts,dims),facts)


def _fixed_simple_bundle_labeling_distribution_for_cycles(cycle_lengths: tuple[int,...], query: CountQuery) -> dict[tuple[int,int,int],int]:
    dp: dict[tuple[int,int,int],int] = {(0,0,0):1}
    for cycle_length in cycle_lengths:
        nxt: DefaultDict[tuple[int,int,int],int]=defaultdict(int)
        for (old_r,old_l,old_c), count in dp.items():
            for bundle in SIMPLE_PRIMITIVE_BUNDLES:
                nr=old_r+cycle_length*bundle.r_count
                nl=old_l+cycle_length*int(bundle.l_count)
                nc=old_c+cycle_length*int(bundle.c_count)
                if query.accepts_components(nr,nl,nc):
                    nxt[(nr,nl,nc)] += count
        dp=dict(nxt)
    return dp


def _assigned_support_distribution_for_support(graph: nx.Graph, terminals: tuple[int,int], query: CountQuery, graph_automorphisms: Iterable[dict[int,int]]|None=None) -> dict[tuple[int,int,int],int]:
    autos = automorphisms(graph) if graph_automorphisms is None else list(graph_automorphisms)
    perms=edge_permutations_preserving_terminal_set(graph, terminals, autos)
    if not perms:
        raise ValueError("no automorphism preserves the terminal pair")
    sums: DefaultDict[tuple[int,int,int],int]=defaultdict(int)
    cache: dict[tuple[int,...],dict[tuple[int,int,int],int]]={}
    for perm in perms:
        cyc=permutation_cycle_lengths(perm)
        dist=cache.get(cyc)
        if dist is None:
            dist=_fixed_simple_bundle_labeling_distribution_for_cycles(cyc, query)
            cache[cyc]=dist
        for k,v in dist.items():
            sums[k]+=v
    out={}
    g=len(perms)
    for k,v in sums.items():
        if v % g:
            raise ArithmeticError(f"Burnside coefficient {v} for {k} is not divisible by group size {g}")
        out[k]=v//g
    return out


def assigned_support_census(query: CountQuery, group_by: tuple[str,...] = ("support-edges",)) -> AssignedSupportCensusResult:
    dims=_normalise_group_by(group_by,_GROUPING_DIMS,"assigned-support")
    raw_by_key={(f.source_support_edges,f.r,f.l,f.c):f.raw_assignments for f in _assignment_facts(query)}
    eff=query.effective_support_edge_range()
    max_edges=eff.maximum or 0
    if (eff.minimum or 1) > max_edges:
        facts=()
    else:
        rel=support_census(max_edges=max_edges).relevant_by_edges if max_edges else {}
        counts: DefaultDict[tuple[int,int,int,int],int]=defaultdict(int)
        for graph,terminals,autos in iter_two_terminal_supports(max_edges):
            e=graph.number_of_edges()
            if e < (eff.minimum or 1) or e > max_edges:
                continue
            for (r,l,c), n in _assigned_support_distribution_for_support(graph,terminals,query,autos).items():
                counts[(e,r,l,c)] += n
        facts=tuple(AssignedSupportFact(e,r,l,c,rel.get(e,0),raw_by_key.get((e,r,l,c),0),n) for (e,r,l,c),n in sorted(counts.items()))
    grouped: DefaultDict[tuple[int,...], list[AssignedSupportFact]]=defaultdict(list)
    for f in facts:
        grouped[tuple(_fact_value(f,d) for d in dims)].append(f)
    records=[]
    for key in sorted(grouped):
        bucket=grouped[key]
        row={d:key[i] for i,d in enumerate(dims)}
        row["raw_assignments"]=sum(f.raw_assignments for f in bucket)
        row["assigned_support_classes"]=sum(f.assigned_support_classes for f in bucket)
        if dims == ("support-edges",):
            row["relevant_supports"]=bucket[0].relevant_supports if bucket else 0
        records.append(row)
    if not dims:
        records=[{"raw_assignments":sum(f.raw_assignments for f in facts),"assigned_support_classes":sum(f.assigned_support_classes for f in facts)}]
    return AssignedSupportCensusResult(query,dims,tuple(records),facts)


def _iter_query_edge_assignments(edges: tuple[tuple[int,int],...], query: CountQuery):
    options=SIMPLE_PRIMITIVE_BUNDLES
    def rec(i:int,r:int,l:int,c:int,current:dict[tuple[int,int],SimplePrimitiveBundle]):
        if i == len(edges):
            if query.accepts_components(r,l,c):
                yield dict(current)
            return
        edge=edges[i]
        for b in options:
            nr=r+b.r_count; nl=l+int(b.l_count); nc=c+int(b.c_count)
            if query.accepts_components(nr,nl,nc):
                current[edge]=b
                yield from rec(i+1,nr,nl,nc,current)
                del current[edge]
    yield from rec(0,0,0,0,{})


def network_census(query: CountQuery, relation: str | NetworkRelation = "local-sp", group_by: tuple[str,...] = ("r","lc")) -> NetworkCensusResult:
    rel=validate_network_relation(relation)
    # A finite support-edge range is enough for the source space: each edge takes
    # exactly one of seven simple primitive bundle labels.  Component budgets and
    # support-edge ranges are both valid ways to make network queries finite.
    eff=query.effective_support_edge_range()
    dims=_normalise_group_by(group_by,_COMPONENT_GROUPING_DIMS,"network")
    max_edges=eff.maximum or 0
    signatures: dict[str, tuple[int,int,int]]={}
    if (eff.minimum or 1) <= max_edges:
        for graph,terminals,_autos in iter_two_terminal_supports(max_edges):
            e=graph.number_of_edges()
            if e < (eff.minimum or 1) or e > max_edges:
                continue
            edges=tuple(tuple(sorted(edge)) for edge in graph.edges())
            for assignment in _iter_query_edge_assignments(edges, query):
                sig=canonical_reduced_signature(graph,terminals,assignment)
                r,l,c=reduced_signature_component_counts(sig)
                if query.accepts_components(r,l,c):
                    signatures.setdefault(sig.stable_string(), (r,l,c))
    counts: Counter[tuple[int,int,int]]=Counter(signatures.values())
    facts=tuple(NetworkFact(r,l,c,n) for (r,l,c),n in sorted(counts.items()))
    grouped: DefaultDict[tuple[int,...], list[NetworkFact]]=defaultdict(list)
    for f in facts:
        grouped[tuple(_fact_value(f,d) for d in dims)].append(f)
    records=[]
    for key in sorted(grouped):
        row={d:key[i] for i,d in enumerate(dims)}
        row["networks"]=sum(f.networks for f in grouped[key])
        records.append(row)
    if not dims:
        records=[{"networks":sum(f.networks for f in facts)}]
    raw=assignment_census(query, group_by=("none",)).raw_assignments_total
    assigned=assigned_support_census(query, group_by=("none",)).assigned_support_classes_total
    return NetworkCensusResult(query,rel,dims,tuple(records),facts,{"raw_assignments":raw,"assigned_support_classes":assigned,"unique_reduced_networks":sum(f.networks for f in facts)})


@dataclass(frozen=True)
class _BundleAssignmentCensusResult:
    """Raw phase-2 simple-bundle assignment census.

    ``assignments_per_support_by_edges`` counts assignments of the seven
    reduced-model primitive bundle labels to a single support with that many
    edges, subject only to the global ``R`` and ``L+C`` budgets. These are raw
    leaves: no quotienting by support automorphisms and no reduced-signature
    merging has been applied.
    """

    max_r: int
    max_reactive: int
    max_edges: int
    relevant_supports_by_edges: dict[int, int]
    assignments_per_support_by_edges: dict[int, int]
    leaf_assignments_by_edges: dict[int, int]

    @property
    def relevant_supports_total(self) -> int:
        return sum(self.relevant_supports_by_edges.values())

    @property
    def leaf_assignments_total(self) -> int:
        return sum(self.leaf_assignments_by_edges.values())


@dataclass(frozen=True)
class _BundleLabelingCensusResult:
    """Phase-3 canonical simple-bundle labeling-orbit census.

    Counts are keyed by support-edge count. ``raw_leaf_assignments_by_edges``
    preserves the phase-2 raw assignment leaves.
    ``canonical_labeling_orbits_by_edges`` counts simple primitive bundle
    assignments modulo automorphisms of each terminal-relevant support that
    preserve the unordered terminal pair, including terminal reversal. No local
    series-span or reduced-signature merging is applied.
    """

    max_r: int
    max_reactive: int
    max_edges: int
    relevant_supports_by_edges: dict[int, int]
    raw_leaf_assignments_by_edges: dict[int, int]
    canonical_labeling_orbits_by_edges: dict[int, int]

    @property
    def relevant_supports_total(self) -> int:
        return sum(self.relevant_supports_by_edges.values())

    @property
    def raw_leaf_assignments_total(self) -> int:
        return sum(self.raw_leaf_assignments_by_edges.values())

    @property
    def canonical_labeling_orbits_total(self) -> int:
        return sum(self.canonical_labeling_orbits_by_edges.values())


PrimitiveName = Literal["R", "L", "C"]
FactorKind = Literal["primitive", "series", "parallel"]


@dataclass(frozen=True, order=True)
class ReducedFactor:
    """Immutable recursive factor used by reduced-topology signatures.

    Public helpers that accept ``ReducedFactor`` instances validate and
    normalise caller-supplied values before using them in signatures. Directly
    constructing this dataclass does not itself canonicalise the payload.
    """

    kind: FactorKind
    value: PrimitiveName | tuple["ReducedFactor", ...]

    def stable_key(self) -> tuple[object, ...]:
        if self.kind == "primitive":
            return ("0", self.value)
        return (
            "1" if self.kind == "series" else "2",
            tuple(operand.stable_key() for operand in self.operands),
        )

    @property
    def operands(self) -> tuple["ReducedFactor", ...]:
        if self.kind == "primitive":
            raise TypeError("primitive factors do not have operands")
        assert isinstance(self.value, tuple)
        return self.value

    def stable_string(self) -> str:
        if self.kind == "primitive":
            assert isinstance(self.value, str)
            return self.value
        joiner = "--" if self.kind == "series" else "||"
        pieces = []
        for operand in self.operands:
            text = operand.stable_string()
            if operand.kind != "primitive":
                text = f"({text})"
            pieces.append(text)
        return joiner.join(pieces)


@dataclass(frozen=True, order=True)
class ReducedSignature:
    """Canonical reduced-topology signature for one assigned two-terminal graph."""

    serialization: tuple[tuple[int, int, ReducedFactor], ...]

    def stable_string(self) -> str:
        return ";".join(f"{u}-{v}:{factor.stable_string()}" for u, v, factor in self.serialization)


def primitive_factor(name: str) -> ReducedFactor:
    if name not in {"R", "L", "C"}:
        raise ValueError(f"unknown primitive factor {name!r}")
    return ReducedFactor("primitive", name)  # type: ignore[arg-type]


def _normalise_composition(kind: Literal["series", "parallel"], factors: Iterable[ReducedFactor]) -> ReducedFactor:
    operands: list[ReducedFactor] = []
    primitive_seen: set[PrimitiveName] = set()
    for factor in factors:
        if factor.kind == kind:
            children = factor.operands
        else:
            children = (factor,)
        for child in children:
            if child.kind == "primitive":
                assert isinstance(child.value, str)
                if child.value in primitive_seen:
                    continue
                primitive_seen.add(child.value)  # type: ignore[arg-type]
            operands.append(child)
    if not operands:
        raise ValueError(f"{kind} composition requires at least one factor")
    operands.sort(key=lambda factor: factor.stable_key())
    if len(operands) == 1:
        return operands[0]
    return ReducedFactor(kind, tuple(operands))


def normalise_reduced_factor(factor: ReducedFactor) -> ReducedFactor:
    """Validate and canonicalise a caller-supplied reduced factor.

    Compositions are recursively normalised, nested compositions of the same
    kind are flattened, operands are sorted by :meth:`ReducedFactor.stable_key`,
    duplicate primitive singleton operands are merged, and one-operand
    compositions collapse to that operand. Repeated equal compound operands are
    intentionally preserved because the reduced-topology model does not merge
    repeated subnetwork arms.
    """

    if not isinstance(factor, ReducedFactor):
        raise ValueError(f"expected ReducedFactor, got {type(factor).__name__}")
    if factor.kind == "primitive":
        if factor.value not in {"R", "L", "C"}:
            raise ValueError(f"malformed primitive factor value {factor.value!r}")
        return primitive_factor(factor.value)
    if factor.kind not in {"series", "parallel"}:
        raise ValueError(f"unknown reduced factor kind {factor.kind!r}")
    if not isinstance(factor.value, tuple):
        raise ValueError(f"{factor.kind} factor value must be a tuple of operands")
    if not factor.value:
        raise ValueError(f"{factor.kind} composition requires at least one factor")
    normalised_operands = []
    for operand in factor.value:
        if not isinstance(operand, ReducedFactor):
            raise ValueError(f"{factor.kind} operands must be ReducedFactor instances")
        normalised_operands.append(normalise_reduced_factor(operand))
    if factor.kind == "series":
        return normalise_series_factor(normalised_operands)
    return normalise_parallel_factor(normalised_operands)


def normalise_series_factor(factors: Iterable[ReducedFactor]) -> ReducedFactor:
    """Return an unordered, flattened series factor with primitive duplicates merged."""

    return _normalise_composition("series", factors)


def normalise_parallel_factor(factors: Iterable[ReducedFactor]) -> ReducedFactor:
    """Return an unordered, flattened parallel factor with primitive duplicates merged."""

    return _normalise_composition("parallel", factors)


def factor_from_simple_primitive_bundle(bundle: str | SimplePrimitiveBundle | ReducedFactor) -> ReducedFactor:
    """Convert one bundle/factor input to a validated canonical factor.

    String and :class:`SimplePrimitiveBundle` inputs are parsed as simple
    primitive bundle labels. Caller-supplied :class:`ReducedFactor` inputs are
    recursively validated and normalised through the same canonicalisation
    route used by parsed bundles.
    """

    if isinstance(bundle, ReducedFactor):
        return normalise_reduced_factor(bundle)
    label = bundle.label if isinstance(bundle, SimplePrimitiveBundle) else bundle
    pieces = tuple(part.strip() for part in label.split("||"))
    if not pieces or any(piece not in {"R", "L", "C"} for piece in pieces):
        raise ValueError(f"unknown simple primitive bundle {label!r}")
    factors = [primitive_factor(piece) for piece in pieces]
    return normalise_parallel_factor(factors) if len(factors) > 1 else factors[0]


def _edge_key(edge: tuple[object, object]) -> frozenset[object]:
    u, v = edge
    return frozenset((u, v))


def _validate_assigned_support(
    graph: nx.Graph,
    terminals: tuple[object, object],
    edge_assignments: dict[tuple[object, object], str | SimplePrimitiveBundle | ReducedFactor],
) -> None:
    if len(terminals) != 2 or terminals[0] == terminals[1]:
        raise ValueError("terminals must be two distinct nodes")
    if terminals[0] not in graph or terminals[1] not in graph:
        raise ValueError("both terminals must be graph nodes")
    if graph.is_multigraph():
        raise ValueError("assigned support graph must be simple, not a multigraph")
    if any(u == v for u, v in graph.edges()):
        raise ValueError("self-loops are not valid support edges")
    if not nx.is_connected(graph):
        raise ValueError("assigned support graph must be connected")
    graph_edges = {_edge_key(edge) for edge in graph.edges()}
    assignment_edges: set[frozenset[object]] = set()
    duplicate_edges: set[frozenset[object]] = set()
    for edge in edge_assignments:
        key = _edge_key(edge)
        if key in assignment_edges:
            duplicate_edges.add(key)
        assignment_edges.add(key)
    if duplicate_edges:
        raise ValueError(f"duplicate or ambiguous assignments for undirected support edge(s): {duplicate_edges!r}")
    missing = graph_edges - assignment_edges
    extra = assignment_edges - graph_edges
    if missing:
        raise ValueError(f"missing assignments for support edges: {missing!r}")
    if extra:
        raise ValueError(f"assignments include non-support edges: {extra!r}")
    if not is_two_terminal_relevant(graph, terminals[0], terminals[1]):
        raise ValueError("assigned support graph is not terminal-relevant")


def _merge_parallel_edges(graph: nx.MultiGraph) -> bool:
    changed = False
    for u, v in list(combinations(list(graph.nodes()), 2)):
        data = graph.get_edge_data(u, v, default={})
        if len(data) <= 1:
            continue
        merged = normalise_parallel_factor(edge_data["factor"] for edge_data in data.values())
        graph.remove_edges_from((u, v, key) for key in list(data))
        graph.add_edge(u, v, factor=merged)
        changed = True
    return changed


def _suppress_one_series_node(graph: nx.MultiGraph, terminals: frozenset[object]) -> bool:
    for node in sorted(graph.nodes(), key=repr):
        if node in terminals or graph.degree(node) != 2:
            continue
        incident = list(graph.edges(node, keys=True, data=True))
        if len(incident) != 2:
            continue
        (u1, v1, k1, d1), (u2, v2, k2, d2) = incident
        other1 = v1 if u1 == node else u1
        other2 = v2 if u2 == node else u2
        if other1 == other2:
            continue
        combined = normalise_series_factor([d1["factor"], d2["factor"]])
        graph.remove_edge(u1, v1, k1)
        graph.remove_edge(u2, v2, k2)
        graph.remove_node(node)
        graph.add_edge(other1, other2, factor=combined)
        return True
    return False


def _reduced_factor_multigraph(
    graph: nx.Graph,
    terminals: tuple[object, object],
    edge_assignments: dict[tuple[object, object], str | SimplePrimitiveBundle | ReducedFactor],
) -> nx.MultiGraph:
    _validate_assigned_support(graph, terminals, edge_assignments)
    reduced = nx.MultiGraph()
    reduced.add_nodes_from(graph.nodes())
    assignments = {_edge_key(edge): value for edge, value in edge_assignments.items()}
    for edge in graph.edges():
        u, v = edge
        reduced.add_edge(u, v, factor=factor_from_simple_primitive_bundle(assignments[_edge_key(edge)]))

    terminal_set = frozenset(terminals)
    while True:
        changed = _merge_parallel_edges(reduced)
        changed = _suppress_one_series_node(reduced, terminal_set) or changed
        if not changed:
            break
    return reduced


def canonical_reduced_signature(
    graph: nx.Graph,
    terminals: tuple[object, object],
    edge_assignments: dict[tuple[object, object], str | SimplePrimitiveBundle | ReducedFactor],
) -> ReducedSignature:
    """Reduce one assigned two-terminal support and return its canonical signature."""

    reduced = _reduced_factor_multigraph(graph, terminals, edge_assignments)
    source, target = terminals
    internal_nodes = [node for node in reduced.nodes() if node not in {source, target}]
    best: tuple[tuple[int, int, ReducedFactor], ...] | None = None
    for oriented in ((source, target), (target, source)):
        for perm in permutations(internal_nodes):
            mapping = {oriented[0]: 0, oriented[1]: 1}
            mapping.update({node: index + 2 for index, node in enumerate(perm)})
            serialized = tuple(
                sorted(
                    (min(mapping[u], mapping[v]), max(mapping[u], mapping[v]), data["factor"])
                    for u, v, data in reduced.edges(data=True)
                )
            )
            if best is None or serialized < best:
                best = serialized
    assert best is not None
    return ReducedSignature(best)



@dataclass(frozen=True)
class _ReducedTopologyCensusResult:
    """End-to-end reduced-topology census result.

    ``exact_table`` is indexed as ``exact_table[r][x]`` where ``x = L+C`` in
    the canonical reduced signatures. ``canonical_signatures`` is a
    deterministic tuple of stable signature strings suitable for catalogue
    generation and duplicate checks.
    """

    max_r: int
    max_reactive: int
    max_edges: int
    exact_table: tuple[tuple[int, ...], ...]
    canonical_signatures: tuple[str, ...]
    raw_leaf_assignments_total: int
    canonical_labeling_orbits_total: int

    @property
    def total(self) -> int:
        return sum(sum(row) for row in self.exact_table)

    def as_markdown_table(self) -> str:
        headers = (
            ["R \\ L+C"]
            + [str(x) for x in range(self.max_reactive + 1)]
            + ["Row total"]
        )
        lines = ["| " + " | ".join(headers) + " |"]
        lines.append("|" + "---:|" * len(headers))
        for r, row in enumerate(self.exact_table):
            values = [str(r)] + [str(v) for v in row] + [str(sum(row))]
            lines.append("| " + " | ".join(values) + " |")
        return "\n".join(lines)


def graph_invariant(graph: nx.Graph) -> tuple[object, ...]:
    """Cheap invariant used to bucket candidate simple graphs.

    Isomorphism testing is still used inside each bucket, so this does not need
    to be a complete canonical form.
    """

    degree_sequence = tuple(sorted(dict(graph.degree()).values()))
    triangle_count = sum(nx.triangles(graph).values()) // 3 if graph.number_of_nodes() > 2 else 0
    return (graph.number_of_nodes(), graph.number_of_edges(), degree_sequence, triangle_count)


def _add_unique(bucketed_graphs: DefaultDict[tuple[object, ...], list[nx.Graph]], graph: nx.Graph) -> bool:
    key = graph_invariant(graph)
    for existing in bucketed_graphs[key]:
        if nx.is_isomorphic(graph, existing):
            return False
    bucketed_graphs[key].append(graph.copy())
    return True


def generate_connected_unlabelled_simple_graphs(max_edges: int) -> list[list[nx.Graph]]:
    """Generate connected unlabelled simple graphs with up to ``max_edges``.

    ``levels[m]`` contains one representative for every connected unlabelled
    simple graph with exactly ``m`` edges.  The method uses canonical
    augmentation in a pragmatic form: every connected graph can be obtained by
    repeatedly adding either a missing edge between existing vertices or a new
    leaf edge, and duplicates are removed by graph isomorphism.
    """

    levels: list[list[nx.Graph]] = []
    initial = nx.Graph()
    initial.add_node(0)
    levels.append([initial])

    for edge_count in range(1, max_edges + 1):
        bucketed: DefaultDict[tuple[object, ...], list[nx.Graph]] = defaultdict(list)
        for graph in levels[edge_count - 1]:
            nodes = sorted(graph.nodes())
            new_node = max(nodes) + 1

            # Add a new vertex joined by one edge.  This is enough to grow any
            # connected graph alongside adding missing edges between old nodes.
            for node in nodes:
                candidate = graph.copy()
                candidate.add_node(new_node)
                candidate.add_edge(node, new_node)
                _add_unique(bucketed, candidate)

            # Add any missing simple edge between existing vertices.
            for i, u in enumerate(nodes):
                for v in nodes[i + 1 :]:
                    if not graph.has_edge(u, v):
                        candidate = graph.copy()
                        candidate.add_edge(u, v)
                        _add_unique(bucketed, candidate)

        levels.append([graph for graphs in bucketed.values() for graph in graphs])

    return levels


def automorphisms(graph: nx.Graph) -> list[dict[int, int]]:
    return list(iso.GraphMatcher(graph, graph).isomorphisms_iter())


def simple_path_edge_cover(graph: nx.Graph, source: object, target: object) -> set[frozenset[object]]:
    """Return the support edges lying on at least one simple source-target path."""

    used: set[frozenset[object]] = set()
    for path in nx.all_simple_paths(graph, source, target, cutoff=graph.number_of_nodes() - 1):
        for u, v in zip(path, path[1:]):
            used.add(frozenset((u, v)))
    return used


def is_two_terminal_relevant(graph: nx.Graph, source: object, target: object) -> bool:
    """Check whether every support edge lies on a simple terminal-terminal path.

    This removes dangling appendages and other branches that are not part of the
    driving-point one-port core.  It is deliberately implemented by enumerating
    simple terminal paths, rather than by a merely connectedness-based bridge
    test, because connectedness alone incorrectly admits edges on non-simple
    walks.
    """

    all_edges = {frozenset(edge) for edge in graph.edges()}
    return simple_path_edge_cover(graph, source, target) == all_edges


def terminal_pair_orbit_representatives(
    graph: nx.Graph, graph_automorphisms: Iterable[dict[int, int]]
) -> list[tuple[int, int]]:
    """Return unordered terminal-pair orbit representatives for a support graph.

    Terminal pairs are quotiented by support-graph automorphisms. Terminal
    reversal is already removed by representing each pair as a sorted tuple.
    No terminal-relevance filtering is applied here.
    """

    autos = list(graph_automorphisms)
    representatives: list[tuple[int, int]] = []
    seen: set[tuple[int, int]] = set()

    for pair in combinations(sorted(graph.nodes()), 2):
        if pair in seen:
            continue
        a, b = pair
        orbit = {tuple(sorted((mapping[a], mapping[b]))) for mapping in autos}
        seen |= orbit
        representatives.append(min(orbit))

    return representatives


def relevant_terminal_pair_orbit_representatives(
    graph: nx.Graph, graph_automorphisms: Iterable[dict[int, int]]
) -> list[tuple[int, int]]:
    """Return terminal-pair orbit representatives that pass relevance filtering."""

    return [
        (source, target)
        for source, target in terminal_pair_orbit_representatives(graph, graph_automorphisms)
        if is_two_terminal_relevant(graph, source, target)
    ]


def edge_permutations_preserving_terminal_set(
    graph: nx.Graph,
    terminals: tuple[int, int],
    graph_automorphisms: Iterable[dict[int, int]],
) -> list[tuple[int, ...]]:
    """Return induced edge permutations for automorphisms preserving terminals setwise.

    Terminals are treated as an unordered pair.  Therefore an automorphism may
    either fix the terminal nodes individually or swap them.
    """

    source, target = terminals
    terminal_set = {source, target}
    edge_list = sorted(tuple(sorted(edge)) for edge in graph.edges())
    edge_index = {edge: i for i, edge in enumerate(edge_list)}

    permutations: list[tuple[int, ...]] = []
    seen: set[tuple[int, ...]] = set()

    for mapping in graph_automorphisms:
        if {mapping[source], mapping[target]} != terminal_set:
            continue
        permutation = []
        for u, v in edge_list:
            image_edge = tuple(sorted((mapping[u], mapping[v])))
            permutation.append(edge_index[image_edge])
        permutation_tuple = tuple(permutation)
        if permutation_tuple not in seen:
            seen.add(permutation_tuple)
            permutations.append(permutation_tuple)

    return permutations


def permutation_cycle_lengths(permutation: tuple[int, ...]) -> tuple[int, ...]:
    seen = [False] * len(permutation)
    lengths: list[int] = []
    for start in range(len(permutation)):
        if seen[start]:
            continue
        node = start
        length = 0
        while not seen[node]:
            seen[node] = True
            length += 1
            node = permutation[node]
        lengths.append(length)
    return tuple(sorted(lengths))


def iter_two_terminal_supports(max_edges: int):
    """Yield terminal-relevant support representatives for every enumeration stage.

    This is the shared support-enumeration entry point used by object-language
    assignment, assigned-support, and network counting implementations.
    """

    levels = generate_connected_unlabelled_simple_graphs(max_edges)
    for edge_count in range(1, max_edges + 1):
        for graph in levels[edge_count]:
            autos = automorphisms(graph)
            for terminals in relevant_terminal_pair_orbit_representatives(graph, autos):
                yield graph, terminals, autos


def support_census(max_edges: int = 8) -> SupportCensusResult:
    """Enumerate the phase-1 support graph census up to ``max_edges``.

    This deliberately stops before component assignment, simple bundles, series
    spans, or reduced signatures.
    """

    if max_edges < 1:
        raise ValueError("max_edges must be at least 1")

    levels = generate_connected_unlabelled_simple_graphs(max_edges)
    basic_by_edges: dict[int, int] = {}
    terminal_labelings_by_edges: dict[int, int] = {}
    relevant_by_edges: dict[int, int] = {}

    for edge_count in range(1, max_edges + 1):
        basic_by_edges[edge_count] = len(levels[edge_count])
        terminal_labelings = 0
        relevant = 0
        for graph in levels[edge_count]:
            autos = automorphisms(graph)
            terminal_pairs = terminal_pair_orbit_representatives(graph, autos)
            terminal_labelings += len(terminal_pairs)
            relevant += sum(
                1 for source, target in terminal_pairs if is_two_terminal_relevant(graph, source, target)
            )
        terminal_labelings_by_edges[edge_count] = terminal_labelings
        relevant_by_edges[edge_count] = relevant

    return SupportCensusResult(
        max_edges=max_edges,
        basic_by_edges=basic_by_edges,
        terminal_labelings_by_edges=terminal_labelings_by_edges,
        relevant_by_edges=relevant_by_edges,
    )


def simple_bundle_assignment_count_by_edge_count(
    max_edges: int, max_r: int = 3, max_reactive: int = 5
) -> dict[int, int]:
    """Count raw simple-bundle assignments for one support of each edge count."""

    if max_edges < 1:
        raise ValueError("max_edges must be at least 1")
    if max_r < 0 or max_reactive < 0:
        raise ValueError("component limits must be non-negative")

    dp: dict[tuple[int, int], int] = {(0, 0): 1}
    counts_by_edges: dict[int, int] = {}

    for edge_count in range(1, max_edges + 1):
        next_dp: DefaultDict[tuple[int, int], int] = defaultdict(int)
        for (old_r, old_x), count in dp.items():
            for bundle in SIMPLE_PRIMITIVE_BUNDLES:
                new_r = old_r + bundle.r_count
                new_x = old_x + bundle.reactive_count
                if new_r <= max_r and new_x <= max_reactive:
                    next_dp[(new_r, new_x)] += count
        dp = dict(next_dp)
        counts_by_edges[edge_count] = sum(dp.values())

    return counts_by_edges


def _simple_bundle_assignment_census(
    max_r: int = 3, max_reactive: int = 5, max_edges: int | None = None
) -> _BundleAssignmentCensusResult:
    """Run the phase-2 raw simple primitive bundle-assignment census."""

    if max_r < 0 or max_reactive < 0:
        raise ValueError("component limits must be non-negative")
    natural_max_edges = max_r + max_reactive
    resolved_max_edges = natural_max_edges if max_edges is None else max_edges
    if resolved_max_edges < 0:
        raise ValueError("max_edges must be non-negative")
    if natural_max_edges > 0 and resolved_max_edges < 1:
        raise ValueError(
            "max_edges must be at least 1 when component budgets are positive"
        )
    if resolved_max_edges > natural_max_edges:
        raise ValueError("max_edges cannot exceed max_r + max_reactive")
    if resolved_max_edges == 0:
        return _BundleAssignmentCensusResult(
            max_r=max_r,
            max_reactive=max_reactive,
            max_edges=0,
            relevant_supports_by_edges={},
            assignments_per_support_by_edges={},
            leaf_assignments_by_edges={},
        )

    supports = support_census(max_edges=resolved_max_edges).relevant_by_edges
    assignments = simple_bundle_assignment_count_by_edge_count(
        resolved_max_edges, max_r=max_r, max_reactive=max_reactive
    )
    leaves = {
        edge_count: supports[edge_count] * assignments[edge_count]
        for edge_count in range(1, resolved_max_edges + 1)
    }

    return _BundleAssignmentCensusResult(
        max_r=max_r,
        max_reactive=max_reactive,
        max_edges=resolved_max_edges,
        relevant_supports_by_edges=supports,
        assignments_per_support_by_edges=assignments,
        leaf_assignments_by_edges=leaves,
    )


def _fixed_simple_bundle_labelings_for_cycles(
    cycle_lengths: tuple[int, ...], max_r: int, max_reactive: int
) -> int:
    """Count simple-bundle labelings fixed by an edge permutation.

    A labeling fixed by a permutation is constant on each edge cycle. The
    component-budget weight of a bundle assigned to a cycle is multiplied by
    the cycle length, because every edge in that cycle receives that bundle.
    """

    dp: dict[tuple[int, int], int] = {(0, 0): 1}
    for cycle_length in cycle_lengths:
        next_dp: DefaultDict[tuple[int, int], int] = defaultdict(int)
        for (old_r, old_x), count in dp.items():
            for bundle in SIMPLE_PRIMITIVE_BUNDLES:
                new_r = old_r + cycle_length * bundle.r_count
                new_x = old_x + cycle_length * bundle.reactive_count
                if new_r <= max_r and new_x <= max_reactive:
                    next_dp[(new_r, new_x)] += count
        dp = dict(next_dp)
    return sum(dp.values())


def _simple_bundle_labeling_orbit_count(
    graph: nx.Graph,
    terminals: tuple[int, int],
    max_r: int = 3,
    max_reactive: int = 5,
    graph_automorphisms: Iterable[dict[int, int]] | None = None,
) -> int:
    """Count canonical simple-bundle labelings of one two-terminal support.

    The quotient group is the set of support automorphisms whose image of the
    terminal pair is the same unordered pair; automorphisms may swap the two
    terminals. The action permutes support edges, and Burnside's lemma counts
    assignment orbits under the global ``R`` and ``L+C`` budgets.
    """

    if max_r < 0 or max_reactive < 0:
        raise ValueError("component limits must be non-negative")
    autos = (
        automorphisms(graph)
        if graph_automorphisms is None
        else list(graph_automorphisms)
    )
    edge_permutations = edge_permutations_preserving_terminal_set(graph, terminals, autos)
    if not edge_permutations:
        raise ValueError("no automorphism preserves the terminal pair")

    total_fixed = 0
    fixed_cache: dict[tuple[int, ...], int] = {}
    for permutation in edge_permutations:
        cycle_lengths = permutation_cycle_lengths(permutation)
        fixed = fixed_cache.get(cycle_lengths)
        if fixed is None:
            fixed = _fixed_simple_bundle_labelings_for_cycles(
                cycle_lengths, max_r, max_reactive
            )
            fixed_cache[cycle_lengths] = fixed
        total_fixed += fixed

    group_size = len(edge_permutations)
    if total_fixed % group_size != 0:
        raise ArithmeticError(
            f"Burnside sum {total_fixed} is not divisible by group size {group_size}"
        )
    return total_fixed // group_size


def _simple_bundle_labeling_census(
    max_r: int = 3, max_reactive: int = 5, max_edges: int | None = None
) -> _BundleLabelingCensusResult:
    """Run the phase-3 canonical simple-bundle labeling-orbit census."""

    if max_r < 0 or max_reactive < 0:
        raise ValueError("component limits must be non-negative")
    natural_max_edges = max_r + max_reactive
    resolved_max_edges = natural_max_edges if max_edges is None else max_edges
    if resolved_max_edges < 0:
        raise ValueError("max_edges must be non-negative")
    if natural_max_edges > 0 and resolved_max_edges < 1:
        raise ValueError(
            "max_edges must be at least 1 when component budgets are positive"
        )
    if resolved_max_edges > natural_max_edges:
        raise ValueError("max_edges cannot exceed max_r + max_reactive")
    if resolved_max_edges == 0:
        return _BundleLabelingCensusResult(
            max_r=max_r,
            max_reactive=max_reactive,
            max_edges=0,
            relevant_supports_by_edges={},
            raw_leaf_assignments_by_edges={},
            canonical_labeling_orbits_by_edges={},
        )

    raw = _simple_bundle_assignment_census(
        max_r=max_r, max_reactive=max_reactive, max_edges=resolved_max_edges
    )
    canonical_by_edges: Counter[int] = Counter()

    for graph, terminals, autos in iter_two_terminal_supports(resolved_max_edges):
        canonical_by_edges[graph.number_of_edges()] += _simple_bundle_labeling_orbit_count(
            graph,
            terminals,
            max_r=max_r,
            max_reactive=max_reactive,
            graph_automorphisms=autos,
        )

    return _BundleLabelingCensusResult(
        max_r=max_r,
        max_reactive=max_reactive,
        max_edges=resolved_max_edges,
        relevant_supports_by_edges=raw.relevant_supports_by_edges,
        raw_leaf_assignments_by_edges=raw.leaf_assignments_by_edges,
        canonical_labeling_orbits_by_edges={
            edge_count: canonical_by_edges[edge_count]
            for edge_count in range(1, resolved_max_edges + 1)
        },
    )


def _component_counts_for_factor(factor: ReducedFactor) -> tuple[int, int, int]:
    if factor.kind == "primitive":
        if factor.value == "R":
            return (1, 0, 0)
        if factor.value == "L":
            return (0, 1, 0)
        return (0, 0, 1)
    r = l = c = 0
    for operand in factor.operands:
        rr, ll, cc = _component_counts_for_factor(operand)
        r += rr
        l += ll
        c += cc
    return r, l, c


def reduced_signature_component_counts(
    signature: ReducedSignature,
) -> tuple[int, int, int]:
    """Return exact primitive ``(R, L, C)`` counts present in a reduced signature."""

    r = l = c = 0
    for _u, _v, factor in signature.serialization:
        rr, ll, cc = _component_counts_for_factor(factor)
        r += rr
        l += ll
        c += cc
    return r, l, c


def _assignment_options_by_budget(
    max_r: int, max_reactive: int
) -> list[SimplePrimitiveBundle]:
    return [
        bundle
        for bundle in SIMPLE_PRIMITIVE_BUNDLES
        if bundle.r_count <= max_r and bundle.reactive_count <= max_reactive
    ]


def _iter_budgeted_edge_assignments(
    edges: tuple[tuple[int, int], ...], max_r: int, max_reactive: int
):
    options = _assignment_options_by_budget(max_r, max_reactive)

    def rec(
        index: int,
        used_r: int,
        used_x: int,
        current: dict[tuple[int, int], SimplePrimitiveBundle],
    ):
        if index == len(edges):
            yield dict(current)
            return
        edge = edges[index]
        for bundle in options:
            new_r = used_r + bundle.r_count
            new_x = used_x + bundle.reactive_count
            if new_r <= max_r and new_x <= max_reactive:
                current[edge] = bundle
                yield from rec(index + 1, new_r, new_x, current)
                del current[edge]

    yield from rec(0, 0, 0, {})


def _iter_reduced_topology_signatures(
    max_r: int = 3, max_reactive: int = 5, max_edges: int | None = None
):
    """Yield unique canonical reduced signatures deterministically for a budget slice."""

    if max_r < 0 or max_reactive < 0:
        raise ValueError("component limits must be non-negative")
    natural_max_edges = max_r + max_reactive
    resolved_max_edges = natural_max_edges if max_edges is None else max_edges
    if resolved_max_edges < 1:
        return
    if resolved_max_edges > natural_max_edges:
        raise ValueError("max_edges cannot exceed max_r + max_reactive")

    signatures: dict[str, ReducedSignature] = {}
    for graph, terminals, _autos in iter_two_terminal_supports(resolved_max_edges):
        edges = tuple(tuple(sorted(edge)) for edge in graph.edges())
        for assignment in _iter_budgeted_edge_assignments(edges, max_r, max_reactive):
            signature = canonical_reduced_signature(graph, terminals, assignment)
            r, l, c = reduced_signature_component_counts(signature)
            if r <= max_r and l + c <= max_reactive:
                signatures.setdefault(signature.stable_string(), signature)

    for key in sorted(signatures):
        yield signatures[key]


def _reduced_topology_census(
    max_r: int = 3, max_reactive: int = 5, max_edges: int | None = None
) -> _ReducedTopologyCensusResult:
    """Run the first end-to-end canonical reduced-topology census."""

    if max_r < 0 or max_reactive < 0:
        raise ValueError("component limits must be non-negative")
    natural_max_edges = max_r + max_reactive
    resolved_max_edges = natural_max_edges if max_edges is None else max_edges
    if resolved_max_edges < 1:
        raise ValueError("max_edges must be at least 1")
    if resolved_max_edges > natural_max_edges:
        raise ValueError("max_edges cannot exceed max_r + max_reactive")

    raw = _simple_bundle_assignment_census(
        max_r=max_r, max_reactive=max_reactive, max_edges=resolved_max_edges
    )
    labelings = _simple_bundle_labeling_census(
        max_r=max_r, max_reactive=max_reactive, max_edges=resolved_max_edges
    )
    counts: DefaultDict[tuple[int, int], int] = defaultdict(int)
    stable_strings: list[str] = []

    for signature in _iter_reduced_topology_signatures(
        max_r=max_r, max_reactive=max_reactive, max_edges=resolved_max_edges
    ):
        r, l, c = reduced_signature_component_counts(signature)
        x = l + c
        counts[(r, x)] += 1
        stable_strings.append(signature.stable_string())

    table = tuple(
        tuple(counts.get((r, x), 0) for x in range(max_reactive + 1))
        for r in range(max_r + 1)
    )
    return _ReducedTopologyCensusResult(
        max_r=max_r,
        max_reactive=max_reactive,
        max_edges=resolved_max_edges,
        exact_table=table,
        canonical_signatures=tuple(stable_strings),
        raw_leaf_assignments_total=raw.leaf_assignments_total,
        canonical_labeling_orbits_total=labelings.canonical_labeling_orbits_total,
    )

# Provisional object enumeration and reduction-provenance API.
import hashlib
DEFAULT_ENUM_MAX_RECORDS = 10000


def _digest(prefix: str, payload: object, length: int = 16) -> str:
    data = repr(payload).encode("utf-8")
    return f"{prefix}-{hashlib.sha256(data).hexdigest()[:length]}"


def _support_canonical_data(graph: nx.Graph, terminals: tuple[object, object]) -> tuple[tuple[int, int], tuple[tuple[int, int], ...]]:
    nodes = list(graph.nodes())
    s, t = terminals
    internal = [n for n in nodes if n not in {s, t}]
    best: tuple[tuple[int, int], tuple[tuple[int, int], ...]] | None = None
    for a, b in ((s, t), (t, s)):
        for perm in permutations(internal):
            mapping = {a: 0, b: 1}
            mapping.update({node: i + 2 for i, node in enumerate(perm)})
            edges = tuple(sorted((min(mapping[u], mapping[v]), max(mapping[u], mapping[v])) for u, v in graph.edges()))
            data = ((0, 1), edges)
            if best is None or data < best:
                best = data
    assert best is not None
    return best


@dataclass(frozen=True)
class SupportRecord:
    support_id: str
    source_support_edges: int
    node_count: int
    terminals: tuple[int, int]
    edge_list: tuple[tuple[int, int], ...]
    graph: nx.Graph
    original_terminals: tuple[object, object]
    automorphisms: tuple[dict[int, int], ...]

    def to_json(self) -> dict[str, object]:
        return {"support_id": self.support_id, "source_support_edges": self.source_support_edges, "node_count": self.node_count, "terminals": list(self.terminals), "edge_list": [list(e) for e in self.edge_list]}


@dataclass(frozen=True)
class BundleTypeRecord:
    bundle_type_id: str
    label: str
    r: int
    l: int
    c: int
    lc: int
    rlc: int
    def to_json(self) -> dict[str, object]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class BundleSetRecord:
    bundle_set_id: str
    source_support_edges: int
    multiplicities: tuple[int, ...]
    r: int
    l: int
    c: int
    lc: int
    rlc: int
    raw_placement_count: int
    bundle_set: BundleSet
    def to_json(self) -> dict[str, object]:
        return {"bundle_set_id": self.bundle_set_id, "source_support_edges": self.source_support_edges, "multiplicities": dict(zip((b.label for b in SIMPLE_PRIMITIVE_BUNDLES), self.multiplicities)), "r": self.r, "l": self.l, "c": self.c, "lc": self.lc, "rlc": self.rlc, "raw_placement_count": self.raw_placement_count}


@dataclass(frozen=True)
class AssignmentRecord:
    assignment_id: str
    support_id: str
    bundle_set_id: str
    source_support_edges: int
    r: int
    l: int
    c: int
    lc: int
    rlc: int
    edge_assignments: tuple[tuple[tuple[int, int], str], ...]
    def to_json(self) -> dict[str, object]:
        return {"assignment_id": self.assignment_id, "support_id": self.support_id, "bundle_set_id": self.bundle_set_id, "source_support_edges": self.source_support_edges, "r": self.r, "l": self.l, "c": self.c, "lc": self.lc, "rlc": self.rlc, "edge_assignments": [[list(e), lab] for e, lab in self.edge_assignments]}


@dataclass(frozen=True)
class AssignedSupportRecord:
    assigned_support_id: str
    support_id: str
    source_support_edges: int
    r: int
    l: int
    c: int
    lc: int
    rlc: int
    canonical_edge_assignments: tuple[tuple[tuple[int, int], str], ...]
    orbit_size: int
    raw_assignment_count: int
    assignment_ids: tuple[str, ...]
    def to_json(self) -> dict[str, object]:
        return {"assigned_support_id": self.assigned_support_id, "support_id": self.support_id, "source_support_edges": self.source_support_edges, "r": self.r, "l": self.l, "c": self.c, "lc": self.lc, "rlc": self.rlc, "canonical_edge_assignments": [[list(e), lab] for e, lab in self.canonical_edge_assignments], "orbit_size": self.orbit_size, "raw_assignment_count": self.raw_assignment_count}


@dataclass(frozen=True)
class NetworkRecord:
    network_id: str
    relation: str
    definition: str
    r: int
    l: int
    c: int
    lc: int
    rlc: int
    canonical_signature: str
    source_assignment_count: int
    assigned_support_count: int
    min_source_support_edges: int
    max_source_support_edges: int
    assigned_support_ids: tuple[str, ...]
    support_ids: tuple[str, ...]
    source_component_tuples: tuple[tuple[int, int, int], ...]
    def to_json(self) -> dict[str, object]:
        return {k: v for k, v in self.__dict__.items() if k not in {"assigned_support_ids", "support_ids", "source_component_tuples"}}


def enum_supports(query: CountQuery) -> tuple[SupportRecord, ...]:
    eff = query.effective_support_edge_range(); max_edges = eff.maximum or 0
    if (eff.minimum or 1) > max_edges: return ()
    records = []
    for graph, terminals, autos in iter_two_terminal_supports(max_edges):
        if not ((eff.minimum or 1) <= graph.number_of_edges() <= max_edges): continue
        terms, edges = _support_canonical_data(graph, terminals)
        sid = _digest("support", (terms, edges))
        canonical_graph = nx.Graph()
        canonical_graph.add_nodes_from(range(len(graph.nodes())))
        canonical_graph.add_edges_from(edges)
        canonical_autos = tuple(automorphisms(canonical_graph))
        records.append(SupportRecord(sid, len(edges), len(graph.nodes()), terms, edges, canonical_graph, terms, canonical_autos))
    return tuple(sorted(records, key=lambda r: (r.source_support_edges, r.node_count, r.edge_list, r.support_id)))


def enum_bundle_types(query: CountQuery | None = None) -> tuple[BundleTypeRecord, ...]:
    del query  # accepted for consistency with the provisional enumeration API
    return tuple(
        BundleTypeRecord(
            _digest("bundle-type", bundle.label),
            bundle.label,
            bundle.r_count,
            int(bundle.l_count),
            int(bundle.c_count),
            bundle.reactive_count,
            bundle.r_count + bundle.reactive_count,
        )
        for bundle in SIMPLE_PRIMITIVE_BUNDLES
    )


def enum_bundle_sets(query: CountQuery) -> tuple[BundleSetRecord, ...]:
    records = []
    for bundle_set in iter_bundle_sets(query):
        records.append(
            BundleSetRecord(
                _digest("bundle-set", bundle_set.multiplicities),
                bundle_set.source_support_edges,
                bundle_set.multiplicities,
                bundle_set.r_count,
                bundle_set.l_count,
                bundle_set.c_count,
                bundle_set.lc_count,
                bundle_set.rlc_count,
                bundle_set.raw_placement_count,
                bundle_set,
            )
        )
    return tuple(
        sorted(
            records,
            key=lambda record: (
                record.source_support_edges,
                record.r,
                record.l,
                record.c,
                record.multiplicities,
            ),
        )
    )


def _enforce_limit(n: int, max_records: int, what: str) -> None:
    if max_records < 1:
        raise ValueError("max_records must be a positive integer")
    if n > max_records:
        raise ValueError(
            f"{what} would produce {n} records, exceeding --max-records "
            f"{max_records}; use tighter limits, a small profile, or an explicit "
            "higher --max-records"
        )


def enum_assignments(query: CountQuery, max_records: int = DEFAULT_ENUM_MAX_RECORDS) -> tuple[AssignmentRecord, ...]:
    query.effective_support_edge_range()
    est = assignment_census(query, group_by=("none",)).raw_assignments_total; _enforce_limit(est, max_records, "assignment enumeration")
    supports = enum_supports(query); bs_records = enum_bundle_sets(query); bs_by_mult={b.multiplicities:b for b in bs_records}
    out=[]
    for sr in supports:
        labels=[b.label for b in SIMPLE_PRIMITIVE_BUNDLES]
        by_label={b.label:b for b in SIMPLE_PRIMITIVE_BUNDLES}
        for combo in product(labels, repeat=sr.source_support_edges):
            r=sum(by_label[x].r_count for x in combo); l=sum(int(by_label[x].l_count) for x in combo); c=sum(int(by_label[x].c_count) for x in combo)
            if not query.accepts_components(r,l,c): continue
            mult=tuple(combo.count(b.label) for b in SIMPLE_PRIMITIVE_BUNDLES); br=bs_by_mult[mult]
            ea=tuple(zip(sr.edge_list, combo))
            aid=_digest("assignment", (sr.support_id, ea))
            out.append(AssignmentRecord(aid, sr.support_id, br.bundle_set_id, sr.source_support_edges, r,l,c,l+c,r+l+c, ea))
    return tuple(sorted(out, key=lambda r:(r.source_support_edges,r.r,r.l,r.c,r.support_id,r.edge_assignments,r.assignment_id)))


def _canon_assignment_under_perms(labels: tuple[str,...], edge_list: tuple[tuple[int,int],...], perms: list[tuple[int,...]]) -> tuple[str,...]:
    reps=[]
    for p in perms:
        new=[None]*len(labels)
        for i,j in enumerate(p): new[j]=labels[i]
        reps.append(tuple(new))
    return min(reps)  # type: ignore[arg-type]


def enum_assigned_supports(query: CountQuery, max_records: int = DEFAULT_ENUM_MAX_RECORDS) -> tuple[AssignedSupportRecord, ...]:
    assignments=enum_assignments(query, max_records=max_records)
    supports={s.support_id:s for s in enum_supports(query)}
    buckets: DefaultDict[tuple[str, tuple[str,...]], list[AssignmentRecord]] = defaultdict(list)
    for ar in assignments:
        sr=supports[ar.support_id]
        perms=edge_permutations_preserving_terminal_set(sr.graph, sr.original_terminals, sr.automorphisms)
        labels=tuple(label for _e,label in ar.edge_assignments)
        canon=_canon_assignment_under_perms(labels, sr.edge_list, perms)
        buckets[(ar.support_id, canon)].append(ar)
    out=[]
    for (sid, canon), ars in buckets.items():
        sr=supports[sid]; sample=ars[0]
        ce=tuple(zip(sr.edge_list, canon)); asid=_digest("assigned-support", (sid, ce))
        out.append(AssignedSupportRecord(asid,sid,sr.source_support_edges,sample.r,sample.l,sample.c,sample.lc,sample.rlc,ce,len(ars),len(ars),tuple(sorted(a.assignment_id for a in ars))))
    _enforce_limit(len(out), max_records, "assigned-support enumeration")
    return tuple(sorted(out, key=lambda r:(r.source_support_edges,r.r,r.l,r.c,r.support_id,r.canonical_edge_assignments,r.assigned_support_id)))


def enum_networks(query: CountQuery, relation: str | NetworkRelation = "local-sp", max_records: int = DEFAULT_ENUM_MAX_RECORDS) -> tuple[NetworkRecord, ...]:
    rel=validate_network_relation(relation)
    assigned=enum_assigned_supports(query, max_records=max_records)
    supports={s.support_id:s for s in enum_supports(query)}
    grouped: dict[str, dict[str, object]]={}
    for ar in assigned:
        sr=supports[ar.support_id]
        edge_assign={tuple(e): lab for e,lab in ar.canonical_edge_assignments}
        sig=canonical_reduced_signature(sr.graph, sr.original_terminals, edge_assign)
        sigs=sig.stable_string(); rr,rl,rc=reduced_signature_component_counts(sig)
        if not query.accepts_components(rr,rl,rc): continue
        nid=_digest("network", (rel.name, sigs))
        g=grouped.setdefault(nid,{"sig":sigs,"r":rr,"l":rl,"c":rc,"assign":0,"assigned":0,"edges":[],"asid":[],"sid":set(),"src":set()})
        g["assign"] = int(g["assign"]) + ar.raw_assignment_count; g["assigned"] = int(g["assigned"]) + 1
        g["edges"].append(ar.source_support_edges); g["asid"].append(ar.assigned_support_id); g["sid"].add(ar.support_id); g["src"].add((ar.r,ar.l,ar.c))
    out=[]
    for nid,g in grouped.items():
        r,l,c=int(g["r"]),int(g["l"]),int(g["c"]); edges=list(g["edges"])
        out.append(NetworkRecord(nid,rel.name,rel.definition,r,l,c,l+c,r+l+c,str(g["sig"]),int(g["assign"]),int(g["assigned"]),min(edges),max(edges),tuple(sorted(g["asid"])),tuple(sorted(g["sid"])),tuple(sorted(g["src"]))))
    _enforce_limit(len(out), max_records, "network enumeration")
    return tuple(sorted(out, key=lambda r:(r.r,r.l+r.c,r.l,r.c,r.network_id)))


@dataclass(frozen=True)
class ReductionCensusResult:
    query: CountQuery
    relation: NetworkRelation
    pipeline_totals: dict[str,int]
    fibre_distributions: dict[str, tuple[dict[str,int], ...]]
    source_edge_transitions: tuple[dict[str,int], ...]
    component_transitions: tuple[dict[str,int], ...]
    collision_summary: dict[str, object]
    diagnostics: dict[str, object]
    def to_json(self) -> dict[str, object]:
        return {"format_version":1,"operation":"count","object":"reductions","query":self.query.to_json(),"relation":self.relation.name,"definition":self.relation.definition,"pipeline_totals":self.pipeline_totals,"fibre_distributions":self.fibre_distributions,"source_edge_transitions":self.source_edge_transitions,"component_transitions":self.component_transitions,"collision_summary":self.collision_summary,"diagnostics":self.diagnostics}


def _dist(sizes: Iterable[int]) -> tuple[dict[str,int],...]:
    c=Counter(sizes); return tuple({"fibre_size":k,"target_objects":v,"source_objects":k*v} for k,v in sorted(c.items()))


def reduction_census(query: CountQuery, relation: str | NetworkRelation = "local-sp", max_records: int = DEFAULT_ENUM_MAX_RECORDS) -> ReductionCensusResult:
    rel=validate_network_relation(relation)
    assignments=enum_assignments(query,max_records=max_records)
    assigned=enum_assigned_supports(query,max_records=max_records)
    networks=enum_networks(query,rel,max_records=max_records)
    as_by_id={a.assigned_support_id:a for a in assigned}
    net_by_as={asid:n for n in networks for asid in n.assigned_support_ids}
    edge_rows=Counter(); edge_nets=defaultdict(set); comp_rows=Counter(); comp_nets=defaultdict(set)
    for asr in assigned:
        n=net_by_as[asr.assigned_support_id]; key=(asr.source_support_edges,n.r,n.l,n.c); edge_rows[key]+=asr.raw_assignment_count; edge_nets[key].add(n.network_id)
        ck=(asr.r,asr.l,asr.c,n.r,n.l,n.c); comp_rows[ck]+=asr.raw_assignment_count; comp_nets[ck].add(n.network_id)
    source_edge_transitions=tuple({"source_support_edges":k[0],"reduced_r":k[1],"reduced_l":k[2],"reduced_c":k[3],"source_assignments":v,"assigned_supports":sum(1 for a in assigned if (a.source_support_edges, net_by_as[a.assigned_support_id].r, net_by_as[a.assigned_support_id].l, net_by_as[a.assigned_support_id].c)==k),"distinct_networks_reached":len(edge_nets[k])} for k,v in sorted(edge_rows.items()))
    component_transitions=tuple({"source_r":k[0],"source_l":k[1],"source_c":k[2],"reduced_r":k[3],"reduced_l":k[4],"reduced_c":k[5],"source_assignments":v,"assigned_supports":sum(1 for a in assigned if (a.r,a.l,a.c,net_by_as[a.assigned_support_id].r,net_by_as[a.assigned_support_id].l,net_by_as[a.assigned_support_id].c)==k),"distinct_networks_reached":len(comp_nets[k])} for k,v in sorted(comp_rows.items()))
    top=sorted(networks,key=lambda n:(-n.source_assignment_count,-n.assigned_support_count,n.network_id))[:5]
    collisions={"multiple_raw_assignments":sum(1 for n in networks if n.source_assignment_count>1),"multiple_assigned_supports":sum(1 for n in networks if n.assigned_support_count>1),"multiple_source_supports":sum(1 for n in networks if len(n.support_ids)>1),"multiple_source_support_edge_counts":sum(1 for n in networks if n.min_source_support_edges != n.max_source_support_edges),"multiple_source_component_tuples":sum(1 for n in networks if len(n.source_component_tuples)>1),"top_collisions":[{"network_id":n.network_id,"source_assignment_count":n.source_assignment_count,"assigned_support_count":n.assigned_support_count} for n in top]}
    pipe={"raw_assignments":len(assignments),"assigned_support_classes":len(assigned),"reduced_networks":len(networks)}
    fibres={"assignments_to_assigned_supports":_dist(a.raw_assignment_count for a in assigned),"assigned_supports_to_networks":_dist(n.assigned_support_count for n in networks),"assignments_to_networks":_dist(n.source_assignment_count for n in networks)}
    diag={"provisional_formats":True,"conservation_checks":{"raw_assignments":sum(a.raw_assignment_count for a in assigned)==len(assignments),"assigned_supports":sum(n.assigned_support_count for n in networks)==len(assigned),"network_ids_unique":len({n.network_id for n in networks})==len(networks)}}
    return ReductionCensusResult(query,rel,pipe,fibres,source_edge_transitions,component_transitions,collisions,diag)
