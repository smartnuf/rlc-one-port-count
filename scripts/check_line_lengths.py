#!/usr/bin/env python3
"""Check tracked hand-maintained text files for long source lines."""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

DEFAULT_MAX_COLUMNS = 79
REPO_ROOT = Path(__file__).resolve().parents[1]

# Keep exclusions narrow and explicit. This is generated snapshot data whose
# compact JSON representation is useful for regeneration and comparison.
EXCLUDED_PATHS = frozenset({"data/counts/small-r2-x3.json"})

INCLUDED_SUFFIXES = frozenset(
    {
        ".bash",
        ".cfg",
        ".in",
        ".ini",
        ".md",
        ".ps1",
        ".py",
        ".sh",
        ".toml",
        ".txt",
        ".yml",
        ".yaml",
    }
)
INCLUDED_NAMES = frozenset(
    {
        ".gitattributes",
        ".gitignore",
        "AGENTS.md",
        "LICENSE",
        "Makefile",
    }
)
HASH_COMMENT_SUFFIXES = frozenset(
    {
        ".bash",
        ".cfg",
        ".ini",
        ".ps1",
        ".py",
        ".sh",
        ".toml",
        ".yml",
        ".yaml",
    }
)
HASH_COMMENT_NAMES = frozenset({"Makefile"})


@dataclass(frozen=True)
class Diagnostic:
    """One line-length or suppression-directive problem."""

    path: str
    line: int
    message: str

    def format(self) -> str:
        return f"{self.path}:{self.line}: {self.message}"


@dataclass(frozen=True)
class CheckResult:
    """Immutable result returned by the importable checking API."""

    diagnostics: tuple[Diagnostic, ...]

    @property
    def ok(self) -> bool:
        return not self.diagnostics

    @property
    def affected_files(self) -> int:
        return len({diagnostic.path for diagnostic in self.diagnostics})


def is_included_path(path: str) -> bool:
    """Return whether a repository path is subject to the policy."""

    normalized = Path(path).as_posix()
    if normalized in EXCLUDED_PATHS:
        return False
    candidate = Path(normalized)
    return (
        candidate.name in INCLUDED_NAMES
        or candidate.suffix in INCLUDED_SUFFIXES
    )


def _decode_nul_paths(data: bytes) -> list[str]:
    return [
        item.decode("utf-8", errors="surrogateescape")
        for item in data.split(b"\0")
        if item
    ]


def _git_paths(
    args: Sequence[str],
    root: Path = REPO_ROOT,
) -> list[str]:
    completed = subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
    )
    return _decode_nul_paths(completed.stdout)


def tracked_files(root: Path = REPO_ROOT) -> list[str]:
    """Return included tracked paths, excluding untracked worktree files."""

    return [
        path
        for path in _git_paths(["ls-files", "-z"], root)
        if is_included_path(path)
    ]


def changed_files(root: Path = REPO_ROOT) -> list[str]:
    """Return changed tracked paths in the index and worktree.

    Deleted files and unstaged untracked files are excluded. A staged new file
    is included. Rename destinations are included when Git recognises a rename.
    """

    common = [
        "--name-only",
        "--find-renames",
        "--diff-filter=ACMRT",
        "-z",
    ]
    staged = _git_paths(["diff", "--cached", *common], root)
    unstaged = _git_paths(["diff", *common], root)
    return list(dict.fromkeys([*staged, *unstaged]))


def changed_files_between(
    base: str,
    head: str,
    root: Path = REPO_ROOT,
) -> list[str]:
    """Return non-deleted destination paths changed in a commit range."""

    return _git_paths(
        [
            "diff",
            "--name-only",
            "--find-renames",
            "--diff-filter=ACMRT",
            "-z",
            base,
            head,
        ],
        root,
    )


def _hash_comment_directive(stripped: str) -> str | None:
    if not stripped.startswith("#"):
        return None
    body = stripped[1:].strip()
    return body if body.startswith("line-length:") else None


def _markdown_comment_directive(stripped: str) -> str | None:
    prefix = "<!--"
    suffix = "-->"
    if not stripped.startswith(prefix) or not stripped.endswith(suffix):
        return None
    body = stripped[len(prefix) : -len(suffix)].strip()
    return body if body.startswith("line-length:") else None


def directive_for_line(path: str, line: str) -> str | None:
    """Return a recognised comment-only directive body, if present."""

    stripped = line.strip()
    candidate = Path(path)
    if candidate.suffix == ".md" or candidate.name == "AGENTS.md":
        return _markdown_comment_directive(stripped)
    if (
        candidate.suffix in HASH_COMMENT_SUFFIXES
        or candidate.name in HASH_COMMENT_NAMES
    ):
        return _hash_comment_directive(stripped)
    return None


def parse_directive(body: str) -> tuple[str, str | None]:
    rest = body.removeprefix("line-length:").strip()
    if "--" in rest:
        action, reason = rest.split("--", 1)
        return action.strip(), reason.strip()
    return rest.strip(), None


