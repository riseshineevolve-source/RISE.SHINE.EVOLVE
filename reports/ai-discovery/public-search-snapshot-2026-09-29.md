# Public-search snapshot — 2026-09-29

Method: ordinary public web search at approximately 21:48 UTC. This is a sampled search-result and cached-text observation, **not Search Console URL Inspection or proof of current Google indexing**. Result order and snippets can vary by engine, location, and time.

## Repeated baseline and app queries

| Query | Returned sample |
| --- | --- |
| `kids big feelings practical resource family book` | The returned batch was dominated by third-party books/resources; no RSE C1 guide was observed in that batch. |
| `kids screen balance practical family resource book` | The returned batch listed third-party screen-balance books/resources; no RSE C1 guide was observed in that batch. |
| `"Rise.Shine.Evolve." official website` | The [RSE homepage](https://rise-shine-evolve-learning-hub.com/) surfaced in the branded result batch. Its search text still included older “Interactive web apps” / “Available Soon Web App” wording. |
| `site:rise-shine-evolve-learning-hub.com/guides/ "Big Feelings in Kids"` | No exact C1 guide URL observed in the returned batch. |
| `site:rise-shine-evolve-learning-hub.com/guides/ "After-School Crash"` | The [World 01 library page](https://rise-shine-evolve-learning-hub.com/library/world-01/) appeared; no exact C1 guide URL observed in the returned batch. |
| `site:rise-shine-evolve-learning-hub.com/guides/ "Screen Balance for Kids"` | No exact C1 guide URL observed in the returned batch. |
| `"Project Unstoppable App" "Rise Shine Evolve"` and `site:rise-shine-evolve-learning-hub.com/unstoppable-app/ Project Unstoppable` | A result targeting the [Unstoppable app page](https://rise-shine-evolve-learning-hub.com/unstoppable-app/) still returned an older crawled text view with retired SaaS/PWA, 1-year/12-month access, 365-day expiry, and Paddle/payment/refund language. The search result labeled its crawl approximately two weeks old. |
| `site:rise-shine-evolve-learning-hub.com/adventure-app/ "Confident"` | The returned sample did not surface the exact Adventure app URL; it surfaced the homepage. This does not establish indexing status. |

## Interpretation and boundary

The 2026-09-29 read-only production verifier returned HTTP 200 for all 11 checked routes. Both app pages and the four guides matched current repository source byte-for-byte. The current Unstoppable source/live page says **Coming Soon on Google Play** and contains none of the retired wording above. The stale public-search text is therefore a cached representation, not current production copy in the tested page. The homepage, HTML site map, and XML sitemap differ from the refreshed local branch because its changes are not deployed.

The observed public results continue the stale-snippet and weak unbranded-guide signal recorded on 2026-09-19 and 2026-09-24. They cannot update the historical GSC counts, crawl dates, or Google-selected canonical. GSC Wizard remained externally gated by `payment_required`; no paid access was restored and no fresh Search Console evidence was claimed. No C2 content decision follows from this sample.
