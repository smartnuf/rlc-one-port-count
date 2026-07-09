# 00-records / 03 — Update README motivation for enumeration

Status: `todo`

## Goal

Plan a README motivation update explaining why enumerating small RLC networks matters for rice and for network theory. Do not update `README.md` in this task unless a later implementation task explicitly calls for it.

## Draft motivation

Enumerating finite classes of RLC one-port networks is useful because it turns vague questions about possible circuit forms into reproducible catalogues. A catalogue can be searched, counted, compared with known results, and used to test hypotheses about realisability and minimality.

For rice specifically, enumeration can help to:

- test whether the descriptor language covers the intended classes of networks;
- discover duplicate descriptors that describe equivalent networks;
- build canonicalisation rules from evidence rather than guesswork;
- generate golden examples for impedance calculation and simplification tests;
- compare rice output with historical catalogues;
- explore where series-parallel forms cease to be enough and bridge-like primitives become necessary;
- support future claims about completeness, expressiveness, and minimal realisations.

## Done means

- The repository has a clear plan for a README motivation note.
- The note distinguishes practical software motivation from mathematical claims.
- Any historical catalogue comparisons are cited in the documentation.
