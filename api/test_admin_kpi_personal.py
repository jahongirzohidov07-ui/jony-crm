# -*- coding: utf-8 -*-
"""ADMINLAR KPI: yangi mijoz SHAXSIY, eski to'lov FILIAL (2026-08-30).

Jahongir: "eski to'lovlarni yig'ish umumiy FILIALLAR KESIMIDA foizda
hisoblanadi, lekin yangi to'lovlar bu INDIVIDUAL KPI bo'ladi shuning
uchun u KIM YANGI TO'LOV QILDIRSA O'ZIGA hisoblanishi kerak"

XATO SHU EDI: bir filialda ikkita admin bo'lsa, ikkalasi ham bir xil
"39 ta yangi mijoz" ni ko'rardi va ikkalasi ham to'liq bonus olardi —
kim ishlagani ahamiyatsiz edi.
"""
import os
import sys

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_kpi/db.sqlite"
os.makedirs("/tmp/verify_kpi", exist_ok=True)
if os.path.exists("/tmp/verify_kpi/db.sqlite"):
    os.remove("/tmp/verify_kpi/db.sqlite")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import date, datetime                 # noqa: E402
from fastapi.testclient import TestClient           # noqa: E402
import main, models, roles                          # noqa: E402
import entry                                        # noqa: F401,E402
import common                                       # noqa: E402
from database import SessionLocal                   # noqa: E402
from auth import hash_password                      # noqa: E402

c = TestClient(main.app)
db = SessionLocal()
fails = []


