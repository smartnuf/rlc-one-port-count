# 03-counting / 02 — Define “distinct network” precisely

Status: `prog`

## Goal

Define exactly what is being counted before generating counts.

## Questions to settle

- Are networks compared as terminal-labelled graphs?
- Are R elements indistinguishable from one another?
- Are L elements indistinguishable from one another?
- Are C elements indistinguishable from one another?
- Is L/C type part of the graph colouring?
- Are series and parallel reductions applied before counting?
- Are same-kind series/parallel combinations excluded as non-generic or reducible?
- Are open circuits, shorts, disconnected graphs, and dangling subgraphs excluded?
- Are networks equivalent under impedance identity, graph isomorphism, known transformations, or some staged combination of these?

## Working approach

Use the reduced-model staging from the normative model docs:

1. Enumerate connected, loopless, simple, unlabelled support graphs.
2. Choose unordered terminal pairs up to support-graph automorphism. Terminal
   reversal does not create a new topology.
3. Reject terminal-irrelevant two-terminal support graphs as whole objects; do
   not prune dangling branches or pendant blobs into smaller accepted graphs.
4. Assign simple primitive R/L/C bundles under the component budgets. Each bundle
   is a non-empty subset of `{R, L, C}` between the same two support nodes.
5. Canonicalise assigned supports under internal node renaming and terminal-pair
   reversal.
6. Apply the documented local series/parallel reduction rules: operands
   commute within local series spans and parallel bundles, duplicate primitive
   singleton factors merge, and duplicate compound subnetworks do not merge
   merely because they are repeated.
7. Record or discuss stronger equivalences such as Y-Delta/Delta-Y transforms,
   duality, bridge-balance special cases, Foster/Cauer transformations, or
   rational impedance identity as possible later refinements. Do not silently
   collapse them in the current reduced-model counting contract unless a later
   phase explicitly opts in.

The reduced model is therefore a canonical reduced-topology count, not a full
solver for general electrical equivalence.

## Done means

- The definition is written down before counts are treated as meaningful.
- Count tables state which equivalence relation they use.
- Tests encode the definition.

## Progress notes

- All five reduced-model stages are now implemented: connected unlabelled
  simple support graphs, unordered terminal-pair orbits, and
  terminal-relevance filtering (`rice supports`); raw simple primitive bundle
  assignment (`rice bundles`); assigned-support labeling-orbit
  canonicalisation (`rice labelings`); local canonical reduced-signature
  machinery (`canonical_reduced_signature`); and an end-to-end reduced-topology
  census for the committed small golden slice (`rice reduced`). The legacy
  `count_networks` path, which used multiset component-count bundles, has
  been removed in full (`docs/plan/02-cleanup/02-legacy.md`).
- Phase-2 raw simple primitive bundle assignment is implemented in `rice.core`
  and exposed through `rice bundles`, using only `R`, `L`, `C`, `R||L`,
  `R||C`, `L||C`, and `R||L||C`. The normal `R <= 3`, `L+C <= 5` interface derives `max_edges=8`
  and the leaf total is tested as `1,166,714`.
- Assigned-support canonicalisation is implemented as `simple_bundle_labeling_census`
  and exposed through `rice labelings`; for `R <= 3`, `L+C <= 5` it preserves
  `1,166,714` raw leaves and counts `830,094` canonical bundle-labeling orbits.
  Local series-span signature machinery is now implemented for individual
  assigned two-terminal networks with deterministic recursive factor
  normalisation and graph-core canonicalisation. Small-slice census integration is implemented by `reduced_topology_census` and `rice reduced`, with phase-3 orbit witnesses merged by canonical reduced signatures for the `R <= 2`, `L+C <= 3` golden slice. Full `R <= 3`, `L+C <= 5` census execution and descriptor output remain unfinished, so the overall distinct-network task is still `prog` rather than `done`.

## Near-term next steps

1. Extend the reduced-signature census path from the committed small golden slice to the full standard slice after performance and output-size review.
2. Keep the phase-2 raw leaf-assignment and phase-3 bundle-labeling-orbit totals
   as regression tests while adding signature merging.
