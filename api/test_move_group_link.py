"""BOSHQA GURUHGA O'TKAZGANDA ESKI GURUHDA QOLMASIN (2026-09-03).

Jahongir: "bir o'quvchini boshqa guruhga o'tkizish qilsa eski
guruhida qolyabdi ekan shunaqami unaqa bolsa togrlash kerak".

SABAB. move-group endpointi bog'lanish jadvalida (student_groups)
YANGI guruhni yopardi — detach_group(db, s, g.id) — eskisi esa faol
qolib ketardi. Ro'yxatlar in_group() orqali ikkala manbani ham
o'qiydi (Student.group_id VA faol bog'lanish), shuning uchun
o'quvchi ESKI guruh ro'yxatida ham turaverardi.

Test uchta narsani isbotlaydi:
  1. Ko'chirgandan keyin o'quvchi FAQAT yangi guruhda;
  2. Eski bog'lanish O'CHIRILMAYDI — yopiladi va tarixda qoladi;
  3. Haqiqiy IKKI GURUHLI o'quvchi buzilmaydi.
Ustiga bir martalik tuzatish ham tekshiriladi.
"""
import os, sys
from datetime import date, timedelta

os.environ["DATABASE_URL"] = "sqlite:////tmp/mvgrp_test.db"
if os.path.exists("/tmp/mvgrp_test.db"):
    os.remove("/tmp/mvgrp_test.db")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
import main, models, roles, students as students_mod
import entry  # noqa: F401 — production yo'li
from database import SessionLocal
from auth import hash_password
from common import attach_group

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


def gr_ids(gid, H):
    r = client.get(f"/api/students?group_id={gid}", headers=H)
    return [x["id"] for x in r.json()] if r.status_code == 200 else []


TODAY = date.today()
db = SessionLocal()
b = models.Branch(name="Zafar")
db.add(b)
db.commit()
BID = b.id
db.add(models.User(username="asos", password_hash=hash_password("x"),
                   full_name="Asoschi", role="founder"))
db.commit()
t = models.Teacher(full_name="Ustoz", branch_id=BID, is_active=1,
                   grade="senior", hired_date=TODAY - timedelta(days=500))
db.add(t)
db.commit()
TID = t.id

G = {}
for nm in ("Eski guruh", "Yangi guruh", "Uchinchi guruh"):
    g = models.Group(name=nm, teacher_id=TID, branch_id=BID,
                     subject="english", lesson_days="mon,wed,fri",
                     lesson_time="09:00",
                     start_date=TODAY - timedelta(days=90),
                     lesson_price=40000, monthly_fee=480000,
                     standard_lessons_per_month=12)
    db.add(g)
    db.commit()
    G[nm] = g.id

s1 = models.Student(full_name="Ko'chadigan Ali", branch_id=BID,
                    group_id=G["Eski guruh"], status="active",
                    enrolled_date=TODAY - timedelta(days=80))
s2 = models.Student(full_name="Ikki guruhli Vali", branch_id=BID,
                    group_id=G["Eski guruh"], status="active",
                    enrolled_date=TODAY - timedelta(days=80))
db.add_all([s1, s2])
db.commit()
S1, S2 = s1.id, s2.id
# Bog'lanishlar: ikkalasi eski guruhda, Vali qo'shimcha uchinchi guruhda
attach_group(db, s1, G["Eski guruh"], joined=s1.enrolled_date)
attach_group(db, s2, G["Eski guruh"], joined=s2.enrolled_date)
attach_group(db, s2, G["Uchinchi guruh"], joined=s2.enrolled_date)
db.commit()
db.close()

H = tok("asos")

print("=== 1. BOSHLANG'ICH HOLAT ===")
ck("eski guruhda 2 ta", sorted(gr_ids(G["Eski guruh"], H)),
   sorted([S1, S2]))
ck("yangi guruh bo'sh", gr_ids(G["Yangi guruh"], H), [])
ck("Vali uchinchi guruhda ham", gr_ids(G["Uchinchi guruh"], H), [S2])

print("\n=== 2. KO'CHIRISH ===")
r = client.post(f"/api/students/{S1}/move-group?force=true", headers=H,
                json={"group_id": G["Yangi guruh"]})
ck("ko'chirildi", r.status_code, 200)
ck("javobda yangi guruh", r.json()["group"], "Yangi guruh")

