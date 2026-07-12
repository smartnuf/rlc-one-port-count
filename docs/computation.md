# Computation notes

This document explains the historical legacy multiset-bundle computation that
the reduced model replaced, then documents the reduced computation's staged
implementation.

## Historical: legacy computation (removed)

The legacy counter, now removed in full (`docs/plan/02-cleanup/02-legacy.md`),
counted isomorphism classes of connected undirected two-terminal multigraphs
by:

1. enumerating connected unlabelled simple support graphs;
2. choosing unordered terminal-pair representatives;
3. rejecting terminal pairs whose support edges are not all on simple
   terminal-to-terminal paths;
4. assigning non-empty component-count bundles to support edges;
5. quotienting those assignments by terminal-set-preserving automorphisms using
   Burnside's lemma.

In legacy `lc` mode, a support-edge bundle was `(r, l, c)` with arbitrary
non-negative counts subject to the global budget. Thus the legacy model
counted `R||R` separately from `R`.

Historical legacy results are recorded, clearly labelled as historical, in
`docs/results.md`.

## Reduced computation

The reduced model counts reduced two-terminal RLC topology classes. See
`docs/model_decisions.md` for the full contract.

The main differences from the historical legacy model above are:

- simple primitive bundles only: `R`, `L`, `C`, `R||L`, `R||C`, `L||C`,
  `R||L||C`;
- no generated duplicate primitive parallel branches such as `R||R`;
- local series spans commute;
- duplicate primitive singleton factors merge in both series and parallel
  compositions;
- duplicate compound subnetworks do not merge.

The reduced model is implemented in stages.

## Stage 1: support graph census

Implemented as `rice count supports` / `support_census`, a support-only census:

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
.venv/bin/python -m rice count supports --max-support-edges 8
.venv/bin/python -m rice count supports --profile main
```

The second form derives `max_edges = max_r + max_reactive`. Subcommand
options must go after `supports`; there is no no-subcommand form.

## Stage 2: simple bundle assignment

Implemented as `rice count assignments` / `assignment_census`, assigning
only simple primitive bundles:

```text
R
L
C
R||L
R||C
L||C
R||L||C
```

For `R <= 3, L+C <= 5`, run `.venv/bin/python -m rice count assignments --profile main`. The command derives `max_edges = max_r + max_reactive`; optional `--max-edges` is only for debugging/truncation and cannot exceed that derived bound. Zero/zero budgets are a valid empty bundle or labeling census with no support-edge rows; negative budgets are invalid. The raw assignment leaf bound before isomorphism or reduced-signature merging is **1,166,714**.

This is small enough to permit straightforward enumeration for the first reduced
implementation.

## Stage 3: reduced signatures

The final reduced count uses canonical signatures rather than raw graph
assignment counts, implemented as `canonical_reduced_signature` for one
assigned network and, for full enumeration and merging across a budget slice,
`rice count networks` / `network_census` — currently computed and
committed for the small golden slice `R <= 2`, `L+C <= 3`
(`docs/plan/05-slices/04-r3-x5.md` tracks running the full `R <= 3`,
`L+C <= 5` scope through the same enumeration).

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

## Enumeration and provenance implementation

The `rice enum` commands materialize the same exact object stages used by the
count commands. Supports are canonically relabelled before IDs and edge ordering
are assigned. Assignment records place simple primitive bundle labels on that
canonical edge order. Assigned-support records then choose deterministic orbit
representatives using the terminal-set-preserving support automorphism action.
Network records group assigned-support representatives by the local-SP canonical
reduced signature and retain aggregate provenance counts rather than embedding
all sources.

`rice count reductions` aggregates those records instead of reconstructing
provenance from presentation tables. It checks conservation of raw assignments,
assigned-support classes, unique network IDs, and provenance references for the
small/golden queries used in tests. Duplicate primitive reductions such as
`R--R -> R`, `R||R -> R`, and `R--L--R -> R--L` appear as component transitions
from larger exact source tuples to smaller reduced tuples.
