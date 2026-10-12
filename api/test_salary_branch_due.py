"""OYLIK: QAYSI FILIALDAN BERILGAN BO'LSA O'SHANGA + SUMMA TAKLIFI
(2026-10-12).

Jahongir: "asliddinga berdim avtomat to'landi bo'lmayabdi" va
"oylik deb ustozni tanlaganda summa avtomat oyligidan kelib chiqib
paydo bo'lsin".

Tekshiriladi:
  * Bekobod 2 dan berilgan pul Bekobod 2 ro'yxatiga to'liq tushadi,
    Bekobod 1 dan berilgani Bekobod 1 ga (ulush bo'yicha bo'linmaydi);
  * filiali yo'q eski yozuv — avvalgidek ulush bo'yicha;
  * ustoz shu oy ishlamagan filialdan kiritilgan pul yo'qolmaydi;
  * sql va ctx yo'li bir xil;
  * /api/expenses/salary-due — xodim uchun fiks oylik minus berilgan.
"""
import os
import sys
import tempfile
from datetime import date

_DIR = os.path.join(tempfile.gettempdir(), "salary_branch_due_test")
os.makedirs(_DIR, exist_ok=True)
_DB = os.path.join(_DIR, "db.sqlite")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace(chr(92), "/")
if os.path.exists(_DB):
    os.remove(_DB)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient          # noqa: E402
import main, models, billing, common, roles        # noqa: E402,F401
from database import SessionLocal                  # noqa: E402
from auth import hash_password                     # noqa: E402

c = TestClient(main.app)
fails = []


def ck(n, g, w):
    ok = g == w
    print(("OK  " if ok else "XATO ") + n + f": {g}"
          + ("" if ok else f" (kutilgan {w})"))
    if not ok:
        fails.append(n)


db = SessionLocal()
b1 = models.Branch(name="Bekobod 1"); b2 = models.Branch(name="Bekobod 2")
b3 = models.Branch(name="Zafar")
db.add_all([b1, b2, b3]); db.commit()
B1, B2, B3 = b1.id, b2.id, b3.id
t = models.Teacher(full_name="Asliddin Nabiyev", branch_id=B2, is_active=1)
db.add(t); db.commit()
TID = t.id
P = "2026-09"
db.add_all([
    models.TeacherPayment(teacher_id=TID, amount=1_703_300, kind="salary",
                          period=P, paid_on=date(2026, 10, 12),
                          branch_id=B2),
    models.TeacherPayment(teacher_id=TID, amount=921_000, kind="salary",
                          period=P, paid_on=date(2026, 10, 9),
                          branch_id=B1),
])
db.add(models.User(username="asos", full_name="Asoschi", role=roles.FOUNDER,
                   password_hash=hash_password("x"), is_active=1))
adm = models.User(username="admin1", full_name="Admin Bir",
                  role=roles.ADMINISTRATOR, branch_id=B2, fix_salary=3_000_000,
                  password_hash=hash_password("x"), is_active=1)
db.add(adm); db.commit()
ADM = adm.id
db.add(models.Expense(category="admin_salary", amount=1_000_000,
                      staff_user_id=ADM, period=P, branch_id=B2,
                      date=date(2026, 10, 5)))
db.commit()

S, E = billing.month_bounds(2026, 9)
# Asliddin: B2 da 1 703 333, B1 da 921 000 ishlagan (jami 2 624 333)
PART_B2, WHOLE = 1_703_333.33, 2_624_333.33
WORKED = {B1, B2}


def scoped(branches, part, use_ctx, worked=WORKED):
    ctx = None
    if use_ctx:
        ctx = billing.PayrollContext(db)
        ctx.prefetch([TID])
    return common._teacher_paid_scoped(
        db, TID, since=S, until=E, ctx=ctx, period=P, branches=branches,
        part=part, whole=WHOLE, worked=worked)


for use_ctx in (False, True):
    tag = "ctx" if use_ctx else "sql"
    ck(f"[{tag}] Bekobod 2 ga faqat B2 dan berilgani",
       scoped({B2}, PART_B2, use_ctx), 1_703_300.0)
    ck(f"[{tag}] Bekobod 1 ga faqat B1 dan berilgani",
       scoped({B1}, WHOLE - PART_B2, use_ctx), 921_000.0)
    ck(f"[{tag}] barcha filiallar — hammasi",
       scoped(None, WHOLE, use_ctx), 2_624_300.0)

# Filiali yo'q eski yozuv — ulush bo'yicha
db.add(models.TeacherPayment(teacher_id=TID, amount=100_000, kind="salary",
                             period=P, paid_on=date(2026, 10, 1),
                             branch_id=None))
db.commit()
ck("filialsiz yozuv ulush bo'yicha qo'shiladi",
   scoped({B2}, PART_B2, False),
   round(1_703_300 + 100_000 * PART_B2 / WHOLE, 2))

# Ishlamagan filialdan (Zafar) kiritilgan pul — yo'qolmaydi, ulush
db.add(models.TeacherPayment(teacher_id=TID, amount=200_000, kind="salary",
                             period=P, paid_on=date(2026, 10, 2),
                             branch_id=B3))
db.commit()
ck("ishlamagan filial puli ham ulush bo'yicha",
   scoped({B2}, PART_B2, True),
   round(1_703_300 + 300_000 * PART_B2 / WHOLE, 2))
db.close()

print("=== salary-due ===")
h = {"Authorization": "Bearer " + c.post(
    "/api/auth/login", json={"username": "asos", "password": "x"}
).json()["access_token"]}
r = c.get(f"/api/expenses/salary-due?period={P}&user_id={ADM}", headers=h)
ck("status", r.status_code, 200)
j = r.json()
ck("xodim: fiks oylik", j.get("earned"), 3_000_000.0)
ck("xodim: berilgan", j.get("paid"), 1_000_000.0)
ck("xodim: qoldiq", j.get("due"), 2_000_000.0)
r = c.get(f"/api/expenses/salary-due?period={P}&teacher_id={TID}"
          f"&branch_id={B2}", headers=h)
ck("ustoz: javob beradi", r.status_code, 200)
ck("ustoz: darsi yo'q — qoldiq 0", r.json().get("due"), 0.0)
ck("noto'g'ri oy — 400",
   c.get(f"/api/expenses/salary-due?period=2026-13&user_id={ADM}",
         headers=h).status_code, 400)

print()
print("XATOLAR:", fails if fails else "yo'q")
sys.exit(1 if fails else 0)
