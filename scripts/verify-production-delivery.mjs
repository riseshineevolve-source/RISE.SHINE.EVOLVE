import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import process from 'node:process';

const ROOT = process.cwd();
const BASE = 'https://rise-shine-evolve-learning-hub.com';
const REPORT_PATH = path.join(ROOT, 'reports/ai-discovery/production-delivery-run.json');
const USER_AGENT = 'RiseShineEvolve-ProductionVerifier/1.0 (+https://rise-shine-evolve-learning-hub.com/)';

const retiredAppPatterns = [
  /Progressive Web App/i,
  /\bPWA\b/i,
  /\bSaaS\b/i,
  /Paddle/i,
  /12[- ]month/i,
  /1[- ]Year Access Pass/i,
  /Install App/i,
  /web browser and click/i
];

const checks = [
  {
    route: '/',
    localPath: 'index.html',
    required: ['https://rise-shine-evolve-learning-hub.com/'],
    forbidden: []
  },
  {
    route: '/adventure-app/',
    localPath: 'adventure-app/index.html',
    required: ['Coming Soon on Google Play', '"operatingSystem":"Android"'],
    forbidden: retiredAppPatterns
  },
  {
    route: '/unstoppable-app/',
    localPath: 'unstoppable-app/index.html',
    required: ['Coming Soon on Google Play', '"operatingSystem":"Android"'],
    forbidden: retiredAppPatterns
  },
  {
    route: '/guides/big-feelings/',
    localPath: 'guides/big-feelings/index.html',
    required: ['Big feelings in kids', 'pause, connect, name, choose'],
    forbidden: []
  },
  {
    route: '/guides/confidence-for-kids/',
    localPath: 'guides/confidence-for-kids/index.html',
    required: ['Confidence for kids', 'Build an evidence bank'],
    forbidden: []
  },
  {
    route: '/guides/after-school-crash/',
    localPath: 'guides/after-school-crash/index.html',
    required: ['After-school crash', 'The After-School Crash'],
    forbidden: []
  },
  {
    route: '/guides/screen-balance/',
    localPath: 'guides/screen-balance/index.html',
    required: ['Screen balance for kids', 'four-part screen transition'],
    forbidden: []
  },
  {
    route: '/sitemap.xml',
    localPath: 'sitemap.xml',
    required: [
      '/guides/big-feelings/',
      '/guides/confidence-for-kids/',
      '/guides/after-school-crash/',
      '/guides/screen-balance/'
    ],
    forbidden: []
  },
  {
    route: '/robots.txt',
    localPath: 'robots.txt',
    required: ['Sitemap:', 'sitemap.xml'],
    forbidden: []
  }
];

const sha256 = (value) => crypto.createHash('sha256').update(value).digest('hex');
const normalizeText = (value) => String(value).replace(/\r\n/g, '\n').trim();
const headerValue = (headers, name) => headers.get(name) || null;

async function fetchWithTimeout(url, timeoutMs = 20000) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, {
      redirect: 'follow',
      signal: controller.signal,
      headers: {
        'user-agent': USER_AGENT,
        'cache-control': 'no-cache',
        pragma: 'no-cache'
      }
    });
  } finally {
    clearTimeout(timer);
  }
}

async function runCheck(check) {
  const url = `${BASE}${check.route}`;
  const localFile = path.join(ROOT, check.localPath);
  const result = {
    route: check.route,
    url,
    localPath: check.localPath,
    status: null,
    finalUrl: null,
    okHttp: false,
    exactBodyMatch: false,
    productionSha256: null,
    localSha256: null,
    missingRequiredMarkers: [],
    forbiddenMarkersFound: [],
    headers: {},
    error: null,
    passed: false
  };

  if (!fs.existsSync(localFile)) {
    result.error = `Local source file missing: ${check.localPath}`;
    return result;
  }

  const localBody = fs.readFileSync(localFile, 'utf8');
  result.localSha256 = sha256(normalizeText(localBody));

  try {
    const response = await fetchWithTimeout(url);
    const body = await response.text();
    const normalizedBody = normalizeText(body);

    result.status = response.status;
    result.finalUrl = response.url;
    result.okHttp = response.ok;
    result.productionSha256 = sha256(normalizedBody);
    result.exactBodyMatch = result.productionSha256 === result.localSha256;
    result.headers = {
      server: headerValue(response.headers, 'server'),
      via: headerValue(response.headers, 'via'),
      age: headerValue(response.headers, 'age'),
      etag: headerValue(response.headers, 'etag'),
      lastModified: headerValue(response.headers, 'last-modified'),
      cacheControl: headerValue(response.headers, 'cache-control'),
      cfRay: headerValue(response.headers, 'cf-ray'),
      cfCacheStatus: headerValue(response.headers, 'cf-cache-status'),
      xNfRequestId: headerValue(response.headers, 'x-nf-request-id'),
      xServedBy: headerValue(response.headers, 'x-served-by'),
      xCache: headerValue(response.headers, 'x-cache'),
      xVercelId: headerValue(response.headers, 'x-vercel-id')
    };

    for (const marker of check.required || []) {
      if (!body.toLowerCase().includes(marker.toLowerCase())) {
        result.missingRequiredMarkers.push(marker);
      }
    }

    for (const pattern of check.forbidden || []) {
      if (pattern.test(body)) {
        result.forbiddenMarkersFound.push(pattern.toString());
      }
    }

    result.passed = result.okHttp && result.missingRequiredMarkers.length === 0 && result.forbiddenMarkersFound.length === 0;
  } catch (error) {
    result.error = `${error.name || 'Error'}: ${error.message || String(error)}`;
  }

  return result;
}

const results = [];
for (const check of checks) {
  // Sequential requests keep the report readable and avoid hammering production.
  results.push(await runCheck(check));
}

const providerSignals = {
  netlify: results.some((result) => Boolean(result.headers?.xNfRequestId)),
  cloudflare: results.some((result) => Boolean(result.headers?.cfRay || /cloudflare/i.test(result.headers?.server || ''))),
  vercel: results.some((result) => Boolean(result.headers?.xVercelId))
};

const report = {
  schemaVersion: 1,
  checkedAt: new Date().toISOString(),
  baseUrl: BASE,
  providerSignals,
  passed: results.every((result) => result.passed),
  exactBodyMatchCount: results.filter((result) => result.exactBodyMatch).length,
  checkCount: results.length,
  results
};

fs.mkdirSync(path.dirname(REPORT_PATH), { recursive: true });
fs.writeFileSync(REPORT_PATH, `${JSON.stringify(report, null, 2)}\n`);

console.log(JSON.stringify(report, null, 2));

if (!report.passed) {
  const failed = results.filter((result) => !result.passed).map((result) => result.route);
  console.error(`Production delivery verification failed for: ${failed.join(', ')}`);
  process.exit(1);
}

console.log(`Production delivery verification passed for ${results.length} URLs.`);
