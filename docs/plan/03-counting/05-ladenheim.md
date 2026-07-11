# 03-counting / 05 — Define Ladenheim comparison contracts

Status: `prog`

## Goal

Define the historical Ladenheim scope and the named reduction contracts that the
repository will compare without replacing the implemented RICE local
series/parallel model.

## Historical scope

The structural starting scope for the 148-network Ladenheim set is:

```text
R + L + C <= 5
L + C <= 2
```

The 148 are essentially distinct primitive RLC networks obtained under the
historical structural treatment, including graph 2-isomorphism and exclusion of
trivially same-kind series/parallel-reducible candidates. This starting set
includes eight networks with four resistors and one reactive element.

The canonical 108-network Ladenheim catalogue is a subset of the 148 after forty
further exclusions. Its members satisfy `R <= 3`, `L+C <= 2`, and
`R+L+C <= 5`. The forty exclusions comprise eight four-resistor/one-reactive
networks whose bilinear impedances have simpler realizations, four four-element
networks reducible by Zobel transformation, twenty five-element series-parallel
networks reducible by Zobel transformation, and eight further O/O-dual and
bridge cases excluded using the source's Cauer-Foster, regularity,
realizability, and related Y-delta reasoning. The 62 classes are a later
realizability-set classification of the 108 catalogue members, not another graph
signature count.

The documented RICE local series/parallel result for `R <= 3`, `L+C <= 2`, and
`max_edges = 5` is 140 signatures. Every historical 108 catalogue member lies
within that component-budget region; after historical representatives are
imported, each can be assigned a RICE local series/parallel signature. Multiple
historical members may map to one RICE signature, and the mapping has not yet
been measured.

Source context: A. Morelli and M. C. Smith, *Passive Network Synthesis: An
Approach to Classification*, SIAM, 2019, especially Chapter 3 Section 3.1,
Chapter 5, the Chapter 6 classification discussion, and Theorem 7.4.

## Named reduction contracts

- **RICE local series/parallel reduction**: the implemented relation used by
  `canonical_reduced_signature` and `rice reduced`. It normalises local
  primitive series spans and parallel bundles inside arbitrary two-terminal
  networks. Bridge and other non-series-parallel cores may remain.
- **RICE local series/parallel plus star-delta**: a planned augmentation of the
  implemented relation after an admissibility contract for star-delta and
  delta-star moves is defined.
- **Colour-preserving two-terminal 2-isomorphism**: a planned structural
  relation on primitive R/L/C edge-coloured graphs, with terminal reversal and
  internal relabelling ignored and with a port-preserving treatment such as a
  source-augmented graph if needed.
- **Colour-preserving two-terminal 2-isomorphism plus star-delta**: a planned
  augmentation of the 2-isomorphism relation using the same admissibility
  contract.

The RICE local series/parallel partition and the 2-isomorphism partition are not
assumed to refine each other. Their relationship is an empirical comparison
result.

## Star-delta questions

Use `star-delta` to mean both Y-to-delta and delta-to-Y directions where
admissible. Before implementation, define whether the relation is structural or
electrical, the component-value mapping, positivity requirements, whether the
outputs must remain primitive R/L/C branches, the equality notion, closure and
canonicalisation, termination and duplicate suppression, and how to handle moves
that leave the primitive RLC network class.

## Done means

- The four named contracts above are reflected in model, result, and plan docs.
- The historical 148, 108, and 62 targets are stated without conflating them.
- CLI/API design remains deferred until the contracts and outputs are precise.
