# RSE AI Discovery — Phase 0 Current-State Audit

**Audit date:** 2026-09-16  
**Repository:** `riseshineevolve-source/RISE.SHINE.EVOLVE`  
**Baseline:** `main` after PR #573  
**Implementation issue:** #574

## Executive result

The previous PWA/Paddle cleanup is no longer a blocker. `main` now positions both future apps as Google Play / Coming Soon. The next blocker is **product/entity truth consistency and discovery coverage**.

## Verified strengths

- Static HTML-first site with crawlable audience/product/resource landing pages.
- Canonical URLs, Open Graph, Twitter metadata and JSON-LD already exist across the main SEO landing-page set.
- Existing `robots.txt` is permissive:
  - `User-agent: *`
  - `Allow: /`
  - sitemap declared.
- Existing sitemap includes the major hubs, library pages, gifts and Seniors.
- Existing SEO scripts and GitHub Actions validation/Lighthouse pipeline are operational.
- Adventure App public page now says **Coming Soon on Google Play** and no longer exposes the retired PWA purchase model.
- Seniors page is already present.

## Findings requiring implementation

### F1 — app pages are outside the centralized SEO inventory

`scripts/seo-config.json` currently inventories hubs/books/gifts but does not include:

- `adventure-app/index.html` / `/adventure-app/`
- `unstoppable-app/index.html` / `/unstoppable-app/`

**Risk:** SEO CI can be green while app pages are not covered by the same metadata/audit inventory.

**Action:** add both pages/paths during Phase A.

### F2 — app pages are not currently represented in sitemap discovery

Current sitemap inspection did not find `/adventure-app/` or `/unstoppable-app/`.

**Action:** add canonical app URLs in Phase B after confirming metadata/schema.

### F3 — app pages lack app-specific JSON-LD

The Adventure App page has canonical/meta copy but no `SoftwareApplication` / `MobileApplication` structured-data entity.

**Action:** add truthful Android application schema in Phase B. Do not invent Google Play URL, price, rating or offer.

### F4 — Amazon stock truth is overclaimed in book JSON-LD

World 01 and World 02 currently use `Book` JSON-LD with an Amazon URL and hard-coded `availability: https://schema.org/InStock`.

RSE does not own Amazon inventory truth in this repository.

**Action:** review/remove unverifiable availability/Offer semantics or replace only when a verified source exists.

### F5 — product naming drift exists

Homepage presents **24 Gentle Steps to Christmas** while `/library/christmas-book/` uses **Christmas Family Book** in title/H1/Book schema.

**Action:** canonical catalog should use `24 Gentle Steps to Christmas`; visible/schema alignment should be corrected in Phase B after owner-approved canonical naming is confirmed.

### F6 — old SEO documentation contains domain drift

`docs/url-map-seo-plan.md` includes release checklist references to `https://rise-shine-evolve.com`, while the current production/canonical domain is `https://rise-shine-evolve-learning-hub.com`.

**Action:** correct the operational checklist in Phase B so agents do not follow stale deployment/indexing instructions.

### F7 — deployment command does not represent static-site deployment

`package.json` defines `npm run deploy` as:

`wrangler deploy ./cloudflare-worker.js --config ./wrangler.toml`

This deploys the worker, not necessarily the full static website.

**Action:** do not use `npm run deploy` as a generic website deployment command. Preserve the repository's actual Git/hosting integration unless separately verified.

### F8 — OpenAI feed architecture in the older brief is stale

The earlier 9-field feed assumption is not sufficient as a permanent contract. Current OpenAI commerce documentation contains additional required flags/merchant/market fields and also supports a Google-compatible file-upload path.

**Action:** canonical RSE data first; OpenAI export generated later against the current official specification. No live submission in this phase.

## Crawler status

### robots.txt

Current wildcard policy allows search crawlers by default.

Do not add redundant per-bot `Allow` rules merely for decoration. Instead, Phase B should also verify CDN/firewall behavior for:

- OAI-SearchBot / ChatGPT user retrieval,
- Googlebot,
- Bingbot,
- Claude-SearchBot,
- Claude-User.

Do not change training-crawler policy (`GPTBot`, `ClaudeBot`, Google-Extended or equivalents) without owner approval.

## Canonical product inventory for foundation

1. Level Up Your Brain - World 01 — book — Amazon purchase model.
2. Level Up Your Brain - World 02 — book — Amazon purchase model.
3. The Confident, Mindful & Happy Me Adventure — book — Amazon purchase model.
4. 24 Gentle Steps to Christmas — book — Amazon purchase model / exact product offer details still need verification.
5. Grandma Bibi Anti-Boredom Club — book/project — availability/merchant details not verified in this audit.
6. The Confident, Mindful & Happy Me Adventure App — Android app — coming soon on Google Play; store URL/price unknown.
7. Project Unstoppable App — Android app — coming soon on Google Play; store URL/price unknown.

Future Seniors product remains an audience area until an actual product is defined.

## Phase A file-level plan

Create:

- `data/rse-product-catalog.json`
- `data/rse-entity-registry.json`
- `scripts/validate-ai-discovery.mjs`

Modify:

- `scripts/seo-config.json`
- `package.json`

Then run through GitHub Actions/Node:

- existing SEO pipeline,
- AI-discovery validation.

## Phase B file-level plan

Review/modify:

- `adventure-app/index.html`
- `unstoppable-app/index.html`
- `sitemap.xml`
- `library/world-01/index.html`
- `library/world-02/index.html`
- `library/christmas-book/index.html`
- `docs/url-map-seo-plan.md`
- SEO validation scripts/workflow as necessary.

Create only if supported by hosting reality:

- `scripts/indexnow-submit.mjs`
- generated/readiness report files under `reports/ai-discovery/`.

## Stop conditions

Stop and report instead of guessing if implementation requires:

- unknown ISBN/GTIN/ASIN,
- current Amazon price/stock,
- Google Play URL or app price,
- merchant/feed eligibility claims,
- training-crawler policy,
- legal/refund/privacy changes,
- hosting/deployment changes.
