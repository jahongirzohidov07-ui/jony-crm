"""MUZLATISH HISOBI: YO'QLAMASI BOR DARSLAR TUSHIB QOLMASIN (2026-08-18).

Jahongir: "muzlatishda abdullayeva Muhlisa 5ta dars kelgan lekin men
muzlatiladigan sanani tanlasam 3ta darsga hisoblayabdi nega".

Sabab: hisob "qo'shilgan sana"dan boshlanardi. O'quvchi guruhga 6-avgust
deb rasmiylashtirilgan, lekin 1 va 4-avgust darslarida ham yo'qlamasi
bor edi — o'sha ikkitasi hisobdan tushib qolgan (5 o'rniga 3).

Yangi qoida: yo'qlama belgisi bor dars — qo'shilgan sanadan qat'i
nazar hisobga kiradi. Belgisiz darslar avvalgidek faqat qo'shilgan
sanadan keyin.
"""
import os, sys
from datetime import date
os.environ["DATABASE_URL"] = "sqlite:////tmp/fzprev.db"
if os.path.exists("/tmp/fzprev.db"):
    os.remove("/tmp/fzprev.db")
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


T = date.today()
Y, M_ = T.year, T.month

db = SessionLocal()
b = models.Branch(name="Bekobod 2"); db.add(b); db.commit()
t = models.Teacher(full_name="Asliddin", branch_id=b.id)
db.add(t); db.commit()
g = models.Group(name="Yangi", branch_id=b.id, teacher_id=t.id,
                 lesson_price=40000, standard_lessons_per_month=12,
                 monthly_fee=480000)
db.add(g); db.commit()

# Muhlisa: guruhga 6-kuni RASMIYLASHTIRILGAN, lekin 1 va 4 dagi
# darslarda ham yo'qlamasi bor
s = models.Student(full_name="Abdullaeva Muhlisa", branch_id=b.id,
                   group_id=g.id, status="active",
                   enrolled_date=date(Y, M_, 6))
db.add(s); db.commit()

days = [1, 4, 6, 8, 9]
for d in days:
    L = models.Lesson(group_id=g.id, date=date(Y, M_, d), held=1)
    db.add(L); db.flush()
    db.add(models.Attendance(lesson_id=L.id, student_id=s.id, present=1))
db.commit()
SID = s.id
db.add(models.User(username="asos", full_name="Asoschi",
                   password_hash=hash_password("x"), role=roles.FOUNDER,
                   branch_id=b.id))
db.commit(); db.close()
tok = c.post("/api/auth/login",
             json={"username": "asos", "password": "x"}).json()["access_token"]
H = {"Authorization": f"Bearer {tok}"}

# ---------------------------------------------------------------- 1
print("\n=== 1. 10-kundan muzlatish: 5 ta dars (3 emas!) ===")
r = c.get(f"/api/students/{SID}/freeze-preview?from_date="
          f"{Y}-{M_:02d}-10", headers=H).json()
ck("darslar soni 5", r["lessons"], 5)
ck("summa 200 000", r["target"], 200000)

# ---------------------------------------------------------------- 2
print("\n=== 2. Belgisiz dars qo'shilgan sanadan OLDIN — hisobga kirmaydi ===")
db = SessionLocal()
GID2 = db.query(models.Group).first().id
L = models.Lesson(group_id=GID2, date=date(Y, M_, 2), held=1)
db.add(L); db.commit(); db.close()   # 2-kunda dars bor, lekin belgisi yo'q
r = c.get(f"/api/students/{SID}/freeze-preview?from_date="
          f"{Y}-{M_:02d}-10", headers=H).json()
ck("baribir 5 (2-kun belgisiz, 6-dan oldin)", r["lessons"], 5)

# ---------------------------------------------------------------- 3
print("\n=== 3. Muzlatish kunidagi dars: faqat KELGAN bo'lsa ===")
db = SessionLocal()
L10 = models.Lesson(group_id=db.query(models.Group).first().id,
                    date=date(Y, M_, 10), held=1)
db.add(L10); db.flush()
db.add(models.Attendance(lesson_id=L10.id, student_id=SID, present=0))
db.commit(); db.close()
r = c.get(f"/api/students/{SID}/freeze-preview?from_date="
          f"{Y}-{M_:02d}-10", headers=H).json()
ck("kelmagan — qo'shilmadi", r["lessons"], 5)

# ---------------------------------------------------------------- 4
print("\n=== 4. Oddiy o'quvchi (oy boshidan) — o'zgarmagan ===")
db = SessionLocal()
s2 = models.Student(full_name="Oddiy Bola",
                    branch_id=db.query(models.Branch).first().id,
                    group_id=db.query(models.Group).first().id,
                    status="active",
                    enrolled_date=date(Y, M_, 1))
db.add(s2); db.commit(); S2 = s2.id; db.close()
r = c.get(f"/api/students/{S2}/freeze-preview?from_date="
          f"{Y}-{M_:02d}-10", headers=H).json()
# 1,2,4,6,8,9 - jami 6 ta o'tilgan dars (10 dagisi kelmagani uchun emas,
# belgisi yo'qligi uchun kirmaydi)
ck("oy boshidan hammasi", r["lessons"], 6)

print("\n" + ("HAMMASI JOYIDA" if not fails
              else f"MUAMMO: {len(fails)} ta -> {fails}"))
sys.exit(1 if fails else 0)
