# HMDA Spatial Case Spread - Production Spec

Status: **CANONICAL PAGE-FAMILY SPEC**

## Why this exists

A spatial case must feel like a real case file, not a worksheet with a map squeezed beside seven clues.

The final spatial experience is a paired page family:

1. **WITNESS BOARD** - story, objective, Happy Makers banter, all fair-play clue statements
2. **LIVE CASE MAP** - large original-Shigai hybrid map, explicit grid coordinates and reader verdict

After the reader solves the case, the normal Room Zero signal / Big Case structure continues.

This preserves the premium original Shigai map scale while keeping every clue readable.

## Witness Board page

Required:
- case number / rank / title
- concise case context
- reader objective
- 1-3 short Happy Makers lines with distinct character voice
- every source-equivalent clue, presented as checkable witness statements
- no answer or solution leakage
- bottom instruction that the map must be solved from evidence, not guessed

The clue page and map page are one case unit. The narrative may be rewritten for RSE style, but source clue meaning may not change.

## Live Case Map page

Required:
- large hybrid map using the **original verified Shigai raster geometry/art**
- final RSE ROOM/ZONE names
- explicit coordinate rail: letters = columns, numbers = rows
- no highlighted meta carrier before Case 26
- no answer marker
- clear verdict field
- optional compact Happy Makers field note only if it does not reduce map readability

Do not shrink the map merely to keep clue cards on the same page.

## Solution treatment

The solution section must pair:
- verified hybrid solution map
- answer + coordinate
- reasoning steps from the canonical `solution_steps`

The source map may show placements, but the explanatory path remains RSE-authored and must show why the conclusion follows.

## Asset boundary

The public GitHub repo stores:
- renderer code
- source hashes
- case IDs
- room skin
- asset-manifest schema

Private/local build storage holds:
- source Shigai PDF/checkpoint
- generated puzzle/solution map rasters

Final release builds attach generated map assets via an external asset manifest. No local Windows path is hard-coded.

## Print rules

- Letter / 8.5 x 11
- grayscale
- predominantly light paper field
- room labels and coordinate rails readable at print size
- no full-black interior page
- furniture/objects remain legible in grayscale
- minimum useful text size must survive 300 dpi print proof
