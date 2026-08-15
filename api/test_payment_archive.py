"""O'CHIRILGAN TO'LOV ARXIVI + XATO OGOHLANTIRISHI (2026-08-15).

Jahongir'ning asosiy qoidasi: "hech narsa o'chmasin". Ilgari
delete_payment yozuvni butunlay yo'q qilardi. Endi u payments'dan
olinadi (balans darrov to'g'rilanadi), lekin payments_deleted
arxivida to'liq saqlanadi va asoschi uni qaytara oladi.
"""
import os, sys
os.environ["DATABASE_URL"] = "sqlite:////tmp/payarch.db"
if os.path.exists("/tmp/payarch.db"):
    os.remove("/tmp/payarch.db")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fastapi.testclient import TestClient          # noqa: E402
import main, models                                # noqa: E402
import entry                                       # noqa: E402
from database import SessionLocal                  # noqa: E402
from auth import hash_password                     # noqa: E402

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
st = models.Student(full_name="Karimov Aziz", branch_id=BID,
                    status="active")
db.add(st); db.commit(); SID = st.id
db.add_all([
    models.User(username="asos", full_name="Asoschi", role="founder",
                password_hash=hash_password("x"), is_active=1),
    models.User(username="mol", full_name="Moliyachi",
                role="finance_director", branch_id=BID,
                password_hash=hash_password("x"), is_active=1),
    models.User(username="adm", full_name="Admin", role="administrator",
                branch_id=BID, password_hash=hash_password("x"),
                is_active=1),
])
db.commit(); db.close()


def tok(u):
    return {"Authorization": "Bearer " + c.post(
        "/api/auth/login", json={"username": u, "password": "x"})
        .json()["access_token"]}


F, M, A = tok("asos"), tok("mol"), tok("adm")

print("=== 1. To'lov kiritamiz ===")
r = c.post(f"/api/students/{SID}/payments", headers=A,
           json={"amount": 500000, "kind": "payment", "method": "cash",
                 "client_key": "arch-1"})
ck("kiritildi", r.status_code, 200)
PID = r.json()["id"]
r = c.get(f"/api/students/{SID}", headers=A)
ck("balans 500 000", r.json()["balance"], 500000)

print("\n=== 2. O'chirish: balans to'g'rilanadi ===")
r = c.delete(f"/api/payments/{PID}?reason=Ikki marta kiritilgan",
             headers=F)
ck("o'chirildi", r.status_code, 200)
ck("arxivga ko'chdi", r.json().get("archived"), True)
r = c.get(f"/api/students/{SID}", headers=A)
ck("balans 0 ga qaytdi", r.json()["balance"], 0)

print("\n=== 3. LEKIN YO'QOLMADI — arxivda turibdi ===")
db = SessionLocal()
n = db.query(models.DeletedPayment).count()
ck("arxivda 1 ta yozuv", n, 1)
row = db.query(models.DeletedPayment).first()
ck("summa saqlangan", row.amount, 500000)
ck("o'quvchi ismi saqlangan", row.student_name, "Karimov Aziz")
ck("kim o'chirgani yozilgan", row.deleted_by, "Asoschi")
ck("sabab yozilgan", row.reason, "Ikki marta kiritilgan")
ck("qaysi yozuv edi", row.payment_id, PID)
ARCH = row.id
db.close()

print("\n=== 4. Arxiv ro'yxati ko'rinadi ===")
r = c.get("/api/payments/deleted", headers=F)
ck("200", r.status_code, 200)
ck("1 ta qator", len(r.json()), 1)
ck("sabab ro'yxatda ham bor", r.json()[0]["reason"],
   "Ikki marta kiritilgan")
r = c.get("/api/payments/deleted", headers=A)
ck("administratorga yopiq", r.status_code, 403)

print("\n=== 5. Asoschi QAYTARA oladi ===")
r = c.post(f"/api/payments/deleted/{ARCH}/restore", headers=M)
ck("moliyachiga yopiq (faqat asoschi)", r.status_code, 403)
r = c.post(f"/api/payments/deleted/{ARCH}/restore", headers=F)
ck("asoschiga ruxsat", r.status_code, 200)
r = c.get(f"/api/students/{SID}", headers=A)
ck("balans qaytdi", r.json()["balance"], 500000)

print("\n=== 6. Ikkinchi marta qaytarib bo'lmaydi (dubl bo'lmasin) ===")
r = c.post(f"/api/payments/deleted/{ARCH}/restore", headers=F)
ck("400 qaytadi", r.status_code, 400)
r = c.get(f"/api/students/{SID}", headers=A)
ck("balans o'zgarmadi", r.json()["balance"], 500000)

