#!/usr/bin/env node
// Deterministic source audit. No network calls or paid services.
import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';

const root = process.cwd();
const config = JSON.parse(fs.readFileSync(path.join(root, 'scripts/seo-config.json'), 'utf8'));
const base = config.baseUrl;
const trackedRoutes = [
  '/', '/adventure-app/', '/unstoppable-app/', '/seniors/',
  '/guides/big-feelings/', '/guides/confidence-for-kids/',
  '/guides/after-school-crash/', '/guides/screen-balance/'
];
const appRoutes = ['/adventure-app/', '/unstoppable-app/'];
const guideRoutes = trackedRoutes.filter((route) => route.startsWith('/guides/'));
const read = (file) => fs.readFileSync(path.join(root, file), 'utf8');
const fileFor = (route) => route === '/' ? 'index.html' : `${route.slice(1)}index.html`;
const errors = [];
const check = (condition, message) => { if (!condition) errors.push(message); };
const decode = (value) => String(value ?? '')
  .replace(/&#(x[0-9a-f]+|\d+);/gi, (_, code) => String.fromCodePoint(
    code[0].toLowerCase() === 'x' ? Number.parseInt(code.slice(1), 16) : Number(code)
  ))
  .replace(/&(amp|quot|apos|lt|gt|nbsp);/gi, (_, name) => ({
    amp: '&', quot: '"', apos: "'", lt: '<', gt: '>', nbsp: ' '
  })[name.toLowerCase()]);
const normalize = (value) => decode(value).replace(/\s+/g, ' ').trim();
const visibleText = (html) => normalize((html.match(/<body\b[^>]*>([\s\S]*?)<\/body>/i)?.[1] ?? '')
  .replace(/<(script|style|template)\b[^>]*>[\s\S]*?<\/\1>/gi, ' ')
  .replace(/<!--[^]*?-->/g, ' ')
  .replace(/<\/?(?:p|div|section|h[1-6]|li|ul|ol|br|main|nav)\b[^>]*>/gi, ' ')
  .replace(/<[^>]+>/g, ''));
const tags = (html, name) => [...html.matchAll(new RegExp(`<${name}\\b[^>]*>`, 'gi'))]
  .map(([tag]) => Object.fromEntries([...tag.matchAll(/([\w:-]+)\s*=\s*"([^"]*)"/g)]
    .map(([, key, value]) => [key.toLowerCase(), decode(value)])));
const meta = (head, key, value) => tags(head, 'meta')
  .find((tag) => tag[key] === value)?.content ?? null;
const link = (head, rel, extra = {}) => tags(head, 'link')
  .find((tag) => tag.rel === rel && Object.entries(extra).every(([key, value]) => tag[key] === value))?.href ?? null;
const jsonLd = (html, file) => [...html.matchAll(/<script\s+type="application\/ld\+json">([\s\S]*?)<\/script>/gi)]
  .map(([, raw]) => {
    try { return JSON.parse(raw); }
    catch { errors.push(`${file}: invalid JSON-LD`); return {}; }
  });
const links = (html) => new Set(tags(html, 'a').map((tag) => {
  try { return new URL(tag.href, `${base}/`).href; }
  catch { return null; }
}).filter(Boolean));

const expectedPaths = config.expectedPaths;
const expectedUrls = expectedPaths.map((route) => `${base}${route}`);
check(new Set(expectedPaths).size === expectedPaths.length, 'SEO inventory has duplicate paths');
check(new Set(config.pages).size === config.pages.length, 'SEO page inventory has duplicates');
for (const route of trackedRoutes) {
  check(config.pages.includes(fileFor(route)), `${route}: missing from SEO page inventory`);
  check(expectedPaths.includes(route), `${route}: missing from expected canonical URL inventory`);
}

const sitemap = read('sitemap.xml');
const sitemapEntries = [...sitemap.matchAll(/<url>\s*<loc>([^<]+)<\/loc>([\s\S]*?)<\/url>/g)]
  .map(([, url, body]) => ({ url, body }));
const sitemapUrls = sitemapEntries.map((entry) => entry.url);
check(new Set(sitemapUrls).size === sitemapUrls.length, 'sitemap.xml has duplicate URL entries');
for (const url of expectedUrls) check(sitemapUrls.includes(url), `sitemap.xml missing ${url}`);
for (const url of sitemapUrls) check(expectedUrls.includes(url), `sitemap.xml has unexpected URL ${url}`);
for (const entry of sitemapEntries) {
  for (const language of ['en', 'x-default']) {
    const alternate = [...entry.body.matchAll(/<xhtml:link\b[^>]*\/>/g)]
      .map(([raw]) => tags(raw, 'xhtml:link')[0])
      .find((tag) => tag?.hreflang === language);
    check(alternate?.href === entry.url, `${entry.url}: ${language} sitemap alternate differs from loc`);
  }
}

