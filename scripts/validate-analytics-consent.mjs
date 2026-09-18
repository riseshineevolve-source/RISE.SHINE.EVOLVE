#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";

const ROOT = process.cwd();
const ANALYTICS_SRC = "/assets/js/rse-analytics-consent.js";
const ANALYTICS_FILE = path.join(ROOT, "assets", "js", "rse-analytics-consent.js");
const EXPECTED_ID = "G-WW6C0S6031";

function walk(dir) {
  const out = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if ([".git", "node_modules", ".lighthouseci"].includes(entry.name)) continue;
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) out.push(...walk(full));
    else out.push(full);
  }
  return out;
}

const errors = [];
const htmlFiles = walk(ROOT).filter((file) => file.endsWith(".html"));
const analytics = fs.readFileSync(ANALYTICS_FILE, "utf8");

if (!htmlFiles.length) errors.push("No HTML files found.");

for (const file of htmlFiles) {
  const rel = path.relative(ROOT, file).replaceAll("\\", "/");
  const source = fs.readFileSync(file, "utf8");
  const includeCount = (source.match(/<script\s+src=["']\/assets\/js\/rse-analytics-consent\.js["']><\/script>/g) || []).length;
  if (includeCount !== 1) {
    errors.push(`${rel}: expected exactly one analytics-consent include, found ${includeCount}`);
  }
  if (/googletagmanager\.com\/gtag\/js/i.test(source)) {
    errors.push(`${rel}: direct Google tag found outside the consent module`);
  }
}

const requiredSnippets = [
  `var MEASUREMENT_ID = "${EXPECTED_ID}"`,
  'analytics_storage: "denied"',
  'ad_storage: "denied"',
  'ad_user_data: "denied"',
  'ad_personalization: "denied"',
  'allow_google_signals: false',
  'allow_ad_personalization_signals: false',
  'navigator.globalPrivacyControl === true',
  'rise-shine-evolve-learning-hub.com',
  'www.rise-shine-evolve-learning-hub.com'
];

for (const snippet of requiredSnippets) {
  if (!analytics.includes(snippet)) errors.push(`analytics module missing required guard: ${snippet}`);
}

if (!analytics.includes("if (!isProduction()) return;")) {
  errors.push("analytics module does not fail closed on non-production hosts");
}

if (!analytics.includes("clearAnalyticsCookies")) {
  errors.push("analytics module does not clear first-party GA cookies after revocation");
}

if (/allow_google_signals:\s*true/.test(analytics)) {
  errors.push("Google Signals must remain disabled");
}
if (/allow_ad_personalization_signals:\s*true/.test(analytics)) {
  errors.push("Ad personalization signals must remain disabled");
}

console.log(`Analytics coverage: ${htmlFiles.length} HTML files`);
console.log(`Measurement ID: ${EXPECTED_ID}`);
console.log("Mode: privacy-first BASIC consent mode; Google tag blocked before opt-in");

if (errors.length) {
  console.error("\nANALYTICS CONSENT VALIDATION: FAIL");
  for (const error of errors) console.error(`- ${error}`);
  process.exit(1);
}

console.log("ANALYTICS CONSENT VALIDATION: PASS");
