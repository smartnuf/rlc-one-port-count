from __future__ import annotations

import os
import shutil
import stat
import subprocess
import textwrap
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"

_REQUIRES_BASH = pytest.mark.skipif(
    shutil.which("bash") is None,
    reason="bash is not available on PATH (e.g. native Windows without Git Bash/WSL)",
)

# External commands scripts/setup.sh, scripts/_common.sh, and the fake
# python stubs below call while running with RICE_SETUP_ONLY_PRINT_PYTHON=1
# (before any pip install/run() calls).
_REQUIRED_SYSTEM_TOOLS = ("bash", "awk", "basename", "dirname", "mktemp", "rm", "mkdir")


@_REQUIRES_BASH
def test_public_shell_scripts_parse_with_bash() -> None:
    scripts = sorted(SCRIPTS.glob("*.sh"))
    assert scripts
    subprocess.run(["bash", "-n", *map(str, scripts)], check=True, cwd=REPO_ROOT)


def test_public_shell_scripts_avoid_bash4_only_features() -> None:
    forbidden = ("mapfile", "readarray", "declare -A")
    for script in sorted(SCRIPTS.glob("*.sh")):
        text = script.read_text(encoding="utf-8")
        for needle in forbidden:
            assert needle not in text, f"{script.relative_to(REPO_ROOT)} uses {needle}"
        assert ",," not in text, f"{script.relative_to(REPO_ROOT)} uses Bash 4 case conversion"


def _write_fake_python(path: Path, *, version: str, venv_works: bool) -> None:
    path.write_text(
        textwrap.dedent(
            f"""
            #!/usr/bin/env bash
            set -euo pipefail
            if [[ "$1" == "-c" ]]; then
                if [[ "$2" == *"sys.version_info >= (3, 11)"* ]]; then
                    exit 0
                fi
                printf '%s\n' '  executable: {path}'
                printf '%s\n' '  version: {version}'
                exit 0
            fi
            if [[ "$1" == "-m" && "$2" == "venv" ]]; then
                if [[ "{str(venv_works).lower()}" == "true" ]]; then
                    mkdir -p "$3/bin"
                    exit 0
                fi
                exit 1
            fi
            exit 99
            """
        ).lstrip(),
        encoding="utf-8",
    )
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def _add_required_system_tool_symlinks(bindir: Path) -> None:
    """Symlink the external tools setup.sh needs into ``bindir``.

    The test PATH is set to ``bindir`` alone so that no real ``pythonX.Y``
    elsewhere on the host can be found by ``type -P -a`` and picked instead of
    the fake interpreters below; only these coreutils/bash are still needed.
    """

    for tool in _REQUIRED_SYSTEM_TOOLS:
        found = shutil.which(tool)
        assert found, f"required tool {tool!r} was not found on PATH"
        link = bindir / tool
        if not link.exists():
            os.symlink(found, link)


@_REQUIRES_BASH
def test_setup_sh_skips_python_without_working_venv(tmp_path: Path) -> None:
    bindir = tmp_path / "bin"
    bindir.mkdir()
    _write_fake_python(bindir / "python3.14", version="3.14.0", venv_works=False)
    _write_fake_python(bindir / "python3.13", version="3.13.0", venv_works=True)
    _add_required_system_tool_symlinks(bindir)

    env = os.environ.copy()
    # PATH is replaced, not prepended: if a real python3.14 (or any other
    # probed candidate name) were still reachable elsewhere on PATH, the
    # script would find and select it ahead of the fake python3.13 below,
    # since `type -P -a` returns every match for a name, not just the first.
    env["PATH"] = str(bindir)
    env["RICE_SETUP_ONLY_PRINT_PYTHON"] = "1"

    completed = subprocess.run(
        ["bash", "scripts/setup.sh"],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )

    assert str(bindir / "python3.13") in completed.stdout
    assert str(bindir / "python3.14") not in completed.stdout


def test_powershell_setup_uses_forward_compatible_launcher_probe() -> None:
    text = (SCRIPTS / "setup.ps1").read_text(encoding="utf-8")
    assert "@('-3')" in text
    assert "-m venv" in text
    assert "3.14" in text and "3.13" in text


def test_powershell_clean_skips_reparse_points_before_recursing() -> None:
    text = (SCRIPTS / "clean.ps1").read_text(encoding="utf-8")
    reparse_check = "[System.IO.FileAttributes]::ReparsePoint"
    assert reparse_check in text
    assert text.index("Test-IsReparsePoint -Item $child") < text.index("Remove-PycacheDirectories -Directory $child.FullName")
