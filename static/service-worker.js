// Service worker do News Intelligence Hub — cache básico do app shell para reduzir
// recarregamentos e permitir instalação como PWA.
const CACHE_NAME = "nih-shell-v1";
const SHELL_ASSETS = [
  "/app/static/manifest.json",
  "/app/static/icons/icon-192.png",
  "/app/static/icons/icon-512.png",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(SHELL_ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key)))
    )
  );
  self.clients.claim();
});

// Cache-first apenas para os assets do próprio shell (ícones/manifest); demais
// requisições (dados da app, RSS, etc.) seguem direto para a rede.
self.addEventListener("fetch", (event) => {
  if (SHELL_ASSETS.some((asset) => event.request.url.endsWith(asset))) {
    event.respondWith(
      caches.match(event.request).then((cached) => cached || fetch(event.request))
    );
  }
});
