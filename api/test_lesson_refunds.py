"""KAM DARS — FARQ QAYTARILDI (2026-10-02).

Jahongir: "ba'zi o'quvchilarda 1-oktabrda qanaqadur chegirma bilan pul
qo'shilib qolyabdi ... qayerdan paydo bo'lyabdi shuni bilish kerak",
"chegirmalar +summa bo'lib qo'shilmasin", kam dars uchun —
"Qaytarilmasin".

Tekshiriladi:
  1. Oy oxiridagi avtomat qaytarish endi hech narsa yozmaydi.
  2. Ro'yxat har qator uchun sababni ko'rsatadi: guruh almashgan,
     yo'qlama qo'yilmagan darslar.
  3. Faqat asoschi ko'radi va bekor qiladi.
  4. Bekor qilish: qator arxivga (payments_deleted), audit, balans
     to'liq oylikka qaytadi; boshqa turdagi to'lovga tegilmaydi.
"""
import os
import sys
import tempfile
from datetime import date, datetime, timedelta

_DIR = os.path.join(tempfile.gettempdir(), "lesson_refunds_test")
os.makedirs(_DIR, exist_ok=True)
_DB = os.path.join(_DIR, "db.sqlite")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace(chr(92), "/")
if os.path.exists(_DB):
    os.remove(_DB)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                         # noqa: E402
import entry                                       # noqa: E402
import common as _cm_stub                          # noqa: E402
from database import SessionLocal                  # noqa: E402
from auth import hash_password                     # noqa: E402

_cm_stub._ensure_month_charges = lambda db, **kw: None

client = TestClient(main.app)
fails = []


