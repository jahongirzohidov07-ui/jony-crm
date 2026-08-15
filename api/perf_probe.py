"""N+1 O'LCHAGICH (2026-08-15) — Jahongir: "D ni ham qil".

Ishlatish:
    python3 perf_probe.py [--save nom]

Realistik hajmdagi sinov bazasi quradi (3 filial, 45 guruh, 700
o'quvchi, ~4 200 to'lov, ~5 600 yo'qlama) va og'ir sahifalarni
chaqirib HAR BIRI NECHTA SQL SO'ROV yuborishini sanaydi.

--save bilan javoblar /tmp ga yoziladi; tuzatishdan keyin qayta
yurgizib solishtiriladi — javob BIR HARF ham o'zgarmasligi kerak.
Aynan shu tekshiruv "tezlashtiraman deb buzib qo'ymaslik"ni
kafolatlaydi (Jahongir: "platformani biror joyini buzib qoyib
enasini korsatma").
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DATABASE_URL", "sqlite:////tmp/perf.db")

from sqlalchemy import event                       # noqa: E402
from sqlalchemy.engine import Engine               # noqa: E402

_N = [0]


@event.listens_for(Engine, "before_cursor_execute")
def _count(conn, cur, st, p, ctx, many):
    _N[0] += 1


from fastapi.testclient import TestClient          # noqa: E402
import main, models                                # noqa: E402
import entry                                       # noqa: E402
from database import SessionLocal                  # noqa: E402
from auth import hash_password                     # noqa: E402
from datetime import date, timedelta               # noqa: E402

c = TestClient(main.app)


def seed():
    db = SessionLocal()
    if db.query(models.Student).count() > 100:
        db.close()
        return
    print("Sinov bazasi qurilmoqda…")
    brs = []
    for n in ("Bekobod 1", "Bekobod 2", "Yangiyer"):
        b = models.Branch(name=n)
        db.add(b)
        brs.append(b)
    db.commit()
    tchs = []
    for i in range(18):
        t = models.Teacher(full_name=f"Ustoz {i:02d}",
                           branch_id=brs[i % 3].id, is_active=1)
        db.add(t)
        tchs.append(t)
    db.commit()
    groups = []
    for i in range(45):
        g = models.Group(name=f"G-{i:02d}", teacher_id=tchs[i % 18].id,
                         branch_id=brs[i % 3].id, monthly_fee=400000,
                         lesson_price=50000,
                         standard_lessons_per_month=8,
                         lesson_days="mon,wed",
                         lesson_time="10:00 - 12:00")
        db.add(g)
        groups.append(g)
    db.commit()
    today = date.today()
    first = today.replace(day=1)
    studs = []
    for i in range(700):
        g = groups[i % 45]
        s = models.Student(full_name=f"O'quvchi {i:04d}",
                           phone=f"+99890{i:07d}", branch_id=g.branch_id,
                           group_id=g.id, status="active",
                           enrolled_date=first - timedelta(days=90))
        db.add(s)
        studs.append(s)
    db.commit()
    for g in groups:
        for d in range(1, 9):
            db.add(models.Lesson(group_id=g.id,
                                 date=first + timedelta(days=d * 2),
                                 held=1, teacher_id=g.teacher_id))
    db.commit()
    by_group = {}
    for ls in db.query(models.Lesson).all():
        by_group.setdefault(ls.group_id, []).append(ls)
    n = 0
    for s in studs:
        for ls in by_group.get(s.group_id, []):
            db.add(models.Attendance(lesson_id=ls.id, student_id=s.id,
                                     present=1 if (s.id + ls.id) % 7 else 0,
                                     created_by="Ustoz"))
            n += 1
        if n % 4000 == 0:
            db.commit()
    db.commit()
    for s in studs:
        for k in range(3):
            per = (first - timedelta(days=31 * k)).strftime("%Y-%m")
            db.add(models.Payment(student_id=s.id, amount=-400000,
                                  kind="charge", period=per,
                                  created_by="avtomat (oylik)"))
            db.add(models.Payment(student_id=s.id, amount=400000,
                                  kind="payment", method="cash",
                                  created_by="Admin"))
    db.commit()
    for i in range(120):
        db.add(models.Expense(branch_id=brs[i % 3].id, amount=200000,
                              category="rent", date=first,
                              created_by="Admin"))
    for i in range(200):
        db.add(models.Lead(full_name=f"Lid {i:03d}",
                           phone=f"+99891{i:07d}",
                           branch_id=brs[i % 3].id, stage="new",
                           source="instagram"))
    db.commit()
    db.add(models.User(username="asos", full_name="Asoschi",
                       role="founder", password_hash=hash_password("x"),
                       is_active=1))
    db.commit()
    print(f"  {len(studs)} o'quvchi, {len(groups)} guruh, "
          f"{db.query(models.Payment).count()} to'lov, "
          f"{db.query(models.Attendance).count()} yo'qlama")
    db.close()


seed()
H = {"Authorization": "Bearer " + c.post(
    "/api/auth/login", json={"username": "asos", "password": "x"})
    .json()["access_token"]}

PAGES = [
    ("Dashboard", "/api/dashboard"),
    ("O'quvchilar", "/api/students?limit=100"),
    ("Guruhlar", "/api/groups"),
    ("Qarzdorlar", "/api/debtors"),
    ("Pul oqimi", "/api/cashflow/ledger"),
    ("Moliya umumiy", "/api/finance/overview"),
    ("Ustozlar", "/api/teachers"),
    ("Oyliklar", "/api/payouts"),
    ("Lidlar", "/api/leads"),
    ("Xarajatlar", "/api/expenses"),
    ("Vazifalar", "/api/tasks"),
    ("Reja", "/api/plan"),
    ("Zararsizlik", "/api/finance/break-even"),
    ("Ustoz oyligi (kesim)", "/api/reports/teacher-salary-detail"),
    ("Imtihon hisoboti", "/api/reports/exams"),
    ("Davomat hisoboti", "/api/reports/attendance"),
]

save = None
if "--save" in sys.argv:
    save = sys.argv[sys.argv.index("--save") + 1]

print(f"\n{'SAHIFA':26} {'SO`ROV':>7} {'VAQT':>9}   holat")
print("-" * 60)
out = {}
total_q = 0
for label, url in PAGES:
    _N[0] = 0
    t = time.monotonic()
    try:
        r = c.get(url, headers=H)
        ms = round((time.monotonic() - t) * 1000)
        q = _N[0]
        if r.status_code != 200:
            print(f"{label:26} {'—':>7}   {r.status_code}")
            out[label] = {"url": url, "status": r.status_code}
            continue
        total_q += q
        flag = "!!!" if q > 60 else ("!" if q > 25 else "")
        print(f"{label:26} {q:7} {ms:8} ms   {flag}")
        out[label] = {"url": url, "status": 200, "queries": q, "ms": ms}
        if save:
            out[label]["body"] = r.text
    except Exception as e:
        print(f"{label:26} {'XATO':>7}   {str(e)[:60]}")
        out[label] = {"url": url, "error": str(e)}
print("-" * 60)
print(f"{'JAMI':26} {total_q:7}")

if save:
    with open(f"/tmp/perf_{save}.json", "w", encoding="utf-8") as f:
        json.dump(out, f)
    print(f"\nSaqlandi: /tmp/perf_{save}.json")
