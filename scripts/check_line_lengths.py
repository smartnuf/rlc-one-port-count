#!/usr/bin/env python3
"""Check tracked hand-maintained text files for long source lines."""

from __future__ import annotations

import argparse
import fnmatch
import subprocess
from collections import Counter
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

DEFAULT_MAX_COLUMNS = 79
REPO_ROOT = Path(__file__).resolve().parents[1]

# Keep exclusions narrow and explicit. These files are generated data
# snapshots; wrapping their single-line JSON payloads would either change
# machine output or make diffs harder to compare with regenerated artefacts.
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
    path: str
    line: int
    message: str

    def format(self) -> str:
        return f"{self.path}:{self.line}: {self.message}"


@dataclass(frozen=True)
class CheckResult:
    diagnostics: tuple[Diagnostic, ...]

    @property
    def ok(self) -> bool:
        return not self.diagnostics


def is_included_path(path: str) -> bool:
    if path in EXCLUDED_PATHS:
        return False
    name = Path(path).name
    return name in INCLUDED_NAMES or Path(path).suffix in INCLUDED_SUFFIXES


def tracked_files(root: Path = REPO_ROOT) -> list[str]:
    completed = subprocess.run(
        ["git", "ls-files"],
        cwd=root,
        text=True,
        check=True,
        capture_output=True,
    )
    return [
        line
        for line in completed.stdout.splitlines()
        if is_included_path(line)
    ]


def changed_files(root: Path = REPO_ROOT) -> list[str]:
    completed = subprocess.run(
        ["git", "status", "--porcelain=v1"],
        cwd=root,
        text=True,
        check=True,
        capture_output=True,
    )
    paths: list[str] = []
    for line in completed.stdout.splitlines():
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        if path:
            paths.append(path)
    return paths


def changed_files_between(
    base: str,
    head: str,
    root: Path = REPO_ROOT,
) -> list[str]:
    completed = subprocess.run(
        ["git", "diff", "--name-status", "--find-renames", base, head],
        cwd=root,
        text=True,
        check=True,
        capture_output=True,
    )
    paths: list[str] = []
    for line in completed.stdout.splitlines():
        parts = line.split("\t")
        if not parts:
            continue
        status = parts[0]
        if status.startswith("D"):
            continue
        if status.startswith("R") and len(parts) == 3:
            paths.append(parts[2])
        elif len(parts) >= 2:
            paths.append(parts[-1])
    return paths


def _hash_comment_directive(stripped: str) -> str | None:
    if not stripped.startswith("#"):
        return None
    body = stripped[1:].strip()
    return body if body.startswith("line-length:") else None


def _markdown_comment_directive(
    stripped: str,
) -> str | None:
    prefix = "<!--"
    suffix = "-->"
    if not stripped.startswith(prefix) or not stripped.endswith(suffix):
        return None
    body = stripped[len(prefix) : -len(suffix)].strip()
    return body if body.startswith("line-length:") else None


def directive_for_line(path: str, line: str) -> str | None:
    stripped = line.strip()
    suffix = Path(path).suffix
    name = Path(path).name
    if suffix == ".md" or name == "AGENTS.md":
        return _markdown_comment_directive(stripped)
    if suffix in HASH_COMMENT_SUFFIXES or name in HASH_COMMENT_NAMES:
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


def ref_line_counts(
    path: str,
    root: Path = REPO_ROOT,
    ref: str = "HEAD",
) -> Counter[str]:
    completed = subprocess.run(
        ["git", "show", f"{ref}:{path}"],
        cwd=root,
        text=True,
        capture_output=True,
    )
    if completed.returncode != 0:
        return Counter()
    return Counter(completed.stdout.splitlines())


def check_paths(
    paths: Iterable[str],
    *,
    root: Path = REPO_ROOT,
    max_columns: int = DEFAULT_MAX_COLUMNS,
    ignore_existing: bool = False,
    existing_ref: str = "HEAD",
) -> CheckResult:
    diagnostics: list[Diagnostic] = []
    for path in sorted(p for p in paths if is_included_path(p)):
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
        path_diagnostics = check_lines(path, data, max_columns=max_columns)
        if ignore_existing:
            old_lines = ref_line_counts(path, root, existing_ref)
            kept: list[Diagnostic] = []
            current_lines = [line.rstrip("\r\n") for line in data]
            for diagnostic in path_diagnostics:
                text = current_lines[diagnostic.line - 1]
                if old_lines[text] > 0:
                    old_lines[text] -= 1
                    continue
                kept.append(diagnostic)
            path_diagnostics = kept
        diagnostics.extend(path_diagnostics)
    return CheckResult(tuple(diagnostics))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "paths",
        nargs="*",
        help="paths to check instead of git ls-files",
    )
    parser.add_argument("--max-columns", type=int, default=DEFAULT_MAX_COLUMNS)
    parser.add_argument(
        "--changed",
        action="store_true",
        help="check changed worktree paths instead of all tracked files",
    )
    parser.add_argument("--base", help="base ref/SHA for explicit comparison")
    parser.add_argument("--head", help="head ref/SHA for explicit comparison")
    args = parser.parse_args(argv)

    if args.paths:
        paths = args.paths
    elif args.base:
        if not args.head:
            parser.error("--base requires --head")
        paths = changed_files_between(args.base, args.head)
    elif args.changed:
        paths = changed_files()
    else:
        paths = tracked_files()
    result = check_paths(
        paths,
        max_columns=args.max_columns,
        ignore_existing=args.changed or bool(args.base),
        existing_ref=args.base or "HEAD",
    )
    for diagnostic in result.diagnostics:
        print(diagnostic.format(), file=sys.stderr)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
