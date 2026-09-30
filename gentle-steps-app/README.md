# Gentle Steps Advent app - Days 1-3 vertical slice

Status: owner-review vertical slice, not deployed and not publication-authorized.

This folder is the first real product conversion of 24 Gentle Steps to Christmas into a simple EN + PL mobile-first Advent experience.

What works:
- 24-day calendar shell;
- real published English content for Days 1-3;
- native Polish re-authoring candidate for Days 1-3;
- three recurring daily ritual cards;
- local completion progress;
- persistent EN / PL choice;
- offline-first service worker and installable web-app manifest;
- no account, backend, social feed or AI dependency.

Source evidence:
- published English paperback pages 21-29 were visually re-read on 2026-09-30;
- Polish copy in this slice is intentionally not the earlier close translation/calibration wording;
- pl-PL text is a fresh native-family-language candidate and requires owner editorial approval before scale-out.

Local validation:
node gentle-steps-app/tests/validate-slice.mjs

Remaining after owner approval:
1. scale content mapping to all 24 days;
2. run the same native PL re-authoring workflow across Days 4-24;
3. add native/local notification implementation at Android packaging stage;
4. add icons/splash/store packaging and Capacitor or equivalent Android shell;
5. real-device offline, accessibility and Play preflight;
6. owner release approval before deployment/publication.
