import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';
import sharp from 'sharp';

const shellRoot = path.dirname(fileURLToPath(import.meta.url));
const resRoot = path.join(shellRoot, 'android', 'app', 'src', 'main', 'res');
const brandRoot = path.join(shellRoot, '..', 'brand');

const icon = await fs.readFile(path.join(brandRoot, 'app-icon.svg'));
const foreground = await fs.readFile(path.join(brandRoot, 'app-icon-foreground.svg'));
const splash = await fs.readFile(path.join(brandRoot, 'splash-mark.svg'));
const splashCity = await fs.readFile(path.join(brandRoot, 'concepts', 'splash-v2-city-family.webp'));

const densities = {
  mdpi: { legacy: 48, foreground: 108 },
  hdpi: { legacy: 72, foreground: 162 },
  xhdpi: { legacy: 96, foreground: 216 },
  xxhdpi: { legacy: 144, foreground: 324 },
  xxxhdpi: { legacy: 192, foreground: 432 }
};

for (const [density, sizes] of Object.entries(densities)) {
  const dir = path.join(resRoot, 'mipmap-' + density);
  await fs.mkdir(dir, { recursive: true });
  await sharp(icon).resize(sizes.legacy, sizes.legacy).png().toFile(path.join(dir, 'ic_launcher.png'));
  await sharp(icon).resize(sizes.legacy, sizes.legacy).png().toFile(path.join(dir, 'ic_launcher_round.png'));
  await sharp(foreground).resize(sizes.foreground, sizes.foreground).png().toFile(path.join(dir, 'ic_launcher_foreground.png'));
}

const anydpi = path.join(resRoot, 'mipmap-anydpi-v26');
await fs.mkdir(anydpi, { recursive: true });
const adaptive = `<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
  <background android:drawable="@color/gentle_icon_bg"/>
  <foreground android:drawable="@mipmap/ic_launcher_foreground"/>
  <monochrome android:drawable="@drawable/ic_launcher_monochrome"/>
</adaptive-icon>
`;
await fs.writeFile(path.join(anydpi, 'ic_launcher.xml'), adaptive);
await fs.writeFile(path.join(anydpi, 'ic_launcher_round.xml'), adaptive);

const values = path.join(resRoot, 'values');
await fs.mkdir(values, { recursive: true });
await fs.writeFile(path.join(values, 'gentle_brand.xml'), `<?xml version="1.0" encoding="utf-8"?>
<resources>
  <color name="gentle_icon_bg">#4C1D72</color>
  <color name="gentle_splash_bg">#24112F</color>
</resources>
`);

const drawable = path.join(resRoot, 'drawable');
await fs.mkdir(drawable, { recursive: true });
await fs.writeFile(path.join(drawable, 'ic_launcher_monochrome.xml'), `<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
  android:width="108dp" android:height="108dp"
  android:viewportWidth="108" android:viewportHeight="108">
  <path android:fillColor="#FFFFFFFF"
    android:pathData="M54,15 L62,46 L93,54 L62,62 L54,93 L46,62 L15,54 L46,46 Z"/>
</vector>
`);

for (const dirent of await fs.readdir(resRoot, { withFileTypes: true })) {
  if (!dirent.isDirectory() || !dirent.name.startsWith('drawable')) continue;
  await fs.rm(path.join(resRoot, dirent.name, 'splash.png'), { force: true });
}

const splashNoDpi = path.join(resRoot, 'drawable-nodpi');
await fs.mkdir(splashNoDpi, { recursive: true });
await sharp(splash).resize(384, 384).png().toFile(path.join(splashNoDpi, 'gentle_splash_mark.png'));
await sharp(splashCity)
  .resize(1080, 1920, { fit: 'cover', position: 'centre' })
  .png()
  .toFile(path.join(splashNoDpi, 'gentle_splash_city.png'));
await fs.writeFile(path.join(drawable, 'splash.xml'), `<?xml version="1.0" encoding="utf-8"?>
<layer-list xmlns:android="http://schemas.android.com/apk/res/android">
  <item android:drawable="@color/gentle_splash_bg"/>
  <item>
    <bitmap android:src="@drawable/gentle_splash_city" android:gravity="fill"/>
  </item>
</layer-list>
`);

const sha = (buf) => crypto.createHash('sha256').update(buf).digest('hex');
const metadata = {
  status: 'PROVISIONAL_INTERNAL_TEST_BRANDING',
  palette: ['#24112F','#4C1D72','#8E4BC1','#D2A640','#FFF7E8'],
  app_icon_source_sha256: sha(icon),
  adaptive_foreground_source_sha256: sha(foreground),
  splash_mark_source_sha256: sha(splash),
  splash_city_source_sha256: sha(splashCity),
  splash_direction: 'OWNER_APPROVED_V2_CITY_FAMILY',
  final_owner_approval_required_before_play_creation: true
};
await fs.writeFile(path.join(shellRoot, 'android-branding.json'), JSON.stringify(metadata, null, 2) + '\n');
console.log('Gentle Steps Android branding prepared');
