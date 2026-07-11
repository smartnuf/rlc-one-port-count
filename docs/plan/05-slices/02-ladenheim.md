# 05-slices / 02 — Ladenheim structural slice

Status: `todo`

## Goal

Use the historical structural starting scope:

```text
R + L + C <= 5
L + C <= 2
```

The generated primitive candidates feed the colour-preserving two-terminal
2-isomorphism contract planned in `docs/plan/04-ladenheim/01-148.md` and the
comparison study planned in `docs/plan/04-ladenheim/07-compare-reductions.md`.
The related canonical 108-network catalogue is a later subset whose members
satisfy `R <= 3`, `L+C <= 2`, and `R+L+C <= 5`.

## Done means

- The slice generator accepts exactly the documented historical bounds.
- The output can be consumed by the 148 reproduction, descriptor fixtures, and
  reduction-comparison study.