def ck(name, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + name + f": {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


Y, M = 2026, 9
P = f"{Y}-{M:02d}"
db = SessionLocal()
b = models.Branch(name="Bekobod 2"); db.add(b); db.commit()
BID = b.id
for login, role in (("asos", roles.FOUNDER), ("adm", roles.SALES_MANAGER)):
    db.add(models.User(username=login, password_hash=hash_password("x"),
                       full_name=login, role=role,
                       branch_id=None if role == roles.FOUNDER else BID,
                       is_active=1))
g1 = models.Group(name="Louisiana", branch_id=BID, lesson_price=40_000,
                  standard_lessons_per_month=12, lesson_days="")
g2 = models.Group(name="LOUISIANA 2", branch_id=BID, lesson_price=40_000,
                  standard_lessons_per_month=12, lesson_days="")
db.add_all([g1, g2]); db.commit()
# Sentabr: har guruhda 12 dars; LOUISIANA 2 da 3 tasiga yo'qlama yo'q
for g, unmarked in ((g1, 0), (g2, 3)):
    for i in range(12):
        db.add(models.Lesson(group_id=g.id, date=date(Y, M, 2 + i * 2),
                             held=0 if i >= 12 - unmarked else 1))
db.commit()
moved = models.Student(full_name="Murodov Shohruh", branch_id=BID,
                       status="active", group_id=g2.id,
                       enrolled_date=date(Y, 8, 6))
stay = models.Student(full_name="Simora", branch_id=BID, status="active",
                      group_id=g2.id, enrolled_date=date(Y, 8, 1))
db.add_all([moved, stay]); db.commit()
SID, SID2 = moved.id, stay.id


def pay(sid, amt, kind, note, by="avtomat (oylik)", period=P, at=None):
    p = models.Payment(student_id=sid, amount=amt, kind=kind, note=note,
                       created_by=by, period=period,
                       created_at=at or datetime(Y, 10, 1, 0, 5))
    db.add(p); db.commit()
    return p.id


pay(SID, -480_000, "charge", f"Louisiana — {P}: 12 dars (standart oy, avtomat)",
    at=datetime(Y, M, 1))
R1 = pay(SID, 120_000, "discount",
         f"LOUISIANA 2 — {P}: 9 dars o'tildi, farq qaytarildi")
pay(SID2, -480_000, "charge",
    f"LOUISIANA 2 — {P}: 12 dars (standart oy, avtomat)", at=datetime(Y, M, 1))
R2 = pay(SID2, 120_000, "discount",
         f"LOUISIANA 2 — {P}: 9 dars o'tildi, farq qaytarildi")
OTHER = pay(SID2, 50_000, "discount", "Jony Shop chegirmasi",
            by="Jony Shop (coin)")
db.close()

print("=== 1. Avtomat qaytarish o'chirilgan ===")
s = SessionLocal()
ck("hech narsa yozmaydi", entry._mc_refund_prev(s, date(Y, 10, 1)),
   (0, True))
s.close()


def tok(u):
    return {"Authorization": "Bearer " + client.post(
        "/api/auth/login", json={"username": u, "password": "x"}
    ).json()["access_token"]}


F = tok("asos")
URL = "/api/admin/lesson-refunds"

print("\n=== 2. Ro'yxat va sabablar ===")
d = client.get(URL, headers=F).json()
ck("2 ta qator, jami", (d["count"], d["total"]), (2, 240_000))
rows = {r["payment_id"]: r for r in d["rows"]}
r1 = rows[R1]
ck("guruh almashgani aytildi", any("guruh almashgan" in x
                                   for x in r1["reasons"]), True)
ck("yo'qlama qo'yilmagan 3 dars", any("3 ta darsga yo'qlama" in x
                                      for x in r1["reasons"]), True)
ck("guruhlar", (r1["charged_groups"], r1["refund_group"]),
   (["Louisiana"], "LOUISIANA 2"))
ck("ikkinchisida guruh almashmagan", any(
    "guruh almashgan" in x for x in rows[R2]["reasons"]), False)
ck("Jony Shop qatori ro'yxatda yo'q", OTHER in rows, False)

print("\n=== 3. Ruxsat ===")
A = tok("adm")
ck("admin ko'rmaydi", client.get(URL, headers=A).status_code, 403)
ck("admin bekor qila olmaydi", client.post(
    f"{URL}/cancel", headers=A, json={"ids": [R1]}).status_code, 403)

print("\n=== 4. Bekor qilish ===")
r = client.post(f"{URL}/cancel", headers=F,
                json={"ids": [R1, OTHER]}).json()
ck("faqat qaytarish qatori bekor qilindi",
   [x["payment_id"] for x in r["cancelled"]], [R1])
s = SessionLocal()
ck("qator payments'dan chiqdi", s.query(models.Payment).get(R1), None)
ck("arxivda bor", s.query(models.DeletedPayment)
   .filter(models.DeletedPayment.payment_id == R1).count(), 1)
ck("Jony Shop qatori joyida", s.query(models.Payment).get(OTHER) is not None,
   True)
ck("balans to'liq oylikka qaytdi", round(_cm_stub.student_balance(s, SID)),
   -480_000)
ck("audit yozildi", s.query(models.AuditLog).filter(
    models.AuditLog.entity == "payment",
    models.AuditLog.entity_id == R1).count(), 1)
s.close()
ck("ro'yxatda 1 ta qoldi", client.get(URL, headers=F).json()["count"], 1)

print("\n=== 5. Bir martalik avtomat bekor qilish (Jahongir: olib tashla) ===")
s = SessionLocal()
R3 = models.Payment(student_id=SID, amount=80_000, kind="discount",
                    note=f"Louisiana — {P}: 10 dars o'tildi, farq qaytarildi",
                    created_by="avtomat (oylik)", period=P,
                    created_at=datetime(Y, 10, 1, 0, 5))
s.add(R3); s.commit(); R3 = R3.id
entry._mc_ensure(s)
s.close()
s = SessionLocal()
left = s.query(models.Payment).filter(
    models.Payment.kind == "discount",
    models.Payment.note.like("%farq qaytarildi%")).count()
ck("hammasi olib tashlandi", left, 0)
ck("arxivda", s.query(models.DeletedPayment).filter(
    models.DeletedPayment.payment_id.in_([R2, R3])).count(), 2)
ck("Jony Shop qatori joyida", s.query(models.Payment).get(OTHER) is not None,
   True)
ck("Simora sentabri to'liq oylik (Jony Shop alohida)",
   round(sum(x.amount for x in s.query(models.Payment).filter(
       models.Payment.student_id == SID2, models.Payment.period == P,
       models.Payment.kind != "discount"))), -480_000)
R4 = models.Payment(student_id=SID, amount=1, kind="discount",
                    note=f"X — {P}: 1 dars o'tildi, farq qaytarildi",
                    created_by="avtomat (oylik)", period=P)
s.add(R4); s.commit(); R4 = R4.id
entry._mc_ensure(s)
ck("bir martalik — keyingi yurishda tegmaydi",
   s.query(models.Payment).get(R4) is not None, True)
s.close()

print()
if fails:
    print(f"{len(fails)} ta XATO: {fails}")
    sys.exit(1)
print("HAMMASI OK")
