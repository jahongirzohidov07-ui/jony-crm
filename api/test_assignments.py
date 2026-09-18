"""TOPSHIRIQLAR (2026-09-18, Jahongir, 4- va 6-bandlar): rejadan yuborish,
avtomat tekshirish (katta-kichik harf, bir nechta javob, qisqartma),
ustoz tekshiruvi (rubrika, izoh, coin), o'quvchi ilovasi (ro'yxat, bugungi
dars, qoldirilgan dars paketi), bildirishnomalar."""
import json
import os
import sys
import tempfile
from datetime import timedelta

_DIR = os.path.join(tempfile.gettempdir(), "assignments_test")
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
import assignments as A                            # noqa: E402

c = TestClient(main.app)
fails = []


def ck(name, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + name + f": {got}" + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


# --- sof funksiyalar: javob solishtirish
ck("gap: katta-kichik harf", A.is_correct("gap", "  AM ", "am"), True)
ck("gap: bir nechta javob", A.is_correct("gap", "so", "so / and"), True)
ck("gap: qisqartma", A.is_correct("gap", "isn't", "is not"), True)
ck("gap: izoh qavsda", A.is_correct("gap", "are", "are (ko'plik)"), True)
ck("gap: xato", A.is_correct("gap", "is", "am"), False)
ck("tf: false/F", (A.is_correct("tf", "false", "F (alarm)"), A.is_correct("tf", "To'g'ri", "T")), (True, True))
ck("mcq", (A.is_correct("mcq", "2", 2), A.is_correct("mcq", 1, 2)), (True, False))

today = roles.local_today()
db = SessionLocal()
b1 = models.Branch(name="Bekobod 1"); db.add(b1); db.commit()
u_t = models.User(username="ustoz", password_hash=hash_password("x"), full_name="Ustoz", role=roles.TEACHER, branch_id=b1.id)
u_s = models.User(username="aziz", password_hash=hash_password("x"), full_name="Aziz Karimov", role=roles.STUDENT, branch_id=b1.id)
u_b = models.User(username="bobur", password_hash=hash_password("x"), full_name="Bobur Aliyev", role=roles.STUDENT, branch_id=b1.id)
db.add_all([u_t, u_s, u_b]); db.commit()
t1 = models.Teacher(full_name="Ustoz", user_id=u_t.id, branch_id=b1.id, subject="english"); db.add(t1); db.commit()
g1 = models.Group(name="IELTS A1", branch_id=b1.id, teacher_id=t1.id, lesson_price=50000, standard_lessons_per_month=12, monthly_fee=600000)
db.add(g1); db.commit()
s1 = models.Student(full_name="Aziz Karimov", branch_id=b1.id, status="active", group_id=g1.id, user_id=u_s.id)
s2 = models.Student(full_name="Bobur Aliyev", branch_id=b1.id, status="active", group_id=g1.id, user_id=u_b.id)
db.add_all([s1, s2]); db.commit()
db.add(models.GroupPlan(group_id=g1.id, course="ielts_1_0", next_lesson_no=7, carry="[]")); db.commit()
prev = models.Lesson(group_id=g1.id, teacher_id=t1.id, date=today - timedelta(days=2), held=1); db.add(prev); db.commit()
db.add(models.Attendance(lesson_id=prev.id, student_id=s1.id, present=0))
db.add(models.LessonRun(lesson_id=prev.id, group_id=g1.id, course="ielts_1_0", lesson_no=6, stages="[]", status="finished"))
db.commit()
G1, S1 = g1.id, s1.id
db.close()


def tok(u):
    return {"Authorization": "Bearer " + c.post("/api/auth/login", json={"username": u, "password": "x"}).json()["access_token"]}


T, S, B = tok("ustoz"), tok("aziz"), tok("bobur")

# --- yuborish mumkin bo'lgan qismlar
parts = c.get("/api/plans/ielts_1_0/7/assignable", headers=T).json()
ck("assignable: vocab+grammar+reading+hw", ([p["part"] for p in parts][:3], any(p["part"].startswith("hw:") for p in parts)), (["vocab", "grammar", "reading"], True))
hw_auto = next((p["part"] for p in parts if p["part"].startswith("hw:") and p["auto"]), None)
hw_write = next((p["part"] for p in parts if p.get("kind") == "writing"), "writing")
ck("avtomat va yozma vazifa bor", (bool(hw_auto), bool(hw_write)), (True, True))

# --- yuborish
r = c.post(f"/api/groups/{G1}/assignments/from-plan", json={"course": "ielts_1_0", "lesson_no": 7, "parts": ["vocab", hw_auto, hw_write], "due_days": 2}, headers=T)
ck("yuborildi 3 ta", (r.status_code, len(r.json())), (200, 3))
A_VOC, A_HW, A_WR = [x["id"] for x in r.json()]
ck("lug'at testi 20 savol, avtomat", (r.json()[0]["questions_count"], r.json()[0]["auto"]), (20, True))
ck("writing ustoz tekshiradi, rubrika", (r.json()[2]["auto"], r.json()[2]["max_score"]), (False, 10.0))
lst = c.get(f"/api/groups/{G1}/assignments", headers=T).json()
ck("guruh ro'yxati", (len(lst), lst[0]["targets"]), (3, 2))

# --- o'quvchi ko'radi
my = c.get("/api/student/assignments", headers=S).json()
ck("o'quvchida 3 ta, bajarilmagan", (len(my["items"]), my["pending"]), (3, 3))
ck("bugungi dars + kartochkalar", (my["today"]["lesson_no"], len(my["today"]["cards"])), (7, 20))
ck("qoldirilgan dars paketi (6-dars)", (my["missed"] or {}).get("lesson_no"), 6)
nt = c.get("/api/student/notifications", headers=S).json()["items"]
ck("bildirishnoma: yangi topshiriq", sum(1 for n in nt if n["kind"] == "assignment"), 3)

# --- lug'at testi: javob kalitsiz keladi, avtomat tekshiriladi
q = c.get(f"/api/student/assignments/{A_VOC}", headers=S).json()
ck("kalit yashirin", all("answer" not in x for x in q["questions"]), True)
db = SessionLocal()
qs = json.loads(db.query(models.Assignment).get(A_VOC).questions); db.close()
full = {str(i): x["answer"] for i, x in enumerate(qs)}
answers = dict(full); answers["3"] = (qs[3]["answer"] + 1) % 4   # bitta xato
r = c.post(f"/api/student/assignments/{A_VOC}/submit", json={"answers": answers}, headers=S).json()
ck("avtomat: 19/20, coin yo'q", (r["status"], r["auto_score"], r["auto_max"], r["coins"]), ("graded", 19.0, 20.0, 0))
ck("xatolar ro'yxati", [x["i"] for x in r["review"] if not x["ok"]], [3])
r2 = c.post(f"/api/student/assignments/{A_VOC}/submit", json={"answers": full}, headers=S).json()
ck("xatolar ustida qayta: 20/20, lekin coin yo'q", (r2["attempt"], r2["auto_score"], r2["coins"]), (2, 20.0, 0))
r = c.post(f"/api/student/assignments/{A_VOC}/submit", json={"answers": full}, headers=B).json()
ck("100% birinchi urinish — 1 coin", (r["auto_score"], r["coins"]), (20.0, 1))

# --- gap vazifasi: katta harf, bo'sh joy
db = SessionLocal(); qs2 = json.loads(db.query(models.Assignment).get(A_HW).questions); db.close()
ans2 = {str(i): x["answer"].upper() + " " for i, x in enumerate(qs2)}
r = c.post(f"/api/student/assignments/{A_HW}/submit", json={"answers": ans2}, headers=S).json()
ck("gap: katta harf bilan 100%", r["auto_score"] == r["auto_max"], True)

# --- writing: ustoz tekshiradi
r = c.post(f"/api/student/assignments/{A_WR}/submit", json={"text": "I am go to school every day. I am reading now."}, headers=S).json()
ck("writing submitted", r["status"], "submitted")
SUB = r["id"]
ck("ikkinchi marta yo'q", c.post(f"/api/student/assignments/{A_WR}/submit", json={"text": "x"}, headers=S).status_code, 400)
chk = c.get("/api/teacher/checks", headers=T).json()
ck("ustozda tekshirish kutayotgan 1", (len(chk), chk[0]["student"]), (1, "Aziz Karimov"))
det = c.get(f"/api/submissions/{SUB}", headers=T).json()
ck("detal: rubrika 4 mezon, tayyor izohlar", (len(det["rubric"]), len(det["canned"]) > 5), (4, True))
ai = c.post(f"/api/submissions/{SUB}/ai-review", headers=T).json()
ck("AI/evristika tavsiya", isinstance(ai.get("errors"), list) and "comment_uz" in ai, True)
r = c.post(f"/api/submissions/{SUB}/grade", json={"score": 9, "rubric_scores": {"Grammatika to'g'riligi": 2}, "comment": "Yaxshi!"}, headers=T).json()
ck("baholandi 9/10 → 2 coin", (r["status"], r["teacher_score"], r["coins"]), ("graded", 9.0, 2))
ck("tekshirish ro'yxati bo'shadi", c.get("/api/teacher/checks", headers=T).json(), [])
my = c.get("/api/student/assignments", headers=S).json()
wr = next(i for i in my["items"] if i["id"] == A_WR)
ck("o'quvchida izoh + ball", (wr["submission"]["comment"], wr["submission"]["teacher_score"]), ("Yaxshi!", 9.0))
nt = c.get("/api/student/notifications", headers=S).json()["items"]
ck("bildirishnoma: tekshirildi", any(n["title"] == "Tekshirildi" for n in nt), True)
db = SessionLocal()
ck("coin yozuvlari (assignment)", db.query(models.CoinEntry).filter(models.CoinEntry.source == "assignment").count(), 2)
db.close()

# --- qoldirilgan dars: shaxsiy lug'at testi
r = c.post("/api/student/assignments/missed-test", headers=S)
ck("missed-test shaxsiy", (r.status_code, r.json()["student_id"] == S1, r.json()["lesson_no"]), (200, True, 6))
ck("Boburga ko'rinmaydi", any(i["id"] == r.json()["id"] for i in c.get("/api/student/assignments", headers=B).json()["items"]), False)

print("\nJAMI XATO:", len(fails), fails)
sys.exit(1 if fails else 0)
