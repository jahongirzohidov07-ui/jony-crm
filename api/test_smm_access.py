# -*- coding: utf-8 -*-
"""Marketolog uchun hisobot, analitika va obunachilar (2026-08-27).

Jahongir: "Keyin SMMda ijtimoiy tarmoqlardagi obunachilar soni ham
dashboardda korinib tursin. Smm mutaxasisi uchun hisobotlardan va
analitikadan qismida unga kerakli foydali boladiganlari
korsatilsin." Va: "reja va fakt ham filialga qarab o'zgarishi
kerak, har bir filial rejasi va barchasini korsatish kerak."

QOIDA: marketologga MARKETING ma'lumoti ochiladi, PUL ma'lumoti
emas. Foyda-zarar, oyliklar va umumiy BI panel unga yopiq qoladi —
test buni ham tekshiradi.
"""
import os
import sys

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_smm/db.sqlite"
os.makedirs("/tmp/verify_smm", exist_ok=True)
if os.path.exists("/tmp/verify_smm/db.sqlite"):
    os.remove("/tmp/verify_smm/db.sqlite")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import date, timedelta                # noqa: E402
from fastapi.testclient import TestClient           # noqa: E402
import main, models, roles                          # noqa: E402
import entry                                        # noqa: F401,E402
import common                                       # noqa: E402
from database import SessionLocal                   # noqa: E402
from auth import hash_password                      # noqa: E402

c = TestClient(main.app)
db = SessionLocal()
fails = []


def ck(n, got, want):
    ok = got == want
    print(("OK   " if ok else "XATO ") + f"{n}: {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(n)


maktab = models.Branch(name="Maktab")
zafar = models.Branch(name="Zafar")
db.add_all([maktab, zafar])
db.commit()
common.reset_partner_cache()

# Sotuv rejasi: ikkala filialga
for b, amount in ((maktab, 10_000_000), (zafar, 20_000_000)):
    db.add(models.SmmSalesPlan(branch_id=b.id, year=date.today().year,
                               month=date.today().month, amount=amount))
# Obunachilar tarixi
for pl, old, new in (("telegram", 1000, 1250), ("instagram", 500, 640)):
    db.add(models.SocialStat(platform=pl, followers=old, source="manual",
                             date=date.today() - timedelta(days=40)))
    db.add(models.SocialStat(platform=pl, followers=new, source="manual",
                             date=date.today()))
db.commit()

u = models.User(username="marhabo", password_hash=hash_password("jonyjony"),
                role=roles.SMM_MANAGER, full_name="Marhabo",
                branch_id=maktab.id, is_active=1)
db.add(u)
db.commit()
H = {"Authorization": "Bearer " + c.post(
    "/api/auth/login",
    json={"username": "marhabo", "password": "jonyjony"}
).json()["access_token"]}

print("=== OBUNACHILAR DASHBOARDDA ===")
d = c.get("/api/me/dashboard", headers=H).json()
labels = [x["label"] for x in d["cards"]]
ck("Telegram kartasi bor", "Telegram obunachilar" in labels, True)
ck("Instagram kartasi bor", "Instagram obunachilar" in labels, True)
tg = next(x for x in d["cards"] if x["label"] == "Telegram obunachilar")
ck("  soni to'g'ri", tg["value"], 1250)
ck("  30 kunlik o'sish ko'rsatilgan", "+250" in (tg["hint"] or ""), True)

print("\n=== SOTUV REJASI FILIAL BO'YICHA ===")
r = c.get("/api/smm/sales-plan", headers=H).json()
ck("ikkala filial ham chiqdi", len(r["rows"]), 2)
ck("JAMI qatori bor", r["total"] is not None, True)
ck("  jami reja 30 mln", r["total"]["plan"], 30_000_000)
r1 = c.get("/api/smm/sales-plan?branch_id=%d" % zafar.id, headers=H).json()
ck("Zafar tanlansa faqat Zafar", [x["branch"] for x in r1["rows"]], ["Zafar"])
ck("  bitta filialda JAMI yo'q", r1["total"], None)
ck("  Zafar rejasi 20 mln", r1["rows"][0]["plan"], 20_000_000)

print("\n=== REJA VA FAKT TANLAGICHGA BO'YSUNADI ===")
p_all = c.get("/api/plan", headers=H)
ck("Reja sahifasi ochiladi", p_all.status_code, 200)
ck("  filial tanlagichi chiqadi",
   len(p_all.json().get("branches") or []) >= 2, True)
p_z = c.get("/api/plan?branch_id=%d" % zafar.id, headers=H).json()
ck("  tanlangan filial qabul qilindi", p_z["branch_id"], zafar.id)
ck("  endi umumiy emas", p_z["is_total"], False)

print("\n=== MARKETING HISOBOTLARI OCHIQ ===")
for path, nom in (("/api/reports/funnel", "Sotuv voronkasi"),
                  ("/api/analytics/sources", "Manbalar"),
                  ("/api/analytics/acquisition", "Jalb qilish voronkasi"),
                  ("/api/analytics/lifecycle", "Hayot davri"),
                  ("/api/analytics/cac", "Bitta lid narxi"),
                  ("/api/nps/summary", "NPS"),
                  ("/api/reports/marketing-funnel", "Marketing voronkasi")):
    ck(nom, c.get(path, headers=H).status_code, 200)

print("\n=== PUL MA'LUMOTI YOPIQ QOLDI ===")
for path, nom in (("/api/analytics/summary", "Umumiy BI (foyda bor)"),
                  ("/api/reports/pnl?year=2026&month=8", "Foyda-zarar"),
                  ("/api/reports/cashflow", "Pul oqimi"),
                  ("/api/reports/teacher-payroll", "Ustoz oyligi")):
    ck(nom + " yopiq", c.get(path, headers=H).status_code, 403)

print("\n=== ASOSCHIDA HAMMASI ISHLAYDI ===")
f = models.User(username="asoschi", password_hash=hash_password("jonyjony"),
                role=roles.FOUNDER, full_name="Jahongir", is_active=1)
db.add(f)
db.commit()
HF = {"Authorization": "Bearer " + c.post(
    "/api/auth/login",
    json={"username": "asoschi", "password": "jonyjony"}
).json()["access_token"]}
ck("asoschida BI ochiq",
   c.get("/api/analytics/summary", headers=HF).status_code, 200)
# /api/reports/pnl majburiy year parametri talab qiladi
ck("asoschida foyda-zarar ochiq",
   c.get("/api/reports/pnl?year=%d&month=%d"
         % (date.today().year, date.today().month),
         headers=HF).status_code, 200)

print("\n" + ("HAMMASI O'TDI" if not fails else "XATO: " + ", ".join(fails)))
sys.exit(1 if fails else 0)
