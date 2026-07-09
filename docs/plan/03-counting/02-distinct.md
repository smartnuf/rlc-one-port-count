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

- Current implementation has completed the support-only portion of the staged
  reduced model: connected unlabelled simple support graphs, unordered terminal
  pair orbits, and terminal-relevance filtering are implemented in `rice.core`
  and exposed through `rice supports`.
- The legacy `count_networks` path is explicitly labelled legacy and still uses
  multiset component-count bundles. Simple primitive bundle assignment,
  assigned-support canonicalisation, and reduced signatures remain unimplemented,
  so the overall distinct-network task is still `prog` rather than `done`.

## Near-term next steps

1. Add the phase-2 simple bundle-assignment layer using only `R`, `L`, `C`,
   `R||L`, `R||C`, `L||C`, and `R||L||C` on terminal-relevant supports.
2. Validate the raw leaf-assignment totals from the normative docs before any
   signature merging.
3. Only after that, add reduced canonical signatures and the documented boundary
   tests for local series/parallel reductions.
