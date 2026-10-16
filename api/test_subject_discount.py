"""FAN BO'YICHA CHEGIRMA (2026-10-16).

Jahongir: "xar bir fan alohida chegirma alohida muzlatish bo'lsin".
Muzlatish — link_freeze.py (alohida test). Bu yerda chegirma:
  1. Faqat bitta fanga berilgan chegirma — faqat o'sha fan "#g" qatori
     kamayadi, asosiy fan va uning foizi o'zgarmaydi.
  2. Asosiy fanga berilgan chegirma — faqat asosiy qator.
  3. Fan tanlanmagan chegirma — barcha fanlarga (avvalgidek).
  4. O'qimaydigan fanga — 400; javobda fan nomi.
  5. Fan chegirmasi keyingi oy (kunlik jarayon) ham o'sha fanga.
"""
import os
import sys
import tempfile
from datetime import date, datetime

_DIR = os.path.join(tempfile.gettempdir(), "subject_discount_test")
os.makedirs(_DIR, exist_ok=True)
_DB = os.path.join(_DIR, "db.sqlite")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace(chr(92), "/")
if os.path.exists(_DB):
    os.remove(_DB)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import roles                                        # noqa: E402
TODAY = date(2026, 10, 16)
roles.local_today = lambda: TODAY
roles.local_now = lambda: datetime(2026, 10, 16, 10, 0)

from fastapi.testclient import TestClient          # noqa: E402
import main, models                                # noqa: E402
import entry                                       # noqa: E402
import common                                      # noqa: E402
import multi_subject as MS                         # noqa: E402
import groups_lessons as GL                        # noqa: E402
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


db = SessionLocal()
b = models.Branch(name="Zafar"); db.add(b); db.commit()
db.add(models.User(username="asos", password_hash=hash_password("x"),
                   full_name="Asoschi", role=roles.FOUNDER, is_active=1))
tu = models.User(username="ust", password_hash=hash_password("x"),
                 full_name="Ustoz", role=roles.TEACHER, branch_id=b.id,
                 is_active=1)
db.add(tu); db.commit()
t = models.Teacher(full_name="Ustoz", branch_id=b.id, is_active=1,
                   user_id=tu.id)
db.add(t); db.commit()


def grp(name, price):
    g = models.Group(name=name, branch_id=b.id, teacher_id=t.id,
                     lesson_days="mon,wed,fri", lesson_time="14:00",
                     lesson_price=price, monthly_fee=price * 12,
                     standard_lessons_per_month=12)
    db.add(g); db.commit()
    return g


G1, G2, G3 = grp("IELTS", 40_000), grp("Matematika", 50_000), grp("X", 30_000)
for g in (G1, G2):
    GL._sync_scheduled_lessons(db, g, date(2026, 10, 1), date(2026, 10, 31))
db.commit()


def student(name):
    s = models.Student(full_name=name, branch_id=b.id, group_id=G1.id,
                       status="active", enrolled_date=date(2026, 9, 1))
    db.add(s); db.commit()
    db.add_all([
        models.StudentGroupLink(student_id=s.id, group_id=G1.id,
                                is_primary=1, active=1, status="active",
                                joined_date=date(2026, 9, 1)),
        models.StudentGroupLink(student_id=s.id, group_id=G2.id, active=1,
                                status="active",
                                joined_date=date(2026, 9, 1)),
        models.Payment(student_id=s.id, amount=-480_000, kind="charge",
                       period="2026-10", created_by=entry._MC_BY,
                       note="IELTS — 2026-10: 12 dars (standart oy, avtomat)"),
    ])
    db.commit()
    return s.id


A, B, C3 = student("Faqat matematikaga"), student("Faqat asosiyga"), \
    student("Hammasiga")
MS.daily(db, TODAY); db.commit()
K2 = MS.key("2026-10", G2.id)
H = {"Authorization": "Bearer " + c.post(
    "/api/auth/login", json={"username": "asos", "password": "x"}
).json()["access_token"]}


def rows(sid):
    db.expire_all()
    return {p.period: -p.amount for p in db.query(models.Payment)
            .filter(models.Payment.student_id == sid,
                    models.Payment.kind == "charge").all()}


def disc(sid, **kw):
    return c.post("/api/discounts", headers=H, json={
        "student_id": sid, "kind": "individual", "reason": "test", **kw})


r0 = rows(A)
ck("boshlang'ich: ikkala fanga 2-fan 10%", r0, {"2026-10": 432_000,
                                              K2: 540_000})

print("\n=== 1. FAQAT QO'SHIMCHA FANGA ===")
r = disc(A, percent=10, group_id=G2.id)
ck("yaratildi, fan nomi", (r.status_code, r.json().get("group_name")),
   (200, "Matematika"))
ck("faqat Matematika qatori: 600 000 x 80%", rows(A),
   {"2026-10": 432_000, K2: 480_000})
s = db.query(models.Student).get(A)
ck("asosiy foiz o'zgarmadi (10%)", common._student_discount_percent(db, s), 10)
ck("Matematika foizi 20%",
   common._student_discount_percent(db, s, group_id=G2.id), 20)

print("\n=== 2. FAQAT ASOSIY FANGA ===")
r = disc(B, percent=10, group_id=G1.id)
ck("yaratildi", (r.status_code, r.json().get("group_name")), (200, "IELTS"))
ck("faqat asosiy qator: 480 000 x 80%", rows(B),
   {"2026-10": 384_000, K2: 540_000})

print("\n=== 3. BARCHA FANLARGA ===")
r = disc(C3, percent=5)
ck("yaratildi, fan yo'q", (r.status_code, r.json().get("group_name")),
   (200, None))
ck("ikkala qator 15%", rows(C3), {"2026-10": 408_000, K2: 510_000})

print("\n=== 4. NOTO'G'RI FAN ===")
ck("o'qimaydigan fanga — 400",
   disc(A, percent=5, group_id=G3.id).status_code, 400)
# so'mli chegirma — o'sha fan narxiga nisbatan
s = db.query(models.Student).get(A)
r = disc(A, amount=60_000, group_id=G2.id)
ck("so'mli fan chegirmasi: 60 000 / 600 000 = +10%",
   (r.status_code,
    common._student_discount_percent(db, s, group_id=G2.id)), (200, 30))

print("\n=== 5. KEYINGI OY ===")
NOV = date(2026, 11, 2)
roles.local_today = lambda: NOV
for g in (G1, G2):
    GL._sync_scheduled_lessons(db, g, date(2026, 11, 1), date(2026, 11, 30))
db.commit()
MS.daily(db, NOV); db.commit()
ck("noyabr Matematika: 600 000 x 70%", rows(A).get(MS.key("2026-11", G2.id)),
   420_000)
ck("noyabr B (asosiyga chegirma) Matematika: 600 000 x 90%",
   rows(B).get(MS.key("2026-11", G2.id)), 540_000)

print()
if fails:
    print(f"XATO: {len(fails)} ta tekshiruv o'tmadi")
    for x in fails:
        print("   - " + x)
    sys.exit(1)
print("HAMMASI O'TDI")
sys.exit(0)
