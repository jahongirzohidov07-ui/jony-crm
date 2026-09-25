"""UNIT TIZIMI V2 (2026-08-11): to'g'ri 33 unit, 3x/6x/99%/ustoz tick.

Jahongir: "botda har unitda 116 ta atrofida so'z bor edi... menga
faqat 33 unit so'zlarni ber. Har so'zni 3 marta topsa ko'k, 6 marta
topsa yashil, 99% gacha o'zi yig'adi, ustoz tick qo'ysa 100%."
"""
import os, sys

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_vu2/db.sqlite"
os.makedirs("/tmp/verify_vu2", exist_ok=True)
if os.path.exists("/tmp/verify_vu2/db.sqlite"):
    os.remove("/tmp/verify_vu2/db.sqlite")
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
tu = models.User(username="ust", full_name="Ustoz",
                 password_hash=hash_password("Parol123!"),
                 role=roles.TEACHER, branch_id=b.id, is_active=1)
db.add(tu); db.commit()
t = models.Teacher(full_name="Ustoz", branch_id=b.id, user_id=tu.id,
                   is_active=1)
db.add(t); db.commit()
g = models.Group(name="IELTS-V", subject="english", level="step1",
                 branch_id=b.id, teacher_id=t.id, lesson_time="09:00",
                 monthly_fee=500000, lesson_days="mon,wed,fri",
                 capacity=15)
db.add(g); db.commit()
s = models.Student(full_name="Ali Valiyev", branch_id=b.id,
                   group_id=g.id, status="active",
                   phone="998901112233", public_id="STU-VU-1")
db.add(s); db.commit()
u = models.User(username="998901112233",
                password_hash=hash_password("jonyjony"),
                full_name="Ali Valiyev", role=roles.STUDENT,
                branch_id=b.id, is_active=1)
db.add(u); db.commit()
s.user_id = u.id; db.commit()

Hs = {"Authorization": f"Bearer {c.post('/api/auth/login', json={'username':'998901112233','password':'jonyjony'}).json()['access_token']}"}
Ht = {"Authorization": f"Bearer {c.post('/api/auth/login', json={'username':'ust','password':'Parol123!'}).json()['access_token']}"}

print("=== 1–33 BOT UNITLARI (SAT YO'Q) + 34+ CHASTOTA UNITLARI ===")
r = c.get("/api/student/vocab/units", headers=Hs)
units = r.json()["units"]
# 2026-09-25: Jahongir "umumiy 100ta unit bolsin" — 34–100 unitlar
# qo'shildi (vocab_extra_seed). SAT bo'limi baribir yo'q: 1–33
# botniki, 34+ chastota bo'yicha.
ck("33 dan ko'p unit", len(units) > 33, True)
ck("birinchi 33 tasi bot unitlari",
   [u["key"] for u in units[:33]], [f"Unit {i}" for i in range(1, 34)])
ck("Unit 1 da 116 so'z", units[0]["n"], 116)
ck("boshida 0%", units[0]["percent"], 0)
ck("rangi ko'k", units[0]["tone"], "blue")

print("\n=== 3 MARTA -> O'RGANILGAN, FOIZ 99 CAP ===")
w = (db.query(models.VocabWord)
     .filter(models.VocabWord.topic == "Unit 1",
             (models.VocabWord.language == "en")
             | (models.VocabWord.language.is_(None))).first())
for _ in range(3):
    db.add(models.VocabAttempt(student_id=s.id, word_id=w.id,
                               game="en_uz", correct=1,
                               date=date.today()))
db.commit()
r = c.get("/api/student/vocab/units", headers=Hs)
u1 = r.json()["units"][0]
ck("learned3 = 1", u1["learned3"], 1)
ck("foiz > 0", u1["percent"] >= 1, True)

# Hammasini 3 martadan "o'rgangan" qilamiz - foiz 99 dan oshmasin
ids = [x.id for x in db.query(models.VocabWord)
       .filter(models.VocabWord.topic == "Unit 1",
               (models.VocabWord.language == "en")
               | (models.VocabWord.language.is_(None))).all()]
for wid in ids:
    for _ in range(3):
        db.add(models.VocabAttempt(student_id=s.id, word_id=wid,
                                   game="en_uz", correct=1,
                                   date=date.today()))
db.commit()
r = c.get("/api/student/vocab/units", headers=Hs)
u1 = r.json()["units"][0]
ck("hammasi o'rganilgan", u1["learned3"], u1["n"])
ck("LEKIN 99% dan oshmaydi", u1["percent"], 99)
ck("hali ko'k (6x emas)", u1["tone"], "blue")

print("\n=== 6 MARTA -> YASHIL ===")
for wid in ids:
    for _ in range(3):
        db.add(models.VocabAttempt(student_id=s.id, word_id=wid,
                                   game="en_uz", correct=1,
                                   date=date.today()))
db.commit()
r = c.get("/api/student/vocab/units", headers=Hs)
u1 = r.json()["units"][0]
ck("learned6 to'liq", u1["learned6"], u1["n"])
ck("rangi yashil", u1["tone"], "green")
ck("baribir 99%", u1["percent"], 99)

print("\n=== USTOZ TICK -> 100% ===")
r = c.post("/api/teacher/vocab-pass", headers=Ht,
           json={"student_id": s.id, "unit": "Unit 1", "passed": True})
ck("tasdiqlash 200", r.status_code, 200)
r = c.get("/api/student/vocab/units", headers=Hs)
u1 = r.json()["units"][0]
ck("ENDI 100%", u1["percent"], 100)
ck("passed belgisi", u1["passed"], True)
ck("oltin rang", u1["tone"], "gold")

r = c.post("/api/teacher/vocab-pass", headers=Ht,
           json={"student_id": s.id, "unit": "Unit 1",
                 "passed": False})
r = c.get("/api/student/vocab/units", headers=Hs)
ck("bekor qilinsa yana 99%", r.json()["units"][0]["percent"], 99)

print("\n=== BOSHQA USTOZ TASDIQLAY OLMAYDI ===")
tu2 = models.User(username="ust2", full_name="Begona Ustoz",
                  password_hash=hash_password("Parol123!"),
                  role=roles.TEACHER, branch_id=b.id, is_active=1)
db.add(tu2); db.commit()
t2 = models.Teacher(full_name="Begona Ustoz", branch_id=b.id,
                    user_id=tu2.id, is_active=1)
db.add(t2); db.commit()
H2 = {"Authorization": f"Bearer {c.post('/api/auth/login', json={'username':'ust2','password':'Parol123!'}).json()['access_token']}"}
r = c.post("/api/teacher/vocab-pass", headers=H2,
           json={"student_id": s.id, "unit": "Unit 2", "passed": True})
ck("begona ustoz 403", r.status_code, 403)

print("\n=== TIL: RUSCHA LUG'AT ===")
r = c.get("/api/student/vocab/units?language=ru", headers=Hs)
ru = r.json()["units"]
ck("rus unitlari bor", len(ru), 30)
r = c.get("/api/student/vocab/round?game=en_uz&language=ru&unit=Unit 1",
          headers=Hs)
ck("ruscha round ochiladi", r.status_code, 200)

print("\n" + ("BARCHASI OK" if not fails else f"XATOLAR: {fails}"))
sys.exit(1 if fails else 0)
