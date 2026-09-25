"""Jony Student — inglizcha lug'atning DAVOMI: Unit 34–100 (2026-09-25).

NEGA. Jahongir: "JonyStudentAPP da lugat 33ta unit bor shuni ozi bilan
lugat balli 9.0 soz kamku u yerda 9.0 uchun 15000+ soz kerak kamida
shuning uchun ... davomiy unitlarni ham qosh 100tadan soz bolsin va
men bergan 34ta unitdan tashqari barcha common sozlarni commonligi
boyicha ketma ket qoyib ketgin ... umumiy 100ta unit bolsin ...
shundan kelib chiqib IELTS ball bersin".

MANBA. wordfreq (subtitr + kitob + yangilik + web korpuslari
aralashmasi) chastota ro'yxati. Undan olib tashlandi: 1–33 unitdagi
so'zlar; atoqli otlar (ism, shahar, brend, millat); qisqartmalar;
ko'plik / o'tgan zamon / qiyosiy shakllar va sof -ing fe'l shakllari
(building, meeting kabi mustaqil so'zlar QOLDI); Britaniya imlosi
dublikatlari (colour/color); qo'pol so'zlar (maktab ilovasi).
Qolgani CHASTOTA TARTIBIDA 100 tadan 67 unitga bo'lindi —
vocab_extra_data.json: {"en": [[so'z, tarjima, unit, misol], ...]}.
E'tibor: botning 1–33 unitida "the, to, in, you, it" kabi eng oddiy
so'zlar yo'q edi — ular ham shu tartib bilan 34-unitga tushdi.

SEED QOIDASI (koreys tili xatosidan saboq, 2026-09-25): marker
KONTENTDAN chiqadi (fayl hajmi) — fayl kengaysa/o'zgarsa seed o'zi
qayta ishlaydi. Jonli bazada bir sovuq startda WORD_BUDGET tagacha
yoziladi, qolgani keyingi startda DAVOM ETADI (500 xatosi bermaslik
uchun; vocab_seed._add_lang_words bilan bir xil qoida).

MA'LUMOT YO'QOTILMAYDI: bazada allaqachon bor so'z (masalan eski SAT
bo'limidan is_active=0 bo'lib qolgan) o'chirilmaydi — yangi unitga
ko'chiriladi va qayta faollashtiriladi (VocabAttempt'lar word_id
orqali saqlanadi); faol so'zga tegilmaydi.
"""
import json
import os

_DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "vocab_extra_data.json")

# Bir sovuq startda yoziladigan eng ko'p so'z (vocab_seed bilan bir xil).
WORD_BUDGET = 1200

FIRST_UNIT = 34
LAST_UNIT = 100
WORDS_PER_UNIT = 100


def _level_for_unit(u: int) -> str:
    """Unit -> taxminiy CEFR (chastota o'rni bo'yicha: ~5 000-so'zgacha
    B2, ~7 500-gacha C1, undan yuqorisi C2). 1–33 uchun vocab_seed
    o'z xaritasini ishlatadi, bu faqat 34+ uchun."""
    if u <= 45:
        return "B2"
    if u <= 70:
        return "C1"
    return "C2"


def _load() -> list:
    with open(_DATA, encoding="utf-8") as f:
        return json.load(f)["en"]


def _seed_key() -> str:
    """Marker kaliti fayl hajmidan chiqadi — kontent o'zgarsa kalit
    o'zgaradi va seed qayta ishlaydi (faylni ochmasdan, arzon)."""
    try:
        size = os.path.getsize(_DATA)
    except OSError:
        size = 0
    return f"vocab_en_extra:{size}"


LOCK_ID = 20260925          # pg_advisory lock kaliti (ixtiyoriy son)


def _try_lock(db) -> bool:
    """PARALLEL SOVUQ STARTLAR QULFI (2026-09-25, jonli logdan saboq).

    Deploydan keyin bir vaqtda 4 ta instansiya uyg'ondi, har biri
    o'zicha birinchi 1 200 so'zni yozdi — bir-birining yozuvini
    ko'rmagani uchun DUBLIKATLAR paydo bo'ldi (vocab_words.word da
    unique cheklov yo'q). Endi Postgres'da tranzaksiya qulfi olinadi:
    qulf band bo'lsa (boshqa instansiya yozyapti) bu start seedni
    o'tkazib yuboradi. Qulf commit/rollback bilan o'zi bo'shaydi —
    instansiya o'lib qolsa ham osilib qolmaydi. SQLite (testlar,
    bitta jarayon) da qulf shart emas."""
    try:
        if db.bind.dialect.name != "postgresql":
            return True
        from sqlalchemy import text
        got = db.execute(text("SELECT pg_try_advisory_xact_lock(:k)"),
                         {"k": LOCK_ID}).scalar()
        return bool(got)
    except Exception:
        return True


