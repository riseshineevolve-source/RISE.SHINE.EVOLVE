# SEO URL map and phased implementation plan

## URL map (books)
- `/library/world-02/` → `bookType: level-up-brain-world02`
- `/library/world-01/` → `bookType: level-up-brain`
- `/library/confident-adventure/` → `bookType: confident-adventure`
- `/library/christmas-book/` → `bookType: christmas-book`
- `/library/grandma-book/` → `bookType: grandma-book`

## URL map (gifts)
- `/gifts/family-motto/` → `gift key: familyMotto`
- `/gifts/calm-energy/` → `gift key: calmEnergy`
- `/gifts/word-search/` → `gift key: wordSearch`
- `/gifts/word-search-studio/` → `gift key: wordSearchPro`

## Stage 1 quick wins (implemented)
- one clear H1 per new landing page
- teenagers/adults hubs expanded with meaningful starter content (indexable)
- dedicated hubs: `/kids/`, `/library/`, `/gifts/`
- sitemap and robots baseline

## Stage 2 landing pages (implemented)
- dedicated SEO pages for all books and gifts listed above
- internal links between hubs and resources


## Current progress status
- ✅ URL map prepared (books + gifts)
- ✅ Quick wins implemented (dedicated hubs + base indexing rules)
- ✅ Dedicated landing pages implemented for books and gifts
- ✅ Technical SEO baseline implemented (`robots.txt`, `sitemap.xml`, canonical/OG/Twitter, JSON-LD)
- ✅ Internal linking strengthened (cross-links + breadcrumbs + homepage static links)
- ✅ HTML site map added at `/site-map/` and linked from hubs
- ✅ Production absolute URL normalization completed for canonical/OG/hreflang/JSON-LD/feed/sitemap/robots

- ✅ Teenagers and Adults hubs expanded and switched to `index,follow`
- ✅ Structured data expanded: ItemList on hubs and FAQPage on Teenagers/Adults
- ✅ BreadcrumbList JSON-LD added across hubs and resource landing pages
- ✅ Added hreflang self/x-default tags across SEO pages and WebSite JSON-LD on homepage
- ✅ Added RSS feed (`/feed.xml`) and linked it from SEO pages + sitemap
- ✅ Social metadata expanded with `og:site_name`, `twitter:title`, and `twitter:description`
- ✅ JSON-LD normalized with `inLanguage` and `isPartOf` relations across SEO pages
- ✅ Entity consistency improved: `author` meta + JSON-LD `publisher` on SEO pages

- ✅ Social preview image metadata added (`og:image`, `twitter:image`, `summary_large_image`) across SEO pages

- ✅ JSON-LD publisher normalized with Organization `@id` and root Organization entity on homepage

- ✅ Social image accessibility metadata added (`og:image:alt`, `twitter:image:alt`) across SEO pages

- ✅ Open Graph image dimensions/type added (`og:image:width`, `og:image:height`, `og:image:type`) across SEO pages

- ✅ Added explicit `WebPage` JSON-LD (+ `primaryImageOfPage`) for hubs/landing pages and `SearchAction` on homepage `WebSite`

- ✅ `sitemap.xml` enriched with image sitemap entries (`image:image`) for richer discovery signals

- ✅ `sitemap.xml` enriched with `xhtml:link` hreflang alternates (`en`, `x-default`) for each URL

- ✅ `feed.xml` upgraded with Atom self-link, channel image, editor metadata and categorized permalink items

- ✅ Advanced crawl directives added on all SEO pages (`robots` + `googlebot` with large preview/snippet policies)

- ✅ `WebPage` JSON-LD enriched with `datePublished` and `dateModified` on hubs/landing pages

- ✅ Added global metadata consistency for locale/device parsing (`og:locale=en_US`, `format-detection=telephone=no`) across SEO pages

- ✅ Added baseline client metadata across SEO pages (`theme-color`, `color-scheme`, strict `referrer` policy)

- ✅ Social metadata expanded with `og:image:secure_url`, `twitter:site`, and `twitter:creator` across SEO pages

- ✅ Added explicit freshness metadata across SEO pages (`og:updated_time`, `last-modified`)

- ✅ Added cross-device app metadata consistency (`application-name`, Apple web-app tags) across SEO pages

- ✅ JSON-LD entities linked to page nodes using `mainEntityOfPage` across hubs and resource landing pages

- ✅ WebPage schemas enhanced with `ReadAction` + `isAccessibleForFree`, and homepage WebPage entity added

- ✅ Added automated SEO validation script (`npm run seo:validate`) covering metadata presence + sitemap/feed/robots sanity checks

## Stage completion
- ✅ SEO rollout stage completed: metadata, structured data, crawl assets, and validation automation are now in place

- ✅ Validation automation upgraded to strict schema checks (canonical↔og/hreflang parity, WebPage graph integrity, `mainEntityOfPage` consistency)

- ✅ CI quality gate added: GitHub Actions workflow runs `npm run seo:validate:strict` on push/PR

- ✅ Added SEO inventory audit (`npm run seo:audit`) to verify URL map ↔ files ↔ sitemap/feed consistency

- ✅ Added unified SEO pipeline (`npm run seo:all`) with machine-readable report artifact (`reports/seo-status.json`) and CI schedule/manual trigger

- ✅ Finalized SEO tooling with centralized config (`scripts/seo-config.json`) used by validator and audit scripts
