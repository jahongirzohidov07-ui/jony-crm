"""SO'Z BILISH — CRM sertifikatlari belgisi va Telegram importi (2026-10-17).

Jahongir: CRM'da xodim qo'shgan IELTS/CEFR sertifikati "Ha, chiqsin";
Telegram kanalidagi natijalar "Darhol tasdiqlangan". Tekshiriladi:
  * CRM IELTS/CEFR sertifikati tasdiqlangan belgi bo'ladi, ichki turi
    yo'q; tasdiqlangan yuklamadan yaratilgani ikki marta chiqmaydi;
  * Telegram importi ismni faqat BITTA aniq o'quvchiga bog'laydi (kirill,
    x/h, otasining ismi farqi hisobga olinmaydi), ikkita o'quvchi yoki
    hech kim mos kelsa — o'tkaziladi; bitta so'zli ism va boshqa imtihon
    import qilinmaydi; takror post qayta yozilmaydi;
  * hisobotda ism yo'q (faqat sonlar va post raqamlari); bir marta.

Ishga tushirish: PYTHONIOENCODING=utf-8 python test_wordbank_tg.py
"""
import json
import os
import sys
from datetime import date

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_wordbank_tg/db.sqlite"
os.makedirs("/tmp/verify_wordbank_tg", exist_ok=True)
if os.path.exists("/tmp/verify_wordbank_tg/db.sqlite"):
    os.remove("/tmp/verify_wordbank_tg/db.sqlite")
os.environ["WORDBANK_WORDS_FILE"] = "/tmp/verify_wordbank_tg/yoq.json"
os.environ["WORDBANK_TG_FILE"] = "/tmp/verify_wordbank_tg/yoq_tg.json"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient  # noqa: E402
import main, models  # noqa: E402,F401
import entry  # noqa: E402,F401 - jonli yo'llar va yamoqlar
import wordbank as WB  # noqa: E402
import wordbank_certs as WCERT  # noqa: E402
from database import SessionLocal  # noqa: E402

client = TestClient(main.app)
fails = []


