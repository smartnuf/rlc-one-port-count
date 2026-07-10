# 02-cleanup / 03 — Remove generic `X` implementation, tests, validation commands, and active documentation

Status: `done`

## Goal

Remove support for treating all reactive elements as a single generic
component type `X`, while temporarily retaining the legacy LC counter (`rice
count`, the no-subcommand LC form, `CountResult`, `count_networks`) until
`docs/plan/02-cleanup/02-legacy.md`.

The review in `docs/plan/02-cleanup/01-review.md` (section 4, "Generic `X`
inventory") is the evidence base for this task. It recommended removing
generic `X` support before removing the wider legacy counter, so that no
intermediate state has `mode="generic"` implemented without matching CLI
support, or CLI support without an implementation. This task follows that
recommendation.

## Not generic-`X` support

Be precise: do not remove every letter `X` or every variable named `x`.

- The **generic component type `X`** — an undifferentiated reactive element
  that stood in for "either L or C, uncounted separately" — is in scope for
  removal.
- The **budget/table coordinate `x = l + c`** — used as a local variable name,
  a table column index, or a markdown heading aggregate (`R \ L+C`, `x` in
  `reduced_topology_census`, `x` in `CountResult.table[r][x]`) — is **not**
  generic-element support and must not be touched by this task. It remains
  wherever it is currently useful in the reduced-model and legacy-`lc` code.

## Implementation checklist

This is the concrete checklist carried over from `01-review.md`'s recommended
deletion sequence (section 8, step 1), not a discovery-only list.

### Source (`src/rice/core.py`)

- [x] Change `Mode` to permit only `"lc"` (`Mode = Literal["lc"]`).
- [x] Keep the public `mode` parameter on `count_networks` temporarily; make
      `count_networks(..., mode="generic")` (or any non-`"lc"` value) raise a
      clear `ValueError` naming `"lc"` as the only supported mode.
- [x] Remove the generic dynamic-programming branch from
      `fixed_assignments_by_total`, and remove the now-redundant `mode`
      parameter from that internal helper and from its cache key in
      `count_networks`.
- [x] Update `CountResult`'s docstring so it describes only LC behaviour and
      records that `mode`/`"generic"` is retained only as a legacy artifact
      pending full removal.
- [x] Change the legacy live markdown table heading from `"R \\ X"` to
      `"R \\ L+C"` (`CountResult.as_markdown_table`).
- [x] Leave all support enumeration, automorphism, relevance, simple-bundle,
      labeling, reduction, signature, and reduced-census algorithms
      unchanged.

### CLI (`src/rice/cli.py`)

- [x] Retain `--mode`, but restrict `choices` to `("lc",)`.
- [x] Remove help text that advertises generic reactive elements.
- [x] Remove the conditional `reactive_label = "L+C" if mode == "lc" else "X"`
      output logic; the surviving legacy output unconditionally says `L+C`.
- [x] Confirm `rice count --mode generic ...` and `rice --mode generic ...`
      both fail through argparse with exit status 2 and no traceback.
- [x] Preserve `allow_abbrev=False` and the existing protection against
      options being silently accepted in the wrong position
      (`_reject_legacy_globals_before_supports`).
- [x] Do not remove `count` or the no-subcommand LC path in this task.

### Makefile and check scripts

- [x] Remove `legacy-generic` from `.PHONY` and delete the `legacy-generic`
      Make target.
- [x] Remove the generic invocation from `scripts/check.sh`.
- [x] Remove the equivalent generic invocation from `scripts/check.ps1`.
- [x] Retain the `legacy-count` / `legacy lc count` targets and invocations.
- [x] Keep the Bash, Make, and PowerShell validation sequences equivalent.

### Tests

- [x] Remove `test_generic_reactive_counts_match_reference_table`.
- [x] Preserve `test_lc_counts_match_reference_table`.
- [x] Add an API test confirming `count_networks(mode="generic")` raises a
      clear `ValueError`
      (`tests/test_counts.py::test_generic_mode_is_no_longer_supported`).
- [x] In `test_abbreviated_long_options_are_rejected`, replace the
      `--mo generic` case with an LC-only case (`--mo lc`) that continues to
      exercise disabled-abbreviation coverage.
- [x] Add CLI regression coverage showing `rice count --mode generic` and
      `rice --mode generic` both fail cleanly without a traceback
      (`tests/test_cli.py::test_generic_mode_is_rejected_cleanly_without_traceback`).
- [x] Do not change the expected top-level export set in
      `tests/test_public_exports.py`; generic mode was never a top-level
      export.
- [x] Do not delete the count-command and no-subcommand LC tests.
- [x] Do not weaken any modern reduced-model tests or golden values.

### Documentation

- [x] Audit `README.md`, `AGENTS.md`, `docs/results.md`, `docs/computation.md`,
      `docs/model_decisions.md`, `docs/bundles_and_multiedges.md`, and
      relevant plan records.
- [x] Remove active `--mode generic` examples, `legacy-generic` instructions,
      claims that generic mode is currently supported, generic-mode
      regeneration commands, and generic-mode regression-test language.
- [x] Preserve the historical totals `57,945` and `51,736` only under an
      explicit "historical"/"removed" label in `docs/results.md`, with no
      live regeneration command and no active validation-contract role.
- [x] `docs/computation.md`, `docs/model_decisions.md`, and
      `docs/bundles_and_multiedges.md` were audited and contained no
      generic-mode references to begin with (they only ever contrasted the
      legacy `lc` bundle model against the reduced model); no changes were
      needed in those three files.

## Done means

- Generic `X` is absent from the public API, CLI help, active documentation,
  and the active validation contract (tests, scripts, Make targets).
- `rice count --mode generic ...` and `rice --mode generic ...` fail with a
  normal argparse error (exit status 2), not a traceback.
- `count_networks(mode="generic")` fails with a clear `ValueError`, not a
  traceback, when called directly as an API.
- The legacy `lc` counter (`rice count`, the no-subcommand form,
  `CountResult`, `count_networks`) and the modern `supports`/`bundles`/
  `labelings`/`reduced` paths are unchanged in behaviour.
- Historical generic-mode totals remain only as clearly labelled historical
  data in `docs/results.md`.
- Tests, scripts, Makefile, and documentation agree with the implementation.

## Progress notes

- 2026-07-10: Implemented. `Mode` narrowed to `Literal["lc"]`;
  `fixed_assignments_by_total` lost its `mode` parameter and generic DP
  branch; `count_networks` now raises `ValueError` for any non-`"lc"` mode;
  `CountResult.as_markdown_table` heading changed to `R \ L+C`. CLI `--mode`
  choices narrowed to `("lc",)` with updated help text; the conditional
  `X`/`L+C` output label removed in favour of an unconditional `L+C`.
  `legacy-generic` removed from `Makefile`, `scripts/check.sh`, and
  `scripts/check.ps1`. `tests/test_counts.py`'s generic golden test replaced
  by a `ValueError` regression test; `tests/test_cli.py` gained a clean
  no-traceback regression test for `--mode generic` and had its abbreviation
  test's literal swapped from `generic` to `lc`. README/AGENTS.md/
  `docs/results.md` updated to remove active generic examples/instructions
  and to relabel the historical `57,945`/`51,736` totals as results of a
  removed implementation. Validated with `make test`, `make lint`,
  `make check`, `git diff --check`, and the full set of CLI commands listed
  in this task's parent prompt; all passed. Next cleanup task:
  `docs/plan/02-cleanup/02-legacy.md`.