print("\n=== 7. Qarz (charge) o'chirilsa ham arxivga tushadi ===")
r = c.post(f"/api/students/{SID}/payments", headers=A,
           json={"amount": 300000, "kind": "charge"})
CID = r.json()["id"]
r = c.delete(f"/api/payments/{CID}?reason=Xato hisoblangan", headers=F)
ck("o'chirildi", r.status_code, 200)
db = SessionLocal()
ck("arxivda 2 ta", db.query(models.DeletedPayment).count(), 2)
last = (db.query(models.DeletedPayment)
        .order_by(models.DeletedPayment.id.desc()).first())
ck("manfiy summa saqlandi", last.amount, -300000)
ck("turi charge", last.kind, "charge")
db.close()

print("\n=== 8. Sababsiz o'chirish ham ishlaydi ===")
r = c.post(f"/api/students/{SID}/payments", headers=A,
           json={"amount": 111000, "kind": "payment", "method": "cash",
                 "client_key": "arch-2"})
r = c.delete(f"/api/payments/{r.json()['id']}", headers=F)
ck("o'chirildi", r.status_code, 200)

print("\n=== 9. Xato ogohlantirishi: bosib turish ishlaydi ===")
import main as M2
M2._ALERT_SEEN.clear()
db = SessionLocal()
# Telegram sozlanmagan - False qaytaradi, lekin yiqilmaydi
res1 = M2._alert_founders(db, "/api/test", "GET", "Admin",
                          "Traceback\nValueError: sinov")
ck("botsiz jimgina False", res1, False)
db.close()
# Bosib turish mantig'ini alohida tekshiramiz
import notify as _n
_orig_enabled, _orig_send = _n.enabled, _n.send
sent = []
_n.enabled = lambda: True
_n.send = lambda chat, text: (sent.append((chat, text)) or True)
db = SessionLocal()
u = db.query(models.User).filter(models.User.username == "asos").first()
u.telegram_chat_id = "12345"     # xodim Telegrami (2026-08-15)
db.commit()
M2._ALERT_SEEN.clear()
ck("1-xato yuborildi",
   M2._alert_founders(db, "/api/x", "GET", "Admin", "Tr\nKeyError: a"),
   True)
ck("AYNI xato darrov qayta yuborilmaydi",
   M2._alert_founders(db, "/api/x", "GET", "Admin", "Tr\nKeyError: a"),
   False)
ck("BOSHQA xato yuboriladi",
   M2._alert_founders(db, "/api/y", "GET", "Admin", "Tr\nKeyError: b"),
   True)
ck("jami 2 ta xabar", len(sent), 2)
ck("xabarda manzil bor", "/api/x" in sent[0][1], True)
ck("xabarda kim duch kelgani bor", "Admin" in sent[0][1], True)
db.close()
_n.enabled, _n.send = _orig_enabled, _orig_send

print("\n=== 10. Telegram ulash: kod beriladi, bog'lanadi ===")
db = SessionLocal()          # 9-bandda qo'lda qo'yilgan chatni tozalaymiz
db.query(models.User).filter(models.User.username == "asos").first(
    ).telegram_chat_id = None
db.commit(); db.close()
r = c.get("/api/me/telegram", headers=F)
ck("200", r.status_code, 200)
d = r.json()
ck("kod berildi", bool(d.get("code")) and len(d["code"]) == 6, True)
CODE = d["code"]
r2 = c.get("/api/me/telegram", headers=F)
ck("kod o'zgarmaydi", r2.json()["code"], CODE)
ck("hali ulanmagan deb ko'rsatadi", r2.json()["linked"], False)

# Webhook orqali ulanish (bot sozlangan holatni taqlid qilamiz)
import notify as _n2
_n2.enabled = lambda: True
_n2.send = lambda chat, text: True
_n2.webhook_secret = lambda: "sinov"
r = c.post("/api/telegram/webhook?secret=sinov",
           json={"message": {"chat": {"id": 777},
                             "text": f"/start {CODE}"}})
ck("webhook qabul qildi", r.status_code, 200)
db = SessionLocal()
u = db.query(models.User).filter(models.User.username == "asos").first()
ck("chat bog'landi", u.telegram_chat_id, "777")
db.close()
r = c.get("/api/me/telegram", headers=F)
ck("endi ulangan", r.json()["linked"], True)
r = c.delete("/api/me/telegram", headers=F)
ck("aloqa uzildi", r.status_code, 200)
ck("holat yangilandi", c.get("/api/me/telegram", headers=F)
   .json()["linked"], False)

print("\n" + ("HAMMASI OK" if not fails
              else f"{len(fails)} ta XATO: {fails}"))
sys.exit(1 if fails else 0)
