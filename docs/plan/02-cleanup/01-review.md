# 02-cleanup / 01 — Review current implementation before deletion

Status: `done`

## Goal

Understand what exists before removing legacy code or generic `X` support.

## Tasks

- Identify the current intended implementation.
- Identify legacy modules, tests, examples, and docs.
- Identify all uses of the generic `X` element.
- Record anything worth preserving before deletion.
- Decide whether any compatibility shim is needed.

## Done means

- There is a short review note listing what will be deleted and what will replace it.
- The planned deletions are low-risk and test-backed.

## Scope of this review

This task is analysis and risk-reduction only. No API, CLI, test, script, or
documentation behaviour was deleted, renamed, deprecated, or changed in this
task. `rice count`, the no-subcommand `count` form, `--mode lc`, `--mode
generic`, `count_networks`, `CountResult`, and generic `X` behaviour are all
still present, unchanged, and still validated by `make check` /
`scripts/check.sh` / `scripts/check.ps1`. One characterisation test file was
added (see "Test and validation coverage" below) because it closed a concrete,
currently untested boundary that the later deletion tasks depend on; nothing
existing was modified to make it pass.

All findings below are evidence-backed against the current tree (commit
`94f4346`, branch `main`) as of 2026-07-10, primarily `src/rice/core.py`,
`src/rice/cli.py`, `src/rice/__init__.py`, `tests/`, `Makefile`,
`scripts/check.sh`, `scripts/check.ps1`, `README.md`, `AGENTS.md`, and
`docs/*.md`.

## 1. Current intended implementation

The reduced-topology model is the surviving implementation. It **replaces**
the legacy multiset-bundle counter; it does not wrap it, and its final stage
(`rice reduced`) does not call `count_networks` or any legacy-only helper.
The staged pipeline, all implemented in `src/rice/core.py` and exposed
through `src/rice/cli.py`:

| Stage | Core API | CLI | Purpose |
|---|---|---|---|
| 1. Support-graph census | `support_census`, `SupportCensusResult`, `generate_connected_unlabelled_simple_graphs`, `automorphisms`, `is_two_terminal_relevant`, `terminal_pair_orbit_representatives`, `relevant_terminal_pair_orbit_representatives` | `rice supports` | Enumerate connected unlabelled simple support graphs, unordered terminal-pair orbits, and terminal-relevant two-terminal supports (`docs/support_graph_enumeration.md`). |
| 2. Simple primitive bundle assignment | `SIMPLE_PRIMITIVE_BUNDLES`, `SimplePrimitiveBundle`, `simple_bundle_assignment_count_by_edge_count`, `simple_bundle_assignment_census`, `BundleAssignmentCensusResult` | `rice bundles` | Assign only the seven simple primitive bundles (`R`, `L`, `C`, `R\|\|L`, `R\|\|C`, `L\|\|C`, `R\|\|L\|\|C`) to terminal-relevant support edges; raw leaves, no quotienting. |
| 3. Assigned-support labeling orbits | `simple_bundle_labeling_orbit_count`, `simple_bundle_labeling_census`, `BundleLabelingCensusResult`, `edge_permutations_preserving_terminal_set`, `permutation_cycle_lengths` | `rice labelings` | Quotient phase-2 assignments by support automorphisms that preserve the unordered terminal pair (including terminal reversal), via Burnside's lemma. |
| 4. Local reduction / canonical signatures | `ReducedFactor`, `ReducedSignature`, `primitive_factor`, `normalise_series_factor`, `normalise_parallel_factor`, `normalise_reduced_factor`, `factor_from_simple_primitive_bundle`, `canonical_reduced_signature`, `reduced_signature_component_counts` | (library only; used by `rice reduced`) | Local series/parallel reduction and canonical signatures for one assigned two-terminal network (`docs/model_decisions.md`, `docs/bundles_and_multiedges.md`). |
| 5. End-to-end reduced-topology census | `iter_reduced_topology_signatures`, `reduced_topology_census`, `ReducedTopologyCensusResult` | `rice reduced` | Full census over a budget slice: enumerate supports, assign budgeted bundles, canonicalise, deduplicate by signature. Default/golden slice `R<=2, L+C<=3` (`data/counts/small-r2-x3.json`, `docs/counts/small-r2-x3.md`). |

Supporting exports and artefacts that belong to this surviving path: all of
the above symbols exported from `rice/__init__.py`; tests
`test_support_census.py`, `test_bundle_census.py`, `test_bundle_labelings.py`,
`test_reduced_signatures.py`, `test_reduced_census.py`, and the `supports` /
`bundles` / `labelings` / `reduced` sections of `test_cli.py`; the data file
`data/counts/small-r2-x3.json` and its human-readable twin
`docs/counts/small-r2-x3.md`; and the normative docs `docs/model_decisions.md`,
`docs/support_graph_enumeration.md`, `docs/bundles_and_multiedges.md`,
`docs/simple_path_coverage.md`, `docs/computation.md`, and the non-legacy
sections of `docs/results.md`.

