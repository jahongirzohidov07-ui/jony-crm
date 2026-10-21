"""BOG'LANGAN IMTIHONNI O'CHIRISH (2026-10-21).

Jahongir: "achievers new azizova guruhida bir kunda ikkita imtixon
belgilanib qolibdi bittasida hech narsa kiritilmagan bittasida
o'quvchilar ishlagan bo'sh imtixonni bosh examiner o'chirmoqchi bo'lsa
serverda xatolik deyabdi".

Sabab: bo'sh imtihonga BUYURTMA (exam_orders.exam_id), XP yozuvi yoki
jonli o'yin bog'langan edi — Postgres bog'langan yozuvi bor imtihonni
o'chirishga ruxsat bermaydi (500). SQLite'da ham FK yoqib tekshiramiz.

Tekshiriladi:
  1. Bo'sh takror imtihon o'chiriladi (200); buyurtma natijali
     imtihonga o'tadi; XP va o'yin tarixi qoladi, havola bo'shaydi.
  2. Boshqa imtihoni yo'q buyurtma — bog'lanish uziladi.
  3. Buyurtma qabul qilinganda shu kuni xuddi shu imtihon bo'lsa —
     yangisi yaratilmaydi.
"""
import os
import sys
import tempfile

_DIR = os.path.join(tempfile.gettempdir(), "exam_delete_linked_test")
os.makedirs(_DIR, exist_ok=True)
_DB = os.path.join(_DIR, "db.sqlite")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace(chr(92), "/")
if os.path.exists(_DB):
    os.remove(_DB)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import timedelta                     # noqa: E402
from sqlalchemy import event                       # noqa: E402
from fastapi.testclient import TestClient          # noqa: E402
import database                                    # noqa: E402


@event.listens_for(database.engine, "connect")
def _fk_on(conn, _rec):
    # Prod (Postgres) kabi — bog'langan yozuvli qatorni o'chirib bo'lmaydi
    conn.execute("PRAGMA foreign_keys=ON")


import main, models, roles                         # noqa: E402
import entry                                       # noqa: E402,F401
from database import SessionLocal                  # noqa: E402
from auth import hash_password                     # noqa: E402

c = TestClient(main.app)
fails = []


def ck(name, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + name + f": {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


db = SessionLocal()
b = models.Branch(name="Chilonzor"); db.add(b); db.commit()
he = models.User(username="bosh", password_hash=hash_password("x"),
                 full_name="Bosh Examiner", role=roles.HEAD_EXAMINER,
                 branch_id=b.id, is_active=1)
db.add(he); db.commit()
g = models.Group(name="Achievers New Azizova", branch_id=b.id,
                 lesson_price=45_000, standard_lessons_per_month=12,
                 monthly_fee=540_000)
db.add(g); db.commit()
st = models.Student(full_name="Ali Valiyev", branch_id=b.id,
                    status="active")
db.add(st); db.commit()
T = roles.local_today()
H = {"Authorization": "Bearer " + c.post(
    "/api/auth/login", json={"username": "bosh", "password": "x"}
).json()["access_token"]}


def exam(day=T, unit=3):
    e = models.Exam(group_id=g.id, kind="unit", unit_no=unit, date=day,
                    status="approved", max_score=50)
    db.add(e); db.commit()
    return e


print("=== 1. BO'SH TAKROR IMTIHON (buyurtma + XP + o'yin bog'langan) ===")
full = exam()
db.add(models.ExamResult(exam_id=full.id, student_id=st.id, score=40))
empty = exam()
o = models.ExamOrder(branch_id=b.id, group_id=g.id, kind="unit", unit_no=3,
                     date=T, status="accepted", exam_id=empty.id)
xp = models.XpTransaction(student_id=st.id, amount=5, exam_id=empty.id)
lg = models.LiveGame(code="123456", course="ielts_1_0", lesson_no=1,
                     questions="[]", group_id=g.id, exam_id=empty.id)
db.add_all([o, xp, lg]); db.commit()
oid, xid, lid, eid = o.id, xp.id, lg.id, empty.id

r = c.delete(f"/api/exams/{eid}", headers=H)
ck("o'chirildi (500 emas)", r.status_code, 200)
db.expire_all()
ck("bo'sh imtihon yo'q", db.query(models.Exam).get(eid), None)
ck("buyurtma natijali imtihonga o'tdi",
   db.query(models.ExamOrder).get(oid).exam_id, full.id)
ck("XP yozuvi saqlandi", db.query(models.XpTransaction).get(xid).amount, 5)
ck("XP havolasi bo'shadi",
   db.query(models.XpTransaction).get(xid).exam_id, None)
ck("o'yin havolasi bo'shadi", db.query(models.LiveGame).get(lid).exam_id,
   None)
ck("natijali imtihon joyida",
   len(db.query(models.Exam).get(full.id).results), 1)

print("\n=== 2. YAGONA IMTIHON — BUYURTMA BOG'LANISHI UZILADI ===")
lone = exam(day=T + timedelta(days=7), unit=4)
o2 = models.ExamOrder(branch_id=b.id, group_id=g.id, kind="unit", unit_no=4,
                      date=lone.date, status="accepted", exam_id=lone.id)
db.add(o2); db.commit()
r = c.delete(f"/api/exams/{lone.id}", headers=H)
ck("o'chirildi", r.status_code, 200)
db.expire_all()
ck("buyurtmada imtihon yo'q", db.query(models.ExamOrder).get(o2.id).exam_id,
   None)

print("\n=== 3. QABUL QILISHDA TAKROR IMTIHON OCHILMAYDI ===")
day = T + timedelta(days=3)
have = exam(day=day, unit=5)
o3 = models.ExamOrder(branch_id=b.id, group_id=g.id, kind="unit", unit_no=5,
                      date=day, status="new")
db.add(o3); db.commit()
before = db.query(models.Exam).filter(models.Exam.group_id == g.id).count()
r = c.post(f"/api/exam-orders/{o3.id}/accept", headers=H, json={})
ck("qabul qilindi", r.status_code, 200)
db.expire_all()
ck("yangi imtihon yaratilmadi",
   db.query(models.Exam).filter(models.Exam.group_id == g.id).count(),
   before)
ck("buyurtma mavjud imtihonga bog'landi",
   db.query(models.ExamOrder).get(o3.id).exam_id, have.id)
# Boshqa unit — oddiy holatda imtihon yaratiladi
o4 = models.ExamOrder(branch_id=b.id, group_id=g.id, kind="unit", unit_no=6,
                      date=day, status="new")
db.add(o4); db.commit()
r = c.post(f"/api/exam-orders/{o4.id}/accept", headers=H, json={})
ck("boshqa unit qabul qilindi", r.status_code, 200)
db.expire_all()
ck("boshqa unit uchun yangi imtihon yaratildi",
   db.query(models.Exam).filter(models.Exam.group_id == g.id).count(),
   before + 1)

print()
if fails:
    print(f"XATO: {len(fails)} ta tekshiruv o'tmadi")
    for x in fails:
        print("   - " + x)
    sys.exit(1)
print("HAMMASI O'TDI")
sys.exit(0)
