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


def test_removed_staged_commands_are_rejected_cleanly(capsys):
    for command in ("supports", "bundles", "labelings", "reduced"):
        _assert_cli_error_without_traceback(capsys, [command], "invalid choice")


def test_bare_rice_requires_command():
    result = subprocess.run([sys.executable, "-m", "rice"], text=True, capture_output=True)
    assert result.returncode == 2
    assert "the following arguments are required: command" in result.stderr
    assert "Traceback" not in result.stderr


def test_top_level_help_lists_only_count_subcommand():
    result = subprocess.run([sys.executable, "-m", "rice", "--help"], check=True, text=True, capture_output=True)
    assert "usage: rice" in result.stdout
    assert "count" in result.stdout
    for removed in ("bundles", "labelings", "reduced"):
        assert removed not in result.stdout
    assert "--max-reactive" not in result.stdout


def test_count_help_lists_all_and_only_count_objects():
    result = subprocess.run([sys.executable, "-m", "rice", "count", "--help"], check=True, text=True, capture_output=True)
    for obj in ("supports", "bundle-types", "bundle-sets", "assignments", "assigned-supports", "networks"):
        assert obj in result.stdout
    for removed in ("labelings", "reduced", "bundles"):
        assert removed not in result.stdout


def test_object_options_remain_on_object_parser(capsys):
    assert main(["count", "supports", "--max-support-edges", "2"]) == 0
    assert "Support object census" in capsys.readouterr().out
    _assert_cli_error_without_traceback(capsys, ["count", "--max-support-edges", "2", "supports"], "invalid choice")
