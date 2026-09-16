"""PUL OQIMI ORALIQDA (2026-09-16).

Jahongir: "cashflow pul oqimini, faqat 1 oylikni koryabmiz shuni 2-3
oylikni toliq yillikni korsa boladigan qilib bergin".

Tekshiriladi:
  1. Bitta oy — avvalgidek (eski chaqiruv buzilmagan);
  2. Oraliq (3 oy) — hamma kirim/chiqim, oylar kesimi bo'sh oy bilan;
  3. Butun yil — 12 oy qatori;
  4. Teskari tanlangan oraliq ham ishlaydi, 24 oydan uzun — rad.
"""
import os
import sys
import tempfile
from datetime import date, datetime

_DIR = os.path.join(tempfile.gettempdir(), "cashflow_range_test")
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

client = TestClient(main.app)
fails = []


def ck(name, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + name + f": {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


Y = 2026
db = SessionLocal()
b = models.Branch(name="Bekobod 1"); db.add(b); db.commit()
db.add(models.User(username="asos", password_hash=hash_password("x"),
                   full_name="Asoschi", role=roles.FOUNDER))
s = models.Student(full_name="Ali", branch_id=b.id, status="active")
t = models.Teacher(full_name="Elena", is_active=1, branch_id=b.id)
db.add_all([s, t]); db.commit()
# Iyun: 500k kirim; Iyul: hech narsa; Avgust: 300k kirim, 100k xarajat,
# 50k ustoz oyligi
db.add(models.Payment(student_id=s.id, amount=500_000, kind="payment",
                      method="cash", created_at=datetime(Y, 6, 10, 9)))
db.add(models.Payment(student_id=s.id, amount=300_000, kind="payment",
                      method="card", created_at=datetime(Y, 8, 5, 9)))
db.add(models.Expense(date=date(Y, 8, 7), category="rent", amount=100_000,
                      branch_id=b.id, method="cash"))
db.add(models.TeacherPayment(teacher_id=t.id, amount=50_000, kind="salary",
                             paid_on=date(Y, 8, 20), method="cash"))
db.commit()
db.close()

H = {"Authorization": "Bearer " + client.post(
    "/api/auth/login", json={"username": "asos", "password": "x"}
).json()["access_token"]}
URL = "/api/reports/cashflow-ledger"

print("=== 1. Bitta oy (eski chaqiruv) ===")
d = client.get(f"{URL}?year={Y}&month=8", headers=H).json()
ck("avgust kirim", d["kirim"]["total"], 300_000)
ck("avgust chiqim (xarajat + ustoz oyligi)", d["chiqim"]["total"], 150_000)
ck("yozuvlar 3 ta", len(d["rows"]), 3)
ck("oylar kesimi 1 qator", len(d["months"]), 1)

print("\n=== 2. Iyun–avgust ===")
d = client.get(f"{URL}?year={Y}&month=6&to_year={Y}&to_month=8", headers=H).json()
ck("davr", (d["period"], d["period_to"]), (f"{Y}-06", f"{Y}-08"))
ck("jami kirim", d["kirim"]["total"], 800_000)
ck("jami kassa", d["kassa"]["total"], 650_000)
ck("yozuvlar 4 ta", len(d["rows"]), 4)
ck("3 oy qatori, bo'sh iyul ham",
   [(m["period"], m["kirim"], m["chiqim"]) for m in d["months"]],
   [(f"{Y}-06", 500_000, 0), (f"{Y}-07", 0, 0), (f"{Y}-08", 300_000, 150_000)])
ck("oy nomi", d["months"][0]["title"], "Iyun 2026")

print("\n=== 3. Butun yil ===")
d = client.get(f"{URL}?year={Y}&month=1&to_year={Y}&to_month=12", headers=H).json()
ck("12 oy", len(d["months"]), 12)
ck("yil kirimi", d["kirim"]["total"], 800_000)

print("\n=== 4. Teskari va juda uzun oraliq ===")
d = client.get(f"{URL}?year={Y}&month=8&to_year={Y}&to_month=6", headers=H).json()
ck("teskari ham iyun–avgust", (d["period"], d["period_to"], d["kirim"]["total"]),
   (f"{Y}-06", f"{Y}-08", 800_000))
r = client.get(f"{URL}?year={Y - 2}&month=1&to_year={Y}&to_month=12", headers=H)
ck("36 oy — rad", r.status_code, 400)

print()
if fails:
    print(f"XATOLAR ({len(fails)}): " + ", ".join(fails))
    sys.exit(1)
print("HAMMASI O'TDI")
