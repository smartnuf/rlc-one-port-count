"""Cheap drift checks for live interface documentation."""

from pathlib import Path


ACTIVE_DOCS = (
    Path("README.md"),
    Path("AGENTS.md"),
    Path("docs/computation.md"),
    Path("docs/counting_language.md"),
    Path("docs/python_api.md"),
    Path("docs/results.md"),
    Path("docs/plan/05-slices/01-r2-x3.md"),
    Path("docs/plan/07-tests/02-golden-counts.md"),
)

REMOVED_LIVE_SYNTAX = (
    "rice supports",
    "rice bundles",
    "rice labelings",
    "rice reduced",
    "--max-reactive",
    "--max-edges",
    "no-argument `rice reduced`",
    "commands remain PR3 work",
    "no command currently enumerates",
)


def test_live_docs_do_not_reintroduce_removed_cli_syntax_or_stale_claims():
    offenders: list[str] = []
    for path in ACTIVE_DOCS:
        text = path.read_text()
        for needle in REMOVED_LIVE_SYNTAX:
            if needle in text:
                offenders.append(f"{path}: {needle}")

    assert offenders == []


def test_interface_consolidation_notes_do_not_claim_pr3_is_still_open():
# line-length: ignore-next-line -- legacy line pending wrap
    text = Path("docs/plan/10-count-language/04-interface-consolidation.md").read_text()
    assert "Left PR3 work" not in text
    assert "was subsequently completed" in text


def test_active_docs_link_core_normative_files():
# line-length: ignore-next-line -- legacy line pending wrap
    assert "[`docs/model_decisions.md`](model_decisions.md)" in Path("docs/computation.md").read_text()
# line-length: ignore-next-line -- legacy line pending wrap
    assert "[`docs/plan/05-slices/04-r3-x5.md`](plan/05-slices/04-r3-x5.md)" in Path("docs/results.md").read_text()
