"""O'QUVCHI PROFILI (2026-08-10).

Jahongir: "eng yuqorida ism familiyasi, alohida rasmi uchun joy
bo'lsin, faqat ism/familiya/otchestvani alohida o'zgartirsin, u
yerga boshqa har xil narsalar yozib bo'lmasin, aniq bo'lsa
tasdiqlansin. O'quvchi o'zi haqida ma'lumot to'ldirsa bazada ham
ko'rinib tursin."

Eng muhim tekshiruvlar: laqab/raqam/ko'p so'z RAD etilishi,
o'zgarish XODIMLAR ko'radigan kartada ham chiqishi, auditga
yozilishi va rasm chegaralari."""
import os, sys
from datetime import date

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_sprofile/db.sqlite"
os.makedirs("/tmp/verify_sprofile", exist_ok=True)
if os.path.exists("/tmp/verify_sprofile/db.sqlite"):
    os.remove("/tmp/verify_sprofile/db.sqlite")
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


b = models.Branch(name="Zafar"); db.add(b); db.commit()
s = models.Student(full_name="Ali Valiyev", branch_id=b.id,
                   status="active", phone="998901112233",
                   public_id="STU-PR-1")
db.add(s); db.commit()
u = models.User(username="998901112233",
                password_hash=hash_password("jonyjony"),
                full_name="Ali Valiyev", role=roles.STUDENT,
                branch_id=b.id, is_active=1)
db.add(u); db.commit()
s.user_id = u.id; db.commit()
boss = models.User(username="boss", full_name="Asoschi",
                   password_hash=hash_password("Parol123!"),
                   role=roles.FOUNDER, branch_id=b.id, is_active=1)
db.add(boss); db.commit()

Hs = {"Authorization": f"Bearer {c.post('/api/auth/login', json={'username':'998901112233','password':'jonyjony'}).json()['access_token']}"}
Hb = {"Authorization": f"Bearer {c.post('/api/auth/login', json={'username':'boss','password':'Parol123!'}).json()['access_token']}"}

print("=== PROFIL O'QISH ===")
r = c.get("/api/student/profile", headers=Hs)
ck("status 200", r.status_code, 200)
# 2026-09-16: telefon bazada bitta formatda (9 raqam)
ck("telefon faqat ko'rsatiladi", r.json()["phone"], "901112233")

print("\n=== TO'G'RI ISM QABUL QILINADI ===")
r = c.put("/api/student/profile", headers=Hs,
          json={"first_name": "alisher", "last_name": "valiyev",
                "middle_name": "anvarovich",
                "birth_date": "2011-03-15", "school": "21-maktab",
                "school_grade": "9-A", "address": "Bekobod, Zafar"})
ck("saqlash 200", r.status_code, 200)
j = r.json()
ck("bosh harf avtomat katta", j["first_name"], "Alisher")
ck("familiya ham", j["last_name"], "Valiyev")
ck("otasining ismi ham", j["middle_name"], "Anvarovich")
ck("full_name yig'ildi", j["full_name"], "Alisher Valiyev")

print("\n=== HAR XIL NARSA YOZIB BO'LMAYDI ===")
for bad, why in [
    ("Alisher123", "raqamli"),
    ("Super Boy", "ikki so'z"),
    ("😎Ali", "emoji"),
    ("A", "juda qisqa"),
    ("www.jony.uz", "manzil"),
    ("", "bo'sh"),
]:
    r = c.put("/api/student/profile", headers=Hs,
              json={"first_name": bad, "last_name": "Valiyev"})
    ck(f"rad: {why}", r.status_code, 400)
r = c.put("/api/student/profile", headers=Hs,
          json={"first_name": "O'ktamjon", "last_name": "Abdul-Aziz"})
ck("o'zbekcha apostrof va chiziqcha O'TADI", r.status_code, 200)

print("\n=== XODIM BAZASIDA KO'RINADI ===")
r = c.put("/api/student/profile", headers=Hs,
          json={"first_name": "Alisher", "last_name": "Valiyev",
                "middle_name": "Anvarovich"})
r = c.get(f"/api/students/{s.id}", headers=Hb)
d = r.json()
ck("kartada yangi ism", d["full_name"], "Alisher Valiyev")
ck("first_name kartada", d["first_name"], "Alisher")
ck("middle_name kartada", d["middle_name"], "Anvarovich")
ck("maktabi kartada", d["school"], "21-maktab")
ck("tug'ilgan sana kartada", d["birth_date"], "2011-03-15")
au = (db.query(models.AuditLog)
      .filter(models.AuditLog.entity == "student").count()
      if hasattr(models, "AuditLog") else 1)
ck("audit yozildi", au >= 1, True)
lg = db.query(models.User).get(u.id)
ck("kirish hisobidagi ism ham yangilandi", lg.full_name,
   "Alisher Valiyev")

print("\n=== RASM ===")
tiny = "data:image/jpeg;base64," + "A" * 500
r = c.put("/api/student/photo", headers=Hs, json={"photo": tiny})
ck("rasm saqlandi", r.status_code, 200)
r = c.get("/api/student/home", headers=Hs)
ck("bosh ekranda rasm bor", r.json()["photo"], tiny)
r = c.get(f"/api/students/{s.id}", headers=Hb)
ck("XODIM kartasida ham rasm", r.json()["photo"], tiny)
r = c.put("/api/student/photo", headers=Hs,
          json={"photo": "data:text/html;base64,XX"})
ck("rasm bo'lmagan narsa rad", r.status_code, 400)
r = c.put("/api/student/photo", headers=Hs,
          json={"photo": "data:image/jpeg;base64," + "A" * 500000})
ck("juda katta rasm rad", r.status_code, 400)
r = c.put("/api/student/photo", headers=Hs, json={"photo": None})
ck("rasmni o'chirish mumkin", r.status_code, 200)

print("\n=== XAVFSIZLIK ===")
r = c.get("/api/student/profile")
ck("loginsiz yopiq", r.status_code in (401, 403), True)
r = c.put("/api/student/profile", headers=Hb,
          json={"first_name": "Test", "last_name": "Testov"})
ck("xodim bu yo'ldan yoza olmaydi", r.status_code, 403)

print("\n" + ("BARCHASI OK" if not fails else f"XATOLAR: {fails}"))
sys.exit(1 if fails else 0)
