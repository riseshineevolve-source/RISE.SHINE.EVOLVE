#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

const ROOT = process.cwd();
const cfg = require('./seo-config.json');
const BASE = cfg.baseUrl;
const expectedPaths = cfg.expectedPaths;

const expectedFiles = expectedPaths
  .filter(p => p.endsWith('/'))
  .map(p => p === '/' ? 'index.html' : `${p.slice(1)}index.html`)
  .concat(['sitemap.xml','feed.xml','robots.txt']);

let failed = false;
let checks = 0;
const fail = (m)=>{ console.error('✖', m); failed = true; };
const ok = (m)=>console.log('✔', m);
const assert = (c,m)=>{ checks += 1; if(!c) fail(m); };

const read = (f) => fs.readFileSync(path.join(ROOT,f),'utf8');

// 1) file existence
for (const f of expectedFiles) {
  assert(fs.existsSync(path.join(ROOT,f)), `Missing expected file: ${f}`);
}
ok('Expected file set checked');

// 2) sitemap coverage
const sitemap = read('sitemap.xml');
const sitemapLocs = [...sitemap.matchAll(/<loc>([^<]+)<\/loc>/g)].map(m=>m[1]);
for (const p of expectedPaths) {
  const abs = `${BASE}${p}`;
  assert(sitemapLocs.includes(abs), `sitemap.xml missing expected URL: ${abs}`);
}
ok('sitemap expected URL coverage checked');

// 3) canonical consistency for expected HTML pages
for (const f of expectedFiles.filter(x=>x.endsWith('.html'))) {
  const txt = read(f);
  const m = txt.match(/<link rel="canonical" href="([^"]+)"/i);
  assert(!!m, `${f}: missing canonical`);
  if (!m) continue;

  let expected;
  if (f === 'index.html') expected = `${BASE}/`;
  else expected = `${BASE}/${f.replace(/index\.html$/,'')}`;
  assert(m[1] === expected, `${f}: canonical mismatch (expected ${expected}, got ${m[1]})`);
}
ok('Canonical URL parity checked');

// 4) feed links must be known expected URLs
const feed = read('feed.xml');
const itemLinks = [...feed.matchAll(/<item>[\s\S]*?<link>([^<]+)<\/link>[\s\S]*?<\/item>/g)].map(m=>m[1]);
assert(itemLinks.length > 0, 'feed.xml has no item links');
for (const link of itemLinks) {
  assert(expectedPaths.map(p=>`${BASE}${p}`).includes(link), `feed.xml has unknown link: ${link}`);
}
ok('Feed links checked against expected URL inventory');

// 5) docs URL map sanity (ensure mapped URLs exist on disk)
const plan = read('docs/url-map-seo-plan.md');
const mapped = [...plan.matchAll(/`(\/[a-z0-9\-\/]+\/)`\s*→/gi)].map(m=>m[1]);
for (const p of mapped) {
  const file = p === '/' ? 'index.html' : `${p.slice(1)}index.html`;
  assert(fs.existsSync(path.join(ROOT,file)), `docs/url-map-seo-plan.md maps URL with missing file: ${p} -> ${file}`);
}
ok('docs URL map file-existence checks passed');

if (failed) {
  console.error(`\nSEO audit failed (${checks} checks).`);
  process.exit(1);
}
ok(`SEO audit passed (${checks} checks).`);
