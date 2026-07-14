import json
import subprocess
import sys

import pytest

from rice import (
    BundleSet,
    ComponentConstraints,
    CountQuery,
    SIMPLE_PRIMITIVE_BUNDLES,
    bundle_set_census,
    assignment_census,
    iter_bundle_sets,
    network_census,
)
from rice.cli import main
from rice.core import simple_bundle_assignment_count_by_edge_count


def cli_json(argv, capsys):
    assert main(argv + ["--format", "json"]) == 0
    return json.loads(capsys.readouterr().out)


def assert_error(capsys, argv, text):
    with pytest.raises(SystemExit) as exc:
        main(argv)
    assert exc.value.code == 2
    err = capsys.readouterr().err
    assert text in err
    assert "Traceback" not in err


def test_bundle_type_weights_api_and_cli(capsys):
# line-length: ignore-next-line -- legacy line pending wrap
    assert [(b.label, b.r_count, b.l_count, b.c_count, b.reactive_count) for b in SIMPLE_PRIMITIVE_BUNDLES] == [
        ("R", 1, 0, 0, 0),
        ("L", 0, 1, 0, 1),
        ("C", 0, 0, 1, 1),
        ("R||L", 1, 1, 0, 1),
        ("R||C", 1, 0, 1, 1),
        ("L||C", 0, 1, 1, 2),
        ("R||L||C", 1, 1, 1, 2),
    ]
    out = cli_json(["count", "bundle-types"], capsys)
    assert out["object"] == "bundle-types"
    assert out["totals"] == {"bundle_types": 7}
# line-length: ignore-next-line -- legacy line pending wrap
    assert [row["label"] for row in out["records"]] == [b.label for b in SIMPLE_PRIMITIVE_BUNDLES]


def test_bundle_types_rejects_inapplicable_options(capsys):
# line-length: ignore-next-line -- legacy line pending wrap
    assert_error(capsys, ["count", "bundle-types", "--max-r", "3"], "unrecognized arguments")


def test_bundle_set_main_and_golden_counts(capsys):
# line-length: ignore-next-line -- legacy line pending wrap
    main_result = cli_json(["count", "bundle-sets", "--max-r", "3", "--max-lc", "5"], capsys)
# line-length: ignore-next-line -- legacy line pending wrap
    assert [r["support-edges"] for r in main_result["records"]] == list(range(1, 9))
# line-length: ignore-next-line -- legacy line pending wrap
    assert [r["distinct_bundle_sets"] for r in main_result["records"]] == [7, 28, 80, 127, 120, 64, 25, 6]
# line-length: ignore-next-line -- legacy line pending wrap
    assert [r["raw_placements"] for r in main_result["records"]] == [7, 49, 335, 1622, 4602, 7192, 5712, 1792]
# line-length: ignore-next-line -- legacy line pending wrap
    assert [r["raw_placements"] for r in main_result["records"]] == list(simple_bundle_assignment_count_by_edge_count(8, 3, 5).values())

    golden = cli_json(["count", "bundle-sets", "--profile", "golden"], capsys)
    assert [r["support-edges"] for r in golden["records"]] == list(range(1, 6))
# line-length: ignore-next-line -- legacy line pending wrap
    assert [r["distinct_bundle_sets"] for r in golden["records"]] == [7, 25, 32, 15, 4]
# line-length: ignore-next-line -- legacy line pending wrap
    assert [r["raw_placements"] for r in golden["records"]] == [7, 45, 137, 176, 80]


def test_separate_l_c_bounds_repeated_bundles_and_multinomial(capsys):
# line-length: ignore-next-line -- legacy line pending wrap
    result = cli_json(["count", "bundle-sets", "--max-r", "1", "--max-l", "1", "--max-c", "0"], capsys)
    assert result["records"] == [
        {"support-edges": 1, "distinct_bundle_sets": 3, "raw_placements": 3},
        {"support-edges": 2, "distinct_bundle_sets": 1, "raw_placements": 2},
    ]
