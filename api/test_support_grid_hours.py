"""SUPPORT YO'QLAMASI USTOZNIKIDEK + QO'LDA SOAT (2026-08-10).

Jahongir: "ha ustoznikiday va unga qo'shimcha ravishda qancha dars
o'tganligini qo'lda belgilaydigan bo'lishi kerak."

Telefondagi support ekrani endi PUT /groups/{id}/support-attendance
orqali per-o'quvchi belgi + soat yuboradi. Tekshiriladi: seans soati
aynan support tanlagan soat bo'lishi, 1-3 chegara, seansning
yo'qlamadan avtomat sinxronlanishi va USTOZNING ASOSIY YO'QLAMASIGA
umuman tegmasligi."""
import os, sys
from datetime import date, timedelta

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_sgh/db.sqlite"
os.makedirs("/tmp/verify_sgh", exist_ok=True)
if os.path.exists("/tmp/verify_sgh/db.sqlite"):
    os.remove("/tmp/verify_sgh/db.sqlite")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
import main, models, roles
import entry  # noqa: F401
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
today = roles.local_today()
WD = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"][today.weekday()]

sup = models.User(username="sup", full_name="Dilnoza Support",
                  password_hash=hash_password("Parol123!"),
                  role=roles.SUPPORT_TEACHER, branch_id=b.id, is_active=1)
db.add(sup); db.commit()
st = models.Teacher(full_name="Dilnoza Support", branch_id=b.id,
                    user_id=sup.id, is_active=1)
db.add(st); db.commit()

ustu = models.User(username="ust", full_name="Ustoz",
                   password_hash=hash_password("Parol123!"),
                   role=roles.TEACHER, branch_id=b.id, is_active=1)
db.add(ustu); db.commit()
t = models.Teacher(full_name="Ustoz", branch_id=b.id, user_id=ustu.id,
                   is_active=1)
db.add(t); db.commit()

# Asosiy dars boshqa kunlarda - support seansi bilan to'qnashmasin
other = [d for d in ("mon", "tue", "wed", "thu", "fri", "sat")
         if d != WD][:2]
g = models.Group(name="IELTS-S", subject="english", level="step1",
                 branch_id=b.id, teacher_id=t.id, lesson_time="09:00",
                 monthly_fee=500000, lesson_days=",".join(other),
                 capacity=15)
db.add(g); db.commit()

# Support biriktirish: BUGUNGI hafta kuni, 14:00-15:00
db.add(models.SupportAssignment(user_id=sup.id, group_id=g.id,
                                days=WD, start="14:00", end="15:00"))
db.commit()

sts = []
for i, nm in enumerate(("Ali Valiyev", "Bahrom Aliyev", "Kamola Umarova")):
    s = models.Student(full_name=nm, branch_id=b.id, group_id=g.id,
                       status="active", enrolled_date=today,
                       public_id=f"STU-SG-{i}")
    db.add(s); db.commit(); sts.append(s)


def H(u):
    r = c.post("/api/auth/login", json={"username": u,
                                        "password": "Parol123!"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


Hs = H("sup")

print("=== JADVAL OCHILADI ===")
r = c.get(f"/api/groups/{g.id}/support-attendance"
          f"?year={today.year}&month={today.month}", headers=Hs)
ck("status 200", r.status_code, 200)
d0 = r.json()
ck("bugun support kuni ro'yxatda", today.isoformat() in d0["days"], True)
ck("3 o'quvchi ko'rinadi", len(d0["students"]), 3)
ck("tahrirlash ochiq", d0["can_edit"], True)
ck("standart vaqt keladi", d0["default_start"], "14:00")

print("\n=== USTOZNIKIDEK BELGILASH + QO'LDA SOAT (1.5) ===")
r = c.put(f"/api/groups/{g.id}/support-attendance", headers=Hs,
          json={"day": today.isoformat(),
                "marks": [
                    {"student_id": sts[0].id, "present": True},
                    {"student_id": sts[1].id, "present": True,
                     "late": True},
                    {"student_id": sts[2].id, "present": False},
                ],
                "start_time": "14:00", "hours": 1.5})
ck("saqlash 200", r.status_code, 200)
j = r.json()
ck("seans yaratildi", j.get("session") is not None, True)
ck("SOAT AYNAN TANLANGANIDEK (1.5)", j["session"]["hours"], 1.5)
ck("tugash vaqti hisoblandi (15:30)", j["session"]["end"], "15:30")
ck("kelganlar 2 ta (kech ham kelgan)", j["session"]["students"], 2)

print("\n=== JADVALDA KO'RINADI ===")
r = c.get(f"/api/groups/{g.id}/support-attendance"
          f"?year={today.year}&month={today.month}", headers=Hs)
d1 = r.json()
mk = d1["marks"]
ck("Ali keldi", mk.get(f"{today.isoformat()}:{sts[0].id}"), True)
ck("Bahrom kech", mk.get(f"{today.isoformat()}:{sts[1].id}"), 2)
ck("Kamola yo'q", mk.get(f"{today.isoformat()}:{sts[2].id}"), False)
ck("oy jami soati 1.5", d1["hours_total"], 1.5)

print("\n=== 1-3 CHEGARASI BU YO'LDA HAM ===")
r = c.put(f"/api/groups/{g.id}/support-attendance", headers=Hs,
          json={"day": today.isoformat(),
                "marks": [{"student_id": sts[0].id, "present": True}],
                "start_time": "14:00", "hours": 0.5})
ck("0.5 soat rad etiladi", r.status_code, 400)
r = c.put(f"/api/groups/{g.id}/support-attendance", headers=Hs,
          json={"day": today.isoformat(),
                "marks": [{"student_id": sts[0].id, "present": True}],
                "start_time": "14:00", "hours": 3.5})
ck("3.5 soat rad etiladi", r.status_code, 400)

print("\n=== SOAT O'ZGARTIRILSA SEANS YANGILANADI (2) ===")
r = c.put(f"/api/groups/{g.id}/support-attendance", headers=Hs,
          json={"day": today.isoformat(), "marks": [],
                "start_time": "14:00", "hours": 2})
ck("saqlash 200", r.status_code, 200)
ck("soat endi 2", r.json()["session"]["hours"], 2.0)

print("\n=== USTOZNING ASOSIY YO'QLAMASIGA TEGILMAGAN ===")
ck("attendance jadvali BO'SH",
   db.query(models.Attendance).count(), 0)
ck("lessons jadvali BO'SH",
   db.query(models.Lesson).count(), 0)
ck("support yozuvi support jadvalida", db.query(
    models.SupportAttendance).count(), 3)

print("\n=== HAMMA BELGI OLIB TASHLANSA SEANS O'CHADI ===")
r = c.put(f"/api/groups/{g.id}/support-attendance", headers=Hs,
          json={"day": today.isoformat(),
                "marks": [{"student_id": s.id, "remove": True}
                          for s in sts]})
ck("saqlash 200", r.status_code, 200)
ck("seans o'chdi", r.json().get("session"), None)
ck("seans bazada ham yo'q",
   db.query(models.SupportSession).count(), 0)

print("\n=== KELAJAK KUNGA YOZIB BO'LMAYDI ===")
fut = today + timedelta(days=7)
r = c.put(f"/api/groups/{g.id}/support-attendance", headers=Hs,
          json={"day": fut.isoformat(),
                "marks": [{"student_id": sts[0].id, "present": True}],
                "hours": 1})
ck("kelajak bloklanadi", r.status_code, 400)

print("\n" + ("BARCHASI OK" if not fails else f"XATOLAR: {fails}"))
sys.exit(1 if fails else 0)
