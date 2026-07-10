# AGENTS.md

Guidance for Codex or other coding agents working on this repository.

## Project purpose

This repository counts small two-terminal RLC one-port topology classes. The
reference problem is:

```text
R <= 3
L + C <= 5
```

The current source implements the reduced-topology model described below. An
earlier legacy multiset-bundle counter has been removed in full
(`docs/plan/02-cleanup/02-legacy.md`); its historical counts are recorded,
clearly labelled as historical, in `docs/results.md`. Treat the docs below as
the normative specification for new work:

1. `docs/model_decisions.md` — counting contract, reductions, boundary cases.
2. `docs/support_graph_enumeration.md` — first implementation milestone.
3. `docs/bundles_and_multiedges.md` — bundle/span terminology and the
   historical multiset-bundle model it replaced.
4. `docs/simple_path_coverage.md` — terminal relevance and whole-graph rejection.
5. `docs/results.md` — historical legacy counts and support-census target
   counts.

If code and docs disagree, do not silently preserve the old behaviour. Either
update the code to the documented model or explicitly mark the old behaviour as
historical.

## Plan index maintenance

Keep `docs/plan/00-index.md` grouped by its numbered subdirectories. Each top-level
index heading must list all and only the task files in the matching subdirectory
for that group. For example, `## 00 — ...` lists only files under
`docs/plan/00-records/`, `## 07 — ...` lists only files under
`docs/plan/07-tests/`, and `## 08 — ...` lists only files under
`docs/plan/08-docs/`. If a task belongs in a different group, rename or move the
file and update the index rather than cross-linking it from the wrong group.

## Plan record maintenance

Agents should keep the plan records current as implementation changes are made.
Before substantive changes, check the relevant plan documents under
`docs/plan/00-index.md` and `docs/plan/*/*`; most task prompts will reference a
specific plan document. After substantive changes, update the relevant plan
status and notes: use `todo` for unstarted work, `prog` for in-progress or
partially completed work, and `done` only when the work is implemented, tested,
and documented sufficiently. Not every task is intended to move an item to
`done`. Add concise progress notes against the relevant plan document, and
expand near-term plan steps as the implementation path becomes clearer.

## Development environment

Use Python 3.11 or newer.

This repository uses an explicit local virtual environment at `.venv`. Do not
rely on `source .venv/bin/activate` or `.venv\Scripts\Activate.ps1` persisting
between shell sessions. In Codex Cloud, setup scripts and task commands may run
in separate shells, so plain `python`, `python -m pytest`, and `pytest` can
accidentally use the non-venv interpreter.

Preferred setup and validation commands:

```bash
make setup
make test
make lint
make check
```

Supported non-Make Linux/WSL shell scripts are also available:

```bash
./scripts/setup.sh
./scripts/test.sh
./scripts/lint.sh
./scripts/check.sh
./scripts/clean.sh
```

The shell scripts must be run from the repository root. They validate that
location before making environment-sensitive changes or deleting generated
artefacts.

Native Windows PowerShell scripts are available without Make, Bash, WSL, or
activation:

```powershell
.\scripts\setup.ps1
.\scripts\test.ps1
.\scripts\lint.ps1
.\scripts\check.ps1
.\scripts\clean.ps1
```

The PowerShell scripts must also be run from the repository root and use
`.venv\Scripts\python.exe` explicitly after setup.

Equivalent explicit commands:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip setuptools wheel
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/python -m pytest -q
.venv/bin/python -m rice supports --max-edges 8
.venv/bin/python -m rice bundles --max-r 3 --max-reactive 5
.venv/bin/python -m rice labelings --max-r 3 --max-reactive 5
.venv/bin/python -m rice reduced --max-r 2 --max-reactive 3
```

Do not run these ambiguous commands in Codex tasks:

```bash
pytest
python -m pytest
python -m pip install -e ".[dev]"
```

If dependencies are missing, do not install them into the system interpreter.
Use .venv/bin/python -m pip ... on Linux/WSL, .venv\Scripts\python.exe -m pip ... on Windows, or rerun the repository setup
script.

Do not commit `.venv/`, `__pycache__/`, build artefacts, or generated archives.

## CLI changes

After changing argument parsing, run the relevant CLI help commands and check
that the output is correct and reasonable. Check both top-level help and any
changed subcommand help, for example:

```bash
.venv/bin/python -m rice --help
.venv/bin/python -m rice supports --help
.venv/bin/python -m rice reduced --help
```

Whenever CLI syntax changes, update README and docs examples in the same
change. Keep examples explicit about option placement: subcommand options go
after the subcommand name; a subcommand (`supports`, `bundles`, `labelings`,
or `reduced`) is always required, and there is no no-subcommand form.

## Codex cloud expectations

A Codex Cloud environment should run the repository scripts:

```bash
bash .codex/setup.sh
bash .codex/maintenance.sh
```

The setup script creates `.venv`, installs the package and dev dependencies into
that venv, appends a guarded activation stanza to `~/.bashrc`, and runs the test
suite through `.venv/bin/python`.

The maintenance script reuses `.venv` in cached environments, refreshes the
editable install without fetching dependencies, and runs the same venv-explicit
checks.

No external graph-generation binaries such as nauty/Traces are required for the
current project direction. The current implementation uses NetworkX only. The supported/tested runtime floor is `networkx>=3.2` on Python 3.11 or newer; do not add unnecessary upper bounds.

## Current validation commands

These validate the current source as it stands. make check, ./scripts/check.sh, and
.\scripts\check.ps1 are the full currently documented validation paths and run
lint/static checks, tests, support census, bundle assignment census, labeling
census, and the small golden reduced-topology census.

```bash
make check
```

or explicitly:

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m rice supports --max-edges 8
.venv/bin/python -m rice bundles --max-r 3 --max-reactive 5
.venv/bin/python -m rice labelings --max-r 3 --max-reactive 5
.venv/bin/python -m rice reduced --max-r 2 --max-reactive 3
```

