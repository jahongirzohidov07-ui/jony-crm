"""FILIAL RAHBARI BALANSNI TAHRIRLAYDI (2026-09-01).

Jahongir: "filial rahbarlari balansni tahrirlash huquqi bormi yoq
bolsa shu tahrirlash huquqi bolsin".

Tekshiriladi:
  A) PUL balansi — filial rahbarida ALLAQACHON bor edi (yozuv
     qo'shish va summani tahrirlash). Bu qism REGRESSIYA testi:
     huquq bekorga olib qo'yilmaganini isbotlaydi.
  B) COIN balansi — YANGI. Ilgari faqat asoschida edi, endi filial
     rahbarida ham bor, lekin FAQAT O'Z FILIALI o'quvchisiga.
  C) Tarix o'chmaydi: to'g'rilash FARQ yozuvi bo'lib qo'shiladi,
     eski coin yozuvlari joyida qoladi, auditga yoziladi.
"""
import os, sys
from datetime import date, timedelta

os.environ["DATABASE_URL"] = "sqlite:////tmp/mbal_test.db"
if os.path.exists("/tmp/mbal_test.db"):
    os.remove("/tmp/mbal_test.db")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
import main, models, roles
import entry  # noqa: F401
from database import SessionLocal
from auth import hash_password
from common import student_balance

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


TODAY = date.today()
db = SessionLocal()
b1 = models.Branch(name="Zafar")
b2 = models.Branch(name="Bekobod 1")
db.add_all([b1, b2])
db.commit()
B1, B2 = b1.id, b2.id

db.add(models.User(username="asos", password_hash=hash_password("x"),
                   full_name="Asoschi", role="founder"))
db.add(models.User(username="rahbar", password_hash=hash_password("x"),
                   full_name="Zafar Rahbari", role="branch_manager",
                   branch_id=B1))
db.add(models.User(username="admin1", password_hash=hash_password("x"),
                   full_name="Administrator", role="sales_manager",
                   branch_id=B1))
db.add(models.User(username="oquv", password_hash=hash_password("x"),
                   full_name="O'quv rahbari", role="academic_head",
                   branch_id=B1))
db.commit()

s1 = models.Student(full_name="Mening bola", branch_id=B1,
                    status="active",
                    enrolled_date=TODAY - timedelta(days=100))
s2 = models.Student(full_name="Begona bola", branch_id=B2,
                    status="active",
                    enrolled_date=TODAY - timedelta(days=100))
db.add_all([s1, s2])
db.commit()
S1, S2 = s1.id, s2.id

# Eski coin tarixi — o'chib ketmasligi tekshiriladi
db.add(models.CoinEntry(student_id=S1, amount=30, source="daily",
                        note="kunlik", created_by="tizim"))
db.add(models.CoinEntry(student_id=S1, amount=-10, source="reward",
                        note="sovg'a", created_by="tizim"))
db.commit()
db.close()

H = tok("asos")
BM = tok("rahbar")
AD = tok("admin1")
AC = tok("oquv")

print("=== 0. HUQUQ RO'YXATI ===")
ck("COIN_BALANCE_EDIT alohida ro'yxat",
   roles.COIN_BALANCE_EDIT, [roles.FOUNDER, roles.BRANCH_MANAGER])
ck("COIN_ADMIN bilan bir OBYEKT emas",
   roles.COIN_BALANCE_EDIT is roles.COIN_ADMIN, False)
ck("filial rahbari pul yozuvini qo'sha oladi (CASH_ACCESS)",
   roles.BRANCH_MANAGER in roles.CASH_ACCESS, True)
ck("filial rahbari to'lov summasini tahrirlaydi (PAYMENT_EDIT)",
   roles.BRANCH_MANAGER in roles.PAYMENT_EDIT, True)

print("\n=== B. COIN BALANSI — YANGI HUQUQ ===")
db = SessionLocal()
before = db.query(models.CoinEntry).filter(
    models.CoinEntry.student_id == S1).count()
db.close()
ck("boshlang'ich coin yozuvlari", before, 2)

r = client.get(f"/api/students/{S1}/coins", headers=BM)
ck("coin tarixi ochiladi", r.status_code, 200)

r = client.put(f"/api/students/{S1}/coins", headers=BM,
               json={"balance": 55, "note": "LC UP bilan tenglashtirildi"})
ck("FILIAL RAHBARI coin balansini to'g'riladi", r.status_code, 200)
ck("yangi balans", r.json()["balance"], 55)
ck("farq", r.json()["changed"], 35)

