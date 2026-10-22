"""USTOZ CHEGARASIDAN ORTIQ GURUH — HR RUXSATI (2026-10-22).

Jahongir: "HRga ruxsat ber ustoz chegarasidan ortiq guruh
biriktirish uchun".

Guruhlar SONI chegarasida HR'ga "baribir saqlash" bor edi, lekin
KUNLIK DARS chegarasi ("Dushanba kuni ustozda 2 ta dars bo'ladi —
chegara 1 ta") qat'iy block edi — uni hech kim o'tkaza olmasdi.

Tekshiriladi:
  1. HR — kunlik chegaradan oshganda 409 ogohlantirish (can_force),
     "baribir saqlash" bilan guruh ochiladi.
  2. HR — guruhlar soni chegarasi ham avvalgidek o'tadi.
  3. Filial rahbari — kunlik chegarada qat'iy 400 (force ham yordam
     bermaydi); mavjud guruhning kunini o'zgartirib ham o'tolmaydi.
  4. Ustoz bir vaqtda ikki guruhda (to'qnashuv) — HR uchun ham block.
"""
import os
import sys
import tempfile

_DIR = os.path.join(tempfile.gettempdir(), "teacher_daily_limit_test")
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
for u, r in (("hr", roles.HR_MANAGER), ("rahbar", roles.BRANCH_MANAGER)):
    db.add(models.User(username=u, password_hash=hash_password("x"),
                       full_name=u, role=r, branch_id=b.id, is_active=1))
db.commit()
# Kuniga 1 ta dars, guruh soni cheklovi keng (10)
t = models.Teacher(full_name="Ustoz", branch_id=b.id, is_active=1,
                   max_groups=10, max_lessons_per_day=1)
db.add(t); db.commit()
g1 = models.Group(name="Ertalab", branch_id=b.id, teacher_id=t.id,
                  lesson_days="mon,wed", lesson_time="10:00",
                  lesson_price=1000, standard_lessons_per_month=12,
                  monthly_fee=12000)
db.add(g1); db.commit()


def tok(u):
    r = c.post("/api/auth/login", json={"username": u, "password": "x"})
    return {"Authorization": "Bearer " + r.json()["access_token"]}


def body(name, days="mon", time="14:00"):
    return {"name": name, "branch_id": b.id, "teacher_id": t.id,
            "lesson_days": days, "lesson_time": time, "lesson_price": 1000,
            "standard_lessons_per_month": 12, "monthly_fee": 12000}


H, R = tok("hr"), tok("rahbar")

print("=== 1. HR — KUNLIK CHEGARA ===")
r = c.post("/api/groups", headers=H, json=body("Kechki HR"))
d = r.json().get("detail", {})
ck("409 ogohlantirish", r.status_code, 409)
ck("baribir saqlash mumkin", d.get("can_force"), True)
ck("sabab — kunlik chegara", "kuni ustozda" in (d.get("message") or ""), True)
r = c.post("/api/groups?force=true", headers=H, json=body("Kechki HR"))
ck("force bilan ochildi", r.status_code, 200)

print("\n=== 2. HR — GURUHLAR SONI CHEGARASI ===")
t.max_groups = 1; db.commit()
r = c.post("/api/groups?force=true", headers=H,
           json=body("Yana biri", days="fri", time="09:00"))
ck("guruh soni chegarasidan ham o'tdi", r.status_code, 200)
t.max_groups = 10; db.commit()

print("\n=== 3. FILIAL RAHBARI — QAT'IY ===")
r = c.post("/api/groups?force=true", headers=R, json=body("Rahbar", days="wed"))
ck("kunlik chegara — 400", r.status_code, 400)
ck("Mumkin emas", (r.json().get("detail") or {}).get("message", "")[:11],
   "Mumkin emas")
g3 = models.Group(name="Juma", branch_id=b.id, teacher_id=t.id,
                  lesson_days="sat", lesson_time="12:00", lesson_price=1000,
                  standard_lessons_per_month=12, monthly_fee=12000)
db.add(g3); db.commit()
r = c.put(f"/api/groups/{g3.id}?force=true", headers=R,
          json={"lesson_days": "mon"})
ck("kunni o'zgartirib ham o'tolmaydi", r.status_code, 400)
r = c.put(f"/api/groups/{g3.id}", headers=R, json={"lesson_time": "13:00"})
ck("chegaraga tegmaydigan o'zgarish o'tadi", r.status_code, 200)

print("\n=== 4. TO'QNASHUV — HR UCHUN HAM BLOCK ===")
t.max_lessons_per_day = 10; db.commit()
r = c.post("/api/groups?force=true", headers=H,
           json=body("Bir vaqtda", days="mon", time="10:00"))
ck("ustoz bir vaqtda ikki guruhda — 400", r.status_code, 400)

print()
if fails:
    print(f"XATO: {len(fails)} ta tekshiruv o'tmadi")
    for x in fails:
        print("   - " + x)
    sys.exit(1)
print("HAMMASI O'TDI")
sys.exit(0)
