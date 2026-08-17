"""IKKI YOZUVNI BITTA QILISH (2026-08-17).

Jahongir: "qara sen aytyabman shu ikktani bitta qil, bittasini toliq
ochirib tashla, davomatri, otsin lekin bunga".

Eng muhim shart: "o'chirish" hech qanday MA'LUMOTNI yo'qotmasligi
kerak. Shuning uchun test avval ikkala kartaga tarix yozadi, keyin
birlashtiradi va HAMMASI omon qolgan kartada turganini tekshiradi.
"""
import os, sys
from datetime import date, timedelta
os.environ["DATABASE_URL"] = "sqlite:////tmp/mergestu.db"
if os.path.exists("/tmp/mergestu.db"):
    os.remove("/tmp/mergestu.db")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                         # noqa: E402
import entry                                       # noqa: E402
from database import SessionLocal                  # noqa: E402
from auth import hash_password                     # noqa: E402
from common import student_balance, student_group_ids  # noqa: E402

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
t = models.Teacher(full_name="Ustoz", branch_id=BID); db.add(t); db.commit()
g1 = models.Group(name="Rus tili", branch_id=BID, teacher_id=t.id,
                  lesson_price=60000, standard_lessons_per_month=8,
                  monthly_fee=480000)
g2 = models.Group(name="New", branch_id=BID, teacher_id=t.id,
                  lesson_price=60000, standard_lessons_per_month=8,
                  monthly_fee=480000)
db.add_all([g1, g2]); db.commit()
G1, G2 = g1.id, g2.id

A = models.Student(full_name="Abduvalieva Munisa", branch_id=BID,
                   status="active", group_id=G1, phone="+998940411480",
                   enrolled_date=date(2026, 7, 7))
B = models.Student(full_name="Abduvalieva Munisa", branch_id=BID,
                   status="active", group_id=G2, phone="+998940411480",
                   enrolled_date=date(2026, 8, 6), school="21-maktab")
db.add_all([A, B]); db.commit()
AID, BID_S = A.id, B.id

# Har guruhda darslar va davomat
today = date(2026, 8, 17)
for i, (grp, sid) in enumerate(((G1, AID), (G2, BID_S))):
    for k in range(7):
        L = models.Lesson(group_id=grp, date=today - timedelta(days=k * 2 + i),
                          held=1)
        db.add(L); db.commit()
        db.add(models.Attendance(lesson_id=L.id, student_id=sid,
                                 present=1 if k % 3 else 0))
    db.commit()

# Pul, coin, XP, imtihon
db.add_all([
    models.Payment(student_id=AID, amount=-480000, kind="charge",
                   period="2026-08", created_by="avtomat (oylik)"),
    models.Payment(student_id=BID_S, amount=-480000, kind="charge",
                   period="2026-08", created_by="avtomat (oylik)"),
    models.CoinEntry(student_id=AID, amount=20, source="manual",
                     created_by="Admin"),
    models.CoinEntry(student_id=BID_S, amount=13, source="manual",
                     created_by="Admin"),
    models.XpTransaction(student_id=BID_S, amount=55, is_reversal=0),
])
db.commit()
db.add_all([
    models.User(username="asos", full_name="Asoschi", role="founder",
                password_hash=hash_password("x"), is_active=1),
    models.User(username="rah", full_name="Filial rahbari",
                role="branch_manager", branch_id=BID,
                password_hash=hash_password("x"), is_active=1),
])
db.commit()
BEG_ATT = db.query(models.Attendance).count()
db.close()


def tok(u_):
    return {"Authorization": "Bearer " + c.post(
        "/api/auth/login", json={"username": u_, "password": "x"})
        .json()["access_token"]}


F, R = tok("asos"), tok("rah")

print("=== 1. Boshlang'ich holat ===")
db = SessionLocal()
ck("A davomati", db.query(models.Attendance).filter(
    models.Attendance.student_id == AID).count(), 7)
ck("B davomati", db.query(models.Attendance).filter(
    models.Attendance.student_id == BID_S).count(), 7)