print("\n=== 3. ESKI GURUHDA QOLMADI ===")
ck("ESKI guruhda Ali YO'Q", S1 in gr_ids(G["Eski guruh"], H), False)
ck("eski guruhda faqat Vali qoldi", gr_ids(G["Eski guruh"], H), [S2])
ck("YANGI guruhda Ali BOR", gr_ids(G["Yangi guruh"], H), [S1])

db = SessionLocal()
st = db.query(models.Student).get(S1)
ck("asosiy guruh yangisi", st.group_id, G["Yangi guruh"])

print("\n=== 4. TARIX O'CHMADI ===")
links = (db.query(models.StudentGroupLink)
         .filter(models.StudentGroupLink.student_id == S1).all())
ck("ikkala bog'lanish ham bazada", len(links), 2)
old = [l for l in links if l.group_id == G["Eski guruh"]][0]
new = [l for l in links if l.group_id == G["Yangi guruh"]][0]
ck("eskisi yopildi", old.active, 0)
ck("chiqqan sanasi yozildi", old.left_date is not None, True)
ck("yangisi faol", new.active, 1)
ck("yangisi ASOSIY", new.is_primary, 1)
db.close()

print("\n=== 5. IKKI GURUHLI O'QUVCHI BUZILMADI ===")
ck("Vali eski guruhda", S2 in gr_ids(G["Eski guruh"], H), True)
ck("Vali uchinchi guruhda ham", S2 in gr_ids(G["Uchinchi guruh"], H),
   True)

print("\n=== 6. IKKI GURUHLINI KO'CHIRSAK ===")
r = client.post(f"/api/students/{S2}/move-group?force=true", headers=H,
                json={"group_id": G["Yangi guruh"]})
ck("ko'chirildi", r.status_code, 200)
ck("ESKI guruh endi bo'sh", gr_ids(G["Eski guruh"], H), [])
ck("uchinchi guruh saqlanib qoldi",
   S2 in gr_ids(G["Uchinchi guruh"], H), True)
db = SessionLocal()
st2 = db.query(models.Student).get(S2)
ck("asosiy guruh — ko'chirilgani", st2.group_id, G["Yangi guruh"])
db.close()

print("\n=== 7. ESKI BUZUQ YOZUV TUZATILADI ===")
# Xato ko'chirishdan keyingi holatni aynan yasaymiz: group_id yangi
# guruh, bog'lanish esa hamon eskisida.
db = SessionLocal()
s3 = models.Student(full_name="Buzuq Hasan", branch_id=BID,
                    group_id=G["Eski guruh"], status="active",
                    enrolled_date=TODAY - timedelta(days=70))
db.add(s3)
db.commit()
S3 = s3.id
attach_group(db, s3, G["Eski guruh"], joined=s3.enrolled_date)
db.commit()
s3.group_id = G["Uchinchi guruh"]      # ko'chirildi, lekin bog'lanish eski
db.commit()
db.close()

ck("buzuq: eski guruhda ham chiqadi",
   S3 in gr_ids(G["Eski guruh"], H), True)
ck("buzuq: uchinchi guruhda ham chiqadi",
   S3 in gr_ids(G["Uchinchi guruh"], H), True)

db = SessionLocal()
n = students_mod.fix_stale_group_links(db)
db.close()
ck("1 ta o'quvchi tuzatildi", n, 1)
ck("endi eski guruhda YO'Q", S3 in gr_ids(G["Eski guruh"], H), False)
ck("uchinchi guruhda BOR", S3 in gr_ids(G["Uchinchi guruh"], H), True)

db = SessionLocal()
ls = (db.query(models.StudentGroupLink)
      .filter(models.StudentGroupLink.student_id == S3).all())
ck("eski bog'lanish o'chirilmadi, yopildi",
   sorted([(l.group_id, l.active) for l in ls]),
   sorted([(G["Eski guruh"], 0), (G["Uchinchi guruh"], 1)]))
db.close()

print("\n=== 8. TUZATISH IDEMPOTENT VA BOSHQALARGA TEGMAYDI ===")
db = SessionLocal()
ck("ikkinchi marta 0", students_mod.fix_stale_group_links(db), 0)
db.close()
ck("Vali hamon ikki guruhda",
   S2 in gr_ids(G["Yangi guruh"], H)
   and S2 in gr_ids(G["Uchinchi guruh"], H), True)

print("\n" + ("BARCHASI OK" if not fails else f"XATOLAR: {fails}"))
sys.exit(1 if fails else 0)
