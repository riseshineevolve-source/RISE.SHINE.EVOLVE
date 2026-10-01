# Gentle Steps — Internal testing readiness

Status: SOURCE/BUILD CANDIDATE — pending current-head CI and owner real-device install.

## Automated source gates

Required before owner device install:
- full EN validator green;
- Home / Family / Day 01 / Day 12 / Day 22 / Day 23 / Day 24 proof render green;
- host SEO/privacy/Lighthouse green;
- Android lintDebug + debug APK + unsigned AAB green;
- provisional icon/splash present in generated Android resources.

## Owner real-device smoke test

Install the debug APK on one Android phone and verify:
1. branded launcher icon and purple/gold splash;
2. Home opens without clipped text or horizontal scroll;
3. Family sheet opens/closes and remains scrollable;
4. Day 01 reads comfortably;
5. Day 22 and Day 23 long content can be read to the bottom;
6. complete a day, kill/restart app, completion remains;
7. turn airplane mode on, reopen app, content still works;
8. set a reminder, grant notification permission, verify reminder remains local/device-only;
9. increase system font size one step and repeat Home + one long day;
10. enable TalkBack for a short pass through Home → Day → Complete.

Passing this smoke test is the remaining evidence needed to label the current build READY FOR INTERNAL TESTING on real hardware.

## Still owner-gated before Google Play creation

- final package ID;
- final icon/splash approval;
- signing / Play App Signing;
- pricing/monetization;
- Data Safety/privacy declarations;
- store creation/upload/publication.
