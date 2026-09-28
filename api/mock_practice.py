"""XODIMLAR MOCK TESTNI O'ZI YECHIB KO'RADI (2026-09-27).

Jahongir: "faqat guruhda emas, boshqalar ham o'zi kirib ishlaydigan
bo'lsa yaxshi bo'lardi mock testni xodimlargayam koproq ustozlarga
ular ham experience qilib xatolarni aytadida".

  * Xodim (ustoz, support, examiner, rahbarlar) mock bazasidagi istalgan
    variantni o'zi yechadi — guruhsiz, linksiz, login bilan.
  * Natija FAQAT O'ZIGA ko'rinadi va hech qayerga yozilmaydi: Exam,
    ExamOnline, ExamSubmission, ExamResult, coin va XP ga tegilmaydi
    (_finalize / _write_result / _place bu yerdan chaqirilMAYDI).
  * Savolda xato ko'rsa — "xabar berish" (test paytida ham, keyin ham).
    Examinerlar boshlig'i xabarlarni savol bo'yicha guruhlab ko'radi,
    shablonni tuzatib saqlaganda xabar "tuzatildi" bo'ladi
    (exam_online.update_template: resolve_issue_ids).

Javob kaliti himoyasi (ustozlar — roles.MOCK_LIMITED): bir variant 30
kunda bir marta; natijada to'g'ri javob faqat XATO BELGILANGAN
savollarda ko'rinadi, savollarning 60% dan kami belgilangan bo'lsa —
umuman ko'rinmaydi ("ustozlar aynan testga tayyorlash", mix_parts).

Grading doim JORIY shablon bo'yicha (nusxa saqlanmaydi): savol id lari
barqaror, tahrir oynasi q.id ni saqlaydi. Shablon o'chirilsa urinish
content_key (canon_title) bo'yicha boshqa daraja nusxasiga o'tadi.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

import audit
import models
import roles
from auth import has_role, require_role
from database import get_db
from exam_online import (GRACE_SEC, ESSAY_MAX_CHARS, _BANK_LABELS,
                         _BANK_ORDER, _GRADING, _PRACTICE_BANKS,
                         _SEC_ORDER, _parse_iso, AI_RUNNING_SEC,
                         _answer_sheet, _iso, _load, _load_dict,
                         deny_mobile,
                         _mock_section, _norm, _opt_label, _qmap,
                         _questions, _tpl_skill, grade, mock_band,
                         public_parts)
from mock_seed import canon_title

router = APIRouter()

# Vaqt (daqiqa). Speaking — vaqtsiz (yuzma-yuz bo'limi). CEFR
# qiymatlarini examinerlar boshlig'i tasdiqlashi kerak (reja, 1.3).
DURATION = {
    "ielts_listening": 30, "ielts_reading": 60, "ielts_writing": 60,
    "cefr_listening": 35, "cefr_reading": 60, "cefr_writing": 60,
}
LIMIT_DAYS = 30                 # ustoz bir variantni necha kunda bir marta
KEY_MIN_ANSWERED = 0.6          # shundan kam belgilansa kalit ko'rsatilmaydi
KEY_MIN_SCORE = 0.5             # natija shundan past bo'lsa ham ko'rsatilmaydi
ISSUE_DAY_CAP = 30              # bir xodim bir kunda nechta xabar
SIGNAL_DAYS = 90                # xato foizi qancha kunlik urinishlardan
SUSPECT_MIN_ATTEMPTS = 3
SUSPECT_SAME_WRONG = 0.6
ANSWERS_MAX_CHARS = 60_000      # Writing: 2 ta insho x 12 000 + zaxira
ISSUE_KINDS = ("answer_key", "two_answers", "typo", "unclear",
               "script_audio", "other")
ISSUE_STATUSES = ("open", "fixed", "rejected", "duplicate")


# ------------------------------------------------------------- yordamchi
def _limited(user) -> bool:
    return getattr(user, "role", None) in roles.MOCK_LIMITED


def _mock_rows_by_key(db: Session, content_key: str) -> list:
    """Shu mazmundagi (canon_title) barcha mock qatorlari, id bo'yicha."""
    rows = (db.query(models.ExamTemplate)
            .filter(models.ExamTemplate.kind == "mock",
                    models.ExamTemplate.title.startswith(content_key,
                                                         autoescape=True))
            .order_by(models.ExamTemplate.id).all())
    return [t for t in rows if canon_title(t.title) == content_key]


def _rep(db: Session, content_key: str, active_only: bool = False):
    """Mazmunning vakil qatori: eng kichik id li FAOL mock; faoli yo'q
    bo'lsa — istalgani; umuman yo'q bo'lsa 410."""
    rows = _mock_rows_by_key(db, content_key or "")
    act = [t for t in rows if t.is_active == 1]
    if act:
        return act[0]
    if rows and not active_only:
        return rows[0]
    raise HTTPException(410, "Test o'chirilgan")


def _tpl_for(db: Session, p: models.MockPractice):
    t = db.query(models.ExamTemplate).get(p.template_id)
    if t is not None:
        return t
    return _rep(db, p.content_key)


def _bank_sec(skill: str) -> tuple:
    bank, _, sec = (skill or "").partition("_")
    if not sec:
        return "ielts", (skill or "?")
    return bank, sec


def _script_parts(parts: list) -> list:
    """Audio yo'q, lekin skripti bor bo'limlar — brauzer o'qib beradi."""
    return [i for i, p in enumerate(parts)
            if (p.get("script") or "").strip() and not p.get("audio_url")]


