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

---

## Delta — 2026-09-24: modern-prop audit and safe scaffolding

This delta supersedes only the object-art assumption above; later Book 1
checkpoints remain authoritative for work completed after 2026-09-21.

### Audit result

**NOT INTEGRATED:** the current production map path still uses
`hybrid-original-shigai`, and `render_spatial_map_hybrid_hardened.py`
explicitly preserves original object art in the source raster.
`validate_spatial_object_art.py` also protects the dark-pixel core of every
locked object cell. The existing maps therefore do **not** yet contain a
modern-prop replacement layer.

### Safe work completed

- Added `MODERN_PROP_PRESENTATION_CONTRACT.md`.
- Added `content/modern_prop_catalog.template.yml` without guessing source
  object types.
- Added `scripts/validate_modern_prop_contract.py`.
- The validator checks runtime cell/type/variant/blocked/occupiable semantics,
  rejects blocked/occupiable drift, checks catalog compatibility, inventories
  unmapped object types and emits `object_semantics_sha256`.
- Added a deterministic self-test proving that presentation-key changes do not
  change the semantic fingerprint, missing mappings fail closed in release
  mode, and semantic drift is rejected.
- No source raster, puzzle geometry, clue, answer, witness placement, Room Zero
  meta logic or owner visual asset was changed.

### Verification

- LOCAL PASS: `python scripts/validate_modern_prop_contract.py --self-test`.
- CI hook added to the Detective build so the contract self-test runs on every
  relevant pull-request build.
- Real all-15 object inventory remains a private-runtime step; no source object
  types were invented in GitHub.

### Next safe slice

1. Run inventory-only validation against the generated private all-15 runtime
   when that runtime is available to the execution environment.
2. Populate a private/release catalog from the exact discovered object types.
3. Add opt-in renderer support and a footprint-safety validator before any
   original Shigai object pixels are replaced.
4. Preview representative 6x6 / 7x7 / boss 9x9 maps before all-15 scale-out.

Production modern-prop substitution is intentionally **not** performed in this
delta.

---

## Delta — 2026-09-24: cell-confined overlay planner and asset contract

### Safe work completed

- Added `scripts/modern_prop_presentation.py` as an **isolated overlay planner**,
  not as a production substitution path.
- Added `content/modern_prop_assets.template.yml`; it intentionally contains no
  guessed presentation keys or object types.
- The planner resolves exact runtime type/variant mappings, validates asset-pack
  keys and SHA-256 hashes, rejects path traversal/non-PNG assets, and computes
  deterministic per-cell safe boxes.
- `cell_core` is confined to normalized cell bounds `(0.16, 0.16)-(0.84, 0.84)`;
  `cell_center_safe` is confined to `(0.24, 0.24)-(0.76, 0.76)`.
- The planner can render a transparent **isolated** sprite layer only. It does
  not erase or overwrite original Shigai pixels and is not wired into the
  production map renderer.
- The produced plan retains `cell`, source type/variant,
  `occupiable`/`blocked`, asset hash and the same immutable object-semantics
  fingerprint.

### Verification

- LOCAL PASS: `python scripts/modern_prop_presentation.py --self-test`.
- The self-test covers representative synthetic 6x6, 7x7 and 9x9 boards and
  proves every rendered alpha pixel stays inside the approved object-cell box.
- PASS: missing assets fail closed.
- PASS: path traversal fails closed.
- PASS: blocked/occupiable drift fails closed.
- PASS: presentation changes do not change the semantic fingerprint.
- CI wiring added to compile and run the new self-test.
- GitHub Actions `Build Detective Academy PDF` run **#160** at head
  `c065f222ee6fa698c7111464aa3b5b45774a62d2` completed **SUCCESS**.

### Current blocker / boundary

The generated all-15 private runtime is still not present in the current remote
execution artifact, so exact source object types and real modern-prop asset keys
cannot be populated without guessing. No guessing was performed.

### Next safe slice

1. Add the independent before/after footprint validator that proves a future
   modern-prop composite changes pixels only inside catalog-approved object
   boxes and leaves all non-object cells untouched.
2. When the exact private runtime becomes available, run inventory-only mode,
   populate the catalog and asset manifest from discovered types only, then
   generate isolated overlays for representative 6x6 / 7x7 / 9x9 cases.
3. Production substitution stays disabled until the footprint validator and
   representative visual QA both pass.
