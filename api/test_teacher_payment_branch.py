"""USTOZ OYLIGI QAYSI FILIALDAN BERILSA — O'SHA FILIALGA (2026-09-16).

Jahongir: "2ta filialda ishlaydigan xodimlarni oyligi qaysi filialdan
turib kiritsa o'sha filialga tushsin, asosiy filialiga belgilanib
qolyabdi. Barcha filiallardan turib filialni bekobod 1 qilib tanlab
kiritsam ham bekobod 2ga o'tib ketdi oyligi".

Tekshiriladi:
  1. "Barcha filiallar"dan Bekobod 1 tanlab kiritilsa — Bekobod 1 ga;
  2. Administrator (Bekobod 1) kiritsa — Bekobod 1 ga;
  3. Xarajatlar ro'yxati va pul oqimi filial bo'yicha to'g'ri ajratadi;
  4. Ustoz kartasidan berilgan pul ham filial bilan;
  5. Eski yozuv (filialsiz) — asosiy filial, filialini to'g'rilash mumkin;
  6. Administrator o'ziga tegishli bo'lmagan filialga o'tkaza olmaydi.
"""
import os
import sys
import tempfile
from datetime import date

_DIR = os.path.join(tempfile.gettempdir(), "teacher_payment_branch_test")
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


def tok(u, p="x"):
    return {"Authorization": "Bearer " + client.post(
        "/api/auth/login", json={"username": u, "password": p}
    ).json()["access_token"]}


TODAY = date.today()
Y, M = TODAY.year, TODAY.month
db = SessionLocal()
b1 = models.Branch(name="Bekobod 1"); b2 = models.Branch(name="Bekobod 2")
db.add_all([b1, b2]); db.commit()
B1, B2 = b1.id, b2.id
db.add_all([
    models.User(username="asos", password_hash=hash_password("x"),
                full_name="Asoschi", role=roles.FOUNDER),
    models.User(username="adm", password_hash=hash_password("x"),
                full_name="Admin B1", role=roles.ADMINISTRATOR, branch_id=B1),
])
db.commit()
# Asosiy filiali BEKOBOD 2, qo'shimcha — Bekobod 1
t = models.Teacher(full_name="Sardor Teacher", is_active=1, branch_id=B2)
db.add(t); db.commit()
db.add(models.TeacherBranch(teacher_id=t.id, branch_id=B1))
old = models.TeacherPayment(teacher_id=t.id, amount=10_000, kind="salary",
                            paid_on=TODAY, method="cash", note="eski")
db.add(old); db.commit()
TID, OLD_ID = t.id, old.id
db.close()

H, A = tok("asos"), tok("adm")


def branch_of(pid):
    s = SessionLocal()
    v = s.query(models.TeacherPayment).get(pid).branch_id
    s.close()
    return v


def rows(headers, bid=None):
    q = f"/api/expenses?year={Y}&month={M}&with_teacher=1"
    if bid:
        q += f"&branch_id={bid}"
    return [e for e in client.get(q, headers=headers).json()
            if e["category"] == "teacher_salary"]


print("=== 1. Barcha filiallardan Bekobod 1 tanlab ===")
r = client.post("/api/expenses", headers=H, json={
    "date": TODAY.isoformat(), "category": "admin_salary", "amount": 1_700_000,
    "teacher_id": TID, "method": "cash", "branch_id": B1})
P1 = -r.json()["id"]
ck("Bekobod 1 ga yozildi (asosiy Bekobod 2 emas)", branch_of(P1), B1)

print("\n=== 2. Administrator (Bekobod 1) ===")
r = client.post("/api/expenses", headers=A, json={
    "date": TODAY.isoformat(), "category": "admin_salary", "amount": 500_000,
    "teacher_id": TID, "method": "cash"})
ck("administrator kiritdi", r.status_code, 200)
P2 = -r.json()["id"]
ck("uning filialiga", branch_of(P2), B1)
r = client.post("/api/expenses", headers=A, json={
    "date": TODAY.isoformat(), "category": "admin_salary", "amount": 1,
    "teacher_id": TID, "method": "cash", "branch_id": B2})
ck("boshqa filialni tanlasa ham — o'z filialiga", branch_of(-r.json()["id"]), B1)

print("\n=== 3. Ro'yxat va pul oqimi ===")
b1rows = rows(H, B1)
ck("Bekobod 1 ro'yxatida 3 ta", len(b1rows), 3)
ck("filial nomi Bekobod 1", {e["branch"]["name"] for e in b1rows}, {"Bekobod 1"})
b2rows = rows(H, B2)
ck("Bekobod 2 da faqat eski (filialsiz) yozuv", [e["amount"] for e in b2rows], [10_000])
cf = client.get(f"/api/reports/cashflow-ledger?year={Y}&month={M}&branch_id={B1}",
                headers=H).json()
tcf = [x for x in cf["rows"] if x["category"] == "teacher_salary"]
ck("pul oqimi Bekobod 1: 3 ta ustoz oyligi", len(tcf), 3)
ck("pul oqimida filial Bekobod 1", {x["branch"] for x in tcf}, {"Bekobod 1"})
cf2 = client.get(f"/api/reports/cashflow-ledger?year={Y}&month={M}&branch_id={B2}",
                 headers=H).json()
ck("pul oqimi Bekobod 2: faqat eski",
   [x["amount"] for x in cf2["rows"] if x["category"] == "teacher_salary"], [10_000])
cfa = client.get(f"/api/reports/cashflow-ledger?year={Y}&month={M}", headers=A).json()
ck("administrator pul oqimida o'z filiali ustoz oyliklari",
   len([x for x in cfa["rows"] if x["category"] == "teacher_salary"]), 3)

print("\n=== 4. Ustoz kartasidan ===")
r = client.post(f"/api/teachers/{TID}/payments", headers=H, json={
    "amount": 200_000, "kind": "salary", "branch_id": B1})
ck("qabul qilindi", r.status_code, 200)
s = SessionLocal()
last = s.query(models.TeacherPayment).order_by(models.TeacherPayment.id.desc()).first()
s.close()
ck("filial Bekobod 1", last.branch_id, B1)

print("\n=== 5. Eski yozuvning filialini to'g'rilash ===")
ck("eski yozuvda filial bo'sh", branch_of(OLD_ID), None)
r = client.put(f"/api/teacher-payments/{OLD_ID}/branch", headers=H, json={"branch_id": B1})
ck("to'g'rilandi", (r.status_code, branch_of(OLD_ID)), (200, B1))
ck("endi Bekobod 2 da yo'q", rows(H, B2), [])

print("\n=== 6. Administrator boshqa filialga o'tkaza olmaydi ===")
r = client.put(f"/api/teacher-payments/{P2}/branch", headers=A, json={"branch_id": B2})
ck("rad etildi", r.status_code, 403)
ck("filial o'zgarmadi", branch_of(P2), B1)

print()
if fails:
    print(f"XATOLAR ({len(fails)}): " + ", ".join(fails))
    sys.exit(1)
print("HAMMASI O'TDI")
