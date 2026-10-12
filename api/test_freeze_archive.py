"""Avtomuzlatish: yo'qlama arxivga, yo'qolganlar ro'yxati (2026-10-08)."""
import os, sys
from datetime import date, timedelta

os.environ["DATABASE_URL"] = "sqlite:////tmp/freeze_archive_test.db"
if os.path.exists("/tmp/freeze_archive_test.db"):
    os.remove("/tmp/freeze_archive_test.db")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
import main, models, roles
import entry  # noqa: F401 — production yo'li
from database import SessionLocal
from auth import hash_password

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


TODAY = date.today()
db = SessionLocal()
b = models.Branch(name="Zafar")
db.add(b)
db.commit()
BID = b.id

db.add(models.User(username="asos", password_hash=hash_password("x"),
                   full_name="Asoschi", role="founder"))
uadm = models.User(username="admin1", password_hash=hash_password("x"),
                   full_name="Administrator Aziz", role="sales_manager",
                   branch_id=BID)
ut = models.User(username="ustoz1", password_hash=hash_password("x"),
                 full_name="Ustoz Sardor", role="teacher", branch_id=BID)
usup = models.User(username="support1", password_hash=hash_password("x"),
                   full_name="Support Nodira", role="support_teacher",
                   branch_id=BID)
db.add_all([uadm, ut, usup])
db.commit()
UADM, UT, USUP = uadm.id, ut.id, usup.id

t = models.Teacher(full_name="Ustoz Sardor", branch_id=BID, is_active=1,
                   grade="senior", user_id=UT,
                   hired_date=TODAY - timedelta(days=500))
db.add(t)
db.commit()
TID = t.id

g = models.Group(name="Best Kids", teacher_id=TID, branch_id=BID,
                 subject="english", lesson_days="mon,tue,wed,thu,fri,sat",
                 lesson_time="09:00",
                 start_date=TODAY - timedelta(days=60),
                 lesson_price=40000, monthly_fee=480000,
                 standard_lessons_per_month=12)
db.add(g)
db.commit()
GID = g.id
db.add(models.SupportAssignment(user_id=USUP, group_id=GID,
                                created_by="Test"))

st = models.Student(full_name="Kelmayotgan Bola", branch_id=BID,
                    group_id=GID, status="active",
                    enrolled_date=TODAY - timedelta(days=60))
boshqa = models.Student(full_name="Kelayotgan Bola", branch_id=BID,
                        group_id=GID, status="active",
                        enrolled_date=TODAY - timedelta(days=60))
db.add_all([st, boshqa])
db.commit()
SID, OID = st.id, boshqa.id

LIDS = []
for i in (3, 2, 1):
    ls = models.Lesson(group_id=GID, teacher_id=TID,
                       date=TODAY - timedelta(days=i), held=0)
    db.add(ls)
    db.commit()
    LIDS.append(ls.id)
db.close()

H = tok("asos")

print("=== 1. 3 darsga kelmadi -> muzlatildi, yo'qlama ARXIVGA ===")
for lid in LIDS:
    r = client.put(f"/api/lessons/{lid}/attendance", headers=H, json={
        "marks": [{"student_id": SID, "present": False},
                  {"student_id": OID, "present": True}]})
    ck("saqlandi", r.status_code, 200)
_d0 = SessionLocal()
ck("saqlashda darhol muzlamaydi", _d0.query(models.Student).get(SID).status, "active")
_d0.close()
# 2026-10-12: muzlatish saqlashda emas — ertalabki kunlik tekshiruvda
import groups_lessons as _GL  # noqa: E402
_dbf = SessionLocal(); _GL.run_auto_freeze(_dbf); _dbf.close()
db = SessionLocal()
ck("muzlatildi", db.query(models.Student).get(SID).status, "frozen")
ck("jadvalda yo'qlamasi yo'q (oylikka kirmaydi)",
   db.query(models.Attendance).filter(
       models.Attendance.student_id == SID).count(), 0)
arc = db.query(models.AttendanceArchive).filter(
    models.AttendanceArchive.student_id == SID).all()
ck("arxivda 3 ta", len(arc), 3)
ck("sabab", {a.reason for a in arc}, {"auto_freeze"})
ck("arxivda kelmadi", {a.present for a in arc}, {0})
ev = db.query(models.AuditLog).filter(
    models.AuditLog.action == "auto_freeze").first()
ck("auditda sanalar", all(
    (TODAY - timedelta(days=i)).isoformat() in (ev.note or "")
    for i in (1, 2, 3)), True)
ck("boshqa bola joyida", db.query(models.Attendance).filter(
    models.Attendance.student_id == OID).count(), 3)
# Muzlatilgandan keyin o'tilgan dars (belgisiz)
ls = models.Lesson(group_id=GID, teacher_id=TID, date=TODAY, held=1)
db.add(ls); db.commit()
db.close()

print("\n=== 2. Yo'qolganlar ro'yxati (faqat o'qish) ===")
r = client.get("/api/attendance/freeze-losses", headers=H)
ck("ochildi", r.status_code, 200)
d = r.json()
row = next((x for x in d["rows"] if x["student_id"] == SID), None)
ck("o'quvchi ro'yxatda", row is not None, True)
ck("3 ta yo'qolgan kelmadi",
   [x["value"] for x in row["lost"]] if row else None, ["kelmadi"] * 3)
ck("kim belgilagani", {x["by"] for x in row["lost"]} if row else None,
   {"Asoschi"})
ck("muzlatilgandan keyin belgisiz dars", row["blank"] if row else None,
   [TODAY.isoformat()])
ck("kelayotgan bola ro'yxatda yo'q",
   any(x["student_id"] == OID for x in d["rows"]), False)
ck("ustozga ruxsat yo'q", client.get(
    "/api/attendance/freeze-losses", headers=tok("ustoz1")).status_code, 403)

print()
if fails:
    print(f"{len(fails)} ta XATO: {fails}"); sys.exit(1)
print("HAMMASI OK")
