"""DARS REJALARI + JONLI O'YIN (Kahoot uslubi), 2026-09-18.

Jahongir: "saytgayam qoy va grammar ham vocabularyga kahoot
korinishidagi oyinlar ham qosh link bilan QR kod bilan live oynasa
boladigan qilib hamma togri topgan bilan kim tez bossa shu oldinga
chiqadigan achkoni koproq beradigan bolsin kahoot tizimi har bir
unitda".

Ikki qism:
  1. /api/plans — IELTS dars rejalari (api/plans_data/*.json —
     ustozlar uchun tayyorlangan 28 darsning to'liq matni).
  2. /api/live/... — jonli viktorina. Ustoz o'yin ochadi (PIN + QR),
     o'quvchilar telefondan LOGINSIZ kiradi (ism yozadi), savollar
     dars lug'ati va grammatikasidan AVTOMAT tuziladi. Ball: to'g'ri
     javob 500..1000 (tezroq bosgan ko'proq oladi) + ketma-ket
     to'g'ri javob bonusi. Vercel'da websocket yo'q — mijoz 1–1.5
     soniyada holatni so'rab turadi (polling).
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
import random
import re
import secrets
from datetime import datetime
from functools import lru_cache
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

import models
import roles
from auth import require_role
from database import get_db
from me import is_english_teacher
from common import (_get_group_in_scope, _group_students, _sync_coin_entry,
                    _teacher_owns, scope_to_branch)

router = APIRouter()

_PLANS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plans_data")


# ---------------------------------------------------------------
#  DARS REJALARI (JSON)
# ---------------------------------------------------------------
@lru_cache(maxsize=8)
def _load_course(course: str) -> Optional[dict]:
    if not re.fullmatch(r"[a-z0-9_]+", course or ""):
        return None
    path = os.path.join(_PLANS_DIR, course + ".json")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _lesson(course: str, no: int) -> dict:
    if course.startswith("outline_"):
        raise HTTPException(404, "Kurs topilmadi")
    d = _load_course(course)
    if not d:
        raise HTTPException(404, "Bu darajaning rejasi hali tayyorlanmoqda")
    for L in d["lessons"]:
        if int(L["no"]) == int(no):
            return L
    raise HTTPException(404, "Dars topilmadi")


def _summary(L: dict) -> dict:
    V = L.get("vocab") or {}
    return {
        "no": L["no"], "title": L["title"],
        "grammar_topic": L.get("grammar_topic"),
        "vocab_topic": L.get("vocab_topic"),
        "test_after": L.get("test_after") or "",
        "audios": (L.get("listening") or {}).get("audios") or "",
        "reading": bool(L.get("reading")),
        "words": sum(len(V.get(t) or []) for t in ("core", "strong", "super")),
    }


# DARAJALAR RO'YXATI (2026-09-18, Jahongir: "IELTS 1.0 (A1) IELTS 2.0
# (A2) qilib darajalarni ber ... IELTS 1.0 DAN 7.0 gacha bo'lishi
# kerak"). To'liq reja bor daraja — ielts_X_Y.json; faqat mavzular
# ro'yxati bor daraja — outline_ielts_X_Y.json (xlsx dan); qolganlari
# hozircha bo'sh ("tayyorlanmoqda").
LEVELS = [
    ("ielts_1_0", "IELTS 1.0", "A1"),
    ("ielts_2_0", "IELTS 2.0", "A2"),
    ("ielts_3_0", "IELTS 3.0", "B1"),
    ("ielts_4_0", "IELTS 4.0", "B1+"),
    # 2026-09-18, Jahongir: "IELTS 5.0 leveli yoniga - qib turib IELTS
    # INTRODUCTION ... keyingisiga IELTS FOUNDATION ... IELTS GRADUATION"
    ("ielts_5_0", "IELTS 5.0 - IELTS INTRODUCTION", "B2"),
    ("ielts_6_0", "IELTS 6.0 - IELTS FOUNDATION", "B2+"),
    ("ielts_7_0", "IELTS 7.0 - IELTS GRADUATION", "C1"),
]


def _level(course: str, title: str, cefr: str) -> dict:
    """To'liq reja (ielts_X.json) + mavzular ro'yxati (outline_*.json)
    birlashtiriladi: tayyor darslar 'ready', qolganlari faqat mavzu.
    Shunda 2.0 darslari tayyor bo'lgani sari saytga chiqadi (2026-09-18)."""
    full = _load_course(course) or {"lessons": []}
    outline = _load_course("outline_" + course) or {"lessons": []}
    ready = {int(L["no"]): dict(_summary(L), ready=True) for L in full["lessons"]}
    lessons = []
    seen = set()
    for L in outline["lessons"]:
        no = int(L["no"])
        lessons.append(ready.get(no) or dict(L, ready=False))
        seen.add(no)
    for no in sorted(ready):
        if no not in seen:
            lessons.append(ready[no])
    lessons.sort(key=lambda L: int(L["no"]))
    return {"course": course, "title": title, "cefr": cefr,
            "ready": bool(lessons) and all(L.get("ready") for L in lessons),
            "lessons": lessons, "ready_count": len(ready)}


