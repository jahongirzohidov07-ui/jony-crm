"""USTOZ YUKLAMASI CHEGARASI: STETCH RAHBARI "BARIBIR SAQLASH" (2026-10-03).

Jahongir: "shu joyda baribir ochilsin buyrug'i Stetch filial rahbariga
ham berilsin" (Ustozda 9 ta guruh bo'ladi — chegara 8 ta).

Tekshiriladi:
  1. Hamkor (Stetch) filial rahbari: chegaradan oshsa 409 ogohlantirish,
     force=true bilan guruh ochiladi.
  2. Oddiy filial rahbari — avvalgidek 400 (o'tolmaydi).
"""
import os
import sys
import tempfile

_DIR = os.path.join(tempfile.gettempdir(), "group_limit_partner_test")
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

common._ensure_month_charges = lambda db, **kw: None
c = TestClient(main.app)
fails = []


def ck(name, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + name + f": {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


db = SessionLocal()
st = models.Branch(name="Stetch", is_partner=1)
za = models.Branch(name="Zafar")
db.add_all([st, za]); db.commit()
ST, ZA = st.id, za.id
for login, br in (("stetch", ST), ("zafar", ZA)):
    db.add(models.User(username=login, password_hash=hash_password("x"),
                       full_name=login, role=roles.BRANCH_MANAGER,
                       branch_id=br, is_active=1))
db.commit()


def teacher(name, br):
    t = models.Teacher(full_name=name, branch_id=br, is_active=1)
    db.add(t); db.commit()
    for i in range(roles.TEACHER_MAX_GROUPS):
        db.add(models.Group(name=f"{name}{i}", branch_id=br, teacher_id=t.id,
                            lesson_time=f"{8 + i:02d}:00",
                            lesson_days="mon,wed,fri"))
    db.commit()
    return t.id


TS, TZ = teacher("Mukam", ST), teacher("Ali", ZA)
db.close()


def H(u):
    return {"Authorization": "Bearer " + c.post("/api/auth/login", json={
        "username": u, "password": "x"}).json()["access_token"]}


def new_group(h, tid, br, force=False):
    return c.post("/api/groups" + ("?force=true" if force else ""), headers=h,
                  json={"name": f"Yangi{tid}{force}", "teacher_id": tid,
                        "branch_id": br, "lesson_time": "18:00",
                        "lesson_days": "tue,thu,sat"})


print("=== 1. Stetch rahbari ===")
hs = H("stetch")
r = new_group(hs, TS, ST)
ck("ogohlantirish 409 (to'xtatilmaydi)", r.status_code, 409)
r = new_group(hs, TS, ST, force=True)
ck("baribir saqlash — ochildi", r.status_code, 200)

print("\n=== 2. Oddiy filial rahbari ===")
r = new_group(H("zafar"), TZ, ZA, force=True)
ck("o'tolmaydi", r.status_code, 400)

print()
if fails:
    print(f"{len(fails)} ta XATO: {fails}")
    sys.exit(1)
print("HAMMASI OK")
