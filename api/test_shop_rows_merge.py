"""ESKI "+PUL" DO'KON CHEGIRMA QATORLARINI HISOBGA KO'CHIRISH (2026-09-30).

Jahongir (Abdullayeva Umida #688): "coinga almashganlarda nimaga hisobida
pul bn ko'rinyabdi ... pul ortiqcha ekan qaytaring deyishi mumkin ... oy
boshida 480 000 hisoblansa shuni o'zgartirib qo'yadigan bo'lsin".

Umida: 1-sentabr 480 000 hisob -> 25-sentabr chegirma bilan qayta yozildi
(321 600) + alohida "+158 000 Jony Shop" qatori = IKKI MARTA chegirma.

Tekshiriladi:
  1. Ko'rish (GET) hech narsani o'zgartirmaydi; faqat asoschiga.
  2. Ikki marta chegirma: qator arxivga, balans ortiqcha summaga kamayadi.
  3. Hisob chegirmasiz qolgan (avgust): hisob kamayadi, qator arxivga,
     balans O'ZGARMAYDI.
  4. Qatorlar payments_deleted'da to'liq saqlanadi.
  5. Ikkinchi yurish hech narsa qilmaydi.
"""
import os, sys
from datetime import date, datetime, timedelta
os.environ["DATABASE_URL"] = "sqlite:////tmp/shoprows.db"
if os.path.exists("/tmp/shoprows.db"):
    os.remove("/tmp/shoprows.db")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                         # noqa: E402
import entry                                       # noqa: E402
from database import SessionLocal                  # noqa: E402
import common as _cm_stub                           # noqa: E402
# Login oylik yechimni ishga tushiradi (auth_users -> common, 2026-10-02
# dan beri to'g'ri ulangan). Bu test unga bog'liq emas — o'chiramiz.
_cm_stub._ensure_month_charges = lambda db, **kw: None
from auth import hash_password                     # noqa: E402
from common import student_balance                 # noqa: E402

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
g = models.Group(name="Les Etoiles", branch_id=BID, monthly_fee=480000,
                 lesson_price=40000, standard_lessons_per_month=12)
db.add(g); db.commit(); GID = g.id
db.add_all([
    models.User(username="asos", full_name="Asoschi", role="founder",
                password_hash=hash_password("x"), is_active=1),
    models.User(username="adm", full_name="Admin", role="administrator",
                branch_id=BID, password_hash=hash_password("x"),
                is_active=1)])
db.commit()


def student(name):
    s = models.Student(full_name=name, branch_id=BID, status="active",
                       group_id=GID)
    db.add(s); db.commit()
    return s.id


def at(y, m, d, h=6):
    return datetime(y, m, d, h, 0)


# --- Umida: ikki marta chegirma (sentabr) ---
U = student("Abdullayeva Umida")
db.add(models.Payment(student_id=U, amount=-321600, kind="charge",
                      period="2026-09", created_by="avtomat (oylik)",
                      created_at=at(2026, 9, 1), updated_at=at(2026, 9, 25),
                      note="Les Etoiles — 2026-09: 12 dars · chegirma "
                           "qo'llandi: 480 000 -> 321 600"))
db.add(models.Payment(student_id=U, amount=322000, kind="payment",
                      method="cash", created_at=at(2026, 9, 11)))
db.add(models.Discount(student_id=U, kind="coin_shop", percent=33,
                       reason="Jony Shop: 33% (100 coin)", status="active",
                       period="2026-09", start_date=date(2026, 9, 1),
                       end_date=date(2026, 9, 30),
                       created_at=at(2026, 9, 11), approved_at=at(2026, 9, 11),
                       applied_at=at(2026, 9, 11)))
db.add(models.Payment(student_id=U, amount=158000, kind="discount",
                      period="2026-09", created_by="Jony Shop (coin)",
                      created_at=at(2026, 9, 11, 7),
                      note="2026-09 - Jony Shop chegirmasi"))
