"""CHEGIRMA SHU OY HISOBIGA QO'LLANISHI (2026-09-25).

Jahongir: "Chegirmada muammo bor bolyabdi, 10% chegirma yechib
olmayabdi".

Ikki teshik tuzatildi:
  1) tasdiqlash huquqi bor odam (asoschi/filial rahbari/moliya)
     chegirmani O'ZI yozsa — u darrov amalda bo'lardi, lekin shu
     oyning hisobi eski (to'liq) summada qolardi;
  2) oy o'rtasida faollashgan o'quvchining QISMAN hisobiga umuman
     tegilmasdi.
Yana: eski qolib ketganlarni _dsc_fix_month() topib to'g'rilaydi.

Tekshiriladi:
  A) asoschi o'zi qo'shsa      -> 480 000 -> 432 000;
  B) so'rov -> tasdiq          -> 480 000 -> 432 000;
  C) qisman oy (240 000)       -> 216 000;
  D) yana 10% (jami 20%)       -> asl 240 000 dan 192 000;
  E) chegirmasi yo'q o'quvchi  -> tegilmaydi;
  F) eski qolib ketgan hisob   -> _dsc_fix_month() to'g'rilaydi;
  G) ikkinchi yurishda takror kamaymaydi.
"""
import os
import sys
import tempfile
from datetime import date

_DIR = os.path.join(tempfile.gettempdir(), "discount_fix_test")
os.makedirs(_DIR, exist_ok=True)
_DB = os.path.join(_DIR, "db.sqlite")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace(chr(92), "/")
if os.path.exists(_DB):
    os.remove(_DB)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                         # noqa: E402
import entry                                       # noqa: E402
from database import SessionLocal                  # noqa: E402
from auth import hash_password                     # noqa: E402

c = TestClient(main.app)
fails = []


