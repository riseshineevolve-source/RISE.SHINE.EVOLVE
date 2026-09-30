# 24 Gentle Steps to Christmas — English Advent app

Status: full 24-day English product build / owner visual review / not deployed. Final mobile proof workflow includes deterministic render wait.

## Owner direction — 2026-09-30

English first.

The final user-supplied English paperback is the text source of truth. The Polish app path is paused until the Polish re-authoring is approved.

Visual direction:
- modern Christmas rather than red/green Christmas;
- purple + gold + cream as the dominant palette;
- burgundy may be used as an elegant book-derived accent;
- elegant serif display typography;
- preserve the Happy-Makers product identity.

## What works

- all 24 real English days;
- exact 3-part daily structure: Mindful Moment / Fun Spark / Family Connection;
- source-locked copy mapped from paperback pages 21–95;
- 4 week groupings and source week quotes;
- full 24-day Advent calendar;
- local completion/progress;
- December day locking with a deterministic `?preview=1` owner/test override;
- direct day review via `?preview=1&day=N`;
- offline-first service worker;
- installable web app manifest;
- no account, social feed, AI or new backend;
- privacy-first analytics-consent contract inherited from the host repository.

## Source lock

Paperback:
- file: `24 Gentle Paperback ok(1).pdf`
- SHA-256: `1f79edd316f353963ef33bb980843b37f367a0bacb9198bd63e0d221cb8c9ba7`
- daily activity pages: 21–95
- owner state: FINAL EN TEXT

Cover reference:
- file: `24 Gentle Steps to Christmas COVER HARDCOVER(1).pdf`
- SHA-256: `3e02c50253fb136f6c21029a31cd31436e8077db5d3bf35eec16ecc5939e315b`

No editorial rewrite was performed while mapping the daily content. Layout line breaks were normalized into mobile paragraphs, while source wording was retained.

## Validation

`node gentle-steps-app/tests/validate-full-en.mjs`

## Remaining release path

1. owner visual review of the purple/gold/cream English build;
2. bounded UI fixes only;
3. Android wrapper / app icon / splash;
4. optional native local reminder;
5. real-device offline/accessibility QA;
6. Play packaging/preflight;
7. explicit owner release/publication decision.

Polish remains a separate later content lane and is not bundled in this build.
