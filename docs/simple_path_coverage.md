# Connectivity, simple-path coverage, and edge deletion

This note documents the terminal-relevance test used by the RLC one-port
topology counter. It explains why plain connectedness is too weak, why a simple
edge-deletion test is not sufficient, and why terminal-to-terminal simple-path
coverage is the intended support-graph criterion.

Throughout this note, let the two terminal nodes be denoted by `s` and `t`.

## Connectivity is too weak

A graph is **connected** if every node can be reached from every other node.

For example, the following graph is connected:

```text
s ---- a ---- t
       |
       x
```

Every node is reachable from every other node, so the graph passes a
<!-- line-length: ignore-next-line -- legacy line pending wrap -->
connectivity test. But the branch `a-x` is a dangling appendage. It cannot carry
current in an ideal passive driving-point one-port, because it is not part of
any route from `s` to `t`.

Connectedness is necessary, but not sufficient.

## Simple terminal-to-terminal paths

<!-- line-length: ignore-next-line -- legacy line pending wrap -->
A **simple path** from `s` to `t` is a path that starts at `s`, ends at `t`, and
does not repeat vertices.

The project keeps a terminal-labelled support graph only if:

> Every support edge lies on at least one simple path from `s` to `t`.

Equivalently, every branch in the support graph must be part of at least one
non-self-intersecting terminal-to-terminal route.

This series network is valid:

```text
s ---- a ---- t
```

Both edges lie on the simple path:

```text
s, a, t
```

This parallel/cyclic network is also valid:

```text
      a
     / \
s ---   --- t
     \ /
      b
```

Every edge lies on one of the simple paths `s-a-t` or `s-b-t`.

By contrast, this graph is not valid:

```text
s ---- a ---- t
       |
       x
```

The edge `a-x` lies on no simple `s-t` path.

The test also excludes pendant cycles or pendant blobs. For example:

```text
s ---- a ---- t
       |\
       | \
       b--c
```

<!-- line-length: ignore-next-line -- legacy line pending wrap -->
The triangle `a-b-c-a` is connected to the rest of the network, but only through
the articulation vertex `a`. To traverse an edge in the triangle and still get
<!-- line-length: ignore-next-line -- legacy line pending wrap -->
from `s` to `t`, a walk would have to enter the triangle at `a` and later return
to `a`, repeating `a`. That is a walk, but not a simple path.

Therefore the terminal-labelled support graph is rejected.

## Rejection is not pruning

If a terminal-labelled support graph fails simple-path coverage, reject the
whole terminal-labelled graph.

Do not prune the dangling or pendant part and keep the remaining graph. The
<!-- line-length: ignore-next-line -- legacy line pending wrap -->
remaining graph is a different support graph that should be generated and tested
on its own.

For example:

```text
s ---- a ---- t
       |
       x
```

is rejected as a whole. It is not converted into:

```text
s ---- a ---- t
```

That smaller support graph will appear separately in the support enumeration.

## Edge deletion is not enough

A tempting relevance test is:

> Delete edge `e`. If `s` and `t` become disconnected, then `e` matters.

This identifies terminal bridges. For example:

```text
s ---- a ---- t
```

<!-- line-length: ignore-next-line -- legacy line pending wrap -->
Deleting either edge disconnects `s` from `t`, so each edge is clearly relevant.

However, this implication only works in one direction:

```text
edge deletion disconnects s and t  =>  edge is relevant
```

The converse is false.

For example, in this network:

```text
      a
     / \
s ---   --- t
     \ /
      b
```

Deleting the edge `s-a` does not disconnect the terminals, because `s-b-t`
<!-- line-length: ignore-next-line -- legacy line pending wrap -->
remains. But `s-a` is still a relevant branch, because it lies on the simple path
`s-a-t`.

So:

```text
edge deletion does not disconnect s and t  =>  inconclusive
```

The edge might be a legitimate branch in a cycle, or it might be irrelevant
material in a pendant cycle.

## Criterion used by the project

The project applies simple terminal-path coverage:

```python
used_edges = union of edges appearing in all simple paths from s to t
valid = used_edges == all_edges
```

In words:

> Keep a two-terminal support graph only if every edge is used by at least one
> simple terminal-to-terminal path.

This accepts series edges and bridge edges, because they lie on the unique
<!-- line-length: ignore-next-line -- legacy line pending wrap -->
terminal path. It also accepts cyclic alternatives, because each edge can lie on
<!-- line-length: ignore-next-line -- legacy line pending wrap -->
at least one terminal path. It rejects dangling trees and pendant blobs, because
their edges are not on any simple terminal path.

## Biconnected-component equivalent

There is a useful equivalent graph-theoretic formulation.

1. Add a temporary artificial edge directly between the terminals `s` and `t`.
2. Find the biconnected component containing that artificial edge.
3. Remove the artificial edge.
4. Check whether all original edges lie in that same biconnected component.

If they do, then every original edge lies on at least one simple path between
`s` and `t`.

For a series chain:

```text
s ---- a ---- b ---- t
```

adding the artificial terminal edge gives:

```text
s ---- a ---- b ---- t
|                   |
+-------------------+
```

All original edges now lie in the same biconnected component as the artificial
edge, so the series chain is accepted.

For the pendant-triangle graph:

```text
s ---- a ---- t
       |\
       | \
       b--c
```

adding the artificial edge `s-t` puts the main terminal path edges in the
<!-- line-length: ignore-next-line -- legacy line pending wrap -->
terminal biconnected component, but the pendant triangle remains outside it. The
support graph is therefore rejected.

<!-- line-length: ignore-next-line -- legacy line pending wrap -->
This formulation is often more efficient and elegant than explicitly enumerating
all simple paths, especially as the graph size grows.

## Relationship to series spans

Terminal relevance and series-span detection are different questions.

A support edge is terminal-relevant if it lies on at least one simple path
between the external terminals.

A local series span is found from two-valent runs in the current reduced graph.
It does not need to lie on every simple terminal-to-terminal path.

For example:

```text
      R---L
s ------------- t
 \             /
  ----- C -----
```

the upper `R--L` arm is a local series span even though the lower `C` arm gives
another simple terminal path. This is why the reduced-signature implementation
should not rely only on terminal-separating articulation nodes to find series
spans.

## Relationship to support graphs and labelled branches

The terminal-relevance test is applied to the support graph before assigning
component labels.

A support edge may later represent a primitive branch, a simple primitive
parallel bundle, or a reduced factor. The support graph test asks only whether
the underlying connection between two nodes belongs to the terminal one-port
core.
