# 02-cleanup / 04 — Update examples, imports, and public surface

Status: `done`

## Goal

Perform the **final audit** of help text, examples, imports, terminology, and
documentation after `docs/plan/02-cleanup/02-legacy.md` had already deleted
the legacy counter and updated the exports. This task is a coherence sweep and
public-API finalisation, not the place where the legacy counter's removal
happens for the first time — that already landed atomically with
`02-legacy.md`.

## Scope

By the time this task started:

- generic `X` support was already gone (`03-generic-x.md`);
- the legacy counter, its CLI surface, and its exports were already gone
  (`02-legacy.md`), including the `rice/__init__.py`/`__all__` update and the
  matching `tests/test_public_exports.py` update.

This task audited everything *around* those removals for leftover
references, stale prospective/"intended" wording, and coherence gaps, and
additionally finalised the supported Python API surface (two names were
deliberately added — see below) and its documentation.

## Tasks

- Reviewed package exports (`rice/__init__.py`, `rice.__all__`) for
  coherence, classifying every non-private definition in `src/rice/core.py`
  as top-level supported API, public only through `rice.core`, or internal
  implementation detail (see "Public API decision" below).
- Updated examples and CLI docs: swept README.md, AGENTS.md, and `docs/*.md`
  for remaining references to `rice count`, `--mode`, `count_networks`, or
  `CountResult` outside explicitly historical sections, and for stale
  "intended"/prospective wording describing already-implemented stages as
  future work.
- Checked for notebook-facing examples: none exist in the repository; none
  were added, consistent with not creating one solely for this task.
- No deprecation-warning code existed to evaluate; per `01-review.md` section
  6, no compatibility shim was ever added, so there was nothing to keep or
  remove here.
- Corrected the `iter_two_terminal_supports` docstring in `02-legacy.md`
  already fixed the clearest instance flagged by `01-review.md` section 3; no
  further misleading "legacy" labels on shared code were found in this pass.
- Addressed stale wording previously flagged out of scope for earlier tasks:
  the `core.py` module docstring (already corrected in `02-legacy.md`), the
  "Suggested implementation order" section of `docs/model_decisions.md`, the
  "Reduced computation target"/"Stage 1-3" prospective wording in
  `docs/computation.md`, and the "Intended reduced-topology model"/"First
  implementation milestone" headings in `README.md`.

## Public API decision

Reviewed every non-private (non-underscore) definition in `src/rice/core.py`
and classified each as:

- **top-level supported API** (exported from `rice.__all__`): all previously
  exported names, plus two additions —
  - `SimplePrimitiveBundle`: `SIMPLE_PRIMITIVE_BUNDLES` was already exported
    and its entries are `SimplePrimitiveBundle` instances, so the type itself
    belongs alongside the constant;
  - `normalise_reduced_factor`: the general recursive validation/
    canonicalisation entry point for caller-supplied `ReducedFactor` trees,
    directly analogous to the already-exported, more specialised
    `normalise_series_factor`/`normalise_parallel_factor`.
- **public only through `rice.core`** (no top-level export): `PrimitiveName`,
  `FactorKind` (typing aliases), `graph_invariant`,
  `generate_connected_unlabelled_simple_graphs`, `automorphisms`,
  `simple_path_edge_cover`, `is_two_terminal_relevant`,
  `terminal_pair_orbit_representatives`,
  `relevant_terminal_pair_orbit_representatives`,
  `edge_permutations_preserving_terminal_set`, `permutation_cycle_lengths`,
  `iter_two_terminal_supports`, `simple_bundle_assignment_count_by_edge_count`
  — low-level graph-generation, automorphism, and combinatorial
  infrastructure, deliberately not promoted merely to enlarge the public
  surface.
- **internal implementation detail** (underscore-prefixed): every
  `_`-prefixed helper (`_normalise_composition`, `_edge_key`,
  `_validate_assigned_support`, `_merge_parallel_edges`,
  `_suppress_one_series_node`, `_reduced_factor_multigraph`, `_add_unique`,
  `_fixed_simple_bundle_labelings_for_cycles`, `_component_counts_for_factor`,
  `_assignment_options_by_budget`, `_iter_budgeted_edge_assignments`).

`tests/test_public_exports.py` was updated atomically with the two additions.

## Done means

- The supported API is obvious: `rice.__all__` contains the 21
  supports/bundles/labelings/reduced-factor/reduced-topology-path symbols
  listed above (19 pre-existing plus `SimplePrimitiveBundle` and
  `normalise_reduced_factor`), and every name in it is documented in
  `docs/python_api.md`, linked prominently from README.
- Removed internals (`count_networks`, `CountResult`, `Mode`,
  `fixed_assignments_by_total`, generic `X`) are not visible in examples,
  docs, or help text, except inside explicitly historical sections.
- `rice.__all__` and `tests/test_public_exports.py` are consistent as of this
  task's final commit.
- Prospective/"intended" wording describing already-implemented stages as
  future work has been corrected to present tense across README.md,
  AGENTS.md, `docs/model_decisions.md`, and `docs/computation.md`, while
  historical explanations of the removed legacy model are preserved.

## Progress notes

