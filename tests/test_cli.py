import json
import subprocess
import sys

import pytest

from rice.cli import main


def _assert_cli_error_without_traceback(capsys, argv, expected):
    with pytest.raises(SystemExit) as excinfo:
        main(argv)

    assert excinfo.value.code == 2
    err = capsys.readouterr().err
    if isinstance(expected, tuple):
        assert any(piece in err for piece in expected)
    else:
        assert expected in err
    assert "Traceback" not in err


def test_abbreviated_long_options_are_rejected(capsys):
    _assert_cli_error_without_traceback(capsys, ["--mo", "lc", "supports"], ("unrecognized arguments", "invalid choice"))
    _assert_cli_error_without_traceback(capsys, ["supports", "--max-e", "8"], "unrecognized arguments")
    _assert_cli_error_without_traceback(capsys, ["bundles", "--max-re", "5"], "unrecognized arguments")


def test_generic_mode_is_rejected_cleanly_without_traceback(capsys):
    _assert_cli_error_without_traceback(
        capsys,
        ["count", "--mode", "generic", "--max-r", "3", "--max-reactive", "5"],
        "invalid choice",
    )
    _assert_cli_error_without_traceback(
        capsys,
        ["--mode", "generic", "--max-r", "3", "--max-reactive", "5"],
        "invalid choice",
    )


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


def test_supports_rejects_invalid_limits_without_traceback(capsys):
    cases = [
        (["supports", "--max-edges", "0"], "must be a positive integer"),
        (["supports", "--max-edges", "-1"], "must be a positive integer"),
        (["supports", "--max-r", "-1", "--max-reactive", "2"], "must be nonnegative"),
        (["supports", "--max-r", "1", "--max-reactive", "-2"], "must be nonnegative"),
        (["supports", "--max-r", "0", "--max-reactive", "0"], "must be positive"),
        (["supports", "--max-reactive", "1"], "must be provided together"),
    ]
    for argv, expected in cases:
        _assert_cli_error_without_traceback(capsys, argv, expected)


def test_supports_allows_one_zero_budget_when_sum_positive(capsys):
    assert main(["supports", "--max-r", "0", "--max-reactive", "1"]) == 0

    assert "Support census: max_edges <= 1" in capsys.readouterr().out


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
    assert "reduced" in result.stdout
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


def test_bundles_zero_zero_budget_is_empty_census(capsys):
    assert main(["bundles", "--max-r", "0", "--max-reactive", "0"]) == 0

    output = capsys.readouterr().out
    assert "max_edges <= 0" in output
    assert "| Total | 0 | — | 0 |" in output
    assert "| 1 |" not in output


def test_bundles_rejects_invalid_limits_without_traceback(capsys):
    cases = [
        (["bundles", "--max-r", "-1", "--max-reactive", "0"], "must be nonnegative"),
        (["bundles", "--max-r", "0", "--max-reactive", "-1"], "must be nonnegative"),
        (["bundles", "--max-r", "1", "--max-reactive", "0", "--max-edges", "0"], "must be a positive integer"),
        (["bundles", "--max-r", "1", "--max-reactive", "0", "--max-edges", "-1"], "must be a positive integer"),
    ]
    for argv, expected in cases:
        _assert_cli_error_without_traceback(capsys, argv, expected)


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


def test_labelings_subcommand_outputs_phase_3_census(capsys):
    assert main(["labelings", "--max-r", "3", "--max-reactive", "5"]) == 0

    output = capsys.readouterr().out

    assert "Canonical simple-bundle labeling census: R <= 3, L+C <= 5, max_edges <= 8" in output
    assert "| Total | 383 | 1166714 | 830094 |" in output


def test_labelings_json_output(capsys):
    assert main(["labelings", "--format", "json"]) == 0

    output = json.loads(capsys.readouterr().out)

    assert output["raw_leaf_assignments_total"] == 1166714
    assert output["canonical_labeling_orbits_total"] == 830094
    assert output["canonical_labeling_orbits_by_edges"] == {
        "1": 7,
        "2": 28,
        "3": 380,
        "4": 3770,
        "5": 28004,
        "6": 127627,
        "7": 323330,
        "8": 346948,
    }


def test_labelings_max_edges_cannot_exceed_derived_budget(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(["labelings", "--max-r", "3", "--max-reactive", "5", "--max-edges", "9"])

    assert excinfo.value.code == 2
    assert "cannot exceed" in capsys.readouterr().err


def test_labelings_zero_zero_budget_is_empty_census(capsys):
    assert main(["labelings", "--max-r", "0", "--max-reactive", "0"]) == 0

    output = capsys.readouterr().out
    assert "max_edges <= 0" in output
    assert "| Total | 0 | 0 | 0 |" in output
    assert "| 1 |" not in output


def test_labelings_rejects_invalid_limits_without_traceback(capsys):
    cases = [
        (["labelings", "--max-r", "-1", "--max-reactive", "0"], "must be nonnegative"),
        (["labelings", "--max-r", "0", "--max-reactive", "-1"], "must be nonnegative"),
        (["labelings", "--max-r", "1", "--max-reactive", "0", "--max-edges", "0"], "must be a positive integer"),
        (["labelings", "--max-r", "1", "--max-reactive", "0", "--max-edges", "-1"], "must be a positive integer"),
    ]
    for argv, expected in cases:
        _assert_cli_error_without_traceback(capsys, argv, expected)


def test_labelings_subcommand_help_shows_labeling_options():
    result = subprocess.run(
        [sys.executable, "-m", "rice", "labelings", "--help"],
        check=True,
        text=True,
        capture_output=True,
    )

    assert "--max-r" in result.stdout
    assert "--max-reactive" in result.stdout
    assert "--max-edges" in result.stdout
    assert "debugging/truncation" in result.stdout


def test_reduced_subcommand_outputs_canonical_census(capsys):
    assert main(["reduced"]) == 0

    output = capsys.readouterr().out

    assert "Canonical reduced-topology census: R <= 2, L+C <= 3, max_edges <= 5" in output
    assert "Cumulative reduced-topology total: 313" in output
    assert "raw phase-2 assignments=1830" in output


def test_reduced_json_output(capsys):
    assert main(["reduced", "--max-r", "2", "--max-reactive", "3", "--format", "json"]) == 0

    output = json.loads(capsys.readouterr().out)

    assert output["exact_counts_by_r_x"] == [[0, 2, 2, 4], [1, 4, 12, 40], [0, 4, 34, 210]]
    assert output["total"] == 313
    assert output["diagnostics"]["raw_phase2_assignments_total"] == 1830
    assert output["diagnostics"]["phase3_assigned_support_labeling_orbits_total"] == 1112
    assert "canonical_signatures" not in output
    assert (
        output["regeneration_command"]
        == ".venv/bin/python -m rice reduced --max-r 2 --max-reactive 3 --format json"
    )


def test_reduced_subcommand_defaults_to_small_golden_slice(capsys):
    assert main(["reduced"]) == 0

    output = capsys.readouterr().out

    assert "Canonical reduced-topology census: R <= 2, L+C <= 3, max_edges <= 5" in output
    assert "Cumulative reduced-topology total: 313" in output


def test_reduced_subcommand_help_shows_reduced_options():
    result = subprocess.run(
        [sys.executable, "-m", "rice", "reduced", "--help"],
        check=True,
        text=True,
        capture_output=True,
    )

    assert "--max-r" in result.stdout
    assert "--max-reactive" in result.stdout
    assert "--format" in result.stdout
    assert "default: 2" in result.stdout
    assert "default: 3" in result.stdout
