# Native Search Console check — owner worksheet

Use the free, native Search Console UI for the `sc-domain:rise-shine-evolve-learning-hub.com` property. This worksheet has **no fresh GSC results**. GSC Wizard returned `payment_required` on 2026-09-24 and must not be reactivated for this task.

## Before inspecting

1. Confirm the homepage, `/site-map/`, and `/sitemap.xml` match the approved source after deployment. The 2026-09-29 source audit marks these three routes **delivery pending**.
2. Open [Search Console URL Inspection](https://support.google.com/webmasters/answer/9012289?hl=en) for the correct property. Inspect each full URL below. Record the **indexed version** first; a live test only checks whether Google can access a page now and cannot predict Google's selected canonical.

| URL | Indexed? / reason | Last crawl | Crawl/index allowed? | Google-selected canonical | Live test | Request indexing sent? / date |
| --- | --- | --- | --- | --- | --- | --- |
| `https://rise-shine-evolve-learning-hub.com/adventure-app/` | | | | | | |
| `https://rise-shine-evolve-learning-hub.com/unstoppable-app/` | | | | | | |
| `https://rise-shine-evolve-learning-hub.com/seniors/` | | | | | | |
| `https://rise-shine-evolve-learning-hub.com/guides/big-feelings/` | | | | | | |
| `https://rise-shine-evolve-learning-hub.com/guides/confidence-for-kids/` | | | | | | |
| `https://rise-shine-evolve-learning-hub.com/guides/after-school-crash/` | | | | | | |
| `https://rise-shine-evolve-learning-hub.com/guides/screen-balance/` | | | | | | |

For a page that is missing or has an old crawl, use **Test Live URL**. If it is indexable and current, use **Request Indexing** where appropriate; record the action rather than assuming it succeeded. Google says requests have quotas and do not guarantee indexing. Do not request indexing for a URL the live test considers non-indexable; investigate its reason first.

## Sitemap and follow-up

- In the [Sitemaps report](https://support.google.com/webmasters/answer/7451001?hl=en), check the submitted `https://rise-shine-evolve-learning-hub.com/sitemap.xml`: last submission/read, fetch status, errors, warnings, and discovered URLs. Record any resubmission only if needed; the sitemap was previously accepted.
- Compare new observations with the last durable issue #584 state: 4/4 C1 guides indexed, 7/10 tracked URLs indexed, both apps crawled but not indexed on old June/July crawls, Seniors unresolved. These are historical baselines, not current verdicts.
- Add dated results to [issue #584](https://github.com/riseshineevolve-source/RISE.SHINE.EVOLVE/issues/584). Repeat the saved public-search queries after recrawl. Keep C2 Anger/Growth Mindset pages gated until fresh evidence shows a specific remaining intent gap and the owner authorizes them.
