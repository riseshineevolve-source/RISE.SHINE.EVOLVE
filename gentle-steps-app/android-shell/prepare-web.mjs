import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import sharp from 'sharp';

const shellRoot = path.dirname(fileURLToPath(import.meta.url));
const appRoot = path.resolve(shellRoot, '..');
const repoRoot = path.resolve(shellRoot, '../..');
const dist = path.join(shellRoot, 'dist');

await fs.rm(dist, { recursive: true, force: true });
await fs.mkdir(path.join(dist, 'content'), { recursive: true });
await fs.mkdir(path.join(dist, 'assets', 'images'), { recursive: true });

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
const assetMap = {
  "../assets/images/24%20Gentle%20Steps%20to%20Christmas%20cover.jpg": "./assets/images/gentle-cover.webp",
  "../assets/images/Mimi.png": "./assets/images/Mimi.webp",
  "../assets/images/Luli.png": "./assets/images/Luli.webp",
  "../assets/images/Dilo.png": "./assets/images/Dilo.webp",
  "../assets/images/Alio.png": "./assets/images/Alio.webp",
  "../assets/images/Nini.png": "./assets/images/Nini.webp"
};
for (const [from, to] of Object.entries(assetMap)) app = app.replaceAll(from, to);
app = app.replace(
  /\n\s*if \('serviceWorker' in navigator && location\.protocol !== 'file:'\) \{[\s\S]*?\n\s*\}/,
  ''
);
await write('app.js', app);
await write('manifest.webmanifest', await read('manifest.webmanifest'));

for (const name of ['source-lock.json','week-01.json','week-02.json','week-03.json','week-04.json']) {
  await fs.copyFile(path.join(appRoot, 'content', name), path.join(dist, 'content', name));
}

const sourceImages = path.join(repoRoot, 'assets', 'images');
await sharp(path.join(sourceImages, '24 Gentle Steps to Christmas cover.jpg'))
  .resize(760, 760, { fit: 'cover', position: 'centre' })
  .webp({ quality: 84 })
  .toFile(path.join(dist, 'assets', 'images', 'gentle-cover.webp'));

for (const name of ['Mimi','Luli','Dilo','Alio','Nini']) {
  await sharp(path.join(sourceImages, name + '.png'))
    .resize(256, 256, { fit: 'cover', position: 'north' })
    .webp({ quality: 80 })
    .toFile(path.join(dist, 'assets', 'images', name + '.webp'));
}

await write('native-build.json', JSON.stringify({
  product_id: 'gentle_steps_christmas',
  canonical_locale: 'en',
  source_sha256: '1f79edd316f353963ef33bb980843b37f367a0bacb9198bd63e0d221cb8c9ba7',
  android_package_id_status: 'PROVISIONAL_PRE_PLAY',
  android_package_id: 'com.riseshineevolve.gentlesteps',
  reminders: 'native_local_only'
}, null, 2));

console.log('Prepared native web bundle at', dist);
