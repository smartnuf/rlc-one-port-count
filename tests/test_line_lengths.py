from __future__ import annotations

import subprocess
from pathlib import Path

from scripts.check_line_lengths import (
    DEFAULT_MAX_COLUMNS,
    changed_files,
    changed_files_between,
    check_lines,
    check_paths,
    is_included_path,
    main,
    tracked_files,
)


def messages(path: str, lines: list[str]) -> list[str]:
    return [
        diagnostic.format()
        for diagnostic in check_lines(path, lines)
    ]


def git(cwd: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=cwd,
        text=True,
        check=True,
        capture_output=True,
    )
    return completed.stdout.strip()


def init_repo(path: Path) -> None:
    git(path, "init")
    git(path, "config", "user.email", "test@example.com")
    git(path, "config", "user.name", "Test User")


def test_exactly_79_characters_passes() -> None:
    assert messages("example.py", ["x" * DEFAULT_MAX_COLUMNS]) == []


def test_ordinary_overlong_line_reports_diagnostic() -> None:
    assert messages("example.py", ["x" * 80]) == [
        "example.py:1: line has 80 characters; maximum is 79"
    ]


def test_tabs_expand_to_eight_column_stops() -> None:
    assert messages("example.py", ["x" * 72 + "\t"]) == [
        "example.py:1: line has 80 characters; maximum is 79"
    ]


def test_hash_comment_ignore_next_line() -> None:
    lines = [
        "# line-length: ignore-next-line -- exact generated output\n",
        "x" * 100 + "\n",
    ]
    assert messages("example.py", lines) == []


def test_markdown_comment_ignore_next_line() -> None:
    lines = [
        "<!-- line-length: ignore-next-line -- exact URL -->\n",
        "x" * 100 + "\n",
    ]
    assert messages("README.md", lines) == []


def test_paired_disable_and_enable() -> None:
    lines = [
        "# line-length: disable -- compact table fixture\n",
        "x" * 100 + "\n",
        "# line-length: enable\n",
    ]
    assert messages("example.py", lines) == []


def test_missing_reasons_are_errors() -> None:
    assert messages(
        "example.py",
        ["# line-length: ignore-next-line\n", "ok\n"],
    ) == [
        "example.py:1: ignore-next-line directive requires a reason"
    ]
    assert messages(
        "example.py",
        [
            "# line-length: disable\n",
            "# line-length: enable\n",
        ],
    ) == [
        "example.py:1: disable directive requires a reason"
    ]


def test_unmatched_and_nested_directives() -> None:
    assert messages(
        "example.py",
        ["# line-length: enable\n"],
    ) == [
        "example.py:1: enable directive without matching disable"
    ]
    assert messages(
        "example.py",
        [
            "# line-length: disable -- first\n",
            "# line-length: disable -- second\n",
            "# line-length: enable\n",
        ],
    ) == [
        "example.py:2: nested disable directive; "
        "previous disable at line 1"
    ]
    assert messages(
        "example.py",
        ["# line-length: disable -- open\n"],
    ) == [
        "example.py:1: disable directive without matching enable"
    ]


def test_ignore_next_line_at_end_of_file_is_error() -> None:
    assert messages(
        "example.py",
        [
            "# line-length: ignore-next-line -- no next line\n",
        ],
    ) == [
        "example.py:1: ignore-next-line directive at end of file"
    ]


def test_directive_token_outside_comment_is_ignored() -> None:
    line = (
        "print('line-length: ignore-next-line -- not a comment')"
        + "x" * 40
    )
    assert messages("example.py", [line]) == [
        "example.py:1: line has 95 characters; maximum is 79"
    ]


def test_path_inclusion_and_deliberate_exclusion(
    tmp_path: Path,
) -> None:
    assert is_included_path("docs/example.md")
    assert is_included_path("scripts/example.sh")
    assert not is_included_path(
        "data/counts/small-r2-x3.json"
    )

    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/example.md").write_text(
        "x" * 80,
        encoding="utf-8",
    )
    (tmp_path / "data/counts").mkdir(parents=True)
    snapshot = tmp_path / "data/counts/small-r2-x3.json"
    snapshot.write_text("x" * 80, encoding="utf-8")

    result = check_paths(
        [
            "docs/example.md",
            "data/counts/small-r2-x3.json",
        ],
        root=tmp_path,
    )
    assert [item.format() for item in result.diagnostics] == [
        "docs/example.md:1: line has 80 characters; maximum is 79"
    ]


