# Production Delivery Snapshot — 2026-09-16

## Result

**PASS — production is current for the tested AI-discovery surface.**

A GitHub-hosted external verification run fetched the public production domain directly on 2026-09-16 at approximately 17:38 UTC and compared each response against the corresponding repository file checked out from the verification branch, whose public-site files are unchanged from current `main`.

## Verified routes

All 9 checks returned HTTP 200 and passed required/forbidden content checks:

1. `/`
2. `/adventure-app/`
3. `/unstoppable-app/`
4. `/guides/big-feelings/`
5. `/guides/confidence-for-kids/`
6. `/guides/after-school-crash/`
7. `/guides/screen-balance/`
8. `/sitemap.xml`
9. `/robots.txt`

## Byte/content parity

All 9 production responses matched the normalized local repository files exactly by SHA-256.

- checks: 9
- exact body matches: 9
- exact body match rate: 100%

This is stronger than checking titles or snippets. It establishes that the tested live HTML/XML/text bodies are the same content currently represented in the repository for those routes.

## App truth checks

Both app pages passed the current canonical requirements:

- Android / Google Play positioning is present
- `Coming Soon on Google Play` is present
- `operatingSystem: Android` structured data is present
- no tested retired `Progressive Web App` / `PWA` / `SaaS` / Paddle / 12-month web-access language was found

Therefore the stale PWA/SaaS/Paddle text observed in public-search snapshots is **not current production copy**.

## C1 guide delivery

All four C1 guide routes are live and match the repository exactly:

- Big Feelings
- Confidence for Kids
- After-School Crash
- Screen Balance

The sitemap and robots files also match the repository exactly, including the C1 guide discovery entries.

## Serving-layer signals

Observed response-header signals across the tested routes:

- `server: cloudflare`
- Cloudflare `cf-ray` present
- no `x-nf-request-id` observed
- no `x-vercel-id` observed

Interpretation:

- Cloudflare is definitely on the public serving path / edge.
- The test does not by itself prove whether the static origin is Cloudflare Pages or another origin behind Cloudflare.
- No Netlify- or Vercel-specific response-header signal was observed in this run.

Do not overstate this as proof of the exact dashboard/project integration until that configuration is inspected directly.

## Main conclusion

The previously observed stale public-search snippets are now classified as an **index freshness / recrawl issue**, not a production-content parity issue.

Current state:

- repository truth: current
- tested live production: current
- live-vs-repo parity: exact for 9/9 tested routes
- public search snippets: still stale in sampled results
- C1 guide search visibility: not yet observed in same-day sampled site-restricted searches

## Operational follow-up

A reusable verifier now exists at:

- `scripts/verify-production-delivery.mjs`
- `npm run production:verify`
- `.github/workflows/production-verification.yml`

The dedicated workflow also uploads a machine-readable report artifact.

## IndexNow decision

Production parity is now confirmed, satisfying the earlier safety prerequisite for considering IndexNow.

However, the existing IndexNow implementation requires `INDEXNOW_KEY`, and the official protocol requires ownership verification using a key file. The current repository intentionally does not commit the key.

Therefore IndexNow should only be activated after a key and key-location strategy are configured without exposing the key in the public repository.

## C2 status

C2 content expansion remains blocked.

There is no evidence yet that adding Anger or Growth Mindset pages is more useful than allowing the already-correct production pages to be recrawled and measuring the result against the new benchmark.
