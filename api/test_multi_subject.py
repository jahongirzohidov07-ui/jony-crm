"""IKKI FAN: qo'shimcha guruh oyligi + 10% chegirma (2026-10-14).

Jahongir: "bitta o'quvchi 2ta fanga guruhga kelsa skidka bor edi 10%
avtomat bo'lishi kerak". Holmirzaeva Sabina: Rus tili (asosiy) +
LOUISIANA 2 (7-oktabrdan). Tizim faqat Rus tilini 540 000 yechgan,
ikkinchi guruh umuman hisoblanmagan.
"""
import os
import sys
import tempfile
from datetime import date, timedelta

_DIR = os.path.join(tempfile.gettempdir(), "multi_subject_test")
os.makedirs(_DIR, exist_ok=True)
_DB = os.path.join(_DIR, "db.sqlite")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace(chr(92), "/")
if os.path.exists(_DB):
    os.remove(_DB)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                         # noqa: E402
import entry as E                                  # noqa: E402
import multi_subject as MS                         # noqa: E402
import common as C                                 # noqa: E402
from database import SessionLocal                  # noqa: E402
from auth import hash_password                     # noqa: E402

c = TestClient(main.app)
fails = []


def ck(n, g, w):
    ok = g == w
    print(("OK  " if ok else "XATO ") + n + f": {g}"
          + ("" if ok else f" (kutilgan {w})"))
    if not ok:
        fails.append(n)


TODAY = roles.local_today()
PER = f"{TODAY.year:04d}-{TODAY.month:02d}"
M0 = TODAY.replace(day=1)

db = SessionLocal()
b = models.Branch(name="Bekobod 2"); db.add(b); db.commit(); BID = b.id
db.add(models.User(username="asos", full_name="Asoschi", role=roles.FOUNDER,
                   password_hash=hash_password("x"), is_active=1))
t = models.Teacher(full_name="Elena", branch_id=b.id, is_active=1,
                   grade="senior", hired_date=date(2025, 1, 1))
db.add(t); db.commit()


def mk_group(name):
    g = models.Group(name=name, teacher_id=t.id, branch_id=b.id,
                     subject="english", lesson_days="tue,thu,sat",
                     lesson_time="16:00", monthly_fee=540000,
                     lesson_price=45000, standard_lessons_per_month=12,
                     start_date=date(2026, 8, 1))
    db.add(g); db.commit()
    s, e = main.billing.month_bounds(TODAY.year, TODAY.month)
    main._sync_scheduled_lessons(db, g, s, e)
    db.commit()
    return g.id


G1, G2, G3 = mk_group("Rus tili"), mk_group("LOUISIANA 2"), mk_group("Nemis")
st = models.Student(full_name="Holmirzaeva Sabina", branch_id=b.id,
                    group_id=G1, status="active",
                    enrolled_date=date(2026, 9, 29))
db.add(st); db.commit()
C.attach_group(db, st, G1, None, joined=date(2026, 9, 29))
db.add(models.Payment(student_id=st.id, amount=-540000, kind="charge",
                      period=PER, created_by=E._MC_BY,
                      note=f"Rus tili - {PER} oyi uchun 12 dars (avtomat)"))
db.commit()
SID = st.id
db.close()

H = {"Authorization": "Bearer " + c.post(
    "/api/auth/login", json={"username": "asos", "password": "x"}
).json()["access_token"]}


def lessons(g, since, until):
    db = SessionLocal()
    n = MS._lessons_between(db, db.query(models.Group).get(g),
                            since, until)
    db.close()
    return n


def rows():
    db = SessionLocal()
    r = {p.period: abs(p.amount) for p in db.query(models.Payment)
         .filter(models.Payment.student_id == SID,
                 models.Payment.kind == "charge").all()}
    db.close()
    return r


print("=== 2-guruh qo'shildi ===")
JOIN = max(M0, TODAY - timedelta(days=7))
r = c.post(f"/api/students/{SID}/groups", headers=H,
           json={"group_id": G2, "joined_date": JOIN.isoformat()})
ck("qo'shish 200", r.status_code, 200)
# 2026-10-14 (R4): guruhi bor o'quvchiga qo'shilgan guruh avval SINOVDA —
# pul yo'q; "Faollashtirish" (qo'shilgan kundan) bosilgach yechiladi.
ck("qo'shilganda sinov", r.json().get("link_status"), "trial")
ck("sinovda pul yechilmadi", MS.key(PER, G2) in rows(), False)
r = c.post(f"/api/students/{SID}/groups/{G2}/activate", headers=H,
           json={"on": JOIN.isoformat()})
