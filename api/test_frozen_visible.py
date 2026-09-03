"""MUZLATILGAN O'QUVCHI USTOZGA KO'RINSIN, LEKIN YO'QLAMAGA CHIQMASIN
(2026-09-03).

Jahongir: "ustozlarga muzlatilgan o'quvchilari korinsin faqat
yoqlamasi chiqmasin iltmos".

Avval (2026-08-10) qoida boshqacha edi: "muzlatilgan o'quvchilar
o'qituvchilarga ko'rinmasin" — va ular ustozning RO'YXATLARIDAN ham
butunlay olib tashlangan edi. Endi qoida ikkiga bo'linadi:

  KO'RINADI   — "O'quvchilarim" ro'yxatida va guruh ro'yxatida
                turadi, "muzlatilgan" deb belgilanadi;
  KO'RINMAYDI — davomat jadvalida yo'q, yo'qlama ham, baho ham
                qo'yib bo'lmaydi (yo'qlama — ish haqi hujjati).

Test AYNAN shu ikki tomonni tekshiradi.
"""
import os, sys
from datetime import date, timedelta

os.environ["DATABASE_URL"] = "sqlite:////tmp/frzvis_test.db"
if os.path.exists("/tmp/frzvis_test.db"):
    os.remove("/tmp/frzvis_test.db")
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
db.commit()

t = models.Teacher(full_name="Mening Ustoz", branch_id=BID, is_active=1,
                   grade="senior", hired_date=TODAY - timedelta(days=800))
db.add(t)
db.commit()
TID = t.id
u = models.User(username="mening.ustoz", password_hash=hash_password("x"),
                full_name="Mening Ustoz", role="teacher", branch_id=BID)
db.add(u)
db.commit()
t.user_id = u.id
db.commit()

g = models.Group(name="Kids", teacher_id=TID, branch_id=BID,
                 subject="english", lesson_days="mon,wed,fri",
                 lesson_time="09:00", start_date=TODAY - timedelta(days=60),
                 lesson_price=40000, monthly_fee=480000,
                 standard_lessons_per_month=12)
db.add(g)
db.commit()
GID = g.id

aktiv = models.Student(full_name="Aktiv Ali", branch_id=BID, group_id=GID,
                       status="active",
                       enrolled_date=TODAY - timedelta(days=60))
muz = models.Student(full_name="Muzlatilgan Vali", branch_id=BID,
                     group_id=GID, status="frozen",
                     enrolled_date=TODAY - timedelta(days=60))
db.add_all([aktiv, muz])
db.commit()
AID, MID = aktiv.id, muz.id
db.close()

ME = tok("mening.ustoz")
H = tok("asos")

print("=== 1. \"O'QUVCHILARIM\"DA MUZLATILGAN KO'RINADI ===")
d = client.get("/api/me/students", headers=ME).json()
ids = [r["id"] for r in d["rows"]]
ck("aktiv bor", AID in ids, True)
ck("MUZLATILGAN HAM BOR", MID in ids, True)
row = [r for r in d["rows"] if r["id"] == MID][0]
ck("statusi ko'rinadi", row["status"], "frozen")
ck("muzlatilganlar soni beriladi", d.get("frozen"), 1)
ck("eslatmada aytilgan",
   "yo'qlama qo'yilmaydi" in d.get("hint", ""), True)

print("\n=== 2. GURUH RO'YXATIDA HAM KO'RINADI ===")
r = client.get(f"/api/students?group_id={GID}", headers=ME)
ck("so'rov 200", r.status_code, 200)
gids = [x["id"] for x in r.json()]
ck("aktiv bor", AID in gids, True)
ck("MUZLATILGAN HAM BOR", MID in gids, True)

print("\n=== 3. DAVOMAT JADVALIDA YO'Q ===")
a = client.get(f"/api/groups/{GID}/attendance"
               f"?year={TODAY.year}&month={TODAY.month}",
               headers=ME).json()
sids = [x["id"] for x in a["students"]]
ck("aktiv bor", AID in sids, True)
ck("MUZLATILGAN YO'Q", MID in sids, False)

print("\n=== 4. BAHOLASH RO'YXATIDA HAM YO'Q ===")
gr = client.get(f"/api/groups/{GID}/grades"
                f"?year={TODAY.year}&month={TODAY.month}",
                headers=ME)
if gr.status_code == 200:
    gsids = [x["id"] for x in gr.json().get("students", [])]
    ck("aktiv bor", AID in gsids, True)
    ck("MUZLATILGAN YO'Q", MID in gsids, False)
else:
    print(f"    (baholash ro'yxati {gr.status_code} — o'tkazildi)")

print("\n=== 5. QO'LDA SO'ROV YUBORILSA HAM BELGILANMAYDI ===")
db = SessionLocal()
# BUGUNGI dars — o'tib ketgan kunning yo'qlamasini ustoz o'zgartira
# olmaydi (bu alohida qoida), shuning uchun sanani bugunga qo'yamiz.
les = db.query(models.Lesson).filter(
    models.Lesson.group_id == GID).order_by(
    models.Lesson.date.desc()).first()
if les is not None:
    les.date = TODAY
    db.commit()
LID = les.id if les else None
db.close()
ck("tekshirish uchun dars topildi", LID is not None, True)
r = client.put(f"/api/lessons/{LID}/attendance", headers=ME, json={
    "marks": [{"student_id": AID, "present": True},
              {"student_id": MID, "present": True}]})
ck("so'rov rad etilmadi (aktiv saqlanadi)", r.status_code, 200)
db = SessionLocal()
ck("aktivga belgi qo'yildi",
   bool(db.query(models.Attendance).filter(
       models.Attendance.lesson_id == LID,
       models.Attendance.student_id == AID).first()), True)
ck("MUZLATILGANGA BELGI QO'YILMADI",
   bool(db.query(models.Attendance).filter(
       models.Attendance.lesson_id == LID,
       models.Attendance.student_id == MID).first()), False)
db.close()

print("\n=== 6. ERIGANDAN KEYIN HAMMA JOYDA QAYTADI ===")
db = SessionLocal()
db.query(models.Student).filter(models.Student.id == MID).update(
    {"status": "active"})
db.commit()
db.close()
d = client.get("/api/me/students", headers=ME).json()
ck("ro'yxatda", MID in [r["id"] for r in d["rows"]], True)
ck("muzlatilganlar soni 0", d.get("frozen"), 0)
a = client.get(f"/api/groups/{GID}/attendance"
               f"?year={TODAY.year}&month={TODAY.month}",
               headers=ME).json()
ck("DAVOMATDA ham qaytdi",
   MID in [x["id"] for x in a["students"]], True)

print("\n" + ("BARCHASI OK" if not fails else f"XATOLAR: {fails}"))
sys.exit(1 if fails else 0)
