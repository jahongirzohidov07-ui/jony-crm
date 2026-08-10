"""JONY STUDENT — o'quvchining O'Z ilovasi (2026-08-09).

Jahongir so'radi: o'quvchilar uchun alohida ilova — ichida lug'at
o'yinlari (Jonylearning bot uslubida), reytinglar, va grammar/reading/
listening/writing/speaking bo'yicha ALOHIDA darajalar; umumiy daraja
ustiga bosilganda har biri alohida progress bilan ko'rinsin.

XAVFSIZLIK QOIDASI — bu fayldagi HAR BIR yo'l faqat KIRGAN
O'QUVCHINING O'ZI haqida ma'lumot beradi. Hech qayerda student_id
tashqaridan qabul qilinmaydi: har doim _me(db, user) orqali
tokendagi foydalanuvchidan topiladi. Shunday qilib bir o'quvchi
boshqasining ma'lumotini so'ray olmaydi (URL'ni o'zgartirib ham).

Reytingda boshqa o'quvchilar ko'rinadi — bu ataylab (musobaqa
motivatsiya beradi), lekin FAMILIYA QISQARTIRILADI (roles.mask_name
bilan bir xil uslub) va faqat o'z guruhi/filiali doirasida.
"""
import json
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import random
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

import audit
import models
import roles
import schemas
from auth import get_current_user, require_role
from database import get_db
from common import *  # noqa: F401,F403 - shared helpers/state

router = APIRouter()


# =====================================================================
#  YORDAMCHILAR
# =====================================================================
def _me(db: Session, user: models.User) -> models.Student:
    """Tokendagi foydalanuvchining o'quvchi kartasi.

    Bu — butun fayldagi yagona "men kimman" manbai. student_id
    tashqaridan HECH QACHON olinmaydi."""
    s = _student_of_user(db, user)
    if not s:
        raise HTTPException(
            403, "Bu bo'lim faqat o'quvchilar uchun. Hisobingiz "
                 "o'quvchi kartasiga bog'lanmagan — administratorga "
                 "murojaat qiling.")
    return s


def _mask(full_name: str) -> str:
    """Reytingda: "Aziz Karimov" -> "Aziz K." — bola boshqa oilalarning
    to'liq ismini ko'rmasin."""
    parts = (full_name or "").split()
    if len(parts) < 2:
        return full_name or ""
    return f"{parts[0]} {parts[1][0]}."


def _streak_days(db: Session, student_id: int) -> int:
    """Ketma-ket necha kun mashq qilgan (bugundan orqaga).

    Bugun hali o'ynamagan bo'lsa ham kechagi ketma-ketlik saqlanadi —
    "kun tugamaguncha yo'qolmaydi" tamoyili (aks holda ertalab kirgan
    bola streak nolga tushganini ko'rib ko'nglini qoldiradi)."""
    rows = (db.query(models.VocabAttempt.date)
            .filter(models.VocabAttempt.student_id == student_id)
            .distinct().order_by(models.VocabAttempt.date.desc())
            .limit(400).all())
    days = [r[0] for r in rows if r[0]]
    if not days:
        return 0
    today = date.today()
    if days[0] < today - timedelta(days=1):
        return 0
    streak = 0
    cursor = days[0]
    for d in days:
        if d == cursor:
            streak += 1
            cursor = cursor - timedelta(days=1)
        elif d < cursor:
            break
    return streak


def _active_words(db: Session, level: str | None = None):
    q = db.query(models.VocabWord).filter(models.VocabWord.is_active == 1)
    if level:
        q = q.filter(models.VocabWord.level == level)
    return q


