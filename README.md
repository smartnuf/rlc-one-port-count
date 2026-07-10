# RICE — Resistor-Inductor-Capacitor Enumerator

RICE — Resistor-Inductor-Capacitor Enumerator — enumerates, catalogues,
and counts small connected two-terminal RLC one-port topology classes. It was created around the case:

> **R <= 3, L + C <= 5**, with inductors and capacitors treated as distinct component types.

## Motivation

Classical network synthesis asks an inverse question: given a prescribed
driving-point immittance, what passive network topologies can realise it? For
RLC one-ports this links graph topology, component type, positive-real rational
functions, and minimal realisation. Even for low-degree functions, the difficult
question is often not merely whether a realisation exists, but which finite set
of network forms must be considered before claims about minimality,
sufficiency, or necessity are credible.

This repository is therefore concerned with **catalogues**, not just totals.
Counts are valuable because they act as reproducible checksums for a catalogue,
but the catalogue itself is the useful object: it can be inspected, searched,
rendered, compared with historical lists, converted to descriptors, tested for
its immittance, and grouped into equivalence classes or generator sets.

The immediate historical benchmark is the Ladenheim catalogue of RLC one-port
networks with no more than two reactive elements and no more than three
resistors. In the terminology used here, that comparison slice is:

```text
R <= 3
L + C <= 2
R + L + C <= 5
```

The literature around Ladenheim, Kalman, Morelli, Hughes, and Smith motivates a
deliberately enumerative approach. Morelli's reworking of the Ladenheim problem
distinguishes an unabridged set of 148 candidate networks, the canonical
108-network Ladenheim catalogue, and a further grouping into 62 equivalence
classes. That separation is important for this project: different notions of
"distinct" produce different valid catalogues.

The project will therefore keep the following ideas separate:

- **counting**: producing totals for a specified class;
- **enumeration**: generating every candidate object in that class;
- **cataloguing**: storing stable representatives, identifiers, metadata, and
  outputs;
- **reduced-topology distinctness**: quotienting by graph isomorphism, terminal
  reversal, and documented local reductions;
- **genericity and rejection rules**: excluding forms that are trivial,
  degenerate, or non-generic under a stated criterion;
- **equivalence classes**: grouping catalogued networks under named
  transformations or immittance equivalence;
- **generator sets**: finding smaller sets from which larger families can be
  produced.

Several natural sufficiency questions are intentionally treated as open
investigations here. In particular, this repository should not assume that any
of the following are already known to realise every biquadratic immittance:

```text
R <= 2, L + C <= 5
R <= 5, L + C <= 3
series-parallel networks with R + L + C <= 8
```

Those bounds are useful named slices for exploration, comparison, and
regression testing, but their sufficiency or insufficiency must be established
by documented arguments or counterexamples, not by assumption.


## Status

The **reduced-topology model** is the current implementation. It counts
two-terminal RLC one-port topology classes after local primitive series and
parallel redundancies have been removed. It replaces an earlier legacy
multiset-bundle counter, which has since been removed in full
(`docs/plan/02-cleanup/02-legacy.md`); the removed counter's historical
totals are recorded, clearly labelled as historical, in
[`docs/results.md`](docs/results.md).

The model is documented in:

- [`docs/model_decisions.md`](docs/model_decisions.md) defines the counting
  contract and boundary cases.
- [`docs/support_graph_enumeration.md`](docs/support_graph_enumeration.md)
  defines the support-graph census and terminal-relevance filtering that
  every later stage builds on.
- [`docs/bundles_and_multiedges.md`](docs/bundles_and_multiedges.md) explains
  the historical legacy multiset bundles and the simple primitive bundles and
  series spans that replaced them.
- [`docs/simple_path_coverage.md`](docs/simple_path_coverage.md) documents the
  terminal-relevance test.

Implemented reduced-model stages now include `rice supports` for phase 1
terminal-relevant supports, `rice bundles` for phase 2 raw simple-bundle
assignment leaves, and `rice labelings` for phase 3 canonical bundle-labeling
orbits under internal-node renaming and reversal of the unordered terminal pair.
Local series-span reductions and recursive reduced signatures are available as a focused API for individual assigned networks. The first complete end-to-end reduced-topology census is implemented as `rice reduced` for the small golden slice `R <= 2`, `L+C <= 3`; the full `R <= 3`, `L+C <= 5` reduced catalogue remains future work.

