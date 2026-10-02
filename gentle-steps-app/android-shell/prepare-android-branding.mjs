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
const cityMark = await sharp(splash)
  .resize(760, 760, { fit: 'contain' })
  .png()
  .toBuffer();

await sharp({
  create: {
    width: 1080,
    height: 1920,
    channels: 4,
    background: { r: 36, g: 17, b: 47, alpha: 1 }
  }
})
  .composite([
    {
      input: Buffer.from(`<svg width="1080" height="1920" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <radialGradient id="glow" cx="50%" cy="38%" r="60%">
            <stop offset="0" stop-color="#8E4BC1" stop-opacity=".76"/>
            <stop offset=".48" stop-color="#4C1D72" stop-opacity=".46"/>
            <stop offset="1" stop-color="#24112F" stop-opacity="0"/>
          </radialGradient>
          <linearGradient id="gold" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stop-color="#FFF4C8"/>
            <stop offset=".55" stop-color="#D2A640"/>
            <stop offset="1" stop-color="#8F6114"/>
          </linearGradient>
        </defs>
        <rect width="1080" height="1920" fill="url(#glow)"/>
        <g fill="#E9D08B" opacity=".7">
          <circle cx="170" cy="250" r="5"/><circle cx="900" cy="320" r="7"/>
          <circle cx="250" cy="520" r="4"/><circle cx="830" cy="620" r="5"/>
          <circle cx="120" cy="920" r="6"/><circle cx="930" cy="1080" r="5"/>
          <circle cx="260" cy="1320" r="4"/><circle cx="810" cy="1420" r="6"/>
        </g>
        <path d="M0 1625 L110 1560 L210 1600 L325 1480 L430 1545 L535 1430 L640 1515 L760 1460 L870 1550 L980 1490 L1080 1540 L1080 1920 L0 1920 Z" fill="#1B0A24"/>
        <g fill="#D2A640" opacity=".82">
          <rect x="148" y="1632" width="18" height="22" rx="2"/>
          <rect x="364" y="1574" width="18" height="22" rx="2"/>
          <rect x="558" y="1530" width="18" height="22" rx="2"/>
          <rect x="774" y="1570" width="18" height="22" rx="2"/>
          <rect x="934" y="1585" width="18" height="22" rx="2"/>
        </g>
        <path d="M80 1710 C260 1620 355 1685 520 1605 C675 1530 820 1610 1000 1515" fill="none" stroke="url(#gold)" stroke-width="9" stroke-linecap="round" opacity=".8"/>
      </svg>`),
      top: 0,
      left: 0
    },
    {
      input: cityMark,
      top: 420,
      left: 160
    }
  ])
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
  splash_city_source_sha256: 'DETERMINISTIC_FROM_SPLASH_MARK',
  splash_direction: 'OWNER_APPROVED_V2_CITY_SIMPLIFIED_RUNTIME',
  final_owner_approval_required_before_play_creation: true
};
await fs.writeFile(path.join(shellRoot, 'android-branding.json'), JSON.stringify(metadata, null, 2) + '\n');
console.log('Gentle Steps Android branding prepared');
