"""AVGUST DUBL YECHIMINI TOZALASH (2026-08-22).

Jahongir: "JonyOSda ikki marta avgust uchun yechganlarni ochirsang
balans tenglashadiganlari bor... shularni ochir, hammasidan avgust
oyi uchun yechilgan pul".

Tekshiriladi: dubl (avto oylik + LC import yechimi) topiladi, faqat
asoschi ishlatadi, commit'da arxivga ko'chadi (payments_deleted),
avto oylik va boshqa oylar yechimiga TEGILMAYDI, balans to'g'rilanadi.
"""
import os, sys

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_lca/db.sqlite"
os.makedirs("/tmp/verify_lca", exist_ok=True)
if os.path.exists("/tmp/verify_lca/db.sqlite"):
    os.remove("/tmp/verify_lca/db.sqlite")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
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
uf = models.User(username="asos", full_name="Asoschi",
                 password_hash=hash_password("Parol123!"),
                 role=roles.FOUNDER, branch_id=b.id, is_active=1)
um = models.User(username="mol", full_name="Moliyachi",
                 password_hash=hash_password("Parol123!"),
                 role=roles.FINANCE_DIRECTOR, branch_id=b.id, is_active=1)
db.add_all([uf, um]); db.commit()

s1 = models.Student(full_name="Dubl Bola", branch_id=b.id,
                    status="active", public_id="S1")
s2 = models.Student(full_name="Toza Bola", branch_id=b.id,
                    status="active", public_id="S2")
db.add_all([s1, s2]); db.commit()

# s1: avto avgust oyligi + LC import juftligi (to'lov + avgust yechimi)
db.add(models.Payment(student_id=s1.id, amount=-480000, kind="charge",
                      period="2026-08", note="2026-08 oylik",
                      created_at=datetime(2026, 8, 1)))
db.add(models.Payment(student_id=s1.id, amount=480000, kind="payment",
                      note="[LC UP] eski to'lov",
                      created_at=datetime(2026, 8, 17)))
db.add(models.Payment(student_id=s1.id, amount=-480000, kind="charge",
                      note="[LC UP] eski hisob (2026-08)",
                      created_at=datetime(2026, 8, 17)))
# s1 iyul juftligi — TEGILMASLIGI kerak
db.add(models.Payment(student_id=s1.id, amount=-325000, kind="charge",
                      note="[LC UP] eski hisob (2026-07)",
                      created_at=datetime(2026, 7, 15)))
# s2: faqat LC import yechimi bor, avto avgust YO'Q — tegilmaydi
db.add(models.Payment(student_id=s2.id, amount=-480000, kind="charge",
                      note="[LC UP] eski hisob (2026-08)",
                      created_at=datetime(2026, 8, 15)))
db.commit()

Hf = {"Authorization": f"Bearer {c.post('/api/auth/login', json={'username': 'asos', 'password': 'Parol123!'}).json()['access_token']}"}
Hm = {"Authorization": f"Bearer {c.post('/api/auth/login', json={'username': 'mol', 'password': 'Parol123!'}).json()['access_token']}"}

print("=== KO'RIB CHIQISH ===")
r = c.post("/api/lcup/cleanup-august", headers=Hf, json={"commit": False})
ck("status 200", r.status_code, 200)
j = r.json()
ck("faqat dubl topildi (s1)", j["count"], 1)
ck("summasi to'g'ri", j["total"], 480000.0)
ck("hali bajarilmadi", j["committed"], False)
ck("bazada hali turibdi",
   db.query(models.Payment).filter(
       models.Payment.note.like("%eski hisob (2026-08)%")).count(), 2)

print("\n=== FAQAT ASOSCHI ===")
r = c.post("/api/lcup/cleanup-august", headers=Hm, json={"commit": True})
ck("moliyachiga yopiq", r.status_code, 403)

print("\n=== TASDIQLASH ===")
r = c.post("/api/lcup/cleanup-august", headers=Hf, json={"commit": True})
ck("status 200", r.status_code, 200)
ck("bajarildi", r.json()["committed"], True)
db.expire_all()
ck("s1 avgust dubl yechimi ketdi",
   db.query(models.Payment).filter(
       models.Payment.student_id == s1.id,
       models.Payment.note.like("%eski hisob (2026-08)%")).count(), 0)
ck("s1 iyul yechimi JOYIDA",
   db.query(models.Payment).filter(
       models.Payment.student_id == s1.id,
       models.Payment.note.like("%eski hisob (2026-07)%")).count(), 1)
ck("s1 avto oyligi JOYIDA",
   db.query(models.Payment).filter(
       models.Payment.student_id == s1.id,
       models.Payment.period == "2026-08").count(), 1)
ck("s2 yechimi TEGILMADI (avto oyligi yo'q edi)",
   db.query(models.Payment).filter(
       models.Payment.student_id == s2.id).count(), 1)
ck("ARXIVGA tushdi",
   db.query(models.DeletedPayment).count(), 1)
arch = db.query(models.DeletedPayment).first()
ck("arxivda sababi yozilgan", "dubl" in (arch.reason or ""), True)
# s1 balansi endi: -480000 (avto) + 480000 (to'lov) - 325000 (iyul) = -325000

print("\n=== QAYTA BOSILSA — BO'SH ===")
r = c.post("/api/lcup/cleanup-august", headers=Hf, json={"commit": True})
ck("endi dubl yo'q", r.json()["count"], 0)

print()
if fails:
    print("XATOLAR:", fails); sys.exit(1)
print("BARCHASI OK")
