"""PUL OQIMI: OLDINGI OYDAN QOLDIQ (2026-10-02).

Jahongir: "Pul oqimi bo'limiga JonySchoolga o'xshab qoldiqlar keyingi
oydan o'tsin, click, naqd va terminalniki". Qoldiq 1-sentabr 2026 dan
yuritiladi (undan oldingisi import — hisobga olinmaydi).

Tekshiriladi:
  1. Oktabr: oy boshida usul bo'yicha "Oldingi oydan qoldiq" qatorlari
     (sentabr kirimi − xarajat − berilgan ustoz oyligi); avgust kirmaydi;
     qoldiq kirim/chiqim jamiga qo'shilmaydi; Kassa = qoldiq + kirim −
     chiqim.
  2. Sentabr: qoldiq yo'q (hisob shu oydan boshlanadi).
  3. Avgust–oktabr oralig'i: har oy o'z qoldig'i bilan, avgust
     sentabrga o'tmaydi; jami kassa = oktabr oxiridagi pul.
  4. Boshqa filial ko'rinmaydi (filial chegarasi qoldiqqa ham amal
     qiladi).
"""
import os
import sys
import tempfile
from datetime import date, datetime

_DIR = os.path.join(tempfile.gettempdir(), "cashflow_opening_test")
os.makedirs(_DIR, exist_ok=True)
_DB = os.path.join(_DIR, "db.sqlite")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace(chr(92), "/")
if os.path.exists(_DB):
    os.remove(_DB)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                         # noqa: E402
import entry                                       # noqa: E402,F401
import common as _cm_stub                          # noqa: E402
from database import SessionLocal                  # noqa: E402
from auth import hash_password                     # noqa: E402

# Login oylik yechimni ishga tushiradi — bu test unga bog'liq emas
_cm_stub._ensure_month_charges = lambda db, **kw: None

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
b = models.Branch(name="Zafar"); db.add(b)
b2 = models.Branch(name="Bekobod"); db.add(b2); db.commit()
db.add(models.User(username="asos", password_hash=hash_password("x"),
                   full_name="Asoschi", role=roles.FOUNDER))
db.add(models.User(username="adm", password_hash=hash_password("x"),
                   full_name="Admin", role=roles.SALES_MANAGER,
                   branch_id=b2.id))
s = models.Student(full_name="Ali", branch_id=b.id, status="active")
s2 = models.Student(full_name="Vali", branch_id=b2.id, status="active")
t = models.Teacher(full_name="Elena", is_active=1, branch_id=b.id)
db.add_all([s, s2, t]); db.commit()
BID = b.id


def pay(st, amt, method, d):
    db.add(models.Payment(student_id=st.id, amount=amt, kind="payment",
                          method=method, created_at=datetime(*d, 7)))


# Avgust — hisobga OLINMAYDI (qoldiq sentabrdan)
pay(s, 1_000_000, "cash", (Y, 8, 15))
# Sentabr
pay(s, 500_000, "cash", (Y, 9, 10))
pay(s, 300_000, "card", (Y, 9, 12))
pay(s, 200_000, "terminal", (Y, 9, 20))
db.add(models.Expense(date=date(Y, 9, 25), category="rent", amount=100_000,
                      branch_id=b.id, method="cash"))
db.add(models.TeacherPayment(teacher_id=t.id, amount=50_000, kind="salary",
                             paid_on=date(Y, 9, 28), method="card"))
# Hisob yozuvi (charge) kassaga kirmaydi
db.add(models.Payment(student_id=s.id, amount=-480_000, kind="charge",
                      period=f"{Y}-09", created_at=datetime(Y, 9, 1, 7)))
# Oktabr
pay(s, 40_000, "cash", (Y, 10, 2))
# Boshqa filial — sentabr
pay(s2, 700_000, "cash", (Y, 9, 11))
db.commit()
db.close()


def tok(u):
    return {"Authorization": "Bearer " + client.post(
        "/api/auth/login", json={"username": u, "password": "x"}
    ).json()["access_token"]}


H = tok("asos")
URL = "/api/reports/cashflow-ledger"

print("=== 1. Oktabr (bitta filial) ===")
d = client.get(f"{URL}?year={Y}&month=10&branch_id={BID}", headers=H).json()
ck("qoldiq usullar bo'yicha",
   {k: d["opening"][k] for k in ("cash", "card", "terminal")},
   {"cash": 400_000, "card": 250_000, "terminal": 200_000})
ck("qoldiq jami", d["opening"]["total"], 850_000)
bal = [r for r in d["rows"] if r["direction"] == "balance"]
ck("qoldiq qatorlari", sorted((r["method"], r["amount"]) for r in bal),
   [("card", 250_000), ("cash", 400_000), ("terminal", 200_000)])
ck("qatorlar 1-oktabrda", {r["date"] for r in bal}, {f"{Y}-10-01"})
ck("izoh — qaysi oydan", {r["title"] for r in bal} | {r["note"] for r in bal},
   {"Oldingi oydan qoldiq", f"{Y}-09"})
ck("kirim faqat oktabr", d["kirim"]["total"], 40_000)
ck("chiqim yo'q", d["chiqim"]["total"], 0)
ck("kassa = qoldiq + kirim − chiqim (naqd)", d["kassa"]["cash"], 440_000)
ck("kassa jami", d["kassa"]["total"], 890_000)

print("\n=== 2. Sentabr — hisob boshlanishi ===")
d = client.get(f"{URL}?year={Y}&month=9&branch_id={BID}", headers=H).json()
ck("qoldiq 0", d["opening"]["total"], 0)
ck("qoldiq qatori yo'q",
   [r for r in d["rows"] if r["direction"] == "balance"], [])
ck("kassa = sentabr kirim − chiqim", d["kassa"]["total"], 850_000)

print("\n=== 3. Avgust–oktabr ===")
d = client.get(f"{URL}?year={Y}&month=8&to_year={Y}&to_month=10"
               f"&branch_id={BID}", headers=H).json()
ck("oylar: qoldiq va kassa",
   [(m["period"], m["opening"], m["kassa"]) for m in d["months"]],
   [(f"{Y}-08", 0, 1_000_000), (f"{Y}-09", 0, 850_000),
    (f"{Y}-10", 850_000, 890_000)])
ck("faqat oktabrda qoldiq qatori",
   {r["date"] for r in d["rows"] if r["direction"] == "balance"},
   {f"{Y}-10-01"})
ck("jami kassa — oktabr oxiri", d["kassa"]["total"], 890_000)

print("\n=== 4. Filial chegarasi ===")
d = client.get(f"{URL}?year={Y}&month=10", headers=tok("adm")).json()
ck("boshqa filial admini — faqat o'z qoldig'i", d["opening"]["total"],
   700_000)

print()
if fails:
    print(f"{len(fails)} ta XATO: {fails}")
    sys.exit(1)
print("HAMMASI OK")
