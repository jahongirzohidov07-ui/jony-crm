"""Ota-ona portali: to'lovlar tarixi, coin/XP, o'zlashtirish va test
natijalari (2026-08-09).

Muammo (Jahongir so'radi): ota-ona sahifasida faqat davomat va jami
balans ko'rinardi. Endi: to'lovlar tarixi (har bir harakat),
coin/XP gamifikatsiya kartasi, kundalik baholar (o'zlashtirish) va
test natijalari ham qo'shildi.

MUHIM: bu tekshiruv `import entry` qiladi va HAQIQIY jonli yo'lga
(GET /api/parent/{token}, entry.py'dagi mustaqil nusxa) so'rov
yuboradi — parents.py'dagi bir xil nomli funksiya HECH QACHON
ishlamaydi (entry.py o'z ustidan butunlay mustaqil yozib, _drop_route
orqali almashtiradi), shuning uchun faqat parents.py'ni tekshirish
soxta ijobiy natija bergan bo'lardi."""
import os, sys
from datetime import date

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_parent2/parent_extras_test.db"
if os.path.exists("/tmp/verify_parent2/parent_extras_test.db"):
    os.remove("/tmp/verify_parent2/parent_extras_test.db")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
import main, models
import entry  # noqa: F401 - haqiqiy jonli yo'lni ro'yxatdan o'tkazadi
from database import SessionLocal
from auth import hash_password

client = TestClient(main.app)
fails = []


def ck(name, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + name + f": {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


db = SessionLocal()
b = models.Branch(name="Zafar")
db.add(b)
db.commit()

user_t = models.User(username="ust1", full_name="Ustoz Anvar",
                     password_hash=hash_password("x"), role="teacher",
                     branch_id=b.id, is_active=1)
db.add(user_t)
db.commit()

teacher = models.Teacher(full_name="Ustoz Anvar", branch_id=b.id,
                         user_id=user_t.id, is_active=1)
db.add(teacher)
db.commit()

g = models.Group(name="IELTS-5", subject="english", level="B2",
                 branch_id=b.id, teacher_id=teacher.id,
                 lesson_time="18:00", monthly_fee=500000,
                 lesson_days="135", capacity=15)
db.add(g)
db.commit()

s = models.Student(full_name="Aziz Karimov", branch_id=b.id, group_id=g.id,
                   status="active", enrolled_date=date.today(),
                   parent_token="abcdefghijklmnop1234",
                   public_id="STU-000001")
db.add(s)
db.commit()

today = date.today()
ls = models.Lesson(group_id=g.id, date=today, teacher_id=user_t.id, held=1)
db.add(ls)
db.commit()

db.add(models.Attendance(lesson_id=ls.id, student_id=s.id, present=1,
                         homework=2))
db.add(models.DailyGrade(lesson_id=ls.id, student_id=s.id, score=5,
                         created_by=user_t.username))
db.add(models.Payment(student_id=s.id, amount=-500000, kind="charge",
                      period=today.strftime("%Y-%m"), public_id="PAY-0001"))
db.add(models.Payment(student_id=s.id, amount=300000, kind="payment",
                      method="cash", note="Avgust uchun qisman",
                      public_id="PAY-0002"))
db.commit()

# Tasdiqlangan test — ko'rinishi kerak.
ex_ok = models.Exam(group_id=g.id, kind="unit", unit_no=5, date=today,
                    status="approved", max_score=20)
db.add(ex_ok)
db.commit()
db.add(models.ExamResult(exam_id=ex_ok.id, student_id=s.id, score=17,
                         percent=85.0, coins=5))

# Qoralama (hali tasdiqlanmagan) test — KO'RINMASLIGI kerak.
ex_draft = models.Exam(group_id=g.id, kind="mock", date=today,
                       status="draft", max_score=9)
db.add(ex_draft)
db.commit()
db.add(models.ExamResult(exam_id=ex_draft.id, student_id=s.id, band=6.5))
db.commit()

db.add(models.CoinEntry(student_id=s.id, amount=25, source="daily_grade",
                        ref_id=ls.id))
db.commit()

r = client.get(f"/api/parent/{s.parent_token}")
ck("status 200", r.status_code, 200)
d = r.json()

print("\n=== TO'LOVLAR TARIXI ===")
ck("2 ta to'lov yozuvi bor", len(d.get("payments", [])), 2)
pay_kinds = sorted(p["kind"] for p in d["payments"])
ck("kind'lar to'g'ri belgilangan", pay_kinds, ["Hisoblandi", "To'lov"])
paid = next(p for p in d["payments"] if p["kind"] == "To'lov")
ck("to'lov usuli belgilangan", paid["method"], "Naqd")
ck("to'lov izohi saqlangan", paid["note"], "Avgust uchun qisman")

print("\n=== COIN VA XP ===")
gam = d.get("gamification") or {}
ck("coin balansi to'g'ri", gam.get("coins"), 25)
ck("liga mavjud", bool(gam.get("league")), True)
ck("xp_history ro'yxat qaytadi", isinstance(d.get("xp_history"), list), True)

print("\n=== O'ZLASHTIRISH (kundalik baho) ===")
ck("1 ta kundalik baho bor", len(d.get("daily_grades", [])), 1)
ck("baho qiymati to'g'ri", d["daily_grades"][0]["score"], 5)

print("\n=== TEST NATIJALARI ===")
ck("faqat TASDIQLANGAN test ko'rinadi (1 ta, qoralama emas)",
   len(d.get("exam_results", [])), 1)
er = d["exam_results"][0]
ck("sarlavha avtomatik yaratilgan", er["title"], "Unit 5")
ck("foiz to'g'ri", er["percent"], 85.0)
ck("band bo'sh (unit test uchun)", er["band"], None)

print("\n=== MUDDATI TUGAGAN HAVOLA HAMON BLOKLANADI (regressiya) ===")
from datetime import datetime, timedelta
s.parent_token_expires_at = datetime.utcnow() - timedelta(days=1)
db.commit()
r2 = client.get(f"/api/parent/{s.parent_token}")
ck("muddati tugagan token 404 beradi", r2.status_code, 404)

print("\n" + ("BARCHASI OK" if not fails else f"XATOLAR: {fails}"))
sys.exit(1 if fails else 0)