Confirmed by running the full suite (see "Validation performed" below):
`rice supports --max-edges 8` reproduces the 358/4,923/383 table;
`rice bundles --max-r 3 --max-reactive 5` reproduces the 1,166,714 leaf total;
`rice labelings --max-r 3 --max-reactive 5` reproduces the 830,094 orbit
total; `rice reduced` (default slice) reproduces the 313 golden total.

## 2. Legacy deletion inventory

"Legacy-only" below means the item exists solely to support
`count_networks`/`CountResult`/generic-`X` and has no reduced-model caller.
"Shared" means the reduced-model path also calls it — do not delete it in the
legacy-removal task without first re-homing/renaming it. See section 3 for the
detailed shared-infrastructure list; this table only flags the shared items,
it does not repeat their full rationale.

| Item | Where | Used by | Legacy-only or shared? | Replacement | Cleanup task |
|---|---|---|---|---|---|
| `Mode` type alias | `src/rice/core.py:29` | `count_networks`, `fixed_assignments_by_total`, `CountResult.mode` | Legacy-only | none needed (reduced model has no mode concept) | 02-legacy |
| `CountResult` dataclass | `src/rice/core.py:449-490` | `count_networks`, CLI no-subcommand/`count` output, `_count_json` | Legacy-only | `ReducedTopologyCensusResult` (already implemented) | 02-legacy |
| `fixed_assignments_by_total` | `src/rice/core.py:671-728` | `count_networks` only | Legacy-only (has its own `mode` branching, including the generic DP; distinct from phase-2/3 helpers which take no `mode`) | `_fixed_simple_bundle_labelings_for_cycles` (already implemented, phase-3) | 02-legacy (and 03-generic-x for the `mode=="generic"` branch specifically, see section 4) |
| `count_networks` | `src/rice/core.py:1113-1162` | CLI `count` subcommand and no-subcommand fallback; `tests/test_counts.py`; `docs/results.md` legacy tables | Legacy-only | `reduced_topology_census` (already implemented) | 02-legacy |
| `rice count` subcommand | `src/rice/cli.py:51-54`, `393-573` fallthrough | end users, `Makefile` `legacy-count`/`legacy-generic`, `scripts/check.sh`/`.ps1` | Legacy-only CLI surface (dispatch logic in `main()` shared only in the sense that it is the same `if/elif` chain as the other subcommands — the branch itself is legacy-only) | `rice reduced` | 02-legacy |
| No-subcommand compatibility path | `src/rice/cli.py:173-176` (`_add_count_arguments` on the top-level parser), `393-573` fallthrough when `args.command` is `None` | `tests/test_cli.py::test_legacy_no_subcommand_count_interface_still_works`; README "legacy no-subcommand count form" section | Legacy-only | none (drop entirely, or keep as a deliberate compatibility shim — see section 6) | 02-legacy |
| `_count_json` | `src/rice/cli.py:293-298` | `count`/no-subcommand JSON output only | Legacy-only | `_reduced_topology_census_json` (already implemented) | 02-legacy |
| `_COUNT_OPTION_NAMES`, `_LEGACY_GLOBAL_OPTION_NAMES`, `_reject_legacy_globals_before_supports` | `src/rice/cli.py:28-29, 305-326` | guards against stray legacy globals before subcommands | Legacy-only guard logic, but it also protects the *modern* subcommands (`supports`/`bundles`/`labelings`/`reduced`) from silently swallowed legacy options | Mixed — see note below | 02-legacy, with care (see section 3) |
| `CountResult`/`count_networks` markdown/JSON formatting in `main()` | `src/rice/cli.py:550-573` | count/no-subcommand path only | Legacy-only | reduced/labelings formatting blocks (already implemented) | 02-legacy |
| `rice.__init__` exports `CountResult`, `count_networks` | `src/rice/__init__.py` | package consumers | Legacy-only | none (remove from `__all__` and the import) | 02-legacy / 04-public-api |
| `tests/test_counts.py` (both tests) | whole file | legacy `lc`/`generic` golden tables | Legacy-only | already superseded by `test_reduced_census.py` for the golden-slice pattern | 02-legacy (delete or explicitly retitle as historical, see section 5) |
| CLI legacy tests in `tests/test_cli.py`: `test_count_subcommand_help_shows_count_options`, `test_legacy_no_subcommand_count_interface_still_works`, `test_count_subcommand_still_works`, `test_legacy_count_options_before_supports_are_rejected`, part of `test_abbreviated_long_options_are_rejected` (the `--mo generic` case) | `tests/test_cli.py` | legacy CLI surface | Legacy-only, **except** `test_legacy_count_options_before_supports_are_rejected` and the abbreviation case, which also exercise the shared `_reject_legacy_globals_before_supports` guard and `allow_abbrev=False` policy that the modern subcommands rely on | Keep guard-behaviour coverage; delete only the count-specific assertions | 02-legacy / 07-tests/04 |
| `Makefile` targets `legacy-count`, `legacy-generic` | `Makefile:28-32` | `make check` | Legacy-only (both) | remove; `make check` keeps `supports`/`bundles`/`labelings` | 02-legacy (generic first per 03, then legacy per 02 — see section 7) |
| `scripts/check.sh` / `scripts/check.ps1` legacy/generic invocation lines | `scripts/check.sh:16-17`, `scripts/check.ps1:14-15` | `make check` equivalents | Legacy-only (both lines) | remove both; keep the `supports`/`bundles`/`labelings`/(future `reduced`) lines | 02-legacy |
| README "Current legacy results" section, legacy no-subcommand examples, `legacy-generic` notes | `README.md:97-116, 244-283` | documentation | Legacy-only | replace with a pointer to `docs/results.md` reduced-model sections and `rice reduced` | 02-legacy / 04-public-api |
| `docs/results.md` "Legacy result" section (`lc` and `generic` tables) | `docs/results.md:1-45` | documentation, regression reference | Legacy-only *content*, but the file as a whole is shared (support-census and reduced-topology sections must stay) | keep the file, delete only the legacy section, and add an explicit "historical reference" framing (see section 5) | 02-legacy |
| `AGENTS.md` "Current legacy validation commands" section, "Legacy reference totals" | `AGENTS.md:162-193` | contributor instructions | Legacy-only | replace with the surviving `make check` command list once 02/03 land | 02-legacy / 04-public-api |
| `docs/computation.md`, `docs/bundles_and_multiedges.md`, `docs/model_decisions.md` legacy-model sections ("Legacy bundle model", "Current legacy model", "Legacy computation currently implemented") | respective files | documentation contrasting old vs. new | Legacy-only *prose*, kept deliberately as contrast material for the reduced model — see section 5 for the "keep as historical explanation" recommendation | keep with light "historical" framing, do not delete outright | 02-legacy (framing only, not deletion) |
| `docs/plan/01-dev-env/06-contract.md` progress note listing "legacy LC count, and legacy generic count" as part of the check-ordering contract | `docs/plan/01-dev-env/06-contract.md:32` | plan record | Legacy-only reference inside an otherwise-`done`, otherwise-accurate record | update wording once the targets are actually removed | 02-legacy (do not edit now — task is `done` and describes history accurately as of today) |

