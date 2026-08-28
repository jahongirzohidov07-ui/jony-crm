# -*- coding: utf-8 -*-
"""KONTENT-PLAN: sana bo'yicha ketma-ketlik + import qaysi oyga (2026-08-28).

Jahongir: "qara men excel fayl qilib yukladim SENTABRnikini lekin
menda ko'rinmayabdi. shu OY TANLASH EMAS, eng oldingilari bo'yicha
SANA bo'yicha eng yaqinlari bo'yicha KETMA-KETLIKDA tursin"

IKKI XATO TEKSHIRILADI:
  1) IMPORT OYNI EKRANDAN OLARDI. Avgustda turib sentabr faylini
     yuklasa — hamma qator AVGUSTGA yozilardi va sentabr bo'sh
     qolardi. Aynan shu bo'lgan.
  2) RO'YXAT FAQAT BITTA OYNI KO'RSATARDI. Boshqa oyga tushib
     ketgan qatorni topib bo'lmasdi.
"""
import os
import sys

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_plan_order/db.sqlite"
os.makedirs("/tmp/verify_plan_order", exist_ok=True)
if os.path.exists("/tmp/verify_plan_order/db.sqlite"):
    os.remove("/tmp/verify_plan_order/db.sqlite")
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


b = models.Branch(name="Bekobod 1")
db.add(b); db.commit()
common.reset_partner_cache()
u = models.User(username="smm1", password_hash=hash_password("jonyjony"),
                role=roles.SMM_MANAGER, full_name="Marhabo",
                branch_id=b.id, is_active=1)
db.add(u); db.commit()
H = {"Authorization": "Bearer " + c.post(
    "/api/auth/login",
    json={"username": "smm1", "password": "jonyjony"}
).json()["access_token"]}

BUGUN = roles.local_today()


# =====================================================================
print("=== 1. IMPORT: OY FAYLDAN OLINADI (ekrandan emas) ===")
# =====================================================================
# Sentabr rejasi TO'LIQ sana bilan. Nishon oy ataylab AVGUST
# ko'rsatilyapti — aynan Jahongirning holati.
sent = [
    {"Sana": "2026-09-01", "Vaqt": "10:00", "Platforma": "Instagram",
     "Mavzu": "Sentabr 1-post", "Format": "Reels"},
    {"Sana": "2026-09-14", "Vaqt": "18:00", "Platforma": "Telegram",
     "Mavzu": "Sentabr 14-post", "Format": "Post"},
]
r = c.post("/api/smm/plan/import", headers=H, json={
    "year": 2026, "month": 8, "rows": sent, "dry_run": False}).json()
ck("2 ta qator qo'shildi", r["added"], 2)
rows = (db.query(models.Content)
        .filter(models.Content.title.like("Sentabr%"))
        .order_by(models.Content.planned_date).all())
ck("1-post SENTABRga tushdi (avgustga emas)",
   [x.planned_date.isoformat() for x in rows],
   ["2026-09-01", "2026-09-14"])

# Faqat KUN yozilgan bo'lsa — nishon oy qo'llanadi (eski xatti-harakat)
r2 = c.post("/api/smm/plan/import", headers=H, json={
    "year": 2026, "month": 10, "rows": [
        {"Sana": "5", "Mavzu": "Faqat kun", "Platforma": "Telegram"}],
    "dry_run": False}).json()
ck("faqat kun bo'lsa nishon oy ishlatiladi", r2["added"], 1)
fk = db.query(models.Content).filter(
    models.Content.title == "Faqat kun").first()
ck("  -> 2026-10-05", fk.planned_date.isoformat(), "2026-10-05")

# Turli formatlar
for txt, want in (("14.09.2026", "2026-09-14"),
                  ("2026-09-20T00:00:00", "2026-09-20")):
    c.post("/api/smm/plan/import", headers=H, json={
        "year": 2026, "month": 1, "rows": [
            {"Sana": txt, "Mavzu": f"Format {txt}"}], "dry_run": False})
    got = db.query(models.Content).filter(
        models.Content.title == f"Format {txt}").first()
    ck(f"'{txt}' o'qildi", got.planned_date.isoformat() if got else None, want)

