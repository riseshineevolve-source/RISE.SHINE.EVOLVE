# AI Discovery technical refresh — 2026-09-26

Branch: `codex/ai-discovery-technical-refresh`

Starting revision: `a60992e`

Scope: homepage, two app pages, Seniors, four C1 guides, HTML/XML site maps, robots, structured data, metadata, links, and repository delivery checks.

## Verified source result

- `npm run ai:technical` passes: 8 tracked HTML pages, 26 canonical sitemap URLs, 23 visible HTML site-map entries, and 0 retired-claim matches in the 25-page SEO inventory.
- The eight tracked pages have the expected self-canonical, matching `og:url`, indexable robots metadata, `en`/`x-default` alternates, and WebPage JSON-LD name/description matching their title/meta description. OG and Twitter title/description are present. The four C1 FAQ schema question/answer pairs match the visible FAQ text.
- Both app pages still describe Android/Google Play as coming soon in visible copy and `SoftwareApplication` schema, with no `Offer`. Seniors is a coming-soon audience page, not a fabricated product listing.
- `robots.txt` remains `User-agent: *` / `Allow: /` with the canonical sitemap URL. No training-crawler policy was changed. The sitemap has 26 unique expected URLs and matching `en`/`x-default` alternates.
- The repository contains a Worker deployment command, but no verified static-site deploy command. Cloudflare response headers prove it is on the public serving path, not the exact static origin or dashboard setup.

The deterministic metadata snapshot is [`source-metadata-2026-09-26.json`](source-metadata-2026-09-26.json). It records title, description, canonical, OG/Twitter fields, robots directive, schema types, and source modification date for all eight tracked pages. Run `npm run ai:technical` for a concise result or `node scripts/audit-discovery.mjs --json` for a fresh machine-readable snapshot. No paid service or Search Console data is used by this script.

## Concrete source fixes

1. Removed the homepage `SearchAction` that pointed to `/site-map/?q=...`; the target is a static list and has no search implementation.
2. Added crawlable homepage links to the four C1 guides, both coming-soon app pages, and the HTML site map. The previous homepage had none of those anchor links.
3. Added both app pages to the visible HTML site map, then made its 23 `ItemList` entries follow the visible order and names. Previously the app pages were missing and the structured list order/names differed from the visible list.
4. Updated modification signals for the changed homepage and HTML site map, including their sitemap `lastmod` dates. Canonical and OG URLs did not change.
5. Added a free source audit to the quality script and CI. Extended the production verifier to Seniors and the HTML site map and made exact source/live body parity a required pass condition. Generated run files are ignored by Git.

## Retired-term count, before → after

| Source check | Before | After | Interpretation |
| --- | ---: | ---: | --- |
| `PWA`, `SaaS`, `Paddle`, 365-day access, 12-month access, 1-year access pass, instant web-app access, “No App Store needed” across 25 SEO HTML pages | 0 | 0 | No current source claim to remove. |
| `web app` positioning on the two app pages | 0 | 0 | Both remain Android/Google Play coming soon. |
| Bare “12 months” on homepage | 2 | 2 | Both refer to Grandma Bibi book adventure/coloring content, not app access or subscription duration. |
| Homepage links to four C1 guides, two apps, and HTML site map | 0/7 | 7/7 | Crawlable links added. |
| HTML site-map links to the two app pages | 0/2 | 2/2 | App URLs now included in visible and structured lists. |
| Homepage `SearchAction` to static site map | 1 | 0 | Unsupported action removed. |

## Live delivery and tests

Before source edits, the existing production verifier checked 9 routes at 2026-09-26 19:46 UTC: all returned HTTP 200 and all nine bodies matched the checkout exactly. After source edits, the expanded verifier checked 11 routes at 19:54 UTC: all returned HTTP 200, and 8 matched exactly. `/`, `/site-map/`, and `/sitemap.xml` differ because this branch's changes are local and have not been deployed; the live HTML site map still lacks the two app links. The two app pages, Seniors, four C1 guides, and robots remain exact live/source matches. This expected parity failure is recorded, not treated as an indexing failure.

Validation after changes:

- `npm run quality:all` — pass (SEO validation 1,377 checks; SEO audit 117 checks; AI truth layer; new technical audit; evaluation spec/template).
- `npm run analytics:validate` — pass (31 HTML files).
- `node --check` on both edited audit/verifier scripts — pass.
- `git diff --check` — pass.
- `npm run production:verify` — expected failure until source changes reach production: 8/11 exact body matches, 11/11 HTTP 200.

## Measurement boundary and next action

The last durable Search Console evidence in [issue #584](https://github.com/riseshineevolve-source/RISE.SHINE.EVOLVE/issues/584) is historical: four C1 guides indexed, 7/10 tracked URLs indexed, `/adventure-app/` and `/unstoppable-app/` crawled but not indexed on 2026-06-16 and 2026-07-04 crawls, and `/seniors/` unresolved. GSC Wizard returned `payment_required` on 2026-09-24; no fresh Search Console inspection was performed here. Public search still showed stale app copy in the last recorded sample on 2026-09-24, but no new public-search baseline was measured in this audit. Cloudflare Crawler Hints was recorded as enabled on 2026-09-17, but its current account setting was not independently rechecked. Bing API-key visibility is also unavailable here.

Free next step: after these source changes are deployed through the verified site deployment path, rerun `npm run production:verify`. Then use the native Search Console UI, if the owner has direct access, to inspect/request indexing for the two app URLs and inspect Seniors and sitemap status; repeat the saved public-search baseline after recrawl. This does not require reactivating GSC Wizard. C2 Anger/Growth Mindset pages remain gated on fresh intent evidence and owner authorization.
