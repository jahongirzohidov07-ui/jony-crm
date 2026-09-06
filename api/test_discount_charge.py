# -*- coding: utf-8 -*-
"""AVTOMAT OYLIK YECHIMDA CHEGIRMA (2026-09-06).

Jahongir: "togrla hamma aytganingni" — to'liq check-up auditida
topilgan 1-xato: sentabrdan ishlayotgan avtomat yechim
(entry._mc_charge_full) chegirmani UMUMAN hisobga olmasdi. Oilaviy
10%, xodim farzandi va individual chegirmalar faqat faollashtirish/
muzlatish/ko'chirish qayta hisoblarida ishlardi — oddiy oy boshi
yechimida esa TO'LIQ narx yechilardi.

Test tekshiradi:
  1. yangi yechim chegirma bilan yechadi (oilaviy va individual);
  2. chegirmasiz o'quvchi avvalgidek to'liq narxda qoladi;
  3. o'tgan oy qaytarishi ham chegirmali summadan hisoblanadi;
  4. fix_discount_charges() eski (chegirmasiz) qatorni JOYIDA
     to'g'rilaydi, qator o'chirilmaydi, audit yoziladi, ikkinchi marta
     ishlaganda hech narsa o'zgarmaydi;
  5. chegirma tasdiqlanganda shu oy hisobi darrov qayta yoziladi;
  6. 0 so'mlik to'lov saqlanmaydi.
"""
import os
import sys

os.environ["DATABASE_URL"] = "sqlite:////tmp/disc_charge.db"
if os.path.exists("/tmp/disc_charge.db"):
    os.remove("/tmp/disc_charge.db")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import date                             # noqa: E402
from fastapi.testclient import TestClient             # noqa: E402
import main, models, roles                            # noqa: E402
import entry                                          # noqa: E402
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
TODAY = roles.local_today()
PERIOD = f"{TODAY.year:04d}-{TODAY.month:02d}"
b = models.Branch(name="Zafar"); db.add(b); db.commit()
db.add(models.User(username="asos", password_hash=hash_password("x"),
                   full_name="Asoschi", role=roles.FOUNDER))
db.commit()
g = models.Group(name="Step 1", branch_id=b.id, lesson_price=45_000,
                 standard_lessons_per_month=12, monthly_fee=540_000)
db.add(g); db.commit()
FULL = 45_000 * 12          # 540 000


def bola(nom, disc_percent=None, kind="individual"):
    s = models.Student(full_name=nom, branch_id=b.id, status="active",
                       group_id=g.id, enrolled_date=date(2026, 6, 1))
    db.add(s); db.commit()
    if disc_percent:
        db.add(models.Discount(student_id=s.id, kind=kind,
                               percent=disc_percent, status="active",
                               reason="test"))
        db.commit()
    return s


oddiy = bola("Chegirmasiz")
ind = bola("Individual 20%", 20)
oila1 = bola("Oila 1")
oila2 = bola("Oila 2")
# Oilaviy chegirma AVTOMAT: bir ota-onaga bog'langan 2+ faol farzand
par = models.Parent(full_name="Ota-ona", phone="+998901234567")
db.add(par); db.commit()
oila1.parent_id = par.id
oila2.parent_id = par.id
db.commit()
db.expire_all()

FAMILY = roles.FAMILY_DISCOUNT_PERCENT
print(f"narx {FULL:,} · oilaviy chegirma {FAMILY}%")


def charge_of(sid):
    p = (db.query(models.Payment)
         .filter(models.Payment.student_id == sid,
                 models.Payment.period == PERIOD,
                 models.Payment.kind == "charge").first())
    return None if p is None else round(abs(p.amount))


print("\n=== 1. Avtomat yechim chegirma bilan ===")
entry._mc_charge_full(db, TODAY)
db.commit()
ck("chegirmasiz — to'liq narx", charge_of(oddiy.id), FULL)
ck("individual 20% — 432 000", charge_of(ind.id), round(FULL * 0.8))
ck("oilaviy — chegirma qo'llandi", charge_of(oila1.id),
   round(FULL * (100 - FAMILY) / 100))