# =====================================================================
#  BOSH SAHIFA
# =====================================================================
@router.get("/api/student/home")
def student_home(db: Session = Depends(get_db),
                 user=Depends(require_role(roles.STUDENT))):
    """Jony Student bosh ekrani: daraja, coin/XP, streak, reyting."""
    s = _me(db, user)
    g = db.query(models.Group).get(s.group_id) if s.group_id else None
    gam = _gam_card(db, s)
    skills = _skills_card(db, s.id)
    ranks = _student_ranks(db, s.id)

    today = date.today()
    solved_today = (db.query(func.count(models.VocabAttempt.id))
                    .filter(models.VocabAttempt.student_id == s.id,
                            models.VocabAttempt.date == today).scalar() or 0)
    correct_today = (db.query(func.count(models.VocabAttempt.id))
                     .filter(models.VocabAttempt.student_id == s.id,
                             models.VocabAttempt.date == today,
                             models.VocabAttempt.correct == 1).scalar() or 0)

    return {
        "name": s.full_name,
        "photo": s.photo,
        "group": g.name if g else None,
        "level_label": (g.level if g else None) or s.level,
        "status": s.status,
        "overall": skills["overall"],
        "skills": skills["skills"],
        "gamification": {
            "coins": gam.get("coins"),
            "lifetime_xp": gam.get("lifetime_xp"),
            "level": gam.get("level"),
            "league": gam.get("league"),
        },
        "streak": _streak_days(db, s.id),
        "today": {"answered": int(solved_today), "correct": int(correct_today)},
        "ranks": ranks,
        "games": [{"key": k, "label": lbl, "hint": hint}
                  for k, lbl, hint in roles.VOCAB_GAMES],
    }


@router.get("/api/student/skills")
def student_skills(db: Session = Depends(get_db),
                   user=Depends(require_role(roles.STUDENT))):
    """Umumiy daraja + har bir ko'nikma bo'yicha alohida daraja va
    keyingi darajagacha qancha qolgani."""
    s = _me(db, user)
    return _skills_card(db, s.id)


# =====================================================================
#  LUG'AT O'YINLARI
# =====================================================================
def _round_flashcard(words):
    return [{"word_id": w.id, "prompt": w.word, "answer": w.translation,
             "example": w.example} for w in words]


def _round_choice(words, pool, forward: bool):
    """4 variantli tanlov. forward=True: inglizcha -> o'zbekcha."""
    out = []
    for w in words:
        right = w.translation if forward else w.word
        others = [x for x in pool if x.id != w.id]
        random.shuffle(others)
        wrong = [(x.translation if forward else x.word) for x in others]
        # Bir xil variant ikki marta chiqmasin
        seen, opts = {right}, [right]
        for cand in wrong:
            if cand in seen:
                continue
            seen.add(cand)
            opts.append(cand)
            if len(opts) == 4:
                break
        random.shuffle(opts)
        out.append({
            "word_id": w.id,
            "prompt": w.word if forward else w.translation,
            "options": opts,
            "answer": right,
        })
    return out


def _round_match(words):
    left = [{"word_id": w.id, "text": w.word} for w in words]
    right = [{"word_id": w.id, "text": w.translation} for w in words]
    random.shuffle(right)
    return [{"left": left, "right": right}]


def _round_truefalse(words, pool):
    """To'g'ri/Xato: yarmiga TO'G'RI tarjima, yarmiga boshqa so'zning
    tarjimasi qo'yiladi. Tasodifiy emas — aniq yarma-yarim, shunda
    "hamma vaqt ha desam bo'ldi" degan hiyla ishlamaydi."""
    out = []
    for i, w in enumerate(words):
        show_correct = (i % 2 == 0)
        if show_correct:
            shown = w.translation
        else:
            others = [x for x in pool
                      if x.id != w.id and x.translation != w.translation]
            shown = random.choice(others).translation if others else w.translation
            if shown == w.translation:
                show_correct = True
        out.append({
            "word_id": w.id,
            "prompt": w.word,
            "shown": shown,
            "answer": "togri" if show_correct else "xato",
        })
    random.shuffle(out)
    return out


def _round_scramble(words):
    """Harflarni tartiblash: so'z harflari aralashtiriladi."""
    out = []
    for w in words:
        letters = list(w.word)
        if len(letters) > 1:
            for _ in range(8):
                random.shuffle(letters)
                if "".join(letters).lower() != w.word.lower():
                    break
        out.append({
            "word_id": w.id,
            "prompt": w.translation,
            "letters": letters,
            "answer": w.word,
        })
    return out


