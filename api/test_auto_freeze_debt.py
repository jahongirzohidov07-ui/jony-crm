"""AVTOMUZLATISHDA OY HISOBI QAYTA HISOBLANADI (2026-09-25).

Jahongir: "muzlatilgan oquvchida katta qarzdorlik qolib ketyabdi".

Sabab: ketma-ket 3 darsga kelmagan o'quvchi avtomat muzlatilganda oy
hisobini kamaytiradigan kod (_af_recount) bor edi, lekin u JONLI
TIZIMDA hech qachon ishlamasdi — `_af_install()` faqat "common",
"system", "main" modullarini yamardi, avtomuzlatishni chaqiradigan
groups_lessons.py esa funksiyaning eski nusxasini ushlab turardi.
Natijada oy boshida yechilgan to'liq summa qarz bo'lib qolaverardi.

Tekshiriladi:
  1) yamoq avtomuzlatish chaqiradigan modulga ham tushgan;
  2) 6 ta dars o'tib, oxirgi 3 tasiga kelmagan o'quvchi avtomat
     muzlatiladi va oy hisobi o'tilgan darslar bo'yicha kamayadi;
  3) muzlatilgandan keyin oylik dvigatel yangi pul yechmaydi.
"""
import os
import sys
import tempfile
from datetime import date

_DIR = os.path.join(tempfile.gettempdir(), "auto_freeze_debt_test")
os.makedirs(_DIR, exist_ok=True)
_DB = os.path.join(_DIR, "db.sqlite")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace(chr(92), "/")
if os.path.exists(_DB):
    os.remove(_DB)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                         # noqa: E402
import entry                                       # noqa: E402
import groups_lessons                              # noqa: E402
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

print("=== 1. Yamoq avtomuzlatish moduliga tushdimi ===")
ck("groups_lessons yamalgan",
   getattr(groups_lessons._freeze_task, "_af_new", False), True)

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

s = models.Student(full_name="Kelmay qo'ygan bola", branch_id=BID,
                   group_id=GID, status="active",
                   enrolled_date=today.replace(day=1))
db.add(s); db.commit()
SID = s.id
db.add(models.StudentGroupLink(student_id=SID, group_id=GID,
                               is_primary=1, active=1))
# Oy boshida to'liq oylik yechilgan
db.add(models.Payment(student_id=SID, amount=-480_000, kind="charge",
                      period=PERIOD, note="Guruh — 12 dars",
                      created_by="avtomat (oylik)"))
# Shu oyning 1-6 kunlari dars
les = []
for d in range(1, 7):
    ln = models.Lesson(group_id=GID, teacher_id=TID,
                       date=date(today.year, today.month, d), held=1)
    db.add(ln); db.commit()
    les.append(ln.id)
db.commit(); db.close()


def charge():
    s2 = SessionLocal()
    p = (s2.query(models.Payment)
         .filter(models.Payment.student_id == SID,
                 models.Payment.kind == "charge",
                 models.Payment.period == PERIOD).first())
    out = int(abs(p.amount)) if p else None
    s2.close()
    return out


def status():
    s2 = SessionLocal()
    st = s2.query(models.Student).get(SID)
    out = st.status
    s2.close()
    return out


H = {"Authorization": "Bearer " + c.post(
    "/api/auth/login", json={"username": "asos", "password": "x"}
).json()["access_token"]}

print("\n=== 2. Dastlabki holat ===")
ck("hisob to'liq", charge(), 480_000)
ck("holat faol", status(), "active")

print("\n=== 3. 3 ta darsga keldi, keyingi 3 tasiga kelmadi ===")
for i, lid in enumerate(les):
    r = c.put(f"/api/lessons/{lid}/attendance", headers=H,
              json={"marks": [{"student_id": SID,
                               "present": 1 if i < 3 else 0}]})
    if r.status_code >= 400:
        print("   yo'qlama xatosi:", r.status_code, r.text[:140])
        break

ck("avtomat muzlatildi", status(), "frozen")
got = charge()
ck("qarz o'tilgan darslar bo'yicha kamaydi",
   got is not None and got < 480_000, True)
print("   hisob:", got, "(oy boshida 480 000 edi)")

print("\n=== 4. Muzlatilgach yangi pul yechilmaydi ===")
db = SessionLocal()
before = charge()
entry._mc_ensure(db, budget_s=10.0)
db.commit(); db.close()
ck("hisob o'zgarmadi", charge(), before)

print("\nJAMI XATO:", len(fails), fails)
sys.exit(1 if fails else 0)
