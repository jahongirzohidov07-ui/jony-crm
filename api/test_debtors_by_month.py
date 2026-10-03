"""QARZDORLAR OY KESIMIDA (2026-10-03, Jahongir: "o'tgan oy, undan
oldingi oyda qolib ketgan qarzdorlarni ko'rish").
Tekshiriladi: oylar bo'yicha qoldiq = balans; to'lov eng eski oyni
yopadi; oyi ko'rsatilgan chegirma o'z oyini; period filtri."""
import os, sys, tempfile
from datetime import date, datetime

_DB = os.path.join(tempfile.gettempdir(), "debt_month.sqlite")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB
if os.path.exists(_DB):
    os.remove(_DB)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient   # noqa: E402
import main, models, roles, entry, common   # noqa: E402,F401
from database import SessionLocal           # noqa: E402
from auth import hash_password              # noqa: E402

common._ensure_month_charges = lambda db, **kw: None
c = TestClient(main.app)
fails = []


def ck(name, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + name + f": {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


db = SessionLocal()
b = models.Branch(name="Zafar"); db.add(b); db.commit()
db.add(models.User(username="asos", password_hash=hash_password("x"),
                   full_name="A", role=roles.FOUNDER, is_active=1))
db.commit()
S = []
for n in ("Ali", "Vali", "Gani"):
    s = models.Student(full_name=n, branch_id=b.id, status="active",
                       enrolled_date=date(2026, 7, 1))
    db.add(s); db.commit(); S.append(s.id)


def pay(sid, amt, kind, period=None, at=None):
    db.add(models.Payment(student_id=sid, amount=amt, kind=kind, period=period,
                          method="cash" if kind == "payment" else None,
                          created_at=at or datetime(2026, 10, 1, 6)))


# Ali: avg 480 + sen 540 + okt 540 yechildi; 600 to'ladi -> avg yopiladi,
# sen 120 qoldi... 600-480=120 sen'dan -> sen 420, okt 540
for P in ("2026-08", "2026-09", "2026-10"):
    pay(S[0], -480_000 if P == "2026-08" else -540_000, "charge", P)
pay(S[0], 600_000, "payment")
# Vali: faqat okt qarzi, sen chegirmasi sen'ni yopadi
pay(S[1], -540_000, "charge", "2026-09")
pay(S[1], 540_000, "discount", "2026-09")
pay(S[1], -540_000, "charge", "2026-10")
# Gani: qarzi yo'q
pay(S[2], -540_000, "charge", "2026-09"); pay(S[2], 540_000, "payment")
db.commit()

bp = common  # noqa
import finance  # noqa: E402
m = finance._debt_by_period(db, S)
ck("Ali oylari", m.get(S[0]), {"2026-09": 420_000, "2026-10": 540_000})
ck("Vali faqat okt", m.get(S[1]), {"2026-10": 540_000})
ck("Gani yo'q", S[2] in m, False)
db.close()

H = {"Authorization": "Bearer " + c.post("/api/auth/login", json={
    "username": "asos", "password": "x"}).json()["access_token"]}
d = c.get("/api/debtors", headers=H).json()
ck("jami", (d["count"], d["total_debt"]), (2, 1_500_000))
ck("oylar ro'yxati", d["months"], [
    {"period": "2026-10", "count": 2, "sum": 1_080_000},
    {"period": "2026-09", "count": 1, "sum": 420_000}])
ali = next(r for r in d["rows"] if r["full_name"] == "Ali")
ck("qator oylari = qarz", sum(x["amount"] for x in ali["months"]), ali["debt"])
d = c.get("/api/debtors?period=2026-09", headers=H).json()
ck("sentabr: faqat Ali", [r["full_name"] for r in d["rows"]], ["Ali"])
ck("sentabr qarzi", (d["period_debt"], d["rows"][0]["period_debt"]),
   (420_000, 420_000))
d = c.get("/api/debtors?period=bad", headers=H).json()
ck("noto'g'ri oy — filtr yo'q", d["count"], 2)
print()
if fails:
    print(f"{len(fails)} ta XATO: {fails}"); sys.exit(1)
print("HAMMASI OK")
