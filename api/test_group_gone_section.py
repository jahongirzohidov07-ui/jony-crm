"""GURUHDAN O'CHIRILGANLAR ALOHIDA + ARXIVDAN O'CHIRISH FAQAT ASOSCHIGA
(2026-08-18).

Jahongir: "guruhdan ochirilgan talaba bu yerda turmasin, bunaqa bolib.
Pastda alohida guruhdan ochirilganlar bolimi tursa osha yerdni
bossagina alohida chiqsin bosilmasa chiqmasin keyin arxivdagilarni
ochirishni faqatgina menga asoschiga ruxsatini ber".
"""
import os, sys
from datetime import date
os.environ["DATABASE_URL"] = "sqlite:////tmp/gonesec.db"
if os.path.exists("/tmp/gonesec.db"):
    os.remove("/tmp/gonesec.db")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                         # noqa: E402
import entry                                       # noqa: E402
from database import SessionLocal                  # noqa: E402
from auth import hash_password                     # noqa: E402

c = TestClient(main.app)
fails = []


def ck(n, g, w):
    ok = g == w
    print(("OK  " if ok else "MUAMMO ") + n + f": {g}"
          + ("" if ok else f" (kutilgan {w})"))
    if not ok:
        fails.append(n)


db = SessionLocal()
b = models.Branch(name="Bekobod 2"); db.add(b); db.commit(); BID = b.id
t = models.Teacher(full_name="Sardor", branch_id=BID); db.add(t); db.commit()
g = models.Group(name="New", branch_id=BID, teacher_id=t.id,
                 lesson_price=40000, standard_lessons_per_month=12,
                 monthly_fee=480000)
db.add(g); db.commit(); GID = g.id

aktiv = models.Student(full_name="Faol Bola", branch_id=BID,
                       group_id=GID, status="active")
arxiv = models.Student(full_name="Arxiv Bola", branch_id=BID,
                       group_id=GID, status="archived")
arxiv_iz = models.Student(full_name="Arxiv Izli", branch_id=BID,
                          group_id=GID, status="archived")
db.add_all([aktiv, arxiv, arxiv_iz]); db.commit()
A, X, XI = aktiv.id, arxiv.id, arxiv_iz.id

# Arxiv Izlining shu oyda BITTA yo'qlamasi bor — tarixi ko'rinishi kerak
ls = models.Lesson(group_id=GID, date=date.today(), held=1)
db.add(ls); db.commit()
db.add(models.Attendance(lesson_id=ls.id, student_id=XI, present=1))
db.add(models.User(username="asos", full_name="Asoschi",
                   password_hash=hash_password("x"), role=roles.FOUNDER,
                   branch_id=BID))
db.add(models.User(username="adm", full_name="Admin",
                   password_hash=hash_password("x"),
                   role=roles.ADMINISTRATOR, branch_id=BID))
db.commit(); db.close()


def tok(u):
    return c.post("/api/auth/login",
                  json={"username": u, "password": "x"}).json()["access_token"]


AS = {"Authorization": f"Bearer {tok('asos')}"}
AD = {"Authorization": f"Bearer {tok('adm')}"}

# ---------------------------------------------------------------- 1
print("\n=== 1. Guruh ro'yxatida arxivdagilar TURMAYDI ===")
r = c.get(f"/api/students?group_id={GID}", headers=AS).json()
ck("faqat faol bola", [x["full_name"] for x in r], ["Faol Bola"])

# ---------------------------------------------------------------- 2
print("\n=== 2. 'O'chirilganlar' faqat so'ralganda keladi ===")
r = c.get(f"/api/students?group_id={GID}&left=1", headers=AS).json()
ck("2 ta o'chirilgan", sorted(x["full_name"] for x in r),
   ["Arxiv Bola", "Arxiv Izli"])
ck("faol bola bu ro'yxatda YO'Q",
   any(x["id"] == A for x in r), False)

# ---------------------------------------------------------------- 3
print("\n=== 3. Davomat jadvali ===")
today = date.today()
r = c.get(f"/api/groups/{GID}/attendance?year={today.year}"
          f"&month={today.month}", headers=AS).json()
names = {x["full_name"]: x["status"] for x in r["students"]}
ck("faol bola ODATIY qator", names.get("Faol Bola"), "active")
ck("izsiz arxiv UMUMAN chiqmaydi", "Arxiv Bola" in names, False)

# 2026-08-20 (Jahongir): "pastiga ketganlar va muzaltilganlarni
# daovmatini korsatish degan tugmani qoysak bosganda korinsin
# muzlatilganlar va ketganlarniki ham".
#
# Ya'ni odatiy jadval TOZA bo'ladi — faqat faollar. Ketganlar
# tugma bosilganda (others=1) qo'shiladi. Bu test o'sha tugma
# qo'shilishidan oldin yozilgan va eski holatni kutib qolgan edi
# (2026-09-21 da tuzatildi).
ck("tugmasiz izli arxiv ham chiqmaydi", "Arxiv Izli" in names, False)

r2 = c.get(f"/api/groups/{GID}/attendance?year={today.year}"
           f"&month={today.month}&others=1", headers=AS).json()
names2 = {x["full_name"]: x["status"] for x in r2["students"]}
ck("tugma bosilganda izli arxiv chiqadi",
   names2.get("Arxiv Izli"), "transferred")
ck("tugma bosilganda ham izsiz arxiv yo'q",
   "Arxiv Bola" in names2, False)
ck("faol bola tugmada ham joyida", names2.get("Faol Bola"), "active")

# Admin (rahbariyat emas deb emas — u ham ko'radi, lekin ustozda test
# qilish uchun teacher kerak emas; asosiy talab bajarildi)

# ---------------------------------------------------------------- 4
print("\n=== 4. Baholash jadvali ===")
r = c.get(f"/api/groups/{GID}/grades?year={today.year}"
          f"&month={today.month}", headers=AS).json()
gn = [x["full_name"] for x in r["students"]]
ck("arxivdagilar baholashda ham yo'q",
   "Arxiv Bola" in gn, False)

# ---------------------------------------------------------------- 5
print("\n=== 5. O'chirish faqat asoschiga ===")
r = c.delete(f"/api/students/{X}", headers=AD)
ck("admin o'chira olmaydi", r.status_code, 403)
db = SessionLocal()
ck("yozuv joyida", db.query(models.Student).get(X) is not None, True)
db.close()
r = c.delete(f"/api/students/{X}", headers=AS)
ck("asoschi o'chira oladi", r.status_code, 200)
db = SessionLocal()
ck("endi yo'q", db.query(models.Student).get(X), None)
a = (db.query(models.AuditLog)
     .filter(models.AuditLog.entity == "student",
             models.AuditLog.action == "delete",
             models.AuditLog.entity_id == X).count())
ck("o'chirish auditda qoldi", a, 1)
db.close()

print("\n" + ("HAMMASI JOYIDA" if not fails
              else f"MUAMMO: {len(fails)} ta -> {fails}"))
sys.exit(1 if fails else 0)