def ck(name, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + f"{name}: {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


db = SessionLocal()
br = models.Branch(name="TG filial")
db.add(br)
db.commit()
SID = {}
for i, nm in enumerate(["Sobirov Abdurahmon Akmal o'g'li", "Азамова Севинч",
                        "Karimova Ziyoda", "Karimova Ziyoda Anvarovna",
                        "Toshmatov Ali", "Rustamova Laylo"]):
    s = models.Student(full_name=nm, branch_id=br.id, status="active",
                       enrolled_date=date(2026, 9, 1),
                       public_id=f"STU-TG-{i}",
                       parent_token=f"tok-tg-{i}-" + "z" * 12)
    db.add(s)
    db.commit()
    SID[nm] = s.id
SOB, AZA = SID["Sobirov Abdurahmon Akmal o'g'li"], SID["Азамова Севинч"]
TOSH, LAY = SID["Toshmatov Ali"], SID["Rustamova Laylo"]

print("=== 1. CRM SERTIFIKATI BELGI BO'LADI ===")
db.add(models.Certificate(student_id=LAY, kind="ielts", level="7.5",
                          score=7.5, date=date(2026, 5, 1)))
db.add(models.Certificate(student_id=LAY, kind="internal", level="B1",
                          date=date(2026, 6, 1)))
db.commit()
b = WCERT.confirmed_badges(db, [LAY]).get(LAY, [])
ck("CRM IELTS — belgi, ichki tur — yo'q", [x["label"] for x in b],
   ["IELTS 7.5"])
ck("CRM belgisi id'si manfiy", b[0]["id"] < 0, True)
# Tasdiqlangan yuklama o'z Certificate'ini yaratadi — bitta belgi qolsin
c2 = models.Certificate(student_id=LAY, kind="ielts", level="8.0", score=8.0,
                        date=date(2026, 9, 1))
db.add(c2)
db.flush()
db.add(models.WordbankCertUpload(
    student_id=LAY, exam_type="ielts", result_label="IELTS 8.0", score=8.0,
    test_date=date(2026, 9, 1), status="confirmed", certificate_id=c2.id))
db.commit()
ck("yuklama + uning Certificate'i — bitta belgi, eng yangisi birinchi",
   [x["label"] for x in WCERT.confirmed_badges(db, [LAY])[LAY]],
   ["IELTS 8.0", "IELTS 7.5"])
ck("latest_badges ham CRM'ni ko'radi",
   WCERT.latest_badges(db, [LAY]), {LAY: "IELTS 8.0"})

print("\n=== 2. TELEGRAM IMPORTI ===")
P = "/tmp/verify_wordbank_tg/telegram_results.json"
ROWS = [
    {"post": 101, "date": "2026-10-03", "name": "Sobirov Abduraxmon",
     "exam": "multilevel", "level": "B2", "score": 61},
    {"post": 102, "date": "2026-10-03", "name": "Azamova Sevinch",
     "exam": "multilevel", "level": "b2", "score": 51},
    {"post": 103, "date": "2026-10-04", "name": "Ziyoda Karimova",
     "exam": "ielts", "level": "", "score": 6.5},
    {"post": 104, "date": "2026-10-04", "name": "Nobody Unknown",
     "exam": "ielts", "level": "", "score": 7.0},
    {"post": 105, "date": "2026-10-04", "name": "Diyorbek",
     "exam": "ielts", "level": "", "score": 5.5},
    {"post": 106, "date": "2026-10-04", "name": "Toshmatov Ali",
     "exam": "other", "level": "", "score": 1400},
    {"post": 107, "date": "2026-10-05", "name": "Toshmatov Ali",
     "exam": "ielts", "level": "", "score": 7},
    {"post": 108, "date": "2026-10-06", "name": "Ali Toshmatov",
     "exam": "ielts", "level": "", "score": 7.0},
]
json.dump({"results": ROWS}, open(P, "w", encoding="utf-8"))
n0 = db.query(models.Certificate).count()
rep = WCERT.seed_telegram(db, P)
ck("hisobot sonlari",
   (rep["created"], rep["existing"], rep["ambiguous"], rep["unmatched"],
    sorted(rep["skipped"])),
   (3, 1, [103], [104], [105, 106]))
ck("hisobotda ism yo'q",
   any(n in json.dumps(rep) for n in ("Karimova", "Nobody", "Diyorbek")),
   False)
ck("3 ta yangi Certificate", db.query(models.Certificate).count(), n0 + 3)
cs = db.query(models.Certificate).filter_by(student_id=SOB).all()
ck("Sobirov (x/h, otasining ismi): Multilevel B2, sana, izoh, kim",
   [(c.kind, c.level, c.score, c.date, c.note, c.created_by) for c in cs],
   [("cefr", "B2", 61.0, date(2026, 10, 3),
     "Telegram: https://t.me/JonyAcademy/101 · Multilevel",
     "Telegram (avtomat)")])
ck("Sobirov belgisi",
   [x["label"] for x in WCERT.confirmed_badges(db, [SOB])[SOB]],
   ["Multilevel B2 (61)"])
ck("Azamova (kirill CRM) — bog'landi",
   WCERT.latest_badges(db, [AZA]), {AZA: "Multilevel B2 (51)"})
ck("Toshmatov — bitta IELTS 7.0 (takror post qayta yozilmadi)",
   [(c.kind, c.level) for c in
    db.query(models.Certificate).filter_by(student_id=TOSH)],
   [("ielts", "7.0")])
ck("ikkita Karimova Ziyoda — hech biriga yozilmadi",
   db.query(models.Certificate).filter(models.Certificate.student_id.in_(
       [SID["Karimova Ziyoda"], SID["Karimova Ziyoda Anvarovna"]])).count(),
   0)
ck("audit yozuvi (Telegram)",
   db.query(models.AuditLog).filter(
       models.AuditLog.note.like("Telegram kanalidan avtomat%")).count(), 3)
ck("hisobot saqlandi", WCERT.tg_report(db)["created"], 3)

print("\n=== 3. BIR MARTALIK, FAYL O'ZGARSA — TAKRORSIZ ===")
ck("ikkinchi yurish — hech narsa", WCERT.seed_telegram(db, P), None)
json.dump({"results": ROWS + [{"post": 109, "date": "2026-10-07",
                               "name": "Rustamova Laylo", "exam": "ielts",
                               "level": "", "score": 7.5}]},
          open(P, "w", encoding="utf-8"))
rep2 = WCERT.seed_telegram(db, P)
ck("yangi fayl: yangisi yo'q, bor sertifikatlar (Laylo CRM 7.5 ham) takrorlanmadi",
   (rep2["created"], rep2["existing"]), (0, 5))
ck("Certificate soni o'zgarmadi", db.query(models.Certificate).count(),
   n0 + 3)

print("\n=== 4. HOLAT YO'LI — FAQAT SONLAR ===")
WB._STATUS_DONE = False
d = client.get("/api/wordbank/status").json()
ck("status: tg_certs hisoboti (sonlar)",
   (d["tg_certs"]["created"], d["tg_certs"]["existing"]), (0, 5))
ck("status javobida ism yo'q",
   any(n in json.dumps(d) for n in ("Sobirov", "Karimova", "Toshmatov")),
   False)
db.close()

print("\n" + ("BARCHASI OK" if not fails else f"XATOLAR: {len(fails)}"))
for f_ in fails:
    print("  -", f_)
sys.exit(1 if fails else 0)