def _english_only(db, user):
    """Dars rejalari BARCHA ustozlarga ochiq (2026-09-18, Jahongir:
    "Hammasiga ochilaversin rus til ingliz qilib otirmasdan ustozmi
    hammasiga ochilsin"). Fan bo'yicha cheklov olib tashlandi; rol
    cheklovi (TEACHING_ACCESS) endpoint'da qoladi."""
    return None


@router.get("/api/plans")
def list_plans(db: Session = Depends(get_db),
               user=Depends(require_role(*roles.PLANS_ACCESS))):
    _english_only(db, user)
    return [_level(c, t, cefr) for c, t, cefr in LEVELS]


_MEDIA_DIR = os.path.join(_PLANS_DIR, "media")


@router.get("/api/plan-media/{name}")
def plan_media(name: str, db: Session = Depends(get_db),
               user=Depends(require_role(*roles.PLANS_ACCESS))):
    """Dars rejasiga biriktirilgan material (ustoz bergan reading
    hujjati rasmi va h.k., 2026-09-21). Faqat tizimga kirgan va dars
    rejalariga ruxsati bor xodimga beriladi — ochiq havola emas."""
    from fastapi.responses import FileResponse
    if not re.fullmatch(r"[a-z0-9_]+\.(jpg|png|pdf)", name or ""):
        raise HTTPException(404, "Topilmadi")
    path = os.path.join(_MEDIA_DIR, name)
    if not os.path.exists(path):
        raise HTTPException(404, "Topilmadi")
    kind = {"jpg": "image/jpeg", "png": "image/png", "pdf": "application/pdf"}[name.rsplit(".", 1)[1]]
    return FileResponse(path, media_type=kind,
                        headers={"Cache-Control": "private, max-age=86400"})


@router.get("/api/plans/{course}/{no}")
def get_plan(course: str, no: int, db: Session = Depends(get_db),
             user=Depends(require_role(*roles.PLANS_ACCESS))):
    _english_only(db, user)
    return _lesson(course, no)


# ---------------------------------------------------------------
#  SAVOL TUZISH — dars lug'ati va grammatikasidan
# ---------------------------------------------------------------
def _head(word: str) -> str:
    """'understand – understood – understood' -> 'understand'."""
    return re.split(r"\s+[–-]\s+", word)[0].strip()


def _pick_distractors(rnd, pool, correct, n=3):
    cands = []
    seen = {correct.strip().lower()}
    for x in pool:
        k = (x or "").strip().lower()
        if k and k not in seen:
            seen.add(k)
            cands.append(x)
    if len(cands) < n:
        return None
    return rnd.sample(cands, n)


def _mk(rnd, kind, prompt, correct, distractors, explain=None, sub=None):
    opts = [correct] + list(distractors)
    rnd.shuffle(opts)
    return {"kind": kind, "prompt": prompt, "options": opts,
            "correct": opts.index(correct), "explain": explain, "sub": sub}


