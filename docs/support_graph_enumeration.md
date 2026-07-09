# Support graph enumeration plan

This document defines the first implementation milestone for RICE, the reduced RLC
one-port enumerator.

The goal is to enumerate and classify basic two-terminal support graphs before
assigning components. This gives the later component-assignment and reduced
signature phases a stable base.

## Definitions

### Basic support graph

A **basic support graph** is a connected, loopless, simple, unlabelled graph.

It records only which nodes are connected. It does not yet record R, L, or C
labels.

### Two-terminal basic graph

A **two-terminal basic graph** is a basic support graph with an unordered pair of
distinct nodes chosen as the external terminals.

Terminal reversal does not create a new two-terminal graph. Internal node
renaming does not create a new graph.

### Terminal-relevant two-terminal graph

A two-terminal basic graph is **terminal-relevant** iff every support edge lies
on at least one simple path between the two terminals.

Equivalently, the union of support edges used by all simple terminal-to-terminal
paths equals the full support-edge set.

If the test fails, reject the whole terminal-labelled graph. Do not prune the
dangling or pendant part.

## Support-edge bound

For the main problem:

```text
R <= 3
L + C <= 5
```

the maximum number of primitive components is eight.

Because every support edge must receive at least one non-empty component bundle,
the support graph can have at most eight edges:

```text
1 <= support_edges <= 8
```

For an exact component total `n = R + L + C`, under the future simple-bundle rule
where a support edge can carry at most one `R`, one `L`, and one `C`, the crude
possible support-edge range is:

```text
ceil(n / 3) <= support_edges <= n
```

The first census should simply run up to `max_edges = max_r + max_reactive`.

## Enumeration stages

For each support-edge count `m`, report three numbers.

### 1. Basic connected unlabelled graphs

Enumerate connected unlabelled simple graphs with exactly `m` edges.

This is independent of terminal choice and component labels.

### 2. Unordered two-terminal labelings

For each basic support graph, choose an unordered pair of distinct nodes as
terminals. Quotient those terminal pairs by the automorphism group of the basic
support graph.

At this stage, do not apply terminal-relevance filtering.

### 3. Terminal-relevant two-terminal graphs

Apply the terminal-relevance test to each two-terminal labelling. Keep only
those for which every support edge lies on at least one simple path between the
terminals.

Then quotient by the same support-graph automorphisms, treating the terminal
pair as unordered.

## Expected census for max_edges = 8

The current source can already be used to verify the target support counts. The
expected census is:

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

These counts are the first regression targets for the next implementation
phase.

## Why rejection is not pruning

Consider:

```text
s ---- a ---- t
       |
       x
```

The support edge `a-x` lies on no simple path from `s` to `t`. The two-terminal
support graph is therefore rejected.

Do not prune `a-x` and keep the remaining path `s-a-t`. The path `s-a-t` is a
different support graph that will be generated separately.

The same applies to pendant blobs:

```text
s ---- a ---- t
       |\
       | \
       b--c
```

The triangle is connected to the terminal path, but its edges lie on no simple
terminal-to-terminal path. Reject the whole terminal-labelled support graph.

## Assignment leaf bound for the future simple-bundle phase

Once the support census is stable, the next phase should assign only the seven
simple primitive bundles:

```text
R
L
C
R||L
R||C
L||C
R||L||C
```

For `R <= 3, L+C <= 5`, the number of raw assignment leaves to visit before
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

This is small enough for a clear brute-force assignment pass before introducing
more elaborate canonical-generation machinery.

## Suggested CLI for phase 1

Add a command or option that reports the support census without running the full
component count. Possible shapes:

```bash
python -m rice supports --max-edges 8
```

or:

```bash
python -m rice census --max-r 3 --max-reactive 5
```

The exact CLI shape is less important than making the stage inspectable and
testable.

## Required phase-1 tests

Add tests for:

```text
connected unlabelled graph counts by edge count up to 8
unordered terminal-pair orbit counts by edge count up to 8
terminal-relevant support counts by edge count up to 8
terminal reversal gives one two-terminal support, not two
dangling branch causes whole terminal-labelled graph rejection
pendant blob causes whole terminal-labelled graph rejection
series chain is accepted
parallel/cyclic alternatives are accepted
```