print("\n=== C. TARIX O'CHMAYDI ===")
db = SessionLocal()
rows = db.query(models.CoinEntry).filter(
    models.CoinEntry.student_id == S1).order_by(
    models.CoinEntry.id).all()
ck("yozuvlar soni 2 dan 3 ga chiqdi (o'chirilmadi)", len(rows), 3)
ck("eski 1-yozuv joyida", (rows[0].amount, rows[0].source), (30, "daily"))
ck("eski 2-yozuv joyida", (rows[1].amount, rows[1].source), (-10, "reward"))
ck("yangi yozuv FARQ", rows[2].amount, 35)
ck("manbasi admin_fix", rows[2].source, "admin_fix")
ck("izohda lavozim ko'rinadi",
   rows[2].note.startswith("Filial rahbari to'g'riladi: 20 -> 55"), True)
ck("sabab saqlangan",
   "LC UP bilan tenglashtirildi" in (rows[2].note or ""), True)
ck("kim qilgani saqlangan", rows[2].created_by, "Zafar Rahbari")

a = db.query(models.AuditLog).filter(
    models.AuditLog.entity == "student",
    models.AuditLog.action == "coin_fix",
    models.AuditLog.entity_id == S1).all()
ck("auditga yozildi", len(a), 1)
ck("auditda eski qiymat", a[0].old_value, "20")
ck("auditda yangi qiymat", a[0].new_value, "55")
ck("auditda kim", a[0].user_name, "Zafar Rahbari")
db.close()

print("\n=== D. FILIAL CHEGARASI ===")
r = client.put(f"/api/students/{S2}/coins", headers=BM,
               json={"balance": 999, "note": "boshqa filial"})
ck("BOSHQA filial o'quvchisi 403", r.status_code, 403)
db = SessionLocal()
ck("begona bolaning coini tegilmagan",
   db.query(models.CoinEntry).filter(
       models.CoinEntry.student_id == S2).count(), 0)
db.close()

print("\n=== E. QOLGANLARGA YOPIQ ===")
for nm, h in [("administrator", AD), ("o'quv bo'limi rahbari", AC)]:
    r = client.put(f"/api/students/{S1}/coins", headers=h,
                   json={"balance": 1, "note": "x"})
    ck(f"{nm} coin balansiga tegolmaydi", r.status_code, 403)

print("\n=== F. ASOSCHI HAMMA FILIALDA ===")
r = client.put(f"/api/students/{S2}/coins", headers=H,
               json={"balance": 7, "note": "asoschi"})
ck("asoschi boshqa filialda ham to'g'rilaydi", r.status_code, 200)
ck("balans", r.json()["balance"], 7)

print("\n=== G. NOTO'G'RI QIYMAT ===")
r = client.put(f"/api/students/{S1}/coins", headers=BM,
               json={"balance": -5, "note": "x"})
ck("manfiy coin 400", r.status_code, 400)
r = client.put(f"/api/students/{S1}/coins", headers=BM,
               json={"balance": 55, "note": "o'zgarish yo'q"})
ck("bir xil qiymat — 200, lekin yangi yozuv yo'q", r.status_code, 200)
ck("changed 0", r.json()["changed"], 0)
db = SessionLocal()
ck("yozuvlar soni oshmadi",
   db.query(models.CoinEntry).filter(
       models.CoinEntry.student_id == S1).count(), 3)
db.close()

print("\n=== H. PUL BALANSI — AVVALDAN BOR (regressiya) ===")
# DIQQAT: bu bo'lim ATAYLAB oxirida. To'lov qabul qilinganda
# tizim avtomat "o'z vaqtida to'lov" coin bonusini qo'shadi —
# agar bu blok coin tekshiruvlaridan oldin tursa, coin sonlari
# siljib, testning o'zi yolg'on xato bergan bo'lardi.
r = client.post(f"/api/students/{S1}/payments", headers=BM,
                json={"amount": 500000, "method": "cash",
                      "note": "Filial rahbari kiritdi"})
ck("yozuv qo'shildi", r.status_code, 200)
PID = r.json()["id"]
db = SessionLocal()
ck("balans o'zgardi", student_balance(db, S1), 500000)
db.close()

r = client.put(f"/api/payments/{PID}", headers=BM,
               json={"amount": 400000})
ck("summa tahrirlandi", r.status_code, 200)
db = SessionLocal()
ck("balans qayta hisoblandi", student_balance(db, S1), 400000)
db.close()

r = client.put(f"/api/payments/{PID}", headers=AD, json={"amount": 1})
ck("administrator summani tahrirlay OLMAYDI", r.status_code, 403)

print("\n" + ("BARCHASI OK" if not fails else f"XATOLAR: {fails}"))
sys.exit(1 if fails else 0)
