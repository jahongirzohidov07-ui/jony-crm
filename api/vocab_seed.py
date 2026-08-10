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


def seed_vocab(db):
    """Idempotent seed + eski yozuvlarni to'g'rilash."""
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

    # ---- 3) BOSHQA TILLAR (ru/de/ko) ----
    for lang in ("ru", "de", "ko"):
        have = {w for (w,) in db.query(models.VocabWord.word)
                .filter(models.VocabWord.language == lang).all()}
        for word, tr, unit, ex in data.get(lang, []):
            if word in have:
                continue
            have.add(word)
            db.add(models.VocabWord(
                word=word, translation=tr, level=None,
                topic=f"Unit {unit}", example=ex or None,
                language=lang, is_active=1, created_by="JonyLugatBot"))
            made += 1
    if made or moved or deact:
        db.commit()
    return {"made": made, "moved": moved, "deactivated": deact}
