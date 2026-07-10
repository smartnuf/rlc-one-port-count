import json
import subprocess
import sys
from pathlib import Path

import networkx as nx

from rice.core import (
    canonical_reduced_signature,
    iter_reduced_topology_signatures,
    reduced_signature_component_counts,
    reduced_topology_census,
)

GOLDEN = json.loads(Path("data/counts/small-r2-x3.json").read_text())
EXPECTED_TABLE = ((0, 2, 2, 4), (1, 4, 12, 40), (0, 4, 34, 210))


def test_small_r2_x3_reduced_census_matches_literal_golden_table():
    result = reduced_topology_census(max_r=2, max_reactive=3)

    assert result.exact_table == EXPECTED_TABLE
    assert result.total == 313
    assert result.raw_leaf_assignments_total == 1830
    assert result.canonical_labeling_orbits_total == 1112


def test_small_r2_x3_api_cli_and_committed_json_agree():
    result = reduced_topology_census(max_r=2, max_reactive=3)
    cli = subprocess.run(
        [
            sys.executable,
            "-m",
            "rice",
            "reduced",
            "--max-r",
            "2",
            "--max-reactive",
            "3",
            "--format",
            "json",
        ],
        check=True,
        text=True,
        capture_output=True,
    )
    payload = json.loads(cli.stdout)

    assert payload == GOLDEN
    assert payload["exact_counts_by_r_x"] == [list(row) for row in EXPECTED_TABLE]
    assert payload["total"] == result.total == GOLDEN["total"]


def test_reduced_census_output_is_deterministic_and_has_no_duplicates():
    first = reduced_topology_census(max_r=2, max_reactive=3).canonical_signatures
    second = reduced_topology_census(max_r=2, max_reactive=3).canonical_signatures

    assert first == second
    assert len(first) == len(set(first)) == 313
    assert list(first) == sorted(first)


def test_each_signature_is_counted_in_its_reduced_primitive_cell():
    counts = [[0 for _ in range(4)] for _ in range(3)]
    for signature in iter_reduced_topology_signatures(max_r=2, max_reactive=3):
        r, l, c = reduced_signature_component_counts(signature)
        counts[r][l + c] += 1

    assert tuple(tuple(row) for row in counts) == EXPECTED_TABLE


def test_l_and_c_distinctions_are_preserved_while_table_aggregates_by_x():
    signatures = set(reduced_topology_census(max_r=0, max_reactive=1).canonical_signatures)

    assert "0-1:L" in signatures
    assert "0-1:C" in signatures
    assert reduced_topology_census(max_r=0, max_reactive=1).exact_table == ((0, 2),)


def test_independent_bruteforce_r1_x1_matches_census_api():
    concrete = set()

    # Single primitive or mixed bundle between terminals.
    graph = nx.Graph([(0, 1)])
    for label in ["R", "L", "C", "R||L", "R||C"]:
        concrete.add(canonical_reduced_signature(graph, (0, 1), {(0, 1): label}).stable_string())

    # Two-edge terminal path with all budgeted primitive labels.
    path = nx.Graph([(0, 1), (1, 2)])
    for first, second in [("R", "L"), ("L", "R"), ("R", "C"), ("C", "R")]:
        concrete.add(
            canonical_reduced_signature(
                path,
                (0, 2),
                {(0, 1): first, (1, 2): second},
            ).stable_string()
        )

    api = set(reduced_topology_census(max_r=1, max_reactive=1).canonical_signatures)
    assert api == concrete
