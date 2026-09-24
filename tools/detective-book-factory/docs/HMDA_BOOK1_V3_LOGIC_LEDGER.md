# HMDA Book 1 V3 — Case logic ledger

This ledger is generated from the declared publication input and the locked spatial runtime. It distinguishes exhaustive constraint proof from interpretive story/visual review. It does not certify rendered illustrations, page visibility, marker readability or physical print quality.

Logic status: **PASS**. Remaining machine/editorial gaps: none in the encoded constraints.

## Evidence and reproducibility

Run `python scripts/validate_book1_v3_logic.py --master dist/book1_en_master_owner_review_v3.yml --runtime dist/hmda_spatial_runtime_v3.json`. Use the actual final runtime path if different. The matching JSON report records solution counts, counterexamples, domains, constraints and input hashes.

```json
{
  "runtime": "hmda_spatial_runtime_v3.json",
  "runtime_sha256": "06bb284162ab62e993c8eee9237c58b67b6b545a425d2b04085725a81d50afc8",
  "selection_manifest_sha256": "fc5003696d9d5f6a33dc5ea5c1d11fe567076bdf4fc76b155a3f301cec22c8eb",
  "checkpoint_sha256": "cdc6de5b60117fe19e89fc4a13e2b9c1d92657f5e7fdb8ec69a18ae85ba8723e",
  "content": {
    "book1_en_master_owner_review_v3.yml": "bd0d8f464097f35073c85cedfb623de59483adf6436bd24e111e282fa2061bb5"
  }
}
```

The 15 spatial CSPs start with every usable floor/object square. Unary clues filter domains; binary clues, one-person-per-row/column, solo-room constraints, the bench companion and exactly one owner companion are enforced. AC-3 and finite backtracking exhaust the remaining assignments. Stored answer placements are consulted only after search. The source engine’s initial domains are not used to seed this solver.

Source-dependent rules: beside means an edge-sharing cell within the same space; diagonally next means one row and one column away; grid-step distance is Manhattan distance without routing around walls; cardinal offsets do not imply a shared row or column. Every witness belongs to one simultaneous snapshot. A not-beside-object clue also states that the room contains the object. These rules must be supplied to the child, not inferred from this internal ledger.

## Repairs and proof boundaries

- Case 01 baseline had two complete placements. Its delivery witness was uniquely Dani, but the claimed Cole=A3 step was unjustified. An explicit row3/columnA clue repairs the full placement.
- Case 05 baseline allowed BALL–STAR–BOLT–HEART and BALL–HEART–STAR–BOLT. The explicit HEART-after-BOLT clue removes the second code without changing the intended answer.
- Case 21 baseline A→C tear did not match (curve-1 versus wave-4), giving zero edge-valid chains. Both physical edges must match; the answer list is not evidence.
- Case 08 requires a departure before the closure ends; Case 11 must ask about the out-of-window timestamped record, not assert that an entire physical phone can never be evidence.
- Case 03 needs an explicit relevance rubric; Case 27 needs measurable landmark/target geometry; Case 28 needs an explicit categorization rubric. Their answer declarations alone are insufficient.
- Naming/room display changes preserve source identities. A companion witness is not automatically the person responsible for moving an object: the incident must state that the recorded handover was to/from that companion, or the objective must only ask who shared the space.

## Case coverage

|Case|Type|Logic check|Unique answer evidence|
|---|---|---|---|
|01|guided|PASS|Exhaustive 4! × 4! row/column assignments: 1 valid complete placement(s).|
|02|spatial|PASS|1 placement(s), exhaustive=True|
|03|visual|PASS|Printed relevance rule distinguishes parcel identity, evidence-tag identity and route. Three named changes fit those categories; background decoration/loose props do not.|
|04|spatial|PASS|1 placement(s), exhaustive=True|
|05|code|PASS|Exhaustive 4! symbol permutations: 1 valid code(s).|
|06|spatial|PASS|1 placement(s), exhaustive=True|
|07|spatial|PASS|1 placement(s), exhaustive=True|
|08|route|PASS|Hard closures eliminate A/B; remaining route(s) ['C']. Closure until 16:30 requires a stated current time before 16:30 and no waiting.|
|09|room-zero-checkpoint|PASS|4 matching plain-zero items; decorative ring/pointer patterns excluded. These establish recurrence, not cause.|
|10|spatial|PASS|1 placement(s), exhaustive=True|
|11|classification|PASS|Only timestamped record(s) ['D'] fall outside 15:20–16:05; untimestamped personal objects are not contradictory records.|
|12|spatial|PASS|1 placement(s), exhaustive=True|
|13|spatial|PASS|1 placement(s), exhaustive=True|
|14|consistency|PASS|Shortest path Stage → Hall → Dressing has two edges, 2 min each, so 4 min; claimed 16:10→16:12 allows only 2 min. Other statements admit placements.|
|15|spatial|PASS|1 placement(s), exhaustive=True|
|16|timeline-visual|PASS|Candidate years intersect the printed badge period 1999–2003 and installed security date≥2001: only 2002. Crest/plaque identifies the Training Annex. Envelope expiry is unnecessary and cannot alone date a photo.|
|17|spatial|PASS|1 placement(s), exhaustive=True|
|18|timeline|PASS|Subtract each clock offset from its displayed time; all four real timestamps differ, so their ascending order is unique.|
|19|spatial|PASS|1 placement(s), exhaustive=True|
|20|spatial|PASS|1 placement(s), exhaustive=True|
|21|reconstruction|PASS|Enumerated 24 scrap orders using physical edge labels alone: 1 complete chain(s); sentence read only afterward.|
|22|spatial|PASS|1 placement(s), exhaustive=True|
|23|spatial|PASS|1 placement(s), exhaustive=True|
|24|visual-sequence|PASS|Strictly decreasing transfer 100→70→35→10 gives one ordered trail from East Path to West Gate; tread decoration does not encode movement.|
|25|spatial|PASS|1 placement(s), exhaustive=True|
|26|room-zero-checkpoint|PASS|Count occupants in each ROOM using independently solved placements, exclude ZONES, take the sole empty-room initial in ascending case order.|
|27|map-overlay|PASS|Three named non-collinear landmarks fix the alignment. Enumerated all eight square-grid rotations/reflections with translation fixed by the first anchor; exactly one maps all anchors and the old target onto the current Archive wall.|
|28|fact-theory-sort|PASS|Three claims repeat earned observations (zero marks, empty-room message, sealed-space match). Unfinished-training explanation remains possible, not proven. Watcher/tunnel claims have no observed support.|
|29|boss-spatial|PASS|1 placement(s), exhaustive=True|
|30|multi-stage-finale|PASS|All four lock fields equal answers earned earlier: Rule Zero word, boss coordinate, unique four-symbol code, and the reader’s one opening ID. Reader name is intentionally variable, not a fixed spelling puzzle.|

## Case 01 — THE BADGE THAT ARRIVED BEFORE THE MAIL

- **Narrative setup:** The post has not arrived. The front door has not opened. Yet a Detective Academy badge is sitting on Mimi's kitchen table.
- **Objective:** Work out who was at the delivery desk when the badge appeared.
- **Puzzle type:** guided.
- **Happy Makers:** MIMI, LULI.
- **Unique intended answer:** DANI
- **Other participants:** ARI, BEA, COLE, DANI.
- **Rules:** Each of the four people uses a different row and column; room cells are explicitly listed.
- **Solvability evidence:** Exhaustive 4! × 4! row/column assignments: 1 valid complete placement(s).
- **Timing/rule assumption:** Only the explicit finite options and evidence printed with the case may be used; no outside history or hidden clue.
- **Naming aliases:** Named nonspatial participants are taken from this publication case’s evidence; no source-name substitution is used in the solver.
- **Visual assets:** 4×4 tutorial map and numeric witness key.
- **Enumerated solution count:** 1.
- **Baseline before repair:** 2 valid complete solutions.

### Evidence given to the reader

1. ARI was in row 1, column B.
2. COLE was in row 3, column A.
3. BEA was in column C, but not in row 2.
4. Each person used a different row and a different column.
5. The badge appeared at the Delivery desk.
6. ARCHIVE: A1, A2, B1, B2
7. LIBRARY: A3, A4, B3, B4
8. WORKSHOP: C1, C2, C3, C4
9. DELIVERY: D1, D2, D3, D4

### Deduction path

1. ARI goes to B1.
2. COLE goes to A3.
3. BEA must use C4 because C2 is ruled out.
4. DANI takes the only remaining row and column: D2.
5. D2 is inside Delivery, so DANI is the person we need.

- **Room Zero / meta signal:** {"code": "INTAKE-01", "label": "BADGE REVERSE", "reaction": "The printer issued the next file only after you signed the Academy ID.", "reader_move": "Add INTAKE-01 to your Case Wall.", "speaker": "mimi", "status": "FIRST VERIFIED 0"}
- **Later callback / required reuse:** First five-case recap; Cases 09/28 recurring-signal audit. Opening ID is reused in30.
- **Final QA status:** Logic **PASS** for the bound inputs. Rendered visual evidence, numeric marker clarity, clues-before-puzzle placement and page references require the separate V3 PDF audit.

## Case 02 — THE TROPHY THAT NEVER REACHED THE SHELF

- **Narrative setup:** A junior sports trophy was photographed before the team photo. Minutes later its shelf was empty. Nobody left the Academy wing, so the useful question is who was with Max when it moved.
- **Objective:** Rebuild the Academy positions and identify who was with Max when the trophy changed hands.
- **Puzzle type:** spatial.
- **Happy Makers:** LULI, ALIO.
- **Witness identities / naming aliases:** 01 Hope → Nova; 02 Drew → Dax; 03 Rory → Rook; 04 Edgar → Atlas; 05 Vesta → Ivy; 06 Bobby → Max.
- **Rules:** One person in each row and each column; only declared occupiable cells; all clue relations refer to this single snapshot. Exactly one other person shares the owner’s final space. Full placement must be recorded for later reuse.
- **Unique intended answer:** Dax at D2 (locked source identity Drew).
- **Complete independently solved placement:** 01 Nova — B3; 02 Dax — D2; 03 Rook — A6; 04 Atlas — F4; 05 Ivy — C5; 06 Max — E1.
- **Solvability evidence:** Exhaustive CSP found 1 complete assignment(s), canonical match=True, search nodes=1. No answer position was an input constraint.
- **Timing assumption:** All observations are simultaneous at the stated incident/record time; no witness moves between clues. The named companion only answers the physical-incident question when that incident’s handover/access link is explicit.
- **Visual asset (source_page_asset):** `dist/map_factory_owner_review_v3/HMDA_02_puzzle_original_shigai_relabelled.png`.
- **Visual asset (puzzle_asset):** `dist/map_factory_owner_review_v3/HMDA_02_puzzle_original_shigai_relabelled.png`.
- **Visual asset (solution_asset):** `dist/map_factory_owner_review_v3/HMDA_02_solution_original_shigai_relabelled.png`.

### Evidence given to the reader

1. Nova was in row 3 and column B.
2. Dax was in the Display Room and in column D.
3. Rook was in a corner and beside a teacher's desk.
4. Atlas was in the Equipment Room and in column F.
5. Ivy was standing on a desk.
6. Max was the trophy keeper. Exactly one other person shared his room.

### Deduction path

1. Nova is fixed at B3.
2. Dax is D2 in the Display Room.
3. Rook resolves to A6 and Atlas to F4.
4. Max is forced to E1; Ivy takes C5.
5. Dax is the only other person sharing Max's final room, so Dax is the answer.

- **Room Zero / meta signal:** {"code": "INTAKE-02", "label": "TROPHY TAG", "reaction": "Same mark, different file. Record the match; do not invent the reason.", "reader_move": "Record witness numbers beside final map positions. You may need them later.", "speaker": "luli", "status": "MATCH CONFIRMED"}
- **Later callback / required reuse:** Case 26 revisits this map; the empty ROOM initial joins CHECK THE OLD MAP. Cases 27–30 depend on that instruction.
- **Required hidden output:** Empty ROOM `Coach's Office` → `C`. Its existence follows from the solved occupancy; it is not assumed by the solver.
- **Final QA status:** Logic **PASS** for the bound inputs. Rendered visual evidence, numeric marker clarity, clues-before-puzzle placement and page references require the separate V3 PDF audit.

