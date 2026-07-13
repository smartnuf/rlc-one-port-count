"""Exercise runnable examples from docs/python_api.md."""

import inspect

import pytest

import rice
from rice import (
    COUNT_PROFILES,
    LOCAL_SP_RELATION,
    ComponentConstraints,
    CountQuery,
    assignment_census,
    enum_assigned_supports,
    enum_assignments,
    enum_networks,
    network_census,
    validate_network_relation,
)


def test_minimal_count_example_from_docs():
    result = network_census(CountQuery(profile="golden"))

    assert result.total == 313
    assert result.records[0] == {"r": 0, "lc": 1, "networks": 2}
    assert result.matrix() == ((0, 2, 2, 4), (1, 4, 12, 40), (0, 4, 34, 210))


def test_minimal_enumeration_example_from_docs():
    query = CountQuery(component_constraints=ComponentConstraints(max_r=1, max_lc=1))
    records = enum_networks(query, max_records=100)

    assert len(records) == 7
    assert records[0].network_id.startswith("network-")
    assert records[0].canonical_signature == "0-1:C"


def test_support_record_exposes_defensive_graph_copy_and_read_only_automorphisms():
    from rice import enum_supports

    record = enum_supports(CountQuery(max_support_edges=1))[0]
    graph_copy = record.graph
    graph_copy.add_edge(100, 101)

    assert record.graph.number_of_edges() == record.source_support_edges
    with pytest.raises(TypeError):
        record.automorphisms[0][0] = 99


def test_profiles_and_defaults_examples_from_docs():
    assert sorted(COUNT_PROFILES) == [
        "golden",
        "ladenheim-108-region",
        "ladenheim-structural-region",
        "main",
    ]
    assert CountQuery(profile="main").effective_support_edge_range().to_json() == {
        "min": 1,
        "max": 8,
    }
    with pytest.raises(ValueError, match="finite maximum"):
        network_census(CountQuery())


def test_query_construction_and_exact_support_edge_examples_from_docs():
    query = CountQuery(
        component_constraints=ComponentConstraints(max_r=2, max_lc=3),
        min_support_edges=2,
        max_support_edges=4,
    )
    assert query.requested_support_edge_range().to_json() == {"min": 2, "max": 4}
    assert query.effective_support_edge_range().to_json() == {"min": 2, "max": 4}

    exact = CountQuery(
        component_constraints=ComponentConstraints(max_r=1, max_lc=1),
        support_edges=2,
    )
    assert assignment_census(exact).raw_assignments_total == 4


def test_grouping_relation_json_and_guard_examples_from_docs():
    grouped = assignment_census(CountQuery(profile="golden"), group_by=("r", "lc"))
    assert grouped.records[:3] == (
        {"r": 0, "lc": 1, "distinct_bundle_sets": 2, "raw_assignments": 2},
        {"r": 0, "lc": 2, "distinct_bundle_sets": 4, "raw_assignments": 5},
        {"r": 0, "lc": 3, "distinct_bundle_sets": 6, "raw_assignments": 20},
    )

    total = network_census(CountQuery(profile="golden"), group_by=("none",))
    assert total.records == ({"networks": 313},)
    assert total.to_json()["object"] == "networks"
    assert total.to_json()["totals"] == {"networks": 313}

    relation = validate_network_relation("local-sp")
    assert relation == LOCAL_SP_RELATION
    assert relation.definition == "canonical-reduced-topology-local-series-parallel-v1"

    tiny = CountQuery(component_constraints=ComponentConstraints(max_r=1, max_lc=1))
    assert len(enum_assignments(tiny, max_records=20)) == 9

    record = enum_assigned_supports(tiny, max_records=20)[0]
    assert (record.source_support_edges, record.r, record.l, record.c) == (1, 0, 0, 1)
    assert (record.orbit_size, record.raw_assignment_count) == (1, 1)

    with pytest.raises(ValueError, match="grouping"):
        network_census(CountQuery(profile="golden"), group_by=("support-edges",))
    with pytest.raises(ValueError, match="max-records"):
        enum_assignments(CountQuery(profile="golden"), max_records=1)


def test_public_callables_and_classes_have_authored_documentation():
    for name in rice.__all__:
        obj = getattr(rice, name)
        if inspect.isfunction(obj) or inspect.isclass(obj):
            doc = inspect.getdoc(obj)
            assert doc, name
            assert not doc.startswith(f"{name}(")
            assert len(doc.split()) >= 8, name
