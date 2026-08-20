"""COIN TAHRIRLASH (asoschi) + JONY SHOP CHEGIRMASI (2026-08-15).

Jahongir: "faqatgina asoschida coinlarni tahrirlaydigan funksiya
qoshib ber coin oldida bitta qalamcha bilan yetadi. va oquvchilar o'z
profilidan kirib Jony Shopda coiniga skidka sotib olsa avtomat
balansida shu narsa ozgarsin va 15-kungacha sotib olsa shu oy uchun
15-kundan keyin sotib olsa keyingi oyga ishlasin".
"""
import os, sys
from datetime import date
os.environ["DATABASE_URL"] = "sqlite:////tmp/coinshop.db"
if os.path.exists("/tmp/coinshop.db"):
    os.remove("/tmp/coinshop.db")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                         # noqa: E402
import entry                                       # noqa: E402
from database import SessionLocal                  # noqa: E402
from auth import hash_password                     # noqa: E402
from common import (_student_coin_balance, student_balance,  # noqa: E402
                    _apply_shop_discounts)

c = TestClient(main.app)
fails = []


def ck(n, g, w):
    ok = g == w
    print(("OK  " if ok else "XATO ") + n + f": {g}"
          + ("" if ok else f" (kutilgan {w})"))
    if not ok:
        fails.append(n)


db = SessionLocal()
b = models.Branch(name="Bekobod 1"); db.add(b); db.commit(); BID = b.id
g = models.Group(name="G1", branch_id=BID, monthly_fee=400000,
                 lesson_price=50000, standard_lessons_per_month=8)
db.add(g); db.commit(); GID = g.id
st = models.Student(full_name="Abdumuminov Asilbek", branch_id=BID,
                    status="active", group_id=GID, phone="+998507083310")
db.add(st); db.commit(); SID = st.id
db.add(models.CoinEntry(student_id=SID, amount=113, source="manual",
                        note="boshlang'ich", created_by="Admin"))
db.commit()
u = models.User(username="oquvchi", full_name="Abdumuminov Asilbek",
                role="student", branch_id=BID,
                password_hash=hash_password("x"), is_active=1)
db.add(u); db.commit()
st.user_id = u.id
db.add_all([
    models.User(username="asos", full_name="Asoschi", role="founder",
                password_hash=hash_password("x"), is_active=1),
    models.User(username="adm", full_name="Admin", role="administrator",
                branch_id=BID, password_hash=hash_password("x"),
                is_active=1),
])
db.commit(); db.close()


def tok(u_):
    return {"Authorization": "Bearer " + c.post(
        "/api/auth/login", json={"username": u_, "password": "x"})
        .json()["access_token"]}


F, A, S = tok("asos"), tok("adm"), tok("oquvchi")

print("=== 1. Coin tahrirlash — FAQAT ASOSCHI ===")
r = c.put(f"/api/students/{SID}/coins", headers=A,
          json={"balance": 200})
ck("administratorga 403", r.status_code, 403)
r = c.put(f"/api/students/{SID}/coins", headers=F,
          json={"balance": 200, "note": "LC UP bilan tenglashtirildi"})
ck("asoschiga ruxsat", r.status_code, 200)
ck("yangi balans", r.json()["balance"], 200)
ck("farq yozildi", r.json()["changed"], 87)

print("\n=== 2. Eski yozuvlar O'CHMAYDI, tarix qoladi ===")
db = SessionLocal()
ck("balans to'g'ri", _student_coin_balance(db, SID), 200)
ck("ikkita yozuv bor",
   db.query(models.CoinEntry).filter(
       models.CoinEntry.student_id == SID).count(), 2)
fix = (db.query(models.CoinEntry)
       .filter(models.CoinEntry.source == "admin_fix").first())
ck("sabab saqlangan", "LC UP" in (fix.note or ""), True)
ck("kim qilgani yozilgan", fix.created_by, "Asoschi")
db.close()

print("\n=== 3. Kamaytirish ham ishlaydi, manfiy — yo'q ===")
r = c.put(f"/api/students/{SID}/coins", headers=F, json={"balance": 150})
ck("kamaytirildi", r.json()["balance"], 150)
r = c.put(f"/api/students/{SID}/coins", headers=F, json={"balance": -5})
ck("manfiyga ruxsat yo'q", r.status_code, 400)
r = c.put(f"/api/students/{SID}/coins", headers=F, json={"balance": 150})
ck("o'zgarish bo'lmasa 0", r.json()["changed"], 0)

