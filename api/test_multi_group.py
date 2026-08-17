"""BITTA O'QUVCHI — KO'P GURUH, 1-BOSQICH (2026-08-17).

Jahongir: "Abduvaliyeva Munisa degan qiz 2ta gruppaga keladi, shuning
uchun ham biz ham bazda 2ta gruppa qilishimiz kerak" + "A) Bitta
o'quvchi — ko'p guruh (to'g'ri yo'l). shuni qil va balansni shoshmay
tur aytaman".

Shu sababli bu bosqichda PUL MANTIG'IGA TEGILMAYDI. Test aynan shuni
ham tekshiradi: oylik hisob o'zgarmagan bo'lishi kerak.
"""
import os, sys
from datetime import date
os.environ["DATABASE_URL"] = "sqlite:////tmp/multigroup.db"
if os.path.exists("/tmp/multigroup.db"):
    os.remove("/tmp/multigroup.db")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                         # noqa: E402
import entry                                       # noqa: E402
from database import SessionLocal                  # noqa: E402
from auth import hash_password                     # noqa: E402
from common import (student_group_ids, backfill_student_groups,  # noqa: E402
                    student_balance)

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
b2 = models.Branch(name="Zafar"); db.add(b2); db.commit(); BID2 = b2.id
g1 = models.Group(name="Rus tili", branch_id=BID, subject="rus",
                  lesson_price=60000, standard_lessons_per_month=8,
                  monthly_fee=480000)
g2 = models.Group(name="New", branch_id=BID, subject="ingliz",
                  lesson_price=60000, standard_lessons_per_month=8,
                  monthly_fee=480000)
g3 = models.Group(name="Zafar guruh", branch_id=BID2, lesson_price=50000,
                  standard_lessons_per_month=8, monthly_fee=400000)
db.add_all([g1, g2, g3]); db.commit()
G1, G2, G3 = g1.id, g2.id, g3.id
st = models.Student(full_name="Abduvalieva Munisa", branch_id=BID,
                    status="active", group_id=G1, phone="+998940411480",
                    enrolled_date=date(2026, 7, 7))
db.add(st); db.commit(); SID = st.id
db.add_all([
    models.User(username="asos", full_name="Asoschi", role="founder",
                password_hash=hash_password("x"), is_active=1),
    models.User(username="ust", full_name="Ustoz", role="teacher",
                branch_id=BID, password_hash=hash_password("x"),
                is_active=1),
])
db.commit(); db.close()


def tok(u_):
    return {"Authorization": "Bearer " + c.post(
        "/api/auth/login", json={"username": u_, "password": "x"})
        .json()["access_token"]}


F, T = tok("asos"), tok("ust")

print("=== 1. Eski yozuvlar bog'lanish jadvaliga ko'chadi ===")
db = SessionLocal()
n = backfill_student_groups(db)
ck("bitta bog'lanish yaratildi", n, 1)
ck("faol guruhi bitta", student_group_ids(db, SID), [G1])
ck("ikkinchi marta ishlaganda takrorlamaydi",
   backfill_student_groups(db), 0)
db.close()

print("\n=== 2. IKKINCHI guruhga qo'shish ===")
r = c.get(f"/api/students/{SID}/groups", headers=F)
ck("ro'yxat ochildi", r.status_code, 200)
ck("hozircha bitta", r.json()["active_count"], 1)
r = c.post(f"/api/students/{SID}/groups", headers=F, json={"group_id": G2})
ck("qo'shildi", r.status_code, 200)
ck("endi ikkita", r.json()["active_count"], 2)
r = c.post(f"/api/students/{SID}/groups", headers=F, json={"group_id": G2})
ck("ikki marta qo'shib bo'lmaydi", r.status_code, 400)
r = c.post(f"/api/students/{SID}/groups", headers=F, json={"group_id": G3})
ck("boshqa filial guruhi rad etiladi", r.status_code, 400)
r = c.post(f"/api/students/{SID}/groups", headers=F, json={})
ck("guruhsiz so'rov rad etiladi", r.status_code, 400)

print("\n=== 3. IKKALA GURUHDA HAM ko'rinadi (asosiy muammo) ===")
for gid, nom in ((G1, "Rus tili"), (G2, "New")):
    rows = c.get(f"/api/students?group_id={gid}", headers=F).json()
    ck(f"{nom} ro'yxatida bor",
       any(x["id"] == SID for x in rows), True)
ck("asosiy guruh o'zgarmadi (Rus tili)",
   c.get(f"/api/students/{SID}/groups", headers=F).json()["primary_group_id"],
   G1)

print("\n=== 4. PULGA TEGILMADI (shu bosqichda ataylab) ===")
db = SessionLocal()
ck("balans hamon 0", student_balance(db, SID), 0)
ck("to'lov yozuvi yo'q",
   db.query(models.Payment).filter(
       models.Payment.student_id == SID).count(), 0)
db.close()

print("\n=== 5. Bitta guruhdan chiqarish ===")
r = c.delete(f"/api/students/{SID}/groups/{G2}", headers=F)
ck("chiqarildi", r.status_code, 200)
ck("bitta qoldi", r.json()["active_count"], 1)
rows = c.get(f"/api/students?group_id={G2}", headers=F).json()
ck("New ro'yxatidan chiqdi", any(x["id"] == SID for x in rows), False)
r = c.delete(f"/api/students/{SID}/groups/{G1}", headers=F)
ck("oxirgi guruhni olib bo'lmaydi", r.status_code, 400)
ck("sababi tushuntirilgan", "Guruhdan chiqarish" in str(r.json()), True)

print("\n=== 6. Yozuv O'CHIRILMAYDI — tarix qoladi ===")
db = SessionLocal()
ck("ikkita bog'lanish yozuvi bor",
   db.query(models.StudentGroupLink).filter(
       models.StudentGroupLink.student_id == SID).count(), 2)
closed = (db.query(models.StudentGroupLink)
          .filter(models.StudentGroupLink.student_id == SID,
                  models.StudentGroupLink.active == 0).first())
ck("yopilganida sana qo'yilgan", closed.left_date is not None, True)
db.close()

print("\n=== 7. Kartadagi guruhni almashtirsa bog'lanish ham yuradi ===")
r = c.put(f"/api/students/{SID}", headers=F, json={"group_id": G2})
ck("almashtirildi", r.status_code, 200)
db = SessionLocal()
ck("faol guruh — New", student_group_ids(db, SID), [G2])
ck("asosiy guruh ham New", db.query(models.Student).get(SID).group_id, G2)
db.close()

print("\n=== 8. Yangi o'quvchi ham bog'lanadi ===")
r = c.post("/api/students", headers=F, json={
    "full_name": "Yangi Bola", "phone": "+998901112299",
    "branch_id": BID, "group_id": G1, "status": "active"})
ck("yaratildi", r.status_code, 200)
NID = r.json()["id"]
db = SessionLocal()
ck("bog'lanish avtomat ochildi", student_group_ids(db, NID), [G1])
db.close()

print("\n=== 9. Ruxsatlar ===")
ck("ustoz guruh qo'sha olmaydi",
   c.post(f"/api/students/{SID}/groups", headers=T,
          json={"group_id": G1}).status_code, 403)
ck("ustoz ro'yxatni ko'ra oladi",
   c.get(f"/api/students/{SID}/groups", headers=T).status_code, 200)

print("\n" + ("HAMMASI OK" if not fails
              else f"{len(fails)} ta muammo: {fails}"))
sys.exit(1 if fails else 0)
