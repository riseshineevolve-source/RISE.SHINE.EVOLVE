import fs from 'node:fs';
import path from 'node:path';

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const read = (relative) => fs.readFileSync(path.join(root, relative), 'utf8');
const parse = (relative) => JSON.parse(read(relative));

const sourceSha = '1f79edd316f353963ef33bb980843b37f367a0bacb9198bd63e0d221cb8c9ba7';
const weekFiles = ['content/week-01.json', 'content/week-02.json', 'content/week-03.json', 'content/week-04.json'];
const packs = weekFiles.map(parse);
const days = packs.flatMap((pack) => pack.days).sort((a, b) => a.day - b.day);
const index = read('index.html');
const app = read('app.js');
const css = read('styles.css');
const sw = read('service-worker.js');
const manifest = parse('manifest.webmanifest');
const sourceLock = parse('content/source-lock.json');

const fail = (message) => {
  console.error('FAIL:', message);
  process.exitCode = 1;
};

if (packs.map((pack) => pack.week).join(',') !== '1,2,3,4') fail('expected weeks 1-4');
for (const pack of packs) {
  if (pack.product_id !== 'gentle_steps_christmas') fail('wrong product_id in week ' + pack.week);
  if (pack.canonical_locale !== 'en') fail('English must be canonical in week ' + pack.week);
  if (pack.source_sha256 !== sourceSha) fail('source SHA mismatch in week ' + pack.week);
  if (!pack.week_quote) fail('week quote missing in week ' + pack.week);
}

if (days.length !== 24) fail('expected exactly 24 days');
if (days.map((day) => day.day).join(',') !== Array.from({ length: 24 }, (_, i) => i + 1).join(',')) {
  fail('days are not sequential 1-24');
}

const expectedCategories = ['Mindful Moment', 'Fun Spark', 'Family Connection'];
const sourcePages = [];
for (const day of days) {
  if (!Array.isArray(day.sections) || day.sections.length !== 3) fail('day ' + day.day + ' must have exactly 3 sections');
  const categories = day.sections.map((section) => section.category);
  if (categories.join('|') !== expectedCategories.join('|')) fail('day ' + day.day + ' category order mismatch');

  for (const section of day.sections) {
    sourcePages.push(section.page);
    if (!section.title || !section.tagline) fail('day ' + day.day + ' missing title/tagline');
    if (!Array.isArray(section.body) || section.body.length === 0) fail('day ' + day.day + ' missing body');
    if (!section.note_label || !section.note) fail('day ' + day.day + ' missing Happy-Makers note');
  }
}

const expectedPages = [];
for (let day = 1; day <= 24; day += 1) {
  let start;
  if (day <= 7) start = 21 + (day - 1) * 3;
  else if (day <= 14) start = 43 + (day - 8) * 3;
  else if (day <= 21) start = 65 + (day - 15) * 3;
  else start = 87 + (day - 22) * 3;
  expectedPages.push(start, start + 1, start + 2);
}
if (sourcePages.join(',') !== expectedPages.join(',')) fail('source-page map mismatch');

const rawContent = weekFiles.map(read).join('\n');
if (rawContent.includes('pl-PL')) fail('Polish locale must not be bundled in English build');
if (app.includes('pl-PL') || app.includes('data-locale')) fail('language switch must not exist in English-first build');

if (!app.includes('week-01.json') || !app.includes('week-04.json')) fail('app does not load all week packs');
if (!app.includes('localStorage')) fail('local progress persistence missing');
if (!app.includes("params.get('preview') === '1'")) fail('owner/test preview override missing');
if (!app.includes("params.get('family') === '1'")) fail('family review route missing');
if (!app.includes('FAMILY_ASSET')) fail('family hero asset contract missing');
if (!app.includes('CHARACTER_ASSETS')) fail('character avatar contract missing');
if (!app.includes('familyDialog()')) fail('Meet the Happy-Makers experience missing');
if (!app.includes('nativeReminderPlugin()')) fail('native reminder bridge missing');
if (!app.includes('REMINDER_NOTIFICATION_BASE_ID')) fail('Advent reminder ID contract missing');
if (!app.includes('for (let day = 1; day <= 24; day += 1)')) fail('24-day reminder scheduling loop missing');
if (!app.includes('isUnlocked')) fail('Advent day-lock behavior missing');
if (app.includes('supabase') || app.includes('firebase') || app.includes('openai')) fail('no backend/AI dependency allowed');

for (const required of ['./styles.css', './app.js', './manifest.webmanifest']) {
  if (!index.includes(required)) fail('index missing ' + required);
}
if (!index.includes('/assets/js/rse-analytics-consent.js')) fail('privacy-first analytics consent include missing');

for (const file of weekFiles) {
  if (!sw.includes(file.replace('content/', './content/'))) fail('offline cache missing ' + file);
}
if (!app.includes("24%20Gentle%20Steps%20to%20Christmas%20cover.jpg")) fail('canonical Gentle Steps cover artwork missing');
if (!app.includes("'../assets/images/Mimi.png'")) fail('character portrait mapping missing');
if (manifest.display !== 'standalone') fail('PWA standalone display required');
if (manifest.lang !== 'en') fail('manifest must be English');
if (manifest.theme_color !== '#4b2865') fail('purple theme color mismatch');

for (const token of ['--purple-950', '--purple-800', '--purple-600', '--purple-500', '--gold-500', '--cream', '--burgundy']) {
  if (!css.includes(token)) fail('palette token missing: ' + token);
}
if (!css.includes('.character-avatar')) fail('character-note avatar styling missing');
if (!css.includes('.family-profile-grid')) fail('family-profile styling missing');
if (!css.includes('.hero-visual')) fail('family hero styling missing');
if (css.includes('--evergreen')) fail('old green palette leaked into English build');

if (sourceLock.paperback.sha256 !== sourceSha) fail('source-lock paperback hash mismatch');
if (sourceLock.paperback.status !== 'FINAL_EN_TEXT_OWNER_LOCKED') fail('source lock status missing');
if (sourceLock.app_content.polish_included !== false) fail('source lock must record Polish as excluded');

const day1 = days[0];
const day24 = days[23];
if (day1.sections[0].title !== 'Shared Silence') fail('Day 1 source anchor mismatch');
if (day24.sections[2].title !== 'Circle of Gratitude & Wishes') fail('Day 24 source anchor mismatch');

if (!process.exitCode) {
  console.log('PASS: Gentle Steps full English 24-day app contract');
  console.log('PASS: 24 days / 72 source pages / EN-only / multi-purple-gold-cream / Happy-Makers visual identity / offline / no backend');
}
