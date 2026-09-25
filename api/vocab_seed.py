"""Jony Student — lug'at bazasi (2026-08-11 da QAYTA QURILDI).

MANBA: JonyLugatBot (github.com/jahongirzohidov07-ui/JonyLugatBot).
Ma'lumot vocab_data.json faylida (repoda birga yuradi):
  en: 3751 so'z, Unit 1-33  — botning ASOSIY (General) kursi.
      Jahongir (2026-08-11): "botda har unitda 116 ta atrofida so'z
      bor edi, sen unitlarga bo'lingan joylarini noto'g'ri
      anglagansan... SAT vocabulary'ni bu yerga qo'shmaganing
      ma'qul, menga faqat 33 unit so'zlarni ber." Avvalgi seed
      botning SAT bo'limini (unit 34-59) ham aralashtirib yuborgan
      edi - endi FAQAT 1-33.
  ru: 2995 so'z (30 unit), de: 3822 (39), ko: 4166 (104) — botning
      boshqa til kurslari, bayroq almashtirilganda ishlaydi.

MIGRATSIYA: eski (noto'g'ri bo'lingan) inglizcha yozuvlar
O'CHIRILMAYDI - so'z matni bo'yicha yangi unitga KO'CHIRILADI
(VocabAttempt'lar word_id ga bog'liq, o'quvchi progressi saqlanadi).
Yangi ro'yxatda yo'q so'zlar (SAT va h.k.) is_active=0 bo'ladi.
"""
import json
import os

_DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "vocab_data.json")

# Unit -> CEFR daraja (taxminiy, level filtri uchun; asosiy
# navigatsiya endi unit bo'yicha)
def _level_for_unit(u: int) -> str:
    if u <= 8:
        return "A1"
    if u <= 16:
        return "A2"
    if u <= 25:
        return "B1"
    return "B2"


def _load():
    with open(_DATA, encoding="utf-8") as f:
        return json.load(f)


OTHER_LANGS = ("ru", "de", "ko")


def _langs_without_words(db) -> list:
    """Qaysi tilda bazada umuman so'z yo'q — bitta guruhlangan so'rov.

    NEGA KERAK (2026-09-25, Jahongir: "koreys tiliga o'tmayabdi
    ekan"). "vocab_v2" markeri bir marta yozilgandan keyin bu seed
    boshqa ochilmaydi. Agar keyinchalik faylga yangi til qo'shilsa,
    jonli bazaga tushmay qoladi — yangi (test) bazada esa hammasi
    joyida ko'rinadi. Shuning uchun marker ustiga arzon KONTENT
    tekshiruvi qo'yildi."""
    import models
    from sqlalchemy import func
    rows = (db.query(models.VocabWord.language,
                     func.count(models.VocabWord.id))
            .group_by(models.VocabWord.language).all())
    have = {lang for lang, n in rows if n and lang}
    return [lg for lg in OTHER_LANGS if lg not in have]


# Bitta sovuq startda qo'shiladigan eng ko'p so'z. Til butunlay yo'q
# bo'lsa 4000 ga yaqin so'z yozilishi kerak — hammasini bir so'rovda
# yozish sovuq startni cho'zib, 500 xatosi berishi mumkin. Shuning
# uchun bo'lib-bo'lib yoziladi va keyingi startda DAVOM ETADI
# (oylik hisoblashdagi "uzilsa davom etadi" qoidasi bilan bir xil).
WORD_BUDGET = 1200


def _lang_key(lang: str) -> str:
    """Til to'liq yuklangani belgisi — shu bo'lsa qayta sanalmaydi."""
    return f"vocab_lang_{lang}"


def _add_lang_words(db, data, langs, budget=None) -> int:
    """Berilgan tillarning so'zlarini qo'shadi (borini tegmaydi).

    budget=None — chegara yo'q. BO'SH BAZADA shunday chaqiriladi:
    u yerda birinchi start baribir sekin (173 jadval yaratiladi) va
    hammasi bir yo'la tushishi kerak.

    budget=son — JONLI bazada til keyin qo'shilgan holat uchun. Til
    oxirigacha yozilsa o'sha til uchun belgi qo'yiladi; byudjet
    tugasa belgi QO'YILMAYDI va keyingi startda shu tildan davom
    etiladi (sovuq startni cho'zib 500 xatosi bermaslik uchun)."""
    import models
    from common import _seed_done, _seed_mark
    cap = float("inf") if budget is None else budget
    made = 0
    for lang in langs:
        if _seed_done(db, _lang_key(lang)):
            continue
        if made >= cap:
            break
        have = {w for (w,) in db.query(models.VocabWord.word)
                .filter(models.VocabWord.language == lang).all()}
        rows = data.get(lang, [])
        finished = True
        for word, tr, unit, ex in rows:
            if made >= cap:
                finished = False
                break
            if word in have:
                continue
            have.add(word)
            db.add(models.VocabWord(
                word=word, translation=tr, level=None,
                topic=f"Unit {unit}", example=ex or None,
                language=lang, is_active=1, created_by="JonyLugatBot"))
            made += 1
        if made:
            db.commit()
        if finished:
            _seed_mark(db, _lang_key(lang))
            print(f"[vocab] {lang}: to'liq yuklandi")
        else:
            print(f"[vocab] {lang}: qismi yuklandi, keyingi startda davom")
            break
    return made


