"""SEED MARKERI YANGI KONTENTNI TO'SIB QO'YMASIN (2026-09-25).

MUAMMO. Jahongir: "programmada JonyStudentappda muammo koreys tiliga
o'tmayabdi ekan". Sabab: seed'lar "bajarildi" markeri bilan
qo'riqlangan edi. Marker bir marta yozilgach, keyinchalik faylga
qo'shilgan YANGI TIL jonli bazaga tushmay qoldi. Yangi (test)
bazada marker yo'q — shuning uchun test yashil, jonli tizim esa
bo'sh. Xatoni ko'rsatmaydigan test — eng yomon test.

BU TEST aynan jonli tizimdagi holatni yasaydi: markerni OLDIN
yozib qo'yadi, keyin seed'ni chaqiradi. To'g'ri yozilgan seed
baribir yetishmayotgan kontentni qo'shishi kerak.
"""
import os, sys

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_seedmark/db.sqlite"
os.makedirs("/tmp/verify_seedmark", exist_ok=True)
if os.path.exists("/tmp/verify_seedmark/db.sqlite"):
    os.remove("/tmp/verify_seedmark/db.sqlite")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import models  # noqa: E402
from database import SessionLocal, engine  # noqa: E402

models.Base.metadata.create_all(bind=engine)
db = SessionLocal()
fails = []


def ck(n, g, w):
    ok = g == w
    print(("OK  " if ok else "XATO ") + f"{n}: {g}"
          + ("" if ok else f"   (kutilgan {w})"))
    if not ok:
        fails.append(n)


import common  # noqa: E402
import grammar_seed3  # noqa: E402
import vocab_seed  # noqa: E402

print("=== JONLI TIZIM HOLATI YASALADI (marker bor, kontent yo'q) ===")
common._SEED_KEYS = None
common._seed_mark(db, "grammar_v3")
common._seed_mark(db, "vocab_v2")
ck("grammar_v3 markeri qo'yildi", common._seed_done(db, "grammar_v3"),
   True)
ck("vocab_v2 markeri qo'yildi", common._seed_done(db, "vocab_v2"), True)
ck("grammatika bazasi bo'sh",
   db.query(models.GrammarQuestion).count(), 0)
ck("lug'at bazasi bo'sh", db.query(models.VocabWord).count(), 0)

print("\n=== GRAMMATIKA SEED'I MARKERGA QARAMAY ISHLASHI KERAK ===")
grammar_seed3.seed_grammar_extra(db)
by_lang = {}
for lang, lvl, n in (
        db.query(models.GrammarQuestion.language,
                 models.GrammarQuestion.level,
                 __import__("sqlalchemy").func.count(
                     models.GrammarQuestion.id))
        .group_by(models.GrammarQuestion.language,
                  models.GrammarQuestion.level).all()):
    by_lang[(lang, lvl)] = n
print("     " + str(sorted(by_lang.items())))
for lang, lvl in (("ko", "A1"), ("ko", "A2"), ("ru", "A1"),
                  ("ru", "A2"), ("de", "A1"), ("de", "A2"),
                  ("en", "C1"), ("en", "C2")):
    ck(f"grammatika {lang} {lvl} tushdi",
       by_lang.get((lang, lvl), 0) > 0, True)

print("\n=== IKKINCHI CHAQIRIQ HECH NARSA QO'SHMASIN (idempotent) ===")
before = db.query(models.GrammarQuestion).count()
grammar_seed3.seed_grammar_extra(db)
after = db.query(models.GrammarQuestion).count()
ck("qayta chaqirilganda son o'zgarmadi", after, before)

print("\n=== LUG'AT BYUDJET BILAN BO'LIB YUKLANADI ===")
# Til butunlay yo'q bo'lsa 4000 ga yaqin so'z kerak. Hammasini bir
# sovuq startda yozish 500 xatosi berishi mumkin — shuning uchun
# byudjet bor va keyingi startda DAVOM etadi. Shuni isbotlaymiz:
# kichik byudjet bilan chaqirsak, bir qismi tushadi va til "tugadi"
# deb belgilanmaydi.
_data = vocab_seed._load()
n1 = vocab_seed._add_lang_words(db, _data, ["ko"], budget=50)
ck("byudjet bo'yicha 50 so'z tushdi", n1, 50)
ck("til hali 'tugadi' deb belgilanmadi",
   common._seed_done(db, vocab_seed._lang_key("ko")), False)
n2 = vocab_seed._add_lang_words(db, _data, ["ko"], budget=50)
ck("keyingi chaqiriqda DAVOM etdi (yana 50)", n2, 50)
ko_now = (db.query(models.VocabWord)
          .filter(models.VocabWord.language == "ko").count())
ck("jami 100 koreys so'zi bor", ko_now, 100)

print("\n=== LUG'AT: YANGI TIL MARKERGA QARAMAY TUSHSIN ===")
# Har chaqiriq byudjet chegarasida ishlaydi, shuning uchun bir necha
# "sovuq start"ni taqlid qilamiz (jonli tizimda ham shunday bo'ladi).
starts = 0
for _ in range(30):
    starts += 1
    vocab_seed.seed_vocab(db)
    if vocab_seed._all_langs_done(db):
        break
print(f"     {starts} ta 'sovuq start'dan keyin tugadi")
ck("hamma til tugadi deb belgilandi",
   vocab_seed._all_langs_done(db), True)
vb = dict(db.query(models.VocabWord.language,
                   __import__("sqlalchemy").func.count(
                       models.VocabWord.id))
          .group_by(models.VocabWord.language).all())
print("     " + str(vb))
for lang in ("ru", "de", "ko"):
    ck(f"lug'at {lang} tushdi", vb.get(lang, 0) > 500, True)

print("\n=== LUG'AT IKKINCHI CHAQIRIQ (idempotent) ===")
before = db.query(models.VocabWord).count()
vocab_seed.seed_vocab(db)
after = db.query(models.VocabWord).count()
ck("qayta chaqirilganda son o'zgarmadi", after, before)

print("\n=== BOR TIL QAYTA YOZILMAYDI ===")
todo = vocab_seed._langs_without_words(db)
ck("yetishmayotgan til yo'q", todo, [])
miss = grammar_seed3._missing_sets(db)
ck("yetishmayotgan grammatika to'plami yo'q", len(miss), 0)

print("\n=== MARKER KALITI KONTENTGA BOG'LANGAN ===")
# Kalit tillar/darajalar ro'yxatidan chiqadi: yangi til qo'shilsa
# kalit o'zgaradi va seed bir marta qayta ishlaydi.
gkey = grammar_seed3._seed_key()
vkey = vocab_seed._seed_key()
print("     grammatika kaliti: " + gkey)
print("     lug'at kaliti:     " + vkey)
ck("grammatika kalitida 'ko' bor", "ko-" in gkey, True)
ck("lug'at kalitida 'ko' bor", "ko" in vkey, True)
ck("grammatika kaliti yozilgan", common._seed_done(db, gkey), True)
ck("lug'at kaliti yozilgan", common._seed_done(db, vkey), True)
ck("eski kalit yangisidan farq qiladi", gkey == "grammar_v3", False)

print()
if fails:
    print(f"XATO: {len(fails)} ta tekshiruv o'tmadi")
    for f in fails:
        print("   - " + f)
    sys.exit(1)
print("HAMMASI O'TDI")
sys.exit(0)
