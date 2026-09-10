"""KUNLIK TUSHUM — ADMIN KESIMI (2026-09-10).

Jahongir: "shu joyini adminni tanlanadigan qilib bering. opam/Mavluda
opa qancha naqt qancha clickdan pul olgani chiqib turadigan qilib
1talab hisoblab chiqishyaptikan hozir".

Tanlash frontendda bo'ladi (src/lib/cashDaySlice.ts) — endpoint kunning
HAMMA to'lovini `rows` da beradi, shuning uchun admin bosilganda yangi
so'rov yubormaymiz (Neon trafigi ortmaydi).

Shu test ikki narsani isbotlaydi:

  A) QOIDA TO'G'RI. Haqiqiy endpoint javobi ustida frontenddagi ayni
     qoida (rows ni `received_by or "—"` bo'yicha filtrlab qayta
     yig'ish) bajariladi va:
       - har adminning naqd/Click/terminal raqamlari qo'lda
         hisoblangani bilan bir xil chiqadi;
       - hamma adminlar kesimi qo'shilsa endpointning JAMI raqamiga
         teng bo'ladi (ya'ni bironta to'lov yo'qolmaydi, ikki marta
         ham sanalmaydi);
       - `created_by` bo'sh to'lov "—" nomi ostida yig'iladi va
         yo'qolib qolmaydi;
       - hech kim tanlanmagan holat = backend raqamlari o'zi.

  B) DASTURGA ULANGAN. cashDaySlice.ts va CashDay.tsx haqiqatda shu
     qoidani ishlatyapti: chiplar tugmaga aylangan, kartalar va
     ro'yxat tanlangan kesimdan (`view`) chiqyapti.

Backend O'ZGARMAGAN — pul raqamlariga tegilmagan.
"""
import os
import re
import sys
import tempfile
from datetime import date, datetime, timedelta

_DB = os.path.join(tempfile.gettempdir(), "cashday_receiver_test.db")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace("\\", "/")
if os.path.exists(_DB):
    os.remove(_DB)
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                          # noqa: E402
import entry  # noqa: F401,E402
from database import SessionLocal                   # noqa: E402
from auth import hash_password                      # noqa: E402

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
    return datetime.combine(d, datetime.min.time()).replace(
        hour=hh, minute=mm) - OFF


# ---------------------------------------------------------------
# FRONTENDDAGI QOIDANING AYNAN O'ZI (src/lib/cashDaySlice.ts)
# ---------------------------------------------------------------
NO_RECEIVER = "—"


def receiver_key(row):
    return row["received_by"] or NO_RECEIVER


def slice_by_receiver(data, who):
    """cashDaySlice.ts -> sliceByReceiver() ning Python ko'chirmasi."""
    if not who:
        return {k: data[k] for k in (
            "total", "count", "by_method", "new_count", "new_sum",
            "old_count", "old_sum", "rows")}

    rows = [r for r in data["rows"] if receiver_key(r) == who]
    sums = {m["method"]: {"amount": 0.0, "count": 0}
            for m in data["by_method"]}
    total = 0.0
    new_count = 0
    new_sum = 0.0
    for r in rows:
        total += r["amount"]
        sums.setdefault(r["method"], {"amount": 0.0, "count": 0})
        sums[r["method"]]["amount"] += r["amount"]
        sums[r["method"]]["count"] += 1
        if r["is_new"]:
            new_count += 1
            new_sum += r["amount"]
    return {
        "total": round(total, 2),
        "count": len(rows),
        "by_method": [{"method": m["method"], "label": m["label"],
                       "amount": round(sums[m["method"]]["amount"], 2),
                       "count": sums[m["method"]]["count"]}
                      for m in data["by_method"]],
        "new_count": new_count,
        "new_sum": round(new_sum, 2),
        "old_count": len(rows) - new_count,
        "old_sum": round(total - new_sum, 2),
        "rows": rows,
    }


# ---------------------------------------------------------------
# MA'LUMOT
# ---------------------------------------------------------------
db = SessionLocal()
b1 = models.Branch(name="Zafar")
db.add(b1)
db.commit()
B1 = b1.id
db.add(models.User(username="asos", password_hash=hash_password("x"),
                   full_name="Asoschi", role="founder"))
db.commit()

S = {}
for nm in ["Umidjonova Dilafruz", "Nazarova Madina", "Amanova Zilola",
           "Yusufjonova Shaxnoza", "Sattorov Otabek", "Eski O'quvchi"]:
    s = models.Student(full_name=nm, branch_id=B1, status="active",
                       enrolled_date=TODAY - timedelta(days=30))
    db.add(s)
    db.commit()
    S[nm] = s.id


