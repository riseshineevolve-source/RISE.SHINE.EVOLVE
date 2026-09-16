import process from 'node:process';

const PRODUCTION_ORIGIN = 'https://rise-shine-evolve-learning-hub.com';
const PRODUCTION_HOST = 'rise-shine-evolve-learning-hub.com';
const DEFAULT_ENDPOINT = 'https://api.indexnow.org/indexnow';
const MAX_URLS = 10000;

const args = process.argv.slice(2);
const dryRun = args.includes('--dry-run');
const rawUrls = args.filter((arg) => arg !== '--dry-run');

function fail(message) {
  console.error(`IndexNow: ${message}`);
  process.exit(1);
}

if (rawUrls.length === 0) {
  fail('provide at least one production URL, e.g. npm run indexnow:submit -- https://rise-shine-evolve-learning-hub.com/library/world-01/');
}

if (rawUrls.length > MAX_URLS) {
  fail(`a single request may contain at most ${MAX_URLS} URLs.`);
}

const uniqueUrls = [...new Set(rawUrls)].map((value) => {
  let url;
  try {
    url = new URL(value);
  } catch {
    fail(`invalid URL: ${value}`);
  }

  if (url.origin !== PRODUCTION_ORIGIN) {
    fail(`refusing non-production URL: ${value}`);
  }

  if (url.username || url.password) {
    fail(`credentials are not allowed in submitted URLs: ${value}`);
  }

  url.hash = '';
  return url.toString();
});

const key = process.env.INDEXNOW_KEY?.trim();
const keyLocation = process.env.INDEXNOW_KEY_LOCATION?.trim();
const endpoint = process.env.INDEXNOW_ENDPOINT?.trim() || DEFAULT_ENDPOINT;

if (!dryRun && !key) {
  fail('INDEXNOW_KEY is required. Do not commit the key to the repository.');
}

if (key && !/^[A-Za-z0-9-]{8,128}$/.test(key)) {
  fail('INDEXNOW_KEY must be 8-128 characters using letters, numbers, or dashes.');
}

if (keyLocation) {
  let location;
  try {
    location = new URL(keyLocation);
  } catch {
    fail('INDEXNOW_KEY_LOCATION must be a valid HTTPS URL.');
  }
  if (location.protocol !== 'https:' || location.hostname !== PRODUCTION_HOST) {
    fail('INDEXNOW_KEY_LOCATION must be hosted on the RSE production domain over HTTPS.');
  }
}

let endpointUrl;
try {
  endpointUrl = new URL(endpoint);
} catch {
  fail('INDEXNOW_ENDPOINT must be a valid HTTPS URL.');
}
if (endpointUrl.protocol !== 'https:') {
  fail('INDEXNOW_ENDPOINT must use HTTPS.');
}

const payload = {
  host: PRODUCTION_HOST,
  key: dryRun ? '[redacted-dry-run]' : key,
  ...(keyLocation ? { keyLocation } : {}),
  urlList: uniqueUrls,
};

if (dryRun) {
  console.log(`IndexNow dry run: ${uniqueUrls.length} URL(s) validated for ${PRODUCTION_HOST}.`);
  console.log(JSON.stringify({ ...payload, key: '[redacted]' }, null, 2));
  process.exit(0);
}

const response = await fetch(endpointUrl, {
  method: 'POST',
  headers: {
    'content-type': 'application/json; charset=utf-8',
  },
  body: JSON.stringify(payload),
});

if (![200, 202].includes(response.status)) {
  const body = await response.text().catch(() => '');
  fail(`submission failed with HTTP ${response.status}${body ? `: ${body.slice(0, 500)}` : ''}`);
}

console.log(`IndexNow accepted ${uniqueUrls.length} URL(s) with HTTP ${response.status}.`);