def _round_spelling(words):
    return [{"word_id": w.id, "prompt": w.translation, "answer": w.word,
             "hint": (w.word[0] + "·" * (len(w.word) - 1)) if w.word else ""}
            for w in words]


@router.get("/api/student/vocab/round")
def vocab_round(game: str = "en_uz", level: str | None = None,
                db: Session = Depends(get_db),
                user=Depends(require_role(roles.STUDENT))):
    """Bitta o'yin bosqichi (round) tuzadi.

    MUHIM: to'g'ri javob ham qaytariladi — o'yin telefonning o'zida
    tez ishlashi uchun (har bosishda serverga so'rov yubormaydi).
    Ball esa FAQAT serverda hisoblanadi (/answer), shuning uchun
    javobni oldindan bilish reytingni buzmaydi: ball berilishidan
    oldin server so'zni bazadan qayta tekshiradi."""
    s = _me(db, user)
    if game not in roles.VOCAB_GAME_KEYS:
        raise HTTPException(400, "Bunday o'yin yo'q")

    pool = _active_words(db, level).all()
    if len(pool) < 4:
        raise HTTPException(
            400, "Lug'at bazasi hali to'lmagan — administratorga "
                 "murojaat qiling")

    n = min(roles.VOCAB_ROUND_SIZE, len(pool))
    words = random.sample(pool, n)

    if game == "flashcard":
        items = _round_flashcard(words)
    elif game == "en_uz":
        items = _round_choice(words, pool, forward=True)
    elif game == "uz_en":
        items = _round_choice(words, pool, forward=False)
    elif game == "match":
        items = _round_match(words[:min(5, len(words))])
    elif game == "truefalse":
        items = _round_truefalse(words, pool)
    elif game == "scramble":
        items = _round_scramble(words)
    else:  # spelling
        items = _round_spelling(words)

    return {
        "game": game,
        "label": roles.VOCAB_GAME_LABELS[game],
        "items": items,
        "xp_per_correct": roles.VOCAB_XP_PER_CORRECT,
        "student": s.full_name,
    }


@router.post("/api/student/vocab/answer")
def vocab_answer(payload: schemas.VocabAnswerIn,
                 db: Session = Depends(get_db),
                 user=Depends(require_role(roles.STUDENT))):
    """Bitta javobni yozadi va to'g'ri bo'lsa ball/XP beradi.

    To'g'riligini SERVER hal qiladi (mijozning "correct: true" degan
    so'ziga ishonmaymiz) — so'z bazadan olinadi va solishtiriladi."""
    s = _me(db, user)
    if payload.game not in roles.VOCAB_GAME_KEYS:
        raise HTTPException(400, "Bunday o'yin yo'q")
    w = db.query(models.VocabWord).get(payload.word_id)
    if not w:
        raise HTTPException(404, "So'z topilmadi")

    given = (payload.answer or "").strip().lower()
    if payload.game in ("uz_en", "spelling", "scramble"):
        expected = (w.word or "").strip().lower()
    elif payload.game == "flashcard":
        # Kartochkada o'quvchi o'zini o'zi baholaydi ("bildim"/"bilmadim")
        expected = "bildim"
    elif payload.game == "truefalse":
        # Bu yerda mijoz "togri"/"xato" deb javob beradi, LEKIN qaysi
        # tarjima ko'rsatilgani ham kerak — aks holda server nimani
        # tekshirishini bilmaydi. shown maydonini solishtiramiz.
        shown = (payload.shown or "").strip().lower()
        truth = "togri" if shown == (w.translation or "").strip().lower() \
            else "xato"
        expected = truth
    else:
        expected = (w.translation or "").strip().lower()
    ok = bool(given) and given == expected

    db.add(models.VocabAttempt(
        student_id=s.id, word_id=w.id, game=payload.game,
        correct=1 if ok else 0, answer=(payload.answer or "")[:200],
        date=date.today()))
    db.commit()

    xp_given = 0.0
    if ok:
        # Mavjud XP tizimi orqali (alohida hisob-kitob yozilmadi):
        # takrorlanmasligi uchun idempotentlik kaliti — kun + so'z +
        # o'yin, ya'ni bir kunda bir so'zdan bir o'yinda bir marta XP.
        try:
            res = award_xp(
                db, student_id=s.id, event_code="VOCAB_CORRECT",
                amount=roles.VOCAB_XP_PER_CORRECT,
                source_type="vocab_game", source_id=w.id,
                reason=f"Lug'at o'yini: {roles.VOCAB_GAME_LABELS[payload.game]}",
                idempotency_key=f"VOCAB:{date.today()}:{s.id}:{w.id}:{payload.game}")
            if res.get("ok"):
                xp_given = float(roles.VOCAB_XP_PER_CORRECT)
        except Exception:
            db.rollback()

    return {
        "correct": ok,
        "expected": (w.word
                     if payload.game in ("uz_en", "spelling", "scramble")
                     else w.translation),
        "xp": xp_given,
        "skills": _skills_card(db, s.id),
    }