def ck(n, got, want):
    ok = got == want
    print(("OK   " if ok else "XATO ") + f"{n}: {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(n)


YIL, OY = 2026, 8
b = models.Branch(name="Zafar")
db.add(b); db.commit()
common.reset_partner_cache()
g = models.Group(name="G1", branch_id=b.id, lesson_price=40_000,
                 monthly_fee=480_000, standard_lessons_per_month=12)
db.add(g); db.commit()

# Bonus jadvallari
db.add(models.KpiNewClientRule(min_clients=5, bonus=300_000))
db.add(models.KpiNewClientRule(min_clients=10, bonus=600_000))
db.add(models.KpiCollectionRule(min_students=1, max_students=None,
                                min_percent=90, bonus=2_000_000))
db.commit()

# BITTA filialda IKKITA admin
shaxlo = models.User(username="shaxlo", password_hash=hash_password("jonyjony"),
                     role=roles.SALES_MANAGER, full_name="Zohidova Shaxlo",
                     branch_id=b.id, is_active=1, fix_salary=1_500_000)
dilnoza = models.User(username="dilnoza",
                      password_hash=hash_password("jonyjony"),
                      role=roles.SALES_MANAGER, full_name="Karimova Dilnoza",
                      branch_id=b.id, is_active=1, fix_salary=1_500_000)
fo = models.User(username="asoschi_k", password_hash=hash_password("jonyjony"),
                 role=roles.FOUNDER, full_name="Jahongir", is_active=1)
db.add_all([shaxlo, dilnoza, fo]); db.commit()
HF = {"Authorization": "Bearer " + c.post("/api/auth/login", json={
    "username": "asoschi_k", "password": "jonyjony"}).json()["access_token"]}


def yangi(nom, kim):
    """Yangi mijoz: shu oy birinchi marta to'laydi. kim — qabul qilgan."""
    s = models.Student(full_name=nom, group_id=g.id, branch_id=b.id,
                       status="active", enrolled_date=date(YIL, OY, 1))
    db.add(s); db.commit()
    db.add(models.Payment(student_id=s.id, amount=480_000, kind="payment",
                          created_at=datetime(YIL, OY, 10),
                          created_by=kim))
    db.commit()
    return s


def eski(nom):
    """Eski o'quvchi: o'tgan oy ham to'lagan. Yig'ish foiziga kiradi."""
    s = models.Student(full_name=nom, group_id=g.id, branch_id=b.id,
                       status="active", enrolled_date=date(YIL, 1, 1))
    db.add(s); db.commit()
    db.add(models.Payment(student_id=s.id, amount=480_000, kind="payment",
                          created_at=datetime(YIL, OY - 1, 10),
                          created_by="Kimdir"))
    db.add(models.Payment(student_id=s.id, amount=-480_000, kind="charge",
                          created_at=datetime(YIL, OY, 1)))
    db.add(models.Payment(student_id=s.id, amount=480_000, kind="payment",
                          created_at=datetime(YIL, OY, 12),
                          created_by="Kimdir"))
    db.commit()
    return s


# Shaxlo 6 ta yangi mijoz olib keldi, Dilnoza 2 ta
for i in range(6):
    yangi(f"Yangi Shaxlo {i}", "Zohidova Shaxlo")
for i in range(2):
    yangi(f"Yangi Dilnoza {i}", "Karimova Dilnoza")
# 3 tasini ASOSCHI qabul qilgan — hech kimga tegishli emas
for i in range(3):
    yangi(f"Yangi Asoschi {i}", "Jahongir")
# 10 ta eski o'quvchi to'liq to'ladi -> yig'ish 100%
for i in range(10):
    eski(f"Eski {i}")
db.commit()

r = c.get(f"/api/kpi/admins?year={YIL}&month={OY}", headers=HF).json()
rows = {x["full_name"]: x for x in r["rows"]}


# =====================================================================
print("=== 1. YANGI MIJOZ — SHAXSIY ===")
# =====================================================================
ck("ikkala admin ham ro'yxatda", sorted(rows), 
   ["Karimova Dilnoza", "Zohidova Shaxlo"])
ck("Shaxlo o'zi 6 ta olib keldi", rows["Zohidova Shaxlo"]["new_clients"], 6)
ck("Dilnoza o'zi 2 ta", rows["Karimova Dilnoza"]["new_clients"], 2)
ck("  IKKALASI 11 ta EMAS (eski xato)",
   rows["Zohidova Shaxlo"]["new_clients"] != 11
   and rows["Karimova Dilnoza"]["new_clients"] != 11, True)

ck("filialda jami 11 ta ekani ko'rinadi",
   rows["Zohidova Shaxlo"]["branch_new_clients"], 11)
ck("  3 tasi hech kimga tegishli emasligi aytiladi",
   rows["Zohidova Shaxlo"]["unassigned_new_clients"], 3)
ck("tushum ham shaxsiy",
   rows["Zohidova Shaxlo"]["new_client_revenue"], 6 * 480_000)


# =====================================================================
print("\n=== 2. BONUS SHAXSIY NATIJADAN ===")
# =====================================================================
ck("Shaxlo 6 ta -> 300 ming bonus",
   rows["Zohidova Shaxlo"]["new_client_bonus"], 300_000)
ck("Dilnoza 2 ta -> bonus yo'q",
   rows["Karimova Dilnoza"]["new_client_bonus"], 0)
ck("  ilgari ikkalasi ham 600 ming olardi (11 ta uchun)",
   rows["Karimova Dilnoza"]["new_client_bonus"] != 600_000, True)


# =====================================================================
print("\n=== 3. ESKI TO'LOV — FILIAL (o'zgarmadi) ===")
# =====================================================================
ck("yig'ish foizi ikkalasida bir xil",
   rows["Zohidova Shaxlo"]["collection_percent"],
   rows["Karimova Dilnoza"]["collection_percent"])
ck("  100%", rows["Zohidova Shaxlo"]["collection_percent"], 100.0)
ck("yig'ish bonusi ikkalasiga ham to'liq",
   [rows["Zohidova Shaxlo"]["collection_bonus"],
    rows["Karimova Dilnoza"]["collection_bonus"]],
   [2_000_000, 2_000_000])
ck("  yangi mijoz to'lovi yig'ish foiziga kirmadi",
   rows["Zohidova Shaxlo"]["collected"], 10 * 480_000)


# =====================================================================
print("\n=== 4. JAMI OYLIK ===")
# =====================================================================
ck("Shaxlo: 1.5 + 2.0 + 0.3 mln",
   rows["Zohidova Shaxlo"]["total"], 1_500_000 + 2_000_000 + 300_000)
ck("Dilnoza: 1.5 + 2.0 mln (yangi mijoz bonusisiz)",
   rows["Karimova Dilnoza"]["total"], 1_500_000 + 2_000_000)
ck("  ikkalasi TENG EMAS — ish farqi ko'rindi",
   rows["Zohidova Shaxlo"]["total"] != rows["Karimova Dilnoza"]["total"],
   True)


# =====================================================================
print("\n=== 5. ISM YOZILISHI FARQ QILSA HAM ===")
# =====================================================================
s2 = yangi("Apostrofli Bola", "  zohidova   SHAXLO ")
r2 = c.get(f"/api/kpi/admins?year={YIL}&month={OY}", headers=HF).json()
w2 = {x["full_name"]: x for x in r2["rows"]}
ck("katta-kichik harf va ortiqcha bo'shliq muammo emas",
   w2["Zohidova Shaxlo"]["new_clients"], 7)


# =====================================================================
print("\n=== 6. HAR KIM FAQAT O'ZINIKINI KO'RADI ===")
# =====================================================================
HS = {"Authorization": "Bearer " + c.post("/api/auth/login", json={
    "username": "shaxlo", "password": "jonyjony"}).json()["access_token"]}
r3 = c.get(f"/api/kpi/admins?year={YIL}&month={OY}", headers=HS).json()
ck("admin faqat o'z qatorini ko'radi",
   [x["full_name"] for x in r3["rows"]], ["Zohidova Shaxlo"])


print("\n=== Filial tanlansa — faqat shu filial adminlari ===")
_s = SessionLocal() if "SessionLocal" in globals() else db
_b2 = models.Branch(name="Bekobod 1"); _s.add(_b2); _s.commit()
_s.add(models.User(username="bek_admin", password_hash=hash_password("x"),
                   role=roles.SALES_MANAGER, full_name="Bekobod Admin",
                   branch_id=_b2.id, is_active=1, fix_salary=1_000_000))
_s.commit()
_all = {x["full_name"] for x in c.get(
    f"/api/kpi/admins?year={YIL}&month={OY}", headers=HF).json()["rows"]}
_za = {x["full_name"] for x in c.get(
    f"/api/kpi/admins?year={YIL}&month={OY}&branch_id={b.id}",
    headers=HF).json()["rows"]}
_bk = [x["full_name"] for x in c.get(
    f"/api/kpi/admins?year={YIL}&month={OY}&branch_id={_b2.id}",
    headers=HF).json()["rows"]]
ck("barcha filiallar — Bekobod admini ham", "Bekobod Admin" in _all, True)
ck("Zafar — Bekobod admini yo'q", "Bekobod Admin" in _za, False)
ck("Zafar — Shaxlo bor", "Zohidova Shaxlo" in _za, True)
ck("Bekobod 1 — faqat o'z admini", _bk, ["Bekobod Admin"])

print("\n" + "=" * 60)
if fails:
    print("YIQILGAN TEKSHIRUVLAR:", len(fails))
    for f in fails:
        print("  -", f)
else:
    print("HAMMASI O'TDI")
sys.exit(1 if fails else 0)
