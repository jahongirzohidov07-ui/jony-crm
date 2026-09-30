"""GURUH ARXIVI (2026-09-30).

Jahongir: "guruhda o'quvchi qolmagan yoki faol bo'lmagan guruhlarni
arxivga tushirib ko'rinmaydigan qilish funksiyasini qo'sh".

Tekshiriladi:
  1. Taklif ro'yxati: faqat hozirgi o'quvchisi yo'q guruhlar (faol,
     sinov, muzlatilgan va qo'shimcha bog'lanish ham hisoblanadi).
  2. O'quvchisi bor guruh arxivlanmaydi (400); bulk — o'tkazib yuboradi.
  3. Arxivda: GET /api/groups da yo'q, ?archived=1 da bor; kelajakdagi
     bo'sh darslar olinadi, o'tgan dars joyida; support bo'shatiladi;
     ustoz kabinetida yo'q; dars avtomat yaratilmaydi; o'quvchi
     qo'shib bo'lmaydi.
  4. Qaytarish: yana ro'yxatda.
  5. Ruxsat: administrator — 403; audit yoziladi.
"""
import os
import sys
import tempfile
from datetime import date, timedelta

_DIR = os.path.join(tempfile.gettempdir(), "group_archive_test")
os.makedirs(_DIR, exist_ok=True)
_DB = os.path.join(_DIR, "db.sqlite")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace(chr(92), "/")
if os.path.exists(_DB):
    os.remove(_DB)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                         # noqa: E402
import entry                                       # noqa: E402,F401
import common                                      # noqa: E402
import groups_lessons                              # noqa: E402
from database import SessionLocal                  # noqa: E402
from auth import hash_password                     # noqa: E402

c = TestClient(main.app)
fails = []


