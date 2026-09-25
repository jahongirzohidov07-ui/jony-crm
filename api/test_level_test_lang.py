# -*- coding: utf-8 -*-
"""DARAJA TESTIDA FAQAT INGLIZ TILI (2026-09-08)

Jahongir: "tanlab bo'lmayabdi ekan xatolik bor ekan. Programmada
daraja aniqlash testi ingliz tilida olinganda koreys tili savoli ham
chiqib qolyabdi".

SABAB: _mk_grammar() GrammarQuestion'ni TIL bo'yicha filtrlamasdi.
Bazada ru/de/ko grammatikasi ham bor (2026-08-24 da qo'shilgan), va
ular ingliz daraja testiga aralashib chiqardi — o'quvchi savolni
o'qiy olmasdi, ya'ni javob tanlay olmasdi.

Test tekshiradi:
  1. koreys/rus grammatika savoli daraja testiga UMUMAN chiqmaydi;
  2. til belgisi noto'g'ri qo'yilgan (language='en') koreys SO'ZI ham
     lug'at/listening bo'limiga chiqmaydi — yozuv lotin alifbosida
     bo'lishi tekshiriladi;
  3. bir xil tarjimali ikki so'z bo'lsa, variantlar TAKRORLANMAYDI
     (ilgari bir xil ikki tugma chiqib, qaysi birini bosish noma'lum
     bo'lardi);
  4. ingliz savollari avvalgidek ishlayveradi.
"""
import os
import sys

os.environ["DATABASE_URL"] = "sqlite:////tmp/lt_lang.db"
if os.path.exists("/tmp/lt_lang.db"):
    os.remove("/tmp/lt_lang.db")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json                                          # noqa: E402
from fastapi.testclient import TestClient            # noqa: E402
import main, models, roles, level_test               # noqa: E402
import entry                                         # noqa: E402,F401
from database import SessionLocal                    # noqa: E402
from auth import hash_password                       # noqa: E402

client = TestClient(main.app)
fails = []


