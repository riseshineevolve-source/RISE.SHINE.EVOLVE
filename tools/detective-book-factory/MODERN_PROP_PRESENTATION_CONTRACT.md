# Detective Academy — Modern Prop Presentation Contract

Status: **SOURCE INVENTORY LOCKED — ASSETS NOT YET IN PRODUCTION MAPS**  
Date: 2026-09-24  
Scope: presentation-only replacement of legacy Shigai furniture/object artwork.

## Current truth

The production map path is still `hybrid-original-shigai`. The hardened hybrid
renderer deliberately keeps the original source raster for walls, furniture,
object placement and character placement while replacing only approved
presentation surfaces such as room labels and page framing.

Therefore **modern props are not yet integrated into the production maps**.

The deterministic all-15 source inventory is now recovered and hash-bound, so
future visual work no longer needs to guess object types, cells, variants or
blocked/occupiable semantics.

## Authority

The hash-locked Shigai-derived runtime remains authoritative for every object.
The following fields are immutable puzzle semantics:

- case id,
- grid dimensions,
- object `cell`,
- source object `type`,
- source `variant`,
- `occupiable`,
- `blocked`.

A modern prop is only a visual skin over that immutable record.

## Non-negotiable invariants

A prop presentation change may never alter:

1. grid rows/columns or coordinate system;
2. room topology, room ownership, room boundaries or door geometry;
3. the object cell;
4. blocked/occupiable semantics;
5. witness/person identity or placement;
6. clue text, clue meaning, solution logic or answer;
7. Room Zero / meta-carrier logic;
8. source provenance or locked checkpoint/PDF hashes;
9. owner-supplied final visual assets.

If any of these drift, the modern-prop layer must fail closed.

## Source lock — completed 2026-09-24

The exact checkpoint selected by `content/spatial_source_manifest_final.yml` is:

- file: `HMDA_checkpoint_19_HMDA20_UPGRADE.shigai.json`;
- locked SHA-256: `cdc6de5b60117fe19e89fc4a13e2b9c1d92657f5e7fdb8ec69a18ae85ba8723e`.

Two Library entries with that filename were independently materialized through
the authorized text representation. Both materializations were byte-identical,
valid Shigai JSON, 581371 bytes long, and each independently hashed to the
locked SHA above. This closes the previous source-provenance ambiguity without
committing the private checkpoint to Git.

The production selection was then checked against the locked manifest:

- 15/15 selected cases resolved;
- each scene/clue page pair had identical source-board identity;
- every raw title and 6x6 / 7x7 / 9x9 grid matched the manifest;
- exact furniture / variant / occupiable semantics were extracted;
- object count: **260**;
- distinct exact source object types: **70**;
- immutable object semantic fingerprint:
  `54a03f3ee4ef474c74c1dd2cd44fb601ae7fd552c1ca6d46ccce03f4837471ca`.

The private checkpoint itself remains outside Git history.

## Catalog contract

`content/modern_prop_catalog.template.yml` remains the empty public schema
scaffold.

`content/modern_prop_catalog.source-locked.yml` is now the first deterministic
source-bound catalog stage. It contains all 70 exact source types, their locked
variant inventory, exact allowed `occupiable` values, conservative
`cell_center_safe` render boxes and stable presentation keys.

This source-locked catalog is **not artwork approval**. It selects no sprite,
style, silhouette or production visual. Its purpose is to remove guesswork from
the next presentation phase while keeping the visual choice reversible.

Every source object type used by a release runtime must resolve to exactly one
presentation mapping, optionally refined by a source variant override.

Each resolved mapping must declare:

- `presentation_key`: stable presentation asset/profile id;
- `allowed_occupiable`: the source occupiable state(s) this visual is allowed
  to represent;
- `render_box`: `cell_core` or `cell_center_safe`.

The catalog is not allowed to redefine cell, type, variant, blocked or
occupiable values.

## Deterministic inventory gate

The reproducible bridge remains:

```bash
python scripts/build_modern_prop_source_inventory.py \
  --checkpoint /private/path/HMDA_checkpoint_19_HMDA20_UPGRADE.shigai.json \
  --report /private/path/modern_prop_source_inventory.json
```

