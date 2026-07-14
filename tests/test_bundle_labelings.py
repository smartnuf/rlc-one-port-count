from itertools import product

import networkx as nx
import pytest

from rice.core import (
    SIMPLE_PRIMITIVE_BUNDLES,
    automorphisms,
    edge_permutations_preserving_terminal_set,
    _simple_bundle_labeling_census,
    _simple_bundle_labeling_orbit_count,
)


def _path(n):
    g = nx.Graph()
    g.add_edges_from((i, i + 1) for i in range(n - 1))
    return g


def _brute_orbit_count(graph, terminals, max_r, max_reactive):
    edges = sorted(tuple(sorted(e)) for e in graph.edges())
# line-length: ignore-next-line -- legacy line pending wrap
    perms = edge_permutations_preserving_terminal_set(graph, terminals, automorphisms(graph))
    valid = []
# line-length: ignore-next-line -- legacy line pending wrap
    for assignment in product(range(len(SIMPLE_PRIMITIVE_BUNDLES)), repeat=len(edges)):
        r = sum(SIMPLE_PRIMITIVE_BUNDLES[i].r_count for i in assignment)
        x = sum(SIMPLE_PRIMITIVE_BUNDLES[i].reactive_count for i in assignment)
        if r <= max_r and x <= max_reactive:
            valid.append(assignment)

    seen = set()
    for assignment in valid:
# line-length: ignore-next-line -- legacy line pending wrap
        orbit = {tuple(assignment[p[i]] for i in range(len(edges))) for p in perms}
        seen.add(min(orbit))
    return len(seen)


def test_single_edge_support_every_assignment_is_canonical():
    g = _path(2)

    assert (
        _simple_bundle_labeling_orbit_count(g, (0, 1), max_r=3, max_reactive=5)
        == 7
    )


def test_two_edge_terminal_path_identifies_reversal_pairs():
    g = _path(3)

    assert (
        _simple_bundle_labeling_orbit_count(g, (0, 2), max_r=3, max_reactive=5)
        == 28
    )


# line-length: ignore-next-line -- legacy line pending wrap
def test_asymmetric_terminal_labeling_does_not_merge_without_actual_automorphism():
    g = nx.Graph()
    g.add_edges_from([(0, 1), (1, 2), (0, 3)])

    assert (
        _simple_bundle_labeling_orbit_count(g, (0, 2), max_r=3, max_reactive=5)
        == 335
    )


def test_support_symmetry_not_preserving_terminal_set_is_excluded():
    g = nx.star_graph(3)

    # The star has leaf symmetries, but with terminals at center and one leaf
# line-length: ignore-next-line -- legacy line pending wrap
    # the two other terminal-irrelevant leaf edges may swap only with each other.
    assert _simple_bundle_labeling_orbit_count(
        g, (0, 1), max_r=3, max_reactive=5
    ) == _brute_orbit_count(g, (0, 1), 3, 5)
# line-length: ignore-next-line -- legacy line pending wrap
    assert _simple_bundle_labeling_orbit_count(g, (0, 1), max_r=3, max_reactive=5) < 7**3


def test_terminal_swapping_automorphism_is_included():
    g = _path(3)
# line-length: ignore-next-line -- legacy line pending wrap
    perms = edge_permutations_preserving_terminal_set(g, (0, 2), automorphisms(g))

    assert (1, 0) in perms


def test_budget_accounting_multiplies_bundle_weight_by_edge_cycle_length():
    g = _path(3)

# line-length: ignore-next-line -- legacy line pending wrap
    # On the 2-edge terminal path, terminal reversal fixes only assignments with
    # the same bundle on both edges. Under R<=1, L+C<=2 that permits L, C, and
    # L||C as fixed assignments, but not R||L or R||L||C because R would be
    # consumed once per edge in the 2-cycle.
# line-length: ignore-next-line -- legacy line pending wrap
    assert _simple_bundle_labeling_orbit_count(g, (0, 2), max_r=1, max_reactive=2) == 10


def test_orbit_counts_match_brute_force_on_small_supports_and_budgets():
    supports = [
        (_path(2), (0, 1)),
        (_path(3), (0, 2)),
        (nx.cycle_graph(3), (0, 1)),
    ]
    for graph, terminals in supports:
        for max_r, max_reactive in [(1, 1), (2, 2), (3, 2)]:
            assert _simple_bundle_labeling_orbit_count(
                graph, terminals, max_r, max_reactive
            ) == _brute_orbit_count(graph, terminals, max_r, max_reactive)


def test_phase_2_raw_and_phase_3_canonical_standard_totals():
    result = _simple_bundle_labeling_census(max_r=3, max_reactive=5)

    assert result.raw_leaf_assignments_total == 1166714
    assert result.canonical_labeling_orbits_by_edges == {
        1: 7,
        2: 28,
        3: 380,
        4: 3770,
        5: 28004,
        6: 127627,
        7: 323330,
        8: 346948,
    }
    assert result.canonical_labeling_orbits_total == 830094


def test__simple_bundle_labeling_census_zero_budget_is_empty():
    result = _simple_bundle_labeling_census(max_r=0, max_reactive=0)

    assert result.max_edges == 0
    assert result.relevant_supports_by_edges == {}
    assert result.raw_leaf_assignments_by_edges == {}
    assert result.canonical_labeling_orbits_by_edges == {}
    assert result.relevant_supports_total == 0
    assert result.raw_leaf_assignments_total == 0
    assert result.canonical_labeling_orbits_total == 0


# line-length: ignore-next-line -- legacy line pending wrap
def test__simple_bundle_labeling_census_rejects_negative_budgets_and_zero_edges_when_nonempty():
    with pytest.raises(ValueError, match="non-negative"):
        _simple_bundle_labeling_census(max_r=-1, max_reactive=0)
    with pytest.raises(ValueError, match="non-negative"):
        _simple_bundle_labeling_census(max_r=0, max_reactive=-1)
    with pytest.raises(ValueError, match="at least 1"):
        _simple_bundle_labeling_census(max_r=1, max_reactive=0, max_edges=0)
