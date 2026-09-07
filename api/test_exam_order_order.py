# -*- coding: utf-8 -*-
"""IMTIHON BUYURTMALARI RO'YXATI (2026-09-07).

Jahongir: "Ob bo'lingan testlarni betdan o'chirsa bo'ladimi, yangi
testlar tepada emas paaastda ko'b ketarkan, noqulay bo'lyapti yangi
test tushsa ko'rgani".

QOIDA (hech narsa O'CHIRILMAYDI):
  · sukut bo'yicha faqat OCHIQ so'rovlar (yangi + qabul qilingan);
  · yangi so'rovlar eng tepada, ichida sanasi yaqinlari birinchi;
  · o'tkazilgan/rad etilganlar tanlagich orqali ochiladi
    ("O'tkazildi" yoki "Barchasi") va eng yangisi tepada turadi.
"""
import os
import sys

os.environ["DATABASE_URL"] = "sqlite:////tmp/exord.db"
if os.path.exists("/tmp/exord.db"):
    os.remove("/tmp/exord.db")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import date, timedelta                  # noqa: E402
from fastapi.testclient import TestClient             # noqa: E402
import main, models, roles                            # noqa: E402
import entry                                          # noqa: E402,F401
from database import SessionLocal                     # noqa: E402
from auth import hash_password                        # noqa: E402

client = TestClient(main.app)
fails = []


def ck(name, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + name + f": {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


def tok(u, p="x"):
    return {"Authorization": "Bearer " + client.post(
        "/api/auth/login", json={"username": u, "password": p}
    ).json()["access_token"]}


db = SessionLocal()
b = models.Branch(name="Zafar"); db.add(b); db.commit()
db.add(models.User(username="asos", password_hash=hash_password("x"),
                   full_name="Asoschi", role=roles.FOUNDER))
db.commit()
g = models.Group(name="Step 1", branch_id=b.id, lesson_price=45_000,
                 standard_lessons_per_month=12, monthly_fee=540_000)
db.add(g); db.commit()
T = roles.local_today()


def buyurtma(kun, holat, unit=1):
    o = models.ExamOrder(branch_id=b.id, group_id=g.id, kind="unit",
                         unit_no=unit, date=T + timedelta(days=kun),
                         status=holat, note=f"{holat} {kun}")
    db.add(o); db.commit(); return o


# Eski, allaqachon o'tkazilgan 5 ta (sanasi eng eskisi birinchi)
done = [buyurtma(-d, "done", unit=d) for d in (30, 20, 10, 5, 2)]
# Qabul qilingan 1 ta
acc = buyurtma(3, "accepted", unit=6)
# YANGI 2 ta: biri ertaga (shoshilinch), biri 10 kundan keyin
new_far = buyurtma(10, "new", unit=7)
new_soon = buyurtma(1, "new", unit=8)

A = tok("asos")

print("=== 1. Sukut bo'yicha: faqat ochiq so'rovlar, yangilar tepada ===")
r = client.get("/api/exam-orders", headers=A)
ck("status 200", r.status_code, 200)
d = r.json()
ids = [x["id"] for x in d["rows"]]
ck("faqat 3 ta ochiq so'rov (5 ta o'tkazilgani yashirin)", len(ids), 3)
ck("1-o'rinda ERTANGI yangi so'rov", ids[0], new_soon.id)
ck("2-o'rinda keyingi yangi so'rov", ids[1], new_far.id)
ck("3-o'rinda qabul qilingani", ids[2], acc.id)
ck("hisoblagichlar", (d["new"], d["accepted"]), (2, 1))
ck("shoshilinch bloki ertangini ko'rsatadi",
   [x["id"] for x in d["urgent"]], [new_soon.id])

print("\n=== 2. O'tkazilganlar YO'QOLMAGAN — filtr bilan ochiladi ===")
r = client.get("/api/exam-orders?status=done", headers=A)
dd = r.json()
ck("5 tasi ham joyida", len(dd["rows"]), 5)
ck("eng YANGISI tepada (2 kun oldingi)", dd["rows"][0]["id"], done[-1].id)
ck("eng eskisi pastda (30 kun oldingi)", dd["rows"][-1]["id"], done[0].id)

print("\n=== 3. Barchasi: ochiqlar tepada, tarix pastda ===")
r = client.get("/api/exam-orders?status=all", headers=A)
al = [x["id"] for x in r.json()["rows"]]
ck("hammasi ko'rinadi", len(al), 8)
ck("boshida yangi va qabul qilingan",
   al[:3], [new_soon.id, new_far.id, acc.id])
ck("keyin o'tkazilganlar (yangisidan eskisiga)",
   al[3:], [x.id for x in reversed(done)])

print("\n=== 4. Bazada hech narsa o'chmagan ===")
ck("8 ta buyurtma bazada turibdi",
   db.query(models.ExamOrder).count(), 8)

print()
print("XATOLAR:", fails if fails else "yo'q")
sys.exit(1 if fails else 0)