const robots = read('robots.txt');
const wildcardGroup = robots.split(/(?=^User-agent:\s*)/im)
  .find((group) => /^User-agent:\s*\*\s*$/im.test(group));
check(!!wildcardGroup, 'robots.txt missing wildcard user-agent');
check(/^Allow:\s*\/\s*$/im.test(wildcardGroup ?? ''), 'robots.txt missing wildcard Allow: /');
check(!/^Disallow:/im.test(wildcardGroup ?? ''), 'robots.txt wildcard group contains a Disallow directive');
check(robots.split(/\r?\n/).some((line) => line.trim() === `Sitemap: ${base}/sitemap.xml`),
  'robots.txt sitemap URL differs from canonical sitemap');

const retiredClaims = [
  ['PWA', /\bPWA\b/i], ['SaaS', /\bSaaS\b/i], ['Paddle', /\bPaddle\b/i],
  ['No App Store needed', /No App Store needed/i]
];
const retiredAppClaims = [
  ['web-app positioning', /\bweb[- ]apps?\b|\bweb[- ]applications?\b/i],
  ['365-day expiry', /\b365[- ]days?\b/i],
  ['12-month access', /\b12[- ]months?\b.{0,80}\b(?:access|license|pass)\b/i],
  ['1-year access pass', /\b1[- ]year\s+access\s+pass\b/i],
  ['instant access', /\binstant[- ]access\b/i],
  ['all-sales-final claim', /\ball sales are final\b/i],
  ['browser install claim', /\bInstall App\b|\binstall[^.]{0,80}\bbrowser\b/i]
];
const staleOccurrences = [];
for (const file of config.pages) {
  const html = read(file);
  for (const [label, pattern] of retiredClaims) {
    if (pattern.test(html)) staleOccurrences.push({ file, claim: label });
  }
  if (file === 'index.html' || appRoutes.some((route) => file === fileFor(route))) {
    const claimText = html.replace(/<meta\s+name="apple-mobile-web-app[^"]*"[^>]*>/gi, '');
    for (const [label, pattern] of retiredAppClaims) {
      if (pattern.test(claimText)) staleOccurrences.push({ file, claim: label });
    }
  }
  check(!/https?:\/\/schema\.org\/InStock\b/i.test(html), `${file}: unverified InStock schema claim`);
}
for (const occurrence of staleOccurrences) errors.push(`${occurrence.file}: retired ${occurrence.claim} claim`);

const pages = [];
for (const route of trackedRoutes) {
  const file = fileFor(route);
  const html = read(file);
  const head = html.match(/<head\b[^>]*>([\s\S]*?)<\/head>/i)?.[1] ?? '';
  const title = normalize(head.match(/<title>([\s\S]*?)<\/title>/i)?.[1]);
  const description = meta(head, 'name', 'description');
  const canonical = link(head, 'canonical');
  const ogTitle = meta(head, 'property', 'og:title');
  const ogDescription = meta(head, 'property', 'og:description');
  const ogUrl = meta(head, 'property', 'og:url');
  const twitterTitle = meta(head, 'name', 'twitter:title');
  const twitterDescription = meta(head, 'name', 'twitter:description');
  const robotsMeta = meta(head, 'name', 'robots');
  const schema = jsonLd(head, file);
  const webPage = schema.find((item) => item['@type'] === 'WebPage');
  const expectedCanonical = `${base}${route}`;
  const body = visibleText(html);
  check(title.length > 0 && description?.length > 0, `${file}: title or description missing`);
  check(canonical === expectedCanonical, `${file}: canonical differs from expected URL`);
  check(ogUrl === canonical, `${file}: og:url differs from canonical`);
  check(!!ogTitle && !!ogDescription && !!twitterTitle && !!twitterDescription,
    `${file}: incomplete OG/Twitter metadata`);
  check(link(head, 'alternate', { hreflang: 'en' }) === canonical, `${file}: en alternate differs from canonical`);
  check(link(head, 'alternate', { hreflang: 'x-default' }) === canonical, `${file}: x-default alternate differs from canonical`);
  check(!!robotsMeta && !/noindex|nofollow/i.test(robotsMeta), `${file}: indexing metadata blocks discovery`);
  check(webPage?.url === canonical, `${file}: WebPage URL differs from canonical`);
  check(normalize(webPage?.name) === title, `${file}: WebPage name differs from title`);
  check(normalize(webPage?.description) === normalize(description), `${file}: WebPage description differs from meta description`);

  if (appRoutes.includes(route)) {
    const app = schema.find((item) => item['@type'] === 'SoftwareApplication');
    check(app?.url === canonical && app?.operatingSystem === 'Android', `${file}: app schema URL or OS differs`);
    for (const unsupported of ['offers', 'aggregateRating', 'review', 'downloadUrl', 'installUrl', 'price', 'availability']) {
      check(app?.[unsupported] == null, `${file}: coming-soon app schema has unverified ${unsupported}`);
    }
    check(!/https?:\/\/play\.google\.com\/store\/apps\//i.test(html),
      `${file}: Google Play listing URL appeared before launch verification`);
    check(body.includes(normalize(app?.name).replace(/ App$/, '')), `${file}: app name absent from visible body`);
    check(/coming soon on google play/i.test(body) && /coming soon on google play/i.test(app?.description ?? ''),
      `${file}: visible copy and app schema do not agree on launch state`);
  }
  if (guideRoutes.includes(route)) {
    const faq = schema.find((item) => item['@type'] === 'FAQPage');
    const section = html.match(/<section\s+id="faq"[^>]*>([\s\S]*?)<\/section>/i)?.[1] ?? '';
    const faqText = visibleText(`<body>${section}</body>`).toLowerCase();
    check(Array.isArray(faq?.mainEntity) && faq.mainEntity.length > 0, `${file}: FAQ schema missing`);
    for (const question of faq?.mainEntity ?? []) {
      check(faqText.includes(normalize(question.name).toLowerCase()), `${file}: FAQ question not visible: ${question.name}`);
      check(faqText.includes(normalize(question.acceptedAnswer?.text).toLowerCase()),
        `${file}: FAQ answer not visible: ${question.name}`);
    }
  }
  pages.push({ route, title, description, canonical, ogTitle, ogDescription, ogUrl,
    twitterTitle, twitterDescription, robots: robotsMeta, schemaTypes: schema.map((item) => item['@type']),
    sourceLastModified: meta(head, 'name', 'last-modified') });
}

