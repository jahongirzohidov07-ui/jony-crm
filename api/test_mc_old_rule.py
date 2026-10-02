"""OY BOSHIDA CHALA YECHILGAN OYLIK (2026-10-02).

Jahongir: "58 ta o'quvchi 40 ta qarzdor ... har oy boshida faol
o'quvchilardan pul yechilishi kerak edi avtomat. Ba'zilaridan yechilgan,
ba'zilaridan esa bitta darsga yechilgan".

Sabab: 27-sentabrdagi bo'linishdan keyin login (auth_users.py) yangi
oylik qoidasiga ulanmay qolgan — 1-oktabrdagi birinchi kirish ESKI
"faqat o'tilgan darslar" qoidasi bilan 1 dars uchun yechdi, yangi qoida
esa "shu oy yechimi bor" deb ularni o'tkazib yubordi.

Tekshiriladi:
  1. Login yo'li ham yangi qoidaga ulangan: 1 dars o'tilgan guruhda
     ham login to'liq standart oyni yechadi (eski kodda — 1 dars).
  2. Eski qoida yozib qo'ygan qatorlar to'liq oylikka ko'tariladi
     (chegirmasi bo'lsa chegirma bilan), qator o'chirilmaydi, audit
     yoziladi.
  3. Boshqa guruh nomidagi qator va qo'lda kiritilgan qatorga
     tegilmaydi; ikkinchi yurish hech narsa o'zgartirmaydi.
"""
import os
import sys
import tempfile
from datetime import date, timedelta

_DIR = os.path.join(tempfile.gettempdir(), "mc_old_rule_test")
os.makedirs(_DIR, exist_ok=True)
_DB = os.path.join(_DIR, "db.sqlite")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace(chr(92), "/")
if os.path.exists(_DB):
    os.remove(_DB)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                         # noqa: E402
import entry                                       # noqa: E402
import auth_users                                  # noqa: E402
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
NOW = f"{TODAY.year:04d}-{TODAY.month:02d}"
PRICE = 40_000
FULL = 12 * PRICE
_next = date(TODAY.year + (TODAY.month == 12), TODAY.month % 12 + 1, 1)
LAST = (_next - timedelta(days=1)).day

db = SessionLocal()
b = models.Branch(name="Zafar"); db.add(b); db.commit()
BID = b.id
db.add(models.User(username="adm", password_hash=hash_password("x"),
                   full_name="Admin", role=roles.ADMINISTRATOR, branch_id=BID))
t = models.Teacher(full_name="Ustoz", is_active=1, branch_id=BID)
db.add(t); db.commit()
g = models.Group(name="IELTS 3.0", branch_id=BID, teacher_id=t.id,
                 lesson_price=PRICE, standard_lessons_per_month=12,
                 monthly_fee=FULL, lesson_days="")
db.add(g); db.commit()
GID = g.id
lessons = {}
for d in range(1, LAST + 1, 2):
    ls = models.Lesson(group_id=GID, teacher_id=t.id, held=0,
                       date=date(TODAY.year, TODAY.month, d))
    db.add(ls); db.commit()
    lessons[d] = ls


def student(name, enrolled):
    s = models.Student(full_name=name, branch_id=BID, status="active",
                       group_id=GID, enrolled_date=enrolled)
    db.add(s); db.commit()
    return s


OLD = date(TODAY.year - 1, 9, 5)
a = student("Oddiy faol", OLD)
bb = student("Eski qoida 1 dars", OLD)
JOIN = TODAY.replace(day=1)
c = student("Shu oy qo'shilgan", JOIN)
d_ = student("Boshqa guruh qatori", OLD)
e = student("Qo'lda kiritilgan", OLD)

# 1-kungi dars o'tilgan (yo'qlama bor) — eski qoida aynan shu darsni
# yechardi
lessons[1].held = 1
for s in (a, bb, c, d_, e):
    db.add(models.Attendance(lesson_id=lessons[1].id, student_id=s.id,
                             present=1))
db.commit()


def old_row(sid, gname=g.name, by=entry._MC_BY):
    db.add(models.Payment(
        student_id=sid, amount=-PRICE, kind="charge",
        note=f"{gname} - {NOW} oyi uchun 1 dars (avtomat)",
        created_by=by, period=NOW))
    db.commit()


old_row(bb.id)
old_row(c.id)
old_row(d_.id, gname="Boshqa guruh")
old_row(e.id, by="Admin")
IDS = dict(a=a.id, b=bb.id, c=c.id, d=d_.id, e=e.id)
# Oilaviy/individual chegirma — 10%
db.add(models.Discount(student_id=c.id, kind="individual", percent=10, reason="test",
                       status="active"))
db.commit()
C_WANT = round(FULL * 0.9)
db.close()


def charges(sid):
    s = SessionLocal()
    out = [round(-p.amount) for p in s.query(models.Payment).filter(
        models.Payment.student_id == sid, models.Payment.kind == "charge",
        models.Payment.period == NOW).all()]
    s.close()
    return out


print("=== 1. Login yo'li yangi qoidaga ulangan ===")
ck("auth_users dagi funksiya almashtirilgan",
   bool(getattr(auth_users._ensure_month_charges, "_bud_new", False)), True)
r = client.post("/api/auth/login", json={"username": "adm", "password": "x"})
ck("login", r.status_code, 200)
ck("1 dars o'tilgan guruhda ham to'liq oy yechildi", charges(IDS["a"]),
   [FULL])

print("\n=== 2. Eski qoida qatorlari to'g'rilandi ===")
ck("eski qoida 1 dars -> standart oy", charges(IDS["b"]), [FULL])
ck("chegirmali -> to'liq oylik minus 10%", charges(IDS["c"]), [C_WANT])
s = SessionLocal()
p = s.query(models.Payment).filter(
    models.Payment.student_id == IDS["b"],
    models.Payment.kind == "charge").one()
ck("izohda belgi", entry._MC_OLD_FIX in (p.note or ""), True)
ck("audit yozildi", s.query(models.AuditLog).filter(
    models.AuditLog.entity == "payment",
    models.AuditLog.entity_id == p.id,
    models.AuditLog.action == "update").count(), 1)
s.close()

print("\n=== 3. Tegilmaydiganlar va takror yurish ===")
ck("boshqa guruh qatori o'zgarmadi", charges(IDS["d"]), [PRICE])
ck("qo'lda kiritilgan o'zgarmadi", charges(IDS["e"]), [PRICE])
s = SessionLocal()
ck("ikkinchi yurish bo'sh", entry._mc_fix_old_rule(s, TODAY), [])
s.close()
ck("summa o'zgarmadi", charges(IDS["b"]), [FULL])

print()
if fails:
    print(f"{len(fails)} ta XATO: {fails}")
    sys.exit(1)
print("HAMMASI OK")
