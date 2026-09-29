# HMDA Book 1 — FINAL bounded owner-review fixes

Date: 2026-09-29
Branch: `feature/detective-book-factory`
Status: BOUNDED OWNER FIX PASS AUTHORIZED / NO REWRITE / EN NOT FROZEN

## Why this pass exists

The 180-page premium artifact restored the correct overall scale and spatial spread parity, but owner review of the actual PDF found presentation regressions that structural QA did not catch.

This is NOT another creative redesign.
Do not reopen story structure, puzzle logic, solutions, Room Zero, Case 03 art, map geometry or the 30-case architecture.

The goal is one bounded correction pass and a new owner-review PDF.

## Keep exactly

- current V3 reader text and current story-flow/WOW logic;
- all 30 cases and all current transitions/payoffs;
- exact owner Case 03 images and exact 15 spatial map pairs;
- Witness Board LEFT / Live Case Map RIGHT physical pairing;
- reverse Hint Vault / Solutions;
- Case 03 ten-question-mark progress tracker;
- current page 2 cozy-site copy;
- all current Room Zero / certification / Archive File 001 logic;
- original approved squad art unchanged.

## Defects found in the 180-page owner PDF

### A. Generic parity worksheets are wrong

Current pages:
**15, 19, 23, 31, 49, 59, 73, 77, 85, 89, 95, 107**

contain generic:
- PREP THE EVIDENCE
- FACTS
- POSSIBLE LINKS
- OPEN QUESTIONS

Owner rejects this.
They read like repetitive school worksheets and create fake work that is not part of the puzzle.

The renderer has already been changed so parity preservation uses an **EVIDENCE GRID interstitial**, not these fields.

If a parity page is required solely to keep Witness Board LEFT / Map RIGHT:
- it must be an intentional visual dossier/interstitial;
- no FACTS / POSSIBLE LINKS / OPEN QUESTIONS prompts;
- no fake task;
- use the signature evidence-grid visual language;
- keep it visually light enough for KDP (no full-black page).

### B. Happy Makers Chat is not a spreadsheet

The current two-column card matrix is rejected.

Required:
- one continuous full-width **HAPPY MAKERS // COMMS** panel;
- natural dialogue order top-to-bottom;
- names clearly differentiated;
- no separate card per sentence;
- black panel with subtle white evidence-grid texture is allowed/preferred;
- preserve all current dialogue beats;
- do not shorten humor merely to fit a historical page count;
- if a chat genuinely needs a continuation page, make it one intentional transcript page, never two orphan cards.

The renderer source has already been changed toward this treatment.

### C. Witness Board reader copy regressed to raw Shigai text

This is a logic-critical blocker.

Examples in the rejected 180-page PDF:
- Case 02 says Dax was in the **Library** and describes Max as a **victim / thief** scenario, while the current case/solution uses the Display Room and a missing trophy handoff.
- Case 06 describes Uma as a **victim** and says a **treasure vanished / thief**, contradicting the Roman-spoon / moved-label story.
- multiple boards leak stale source character names inside clues.

Cause:
`build_v3_premium_interior.py` rendered `person["raw_clue"]` from the Shigai runtime.

Fix already committed:
- canonical reader-facing board copy:
  `content/v3_witness_board_copy.json`
- premium renderer now uses the locked presentation clue copy and fails on display-name drift;
- the reader audit now fails if the old crime words or locked clue copy regress.

Do NOT switch back to `raw_clue` for reader-facing copy.

### D. Evidence Grid is the visual signature

Owner visual direction:
**elegant modern black field + fine white grid**, used as a recognizable recurring motif.

It must feel like premium detective-interface design, not graph paper and not Excel.

Use it selectively:
- a compact grid banner/accent on each new case page;
- parity dossier/interstitial when one is genuinely required;
- selected evidence/checkpoint surfaces;
- optional subtle support inside COMMS panels.

Do not turn every page black.
Do not reduce writing/readability space.
Do not use a pale generic school grid as the main signature.

