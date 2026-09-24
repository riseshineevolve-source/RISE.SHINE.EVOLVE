# HMDA Book 1 V3.1 — bounded correction pass

Status: **IMPLEMENTED IN SOURCE; ENGLISH NOT FROZEN**.

Authority: independent owner-level review of the exact 145-page V3 artifact at commit `d95847fe778850bd80c3a160185536677f04c580`, PDF SHA-256 `994db4ec8b2bc4f95e351b40646add51e55bc71b29379217be15b1752a6d6eb8`.

## Scope lock

V3.1 is a bounded correction layer only. It must not reopen accepted puzzle logic, Shigai geometry, Witness Board architecture, naming, aliases, the five-act narrative, or Room Zero mechanics.

Implemented corrections:

1. **Spatial map rule/coordinate clearance** — the Live Case Map renderer now guarantees a visible safe gap between the bottom of `MAP RULES / WITNESS KEY` and the column-coordinate row. This addresses the overlap family observed on V3 pages 15, 27, 39, 49, 55, 63, 69, 73, 81, 85 and 103 without changing map geometry or clues.
2. **Certificate copy** — removed the rejected `certificate committee` joke. The certificate now rewards following evidence and making the final call.
3. **Hint/Solution onboarding** — opening instructions now tell the child exactly where the Hint Vault sits in the flow, to start with Level 1, return to the case, and use stronger hints only as needed; Solutions are explicitly after the Hint Vault and should be checked only after committing to a verdict.
4. **Team/recruit wording** — Mimi, Luli, Dilo, Alio and Nini are explicitly the five field detectives; Grandma Bibi is the archive mentor; the reader occupies the empty sixth field badge/recruit slot.
5. **Act I gate** — the detached floating act circle is replaced by an integrated dossier-style `CASE ARC / ACT I` badge.
6. **Concrete visual evidence** — Cases 03, 08, 11 and 24 receive code-native evidence diagrams rather than prose-led puzzle delivery. Case 16's existing artifact page is upgraded to show the archive photograph evidence, plaque, security sticker, striped badges, processing envelope and candidate controls directly.

Implementation entry point: `scripts/build_owner_review_v31.py`. It wraps the verified V3 builder and patches only the surfaces above.

## Verification gate

Before any English freeze:

- render the complete V3.1 PDF from the canonical 30-case master/runtime/maps;
- run normal production preflight and machine audit;
- inspect every page of the new PDF, with focused review of pages corresponding to the eleven spatial-map overlap reports, opening/onboarding, Act I gate, Cases 03/08/11/16/24, certificate and finale;
- confirm logic remains 30/30 PASS and all 15 spatial cases remain uniquely solvable;
- create print-scale previews/contact sheets;
- complete a representative physical proof for gutter comfort, pencil space, small-label clarity and grayscale density.

Only after owner visual approval and the physical-proof gate may the owner separately authorize an explicit English-source freeze. Full Polish Detective production remains parked until that explicit freeze.
