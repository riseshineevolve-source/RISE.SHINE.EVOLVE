# Happy Makers Detective Academy - Book Factory

Reusable, content-driven production system for the Rise.Shine.Evolve. Detective Academy series.

## Production model

Story and puzzle data live in YAML. Layout and validation live in Python. Character portraits and final spatial maps are replaceable assets. Canva is a finishing layer only, never the source of pagination, solutions or print logic.

## Current Book 1 state

`The Mystery of Room Zero` has a complete 30-mission editorial structure. The latest assembled editorial-lock build is **84 pages before final spatial-map replacement** and includes:

- reader recruitment + Detective ID
- all six Happy Makers including Grandma Bibi
- Rookie / Field Agent / Master Detective / Room Zero progression
- Cases 01-30 and the complete Room Zero final act
- `CHECK THE OLD MAP` meta reveal
- 3-level Hint Vault for all 30 missions
- reader-facing solutions for all 30 missions
- Room Zero certificate
- final `CASE 001 // STILL OPEN` after-credits hook
- print-safe grayscale UI with no full-black interior pages

`EDITORIAL_LOCK_v4.md` is the editorial boundary. Do not reopen the core Room Zero twist, reader-is-the-missing-detective reveal, Happy Makers roles, 30-mission architecture, rank progression, Hint Vault structure or series hook without explicit approval.

## Final spatial source bank

The Shigai selection phase is complete. Production now uses the locked final source files:

- `HMDA_checkpoint_19_HMDA20_UPGRADE.shigai.json`
- `HMDA_SHIGAI_SOURCE_15_MODULES_FINAL.pdf`

Their SHA-256 hashes and the exact 15-module selection are stored in:

- `content/spatial_source_manifest_final.yml`
- `SPATIAL_SOURCE_LOCK.md`

Final upgrades retained from the later Shigai pass include:

- HMDA_13 - `What Happened to the Empty Display?` - EXPERT 8.4
- HMDA_19 - `The Relic and the Little Ledger Note` - EXPERT 8.2
- HMDA_20 - `The Adventure: The Missing Relic` - EXPERT 8.3
- HMDA_22 - `The Remarkable Adventure: The Heirloom` - EXPERT 8.3

The locked 9x9 boss source is **`The Search for the Unclaimed Gem`**, stored answer **Vera @ D3**. Earlier experimental boss candidates are not production sources unless a new source export is explicitly approved.

## Room Zero meta engine

The fourteen non-boss spatial cases spell:

`CHECK THE OLD MAP`

The final RSE map system distinguishes **ROOMS** from **ZONES**. Mission 26 asks the reader to inspect only spaces visibly styled as ROOM. After the verified placement, each marked case has exactly one empty ROOM. Its first letter is the hidden meta letter. Extra empty source partitions are intentionally re-skinned as corridors, platforms, queues or other ZONES and never count as the meta answer.

The room/zone skin is locked in:

`content/spatial_room_skin.yml`

The meta carrier must never receive special visual emphasis before Mission 26. It should look like any other room.

## Source validation

Run the source-lock validator whenever the selection or room skin changes:

```bash
cd tools/detective-book-factory
python scripts/validate_spatial_source_manifest.py \
  --manifest content/spatial_source_manifest_final.yml \
  --skin content/spatial_room_skin.yml \
  --checkpoint /path/to/HMDA_checkpoint_19_HMDA20_UPGRADE.shigai.json
```

The gate checks:

- selected raw title/page identity
- source answer and exact coordinate
- one-person-per-row and one-person-per-column placement
- no person on a blocked source cell
- source owner-answer room relation
- full source-room coverage by the RSE room/zone skin
- exactly one empty final ROOM in every marked case
- final message `CHECK THE OLD MAP`

This is a structural source gate. The final rewritten RSE clues receive a second semantic/solver validation before publication.

## Map Factory

The old two-case pilot remains useful as development history, but it is **not** the source of truth for Book 1. The final renderer must ingest the locked selection plus native source geometry and produce new RSE maps without Shigai branding or raw generator art.

Final visual rules:

- preserve source grid topology and blocked/occupiable meaning
- preserve repeated-object equivalence when a clue depends on it
- replace Shigai people, room names and story framing with final RSE case content
- use light grayscale gaming/dossier design, not noir and not worksheet styling
- distinguish ROOM and ZONE clearly but subtly
- keep the meta-carrier room visually ordinary
- puzzle map contains no answer markers
- solution map shows placements and a short deduction trail
- HMDA_29 resolves to a coordinate used by the Room Zero finale, not a criminal verdict

See `MAP_FACTORY_FINAL_SPEC.md` for the production contract.

## Build locally

```bash
cd tools/detective-book-factory
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python render_book.py --content content/book1_en_production.yml --output dist/HMDA_Book1.pdf
python scripts/preflight.py --content content/book1_en_production.yml --pdf dist/HMDA_Book1.pdf --min-pages 25 --report dist/preflight.txt
python scripts/make_previews.py --pdf dist/HMDA_Book1.pdf --out dist/previews --dpi 144
```

## Cloud build

Pushes to `feature/detective-book-factory` use the Book Factory GitHub Actions pipeline for repeatable artifacts. The workflow should remain isolated from the live website until the book branch is explicitly approved for merge.

## Current next tranche

1. Render three final-system pilots: HMDA_02, HMDA_13 and HMDA_29.
2. Lock final case-specific prop skins and character aliases while preserving source clue semantics.
3. Extend the true RSE vector renderer to all 15 selected spatial modules.
4. Rewrite and independently validate the final reader-facing clues and solution trails.
5. Replace temporary spatial assets in the full 30-mission book build.
6. Run page-by-page visual QA, KDP print preflight and physical proof.
7. Create the Polish localization source after the English layout is stable.

## Series reuse

Book 2 or another language edition should require mostly new content YAML plus new puzzle/art assets. Reusable components include page templates, Happy Makers callouts, chapter gates, Hint Vault, solution layouts, map validation, preflight and export.
