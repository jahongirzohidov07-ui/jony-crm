# -*- coding: utf-8 -*-
"""ADMIN KPI: KEYINGI BONUSGACHA QANCHA QOLDI (2026-10-02).

Jahongir: "Sarvar Ibragimov va boshqa adminlarni bonusi keyingisiga
qancha qolishi va qancha oylik olishini ko'rsatib turishi kerak va
ularni undashi kerak".

Tekshiriladi:
  1. Yig'ish 70% (pog'onalar 80% -> 1 mln, 90% -> 2 mln): keyingisi 80%,
     bonusi 1 mln, yana 480 000 so'm yig'ish kerak.
  2. 3 ta yangi mijoz (pog'onalar 5 -> 300k, 10 -> 600k): yana 2 ta,
     bonusi 300k.
  3. Eng yuqori pog'onada — keyingi pog'ona yo'q (None).
  4. Admin faqat o'z qatorini ko'radi.
"""
import os
import sys
import tempfile
from datetime import date, datetime

_DIR = os.path.join(tempfile.gettempdir(), "admin_kpi_next_test")
os.makedirs(_DIR, exist_ok=True)
_DB = os.path.join(_DIR, "db.sqlite")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace(chr(92), "/")
if os.path.exists(_DB):
    os.remove(_DB)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient           # noqa: E402
import main, models, roles                          # noqa: E402
import entry                                        # noqa: F401,E402
import common                                       # noqa: E402
from database import SessionLocal                   # noqa: E402
from auth import hash_password                      # noqa: E402

common._ensure_month_charges = lambda db, **kw: None

c = TestClient(main.app)
db = SessionLocal()
fails = []


def ck(n, got, want):
    ok = got == want
    print(("OK   " if ok else "XATO ") + f"{n}: {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(n)


YIL, OY = 2026, 8
ba = models.Branch(name="Zafar"); bb = models.Branch(name="Bekobod")
db.add_all([ba, bb]); db.commit()
common.reset_partner_cache()
ga = models.Group(name="GA", branch_id=ba.id, lesson_price=40_000)
gb = models.Group(name="GB", branch_id=bb.id, lesson_price=40_000)
db.add_all([ga, gb]); db.commit()
# Ilova standart pog'onalarni o'zi yozadi — testda faqat o'zimizniki
db.query(models.KpiNewClientRule).delete()
db.query(models.KpiCollectionRule).delete()
db.commit()
db.add(models.KpiNewClientRule(min_clients=5, bonus=300_000))
db.add(models.KpiNewClientRule(min_clients=10, bonus=600_000))
db.add(models.KpiCollectionRule(min_students=1, min_percent=80,
                                bonus=1_000_000))
db.add(models.KpiCollectionRule(min_students=1, min_percent=90,
                                bonus=2_000_000))
db.commit()


def admin(login, name, br):
    u = models.User(username=login, password_hash=hash_password("jonyjony"),
                    role=roles.SALES_MANAGER, full_name=name, branch_id=br,
                    is_active=1, fix_salary=1_500_000)
    db.add(u); db.commit()
    return u


sarvar = admin("sarvar", "Sarvar Ibragimov", ba.id)
top = admin("top", "Eng Zo'r Admin", bb.id)
db.add(models.User(username="asos", password_hash=hash_password("jonyjony"),
                   role=roles.FOUNDER, full_name="Asoschi", is_active=1))
db.commit()


def student(g, nom, old=True, pays=True, by="Kimdir"):
    s = models.Student(full_name=nom, group_id=g.id, branch_id=g.branch_id,
                       status="active", enrolled_date=date(YIL, 1, 1))
    db.add(s); db.commit()
    if old:
        db.add(models.Payment(student_id=s.id, amount=480_000,
                              kind="payment", created_by="Kimdir",
                              created_at=datetime(YIL, OY - 1, 10)))
        db.add(models.Payment(student_id=s.id, amount=-480_000,
                              kind="charge", created_at=datetime(YIL, OY, 1)))
    if pays:
        db.add(models.Payment(student_id=s.id, amount=480_000,
                              kind="payment", created_by=by,
                              created_at=datetime(YIL, OY, 12)))
    db.commit()


# Zafar: 10 eski o'quvchi, 7 tasi to'ladi -> 70%; Sarvar 3 yangi mijoz
for i in range(10):
    student(ga, f"A{i}", pays=i < 7)
for i in range(3):
    student(ga, f"NA{i}", old=False, by="Sarvar Ibragimov")
# Bekobod: hamma to'ladi -> 100%; 10 yangi mijoz
for i in range(4):
    student(gb, f"B{i}")
for i in range(10):
    student(gb, f"NB{i}", old=False, by="Eng Zo'r Admin")


def tok(u):
    return {"Authorization": "Bearer " + c.post("/api/auth/login", json={
        "username": u, "password": "jonyjony"}).json()["access_token"]}


r = c.get(f"/api/kpi/admins?year={YIL}&month={OY}", headers=tok("asos"))
rows = {x["full_name"]: x for x in r.json()["rows"]}
s = rows["Sarvar Ibragimov"]

print("=== 1. Yig'ish: keyingi pog'ona ===")
ck("hozir 70%", s["collection_percent"], 70.0)
ck("keyingisi 80% / 1 mln", (s["next_collection_percent"],
                             s["next_collection_bonus"]), (80, 1_000_000))
ck("yana 480 000 yig'ish kerak", s["collection_gap"], 480_000)

print("\n=== 2. Yangi mijoz: keyingi pog'ona ===")
ck("3 ta, yana 2 ta, bonusi 300k", (s["new_clients"], s["new_clients_gap"],
                                    s["next_new_clients"],
                                    s["next_new_client_bonus"]),
   (3, 2, 5, 300_000))
ck("hozirgi oylik — faqat fiks", s["total"], 1_500_000)

print("\n=== 3. Eng yuqorisida ===")
t = rows["Eng Zo'r Admin"]
ck("yig'ishda keyingisi yo'q", (t["collection_percent"],
                               t["next_collection_percent"],
                               t["collection_gap"]), (100.0, None, None))
ck("yangi mijozda keyingisi yo'q", (t["new_clients"], t["next_new_clients"]),
   (10, None))
ck("oylik = fiks + 2 mln + 600k", t["total"], 4_100_000)

print("\n=== 4. Admin faqat o'zini ko'radi ===")
mine = c.get(f"/api/kpi/admins?year={YIL}&month={OY}",
             headers=tok("sarvar")).json()["rows"]
ck("bitta qator — o'zi", [x["full_name"] for x in mine],
   ["Sarvar Ibragimov"])

print()
if fails:
    print(f"{len(fails)} ta XATO: {fails}")
    sys.exit(1)
print("HAMMASI OK")
