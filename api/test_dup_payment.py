"""Dubl to'lovga qarshi himoya + oylik hisoblashning bosqichma-bosqich
bajarilishi (2026-08-14, Jahongir: "Tugma ikki marta bosilsa yoki
internet uzilib qayta yuborilsa - ikkita to'lov tushadi ... Oylik
avtomat hisoblash ... yarmida uzilib, oyning bir qismi hisoblanmay
qolishi mumkin. shularni qilda")."""
import os, sys
from datetime import date
os.environ["DATABASE_URL"] = "sqlite:////tmp/duppay.db"
if os.path.exists("/tmp/duppay.db"): os.remove("/tmp/duppay.db")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fastapi.testclient import TestClient
import main, models, roles
import entry  # noqa
from database import SessionLocal
from auth import hash_password
c = TestClient(main.app); fails = []


def ck(n, g, w):
    ok = g == w
    print(("OK  " if ok else "XATO ") + n + f": {g}"
          + ("" if ok else f" (kutilgan {w})"))
    if not ok:
        fails.append(n)


db = SessionLocal()
b = models.Branch(name="Bekobod 1"); db.add(b); db.commit(); BID = b.id
t = models.Teacher(full_name="Ustoz", branch_id=BID); db.add(t); db.commit()
TID = t.id
g = models.Group(name="G1", teacher_id=TID, branch_id=BID,
                 monthly_fee=400000, lesson_days="mon,wed",
                 lesson_time="10:00 - 12:00")
db.add(g); db.commit(); GID = g.id
st = models.Student(full_name="Aliyev Ali", branch_id=BID,
                    status="active", group_id=GID)
st2 = models.Student(full_name="Valiyev Vali", branch_id=BID,
                     status="active", group_id=GID)
db.add_all([st, st2]); db.commit(); SID, SID2 = st.id, st2.id
db.add_all([
    models.User(username="adm", full_name="Admin", role="administrator",
                branch_id=BID, password_hash=hash_password("x"),
                is_active=1),
    models.User(username="adm2", full_name="Admin 2",
                role="administrator", branch_id=BID,
                password_hash=hash_password("x"), is_active=1),
])
db.commit(); db.close()


def tok(u):
    return {"Authorization": "Bearer " + c.post(
        "/api/auth/login", json={"username": u, "password": "x"})
        .json()["access_token"]}


A, A2 = tok("adm"), tok("adm2")

print("=== 1. Bir xil kalit bilan 2 marta yuborilsa - BITTA to'lov ===")
KEY = "test-key-0001"
body = {"amount": 480000, "kind": "payment", "method": "terminal",
        "client_key": KEY}
r1 = c.post(f"/api/students/{SID}/payments", headers=A, json=body)
ck("1-so'rov o'tdi", r1.status_code, 200)
r2 = c.post(f"/api/students/{SID}/payments", headers=A, json=body)
ck("2-so'rov ham 200 (xato emas)", r2.status_code, 200)
ck("AYNI o'sha yozuv qaytdi", r2.json()["id"], r1.json()["id"])

db = SessionLocal()
n = db.query(models.Payment).filter(
    models.Payment.student_id == SID,
    models.Payment.kind == "payment").count()
ck("bazada faqat 1 ta to'lov", n, 1)
bal = sum(p.amount for p in db.query(models.Payment)
          .filter(models.Payment.student_id == SID).all())
ck("balans 480 000 (960 000 emas)", bal, 480000)
db.close()

print("\n=== 2. Kalit boshqa, summa bir xil, 2 daqiqa ichida -> 409 ===")
r3 = c.post(f"/api/students/{SID}/payments", headers=A,
            json={"amount": 480000, "kind": "payment",
                  "method": "terminal", "client_key": "test-key-0002"})
ck("409 ogohlantirish", r3.status_code, 409)
d = r3.json().get("detail") or {}
ck("tasdiqlash mumkin (can_force)", d.get("can_force"), True)
ck("xabarda ism bor", "Aliyev Ali" in (d.get("message") or ""), True)

print("\n=== 3. Boshqa xodim kiritsa ham to'sadi (ikki kishi bir vaqtda) ===")
r4 = c.post(f"/api/students/{SID}/payments", headers=A2,
            json={"amount": 480000, "kind": "payment",
                  "method": "cash", "client_key": "test-key-0003"})
ck("409", r4.status_code, 409)

print("\n=== 4. force=true bilan tasdiqlansa - o'tadi ===")
r5 = c.post(f"/api/students/{SID}/payments", headers=A,
            json={"amount": 480000, "kind": "payment",
                  "method": "terminal", "client_key": "test-key-0004",
                  "force": True})
ck("qabul qilindi", r5.status_code, 200)
db = SessionLocal()
n = db.query(models.Payment).filter(
    models.Payment.student_id == SID,
    models.Payment.kind == "payment").count()
ck("endi 2 ta to'lov", n, 2)
db.close()

print("\n=== 5. Boshqa summa - to'siq yo'q ===")
r6 = c.post(f"/api/students/{SID}/payments", headers=A,
            json={"amount": 250000, "kind": "payment", "method": "cash",
                  "client_key": "test-key-0005"})
ck("qabul qilindi", r6.status_code, 200)

print("\n=== 6. Boshqa o'quvchi, bir xil summa - to'siq yo'q ===")
r7 = c.post(f"/api/students/{SID2}/payments", headers=A,
            json={"amount": 480000, "kind": "payment", "method": "cash",
                  "client_key": "test-key-0006"})
ck("qabul qilindi", r7.status_code, 200)

