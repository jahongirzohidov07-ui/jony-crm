"""USTOZ ALMASHGANDA DARSLAR (2026-10-03).

Jahongir: "oylik bo'limida Rayxona Xoshimova turibdi, lekin Bekobod 1da
Rayxona Abdujalilova; Xoshimova avgustda ishdan bo'shagan".

Sabab: oy boshida butun oyning darslari guruhning o'sha paytdagi ustozi
nomida yaratiladi; guruh boshqa ustozga o'tsa ham ular eski ustozda
qolib, yoqlama qo'yilganda pul eski ustozga yozilardi.

Tekshiriladi:
  1. Guruh ustozi almashsa — o'tilmagan darslar yangi ustozga,
     o'tilgan dars eski ustozda qoladi.
  2. Dars ishdan ketgan ustoz nomida qolgan bo'lsa, yoqlama qo'yilganda
     guruhning hozirgi ustoziga yoziladi; faol boshqa ustoz (o'rinbosar)
     nomidagi darsga tegilmaydi.
"""
import os
import sys
import tempfile
from datetime import timedelta

_DB = os.path.join(tempfile.gettempdir(), "teacher_change_lessons.db")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace("\\", "/")
if os.path.exists(_DB):
    os.remove(_DB)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                         # noqa: E402
import entry  # noqa: F401,E402
import common                                      # noqa: E402
import groups_lessons as GL                        # noqa: E402
from database import SessionLocal                  # noqa: E402
from auth import hash_password                     # noqa: E402

common._ensure_month_charges = lambda db, **kw: None
c = TestClient(main.app)
fails = []


def ck(name, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + name + f": {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


T = roles.local_today()
db = SessionLocal()
b = models.Branch(name="Bekobod 1"); db.add(b); db.commit()
db.add(models.User(username="asos", password_hash=hash_password("x"),
                   full_name="Asoschi", role=roles.FOUNDER, is_active=1))
old = models.Teacher(full_name="Xoshimova Rayxona", branch_id=b.id, is_active=1)
new = models.Teacher(full_name="Abdujalilova Rayxona", branch_id=b.id, is_active=1)
sub = models.Teacher(full_name="O'rinbosar", branch_id=b.id, is_active=1)
db.add_all([old, new, sub]); db.commit()
OLD, NEW, SUB = old.id, new.id, sub.id
g = models.Group(name="G", branch_id=b.id, teacher_id=OLD, lesson_price=40_000,
                 lesson_days="mon,tue,wed,thu,fri,sat,sun", lesson_time="09:00")
db.add(g); db.commit(); GID = g.id
d0 = T - timedelta(days=2)
done = models.Lesson(group_id=GID, teacher_id=OLD, date=d0, held=1)
fut = [models.Lesson(group_id=GID, teacher_id=OLD, date=T + timedelta(days=i),
                     held=0, created_by="avtomat") for i in range(1, 4)]
db.add(done); db.add_all(fut); db.commit()
DONE, FUT = done.id, [l.id for l in fut]
db.close()

H = {"Authorization": "Bearer " + c.post("/api/auth/login", json={
    "username": "asos", "password": "x"}).json()["access_token"]}

print("=== 1. Ustoz almashdi ===")
r = c.put(f"/api/groups/{GID}?force=true", headers=H, json={"teacher_id": NEW})
ck("saqlandi", r.status_code, 200)
s = SessionLocal()
ck("o'tilmagan darslar yangi ustozda",
   [s.query(models.Lesson).get(i).teacher_id for i in FUT], [NEW] * 3)
ck("o'tilgan dars eski ustozda", s.query(models.Lesson).get(DONE).teacher_id, OLD)

print("\n=== 2. Ishdan ketgan ustoz nomidagi dars ===")
s.query(models.Teacher).get(OLD).is_active = 0
l1 = models.Lesson(group_id=GID, teacher_id=OLD, date=T + timedelta(days=9),
                   held=0, created_by="avtomat")
l2 = models.Lesson(group_id=GID, teacher_id=SUB, date=T + timedelta(days=10),
                   held=0, created_by="avtomat")
s.add_all([l1, l2]); s.commit()
GL._mark_lesson_held(s, l1)
GL._mark_lesson_held(s, l2)
s.commit()
ck("ketgan ustoz darsi — guruhning hozirgi ustoziga", l1.teacher_id, NEW)
ck("faol o'rinbosar darsiga tegilmaydi", l2.teacher_id, SUB)
s.close()

print()
if fails:
    print(f"{len(fails)} ta XATO: {fails}")
    sys.exit(1)
print("HAMMASI OK")