# line-length: ignore-next-line -- legacy line pending wrap
    sets = list(iter_bundle_sets(CountQuery(ComponentConstraints(max_r=2), support_edges=2)))
    rr = next(bs for bs in sets if bs.multiplicities[0] == 2)
    assert rr.raw_placement_count == 1
    rl = BundleSet((1, 1, 0, 0, 0, 0, 0))
    assert rl.raw_placement_count == 2
    with pytest.raises(ValueError):
        type(SIMPLE_PRIMITIVE_BUNDLES[0])("R||R", 2, 0)


def test_component_constraints_intersect_total_bounds_before_edge_cap(capsys):
    query = CountQuery(ComponentConstraints(max_rlc=12, max_r=0, max_lc=1))
    assert query.component_max_edges() == 1
    assert query.effective_support_edge_range().maximum == 1
# line-length: ignore-next-line -- legacy line pending wrap
    supports = cli_json(["count", "supports", "--max-rlc", "12", "--max-r", "0", "--max-lc", "1"], capsys)
    assert [row["support_edges"] for row in supports["records"]] == [1]
# line-length: ignore-next-line -- legacy line pending wrap
    bundle_sets = cli_json(["count", "bundle-sets", "--max-rlc", "12", "--max-r", "0", "--max-lc", "1"], capsys)
    assert [row["support-edges"] for row in bundle_sets["records"]] == [1]

def test_bundle_set_rejects_invalid_multiplicity_boundaries():
    for multiplicities in (
        (),
        (0, 0, 0, 0, 0, 0),
        (0, 0, 0, 0, 0, 0, 0, 0),
    ):
# line-length: ignore-next-line -- legacy line pending wrap
        with pytest.raises(ValueError, match="one entry per simple primitive bundle type"):
            BundleSet(multiplicities)

    with pytest.raises(ValueError, match="non-negative"):
        BundleSet((-1, 0, 0, 0, 0, 0, 0))

    with pytest.raises(ValueError, match="integers"):
        BundleSet((1.5, 0, 0, 0, 0, 0, 0))


# line-length: ignore-next-line -- legacy line pending wrap
def test_component_upper_bounds_are_intersected_before_support_edge_cap(capsys):
# line-length: ignore-next-line -- legacy line pending wrap
    supports = cli_json(["count", "supports", "--max-rlc", "12", "--max-r", "0", "--max-lc", "1"], capsys)
    assert supports["query"]["effective_support_edges"]["max"] == 1
    assert [row["support_edges"] for row in supports["records"]] == [1]

# line-length: ignore-next-line -- legacy line pending wrap
    bundle_sets = cli_json(["count", "bundle-sets", "--max-rlc", "12", "--max-r", "0", "--max-l", "1", "--max-c", "1"], capsys)
    assert bundle_sets["query"]["effective_support_edges"]["max"] == 2
    assert [row["support-edges"] for row in bundle_sets["records"]] == [1, 2]


def test_bundle_set_rejects_invalid_multiplicity_shape():
# line-length: ignore-next-line -- legacy line pending wrap
    with pytest.raises(ValueError, match="one entry per simple primitive bundle type"):
        BundleSet((0,) * (len(SIMPLE_PRIMITIVE_BUNDLES) - 1))
# line-length: ignore-next-line -- legacy line pending wrap
    with pytest.raises(ValueError, match="one entry per simple primitive bundle type"):
        BundleSet((0,) * (len(SIMPLE_PRIMITIVE_BUNDLES) + 1))
    with pytest.raises(ValueError, match="integers"):
        BundleSet((0.5,) + (0,) * (len(SIMPLE_PRIMITIVE_BUNDLES) - 1))
    with pytest.raises(ValueError, match="non-negative"):
        BundleSet((-1,) + (0,) * (len(SIMPLE_PRIMITIVE_BUNDLES) - 1))


