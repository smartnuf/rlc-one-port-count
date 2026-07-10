import json
import subprocess
import sys

import pytest

from rice.cli import main


def test_supports_max_edges_option_works(capsys):
    assert main(["supports", "--max-edges", "9"]) == 0

    output = capsys.readouterr().out

    assert "Support census: max_edges <= 9" in output


def test_supports_budget_options_derive_max_edges(capsys):
    assert main(["supports", "--max-r", "3", "--max-reactive", "6"]) == 0

    output = capsys.readouterr().out

    assert "Support census: max_edges <= 9" in output


def test_supports_max_edges_and_budget_options_are_mutually_exclusive(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(["supports", "--max-edges", "9", "--max-r", "3", "--max-reactive", "6"])

    assert excinfo.value.code == 2
    assert "mutually exclusive" in capsys.readouterr().err


def test_supports_requires_complete_budget_pair(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(["supports", "--max-r", "3"])

    assert excinfo.value.code == 2
    assert "must be provided together" in capsys.readouterr().err


def test_supports_subcommand_help_shows_max_edges():
    result = subprocess.run(
        [sys.executable, "-m", "rice", "supports", "--help"],
        check=True,
        text=True,
        capture_output=True,
    )

    assert "--max-edges" in result.stdout
    assert "--max-r" in result.stdout
    assert "--max-reactive" in result.stdout


def test_top_level_help_does_not_show_support_or_count_options_as_global():
    result = subprocess.run(
        [sys.executable, "-m", "rice", "--help"],
        check=True,
        text=True,
        capture_output=True,
    )

    assert "usage: rice" in result.stdout
    assert "Resistor-Inductor-Capacitor Enumerator" in result.stdout
    assert "count" in result.stdout
    assert "supports" in result.stdout
    assert "bundles" in result.stdout
    assert "--max-edges" not in result.stdout
    assert "--max-r" not in result.stdout
    assert "--max-reactive" not in result.stdout
    assert "--mode" not in result.stdout


def test_bundles_subcommand_outputs_phase_2_census(capsys):
    assert main(["bundles", "--max-r", "3", "--max-reactive", "5"]) == 0

    output = capsys.readouterr().out

    assert "Simple-bundle assignment census: R <= 3, L+C <= 5, max_edges <= 8" in output
    assert "| Total | 383 | — | 1166714 |" in output


def test_bundles_json_output(capsys):
    assert main(["bundles", "--format", "json"]) == 0

    output = json.loads(capsys.readouterr().out)

    assert output["assignments_per_support_by_edges"] == {
        "1": 7,
        "2": 49,
        "3": 335,
        "4": 1622,
        "5": 4602,
        "6": 7192,
        "7": 5712,
        "8": 1792,
    }
    assert output["leaf_assignments_total"] == 1166714


def test_bundles_max_edges_can_truncate_for_debugging(capsys):
    assert main(["bundles", "--max-r", "3", "--max-reactive", "5", "--max-edges", "7"]) == 0

    output = capsys.readouterr().out

    assert "Simple-bundle assignment census: R <= 3, L+C <= 5, max_edges <= 7" in output


def test_bundles_max_edges_cannot_exceed_derived_budget(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(["bundles", "--max-r", "3", "--max-reactive", "5", "--max-edges", "9"])

    assert excinfo.value.code == 2
    assert "cannot exceed" in capsys.readouterr().err


def test_bundles_subcommand_help_shows_bundle_options():
    result = subprocess.run(
        [sys.executable, "-m", "rice", "bundles", "--help"],
        check=True,
        text=True,
        capture_output=True,
    )

    assert "--max-r" in result.stdout
    assert "--max-reactive" in result.stdout
    assert "--max-edges" in result.stdout
    assert "debugging/truncation" in result.stdout


def test_count_subcommand_help_shows_count_options():
    result = subprocess.run(
        [sys.executable, "-m", "rice", "count", "--help"],
        check=True,
        text=True,
        capture_output=True,
    )

    assert "--max-r" in result.stdout
    assert "--max-reactive" in result.stdout
    assert "--mode" in result.stdout


def test_legacy_count_options_before_supports_are_rejected(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(["--max-r", "3", "--max-reactive", "6", "supports"])

    assert excinfo.value.code == 2
    err = capsys.readouterr().err
    assert "must be placed after the subcommand" in err


def test_legacy_no_subcommand_count_interface_still_works(capsys):
    assert main(["--max-r", "2", "--max-reactive", "0", "--format", "json"]) == 0

    output = json.loads(capsys.readouterr().out)

    assert len(output["table"]) == 3
    assert all(len(row) == 1 for row in output["table"])


def test_count_subcommand_still_works(capsys):
    assert main(["count", "--max-r", "2", "--format", "json", "--max-reactive", "0"]) == 0

    output = json.loads(capsys.readouterr().out)

    assert len(output["table"]) == 3
    assert all(len(row) == 1 for row in output["table"])
