# Detective KDP Finalization Checkpoint

Status: **V4.1 SOURCE POLISH COMPLETE / OWNER VISUAL GATE OPEN / ENGLISH NOT FROZEN**

Updated: 2026-09-23
Canonical branch: `feature/detective-book-factory`
PR: #571 (Draft; do not merge without owner approval)
Verified implementation head before this checkpoint sync: `5560207f80fa8a1f1392ff782ee38920365ac798`
Latest Detective build: **#155 PASS**
Latest confirmed SEO validation: **#671 PASS** (`#675` was still in progress when this checkpoint was written)

## Protected product decisions

Do not reopen the locked 30-case logic, five-act story, Detective Six premise,
Room Zero causal mechanism, Naming B, numeric witness IDs, solved Shigai
geometry, first-five signals, `CHECK THE OLD MAP`, Rule Zero, D3, locker
sequence, or Book 2 premise unless a concrete regression requires the smallest
possible fix.

## V4.1 source state

The canonical source contains the V4.1 finalizer, reverse-entry engine,
Case 26 generated page references, owner-visual fail-closed gate, reader-surface
cleanup, Signal Log / Witness Board / finale / certificate presentation layers,
print typography QA, grayscale audit, final-artifact audit, and the locked-V4
spatial recovery bridge.

The owner-audit layer also provides:

- exact Field Detective ID fields `DETECTIVE NAME` + `OFFICIAL CALL SIGN` with
  field slot `06`;
- Case 30 / finale prompts that explicitly ask for the `OFFICIAL CALL SIGN`;
- a dedicated front-matter **CASE WALL / EVIDENCE LOG** at physical page 009,
  using the existing page slot so case/map pagination is not shifted;
- front onboarding on page 008 that explicitly instructs the reader to **STOP,
  turn the book upside down, and open from the back** for Hint Vault / Solutions;
- a direct callback from the ID/onboarding surfaces to the shared Case Wall;
- non-ceremonial certificate meta copy removed;
- the ARCHIVE Signal Log family no longer overuses a giant Room Zero glyph.

These are presentation/navigation corrections only. They do not change case
logic, clue text, spatial geometry, answers, or English freeze state.

## Physical STOP / Hint Vault boundary — completed

The canonical V4.1 finalizer inserts one dedicated upright support divider at
**physical page 110** after locked main-content page 109.

Deterministic contract:

- locked V4 recovery/source builder remains **145 pages**;
- final V4.1 physical artifact is **146 pages**;
- physical pages **1-109 remain unchanged in position**;
- page **110** is the upright `STOP // HINT VAULT // SOLUTIONS` boundary;
- reverse-entry Hint Vault / Solutions starts on page **111** and continues to
  page 146;
- the divider explicitly says to turn the whole book upside down, open from the
  back, take the smallest needed hint, then return to the case;
- reverse-entry constants, index, manifest and fail-closed artifact audit are
  updated deterministically for the 146-page contract.

## Final owner-audit source polish — completed

The remaining asset-independent presentation work is now implemented in
`scripts/build_owner_review_v41.py` and passed the full Detective workflow at
implementation head `5560207f80fa8a1f1392ff782ee38920365ac798`.

### 11 parity interludes

The case-specific `CASE WALL // FIELD INTERLUDE` pages no longer share one
repeated layout. They rotate deterministically through four grayscale-safe page
families while preserving the same usable `FACTS / SIGNALS / QUESTIONS`
function, unique Happy Makers field note, page count and case order:

- `TRIAGE_COLUMNS`
- `EVIDENCE_RAIL`
- `CASE_STRIPS`
- `CROSSCHECK_GRID`

The family selector is stable from case number + physical page and uses no
render-order state. Each interlude also names the current case file so the page
is visibly case-specific rather than generic filler.

### Book 2 hook

The owner-locked Book 2 archival surface is now prepared as
`CINEMATIC_ARCHIVE_WAKE_V1` instead of a bullet-report treatment:

- large preserved-aspect-ratio archive photo stage;
- archive wake / CASE 001 framing;
- sequential `CUT 01-03` story beats instead of bullet points;
- a dedicated `VOICE TRACK // HAPPY MAKERS` panel;
- unchanged final-line / next-file premise.

This source change does **not** select, regenerate, restyle or destructively
crop the owner-gated Book 2 image. The cinematic surface executes only after an
explicit owner-locked visual manifest passes the existing visual gate.

## Owner visual gate

The final owner-supplied visual set is expected to contain exactly four files:

- `case03_photo_A.png`
- `case03_photo_B.png`
- `case03_solution.png`
- `book2_archive_photo.png`

The current canonical source intentionally still knows the older three-asset
gate. Do **not** pre-approve or synthesize the fourth asset. When the owner
supplies the exact four final files, the local final pass must:

1. extend the gate to all four files;
2. SHA-lock the exact owner files;
3. integrate the exact `case03_solution.png` into Case 03's solution slot;
4. fail closed unless all four files validate;
5. never regenerate, restyle, destructively crop, or silently substitute any
   owner-supplied visual.

## Validation

- Detective Build #155: **PASS** at implementation head
  `5560207f80fa8a1f1392ff782ee38920365ac798` after the interlude-family and
  cinematic Book 2 source polish.
- SEO Validation #671 remains the latest confirmed PASS at checkpoint time;
  SEO #675 for the same implementation head was still in progress when this
  checkpoint was written.
- The final-artifact contract verifies 146 Letter pages, page 110 divider
  orientation/content, unchanged case/map pages 1-109, correct 180-degree
  reverse support, index/manifest/reverse-contract integrity, Case 26 generated
  references, grayscale-only output and `english_frozen=false`.
- English remains **NOT FROZEN**.
- `main` remains outside this PR lane and must not be touched until explicit
  owner approval.

## Current lane

Source-side V4.1 premium polish that is independent of owner art is exhausted.
Do not manufacture further refactors or audits. Wait for the exact four owner
visual files, then run the bounded final Codex pass to extend the gate to four,
SHA-lock the exact files, integrate `case03_solution.png`, render the canonical
146-page artifact, and perform full-page human visual QA plus physical
back-entry simulation.

## Owner-only gates

Do not automatically:

- freeze English;
- select, regenerate, restyle, destructively crop or silently substitute
  owner-gated visuals;
- merge PR #571 or touch `main`;
- publish or upload to KDP;
- change cover or price;
- begin Polish Detective production before explicit English freeze;
- activate paid marketing or make legal/compliance declarations.

Current owner action required: **provide the four exact final visual files when ready**.
