"""QAYTIB KELGANDA OYLIK YECHILMAY QOLISHI (2026-09-28).

Jahongir: "mana bu o'quvchi 3 ta darsdan beri kelyabdi lekin pul
yechilmagan ... shunaqa holatlar yana bormikan sababini topib tuzat".

Aloviddinov Asadbek: 11-sentabr asoschi "sentabr kelmagan" deb sentabr
yechimini o'chirdi (ChargeSkip), 23-sentabr o'quvchi qaytib faollashdi —
skip faollashish yechimini ham to'sib qo'ydi, pul yechilmadi.

Tekshiriladi:
  1. Skip bor, o'quvchi qaytib faollashtirildi — faollashgan kundan
     oy oxirigacha yechiladi (endpoint orqali).
  2. Avtomat faollashish (_activate_student, 3 dars / to'lov) ham xuddi shunday.
  3. Faollashishsiz skip (asoschi bila turib o'chirgan) — tegilmaydi.
  4. Oldin qolib ketganlar: skip'dan KEYIN faollashgan, yechilmagan —
     kunlik to'r yechadi (audit sanasidan); ikkinchi yurishda takror yo'q.
  5. Faollashishdan KEYIN qo'yilgan skip (asoschi qaytgandan keyingi
     yechimni o'chirgan) — hurmat qilinadi, qayta yozilmaydi.
  6. Keyingi oylar uchun skip hali ham ishlaydi (_charge_months_after).
"""
import os
import sys
import tempfile
from datetime import date, datetime, timedelta

_DIR = os.path.join(tempfile.gettempdir(), "reactivate_skip_test")
os.makedirs(_DIR, exist_ok=True)
_DB = os.path.join(_DIR, "db.sqlite")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace(chr(92), "/")
if os.path.exists(_DB):
    os.remove(_DB)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                         # noqa: E402
import entry                                       # noqa: E402
import common                                      # noqa: E402
from database import SessionLocal                  # noqa: E402
from auth import hash_password                     # noqa: E402

client = TestClient(main.app)
fails = []