def test_groupings_and_totals_only(capsys):
# line-length: ignore-next-line -- legacy line pending wrap
    r_lc = cli_json(["count", "bundle-sets", "--max-rlc", "3", "--group-by", "r,lc"], capsys)
    assert r_lc["group_by"] == ["r", "lc"]
# line-length: ignore-next-line -- legacy line pending wrap
    assert all(set(row) == {"r", "lc", "distinct_bundle_sets", "raw_placements"} for row in r_lc["records"])
# line-length: ignore-next-line -- legacy line pending wrap
    rlc = cli_json(["count", "bundle-sets", "--max-r", "1", "--max-l", "1", "--max-c", "1", "--group-by", "r,l,c"], capsys)
    assert rlc["group_by"] == ["r", "l", "c"]
# line-length: ignore-next-line -- legacy line pending wrap
    total = cli_json(["count", "bundle-sets", "--max-rlc", "0", "--group-by", "none"], capsys)
# line-length: ignore-next-line -- legacy line pending wrap
    assert total["records"] == [{"distinct_bundle_sets": 0, "raw_placements": 0}]
    assert total["totals"] == {"distinct_bundle_sets": 0, "raw_placements": 0}


def test_support_count_regression_and_kinds(capsys):
    out = cli_json(["count", "supports", "--max-support-edges", "8"], capsys)
# line-length: ignore-next-line -- legacy line pending wrap
    assert [r["basic"] for r in out["records"]] == [1, 1, 3, 5, 12, 30, 79, 227]
# line-length: ignore-next-line -- legacy line pending wrap
    assert [r["terminal"] for r in out["records"]] == [1, 2, 7, 21, 73, 255, 946, 3618]
# line-length: ignore-next-line -- legacy line pending wrap
    assert [r["relevant"] for r in out["records"]] == [1, 1, 2, 4, 10, 27, 80, 258]
# line-length: ignore-next-line -- legacy line pending wrap
    exact = cli_json(["count", "supports", "--support-edges", "3", "--support-kind", "relevant"], capsys)
    assert exact["records"] == [{"support_edges": 3, "relevant": 2}]
# line-length: ignore-next-line -- legacy line pending wrap
    ranged = cli_json(["count", "supports", "--min-support-edges", "2", "--max-support-edges", "3", "--support-kind", "basic"], capsys)
    assert ranged["totals"] == {"basic": 4}


@pytest.mark.parametrize("kwargs,finite", [
# line-length: ignore-next-line -- legacy line pending wrap
    ({"max_rlc": 5}, True), ({"max_r": 3}, False), ({"max_l": 2}, False), ({"max_c": 2}, False), ({"max_lc": 3}, False),
# line-length: ignore-next-line -- legacy line pending wrap
    ({"max_r": 3, "max_lc": 5}, True), ({"max_r": 3, "max_l": 2, "max_c": 2}, True), ({"max_l": 2, "max_c": 2}, False),
])
def test_component_finiteness(kwargs, finite):
    q = CountQuery(ComponentConstraints(**kwargs))
    if finite:
        assert q.effective_support_edge_range().maximum is not None
    else:
        with pytest.raises(ValueError):
            q.effective_support_edge_range()


def test_all_component_presence_combinations_become_finite_with_edge_cap():
    names = ["max_rlc", "max_r", "max_l", "max_c", "max_lc"]
    for mask in range(32):
        kwargs = {name: 3 for i, name in enumerate(names) if mask & (1 << i)}
        q = CountQuery(ComponentConstraints(**kwargs), max_support_edges=4)
        assert q.effective_support_edge_range().maximum <= 4


def test_scope_errors_profiles_and_empty_queries(capsys):
# line-length: ignore-next-line -- legacy line pending wrap
    assert_error(capsys, ["count", "supports", "--max-r", "3"], "no finite maximum")
# line-length: ignore-next-line -- legacy line pending wrap
    assert cli_json(["count", "supports", "--max-r", "3", "--max-support-edges", "5"], capsys)["query"]["effective_support_edges"]["max"] == 5
