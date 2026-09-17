# Public Search Discovery Snapshot — 2026-09-17

## Scope

This is the first exact-query public-search rerun after the 2026-09-16 sitemap submission and the 2026-09-17 Google recrawl/indexing change.

It uses the same ChatGPT web-search surface and the same six benchmark query strings recorded in `public-search-snapshot-2026-09-16.md`.

This is not a substitute for Google Search Console. GSC is the authoritative source for Google indexing state; this report measures what the public-search surface returned for the benchmark wording at this moment.

## Exact queries rerun

### Unbranded discovery

1. `kids big feelings practical resource family book`
2. `kids screen balance practical family resource book`

### Branded / entity discovery

3. `"Rise.Shine.Evolve." official website`

### New C1 guide index checks

4. `site:rise-shine-evolve-learning-hub.com/guides/ "Big Feelings in Kids"`
5. `site:rise-shine-evolve-learning-hub.com/guides/ "After-School Crash"`
6. `site:rise-shine-evolve-learning-hub.com/guides/ "Screen Balance for Kids"`

## Observations

### 1. GSC index state has improved materially

Separate live GSC URL Inspection on 2026-09-17 reports all four C1 guides as `PASS` / `Submitted and indexed`, with successful mobile fetches and crawl times on 2026-09-17.

This is a major change from the 2026-09-16 baseline, when all four guide URLs were unknown to Google.

### 2. Public-search guide queries still returned no result in this rerun

The three exact site-restricted guide queries returned no public-search results on this search surface at the time of the rerun.

Interpretation: Search Console can already report a page as submitted/indexed while a separate public-search provider or query surface has not yet surfaced it for a particular query. This is evidence of propagation/ranking lag, not evidence that the guides are still unknown to Google.

### 3. Unbranded discovery remains weak in the two exact sampled intents

The Big Feelings query returned other publishers/resources such as Little Calm Club, Penguin Random House/other books and family resources. RSE was not observed in the returned result set.

The Screen Balance query returned other resources/products. RSE was not observed in the returned result set.

So the 2026-09-16 conclusion remains unchanged for these two narrow unbranded samples: RSE is not yet observed in the returned result set.

### 4. Branded exact query was not returned by this search surface in the rerun

The exact benchmark query `"Rise.Shine.Evolve." official website` returned no result in this rerun.

This does not override GSC evidence or the earlier 2026-09-16 observation that branded discoverability existed. It is a provider/query-surface observation and should be treated as such.

### 5. Stale snippet question is not yet resolved by this sample

Because the exact branded/site-restricted queries did not return RSE snippets in this rerun, this run cannot yet prove whether retired PWA/SaaS/Paddle snippet language has disappeared from public-search results.

Do not manufacture a pass/fail result for snippet freshness until RSE snippets are actually returned and can be compared.

## Before / after

| Signal | 2026-09-16 | 2026-09-17 |
|---|---|---|
| GSC C1 guide discovery | 4/4 unknown to Google | 4/4 submitted and indexed |
| Public-search site-restricted guide visibility | not observed | still not observed on sampled search surface |
| Unbranded Big Feelings visibility | not observed | not observed |
| Unbranded Screen Balance visibility | not observed | not observed |
| Retired snippet cleanup | stale snippets observed | not measurable in this run because RSE snippet did not surface |
| Evidence to create C2 Anger/Growth Mindset pages | insufficient | still insufficient |

## Decision

Do **not** open C2 Anger/Growth Mindset pages yet.

The largest technical change since the baseline is positive: all C1 guides are now indexed in Google Search Console. Public-search discovery/ranking has not caught up in these exact samples, so the correct next move is measurement after additional propagation time, not immediate new-content production.

Keep `/adventure-app/` and `/unstoppable-app/` under indexing observation separately. They remain `Crawled - currently not indexed` in GSC with old crawl dates, unlike the four new guides.
