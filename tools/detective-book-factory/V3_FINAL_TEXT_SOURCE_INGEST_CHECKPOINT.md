# Detective Academy — V3 Final Text Source Ingest Checkpoint

Date: 2026-09-28  
Branch: `feature/detective-book-factory`  
Status: SOURCE INGESTED / PROVENANCE VERIFIED / RENDERER WIRING STILL OPEN / EN NOT FROZEN

## What changed

The exact owner-authorized V3 final text master is now durably present inside the Detective book factory at:

`tools/detective-book-factory/content/DETECTIVE_ACADEMY_BOOK1_TEXT_GOLD_MASTER_V3.md`

Authoritative upstream:
- repo: `riseshineevolve-source/agency-agents`
- source: `orchestration/detective/DETECTIVE_ACADEMY_BOOK1_TEXT_GOLD_MASTER_V3.md`
- commit: `6c2e21a24d760218923cfd8d47655a3cbf72c575`
- Git blob: `f6e16e99084562ddf56825ccc7bfdd12baad0656`

Ingest commit:
`9a67c95451450f38cf56cec6a3ed154153db23bd`

A fail-closed source verifier was added at:

`tools/detective-book-factory/scripts/verify_v3_final_text_source.py`

Verifier commits:
- initial verifier: `02e9ad7d5fde98980f77730dbc3a2e5a0d724dfe`
- canonical Case 21 arrow-notation correction: `03ca0eebc9137ee74dca12e3b836b230aeffe477`

## Verified source invariants

Direct branch read confirms the ingested file has the exact canonical Git blob
`f6e16e99084562ddf56825ccc7bfdd12baad0656`.

A bounded static verification of the exact source confirms:
- 30/30 main reader cases in order;
- 30/30 Hint Vault entries at each of Levels 1, 2 and 3;
- 30/30 Solution Files;
- Case 03 exact-ten solution list contains exactly items 1-10;
- Case 05 is the six-symbol version and resolves to
  `BALL -> STAR -> BOLT -> HEART -> KEY -> MOON`;
- Case 21 preserves physical order `B → D → A → C` and
  `THE ANSWER IS IN WHAT YOU LEAVE EMPTY`;
- Case 26 MAP LOOKUP is exactly
  02, 04, 06, 07, 10, 12, 13, 15, 17, 19, 20, 22, 23, 25;
- Case 01 is excluded from that fourteen-map extraction set;
- Case 01 support surfaces preserve QUILL / MORSE / PIP / KNOX;
- Rule Zero remains `ZERO ASSUMPTIONS. NOTICE FIRST. THEORIZE SECOND.`;
- Case 29 access coordinate remains `D3`;
- Book 2 hook remains `ARCHIVE FILE 001 // STILL OPEN`;
- all 30 cases retain an `EVIDENCE / PUZZLE TEXT` hydration surface.

## CI evidence

At head `03ca0eebc9137ee74dca12e3b836b230aeffe477`:
- Detective Build #179 / run `36442878914`: PASS.
- SEO Validation #730 / run `36442878781`: in progress at checkpoint time.

Build #179 proves the existing factory pipeline was not broken by the source ingest.
It does **not** prove that the new V3 verifier is executed in CI and does **not**
prove renderer integration.

An attempt to add the V3 verifier directly to
`.github/workflows/build-detective-book.yml` was blocked before mutation by the
GitHub/OpenAI workflow write-safety gate. No workflow change was made.

## Important non-claims

This checkpoint does NOT claim:
- the historical V4/V4.1 reader copy has been replaced in rendered output;
- the renderer is already using V3 as its text authority;
- Case 03 owner art is hydrated;
- locked Witness Boards/maps/archive/finale evidence is fully hydrated;
- final pagination is known;
- KDP preflight or human visual audit has passed for a V3 render;
- English is frozen.

The existing V4/V4.1 production files remain useful only as locked
logic/evidence/layout source where they do not conflict with current V3 reader copy.

## Next safe production slice

1. Build a bounded V3 reader-copy integration bridge that consumes the exact
   ingested source rather than historical V4/V4.1 prose.
2. Preserve evidence as source-backed hydrated surfaces; do not reconstruct
   missing Case 03/photo/archive/map truth from prose.
3. Enforce QUILL / MORSE / PIP / KNOX on the rendered Case 01 evidence surface.
4. Remove early reader-facing field-slot / "Detective Six" reveals that conflict
   with the V3 recruit-to-certification arc.
5. Re-run Case 03 / Case 05 / Case 21 / Case 26 / Room Zero regressions after
   hydration.
6. Let the resulting text determine final pagination; reflow/add pages before
   deleting approved text.
7. Only after a complete render: deterministic KDP preflight + full human
   print-scale visual audit.

No main merge, EN freeze, KDP upload/publication, price change or locked-cover
change is authorized by this checkpoint.
