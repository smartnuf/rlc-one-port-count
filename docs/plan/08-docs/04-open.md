# 08-docs / 04 — Document known limits and open questions

Status: `prog`

## Goal

Avoid overstating what rice proves.

## Open questions

- Does the descriptor language cover all generated planar one-port networks in the target scope?
- Which generated networks require bridge or other non-series-parallel forms?
- Which equivalences should be structural, electrical, or both?
- How should non-generic networks be handled?
- Which counts are implementation facts versus mathematical claims?

## Done means

- Known limits are written down.
- Future work is clear.
- Documentation avoids unsupported completeness claims.

## Progress notes

- Current docs explicitly warn that legacy counts are not final reduced-topology
  counts and that the reduced model is not a full electrical-equivalence solver.
- Open questions about genericity, descriptor coverage, structural versus
  electrical equivalence, and biquadratic sufficiency remain unresolved.

## Near-term next steps

1. Add concrete known-limit notes as implementation exposes unsupported cases.
2. Keep sufficiency questions in the investigation plan until source-backed
   conclusions are ready for user-facing documentation.
