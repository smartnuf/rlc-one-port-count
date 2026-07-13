import json
import subprocess
import sys

from rice import CountQuery, ComponentConstraints, enum_assignments, enum_assigned_supports, enum_bundle_types, enum_networks, reduction_census


def run_json(*args):
    out = subprocess.check_output([sys.executable, "-m", "rice", *args], text=True)
    return json.loads(out)


def small_query():
    return CountQuery(component_constraints=ComponentConstraints(max_r=1, max_l=1, max_c=0))


def test_small_rl_catalogue_and_reduction_fibres():
    q = small_query()
    assignments = enum_assignments(q)
    assigned = enum_assigned_supports(q)
    networks = enum_networks(q)
    assert len(assignments) == 5
    assert sorted(a.raw_assignment_count for a in assigned) == [1, 1, 1, 2]
    assert len(assigned) == 4
    assert len(networks) == 4
    assert sorted((n.r, n.l, n.c) for n in networks) == [(0, 1, 0), (1, 0, 0), (1, 1, 0), (1, 1, 0)]
    result = reduction_census(q)
    assert result.pipeline_totals == {"raw_assignments": 5, "assigned_support_classes": 4, "reduced_networks": 4}
    assert result.diagnostics["conservation_checks"] == {"raw_assignments": True, "assigned_supports": True, "network_ids_unique": True}


def test_enum_bundle_types_accepts_ignored_query_for_api_consistency():
    assert enum_bundle_types() == enum_bundle_types(small_query())


def test_cli_enum_targets_are_deterministic_json():
    args = ("enum", "assignments", "--max-r", "1", "--max-l", "1", "--max-c", "0", "--format", "json")
    first = run_json(*args)
    second = run_json(*args)
    assert first == second
    assert first["operation"] == "enum"
    assert first["totals"]["records"] == 5


def test_all_enum_targets_and_golden_reductions_cli():
    assert run_json("enum", "supports", "--max-support-edges", "3", "--format", "json")["totals"]["records"] == 4
    assert run_json("enum", "bundle-types", "--format", "json")["totals"]["records"] == 7
    assert run_json("enum", "bundle-sets", "--max-r", "1", "--max-l", "1", "--max-c", "0", "--format", "json")["totals"]["records"] == 4
    assert run_json("enum", "assigned-supports", "--max-r", "1", "--max-l", "1", "--max-c", "0", "--format", "json")["totals"]["records"] == 4
    assert run_json("enum", "networks", "--max-r", "1", "--max-l", "1", "--max-c", "0", "--format", "json")["totals"]["records"] == 4
    reductions = run_json("count", "reductions", "--profile", "golden", "--format", "json")
    assert reductions["pipeline_totals"] == {"raw_assignments": 1830, "assigned_support_classes": 1112, "reduced_networks": 313}


def test_output_size_guard_fails_cleanly():
    proc = subprocess.run([sys.executable, "-m", "rice", "enum", "assignments", "--profile", "golden", "--max-records", "10"], text=True, capture_output=True)
    assert proc.returncode == 2
    assert "exceeding --max-records" in proc.stderr
    assert "Traceback" not in proc.stderr


def test_max_records_must_be_positive():
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "rice",
            "enum",
            "assignments",
            "--max-r",
            "1",
            "--max-records",
            "0",
        ],
        text=True,
        capture_output=True,
    )
    assert proc.returncode == 2
    assert "must be a positive integer" in proc.stderr
    assert "Traceback" not in proc.stderr
