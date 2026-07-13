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
    assert "| Support edges |" in tty
