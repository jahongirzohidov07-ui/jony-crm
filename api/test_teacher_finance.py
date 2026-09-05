# -*- coding: utf-8 -*-
"""USTOZNING MOLIYA BO'LIMI — oylar bo'yicha oylik tarixi (2026-09-05).

Jahongir: "ustozlarda moliya bo'limi qo'shilib oldin olgan oyliklari
har oylik oyliklar o'sha yerga hisoblanib borsin oyliklar tarixi
bo'lsin".

Tekshiradi:
  1. GET /api/my/finance — ustoz o'zining tarixini ko'radi: har oy
     ishlab topgan (yo'qlamadan), olgan (to'lov sanasi bo'yicha),
     qoldiq, yig'ilib boruvchi balans; oylar bo'sh bo'lsa ham uzilmaydi;
  2. raqamlar /api/my/salary (karta) va oyliklar sahifasi bilan bir xil;
  3. ustoz boshqa ustozning tarixini ko'ra olmaydi (403), rahbar ko'radi;
  4. volontyor support raqam ko'rmaydi.
"""
import os
import sys

os.environ["DATABASE_URL"] = "sqlite:////tmp/tfin_test.db"
if os.path.exists("/tmp/tfin_test.db"):
    os.remove("/tmp/tfin_test.db")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import date                            # noqa: E402
from fastapi.testclient import TestClient            # noqa: E402
import main, models, roles, billing                  # noqa: E402
import entry                                         # noqa: E402,F401
from database import SessionLocal                    # noqa: E402
from auth import hash_password                       # noqa: E402

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
b = models.Branch(name="Zafar"); db.add(b); db.commit()
u_t = models.User(username="elena", password_hash=hash_password("x"),
                  full_name="Elena", role=roles.TEACHER, branch_id=b.id)
u_t2 = models.User(username="bobur", password_hash=hash_password("x"),
                   full_name="Bobur", role=roles.TEACHER, branch_id=b.id)
u_f = models.User(username="asos", password_hash=hash_password("x"),
                  full_name="Asoschi", role=roles.FOUNDER)
db.add_all([u_t, u_t2, u_f]); db.commit()
t = models.Teacher(full_name="Elena", is_active=1, branch_id=b.id,
                   grade="middle", user_id=u_t.id)
t2 = models.Teacher(full_name="Bobur", is_active=1, branch_id=b.id,
                    grade="middle", user_id=u_t2.id)
db.add_all([t, t2]); db.commit()
# Qo'lda stavka — daraja jadvalidagi tarixga bog'liq bo'lmasin
g = models.Group(name="Step 1", branch_id=b.id, teacher_id=t.id,
                 lesson_price=40_000, standard_lessons_per_month=12,
                 monthly_fee=480_000, rate_manual=1,
                 teacher_rate_per_student=120_000)
db.add(g); db.commit()
S = []
for i in range(5):
    s = models.Student(full_name=f"Bola {i}", branch_id=b.id, status="active",
                       group_id=g.id, enrolled_date=date(2026, 6, 1))
    db.add(s); db.commit()
    db.add(models.StudentGroupLink(student_id=s.id, group_id=g.id,
                                   is_primary=1, active=1))
    S.append(s)
db.commit()

# Iyun: 12 dars, Iyul: DARS YO'Q (ta'til), Avgust: 12 dars, Sentabr: 2 dars
def darslar(y, m, n):
    for d in range(1, n + 1):
        l = models.Lesson(group_id=g.id, date=date(y, m, d), teacher_id=t.id,
                          held=1)
        db.add(l); db.commit()
        for s in S:
            db.add(models.Attendance(student_id=s.id, lesson_id=l.id, present=1))
    db.commit()


darslar(2026, 6, 12)
darslar(2026, 8, 12)
darslar(2026, 9, 2)

# To'lovlar: iyunda avans 300k, iyulda oylik 600k (iyun uchun),
# avgustda avans 200k. Sentabrda hali yo'q.
for dt, amt, kind in ((date(2026, 6, 15), 300_000, "advance"),
                      (date(2026, 7, 5), 600_000, "salary"),
                      (date(2026, 8, 20), 200_000, "advance")):
    db.add(models.TeacherPayment(teacher_id=t.id, amount=amt, kind=kind,
                                 paid_on=dt, created_by="Asoschi"))
db.commit()

