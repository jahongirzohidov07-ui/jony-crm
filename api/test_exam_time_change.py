"""USTOZ IMTIHON VAQTINI O'ZGARTIRADI (2026-10-05).

Jahongir: "ustozlarga imtixon vaqtini o'zgartirishga ruxsat berish kerak".

Tekshiriladi:
  1. Yangi (qabul qilinmagan) buyurtma: kun/vaqt o'zgaradi, filial
     examinerlariga vazifa boradi.
  2. Qabul qilingan: examiner o'z o'rnida, imtihon (Exam) sanasi ham
     ko'chadi, faqat o'sha examinerga vazifa.
  3. Qoidalar: o'tgan kun / bugun, 60 kundan uzoq, o'zgarishsiz,
     shu kunga guruhda boshqa buyurtma — 400.
  4. Examiner taklifi kutilayotganda — 400; yopilgan buyurtma — 400.
  5. Boshqa ustozning buyurtmasi — 403. Audit yoziladi.
"""
import os
import sys
import tempfile
from datetime import timedelta

_DIR = os.path.join(tempfile.gettempdir(), "exam_time_change_test")
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
    print(("OK  " if ok else "XATO ") + name + f": {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


db = SessionLocal()
b = models.Branch(name="A"); db.add(b); db.commit()


def user(login, role):
    u = models.User(username=login, password_hash=hash_password("x"),
                    full_name=login.upper(), role=role, branch_id=b.id,
                    is_active=1)
    db.add(u); db.commit()
    return u


ut = user("ust", roles.TEACHER)
ut2 = user("ust2", roles.TEACHER)
ex = user("ex", roles.EXAMINER)
ex2 = user("ex2", roles.EXAMINER)
t = models.Teacher(full_name="USTOZ", branch_id=b.id, user_id=ut.id, is_active=1)
t2 = models.Teacher(full_name="USTOZ2", branch_id=b.id, user_id=ut2.id, is_active=1)
db.add_all([t, t2]); db.commit()
g = models.Group(name="G1", branch_id=b.id, teacher_id=t.id,
                 lesson_time="09:00", lesson_days="mon,wed,fri",
                 monthly_fee=480_000)
db.add(g); db.commit()
for i in range(3):
    db.add(models.Student(full_name=f"S{i}", branch_id=b.id, group_id=g.id,
                          status="active"))
db.commit()
GID, EX, EX2 = g.id, ex.id, ex2.id
today = roles.local_today()
d = lambda n: (today + timedelta(days=n)).isoformat()  # noqa: E731


def H(u):
    r = c.post("/api/auth/login", json={"username": u, "password": "x"})
    return {"Authorization": "Bearer " + r.json()["access_token"]}


HT, HT2, HE = H("ust"), H("ust2"), H("ex")


def tasks(uid, word):
    db.expire_all()
    return [x.title for x in db.query(models.Task)
            .filter(models.Task.assignee_id == uid).all() if word in x.title]


def order(day):
    r = c.post("/api/me/exam-orders", headers=HT,
               json={"group_id": GID, "date": d(day), "kind": "unit",
                     "unit_no": 2})
    assert r.status_code == 200, r.text
    return r.json()["id"]


URL = "/api/me/exam-orders/{}/change-time"

print("=== 1. YANGI BUYURTMA ===")
o1 = order(5)
r = c.post(URL.format(o1), headers=HT,
           json={"date": d(7), "time": "16:30", "note": "Bayram"})
ck("o'zgardi", r.status_code, 200)
ck("yangi kun/vaqt", (r.json()["date"], r.json()["time"]), (d(7), "16:30"))
ck("holat o'zgarmadi", r.json()["status"], "new")
ck("ikkala examinerga xabar",
   (len(tasks(EX, "vaqti o'zgardi")), len(tasks(EX2, "vaqti o'zgardi"))),
   (1, 1))

print("\n=== 2. QABUL QILINGAN ===")
r = c.post(f"/api/exam-orders/{o1}/accept", headers=HE, json={})
ck("examiner qabul qildi", r.status_code, 200)
db.expire_all()
eo = db.query(models.ExamOrder).get(o1)
r = c.post(URL.format(o1), headers=HT, json={"date": d(9), "time": "10:00"})
ck("qabul qilinganda ham o'zgaradi", r.status_code, 200)
ck("examiner joyida, holat accepted",
   (r.json()["status"], r.json()["accepted_by"]), ("accepted", "EX"))
db.expire_all()
eo = db.query(models.ExamOrder).get(o1)
if eo.exam_id:
    ck("Exam sanasi ham ko'chdi",
       db.query(models.Exam).get(eo.exam_id).date.isoformat(), d(9))
ck("faqat qabul qilgan examinerga",
   (len(tasks(EX, "Ustoz imtihon vaqtini")),
    len(tasks(EX2, "Ustoz imtihon vaqtini"))), (1, 0))

print("\n=== 3. QOIDALAR ===")
for name, body in [
    ("bugun — 400", {"date": d(0)}),
    ("o'tgan kun — 400", {"date": d(-2)}),
    ("61 kun — 400", {"date": d(61)}),
    ("o'zgarishsiz — 400", {"date": d(9), "time": "10:00"}),
]:
    ck(name, c.post(URL.format(o1), headers=HT, json=body).status_code, 400)
o2 = order(20)
ck("shu kunga boshqa buyurtma — 400",
   c.post(URL.format(o2), headers=HT, json={"date": d(9)}).status_code, 400)

print("\n=== 4. TAKLIF KUTILAYOTGANDA / YOPILGAN ===")
r = c.post(f"/api/exam-orders/{o2}/reschedule", headers=HE,
           json={"date": d(22), "reason":
                 roles.EXAM_ORDER_RESCHEDULE_REASONS[0][0]})
ck("examiner taklif qildi", r.status_code, 200)
ck("taklif kutilayotganda — 400",
   c.post(URL.format(o2), headers=HT, json={"date": d(25)}).status_code, 400)
c.post(f"/api/me/exam-orders/{o2}/cancel", headers=HT, json={})
ck("bekor qilingan — 400",
   c.post(URL.format(o2), headers=HT, json={"date": d(25)}).status_code, 400)

print("\n=== 5. RUXSAT VA AUDIT ===")
ck("boshqa ustoz — 403",
   c.post(URL.format(o1), headers=HT2, json={"date": d(11)}).status_code, 403)
n = (db.query(models.AuditLog)
     .filter(models.AuditLog.action == "time_change",
             models.AuditLog.entity_id == o1).count())
ck("audit: 2 ta o'zgarish", n, 2)

print()
if fails:
    print(f"XATO: {len(fails)} ta tekshiruv o'tmadi")
    for f in fails:
        print("   - " + f)
    sys.exit(1)
print("HAMMASI O'TDI")
sys.exit(0)
