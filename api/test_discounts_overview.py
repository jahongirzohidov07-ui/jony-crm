"""CHEGIRMALAR BO'LIMI (2026-09-17).

Jahongir: "chegirmalar degan bo'limni ham qo'shish kerak ...
chegirmadagilar korinishi kerak". /api/discounts/overview: hamma
chegirmalar, oyiga taxminiy summa, filial kesimi.
"""
import os
import sys
import tempfile
from datetime import date

_DIR = os.path.join(tempfile.gettempdir(), "discounts_overview_test")
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
b1 = models.Branch(name="Bekobod 1"); b2 = models.Branch(name="Bekobod 2")
db.add_all([b1, b2]); db.commit()
B1, B2 = b1.id, b2.id
db.add_all([
    models.User(username="asos", password_hash=hash_password("x"),
                full_name="Asoschi", role=roles.FOUNDER),
    models.User(username="adm", password_hash=hash_password("x"),
                full_name="Admin", role=roles.ADMINISTRATOR, branch_id=B1),
    models.User(username="ustoz", password_hash=hash_password("x"),
                full_name="Ustoz", role=roles.TEACHER, branch_id=B1),
])
g = models.Group(name="Cambridge", branch_id=B1, lesson_price=50000,
                 standard_lessons_per_month=12, monthly_fee=600000)
db.add(g); db.commit()
s1 = models.Student(full_name="Ali", branch_id=B1, status="active",
                    group_id=g.id)
s2 = models.Student(full_name="Vali", branch_id=B2, status="active")
db.add_all([s1, s2]); db.commit()
db.add_all([
    models.Discount(student_id=s1.id, kind="individual", percent=20,
                    reason="Yaxshi o'qiydi", status="active",
                    start_date=date(2026, 1, 1), requested_by="Admin",
                    approved_by="Asoschi"),
    models.Discount(student_id=s1.id, kind="individual", amount=50000,
                    reason="So'rov", status="pending",
                    requested_by="Admin"),
    models.Discount(student_id=s2.id, kind="individual", percent=10,
                    reason="Boshqa filial", status="active",
                    start_date=date(2026, 1, 1)),
])
db.commit(); db.close()


def tok(u):
    return {"Authorization": "Bearer " + c.post(
        "/api/auth/login", json={"username": u, "password": "x"}
    ).json()["access_token"]}


r = c.get("/api/discounts/overview", headers=tok("asos"))
ck("asoschi 200", r.status_code, 200)
d = r.json()
ck("hamma chegirmalar", len(d["rows"]), 3)
ali = next(x for x in d["rows"] if x["status"] == "active"
           and x["student_name"] == "Ali")
ck("20% dan oyiga 120 000", ali["monthly"], 120000)
ck("guruh nomi", ali["group"], "Cambridge")
ck("kim tasdiqlagan", ali["approved_by"], "Asoschi")
ck("amaldagi o'quvchilar", d["summary"]["students"], 2)
ck("kutayotgan", d["summary"]["pending"], 1)
ck("tasdiqlay oladi", d["can_approve"], True)

r = c.get("/api/discounts/overview", headers=tok("adm"))
ck("admin faqat o'z filiali",
   sorted({x["student_name"] for x in r.json()["rows"]}), ["Ali"])
ck("admin tasdiqlay olmaydi", r.json()["can_approve"], False)

ck("ustozga yopiq",
   c.get("/api/discounts/overview", headers=tok("ustoz")).status_code, 403)

print()
if fails:
    print(f"XATOLAR ({len(fails)}): " + ", ".join(fails))
    sys.exit(1)
print("HAMMASI O'TDI")
