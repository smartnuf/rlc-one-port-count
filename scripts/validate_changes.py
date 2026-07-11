#!/usr/bin/env python3
"""Select and run proportionate validation for changed repository paths."""

from __future__ import annotations

import argparse
import fnmatch
import os
import platform
import re
import subprocess
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = REPO_ROOT / "validation" / "impact.toml"


@dataclass(frozen=True)
class ChangedPath:
    path: str
    status: str = "M"
    old_path: str | None = None

    def display(self) -> str:
        if self.old_path:
            return f"{self.status}\t{self.old_path} -> {self.path}"
        return f"{self.status}\t{self.path}"

    def classification_paths(self) -> tuple[str, ...]:
        if self.old_path:
            return (self.old_path, self.path)
        return (self.path,)


@dataclass(frozen=True)
class Rule:
    profile: str
    reason: str
    patterns: tuple[str, ...]


@dataclass(frozen=True)
class Policy:
    order: tuple[str, ...]
    default: str
    rules: tuple[Rule, ...]

    @property
    def rank(self) -> dict[str, int]:
        return {profile: index for index, profile in enumerate(self.order)}


@dataclass(frozen=True)
class Classification:
    profile: str
    reasons: tuple[str, ...]
    paths: tuple[ChangedPath, ...]


def load_policy(path: Path = POLICY_PATH) -> Policy:
    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
        profiles = raw["profiles"]
        order = tuple(profiles["order"])
        default = profiles["default"]
        raw_rules = raw["rules"]
    except Exception as exc:  # malformed policy must fail safely
        raise ValueError(f"could not load validation policy {path}: {exc}") from exc

    if not order or default not in order:
        raise ValueError("validation policy must define profiles.order and a default in that order")
    if set(order) != {"docs", "code", "full"}:
        raise ValueError("validation policy must define exactly docs, code, and full profiles")

    rules: list[Rule] = []
    for index, raw_rule in enumerate(raw_rules):
        try:
            profile = raw_rule["profile"]
            reason = raw_rule["reason"]
            patterns = tuple(raw_rule["patterns"])
        except Exception as exc:
            raise ValueError(f"validation policy rule {index} is incomplete: {exc}") from exc
        if profile not in order:
            raise ValueError(f"validation policy rule {index} has unknown profile {profile!r}")
        if not reason or not patterns or not all(isinstance(p, str) and p for p in patterns):
            raise ValueError(f"validation policy rule {index} must have a reason and patterns")
        rules.append(Rule(profile=profile, reason=reason, patterns=patterns))
    if not rules:
        raise ValueError("validation policy must contain at least one rule")
    return Policy(order=order, default=default, rules=tuple(rules))


def _matches(pattern: str, path: str) -> bool:
    if pattern.endswith("/**"):
        prefix = pattern[:-3]
        return path == prefix or path.startswith(prefix + "/")
    return fnmatch.fnmatchcase(path, pattern)


def classify_paths(paths: Sequence[ChangedPath], policy: Policy) -> Classification:
    rank = policy.rank
    selected = policy.order[0]
    reasons: list[str] = []

    if not paths:
        return Classification(profile="docs", reasons=("no changed paths; running lightweight checks",), paths=tuple())

    for changed in paths:
        path_profile = policy.default
        path_reason = "unclassified path; conservative full validation"
        matched_pattern = "<default>"
        for candidate in changed.classification_paths():
            for rule in policy.rules:
                pattern = next((p for p in rule.patterns if _matches(p, candidate)), None)
                if pattern is not None and rank[rule.profile] >= rank[path_profile if path_profile != policy.default else policy.order[0]]:
                    path_profile = rule.profile
                    path_reason = rule.reason
                    matched_pattern = pattern
            if path_profile == policy.default and path_reason.startswith("unclassified"):
                matched_pattern = candidate
        if rank[path_profile] > rank[selected]:
            selected = path_profile
        reasons.append(f"{changed.display()}: {path_profile} ({path_reason}; matched {matched_pattern})")

    return Classification(profile=selected, reasons=tuple(reasons), paths=tuple(paths))


def run_git(args: Sequence[str]) -> str:
    completed = subprocess.run(["git", *args], cwd=REPO_ROOT, text=True, check=True, capture_output=True)
    return completed.stdout


def changed_paths_worktree() -> list[ChangedPath]:
    output = run_git(["status", "--porcelain=v1", "--renames"])
    paths: list[ChangedPath] = []
    for line in output.splitlines():
        status = line[:2].strip() or "M"
        rest = line[3:]
        if " -> " in rest:
            old, new = rest.split(" -> ", 1)
            paths.append(ChangedPath(path=new, old_path=old, status=status))
        else:
            paths.append(ChangedPath(path=rest, status=status))
    return paths


def changed_paths_between(base: str, head: str) -> list[ChangedPath]:
    output = run_git(["diff", "--name-status", "--find-renames", base, head])
    paths: list[ChangedPath] = []
    for line in output.splitlines():
        parts = line.split("\t")
        status = parts[0]
        if status.startswith("R") and len(parts) == 3:
            paths.append(ChangedPath(path=parts[2], old_path=parts[1], status=status))
        elif len(parts) >= 2:
            paths.append(ChangedPath(path=parts[-1], status=status))
    return paths