def _vocab_questions(rnd, entries) -> list:
    """Har so'z uchun 3 xil savol (tarjima, inglizchasi, gapdagi bo'sh joy)
    — avval har so'zdan bittadan, keyin ikkinchi turi... Shunda 20 so'zdan
    kamida 20 (kerak bo'lsa 40–60) savol chiqadi."""
    words = [_head(e[0]) for e in entries]
    uzs = [e[1] for e in entries]
    per_word = []
    for e in entries:
        w, uz = _head(e[0]), e[1]
        ex, ex_uz = (e[2] if len(e) > 2 else ""), (e[3] if len(e) > 3 else "")
        variants = []
        d = _pick_distractors(rnd, uzs, uz)
        if d:
            variants.append(_mk(rnd, "vocab", f"«{w}» — tarjimasi?", uz, d))
        d = _pick_distractors(rnd, words, w)
        if d:
            variants.append(_mk(rnd, "vocab", f"«{uz}» — inglizchasi?", w, d))
        if ex and re.search(r"\b" + re.escape(w) + r"\b", ex, re.I):
            d = _pick_distractors(rnd, words, w)
            if d:
                gap = re.sub(r"\b" + re.escape(w) + r"\b", "_____", ex, count=1, flags=re.I)
                variants.append(_mk(rnd, "vocab", gap, w, d, sub=ex_uz or None))
        rnd.shuffle(variants)
        per_word.append(variants)
    out = []
    for round_no in range(3):
        layer = [v[round_no] for v in per_word if len(v) > round_no]
        rnd.shuffle(layer)
        out.extend(layer)
    return out


def _grammar_questions(rnd, L) -> list:
    out = []
    G = L.get("grammar") or {}
    mistakes = [m for m in (G.get("mistakes") or []) if len(m) >= 2]
    wrongs = [m[0] for m in mistakes]
    for m in mistakes:
        d = _pick_distractors(rnd, wrongs, m[1])
        if d:
            out.append(_mk(rnd, "grammar", "Qaysi gap TO'G'RI?", m[1], d,
                           explain=(m[2] if len(m) > 2 else None)))
    for ex in (L.get("class_ex") or []) + (L.get("homework") or []):
        items, answers = ex.get("items"), ex.get("answers")
        if not (isinstance(items, list) and isinstance(answers, list)
                and len(items) == len(answers)):
            continue
        if not all(isinstance(a, str) for a in answers):
            continue
        good = [(i, a) for i, a in zip(items, answers)
                if 0 < len(a) <= 45 and "/" not in a and "(" not in a
                and isinstance(i, str) and len(i) <= 160]
        if len(good) < 4:
            continue
        pool = [a for _, a in good]
        for item, ans in good:
            d = _pick_distractors(rnd, pool, ans)
            if d:
                out.append(_mk(rnd, "grammar", item, ans, d, sub=ex.get("title")))
    return out


def build_questions(L: dict, mode: str, count: int, seed=None) -> list:
    rnd = random.Random(seed)
    V = L.get("vocab") or {}
    core = V.get("core") or []
    strong = V.get("strong") or []
    voc, gram = [], []
    if mode in ("vocab", "mixed"):
        voc = _vocab_questions(rnd, core)
    elif mode == "vocab40":
        voc = _vocab_questions(rnd, core + strong)
    if mode in ("grammar", "mixed"):
        gram = _grammar_questions(rnd, L)
    rnd.shuffle(gram)
    if mode == "mixed":
        half = count // 2
        g_part = gram[:half]
        qs = g_part + voc[:count - len(g_part)]
        rnd.shuffle(qs)
    else:
        qs = (voc or gram)[:count]
    if not qs:
        raise HTTPException(400, "Bu dars uchun savol tuzib bo'lmadi")
    return qs


# ---------------------------------------------------------------
#  JONLI O'YIN
# ---------------------------------------------------------------
MODES = {"vocab": "Lug'at (CORE 20)", "vocab40": "Lug'at (40 so'z)",
         "grammar": "Grammatika", "mixed": "Aralash"}


