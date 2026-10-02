const CACHE_NAME = 'gentle-steps-en-full24-v5';
const APP_SHELL = [
  './',
  './index.html',
  './styles.css',
  './app.js',
  './manifest.webmanifest',
  './content/week-01.json',
  './content/week-02.json',
  './content/week-03.json',
  './content/week-04.json',
  './brand/generated/family-clean.webp',
  './brand/app-icon.svg',
  './brand/generated/Mimi.webp',
  './brand/generated/Luli.webp',
  './brand/generated/Dilo.webp',
  './brand/generated/Alio.webp',
  './brand/generated/Nini.webp',
  '../assets/js/rse-analytics-consent.js'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(APP_SHELL))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(
        keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
      ))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;

  event.respondWith(
    fetch(event.request)
      .then((response) => {
        if (response && response.ok) {
          const copy = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copy));
        }
        return response;
      })
      .catch(async () => {
        const cached = await caches.match(event.request);
        if (cached) return cached;
        if (event.request.mode === 'navigate') return caches.match('./index.html');
        throw new Error('offline resource unavailable');
      })
  );
});
