"""Oy o'rtasida guruh almashsa — hisob qayta bo'linadi (2026-08-13).

Jahongir: "narxi boshqa guruhga oy o'rtasida ko'chsa, o'sha oyning
hisobi eski narxda qolib ketardi... shuni ham avtomat qil"."""
import os, sys
from datetime import date, timedelta

os.environ["DATABASE_URL"] = "sqlite:////tmp/move_recharge.db"
if os.path.exists("/tmp/move_recharge.db"):
    os.remove("/tmp/move_recharge.db")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
import main, models, roles, billing
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


TODAY = roles.local_today()
Y, M = TODAY.year, TODAY.month
START, END = billing.month_bounds(Y, M)
PERIOD = f"{Y:04d}-{M:02d}"

db = SessionLocal()
b = models.Branch(name="Bekobod 1"); db.add(b); db.commit()
t = models.Teacher(full_name="Ustoz", branch_id=b.id, is_active=1)
db.add(t); db.commit()
# Eski guruh: dars 40 000, yangi guruh: 30 000
g1 = models.Group(name="Qimmat guruh", branch_id=b.id, teacher_id=t.id,
                  monthly_fee=480000, lesson_price=40000,
                  standard_lessons_per_month=12)
g2 = models.Group(name="Arzon guruh", branch_id=b.id, teacher_id=t.id,
                  monthly_fee=360000, lesson_price=30000,
                  standard_lessons_per_month=12)
db.add_all([g1, g2]); db.commit()
G1, G2, BID = g1.id, g2.id, b.id
st = models.Student(full_name="Ko'chuvchi O'quvchi", branch_id=b.id,
                    group_id=G1, status="active")
db.add(st); db.commit()
SID = st.id

# Oy boshidan bugungacha 4 ta dars (eski guruh), bugundan keyin 6 ta
# (yangi guruh) — sanalar oy ichida bo'lishi uchun bugundan orqaga
# va oldinga tarqatamiz.
old_days = [TODAY - timedelta(days=d) for d in (7, 5, 3, 1)]
old_days = [d for d in old_days if d >= START]
new_days = [TODAY + timedelta(days=d) for d in (0, 2, 4, 6, 8, 10)]
new_days = [d for d in new_days if d <= END]
for d in old_days:
    db.add(models.Lesson(group_id=G1, teacher_id=t.id, date=d, held=1))
for d in new_days:
    db.add(models.Lesson(group_id=G2, teacher_id=t.id, date=d, held=0))
# Shu oy uchun hisob allaqachon yozilgan: 12 dars x 40 000
db.add(models.Payment(student_id=SID, amount=-480000, kind="charge",
                      period=PERIOD, note="Qimmat guruh — 12 dars",
                      created_by="Avtomat"))
db.add(models.User(username="asos", full_name="Asoschi", role="founder",
                   password_hash=hash_password("x"), is_active=1))
db.commit(); db.close()

H = {"Authorization": "Bearer " + c.post(
    "/api/auth/login", json={"username": "asos", "password": "x"}
).json()["access_token"]}

print(f"=== Oy boshidan bugungacha {len(old_days)} dars (eski, 40 000), "
      f"bugundan keyin {len(new_days)} dars (yangi, 30 000) ===")

print("\n=== 1. Ko'chirishdan oldingi balans ===")
before = c.get(f"/api/students/{SID}", headers=H).json()["balance"]
ck("balans -480 000", before, -480000)

print("\n=== 2. Boshqa guruhga o'tkazamiz ===")
r = c.post(f"/api/students/{SID}/move-group?force=true", headers=H,
           json={"group_id": G2})
ck("o'tkazildi", r.status_code, 200)
rc = r.json().get("recharge")
ck("hisob qayta hisoblandi", bool(rc), True)
ck("eski guruh darslari", rc["old_lessons"] if rc else 0, len(old_days))
ck("yangi guruh darslari", rc["new_lessons"] if rc else 0, len(new_days))
kutilgan = len(old_days) * 40000 + len(new_days) * 30000
ck("yangi summa to'g'ri", rc["new"] if rc else 0, kutilgan)
ck("eski summa saqlandi", rc["old"] if rc else 0, 480000)

print("\n=== 3. Balans ham o'zgardi ===")
after = c.get(f"/api/students/{SID}", headers=H).json()["balance"]
ck("balans yangi summaga teng", after, -kutilgan)

print("\n=== 4. Bitta oyga bitta hisob qatori qoldi ===")
db = SessionLocal()
rows = db.query(models.Payment).filter(
    models.Payment.student_id == SID,
    models.Payment.kind == "charge",
    models.Payment.period == PERIOD).all()
note = rows[0].note if rows else ""
db.close()
ck("bitta qator", len(rows), 1)
# Dars soni SANAGA bog'liq: oy oxirida rejadagi kunlarning bir qismi
# keyingi oyga tushadi. Shuning uchun qo'lda "6 dars" deb yozib
# bo'lmaydi — tepada hisoblangan ro'yxat uzunligi olinadi (2026-09-23).
ck("izohda eski guruh va summasi",
   f"Qimmat guruh: {len(old_days)} dars" in note, True)
ck("izohda yangi guruh va summasi",
   f"Arzon guruh: {len(new_days)} dars" in note, True)
print("   izoh:", note)
ck("izohda darslar soni", f"[dars:{len(old_days)+len(new_days)}]" in note, True)

print("\n=== 5. Auditda eski summa qoldi ===")
db = SessionLocal()
al = [a for a in db.query(models.AuditLog).all()
      if a.action == "lessons_recount"]
db.close()
ck("audit yozuvi bor", len(al) >= 1, True)
ck("eski summa auditda", "480 000" in (al[0].old_value or ""), True)

print("\n=== 6. Hisob yozilmagan bo'lsa — tegilmaydi ===")
db = SessionLocal()
st2 = models.Student(full_name="Hisobsiz O'quvchi", branch_id=BID,
                     group_id=G1, status="active")
db.add(st2); db.commit()
S2 = st2.id
db.close()
r6 = c.post(f"/api/students/{S2}/move-group?force=true", headers=H,
            json={"group_id": G2})
ck("o'tkazildi", r6.status_code, 200)
ck("qayta hisob yo'q", r6.json().get("recharge"), None)

print()
if fails:
    print(f"XATOLAR ({len(fails)}): " + ", ".join(fails))
    sys.exit(1)
print("HAMMASI O'TDI")
