# HMDA Book 1 - QA Round 1

Status: **full Production Preview v3 assembled locally (81 pages)**. This is not yet the final KDP interior.

## Fixed in v3

- Replaced the full-black title treatment with a print-safer light title page while keeping the dark gaming HUD language.
- Uses the six-member Happy Makers squad including Grandma Bibi in the opening.
- Case 03 rebuilt so the visual evidence puzzle contains three meaningful differences that affect who / when / where.
- Case 05 had two valid code orders. Added `HEART comes after BOLT`, leaving one solution: `BALL -> STAR -> BOLT -> HEART`.
- Case 08 previously had no valid route. Rebuilt it with three labelled routes and exactly one valid route: `C`.
- Corrected the Grandma Bibi checkpoint numbering to Case 16.
- Case 18 previously produced tied timestamps. Revised values now give one order: `A -> C -> B -> D`.
- Cases 19 and 20 no longer reuse earlier spatial modules. They now use verified Shigai source modules from source pages 10 and 12.
- Case 24 now encodes facing direction versus real travel direction using footprints plus fading mud.
- Case 28 no longer prints the FACT / THEORY / NO EVIDENCE answers beside each statement.
- Added a 3-level Hint Vault for all 30 missions.
- Added solution entries for all 30 missions.
- Added the Room Zero completion certificate.
- `CASE 001 // STILL OPEN` remains the final after-credits page.

## Verified source verdicts currently used

- Case 02 -> PORTIA
- Case 04 -> WARREN
- Case 06 -> INDIA
- Case 07 -> ANN
- Case 10 -> DEXTER
- Case 12 -> JOSEPHINE
- Case 13 -> GEOFFREY
- Case 15 -> REGINALD
- Case 17 -> MARLENE
- Case 19 -> WILSON
- Case 20 -> DELIA
- Case 22 -> RAMONA
- Case 23 -> JASPER
- Case 25 -> FLORENCE
- Boss Case 29 -> source target TRAVIS at coordinate E2

## Still prototype / must be done before KDP

1. Spatial maps still contain Shigai source-room artwork, labels and placeholder character names. Rebuild/re-theme them into the RSE world while preserving the verified geometry.
2. Re-run uniqueness validation after every rebuilt spatial map.
3. The `CHECK THE OLD MAP` meta-story is locked, but the fourteen meta letters are not yet geometry-validated against the raw Shigai room names. Final RSE maps must deliberately provide `C-H-E-C-K-T-H-E-O-L-D-M-A-P` through the hidden second-answer system.
4. Several Quick Mission visuals are intentionally schematic while logic is being locked. Replace them with premium evidence art only after puzzle logic is final.
5. A physical KDP proof copy is mandatory before publication to judge grayscale density, show-through, gutter, writing comfort and paper feel.
6. Recalculate final margins/gutter and final page count after all spatial maps, story art and solution pages are locked.

## Current product structure

- Opening + recruitment
- Rookie Files
- Field Agent
- Master Detective
- Room Zero final act
- Hint Vault
- Solutions
- Room Zero certificate
- After credits: `CASE 001 // STILL OPEN`

The intended production model remains content-driven: YAML/content -> reusable renderer -> automatic preflight -> PDF/PNG outputs. Canva remains a finishing layer, not the source of pagination.
