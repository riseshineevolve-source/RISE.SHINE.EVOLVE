# Owner Review V2 correction pass

English remains open for owner review. This work is isolated to the Book Factory
branch; the live website, cover, pricing and Polish edition are unchanged.

## Recovery and preservation

The run began at `71baf0c` with two uncommitted map-renderer corrections and an
existing all-15 output set. Both source changes were preserved before editing.
Existing outputs were inspected first. Regeneration was necessary after verified
systemic defects were found, rather than because an earlier process was assumed
incomplete. Unrelated local files and the earlier OwnerReview PDF were retained.

The remote branch advanced to `ee13d26` during the sprint. Its approved-squad
resolver is incorporated intact, and the build workflow uses its strict switch.
Both histories are retained by a normal merge before the final normal push.

## Production changes

- Canonical modern squad PNG is durable under `assets/images/Happy Makers detectives.png`.
  Sync uses `--require-approved-squad`; normalized individual character art is unchanged.
- Body, clue and instruction copy uses 11–12 pt where applicable; essential
  labels have a 9.5 pt floor. Text uses black on light or white on dark.
  Measured text helpers fail on overflow instead of silently shrinking copy.
- Opening panels, guided examples, the single Detective ID, evidence tables,
  Hint Vault, solutions and finale share the corrected hierarchy and safe margins.
  Writable names, notes, codes and verdicts use white surfaces and black lines.
- The Witness Board has a case/rank/status header, hook, objective, agent note,
  numbered evidence cards, bold names, and checkboxes. All source clues are retained.
- Puzzle maps occupy approximately seven inches of the Letter page; solution maps
  use six inches. Effective raster resolution is at least 300 dpi. Coordinates
  are black bold 14–16 pt; room labels are at least 10.5 pt at solution scale.
- Map paper is whitened while retaining object art, wall geometry, doors and a
  usable coordinate lattice. Labels are placed only in verified room-owned
  whitespace, without reducing type size.
- The crop detector requires a complete square outer frame. The earlier detector
  included non-map material in three puzzle crops and dropped upper rows from
  HMDA_17's solution. Synthetic regressions cover both failures.
- Contours centered on locked object art are rejected as labels. This prevents
  bench seats from being erased as false room-name pills. Paired source evidence
  and explicit normalized footprints resolve attached labels without guessing.
- The generated V2 master applies the approved character and room display names
  consistently across clues, hints, maps, verdicts and solutions. Existing final
  room phrases are protected against repeated substitution. Source identities
  and canonical content files remain unchanged.

## Logic boundary

All 15 extracted runtime cases exactly match fresh extraction from the locked
checkpoint: geometry, rooms, zones, doors, objects, blocked/occupiable cells,
placements, source clue text, hints, explanations, answers and coordinates.
There are still 30 ordered missions and 15 spatial modules. The boss answer
remains Vega at D3, and the meta message remains `CHECK THE OLD MAP`.

This is source-lock and presentation regression evidence, not a new independent
solver of all prose clues. Display-name substitutions do not change deduction
constraints. Pixel-level object checks and visual review supplement runtime
equality, because unchanged JSON alone cannot prove that raster art survived.

## Reproduction

From this directory, with the existing private locked source and runtime available:

```powershell
python scripts/sync_brand_assets.py --require-approved-squad
python scripts/build_book1_master.py --output dist/book1_en_master.yml
python scripts/render_spatial_map_hybrid_hardened.py --source-pdf <locked-source.pdf> --runtime dist/hmda_spatial_runtime_aliases.json --out dist/map_factory_owner_review_v2
python scripts/build_owner_review_v2.py --master dist/book1_en_master.yml --runtime dist/hmda_spatial_runtime_aliases.json --maps dist/map_factory_owner_review_v2 --output dist/HMDA_Book1_EN_OwnerReview_v2.pdf
python scripts/render_spatial_case_spreads.py --master dist/book1_en_master_owner_review_v2.yml --runtime dist/hmda_spatial_runtime_aliases.json --maps dist/map_factory_owner_review_v2 --out dist/spatial_spreads_owner_review_v2
python scripts/preflight.py --content dist/book1_en_master_owner_review_v2.yml --pdf dist/HMDA_Book1_EN_OwnerReview_v2.pdf --min-pages 141 --report dist/HMDA_Book1_EN_OwnerReview_v2_preflight.txt
python scripts/audit_owner_review_v2.py --content dist/book1_en_master_owner_review_v2.yml --pdf dist/HMDA_Book1_EN_OwnerReview_v2.pdf --runtime dist/hmda_spatial_runtime_aliases.json --out dist/owner_review_v2_qa
```

