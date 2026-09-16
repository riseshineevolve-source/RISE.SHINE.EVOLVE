import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';

const root = process.cwd();
const readJson = (relativePath) => JSON.parse(fs.readFileSync(path.join(root, relativePath), 'utf8'));
const readText = (relativePath) => fs.readFileSync(path.join(root, relativePath), 'utf8');

const catalog = readJson('data/rse-product-catalog.json');
const registry = readJson('data/rse-entity-registry.json');
const seoConfig = readJson('scripts/seo-config.json');

const errors = [];
const warnings = [];
const fail = (message) => errors.push(message);
const warn = (message) => warnings.push(message);

const products = Array.isArray(catalog.products) ? catalog.products : [];
const entities = Array.isArray(registry.entities) ? registry.entities : [];
const seoPages = Array.isArray(seoConfig.pages) ? seoConfig.pages : [];
const requiredAppPages = ['adventure-app/index.html', 'unstoppable-app/index.html'];

if (!products.length) fail('Product catalog must contain at least one product.');
if (!entities.length) fail('Entity registry must contain at least one entity.');

const assertUnique = (items, key, label) => {
  const seen = new Map();
  for (const item of items) {
    const value = item?.[key];
    if (!value) {
      fail(`${label} is missing ${key}.`);
      continue;
    }
    if (seen.has(value)) {
      fail(`Duplicate ${label} ${key}: ${value}`);
    } else {
      seen.set(value, true);
    }
  }
};

assertUnique(products, 'id', 'product');
assertUnique(products, 'canonicalUrl', 'product');
assertUnique(products, 'canonicalName', 'product');
assertUnique(entities, 'id', 'entity');
assertUnique(entities, 'canonicalUrl', 'entity');

const allowedProductTypes = new Set(['book', 'android_app']);
const allowedStatuses = new Set(['available', 'coming_soon', 'availability_unverified', 'retired']);

for (const product of products) {
  const prefix = product.id || product.canonicalName || 'unknown-product';

  if (product.brand !== 'Rise.Shine.Evolve.') {
    fail(`${prefix}: brand must be exactly Rise.Shine.Evolve.`);
  }

  if (!allowedProductTypes.has(product.productType)) {
    fail(`${prefix}: unsupported productType ${product.productType}`);
  }

  if (!allowedStatuses.has(product.status)) {
    fail(`${prefix}: unsupported status ${product.status}`);
  }

  if (!product.canonicalUrl?.startsWith('https://rise-shine-evolve-learning-hub.com/')) {
    fail(`${prefix}: canonicalUrl must use the production RSE domain.`);
  }

  if (product.imageUrl && !product.imageUrl.startsWith('https://')) {
    fail(`${prefix}: imageUrl must be HTTPS.`);
  }

  if (product.identifiers?.asin && !/^[A-Z0-9]{10}$/.test(product.identifiers.asin)) {
    fail(`${prefix}: ASIN must be exactly 10 uppercase alphanumeric characters.`);
  }

  if (product.identifiers?.isbn13 && !/^\d{13}$/.test(product.identifiers.isbn13)) {
    fail(`${prefix}: isbn13 must be exactly 13 digits when present.`);
  }

  if (product.status === 'coming_soon' && product.purchase?.availability === 'in_stock') {
    fail(`${prefix}: coming_soon products cannot be marked in_stock.`);
  }

  if (product.productType === 'android_app') {
    if (product.distribution?.platform !== 'Google Play') {
      fail(`${prefix}: Android app distribution platform must be Google Play.`);
    }
    if (product.status === 'coming_soon' && product.purchase?.price != null) {
      fail(`${prefix}: do not publish a price for a coming-soon app before it is verified.`);
    }
  }

  if (product.purchase?.price == null && product.purchase?.currency != null) {
    fail(`${prefix}: currency cannot be set when price is null.`);
  }

  const readiness = product.aiDiscovery || {};
  if (readiness.openaiFeedReady === true) {
    const missing = [];
    if (product.purchase?.price == null) missing.push('price');
    if (!product.purchase?.currency) missing.push('currency');
    if (!product.purchase?.availability) missing.push('availability');
    if (!product.purchase?.merchantName) missing.push('merchantName');
    if (!product.imageUrl) missing.push('imageUrl');
    if (missing.length) fail(`${prefix}: openaiFeedReady=true but missing ${missing.join(', ')}.`);
    if (Array.isArray(readiness.feedBlockers) && readiness.feedBlockers.length) {
      fail(`${prefix}: openaiFeedReady=true but feedBlockers is not empty.`);
    }
  } else if (!Array.isArray(readiness.feedBlockers) || readiness.feedBlockers.length === 0) {
    warn(`${prefix}: not feed-ready but no explicit feed blockers are recorded.`);
  }
}

