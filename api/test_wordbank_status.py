"""LUG'AT BANKI — ochiq holat yo'li /api/wordbank/status (2026-10-17).

Jahongir: "o'zing tekshir va yuklanmagan bo'lsa tugat". Tekshiriladi:
  * kirishsiz ochiladi, faqat sonlar qaytadi (so'zlar, darajalar, bayroq);
  * so'zlar to'liq bo'lmasa har chaqiruv bitta budjetli qadam yuklaydi,
    oxirida bir martalik "hammaga ochish" bayroqni "all" qiladi;
  * tugagach qadam bajarilmaydi (jarayon xotirasida eslanadi);
  * asoschi qo'ygan bayroq bosilmaydi.

Ishga tushirish: PYTHONIOENCODING=utf-8 python test_wordbank_status.py
"""
import json
import os
import sys

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_wordbank_status/db.sqlite"
os.makedirs("/tmp/verify_wordbank_status", exist_ok=True)
if os.path.exists("/tmp/verify_wordbank_status/db.sqlite"):
    os.remove("/tmp/verify_wordbank_status/db.sqlite")
# Startdagi seed haqiqiy faylni yuklamasin — fayl keyin almashtiriladi.
os.environ["WORDBANK_WORDS_FILE"] = "/tmp/verify_wordbank_status/yoq.json"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient  # noqa: E402
import main, models  # noqa: E402,F401
import entry  # noqa: E402,F401 - jonli yo'llar va yamoqlar
import wordbank as WB  # noqa: E402
from database import SessionLocal  # noqa: E402

client = TestClient(main.app)
fails = []


def ck(name, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + f"{name}: {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


def flag_raw():
    dd = SessionLocal()
    try:
        row = dd.query(models.IntegrationSetting).get(WB.FLAG_KEY)
        return row.value if row is not None else None
    finally:
        dd.close()


def set_flag(value):
    dd = SessionLocal()
    row = dd.query(models.IntegrationSetting).get(WB.FLAG_KEY)
    if row is None:
        dd.add(models.IntegrationSetting(key=WB.FLAG_KEY, value=value))
    else:
        row.value = value
    dd.commit()
    dd.close()


# 7 daraja x 1000 so'z = 7000 qator: budjet 5000 bo'lgani uchun ikki qadam.
BANDS = 7
P = "/tmp/verify_wordbank_status/words.json"
with open(P, "w", encoding="utf-8") as f:
    json.dump({"words": [
        {"rank": r, "band": (r - 1) // 1000 + 1, "lemma": f"zzw{r}",
         "pos": "NOUN", "uz_primary": f"so'z{r}",
         "example_en": f"A zzw{r} here.", "example_uz": "(misol)"}
        for r in range(1, BANDS * 1000 + 1)]}, f)
os.environ["WORDBANK_WORDS_FILE"] = P
WB._STATUS_DONE = False

print("=== 1. KIRISHSIZ, BIRINCHI QADAM ===")
ck("bayroq hali yo'q", flag_raw(), None)
r = client.get("/api/wordbank/status")
ck("kirishsiz 200", r.status_code, 200)
d = r.json()
ck("1-qadam: 5000 yozildi, 2000 qoldi",
   (d["step"]["words"]["inserted"], d["step"]["words"]["left"]),
   (5000, 2000))
ck("1-qadam: hali kutilmoqda, ochilmagan",
   (d["words_pending"], d["done"], d["enabled"], d["step"]["enable_all"]),
   (True, False, "off", "pending"))
ck("1-qadam: so'zlar 5000, 5 daraja tayyor",
   (d["words"], d["bands_ready"]), (5000, 5))
ck("javobda so'zning o'zi yo'q", "zzw" in r.text, False)

print("\n=== 2. IKKINCHI QADAM: TUGADI VA HAMMAGA OCHILDI ===")
d = client.get("/api/wordbank/status").json()
ck("2-qadam: 2000 yozildi, tugadi",
   (d["step"]["words"]["inserted"], d["step"]["words"]["finished"]),
   (2000, True))
ck("2-qadam: hammaga ochildi",
   (d["step"]["enable_all"], d["enabled"], d["done"], d["words_pending"]),
   ("enabled", "all", True, False))
ck("2-qadam: 7000 so'z, 7 daraja", (d["words"], d["bands_ready"]),
   (7000, BANDS))
ck("bazada bayroq 'all'", flag_raw(), "all")

print("\n=== 3. TUGAGACH QADAM YO'Q ===")
d = client.get("/api/wordbank/status").json()
ck("3-chaqiruv: qadam bajarilmadi", (d["step"], d["done"]), (None, True))
ck("3-chaqiruv: son o'sha", d["words"], 7000)

print("\n=== 4. ASOSCHI QARORI BOSILMAYDI ===")
set_flag(json.dumps([5]))
WB._STATUS_DONE = False          # yangi instansiya kabi
d = client.get("/api/wordbank/status").json()
ck("asoschi bitta filial qoldirgan — o'zgarmadi",
   (d["enabled"], flag_raw()), ("1 filial", "[5]"))
ck("yangi instansiyada ham yozuv yo'q",
   (d["step"]["words"], d["step"]["enable_all"], d["done"]),
   (None, None, True))
set_flag("")
WB._STATUS_DONE = False
d = client.get("/api/wordbank/status").json()
ck("asoschi o'chirgan ([] / bo'sh) — qayta ochilmaydi",
   (d["enabled"], flag_raw()), ("off", ""))

print("\n" + ("BARCHASI OK" if not fails else f"XATOLAR: {len(fails)}"))
for f_ in fails:
    print("  -", f_)
sys.exit(1 if fails else 0)
