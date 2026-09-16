# AI Discovery V1 - Phase C1 Intent Pages

Date: 2026-09-16
Issue: #578
Branch: `ai-discovery/v1-phase-c1-intent-pages-2026-09-16`

## Purpose

Phase C1 is the first controlled people-first intent layer built on top of the canonical RSE product and entity truth layer.

It is deliberately small. The goal is to establish a clean baseline for search and AI discovery before creating more intent pages.

## Source of truth

All product naming, URLs, status and platform facts must come from:

- `data/rse-product-catalog.json`
- `data/rse-entity-registry.json`

Do not infer missing prices, ratings, availability, launch dates, Google Play URLs, ISBNs, ASINs or merchant data.

## C1 routes and mappings

| Intent route | Primary mapping | Secondary / future mapping |
| --- | --- | --- |
| `/guides/big-feelings/` | `Level Up Your Brain - World 01` | `The Confident, Mindful & Happy Me Adventure`; Confident Adventure Android app only as `coming soon` |
| `/guides/confidence-for-kids/` | `The Confident, Mindful & Happy Me Adventure` | `Level Up Your Brain - World 01`; Confident Adventure Android app only as `coming soon` |
| `/guides/after-school-crash/` | `Level Up Your Brain - World 01` | factual anchor: existing level `The After-School Crash` |
| `/guides/screen-balance/` | `Level Up Your Brain - World 02` | `Project Unstoppable App` only as `coming soon` |

## Content design

The pages must remain materially distinct and useful without requiring a purchase.

- Big Feelings: `pause -> connect -> name -> choose`
- Confidence: small brave actions, specific feedback, evidence bank, practice loop
- After-School Crash: low-demand arrival, basics check, decompression menu, later conversation
- Screen Balance: pre-agreed ending, reliable warning, clear next activity, repeatable transition rhythm

The pages are educational family guides. They must not present RSE products as therapy, medical treatment or clinical care, and must not make guaranteed outcome claims.

## Discovery plumbing

C1 pages must remain present in:

- `scripts/seo-config.json`
- `sitemap.xml`
- `site-map/index.html`

`scripts/validate-ai-discovery.mjs` is the guardrail that ties each guide back to the canonical product records and prevents retired PWA/Paddle/SaaS language or invented commerce data from reappearing.

## C2 hold

Do not add the planned Anger or Growth Mindset intent pages yet.

C2 should be considered only after the C1 baseline can be evaluated using available Search Console, Bing/AI discovery signals and AI evaluation prompts. The goal is to expand from evidence, not create a large SEO landing-page farm.

## Explicitly out of scope for C1

- live OpenAI Commerce feed submission
- direct checkout
- IndexNow activation or key configuration
- crawler-training policy changes
- app repository changes
- new Google Play URLs before listings exist
- fabricated Amazon stock
- new prices or ratings
- legal/privacy/refund changes
- Anger / Growth Mindset guide pages

## Definition of done

C1 is complete only when:

1. the four guide pages are live in the branch and materially distinct,
2. canonical product names and links match the truth layer,
3. SEO inventory, XML sitemap and HTML site map include all four routes,
4. guide-specific AI Discovery validation passes,
5. the full SEO pipeline passes,
6. Lighthouse passes,
7. final review confirms no fabricated product, commerce or clinical claims,
8. the PR is merged into `main` and the post-merge workflow remains green.
