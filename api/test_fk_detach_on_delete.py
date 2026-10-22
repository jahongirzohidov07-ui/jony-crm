"""BOG'LANGAN TO'LOV / LIDNI O'CHIRISH (2026-10-22).

Prod loglarida (2026-10-22 05:27–06:21 UTC) 500 xatolar:
  - payments 18631 -> payment_fix_requests_payment_id_fkey
  - leads 516      -> wheel_spins_lead_id_fkey

Sabab: to'lovni tuzatish so'rovi ("o'chirish") tasdiqlanganda yoki
asoschi to'lovni o'chirganda, to'lovga hali so'rov bog'langan edi;
lid o'chirilganda unga g'ildirak aylanishi bog'langan edi. Postgres
bunday qatorni o'chirishga ruxsat bermaydi. SQLite'da ham FK yoqib
tekshiramiz.

Tekshiriladi:
  1. "O'chirish" so'rovi tasdiqlanadi (200); so'rov tarixda qoladi,
     havolasi bo'shaydi.
  2. Asoschi to'lovni o'chiradi — kutilayotgan so'rov rad etiladi,
     pul qaytarish so'rovi saqlanadi, havolalar bo'shaydi.
  3. Ommaviy (query.delete) o'chirish ham yiqilmaydi.
  4. G'ildirak, ijtimoiy xabar, bot ro'yxati, joylashtirish testi
     bog'langan lid o'chiriladi — yozuvlar qoladi, lead_id bo'shaydi.
  5. Login ichidagi oylik ish yiqilsa ham login 200 qaytaradi.
"""
import os
import sys
import tempfile

_DIR = os.path.join(tempfile.gettempdir(), "fk_detach_on_delete_test")
os.makedirs(_DIR, exist_ok=True)
_DB = os.path.join(_DIR, "db.sqlite")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace(chr(92), "/")
if os.path.exists(_DB):
    os.remove(_DB)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import event                       # noqa: E402
from fastapi.testclient import TestClient          # noqa: E402
import database                                    # noqa: E402


@event.listens_for(database.engine, "connect")
def _fk_on(conn, _rec):
    # Prod (Postgres) kabi — bog'langan yozuvli qatorni o'chirib bo'lmaydi
    conn.execute("PRAGMA foreign_keys=ON")


import main, models, roles                         # noqa: E402
import entry                                       # noqa: E402,F401
import common                                      # noqa: E402
from database import SessionLocal                  # noqa: E402
from auth import hash_password                     # noqa: E402

c = TestClient(main.app, raise_server_exceptions=False)
fails = []


