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


def _active_words(db: Session, level: str | None = None,
                  unit: str | None = None, language: str = "en"):
    q = db.query(models.VocabWord).filter(models.VocabWord.is_active == 1)
    # Til (2026-08-11, bayroq): eski yozuvlarda NULL = en
    if language == "en":
        q = q.filter((models.VocabWord.language == "en")
                     | (models.VocabWord.language.is_(None)))
    else:
        q = q.filter(models.VocabWord.language == language)
    if level:
        q = q.filter(models.VocabWord.level == level)
    if unit:
        q = q.filter(models.VocabWord.topic == unit)
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
        "balance": student_balance(db, s.id),
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
                unit: str | None = None, language: str = "en",
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

    if language not in ("en", "ru", "de", "ko"):
        language = "en"
    pool = _active_words(db, level, unit, language).all()
    if len(pool) < 4:
        raise HTTPException(
            400, "Bu bo'limda so'z kam - boshqa unit tanlang"
                 if unit else
                 "Lug'at bazasi hali to'lmagan — administratorga "
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
        "unit": unit,
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
#  TO'LOVLAR VA IMTIHONLAR TARIXI (2026-08-10, Jahongir: "Profil
#  qismida to'lovlar tarixi, imtihonlar tarixi ham tursin, bosh
#  sahifada balansi ko'rinib turishi kerak")
# =====================================================================

@router.get("/api/student/payments")
def student_payments(db: Session = Depends(get_db),
                     user=Depends(require_role(roles.STUDENT))):
    """O'quvchining pul tarixi: to'lovlar (+), hisoblangan oylik (-),
    chegirmalar. Ota-ona portalidagi bilan bir xil manba - payments
    jadvali, hech qanday alohida hisob yo'q."""
    s = _me(db, user)
    rows = (db.query(models.Payment)
            .filter(models.Payment.student_id == s.id)
            .order_by(models.Payment.created_at.desc())
            .limit(60).all())
    kinds = {"payment": "To'lov", "charge": "Oylik hisob",
             "discount": "Chegirma"}
    return {
        "balance": student_balance(db, s.id),
        "rows": [{
            "id": p.public_id or p.id,
            "amount": p.amount,
            "kind": p.kind,
            "kind_label": kinds.get(p.kind, p.kind),
            "note": p.note,
            "date": (p.created_at.date().isoformat()
                     if p.created_at else None),
        } for p in rows],
    }


@router.get("/api/student/exams")
def student_exams(db: Session = Depends(get_db),
                  user=Depends(require_role(roles.STUDENT))):
    """Imtihonlar tarixi - tasdiqlangan natijalar."""
    s = _me(db, user)
    rows = (db.query(models.ExamResult, models.Exam)
            .join(models.Exam,
                  models.ExamResult.exam_id == models.Exam.id)
            .filter(models.ExamResult.student_id == s.id,
                    models.Exam.status.in_(["approved", "done"]))
            .order_by(models.Exam.date.desc()).limit(40).all())
    return {"rows": [{
        "id": er.id,
        "title": ex.title or roles.exam_title(ex.kind, ex.unit_no),
        "date": ex.date.isoformat() if ex.date else None,
        "score": er.score,
        "max_score": ex.max_score,
        "percent": er.percent,
        "band": er.band,
        "coins": er.coins,
        "absent": bool(er.absent),
    } for er, ex in rows]}


# =====================================================================
#  LUG'AT UNITLARI (2026-08-10, Jahongir: "botga unit so'zlarni
#  kiritgandim - unitni tanlab shu bo'yicha practica qilsin")
# =====================================================================

@router.get("/api/student/vocab/units")
def vocab_units(language: str = "en", db: Session = Depends(get_db),
                user=Depends(require_role(roles.STUDENT))):
    """Unitlar ro'yxati + o'rganish foizi (2026-08-11 qoidasi).

    Jahongir: "har bir so'zni kamida 3 marta to'g'ri topgan bo'lsa
    progress bar ko'k, 6 marta topgan bo'lsa yashil; 99% gacha o'zi
    practice qilib boradi, ustoz 'unitni topshirdi' deb tick qo'ysa
    100% bo'ladi."

    Hisob: har so'z bo'yicha TO'G'RI javoblar SONI (takror o'yinlar
    ham sanaladi - bola necha marta mashq qilgani muhim):
      3+  = so'z "o'rganilgan" (ko'k mezon)
      6+  = so'z "mustahkam" (yashil mezon)
    Foiz = o'rganilgan(3+) / jami * 99 (yaxlitlab) - 99% dan
    oshmaydi. Ustoz tasdig'i (VocabUnitPass) = 100%.
    Bar rangi: passed -> "gold", hammasi 6+ -> "green", aks "blue"."""
    s = _me(db, user)
    if language not in ("en", "ru", "de", "ko"):
        language = "en"

    words = _active_words(db, language=language).all()
    if not words:
        return {"units": [], "total_words": 0, "language": language}

    by_unit = {}
    for w in words:
        by_unit.setdefault(w.topic or "Boshqa", []).append(w.id)

    # Har so'z bo'yicha to'g'ri javoblar soni (bitta so'rov)
    cnt_rows = (db.query(models.VocabAttempt.word_id,
                         func.count(models.VocabAttempt.id))
                .filter(models.VocabAttempt.student_id == s.id,
                        models.VocabAttempt.correct == 1)
                .group_by(models.VocabAttempt.word_id).all())
    cnt = dict(cnt_rows)

    passed = {p.unit for p in db.query(models.VocabUnitPass)
              .filter(models.VocabUnitPass.student_id == s.id,
                      models.VocabUnitPass.language == language).all()}

    def unit_no(t):
        try:
            return int(str(t).split()[-1])
        except (ValueError, IndexError):
            return 9999

    units = []
    for topic, ids in by_unit.items():
        n = len(ids)
        l3 = sum(1 for i in ids if cnt.get(i, 0) >= 3)
        l6 = sum(1 for i in ids if cnt.get(i, 0) >= 6)
        is_passed = topic in passed
        percent = 100 if is_passed else min(99, round(l3 * 99 / n)) \
            if n else 0
        units.append({
            "key": topic, "n": n,
            "learned3": l3, "learned6": l6,
            "percent": percent,
            "passed": is_passed,
            "tone": ("gold" if is_passed
                     else "green" if n and l6 >= n else "blue"),
        })
    units.sort(key=lambda x: unit_no(x["key"]))
    return {"units": units, "total_words": len(words),
            "language": language}


# =====================================================================
#  BILDIRISHNOMALAR (2026-08-10, Jahongir: "o'ng burchakda
#  qo'ng'iroqcha - to'lov vaqti yetgani, imtihon natijasi chiqqani")
#
#  Alohida jadval YO'Q - xabarlar mavjud ma'lumotdan quriladi
#  (balans va imtihon natijalari), shuning uchun hech qachon
#  eskirmaydi va sinxronlash muammosi bo'lmaydi. "O'qildi" belgisi
#  mijozda saqlanadi (oxirgi ko'rilgan vaqt).
# =====================================================================

@router.get("/api/student/notifications")
def student_notifications(db: Session = Depends(get_db),
                          user=Depends(require_role(roles.STUDENT))):
    s = _me(db, user)
    items = []

    # 1) To'lov: balans manfiy bo'lsa - to'lov vaqti kelgan
    bal = student_balance(db, s.id)
    if bal < 0:
        items.append({
            "id": f"pay:{date.today().strftime('%Y-%m')}",
            "kind": "payment",
            "title": "To'lov vaqti keldi",
            "body": (f"Balansingiz: {int(bal):,} so'm. "
                     f"Administratorga to'lovni topshiring."
                     ).replace(",", " "),
            "date": date.today().isoformat(),
        })

    # 2) Imtihon natijalari (oxirgi 60 kun, tasdiqlanganlari)
    since = date.today() - timedelta(days=60)
    rows = (db.query(models.ExamResult, models.Exam)
            .join(models.Exam,
                  models.ExamResult.exam_id == models.Exam.id)
            .filter(models.ExamResult.student_id == s.id,
                    models.Exam.status.in_(["approved", "done"]),
                    models.Exam.date >= since)
            .order_by(models.Exam.date.desc()).limit(15).all())
    for er, ex in rows:
        title = ex.title or roles.exam_title(ex.kind, ex.unit_no)
        if er.absent:
            body = "Siz bu imtihonda qatnashmagansiz"
        elif er.band is not None:
            body = f"Natijangiz: band {er.band}"
        elif er.percent is not None:
            body = f"Natijangiz: {er.score or 0} ball ({round(er.percent)}%)"
        else:
            body = f"Natijangiz: {er.score or 0} ball"
        items.append({
            "id": f"exam:{er.id}",
            "kind": "exam",
            "title": f"Imtihon natijasi chiqdi: {title}",
            "body": body,
            "date": ex.date.isoformat() if ex.date else None,
        })

    items.sort(key=lambda x: x["date"] or "", reverse=True)
    return {"items": items,
            "latest": items[0]["date"] if items else None}


# =====================================================================
#  4 KO'NIKMA MASHQLARI (2026-08-10, Jahongir: "listening, reading,
#  writing, speaking mashqlari ham qo'shaylik")
#
#  Kontent qayerdan:
#   - listening: lug'at so'zlari va grammar jumlalarini brauzer TTS
#     o'qib beradi - diktant yoki tanlov (yangi kontent yozilmadi,
#     mavjud 4341 so'z + 300+ jumla ishlaydi);
#   - speaking: o'sha jumlalarni MIKROFONGA o'qib berish - brauzer
#     nutqni matnga aylantiradi, server solishtiradi;
#   - writing: grammar'ning "order" savollari - o'zbekcha ma'noni
#     INGLIZCHA YOZIB tarjima qilish;
#   - reading: reading_seed matnlari + tushunish savollari.
#  Ball: har ko'nikmada distinct to'g'ri mashq = 1 ball (skills
#  kartasidagi tegishli qatorga tushadi).
# =====================================================================

PRACTICE_SKILLS = ("listening", "reading", "writing", "speaking")
PRACTICE_ROUND = 8


def _norm_loose(t: str) -> str:
    t = (t or "").strip().lower()
    for ch in ".,!?;:'\u2019\u2018ʻ`-":
        t = t.replace(ch, " ")
    return " ".join(t.split())


def _word_overlap(a: str, b: str) -> float:
    """Speaking uchun: aytilgan matn nishonga qancha mos (0..1)."""
    wa, wb = _norm_loose(a).split(), _norm_loose(b).split()
    if not wa or not wb:
        return 0.0
    match = 0
    used = [False] * len(wa)
    for w in wb:
        for i, x in enumerate(wa):
            if not used[i] and x == w:
                used[i] = True
                match += 1
                break
    return match / max(len(wa), len(wb))


def _gram_sentences(db, limit=400):
    rows = (db.query(models.GrammarQuestion)
            .filter(models.GrammarQuestion.kind == "order",
                    models.GrammarQuestion.is_active == 1).all())
    return rows[:limit]


@router.get("/api/student/practice/{skill}/round")
def practice_round(skill: str, db: Session = Depends(get_db),
                   user=Depends(require_role(roles.STUDENT))):
    s = _me(db, user)
    if skill not in PRACTICE_SKILLS:
        raise HTTPException(404, "Bunday mashq yo'q")

    solved = {r for (r,) in
              db.query(func.distinct(models.SkillAttempt.ref))
              .filter(models.SkillAttempt.student_id == s.id,
                      models.SkillAttempt.skill == skill,
                      models.SkillAttempt.correct == 1).all()}

    def prefer_fresh(pool, key):
        fresh = [x for x in pool if key(x) not in solved]
        done = [x for x in pool if key(x) in solved]
        random.shuffle(fresh)
        random.shuffle(done)
        return fresh + done

    if skill == "reading":
        # Bitta matn + savollari. Avval yechilmagan savoli KO'PROQ
        # qolgan matn tanlanadi.
        texts = (db.query(models.ReadingText)
                 .filter(models.ReadingText.is_active == 1).all())
        if not texts:
            raise HTTPException(400, "Matnlar hali yuklanmagan")
        qs_by_text = {}
        for q in db.query(models.ReadingQuestion).all():
            qs_by_text.setdefault(q.text_id, []).append(q)
        texts.sort(key=lambda t: sum(
            1 for q in qs_by_text.get(t.id, [])
            if f"read:{q.id}" not in solved), reverse=True)
        tx = texts[0] if texts else None
        qs = qs_by_text.get(tx.id, [])
        return {
            "skill": skill,
            "text": {"title": tx.title, "level": tx.level,
                     "body": tx.body},
            "items": [{
                "ref": f"read:{q.id}", "kind": "read_mcq",
                "prompt": q.prompt,
                "options": _shuffled(json.loads(q.options)),
                "solved": f"read:{q.id}" in solved,
            } for q in qs],
        }

    if skill == "writing":
        pool = prefer_fresh(_gram_sentences(db),
                            lambda q: f"gram:{q.id}")
        items = [{
            "ref": f"gram:{q.id}", "kind": "write_translate",
            "prompt": q.prompt,          # o'zbekcha ma'no
            "words": len(json.loads(q.options)),
            "solved": f"gram:{q.id}" in solved,
        } for q in pool[:PRACTICE_ROUND]]
        return {"skill": skill, "items": items}

    if skill == "speaking":
        pool = prefer_fresh(_gram_sentences(db),
                            lambda q: f"gram:{q.id}")
        items = [{
            "ref": f"gram:{q.id}", "kind": "speak_read",
            "text": q.answer,            # ovoz chiqarib o'qiladi
            "solved": f"gram:{q.id}" in solved,
        } for q in pool[:PRACTICE_ROUND]]
        return {"skill": skill, "items": items}

    # listening: yarmi so'z (diktant yoki tanlov), yarmi jumla diktanti
    words = (db.query(models.VocabWord)
             .filter(models.VocabWord.is_active == 1).all()
             if hasattr(models.VocabWord, "is_active")
             else db.query(models.VocabWord).all())
    wpool = prefer_fresh(words, lambda w: f"word:{w.id}")
    spool = prefer_fresh(_gram_sentences(db),
                         lambda q: f"gram:{q.id}")
    items = []
    for w in wpool[:PRACTICE_ROUND // 2]:
        if len(items) % 2 == 0:
            items.append({
                "ref": f"word:{w.id}", "kind": "listen_type",
                "say": w.word, "solved": f"word:{w.id}" in solved,
            })
        else:
            wrong = random.sample(
                [x.translation for x in words
                 if x.id != w.id and x.translation], 3)                 if len(words) > 4 else []
            opts = wrong + [w.translation]
            random.shuffle(opts)
            items.append({
                "ref": f"word:{w.id}", "kind": "listen_choice",
                "say": w.word, "options": opts,
                "solved": f"word:{w.id}" in solved,
            })
    for q in spool[:PRACTICE_ROUND - len(items)]:
        items.append({
            "ref": f"gram:{q.id}", "kind": "listen_dictation",
            "say": q.answer, "solved": f"gram:{q.id}" in solved,
        })
    random.shuffle(items)
    return {"skill": skill, "items": items}


def _shuffled(lst):
    out = lst[:]
    random.shuffle(out)
    return out


@router.post("/api/student/practice/answer")
def practice_answer(payload: schemas.PracticeAnswerIn,
                    db: Session = Depends(get_db),
                    user=Depends(require_role(roles.STUDENT))):
    """Tekshiruv FAQAT serverda - ref manbadan qayta o'qiladi."""
    s = _me(db, user)
    skill = payload.skill
    if skill not in PRACTICE_SKILLS:
        raise HTTPException(404, "Bunday mashq yo'q")
    kind, _, sid = payload.ref.partition(":")
    if not sid.isdigit():
        raise HTTPException(400, "Noto'g'ri mashq kaliti")
    sid = int(sid)

    expected, explain = None, None
    if kind == "word":
        w = db.query(models.VocabWord).get(sid)
        if not w:
            raise HTTPException(404, "So'z topilmadi")
        given = _norm_loose(payload.answer)
        ok = given in (_norm_loose(w.word), _norm_loose(w.translation))
        expected = w.word + " — " + (w.translation or "")
    elif kind == "gram":
        q = db.query(models.GrammarQuestion).get(sid)
        if not q:
            raise HTTPException(404, "Mashq topilmadi")
        expected = q.answer
        if skill == "speaking":
            ok = _word_overlap(q.answer, payload.answer) >= 0.75
        else:
            ok = _norm_loose(payload.answer) == _norm_loose(q.answer)
    elif kind == "read":
        q = db.query(models.ReadingQuestion).get(sid)
        if not q:
            raise HTTPException(404, "Savol topilmadi")
        ok = (payload.answer or "").strip() == q.answer.strip()
        expected, explain = q.answer, q.explain
    else:
        raise HTTPException(400, "Noto'g'ri mashq kaliti")

    was = (db.query(models.SkillAttempt.id)
           .filter(models.SkillAttempt.student_id == s.id,
                   models.SkillAttempt.skill == skill,
                   models.SkillAttempt.ref == payload.ref,
                   models.SkillAttempt.correct == 1)
           .first() is not None)
    db.add(models.SkillAttempt(
        student_id=s.id, skill=skill, ref=payload.ref,
        correct=1 if ok else 0,
        answer=(payload.answer or "")[:300], date=date.today()))
    db.commit()

    xp_given = 0.0
    if ok and not was:
        try:
            res = award_xp(
                db, student_id=s.id, event_code="PRACTICE_CORRECT",
                amount=roles.GRAMMAR_XP_PER_CORRECT,
                source_type=f"practice_{skill}", source_id=sid,
                reason=f"{skill.capitalize()} mashqi",
                idempotency_key=f"PRACT:{skill}:{s.id}:{payload.ref}")
            if res.get("ok"):
                xp_given = float(roles.GRAMMAR_XP_PER_CORRECT)
        except Exception:
            db.rollback()

    return {"correct": ok, "expected": expected, "explain": explain,
            "first_time": ok and not was, "xp": xp_given}


# =====================================================================
#  GRAMMAR MASHQLARI (2026-08-10, Jahongir: "Grammar har bir ingliz
#  tilidagi mavzuga xilma-xil mashqlar bo'lsin")
# =====================================================================

@router.get("/api/student/grammar/topics")
def grammar_topics(db: Session = Depends(get_db),
                   user=Depends(require_role(roles.STUDENT))):
    """A1 dasturi (Jahongir bergan tartibda) + A2 qulfi.

    Qoida (2026-08-11): "Avval A1 ni tugatgandan keyin A2 ochilsin,
    A2 mavzulari umuman ko'rinmasin, faqat qulf bo'lib tursin.
    A1 tugaganda A1 yopiladi (yig'ilib turadi), xohlasa ochib eski
    mavzularni ishlayveradi." Mavzu "yopildi" = hamma savoli kamida
    bir marta to'g'ri yechildi."""
    s = _me(db, user)
    qs = (db.query(models.GrammarQuestion)
          .filter(models.GrammarQuestion.is_active == 1)
          .order_by(models.GrammarQuestion.topic_order,
                    models.GrammarQuestion.id).all())
    solved = {qid for (qid,) in
              db.query(func.distinct(models.GrammarAttempt.question_id))
              .filter(models.GrammarAttempt.student_id == s.id,
                      models.GrammarAttempt.correct == 1).all()}

    def build(level):
        topics = {}
        for q in qs:
            if q.level != level:
                continue
            t = topics.setdefault(q.topic, {
                "topic": q.topic, "order": q.topic_order,
                "boss": bool(q.is_boss), "total": 0, "solved": 0,
            })
            t["total"] += 1
            if q.id in solved:
                t["solved"] += 1
        out = sorted(topics.values(), key=lambda x: x["order"])
        for t in out:
            t["percent"] = round(t["solved"] * 100 / t["total"]) \
                if t["total"] else 0
            t["done"] = t["total"] > 0 and t["solved"] >= t["total"]
        return out

    a1 = build("A1")
    a1_completed = bool(a1) and all(t["done"] for t in a1)
    a2 = build("A2") if a1_completed else []

    return {
        "a1": {"topics": a1,
               "done": sum(1 for t in a1 if t["done"]),
               "total": len(a1),
               "completed": a1_completed},
        "a2_locked": not a1_completed,
        "a2": {"topics": a2, "ready": len(a2) > 0},
        "total_correct": len(solved),
        "round_size": roles.GRAMMAR_ROUND_SIZE,
        # eski UI mosligi uchun
        "levels": [{"level": "A1", "topics": a1}]
                  + ([{"level": "A2", "topics": a2}] if a2 else []),
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
