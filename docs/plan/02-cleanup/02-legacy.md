# 02-cleanup / 02 — Remove legacy implementation

Status: `done`

## Goal

Remove the legacy multiset-bundle counter (`count_networks`, `CountResult`,
the `rice count` subcommand, and the no-subcommand LC compatibility form) now
that the current reduced-topology implementation is validated and generic `X`
support has already been removed.

## Sequencing

This task follows completion of `docs/plan/02-cleanup/03-generic-x.md`.
Generic-`X` removal narrowed the legacy counter to LC-only behaviour first, so
this task never has to remove `mode="generic"` handling and the legacy
counter's CLI surface in the same change — by the time this task starts,
`Mode = Literal["lc"]` and `count_networks` already rejects anything other
than `"lc"`. This task removes the rest of the legacy counter, including that
now-single-valued `mode` parameter itself.

Read `docs/plan/02-cleanup/01-review.md` in full before starting, in
particular:

- section 2 ("Legacy deletion inventory") for the exact symbols, line ranges,
  and classification (legacy-only vs. shared) of everything this task may
  touch;
- section 3 ("Shared infrastructure to preserve") for what must **not** be
  deleted;
- section 5 ("What must be preserved") for what should survive even though it
  currently lives inside legacy-adjacent code or docs;
- section 6 for the no-compatibility-shim recommendation and its rationale;
- section 8 ("Recommended deletion sequence"), step 2, for the detailed
  ordering this task should follow.

## Tasks

Do not describe this as "delete legacy source files" — the legacy counter is
not an isolated file; its symbols and CLI branches are embedded in the same
modules (`src/rice/core.py`, `src/rice/cli.py`) as the shared and
reduced-model code. Delete the specific legacy-only symbols and CLI branches,
not the modules that contain them:

- In `src/rice/core.py`, delete: `Mode`, `CountResult`,
  `fixed_assignments_by_total`, and `count_networks`.
- In `src/rice/cli.py`, delete: the `count` subparser registration, the
  `_add_count_arguments` call that attaches compatibility options to the
  top-level parser (and the function itself if nothing else uses it), the
  no-subcommand fallback branch at the bottom of `main()`, `_count_json`, and
  `--mode`/`_COUNT_OPTION_NAMES` entries that only exist for the legacy path.
  Re-evaluate whether `_reject_legacy_globals_before_supports` and
  `_LEGACY_GLOBAL_OPTION_NAMES` are still needed once `--mode` is gone (see
  01-review.md section 8, step 2, and its "Risks" note on this guard) rather
  than assuming they can be deleted outright — `--format` may still need
  protection ahead of the modern subcommands.
- Delete or migrate the legacy-only tests identified in 01-review.md section
  2 and section 7 ("Test changes expected in the later deletion PRs"):
  `tests/test_counts.py` in full, and the count-specific cases in
  `tests/test_cli.py` (`test_count_subcommand_help_shows_count_options`,
  `test_legacy_no_subcommand_count_interface_still_works`,
  `test_count_subcommand_still_works`). **Keep and generalise**
  `test_legacy_count_options_before_supports_are_rejected` and the
  abbreviation-rejection test — both also exercise the shared
  `_reject_legacy_globals_before_supports` guard and `allow_abbrev=False`
  policy that the modern subcommands rely on; adjust their literals so they
  no longer reference `--mode`/`count` by name once those are gone.
- Update or remove legacy documentation per 01-review.md section 2's table:
  the README "Current legacy results" section and no-subcommand examples,
  `AGENTS.md`'s legacy validation commands and reference totals, and
  `docs/results.md`'s legacy `lc` section (move its totals into a clearly
  labelled historical section per 01-review.md section 5, alongside the
  already-historical generic-mode totals from 03-generic-x).
- **Preserve explicitly** (do not delete, do not assume deletable merely
  because they live near legacy code): every symbol listed in
  01-review.md section 3's shared-infrastructure table —
  `generate_connected_unlabelled_simple_graphs`, `automorphisms`,
  `simple_path_edge_cover`, `is_two_terminal_relevant`,
  `terminal_pair_orbit_representatives`,
  `relevant_terminal_pair_orbit_representatives`,
  `edge_permutations_preserving_terminal_set`, `permutation_cycle_lengths`,
  and `iter_two_terminal_supports` (the last of these has a docstring that
  reads as legacy-only; it is not — see the note below) — plus all of
  `support_census`, the phase-2/3 bundle-assignment and labeling census APIs,
  and the reduced-signature/reduced-census APIs, none of which depend on
  `Mode`, `CountResult`, or `count_networks`.
- While touching `iter_two_terminal_supports`, correct its docstring (currently
  "Yield terminal-relevant support representatives for legacy counting.") to
  reflect that it is the shared enumeration entry point for phases 2+ and the
  (now removed) legacy counter, since the misleading label would otherwise
  persist after the legacy counter it references is gone.
- **Atomically update the public export surface with the deletion** — this is
  not deferred to `04-public-api.md`. In the same change that deletes
  `CountResult` and `count_networks` from `src/rice/core.py`:
  - remove them from the `from .core import (...)` list and `__all__` in
    `src/rice/__init__.py`;
  - update `tests/test_public_exports.py` so `LEGACY_ONLY_EXPORTS` becomes
    empty (or is removed) and `SURVIVING_EXPORTS` is the sole reference set,
    so the export-surface test never has a commit where it is inconsistent
    with the actual exports.
- Run the full test suite and the complete `make check` sequence.

## Done means

- No dead legacy implementation remains: `Mode`, `CountResult`,
  `count_networks`, `fixed_assignments_by_total`, the `count` subcommand, and
  the no-subcommand compatibility form are gone from source, CLI, exports,
  and `__all__`.