def _opened(p) -> list:
    out = []
    for x in (p.script_opened or "").split(","):
        try:
            out.append(int(x))
        except ValueError:
            pass
    return out


def _answered(v) -> bool:
    return v is not None and str(v).strip() != ""


def _clean_answers(answers) -> dict:
    """Javoblarni tozalaydi. public_save butun JSON ni 20 000 belgida
    kesardi (Writing'da buzuq JSON bo'lib qolishi mumkin) — bu yerda
    har javob alohida cheklanadi, jami juda katta bo'lsa 400."""
    out = {}
    for k, v in list((answers or {}).items())[:400]:
        k = str(k)[:40]
        if isinstance(v, bool) or v is None:
            continue
        if isinstance(v, (int, float)):
            out[k] = v
        elif isinstance(v, str):
            out[k] = v[:ESSAY_MAX_CHARS]
        elif isinstance(v, list):
            out[k] = [x for x in v[:10]
                      if isinstance(x, (int, str)) and not isinstance(x, bool)]
    if len(json.dumps(out, ensure_ascii=False)) > ANSWERS_MAX_CHARS:
        raise HTTPException(400, "Javoblar juda katta")
    return out


def _label(q: dict, v) -> Optional[str]:
    """Javobning o'qiladigan ko'rinishi: "B) is", "A, C" yoki matn."""
    if v is None or v == "" or v == []:
        return None
    typ = q.get("type")
    opts = q.get("options") or []
    if typ == "choice":
        try:
            i = int(v)
        except (TypeError, ValueError):
            return str(v)[:200]
        return _opt_label(opts, i) if 0 <= i < len(opts) else str(v)[:200]
    if typ == "multi":
        raw = v if isinstance(v, list) else str(v).split(",")
        try:
            idx = sorted({int(x) for x in raw if str(x).strip() != ""})
        except (TypeError, ValueError):
            return str(v)[:200]
        return ", ".join(_opt_label(opts, i) for i in idx
                         if 0 <= i < len(opts)) or None
    return str(v)[:200]


def _key_label(q: dict) -> Optional[str]:
    typ = q.get("type")
    a = q.get("answer")
    if typ == "essay":
        return None
    if typ in ("choice", "multi"):
        return _label(q, a)
    return " / ".join(str(x) for x in (a or [])) or None


def _q_view(q: Optional[dict]) -> Optional[dict]:
    """Savolning server tomondagi nusxasi (javob bilan). Faqat triage
    ro'yxatiga (examinerlar) chiqadi."""
    if not q:
        return None
    return {"q": q.get("q") or "", "options": q.get("options") or [],
            "answer": q.get("answer"), "type": q.get("type"),
            "part": q.get("part")}


def _q_hash(q: Optional[dict]) -> Optional[str]:
    if not q:
        return None
    norm = {"q": " ".join(str(q.get("q") or "").split()),
            "options": [" ".join(str(o).split())
                        for o in (q.get("options") or [])],
            "answer": q.get("answer"), "type": q.get("type")}
    raw = json.dumps(norm, ensure_ascii=False, sort_keys=True)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def _cefr_of(p) -> Optional[dict]:
    try:
        v = json.loads(p.cefr) if p.cefr else None
        return v if isinstance(v, dict) else None
    except Exception:          # noqa: BLE001
        return None


def _finish(db: Session, p: models.MockPractice, answers) -> None:
    """Urinishni baholab yopadi. HECH NARSA boshqa jadvalga yozilmaydi."""
    tpl = _tpl_for(db, p)
    parts = _load(tpl.parts)
    answers = _clean_answers({str(k): v for k, v in (answers or {}).items()})
    score, total, detail = grade(parts, answers)
    sec = _mock_section(parts) or (p.skill or "")
    cefr = None
    if sec in ("cefr_listening", "cefr_reading") and total > 0:
        try:
            from cefr_score import lr_approx
            cefr = lr_approx(score, int(total))
        except Exception:      # noqa: BLE001
            cefr = None
    p.answers = json.dumps(answers, ensure_ascii=False)
    p.detail = json.dumps(detail, ensure_ascii=False)
    p.score = score
    p.max_score = total
    p.band = mock_band(parts, score, total)
    p.cefr = json.dumps(cefr, ensure_ascii=False) if cefr else None
    p.status = "submitted"
    p.submitted_at = datetime.utcnow()
    db.commit()


def _deadline_passed(p) -> bool:
    return bool(p.ends_at) and \
        datetime.utcnow() > p.ends_at + timedelta(seconds=GRACE_SEC)


def _expire_if_due(db: Session, p: models.MockPractice,
                   orphan_ok: bool = False) -> bool:
    """Vaqt + muhlat o'tgan urinish saqlangan javoblari bilan yopiladi
    (sahifa yopilib qolsa ham). orphan_ok — shablon butunlay o'chgan
    bo'lsa ham urinish yopilsin (yangisini boshlashga to'sqinlik
    qilmasin)."""
    if p.status != "in_progress" or not _deadline_passed(p):
        return False
    try:
        _finish(db, p, _load_dict(p.answers))
    except HTTPException:
        if not orphan_ok:
            raise
        db.rollback()
        p.status = "submitted"
        p.submitted_at = datetime.utcnow()
        db.commit()
    return True


