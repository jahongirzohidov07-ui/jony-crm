"""LIDDAN SINOVGA VA FAOLLASHGANDA OYLIK YECHISH (2026-09-16).

Jahongir: "liddan o'quvchiga o'tkizganda sinov darsi bo'lib tushsin
administrator, qara 3ta darsga kelsa avtomat faol boladigan funksiya
borku shunda faol qilganingda faollashtirilgan kundan boshlab oylik
tolovni yechib olish kerak, bazi o'quvchilar faol bolsa ham pul
yechilmayabdi shuni togrla".

Tekshiriladi:
  1. Lid o'quvchiga aylansa — SINOV holatida, pul yechilmaydi;
  2. Sinov o'tgan oyda boshlanib, shu oy faollashsa — o'tgan oy
     qolgan darslari + shu oy to'liq yechiladi;
  3. Xavfsizlik to'ri: faol, lekin shu oy yechilmaganlardan yechiladi
     (shu oy qo'shilgan — qo'shilgan kundan), asoschi o'chirgani
     (ChargeSkip) va sinovdagilarga tegilmaydi, ikki marta yechilmaydi.
"""
import os
import sys
import tempfile
from datetime import date, timedelta

_DIR = os.path.join(tempfile.gettempdir(), "activation_charge_test")
os.makedirs(_DIR, exist_ok=True)
_DB = os.path.join(_DIR, "db.sqlite")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace(chr(92), "/")
if os.path.exists(_DB):
    os.remove(_DB)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles, billing                # noqa: E402
import entry                                       # noqa: E402
import common                                      # noqa: E402
from database import SessionLocal                  # noqa: E402
from auth import hash_password                     # noqa: E402

client = TestClient(main.app)
fails = []


def ck(name, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + name + f": {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


TODAY = roles.local_today()
first = TODAY.replace(day=1)
prev_end = first - timedelta(days=1)
PY, PM = prev_end.year, prev_end.month
NOW = f"{TODAY.year:04d}-{TODAY.month:02d}"
PREV = f"{PY:04d}-{PM:02d}"
PRICE = 40_000
_next = date(TODAY.year + (TODAY.month == 12), TODAY.month % 12 + 1, 1)
LAST = (_next - timedelta(days=1)).day

db = SessionLocal()
b = models.Branch(name="Bekobod 1"); db.add(b); db.commit()
BID = b.id
db.add(models.User(username="adm", password_hash=hash_password("x"),
                   full_name="Admin", role=roles.ADMINISTRATOR, branch_id=BID))
t = models.Teacher(full_name="Elena", is_active=1, branch_id=BID)
db.add(t); db.commit()
TID = t.id
g = models.Group(name="Step 1", branch_id=BID, teacher_id=TID,
                 lesson_price=PRICE, standard_lessons_per_month=12,
                 monthly_fee=480_000, lesson_days="")
db.add(g); db.commit()
GID = g.id
# O'tgan oy oxirida 2 ta dars (25, 27), shu oy toq kunlarda darslar
for d in (25, 27):
    if d <= prev_end.day:
        db.add(models.Lesson(group_id=GID, teacher_id=t.id, date=date(PY, PM, d)))
for d in range(1, LAST + 1, 2):
    db.add(models.Lesson(group_id=GID, teacher_id=t.id,
                         date=date(TODAY.year, TODAY.month, d)))
db.commit()


def student(name, status, enrolled):
    s = models.Student(full_name=name, branch_id=BID, status=status,
                       group_id=GID, enrolled_date=enrolled)
    db.add(s); db.commit()
    return s


def charges(sid, period=None):
    s = SessionLocal()
    q = s.query(models.Payment).filter(models.Payment.student_id == sid,
                                       models.Payment.kind == "charge")
    if period:
        q = q.filter(models.Payment.period == period)
    out = [round(-p.amount) for p in q.all()]
    s.close()
    return out


lead = models.Lead(full_name="Yangi Bola", phone="998901234567", source="visit",
                   stage="trial_scheduled", branch_id=BID)
db.add(lead); db.commit()
LID = lead.id
db.close()

H = {"Authorization": "Bearer " + client.post(
    "/api/auth/login", json={"username": "adm", "password": "x"}
).json()["access_token"]}

print("=== 1. Lid -> sinov darsi ===")
r = client.post(f"/api/leads/{LID}/convert", headers=H, json={"group_id": GID})
ck("aylantirildi", r.status_code, 200)
SID = r.json()["id"]
ck("holati SINOV", r.json()["status"], "trial")
ck("pul yechilmadi", charges(SID), [])

print("\n=== 2. O'tgan oyda boshlanib, shu oy faollashdi ===")
db = SessionLocal()
s2 = student("Oylar oralig'i", "trial", date(PY, PM, 25))
res = common._activate_student(db, s2, on=date(PY, PM, 25), reason="test")
db.commit()
S2 = s2.id
db.close()
ck("faol bo'ldi", res is not None, True)
prev_n = len([d for d in (25, 27) if d <= prev_end.day])
ck("o'tgan oy: qolgan darslari", charges(S2, PREV), [prev_n * PRICE] if prev_n else [])
ck("shu oy: to'liq oylik", charges(S2, NOW), [12 * PRICE])

print("\n=== 3. Xavfsizlik to'ri ===")
db = SessionLocal()
old = student("Eski faol", "active", date(PY, PM, 1))
new = student("Shu oy faol", "active", TODAY)
skip = student("O'chirilgan yechim", "active", date(PY, PM, 1))
paid = student("Yechilgan", "active", date(PY, PM, 1))
trial = student("Sinovdagi", "trial", date(PY, PM, 1))
db.add(models.ChargeSkip(student_id=skip.id, period=NOW, created_by="Asoschi"))
db.add(models.Payment(student_id=paid.id, amount=-480_000, kind="charge",
                      period=NOW, note="bor"))
db.commit()
common._seed_mark(db, f"mcf_{NOW}_g{GID}")
ids = dict(old=old.id, new=new.id, skip=skip.id, paid=paid.id, trial=trial.id)
done = entry._mc_charge_missed(db, TODAY)
left = (db.query(models.Lesson)
        .filter(models.Lesson.group_id == GID, models.Lesson.date >= TODAY,
                models.Lesson.date <= date(TODAY.year, TODAY.month, LAST))
        .count())
db.close()
ck("eski faol — to'liq oy", charges(ids["old"], NOW), [12 * PRICE])
ck("shu oy qo'shilgan — qo'shilgan kundan", charges(ids["new"], NOW),
   [min(left, 12) * PRICE] if left else [])
ck("asoschi o'chirgani qayta yozilmadi", charges(ids["skip"], NOW), [])
ck("yechilgan — ikkinchi marta yo'q", charges(ids["paid"], NOW), [480_000])
ck("sinovdagi — yechilmadi", charges(ids["trial"], NOW), [])
ck("lid-o'quvchi (sinov) — yechilmadi", charges(SID, NOW), [])
db = SessionLocal()
again = entry._mc_charge_missed(db, TODAY)
db.close()
ck("ikkinchi yurishda hech kim yo'q", again, [])
ck("birinchi yurishda nechta", len(done), 2 if left else 1)

print()
if fails:
    print(f"XATOLAR ({len(fails)}): " + ", ".join(fails))
    sys.exit(1)
print("HAMMASI O'TDI")
