"""QO'SHIMCHA LAVOZIM "EXAMINER" (2026-10-07).

Jahongir: "examinerlarni valantyordan juniorga o'zgartirgandim, examlar
ko'rinmay qoldi ularga buyurtmalar" -> "mahbuba va Jasmina examinerlarda
ko'rinmayabdi ekan".

Holat: asosiy lavozimi boshqa (ustoz), examinerlik — qo'shimcha lavozim.
Tekshiriladi:
  1. HR -> Examinerlar (staff-grades?only=examiner) ro'yxatida bor,
     lavozimi "O'qituvchi + Examiner"; junior qilish o'tadi.
  2. Ustoz buyurtma yuborsa — unga ham vazifa tushadi.
  3. Lavozimni "Examiner"ga almashtirsa — buyurtmani ko'radi va qabul
     qiladi; oyligi (junior) yashirin emas.
  4. Examiner oyliklari ro'yxatida bor; ball ayirish o'tadi.
  5. Examinerligi yo'q ustoz — ro'yxatlarda yo'q.
"""
import os
import sys
import tempfile
from datetime import date, timedelta

_DIR = os.path.join(tempfile.gettempdir(), "examiner_extra_role_test")
os.makedirs(_DIR, exist_ok=True)
_DB = os.path.join(_DIR, "db.sqlite")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace(chr(92), "/")
if os.path.exists(_DB):
    os.remove(_DB)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                         # noqa: E402
import entry                                       # noqa: E402,F401
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


def user(login, name, role, extra=()):
    u = models.User(username=login, password_hash=hash_password("x"),
                    full_name=name, role=role, branch_id=b.id, is_active=1)
    db.add(u); db.commit()
    for r in extra:
        db.add(models.UserRole(user_id=u.id, role=r))
    db.commit()
    return u


user("hr", "HR", roles.HR_MANAGER)
user("asos", "Asoschi", roles.FOUNDER)
mah = user("mah", "Mahbuba", roles.TEACHER, extra=[roles.EXAMINER])
user("jas", "Jasmina", roles.EXAMINER)               # asosiy examiner
ut = user("ust", "Oddiy Ustoz", roles.TEACHER)
t = models.Teacher(full_name="Oddiy Ustoz", branch_id=b.id, user_id=ut.id,
                   is_active=1)
db.add(t); db.commit()
g = models.Group(name="G1", branch_id=b.id, teacher_id=t.id,
                 lesson_time="09:00", lesson_days="mon,wed,fri",
                 monthly_fee=480_000)
db.add(g); db.commit()
db.add(models.Student(full_name="S1", branch_id=b.id, group_id=g.id,
                      status="active"))
db.commit()
MAH, GID = mah.id, g.id


def H(u, role=None):
    r = c.post("/api/auth/login", json={"username": u, "password": "x"})
    h = {"Authorization": "Bearer " + r.json()["access_token"]}
    if role:
        h["X-Active-Role"] = role
    return h


HR, HF, HU = H("hr"), H("asos"), H("ust")

print("=== 1. HR -> EXAMINERLAR ===")
rows = c.get("/api/staff-grades?only=examiner", headers=HR).json()["rows"]
by = {r["name"]: r for r in rows}
ck("ikkalasi ro'yxatda", sorted(by), ["Jasmina", "Mahbuba"])
ck("lavozim yozuvi", by["Mahbuba"]["role"], "O'qituvchi + Examiner")
ck("oddiy ustoz yo'q", "Oddiy Ustoz" in by, False)
r = c.put(f"/api/staff-grades/{MAH}", headers=HR, json={"grade": "junior"})
ck("junior qilindi", r.status_code, 200)

print("\n=== 2. BUYURTMA XABARI ===")
when = (date.today() + timedelta(days=3)).isoformat()
r = c.post("/api/me/exam-orders", headers=HU,
           json={"group_id": GID, "date": when, "kind": "unit", "unit_no": 2})
ck("buyurtma yuborildi", r.status_code, 200)
OID = r.json()["id"]
db.expire_all()
t_mah = [x.title for x in db.query(models.Task)
         .filter(models.Task.assignee_id == MAH).all()]
ck("Mahbubaga vazifa tushdi", any("Imtihon buyurtmasi" in x for x in t_mah),
   True)

print("\n=== 3. EXAMINER SIFATIDA ===")
HM = H("mah", roles.EXAMINER)
r = c.get("/api/exam-orders", headers=HM)
ck("buyurtmalarni ko'radi", (r.status_code,
                              [x["id"] for x in r.json().get("rows", [])]),
   (200, [OID]))
r = c.post(f"/api/exam-orders/{OID}/accept", headers=HM, json={})
ck("qabul qiladi", r.status_code, 200)
me = c.get("/api/me", headers=HM).json()
ck("junior — oylik yashirin emas", me.get("salary_hidden"), False)

print("\n=== 4. OYLIKLAR VA BALL ===")
r = c.get("/api/examiners/salary", headers=HF)
names = {x["name"]: x["role"] for x in r.json()["rows"]}
ck("oyliklar ro'yxatida", names.get("Mahbuba"), "O'qituvchi + Examiner")
r = c.post("/api/examiner-adjustments", headers=HF,
           json={"user_id": MAH, "points": 5, "reason": "kechikdi"})
ck("ball ayirish o'tadi", r.status_code, 200)

print("\n=== 5. FILIAL FILTRI (HR -> Oyliklar) ===")
b2 = models.Branch(name="Boshqa"); db.add(b2); db.commit()
for url in ("/api/examiners/salary", "/api/support/salary"):
    r = c.get(f"{url}?branch_id={b.id}", headers=HF)
    ck(f"{url} o'z filiali 200", r.status_code, 200)
r = c.get(f"/api/examiners/salary?branch_id={b.id}", headers=HF).json()
ck("o'z filialida Mahbuba bor",
   "Mahbuba" in {x["name"] for x in r["rows"]}, True)
r = c.get(f"/api/examiners/salary?branch_id={b2.id}", headers=HF).json()
ck("boshqa filialda bo'sh", len(r["rows"]), 0)
ck("boshqa filial jami 0", r.get("total") or 0, 0)

print("\n=== 6. VOLONTYORLAR PASTDA ===")
vol = models.User(username="vol1", password_hash=hash_password("x"),
                  full_name="Aaa Volontyor", role=roles.EXAMINER,
                  branch_id=b.id, is_active=1)
db.add(vol); db.commit()
for url in ("/api/examiners/salary", "/api/support/salary"):
    rows = c.get(url, headers=HF).json()["rows"]
    flags = [float(x.get("grade_coef", 1)) == 0 for x in rows]
    ck(f"{url}: volontyorlar oxirida", flags == sorted(flags), True)
rows = c.get("/api/examiners/salary", headers=HF).json()["rows"]
names = [x["name"] for x in rows]
vi = names.index("Aaa Volontyor")
ck("Mahbuba (junior) volontyordan oldin", names.index("Mahbuba") < vi, True)
ck("volontyor oyligi hamon 0", rows[vi].get("salary"), 0)

print()
if fails:
    print(f"XATO: {len(fails)} ta tekshiruv o'tmadi")
    for x in fails:
        print("   - " + x)
    sys.exit(1)
print("HAMMASI O'TDI")
sys.exit(0)
