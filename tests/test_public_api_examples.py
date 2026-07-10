"""Exercise the small runnable examples documented in docs/python_api.md.

These tests are deliberately cheap (tiny budgets/graphs) and exist to catch
drift between the documented API examples and the actual behaviour of
rice.__all__, not to duplicate the golden-count regression suite.
"""

import networkx as nx

from rice import (
    BundleAssignmentCensusResult,
    BundleLabelingCensusResult,
    ReducedFactor,
    ReducedSignature,
    ReducedTopologyCensusResult,
    SIMPLE_PRIMITIVE_BUNDLES,
    SimplePrimitiveBundle,
    SupportCensusResult,
    canonical_reduced_signature,
    factor_from_simple_primitive_bundle,
    normalise_parallel_factor,
    normalise_reduced_factor,
    normalise_series_factor,
    primitive_factor,
    reduced_signature_component_counts,
    reduced_topology_census,
    simple_bundle_assignment_census,
    simple_bundle_labeling_census,
    support_census,
)


def test_support_census_example_matches_documented_output():
    result = support_census(max_edges=3)

    assert isinstance(result, SupportCensusResult)
    assert result.relevant_by_edges == {1: 1, 2: 1, 3: 2}
    assert result.relevant_total == 4


def test_simple_bundle_assignment_census_example_matches_documented_output():
    result = simple_bundle_assignment_census(max_r=1, max_reactive=1)

    assert isinstance(result, BundleAssignmentCensusResult)
    assert result.leaf_assignments_total == 9
    assert result.leaf_assignments_by_edges == {1: 5, 2: 4}


def test_simple_bundle_labeling_census_example_matches_documented_output():
    result = simple_bundle_labeling_census(max_r=1, max_reactive=1)

    assert isinstance(result, BundleLabelingCensusResult)
    assert result.canonical_labeling_orbits_total == 7
    assert result.canonical_labeling_orbits_by_edges == {1: 5, 2: 2}


def test_simple_primitive_bundle_matches_type_of_bundle_entries():
    assert all(isinstance(bundle, SimplePrimitiveBundle) for bundle in SIMPLE_PRIMITIVE_BUNDLES)
    assert [bundle.label for bundle in SIMPLE_PRIMITIVE_BUNDLES] == [
        "R",
        "L",
        "C",
        "R||L",
        "R||C",
        "L||C",
        "R||L||C",
    ]


def test_factor_construction_and_normalisation_example():
    r = primitive_factor("R")
    l = primitive_factor("L")

    series = normalise_series_factor([r, l])
    assert series.stable_string() == "L--R"

    parallel_dup = normalise_parallel_factor([r, r])
    assert parallel_dup.stable_string() == "R"

    bundle_factor = factor_from_simple_primitive_bundle("R||L")
    assert bundle_factor.stable_string() == "L||R"

    messy = ReducedFactor("parallel", (ReducedFactor("parallel", (r, r)), l))
    clean = normalise_reduced_factor(messy)

    assert clean.stable_string() == "L||R"
    assert clean == bundle_factor


def test_normalise_reduced_factor_is_recursive():
    r, l, c = primitive_factor("R"), primitive_factor("L"), primitive_factor("C")

    deeply_nested = ReducedFactor(
        "series",
        (
            ReducedFactor("series", (r, r)),
            ReducedFactor("parallel", (ReducedFactor("parallel", (l, l)), c)),
        ),
    )
    result = normalise_reduced_factor(deeply_nested)

    # Fully flattened/collapsed: R--R -> R and L||L -> L merge at every depth,
    # leaving a two-factor series of R and (L||C).
    assert result.kind == "series"
    assert {operand.stable_string() for operand in result.operands} == {"R", "C||L"}


def test_canonical_reduced_signature_example_is_deterministic():
    graph = nx.Graph([(0, 1), (1, 2)])
    assignments = {(0, 1): "R", (1, 2): "L"}

    signature = canonical_reduced_signature(graph, (0, 2), assignments)
    signature_again = canonical_reduced_signature(graph, (0, 2), assignments)
    reversed_signature = canonical_reduced_signature(graph, (2, 0), assignments)

    assert isinstance(signature, ReducedSignature)
    assert signature.stable_string() == "0-1:L--R"
    assert signature == signature_again
    assert signature == reversed_signature
    assert reduced_signature_component_counts(signature) == (1, 1, 0)


def test_reduced_topology_census_example_matches_documented_output():
    result = reduced_topology_census(max_r=1, max_reactive=1)

    assert isinstance(result, ReducedTopologyCensusResult)
    assert result.exact_table == ((0, 2), (1, 4))
    assert result.total == 7
    assert result.canonical_signatures == (
        "0-1:C",
        "0-1:C--R",
        "0-1:C||R",
        "0-1:L",
        "0-1:L--R",
        "0-1:L||R",
        "0-1:R",
    )
