"""BUDJET: XODIM OYLIGI BITTALAB, XO'JALIK, ASOSCHI OYLIGI (2026-10-02).

Jahongir: "ustozlar oyligidan tashqari boshqa xodimlar oyligini bitta
bitta kiritadigan qilish kerak, yana xo'jalik xarajatlarini ham kiritish
kerak", "Ichiga Asoschi oylik deb ham qo'shasan".

Tekshiriladi:
  1. Formaga xodimlar ro'yxati keladi (ustoz va asoschi yo'q), fiks
     oylik bilan; xo'jalik va asoschi oyligi kategoriyalari bor.
  2. "staff:<id>" rejasi saqlanadi, oy rejasi formaga qaytadi.
  3. Fakt: xodimga berilgan oylik o'sha xodim qatoriga, asoschiniki
     "Asoschi oyligi"ga tushadi; jami o'zgarmaydi; bo'limda Ma'muriyat.
  4. Tozalangan maydon 0 bo'lib saqlanadi.
"""
import os
import sys
import tempfile
from datetime import date

_DIR = os.path.join(tempfile.gettempdir(), "budget_staff_test")
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

_cm_stub._ensure_month_charges = lambda db, **kw: None

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


def mk(login, role, fix=0):
    u = models.User(username=login, full_name=login.capitalize(),
                    password_hash=hash_password("x"), role=role,
                    branch_id=None if role == roles.FOUNDER else b.id,
                    is_active=1, fix_salary=fix)
    db.add(u); db.commit()
    return u.id


F = mk("asos", roles.FOUNDER)
SARVAR = mk("sarvar", roles.SALES_MANAGER, 3_000_000)
HR = mk("hr", roles.HR_MANAGER if hasattr(roles, "HR_MANAGER")
        else roles.ACCOUNTANT, 2_500_000)
UST = mk("ust", roles.TEACHER)
db.add(models.Teacher(full_name="Ust", branch_id=b.id, user_id=UST,
                      is_active=1))
db.commit()
H = {"Authorization": "Bearer " + c.post("/api/auth/login", json={
    "username": "asos", "password": "x"}).json()["access_token"]}

today = date.today()
Y = today.year if today.month >= 9 else today.year - 1
M = today.month

print("=== 1. Forma ma'lumotlari ===")
d = c.get(f"/api/finance/budget?year={Y}&month={M}", headers=H).json()
ids = [x["user_id"] for x in d["staff"]]
ck("xodimlar: ustoz va asoschi yo'q", sorted(ids), sorted([SARVAR, HR]))
ck("fiks oylik", {x["user_id"]: x["fix_salary"] for x in d["staff"]}[SARVAR],
   3_000_000)
keys = {x["key"]: x["group"] for x in d["expense_categories"]}
ck("xo'jalik kategoriyalari", all(keys.get(k) == "household" for k in
                                  ("cleaning", "hygiene", "kitchen",
                                   "household")), True)
ck("asoschi oyligi", keys.get("founder_salary"), "admin_salary")

print("\n=== 2. Saqlash ===")
items = [
    {"month": M, "kind": "expense", "category": f"staff:{SARVAR}",
     "amount": 3_000_000},
    {"month": M, "kind": "expense", "category": f"staff:{HR}",
     "amount": 2_000_000},
    {"month": M, "kind": "expense", "category": "founder_salary",
     "amount": 10_000_000},
    {"month": M, "kind": "expense", "category": "cleaning",
     "amount": 300_000},
]
ck("saqlandi", c.put(f"/api/finance/budget/{Y}", headers=H,
                     json={"items": items}).status_code, 200)

# Fakt: Sarvarga 2.8 mln, asoschiga 9 mln oylik, tozalash 250k
for amt, cat, uid in ((2_800_000, "admin_salary", SARVAR),
                      (9_000_000, "admin_salary", F),
                      (250_000, "cleaning", None)):
    db.add(models.Expense(date=date(today.year, M, 1), category=cat,
                          amount=amt, branch_id=b.id, staff_user_id=uid))
db.commit()

d = c.get(f"/api/finance/budget?year={Y}&month={M}", headers=H).json()
plan = d["plans"][str(M)]["expense"]
ck("oy rejasi formaga qaytadi", (plan.get(f"staff:{SARVAR}"),
                                 plan.get("founder_salary"),
                                 plan.get("cleaning")),
   (3_000_000, 10_000_000, 300_000))

print("\n=== 3. Fakt ===")
cats = {x["category"]: x for x in d["monthly"]["categories"]}
ck("Sarvar qatori", (cats[f"staff:{SARVAR}"]["label"],
                     cats[f"staff:{SARVAR}"]["plan"],
                     cats[f"staff:{SARVAR}"]["fakt"]),
   ("Sarvar", 3_000_000, 2_800_000))
ck("asoschi oyligi", (cats["founder_salary"]["plan"],
                      cats["founder_salary"]["fakt"]),
   (10_000_000, 9_000_000))
ck("umumiy admin_salary'da qolmadi", "admin_salary" in cats, False)
ck("tozalash", cats["cleaning"]["fakt"], 250_000)
deps = {x["department"]: x for x in d["departments"]}
ck("Ma'muriyat bo'limi", (deps["admin_salary"]["plan"],
                          deps["admin_salary"]["fakt"]),
   (15_000_000, 11_800_000))
ck("Xo'jalik bo'limi", deps["household"]["label"], "Xo'jalik")

print("\n=== 4. Tozalash ===")
c.put(f"/api/finance/budget/{Y}", headers=H, json={"items": [
    {"month": M, "kind": "expense", "category": f"staff:{HR}",
     "amount": 0}]})
d = c.get(f"/api/finance/budget?year={Y}&month={M}", headers=H).json()
ck("HR rejasi 0", d["plans"][str(M)]["expense"].get(f"staff:{HR}"), 0)

print("\n=== 5. Filial tanlanganda — faqat shu filial xodimlari ===")
db2 = SessionLocal()
b2 = models.Branch(name="Bekobod 1"); db2.add(b2); db2.commit()
u2 = models.User(username="boshqa", full_name="Boshqa", role=roles.SALES_MANAGER,
                 branch_id=b2.id, is_active=1, password_hash="x")
db2.add(u2); db2.commit()
B2, U2 = b2.id, u2.id
db2.close()
d = c.get(f"/api/finance/budget?year={Y}&month={M}&branch_id={B2}",
          headers=H).json()
ck("Bekobod 1: faqat o'zi", [x["user_id"] for x in d["staff"]], [U2])
d = c.get(f"/api/finance/budget?year={Y}&month={M}", headers=H).json()
ck("barcha filiallar: hammasi", sorted(x["user_id"] for x in d["staff"]),
   sorted([SARVAR, HR, U2]))

print("\n=== 6. Ustoz bonuslari ===")
c.put(f"/api/finance/budget/{Y}", headers=H, json={"items": [
    {"month": M, "kind": "expense", "category": "teacher_bonus",
     "amount": 4_000_000}]})
d = c.get(f"/api/finance/budget?year={Y}&month={M}", headers=H).json()
cats = {x["category"]: x for x in d["monthly"]["categories"]}
ck("qator", (cats["teacher_bonus"]["label"], cats["teacher_bonus"]["plan"]),
   ("Ustoz bonuslari", 4_000_000))
deps = {x["department"]: x for x in d["departments"]}
ck("O'quv bo'limiga tushdi", deps["teacher_payroll"]["plan"], 4_000_000)

print()
if fails:
    print(f"{len(fails)} ta XATO: {fails}")
    sys.exit(1)
print("HAMMASI OK")
