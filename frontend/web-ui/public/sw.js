/**
 * [PHASE2] Adam Prism — PWA Service Worker
 * Caches static assets for offline use, but always tries network first for API.
 */

const CACHE_VERSION = 'adam-prism-v1';
const STATIC_CACHE = `${CACHE_VERSION}-static`;
const RUNTIME_CACHE = `${CACHE_VERSION}-runtime`;

// Static assets to precache
const PRECACHE_URLS = [
  '/',
  '/manifest.json',
  '/logo.svg',
  '/offline',
];

// Install: precache static assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE).then((cache) => {
      return cache.addAll(PRECACHE_URLS).catch((err) => {
        // Non-fatal: some URLs may not exist in dev
        console.warn('[SW] Precache failed for some URLs:', err);
      });
    })
  );
  self.skipWaiting();
});

// Activate: clean up old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => name !== STATIC_CACHE && name !== RUNTIME_CACHE)
          .map((name) => caches.delete(name))
      );
    })
  );
  self.clients.claim();
});

// Fetch: network-first for API, cache-first for static
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET, cross-origin, and API requests
  if (request.method !== 'GET' || url.origin !== location.origin) {
    return;
  }

  // API calls: always go to network (don't cache)
  if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/ws/')) {
    return;
  }

  // Static assets: cache-first, then network
  event.respondWith(
    caches.match(request).then((cached) => {
      if (cached) {
        // Return cached, but also update cache in background
        event.waitUntil(
          fetch(request).then((response) => {
            if (response && response.status === 200) {
              const clone = response.clone();
              caches.open(RUNTIME_CACHE).then((cache) => {
                cache.put(request, clone);
              });
            }
          }).catch(() => {})
        );
        return cached;
      }
      // Not in cache: fetch from network
      return fetch(request).then((response) => {
        if (response && response.status === 200) {
          const clone = response.clone();
          caches.open(RUNTIME_CACHE).then((cache) => {
            cache.put(request, clone);
          });
        }
        return response;
      }).catch(() => {
        // Network failed and no cache: show offline page
        if (request.mode === 'navigate') {
          return caches.match('/offline');
        }
        return new Response('Offline', { status: 503 });
      });
    })
  );
});

// Listen for messages from the page
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});
