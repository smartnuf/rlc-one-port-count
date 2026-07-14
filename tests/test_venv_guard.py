from pathlib import Path

from conftest import (
    _is_repository_venv_prefix,
    _pytest_command_hint,
    _repository_venv_python,
)


# line-length: ignore-next-line -- legacy line pending wrap
def test_repository_venv_python_prefers_windows_layout_on_windows(tmp_path: Path):
    windows_python = tmp_path / ".venv" / "Scripts" / "python.exe"
    posix_python = tmp_path / ".venv" / "bin" / "python"
    windows_python.parent.mkdir(parents=True)
    posix_python.parent.mkdir(parents=True)
    windows_python.write_text("", encoding="utf-8")
    posix_python.write_text("", encoding="utf-8")

# line-length: ignore-next-line -- legacy line pending wrap
    assert _repository_venv_python(tmp_path, platform="win32") == windows_python


def test_repository_venv_python_prefers_posix_layout_on_posix(tmp_path: Path):
    windows_python = tmp_path / ".venv" / "Scripts" / "python.exe"
    posix_python = tmp_path / ".venv" / "bin" / "python"
    windows_python.parent.mkdir(parents=True)
    posix_python.parent.mkdir(parents=True)
    windows_python.write_text("", encoding="utf-8")
    posix_python.write_text("", encoding="utf-8")

    assert _repository_venv_python(tmp_path, platform="linux") == posix_python


# line-length: ignore-next-line -- legacy line pending wrap
def test_repository_venv_prefix_matches_resolved_venv_directory(tmp_path: Path):
    venv_dir = tmp_path / ".venv"
    venv_dir.mkdir()

    assert _is_repository_venv_prefix(str(venv_dir), tmp_path)
    assert not _is_repository_venv_prefix(str(tmp_path), tmp_path)


def test_pytest_command_hint_is_platform_specific():
# line-length: ignore-next-line -- legacy line pending wrap
    assert _pytest_command_hint(platform="win32") == r".\.venv\Scripts\python.exe -m pytest -q"
# line-length: ignore-next-line -- legacy line pending wrap
    assert _pytest_command_hint(platform="linux") == ".venv/bin/python -m pytest -q"
