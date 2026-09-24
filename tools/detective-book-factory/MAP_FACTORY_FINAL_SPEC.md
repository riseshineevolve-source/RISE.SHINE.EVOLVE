# HMDA Map Factory - Final Production Contract

Status: **CANONICAL IMPLEMENTATION SPEC**
Launch issue: #585

## Purpose

Turn a locked Shigai logic source into publication-safe Happy Makers Detective Academy puzzle and solution maps without altering the verified deduction geometry.

Shigai is a **source logic generator/reference**, not the final book layout and not the durable source of RSE narrative.

## Inputs

Required:

- external native Shigai checkpoint
- `content/spatial_source_manifest_final.yml`
- `content/spatial_room_skin.yml`

Optional supporting source PDF may be used for visual comparison only.

## Immutable puzzle facts

The production system must preserve:

- grid rows / columns
- source partition topology
- blocked vs occupiable cell semantics
- furniture/object cell location when a clue depends on it
- source character placement
- source clue meaning
- unique verified source answer and coordinate

A change to any item above requires revalidation and must not be treated as a cosmetic edit.

## RSE-owned transformation layer

The Map Factory may change:

- room display names
- whether a source partition is presented as ROOM or ZONE
- character display aliases
- prop display labels when semantic equivalence is preserved
- typography
- borders / fills / icons
- evidence-card styling
- story framing
- Happy Makers chrome
- solution presentation

The transformation layer must never make the meta carrier visually special before Case 26.

## Room Zero meta contract

For cases 02, 04, 06, 07, 10, 12, 13, 15, 17, 19, 20, 22, 23 and 25:

- solve using the locked source placement
- count only final spaces marked `kind: room`
- exactly one final ROOM must remain empty
- its first letter must equal the case's locked meta letter
- concatenation must equal `CHECKTHEOLDMAP`

Spaces marked ZONE are deliberately excluded from the meta answer.

## Required outputs per spatial case

- normalized runtime geometry JSON/YAML
- reader puzzle map asset
- completed solution map asset
- validation report containing:
  - source hash
  - source case identity
  - grid
  - stored answer
  - answer coordinate
  - unique-solution status
  - meta-room status if applicable

No source-production wording such as Shigai, raw module, victim/murderer generator terminology or internal IDs may appear in reader-facing output.

## Rendering direction

- Letter 8.5 x 11 compatible
- grayscale
- light page field
- clear grid coordinates
- premium detective-game/dossier feel
- enough white space for pencil use
- readable at print size
- no answer marker on puzzle map
- solution map may show placements and the short deduction trail
- character/prop icons must remain legible when printed in grayscale

## Pilot gate

Before scaling, render:

1. HMDA_02, early 6x6
2. HMDA_13, advanced 7x7
3. HMDA_29, 9x9 boss

These three must prove readability, visual hierarchy, solver integrity and scalability.

Final visual choice is an OWNER GATE. After approval, scale mechanically.

## Validation order

1. checkpoint hash
2. source identity / scene index
3. topology
4. blocked/occupiable semantics
5. placement + stored answer coordinate
6. source clue/solution consistency
7. final ROOM/ZONE skin
8. Room Zero meta carrier
9. final rewritten clue semantic equivalence
10. print visual QA

A visual PASS may never override a logic FAIL.
