"""Enumerate small two-terminal RLC one-port support graphs and legacy counts.

The reduced-model work starts with a support-only census: connected unlabelled
simple support graphs, unordered terminal-pair orbits, and terminal-relevant
two-terminal supports. Phase 2 adds a raw simple-bundle assignment census over
those supports; series spans and reduced signatures are intentionally outside
that census. Phase 3 quotients those assigned supports by support
automorphisms preserving the unordered terminal pair. The module also exposes
focused per-network local reduction and canonical reduced-signature helpers;
full standard-slice signature enumeration and merging is intentionally not yet
implemented.

The older :func:`count_networks` entry point remains as a legacy
multiset-bundle counter.  It assigns non-empty component-count bundles to
terminal-relevant support edges and uses Burnside's lemma only for that legacy
bundle-orbit calculation.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from itertools import combinations, permutations
from typing import DefaultDict, Iterable, Literal

import networkx as nx
from networkx.algorithms import isomorphism as iso

Mode = Literal["lc", "generic"]


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
    """A reduced-model primitive bundle label and its component-budget weight."""

    label: str
    r_count: int
    reactive_count: int


SIMPLE_PRIMITIVE_BUNDLES: tuple[SimplePrimitiveBundle, ...] = (
    SimplePrimitiveBundle("R", 1, 0),
    SimplePrimitiveBundle("L", 0, 1),
    SimplePrimitiveBundle("C", 0, 1),
    SimplePrimitiveBundle("R||L", 1, 1),
    SimplePrimitiveBundle("R||C", 1, 1),
    SimplePrimitiveBundle("L||C", 0, 2),
    SimplePrimitiveBundle("R||L||C", 1, 2),
)


@dataclass(frozen=True)
class BundleAssignmentCensusResult:
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
class BundleLabelingCensusResult:
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
    """Immutable recursive factor used by reduced-topology signatures."""

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


def normalise_series_factor(factors: Iterable[ReducedFactor]) -> ReducedFactor:
    """Return an unordered, flattened series factor with primitive duplicates merged."""

    return _normalise_composition("series", factors)


def normalise_parallel_factor(factors: Iterable[ReducedFactor]) -> ReducedFactor:
    """Return an unordered, flattened parallel factor with primitive duplicates merged."""

    return _normalise_composition("parallel", factors)


def factor_from_simple_primitive_bundle(bundle: str | SimplePrimitiveBundle | ReducedFactor) -> ReducedFactor:
    """Convert one generated simple primitive bundle label to its initial factor."""

    if isinstance(bundle, ReducedFactor):
        return bundle
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
    assignment_edges = {_edge_key(edge) for edge in edge_assignments}
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
class CountResult:
    """Legacy component-bundle result returned by :func:`count_networks`.

    Attributes:
        max_r: Maximum total number of resistors.
        max_reactive: Maximum total number of reactive elements.
        mode: ``"lc"`` distinguishes inductors and capacitors. ``"generic"``
            treats all reactive elements as one type ``X``.
        table: A rectangular table indexed by ``table[r][x]``, where ``x`` is
            total reactive count.  For ``mode="lc"`` the count sums over all
            L/C splittings with ``l + c == x``.
        support_count: Number of terminal-relevant two-terminal support graphs
            used by the legacy bundle counter.
        support_count_by_edges: Terminal-relevant support counts by number of
            support edges.
    """

    max_r: int
    max_reactive: int
    mode: Mode
    table: tuple[tuple[int, ...], ...]
    support_count: int
    support_count_by_edges: dict[int, int]

    @property
    def total(self) -> int:
        return sum(sum(row) for row in self.table)

    def row_total(self, r: int) -> int:
        return sum(self.table[r])

    def exactly_r_total(self, r: int) -> int:
        return self.row_total(r)

    def as_markdown_table(self) -> str:
        headers = ["R \\ X"] + [str(x) for x in range(self.max_reactive + 1)] + ["Row total"]
        lines = ["| " + " | ".join(headers) + " |"]
        lines.append("|" + "---:|" * len(headers))
        for r, row in enumerate(self.table):
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


def fixed_assignments_by_total(
    cycle_lengths: tuple[int, ...],
    max_r: int,
    max_reactive: int,
    mode: Mode,
) -> dict[tuple[int, int], int]:
    """Count legacy bundle assignments fixed by an edge permutation.

    This helper is part of the legacy component-count bundle counter, not the
    phase-1 support census.  For a fixed edge permutation, every edge in a cycle
    must receive the same non-empty count bundle.
    """

    if mode == "generic":
        dp: dict[tuple[int, int], int] = {(0, 0): 1}
        for cycle_length in cycle_lengths:
            next_dp: DefaultDict[tuple[int, int], int] = defaultdict(int)
            options = [
                (r, x)
                for r in range(max_r // cycle_length + 1)
                for x in range(max_reactive // cycle_length + 1)
                if r + x > 0
            ]
            for (old_r, old_x), count in dp.items():
                for r, x in options:
                    new_r = old_r + cycle_length * r
                    new_x = old_x + cycle_length * x
                    if new_r <= max_r and new_x <= max_reactive:
                        next_dp[(new_r, new_x)] += count
            dp = dict(next_dp)
        return dp

    if mode != "lc":
        raise ValueError(f"unknown mode {mode!r}; expected 'lc' or 'generic'")

    dp_lc: dict[tuple[int, int, int], int] = {(0, 0, 0): 1}
    for cycle_length in cycle_lengths:
        next_dp_lc: DefaultDict[tuple[int, int, int], int] = defaultdict(int)
        options_lc = [
            (r, l, c)
            for r in range(max_r // cycle_length + 1)
            for l in range(max_reactive // cycle_length + 1)
            for c in range(max_reactive // cycle_length + 1)
            if r + l + c > 0 and cycle_length * (l + c) <= max_reactive
        ]
        for (old_r, old_l, old_c), count in dp_lc.items():
            for r, l, c in options_lc:
                new_r = old_r + cycle_length * r
                new_l = old_l + cycle_length * l
                new_c = old_c + cycle_length * c
                if new_r <= max_r and new_l + new_c <= max_reactive:
                    next_dp_lc[(new_r, new_l, new_c)] += count
        dp_lc = dict(next_dp_lc)

    aggregated: DefaultDict[tuple[int, int], int] = defaultdict(int)
    for (r, l, c), count in dp_lc.items():
        aggregated[(r, l + c)] += count
    return dict(aggregated)


def iter_two_terminal_supports(max_edges: int):
    """Yield terminal-relevant support representatives for legacy counting."""

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


def simple_bundle_assignment_census(
    max_r: int = 3, max_reactive: int = 5, max_edges: int | None = None
) -> BundleAssignmentCensusResult:
    """Run the phase-2 raw simple primitive bundle-assignment census."""

    if max_r < 0 or max_reactive < 0:
        raise ValueError("component limits must be non-negative")
    natural_max_edges = max_r + max_reactive
    resolved_max_edges = natural_max_edges if max_edges is None else max_edges
    if resolved_max_edges < 1:
        raise ValueError("max_edges must be at least 1")
    if resolved_max_edges > natural_max_edges:
        raise ValueError("max_edges cannot exceed max_r + max_reactive")

    supports = support_census(max_edges=resolved_max_edges).relevant_by_edges
    assignments = simple_bundle_assignment_count_by_edge_count(
        resolved_max_edges, max_r=max_r, max_reactive=max_reactive
    )
    leaves = {
        edge_count: supports[edge_count] * assignments[edge_count]
        for edge_count in range(1, resolved_max_edges + 1)
    }

    return BundleAssignmentCensusResult(
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


def simple_bundle_labeling_orbit_count(
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


def simple_bundle_labeling_census(
    max_r: int = 3, max_reactive: int = 5, max_edges: int | None = None
) -> BundleLabelingCensusResult:
    """Run the phase-3 canonical simple-bundle labeling-orbit census."""

    if max_r < 0 or max_reactive < 0:
        raise ValueError("component limits must be non-negative")
    natural_max_edges = max_r + max_reactive
    resolved_max_edges = natural_max_edges if max_edges is None else max_edges
    if resolved_max_edges < 1:
        raise ValueError("max_edges must be at least 1")
    if resolved_max_edges > natural_max_edges:
        raise ValueError("max_edges cannot exceed max_r + max_reactive")

    raw = simple_bundle_assignment_census(
        max_r=max_r, max_reactive=max_reactive, max_edges=resolved_max_edges
    )
    canonical_by_edges: Counter[int] = Counter()

    for graph, terminals, autos in iter_two_terminal_supports(resolved_max_edges):
        canonical_by_edges[graph.number_of_edges()] += simple_bundle_labeling_orbit_count(
            graph,
            terminals,
            max_r=max_r,
            max_reactive=max_reactive,
            graph_automorphisms=autos,
        )

    return BundleLabelingCensusResult(
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


def count_networks(max_r: int = 3, max_reactive: int = 5, mode: Mode = "lc") -> CountResult:
    """Run the legacy multiset-bundle two-terminal network count."""

    if max_r < 0 or max_reactive < 0:
        raise ValueError("component limits must be non-negative")
    if mode not in {"lc", "generic"}:
        raise ValueError("mode must be 'lc' or 'generic'")

    max_edges = max_r + max_reactive
    counts: DefaultDict[tuple[int, int], int] = defaultdict(int)
    support_count = 0
    support_count_by_edges: Counter[int] = Counter()
    fixed_count_cache: dict[tuple[tuple[int, ...], int, int, Mode], dict[tuple[int, int], int]] = {}

    for graph, terminals, autos in iter_two_terminal_supports(max_edges):
        support_count += 1
        support_count_by_edges[graph.number_of_edges()] += 1
        edge_permutations = edge_permutations_preserving_terminal_set(graph, terminals, autos)
        group_size = len(edge_permutations)
        burnside_sum: DefaultDict[tuple[int, int], int] = defaultdict(int)

        for permutation in edge_permutations:
            cycle_lengths = permutation_cycle_lengths(permutation)
            cache_key = (cycle_lengths, max_r, max_reactive, mode)
            fixed_counts = fixed_count_cache.get(cache_key)
            if fixed_counts is None:
                fixed_counts = fixed_assignments_by_total(cycle_lengths, max_r, max_reactive, mode)
                fixed_count_cache[cache_key] = fixed_counts
            for total_key, count in fixed_counts.items():
                burnside_sum[total_key] += count

        for total_key, count in burnside_sum.items():
            if count % group_size != 0:
                raise ArithmeticError(
                    f"Burnside sum {count} is not divisible by group size {group_size} for {total_key}"
                )
            counts[total_key] += count // group_size

    table = tuple(
        tuple(counts.get((r, x), 0) for x in range(max_reactive + 1)) for r in range(max_r + 1)
    )

    return CountResult(
        max_r=max_r,
        max_reactive=max_reactive,
        mode=mode,
        table=table,
        support_count=support_count,
        support_count_by_edges=dict(sorted(support_count_by_edges.items())),
    )
