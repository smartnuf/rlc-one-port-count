import networkx as nx
import pytest

from rice.core import (
    ReducedFactor,
    canonical_reduced_signature,
    factor_from_simple_primitive_bundle,
    normalise_parallel_factor,
    normalise_reduced_factor,
    normalise_series_factor,
    primitive_factor,
)


def path_graph(labels):
    graph = nx.Graph()
    graph.add_edges_from((i, i + 1) for i in range(len(labels)))
# line-length: ignore-next-line -- legacy line pending wrap
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

# line-length: ignore-next-line -- legacy line pending wrap
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

# line-length: ignore-next-line -- legacy line pending wrap
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
# line-length: ignore-next-line -- legacy line pending wrap
    renamed_assignments = {tuple(sorted(("t", "x"))): "R", tuple(sorted(("x", "y"))): "L", tuple(sorted(("y", "s"))): "C"}
# line-length: ignore-next-line -- legacy line pending wrap
    assert sig(graph, (0, 3), assignments) == sig(renamed, ("s", "t"), renamed_assignments)


def bridge_core(label_for_bridge="C"):
    graph = nx.Graph()
    graph.add_edges_from([(0, 2), (2, 1), (0, 3), (3, 1), (2, 3)])
# line-length: ignore-next-line -- legacy line pending wrap
    assignments = {(0, 2): "R", (2, 1): "L", (0, 3): "R", (3, 1): "L", (2, 3): label_for_bridge}
# line-length: ignore-next-line -- legacy line pending wrap
    return graph, {tuple(sorted(edge)): label for edge, label in assignments.items()}


# line-length: ignore-next-line -- legacy line pending wrap
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

# line-length: ignore-next-line -- legacy line pending wrap
    assert sig(graph, (0, 1), assignments) == sig(renamed, ("b", "a"), renamed_assignments)

    graph2, assignments2 = bridge_core("R||C")
    assert sig(graph, (0, 1), assignments) != sig(graph2, (0, 1), assignments2)


# line-length: ignore-next-line -- legacy line pending wrap
def test_repeated_reduction_after_series_suppression_creates_parallel_then_more_series():
    graph = nx.Graph()
    graph.add_edges_from([(0, 1), (1, 2), (0, 2), (2, 3)])
    assignments = {(0, 1): "R", (1, 2): "L", (0, 2): "C", (2, 3): "R"}

# line-length: ignore-next-line -- legacy line pending wrap
    assert sig(graph, (0, 3), assignments).stable_string() == "0-1:R--(C||(L--R))"


# line-length: ignore-next-line -- legacy line pending wrap
def test_mixed_node_label_types_are_supported_by_reduced_signature_validation():
    mixed = nx.Graph()
    mixed.add_edges_from([("s", 0), (0, "t")])
    mixed_assignments = {("s", 0): "R", (0, "t"): "L"}

    integer_graph, integer_assignments = path_graph(["R", "L"])

    assert sig(mixed, ("s", "t"), mixed_assignments) == sig(
        integer_graph, (0, 2), integer_assignments
    )


def test_duplicate_opposite_assignment_orientations_are_rejected():
    graph = nx.Graph([(0, 1)])

    with pytest.raises(ValueError, match="duplicate or ambiguous.*0.*1"):
        sig(graph, (0, 1), {(0, 1): "R", (1, 0): "L"})


# line-length: ignore-next-line -- legacy line pending wrap
def test_duplicate_opposite_assignment_orientations_are_rejected_even_with_same_value():
    graph = nx.Graph([(0, 1)])

    with pytest.raises(ValueError, match="duplicate or ambiguous.*0.*1"):
        sig(graph, (0, 1), {(0, 1): "R", (1, 0): "R"})


def test_single_reversed_orientation_assignment_is_accepted():
    graph = nx.Graph([(0, 1)])

    assert sig(graph, (0, 1), {(1, 0): "R"}).stable_string() == "0-1:R"


def test_duplicate_assignment_detection_supports_mixed_type_node_labels():
    graph = nx.Graph()
    graph.add_edge("s", 0)

    with pytest.raises(ValueError, match="duplicate or ambiguous"):
        sig(graph, ("s", 0), {("s", 0): "R", (0, "s"): "L"})


def test_duplicate_assignment_rejection_is_insertion_order_independent():
    graph = nx.Graph([(0, 1)])

    first = {(0, 1): "R", (1, 0): "L"}
    second = {(1, 0): "L", (0, 1): "R"}

    with pytest.raises(ValueError, match="duplicate or ambiguous"):
        sig(graph, (0, 1), first)
    with pytest.raises(ValueError, match="duplicate or ambiguous"):
        sig(graph, (0, 1), second)

