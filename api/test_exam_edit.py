"""TESTNI TAHRIRLASH VA O'CHIRISH — EXAMINERLAR BOSHLIG'I (2026-09-17).

Jahongir: "examiner testlarni edit qilish va o'chirishni examinerlar
boshlig'iga qo'shib ber".

Tekshiriladi:
  A. Examinerlar boshlig'i testni tahrirlay oladi (sana, nom, unit);
  B. Maksimal ball o'zgarsa foiz va coin qayta hisoblanadi;
  C. Mavjud balldan past maksimal ball, noto'g'ri unit rad etiladi;
  D. Natijali testni Mock'ga o'tkazib bo'lmaydi;
  E. Oddiy examiner va ustoz tahrirlay/o'chira olmaydi;
  F. Boshliq o'chiradi — coinlar qaytadi, auditga yoziladi;
  G. Frontend shu huquqni ishlatyapti.
"""
import os
import sys
import tempfile
from datetime import timedelta

_DB = os.path.join(tempfile.gettempdir(), "exam_edit_test.db")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace("\\", "/")
if os.path.exists(_DB):
    os.remove(_DB)
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                          # noqa: E402
import entry  # noqa: F401,E402
from database import SessionLocal                   # noqa: E402
from auth import hash_password                      # noqa: E402

client = TestClient(main.app)
fails = []


