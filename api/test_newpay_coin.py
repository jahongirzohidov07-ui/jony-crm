"""YANGI O'QUVCHI 3-DARSGACHA TO'LASA +10 COIN (2026-09-28).

Jahongir: "yangi tolov qilganlarga 3-darsgacha qilsa 10 coin berilishi
kerak". Misol: Abduvaliyev Shaxriyor — 23 va 25-sentabr darsga keldi,
28-sentabr (3-darsi kuni) to'ladi, 0 coin oldi (sana qoidasi 16+ = 0).

Tekshiriladi:
  1. 2 ta darsdan keyin (3-darsi kuni) birinchi to'lov -> +10.
  2. Hali darsga kelmay oldindan to'lagan -> +10.
  3. 3 ta darsga kelib, keyin to'lagan -> yangi bonus YO'Q.
  4. Oldin to'lovi bor o'quvchi -> yangi bonus YO'Q.
  5. Eski o'quvchi (100 kun oldin boshlagan, JonyOS'da birinchi to'lovi)
     -> yangi bonus YO'Q.
  6. Shu oy ikkinchi to'lov -> qo'shimcha coin yo'q (jami 10).
  7. Coin "pay_ontime" + ref_id=to'lov: to'lov o'chirilsa qaytadi.
  8. Orqaga to'ldirish: qoida yo'qligida to'laganlarga +10, +5 olganga +5;
     ikkinchi yurishda hech narsa qo'shilmaydi; eski/3+ darslilar tegilmaydi.
"""
import os
import sys
import tempfile
from datetime import date, datetime, timedelta

_DIR = os.path.join(tempfile.gettempdir(), "newpay_coin_test")
os.makedirs(_DIR, exist_ok=True)
_DB = os.path.join(_DIR, "db.sqlite")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace(chr(92), "/")
if os.path.exists(_DB):
    os.remove(_DB)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                         # noqa: E402
import students                                    # noqa: E402
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
db = SessionLocal()
b = models.Branch(name="Bekobod 1"); db.add(b); db.commit()
BID = b.id
db.add(models.User(username="adm", password_hash=hash_password("x"),
                   full_name="Baxriniso", role=roles.ADMINISTRATOR,
                   branch_id=BID))
t = models.Teacher(full_name="Shirinabonu", is_active=1, branch_id=BID)
db.add(t); db.commit()
g = models.Group(name="Cambridge", branch_id=BID, teacher_id=t.id,
                 lesson_price=45_000, standard_lessons_per_month=12,
                 monthly_fee=540_000, lesson_days="")
db.add(g); db.commit()
GID = g.id
# O'tgan darslar: bugundan 9, 7, 5, 3 kun oldin
LESSONS = []
for k in (9, 7, 5, 3):
    les = models.Lesson(group_id=GID, teacher_id=t.id,
                        date=TODAY - timedelta(days=k))
    db.add(les); db.commit(); LESSONS.append(les.id)


def student(name, came=0, enrolled=None, status="active"):
    s = models.Student(full_name=name, branch_id=BID, status=status,
                       group_id=GID,
                       enrolled_date=enrolled or (TODAY - timedelta(days=9)))
    db.add(s); db.commit()
    for lid in LESSONS[:came]:
        db.add(models.Attendance(student_id=s.id, lesson_id=lid, present=1))
    db.commit()
    return s.id


A = student("Abduvaliyev Shaxriyor", came=2)
B = student("Oldindan to'lagan", came=0)
C = student("Uch darsdan keyin", came=3)
D = student("Oldin to'lagan", came=1)
db.add(models.Payment(student_id=D, amount=100_000, kind="payment",
                      created_at=datetime.utcnow() - timedelta(days=6)))
E = student("Eski o'quvchi", came=0, enrolled=TODAY - timedelta(days=100))
db.commit()
db.close()

H = {"Authorization": "Bearer " + client.post(
    "/api/auth/login", json={"username": "adm", "password": "x"}
).json()["access_token"]}


def pay(sid, amount=540_000):
    r = client.post(f"/api/students/{sid}/payments", headers=H,
                    json={"amount": amount, "kind": "payment",
                          "method": "card", "force": True})
    assert r.status_code == 200, r.text
    return r.json()["id"]


def coins(sid):
    s = SessionLocal()
    rows = [(c.amount, c.source, c.ref_id, c.note or "") for c in
            s.query(models.CoinEntry).filter(
                models.CoinEntry.student_id == sid).all()]
    s.close()
    return rows


def newbonus(sid):
    return sum(a for a, _s, _r, n in coins(sid) if "Yangi o'quvchi" in n)


print("=== 1-6. To'lov paytida ===")
pa = pay(A)
ck("1. 2 darsdan keyin to'lov: +10", newbonus(A), 10)
rows = coins(A)
ck("7. manba pay_ontime, ref=to'lov",
   [(s_, r) for _a, s_, r, n in rows if "Yangi" in n], [("pay_ontime", pa)])
pay(B)
ck("2. darsga kelmay oldindan to'lagan: +10", newbonus(B), 10)
pay(C)
ck("3. 3 darsdan keyin: yangi bonus yo'q", newbonus(C), 0)
pay(D)
ck("4. oldin to'lagan: yangi bonus yo'q", newbonus(D), 0)
pay(E)
ck("5. eski o'quvchi: yangi bonus yo'q", newbonus(E), 0)
pay(A, 100_000)
ck("6. ikkinchi to'lov: jami coin 10", sum(a for a, *_ in coins(A)), 10)

print("=== 8. Orqaga to'ldirish ===")
db = SessionLocal()
F = student("Qoidadan oldin to'lagan", came=1)
G = student("Sanadan +5 olgan", came=2)
Hs = student("Uch darsdan keyin (eski)", came=3)
db = SessionLocal()
_when = datetime.utcnow() - timedelta(hours=1)
pf = models.Payment(student_id=F, amount=540_000, kind="payment",
                    created_at=_when)
pg = models.Payment(student_id=G, amount=540_000, kind="payment",
                    created_at=_when)
ph = models.Payment(student_id=Hs, amount=540_000, kind="payment",
                    created_at=_when)
db.add_all([pf, pg, ph]); db.commit()
db.add(models.CoinEntry(student_id=G, amount=5, source="pay_ontime",
                        ref_id=pg.id, note="10-sanagacha (+5)",
                        created_by="Avtomat"))
db.commit()
got = students._newpay_backfill(db, TODAY - timedelta(days=30))
names = sorted(x["name"] for x in got)
# D ning BIRINCHI to'lovi (6 kun oldin, 1 darsdan keyin) ham qoidaga
# mos — u ham oladi; bugungi ikkinchi to'lovi esa olmagan (4-band).
ck("F, G va D ning birinchi to'lovi to'ldirildi", names,
   sorted(["Qoidadan oldin to'lagan", "Sanadan +5 olgan",
           "Oldin to'lagan"]))
ck("D jami 10", sum(a for a, *_ in coins(D)), 10)
ck("F jami 10", sum(a for a, *_ in coins(F)), 10)
ck("G jami 10 (5+5)", sum(a for a, *_ in coins(G)), 10)
ck("H (3 dars) tegilmadi", coins(Hs), [])
ck("A, B takror olmadi", (sum(a for a, *_ in coins(A)),
                          sum(a for a, *_ in coins(B))), (10, 10))
again = students._newpay_backfill(db, TODAY - timedelta(days=30))
ck("ikkinchi yurish: hech narsa", again, [])
db.close()

print("\nNATIJA:", "HAMMASI OK" if not fails else f"{len(fails)} XATO: {fails}")
sys.exit(1 if fails else 0)
