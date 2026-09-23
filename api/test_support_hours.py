"""SUPPORT SEANSI: 1-3 SOAT QOIDASI (2026-08-10, Jahongir belgiladi).

"supportlarni senga aytgandim minimum 1 soat bo'lmasa 3 soatgacha
dars o'tishi mumkin, qancha dars o'tganligini o'zi belgilasin"

Shuning uchun: support tugash vaqtini hisoblab o'tirmaydi — necha
soat dars o'tganini TANLAYDI (1/1.5/2/2.5/3), server tugash vaqtini
o'zi chiqaradi. Chegaradan chiqqan seans YOZILMAYDI, chunki oylik
aynan shu yozuvlardan hisoblanadi."""
import os, sys
from datetime import timedelta

os.environ["DATABASE_URL"] = "sqlite:////tmp/vsh/db.sqlite"
os.makedirs("/tmp/vsh", exist_ok=True)
if os.path.exists("/tmp/vsh/db.sqlite"):
    os.remove("/tmp/vsh/db.sqlite")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
import main, models, roles
import entry  # noqa
from database import SessionLocal
from auth import hash_password

c = TestClient(main.app)
db = SessionLocal()
fails = []


def ck(n, g, w):
    ok = g == w
    print(("OK  " if ok else "XATO ") + f"{n}: {g}" + ("" if ok else f"  (kutilgan {w})"))
    if not ok:
        fails.append(n)


b = models.Branch(name="Zafar"); db.add(b); db.commit()
u = models.User(username="sup", full_name="Support Aziza",
                password_hash=hash_password("Parol123!"),
                role=roles.SUPPORT_TEACHER, branch_id=b.id, is_active=1)
db.add(u); db.commit()
t = models.Teacher(full_name="Support Aziza", branch_id=b.id,
                   user_id=u.id, is_active=1)
db.add(t); db.commit()

ut = models.User(username="ust", full_name="Ustoz Anvar",
                 password_hash=hash_password("Parol123!"),
                 role=roles.TEACHER, branch_id=b.id, is_active=1)
db.add(ut); db.commit()
tt = models.Teacher(full_name="Ustoz Anvar", branch_id=b.id,
                    user_id=ut.id, is_active=1)
db.add(tt); db.commit()

gs = []
for i, nm in enumerate(["G1", "G2", "G3", "G4", "G5"]):
    g = models.Group(name=nm, subject="english", level="B1", branch_id=b.id,
                     teacher_id=tt.id, lesson_time="18:00",
                     monthly_fee=500000, lesson_days="135", capacity=15)
    db.add(g); db.commit()
    gs.append(g)
    db.add(models.SupportAssignment(user_id=u.id, group_id=g.id))
db.commit()

H = {"Authorization": f"Bearer {c.post('/api/auth/login', json={'username':'sup','password':'Parol123!'}).json()['access_token']}"}

print("=== TANLOVLAR BACKEND'DAN KELADI ===")
r = c.get("/api/teacher/support-options", headers=H)
ck("status 200", r.status_code, 200)
o = r.json()
ck("soat qadamlari", o["hour_steps"], [1, 1.5, 2, 2.5, 3])
ck("eng kami 1 soat", o["min_hours"], 1)
ck("eng ko'pi 3 soat", o["max_hours"], 3)
ck("guruhlari keladi", len(o["groups"]), 5)

print("\n=== SOATNI O'ZI TANLAYDI (tugash vaqti server hisoblaydi) ===")
r = c.post("/api/me/support-sessions", headers=H,
           json={"group_id": gs[0].id, "start_time": "10:00",
                 "hours": 1.5, "students_count": 6})
ck("1.5 soat qabul qilindi", r.status_code, 200)
ck("90 daqiqa yozildi", r.json()["minutes"], 90)
row = db.query(models.SupportSession).order_by(
    models.SupportSession.id.desc()).first()
ck("tugash vaqti o'zi hisoblandi", row.end_time, "11:30")

print("\n=== CHEGARALAR ===")
r = c.post("/api/me/support-sessions", headers=H,
           json={"group_id": gs[1].id, "start_time": "10:00",
                 "hours": 0.5, "students_count": 6})
ck("0.5 soat RAD ETILADI", r.status_code, 400)
ck("sababi 'kamida' deb aytiladi",
   "kamida" in r.json()["detail"].lower(), True)

r = c.post("/api/me/support-sessions", headers=H,
           json={"group_id": gs[1].id, "start_time": "10:00",
                 "hours": 4, "students_count": 6})
ck("4 soat RAD ETILADI", r.status_code, 400)

r = c.post("/api/me/support-sessions", headers=H,
           json={"group_id": gs[1].id, "start_time": "10:00",
                 "hours": 3, "students_count": 6})
ck("aniq 3 soat QABUL qilinadi", r.status_code, 200)

r = c.post("/api/me/support-sessions", headers=H,
           json={"group_id": gs[2].id, "start_time": "10:00",
                 "hours": 1, "students_count": 6})
ck("aniq 1 soat QABUL qilinadi", r.status_code, 200)

print("\n=== ESKI USUL (tugash vaqti) HAM ISHLAYDI ===")
r = c.post("/api/me/support-sessions", headers=H,
           json={"group_id": gs[3].id, "start_time": "09:00",
                 "end_time": "11:00", "students_count": 5})
ck("2 soatlik oraliq qabul qilindi", r.status_code, 200)
ck("120 daqiqa", r.json()["minutes"], 120)

r = c.post("/api/me/support-sessions", headers=H,
           json={"group_id": gs[4].id, "start_time": "09:00",
                 "end_time": "09:30", "students_count": 5})
ck("yarim soatlik oraliq ham RAD ETILADI", r.status_code, 400)

print("\n=== OYLIK ALOHIDA HISOBLANADI ===")
# Volontyor darajasida oylik umuman hisoblanmaydi (2026-09-23) —
# bu test soat qoidasi haqida, shuning uchun support Junior qilinadi.
_d = SessionLocal()
_d.add(models.StaffGrade(user_id=u.id, grade="junior"))
_d.commit()
_d.close()
r = c.get("/api/me/support-sessions", headers=H)
ck("seanslar ro'yxati 200", r.status_code, 200)
d = r.json()
ck("4 ta seans yozilgan", d["session_count"], 4)
# 1.5 + 3 + 1 + 2 = 7.5 soat
ck("jami soat to'g'ri", d["hours"], 7.5)
ck("oylik hisoblangan", d["salary"] > 0, True)
ck("support formulasi ishlatilgan", "soat x" in d["formula"], True)

print("\n=== USTOZ BU YO'LGA KIRA OLMAYDI (rollar alohida) ===")
Ht = {"Authorization": f"Bearer {c.post('/api/auth/login', json={'username':'ust','password':'Parol123!'}).json()['access_token']}"}
r = c.post("/api/me/support-sessions", headers=Ht,
           json={"group_id": gs[0].id, "start_time": "10:00",
                 "hours": 2, "students_count": 5})
ck("oddiy ustoz support seansi yoza olmaydi", r.status_code, 403)

print("\n" + ("BARCHASI OK" if not fails else f"XATOLAR: {fails}"))
sys.exit(1 if fails else 0)