# Dubl: xuddi shu fayl ikkinchi marta yuklansa qo'shilmaydi
r3 = c.post("/api/smm/plan/import", headers=H, json={
    "year": 2026, "month": 8, "rows": sent, "dry_run": False}).json()
ck("ikkinchi marta yuklansa dubl chiqmaydi", r3["added"], 0)
ck("  hammasi 'allaqachon bor' deb belgilandi", r3["skipped"], 2)


# =====================================================================
print("\n=== 2. RO'YXAT: SANA BO'YICHA, OY FILTRI YO'Q ===")
# =====================================================================
# Uch xil oyga post qo'shamiz: kecha, bugun, ertaga, o'tgan oy
for nm, dd in (("Kecha", BUGUN - timedelta(days=1)),
               ("Bugun", BUGUN),
               ("Ertaga", BUGUN + timedelta(days=1)),
               ("O'tgan oy", BUGUN - timedelta(days=40))):
    db.add(models.Content(title=nm, planned_date=dd, branch_id=b.id,
                          platform="Telegram", status="idea"))
db.commit()

r = c.get("/api/smm/plan", headers=H).json()
titles = [x["title"] for x in r["rows"]]
ck("sentabr postlari ham RO'YXATDA", "Sentabr 1-post" in titles, True)
ck("o'tgan oydagisi ham ro'yxatda", "O'tgan oy" in titles, True)
ck("bugungi sana javobda bor", r["today"], BUGUN.isoformat())

# Tartib: bugun va keyingi kunlar OLDIN (eng yaqini birinchi)
kel = [x for x in r["rows"] if x["date"] >= BUGUN.isoformat()]
otgan = [x for x in r["rows"] if x["date"] < BUGUN.isoformat()]
ck("kelayotganlar ro'yxat BOSHIDA",
   [x["title"] for x in r["rows"][:len(kel)]] == [x["title"] for x in kel],
   True)
ck("  eng yaqini birinchi — 'Bugun'", kel[0]["title"], "Bugun")
ck("  keyin 'Ertaga'", kel[1]["title"], "Ertaga")
ck("kelayotganlar o'sish tartibida",
   [x["date"] for x in kel] == sorted(x["date"] for x in kel), True)
ck("o'tganlar KAMAYISH tartibida (eng yaqini birinchi)",
   [x["date"] for x in otgan] == sorted((x["date"] for x in otgan),
                                        reverse=True), True)
ck("  o'tganlarning birinchisi 'Kecha'", otgan[0]["title"], "Kecha")


# =====================================================================
print("\n=== 3. OY TANLAGICHI ISHLAYDI (kerak bo'lganda) ===")
# =====================================================================
ck("qaysi oylarda post borligi ko'rsatiladi",
   len(r["months"]) >= 2, True)
ck("  har oyda soni bor",
   all(m["count"] > 0 for m in r["months"]), True)
ck("  yangi oy birinchi (teskari tartib)",
   r["months"][0]["year"] * 100 + r["months"][0]["month"]
   >= r["months"][-1]["year"] * 100 + r["months"][-1]["month"], True)

r9 = c.get("/api/smm/plan?scope=month&year=2026&month=9", headers=H).json()
t9 = [x["title"] for x in r9["rows"]]
ck("sentabr tanlansa faqat sentabr", all(x["date"][:7] == "2026-09"
                                         for x in r9["rows"]), True)
ck("  sentabrda 4 ta post", len(t9), 4)
ck("  oy nomi to'g'ri", r9["month_label"].lower(), "sentabr")


# =====================================================================
print("\n=== 4. HECH NARSA YO'QOLMADI ===")
# =====================================================================
jami = db.query(models.Content).count()
ck("bazadagi hamma post ro'yxatda",
   len(c.get("/api/smm/plan", headers=H).json()["rows"]), jami)
ck("  soni", jami, 9)


