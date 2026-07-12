# Results and census targets

This file records the modern reduced-model census targets (support census,
bundle assignment, bundle labeling, and the reduced-topology golden slice),
plus the historical counts produced by the now fully-removed legacy
multiset-bundle counter, kept for later comparison against the full reduced
`R <= 3`, `L+C <= 5` census.

## Historical legacy multiset-bundle counts

The legacy multiset-bundle counter and every command that generated the two
tables below have been removed in full (`docs/plan/02-cleanup/02-legacy.md`,
following the earlier removal of its `generic` mode in
`docs/plan/02-cleanup/03-generic-x.md`). These figures are **not** generated
by the current source, are **not** reproducible by any current command, are
**not** tested golden values, and are **not** part of `make check` or the
supported model. They are kept only as a historical reference point, for
later comparison once the full reduced `R <= 3`, `L+C <= 5` census is
computed (`docs/plan/05-slices/04-r3-x5.md`).

### `lc` mode (L and C counted as distinct component types)

Reactive column is `X = L + C`. The legacy counter's bundles allowed repeated
same-type parallel branches (for example, counting `R || R` separately from
a single `R`).

| R \ X=L+C | 0 | 1 | 2 | 3 | 4 | 5 | Row total |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0 | 2 | 6 | 22 | 106 | 596 | 732 |
| 1 | 1 | 4 | 24 | 160 | 1,205 | 9,668 | 11,062 |
| 2 | 2 | 14 | 128 | 1,186 | 11,582 | 115,808 | 128,720 |
| 3 | 4 | 48 | 634 | 7,878 | 96,376 | 1,163,342 | 1,268,282 |

Historical total: **1,408,796**.

### `generic` mode (single undifferentiated reactive type `X`)

The legacy counter also previously supported a `generic` mode that treated
every reactive element as one undifferentiated type `X` instead of
distinguishing inductors from capacitors.

| R \ X | 0 | 1 | 2 | 3 | 4 | 5 | Row total |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0 | 1 | 2 | 4 | 11 | 31 | 49 |
| 1 | 1 | 2 | 7 | 24 | 97 | 403 | 534 |
| 2 | 2 | 7 | 36 | 170 | 875 | 4,536 | 5,626 |
| 3 | 4 | 24 | 170 | 1,083 | 6,928 | 43,527 | 51,736 |

Historical total: **57,945**.

## Support graph census target

For the reduced implementation, the first milestone is support graph census. For
`max_edges = 8`, the expected table is:

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

## Simple-bundle assignment leaf target

After support graph census, the next reduced-model phase assigns one of the
seven valid primitive bundles to each terminal-relevant support edge:

```text
R
L
C
R||L
R||C
L||C
R||L||C
```

This target is implemented by `rice count assignments --profile main`. The command derives the natural support bound `max_support_edges = max_r + max_lc`; optional `--max-support-edges` is only for debugging/truncation and cannot exceed that bound. For `R <= 3, L+C <= 5`, the raw assignment leaves before isomorphism/signature merging are:

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

These are not final reduced-topology counts. They are sizing and regression
targets for the next implementation phases.


## Canonical simple-bundle labeling orbit target

The next reduced-model phase is implemented by
`rice count assigned-supports --profile main`. It preserves the phase-2 raw
assignment leaves and counts canonical bundle labelings modulo automorphisms of
each terminal-relevant support that preserve the unordered terminal pair. Such
automorphisms may swap the two terminals. This phase removes only
assigned-support graph isomorphism; it does not apply local series-span
reduction, primitive series duplicate merging, recursive reduced signatures, or
any electrical-equivalence transforms.

For `R <= 3, L+C <= 5`, the phase-3 assigned-support count is:

| Support edges | Relevant supports | Raw assignment leaves | Canonical bundle-labeling orbits |
|---:|---:|---:|---:|
| 1 | 1 | 7 | 7 |
| 2 | 1 | 49 | 28 |
| 3 | 2 | 670 | 380 |
| 4 | 4 | 6,488 | 3,770 |
| 5 | 10 | 46,020 | 28,004 |
| 6 | 27 | 194,184 | 127,627 |
| 7 | 80 | 456,960 | 323,330 |
| 8 | 258 | 462,336 | 346,948 |
| **Total** | **383** | **1,166,714** | **830,094** |

This **830,094** total is a phase-3 assigned-support orbit count, not the final
reduced-topology count. The code now also has local reduction and canonical
reduced-signature machinery for individual assigned two-terminal networks, but
no command currently enumerates the full standard slice, merges phase-3 orbits
by those signatures, or claims a final reduced-topology total.

