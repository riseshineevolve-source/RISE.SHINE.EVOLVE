# HMDA Book 1 — V3 premium interior owner-review checkpoint

Date: 2026-09-29
Branch: `feature/detective-book-factory`
Base HEAD checked before work: `989bce1fc1846fcb2480517d1b4965f3add204aa`
Scope: complete English Book 1 interior owner-review render; no English freeze or KDP upload.

## Bound inputs

- Canonical reader text commit: `3c0caedbcc313658767cb4251b2c1741c4a7edcf`.
- Factory V3 text blob: `8370026a811ad3354aaa8e422ebe2edf58464845` (Git LF blob; Windows CRLF is normalized only for verification).
- Exact owner packet SHA-256: `55439b308d6d7a2db7b40485665bcc46aceeb9dffde528afffb276790378680c`.
- All four owner visuals match `content/v3_owner_visual_contract.json`; all 30 locked spatial puzzle/solution rasters match `content/v3_locked_spatial_evidence_contract.json`.
- The render bridge runtime is SHA-256 `06bb284162ab62e993c8eee9237c58b67b6b545a425d2b04085725a81d50afc8`. It is the packet render runtime, not the unrecovered byte-identical source runtime (`3b3328fe9072bb4e62ef51589410f3193bb1c5c0b67de2c48c0f2173670b6d45`). This distinction remains explicit in the locked contract.
- The audited evidence hydration master is a separate private input with SHA-256 `0a61b726e6335cc731f114749db632b6b0a50f2a8da76ef763a8961e066feacc`; the ZIP's V4 master is different. The scanner squad variant is a separate private input with SHA-256 `9129bfa03c7f347e27ae9b98c431395916b0c9cc12924b158116360a4869620e`.
- Page 3 uses the owner-approved scanner-emblem variant. The original squad image file was preserved, as directed by the owner.

## Output

- `dist/HMDA_Book1_EN_PREMIUM_ALMOST_KDP_READY_V3.pdf`
- PDF SHA-256: `2a2fffebfe43ddc4d3e50c22e27b1e9bb68225d01a6a786ca9e0c118996af858`.
- 180 physical pages, all 612 × 792 pt (8.5 × 11 in), grayscale, no bleed.
- Page index: `dist/HMDA_Book1_EN_PREMIUM_ALMOST_KDP_READY_V3_page_index.json` with physical page, family, case, physical left/right side and reading orientation.
- Consolidated preflight: `dist/HMDA_Book1_EN_PREMIUM_ALMOST_KDP_READY_V3_final_QA.json` (`PASS`); structural and grayscale subreports use the same PDF SHA.
- Visual package: `dist/v3_premium_review/final/pages/page-*.png` (180 page renders) and `contact-01.jpg` through `contact-09.jpg` (all pages numbered).

Spatial Witness Board left-page / live map right-page pairs (physical pages):

`02:16/17, 04:24/25, 06:32/33, 07:36/37, 10:44/45, 12:50/51, 13:54/55, 15:60/61, 17:68/69, 19:74/75, 20:78/79, 22:86/87, 23:90/91, 25:96/97, 29:108/109`.

Case 03 Photo A/B are pages 20/21; the tracker has exactly ten question marks. STOP is page 121. The 59 subsequent support pages have a true 180-degree content transform.

## Verified checks

- Source verifier: 30 main cases, 30 × 3 hint cases, 30 solutions; all V3 invariant checks pass.
- PDF regression: 714 substantive reader-text fragments checked, zero missing; 30 case titles match across index, brief and solution.
- Spatial logic: all 15 locked cases have exactly one exhaustively enumerated solution using the audited packet runtime; all 15 named answer witnesses appear on their Witness Boards.
- Case 05: six printed clue constraints yield exactly `BALL → STAR → BOLT → HEART → KEY → MOON`.
- Asset hashes: four owner visuals and 30 locked maps pass exact-file checks. Original source assets were not modified.
- Print preflight: used Arial/Arial Bold font subsets embedded; 4,695 vector color operators and 36 embedded images are grayscale; no glyph or embedded image enters the 30 pt horizontal / 18 pt vertical trim inset; renderer reported zero overflow errors.
- Visual QA: all nine final numbered contact sheets inspected; enlarged review covered publication/squad/index pages, case brief/notes/Witness Board/map, Case 03 A/B and tracker, finale, reverse support and solution examples. No visible clipping or accidental blank page found. The parity preparation pages were enlarged into usable lined evidence modules; case file and rules panels and chat markdown were corrected during this pass.

## Remaining gates

This is an owner-review artifact. The owner must review the pages, including physical map/axis and handwriting readability. After bounded fixes: KDP Previewer, representative physical proof, explicit English freeze, cover spine recalculation and owner-controlled upload. The exact owner image/map files and rendered `dist` package are local production inputs/artifacts and have not been committed as private source material. A clean CI machine needs approved private distribution of the hash-pinned packet, evidence master and scanner variant before it can reproduce this PDF; `scripts/prepare_v3_premium_inputs.py` verifies and stages them. The source-locked runtime byte file is still unrecovered, despite the 15 unique-solution checks on the audited packet render runtime.
