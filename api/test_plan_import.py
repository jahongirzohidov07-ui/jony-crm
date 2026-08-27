# -*- coding: utf-8 -*-
"""Kontent-planni Excel'dan import qilish (2026-08-27).

Jahongir: "ha shunday qil" — sentabr rejasini Excel'dan import
qilish so'raldi.

Test HAQIQIY faylning tuzilishi bilan ishlaydi: Jahongir yuborgan
"Jony Academy Kontent-plan Sentabr 2026.xlsx" dagi ustunlar va
so'zlar aynan shu ko'rinishda beriladi.

Tekshiriladi:
  - o'zbekcha so'zlar tizim kalitlariga to'g'ri bog'lanishi
  - "1-sen" kabi sana yozuvi tushunilishi
  - dry_run avval ko'rsatishi, keyin haqiqiy import
  - IKKI MARTA bosilsa kontent IKKILANMASLIGI
  - mas'ul ismi topilmasa ham post qo'shilishi (izohga yozilib)
"""
import os
import sys

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_imp/db.sqlite"
os.makedirs("/tmp/verify_imp", exist_ok=True)
if os.path.exists("/tmp/verify_imp/db.sqlite"):
    os.remove("/tmp/verify_imp/db.sqlite")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient           # noqa: E402
import main, models, roles                          # noqa: E402
import entry                                        # noqa: F401,E402
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


b = models.Branch(name="Zafar")
db.add(b)
db.commit()
u = models.User(username="marhabo", password_hash=hash_password("jonyjony"),
                role=roles.SMM_MANAGER, full_name="Marhabo Mamatqulova",
                branch_id=b.id, is_active=1)
db.add(u)
db.commit()
H = {"Authorization": "Bearer " + c.post(
    "/api/auth/login",
    json={"username": "marhabo", "password": "jonyjony"}
).json()["access_token"]}

# --- Jahongir faylidan olingan haqiqiy qatorlar ------------------
ROWS = [
    {"Sana": "1-sen", "Kun": "Se", "Vaqt": "10:00",
     "Platforma": "IG + TG", "Auditoriya segmenti": "Ota-onalar",
     "Kontent ustuni": "Muhit va jarayon",
     "Voronka bosqichi": "Tanilish", "Maqsad": "Qamrov",
     "Mavzu": "Ikki bayram: Mustaqillik kuni va yangi o'quv yili",
     "Hook (1-jumla)": "Bugun O'zbekiston bayram qiladi.",
     "Asosiy fikr": "Jony — yil boshlanadigan muhit",
     "Dalil": "5 filialdagi birinchi kun lavhalari",
     "Format": "Reels-montaj",
     "CTA": "Yangi yilni biz bilan boshlang — DM",
     "Mas'ul": "Marhabo + Claude (matn)",
     "Syomka sanasi": "1-sen (jonli)", "Holati": "G'oya",
     "Kutilayotgan KPI": "8k ko'rish"},
    {"Sana": "2-sen", "Vaqt": "19:00", "Platforma": "IG + TG",
     "Auditoriya segmenti": "Maktab o'quvchilari",
     "Kontent ustuni": "DAY X (urg'u)",
     "Voronka bosqichi": "Tanilish", "Maqsad": "Qamrov",
     "Mavzu": "Day X yangi mavsum: Umragacha yo'l",
     "Format": "Reels (Jahongir kamerada)",
     "Mas'ul": "Marhabo + Jahongir",
     "Kutilayotgan KPI": "15k ko'rish, 100 ulashish"},
    {"Sana": "3-sen", "Vaqt": "19:00", "Platforma": "IG + TG",
     "Auditoriya segmenti": "IELTS/CEFR topshiruvchilar",
     "Kontent ustuni": "Foydali ta'lim",
     "Voronka bosqichi": "Ishonch", "Maqsad": "Ishonch",
     "Mavzu": "IELTS Listening'dagi 3 ta trap",
     "Format": "Reels (ustoz kamerada)", "Mas'ul": "Marhabo + ustoz",
     "Syomka sanasi": "3-sen (batch №1)"},
    {"Sana": "8-sen", "Vaqt": "19:00", "Platforma": "IG + TG",
     "Kontent ustuni": "Natijalar va hikoyalar",
     "Voronka bosqichi": "Tavsiya", "Maqsad": "Muloqot",
     "Mavzu": "Shirinabonu: IELTS 8.0 — Bekobod rekordi",
     "Format": "Reels-intervyu", "Mas'ul": "Shoxruh/Sarvar"},
    {"Sana": "12-sen", "Vaqt": "20:00", "Platforma": "YouTube",
     "Kontent ustuni": "STUDENT APP (urg'u)",
     "Voronka bosqichi": "Sotuv", "Maqsad": "Sotuv",
     "Mavzu": "Jony Student App to'liq ko'rsatuv",
     "Format": "Video (15 daqiqa)"},
    # Xato qatorlar — import ularni yutib yubormasligi kerak
    {"Sana": "", "Mavzu": "Sanasiz qator"},
    {"Sana": "31-sen", "Mavzu": "Sentabrda 31-kun yo'q"},
]

