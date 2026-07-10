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

The source currently implements a **legacy multiset-bundle counter**. That counter
is useful as a first reference point, but it is intentionally being replaced by a
more useful **reduced-topology** model.

The new direction is documented before implementation so that Codex/agentic
phases have a clear target:

- [`docs/model_decisions.md`](docs/model_decisions.md) defines the intended
  counting contract and boundary cases.
- [`docs/support_graph_enumeration.md`](docs/support_graph_enumeration.md)
  defines the first implementation milestone: support-graph census and
  terminal-relevance filtering.
- [`docs/bundles_and_multiedges.md`](docs/bundles_and_multiedges.md) explains
  legacy multiset bundles and the intended replacement by simple primitive
  bundles and series spans.
- [`docs/simple_path_coverage.md`](docs/simple_path_coverage.md) documents the
  terminal-relevance test.

Implemented reduced-model stages now include `rice supports` for phase 1
terminal-relevant supports, `rice bundles` for phase 2 raw simple-bundle
assignment leaves, and `rice labelings` for phase 3 canonical bundle-labeling
orbits under internal-node renaming and reversal of the unordered terminal pair.
Local series-span reductions and recursive reduced signatures are available as a focused API for individual assigned networks; full signature enumeration and merging remain future work.

## Current legacy results

The current source counts raw graph-topology classes using support graphs and
parallel component-count bundles. In that model, repeated same-type parallel
branches such as `R || R` are counted separately from a single `R` branch.

For `R <= 3, L + C <= 5`, with L and C distinct, the legacy result is:

- **1,408,796** networks with **at most 3 R** and **at most 5 L+C**;
- **1,268,282** networks with **exactly 3 R** and **at most 5 L+C**.

For `R <= 3, X <= 5`, where all reactive elements are treated as one generic
`X`, the legacy result is:

- **57,945** networks with **at most 3 R** and **at most 5 X**;
- **51,736** networks with **exactly 3 R** and **at most 5 X**.

These numbers are retained as a regression/reference for the legacy counter.
They should not be treated as the final target count for the reduced-topology
model.

## Intended reduced-topology model

The intended model counts reduced two-terminal RLC one-port topologies rather
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
- local series chains/spans are intended to commute: `R--L` and `L--R` should
  have the same reduced signature;
- duplicate primitive singleton factors in a series span merge: `R--A--R`
  reduces to `A--R`;
- duplicate compound subnetworks do not merge: `A--A` is not reduced to `A`
  unless `A` is a primitive singleton `R`, `L`, or `C`.

The reduced model is deliberately not a full electrical-equivalence solver. It
does not attempt Y-Delta transformations, bridge balance simplifications,
duality, Foster/Cauer equivalences, or rational impedance equality.

## First implementation milestone

Before changing component assignment or reduced signatures, implement the
support-graph census described in [`docs/support_graph_enumeration.md`](docs/support_graph_enumeration.md).

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

Run the support-census smoke check, phase-2 raw bundle-assignment smoke check, and current legacy counts:

```bash
make check
```

The equivalent explicit commands are:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip setuptools wheel
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/python -m pytest -q
.venv/bin/python -m rice supports --max-edges 8
.venv/bin/python -m rice supports --max-r 3 --max-reactive 5
.venv/bin/python -m rice bundles --max-r 3 --max-reactive 5
.venv/bin/python -m rice labelings --max-r 3 --max-reactive 5
.venv/bin/python -m rice --mode lc --max-r 3 --max-reactive 5
.venv/bin/python -m rice --mode generic --max-r 3 --max-reactive 5
```

`make check` includes `legacy-generic` only while generic-X support remains present.
A future generic-removal PR should remove that target from `make check` together
with `--mode generic` and the matching documentation/results entries.

The primary installed console script can also be run explicitly from the venv.
Subcommand options go after the subcommand:

```bash
.venv/bin/rice supports --max-edges 8
.venv/bin/rice supports --max-r 3 --max-reactive 5
.venv/bin/rice bundles --max-r 3 --max-reactive 5
.venv/bin/rice labelings --max-r 3 --max-reactive 5
.venv/bin/rice count --mode lc --max-r 3 --max-reactive 5
```

The legacy no-subcommand count form is retained for compatibility only:

```bash
.venv/bin/rice --mode lc --max-r 3 --max-reactive 5
```

The `bundles` command reports raw phase-2 simple primitive bundle-assignment
leaves before support-automorphism quotienting or reduced-signature merging; it
is not a final reduced-topology count. Its normal interface derives the support
edge bound as `max_edges = max_r + max_reactive`. An optional `--max-edges` flag
may be supplied after `bundles` only for debugging/truncation, and values greater
than the derived component-budget bound are rejected.

Do not put support-census options before `supports`; for example,
`.venv/bin/rice --max-edges 8 supports` is not valid. Count-budget options
before `supports` are rejected rather than silently ignored.

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


The `labelings` command reports phase-3 canonical bundle-labeling orbits. It preserves the phase-2 raw leaf total and additionally quotients assignments by automorphisms of each terminal-relevant support that preserve the unordered terminal pair, including automorphisms that swap the terminals. For `R <= 3, L+C <= 5`, the standard slice has **1,166,714** raw leaves and **830,094** canonical bundle-labeling orbits. This is still not a final reduced-topology count: local series-span reductions and recursive reduced signatures are now available only as a focused per-network API, while full standard-slice signature enumeration and merging remain deliberately deferred.
