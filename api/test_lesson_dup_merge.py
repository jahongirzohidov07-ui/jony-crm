"""BIR KUNDA IKKITA DARS (2026-10-02).

Jahongir (skrinshot): davomatda "01 okt" ikki marta, "28 dars kuni".
Oy jadvali ikki parallel so'rovda ikki marta yaratilgan, ustoz ikkala
ustunga ham yo'qlama qo'ygan.

Tekshiriladi:
  1. Bo'sh dublikatlar o'chiriladi va bu SAQLANADI (keyingi so'rovda
     ham qaytib kelmaydi).
  2. Ikkalasiga ham belgi qo'yilgan, belgilar mos — bitta darsga
     birlashtiriladi: yo'qlama ko'chadi, takror o'chadi, "o'tilgan"
     saqlanadi, audit yoziladi.
  3. Ziddiyatli belgi (bir o'quvchi bir darsda keldi, ikkinchisida
     kelmadi) — tegilmaydi.
  4. Nusxaga XP bog'langan — tegilmaydi.
"""
import os
import sys
import tempfile
from datetime import date, timedelta

_DIR = os.path.join(tempfile.gettempdir(), "lesson_dup_merge_test")
os.makedirs(_DIR, exist_ok=True)
_DB = os.path.join(_DIR, "db.sqlite")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace(chr(92), "/")
if os.path.exists(_DB):
    os.remove(_DB)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import main, models, roles                         # noqa: E402,F401
import entry                                       # noqa: E402,F401
import groups_lessons as GL                        # noqa: E402
from database import SessionLocal                  # noqa: E402

fails = []


def ck(name, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + name + f": {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


TODAY = roles.local_today()
Y, M = TODAY.year, TODAY.month
_next = date(Y + (M == 12), M % 12 + 1, 1)
LAST = (_next - timedelta(days=1)).day
D_OK, D_BAD, D_XP = date(Y, M, 10), date(Y, M, 11), date(Y, M, 12)

db = SessionLocal()
b = models.Branch(name="Zafar"); db.add(b); db.commit()
t = models.Teacher(full_name="Ustoz", is_active=1, branch_id=b.id)
db.add(t); db.commit()
g = models.Group(name="Cambridge", branch_id=b.id, teacher_id=t.id,
                 lesson_price=40_000,
                 lesson_days="mon,tue,wed,thu,fri,sat,sun",
                 start_date=date(Y - 1, 1, 1))
db.add(g); db.commit()
GID = g.id
studs = []
for i in range(5):
    s = models.Student(full_name=f"O'quvchi {i}", branch_id=b.id,
                       status="active", group_id=GID,
                       enrolled_date=date(Y - 1, 9, 1))
    db.add(s); db.commit()
    studs.append(s.id)

# Poyga: butun oy ikki marta yaratilgan
for _ in range(2):
    for d in range(1, LAST + 1):
        db.add(models.Lesson(group_id=GID, teacher_id=t.id, held=0,
                             date=date(Y, M, d), created_by="avtomat"))
db.commit()


def pair(day):
    return (db.query(models.Lesson)
            .filter(models.Lesson.group_id == GID,
                    models.Lesson.date == day)
            .order_by(models.Lesson.id).all())


def mark(lesson, sids, present):
    lesson.held = 1
    for sid in sids:
        db.add(models.Attendance(lesson_id=lesson.id, student_id=sid,
                                 present=present))
    db.commit()


# 2: mos belgilar — 1-ustun 5 ta "kelmadi", 2-ustun 2 ta "kelmadi"
k_ok, d_ok = pair(D_OK)
mark(k_ok, studs, 0)
mark(d_ok, studs[:2], 0)
db.add(models.DailyGrade(lesson_id=d_ok.id, student_id=studs[3], score=4))
db.commit()
KEEP_OK, DUP_OK = k_ok.id, d_ok.id
# 3: ziddiyat
k_bad, d_bad = pair(D_BAD)
mark(k_bad, studs[:1], 1)
mark(d_bad, studs[:1], 0)
# 4: nusxada XP
k_xp, d_xp = pair(D_XP)
mark(k_xp, studs[:1], 1)
mark(d_xp, studs[:1], 1)
db.add(models.XpTransaction(student_id=studs[0], amount=5,
                            lesson_id=d_xp.id, event_code="LESSON_PRESENT"))
db.commit()
db.close()

start, end = main.billing.month_bounds(Y, M)
s = SessionLocal()
got = GL._group_lessons_in_month(s, GID, Y, M)
s.close()


def count(day=None):
    s = SessionLocal()
    q = s.query(models.Lesson).filter(models.Lesson.group_id == GID,
                                      models.Lesson.date >= start,
                                      models.Lesson.date <= end)
    if day:
        q = q.filter(models.Lesson.date == day)
    n = q.count()
    s.close()
    return n


print("=== 1. Bo'sh dublikatlar o'chdi va saqlandi ===")
ck("javobda: har kunga bitta (+2 ziddiyatli)", len(got), LAST + 2)
ck("bazada ham", count(), LAST + 2)
s = SessionLocal()
GL._group_lessons_in_month(s, GID, Y, M)
s.close()
ck("ikkinchi so'rovdan keyin ham", count(), LAST + 2)

print("\n=== 2. Mos belgilar birlashtirildi ===")
ck("10-kunda bitta dars", count(D_OK), 1)
s = SessionLocal()
ck("qolgani — birinchisi", s.query(models.Lesson.id).filter(
    models.Lesson.group_id == GID,
    models.Lesson.date == D_OK).scalar(), KEEP_OK)
att = s.query(models.Attendance).filter(
    models.Attendance.lesson_id == KEEP_OK).all()
ck("yo'qlama: 5 o'quvchi, takrorsiz", sorted(a.student_id for a in att),
   sorted(studs))
ck("nusxada yo'qlama qolmadi", s.query(models.Attendance).filter(
    models.Attendance.lesson_id == DUP_OK).count(), 0)
ck("baho ko'chdi", s.query(models.DailyGrade.lesson_id).filter(
    models.DailyGrade.student_id == studs[3]).scalar(), KEEP_OK)
ck("o'tilgan saqlandi", s.query(models.Lesson.held).filter(
    models.Lesson.id == KEEP_OK).scalar(), 1)
ck("audit yozildi", s.query(models.AuditLog).filter(
    models.AuditLog.entity == "lesson",
    models.AuditLog.action == "merge").count(), 1)
s.close()

print("\n=== 3-4. Tegilmaydiganlar ===")
ck("ziddiyatli belgilar — ikkala dars qoldi", count(D_BAD), 2)
ck("nusxada XP — ikkala dars qoldi", count(D_XP), 2)

print()
if fails:
    print(f"{len(fails)} ta XATO: {fails}")
    sys.exit(1)
print("HAMMASI OK")
