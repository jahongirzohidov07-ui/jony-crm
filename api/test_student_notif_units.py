"""BILDIRISHNOMALAR + UNIT TANLASH (2026-08-10).

Jahongir: "qo'ng'iroqcha belgisida to'lov vaqti yetgani, imtihon
natijasi chiqqani haqida xabarlar kelib tursin. Unitni tanlab shu
bo'yicha practica qilsin."
"""
import os, sys
from datetime import date, timedelta

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_notif/db.sqlite"
os.makedirs("/tmp/verify_notif", exist_ok=True)
if os.path.exists("/tmp/verify_notif/db.sqlite"):
    os.remove("/tmp/verify_notif/db.sqlite")
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
t = models.Teacher(full_name="Ustoz", branch_id=b.id, is_active=1)
db.add(t); db.commit()
g = models.Group(name="IELTS-N", subject="english", level="step1",
                 branch_id=b.id, teacher_id=t.id, lesson_time="09:00",
                 monthly_fee=500000, lesson_days="mon,wed,fri",
                 capacity=15)
db.add(g); db.commit()
s = models.Student(full_name="Ali Valiyev", branch_id=b.id,
                   group_id=g.id, status="active",
                   phone="998901112233", public_id="STU-NT-1")
db.add(s); db.commit()
u = models.User(username="998901112233",
                password_hash=hash_password("jonyjony"),
                full_name="Ali Valiyev", role=roles.STUDENT,
                branch_id=b.id, is_active=1)
db.add(u); db.commit()
s.user_id = u.id; db.commit()
H = {"Authorization": f"Bearer {c.post('/api/auth/login', json={'username':'998901112233','password':'jonyjony'}).json()['access_token']}"}

print("=== BOSHIDA BILDIRISHNOMA YO'Q ===")
r = c.get("/api/student/notifications", headers=H)
ck("status 200", r.status_code, 200)
ck("bo'sh", len(r.json()["items"]), 0)

print("\n=== TO'LOV XABARI (balans manfiy) ===")
db.add(models.Payment(student_id=s.id, amount=-500000,
                      kind="charge"))
db.commit()
r = c.get("/api/student/notifications", headers=H)
items = r.json()["items"]
pay = [x for x in items if x["kind"] == "payment"]
ck("to'lov xabari bor", len(pay), 1)
ck("sarlavha to'g'ri", pay[0]["title"], "To'lov vaqti keldi")

print("\n=== IMTIHON NATIJASI XABARI ===")
ex = models.Exam(group_id=g.id, kind="unit", unit_no=3,
                 date=date.today() - timedelta(days=2),
                 status="done", max_score=30)
db.add(ex); db.commit()
db.add(models.ExamResult(exam_id=ex.id, student_id=s.id,
                         score=25, percent=83.3))
db.commit()
r = c.get("/api/student/notifications", headers=H)
items = r.json()["items"]
exn = [x for x in items if x["kind"] == "exam"]
ck("imtihon xabari bor", len(exn), 1)
ck("natija matnda", "25" in exn[0]["body"] and "83" in exn[0]["body"],
   True)
ck("latest maydoni bor", bool(r.json()["latest"]), True)

print("\n=== UNITLAR RO'YXATI ===")
r = c.get("/api/student/vocab/units", headers=H)
ck("status 200", r.status_code, 200)
units = r.json()["units"]
ck("59 unit bor", len(units), 59)
ck("tartib raqam bo'yicha", units[0]["key"], "Unit 1")
ck("oxirgisi Unit 59", units[-1]["key"], "Unit 59")
u1_n = units[0]["n"]
ck("Unit 1 da so'z bor", u1_n > 0, True)

print("\n=== UNIT BO'YICHA ROUND ===")
r = c.get("/api/student/vocab/round?game=en_uz&unit=Unit 1", headers=H)
ck("status 200", r.status_code, 200)
d = r.json()
ck("javobda unit ko'rsatilgan", d["unit"], "Unit 1")
# Har bir savol so'zi haqiqatan Unit 1 dan ekanini tekshiramiz
ids = [it["word_id"] for it in d["items"] if "word_id" in it]
w_units = {w.topic for w in db.query(models.VocabWord)
           .filter(models.VocabWord.id.in_(ids or [-1])).all()}
ck("hamma so'z Unit 1 dan", w_units, {"Unit 1"})

print("\n=== UNIT PROGRESSI ===")
w = (db.query(models.VocabWord)
     .filter(models.VocabWord.topic == "Unit 1").first())
c.post("/api/student/vocab/answer", headers=H,
       json={"game": "en_uz", "word_id": w.id,
             "answer": w.translation})
r = c.get("/api/student/vocab/units", headers=H)
u1 = [x for x in r.json()["units"] if x["key"] == "Unit 1"][0]
ck("yechilganlar soni oshdi", u1["solved"], 1)

print("\n=== BALANS, TO'LOV VA IMTIHON TARIXI ===")
r = c.get("/api/student/home", headers=H)
ck("bosh sahifada balans", r.json()["balance"], -500000.0)
r = c.get("/api/student/payments", headers=H)
d = r.json()
ck("to'lovlar tarixi 200", r.status_code, 200)
ck("balans mos", d["balance"], -500000.0)
ck("1 ta yozuv (oylik hisob)", len(d["rows"]), 1)
ck("turi belgilangan", d["rows"][0]["kind_label"], "Oylik hisob")
r = c.get("/api/student/exams", headers=H)
ck("imtihonlar tarixi 200", r.status_code, 200)
ck("1 ta imtihon", len(r.json()["rows"]), 1)
ck("foiz bor", round(r.json()["rows"][0]["percent"]), 83)

print("\n=== XAVFSIZLIK ===")
r = c.get("/api/student/notifications")
ck("loginsiz yopiq", r.status_code in (401, 403), True)
r = c.get("/api/student/payments")
ck("to'lovlar loginsiz yopiq", r.status_code in (401, 403), True)

print("\n" + ("BARCHASI OK" if not fails else f"XATOLAR: {fails}"))
sys.exit(1 if fails else 0)