def _own(db: Session, pid: int, user) -> models.MockPractice:
    p = db.query(models.MockPractice).get(pid)
    if not p or p.user_id != user.id:
        # Boshqaning urinishi borligi ham oshkor qilinmaydi
        raise HTTPException(404, "Urinish topilmadi")
    return p


def _issues_of_attempt(db: Session, p) -> list:
    rows = (db.query(models.MockIssue)
            .filter(models.MockIssue.practice_id == p.id,
                    models.MockIssue.reporter_id == p.user_id)
            .order_by(models.MockIssue.id).all())
    return [{"id": i.id, "qid": i.qid, "q_n": i.q_n, "kind": i.kind,
             "comment": i.comment, "suggested": i.suggested,
             "status": i.status, "resolution_note": i.resolution_note}
            for i in rows]


def _tpl_changed(p, tpl) -> bool:
    if tpl.id != p.template_id:
        return True
    return bool(tpl.updated_at and p.tpl_updated_at
                and tpl.updated_at != p.tpl_updated_at)


def _head(p) -> dict:
    return {"id": p.id, "status": p.status, "content_key": p.content_key,
            "title": p.content_key, "skill": p.skill,
            "variant": p.variant or "A",
            "started_at": _iso(p.started_at), "ends_at": _iso(p.ends_at),
            "duration_min": p.duration_min,
            "server_now": _iso(datetime.utcnow())}


def _review(db: Session, p: models.MockPractice, user, tpl) -> dict:
    """Topshirilgan urinish: ball + javoblar varag'i. Ustozlarda
    (MOCK_LIMITED) to'g'ri javob cheklanadi — modul izohiga qarang.
    Skriptlar topshirilgandan keyin qaytarilmaydi."""
    parts = _load(tpl.parts)
    sheet = _answer_sheet(_load(p.detail), _qmap(parts))
    auto = [d for d in sheet if d.get("ok") is not None]
    answered = sum(1 for d in auto if _answered(d.get("given")))
    ratio = (answered / len(auto)) if auto else 1.0
    right = (sum(1 for d in auto if d.get("ok")) / len(auto)) if auto else 1.0
    limited = _limited(user)
    # Faqat "javob berilgan" sharti yetmaydi (2026-09-27 xavfsizlik
    # ko'rigi): hamma savolga tasodifiy javob belgilab topshirilsa,
    # hammasi xato bo'ladi va butun kalit bir urinishda ochilardi.
    # Shuning uchun kalit faqat HAQIQIY urinishda ko'rsatiladi — natija
    # kamida KEY_MIN_SCORE bo'lsa. Tasodifiy javoblar bunga yetmaydi.
    hide_all = limited and (ratio < KEY_MIN_ANSWERED or right < KEY_MIN_SCORE)
    if limited:
        for d in sheet:
            if hide_all or not _answered(d.get("given")):
                d["correct"] = None
    return {
        **_head(p),
        "score": p.score, "max": p.max_score, "band": p.band,
        "cefr": _cefr_of(p),
        "submitted_at": _iso(p.submitted_at),
        "script_opened": _opened(p),
        "tpl_changed": _tpl_changed(p, tpl),
        "answered": answered, "auto_count": len(auto),
        "limited": limited, "key_hidden": bool(hide_all),
        "detail": sheet,
        "issues": _issues_of_attempt(db, p),
        # Writing — AI bahosi (2026-09-28); sahifa yo'q bo'lsa baholatadi
        "ai_writing": _is_writing(parts),
        "ai": _ai_of(p),
    }


# ------------------------------------------------------- WRITING AI
# 2026-09-28, Jahongir: "Writingni ham avtobaholaydigan qilib qoysak".
# Xodim sinovida ham insho AI bilan baholanadi — natija faqat egasiga.
# Holat p.ai_review JSON ichida: {"status": running|done|error|no_key}.
AI_OWNER_TRIES = 5


def _is_writing(parts) -> bool:
    import writing_ai
    return writing_ai.skill_of(parts) is not None


def _ai_of(p) -> Optional[dict]:
    d = _load_dict(p.ai_review)
    if not d:
        return None
    d.pop("started", None)
    d.pop("prev", None)
    return d


