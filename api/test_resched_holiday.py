"""DARS DAM KUNIGA KO'CHIRILMASIN (2026-09-03).

Jahongir: "negadur 5-kundan boshlanyabdi darslar lekin 3-kundan
boshlanishi kerak, balkim boshqa shunaqa holatlar ham bordir nega
unaqa boldi".

HAQIQIY HOLAT. "Best Kids" guruhida 3-sentabr darsi 1-sentabrga
ko'chirilgan edi. 1-sentabr esa har yilgi qat'iy dam kuni — jadval
sinxronlanganda o'sha dars avtomat BEKOR bo'ldi. Asl kunida (3-sentabr)
esa yangi dars yaratilmaydi, chunki u kun "ko'chirilgan" deb
belgilangan. Natijada dars butunlay yo'qoldi va guruh oyda 12 o'rniga
11 dars bilan qoldi.

Test ikki narsani isbotlaydi:
  1. TAKRORLANMAYDI — endi dam kuniga ko'chirishga urinish rad
     etiladi va sabab aytiladi;
  2. QAYTARILADI — mavjud shunday holat bir martalik tuzatish bilan
     o'z kuniga qaytariladi, ko'chirish yozuvi esa o'chirilmaydi.
"""
import os, sys
from datetime import date, timedelta

os.environ["DATABASE_URL"] = "sqlite:////tmp/rhol_test.db"
if os.path.exists("/tmp/rhol_test.db"):
    os.remove("/tmp/rhol_test.db")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
import main, models, roles, groups_lessons
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
b = models.Branch(name="Bekobod 2")
db.add(b)
db.commit()
BID = b.id
db.add(models.User(username="asos", password_hash=hash_password("x"),
                   full_name="Asoschi", role="founder"))
db.commit()
t = models.Teacher(full_name="Sardor Mirfozilov", branch_id=BID,
                   is_active=1, grade="middle",
                   hired_date=date(2026, 8, 3))
db.add(t)
db.commit()
TID = t.id
# Haqiqiy guruh: seshanba/payshanba/shanba, 1-avgustdan
g = models.Group(name="Best Kids", teacher_id=TID, branch_id=BID,
                 subject="english", lesson_days="tue,thu,sat",
                 lesson_time="08:00", start_date=date(2026, 8, 1),
                 lesson_price=40000, monthly_fee=480000,
                 standard_lessons_per_month=12)
db.add(g)
db.commit()
GID = g.id
for i in range(10):
    db.add(models.Student(full_name=f"Bola {i}", branch_id=BID,
                          group_id=GID, status="active",
                          enrolled_date=date(2026, 8, 1)))
db.commit()
db.close()

H = tok("asos")

print("=== 1. SENTABR JADVALI TO'LIQ (dam kunidan tashqari) ===")
d = client.get(f"/api/groups/{GID}/attendance?year=2026&month=9",
               headers=H).json()
days = [x["date"] for x in d["lessons"]]
ck("dars 3-sentabrdan boshlanadi", days[0], "2026-09-03")
ck("1-sentabr yo'q (dam kuni)", "2026-09-01" in days, False)
ck("sentabrda 12 ta dars", len(days), 12)

print("\n=== 2. DAM KUNI ANIQLANADI ===")
db = SessionLocal()
ck("1-sentabr dam", groups_lessons.dam_kun_nomi(db, date(2026, 9, 1)),
   "1-sentabr")
ck("8-mart dam", groups_lessons.dam_kun_nomi(db, date(2027, 3, 8)),
   "8-mart")
ck("25-may dam", groups_lessons.dam_kun_nomi(db, date(2027, 5, 25)),
   "25-may")
ck("3-sentabr dam EMAS",
   groups_lessons.dam_kun_nomi(db, date(2026, 9, 3)), None)
db.close()

print("\n=== 3. DAM KUNIGA KO'CHIRIB BO'LMAYDI ===")
r = client.post(f"/api/groups/{GID}/reschedule", headers=H, json={
    "from_date": "2026-09-03", "to_date": "2026-09-01",
    "reason": "other", "note": "sinov"})
ck("rad etiladi", r.status_code, 400)
msg = str(r.json().get("detail", ""))
ck("sabab tushunarli", "dam kuni" in msg, True)
ck("dam kuni nomi aytiladi", "1-sentabr" in msg, True)

db = SessionLocal()
ck("ko'chirish yozuvi YARATILMADI",
   db.query(models.LessonReschedule).count(), 0)
db.close()
d = client.get(f"/api/groups/{GID}/attendance?year=2026&month=9",
               headers=H).json()
ck("3-sentabr joyida qoldi",
   d["lessons"][0]["date"], "2026-09-03")
ck("dars soni o'zgarmadi", len(d["lessons"]), 12)

print("\n=== 4. QO'LDA BELGILANGAN DAM KUNIGA HAM BO'LMAYDI ===")
db = SessionLocal()
db.add(models.Holiday(date=date(2026, 9, 12), name="Markaz tadbiri",
                      created_by="Asoschi"))