## Case 03 — LULI'S LOOK-TWICE FILE

- **Narrative setup:** Two evidence photos were taken less than a minute apart. Most differences are harmless. Three change what the team can conclude.
- **Objective:** Circle the three differences that matter to the case. Ignore decorative noise.
- **Puzzle type:** visual.
- **Happy Makers:** LULI, NINI.
- **Unique intended answer:** RIBBON KNOT + TAG NUMBER + SHOEPRINT DIRECTION
- **Other participants:** No additional named solver/witness beyond the listed team is required..
- **Rules:** Use the supplied evidence relevance rubric, not aesthetic preference; select exactly three changes.
- **Solvability evidence:** Printed relevance rule distinguishes parcel identity, evidence-tag identity and route. Three named changes fit those categories; background decoration/loose props do not.
- **Timing/rule assumption:** Only the explicit finite options and evidence printed with the case may be used; no outside history or hidden clue.
- **Naming aliases:** Named nonspatial participants are taken from this publication case’s evidence; no source-name substitution is used in the solver.
- **Visual assets:** paired evidence photographs with six controlled changes.

### Evidence given to the reader

1. relevance_rule: Choose changes to parcel identity, evidence-tag identity or travel direction. The poster, cup and pencil are not part of the evidence record.
2. meaningful: ["The ribbon knot changes from LEFT to RIGHT.", "Evidence tag 0417 becomes 0471.", "The muddy shoeprint points toward the door in Photo B."]
3. decoys: ["One poster has one extra star.", "A cup handle turns slightly.", "A pencil rolls a few centimetres."]

### Deduction path

1. The ribbon knot identifies which package was handled.
2. The tag number changes the identity of the evidence item.
3. The footprint direction changes the likely route.
4. Stars, cup handles and a rolling pencil do not alter the case.

- **Room Zero / meta signal:** {"code": "INTAKE-03", "label": "TAG 0471", "reaction": "The changed tag is the one the old intake system copied into its log.", "reader_move": "Write the three meaningful changes, then mark the stamp.", "speaker": "nini", "status": "ROUTING STAMP"}
- **Later callback / required reuse:** First five-case recap and Case 28 evidence-versus-assumption lesson.
- **Final QA status:** Logic **PASS** for the bound inputs. Rendered visual evidence, numeric marker clarity, clues-before-puzzle placement and page references require the separate V3 PDF audit.

## Case 04 — THE CUPCAKE BOX WITH SIX ALIBIS

- **Narrative setup:** Six identical boxes leave the fair kitchen. One carries the emergency test batch with salt sprinkles. The labels are mixed up before collection, and Pixel needs the chain reconstructed.
- **Objective:** Rebuild the fair positions and identify who was with Pixel when the wrong cupcake box was collected.
- **Puzzle type:** spatial.
- **Happy Makers:** MIMI, DILO.
- **Witness identities / naming aliases:** 01 Finlay → Echo; 02 Ivor → Kai; 03 Raquel → Zuri; 04 Amelie → Briar; 05 Clarissa → Clover; 06 Lisa → Pixel.
- **Rules:** One person in each row and each column; only declared occupiable cells; all clue relations refer to this single snapshot. Exactly one other person shares the owner’s final space. Full placement must be recorded for later reuse.
- **Unique intended answer:** Zuri at F4 (locked source identity Raquel).
- **Complete independently solved placement:** 01 Echo — A2; 02 Kai — B6; 03 Zuri — F4; 04 Briar — D3; 05 Clover — C5; 06 Pixel — E1.
- **Solvability evidence:** Exhaustive CSP found 1 complete assignment(s), canonical match=True, search nodes=1. No answer position was an input constraint.
- **Timing assumption:** All observations are simultaneous at the stated incident/record time; no witness moves between clues. The named companion only answers the physical-incident question when that incident’s handover/access link is explicit.
- **Visual asset (source_page_asset):** `dist/map_factory_owner_review_v3/HMDA_04_puzzle_original_shigai_relabelled.png`.
- **Visual asset (puzzle_asset):** `dist/map_factory_owner_review_v3/HMDA_04_puzzle_original_shigai_relabelled.png`.
- **Visual asset (solution_asset):** `dist/map_factory_owner_review_v3/HMDA_04_solution_original_shigai_relabelled.png`.

### Evidence given to the reader

1. Echo was in row 2 and column A.
2. Kai was the only person in the Kitchen.
3. Zuri was in the Pickup Tent and in row 4.
4. Briar was beside a ring-toss stand.
5. Clover was in the Packing Room and in row 5.
6. Pixel had the collection list. Exactly one other person shared her room.

### Deduction path

1. Echo is fixed at A2.
2. Zuri is F4 in the Pickup Tent.
3. Briar resolves to D3 beside the ring-toss stand.
4. Clover is C5; Kai is B6.
5. Pixel is E1 in the Pickup Tent.
6. Zuri is the only other person sharing Pixel's final room, so Zuri is the answer.

- **Room Zero / meta signal:** {"code": "INTAKE-04", "label": "QUALITY LABEL", "reaction": "The 0 is printed in the same place as the archive-routing field. That is useful weirdness.", "reader_move": "Record witness numbers beside final map positions.", "speaker": "dilo", "status": "ROUTED FILE"}
- **Later callback / required reuse:** Case 26 revisits this map; the empty ROOM initial joins CHECK THE OLD MAP. Cases 27–30 depend on that instruction.
- **Required hidden output:** Empty ROOM `Hospitality Room` → `H`. Its existence follows from the solved occupancy; it is not assumed by the solver.
- **Final QA status:** Logic **PASS** for the bound inputs. Rendered visual evidence, numeric marker clarity, clues-before-puzzle placement and page references require the separate V3 PDF audit.

## Case 05 — DILO'S CODE THAT DEFINITELY WASN'T 1234

- **Narrative setup:** Dilo has locked the evidence locker with a four-symbol code and described it as "legendary security". Luli has already ruled out legendary.
- **Objective:** Put the four symbols in the only order that satisfies every clue.
- **Puzzle type:** code.
- **Happy Makers:** DILO, LULI.
- **Unique intended answer:** ["BALL", "STAR", "BOLT", "HEART"]
- **Other participants:** No additional named solver/witness beyond the listed team is required..
- **Rules:** Use each of the four symbols once; satisfy every order constraint simultaneously.
- **Solvability evidence:** Exhaustive 4! symbol permutations: 1 valid code(s).
- **Timing/rule assumption:** Only the explicit finite options and evidence printed with the case may be used; no outside history or hidden clue.
- **Naming aliases:** Named nonspatial participants are taken from this publication case’s evidence; no source-name substitution is used in the solver.
- **Visual assets:** four symbol tiles and four writable lock positions.
- **Enumerated solution count:** 1.
- **Baseline before repair:** 2 valid complete solutions.

### Evidence given to the reader

1. symbols: ["BALL", "STAR", "BOLT", "HEART"]
2. clues: ["BOLT comes immediately after STAR.", "BALL appears before HEART.", "STAR is not first.", "HEART comes after BOLT."]

### Deduction path

1. STAR and BOLT must stay together in that order.
2. STAR cannot be first, so the pair must occupy positions 2 and 3.
3. BALL must be before HEART.
4. That forces BALL, STAR, BOLT, HEART.

- **Room Zero / meta signal:** {"code": "INTAKE-05", "label": "SEALED ENVELOPE", "reaction": "Five actual files. My tunnel chart has been postponed by evidence.", "reader_move": "Circle all five verified records on the Case Wall.", "speaker": "alio", "status": "FIVE REAL SIGNALS"}
- **Later callback / required reuse:** First five-case recap; exact four-symbol order required by Case 30 CODE stage.
- **Final QA status:** Logic **PASS** for the bound inputs. Rendered visual evidence, numeric marker clarity, clues-before-puzzle placement and page references require the separate V3 PDF audit.

## Case 06 — THE MUSEUM LABEL THAT LIED

- **Narrative setup:** A tiny Roman spoon has somehow become a CEREMONIAL DRAGON TOOTH. The object never moved. The labels did, sometime between two school-group tours.
- **Objective:** Rebuild the museum positions and identify who was with Uma when the labels were switched.
- **Puzzle type:** spatial.
- **Happy Makers:** LULI, NINI.
- **Witness identities / naming aliases:** 01 Stafford → Scout; 02 Hubert → Hugo; 03 Ava → Arlo; 04 Vera → Vale; 05 Wallace → Wren; 06 Eunice → Uma.
- **Rules:** One person in each row and each column; only declared occupiable cells; all clue relations refer to this single snapshot. Exactly one other person shares the owner’s final space. Full placement must be recorded for later reuse.
- **Unique intended answer:** Arlo at D2 (locked source identity Ava).
- **Complete independently solved placement:** 01 Scout — E3; 02 Hugo — A6; 03 Arlo — D2; 04 Vale — F5; 05 Wren — C4; 06 Uma — B1.
- **Solvability evidence:** Exhaustive CSP found 1 complete assignment(s), canonical match=True, search nodes=1. No answer position was an input constraint.
- **Timing assumption:** All observations are simultaneous at the stated incident/record time; no witness moves between clues. The named companion only answers the physical-incident question when that incident’s handover/access link is explicit.
- **Visual asset (source_page_asset):** `dist/map_factory_owner_review_v3/HMDA_06_puzzle_original_shigai_relabelled.png`.
- **Visual asset (puzzle_asset):** `dist/map_factory_owner_review_v3/HMDA_06_puzzle_original_shigai_relabelled.png`.
- **Visual asset (solution_asset):** `dist/map_factory_owner_review_v3/HMDA_06_solution_original_shigai_relabelled.png`.

### Evidence given to the reader

1. Scout was in row 3 and column E.
2. Hugo was in the Dinosaur Gallery, beside a display case.
3. Arlo was in the Foyer and in row 2.
4. Vale was in the Gallery, beside a statue.
5. Wren was on a bench, beside the skeleton display.
6. Uma checked the labels. Exactly one other person was with her.

### Deduction path

1. Scout is fixed at E3.
2. Arlo must be D2 in the Foyer.
3. Vale resolves to F5 in the Gallery.
4. Wren is C4 and Hugo is A6 in the Dinosaur Gallery.
5. Uma is B1 in the Foyer.
6. Arlo is the only other person with Uma, so Arlo is the answer.

- **Room Zero / meta signal:** {"code": "QUEUE-06", "label": "MUSEUM LABEL", "reaction": "This label came from a closed Academy file. The machine chose it; it did not cause it.", "reader_move": "Write every witness number in its final square. Keep the completed map.", "speaker": "bibi", "status": "OLD FILE REOPENED"}
- **Later callback / required reuse:** Case 26 revisits this map; the empty ROOM initial joins CHECK THE OLD MAP. Cases 27–30 depend on that instruction.
- **Required hidden output:** Empty ROOM `Egypt Room` → `E`. Its existence follows from the solved occupancy; it is not assumed by the solver.
- **Final QA status:** Logic **PASS** for the bound inputs. Rendered visual evidence, numeric marker clarity, clues-before-puzzle placement and page references require the separate V3 PDF audit.

## Case 07 — THE COSTUME THAT WALKED AWAY

