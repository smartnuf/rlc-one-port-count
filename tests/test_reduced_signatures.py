import networkx as nx
import pytest

from rice.core import (
    canonical_reduced_signature,
    normalise_parallel_factor,
    normalise_series_factor,
    primitive_factor,
)


def path_graph(labels):
    graph = nx.Graph()
    graph.add_edges_from((i, i + 1) for i in range(len(labels)))
    return graph, {tuple(sorted((i, i + 1))): label for i, label in enumerate(labels)}


def sig(graph, terminals, assignments):
    return canonical_reduced_signature(graph, terminals, assignments)


def test_series_order_and_primitive_duplicate_normalisation():
    rl_graph, rl = path_graph(["R", "L"])
    lr_graph, lr = path_graph(["L", "R"])
    rlc_graph, rlc = path_graph(["R", "L", "C"])
    crl_graph, crl = path_graph(["C", "R", "L"])
    lcr_graph, lcr = path_graph(["L", "C", "R"])
    rrl_graph, rrl = path_graph(["R", "R", "L"])

    assert sig(rl_graph, (0, 2), rl) == sig(lr_graph, (0, 2), lr)
    assert sig(rlc_graph, (0, 3), rlc) == sig(crl_graph, (0, 3), crl)
    assert sig(rlc_graph, (0, 3), rlc) == sig(lcr_graph, (0, 3), lcr)
    assert sig(rrl_graph, (0, 3), rrl) == sig(rl_graph, (0, 2), rl)


def test_parallel_primitive_duplicate_normalisation():
    for label in ["R", "L", "C"]:
        primitive = primitive_factor(label)
        assert normalise_parallel_factor([primitive, primitive]) == primitive
        assert normalise_series_factor([primitive, primitive]) == primitive


def test_series_and_parallel_remain_distinct():
    series_graph, series = path_graph(["R", "L"])
    parallel_graph = nx.Graph()
    parallel_graph.add_edge(0, 1)

    assert sig(series_graph, (0, 2), series) != sig(parallel_graph, (0, 1), {(0, 1): "R||L"})


def test_series_arm_inside_parallel_network_is_reduced_locally():
    graph = nx.Graph()
    graph.add_edges_from([(0, 1), (1, 2), (0, 2)])
    assignments = {(0, 1): "R", (1, 2): "L", (0, 2): "C"}
    signature = sig(graph, (0, 2), assignments)
    flat_parallel = sig(nx.Graph([(0, 1)]), (0, 1), {(0, 1): "R||L||C"})

    assert signature != flat_parallel
    assert signature.stable_string() == "0-1:C||(L--R)"


def test_repeated_compound_operands_do_not_merge():
    diamond = nx.Graph()
    diamond.add_edges_from([(0, 1), (1, 3), (0, 2), (2, 3)])
    repeated_series = {(0, 1): "R", (1, 3): "L", (0, 2): "R", (2, 3): "L"}
    single_series_graph, single_series = path_graph(["R", "L"])

    assert sig(diamond, (0, 3), repeated_series) != sig(single_series_graph, (0, 2), single_series)

    series_of_parallel_graph, assignments = path_graph(["R||L", "R||L"])
    single_parallel = nx.Graph([(0, 1)])
    assert sig(series_of_parallel_graph, (0, 2), assignments) != sig(
        single_parallel, (0, 1), {(0, 1): "R||L"}
    )


def test_terminal_reversal_and_internal_renaming_are_canonical():
    graph, assignments = path_graph(["R", "L", "C"])
    assert sig(graph, (0, 3), assignments) == sig(graph, (3, 0), assignments)

    renamed = nx.relabel_nodes(graph, {0: "t", 1: "x", 2: "y", 3: "s"})
    renamed_assignments = {tuple(sorted(("t", "x"))): "R", tuple(sorted(("x", "y"))): "L", tuple(sorted(("y", "s"))): "C"}
    assert sig(graph, (0, 3), assignments) == sig(renamed, ("s", "t"), renamed_assignments)


