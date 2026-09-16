# RSE AI Discovery & Commerce V1 — Implementation Brief V2

**Repository:** `riseshineevolve-source/RISE.SHINE.EVOLVE`  
**Branch:** `ai-discovery/v1-foundation-2026-09-16`  
**Issue:** #574  
**Date:** 2026-09-16

## 1. Goal

Build a durable discovery layer so major search/AI systems can determine, without guessing:

- what Rise.Shine.Evolve. is,
- what each product is,
- who it is for,
- which real problem/use case it addresses,
- which canonical RSE URL describes it,
- where it can actually be obtained,
- which facts are current and verified.

The architecture uses **one canonical RSE product/entity truth layer** and generates or validates platform-specific outputs from it.

## 2. Closed decisions — do not rediscover

- Apps are moving to **Android / Google Play**.
- Public PWA/SaaS/Paddle/12-month-browser-access positioning has already been removed from the website.
- App pages use **Coming Soon on Google Play** until real store listings exist.
- `SENIORS` already exists after `ADULTS` and `/seniors/` is already present.
- Existing SEO validation/Lighthouse workflow is active and green.
- Books currently use Amazon for purchase; RSE is primarily the authoritative product/content page for those books.
- Do not invent price, stock, ISBN/GTIN/ASIN, review, rating, launch date, Google Play URL, scientific claim or medical claim.
- Do not change model-training crawler policy without owner approval.
- Do not add direct commerce architecture in this project.

## 3. Current platform model

### OpenAI / ChatGPT

Treat search discovery separately from commerce eligibility.

Current OpenAI product-feed implementations must follow the **current official specification at implementation time**, not a frozen historical field list. The canonical RSE catalog is the source of truth; OpenAI export is an adapter.

A product may be:

- `searchEntityReady`: RSE has a crawlable canonical page with coherent product facts.
- `openaiFeedReady`: RSE has verified merchant/feed rights plus every required current feed field.

Do not submit a live feed for Amazon-fulfilled books or Google-Play-distributed apps until seller/merchant eligibility and required current fields are verified.

### Google / Gemini / AI Mode

Do not create a separate Gemini site or AI-only pages. Use normal Search fundamentals: crawlability, canonical URLs, useful visible content, internal linking, structured data and Search Console.

### Bing / Copilot

Use sitemap + Bing Webmaster Tools + IndexNow. Bing AI Performance is the measurement surface for cited pages and grounding queries when data becomes available.

### Claude

Search retrieval (`Claude-SearchBot`, `Claude-User`) and training (`ClaudeBot`) are separate policy decisions. Preserve current owner policy for training access.

### Perplexity

Treat merchant integration as a later adapter. Do not submit incomplete or fabricated commerce data.

## 4. Architecture

### Canonical truth layer

- `data/rse-product-catalog.json`
- `data/rse-entity-registry.json`

### Validation / generated outputs

- `scripts/validate-ai-discovery.mjs`
- later: `scripts/generate-openai-product-feed.mjs`
- later: `scripts/indexnow-submit.mjs`
- later: `reports/ai-discovery/*`

Do not maintain manually duplicated product truth per AI platform.

## 5. Phase A — foundation (this PR)

1. Create canonical product catalog.
2. Create entity registry.
3. Record lifecycle, canonical URL, merchant model and verified/null commerce fields.
4. Add machine validation for:
   - unique product IDs,
   - unique canonical product URLs,
   - entity ID uniqueness,
   - valid lifecycle values,
   - no `coming_soon` app marked as in stock,
   - no fake placeholder price/availability,
   - Google Play app records have no invented store URL,
   - merchant truth is explicit.
5. Add both app pages to the SEO inventory so existing CI audits them.
6. Commit current-state audit and exact Phase B plan.

## 6. Phase B — discovery plumbing

After Phase A validation is green:

1. Ensure `/adventure-app/` and `/unstoppable-app/` are in `sitemap.xml`.
2. Add truthful `SoftwareApplication` / `MobileApplication` JSON-LD to both app pages:
   - Android,
   - coming soon,
   - no fake `Offer`, price or store URL.
3. Review book JSON-LD. Remove hard-coded Amazon `InStock` when stock is not owned/verified by RSE.
4. Resolve canonical product-name drift, starting with `24 Gentle Steps to Christmas` vs `Christmas Family Book`.
5. Audit CDN/firewall rules in addition to `robots.txt` so search crawlers are not blocked outside robots.
6. Prepare IndexNow implementation without committing a real key/secret.
7. Extend CI to validate AI-discovery truth alongside existing SEO checks.

## 7. Phase C — first intent graph

Do **not** create 10–12 pages immediately. Start with 4–6 high-value human-useful pages:

1. big feelings in children,
2. confidence / self-esteem,
3. anger tools,
4. after-school regulation,
5. growth mindset,
6. screen balance.

Each page must answer the human problem first and connect naturally to verified RSE products. No mass AI-generated SEO pages.

## 8. Phase D — commerce adapters

Only after product truth and eligibility are verified:

- OpenAI feed generator + readiness report + validator,
- optional Google-compatible/OpenAI-compatible export as supported by current docs,
- merchant/feed application steps,
- Perplexity eligibility evaluation.

No live feed submission in this foundation PR.

## 9. Phase E — measurement

Start with a small, high-quality eval set and expand after baseline:

- first 20 consumer prompts,
- later expand toward 40,
- measure RSE cited yes/no,
- correct product,
- correct canonical URL,
- correct merchant/platform,
- hallucinated facts,
- stale PWA/Paddle wording.

Use Search Console and Bing AI Performance to decide which content gaps deserve expansion.

## 10. Files agents may not change without owner approval

- brand name / visual identity,
- Happy Makers universe,
- locked product titles unless correcting documented drift,
- book content,
- app mechanics,
- pricing,
- Amazon strategy,
- Google Play strategy,
- refunds/legal/privacy,
- model-training crawler policy,
- direct-commerce architecture,
- unrelated app repositories,
- deployment environment.

## 11. Definition of Done for foundation PR

- V2 brief committed,
- current audit committed,
- product catalog committed,
- entity registry committed,
- AI-discovery validator committed and runnable,
- both app pages included in SEO inventory,
- no fabricated commerce data,
- existing SEO workflow remains green,
- Draft PR opened,
- no production deploy/merge without review.
