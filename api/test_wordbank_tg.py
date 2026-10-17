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

2026-10-17 (v2) qo'shimcha:
  * ehtiyotkor o'xshashlik: -xon qo'shimchasi, o'/u, a/o, dj/j, iy/i,
    ruscha yozilish mos keladi; aniq moslik o'xshashlikdan ustun; ikki
    o'xshash o'quvchi — ambiguous; qisqa so'z (< 4 / < 5 harf) va bitta
    so'zga ikki marta mos kelish — yo'q;
  * takror qoidasi: bitta postda bir odamning ikki natijasi — ikkalasi
    yaratiladi; v2 qayta yurishi hech narsani takrorlamaydi;
  * xodim yo'llari (/api/wordbank/telegram-results): ustoz, o'quvchi,
    administrator — 403; filial rahbari boshqa filial o'quvchisini
    ko'rmaydi va bog'lay olmaydi (404); bog'lash — Certificate + audit +
    tasdiqlangan belgi, ikkinchisi 409; "bizniki emas" / qaytarish
    qatorni ro'yxatlar orasida ko'chiradi, sonlar to'g'ri; Student.photo
    o'qilmaydi; ochiq /api/wordbank/status da ism yo'q.
Oldingi 1–4 bo'limlar kutilgan qiymatlari O'ZGARMADI (v2 va takror
tuzatishi ularning natijasini o'zgartirmaydi).

2026-10-17 (v2, review) qo'shimcha:
  * o'xshashlik — faqat tor ro'yxat: aka-uka / opa-singil (-ov/-ova,
    Diyor/Diyora), bitta harfi farqli boshqa ismlar (Kamola/Kamila,
    Xasan/Husan) va familiyalar (Aliyev/Valiyev) avtomat MOS EMAS;
    otasining ismi (o'g'li/qizi, -ovna) solishtirilmaydi; egasi misollari
    baribir mos;
  * xodim bog'lagan natijani keyingi seed boshqa o'quvchiga bermaydi;
    bog'langan natijani boshqa o'quvchiga bog'lab bo'lmaydi (409, egasi
    ismi faqat chegarada); o'quvchida natija allaqachon bo'lsa — 409,
    {"existing": true} bilan — sertifikatsiz "bog'langan"; bitta postda
    ikki odam — xodim tanlovi saqlanadi; boshqa filial o'quvchisi ismi
    ko'rinmaydi; juda katta id — 404;
  * ikki nusxa bir vaqtda seed qilsa — takror sertifikat yo'q.

Ishga tushirish: PYTHONIOENCODING=utf-8 python test_wordbank_tg.py
"""
import hashlib
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
from sqlalchemy import event  # noqa: E402
import main, models, roles  # noqa: E402,F401
import entry  # noqa: E402,F401 - jonli yo'llar va yamoqlar
import common  # noqa: E402
import wordbank as WB  # noqa: E402
import wordbank_certs as WCERT  # noqa: E402
from auth import hash_password  # noqa: E402
from database import SessionLocal, engine  # noqa: E402

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

print("\n=== 5. EHTIYOTKOR O'XSHASHLIK (_match, bazasiz) ===")
ck("TG_SEED — v2 (production bir marta qayta yuradi)", WCERT.TG_SEED,
   "wordbank_tg_certs_v2")
IX = WCERT._TgIndex([
    (1, "Azamova Sevinchxon", None),
    (2, "Fayzullayeva Gulnozaxon", None),
    (3, "Sabirov Jasur", None),
    (4, "Yuldashev Axmadiyor", None),
    (5, "Adiljonova Zebo", None),
    (6, "Sotiboldieva Munisxon", None),
    (7, "Karimov Sardor", None),
    (8, "Karimov Sardar", None),
    (9, "Alijon Valiyev", None),
    (10, "Zeba Toshpulatova", None),
    (11, "Abdumannabxonov Jasurbek", None),
    (12, "Отаева Камола", None),
])
for post_name, want in [
        ("Azamova Sevinch", ("match", [1])),            # -xon
        ("Gulnoza Fayzullayeva", ("match", [2])),       # -xon, tartib
        ("Sobirov Jasur", ("match", [3])),              # o/a
        ("Axmadiyor Yo'ldashev", ("match", [4])),       # o'/u
        ("Adildjonova Zebo", ("match", [5])),           # dj/j
        ("Munisxon Sotiboldiyeva", ("match", [6])),     # iy/i
        ("Otayeva Kamola", ("match", [12])),            # ruscha yozilish
        ("Karimov Sardor", ("match", [7])),             # aniq — o'xshashdan ustun
        ("Karimov Sardur", ("match", [7])),             # u/o — faqat Sardor
        ("Karimav Sardor", ("ambiguous", [7, 8])),      # ikki o'xshash odam
        ("Ali Valiyev", ("unmatched", [])),             # "ali" < 4 harf
        ("Zebo Toshpulatova", ("unmatched", [])),       # zebo/zeba < 5 harf
        ("Sevinch Sevinchxon", ("unmatched", [])),      # bitta so'zga ikki marta
        ("Jasur Abdumannab", ("unmatched", [])),        # 5 harf qo'shiladi
        ("Diyorbek", ("unmatched", [])),                # bitta so'z
]:
    ck(f"_match: {post_name}", WCERT._match(IX, post_name), want)
ck("_match_how: aniq / o'xshash usuli",
   (WCERT._match_how(IX, "Karimov Sardor")[2],
    WCERT._match_how(IX, "Azamova Sevinch")[2]), ("exact", "fuzzy"))
ck("yaqin nomzod (taklif, avtomat emas): Abdumannab -> Abdumannabxonov",
   WCERT._suggest(IX, WCERT._name_tokens("Jasur Abdumannab")), [11])
ck("daraja kaliti: '7' / 'IELTS 7' / 7.0 bir xil, 'b2 (61)' = B2",
   (WCERT._lvl_key("ielts", "7", None), WCERT._lvl_key("ielts", "IELTS 7", 7),
    WCERT._lvl_key("ielts", "", 7.0), WCERT._lvl_key("cefr", "b2 (61)", None)),
   ("7.0", "7.0", "7.0", "B2"))

print("\n=== 5b. AKA-UKA, ADASH ISMLAR, OTASINING ISMI — AVTOMAT MOS EMAS ===")
# 2026-10-17 (review): eski "bitta harf farqi" qoidasi bularni bitta odam
# qilib, boshqa odamga darhol tasdiqlangan sertifikat berardi
NEG = [  # (postdagi ism, CRM'dagi BOSHQA odam)
    ("Olimova Nozima", "Olimov Nozim"),
    ("Umida Nashirova", "Nashirov Umid"),
    ("Tojiboyeva Diyora", "Tojiboyev Diyor"),
    ("Mominjanova Ozoda", "Mominjanov Ozod"),
    ("Murtazaxanova Shahzoda", "Murtazaxanov Shahzod"),
    ("Abdullayeva Ziyoda", "Abdullayev Ziyod"),
    ("Ziyoda Karimova", "Karimov Ziyod"),
    ("Abdug'oniyeva Dilnura", "Abdug'oniyev Dilnur"),
    ("Otayeva Kamola", "Otayeva Kamila"),
    ("Tojiboyeva Dinora", "Tojiboyeva Diyora"),
    ("Ikramova Munisa", "Ikramova Munira"),
    ("Fayzullayeva Gulnoza", "Fayzullayeva Gulnora"),
    ("Ashirova Madina", "Ashirova Marina"),
    ("Kimsanboyeva Samira", "Kimsanboyeva Samina"),
    ("Mahmudova Sabina", "Mahmudova Sabrina"),
    ("Abdunazarov Xasan", "Abdunazarov Husan"),
    ("Aliyev Islomjon", "Valiyev Islomjon"),
    ("Nazarova Umidaxon", "Nazirova Umidaxon"),
    ("Abdujalilov Ravshan", "Abdujalolov Ravshan"),
    ("Xasanova Munisa", "Xusanova Munisa"),
    ("Anvarova Ziyoda", "Karimova Ziyoda Anvarovna"),        # otasining ismi
    ("Akmal Sobirov", "Sobirov Abdurahmon Akmal o'g'li"),     # ota
    ("Anvar Ortiqjonova", "Ortiqjonova Go'zal Anvar qizi"),
]
bad = [(a, b) for a, b in NEG
       if WCERT._match(WCERT._TgIndex([(1, b, None)]), a) != ("unmatched", [])]
ck("aka-uka / adash / ota — hech biri avtomat mos emas", bad, [])
ck("lekin xodimga nomzod bo'lib chiqadi (Kamola -> Kamila)",
   WCERT._suggest(WCERT._TgIndex([(1, "Otayeva Kamila", None)]),
                  WCERT._name_tokens("Otayeva Kamola")), [1])
ck("otasining ismi bilan post — nomzod (avtomat emas)",
   WCERT._suggest(WCERT._TgIndex([(1, "Sobirov Abdurahmon Akmal o'g'li",
                                   None)]),
                  WCERT._name_tokens("Akmal Sobirov")), [1])
POS = [  # egasi misollari va boshqa to'g'ri yozilish farqlari
    ("Azamova Sevinch", "Azamova Sevinchxon"),
    ("Pulatova Sarvinoz", "Po'latova Sarvinoz"),
    ("Otayeva Kamola", "Отаева Камола"),
    ("Adildjonova Zebo", "Adiljonova Zebo"),
    ("Axmadiyor Yo'ldashev", "Yuldashev Axmadiyor"),
    ("Gaibova Dilnura", "Gaipova Dilnura"),
    ("Abdug'oniyeva Dilnura", "Abdug'oniyeva Dilnuraxon"),
    ("Rustamova Muslima", "Rustamova Muslima Anvarovna"),
    ("Sobirov Abduraxmon", "Sobirov Abdurahmon Akmal o'g'li"),
    ("Normurotov Arslonbek", "Normurodov Arslon"),
    ("Abdunabiyev Husayn", "Abdunabiev Husayn"),
    ("Qodirova Malika", "Kodirova Malika"),
]
bad = [(a, b) for a, b in POS
       if WCERT._match(WCERT._TgIndex([(1, b, None)]), a) != ("match", [1])]
ck("egasi misollari baribir mos", bad, [])

print("\n=== 6. v2 IMPORT: O'XSHASHLIK, BIR POSTDA IKKI NATIJA ===")
br2 = models.Branch(name="TG ikkinchi filial")
db.add(br2)
db.commit()


def mk_st(nm, branch, tag):
    s = models.Student(full_name=nm, branch_id=branch.id, status="active",
                       enrolled_date=date(2026, 9, 1),
                       public_id=f"STU-TG-{tag}",
                       parent_token=f"tok-tg-{tag}-" + "z" * 12)
    db.add(s)
    db.commit()
    return s.id


PUL = mk_st("Po'latova Sarvinozxon", br, "pul")
OTA = mk_st("Отаева Камола", br, "ota")
ASA = mk_st("Asatov Mahmudjon", br, "asa")
YUL = mk_st("Yuldashev Axmadiyor", br, "yul")
QS1 = mk_st("Qodirov Sardor", br, "qs1")
QS2 = mk_st("Qodirov Sardar", br, "qs2")
P3 = "/tmp/verify_wordbank_tg/telegram_results_v2.json"
ROWS3 = [
    {"post": 301, "date": "2026-10-03", "name": "Pulatova Sarvinoz",
     "exam": "multilevel", "level": "B2", "score": 61},
    {"post": 302, "date": "2026-10-05", "name": "Otayeva Kamola",
     "exam": "ielts", "level": "", "score": 6.5},
    {"post": 303, "date": "2022-06-06", "name": "Asatov Mahmudjon",
     "exam": "ielts", "level": "", "score": 7},
    {"post": 303, "date": "2022-06-06", "name": "Asatov Mahmudjon",
     "exam": "ielts", "level": "", "score": 7.5},
    {"post": 304, "date": "2026-10-05", "name": "Axmadiyor Yo'ldashev",
     "exam": "cefr", "level": "B2", "score": None},
    {"post": 305, "date": "2026-10-05", "name": "Qadirov Sardor",
     "exam": "ielts", "level": "", "score": 6.0},
]
json.dump({"results": ROWS3}, open(P3, "w", encoding="utf-8"))
# production holati: v1 bu faylni allaqachon ko'rgan (belgisi bor)
common._seed_mark(db, "wordbank_tg_certs_v1:" + hashlib.sha256(
    open(P3, "rb").read()).hexdigest()[:12])
n1 = db.query(models.Certificate).count()
rep3 = WCERT.seed_telegram(db, P3)
ck("v1 belgisi bor bo'lsa ham v2 yuradi", rep3 is not None, True)
ck("v2 hisoboti: yaratildi, bor, o'xshashlik bilan, ambiguous, unmatched",
   (rep3["created"], rep3["existing"], rep3["fuzzy"], rep3["ambiguous"],
    rep3["unmatched"]), (5, 0, 3, [305], []))


def certs_of(sid):
    return sorted((c.kind, c.level, c.score, c.note) for c in
                  db.query(models.Certificate).filter_by(student_id=sid))


ck("bitta postda bir odamning ikki natijasi — IKKALASI yaratildi (takror "
   "xatosi tuzatildi)", certs_of(ASA),
   [("ielts", "7.0", 7.0, "Telegram: https://t.me/JonyAcademy/303"),
    ("ielts", "7.5", 7.5, "Telegram: https://t.me/JonyAcademy/303")])
ck("Pulatova Sarvinoz -> Po'latova Sarvinozxon (o'/u, -xon)",
   certs_of(PUL), [("cefr", "B2", 61.0,
                    "Telegram: https://t.me/JonyAcademy/301 · Multilevel")])
ck("Otayeva Kamola -> Отаева Камола (ruscha)",
   [x[:2] for x in certs_of(OTA)], [("ielts", "6.5")])
ck("Axmadiyor Yo'ldashev -> Yuldashev Axmadiyor (o'/u)",
   [x[:2] for x in certs_of(YUL)], [("cefr", "B2")])
ck("ikki o'xshash Qodirov — hech biriga yozilmadi",
   certs_of(QS1) + certs_of(QS2), [])
ck("hisobotda ism yo'q (v2)",
   any(n in json.dumps(rep3) for n in ("Pulatova", "Asatov", "Qodirov")),
   False)
ck("bir xil fayl, bir xil v2 — hech narsa", WCERT.seed_telegram(db, P3),
   None)
_old_seed = WCERT.TG_SEED
WCERT.TG_SEED = "wordbank_tg_certs_v2_qayta"     # yana bir qayta yurish
rep4 = WCERT.seed_telegram(db, P3)
WCERT.TG_SEED = _old_seed
ck("qayta yurish: yangisi yo'q, hammasi 'bor' (takror yaratilmadi)",
   (rep4["created"], rep4["existing"], rep4["ambiguous"]), (0, 5, [305]))
ck("Certificate soni: faqat v2 ning 5 tasi qo'shildi",
   db.query(models.Certificate).count(), n1 + 5)

print("\n=== 7. XODIM YO'LLARI: RUXSAT ===")
GZA = mk_st("O'rtiqjonova Go'zal", br, "gza")
GZB = mk_st("Ortiqjonova Go'zal Anvar qizi", br2, "gzb")


def mk_user(uname, role, branch, name):
    u = models.User(username=uname, full_name=name,
                    password_hash=hash_password("Parol123!"), role=role,
                    branch_id=branch.id if branch else None, is_active=1)
    db.add(u)
    db.commit()
    return u.id


U_BM = mk_user("tgbm", roles.BRANCH_MANAGER, br, "Rahbar Bir")
mk_user("tgbm2", roles.BRANCH_MANAGER, br2, "Rahbar Ikki")
mk_user("tgboss", roles.FOUNDER, br, "Asoschi")
mk_user("tghead", roles.ACADEMIC_HEAD, None, "O'quv Rahbari")
mk_user("tgteach", roles.TEACHER, br, "Ustoz")
mk_user("tgadm", roles.ADMINISTRATOR, br, "Administrator")
_stu = models.Student(full_name="Qorovul Tekshiruvchi", branch_id=br.id,
                      status="active", enrolled_date=date(2026, 9, 1),
                      public_id="STU-TG-stud", parent_token="tok-tg-stud-"
                      + "z" * 12,
                      user_id=mk_user("tgstud", roles.STUDENT, br,
                                      "Qorovul Tekshiruvchi"))
db.add(_stu)
db.commit()


def H(uname):
    r = client.post("/api/auth/login",
                    json={"username": uname, "password": "Parol123!"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


HBM, HBM2, HF, HAH = H("tgbm"), H("tgbm2"), H("tgboss"), H("tghead")
HT, HADM, HS = H("tgteach"), H("tgadm"), H("tgstud")

P5 = "/tmp/verify_wordbank_tg/telegram_results_staff.json"
ROWS5 = [
    {"post": 501, "date": "2026-10-05", "name": "Rustamova Laylo",
     "exam": "ielts", "level": "", "score": 7.5},          # 0: CRM 7.5 bor
    {"post": 101, "date": "2026-10-03", "name": "Sobirov Abduraxmon",
     "exam": "multilevel", "level": "B2", "score": 61},    # 1: import qilingan
    {"post": 502, "date": "2026-10-04", "name": "Ziyoda Karimova",
     "exam": "ielts", "level": "", "score": 6.5},          # 2: ikki Karimova
    {"post": 503, "date": "2026-10-06", "name": "Ortikjanova Go'zalxon",
     "exam": "ielts", "level": "", "score": 6.0},          # 3: faqat yaqin
    {"post": 504, "date": "2026-10-02", "name": "Nobody Unknown",
     "exam": "cefr", "level": "B1", "score": None},        # 4: hech kim
    {"post": 505, "date": "2026-10-01", "name": "Pulatova Sarvinoz",
     "exam": "ielts", "level": "", "score": 7.0},          # 5: bitta, sertifikatsiz
    {"post": 506, "date": "2026-10-01", "name": "Toshmatov Ali",
     "exam": "sat", "level": "", "score": 1400},           # 6: noma'lum imtihon
]
json.dump({"results": ROWS5}, open(P5, "w", encoding="utf-8"))
os.environ["WORDBANK_TG_FILE"] = P5
# "So'z bilish" bayrog'i o'chiq — bu yo'llar baribir ishlaydi
_fl = db.query(models.IntegrationSetting).get("wordbank_branches")
if _fl is None:
    db.add(models.IntegrationSetting(key="wordbank_branches", value="[]"))
else:
    _fl.value = "[]"
db.commit()
TGU = "/api/wordbank/telegram-results"
for who, hh in (("ustoz", HT), ("o'quvchi", HS), ("administrator", HADM)):
    ck(f"{who}: ro'yxat / bog'lash / yashirish — 403",
       (client.get(TGU, headers=hh).status_code,
        client.post(f"{TGU}/3/link", json={"student_id": GZA},
                    headers=hh).status_code,
        client.post(f"{TGU}/4/dismiss", json={}, headers=hh).status_code),
       (403, 403, 403))
ck("kirmagan — 401", client.get(TGU).status_code, 401)
ck("o'quv bo'limi rahbari — 200 (bayroq o'chiq bo'lsa ham)",
   client.get(TGU, headers=HAH).status_code, 200)
ck("noto'g'ri status — 400",
   client.get(TGU + "?status=hammasi", headers=HF).status_code, 400)

print("\n=== 8. XODIM YO'LLARI: RO'YXAT, BOG'LASH, YASHIRISH ===")
SQL = []


def _spy(conn, cursor, statement, params, context, executemany):
    SQL.append(statement)


event.listen(engine, "before_cursor_execute", _spy)
d = client.get(TGU + "?status=all", headers=HF).json()
event.remove(engine, "before_cursor_execute", _spy)
ck("Student.photo o'qilmaydi",
   [s for s in SQL if "FROM students" in s and "photo" in s], [])
ck("sonlar (asoschi)", d["counts"],
   {"unmatched": 3, "ambiguous": 1, "linked": 2, "dismissed": 0})
ck("tartib: eng yangi post birinchi; noma'lum imtihon ro'yxatda yo'q",
   [r["row"] for r in d["rows"]], [3, 0, 2, 1, 4, 5])
R = {r["row"]: r for r in d["rows"]}
ck("bog'langan (CRM'da shu natija bor, havolasiz)",
   (R[0]["status"], R[0]["student_id"], R[0]["student_name"],
    R[0]["candidates"]), ("linked", LAY, "Rustamova Laylo", []))
ck("bog'langan (import havolasi)", (R[1]["status"], R[1]["student_id"]),
   ("linked", SOB))
ck("qator maydonlari", {k: R[1][k] for k in
                        ("post", "date", "name", "exam", "label", "link")},
   {"post": 101, "date": "2026-10-03", "name": "Sobirov Abduraxmon",
    "exam": "multilevel", "label": "Multilevel B2 (61)",
    "link": "https://t.me/JonyAcademy/101"})
ck("ambiguous: ikkala Karimova nomzod, filiali bilan",
   (R[2]["status"], [(c["id"], c["branch"]) for c in R[2]["candidates"]]),
   ("ambiguous", [(SID["Karimova Ziyoda"], "TG filial"),
                  (SID["Karimova Ziyoda Anvarovna"], "TG filial")]))
ck("unmatched: yaqin nomzodlar (ikkala filial, asoschi)",
   (R[3]["status"], R[3]["label"], [c["id"] for c in R[3]["candidates"]]),
   ("unmatched", "IELTS 6.0", [GZA, GZB]))
ck("hech kim — nomzodsiz", (R[4]["status"], R[4]["candidates"]),
   ("unmatched", []))
ck("bitta o'quvchi topildi, lekin sertifikati yo'q — unmatched, u birinchi "
   "nomzod", (R[5]["status"], R[5]["candidates"][0]["id"]),
   ("unmatched", PUL))
ck("standart status = unmatched",
   [r["row"] for r in client.get(TGU, headers=HF).json()["rows"]], [3, 4, 5])
dbm = client.get(TGU + "?status=all", headers=HBM).json()
RB = {r["row"]: r for r in dbm["rows"]}
ck("filial rahbari: nomzodlar faqat o'z filialidan",
   [c["id"] for c in RB[3]["candidates"]], [GZA])
dbm2 = client.get(TGU + "?status=all", headers=HBM2).json()
ck("boshqa filial rahbari: Karimovalar ko'rinmaydi, faqat o'z o'quvchisi",
   ({r["row"]: r for r in dbm2["rows"]}[2]["candidates"],
    [c["id"] for c in {r["row"]: r for r in dbm2["rows"]}[3]["candidates"]]),
   ([], [GZB]))

ck("filial rahbari boshqa filial o'quvchisiga bog'lay olmaydi (404)",
   client.post(f"{TGU}/3/link", json={"student_id": GZB},
               headers=HBM).status_code, 404)
ck("noma'lum qator / noma'lum imtihon qatori / harf — 404",
   [client.post(f"{TGU}/{x}/link", json={"student_id": GZA},
                headers=HF).status_code for x in ("999", "6", "abc")],
   [404, 404, 404])
ck("noma'lum o'quvchi — 404; o'quvchi tanlanmagan — 400",
   (client.post(f"{TGU}/3/link", json={"student_id": 999999},
                headers=HF).status_code,
    client.post(f"{TGU}/3/link", json={}, headers=HF).status_code),
   (404, 400))
ck("hech narsa yaratilmadi (rad etilgan urinishlar)",
   certs_of(GZA) + certs_of(GZB), [])
na = db.query(models.AuditLog).count()
r = client.post(f"{TGU}/3/link", json={"student_id": GZA}, headers=HBM)
ck("filial rahbari o'z o'quvchisiga bog'ladi — 200", r.status_code, 200)
rj = r.json()
ck("javob — yangilangan qator",
   (rj["row"], rj["status"], rj["student_id"], rj["student_name"],
    rj["candidates"]), (3, "linked", GZA, "O'rtiqjonova Go'zal", []))
db.expire_all()
cz = db.query(models.Certificate).filter_by(student_id=GZA).all()
ck("Certificate seed bilan bir xil (created_by — xodim)",
   [(c.kind, c.level, c.score, c.date, c.note, c.created_by) for c in cz],
   [("ielts", "6.0", 6.0, date(2026, 10, 6),
     "Telegram: https://t.me/JonyAcademy/503", "Rahbar Bir")])
al = (db.query(models.AuditLog)
      .filter(models.AuditLog.entity_id == GZA,
              models.AuditLog.field == "certificate").all())
ck("audit: xodim nomidan, bitta",
   [(a.user_id, a.new_value, a.note) for a in al],
   [(U_BM, "IELTS 6.0",
     "Telegram kanalidan qo'lda bog'landi: https://t.me/JonyAcademy/503")])
ck("audit soni +1", db.query(models.AuditLog).count(), na + 1)
ck("tasdiqlangan belgi bo'ldi (confirmed_badges)",
   [b["label"] for b in WCERT.confirmed_badges(db, [GZA]).get(GZA, [])],
   ["IELTS 6.0"])
ck("ikkinchi bog'lash — 409",
   (client.post(f"{TGU}/3/link", json={"student_id": GZA},
                headers=HF).status_code,
    client.post(f"{TGU}/3/link", json={"student_id": GZA},
                headers=HF).json().get("detail")),
   (409, "Bu o'quvchida bu natija allaqachon bor"))
ck("CRM'da shu natija bor o'quvchiga — 409",
   client.post(f"{TGU}/0/link", json={"student_id": LAY},
               headers=HF).status_code, 409)
ck("Certificate takrorlanmadi", len(certs_of(GZA)), 1)
ck("sonlar: linked +1",
   client.get(TGU + "?status=all", headers=HF).json()["counts"],
   {"unmatched": 2, "ambiguous": 1, "linked": 3, "dismissed": 0})

r = client.post(f"{TGU}/4/dismiss", json={}, headers=HF)
ck("bizniki emas — 200, holat dismissed",
   (r.status_code, r.json()["status"]), (200, "dismissed"))
ck("dismissed ro'yxatida bor, unmatched'da yo'q",
   ([x["row"] for x in client.get(TGU + "?status=dismissed",
                                  headers=HF).json()["rows"]],
    [x["row"] for x in client.get(TGU, headers=HF).json()["rows"]]),
   ([4], [5]))
ck("sonlar: dismissed 1",
   client.get(TGU + "?status=all", headers=HF).json()["counts"],
   {"unmatched": 1, "ambiguous": 1, "linked": 3, "dismissed": 1})
db.expire_all()
ck("ro'yxat kaliti \"post:ism\"",
   json.loads(db.query(models.IntegrationSetting)
              .get("wordbank_tg_dismissed").value), ["504:Nobody Unknown"])
ck("yashirish audit'da",
   db.query(models.AuditLog).filter(
       models.AuditLog.field == "wordbank_tg_dismissed").count(), 1)
ck("qayta bosish — o'zgarish yo'q, audit qo'shilmaydi",
   (client.post(f"{TGU}/4/dismiss", json={}, headers=HF).json()["status"],
    db.query(models.AuditLog).filter(
        models.AuditLog.field == "wordbank_tg_dismissed").count()),
   ("dismissed", 1))
r = client.post(f"{TGU}/4/dismiss", json={"undo": True}, headers=HBM)
ck("qaytarish — unmatched", (r.status_code, r.json()["status"]),
   (200, "unmatched"))
ck("sonlar qaytdi",
   client.get(TGU + "?status=all", headers=HF).json()["counts"],
   {"unmatched": 2, "ambiguous": 1, "linked": 3, "dismissed": 0})
ck("bog'langan natijani yashirib bo'lmaydi — 409; undo matn — 400",
   (client.post(f"{TGU}/0/dismiss", json={}, headers=HF).status_code,
    client.post(f"{TGU}/4/dismiss", json={"undo": "ha"},
                headers=HF).status_code), (409, 400))

print("\n=== 8b. BITTA POSTDA IKKI ODAM, BIR XIL NATIJA ===")
P6 = "/tmp/verify_wordbank_tg/telegram_results_two.json"
json.dump({"results": [
    {"post": 601, "date": "2026-10-07", "name": "Qadirov Sardor",
     "exam": "ielts", "level": "", "score": 8.0},
    {"post": 601, "date": "2026-10-07", "name": "Nobody Unknown",
     "exam": "ielts", "level": "", "score": 8.0},
]}, open(P6, "w", encoding="utf-8"))
os.environ["WORDBANK_TG_FILE"] = P6
ck("ambiguous qatorni qo'lda bog'lash — 200",
   client.post(f"{TGU}/0/link", json={"student_id": QS1},
               headers=HF).status_code, 200)
d6 = {r["row"]: r for r in client.get(TGU + "?status=all",
                                      headers=HF).json()["rows"]}
ck("havola kimniki — ism hal qiladi: Qodirov bog'langan, ikkinchi odam yo'q",
   ((d6[0]["status"], d6[0]["student_id"]), d6[1]["status"]),
   (("linked", QS1), "unmatched"))
# Ikkinchi odamni ism topa olmaydigan o'quvchiga bog'lash — xodim tanlovi
# saqlanadi (ilgari 200 qaytib, qator "unmatched" bo'lib qolardi)
r = client.post(f"{TGU}/1/link", json={"student_id": TOSH}, headers=HF)
ck("ikkinchi odam — boshqa o'quvchiga bog'landi, javob 'linked'",
   (r.status_code, r.json()["status"], r.json()["student_id"]),
   (200, "linked", TOSH))
d6 = {r["row"]: r for r in client.get(TGU + "?status=all",
                                      headers=HF).json()["rows"]}
ck("ikkala qator o'z egasida",
   [(d6[i]["status"], d6[i]["student_id"]) for i in (0, 1)],
   [("linked", QS1), ("linked", TOSH)])
with open(P6, "w", encoding="utf-8") as f_:
    f_.write("{buzuq")
rb = client.get(TGU, headers=HF)
ck("buzilgan fayl — tushunarli 500", (rb.status_code, rb.json().get("detail")),
   (500, "Telegram natijalari fayli buzilgan"))
os.environ["WORDBANK_TG_FILE"] = P5

print("\n=== 8c. BOG'LANGANNI QAYTA BOG'LASH, ALLAQACHON BOR, CHEGARA ===")
r = client.post(f"{TGU}/1/link", json={"student_id": TOSH}, headers=HF)
ck("bog'langan natijani boshqa o'quvchiga — 409, egasi ismi (chegarada)",
   (r.status_code, r.json().get("detail")),
   (409, WCERT.TG_TAKEN + ": Sobirov Abdurahmon Akmal o'g'li"))
r = client.post(f"{TGU}/1/link", json={"student_id": GZB}, headers=HBM2)
ck("boshqa filial rahbari — 409, egasining ismi aytilmaydi",
   (r.status_code, r.json().get("detail")), (409, WCERT.TG_TAKEN))
db.expire_all()
ck("ikkinchi o'quvchiga sertifikat yaratilmadi",
   [x[:2] for x in certs_of(GZB) + certs_of(TOSH)
    if "/101" in (x[3] or "")], [])
RB2 = {r["row"]: r for r in client.get(TGU + "?status=all",
                                       headers=HBM2).json()["rows"]}
ck("boshqa filial rahbari: bog'langan, lekin o'quvchi ismi / id yo'q",
   [(RB2[i]["status"], RB2[i]["student_id"], RB2[i]["student_name"])
    for i in (0, 1)], [("linked", None, None), ("linked", None, None)])
ck("o'z filiali rahbari — ism ko'rinadi",
   {r["row"]: r for r in client.get(TGU + "?status=all", headers=HBM)
    .json()["rows"]}[1]["student_name"], "Sobirov Abdurahmon Akmal o'g'li")
ck("juda katta / nol / manfiy student_id — 404",
   [client.post(f"{TGU}/5/link", json={"student_id": v},
                headers=HF).status_code for v in (10 ** 30, 0, -5)],
   [404, 404, 404])

P7 = "/tmp/verify_wordbank_tg/telegram_results_have.json"
json.dump({"results": [
    {"post": 701, "date": "2026-10-08", "name": "Toshmatova Alina",
     "exam": "ielts", "level": "", "score": 7.0},
]}, open(P7, "w", encoding="utf-8"))
os.environ["WORDBANK_TG_FILE"] = P7
nc = db.query(models.Certificate).count()
r = client.post(f"{TGU}/0/link", json={"student_id": TOSH}, headers=HF)
ck("o'quvchida shu natija bor — 409, qator bog'lanmagan qoladi",
   (r.status_code, r.json().get("detail"),
    client.get(TGU + "?status=all", headers=HF).json()["rows"][0]["status"]),
   (409, WCERT.TG_DUP, "unmatched"))
ck("existing — matn bo'lsa 400",
   client.post(f"{TGU}/0/link", json={"student_id": TOSH, "existing": "ha"},
               headers=HF).status_code, 400)
na = db.query(models.AuditLog).count()
r = client.post(f"{TGU}/0/link", json={"student_id": TOSH, "existing": True},
                headers=HF)
ck("existing=true — 200, bog'langan (sertifikatsiz)",
   (r.status_code, r.json()["status"], r.json()["student_id"]),
   (200, "linked", TOSH))
db.expire_all()
ck("yangi sertifikat yaratilmadi", db.query(models.Certificate).count(), nc)
ck("qaror saqlandi va audit'da",
   (json.loads(db.query(models.IntegrationSetting)
               .get("wordbank_tg_links").value).get(
       "701:Toshmatova Alina:ielts:7.0"),
    db.query(models.AuditLog).filter(
        models.AuditLog.field == "wordbank_tg_links").count(),
    db.query(models.AuditLog).count() - na), (TOSH, 1, 1))
ck("ro'yxatda bog'langan; yashirib bo'lmaydi",
   (client.get(TGU + "?status=all", headers=HF).json()["counts"],
    client.post(f"{TGU}/0/dismiss", json={}, headers=HF).status_code),
   ({"unmatched": 0, "ambiguous": 0, "linked": 1, "dismissed": 0}, 409))
os.environ["WORDBANK_TG_FILE"] = P5

print("\n=== 9. OCHIQ HOLAT YO'LI — ISM YO'Q (v2 importdan keyin ham) ===")
client.post(f"{TGU}/4/dismiss", json={}, headers=HF)    # import buni o'tkazsin
# Xodim 503 ni GZA ga bog'lagan; endi aynan shu ismli o'quvchi paydo
# bo'ldi — seed natijani unga QAYTA bermasin (xodim tanlovi ustun)
GZC = mk_st("Ortikjanova Go'zalxon", br, "gzc")
WB._STATUS_DONE = False
d = client.get("/api/wordbank/status").json()
ck("status: v2 import shu faylda yurdi — yashirilgan o'tkazildi, xodim "
   "bog'lagani 'bor', bitta o'xshash (Pulatova 7.0) yaratildi",
   {k: (d.get("tg_certs") or {}).get(k) for k in
    ("created", "existing", "fuzzy", "ambiguous", "unmatched", "skipped",
     "dismissed")},
   {"created": 1, "existing": 3, "fuzzy": 1, "ambiguous": [502],
    "unmatched": [], "skipped": [506], "dismissed": [504]})
db.expire_all()
ck("xodim bog'lagan natija yangi adashga berilmadi",
   (certs_of(GZC), [x[3] for x in certs_of(GZA)]),
   ([], ["Telegram: https://t.me/JonyAcademy/503"]))
ck("Pulatova endi bog'langan (import yaratdi)",
   {r["row"]: r for r in client.get(TGU + "?status=all", headers=HF)
    .json()["rows"]}[5]["status"], "linked")
ck("status javobida ism yo'q",
   any(n in json.dumps(d, ensure_ascii=False) for n in (
       "Rustamova", "Karimova", "Ortikjanova", "O'rtiqjonova", "Nobody",
       "Pulatova", "Sobirov", "Laylo", "Go'zal")), False)
print("\n=== 10. IKKI NUSXA BIR VAQTDA SEED — TAKROR YO'Q ===")
RACE = mk_st("Poyga Tekshiruvchi", br, "race")
P8 = "/tmp/verify_wordbank_tg/telegram_results_race.json"
json.dump({"results": [
    {"post": 801, "date": "2026-10-08", "name": "Poyga Tekshiruvchi",
     "exam": "ielts", "level": "", "score": 6.5},
]}, open(P8, "w", encoding="utf-8"))
_orig_has = WCERT._has_same
inner = {}


def _racing(dbx, sid, kind, level, score):
    # Birinchi nusxa "yo'q" deb qaror qildi — shu payt ikkinchisi to'liq
    # yurib ulguradi (bir nechta instansiya / bir vaqtdagi status so'rovi)
    got = _orig_has(dbx, sid, kind, level, score)
    if not inner:
        WCERT._has_same = _orig_has
        other = SessionLocal()
        inner["rep"] = WCERT.seed_telegram(other, P8)
        other.close()
    return got


WCERT._has_same = _racing
outer = WCERT.seed_telegram(db, P8)
WCERT._has_same = _orig_has
ck("ikkinchi nusxa yaratdi, birinchisi hamma yozuvini bekor qildi",
   ((inner.get("rep") or {}).get("created"), outer), (1, None))
db.expire_all()
ck("o'quvchida bitta sertifikat", [x[:2] for x in certs_of(RACE)],
   [("ielts", "6.5")])
json.dump({"results": [
    {"post": 802, "date": "2026-10-09", "name": "Poyga Tekshiruvchi",
     "exam": "ielts", "level": "", "score": 7.5},
]}, open(P8, "w", encoding="utf-8"))
db.add(models.SeedMark(key=WCERT.TG_SEED + ":" + hashlib.sha256(
    open(P8, "rb").read()).hexdigest()[:12]))
db.commit()                      # boshqa nusxa belgi qo'ygan, kesh bilmaydi
ck("bazada belgi bor — yurmaydi, yozuv yo'q",
   (WCERT.seed_telegram(db, P8), len(certs_of(RACE))), (None, 1))
db.close()

print("\n" + ("BARCHASI OK" if not fails else f"XATOLAR: {len(fails)}"))
for f_ in fails:
    print("  -", f_)
sys.exit(1 if fails else 0)