- **Narrative setup:** The theatre's giant moon costume has vanished ten minutes before rehearsal. Alio volunteers to test whether it can walk by itself and disappears into the costume rack.
- **Objective:** Rebuild backstage and identify who was with Gray when the moon costume disappeared.
- **Puzzle type:** spatial.
- **Happy Makers:** ALIO, MIMI.
- **Witness identities / naming aliases:** 01 Bruce → Blaze; 02 Isla → Indigo; 03 Winifred → Willa; 04 Zelda → Zoe; 05 Roscoe → Rocket; 06 Grayson → Gray.
- **Rules:** One person in each row and each column; only declared occupiable cells; all clue relations refer to this single snapshot. Exactly one other person shares the owner’s final space. Full placement must be recorded for later reuse.
- **Unique intended answer:** Zoe at C6 (locked source identity Zelda).
- **Complete independently solved placement:** 01 Blaze — A3; 02 Indigo — D2; 03 Willa — B1; 04 Zoe — C6; 05 Rocket — E5; 06 Gray — F4.
- **Solvability evidence:** Exhaustive CSP found 1 complete assignment(s), canonical match=True, search nodes=5. No answer position was an input constraint.
- **Timing assumption:** All observations are simultaneous at the stated incident/record time; no witness moves between clues. The named companion only answers the physical-incident question when that incident’s handover/access link is explicit.
- **Visual asset (source_page_asset):** `dist/map_factory_owner_review_v3/HMDA_07_puzzle_original_shigai_relabelled.png`.
- **Visual asset (puzzle_asset):** `dist/map_factory_owner_review_v3/HMDA_07_puzzle_original_shigai_relabelled.png`.
- **Visual asset (solution_asset):** `dist/map_factory_owner_review_v3/HMDA_07_solution_original_shigai_relabelled.png`.

### Evidence given to the reader

1. Blaze was the only person in the Rehearsal Room.
2. Indigo was either in the Dressing Room or the Rehearsal Room.
3. Willa was 2 grid steps from the stage range marker. Count row difference plus column difference.
4. Zoe was against an outer wall and beside a costume cart.
5. Rocket was in row 5 and column E.
6. Gray's space contained exactly one other person.

### Deduction path

1. Rocket is fixed at E5.
2. Willa resolves to B1.
3. Blaze resolves to A3 in the Rehearsal Room.
4. Indigo is forced to D2 in the Dressing Room.
5. Zoe is C6 beside the costume cart; Gray is F4.
6. Zoe is the only other person in Gray's final space.

- **Room Zero / meta signal:** {"code": "QUEUE-07", "label": "COSTUME RECORD", "reaction": "New call, old routing mark. The cases are joining one investigation.", "reader_move": "Write every witness number in its final square. Keep the completed map.", "speaker": "mimi", "status": "PATTERN HOLDS"}
- **Later callback / required reuse:** Case 26 revisits this map; the empty ROOM initial joins CHECK THE OLD MAP. Cases 27–30 depend on that instruction.
- **Required hidden output:** Empty ROOM `Costume Room` → `C`. Its existence follows from the solved occupancy; it is not assumed by the solver.
- **Final QA status:** Logic **PASS** for the bound inputs. Rendered visual evidence, numeric marker clarity, clues-before-puzzle placement and page references require the separate V3 PDF audit.

## Case 08 — ALIO'S ABSOLUTELY SAFE SHORTCUT

- **Narrative setup:** Alio has drawn three routes to the prop room. Two are impressively fast. One has the additional advantage of not crossing wet paint, a locked staff door or a wall. It is 16:20, the team must arrive now, and waiting for a closure to end is not an option.
- **Objective:** Choose the only route that legally reaches the prop room.
- **Puzzle type:** route.
- **Happy Makers:** ALIO, MIMI.
- **Unique intended answer:** C
- **Other participants:** No additional named solver/witness beyond the listed team is required..
- **Rules:** Depart at16:20; no waiting; closed corridor, locked door and wall cannot be crossed.
- **Solvability evidence:** Hard closures eliminate A/B; remaining route(s) ['C']. Closure until 16:30 requires a stated current time before 16:30 and no waiting.
- **Timing/rule assumption:** Only the explicit finite options and evidence printed with the case may be used; no outside history or hidden clue.
- **Naming aliases:** Named nonspatial participants are taken from this publication case’s evidence; no source-name substitution is used in the solver.
- **Visual assets:** three route diagrams, barriers and departure clock.

### Evidence given to the reader

1. start: LOBBY
2. goal: PROP ROOM
3. options: [{"fails": "The Paint Corridor is closed until 16:30.", "id": "A", "path": ["LOBBY", "PAINT CORRIDOR", "SIDE HALL", "PROP ROOM"]}, {"fails": "The staff door is locked and the drawn shortcut cuts through a wall.", "id": "B", "path": ["LOBBY", "STAFF STAIRS", "PROP ROOM"]}, {"fails": null, "id": "C", "path": ["LOBBY", "COSTUME STORAGE", "SIDE HALL", "PROP ROOM"]}]

### Deduction path

1. Route A fails because the Paint Corridor is closed.
2. Route B fails because the staff door is locked and the line crosses a wall.
3. Route C uses Costume Storage and the Side Hall, both open.
4. Route C is the only valid shortcut.

- **Room Zero / meta signal:** {"code": "CHECK-08", "label": "CORRIDOR ZERO", "reaction": "A corridor label is not the same as the intake stamp. Similar shape, different job.", "reader_move": "Mark FALSE LEAD without erasing the useful route evidence.", "speaker": "luli", "status": "FALSE LEAD REJECTED"}
- **Later callback / required reuse:** Route-checking practice; no new answer token required later.
- **Final QA status:** Logic **PASS** for the bound inputs. Rendered visual evidence, numeric marker clarity, clues-before-puzzle placement and page references require the separate V3 PDF audit.

## Case 09 — THE SYMBOL THAT SHOULDN'T BE HERE

- **Narrative setup:** The same plain 0 has now appeared on objects from completely different cases. Grandma Bibi studies it for a long moment, then becomes suspiciously interested in the ceiling.
- **Objective:** Separate the recurring Academy mark from decorative lookalikes and decide whether the pattern is real.
- **Puzzle type:** room-zero-checkpoint.
- **Happy Makers:** GRANDMA BIBI, LULI, DILO.
- **Unique intended answer:** THE PLAIN 0 IS A RECURRING ACADEMY SIGNAL.
- **Other participants:** No additional named solver/witness beyond the listed team is required..
- **Rules:** Match the deliberate plain0 evidence mark; exclude decorative circles/pointers; do not infer its cause.
- **Solvability evidence:** 4 matching plain-zero items; decorative ring/pointer patterns excluded. These establish recurrence, not cause.
- **Timing/rule assumption:** Only the explicit finite options and evidence printed with the case may be used; no outside history or hidden clue.
- **Naming aliases:** Named nonspatial participants are taken from this publication case’s evidence; no source-name substitution is used in the solver.
- **Visual assets:** recurring-mark evidence cards and decorative lookalikes.

### Evidence given to the reader

1. evidence: [{"item": "opening Academy badge", "mark": "plain engraved 0", "recurring": true}, {"item": "trophy evidence record", "mark": "plain stamped 0", "recurring": true}, {"item": "cupcake quality sticker", "mark": "plain printed 0", "recurring": true}, {"item": "museum label reverse", "mark": "plain printed 0", "recurring": true}, {"item": "poster decoration", "mark": "striped circle", "recurring": false}, {"item": "stage-light dial", "mark": "ring with pointer", "recurring": false}]

### Deduction path

1. Remove the poster circle and stage dial; their shapes and functions differ.
2. The remaining marks use the same plain 0 form.
3. They occur on unrelated evidence across multiple cases.
4. The pattern is real, but its meaning remains unknown.

- **Room Zero / meta signal:** {"code": "ARCHIVE-09", "label": "BIBI MEMORY", "reaction": "I know the mark belonged to intake. I still do not remember what its zero meant.", "reader_move": "Write FACT: OLD ACADEMY INTAKE MARK.", "speaker": "bibi", "status": "ACADEMY LINK"}
- **Later callback / required reuse:** Case 28 distinguishes the established recurring mark from its unproven cause.
- **Final QA status:** Logic **PASS** for the bound inputs. Rendered visual evidence, numeric marker clarity, clues-before-puzzle placement and page references require the separate V3 PDF audit.

## Case 10 — THE ROBOT WITH TWO OWNERS

- **Narrative setup:** Two science-fair teams insist the silver rover belongs to them. Dilo is personally offended by its cable management. Luli would prefer he solve the access problem first.
- **Objective:** Reconstruct the science-fair floor and identify who had access to Dash's prototype area.
- **Puzzle type:** spatial.
- **Happy Makers:** DILO, LULI.
- **Witness identities / naming aliases:** 01 Eliza → Ember; 02 Nicholas → Nico; 03 Willie → Wyatt; 04 Frances → Finn; 05 Blythe → Beck; 06 Verity → Vera; 07 Dora → Dash.
- **Rules:** One person in each row and each column; only declared occupiable cells; all clue relations refer to this single snapshot. Exactly one other person shares the owner’s final space. Full placement must be recorded for later reuse.
- **Unique intended answer:** Ember at D5 (locked source identity Eliza).
- **Complete independently solved placement:** 01 Ember — D5; 02 Nico — F6; 03 Wyatt — B7; 04 Finn — A2; 05 Beck — C1; 06 Vera — G4; 07 Dash — E3.
- **Solvability evidence:** Exhaustive CSP found 1 complete assignment(s), canonical match=True, search nodes=9. No answer position was an input constraint.
- **Timing assumption:** All observations are simultaneous at the stated incident/record time; no witness moves between clues. The named companion only answers the physical-incident question when that incident’s handover/access link is explicit.
- **Visual asset (source_page_asset):** `dist/map_factory_owner_review_v3/HMDA_10_puzzle_original_shigai_relabelled.png`.
- **Visual asset (puzzle_asset):** `dist/map_factory_owner_review_v3/HMDA_10_puzzle_original_shigai_relabelled.png`.
- **Visual asset (solution_asset):** `dist/map_factory_owner_review_v3/HMDA_10_solution_original_shigai_relabelled.png`.

### Evidence given to the reader

1. Ember was on a demo seat and beside another demo seat.
2. Nico was in column F and on a demo seat.
3. Wyatt was in column B and beside a charging pod.
4. Finn was 7 grid steps from the coolant tank. Count row difference plus column difference.
5. Beck was against an outer wall and beside a parts crate.
6. Vera's room contained a control console, but she was not beside any control console in that room.
7. Dash's area contained exactly one other person.

### Deduction path

1. Wyatt is fixed at B7 in the Robotics Lab.
2. Ember resolves to D5; Beck to C1.
3. Nico is F6, Vera G4 and Finn A2.
4. Dash is E3 in the Assembly Hall.
5. Ember is the only other person in the Assembly Hall, so Ember is the answer.

- **Room Zero / meta signal:** {"code": "QUEUE-10", "label": "ROBOT DIAGNOSTIC", "reaction": "The queue copied a real diagnostic card. It did not edit the robot or the witnesses.", "reader_move": "Write every witness number in its final square. Keep the completed map.", "speaker": "dilo", "status": "FILE SELECTED"}
- **Later callback / required reuse:** Case 26 revisits this map; the empty ROOM initial joins CHECK THE OLD MAP. Cases 27–30 depend on that instruction.
- **Required hidden output:** Empty ROOM `Kinetics Lab` → `K`. Its existence follows from the solved occupancy; it is not assumed by the solver.
- **Final QA status:** Logic **PASS** for the bound inputs. Rendered visual evidence, numeric marker clarity, clues-before-puzzle placement and page references require the separate V3 PDF audit.

## Case 11 — MIMI'S EVIDENCE BAG PROBLEM

- **Narrative setup:** Mimi empties her evidence bag. It contains three science-fair case items, two pens, one snack and the phone she has been looking for since breakfast.
- **Objective:** Compare timestamped records A-D and identify the one created outside the 15:20-16:05 case window.
- **Puzzle type:** classification.
- **Happy Makers:** MIMI, NINI.
- **Unique intended answer:** D
- **Other participants:** No additional named solver/witness beyond the listed team is required..
- **Rules:** Evaluate timestamped records A–D against the inclusive15:20–16:05 window; untimed personal items are not competing records.
- **Solvability evidence:** Only timestamped record(s) ['D'] fall outside 15:20–16:05; untimestamped personal objects are not contradictory records.
- **Timing/rule assumption:** Only the explicit finite options and evidence printed with the case may be used; no outside history or hidden clue.
- **Naming aliases:** Named nonspatial participants are taken from this publication case’s evidence; no source-name substitution is used in the solver.
- **Visual assets:** bag contents and legible timestamp labels.