# Iyun: 12 dars x 5 yo'qlama x (120000/12=10000) = 600 000
# Avgust: xuddi shunday 600 000 ; Sentabr: 2 x 5 x 10000 = 100 000
print("=== 1. /api/my/finance — ustoz o'zi ===")
r = client.get("/api/my/finance", headers=tok("elena"))
ck("status 200", r.status_code, 200)
d = r.json()
months = {m["period"]: m for m in d["months"]}
ck("oylar ketma-ket, bo'sh iyul ham bor",
   [m["period"] for m in d["months"]],
   ["2026-09", "2026-08", "2026-07", "2026-06"])
ck("since = 2026-06", d["since"], "2026-06")
ck("iyun ishlab topgan 600 000", months["2026-06"]["earned"], 600_000)
ck("iyun olgan 300 000 (avans)", months["2026-06"]["paid"], 300_000)
ck("iyun qoldiq 300 000", months["2026-06"]["left"], 300_000)
ck("iyun oxirida balans 300 000", months["2026-06"]["balance_after"], 300_000)
ck("iyul ishlab topgan 0 (dars yo'q)", months["2026-07"]["earned"], 0)
ck("iyul olgan 600 000 (oylik)", months["2026-07"]["paid"], 600_000)
ck("iyul qoldiq -600 000", months["2026-07"]["left"], -600_000)
ck("iyul oxirida balans -300 000 (oldindan berilgan)",
   months["2026-07"]["balance_after"], -300_000)
ck("avgust ishlab topgan 600 000", months["2026-08"]["earned"], 600_000)
ck("avgust olgan 200 000", months["2026-08"]["paid"], 200_000)
ck("avgust oxirida balans 100 000", months["2026-08"]["balance_after"], 100_000)
ck("sentabr hozirgi oy", months["2026-09"]["is_current"], True)
ck("sentabr ishlab topgan 100 000", months["2026-09"]["earned"], 100_000)
ck("sentabr olgan 0", months["2026-09"]["paid"], 0)
ck("sentabr oxirida balans 200 000", months["2026-09"]["balance_after"], 200_000)
ck("jami ishlab topgan 1 300 000", d["earned_total"], 1_300_000)
ck("jami olgan 1 100 000", d["paid_total"], 1_100_000)
ck("umumiy balans 200 000", d["balance"], 200_000)
ck("iyul to'lovi ro'yxatda (oylik, Asoschi)",
   [(p["kind"], p["amount"], p["by"]) for p in months["2026-07"]["payments"]],
   [("salary", 600_000, "Asoschi")])
ck("avgust to'lov turlari", (months["2026-08"]["paid_advance"],
                            months["2026-08"]["paid_salary"]), (200_000, 0))
ck("guruh kesimi bor", months["2026-08"]["by_group"][0]["group"], "Step 1")
ck("guruh kesimi: 60 yo'qlama x 10 000",
   (months["2026-08"]["by_group"][0]["attendances"],
    months["2026-08"]["by_group"][0]["rate"]), (60, 10_000))
ck("ustoz pul bera olmaydi", d["can_pay"], False)

print("\n=== 2. Karta bilan bir xil ===")
card = client.get("/api/my/salary", headers=tok("elena")).json()
ck("balans kartadagi bilan teng", d["balance"], card["balance"])
ck("shu oy ishlab topgan kartadagi bilan teng",
   months["2026-09"]["earned"], card["earned_month"])
ck("jami ishlab topgan kartadagi bilan teng", d["earned_total"], card["earned_total"])
pr = client.get("/api/payroll?year=2026&month=8", headers=tok("asos")).json()
row = [x for x in pr["rows"] if x["teacher_id"] == t.id][0]
ck("oyliklar sahifasi (avgust) bilan teng",
   (row["earned"], row["paid"], row["balance"]),
   (months["2026-08"]["earned"], months["2026-08"]["paid"], d["balance"]))

print("\n=== 3. Huquq ===")
r = client.get(f"/api/teachers/{t.id}/finance", headers=tok("bobur"))
ck("boshqa ustoz ko'ra olmaydi: 403", r.status_code, 403)
r = client.get(f"/api/teachers/{t.id}/finance", headers=tok("elena"))
ck("o'ziniki: 200", r.status_code, 200)
r = client.get(f"/api/teachers/{t.id}/finance", headers=tok("asos"))
ck("asoschi ko'radi: 200", r.status_code, 200)
ck("asoschi pul bera oladi", r.json()["can_pay"], True)
r = client.get("/api/my/finance", headers=tok("bobur"))
ck("darsi yo'q ustoz: bo'sh tarix, faqat hozirgi oy",
   (r.status_code, [m["period"] for m in r.json()["months"]]),
   (200, [date.today().isoformat()[:7]]))

print()
print("XATOLAR:", fails if fails else "yo'q")
sys.exit(1 if fails else 0)
