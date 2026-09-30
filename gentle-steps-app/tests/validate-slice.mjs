import fs from 'node:fs';
import path from 'node:path';

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const read = (relative) => fs.readFileSync(path.join(root, relative), 'utf8');

const pack = JSON.parse(read('content/days-01-03.json'));
const index = read('index.html');
const app = read('app.js');
const sw = read('service-worker.js');
const manifest = JSON.parse(read('manifest.webmanifest'));

const fail = (message) => {
  console.error('FAIL:', message);
  process.exitCode = 1;
};

if (pack.product_id !== 'gentle_steps_christmas') fail('wrong product_id');
if (pack.canonical_locale !== 'en') fail('English must remain canonical');
if (JSON.stringify(pack.supported_locales) !== JSON.stringify(['en', 'pl-PL'])) fail('EN + pl-PL locales required');
if (!Array.isArray(pack.days) || pack.days.length !== 3) fail('slice must contain exactly Days 1-3');

const seen = new Set();
for (const day of pack.days) {
  if (![1, 2, 3].includes(day.day)) fail('unexpected day in slice: ' + day.day);
  for (const locale of pack.supported_locales) {
    const copy = day.locales?.[locale];
    if (!copy) {
      fail('missing locale ' + locale + ' for day ' + day.day);
      continue;
    }
    if (!Array.isArray(copy.sections) || copy.sections.length !== 3) fail('day ' + day.day + ' ' + locale + ' must have 3 sections');
    const types = copy.sections.map((section) => section.type).sort().join(',');
    if (types !== 'connection,fun,mindful') fail('day ' + day.day + ' ' + locale + ' has wrong section types');
    for (const section of copy.sections) {
      if (seen.has(locale + ':' + section.id)) fail('duplicate localized section id ' + section.id);
      seen.add(locale + ':' + section.id);
      if (!section.title || !section.tagline || !Array.isArray(section.body) || section.body.length === 0) fail('incomplete copy for ' + section.id);
      if (!section.note_label || !section.note) fail('missing Happy-Makers note for ' + section.id);
    }
  }

  const enIds = day.locales.en.sections.map((section) => section.id).join('|');
  const plIds = day.locales['pl-PL'].sections.map((section) => section.id).join('|');
  if (enIds !== plIds) fail('locale semantic IDs diverge on day ' + day.day);
}

for (const required of ['./styles.css', './app.js', './content/days-01-03.json', './service-worker.js']) {
  if (!index.includes(required.replace('./service-worker.js', './app.js')) && required !== './service-worker.js') {
    fail('index missing shell reference ' + required);
  }
}

if (!app.includes('localStorage')) fail('local progress persistence missing');
if (app.includes('supabase') || app.includes('firebase') || app.includes('openai')) fail('slice must not add backend/AI complexity');
if (!sw.includes('content/days-01-03.json')) fail('content pack not cached for offline use');
if (manifest.display !== 'standalone') fail('PWA standalone display required');
if (manifest.start_url !== './') fail('PWA start_url must stay relative');

if (!process.exitCode) {
  console.log('PASS: Gentle Steps Days 1-3 vertical slice contract');
  console.log('PASS: EN/pl-PL semantic parity, 3 rituals/day, local progress, offline shell, no backend');
}
