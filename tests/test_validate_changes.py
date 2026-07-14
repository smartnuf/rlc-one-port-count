from __future__ import annotations

from pathlib import Path

import pytest

import importlib.util
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
# line-length: ignore-next-line -- legacy line pending wrap
SPEC = importlib.util.spec_from_file_location("validate_changes", REPO_ROOT / "scripts" / "validate_changes.py")
validate_changes = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = validate_changes
assert SPEC.loader is not None
SPEC.loader.exec_module(validate_changes)

ChangedPath = validate_changes.ChangedPath


def policy():
    return validate_changes.load_policy()


@pytest.mark.parametrize(
    ("paths", "expected"),
    [
        ([ChangedPath("docs/results.md")], "docs"),
        ([ChangedPath("README.md")], "docs"),
# line-length: ignore-next-line -- legacy line pending wrap
        ([ChangedPath("docs/results.md"), ChangedPath("src/rice/core.py")], "code"),
        ([ChangedPath("tests/test_support_census.py")], "code"),
        ([ChangedPath("pyproject.toml")], "full"),
        ([ChangedPath(".codex/setup.sh")], "full"),
        ([ChangedPath(".github/workflows/validation.yml")], "full"),
        ([ChangedPath("validation/impact.toml")], "full"),
        ([ChangedPath("scripts/validate_changes.py")], "full"),
        ([ChangedPath("NOTES.md")], "full"),
        ([ChangedPath("docs/old.md", status="D")], "docs"),
# line-length: ignore-next-line -- legacy line pending wrap
        ([ChangedPath("docs/new.md", status="R100", old_path="docs/old.md")], "docs"),
# line-length: ignore-next-line -- legacy line pending wrap
        ([ChangedPath("docs/notes.md", status="R100", old_path="NOTES.md")], "full"),
        ([ChangedPath("README.md"), ChangedPath("Makefile")], "full"),
    ],
)
def test_classification_profiles(paths, expected):
    result = validate_changes.classify_paths(paths, policy())

    assert result.profile == expected


def test_rename_escalates_when_new_path_is_code():
    result = validate_changes.classify_paths(
# line-length: ignore-next-line -- legacy line pending wrap
        [ChangedPath("src/rice/new.py", status="R100", old_path="docs/old.md")], policy()
    )

    assert result.profile == "code"


def test_malformed_policy_fails_safely(tmp_path: Path):
    broken = tmp_path / "impact.toml"
# line-length: ignore-next-line -- legacy line pending wrap
    broken.write_text('[profiles]\norder = ["docs", "code", "full"]\n', encoding="utf-8")

    with pytest.raises(ValueError):
        validate_changes.load_policy(broken)


def test_incomplete_policy_rule_fails_safely(tmp_path: Path):
    broken = tmp_path / "impact.toml"
    broken.write_text(
# line-length: ignore-next-line -- legacy line pending wrap
        '[profiles]\norder = ["docs", "code", "full"]\ndefault = "full"\n\n[[rules]]\nprofile = "docs"\n',
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        validate_changes.load_policy(broken)


# line-length: ignore-next-line -- legacy line pending wrap
@pytest.mark.parametrize("order", [("docs", "code", "full"), ("full", "docs", "code")])
# line-length: ignore-next-line -- legacy line pending wrap
def test_validation_machinery_paths_are_full_even_if_policy_downgrades_them(order):
    bad_policy = validate_changes.Policy(
        order=order,
        default="full",
        rules=(
            validate_changes.Rule(
                profile="docs",
                reason="bad local policy edit",
                patterns=("validation/**", "scripts/**", ".github/**"),
            ),
        ),
    )

# line-length: ignore-next-line -- legacy line pending wrap
    result = validate_changes.classify_paths([ChangedPath("validation/impact.toml")], bad_policy)

    assert result.profile == "full"
    assert "hard-coded full validation" in result.reasons[0]


def write_plan_tree(root: Path, index_text: str) -> Path:
    plan = root / "docs" / "plan"
    (plan / "07-tests").mkdir(parents=True)
    (plan / "08-docs").mkdir(parents=True)
    (plan / "07-tests" / "01-ci.md").write_text("# CI\n", encoding="utf-8")
# line-length: ignore-next-line -- legacy line pending wrap
    (plan / "08-docs" / "01-readme.md").write_text("# README\n", encoding="utf-8")
    index = plan / "00-index.md"
    index.write_text(index_text, encoding="utf-8")
    return index


def test_plan_index_reports_missing_group_heading(tmp_path: Path):
    index = write_plan_tree(
        tmp_path,
        "\n".join(
            [
                "# Plan",
                "## 08 — Docs",
                "- [README](08-docs/01-readme.md)",
                "",
            ]
        ),
    )

    errors = validate_changes.plan_index_errors(index)

    assert "Plan index missing heading groups: ['07']" in errors


def test_plan_index_reports_cross_group_links(tmp_path: Path):
    index = write_plan_tree(
        tmp_path,
        "\n".join(
            [
                "# Plan",
                "## 07 — Tests",
                "- [CI](07-tests/01-ci.md)",
                "## 08 — Docs",
                "- [README](08-docs/01-readme.md)",
                "- [Wrong group](07-tests/01-ci.md)",
                "",
            ]
        ),
    )

    errors = validate_changes.plan_index_errors(index)

# line-length: ignore-next-line -- legacy line pending wrap
    assert "Plan index group 08 lists cross-group links: ['07-tests/01-ci.md']" in errors


def test_docs_profile_uses_explicit_commit_range_for_whitespace_check():
    commands = validate_changes.command_for_profile("docs", ("BASE", "HEAD"))

    assert commands[0] == ["git", "diff", "--check", "BASE", "HEAD"]
    assert commands[-1] == [
        sys.executable,
        "scripts/check_line_lengths.py",
        "--base",
        "BASE",
        "--head",
        "HEAD",
    ]


def test_docs_profile_checks_staged_and_unstaged_worktree_whitespace():
    commands = validate_changes.command_for_profile("docs", tuple())

# line-length: ignore-next-line -- legacy line pending wrap
    assert commands[:2] == [["git", "diff", "--check"], ["git", "diff", "--cached", "--check"]]
    assert commands[-1] == [
        sys.executable,
        "scripts/check_line_lengths.py",
        "--changed",
    ]
