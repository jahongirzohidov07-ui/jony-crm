"""Xarajat formasi: OYLIK / XARAJAT ikki yo'l, soni va ombor (2026-08).

Jahongir: "xarjaat turi juda kengayib ketgan, shuni bitta tanlaydigan
qilish kerak unda 2ta variant boladi oylik yoki xarajat... Agar
kitobni tanlasa, Multilevel, Round-up kitoblar royxatdan tanlaydigan
chiqsin, tanlaydi, sonini kirgizadi, bu yoqda oborda ham korinsin"."""
import os, sys
from datetime import date

os.environ["DATABASE_URL"] = "sqlite:////tmp/exp_salary.db"
if os.path.exists("/tmp/exp_salary.db"):
    os.remove("/tmp/exp_salary.db")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
import main, models, roles
import entry  # noqa
from database import SessionLocal
from auth import hash_password

c = TestClient(main.app)
fails = []


def ck(n, g, w):
    ok = g == w
    print(("OK  " if ok else "XATO ") + n + f": {g}"
          + ("" if ok else f"   (kutilgan {w})"))
    if not ok:
        fails.append(n)


db = SessionLocal()
b = models.Branch(name="Bekobod 1"); db.add(b); db.commit()
BID = b.id
b2 = models.Branch(name="Zafar"); db.add(b2); db.commit()
t = models.Teacher(full_name="Aslidin Nabiyev", branch_id=BID, is_active=1)
sup = models.Teacher(full_name="Support Malika", branch_id=BID, is_active=1)
other = models.Teacher(full_name="Boshqa filial ustozi", branch_id=b2.id,
                       is_active=1)
db.add_all([t, sup, other]); db.commit()
TID = t.id
OTHER_TID = other.id
db.add_all([
    models.User(username="asos", full_name="Asoschi", role="founder",
                password_hash=hash_password("x"), is_active=1),
    models.User(username="adm", full_name="Baxriniso Xatamova",
                role="administrator", branch_id=BID,
                password_hash=hash_password("x"), is_active=1),
])
db.commit()
ADMIN_UID = db.query(models.User).filter(
    models.User.username == "adm").first().id
book = models.Consumable(name="Round-up 4", kind="book", branch_id=BID,
                         qty=2, min_qty=1, unit="dona")
db.add(book); db.commit()
BOOK_ID = book.id
db.close()

F = {"Authorization": "Bearer " + c.post(
    "/api/auth/login", json={"username": "asos", "password": "x"}
).json()["access_token"]}
TODAY = date.today().isoformat()

print("=== 1. Oylik uchun xodimlar ro'yxati (filial kesimida) ===")
r = c.get(f"/api/expenses/staff?branch_id={BID}", headers=F)
ck("200", r.status_code, 200)
names = [x["name"] for x in r.json()["rows"]]
ck("ustoz ro'yxatda", "Aslidin Nabiyev" in names, True)
ck("support ham ro'yxatda", "Support Malika" in names, True)
ck("administrator ham ro'yxatda", "Baxriniso Xatamova" in names, True)
ck("boshqa filial ustozi YO'Q", "Boshqa filial ustozi" in names, False)

print("\n=== 2. USTOZGA oylik -> oylik kartasiga tushadi ===")
r2 = c.post("/api/expenses", headers=F, json={
    "date": TODAY, "category": "admin_salary", "amount": 1500000,
    "teacher_id": TID, "method": "cash", "branch_id": BID})
ck("qabul qilindi", r2.status_code, 200)
db = SessionLocal()
tp = db.query(models.TeacherPayment).filter(
    models.TeacherPayment.teacher_id == TID).all()
n_exp = db.query(models.Expense).count()
db.close()
ck("ustoz oyligi TeacherPayment ga yozildi", len(tp), 1)
ck("summa to'g'ri", tp[0].amount, 1500000)
ck("xarajatlar jadvaliga IKKI MARTA yozilmadi", n_exp, 0)
card = c.get(f"/api/teachers/{TID}/salary", headers=F).json()
ck("ustoz kartasida ko'rinadi", card.get("paid_month"), 1500000)

print("\n=== 3. MA'MURIY xodimga oylik -> xarajat + xodimga bog'lanadi ===")
r3 = c.post("/api/expenses", headers=F, json={
    "date": TODAY, "category": "admin_salary", "amount": 4000000,
    "staff_user_id": ADMIN_UID, "method": "cash", "branch_id": BID})