@router.get("/api/student/vocab/stats")
def vocab_stats(db: Session = Depends(get_db),
                user=Depends(require_role(roles.STUDENT))):
    """O'quvchining o'z lug'at statistikasi: jami, to'g'ri, o'yin
    kesimida va oxirgi 7 kun."""
    s = _me(db, user)
    total = (db.query(func.count(models.VocabAttempt.id))
             .filter(models.VocabAttempt.student_id == s.id).scalar() or 0)
    correct = (db.query(func.count(models.VocabAttempt.id))
               .filter(models.VocabAttempt.student_id == s.id,
                       models.VocabAttempt.correct == 1).scalar() or 0)
    by_game = (db.query(models.VocabAttempt.game,
                        func.count(models.VocabAttempt.id),
                        func.sum(models.VocabAttempt.correct))
               .filter(models.VocabAttempt.student_id == s.id)
               .group_by(models.VocabAttempt.game).all())
    today = date.today()
    week = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        c = (db.query(func.count(models.VocabAttempt.id))
             .filter(models.VocabAttempt.student_id == s.id,
                     models.VocabAttempt.date == d,
                     models.VocabAttempt.correct == 1).scalar() or 0)
        week.append({"date": d.isoformat(), "correct": int(c)})
    return {
        "total": int(total), "correct": int(correct),
        "percent": round(correct * 100 / total, 1) if total else 0,
        "streak": _streak_days(db, s.id),
        "by_game": [{
            "game": gme,
            "label": roles.VOCAB_GAME_LABELS.get(gme, gme),
            "total": int(t), "correct": int(c or 0),
        } for gme, t, c in by_game],
        "week": week,
    }


# =====================================================================
#  REYTING
# =====================================================================
# =====================================================================
#  O'QUVCHI PROFILI (2026-08-10, Jahongir: "eng yuqorida ism familiyasi,
#  alohida rasmi uchun joy bo'lsin, faqat ism/familiya/otchestvani
#  alohida o'zgartirsin, boshqa har xil narsa yozib bo'lmasin")
# =====================================================================

import re as _re

# Ism/familiya/otasining ismi uchun QAT'IY qolip: faqat harflar
# (lotin, kirill, o'zbek belgilar), ichida chiziqcha yoki apostrof
# bo'lishi mumkin. Raqam, emoji, probel, boshqa belgilar - YO'Q.
# Shu tufayli "ism" maydoniga laqab/reklama/har xil narsa yozib
# bo'lmaydi.
_NAME_RE = _re.compile(
    r"^[A-Za-z\u0400-\u04FF\u2018\u2019'ʻ`-]{2,30}$")


