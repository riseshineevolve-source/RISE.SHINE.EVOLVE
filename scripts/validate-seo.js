#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

const ROOT = process.cwd();
const cfg = require('./seo-config.json');
const BASE = cfg.baseUrl;
const pages = cfg.pages;

let failed = false;
let checks = 0;

function fail(msg){ console.error('✖', msg); failed = true; }
function ok(msg){ console.log('✔', msg); }
function assert(cond, msg){ checks += 1; if (!cond) fail(msg); }
function read(rel){ return fs.readFileSync(path.join(ROOT, rel), 'utf8'); }

function extractSingle(re, txt){ const m = txt.match(re); return m ? m[1] : null; }
function allMatches(re, txt){ return [...txt.matchAll(re)].map(m => m[1]); }

function parseJsonLdBlocks(txt, rel){
  const blocks = [...txt.matchAll(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/g)];
  const parsed = [];
  for (const b of blocks) {
    try { parsed.push(JSON.parse(b[1])); }
    catch { fail(`${rel}: invalid JSON-LD block`); }
  }
  return parsed;
}

// -------- Page-level checks --------
const canonicalSet = new Set();
for (const rel of pages) {
  const fp = path.join(ROOT, rel);
  assert(fs.existsSync(fp), `Missing page: ${rel}`);
  if (!fs.existsSync(fp)) continue;

  const txt = read(rel);
  const canonical = extractSingle(/<link rel="canonical" href="([^"]+)"/i, txt);
  const ogUrl = extractSingle(/<meta property="og:url" content="([^"]+)"/i, txt);
  const hreflangEn = extractSingle(/<link rel="alternate" hreflang="en" href="([^"]+)"/i, txt);
  const hreflangXDefault = extractSingle(/<link rel="alternate" hreflang="x-default" href="([^"]+)"/i, txt);

  assert(!!canonical, `${rel}: missing canonical`);
  assert(!!ogUrl, `${rel}: missing og:url`);
  assert(!!hreflangEn, `${rel}: missing hreflang en`);
  assert(!!hreflangXDefault, `${rel}: missing hreflang x-default`);

  if (canonical) {
    canonicalSet.add(canonical);
    assert(canonical.startsWith(BASE), `${rel}: canonical not absolute or wrong domain`);
    if (ogUrl) assert(ogUrl === canonical, `${rel}: og:url differs from canonical`);
    if (hreflangEn) assert(hreflangEn === canonical, `${rel}: hreflang en differs from canonical`);
    if (hreflangXDefault) assert(hreflangXDefault === canonical, `${rel}: hreflang x-default differs from canonical`);
  }

  const robots = 'index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1';
  assert(txt.includes(`meta name="robots" content="${robots}"`), `${rel}: missing/invalid robots directive`);
  assert(txt.includes(`meta name="googlebot" content="${robots}"`), `${rel}: missing/invalid googlebot directive`);
  assert(txt.includes('property="og:locale" content="en_US"'), `${rel}: missing og:locale`);
  assert(txt.includes('property="og:image:secure_url" content="https://rise-shine-evolve-learning-hub.com/assets/images/pp.png"'), `${rel}: missing og:image:secure_url`);
  assert(txt.includes('name="twitter:site" content="@RiseShineEvolve"'), `${rel}: missing twitter:site`);
  assert(txt.includes('name="twitter:creator" content="@RiseShineEvolve"'), `${rel}: missing twitter:creator`);

  const ld = parseJsonLdBlocks(txt, rel);
  assert(ld.length > 0, `${rel}: no JSON-LD blocks`);

  const webPage = ld.find(x => x['@type'] === 'WebPage');
  assert(!!webPage, `${rel}: missing WebPage JSON-LD`);
  if (webPage && canonical) {
    assert(webPage.url === canonical, `${rel}: WebPage.url differs from canonical`);
    const expectedId = rel === 'index.html' ? `${BASE}/#homepage` : `${canonical}#webpage`;
    assert(webPage['@id'] === expectedId, `${rel}: WebPage.@id mismatch`);
    assert(webPage.isAccessibleForFree === true, `${rel}: WebPage.isAccessibleForFree missing/invalid`);
    assert(webPage.potentialAction && webPage.potentialAction['@type'] === 'ReadAction', `${rel}: WebPage missing ReadAction`);
    assert(Array.isArray(webPage.potentialAction?.target) && webPage.potentialAction.target[0] === canonical, `${rel}: WebPage ReadAction target mismatch`);
  }

  const entityTypes = new Set(['CollectionPage','ItemList','FAQPage','Book','CreativeWork','Game','SoftwareApplication']);
  for (const obj of ld) {
    if (entityTypes.has(obj['@type']) && canonical) {
      assert(!!obj.mainEntityOfPage && !!obj.mainEntityOfPage['@id'], `${rel}: ${obj['@type']} missing mainEntityOfPage.@id`);
      if (obj.mainEntityOfPage?.['@id']) {
        assert(obj.mainEntityOfPage['@id'] === `${canonical}#webpage`, `${rel}: ${obj['@type']} mainEntityOfPage points to wrong webpage id`);
      }
    }
  }
}

// -------- XML and crawl checks --------
for (const xmlFile of ['sitemap.xml','feed.xml']) {
  const fp = path.join(ROOT, xmlFile);
  assert(fs.existsSync(fp), `Missing ${xmlFile}`);
  if (!fs.existsSync(fp)) continue;
  const txt = read(xmlFile).trim();
  assert(txt.startsWith('<?xml'), `${xmlFile}: missing XML declaration`);
  ok(`${xmlFile}: XML declaration present`);
}

const robotsPath = path.join(ROOT, 'robots.txt');
assert(fs.existsSync(robotsPath), 'Missing robots.txt');
if (fs.existsSync(robotsPath)) {
  const robotsTxt = read('robots.txt');
  assert(robotsTxt.includes(`Sitemap: ${BASE}/sitemap.xml`), 'robots.txt missing absolute sitemap directive');
  ok('robots.txt sitemap directive present');
}

// -------- Cross-file consistency checks --------
if (fs.existsSync(path.join(ROOT,'sitemap.xml'))) {
  const sm = read('sitemap.xml');
  const locs = allMatches(/<loc>([^<]+)<\/loc>/g, sm);
  const sitemapPageLocs = locs.filter(u => /\/$/.test(u));
  assert(sitemapPageLocs.length >= pages.length, 'sitemap.xml: too few page loc entries');
  for (const c of canonicalSet) {
    assert(sitemapPageLocs.includes(c), `sitemap.xml: missing canonical URL ${c}`);
  }
  ok('sitemap.xml canonical coverage checked');
}

if (fs.existsSync(path.join(ROOT,'feed.xml'))) {
  const fd = read('feed.xml');
  const itemLinks = allMatches(/<item>[\s\S]*?<link>([^<]+)<\/link>[\s\S]*?<\/item>/g, fd);
  assert(itemLinks.length > 0, 'feed.xml: no item links found');
  for (const link of itemLinks) {
    assert(canonicalSet.has(link), `feed.xml: item link not matching known canonical page (${link})`);
  }
  ok('feed.xml item links mapped to canonical pages');
}

if (failed) {
  console.error(`\nSEO validation failed (${checks} checks).`);
  process.exit(1);
}
ok(`SEO validation checks passed (${checks} checks).`);