@router.post("/api/mock-practice/{pid}/ai-grade")
def ai_grade(pid: int, force: bool = False, db: Session = Depends(get_db),
             user=Depends(require_role(*roles.MOCK_PRACTICE))):
    """Topshirilgan Writing urinishini AI bilan baholaydi (bitta so'rov —
    bitta urinish, Vercel 30 s). Idempotent: baholangan bo'lsa qayta
    chaqirmaydi (force — qayta baholash)."""
    import writing_ai
    p = _own(db, pid, user)
    tpl = _tpl_for(db, p)
    parts = _load(tpl.parts)
    if p.status != "submitted" or not writing_ai.skill_of(parts):
        return _review(db, p, user, tpl) if p.status == "submitted" else {"ok": False}
    meta = _load_dict(p.ai_review)
    st = meta.get("status")
    now = datetime.utcnow()
    tries = int(meta.get("tries") or 0)
    if st == "done" and not force:
        return _review(db, p, user, tpl)
    if st == "running":
        started = _parse_iso(meta.get("started"))
        if started and (now - started).total_seconds() < AI_RUNNING_SEC:
            return _review(db, p, user, tpl)
    # Avtomat urinishlar 5 ta; egasi "Qayta urinish" (force) bosa — 10 tagacha
    if st != "done" and tries >= (AI_OWNER_TRIES * 2 if force else AI_OWNER_TRIES):
        return _review(db, p, user, tpl)
    M = models.MockPractice
    old = p.ai_review
    claim = {"status": "running", "tries": tries,
             "started": now.isoformat(timespec="seconds")}
    q = db.query(M).filter(M.id == p.id)
    q = q.filter(M.ai_review.is_(None) if old is None else M.ai_review == old)
    got = q.update({M.ai_review: json.dumps(claim)}, synchronize_session=False)
    db.commit()
    db.refresh(p)
    if got != 1:
        return _review(db, p, user, tpl)
    try:
        res = writing_ai.grade(parts, _load_dict(p.answers))
    except writing_ai.WritingAIError as e:
        db.refresh(p)
        if st == "done":
            p.ai_review = old         # qayta baholash bo'lmadi — eskisi qoladi
        else:
            p.ai_review = json.dumps({
                "status": "no_key" if e.code == "no_key" else "error",
                "error": e.code, "tries": tries + 1,
                "at": now.isoformat(timespec="seconds")})
        db.commit()
        return _review(db, p, user, tpl)
    db.refresh(p)
    res.update({"status": "done", "tries": tries + 1})
    p.ai_review = json.dumps(res, ensure_ascii=False)
    if res["skill"] == "ielts_writing":
        p.band = float(res["band"])
    else:
        p.cefr = json.dumps({"level": res.get("level"), "score": res.get("score"),
                             "of": 75, "approx": not res.get("exact")},
                            ensure_ascii=False)
    db.commit()
    return _review(db, p, user, tpl)


# ------------------------------------------------------------- katalog
@router.get("/api/mock-practice/catalog")
def catalog(db: Session = Depends(get_db),
            user=Depends(require_role(*roles.MOCK_PRACTICE))):
    """Faol mocklar, MAZMUN bo'yicha bitta (seed har faylni 3 darajaga
    yozadi — ro'yxatda bittasi), bank -> bo'lim -> variant. Savollar va
    kalitlar yo'q."""
    rows = (db.query(models.ExamTemplate)
            .filter(models.ExamTemplate.kind == "mock",
                    models.ExamTemplate.is_active == 1)
            .order_by(models.ExamTemplate.id).all())
    reps: dict = {}
    for t in rows:
        reps.setdefault(canon_title(t.title), t)
    mine = (db.query(models.MockPractice)
            .filter(models.MockPractice.user_id == user.id)
            .order_by(models.MockPractice.id).all())
    last, open_ = {}, {}
    for p in mine:
        if p.status == "submitted":
            last[p.content_key] = p
        elif p.status == "in_progress":
            open_[p.content_key] = p.id
    iss = dict(db.query(models.MockIssue.content_key, func.count())
               .filter(models.MockIssue.status == "open")
               .group_by(models.MockIssue.content_key).all())
    limited = _limited(user)
    now = datetime.utcnow()
    banks: dict = {}
    for ck, t in reps.items():
        parts = _load(t.parts)
        skill = _mock_section(parts) or _tpl_skill(t)
        bank, sec = _bank_sec(skill)
        lp = last.get(ck)
        locked = None
        if limited and lp:
            until = (lp.submitted_at or lp.created_at or now) \
                + timedelta(days=LIMIT_DAYS)
            if until > now:
                locked = _iso(until)
        item = {
            "content_key": ck, "title": ck, "variant": t.variant or "A",
            "skill": skill,
            "q_count": sum(1 for _ in _questions(parts)),
            "auto_count": sum(1 for q in _questions(parts)
                              if q.get("type") != "essay"),
            "duration": DURATION.get(skill),
            "has_script": bool(_script_parts(parts)),
            "my_last": ({"id": lp.id, "score": lp.score,
                         "max": lp.max_score, "band": lp.band,
                         "at": _iso(lp.submitted_at)} if lp else None),
            "my_open": open_.get(ck),
            "locked_until": locked,
            "open_issues": int(iss.get(ck) or 0),
        }
        banks.setdefault(bank, {}).setdefault(sec, []).append(item)
    out = []
    for bank in sorted(banks, key=lambda b: (b in _PRACTICE_BANKS,
                                             _BANK_ORDER.get(b, 9), b)):
        secs = []
        for sec in sorted(banks[bank], key=lambda x: (_SEC_ORDER.get(x, 9), x)):
            items = sorted(banks[bank][sec],
                           key=lambda x: (x["variant"], x["content_key"]))
            auto, note = _GRADING.get((bank, sec), (False, ""))
            secs.append({"section": sec, "skill": f"{bank}_{sec}",
                         "duration": DURATION.get(f"{bank}_{sec}"),
                         "auto": auto, "grading": note,
                         "variants": items})
        out.append({"bank": bank, "label": _BANK_LABELS.get(bank, bank),
                    "practice": bank in _PRACTICE_BANKS, "sections": secs})
    cur = next((p for p in reversed(mine) if p.status == "in_progress"), None)
    return {"banks": out, "limited": limited, "limit_days": LIMIT_DAYS,
            "in_progress": ({"id": cur.id, "content_key": cur.content_key,
                             "ends_at": _iso(cur.ends_at)} if cur else None)}


# ------------------------------------------------------------- urinish
class StartIn(BaseModel):
    content_key: str
    timed: bool = True


