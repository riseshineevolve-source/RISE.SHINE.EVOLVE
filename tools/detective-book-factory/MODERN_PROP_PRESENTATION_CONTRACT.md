# Detective Academy — Modern Prop Presentation Contract

Status: **ACTIVE SCAFFOLDING — NOT YET IN PRODUCTION MAPS**  
Date: 2026-09-24  
Scope: presentation-only replacement of legacy Shigai furniture/object artwork.

## Current truth

The production map path is still `hybrid-original-shigai`. The hardened hybrid
renderer deliberately keeps the original source raster for walls, furniture,
object placement and character placement while replacing only approved
presentation surfaces such as room labels and page framing.

Therefore **modern props are not yet integrated into the production maps**.

This contract defines the safe boundary for introducing them without changing
the puzzle.

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

## Catalog contract

`content/modern_prop_catalog.template.yml` is the public schema scaffold.
A release/private catalog is populated from a real generated runtime inventory.

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

Run:

```bash
python scripts/validate_modern_prop_contract.py \
  --runtime /private/path/hmda_spatial_runtime.json \
  --catalog content/modern_prop_catalog.template.yml \
  --inventory-only \
  --report /private/path/modern_prop_inventory.json
```

Inventory-only mode validates source object semantics and emits:

- exact object count by case/type,
- variants and occupiable/blocked values,
- exact case/cell references,
- unmapped types,
- `object_semantics_sha256`.

That fingerprint is the immutable semantic baseline for later presentation
passes.

Once the private catalog is populated, run without `--inventory-only`.
Unmapped or semantically incompatible objects then block the build.

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
must first add an equivalent semantic-parity and footprint-safety gate for the
explicitly replaced object regions.

## Verification order

1. Runtime object inventory — deterministic.
2. Catalog coverage + blocked/occupiable compatibility — deterministic.
3. Semantic fingerprint lock — deterministic.
4. Opt-in renderer adapter — no production substitution.
5. Representative 6x6 / 7x7 / 9x9 preview.
6. Independent visual/print QA.
7. Mechanical all-15 scale-out only after the representative set passes.

## Owner boundary

This scaffolding is AUTO/AUTO_VERIFY because it does not choose final artwork
or change any map. Final aesthetic selection of modern prop artwork and any
owner-visible production-map substitution remains outside this checkpoint until
the deterministic gates above are green.