The legacy multiset-bundle counter (`count_networks`, `CountResult`,
`rice count`, the no-subcommand form, and `--mode`) has been removed in full
(`docs/plan/02-cleanup/02-legacy.md`); `legacy-count` is no longer a
`make check`/script target. Its historical totals — `lc` mode total
`1,408,796` (exactly `R=3` total `1,268,282`), and the previously-removed
`generic` mode total `57,945` (exactly `R=3` total `51,736`) — are recorded,
clearly labelled as historical, in `docs/results.md`. They are not
reproducible by any current command and are not part of the active
validation contract.

## Near-term implementation sequence

The support, bundle, and assigned-support labeling stages are implemented.
Current reduced-signature work should stay focused on local per-network
canonicalisation before adding full standard-slice signature enumeration and
merging.

### Phase 1: support graph census

Implement and test:

1. enumerate connected unlabelled simple support graphs up to a configurable
   edge bound;
2. enumerate distinct unordered two-terminal labellings of each support graph;
3. filter terminal-relevant two-terminal support graphs;
4. report counts by support-edge count for all three categories.

Definitions for phase 1:

- A **basic support graph** is connected, loopless, simple, and unlabelled.
- A **two-terminal basic graph** is a basic support graph with an unordered pair
  of distinct terminal nodes.
- Terminal reversal must not create a distinct two-terminal graph.
- Internal node renaming must not create a distinct graph.
- A two-terminal basic graph is **terminal-relevant** iff every support edge lies
  on at least one simple path between the two terminals.
- If a terminal-labelled support graph has a dangling tree or pendant blob,
  reject the whole terminal-labelled graph. Do not prune it into a smaller graph.

For `max_edges=8`, the expected census is:

| Support edges | Basic connected unlabelled graphs | Unordered two-terminal labelings | Terminal-relevant two-terminal graphs |
|---:|---:|---:|---:|
| 1 | 1 | 1 | 1 |
| 2 | 1 | 2 | 1 |
| 3 | 3 | 7 | 2 |
| 4 | 5 | 21 | 4 |
| 5 | 12 | 73 | 10 |
| 6 | 30 | 255 | 27 |
| 7 | 79 | 946 | 80 |
| 8 | 227 | 3,618 | 258 |
| **Total** | **358** | **4,923** | **383** |

#### Validation commands

```bash
make test
make check
```

### Phase 2: simple bundle assignment

After phase 1 is stable, assign only valid simple primitive bundles to support
edges:

```text
R
L
C
R||L
R||C
L||C
R||L||C
```

Do not generate `R||R`, `L||L`, `C||C`, or other duplicate same-type primitive
parallel branches in the reduced model.

For `R <= 3, L+C <= 5`, the expected count of raw assignment leaves before
isomorphism/signature merging is:

| Support edges | Relevant supports | Valid bundle assignments per support | Leaf assignments |
|---:|---:|---:|---:|
| 1 | 1 | 7 | 7 |
| 2 | 1 | 49 | 49 |
| 3 | 2 | 335 | 670 |
| 4 | 4 | 1,622 | 6,488 |
| 5 | 10 | 4,602 | 46,020 |
| 6 | 27 | 7,192 | 194,184 |
| 7 | 80 | 5,712 | 456,960 |
| 8 | 258 | 1,792 | 462,336 |
| **Total** | **383** | — | **1,166,714** |

### Phase 3: assigned-support bundle-labeling orbits

Phase 3 is implemented as `rice labelings`. It removes assigned-support
isomorphism only: simple-bundle assignments are quotiented by support
automorphisms that preserve the unordered terminal pair, including terminal
reversal. For `R <= 3, L+C <= 5`, this preserves `1,166,714` raw leaves and
reports `830,094` canonical bundle-labeling orbits. This is not the final
reduced-topology count.

### Current reduced-signature stage

After phase 3, the code adds canonical reduced-topology signatures for
individual assigned two-terminal networks by applying the documented local
series and parallel rules. Full signature enumeration and merging across the
standard slice remains a later stage.

Required boundary tests:

```text
R--L == L--R
R--L--C == C--R--L
R--R--L == R--L
R||R == R
L||L == L
C||C == C
R||L != R--L
(R--L)||C != R||L||C
(R--L)||C reduces the R--L arm even though that arm is not on every terminal path
(R--L)||(R--L) != R--L
(R||L)--(R||L) != R||L
terminal reversal gives the same signature
internal node renaming gives the same signature
dangling branches are rejected
pendant blobs are rejected
```

## Counting model cautions

- Terminal relevance is a filter on a terminal-labelled support graph. Reject the
  whole object if it fails; do not prune dangling material.
- Series spans are local two-valent runs. They need only lie on at least one
  simple terminal-to-terminal path, not every terminal path.
- Do not use terminal-separating articulation nodes as the only way to find
  series spans; that would miss series arms inside parallel structures such as
  `(R--L)||C`.
- The reduced model is not a full electrical-equivalence solver. Do not attempt
  Y-Delta transforms, bridge-balance simplifications, duality, Foster/Cauer
  equivalence, or rational impedance equality unless a later task explicitly
  asks for that.
