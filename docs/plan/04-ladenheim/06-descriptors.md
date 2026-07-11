# 04-ladenheim / 06 — Integrate SP/bridge descriptors

Status: `todo`

## Goal

Use a textual SP/bridge descriptor language as the stable catalogue notation for
Ladenheim representatives and generated examples.

## Tasks

- Obtain and assess the existing descriptor implementation before designing a
  new syntax.
- Record provenance, license, compatibility, and any required adaptation.
- Define canonical formatting for stable fixtures.
- Support parsing and rendering.
- Represent series and parallel compositions.
- Represent bridge or other non-SP cores with reducible branch descriptors.
- Round-trip descriptors to and from the internal graph/network representation.
- Use descriptors as catalogue fixtures and cross-references to historical
  numbering.

## Done means

- Descriptor fixtures can be parsed, rendered, round-tripped, and diffed.
- The implementation provenance is recorded.
- The descriptor syntax covers the reproduced Ladenheim representatives or lists
  unsupported cases explicitly.

## PR2 note

Before `enum networks` depends on textual descriptors, assess the earlier `network-theory` and `pynntt` implementations, record provenance and compatibility, distinguish graph-based RICE interchange from human-readable SP/bridge syntax, support legacy SPB import where useful rather than copying a parser unchanged, and keep source descriptors distinct from reduced descriptors.
