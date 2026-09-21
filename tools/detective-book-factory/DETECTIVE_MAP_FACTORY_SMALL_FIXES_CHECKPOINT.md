# Detective Map Factory — Small Fixes Checkpoint

Status: **PARTIAL PASS — PILOT MAP LAYER**  
Date: 2026-09-21

## Applied presentation changes

- Retained the original verified Shigai map art and source geometry.
- Kept the hybrid map field light/white and preserved pencil-work space.
- Increased the hybrid room/zone label sizing while retaining the original
  label footprint and map topology.
- Added bold external coordinate rails to the final Letter-size map pages.
- Added a deterministic `spatial_character_aliases.yml` presentation layer.
  It maps every stable source identity to exactly one public HMDA alias.

## Alias safeguards

`extract_shigai_runtime.py` now fails closed if a case has a missing or extra
source identity, blank alias, duplicate alias, or duplicate alias initial.
The runtime retains `source_name`, source placement, raw clue and answer
coordinate alongside the presentation `display_name`; verdicts and solution
legends use the alias only.

## Pilot artifacts

- `dist/map_factory_hybrid_pilots/HMDA_02_hybrid_final.pdf`
- `dist/map_factory_hybrid_pilots/HMDA_13_hybrid_final.pdf`
- `dist/map_factory_hybrid_pilots/HMDA_29_hybrid_final.pdf`
- `dist/hmda_spatial_runtime_aliases.json` (generated private runtime evidence)

## Validation

- PASS: all 15 selected modules match the locked checkpoint hash and source
  identity.
- PASS: `CHECKTHEOLDMAP` ROOM/ZONE carrier contract.
- PASS: runtime extraction validates all alias mappings before rendering.
- PASS: HMDA_02 / HMDA_13 / HMDA_29 hybrid puzzle and solution PDFs render.

## Remaining required work

- Implement the reusable premium Witness Board page family with alias-aware,
  bolded clue-card names and attach it to the canonical master renderer.
- Produce paired spread/contact-sheet previews, inspect all pilot pages at
  print scale, then scale unchanged logic mechanically to all 15.
- Run strict full-book preflight only after all final spatial assets are attached.
