# 08-docs / 03 — Document catalogue comparisons and references

Status: `todo`

## Goal

Keep historical comparisons precise and sourced.

## Notes

The relevant historical name appears to be the `Ladenheim catalogue`. It is
described here as a catalogue of distinct RLC networks with no more than two
reactances and three resistances, subject also to a five-element total limit.
These networks are relevant because they are realised by biquadratic functions.

Some sources report 108 networks in the catalogue. rice should compare against this number only after matching the same distinctness and reduction assumptions.

## Planned comparison slices

- Ladenheim-style slice: `R <= 3`, `L+C <= 2`, and `R+L+C <= 5`.
- Explicit boundary point: `R=3`, `L+C=2`, total `5`.
- rice smoke-test slice: `R <= 2`, `L+C <= 3`.
- rice full planned scope: `R <= 3`, `L+C <= 5`.

## Done means

- The repository cites the sources used.
- Agreement or disagreement with historical counts is explained.
- The spelling and scope of the catalogue are consistent throughout the docs.
