"""MASHQ FILIALI — DEMO MA'LUMOT (2026-08-23).

Jahongir: "test deb filial ochganman shu filialga 100 kishilik qilib
o'quvchilar va adminlar qoshib qoyginda shundan bosib bosib
o'rganvolsin adminlar nimani qanday qilishni".

Tekshiriladi: faqat asoschi; faqat nomida "test" bor filial; 100 ta
o'quvchi + guruh + ustoz + xodim akkauntlari yaratiladi; haqiqiy
filialga TEGILMAYDI; tozalash faqat demo yozuvlarni o'chiradi va
haqiqiy yozuvlar joyida qoladi.
"""
import os, sys

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_demo/db.sqlite"
os.makedirs("/tmp/verify_demo", exist_ok=True)
if os.path.exists("/tmp/verify_demo/db.sqlite"):
    os.remove("/tmp/verify_demo/db.sqlite")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
import main, models, roles
import entry  # noqa: F401
from database import SessionLocal
from auth import hash_password

c = TestClient(main.app)
db = SessionLocal()
fails = []


def ck(n, g, w):
    ok = g == w
    print(("OK  " if ok else "XATO ") + f"{n}: {g}"
          + ("" if ok else f"   (kutilgan {w})"))
    if not ok:
        fails.append(n)


test_b = models.Branch(name="Test filial")
real_b = models.Branch(name="Zafar")
db.add_all([test_b, real_b]); db.commit()
TB, RB = test_b.id, real_b.id

# Haqiqiy filialda bitta chin o'quvchi — unga TEGILMASLIGI kerak
real_s = models.Student(full_name="Haqiqiy Bola", branch_id=RB, status="active")
db.add(real_s); db.commit()
REAL_SID = real_s.id

for uname, role in (("asos", roles.FOUNDER), ("mol", roles.FINANCE_DIRECTOR)):
    db.add(models.User(username=uname, full_name=uname,
                       password_hash=hash_password("Parol123!"),
                       role=role, branch_id=RB, is_active=1))
db.commit()


def H(u):
    t = c.post("/api/auth/login",
               json={"username": u, "password": "Parol123!"}
               ).json()["access_token"]
    return {"Authorization": f"Bearer {t}"}


AS, MOL = H("asos"), H("mol")

print("=== 1. FAQAT ASOSCHI ===")
r = c.post("/api/demo/seed", headers=MOL, json={"branch_id": TB})
ck("moliyachiga yopiq", r.status_code, 403)

print("\n=== 2. HAQIQIY FILIALGA TEGMAYDI ===")
r = c.post("/api/demo/seed", headers=AS, json={"branch_id": RB})
ck("nomida test yo'q -> 400", r.status_code, 400)
ck("sabab tushunarli", "test" in r.json().get("detail", "").lower(), True)
ck("haqiqiy o'quvchi joyida",
   db.query(models.Student).filter(models.Student.branch_id == RB).count(), 1)

print("\n=== 3. TEST FILIALI TO'LDIRILDI ===")
r = c.post("/api/demo/seed", headers=AS,
           json={"branch_id": TB, "students": 100})
ck("status 200", r.status_code, 200)
j = r.json()
ck("100 ta o'quvchi", j["students_total"], 100)
ck("guruhlar ochildi", j["created"]["groups"] >= 5, True)
ck("ustozlar qo'shildi", j["created"]["teachers"] >= 5, True)
ck("xodim akkauntlari", j["created"]["users"] >= 6, True)
ck("darslar bor", j["created"]["lessons"] > 0, True)
ck("yo'qlamalar bor", j["created"]["attendances"] > 0, True)
ck("to'lovlar bor", j["created"]["payments"] > 0, True)
ck("lidlar bor", j["created"]["leads"] > 0, True)
ck("parol qaytdi", bool(j.get("password")), True)

print("\n=== 4. HOLATLAR ARALASH (hayotdagidek) ===")
sts = {}
for s in db.query(models.Student).filter(models.Student.branch_id == TB).all():
    sts[s.status] = sts.get(s.status, 0) + 1
ck("aktivlar bor", sts.get("active", 0) > 50, True)
ck("sinovdagilar bor", sts.get("trial", 0) > 0, True)
ck("muzlatilganlar bor", sts.get("frozen", 0) > 0, True)
ck("arxivdagilar bor", sts.get("archived", 0) > 0, True)

print("\n=== 5. QARZDOR HAM, TO'LAGAN HAM BOR ===")
bals = {}
for p in db.query(models.Payment).all():
    bals[p.student_id] = bals.get(p.student_id, 0) + p.amount
ck("qarzdorlar bor", sum(1 for v in bals.values() if v < -1) > 0, True)
ck("hisobi tozalar bor", sum(1 for v in bals.values() if v >= -1) > 0, True)

print("\n=== 6. DEMO XODIM KIRA OLADI ===")
r = c.post("/api/auth/login",
           json={"username": "demo.admin1", "password": j["password"]})
ck("demo admin login", r.status_code, 200)

print("\n=== 7. IKKI MARTA BOSILSA IKKILANMAYDI ===")
r2 = c.post("/api/demo/seed", headers=AS,
            json={"branch_id": TB, "students": 100})
ck("yangisi qo'shilmadi", r2.json()["created"], 0)
ck("hali ham 100 ta", r2.json()["students_total"], 100)

print("\n=== 8. HOLAT KO'RSATKICHI ===")
r = c.get(f"/api/demo/status?branch_id={TB}", headers=AS)
ck("status 200", r.status_code, 200)
ck("100 ta ko'rinadi", r.json()["students"], 100)

print("\n=== 9. TOZALASH — FAQAT DEMO ===")
r = c.delete(f"/api/demo/seed?branch_id={TB}", headers=AS)
ck("tozalandi", r.status_code, 200)
db.expire_all()
ck("test filialda o'quvchi qolmadi",
   db.query(models.Student).filter(models.Student.branch_id == TB).count(), 0)
ck("guruhlar ketdi",
   db.query(models.Group).filter(models.Group.branch_id == TB).count(), 0)
ck("demo xodimlar ketdi",
   db.query(models.User).filter(
       models.User.username.like("demo.%")).count(), 0)
ck("HAQIQIY o'quvchi joyida",
   db.query(models.Student).get(REAL_SID) is not None, True)
ck("asoschi hisobi joyida",
   db.query(models.User).filter(models.User.username == "asos").count(), 1)

print("\n" + ("HAMMASI O'TDI" if not fails else f"XATOLAR: {fails}"))
sys.exit(1 if fails else 0)
