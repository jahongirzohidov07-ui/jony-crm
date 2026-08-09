"""Rahbariyat/HR menejer darsni BUGUNGA ham ko'chira olishi (2026-08).

Kontekst: avval group_reschedule() HAMMA uchun (rahbariyatni ham
qo'shib) `to_date <= today` bo'lsa 400 qaytarardi — "Yangi sana
kelajakda bo'lishi kerak". Jahongirning aytishicha, oy oxiridagi
darslarni TEZLASHTIRIB, guruhni muddatidan oldin tugatish uchun,
ba'zan darsni AYNAN BUGUNGA ko'chirish kerak bo'ladi. Bu esa faqat
rahbariyat/HR menejer huquqi (roles.RESCHEDULE_APPROVE) — oddiy ustoz
o'z darsini hali ham kamida ertaga ko'chirishi kerak (o'zgarmadi).

MUHIM: `import entry` qilinadi — /api/groups/{gid}/reschedule ni
entry.py'dagi group_reschedule_v2 ochadi (garchi bu safar u to'g'ri
DELEGATSIYA qiladi, o'zining mustaqil nusxasini yozmaydi — lekin
buni FARQINI his qilmasdan, har doim haqiqiy ishlaydigan yo'l orqali
tekshirish kerak)."""
import os, sys
from datetime import date, timedelta

os.environ["DATABASE_URL"] = "sqlite:////tmp/resched_today_test.db"
if os.path.exists("/tmp/resched_today_test.db"):
    os.remove("/tmp/resched_today_test.db")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
import main, models, roles
import entry  # noqa: F401
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


db = SessionLocal()
b = models.Branch(name="Zafar")
db.add(b)
db.commit()
BID = b.id

t = models.Teacher(full_name="Ustoz A", branch_id=BID, is_active=1)
db.add(t)
db.commit()
db.add(models.User(username="ust2", full_name="Ustoz A", role="teacher",
                   branch_id=BID, password_hash=hash_password("x"),
                   is_active=1))
db.add(models.User(username="hrm2", full_name="HR Menejer",
                   role="hr_manager", branch_id=BID,
                   password_hash=hash_password("x"), is_active=1))
db.commit()
t.user_id = db.query(models.User).filter(
    models.User.username == "ust2").first().id
db.commit()

g = models.Group(name="G-Sep", branch_id=BID, teacher_id=t.id,
                 lesson_time="10:00-11:00")
db.add(g)
db.commit()
GID = g.id

TODAY = date.today()
HR = tok("hrm2")
TEA = tok("ust2")

print("=== 1. GET attendance: box.manager to'g'ri keladi ===")
r0 = client.get(f"/api/groups/{GID}/attendance",
                params={"year": TODAY.year, "month": TODAY.month},
                headers=HR)
ck("status 200", r0.status_code, 200)
ck("HR uchun box.manager=True", r0.json()["reschedule"]["manager"], True)

r0b = client.get(f"/api/groups/{GID}/attendance",
                 params={"year": TODAY.year, "month": TODAY.month},
                 headers=TEA)
ck("ustoz uchun box.manager=False", r0b.json()["reschedule"]["manager"],
   False)

print("\n=== 2. HR menejer darsni BUGUNGA ko'chiradi (yangilik) ===")
from_date = TODAY + timedelta(days=15)
r1 = client.post(f"/api/groups/{GID}/reschedule", headers=HR, json={
    "from_date": from_date.isoformat(), "to_date": TODAY.isoformat(),
    "reason": "tezroq tugatish",
})
ck("so'rov muvaffaqiyatli (ilgari 400 edi)", r1.status_code, 200)
ck("darrov qo'llandi", r1.json().get("applied"), True)
ls = db.query(models.Lesson).filter(
    models.Lesson.group_id == GID, models.Lesson.date == TODAY).first()
ck("dars bazada bugungi sanaga ko'chgan", bool(ls), True)

print("\n=== 3. HR menejer O'TIB KETGAN sanaga ko'chira OLMAYDI ===")
from_date2 = TODAY + timedelta(days=16)
yesterday = TODAY - timedelta(days=1)
r2 = client.post(f"/api/groups/{GID}/reschedule", headers=HR, json={
    "from_date": from_date2.isoformat(), "to_date": yesterday.isoformat(),
    "reason": "test",
})
ck("status 400 (o'tib ketgan sanaga hamon taqiqlangan)", r2.status_code, 400)
ck("sababi aniq", "O'tib ketgan sanaga" in r2.json().get("detail", ""), True)

print("\n=== 4. Oddiy ustoz hali ham BUGUNGA ko'chira OLMAYDI (o'zgarmadi) ===")
from_date3 = TODAY + timedelta(days=17)
r3 = client.post(f"/api/groups/{GID}/reschedule", headers=TEA, json={
    "from_date": from_date3.isoformat(), "to_date": TODAY.isoformat(),
    "reason": "test",
})
ck("status 400 (ustoz uchun eski qoida saqlanadi)", r3.status_code, 400)
ck("sababi eski xabar bilan mos",
   "kelajakda bo'lishi kerak" in r3.json().get("detail", ""), True)

db.close()

print()
if fails:
    print(f"XATOLAR ({len(fails)}): " + ", ".join(fails))
    sys.exit(1)
print("HAMMASI O'TDI")