### Evidence given to the reader

1. case_window: 15:20-16:05 / SCIENCE FAIR HALL
2. items: [{"id": "A", "item": "prototype access card", "label": "SF-10 / 15:31", "relevant": true}, {"id": "B", "item": "loose cable tie", "label": "SF-10 / HALL B / 15:44", "relevant": true}, {"id": "C", "item": "silver wheel cap", "label": "SF-10 / 15:52", "relevant": true}, {"id": "D", "item": "Mimi's phone", "label": "personal / photo 08:07", "relevant": false}, {"id": "E", "item": "black pen", "label": "team notes", "relevant": false}, {"id": "F", "item": "blue pen", "label": "team notes", "relevant": false}, {"id": "G", "item": "oat bar", "label": "MIMI - DO NOT CATALOGUE", "relevant": false}]
3. question: Among timestamped records A-D, which record was created outside the 15:20-16:05 case window?

### Deduction path

1. The science-fair evidence window begins at 15:20.
2. Items A-C are labelled inside that window.
3. Pens and snack are ordinary bag contents but not contradictory evidence.
4. The phone photo record is from 08:07, so it was created outside the science-fair event window.
5. Record D is the only timestamped record outside 15:20-16:05.

- **Room Zero / meta signal:** {"code": "ARCHIVE-11", "label": "08:07 PHOTO", "reaction": "My lost phone found an older Academy seal. I am calling that efficient evidence storage.", "reader_move": "Log the photo time and keep the seal as a callback.", "speaker": "mimi", "status": "SEAL FOUND"}
- **Later callback / required reuse:** Old Academy context; photo observation must not be treated as proof of a watcher.
- **Final QA status:** Logic **PASS** for the bound inputs. Rendered visual evidence, numeric marker clarity, clues-before-puzzle placement and page references require the separate V3 PDF audit.

## Case 12 — THE PARROT WHO KNEW THE PASSWORD

- **Narrative setup:** A theatre parrot has learned a suspicious four-word phrase that nobody admits teaching it. Nini begins the gentlest interview in Academy history. Dilo brings crackers and a notebook.
- **Objective:** Reconstruct the rehearsal area and identify who was with Winter when the parrot learned the phrase.
- **Puzzle type:** spatial.
- **Happy Makers:** NINI, DILO.
- **Witness identities / naming aliases:** 01 Kendra → Kira; 02 Norris → Nell; 03 Irma → Iris; 04 Earlene → Eli; 05 Cleo → Cove; 06 Siobhan → Sage; 07 Winthrop → Winter.
- **Rules:** One person in each row and each column; only declared occupiable cells; all clue relations refer to this single snapshot. Exactly one other person shares the owner’s final space. Full placement must be recorded for later reuse.
- **Unique intended answer:** Nell at G2 (locked source identity Norris).
- **Complete independently solved placement:** 01 Kira — E6; 02 Nell — G2; 03 Iris — A5; 04 Eli — F4; 05 Cove — B7; 06 Sage — C3; 07 Winter — D1.
- **Solvability evidence:** Exhaustive CSP found 1 complete assignment(s), canonical match=True, search nodes=9. No answer position was an input constraint.
- **Timing assumption:** All observations are simultaneous at the stated incident/record time; no witness moves between clues. The named companion only answers the physical-incident question when that incident’s handover/access link is explicit.
- **Visual asset (source_page_asset):** `dist/map_factory_owner_review_v3/HMDA_12_puzzle_original_shigai_relabelled.png`.
- **Visual asset (puzzle_asset):** `dist/map_factory_owner_review_v3/HMDA_12_puzzle_original_shigai_relabelled.png`.
- **Visual asset (solution_asset):** `dist/map_factory_owner_review_v3/HMDA_12_solution_original_shigai_relabelled.png`.

### Evidence given to the reader

1. Kira was in the Bird Room, and nobody else entered it.
2. Nell was in the Stage Wing and in row 2.
3. Iris was the third person from the south.
4. Eli was either in the Green Room or the Bird Room.
5. Cove was in column B and against an outer wall.
6. Exactly one of Sage and Kira was in the Rehearsal Room.
7. Winter's area contained exactly one other person.

### Deduction path

1. Cove is B7.
2. Nell resolves to G2 in the Stage Wing; Iris to A5.
3. Kira is E6 in the Bird Room and Eli is F4 in the Green Room.
4. Sage resolves to C3 in the Rehearsal Room.
5. Winter is D1 in the Stage Wing.
6. Nell is the only other person with Winter, so Nell is the answer.

- **Room Zero / meta signal:** {"code": "QUEUE-12", "label": "PARROT CUE CARD", "reaction": "The parrot copied words. The machine copied a file. Neither one invented the event.", "reader_move": "Write every witness number in its final square. Keep the completed map.", "speaker": "nini", "status": "ROUTING TRACE"}
- **Later callback / required reuse:** Case 26 revisits this map; the empty ROOM initial joins CHECK THE OLD MAP. Cases 27–30 depend on that instruction.
- **Required hidden output:** Empty ROOM `Training Room` → `T`. Its existence follows from the solved occupancy; it is not assumed by the solver.
- **Final QA status:** Logic **PASS** for the bound inputs. Rendered visual evidence, numeric marker clarity, clues-before-puzzle placement and page references require the separate V3 PDF audit.

## Case 13 — THE CAMERA THAT BLINKED AT 4:17

- **Narrative setup:** A wildlife camera takes one blurry image at 4:17, then vanishes behind a stack of supplies. Alio blames the fox. Luli points out that the fox does not have pockets.
- **Objective:** Rebuild the animal-centre positions and identify who was with Remy when the camera moved.
- **Puzzle type:** spatial.
- **Happy Makers:** LULI, ALIO.
- **Witness identities / naming aliases:** 01 Jewel → Juno; 02 Shirley → Skye; 03 Elliot → Eden; 04 Wanda → Willow; 05 Bronwen → Bodhi; 06 Mercer → Moxie; 07 Rafferty → Remy.
- **Rules:** One person in each row and each column; only declared occupiable cells; all clue relations refer to this single snapshot. Exactly one other person shares the owner’s final space. Full placement must be recorded for later reuse.
- **Unique intended answer:** Bodhi at B7 (locked source identity Bronwen).
- **Complete independently solved placement:** 01 Juno — F3; 02 Skye — E4; 03 Eden — G2; 04 Willow — A1; 05 Bodhi — B7; 06 Moxie — C5; 07 Remy — D6.
- **Solvability evidence:** Exhaustive CSP found 1 complete assignment(s), canonical match=True, search nodes=16. No answer position was an input constraint.
- **Timing assumption:** All observations are simultaneous at the stated incident/record time; no witness moves between clues. The named companion only answers the physical-incident question when that incident’s handover/access link is explicit.
- **Visual asset (source_page_asset):** `dist/map_factory_owner_review_v3/HMDA_13_puzzle_original_shigai_relabelled.png`.
- **Visual asset (puzzle_asset):** `dist/map_factory_owner_review_v3/HMDA_13_puzzle_original_shigai_relabelled.png`.
- **Visual asset (solution_asset):** `dist/map_factory_owner_review_v3/HMDA_13_solution_original_shigai_relabelled.png`.

### Evidence given to the reader

1. Juno was diagonally next to Skye; their corners touched.
2. Skye stayed in the Ranger Station.
3. Eden shared a room with Juno.
4. Willow was north-west of Bodhi: north and west by any number of squares.
5. Bodhi was south-west of Moxie: south and west by any number of squares.
6. Moxie was in the Ranger Station and in row 5.
7. Remy's room contained exactly one other person.

### Deduction path

1. Moxie resolves to C5 and Skye to E4 in the Ranger Station.
2. Juno is F3 and Eden G2.
3. Bodhi resolves to B7 after applying the directional chain.
4. Willow is A1 and Remy is D6.
5. Bodhi is the only other person in Remy's Research Lab, so Bodhi is the answer.

- **Room Zero / meta signal:** {"code": "QUEUE-13", "label": "CAMERA CARD", "reaction": "You found the access point before the team did. From here on, this is our case.", "reader_move": "Write every witness number in its final square. Keep the completed map.", "speaker": "luli", "status": "CASE PARTNER"}
- **Later callback / required reuse:** Case 26 revisits this map; the empty ROOM initial joins CHECK THE OLD MAP. Cases 27–30 depend on that instruction.
- **Required hidden output:** Empty ROOM `Hide Room` → `H`. Its existence follows from the solved occupancy; it is not assumed by the solver.
- **Final QA status:** Logic **PASS** for the bound inputs. Rendered visual evidence, numeric marker clarity, clues-before-puzzle placement and page references require the separate V3 PDF audit.

## Case 14 — ONE WITNESS IS ACCIDENTALLY IMPOSSIBLE

- **Narrative setup:** Four young actors describe a backstage mix-up. Nobody is trying to trick you, but one memory cannot fit the little map and the clock at the same time.
- **Objective:** Find the statement that cannot be true without calling anyone a liar.
- **Puzzle type:** consistency.
- **Happy Makers:** NINI, LULI, DILO.
- **Unique intended answer:** NOAH
- **Other participants:** MAYA, LEO, SOFIA, NOAH.
- **Rules:** Only drawn connections are available; each edge takes at least2 min; compare travel time to claimed elapsed time.
- **Solvability evidence:** Shortest path Stage → Hall → Dressing has two edges, 2 min each, so 4 min; claimed 16:10→16:12 allows only 2 min. Other statements admit placements.
- **Timing/rule assumption:** Edges are all available routes and 2min is the minimum traversal time, including for the witness; no unstated shortcuts.
- **Naming aliases:** Named nonspatial participants are taken from this publication case’s evidence; no source-name substitution is used in the solver.
- **Visual assets:** complete node/edge route map and witness timing cards.

### Evidence given to the reader

1. map: {"edges": [["DRESSING", "HALL"], ["HALL", "STAGE"], ["HALL", "PROP"]], "walking_minutes_per_edge": 2}
2. timeline: [{"event": "rehearsal bell", "time": "16:10"}, {"event": "prop-room photo", "time": "16:14"}]
3. statements: [{"possible": true, "speaker": "MAYA", "text": "At 16:10 I was in Dressing. I stayed there."}, {"possible": true, "speaker": "LEO", "text": "At 16:12 I crossed the Hall toward Stage."}, {"possible": true, "speaker": "SOFIA", "text": "I was in Prop for the 16:14 photo."}, {"possible": false, "speaker": "NOAH", "text": "The 16:10 bell rang while I was on Stage, and I was already in Dressing at 16:12."}]

### Deduction path

1. Dressing and Stage are not directly connected; Hall sits between them.
2. Each edge takes 2 minutes.
3. Stage -> Hall -> Dressing therefore takes 4 minutes.
4. NOAH claims the same move happened between 16:10 and 16:12.
5. His memory is the impossible one. It can be mistaken without being dishonest.

- **Room Zero / meta signal:** {"code": "CHECK-14", "label": "ROOM 0 MEMORY", "reaction": "A witness remembered Room 0. Memory is evidence to test, not a shortcut to trust.", "reader_move": "Write MEMORY, not FACT, beside ROOM 0.", "speaker": "nini", "status": "WORDING UNRELIABLE"}
- **Later callback / required reuse:** Timing/memory lesson; no later lock consumes this witness name.
- **Final QA status:** Logic **PASS** for the bound inputs. Rendered visual evidence, numeric marker clarity, clues-before-puzzle placement and page references require the separate V3 PDF audit.

## Case 15 — THE BACKPACK THAT CHANGED OWNERS

