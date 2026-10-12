"""AVTOMUZLATILGANDA USTOZGA VA ADMINGA XABAR (2026-09-03).

Jahongir: "keyin qaysidur o'quvchi avtomat muzlatilsa, o'qituvchiga
xabar borsin, adminga ham xabar borsin".

Ilgari ketma-ket 3 darsga kelmagan o'quvchi avtomat muzlatilardi va
faqat ADMINISTRATORGA jimgina vazifa tushardi. Ustoz esa umuman
bilmasdi — bola ro'yxatdan chiqib ketgani unga hech qayerda
aytilmasdi.

Test HAQIQIY yo'l bilan ishlaydi: yo'qlama endpointiga uch marta
"kelmadi" yuboriladi va shundan keyin xabarlar tekshiriladi.
"""
import os, sys
from datetime import date, timedelta

os.environ["DATABASE_URL"] = "sqlite:////tmp/afnotify_test.db"
if os.path.exists("/tmp/afnotify_test.db"):
    os.remove("/tmp/afnotify_test.db")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
import main, models, roles
import entry  # noqa: F401 — production yo'li
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


def tok(u, p="x"):
    return {"Authorization": "Bearer " + client.post(
        "/api/auth/login", json={"username": u, "password": p}
    ).json()["access_token"]}


TODAY = date.today()
db = SessionLocal()
b = models.Branch(name="Zafar")
db.add(b)
db.commit()
BID = b.id

db.add(models.User(username="asos", password_hash=hash_password("x"),
                   full_name="Asoschi", role="founder"))
uadm = models.User(username="admin1", password_hash=hash_password("x"),
                   full_name="Administrator Aziz", role="sales_manager",
                   branch_id=BID)
ut = models.User(username="ustoz1", password_hash=hash_password("x"),
                 full_name="Ustoz Sardor", role="teacher", branch_id=BID)
usup = models.User(username="support1", password_hash=hash_password("x"),
                   full_name="Support Nodira", role="support_teacher",
                   branch_id=BID)
db.add_all([uadm, ut, usup])
db.commit()
UADM, UT, USUP = uadm.id, ut.id, usup.id

t = models.Teacher(full_name="Ustoz Sardor", branch_id=BID, is_active=1,
                   grade="senior", user_id=UT,
                   hired_date=TODAY - timedelta(days=500))
db.add(t)
db.commit()
TID = t.id

g = models.Group(name="Best Kids", teacher_id=TID, branch_id=BID,
                 subject="english", lesson_days="mon,tue,wed,thu,fri,sat",
                 lesson_time="09:00",
                 start_date=TODAY - timedelta(days=60),
                 lesson_price=40000, monthly_fee=480000,
                 standard_lessons_per_month=12)
db.add(g)
db.commit()
GID = g.id
db.add(models.SupportAssignment(user_id=USUP, group_id=GID,
                                created_by="Test"))

st = models.Student(full_name="Kelmayotgan Bola", branch_id=BID,
                    group_id=GID, status="active",
                    enrolled_date=TODAY - timedelta(days=60))
boshqa = models.Student(full_name="Kelayotgan Bola", branch_id=BID,
                        group_id=GID, status="active",
                        enrolled_date=TODAY - timedelta(days=60))
db.add_all([st, boshqa])
db.commit()
SID, OID = st.id, boshqa.id

LIDS = []
for i in (3, 2, 1):
    ls = models.Lesson(group_id=GID, teacher_id=TID,
                       date=TODAY - timedelta(days=i), held=0)
    db.add(ls)
    db.commit()
    LIDS.append(ls.id)
db.close()

H = tok("asos")

print("=== 1. BOSHIDA XABAR YO'Q ===")
db = SessionLocal()
ck("vazifa yo'q", db.query(models.Task).count(), 0)
ck("o'quvchi faol",
   db.query(models.Student).get(SID).status, "active")
db.close()

print("\n=== 2. UCH DARSGA KETMA-KET KELMADI ===")
for i, lid in enumerate(LIDS):
    r = client.put(f"/api/lessons/{lid}/attendance", headers=H, json={
        "marks": [{"student_id": SID, "present": False},
                  {"student_id": OID, "present": True}]})
    ck(f"{i + 1}-dars yo'qlamasi saqlandi", r.status_code, 200)

_d0 = SessionLocal()
ck("saqlashda darhol muzlamaydi", _d0.query(models.Student).get(SID).status, "active")
_d0.close()
# 2026-10-12: muzlatish saqlashda emas — ertalabki kunlik tekshiruvda
import groups_lessons as _GL  # noqa: E402
_dbf = SessionLocal(); _GL.run_auto_freeze(_dbf); _dbf.close()
db = SessionLocal()
ck("o'quvchi AVTOMAT muzlatildi",
   db.query(models.Student).get(SID).status, "frozen")
ck("izohda sabab yozilgan",
   "avtomuzlatildi" in (db.query(models.Student).get(SID).frozen_note
                        or "").lower(), True)
ck("kelib turgan bolaga tegilmadi",
   db.query(models.Student).get(OID).status, "active")
db.close()

print("\n=== 3. USTOZGA XABAR BORDI ===")
db = SessionLocal()
tasks = db.query(models.Task).all()
t_ust = [x for x in tasks if x.assignee_id == UT]
ck("ustozga vazifa tushdi", len(t_ust), 1)
ck("sarlavhada avtomuzlatish",
   "Avtomuzlatildi" in (t_ust[0].title if t_ust else ""), True)
ck("o'quvchi ismi bor",
   "Kelmayotgan Bola" in (t_ust[0].title if t_ust else ""), True)
body = t_ust[0].description if t_ust else ""
ck("guruh nomi aytilgan", "Best Kids" in body, True)
ck("nechta dars aytilgan", "3 darsga" in body, True)
ck("nima qilish aytilgan", "bog'lanib" in body, True)

print("\n=== 4. SUPPORT USTOZGA HAM ===")
ck("supportga ham vazifa tushdi",
   len([x for x in tasks if x.assignee_id == USUP]), 1)

print("\n=== 5. ADMINGA XABAR BORDI ===")
t_adm = [x for x in tasks if x.assignee_id == UADM]
ck("administratorga vazifa tushdi", len(t_adm), 1)
ck("sarlavhasi tushunarli",
   "Muzlatilgan o'quvchi" in (t_adm[0].title if t_adm else ""), True)
db.close()

print("\n=== 6. AUDITGA YOZILDI ===")
db = SessionLocal()
a = db.query(models.AuditLog).filter(
    models.AuditLog.action == "auto_freeze",
    models.AuditLog.entity_id == SID).all()
ck("audit yozuvi bor", len(a), 1)
db.close()

print("\n=== 7. TAKROR XABAR YUBORILMAYDI ===")
db = SessionLocal()
n_before = db.query(models.Task).count()
db.close()
import common
db = SessionLocal()
_st = db.query(models.Student).get(SID)
_g = db.query(models.Group).get(GID)
common.auto_freeze_notify(db, _st, _g)
db.commit()
db.close()
db = SessionLocal()
ck("bir xil kun uchun dubl vazifa yo'q",
   db.query(models.Task).count(), n_before)
db.close()

print("\n=== 8. TELEGRAM ULANMAGAN BO'LSA HAM ISHLAYDI ===")
import notify
ck("testda Telegram o'chiq", notify.enabled(), False)
ck("shunga qaramay vazifalar joyida",
   len(t_ust) + len(t_adm) >= 2, True)

print("\n" + ("BARCHASI OK" if not fails else f"XATOLAR: {fails}"))
sys.exit(1 if fails else 0)
