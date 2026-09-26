"""PUL BALANSINI TO'G'RILASH — faqat filial rahbari (2026-09-26).

Jahongir: "o'quvchi kartasiga balans tahrirlash qo'shib ber faqat
filial rahbariga ruxsat berilsin".

Tekshiriladi:
  1. Faqat filial rahbari: asoschi, moliya direktori, administrator,
     buxgalter — 403.
  2. Boshqa filial o'quvchisi — 403.
  3. Sabab majburiy.
  4. Farq "adjustment" yozuvi bo'lib qo'shiladi, eski yozuvlar
     o'zgarmaydi, balans aynan so'ralgan summa bo'ladi; ikkala tomonga
     (qarzni kamaytirish va ko'paytirish).
  5. Kassa (kind == "payment") yig'indisi o'zgarmaydi.
  6. Tuzatish yozuvini moliya direktori o'chira/o'zgartira olmaydi,
     filial rahbari o'chira oladi.
  7. Audit yoziladi; bir xil summa — o'zgarish yo'q.
"""
import os
import sys
import tempfile

_DIR = os.path.join(tempfile.gettempdir(), "balance_fix_test")
os.makedirs(_DIR, exist_ok=True)
_DB = os.path.join(_DIR, "db.sqlite")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace(chr(92), "/")
if os.path.exists(_DB):
    os.remove(_DB)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient          # noqa: E402
from sqlalchemy import func                        # noqa: E402
import main, models, roles                         # noqa: E402
import entry                                       # noqa: E402
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
b1 = models.Branch(name="Zafar"); b2 = models.Branch(name="Bekobod")
db.add_all([b1, b2]); db.commit()


def user(login, role, branch):
    u = models.User(username=login, password_hash=hash_password("x"),
                    full_name=login.upper(), role=role, branch_id=branch.id,
                    is_active=1)
    db.add(u); db.commit()
    return u


user("bm", roles.BRANCH_MANAGER, b1)
user("bm2", roles.BRANCH_MANAGER, b2)
user("asos", roles.FOUNDER, b1)
user("fin", roles.FINANCE_DIRECTOR, b1)
user("adm", roles.ADMINISTRATOR, b1)
user("acc", roles.ACCOUNTANT, b1)

s = models.Student(full_name="Ali Valiyev", branch_id=b1.id, status="active")
db.add(s); db.commit()
SID = s.id
db.add(models.Payment(student_id=SID, amount=-480_000, kind="charge",
                      period="2026-09", created_by="avtomat"))
db.add(models.Payment(student_id=SID, amount=100_000, kind="payment",
                      method="cash", created_by="ADM"))
db.commit()


def tok(u):
    r = c.post("/api/auth/login", json={"username": u, "password": "x"})
    return {"Authorization": "Bearer " + r.json()["access_token"]}


def bal():
    db.expire_all()
    return float(db.query(func.coalesce(func.sum(models.Payment.amount), 0))
                 .filter(models.Payment.student_id == SID).scalar())


def cash():
    db.expire_all()
    return float(db.query(func.coalesce(func.sum(models.Payment.amount), 0))
                 .filter(models.Payment.student_id == SID,
                         models.Payment.kind == "payment").scalar())


H = {u: tok(u) for u in ("bm", "bm2", "asos", "fin", "adm", "acc")}
URL = f"/api/students/{SID}/balance"
ck("boshlang'ich balans", bal(), -380_000.0)

print("=== 1-2. RUXSAT ===")
for u in ("asos", "fin", "adm", "acc"):
    r = c.put(URL, headers=H[u], json={"balance": 0, "note": "sinov"})
    ck(f"{u} — 403", r.status_code, 403)
r = c.put(URL, headers=H["bm2"], json={"balance": 0, "note": "sinov"})
ck("boshqa filial rahbari — 403", r.status_code, 403)

print("\n=== 3. SABAB ===")
r = c.put(URL, headers=H["bm"], json={"balance": 0, "note": "  "})
ck("sababsiz — 400", r.status_code, 400)

print("\n=== 4-5. TUZATISH ===")
rows_before = db.query(models.Payment).filter(
    models.Payment.student_id == SID).count()
r = c.put(URL, headers=H["bm"],
          json={"balance": -240_000, "note": "Ikki dars kasal bo'ldi"})
ck("filial rahbari — 200", r.status_code, 200)
ck("farq", r.json().get("changed"), 140_000.0)
ck("balans aynan -240 000", bal(), -240_000.0)
adj = (db.query(models.Payment)
       .filter(models.Payment.student_id == SID,
               models.Payment.kind == roles.PAYMENT_ADJUST_KIND).all())
ck("bitta tuzatish yozuvi", [a.amount for a in adj], [140_000.0])
ck("izohda eski/yangi summa va sabab",
   "-380 000 -> -240 000" in (adj[0].note or "")
   and "kasal" in (adj[0].note or ""), True)
ck("public_id bor", bool(adj[0].public_id), True)
ck("eski yozuvlar joyida", db.query(models.Payment).filter(
    models.Payment.student_id == SID).count(), rows_before + 1)
ck("kassa o'zgarmadi", cash(), 100_000.0)
# Teskari tomonga: qarzni ko'paytirish
r = c.put(URL, headers=H["bm"], json={"balance": -300_000,
                                      "note": "Kitob puli qo'shildi"})
ck("qarzni ko'paytirish", bal(), -300_000.0)
r = c.put(URL, headers=H["bm"], json={"balance": -300_000, "note": "yana"})
ck("bir xil summa — o'zgarish yo'q", r.json().get("changed"), 0)

print("\n=== 6. TUZATISHNI BOSHQALAR BUZA OLMAYDI ===")
db.expire_all()
last = (db.query(models.Payment)
        .filter(models.Payment.student_id == SID,
                models.Payment.kind == roles.PAYMENT_ADJUST_KIND)
        .order_by(models.Payment.id.desc()).first())
r = c.delete(f"/api/payments/{last.id}?reason=x", headers=H["fin"])
ck("moliya direktori o'chira olmaydi", r.status_code, 403)
r = c.put(f"/api/payments/{last.id}", headers=H["fin"],
          json={"amount": 1, "note": "x"})
ck("moliya direktori o'zgartira olmaydi", r.status_code, 403)
r = c.delete(f"/api/payments/{last.id}?reason=xato", headers=H["bm"])
ck("filial rahbari o'chira oladi", r.status_code, 200)
ck("balans qaytdi", bal(), -240_000.0)

print("\n=== 7. AUDIT ===")
n = (db.query(models.AuditLog)
     .filter(models.AuditLog.action == "balance_fix",
             models.AuditLog.entity_id == SID).count())
ck("audit: 2 ta tuzatish", n, 2)

print()
if fails:
    print(f"XATO: {len(fails)} ta tekshiruv o'tmadi")
    for f in fails:
        print("   - " + f)
    sys.exit(1)
print("HAMMASI O'TDI")
sys.exit(0)
