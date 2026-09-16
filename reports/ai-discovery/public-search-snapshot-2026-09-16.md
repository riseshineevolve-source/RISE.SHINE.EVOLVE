# Public Search Discovery Snapshot — 2026-09-16

## Scope

This is a small observed public-search snapshot collected through ChatGPT web search on 2026-09-16.

It is **not** Google Search Console data, Bing Webmaster Tools data, a Gemini run, a Perplexity run, or a complete ChatGPT product-visibility benchmark.

Its purpose is to capture the current external search/index state immediately after AI Discovery Phase C1 so later measurements can be compared against something real.

## Queries sampled

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

### 1. Branded discoverability exists

The branded query surfaced the official Rise Shine Evolve domain, including the home page and the Project Unstoppable page.

This means the domain/entity is not completely invisible to public search.

### 2. Search-index freshness is currently a material issue

The returned indexed snippets were crawled about five days before this snapshot and still contained retired product language such as:

- `Web App`
- `SaaS`
- `Progressive Web App (PWA)`
- browser installation wording
- 12-month access-pass language
- Paddle payment wording

Those statements no longer match the current repository truth layer after Phase B.

This snapshot therefore proves an **index freshness gap**. It does not by itself prove that the current production HTTP response is stale, because the search result can be based on an older crawl.

### 3. New Phase C1 guides are not indexed yet in this sample

The three sampled site-restricted guide queries returned no results:

- Big Feelings
- After-School Crash
- Screen Balance

Because these pages were merged on the same day as this snapshot, this is a baseline observation rather than a failure condition.

### 4. Unbranded discovery is weak in the two sampled intents

The returned results for the unbranded Big Feelings query were other publishers/resources; RSE did not appear in the returned result set.

The returned results for the unbranded Screen Balance query were also other books/resources; RSE did not appear in the returned result set.

This suggests that RSE currently has stronger branded/entity discoverability than unbranded intent discoverability in these sampled queries.

## Baseline interpretation

Current observed pattern:

- Brand/entity discoverability: **present**
- Canonical new guide index coverage: **not yet observed**
- Search-index freshness: **stale relative to today's repository state**
- Unbranded discovery in sampled intents: **not observed**
- Evidence for immediately creating C2 Anger/Growth Mindset pages: **insufficient**

## What not to conclude

Do not infer from this small snapshot that:

- RSE has zero visibility across all search engines,
- ChatGPT/Gemini/Perplexity never surface RSE,
- the production deployment is definitely stale,
- a new content page is required for every zero-result query.

The next useful comparison is after search engines have had a chance to recrawl the Phase B/C1 canonical pages, using the same benchmark queries plus provider-specific AI eval runs.

## Next checks

1. Re-run the same public-search queries without changing their wording.
2. Check whether C1 guide URLs begin surfacing.
3. Check whether retired PWA/SaaS/Paddle snippets disappear after recrawl.
4. Run the full 20-prompt benchmark against at least two AI providers/models when possible.
5. Use Search Console / Bing data when those systems are connected or exported; do not substitute estimates.