# line-length: ignore-next-line -- legacy line pending wrap
    assert cli_json(["count", "bundle-sets", "--max-rlc", "0"], capsys)["totals"]["distinct_bundle_sets"] == 0
# line-length: ignore-next-line -- legacy line pending wrap
    assert_error(capsys, ["count", "bundle-sets", "--max-r", "-1", "--max-support-edges", "1"], "must be non-negative")
# line-length: ignore-next-line -- legacy line pending wrap
    assert_error(capsys, ["count", "bundle-sets", "--support-edges", "2", "--max-support-edges", "2"], "mutually exclusive")
# line-length: ignore-next-line -- legacy line pending wrap
    assert_error(capsys, ["count", "bundle-sets", "--min-support-edges", "3", "--max-support-edges", "2"], "cannot exceed")
# line-length: ignore-next-line -- legacy line pending wrap
    assert cli_json(["count", "bundle-sets", "--max-rlc", "1", "--support-edges", "2"], capsys)["totals"]["distinct_bundle_sets"] == 0
# line-length: ignore-next-line -- legacy line pending wrap
    prof = cli_json(["count", "bundle-sets", "--profile", "main", "--max-support-edges", "6"], capsys)
    assert prof["query"]["component_constraints"]["max_r"] == 3
    assert prof["query"]["effective_support_edges"]["max"] == 6
# line-length: ignore-next-line -- legacy line pending wrap
    assert_error(capsys, ["count", "bundle-sets", "--profile", "main", "--max-r", "3"], "mutually exclusive")
# line-length: ignore-next-line -- legacy line pending wrap
    assert_error(capsys, ["count", "supports", "--max-supp", "5"], "unrecognized arguments")


def test_help_and_removed_staged_commands(capsys):
# line-length: ignore-next-line -- legacy line pending wrap
    top = subprocess.run([sys.executable, "-m", "rice", "--help"], check=True, text=True, capture_output=True).stdout
    assert "count" in top
    assert "enum" in top
# line-length: ignore-next-line -- legacy line pending wrap
    count = subprocess.run([sys.executable, "-m", "rice", "count", "--help"], check=True, text=True, capture_output=True).stdout
# line-length: ignore-next-line -- legacy line pending wrap
    assert "supports" in count and "bundle-types" in count and "bundle-sets" in count
# line-length: ignore-next-line -- legacy line pending wrap
    target = subprocess.run([sys.executable, "-m", "rice", "count", "bundle-sets", "--help"], check=True, text=True, capture_output=True).stdout
    assert "--max-lc" in target and "--group-by" in target
    assert main(["count"]) == 0
    for command in ("supports", "bundles", "labelings", "reduced"):
        assert_error(capsys, [command], "invalid choice")


def test_assignment_assigned_support_and_network_pr2_golden_results(capsys):
# line-length: ignore-next-line -- legacy line pending wrap
    assignments = cli_json(["count", "assignments", "--profile", "main"], capsys)
    assert assignments["group_by"] == ["support-edges"]
# line-length: ignore-next-line -- legacy line pending wrap
    assert [r["support-edges"] for r in assignments["records"]] == list(range(1, 9))
    assert "source_support_edges" not in assignments["records"][0]
# line-length: ignore-next-line -- legacy line pending wrap
    assert [r["distinct_bundle_sets"] for r in assignments["records"]] == [7, 28, 80, 127, 120, 64, 25, 6]
# line-length: ignore-next-line -- legacy line pending wrap
    assert [r["assignments_per_support"] for r in assignments["records"]] == [7, 49, 335, 1622, 4602, 7192, 5712, 1792]
# line-length: ignore-next-line -- legacy line pending wrap
    assert [r["raw_assignments"] for r in assignments["records"]] == [7, 49, 670, 6488, 46020, 194184, 456960, 462336]
    assert assignments["totals"]["raw_assignments"] == 1166714

# line-length: ignore-next-line -- legacy line pending wrap
    golden_assignments = cli_json(["count", "assignments", "--profile", "golden"], capsys)
