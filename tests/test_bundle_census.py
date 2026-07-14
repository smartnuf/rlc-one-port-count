import pytest

from rice.core import (
    SIMPLE_PRIMITIVE_BUNDLES,
    _simple_bundle_assignment_census,
    simple_bundle_assignment_count_by_edge_count,
)


EXPECTED_ASSIGNMENTS_PER_SUPPORT = {
    1: 7,
    2: 49,
    3: 335,
    4: 1622,
    5: 4602,
    6: 7192,
    7: 5712,
    8: 1792,
}
EXPECTED_LEAVES = {
    1: 7,
    2: 49,
    3: 670,
    4: 6488,
    5: 46020,
    6: 194184,
    7: 456960,
    8: 462336,
}


def test_simple_primitive_bundle_labels_are_reduced_model_labels():
    labels = [bundle.label for bundle in SIMPLE_PRIMITIVE_BUNDLES]

    assert labels == ["R", "L", "C", "R||L", "R||C", "L||C", "R||L||C"]


def test_same_kind_repeated_primitive_bundles_are_not_allowed():
    labels = {bundle.label for bundle in SIMPLE_PRIMITIVE_BUNDLES}

    assert "R||R" not in labels
    assert "L||L" not in labels
    assert "C||C" not in labels
    assert "R||R||L" not in labels
# line-length: ignore-next-line -- legacy line pending wrap
    assert all(len(label.split("||")) == len(set(label.split("||"))) for label in labels)


def test_assignment_counts_per_support_match_phase_2_reference():
    assert simple_bundle_assignment_count_by_edge_count(
        max_edges=8, max_r=3, max_reactive=5
    ) == EXPECTED_ASSIGNMENTS_PER_SUPPORT


def test__simple_bundle_assignment_census_matches_phase_2_reference():
    result = _simple_bundle_assignment_census(max_r=3, max_reactive=5)

    assert result.max_edges == 8
# line-length: ignore-next-line -- legacy line pending wrap
    assert result.assignments_per_support_by_edges == EXPECTED_ASSIGNMENTS_PER_SUPPORT
    assert result.leaf_assignments_by_edges == EXPECTED_LEAVES
    assert result.relevant_supports_total == 383
    assert result.leaf_assignments_total == 1166714


def test__simple_bundle_assignment_census_allows_truncated_max_edges():
# line-length: ignore-next-line -- legacy line pending wrap
    result = _simple_bundle_assignment_census(max_r=3, max_reactive=5, max_edges=7)

    assert result.max_edges == 7
# line-length: ignore-next-line -- legacy line pending wrap
    assert result.leaf_assignments_total == sum(EXPECTED_LEAVES[i] for i in range(1, 8))


def test__simple_bundle_assignment_census_rejects_max_edges_above_budget():
    with pytest.raises(ValueError, match="cannot exceed"):
        _simple_bundle_assignment_census(max_r=3, max_reactive=5, max_edges=9)


def test__simple_bundle_assignment_census_zero_budget_is_empty():
    result = _simple_bundle_assignment_census(max_r=0, max_reactive=0)

    assert result.max_edges == 0
    assert result.relevant_supports_by_edges == {}
    assert result.assignments_per_support_by_edges == {}
    assert result.leaf_assignments_by_edges == {}
    assert result.relevant_supports_total == 0
    assert result.leaf_assignments_total == 0


# line-length: ignore-next-line -- legacy line pending wrap
def test__simple_bundle_assignment_census_rejects_negative_budgets_and_zero_edges_when_nonempty():
    with pytest.raises(ValueError, match="non-negative"):
        _simple_bundle_assignment_census(max_r=-1, max_reactive=0)
    with pytest.raises(ValueError, match="non-negative"):
        _simple_bundle_assignment_census(max_r=0, max_reactive=-1)
    with pytest.raises(ValueError, match="at least 1"):
        _simple_bundle_assignment_census(max_r=1, max_reactive=0, max_edges=0)
