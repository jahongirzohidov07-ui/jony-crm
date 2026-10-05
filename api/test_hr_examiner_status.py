"""HR: EXAMINERNI VOLONTYOR / EXAMINER QILISH (2026-10-05).

Jahongir: "hr uchun examinerlarni valantyor va examiner qilib
o'zgartirishni qo'shib ber".

Tekshiriladi:
  1. GET /api/staff-grades?only=examiner — faqat examinerlar (support
     yo'q), daraja yozilmagani volontyor.
  2. HR examiner qiladi (junior) va qaytadan volontyor qiladi; kim
     o'zgartirgani qaytadi.
  3. Examiner (oylikli) bo'lsa — o'ziga oylik ko'rinadi (salary_hidden
     False), volontyorda — yashirin.
  4. Ustoz — 403.
"""
import os
import sys
import tempfile

_DIR = os.path.join(tempfile.gettempdir(), "hr_examiner_status_test")
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


def user(login, name, role):
    u = models.User(username=login, password_hash=hash_password("x"),
                    full_name=name, role=role, branch_id=b.id, is_active=1)
    db.add(u); db.commit()
    return u


user("hr", "HR", roles.HR_MANAGER)
user("ust", "Ustoz", roles.TEACHER)
ex = user("ex", "Examiner Bir", roles.EXAMINER)
user("sup", "Support Bir", roles.SUPPORT_TEACHER)
EX = ex.id


def H(u):
    r = c.post("/api/auth/login", json={"username": u, "password": "x"})
    return {"Authorization": "Bearer " + r.json()["access_token"]}


HR, HU, HE = H("hr"), H("ust"), H("ex")

print("=== 1. RO'YXAT ===")
r = c.get("/api/staff-grades?only=examiner", headers=HR)
ck("status", r.status_code, 200)
ck("faqat examiner", [x["name"] for x in r.json()["rows"]], ["Examiner Bir"])
ck("sukut — volontyor", r.json()["rows"][0]["grade"], "volunteer")
ck("HR tahrirlay oladi", r.json()["can_edit"], True)
ck("examinerga oylik yashirin",
   c.get("/api/me", headers=HE).json().get("salary_hidden"), True)

print("\n=== 2. O'ZGARTIRISH ===")
r = c.put(f"/api/staff-grades/{EX}", headers=HR, json={"grade": "junior"})
ck("examiner qilindi", r.status_code, 200)
row = c.get("/api/staff-grades?only=examiner", headers=HR).json()["rows"][0]
ck("daraja junior, kim", (row["grade"], row["updated_by"]), ("junior", "HR"))
ck("endi oylik ko'rinadi",
   c.get("/api/me", headers=HE).json().get("salary_hidden"), False)
r = c.put(f"/api/staff-grades/{EX}", headers=HR, json={"grade": "volunteer"})
ck("volontyor qilindi", r.status_code, 200)
ck("yana yashirin",
   c.get("/api/me", headers=HE).json().get("salary_hidden"), True)

print("\n=== 3. RUXSAT ===")
ck("ustoz ko'rmaydi",
   c.get("/api/staff-grades?only=examiner", headers=HU).status_code, 403)
ck("ustoz o'zgartirmaydi",
   c.put(f"/api/staff-grades/{EX}", headers=HU,
         json={"grade": "junior"}).status_code, 403)

print()
if fails:
    print(f"XATO: {len(fails)} ta tekshiruv o'tmadi")
    for x in fails:
        print("   - " + x)
    sys.exit(1)
print("HAMMASI O'TDI")
sys.exit(0)
