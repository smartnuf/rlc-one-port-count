# RLC one-port topology counter

This repository counts small connected two-terminal RLC one-port topology classes.
It was created around the case:

> **R <= 3, L + C <= 5**, with inductors and capacitors treated as distinct component types.

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

Run the support-census smoke check and current legacy counts:

```bash
make check
```

The equivalent explicit commands are:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip setuptools wheel
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/python -m pytest -q
.venv/bin/python -m rlc_oneport_count supports --max-edges 8
.venv/bin/python -m rlc_oneport_count --mode lc --max-r 3 --max-reactive 5
.venv/bin/python -m rlc_oneport_count --mode generic --max-r 3 --max-reactive 5
```

`make check` includes `legacy-generic` only while generic-X support remains present.
A future generic-removal PR should remove that target from `make check` together
with `--mode generic` and the matching documentation/results entries.

The installed console script can also be run explicitly from the venv:

```bash
.venv/bin/rlc-oneport-count --mode lc --max-r 3 --max-reactive 5
```

## Codex Cloud scripts

Repository-local Codex setup scripts are provided in `.codex/`:

```bash
bash .codex/setup.sh
bash .codex/maintenance.sh
```

Point the Codex Cloud environment setup command at `bash .codex/setup.sh` and,
if using a cached environment, the maintenance command at
`bash .codex/maintenance.sh`.

## Repository note

Do not commit a real `.venv` directory. It is platform-specific, can be large,
and is already excluded by `.gitignore`. Commit the source, tests,
documentation, and `pyproject.toml`; recreate `.venv` in each development
environment.