ck("qabul qilindi", r3.status_code, 200)
ck("xodimga bog'landi", r3.json()["staff_user_id"], ADMIN_UID)
ck("izohda ismi bor", "Baxriniso" in (r3.json()["note"] or ""), True)
sal = c.get("/api/expenses/staff-salaries", headers=F).json()
ck("oyliklar ro'yxatida ko'rinadi", sal["count"], 1)
ck("summasi", sal["total"], 4000000)
# entry.py da "Administrator (qabul)" -> "Administrator" deb
# qayta nomlangan (markaz tilida shunday).
ck("lavozimi ham", sal["rows"][0]["role_label"], "Administrator")

print("\n=== 4. KITOB xarajati -> ombor qoldig'i oshadi ===")
r4 = c.post("/api/expenses", headers=F, json={
    "date": TODAY, "category": "book", "amount": 300000,
    "qty": 3, "consumable_id": BOOK_ID, "method": "cash",
    "branch_id": BID})
ck("qabul qilindi", r4.status_code, 200)
ck("soni saqlandi", r4.json()["qty"], 3)
ck("izohda kitob nomi", "Round-up 4" in (r4.json()["note"] or ""), True)
db = SessionLocal()
bk = db.query(models.Consumable).get(BOOK_ID)
mv = db.query(models.StockMove).filter(
    models.StockMove.consumable_id == BOOK_ID).all()
qty_after, price = bk.qty, bk.unit_price
db.close()
ck("ombor qoldig'i 2 -> 5", qty_after, 5)
ck("ombor harakati yozildi", len(mv), 1)
ck("dona narxi hisoblandi", price, 100000)

print("\n=== 5. Ro'yxatda yo'q kitob: nomi bilan ochiladi ===")
r5 = c.post("/api/expenses", headers=F, json={
    "date": TODAY, "category": "book", "amount": 250000,
    "qty": 5, "new_item_name": "Multilevel B2", "method": "cash",
    "branch_id": BID})
ck("qabul qilindi", r5.status_code, 200)
db = SessionLocal()
nb = db.query(models.Consumable).filter(
    models.Consumable.name == "Multilevel B2").first()
db.close()
ck("yangi kitob ochildi", bool(nb), True)
ck("qoldig'i 5", nb.qty if nb else 0, 5)

print("\n=== 6. Vlajniy: soni yoziladi, ombor tegilmaydi ===")
r6 = c.post("/api/expenses", headers=F, json={
    "date": TODAY, "category": "wet_wipes", "amount": 45000,
    "qty": 3, "method": "cash", "branch_id": BID})
ck("qabul qilindi", r6.status_code, 200)
ck("soni 3", r6.json()["qty"], 3)

print("\n=== 7. Ishxona telefoni — yangi tur ===")
r7 = c.post("/api/expenses", headers=F, json={
    "date": TODAY, "category": "office_phone", "amount": 80000,
    "method": "cash", "branch_id": BID})
ck("qabul qilindi", r7.status_code, 200)

# 2026-09-16, Jahongir: "administratorga oylik berish huquqini ber" —
# administrator oylik beradi, lekin faqat O'Z filialiga.
print("\n=== 8. Administrator — faqat o'z filialiga oylik beradi ===")
A = {"Authorization": "Bearer " + c.post(
    "/api/auth/login", json={"username": "adm", "password": "x"}
).json()["access_token"]}
r8 = c.post("/api/expenses", headers=A, json={
    "date": TODAY, "category": "admin_salary", "amount": 100000,
    "staff_user_id": ADMIN_UID, "branch_id": BID})
ck("administrator o'z filiali xodimiga oylik bera oladi", r8.status_code, 200)
r9 = c.post("/api/expenses", headers=A, json={
    "date": TODAY, "category": "admin_salary", "amount": 100000,
    "teacher_id": OTHER_TID, "branch_id": BID})
ck("boshqa filial ustoziga bera olmaydi", r9.status_code, 403)
r10 = c.post("/api/expenses", headers=A, json={
    "date": TODAY, "category": "admin_salary", "amount": 100000,
    "teacher_id": TID, "branch_id": BID})
ck("o'z filiali ustoziga bera oladi", r10.status_code, 200)
ck("oyliklar sahifasi administratorga yopiq",
   c.get("/api/payroll", headers=A).status_code, 403)

print()
if fails:
    print(f"XATOLAR ({len(fails)}): " + ", ".join(fails))
    sys.exit(1)
print("HAMMASI O'TDI")
