"""Xona/guruh sig'imi FAQAT faol o'quvchilar bo'yicha hisoblanishi
(2026-08-09, Jahongir xabar qildi).

Misol: xona sig'imi 30, guruhda 34 ta o'quvchi bor - 29 tasi faol,
5 tasi muzlatilgan. Tizim "34 ta, sig'maydi" derdi - aslida faqat
29 ta joy band, 30 taga sig'adi. Ildiz sabab: _check_schedule() va
_check_enrolment() `status != "archived"` bilan hisoblardi (trial
va frozen'ni ham qo'shib) - /api/groups va /api/timetable esa har
doim `status == "active"` bilan hisoblagan (izchil emas edi)."""
import os, sys
from datetime import date

os.environ["DATABASE_URL"] = "sqlite:////tmp/capacity_active_test.db"
if os.path.exists("/tmp/capacity_active_test.db"):
    os.remove("/tmp/capacity_active_test.db")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import main, models, common  # noqa: F401 - import main triggers create_all
from database import SessionLocal

fails = []


def ck(name, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + name + f": {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


db = SessionLocal()
b = models.Branch(name="Zafar")
db.add(b)
db.commit()

room = models.Room(name="201-xona", branch_id=b.id, capacity=30)
t = models.Teacher(full_name="Ustoz A", branch_id=b.id, is_active=1)
db.add_all([room, t])
db.commit()

g = models.Group(name="G-Katta", branch_id=b.id, teacher_id=t.id,
                 room_id=room.id, lesson_time="10:00-11:00")
db.add(g)
db.commit()
GID = g.id

# Jahongirning aniq misoli: 29 faol + 5 muzlatilgan = 34 jami
for i in range(29):
    db.add(models.Student(full_name=f"Faol {i}", branch_id=b.id,
                          group_id=GID, status="active"))
for i in range(5):
    db.add(models.Student(full_name=f"Muzlatilgan {i}", branch_id=b.id,
                          group_id=GID, status="frozen"))
db.commit()

print("=== 1. _active_student_count faqat FAOLlarni sanaydi ===")
n = common._active_student_count(db, GID)
ck("29 (34 jami, 5 tasi muzlatilgan hisoblanmaydi)", n, 29)

print("\n=== 2. _check_schedule: 34 jami / 30 sig'im - ILGARI "
      "xato blok berardi ===")
problems = common._check_schedule(
    db, group_id=GID, teacher_id=t.id, room_id=room.id,
    lesson_days="mon", lesson_time="10:00-11:00")
over = [p for p in problems if p["key"] == "over_capacity"]
ck("over_capacity YO'Q (29 <= 30, endi to'g'ri)", over, [])

print("\n=== 3. Haqiqatan ham sig'imdan oshsa - hamon TO'G'RI "
      "block qiladi ===")
for i in range(2):   # 29 + 2 = 31 > 30
    db.add(models.Student(full_name=f"Yana faol {i}", branch_id=b.id,
                          group_id=GID, status="active"))
db.commit()
problems2 = common._check_schedule(
    db, group_id=GID, teacher_id=t.id, room_id=room.id,
    lesson_days="mon", lesson_time="10:00-11:00")
over2 = [p for p in problems2 if p["key"] == "over_capacity"]
ck("over_capacity BOR (31 faol > 30 sig'im)", len(over2), 1)
ck("severity block", over2[0]["severity"] if over2 else None, "block")

print("\n=== 4. _check_enrolment: yangi o'quvchi qo'shish ===")
# Guruhni yana 29 faol + 5 muzlatilganga qaytaramiz (2-band holatiga)
db.query(models.Student).filter(
    models.Student.full_name.like("Yana faol%")).delete(
    synchronize_session=False)
db.commit()

new_student = models.Student(full_name="Yangi nomzod", branch_id=b.id,
                             status="trial")
db.add(new_student)
db.commit()

probs3 = common._check_enrolment(db, new_student, g)
over3 = [p for p in probs3 if p["key"] == "over_capacity"]
ck("30-chi (oxirgi) joyga sig'adi (29 faol + 1 = 30)", over3, [])

new_student2 = models.Student(full_name="Yana nomzod", branch_id=b.id,
                              status="trial")
db.add(new_student2)
db.commit()
new_student.group_id = GID
new_student.status = "active"  # avvalgisi endi haqiqatan guruhda - 30 faol
db.commit()

probs4 = common._check_enrolment(db, new_student2, g)
over4 = [p for p in probs4 if p["key"] == "over_capacity"]
ck("31-chi joyga SIG'MAYDI (30 faol + 1 > 30)", len(over4), 1)

db.close()

print()
if fails:
    print(f"XATOLAR ({len(fails)}): " + ", ".join(fails))
    sys.exit(1)
print("HAMMASI O'TDI")