- **Narrative setup:** Six black backpacks, one departure bus and zero readable name tags. One camper has picked up the wrong bag. Mimi calls it a system failure. Alio calls it camouflage training.
- **Objective:** Rebuild the camp positions and identify who ended up with Milo's backpack.
- **Puzzle type:** spatial.
- **Happy Makers:** MIMI, ALIO.
- **Witness identities / naming aliases:** 01 Hiram → Harper; 02 Primrose → Piper; 03 Damian → Duke; 04 Carolyn → Cruz; 05 Jonquil → Jett; 06 Isabella → Inez; 07 Mona → Milo.
- **Rules:** One person in each row and each column; only declared occupiable cells; all clue relations refer to this single snapshot. Exactly one other person shares the owner’s final space. Full placement must be recorded for later reuse.
- **Unique intended answer:** Harper at D2 (locked source identity Hiram).
- **Complete independently solved placement:** 01 Harper — D2; 02 Piper — F4; 03 Duke — E5; 04 Cruz — C3; 05 Jett — G7; 06 Inez — B6; 07 Milo — A1.
- **Solvability evidence:** Exhaustive CSP found 1 complete assignment(s), canonical match=True, search nodes=65. No answer position was an input constraint.
- **Timing assumption:** All observations are simultaneous at the stated incident/record time; no witness moves between clues. The named companion only answers the physical-incident question when that incident’s handover/access link is explicit.
- **Visual asset (source_page_asset):** `dist/map_factory_owner_review_v3/HMDA_15_puzzle_original_shigai_relabelled.png`.
- **Visual asset (puzzle_asset):** `dist/map_factory_owner_review_v3/HMDA_15_puzzle_original_shigai_relabelled.png`.
- **Visual asset (solution_asset):** `dist/map_factory_owner_review_v3/HMDA_15_solution_original_shigai_relabelled.png`.

### Evidence given to the reader

1. Harper was north-east of Cruz: north and east by any number of squares.
2. Piper was north-east of Duke.
3. Duke was in the First Aid Hut and in row 5.
4. Cruz was beside a camp cot.
5. Jett was the only person in the Welcome Lodge.
6. Inez shared a room with a cot but was not beside it.
7. Milo's room contained exactly one other person.

### Deduction path

1. Duke resolves to E5 in the First Aid Hut.
2. Piper is F4 and Cruz C3.
3. Jett is G7 in the Welcome Lodge.
4. Harper resolves to D2; Inez to B6.
5. Milo is A1 in the Games Cabin.
6. Harper is the only other person in Milo's Games Cabin, so Harper is the answer.

- **Room Zero / meta signal:** {"code": "QUEUE-15", "label": "LUGGAGE TAG", "reaction": "The replacement tag used the same retired intake template.", "reader_move": "Write every witness number in its final square. Keep the completed map.", "speaker": "mimi", "status": "OLD FORM"}
- **Later callback / required reuse:** Case 26 revisits this map; the empty ROOM initial joins CHECK THE OLD MAP. Cases 27–30 depend on that instruction.
- **Required hidden output:** Empty ROOM `Equipment Room` → `E`. Its existence follows from the solved occupancy; it is not assumed by the solver.
- **Final QA status:** Logic **PASS** for the bound inputs. Rendered visual evidence, numeric marker clarity, clues-before-puzzle placement and page references require the separate V3 PDF audit.

## Case 16 — GRANDMA BIBI'S VERY OLD, VERY EMBARRASSING PHOTOGRAPH

- **Narrative setup:** Bibi finally produces an old photograph of five children wearing Detective Academy badges. One is unmistakably her. The hat is enormous. The family behaves with admirable restraint for almost four seconds.
- **Objective:** Use only the evidence printed on the page to identify the building and the photo year.
- **Puzzle type:** timeline-visual.
- **Happy Makers:** GRANDMA BIBI, MIMI, ALIO.
- **Unique intended answer:** {"building": "OLD ACADEMY ANNEX", "year": 2002}
- **Other participants:** No additional named solver/witness beyond the listed team is required..
- **Rules:** Use the on-page official-event badge period and installed sticker date, not outside history.
- **Solvability evidence:** Candidate years intersect the printed badge period 1999–2003 and installed security date≥2001: only 2002. Crest/plaque identifies the Training Annex. Envelope expiry is unnecessary and cannot alone date a photo.
- **Timing/rule assumption:** Badge-period evidence describes the official event date, not merely a vintage badge worn later; sticker was already installed when photo taken.
- **Naming aliases:** Named nonspatial participants are taken from this publication case’s evidence; no source-name substitution is used in the solver.
- **Visual assets:** old group photo, plaque, badge-period sheet and dated sticker.

### Evidence given to the reader

1. candidate_buildings: ["OLD ACADEMY ANNEX", "CITY LIBRARY", "NORTH STATION"]
2. candidate_years: [1998, 2002, 2008]
3. evidence: ["A plaque behind the group shows the old Academy crest and the words TRAINING ANNEX.", "The archive rule says striped badges were issued and worn at official events only from 1999 through 2003.", "A maintenance sticker on the door says SECURITY UPGRADE COMPLETED 2001; the photo record says it was taken after that sticker was installed.", "The photo lab envelope is printed with EXPIRES 2004 and the processing log confirms it was used before expiry.", "The 2008 candidate is therefore too late, and 1998 is too early for the installed security sticker."]

### Deduction path

1. The visible crest and TRAINING ANNEX plaque identify the Old Academy Annex.
2. The striped badge can only be from 1999-2003.
3. The security sticker requires 2001 or later.
4. The processing log says the envelope was used before its 2004 expiry.
5. Of the three offered years, only 2002 satisfies every clue.
6. The back of the photograph adds the unexplained message: RULE 0 FIRST.

- **Room Zero / meta signal:** {"code": "ARCHIVE-16", "label": "RULE 0 FIRST", "reaction": "That is my handwriting. The rule came before the room, and I still owe you the missing word.", "reader_move": "Add RULE 0 FIRST beneath the dated photo.", "speaker": "bibi", "status": "PHOTO DATED"}
- **Later callback / required reuse:** Old Academy provenance and RULE0 FIRST seed Cases 27–28 and the final reveal.
- **Final QA status:** Logic **PASS** for the bound inputs. Rendered visual evidence, numeric marker clarity, clues-before-puzzle placement and page references require the separate V3 PDF audit.

## Case 17 — THE TRAIN TICKET THAT WASN'T LOST

- **Narrative setup:** At a heritage railway event, one special ticket appears to vanish. The real question is not where it went, but who was handed it before anyone noticed.
- **Objective:** Rebuild the railway positions and identify who was with Reed when the ticket changed hands.
- **Puzzle type:** spatial.
- **Happy Makers:** ALIO, LULI.
- **Witness identities / naming aliases:** 01 Octavia → Otis; 02 Margaret → Mika; 03 Kerry → Koa; 04 Samuel → Sunny; 05 Lincoln → Luna; 06 Ambrose → Axel; 07 Rhoda → Reed.
- **Rules:** One person in each row and each column; only declared occupiable cells; all clue relations refer to this single snapshot. Exactly one other person shares the owner’s final space. Full placement must be recorded for later reuse.
- **Unique intended answer:** Axel at E3 (locked source identity Ambrose).
- **Complete independently solved placement:** 01 Otis — A1; 02 Mika — B4; 03 Koa — F6; 04 Sunny — D5; 05 Luna — G7; 06 Axel — E3; 07 Reed — C2.
- **Solvability evidence:** Exhaustive CSP found 1 complete assignment(s), canonical match=True, search nodes=7. No answer position was an input constraint.
- **Timing assumption:** All observations are simultaneous at the stated incident/record time; no witness moves between clues. The named companion only answers the physical-incident question when that incident’s handover/access link is explicit.
- **Visual asset (source_page_asset):** `dist/map_factory_owner_review_v3/HMDA_17_puzzle_original_shigai_relabelled.png`.
- **Visual asset (puzzle_asset):** `dist/map_factory_owner_review_v3/HMDA_17_puzzle_original_shigai_relabelled.png`.
- **Visual asset (solution_asset):** `dist/map_factory_owner_review_v3/HMDA_17_solution_original_shigai_relabelled.png`.

### Evidence given to the reader

1. Otis was either in the Ticket Office or on the Baggage Platform.
2. Mika was in the Ticket Office and in column B.
3. Koa was in the Waiting Lounge and in row 6.
4. Sunny was on a bench.
5. Luna was in the Waiting Lounge and in column G.
6. Axel was exactly three rows north of Koa.
7. Reed's final area contained exactly one other person.

### Deduction path

1. Koa resolves to F6 and Luna to G7 in the Waiting Lounge.
2. Mika is B4 in the Ticket Office; Sunny resolves to D5.
3. Otis is A1.
4. Axel is E3, exactly three rows north of Koa.
5. Reed is C2 in the Main Corridor.
6. Axel is the only other person in Reed's final area.

- **Room Zero / meta signal:** {"code": "QUEUE-17", "label": "PUNCHED TICKET", "reaction": "The queue keeps returning to solved maps. I would like to know what it expects us to notice.", "reader_move": "Write every witness number in its final square. Keep the completed map.", "speaker": "dilo", "status": "BOOK REMEMBERS"}
- **Later callback / required reuse:** Case 26 revisits this map; the empty ROOM initial joins CHECK THE OLD MAP. Cases 27–30 depend on that instruction.
- **Required hidden output:** Empty ROOM `Observation Car` → `O`. Its existence follows from the solved occupancy; it is not assumed by the solver.
- **Final QA status:** Logic **PASS** for the bound inputs. Rendered visual evidence, numeric marker clarity, clues-before-puzzle placement and page references require the separate V3 PDF audit.

## Case 18 — THE SEVEN-MINUTE ALIBI

- **Narrative setup:** One cafe clock is seven minutes slow. Dilo's watch is two minutes fast. Four records look contradictory until every timestamp is converted to real time.
- **Objective:** Build the only real-time sequence that fits all four records.
- **Puzzle type:** timeline.
- **Happy Makers:** MIMI, DILO.
- **Unique intended answer:** ["A", "B", "C", "D"]
- **Other participants:** No additional named solver/witness beyond the listed team is required..
- **Rules:** Real time equals displayed time minus the stated clock offset; then sort.
- **Solvability evidence:** Subtract each clock offset from its displayed time; all four real timestamps differ, so their ascending order is unique.
- **Timing/rule assumption:** Same day, fixed clock offsets, no midnight rollover.
- **Naming aliases:** Named nonspatial participants are taken from this publication case’s evidence; no source-name substitution is used in the solver.
- **Visual assets:** four clock records with source labels.

### Evidence given to the reader

1. rules: ["CAFE CLOCK = real time minus 7 minutes.", "DILO'S WATCH = real time plus 2 minutes.", "STATION CAMERA = real time."]
2. records: [{"event": "ticket envelope placed on counter", "id": "A", "real": "15:15", "shown": "15:08", "source": "CAFE CLOCK"}, {"event": "team enters platform", "id": "B", "real": "15:16", "shown": "15:18", "source": "DILO'S WATCH"}, {"event": "ticket seen in hand", "id": "C", "real": "15:17", "shown": "15:17", "source": "STATION CAMERA"}, {"event": "empty envelope collected", "id": "D", "real": "15:18", "shown": "15:11", "source": "CAFE CLOCK"}]

### Deduction path

1. Cafe 15:08 becomes real 15:15.
2. Dilo 15:18 becomes real 15:16.
3. Station 15:17 is already real 15:17.
4. Cafe 15:11 becomes real 15:18.
5. The only order is A, B, C, D.

- **Room Zero / meta signal:** {"code": "CHECK-18", "label": "0:07", "reaction": "Seven minutes written as 0:07 is a time, not our mark. Context wins.", "reader_move": "Mark DECOY: TIME FORMAT.", "speaker": "luli", "status": "NUMERIC DECOY"}
- **Later callback / required reuse:** Deliberate false lead:0:07 is NOT a required meta token.
- **Final QA status:** Logic **PASS** for the bound inputs. Rendered visual evidence, numeric marker clarity, clues-before-puzzle placement and page references require the separate V3 PDF audit.