def test_tracked_files_ignore_untracked_report(
    tmp_path: Path,
) -> None:
    init_repo(tmp_path)
    (tmp_path / "tracked.py").write_text(
        "ok = 1\n",
        encoding="utf-8",
    )
    git(tmp_path, "add", "tracked.py")
    git(tmp_path, "commit", "-m", "base")
    (tmp_path / "selection.txt").write_text(
        "x" * 120,
        encoding="utf-8",
    )

    assert tracked_files(tmp_path) == ["tracked.py"]
    assert check_paths(
        tracked_files(tmp_path),
        root=tmp_path,
    ).ok


def test_default_check_fails_for_tracked_overlong_file(
    tmp_path: Path,
) -> None:
    init_repo(tmp_path)
    (tmp_path / "tracked.py").write_text(
        "x" * 80 + "\n",
        encoding="utf-8",
    )
    git(tmp_path, "add", "tracked.py")
    git(tmp_path, "commit", "-m", "base")

    result = check_paths(
        tracked_files(tmp_path),
        root=tmp_path,
    )
    assert not result.ok
    assert result.diagnostics[0].path == "tracked.py"


def test_range_skips_deletion_and_uses_rename_destination(
    tmp_path: Path,
) -> None:
    init_repo(tmp_path)
    (tmp_path / "deleted.md").write_text(
        "short\n",
        encoding="utf-8",
    )
    (tmp_path / "old.md").write_text(
        "short\n",
        encoding="utf-8",
    )
    git(tmp_path, "add", "deleted.md", "old.md")
    git(tmp_path, "commit", "-m", "base")
    base = git(tmp_path, "rev-parse", "HEAD")

    (tmp_path / "deleted.md").unlink()
    git(tmp_path, "mv", "old.md", "new.md")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-m", "head")
    head = git(tmp_path, "rev-parse", "HEAD")

    assert changed_files_between(
        base,
        head,
        tmp_path,
    ) == ["new.md"]


def test_local_changes_exclude_deleted_and_untracked(
    tmp_path: Path,
) -> None:
    init_repo(tmp_path)
    for name in ["deleted.md", "renamed.md", "modified.md"]:
        (tmp_path / name).write_text(
            "short\n",
            encoding="utf-8",
        )
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-m", "base")

    (tmp_path / "deleted.md").unlink()
    git(tmp_path, "mv", "renamed.md", "rename dest.md")
    (tmp_path / "modified.md").write_text(
        "changed\n",
        encoding="utf-8",
    )
    (tmp_path / "staged new.md").write_text(
        "new\n",
        encoding="utf-8",
    )
    git(
        tmp_path,
        "add",
        "deleted.md",
        "rename dest.md",
        "staged new.md",
    )
    (tmp_path / "selection.txt").write_text(
        "x" * 120,
        encoding="utf-8",
    )

    assert changed_files(tmp_path) == [
        "rename dest.md",
        "staged new.md",
        "modified.md",
    ]


def test_complete_selected_file_reports_unmatched_disable(
    tmp_path: Path,
) -> None:
    path = tmp_path / "example.py"
    path.write_text(
        "# line-length: disable -- generated table\n"
        "x = 1\n",
        encoding="utf-8",
    )
    result = check_paths([str(path)], root=tmp_path)
    assert result.diagnostics[0].message == (
        "disable directive without matching enable"
    )


def test_report_mode_does_not_fail_adoption(
    tmp_path: Path,
    capsys,
) -> None:
    path = tmp_path / "example.py"
    path.write_text("x" * 80 + "\n", encoding="utf-8")

    assert main([str(path), "--report"]) == 0
    output = capsys.readouterr().out
    assert "line has 80 characters" in output
    assert "1 violation in 1 file." in output


def test_check_mode_fails_the_same_input(
    tmp_path: Path,
    capsys,
) -> None:
    path = tmp_path / "example.py"
    path.write_text("x" * 80 + "\n", encoding="utf-8")

    assert main([str(path)]) == 1
    assert "line has 80 characters" in capsys.readouterr().err