class GameIn(BaseModel):
    course: str
    lesson_no: int
    group_id: Optional[int] = None   # ustoz O'Z guruhini tanlaydi (coin uchun)
    mode: str = "mixed"
    count: int = 20            # kamida 20 savol (Jahongir)
    seconds: int = 20


class JoinIn(BaseModel):
    code: str
    nickname: Optional[str] = None
    student_id: Optional[int] = None   # ro'yxatdan tanlangan o'quvchi


class AnswerIn(BaseModel):
    q_index: int
    option: int


def _now():
    return datetime.utcnow()


def _new_code(db) -> str:
    for _ in range(50):
        code = "".join(secrets.choice("0123456789") for _ in range(6))
        busy = db.query(models.LiveGame).filter(
            models.LiveGame.code == code,
            models.LiveGame.status != "ended").first()
        if not busy:
            return code
    raise HTTPException(500, "PIN topilmadi")


def _qs(g) -> list:
    return json.loads(g.questions or "[]")


def _public_q(q: dict, i: int, total: int, secs: int) -> dict:
    return {"index": i, "total": total, "kind": q["kind"], "prompt": q["prompt"],
            "sub": q.get("sub"), "options": q["options"], "seconds": secs}


def _elapsed_ms(g) -> int:
    if not g.q_started_at:
        return 0
    return int((_now() - g.q_started_at).total_seconds() * 1000)


def _points(ms: int, secs: int, streak: int) -> int:
    """Tez bosgan ko'proq oladi: 1000 (darhol) ... 500 (oxirgi soniya).
    Ketma-ket 3+ to'g'ri javob — +100 bonus."""
    T = max(1, secs) * 1000
    frac = min(max(ms, 0), T) / T
    base = 500 + round(500 * (1 - frac))
    return base + (100 if streak >= 3 else 0)


def _leaderboard(db, g, limit=None) -> list:
    ps = db.query(models.LivePlayer).filter(
        models.LivePlayer.game_id == g.id).all()
    ps.sort(key=lambda p: (-(p.score or 0), p.joined_at or _now()))
    rows = [{"id": p.id, "nickname": p.nickname, "score": p.score or 0,
             "rank": i + 1, "student_id": p.student_id,
             "coins": p.coins or 0, "correct": p.correct_count or 0}
            for i, p in enumerate(ps)]
    return rows[:limit] if limit else rows


def _game_or_404(db, gid: int, user):
    g = db.query(models.LiveGame).filter(models.LiveGame.id == gid).first()
    if not g:
        raise HTTPException(404, "O'yin topilmadi")
    if g.host_user_id != user.id and user.role not in roles.FULL_ACCESS:
        raise HTTPException(403, "Bu o'yin sizniki emas")
    return g


@router.post("/api/live/games")
def create_game(body: GameIn, db: Session = Depends(get_db),
                user=Depends(require_role(*roles.TEACHING_ACCESS))):
    _english_only(db, user)
    if body.mode not in MODES:
        raise HTTPException(400, "Rejim noto'g'ri")
    L = _lesson(body.course, body.lesson_no)
    # Eski (keshlangan) sahifa guruhsiz yuborsa — 422 o'rniga tushunarli xabar
    if not body.group_id:
        raise HTTPException(400, "Guruhni tanlang (sahifani yangilang — Ctrl+F5)")
    group = _get_group_in_scope(db, body.group_id, user)
    # Kamida 20 savol (2026-09-18, Jahongir: "savollar soni kamida 20ta
    # bo'lishi kerak"). Dars shuncha savol bermasa — lug'atning 40
    # so'zli ro'yxatidan to'ldiriladi.
    count = max(20, min(60, int(body.count or 20)))
    secs = max(5, min(90, int(body.seconds or 20)))
    qs = build_questions(L, body.mode, count)
    if len(qs) < count and body.mode != "vocab40":
        extra = build_questions(L, "vocab40", count)
        seen = {q["prompt"] for q in qs}
        qs += [q for q in extra if q["prompt"] not in seen][:count - len(qs)]
    if len(qs) < 20:
        raise HTTPException(400, "Bu dars uchun 20 ta savol tuzib bo'lmadi")
    g = models.LiveGame(
        code=_new_code(db), course=body.course, lesson_no=body.lesson_no,
        group_id=group.id,
        mode=body.mode, title=f"Dars {L['no']} — {L['title']}",
        questions=json.dumps(qs, ensure_ascii=False), question_seconds=secs,
        status="lobby", q_index=-1, host_user_id=user.id,
        branch_id=getattr(user, "branch_id", None), created_at=_now(),
    )
    db.add(g)
    db.commit()
    db.refresh(g)
    return _host_state(db, g)