## Case 19 — THE LIBRARY BOOK THAT CHECKED ITSELF OUT

- **Narrative setup:** The library system says a rare book left the building. The book is still on the shelf.
- **Objective:** Rebuild the library positions and identify who was with Sasha when the wrong account was scanned.
- **Puzzle type:** spatial.
- **Happy Makers:** DILO, LULI.
- **Witness identities / naming aliases:** 01 Archibald → Avery; 02 Theodore → Theo; 03 Ottoline → Ollie; 04 Drew → Dex; 05 Madge → Mack; 06 Kimberly → Kian; 07 Sonia → Sasha.
- **Rules:** One person in each row and each column; only declared occupiable cells; all clue relations refer to this single snapshot. Exactly one other person shares the owner’s final space. Full placement must be recorded for later reuse.
- **Unique intended answer:** Mack at A7 (locked source identity Madge).
- **Complete independently solved placement:** 01 Avery — E5; 02 Theo — C1; 03 Ollie — D3; 04 Dex — G2; 05 Mack — A7; 06 Kian — F4; 07 Sasha — B6.
- **Solvability evidence:** Exhaustive CSP found 1 complete assignment(s), canonical match=True, search nodes=16. No answer position was an input constraint.
- **Timing assumption:** All observations are simultaneous at the stated incident/record time; no witness moves between clues. The named companion only answers the physical-incident question when that incident’s handover/access link is explicit.
- **Visual asset (source_page_asset):** `dist/map_factory_owner_review_v3/HMDA_19_puzzle_original_shigai_relabelled.png`.
- **Visual asset (puzzle_asset):** `dist/map_factory_owner_review_v3/HMDA_19_puzzle_original_shigai_relabelled.png`.
- **Visual asset (solution_asset):** `dist/map_factory_owner_review_v3/HMDA_19_solution_original_shigai_relabelled.png`.

### Evidence given to the reader

1. Avery was exactly two rows north of Mack.
2. Theo was 7 grid steps from the piano.
3. Exactly one of Ollie and Avery was in the Archive Room.
4. Dex shared a room with Theo.
5. Mack was south-west of Ollie.
6. Kian was in the Study Hall and in column F.
7. Sasha's final area contained exactly one other person.

### Deduction path

1. Kian resolves to F4.
2. Theo is C1 and Dex G2 in the Reference Room.
3. Avery resolves to E5 and Ollie to D3.
4. Mack is A7, south-west of Ollie.
5. Sasha is B6 in the Returns Hall.
6. Mack is the only other person in Sasha's final area.

- **Room Zero / meta signal:** {"code": "QUEUE-19", "label": "SCANNER BLANK", "reaction": "The mark sits where the record normally leaves nothing. Empty may be the useful part.", "reader_move": "Write every witness number in its final square. Keep the completed map.", "speaker": "nini", "status": "EMPTY FIELD"}
- **Later callback / required reuse:** Case 26 revisits this map; the empty ROOM initial joins CHECK THE OLD MAP. Cases 27–30 depend on that instruction.
- **Required hidden output:** Empty ROOM `Library Office` → `L`. Its existence follows from the solved occupancy; it is not assumed by the solver.
- **Final QA status:** Logic **PASS** for the bound inputs. Rendered visual evidence, numeric marker clarity, clues-before-puzzle placement and page references require the separate V3 PDF audit.

## Case 20 — THE PAINT-SPLATTERED ALIBI

- **Narrative setup:** A community art wall ends up in the wrong order. Nobody is in trouble. The challenge is reconstructing who was where before the paint dried.
- **Objective:** Rebuild the studio and identify who was with Demi when the panels were switched.
- **Puzzle type:** spatial.
- **Happy Makers:** MIMI, NINI.
- **Witness identities / naming aliases:** 01 Standish → Sid; 02 Pamela → Pax; 03 Leslie → Luca; 04 Millie → Mara; 05 Aurora → Asa; 06 Thatcher → Toby; 07 Danielle → Demi.
- **Rules:** One person in each row and each column; only declared occupiable cells; all clue relations refer to this single snapshot. Exactly one other person shares the owner’s final space. Full placement must be recorded for later reuse.
- **Unique intended answer:** Pax at F5 (locked source identity Pamela).
- **Complete independently solved placement:** 01 Sid — E7; 02 Pax — F5; 03 Luca — A1; 04 Mara — D4; 05 Asa — B2; 06 Toby — C6; 07 Demi — G3.
- **Solvability evidence:** Exhaustive CSP found 1 complete assignment(s), canonical match=True, search nodes=27. No answer position was an input constraint.
- **Timing assumption:** All observations are simultaneous at the stated incident/record time; no witness moves between clues. The named companion only answers the physical-incident question when that incident’s handover/access link is explicit.
- **Visual asset (source_page_asset):** `dist/map_factory_owner_review_v3/HMDA_20_puzzle_original_shigai_relabelled.png`.
- **Visual asset (puzzle_asset):** `dist/map_factory_owner_review_v3/HMDA_20_puzzle_original_shigai_relabelled.png`.
- **Visual asset (solution_asset):** `dist/map_factory_owner_review_v3/HMDA_20_solution_original_shigai_relabelled.png`.

### Evidence given to the reader

1. Sid was somewhere south of Pax.
2. Pax was south-east of Mara.
3. Luca was diagonally next to Asa.
4. Mara was in the Main Studio and in row 4.
5. Asa shared a room with Mara.
6. Toby was the only person in the Workshop Hall.
7. Demi's final room contained exactly one other person.

### Deduction path

1. Mara resolves to D4 and Asa to B2 in the Main Studio.
2. Luca becomes A1.
3. Toby resolves to C6 in the Workshop Hall.
4. Pax is F5 and Sid E7.
5. Demi is G3 in the Safety Station.
6. Pax is the only other person in Demi's final room.

- **Room Zero / meta signal:** {"code": "QUEUE-20", "label": "DRYING CARD", "reaction": "Different building. Different people. The queue still wants the completed map preserved.", "reader_move": "Write every witness number in its final square. Keep the completed map.", "speaker": "mimi", "status": "REPEATED TRACE"}
- **Later callback / required reuse:** Case 26 revisits this map; the empty ROOM initial joins CHECK THE OLD MAP. Cases 27–30 depend on that instruction.
- **Required hidden output:** Empty ROOM `Drying Room` → `D`. Its existence follows from the solved occupancy; it is not assumed by the solver.
- **Final QA status:** Logic **PASS** for the bound inputs. Rendered visual evidence, numeric marker clarity, clues-before-puzzle placement and page references require the separate V3 PDF audit.

## Case 21 — THE NOTE IN FOUR PIECES

- **Narrative setup:** Four torn scraps belong to one message. Rebuild it using edges, handwriting and sentence logic.
- **Objective:** Put the scraps in order and read the hidden instruction.
- **Puzzle type:** reconstruction.
- **Happy Makers:** DILO, NINI.
- **Unique intended answer:** ["THE ANSWER IS IN WHAT YOU LEAVE EMPTY."]
- **Other participants:** No additional named solver/witness beyond the listed team is required..
- **Rules:** Use every scrap exactly once, with the printed text upright; match physical edge types from straight left to straight right.
- **Solvability evidence:** Enumerated 24 scrap orders using physical edge labels alone: 1 complete chain(s); sentence read only afterward.
- **Timing/rule assumption:** Only the explicit finite options and evidence printed with the case may be used; no outside history or hidden clue.
- **Naming aliases:** Named nonspatial participants are taken from this publication case’s evidence; no source-name substitution is used in the solver.
- **Visual assets:** four torn scraps with matching physical edge profiles.
- **Enumerated solution count:** 1.
- **Baseline before repair:** 0 valid complete solutions.

### Evidence given to the reader

1. scraps: [{"id": "A", "left_edge": "zigzag-2", "right_edge": "curve-1", "text": "WHAT YOU"}, {"id": "B", "left_edge": "straight", "right_edge": "notch-3", "text": "THE ANSWER IS"}, {"id": "C", "left_edge": "curve-1", "right_edge": "straight", "text": "LEAVE EMPTY."}, {"id": "D", "left_edge": "notch-3", "right_edge": "zigzag-2", "text": "IN"}]
2. joins: [["B", "D"], ["D", "A"], ["A", "C"]]

### Deduction path

1. B must begin because it has the straight left edge.
2. B's right notch joins D.
3. D joins A, then A joins C.
4. The completed note reads: THE ANSWER IS IN WHAT YOU LEAVE EMPTY.

- **Room Zero / meta signal:** {"code": "MESSAGE-21", "label": "TORN NOTE", "reaction": "THE ANSWER IS IN WHAT YOU LEAVE EMPTY. The machine finally sent a sentence.", "reader_move": "Copy the exact sentence to the Case Wall.", "speaker": "dilo", "status": "INSTRUCTION RECOVERED"}
- **Later callback / required reuse:** The empty-space instruction is required to motivate Case 26.
- **Final QA status:** Logic **PASS** for the bound inputs. Rendered visual evidence, numeric marker clarity, clues-before-puzzle placement and page references require the separate V3 PDF audit.

## Case 22 — THE MUSIC ROOM MIX-UP

- **Narrative setup:** Three identical black instrument cases have migrated across the music school.
- **Objective:** Rebuild the school positions and identify who was with Zara when the wrong case changed hands.
- **Puzzle type:** spatial.
- **Happy Makers:** LULI, ALIO.
- **Witness identities / naming aliases:** 01 Leigh → Lex; 02 Irene → Imani; 03 Clarence → Cody; 04 Natasha → Nia; 05 Gemma → Gia; 06 William → Wes; 07 Zelda → Zara.
- **Rules:** One person in each row and each column; only declared occupiable cells; all clue relations refer to this single snapshot. Exactly one other person shares the owner’s final space. Full placement must be recorded for later reuse.
- **Unique intended answer:** Cody at C4 (locked source identity Clarence).
- **Complete independently solved placement:** 01 Lex — E6; 02 Imani — F7; 03 Cody — C4; 04 Nia — G5; 05 Gia — B1; 06 Wes — D3; 07 Zara — A2.
- **Solvability evidence:** Exhaustive CSP found 1 complete assignment(s), canonical match=True, search nodes=136. No answer position was an input constraint.
- **Timing assumption:** All observations are simultaneous at the stated incident/record time; no witness moves between clues. The named companion only answers the physical-incident question when that incident’s handover/access link is explicit.
- **Visual asset (source_page_asset):** `dist/map_factory_owner_review_v3/HMDA_22_puzzle_original_shigai_relabelled.png`.
- **Visual asset (puzzle_asset):** `dist/map_factory_owner_review_v3/HMDA_22_puzzle_original_shigai_relabelled.png`.
- **Visual asset (solution_asset):** `dist/map_factory_owner_review_v3/HMDA_22_solution_original_shigai_relabelled.png`.

### Evidence given to the reader

1. Lex was diagonally next to Imani.
2. Imani and Nia shared a room.
3. Cody was diagonally next to Wes.
4. Exactly one of Nia and Lex was in the Practice Hall.
5. Gia was 7 grid steps from the piano.
6. Wes's room contained an instrument locker, but he was not beside any instrument locker in that room.
7. Zara's final room contained exactly one other person.

### Deduction path

1. Wes resolves to D3 in the Instrument Locker Room.
2. Cody resolves diagonally to C4 in the Rehearsal Room.
3. Gia is B1; Lex E6; Imani F7.
4. Nia is G5 in the Practice Hall.
5. Zara is A2 in the Rehearsal Room.
6. Cody is the only other person in Zara's final room.

- **Room Zero / meta signal:** {"code": "QUEUE-22", "label": "INVENTORY CARD", "reaction": "Keep the completed map. A later case will ask you to inspect what your placements leave behind.", "reader_move": "Write every witness number in its final square. Do not guess why yet.", "speaker": "luli", "status": "RETROACTIVE EVIDENCE"}
- **Later callback / required reuse:** Case 26 revisits this map; the empty ROOM initial joins CHECK THE OLD MAP. Cases 27–30 depend on that instruction.
- **Required hidden output:** Empty ROOM `Music Archive` → `M`. Its existence follows from the solved occupancy; it is not assumed by the solver.
- **Final QA status:** Logic **PASS** for the bound inputs. Rendered visual evidence, numeric marker clarity, clues-before-puzzle placement and page references require the separate V3 PDF audit.

