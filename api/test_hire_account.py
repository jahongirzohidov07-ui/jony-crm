"""ISHGA OLINGAN NOMZODGA HISOB AVTOMAT OCHILADI (2026-08-19).

Jahongir: "hr bo'limida nomzod ishga olindi qilinsa to'g'ridan to'g'ri
akkaunt ochiladigan qilaylik, shu ma'lumotlarni boshqatdan profiliga
kiritib chiqish kerak bo'larkan baribr".
"""
import os, sys
os.environ["DATABASE_URL"] = "sqlite:////tmp/hireacc.db"
if os.path.exists("/tmp/hireacc.db"):
    os.remove("/tmp/hireacc.db")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                         # noqa: E402
import entry                                       # noqa: E402
from database import SessionLocal                  # noqa: E402
from auth import hash_password, verify_password    # noqa: E402

c = TestClient(main.app)
fails = []


def ck(n, g, w):
    ok = g == w
    print(("OK  " if ok else "MUAMMO ") + n + f": {g}"
          + ("" if ok else f" (kutilgan {w})"))
    if not ok:
        fails.append(n)


db = SessionLocal()
b = models.Branch(name="Bekobod 2"); db.add(b); db.commit(); BID = b.id
db.add(models.User(username="hr", full_name="HR Menejer",
                   password_hash=hash_password("x"),
                   role=roles.HR_MANAGER, branch_id=BID))
db.commit(); db.close()
tok = c.post("/api/auth/login",
             json={"username": "hr", "password": "x"}).json()["access_token"]
H = {"Authorization": f"Bearer {tok}"}


def new_cand(name, phone, position, subject=None):
    r = c.post("/api/candidates", headers=H, json={
        "full_name": name, "phone": phone, "position": position,
        "subject": subject, "branch_id": BID, "source": "other"})
    return r.json()["id"]


# ---------------------------------------------------------------- 1
print("\n=== 1. Ustoz nomzodi ishga olindi -> hisob + ustoz kartasi ===")
cid = new_cand("Aliyev Ustoz", "+998 90 111 22 33", "teacher", "english")
r = c.put(f"/api/candidates/{cid}", headers=H,
          json={"stage": "hired"}).json()
acc = r.get("account") or {}
ck("hisob ochildi", acc.get("created"), True)
ck("login telefon", acc.get("login"), "998901112233")

db = SessionLocal()
u = db.query(models.User).filter(
    models.User.username == "998901112233").first()
ck("bazada bor", u is not None, True)
ck("roli ustoz", u.role, roles.TEACHER)
ck("filiali nomzoddan", u.branch_id, BID)
ck("parol jonyjony", verify_password("jonyjony", u.password_hash), True)
t = db.query(models.Teacher).filter(
    models.Teacher.user_id == u.id).first()
ck("ustoz kartasi ochildi", t is not None, True)
ck("fani ko'chdi", t.subject, "english")
ck("telefoni ko'chdi", "111" in (t.phone or ""), True)
cand = db.query(models.Candidate).get(cid)
ck("izohda login yozildi", "998901112233" in (cand.note or ""), True)
a = (db.query(models.AuditLog)
     .filter(models.AuditLog.entity == "user",
             models.AuditLog.entity_id == u.id).count())
ck("auditda iz bor", a >= 1, True)
db.close()

# ---------------------------------------------------------------- 2
print("\n=== 2. Takror 'hired' — ikkinchi hisob OCHILMAYDI ===")
c.put(f"/api/candidates/{cid}", headers=H, json={"stage": "interview"})
r = c.put(f"/api/candidates/{cid}", headers=H,
          json={"stage": "hired"}).json()
acc = r.get("account") or {}
ck("yangi ochilmadi", acc.get("created"), False)
ck("mavjudini aytdi", "allaqachon bor" in (acc.get("reason") or ""), True)
db = SessionLocal()
ck("hisoblar soni o'smadi",
   db.query(models.User).filter(
       models.User.username == "998901112233").count(), 1)
db.close()

# ---------------------------------------------------------------- 3
print("\n=== 3. Support -> support roli ===")
cid3 = new_cand("Bekova Support", "998905556677", "support")
r = c.put(f"/api/candidates/{cid3}", headers=H,
          json={"stage": "hired"}).json()
ck("ochildi", (r.get("account") or {}).get("created"), True)
db = SessionLocal()
u3 = db.query(models.User).filter(
    models.User.username == "998905556677").first()
ck("roli support", u3.role, roles.SUPPORT_TEACHER)
db.close()

# ---------------------------------------------------------------- 4
print("\n=== 4. Farrosh — hisob ochilmaydi (kerak emas) ===")
cid4 = new_cand("Farrosh Opa", "998901234500", "cleaner")
r = c.put(f"/api/candidates/{cid4}", headers=H,
          json={"stage": "hired"}).json()
acc = r.get("account") or {}
ck("ochilmadi", acc.get("created"), False)
db = SessionLocal()
ck("bazada yo'q", db.query(models.User).filter(
    models.User.username == "998901234500").count(), 0)
db.close()

# ---------------------------------------------------------------- 5
print("\n=== 5. Telefonsiz nomzod — ochilmaydi, lekin yiqilmaydi ===")
cid5 = new_cand("Telefonsiz Odam", None, "teacher", "english")
r = c.put(f"/api/candidates/{cid5}", headers=H, json={"stage": "hired"})
ck("so'rov o'tdi", r.status_code, 200)
acc = r.json().get("account") or {}
ck("sabab aytildi", "Telefon" in (acc.get("reason") or ""), True)

print("\n" + ("HAMMASI JOYIDA" if not fails
              else f"MUAMMO: {len(fails)} ta -> {fails}"))
sys.exit(1 if fails else 0)
