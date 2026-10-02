import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';
import sharp from 'sharp';

const shellRoot = path.dirname(fileURLToPath(import.meta.url));
const appRoot = path.resolve(shellRoot, '..');
const repoRoot = path.resolve(shellRoot, '../..');
const sourceRoot = path.join(repoRoot, 'assets', 'images');
const outRoot = path.join(appRoot, 'brand', 'generated');

await fs.mkdir(outRoot, { recursive: true });

await sharp(path.join(sourceRoot, '24 Gentle Steps to Christmas cover.jpg'))
  .resize(960, 720, { fit: 'cover', position: 'south' })
  .webp({ quality: 86, effort: 5 })
  .toFile(path.join(outRoot, 'family-clean.webp'));

for (const name of ['Mimi', 'Luli', 'Dilo', 'Alio', 'Nini']) {
  await sharp(path.join(sourceRoot, name + '.png'))
    .resize(192, 192, { fit: 'cover', position: 'north' })
    .webp({ quality: 82, effort: 5, alphaQuality: 90 })
    .toFile(path.join(outRoot, name + '.webp'));
}

const files = ['family-clean.webp','Mimi.webp','Luli.webp','Dilo.webp','Alio.webp','Nini.webp'];
const manifest = {};
for (const file of files) {
  const bytes = await fs.readFile(path.join(outRoot, file));
  const meta = await sharp(bytes).metadata();
  manifest[file] = {
    sha256: crypto.createHash('sha256').update(bytes).digest('hex'),
    bytes: bytes.length,
    width: meta.width,
    height: meta.height
  };
}
await fs.writeFile(path.join(outRoot, 'manifest.json'), JSON.stringify({
  status: 'GENERATED_FROM_OWNER_LOCKED_REPO_ART',
  generated_by: 'gentle-steps generate web brand assets',
  family_source: 'assets/images/24 Gentle Steps to Christmas cover.jpg',
  portrait_sources: ['Mimi.png','Luli.png','Dilo.png','Alio.png','Nini.png'],
  files: manifest
}, null, 2) + '\n');

console.log(JSON.stringify(manifest, null, 2));
