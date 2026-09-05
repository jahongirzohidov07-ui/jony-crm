"""STAVKA TARIXI: O'ZGARISH FAQAT TANLANGAN OYDAN (2026-09-03).

Jahongir: "men tepadagi 80-160gacha bo'lgan summani 20,000dan
oshirmoqchiman sentabrdan ustozlarniki" va "A menga maqul".

Ilgari daraja stavkasi faqat bitta ustunda turardi. Uni oshirsangiz,
AVGUST oyligi ham (allaqachon eski narxda to'langan) yangi stavkada
qayta hisoblanib ko'rinardi — avgust oyligi saqlanmagan edi. Endi
har o'zgarish "qaysi oydan" bilan tarixga yoziladi va oylik hisobi
dars sanasida amalda bo'lgan stavkani oladi.

Test PUL bilan isbotlaydi: bir xil ustoz, avgustda 6 dars, sentabrda
6 dars; stavka 1-sentabrdan 80 000 -> 100 000 qilinadi. Avgust oyligi
o'zgarmasligi, sentabr oyligi oshishi shart.
"""
import os, sys
from datetime import date, timedelta

os.environ["DATABASE_URL"] = "sqlite:////tmp/grh_test.db"
if os.path.exists("/tmp/grh_test.db"):
    os.remove("/tmp/grh_test.db")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
import main, models, roles, billing
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
db.add(models.User(username="asos", password_hash=hash_password("x"),
                   full_name="Asoschi", role="founder"))
db.commit()

jg = db.query(models.TeacherGrade).filter(
    models.TeacherGrade.key == "junior").first()
if jg is None:
    jg = models.TeacherGrade(key="junior", label="Junior teacher",
                             order_no=1, rate_per_student=80000)
    db.add(jg)
else:
    jg.rate_per_student = 80000
db.commit()

t = models.Teacher(full_name="Junior Ustoz", branch_id=BID, is_active=1,
                   grade="junior", hired_date=date(2026, 1, 10))
db.add(t)
db.commit()
TID = t.id
g = models.Group(name="Kids", teacher_id=TID, branch_id=BID,
                 subject="english", lesson_days="mon,wed,fri",
                 lesson_time="09:00", start_date=date(2026, 7, 1),
                 lesson_price=40000, monthly_fee=480000,
                 standard_lessons_per_month=12,
                 teacher_rate_per_student=80000, rate_manual=0)
db.add(g)
db.commit()
GID = g.id
sts = []
for i in range(5):
    s = models.Student(full_name=f"Bola {i}", branch_id=BID, group_id=GID,
                       status="active", enrolled_date=date(2026, 7, 1))
    db.add(s)
    sts.append(s)
db.commit()
for d in [date(2026, 8, 3), date(2026, 8, 5), date(2026, 8, 7),
          date(2026, 8, 10), date(2026, 8, 12), date(2026, 8, 14),
          date(2026, 9, 2), date(2026, 9, 4), date(2026, 9, 7),
          date(2026, 9, 9), date(2026, 9, 11), date(2026, 9, 14)]:
    ls = models.Lesson(group_id=GID, teacher_id=TID, date=d, held=1)
    db.add(ls)
    db.commit()
    for s in sts:
        db.add(models.Attendance(lesson_id=ls.id, student_id=s.id,
                                 present=1))
db.commit()
db.close()

db = SessionLocal()
billing.backfill_grade_rate_history(db)
db.close()


def payroll(y, m):
    db = SessionLocal()
    g_ = db.query(models.Group).get(GID)
    rows = billing.compute_teacher_payroll(db, g_, y, m)
    db.close()
    row = [r for r in rows if r.get("teacher_id") == TID][0]
    return round(row["amount"]), row["rate_per_student_month"]


print("=== 1. OSHIRISHDAN OLDIN ===")
a_amt, a_ps = payroll(2026, 8)
s_amt, s_ps = payroll(2026, 9)
ck("avgust oyligi", a_amt, 200000)
ck("avgust stavkasi", a_ps, 80000)
ck("sentabr oyligi (hozircha eski)", s_amt, 200000)