const homepage = read('index.html');
const homepageLinks = links(homepage);
for (const route of [...guideRoutes, ...appRoutes, '/seniors/', '/site-map/']) {
  check(homepageLinks.has(`${base}${route}`), `homepage has no crawlable link to ${route}`);
}
const homepageSchema = jsonLd(homepage, 'index.html');
check(!homepageSchema.some((item) => item['@type'] === 'WebSite' && item.potentialAction?.['@type'] === 'SearchAction'),
  'homepage advertises a SearchAction without a working site search');

const siteMap = read('site-map/index.html');
const siteMapLinks = links(siteMap);
const itemList = jsonLd(siteMap, 'site-map/index.html').find((item) => item['@type'] === 'ItemList');
const visibleList = [...siteMap.matchAll(/<li>\s*<a href="([^"]+)">([\s\S]*?)<\/a>\s*<\/li>/g)]
  .map(([, href, label]) => ({
    url: new URL(href, `${base}/`).href,
    name: normalize(label.replace(/<[^>]+>/g, ''))
  }));
const schemaList = itemList?.itemListElement ?? [];
const itemListUrls = new Set(schemaList.map((item) => item.url));
const expectedSiteMapUrls = expectedPaths.filter((route) => route !== '/' && route !== '/site-map/' && route !== '/feed.xml')
  .map((route) => `${base}${route}`);
check(visibleList.length === expectedSiteMapUrls.length, 'HTML site map does not list every canonical HTML page');
for (const url of expectedSiteMapUrls) check(siteMapLinks.has(url), `HTML site map missing ${url}`);
check(schemaList.length === visibleList.length, 'site map ItemList length differs from visible list');
for (let index = 0; index < visibleList.length; index++) {
  const item = schemaList[index];
  check(item?.position === index + 1 && item?.url === visibleList[index].url &&
    normalize(item?.name) === visibleList[index].name,
    `site map ItemList entry ${index + 1} differs from the visible list`);
}
for (const url of itemListUrls) check(siteMapLinks.has(url), `site map ItemList URL is not a visible link: ${url}`);
for (const route of [...guideRoutes, ...appRoutes, '/seniors/']) {
  check(siteMapLinks.has(`${base}${route}`), `site map has no visible link to ${route}`);
  check(itemListUrls.has(`${base}${route}`), `site map ItemList missing ${route}`);
}

const result = {
  ok: errors.length === 0,
  trackedPageCount: pages.length,
  canonicalInventoryCount: expectedUrls.length,
  sitemapUrlCount: sitemapUrls.length,
  retiredClaimOccurrences: staleOccurrences,
  pages,
  errors
};
if (process.argv.includes('--json')) console.log(JSON.stringify(result, null, 2));
else {
  console.log(`Discovery source audit: ${result.ok ? 'PASS' : 'FAIL'}; ${pages.length} tracked pages, ${sitemapUrls.length} sitemap URLs, ${staleOccurrences.length} retired claims.`);
  for (const error of errors) console.error(`ERROR: ${error}`);
}
if (!result.ok) process.exitCode = 1;