The native map renderer also needs NumPy and OpenCV. Private source/runtime files,
generated books, previews, maps, environment dependencies and local caches are not
committed. CI builds the source-driven editorial edition without private maps;
the complete V2 production artifact is verified locally.

## Review packet

Local outputs under `dist/` include the new 141-page V2 PDF, production preflight,
all 30 map rasters, 15 two-page map PDFs, 15 paired Witness Board/map spreads,
141 page previews at 150 dpi, opening/onboarding, map, Witness Board and writing
contact sheets, plus representative and squad previews. The original PDF remains
available separately.

Machine audit covers Letter geometry, no-bleed margins/gutter, embedded fonts,
minimum text size, text contrast, image color/resolution, missing/duplicate assets,
alias/room-name drift, page families, answer coordinates and Room Zero copy.
Visual evidence names the actual inspected pages and distinguishes overview
contact sheets from full-page previews. Neither is a physical paper proof.

KDP checks follow the current [print options](https://kdp.amazon.com/en_US/help/topic/G201857950)
and [trim/margin guidance](https://kdp.amazon.com/en_US/help/topic/GVBQ3CMEQW3W2VL6):
8.5 × 11 inch no-bleed trim, at least 0.375 inch inner gutter for 141 pages,
at least 0.25 inch outer/top/bottom margins, embedded fonts, grayscale art and
300 dpi placed rasters. No upload or publication is performed.

## Final local validation

PASS: 141 Letter pages, 30 missions, 15 Witness Boards, 15 puzzle maps and all
30 mission solutions. The final strict PDF audit reports zero errors and zero
warnings. All 141 page previews and the requested contact sheets are generated.

Final PDF SHA-256:
`ee42ff3ba086883bf2bab8b54f7ce1361bb3f50530eef5c519004c43317b60d4`.

PASS: locked checkpoint/runtime equality, canonical 30-mission audit, source-grid
crop regressions, topology/bench rejection tests and synthetic spread rendering.
The object-art gate checks 520 object cores across all 30 final rasters, retaining
8,100,765 protected dark pixels with zero losses. Every actual source-label
exemption and final map hash is recorded; eight harmless gray-to-black marker-edge
pixels are distinguished from lost artwork. This check does not claim to certify
every object edge, raster label or room wall.

PASS: all 141 pages reviewed in contact sheets; 18 nonspatial full-page samples
inspected separately; all-15 map, board and spatial-solution sheets reviewed.
Full-page spatial checks explicitly include HMDA_02, HMDA_13 and HMDA_29,
corrected early Witness Boards, museum/camp solutions and the changed first
Hint Vault page. Poppler also renders the final boss solution successfully.
Unchanged nonspatial previews are verified by image hashes after the final
spatial repair. No unresolved digital visual blockers remain.

The complete evidence is in `dist/owner_review_v2_qa/`, the production preflight,
`dist/owner_review_v2_logic_report.txt` and
`dist/owner_review_v2_object_art_report.json`. Generated evidence and the review
packet remain local. CI is run once through the existing draft PR at the coherent
pushed boundary; its result is recorded in the delivery report and local packet.

Next step: owner reads the V2 PDF and prints representative pages at 100% scale
to judge pencil space, paper contrast and binding comfort. English is not frozen;
no KDP upload, merge to main, publication or Polish translation is authorized by
this pass.
