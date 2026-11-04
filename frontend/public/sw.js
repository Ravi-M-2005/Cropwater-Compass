/**
 * Cropwater Compass - Service Worker for Offline Caching
 * Ensures application shell, static assets, and offline dataset load even when completely disconnected.
 */
const CACHE_NAME = 'cropwater-compass-v2';
const PRECACHE_ASSETS = [
  '/',
  '/index.html',
  '/offline_dataset.json',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(PRECACHE_ASSETS).catch((err) => {
        console.warn('Pre-cache asset warning:', err);
      });
    }).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;

  const url = new URL(event.request.url);

  // Bypass API and weather requests so live network and reachability checks function as intended
  if (url.pathname.startsWith('/api') || url.hostname.includes('open-meteo.com')) {
    return;
  }

  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      if (cachedResponse) {
        // If online, revalidate in background without throwing errors if offline
        if (typeof self.navigator !== 'undefined' && self.navigator.onLine) {
          fetch(event.request)
            .then((networkResponse) => {
              if (networkResponse && networkResponse.status === 200) {
                caches.open(CACHE_NAME).then((cache) => cache.put(event.request, networkResponse));
              }
            })
            .catch(() => {
              // Ignore background refresh failure
            });
        }
        return cachedResponse;
      }

      // Fetch from network and cache for offline usage
      return fetch(event.request)
        .then((networkResponse) => {
          if (!networkResponse || networkResponse.status !== 200) {
            return networkResponse;
          }
          const responseToCache = networkResponse.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, responseToCache);
          });
          return networkResponse;
        })
        .catch(async () => {
          // Fallback to cached index.html for SPA page navigation when offline
          if (event.request.mode === 'navigate') {
            const fallback = await caches.match('/index.html') || await caches.match('/');
            if (fallback) return fallback;
          }
          return caches.match(event.request);
        });
    })
  );
});
