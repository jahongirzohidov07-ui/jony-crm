"""Ustoz oyligi o'quvchi kesimida (2026-08-13).

Jahongir: "hisobotlar bolimidan har bir o'quvchidan qancha summa
nechta yo'qlama qoyganligi to'liq korinib turadigan ham korinib
tursin"."""
import os, sys
from datetime import date

os.environ["DATABASE_URL"] = "sqlite:////tmp/sal_detail.db"
if os.path.exists("/tmp/sal_detail.db"):
    os.remove("/tmp/sal_detail.db")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
import main, models, billing
import entry  # noqa
from database import SessionLocal
from auth import hash_password

c = TestClient(main.app)
fails = []


def ck(n, g, w):
    ok = g == w
    print(("OK  " if ok else "XATO ") + n + f": {g}"
          + ("" if ok else f"   (kutilgan {w})"))
    if not ok:
        fails.append(n)


db = SessionLocal()
b = models.Branch(name="Bekobod 1"); db.add(b); db.commit()
t = models.Teacher(full_name="Aslidin Nabiyev", branch_id=b.id, is_active=1)
db.add(t); db.commit()
g = models.Group(name="North Carolina", branch_id=b.id, teacher_id=t.id,
                 monthly_fee=480000, lesson_price=40000,
                 standard_lessons_per_month=12,
                 rate_manual=1, teacher_rate_per_student=120000)
db.add(g); db.commit()
s1 = models.Student(full_name="Ali Valiyev", branch_id=b.id, group_id=g.id,
                    status="active")
s2 = models.Student(full_name="Vali Aliyev", branch_id=b.id, group_id=g.id,
                    status="active")
db.add_all([s1, s2]); db.commit()
S1, S2, TID, GID = s1.id, s2.id, t.id, g.id
today = date.today()
y, m = today.year, today.month
d1, d2, d3 = date(y, m, 3), date(y, m, 5), date(y, m, 7)
for dd in (d1, d2, d3):
    l = models.Lesson(group_id=GID, teacher_id=TID, date=dd, held=1)
    db.add(l); db.commit()
    # Ali uchala darsda ham belgilangan (biri kelmagan),
    # Vali faqat bitta darsda
    db.add(models.Attendance(lesson_id=l.id, student_id=S1,
                             present=0 if dd == d2 else 1))
    if dd == d1:
        db.add(models.Attendance(lesson_id=l.id, student_id=S2, present=1))
    db.commit()
db.add(models.User(username="asos", full_name="Asoschi", role="founder",
                   password_hash=hash_password("x"), is_active=1))
db.commit(); db.close()

H = {"Authorization": "Bearer " + c.post(
    "/api/auth/login", json={"username": "asos", "password": "x"}
).json()["access_token"]}

print("=== 1. Hisobot ochiladi ===")
r = c.get(f"/api/reports/teacher-salary-detail?year={y}&month={m}",
          headers=H)
ck("200", r.status_code, 200)
d = r.json()
ck("bitta ustoz", len(d["rows"]), 1)
row = d["rows"][0]
ck("ustoz nomi", row["teacher"], "Aslidin Nabiyev")
ck("3 ta dars", row["lessons"], 3)
ck("jami 4 ta yo'qlama", row["attendances"], 4)
ck("2 ta o'quvchi", row["students_count"], 2)

print("\n=== 2. O'quvchi kesimi: kimdan qancha ===")
st = {x["student"]: x for x in row["students"]}
ck("Ali 3 ta yo'qlama", st["Ali Valiyev"]["attendances"], 3)
ck("Ali 2 marta keldi", st["Ali Valiyev"]["present"], 2)
ck("Ali 1 marta kelmadi", st["Ali Valiyev"]["absent"], 1)
ck("Vali 1 ta yo'qlama", st["Vali Aliyev"]["attendances"], 1)
ck("guruh nomi ko'rinadi", st["Ali Valiyev"]["groups"], "North Carolina")

print("\n=== 3. Summalar to'g'ri taqsimlangan ===")
rate = st["Vali Aliyev"]["amount"]           # bir yo'qlama narxi
ck("Ali = 3 x bir yo'qlama", round(st["Ali Valiyev"]["amount"], 2),
   round(rate * 3, 2))
ck("ustoz jami = o'quvchilar yig'indisi", round(row["amount"], 2),
   round(st["Ali Valiyev"]["amount"] + st["Vali Aliyev"]["amount"], 2))
ck("bir yo'qlama narxi ko'rsatilgan", row["per_attendance"] > 0, True)

print("\n=== 4. Oylik kartadagi summa bilan bir xil ===")
card = c.get(f"/api/teachers/{TID}/salary", headers=H).json()
ck("kartadagi 'shu oy ishlab topgani' bilan teng",
   round(card["earned_month"], 2), round(row["amount"], 2))

print("\n=== 5. Yo'qlama qo'yilmagan dars pul keltirmaydi ===")
db = SessionLocal()
l4 = models.Lesson(group_id=GID, teacher_id=TID, date=date(y, m, 9), held=1)
db.add(l4); db.commit(); db.close()
d2r = c.get(f"/api/reports/teacher-salary-detail?year={y}&month={m}",
            headers=H).json()["rows"][0]
ck("darslar soni oshdi", d2r["lessons"], 4)
ck("summa o'zgarmadi", round(d2r["amount"], 2), round(row["amount"], 2))

print("\n=== 6. Bitta ustozni alohida so'rash ===")
one = c.get(f"/api/reports/teacher-salary-detail?teacher_id={TID}",
            headers=H).json()
ck("faqat bitta ustoz", len(one["rows"]), 1)

print()
if fails:
    print(f"XATOLAR ({len(fails)}): " + ", ".join(fails))
    sys.exit(1)
print("HAMMASI O'TDI")
