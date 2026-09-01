# -*- coding: utf-8 -*-
"""TEST FILIALI HR RAHBARIGA (2026-08-31).

Jahongir: "test filial HR rahbariga ko'rinsin, u ishlatib ko'radi
tekshiradi".

ENG MUHIM XAVF: test filialida SOXTA o'quvchi va SOXTA to'lov bor
(mashq uchun 100 ta o'quvchi kiritilgan). Agar u yig'indiga
qo'shilib ketsa — tushum, o'quvchi soni, qarz, hammasi yolg'on
bo'ladi. Shuning uchun testning yarmi aynan shuni tekshiradi:
HR uni KO'RADI, lekin YIG'INDI o'zgarmaydi.
"""
import os
import sys

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_hrtb/db.sqlite"
os.makedirs("/tmp/verify_hrtb", exist_ok=True)
if os.path.exists("/tmp/verify_hrtb/db.sqlite"):
    os.remove("/tmp/verify_hrtb/db.sqlite")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import date, datetime                  # noqa: E402
from fastapi.testclient import TestClient            # noqa: E402
import main, models, roles                           # noqa: E402
import entry                                         # noqa: F401,E402
import common                                        # noqa: E402
from database import SessionLocal                    # noqa: E402
from auth import hash_password                       # noqa: E402

c = TestClient(main.app)
db = SessionLocal()
fails = []


def ck(n, got, want):
    ok = got == want
    print(("OK   " if ok else "XATO ") + f"{n}: {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(n)


zafar = models.Branch(name="Zafar")
bek = models.Branch(name="Bekobod 1")
test_b = models.Branch(name="Test - filial")
# Hamkor filial ALOHIDA USTUN bilan belgilanadi (nom bilan emas)
stech = models.Branch(name="Stech", is_partner=1)
db.add_all([zafar, bek, test_b, stech]); db.commit()
common.reset_partner_cache()
common._TEST_IDS = None

g_real = models.Group(name="Real", branch_id=zafar.id, lesson_price=40_000,
                      monthly_fee=480_000)
g_test = models.Group(name="Mashq", branch_id=test_b.id, lesson_price=40_000,
                      monthly_fee=480_000)
db.add_all([g_real, g_test]); db.commit()

# REAL: 2 ta o'quvchi, 1 mln to'lov
for i in range(2):
    s = models.Student(full_name=f"Real {i}", group_id=g_real.id,
                       branch_id=zafar.id, status="active",
                       enrolled_date=date.today())
    db.add(s); db.commit()
    db.add(models.Payment(student_id=s.id, amount=500_000, kind="payment",
                          created_at=datetime.now(), created_by="Admin"))
# TEST: 5 ta SOXTA o'quvchi, 5 mln soxta to'lov
for i in range(5):
    s = models.Student(full_name=f"Soxta {i}", group_id=g_test.id,
                       branch_id=test_b.id, status="active",
                       enrolled_date=date.today())
    db.add(s); db.commit()
    db.add(models.Payment(student_id=s.id, amount=1_000_000, kind="payment",
                          created_at=datetime.now(), created_by="Admin"))
db.commit()

users = {}
for nm, role, br in (("hr", roles.HR_MANAGER, None),
                     ("asoschi_h", roles.FOUNDER, None),
                     ("smm_h", roles.SMM_MANAGER, zafar.id),
                     ("sotuv_h", roles.SALES_MANAGER, zafar.id)):
    u = models.User(username=nm, password_hash=hash_password("jonyjony"),
                    role=role, full_name=nm.title(), branch_id=br,
                    is_active=1)
    db.add(u); users[nm] = u
db.commit()


def hdr(nm):
    return {"Authorization": "Bearer " + c.post("/api/auth/login", json={
        "username": nm, "password": "jonyjony"}).json()["access_token"]}


HR, HF, HS, HA = hdr("hr"), hdr("asoschi_h"), hdr("smm_h"), hdr("sotuv_h")


# =====================================================================
print("=== 1. TANLAGICHDA KO'RINISHI ===")
# =====================================================================
def branches(h):
    r = c.get("/api/branches", headers=h)
    return sorted(x["name"] for x in r.json()) if r.status_code == 200 else r.status_code


b_hr = branches(HR)
ck("HR test filialini KO'RADI", "Test - filial" in b_hr, True)
ck("  lekin Stech unga KO'RINMAYDI", "Stech" in b_hr, False)
ck("  real filiallar joyida",
   all(x in b_hr for x in ("Zafar", "Bekobod 1")), True)

ck("asoschi hammasini ko'radi",
   all(x in branches(HF) for x in ("Test - filial", "Stech")), True)
ck("SMM test filialini KO'RMAYDI", "Test - filial" in branches(HS), False)
ck("sotuv menejeri ham ko'rmaydi", "Test - filial" in branches(HA), False)


# =====================================================================
print("\n=== 2. HR TEST FILIALINI OCHIB ISHLATA OLADI ===")
# =====================================================================
r = c.get(f"/api/students?branch_id={test_b.id}", headers=HR)
ck("test filial o'quvchilari ochiladi", r.status_code, 200)
names = sorted(x["full_name"] for x in r.json())
ck("  5 ta mashq o'quvchisi ko'rinadi", len(names), 5)
ck("  aynan soxtalari", names[0].startswith("Soxta"), True)

r = c.get(f"/api/groups?branch_id={test_b.id}", headers=HR)
ck("guruhlari ham ochiladi",
   [x["name"] for x in r.json()], ["Mashq"])


# =====================================================================
print("\n=== 3. ENG MUHIMI: YIG'INDI BUZILMASLIGI ===")
# =====================================================================
# "Barcha filiallar" tanlanganda test filiali QO'SHILMAYDI —
# na HRda, na asoschida.
for nm, h in (("HR", HR), ("asoschi", HF)):
    r = c.get("/api/students", headers=h)
    got = [x["full_name"] for x in r.json()]
    ck(f"{nm}: umumiy ro'yxatda soxta o'quvchi YO'Q",
       any(x.startswith("Soxta") for x in got), False)
    ck(f"  {nm}: faqat 2 ta real", len(got), 2)

ck("test filiali yig'indidan chetlatilgan ro'yxatda",
   test_b.id in common.aggregate_skip_ids(db, users["hr"]), True)
ck("  asoschida ham chetlatilgan",
   test_b.id in common.aggregate_skip_ids(db, users["asoschi_h"]), True)


# =====================================================================
print("\n=== 4. STECH HRga BARIBIR YOPIQ ===")
# =====================================================================
ck("Stech bloklangan ro'yxatda (HR)",
   stech.id in common.blocked_branch_ids(db, users["hr"]), True)
r = c.get(f"/api/students?branch_id={stech.id}", headers=HR)
ck("  tanlab ham ochib bo'lmaydi (bo'sh)", len(r.json()), 0)


# =====================================================================
print("\n=== 5. O'RGATUVCHI HRga OCHIQ ===")
# =====================================================================
r = c.get("/api/guide/state", headers=HR)
ck("interaktiv o'rgatuvchi ochiladi", r.status_code, 200)


print("\n" + "=" * 60)
if fails:
    print("YIQILGAN TEKSHIRUVLAR:", len(fails))
    for f in fails:
        print("  -", f)
else:
    print("HAMMASI O'TDI")
sys.exit(1 if fails else 0)