No entire module or helper block was assumed deletable without checking for a
reduced-model caller; the "shared" flags above and section 3 record every case
found where a helper is called from both paths.

## 3. Shared infrastructure to preserve

These helpers in `src/rice/core.py` are called by **both** `count_networks`
(legacy) and by the phase-1/2/3/reduced reduced-model APIs. None of them may
be deleted by the legacy-removal task. Some have docstrings or module-level
prose that reads as legacy-flavoured even though they are not legacy-only;
those are flagged for a documentation correction, not a code change, and no
such correction was made in this task beyond what was already accurate.

| Symbol | Legacy caller(s) | Reduced-model caller(s) | Note |
|---|---|---|---|
| `generate_connected_unlabelled_simple_graphs` | `iter_two_terminal_supports` (used by `count_networks`) | `support_census`, `iter_two_terminal_supports` (used by `simple_bundle_labeling_census`, `iter_reduced_topology_signatures`) | Core graph generator; fully shared. |
| `automorphisms` | `iter_two_terminal_supports` | `support_census`, `simple_bundle_labeling_orbit_count`, `iter_two_terminal_supports` | Fully shared. |
| `graph_invariant`, `_add_unique` | via `generate_connected_unlabelled_simple_graphs` | via `generate_connected_unlabelled_simple_graphs` | Fully shared; internal to the same generator. |
| `simple_path_edge_cover`, `is_two_terminal_relevant` | via `relevant_terminal_pair_orbit_representatives` | `support_census`, `_validate_assigned_support` (reduced-signature validation), test suite directly | Fully shared. Module docstring at `core.py:1-17` already correctly separates this from the "older `count_networks` entry point"; no misleading legacy label found here. |
| `terminal_pair_orbit_representatives`, `relevant_terminal_pair_orbit_representatives` | `iter_two_terminal_supports` | `support_census` | Fully shared. |
| `edge_permutations_preserving_terminal_set` | `count_networks` (via `iter_two_terminal_supports`'s consumer) | `simple_bundle_labeling_orbit_count` | Fully shared. Docstring is generic ("Return induced edge permutations…"), not legacy-flavoured. |
| `permutation_cycle_lengths` | `count_networks` | `simple_bundle_labeling_orbit_count` | Fully shared, generic combinatorial helper. |
| `iter_two_terminal_supports` | `count_networks` | `simple_bundle_labeling_census`, `iter_reduced_topology_signatures` | Fully shared; docstring says "for legacy counting" (`core.py:731`) but is in fact the shared support-iteration entry point for phases 2 and beyond. **This is the clearest instance of a misleading "legacy" label on shared code** — flagged as preserve + rename/redocument later, not touched in this task because the fix is not essential to the accuracy of this review (the code path and its real callers are unambiguous from the source). |
| `support_census`, `SupportCensusResult` | not used by legacy path (legacy calls `iter_two_terminal_supports` directly, not `support_census`) | `rice supports`, `simple_bundle_assignment_census` | Not legacy at all despite living in the same module as `count_networks`; no misleading naming found. |
| `_validate_assigned_support`, `_merge_parallel_edges`, `_suppress_one_series_node`, `_reduced_factor_multigraph` | not used by legacy path | `canonical_reduced_signature` | Reduced-model-only, not legacy, not shared — listed here only to confirm they have **no** legacy dependency and are fully safe from the legacy-removal task. |
| `_reject_legacy_globals_before_supports` (CLI) | guards the no-subcommand path indirectly (it is invoked unconditionally in `main()`) | protects `supports`/`bundles`/`labelings`/`reduced` from silently-ignored stray `--mode`/`--max-r` etc. placed before the subcommand | Mixed: the function name says "legacy" but half its purpose is protecting the modern subcommands. Do not delete this function when removing `count`; only stop treating `_COUNT_OPTION_NAMES`/`--mode` as needing rejection once `--mode` itself is gone. Preserve the "options before a subcommand are rejected" behaviour and its test coverage. |
| `RiceArgumentParser`, `allow_abbrev=False` policy | applies to every parser including `count` | applies to every parser including `supports`/`bundles`/`labelings`/`reduced` | Fully shared, no legacy content at all. |

Recommendation for `iter_two_terminal_supports`: when 02-legacy is
implemented, either rename it (e.g. drop "legacy" from any future docstring
wording, since none currently says "legacy" verbatim — recheck at
delete-time) or add one sentence to its docstring clarifying it is the shared
enumeration entry point for phases 2+ and the (soon to be removed) legacy
counter. This is a documentation nit, not a functional split, and does not
block deletion of `count_networks` itself.

## 4. Generic `X` inventory

Search method: exact matches on `"generic"` (case-insensitive) and on the
string `"X"`/`X`-as-reactive-label in prose, cross-checked against `Mode`
call sites. `x` used as the coordinate `L+C` in reduced-model tables
(`docs/results.md` reduced-topology tables, `docs/model_decisions.md`,
`ReducedTopologyCensusResult.as_markdown_table` header `"R \\ L+C"`,
`_reduced_topology_census_json`'s `x = l + c` local variable in
`reduced_topology_census`) is a **different, legitimate** concept and is
excluded from this table.

| Item | Where | Classification |
|---|---|---|
| `Mode = Literal["lc", "generic"]` | `src/rice/core.py:29` | generic-X support (the `"generic"` value only; `"lc"` stays as part of the retained legacy mode until 02-legacy) |
| `mode: Mode = "lc"` parameter, `mode not in {"lc", "generic"}` validation, `mode == "generic"` DP branch | `count_networks` (`core.py:1113-1162`), `fixed_assignments_by_total` (`core.py:684-701`) | generic-X support |
| `CountResult.mode` field and its docstring line describing `"generic"` | `core.py:455-456, 468` | generic-X support (field itself is legacy+generic; the `"generic"` value specifically is in scope for 03) |
| CLI `--mode` argument, `choices=("lc", "generic")` | `src/rice/cli.py:201-206` (via `_add_count_arguments`) | generic-X support (the `"generic"` choice; `--mode` itself and the `"lc"` choice are legacy-scope, task 02) |
| `reactive_label = "L+C" if mode == "lc" else "X"` output line | `src/rice/cli.py:558` | generic-X support (the `"X"` output label) |
| `mode="generic"` legacy result table and prose | `docs/results.md:29-45` | generic-X support |
| Generic-X caveats in `AGENTS.md:184-193`, `README.md:108-116, 248-250`, `docs/computation.md` (implicitly, via shared legacy contrast prose — no generic-specific text found there beyond the general legacy contrast) | doc files | generic-X support (the specific generic-mode sentences; the general legacy-vs-reduced contrast sentences around them are task-02 scope) |
| `Makefile:31-32` `legacy-generic` target | `Makefile` | generic-X support |
| `scripts/check.sh:17`, `scripts/check.ps1:15` generic invocation line | scripts | generic-X support |
| `tests/test_counts.py::test_generic_reactive_counts_match_reference_table` | test file | generic-X support |
| `tests/test_cli.py::test_abbreviated_long_options_are_rejected` first case (`["--mo", "generic", "supports"]`) | test file | generic-X support only incidentally — the case also exercises abbreviation rejection and the legacy-globals-before-subcommand guard, both of which are shared behaviour; replace the literal `"generic"` value with any other `--mode` value (or drop `--mode` from the case entirely) rather than deleting the whole test | keep the guard assertion, adjust the literal |
| Docstring phrase `'"generic"' treats all reactive elements as one type X` | `core.py:455-456`, `cli.py:205` | generic-X support |

No occurrence of a variable literally named `x` (e.g. the `x` in
`reduced_topology_census`'s `x = l + c`, or the `X` column header in reduced
tables) was misclassified as generic-element support; those are the budget
coordinate and are explicitly out of scope for 03-generic-x.

## 5. What must be preserved

- **Graph/support machinery** (section 3's shared list in full) — general
  purpose, reduced-model-load-bearing, must survive regardless of what happens
  to `count_networks`.
- **Test techniques**: the brute-force cross-check pattern in
  `tests/test_bundle_labelings.py` (`_brute_orbit_count`) and the
  independent-brute-force pattern in `tests/test_reduced_census.py`
  (`test_independent_bruteforce_r1_x1_matches_census_api`) are reusable
  verification techniques independent of the legacy counter; keep them as
  templates for any future Ladenheim-slice or full-slice golden tests
  (`docs/plan/03-counting/05-ladenheim.md`, `06-full-counts.md`).
- **Golden legacy numbers as historical reference, not active runtime
  support**: the `lc` totals (`1,408,796` / `1,268,282` exactly-R=3) and the
  `generic` totals (`57,945` / `51,736`) in `docs/results.md` and `AGENTS.md`
  are independently useful as a permanent historical data point — they
  quantify exactly how much the legacy multiset-bundle overcount differs from
  the reduced model (e.g. compare `1,408,796` legacy vs the eventual full
  `R<=3, L+C<=5` reduced total once 05-slices/04 is done). Recommendation:
  when 02-legacy and 03-generic-x land, move these numbers into a clearly
  labelled "historical legacy reference" subsection (or a dedicated
  `docs/legacy_reference.md`) rather than deleting them outright, and stop
  regenerating them from any script or `make check` target. They should no
  longer be asserted against by any test at that point — they become a static
  historical citation, not a golden value protecting live code.
- **Documentation explaining historical behaviour**: the "Legacy bundle
  model" section of `docs/bundles_and_multiedges.md` and the "Current legacy
  model" section of `docs/model_decisions.md` are valuable precisely because
  they explain *why* `R||R` used to be counted separately and *why* that was
  wrong for the reduced model. Recommendation: keep these sections (retitled
  if needed to read unambiguously as history, e.g. "Historical: the removed
  legacy bundle model") rather than deleting them; they are cheap to keep and
  expensive to reconstruct.
- **Public behaviour needing an intentional migration note**: `rice count`
  and the no-subcommand form are currently the *only* documented way to
  reproduce the legacy totals at all (there is no flag on `rice reduced` that
  reproduces multiset-bundle counting). Task 02-legacy must include an
  explicit migration note (README/CHANGELOG-equivalent) telling any user of
  `rice count`/`rice --mode lc` that the closest replacement is `rice reduced`
  and that the numbers are not equivalent (reduced counts are smaller because
  `R||R`-style duplicates no longer exist as distinct topologies).
- **Reusable formatting/validation logic**: `RiceArgumentParser`
  (`allow_abbrev=False`), `_validate_nonnegative`, `_validate_positive`,
  `_resolve_component_census_limits`, and the JSON-payload-plus-computed-totals
  pattern (`asdict(result)` + extra totals, used by every `_*_json` helper)
  are all reusable independent of `count_networks` and must survive.
- **Evidence for comparing old and replacement counts**: keep
  `tests/test_counts.py`'s golden tables (or their numeric content) available
  somewhere even after the test file itself is retired, specifically so a
  future comparison document (e.g. an addition to `docs/results.md` or
  `docs/plan/05-slices/04-r3-x5.md` once the full reduced slice is computed)
  can state "legacy over-count was 1,408,796; reduced count is N" with a
  citable source.

## 6. Compatibility decision

**Recommendation: no compatibility shim.**

Evidence:

- `pyproject.toml` declares `version = "0.1.0"`, a single author
  (`Andy Ackland / ChatGPT`), no `Repository`/`Homepage` project URL, and no
  PyPI classifiers or trove metadata suggesting a published release.
- There is no `CHANGELOG`, no version-support policy, no deprecation-policy
  document, and no SemVer commitment anywhere in the repository.
- `git log` shows 42 commits total, all authored in the same short
  development window, with no tags and no evidence of external forks,
  release branches, or a publishing workflow (`.github/` contains no
  workflow files at all — none exist in the tree).
- README and `AGENTS.md` both already describe `rice count`/the
  no-subcommand form as "legacy" and "compatibility only", and `docs/results.md`
  / `README.md` already state that the generic-X figures "should not be
  treated as the final target count" — i.e. the project itself already frames
  this surface as provisional, not as a stable public contract.
- No test, doc, or config file references an external package name, install
  target, or downstream project depending on `rice`.

Absence of an identified consumer is not proof that none exists — this is a
public GitHub repository and an anonymous clone or fork cannot be ruled out by
inspecting the tree alone. However, the repository provides no compatibility
commitment of any kind (no version promise, no publish target, no documented
consumer), so speculative preservation of `count_networks`/`--mode
generic`/the no-subcommand form beyond a clear migration note (section 5) is
not warranted. A temporary warning/deprecation shim (e.g. a `DeprecationWarning`
on `rice count`/no-subcommand invocation for one release before deletion)
would be a reasonable, low-cost middle ground if the maintainer wants extra
safety margin, but the evidence here does not compel it. No shim was added in
this task.

## 7. Test and validation coverage

### Safeguards already present

- Legacy `lc` output: `tests/test_counts.py::test_lc_counts_match_reference_table`
  pins the full `R<=3, L+C<=5` table, exactly-R=3 total, and grand total.
- Generic output: `tests/test_counts.py::test_generic_reactive_counts_match_reference_table`
  pins the equivalent generic table/totals.
- `rice count`: `tests/test_cli.py::test_count_subcommand_still_works`,
  `test_count_subcommand_help_shows_count_options`.
- No-subcommand interface:
  `tests/test_cli.py::test_legacy_no_subcommand_count_interface_still_works`,
  `test_legacy_count_options_before_supports_are_rejected`.
- Modern `supports`: `tests/test_support_census.py` (full census table,
  terminal reversal, dangling/pendant rejection, series/parallel acceptance)
  plus CLI tests in `test_cli.py` (`test_supports_*`).
- Modern `bundles`: `tests/test_bundle_census.py` (assignment counts, leaf
  totals, budget edge cases) plus CLI tests (`test_bundles_*`).
- Modern `labelings`: `tests/test_bundle_labelings.py` (orbit counts,
  brute-force cross-checks, Burnside budget accounting) plus CLI tests
  (`test_labelings_*`).
- Modern `reduced`: `tests/test_reduced_signatures.py` (all documented
  boundary cases: series commutation, primitive duplicate merging, compound
  non-merging, terminal reversal, internal renaming, series-in-parallel,
  bridge/core stability, malformed-input rejection) and
  `tests/test_reduced_census.py` (golden slice, determinism, no duplicates,
  API/CLI/committed-JSON agreement).
- Public exports and CLI help: `tests/test_cli.py::test_top_level_help_does_not_show_support_or_count_options_as_global`
  and the per-subcommand `--help` tests cover CLI help; **package export
  surface had no equivalent pinning test before this task** (see below).

### Characterisation test added in this task

`tests/test_public_exports.py` (new file, 3 tests):

- `test_current_public_export_surface_matches_documented_legacy_split` — pins
  `rice.__all__` against two explicit sets, `LEGACY_ONLY_EXPORTS =
  {"CountResult", "count_networks"}` and `SURVIVING_EXPORTS` (the 19 remaining
  names). This closes the one material gap found: no existing test asserted
  anything about `rice.__all__`/`rice/__init__.py` at all, so a future
  cleanup PR could accidentally remove a surviving export (or forget to remove
  a legacy one) without a failing test pointing at it.
- `test_every_documented_export_name_is_importable_from_top_level_package` —
  confirms every name in both sets actually resolves via `hasattr(rice,
  name)`, catching drift between `__all__` and the actual `from .core import
  (...)` list in `__init__.py`.
- `test_generic_mode_is_not_a_top_level_export` — documents that `Mode` and
  the string `"generic"` are not, and should not become, top-level exports;
  this is a cheap guard against 03-generic-x accidentally promoting the mode
  concept to the public surface while trying to preserve something else.

This test file is deliberately the only addition in this task. It was written
because task 02-legacy and 04-public-api both operate directly on
`rice.__all__`, and until this test existed there was no low-risk,
automatic signal for "did this cleanup PR change the export surface exactly as
intended." No other characterisation tests were added: the existing suite
already covers every other required boundary (legacy `lc`/`generic`/`count`/
no-subcommand behaviour, and all four modern subcommands) at golden-value
granularity, and duplicating that would not add information.

### Test changes expected in the later deletion PRs

- 03-generic-x: remove `test_generic_reactive_counts_match_reference_table`;
  edit the `--mo generic` case in `test_abbreviated_long_options_are_rejected`
  to use a different literal (e.g. `--mo lc`) so the abbreviation-rejection
  assertion survives; remove `"generic"` from `_COUNT_OPTION_NAMES`/CLI
  `choices` tests if any start asserting on the `choices` tuple contents
  directly (none currently do — `test_count_subcommand_help_shows_count_options`
  only checks substrings are present, so it will keep passing once `--mode`
  itself still exists with only `"lc"`); shrink `LEGACY_ONLY_EXPORTS`/mode
  validation only if `Mode` collapses to a non-`Literal` type — no export
  change is needed since `Mode` was never exported.
- 02-legacy: remove `tests/test_counts.py` in full (or relocate its golden
  numbers into a comment/fixture purely for historical citation, per section
  5); remove the count-specific tests listed in section 2's CLI-tests row from
  `test_cli.py`, but **keep**
  `test_legacy_count_options_before_supports_are_rejected` and the
  abbreviation-rejection test, generalising their assertions so they no longer
  reference `--mode`/`count` by name once those are gone (e.g. assert on
  `--max-r`/`--format` instead); move `"CountResult"` and `"count_networks"`
  out of `SURVIVING_EXPORTS` and delete `LEGACY_ONLY_EXPORTS` (or assert it is
  empty) in `test_public_exports.py`.
- 04-public-api: re-run `test_public_exports.py` after edits and update the
  golden `LEGACY_ONLY_EXPORTS`/`SURVIVING_EXPORTS` sets to match; audit
  README/AGENTS.md examples for any remaining `rice count`/`--mode` mentions
  outside a historical-reference section.
- 07-tests/04-cleanup-tests: record, once 02/03 land, which exact test IDs
  were deleted vs. generalised (this review does not delete anything, so
  nothing is recorded there yet beyond the note added below).

### Commands that should fail after deletion

Once 02-legacy and 03-generic-x are both complete:

```bash
.venv/bin/python -m rice count --mode generic --max-r 3 --max-reactive 5
.venv/bin/python -m rice --mode lc --max-r 3 --max-reactive 5
.venv/bin/python -m rice --max-r 3 --max-reactive 5
python -c "from rice import count_networks, CountResult"
make legacy-count
make legacy-generic
```

### Commands and APIs that must continue to pass unchanged, before and after cleanup

```bash
.venv/bin/python -m rice supports --max-edges 8
.venv/bin/python -m rice bundles --max-r 3 --max-reactive 5
.venv/bin/python -m rice labelings --max-r 3 --max-reactive 5
.venv/bin/python -m rice reduced
.venv/bin/python -m rice reduced --max-r 2 --max-reactive 3 --format json
python -c "from rice import support_census, simple_bundle_assignment_census, simple_bundle_labeling_census, reduced_topology_census, canonical_reduced_signature"
```

## 8. Recommended deletion sequence

The sequence below is designed so that no step temporarily breaks
shared code (section 3), and so generic-X removal (a strictly smaller,
independent change) lands before the larger legacy-counter removal, matching
the existing hint in `AGENTS.md`/`README.md`/`docs/results.md` that
`legacy-generic` should be removed "together with `--mode generic`" ahead of a
full legacy removal.

1. **Removal of generic `X` support (`docs/plan/02-cleanup/03-generic-x.md`)**
   — narrowest change, entirely inside the legacy counter's own `mode`
   parameter:
   - Collapse `Mode` to just `"lc"` (or remove the parameter and hard-code
     `lc` behaviour) in `count_networks`/`fixed_assignments_by_total`.
   - Remove `"generic"` from CLI `--mode` choices; update the `reactive_label`
     line in `cli.py`.
   - Remove `Makefile:31-32` (`legacy-generic`), the matching line in
     `scripts/check.sh`/`scripts/check.ps1`.
   - Remove `test_generic_reactive_counts_match_reference_table`; fix the
     `--mo generic` literal in the abbreviation test.
   - Remove the `docs/results.md` generic table and the generic-specific
     sentences in `AGENTS.md`/`README.md` (leave the `lc` legacy material
     alone — that is task 02's job).
   - Do not touch `support_census`, `iter_two_terminal_supports`, or any
     phase 1-5 reduced-model code; none of it depends on `Mode`.
2. **Removal of the legacy counter and CLI
   (`docs/plan/02-cleanup/02-legacy.md`)** — only after step 1, so there is
   never a state where `mode="generic"` exists without CLI support for it:
   - Delete `count_networks`, `CountResult`, `fixed_assignments_by_total`,
     `Mode` (now `Literal["lc"]` or gone entirely), `_count_json`, the
     `count` subparser, the no-subcommand fallback branch, and
     `_add_count_arguments`'s use on the top-level parser (or replace with a
     clear "removed" error message if a compatibility shim is chosen per
     section 6).
   - Do **not** delete `generate_connected_unlabelled_simple_graphs`,
     `automorphisms`, `simple_path_edge_cover`, `is_two_terminal_relevant`,
     `terminal_pair_orbit_representatives`,
     `relevant_terminal_pair_orbit_representatives`,
     `edge_permutations_preserving_terminal_set`,
     `permutation_cycle_lengths`, or `iter_two_terminal_supports` — all are
     shared per section 3.
   - Keep `_reject_legacy_globals_before_supports` but shrink
     `_LEGACY_GLOBAL_OPTION_NAMES` to whatever legacy-only globals remain (if
     none remain, consider whether the guard is still needed at all, since
     every remaining subcommand already takes its own options after itself —
     re-verify against 04-public-api rather than deciding now).
   - Remove `tests/test_counts.py` and the count-specific `test_cli.py` cases
     listed above; keep and generalise the two shared-guard tests.
   - Move `docs/results.md`'s legacy `lc` table and `AGENTS.md`'s "Legacy
     reference totals" into a clearly labelled historical section (section 5).
3. **Cleanup of exports, examples, docs, scripts, and public surface
   (`docs/plan/02-cleanup/04-public-api.md`)** — after both removals land:
   - Update `rice/__init__.py` and `__all__` to drop `CountResult`/
     `count_networks`; update `tests/test_public_exports.py`'s
     `LEGACY_ONLY_EXPORTS`/`SURVIVING_EXPORTS` accordingly (should become
     `LEGACY_ONLY_EXPORTS == set()`).
   - Sweep README/AGENTS.md for any remaining `rice count`/`--mode` examples
     outside the historical section; update the documented `make check`/
     `scripts/check.sh` command list.
   - Confirm `rice --help` no longer lists `count` and that top-level help
     text no longer mentions the no-subcommand form (update the parser
     epilog in `cli.py:44-47`).
4. **Cleanup regression testing
   (`docs/plan/07-tests/04-cleanup-tests.md`)** — after steps 1-3:
   - Run the "commands that should fail after deletion" list in section 7 and
     confirm each one now fails with a clear error (not a traceback).
   - Run the "commands and APIs that must continue to pass unchanged" list
     and confirm all still pass byte-for-byte identical output.
   - Run `make check` end to end and confirm it no longer references
     `legacy-count`/`legacy-generic`.
   - Update this review's section 7 "expected test changes" notes to `done`
     once each is actually carried out, rather than marking 07-tests/04
     complete prematurely.

## Risks and follow-up items

- **Risk**: deleting `iter_two_terminal_supports` by mistake because its
  docstring says "legacy counting". Mitigated by section 3's explicit flag;
  the fix at delete-time is a docstring edit, not a deletion.
- **Risk**: the `_reject_legacy_globals_before_supports` guard and
  `_LEGACY_GLOBAL_OPTION_NAMES` are named as if entirely legacy-scoped, but
  the guard also protects the modern subcommands from a stray `--format`
  placed before them. Mitigated by calling this out explicitly in sections 2
  and 8 step 2.
  - Follow-up: 02-legacy should re-verify, not assume, whether any
    non-legacy global option still needs pre-subcommand rejection once
    `--mode` is gone; today `--format` is the only remaining shared global
    and it is already validated per-subcommand, so this guard may become
    fully removable, but that determination belongs to 02-legacy, not this
    review.
- **Risk**: `docs/results.md` and `AGENTS.md` mixing shared and legacy-only
  content in the same file/section makes partial deletion error-prone.
  Mitigated by section 2's line-range references and the explicit
  "historical section" recommendation in section 5.
- **Risk**: no automated check currently prevents a future PR from
  re-introducing a `generic`-like mode or restoring `count_networks` under a
  new name. Not addressed in this task (out of scope — no shim, no new
  guard added) beyond the new `test_public_exports.py` pinning the intended
  export set.
- **Follow-up for 03-counting/06-full-counts.md**: once the full `R<=3,
  L+C<=5` reduced-topology census is implemented, add the direct numeric
  comparison against the legacy `1,408,796`/`57,945` totals recommended in
  section 5, ideally before the legacy tables are demoted to a purely
  historical section, so the comparison is easy to write while both numbers
  are still fresh in the same PR sequence.
- **Follow-up for 07-tests/04-cleanup-tests.md**: this review's section 7
  "Test changes expected in the later deletion PRs" list should be treated as
  the checklist for that task; it is intentionally more specific than the
  current one-line goal in `docs/plan/07-tests/04-cleanup-tests.md`.

## Validation performed for this review

Environment: repository-local `.venv` created via `./scripts/setup.sh`
(Python 3.13.12, networkx 3.6.1, pytest 9.1.1), per `AGENTS.md`.

```bash
./scripts/setup.sh        # created .venv, installed rice + dev deps — succeeded
./scripts/test.sh         # .venv/bin/python -m pytest -q — 99 passed
./scripts/check.sh        # lint (git diff --check + syntax compile) + test.sh +
                          # supports/bundles/labelings/legacy-lc/legacy-generic
                          # — all stages succeeded, all reference totals matched
git diff --check          # no whitespace errors
.venv/bin/python -m rice --help
.venv/bin/python -m rice count --help
.venv/bin/python -m rice supports --help
.venv/bin/python -m rice bundles --help
.venv/bin/python -m rice labelings --help
.venv/bin/python -m rice reduced --help
```

After adding `tests/test_public_exports.py`:

```bash
.venv/bin/python -m pytest -q       # 102 passed (99 + 3 new)
```

All commands above ran to completion with no unexpected failures; no
command's output was truncated or skipped. This review made no source,
Makefile, script, or CLI-behaviour changes — only this document,
`docs/plan/00-index.md` (status update), and the new
`tests/test_public_exports.py` characterisation test were added/changed.

## Progress notes

- 2026-07-10: Completed the required review. Ran the full validation stack
  (`setup.sh`, `test.sh`, `check.sh`, `git diff --check`, all CLI `--help`
  invocations) against the current `main` tree with a freshly created
  `.venv`; every command succeeded and every documented reference total
  matched. Added one small characterisation test file
  (`tests/test_public_exports.py`, 3 tests) pinning the legacy-vs-surviving
  split of `rice.__all__`, because no existing test covered the package
  export surface at all and both 02-legacy and 04-public-api operate on that
  surface directly. Made no other code, test, script, or Makefile changes.
  Recommendation: no compatibility shim (section 6); recommended deletion
  order is generic-X removal (03) before legacy-counter removal (02), then
  export/docs cleanup (04), then cleanup regression testing (07-tests/04),
  detailed in section 8.