def ck(name, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + name + f": {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


db = SessionLocal()
b = models.Branch(name="Zafar"); db.add(b); db.commit()

# --- GRAMMATIKA: 3 ta ingliz + 3 ta koreys + 2 ta rus ---
for i in range(3):
    db.add(models.GrammarQuestion(
        topic="Present Simple", level="A1", kind="fill", is_active=1,
        prompt=f"She ___ to school every day ({i}).",
        options=json.dumps(["goes", "go", "going", "gone"]),
        answer="goes", language=None))          # NULL = ingliz
for i in range(3):
    db.add(models.GrammarQuestion(
        topic="조사", level="A1", kind="fill", is_active=1,
        prompt=f"저는 학생___ 입니다 ({i}).",
        options=json.dumps(["이", "가", "을", "를"]),
        answer="이", language="ko"))
for i in range(2):
    db.add(models.GrammarQuestion(
        topic="Падежи", level="A1", kind="fill", is_active=1,
        prompt=f"Я иду ___ школу ({i}).",
        options=json.dumps(["в", "на", "к", "у"]),
        answer="в", language="ru"))
db.commit()

# --- LUG'AT: ingliz so'zlar + til belgisi XATO qo'yilgan koreyscha ---
EN = [("apple", "olma"), ("book", "kitob"), ("water", "suv"),
      ("house", "uy"), ("bread", "non"), ("table", "stol")]
for w, t in EN:
    db.add(models.VocabWord(word=w, translation=t, level="A1",
                            language="en", is_active=1))
# language="en" deb yozilgan, lekin so'z koreyscha — eski xato yozuv
db.add(models.VocabWord(word="사과", translation="olma (ko)", level="A1",
                        language="en", is_active=1))
db.add(models.VocabWord(word="книга", translation="kitob (ru)", level="A1",
                        language="en", is_active=1))
db.commit()

print("=== 1. Grammatika: faqat ingliz savollari ===")
# MEZON (2026-09-25 tuzatildi): "ord(ch) > 0x24F" deb tekshirish
# XATO edi — ingliz gapidagi uzun tire ("— it's arranged", U+2014)
# ham "koreyscha" deb sanalardi va bu test sababsiz qizil turardi.
# Tilni HARF bildiradi: hangul, kirill, arab, xitoy. Tinish belgisi
# emas. Mezon mahsulot kodi bilan bitta joyda — level_test._foreign_letter.
seen, ko_ru, leaked = set(), 0, []
for _ in range(60):
    q = level_test._mk_grammar(db, "A1", [])
    if not q:
        continue
    pr = q["payload"]["prompt"]
    seen.add(pr)
    if any(level_test._foreign_letter(ch) for ch in pr):
        ko_ru += 1
        leaked.append(pr)
ck("koreys/rus savoli chiqmadi", ko_ru, 0)
if leaked:
    print("      aralashib ketgan savollar: " + str(leaked[:3]))
ck("ingliz savollari chiqdi", len(seen) > 0, True)
# Tinish belgisi bor ingliz gapi CHETLATILMASLIGI kerak
ck("uzun tire ingliz savolini chetlatmaydi",
   level_test._latin_word("We meet tomorrow — it's arranged."), True)
ck("qo'shtirnoq (’) chetlatmaydi",
   level_test._latin_word("don’t"), True)
ck("hangul chetlatiladi", level_test._latin_word("사과"), False)
ck("kirill chetlatiladi",
   level_test._latin_word("книга"), False)

print()
print("=== 2. Lug'at: lotin bo'lmagan so'z chiqmaydi ===")
from sqlalchemy import or_ as _or                   # noqa: E402
_all = (db.query(models.VocabWord)
        .filter(models.VocabWord.is_active == 1,
                models.VocabWord.level == "A1",
                _or(models.VocabWord.language == "en",
                    models.VocabWord.language.is_(None))).all())
# Mezon mahsulot kodi bilan BIR XIL bo'lishi shart — aks holda
# sonlar mos kelmaydi (seed'dagi ingliz so'zlarida tinish belgisi
# bo'lishi mumkin, u chetlatilmaydi).
_bad = [w for w in _all
        if any(level_test._foreign_letter(ch) for ch in w.word)]
pool = level_test._vocab_pool(db, "A1")
ck("bazada lotin bo'lmagan yozuv bor", len(_bad) >= 2, True)
ck("to'plam aynan shularsiz", len(pool), len(_all) - len(_bad))
ck("koreys so'zi yo'q", any(w.word == "\uc0ac\uacfc" for w in pool), False)
ck("kirill so'zi yo'q", any(w.word == "\u043a\u043d\u0438\u0433\u0430"
                            for w in pool), False)

print()
print("=== 3. Listening savolida hamma variant lotin va TAKRORLANMAS ===")
bad_script = dupes = 0
for _ in range(40):
    q = level_test._mk_vocab(db, "A1", [], listen=True)
    if not q:
        continue
    opts = q["payload"]["options"]
    if len(set(opts)) != len(opts):
        dupes += 1
    if any(ord(ch) > 0x24F for ch in q["payload"]["say"]):
        bad_script += 1
    if q["answer"] not in opts:
        fails.append("to'g'ri javob variantlar orasida yo'q")
ck("aytiladigan so'z hamisha lotin", bad_script, 0)
ck("takrorlangan variant yo'q", dupes, 0)

print()
print("=== 4. Bir xil tarjimali so'zlar bo'lsa ham dubl chiqmaydi ===")
db.add(models.VocabWord(word="volume", translation="kitob", level="A1",
                        language="en", is_active=1))
db.add(models.VocabWord(word="residence", translation="uy", level="A1",
                        language="en", is_active=1))
db.commit()
dupes2 = 0
for _ in range(60):
    q = level_test._mk_vocab(db, "A1", [])
    if not q:
        continue
    opts = q["payload"]["options"]
    if len(set(opts)) != len(opts):
        dupes2 += 1
ck("dubl variant yo'q", dupes2, 0)

print()
print("XULOSA: " + ("HAMMASI O'TDI" if not fails
                    else f"{len(fails)} ta xato: {fails}"))
sys.exit(1 if fails else 0)
