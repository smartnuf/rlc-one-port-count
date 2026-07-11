# Bundles, multi-edges, and series spans

This document explains the historical legacy bundle model and the reduced
model that replaced it.

## Historical: legacy bundle model (removed)

The legacy counter, now removed in full (`docs/plan/02-cleanup/02-legacy.md`),
represented parallel branches by assigning a component-count bundle to each
edge of a simple support graph.

In legacy `lc` mode, a bundle was:

```text
(r, l, c)
```

where `r`, `l`, and `c` are arbitrary non-negative counts subject to the global
component budget.

Therefore the legacy counter treated these as distinct:

```text
(r=1, l=0, c=0)   one resistor
(r=2, l=0, c=0)   two parallel resistors
```

and similarly for repeated inductors or capacitors. This was a legacy
overcount relative to the reduced-topology model, and is documented here only
as historical background.

## Simple primitive bundles

The reduced model uses only simple primitive bundles. Phase 2 implements these
bundles for the raw assignment census exposed as `rice bundles`. A bundle is a
non-empty subset of `{R, L, C}` between the same two support nodes.

Allowed bundles:

```text
R
L
C
R || L
R || C
L || C
R || L || C
```

Not generated in the reduced model:

```text
R || R
L || L
C || C
R || R || L
R || C || C
```

The reason is that repeated same-type ideal primitive components in direct
parallel reduce to a single primitive of the same type with a changed value.
Values are not part of the topology count.

## Bundle order is not counted

The order of items inside a bundle is irrelevant:

```text
R || L == L || R
R || L || C == C || R || L
```

This is an order inside a parallel composition, not a drawing convention.

## Parallel bundle versus series span

A parallel `R` and `L` between the same two nodes is:

```text
  R
a---b
 \ /
  L
```

Its reduced bundle label is:

```text
R || L
```

A series `R` and `L` is different:

```text
a --- R --- x --- L --- b
```

Its reduced series-span label is:

```text
R -- L
```

These are counted separately:

```text
R || L != R -- L
```

## Series spans

A series span is the local series analogue of a parallel bundle. Series spans
are part of the staged reduced-signature model; local series-span reduction
and canonical reduced signatures are implemented (see `rice reduced` and
`docs/model_decisions.md`).

A span is a maximal local chain of two-terminal factors separated by internal nodes
of incidence 2 in the current reduced graph.

A span need only lie on at least one simple terminal-to-terminal path. It need
not lie on every terminal path.

For example:

```text
      R---L
s ------------- t
 \             /
  ----- C -----
```

the upper `R--L` arm is a series span, even though the lower `C` arm provides a
second terminal path.

## Series order is not counted

When local series spans are implemented, the reduced model should count these as
the same span:

```text
R -- L
L -- R
```

and all of these as the same primitive span:

```text
R -- L -- C
C -- R -- L
L -- C -- R
```

## Primitive duplicates merge in series and parallel

In parallel:

```text
R || R -> R
L || L -> L
C || C -> C
```

In series:

```text
R -- R -> R
L -- L -> L
C -- C -> C
R -- L -- R -> R -- L
```

More generally, repeated primitive singleton factors merge inside an unordered
series composition:

```text
R -- A -- R -> A -- R
```

## Compound duplicates do not merge

Repeated compound factors do not collapse merely because they are repeated.

This parallel composition:

```text
(R--L) || (R--L)
```

is not reduced to:

```text
R--L
```

This series composition:

```text
(R||L) -- (R||L)
```

is not reduced to:

```text
R||L
```

The reduction rule is local and primitive:

```text
collapse repeated primitive singleton R/L/C factors;
do not collapse repeated compound subnetworks.
```

## Current implementation status

Support graphs provide the structural skeleton for the staged reduced model:

1. enumerate connected unlabelled simple graphs;
2. choose unordered terminal pairs;
3. reject terminal-irrelevant choices;
4. assign reduced bundle/span/component labels;
5. canonicalise the result up to internal node renaming and terminal reversal.

The reduced-model implementation is staged:

- Phase 1 support census is implemented as `rice supports`: it performs steps 1
  through 3 and reports basic support graphs, unordered two-terminal labellings,
  and terminal-relevant two-terminal supports.
- Phase 2 raw simple primitive bundle-assignment census is implemented as
  `rice bundles`: it assigns the seven simple primitive bundles above to
  terminal-relevant supports under the component budgets and reports raw leaf
  assignments before assigned-support isomorphism or signature merging.
- Phase 3 canonical bundle-labeling orbit census is implemented as
  `rice labelings`: it quotients the simple-bundle assignments by
  automorphisms of each terminal-relevant support that preserve the unordered
  terminal pair, including terminal reversal.
- Local series spans, recursive reduced signatures, and full standard-slice
  signature enumeration and merging are implemented as `rice reduced`,
  currently exposed for the small golden slice `R <= 2`, `L+C <= 3`; the full
  `R <= 3`, `L+C <= 5` reduced catalogue remains future work.

The legacy `count_networks` path that previously used multiset
component-count bundles, and overcounted relative to the reduced-topology
model, has been removed in full (`docs/plan/02-cleanup/02-legacy.md`).

## Bundle types and bundle sets in the count language

`rice count bundle-types` reports the fixed seven simple primitive bundle types
with exact `(R,L,C)` weights. `reactive_count` in the Python API remains
`L+C`, but exact `l_count` and `c_count` are now exposed from the same validated
bundle-weight source of truth.

`rice count bundle-sets` counts multisets of these seven bundle types. A bundle
set's cardinality is the number of source support edges it can fill. Its raw
placement count on distinguishable edges is the multinomial coefficient of its
multiplicities. This is deliberately separate from `rice bundles`, which counts
ordered raw assignments per relevant support shape.
