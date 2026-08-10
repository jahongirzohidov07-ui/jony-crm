"""KELMAGAN O'QUVCHIGA BAHO/COIN QO'YILMASLIGI + MUZLATILGAN
O'QUVCHI USTOZGA KO'RINMASLIGI (2026-08-10).

Jahongir: "kelmagan o'quvchilarga baho qo'yib coin qo'yib bo'lyabdi,
qo'yib bo'lmasin. Muzlatilgan o'quvchilar o'qituvchilarga
ko'rinmasin, yo'qlama baho qo'yib bo'lmasin."

TESHIK QAYERDA EDI: yangi baho qo'yishda tekshiruv BOR edi
(kelmaganga baho qo'yib bo'lmasdi). Lekin ustoz avval "keldi" deb
belgilab BAHO QO'YSA, keyin "yo'q"ga o'zgartirsa — baho ham, coin
ham bazada QOLIB KETARDI. Endi belgi "kelmadi"ga o'zgarganda o'sha
darsdagi baho va coin avtomat qaytariladi."""
import os, sys
from datetime import date

os.environ["DATABASE_URL"] = "sqlite:////tmp/vang/db.sqlite"
os.makedirs("/tmp/vang", exist_ok=True)
if os.path.exists("/tmp/vang/db.sqlite"):
    os.remove("/tmp/vang/db.sqlite")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
import main, models, roles
import entry  # noqa
from database import SessionLocal
from auth import hash_password

c = TestClient(main.app)
db = SessionLocal()
fails = []


def ck(n, g, w):
    ok = g == w
    print(("OK  " if ok else "XATO ") + f"{n}: {g}" + ("" if ok else f"  (kutilgan {w})"))
    if not ok:
        fails.append(n)


def coins(sid):
    return sum(x.amount for x in db.query(models.CoinEntry)
               .filter(models.CoinEntry.student_id == sid).all())


b = models.Branch(name="Zafar"); db.add(b); db.commit()
ut = models.User(username="ust", full_name="Ustoz",
                 password_hash=hash_password("Parol123!"),
                 role=roles.TEACHER, branch_id=b.id, is_active=1)
db.add(ut); db.commit()
t = models.Teacher(full_name="Ustoz", branch_id=b.id, user_id=ut.id,
                   is_active=1)
db.add(t); db.commit()
g = models.Group(name="G1", subject="english", level="step1",
                 branch_id=b.id, teacher_id=t.id, lesson_time="09:00",
                 monthly_fee=500000, lesson_days="mon,wed,fri", capacity=15)
db.add(g); db.commit()

today = roles.local_today()
s1 = models.Student(full_name="Kelgan Bola", branch_id=b.id, group_id=g.id,
                    status="active", enrolled_date=today, public_id="S1")
s2 = models.Student(full_name="Muzlagan Bola", branch_id=b.id, group_id=g.id,
                    status="frozen", enrolled_date=today, public_id="S2")
db.add_all([s1, s2]); db.commit()
ls = models.Lesson(group_id=g.id, date=today, teacher_id=ut.id, held=0)
db.add(ls); db.commit()

H = {"Authorization": f"Bearer {c.post('/api/auth/login', json={'username':'ust','password':'Parol123!'}).json()['access_token']}"}

print("=== 1. KELDI -> BAHO QO'YILADI ===")
r = c.put(f"/api/lessons/{ls.id}/attendance", headers=H,
          json={"marks": [{"student_id": s1.id, "present": True,
                           "late": False}]})
ck("yo'qlama saqlandi", r.status_code, 200)
r = c.put(f"/api/lessons/{ls.id}/grades", headers=H,
          json={"marks": [{"student_id": s1.id, "score": 5}]})
ck("kelgan o'quvchiga baho qo'yildi", r.status_code, 200)
ck("baho bazada bor",
   db.query(models.DailyGrade).filter(
       models.DailyGrade.student_id == s1.id).count(), 1)
ck("coin ham berildi (5)", coins(s1.id), 5)

print("\n=== 2. ENDI 'KELMADI'GA O'ZGARTIRILDI (asosiy teshik) ===")
r = c.put(f"/api/lessons/{ls.id}/attendance", headers=H,
          json={"marks": [{"student_id": s1.id, "present": False,
                           "late": False}]})
ck("belgi o'zgartirildi", r.status_code, 200)
ck("BAHO O'CHIRILDI",
   db.query(models.DailyGrade).filter(
       models.DailyGrade.student_id == s1.id).count(), 0)
ck("COIN QAYTARILDI", coins(s1.id), 0)

print("\n=== 3. KELMAGANGA YANGI BAHO QO'YIB BO'LMAYDI ===")
r = c.put(f"/api/lessons/{ls.id}/grades", headers=H,
          json={"marks": [{"student_id": s1.id, "score": 5}]})
ck("rad etiladi", r.status_code, 400)
ck("sabab tushuntirilgan",
   "kelmagan" in str(r.json()["detail"]).lower(), True)
ck("coin baribir 0", coins(s1.id), 0)

print("\n=== 4. MUZLATILGAN O'QUVCHI ===")
r = c.get("/api/me/students", headers=H)
names = [x["full_name"] for x in r.json()["rows"]]
ck("ustozning ro'yxatida muzlatilgan YO'Q", "Muzlagan Bola" in names, False)
ck("faol o'quvchi esa bor", "Kelgan Bola" in names, True)

r = c.get(f"/api/groups/{g.id}/attendance?year={today.year}&month={today.month}",
          headers=H)
ids = [x["id"] for x in r.json()["students"]]
ck("davomat jadvalida ham yo'q", s2.id in ids, False)

r = c.get(f"/api/groups/{g.id}/grades?year={today.year}&month={today.month}",
          headers=H)
ids2 = [x["id"] for x in r.json()["students"]]
ck("baho jadvalida ham yo'q", s2.id in ids2, False)

before_att = db.query(models.Attendance).filter(
    models.Attendance.student_id == s2.id).count()
c.put(f"/api/lessons/{ls.id}/attendance", headers=H,
      json={"marks": [{"student_id": s2.id, "present": True, "late": False}]})
ck("muzlatilganga yo'qlama yozilmaydi",
   db.query(models.Attendance).filter(
       models.Attendance.student_id == s2.id).count(), before_att)

c.put(f"/api/lessons/{ls.id}/grades", headers=H,
      json={"marks": [{"student_id": s2.id, "score": 5}]})
ck("muzlatilganga baho ham yozilmaydi",
   db.query(models.DailyGrade).filter(
       models.DailyGrade.student_id == s2.id).count(), 0)
ck("muzlatilganga coin ham yo'q", coins(s2.id), 0)

print("\n" + ("BARCHASI OK" if not fails else f"XATOLAR: {fails}"))
sys.exit(1 if fails else 0)