@router.post("/api/mock-practice")
def start(payload: StartIn, request: Request, db: Session = Depends(get_db),
          user=Depends(require_role(*roles.MOCK_PRACTICE))):
    """Yangi urinish. Bir vaqtda bittasi: boshlangani bo'lsa o'sha
    qaytadi. Ustozlarga bir variant 30 kunda bir marta.

    Mock faqat kompyuterda (2026-09-27, Jahongir: "mock test faqat
    kompyuterda ishlanadi bizda telda mumkinmas") — telefon/planshetdan
    boshlanmaydi. Asosiy tekshiruv sahifada, bu ikkinchi qavat."""
    deny_mobile(request)
    ck = canon_title(payload.content_key)
    for p in (db.query(models.MockPractice)
              .filter(models.MockPractice.user_id == user.id,
                      models.MockPractice.status == "in_progress")
              .order_by(models.MockPractice.id).all()):
        if _expire_if_due(db, p, orphan_ok=True):
            continue
        # Vaqtsiz urinish (Speaking yoki timed=false) testi o'chirilgan
        # bo'lsa, u hech qachon yopilmas va foydalanuvchi mockdan butunlay
        # qulflanib qolardi (2026-09-27 ko'rik) — bunday urinish yopiladi.
        try:
            _tpl_for(db, p)
        except HTTPException:
            db.rollback()
            p.status = "submitted"
            p.submitted_at = datetime.utcnow()
            db.commit()
            continue
        return {"id": p.id, "resumed": True, "content_key": p.content_key}
    if _limited(user):
        since = datetime.utcnow() - timedelta(days=LIMIT_DAYS)
        done = (db.query(models.MockPractice.id)
                .filter(models.MockPractice.user_id == user.id,
                        models.MockPractice.content_key == ck,
                        models.MockPractice.status == "submitted",
                        models.MockPractice.submitted_at >= since).first())
        if done:
            raise HTTPException(
                429, f"Bu variantni {LIMIT_DAYS} kunda bir marta yechish "
                     f"mumkin")
    t = _rep(db, ck, active_only=True)
    parts = _load(t.parts)
    skill = _mock_section(parts) or _tpl_skill(t)
    now = datetime.utcnow()
    dur = DURATION.get(skill) if payload.timed else None
    p = models.MockPractice(
        user_id=user.id, user_name=user.full_name, template_id=t.id,
        content_key=ck, skill=skill or None, variant=(t.variant or "A")[:4],
        tpl_updated_at=t.updated_at, answers="{}", status="in_progress",
        duration_min=dur, started_at=now,
        ends_at=(now + timedelta(minutes=dur)) if dur else None)
    db.add(p)
    db.commit()
    audit.log(db, user, entity="mock_practice", action="start",
              entity_id=p.id, entity_label=ck, commit=True)
    return {"id": p.id, "resumed": False, "content_key": ck}


@router.get("/api/mock-practice/mine")
def my_attempts(db: Session = Depends(get_db),
                user=Depends(require_role(*roles.MOCK_PRACTICE))):
    rows = (db.query(models.MockPractice)
            .filter(models.MockPractice.user_id == user.id)
            .order_by(models.MockPractice.id.desc()).limit(200).all())
    for p in rows:
        _expire_if_due(db, p, orphan_ok=True)
    counts: dict = defaultdict(Counter)
    ids = [p.id for p in rows]
    if ids:
        for pid, st, n in (db.query(models.MockIssue.practice_id,
                                    models.MockIssue.status, func.count())
                           .filter(models.MockIssue.practice_id.in_(ids),
                                   models.MockIssue.reporter_id == user.id)
                           .group_by(models.MockIssue.practice_id,
                                     models.MockIssue.status).all()):
            counts[pid][st] = int(n)
    return [{"id": p.id, "content_key": p.content_key,
             "title": p.content_key, "skill": p.skill,
             "variant": p.variant or "A", "status": p.status,
             "score": p.score, "max": p.max_score, "band": p.band,
             "cefr_level": (_cefr_of(p) or {}).get("level"),
             "started_at": _iso(p.started_at), "ends_at": _iso(p.ends_at),
             "submitted_at": _iso(p.submitted_at),
             "issues": {s: counts[p.id].get(s, 0) for s in ISSUE_STATUSES}}
            for p in rows]


@router.get("/api/mock-practice/log")
def exposure_log(days: int = 90, db: Session = Depends(get_db),
                 user=Depends(require_role(*roles.MOCK_ISSUE_TRIAGE))):
    """Kim qaysi variantni qachon ochgan (kalitlar kimga ochilgani).
    Ball YO'Q — natija faqat egasiga."""
    days = max(1, min(365, int(days or 90)))
    since = datetime.utcnow() - timedelta(days=days)
    rows = (db.query(models.MockPractice)
            .filter(models.MockPractice.created_at >= since)
            .order_by(models.MockPractice.id.desc()).limit(2000).all())
    role_of = dict(db.query(models.User.id, models.User.role)
                   .filter(models.User.id.in_(
                       sorted({p.user_id for p in rows}) or [0])).all())
    return [{"id": p.id, "user_id": p.user_id, "user_name": p.user_name,
             "role": role_of.get(p.user_id), "content_key": p.content_key,
             "skill": p.skill, "variant": p.variant or "A",
             "status": p.status, "started_at": _iso(p.started_at),
             "submitted_at": _iso(p.submitted_at),
             "script_opened": _opened(p)}
            for p in rows]


