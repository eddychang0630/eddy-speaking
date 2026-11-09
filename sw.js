const CACHE_NAME = 'eddy-speaking-v4';
const urlsToCache = ['./', './index.html', './lessons/index.js', './manifest.json', './icon-192.png', './icon-512.png', './apple-touch-icon.png'];

self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(urlsToCache)).then(() => self.skipWaiting()));
});

// 同源資源：網路優先（部署新版立即生效），離線時退回快取
self.addEventListener('fetch', event => {
  const request = event.request;
  if (request.method !== 'GET') return;
  const url = new URL(request.url);
  // 只快取本 App 註冊範圍內的資源。
  if (url.origin !== self.location.origin || !url.pathname.startsWith(new URL(self.registration.scope).pathname)) return;
  // MP3 交給瀏覽器自己處理：Safari 播音檔會發 Range 請求，從 Service Worker 快取回應會讓 iOS 播不出來
  if (url.pathname.endsWith('.mp3')) return;
  event.respondWith(
    fetch(request, { cache: 'no-store' }) // 跳過瀏覽器 HTTP 快取，部署新版立即生效
      .then(response => {
        if (response.ok) { const copy = response.clone(); caches.open(CACHE_NAME).then(c => c.put(request, copy)); }
        return response;
      })
      .catch(() => caches.match(request).then(r => r || caches.match('./index.html')))
  );
});

// 啟用時清掉本 App 的舊版快取，以及搬家前舊版口說 App（/eddy-flashcards/speaking/）留下的 eddy-chunks-* 快取
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(names => Promise.all(names.filter(n => (n.startsWith('eddy-speaking-') && n !== CACHE_NAME) || n.startsWith('eddy-chunks-')).map(n => caches.delete(n)))).then(() => self.clients.claim())
  );
});