The supported Python API (`support_census`, `simple_bundle_assignment_census`,
`simple_bundle_labeling_census`, `canonical_reduced_signature`,
`reduced_topology_census`, and their result types) is documented with small
runnable examples in [`docs/python_api.md`](docs/python_api.md).

## Migration from the removed legacy counter

The legacy multiset-bundle counter (`rice count`, `--mode`, and the
no-subcommand compatibility form) has been removed
(`docs/plan/02-cleanup/02-legacy.md`). `rice reduced` is the closest
supported replacement, but the two are **not numerically equivalent**
counting contracts: the reduced model excludes or merges additional raw
representations that the legacy counter treated as distinct (for example,
repeated same-type primitive parallel branches such as `R||R` are not
generated as separate reduced topologies), so reduced-topology counts are
generally lower than the old multiset-bundle counts for a given `R`/`L+C`
budget. This is a difference in what is being counted, not a fixed scaling
factor, and reduced counts should not be assumed strictly smaller for every
possible budget slice.

```bash
.venv/bin/python -m rice reduced --max-r 2 --max-reactive 3
```

The removed counter's historical totals (both its `lc` mode and its
previously-removed `generic` mode) are recorded, clearly labelled as
historical, in [`docs/results.md`](docs/results.md).

## Reduced-topology model

The reduced model counts reduced two-terminal RLC one-port topologies rather
than every raw multigraph drawing. The guiding decisions are:

- terminals form an unordered pair, so terminal reversal does not create a new
  topology;
- internal node names are irrelevant;
- self-loops are not permitted;
- a two-terminal support graph is accepted only if every support edge lies on at
  least one simple terminal-to-terminal path;
- terminal-irrelevant support graphs are rejected as whole objects, not pruned;
- simple primitive parallel bundles are used: `R`, `L`, `C`, `R||L`, `R||C`,
  `L||C`, `R||L||C`;
- repeated primitive same-type parallel branches, such as `R||R`, are not
  generated in the reduced model;
- local series chains/spans commute: `R--L` and `L--R` have the same reduced
  signature;
- duplicate primitive singleton factors in a series span merge: `R--A--R`
  reduces to `A--R`;
- duplicate compound subnetworks do not merge: `A--A` is not reduced to `A`
  unless `A` is a primitive singleton `R`, `L`, or `C`.

The reduced model is deliberately not a full electrical-equivalence solver. It
does not attempt Y-Delta transformations, bridge balance simplifications,
duality, Foster/Cauer equivalences, or rational impedance equality.

## Support-graph census

Every later stage builds on the support-graph census described in
[`docs/support_graph_enumeration.md`](docs/support_graph_enumeration.md).

For `max_edges = 8`, the expected census is:

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

## Use

This repository deliberately uses an explicit local virtual environment for all
commands. Do not rely on `source .venv/bin/activate` persisting between shells.

Create or refresh the environment:

```bash
make setup
```

`make install` remains available temporarily as a compatibility alias.

Run the tests:

```bash
make test
```

Run the support-census smoke check, phase-2 raw bundle-assignment smoke check, phase-3 labeling smoke check, and the small golden reduced-topology census:

```bash
make check
```

On Linux, macOS, and WSL, the same development path is available without Make
through repository-root shell scripts:

```bash
./scripts/setup.sh
./scripts/test.sh
./scripts/lint.sh
./scripts/check.sh
./scripts/clean.sh
```

These scripts validate that they are being run from the repository root, are
kept compatible with Bash 3.2 for the system Bash on older macOS releases, use
`.venv/bin/python` explicitly after setup, and print the Python executable in
use. `setup.sh` selects Python 3.11 or newer only after verifying that the
interpreter can create virtual environments.

On native Windows PowerShell, use the repository-root PowerShell scripts:

```powershell
.\scripts\setup.ps1
.\scripts\test.ps1
.\scripts\lint.ps1
.\scripts\check.ps1
.\scripts\clean.ps1
```

The PowerShell path uses `.venv\Scripts\python.exe` explicitly after setup,
selects Python 3.11 or newer with working `venv` support through the Windows
launcher or `python.exe`, and does not require Make, Bash, WSL, or
virtual-environment activation. If local execution
policy blocks a script, prefer a process-scoped policy for that shell:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