# line-length: ignore-next-line -- legacy line pending wrap
    assert [r["assignments_per_support"] for r in golden_assignments["records"]] == [7, 45, 137, 176, 80]
    assert golden_assignments["totals"]["raw_assignments"] == 1830

# line-length: ignore-next-line -- legacy line pending wrap
    assigned = cli_json(["count", "assigned-supports", "--profile", "main"], capsys)
# line-length: ignore-next-line -- legacy line pending wrap
    assert [r["assigned_support_classes"] for r in assigned["records"]] == [7, 28, 380, 3770, 28004, 127627, 323330, 346948]
# line-length: ignore-next-line -- legacy line pending wrap
    assert assigned["totals"] == {"assigned_support_classes": 830094, "raw_assignments": 1166714}

    networks = cli_json(["count", "networks", "--profile", "golden"], capsys)
    assert networks["object"] == "networks"
    assert networks["relation"] == "local-sp"
# line-length: ignore-next-line -- legacy line pending wrap
    assert networks["definition"] == "canonical-reduced-topology-local-series-parallel-v1"
    assert "canonical_signatures" not in networks
    assert networks["totals"]["networks"] == 313
# line-length: ignore-next-line -- legacy line pending wrap
    assert networks["diagnostics"] == {"raw_assignments": 1830, "assigned_support_classes": 1112, "unique_reduced_networks": 313}


def test_pr2_separate_l_c_fixture_across_stages(capsys):
    args = ["--max-r", "1", "--max-l", "1", "--max-c", "0"]
# line-length: ignore-next-line -- legacy line pending wrap
    assert cli_json(["count", "assignments", *args], capsys)["totals"]["raw_assignments"] == 5
# line-length: ignore-next-line -- legacy line pending wrap
    assert cli_json(["count", "assigned-supports", *args], capsys)["totals"]["assigned_support_classes"] == 4
# line-length: ignore-next-line -- legacy line pending wrap
    networks = cli_json(["count", "networks", *args, "--group-by", "r,l,c"], capsys)
    assert networks["totals"]["networks"] == 4
    assert networks["records"] == [
        {"r": 0, "l": 1, "c": 0, "networks": 1},
        {"r": 1, "l": 0, "c": 0, "networks": 1},
        {"r": 1, "l": 1, "c": 0, "networks": 2},
    ]


def test_pr2_ladenheim_nearby_local_sp_slice_and_grouping_errors(capsys):
# line-length: ignore-next-line -- legacy line pending wrap
    result = network_census(CountQuery(ComponentConstraints(max_r=3, max_lc=2), max_support_edges=5))
    assert result.total == 140
    assert result.matrix() == ((0, 2, 2), (1, 4, 12), (0, 4, 34), (0, 4, 77))
# line-length: ignore-next-line -- legacy line pending wrap
    assert cli_json(["count", "networks", "--max-rlc", "0"], capsys)["totals"]["networks"] == 0
# line-length: ignore-next-line -- legacy line pending wrap
    edge_only = cli_json(["count", "assignments", "--support-edges", "4"], capsys)
# line-length: ignore-next-line -- legacy line pending wrap
    assert edge_only["query"]["effective_support_edges"] == {"min": 4, "max": 4}
# line-length: ignore-next-line -- legacy line pending wrap
    edge_only_networks = cli_json(["count", "networks", "--support-edges", "4"], capsys)
# line-length: ignore-next-line -- legacy line pending wrap
    assert edge_only_networks["query"]["effective_support_edges"] == {"min": 4, "max": 4}
    assert edge_only_networks["totals"]["networks"] > 0
# line-length: ignore-next-line -- legacy line pending wrap
    assert_error(capsys, ["count", "networks", "--profile", "golden", "--relation", "bogus"], "invalid choice")
# line-length: ignore-next-line -- legacy line pending wrap
    assert_error(capsys, ["count", "networks", "--profile", "golden", "--group-by", "support-edges"], "unsupported network grouping dimension")
