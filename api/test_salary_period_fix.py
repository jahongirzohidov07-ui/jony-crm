"""OYLIK QAYSI OY UCHUN (2026-10-03).

Jahongir: "sentabr oyinikini oktabrda berilsa ham sentabrniki bo'lib
yozilsin"; examiner — "imtihon olmasa 0 tursin, kam olsa 400 bo'ladi".

Tekshiriladi:
  1. Standart oy: 1–15 kunlari oylik o'tgan oyniki, 16+ — shu oy;
     avans doim shu oyniki.
  2. Bir martalik tuzatish: 1–15 oktabrda berilgan ustoz, examiner va
     xodim oyliklari (avans emas) sentabrniki bo'ladi; 20-oktabrdagi,
     avans va qo'lda boshqa oy tanlanganiga tegilmaydi; ikkinchi
     yurishda hech narsa qilmaydi.
  3. Examiner: imtihonsiz oy — 0.
"""
import os
import sys
import tempfile
from datetime import date

_DIR = os.path.join(tempfile.gettempdir(), "salary_period_fix_test")
os.makedirs(_DIR, exist_ok=True)
_DB = os.path.join(_DIR, "db.sqlite")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace(chr(92), "/")
if os.path.exists(_DB):
    os.remove(_DB)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import main, models, roles                         # noqa: E402,F401
import entry                                       # noqa: E402
import common                                      # noqa: E402
from database import SessionLocal                  # noqa: E402

fails = []


def ck(name, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + name + f": {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


print("=== 1. Standart oy ===")
ck("5-oktabr oylik", roles.default_pay_period(date(2026, 10, 5)), "2026-09")
ck("15-oktabr oylik", roles.default_pay_period(date(2026, 10, 15)), "2026-09")
ck("16-oktabr oylik", roles.default_pay_period(date(2026, 10, 16)), "2026-10")
ck("5-oktabr avans", roles.default_pay_period(date(2026, 10, 5), "advance"),
   "2026-10")
ck("yanvar boshi", roles.default_pay_period(date(2027, 1, 3)), "2026-12")

print("\n=== 2. Bir martalik tuzatish ===")
db = SessionLocal()
b = models.Branch(name="Zafar"); db.add(b); db.commit()
t = models.Teacher(full_name="Ust", branch_id=b.id, is_active=1)
u = models.User(username="hr", full_name="Hr", role=roles.HR_MANAGER,
                password_hash="x", is_active=1)
ex = models.User(username="ex", full_name="Ex", role=roles.EXAMINER,
                 password_hash="x", is_active=1, branch_id=b.id)
db.add_all([t, u, ex]); db.commit()


def tp(day, kind="salary", period="2026-10"):
    p = models.TeacherPayment(teacher_id=t.id, amount=1, kind=kind,
                              period=period, paid_on=date(2026, 10, day))
    db.add(p); db.commit()
    return p.id


T5, T20, TA, TM = tp(5), tp(20), tp(7, "advance"), tp(6, period="2026-08")
s5 = models.StaffSalaryPayment(user_id=ex.id, amount=1, kind="salary",
                               period="2026-10", paid_on=date(2026, 10, 2))
e5 = models.Expense(date=date(2026, 10, 3), category="admin_salary", amount=1,
                    staff_user_id=u.id)
e9 = models.Expense(date=date(2026, 10, 3), category="rent", amount=1)
db.add_all([s5, e5, e9]); db.commit()
S5, E5, E9 = s5.id, e5.id, e9.id
n = entry._salary_period_fix(db, date(2026, 10, 1), date(2026, 10, 15),
                             "2026-09")
ck("o'zgargan yozuvlar", n, 3)


def per(model, i):
    return db.query(model).get(i).period


ck("ustoz 5-okt -> sentabr", per(models.TeacherPayment, T5), "2026-09")
ck("ustoz 20-okt joyida", per(models.TeacherPayment, T20), "2026-10")
ck("avans joyida", per(models.TeacherPayment, TA), "2026-10")
ck("qo'lda avgust tanlangani joyida", per(models.TeacherPayment, TM),
   "2026-08")
ck("examiner -> sentabr", per(models.StaffSalaryPayment, S5), "2026-09")
ck("xodim xarajati -> sentabr", per(models.Expense, E5), "2026-09")
ck("ijaraga tegilmadi", per(models.Expense, E9), None)

key = "salary_period_fix_2026-10"
entry._mc_ensure(db)
ck("bir martalik belgi qo'yildi", bool(common._seed_done(db, key)), True)
T6 = tp(6)
entry._mc_ensure(db)
ck("ikkinchi yurishda tegmaydi", per(models.TeacherPayment, T6), "2026-10")

print("\n=== 3. Examiner imtihonsiz ===")
d = common._examiner_month(db, ex.id, 2026, 9)
ck("imtihonsiz oy — 0", (d["exam_count"], d["salary"]), (0, 0))
db.close()

print()
if fails:
    print(f"{len(fails)} ta XATO: {fails}")
    sys.exit(1)
print("HAMMASI OK")
