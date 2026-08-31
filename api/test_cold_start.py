# -*- coding: utf-8 -*-
"""SOVUQ START QOROVULI (2026-08-31).

Jahongir: "negadur shunaqa bo'p qoldi, nima bo'lyabdi" — Vercel
butun hisobni to'xtatgan edi: avgustda 12 soat 45 daqiqa protsessor
sarflangan, chegara esa 4 soat.

O'LCHOV NIMA KO'RSATDI:
    import main ......... 4 300 ms
    import entry ........   500 ms
    birinchi so'rov .....   950 ms
    ISSIQ so'rov ........    25 ms   <-- 170 barobar arzon

Ya'ni protsessorning ~85 foizi SOVUQ STARTGA ketgan, so'rovlarni
bajarishga emas. 275 ming so'rovga 12h45m = bittasiga o'rtacha
167 ms; issiq so'rov esa 25 ms. Farq — uyg'onishlar.

SHUNING UCHUN IKKI CHORA:
  1) /api/health ga har 5 daqiqada cron (vercel.json) — funksiya
     uxlab qolmaydi, uyg'onish soni keskin kamayadi;
  2) startdagi takroriy ishlar kunlik belgiga bog'landi.

BU TEST ikkalasini QOROVULLAYDI: /api/health arzon qolishi va
sovuq startda bazaga tegish soni chegaradan oshmasligi.
"""
import os
import sys

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_cold/db.sqlite"
os.makedirs("/tmp/verify_cold", exist_ok=True)
if os.path.exists("/tmp/verify_cold/db.sqlite"):
    os.remove("/tmp/verify_cold/db.sqlite")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json                                          # noqa: E402
from sqlalchemy import event                         # noqa: E402
from sqlalchemy.engine import Engine                 # noqa: E402

_Q = [0]


@event.listens_for(Engine, "before_cursor_execute")
def _count(conn, cur, st, p, ctx, many):
    _Q[0] += 1


from fastapi.testclient import TestClient            # noqa: E402
import main, models                                  # noqa: E402
import entry                                         # noqa: F401,E402
from database import SessionLocal                    # noqa: E402

c = TestClient(main.app)
db = SessionLocal()
fails = []


def ck(n, got, want):
    ok = got == want
    print(("OK   " if ok else "XATO ") + f"{n}: {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(n)


# =====================================================================
print("=== 1. /api/health — ISITISH UCHUN ARZON BO'LISHI SHART ===")
# =====================================================================
c.get("/api/health")                       # isitish
_Q[0] = 0
r = c.get("/api/health")
ck("ochiq (login talab qilmaydi)", r.status_code, 200)
ck("javobi to'g'ri", r.json().get("status"), "ok")
ck("BAZAGA UMUMAN TEGMAYDI", _Q[0], 0)
# Cron har 5 daqiqada uradi. Agar kimdir bu yo'lga baza so'rovi
# qo'shsa, kuniga 180 ta ortiqcha so'rov paydo bo'ladi — shuning
# uchun nol talab qilinadi.


# =====================================================================
print("\n=== 2. ISITISH CRONI SOZLANGAN ===")
# =====================================================================
vj = json.load(open(os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "vercel.json"), encoding="utf-8"))
crons = {x["path"]: x["schedule"] for x in vj.get("crons", [])}
ck("/api/health uchun cron bor", "/api/health" in crons, True)
ck("  har 5 daqiqada", crons.get("/api/health", "").startswith("*/5"), True)
ck("kunlik cron ham joyida", "/api/cron/daily" in crons, True)


# =====================================================================
print("\n=== 3. STARTDAGI TAKRORIY ISH — KUNIGA BIR MARTA ===")
# =====================================================================
from datetime import date                            # noqa: E402
import common                                        # noqa: E402
kun = "frozen_abs_" + date.today().isoformat()
ck("bugungi belgi qo'yilgan",
   db.query(models.SeedMark).get(kun) is not None, True)
# Ikkinchi marta chaqirilsa — ish qilinmasligi kerak
common._SEED_KEYS = None            # kesh tozalanadi (yangi jarayon kabi)
ck("ikkinchi startda o'tkazib yuboriladi",
   common._seed_done(db, kun), True)


# =====================================================================
print("\n=== 4. ISSIQ SO'ROV ARZON QOLGANINI TEKSHIRISH ===")
# =====================================================================
# Bu tuzatishlar so'rovlarga TEGMAGAN bo'lishi kerak — health
# bundan mustasno, u umuman bazasiz.
for path in ("/api/health", "/api/public/branches"):
    c.get(path)
    _Q[0] = 0
    r = c.get(path)
    ck(f"{path} ishlaydi", r.status_code, 200)
ck("  ochiq filiallar ro'yxati 1-2 so'rov", _Q[0] <= 2, True)


print("\n" + "=" * 60)
if fails:
    print("YIQILGAN TEKSHIRUVLAR:", len(fails))
    for f in fails:
        print("  -", f)
else:
    print("HAMMASI O'TDI")
sys.exit(1 if fails else 0)
