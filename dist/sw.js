// Jony Academy — Ota-ona (Parent) PWA uchun minimal servis worker.
//
// Maqsad FAQAT ikkita narsa:
//   1. Android/Chrome'ning "o'rnatish mumkin" (installable) mezonini
//      qondirish — bu esa uy ekraniga ilova sifatida qo'shishga
//      imkon beradi;
//   2. Statik fayllarni (JS/CSS/rasmlar) tezroq ko'rsatish.
//
// API so'rovlariga ("/api/...") HECH QACHON aralashmaydi — davomat,
// balans va boshqa ma'lumotlar doim jonli tarmoqdan olinishi SHART,
// eskirgan (keshlangan) raqamlar ota-onaga noto'g'ri ma'lumot berishi
// mumkin. Ro'yxatdan faqat /parent/ doirasida o'tkaziladi (Parent.tsx
// ga qarang) — xodimlar paneliga bu servis worker tegmaydi.
const CACHE = "jonyos-parent-v1";

self.addEventListener("install", () => {
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
      )
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (request.method !== "GET") return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;
  if (url.pathname.startsWith("/api/")) return; // har doim jonli

  event.respondWith(
    caches.open(CACHE).then(async (cache) => {
      const cached = await cache.match(request);
      const network = fetch(request)
        .then((res) => {
          if (res.ok) cache.put(request, res.clone());
          return res;
        })
        .catch(() => cached);
      return cached || network;
    })
  );
});
