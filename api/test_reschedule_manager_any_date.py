"""Rahbariyat/HR menejer darsni ISTALGAN sanaga ko'chira olishi,
hatto o'tib ketganiga ham (2026-08).

Kontekst: avval group_reschedule() HAMMA uchun (rahbariyatni ham
qo'shib) `to_date <= today` bo'lsa 400 qaytarardi. Birinchi bosqichda
faqat BUGUNGA ko'chirishga ruxsat berildi. Jahongir keyinroq aniq
so'radi: "o'tib ketganga ham hozir kerak" — oy oxirini qayta
taqsimlash yoki orqada qolgan jadvalni tuzatish uchun, HR menejerga
har qanday (o'tmish, bugun, kelajak) sanaga ko'chirish kerak. Yagona
qolgan chegara — shift_days (ikkala tomonga ham amal qiladi) va
manba darsning "held" (allaqachon o'qitilgan/ish haqiga kirgan)
bo'lmasligi. Oddiy ustoz uchun talab o'zgarmadi: qat'iy kelajak.

MUHIM: `import entry` qilinadi — /api/groups/{gid}/reschedule ni
entry.py'dagi group_reschedule_v2 ochadi (to'g'ri delegatsiya qiladi,
lekin bu farqni his qilmasdan har doim haqiqiy yo'l orqali
tekshirish kerak)."""
import os, sys
from datetime import date, timedelta

os.environ["DATABASE_URL"] = "sqlite:////tmp/resched_anydate_test.db"
if os.path.exists("/tmp/resched_anydate_test.db"):
    os.remove("/tmp/resched_anydate_test.db")

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
db.add(models.User(username="ust3", full_name="Ustoz A", role="teacher",
                   branch_id=BID, password_hash=hash_password("x"),
                   is_active=1))
db.add(models.User(username="hrm3", full_name="HR Menejer",
                   role="hr_manager", branch_id=BID,
                   password_hash=hash_password("x"), is_active=1))
db.commit()
t.user_id = db.query(models.User).filter(
    models.User.username == "ust3").first().id
db.commit()

g = models.Group(name="G-Sep", branch_id=BID, teacher_id=t.id,
                 lesson_time="10:00-11:00")
db.add(g)
db.commit()
GID = g.id

TODAY = date.today()
HR = tok("hrm3")
TEA = tok("ust3")

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

print("\n=== 2. HR menejer darsni BUGUNGA ko'chiradi ===")
from_date = TODAY + timedelta(days=15)
r1 = client.post(f"/api/groups/{GID}/reschedule", headers=HR, json={
    "from_date": from_date.isoformat(), "to_date": TODAY.isoformat(),
    "reason": "tezroq tugatish",
})
ck("so'rov muvaffaqiyatli", r1.status_code, 200)
ck("darrov qo'llandi", r1.json().get("applied"), True)
ls = db.query(models.Lesson).filter(
    models.Lesson.group_id == GID, models.Lesson.date == TODAY).first()
ck("dars bazada bugungi sanaga ko'chgan", bool(ls), True)

print("\n=== 3. HR menejer O'TIB KETGAN sanaga ham ko'chiradi (YANGILIK) ===")
from_date2 = TODAY + timedelta(days=16)
past_ok = TODAY - timedelta(days=5)   # shift_days (30) doirasida
r2 = client.post(f"/api/groups/{GID}/reschedule", headers=HR, json={
    "from_date": from_date2.isoformat(), "to_date": past_ok.isoformat(),
    "reason": "jadvalni qayta taqsimlash",
})
ck("so'rov muvaffaqiyatli (ilgari 400 edi)", r2.status_code, 200)
ck("darrov qo'llandi", r2.json().get("applied"), True)
ls2 = db.query(models.Lesson).filter(
    models.Lesson.group_id == GID, models.Lesson.date == past_ok).first()
ck("dars bazada o'tgan sanaga ko'chgan", bool(ls2), True)
ck("held=0 (hali o'qitilmagan, keyin belgilanishi mumkin)",
   ls2.held or 0, 0)

print("\n=== 4. shift_days chegarasi HALI HAM amal qiladi (ikkala "
      "tomonga ham) ===")
from_date3 = TODAY + timedelta(days=17)
too_far_past = TODAY - timedelta(
    days=roles.RESCHEDULE_MAX_SHIFT_DAYS + 10)
r3 = client.post(f"/api/groups/{GID}/reschedule", headers=HR, json={
    "from_date": from_date3.isoformat(),
    "to_date": too_far_past.isoformat(),
    "reason": "test",
})
ck("status 400 (shift chegarasi buzilmaydi)", r3.status_code, 400)
ck("sababi shift haqida",
   "ko'pi bilan" in r3.json().get("detail", ""), True)

print("\n=== 5. Oddiy ustoz hali ham bugun/o'tmishga ko'chira OLMAYDI "
      "(o'zgarmadi) ===")
from_date4 = TODAY + timedelta(days=18)
r4 = client.post(f"/api/groups/{GID}/reschedule", headers=TEA, json={
    "from_date": from_date4.isoformat(), "to_date": TODAY.isoformat(),
    "reason": "test",
})
ck("status 400 (ustoz uchun eski qoida saqlanadi)", r4.status_code, 400)
ck("sababi eski xabar bilan mos",
   "kelajakda bo'lishi kerak" in r4.json().get("detail", ""), True)

db.close()

print()
if fails:
    print(f"XATOLAR ({len(fails)}): " + ", ".join(fails))
    sys.exit(1)
print("HAMMASI O'TDI")
