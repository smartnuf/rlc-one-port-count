# Provisional counting language

RICE currently exposes one user-facing counting grammar:

```text
rice count <object> [options]
```

Implemented objects are `supports`, `bundle-types`, `bundle-sets`,
`assignments`, `assigned-supports`, and `networks`. The command language, Python
API, JSON fields and report formatting are provisional until a versioned public
interface is declared.

Object meanings:

- `supports`: support-only graph counts.
- `bundle-types`: the seven simple primitive bundle labels.
- `bundle-sets`: exact bundle inventories satisfying a query.
- `assignments`: raw placements of inventories on relevant supports.
- `assigned-supports`: assignment classes modulo terminal-set-preserving support
  automorphisms.
- `networks`: final unique networks under the named network relation. The
  current relation is `canonical-reduced-topology-local-series-parallel-v1`.

Exact facts are the fundamental representation. JSON results use `object`,
`query`, `group_by`, `records`, `facts`, `totals`, relation metadata and
`diagnostics` where meaningful. The `format_version` field is an internal schema
discriminator and is not a stability promise.

Network source-query diagnostics (`raw_assignments`, `assigned_support_classes`)
are distinct from final reduced-network facts. Network count output intentionally
does not expose a full signature catalogue; enumeration and reduction-analysis
commands remain PR3 work.

## Provisional enumeration language

RICE also exposes the matching provisional enumeration grammar:

```text
rice enum <object> [options]
```

The implemented enumeration objects are `supports`, `bundle-types`,
`bundle-sets`, `assignments`, `assigned-supports`, and `networks`. Enumeration
uses the same profiles and component/support-edge option names as `count`, and
supports `--format markdown|json`. Output formats, IDs, and the reduced
signature serialization are provisional.

Enumeration records are exact source objects unless otherwise stated:

- `enum supports` lists terminal-relevant two-terminal supports after basic
  support generation, unordered terminal-pair quotienting, and whole-graph
  terminal-relevance rejection. Support IDs are derived from a canonical
  relabelling with terminals `0` and `1`, so they are invariant under internal
  node names and terminal reversal.
- `enum bundle-types` lists the seven `SIMPLE_PRIMITIVE_BUNDLES` in model order.
- `enum bundle-sets` lists exact validated bundle inventories and their raw
  placement counts.
- `enum assignments` lists raw placements of bundle labels on canonical support
  edges. It does not quotient by automorphisms.
- `enum assigned-supports` lists canonical assignment-orbit representatives
  under terminal-set-preserving support automorphisms. `raw_assignment_count`
  is the fibre size represented by that orbit.
- `enum networks --relation local-sp` lists unique locally reduced networks
  under `canonical-reduced-topology-local-series-parallel-v1`. The emitted
  `canonical_signature` is a provisional structural serialization, not a
  permanent descriptor grammar and not rational immittance equivalence.

Enumeration has an explicit output guard. Catalogue-producing commands default
to `--max-records 10000`; larger catalogues must opt in with a higher explicit
limit. This prevents accidentally launching the main assignment catalogue as a
routine command.

## Reduction provenance count

`rice count reductions` is a provenance analysis, not a network equivalence
relation. For one finite source query and relation it enumerates the maps

```text
assignments -> assigned supports -> local-SP networks
```

and reports pipeline totals, fibre-size distributions, source-support-edge
transitions, exact source-to-reduced component transitions, and collision
summaries. In fibre tables, `target_objects` counts how many target objects have
a given fibre size, while `source_objects` is the conserved source total for
those fibres. Source-edge transition `distinct_networks_reached` values are
explicit provenance facts and are not additive across rows because one network
may be reached from multiple source-edge counts.
