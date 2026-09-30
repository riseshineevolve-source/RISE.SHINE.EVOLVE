# HMDA Book 1 - KDP Launch Checkpoint

Status: **ACTIVE / RECOVERABLE**
Launch issue: #585
Branch: `feature/detective-book-factory`

This file is the restart point when chat history is missing. Read it before doing new Detective Academy work.

## Product

**Happy Makers Detective Academy: The Mystery of Room Zero**

Target: fastest safe route to an English KDP paperback, followed by a Polish edition from the same canonical content model.

## Locked editorial decisions

Do not reopen without owner approval:

- reader is recruited as the missing detective
- six Happy Makers guide the reader, including Grandma Bibi
- 30-mission structure
- Rookie -> Field Agent -> Master Detective -> Room Zero progression
- Rule Zero: `ZERO ASSUMPTIONS. NOTICE FIRST. THEORIZE SECOND.`
- 14-case meta message: `CHECK THE OLD MAP`
- Room Zero final reveal
- 3-level Hint Vault model
- certificate
- after-credits `CASE 001 // STILL OPEN`
- grayscale / print-safe dossier-game direction
- no full-black interior pages

`EDITORIAL_LOCK_v4.md` is the editorial lock.

## Source-of-truth precedence

When files disagree, use this order:

1. `content/spatial_source_manifest_final.yml`
2. `SPATIAL_SOURCE_LOCK.md`
3. external native Shigai checkpoint whose SHA matches the manifest
4. `content/spatial_room_skin.yml`
5. canonical renderer-ready 30-mission master once created
6. `EDITORIAL_LOCK_v4.md`
7. `book_en.yml` for the locked 30-mission story blueprint
8. old phase / QA / pilot files as historical support only

Never let old names, answers, page numbers or coordinates override the final spatial source manifest.

## Locked Shigai source

Native checkpoint:
`HMDA_checkpoint_19_HMDA20_UPGRADE.shigai.json`

Expected SHA-256:
`cdc6de5b60117fe19e89fc4a13e2b9c1d92657f5e7fdb8ec69a18ae85ba8723e`

Supporting source PDF:
`HMDA_SHIGAI_SOURCE_15_MODULES_FINAL.pdf`

Expected SHA-256:
`6662c292642f3d66148e41eef180bb7d2b15a0975ca822981f4f33aa7153aada`

The checkpoint may contain additional candidate boards. **Only the 15 cases in `content/spatial_source_manifest_final.yml` are Book 1 production sources.**

## Final 15 selected spatial modules

`HMDA_02, 04, 06, 07, 10, 12, 13, 15, 17, 19, 20, 22, 23, 25, 29`

The fourteen non-boss cases carry the second-answer letters:
`C H E C K  T H E  O L D  M A P`

HMDA_29 is the 9x9 boss source and resolves to **Vera @ D3** in the locked source.

## What exists now

### Strong

- full 30-mission story blueprint: `content/book_en.yml`
- detailed renderer-ready Cases 01-05: `content/book1_en_production.yml`
- later production copy for Cases 17-30: `content/book1_en_phase3.yml`
- final Shigai selection manifest
- ROOM/ZONE final skin
- source validator
- pilot map validator / solver
- reusable ReportLab book renderer
- editorial preview CI
- Happy Makers asset sync
- preflight and preview generation

### Canonical English master recovery — PASS

The earlier reproducibility gap is now closed.

The branch contains a deterministic master builder:
- `scripts/build_book1_master.py`

and a launch-state auditor:
- `scripts/audit_book1_launch_state.py`

Current CI evidence from **Build Detective Academy PDF run #72 / run id 35336391714**:
- `PASS: assembled canonical HMDA Book 1 master with 30 missions`
- assembled canonical master: **30 missions**
- locked spatial sources: **15**
- editorial preview built successfully at **141 pages**
- editorial preflight: **PASS**

The durable generated source is:
- `dist/book1_en_master.yml`

This means the complete English editorial master is now reproducible from GitHub logic/content. The remaining release blocker is no longer missing Book 1 content assembly.

### Current critical gap

All 15 locked spatial cases still require final Map Factory puzzle + solution raster assets. Editorial preview mode currently renders explicit placeholders and is intentionally **not release-ready** until those assets are promoted.

Current pending spatial sources:
`HMDA_02, 04, 06, 07, 10, 12, 13, 15, 17, 19, 20, 22, 23, 25, 29`.

The next real gate is the three-pilot visual/print approval for HMDA_02 / HMDA_13 / HMDA_29, followed by mechanical scale-out to all 15.

## Launch order

1. ✅ Assemble and audit one canonical renderer-ready English master with Cases 01-30.
2. ✅ Preserve reusable page families, Hint Vault and Solutions in the canonical master.
3. ✅ Keep Shigai ingestion external/path-independent and hash-verified at the production boundary.
4. Generate final-system pilots HMDA_02 / HMDA_13 / HMDA_29.
5. OWNER GATE: approve one map visual system at real KDP print size.
6. Scale that locked system mechanically to all 15 selected modules.
7. Validate geometry, unique answer, ROOM/ZONE meta carrier and rewritten-clue semantic equivalence.
8. Run strict English release CI/KDP preflight with all final map assets present.
9. Freeze English.
10. Generate Polish edition using the Polish Localization Engine.
11. Human proof / owner KDP publication gate.

## Book 2 rule

Do not fork a one-off Book 1 script.

Reusable architecture must remain:

`source puzzle -> normalized geometry -> RSE map skin -> content master -> reusable page renderer -> locale -> preflight -> PDF`

Book 2 should need new validated puzzles/content/assets, not a new production system.