- All shared graph/support/reduced-model machinery listed above is intact and
  passes its existing tests unchanged.
- Tests confirm the supported implementation (`supports`, `bundles`,
  `labelings`, `reduced`) still works exactly as before.
- `tests/test_public_exports.py` reflects the post-deletion export surface in
  the same commit as the deletion, not a later one.
- Documentation no longer points users to removed code, and any historical
  legacy totals are clearly labelled as historical rather than active.
- `rice count ...`, `rice --mode lc ...`, and `from rice import count_networks`
  now fail with a normal, non-traceback error appropriate to a removed
  feature (see `01-review.md` section 7's "commands that should fail after
  deletion" list, adjusted at implementation time for whatever
  compatibility-shim decision, if any, is made per section 6).

## Progress notes

- 2026-07-10: Implemented, no compatibility shim (per section 6's
  recommendation and this task's explicit instruction not to retain one).
  **Source**: deleted `Mode`, `CountResult`, `fixed_assignments_by_total`, and
  `count_networks` from `src/rice/core.py`; updated the module docstring to
  describe the current reduced-model pipeline instead of the removed counter,
  and corrected `iter_two_terminal_supports`'s docstring (it no longer says
  "for legacy counting"; it now states its shared role across
  `simple_bundle_labeling_census` and `iter_reduced_topology_signatures`). No
  imports became unused (`Literal`, `DefaultDict`, `Counter`, `combinations`,
  `permutations` are all still used elsewhere in the module — confirmed with
  `rg` before deleting anything).
  **CLI**: deleted the `count` subparser, `_add_count_arguments`, the hidden
  top-level compatibility arguments, `--mode`, `_count_json`, and the
  no-subcommand fallback branch in `main()`. `add_subparsers(...,
  required=True)` now makes a bare `rice` fail with a normal argparse
  "the following arguments are required: command" error instead of falling
  through to a dispatch branch. **The pre-subcommand guard
  (`_reject_legacy_globals_before_supports`, `_LEGACY_GLOBAL_OPTION_NAMES`,
  `_COUNT_OPTION_NAMES`, `_option_name`) was deleted outright**, not adapted:
  empirically, `rice --max-r 3 supports` and `rice --format json reduced` now
  fail cleanly through ordinary argparse (`invalid choice` on the `command`
  positional, exit 2, no traceback) once the hidden top-level options that
  the guard existed to protect against no longer exist. `RiceArgumentParser`
  and `allow_abbrev=False` are unchanged.
  **Exports**: removed `CountResult` and `count_networks` from both the
  import list and `__all__` in `src/rice/__init__.py` in this same commit.
  **Makefile/scripts**: removed `legacy-count` from `.PHONY` and as a target;
  added a `reduced` target/`.PHONY` entry; replaced the `--mode lc` line in
  `scripts/check.sh` and `scripts/check.ps1` with
  `rice reduced --max-r 2 --max-reactive 3`.
  **Tests**: deleted `tests/test_counts.py` in full; removed
  `test_count_subcommand_help_shows_count_options`,
  `test_legacy_no_subcommand_count_interface_still_works`, and
  `test_count_subcommand_still_works` from `tests/test_cli.py`; replaced
  `test_legacy_count_options_before_supports_are_rejected` with
  `test_subcommand_options_before_the_subcommand_are_rejected` (generalised
  to describe the user-facing rule, not the removed guard implementation);
  removed the `--mode`-based abbreviation case and added a `reduced --max-e 5`
  case to `test_abbreviated_long_options_are_rejected`; added
  `test_bare_rice_requires_a_subcommand` and
  `test_removed_count_interface_is_rejected_cleanly` (covering `rice`,
  `rice count`, `rice count --max-r 2`, `rice --mode lc`, and
  `rice --max-r 2 --max-reactive 3`); refactored
  `tests/test_public_exports.py` to a single `PUBLIC_EXPORTS` set plus a
  `REMOVED_NAMES` check (`CountResult`, `count_networks`, `Mode`,
  `fixed_assignments_by_total`) asserting both absence from `__all__` and
  `hasattr`.
  **Docs**: README.md's "Current legacy results" section replaced with a
  "Migration from the removed legacy counter" note (closest replacement is
  `rice reduced`; counts are not numerically equivalent; `R||R` is not
  generated separately); all active `rice count`/`--mode`/no-subcommand/
  `legacy-count` examples removed from README.md and AGENTS.md;
  `docs/results.md`'s `lc` and `generic` tables consolidated under one
  "Historical legacy multiset-bundle counts" heading stating the
  implementation and commands are removed; `docs/computation.md`,
  `docs/model_decisions.md`, and `docs/bundles_and_multiedges.md` had their
  legacy-model sections retitled "Historical: ... (removed)" and rewritten to
  past tense, while keeping the `R||R`/primitive-duplicate-merging rationale
  intact; `docs/bundles_and_multiedges.md`'s "Current implementation status"
  section and an internally-contradictory "not yet implemented" line about
  series spans were corrected to reflect that `rice reduced` now implements
  full signature enumeration and merging for the golden slice.
  **Validation**: `bash .codex/setup.sh`, `make test` (99 passed), `make
  lint`, `make check` (including the new `rice reduced` final stage), `git
  diff --check`, `make supports`/`bundles`/`labelings`/`reduced` individually,
  all `--help` outputs, all surviving commands, and all explicitly-required
  removed-command failure cases (`rice`, `rice count`, `rice count --max-r 2`,
  `rice --mode lc`, `rice --max-r 2 --max-reactive 3`) all ran as expected.
  `scripts/check.ps1` was inspected line-by-line for exact stage parity with
  `scripts/check.sh` but not executed — no `pwsh`/Windows environment was
  available in this session. Next cleanup task:
  `docs/plan/02-cleanup/04-public-api.md`.
