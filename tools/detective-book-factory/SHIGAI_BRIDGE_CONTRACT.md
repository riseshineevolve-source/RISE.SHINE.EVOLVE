# HMDA Shigai Bridge Contract

Status: **CANONICAL RECOVERY CONTRACT**
Launch issue: #585

## Problem this solves

The Detective Academy production system must survive loss of a chat, local working directory or Shigai browser session.

The bridge therefore treats the native Shigai file as an external immutable input and GitHub as the durable record of exactly which source geometry is allowed into Book 1.

## Durable split

### GitHub stores

- expected source SHA-256
- selected case IDs
- source scene/clue indices
- raw source title
- expected grid / difficulty
- expected answer + coordinate
- final ROOM/ZONE skin
- final RSE room names
- extraction / validation code
- content and renderer code

### External/private storage keeps

- native `.shigai.json`
- source PDF / ZIP / PNG exports
- any source-generator artwork that should not be copied into a public repository

## Required bridge behavior

A bridge command must:

1. receive the checkpoint path explicitly
2. compute SHA-256 and fail closed on mismatch
3. load only the cases selected by `spatial_source_manifest_final.yml`
4. locate pages using the locked checkpoint scene/clue indices
5. prove both pages resolve to the expected source board
6. prove expected rows, columns, raw title, stored answer and coordinate
7. apply final ROOM/ZONE display skin without changing source cells
8. emit a deterministic local normalized runtime bundle
9. never require the original chat transcript
10. never hard-code a user's Windows path

## Normalized runtime bundle

For every selected case the local bundle should contain at minimum:

- case id
- provenance hash
- raw source title
- final case title
- rows / columns
- room index per cell
- final room display names + ROOM/ZONE kind
- doors if present
- object type / cell / blocked-or-occupiable meaning
- characters
- raw clue text
- verified placements
- source answer + coordinate
- difficulty metrics
- source solve hints / deduction steps where available
- locked meta letter / room where applicable

The normalized bundle is generated, not hand-edited.

## Publication boundary

Raw Shigai story language and source character identities are not automatically publication copy.

Final reader-facing clues must be rewritten into the RSE story and then semantically checked against the normalized source logic.

## Recovery command target

The intended end-state is conceptually:

```bash
python scripts/extract_shigai_runtime.py \
  --checkpoint /private/path/HMDA_checkpoint_19_HMDA20_UPGRADE.shigai.json \
  --manifest content/spatial_source_manifest_final.yml \
  --skin content/spatial_room_skin.yml \
  --output /private/work/HMDA_BOOK1_RUNTIME.json
```

After this succeeds, Map Factory work no longer depends on reopening Shigai or recovering an old chat.