A single script can also be verified with a one-process invocation:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\test.ps1
```

The equivalent explicit commands are:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip setuptools wheel
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/python -m pytest -q
.venv/bin/python -m rice supports --max-edges 8
.venv/bin/python -m rice bundles --max-r 3 --max-reactive 5
.venv/bin/python -m rice labelings --max-r 3 --max-reactive 5
.venv/bin/python -m rice reduced --max-r 2 --max-reactive 3
.venv/bin/python -m rice reduced --max-r 2 --max-reactive 3 --format json
```

The legacy multiset-bundle counter (`rice count`, `--mode`, and the
no-subcommand form) has been removed
(`docs/plan/02-cleanup/02-legacy.md`); a subcommand is now required.

The primary installed console script can also be run explicitly from the venv.
Subcommand options go after the subcommand:

```bash
.venv/bin/rice supports --max-edges 8
.venv/bin/rice supports --max-r 3 --max-reactive 5
.venv/bin/rice bundles --max-r 3 --max-reactive 5
.venv/bin/rice labelings --max-r 3 --max-reactive 5
.venv/bin/rice reduced --max-r 2 --max-reactive 3
```

The `bundles` command reports raw phase-2 simple primitive bundle-assignment
leaves before support-automorphism quotienting or reduced-signature merging; it
is not a final reduced-topology count. Its normal interface derives the support
edge bound as `max_edges = max_r + max_reactive`. An optional `--max-edges` flag
may be supplied after `bundles` only for debugging/truncation, and values greater
than the derived component-budget bound are rejected. `bundles` and `labelings`
treat `--max-r 0 --max-reactive 0` as a valid empty census with zero totals and
no support-edge rows; negative budgets and zero/negative explicit edge bounds
when the component budget is nonzero are rejected at the CLI boundary.

Do not put subcommand options before the subcommand name; for example,
`.venv/bin/rice --max-edges 8 supports` is not valid and is rejected rather
than silently ignored. Every option belongs to exactly one subcommand parser,
so a bare `rice` (no subcommand) is also rejected. Long options must use their
exact documented names; argparse abbreviation is disabled for the top-level
parser and all subcommands.

The declared runtime dependency floor is NetworkX 3.2 on Python 3.11 or newer; do not add an upper bound unless a tested incompatibility requires one.

## Codex Cloud scripts

Repository-local Codex setup scripts are provided in `.codex/`:

```bash
bash .codex/setup.sh
bash .codex/maintenance.sh
```

Point the Codex Cloud environment setup command at `bash .codex/setup.sh` and,
if using a cached environment, the maintenance command at
`bash .codex/maintenance.sh`.

## Background references

The immediate bibliography to document more fully is:

- Edward L. Ladenheim, *A Synthesis of Biquadratic Impedances*, Master's
  thesis, Polytechnic Institute of Brooklyn, 1948.
- R. E. Kalman, work on minimal realisation and the role of complete
  enumeration in understanding low-degree passive-network synthesis problems.
- Alessandro Morelli, *Realisation of Positive-Real Functions by Electrical
  Networks*, PhD thesis, University of Cambridge, 2017.
- T. H. Hughes, A. Morelli, and M. C. Smith, "Electrical network synthesis: A
  survey of recent work", in *Emerging Applications of Control and Systems
  Theory*, Springer, 2018.
- T. H. Hughes, "Why RLC realizations of certain impedances need many more
  energy storage elements than expected", 2017.

These references should be expanded into a dedicated literature note before the
project relies on any detailed catalogue or sufficiency claim.


## Repository note

Do not commit a real `.venv` directory. It is platform-specific, can be large,
and is already excluded by `.gitignore`. Commit the source, tests,
documentation, and `pyproject.toml`; recreate `.venv` in each development
environment.


The `labelings` command reports phase-3 canonical bundle-labeling orbits. It preserves the phase-2 raw leaf total and additionally quotients assignments by automorphisms of each terminal-relevant support that preserve the unordered terminal pair, including automorphisms that swap the terminals. For `R <= 3, L+C <= 5`, the standard slice has **1,166,714** raw leaves and **830,094** canonical bundle-labeling orbits. This is still not a final reduced-topology count: local series-span reductions and canonical reduced signatures are applied, and full signature enumeration and merging across a budget slice is implemented as `rice reduced`. Running the full standard `R <= 3`, `L+C <= 5` slice through that enumeration remains future work (`docs/plan/05-slices/04-r3-x5.md`); the committed small golden slice `R <= 2`, `L+C <= 3` is fully computed today.