db.commit()
db.close()
r = client.post(f"/api/groups/{GID}/reschedule", headers=H, json={
    "from_date": "2026-09-10", "to_date": "2026-09-12",
    "reason": "other"})
ck("rad etiladi", r.status_code, 400)
ck("nomi aytiladi", "Markaz tadbiri" in str(r.json().get("detail", "")),
   True)

print("\n=== 5. ODDIY KUNGA KO'CHIRISH ISHLAYDI ===")
r = client.post(f"/api/groups/{GID}/reschedule", headers=H, json={
    "from_date": "2026-09-10", "to_date": "2026-09-11",
    "reason": "other"})
ck("saqlandi", r.status_code, 200)
ck("qo'llandi", r.json()["applied"], True)
d = client.get(f"/api/groups/{GID}/attendance?year=2026&month=9",
               headers=H).json()
days = [x["date"] for x in d["lessons"]]
ck("11-sentabrga ko'chdi", "2026-09-11" in days, True)
ck("10-sentabr bo'shadi", "2026-09-10" in days, False)
ck("dars soni O'ZGARMADI (yo'qolmadi)", len(days), 12)

print("\n=== 6. ESKI BUZUQ HOLAT QAYTARILADI ===")
# Haqiqiy bazadagi holatni aynan qayta yasaymiz: 3-sentabr darsi
# 1-sentabrga ko'chirilgan, u yerda esa avtomat bekor bo'lgan.
db = SessionLocal()
_ls = db.query(models.Lesson).filter(
    models.Lesson.group_id == GID,
    models.Lesson.date == date(2026, 9, 3)).first()
_ls.date = date(2026, 9, 1)
_ls.note = "· ko'chirildi"
_ls.cancelled = 1
_ls.cancel_note = "Dam kuni: 1-sentabr"
bad = models.LessonReschedule(
    group_id=GID, teacher_id=TID,
    from_date=date(2026, 9, 3), to_date=date(2026, 9, 1),
    status="auto", auto_approved=1, reason="other")
db.add(bad)
db.commit()
BAD_ID = bad.id
db.close()

d = client.get(f"/api/groups/{GID}/attendance?year=2026&month=9",
               headers=H).json()
ck("buzuq holat: 11 ta dars", len(d["lessons"]), 11)
ck("buzuq holat: 5-sentabrdan boshlanadi",
   d["lessons"][0]["date"], "2026-09-05")

db = SessionLocal()
n = groups_lessons.fix_reschedules_onto_holidays(db)
db.close()
ck("1 ta ko'chirish qaytarildi", n, 1)

d = client.get(f"/api/groups/{GID}/attendance?year=2026&month=9",
               headers=H).json()
ck("yana 3-sentabrdan boshlanadi",
   d["lessons"][0]["date"], "2026-09-03")
ck("yana 12 ta dars", len(d["lessons"]), 12)

db = SessionLocal()
row = db.query(models.LessonReschedule).get(BAD_ID)
ck("ko'chirish yozuvi O'CHIRILMADI", row is not None, True)
ck("statusi bekor qilindi", row.status, "cancelled")
ck("sabab yozilgan", "dam kuni" in (row.decision_note or ""), True)
_l = db.query(models.Lesson).filter(
    models.Lesson.group_id == GID,
    models.Lesson.date == date(2026, 9, 3)).first()
ck("dars o'z kuniga qaytdi", _l is not None, True)
ck("bekor belgisi olindi", _l.cancelled, 0)
ck("\"ko'chirildi\" izohi tozalandi", _l.note, None)
db.close()

print("\n=== 7. TUZATISH IDEMPOTENT ===")
db = SessionLocal()
ck("ikkinchi marta hech nima qilmaydi",
   groups_lessons.fix_reschedules_onto_holidays(db), 0)
db.close()

print("\n=== 8. O'TILGAN DARSGA TEGILMAYDI ===")
db = SessionLocal()
held = models.Lesson(group_id=GID, date=date(2027, 3, 8), held=1,
                     teacher_id=TID)
db.add(held)
db.commit()
db.add(models.LessonReschedule(
    group_id=GID, teacher_id=TID,
    from_date=date(2027, 3, 6), to_date=date(2027, 3, 8),
    status="auto", auto_approved=1, reason="other"))
db.commit()
HELD_ID = held.id
n2 = groups_lessons.fix_reschedules_onto_holidays(db)
db.close()
ck("yozuv bekor qilindi", n2, 1)
db = SessionLocal()
hl = db.query(models.Lesson).get(HELD_ID)
ck("O'TILGAN dars joyida qoldi", hl.date.isoformat(), "2027-03-08")
ck("o'tilganligi saqlandi", hl.held, 1)
db.close()

print("\n" + ("BARCHASI OK" if not fails else f"XATOLAR: {fails}"))
sys.exit(1 if fails else 0)