def ck(name, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + name + f": {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


def tok(u, p="x"):
    return {"Authorization": "Bearer " + client.post(
        "/api/auth/login", json={"username": u, "password": p}
    ).json()["access_token"]}


TODAY = roles.local_today()

db = SessionLocal()
b = models.Branch(name="Zafar")
db.add(b)
db.commit()
BID = b.id
for un, role in [("asos", "founder"), ("bosh", "head_examiner"),
                 ("exam", "examiner"), ("ustoz", "teacher")]:
    db.add(models.User(username=un, password_hash=hash_password("x"),
                       full_name=un.title(), role=role, branch_id=BID))
db.commit()
t = models.Teacher(full_name="Ustoz", branch_id=BID)
db.add(t)
db.commit()
g = models.Group(name="Apex", branch_id=BID, teacher_id=t.id, level="B1")
db.add(g)
db.commit()
GID = g.id
S = {}
for nm in ["Aliyev", "Boboyev"]:
    s = models.Student(full_name=nm, branch_id=BID, group_id=GID,
                       status="active",
                       enrolled_date=TODAY - timedelta(days=60))
    db.add(s)
    db.commit()
    S[nm] = s.id
# Imtihondan oldin yo'qlama bor — natija hisobga va coinga kiradi
les = models.Lesson(group_id=GID, date=TODAY - timedelta(days=10))
db.add(les)
db.commit()
for sid in S.values():
    db.add(models.Attendance(lesson_id=les.id, student_id=sid, present=1))
db.commit()
# Aniq coin qoidasi: 90%+ -> 10, 50%+ -> 5
db.query(models.ExamCoinRule).delete()
db.add(models.ExamCoinRule(min_percent=90, coins=10))
db.add(models.ExamCoinRule(min_percent=50, coins=5))
db.commit()
db.close()

H = tok("asos")
HB = tok("bosh")
HE = tok("exam")
HT = tok("ustoz")


def coins(sid):
    d = SessionLocal()
    v = sum(c.amount for c in d.query(models.CoinEntry)
            .filter(models.CoinEntry.student_id == sid,
                    models.CoinEntry.source == "exam").all())
    d.close()
    return v


r = client.post(f"/api/groups/{GID}/exams", headers=H, json={
    "kind": "unit", "unit_no": 1, "date": TODAY.isoformat(),
    "max_score": 50})
assert r.status_code == 200, r.text
EID = r.json()["id"]
r = client.put(f"/api/exams/{EID}/results", headers=H, json={
    "marks": [{"student_id": S["Aliyev"], "score": 45},
              {"student_id": S["Boboyev"], "score": 30}]})
ck("natijalar saqlandi", r.status_code, 200)
ck("Aliyev 90% -> 10 coin", coins(S["Aliyev"]), 10)
ck("Boboyev 60% -> 5 coin", coins(S["Boboyev"]), 5)

print("\n=== A. BOSHLIQ TAHRIRLAYDI ===")
new_day = (TODAY - timedelta(days=2)).isoformat()
r = client.put(f"/api/exams/{EID}", headers=HB, json={
    "date": new_day, "unit_no": 3, "title": "Unit 3 qayta"})
ck("javob 200", r.status_code, 200)
ck("sana o'zgardi", r.json().get("date"), new_day)
ck("unit o'zgardi", r.json().get("unit_no"), 3)
ck("nom o'zgardi", r.json().get("title"), "Unit 3 qayta")
ck("coin o'zgarmadi", coins(S["Aliyev"]), 10)

print("\n=== B. MAKSIMAL BALL -> QAYTA HISOB ===")
r = client.put(f"/api/exams/{EID}", headers=HB, json={"max_score": 100})
ck("javob 200", r.status_code, 200)
d = client.get(f"/api/exams/{EID}", headers=H).json()
pc = {x["student_id"]: x["percent"] for x in d["results"]}
ck("Aliyev foizi 45%", pc.get(S["Aliyev"]), 45.0)
ck("Boboyev foizi 30%", pc.get(S["Boboyev"]), 30.0)
ck("Aliyev coini 0 (45% < 50%)", coins(S["Aliyev"]), 0)
ck("Boboyev coini 0", coins(S["Boboyev"]), 0)
r = client.put(f"/api/exams/{EID}", headers=HB, json={"max_score": 60})
ck("Aliyev 75% -> 5 coin", coins(S["Aliyev"]), 5)
ck("Boboyev 50% -> 5 coin", coins(S["Boboyev"]), 5)

early = (TODAY - timedelta(days=20)).isoformat()
client.put(f"/api/exams/{EID}", headers=HB, json={"date": early})
ck("yo'qlamadan oldingi sana -> coin yo'q", coins(S["Aliyev"]), 0)
client.put(f"/api/exams/{EID}", headers=HB, json={"date": new_day})
ck("sana qaytdi -> coin qaytdi", coins(S["Aliyev"]), 5)

print("\n=== C. NOTO'G'RI QIYMATLAR ===")
r = client.put(f"/api/exams/{EID}", headers=HB, json={"max_score": 40})
ck("balldan past maksimal rad", r.status_code, 400)
r = client.put(f"/api/exams/{EID}", headers=HB, json={"unit_no": 999})
ck("noto'g'ri unit rad", r.status_code, 400)
r = client.put(f"/api/exams/{EID}", headers=HB, json={"max_score": 0})
ck("0 maksimal rad", r.status_code, 400)

print("\n=== D. NATIJALI TESTNI MOCK'GA O'TKAZIB BO'LMAYDI ===")
r = client.put(f"/api/exams/{EID}", headers=HB, json={"kind": "mock"})
ck("mock rad", r.status_code, 400)
r = client.put(f"/api/exams/{EID}", headers=HB, json={"kind": "mid"})
ck("mid ga o'tdi", r.status_code, 200)
ck("unit_no tozalandi", r.json().get("unit_no"), None)

print("\n=== E. BOSHQALARGA RUXSAT YO'Q ===")
for nm, hh in [("examiner", HE), ("ustoz", HT)]:
    r = client.put(f"/api/exams/{EID}", headers=hh, json={"title": "x"})
    ck(f"{nm} tahrirlay olmaydi", r.status_code, 403)
    r = client.delete(f"/api/exams/{EID}", headers=hh)
    ck(f"{nm} o'chira olmaydi", r.status_code, 403)

print("\n=== F. BOSHLIQ O'CHIRADI ===")
r = client.delete(f"/api/exams/{EID}", headers=HB)
ck("javob 200", r.status_code, 200)
d = SessionLocal()
ck("test yo'q", d.query(models.Exam).get(EID), None)
ck("natijalar yo'q",
   d.query(models.ExamResult).filter(
       models.ExamResult.exam_id == EID).count(), 0)
logs = d.query(models.AuditLog).filter(
    models.AuditLog.entity == "exam").all()
ck("o'chirish auditda", any(x.action == "delete" for x in logs), True)
ck("tahrir auditda",
   any(x.action == "update" and x.field == "max_score" for x in logs), True)
d.close()
ck("Aliyev coini qaytdi", coins(S["Aliyev"]), 0)
ck("Boboyev coini qaytdi", coins(S["Boboyev"]), 0)

print("\n=== G. FRONTEND ===")
with open(os.path.join(ROOT, "src", "lib", "roles.ts"), encoding="utf-8") as f:
    ck("roles.ts EXAM_EDIT", "EXAM_EDIT = [FOUNDER, BRANCH_MANAGER, HEAD_EXAMINER]"
       in f.read(), True)
with open(os.path.join(ROOT, "src", "pages", "GroupDetail.tsx"), encoding="utf-8") as f:
    ck("GroupDetail EXAM_EDIT", "can(user?.role, EXAM_EDIT)" in f.read(), True)
with open(os.path.join(ROOT, "src", "components", "GroupGrids.tsx"), encoding="utf-8") as f:
    ck("GroupGrids PUT /exams", "api.put(`/exams/${exam.id}`" in f.read(), True)

print()
print("HAMMASI O'TDI" if not fails else f"XATOLAR: {fails}")
sys.exit(1 if fails else 0)