def _clean_name(raw: str, label: str, required: bool = True):
    v = (raw or "").strip()
    if not v:
        if required:
            raise HTTPException(400, f"{label} kiritilishi shart")
        return None
    if " " in v:
        raise HTTPException(
            400, f"{label} bitta so'z bo'lishi kerak (probelsiz)")
    if not _NAME_RE.match(v):
        raise HTTPException(
            400, f"{label} faqat harflardan iborat bo'lsin - raqam va "
                 f"boshqa belgilar mumkin emas")
    # Bosh harfini katta qilamiz, qolganiga tegmaymiz (O'ktamjon,
    # Abdul-Aziz kabi ismlar buzilmasin)
    return v[0].upper() + v[1:]


@router.get("/api/student/profile")
def student_profile(db: Session = Depends(get_db),
                    user=Depends(require_role(roles.STUDENT))):
    s = _me(db, user)
    g = db.query(models.Group).get(s.group_id) if s.group_id else None
    return {
        "full_name": s.full_name,
        "first_name": s.first_name,
        "last_name": s.last_name,
        "middle_name": s.middle_name,
        "photo": s.photo,
        "birth_date": s.birth_date.isoformat() if s.birth_date else None,
        "address": s.address,
        "school": s.school,
        "school_grade": s.school_grade,
        "phone": s.phone,          # faqat ko'rsatish uchun (login)
        "group": g.name if g else None,
    }


@router.put("/api/student/profile")
def student_profile_save(payload: schemas.StudentProfileIn,
                         db: Session = Depends(get_db),
                         user=Depends(require_role(roles.STUDENT))):
    """O'quvchi o'z ma'lumotlarini to'ldiradi.

    Ism/familiya/otasining ismi QAT'IY tekshiruvdan o'tadi va
    full_name shulardan yig'iladi - xodimlar bazasida ham darhol
    yangi ism ko'rinadi. O'zgarish auditga yoziladi - kim qachon
    o'zgartirgani izsiz qolmaydi. Telefon BU YERDAN o'zgarmaydi
    (u login)."""
    s = _me(db, user)

    first = _clean_name(payload.first_name, "Ism")
    last = _clean_name(payload.last_name, "Familiya")
    middle = _clean_name(payload.middle_name, "Otasining ismi",
                         required=False)

    old_name = s.full_name
    s.first_name, s.last_name, s.middle_name = first, last, middle
    s.full_name = f"{first} {last}"

    if payload.birth_date is not None:
        if payload.birth_date > date.today():
            raise HTTPException(400, "Tug'ilgan sana kelajakda bo'lmaydi")
        if payload.birth_date.year < 1950:
            raise HTTPException(400, "Tug'ilgan sanani tekshiring")
        s.birth_date = payload.birth_date
    for f in ("address", "school", "school_grade"):
        v = getattr(payload, f)
        if v is not None:
            setattr(s, f, v.strip()[:200] or None)

    # Kirish hisobidagi ism ham yangilansin - salomlashish va
    # xodimlar ro'yxatida bir xil ko'rinsin
    if s.user_id:
        u = db.query(models.User).get(s.user_id)
        if u:
            u.full_name = s.full_name
    db.commit()

    if old_name != s.full_name:
        try:
            audit.log(db, user, entity="student", action="update",
                      entity_id=s.id, entity_label=s.full_name,
                      field="F.I.Sh.", old_value=old_name,
                      new_value=f"{last} {first}"
                                + (f" {middle}" if middle else ""),
                      note="O'quvchi ilovadan o'zi o'zgartirdi",
                      branch_id=s.branch_id, commit=True)
        except Exception:
            db.rollback()
    return student_profile(db=db, user=user)


@router.put("/api/student/photo")
def student_photo_save(payload: schemas.StudentPhotoIn,
                       db: Session = Depends(get_db),
                       user=Depends(require_role(roles.STUDENT))):
    """Avatar: kichraytirilgan rasm data URL ko'rinishida.

    Chegara ~300KB - mijoz rasmni saqlashdan avval o'zi 512px ga
    kichraytiradi. Katta fayl kelsa rad etiladi (baza shishmasin)."""
    s = _me(db, user)
    ph = payload.photo
    if ph:
        if not ph.startswith(("data:image/jpeg;base64,",
                              "data:image/png;base64,",
                              "data:image/webp;base64,")):
            raise HTTPException(400, "Faqat rasm yuklash mumkin")
        if len(ph) > 400_000:
            raise HTTPException(400, "Rasm juda katta - qayta urining")
        s.photo = ph
    else:
        s.photo = None
    db.commit()
    return {"ok": True, "photo": bool(s.photo)}