@router.get("/api/live/groups")
def my_groups(db: Session = Depends(get_db),
              user=Depends(require_role(*roles.TEACHING_ACCESS))):
    """O'yin ochishda tanlash uchun guruhlar: ustoz — faqat o'z
    guruhlari, rahbariyat — filialdagi hammasi. Har guruh bilan
    o'quvchilar ro'yxati (ism tanlash uchun)."""
    q = scope_to_branch(db.query(models.Group), models.Group, user)
    out = []
    for grp in q.order_by(models.Group.name).all():
        if user.role in tuple(roles.OWN_GROUPS_ONLY) and not _teacher_owns(db, grp, user):
            continue
        studs = [st for st in _group_students(db, grp.id)
                 if (st.status or "active") in ("active", "trial")]
        out.append({"id": grp.id, "name": grp.name,
                    "students": [{"id": st.id, "name": st.full_name} for st in studs]})
    return out


@router.get("/api/live/games")
def my_games(db: Session = Depends(get_db),
             user=Depends(require_role(*roles.TEACHING_ACCESS))):
    rows = db.query(models.LiveGame).filter(
        models.LiveGame.host_user_id == user.id
    ).order_by(models.LiveGame.id.desc()).limit(20).all()
    out = []
    for g in rows:
        n = db.query(models.LivePlayer).filter(
            models.LivePlayer.game_id == g.id).count()
        out.append({"id": g.id, "code": g.code, "title": g.title, "mode": g.mode,
                    "mode_label": MODES.get(g.mode, g.mode), "status": g.status,
                    "players": n, "questions": len(_qs(g)),
                    "created_at": g.created_at.isoformat() if g.created_at else None})
    return out


def _host_state(db, g) -> dict:
    qs = _qs(g)
    i = g.q_index if g.q_index is not None else -1
    cur = qs[i] if 0 <= i < len(qs) else None
    counts = [0] * (len(cur["options"]) if cur else 0)
    answered = 0
    if cur:
        for a in db.query(models.LiveAnswer).filter(
                models.LiveAnswer.game_id == g.id,
                models.LiveAnswer.q_index == i).all():
            answered += 1
            if 0 <= (a.option_index or 0) < len(counts):
                counts[a.option_index] += 1
    grp = db.query(models.Group).get(g.group_id) if g.group_id else None
    return {
        "id": g.id, "code": g.code, "title": g.title, "mode": g.mode,
        "group": grp.name if grp else None, "group_id": g.group_id,
        "exam_id": g.exam_id,
        "mode_label": MODES.get(g.mode, g.mode), "status": g.status,
        "q_index": i, "total": len(qs), "seconds": g.question_seconds,
        "elapsed_ms": _elapsed_ms(g) if g.status == "question" else None,
        "question": _public_q(cur, i, len(qs), g.question_seconds) if cur else None,
        "correct": cur["correct"] if (cur and g.status in ("reveal", "ended")) else None,
        "explain": cur.get("explain") if (cur and g.status in ("reveal", "ended")) else None,
        "counts": counts, "answered": answered,
        "players": _leaderboard(db, g),
    }


@router.get("/api/live/games/{gid}/host")
def host_state(gid: int, db: Session = Depends(get_db),
               user=Depends(require_role(*roles.TEACHING_ACCESS))):
    return _host_state(db, _game_or_404(db, gid, user))


