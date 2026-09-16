# Happy Makers Detective Academy - Book Factory

Reusable content-driven PDF generator for the Rise.Shine.Evolve. Detective Academy series.

## Production model

Story and puzzle data live in YAML. Layout lives in Python. Character portraits and spatial logic modules are replaceable assets. Canva is a finishing layer, not the source of pagination.

## Current Book 1 state

`The Mystery of Room Zero` now has a complete 30-mission production structure and a locally assembled 81-page Production Preview v3 with:

- opening recruitment + Detective ID
- six-member Happy Makers squad including Grandma Bibi
- Rookie Files, Field Agent and Master Detective progression
- Room Zero final act and `CHECK THE OLD MAP` meta reveal
- corrected Quick Missions after QA
- verified Shigai spatial modules mapped to story cases
- 3-level Hint Vault for all 30 missions
- solution entries for all 30 missions
- Room Zero certificate
- final after-credits hook: `CASE 001 // STILL OPEN`

See `QA_ROUND1.md` for the current blocker list and source verdicts.

## Build locally

```bash
cd tools/detective-book-factory
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python render_book.py --content content/book1_en_production.yml --output dist/HMDA_Book1_Production_Preview_v1.pdf
python scripts/preflight.py --content content/book1_en_production.yml --pdf dist/HMDA_Book1_Production_Preview_v1.pdf --min-pages 25 --report dist/preflight.txt
python scripts/make_previews.py --pdf dist/HMDA_Book1_Production_Preview_v1.pdf --out dist/previews --dpi 144
```

## Map Factory pilot (spatial-map visual rebuild)

`content/spatial_map_pilots.yml` holds two raw candidate spatial-deduction
modules (`HMDA_10`, `HMDA_17`) imported from a native Shigai checkpoint as a
pilot for the reusable, code-drawn, grayscale map renderer that will
eventually replace the raw Shigai scan crops used by `spatial_puzzle_page`
in `render_book.py`. Neither pilot case is currently mapped to a retained
Book 1 case (see `content/shigai_module_map.yml`); they exist only to prove
the visual system before scaling to the 14 retained maps.

```bash
cd tools/detective-book-factory
python -m venv .venv && .venv\Scripts\activate  # or source .venv/bin/activate
pip install -r requirements.txt
python scripts/validate_spatial_map_pilot.py --manifest content/spatial_map_pilots.yml
python scripts/render_spatial_map.py --manifest content/spatial_map_pilots.yml --out dist/spatial_maps
```

`validate_spatial_map_pilot.py` proves topology, room partition, furniture
placement, answer identity and (via brute-force search) unique solvability
against SHA-256 baselines pinned in each case's `integrity` block, and fails
the build if a rebuild ever changes verified geometry. `render_spatial_map.py`
draws the canonical puzzle/solution maps and rasterizes PNG previews; it
reads geometry only from the manifest, never from artwork.
`scripts/build_spatial_map_pilot_manifest.py` is the reusable ingestion tool
that mechanically imports grid/room/furniture/placement data from a Shigai
checkpoint for future cases -- constraints must still be hand-authored and
proven by the validator, never auto-guessed from clue text.

## Cloud build

Pushes to `feature/detective-book-factory` trigger `.github/workflows/build-detective-book.yml`. The workflow builds the PDF, runs preflight, creates PNG previews, and uploads everything as a GitHub Actions artifact.

## Asset rules

- `assets/production/*.png|jpg`: normalized grayscale Happy Makers portraits and temporary verified spatial modules.
- Temporary Shigai map assets are logic references only. Final publication art must be rebuilt/re-themed while preserving verified clue geometry.
- Every reframed spatial case must be revalidated before publication.
- The fourteen hidden meta outputs must spell `CHECK THE OLD MAP` after the final RSE map rebuild.
- Avoid full-black interior pages. Use dark HUD panels on light pages for print safety.

## Current next tranche

1. Rebuild the fourteen meta-carrying spatial maps in a consistent RSE visual system.
2. Lock the `CHECK THE OLD MAP` empty-room letter sequence into those maps.
3. Revalidate every rebuilt spatial puzzle for uniqueness.
4. Replace remaining schematic Quick Mission art with premium grayscale evidence art.
5. Upgrade the renderer/workflow so GitHub Actions produces the same full-book build, not only the early preview tranche.
6. Run final KDP print preflight and order a physical proof.

## Series reuse

Book 2 or another language edition should require mostly new YAML plus new puzzle/art assets. Page templates, Happy Makers callouts, chapter gates, hint pages, solution layouts, preflight and export stay reusable.