def ck(name, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + name + f": {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


today = roles.local_today()
PERIOD = f"{today.year:04d}-{today.month:02d}"
FIRST = today.replace(day=1)
MC = "avtomat (oylik)"

db = SessionLocal()
b = models.Branch(name="Filial"); db.add(b); db.commit()
t = models.Teacher(full_name="Ustoz", branch_id=b.id); db.add(t); db.commit()
g = models.Group(name="Guruh", branch_id=b.id, teacher_id=t.id,
                 lesson_price=40_000, standard_lessons_per_month=12,
                 monthly_fee=480_000)
db.add(g); db.commit()
# Shu oyning 1-12 kunlari dars bor
for d in range(1, 13):
    db.add(models.Lesson(group_id=g.id, teacher_id=t.id,
                         date=date(today.year, today.month, d), held=1))
BID, GID = b.id, g.id
db.add_all([
    models.User(username="asos", password_hash=hash_password("x"),
                full_name="Asoschi", role=roles.FOUNDER, is_active=1),
    models.User(username="admin1", password_hash=hash_password("x"),
                full_name="Administrator", role=roles.ADMINISTRATOR,
                branch_id=b.id, is_active=1),
])
db.commit()


def student(name, amount, created_by=MC, note="Guruh — 12 dars",
            enrolled=None):
    s = models.Student(full_name=name, branch_id=BID, group_id=GID,
                       status="active", enrolled_date=enrolled or FIRST)
    db.add(s); db.commit()
    db.add(models.Payment(student_id=s.id, amount=-amount, kind="charge",
                          period=PERIOD, note=note, created_by=created_by))
    db.commit()
    return s.id


A = student("A asoschi qo'shadi", 480_000)
B = student("B tasdiqlanadi", 480_000)
C = student("C qisman oy", 240_000, created_by="avtomat",
            note="Guruh — faollashgandan 6 dars",
            enrolled=date(today.year, today.month, 7))
E = student("E chegirmasiz", 480_000)
F = student("F eski qolib ketgan", 480_000)
db.close()


def charge(sid):
    s = SessionLocal()
    p = (s.query(models.Payment)
         .filter(models.Payment.student_id == sid,
                 models.Payment.kind == "charge",
                 models.Payment.period == PERIOD).first())
    out = int(abs(p.amount)) if p else None
    s.close()
    return out


def tok(u):
    return {"Authorization": "Bearer " + c.post(
        "/api/auth/login", json={"username": u, "password": "x"}
    ).json()["access_token"]}


H, HA = tok("asos"), tok("admin1")
BODY = {"kind": "individual", "percent": 10, "reason": "Sinov"}

print("Guruh: 1 dars 40 000 · oylik 480 000 · chegirma 10%")

print("\n=== A) Asoschi chegirmani o'zi qo'shdi ===")
r = c.post("/api/discounts", headers=H, json={**BODY, "student_id": A})
ck("qo'shildi", r.status_code, 200)
ck("darrov amalda", r.json().get("status"), "active")
ck("hisob 432 000 bo'ldi", charge(A), 432_000)

print("\n=== B) Administrator so'radi -> asoschi tasdiqladi ===")
r = c.post("/api/discounts", headers=HA, json={**BODY, "student_id": B})
did = r.json()["id"]
ck("so'rov kutilmoqda", r.json().get("status"), "pending")
ck("tasdiqgacha hisob eski", charge(B), 480_000)
c.post(f"/api/discounts/{did}/approve", headers=H,
       json={"approve": True, "reason": "ok"})
ck("tasdiqdan keyin 432 000", charge(B), 432_000)

print("\n=== C) Oy o'rtasida faollashgan — qisman hisob ===")
c.post("/api/discounts", headers=H, json={**BODY, "student_id": C})
ck("qisman hisob 216 000", charge(C), 216_000)

print("\n=== D) Yana 10% (jami 20%) — asl summadan hisoblanadi ===")
c.post("/api/discounts", headers=H, json={**BODY, "student_id": C})
ck("240 000 dan 20% = 192 000", charge(C), 192_000)

print("\n=== E) Chegirmasiz o'quvchiga tegilmaydi ===")
ck("hisob o'zgarmadi", charge(E), 480_000)

print("\n=== F) Eski qolib ketgan hisobni avtomat to'g'rilaydi ===")
db = SessionLocal()
db.add(models.Discount(student_id=F, kind="individual", percent=10,
                       reason="Eski", status="active",
                       start_date=FIRST, requested_by="Asoschi",
                       approved_by="Asoschi"))
db.commit()
ck("hali chegirmasiz", charge(F), 480_000)
fixed = entry._dsc_fix_month(db, today)
db.commit(); db.close()
ck("to'g'rilanganlar soni", len(fixed), 1)
ck("hisob 432 000 bo'ldi", charge(F), 432_000)

print("\n=== G) Ikkinchi marta yurganda takror kamaytirmaydi ===")
db = SessionLocal()
again = entry._dsc_fix_month(db, today)
db.commit(); db.close()
ck("boshqa tuzatish yo'q", len(again), 0)
ck("hisob o'zgarmadi", charge(F), 432_000)
ck("A ham o'zgarmadi", charge(A), 432_000)

print("\n=== H) Aka-uka: IKKALASIGA ham chegirma tushadi ===")
# Jahongir: "aka uka bolsa bittasiga chegirma ishlab ikkinchisiga
# ishlamayabdi". Ilgari bog'langanda faqat SO'ROV YUBORILGAN bolaning
# hisobi qayta yozilardi, ikkinchisi to'liq summada qolardi.
db = SessionLocal()
K1 = student("Aziz Fozilov", 480_000)
K2 = student("Aziza Fozilova", 480_000)
db.close()
ck("aka: boshida to'liq", charge(K1), 480_000)
ck("uka: boshida to'liq", charge(K2), 480_000)
r = c.post(f"/api/students/{K1}/family-link", headers=H,
           json={"sibling_id": K2})
ck("bog'landi", r.status_code, 200)
ck("oilaviy foiz", r.json().get("family_percent"), 10.0)
ck("AKA hisobi 432 000", charge(K1), 432_000)
ck("UKA hisobi ham 432 000", charge(K2), 432_000)

print("\nJAMI XATO:", len(fails), fails)
sys.exit(1 if fails else 0)