# =====================================================================
print("\n=== 5. FILIALSIZ KONTENT — JAHONGIRNING HOLATI ===")
# =====================================================================
# "baribir ko'rinmayabdi excel jadval yuklasam ham" (2026-08-28).
#
# Sabab: asoschining o'zida filial yo'q, shuning uchun Excel'dan
# yuklangan qatorlar FILIALSIZ saqlanardi. Tepadagi tanlagichda esa
# "Bekobod 1" turgan edi va filialsiz qatorlar filtrdan o'tmasdi.
# Ekran bo'm-bo'sh, ma'lumot esa joyida.
b2 = models.Branch(name="Zafar")
db.add(b2); db.commit()
common.reset_partner_cache()

asos = models.User(username="asoschi_plan",
                   password_hash=hash_password("jonyjony"),
                   role=roles.FOUNDER, full_name="Asoschi",
                   branch_id=None, is_active=1)
db.add(asos); db.commit()
HA = {"Authorization": "Bearer " + c.post(
    "/api/auth/login",
    json={"username": "asoschi_plan", "password": "jonyjony"}
).json()["access_token"]}

# Asoschi filial tanlamasdan yuklaydi -> qator FILIALSIZ qoladi
c.post("/api/smm/plan/import", headers=HA, json={
    "year": 2026, "month": 11, "rows": [
        {"Sana": "2026-11-03", "Mavzu": "Filialsiz post"}],
    "dry_run": False})
fs = db.query(models.Content).filter(
    models.Content.title == "Filialsiz post").first()
ck("filialsiz post yaratildi", fs.branch_id, None)

ck("BARCHA FILIALLARda ko'rinadi",
   "Filialsiz post" in [x["title"] for x in
                        c.get("/api/smm/plan", headers=HA).json()["rows"]],
   True)
ck("BEKOBOD tanlansa ham ko'rinadi",
   "Filialsiz post" in [x["title"] for x in c.get(
       "/api/smm/plan?branch_id=%d" % b.id, headers=HA).json()["rows"]],
   True)
ck("ZAFAR tanlansa ham ko'rinadi",
   "Filialsiz post" in [x["title"] for x in c.get(
       "/api/smm/plan?branch_id=%d" % b2.id, headers=HA).json()["rows"]],
   True)
ck("filialga bog'langan SMM ham ko'radi",
   "Filialsiz post" in [x["title"] for x in
                        c.get("/api/smm/plan", headers=H).json()["rows"]],
   True)

# Filial tanlab yuklasa — o'sha filialga yoziladi
c.post("/api/smm/plan/import", headers=HA, json={
    "year": 2026, "month": 11, "branch_id": b2.id, "rows": [
        {"Sana": "2026-11-04", "Mavzu": "Zafar posti"}],
    "dry_run": False})
zp = db.query(models.Content).filter(
    models.Content.title == "Zafar posti").first()
ck("filial berilsa — o'shanga yoziladi", zp.branch_id, b2.id)
ck("  Bekobodda KO'RINMAYDI",
   "Zafar posti" in [x["title"] for x in c.get(
       "/api/smm/plan?branch_id=%d" % b.id, headers=HA).json()["rows"]],
   False)
ck("  Zafarda ko'rinadi",
   "Zafar posti" in [x["title"] for x in c.get(
       "/api/smm/plan?branch_id=%d" % b2.id, headers=HA).json()["rows"]],
   True)

# PUL ma'lumotida filialsizlik OCHILIB KETMASIN — chegara saqlansin
sf = models.Student(full_name="Filialsiz Talaba", branch_id=None,
                    status="active")
db.add(sf); db.commit()
st_rows = c.get("/api/students?branch_id=%d" % b.id, headers=HA).json()
names = [x["full_name"] for x in (st_rows if isinstance(st_rows, list)
                                  else st_rows.get("rows", []))]
ck("filialsiz O'QUVCHI esa oshkor bo'lmadi (pul chegarasi joyida)",
   "Filialsiz Talaba" in names, False)


print("\n" + "=" * 60)
if fails:
    print("YIQILGAN TEKSHIRUVLAR:", len(fails))
    for f in fails:
        print("  -", f)
else:
    print("HAMMASI O'TDI")
sys.exit(1 if fails else 0)