@router.get("/api/mock-practice/{pid}")
def get_attempt(pid: int, db: Session = Depends(get_db),
                user=Depends(require_role(*roles.MOCK_PRACTICE))):
    p = _own(db, pid, user)
    _expire_if_due(db, p)
    tpl = _tpl_for(db, p)
    if p.status == "submitted":
        return _review(db, p, user, tpl)
    parts = _load(tpl.parts)
    return {**_head(p),
            "parts": public_parts(parts),
            "answers": _load_dict(p.answers),
            "script_parts": _script_parts(parts),
            "script_opened": _opened(p),
            "tpl_changed": _tpl_changed(p, tpl),
            "issues": _issues_of_attempt(db, p)}


class SaveIn(BaseModel):
    answers: dict


@router.post("/api/mock-practice/{pid}/save")
def save(pid: int, payload: SaveIn, db: Session = Depends(get_db),
         user=Depends(require_role(*roles.MOCK_PRACTICE))):
    p = _own(db, pid, user)
    if p.status != "in_progress":
        return {"ok": True, "submitted": True}
    if _deadline_passed(p):
        return {"ok": False, "expired": True}
    p.answers = json.dumps(_clean_answers(payload.answers),
                           ensure_ascii=False)
    db.commit()
    return {"ok": True}


@router.post("/api/mock-practice/{pid}/script/{part_idx}")
def script(pid: int, part_idx: int, db: Session = Depends(get_db),
           user=Depends(require_role(*roles.MOCK_PRACTICE))):
    """Audio yo'q listening bo'limi: matn brauzerda ovozga o'giriladi
    (speechSynthesis). Ekranda ko'rsatilmaydi; kim ochgani yoziladi."""
    p = _own(db, pid, user)
    if p.status != "in_progress" or _deadline_passed(p):
        raise HTTPException(400, "Test yakunlangan")
    parts = _load(_tpl_for(db, p).parts)
    if part_idx not in _script_parts(parts):
        raise HTTPException(400, "Bu bo'limda o'qib beriladigan matn yo'q")
    opened = _opened(p)
    if part_idx not in opened:
        opened.append(part_idx)
        p.script_opened = ",".join(str(i) for i in opened)
        db.commit()
    return {"script": parts[part_idx].get("script") or ""}


class SubmitIn(BaseModel):
    answers: Optional[dict] = None


@router.post("/api/mock-practice/{pid}/submit")
def submit(pid: int, payload: SubmitIn, db: Session = Depends(get_db),
           user=Depends(require_role(*roles.MOCK_PRACTICE))):
    """Idempotent: ikkinchi marta bosilsa ham o'sha natija qaytadi."""
    p = _own(db, pid, user)
    if p.status == "in_progress":
        if _deadline_passed(p) or payload.answers is None:
            answers = _load_dict(p.answers)
        else:
            answers = payload.answers
        _finish(db, p, answers)
    return _review(db, p, user, _tpl_for(db, p))


# --------------------------------------------------------- savol xatolari
class IssueIn(BaseModel):
    practice_id: Optional[int] = None
    content_key: Optional[str] = None
    qid: Optional[str] = None
    part_idx: Optional[int] = None      # qid siz: butun bo'lim haqida
    kind: str
    comment: Optional[str] = None
    suggested: Optional[str] = None


@router.post("/api/mock-issues")
def report_issue(payload: IssueIn, db: Session = Depends(get_db),
                 user=Depends(require_role(*roles.MOCK_PRACTICE))):
    """Savolda xato haqida xabar. Javobda hech qanday kalit yo'q."""
    if payload.kind not in ISSUE_KINDS:
        raise HTTPException(400, "Xato turi noto'g'ri")
    p = None
    if payload.practice_id is not None:
        p = db.query(models.MockPractice).get(payload.practice_id)
        if not p or p.user_id != user.id:
            raise HTTPException(403, "Faqat o'zingiz yechgan test haqida "
                                     "xabar bera olasiz")
        tpl = _tpl_for(db, p)
        ck = p.content_key
    else:
        # Examinerlar urinishsiz ham (Test bazasini ko'rib) xabar beradi
        if not has_role(user, roles.MOCK_ISSUE_VIEW):
            raise HTTPException(403, "Avval testni yechib ko'ring")
        ck = canon_title(payload.content_key or "")
        if not ck:
            raise HTTPException(400, "Test ko'rsatilmagan")
        tpl = _rep(db, ck)
    parts = _load(tpl.parts)
    qmap = _qmap(parts)
    qid = (payload.qid or "").strip() or None
    q = None
    part_title = None
    if qid:
        q = qmap.get(qid)
        if not q:
            raise HTTPException(400, "Savol topilmadi")
        part_title = q.get("part")
    elif payload.part_idx is not None:
        if not (0 <= payload.part_idx < len(parts)):
            raise HTTPException(400, "Bo'lim topilmadi")
        part_title = parts[payload.part_idx].get("title")
    since = datetime.utcnow() - timedelta(days=1)
    row = (db.query(models.MockIssue)
           .filter(models.MockIssue.reporter_id == user.id,
                   models.MockIssue.content_key == ck,
                   models.MockIssue.qid.is_(None) if qid is None
                   else models.MockIssue.qid == qid,
                   models.MockIssue.status == "open").first())
    if row is None:
        n_today = (db.query(func.count(models.MockIssue.id))
                   .filter(models.MockIssue.reporter_id == user.id,
                           models.MockIssue.created_at >= since).scalar())
        if (n_today or 0) >= ISSUE_DAY_CAP:
            raise HTTPException(429, f"Bir kunda {ISSUE_DAY_CAP} tadan "
                                     f"ko'p xabar yuborib bo'lmaydi")
        row = models.MockIssue(content_key=ck, qid=qid, reporter_id=user.id,
                               reporter_name=user.full_name, status="open")
        db.add(row)
    given = None
    if p is not None and qid and q:
        given = _label(q, _load_dict(p.answers).get(qid))
    skill = _mock_section(parts) or _tpl_skill(tpl)
    row.template_id = tpl.id
    row.skill = (skill or None) and skill[:40]
    row.variant = (tpl.variant or "A")[:4]
    row.q_n = q.get("n") if q else None
    row.part_title = part_title
    row.q_snapshot = (json.dumps(_q_view(q), ensure_ascii=False)
                      if q else None)
    row.q_hash = _q_hash(q)
    row.kind = payload.kind
    row.comment = (payload.comment or "").strip()[:1000] or None
    row.suggested = (payload.suggested or "").strip()[:300] or None
    row.given = given[:200] if given else None
    row.during_test = 1 if (p is not None and p.status == "in_progress") \
        else 0
    row.practice_id = p.id if p is not None else None
    db.commit()
    return {"id": row.id, "status": row.status}


