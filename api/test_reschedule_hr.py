"""DARS KO'CHIRISH SO'ROVI HAR BIR TASDIQLOVCHIGA BORADIMI (2026-08-24).

Jahongir: "HR uchun dars tasdiqlash chiqmay qolibdi dars
kochirishlarniki".

Sabab: so'rov FAQAT bitta odamga (amalda asoschiga) vazifa bo'lib
tushardi. Tekshiriladi: endi HR ham, o'quv bo'limi rahbari ham
ko'radi; boshqa filial rahbari ko'rmaydi; bittasi tasdiqlagach
hammasining vazifasi yopiladi.
"""
import os, sys
from datetime import date, timedelta

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_rhr/db.sqlite"
os.makedirs("/tmp/verify_rhr", exist_ok=True)
if os.path.exists("/tmp/verify_rhr/db.sqlite"):
    os.remove("/tmp/verify_rhr/db.sqlite")
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


b1 = models.Branch(name="Zafar")
b2 = models.Branch(name="Chilonzor")
db.add_all([b1, b2]); db.commit()

people = [
    ("asoschi", roles.FOUNDER, None),
    ("hr", roles.HR_MANAGER, None),
    ("oquv", roles.ACADEMIC_HEAD, None),
    ("rahbar1", roles.BRANCH_MANAGER, b1.id),
    ("rahbar2", roles.BRANCH_MANAGER, b2.id),
    ("admin", roles.ADMINISTRATOR, b1.id),
    ("ustoz", roles.TEACHER, b1.id),
]
for uname, role, bid in people:
    db.add(models.User(username=uname, full_name=uname.upper(),
                       password_hash=hash_password("Parol123!"),
                       role=role, branch_id=bid, is_active=1))
db.commit()

tu = db.query(models.User).filter(
    models.User.username == "ustoz").first()
t = models.Teacher(full_name="Ustoz Aziz", branch_id=b1.id, user_id=tu.id)
db.add(t); db.commit()
g = models.Group(name="B1-01", branch_id=b1.id, teacher_id=t.id,
                 lesson_time="10:00", monthly_fee=500000)
db.add(g); db.commit()

from common import _reschedule_usage


def _quota_ok():
    return _reschedule_usage(db, t.id, FROM)["auto_ok"]


FROM = date.today() + timedelta(days=10)
TO = FROM + timedelta(days=2)
db.add(models.Lesson(group_id=g.id, date=FROM, held=0))
db.commit()

# Kvotani tugatamiz — shundagina tasdiq talab qilinadi.
# Hisob KO'CHIRILAYOTGAN DARS oyi bo'yicha yuritiladi, shuning uchun
# soxta yozuvlar ham SHU oyning ichida bo'lishi kerak.
for i in range(roles.RESCHEDULE_PER_MONTH):
    db.add(models.LessonReschedule(
        group_id=g.id, teacher_id=t.id, requested_by=tu.id,
        from_date=FROM + timedelta(days=i + 1),
        to_date=FROM + timedelta(days=i + 2),
        from_time="10:00", to_time="10:00",
        reason="other", status="auto", auto_approved=1))
db.commit()
assert not _quota_ok(), "kvota hali tugamadi — test noto'g'ri"


def H(u):
    tok = c.post("/api/auth/login",
                 json={"username": u, "password": "Parol123!"}
                 ).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


print("=== 1. USTOZ SO'ROV YUBORDI (kvota tugagan) ===")
r = c.post("/api/me/reschedules", headers=H("ustoz"),
           json={"group_id": g.id, "from_date": FROM.isoformat(),
                 "to_date": TO.isoformat(), "reason": "other",
                 "note": "ustoz kasal"})
ck("status 200", r.status_code, 200)
j = r.json()
ck("tasdiq kutmoqda", j.get("status"), "pending")
rid = j["id"]

print("\n=== 2. KIMGA VAZIFA TUSHDI ===")
title = f"Dars ko'chirish so'rovi #{rid}"
rows = db.query(models.Task).filter(models.Task.title == title).all()
who = sorted(db.query(models.User).get(x.assignee_id).username
             for x in rows if x.assignee_id)
ck("HR ko'radi", "hr" in who, True)
ck("o'quv bo'limi rahbari ko'radi", "oquv" in who, True)
ck("asoschi ko'radi", "asoschi" in who, True)
ck("guruh filiali rahbari ko'radi", "rahbar1" in who, True)
ck("BOSHQA filial rahbari ko'rmaydi", "rahbar2" in who, False)
ck("administratorga tushmaydi", "admin" in who, False)

print("\n=== 3. HR RO'YXATNI OCHA OLADI ===")
r = c.get("/api/reschedules?status=pending", headers=H("hr"))
ck("status 200", r.status_code, 200)
ck("so'rov ko'rinadi", any(x["id"] == rid for x in r.json()["rows"]), True)
ck("pending soni", r.json()["pending"], 1)

print("\n=== 4. HR TASDIQLAYDI ===")
r = c.post(f"/api/reschedules/{rid}/decide", headers=H("hr"),
           json={"decision": "approved"})
ck("status 200", r.status_code, 200)
ck("tasdiqlandi", r.json()["status"], "approved")

print("\n=== 5. HAMMANING VAZIFASI YOPILDI ===")
db.expire_all()
rows = db.query(models.Task).filter(models.Task.title == title).all()
ck("ochiq vazifa qolmadi",
   [x.username for x in
    [db.query(models.User).get(y.assignee_id) for y in rows
     if y.status != "done"] if x], [])
ck("natija yozildi", all("Tasdiqlandi" in (x.result or "") for x in rows),
   True)

print("\n=== 6. DARS HAQIQATAN KO'CHDI ===")
db.expire_all()
ls = db.query(models.Lesson).filter(models.Lesson.group_id == g.id,
                                    models.Lesson.date == TO).first()
ck("yangi sanada dars bor", ls is not None, True)

print("\n" + ("HAMMASI O'TDI" if not fails else f"XATOLAR: {fails}"))
sys.exit(1 if fails else 0)
