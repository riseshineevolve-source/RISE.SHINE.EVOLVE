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
function normalizeSpace(str){ return String(str || '').replace(/\s+/g, ' ').trim(); }

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
const titleToPages = new Map();
const descriptionToPages = new Map();
for (const rel of pages) {
  const fp = path.join(ROOT, rel);
  assert(fs.existsSync(fp), `Missing page: ${rel}`);
  if (!fs.existsSync(fp)) continue;

  const txt = read(rel);
  const canonical = extractSingle(/<link rel="canonical" href="([^"]+)"/i, txt);
  const title = extractSingle(/<title>([\s\S]*?)<\/title>/i, txt);
  const metaDescription = extractSingle(/<meta name="description" content="([^"]*)"\s*\/?>/i, txt);
  const ogTitle = extractSingle(/<meta property="og:title" content="([^"]*)"\s*\/?>/i, txt);
  const ogDescription = extractSingle(/<meta property="og:description" content="([^"]*)"\s*\/?>/i, txt);
  const twitterTitle = extractSingle(/<meta name="twitter:title" content="([^"]*)"\s*\/?>/i, txt);
  const twitterDescription = extractSingle(/<meta name="twitter:description" content="([^"]*)"\s*\/?>/i, txt);
  const ogUrl = extractSingle(/<meta property="og:url" content="([^"]+)"/i, txt);
  const hreflangEn = extractSingle(/<link rel="alternate" hreflang="en" href="([^"]+)"/i, txt);
  const hreflangXDefault = extractSingle(/<link rel="alternate" hreflang="x-default" href="([^"]+)"/i, txt);

  assert(!!canonical, `${rel}: missing canonical`);
  assert(!!title, `${rel}: missing <title>`);
  assert(!!metaDescription, `${rel}: missing meta description`);
  assert(!!ogTitle, `${rel}: missing og:title`);
  assert(!!ogDescription, `${rel}: missing og:description`);
  assert(!!twitterTitle, `${rel}: missing twitter:title`);
  assert(!!twitterDescription, `${rel}: missing twitter:description`);
  assert(!!ogUrl, `${rel}: missing og:url`);
  assert(!!hreflangEn, `${rel}: missing hreflang en`);
  assert(!!hreflangXDefault, `${rel}: missing hreflang x-default`);

  if (title) {
    const normalizedTitle = normalizeSpace(title);
    assert(normalizedTitle.length >= 8, `${rel}: title too short (<8 chars)`);
    assert(normalizedTitle.length <= 80, `${rel}: title too long (>80 chars)`);
    assert(!/^(home|untitled|new page)$/i.test(normalizedTitle), `${rel}: title appears placeholder-like`);
    if (!titleToPages.has(normalizedTitle)) titleToPages.set(normalizedTitle, []);
    titleToPages.get(normalizedTitle).push(rel);
  }

  if (metaDescription) {
    const normalizedDescription = normalizeSpace(metaDescription);
    assert(normalizedDescription.length >= 35, `${rel}: meta description too short (<35 chars)`);
    assert(normalizedDescription.length <= 220, `${rel}: meta description too long (>220 chars)`);
    assert(!/(lorem ipsum|todo|tbd)/i.test(normalizedDescription), `${rel}: meta description appears placeholder-like`);
    if (!descriptionToPages.has(normalizedDescription)) descriptionToPages.set(normalizedDescription, []);
    descriptionToPages.get(normalizedDescription).push(rel);
  }

  if (ogTitle) {
    const normalizedOgTitle = normalizeSpace(ogTitle);
    assert(normalizedOgTitle.length >= 8, `${rel}: og:title too short (<8 chars)`);
    assert(normalizedOgTitle.length <= 110, `${rel}: og:title too long (>110 chars)`);
    assert(!/^(home|untitled|new page)$/i.test(normalizedOgTitle), `${rel}: og:title appears placeholder-like`);
  }

  if (ogDescription) {
    const normalizedOgDescription = normalizeSpace(ogDescription);
    assert(normalizedOgDescription.length >= 20, `${rel}: og:description too short (<20 chars)`);
    assert(normalizedOgDescription.length <= 220, `${rel}: og:description too long (>220 chars)`);
    assert(!/(lorem ipsum|todo|tbd)/i.test(normalizedOgDescription), `${rel}: og:description appears placeholder-like`);
  }

  if (twitterTitle) {
    const normalizedTwitterTitle = normalizeSpace(twitterTitle);
    assert(normalizedTwitterTitle.length >= 8, `${rel}: twitter:title too short (<8 chars)`);
    assert(normalizedTwitterTitle.length <= 110, `${rel}: twitter:title too long (>110 chars)`);
    assert(!/^(home|untitled|new page)$/i.test(normalizedTwitterTitle), `${rel}: twitter:title appears placeholder-like`);
  }

  if (twitterDescription) {
    const normalizedTwitterDescription = normalizeSpace(twitterDescription);
    assert(normalizedTwitterDescription.length >= 20, `${rel}: twitter:description too short (<20 chars)`);
    assert(normalizedTwitterDescription.length <= 220, `${rel}: twitter:description too long (>220 chars)`);
    assert(!/(lorem ipsum|todo|tbd)/i.test(normalizedTwitterDescription), `${rel}: twitter:description appears placeholder-like`);
  }

  if (title && ogTitle) {
    assert(normalizeSpace(title) === normalizeSpace(ogTitle), `${rel}: og:title differs from <title>`);
  }

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
  const ogImage = extractSingle(/<meta property="og:image" content="([^"]+)"/i, txt);
  const ogImageSecure = extractSingle(/<meta property="og:image:secure_url" content="([^"]+)"/i, txt);
  assert(!!ogImageSecure, `${rel}: missing og:image:secure_url`);
  if (ogImage && ogImageSecure) {
    assert(ogImageSecure.startsWith('https://'), `${rel}: og:image:secure_url must be https`);
    assert(ogImageSecure === ogImage, `${rel}: og:image:secure_url differs from og:image`);
  }
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

for (const [title, rels] of titleToPages.entries()) {
  assert(rels.length === 1, `Duplicate title used by ${rels.join(', ')} => "${title}"`);
}

for (const [description, rels] of descriptionToPages.entries()) {
  assert(rels.length === 1, `Duplicate meta description used by ${rels.join(', ')} => "${description}"`);
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
