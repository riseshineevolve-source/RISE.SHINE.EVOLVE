import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const shellRoot = path.dirname(fileURLToPath(import.meta.url));
const appRoot = path.resolve(shellRoot, '..');
const repoRoot = path.resolve(shellRoot, '../..');
const dist = path.join(shellRoot, 'dist');

await fs.rm(dist, { recursive: true, force: true });
await fs.mkdir(path.join(dist, 'content'), { recursive: true });
await fs.mkdir(path.join(dist, 'brand', 'concepts'), { recursive: true });

async function read(relative) {
  return fs.readFile(path.join(appRoot, relative), 'utf8');
}
async function write(relative, content) {
  const target = path.join(dist, relative);
  await fs.mkdir(path.dirname(target), { recursive: true });
  await fs.writeFile(target, content);
}

let index = await read('index.html');
index = index.replace(/\s*<script src="\/assets\/js\/rse-analytics-consent\.js"><\/script>\s*/g, '\n');
await write('index.html', index);

await write('styles.css', await read('styles.css'));

let app = await read('app.js');
app = app.replace(
  /\n\s*if \('serviceWorker' in navigator && location\.protocol !== 'file:'\) \{[\s\S]*?\n\s*\}/,
  ''
);
await write('app.js', app);
await write('manifest.webmanifest', await read('manifest.webmanifest'));

for (const name of ['source-lock.json','week-01.json','week-02.json','week-03.json','week-04.json']) {
  await fs.copyFile(path.join(appRoot, 'content', name), path.join(dist, 'content', name));
}

await fs.copyFile(
  path.join(appRoot, 'brand', 'concepts', 'splash-v2-city-family.webp'),
  path.join(dist, 'brand', 'concepts', 'splash-v2-city-family.webp')
);

await write('native-build.json', JSON.stringify({
  product_id: 'gentle_steps_christmas',
  canonical_locale: 'en',
  source_sha256: '1f79edd316f353963ef33bb980843b37f367a0bacb9198bd63e0d221cb8c9ba7',
  android_package_id_status: 'PROVISIONAL_PRE_PLAY',
  android_package_id: 'com.riseshineevolve.gentlesteps',
  reminders: 'native_local_only',
  family_visual: 'brand/concepts/splash-v2-city-family.webp'
}, null, 2));

console.log('Prepared native web bundle at', dist);
