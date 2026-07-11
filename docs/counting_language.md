# Object-oriented counting language

The long-term command language is organized by counted or enumerated object:

```bash
rice count <object> ...
rice enum <object> ...
```

This PR implements `rice count supports`, `rice count bundle-types`, and
`rice count bundle-sets`. Enumeration commands and later count targets are
planned, not registered as placeholders.

## Object pipeline

1. **Basic supports** are connected, loopless, simple, unlabelled graphs.
2. **Terminal supports** are basic supports with an unordered pair of distinct
   terminals, quotiented by support automorphisms. Terminal reversal is not a new
   object.
3. **Relevant supports** are terminal supports whose every edge lies on at least
   one simple terminal-to-terminal path.
4. **Bundle types** are exactly `R`, `L`, `C`, `R||L`, `R||C`, `L||C`, and
   `R||L||C`. A bundle has at most one primitive of each type; `R||R`, `L||L`,
   `C||C`, and similar repeated same-type primitive bundles are excluded.
5. **Bundle sets** are multisets or inventories of allowed bundle types. The CLI
   name is `bundle-sets`, but multiplicity matters: `{R, L, R||C}` and
   `{R, R, L, R||C}` are different valid inventories, and the second inventory
   has two separate `R` bundles for two different source support edges.
6. **Support-bundle pairs** will pair a relevant support shape with a compatible
   bundle set before placement.
7. **Assignments** are raw placements of a bundle set onto the edges of one
   terminal-relevant support. This is the stage currently counted by
   `rice bundles`.
8. **Assigned supports** are assignments quotiented by automorphisms of the
   terminal-relevant support that preserve the unordered terminal pair,
   including terminal-swapping automorphisms. This is the stage currently called
   `labelings`.
9. **Networks** are assigned supports canonicalised under a named network
   relation, initially the existing RICE local series/parallel relation.
10. **Reductions** will describe many-to-one mappings from raw assignments to
    assigned-support classes to reduced networks.

There are two meanings of labelling in older text: choosing the unordered
terminal pair on a basic support, and assigning bundle labels to support edges.
The planned user-facing object name for the second quotient is
`assigned-supports`.

## Constraints, finiteness, and profiles

Component options intersect by logical AND:

- `--max-rlc T`: `r + l + c <= T`
- `--max-r R`: `r <= R`
- `--max-l L`: `l <= L`
- `--max-c C`: `c <= C`
- `--max-lc X`: `l + c <= X`

Omitted component options are not defaulted independently. A supports or
bundle-sets query must have a finite effective source support-edge maximum from
`--support-edges`, `--max-support-edges`, a finite component region, or a named
finite profile. Exact edge count is supplied with `--support-edges`; ranged
queries use `--min-support-edges` and/or `--max-support-edges`.

Named profiles are finite component regions:

- `golden`: `--max-r 2 --max-lc 3`
- `main`: `--max-r 3 --max-lc 5`
- `ladenheim-structural-region`: `--max-rlc 5 --max-lc 2`
- `ladenheim-108-region`: `--max-rlc 5 --max-r 3 --max-lc 2`

The Ladenheim names deliberately end in `-region`: they are component scopes,
not historical equivalence rules or source-specific exclusions.

## Bundle-set counts

For multiplicities `(n1, ..., n7)` with cardinality `m`, raw placements onto
`m` distinguishable support edges are counted by:

```text
m! / (n1! n2! ... n7!)
```

`rice count bundle-sets` reports both distinct inventories and the raw
placements represented by those inventories. It does not multiply by support
shape counts.

## Implemented and planned commands

Implemented now:

```bash
rice count supports [OPTIONS]
rice count bundle-types [OPTIONS]
rice count bundle-sets [OPTIONS]
```

Planned later:

```bash
rice count assignments
rice count assigned-supports
rice count networks
rice count reductions
rice enum supports
rice enum bundle-types
rice enum bundle-sets
rice enum assignments
rice enum assigned-supports
rice enum networks
```

Compatibility mapping:

```text
current rice supports -> future rice count supports
current rice bundles -> future rice count assignments
current rice labelings -> future rice count assigned-supports
current rice reduced -> future rice count networks --relation local-sp
```
