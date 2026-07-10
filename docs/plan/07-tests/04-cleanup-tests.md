# 07-tests / 04 — Regression tests for cleanup

Status: `done`

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
- 2026-07-10: `docs/plan/02-cleanup/03-generic-x.md` landed. Test changes made:
  `tests/test_counts.py::test_generic_reactive_counts_match_reference_table`
  removed and replaced by
  `test_generic_mode_is_no_longer_supported` (asserts `count_networks(mode=
  "generic")` raises `ValueError`); `test_lc_counts_match_reference_table`
  unchanged. In `tests/test_cli.py`, the `--mo generic` literal in
  `test_abbreviated_long_options_are_rejected` was swapped to `--mo lc`
  (abbreviation-rejection coverage preserved, generic value no longer
  exists to reference), and a new
  `test_generic_mode_is_rejected_cleanly_without_traceback` test confirms
  both `rice count --mode generic` and `rice --mode generic` fail via
  argparse (exit 2, no traceback). `tests/test_public_exports.py` was left
  unchanged as instructed — generic mode was never a top-level export. The
  count-command and no-subcommand LC tests were not touched; they remain for
  `02-legacy` to remove/generalise per the bullet list above, which still
  applies unchanged now that generic-X removal has landed first.
- 2026-07-10: `docs/plan/02-cleanup/02-legacy.md` landed, removing the legacy
  multiset-bundle counter in full. Tests **deleted**: `tests/test_counts.py`
  in full (both `test_generic_mode_is_no_longer_supported` and
  `test_lc_counts_match_reference_table`); from `tests/test_cli.py`,
  `test_count_subcommand_help_shows_count_options`,
  `test_legacy_no_subcommand_count_interface_still_works`,
  `test_count_subcommand_still_works`, and
  `test_generic_mode_is_rejected_cleanly_without_traceback` (the `--mode`
  parser it exercised no longer exists at all). Tests **generalised**:
  `test_legacy_count_options_before_supports_are_rejected` →
  `test_subcommand_options_before_the_subcommand_are_rejected` (asserts the
  user-facing rule — exit 2, a `rice: error:` message, no traceback — for
  surviving `--max-r`/`--format` placed before a subcommand, rather than
  asserting on the now-deleted guard's specific error text); the `--mo
  generic`/`--mo lc` abbreviation case in `test_abbreviated_long_options_are_
  rejected` was **removed outright** (there is no longer a `--mode` option
  anywhere to abbreviate) and a `reduced --max-e 5` case was added in its
  place so all three subcommands with truncatable options are covered.
  Tests **added**: `test_bare_rice_requires_a_subcommand` and
  `test_removed_count_interface_is_rejected_cleanly` (covering `rice`,
  `rice count`, `rice count --max-r 2`, `rice --mode lc`, and
  `rice --max-r 2 --max-reactive 3`, all exit 2 with no traceback).
  `tests/test_public_exports.py` was refactored from the `LEGACY_ONLY_EXPORTS`
  `|` `SURVIVING_EXPORTS` split to a single `PUBLIC_EXPORTS` set plus a
  `REMOVED_NAMES` set (`CountResult`, `count_networks`, `Mode`,
  `fixed_assignments_by_total`) checked absent from both `__all__` and
  `hasattr`. All modern support/bundle/labeling/reduced-model tests and CLI
  markdown/JSON tests were left unchanged and still pass with their existing
  golden values (99 tests total after this round of deletions/additions).
  This item is **not** marked `done`: `docs/plan/02-cleanup/04-public-api.md`
  is still `todo` and is the final repository-wide coherence audit (help
  text, examples, imports, terminology); this file's "Confirm docs examples
  run or at least parse" task item and any tests that audit surfaces belong
  to that final pass, not yet performed.
- 2026-07-10: `docs/plan/02-cleanup/04-public-api.md` landed in the same PR
  as this final pass, completing the cleanup family. Both "Done means" items
  for this file are now satisfied:
  - **"Cleanup removes only intended behaviour"**: the full-repo `rg` sweeps
    described in `02-cleanup/04-public-api.md`'s progress notes confirm no
    remaining active reference to `count_networks`, `CountResult`, `--mode`,
    `rice count`, `legacy-count`, `legacy-generic`, or the no-subcommand
    form, and no remaining prospective wording describing an already-
    implemented stage as future work.
  - **"Test failures guide users away from removed APIs"**: exercised
    directly — `rice`, `rice count`, `rice count --max-r 2`, `rice --mode
    lc`, and `rice --max-r 2 --max-reactive 3` all fail with a normal
    argparse error (exit 2, no traceback,
    `tests/test_cli.py::test_removed_count_interface_is_rejected_cleanly`
    and `test_bare_rice_requires_a_subcommand`), and
    `tests/test_public_exports.py::test_removed_legacy_names_are_absent_
    from_exports_and_attributes` confirms `CountResult`, `count_networks`,
    `Mode`, and `fixed_assignments_by_total` are absent from both
    `rice.__all__` and `hasattr(rice, ...)`.
  - **"Confirm docs examples run or at least parse"**: every active CLI
    command in README.md, AGENTS.md, and the new `docs/python_api.md` was
    either executed directly in the repository `.venv` (all `rice --help`/
    `supports`/`bundles`/`labelings`/`reduced` invocations, both markdown and
    `--format json` forms, and every Python code example in
    `docs/python_api.md`) or is an environment-setup command
    (`make setup`, `bash .codex/setup.sh`, `python3 -m venv .venv`, pip
    install lines) whose syntax and documented role were checked by
    inspection rather than execution, consistent with not re-running
    environment bootstrapping unnecessarily. No historical/removed command
    was executed to "confirm" it — those are documented as failing by
    design and were verified to fail, not to succeed.
  - Tests **added** in this pass: `tests/test_public_api_examples.py` (8
    tests, exercising every `docs/python_api.md` example at tiny budgets).
  - Tests **updated**: `tests/test_public_exports.py`'s `PUBLIC_EXPORTS` set
    gained `SimplePrimitiveBundle` and `normalise_reduced_factor`
    (`docs/plan/02-cleanup/04-public-api.md`'s public-API decision).
  - No notebook-facing examples exist in the repository; none were added.
  - Full suite: 107 tests passing (99 before this pass + 8 new).
  - This file (`07-tests/04-cleanup-tests.md`) is now marked `done`: all of
    its "Done means" criteria are satisfied and its final post-public-audit
    verification, which was the only reason it was left open, is complete.