## Case 23 — THE WRISTBAND SWITCH AT ADVENTURE PARK

- **Narrative setup:** One wristband opens the climbing course. Another opens the arcade-credit locker.
- **Objective:** Rebuild the park positions and identify who was with Jude when the wristbands were switched.
- **Puzzle type:** spatial.
- **Happy Makers:** MIMI, DILO.
- **Witness identities / naming aliases:** 01 Vesta → Vivi; 02 Charlene → Cora; 03 Owen → Ozzy; 04 Rebecca → Rae; 05 Madge → Mae; 06 Peyton → Pia; 07 Judy → Jude.
- **Rules:** One person in each row and each column; only declared occupiable cells; all clue relations refer to this single snapshot. Exactly one other person shares the owner’s final space. Full placement must be recorded for later reuse.
- **Unique intended answer:** Rae at F6 (locked source identity Rebecca).
- **Complete independently solved placement:** 01 Vivi — G7; 02 Cora — D1; 03 Ozzy — A3; 04 Rae — F6; 05 Mae — C5; 06 Pia — B2; 07 Jude — E4.
- **Solvability evidence:** Exhaustive CSP found 1 complete assignment(s), canonical match=True, search nodes=22. No answer position was an input constraint.
- **Timing assumption:** All observations are simultaneous at the stated incident/record time; no witness moves between clues. The named companion only answers the physical-incident question when that incident’s handover/access link is explicit.
- **Visual asset (source_page_asset):** `dist/map_factory_owner_review_v3/HMDA_23_puzzle_original_shigai_relabelled.png`.
- **Visual asset (puzzle_asset):** `dist/map_factory_owner_review_v3/HMDA_23_puzzle_original_shigai_relabelled.png`.
- **Visual asset (solution_asset):** `dist/map_factory_owner_review_v3/HMDA_23_solution_original_shigai_relabelled.png`.

### Evidence given to the reader

1. Vivi was 7 grid steps from the gondola.
2. Cora was north-east of Mae.
3. Ozzy was south-west of Cora.
4. Rae was exactly two columns east of Cora.
5. Mae shared a room with either Ozzy or Pia, who was on a bench.
6. Exactly one of Pia and Vivi was in the Snack Stand.
7. Jude's final room contained exactly one other person.

### Deduction path

1. Vivi resolves to G7 and Pia to B2.
2. Mae resolves to C5 and Cora to D1.
3. Ozzy becomes A3.
4. Jude is E4 in the Prize Tent.
5. Rae is F6, exactly two columns east of Cora.
6. Rae is the only other person in Jude's final room.

- **Room Zero / meta signal:** {"code": "QUEUE-23", "label": "WRISTBAND SERIAL", "reaction": "A completed map can be evidence twice. I have officially stopped doodling on it.", "reader_move": "Write every witness number in its final square. Do not guess why yet.", "speaker": "alio", "status": "RETROACTIVE EVIDENCE"}
- **Later callback / required reuse:** Case 26 revisits this map; the empty ROOM initial joins CHECK THE OLD MAP. Cases 27–30 depend on that instruction.
- **Required hidden output:** Empty ROOM `Access Office` → `A`. Its existence follows from the solved occupancy; it is not assumed by the solver.
- **Final QA status:** Logic **PASS** for the bound inputs. Rendered visual evidence, numeric marker clarity, clues-before-puzzle placement and page references require the separate V3 PDF audit.

## Case 24 — THE FOOTPRINTS THAT WALKED BACKWARDS

- **Narrative setup:** The tread arrows point one way. The fresh mud transfer from one uninterrupted controlled-track walk tells a different story; no fresh mud was added between prints.
- **Objective:** Use the changing amount of wet mud to work out the real direction of travel.
- **Puzzle type:** visual-sequence.
- **Happy Makers:** ALIO, LULI.
- **Unique intended answer:** EAST PATH -> WEST GATE
- **Other participants:** No additional named solver/witness beyond the listed team is required..
- **Rules:** One uninterrupted controlled-track walk; no new mud; deposited mud decreases after leaving the muddy patch.
- **Solvability evidence:** Strictly decreasing transfer 100→70→35→10 gives one ordered trail from East Path to West Gate; tread decoration does not encode movement.
- **Timing/rule assumption:** One uninterrupted walk; same wet-mud source, no fresh mud added, comparable ground and print pressure.
- **Naming aliases:** Named nonspatial participants are taken from this publication case’s evidence; no source-name substitution is used in the solver.
- **Visual assets:** four visible prints with strictly decreasing mud intensity.

### Evidence given to the reader

1. positions: ["WEST GATE", "P2", "P3", "EAST PATH"]
2. prints: [{"mud": 100, "position": "EAST PATH", "tread_arrow": "EAST"}, {"mud": 70, "position": "P3", "tread_arrow": "EAST"}, {"mud": 35, "position": "P2", "tread_arrow": "EAST"}, {"mud": 10, "position": "WEST GATE", "tread_arrow": "EAST"}]
3. rule: During one uninterrupted walk with no new mud added, wet mud transfers most strongly on the first print after leaving the patch, then fades.

### Deduction path

1. The first print after wet mud must carry the most mud.
2. Mud decreases 100 -> 70 -> 35 -> 10.
3. That sequence runs from the East Path toward the West Gate.
4. The tread arrow is a pattern on the sole, not proof of walking direction.

- **Room Zero / meta signal:** {"code": "CHECK-24", "label": "SOLE CUT", "reaction": "The circular cut matches the shape, but it is not an intake record. Keep the route; reject the claim.", "reader_move": "Mark MOTIF, NOT SIGNAL.", "speaker": "nini", "status": "MOTIF ONLY"}
- **Later callback / required reuse:** Observation practice; the tread motif adds context but no extra meta letter.
- **Final QA status:** Logic **PASS** for the bound inputs. Rendered visual evidence, numeric marker clarity, clues-before-puzzle placement and page references require the separate V3 PDF audit.

## Case 25 — THE PACKAGE WITH NO NAME

- **Narrative setup:** A harmless parcel has been passed around so many times that nobody remembers its destination.
- **Objective:** Rebuild the guest-house positions and identify who accepted the parcel from Nori.
- **Puzzle type:** spatial.
- **Happy Makers:** NINI, MIMI.
- **Witness identities / naming aliases:** 01 Giselle → Gabe; 02 Celia → Casey; 03 Regan → Rio; 04 Theodore → Tate; 05 Silas → Sol; 06 Warren → Wynn; 07 Noreen → Nori.
- **Rules:** One person in each row and each column; only declared occupiable cells; all clue relations refer to this single snapshot. Exactly one other person shares the owner’s final space. Full placement must be recorded for later reuse.
- **Unique intended answer:** Casey at D5 (locked source identity Celia).
- **Complete independently solved placement:** 01 Gabe — F3; 02 Casey — D5; 03 Rio — E2; 04 Tate — C6; 05 Sol — G1; 06 Wynn — B7; 07 Nori — A4.
- **Solvability evidence:** Exhaustive CSP found 1 complete assignment(s), canonical match=True, search nodes=14. No answer position was an input constraint.
- **Timing assumption:** All observations are simultaneous at the stated incident/record time; no witness moves between clues. The named companion only answers the physical-incident question when that incident’s handover/access link is explicit.
- **Visual asset (source_page_asset):** `dist/map_factory_owner_review_v3/HMDA_25_puzzle_original_shigai_relabelled.png`.
- **Visual asset (puzzle_asset):** `dist/map_factory_owner_review_v3/HMDA_25_puzzle_original_shigai_relabelled.png`.
- **Visual asset (solution_asset):** `dist/map_factory_owner_review_v3/HMDA_25_solution_original_shigai_relabelled.png`.

### Evidence given to the reader

1. Gabe was diagonally next to Rio.
2. Casey was in the Lobby and in column D.
3. Rio was north-west of Gabe.
4. Tate was diagonally next to Wynn.
5. Sol was north-east of Gabe.
6. Wynn was in the Laundry and on a bar stool.
7. Nori's final room contained exactly one other person.

### Deduction path

1. Casey resolves to D5 in the Lobby.
2. Wynn is B7 and Tate C6 in the Laundry.
3. Gabe resolves to F3 and Rio E2.
4. Sol becomes G1.
5. Nori is A4 in the Lobby.
6. Casey is the only other person in Nori's final room.

- **Room Zero / meta signal:** {"code": "QUEUE-25", "label": "PARCEL ROUTING", "reaction": "Fourteen completed maps are ready. Time to inspect what the placements leave behind.", "reader_move": "Write every witness number in its final square, then turn to Case 26.", "speaker": "mimi", "status": "FOURTEEN MAPS READY"}
- **Later callback / required reuse:** Case 26 revisits this map; the empty ROOM initial joins CHECK THE OLD MAP. Cases 27–30 depend on that instruction.
- **Required hidden output:** Empty ROOM `Parcel Room` → `P`. Its existence follows from the solved occupancy; it is not assumed by the solver.
- **Final QA status:** Logic **PASS** for the bound inputs. Rendered visual evidence, numeric marker clarity, clues-before-puzzle placement and page references require the separate V3 PDF audit.

## Case 26 — THE CASE OF THE MISSING PEOPLE

- **Narrative setup:** Nini looks at an old solved map and asks one tiny question: Why is one named room always empty?
- **Objective:** Revisit the fourteen marked spatial cases and record the first letter of each unique empty ROOM.
- **Puzzle type:** room-zero-checkpoint.
- **Happy Makers:** LULI, DILO, NINI.
- **Unique intended answer:** CHECKTHEOLDMAP
- **Other participants:** No additional named solver/witness beyond the listed team is required..
- **Rules:** Use the fourteen listed earlier cases in order; find the sole empty ROOM, excluding all ZONES; take its initial.
- **Solvability evidence:** Count occupants in each ROOM using independently solved placements, exclude ZONES, take the sole empty-room initial in ascending case order.
- **Timing/rule assumption:** Reader was told to preserve each full placement; final ROOM/ZONE labels match the locked runtime.
- **Naming aliases:** Named nonspatial participants are taken from this publication case’s evidence; no source-name substitution is used in the solver.
- **Visual assets:** fourteen prior completed maps plus the case index.

### Evidence given to the reader

1. case_numbers: [2, 4, 6, 7, 10, 12, 13, 15, 17, 19, 20, 22, 23, 25]
2. instruction: On each solved map, find the one named space classified as a ROOM that contains zero people. Ignore corridors, platforms, queues and other ZONES. Write the first letter of each empty ROOM.

### Deduction path

1. Each marked spatial case has exactly one empty final ROOM.
2. Record the first letter of that room in case order.
3. The fourteen letters are C H E C K T H E O L D M A P.
4. The hidden instruction is CHECK THE OLD MAP.

- **Room Zero / meta signal:** {"code": "MESSAGE-26", "label": "EMPTY-ROOM INITIALS", "reaction": "The queue selected files whose verified empty rooms carry a stored initiation message.", "reader_move": "Write CHECK THE OLD MAP exactly as earned.", "speaker": "luli", "status": "CHECK THE OLD MAP"}
- **Later callback / required reuse:** CHECK THE OLD MAP is the explicit instruction driving Case 27.
- **Final QA status:** Logic **PASS** for the bound inputs. Rendered visual evidence, numeric marker clarity, clues-before-puzzle placement and page references require the separate V3 PDF audit.

## Case 27 — BIBI'S MAP HAS ONE ROOM WITH ZERO DOORS

