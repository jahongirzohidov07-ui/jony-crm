"""HR O'QUVCHI KARTASIDAN IMTIHON NATIJASINI TUZATADI (2026-09-24).

Jahongir: "imtixon tarixini o'zgartirish qo'shish tahrirlashni ham
qo'sh hrga".

Tekshiriladi:
  A. HR imtihon tarixini ko'radi (ilgari ruxsat xatosi edi);
  B. Natijasi yozilmagan testlar alohida ro'yxatda ("missing") —
     kartadan turib qo'shish uchun;
  C. HR natija qo'sha oladi: foiz va coin avtomat hisoblanadi;
  D. HR mavjud natijani tuzatsa — foiz va coin QAYTA hisoblanadi,
     eski coin qoldiqda qolib ketmaydi;
  E. "Kelmadi" belgilansa natija va coin olib tashlanadi;
  F. Ustoz tuzata olmaydi (baholash uniki emas), begona guruhdagi
     testga va boshqa filial o'quvchisiga tegib bo'lmaydi.
"""
import os
import sys
import tempfile
from datetime import timedelta

_DB = os.path.join(tempfile.gettempdir(), "hr_exams_test.db")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace("\\", "/")
if os.path.exists(_DB):
    os.remove(_DB)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                         # noqa: E402
import entry  # noqa: F401,E402
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


def tok(u):
    return {"Authorization": "Bearer " + client.post(
        "/api/auth/login",
        json={"username": u, "password": "Parol123!"}
    ).json()["access_token"]}


TODAY = roles.local_today()

db = SessionLocal()
b1 = models.Branch(name="Zafar")
b2 = models.Branch(name="Chilonzor")
db.add_all([b1, b2])
db.commit()
BID, BID2 = b1.id, b2.id
for un, nm, role, bid in [("asos", "Asoschi", roles.FOUNDER, BID),
                          ("hr", "HR Nodira", roles.HR_MANAGER, BID),
                          ("ust", "Ustoz Anvar", roles.TEACHER, BID)]:
    db.add(models.User(username=un, full_name=nm,
                       password_hash=hash_password("Parol123!"),
                       role=role, branch_id=bid, is_active=1))
db.commit()
t = models.Teacher(full_name="Ustoz Anvar", branch_id=BID, is_active=1)
db.add(t)
db.commit()
g = models.Group(name="Apex", subject="english", level="B1", branch_id=BID,
                 teacher_id=t.id, lesson_time="18:00", monthly_fee=500000,
                 lesson_days="135", capacity=15)
g2 = models.Group(name="Begona", subject="english", level="B1",
                  branch_id=BID2, lesson_time="10:00", monthly_fee=1,
                  lesson_days="24", capacity=15)
db.add_all([g, g2])
db.commit()
GID, GID2 = g.id, g2.id
s1 = models.Student(full_name="Aliyev Ali", branch_id=BID, group_id=GID,
                    status="active", enrolled_date=TODAY - timedelta(days=90))
s2 = models.Student(full_name="Boboyev Bobur", branch_id=BID, group_id=GID,
                    status="active", enrolled_date=TODAY - timedelta(days=90))
db.add_all([s1, s2])
db.commit()
SID, SID2 = s1.id, s2.id
# Imtihondan oldin dars bo'lgan — natija coinga kiradi
les = models.Lesson(group_id=GID, date=TODAY - timedelta(days=5))
db.add(les)
db.commit()
for sid in (SID, SID2):
    db.add(models.Attendance(lesson_id=les.id, student_id=sid, present=1))
db.query(models.ExamCoinRule).delete()
db.add(models.ExamCoinRule(min_percent=90, coins=10))
db.add(models.ExamCoinRule(min_percent=50, coins=5))
db.commit()
db.close()

H = tok("asos")
HH = tok("hr")
HT = tok("ust")


def coins(sid):
    d = SessionLocal()
    v = sum(c.amount for c in d.query(models.CoinEntry)
            .filter(models.CoinEntry.student_id == sid,
                    models.CoinEntry.source == "exam").all())
    d.close()
    return v


# Test tuziladi va faqat Boburning natijasi kiritiladi
EID = client.post(f"/api/groups/{GID}/exams", headers=H, json={
    "kind": "unit", "unit_no": 1, "date": TODAY.isoformat(),
    "max_score": 50}).json()["id"]
client.put(f"/api/exams/{EID}/results", headers=H, json={
    "marks": [{"student_id": SID2, "score": 25}]})

print("\n=== A. HR TARIXNI KO'RADI ===")
r = client.get(f"/api/students/{SID}/exams", headers=HH)
ck("HR ocha oladi", r.status_code, 200)
d = r.json()
ck("tuzatish huquqi bor", d["can_edit"], True)

print("\n=== B. NATIJASI YO'Q TEST KO'RINADI ===")
ck("natijasi yo'q", d["results"], [])
ck("qo'shish uchun ro'yxatda turibdi",
   [x["exam_id"] for x in d["missing"]], [EID])

print("\n=== C. HR NATIJA QO'SHADI ===")
r = client.put(f"/api/students/{SID}/exams/{EID}", headers=HH,
               json={"score": 46})
ck("qo'shildi", r.status_code, 200)
ck("foiz hisoblandi", r.json()["percent"], 92.0)
ck("coin berildi", coins(SID), 10)
d = client.get(f"/api/students/{SID}/exams", headers=HH).json()
ck("endi tarixda turibdi", len(d["results"]), 1)
ck("qo'shish ro'yxatidan chiqdi", d["missing"], [])

print("\n=== D. TUZATISH: COIN QAYTA HISOBLANADI ===")
r = client.put(f"/api/students/{SID}/exams/{EID}", headers=HH,
               json={"score": 30, "note": "Varaq qayta tekshirildi"})
ck("tuzatildi", r.json()["percent"], 60.0)
ck("coin 10 dan 5 ga tushdi", coins(SID), 5)

print("\n=== E. KELMADI ===")
r = client.put(f"/api/students/{SID}/exams/{EID}", headers=HH,
               json={"absent": True})
ck("kelmagan deb belgilandi", r.json()["absent"], True)
ck("bali olib tashlandi", r.json()["percent"], None)
ck("coin qaytarib olindi", coins(SID), 0)

print("\n=== F. CHEGARALAR ===")
ck("ustoz tuzata olmaydi",
   client.put(f"/api/students/{SID}/exams/{EID}", headers=HT,
              json={"score": 50}).status_code, 403)
ck("ustoz ko'ra oladi",
   client.get(f"/api/students/{SID}/exams", headers=HT).status_code, 200)
db = SessionLocal()
eid2 = models.Exam(group_id=GID2, kind="unit", unit_no=1, date=TODAY,
                   max_score=50, status="done")
db.add(eid2)
db.commit()
EID2 = eid2.id
db.close()
ck("begona guruh testiga tegib bo'lmaydi",
   client.put(f"/api/students/{SID}/exams/{EID2}", headers=HH,
              json={"score": 50}).status_code, 400)
ck("yo'q o'quvchi", client.put(f"/api/students/99999/exams/{EID}",
                               headers=HH, json={"score": 1}).status_code,
   404)

print()
if fails:
    print("XATOLAR:", ", ".join(fails))
    sys.exit(1)
print("HAMMASI O'TDI")
