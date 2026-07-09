import json
import subprocess
import sys
from pathlib import Path

from rice.cli import main


def test_top_level_format_is_preserved_before_supports_subcommand(capsys):
    assert main(["--format", "json", "supports", "--max-edges", "1"]) == 0

    output = json.loads(capsys.readouterr().out)

    assert output["max_edges"] == 1
    assert output["basic_total"] == 1
    assert output["terminal_labelings_total"] == 1
    assert output["relevant_total"] == 1


def test_top_level_count_options_are_preserved_before_count_subcommand(capsys):
    assert (
        main(["--max-r", "2", "--format", "json", "count", "--max-reactive", "0"]) == 0
    )

    output = json.loads(capsys.readouterr().out)

    assert len(output["table"]) == 3
    assert all(len(row) == 1 for row in output["table"])


def test_rice_module_help_smoke():
    result = subprocess.run(
        [sys.executable, "-m", "rice", "--help"],
        check=True,
        text=True,
        capture_output=True,
    )

    assert "usage: rice" in result.stdout
    assert "Resistor-Inductor-Capacitor Enumerator" in result.stdout


def test_legacy_console_alias_help_smoke():
    legacy_command = Path(sys.executable).parent / "rlc-oneport-count"
    assert legacy_command.exists()

    result = subprocess.run(
        [str(legacy_command), "--help"],
        check=True,
        text=True,
        capture_output=True,
    )

    assert "usage: rice" in result.stdout
    assert "Resistor-Inductor-Capacitor Enumerator" in result.stdout
