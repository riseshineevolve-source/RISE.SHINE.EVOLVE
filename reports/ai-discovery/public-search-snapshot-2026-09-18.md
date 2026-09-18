# Public Search Discovery Snapshot — 2026-09-18

## Scope

Second exact-query public-search propagation check after the 2026-09-16 sitemap submission and 2026-09-17 Google recrawl/indexing change. Same benchmark wording as the 2026-09-16 and 2026-09-17 snapshots.

GSC remains authoritative for Google indexing state; public search is a separate discovery/ranking signal.

## GSC verification

Live GSC Wizard tracker check on 2026-09-18 shows all four C1 guides as `PASS` / `Submitted and indexed`. A targeted fresh inspection of `/guides/confidence-for-kids/` was run because the tracker initially showed stale `URL is unknown to Google`; the fresh result self-repaired that apparent discrepancy and confirmed `PASS`, with last crawl `2026-09-17T10:59:31Z`.

The two app pages remain `Crawled - currently not indexed` with old crawl dates:
- `/adventure-app/`: last crawl 2026-06-16
- `/unstoppable-app/`: last crawl 2026-07-04

No tracker errors or warnings were present after the check.

## Exact public-search benchmark

Queries rerun:
1. `kids big feelings practical resource family book`
2. `kids screen balance practical family resource book`
3. `"Rise.Shine.Evolve." official website`
4. `site:rise-shine-evolve-learning-hub.com/guides/ "Big Feelings in Kids"`
5. `site:rise-shine-evolve-learning-hub.com/guides/ "After-School Crash"`
6. `site:rise-shine-evolve-learning-hub.com/guides/ "Screen Balance for Kids"`

## Observations

- Unbranded Big Feelings discovery remains weak: the sampled result set surfaced established competing resources rather than RSE.
- Unbranded Screen Balance discovery remains weak: the sampled result set surfaced established competing resources rather than RSE.
- The combined search surface did surface an RSE library page (`/library/world-01/`) during the benchmark batch, which is a small positive sign that the domain is being crawled and can surface, but it is not sufficient evidence to claim success for either exact unbranded benchmark intent.
- No evidence in this run justifies opening C2 Anger/Growth Mindset pages.
- The app-page indexing problem remains separate from the now-successful C1 guide indexing state.

## Decision

Keep C2 unauthorized. Continue propagation measurement rather than creating speculative content. Maintain `/adventure-app/` and `/unstoppable-app/` as the active indexing follow-up because they remain the clearest unresolved technical discovery signal.