@router.post("/api/live/games/{gid}/next")
def next_step(gid: int, db: Session = Depends(get_db),
              user=Depends(require_role(*roles.TEACHING_ACCESS))):
    """lobby -> 1-savol; question -> reveal; reveal -> keyingi savol
    yoki ended."""
    g = _game_or_404(db, gid, user)
    qs = _qs(g)
    if g.status == "lobby":
        g.q_index, g.status, g.q_started_at = 0, "question", _now()
    elif g.status == "question":
        g.status = "reveal"
    elif g.status == "reveal":
        if g.q_index + 1 >= len(qs):
            g.status, g.ended_at = "ended", _now()
            _finalize(db, g, user)
        else:
            g.q_index += 1
            g.status, g.q_started_at = "question", _now()
    db.commit()
    return _host_state(db, g)


def _finalize(db, g, user) -> None:
    """O'yin tugagach: natija IMTIHONLAR bo'limiga (kind="kahoot") yoziladi
    va coin AVTOMAT beriladi (2026-09-18, Jahongir): 100% to'g'ri —
    hammaga 3 coin; 1-o'rin +3, 2-o'rin +2, 3-o'rin +1. Faqat ro'yxatdan
    tanlangan (student_id bor) o'quvchilar; bir marta."""
    if g.exam_id or not g.group_id:
        return
    qs = _qs(g)
    total = len(qs)
    board = _leaderboard(db, g)
    players = {p.id: p for p in db.query(models.LivePlayer).filter(
        models.LivePlayer.game_id == g.id).all()}
    correct_by = {}
    for a in db.query(models.LiveAnswer).filter(models.LiveAnswer.game_id == g.id).all():
        if a.correct:
            correct_by[a.player_id] = correct_by.get(a.player_id, 0) + 1
    exam = models.Exam(group_id=g.group_id, kind="kahoot", title=f"Kahoot: {g.title}",
                       date=datetime.utcnow().date(), max_score=float(total),
                       status="done", created_by=user.full_name,
                       note=f"Jonli o'yin, {total} savol, {len(board)} o'yinchi")
    db.add(exam)
    db.flush()
    place_bonus = {1: 3, 2: 2, 3: 1}
    used_students = set()
    for row in board:
        p = players.get(row["id"])
        if not p:
            continue
        p.correct_count = correct_by.get(p.id, 0)
        if not p.student_id or p.student_id in used_students:
            continue
        used_students.add(p.student_id)
        pct = round(100.0 * p.correct_count / total, 1) if total else 0.0
        coins = (3 if p.correct_count == total and total > 0 else 0) + place_bonus.get(row["rank"], 0)
        p.coins = coins
        res = models.ExamResult(exam_id=exam.id, student_id=p.student_id,
                                score=float(p.correct_count), percent=pct, coins=coins,
                                note=f"{row['rank']}-o'rin, {row['score']} ball")
        db.add(res)
        db.flush()
        if coins:
            parts = []
            if p.correct_count == total:
                parts.append("100% to'g'ri +3")
            if row["rank"] in place_bonus:
                parts.append(f"{row['rank']}-o'rin +{place_bonus[row['rank']]}")
            _sync_coin_entry(db, student_id=p.student_id, source="kahoot", ref_id=res.id,
                             amount=coins, note=f"Kahoot: {g.title} ({', '.join(parts)})",
                             created_by=user.full_name)
    g.exam_id = exam.id
    db.commit()


@router.post("/api/live/games/{gid}/end")
def end_game(gid: int, db: Session = Depends(get_db),
             user=Depends(require_role(*roles.TEACHING_ACCESS))):
    g = _game_or_404(db, gid, user)
    if g.status != "ended":
        g.status, g.ended_at = "ended", _now()
        _finalize(db, g, user)
    db.commit()
    return _host_state(db, g)