ck("A balansi", student_balance(db, AID), -480000)
ck("B balansi", student_balance(db, BID_S), -480000)
db.close()

print("\n=== 2. Ruxsat: faqat asoschi ===")
ck("filial rahbariga yopiq",
   c.post(f"/api/students/{AID}/merge/{BID_S}", headers=R).status_code, 403)

print("\n=== 3. Begona odamni qo'shib bo'lmaydi ===")
db = SessionLocal()
x = models.Student(full_name="Boshqa Bola", branch_id=BID, status="active",
                   phone="+998901112233")
db.add(x); db.commit(); XID = x.id
db.close()
r = c.post(f"/api/students/{AID}/merge/{XID}", headers=F)
ck("boshqa odam rad etiladi", r.status_code, 400)
ck("sababi tushunarli", "bir odamga o'xshamayapti" in str(r.json()), True)
ck("o'zini o'ziga qo'shib bo'lmaydi",
   c.post(f"/api/students/{AID}/merge/{AID}", headers=F).status_code, 400)

print("\n=== 4. BIRLASHTIRISH ===")
r = c.post(f"/api/students/{AID}/merge/{BID_S}", headers=F)
ck("bajarildi", r.status_code, 200)
d = r.json()
ck("qolgan karta", d["kept"], AID)
ck("ikkita guruh", d["groups"], 2)
print("   ko'chirilgan:", d["moved"])

print("\n=== 5. DAVOMAT KO'CHDI — bitta ham yo'qolmadi ===")
db = SessionLocal()
ck("hammasi omon qolgan kartada",
   db.query(models.Attendance).filter(
       models.Attendance.student_id == AID).count(), 14)
ck("bazadagi umumiy davomat o'zgarmadi",
   db.query(models.Attendance).count(), BEG_ATT)
ck("yo'q qilingan kartada yozuv qolmadi",
   db.query(models.Attendance).filter(
       models.Attendance.student_id == BID_S).count(), 0)

print("\n=== 6. Pul, coin, XP ham ko'chdi ===")
ck("balans ikkalasining yig'indisi", student_balance(db, AID), -960000)
ck("to'lov yozuvlari", db.query(models.Payment).filter(
    models.Payment.student_id == AID).count(), 2)
ck("coin 20+13", int(db.query(models.CoinEntry).filter(
    models.CoinEntry.student_id == AID).count()), 2)
ck("XP ko'chdi", db.query(models.XpTransaction).filter(
    models.XpTransaction.student_id == AID).count(), 1)

print("\n=== 7. Ortiqcha yozuv o'chdi, ma'lumoti esa qoldi ===")
ck("yozuv o'chirilgan", db.query(models.Student).get(BID_S), None)
keep = db.query(models.Student).get(AID)
ck("bo'sh maydon to'ldirildi (maktab)", keep.school, "21-maktab")
ck("eng eski qo'shilgan sana saqlandi", keep.enrolled_date,
   date(2026, 7, 7))
ck("ikkala guruh faol", sorted(student_group_ids(db, AID)),
   sorted([G1, G2]))
db.close()

print("\n=== 8. Tarixga yozildi ===")
db = SessionLocal()
log = (db.query(models.AuditLog)
       .filter(models.AuditLog.field == "Ikki yozuv birlashtirildi")
       .first())
ck("audit yozuvi bor", log is not None, True)
ck("nima ko'chirilgani yozilgan", "Davomat" in (log.new_value or ""), True)
db.close()

print("\n=== 9. Guruh ro'yxatlarida ikkalasida ham ko'rinadi ===")
for gid, nom in ((G1, "Rus tili"), (G2, "New")):
    rows = c.get(f"/api/students?group_id={gid}", headers=F).json()
    ck(f"{nom} ro'yxatida", any(x["id"] == AID for x in rows), True)

print("\n" + ("HAMMASI OK" if not fails
              else f"{len(fails)} ta muammo: {fails}"))
sys.exit(1 if fails else 0)
