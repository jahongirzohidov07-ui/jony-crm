"""TO'LOVNI TUZATISH SO'ROVI (2026-08-15).

Jahongir: "masalan sotuv manager tolovni notogri urvordi, shuni
ozgartirish qilib sorov yuborsa filial rahbari yoki moliyachiga borsa
yoki asoschiga tasdiqlavorsa ozgarsin, chunki shunaqa holat boldi u
menga aloqaga chiqadi men uni topaman ozgartiraman vaqt ketadi".
"""
import os, sys
os.environ["DATABASE_URL"] = "sqlite:////tmp/payfix.db"
if os.path.exists("/tmp/payfix.db"):
    os.remove("/tmp/payfix.db")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                         # noqa: E402
import entry                                       # noqa: E402
from database import SessionLocal                  # noqa: E402
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
b1 = models.Branch(name="Bekobod 1"); b2 = models.Branch(name="Yangiyer")
db.add_all([b1, b2]); db.commit()
B1, B2 = b1.id, b2.id
st = models.Student(full_name="Karimov Aziz", branch_id=B1,
                    status="active")
db.add(st); db.commit(); SID = st.id
for uu in (
    ("sotuv", "Sotuv menejeri", "sales_manager", B1),
    ("rahbar", "Filial rahbari", "branch_manager", B1),
    ("rahbar2", "Yangiyer rahbari", "branch_manager", B2),
    ("mol", "Moliyachi", "finance_director", None),
    ("asos", "Asoschi", "founder", None),
):
    db.add(models.User(username=uu[0], full_name=uu[1], role=uu[2],
                       branch_id=uu[3], password_hash=hash_password("x"),
                       is_active=1))
db.commit(); db.close()


def tok(u):
    return {"Authorization": "Bearer " + c.post(
        "/api/auth/login", json={"username": u, "password": "x"})
        .json()["access_token"]}


SOT, RAH, RAH2, MOL, ASOS = (tok("sotuv"), tok("rahbar"), tok("rahbar2"),
                             tok("mol"), tok("asos"))

print("=== 1. Sotuv menejeri XATO summa kiritdi ===")
r = c.post(f"/api/students/{SID}/payments", headers=SOT,
           json={"amount": 4000000, "kind": "payment", "method": "cash",
                 "client_key": "fix-1"})
ck("to'lov kiritildi", r.status_code, 200)
PID = r.json()["id"]
db = SessionLocal()
ck("balans 4 mln", student_balance(db, SID), 4000000)
db.close()

print("\n=== 2. O'zi tuzata OLMAYDI (huquqi yo'q) ===")
r = c.put(f"/api/payments/{PID}", headers=SOT, json={"amount": 400000})
ck("403", r.status_code, 403)

print("\n=== 3. Lekin SO'ROV yubora oladi ===")
r = c.post(f"/api/payments/{PID}/fix-request", headers=SOT, json={
    "kind": "amount", "amount": 400000,
    "reason": "Nol ortiqcha bosilib ketdi"})
ck("so'rov yuborildi", r.status_code, 200)
FID = r.json()["id"]
ck("xabar tushunarli", "vazifa bo'lib tushdi" in r.json()["message"], True)

print("\n=== 4. Sababsiz so'rov o'tmaydi ===")
r = c.post(f"/api/payments/{PID}/fix-request", headers=SOT, json={
    "kind": "amount", "amount": 1, "reason": ""})
ck("400", r.status_code, 400)

print("\n=== 5. Uchala tasdiqlovchiga VAZIFA tushdi ===")
db = SessionLocal()
tasks = (db.query(models.Task)
         .filter(models.Task.title.like("To'lovni tuzatish so'rovi%")).all())
who = sorted({db.query(models.User).get(t.assignee_id).full_name
              for t in tasks})
ck("filial rahbari, moliyachi, asoschi", who,
   ["Asoschi", "Filial rahbari", "Moliyachi"])
ck("boshqa filial rahbariga tushmadi",
   "Yangiyer rahbari" in who, False)
db.close()

print("\n=== 6. Ro'yxatda ko'rinadi ===")
r = c.get("/api/payments/fix-requests", headers=RAH)
ck("rahbarga ko'rinadi", len(r.json()), 1)
ck("tasdiqlay oladi", r.json()[0]["can_approve"], True)
ck("nima o'zgarishi yozilgan",
   "4 000 000 -> 400 000" in r.json()[0]["what"], True)
r = c.get("/api/payments/fix-requests", headers=SOT)
ck("so'ragan xodim o'zinikini ko'radi", len(r.json()), 1)
ck("lekin tasdiqlay olmaydi", r.json()[0]["can_approve"], False)
r = c.get("/api/payments/fix-requests", headers=RAH2)
ck("boshqa filial rahbariga ko'rinmaydi", len(r.json()), 0)