def ck(name, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + name + f": {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


db = SessionLocal()
b = models.Branch(name="Zafar"); db.add(b); db.commit()


def user(login, role):
    u = models.User(username=login, password_hash=hash_password("x"),
                    full_name=login.upper(), role=role, branch_id=b.id,
                    is_active=1)
    db.add(u); db.commit()
    return u


user("asos", roles.FOUNDER)
user("adm", roles.ADMINISTRATOR)
user("salesadm", roles.SALES_MANAGER)
tu = user("ust", roles.TEACHER)
sup = user("sup", roles.SUPPORT_TEACHER)
t = models.Teacher(full_name="USTOZ", branch_id=b.id, is_active=1,
                   user_id=tu.id)
db.add(t); db.commit()


def grp(name):
    g = models.Group(name=name, branch_id=b.id, teacher_id=t.id,
                     lesson_days="mon,wed,fri", lesson_time="14:00",
                     lesson_price=40_000, monthly_fee=480_000)
    db.add(g); db.commit()
    return g


empty = grp("Bo'sh guruh")
live = grp("Faol guruh")
frozen = grp("Muzlatilgan guruh")
linked = grp("Qo'shimcha guruh")
db.add(models.Student(full_name="Faol bola", branch_id=b.id,
                      group_id=live.id, status="active"))
db.add(models.Student(full_name="Muz bola", branch_id=b.id,
                      group_id=frozen.id, status="frozen"))
lb = models.Student(full_name="Ikki guruhli", branch_id=b.id,
                    group_id=live.id, status="active")
db.add(lb); db.commit()
db.add(models.StudentGroupLink(student_id=lb.id, group_id=linked.id,
                               active=1))
# Bo'sh guruhda eski ketgan o'quvchi, o'tgan va kelajak darslar, support
db.add(models.Student(full_name="Ketgan", branch_id=b.id,
                      group_id=empty.id, status="left"))
today = roles.local_today()
db.add(models.Lesson(group_id=empty.id, teacher_id=t.id,
                     date=today - timedelta(days=20), held=1))
db.add(models.Lesson(group_id=empty.id, teacher_id=t.id,
                     date=today + timedelta(days=3), held=0))
db.add(models.SupportAssignment(user_id=sup.id, group_id=empty.id,
                                days="mon", start="15:00", end="16:00"))
db.commit()
EID, LID = empty.id, live.id


def tok(u):
    r = c.post("/api/auth/login", json={"username": u, "password": "x"})
    return {"Authorization": "Bearer " + r.json()["access_token"]}


HF, HA, HT = tok("asos"), tok("adm"), tok("ust")

print("=== 1. TAKLIF RO'YXATI ===")
r = c.get("/api/groups/archive-candidates", headers=HF)
ck("status", r.status_code, 200)
names = [x["name"] for x in r.json()["rows"]]
ck("faqat bo'sh guruh", names, ["Bo'sh guruh"])
row = r.json()["rows"][0]
ck("oxirgi dars 20 kun oldin", row["idle_days"], 20)
ck("ilgari o'qiganlar", row["past_students"], 1)

print("\n=== 2. O'QUVCHISI BOR GURUH ARXIVLANMAYDI ===")
r = c.post(f"/api/groups/{LID}/archive", headers=HF, json={})
ck("faol guruh — 400", r.status_code, 400)
r = c.post("/api/groups/archive-bulk", headers=HF,
           json={"ids": [frozen.id, linked.id], "note": "x"})
ck("muzlatilgan va qo'shimcha bog'langan o'tkazildi",
   ([x["name"] for x in r.json()["archived"]],
    sorted(x["name"] for x in r.json()["skipped"])),
   ([], ["Muzlatilgan guruh", "Qo'shimcha guruh"]))
r = c.post(f"/api/groups/{EID}/archive", headers=HA, json={})
ck("administrator — 403", r.status_code, 403)

print("\n=== 3. ARXIVLASH ===")
r = c.post("/api/groups/archive-bulk", headers=HF,
           json={"ids": [EID], "note": "Kurs tugadi"})
ck("arxivlandi", [x["name"] for x in r.json()["archived"]], ["Bo'sh guruh"])
ck("support tarixi saqlandi", r.json()["archived"][0]["supports_released"],
   [])
ck("kelajak darsi saqlandi", r.json()["archived"][0]["lessons_removed"], 0)
db.expire_all()
ck("o'tgan dars joyida", db.query(models.Lesson).filter(
    models.Lesson.group_id == EID, models.Lesson.held == 1).count(), 1)
names = [g["name"] for g in c.get("/api/groups", headers=HF).json()]
ck("ro'yxatda yo'q", "Bo'sh guruh" in names, False)
arch = c.get("/api/groups?archived=1", headers=HF).json()
ck("arxiv ro'yxatida bor", [g["name"] for g in arch], ["Bo'sh guruh"])
ck("sabab va kim", (arch[0]["archive_note"], arch[0]["archived_by"]),
   ("Kurs tugadi", "ASOS"))
r = c.get("/api/me/groups", headers=HT)
ck("ustoz kabinetida yo'q",
   "Bo'sh guruh" in str(r.json()), False)
g = db.query(models.Group).get(EID)
first = today.replace(day=1)
groups_lessons._sync_scheduled_lessons(
    db, g, first, first + timedelta(days=60))
db.commit()
ck("dars avtomat yaratilmadi", db.query(models.Lesson).filter(
    models.Lesson.group_id == EID, models.Lesson.held == 0).count(), 1)
st = db.query(models.Student).filter_by(full_name="Ketgan").one()
probs = common._check_enrolment(db, st, g)
ck("o'quvchi qo'shib bo'lmaydi",
   [(p["key"], p["severity"]) for p in probs], [("group_archived", "block")])
r = c.get("/api/groups/archive-candidates", headers=HF)
ck("taklifda endi yo'q", [x["name"] for x in r.json()["rows"]], [])

print("\n=== 4. QAYTARISH ===")
r = c.post(f"/api/groups/{EID}/restore", headers=HF)
ck("qaytarildi", r.status_code, 200)
names = [g["name"] for g in c.get("/api/groups", headers=HF).json()]
ck("yana ro'yxatda", "Bo'sh guruh" in names, True)

print("\n=== 5. AUDIT ===")
acts = [a.action for a in db.query(models.AuditLog)
        .filter(models.AuditLog.entity == "group",
                models.AuditLog.entity_id == EID).all()]
ck("arxiv va qaytarish yozildi", sorted(acts), ["archive", "restore"])

print("=== 6. ADMIN CREATE AND DELETE-AS-ARCHIVE ===")
r = c.post("/api/groups", headers=HA, json={"name": "Admin created", "branch_id": b.id})
ck("administrator creates group", r.status_code, 200)
HS = tok("salesadm")
r = c.post("/api/groups", headers=HS, json={"name": "Reception admin created", "branch_id": b.id})
ck("second administrator role creates group", r.status_code, 200)
other = models.Branch(name="Other"); db.add(other); db.commit()
r = c.post("/api/groups", headers=HA, json={"name": "Wrong branch", "branch_id": other.id})
ck("other branch denied", r.status_code, 403)
r = c.post("/api/groups", headers=HS, json={"name": "Wrong branch sales", "branch_id": other.id})
ck("second administrator other branch denied", r.status_code, 403)
r = c.post("/api/groups", headers=HT, json={"name": "Teacher created", "branch_id": b.id})
ck("teacher cannot create", r.status_code, 403)
student = db.query(models.Student).filter_by(group_id=LID, status="active").first()
lesson = models.Lesson(group_id=LID, teacher_id=t.id, date=today, held=1)
db.add(lesson); db.flush()
att = models.Attendance(lesson_id=lesson.id, student_id=student.id, present=1)
grade = models.DailyGrade(lesson_id=lesson.id, student_id=student.id, score=5)
db.add_all([att, grade]); db.commit()
ids = (lesson.id, att.id, grade.id, student.id)
r = c.delete(f"/api/groups/{LID}", headers=HF)
ck("delete archives populated group", r.status_code, 200)
db.expire_all()
ck("group kept", db.get(models.Group, LID).archived_at is not None, True)
ck("lesson kept", db.get(models.Lesson, ids[0]) is not None, True)
ck("attendance kept", db.get(models.Attendance, ids[1]).present, 1)
ck("grade kept", db.get(models.DailyGrade, ids[2]).score, 5)
ck("student link kept", db.get(models.Student, ids[3]).group_id, LID)
ck("repeat delete safe", c.delete(f"/api/groups/{LID}", headers=HF).status_code, 200)
for path in ("/api/timetable", "/api/timetable/grid?day=mon"):
    r = c.get(path, headers=HF)
    if path.startswith("/api/timetable"):
        ck(path + " status", r.status_code, 200)
        ck(path + " hides archived", "Faol guruh" in r.text, False)
ck("restore works", c.post(f"/api/groups/{LID}/restore", headers=HF).status_code, 200)
ck("restored timetable", "Faol guruh" in c.get("/api/timetable", headers=HF).text, True)

print()
if fails:
    print(f"XATO: {len(fails)} ta tekshiruv o'tmadi")
    for f in fails:
        print("   - " + f)
    sys.exit(1)
print("HAMMASI O'TDI")
sys.exit(0)
