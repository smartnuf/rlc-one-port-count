# 08-docs / 03 — Document catalogue comparisons and references

Status: `todo`

## Goal

Keep historical comparisons precise and sourced.

## Notes

The relevant historical name is the Ladenheim catalogue. Repository
Ladenheim documentation should distinguish:

- the 148 structural primitive RLC networks in the scope `R+L+C <= 5`,
  `L+C <= 2`, after colour-preserving graph 2-isomorphism and same-kind
  series/parallel rejection;
- the canonical 108-network catalogue, a subset of the 148 after forty further
  exclusions, whose members satisfy `R <= 3`, `L+C <= 2`, and `R+L+C <= 5`;
- the later 62 realizability-set equivalence classes, distinct from the reported
  35 group-action orbits and 24 subfamilies.

Bibliographic source: A. Morelli and M. C. Smith, *Passive Network Synthesis: An
Approach to Classification*, SIAM, 2019, including Chapter 3 Section 3.1,
Chapter 5, the Chapter 6 classification discussion, and Theorem 7.4.

## Planned comparison slices

- Historical Ladenheim structural scope: `R+L+C <= 5` and `L+C <= 2`.
- RICE local series/parallel comparison point: `R <= 3`, `L+C <= 2`,
  `max_edges = 5`, currently counting 140 reduced signatures. Historical 108
  members lie in this budget region, but their mapping to these signatures has
  not yet been measured.
- RICE smoke-test slice: `R <= 2`, `L+C <= 3`.
- RICE full planned scope: `R <= 3`, `L+C <= 5`.

## Done means

- The repository cites the sources used.
- Agreement or disagreement with historical counts is explained by named
  contracts rather than by informal distinctness language.
- The spelling and scope of each catalogue are consistent throughout the docs.
