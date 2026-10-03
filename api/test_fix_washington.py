"""BIR MARTALIK: Bekobod 1 Washington sentabr darslari Xoshimovadan
guruhning hozirgi ustozi Abdujalilovaga (2026-10-03, Jahongir: "hop").
Tekshiriladi: darslar o'tadi, sentabr muhri faqat shu ikkisida qayta
hisoblanadi, boshqa ustoz muhriga tegilmaydi, boshqa guruh/filialga
tegilmaydi; Abdujalilova Bekobod 1 sentabr oyligida chiqadi."""
import os, sys, tempfile
from datetime import date

_DB = os.path.join(tempfile.gettempdir(), "fix_wash.sqlite")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB
if os.path.exists(_DB):
    os.remove(_DB)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import models, entry, common            # noqa: E402
from database import SessionLocal       # noqa: E402

fails = []


def ck(name, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + name + f": {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


db = SessionLocal()
za, b1 = models.Branch(name="Zafar"), models.Branch(name="Bekobod 1")
db.add_all([za, b1]); db.commit()
xo = models.Teacher(full_name="Xoshimova Rayxona", is_active=0, branch_id=za.id)
ab = models.Teacher(full_name="Rayxona Abdujalilova", is_active=1, branch_id=b1.id)
ot = models.Teacher(full_name="Boshqa", is_active=1, branch_id=b1.id)
db.add_all([xo, ab, ot]); db.commit()
W = models.Group(name="Washington", branch_id=b1.id, teacher_id=ab.id,
                 lesson_price=45_000, standard_lessons_per_month=10,
                 monthly_fee=450_000, rate_manual=1,
                 teacher_rate_per_student=450_000)
Z = models.Group(name="Zafar G", branch_id=za.id, teacher_id=xo.id,
                 lesson_price=40_000, standard_lessons_per_month=12,
                 monthly_fee=480_000)
O = models.Group(name="Other", branch_id=b1.id, teacher_id=ot.id,
                 lesson_price=40_000, standard_lessons_per_month=12,
                 monthly_fee=480_000)
db.add_all([W, Z, O]); db.commit()
s = models.Student(full_name="Bola", branch_id=b1.id, status="active",
                   group_id=W.id, enrolled_date=date(2026, 8, 1))
db.add(s); db.commit()
db.add(models.StudentGroupLink(student_id=s.id, group_id=W.id, is_primary=1, active=1))
for d in range(1, 11):
    for g, t in ((W, xo), (O, ot)):
        l = models.Lesson(group_id=g.id, date=date(2026, 9, d), teacher_id=t.id, held=1)
        db.add(l); db.commit()
        if g is W:
            db.add(models.Attendance(student_id=s.id, lesson_id=l.id, present=1))
# Avgust (Zafar) — tegilmasin
lz = models.Lesson(group_id=Z.id, date=date(2026, 8, 5), teacher_id=xo.id, held=1)
db.add(lz); db.commit()
common._seal_month(db, 2026, 9)
seals = {x.teacher_id: x.amount for x in db.query(models.PayrollSeal).filter(
    models.PayrollSeal.period == "2026-09")}
ck("oldin Xoshimovada muhr bor", xo.id in seals, True)
ck("oldin Xoshimova 450 000", seals.get(xo.id), 450_000)
other_before = seals.get(ot.id)
# Boshqa ustoz muhrini qo'lda o'zgartiramiz — tuzatish unga tegmasligi kerak
db.query(models.PayrollSeal).filter(models.PayrollSeal.teacher_id == ot.id).update(
    {"amount": 123})
db.commit()

n = entry._fix_washington_teacher(db)
ck("10 ta dars o'tdi", n, 10)
ck("Washington darslari Abdujalilovada",
   {l.teacher_id for l in db.query(models.Lesson).filter(models.Lesson.group_id == W.id)},
   {ab.id})
ck("Zafar avgust darsi tegilmadi", db.query(models.Lesson).get(lz.id).teacher_id, xo.id)
seals = {x.teacher_id: x.amount for x in db.query(models.PayrollSeal).filter(
    models.PayrollSeal.period == "2026-09")}
ck("Xoshimova sentabr muhri yo'q", xo.id in seals, False)
ck("Abdujalilova muhri = hisoblangan",
   seals.get(ab.id),
   common._teacher_earned(db, ab.id, since=date(2026, 9, 1), until=date(2026, 9, 30))["amount"])
ck("Abdujalilova muhri > 0", (seals.get(ab.id) or 0) > 0, True)
ck("boshqa ustoz muhriga tegilmadi", seals.get(ot.id), 123)
ck("audit yozildi", db.query(models.AuditLog).filter(
    models.AuditLog.field == "darslar ustozi").count(), 1)
ck("ikkinchi marta — 0", entry._fix_washington_teacher(db), 0)
db.close()
print()
if fails:
    print(f"{len(fails)} ta XATO: {fails}"); sys.exit(1)
print("HAMMASI OK")
