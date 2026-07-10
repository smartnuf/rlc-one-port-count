# 07-tests / 04 — Regression tests for cleanup

Status: `todo`

## Goal

Ensure removing legacy implementation and generic `X` support does not silently break intended behaviour.

## Tasks

- Preserve tests for still-supported R/L/C behaviour.
- Remove tests that only assert deleted behaviour.
- Add tests for clear failure on removed syntax where useful.
- Confirm docs examples run or at least parse.

## Done means

- Cleanup removes only intended behaviour.
- Test failures guide users away from removed APIs.


## Progress notes

- 2026-07-10: Added CLI regression coverage for disabled long-option
  abbreviations, support-limit validation, clean argparse failures, and the
  zero-budget bundle/labeling census contract.
- 2026-07-10: `docs/plan/02-cleanup/01-review.md` (review task) added
  `tests/test_public_exports.py`, pinning `rice.__all__` split into
  `LEGACY_ONLY_EXPORTS = {"CountResult", "count_networks"}` versus the 19
  surviving reduced-model exports. That review's section 7 records the
  concrete test changes this task should carry out once 02-legacy and
  03-generic-x land:
  - remove `tests/test_counts.py` in full;
  - remove the count-specific cases from `tests/test_cli.py`
    (`test_count_subcommand_help_shows_count_options`,
    `test_legacy_no_subcommand_count_interface_still_works`,
    `test_count_subcommand_still_works`) but **keep and generalise**
    `test_legacy_count_options_before_supports_are_rejected` and the
    `--mo generic` abbreviation case (swap the literal, do not delete —
    both also exercise the shared pre-subcommand-guard and
    `allow_abbrev=False` behaviour that the modern subcommands rely on);
  - update `tests/test_public_exports.py`'s `LEGACY_ONLY_EXPORTS`/
    `SURVIVING_EXPORTS` sets so `LEGACY_ONLY_EXPORTS` becomes empty;
  - after deletion, confirm `rice count`, `rice --mode lc`,
    `rice --mode generic`, the no-subcommand form, and
    `from rice import count_networks, CountResult` all fail with a clear
    error (not a traceback), and that `rice supports`/`bundles`/`labelings`/
    `reduced` and their exports are unchanged.