print("\n=== 4. Do'konga chegirma qo'yish ===")
r = c.post("/api/rewards", headers=F, json={
    "name": "33% chegirma", "cost": 100, "kind": "discount",
    "discount_percent": 33, "branch_id": BID})
ck("chegirma yaratildi", r.status_code, 200)
RID = r.json()["id"]
# 2026-08-20: 33% va 100% avtomat, qolgani xodim tasdig'i bilan
r = c.post("/api/rewards", headers=F, json={
    "name": "10% chegirma", "cost": 30, "kind": "discount",
    "discount_percent": 10, "branch_id": BID})
RID10 = r.json()["id"]
ck("turi discount", r.json()["kind"], "discount")
r = c.post("/api/rewards", headers=F, json={
    "name": "Bo'sh chegirma", "cost": 50, "kind": "discount"})
ck("foizsiz/summasiz rad etiladi", r.status_code, 400)
r = c.post("/api/rewards", headers=F, json={
    "name": "Ruchka", "cost": 20, "branch_id": BID})
ck("oddiy sovg'a ham ishlaydi", r.json()["kind"], "gift")

print("\n=== 5. O'quvchi 33% chegirmani AVTOMAT sotib oladi ===")
db = SessionLocal()
period_now = roles.local_today().strftime("%Y-%m")
# Shu oy hisobi mavjud bo'lsin — balans darrov o'zgarishi kerak
db.add(models.Payment(student_id=SID, amount=-400000, kind="charge",
                      period=period_now, created_by="avtomat (oylik)"))
db.commit()
bal_before = student_balance(db, SID)
coins_before = _student_coin_balance(db, SID)
db.close()
r = c.post(f"/api/me/rewards/{RID}", headers=S)
ck("sotib olindi", r.status_code, 200)
d = r.json()
ck("turi chegirma", d["kind"], "discount")
ck("summa 132 000 (400 000 ning 33%)", d["amount"], 132000)
db = SessionLocal()
ck("coin yechildi", _student_coin_balance(db, SID), coins_before - 100)
today = roles.local_today()
if today.day <= 15:
    ck("shu oyga tegishli", d["period"], period_now)
    ck("balansga DARROV tushdi", d["applied"], True)
    ck("balans 132 000 ga yaxshilandi",
       round(student_balance(db, SID) - bal_before), 132000)
else:
    nxt = ((today.year + 1, 1) if today.month == 12
           else (today.year, today.month + 1))
    ck("keyingi oyga tegishli", d["period"], f"{nxt[0]:04d}-{nxt[1]:02d}")
    ck("hozir balansga tushmaydi", d["applied"], False)
    ck("balans o'zgarmadi", student_balance(db, SID), bal_before)
disc = (db.query(models.Discount)
        .filter(models.Discount.kind == "coin_shop").first())
ck("chegirma yozuvi ochildi", disc is not None, True)
ck("oyi yozilgan", disc.period, d["period"])
ck("sababda coin soni bor", "100 coin" in (disc.reason or ""), True)
db.close()

print("\n=== 6. Ikki marta tushmaydi ===")
db = SessionLocal()
bal = student_balance(db, SID)
_apply_shop_discounts(db)
_apply_shop_discounts(db)
ck("balans o'zgarmadi", student_balance(db, SID), bal)
db.close()

print("\n=== 7. Coin yetmasa sotib olib bo'lmaydi ===")
r = c.post("/api/rewards", headers=F, json={
    "name": "Katta chegirma", "cost": 100000, "kind": "discount",
    "discount_amount": 200000, "branch_id": BID})
BIG = r.json()["id"]
r = c.post(f"/api/me/rewards/{BIG}", headers=S)
ck("400 qaytadi", r.status_code, 400)
ck("sababi tushunarli", "Coin yetarli emas" in str(r.json()), True)