# =====================================================================
#  GRAMMAR MASHQLARI (2026-08-10, Jahongir: "Grammar har bir ingliz
#  tilidagi mavzuga xilma-xil mashqlar bo'lsin")
# =====================================================================

@router.get("/api/student/grammar/topics")
def grammar_topics(db: Session = Depends(get_db),
                   user=Depends(require_role(roles.STUDENT))):
    """Mavzular ro'yxati + o'quvchining har biridagi progressi.

    Progress = shu mavzuda KAMIDA BIR MARTA to'g'ri yechilgan
    savollar / jami savollar. Shuning uchun bola mavzuni "yopish"
    uchun hamma savolini to'g'ri yechishi kerak - shunchaki kirib
    chiqish foiz bermaydi."""
    s = _me(db, user)
    qs = (db.query(models.GrammarQuestion)
          .filter(models.GrammarQuestion.is_active == 1)
          .order_by(models.GrammarQuestion.topic_order,
                    models.GrammarQuestion.id).all())
    if not qs:
        return {"levels": [], "total_correct": 0}

    solved = {qid for (qid,) in
              db.query(func.distinct(models.GrammarAttempt.question_id))
              .filter(models.GrammarAttempt.student_id == s.id,
                      models.GrammarAttempt.correct == 1).all()}

    topics = {}
    for q in qs:
        t = topics.setdefault(q.topic, {
            "topic": q.topic, "level": q.level, "total": 0,
            "solved": 0, "kinds": set(),
        })
        t["total"] += 1
        t["kinds"].add(q.kind)
        if q.id in solved:
            t["solved"] += 1

    by_level = {}
    for t in topics.values():
        t["percent"] = round(t["solved"] * 100 / t["total"]) \
            if t["total"] else 0
        t["done"] = t["solved"] >= t["total"]
        t["kinds"] = sorted(t["kinds"])
        by_level.setdefault(t["level"], []).append(t)

    order = ["A1", "A2", "B1", "B2", "C1"]
    return {
        "levels": [{"level": lv, "topics": by_level[lv]}
                   for lv in order if lv in by_level],
        "total_correct": len(solved),
        "round_size": roles.GRAMMAR_ROUND_SIZE,
    }


@router.get("/api/student/grammar/round")
def grammar_round(topic: str, db: Session = Depends(get_db),
                  user=Depends(require_role(roles.STUDENT))):
    """Bitta mashg'ulot: mavzudan 8 ta savol.

    AVVAL hali to'g'ri yechilmaganlar olinadi (bola yangi narsa
    o'rgansin), yetmasa yechilganlaridan to'ldiriladi. To'g'ri javob
    MIJOZGA KETMAYDI - tekshiruv faqat serverda (/answer). order
    turida so'zlar shu yerda aralashtiriladi."""
    s = _me(db, user)
    qs = (db.query(models.GrammarQuestion)
          .filter(models.GrammarQuestion.is_active == 1,
                  models.GrammarQuestion.topic == topic).all())
    if not qs:
        raise HTTPException(404, "Bunday mavzu topilmadi")

    solved = {qid for (qid,) in
              db.query(func.distinct(models.GrammarAttempt.question_id))
              .filter(models.GrammarAttempt.student_id == s.id,
                      models.GrammarAttempt.correct == 1).all()}
    fresh = [q for q in qs if q.id not in solved]
    done = [q for q in qs if q.id in solved]
    random.shuffle(fresh)
    random.shuffle(done)
    picked = (fresh + done)[:roles.GRAMMAR_ROUND_SIZE]
    random.shuffle(picked)

    items = []
    for q in picked:
        opts = json.loads(q.options)
        if q.kind == "order":
            # So'zlarni aralashtiramiz; tasodifan to'g'ri tartibda
            # qolib ketmasin
            shuffled = opts[:]
            for _ in range(10):
                random.shuffle(shuffled)
                if shuffled != opts or len(opts) < 2:
                    break
            opts = shuffled
        elif q.kind == "fill":
            opts = opts[:]
            random.shuffle(opts)
        # error turida tartib saqlanadi - variantlar gapning
        # bo'laklari, o'qish tartibi muhim
        items.append({
            "id": q.id, "kind": q.kind, "prompt": q.prompt,
            "options": opts, "solved": q.id in solved,
        })

    return {
        "topic": topic, "items": items,
        "xp_per_correct": roles.GRAMMAR_XP_PER_CORRECT,
    }