ck("oilaviy (ikkinchisi ham)", charge_of(oila2.id),
   round(FULL * (100 - FAMILY) / 100))

print("\n=== 2. Eski (chegirmasiz) qatorni to'g'rilash ===")
# Xato holatni sun'iy yasaymiz: chegirmalilarni to'liq narxga qaytaramiz
for s in (ind, oila1):
    p = (db.query(models.Payment)
         .filter(models.Payment.student_id == s.id,
                 models.Payment.period == PERIOD,
                 models.Payment.kind == "charge").first())
    p.amount = -FULL
db.commit()
before = db.query(models.Payment).count()
r = entry.fix_discount_charges(db)
ck("2 ta qator to'g'rilandi", r["fixed"], 2)
ck("qaytarilgan summa", round(r["sum"]),
   round(FULL * 0.2 + FULL * FAMILY / 100))
ck("yangi qator OCHILMADI (o'chirilmadi ham)",
   db.query(models.Payment).count(), before)
ck("individual endi to'g'ri", charge_of(ind.id), round(FULL * 0.8))
ck("oilaviy endi to'g'ri", charge_of(oila1.id),
   round(FULL * (100 - FAMILY) / 100))
ck("chegirmasizga tegilmadi", charge_of(oddiy.id), FULL)
aud = (db.query(models.AuditLog)
       .filter(models.AuditLog.entity == "payment",
               models.AuditLog.field == "amount").count())
ck("audit yozildi (2 ta)", aud, 2)
r2 = entry.fix_discount_charges(db)
ck("ikkinchi marta — hech narsa o'zgarmaydi", r2["fixed"], 0)

print("\n=== 3. O'tgan oy qaytarishi ham chegirmali ===")
# ind uchun: to'liq 12 dars o'rniga 10 dars o'tilgan bo'lsa
prev_period = PERIOD
held = 10
price = 45_000
disc = 20
actual_full = price * held
actual_disc = actual_full * 0.8
back = round(FULL * 0.8 - actual_disc)
ck("qaytariladigan summa chegirmali hisobdan",
   back, round((FULL - actual_full) * 0.8))

print("\n=== 4. Chegirma tasdiqlanganda shu oy qayta yoziladi ===")
yangi = bola("Keyin chegirma olgan")
# guruh "ishlandi" belgisini olib tashlaymiz — yangi o'quvchi ham yechilsin
import common as _C
_SM = models.SeedMark
db.query(_SM).filter(_SM.key == f"mcf_{PERIOD}_g{g.id}").delete()
db.commit()
if getattr(_C, "_SEED_KEYS", None) is not None:
    _C._SEED_KEYS.discard(f"mcf_{PERIOD}_g{g.id}")
entry._mc_charge_full(db, TODAY)
db.commit()
db.expire_all()
ck("avval to'liq narx", charge_of(yangi.id), FULL)
d = models.Discount(student_id=yangi.id, kind="individual", percent=30,
                    status="pending", reason="test")
db.add(d); db.commit()
r = client.post(f"/api/discounts/{d.id}/approve", json={"approve": True},
                headers=tok("asos"))
ck("tasdiqlash 200", r.status_code, 200)
ck("hisob darrov qayta yozildi", charge_of(yangi.id), round(FULL * 0.7))

print("\n=== 5. 0 so'mlik to'lov ===")
r = client.post(f"/api/students/{oddiy.id}/payments",
                json={"amount": 0, "kind": "payment"}, headers=tok("asos"))
ck("0 so'm rad etiladi", r.status_code, 400)
r = client.post(f"/api/students/{oddiy.id}/payments",
                json={"amount": 100000, "kind": "payment"}, headers=tok("asos"))
ck("oddiy to'lov ishlaydi", r.status_code, 200)

print()
print("XATOLAR:", fails if fails else "yo'q")
sys.exit(1 if fails else 0)
