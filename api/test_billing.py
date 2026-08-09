"""billing.py: grade_rates()/grade_on() - toraytirilgan except va
error_logs'ga yozish (2026-08 mustahkamlash).

Diqqat: bu test TestClient/HTTP orqali emas, to'g'ridan-to'g'ri
billing modulini chaqiradi - chunki maqsad DB xatosi yuz berganda
sodir bo'ladigan ICHKI xatti-harakatni (rollback, ErrorLog yozuvi,
sessiya tozaligi) tekshirish, bu HTTP qatlamidan ko'rinmaydi."""
import os, sys
from datetime import date

os.environ["DATABASE_URL"] = "sqlite:////tmp/billing_test.db"
if os.path.exists("/tmp/billing_test.db"):
    os.remove("/tmp/billing_test.db")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.exc import SQLAlchemyError

import main  # noqa: F401 - jadvallarni yaratish (create_all) uchun import qilinadi
import billing, models
from database import SessionLocal

fails = []


def ck(name, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + name + f": {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


db = SessionLocal()

# roles.TEACHER_GRADES asosida "main" import qilinganda haqiqiy
# darajalar (junior, middle, ...) allaqachon urug'langan (common.py)
# - shu bilan to'qnashmasligi uchun sinov darajasi ALOHIDA, noyob
# kalit bilan qo'shiladi.
t1 = models.Teacher(full_name="Ustoz Bir")
db.add(t1)
db.add(models.TeacherGrade(key="__test_grade__", label="Sinov",
                           order_no=999, rate_per_student=80000))
db.commit()
TID = t1.id

print("=== 1. ODDIY HOLAT (xatosiz) ===")
rates = billing.grade_rates(db)
ck("grade_rates oddiy holatda ishlaydi (o'z + urug'langan darajalar)",
   rates.get("__test_grade__"), 80000)
ck("grade_on teacher_id=None uchun None qaytaradi",
   billing.grade_on(db, None, date.today()), None)
ck("grade_on tarix bo'lmasa hozirgi darajani qaytaradi",
   billing.grade_on(db, TID, date.today()), t1.grade)
ck("hech qanday xato yozilmagan", db.query(models.ErrorLog).count(), 0)


print("\n=== 2. MAJBURIY DB XATOSI - grade_rates() ===")


class _BrokenQuery:
    """db.query(X) o'rniga qaytariladigan soxta obyekt - undagi har
    qanday metod chaqiruvi (.all(), .filter(), ...) SQLAlchemyError
    otadi, xuddi haqiqiy DB xatosi kabi."""
    def __getattr__(self, name):
        def _raise(*a, **kw):
            raise SQLAlchemyError("sun'iy ravishda yaratilgan DB xatosi")
        return _raise


_orig_query = db.query
db.query = lambda model, *a, **kw: (
    _BrokenQuery() if model is models.TeacherGrade
    else _orig_query(model, *a, **kw)
)

result = billing.grade_rates(db)
ck("grade_rates xato paytida bo'sh {} qaytaradi", result, {})

db.query = _orig_query
ck("xato error_logs'ga yozilgan", db.query(models.ErrorLog).count(), 1)
row = db.query(models.ErrorLog).first()
ck("xato manzili to'g'ri qayd etilgan", row.path, "billing.grade_rates")
ck("sessiya rollback'dan keyin ham ishlatilsa bo'ladi (asosiy tekshiruv)",
   db.query(models.Teacher).count(), 1)


print("\n=== 3. MAJBURIY DB XATOSI - grade_on() (zaxira yo'l ham ishlashi kerak) ===")

db.query = lambda model, *a, **kw: (
    _BrokenQuery() if model is models.TeacherGradeEvent
    else _orig_query(model, *a, **kw)
)

g = billing.grade_on(db, TID, date.today())
db.query = _orig_query
ck("grade_on DB xatosidan keyin ham zaxira (hozirgi daraja) qaytaradi",
   g, t1.grade)
ck("ikkinchi xato ham error_logs'ga qo'shilgan (jami 2 ta)",
   db.query(models.ErrorLog).count(), 2)
last = db.query(models.ErrorLog).order_by(models.ErrorLog.id.desc()).first()
ck("ikkinchi xato manzili to'g'ri", last.path, "billing.grade_on")

db.close()

print()
if fails:
    print(f"XATOLAR ({len(fails)}): " + ", ".join(fails))
    sys.exit(1)
print("HAMMASI O'TDI")
