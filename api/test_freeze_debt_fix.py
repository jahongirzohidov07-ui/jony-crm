"""MUZLATISHDAGI QARZ VA OILAVIY CHEGIRMA (2026-09-25).

Jahongir: "muzlatilgan oquvchida katta qarzdorlik qolib ketyabdi" va
"hammasini tuzat togrla".

Uch tuzatish:
  1) ORQAGA SANA bilan muzlatishda faqat o'sha sana OYI to'g'rilanardi;
     62 kungacha orqaga ruxsat berilgani uchun keyingi oy(lar) to'liq
     summada qolib ketardi. Endi muzlatish oyidan bugungi oygacha
     hammasi ko'riladi.
  2) Dars narxi holat "frozen" bo'lgandan KEYIN hisoblanardi —
     chegirma to'xtab, narx qimmatlashib, muzlatish qarzni OSHIRIB
     yuborishi mumkin edi. Endi narx holat o'zgarishidan oldin
     olinadi.
  3) Aka-ukadan biri muzlatilsa, ikkinchisining OILAVIY chegirmasi
     ham o'chib ketardi (hisobda faqat "faol" sanalardi). Endi
     muzlatilgan farzand ham sanaladi, arxivdagi esa yo'q.
"""
import os
import sys
import tempfile
from datetime import date, timedelta

_DIR = os.path.join(tempfile.gettempdir(), "freeze_debt_fix_test")
os.makedirs(_DIR, exist_ok=True)
_DB = os.path.join(_DIR, "db.sqlite")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace(chr(92), "/")
if os.path.exists(_DB):
    os.remove(_DB)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                         # noqa: E402
import entry                                       # noqa: E402,F401
import common                                      # noqa: E402
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
THIS = f"{today.year:04d}-{today.month:02d}"
PREV_D = today.replace(day=1) - timedelta(days=1)
PREV = f"{PREV_D.year:04d}-{PREV_D.month:02d}"

db = SessionLocal()
b = models.Branch(name="Filial"); db.add(b); db.commit()
t = models.Teacher(full_name="Ustoz", branch_id=b.id, is_active=1)
db.add(t); db.commit()
g = models.Group(name="Guruh", branch_id=b.id, teacher_id=t.id,
                 lesson_price=40_000, standard_lessons_per_month=12,
                 monthly_fee=480_000)
db.add(g); db.commit()
db.add(models.User(username="asos", password_hash=hash_password("x"),
                   full_name="Asoschi", role=roles.FOUNDER, is_active=1))
db.commit()
BID, GID, TID = b.id, g.id, t.id


def student(name, status="active"):
    s = models.Student(full_name=name, branch_id=BID, group_id=GID,
                       status=status,
                       enrolled_date=date(PREV_D.year, PREV_D.month, 1))
    db.add(s); db.commit()
    db.add(models.StudentGroupLink(student_id=s.id, group_id=GID,
                                   is_primary=1, active=1))
    db.commit()
    return s.id


def charge(sid, period):
    s2 = SessionLocal()
    p = (s2.query(models.Payment)
         .filter(models.Payment.student_id == sid,
                 models.Payment.kind == "charge",
                 models.Payment.period == period).first())
    out = int(abs(p.amount)) if p else None
    s2.close()
    return out


A = student("Orqaga muzlatiladi")
# O'tgan oy va shu oyning 1-6 kunlarida dars
for per_d in (PREV_D, today):
    for d in range(1, 7):
        db.add(models.Lesson(group_id=GID, teacher_id=TID,
                             date=date(per_d.year, per_d.month, d), held=1))
# Ikkala oyga ham to'liq oylik yozilgan
for per in (PREV, THIS):
    db.add(models.Payment(student_id=A, amount=-480_000, kind="charge",
                          period=per, note="Guruh — 12 dars",
                          created_by="avtomat (oylik)"))
db.commit(); db.close()

H = {"Authorization": "Bearer " + c.post(
    "/api/auth/login", json={"username": "asos", "password": "x"}
).json()["access_token"]}

print("=== 1. Orqaga sana: IKKALA oy ham to'g'rilanadi ===")
ck("o'tgan oy to'liq edi", charge(A, PREV), 480_000)
ck("shu oy to'liq edi", charge(A, THIS), 480_000)
frm = date(PREV_D.year, PREV_D.month, 4)       # o'tgan oyning 4-kuni
r = c.post(f"/api/students/{A}/freeze", headers=H,
           json={"from_date": frm.isoformat(),
                 "until": (today + timedelta(days=30)).isoformat(),
                 "reason": "other", "note": "Sinov"})
ck("muzlatildi", r.status_code, 200)
ck("o'tgan oy kamaydi", charge(A, PREV) < 480_000, True)
print("   o'tgan oy:", charge(A, PREV), "· shu oy:", charge(A, THIS))
ck("shu oy nolga tushdi", charge(A, THIS), 0)

print("\n=== 2. Chegirmali o'quvchida qarz OSHMAYDI ===")
B = student("Chegirmali")
db = SessionLocal()
db.add(models.Payment(student_id=B, amount=-216_000, kind="charge",
                      period=THIS, note="Guruh — 6 dars [dars:6]",
                      created_by="avtomat (oylik)"))
db.add(models.Discount(student_id=B, kind="individual", percent=10,
                       reason="Sinov", status="active",
                       start_date=today.replace(day=1),
                       requested_by="Asoschi", approved_by="Asoschi"))
db.commit(); db.close()
before = charge(B, THIS)
r = c.post(f"/api/students/{B}/freeze", headers=H,
           json={"until": (today + timedelta(days=30)).isoformat(),
                 "reason": "other"})
after = charge(B, THIS)
ck("muzlatildi", r.status_code, 200)
ck("qarz oshmadi", after <= before, True)
print("   muzlatishdan oldin:", before, "· keyin:", after)

print("\n=== 3. Aka-ukadan biri muzlatilsa, chegirma saqlanadi ===")
db = SessionLocal()
K1 = student("Aka")
K2 = student("Uka")
p = models.Parent(full_name="Oila", branch_id=BID)
db.add(p); db.commit()
for kid in (K1, K2):
    st = db.query(models.Student).get(kid)
    st.parent_id = p.id
db.commit()
s1 = db.query(models.Student).get(K1)
ck("ikkalasi faol — chegirma bor",
   common._family_discount_percent(db, s1), 10.0)
s2 = db.query(models.Student).get(K2)
s2.status = "frozen"
db.commit()
ck("uka muzlatilgach ham chegirma saqlandi",
   common._family_discount_percent(db, s1), 10.0)
s2.status = "archived"
db.commit()
ck("arxivga o'tsa chegirma yo'qoladi",
   common._family_discount_percent(db, s1), 0.0)
db.close()

print("\nJAMI XATO:", len(fails), fails)
sys.exit(1 if fails else 0)
