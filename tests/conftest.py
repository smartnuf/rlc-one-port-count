"""Pytest configuration for repository-local virtual environment checks."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _normalised_path(path: Path) -> str:
    return os.path.normcase(str(path.resolve()))


def _repository_venv_python(repo_root: Path, platform: str | None = None) -> Path | None:
    """Return the repository venv interpreter path when the venv exists."""

    platform_name = sys.platform if platform is None else platform
    venv_dir = repo_root / ".venv"
    windows_python = venv_dir / "Scripts" / "python.exe"
    posix_python = venv_dir / "bin" / "python"

    candidates = (
        (windows_python, posix_python)
        if platform_name.startswith("win")
        else (posix_python, windows_python)
    )

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return None


def _is_repository_venv_prefix(current_prefix: str, repo_root: Path) -> bool:
    expected_prefix = repo_root / ".venv"
    return _normalised_path(Path(current_prefix)) == _normalised_path(expected_prefix)


def _pytest_command_hint(platform: str | None = None) -> str:
    platform_name = sys.platform if platform is None else platform
    if platform_name.startswith("win"):
        return r".\.venv\Scripts\python.exe -m pytest -q"
    return ".venv/bin/python -m pytest -q"


def pytest_sessionstart(session):  # type: ignore[no-untyped-def]
    """Fail early when tests run with the wrong Python interpreter.

    Codex Cloud setup/maintenance scripts install project dependencies into the
    repository-local `.venv`. If a later task runs plain `python -m pytest` or
    `pytest`, pytest may use the system interpreter. Because pyproject.toml adds
    `src` to pytest's import path, that wrong interpreter can import the project
    source but then fail with misleading missing-dependency errors such as
    `ModuleNotFoundError: No module named 'networkx'`.

    When `.venv` exists, require tests to be run with that venv. Set
    `RICE_ALLOW_NON_VENV=1` to opt out deliberately, for example in a
    separate tox/nox/CI environment that manages dependencies another way.
    """

    if os.environ.get("RICE_ALLOW_NON_VENV") == "1":
        return

    repo_root = Path(__file__).resolve().parents[1]
    venv_python = _repository_venv_python(repo_root)

    if venv_python is None:
        return

    if not _is_repository_venv_prefix(sys.prefix, repo_root):
        raise RuntimeError(
            "Tests must run inside the repository .venv. Use:\n"
            "\n"
            f"    {_pytest_command_hint()}\n"
            "\n"
            f"Current executable: {sys.executable}\n"
            f"Current sys.prefix: {sys.prefix}\n"
            f"Expected sys.prefix: {(repo_root / '.venv').resolve()}\n"
            "\n"
            "To override intentionally, set RICE_ALLOW_NON_VENV=1."
        )
