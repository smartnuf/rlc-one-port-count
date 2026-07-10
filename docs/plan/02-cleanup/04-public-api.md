# 02-cleanup / 04 — Update examples, imports, and public surface

Status: `todo`

## Goal

Perform the **final audit** of help text, examples, imports, terminology, and
documentation after `docs/plan/02-cleanup/02-legacy.md` has already deleted
the legacy counter and updated the exports. This task is a coherence sweep, not
the place where `rice/__init__.py`, `rice.__all__`, or their corresponding
export tests get edited for the first time — those edits are required for
`02-legacy.md` to be mergeable at all (removing `count_networks`/`CountResult`
from `core.py` while leaving them importable from the top-level package would
be a broken intermediate state) and must land atomically with that deletion,
not be postponed to this task.

## Scope

By the time this task starts:

- generic `X` support is already gone (`03-generic-x.md`);
- the legacy counter, its CLI surface, and its exports are already gone
  (`02-legacy.md`), including the `rice/__init__.py`/`__all__` update and the
  matching `tests/test_public_exports.py` update.

This task audits everything *around* those removals for leftover references,
stale terminology, or coherence gaps — it does not perform new deletions of
its own.

## Tasks

- Review package exports (`rice/__init__.py`, `rice.__all__`) for coherence:
  confirm every exported name is documented, every documented name is
  exported, and nothing legacy-flavoured slipped back in.
- Update examples and CLI docs: sweep README.md, AGENTS.md, and `docs/*.md`
  for any remaining reference to `rice count`, `--mode`, `count_networks`, or
  `CountResult` outside an explicitly historical section, and for any
  remaining "legacy" caveats that are now simply stale.
- Update notebook-facing examples if any exist (none currently do; re-check at
  implementation time).
- Keep deprecation notes only if they are useful — per `01-review.md` section
  6, no compatibility shim was recommended or added, so there should be no
  deprecation warning code to preserve. If a later task did add one, decide
  here whether it is still earning its keep.
- Correct any remaining misleading "legacy" labels on shared code identified
  by `01-review.md` section 3 that `02-legacy.md` did not already fix (for
  example, re-check `iter_two_terminal_supports`'s docstring).
- Address the stale wording flagged out of scope for earlier tasks, such as
  the `core.py` module docstring's description of what is/isn't implemented,
  now that the legacy counter it contrasts against is gone.

## Done means

- The supported API is obvious: `rice.__all__` contains only
  `supports`/`bundles`/`labelings`/`reduced`-path symbols, and every name in
  it is documented somewhere a new contributor would find it.
- Removed internals (`count_networks`, `CountResult`, `Mode`, generic `X`) are
  not visible in examples, docs, or help text, except inside explicitly
  historical sections.
- `rice.__all__` and `tests/test_public_exports.py` are already consistent
  going into this task (verified, not re-derived here) — this task's job is
  the surrounding documentation and terminology, not the export list itself.
