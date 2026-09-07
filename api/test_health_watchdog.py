# -*- coding: utf-8 -*-
"""BAZA QOROVULI + support soati 500 xatosi (2026-09-06).

Jahongir: "har 2 kunda bir vercel o'chib qolyabdi nima qilish kerak".

1. /api/health endi bazani ham tekshiradi ("db": "ok") — cron har
   5 daqiqada chaqiradi, uzilish izsiz o'tmaydi. Baza javob bermasa:
   ErrorLog ga yozuv + asoschiga Telegram.
2. Support seansini saqlashda 500 xatosi: entry.py created_by ustuniga
   ISM yozardi, ustun esa INTEGER (users.id) — Postgres har safar rad
   etardi (jonli xato jurnalida 12 marta, 8 xodimda).
"""
import os
import sys

os.environ["DATABASE_URL"] = "sqlite:////tmp/health_wd.db"
if os.path.exists("/tmp/health_wd.db"):
    os.remove("/tmp/health_wd.db")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import date, timedelta                  # noqa: E402
from fastapi.testclient import TestClient             # noqa: E402
import main, models, roles                            # noqa: E402
import entry                                          # noqa: E402,F401
import system                                         # noqa: E402
from database import SessionLocal                     # noqa: E402
from auth import hash_password                        # noqa: E402

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
su = models.User(username="sup", password_hash=hash_password("x"),
                 full_name="Abduhakimova Shaxnoza", role=roles.SUPPORT_TEACHER,
                 branch_id=b.id)
db.add(su); db.commit()
t = models.Teacher(full_name="Abduhakimova Shaxnoza", is_active=1,
                   branch_id=b.id, user_id=su.id)
db.add(t); db.commit()
g = models.Group(name="Nur", branch_id=b.id, lesson_price=45_000,
                 standard_lessons_per_month=12, monthly_fee=540_000,
                 lesson_time="09:00-10:30")
db.add(g); db.commit()
db.add(models.SupportAssignment(user_id=su.id, group_id=g.id))
db.commit()

print("=== 1. Baza qorovuli ===")
r = client.get("/api/health")
ck("health 200", r.status_code, 200)
d = r.json()
ck("bazani tekshiradi", d.get("db"), "ok")
ck("holat ok", d.get("status"), "ok")
ck("javob vaqti o'lchanadi", isinstance(d.get("ms"), int), True)

print("\n=== 2. Baza yiqilsa — iz qoladi ===")
before = db.query(models.ErrorLog).count()
system._health_alarm(db, RuntimeError("connection refused (test)"))
db.expire_all()
rows = db.query(models.ErrorLog).all()
ck("ErrorLog yozuvi qo'shildi", len(rows) - before, 1)
ck("manzil /api/health", rows[-1].path, "/api/health")
ck("sabab saqlangan", "connection refused" in (rows[-1].detail or ""), True)

print("\n=== 3. Support soati saqlanadi (500 emas) ===")
today = roles.local_today()
r = client.post("/api/me/support-sessions",
                json={"group_id": g.id, "date": today.isoformat(),
                      "start_time": "15:40", "hours": 1,
                      "students_count": 2},
                headers=tok("sup"))
ck("seans saqlandi", r.status_code, 200)
row = db.query(models.SupportSession).first()
ck("yozuv bazada", row is not None, True)
if row is not None:
    ck("created_by — SON (users.id)", row.created_by, su.id)
    ck("filial biriktirildi", row.branch_id, b.id)

print()
print("XATOLAR:", fails if fails else "yo'q")
sys.exit(1 if fails else 0)
