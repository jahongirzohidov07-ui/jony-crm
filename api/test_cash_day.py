"""BUGUNGI TUSHUM (2026-09-05).

Jahongir: "moliya bo'limida ... bugungi tushumlarni kim toladi qancha
va qanchasi klik yoki terminal shularni ham korsatadigan joy kerak".

Tekshiriladi: usullar kesimida yig'indi va soni to'g'ri; har to'lov
qatorda kim/qancha/usul/kim qabul qildi; kechagi to'lov bugunga
tushmaydi; hisoblangan (charge) yozuvlar kirmaydi; filial chegarasi;
Toshkent kechqurungi to'lov (UTC bo'yicha ertasi) o'z kunida qoladi.
"""
import os, sys
from datetime import date, datetime, timedelta

os.environ["DATABASE_URL"] = "sqlite:////tmp/cashday_test.db"
if os.path.exists("/tmp/cashday_test.db"):
    os.remove("/tmp/cashday_test.db")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
import main, models, roles
import entry  # noqa: F401
from database import SessionLocal
from auth import hash_password

client = TestClient(main.app)
fails = []


def ck(name, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + name + f": {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


def tok(u, p="x"):
    return {"Authorization": "Bearer " + client.post(
        "/api/auth/login", json={"username": u, "password": p}
    ).json()["access_token"]}


TODAY = roles.local_today()
OFF = timedelta(hours=roles.TIMEZONE_OFFSET_HOURS)


def utc_at(d: date, hh: int, mm: int = 0) -> datetime:
    """Toshkent vaqti -> bazadagi UTC."""
    return datetime.combine(d, datetime.min.time()).replace(
        hour=hh, minute=mm) - OFF


db = SessionLocal()
b1 = models.Branch(name="Zafar")
b2 = models.Branch(name="Bekobod 1")
db.add_all([b1, b2])
db.commit()
B1, B2 = b1.id, b2.id
db.add(models.User(username="asos", password_hash=hash_password("x"),
                   full_name="Asoschi", role="founder"))
db.add(models.User(username="admin_zafar", password_hash=hash_password("x"),
                   full_name="Zafar Admin", role="sales_manager",
                   branch_id=B1))
db.commit()

S = {}
for nm, br in [("Abdusaidova Madina", B1), ("Usmonov Shoxruxbek", B1),
               ("Karimov Ali", B1), ("Bekobodlik Bola", B2)]:
    s = models.Student(full_name=nm, branch_id=br, status="active",
                       enrolled_date=TODAY - timedelta(days=30))
    db.add(s)
    db.commit()
    S[nm] = s.id


def pay(nm, amount, method, at, by="Zafar Admin", kind="payment"):
    db.add(models.Payment(student_id=S[nm], amount=amount, kind=kind,
                          method=method, created_at=at, created_by=by,
                          period=TODAY.strftime("%Y-%m")))
    db.commit()


# Bugun (Toshkent vaqti bilan)
pay("Abdusaidova Madina", 480000, "card", utc_at(TODAY, 9, 15))
pay("Usmonov Shoxruxbek", 432000, "card", utc_at(TODAY, 10, 40))
pay("Karimov Ali", 300000, "cash", utc_at(TODAY, 12, 0), by="Asoschi")
pay("Karimov Ali", 200000, "terminal", utc_at(TODAY, 18, 30))
# Kechqurun 23:30 Toshkent — UTC da ertangi kun emas, KECHAGI kunning
# 18:30 i (UTC+5). Oyna surilmasa u kechaga tushib qolardi.
pay("Abdusaidova Madina", 50000, "cash", utc_at(TODAY, 23, 30))
# Kecha — bugunga kirmasin
pay("Karimov Ali", 999000, "cash", utc_at(TODAY - timedelta(days=1), 14, 0))
# Hisoblangan (charge) — kassaga kirmasin
pay("Usmonov Shoxruxbek", -480000, "cash", utc_at(TODAY, 8, 0),
    kind="charge")
# Boshqa filial — Zafar admini ko'rmasin
pay("Bekobodlik Bola", 700000, "terminal", utc_at(TODAY, 11, 0),
    by="Bekobod Admin")
db.close()

H = tok("asos")
A = tok("admin_zafar")

print("=== 1. ASOSCHI — BUTUN TIZIM ===")
d = client.get("/api/reports/cash-day", headers=H).json()
ck("sana bugun", d["date"], TODAY.isoformat())
ck("5 ta bugungi + 1 ta boshqa filial = 6", d["count"], 6)
ck("jami", d["total"], 480000 + 432000 + 300000 + 200000 + 50000 + 700000)
bm = {x["method"]: x for x in d["by_method"]}
ck("Click (card) jami", bm["card"]["amount"], 912000)
ck("Click soni", bm["card"]["count"], 2)
ck("Naqd jami (23:30 dagi ham kirdi)", bm["cash"]["amount"], 350000)
ck("Terminal jami", bm["terminal"]["amount"], 900000)
ck("kechagi 999 000 KIRMADI", any(r["amount"] == 999000 for r in d["rows"]),
   False)
ck("hisoblangan (charge) KIRMADI",
   any(r["amount"] < 0 for r in d["rows"]), False)

print("\n=== 2. QATORLAR: KIM, QANCHA, USUL, KIM QABUL QILDI ===")
r0 = [r for r in d["rows"] if r["student"] == "Abdusaidova Madina"
      and r["amount"] == 480000][0]
ck("ism", r0["student"], "Abdusaidova Madina")
ck("usul nomi", r0["method_label"], "Click")
ck("vaqt Toshkentda", r0["time"], "09:15")
ck("kim qabul qildi", r0["received_by"], "Zafar Admin")
ck("o'quvchi kartasiga havola uchun id", r0["student_id"],
   S["Abdusaidova Madina"])
r_late = [r for r in d["rows"] if r["amount"] == 50000][0]
ck("23:30 dagi to'lov vaqti to'g'ri", r_late["time"], "23:30")
ck("eng yangisi tepada", d["rows"][0]["amount"], 50000)

print("\n=== 3. KIM QABUL QILDI KESIMI ===")
br = {x["name"]: x for x in d["by_receiver"]}
ck("Zafar Admin jami", br["Zafar Admin"]["amount"], 480000 + 432000
   + 200000 + 50000)
ck("Zafar Admin soni", br["Zafar Admin"]["count"], 4)
ck("Asoschi jami", br["Asoschi"]["amount"], 300000)

print("\n=== 4. YANGI / ESKI TO'LOV ===")
# Har o'quvchining BIRINCHI to'lovi "yangi". Karimov: kechagi 999 000
# birinchi -> bugungi ikkitasi eski. Madina: 480 000 birinchi -> yangi,
# 50 000 eski. Usmonov: charge hisobga olinmaydi, 432 000 birinchi
# to'lov -> yangi. Bekobodlik: yangi.
ck("yangi soni", d["new_count"], 3)
ck("eski soni", d["old_count"], 3)

print("\n=== 5. FILIAL ADMINI FAQAT O'Z FILIALINI KO'RADI ===")
d2 = client.get("/api/reports/cash-day", headers=A).json()
ck("Bekobod to'lovi yo'q", any(r["branch"] == "Bekobod 1"
                               for r in d2["rows"]), False)
ck("5 ta qator", d2["count"], 5)
ck("terminal faqat Zafarniki", {x["method"]: x["amount"]
                               for x in d2["by_method"]}["terminal"],
   200000)

print("\n=== 6. BOSHQA KUN TANLANSA ===")
d3 = client.get("/api/reports/cash-day?day="
                + (TODAY - timedelta(days=1)).isoformat(),
                headers=H).json()
ck("kechagi kun: 1 ta", d3["count"], 1)
ck("kechagi summa", d3["total"], 999000)
d4 = client.get("/api/reports/cash-day?day="
                + (TODAY - timedelta(days=10)).isoformat(),
                headers=H).json()
ck("bo'sh kun", d4["count"], 0)
ck("bo'sh kunda usullar 0", sum(x["amount"] for x in d4["by_method"]), 0)
r = client.get("/api/reports/cash-day?day=2026-13-40", headers=H)
ck("noto'g'ri sana 400", r.status_code, 400)

print("\n=== 7. FILIAL FILTRI (asoschi) ===")
d5 = client.get(f"/api/reports/cash-day?branch_id={B2}", headers=H).json()
ck("faqat Bekobod", d5["count"], 1)
ck("summa", d5["total"], 700000)

print("\n" + ("BARCHASI OK" if not fails else f"XATOLAR: {fails}"))
sys.exit(1 if fails else 0)
