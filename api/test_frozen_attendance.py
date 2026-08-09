"""Muzlatilgan (frozen) o'quvchi yo'qlama/baholashda hech kimga
ko'rinmasin va belgilanmasin (2026-08-09).

Kontekst: attendance_grid_v2 (entry.py) allaqachon muzlatilgan
o'quvchini ro'yxatdan olib tashlar edi, LEKIN faqat
`user.role == roles.TEACHER` bo'lsa. Jahongir skrinshot bilan
ko'rsatdi: HR menejer (yoki boshqa rol) guruhni ochsa, muzlatilgan
o'quvchi hali ham to'liq qator bo'lib, yoqlama belgisi bilan
chiqaverardi. Sabab (yo'qlama — ish haqi hujjati) ROLGA BOG'LIQ
EMAS, shuning uchun endi HAMMA rol uchun bir xil ishlaydi.

Shu bilan bir qatorda grades_grid() da BUTUNLAY tekshiruv yo'q edi
(hech qanday rol uchun) — shuni ham qo'shdik. Va ikkala saqlash
endpoint'iga (save_attendance, save_grades) himoya qo'shildi: hatto
eski/keshlangan sahifa yoki to'g'ridan-to'g'ri so'rov orqali ham
muzlatilgan o'quvchiga belgi qo'yib bo'lmaydi — payload'dagi boshqa
o'quvchilar esa normal saqlanadi (butun so'rov rad etilmaydi).

MUHIM: `import entry` qilinadi — haqiqiy production yo'li
(attendance_grid_v2, save_attendance_v2, save_grades_v2) orqali
tekshiriladi."""
import os, sys
from datetime import date, timedelta

os.environ["DATABASE_URL"] = "sqlite:////tmp/frozen_att_test.db"
if os.path.exists("/tmp/frozen_att_test.db"):
    os.remove("/tmp/frozen_att_test.db")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
import main, models
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

t = models.Teacher(full_name="Ustoz Frozen", branch_id=BID, is_active=1)
db.add(t)
db.commit()
db.add(models.User(username="ustf1", full_name="Ustoz Frozen",
                   role="teacher", branch_id=BID,
                   password_hash=hash_password("x"), is_active=1))
db.add(models.User(username="hrmf1", full_name="HR Menejer",
                   role="hr_manager", branch_id=BID,
                   password_hash=hash_password("x"), is_active=1))
db.commit()
t.user_id = db.query(models.User).filter(
    models.User.username == "ustf1").first().id
db.commit()

TODAY = date.today()
# _sync_scheduled_lessons() guruhning lesson_days'iga mos kelmagan,
# hali bo'sh (yoqlama/baho yo'q) darslarni "stale" deb o'chirib
# yuboradi — shuning uchun guruhga BUGUNGI hafta kunini albatta
# lesson_days sifatida berish kerak, aks holda pastda qo'lda
# yaratilgan Lesson birinchi GET chaqiruvidayoq o'chib ketadi.
_WD_KEYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
g = models.Group(name="G-Frozen", branch_id=BID, teacher_id=t.id,
                 lesson_time="10:00-11:00",
                 lesson_days=_WD_KEYS[TODAY.weekday()])
db.add(g)
db.commit()
GID = g.id

active = models.Student(full_name="Faol Ali", branch_id=BID, group_id=GID,
                        status="active")
frozen = models.Student(full_name="Muzlatilgan Vali", branch_id=BID,
                        group_id=GID, status="frozen")
db.add(active); db.add(frozen)
db.commit()
ACTIVE_ID, FROZEN_ID = active.id, frozen.id

ls = models.Lesson(group_id=GID, teacher_id=t.id, date=TODAY, held=0)
db.add(ls); db.commit()
LID = ls.id

HR = tok("hrmf1")
TEA = tok("ustf1")

print("=== 1. Davomat ro'yxati: muzlatilgan HR uchun HAM chiqmaydi "
      "(ilgari faqat ustoz uchun ishlardi) ===")
r1 = client.get(f"/api/groups/{GID}/attendance",
                params={"year": TODAY.year, "month": TODAY.month},
                headers=HR)
ck("status 200", r1.status_code, 200)
ids1 = [s["id"] for s in r1.json()["students"]]
ck("faol bor", ACTIVE_ID in ids1, True)
ck("muzlatilgan yo'q (HR uchun ham)", FROZEN_ID in ids1, False)

print("\n=== 2. Xuddi shu — ustoz uchun ham (o'zgarmadi) ===")
r2 = client.get(f"/api/groups/{GID}/attendance",
                params={"year": TODAY.year, "month": TODAY.month},
                headers=TEA)
ck("status 200", r2.status_code, 200)
ids2 = [s["id"] for s in r2.json()["students"]]
ck("muzlatilgan yo'q (ustoz)", FROZEN_ID in ids2, False)

print("\n=== 3. Baholash ro'yxati: muzlatilgan YANGILIK sifatida "
      "chiqmaydi (ilgari hech kim uchun filtrlanmasdi) ===")
r3 = client.get(f"/api/groups/{GID}/grades",
                params={"year": TODAY.year, "month": TODAY.month},
                headers=HR)
ck("status 200", r3.status_code, 200)
ids3 = [s["id"] for s in r3.json()["students"]]
ck("faol bor", ACTIVE_ID in ids3, True)
ck("muzlatilgan yo'q", FROZEN_ID in ids3, False)

print("\n=== 4. Saqlashda himoya: muzlatilganga yoqlama qo'yilsa ham "
      "jimgina o'tkazib yuboriladi, faolniki saqlanadi ===")
r4 = client.put(f"/api/lessons/{LID}/attendance", headers=HR, json={
    "marks": [
        {"student_id": ACTIVE_ID, "present": True},
        {"student_id": FROZEN_ID, "present": True},
    ]
})
ck("status 200 (butun so'rov rad etilmaydi)", r4.status_code, 200)
db.expire_all()
att_active = db.query(models.Attendance).filter(
    models.Attendance.lesson_id == LID,
    models.Attendance.student_id == ACTIVE_ID).first()
att_frozen = db.query(models.Attendance).filter(
    models.Attendance.lesson_id == LID,
    models.Attendance.student_id == FROZEN_ID).first()
ck("faolga belgi qo'yildi", bool(att_active), True)
ck("muzlatilganga belgi QO'YILMADI", bool(att_frozen), False)

print("\n=== 5. Baho saqlashda ham himoya (avval yo'qlama yo'q "
      "bo'lgani uchun ham, muzlatilgan bo'lgani uchun ham bloklanadi). "
      "HR emas, USTOZ tokeni bilan — HR baholashga umuman ruxsati yo'q, "
      "bu boshqa, tegishsiz chegara (GRADE_EDIT) ===")
r5 = client.put(f"/api/lessons/{LID}/grades", headers=TEA, json={
    "marks": [{"student_id": FROZEN_ID, "score": 5}]
})
ck("baho qo'yilmaydi (avval yo'qlama yo'q xabari yoki jim o'tkazish)",
   r5.status_code in (200, 400), True)
grade_frozen = db.query(models.DailyGrade).filter(
    models.DailyGrade.lesson_id == LID,
    models.DailyGrade.student_id == FROZEN_ID).first()
ck("muzlatilganga baho bazada yo'q", bool(grade_frozen), False)

db.close()

print()
if fails:
    print(f"XATOLAR ({len(fails)}): " + ", ".join(fails))
    sys.exit(1)
print("HAMMASI O'TDI")
