import networkx as nx

from rice.core import (
    automorphisms,
    is_two_terminal_relevant,
    support_census,
    terminal_pair_orbit_representatives,
)


EXPECTED_BASIC = {1: 1, 2: 1, 3: 3, 4: 5, 5: 12, 6: 30, 7: 79, 8: 227}
EXPECTED_TERMINAL_LABELINGS = {1: 1, 2: 2, 3: 7, 4: 21, 5: 73, 6: 255, 7: 946, 8: 3618}
EXPECTED_RELEVANT = {1: 1, 2: 1, 3: 2, 4: 4, 5: 10, 6: 27, 7: 80, 8: 258}


def test_support_census_matches_phase_1_reference_counts():
    result = support_census(max_edges=8)

    assert result.basic_by_edges == EXPECTED_BASIC
    assert result.terminal_labelings_by_edges == EXPECTED_TERMINAL_LABELINGS
    assert result.relevant_by_edges == EXPECTED_RELEVANT
    assert result.basic_total == 358
    assert result.terminal_labelings_total == 4923
    assert result.relevant_total == 383


def test_terminal_reversal_is_one_two_terminal_labeling():
    graph = nx.path_graph(2)

    assert terminal_pair_orbit_representatives(graph, automorphisms(graph)) == [(0, 1)]


def test_dangling_branch_rejects_whole_terminal_labelled_graph():
    graph = nx.Graph()
    graph.add_edges_from([("s", "a"), ("a", "t"), ("a", "x")])

    assert not is_two_terminal_relevant(graph, "s", "t")


def test_pendant_blob_rejects_whole_terminal_labelled_graph():
    graph = nx.Graph()
    graph.add_edges_from([
        ("s", "a"),
        ("a", "t"),
        ("a", "b"),
        ("b", "c"),
        ("c", "a"),
    ])

    assert not is_two_terminal_relevant(graph, "s", "t")


def test_series_chain_is_terminal_relevant():
    graph = nx.path_graph(4)

    assert is_two_terminal_relevant(graph, 0, 3)


def test_parallel_cyclic_alternatives_are_terminal_relevant():
    graph = nx.cycle_graph(4)

    assert is_two_terminal_relevant(graph, 0, 2)
