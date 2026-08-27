# -*- coding: utf-8 -*-
"""Dashboard kartalari filial tanlagichiga bo'ysunishi (2026-08-27).

Jahongir: "Marhabo mamatqulova shu qizimiz dashboardga kriganda 49ta
lid korinyabdi, hamma filiallni tanlasa, zafarni tanlasa ham shu
chiqyabdi unga togri chiqarsin filiallar boyicha ham va marhaboga
test filial, Stech korsatmasin Stech umuman alohida markaz".

IKKI XATO BOR EDI:
  1. /api/me/dashboard filial parametrini UMUMAN qabul qilmasdi.
     Tepadagi tanlagich boshqa sahifalarni o'zgartirardi-yu,
     "Mening ishim" kartalari qotib turardi.
  2. Marketolog kartalarida lidlar HECH QANDAY filial filtrisiz
     sanalardi — raqamga test filialining soxta lidlari va hamkor
     markaz (Stech) lidlari ham qo'shilib ketardi.

Bu test o'sha holat qaytmasligi uchun.
"""
import os
import sys

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_dashb/db.sqlite"
os.makedirs("/tmp/verify_dashb", exist_ok=True)
if os.path.exists("/tmp/verify_dashb/db.sqlite"):
    os.remove("/tmp/verify_dashb/db.sqlite")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime                      # noqa: E402
from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                         # noqa: E402
import entry                                       # noqa: F401,E402
import common                                      # noqa: E402
from database import SessionLocal                  # noqa: E402
from auth import hash_password                     # noqa: E402

c = TestClient(main.app)
db = SessionLocal()
fails = []


def ck(n, got, want):
    ok = got == want
    print(("OK   " if ok else "XATO ") + f"{n}: {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(n)


# --- To'rt filial: ikki haqiqiy, hamkor va test -----------------
maktab = models.Branch(name="Maktab")
zafar = models.Branch(name="Zafar")
stech = models.Branch(name="Stech", is_partner=1,
                      partner_note="Hamkorlikda")
testb = models.Branch(name="Test filial")
db.add_all([maktab, zafar, stech, testb])
db.commit()
common.reset_partner_cache()

# --- Lidlar: 3 + 5 + 7 + 11 = 26 -------------------------------
now = datetime.utcnow()
plan = [(maktab, 3), (zafar, 5), (stech, 7), (testb, 11)]
for b, n in plan:
    for i in range(n):
        db.add(models.Lead(full_name=f"{b.name} lid {i}",
                           phone=f"9989{b.id:02d}{i:05d}",
                           source="instagram", stage="new",
                           branch_id=b.id, created_at=now))
db.commit()

# --- Marketolog: asosiy filiali Maktab -------------------------
u = models.User(username="marhabo", password_hash=hash_password("jonyjony"),
                role=roles.SMM_MANAGER, full_name="Marhabo Mamatqulova",
                branch_id=maktab.id, is_active=1)
db.add(u)
db.commit()
# Ataylab test va hamkor filialga ham BIRIKTIRAMIZ — shunda ham
# ular ko'rinmasligi kerak.
for b in (zafar, stech, testb):
    db.add(models.UserBranch(user_id=u.id, branch_id=b.id))
db.commit()
H = {"Authorization": "Bearer " + c.post(
    "/api/auth/login",
    json={"username": "marhabo", "password": "jonyjony"}
).json()["access_token"]}

print("=== FILIAL RO'YXATI (tanlagich) ===")
rows = c.get("/api/branches", headers=H).json()
names = sorted(b["name"] for b in rows)
ck("Stech va Test ko'rsatilmaydi", names, ["Maktab", "Zafar"])

print("\n=== LIDLAR FILIAL BO'YICHA ===")


def leads_card(bid=None):
    q = "?branch_id=%d" % bid if bid else ""
    d = c.get("/api/me/dashboard" + q, headers=H).json()
    row = next((x for x in d["cards"] if x["label"] == "Shu oy lidlar"), None)
    return (row or {}).get("value"), d.get("branch")


v, lbl = leads_card()
ck("Barcha filiallar: faqat Maktab+Zafar (3+5)", v, 8)
# Raqam ikki filialdan yig'ilgan — sarlavha ham shuni aytishi kerak
ck("  sarlavhada 'Barcha filiallar'", lbl, "Barcha filiallar")

v, lbl = leads_card(zafar.id)
ck("Zafar tanlansa: 5", v, 5)
ck("  sarlavhada Zafar", lbl, "Zafar")

v, _ = leads_card(maktab.id)
ck("Maktab tanlansa: 3", v, 3)

v, _ = leads_card(stech.id)
ck("Stech tanlansa: 0 (hamkor markaz yopiq)", v, 0)

print("\n=== ASOSCHI HAMMASINI KO'RADI ===")
f = models.User(username="asoschi", password_hash=hash_password("jonyjony"),
                role=roles.FOUNDER, full_name="Jahongir", is_active=1)
db.add(f)
db.commit()
HF = {"Authorization": "Bearer " + c.post(
    "/api/auth/login",
    json={"username": "asoschi", "password": "jonyjony"}
).json()["access_token"]}
rows = c.get("/api/branches", headers=HF).json()
ck("asoschida 4 filial ham bor", len(rows), 4)
ck("asoschi Stech'ni ochadi",
   len(common.blocked_branch_ids(db, f)), 0)

print("\n=== STECH XODIMI O'Z FILIALINI KO'RADI ===")
h = models.User(username="husayn", password_hash=hash_password("jonyjony"),
                role=roles.SMM_MANAGER, full_name="Husayn",
                branch_id=stech.id, is_active=1)
db.add(h)
db.commit()
HH = {"Authorization": "Bearer " + c.post(
    "/api/auth/login",
    json={"username": "husayn", "password": "jonyjony"}
).json()["access_token"]}
rows = [b["name"] for b in c.get("/api/branches", headers=HH).json()]
ck("Stech xodimida Stech bor", "Stech" in rows, True)
ck("  lekin Test yo'q", "Test filial" in rows, False)

print("\n=== TEST FILIALI: YIG'INDIDA YO'Q, LEKIN TANLASA OCHILADI ===")
# O'rgatuvchi (guide) global filialni test filialiga o'tkazadi —
# shunda ekran bo'sh qolmasligi kerak.
v, _ = leads_card(testb.id)
ck("test filiali tanlansa ochiladi (o'rgatuvchi uchun)", v, 11)
ck("lekin yig'indiga qo'shilmaydi", leads_card()[0], 8)

print("\n=== ADMIN DASHBOARD KARTALARI HAM ===")
d = c.get("/api/dashboard?branch_id=%d" % zafar.id, headers=HF).json()
ck("dashboard endpointi ishlaydi", "active_students" in d, True)

print("\n" + ("HAMMASI O'TDI" if not fails else "XATO: " + ", ".join(fails)))
sys.exit(1 if fails else 0)
