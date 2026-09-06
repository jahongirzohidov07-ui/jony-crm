# -*- coding: utf-8 -*-
"""KUNLIK AVTOMAT ISHLAR (2026-09-06, "togrla hamma aytganingni").

Auditda topilgani: bir necha muhim qoida faqat "kimdir sahifani
ochganda" ishlardi —
  · ustoz darajasi qoidalari (_apply_grade_rules) — Karyera sahifasi;
  · chegirma muddati (_expire_discounts) — o'quvchilar ro'yxati;
  · ketish xavfi (_risk_scan) — dashboard;
  · osilib qolgan support biriktirishlari — server qayta ishga
    tushganda.
Endi ular kunlik cron'da ham yuradi.

Ikkinchi xato: _risk_scan vazifani eski "administrator" roliga
berardi; 3-sentabrda hamma admin sales_manager ga o'tkazilgan edi —
bayroq qo'yilardi, VAZIFA HECH KIMGA tushmasdi.
"""
import os
import sys

os.environ["DATABASE_URL"] = "sqlite:////tmp/cron_daily.db"
if os.path.exists("/tmp/cron_daily.db"):
    os.remove("/tmp/cron_daily.db")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import date, timedelta                 # noqa: E402
from fastapi.testclient import TestClient            # noqa: E402
import main, models, roles                           # noqa: E402
import entry                                         # noqa: E402,F401
import common                                        # noqa: E402
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


db = SessionLocal()
TODAY = roles.local_today()
b = models.Branch(name="Zafar"); db.add(b); db.commit()
asos = models.User(username="asos", password_hash=hash_password("x"),
                   full_name="Asoschi", role=roles.FOUNDER)
adm = models.User(username="adm", password_hash=hash_password("x"),
                  full_name="Zafar admin", role=roles.SALES_MANAGER,
                  branch_id=b.id)
db.add_all([asos, adm]); db.commit()
g = models.Group(name="Step 1", branch_id=b.id, lesson_price=45_000,
                 standard_lessons_per_month=12, monthly_fee=540_000)
db.add(g); db.commit()

# Qarzdor o'quvchi — xavf skaneri uni topishi kerak
s = models.Student(full_name="Qarzdor bola", branch_id=b.id, status="active",
                   group_id=g.id, enrolled_date=date(2026, 6, 1))
db.add(s); db.commit()
db.add(models.Payment(student_id=s.id, amount=-900_000, kind="charge",
                      period="2026-08", created_by="test"))
# Muddati tugagan chegirma
d = models.Discount(student_id=s.id, kind="individual", percent=20,
                    status="active", reason="test",
                    end_date=TODAY - timedelta(days=3))
db.add(d); db.commit()
D_ID = d.id

print("=== 1. Xavf skaneri vazifani ADMINGA beradi ===")
made = common._risk_scan(db)
ck("bayroq/vazifa yaratildi", made > 0, True)
flags = db.query(models.RiskFlag).filter(models.RiskFlag.active == 1).count()
ck("RiskFlag qo'yildi", flags > 0, True)
tasks = (db.query(models.Task)
         .filter(models.Task.assignee_id == adm.id).all())
ck("sales_manager adminga vazifa tushdi", len(tasks) > 0, True)
if tasks:
    print("   vazifa:", tasks[0].title[:70])

print("\n=== 2. Kunlik cron hamma qoidani yurgizadi ===")
# risk_scan bugungi belgisi bor — tozalaymiz, cron o'zi yurgizsin
key = f"risk_scan_{TODAY.isoformat()}"
db.query(models.SeedMark).filter(models.SeedMark.key == key).delete()
db.commit()
if getattr(common, "_SEED_KEYS", None) is not None:
    common._SEED_KEYS.discard(key)
db.query(models.RiskFlag).delete()
db.query(models.Task).delete()
db.commit()

r = client.get("/api/cron/daily", headers={"user-agent": "vercel-cron/1.0"})
ck("cron 200", r.status_code, 200)
db.expire_all()
ck("chegirma muddati tugadi — to'xtatildi",
   db.query(models.Discount).get(D_ID).status, "expired")
ck("xavf skaneri cron'da ishladi",
   db.query(models.RiskFlag).filter(models.RiskFlag.active == 1).count() > 0,
   True)
ck("vazifa yana adminga tushdi",
   db.query(models.Task).filter(models.Task.assignee_id == adm.id).count() > 0,
   True)
ck("cron ikkinchi marta ham xatosiz",
   client.get("/api/cron/daily",
              headers={"user-agent": "vercel-cron/1.0"}).status_code, 200)

print("\n=== 3. Daraja qoidalari cron ro'yxatida ===")
import inspect                                        # noqa: E402
import system                                         # noqa: E402
src = inspect.getsource(system.cron_daily)
for nom in ("grade_rules", "expire_discounts", "risk_scan", "stale_support"):
    ck(f"cron: {nom}", nom in src, True)

print()
print("XATOLAR:", fails if fails else "yo'q")
sys.exit(1 if fails else 0)
