"""ARXIVDAN BUTUNLAY O'CHIRISH — FAQAT ASOSCHI (2026-08-22).

Jahongir: "arxivda qidirv va filtr qoyib ber va arxivdagilarni
ochirishni faqat menga qoshib ber".

Tekshiriladi: arxiv ro'yxati qidirish uchun kerakli maydonlarni
qaytaradi (ism, ID, telefon, guruh, filial — frontend shular ustidan
qidiradi), o'chirish moliyachi/admin/HR uchun YOPIQ, asoschi uchun
ochiq va o'chirilgani auditda qoladi.
"""
import os, sys

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_arch/db.sqlite"
os.makedirs("/tmp/verify_arch", exist_ok=True)
if os.path.exists("/tmp/verify_arch/db.sqlite"):
    os.remove("/tmp/verify_arch/db.sqlite")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import date
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


b = models.Branch(name="Zafar"); db.add(b); db.commit()
users = {}
for uname, role in (("asos", roles.FOUNDER),
                    ("mol", roles.FINANCE_DIRECTOR),
                    ("adm", roles.ADMINISTRATOR)):
    u = models.User(username=uname, full_name=uname.title(),
                    password_hash=hash_password("Parol123!"),
                    role=role, branch_id=b.id, is_active=1)
    db.add(u); users[uname] = u
db.commit()

g = models.Group(name="IELTS 1.0", branch_id=b.id)
db.add(g); db.commit()

s1 = models.Student(full_name="Ketgan Bola", branch_id=b.id, group_id=g.id,
                    status="archived", public_id="S1",
                    phone="+998901112233", parent_phone="+998907778899",
                    enrolled_date=date(2026, 1, 10),
                    left_date=date(2026, 7, 20))
s2 = models.Student(full_name="Boshqa Bola", branch_id=b.id,
                    status="archived", public_id="S2",
                    phone="+998935554433", left_date=date(2025, 5, 5))
s3 = models.Student(full_name="Faol Bola", branch_id=b.id, status="active",
                    public_id="S3")
db.add_all([s1, s2, s3]); db.commit()
s1_id, s2_id = s1.id, s2.id

H = {}
for uname in users:
    tok = c.post("/api/auth/login",
                 json={"username": uname, "password": "Parol123!"}
                 ).json()["access_token"]
    H[uname] = {"Authorization": f"Bearer {tok}"}

print("=== ARXIV RO'YXATI (qidiruv uchun maydonlar) ===")
r = c.get("/api/archive/students", headers=H["asos"])
ck("status 200", r.status_code, 200)
j = r.json()
ck("faqat arxivdagilar", len(j["rows"]), 2)
row = [x for x in j["rows"] if x["public_id"] == "S1"][0]
for f in ("full_name", "public_id", "phone", "parent_phone", "group",
          "branch", "left_date", "group_key"):
    ck(f"qidiruv maydoni '{f}' bor", f in row and row[f] is not None, True)
ck("guruh nomi to'g'ri", row["group"], "IELTS 1.0")
ck("ketgan yili ajratsa bo'ladi", row["left_date"][:4], "2026")

print("\n=== O'CHIRISH — BOSHQALARGA YOPIQ ===")
for uname in ("mol", "adm"):
    r = c.delete(f"/api/students/{s2_id}", headers=H[uname])
    ck(f"{uname} uchun 403", r.status_code, 403)
ck("hech kim o'chmadi",
   db.query(models.Student).filter(models.Student.status == "archived").count(), 2)

print("\n=== O'CHIRISH — ASOSCHIGA OCHIQ ===")
r = c.delete(f"/api/students/{s2_id}", headers=H["asos"])
ck("asoschiga 200", r.status_code, 200)
db.expire_all()
ck("bazadan ketdi", db.query(models.Student).get(s2_id), None)
ck("boshqasi joyida", db.query(models.Student).get(s1_id) is not None, True)

print("\n=== AUDITDA IZ QOLDI ===")
a = (db.query(models.AuditLog)
     .filter(models.AuditLog.entity == "student",
             models.AuditLog.action == "delete").all())
ck("audit yozuvi bor", len(a), 1)
ck("kim o'chirgani yozilgan", a[0].user_role if a else None, roles.FOUNDER)
ck("ismi saqlangan", a[0].entity_label if a else None, "Boshqa Bola")

print("\n=== YO'Q O'QUVCHI ===")
r = c.delete("/api/students/999999", headers=H["asos"])
ck("404 qaytaradi", r.status_code, 404)

print("\n" + ("HAMMASI O'TDI" if not fails else f"XATOLAR: {fails}"))
sys.exit(1 if fails else 0)
