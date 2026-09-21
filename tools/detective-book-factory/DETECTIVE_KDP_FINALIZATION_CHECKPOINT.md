# Detective KDP Finalization Checkpoint

Status: **PILOT WITNESS BOARD PASS / SCALE OUT PENDING**

## Witness Board implementation

`scripts/render_spatial_case_spreads.py` renders a reusable Letter-size paired
page family from canonical mission copy plus the validated runtime bundle:

1. premium Witness Board with case hierarchy, hook, objective, short field
   note, pencil-tick evidence cards, and Rule Zero footer;
2. large Live Case Map with a reader verdict field.

Source clue text is not edited. The renderer substitutes only deterministic
presentation aliases and bolds them in evidence cards.

## Pilot QA

HMDA_02, HMDA_13, and HMDA_29 render as two-page paired spreads. Visual review
of the 144 DPI HMDA_29 preview confirms an unclipped, light, readable dossier
page; source-name case sensitivity was found and fixed before acceptance.

## Validation

- PASS: all 15 locked modules match checkpoint geometry and Room Zero meta.
- PASS: aliases are source-complete and initial-unique per case.
- PASS: pilot spreads render from canonical master copy and validated aliases.
- PASS: no answer, coordinate, or Room Zero meta signal appears on Witness
  Board or Live Case Map pages.

## Scale and book integration

All-15 scale and canonical-master attachment remain pending. The pilot family
is ready for mechanical expansion once its solution-treatment attachment is
implemented with the same alias/runtime input.

## Marketing

`KDP_POSITIONING_COPY.md` contains the durable spoiler-safe product language.

## Owner gates

No new owner design gate is required for mechanical all-15 scale. KDP upload,
price, final cover, and physical proof remain owner-only gates.