def parse_path_specs(specs: Iterable[str]) -> list[ChangedPath]:
    paths = []
    for spec in specs:
        if "=>" in spec:
            old, new = spec.split("=>", 1)
            paths.append(ChangedPath(path=new, old_path=old, status="R"))
        else:
            paths.append(ChangedPath(path=spec, status="M"))
    return paths


def check_plan_index() -> int:
    index = REPO_ROOT / "docs" / "plan" / "00-index.md"
    text = index.read_text(encoding="utf-8")
    heading_re = re.compile(r"^## (\d{2}) — .+$", re.MULTILINE)
    headings = list(heading_re.finditer(text))
    ok = True
    for i, match in enumerate(headings):
        group = match.group(1)
        start = match.end()
        end = headings[i + 1].start() if i + 1 < len(headings) else len(text)
        section = text[start:end]
        links = sorted(re.findall(r"\]\((%s-[^/]+/[^)]+\.md)\)" % group, section))
        dirs = sorted(p.relative_to(index.parent).as_posix() for p in (index.parent).glob(f"{group}-*/*.md"))
        if links != dirs:
            ok = False
            print(f"Plan index mismatch for group {group}:", file=sys.stderr)
            print(f"  listed: {links}", file=sys.stderr)
            print(f"  actual: {dirs}", file=sys.stderr)
    if ok:
        print("Plan index structure is consistent.")
        return 0
    return 1


def whitespace_check_commands(diff_source: Sequence[str] | None = None) -> list[list[str]]:
    """Return git diff --check commands for the selected change source.

    Commit-range validation must check that exact range. Local worktree
    validation covers both unstaged and staged changes because `git status`
    reports both. Explicit --paths inputs have no associated patch, so fall
    back to the current unstaged diff for backward-compatible local use.
    """

    if diff_source is None:
        return [["git", "diff", "--check"]]
    if diff_source:
        return [["git", "diff", "--check", *diff_source]]
    return [["git", "diff", "--check"], ["git", "diff", "--cached", "--check"]]


def command_for_profile(profile: str, diff_source: Sequence[str] | None = None) -> list[list[str]]:
    py = sys.executable
    if profile == "docs":
        return [
            *whitespace_check_commands(diff_source),
            [py, str(Path("scripts") / "validate_changes.py"), "--check-plan-index"],
        ]
    if profile == "code":
        return [["bash", "scripts/lint.sh"], ["bash", "scripts/test.sh"]]
    if profile == "full":
        return [["make", "check"]]
    raise ValueError(f"unknown profile {profile}")


def run_commands(commands: Sequence[Sequence[str]]) -> int:
    for command in commands:
        print("\n==>", " ".join(command), flush=True)
        completed = subprocess.run(command, cwd=REPO_ROOT)
        if completed.returncode != 0:
            return completed.returncode
    return 0


def print_classification(classification: Classification) -> None:
    print(f"Selected validation profile: {classification.profile}")
    print("Changed paths:")
    if classification.paths:
        for path in classification.paths:
            print(f"  {path.display()}")
    else:
        print("  <none>")
    print("Reasons:")
    for reason in classification.reasons:
        print(f"  - {reason}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--worktree", action="store_true", help="validate staged and unstaged local changes")
    source.add_argument("--base", help="base ref/SHA for explicit comparison")
    parser.add_argument("--head", help="head ref/SHA for explicit comparison")
    source.add_argument("--full", action="store_true", help="force authoritative full validation")
    source.add_argument("--paths", nargs="*", help="classify explicit path specs; use old=>new for renames")
    parser.add_argument("--dry-run", action="store_true", help="print selected checks without running them")
    parser.add_argument("--check-plan-index", action="store_true", help="run only the lightweight plan-index structural check")
    args = parser.parse_args(argv)

    if args.check_plan_index:
        return check_plan_index()

    try:
        policy = load_policy()
    except ValueError as exc:
        print(f"Validation policy error: {exc}", file=sys.stderr)
        return run_commands(command_for_profile("full")) if args.full else 2

    diff_source: tuple[str, ...] | None = None
    if args.full:
        classification = Classification("full", ("forced by --full",), tuple())
    elif args.paths is not None:
        classification = classify_paths(parse_path_specs(args.paths), policy)
    elif args.base:
        if not args.head:
            parser.error("--base requires --head")
        classification = classify_paths(changed_paths_between(args.base, args.head), policy)
        diff_source = (args.base, args.head)
    else:
        classification = classify_paths(changed_paths_worktree(), policy)
        diff_source = tuple()

    print_classification(classification)
    commands = command_for_profile(classification.profile, diff_source)
    print("Checks:")
    for command in commands:
        print("  - " + " ".join(command))
    if classification.profile == "docs":
        print("Skipped: pytest and census commands are not run for documentation-only changes.")
    if args.dry_run:
        return 0
    return run_commands(commands)


if __name__ == "__main__":
    raise SystemExit(main())
