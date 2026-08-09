"""HR menejerning dars ko'chirish (reschedule) huquqi (2026-08).

Kontekst: entry.py'da "HR MENEJERGA YANA UCHTA HUQUQ" bo'limi
roles.RESCHEDULE_APPROVE ro'yxatiga HR_MANAGER'ni QO'SHAR edi, lekin
bu qo'shish faylning O'RTASIDA (qator ~3040) turardi - Python
@decorator'larni yozuv tartibida, yuqoridan pastga ishga tushiradi va
require_role(*ro'yxat) ro'yxatni O'SHA DAQIQADAGI holatida (snapshot)
o'qib oladi. Natijada:
  - reschedule_decide_v2 (fayl boshiga yaqinroq, ~1170-qator) hali
    HR_MANAGER qo'shilmasdan turib ro'yxatni o'qib ulgurardi;
  - GET /api/reschedules (groups_lessons.py'da, main.py orqali -
    entry.py o'zining BIRINCHI qatoridayoq to'liq import qilib
    bo'ladi) esa entry.py hali bitta qatori ham ishlamasidan oldin
    to'liq ro'yxatdan o'tib bo'lgan edi - keyingi HAR QANDAY qo'shish
    UNGA umuman yetib bormasdi.
Amalda: HR menejer darsni TO'G'RIDAN-TO'G'RI ko'chira olardi (bu
tekshiruv shu ikkalasiga bog'liq emas edi - alohida "manager"
tekshiruvi), lekin ustozlarning kvotadan oshgan so'rovlarini
KO'RA olmasdi, TASDIQLAY ham olmasdi (403).

Bonus: shu yo'l bilan "kelajakdagi darsni oldinga (ertaroqqa) surish"
imkoniyati chindan ham ALLAQACHON ishlashini ham tasdiqlaymiz - hech
qanday kod hech qaysi yo'nalishni (oldinga/orqaga) cheklamaydi."""
import os, sys
from datetime import date, timedelta

os.environ["DATABASE_URL"] = "sqlite:////tmp/hr_resched_test.db"
if os.path.exists("/tmp/hr_resched_test.db"):
    os.remove("/tmp/hr_resched_test.db")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
import main, models, roles
import entry  # noqa: F401 - HR_MANAGER huquqi shu yerda beriladi;
              # entry.py import qilinmasa bu butun sinov ma'nosiz
              # bo'lib qolardi (production aynan shu orqali ishlaydi).
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
db.add(models.User(username="ust1", full_name="Ustoz A", role="teacher",
                   branch_id=BID, password_hash=hash_password("x"),
                   is_active=1))
db.add(models.User(username="hrm", full_name="HR Menejer",
                   role="hr_manager", branch_id=BID,
                   password_hash=hash_password("x"), is_active=1))
db.commit()
t.user_id = db.query(models.User).filter(
    models.User.username == "ust1").first().id
db.commit()

g = models.Group(name="G-Aug", branch_id=BID, teacher_id=t.id,
                 lesson_time="10:00-11:00")
db.add(g)
db.commit()
GID = g.id

TODAY = date.today()
HR = tok("hrm")
TEA = tok("ust1")

print("=== 1. HR menejer darsni ERTAROQQA (oldinga) ko'chiradi ===")
from_date = TODAY + timedelta(days=20)
to_date = TODAY + timedelta(days=5)   # from_date'dan OLDINROQ
ck("to_date from_date'dan oldinroq (sinov shartini tekshiramiz)",
   to_date < from_date, True)

r = client.post(f"/api/groups/{GID}/reschedule", headers=HR, json={
    "from_date": from_date.isoformat(), "to_date": to_date.isoformat(),
    "reason": "tezroq tugatish",
})
ck("so'rov muvaffaqiyatli", r.status_code, 200)
body = r.json()
ck("darrov qo'llandi (kvotasiz, rahbariyat sifatida)",
   body.get("applied"), True)
ck("holati 'approved'", body.get("status"), "approved")

ls = db.query(models.Lesson).filter(
    models.Lesson.group_id == GID, models.Lesson.date == to_date).first()
ck("dars bazada haqiqatan ham yangi (ertaroq) sanaga ko'chgan",
   bool(ls), True)

print("\n=== 2. HR menejer kutilayotgan so'rovlar ro'yxatini ko'radi ===")
r2 = client.get("/api/reschedules", headers=HR)
ck("ro'yxat ochiladi (ilgari 403 edi)", r2.status_code, 200)

print("\n=== 3. Ustoz kvotasidan oshadi, HR menejer tasdiqlaydi ===")
day_cursor = TODAY + timedelta(days=2)
last_status = None
for i in range(3):
    fd = day_cursor + timedelta(days=i * 3)
    td = fd + timedelta(days=1)
    rr = client.post("/api/me/reschedules", headers=TEA, json={
        "group_id": GID, "from_date": fd.isoformat(),
        "to_date": td.isoformat(),
    })
    last_status = rr.json().get("status")
ck("uchinchi so'rov kvotadan oshib, tasdiqqa kutilmoqda",
   last_status, "pending")

pend = db.query(models.LessonReschedule).filter(
    models.LessonReschedule.status == "pending").first()
ck("kutilayotgan yozuv bazada bor", bool(pend), True)

r3 = client.post(f"/api/reschedules/{pend.id}/decide", headers=HR,
                 json={"decision": "approved", "note": "avgustni tezlashtiramiz"})
ck("HR menejer tasdiqlay oladi (ilgari 403 edi)", r3.status_code, 200)
ck("holati 'approved'ga o'zgardi", r3.json().get("status"), "approved")

print("\n=== 4. RUXSAT: ustozning o'zi hali ham ro'yxatni ko'ra olmaydi ===")
r4 = client.get("/api/reschedules", headers=TEA)
ck("oddiy ustoz uchun rahbariyat ro'yxati yopiq bo'lib qoladi",
   r4.status_code, 403)

db.close()

print()
if fails:
    print(f"XATOLAR ({len(fails)}): " + ", ".join(fails))
    sys.exit(1)
print("HAMMASI O'TDI")
