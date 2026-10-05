"""BAYRAM BILDIRISHNOMALARI (2026-10-05).

Jahongir: "event manager va boshqa bayram bildirishnomalarida kimni
tug'ilgan kuni yo yubileyi ekani ko'rinmayabdi, ustiga bossa batafsil
ma'lumot chiqaradigan qilib ber".

Tekshiriladi (/api/my/alerts):
  1. Event menejer: xodim tug'ilgan kuni, ish yubileyi, o'quvchi
     tug'ilgan kuni va tadbir — har biri ISM bilan, "detail" bilan.
  2. Detail: maydonlar (lavozim/guruh, sana, yosh/yil), tabrik matni.
  3. Muddatdan uzoq sanalar, arxivdagi o'quvchi, bekor qilingan tadbir
     chiqmaydi.
  4. Ustoz (EVENTS/STAFF_DATES huquqisiz) — bayram qatori yo'q.
"""
import os
import sys
import tempfile
from datetime import date, timedelta

_DIR = os.path.join(tempfile.gettempdir(), "celebration_alerts_test")
os.makedirs(_DIR, exist_ok=True)
_DB = os.path.join(_DIR, "db.sqlite")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace(chr(92), "/")
if os.path.exists(_DB):
    os.remove(_DB)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                         # noqa: E402
import entry                                       # noqa: E402,F401
from database import SessionLocal                  # noqa: E402
from auth import hash_password                     # noqa: E402

c = TestClient(main.app)
fails = []


def ck(name, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + name + f": {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


today = date.today()


def years_ago(n, plus_days=0):
    d = today + timedelta(days=plus_days)
    try:
        return d.replace(year=d.year - n)
    except ValueError:                       # 29-fevral
        return (d - timedelta(days=1)).replace(year=d.year - n)


db = SessionLocal()
b = models.Branch(name="Zafar"); db.add(b); db.commit()


def user(login, name, role, **kw):
    u = models.User(username=login, password_hash=hash_password("x"),
                    full_name=name, role=role, branch_id=b.id,
                    is_active=1, **kw)
    db.add(u); db.commit()
    return u


user("ev", "Event Menejer", roles.EVENT_MANAGER)
user("ust", "Oddiy Ustoz", roles.TEACHER)
user("x1", "Diyora Qurbonaliyeva", roles.SUPPORT_TEACHER,
     birth_date=years_ago(25))                          # bugun 25 yosh
user("x2", "Aziz Karimov", roles.ADMINISTRATOR,
     hired_date=years_ago(2, plus_days=2))             # 2 kundan keyin 2 yil
user("x3", "Uzoq Sana", roles.ADMINISTRATOR,
     birth_date=years_ago(30, plus_days=40))           # 40 kun — chiqmaydi
g = models.Group(name="Step 2", branch_id=b.id, monthly_fee=480_000)
db.add(g); db.commit()
db.add(models.Student(full_name="Ali Valiyev", branch_id=b.id,
                      group_id=g.id, status="active",
                      birth_date=years_ago(12, plus_days=1)))  # ertaga
db.add(models.Student(full_name="Ketgan Bola", branch_id=b.id,
                      status="archived", birth_date=years_ago(10)))
db.add(models.Event(title="Mustaqillik bayrami", kind="holiday",
                    event_date=today + timedelta(days=3), start_time="17:00",
                    place="Aktov zal", status="planned"))
db.add(models.Event(title="Bekor tadbir", kind="other",
                    event_date=today + timedelta(days=1), status="cancelled"))
db.commit()


def H(u):
    r = c.post("/api/auth/login", json={"username": u, "password": "x"})
    return {"Authorization": "Bearer " + r.json()["access_token"]}


r = c.get("/api/my/alerts", headers=H("ev"))
ck("status", r.status_code, 200)
items = [i for i in r.json()["items"] if i.get("detail")]
texts = [i["text"] for i in items]
print("   ", *texts, sep="\n    ")

print("=== 1. ISMLAR ===")
ck("xodim tug'ilgan kuni bugun", any(
    "Bugun: Diyora Qurbonaliyeva — tug'ilgan kuni" in t for t in texts), True)
ck("ish yubileyi 2 kundan keyin", any(
    "2 kundan keyin: Aziz Karimov — ish yubileyi (2 yil)" in t
    for t in texts), True)
ck("o'quvchi ertaga", any(
    "Ertaga: Ali Valiyev (o'quvchi) — tug'ilgan kuni, 12 yosh" in t
    for t in texts), True)
ck("tadbir", any("Mustaqillik bayrami" in t and "17:00" in t
                 for t in texts), True)
ck("eng yaqini birinchi", "Diyora" in texts[0], True)

print("\n=== 2. TAFSILOT ===")
det = next(i["detail"] for i in items if "Ali Valiyev" in i["text"])
f = dict(det["fields"])
ck("o'quvchi: guruh, yosh", (f.get("Guruhi"), f.get("Yoshi")),
   ("Step 2", "12 ga to'ladi"))
ck("tabrik matnida ism", "Ali Valiyev" in (det["greeting"] or ""), True)
ck("event menejerga havola Tadbirlar", det["link"], "/events")
det = next(i["detail"] for i in items if "Aziz" in i["text"])
ck("yubiley turi", det["type"], "anniversary")
det = next(i["detail"] for i in items if "Mustaqillik" in i["text"])
ck("tadbir joyi", dict(det["fields"]).get("Joyi"), "Aktov zal")

print("\n=== 3. CHIQMAYDIGANLAR ===")
for name in ("Uzoq Sana", "Ketgan Bola", "Bekor tadbir"):
    ck(f"{name} yo'q", any(name in t for t in texts), False)

print("\n=== 4. USTOZ ===")
r = c.get("/api/my/alerts", headers=H("ust"))
ck("ustozga bayram qatori yo'q",
   [i for i in r.json()["items"] if i.get("detail")], [])

print()
if fails:
    print(f"XATO: {len(fails)} ta tekshiruv o'tmadi")
    for x in fails:
        print("   - " + x)
    sys.exit(1)
print("HAMMASI O'TDI")
sys.exit(0)
