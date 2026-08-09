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
    if payload.game == "uz_en" or payload.game == "spelling":
        expected = (w.word or "").strip().lower()
    elif payload.game == "flashcard":
        # Kartochkada o'quvchi o'zini o'zi baholaydi ("bildim"/"bilmadim")
        expected = "bildim"
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
        "expected": (w.word if payload.game in ("uz_en", "spelling")
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
