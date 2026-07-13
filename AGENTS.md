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
.venv/bin/python -m rice count supports --max-support-edges 8
.venv/bin/python -m rice count assignments --profile main
.venv/bin/python -m rice count assigned-supports --profile main
.venv/bin/python -m rice count networks --profile golden
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


## Proportionate validation

Use the repository change-aware validation command by default after changes:

```bash
make validate-changed
```

This command is backed by `scripts/validate_changes.py` and
`validation/impact.toml`. Documentation-only changes in known public
documentation paths such as `README.md` and `docs/**` do not require pytest or
`make check`; the docs profile runs whitespace checking and plan-index
structural validation. If documentation changes a generated numerical result,
executable CLI example, behavioural claim, or installation instruction, also run
the targeted executable command needed to verify that claim, or force full
validation with `.venv/bin/python scripts/validate_changes.py --full` when in
doubt. Unknown or unclassified paths escalate to full validation.

Do not run commands separately when a broader command already includes them. In
particular, `make check` already includes the repository's normal lint/static
checks, pytest suite, support census, bundle assignment census, labeling census,
and small golden reduced-topology census. Codex setup and maintenance scripts
prepare the environment and run only an import/version smoke test; they do not
certify a task's changes.

## Current CLI language

The provisional command language is discoverable from help. `rice`, `rice -h`,
and `rice --help` all print the top-level map. Bare `rice count` and `rice enum`
print group help; they must not run any legacy no-subcommand count. The preferred
help convention is `rice help`, `rice help count`, and
`rice help count supports`, while normal trailing `--help` remains supported and
`rice --help count supports` is normalized to the same leaf help.

Documented output formats are `auto`, `table`, `markdown`, and `json`. `auto`
uses a readable table for an interactive terminal and deterministic JSON when
redirected.

## CLI changes

After changing argument parsing, run the relevant CLI help commands and check
that the output is correct and reasonable. Check both top-level help and any
changed subcommand help, for example:

```bash
.venv/bin/python -m rice --help
.venv/bin/python -m rice count --help
.venv/bin/python -m rice count networks --help
```

Whenever CLI syntax changes, update README and docs examples in the same
change. Keep examples explicit about option placement: subcommand options go
after the subcommand name; a subcommand (`count <object>`) is always required, and there is no no-subcommand form.

## Codex cloud expectations

A Codex Cloud environment should run the repository scripts:

```bash
bash .codex/setup.sh
bash .codex/maintenance.sh
```

The setup script creates `.venv`, installs the package and dev dependencies into
that venv, appends a guarded activation stanza to `~/.bashrc`, runs a short
import/version smoke test, and records a cache-local environment fingerprint
under `.venv/`.

The maintenance script reuses `.venv` in cached environments, compares the
current Python/package-input fingerprint with the stored `.venv` fingerprint,
skips the editable-install refresh when those inputs are unchanged, refreshes
safely when they have changed, and runs only the same smoke test.

No external graph-generation binaries such as nauty/Traces are required for the
current project direction. The current implementation uses NetworkX only. The supported/tested runtime floor is `networkx>=3.2` on Python 3.11 or newer; do not add unnecessary upper bounds.

## Current validation commands

These validate the current source as it stands. make check, ./scripts/check.sh, and
.\scripts\check.ps1 are the full currently documented validation paths and run
lint/static checks, tests, support, bundle-type, bundle-set, assignment, assigned-support, and golden network object-language counts.

```bash
make check
```

or explicitly:

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m rice count supports --max-support-edges 8
.venv/bin/python -m rice count assignments --profile main
.venv/bin/python -m rice count assigned-supports --profile main
.venv/bin/python -m rice count networks --profile golden
```

The legacy multiset-bundle counter (`count_networks`, `CountResult`, the old
non-object `rice count` form, the no-subcommand form, and `--mode`) has been
removed in full
(`docs/plan/02-cleanup/02-legacy.md`); `legacy-count` is no longer a
`make check`/script target. Its historical totals — `lc` mode total
`1,408,796` (exactly `R=3` total `1,268,282`), and the previously-removed
`generic` mode total `57,945` (exactly `R=3` total `51,736`) — are recorded,
clearly labelled as historical, in `docs/results.md`. They are not
reproducible by any current command and are not part of the active
validation contract.

## Implementation status and remaining work

All five reduced-model stages described below are implemented:

1. Support graph census (`rice count supports` / `support_census`).
2. Raw bundle assignment census (`rice count assignments` /
   `assignment_census`).
3. Assigned-support orbit census (`rice count assigned-supports` /
   `assigned_support_census`).
4. Local canonical reduced signatures for individual assigned two-terminal
   networks (`canonical_reduced_signature`, `ReducedFactor`,
   `ReducedSignature`).
5. End-to-end local-SP network census for the committed small golden slice
   `R <= 2`, `L+C <= 3` (`rice count networks` / `network_census`).

The definitions and golden tables below remain the normative reference for
each stage's contract; they are not prospective instructions.

Remaining work (see the plan index, `docs/plan/00-index.md`, for task-level
detail):

- larger named slices beyond the small golden slice (`docs/plan/05-slices/`);
- performance and output-size review before attempting larger budgets;
- the Ladenheim comparison slice (`docs/plan/03-counting/05-ladenheim.md`,
  `docs/plan/05-slices/02-ladenheim.md`);
- full `R <= 3`, `L+C <= 5` execution (`docs/plan/05-slices/04-r3-x5.md`);
- Ladenheim descriptor/catalogue outputs and reduction comparisons
  (`docs/plan/04-ladenheim/`);
- later Bott-Duffin redundancy and other named features (`docs/plan/09-later/`).

### Phase 1: support graph census

Implemented as `rice count supports` / `support_census`. It:

1. enumerates connected unlabelled simple support graphs up to a configurable
   edge bound;
2. enumerates distinct unordered two-terminal labellings of each support graph;
3. filters terminal-relevant two-terminal support graphs;
4. reports counts by support-edge count for all three categories.

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

Implemented as `rice count assignments` / `assignment_census`. It assigns
only valid simple primitive bundles to support edges:

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

Assigned-support counting is implemented as `rice count assigned-supports`. It removes assigned-support
isomorphism only: simple-bundle assignments are quotiented by support
automorphisms that preserve the unordered terminal pair, including terminal
reversal. For `R <= 3, L+C <= 5`, this preserves `1,166,714` raw leaves and
reports `830,094` canonical bundle-labeling orbits. This is not the final
reduced-topology count.

### Local canonical reduced signatures and end-to-end census

Implemented as `canonical_reduced_signature` (per-network local series/parallel
reduction) and `rice count networks` / `network_census` (full enumeration
and signature merging across a budget slice). `rice count networks` currently
enumerates and merges the committed small golden slice `R <= 2`, `L+C <= 3`
when called with `--profile golden` (see `docs/results.md`); running it
against the full `R <= 3`,
`L+C <= 5` slice is tracked as remaining work
(`docs/plan/05-slices/04-r3-x5.md`), not an unimplemented code path.

Boundary tests (implemented in `tests/test_reduced_signatures.py`):

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
