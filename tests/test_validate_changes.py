from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
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
        ([ChangedPath("docs/results.md"), ChangedPath("src/rice/core.py")], "code"),
        ([ChangedPath("tests/test_support_census.py")], "code"),
        ([ChangedPath("pyproject.toml")], "full"),
        ([ChangedPath(".codex/setup.sh")], "full"),
        ([ChangedPath(".github/workflows/validation.yml")], "full"),
        ([ChangedPath("validation/impact.toml")], "full"),
        ([ChangedPath("scripts/validate_changes.py")], "full"),
        ([ChangedPath("NOTES.md")], "full"),
        ([ChangedPath("docs/old.md", status="D")], "docs"),
        ([ChangedPath("docs/new.md", status="R100", old_path="docs/old.md")], "docs"),
        ([ChangedPath("README.md"), ChangedPath("Makefile")], "full"),
    ],
)
def test_classification_profiles(paths, expected):
    result = validate_changes.classify_paths(paths, policy())

    assert result.profile == expected


def test_rename_escalates_when_new_path_is_code():
    result = validate_changes.classify_paths(
        [ChangedPath("src/rice/new.py", status="R100", old_path="docs/old.md")], policy()
    )

    assert result.profile == "code"


def test_malformed_policy_fails_safely(tmp_path: Path):
    broken = tmp_path / "impact.toml"
    broken.write_text('[profiles]\norder = ["docs", "code", "full"]\n', encoding="utf-8")

    with pytest.raises(ValueError):
        validate_changes.load_policy(broken)


def test_incomplete_policy_rule_fails_safely(tmp_path: Path):
    broken = tmp_path / "impact.toml"
    broken.write_text(
        '[profiles]\norder = ["docs", "code", "full"]\ndefault = "full"\n\n[[rules]]\nprofile = "docs"\n',
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        validate_changes.load_policy(broken)


def test_unclassified_old_path_in_rename_preserves_full_validation():
    result = validate_changes.classify_paths(
        [ChangedPath("docs/notes.md", status="R100", old_path="NOTES.md")], policy()
    )

    assert result.profile == "full"


def test_plan_index_check_is_included_for_mixed_plan_and_code_changes():
    result = validate_changes.classify_paths(
        [ChangedPath("docs/plan/00-index.md"), ChangedPath("src/rice/core.py")], policy()
    )

    commands = validate_changes.command_for_profile(
        result.profile,
        include_plan_index=validate_changes.has_plan_path(result.paths),
    )

    assert result.profile == "code"
    assert [sys.executable, "scripts/validate_changes.py", "--check-plan-index"] in commands


def test_docs_diff_check_uses_explicit_base_head_range():
    commands = validate_changes.command_for_profile("docs", diff_check_args=("BASE", "HEAD"))

    assert commands[0] == ["git", "diff", "--check", "BASE", "HEAD"]
