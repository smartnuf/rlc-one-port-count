# 04-ladenheim / 07 — Compare local SP and 2-isomorphism reductions

Status: `todo`

## Goal

Run an executable comparison study for the RICE local series/parallel track and
the colour-preserving two-terminal 2-isomorphism track, both before and after
admissible star-delta augmentation. The central RICE comparison point is the
current `R <= 3`, `L+C <= 2`, `max_edges = 5` result with 140 local
series/parallel signatures; historical 108 catalogue members lie within that
component-budget region, but their mapping to those signatures has not yet been
measured.

## Tasks

For a common primitive candidate set, record each candidate's:

- ordinary labelled or graph-isomorphism identity;
- RICE local series/parallel reduced signature;
- colour-preserving 2-isomorphism signature;
- class after star-delta augmentation of the RICE track;
- class after star-delta augmentation of the 2-isomorphism track;
- SP/bridge descriptor;
- historical Ladenheim number where known.

Report total class counts under each relation, concrete examples that merge
under one relation but not another, examples that split differently, whether
reduction order changes the result, time and memory costs, early candidate
elimination opportunities, and whether either approach is computationally
preferable for larger slices.

## Done means

- The comparison is reproducible from checked-in fixtures or documented commands.
- The report treats different partitions and computational costs as results,
  without selecting a preferred relation in advance.