print("\n=== 7. Sotuv menejeri O'ZI tasdiqlay olmaydi ===")
r = c.post(f"/api/payments/fix-requests/{FID}/approve", headers=SOT)
ck("403", r.status_code, 403)

print("\n=== 8. Filial rahbari TASDIQLADI -> summa o'zgardi ===")
r = c.post(f"/api/payments/fix-requests/{FID}/approve", headers=RAH)
ck("tasdiqlandi", r.status_code, 200)
db = SessionLocal()
ck("balans to'g'rilandi", student_balance(db, SID), 400000)
ck("yozuv o'chmadi",
   db.query(models.Payment).get(PID) is not None, True)
fx = db.query(models.PaymentFixRequest).get(FID)
ck("holati approved", fx.status, "approved")
ck("kim tasdiqlagani yozildi", fx.decided_by, "Filial rahbari")
ck("so'ragan xodimga xabar bordi",
   db.query(models.Task).filter(
       models.Task.title.like("To'lov tuzatildi%")).count() >= 1, True)
db.close()

print("\n=== 9. Ikkinchi marta tasdiqlab bo'lmaydi ===")
r = c.post(f"/api/payments/fix-requests/{FID}/approve", headers=MOL)
ck("400", r.status_code, 400)

print("\n=== 10. Usulni tuzatish ===")
r = c.post(f"/api/payments/{PID}/fix-request", headers=SOT, json={
    "kind": "method", "method": "terminal",
    "reason": "Naqd emas, terminaldan tushgan"})
F2 = r.json()["id"]
r = c.post(f"/api/payments/fix-requests/{F2}/approve", headers=MOL)
ck("moliyachi tasdiqladi", r.status_code, 200)
db = SessionLocal()
ck("usul o'zgardi", db.query(models.Payment).get(PID).method, "terminal")
db.close()

print("\n=== 11. Bir yozuvga ikkita ochiq so'rov bo'lmaydi ===")
c.post(f"/api/payments/{PID}/fix-request", headers=SOT,
       json={"kind": "note", "note": "izoh", "reason": "sinov"})
r = c.post(f"/api/payments/{PID}/fix-request", headers=SOT,
           json={"kind": "note", "note": "yana", "reason": "sinov 2"})
ck("400 — ochiq so'rov bor", r.status_code, 400)

print("\n=== 12. Rad etish ===")
r = c.get("/api/payments/fix-requests?status=pending", headers=ASOS)
F3 = r.json()[0]["id"]
r = c.post(f"/api/payments/fix-requests/{F3}/reject", headers=ASOS,
           json={"note": "Izoh to'g'ri edi"})
ck("rad etildi", r.status_code, 200)
db = SessionLocal()
fx = db.query(models.PaymentFixRequest).get(F3)
ck("holati rejected", fx.status, "rejected")
ck("sabab saqlandi", fx.decision_note, "Izoh to'g'ri edi")
ck("izoh O'ZGARMADI",
   db.query(models.Payment).get(PID).note is None
   or "izoh" not in (db.query(models.Payment).get(PID).note or ""), True)
db.close()

print("\n=== 13. Bekor qilish so'rovi — arxivga tushadi ===")
r = c.post(f"/api/payments/{PID}/fix-request", headers=SOT, json={
    "kind": "delete", "reason": "Bu to'lov umuman bo'lmagan"})
F4 = r.json()["id"]
db = SessionLocal()
bal = student_balance(db, SID)
db.close()
r = c.post(f"/api/payments/fix-requests/{F4}/approve", headers=ASOS)
ck("tasdiqlandi", r.status_code, 200)
db = SessionLocal()
ck("yozuv payments'dan olindi",
   db.query(models.Payment).get(PID) is None, True)
ck("balans 0 ga qaytdi", student_balance(db, SID), 0)
arch = (db.query(models.DeletedPayment)
        .filter(models.DeletedPayment.payment_id == PID).first())
ck("ARXIVDA saqlandi", arch is not None, True)
ck("summa arxivda", arch.amount, 400000)
ck("sabab arxivda", arch.reason, "Bu to'lov umuman bo'lmagan")
ck("balans o'zgargani to'g'ri", round(bal - student_balance(db, SID)),
   400000)
db.close()

print("\n=== 14. Yo'q yozuvga so'rov — 404 ===")
r = c.post("/api/payments/999999/fix-request", headers=SOT,
           json={"kind": "amount", "amount": 1000, "reason": "sinov"})
ck("404", r.status_code, 404)

print("\n" + ("HAMMASI OK" if not fails
              else f"{len(fails)} ta XATO: {fails}"))
sys.exit(1 if fails else 0)