print("\n=== 7. Kalitsiz eski forma ham ishlayveradi (orqaga moslik) ===")
r8 = c.post(f"/api/students/{SID2}/payments", headers=A,
            json={"amount": 111000, "kind": "payment", "method": "cash"})
ck("qabul qilindi", r8.status_code, 200)

print("\n=== 8. Qarz (charge) yozuviga ogohlantirish qo'yilmaydi ===")
r9 = c.post(f"/api/students/{SID2}/payments", headers=A,
            json={"amount": 90000, "kind": "charge"})
r10 = c.post(f"/api/students/{SID2}/payments", headers=A,
             json={"amount": 90000, "kind": "charge"})
ck("1-charge", r9.status_code, 200)
ck("2-charge ham o'tadi", r10.status_code, 200)

print("\n=== 9. Oylik hisoblash: byudjet tugasa QOLGANIDAN davom etadi ===")
from common import _ensure_month_charges, _seed_done
import common
db = SessionLocal()
period = f"{date.today().year:04d}-{date.today().month:02d}"
# Login paytida allaqachon bir marta ishlagan — belgilarni tozalab,
# "yarmida uzilgan" holatni sun'iy yaratamiz.
db.query(models.SeedMark).filter(
    models.SeedMark.key.like("mc%")).delete(synchronize_session=False)
db.commit()
common._SEED_KEYS = None
ck("belgilar tozalandi", _seed_done(db, f"mc_{period}_g{GID}"), False)
# Haqiqiy dars + yo'qlama qo'shamiz — aks holda hisoblanadigan summa
# 0 bo'ladi va guruh ATAYLAB belgilanmaydi (oy boshidagi holat).
gg = db.query(models.Group).get(GID)
gg.lesson_price = 50000
first = date(date.today().year, date.today().month, 1)
for _sid in (SID, SID2):
    db.query(models.Student).get(_sid).enrolled_date = first
db.commit()
for d in (2, 4, 8, 10):
    try:
        ls = models.Lesson(group_id=GID, date=date(date.today().year,
                                                   date.today().month, d),
                           held=1)
        db.add(ls); db.commit()
        for sid in (SID, SID2):
            db.add(models.Attendance(lesson_id=ls.id, student_id=sid,
                                     present=1))
        db.commit()
    except Exception:
        db.rollback()
# byudjet manfiy => birorta guruh ishlanmaydi, guruh belgisi
# QO'YILMASLIGI kerak — aks holda oyning qolgani hech qachon
# hisoblanmay qolardi (aynan tuzatilgan xato).
_ensure_month_charges(db, budget_s=-1)
ck("byudjet tugagan: guruh belgilanmadi",
   _seed_done(db, f"mc_{period}_g{GID}"), False)
# to'liq byudjet bilan qaytadan - endi guruh ishlanadi
_ensure_month_charges(db, budget_s=30)
ck("guruh ishlandi va belgilandi",
   _seed_done(db, f"mc_{period}_g{GID}"), True)
db.close()

print("\n=== 10. Ikki marta chaqirilsa oylik IKKI marta yechilmaydi ===")
db = SessionLocal()
before = db.query(models.Payment).filter(
    models.Payment.kind == "charge",
    models.Payment.created_by == "avtomat (oylik)").count()
_ensure_month_charges(db, budget_s=30)
_ensure_month_charges(db, budget_s=30)
after = db.query(models.Payment).filter(
    models.Payment.kind == "charge",
    models.Payment.created_by == "avtomat (oylik)").count()
ck("qo'shimcha yechim yo'q", after, before)
db.close()

print("\n=== 11. Sxema tayyorligi bir marta tekshiriladi ===")
ck("_schema_ready() ishlaydi", common._schema_ready(), True)
ck("ensure_tables jim o'tadi", common.ensure_tables([]) is None, True)

print("\n=== 12. Sentyabrdan keyingi qoida (mcf) ham bosqichli ===")
import entry as E
db = SessionLocal()
gg = db.query(models.Group).get(GID)
gg.lesson_price = 40000
gg.standard_lessons_per_month = 12
db.commit()
sept = date(2026, 9, 15)
# byudjet allaqachon tugagan: birorta guruh ishlanmaydi
n, ok = E._mc_charge_full(db, sept, deadline=-1)
ck("byudjet tugagan: 0 yozuv", n, 0)
ck("tugallanmagan deb qaytdi", ok, False)
# to'liq byudjet bilan
import time as _t
n2, ok2 = E._mc_charge_full(db, sept, deadline=_t.monotonic() + 30)
ck("yechimlar yozildi", n2 > 0, True)
ck("tugallandi", ok2, True)
# takroran chaqirilsa yangi yozuv YO'Q (guruh belgilangan)
n3, ok3 = E._mc_charge_full(db, sept, deadline=_t.monotonic() + 30)
ck("takrorda 0 yozuv", n3, 0)
tot = db.query(models.Payment).filter(
    models.Payment.period == "2026-09",
    models.Payment.kind == "charge").count()
ck("sentyabr uchun har o'quvchida 1 tadan", tot, n2)
db.close()

print("\n=== 13. Guruhlar bitta so'rovda olinadi (N+1 yo'q) ===")
from sqlalchemy import event as _ev
from sqlalchemy.engine import Engine as _Eng
cnt = [0]


@_ev.listens_for(_Eng, "before_cursor_execute")
def _cnt(conn, cur, st, p, ctx, many):
    cnt[0] += 1


db = SessionLocal()
cnt[0] = 0
E._mc_active_groups(db)
ck("2 tadan ko'p so'rov yo'q", cnt[0] <= 2, True)
db.close()

print("\n" + ("HAMMASI OK" if not fails
              else f"{len(fails)} ta XATO: {fails}"))
sys.exit(1 if fails else 0)
