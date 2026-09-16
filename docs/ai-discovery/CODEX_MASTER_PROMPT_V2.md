# Codex Master Prompt V2 — RSE AI Discovery

Use this only after the foundation branch is green and the current branch is checked out.

```text
You are the RSE Orchestrator for Rise.Shine.Evolve.

REPOSITORY:
riseshineevolve-source/RISE.SHINE.EVOLVE

WORK ONLY ON BRANCH:
ai-discovery/v1-foundation-2026-09-16

FIRST READ:
- ~/.codex/rse/AGENT_CATALOG.md
- docs/ai-discovery/IMPLEMENTATION_BRIEF_V2.md
- docs/ai-discovery/PHASE_0_AUDIT.md
- data/rse-product-catalog.json
- data/rse-entity-registry.json
- issue #574 context if available

DO NOT REDISCOVER OR REDO CLOSED WORK:
- PWA/SaaS/Paddle public app positioning has already been removed.
- Apps are Coming Soon on Google Play.
- Seniors already exists after Adults.
- The canonical product/entity truth layer already exists on this branch.

ROUTING:
Use CORE-first routing and the smallest specialist squad needed. Suggested leads:
- RSE Orchestrator
- Software Architect
- SEO/GEO specialist
- Product Manager
- Reality Checker / QA
Add structured-data/frontend specialists only where needed.

TASK:
Continue Phase B discovery plumbing, using repository reality as the source of truth.

1. APP DISCOVERY
Upgrade:
- adventure-app/index.html
- unstoppable-app/index.html

Make each page pass the existing centralized SEO validation requirements and add truthful app structured data.

Requirements:
- canonical production URL
- title/meta/OG/Twitter/hreflang consistent with visible content
- WebPage JSON-LD
- SoftwareApplication or MobileApplication JSON-LD as semantically appropriate
- operatingSystem Android
- applicationCategory only if factually supportable
- mainEntityOfPage linked correctly
- no fake Offer
- no price
- no rating/review
- no Google Play URL until it exists
- status remains Coming Soon

After the pages satisfy the normal SEO gate, move them from staged AI-discovery-only inventory into the normal SEO inventory.

2. SITEMAP
Add canonical URLs:
- https://rise-shine-evolve-learning-hub.com/adventure-app/
- https://rise-shine-evolve-learning-hub.com/unstoppable-app/

Use truthful lastmod for this change.
Keep XML/hreflang/image structure consistent with the existing sitemap.

3. BOOK COMMERCE TRUTH
Review:
- library/world-01/index.html
- library/world-02/index.html

RSE currently hard-codes Amazon Offer availability as InStock.
Do not claim Amazon stock unless the repository has a verified, maintained source.
Prefer removing unverifiable availability/Offer semantics rather than inventing replacement facts.
Preserve Amazon outbound links.

4. CHRISTMAS ENTITY ALIGNMENT
The canonical catalog says:
24 Gentle Steps to Christmas

Current landing page still uses Christmas Family Book.
Align title/H1/Book schema/OG/Twitter/breadcrumb-visible naming to the canonical product name while preserving the page URL and useful content.
Do not change book content.

5. DOCUMENTATION DOMAIN DRIFT
Update stale operational references in docs/url-map-seo-plan.md from rise-shine-evolve.com to the real canonical production domain:
https://rise-shine-evolve-learning-hub.com
Do not change unrelated historical notes.

6. INDEXNOW PREPARATION
Implement scripts/indexnow-submit.mjs only if it can be done without embedding a real key/secret.
The script must:
- accept URLs explicitly,
- submit only production-domain URLs,
- avoid repeated unchanged submission by design/documentation,
- require key/keyLocation from environment or documented config,
- not run automatically in CI until owner credentials/setup exist.

7. VALIDATION
Run:
- npm run seo:all
- npm run ai:validate
- any focused structured-data/static checks you add

Do not weaken existing checks just to make them green.

8. OPENAI COMMERCE
Do NOT build or submit a live product feed in this phase.
The older 9-field assumption is obsolete.
Any future generator must target the current official OpenAI commerce specification at implementation time and remain gated by data/eligibility truth.

9. SAFETY
Do not change:
- app repositories
- direct commerce architecture
- legal/refund/privacy text unless strictly required and owner-approved
- training crawler policy
- visual identity
- book content
- pricing
- Amazon strategy
- Google Play strategy
- deployment environment

10. DELIVERY
Work in reviewable commits.
Do not merge or deploy automatically.
At the end report:
- agents used
- files changed
- tests run
- exact remaining blockers
- sitemap status
- structured-data status
- crawler status
- IndexNow setup steps requiring owner access
- rollback instructions

Do not expand scope beyond Phase B.
```