# --- Oybek: avgust, hisob chegirmasiz qolgan ---
O = student("Oybek")
db.add(models.Payment(student_id=O, amount=-480000, kind="charge",
                      period="2026-08", created_by="avtomat (oylik)",
                      created_at=at(2026, 8, 1), note="2026-08: 12 dars"))
db.add(models.Discount(student_id=O, kind="coin_shop", percent=33,
                       reason="Jony Shop: 33% (100 coin)", status="active",
                       period="2026-08", start_date=date(2026, 8, 1),
                       end_date=date(2026, 8, 31),
                       created_at=at(2026, 8, 20), approved_at=at(2026, 8, 20),
                       applied_at=at(2026, 8, 20)))
db.add(models.Payment(student_id=O, amount=158400, kind="discount",
                      period="2026-08", created_by="Jony Shop (coin)",
                      created_at=at(2026, 8, 20, 7)))
db.commit()
BU, BO = student_balance(db, U), student_balance(db, O)
db.close()


def tok(u_):
    return {"Authorization": "Bearer " + c.post(
        "/api/auth/login", json={"username": u_, "password": "x"})
        .json()["access_token"]}


F, A = tok("asos"), tok("adm")
URL = "/api/admin/shop-discount-rows"


print("=== 1. Ko'rish ===")
ck("administratorga 403", c.get(URL, headers=A).status_code, 403)
r = c.get(URL, headers=F)
ck("asoschiga 200", r.status_code, 200)
plan = {x["name"]: x for x in r.json()["rows"]}
ck("Umida — ikki marta", plan["Abdullayeva Umida"]["case"], "ikki_marta")
ck("Umida balansi 158 400 -> 400",
   (plan["Abdullayeva Umida"]["balance_before"],
    plan["Abdullayeva Umida"]["balance_after"]), (158400, 400))
ck("Oybek — hisobga ko'chadi", plan["Oybek"]["case"], "hisobga_kochdi")
ck("Oybek hisobi 480 000 -> 321 600",
   (plan["Oybek"]["charge_before"], plan["Oybek"]["charge_after"]),
   (480000, 321600))
db = SessionLocal()
ck("ko'rish hech narsa o'zgartirmadi",
   (student_balance(db, U), student_balance(db, O),
    db.query(models.Payment).filter(models.Payment.kind == "discount")
    .count()), (BU, BO, 2))
db.close()

print("=== 2-4. Qo'llash ===")
ck("administratorga 403", c.post(URL, headers=A).status_code, 403)
r = c.post(URL, headers=F)
ck("qo'llandi", r.status_code, 200)
db = SessionLocal()
ck("Umida balansi 400 (ortiqcha 158 000 olib tashlandi)",
   round(student_balance(db, U)), 400)
ck("Oybek balansi o'zgarmadi", round(student_balance(db, O)), round(BO))
ch = (db.query(models.Payment)
      .filter(models.Payment.student_id == O,
              models.Payment.kind == "charge").first())
ck("Oybek avgust hisobi 321 600", round(-ch.amount), 321600)
ck("hisob izohida chegirma", "Jony Shop chegirmasi" in (ch.note or ""),
   True)
ck("+pul qatorlari qolmadi",
   db.query(models.Payment).filter(models.Payment.kind == "discount")
   .count(), 0)
arch = db.query(models.DeletedPayment).all()
ck("ikkala qator arxivda", sorted(round(a.amount) for a in arch),
   [158000, 158400])
ck("arxivda sabab bor", all(a.reason for a in arch), True)
db.close()

print("=== 5. Takror ===")
r = c.post(URL, headers=F)
ck("ikkinchi yurish bo'sh", r.json()["rows"], [])

print("\n" + ("HAMMASI OK" if not fails
              else f"{len(fails)} ta XATO: {fails}"))
sys.exit(1 if fails else 0)