def check_lines(
    path: str,
    lines: Sequence[str],
    *,
    max_columns: int = DEFAULT_MAX_COLUMNS,
) -> list[Diagnostic]:
    """Check already-read lines and return deterministic diagnostics."""

    diagnostics: list[Diagnostic] = []
    disabled_at: int | None = None
    ignore_next = False

    for index, raw_line in enumerate(lines, start=1):
        line = raw_line.rstrip("\r\n")
        width = len(line.expandtabs(8))
        directive = directive_for_line(path, line)

        if directive is not None:
            action, reason = parse_directive(directive)
            if width > max_columns:
                diagnostics.append(
                    Diagnostic(
                        path,
                        index,
                        "suppression directive has "
                        f"{width} characters; maximum is {max_columns}",
                    )
                )
            if action in {"ignore-next-line", "disable"} and not reason:
                diagnostics.append(
                    Diagnostic(
                        path,
                        index,
                        f"{action} directive requires a reason",
                    )
                )
            if action == "ignore-next-line":
                if index == len(lines):
                    diagnostics.append(
                        Diagnostic(
                            path,
                            index,
                            "ignore-next-line directive at end of file",
                        )
                    )
                ignore_next = True
            elif action == "disable":
                if disabled_at is not None:
                    diagnostics.append(
                        Diagnostic(
                            path,
                            index,
                            "nested disable directive; previous "
                            f"disable at line {disabled_at}",
                        )
                    )
                else:
                    disabled_at = index
            elif action == "enable":
                if disabled_at is None:
                    diagnostics.append(
                        Diagnostic(
                            path,
                            index,
                            "enable directive without matching disable",
                        )
                    )
                else:
                    disabled_at = None
            else:
                diagnostics.append(
                    Diagnostic(
                        path,
                        index,
                        f"unknown line-length directive {action!r}",
                    )
                )
            continue

        if ignore_next:
            ignore_next = False
            continue
        if disabled_at is not None:
            continue
        if width > max_columns:
            diagnostics.append(
                Diagnostic(
                    path,
                    index,
                    f"line has {width} characters; maximum is {max_columns}",
                )
            )

    if disabled_at is not None:
        diagnostics.append(
            Diagnostic(
                path,
                disabled_at,
                "disable directive without matching enable",
            )
        )
    return diagnostics


def check_paths(
    paths: Iterable[str],
    *,
    root: Path = REPO_ROOT,
    max_columns: int = DEFAULT_MAX_COLUMNS,
) -> CheckResult:
    """Check complete current contents for all included selected paths."""

    diagnostics: list[Diagnostic] = []
    selected = sorted(
        dict.fromkeys(path for path in paths if is_included_path(path))
    )
    for path in selected:
        try:
            data = (root / path).read_text(
                encoding="utf-8"
            ).splitlines(True)
        except UnicodeDecodeError as exc:
            diagnostics.append(
                Diagnostic(path, 1, f"could not decode as UTF-8: {exc}")
            )
            continue
        except OSError as exc:
            diagnostics.append(
                Diagnostic(path, 1, f"could not read file: {exc}")
            )
            continue
        diagnostics.extend(
            check_lines(path, data, max_columns=max_columns)
        )
    return CheckResult(tuple(diagnostics))


def _selected_paths(
    args: argparse.Namespace,
    parser: argparse.ArgumentParser,
) -> list[str]:
    if args.paths:
        if args.changed or args.base or args.head:
            parser.error("paths cannot be combined with a Git selection mode")
        return args.paths
    if args.base or args.head:
        if not args.base or not args.head:
            parser.error("--base and --head must be supplied together")
        return changed_files_between(args.base, args.head)
    if args.changed:
        return changed_files()
    return tracked_files()


def _print_result(
    result: CheckResult,
    *,
    report: bool,
) -> None:
    stream = sys.stdout if report else sys.stderr
    for diagnostic in result.diagnostics:
        print(diagnostic.format(), file=stream)
    if report:
        noun = "violation" if len(result.diagnostics) == 1 else "violations"
        files = "file" if result.affected_files == 1 else "files"
        print(
            f"{len(result.diagnostics)} {noun} in "
            f"{result.affected_files} {files}.",
            file=stream,
        )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "paths",
        nargs="*",
        help="paths to check instead of selecting paths with Git",
    )
    parser.add_argument(
        "--max-columns",
        type=int,
        default=DEFAULT_MAX_COLUMNS,
    )
    parser.add_argument(
        "--changed",
        action="store_true",
        help="check staged and unstaged tracked current files",
    )
    parser.add_argument(
        "--base",
        help="base ref or SHA for an explicit comparison",
    )
    parser.add_argument(
        "--head",
        help="head ref or SHA for an explicit comparison",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="report diagnostics but return success during staged adoption",
    )
    args = parser.parse_args(argv)

    if args.max_columns < 1:
        parser.error("--max-columns must be positive")

    paths = _selected_paths(args, parser)
    result = check_paths(paths, max_columns=args.max_columns)
    _print_result(result, report=args.report)
    if args.report:
        return 0
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
