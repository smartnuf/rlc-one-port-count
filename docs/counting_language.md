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
