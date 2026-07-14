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
    assert expected in err
    assert "Traceback" not in err


def _run(*args):
    return subprocess.run([sys.executable, "-m", "rice", *args], text=True, capture_output=True)


def test_removed_staged_commands_are_rejected_cleanly(capsys):
    for command in ("supports", "bundles", "labelings", "reduced"):
        _assert_cli_error_without_traceback(capsys, [command], "invalid choice")


@pytest.mark.parametrize("args", [(), ("-h",), ("--help",), ("help",)])
def test_top_level_help_forms_succeed(args):
    result = _run(*args)
    assert result.returncode == 0
    assert "Command language map" in result.stdout
    assert "count reductions" in result.stdout
    assert "enum supports" in result.stdout
    assert "Pipeline: supports -> bundle-types" in result.stdout
    assert "Example finite scope:" in result.stdout
    assert "count_object" not in result.stdout
    assert "enum_object" not in result.stdout


@pytest.mark.parametrize("args", [("count",), ("count", "--help"), ("help", "count")])
def test_count_group_help_forms_succeed(args):
    result = _run(*args)
    assert result.returncode == 0
    for obj in ("supports", "bundle-types", "bundle-sets", "assignments", "assigned-supports", "networks", "reductions"):
        assert obj in result.stdout
    assert "count_object" not in result.stdout


@pytest.mark.parametrize("args", [("enum",), ("enum", "--help"), ("help", "enum")])
def test_enum_group_help_forms_succeed(args):
    result = _run(*args)
    assert result.returncode == 0
    for obj in ("supports", "bundle-types", "bundle-sets", "assignments", "assigned-supports", "networks"):
        assert obj in result.stdout
    assert "enum_object" not in result.stdout


@pytest.mark.parametrize("args", [
    ("count", "supports", "--help"),
    ("help", "count", "supports"),
    ("--help", "count", "supports"),
])
def test_leaf_help_forms_succeed(args):
    result = _run(*args)
    assert result.returncode == 0
    assert "unlabelled simple shapes" in result.stdout
    assert "Default: auto" in result.stdout
    assert "golden (R<=2, L+C<=3)" in result.stdout
    assert "--support-kind" in result.stdout


def test_object_options_remain_on_object_parser(capsys):
    assert main(["count", "supports", "--max-support-edges", "2", "--format", "table"]) == 0
    assert "Support object census" in capsys.readouterr().out
    _assert_cli_error_without_traceback(capsys, ["count", "--max-support-edges", "2", "supports"], "invalid choice")


def test_auto_output_redirected_is_json_and_table_is_human_readable(capsys, monkeypatch):
    assert main(["count", "supports", "--max-support-edges", "1"]) == 0
    redirected = capsys.readouterr().out
    assert json.loads(redirected)["object"] == "supports"

    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
    assert main(["count", "supports", "--max-support-edges", "1"]) == 0
    tty = capsys.readouterr().out
    assert "Support object census" in tty
    assert "Support edges  Basic supports" in tty
    assert "|---" not in tty


COUNT_FORMAT_CASES = (
    ("supports", "--max-support-edges", "1"),
    ("bundle-types",),
    ("bundle-sets", "--max-rlc", "1"),
    ("assignments", "--max-rlc", "1"),
    ("assigned-supports", "--max-rlc", "1"),
    ("networks", "--max-rlc", "1"),
    ("reductions", "--max-rlc", "1"),
)


@pytest.mark.parametrize("args", COUNT_FORMAT_CASES)
def test_count_table_and_markdown_are_distinct_formats(capsys, args):
    assert main(["count", *args, "--format", "table"]) == 0
    table = capsys.readouterr().out
    assert main(["count", *args, "--format", "markdown"]) == 0
    markdown = capsys.readouterr().out

    assert table != markdown
    assert "|---" not in table
    assert "|---" in markdown


def test_markdown_renderer_escapes_pipe_characters_in_bundle_labels(capsys):
    assert main(["count", "bundle-types", "--format", "markdown"]) == 0
    count_output = capsys.readouterr().out
    assert "R\\|\\|L" in count_output
    assert "R||L" not in count_output

    assert main(["enum", "bundle-types", "--format", "markdown"]) == 0
    enum_output = capsys.readouterr().out
    assert "R\\|\\|L" in enum_output
    assert "R||L" not in enum_output


def test_network_default_matrix_tables_include_row_totals(capsys):
    assert main(["count", "networks", "--profile", "golden", "--format", "markdown"]) == 0
    markdown = capsys.readouterr().out
    assert "| R \\ L+C | 0 | 1 | 2 | 3 | Row total |" in markdown
    assert "| 0 | 0 | 2 | 2 | 4 | 8 |" in markdown
    assert "| 2 | 0 | 4 | 34 | 210 | 248 |" in markdown

    assert main(["count", "networks", "--profile", "golden", "--format", "table"]) == 0
    table = capsys.readouterr().out
    assert "Row total" in table
    assert "      2  0  4  34  210        248" in table


def test_explicit_formats_override_stdout_tty_state(capsys, monkeypatch):
    monkeypatch.setattr(sys.stdout, "isatty", lambda: False)
    assert main(["count", "supports", "--max-support-edges", "1", "--format", "table"]) == 0
    assert "|---" not in capsys.readouterr().out

    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
    assert main(["count", "supports", "--max-support-edges", "1", "--format", "markdown"]) == 0
    assert "|---" in capsys.readouterr().out


def test_table_renderer_handles_totals_only_grouping(capsys):
    assert main(["count", "bundle-sets", "--max-rlc", "1", "--group-by", "none", "--format", "table"]) == 0
    output = capsys.readouterr().out
    assert "Distinct bundle sets  Raw placements represented" in output
    assert "|---" not in output