def _seed_key() -> str:
    """Marker kaliti tillar ro'yxatidan chiqadi — yangi til
    qo'shilsa kalit o'zgaradi va seed bir marta qayta ishlaydi."""
    return "vocab_v2:" + ",".join(("en",) + OTHER_LANGS)


def _lang_counts(db) -> dict:
    """Til -> bazadagi so'z soni (bitta guruhlangan so'rov)."""
    import models
    from sqlalchemy import func
    return dict(db.query(models.VocabWord.language,
                         func.count(models.VocabWord.id))
                .group_by(models.VocabWord.language).all())


def _all_langs_done(db) -> bool:
    from common import _seed_done
    return all(_seed_done(db, _lang_key(lg)) for lg in OTHER_LANGS)


def seed_vocab(db):
    """Idempotent seed + eski yozuvlarni to'g'rilash."""
    from common import _seed_done, _seed_mark
    key = _seed_key()
    if _seed_done(db, key):
        return None
    if _seed_done(db, "vocab_v2"):
        # Og'ir inglizcha migratsiya allaqachon bajarilgan (eski
        # marker). Lekin keyin yangi til qo'shilgan bo'lishi mumkin
        # — faqat shuni to'ldiramiz.
        todo = [lg for lg in OTHER_LANGS
                if not _seed_done(db, _lang_key(lg))]
        if not todo:
            _seed_mark(db, key)
            return None
        counts = _lang_counts(db)
        data = _load()
        # Allaqachon to'lgan tilga belgi qo'yib, ishni qisqartiramiz
        # (JSON'da dublikat bo'lgani uchun aynan teng bo'lmaydi).
        rest = []
        for lg in todo:
            need = len(data.get(lg, []))
            if need and counts.get(lg, 0) >= need * 0.9:
                _seed_mark(db, _lang_key(lg))
            else:
                rest.append(lg)
        # JONLI baza: byudjet bilan, keyingi startda davom etadi
        made = (_add_lang_words(db, data, rest, budget=WORD_BUDGET)
                if rest else 0)
        if _all_langs_done(db):
            _seed_mark(db, key)
        return {"made": made, "moved": 0, "deactivated": 0,
                "langs": rest}
    import models

    data = _load()

    # ---- 1) ESKI INGLIZCHA YOZUVLARNI TO'G'RILASH ----
    # So'z matni -> yangi unit xaritasi
    en_map = {}
    for word, tr, unit, ex in data["en"]:
        en_map.setdefault(word.strip().lower(), unit)

    existing = (db.query(models.VocabWord)
                .filter((models.VocabWord.language == "en")
                        | (models.VocabWord.language.is_(None)))
                .all())
    seen_words = set()
    moved = deact = 0
    for w in existing:
        if w.language is None:
            w.language = "en"
        key = (w.word or "").strip().lower()
        unit = en_map.get(key)
        if unit is None:
            if w.is_active:
                w.is_active = 0          # SAT yoki ro'yxatdan tashqari
                deact += 1
            continue
        if key in seen_words:
            # bitta so'z ikki marta bo'lsa - dublikatni o'chiramiz
            if w.is_active:
                w.is_active = 0
            continue
        seen_words.add(key)
        new_topic = f"Unit {unit}"
        if w.topic != new_topic or not w.is_active:
            w.topic = new_topic
            w.level = _level_for_unit(unit)
            w.is_active = 1
            moved += 1
    db.commit()

    # ---- 2) YETISHMAYOTGAN SO'ZLARNI QO'SHISH ----
    made = 0
    for word, tr, unit, ex in data["en"]:
        key = word.strip().lower()
        if key in seen_words:
            continue
        seen_words.add(key)
        db.add(models.VocabWord(
            word=word, translation=tr, level=_level_for_unit(unit),
            topic=f"Unit {unit}", example=ex or None,
            language="en", is_active=1, created_by="JonyLugatBot"))
        made += 1

    if made or moved or deact:
        db.commit()

    # ---- 3) BOSHQA TILLAR (ru/de/ko) ----
    # Bitta joyda turadi: keyinchalik yangi til qo'shilsa ham xuddi
    # shu funksiya ishlaydi (yuqoridagi marker yo'li ham shuni
    # chaqiradi), shunda ikki xil mantiq bo'lib ketmaydi.
    made += _add_lang_words(db, data, OTHER_LANGS)
    # Inglizcha migratsiya tugadi — bu belgini darrov qo'yamiz.
    _seed_mark(db, "vocab_v2")
    # Umumiy kalit esa FAQAT hamma til to'liq yuklangach yoziladi
    # (byudjet tugab qolgan bo'lsa keyingi startda davom etadi).
    if _all_langs_done(db):
        _seed_mark(db, _seed_key())
    return {"made": made, "moved": moved, "deactivated": deact}