def _norm_sentence(t: str) -> str:
    t = (t or "").strip().lower()
    for ch in ".,!?;:":
        t = t.replace(ch, "")
    return " ".join(t.split())


@router.post("/api/student/grammar/answer")
def grammar_answer(payload: schemas.GrammarAnswerIn,
                   db: Session = Depends(get_db),
                   user=Depends(require_role(roles.STUDENT))):
    """Javobni tekshiradi (faqat SERVER hal qiladi) va yozib qo'yadi.

    XP bitta savol uchun BIR marta: avval to'g'ri yechilgan savolga
    qayta XP berilmaydi - lekin mashq qilaverish mumkin."""
    s = _me(db, user)
    q = db.query(models.GrammarQuestion).get(payload.question_id)
    if not q or not q.is_active:
        raise HTTPException(404, "Savol topilmadi")

    if q.kind == "order":
        ok = _norm_sentence(payload.answer) == _norm_sentence(q.answer)
    else:
        ok = (payload.answer or "").strip() == (q.answer or "").strip()

    was_solved = (db.query(models.GrammarAttempt.id)
                  .filter(models.GrammarAttempt.student_id == s.id,
                          models.GrammarAttempt.question_id == q.id,
                          models.GrammarAttempt.correct == 1)
                  .first() is not None)

    db.add(models.GrammarAttempt(
        student_id=s.id, question_id=q.id,
        correct=1 if ok else 0,
        answer=(payload.answer or "")[:300], date=date.today()))
    db.commit()

    xp_given = 0.0
    if ok and not was_solved:
        try:
            res = award_xp(
                db, student_id=s.id, event_code="GRAMMAR_CORRECT",
                amount=roles.GRAMMAR_XP_PER_CORRECT,
                source_type="grammar", source_id=q.id,
                reason=f"Grammar mashqi: {q.topic}",
                idempotency_key=f"GRAM:{s.id}:{q.id}")
            if res.get("ok"):
                xp_given = float(roles.GRAMMAR_XP_PER_CORRECT)
        except Exception:
            db.rollback()

    return {
        "correct": ok,
        "expected": q.answer,
        "explain": q.explain,
        "first_time": ok and not was_solved,
        "xp": xp_given,
    }


