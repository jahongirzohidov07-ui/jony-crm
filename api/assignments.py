"""TOPSHIRIQLAR VA TEKSHIRISH (2026-09-18, Jahongir, 4- va 6-bandlar).

  * Ustoz dars rejasidan bir bosishda topshiriq yuboradi (lug'at testi,
    grammatika, uy vazifasi mashqlari, reading, writing, speaking).
  * AVTOMAT tekshiriladi: variantli (mcq), bo'sh joy (gap), T/F —
    bir nechta to'g'ri javob, katta-kichik harf, qisqartma va oddiy
    yozuv farqlari hisobga olinadi.
  * USTOZ tekshiradi: writing, speaking (audio), erkin javob — tayyor
    mezon (rubrika), tayyor izohlar, ovozli fikr; AI dastlabki tavsiya
    beradi, yakuniy bahoni ustoz tasdiqlaydi.
  * O'quvchi ilovasida avtomat paydo bo'ladi, natija ustoz kabinetiga
    qaytadi; Telegram xabar (agar bog'langan bo'lsa).
  * Audio 30 kundan keyin avtomat o'chiriladi (server joyi).
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
import re
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

import models
import notify
import roles
from auth import require_role
from database import get_db
from common import (_get_group_in_scope, _group_students, _student_of_user,
                    _sync_coin_entry, _teacher_of_user, scope_to_branch)
from liveplay import _lesson, build_questions

router = APIRouter()
TEACHER_APP_ROLES = (roles.TEACHER, roles.SUPPORT_TEACHER)

AUTO_KINDS = ("mcq", "gap", "tf")
RUBRICS = {
    "writing": [("Vazifa bajarilgan (mavzu grammatikasi ishlatilgan)", 3), ("Grammatika to'g'riligi", 3),
                ("Lug'at (dars so'zlari)", 2), ("Imlo va tinish belgilar", 2)],
    "speaking": [("Ravonlik va hajm", 3), ("Grammatika to'g'riligi", 3), ("Lug'at (dars so'zlari)", 2), ("Talaffuz", 2)],
    "free": [("To'g'rilik", 5), ("To'liqlik", 3), ("Imlo", 2)],
}
CANNED = [
    "Zo'r! Mavzu grammatikasi to'g'ri ishlatilgan 👏",
    "Yaxshi, lekin 3-shaxsda -s qo'shishni unutma (he goes).",
    "to be bilan fe'lni aralashtirma: 'I am go' emas, 'I go'.",
    "Past simple'da V2 shaklini tekshir (go → went).",
    "did dan keyin fe'l asosiy shaklda: 'Did you go?'.",
    "Vaqt ravishi gap oxirida: 'I went there yesterday'.",
    "Modal fe'ldan keyin 'to' yo'q: 'He must go'.",
    "Ko'proq dars lug'atidan foydalan — CORE so'zlardan kamida 5 tasi.",
    "Gaplar juda qisqa — bog'lovchilar (and, but, because) bilan birlashtir.",
    "Imloga e'tibor: bir nechta so'z xato yozilgan (pastda belgilangan).",
    "Talaffuz yaxshi, tezlikni biroz oshir.",
    "Qayta topshir: ko'rsatilgan xatolarni tuzatib yubor.",
]

# ---------------------------------------------------------------
#  Javobni solishtirish
# ---------------------------------------------------------------
_CONTR = {"isn't": "is not", "aren't": "are not", "wasn't": "was not", "weren't": "were not",
          "don't": "do not", "doesn't": "does not", "didn't": "did not", "can't": "cannot",
          "won't": "will not", "couldn't": "could not", "mustn't": "must not", "i'm": "i am",
          "he's": "he is", "she's": "she is", "it's": "it is", "they're": "they are",
          "we're": "we are", "you're": "you are", "i'll": "i will", "we'll": "we will",
          "i've": "i have", "there's": "there is", "that's": "that is"}


def norm(s: str) -> str:
    s = (s or "").strip().lower().replace("’", "'").replace("‘", "'").replace("`", "'")
    s = re.sub(r"\(.*?\)", "", s)                 # (izoh) olib tashlanadi
    s = re.sub(r"[.!?,;:\"«»]+$", "", s.strip())
    s = re.sub(r"^[\"«»]+", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    for k, v in _CONTR.items():
        s = re.sub(r"\b" + re.escape(k) + r"\b", v, s)
    return s


def alternatives(expected) -> list:
    if isinstance(expected, list):
        out = []
        for e in expected:
            out += alternatives(e)
        return out
    e = str(expected or "")
    parts = re.split(r"\s*(?:/|;|\bor\b|\byoki\b)\s*", e)
    # butun javob ('am / is' — ikki bo'sh joy) ham, har bir varianti ham qabul qilinadi
    return [x for x in [norm(e)] + [norm(p) for p in parts] if x]


def is_correct(kind: str, given, expected) -> bool:
    if kind == "mcq":
        try:
            return int(given) == int(expected)
        except (TypeError, ValueError):
            return False
    if kind == "tf":
        g = norm(str(given))
        if g in ("t", "true", "to'g'ri", "togri", "ha", "yes"):
            g = "t"
        elif g in ("f", "false", "noto'g'ri", "notogri", "yo'q", "no"):
            g = "f"
        return g[:1] == norm(str(expected))[:1]
    g = norm(str(given))
    return bool(g) and g in alternatives(expected)


def auto_grade(questions: list, answers: dict) -> dict:
    """answers: {"0": ..., "1": ...} -> {score, max, items:[{i, ok, given, answer}]}"""
    items, score, mx = [], 0, 0
    for i, q in enumerate(questions):
        if q.get("kind") not in AUTO_KINDS:
            continue
        mx += 1
        given = answers.get(str(i), answers.get(i))
        ok = is_correct(q["kind"], given, q.get("answer"))
        score += int(ok)
        items.append({"i": i, "ok": ok, "given": given, "answer": q.get("answer"), "explain": q.get("explain")})
    return {"score": score, "max": mx, "items": items}


# ---------------------------------------------------------------
#  Rejadan topshiriq tuzish
# ---------------------------------------------------------------
def _ex_to_questions(ex: dict) -> list:
    """Reja mashqi -> savollar. items+answers (ro'yxat) bo'lsa gap/tf, aks holda erkin."""
    items, answers = ex.get("items"), ex.get("answers")
    out = []
    if isinstance(items, list) and isinstance(answers, list) and len(items) == len(answers) \
            and all(isinstance(a, str) for a in answers):
        for it, a in zip(items, answers):
            a0 = a.strip()
            if re.fullmatch(r"[TF]\b.*", a0):
                out.append({"kind": "tf", "prompt": it, "answer": a0[0], "explain": a0})
            elif len(a0) <= 60:
                out.append({"kind": "gap", "prompt": it, "answer": a0, "explain": None})
            else:
                out.append({"kind": "text", "prompt": it, "answer": a0})
    else:
        out.append({"kind": "text", "prompt": ex.get("instr") or ex.get("title") or "",
                    "answer": answers if isinstance(answers, str) else "; ".join(answers or [])})
    return out


def _mcq(qs: list) -> list:
    return [{"kind": "mcq", "prompt": q["prompt"], "sub": q.get("sub"), "options": q["options"],
             "answer": q["correct"], "explain": q.get("explain")} for q in qs]


def _readings(L: dict) -> list:
    """Darsdagi barcha reading matnlari (2026-09-26). IELTS 5.0 da bitta
    darsda bir nechta "readings" bor, eskilarida bitta "reading" — avval
    faqat birligi o'qilardi, shuning uchun IELTS 5.0 da Reading
    topshirig'ini yuborib bo'lmasdi."""
    v = L.get("readings")
    if isinstance(v, list) and v:
        return v
    v = L.get("reading")
    return [v] if v else []


def build_from_plan(L: dict, part: str) -> Optional[dict]:
    """part: vocab | grammar | reading | reading:<i> | hw:<i> | class:<i>
    | writing | speaking"""
    no = L["no"]
    if part == "vocab":
        return {"kind": "vocab_test", "skill": "vocab", "title": f"{no}-dars — lug'at testi (CORE 20)",
                "questions": _mcq(build_questions(L, "vocab", 20))}
    if part == "grammar":
        try:
            qs = build_questions(L, "grammar", 20)
        except HTTPException:
            qs = []
        if len(qs) < 5:
            qs = build_questions(L, "mixed", 20)
        return {"kind": "grammar_test", "skill": "grammar", "title": f"{no}-dars — grammatika testi",
                "questions": _mcq(qs)}
    if part == "reading" or part.startswith("reading:"):
        rs = _readings(L)
        i = int(part.split(":")[1]) if ":" in part else 0
        if not (0 <= i < len(rs)):
            return None
        R = rs[i]
        qs = []
        for t in R.get("tasks", []):
            qs += _ex_to_questions(t)
        return {"kind": "reading", "skill": "reading", "title": f"{no}-dars — Reading: {R['title']}",
                "text": R.get("text"), "glossary": R.get("glossary"), "questions": qs}
    if part.startswith("hw:") or part.startswith("class:"):
        src = L["homework"] if part.startswith("hw:") else L["class_ex"]
        i = int(part.split(":")[1])
        if not (0 <= i < len(src)):
            return None
        ex = src[i]
        typ = ((ex.get("type") or "") + " " + (ex.get("title") or "")).lower()
        if "og'zaki" in typ or "speaking" in typ or "ovozli" in typ:
            return {"kind": "speaking", "skill": "speaking", "title": f"{no}-dars — {ex['title']}",
                    "questions": [{"kind": "audio", "prompt": ex.get("instr") or ex["title"], "answer": ""}],
                    "rubric": RUBRICS["speaking"]}
        if "yozma" in typ or "ijodiy" in typ or "writing" in typ or ("gap tuzish" in typ and not ex.get("items")):
            return {"kind": "writing", "skill": "writing", "title": f"{no}-dars — {ex['title']}",
                    "questions": [{"kind": "text", "prompt": ex.get("instr") or ex["title"],
                                   "answer": ex.get("answers") if isinstance(ex.get("answers"), str) else ""}],
                    "rubric": RUBRICS["writing"]}
        qs = _ex_to_questions(ex)
        auto = all(q["kind"] in AUTO_KINDS for q in qs)
        return {"kind": "homework" if auto else "free", "skill": "grammar",
                "title": f"{no}-dars — {ex['title']}", "instr": ex.get("instr"), "questions": qs,
                "rubric": None if auto else RUBRICS["free"]}
    if part in ("writing", "speaking"):
        keys = ("yozma", "ijodiy", "writing") if part == "writing" else ("og'zaki",)
        for i, h in enumerate(L.get("homework", [])):
            if any(k in ((h.get("type") or "") + (h.get("title") or "")).lower() for k in keys):
                return build_from_plan(L, f"hw:{i}")
    return None


def _public_q(q: dict) -> dict:
    return {k: v for k, v in q.items() if k != "answer"}


# ---------------------------------------------------------------
#  Umumiy chiqish shakllari
# ---------------------------------------------------------------
def _a_out(db, a, with_questions=False, hide_answers=True) -> dict:
    qs = json.loads(a.questions or "[]")
    out = {"id": a.id, "group_id": a.group_id, "student_id": a.student_id, "course": a.course,
           "lesson_no": a.lesson_no, "kind": a.kind, "skill": a.skill, "title": a.title,
           "instr": a.instr, "text": json.loads(a.text) if a.text else None,
           "auto": bool(a.auto), "due_at": a.due_at.isoformat() if a.due_at else None,
           "sent_at": a.sent_at.isoformat() if a.sent_at else None, "status": a.status,
           "rubric": json.loads(a.rubric) if a.rubric else None, "questions_count": len(qs),
           "max_score": a.max_score}
    if with_questions:
        out["questions"] = [_public_q(q) if hide_answers else q for q in qs]
    return out


def _s_out(s, a=None) -> dict:
    return {"id": s.id, "assignment_id": s.assignment_id, "student_id": s.student_id, "status": s.status,
            "attempt": s.attempt, "auto_score": s.auto_score, "auto_max": s.auto_max,
            "teacher_score": s.teacher_score, "max_score": (a.max_score if a else None),
            "rubric_scores": json.loads(s.rubric_scores) if s.rubric_scores else None,
            "comment": s.comment, "voice_media_id": s.voice_media_id,
            "ai_review": json.loads(s.ai_review) if s.ai_review else None,
            "submitted_at": s.submitted_at.isoformat() if s.submitted_at else None,
            "graded_at": s.graded_at.isoformat() if s.graded_at else None, "graded_by": s.graded_by,
            "coins": s.coins or 0, "text": s.text, "transcript": s.transcript,
            "media_id": s.media_id, "result": json.loads(s.result) if s.result else None}


def _tg(student, text):
    try:
        if getattr(student, "telegram_chat_id", None) and notify.enabled():
            notify.send(student.telegram_chat_id, text)
    except Exception:
        pass


# ---------------------------------------------------------------
#  USTOZ: yuborish
# ---------------------------------------------------------------
class FromPlanIn(BaseModel):
    course: str
    lesson_no: int
    parts: list                      # ["vocab", "grammar", "hw:2", "writing", ...]
    due_days: int = 2
    lesson_id: Optional[int] = None
    student_ids: Optional[list] = None   # bo'sh = butun guruh


@router.get("/api/plans/{course}/{no}/assignable")
def assignable(course: str, no: int, user=Depends(require_role(*roles.TEACHING_ACCESS))):
    """Rejadan yuborish mumkin bo'lgan qismlar ro'yxati (tugmalar uchun)."""
    L = _lesson(course, no)
    out = [{"part": "vocab", "label": "Lug'at testi (CORE 20) — avtomat", "auto": True},
           {"part": "grammar", "label": "Grammatika testi — avtomat", "auto": True}]
    for i, R in enumerate(_readings(L)):
        part = "reading" if i == 0 else f"reading:{i}"   # eski linklar buzilmasin
        b = build_from_plan(L, part)
        if not b:
            continue
        out.append({"part": part, "label": f"Reading: {R.get('title') or i + 1}",
                    "auto": bool(all(q["kind"] in AUTO_KINDS
                                     for q in b["questions"]))})
    for i, h in enumerate(L.get("homework", [])):
        b = build_from_plan(L, f"hw:{i}")
        if b:
            out.append({"part": f"hw:{i}", "label": f"Uyga vazifa {i + 1}: {h['title']}",
                        "auto": all(q["kind"] in AUTO_KINDS for q in b["questions"]), "kind": b["kind"]})
    return out


@router.post("/api/groups/{gid}/assignments/from-plan")
def send_from_plan(gid: int, body: FromPlanIn, db: Session = Depends(get_db),
                   user=Depends(require_role(*roles.TEACHING_ACCESS))):
    g = _get_group_in_scope(db, gid, user)
    L = _lesson(body.course, body.lesson_no)
    due = datetime.utcnow() + timedelta(days=max(0, min(30, body.due_days)))
    created = []
    studs = [s for s in _group_students(db, g.id) if (s.status or "active") in ("active", "trial")]
    if body.student_ids:
        studs = [s for s in studs if s.id in set(body.student_ids)]
    for part in body.parts:
        if not isinstance(part, str):
            continue
        b = build_from_plan(L, part)
        if not b or not b.get("questions"):
            continue
        auto = all(q["kind"] in AUTO_KINDS for q in b["questions"])
        mx = (len([q for q in b["questions"] if q["kind"] in AUTO_KINDS]) if auto
              else sum(p for _, p in (b.get("rubric") or RUBRICS["free"])))
        a = models.Assignment(
            group_id=g.id, lesson_id=body.lesson_id, course=body.course, lesson_no=body.lesson_no,
            student_id=(studs[0].id if body.student_ids and len(studs) == 1 else None),
            kind=b["kind"], skill=b["skill"], title=b["title"], instr=b.get("instr"),
            text=(json.dumps({"text": b.get("text"), "glossary": b.get("glossary")}, ensure_ascii=False)
                  if b.get("text") else None),
            questions=json.dumps(b["questions"], ensure_ascii=False), auto=1 if auto else 0,
            rubric=json.dumps(b.get("rubric"), ensure_ascii=False) if b.get("rubric") else None,
            max_score=float(mx), due_at=due, sent_at=datetime.utcnow(), status="sent",
            created_by=user.full_name, targets=json.dumps([s.id for s in studs]))
        db.add(a)
        db.flush()
        created.append(a)
    db.commit()
    if created:
        for s in studs:
            _tg(s, f"📚 Yangi topshiriq ({g.name}): " + "; ".join(a.title for a in created)
                + f"\nMuddat: {due.date().isoformat()}. Jony Student → Darslar.")
    return [_a_out(db, a) for a in created]


@router.get("/api/groups/{gid}/assignments")
def group_assignments(gid: int, db: Session = Depends(get_db),
                      user=Depends(require_role(*roles.TEACHING_ACCESS))):
    g = _get_group_in_scope(db, gid, user)
    rows = (db.query(models.Assignment).filter(models.Assignment.group_id == g.id)
            .order_by(models.Assignment.id.desc()).limit(60).all())
    out = []
    for a in rows:
        subs = db.query(models.AssignmentSubmission).filter(models.AssignmentSubmission.assignment_id == a.id).all()
        d = _a_out(db, a)
        d["targets"] = len(json.loads(a.targets or "[]"))
        d["submitted"] = len({s.student_id for s in subs if s.status in ("submitted", "graded", "returned")})
        d["graded"] = len({s.student_id for s in subs if s.status == "graded"})
        d["pending"] = sum(1 for s in subs if s.status == "submitted" and not a.auto)
        out.append(d)
    return out


@router.get("/api/assignments/{aid}")
def assignment_detail(aid: int, db: Session = Depends(get_db),
                      user=Depends(require_role(*roles.TEACHING_ACCESS))):
    a = db.query(models.Assignment).get(aid)
    if not a:
        raise HTTPException(404, "Topshiriq topilmadi")
    _get_group_in_scope(db, a.group_id, user)
    names = {s.id: s.full_name for s in _group_students(db, a.group_id)}
    subs = (db.query(models.AssignmentSubmission).filter(models.AssignmentSubmission.assignment_id == a.id)
            .order_by(models.AssignmentSubmission.id).all())
    by = {s.student_id: s for s in subs}       # oxirgi urinish
    rows = [{"student_id": sid, "name": names.get(sid, "?"), "submission": _s_out(by[sid], a) if sid in by else None}
            for sid in json.loads(a.targets or "[]")]
    d = _a_out(db, a, with_questions=True, hide_answers=False)
    d["rows"] = rows
    return d


@router.get("/api/teacher/checks")
def teacher_checks(db: Session = Depends(get_db), user=Depends(require_role(*roles.TEACHING_ACCESS))):
    """Tekshirishni kutayotgan writing/speaking/erkin ishlar (mening guruhlarim)."""
    q = (db.query(models.AssignmentSubmission, models.Assignment)
         .join(models.Assignment, models.AssignmentSubmission.assignment_id == models.Assignment.id)
         .filter(models.AssignmentSubmission.status == "submitted", models.Assignment.auto == 0))
    if user.role in TEACHER_APP_ROLES:
        t = _teacher_of_user(db, user)
        if not t:
            return []
        gids = [g.id for g in db.query(models.Group).filter(models.Group.teacher_id == t.id).all()]
    else:
        gids = [g.id for g in scope_to_branch(db.query(models.Group), models.Group, user).all()]
    q = q.filter(models.Assignment.group_id.in_(gids or [-1]))
    out = []
    for s, a in q.order_by(models.AssignmentSubmission.submitted_at).limit(100).all():
        st = db.query(models.Student).get(s.student_id)
        g = db.query(models.Group).get(a.group_id)
        out.append({"submission_id": s.id, "assignment_id": a.id, "title": a.title, "kind": a.kind,
                    "student": st.full_name if st else "?", "group": g.name if g else "?",
                    "submitted_at": s.submitted_at.isoformat() if s.submitted_at else None,
                    "has_ai": bool(s.ai_review)})
    return out


# ---------------------------------------------------------------
#  USTOZ: tekshirish
# ---------------------------------------------------------------
class GradeIn(BaseModel):
    score: float
    rubric_scores: Optional[dict] = None
    comment: Optional[str] = None
    voice: Optional[str] = None          # base64 data URL
    voice_mime: Optional[str] = None
    return_for_fix: bool = False         # qayta topshirishga qaytarish


def _sub_in_scope(db, sid, user):
    s = db.query(models.AssignmentSubmission).get(sid)
    if not s:
        raise HTTPException(404, "Ish topilmadi")
    a = db.query(models.Assignment).get(s.assignment_id)
    _get_group_in_scope(db, a.group_id, user)
    return s, a


@router.get("/api/submissions/{sid}")
def submission_detail(sid: int, db: Session = Depends(get_db),
                      user=Depends(require_role(*roles.TEACHING_ACCESS))):
    s, a = _sub_in_scope(db, sid, user)
    st = db.query(models.Student).get(s.student_id)
    d = _s_out(s, a)
    d["student"] = st.full_name if st else "?"
    d["assignment"] = _a_out(db, a, with_questions=True, hide_answers=False)
    d["answers"] = json.loads(s.answers or "{}")
    d["canned"] = CANNED
    d["rubric"] = json.loads(a.rubric) if a.rubric else RUBRICS["free"]
    try:
        L = _lesson(a.course, a.lesson_no)
        d["lesson_mistakes"] = (L.get("grammar") or {}).get("mistakes", [])[:8]
    except HTTPException:
        d["lesson_mistakes"] = []
    return d


@router.get("/api/media/{mid}")
def get_media(mid: int, db: Session = Depends(get_db),
              user=Depends(require_role(*roles.TEACHING_ACCESS, roles.STUDENT))):
    m = db.query(models.AssignmentMedia).get(mid)
    if not m:
        raise HTTPException(404, "Audio topilmadi (30 kundan keyin o'chiriladi)")
    if user.role == roles.STUDENT:
        st = _student_of_user(db, user)
        if not st or (m.student_id and m.student_id != st.id):
            raise HTTPException(403, "Ruxsat yo'q")
    return {"id": m.id, "mime": m.mime, "data": m.data}


def _save_media(db, *, student_id, submission_id, kind, data, mime) -> Optional[int]:
    if not data:
        return None
    if len(data) > 8_000_000:
        raise HTTPException(400, "Audio juda katta (maks. ~5 MB)")
    m = models.AssignmentMedia(student_id=student_id, submission_id=submission_id, kind=kind,
                               mime=mime or "audio/webm", data=data, created_at=datetime.utcnow())
    db.add(m)
    db.flush()
    return m.id


def purge_old_media(db) -> int:
    """30 kundan eski audio — o'chiriladi (server joyi)."""
    cut = datetime.utcnow() - timedelta(days=30)
    n = db.query(models.AssignmentMedia).filter(models.AssignmentMedia.created_at < cut).delete(synchronize_session=False)
    db.commit()
    return int(n or 0)


@router.post("/api/submissions/{sid}/grade")
def grade_submission(sid: int, body: GradeIn, db: Session = Depends(get_db),
                     user=Depends(require_role(*roles.TEACHING_ACCESS))):
    s, a = _sub_in_scope(db, sid, user)
    mx = float(a.max_score or 10)
    score = max(0.0, min(mx, float(body.score)))
    s.teacher_score = score
    s.rubric_scores = json.dumps(body.rubric_scores, ensure_ascii=False) if body.rubric_scores else None
    s.comment = (body.comment or "")[:2000] or None
    if body.voice:
        s.voice_media_id = _save_media(db, student_id=s.student_id, submission_id=s.id, kind="voice",
                                       data=body.voice, mime=body.voice_mime)
    s.status = "returned" if body.return_for_fix else "graded"
    s.graded_at, s.graded_by = datetime.utcnow(), user.full_name
    pct = score / mx * 100 if mx else 0
    coins = 2 if (pct >= 90 and not body.return_for_fix) else 0   # ustoz bahosi 90%+ — 2 coin
    s.coins = coins
    _sync_coin_entry(db, student_id=s.student_id, source="assignment", ref_id=s.id, amount=coins,
                     note=f"Topshiriq: {a.title} — {round(pct)}%", created_by=user.full_name)
    db.commit()
    st = db.query(models.Student).get(s.student_id)
    if st:
        _tg(st, (f"✅ Tekshirildi: {a.title} — {score:g}/{mx:g}" if not body.return_for_fix
                 else f"↩️ Qayta topshiring: {a.title}") + (f"\nIzoh: {s.comment}" if s.comment else ""))
    return _s_out(s, a)


@router.post("/api/submissions/{sid}/ai-review")
def ai_review(sid: int, db: Session = Depends(get_db), user=Depends(require_role(*roles.TEACHING_ACCESS))):
    """AI dastlabki tavsiya: xatolar + taxminiy ball. Yakuniy — ustoz."""
    s, a = _sub_in_scope(db, sid, user)
    text = s.transcript or s.text or ""
    if not text.strip():
        raise HTTPException(400, "Matn yo'q")
    L = None
    try:
        L = _lesson(a.course, a.lesson_no)
        topic = L.get("grammar_topic") or L["title"]
        core = ", ".join(e[0] for e in (L.get("vocab") or {}).get("core", [])[:20])
    except HTTPException:
        topic, core = "", ""
    rub = json.loads(a.rubric) if a.rubric else RUBRICS["free"]
    review = None
    try:
        from student_app import _ai_reply
        sysmsg = ("You are an English teacher at an Uzbek language school. Check an A1-level student's work. "
                  "Return ONLY JSON: {\"score\": number, \"max\": number, "
                  "\"errors\": [{\"wrong\": str, \"right\": str, \"why_uz\": str}], \"comment_uz\": str}. "
                  "Score by rubric criteria (name, points): " + json.dumps(rub, ensure_ascii=False)
                  + f". Target grammar: {topic}. Lesson vocabulary: {core}. Explanations in Uzbek (Latin).")
        raw = _ai_reply(sysmsg, [{"role": "user", "text": f"Task: {a.title}\nStudent text:\n{text[:3000]}"}],
                        max_tokens=700)
        m = re.search(r"\{.*\}", raw or "", re.S)
        review = json.loads(m.group(0)) if m else None
    except Exception:
        review = None
    if not review:
        words = len(re.findall(r"[A-Za-z']+", text))
        errs = []
        for wrong, right, why in ((L or {}).get("grammar") or {}).get("mistakes", []):
            key = re.sub(r"[^a-z' ]", "", wrong.lower()).strip()
            if key and key in text.lower():
                errs.append({"wrong": wrong, "right": right, "why_uz": why})
        review = {"score": None, "max": float(a.max_score or 10), "errors": errs, "heuristic": True,
                  "comment_uz": f"{words} ta so'z. " + (f"{len(errs)} ta tipik xato topildi." if errs
                                                        else "Dars xatolar ro'yxatidan mos shakl topilmadi.")}
    s.ai_review = json.dumps(review, ensure_ascii=False)
    db.commit()
    return review


# ---------------------------------------------------------------
#  O'QUVCHI
# ---------------------------------------------------------------
def _me(db, user):
    st = _student_of_user(db, user)
    if not st:
        raise HTTPException(403, "O'quvchi hisobi topilmadi")
    return st


def _visible(a, st) -> bool:
    if a.student_id and a.student_id != st.id:
        return False
    tg = json.loads(a.targets or "[]")
    return (not tg) or (st.id in tg)


def _last_sub(db, a, st):
    return (db.query(models.AssignmentSubmission)
            .filter(models.AssignmentSubmission.assignment_id == a.id, models.AssignmentSubmission.student_id == st.id)
            .order_by(models.AssignmentSubmission.id.desc()).first())


def _cards(L) -> list:
    return [{"w": e[0], "uz": e[1], "ex": e[2] if len(e) > 2 else "", "ipa": e[4] if len(e) > 4 else ""}
            for e in (L.get("vocab") or {}).get("core", [])]


@router.get("/api/student/assignments")
def my_assignments(db: Session = Depends(get_db), user=Depends(require_role(roles.STUDENT))):
    st = _me(db, user)
    items = []
    if st.group_id:
        q = (db.query(models.Assignment)
             .filter(models.Assignment.group_id == st.group_id, models.Assignment.status == "sent")
             .order_by(models.Assignment.id.desc()).limit(60))
        for a in q.all():
            if not _visible(a, st):
                continue
            s = _last_sub(db, a, st)
            d = _a_out(db, a)
            d["submission"] = _s_out(s, a) if s else None
            d["overdue"] = bool(a.due_at and a.due_at < datetime.utcnow() and not s)
            items.append(d)
    # Bugungi dars mavzusi + lug'at kartochkalari
    today = {}
    plan = db.query(models.GroupPlan).filter(models.GroupPlan.group_id == st.group_id).first() if st.group_id else None
    if plan:
        run = (db.query(models.LessonRun).filter(models.LessonRun.group_id == st.group_id,
                                                 models.LessonRun.status == "running")
               .order_by(models.LessonRun.id.desc()).first())
        no = run.lesson_no if run else plan.next_lesson_no   # dars ketayotgan bo'lsa — o'sha, aks holda keyingi
        try:
            L = _lesson(plan.course, no)
            today = {"lesson_no": no, "title": L["title"], "grammar": L.get("grammar_topic"),
                     "vocab_topic": L.get("vocab_topic"), "cards": _cards(L),
                     "homework": [h["title"] for h in L.get("homework", [])],
                     "formulas": (L.get("grammar") or {}).get("formulas", [])[:4]}
        except HTTPException:
            pass
    # Qoldirilgan dars paketi
    missed = None
    if st.group_id:
        last = (db.query(models.Lesson).filter(models.Lesson.group_id == st.group_id, models.Lesson.held == 1)
                .order_by(models.Lesson.date.desc()).first())
        if last:
            att = db.query(models.Attendance).filter(models.Attendance.lesson_id == last.id,
                                                     models.Attendance.student_id == st.id).first()
            run = db.query(models.LessonRun).filter(models.LessonRun.lesson_id == last.id).first() if (att and att.present == 0) else None
            if run:
                try:
                    L = _lesson(run.course, run.lesson_no)
                    missed = {"date": last.date.isoformat(), "lesson_no": run.lesson_no, "title": L["title"],
                              "course": run.course, "grammar_intro": (L.get("grammar") or {}).get("intro", [])[:4],
                              "formulas": (L.get("grammar") or {}).get("formulas", []), "cards": _cards(L),
                              "homework": [h["title"] for h in L.get("homework", [])]}
                except HTTPException:
                    pass
    return {"items": items, "today": today, "missed": missed,
            "pending": sum(1 for i in items if not i["submission"] or i["submission"]["status"] == "returned"),
            "graded_new": sum(1 for i in items if i["submission"] and i["submission"]["status"] == "graded"
                              and i["submission"]["graded_by"] != "Avtomat")}


@router.post("/api/student/assignments/missed-test")
def missed_test(db: Session = Depends(get_db), user=Depends(require_role(roles.STUDENT))):
    """Qoldirilgan dars paketi: shu darsning lug'at testi shaxsiy topshiriq bo'lib ochiladi."""
    st = _me(db, user)
    m = my_assignments(db, user).get("missed")
    if not m:
        raise HTTPException(400, "Qoldirilgan dars yo'q")
    L = _lesson(m["course"], m["lesson_no"])
    b = build_from_plan(L, "vocab")
    a = models.Assignment(group_id=st.group_id, student_id=st.id, course=m["course"], lesson_no=m["lesson_no"],
                          kind="vocab_test", skill="vocab", title=f"Qoldirilgan {m['lesson_no']}-dars — lug'at testi",
                          questions=json.dumps(b["questions"], ensure_ascii=False), auto=1,
                          max_score=float(len(b["questions"])), due_at=datetime.utcnow() + timedelta(days=3),
                          sent_at=datetime.utcnow(), status="sent", created_by="Tizim", targets=json.dumps([st.id]))
    db.add(a)
    db.commit()
    return _a_out(db, a)


@router.get("/api/student/assignments/{aid}")
def my_assignment(aid: int, db: Session = Depends(get_db), user=Depends(require_role(roles.STUDENT))):
    st = _me(db, user)
    a = db.query(models.Assignment).get(aid)
    if not a or a.group_id != st.group_id or not _visible(a, st):
        raise HTTPException(404, "Topshiriq topilmadi")
    s = _last_sub(db, a, st)
    done = bool(s and s.status in ("submitted", "graded"))
    d = _a_out(db, a, with_questions=True, hide_answers=not done)
    d["submission"] = _s_out(s, a) if s else None
    if s:
        d["answers"] = json.loads(s.answers or "{}")
    return d


class SubmitIn(BaseModel):
    answers: Optional[dict] = None       # {"0": 2, "1": "am", ...}
    text: Optional[str] = None
    audio: Optional[str] = None          # base64 data URL
    mime: Optional[str] = None
    transcript: Optional[str] = None


@router.post("/api/student/assignments/{aid}/submit")
def submit(aid: int, body: SubmitIn, db: Session = Depends(get_db), user=Depends(require_role(roles.STUDENT))):
    st = _me(db, user)
    a = db.query(models.Assignment).get(aid)
    if not a or a.group_id != st.group_id or not _visible(a, st):
        raise HTTPException(404, "Topshiriq topilmadi")
    qs = json.loads(a.questions or "[]")
    prev = (db.query(models.AssignmentSubmission)
            .filter(models.AssignmentSubmission.assignment_id == a.id, models.AssignmentSubmission.student_id == st.id)
            .all())
    last = max(prev, key=lambda p: p.id) if prev else None
    if last and last.status in ("submitted", "graded") and not a.auto:
        raise HTTPException(400, "Bu ish allaqachon topshirilgan")
    if last and last.status == "submitted" and a.auto:
        raise HTTPException(400, "Bu ish allaqachon topshirilgan")
    attempt = len(prev) + 1
    s = models.AssignmentSubmission(assignment_id=a.id, student_id=st.id, attempt=attempt,
                                    answers=json.dumps(body.answers or {}, ensure_ascii=False),
                                    text=(body.text or "")[:6000] or None,
                                    transcript=(body.transcript or "")[:3000] or None,
                                    status="submitted", submitted_at=datetime.utcnow())
    db.add(s)
    db.flush()
    if body.audio:
        s.media_id = _save_media(db, student_id=st.id, submission_id=s.id, kind="audio", data=body.audio, mime=body.mime)
        if not s.transcript:
            try:
                from student_app import _sp_stt
                s.transcript = _sp_stt(body.audio, body.mime or "audio/webm")[:3000]
            except Exception:
                pass
    if a.auto:
        res = auto_grade(qs, body.answers or {})
        s.auto_score, s.auto_max = float(res["score"]), float(res["max"])
        s.result = json.dumps(res, ensure_ascii=False)
        s.status, s.graded_at, s.graded_by = "graded", datetime.utcnow(), "Avtomat"
        coins = 1 if (attempt == 1 and res["max"] and res["score"] == res["max"]) else 0   # 100% birinchi urinish — 1 coin
        s.coins = coins
        if coins:
            _sync_coin_entry(db, student_id=st.id, source="assignment", ref_id=s.id, amount=coins,
                             note=f"Topshiriq 100%: {a.title}", created_by="Tizim")
    db.commit()
    if body.audio:
        purge_old_media(db)
    d = _s_out(s, a)
    if a.auto:
        d["review"] = [{"i": it["i"], "prompt": qs[it["i"]]["prompt"], "ok": it["ok"], "given": it["given"],
                        "answer": (qs[it["i"]]["options"][it["answer"]] if qs[it["i"]]["kind"] == "mcq" else it["answer"]),
                        "explain": it.get("explain")} for it in res["items"]]
    return d
