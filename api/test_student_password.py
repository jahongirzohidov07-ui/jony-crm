"""O'quvchi parolini almashtirish (2026-10-10)."""
import os, sys
os.environ["DATABASE_URL"] = "sqlite:////tmp/stu_pw_test.db"
if os.path.exists("/tmp/stu_pw_test.db"):
    os.remove("/tmp/stu_pw_test.db")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fastapi.testclient import TestClient  # noqa: E402
import main, models, roles, entry  # noqa: E402,F401
from database import SessionLocal  # noqa: E402
from auth import hash_password  # noqa: E402

c = TestClient(main.app)
fails = []


def ck(n, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + n + f": {got}" + ("" if ok else f" (kutilgan {want})"))
    if not ok:
        fails.append(n)


db = SessionLocal()
b = models.Branch(name="Zafar"); db.add(b); db.commit()
for un, r in (("hr", roles.HR_MANAGER), ("adm", roles.SALES_MANAGER),
              ("ust", roles.TEACHER)):
    db.add(models.User(username=un, password_hash=hash_password("x"),
                       full_name=un, role=r, is_active=1, branch_id=b.id))
s1 = models.Student(full_name="Ali", phone="901234567", branch_id=b.id, status="active")
s2 = models.Student(full_name="Telefonsiz", branch_id=b.id, status="active")
db.add_all([s1, s2]); db.commit(); S1, S2 = s1.id, s2.id
db.close()


def tok(u, p="x"):
    r = c.post("/api/auth/login", json={"username": u, "password": p})
    return r.status_code, (r.json().get("access_token") if r.status_code == 200 else None)


H = {"Authorization": "Bearer " + tok("hr")[1]}
a = c.get(f"/api/students/{S1}/account", headers=H).json()
ck("hisob yo'q", a["has_account"], False)
r = c.put(f"/api/students/{S1}/password", headers=H, json={"password": "qisqa"})
ck("qoidaga mos bo'lmagan parol rad", r.status_code, 400)
r = c.put(f"/api/students/{S1}/password", headers=H, json={"password": "Yangi2026"})
ck("hisob ochilib parol qo'yildi", r.status_code, 200)
login = r.json()["username"]
ck("yangi parol bilan kiradi", tok(login, "Yangi2026")[0], 200)
ck("eski standart parol ishlamaydi", tok(login, "jonyjony")[0] != 200, True)
r = c.put(f"/api/students/{S1}/password", headers=H, json={"reset": True})
ck("standartga qaytdi", tok(login, "jonyjony")[0], 200)
HA = {"Authorization": "Bearer " + tok("adm")[1]}
ck("administrator ham", c.put(f"/api/students/{S1}/password", headers=HA,
   json={"password": "Admin2026"}).status_code, 200)
HU = {"Authorization": "Bearer " + tok("ust")[1]}
ck("ustoz o'zgartira olmaydi", c.put(f"/api/students/{S1}/password", headers=HU,
   json={"password": "Ustoz2026"}).status_code, 403)
r = c.put(f"/api/students/{S2}/password", headers=H, json={"password": "Yangi2026"})
ck("telefonsiz — tushunarli xato", (r.status_code, "telefon" in r.text), (400, True))
db = SessionLocal()
au = db.query(models.AuditLog).filter(models.AuditLog.field == "Kirish paroli").all()
ck("auditda 3 ta, parolning o'zi yo'q", (len(au), any("2026" in (x.new_value or "") for x in au)), (3, False))
db.close()
print()
if fails:
    print(f"{len(fails)} ta XATO: {fails}"); sys.exit(1)
print("HAMMASI OK")
