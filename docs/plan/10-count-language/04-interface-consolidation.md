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