def pay(nm, amount, method, at, by, kind="payment"):
    db.add(models.Payment(student_id=S[nm], amount=amount, kind=kind,
                          method=method, created_at=at, created_by=by,
                          period=TODAY.strftime("%Y-%m")))
    db.commit()


SHAXLO = "Zohidova Shaxlo"
MAVLUDA = "Mavluda Kadirova"

# Eski o'quvchining birinchi to'lovi kecha — bugungisi "eski" bo'ladi.
pay("Eski O'quvchi", 100000, "cash", utc_at(TODAY - timedelta(days=1), 10),
    SHAXLO)

# --- Shaxlo opa: 3 naqd + 1 Click + 1 terminal
pay("Umidjonova Dilafruz", 540000, "terminal", utc_at(TODAY, 16, 34), SHAXLO)
pay("Nazarova Madina", 480000, "cash", utc_at(TODAY, 16, 31), SHAXLO)
pay("Amanova Zilola", 432000, "card", utc_at(TODAY, 16, 30), SHAXLO)
pay("Yusufjonova Shaxnoza", 540000, "cash", utc_at(TODAY, 16, 28), SHAXLO)
pay("Eski O'quvchi", 60000, "cash", utc_at(TODAY, 17, 0), SHAXLO)

# --- Mavluda opa: 1 naqd + 1 Click
pay("Sattorov Otabek", 540000, "cash", utc_at(TODAY, 15, 57), MAVLUDA)
pay("Amanova Zilola", 420000, "card", utc_at(TODAY, 15, 40), MAVLUDA)

# --- Kim qabul qilgani yozilmagan to'lov (eski yozuvlarda uchraydi)
pay("Nazarova Madina", 90000, "terminal", utc_at(TODAY, 9, 0), None)

# Hisoblangan (charge) — kassaga kirmaydi, kesimga ham kirmasligi kerak
pay("Umidjonova Dilafruz", -540000, "cash", utc_at(TODAY, 8, 0), SHAXLO,
    kind="charge")
db.close()

H = tok("asos")
d = client.get("/api/reports/cash-day", headers=H).json()

print("=== 0. KUNNING UMUMIY HOLATI (backend, o'zgarmagan) ===")
ck("bugungi to'lovlar soni", d["count"], 8)
ck("jami", d["total"],
   540000 + 480000 + 432000 + 540000 + 60000 + 540000 + 420000 + 90000)
ck("chiplarda 3 nom", sorted(x["name"] for x in d["by_receiver"]),
   sorted([SHAXLO, MAVLUDA, NO_RECEIVER]))

print("\n=== 1. SHAXLO OPA KESIMI (naqd / Click / terminal) ===")
v = slice_by_receiver(d, SHAXLO)
m = {x["method"]: x for x in v["by_method"]}
ck("Shaxlo jami", v["total"], 540000 + 480000 + 432000 + 540000 + 60000)
ck("Shaxlo to'lovlari soni", v["count"], 5)
ck("Shaxlo NAQD", m["cash"]["amount"], 480000 + 540000 + 60000)
ck("Shaxlo naqd soni", m["cash"]["count"], 3)
ck("Shaxlo CLICK", m["card"]["amount"], 432000)
ck("Shaxlo click soni", m["card"]["count"], 1)
ck("Shaxlo TERMINAL", m["terminal"]["amount"], 540000)
ck("Shaxlo terminal soni", m["terminal"]["count"], 1)
# "Yangi" = o'quvchining ENG BIRINCHI to'lovi (backenddagi qoida).
# Shaxlo opaning 5 ta to'lovidan yangisi 2 ta: Umidjonova va
# Yusufjonova — ular bugun birinchi marta to'ladi. Qolgan uchtasi
# eski: Nazarova bugun ertalab 09:00 da allaqachon to'lagan (chipsiz
# yozuv), Amanova 15:40 da Mavluda opaga to'lagan, Eski O'quvchi esa
# kecha to'lagan. Ya'ni bir o'quvchi bir kunda ikki xil adminga
# to'lasa ham hisob chalkashmaydi.
ck("Shaxlo yangi soni", v["new_count"], 2)
ck("Shaxlo eski soni", v["old_count"], 3)
ck("Shaxlo eski summasi", v["old_sum"], 480000 + 432000 + 60000)
ck("ro'yxatda faqat Shaxlo",
   {r["received_by"] for r in v["rows"]}, {SHAXLO})
ck("hisoblangan (charge) kesimga kirmadi",
   any(r["amount"] < 0 for r in v["rows"]), False)