print("\n=== 8. Keyingi oy chegirmasi hisob chiqqach tushadi ===")
db = SessionLocal()
nxt_p = "2099-01"
d2 = models.Discount(student_id=SID, kind="coin_shop", amount=50000,
                     reason="Jony Shop: sinov (10 coin)",
                     start_date=date(2099, 1, 1),
                     end_date=date(2099, 1, 31), status="active",
                     period=nxt_p, requested_by="test")
db.add(d2); db.commit()
n = _apply_shop_discounts(db, nxt_p)
ck("hisob yo'q — tushmadi", n, 0)
db.add(models.Payment(student_id=SID, amount=-400000, kind="charge",
                      period=nxt_p, created_by="avtomat (oylik)"))
db.commit()
bal = student_balance(db, SID)
n = _apply_shop_discounts(db, nxt_p)
ck("hisob chiqqach tushdi", n, 1)
ck("balans 50 000 ga yaxshilandi",
   round(student_balance(db, SID) - bal), 50000)
n = _apply_shop_discounts(db, nxt_p)
ck("takror tushmadi", n, 0)
db.close()

print("\n=== 8b. 10% chegirma — XODIM TASDIG'I bilan ===")
# Jahongir, 2026-08-20: "33% lik va 100% lik chegirmalarni ... avtomat
# berilsin admin tasdiqlashi shartmas, qolganlarini admin tasdiqlashi
# va berishi kerak bo'ladi".
db = SessionLocal()
coins0 = _student_coin_balance(db, SID)
n_disc0 = db.query(models.Discount).filter(
    models.Discount.kind == "coin_shop").count()
db.close()
r = c.post(f"/api/me/rewards/{RID10}", headers=S)
ck("so'rov qabul qilindi", r.status_code, 200)
ck("darrov berilmadi", r.json().get("status"), "requested")
RQ = r.json()["id"]
db = SessionLocal()
ck("coin hali yechilmadi", _student_coin_balance(db, SID), coins0)
ck("chegirma hali yo'q",
   db.query(models.Discount).filter(
       models.Discount.kind == "coin_shop").count(), n_disc0)
db.close()
r = c.get("/api/rewards/requests", headers=A)
ck("xodim ro'yxatida ko'rinadi",
   any(x["id"] == RQ for x in r.json()["rows"]), True)
r = c.post(f"/api/rewards/requests/{RQ}/give", headers=A,
           json={"give": True})
ck("tasdiqlandi", r.status_code, 200)
db = SessionLocal()
ck("coin endi yechildi", _student_coin_balance(db, SID), coins0 - 30)
ck("chegirma yozuvi ochildi",
   db.query(models.Discount).filter(
       models.Discount.kind == "coin_shop").count(), n_disc0 + 1)
last = (db.query(models.Discount)
        .filter(models.Discount.kind == "coin_shop")
        .order_by(models.Discount.id.desc()).first())
ck("foizi to'g'ri", last.percent, 10)
ck("kim tasdiqlagani yozilgan", last.approved_by, "Admin")
db.close()

print("\n=== 8c. Qoida: qaysi chegirma avtomat ===")
class _R:
    def __init__(self, kind, pct=None, amt=None):
        self.kind, self.discount_percent, self.discount_amount = kind, pct, amt
ck("33% avtomat", roles.shop_auto_discount(_R("discount", 33)), True)
ck("100% avtomat", roles.shop_auto_discount(_R("discount", 100)), True)
ck("10% avtomat emas", roles.shop_auto_discount(_R("discount", 10)), False)
ck("so'mdagi chegirma avtomat emas",
   roles.shop_auto_discount(_R("discount", None, 50000)), False)
ck("sovg'a avtomat emas", roles.shop_auto_discount(_R("gift")), False)

print("\n=== 9. 15-kun qoidasi ===")
ck("14-kun -> shu oy",
   roles.shop_discount_period(date(2026, 8, 14)), "2026-08")
ck("15-kun -> shu oy (chegara ichida)",
   roles.shop_discount_period(date(2026, 8, 15)), "2026-08")
ck("16-kun -> keyingi oy",
   roles.shop_discount_period(date(2026, 8, 16)), "2026-09")
ck("31-dekabr -> keyingi YIL yanvari",
   roles.shop_discount_period(date(2026, 12, 31)), "2027-01")

print("\n" + ("HAMMASI OK" if not fails
              else f"{len(fails)} ta XATO: {fails}"))
sys.exit(1 if fails else 0)