and runtime/catalog validation remains:

```bash
python scripts/validate_modern_prop_contract.py \
  --runtime /private/path/hmda_spatial_runtime.json \
  --catalog content/modern_prop_catalog.source-locked.yml \
  --report /private/path/modern_prop_catalog_validation.json
```

The source inventory emits exact counts, variants, occupiable/blocked values,
case/cell records and the immutable `object_semantics_sha256`. Any checkpoint or
runtime drift fails closed.

## Rendering boundary

The first implementation phase must not overwrite the production hybrid maps.
Modern prop renderer support is introduced behind an explicit opt-in path and
tested on representative 6x6, 7x7 and boss 9x9 cases before all-15 scale-out.

For source-raster replacement, an object-specific erase/replace footprint must
be proven safe before any source pixels are removed. It must not erase or cover:

- room walls/boundaries,
- coordinate lattice,
- room labels,
- door marks,
- person markers,
- unrelated source art.

The existing `validate_spatial_object_art.py` remains the source-preservation
baseline. It must not simply be weakened or disabled. A modern-prop integration
must first pass the existing semantic-parity, footprint-safety and structure
guards for the explicitly replaced object regions.

## Runtime binding and solution-person protection

`validate_modern_prop_footprint.py` must be run against the exact locked runtime
for any solution-map candidate. The guard verifies both:

- the plan-level `object_semantics_sha256` against the complete runtime object
  inventory; and
- the selected case's object records directly, so a moved/tampered approved box
  cannot pass merely by carrying an old fingerprint.

For `--surface solution`, every runtime `characters[].placement` cell is
protected as a whole cell. A modern prop may still be modernized in that same
cell on the puzzle map, but the solution-map composite may not change any pixel
inside the protected object box when a witness/person occupies the cell. This
is deliberately conservative: preserving the person marker has priority over
visual consistency between puzzle and solution maps.

`validate_modern_prop_structure.py` separately protects topology, walls/cell
boundaries, door data and source label footprints so an in-cell replacement
cannot silently damage map structure.

Representative synthetic 6x6 / 7x7 / 9x9 tests prove that:

- puzzle-surface changes inside approved prop boxes pass;
- the same change fails on a solution surface when the object cell is occupied
  by a person;
- an unoccupied object can still change on the solution surface;
- moved plan cells, runtime semantic drift, RGB leaks and alpha-only leaks fail
  closed;
- boundary, door, topology and attached-label damage fail closed.

## Verification order

1. Locked source object inventory — **PASS**.
2. Source-bound catalog coverage + blocked/occupiable compatibility — **PASS**.
3. Semantic fingerprint lock — **PASS**.
4. SHA-locked modern artwork asset pack — pending.
5. Opt-in renderer adapter on real maps — pending.
6. Representative 6x6 / 7x7 / 9x9 real-map preview — pending.
7. Independent visual/print QA — pending.
8. Mechanical all-15 scale-out only after the representative set passes.

## Current bounded implementation checkpoint

The modern-prop lane now contains:

- exact SHA-locked all-15 Shigai inventory: **15 cases / 260 objects / 70 types**;
- deterministic source semantic fingerprint;
- a source-locked 70-type presentation-key catalog with conservative safe boxes;
- runtime inventory/catalog validation;
- SHA-locked transparent PNG asset validation;
- isolated cell-confined overlay rendering;
- before/after RGBA footprint validation;
- direct locked-runtime plan binding;
- solution witness/person-cell protection;
- topology / wall / door / attached-label structure protection.

None of those mechanisms selects final prop artwork or changes a production map.
The previous all-15 runtime/source blocker is closed. The next safe work is the
**asset stage**: prepare candidate modern prop sprites against the exact 70-type
catalog, then run representative real 6x6 / 7x7 / boss 9x9 proofs through all
existing guards before any production substitution.

## Owner boundary

Source recovery, catalog locking and deterministic safety scaffolding are
AUTO/AUTO_VERIFY because they do not choose final artwork or change any map.
Final aesthetic selection of modern prop artwork and any owner-visible
production-map substitution remains owner-visible and must not be silently
promoted. No owner-supplied final images, locked clues, answers, geometry or
Room Zero logic may be altered by this lane.
