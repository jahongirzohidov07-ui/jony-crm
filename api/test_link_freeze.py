"""GURUH BO'YICHA MUZLATISH (2026-10-16).

Jahongir: "2ta guruhi bor o'quvchini bir guruhini muzlatsa ikkinchisi
ham muzlayabdi, ikkalasi alohida alohida muzlatish kerak".
"""
import os
import sys
import tempfile
from datetime import date, timedelta

_DIR = os.path.join(tempfile.gettempdir(), "link_freeze_test")
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
FRZ = max(M0, TODAY - timedelta(days=3))

db = SessionLocal()
b = models.Branch(name="Bekobod 2"); db.add(b); db.commit(); BID = b.id
db.add(models.User(username="asos", full_name="Asoschi", role=roles.FOUNDER,
                   password_hash=hash_password("x"), is_active=1))
t = models.Teacher(full_name="Elena", branch_id=BID, is_active=1,
                   grade="senior", hired_date=date(2025, 1, 1))
db.add(t); db.commit()


def mk_group(name):
    g = models.Group(name=name, teacher_id=t.id, branch_id=BID,
                     subject="english", lesson_days="mon,tue,wed,thu,fri,sat",
                     lesson_time="16:00", monthly_fee=540000,
                     lesson_price=45000, standard_lessons_per_month=12,
                     start_date=date(2026, 8, 1))
    db.add(g); db.commit()
    s, e = main.billing.month_bounds(TODAY.year, TODAY.month)
    main._sync_scheduled_lessons(db, g, s, e)
    db.commit()
    return g.id


G1, G2 = mk_group("Rus tili"), mk_group("LOUISIANA 2")
st = models.Student(full_name="Ikki Fanli", branch_id=BID, group_id=G1,
                    status="active", enrolled_date=date(2026, 9, 1))
db.add(st); db.commit()
C.attach_group(db, st, G1, None, joined=date(2026, 9, 1))
C.attach_group(db, st, G2, None, joined=date(2026, 9, 1))
db.add(models.Payment(student_id=st.id, amount=-486000, kind="charge",
                      period=PER, created_by=E._MC_BY,
                      note=f"Rus tili - {PER} oyi uchun 12 dars (avtomat)"))
db.add(models.Payment(student_id=st.id, amount=-486000, kind="charge",
                      period=MS.key(PER, G2), created_by=MS.BY,
                      note=f"LOUISIANA 2 — {PER}: 12 dars (2-fan, chegirma "
                           f"10%) [dars:12]"))
db.commit()
SID = st.id
db.close()

H = {"Authorization": "Bearer " + c.post(
    "/api/auth/login", json={"username": "asos", "password": "x"}
).json()["access_token"]}


def rows():
    db = SessionLocal()
    r = {p.period: round(abs(p.amount)) for p in db.query(models.Payment)
         .filter(models.Payment.student_id == SID,
                 models.Payment.kind == "charge").all()}
    db.close()
    return r


def lessons(gid, a, z):
    db = SessionLocal()
    n = MS._lessons_between(db, db.query(models.Group).get(gid), a, z)
    db.close()
    return n


def in_group_ids(gid):
    db = SessionLocal()
    ids = {s.id for s in db.query(models.Student).filter(C.in_group(gid))}
    db.close()
    return ids


print("=== 1. Faqat 2-guruh muzlatiladi ===")
r = c.post(f"/api/students/{SID}/groups/{G2}/freeze", headers=H,
           json={"from_date": FRZ.isoformat(), "note": "kasal"})
ck("200", r.status_code, 200)
db = SessionLocal()
s = db.query(models.Student).get(SID)
ck("o'quvchi FAOL qoldi", s.status, "active")
ck("asosiy guruh o'zgarmadi", s.group_id, G1)
ln2 = MS.link_of(db, SID, G2)
ck("2-guruh bog'lanishi muzlagan", ln2.status, "frozen")
ck("2 fan 10% endi yo'q", C._student_discount_percent(db, s), 0.0)
db.close()
n2 = min(lessons(G2, M0, FRZ - timedelta(days=1)), 12)
ck("2-guruh hisobi muzlagan kungacha", rows()[MS.key(PER, G2)],
   round(n2 * 40500))