def bridge_core(label_for_bridge="C"):
    graph = nx.Graph()
    graph.add_edges_from([(0, 2), (2, 1), (0, 3), (3, 1), (2, 3)])
    assignments = {(0, 2): "R", (2, 1): "L", (0, 3): "R", (3, 1): "L", (2, 3): label_for_bridge}
    return graph, {tuple(sorted(edge)): label for edge, label in assignments.items()}


def test_non_series_parallel_core_is_stable_but_different_assignments_do_not_collide():
    graph, assignments = bridge_core("C")
    renamed = nx.relabel_nodes(graph, {0: "a", 1: "b", 2: "x", 3: "y"})
    renamed_assignments = {
        tuple(sorted(("a", "x"))): "R",
        tuple(sorted(("x", "b"))): "L",
        tuple(sorted(("a", "y"))): "R",
        tuple(sorted(("y", "b"))): "L",
        tuple(sorted(("x", "y"))): "C",
    }

    assert sig(graph, (0, 1), assignments) == sig(renamed, ("b", "a"), renamed_assignments)

    graph2, assignments2 = bridge_core("R||C")
    assert sig(graph, (0, 1), assignments) != sig(graph2, (0, 1), assignments2)


def test_repeated_reduction_after_series_suppression_creates_parallel_then_more_series():
    graph = nx.Graph()
    graph.add_edges_from([(0, 1), (1, 2), (0, 2), (2, 3)])
    assignments = {(0, 1): "R", (1, 2): "L", (0, 2): "C", (2, 3): "R"}

    assert sig(graph, (0, 3), assignments).stable_string() == "0-1:R--(C||(L--R))"


def test_mixed_node_label_types_are_supported_by_reduced_signature_validation():
    mixed = nx.Graph()
    mixed.add_edges_from([("s", 0), (0, "t")])
    mixed_assignments = {("s", 0): "R", (0, "t"): "L"}

    integer_graph, integer_assignments = path_graph(["R", "L"])

    assert sig(mixed, ("s", "t"), mixed_assignments) == sig(
        integer_graph, (0, 2), integer_assignments
    )

def test_mixed_node_label_signature_is_invariant_under_renaming_and_terminal_reversal():
    graph = nx.Graph()
    graph.add_edges_from([("s", 0), (0, "t")])
    assignments = {("s", 0): "R", (0, "t"): "L"}

    renamed = nx.relabel_nodes(graph, {"s": "right", "t": "left", 0: ("internal", 1)})
    renamed_assignments = {("right", ("internal", 1)): "R", (("internal", 1), "left"): "L"}

    assert sig(graph, ("s", "t"), assignments) == sig(
        renamed, ("left", "right"), renamed_assignments
    )


def test_terminal_irrelevant_mixed_node_labels_raise_value_error_not_type_error():
    dangling = nx.Graph()
    dangling.add_edges_from([("s", 0), (0, "t"), (0, "dangling")])
    assignments = {("s", 0): "R", (0, "t"): "L", (0, "dangling"): "C"}

    with pytest.raises(ValueError, match="terminal-relevant"):
        sig(dangling, ("s", "t"), assignments)


def test_malformed_and_terminal_irrelevant_inputs_are_rejected():
    graph, assignments = path_graph(["R"])
    with pytest.raises(ValueError, match="distinct"):
        sig(graph, (0, 0), assignments)
    with pytest.raises(ValueError, match="missing assignments"):
        sig(graph, (0, 1), {})

    disconnected = nx.Graph([(0, 1), (2, 3)])
    with pytest.raises(ValueError, match="connected"):
        sig(disconnected, (0, 1), {(0, 1): "R", (2, 3): "L"})

    loop = nx.Graph()
    loop.add_nodes_from([0, 1])
    loop.add_edge(0, 0)
    with pytest.raises(ValueError, match="self-loops"):
        sig(loop, (0, 1), {(0, 0): "R"})

    dangling = nx.Graph([(0, 1), (1, 2), (1, 3)])
    with pytest.raises(ValueError, match="terminal-relevant"):
        sig(dangling, (0, 2), {(0, 1): "R", (1, 2): "L", (1, 3): "C"})