ck("faollashtirish 200", r.status_code, 200)
n2 = min(lessons(G2, JOIN, M0.replace(day=28) + timedelta(days=4)), 12)
R = rows()
ck("2-fan qatori yozildi (10% bilan)", round(R.get(MS.key(PER, G2), 0)),
   round(n2 * 45000 * 0.9))
ck("asosiy fan 10% ga tushdi", round(R.get(PER, 0)), 486000)
ck("javobda hisob", (r.json().get("charge") or {}).get("lessons"), n2)

print("=== Idempotent: kunlik ishga tushsa ham takrorlamaydi ===")
db = SessionLocal()
MS.daily(db, TODAY); db.commit(); db.close()
ck("qatorlar o'zgarmadi", rows(), R)

print("=== Chegirma foizi ===")
db = SessionLocal()
s = db.query(models.Student).get(SID)
ck("2 fan — 10%", C._student_discount_percent(db, s), 10.0)
db.close()

print("=== Kunlik: qatori yo'q 2-fanli o'quvchi ushlanadi ===")
db = SessionLocal()
s2 = models.Student(full_name="Ikki Fan", branch_id=BID, group_id=G1,
                    status="active", enrolled_date=date(2026, 9, 1))
db.add(s2); db.commit()
C.attach_group(db, s2, G1, None, joined=date(2026, 9, 1))
C.attach_group(db, s2, G3, None, joined=date(2026, 9, 1))
db.add(models.Payment(student_id=s2.id, amount=-540000, kind="charge",
                      period=PER, created_by=E._MC_BY,
                      note=f"Rus tili - {PER} oyi uchun 12 dars (avtomat)"))
db.commit()
S2 = s2.id
out = MS.daily(db, TODAY); db.commit()
p3 = db.query(models.Payment).filter(
    models.Payment.student_id == S2,
    models.Payment.period == MS.key(PER, G3)).first()
ck("to'liq oy 12 dars x 45 000 x 90%", round(abs(p3.amount)) if p3 else None,
   486000)
pr = db.query(models.Payment).filter(
    models.Payment.student_id == S2, models.Payment.period == PER).first()
ck("asosiy ham 10%", round(abs(pr.amount)), 486000)
db.close()

print("=== 2-guruhdan chiqdi — qator chiqqan kungacha ===")
r = c.delete(f"/api/students/{SID}/groups/{G2}", headers=H)
ck("chiqarish 200", r.status_code, 200)
upto = lessons(G2, JOIN, TODAY)
ck("2-fan qatori tushdi", round(rows().get(MS.key(PER, G2), 0)),
   round(upto * 45000 * 0.9))
ck("asosiy oshirilmadi (bu oy 10% qoladi)", round(rows().get(PER, 0)),
   486000)
db = SessionLocal()
s = db.query(models.Student).get(SID)
ck("endi 1 fan — 10% yo'q", C._student_discount_percent(db, s), 0.0)
db.close()

print("=== Muzlatilsa (kunlik) — 2-fan qatori tushiriladi ===")
db = SessionLocal()
s2 = db.query(models.Student).get(S2)
s2.status = "frozen"; db.commit()
MS.daily(db, TODAY); db.commit()
p3 = db.query(models.Payment).filter(
    models.Payment.student_id == S2,
    models.Payment.period == MS.key(PER, G3)).first()
up3 = MS._lessons_between(db, db.query(models.Group).get(G3), M0, TODAY)
ck("muzlaganda bugungacha", round(abs(p3.amount)),
   round(up3 * 45000 * 0.9))
db.close()

print("=== Hisobot: oy hisobiga 2-fan ham kiradi ===")
db = SessionLocal()
tot = sum(abs(p.amount) for p in db.query(models.Payment).filter(
    models.Payment.kind == "charge").all())
db.close()
r = c.get(f"/api/finance/month?period={PER}", headers=H)
if r.status_code == 200 and "charges" in r.json():
    ck("finance month charges", round(r.json()["charges"]), round(tot))
else:
    print("  (finance/month endpoint topilmadi — o'tkazildi)", r.status_code)

print()
print("XATOLAR:", fails if fails else "yo'q")
sys.exit(1 if fails else 0)
