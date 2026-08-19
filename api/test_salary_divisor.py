"""OYLIK BO'LUVCHISI — REJADAGI DARS SONI (2026-08-19).

Jahongir: "biz minimum 12ta dars o'tishimiz kerak va bu oy hisoblashi
boyicha 13ta dars bor lekin sen 11ta bilan bir o'quvchiga to'liq
o'tmasidan 140,000 hisoblab qoygansan" -> tasdiqladi: "yangi hisobni
tasdiqlayman 13 ta darsni toliq o'tsa 160,000 oladi".

Qoida: bir yo'qlama = oylik stavka / max(12, shu oydagi rejadagi dars
soni). Faqat 2026-avgustdan; o'tgan oylar eski qoidada.
"""
import os, sys
from datetime import date
os.environ["DATABASE_URL"] = "sqlite:////tmp/saldiv.db"
if os.path.exists("/tmp/saldiv.db"):
    os.remove("/tmp/saldiv.db")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles, billing                # noqa: E402
import entry                                       # noqa: E402
from database import SessionLocal                  # noqa: E402
from auth import hash_password                     # noqa: E402

c = TestClient(main.app)
fails = []


def ck(n, g, w):
    ok = g == w
    print(("OK  " if ok else "MUAMMO ") + n + f": {g}"
          + ("" if ok else f" (kutilgan {w})"))
    if not ok:
        fails.append(n)


db = SessionLocal()
b = models.Branch(name="Zafar"); db.add(b); db.commit()
t = models.Teacher(full_name="Nodira Akramova", branch_id=b.id,
                   is_active=1)
db.add(t); db.commit()
# rate_manual=1: stavka aniq 160 000 bo'lsin (daraja jadvalisiz)
g13 = models.Group(name="NEW LEARNERS", branch_id=b.id, teacher_id=t.id,
                   monthly_fee=480000, lesson_price=40000,
                   standard_lessons_per_month=12,
                   rate_manual=1, teacher_rate_per_student=160000)
g12 = models.Group(name="ODDIY", branch_id=b.id, teacher_id=t.id,
                   monthly_fee=480000, lesson_price=40000,
                   standard_lessons_per_month=12,
                   rate_manual=1, teacher_rate_per_student=160000)
db.add_all([g13, g12]); db.commit()
s1 = models.Student(full_name="Bola Bir", branch_id=b.id,
                    group_id=g13.id, status="active")
s2 = models.Student(full_name="Bola Ikki", branch_id=b.id,
                    group_id=g12.id, status="active")
db.add_all([s1, s2]); db.commit()

Y, M = 2026, 8
# 13 darslik guruh: 13 ta dars REJA, 11 tasi o'tilgan+belgilangan
for d in range(1, 14):
    L = models.Lesson(group_id=g13.id, teacher_id=t.id,
                      date=date(Y, M, d), held=1 if d <= 11 else 0)
    db.add(L); db.flush()
    if d <= 11:
        db.add(models.Attendance(lesson_id=L.id, student_id=s1.id,
                                 present=1))
# 12 darslik guruh: 12 reja, hammasi o'tilgan
for d in range(1, 13):
    L = models.Lesson(group_id=g12.id, teacher_id=t.id,
                      date=date(Y, M, d), held=1)
    db.add(L); db.flush()
    db.add(models.Attendance(lesson_id=L.id, student_id=s2.id, present=1))
db.commit()
db.add(models.User(username="asos", full_name="Asoschi",
                   password_hash=hash_password("x"), role=roles.FOUNDER,
                   branch_id=b.id))
db.commit()
TID = t.id
db.close()
tok = c.post("/api/auth/login",
             json={"username": "asos", "password": "x"}).json()["access_token"]
H = {"Authorization": f"Bearer {tok}"}

r = c.get(f"/api/reports/teacher-salary-detail?year={Y}&month={M}",
          headers=H).json()
row = r["rows"][0]
by = {x["student"]: x for x in row["students"]}

print("\n=== 1. 13 darslik oy: 11 dars = 160000 x 11/13 ===")
ck("Bola Bir", by["Bola Bir"]["amount"], round(160000 * 11 / 13, 2))

print("\n=== 2. 12 darslik oy: to'liq = aynan 160 000 (o'zgarmadi) ===")
ck("Bola Ikki", by["Bola Ikki"]["amount"], 160000.0)

print("\n=== 3. Qolgan 2 dars ham o'tilsa — aynan 160 000 ===")
db = SessionLocal()
for L in (db.query(models.Lesson)
          .filter(models.Lesson.group_id == 1,
                  models.Lesson.held == 0).all()):
    L.held = 1
    db.add(models.Attendance(lesson_id=L.id, student_id=1, present=1))
db.commit(); db.close()
r = c.get(f"/api/reports/teacher-salary-detail?year={Y}&month={M}",
          headers=H).json()
by = {x["student"]: x for x in r["rows"][0]["students"]}
ck("13/13 = to'liq stavka", by["Bola Bir"]["amount"], 160000.0)

print("\n=== 4. O'tgan oy (2026-iyul) eski qoidada qoladi ===")
db = SessionLocal()
g_old = models.Group(name="ESKI", branch_id=1, teacher_id=TID,
                     monthly_fee=480000, lesson_price=40000,
                     standard_lessons_per_month=12,
                     rate_manual=1, teacher_rate_per_student=160000)
db.add(g_old); db.commit()
s3 = models.Student(full_name="Bola Uch", branch_id=1,
                    group_id=g_old.id, status="active")
db.add(s3); db.commit()
for d in range(1, 14):        # iyulda 13 dars, hammasi o'tilgan
    L = models.Lesson(group_id=g_old.id, teacher_id=TID,
                      date=date(2026, 7, d), held=1)
    db.add(L); db.flush()
    db.add(models.Attendance(lesson_id=L.id, student_id=s3.id, present=1))
db.commit(); db.close()
r = c.get("/api/reports/teacher-salary-detail?year=2026&month=7",
          headers=H).json()
by = {x["student"]: x for x in r["rows"][0]["students"]}
# eski qoida: 13 x 160000/12 = 173333.33 — o'tgan oy QAYTA OCHILMAYDI
ck("iyul eski qoidada", by["Bola Uch"]["amount"],
   round(13 * 160000 / 12, 2))

print("\n=== 5. 11 rejali oy bo'lsa ham 12 ga bo'linadi ===")
ck("month_divisor min 12",
   billing.month_divisor.__doc__ is not None, True)
db = SessionLocal()
g11 = models.Group(name="OZ", branch_id=1, teacher_id=TID,
                   monthly_fee=480000, lesson_price=40000,
                   standard_lessons_per_month=12,
                   rate_manual=1, teacher_rate_per_student=160000)
db.add(g11); db.commit()
for d in range(1, 12):
    db.add(models.Lesson(group_id=g11.id, teacher_id=TID,
                         date=date(Y, M, d), held=1))
db.commit()
d_ = billing.month_divisor(db, g11, date(Y, M, 5))
ck("11 reja -> bo'luvchi 12", d_, 12)
d13 = billing.month_divisor(db, db.query(models.Group).get(1),
                            date(Y, M, 5))
ck("13 reja -> bo'luvchi 13", d13, 13)
db.close()

print("\n" + ("HAMMASI JOYIDA" if not fails
              else f"MUAMMO: {len(fails)} ta -> {fails}"))
sys.exit(1 if fails else 0)