def _issue_out(i: models.MockIssue) -> dict:
    snap = _load_dict(i.q_snapshot) if i.q_snapshot else {}
    return {"id": i.id, "content_key": i.content_key, "skill": i.skill,
            "variant": i.variant or "A", "qid": i.qid, "q_n": i.q_n,
            "part_title": i.part_title, "q": snap.get("q"),
            "kind": i.kind, "comment": i.comment,
            "suggested": i.suggested, "given": i.given,
            "during_test": bool(i.during_test),
            "practice_id": i.practice_id, "status": i.status,
            "resolution_note": i.resolution_note,
            "resolved_by": i.resolved_by,
            "resolved_at": _iso(i.resolved_at),
            "created_at": _iso(i.created_at)}


@router.get("/api/mock-issues/mine")
def my_issues(db: Session = Depends(get_db),
              user=Depends(require_role(*roles.MOCK_PRACTICE))):
    """Xabarchining o'z xabarlari holati bilan (kalit YO'Q)."""
    rows = (db.query(models.MockIssue)
            .filter(models.MockIssue.reporter_id == user.id)
            .order_by(models.MockIssue.id.desc()).limit(300).all())
    return [_issue_out(i) for i in rows]


@router.get("/api/mock-issues/count")
def issues_count(db: Session = Depends(get_db),
                 user=Depends(require_role(*roles.MOCK_ISSUE_VIEW))):
    n = (db.query(func.count(models.MockIssue.id))
         .filter(models.MockIssue.status == "open").scalar())
    return {"open": int(n or 0)}


def _signals(db: Session) -> dict:
    """(content_key, qid) -> {n, wrong, blank, wrong_given: Counter}.
    Oxirgi 90 kunda TOPSHIRILGAN xodim urinishlaridan."""
    since = datetime.utcnow() - timedelta(days=SIGNAL_DAYS)
    out: dict = {}
    for ck, detail in (db.query(models.MockPractice.content_key,
                                models.MockPractice.detail)
                       .filter(models.MockPractice.status == "submitted",
                               models.MockPractice.submitted_at >= since)
                       .all()):
        for d in _load(detail):
            if not isinstance(d, dict) or d.get("ok") is None:
                continue
            s = out.setdefault((ck, str(d.get("id"))),
                               {"n": 0, "wrong": 0, "blank": 0,
                                "wrong_given": Counter(), "raw": {}})
            g = d.get("given")
            if not _answered(g):
                s["blank"] += 1
                continue
            s["n"] += 1
            if d.get("ok") is False:
                s["wrong"] += 1
                k = _norm(g) or str(g)
                s["wrong_given"][k] += 1
                s["raw"].setdefault(k, g)
    return out


def _signal_view(s: Optional[dict], q: Optional[dict]) -> Optional[dict]:
    if not s:
        return None
    top, top_n = None, 0
    if s["wrong_given"]:
        k, top_n = s["wrong_given"].most_common(1)[0]
        raw = s["raw"].get(k)
        top = _label(q, raw) if q else str(raw)
    return {"n_attempts": s["n"], "n_blank": s["blank"],
            "wrong": s["wrong"],
            "wrong_pct": round(100 * s["wrong"] / s["n"]) if s["n"] else 0,
            "top_wrong": top, "top_wrong_n": top_n,
            "key": _key_label(q) if q else None}


