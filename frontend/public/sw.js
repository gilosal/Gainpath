// PaceForge Service Worker
// Strategy: network-first for API, cache-first for static assets
// Offline: serves cached today view when gym Wi-Fi fails

const CACHE_NAME = "paceforge-v1";
const STATIC_URLS = ["/today", "/calendar", "/progress", "/settings", "/"];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) =>
      cache.addAll(STATIC_URLS).catch(() => {})
    )
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys
            .filter((k) => k !== CACHE_NAME)
            .map((k) => caches.delete(k))
        )
      )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);

  // Skip non-GET and cross-origin chrome-extension requests
  if (event.request.method !== "GET") return;
  if (url.protocol === "chrome-extension:") return;

  // Network-first for API calls (backend on :8000 or /api/*)
  if (url.port === "8000" || url.pathname.startsWith("/api/")) {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          // Cache successful API responses for offline fallback
          if (
            response.ok &&
            url.pathname.includes("/sessions/today")
          ) {
            const clone = response.clone();
            caches
              .open(CACHE_NAME)
              .then((cache) => cache.put(event.request, clone));
          }
          return response;
        })
        .catch(() => caches.match(event.request))
    );
    return;
  }

  // Cache-first for Next.js static assets (_next/static)
  if (url.pathname.startsWith("/_next/static")) {
    event.respondWith(
      caches.match(event.request).then(
        (cached) =>
          cached ||
          fetch(event.request).then((response) => {
            if (response.ok) {
              const clone = response.clone();
              caches
                .open(CACHE_NAME)
                .then((cache) => cache.put(event.request, clone));
            }
            return response;
          })
      )
    );
    return;
  }

  // Stale-while-revalidate for pages
  event.respondWith(
    caches.open(CACHE_NAME).then((cache) =>
      cache.match(event.request).then((cached) => {
        const networkFetch = fetch(event.request).then((response) => {
          if (response.ok) cache.put(event.request, response.clone());
          return response;
        });
        return cached || networkFetch;
      })
    )
  );
});

// Background sync — process offline queue when connection restores
self.addEventListener("sync", (event) => {
  if (event.tag === "sync-offline-queue") {
    event.waitUntil(notifyClientsToSync());
  }
});

async function notifyClientsToSync() {
  const clients = await self.clients.matchAll({ type: "window" });
  clients.forEach((client) =>
    client.postMessage({ type: "SYNC_OFFLINE_QUEUE" })
  );
}
