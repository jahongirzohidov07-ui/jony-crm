"""ADMINISTRATORGA PUL OQIMI VA XARAJATLAR (2026-08-10).

Jahongir: "administratorlarga cashflow bo'limini ochib ber va
xarajatlarni kirgizishni ham ochib ber."

CHEGARA ATAYLAB SAQLANDI: administrator kunlik kassa bilan
ishlaydi — kirim-chiqimni ko'radi va mayda xarajat kiritadi.
Foyda-zarar, budjet va oyliklar unga OCHILMADI; xarajatni
O'CHIRISH ham moliyada qoldi (o'chirish pul hisobotini
o'zgartiradi)."""
import os, sys
from datetime import date

os.environ["DATABASE_URL"] = "sqlite:////tmp/vac/db.sqlite"
os.makedirs("/tmp/vac", exist_ok=True)
if os.path.exists("/tmp/vac/db.sqlite"):
    os.remove("/tmp/vac/db.sqlite")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
import main, models, roles
import entry  # noqa
from database import SessionLocal
from auth import hash_password

c = TestClient(main.app)
db = SessionLocal()
fails = []


def ck(n, g, w):
    ok = g == w
    print(("OK  " if ok else "XATO ") + f"{n}: {g}" + ("" if ok else f"  (kutilgan {w})"))
    if not ok:
        fails.append(n)


b = models.Branch(name="Zafar"); db.add(b); db.commit()


def mk(u, r):
    x = models.User(username=u, full_name=f"X {u}",
                    password_hash=hash_password("Parol123!"),
                    role=r, branch_id=b.id, is_active=1)
    db.add(x); db.commit(); return x


mk("adm", roles.ADMINISTRATOR)
mk("sm", roles.SALES_MANAGER)
mk("dir", roles.FOUNDER)
mk("ust", roles.TEACHER)


def H(u):
    return {"Authorization": f"Bearer {c.post('/api/auth/login', json={'username':u,'password':'Parol123!'}).json()['access_token']}"}


today = date.today()

print("=== PUL OQIMI ===")
for u, lbl in (("adm", "Administrator"), ("sm", "Sotuv menejeri")):
    ck(f"{lbl}: /reports/cashflow",
       c.get("/api/reports/cashflow?months=3", headers=H(u)).status_code, 200)
    ck(f"{lbl}: kassa daftari",
       c.get(f"/api/reports/cashflow-ledger?year={today.year}"
             f"&month={today.month}", headers=H(u)).status_code, 200)

ck("Ustoz: pul oqimi YOPIQ",
   c.get("/api/reports/cashflow", headers=H("ust")).status_code, 403)

print("\n=== XARAJATLAR ===")
ck("Administrator ro'yxatni ko'radi",
   c.get("/api/expenses", headers=H("adm")).status_code, 200)

r = c.post("/api/expenses", headers=H("adm"), json={
    "category": roles.EXPENSE_CATEGORIES[0], "amount": 250000,
    "date": today.isoformat(), "note": "Suv", "branch_id": b.id})
ck("Administrator xarajat KIRITADI", r.status_code, 200)
eid = r.json()["id"]
ck("bazada saqlandi",
   db.query(models.Expense).filter(models.Expense.id == eid).count(), 1)

r = c.put(f"/api/expenses/{eid}", headers=H("adm"),
          json={"amount": 300000})
ck("Administrator tuzata oladi", r.status_code, 200)

r = c.delete(f"/api/expenses/{eid}", headers=H("adm"))
ck("lekin O'CHIRA OLMAYDI (moliyada qoladi)", r.status_code, 403)
r = c.delete(f"/api/expenses/{eid}", headers=H("dir"))
ck("asoschi o'chiradi", r.status_code, 200)

ck("Ustoz xarajat kirita olmaydi",
   c.post("/api/expenses", headers=H("ust"), json={
       "category": roles.EXPENSE_CATEGORIES[0], "amount": 1000,
       "date": today.isoformat()}).status_code, 403)

print("\n=== CHEGARA: BOSHQA MOLIYA BO'LIMLARI YOPIQ ===")
for path, lbl in (("/api/reports/pnl?year=%d&month=%d" % (today.year, today.month),
                   "Foyda/zarar"),):
    r = c.get(path, headers=H("adm"))
    ck(f"{lbl} administratorga yopiq", r.status_code in (403, 404), True)

print("\n" + ("BARCHASI OK" if not fails else f"XATOLAR: {fails}"))
sys.exit(1 if fails else 0)
