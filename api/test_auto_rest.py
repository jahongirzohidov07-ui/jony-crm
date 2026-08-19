"""HAR YILGI AVTOMAT DAM QOIDALARI (2026-08-19).

Jahongir: "Avgust va Dekabr oylarida 12ta dars bo'ladi undan kop
bolmaydi 12ta darsdan keyingi darslarni doim dam qilib belgila,
1-sentabr dam, 25-may dam, 8-mart dam yanvarda ham 12ta dars otamiz
undan kop emas, lekin unda yanvarni boshidagi kunlar dam bo'lishi
kerak".
"""
import os, sys
from datetime import date
os.environ["DATABASE_URL"] = "sqlite:////tmp/autorest.db"
if os.path.exists("/tmp/autorest.db"):
    os.remove("/tmp/autorest.db")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import main, models, entry, groups_lessons, billing   # noqa: E402
from database import SessionLocal                     # noqa: E402

fails = []


def ck(n, g, w):
    ok = g == w
    print(("OK  " if ok else "MUAMMO ") + n + f": {g}"
          + ("" if ok else f" (kutilgan {w})"))
    if not ok:
        fails.append(n)


db = SessionLocal()
b = models.Branch(name="Zafar"); db.add(b); db.commit()
g = models.Group(name="G", branch_id=b.id, lesson_price=40000,
                 standard_lessons_per_month=12, monthly_fee=480000)
db.add(g); db.commit(); GID = g.id


def mk(y, m, days, held=()):
    for d in days:
        db.add(models.Lesson(group_id=GID, date=date(y, m, d),
                             held=1 if d in held else 0))
    db.commit()


def plan(y, m):
    from sqlalchemy import or_
    s_, e_ = billing.month_bounds(y, m)
    return [(L.date.day, L.cancelled or 0, L.cancel_note)
            for L in db.query(models.Lesson)
            .filter(models.Lesson.group_id == GID,
                    models.Lesson.date >= s_, models.Lesson.date <= e_)
            .order_by(models.Lesson.date).all()]


def run(y, m):
    s_, e_ = billing.month_bounds(y, m)
    groups_lessons._auto_rest(db, db.query(models.Group).get(GID), s_, e_)


print("=== 1. Dekabr: 13 dars -> oxirgisi dam ===")
mk(2026, 12, [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25])
run(2026, 12)
rows = plan(2026, 12)
ck("13 tadan 1 dam", sum(1 for r in rows if r[1]), 1)
ck("aynan OXIRGISI (25-dek)", rows[-1][1], 1)
ck("izohi tushunarli", "dekabrda 12 ta dars" in (rows[-1][2] or ""), True)

print("\n=== 2. Ikkinchi ishga tushirish — hech narsa o'zgarmaydi ===")
run(2026, 12)
ck("baribir 1 dam", sum(1 for r in plan(2026, 12) if r[1]), 1)

print("\n=== 3. Yanvar: 14 dars -> BOSHIDAGI 2 tasi dam ===")
mk(2027, 1, [2, 3, 5, 7, 9, 12, 14, 16, 19, 21, 23, 26, 28, 30])
run(2027, 1)
rows = plan(2027, 1)
ck("2 ta dam", sum(1 for r in rows if r[1]), 2)
ck("2-yanvar dam", rows[0][1], 1)
ck("3-yanvar dam", rows[1][1], 1)
ck("5-yanvardan boshlanadi", rows[2][1], 0)

print("\n=== 4. 1-sentabr har doim dam ===")
mk(2026, 9, [1, 2, 4, 7, 9, 11, 14, 16, 18, 21, 23, 25, 28])
run(2026, 9)
rows = plan(2026, 9)
d1 = [r for r in rows if r[0] == 1][0]
ck("1-sentabr dam", d1[1], 1)
ck("izoh: 1-sentabr", "1-sentabr" in (d1[2] or ""), True)
ck("sentabrda boshqa cheklov yo'q (qolgan 12 turibdi)",
   sum(1 for r in rows if not r[1]), 12)

print("\n=== 5. 8-mart va 25-may ham ===")
mk(2027, 3, [8, 10])
run(2027, 3)
ck("8-mart dam", plan(2027, 3)[0][1], 1)
mk(2027, 5, [24, 25])
run(2027, 5)
ck("25-may dam", [r for r in plan(2027, 5) if r[0] == 25][0][1], 1)

print("\n=== 6. O'tilgan darsga tegilmaydi (avgust-2027) ===")
# Avgust 2027: 13 dars, 13-chisi ALLAQACHON o'tilgan (xato bilan) —
# u tegilmaydi, o'rniga oxiridan keyingi bekor bo'ladigan topiladi
mk(2027, 8, [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 31], held=(31,))
run(2027, 8)
rows = plan(2027, 8)
d31 = [r for r in rows if r[0] == 31][0]
ck("o'tilgan 31-avg tegilmadi", d31[1], 0)
ck("o'rniga 23-avg dam bo'ldi",
   [r for r in rows if r[0] == 23][0][1], 1)

print("\n=== 7. O'quv yili boshigacha (2026-avg va oldin) tegilmaydi ===")
mk(2026, 8, [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 31])
run(2026, 8)
ck("2026-avgust o'z holicha (13 dars qoladi)",
   sum(1 for r in plan(2026, 8) if r[1]), 0)
mk(2025, 12, [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25])
run(2025, 12)
ck("2025-dekabr o'z holicha",
   sum(1 for r in plan(2025, 12) if r[1]), 0)

db.close()
print("\n" + ("HAMMASI JOYIDA" if not fails
              else f"MUAMMO: {len(fails)} ta -> {fails}"))
sys.exit(1 if fails else 0)
