# Public Search Discovery Snapshot — 2026-09-19

## Scope

Fresh propagation check for the AI Discovery V1 recrawl/indexing gate. This snapshot intentionally does not create new content and does not authorize C2.

Google Search Console remains authoritative for Google indexing state. Public-search results are a separate discovery/snippet propagation signal.

## Fresh Google Search Console inspection

A fresh bulk URL Inspection run on 2026-09-19 checked eight URLs.

| URL | GSC verdict | Coverage | Last crawl |
|---|---|---|---|
| /adventure-app/ | NEUTRAL | Crawled - currently not indexed | 2026-06-16T20:42:10Z |
| /unstoppable-app/ | NEUTRAL | Crawled - currently not indexed | 2026-07-04T19:26:34Z |
| /seniors/ | NEUTRAL | URL is unknown to Google | none |
| /guides/big-feelings/ | PASS | Submitted and indexed | 2026-09-17T08:20:14Z |
| /guides/confidence-for-kids/ | PASS | Submitted and indexed | 2026-09-17T10:59:31Z |
| /guides/after-school-crash/ | PASS | Submitted and indexed | 2026-09-17T03:59:00Z |
| /guides/screen-balance/ | PASS | Submitted and indexed | 2026-09-17T09:53:17Z |
| /sitemap.xml | NEUTRAL | URL is unknown to Google | none |

Inspection quota after the run: 10 / 2000 used today.

### Interpretation

- All four C1 guides remain confirmed indexed.
- Neither app page has been recrawled since the old June/July crawl.
- The Seniors page remains completely unknown to Google.
- This confirms that the unresolved discovery problem is technical propagation for app/Seniors surfaces, not a need for more C1 content.

## Sitemap / IndexNow state

GSC reports the submitted sitemap:
- path: `https://rise-shine-evolve-learning-hub.com/sitemap.xml`
- last submitted: 2026-09-16
- last downloaded: 2026-09-17
- warnings: 0
- errors: 0
- submitted web URLs: 26

The sitemap summary currently reports 0 indexed URLs, which conflicts with direct URL Inspection showing all four C1 guides as indexed. For this reason, direct URL Inspection remains the stronger evidence for individual page state.

GSC Wizard IndexNow settings remain **not configured**. No IndexNow submission was attempted because the current task explicitly forbids exposing a public key in the repository and no safe configured key/location is available yet.

Cloudflare Crawler Hints still cannot be verified from the currently connected tool surface.

## Exact public-search benchmark

The same benchmark wording used in the 2026-09-18 snapshot was rerun:

1. `kids big feelings practical resource family book`
2. `kids screen balance practical family resource book`
3. `"Rise.Shine.Evolve." official website`
4. `site:rise-shine-evolve-learning-hub.com/guides/ "Big Feelings in Kids"`
5. `site:rise-shine-evolve-learning-hub.com/guides/ "After-School Crash"`
6. `site:rise-shine-evolve-learning-hub.com/guides/ "Screen Balance for Kids"`

### Observations

- The RSE World 01 library page surfaced in the benchmark batch, so the domain continues to appear in public search.
- The sampled unbranded Big Feelings and Screen Balance result sets are still dominated by established competing resources.
- The exact C1 guide pages did not reliably surface in the sampled public-search result batch despite direct GSC confirmation that all four are indexed.
- Public search still exposes stale RSE app/product wording. A current sampled result for Project Unstoppable still describes the retired SaaS/PWA/365-day/Paddle model.
- The homepage search representation also still includes stale `Web App` wording for the app surfaces.
- This stale public-search representation is consistent with the old GSC crawl dates on the two app pages.

## Decision

**Keep C2 unauthorized.**

There is still no evidence that adding Anger/Growth Mindset pages would solve the current problem. The strongest unresolved signals remain:

1. recrawl/indexing of `/adventure-app/`,
2. recrawl/indexing of `/unstoppable-app/`,
3. first discovery/indexing of `/seniors/`,
4. propagation of current Android / Google Play product truth into public-search snippets.

Next safe action should focus on recrawl signals / indexing infrastructure rather than generating more content.
