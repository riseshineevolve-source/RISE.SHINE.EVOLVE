# Gentle Steps Android shell

Status: PRE-PLAY NATIVE BUILD LANE.

This shell packages the source-locked English 24-day Gentle Steps app with Capacitor 8 for Android.

## Current package identity

`com.riseshineevolve.gentlesteps`

This ID is **provisional until the owner approves the final Google Play package identity**. It can be changed safely before first Play publication. Do not create the Play listing or publish under this ID without explicit owner approval.

## Native behavior

- offline bundled 24-day EN content;
- local progress remains on-device;
- no account/backend requirement;
- character assets are optimized to WebP during the native build;
- optional daily reminder uses Capacitor Local Notifications;
- reminder is scheduled locally on-device only after the user explicitly chooses a time;
- Android 13+ notification permission is requested only when the user saves a reminder;
- no push-notification server.

## Build

Node 22+ is required by Capacitor 8.

```bash
npm install
npm run android:generate
cd android
./gradlew assembleDebug
./gradlew bundleRelease
```

The release bundle generated without signing secrets is build evidence only. A Google Play release still requires final package-ID approval, signing/App Signing setup and store declarations.

## Deliberate release gates

Do not silently:
- create a Google Play application;
- create/upload a signing keystore;
- make pricing decisions;
- add analytics/advertising SDKs;
- add a backend;
- publish to internal/closed/production tracks.
