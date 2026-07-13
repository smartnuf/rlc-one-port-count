# RICE

RICE counts and enumerates small two-terminal (or one-port) resistor/inductor/capacitor
topology classes.

We were inspired by reading a book by
[Morelli and Smith](https://www.google.co.uk/books/edition/Passive_Network_Synthesis_An_Approach_to/IdyZDwAAQBAJ?hl=en&gbpv=0),
and some of the references they site in their bibliography.

## Development status: provisional interfaces

RICE is under active development. Its command-line interface, Python API, data
formats, catalogue representations and equivalence definitions have not yet
been declared stable. Until a versioned public interface is published, scripts
and downstream projects should not rely on current command names, function
signatures, JSON fields, descriptor syntax or serialized output remaining
unchanged.

This does **not** mean mathematical changes are casual: model definitions are
documented, counts are regression-tested, and semantic changes should be
deliberate and recorded. The current warning is about software-interface
compatibility, not about relaxing the counting contract.

## Use

Install the development environment, then run object-language count commands:

```bash
make setup
.venv/bin/python -m rice count supports --max-support-edges 8
.venv/bin/python -m rice count bundle-types
.venv/bin/python -m rice count bundle-sets --profile main
.venv/bin/python -m rice count assignments --profile main
.venv/bin/python -m rice count assigned-supports --profile main
.venv/bin/python -m rice count networks --profile golden
```

The supported provisional command grammars are:

```text
rice count <object> [options]
rice enum <object> [options]
```

Implemented count and enum objects are:

- `supports` — connected unlabelled support graphs, unordered terminal choices,
  and terminal-relevant two-terminal supports.
- `bundle-types` — the seven simple primitive bundle labels `R`, `L`, `C`,
  `R||L`, `R||C`, `L||C`, and `R||L||C`.
- `bundle-sets` — inventories/multisets of simple primitive bundle labels within
  a query budget.
- `assignments` — raw placements of bundle inventories on terminal-relevant
  supports.
- `assigned-supports` — assignments quotiented by automorphisms preserving the
  unordered terminal set.
- `networks` — unique local-series/parallel reduced networks under the current
  relation `canonical-reduced-topology-local-series-parallel-v1`.

`rice count reductions` analyses the provenance maps from raw assignments to
assigned-support classes to local-SP networks, including fibre distributions,
source-edge transitions, exact source-to-reduced component transitions, and
collision summaries. Enumeration output uses provisional SHA-256-derived IDs and
a default `--max-records 10000` guard for catalogue-producing commands.

Detailed semantics are in `docs/counting_language.md`; the provisional Python
API is documented in `docs/python_api.md`.


### Command map and glossary

The bare command and normal help forms are equivalent:

```bash
.venv/bin/python -m rice
.venv/bin/python -m rice -h
.venv/bin/python -m rice --help
.venv/bin/python -m rice help count networks
```

Pipeline glossary (deeper definitions: `docs/counting_language.md` and
`docs/model_decisions.md`):

```text
supports -> bundle-types -> bundle-sets -> assignments -> assigned-supports -> networks
```

- `supports` are source graph shapes and terminal choices before components are
  attached.
- `bundle-types` are the seven simple source edge labels.
- `bundle-sets` are source inventories before support placement.
- `assignments` are raw component-labelled source placements.
- `assigned-supports` quotient assignments by terminal-set-preserving support
  automorphisms.
- `networks` are final local-SP reduced objects.
- `reductions` reports provenance for the many-to-one transitions from source
  assignments to reduced networks.

Help is available as `rice help`, `rice help count`, `rice help count supports`,
or by trailing `--help`; `rice --help count supports` is normalized to the same
leaf help. Bare `rice count` and `rice enum` print group help and do not run any
legacy no-object count.

Output defaults to `--format auto`: an interactive terminal gets a readable
table, while redirected output is deterministic JSON. Explicit formats are
`auto`, `table`, `markdown`, and `json`; `table` currently uses the same stable
plain Markdown table layout as `markdown`. Wide enumeration records should be
saved as JSON rather than a terminal table.

## Validation

```bash
make validate-changed
make check
```

`make check` runs lint/static checks, pytest, representative object-language
counts for the main support/assignment slices, and the golden network slice. It
intentionally does not run the full `R <= 3`, `L+C <= 5` network census.

On native Windows PowerShell, run the equivalent validation without Make or
Bash:

```powershell
.\scripts\check.ps1
```

## Current regression counts

Important regression values include:

- main assignments: **1,166,714**
- main assigned-support classes: **830,094**
- golden assignments: **1,830**
- golden assigned-support classes: **1,112**
- golden local-SP networks: **313**

The golden network table for `R <= 2`, `L+C <= 3` is committed in
`data/counts/small-r2-x3.json` and described in `docs/counts/small-r2-x3.md`.
RICE local-SP counts are not Ladenheim rational-immittance classes; literature
benchmarks such as 148, 108 and 62 remain research context for later analysis.