print("\n=== 2. STAVKA 1-SENTABRDAN 100 000 QILINDI ===")
H = tok("asos")
r = client.put("/api/career/grades/junior", headers=H, json={
    "rate_per_student": 100000, "effective_from": "2026-09-01"})
ck("saqlandi", r.status_code, 200)
ck("javobda qaysi oydan", r.json().get("effective_from"), "2026-09-01")

print("\n=== 3. AVGUST O'ZGARMADI, SENTABR OSHDI ===")
a_amt2, a_ps2 = payroll(2026, 8)
s_amt2, s_ps2 = payroll(2026, 9)
ck("AVGUST OYLIGI O'SHA-O'SHA", a_amt2, 200000)
ck("avgust stavkasi eski", a_ps2, 80000)
ck("SENTABR OYLIGI OSHDI", s_amt2, 250000)
ck("sentabr stavkasi yangi", s_ps2, 100000)

print("\n=== 4. TARIX YOZILDI, O'CHIRILMADI ===")
db = SessionLocal()
hist = (db.query(models.TeacherGradeRate)
        .filter(models.TeacherGradeRate.grade_key == "junior")
        .order_by(models.TeacherGradeRate.effective_from).all())
ck("ikki yozuv", [(h.effective_from.isoformat(), h.rate_per_student)
                  for h in hist],
   [("1900-01-01", 80000.0), ("2026-09-01", 100000.0)])
ck("jadvaldagi hozirgi stavka yangi",
   db.query(models.TeacherGrade).filter(
       models.TeacherGrade.key == "junior").first().rate_per_student,
   100000)
ck("guruh stavkasi ham yangilandi",
   db.query(models.Group).get(GID).teacher_rate_per_student, 100000)
db.close()

print("\n=== 5. KARYERA EKRANIDA TARIX KO'RINADI ===")
c = client.get("/api/career", headers=H).json()
jr = [x for x in c["grades"] if x["key"] == "junior"][0]
ck("rate_history bor", len(jr.get("rate_history", [])), 2)
ck("sentabr yozuvi", jr["rate_history"][-1]["from"], "2026-09-01")

print("\n=== 6. OYNI KO'RSATMASA — JORIY OYDAN ===")
r = client.put("/api/career/grades/junior", headers=H, json={
    "rate_per_student": 110000})
ck("saqlandi", r.status_code, 200)
ck("joriy oyning 1-kuni", r.json().get("effective_from"),
   roles.local_today().replace(day=1).isoformat())

print("\n=== 7. OKTABRDAN YANA O'ZGARSA — SENTABR SAQLANADI ===")
r = client.put("/api/career/grades/junior", headers=H, json={
    "rate_per_student": 120000, "effective_from": "2026-10-01"})
ck("saqlandi", r.status_code, 200)
db = SessionLocal()
rates = billing.grade_rates(db)
ck("avgust: 80 000", rates.on("junior", date(2026, 8, 15)), 80000)
ck("oktabr: 120 000", rates.on("junior", date(2026, 10, 15)), 120000)
ck("dekabr (kelajak): 120 000", rates.on("junior", date(2026, 12, 1)),
   120000)
ck("dict kabi ishlaydi (hozirgi)", rates.get("junior"), 120000)
db.close()

print("\n=== 8. QO'LDA STAVKALI GURUHGA TEGILMAYDI ===")
db = SessionLocal()
g2 = models.Group(name="Istisno", teacher_id=TID, branch_id=BID,
                  subject="english", lesson_days="tue,thu",
                  lesson_time="11:00", start_date=date(2026, 7, 1),
                  lesson_price=40000, monthly_fee=480000,
                  standard_lessons_per_month=12,
                  teacher_rate_per_student=50000, rate_manual=1)
db.add(g2)
db.commit()
ck("qo'lda stavka o'z joyida",
   billing.rate_per_student(db, g2, TID, date(2026, 9, 10)), 50000)
db.close()

print("\n" + ("BARCHASI OK" if not fails else f"XATOLAR: {fails}"))
sys.exit(1 if fails else 0)
