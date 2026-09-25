"""O'TISH VA YAKUNIY TEST — 100 BALLIK (2026-09-25).

Jahongir: "o'tish testi midterm end of course maks ball 100 bo'ladi".

Ilgari maksimal ball test bazasidagi SAVOLLAR SONIGA tenglanardi
(45), shuning uchun mid/end testda 46-100 ball kiritib bo'lmasdi.

Tekshiriladi:
  A. Yangi mid/end imtihon biriktirilganda maksimal ball 100;
  B. Unit testda eskicha — savollar soni;
  C. Online havola ochilganda taqsimot: online = savollar soni,
     qog'oz (Writing/Speaking) = qolgani, jami 100;
  D. Bir martalik yangilash eski mid/end testlarni 100 ga o'tkazadi,
     lekin NATIJASI BOR testga tegmaydi.
"""
import os
import sys
import tempfile
import json

_DB = os.path.join(tempfile.gettempdir(), "mid_end_100_test.db")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace("\\", "/")
if os.path.exists(_DB):
    os.remove(_DB)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                         # noqa: E402
import entry  # noqa: F401,E402
import exam_online                                 # noqa: E402
from database import SessionLocal                  # noqa: E402
from auth import hash_password                     # noqa: E402

client = TestClient(main.app)
fails = []


def ck(name, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + f"{name}: {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


TODAY = roles.local_today()

db = SessionLocal()
b = models.Branch(name="Zafar")
db.add(b)
db.commit()
BID = b.id
db.add(models.User(username="asos", full_name="Asoschi",
                   password_hash=hash_password("Parol123!"),
                   role=roles.FOUNDER, branch_id=BID, is_active=1))
db.commit()
t = models.Teacher(full_name="Ustoz", branch_id=BID, is_active=1)
db.add(t)
db.commit()
g = models.Group(name="Apex", subject="english", level="step1",
                 branch_id=BID, teacher_id=t.id, lesson_time="18:00",
                 monthly_fee=1, lesson_days="135", capacity=15)
db.add(g)
db.commit()
GID = g.id
s1 = models.Student(full_name="Aliyev Ali", branch_id=BID, group_id=GID,
                    status="active", enrolled_date=TODAY)
db.add(s1)
db.commit()
SID = s1.id
db.close()

H = {"Authorization": "Bearer " + client.post(
    "/api/auth/login", json={"username": "asos", "password": "Parol123!"}
).json()["access_token"]}

print("\n=== A. MID/END = 100 BALL ===")
d = client.get(f"/api/groups/{GID}/exam-bank-max?kind=mid", headers=H).json()
ck("o'tish testi bazadan 100", d["max_score"], 100.0)
d = client.get(f"/api/groups/{GID}/exam-bank-max?kind=end", headers=H).json()
ck("yakuniy test ham 100", d["max_score"], 100.0)

print("\n=== B. UNIT ESKICHA ===")
d = client.get(f"/api/groups/{GID}/exam-bank-max?kind=unit&unit_no=1",
               headers=H).json()
ck("unit testda savollar soni", d["max_score"] not in (None, 100.0), True)
print(f"     (unit 1 = {d['max_score']} savol)")

print("\n=== C. ONLINE HAVOLA: TAQSIMOT ===")
EID = client.post(f"/api/groups/{GID}/exams", headers=H, json={
    "kind": "mid", "date": TODAY.isoformat(), "max_score": 100}).json()["id"]
dd = SessionLocal()
tpl = (dd.query(models.ExamTemplate)
       .filter(models.ExamTemplate.level == "step1",
               models.ExamTemplate.kind == "mid").first())
TID = tpl.id
NQ = sum(1 for _ in exam_online._questions(json.loads(tpl.parts)))
dd.close()
r = client.post(f"/api/exams/{EID}/online", headers=H,
                json={"template_id": TID})
ck("havola ochildi", r.status_code, 200)
on = r.json()["online"]
ck("online qismi savollar soniga teng", on["online_max"], float(NQ))
ck("qog'oz qismi qolgani", on["paper_max"], 100.0 - NQ)
ck("jami 100", on["online_max"] + on["paper_max"], 100.0)
ex = client.get(f"/api/exams/{EID}", headers=H).json()
ck("imtihon maksimali 100", ex["max_score"], 100.0)

print("\n=== D. ESKI TESTLAR: NATIJASI BORIGA TEGILMAYDI ===")
dd = SessionLocal()
old_clean = models.Exam(group_id=GID, kind="end", date=TODAY,
                        max_score=45, status="done")
old_scored = models.Exam(group_id=GID, kind="mid", date=TODAY,
                         max_score=45, status="done")
dd.add_all([old_clean, old_scored])
dd.commit()
dd.add(models.ExamResult(exam_id=old_scored.id, student_id=SID,
                         score=40, percent=88.9))
dd.commit()
ids = (old_clean.id, old_scored.id)
dd.close()
dd = SessionLocal()
exam_online.fill_mid_end_100(dd, key="exam_mid_end_100_test")
dd.close()
dd = SessionLocal()
a = dd.query(models.Exam).get(ids[0])
b2 = dd.query(models.Exam).get(ids[1])
ck("natijasiz test 100 ga o'tdi", a.max_score, 100.0)
ck("natijali test tegilmadi", b2.max_score, 45.0)
dd.close()

print()
if fails:
    print("XATOLAR:", ", ".join(fails))
    sys.exit(1)
print("HAMMASI O'TDI")
