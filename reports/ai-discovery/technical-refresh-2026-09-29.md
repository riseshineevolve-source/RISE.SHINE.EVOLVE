# AI Discovery free technical refresh — 2026-09-29

## Git and scope

- Repository: `riseshineevolve-source/RISE.SHINE.EVOLVE`
- GitHub `main` at start: `3beea54060bd22d1c289458558ec2fb1f33f0f83` (verified by remote ref, still the base of the recovered work).
- Remote branch at start: `codex/ai-discovery-technical-refresh` at `a60992e5192aba7dfeee86e7213a5367a4d8bfd3`.
- Local-only work recovered: `6f4a542bdd099b0c54585a1969c76298be213603`, a direct descendant of current `main`. All new writes were made in the dedicated `overnight-2026-09-29` clone.
- No production deploy, main merge, paid service, IndexNow key, or C2 Anger/Growth Mindset page was made.

## Source improvements ready for review

The recovered commit removes a nonfunctional homepage `SearchAction`, adds crawlable homepage links to the four C1 guides, both app pages, and `/site-map/`, adds the apps to the HTML site map, aligns its visible list and ItemList schema, updates modification dates for changed pages, and adds the deterministic `ai:technical` source audit to CI. The production verifier now checks Seniors and the HTML site map and requires exact live/source body parity.

This run strengthened the stale-claim guard to catch older app wording that the first version could miss: web-app positioning, 365-day expiry, 12-month access, 1-year access pass, instant access, all-sales-final, and browser-install wording. The check excludes the harmless `apple-mobile-web-app-*` metadata. It also fails on unsupported coming-soon app schema fields, premature Google Play listing URLs, and unverified `InStock` JSON-LD claims. No app or guide copy was changed because the live/source pages already contain the current verified Android/Google Play and C1 guide truth.

## Deterministic audit

- `npm run quality:all`: pass. SEO validation: 1,377 checks. SEO audit: 117 checks. AI truth layer, technical audit, and 20-prompt evaluation spec/template: pass.
- `npm run analytics:validate`: pass across 31 HTML files.
- `node scripts/audit-discovery.mjs`: pass, 8 tracked pages, 26 unique expected sitemap URLs, 0 retired claims across the 25-page SEO inventory.
- Four C1 FAQ schema question/answer sets match visible copy. App schema still says Android and coming soon on Google Play, with no Offer. All tracked page titles/descriptions, self-canonicals, OG URLs, indexable robots directives, and WebPage schema agree.
- `robots.txt`: wildcard `Allow: /` and canonical sitemap URL. No training-crawler policy edit.
- Metadata snapshot: [`source-metadata-2026-09-29.json`](source-metadata-2026-09-29.json).

## Read-only production check

At 2026-09-29 21:47 UTC, `npm run production:verify` checked 11 routes. All returned HTTP 200. Eight were exact body matches to the refreshed source: both app pages, Seniors, four C1 guides, and robots. The homepage, HTML site map, and XML sitemap differed, so the verifier correctly exited nonzero: **DELIVERY PENDING**, not an indexing verdict. The live site map still lacks app links and the live homepage still lacks the new direct guide/app links. The sitemap difference is changed `lastmod` values for edited pages.

A separate read-only metadata pass found all nine HTML routes HTTP 200, self-canonical, OG URL equal to canonical, and without `noindex`/`nofollow`. JSON-LD types were present on every page: `SoftwareApplication` on both app pages, `FAQPage` on all four C1 guides, and `ItemList` on the site map. The live sitemap contains 26 URLs; live robots remains wildcard allow plus the sitemap directive. Cloudflare appears in response headers, but the exact static-site deployment integration remains unverified. `npm run deploy` targets the Worker, not a confirmed static-site release path.

## Public search and external boundary

The separate [`public-search-snapshot-2026-09-29.md`](public-search-snapshot-2026-09-29.md) repeats the saved baseline and app queries. In sampled results, unbranded Big Feelings and Screen Balance queries did not surface an RSE C1 guide. A Project Unstoppable result still served stale SaaS/PWA/Paddle and old access/refund wording, despite the current live app body exactly matching the clean source. These are public-search observations, **not current Search Console status**.

The last durable GSC evidence remains historical: 4/4 C1 guides indexed, 7/10 tracked URLs indexed, both app pages crawled but not indexed on old June/July crawl dates, Seniors unresolved, sitemap accepted with no warnings/errors. GSC Wizard returned `payment_required` on 2026-09-24. No fresh URL Inspection, selected canonical, crawl-date, or current sitemap report is available from that service. Bing API-key visibility and current Cloudflare Crawler Hints account state were also not checked. The prior issue record says Crawler Hints was enabled; this is not a new verification.

## Owner's next free action

After an approved static-site deployment, rerun `npm run production:verify` and require 11/11 exact matches. Then use the native Search Console UI with the [`manual owner worksheet`](../../docs/ai-discovery/MANUAL_GSC_CHECKLIST_2026-09-29.md) to inspect both app pages, Seniors, four guides, and the sitemap; request indexing only where the live test is indexable and the page is current. Record dated GSC evidence in [issue #584](https://github.com/riseshineevolve-source/RISE.SHINE.EVOLVE/issues/584), then repeat the public-search baseline after recrawl. C2 remains blocked until fresh evidence identifies a specific intent gap and the owner authorizes it.