ck("asosiy hisobga tegilmadi", rows()[PER], 486000)
ck("2-guruh ro'yxatida yo'q", SID in in_group_ids(G2), False)
ck("1-guruh ro'yxatida bor", SID in in_group_ids(G1), True)
db = SessionLocal()
ck("2-guruh davomat ro'yxatida yo'q",
   SID in {x.id for x in E._mgx_group_students(db, G2)}, False)
db.close()

print("=== 2. Kunlik jarayon qayta yechmaydi ===")
before = rows()
db = SessionLocal()
MS.daily(db, TODAY); db.commit(); db.close()
ck("o'zgarmadi", rows(), before)

print("=== 3. Yagona faol guruhni muzlatib bo'lmaydi ===")
r = c.post(f"/api/students/{SID}/groups/{G1}/freeze", headers=H, json={})
ck("400", r.status_code, 400)
ck("xabar", "yagona faol guruhi" in r.json().get("detail", ""), True)

print("=== 4. 2-guruh qayta faollashtiriladi ===")
r = c.post(f"/api/students/{SID}/groups/{G2}/unfreeze", headers=H,
           json={"on": TODAY.isoformat()})
ck("200", r.status_code, 200)
add = lessons(G2, TODAY, M0.replace(day=28) + timedelta(days=4))
want = min(n2 + add, 12)
ck("hisob qaytgan kundan to'ldirildi", rows()[MS.key(PER, G2)],
   round(want * 40500))
ck("ro'yxatga qaytdi", SID in in_group_ids(G2), True)

print("=== 5. ASOSIY guruh muzlatilsa — asosiy belgisi o'tadi ===")
r = c.post(f"/api/students/{SID}/groups/{G1}/freeze", headers=H,
           json={"from_date": FRZ.isoformat()})
ck("200", r.status_code, 200)
db = SessionLocal()
s = db.query(models.Student).get(SID)
ck("asosiy endi 2-guruh", s.group_id, G2)
ck("o'quvchi faol", s.status, "active")
db.close()
R = rows()
n1 = min(lessons(G1, M0, FRZ - timedelta(days=1)), 12)
ck("eski asosiy qator #g ga o'tdi va tushdi", R.get(MS.key(PER, G1)),
   round(n1 * 40500))
ck("yangi asosiyning qatori oddiy oylikka aylandi",
   R.get(PER), round(want * 40500))
ck("1-guruh ro'yxatida yo'q", SID in in_group_ids(G1), False)

print("=== 6. Avtomuzlatish — faqat kelmagan guruh ===")
db = SessionLocal()
s3 = models.Student(full_name="Avto Fan", branch_id=BID, group_id=G1,
                    status="active", enrolled_date=date(2026, 9, 1))
db.add(s3); db.commit()
C.attach_group(db, s3, G1, None, joined=date(2026, 9, 1))
C.attach_group(db, s3, G2, None, joined=date(2026, 9, 1))
S3 = s3.id
past = (db.query(models.Lesson)
        .filter(models.Lesson.group_id == G2,
                models.Lesson.date < TODAY,
                models.Lesson.date >= TODAY - timedelta(days=10))
        .order_by(models.Lesson.date.desc()).limit(3).all())
for ls in past:
    ls.held = 1
    db.add(models.Attendance(lesson_id=ls.id, student_id=S3, present=0))
db.commit()
import groups_lessons as GL                        # noqa: E402
if len(past) == 3:
    GL.run_auto_freeze(db, TODAY)
    db.expire_all()
    s3 = db.query(models.Student).get(S3)
    ck("avto: o'quvchi faol qoldi", s3.status, "active")
    ck("avto: faqat 2-guruh muzladi", MS.link_of(db, S3, G2).status,
       "frozen")
    ck("avto: 1-guruh faol", MS.link_of(db, S3, G1).status or "active",
       "active")
else:
    print("  (oyda yetarli o'tgan dars yo'q — avto test o'tkazildi)")
db.close()

print()
print("XATOLAR:", fails if fails else "yo'q")
sys.exit(1 if fails else 0)