print("\n=== 2. MAVLUDA OPA KESIMI ===")
v2 = slice_by_receiver(d, MAVLUDA)
m2 = {x["method"]: x for x in v2["by_method"]}
ck("Mavluda jami", v2["total"], 540000 + 420000)
ck("Mavluda soni", v2["count"], 2)
ck("Mavluda NAQD", m2["cash"]["amount"], 540000)
ck("Mavluda CLICK", m2["card"]["amount"], 420000)
ck("Mavluda TERMINAL 0", m2["terminal"]["amount"], 0)
ck("Mavluda terminal soni 0", m2["terminal"]["count"], 0)

print("\n=== 3. KIM QABUL QILGANI YOZILMAGAN TO'LOV YO'QOLMAYDI ===")
v3 = slice_by_receiver(d, NO_RECEIVER)
ck('"—" kesimi 1 ta', v3["count"], 1)
ck('"—" summasi', v3["total"], 90000)
ck('chip nomi bilan bir xil',
   [x["name"] for x in d["by_receiver"] if x["amount"] == 90000],
   [NO_RECEIVER])

print("\n=== 4. KESIMLAR YIG'INDISI = KUNNING JAMISI ===")
parts = [slice_by_receiver(d, x["name"]) for x in d["by_receiver"]]
ck("jami teng", round(sum(p["total"] for p in parts), 2), d["total"])
ck("soni teng", sum(p["count"] for p in parts), d["count"])
ck("yangi soni teng", sum(p["new_count"] for p in parts), d["new_count"])
ck("yangi summasi teng",
   round(sum(p["new_sum"] for p in parts), 2), d["new_sum"])
ck("eski soni teng", sum(p["old_count"] for p in parts), d["old_count"])
for meth in ("cash", "card", "terminal"):
    got = round(sum({x["method"]: x for x in p["by_method"]}[meth]["amount"]
                    for p in parts), 2)
    want = {x["method"]: x for x in d["by_method"]}[meth]["amount"]
    ck(f"{meth} yig'indisi teng", got, want)
ids = [r["id"] for p in parts for r in p["rows"]]
ck("har to'lov bir marta sanaldi", len(ids), len(set(ids)))
ck("hamma to'lov qamrab olindi", set(ids), {r["id"] for r in d["rows"]})

print("\n=== 5. HECH KIM TANLANMASA — HOZIRGI KO'RINISH O'ZGARMAYDI ===")
v0 = slice_by_receiver(d, None)
for k in ("total", "count", "new_count", "new_sum", "old_count", "old_sum"):
    ck(f"tanlovsiz {k}", v0[k], d[k])
ck("tanlovsiz usullar", v0["by_method"], d["by_method"])
ck("tanlovsiz qatorlar", [r["id"] for r in v0["rows"]],
   [r["id"] for r in d["rows"]])

print("\n=== 6. DASTURGA ULANGANMI ===")
slice_src = open(os.path.join(ROOT, "src", "lib", "cashDaySlice.ts"),
                 encoding="utf-8").read()
ck("sliceByReceiver eksport qilingan",
   "export function sliceByReceiver" in slice_src, True)
ck('bo\'sh received_by "—" ga tushadi',
   'return row.received_by || NO_RECEIVER' in slice_src, True)
ck("tanlovsiz backend raqamlari qaytadi",
   "if (!who)" in slice_src, True)
ck("filtr received_by bo'yicha",
   "receiverKey(r) === who" in slice_src, True)

tsx = open(os.path.join(ROOT, "src", "components", "CashDay.tsx"),
           encoding="utf-8").read()
ck("CashDay slice'ni import qildi", "sliceByReceiver" in tsx, True)
ck("tanlangan xodim holati bor", "useState<string | null>(null)" in tsx, True)
ck("chip tugmaga aylandi", "setWho(on ? null : r.name)" in tsx, True)
ck('"Hammasi" tugmasi bor', ">\n                  Hammasi\n" in tsx
   or "Hammasi" in tsx, True)
ck("Jami kartasi kesimdan", "formatSom(view.total)" in tsx, True)
ck("usul kartalari kesimdan", "view.by_method" in tsx, True)
ck("yangi/eski kartasi kesimdan", "view.new_count" in tsx, True)
ck("ro'yxat kesimdan", "view.rows.map" in tsx, True)
ck("chiplar kunning to'liq ro'yxatidan (data)",
   "data.by_receiver.map" in tsx, True)
ck("kun almashsa tanlov tushadi",
   len(re.findall(r"setWho\(null\)", tsx)) >= 2, True)

print("\n" + ("BARCHASI OK" if not fails else f"XATOLAR: {fails}"))
sys.exit(1 if fails else 0)
