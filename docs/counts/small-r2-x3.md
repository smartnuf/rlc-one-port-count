# Small reduced-topology golden slice: `R <= 2`, `L+C <= 3`

This file records the first complete reduced-topology census slice. It is a
fast golden regression target, not the full project catalogue.

Scope:

```text
R <= 2
L + C <= 3
```

The table entries are exact primitive counts present in the canonical reduced
signature. Inductors (`L`) and capacitors (`C`) remain distinct topology labels;
the columns aggregate only by `x = L+C`.

Equivalence relation:

- internal node renaming is ignored;
- terminal reversal is ignored;
- operands commute within local series spans and parallel compositions;
- duplicate primitive singleton `R`, `L`, or `C` factors merge in series and in
  parallel;
- duplicate compound subnetworks do not merge.

This is **not** full rational-immittance equivalence. It does not apply Y-Delta
transforms, duality, Foster/Cauer equivalence, bridge-balance simplifications, or
symbolic impedance identity.

| R \ L+C | 0 | 1 | 2 | 3 | Row total |
|---:|---:|---:|---:|---:|---:|
| 0 | 0 | 2 | 2 | 4 | 8 |
| 1 | 1 | 4 | 12 | 40 | 57 |
| 2 | 0 | 4 | 34 | 210 | 248 |

Cumulative reduced-topology total: **313**.

Diagnostic progression for this same slice:

| Stage | Total |
|---|---:|
| Raw phase-2 assignments | 1,830 |
| Phase-3 assigned-support labeling orbits | 1,112 |
| Final canonical reduced signatures | 313 |

Regenerate the machine-readable summary exactly with:

```bash
.venv/bin/python -m rice reduced --max-r 2 --max-reactive 3 --format json
```

The committed JSON summary is `data/counts/small-r2-x3.json`; the command
output is intended to diff cleanly against that file without post-processing.
