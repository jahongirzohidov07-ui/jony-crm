"""ADMINISTRATOR OYLIK BERADI (2026-10-02).

Jahongir: "administratorlar oyliklarni berish mumkin bo'lsin xarajatlar
bo'limida kiritishda ular oylik kiritilsa hamma kerakli joyga ulanib
ko'rinib tursin". O'chirish/tuzatish — "faqat bera olsin".

Sabab: 2026-09-03 da hamma administratorlar SALES_MANAGER ga
birlashtirilgan, 09-16 dagi huquq esa eski ADMINISTRATOR ga qo'shilgan.

Tekshiriladi:
  1. Administrator (sales_manager) Xarajatlar orqali o'z filiali
     ustoziga oylik beradi -> ustozning oylik kartasida, xarajatlar
     ro'yxatida ("Ustoz oyligi") va Pul oqimida chiqim.
  2. O'z filiali xodimiga (administrator, HR...) -> xarajat, xodim
     oyliklari ro'yxatida.
  3. Boshqa filial ustozi/xodimiga — 403.
  4. Administrator berilgan oylikni o'chira / filialini tuzata
     olmaydi (403); asoschi o'chira oladi.
  5. Administrator umumiy oyliklar ro'yxatini (payroll) ko'rmaydi.
"""
import os
import sys
import tempfile
from datetime import date

_DIR = os.path.join(tempfile.gettempdir(), "admin_salary_pay_test")
os.makedirs(_DIR, exist_ok=True)
_DB = os.path.join(_DIR, "db.sqlite")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace(chr(92), "/")
if os.path.exists(_DB):
    os.remove(_DB)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                         # noqa: E402
import entry                                       # noqa: E402
import common as _cm_stub                          # noqa: E402
from database import SessionLocal                  # noqa: E402
from auth import hash_password                     # noqa: E402

_cm_stub._ensure_month_charges = lambda db, **kw: None

client = TestClient(main.app)
fails = []


def ck(name, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + name + f": {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


TODAY = roles.local_today()
db = SessionLocal()
a = models.Branch(name="Zafar"); bb = models.Branch(name="Bekobod")
db.add_all([a, bb]); db.commit()
A, B = a.id, bb.id


def mkuser(login, role, branch):
    u = models.User(username=login, password_hash=hash_password("x"),
                    full_name=login.upper(), role=role, branch_id=branch,
                    is_active=1)
    db.add(u); db.commit()
    return u.id


mkuser("asos", roles.FOUNDER, None)
mkuser("adm", roles.SALES_MANAGER, A)
HR_A = mkuser("hr_a", roles.HR_MANAGER, A)
HR_B = mkuser("hr_b", roles.HR_MANAGER, B)
ta = models.Teacher(full_name="Elena", is_active=1, branch_id=A)
tb = models.Teacher(full_name="Bobur", is_active=1, branch_id=B)
db.add_all([ta, tb]); db.commit()
TA, TB = ta.id, tb.id
db.close()


def tok(u):
    return {"Authorization": "Bearer " + client.post(
        "/api/auth/login", json={"username": u, "password": "x"}
    ).json()["access_token"]}


ADM, FND = tok("adm"), tok("asos")
D = TODAY.isoformat()


def spend(h, **kw):
    body = {"category": "admin_salary", "amount": 1_000_000, "date": D,
            "method": "cash", "branch_id": A}
    body.update(kw)
    return client.post("/api/expenses", headers=h, json=body)


print("=== 1. Ustozga oylik ===")
r = spend(ADM, teacher_id=TA)
ck("berildi", r.status_code, 200)
TP = -r.json().get("id", 0)
s = SessionLocal()
p = s.query(models.TeacherPayment).get(TP)
ck("ustozning oylik kartasida", (p.teacher_id, p.amount, p.branch_id)
   if p else None, (TA, 1_000_000, A))
ck("xarajat jadvaliga ikki marta tushmadi",
   s.query(models.Expense).count(), 0)
s.close()
lst = client.get(f"/api/expenses?year={TODAY.year}&month={TODAY.month}"
                 f"&with_teacher=1", headers=FND).json()
ck("xarajatlar ro'yxatida 'Ustoz oyligi'",
   [(x["category"], x["amount"]) for x in lst],
   [("teacher_salary", 1_000_000)])
cf = client.get(f"/api/reports/cashflow-ledger?year={TODAY.year}"
                f"&month={TODAY.month}", headers=FND).json()
ck("Pul oqimida chiqim", [(x["category"], x["amount"]) for x in cf["rows"]
                          if x["direction"] == "out"],
   [("teacher_salary", 1_000_000)])

print("\n=== 2. Xodimga oylik ===")
r = spend(ADM, staff_user_id=HR_A, amount=3_000_000)
ck("berildi", r.status_code, 200)
st = client.get(f"/api/expenses/staff-salaries?year={TODAY.year}"
                f"&month={TODAY.month}", headers=FND).json()
ck("xodim oyliklari ro'yxatida", [(x["user_id"], x["amount"])
                                  for x in st["rows"]], [(HR_A, 3_000_000)])

print("\n=== 3. Boshqa filial ===")
ck("boshqa filial ustozi — 403", spend(ADM, teacher_id=TB).status_code, 403)
ck("boshqa filial xodimi — 403",
   spend(ADM, staff_user_id=HR_B).status_code, 403)

print("\n=== 4. O'chirish / tuzatish ===")
ck("admin o'chira olmaydi",
   client.delete(f"/api/teacher-payments/{TP}", headers=ADM).status_code, 403)
ck("admin filialini tuzata olmaydi",
   client.put(f"/api/teacher-payments/{TP}/branch", headers=ADM,
              json={"branch_id": B}).status_code, 403)
ck("asoschi o'chira oladi",
   client.delete(f"/api/teacher-payments/{TP}", headers=FND).status_code, 200)

print("\n=== 5. Umumiy oyliklar ===")
ck("admin hamma oyligini ko'rmaydi",
   "sales_manager" in entry._PAYROLL_VIEW, False)

print()
if fails:
    print(f"{len(fails)} ta XATO: {fails}")
    sys.exit(1)
print("HAMMASI OK")