## RICE local series/parallel reduced count for `R <= 3`, `L+C <= 2`

This is a current RICE local series/parallel reduced result, useful for the
planned Ladenheim comparison because it uses the implemented relation on the
component-budget region satisfied by the historical 108 catalogue: `R <= 3`,
`L+C <= 2`, and `R+L+C <= 5`. It is not presented as the historical 148
structural catalogue or the 108 canonical Ladenheim catalogue.

Every historical 108 catalogue member lies within this budget region. Once
historical representatives are imported, each can be assigned one of these RICE
local series/parallel signatures; multiple historical members may map to one
RICE signature, and that mapping has not yet been measured.

Reproduced with:

```bash
.venv/bin/python -m rice count networks \
    --max-r 3 \
    --max-lc 2 \
    --max-support-edges 5 \
    --format json
```

The total number of final canonical reduced signatures is **140**.

Table entries are exact primitive counts in the final reduced signatures;
columns aggregate by `x = L+C`.

| R \ L+C | 0 | 1 | 2 | Row total |
|---:|---:|---:|---:|---:|
| 0 | 0 | 2 | 2 | 4 |
| 1 | 1 | 4 | 12 | 17 |
| 2 | 0 | 4 | 34 | 38 |
| 3 | 0 | 4 | 77 | 81 |

Cumulative RICE local series/parallel reduced total for `R <= 3`, `L+C <= 2`,
`max_edges = 5`: **140**.

## First complete reduced-topology golden slice

The first end-to-end reduced-topology census is implemented for the deliberately
small regression slice. Select this slice explicitly with `--profile golden`; pass
explicit limits only when intentionally exploring a larger slice:

```bash
.venv/bin/python -m rice count networks --profile golden
```

The equivalence relation is the documented canonical reduced-topology relation:
internal node renaming and terminal reversal are ignored; local series and
parallel operands commute; duplicate primitive singleton `R`, `L`, and `C`
factors merge; duplicate compound subnetworks do not merge. This is not full
rational-immittance equivalence.

Table entries are exact primitive counts in the final reduced signatures. `L`
and `C` remain distinct topology labels, although columns aggregate by
`x = L+C`.

| R \ L+C | 0 | 1 | 2 | 3 | Row total |
|---:|---:|---:|---:|---:|---:|
| 0 | 0 | 2 | 2 | 4 | 8 |
| 1 | 1 | 4 | 12 | 40 | 57 |
| 2 | 0 | 4 | 34 | 210 | 248 |

Cumulative reduced-topology total for `R <= 2`, `L+C <= 3`: **313**.

Diagnostic totals for the same slice:

| Stage | Total |
|---|---:|
| Raw phase-2 assignments | 1,830 |
| Phase-3 assigned-support labeling orbits | 1,112 |
| Final canonical reduced signatures | 313 |

Machine-readable summary: `data/counts/small-r2-x3.json`. Human-readable summary:
`docs/counts/small-r2-x3.md`. This slice is a golden regression target and is
not presented as the full `R <= 3`, `L+C <= 5` project count.

## Object-language PR2 golden counts

Modern commands equivalent to the staged golden results are:

```bash
rice count assignments --profile main
rice count assigned-supports --profile main
rice count networks --profile golden
```

For `--profile main` (`R <= 3`, `L+C <= 5`), raw assignments total `1,166,714`
and assigned-support classes total `830,094`. For `--profile golden` (`R <= 2`,
`L+C <= 3`), the pipeline diagnostics are raw assignments `1,830`,
assigned-support classes `1,112`, and local-SP networks `313`.

The RICE local-SP slice

```bash
rice count networks --relation local-sp --max-r 3 --max-lc 2 --max-support-edges 5
```

has total `140`. This is a RICE local-SP count in that component/source region,
not the historical Ladenheim 108 relation.

## PR3 enumeration and reduction-provenance checks

For the hand-checkable exact fixture `--max-r 1 --max-l 1 --max-c 0`, the
enumerated pipeline has 5 raw assignments, 4 assigned-support classes, and 4
local-SP networks. The two placements of the two-edge `R--L` path are one
assigned-support orbit. Final reduced exact facts are one `(0,1,0)`, one
`(1,0,0)`, and two `(1,1,0)` networks.

For `--profile golden`, `rice count reductions --profile golden` preserves the
established pipeline totals: 1,830 raw assignments, 1,112 assigned-support
classes, and 313 local-SP networks. The nearby local-SP region
`--max-r 3 --max-lc 2 --max-support-edges 5` remains 140 networks; this is a
RICE local-SP result, not the historical Ladenheim 108 relation.
