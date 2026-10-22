"""BO'LIM STATISTIKASI — /api/insights/{section} (2026-10-22).

Jahongir: "dars jadvali, support jadvali, talabalar, guruhlar,
o'qituvchilar, kutubxona, xodimlar, namunali xodim, audit, ombor,
tadbirlar, shaxsiy rivojlanish" — premium dizayn + grafiklar.

Tekshiriladi:
  1. Asoschi — 12 bo'limning hammasi 200, kartalar va grafiklar keladi,
     hech biri ichki xato sabab bo'sh qaytmaydi.
  2. Raqamlar to'g'ri: faol/sinov/muzlatilgan o'quvchi, guruh to'lishi,
     ombordagi kam qolgan material, namunali ball.
  3. Filial cheklovi: Zafar filial rahbari Chilonzor o'quvchilarini
     sanamaydi.
  4. Ruxsat: o'qituvchi auditni ko'rmaydi (403), o'quvchi hech narsani
     ko'rmaydi; oddiy xodim kutubxonada faqat o'z natijasini ko'radi.
"""
import os
import sys
import tempfile
from datetime import date, datetime

_DIR = os.path.join(tempfile.gettempdir(), "insights_test")
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
b1, b2 = models.Branch(name="Zafar"), models.Branch(name="Chilonzor")
db.add_all([b1, b2]); db.commit()
T = roles.local_today()


def user(login, role, br):
    u = models.User(username=login, password_hash=hash_password("x"),
                    full_name=login.capitalize(), role=role,
                    branch_id=br.id if br else None, is_active=1,
                    hired_date=T)
    db.add(u); db.commit()
    return u


user("asos", roles.FOUNDER, b1)
user("rahbar", roles.BRANCH_MANAGER, b1)
user("hr", roles.HR_MANAGER, None)
tu = user("ustoz", roles.TEACHER, b1)
user("admin", roles.SALES_MANAGER, b1)
user("bola", roles.STUDENT, b1)
t = models.Teacher(full_name="Ustoz", branch_id=b1.id, user_id=tu.id,
                   is_active=1, subject="english", hired_date=T)
db.add(t); db.commit()
g = models.Group(name="Step 1", branch_id=b1.id, teacher_id=t.id,
                 capacity=4, subject="english", lesson_price=45_000,
                 standard_lessons_per_month=12, monthly_fee=540_000)
db.add(g); db.commit()
for i, st in enumerate(["active", "active", "trial", "frozen"]):
    db.add(models.Student(full_name=f"Z{i}", branch_id=b1.id, group_id=g.id,
                          status=st, enrolled_date=T))
db.add(models.Student(full_name="C1", branch_id=b2.id, status="active",
                      enrolled_date=T))
db.add(models.Lesson(group_id=g.id, teacher_id=t.id, date=T, held=1))
db.add(models.Consumable(name="Marker", kind="stationery", branch_id=b1.id,
                         qty=1, min_qty=5))
db.add(models.Asset(name="Doska", kind="furniture", branch_id=b1.id,
                    condition="good", price=1_500_000))
db.add(models.Event(title="Bayram", kind="holiday", event_date=T,
                    branch_id=b1.id, status="planned", budget=300_000))
db.add(models.ConductViolation(user_id=tu.id, date=T, kind="late", points=5))
db.add(models.AuditLog(user_name="Asos", entity="student", action="update",
                       branch_id=b1.id, created_at=datetime.utcnow()))
db.add(models.LibraryItem(title="Kitob", kind="book", active=1, required=1))
db.commit()


def tok(u):
    r = c.post("/api/auth/login", json={"username": u, "password": "x"})
    return {"Authorization": "Bearer " + r.json()["access_token"]}


SECTIONS = ["hr", "timetable", "support", "students", "groups", "teachers",
            "library", "users", "namunali", "audit", "inventory", "events",
            "development"]
A = tok("asos")
print("=== 1. ASOSCHI — 12 BO'LIM ===")
got = {}
for s in SECTIONS:
    r = c.get(f"/api/insights/{s}", headers=A)
    d = r.json() if r.status_code == 200 else {}
    got[s] = d
    ck(f"{s}: 200 va to'liq", (r.status_code, bool(d.get("cards")),
                               bool(d.get("charts"))), (200, True, True))


def cv(sec, key):
    return next((x["value"] for x in got[sec]["cards"] if x["key"] == key), None)


print("\n=== 2. RAQAMLAR ===")
ck("faol o'quvchi (2 filial)", cv("students", "active"), 3)
ck("sinov", cv("students", "trial"), 1)
ck("muzlatilgan", cv("students", "frozen"), 1)
ck("guruh to'lishi 2/4", cv("groups", "fill"), "50%")
ck("bo'sh o'rin", cv("groups", "free"), 2)
ck("kam qolgan material", cv("inventory", "low"), 1)
ck("jihoz qiymati", cv("inventory", "value"), "1.5 mln")
ck("namunali: ayirilgan ball", cv("namunali", "pts"), 5)
ck("shu hafta dars", cv("timetable", "week"), 1)
ck("rejadagi tadbir", cv("events", "up"), 1)

print("\n=== 3. FILIAL CHEKLOVI ===")
r = c.get("/api/insights/students", headers=tok("rahbar")).json()
ck("Zafar rahbari faqat o'z filiali",
   next(x["value"] for x in r["cards"] if x["key"] == "active"), 2)

print("\n=== 4. RUXSAT ===")
U = tok("ustoz")
ck("ustoz auditni ko'rmaydi", c.get("/api/insights/audit", headers=U).status_code, 403)
ck("ustoz guruhlar statistikasini ko'radi",
   c.get("/api/insights/groups", headers=U).status_code, 200)
import insights                                    # noqa: E402
ck("o'quvchi/ota-ona xodim emas",
   [insights.is_staff(models.User(role=r)) for r in
    (roles.STUDENT, roles.PARENT, roles.TEACHER)], [False, False, True])
lib = c.get("/api/insights/library", headers=tok("admin")).json()
ck("admin kutubxonada o'z natijasi",
   [x["key"] for x in lib["cards"]], ["mine", "done", "req", "pct"])
ck("noma'lum bo'lim 404", c.get("/api/insights/yoq", headers=A).status_code, 404)

print()
if fails:
    print(f"XATO: {len(fails)} ta tekshiruv o'tmadi")
    for x in fails:
        print("   - " + x)
    sys.exit(1)
print("HAMMASI O'TDI")
sys.exit(0)