The case renderer now has a signature black evidence-grid band on new case pages.

### E. Opening branding

The rejected 180-page PDF page 2 uses a generic question mark inside a circle.

Required:
- scanner-question-mark visual language;
- centered, elegant and minimal;
- publication/ISBN copy remains small at the bottom;
- preserve:
  **WE HAVE SAVED A COZY SPOT JUST FOR YOU.**
  and
  `rise-shine-evolve-learning-hub.com`.

The renderer now uses a vector scanner/question-mark mark rather than the generic circle.

### F. Maps

Current LEFT/RIGHT pairing is correct and must remain.

Improve only readability:
- make map itself as large as safely possible;
- column letters and row numbers large, bold and unambiguous;
- keep them OUTSIDE the puzzle raster where possible;
- room/zone overlays must remain readable at real print scale;
- do not alter map geometry, object positions or solution truth.

Renderer target is now 500 pt map image with larger bold coordinate rails.

### G. Case 06 dialogue / flow

Canonical V3 has been corrected again to preserve the earlier humor while keeping the stronger incident bridge.

Current locked chat is:
- NINI: I had emotionally prepared for a dragon tooth.
- LULI: We have a Roman spoon.
- NINI: Less dramatic. Better for soup.
- DILO: So do we have a missing dragon tooth or an overpromoted spoon?
- LULI: Right now, we have a label and an object that disagree.
- BIBI: Which is why we ask before we name a crime.
- NINI: The spoon is taking this very well.
- BIBI: And one tiny number from the Look-Twice file got us here. Good catch.

Do not replace this with the shorter version from the rejected 180-page PDF.

## Current source state to pull before rebuilding

Agency canonical V3:
- commit: `e8e97f5738f9e37887b7b788cd67161bbd3c9bf3`
- blob: `c10c6d20456d75df6e952f9d2d3e1d9a6637b221`

Book Factory branch includes:
- synchronized V3 text;
- `content/v3_witness_board_copy.json`;
- renderer fixes for locked Witness Board presentation copy;
- single-flow COMMS treatment;
- evidence-grid case banner + parity interstitial;
- scanner-question-mark opening mark;
- larger map/axis treatment;
- audit fail-closed checks against prep-page/raw-Shigai regressions.

## Acceptance criteria for the next PDF

Before reporting PASS:

1. Canonical V3 text verifier passes.
2. No printed `PREP THE EVIDENCE`.
3. No printed `POSSIBLE LINKS`.
4. No reader-facing spatial board contains `victim`, `thief`, `treasure vanished` or `took the treasure`.
5. Every locked clue in `v3_witness_board_copy.json` appears in its correct case.
6. All 15 Witness Boards are physical LEFT/even pages.
7. Each matching Live Case Map immediately follows on RIGHT/odd page.
8. Case 03 Photo A/B remains a facing spread and has exactly ten question-mark tracker symbols.
9. Happy Makers dialogue is single-flow COMMS, not two-column cards.
10. No orphan chat continuation page containing only one or two dialogue cards.
11. Evidence Grid motif is visibly black/white and premium on new case pages/parity surfaces.
12. Page 2 uses scanner-question-mark visual language and preserves small publication block + cozy line + website.
13. Spatial coordinate rails are visibly larger/bolder than in the rejected 180-page PDF.
14. All current exact map/image hashes remain unchanged.
15. Unique-solution checks remain 15/15.
16. Hint Vault/Solutions remain correctly reverse-oriented.
17. Full page-by-page raster visual audit after rendering.
18. No clipping, accidental blank pages, microscopic text, or unnecessary density.
19. Page count is whatever this correct layout needs; do not target 180, 146 or 127.
20. EN remains NOT FROZEN. Do not merge or publish.

## Final workflow

Pull latest branch -> stage the same verified private inputs -> build -> run all deterministic audits -> render all pages -> inspect contact sheets AND enlarged samples -> return the new PDF + QA + page index.

Do not make additional creative changes beyond this bounded owner list.