def ck(name, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + name + f": {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


db = SessionLocal()
b = models.Branch(name="Chilonzor"); db.add(b); db.commit()
db.add(models.User(username="asos", password_hash=hash_password("x"),
                   full_name="Asoschi", role=roles.FOUNDER,
                   branch_id=b.id, is_active=1))
st = models.Student(full_name="Ali Valiyev", branch_id=b.id,
                    status="active")
db.add(st); db.commit()
SID, BID = st.id, b.id

# Oylik avtomat ish bu testga aralashmasin (5-bo'limda alohida tekshiriladi)
_orig_mc = common._ensure_month_charges
common._ensure_month_charges = lambda db, **kw: None

H = {"Authorization": "Bearer " + c.post(
    "/api/auth/login", json={"username": "asos", "password": "x"}
).json()["access_token"]}


def pay(amount=100_000, kind="payment", note=None):
    p = models.Payment(student_id=SID, amount=amount, kind=kind,
                       method="cash", note=note)
    db.add(p); db.commit()
    return p


def fix(p, kind="delete"):
    r = models.PaymentFixRequest(
        payment_id=p.id, student_id=SID, branch_id=BID, kind=kind,
        old_amount=p.amount, reason="xato kiritildi", status="pending",
        requested_by="Sotuv menejeri")
    db.add(r); db.commit()
    return r


print("=== 1. \"O'CHIRISH\" SO'ROVI TASDIQLANADI ===")
p1 = pay()
r1 = fix(p1)
P1, R1 = p1.id, r1.id
r = c.post(f"/api/payments/fix-requests/{R1}/approve", headers=H, json={})
ck("tasdiqlandi (500 emas)", r.status_code, 200)
db.expire_all()
ck("to'lov payments'dan chiqdi", db.query(models.Payment).get(P1), None)
ck("to'lov arxivda", db.query(models.DeletedPayment)
   .filter_by(payment_id=P1).count(), 1)
ck("so'rov tarixda qoldi", db.query(models.PaymentFixRequest)
   .get(R1).status, "approved")
ck("so'rov havolasi bo'shadi", db.query(models.PaymentFixRequest)
   .get(R1).payment_id, None)
r = c.get("/api/payments/fix-requests?status=all", headers=H)
ck("so'rovlar ro'yxati ochiladi", r.status_code, 200)

print("\n=== 2. ASOSCHI SO'ROVI BOR TO'LOVNI O'CHIRADI ===")
p2 = pay()
r2 = fix(p2, kind="amount")
rf = models.RefundRequest(student_id=SID, amount=50_000, reason="qaytarish",
                          payment_id=p2.id)
db.add(rf); db.commit()
P2, R2, RF = p2.id, r2.id, rf.id
r = c.delete(f"/api/payments/{P2}?reason=xato", headers=H)
ck("o'chirildi (500 emas)", r.status_code, 200)
db.expire_all()
ck("to'lov payments'dan chiqdi", db.query(models.Payment).get(P2), None)
fr = db.query(models.PaymentFixRequest).get(R2)
ck("kutilayotgan so'rov rad etildi", fr.status, "rejected")
ck("so'rov havolasi bo'shadi", fr.payment_id, None)
ck("pul qaytarish so'rovi saqlandi",
   db.query(models.RefundRequest).get(RF).amount, 50_000)
ck("pul qaytarish havolasi bo'shadi",
   db.query(models.RefundRequest).get(RF).payment_id, None)

print("\n=== 3. OMMAVIY O'CHIRISH (query.delete) ===")
p3 = pay(note="[LC UP] eski to'lov")
r3 = fix(p3)
P3, R3 = p3.id, r3.id
err = None
try:
    db.query(models.Payment).filter(models.Payment.id == P3).delete(
        synchronize_session=False)
    db.commit()
except Exception as e:      # noqa: BLE001
    db.rollback()
    err = type(e).__name__
ck("ommaviy o'chirish yiqilmadi", err, None)
db.expire_all()
ck("to'lov chiqdi", db.query(models.Payment).get(P3), None)
ck("so'rov havolasi bo'shadi",
   db.query(models.PaymentFixRequest).get(R3).payment_id, None)

print("\n=== 4. BOG'LANGAN LID O'CHIRILADI ===")
lead = models.Lead(full_name="G'ildirak lidi", phone="998901112233",
                   source="visit", stage="new", branch_id=BID)
db.add(lead); db.commit()
LID = lead.id
spin = models.WheelSpin(lead_id=LID, phone=lead.phone, name=lead.full_name,
                        branch_id=BID, prize_kind="coin", prize_value=50)
msg = models.SocialMessage(lead_id=LID, phone=lead.phone, text="salom")
reg = models.AcademyBotReg(lead_id=LID, phone=lead.phone, name="Ali")
gp = models.GermanPlacementResult(
    attempt_id="att-1", payload_hash="h", lead_id=LID, branch_id=BID,
    full_name=lead.full_name, phone=lead.phone, result_json="{}",
    answers_json="{}")
db.add_all([spin, msg, reg, gp]); db.commit()
SP, MS, RG, GP = spin.id, msg.id, reg.id, gp.id
REASON = next(iter(roles.LEAD_DELETE_LABELS))
r = c.delete(f"/api/leads/{LID}?reason={REASON}", headers=H)
ck("lid o'chirildi (500 emas)", r.status_code, 200)
db.expire_all()
ck("lid chiqdi", db.query(models.Lead).get(LID), None)
ck("g'ildirak tarixi qoldi",
   db.query(models.WheelSpin).get(SP).prize_value, 50)
ck("g'ildirak havolasi bo'shadi",
   db.query(models.WheelSpin).get(SP).lead_id, None)
ck("ijtimoiy xabar havolasi bo'shadi",
   db.query(models.SocialMessage).get(MS).lead_id, None)
ck("bot ro'yxati havolasi bo'shadi",
   db.query(models.AcademyBotReg).get(RG).lead_id, None)
ck("joylashtirish testi qoldi, havola bo'shadi",
   db.query(models.GermanPlacementResult).get(GP).lead_id, None)

print("\n=== 5. LOGIN ICHIDAGI ISH YIQILSA HAM LOGIN ISHLAYDI ===")


def _broken_job(db, **kw):
    # Yo'q o'quvchiga yechim — flush FK xatosi bilan yiqiladi va sessiya
    # "rollback kerak" holatida qoladi (prod'dagi holat).
    db.add(models.Payment(student_id=999_999, amount=-1, kind="charge"))
    db.flush()


common._ensure_month_charges = _broken_job
r = c.post("/api/auth/login", json={"username": "asos", "password": "x"})
ck("login 200 (fon ishi yiqilgan bo'lsa ham)", r.status_code, 200)
common._ensure_month_charges = _orig_mc

db.close()
print()
if fails:
    print("XATOLAR:", fails)
    sys.exit(1)
print("HAMMASI OK")
