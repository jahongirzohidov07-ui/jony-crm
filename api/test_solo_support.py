"""YAKKA SUPPORT DARSI: ORQADA QOLGAN O'QUVCHI (2026-09-23).

Jahongir: "o'zlashtirishi orqada qolgan o'quvchini ustoz biriktirib
bersa yo'qlamani qanday qo'yadi, u o'quvchiga qanaqa pul oladi".

Qaror: o'quvchi qo'shimcha pul to'lamaydi (chegara ham yo'q), support
esa yakka darsda soat uchun ikki barobar ball oladi.

Tekshiriladi:
  A. Ustoz o'z guruhidagi o'quvchini supportga biriktiradi, sababsiz
     biriktirib bo'lmaydi, begona guruhga aralasha olmaydi;
  B. Support o'ziga biriktirilganlarni ko'radi va darsni yozadi —
     bitta amalda yo'qlama ham, seans ham tushadi;
  C. "Kelmadi" belgilansa — seans yozilmaydi, pul hisoblanmaydi;
  D. Yakka dars soati ikki barobar ball beradi (0.60), guruh darsi
     esa eski qoidada (0.30) qoladi;
  E. O'quvchi hisobiga hech qanday to'lov yozilmaydi;
  F. Biriktirilmagan o'quvchiga dars yoza olmaydi, bir kunga ikki
     marta yozib bo'lmaydi.
"""
import os
import sys
import tempfile

_DB = os.path.join(tempfile.gettempdir(), "solo_support_test.db")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace("\\", "/")
if os.path.exists(_DB):
    os.remove(_DB)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                         # noqa: E402
import entry  # noqa: F401,E402
from database import SessionLocal                  # noqa: E402
from auth import hash_password                     # noqa: E402

client = TestClient(main.app)
fails = []


