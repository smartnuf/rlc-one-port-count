import json
import subprocess
import sys
from pathlib import Path

import networkx as nx

from rice.core import (
    _iter_reduced_topology_signatures,
    _reduced_topology_census,
    canonical_reduced_signature,
    reduced_signature_component_counts,
)

GOLDEN = json.loads(Path("data/counts/small-r2-x3.json").read_text())
EXPECTED_TABLE = ((0, 2, 2, 4), (1, 4, 12, 40), (0, 4, 34, 210))


def test_small_r2_x3_object_language_counts_match_golden_values():
    result = _reduced_topology_census(max_r=2, max_reactive=3)
    assert result.exact_table == EXPECTED_TABLE
    assert result.total == 313
    assert result.raw_leaf_assignments_total == 1830
    assert result.canonical_labeling_orbits_total == 1112


def test_count_networks_cli_matches_committed_json_exactly():
    cli = subprocess.run([sys.executable, "-m", "rice", "count", "networks", "--profile", "golden", "--format", "json"], check=True, text=True, capture_output=True)
    assert json.loads(cli.stdout) == GOLDEN


def test_each_signature_is_counted_in_its_reduced_primitive_cell():
    counts = [[0 for _ in range(4)] for _ in range(3)]
    for signature in _iter_reduced_topology_signatures(max_r=2, max_reactive=3):
        r, l, c = reduced_signature_component_counts(signature)
        counts[r][l + c] += 1
    assert tuple(tuple(row) for row in counts) == EXPECTED_TABLE


def test_l_and_c_distinctions_are_preserved_while_table_aggregates_by_x():
    signatures = {s.stable_string() for s in _iter_reduced_topology_signatures(max_r=0, max_reactive=1)}
    assert "0-1:L" in signatures
    assert "0-1:C" in signatures


def test_independent_bruteforce_r1_x1_matches_internal_network_enumerator():
    concrete = set()
    graph = nx.Graph([(0, 1)])
    for label in ["R", "L", "C", "R||L", "R||C"]:
        concrete.add(canonical_reduced_signature(graph, (0, 1), {(0, 1): label}).stable_string())
    path = nx.Graph([(0, 1), (1, 2)])
    for first, second in [("R", "L"), ("L", "R"), ("R", "C"), ("C", "R")]:
        concrete.add(canonical_reduced_signature(path, (0, 2), {(0, 1): first, (1, 2): second}).stable_string())
    api = {s.stable_string() for s in _iter_reduced_topology_signatures(max_r=1, max_reactive=1)}
    assert api == concrete
