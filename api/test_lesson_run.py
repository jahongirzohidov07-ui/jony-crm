"""DARS BOSHQARUVI (2026-09-18): guruh ↔ reja, bugungi ish oynasi,
"Darsni boshlash" rejimi, ko'chgan bosqichlar. Jahongir: "Har bir guruhda
katta 'Darsni boshlash' tugmasi ... Dars tugallanmasa, qolgan qismi
keyingi darsga ko'chadi. Guruhning haqiqiy o'tgan joyi saqlanadi."
"""
import os
import sys
import tempfile
from datetime import timedelta

_DIR = os.path.join(tempfile.gettempdir(), "lesson_run_test")
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
    print(("OK  " if ok else "XATO ") + name + f": {got}" + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


today = roles.local_today()
db = SessionLocal()
b1 = models.Branch(name="Bekobod 1"); db.add(b1); db.commit()
u_t = models.User(username="ustoz", password_hash=hash_password("x"), full_name="Ustoz", role=roles.TEACHER, branch_id=b1.id)
u_o = models.User(username="ustoz2", password_hash=hash_password("x"), full_name="Boshqa", role=roles.TEACHER, branch_id=b1.id)
db.add_all([u_t, u_o]); db.commit()
t1 = models.Teacher(full_name="Ustoz", user_id=u_t.id, branch_id=b1.id, subject="english")
t2 = models.Teacher(full_name="Boshqa", user_id=u_o.id, branch_id=b1.id, subject="english")
db.add_all([t1, t2]); db.commit()
g1 = models.Group(name="IELTS A1", branch_id=b1.id, teacher_id=t1.id, lesson_price=50000,
                  standard_lessons_per_month=12, monthly_fee=600000, lesson_time="15:00")
g2 = models.Group(name="Boshqa guruh", branch_id=b1.id, teacher_id=t2.id, lesson_price=50000,
                  standard_lessons_per_month=12, monthly_fee=600000)
db.add_all([g1, g2]); db.commit()
s1 = models.Student(full_name="Aziz Karimov", branch_id=b1.id, status="active", group_id=g1.id)
s2 = models.Student(full_name="Bobur Aliyev", branch_id=b1.id, status="active", group_id=g1.id)
db.add_all([s1, s2]); db.commit()
prev = models.Lesson(group_id=g1.id, teacher_id=t1.id, date=today - timedelta(days=2), held=1)
cur = models.Lesson(group_id=g1.id, teacher_id=t1.id, date=today, held=0)
other = models.Lesson(group_id=g2.id, teacher_id=t2.id, date=today, held=0)
db.add_all([prev, cur, other]); db.commit()
db.add_all([models.Attendance(lesson_id=prev.id, student_id=s1.id, present=1, homework=0),
            models.Attendance(lesson_id=prev.id, student_id=s2.id, present=1, homework=2),
            models.DailyGrade(lesson_id=prev.id, student_id=s2.id, score=2)])
db.commit()
G1, G2, CUR = g1.id, g2.id, cur.id
db.close()


def tok(u):
    return {"Authorization": "Bearer " + c.post("/api/auth/login", json={"username": u, "password": "x"}).json()["access_token"]}


T = tok("ustoz")

# --- bugungi ish oynasi (reja yo'q)
r = c.get("/api/teacher/plan-today", headers=T)
ck("plan-today 200", r.status_code, 200)
it = r.json()["items"]
ck("faqat o'z guruhi", [x["group"] for x in it], ["IELTS A1"])
ck("reja bog'lanmagan", it[0]["plan"], None)
ck("uy vazifasini bajarmagan", it[0]["homework_missing"], ["Aziz Karimov"])
ck("yordam kerak (past baho)", [h["name"] for h in it[0]["help_needed"]], ["Bobur Aliyev"])
# 2026-09-27: IELTS 6.0 (Foundation) to'liq tayyor bo'ldi — ro'yxatda; 7.0 hali tayyor emas
ck("kurslar ro'yxati (faqat tayyor)", [x["course"] for x in r.json()["courses"]], ["ielts_1_0", "ielts_2_0", "ielts_3_0", "ielts_4_0", "ielts_5_0", "ielts_6_0"])
ck("rejasiz boshlab bo'lmaydi", c.post(f"/api/lessons/{CUR}/run", headers=T).status_code, 400)

# --- guruhni rejaga bog'lash
ck("tayyor bo'lmagan daraja", c.put(f"/api/groups/{G1}/plan", json={"course": "ielts_7_0"}, headers=T).status_code, 400)
ck("boshqa ustoz guruhi", c.put(f"/api/groups/{G2}/plan", json={"course": "ielts_1_0"}, headers=T).status_code, 403)
r = c.put(f"/api/groups/{G1}/plan", json={"course": "ielts_1_0", "next_lesson_no": 7}, headers=T)
ck("bog'landi 7-dars", (r.status_code, r.json()["next_lesson_no"], "PRESENT CONTINUOUS" in r.json()["next_title"]), (200, 7, True))
it = c.get("/api/teacher/plan-today", headers=T).json()["items"]
ck("oynada reja ko'rinadi", it[0]["plan"]["next_lesson_no"], 7)
# Noto'g'ri bog'langan rejani o'zgartirish (2026-09-21)
_re = c.put(f"/api/groups/{G1}/plan", json={"course": "ielts_2_0", "next_lesson_no": 3}, headers=T)
ck("reja o'zgartiriladi", (_re.status_code, _re.json().get("course"), _re.json().get("next_lesson_no")), (200, "ielts_2_0", 3))
_back = c.put(f"/api/groups/{G1}/plan", json={"course": "ielts_1_0", "next_lesson_no": 7}, headers=T)
ck("reja qaytariladi", (_back.status_code, _back.json().get("course")), (200, "ielts_1_0"))

# --- darsni boshlash
r = c.post(f"/api/lessons/{CUR}/run", headers=T)
ck("run 200", r.status_code, 200)
run = r.json()
RID = run["id"]
ck("run holati", (run["status"], run["lesson_no"], run["current"], run["total"] >= 8), ("running", 7, 0, True))
ck("reja matni bilan", run["plan"]["no"], 7)
ck("o'quvchilar", [s["name"] for s in run["students"]], ["Aziz Karimov", "Bobur Aliyev"])
ck("ikkinchi marta — o'sha run", c.post(f"/api/lessons/{CUR}/run", headers=T).json()["id"], RID)
ck("boshqa ustoz ko'rolmaydi", c.get(f"/api/runs/{RID}", headers=tok("ustoz2")).status_code, 403)

# --- bosqichlar
r = c.put(f"/api/runs/{RID}", json={"done": [0, 1, 2], "current": 3, "notes": "Aziz -s ni unutyapti"}, headers=T)
ck("update", (r.status_code, r.json()["done_count"], r.json()["current"], r.json()["notes"]), (200, 3, 3, "Aziz -s ni unutyapti"))
it = c.get("/api/teacher/plan-today", headers=T).json()["items"]
ck("oynada 'davom ettirish'", (it[0]["run"]["status"], it[0]["run"]["done"]), ("running", 3))

# --- yakunlash: tugallanmagan bosqichlar ko'chadi, reja +1
r = c.post(f"/api/runs/{RID}/finish", json={"advance": True}, headers=T)
ck("finish", (r.status_code, r.json()["next_lesson_no"], len(r.json()["carry"]) > 0), (200, 8, True))
carry = r.json()["carry"]
ck("xizmat bosqichlari ko'chmaydi", any("uyga vazifa" in x.lower() or "salomlash" in x.lower() for x in carry), False)
ck("yakunlangach o'zgartirib bo'lmaydi", c.put(f"/api/runs/{RID}", json={"current": 1}, headers=T).status_code, 400)
p = c.get(f"/api/groups/{G1}/plan", headers=T).json()["plan"]
ck("guruh 8-darsda, ko'chgan bor", (p["next_lesson_no"], p["carry"] == carry), (8, True))

# keyingi dars: ko'chgan bosqichlar boshida
db = SessionLocal()
nxt = models.Lesson(group_id=G1, teacher_id=None, date=today + timedelta(days=2), held=0)
db.add(nxt); db.commit(); NXT = nxt.id; db.close()
r2 = c.post(f"/api/lessons/{NXT}/run", headers=T).json()
ck("keyingi run 8-dars", r2["lesson_no"], 8)
ck("ko'chgan bosqichlar boshida", (r2["stages"][0]["carried"], r2["stages"][0]["title"].startswith("Ko'chgan:")), (True, True))
r = c.post(f"/api/runs/{r2['id']}/finish", json={"advance": False}, headers=T).json()
ck("advance=False — 8-dars qoladi", r["next_lesson_no"], 8)

print("\nJAMI XATO:", len(fails), fails)
sys.exit(1 if fails else 0)
