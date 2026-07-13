# 04 — Interface consolidation

Status: done

## Completed

- Removed staged compatibility commands `rice supports`, `rice bundles`, `rice
  labelings`, and `rice reduced`; `rice count <object>` is the sole user-facing
  counting grammar.
- Removed staged public API exports and result types from `rice.__all__`; shared
  support enumeration, Burnside arithmetic and local-SP reduction machinery are
  retained internally for object-language counts and focused reduction helpers.
- Removed old staged JSON/reporting paths and migrated the committed golden
  network artefact to the object-language `count networks --profile golden`
  schema.
- Declared the CLI, Python API and serialisations provisional in user-facing
  documentation.
- Left PR3 work (`rice enum ...`, reduction provenance and fibre analysis) open.


## 2026-07 CLI language review

- Top-level, group-level, and leaf help are now successful discoverability paths:
  `rice`, `rice -h`, `rice --help`, `rice help count`, and
  `rice help count supports`.
- `count reductions` is included in the top-level and count maps, and the top
  help describes the pipeline order and a finite-scope example.
- Output has an explicit `auto|table|markdown|json` contract: redirected `auto`
  is JSON and interactive `auto` is a readable table.
- Parser destinations are hidden behind user-facing metavars, leaf errors show
  leaf usage, relation choices are argparse choices, and finite fixed
  support-edge source ranges are accepted consistently for network counting and
  enumeration as well as earlier source stages.

## 2026-07 Python API documentation pass

- Audited the provisional `rice.__all__` surface into query/configuration,
  count, enumeration, reduction-helper, record/fact, relation, and constant
  categories.
- Added authored IDE/pydoc documentation for public callables and record/result
  types, including source-versus-reduced component semantics, grouping names,
  relation validation, and enumeration size guards.
- Expanded `docs/python_api.md` into a runnable guide covering profiles, query
  construction, grouping, relations, JSON conversion, record navigation,
  failure cases, and the distinction between `support_census(max_edges=8)` and
  the query-based object-language API.
