"""DARS KO'CHIRISH RO'YXATI TEZLIGI (2026-08-23).

Jahongir: "Dashboard haliyam judayam tez ishlamayabdi".

Jonli o'lchov: /api/reschedules issiq holatda ham 2,5 soniya ketardi.
Sabab — har qator uchun uchta alohida so'rov (guruh, ustoz, qaror
qabul qilgan xodim). 200 qator = 600 so'rov.

Bu test so'rovlar SONINI sanaydi: qator ko'paysa ham so'rov soni
o'zgarmasligi kerak. Javob mazmuni ham avvalgidek qolgani
tekshiriladi — tezlashtirish ma'lumotni buzmasin.
"""
import os, sys

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_resch/db.sqlite"
os.makedirs("/tmp/verify_resch", exist_ok=True)
if os.path.exists("/tmp/verify_resch/db.sqlite"):
    os.remove("/tmp/verify_resch/db.sqlite")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import date, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import event
import main, models, roles
import entry  # noqa: F401
from database import SessionLocal, engine
from auth import hash_password

c = TestClient(main.app)
db = SessionLocal()
fails = []


def ck(n, g, w):
    ok = g == w
    print(("OK  " if ok else "XATO ") + f"{n}: {g}"
          + ("" if ok else f"   (kutilgan {w})"))
    if not ok:
        fails.append(n)


b = models.Branch(name="Zafar"); db.add(b); db.commit()
u = models.User(username="asos", full_name="Asoschi",
                password_hash=hash_password("Parol123!"),
                role=roles.FOUNDER, branch_id=b.id, is_active=1)
db.add(u); db.commit()

teachers, groups = [], []
for i in range(6):
    t = models.Teacher(full_name=f"Ustoz {i}", branch_id=b.id, is_active=1)
    db.add(t); teachers.append(t)
db.commit()
for i in range(6):
    g = models.Group(name=f"Guruh {i}", branch_id=b.id,
                     teacher_id=teachers[i].id)
    db.add(g); groups.append(g)
db.commit()

today = date.today()


def add_rows(n):
    for i in range(n):
        db.add(models.LessonReschedule(
            group_id=groups[i % 6].id, teacher_id=teachers[i % 6].id,
            from_date=today + timedelta(days=i % 20),
            to_date=today + timedelta(days=(i % 20) + 1),
            from_time="10:00", to_time="12:00",
            reason="teacher_sick", status="pending",
            requested_by=u.full_name))
    db.commit()


tok = c.post("/api/auth/login",
             json={"username": "asos", "password": "Parol123!"}
             ).json()["access_token"]
H = {"Authorization": f"Bearer {tok}"}

# --- so'rovlarni sanaymiz
counter = {"n": 0}


@event.listens_for(engine, "before_cursor_execute")
def _count(conn, cursor, statement, params, context, executemany):
    counter["n"] += 1


def measure():
    counter["n"] = 0
    r = c.get("/api/reschedules", headers=H)
    return r, counter["n"]


print("=== 1. 10 QATOR ===")
add_rows(10)
r10, q10 = measure()
ck("status 200", r10.status_code, 200)
ck("10 qator qaytdi", len(r10.json()["rows"]), 10)
print(f"     so'rovlar soni: {q10}")

print("\n=== 2. 100 QATOR ===")
add_rows(90)
r100, q100 = measure()
ck("100 qator qaytdi", len(r100.json()["rows"]), 100)
print(f"     so'rovlar soni: {q100}")

print("\n=== 3. QATOR 10x KO'PAYDI — SO'ROV KO'PAYMASIN ===")
ck("so'rov soni deyarli o'zgarmadi (<=2 farq)", (q100 - q10) <= 2, True)
ck("so'rov soni kichik (<15)", q100 < 15, True)

print("\n=== 4. MA'LUMOT BUZILMADI ===")
row = r100.json()["rows"][0]
for f in ("group", "teacher", "status_label", "reason_label", "from_date"):
    ck(f"'{f}' to'ldirilgan", bool(row.get(f)), True)
ck("guruh nomi to'g'ri", row["group"].startswith("Guruh"), True)
ck("ustoz nomi to'g'ri", row["teacher"].startswith("Ustoz"), True)
ck("kutilayotganlar sanoqda", r100.json()["pending"], 100)

print("\n" + ("HAMMASI O'TDI" if not fails else f"XATOLAR: {fails}"))
sys.exit(1 if fails else 0)