def ck(name, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + name + f": {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


TODAY = roles.local_today()
NOW = f"{TODAY.year:04d}-{TODAY.month:02d}"
PRICE = 40_000
_next = date(TODAY.year + (TODAY.month == 12), TODAY.month % 12 + 1, 1)
LAST = (_next - timedelta(days=1)).day
# Qaytgan kun — oy o'rtasi (1-kun emas: aks holda "to'liq oy" bo'ladi)
BACK = TODAY.replace(day=max(2, TODAY.day - 5)) if TODAY.day >= 2 else TODAY


def left_from(d):
    """Toq kunlardagi darslar: d dan oy oxirigacha, 12 dan oshmaydi."""
    return min(len([x for x in range(d.day, LAST + 1) if x % 2 == 1]), 12)


db = SessionLocal()
b = models.Branch(name="Bekobod 1"); db.add(b); db.commit()
BID = b.id
db.add(models.User(username="adm", password_hash=hash_password("x"),
                   full_name="Admin", role=roles.ADMINISTRATOR, branch_id=BID))
t = models.Teacher(full_name="Shirinabonu", is_active=1, branch_id=BID)
db.add(t); db.commit()
g = models.Group(name="Cambridge", branch_id=BID, teacher_id=t.id,
                 lesson_price=PRICE, standard_lessons_per_month=12,
                 monthly_fee=480_000, lesson_days="")
db.add(g); db.commit()
GID = g.id
for d in range(1, LAST + 1, 2):
    db.add(models.Lesson(group_id=GID, teacher_id=t.id,
                         date=date(TODAY.year, TODAY.month, d)))
db.commit()

EARLY = datetime.utcnow() - timedelta(days=10)


def student(name, status, enrolled=None):
    s = models.Student(full_name=name, branch_id=BID, status=status,
                       group_id=GID,
                       enrolled_date=enrolled or date(TODAY.year, 1, 5))
    db.add(s); db.commit()
    return s


def skip(sid, when=EARLY):
    db.add(models.ChargeSkip(student_id=sid, period=NOW,
                             created_by="Asoschi", created_at=when))
    db.commit()


def charges(sid, period=NOW):
    s = SessionLocal()
    out = [round(-p.amount) for p in s.query(models.Payment).filter(
        models.Payment.student_id == sid, models.Payment.kind == "charge",
        models.Payment.period == period).all()]
    s.close()
    return out


a1 = student("Aloviddinov Asadbek", "archived"); skip(a1.id)
a2 = student("Sinovdan faol", "trial"); skip(a2.id)
a3 = student("Asoschi kechirgan", "active"); skip(a3.id)
a4 = student("Oldin qolib ketgan", "active"); skip(a4.id)
db.add(models.AuditLog(entity="student", entity_id=a4.id, action="activate",
                       field="status", old_value="archived",
                       new_value="active", note=BACK.isoformat(),
                       created_at=EARLY + timedelta(days=2)))
a5 = student("Qaytgandan keyin o'chirilgan", "active")
db.add(models.AuditLog(entity="student", entity_id=a5.id, action="activate",
                       field="status", old_value="archived",
                       new_value="active", note=BACK.isoformat(),
                       created_at=EARLY))
db.commit()
skip(a5.id, when=EARLY + timedelta(days=3))
IDS = dict(a1=a1.id, a2=a2.id, a3=a3.id, a4=a4.id, a5=a5.id)
db.close()

H = {"Authorization": "Bearer " + client.post(
    "/api/auth/login", json={"username": "adm", "password": "x"}
).json()["access_token"]}
WANT = [left_from(BACK) * PRICE] if left_from(BACK) else []

print("=== 1. Skip bor, o'quvchi qaytib faollashtirildi (endpoint) ===")
r = client.post(f"/api/students/{IDS['a1']}/activate", headers=H,
                json={"on": BACK.isoformat()})
ck("faollashdi", r.status_code, 200)
ck("qaytgan kundan oy oxirigacha yechildi", charges(IDS["a1"]), WANT)
ck("javobda hisob bor", bool(r.json().get("charge")), bool(WANT))

print("\n=== 2. Avtomat faollashish (3 dars / to'lov) ===")
db = SessionLocal()
s2 = db.query(models.Student).get(IDS["a2"])
common._activate_student(db, s2, on=BACK, reason="3 ta darsga keldi")
db.commit(); db.close()
ck("avtomat faollashishda ham yechildi", charges(IDS["a2"]), WANT)

print("\n=== 3-5. Kunlik to'r ===")
db = SessionLocal()
done = entry._mc_reactivated_after_skip(db, TODAY)
db.close()
ck("asoschi kechirgan (faollashishsiz) — tegilmadi", charges(IDS["a3"]), [])
ck("oldin qolib ketgan — audit sanasidan yechildi", charges(IDS["a4"]), WANT)
ck("qaytgandan keyin o'chirilgan — qayta yozilmadi", charges(IDS["a5"]), [])
ck("to'r nechta yechdi", len(done), 1 if WANT else 0)
ck("to'r sanani to'g'ri oldi",
   [d["since"] for d in done], [BACK.isoformat()] if WANT else [])
db = SessionLocal()
again = entry._mc_reactivated_after_skip(db, TODAY)
db.close()
ck("ikkinchi yurishda takror yo'q", again, [])
ck("a1 ikki marta yechilmadi", len(charges(IDS["a1"])), len(WANT))

print("\n=== 6. Keyingi oylar skip'i hurmat qilinadi ===")
db = SessionLocal()
s6 = student("Keyingi oy skip", "trial", date(TODAY.year, 1, 5))
s6.enrolled_date = BACK
db.commit()
nxt = f"{_next.year:04d}-{_next.month:02d}"
db.add(models.ChargeSkip(student_id=s6.id, period=nxt, created_by="Asoschi"))
db.commit()
res = entry._charge_months_after(db, s6, BACK)
db.commit()
S6 = s6.id
db.close()
ck("keyingi oy yozilmadi (hali kelmagan yoki skip)", charges(S6, nxt), [])
ck("months_after natijasi bo'sh", res, [])

print()
if fails:
    print(f"XATOLAR ({len(fails)}): " + ", ".join(fails))
    sys.exit(1)
print("HAMMASI O'TDI")