# line-length: ignore-next-line -- legacy line pending wrap
def test_mixed_node_label_signature_is_invariant_under_renaming_and_terminal_reversal():
    graph = nx.Graph()
    graph.add_edges_from([("s", 0), (0, "t")])
    assignments = {("s", 0): "R", (0, "t"): "L"}

# line-length: ignore-next-line -- legacy line pending wrap
    renamed = nx.relabel_nodes(graph, {"s": "right", "t": "left", 0: ("internal", 1)})
# line-length: ignore-next-line -- legacy line pending wrap
    renamed_assignments = {("right", ("internal", 1)): "R", (("internal", 1), "left"): "L"}

    assert sig(graph, ("s", "t"), assignments) == sig(
        renamed, ("left", "right"), renamed_assignments
    )


# line-length: ignore-next-line -- legacy line pending wrap
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


# line-length: ignore-next-line -- legacy line pending wrap
def test_supplied_reduced_factor_parallel_duplicate_primitive_normalises_to_primitive():
    r = primitive_factor("R")

# line-length: ignore-next-line -- legacy line pending wrap
    assert factor_from_simple_primitive_bundle(ReducedFactor("parallel", (r, r))) == r


def test_supplied_reduced_factor_reorders_primitive_and_compound_operands():
    r = primitive_factor("R")
    l = primitive_factor("L")
    c = primitive_factor("C")
    rl = ReducedFactor("series", (r, l))

# line-length: ignore-next-line -- legacy line pending wrap
    assert normalise_reduced_factor(ReducedFactor("parallel", (c, rl, r))) == normalise_reduced_factor(
        ReducedFactor("parallel", (rl, r, c))
    )


def test_supplied_reduced_factor_flattens_nested_series_and_parallel():
    r = primitive_factor("R")
    l = primitive_factor("L")
    c = primitive_factor("C")

# line-length: ignore-next-line -- legacy line pending wrap
    nested_series = ReducedFactor("series", (r, ReducedFactor("series", (l, c))))
    flat_series = ReducedFactor("series", (c, r, l))
# line-length: ignore-next-line -- legacy line pending wrap
    nested_parallel = ReducedFactor("parallel", (r, ReducedFactor("parallel", (l, c))))
    flat_parallel = ReducedFactor("parallel", (c, r, l))

# line-length: ignore-next-line -- legacy line pending wrap
    assert normalise_reduced_factor(nested_series) == normalise_reduced_factor(flat_series)
# line-length: ignore-next-line -- legacy line pending wrap
    assert normalise_reduced_factor(nested_parallel) == normalise_reduced_factor(flat_parallel)


def test_supplied_reduced_factor_repeated_equal_compounds_remain_repeated():
    r = primitive_factor("R")
    l = primitive_factor("L")
    arm = ReducedFactor("series", (r, l))
# line-length: ignore-next-line -- legacy line pending wrap
    normalised = normalise_reduced_factor(ReducedFactor("parallel", (arm, arm)))

    assert normalised.kind == "parallel"
# line-length: ignore-next-line -- legacy line pending wrap
    assert normalised.operands == (normalise_reduced_factor(arm), normalise_reduced_factor(arm))


@pytest.mark.parametrize(
    ("factor", "message"),
    [
        (ReducedFactor("bogus", ()), "unknown reduced factor kind"),
        (ReducedFactor("primitive", "X"), "malformed primitive"),
# line-length: ignore-next-line -- legacy line pending wrap
        (ReducedFactor("primitive", (primitive_factor("R"),)), "malformed primitive"),
        (ReducedFactor("series", ()), "requires at least one"),
        (ReducedFactor("parallel", []), "must be a tuple"),
        (ReducedFactor("series", ("R",)), "operands must be ReducedFactor"),
    ],
)
# line-length: ignore-next-line -- legacy line pending wrap
def test_supplied_reduced_factor_malformed_values_raise_clear_errors(factor, message):
    with pytest.raises(ValueError, match=message):
        normalise_reduced_factor(factor)


def test_canonical_reduced_signature_normalises_supplied_reduced_factors():
    r = primitive_factor("R")
    l = primitive_factor("L")
    c = primitive_factor("C")
    graph = nx.Graph([(0, 1), (1, 2)])
    messy = ReducedFactor("parallel", (ReducedFactor("parallel", (r, r)), c))
    clean = ReducedFactor("parallel", (c, r))

    assert sig(graph, (0, 2), {(0, 1): messy, (1, 2): l}) == sig(
        graph, (0, 2), {(0, 1): clean, (1, 2): l}
    )
