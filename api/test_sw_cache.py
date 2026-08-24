"""SERVIS WORKER KESHI (2026-08-24).

Jahongir: "oxirgi paytlar shunaqa holatlar kop uchrayabdi" —
/student sahifasida "Bu bo'limni ochishda xatolik yuz berdi".

SABAB. Eski servis worker HAMMA narsani (index.html ni ham)
avval keshdan qaytarardi. Yangi versiya chiqqanda brauzer ESKI
index.html ni ko'rsatib, endi serverda yo'q bo'lgan eski JS
bo'laklarini so'rardi -> 404 -> sahifa yiqilardi.

Bu test sw.js MANTIG'INI tekshiradi (brauzersiz): HTML uchun
tarmoq birinchi, /assets/ uchun kesh birinchi, /api/ ga umuman
tegilmasligi.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SW = os.path.join(os.path.dirname(HERE), "public", "sw.js")
src = open(SW, encoding="utf-8").read()
fails = []


def ck(n, g, w):
    ok = g == w
    print(("OK  " if ok else "XATO ") + f"{n}: {g}"
          + ("" if ok else f"   (kutilgan {w})"))
    if not ok:
        fails.append(n)


print("=== 1. KESH NOMI YANGILANDI ===")
m = re.search(r'const CACHE = "([^"]+)"', src)
ck("kesh nomi bor", bool(m), True)
ck("eski v1 emas (eski kesh tozalanadi)",
   m.group(1) if m else "", "jonyos-v3")

print("\n=== 2. HTML — TARMOQ BIRINCHI ===")
ck("navigatsiya ajratilgan", 'request.mode === "navigate"' in src, True)
ck("accept text/html tekshiriladi", 'text/html' in src, True)
# HTML shoxida fetch() birinchi, catch ichida caches.match bo'lishi kerak
html_branch = src[src.index("if (isHtml(request))"):src.index('if (url.pathname.startsWith("/assets/"))')]
ck("HTMLda avval fetch", html_branch.index("fetch(request)")
   < html_branch.index("caches.match"), True)
ck("internetsiz keshga tushadi", "catch(() =>" in html_branch, True)

print("\n=== 3. /assets/ — KESH BIRINCHI (xeshli, o'zgarmaydi) ===")
a_branch = src[src.index('if (url.pathname.startsWith("/assets/"))'):]
a_branch = a_branch[:a_branch.index("// 3)")]
ck("assetsda avval kesh", a_branch.index("caches.match")
   < a_branch.index("fetch(request)"), True)

print("\n=== 4. API GA TEGILMAYDI ===")
ck("/api/ chetlab o'tiladi", 'url.pathname.startsWith("/api/")' in src, True)
ck("va return qilinadi",
   'if (url.pathname.startsWith("/api/")) return;' in src, True)

print("\n=== 5. FAQAT GET VA O'Z DOMENI ===")
ck("GET dan boshqasi tegilmaydi", 'request.method !== "GET"' in src, True)
ck("boshqa domen tegilmaydi",
   "url.origin !== self.location.origin" in src, True)

print("\n=== 6. ESKI KESHLAR TOZALANADI ===")
ck("activate'da eski keshlar o'chadi",
   "caches.delete" in src and "keys()" in src, True)
ck("darrov boshqaruvni oladi", "clients.claim()" in src, True)
ck("kutib turmaydi", "skipWaiting()" in src, True)

print("\n=== 7. MIJOZ TOMONI: VERSIYA XATOSI USHLANADI ===")
main_src = open(os.path.join(os.path.dirname(HERE), "src", "main.tsx"),
                encoding="utf-8").read()
ck("vite:preloadError ushlanadi", "vite:preloadError" in main_src, True)
ck("dinamik import xatosi ham", "unhandledrejection" in main_src, True)
ck("bir martalik bayroq bor", "jonyos_chunk_reload" in main_src, True)
ck("muvaffaqiyatdan keyin tozalanadi",
   "removeItem(RELOAD_KEY)" in main_src, True)
ck("SW yangilanganda qayta yuklanadi",
   "controllerchange" in main_src, True)
ck("birinchi o'rnatishda yuklanmaydi (aylanmasin)",
   "hadController" in main_src, True)

eb = open(os.path.join(os.path.dirname(HERE), "src", "components",
                       "ErrorBoundary.tsx"), encoding="utf-8").read()
ck("ErrorBoundary versiya xatosini ajratadi",
   "isVersionError" in eb, True)
ck("va boshqacha xabar beradi", "Dastur yangilandi" in eb, True)

print("\n" + ("HAMMASI O'TDI" if not fails else f"XATOLAR: {fails}"))
sys.exit(1 if fails else 0)
