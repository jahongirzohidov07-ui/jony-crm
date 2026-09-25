"""USTOZDAN ERKIN DARS SURISH OLIB TASHLANDI (2026-09-24).

Jahongir: "o'qituvchilardan erkin darsni surishni olib tashla".

Ilgari ustoz oyiga ikki marta hech kimdan so'ramay dars ko'chira
olardi — so'rov "avtomat" bo'lib o'sha zahoti kuchga kirardi.

Tekshiriladi:
  A. Ustozning birinchi so'rovi ham DARHOL kuchga kirmaydi — tasdiq
     kutadi va dars eski kunida qoladi;
  B. Guruh sahifasidan (jadval menyusi) ham xuddi shunday;
  C. O'quv bo'limi tasdiqlagach dars ko'chadi;
  D. Rahbariyat avvalgidek to'g'ridan-to'g'ri ko'chiraveradi;
  E. Ustozga ko'rsatiladigan matn "avtomat ruxsat" demaydi.
"""
import os
import sys
import tempfile
from datetime import timedelta

_DB = os.path.join(tempfile.gettempdir(), "no_free_move_test.db")
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
for un, nm, role in [("asos", "Asoschi", roles.FOUNDER),
                     ("oquv", "O'quv rahbari", roles.ACADEMIC_HEAD),
                     ("ust", "Ustoz Anvar", roles.TEACHER)]:
    db.add(models.User(username=un, full_name=nm,
                       password_hash=hash_password("Parol123!"),
                       role=role, branch_id=BID, is_active=1))
db.commit()
u = db.query(models.User).filter(models.User.username == "ust").first()
UST_ID = u.id
t = models.Teacher(full_name="Ustoz Anvar", branch_id=BID, user_id=u.id,
                   is_active=1)
db.add(t)
db.commit()
g = models.Group(name="Apex", subject="english", level="B1", branch_id=BID,
                 teacher_id=t.id, lesson_time="18:00-19:30",
                 monthly_fee=500000, lesson_days="mon,wed,fri",
                 capacity=15)
db.add(g)
db.commit()
GID = g.id
# Kelasi haftadagi dars — ogohlantirish muddatidan uzoqroq
FROM = TODAY + timedelta(days=10)
TO = FROM + timedelta(days=1)
# held=0: hali o'tilmagan dars (o'tilganini ko'chirib bo'lmaydi)
les = models.Lesson(group_id=GID, date=FROM, held=0)
db.add(les)
db.commit()
db.close()

H = tok("asos")
HO = tok("oquv")
HT = tok("ust")


def lesson_dates():
    d = SessionLocal()
    v = sorted(x.date.isoformat() for x in d.query(models.Lesson)
               .filter(models.Lesson.group_id == GID).all())
    d.close()
    return v


print("\n=== A. USTOZNING BIRINCHI SO'ROVI HAM TASDIQ KUTADI ===")
r = client.post(f"/api/groups/{GID}/reschedule", headers=HT, json={
    "from_date": FROM.isoformat(), "to_date": TO.isoformat(),
    "reason": "sick", "note": "Kasal bo'lib qoldim"})
ck("so'rov qabul qilindi", r.status_code, 200)
d = r.json()
ck("darhol qo'llanmadi", d["applied"], False)
ck("holati tasdiq kutmoqda", d["status"], "pending")
ck("matnda kvota haqida gap yo'q", "Kvota" in d["message"], False)
ck("dars hali eski kunida", FROM.isoformat() in lesson_dates(), True)
ck("yangi kunga dars qo'shilmadi", TO.isoformat() in lesson_dates(), False)

print("\n=== B. KVOTA MATNI O'ZGARDI ===")
box = client.get(f"/api/groups/{GID}/attendance?year={TODAY.year}"
                 f"&month={TODAY.month}", headers=HT).json()["reschedule"]
ck("avtomat ruxsat o'chirilgan", box["quota"]["auto_ok"], False)
ck("bayroq ko'rinadi", box["quota"]["teacher_auto"], False)
ck("izohda tasdiq haqida aytilgan",
   "tasdig'idan o'tadi" in (box["hint"] or ""), True)
me = client.get("/api/me/reschedules", headers=HT).json()
ck("ustoz ilovasida ham avtomat yo'q", me["quota"]["auto_ok"], False)
ck("ustoz ilovasidagi izoh",
   "tasdig'idan" in me["hint"], True)

print("\n=== C. O'QUV BO'LIMI TASDIQLAGACH KO'CHADI ===")
rid = d["id"]
r = client.post(f"/api/reschedules/{rid}/decide", headers=HO,
                json={"decision": "approved"})
ck("tasdiqlandi", r.status_code, 200)
ck("endi yangi kunda dars bor", TO.isoformat() in lesson_dates(), True)
ck("eski kundan olindi", FROM.isoformat() in lesson_dates(), False)

print("\n=== C2. USTOZGA XABAR BORDI ===")
d2 = SessionLocal()
tasks = list(d2.query(models.Task)
             .filter(models.Task.assignee_id == UST_ID).all())
d2.close()
ck("ustozga vazifa tushdi", len(tasks), 1)
ck("sarlavhada qaror bor", "TASDIQLANDI" in tasks[0].title, True)
ck("matnda yangi sana bor", TO.isoformat() in tasks[0].description, True)
ck("nima qilish kerakligi yozilgan",
   "ogohlantiring" in tasks[0].description, True)

print("\n=== D. RAHBARIYATGA TEGILMADI ===")
FROM2 = TO
TO2 = FROM2 + timedelta(days=2)
r = client.post(f"/api/groups/{GID}/reschedule", headers=H, json={
    "from_date": FROM2.isoformat(), "to_date": TO2.isoformat(),
    "reason": "other", "note": "Jadval tuzatildi"})
ck("asoschi so'rovi darrov qo'llandi", r.json()["applied"], True)
ck("dars ko'chdi", TO2.isoformat() in lesson_dates(), True)

print("\n=== E. RAD ETILSA HAM XABAR BORADI ===")
FROM3 = TO2 + timedelta(days=3)
d3 = SessionLocal()
d3.add(models.Lesson(group_id=GID, date=FROM3, held=0))
d3.commit()
d3.close()
r = client.post(f"/api/groups/{GID}/reschedule", headers=HT, json={
    "from_date": FROM3.isoformat(),
    "to_date": (FROM3 + timedelta(days=1)).isoformat(),
    "reason": "family", "note": "Oilaviy sabab"})
rid2 = r.json()["id"]
client.post(f"/api/reschedules/{rid2}/decide", headers=HO,
            json={"decision": "rejected", "note": "O'sha kuni xona band"})
d4 = SessionLocal()
tt = list(d4.query(models.Task)
          .filter(models.Task.assignee_id == UST_ID).all())
d4.close()
ck("ikkinchi xabar ham bor", len(tt), 2)
rej = [x for x in tt if "RAD ETILDI" in x.title]
ck("rad etilgani aytildi", len(rej), 1)
ck("sababi yozilgan", "xona band" in rej[0].description, True)
ck("eski kunida qolishi aytilgan",
   "ESKI kunida qoladi" in rej[0].description, True)

print()
if fails:
    print("XATOLAR:", ", ".join(fails))
    sys.exit(1)
print("HAMMASI O'TDI")
