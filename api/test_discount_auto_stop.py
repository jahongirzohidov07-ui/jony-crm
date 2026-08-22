"""CHEGIRMA O'Z-O'ZIDAN TO'XTASHI (2026-08-22).

Jahongir: "chegirma qoyilganda, oila qilib boglaganda xodim qilib
boglaganda, bu xodim ishda[n] boshasa yoki o'quvchi faol bolmasa
muzlatilgan arxivda bolsa chegirma avtomat bekor bolishi kerak".

Tekshiriladi: xodim ishdan ketsa bekor; o'quvchi muzlatilsa vaqtincha
to'xtaydi va faollashsa o'zi tiklanadi; arxiv/ketganda butunlay bekor;
faol o'quvchining chegirmasi tegilmaydi; oila foizi faol farzandlar
soniga qarab o'zi tushadi; chegirma to'xtaganda hisob-kitobda ham
ishlamaydi.
"""
import os, sys

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_disc/db.sqlite"
os.makedirs("/tmp/verify_disc", exist_ok=True)
if os.path.exists("/tmp/verify_disc/db.sqlite"):
    os.remove("/tmp/verify_disc/db.sqlite")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import date, timedelta
from fastapi.testclient import TestClient
import main, models, roles
import entry  # noqa: F401
from common import (_expire_discounts, _student_discount_percent,
                    _family_discount_percent)
from database import SessionLocal
from auth import hash_password

c = TestClient(main.app)
db = SessionLocal()
fails = []


def ck(n, g, w):
    ok = g == w
    print(("OK  " if ok else "XATO ") + f"{n}: {g}"
          + ("" if ok else f"   (kutilgan {w})"))
    if not ok:
        fails.append(n)


b = models.Branch(name="Zafar"); db.add(b); db.commit()
emp = models.User(username="xodim", full_name="Xodim Aka",
                  password_hash=hash_password("Parol123!"),
                  role=roles.ADMINISTRATOR, branch_id=b.id, is_active=1)
db.add(emp); db.commit()


def mk(name, status="active", parent_id=None):
    s = models.Student(full_name=name, branch_id=b.id, status=status,
                       parent_id=parent_id, enrolled_date=date(2026, 1, 1))
    db.add(s); db.commit()
    return s


def disc(s, kind="grant", pct=20, **kw):
    d = models.Discount(student_id=s.id, kind=kind, percent=pct,
                        reason="test", status="active", **kw)
    db.add(d); db.commit()
    return d


s_act = mk("Faol Bola")
s_frz = mk("Muzlatilgan Bola")
s_arc = mk("Arxiv Bola")
s_stf = mk("Xodim Farzandi")

d_act = disc(s_act)
d_frz = disc(s_frz)
d_arc = disc(s_arc)
d_stf = disc(s_stf, kind="staff_child", pct=50, staff_user_id=emp.id)

print("=== 1. BOSHIDA HAMMASI AMALDA ===")
ck("faol chegirmasi", d_act.status, "active")
ck("xodim farzandi chegirmasi", d_stf.status, "active")

print("\n=== 2. O'QUVCHI MUZLATILDI / ARXIVGA TUSHDI ===")
s_frz.status = "frozen"
s_arc.status = "archived"
db.commit()
_expire_discounts(db)
db.expire_all()
d_frz = db.query(models.Discount).get(d_frz.id)
d_arc = db.query(models.Discount).get(d_arc.id)
d_act = db.query(models.Discount).get(d_act.id)
ck("muzlatilgan -> vaqtincha to'xtadi", d_frz.status, "paused")
ck("sababi yozildi", "muzlatilgan" in (d_frz.cancelled_reason or ""), True)
ck("arxiv -> bekor qilindi", d_arc.status, "cancelled")
ck("faolga tegilmadi", d_act.status, "active")

print("\n=== 3. TO'XTAGAN CHEGIRMA HISOBGA OLINMAYDI ===")
ck("muzlatilganda foiz 0", _student_discount_percent(db, s_frz), 0.0)
ck("arxivda foiz 0", _student_discount_percent(db, s_arc), 0.0)
ck("faolda foiz bor", _student_discount_percent(db, s_act), 20.0)

print("\n=== 4. QAYTIB FAOLLASHSA O'ZI TIKLANADI ===")
s_frz.status = "active"
db.commit()
_expire_discounts(db)
db.expire_all()
d_frz = db.query(models.Discount).get(d_frz.id)
ck("chegirma tiklandi", d_frz.status, "active")
ck("sabab tozalandi", d_frz.cancelled_reason, None)
ck("foiz qaytdi", _student_discount_percent(db, s_frz), 20.0)

print("\n=== 5. ARXIVDAGI O'ZI TIKLANMAYDI ===")
s_arc.status = "active"
db.commit()
_expire_discounts(db)
db.expire_all()
ck("bekor qilingan bekorligicha",
   db.query(models.Discount).get(d_arc.id).status, "cancelled")

print("\n=== 6. XODIM ISHDAN KETDI ===")
emp.is_active = 0
db.commit()
_expire_discounts(db)
db.expire_all()
d_stf = db.query(models.Discount).get(d_stf.id)
ck("xodim farzandi bekor", d_stf.status, "cancelled")
ck("sababi yozildi", "Xodim ishdan ketdi" in (d_stf.cancelled_reason or ""), True)
ck("foiz nolga tushdi", _student_discount_percent(db, s_stf), 0.0)

print("\n=== 7. OILA FOIZI FAOL FARZANDLARDAN HISOBLANADI ===")
p = models.Parent(full_name="Oila", branch_id=b.id); db.add(p); db.commit()
k1 = mk("Katta Farzand", parent_id=p.id)
k2 = mk("Kichik Farzand", parent_id=p.id)
ck("ikki faol farzand -> chegirma bor",
   _family_discount_percent(db, k1) > 0, True)
k2.status = "frozen"; db.commit()
ck("biri muzlasa -> foiz o'zi tushdi",
   _family_discount_percent(db, k1), 0.0)
k2.status = "active"; db.commit()
ck("qaytsa -> foiz qaytdi", _family_discount_percent(db, k1) > 0, True)

print("\n=== 8. MUDDATI O'TGANI ===")
s_old = mk("Muddati Otgan")
d_old = disc(s_old, end_date=date.today() - timedelta(days=1))
_expire_discounts(db)
db.expire_all()
ck("muddati tugadi", db.query(models.Discount).get(d_old.id).status, "expired")

print("\n=== 9. TAKROR YUGURSA O'ZGARISH YO'Q ===")
_expire_discounts(db)
ck("ikkinchi yugurish tinch", _expire_discounts(db), 0)

print("\n" + ("HAMMASI O'TDI" if not fails else f"XATOLAR: {fails}"))
sys.exit(1 if fails else 0)
