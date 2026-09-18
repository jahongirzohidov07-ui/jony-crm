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


def _courses() -> list:
    out = []
    if not os.path.isdir(_PLANS_DIR):
        return out
    for fn in sorted(os.listdir(_PLANS_DIR)):
        if fn.endswith(".json"):
            d = _load_course(fn[:-5])
            if d:
                out.append(d)
    return out


def _lesson(course: str, no: int) -> dict:
    d = _load_course(course)
    if not d:
        raise HTTPException(404, "Kurs topilmadi")
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


@router.get("/api/plans")
def list_plans(user=Depends(require_role(*roles.TEACHING_ACCESS))):
    return [{"course": d["course"], "title": d["title"],
             "lessons": [_summary(L) for L in d["lessons"]]}
            for d in _courses()]


@router.get("/api/plans/{course}/{no}")
def get_plan(course: str, no: int,
             user=Depends(require_role(*roles.TEACHING_ACCESS))):
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
    out = []
    words = [_head(e[0]) for e in entries]
    uzs = [e[1] for e in entries]
    for e in entries:
        w, uz = _head(e[0]), e[1]
        ex, ex_uz = (e[2] if len(e) > 2 else ""), (e[3] if len(e) > 3 else "")
        t = rnd.choice(["uz", "en", "gap"])
        if t == "gap" and ex and re.search(r"\b" + re.escape(w) + r"\b", ex, re.I):
            d = _pick_distractors(rnd, words, w)
            if d:
                gap = re.sub(r"\b" + re.escape(w) + r"\b", "_____", ex, count=1, flags=re.I)
                out.append(_mk(rnd, "vocab", gap, w, d, sub=ex_uz or None))
                continue
            t = "uz"
        if t == "en":
            d = _pick_distractors(rnd, words, w)
            if d:
                out.append(_mk(rnd, "vocab", f"«{uz}» — inglizchasi?", w, d))
                continue
        d = _pick_distractors(rnd, uzs, uz)
        if d:
            out.append(_mk(rnd, "vocab", f"«{w}» — tarjimasi?", uz, d))
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
    rnd.shuffle(voc)
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
    mode: str = "mixed"
    count: int = 12
    seconds: int = 20


class JoinIn(BaseModel):
    code: str
    nickname: str


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
             "rank": i + 1} for i, p in enumerate(ps)]
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
    if body.mode not in MODES:
        raise HTTPException(400, "Rejim noto'g'ri")
    L = _lesson(body.course, body.lesson_no)
    count = max(3, min(30, int(body.count or 12)))
    secs = max(5, min(90, int(body.seconds or 20)))
    qs = build_questions(L, body.mode, count)
    g = models.LiveGame(
        code=_new_code(db), course=body.course, lesson_no=body.lesson_no,
        mode=body.mode, title=f"Dars {L['no']} — {L['title']}",
        questions=json.dumps(qs, ensure_ascii=False), question_seconds=secs,
        status="lobby", q_index=-1, host_user_id=user.id,
        branch_id=getattr(user, "branch_id", None), created_at=_now(),
    )
    db.add(g)
    db.commit()
    db.refresh(g)
    return _host_state(db, g)


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
    return {
        "id": g.id, "code": g.code, "title": g.title, "mode": g.mode,
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
        else:
            g.q_index += 1
            g.status, g.q_started_at = "question", _now()
    db.commit()
    return _host_state(db, g)


@router.post("/api/live/games/{gid}/end")
def end_game(gid: int, db: Session = Depends(get_db),
             user=Depends(require_role(*roles.TEACHING_ACCESS))):
    g = _game_or_404(db, gid, user)
    g.status, g.ended_at = "ended", _now()
    db.commit()
    return _host_state(db, g)


# ---- O'quvchi tomoni (loginsiz) ---------------------------------
@router.post("/api/live/join")
def join(body: JoinIn, db: Session = Depends(get_db)):
    code = re.sub(r"\D", "", body.code or "")
    nick = re.sub(r"\s+", " ", (body.nickname or "").strip())[:24]
    if len(nick) < 2:
        raise HTTPException(400, "Ismingizni yozing")
    g = db.query(models.LiveGame).filter(models.LiveGame.code == code,
                                         models.LiveGame.status != "ended").first()
    if not g:
        raise HTTPException(404, "Bunday PIN bilan o'yin topilmadi")
    if g.status != "lobby":
        raise HTTPException(400, "O'yin allaqachon boshlangan")
    taken = db.query(models.LivePlayer).filter(
        models.LivePlayer.game_id == g.id,
        models.LivePlayer.nickname.ilike(nick)).first()
    if taken:
        raise HTTPException(400, "Bu ism band — boshqasini yozing")
    p = models.LivePlayer(game_id=g.id, nickname=nick, token=secrets.token_urlsafe(18),
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