def dedupe_active_en(db) -> int:
    """Faol inglizcha DUBLIKATLARNI tozalaydi — O'CHIRMASDAN.

    Bir xil so'z (kichik harfda) bir nechta faol qatorda bo'lsa: eng
    kichik id QOLADI, qolganlari is_active=0 bo'ladi, ularga bog'langan
    VocabAttempt'lar (o'quvchi urinishlari) asosiy qatorga
    KO'CHIRILADI — progress yo'qolmaydi. Nofaol eski dublikatlarga
    (2026-08-11 migratsiyasi) tegilmaydi."""
    import models
    rows = (db.query(models.VocabWord.id, models.VocabWord.word)
            .filter(models.VocabWord.is_active == 1,
                    (models.VocabWord.language == "en")
                    | (models.VocabWord.language.is_(None)))
            .order_by(models.VocabWord.id).all())
    keep, dups = {}, []
    for wid, word in rows:
        k = (word or "").strip().lower()
        if k in keep:
            dups.append((wid, keep[k]))
        else:
            keep[k] = wid
    for dup_id, keep_id in dups:
        (db.query(models.VocabAttempt)
         .filter(models.VocabAttempt.word_id == dup_id)
         .update({models.VocabAttempt.word_id: keep_id},
                 synchronize_session=False))
        (db.query(models.VocabWord)
         .filter(models.VocabWord.id == dup_id)
         .update({models.VocabWord.is_active: 0},
                 synchronize_session=False))
    if dups:
        db.commit()
        print(f"[vocab-extra] dublikat tozalandi: {len(dups)} ta "
              f"(nofaol qilindi, urinishlar ko'chirildi)")
    return len(dups)


def seed_vocab_extra(db, budget: int | None = WORD_BUDGET) -> dict | None:
    """Idempotent: faqat yo'q so'zlarni qo'shadi, borini tegmaydi.

    budget=None — chegara yo'q (testlar / bo'sh baza uchun)."""
    import models
    from common import _seed_done, _seed_mark
    key = _seed_key()
    if _seed_done(db, key):
        return None
    if not _try_lock(db):
        print("[vocab-extra] boshqa instansiya yozyapti — o'tkazib yuborildi")
        return {"made": 0, "revived": 0, "finished": False, "locked": True}
    # Avval (bo'lsa) parallel startlardan qolgan dublikatlarni tozalaymiz —
    # shunda "have" ro'yxati toza bo'ladi.
    deduped = dedupe_active_en(db)
    if not _try_lock(db):          # dedupe commit qulfni bo'shatgan bo'lishi mumkin
        return {"made": 0, "revived": 0, "finished": False, "locked": True,
                "deduped": deduped}
    rows = _load()
    cap = float("inf") if budget is None else int(budget)

    # Bazadagi inglizcha so'zlar (faol va nofaol) — yengil so'rov.
    # FAOL nusxa birinchi keladi: bitta so'zning faol va nofaol
    # (dublikat) qatori bo'lsa, faoli hisobga olinadi — aks holda
    # nofaol dublikat "tiklanib" yana ikkita faol bo'lib qolardi.
    have = {}
    for wid, word, active, topic in (
            db.query(models.VocabWord.id, models.VocabWord.word,
                     models.VocabWord.is_active, models.VocabWord.topic)
            .filter((models.VocabWord.language == "en")
                    | (models.VocabWord.language.is_(None)))
            .order_by(models.VocabWord.is_active.desc(),
                      models.VocabWord.id.asc()).all()):
        have.setdefault((word or "").strip().lower(), (wid, active, topic))

    made = revived = 0
    finished = True
    for word, tr, unit, ex in rows:
        if made + revived >= cap:
            finished = False
            break
        key_w = word.strip().lower()
        hit = have.get(key_w)
        topic = f"Unit {int(unit)}"
        if hit is not None:
            wid, active, old_topic = hit
            if active:
                continue                     # allaqachon faol — tegmaymiz
            w = db.query(models.VocabWord).get(wid)
            if w is None:
                continue
            w.is_active = 1
            w.topic = topic
            w.level = _level_for_unit(int(unit))
            w.language = "en"
            if not (w.example or "").strip() and ex:
                w.example = ex
            have[key_w] = (wid, 1, topic)
            revived += 1
            continue
        db.add(models.VocabWord(
            word=key_w, translation=tr, level=_level_for_unit(int(unit)),
            topic=topic, example=ex or None, language="en",
            is_active=1, created_by="wordfreq"))
        have[key_w] = (None, 1, topic)
        made += 1
    if made or revived:
        db.commit()
    if finished:
        _seed_mark(db, key)
        print(f"[vocab-extra] en Unit {FIRST_UNIT}-{LAST_UNIT}: to'liq "
              f"(+{made}, tiklandi {revived})")
    else:
        print(f"[vocab-extra] en: qismi yuklandi (+{made}, tiklandi "
              f"{revived}), keyingi startda davom")
    return {"made": made, "revived": revived, "finished": finished,
            "deduped": deduped}