# ---- O'quvchi tomoni (loginsiz) ---------------------------------
def _open_game(db, code: str):
    code = re.sub(r"\D", "", code or "")
    g = db.query(models.LiveGame).filter(models.LiveGame.code == code,
                                         models.LiveGame.status != "ended").first()
    if not g:
        raise HTTPException(404, "Bunday PIN bilan o'yin topilmadi")
    return g


@router.get("/api/live/lobby/{code}")
def lobby(code: str, db: Session = Depends(get_db)):
    """Kirishdan oldin: guruh o'quvchilari ro'yxati — o'quvchi o'z ismini
    tanlaydi (ro'yxatda bo'lmasa — o'zi yozadi). Loginsiz."""
    g = _open_game(db, code)
    taken = {p.student_id for p in db.query(models.LivePlayer).filter(
        models.LivePlayer.game_id == g.id).all() if p.student_id}
    studs = _group_students(db, g.group_id) if g.group_id else []
    grp = db.query(models.Group).get(g.group_id) if g.group_id else None
    return {"title": g.title, "status": g.status, "group": grp.name if grp else None,
            "students": [{"id": st.id, "name": st.full_name, "taken": st.id in taken}
                         for st in studs if (st.status or "active") in ("active", "trial")]}


def _reconnect(db, g, p):
    """O'yin davomida chiqib ketib qayta kirgan o'quvchi (2026-09-18,
    Jahongir: "chiqib ketib boshqattan kirganda savolga javob avtomat
    xato bo'lsin"): yangi token beriladi, joriy savolga javob bermagan
    bo'lsa — XATO deb yoziladi (0 ball), ketma-ketlik uziladi."""
    p.token = secrets.token_urlsafe(18)
    p.streak = 0
    i = g.q_index if g.q_index is not None else -1
    if g.status in ("question", "reveal") and i >= 0:
        has = db.query(models.LiveAnswer).filter(models.LiveAnswer.player_id == p.id,
                                                 models.LiveAnswer.q_index == i).first()
        if not has:
            db.add(models.LiveAnswer(game_id=g.id, player_id=p.id, q_index=i, option_index=-1,
                                     correct=0, ms=_elapsed_ms(g), points=0, created_at=_now()))
    db.commit()
    return {"token": p.token, "game_id": g.id, "title": g.title, "nickname": p.nickname,
            "reconnected": True}


@router.post("/api/live/join")
def join(body: JoinIn, db: Session = Depends(get_db)):
    g = _open_game(db, body.code)
    if g.status != "lobby":
        # Boshlangan o'yinga faqat avval kirgan o'yinchi qaytadi
        q = db.query(models.LivePlayer).filter(models.LivePlayer.game_id == g.id)
        if body.student_id:
            p = q.filter(models.LivePlayer.student_id == body.student_id).first()
        else:
            nick = re.sub(r"\s+", " ", (body.nickname or "").strip())
            p = q.filter(models.LivePlayer.nickname.ilike(nick)).first() if nick else None
        if not p:
            raise HTTPException(400, "O'yin allaqachon boshlangan")
        return _reconnect(db, g, p)
    student_id = None
    if body.student_id:
        st = db.query(models.Student).filter(models.Student.id == body.student_id,
                                             models.Student.group_id == g.group_id).first()
        if not st:
            raise HTTPException(400, "Bu o'quvchi guruhda yo'q")
        dup = db.query(models.LivePlayer).filter(models.LivePlayer.game_id == g.id,
                                                 models.LivePlayer.student_id == st.id).first()
        if dup:
            raise HTTPException(400, "Bu ism allaqachon tanlangan")
        nick, student_id = st.full_name[:40], st.id
    else:
        nick = re.sub(r"\s+", " ", (body.nickname or "").strip())[:24]
        if len(nick) < 2:
            raise HTTPException(400, "Ismingizni yozing")
        taken = db.query(models.LivePlayer).filter(
            models.LivePlayer.game_id == g.id,
            models.LivePlayer.nickname.ilike(nick)).first()
        if taken:
            raise HTTPException(400, "Bu ism band — boshqasini yozing")
    p = models.LivePlayer(game_id=g.id, nickname=nick, student_id=student_id,
                          token=secrets.token_urlsafe(18),
                          score=0, streak=0, joined_at=_now())
    db.add(p)
    db.commit()
    return {"token": p.token, "game_id": g.id, "title": g.title, "nickname": nick}