def ck(name, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + f"{name}: {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


def tok(u):
    return {"Authorization": "Bearer " + client.post(
        "/api/auth/login",
        json={"username": u, "password": "Parol123!"}
    ).json()["access_token"]}


TODAY = roles.local_today()

db = SessionLocal()
b = models.Branch(name="Zafar")
db.add(b)
db.commit()
BID = b.id
users = {}
for un, nm, role in [("asos", "Asoschi", roles.FOUNDER),
                     ("sup", "Support Aziza", roles.SUPPORT_TEACHER),
                     ("ust", "Ustoz Anvar", roles.TEACHER),
                     ("ust2", "Ustoz Botir", roles.TEACHER)]:
    u = models.User(username=un, full_name=nm,
                    password_hash=hash_password("Parol123!"),
                    role=role, branch_id=BID, is_active=1)
    db.add(u)
    db.commit()
    users[un] = u.id
st = models.Teacher(full_name="Support Aziza", branch_id=BID,
                    user_id=users["sup"], is_active=1)
t1 = models.Teacher(full_name="Ustoz Anvar", branch_id=BID,
                    user_id=users["ust"], is_active=1)
t2 = models.Teacher(full_name="Ustoz Botir", branch_id=BID,
                    user_id=users["ust2"], is_active=1)
db.add_all([st, t1, t2])
db.commit()
SUP_T = st.id
g1 = models.Group(name="Apex", subject="english", level="B1", branch_id=BID,
                  teacher_id=t1.id, lesson_time="18:00", monthly_fee=500000,
                  lesson_days="135", capacity=15)
g2 = models.Group(name="Nur", subject="english", level="B1", branch_id=BID,
                  teacher_id=t2.id, lesson_time="16:00", monthly_fee=500000,
                  lesson_days="24", capacity=15)
db.add_all([g1, g2])
db.commit()
GID, GID2 = g1.id, g2.id
s1 = models.Student(full_name="Aliyev Ali", branch_id=BID, group_id=GID,
                    status="active", enrolled_date=TODAY)
s2 = models.Student(full_name="Boboyev Bobur", branch_id=BID, group_id=GID2,
                    status="active", enrolled_date=TODAY)
db.add_all([s1, s2])
db.commit()
SID, SID2 = s1.id, s2.id
db.close()

H = tok("asos")
HS = tok("sup")
HT = tok("ust")


def balance(sid):
    d = SessionLocal()
    v = sum(p.amount for p in d.query(models.Payment)
            .filter(models.Payment.student_id == sid).all())
    d.close()
    return v


print("\n=== A. USTOZ BIRIKTIRADI ===")
r = client.post(f"/api/students/{SID}/support", headers=HT,
                json={"user_id": users["sup"], "days": "24",
                      "start": "14:00", "end": "15:00"})
ck("sababsiz biriktirilmaydi", r.status_code, 400)
r = client.post(f"/api/students/{SID}/support", headers=HT,
                json={"user_id": users["sup"], "days": "24",
                      "start": "14:00", "end": "15:00",
                      "note": "Unit 5 dan 40% oldi, grammatikasi orqada"})
ck("ustoz o'z o'quvchisini biriktirdi", r.status_code, 200)
ck("begona guruhdagi o'quvchiga aralasha olmaydi",
   client.post(f"/api/students/{SID2}/support", headers=HT,
               json={"user_id": users["sup"], "note": "x"}).status_code, 403)
ck("ikki marta biriktirib bo'lmaydi",
   client.post(f"/api/students/{SID}/support", headers=HT,
               json={"user_id": users["sup"], "note": "yana"}).status_code,
   400)
d = client.get(f"/api/students/{SID}/support", headers=HT).json()
ck("kartada ko'rinadi", d["rows"][0]["support"], "Support Aziza")
ck("kun va vaqti saqlandi",
   (d["rows"][0]["days"], d["rows"][0]["start"]), ("24", "14:00"))

print("\n=== B. SUPPORT DARSNI YOZADI ===")
d = client.get("/api/me/support-solo", headers=HS).json()
ck("supportga ko'rinadi", [x["name"] for x in d["rows"]], ["Aliyev Ali"])
ck("guruhi ham ko'rinadi", d["rows"][0]["group"], "Apex")
r = client.post(f"/api/me/support-solo/{SID}/lesson", headers=HS,
                json={"present": True})
ck("dars yozildi", r.status_code, 200)
ck("assignmentdagi vaqtdan 1 soat olindi", r.json()["hours"], 1.0)
d = client.get("/api/me/support-solo", headers=HS).json()["rows"][0]
ck("yo'qlama belgisi qo'yildi", d["done"], 1)
dbx = SessionLocal()
ses = dbx.query(models.SupportSession).filter(
    models.SupportSession.student_id == SID).all()
ck("seans ham yozildi", len(ses), 1)
ck("seansda bitta o'quvchi", ses[0].students_count, 1)
ck("yakka dars deb belgilandi", bool(ses[0].student_id), True)
att = dbx.query(models.SupportAttendance).filter(
    models.SupportAttendance.student_id == SID).all()
ck("yo'qlama alohida jadvalda", len(att), 1)
ck("ustoz yo'qlamasiga tegmadi",
   dbx.query(models.Attendance).count(), 0)
dbx.close()

print("\n=== C. O'QUVCHI PUL TO'LAMAYDI ===")
ck("hisobiga hech narsa yozilmadi", balance(SID), 0)

print("\n=== D. YAKKA DARS SOATI IKKI BAROBAR ===")
ck("1 soat yakka = 0.60 ball",
   roles.support_hours_points(1, 1), 0.6)
ck("1 soat 3 kishi = hali ham yakka", roles.support_hours_points(1, 3), 0.6)
ck("1 soat 4 kishi = guruh qoidasi", roles.support_hours_points(1, 4), 0.3)
sal = client.get("/api/me/support-sessions", headers=HS).json()
ck("oylikda yakka soat ko'rinadi", sal["solo_hours"], 1.0)
ck("soat bali 0.60", sal["hours_part"], 0.6)
ck("yakka darslar soni", sal["solo_count"], 1)
# Yakka dars 3 kishilik darsdek sanaladi (2026-09-23)
ck("hisobotda o'quvchi soni o'zgarmaydi", sal["students"], 1)
ck("oylikda esa 3 o'quvchidek", sal["students_points"], 3)
ck("o'quvchi bali 3 x 0.20", sal["students_part"], 0.6)
# Ish ballari (natija koeffitsiyenti bundan tashqari qo'shiladi)
ck("1 soatlik yakka dars = 1.2 ball (0.60 + 0.60)",
   round(sal["hours_part"] + sal["students_part"], 2), 1.2)
# Guruh darsi qo'shilsa — u eski qoidada (0.30)
client.post("/api/me/support-sessions", headers=HS,
            json={"group_id": GID, "start_time": "10:00", "hours": 2,
                  "students_count": 8})
sal = client.get("/api/me/support-sessions", headers=HS).json()
ck("jami 3 soat", sal["hours"], 3.0)
ck("ball: yakka 1x0.60 + guruh 2x0.30 = 1.2", sal["hours_part"], 1.2)
ck("o'quvchi: yakka 3 + guruh 8 = 11", sal["students_points"], 11)
ck("o'quvchi bali 11 x 0.20", sal["students_part"], 2.2)
ck("formulada ikkalasi ham ko'rinadi",
   "yakka soat" in sal["formula"], True)

print("\n=== E. KELMADI: PUL YOZILMAYDI ===")
dbx = SessionLocal()
dbx.query(models.SupportAttendance).delete()
dbx.query(models.SupportSession).filter(
    models.SupportSession.student_id == SID).delete()
dbx.commit()
dbx.close()
r = client.post(f"/api/me/support-solo/{SID}/lesson", headers=HS,
                json={"present": False})
ck("kelmadi yozildi", r.status_code, 200)
dbx = SessionLocal()
ck("belgi qo'yildi", dbx.query(models.SupportAttendance).count(), 1)
ck("seans yozilmadi", dbx.query(models.SupportSession).filter(
    models.SupportSession.student_id == SID).count(), 0)
dbx.close()

print("\n=== F. CHEGARALAR ===")
ck("biriktirilmagan o'quvchiga yoza olmaydi",
   client.post(f"/api/me/support-solo/{SID2}/lesson", headers=HS,
               json={"present": True}).status_code, 403)
client.post(f"/api/me/support-solo/{SID}/lesson", headers=HS,
            json={"present": True})
ck("bir kunga ikki marta yozilmaydi",
   client.post(f"/api/me/support-solo/{SID}/lesson", headers=HS,
               json={"present": True}).status_code, 400)
ck("kelajakka yozilmaydi",
   client.post(f"/api/me/support-solo/{SID}/lesson", headers=HS,
               json={"present": True,
                     "date": (TODAY.replace(day=28)).isoformat()
                     if TODAY.day < 28 else "2099-01-01"}).status_code, 400)
ck("ustoz biriktirishni olib tashlaydi",
   client.delete(f"/api/students/{SID}/support/"
                 f"{client.get(f'/api/students/{SID}/support', headers=HT).json()['rows'][0]['id']}",
                 headers=HT).status_code, 200)

print()
if fails:
    print("XATOLAR:", ", ".join(fails))
    sys.exit(1)
print("HAMMASI O'TDI")