@router.get("/api/mock-issues")
def list_issues(status: str = "open", db: Session = Depends(get_db),
                user=Depends(require_role(*roles.MOCK_ISSUE_VIEW))):
    """Savol bo'yicha guruhlangan xabarlar (ko'p xabar berilgani
    tepada) + xabarsiz "shubhali" savollar (xodimlarning ko'pchiligi
    bir xil xato javob bergan — kalit xato bo'lishi mumkin)."""
    q = db.query(models.MockIssue)
    if status != "all":
        if status not in ISSUE_STATUSES:
            raise HTTPException(400, "Holat noto'g'ri")
        q = q.filter(models.MockIssue.status == status)
    issues = q.order_by(models.MockIssue.id).all()

    # Mazmun -> qatorlar (nusxalar soni, faol vakil, joriy savollar)
    by_key: dict = defaultdict(list)
    for tid, title, act in (db.query(models.ExamTemplate.id,
                                     models.ExamTemplate.title,
                                     models.ExamTemplate.is_active)
                            .filter(models.ExamTemplate.kind == "mock")
                            .order_by(models.ExamTemplate.id).all()):
        by_key[canon_title(title)].append((tid, act))
    qmaps: dict = {}

    def cur_map(ck):
        if ck not in qmaps:
            rows = by_key.get(ck) or []
            act = [tid for tid, a in rows if a == 1]
            tid = (act or [r[0] for r in rows] or [None])[0]
            t = db.query(models.ExamTemplate).get(tid) if tid else None
            qmaps[ck] = (tid, _qmap(_load(t.parts)) if t else {}, t)
        return qmaps[ck]

    sig = _signals(db)
    groups: dict = {}
    for i in issues:
        g = groups.setdefault((i.content_key, i.qid), [])
        g.append(i)
    out = []
    for (ck, qid), rows in groups.items():
        tid, qm, t = cur_map(ck)
        cur = qm.get(qid) if qid else None
        cur_hash = _q_hash(cur)
        last = rows[-1]
        snap = _load_dict(last.q_snapshot) if last.q_snapshot else None
        out.append({
            "content_key": ck, "qid": qid, "q_n": last.q_n,
            "part_title": last.part_title, "skill": last.skill,
            "variant": last.variant or "A",
            "template_id": tid,
            "copies": len(by_key.get(ck) or []),
            "n": len({i.reporter_id for i in rows}),
            "issue_ids": [i.id for i in rows],
            "statuses": dict(Counter(i.status for i in rows)),
            "kinds": dict(Counter(i.kind for i in rows)),
            "comments": [{"id": i.id, "name": i.reporter_name,
                          "kind": i.kind, "text": i.comment,
                          "suggested": i.suggested, "given": i.given,
                          "during_test": bool(i.during_test),
                          "status": i.status,
                          "resolution_note": i.resolution_note,
                          "at": _iso(i.created_at)} for i in rows],
            "snapshot": snap,
            "current": _q_view(cur),
            "changed": bool(qid) and any(
                (i.q_hash or None) != cur_hash for i in rows),
            "signal": _signal_view(sig.get((ck, qid)), cur) if qid else None,
        })
    out.sort(key=lambda x: (-x["n"], -len(x["issue_ids"]),
                            x["content_key"], x["q_n"] or 0))

    # Shubhali savollar: umuman xabar yo'q, lekin >=3 urinish va >=60%
    # bir xil XATO javob
    reported = {(k, qid) for k, qid in
                db.query(models.MockIssue.content_key,
                         models.MockIssue.qid).distinct().all()}
    suspect = []
    for (ck, qid), s in sig.items():
        if (ck, qid) in reported or s["n"] < SUSPECT_MIN_ATTEMPTS:
            continue
        if not s["wrong_given"]:
            continue
        _k, top_n = s["wrong_given"].most_common(1)[0]
        if top_n / s["n"] < SUSPECT_SAME_WRONG:
            continue
        tid, qm, t = cur_map(ck)
        cur = qm.get(qid)
        if not cur:
            continue
        suspect.append({"content_key": ck, "qid": qid, "q_n": cur.get("n"),
                        "part_title": cur.get("part"),
                        "variant": (t.variant if t else None) or "A",
                        "template_id": tid, "q": cur.get("q") or "",
                        "current": _q_view(cur),
                        **_signal_view(s, cur)})
    suspect.sort(key=lambda x: (-x["top_wrong_n"], x["content_key"],
                                x["q_n"] or 0))
    return {"groups": out, "suspect": suspect}


class TriageIn(BaseModel):
    status: str
    note: Optional[str] = None


@router.put("/api/mock-issues/{iid}")
def triage(iid: int, payload: TriageIn, db: Session = Depends(get_db),
           user=Depends(require_role(*roles.MOCK_ISSUE_TRIAGE))):
    """Butun guruhni (bir savol bo'yicha barcha ochiq xabarlarni) yopadi."""
    if payload.status not in ("fixed", "rejected", "duplicate"):
        raise HTTPException(400, "Holat noto'g'ri")
    i = db.query(models.MockIssue).get(iid)
    if not i:
        raise HTTPException(404, "Xabar topilmadi")
    # Eskirgan ro'yxatdan bosilgan tugma allaqachon yopilgan xabarni
    # qayta yozmasin va shu savolga keyin kelgan yangi xabarlarni ham
    # ko'r-ko'rona yopmasin (2026-09-27 ko'rik).
    if i.status != "open":
        raise HTTPException(409, "Bu xabar allaqachon yopilgan — "
                                 "ro'yxatni yangilang")
    q = db.query(models.MockIssue).filter(
        models.MockIssue.content_key == i.content_key,
        models.MockIssue.status == "open")
    q = q.filter(models.MockIssue.qid.is_(None) if i.qid is None
                 else models.MockIssue.qid == i.qid)
    rows = {r.id: r for r in q.all()}
    rows[i.id] = i
    now = datetime.utcnow()
    note = (payload.note or "").strip()[:300] or None
    for r in rows.values():
        r.status = payload.status
        r.resolution_note = note
        r.resolved_by = user.full_name
        r.resolved_at = now
    audit.log(db, user, entity="mock_issue", action=payload.status,
              entity_id=i.id, entity_label=i.content_key,
              note=f"{i.qid or 'butun'} · {len(rows)} ta xabar"
                   + (f" · {note}" if note else ""))
    db.commit()
    return {"ok": True, "closed": len(rows), "status": payload.status}