def _player_or_404(db, token: str):
    p = db.query(models.LivePlayer).filter(models.LivePlayer.token == token).first()
    if not p:
        raise HTTPException(404, "O'yinchi topilmadi")
    g = db.query(models.LiveGame).filter(models.LiveGame.id == p.game_id).first()
    if not g:
        raise HTTPException(404, "O'yin topilmadi")
    return p, g


@router.get("/api/live/p/{token}")
def player_state(token: str, db: Session = Depends(get_db)):
    p, g = _player_or_404(db, token)
    qs = _qs(g)
    i = g.q_index if g.q_index is not None else -1
    cur = qs[i] if 0 <= i < len(qs) else None
    board = _leaderboard(db, g)
    me = next((r for r in board if r["id"] == p.id), None)
    out = {"status": g.status, "title": g.title, "nickname": p.nickname,
           "score": p.score or 0, "rank": me["rank"] if me else None,
           "players": len(board), "q_index": i, "total": len(qs)}
    if g.status == "question" and cur:
        a = db.query(models.LiveAnswer).filter(
            models.LiveAnswer.player_id == p.id,
            models.LiveAnswer.q_index == i).first()
        out["question"] = _public_q(cur, i, len(qs), g.question_seconds)
        out["elapsed_ms"] = _elapsed_ms(g)
        out["answered"] = a.option_index if a else None
    elif g.status in ("reveal", "ended") and cur:
        a = db.query(models.LiveAnswer).filter(
            models.LiveAnswer.player_id == p.id,
            models.LiveAnswer.q_index == i).first()
        out["reveal"] = {
            "prompt": cur["prompt"], "options": cur["options"],
            "correct": cur["correct"], "explain": cur.get("explain"),
            "my_option": a.option_index if a else None,
            "is_correct": bool(a and a.correct),
            "points": (a.points or 0) if a else 0,
        }
        out["top"] = board[:5]
    if g.status == "ended":
        out["top"] = board[:10]
        out["coins"] = p.coins or 0
        out["correct"] = p.correct_count or 0
        out["linked"] = bool(p.student_id)
    return out


@router.post("/api/live/p/{token}/answer")
def answer(token: str, body: AnswerIn, db: Session = Depends(get_db)):
    p, g = _player_or_404(db, token)
    qs = _qs(g)
    i = g.q_index if g.q_index is not None else -1
    if g.status != "question" or body.q_index != i or not (0 <= i < len(qs)):
        raise HTTPException(400, "Bu savol yopilgan")
    cur = qs[i]
    if not (0 <= body.option < len(cur["options"])):
        raise HTTPException(400, "Variant noto'g'ri")
    dup = db.query(models.LiveAnswer).filter(
        models.LiveAnswer.player_id == p.id, models.LiveAnswer.q_index == i).first()
    if dup:
        raise HTTPException(400, "Javob allaqachon berilgan")
    ms = _elapsed_ms(g)
    # 1.5 soniya "imtiyoz": tarmoq kechikishi uchun. Undan kech kelgan
    # javob qabul qilinadi, lekin ball bermaydi.
    late = ms > g.question_seconds * 1000 + 1500
    correct = 1 if (body.option == cur["correct"] and not late) else 0
    if correct:
        p.streak = (p.streak or 0) + 1
        pts = _points(ms, g.question_seconds, p.streak)
    else:
        p.streak = 0
        pts = 0
    p.score = (p.score or 0) + pts
    db.add(models.LiveAnswer(game_id=g.id, player_id=p.id, q_index=i,
                             option_index=body.option, correct=correct,
                             ms=ms, points=pts, created_at=_now()))
    db.commit()
    return {"ok": True, "points": pts, "correct": bool(correct),
            "score": p.score, "streak": p.streak}
