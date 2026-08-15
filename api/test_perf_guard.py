"""TEZLIK QOROVULI (2026-08-15) — Jahongir: "D ni ham qil".

N+1 xatosi shu bilan yomonki: kod to'g'ri ishlaydi, faqat SEKIN.
Test yozilmasa, keyingi o'zgarishda jimgina qaytib keladi va buni
faqat sayt yotganda bilib qolamiz (avgustdagi Neon kvotasi shunday
tugagan edi).

Shu test o'quvchilar sonini IKKI BARAVAR oshirib ko'radi: agar
so'rovlar soni ham oshsa — demak N+1 qaytib kelgan va test yiqiladi.
Bu "shu paytdagi son" ni yodlab olishdan ko'ra ishonchli: mashina
tezligiga ham, ma'lumot hajmiga ham bog'liq emas.
"""
import os
import sys

os.environ["DATABASE_URL"] = "sqlite:////tmp/perfguard.db"
if os.path.exists("/tmp/perfguard.db"):
    os.remove("/tmp/perfguard.db")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import event                       # noqa: E402
from sqlalchemy.engine import Engine               # noqa: E402

_N = [0]


@event.listens_for(Engine, "before_cursor_execute")
def _count(conn, cur, st, p, ctx, many):
    _N[0] += 1


from fastapi.testclient import TestClient          # noqa: E402
from datetime import date, timedelta               # noqa: E402
import main, models                                # noqa: E402
import entry                                       # noqa: E402
from database import SessionLocal                  # noqa: E402
from auth import hash_password                     # noqa: E402

c = TestClient(main.app)
fails = []


def ck(n, g, w):
    ok = g == w
    print(("OK  " if ok else "XATO ") + n + f": {g}"
          + ("" if ok else f" (kutilgan {w})"))
    if not ok:
        fails.append(n)


def build(n_students: int, n_groups: int, tag: str):
    """Bazaga yana o'quvchi qo'shadi."""
    db = SessionLocal()
    br = db.query(models.Branch).first()
    if br is None:
        br = models.Branch(name="Bekobod 1")
        db.add(br)
        db.commit()
    first = date.today().replace(day=1)
    gs = []
    for i in range(n_groups):
        t = models.Teacher(full_name=f"Ustoz {tag}{i}", branch_id=br.id,
                           is_active=1, grade="middle")
        db.add(t)
        db.commit()
        g = models.Group(name=f"G{tag}{i}", teacher_id=t.id,
                         branch_id=br.id, monthly_fee=400000,
                         lesson_price=50000,
                         standard_lessons_per_month=8,
                         lesson_days="mon,wed",
                         lesson_time="10:00 - 12:00")
        db.add(g)
        gs.append(g)
    db.commit()
    for g in gs:
        for d in (2, 4, 6, 8):
            db.add(models.Lesson(group_id=g.id,
                                 date=first + timedelta(days=d),
                                 held=1, teacher_id=g.teacher_id))
    db.commit()
    less = {}
    for ls in db.query(models.Lesson).filter(
            models.Lesson.group_id.in_([g.id for g in gs])).all():
        less.setdefault(ls.group_id, []).append(ls)
    for i in range(n_students):
        g = gs[i % n_groups]
        s = models.Student(full_name=f"O'quvchi {tag}{i:04d}",
                           branch_id=br.id, group_id=g.id,
                           status="active",
                           enrolled_date=first - timedelta(days=60))
        db.add(s)
        db.commit()
        for ls in less.get(g.id, []):
            db.add(models.Attendance(lesson_id=ls.id, student_id=s.id,
                                     present=1, created_by="Ustoz"))
        db.add(models.Payment(student_id=s.id, amount=400000,
                              kind="payment", method="cash",
                              created_by="Admin"))
        db.add(models.Payment(student_id=s.id, amount=-400000,
                              kind="charge",
                              period=first.strftime("%Y-%m"),
                              created_by="avtomat (oylik)"))
    db.commit()
    db.close()


build(60, 6, "a")
db = SessionLocal()
db.add(models.User(username="asos", full_name="Asoschi", role="founder",
                   password_hash=hash_password("x"), is_active=1))
db.commit()
db.close()

H = {"Authorization": "Bearer " + c.post(
    "/api/auth/login", json={"username": "asos", "password": "x"})
    .json()["access_token"]}

PAGES = {
    "Dashboard": "/api/dashboard",
    "O'quvchilar": "/api/students",
    "Guruhlar": "/api/groups",
    "Moliya umumiy": "/api/finance/overview",
    "Zararsizlik": "/api/finance/break-even",
    "Ustoz oyligi (kesim)": "/api/reports/teacher-salary-detail",
}


def measure():
    out = {}
    for label, url in PAGES.items():
        _N[0] = 0
        r = c.get(url, headers=H)
        out[label] = (_N[0], r.status_code, r.text)
    return out


print("=== 1. Kichik bazada o'lchov ===")
small = measure()
for k, (q, code, _) in small.items():
    print(f"    {k:24} {q:4} so'rov  (javob {code})")
    ck(f"{k} — javob 200", code, 200)

print("\n=== 2. Ma'lumot IKKI BARAVAR oshirildi ===")
build(60, 6, "b")
big = measure()

print("\n=== 3. So'rovlar soni ma'lumot bilan O'SMASLIGI kerak ===")
print(f"    {'SAHIFA':24} {'kichik':>7} {'katta':>7} {'farq':>6}")
for k in PAGES:
    q1 = small[k][0]
    q2 = big[k][0]
    print(f"    {k:24} {q1:7} {q2:7} {q2 - q1:+6}")
    # Ruxsat: 3 tagacha o'sish (chunk chegaralari, yangi filial va h.k.)
    ck(f"{k} — N+1 yo'q", q2 <= q1 + 3, True)

print("\n=== 4. Har sahifa mutlaq chegaradan oshmasin ===")
LIMITS = {
    "Dashboard": 25,
    "O'quvchilar": 20,
    "Guruhlar": 20,
    "Moliya umumiy": 45,
    "Zararsizlik": 25,
    "Ustoz oyligi (kesim)": 25,
}
for k, lim in LIMITS.items():
    ck(f"{k} <= {lim} so'rov", big[k][0] <= lim, True)

print("\n" + ("HAMMASI OK" if not fails
              else f"{len(fails)} ta XATO: {fails}"))
sys.exit(1 if fails else 0)
