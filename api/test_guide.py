"""INTERAKTIV O'RGATUVCHI — holat saqlash (2026-08-23).

Jahongir: "yangi xodim kirsa toliq demo yani onboarding qilinsin
avtomat... profil bolimida mening funksiyalarim bolimi bolsa".

Tekshiriladi: yangi xodimga taklif ko'rsatiladi (intro_seen=false),
dars tugagach belgilanadi, "keyinroq" degani tugatgan hisoblanmaydi,
mashq filiali topiladi, har kim FAQAT o'z holatini ko'radi.
"""
import os, sys

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_guide/db.sqlite"
os.makedirs("/tmp/verify_guide", exist_ok=True)
if os.path.exists("/tmp/verify_guide/db.sqlite"):
    os.remove("/tmp/verify_guide/db.sqlite")
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


real = models.Branch(name="Zafar")
test_b = models.Branch(name="Test - filial")
db.add_all([real, test_b]); db.commit()
TB = test_b.id

for uname, role in (("admin1", roles.ADMINISTRATOR),
                    ("admin2", roles.ADMINISTRATOR)):
    db.add(models.User(username=uname, full_name=uname,
                       password_hash=hash_password("Parol123!"),
                       role=role, branch_id=real.id, is_active=1))
db.commit()


def H(u):
    t = c.post("/api/auth/login",
               json={"username": u, "password": "Parol123!"}
               ).json()["access_token"]
    return {"Authorization": f"Bearer {t}"}


A1, A2 = H("admin1"), H("admin2")

print("=== 1. YANGI XODIM ===")
r = c.get("/api/guide/state", headers=A1)
ck("status 200", r.status_code, 200)
j = r.json()
ck("hali hech narsa o'rganmagan", j["done"], [])
ck("taklif hali ko'rsatilmagan", j["intro_seen"], False)
ck("mashq filiali topildi", j["test_branch_id"], TB)
ck("lavozimi ko'rinadi", j["role"], roles.ADMINISTRATOR)

print("\n=== 2. DARS TUGADI ===")
r = c.post("/api/guide/done", headers=A1, json={"lesson_id": "admin-payment"})
ck("saqlandi", r.json()["state"], "done")
j = c.get("/api/guide/state", headers=A1).json()
ck("ro'yxatda ko'rinadi", j["done"], ["admin-payment"])

print("\n=== 3. IKKI MARTA BOSILSA DUBL BO'LMAYDI ===")
c.post("/api/guide/done", headers=A1, json={"lesson_id": "admin-payment"})
j = c.get("/api/guide/state", headers=A1).json()
ck("hali ham bitta", j["done"], ["admin-payment"])

print("\n=== 4. 'KEYINROQ' — TUGATGAN HISOBLANMAYDI ===")
c.post("/api/guide/done", headers=A1,
       json={"lesson_id": "__intro__", "skipped": True})
j = c.get("/api/guide/state", headers=A1).json()
ck("taklif ko'rsatilgan deb belgilandi", j["intro_seen"], True)
ck("lekin dars ro'yxatiga tushmadi", j["done"], ["admin-payment"])

c.post("/api/guide/done", headers=A1,
       json={"lesson_id": "admin-freeze", "skipped": True})
j = c.get("/api/guide/state", headers=A1).json()
ck("keyinroq dedi — o'rganilgan emas", "admin-freeze" in j["done"], False)
c.post("/api/guide/done", headers=A1, json={"lesson_id": "admin-freeze"})
j = c.get("/api/guide/state", headers=A1).json()
ck("keyin tugatdi — endi o'rganilgan", "admin-freeze" in j["done"], True)

print("\n=== 5. HAR KIM FAQAT O'ZINIKINI KO'RADI ===")
j2 = c.get("/api/guide/state", headers=A2).json()
ck("ikkinchi xodimda bo'sh", j2["done"], [])
ck("unga taklif hali ko'rsatilmagan", j2["intro_seen"], False)

print("\n=== 6. QAYTA O'RGANISH ===")
c.delete("/api/guide/done?lesson_id=admin-payment", headers=A1)
j = c.get("/api/guide/state", headers=A1).json()
ck("belgisi olindi", "admin-payment" in j["done"], False)
ck("boshqasi joyida", "admin-freeze" in j["done"], True)
c.delete("/api/guide/done", headers=A1)
j = c.get("/api/guide/state", headers=A1).json()
ck("hammasi tozalandi", j["done"], [])

print("\n=== 7. TEST FILIALI BO'LMASA HAM YIQILMAYDI ===")
db.query(models.Branch).filter(models.Branch.id == TB).delete()
db.commit()
r = c.get("/api/guide/state", headers=A2)
ck("status 200", r.status_code, 200)
ck("mashq filiali yo'q deb qaytadi", r.json()["test_branch_id"], None)

print("\n=== 8. JADVAL YO'Q BO'LSA — O'ZI TIKLAYDI ===")
# Jonli bazada aynan shu bo'ldi: yangi jadval yaratilmagan edi va
# so'rov 500 qaytardi, ustiga tranzaksiyani buzib boshqa
# bo'limlarni ham yiqitdi. Endi o'zi yaratib davom etishi kerak.
from sqlalchemy import text as _sql_text
import guide as _guide
db.execute(_sql_text("DROP TABLE guide_progress"))
db.commit()
r = c.get("/api/guide/state", headers=A1)
ck("jadval yo'q bo'lsa ham 200", r.status_code, 200)
ck("bo'sh ro'yxat qaytdi", r.json()["done"], [])
r = c.post("/api/guide/done", headers=A1, json={"lesson_id": "admin-payment"})
ck("jadval tiklangach saqlanadi", r.json().get("ok"), True)
j = c.get("/api/guide/state", headers=A1).json()
ck("va o'qiladi", j["done"], ["admin-payment"])

print("\n" + ("HAMMASI O'TDI" if not fails else f"XATOLAR: {fails}"))
sys.exit(1 if fails else 0)