- **Narrative setup:** The old Academy plan contains a rectangular space surrounded by walls with no door.
- **Objective:** Align the old and current plans using fixed landmarks and locate the sealed room.
- **Puzzle type:** map-overlay.
- **Happy Makers:** GRANDMA BIBI, ALIO.
- **Unique intended answer:** SEALED TRAINING ROOM BEHIND THE CURRENT ARCHIVE WALL
- **Other participants:** No additional named solver/witness beyond the listed team is required..
- **Rules:** Use fixed named landmarks and the stated common scale; page edges are not alignment evidence.
- **Solvability evidence:** Three named non-collinear landmarks fix the alignment. Enumerated all eight square-grid rotations/reflections with translation fixed by the first anchor; exactly one maps all anchors and the old target onto the current Archive wall.
- **Timing/rule assumption:** Only the explicit finite options and evidence printed with the case may be used; no outside history or hidden clue.
- **Naming aliases:** Named nonspatial participants are taken from this publication case’s evidence; no source-name substitution is used in the solver.
- **Visual assets:** old/current plan layers with matching landmarks and a sealed target footprint.
- **Enumerated solution count:** 1.

### Evidence given to the reader

1. grid: {"columns": 6, "rows": 5}
2. anchors: [{"current": "NORTH STAIR", "current_cell": "C1", "old": "NORTH STAIR", "old_cell": "C1"}, {"current": "COURTYARD COLUMN", "current_cell": "F3", "old": "COURTYARD COLUMN", "old_cell": "F3"}, {"current": "WEST LIFT SHAFT", "current_cell": "A5", "old": "WEST LIFT SHAFT", "old_cell": "A5"}]
3. old_room_cells: ["D2", "E2", "D3", "E3"]
4. current_archive_wall_cells: ["D2", "E2", "D3", "E3"]
5. transform: NO ROTATION; SAME SCALE; ALIGN C1, F3 AND A5
6. old_only_space: SEALED TRAINING ROOM
7. current_covering_space: ARCHIVE WALL / NO DOOR

### Deduction path

1. The North Stair fixes rotation.
2. The Courtyard Column fixes horizontal position.
3. The West Lift Shaft confirms scale.
4. The old sealed training room lands directly behind the current Archive wall.
5. The note says RULE FIRST, ROOM SECOND.

- **Room Zero / meta signal:** {"code": "ARCHIVE-27", "label": "SEALED TRAINING ROOM", "reaction": "The old plan and current wall agree. Room Zero was a training room, not a person watching us.", "reader_move": "Mark the sealed rectangle on both plans.", "speaker": "bibi", "status": "LOCATION VERIFIED"}
- **Later callback / required reuse:** The sealed-space observation becomes FACT in28; RULE FIRST, ROOM SECOND orders the finale.
- **Final QA status:** Logic **PASS** for the bound inputs. Rendered visual evidence, numeric marker clarity, clues-before-puzzle placement and page references require the separate V3 PDF audit.

## Case 28 — RULE ZERO

- **Narrative setup:** Before the final map, Bibi remembers what the Academy meant by zero.
- **Objective:** Sort the team's evidence into FACT, THEORY and UNSUPPORTED ASSUMPTION.
- **Puzzle type:** fact-theory-sort.
- **Happy Makers:** GRANDMA BIBI, MIMI, LULI, ALIO.
- **Unique intended answer:** ASSUMPTIONS
- **Other participants:** No additional named solver/witness beyond the listed team is required..
- **Rules:** Classify using the three explicitly supplied evidence-support definitions; no invented watcher/tunnel fact.
- **Solvability evidence:** Three claims repeat earned observations (zero marks, empty-room message, sealed-space match). Unfinished-training explanation remains possible, not proven. Watcher/tunnel claims have no observed support.
- **Timing/rule assumption:** Printed rubric distinguishes an evidence-linked tentative explanation from an unsupported assertion; Case27 observation must actually be earned.
- **Naming aliases:** Named nonspatial participants are taken from this publication case’s evidence; no source-name substitution is used in the solver.
- **Visual assets:** six statement cards and three defined category zones.

### Evidence given to the reader

1. definitions: {"FACT": "Directly observed or deduced from evidence.", "THEORY": "A tentative explanation linked to the facts but not yet proved.", "UNSUPPORTED ASSUMPTION": "An extra claim with no supporting evidence."}
2. cards: [{"bucket": "FACT", "text": "The same plain 0 appeared across unrelated cases."}, {"bucket": "FACT", "text": "Fourteen empty-room initials spell CHECK THE OLD MAP."}, {"bucket": "FACT", "text": "An old room sits behind the current Archive wall."}, {"bucket": "UNSUPPORTED ASSUMPTION", "text": "Someone has been secretly watching every case."}, {"bucket": "THEORY", "text": "The old Academy may have left an unfinished training system."}, {"bucket": "UNSUPPORTED ASSUMPTION", "text": "There must be a dramatic underground tunnel."}]
3. rule_zero: ZERO ASSUMPTIONS. NOTICE FIRST. THEORIZE SECOND.

### Deduction path

1. Sort direct observations into FACT.
2. Keep the unfinished-training-system idea as a THEORY.
3. Move the secret watcher and guaranteed tunnel into UNSUPPORTED ASSUMPTION.
4. The restored rule is ZERO ASSUMPTIONS. NOTICE FIRST. THEORIZE SECOND.

- **Room Zero / meta signal:** {"code": "RULE-28", "label": "ZERO ASSUMPTIONS", "reaction": "My tunnel theory has been moved to the unsupported shelf. I object accurately.", "reader_move": "Complete Rule Zero only now.", "speaker": "alio", "status": "RULE RESTORED"}
- **Later callback / required reuse:** ASSUMPTIONS is required by Case 30 RULE stage.
- **Final QA status:** Logic **PASS** for the bound inputs. Rendered visual evidence, numeric marker clarity, clues-before-puzzle placement and page references require the separate V3 PDF audit.

## Case 29 — THE MAP BENEATH THE MAP

- **Narrative setup:** The old Academy plan hides a service level. The largest spatial case in the book protects the final access coordinate.
- **Objective:** Solve the 9x9 service-level deduction and identify the coordinate of the only witness sharing Seth's room.
- **Puzzle type:** boss-spatial.
- **Happy Makers:** LULI, DILO, ALIO.
- **Witness identities / naming aliases:** 01 Michelle → Mavis; 02 Cassandra → Cato; 03 Jordana → Jules; 04 Betsy → Bryn; 05 Vera → Vega; 06 Ransom → Ren; 07 Payton → Poppy; 08 Wilhelmina → Wade; 09 Shepherd → Seth.
- **Rules:** One person in each row and each column; only declared occupiable cells; all clue relations refer to this single snapshot. Exactly one other person shares the owner’s final space. Full placement must be recorded for later reuse.
- **Unique intended answer:** Vega at D3 (locked source identity Vera).
- **Complete independently solved placement:** 01 Mavis — A2; 02 Cato — I4; 03 Jules — E8; 04 Bryn — G9; 05 Vega — D3; 06 Ren — H5; 07 Poppy — C6; 08 Wade — F7; 09 Seth — B1.
- **Solvability evidence:** Exhaustive CSP found 1 complete assignment(s), canonical match=True, search nodes=39. No answer position was an input constraint.
- **Timing assumption:** All observations are simultaneous at the stated incident/record time; no witness moves between clues. The named companion only answers the physical-incident question when that incident’s handover/access link is explicit.
- **Visual asset (source_page_asset):** `dist/map_factory_owner_review_v3/HMDA_29_puzzle_original_shigai_relabelled.png`.
- **Visual asset (puzzle_asset):** `dist/map_factory_owner_review_v3/HMDA_29_puzzle_original_shigai_relabelled.png`.
- **Visual asset (solution_asset):** `dist/map_factory_owner_review_v3/HMDA_29_solution_original_shigai_relabelled.png`.

### Evidence given to the reader

1. Mavis was north-west of Vega.
2. Cato was north-east of Ren.
3. Jules was diagonally next to Wade.
4. Bryn shared a space with Jules.
5. Vega was north-west of Cato.
6. Ren was in the Control Room.
7. Poppy shared a room with Mavis.
8. Wade was in the Operations Office, beside the teacher's desk.
9. Seth's final area contained exactly one other person.

### Deduction path

1. Wade resolves to F7.
2. Jules is E8 and Bryn G9.
3. Ren is H5 and Cato I4.
4. Vega resolves to D3; Mavis A2 and Poppy C6.
5. Seth is B1 in the Equipment Hall.
6. Vega is the only other person in Seth's final area.
7. The final access coordinate is D3.

- **Room Zero / meta signal:** {"code": "ACCESS-29", "label": "D3", "reaction": "D3 is an earned coordinate. The four-symbol code is already in your earlier file.", "reader_move": "Bring the Case 05 code and D3 to the final lock.", "speaker": "dilo", "status": "FINAL LOCK READY"}
- **Later callback / required reuse:** D3 is required by Case 30 ROOM stage; no extra empty-room letter.
- **Final QA status:** Logic **PASS** for the bound inputs. Rendered visual evidence, numeric marker clarity, clues-before-puzzle placement and page references require the separate V3 PDF audit.

## Case 30 — THE MYSTERY OF ROOM ZERO

- **Narrative setup:** The hatch opens into a room the modern Academy forgot. Six badge hooks wait on the wall. Five are occupied.
- **Objective:** Use only evidence already earned to open the final lock and identify the missing detective.
- **Puzzle type:** multi-stage-finale.
- **Happy Makers:** GRANDMA BIBI, MIMI, LULI, DILO, ALIO, NINI.
- **Unique intended answer:** {"CODE": ["BALL", "STAR", "BOLT", "HEART"], "DETECTIVE": "READER-WRITTEN NAME", "ROOM": "D3", "RULE": "ASSUMPTIONS"}
- **Other participants:** No additional named solver/witness beyond the listed team is required..
- **Rules:** Use previously earned word, coordinate and code plus the chosen reader ID; introduce no new lock rule.
- **Solvability evidence:** All four lock fields equal answers earned earlier: Rule Zero word, boss coordinate, unique four-symbol code, and the reader’s one opening ID. Reader name is intentionally variable, not a fixed spelling puzzle.
- **Timing/rule assumption:** Reader identity reveal depends on the invitation and NEXT DETECTIVE hook being shown before asking for identification; causal system explanation needs story QA.
- **Naming aliases:** Named nonspatial participants are taken from this publication case’s evidence; no source-name substitution is used in the solver.
- **Visual assets:** four final lock fields, reader ID and five badges plus one NEXT DETECTIVE hook.

### Evidence given to the reader

1. stages: [{"answer": "ASSUMPTIONS", "id": "RULE", "prompt": "Complete Rule Zero.", "source_case": 28}, {"answer": "D3", "id": "ROOM", "prompt": "Enter the access coordinate earned on the service-level map.", "source_case": 29}, {"answer": ["BALL", "STAR", "BOLT", "HEART"], "id": "CODE", "prompt": "Enter Dilo's four-symbol locker sequence.", "source_case": 5}, {"answer": "READER-WRITTEN NAME", "id": "DETECTIVE", "prompt": "Write the name printed on your Detective ID.", "source_case": "opening"}]

### Deduction path

1. Complete Rule Zero with ASSUMPTIONS.
2. Use D3 from Case 29.
3. Use BALL, STAR, BOLT, HEART from Case 5.
4. Use the reader-written name from the opening Detective ID.
5. The sixth badge hook says NEXT DETECTIVE.
6. The reader has been the missing detective from page one.

- **Room Zero / meta signal:** {"code": "MEMBER-30", "label": "SIXTH BADGE HOOK", "reaction": "The system was looking for a detective who notices before assuming. It found you.", "reader_move": "Sign the certificate with the detective name you chose at the start.", "speaker": "nini", "status": "ACADEMY MEMBER"}
- **Later callback / required reuse:** Book 1 resolves; new incoming case belongs to Book 2 and supplies no retroactive Book 1 clue.
- **Final QA status:** Logic **PASS** for the bound inputs. Rendered visual evidence, numeric marker clarity, clues-before-puzzle placement and page references require the separate V3 PDF audit.