const entityIds = new Set(entities.map((entity) => entity.id));
for (const entity of entities) {
  if (entity.parentEntityId && !entityIds.has(entity.parentEntityId)) {
    fail(`${entity.id}: parentEntityId ${entity.parentEntityId} does not exist.`);
  }
  if (!entity.canonicalUrl?.startsWith('https://rise-shine-evolve-learning-hub.com/')) {
    fail(`${entity.id}: canonicalUrl must use the production RSE domain.`);
  }
}

const retiredCopy = /Paddle|Progressive Web App|\bPWA\b|\bSaaS\b|12[- ]month|12[- ]MONTH|browser-install|No App Store needed|\bweb app\b/i;
for (const relativePath of requiredAppPages) {
  if (!seoPages.includes(relativePath)) {
    fail(`${relativePath}: app page must be in the centralized SEO inventory.`);
  }

  const absolutePath = path.join(root, relativePath);
  if (!fs.existsSync(absolutePath)) {
    fail(`AI discovery app page is missing: ${relativePath}`);
    continue;
  }

  const html = readText(relativePath);
  if (retiredCopy.test(html)) {
    fail(`${relativePath}: retired PWA/Paddle/SaaS/web-app copy reappeared.`);
  }

  const canonical = html.match(/<link rel="canonical" href="([^"]+)"/i)?.[1];
  if (!canonical?.startsWith('https://rise-shine-evolve-learning-hub.com/')) {
    fail(`${relativePath}: missing or invalid production canonical URL.`);
  }

  if (!html.includes('"@type":"SoftwareApplication"')) {
    fail(`${relativePath}: missing SoftwareApplication JSON-LD.`);
  }
  if (!html.includes('"operatingSystem":"Android"')) {
    fail(`${relativePath}: app schema must declare Android operating system.`);
  }
  if (/"offers"\s*:/.test(html)) {
    fail(`${relativePath}: coming-soon app schema must not publish an Offer.`);
  }
}

for (const relativePath of ['library/world-01/index.html', 'library/world-02/index.html']) {
  const html = readText(relativePath);
  if (html.includes('https://schema.org/InStock')) {
    fail(`${relativePath}: Amazon stock must not be hard-coded as InStock without a verified source.`);
  }
}

const christmasPage = readText('library/christmas-book/index.html');
const christmasProduct = products.find((product) => product.id === 'rse-24-gentle-steps-christmas');
if (!christmasProduct) {
  fail('Christmas canonical product record is missing.');
} else if (!christmasPage.includes(christmasProduct.canonicalName)) {
  fail(`Christmas page must contain canonical name: ${christmasProduct.canonicalName}`);
}

for (const warning of warnings) console.warn(`WARN: ${warning}`);

if (errors.length) {
  for (const error of errors) console.error(`ERROR: ${error}`);
  console.error(`AI discovery validation failed with ${errors.length} error(s).`);
  process.exit(1);
}

console.log(`AI discovery validation passed: ${products.length} products, ${entities.length} entities, ${requiredAppPages.length} app pages, ${warnings.length} warning(s).`);
