// Jony Academy — PWA servis worker.
//
// 2026-08-24 TUZATISH (Jahongir: "oxirgi paytlar shunaqa holatlar
// kop uchrayabdi" — /student sahifasida "Bu bo'limni ochishda
// xatolik yuz berdi").
//
// NIMA BO'LGAN EDI. Avvalgi versiya HAMMA narsani "avval keshdan"
// (cache-first) qaytarardi — index.html ni ham. Yangi versiya
// chiqqanda brauzer ESKI index.html ni ko'rsatardi; u esa endi
// serverda yo'q bo'lgan eski JS bo'laklarini so'rardi -> 404 ->
// sahifa yiqilardi. Kunda bir necha marta deploy qilinganda bu
// tez-tez uchraydi. Ustiga: sw.js ildizda turgani uchun uning
// ta'siri butun saytga (xodimlar paneliga ham) tarqalgan.
//
// ENDI QANDAY. Ikki xil qoida:
//   1. SAHIFA (HTML / navigatsiya) — DOIM avval tarmoqdan. Internet
//      bo'lmasa keshdagi nusxa ishlatiladi. Ya'ni yangi versiya
//      chiqsa, foydalanuvchi darrov uni oladi.
//   2. /assets/ ichidagi fayllar — nomida o'zgarmas xesh bor
//      (index-AbC123.js). Ular hech qachon o'zgarmaydi, shuning
//      uchun keshdan berish xavfsiz va tez.
//   3. Qolgan statik fayllar (ikonka, rasm, manifest) — keshdan
//      beriladi, lekin orqa fonda yangilanadi.
//
// API so'rovlariga ("/api/...") HECH QACHON aralashmaydi — davomat,
// balans va boshqa raqamlar doim jonli tarmoqdan olinishi SHART.
const CACHE = "jonyos-v3";

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

function isHtml(request) {
  if (request.mode === "navigate") return true;
  const accept = request.headers.get("accept") || "";
  return accept.includes("text/html");
}

self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (request.method !== "GET") return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;
  if (url.pathname.startsWith("/api/")) return; // har doim jonli

  // 1) Sahifa — avval tarmoq, keyin kesh (eski qobiq qotib qolmasin)
  if (isHtml(request)) {
    event.respondWith(
      fetch(request)
        .then((res) => {
          if (res && res.ok) {
            const copy = res.clone();
            caches.open(CACHE).then((c) => c.put(request, copy));
          }
          return res;
        })
        .catch(() =>
          caches.match(request).then((c) => c || caches.match("/index.html"))
        )
    );
    return;
  }

  // 2) Xeshli bo'laklar — keshdan (ular o'zgarmaydi)
  if (url.pathname.startsWith("/assets/")) {
    event.respondWith(
      caches.match(request).then(
        (cached) =>
          cached ||
          fetch(request).then((res) => {
            if (res && res.ok) {
              const copy = res.clone();
              caches.open(CACHE).then((c) => c.put(request, copy));
            }
            return res;
          })
      )
    );
    return;
  }

  // 3) Qolgan statik — keshdan, orqa fonda yangilanadi
  event.respondWith(
    caches.open(CACHE).then(async (cache) => {
      const cached = await cache.match(request);
      const network = fetch(request)
        .then((res) => {
          if (res && res.ok) cache.put(request, res.clone());
          return res;
        })
        .catch(() => cached);
      return cached || network;
    })
  );
});
