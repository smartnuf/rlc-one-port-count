"""Pytest configuration for repository-local virtual environment checks."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def pytest_sessionstart(session):  # type: ignore[no-untyped-def]
    """Fail early when tests run with the wrong Python interpreter.

    Codex Cloud setup/maintenance scripts install project dependencies into the
    repository-local `.venv`. If a later task runs plain `python -m pytest` or
    `pytest`, pytest may use the system interpreter. Because pyproject.toml adds
    `src` to pytest's import path, that wrong interpreter can import the project
    source but then fail with misleading missing-dependency errors such as
    `ModuleNotFoundError: No module named 'networkx'`.

    When `.venv` exists, require tests to be run with that venv. Set
    `RLC_ONEPORT_ALLOW_NON_VENV=1` to opt out deliberately, for example in a
    separate tox/nox/CI environment that manages dependencies another way.
    """

    if os.environ.get("RLC_ONEPORT_ALLOW_NON_VENV") == "1":
        return

    repo_root = Path(__file__).resolve().parents[1]
    venv_dir = repo_root / ".venv"
    venv_python = venv_dir / "bin" / "python"

    if not venv_python.exists():
        return

    current_prefix = Path(sys.prefix).resolve()
    expected_prefix = venv_dir.resolve()

    if current_prefix != expected_prefix:
        raise RuntimeError(
            "Tests must run inside the repository .venv. Use:\n"
            "\n"
            "    .venv/bin/python -m pytest -q\n"
            "\n"
            f"Current executable: {sys.executable}\n"
            f"Current sys.prefix: {sys.prefix}\n"
            f"Expected sys.prefix: {expected_prefix}\n"
            "\n"
            "To override intentionally, set RLC_ONEPORT_ALLOW_NON_VENV=1."
        )
