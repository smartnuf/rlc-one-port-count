# Computation notes

This document separates the current legacy computation from the intended reduced
computation.

## Legacy computation currently implemented

The current source counts isomorphism classes of connected undirected
two-terminal multigraphs by:

1. enumerating connected unlabelled simple support graphs;
2. choosing unordered terminal-pair representatives;
3. rejecting terminal pairs whose support edges are not all on simple
   terminal-to-terminal paths;
4. assigning non-empty component-count bundles to support edges;
5. quotienting those assignments by terminal-set-preserving automorphisms using
   Burnside's lemma.

In legacy `lc` mode, a support-edge bundle is `(r, l, c)` with arbitrary
non-negative counts subject to the global budget. Thus the legacy model counts
`R||R` separately from `R`.

Legacy results are recorded in `docs/results.md`.

## Reduced computation target

The intended next model counts reduced two-terminal RLC topology classes. See
`docs/model_decisions.md` for the full contract.

The main changes are:

- simple primitive bundles only: `R`, `L`, `C`, `R||L`, `R||C`, `L||C`,
  `R||L||C`;
- no generated duplicate primitive parallel branches such as `R||R`;
- local series spans commute;
- duplicate primitive singleton factors merge in both series and parallel
  compositions;
- duplicate compound subnetworks do not merge.

The reduced model should be implemented in stages.

## Stage 1: support graph census

Before changing component assignment, implement a support-only census:

1. enumerate basic connected unlabelled simple support graphs;
2. enumerate unordered two-terminal labellings of each basic graph;
3. reject terminal-irrelevant terminal labellings;
4. report counts by support-edge number.

For `max_edges = 8`, expected counts are:

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

A terminal-irrelevant graph is rejected as a whole. It is not pruned into a
smaller accepted graph.

Run the census with subcommand options after `supports`:

```bash
.venv/bin/python -m rice supports --max-edges 8
.venv/bin/python -m rice supports --max-r 3 --max-reactive 5
```

The second form derives `max_edges = max_r + max_reactive`. Do not use the
legacy no-subcommand count form for support census commands.

## Stage 2: simple bundle assignment

After support graph census is stable, assign only simple primitive bundles:

```text
R
L
C
R||L
R||C
L||C
R||L||C
```

For `R <= 3, L+C <= 5`, run `.venv/bin/python -m rice bundles --max-r 3 --max-reactive 5`. The command derives `max_edges = max_r + max_reactive`; optional `--max-edges` is only for debugging/truncation and cannot exceed that derived bound. The raw assignment leaf bound before isomorphism or reduced-signature merging is **1,166,714**.

This is small enough to permit straightforward enumeration for the first reduced
implementation.

## Stage 3: reduced signatures

The final reduced count should use canonical signatures rather than raw graph
assignment counts.

At minimum, the signature layer must satisfy:

```text
R--L == L--R
R--L--C == C--R--L
R--R--L == R--L
R||R == R
L||L == L
C||C == C
R||L != R--L
(R--L)||C != R||L||C
(R--L)||(R--L) != R--L
(R||L)--(R||L) != R||L
```

A series span is local. It can be an arm inside a parallel network and does not
need to lie on every simple terminal-to-terminal path.

## What the reduced computation should not do

Do not implement general electrical equivalence as part of this phase. In
particular, do not collapse networks via:

- Y-Delta transformations;
- bridge-balance simplifications;
- Foster/Cauer equivalence;
- duality;
- algebraic equality of rational impedances.