@router.get("/api/student/leaderboard")
def student_leaderboard(scope: str = "group", period: str = "all",
                        db: Session = Depends(get_db),
                        user=Depends(require_role(roles.STUDENT))):
    """Lug'at o'yinlari reytingi.

    scope: group (o'z guruhi) | branch (o'z filiali)
    period: all (butun davr) | week (shu hafta)

    Faqat O'Z guruhi/filiali — butun markaz bo'yicha ro'yxat
    berilmaydi (bola o'zi tanimagan yuzlab odam orasida 300-o'rinni
    ko'rib ruhlanmaydi). Familiya qisqartiriladi."""
    s = _me(db, user)
    if scope not in ("group", "branch"):
        raise HTTPException(400, "scope: group yoki branch")
    if period not in ("all", "week"):
        raise HTTPException(400, "period: all yoki week")

    q = (db.query(models.Student.id, models.Student.full_name,
                  func.count(models.VocabAttempt.id).label("pts"))
         .join(models.VocabAttempt,
               models.VocabAttempt.student_id == models.Student.id)
         .filter(models.VocabAttempt.correct == 1,
                 models.Student.status.in_(("active", "trial"))))

    if scope == "group":
        if not s.group_id:
            return {"scope": scope, "period": period, "rows": [],
                    "me": None,
                    "hint": "Siz hali guruhga biriktirilmagansiz."}
        q = q.filter(models.Student.group_id == s.group_id)
    else:
        if not s.branch_id:
            return {"scope": scope, "period": period, "rows": [], "me": None,
                    "hint": "Filial biriktirilmagan."}
        q = q.filter(models.Student.branch_id == s.branch_id)

    if period == "week":
        today = date.today()
        q = q.filter(models.VocabAttempt.date
                     >= today - timedelta(days=today.weekday()))

    rows = (q.group_by(models.Student.id, models.Student.full_name)
            .order_by(func.count(models.VocabAttempt.id).desc())
            .limit(50).all())

    out, me = [], None
    for i, (sid, name, pts) in enumerate(rows, 1):
        mine = sid == s.id
        item = {"rank": i, "name": ("Siz" if mine else _mask(name)),
                "points": int(pts), "is_me": mine}
        out.append(item)
        if mine:
            me = item
    return {"scope": scope, "period": period, "rows": out, "me": me,
            "total": len(out)}


# =====================================================================
#  ADMIN: LUG'AT BAZASINI TO'LDIRISH
# =====================================================================
@router.get("/api/vocab/words")
def vocab_words(level: str | None = None, q: str | None = None,
                db: Session = Depends(get_db),
                user=Depends(require_role(*roles.ACADEMIC_ACCESS))):
    """Lug'at bazasini ko'rish (xodimlar uchun)."""
    query = db.query(models.VocabWord)
    if level:
        query = query.filter(models.VocabWord.level == level)
    if q:
        like = f"%{q.strip()}%"
        query = query.filter(models.VocabWord.word.ilike(like))
    rows = query.order_by(models.VocabWord.id.desc()).limit(500).all()
    total = db.query(func.count(models.VocabWord.id)).scalar() or 0
    return {
        "total": int(total),
        "rows": [{"id": w.id, "word": w.word, "translation": w.translation,
                  "level": w.level, "topic": w.topic, "example": w.example,
                  "is_active": bool(w.is_active)} for w in rows],
    }


@router.post("/api/vocab/import")
def vocab_import(payload: schemas.VocabImportIn,
                 db: Session = Depends(get_db),
                 user=Depends(require_role(*roles.ACADEMIC_ACCESS))):
    """Katta so'z ro'yxatini bir zumda yuklash.

    Jonylearning botdagi so'z bazasini (yoki istalgan Excel/CSV
    ro'yxatni) shu yerdan yuklash mumkin — KOD O'ZGARTIRMASDAN.
    Bir xil so'z+tarjima ikki marta yozilmaydi."""
    added, skipped = 0, 0
    for item in payload.words:
        w = (item.word or "").strip()
        t = (item.translation or "").strip()
        if not w or not t:
            skipped += 1
            continue
        dup = (db.query(models.VocabWord)
               .filter(func.lower(models.VocabWord.word) == w.lower(),
                       func.lower(models.VocabWord.translation) == t.lower())
               .first())
        if dup:
            skipped += 1
            continue
        db.add(models.VocabWord(
            word=w, translation=t,
            level=(item.level or "").strip() or None,
            topic=(item.topic or "").strip() or None,
            example=(item.example or "").strip() or None,
            is_active=1, created_by=user.full_name))
        added += 1
    db.commit()
    audit.log(db, user, entity="vocab", action="import",
              new_value=f"{added} ta so'z", commit=True)
    total = db.query(func.count(models.VocabWord.id)).scalar() or 0
    return {"added": added, "skipped": skipped, "total": int(total)}
