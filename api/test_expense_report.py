"""XARAJATLAR HISOBOTI (2026-10-02).

Jahongir: "harajatlar kesimida ham nechta qaysinga qaysi oyda qancha
harajat ketyabdi hisobotlarda to'g'ri tushunarli ... chartlar bilan".

Tekshiriladi:
  1. Oylar kesimi (bo'sh oy ham), har tur: summa, yozuvlar soni, dona.
  2. Ustozlarga berilgan oylik "Ustoz oyligi" bo'lib qo'shiladi.
  3. Guruhlar jami va ulushi; jami = oylar yig'indisi.
  4. Oynadan tashqaridagi yozuv kirmaydi; filial chegarasi.
  5. Administrator ko'rmaydi (403).
"""
import os
import sys
import tempfile
from datetime import date

_DIR = os.path.join(tempfile.gettempdir(), "expense_report_test")
os.makedirs(_DIR, exist_ok=True)
_DB = os.path.join(_DIR, "db.sqlite")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace(chr(92), "/")
if os.path.exists(_DB):
    os.remove(_DB)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                         # noqa: E402
import entry                                       # noqa: E402,F401
import common as _cm_stub                          # noqa: E402
from database import SessionLocal                  # noqa: E402
from auth import hash_password                     # noqa: E402

_cm_stub._ensure_month_charges = lambda db, **kw: None

client = TestClient(main.app)
fails = []


def ck(name, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + name + f": {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


Y = 2026
db = SessionLocal()
a = models.Branch(name="Zafar"); bb = models.Branch(name="Bekobod")
db.add_all([a, bb]); db.commit()
A, B = a.id, bb.id
for login, role, br in (("asos", roles.FOUNDER, None),
                        ("rah", roles.BRANCH_MANAGER, B),
                        ("adm", roles.SALES_MANAGER, A)):
    db.add(models.User(username=login, password_hash=hash_password("x"),
                       full_name=login, role=role, branch_id=br,
                       is_active=1))
t = models.Teacher(full_name="Elena", is_active=1, branch_id=A)
db.add(t); db.commit()


def exp(d, cat, amt, br=A, qty=None):
    db.add(models.Expense(date=d, category=cat, amount=amt, branch_id=br,
                          method="cash", qty=qty))


exp(date(Y, 5, 31), "rent", 9_999_999)          # oynadan tashqari
exp(date(Y, 8, 1), "rent", 3_000_000)
exp(date(Y, 9, 1), "rent", 3_000_000)
exp(date(Y, 9, 5), "marker", 60_000, qty=4)
exp(date(Y, 9, 20), "marker", 30_000, qty=2)
exp(date(Y, 9, 10), "electricity", 400_000)
exp(date(Y, 9, 10), "rent", 2_000_000, br=B)    # boshqa filial
db.add(models.TeacherPayment(teacher_id=t.id, amount=1_500_000,
                             kind="salary", paid_on=date(Y, 9, 30),
                             method="cash", branch_id=A))
db.commit()
db.close()


def tok(u):
    return {"Authorization": "Bearer " + client.post(
        "/api/auth/login", json={"username": u, "password": "x"}
    ).json()["access_token"]}


URL = "/api/reports/expenses"
d = client.get(f"{URL}?year={Y}&month=9&months=3&branch_id={A}",
               headers=tok("asos")).json()

print("=== 1. Oylar va turlar ===")
ck("oylar (iyul bo'sh)", [(m["period"], m["total"], m["count"])
                          for m in d["months"]],
   [(f"{Y}-07", 0, 0), (f"{Y}-08", 3_000_000, 1),
    (f"{Y}-09", 4_990_000, 5)])
cat = {c["key"]: c for c in d["categories"]}
ck("ijara: 2 oy, 2 ta yozuv", (cat["rent"]["total"], cat["rent"]["count"],
                                cat["rent"]["by_month"][f"{Y}-09"]),
   (6_000_000, 2, 3_000_000))
ck("marker: soni va dona", (cat["marker"]["count"], cat["marker"]["qty"],
                            cat["marker"]["total"]), (2, 6, 90_000))
ck("tur nomi va guruhi", (cat["electricity"]["label"],
                          cat["electricity"]["group"]),
   ("Elektr toki", "communal"))

print("\n=== 2. Ustoz oyligi ===")
ck("ustoz oyligi qo'shildi", (cat["teacher_salary"]["total"],
                              cat["teacher_salary"]["group"]),
   (1_500_000, "teacher_salary"))

print("\n=== 3. Guruhlar va jami ===")
grp = {g["key"]: g for g in d["groups"]}
ck("jami", d["total"], 7_990_000)
ck("jami = oylar yig'indisi", sum(m["total"] for m in d["months"]),
   d["total"])
ck("ijara ulushi %", grp["rent"]["share"], 75.1)
ck("sentabr guruhlari", d["months"][2]["groups"],
   {"rent": 3_000_000, "office": 90_000, "communal": 400_000,
    "teacher_salary": 1_500_000})

print("\n=== 4. Filial chegarasi ===")
r = client.get(f"{URL}?year={Y}&month=9&months=3", headers=tok("rah")).json()
ck("filial rahbari — faqat o'z filiali", r["total"], 2_000_000)

print("\n=== 5. Ruxsat ===")
ck("administrator — 403", client.get(f"{URL}?year={Y}&month=9",
                                     headers=tok("adm")).status_code, 403)

print()
if fails:
    print(f"{len(fails)} ta XATO: {fails}")
    sys.exit(1)
print("HAMMASI OK")
