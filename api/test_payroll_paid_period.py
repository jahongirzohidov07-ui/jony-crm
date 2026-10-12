"""OYLIK QAYSI OYGA YOZILADI (2026-10-12).

Jahongir: "men sentabr oyligi qilib bersam sentabr emas oktabr
oyligida o'zgarish bo'lyabdi, to'langan bo'p qolyabdi".

To'lovda period="2026-09" yoziladi, hisobot esa pulni BERILGAN SANA
bo'yicha yig'ardi. Tekshiriladi: 12-oktabrda berilgan sentabr oyligi
sentabrda "to'langan", oktabrda emas; oyi yozilmagan eski yozuv sana
bo'yicha; xotiradagi (ctx) va SQL yo'li bir xil natija beradi.
"""
import os
import sys
import tempfile
from datetime import date

_DIR = os.path.join(tempfile.gettempdir(), "payroll_paid_period_test")
os.makedirs(_DIR, exist_ok=True)
_DB = os.path.join(_DIR, "db.sqlite")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace(chr(92), "/")
if os.path.exists(_DB):
    os.remove(_DB)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import main, models, billing, common              # noqa: E402,F401
from database import SessionLocal                  # noqa: E402

fails = []


def ck(n, g, w):
    ok = g == w
    print(("OK  " if ok else "XATO ") + n + f": {g}"
          + ("" if ok else f" (kutilgan {w})"))
    if not ok:
        fails.append(n)


db = SessionLocal()
b = models.Branch(name="Bekobod 2"); db.add(b); db.commit()
t = models.Teacher(full_name="Sardor Mirfozilov", branch_id=b.id,
                   is_active=1); db.add(t); db.commit()
TID = t.id
db.add_all([
    # Sentabr oyligi — 12-oktabrda berilgan
    models.TeacherPayment(teacher_id=TID, amount=1_890_000, kind="salary",
                          period="2026-09", paid_on=date(2026, 10, 12)),
    # Oktabr avansi — oktabrda berilgan
    models.TeacherPayment(teacher_id=TID, amount=300_000, kind="advance",
                          period="2026-10", paid_on=date(2026, 10, 20)),
    # Eski yozuv: oyi yozilmagan — sana bo'yicha (sentabr)
    models.TeacherPayment(teacher_id=TID, amount=100_000, kind="salary",
                          period=None, paid_on=date(2026, 9, 25)),
])
db.commit()

S9, E9 = billing.month_bounds(2026, 9)
S10, E10 = billing.month_bounds(2026, 10)


def paid(s, e, per, use_ctx):
    ctx = None
    if use_ctx:
        ctx = billing.PayrollContext(db)
        ctx.prefetch([TID])
    return common._teacher_paid(db, TID, since=s, until=e, ctx=ctx,
                                period=per)


for use_ctx in (False, True):
    tag = "ctx" if use_ctx else "sql"
    ck(f"[{tag}] sentabr to'langan", paid(S9, E9, "2026-09", use_ctx),
       1_990_000.0)
    ck(f"[{tag}] oktabr to'langan", paid(S10, E10, "2026-10", use_ctx),
       300_000.0)

# period berilmasa — eski xulq (sana bo'yicha) o'zgarmaydi
ck("periodsiz sentabr (eski xulq)",
   common._teacher_paid(db, TID, since=S9, until=E9), 100_000.0)
ck("periodsiz oktabr (eski xulq)",
   common._teacher_paid(db, TID, since=S10, until=E10), 2_190_000.0)
ck("umumiy jami o'zgarmaydi", common._teacher_paid(db, TID), 2_290_000.0)
db.close()

print()
print("XATOLAR:", fails if fails else "yo'q")
sys.exit(1 if fails else 0)