- 2026-07-10: Completed. Ran the required search sweeps
  (`count_networks|CountResult|fixed_assignments_by_total|--mode|rice count|
  legacy-count|legacy-generic|no-subcommand` and `intended reduced|intended
  replacement|not yet implemented|remains a later stage|before changing|when
  reduced signatures are introduced|current legacy|legacy count path|
  reduced-signature tests have not started`) against README.md, AGENTS.md,
  `docs/`, `src/`, `tests/`, `Makefile`, and `scripts/`, both before and after
  editing. Every remaining match after editing is either a dated progress
  note, a completed historical task record (`01-review.md`, `02-legacy.md`,
  `03-generic-x.md`), or a test asserting a removed name's absence — no
  active instruction, CLI example, or validation command referencing removed
  syntax remains.
  - Rewrote AGENTS.md's "Near-term implementation sequence" as "Implementation
    status and remaining work", listing the five implemented stages
    up front and separating genuinely remaining work (larger slices,
    performance review, Ladenheim comparison, full `R<=3,L+C<=5` execution,
    descriptor/catalogue outputs) from the per-phase reference material,
    which is retained.
  - Retitled and rewrote README.md's "Intended reduced-topology model" →
    "Reduced-topology model" and "First implementation milestone" →
    "Support-graph census", both now present tense; corrected "series spans
    are intended to commute" → "commute"; corrected the migration note's
    "always smaller" claim to state the two counting contracts are not
    numerically equivalent and reduced counts are *generally* lower (not
    strictly smaller for every slice); fixed a stale trailing paragraph that
    still described full signature enumeration/merging as unimplemented.
  - Retitled `docs/model_decisions.md`'s "Intended reduced model" → "Reduced
    model" and rewrote its "Suggested implementation order" as
    "Implementation stages", stating each of the four stages is implemented
    (the fourth for the committed small golden slice, with the full-scope run
    tracked as separate remaining work, not an unimplemented stage).
  - Rewrote `docs/computation.md`'s "Reduced computation target"/"Stage 1-3"
    sections from prospective ("should be implemented", "before changing...
    implement") to present tense, naming the implementing function/CLI
    command for each stage.
  - Corrected stale plan-doc progress notes in `docs/plan/03-counting/
    02-distinct.md` (no longer claims only the support portion is
    implemented, no longer describes `count_networks` as extant),
    `docs/plan/03-counting/03-scope.md` (no longer describes a "legacy count
    path" or `make check` validating legacy totals as current), `docs/plan/
    07-tests/01-strategy.md` (reduced-signature tests are extensively
    implemented, not "not started"; next-steps list updated to genuinely
    remaining items), `docs/plan/07-tests/02-golden-counts.md` (no longer
    claims a live `lc` golden test exists), `docs/plan/07-tests/
    03-canon-tests.md` (full census integration is implemented and tested for
    the golden slice), and `docs/plan/08-docs/02-count-method.md` (no longer
    describes `count_networks` as extant). Dated historical notes elsewhere
    (e.g. the 2026-07-10 entries in `docs/plan/01-dev-env/06-contract.md`)
    were left untouched, per instruction to preserve accurate historical
    records.
  - Added `SimplePrimitiveBundle` and `normalise_reduced_factor` to
    `src/rice/__init__.py`'s import list and `__all__`; updated
    `tests/test_public_exports.py`'s `PUBLIC_EXPORTS` set in the same commit.
  - Created `docs/python_api.md`: every one of the 21 `rice.__all__` names,
    grouped by role (support census; primitive bundles and raw assignment
    census; labeling-orbit census; reduced factors and signatures; end-to-end
    reduced-topology enumeration), each with its role, signature/fields,
    equivalence stage, raw/orbit/reduced classification, and limits. Every
    code example was run in the repository `.venv` and its exact output
    pasted into the doc (not hand-derived). Linked prominently from README's
    "Status" section.
  - Audited CLI help text (`rice --help` and all four subcommand `--help`
    outputs): already coherent — only the four subcommands appear, phase
    terminology matches README/API docs, "raw"/"labeling orbit"/"reduced
    topology" are already textually distinct, and no help text references a
    removed count mode. No CLI wording changes were needed.
  - Added `tests/test_public_api_examples.py` (8 tests) exercising the
    `docs/python_api.md` examples at tiny budgets: support/bundle/labeling/
    reduced census calls, `SimplePrimitiveBundle` type-matching, factor
    construction/normalisation (including a deliberately messy
    caller-constructed `ReducedFactor` to exercise `normalise_reduced_factor`
    recursively), canonical-signature determinism/terminal-reversal
    invariance, and the reduced-topology census result fields.
  - Validated: `bash .codex/setup.sh`, `make test` (107 passed), `make lint`,
    `make check` (including the `rice reduced` final stage), `git diff
    --check`, `make supports`/`bundles`/`labelings`/`reduced` individually,
    all five `--help` outputs, the documented `docs/python_api.md` examples
    (run directly, not just via the new test module), the three required
    removed-CLI-form checks (`rice`, `rice count`, `rice --mode lc` — all
    exit 2, no traceback), and the exact final-import smoke test from this
    task's instructions (including `SimplePrimitiveBundle`/
    `normalise_reduced_factor`). `pwsh` was not available in this session;
    `scripts/check.ps1` was re-inspected against `scripts/check.sh` (neither
    changed in this task) and re-confirmed to have exact stage parity.
  - Next substantive task: reconciling and beginning the Ladenheim comparison
    work described by `docs/plan/03-counting/05-ladenheim.md` and
    `docs/plan/05-slices/02-ladenheim.md`. Not started in this task.
