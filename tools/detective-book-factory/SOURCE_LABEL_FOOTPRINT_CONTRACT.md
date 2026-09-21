# HMDA Source Label Footprint Contract

Status: **CANONICAL / OWNER-APPROVED**
Date: 2026-09-21

## Purpose

The hybrid renderer must preserve locked source art and geometry while replacing source-facing room labels with final HMDA ROOM/ZONE names.

A missing image-detected label must never force a guessed pixel box.

This contract defines the safe fallback when a source room has no trustworthy standard label footprint.

## Source authority

Every label decision is bound to:
- the locked source PDF SHA-256,
- the locked case ID,
- the locked source room ID,
- the declared source puzzle page,
- the verified runtime topology.

A metadata entry is invalid if the source hash or case/page identity changes.

## Allowed source-label states

For each source room, exactly one state applies:

1. **detected**
   - a trustworthy source label footprint is found automatically;
   - topology-mask overlap identifies one source room unambiguously;
   - the source footprint is replaced in place.

2. **absent_verified**
   - human/source-page inspection verifies that no standard source room-name pill/footprint exists for that room;
   - the renderer must not erase or invent a source footprint;
   - the final HMDA label is placed using a deterministic topology-bound safe anchor.

3. **explicit_reference**
   - a source label exists but cannot be detected reliably;
   - a human-verified normalized footprint may be stored as metadata;
   - the reference must be normalized to the detected grid bbox, tied to source hash + case + source room ID + source page;
   - it is used only to replace the verified source label, never to change topology.

## Topology-bound safe anchor

For **absent_verified** rooms, placement is derived from verified room cells, not image guessing.

The renderer should:
1. construct the exact pixel mask from the locked runtime room topology;
2. identify candidate interior regions away from room boundaries;
3. exclude or heavily penalize areas occupied by locked furniture/object artwork;
4. prefer the largest clear interior region or safest central cell cluster;
5. fit the final label within the room mask with bounded padding;
6. never cover grid boundaries, clue-critical furniture, characters, or answer markers;
7. fail closed if no safe anchor exists.

The anchor must be deterministic for the same source hash/runtime.

## Required validation

After any fallback:
- room topology remains byte/logically unchanged;
- no source wall/furniture/object is erased;
- final label is fully inside the intended source room/zone;
- no two labels overlap;
- coordinates remain unchanged;
- solution and puzzle pages use the same source-bound placement logic;
- meta-carrier rooms are not visually emphasized;
- no answer leakage occurs;
- print readability passes.

## HMDA_04 decision

Owner-approved classification for the current locked source:
- source room 0: **absent_verified**
- source room 3: **absent_verified**

This classification is tied to the currently locked HMDA source PDF/checkpoint only.

The renderer may therefore use the topology-bound safe-anchor policy for those two rooms instead of requiring a nonexistent source pill footprint.

This is a presentation-layer repair only. It does not authorize any change to puzzle logic, source identity, source room partition, placement, clues, answer, or Room Zero meta behavior.