# line-length: ignore-next-line -- legacy line pending wrap
    assert cli_json(["count", "networks", "--profile", "golden", "--group-by", "none"], capsys)["records"] == [{"networks": 313}]


def _markdown_rows(output: str) -> list[list[str]]:
    return [
        [cell.strip() for cell in line.strip().strip("|").split("|")]
        for line in output.splitlines()
        if line.startswith("|")
    ]


def test_pr2_grouped_json_keys_totals_and_markdown_alignment(capsys):
# line-length: ignore-next-line -- legacy line pending wrap
    default_assignments = cli_json(["count", "assignments", "--max-rlc", "1"], capsys)
    assert default_assignments["group_by"] == ["support-edges"]
# line-length: ignore-next-line -- legacy line pending wrap
    assert all("support-edges" in row for row in default_assignments["records"])
# line-length: ignore-next-line -- legacy line pending wrap
    assert all("source_support_edges" not in row for row in default_assignments["records"])

# line-length: ignore-next-line -- legacy line pending wrap
    compound_assignments = cli_json(["count", "assignments", "--max-rlc", "1", "--group-by", "support-edges,r"], capsys)
    assert compound_assignments["group_by"] == ["support-edges", "r"]
# line-length: ignore-next-line -- legacy line pending wrap
    assert all("support-edges" in row and "r" in row for row in compound_assignments["records"])

# line-length: ignore-next-line -- legacy line pending wrap
    default_assigned = cli_json(["count", "assigned-supports", "--max-rlc", "1"], capsys)
    assert default_assigned["group_by"] == ["support-edges"]
    assert all("support-edges" in row for row in default_assigned["records"])
# line-length: ignore-next-line -- legacy line pending wrap
    assert all("source_support_edges" not in row for row in default_assigned["records"])

# line-length: ignore-next-line -- legacy line pending wrap
    compound_assigned = cli_json(["count", "assigned-supports", "--max-rlc", "1", "--group-by", "support-edges,r"], capsys)
    assert compound_assigned["group_by"] == ["support-edges", "r"]
# line-length: ignore-next-line -- legacy line pending wrap
    assert all("support-edges" in row and "r" in row for row in compound_assigned["records"])

    query = CountQuery(ComponentConstraints(max_r=3, max_lc=5))
# line-length: ignore-next-line -- legacy line pending wrap
    expected = assignment_census(query, group_by=("support-edges",)).relevant_supports_total
    assert expected == 383
# line-length: ignore-next-line -- legacy line pending wrap
    assert assignment_census(query, group_by=("r",)).relevant_supports_total == expected
# line-length: ignore-next-line -- legacy line pending wrap
    assert assignment_census(query, group_by=("none",)).relevant_supports_total == expected

# line-length: ignore-next-line -- legacy line pending wrap
    for target, group_by in (("assignments", "none"), ("assignments", "r,lc"), ("assigned-supports", "none"), ("assigned-supports", "r,lc")):
# line-length: ignore-next-line -- legacy line pending wrap
        assert main(["count", target, "--max-rlc", "1", "--group-by", group_by, "--format", "table"]) == 0
        rows = _markdown_rows(capsys.readouterr().out)
        header_width = len(rows[0])
        assert len(rows[-1]) == header_width


def test_pr2_help_lists_objects_without_reductions_or_enum():
# line-length: ignore-next-line -- legacy line pending wrap
    count = subprocess.run([sys.executable, "-m", "rice", "count", "--help"], check=True, text=True, capture_output=True).stdout
# line-length: ignore-next-line -- legacy line pending wrap
    for word in ("supports", "bundle-types", "bundle-sets", "assignments", "assigned-supports", "networks"):
        assert word in count
    assert "reductions" in count
    assert "enum supports" not in count
# line-length: ignore-next-line -- legacy line pending wrap
    target = subprocess.run([sys.executable, "-m", "rice", "count", "networks", "--help"], check=True, text=True, capture_output=True).stdout
    assert "--relation" in target and "--group-by" in target