print("=== KO'RIB CHIQISH (dry run) ===")
r = c.post("/api/smm/plan/import", headers=H, json={
    "year": 2026, "month": 9, "rows": ROWS, "dry_run": True}).json()
ck("qo'shiladiganlar", r["will_add"], 5)
ck("hali hech narsa qo'shilmadi",
   len(c.get("/api/smm/plan?year=2026&month=9",
             headers=H).json()["rows"]), 0)
ck("xato qatorlar aytildi", len(r["bad"]), 2)
ck("  31-sentabr tutildi",
   any("31" in x["why"] for x in r["bad"]), True)

def pv_of(prefix):
    """Sarlavha boshiga qarab topamiz — belgilab kesish mo'rt."""
    return next(x for x in r["preview"] if x["title"].startswith(prefix))
ck("Muhit va jarayon -> yo'nalish",
   pv_of("Ikki bayram")["pillar"], "Muhit va jarayon")
ck("Tanilish -> voronka",
   pv_of("Ikki bayram")["funnel"], "Tanilish")
ck("Reels-montaj -> Reels",
   pv_of("Ikki bayram")["fmt"], "Reels")
ck("Tavsiya bosqichi tanildi",
   pv_of("Shirinabonu")["funnel"], "Tavsiya")
ck("Video (15 daqiqa) -> Uzun video",
   pv_of("Jony Student App")["fmt"], "Uzun video")
ck("Reels-intervyu -> Testimonial",
   pv_of("Shirinabonu")["fmt"], "Testimonial")
ck("mas'ul topildi (Marhabo)",
   pv_of("Ikki bayram")["owner_found"], True)
ck("noma'lum mas'ul belgilandi",
   pv_of("Shirinabonu")["owner_found"], False)

print("\n=== HAQIQIY IMPORT ===")
r = c.post("/api/smm/plan/import", headers=H, json={
    "year": 2026, "month": 9, "rows": ROWS, "dry_run": False}).json()
ck("qo'shildi", r["added"], 5)
plan = c.get("/api/smm/plan?year=2026&month=9", headers=H).json()
ck("jadvalda ko'rinadi", len(plan["rows"]), 5)
row = plan["rows"][0]
ck("  sana to'g'ri", row["date"], "2026-09-01")
ck("  vaqt", row["time"], "10:00")
ck("  platforma", row["platform"], "IG + TG")
ck("  auditoriya", row["audience"], "Ota-onalar")
ck("  hook", bool(row["hook"]), True)
ck("  dalil", bool(row["proof"]), True)
ck("  CTA", bool(row["cta"]), True)
ck("  kutilgan KPI", row["kpi_target"], "8k ko'rish")
ck("  syomka sanasi", row["shoot_date"], "2026-09-01")
ck("  mas'ul biriktirildi", row["owner"], "Marhabo Mamatqulova")

print("\n=== IKKI MARTA BOSILSA IKKILANMAYDI ===")
r = c.post("/api/smm/plan/import", headers=H, json={
    "year": 2026, "month": 9, "rows": ROWS, "dry_run": False}).json()
ck("yangi qo'shilmadi", r["added"], 0)
ck("  o'tkazib yuborildi", r["skipped"], 5)
ck("jadvalda hamon 5 ta",
   len(c.get("/api/smm/plan?year=2026&month=9",
             headers=H).json()["rows"]), 5)

print("\n=== ASL FORMAT SO'ZI SAQLANDI ===")
cc = (db.query(models.Content)
      .filter(models.Content.title.like("Ikki bayram%")).first())
ck("izohda 'Reels-montaj' bor",
   "Reels-montaj" in (cc.note or ""), True)
sh = (db.query(models.Content)
      .filter(models.Content.title.like("Shirinabonu%")).first())
ck("topilmagan mas'ul izohda",
   "Shoxruh" in (sh.note or ""), True)

print("\n" + ("HAMMASI O'TDI" if not fails else "XATO: " + ", ".join(fails)))
sys.exit(1 if fails else 0)
