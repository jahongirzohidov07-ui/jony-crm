"""ONLINE TEST — LINK ORQALI (2026-09-18).

Jahongir: "guruhga test biriktirganda unit midterm yoki end of course
link paydo bo'lsin shu linkni examiner telegramdan tashlab bersa
o'quvchilar kirib baholay olsin natijalar to'g'ridan to'g'ri guruhga
biriktirilgan exam natijalarga tushaversin ismi familyasi xato yoki
yangi o'quvchilar bo'lsa qizil chiziqdan pastdan alohida ko'rinsin
examiner uni to'g'irlasa o'z o'rniga tushib qolsin".

  - Test bazasi (ExamTemplate): daraja + tur + unit bo'yicha savollar.
    Examinerlar boshlig'i tahrirlaydi, examinerlar ko'radi.
  - Guruh testiga link (ExamOnline): savollar link ochilgan paytda
    nusxalanadi. Link ochiq/yopiq bo'ladi.
  - O'quvchi ro'yxatdan o'zini tanlaydi (yo'q bo'lsa ismini yozadi),
    kameradan rasm oladi, testni yechadi — server tekshiradi.
  - Ro'yxatdan tanlangan natija guruh testidagi o'z qatoriga tushadi
    (exams._apply_exam_marks: foiz, coin, XP, sertifikat — qo'lda
    kiritish bilan bir xil). Qolganlari "pending" — examiner
    biriktiradi.
  - Writing + Speaking qog'ozda: paper_max > 0 bo'lsa natija qog'oz
    bali kiritilgandagina yoziladi (yarim ball bilan coin berilmaydi).
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import re
import secrets
import time
from datetime import datetime, timedelta
from types import SimpleNamespace
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session, undefer

import audit
import models
import roles
import schemas
import exams as _exams
from auth import require_role
from database import get_db
from common import _group_students, _get_group_in_scope, _seed_done, _seed_mark

router = APIRouter()

# Natija kirita oladiganlar (exams.save_exam_results bilan bir xil)
RESULT_ROLES = [r for r in roles.TEACHING_ACCESS
                if r not in (roles.TEACHER, roles.SUPPORT_TEACHER)]
# Natijalarni TASDIQLAYDI (e'lon qiladi) — examiner tomoni (2026-09-18)
PUBLISH_ROLES = list(dict.fromkeys(roles.EXAM_ACCESS + roles.EXAM_EDIT))

PHOTO_MAX_CHARS = 400_000          # ~300KB rasm (frontend 480px ga kichraytiradi)
_HITS: dict = {}
_MAX_PER_HOUR = 300                # bitta sinf bitta Wi-Fi (bitta IP) dan kiradi
COUNTDOWN_SEC = 10                 # "Start"dan keyin teskari sanoq
AWAY_LIMIT_DEFAULT = 5             # sahifadan chiqishga ruxsat (undan keyin chetlatiladi)
GRACE_SEC = 90                     # vaqt tugagach avtomatik topshirish muhlati


def timer_state(o) -> str:
    """waiting — examiner hali Start bosmagan; countdown — teskari sanoq;
    running — savollar ochiq; finished — vaqt tugadi."""
    if not o or not o.started_at or not o.ends_at:
        return "waiting"
    now = datetime.utcnow()
    if now < o.started_at:
        return "countdown"
    if now < o.ends_at:
        return "running"
    return "finished"


def _iso(d):
    # Server vaqti UTC — brauzer to'g'ri hisoblashi uchun "Z" bilan
    return d.isoformat() + "Z" if d else None


# ------------------------------------------------------------- yordamchi
def _norm(s) -> str:
    """Matnli javobni solishtirish uchun: kichik harf, faqat harf va
    raqam ("the USA" = "theusa", "he SA" = "hesa")."""
    s = str(s or "").lower().replace("’", "'").replace("‘", "'")
    return re.sub(r"[^0-9a-zа-яёўқғҳ]", "", s)


def _load(txt) -> list:
    try:
        v = json.loads(txt or "[]")
        return v if isinstance(v, list) else []
    except Exception:
        return []


def _questions(parts: list):
    for p in parts:
        for q in p.get("questions") or []:
            yield q


IMAGE_MAX_CHARS = 300_000          # savol rasmi (data URL) ~220KB


def _clean_image(v, where: str):
    """Savol rasmi: yuklangan (data:image/…) yoki loyihadagi statik fayl
    (/exam-img/…). Boshqa manzilga ruxsat yo'q — begona sayt rasmi
    o'quvchi sahifasiga tushmasin."""
    v = str(v or "").strip()
    if not v:
        return None
    if v.startswith("/exam-img/") and ".." not in v:
        return v
    if v.startswith("data:image/") and len(v) <= IMAGE_MAX_CHARS:
        return v
    raise HTTPException(400, f"{where}: rasm noto'g'ri yoki juda katta")


def clean_parts(parts) -> list:
    """Test bazasidan kelgan bo'limlarni tekshiradi va savollarni
    1 dan boshlab raqamlaydi. Xato bo'lsa 400."""
    if not isinstance(parts, list) or not parts:
        raise HTTPException(400, "Kamida bitta bo'lim bo'lishi kerak")
    out, n, seen = [], 0, set()
    for pi, p in enumerate(parts):
        if not isinstance(p, dict):
            raise HTTPException(400, "Bo'lim noto'g'ri")
        qs = []
        for q in p.get("questions") or []:
            n += 1
            typ = q.get("type") or "choice"
            text = str(q.get("q") or "").strip()
            qid = str(q.get("id") or "").strip() or f"q{n}"
            while qid in seen:
                qid = f"{qid}_{n}"
            seen.add(qid)
            item = {"id": qid, "n": n, "type": typ, "q": text}
            img = _clean_image(q.get("image"), f"{n}-savol")
            if img:
                item["image"] = img
            if typ == "choice":
                opts = [str(o).strip() for o in (q.get("options") or [])
                        if str(o).strip()]
                if len(opts) < 2:
                    raise HTTPException(
                        400, f"{n}-savol: kamida 2 ta variant kerak")
                a = q.get("answer")
                if not isinstance(a, int) or not (0 <= a < len(opts)):
                    raise HTTPException(
                        400, f"{n}-savol: to'g'ri variant belgilanmagan")
                item["options"] = opts
                item["answer"] = a
            elif typ == "text":
                ans = q.get("answer")
                if isinstance(ans, str):
                    ans = [x for x in re.split(r"[/;\n]", ans)]
                ans = [str(x).strip() for x in (ans or []) if str(x).strip()]
                if not ans:
                    raise HTTPException(
                        400, f"{n}-savol: to'g'ri javob yozilmagan")
                item["answer"] = ans
            else:
                raise HTTPException(400, f"{n}-savol: noma'lum tur")
            qs.append(item)
        out.append({
            "title": str(p.get("title") or f"Part {pi + 1}").strip(),
            "instructions": str(p.get("instructions") or "").strip(),
            "passage": str(p.get("passage") or "").strip(),
            "audio_url": (str(p.get("audio_url") or "").strip() or None),
            # Bo'lim rasmi — masalan A–G kasblar jadvali (2026-09-18)
            "image": _clean_image(p.get("image"), p.get("title") or "Bo'lim"),
            "questions": qs,
        })
    if n == 0:
        raise HTTPException(400, "Kamida bitta savol bo'lishi kerak")
    return out


def public_parts(parts: list) -> list:
    """O'quvchiga boradigan nusxa — to'g'ri javoblarsiz."""
    out = []
    for p in parts:
        out.append({
            **{k: p.get(k) for k in ("title", "instructions", "passage",
                                     "audio_url", "image")},
            "questions": [{k: q.get(k) for k in ("id", "n", "type", "q",
                                                 "options", "image")}
                          for q in p.get("questions") or []],
        })
    return out


def grade(parts: list, answers: dict):
    """(ball, maksimal, tafsilot). Har savol 1 ball."""
    score, total, detail = 0, 0, []
    for q in _questions(parts):
        total += 1
        given = answers.get(q["id"])
        if q["type"] == "choice":
            try:
                ok = given is not None and int(given) == int(q["answer"])
            except (TypeError, ValueError):
                ok = False
        else:
            g = _norm(given)
            ok = bool(g) and any(g == _norm(a) for a in q["answer"])
        score += 1 if ok else 0
        detail.append({"id": q["id"], "n": q["n"], "ok": ok,
                       "given": None if given is None else str(given)[:200]})
    return float(score), float(total), detail


def _system_user():
    return SimpleNamespace(id=None, role="system", full_name="Online test")


def _roster(db: Session, group_id: int) -> list:
    return [s for s in _group_students(db, group_id)
            if (s.status or "active") in ("active", "trial", "frozen")] \
        or list(_group_students(db, group_id))


def _write_result(db: Session, exam: models.Exam, online: models.ExamOnline,
                  sub: models.ExamSubmission, user) -> None:
    """Joylashtirilgan topshiriqni guruh testining natijasiga yozadi.
    Qog'oz qismi bor, lekin hali kiritilmagan bo'lsa — kutadi."""
    if not sub.student_id or sub.status != "placed":
        return
    if not online.published_at:
        return          # examiner hali tasdiqlamagan
    if (online.paper_max or 0) > 0 and sub.paper_score is None:
        return
    total = (sub.online_score or 0) + (sub.paper_score or 0)
    _exams._apply_exam_marks(db, exam, schemas.ExamScoreBulk(marks=[
        schemas.ExamScoreMark(student_id=sub.student_id, score=total,
                              absent=False)]), user)


def _place(db: Session, exam, online, sub, student_id: int, user) -> None:
    """Topshiriqni o'quvchiga biriktiradi. Shu o'quvchining avvalgi
    joylashgan topshirig'i "replaced" bo'ladi."""
    for old in (db.query(models.ExamSubmission)
                .filter(models.ExamSubmission.exam_id == exam.id,
                        models.ExamSubmission.student_id == student_id,
                        models.ExamSubmission.status == "placed",
                        models.ExamSubmission.id != sub.id).all()):
        old.status = "replaced"
        if sub.paper_score is None:
            sub.paper_score = old.paper_score
    sub.student_id = student_id
    sub.status = "placed"
    sub.placed_by = user.full_name
    sub.placed_at = datetime.utcnow()
    db.commit()
    _write_result(db, exam, online, sub, user)


def bank_max(db: Session, group, kind: str, unit_no=None):
    """Test bazasidagi mos testning maksimal bali (savollar soni +
    qog'oz qismi). Guruh darajasi, tur va unit bo'yicha; topilmasa None.
    (2026-09-18, Jahongir: "xamma biriktirilgan test unitlarini
    maksimal ballini test soniga qarab o'zing belgilab chiq")"""
    if kind not in ("unit", "mid", "end") or not group or not group.level:
        return None
    q = db.query(models.ExamTemplate).filter(
        models.ExamTemplate.is_active == 1,
        models.ExamTemplate.level == group.level,
        models.ExamTemplate.kind == kind)
    if kind == "unit":
        if not unit_no:
            return None
        q = q.filter(models.ExamTemplate.unit_no == unit_no)
    t = q.order_by(models.ExamTemplate.id).first()
    if not t:
        return None
    n = sum(1 for _ in _questions(_load(t.parts)))
    return float(n) + float(t.paper_max or 0)


def _exam_open_for_results(exam: models.Exam) -> bool:
    return (exam.status or "done") in ("approved", "done")


# ------------------------------------------------------------ test bazasi
class TemplateIn(BaseModel):
    level: Optional[str] = None
    kind: str = "unit"
    unit_no: Optional[int] = None
    title: str
    parts: list
    paper_max: float = 0
    is_active: bool = True


def _tpl_summary(t: models.ExamTemplate) -> dict:
    parts = _load(t.parts)
    return {
        "id": t.id, "level": t.level, "kind": t.kind, "unit_no": t.unit_no,
        "title": t.title, "paper_max": t.paper_max or 0,
        "q_count": sum(1 for _ in _questions(parts)),
        "is_active": bool(t.is_active),
        "updated_at": t.updated_at.isoformat() if t.updated_at else None,
    }


def _validate_tpl(p: TemplateIn):
    if p.kind not in ("unit", "mid", "end"):
        raise HTTPException(400, "Online test faqat Unit, Mid-course va "
                                 "End of course uchun")
    if p.kind == "unit" and not (p.unit_no and 1 <= p.unit_no <= roles.UNIT_COUNT):
        raise HTTPException(400, f"Unit raqami 1-{roles.UNIT_COUNT} oralig'ida")
    if p.level and p.level not in roles.ALL_LEVELS:
        raise HTTPException(400, "Noto'g'ri daraja")
    if p.paper_max < 0 or p.paper_max > 500:
        raise HTTPException(400, "Writing/Speaking bali noto'g'ri")
    if not p.title.strip():
        raise HTTPException(400, "Nomini yozing")


@router.get("/api/exam-templates")
def list_templates(level: Optional[str] = None, kind: Optional[str] = None,
                   db: Session = Depends(get_db),
                   user=Depends(require_role(*RESULT_ROLES))):
    q = db.query(models.ExamTemplate)
    if level:
        q = q.filter(models.ExamTemplate.level == level)
    if kind:
        q = q.filter(models.ExamTemplate.kind == kind)
    rows = q.order_by(models.ExamTemplate.level, models.ExamTemplate.kind,
                      models.ExamTemplate.unit_no).all()
    return [_tpl_summary(t) for t in rows]


@router.get("/api/exam-templates/{tid}")
def get_template(tid: int, db: Session = Depends(get_db),
                 user=Depends(require_role(*roles.EXAM_ACCESS,
                                           *roles.EXAM_EDIT))):
    t = db.query(models.ExamTemplate).get(tid)
    if not t:
        raise HTTPException(404, "Test topilmadi")
    return {**_tpl_summary(t), "parts": _load(t.parts)}


@router.post("/api/exam-templates")
def create_template(payload: TemplateIn, db: Session = Depends(get_db),
                    user=Depends(require_role(*roles.EXAM_EDIT))):
    _validate_tpl(payload)
    t = models.ExamTemplate(
        level=payload.level or None, kind=payload.kind,
        unit_no=payload.unit_no if payload.kind == "unit" else None,
        title=payload.title.strip(),
        parts=json.dumps(clean_parts(payload.parts), ensure_ascii=False),
        paper_max=payload.paper_max, is_active=1 if payload.is_active else 0,
        created_by=user.full_name)
    db.add(t)
    db.commit()
    audit.log(db, user, entity="exam_template", action="create",
              entity_id=t.id, entity_label=t.title, commit=True)
    return {**_tpl_summary(t), "parts": _load(t.parts)}


@router.put("/api/exam-templates/{tid}")
def update_template(tid: int, payload: TemplateIn,
                    db: Session = Depends(get_db),
                    user=Depends(require_role(*roles.EXAM_EDIT))):
    t = db.query(models.ExamTemplate).get(tid)
    if not t:
        raise HTTPException(404, "Test topilmadi")
    _validate_tpl(payload)
    t.level = payload.level or None
    t.kind = payload.kind
    t.unit_no = payload.unit_no if payload.kind == "unit" else None
    t.title = payload.title.strip()
    t.parts = json.dumps(clean_parts(payload.parts), ensure_ascii=False)
    t.paper_max = payload.paper_max
    t.is_active = 1 if payload.is_active else 0
    db.commit()
    audit.log(db, user, entity="exam_template", action="update",
              entity_id=t.id, entity_label=t.title, commit=True)
    return {**_tpl_summary(t), "parts": _load(t.parts)}


@router.delete("/api/exam-templates/{tid}")
def delete_template(tid: int, db: Session = Depends(get_db),
                    user=Depends(require_role(*roles.EXAM_EDIT))):
    t = db.query(models.ExamTemplate).get(tid)
    if not t:
        raise HTTPException(404, "Test topilmadi")
    used = db.query(models.ExamOnline).filter(
        models.ExamOnline.template_id == tid).count()
    if used:
        # Ishlatilgan test o'chirilmaydi — faqat yashiriladi
        t.is_active = 0
    else:
        db.delete(t)
    db.commit()
    audit.log(db, user, entity="exam_template", action="delete",
              entity_id=tid, entity_label=t.title, commit=True)
    return {"ok": True, "hidden": bool(used)}


# ---------------------------------------------------- guruh testining linki
class OnlineIn(BaseModel):
    template_id: int
    paper_max: Optional[float] = None


class OnlineToggle(BaseModel):
    is_open: bool


class AssignIn(BaseModel):
    student_id: int


class PaperMark(BaseModel):
    student_id: int
    paper: Optional[float] = None


class PaperBulk(BaseModel):
    marks: List[PaperMark]


def _online_of(db: Session, exam_id: int):
    return db.query(models.ExamOnline).filter(
        models.ExamOnline.exam_id == exam_id).first()


def _answer_sheet(detail: list, qmap: dict) -> list:
    """Examiner uchun javob varag'i (2026-09-18, Jahongir: "ustiga
    bossa javoblari ham ko'rinsin aynan nimada xato qilganini examiner
    isbotlay olsin"). Savol matni va to'g'ri javob link ochilgan
    paytdagi nusxadan olinadi — keyin bazada test tahrirlansa ham
    o'quvchi yechgan savollar ko'rinadi."""
    out = []
    for d in detail:
        q = qmap.get(d.get("id")) or {}
        given = d.get("given")
        opts = q.get("options") or []
        if q.get("type") == "choice":
            try:
                gi = int(given) if given not in (None, "") else None
            except (TypeError, ValueError):
                gi = None
            given_text = (_opt_label(opts, gi)
                          if gi is not None and 0 <= gi < len(opts) else None)
            a = q.get("answer")
            correct = (_opt_label(opts, a)
                       if isinstance(a, int) and 0 <= a < len(opts) else None)
        else:
            given_text = given if given not in (None, "") else None
            correct = " / ".join(q.get("answer") or [])
        img = q.get("image") or ""
        out.append({**d, "part": q.get("part"), "q": q.get("q") or "",
                    # Statik rasm (manzil) javob varag'ida ham ko'rinadi;
                    # yuklangan (data:) rasm ro'yxatni og'irlashtirmasin
                    "image": img if img.startswith("/exam-img/") else None,
                    "has_image": bool(img),
                    "type": q.get("type"), "given_text": given_text,
                    "correct": correct})
    return out


def _opt_label(opts: list, i: int) -> str:
    """ "B) is" — variant faqat harfning o'zi bo'lsa (rasmdan tanlash) "B"."""
    letter = "ABCDEFGH"[i]
    return letter if opts[i] == letter else f"{letter}) {opts[i]}"


def _qmap(parts: list) -> dict:
    m = {}
    for p in parts:
        for q in p.get("questions") or []:
            m[q["id"]] = {**q, "part": p.get("title")}
    return m


def _sub_out(s: models.ExamSubmission, names: dict,
             qmap: Optional[dict] = None) -> dict:
    return {
        "id": s.id, "student_id": s.student_id,
        "student_name": names.get(s.student_id) if s.student_id else None,
        "typed_name": s.typed_name, "status": s.status,
        "online_score": s.online_score, "online_max": s.online_max,
        "paper_score": s.paper_score,
        "submitted_at": s.submitted_at.isoformat() if s.submitted_at else None,
        "placed_by": s.placed_by,
        "away_count": s.away_count or 0,
        "away_sec": s.away_sec or 0,
        "note": s.note,
        "photo": s.photo,
        "detail": _answer_sheet(_load(s.detail), qmap or {}),
    }


@router.get("/api/groups/{group_id}/exam-bank-max")
def exam_bank_max(group_id: int, kind: str, unit_no: Optional[int] = None,
                  db: Session = Depends(get_db),
                  user=Depends(require_role(*roles.TEACHING_ACCESS))):
    """Yangi test formasi uchun: shu guruh darajasida mos test bazada
    bo'lsa — maksimal ball (savollar soni)."""
    group = _get_group_in_scope(db, group_id, user)
    return {"max_score": bank_max(db, group, kind, unit_no)}


@router.get("/api/exams/{exam_id}/online")
def get_online(exam_id: int, db: Session = Depends(get_db),
               user=Depends(require_role(*roles.TEACHING_ACCESS))):
    exam = _exams._exam_in_scope(db, exam_id, user)
    group = db.query(models.Group).get(exam.group_id)
    o = _online_of(db, exam.id)
    if o:
        finalize_expired(db, o, exam)
    subs = (db.query(models.ExamSubmission)
            .options(undefer(models.ExamSubmission.photo))
            .filter(models.ExamSubmission.exam_id == exam.id)
            .order_by(models.ExamSubmission.submitted_at).all())
    published = bool(o and o.published_at)
    can_see = (published or user.role in PUBLISH_ROLES
               or user.role in RESULT_ROLES)
    if not can_see:
        subs = []       # ustoz: examiner tasdiqlaguncha natija ko'rinmaydi
    ids = {s.student_id for s in subs if s.student_id}
    names = {st.id: st.full_name for st in db.query(models.Student)
             .filter(models.Student.id.in_(ids)).all()} if ids else {}
    tq = db.query(models.ExamTemplate).filter(
        models.ExamTemplate.is_active == 1,
        models.ExamTemplate.kind == exam.kind)
    if exam.kind == "unit" and exam.unit_no:
        tq = tq.filter(models.ExamTemplate.unit_no == exam.unit_no)
    templates = [_tpl_summary(t) for t in tq.all()]
    lvl = (group.level if group else None)
    # Guruh darajasiga moslari birinchi
    templates.sort(key=lambda t: (t["level"] != lvl, t["title"]))
    online = None
    qmap = _qmap(_load(o.parts)) if o else {}
    if o:
        t = db.query(models.ExamTemplate).get(o.template_id)
        online = {
            "token": o.token, "is_open": bool(o.is_open),
            "template_id": o.template_id,
            "template_title": t.title if t else None,
            "online_max": o.online_max, "paper_max": o.paper_max,
            "published_at": (o.published_at.isoformat()
                             if o.published_at else None),
            "published_by": o.published_by,
            "state": timer_state(o),
            "server_now": _iso(datetime.utcnow()),
            "starts_at": _iso(o.started_at),
            "ends_at": _iso(o.ends_at),
            "duration_min": o.duration_min,
            "in_progress": sum(1 for s in subs if s.status == "in_progress"),
            "away_limit": o.away_limit,
            "live": [
                {"id": s.id,
                 "name": s.typed_name or names.get(s.student_id) or "—",
                 "away_count": s.away_count or 0, "away_sec": s.away_sec or 0}
                for s in subs if s.status == "in_progress"
            ],
            "expelled": [
                {"id": s.id,
                 "name": s.typed_name or names.get(s.student_id) or "—",
                 "note": s.note}
                for s in subs if s.status == "expelled"
            ],
        }
    return {"online": online, "group_level": lvl,
            "can_manage": user.role in RESULT_ROLES,
            "can_publish": user.role in PUBLISH_ROLES,
            "hidden": not can_see,
            "templates": templates,
            "submissions": [_sub_out(s, names, qmap) for s in subs]}


@router.post("/api/exams/{exam_id}/online")
def create_online(exam_id: int, payload: OnlineIn,
                  db: Session = Depends(get_db),
                  user=Depends(require_role(*RESULT_ROLES))):
    exam = _exams._exam_in_scope(db, exam_id, user)
    if exam.kind not in ("unit", "mid", "end"):
        raise HTTPException(400, "Online link faqat Unit, Mid-course va "
                                 "End of course testlari uchun")
    if not _exam_open_for_results(exam):
        raise HTTPException(400, "Test hali tasdiqlanmagan — avval Examiner "
                                 "tasdiqlashi kerak")
    if _online_of(db, exam.id):
        raise HTTPException(409, "Bu testning linki allaqachon bor")
    t = db.query(models.ExamTemplate).get(payload.template_id)
    if not t or not t.is_active:
        raise HTTPException(404, "Test bazada topilmadi")
    parts = _load(t.parts)
    online_max = float(sum(1 for _ in _questions(parts)))
    paper_max = float(t.paper_max or 0) if payload.paper_max is None \
        else float(payload.paper_max)
    if paper_max < 0:
        raise HTTPException(400, "Writing/Speaking bali noto'g'ri")
    total = online_max + paper_max
    scored = [r for r in exam.results if not r.absent and r.score is not None]
    if scored and abs((exam.max_score or 0) - total) > 1e-6:
        raise HTTPException(
            400, f"Testga natija kiritilgan va maksimal ball "
                 f"{exam.max_score:g}. Online {online_max:g} + qog'oz "
                 f"{paper_max:g} = {total:g} — mos emas")
    old_max = exam.max_score
    exam.max_score = total
    o = models.ExamOnline(exam_id=exam.id, template_id=t.id,
                          token=secrets.token_urlsafe(9), is_open=1,
                          parts=t.parts, online_max=online_max,
                          paper_max=paper_max, created_by=user.full_name)
    db.add(o)
    db.commit()
    audit.log(db, user, entity="exam", action="update", entity_id=exam.id,
              entity_label=exam.title or roles.exam_title(exam.kind, exam.unit_no),
              field="online_link", old_value=old_max,
              new_value=f"{t.title}: online {online_max:g} + qog'oz {paper_max:g}",
              commit=True)
    return get_online(exam_id, db, user)


@router.put("/api/exams/{exam_id}/online")
def toggle_online(exam_id: int, payload: OnlineToggle,
                  db: Session = Depends(get_db),
                  user=Depends(require_role(*RESULT_ROLES))):
    exam = _exams._exam_in_scope(db, exam_id, user)
    o = _online_of(db, exam.id)
    if not o:
        raise HTTPException(404, "Link yo'q")
    o.is_open = 1 if payload.is_open else 0
    db.commit()
    return get_online(exam_id, db, user)


class StartIn(BaseModel):
    minutes: int
    countdown: Optional[int] = None
    away_limit: Optional[int] = None


@router.post("/api/exams/{exam_id}/online/start")
def start_online(exam_id: int, payload: StartIn, db: Session = Depends(get_db),
                 user=Depends(require_role(*RESULT_ROLES))):
    """Examiner vaqt belgilab testni boshlaydi: teskari sanoqdan keyin
    savollar ochiladi, belgilangan vaqt tugagach hammasi avtomatik
    topshiriladi."""
    exam = _exams._exam_in_scope(db, exam_id, user)
    o = _online_of(db, exam.id)
    if not o:
        raise HTTPException(404, "Link yo'q")
    if not _exam_open_for_results(exam):
        raise HTTPException(400, "Test tasdiqlanmagan yoki bekor qilingan")
    if timer_state(o) in ("countdown", "running"):
        raise HTTPException(400, "Test allaqachon boshlangan")
    if not (1 <= payload.minutes <= 300):
        raise HTTPException(400, "Vaqt 1 dan 300 daqiqagacha bo'lishi kerak")
    cd = COUNTDOWN_SEC if payload.countdown is None else max(0, min(60, payload.countdown))
    now = datetime.utcnow()
    o.duration_min = payload.minutes
    if payload.away_limit is not None:
        o.away_limit = max(0, min(50, payload.away_limit))
    elif o.away_limit is None:
        o.away_limit = AWAY_LIMIT_DEFAULT
    o.started_at = now + timedelta(seconds=cd)
    o.ends_at = o.started_at + timedelta(minutes=payload.minutes)
    o.is_open = 1
    db.commit()
    audit.log(db, user, entity="exam", action="update", entity_id=exam.id,
              entity_label=exam.title or roles.exam_title(exam.kind, exam.unit_no),
              field="online_start", new_value=f"{payload.minutes} daqiqa",
              commit=True)
    return get_online(exam_id, db, user)


@router.post("/api/exams/{exam_id}/online/stop")
def stop_online(exam_id: int, db: Session = Depends(get_db),
                user=Depends(require_role(*RESULT_ROLES))):
    """Testni muddatidan oldin tugatish — hamma o'quvchida vaqt tugaydi
    va javoblari avtomatik topshiriladi."""
    exam = _exams._exam_in_scope(db, exam_id, user)
    o = _online_of(db, exam.id)
    if not o or timer_state(o) not in ("countdown", "running"):
        raise HTTPException(400, "Test hozir ketmayapti")
    o.ends_at = datetime.utcnow()
    db.commit()
    return get_online(exam_id, db, user)


@router.delete("/api/exams/{exam_id}/online")
def delete_online(exam_id: int, db: Session = Depends(get_db),
                  user=Depends(require_role(*RESULT_ROLES))):
    exam = _exams._exam_in_scope(db, exam_id, user)
    o = _online_of(db, exam.id)
    if not o:
        raise HTTPException(404, "Link yo'q")
    if db.query(models.ExamSubmission).filter(
            models.ExamSubmission.exam_id == exam.id).count():
        raise HTTPException(400, "Bu link orqali topshirganlar bor — "
                                 "o'chirib bo'lmaydi, faqat yopish mumkin")
    db.delete(o)
    db.commit()
    return get_online(exam_id, db, user)


def _sub_in_scope(db: Session, sid: int, user):
    s = db.query(models.ExamSubmission).get(sid)
    if not s:
        raise HTTPException(404, "Topshiriq topilmadi")
    exam = _exams._exam_in_scope(db, s.exam_id, user)
    o = _online_of(db, exam.id)
    return s, exam, o


@router.post("/api/exam-submissions/{sid}/assign")
def assign_submission(sid: int, payload: AssignIn,
                      db: Session = Depends(get_db),
                      user=Depends(require_role(*RESULT_ROLES))):
    """Qizil chiziqdan pastdagi natijani guruhdagi o'quvchiga
    biriktirish (ismi xato yozilgan yoki qayta topshirgan)."""
    s, exam, o = _sub_in_scope(db, sid, user)
    if s.status not in ("pending", "duplicate", "replaced"):
        raise HTTPException(400, "Bu natija allaqachon joyida")
    if payload.student_id not in {st.id for st in
                                  _group_students(db, exam.group_id)}:
        raise HTTPException(400, "Bu o'quvchi guruhda yo'q — avval guruhga "
                                 "qo'shing")
    _place(db, exam, o, s, payload.student_id, user)
    audit.log(db, user, entity="exam", action="update", entity_id=exam.id,
              entity_label=exam.title or roles.exam_title(exam.kind, exam.unit_no),
              field="online_assign",
              old_value=s.typed_name or "", new_value=payload.student_id,
              commit=True)
    return get_online(exam.id, db, user)


@router.post("/api/exam-submissions/{sid}/expel")
def expel_submission(sid: int, db: Session = Depends(get_db),
                     user=Depends(require_role(*RESULT_ROLES))):
    """Examiner o'quvchini testdan chetlatadi — test o'sha zahoti
    yopiladi, natijasi hisobga olinmaydi."""
    s, exam, o = _sub_in_scope(db, sid, user)
    if s.status == "expelled":
        raise HTTPException(400, "Allaqachon chetlatilgan")
    expel(db, exam, s, f"Examiner chetlatdi ({user.full_name})")
    audit.log(db, user, entity="exam", action="update", entity_id=exam.id,
              entity_label=exam.title or roles.exam_title(exam.kind, exam.unit_no),
              field="online_expel",
              new_value=s.typed_name or s.student_id, commit=True)
    return get_online(exam.id, db, user)


@router.post("/api/exam-submissions/{sid}/reject")
def reject_submission(sid: int, db: Session = Depends(get_db),
                      user=Depends(require_role(*RESULT_ROLES))):
    s, exam, o = _sub_in_scope(db, sid, user)
    if s.status == "placed":
        raise HTTPException(400, "Joylashgan natijani rad etib bo'lmaydi — "
                                 "o'rniga boshqasini biriktiring")
    s.status = "rejected"
    db.commit()
    return get_online(exam.id, db, user)


@router.put("/api/exams/{exam_id}/paper")
def save_paper(exam_id: int, payload: PaperBulk,
               db: Session = Depends(get_db),
               user=Depends(require_role(*RESULT_ROLES))):
    """Writing + Speaking (qog'oz) ballari. Jami = online + qog'oz —
    shu jami natijaga yoziladi (foiz, coin shundan)."""
    exam = _exams._exam_in_scope(db, exam_id, user)
    o = _online_of(db, exam.id)
    if not o or not (o.paper_max or 0) > 0:
        raise HTTPException(400, "Bu testda qog'oz qismi yo'q")
    placed = {s.student_id: s for s in db.query(models.ExamSubmission)
              .filter(models.ExamSubmission.exam_id == exam.id,
                      models.ExamSubmission.status == "placed").all()}
    marks = []
    for m in payload.marks:
        s = placed.get(m.student_id)
        if not s:
            continue
        if m.paper is not None and not (0 <= m.paper <= o.paper_max):
            raise HTTPException(
                400, f"Writing/Speaking bali 0 va {o.paper_max:g} oralig'ida")
        if s.paper_score == m.paper:
            continue
        s.paper_score = m.paper
        if m.paper is not None:
            marks.append(schemas.ExamScoreMark(
                student_id=m.student_id,
                score=(s.online_score or 0) + m.paper, absent=False))
    db.commit()
    if marks and o.published_at:
        _exams._apply_exam_marks(db, exam, schemas.ExamScoreBulk(marks=marks),
                                 user)
    return get_online(exam_id, db, user)


@router.post("/api/exams/{exam_id}/online/publish")
def publish_online(exam_id: int, db: Session = Depends(get_db),
                   user=Depends(require_role(*PUBLISH_ROLES))):
    """Examiner natijalarni TASDIQLAYDI: joyidagi barcha topshiriqlar
    guruh testiga yoziladi — shundan keyin ustoz, o'quvchi va ota-ona
    ko'radi, coin beriladi, Telegram xabari ketadi. Qog'oz qismi bor
    bo'lsa, bali kiritilganlargina yoziladi (qolgani kiritilganda)."""
    exam = _exams._exam_in_scope(db, exam_id, user)
    o = _online_of(db, exam.id)
    if not o:
        raise HTTPException(404, "Link yo'q")
    if o.published_at:
        raise HTTPException(400, "Natijalar allaqachon tasdiqlangan")
    if not _exam_open_for_results(exam):
        raise HTTPException(400, "Test tasdiqlanmagan yoki bekor qilingan")
    placed = (db.query(models.ExamSubmission)
              .filter(models.ExamSubmission.exam_id == exam.id,
                      models.ExamSubmission.status == "placed",
                      models.ExamSubmission.student_id.isnot(None)).all())
    marks = []
    for s in placed:
        if (o.paper_max or 0) > 0 and s.paper_score is None:
            continue
        marks.append(schemas.ExamScoreMark(
            student_id=s.student_id,
            score=(s.online_score or 0) + (s.paper_score or 0), absent=False))
    o.published_at = datetime.utcnow()
    o.published_by = user.full_name
    db.commit()
    if marks:
        _exams._apply_exam_marks(db, exam, schemas.ExamScoreBulk(marks=marks),
                                 user)
    audit.log(db, user, entity="exam", action="update", entity_id=exam.id,
              entity_label=exam.title or roles.exam_title(exam.kind, exam.unit_no),
              field="online_publish", new_value=f"{len(marks)} ta natija",
              commit=True)
    return get_online(exam_id, db, user)


# -------------------------------------------------------- ochiq (loginsiz)
def _rate_ok(ip: str) -> bool:
    now = time.time()
    hits = [t for t in _HITS.get(ip, []) if now - t < 3600]
    if len(hits) >= _MAX_PER_HOUR:
        _HITS[ip] = hits
        return False
    hits.append(now)
    _HITS[ip] = hits
    return True


def _public(db: Session, token: str):
    if not token or len(token) < 8:
        raise HTTPException(404, "Test topilmadi")
    o = db.query(models.ExamOnline).filter(
        models.ExamOnline.token == token).first()
    if not o:
        raise HTTPException(404, "Test topilmadi")
    exam = db.query(models.Exam).get(o.exam_id)
    if not exam or exam.status == "cancelled":
        raise HTTPException(404, "Test topilmadi")
    return o, exam


@router.get("/api/public/exam/{token}")
def public_exam(token: str, db: Session = Depends(get_db)):
    """Ochiq sahifa holati. Savollar faqat test ketayotganda beriladi —
    examiner "Start" bosmaguncha o'quvchi kutib turadi (2026-09-18)."""
    o, exam = _public(db, token)
    finalize_expired(db, o, exam)
    group = db.query(models.Group).get(exam.group_id)
    is_open = bool(o.is_open) and _exam_open_for_results(exam)
    state = timer_state(o)
    parts = _load(o.parts)
    return {
        "title": exam.title or roles.exam_title(exam.kind, exam.unit_no),
        "group": group.name if group else "",
        "date": exam.date.isoformat() if exam.date else None,
        "is_open": is_open,
        "state": state if is_open else "closed",
        "server_now": _iso(datetime.utcnow()),
        "starts_at": _iso(o.started_at),
        "ends_at": _iso(o.ends_at),
        "duration_min": o.duration_min,
        "q_count": int(o.online_max or 0),
        "paper_max": o.paper_max or 0,
        "students": [{"id": s.id, "name": s.full_name}
                     for s in _roster(db, exam.group_id)]
        if is_open and state != "finished" else [],
        "parts": public_parts(parts) if is_open and state == "running" else [],
    }


class BeginIn(BaseModel):
    student_id: Optional[int] = None
    name: Optional[str] = None
    photo: str


class SaveIn(BaseModel):
    key: str
    answers: dict


class AwayIn(BaseModel):
    key: str
    seconds: int = 0


class SubmitIn(BaseModel):
    # Yangi tartib: begin'dan olingan kalit bilan
    key: Optional[str] = None
    answers: dict
    # Eski tartib (kalitsiz) — keshlangan eski sahifalar uchun
    student_id: Optional[int] = None
    name: Optional[str] = None
    photo: Optional[str] = None


def _client_ip(request: Request) -> str:
    return ((request.headers.get("x-forwarded-for") or "").split(",")[0].strip()
            or (request.client.host if request.client else ""))


def _identify(db: Session, exam, student_id, name, photo):
    """Ro'yxatdan tanlangan yoki yozilgan ism + kamera rasmi."""
    photo = photo or ""
    if not photo.startswith("data:image/") or len(photo) > PHOTO_MAX_CHARS:
        raise HTTPException(400, "Kameradan rasm oling")
    roster = {s.id: s for s in _roster(db, exam.group_id)}
    typed = (name or "").strip()[:120] or None
    if student_id is not None and student_id not in roster:
        raise HTTPException(400, "Ro'yxatdan o'zingizni tanlang")
    if student_id is None:
        if not typed or len(typed) < 3:
            raise HTTPException(400, "Ism va familiyangizni yozing")
        # Yozilgan ism ro'yxatdagi bilan AYNAN mos kelsa — o'sha o'quvchi
        want = _norm(typed)
        same = [s.id for s in roster.values() if _norm(s.full_name) == want]
        if len(same) == 1:
            student_id = same[0]
    if not typed and student_id in roster:
        typed = roster[student_id].full_name
    return student_id, typed, photo


def _finalize(db: Session, o, exam, sub, answers: dict, by: str = "Online test"):
    """Topshiriqni baholab joylashtiradi (qo'lda topshirish ham, vaqt
    tugab avtomatik topshirish ham shu yerdan)."""
    answers = {str(k): v for k, v in (answers or {}).items()}
    score, total, detail = grade(_load(o.parts), answers)
    status = "pending"
    if sub.student_id is not None:
        already = db.query(models.ExamSubmission).filter(
            models.ExamSubmission.exam_id == exam.id,
            models.ExamSubmission.student_id == sub.student_id,
            models.ExamSubmission.status == "placed",
            models.ExamSubmission.id != sub.id).first()
        status = "duplicate" if already else "placed"
    sub.answers = json.dumps(answers, ensure_ascii=False)[:20000]
    sub.detail = json.dumps(detail, ensure_ascii=False)
    sub.online_score = score
    sub.online_max = total
    sub.status = status
    sub.submitted_at = datetime.utcnow()
    if status != "placed" and status != "duplicate":
        sub.student_id = None
    if status == "placed":
        sub.placed_by = by
        sub.placed_at = datetime.utcnow()
    db.commit()
    if status == "placed":
        try:
            _write_result(db, exam, o, sub, _system_user())
        except HTTPException:
            # Masalan, maksimal ball keyin o'zgartirilgan — javob baribir
            # saqlangan, examiner ExamSheet'da ko'radi
            db.rollback()
    return status


def finalize_expired(db: Session, o, exam) -> int:
    """Vaqt tugab (va kechikib keluvchilar uchun muhlat o'tib) hali
    topshirilmagan ishlar SAQLANGAN javoblari bilan topshiriladi — kim
    qancha belgilagan bo'lsa (Jahongir). Sahifa yopilib qolgan
    o'quvchi ham natijasiz qolmaydi."""
    if not o.ends_at or datetime.utcnow() < o.ends_at + timedelta(seconds=GRACE_SEC):
        return 0
    subs = (db.query(models.ExamSubmission)
            .filter(models.ExamSubmission.exam_id == exam.id,
                    models.ExamSubmission.status == "in_progress").all())
    for s in subs:
        _finalize(db, o, exam, s, _load_dict(s.answers), by="Vaqt tugadi (avtomat)")
    return len(subs)


def _load_dict(txt) -> dict:
    try:
        v = json.loads(txt or "{}")
        return v if isinstance(v, dict) else {}
    except Exception:
        return {}


def expel(db: Session, exam, sub, why: str):
    """O'quvchini testdan chetlatish: uning testi yopiladi va natijasi
    umuman hisobga olinmaydi (2026-09-23, Jahongir)."""
    if sub.status == "placed" and sub.student_id:
        # Allaqachon yozilgan natija olib tashlanadi (coin ham qaytadi)
        for r in (db.query(models.ExamResult)
                  .filter(models.ExamResult.exam_id == exam.id,
                          models.ExamResult.student_id == sub.student_id).all()):
            _drop_coin_entry(db, "exam", r.id)
            db.delete(r)
    sub.status = "expelled"
    sub.note = why
    db.commit()


def _sub_by_key(db: Session, exam, key: str):
    if not key or len(key) < 10:
        raise HTTPException(400, "Qaytadan kiring")
    s = (db.query(models.ExamSubmission)
         .filter(models.ExamSubmission.exam_id == exam.id,
                 models.ExamSubmission.sub_key == key).first())
    if not s:
        raise HTTPException(400, "Qaytadan kiring")
    return s


def _can_answer(o) -> bool:
    """Javob qabul qilinadimi: test ketyapti yoki tugaganiga hali
    muhlat (GRACE_SEC) o'tmagan — avtomatik topshirish yetib kelsin."""
    if not o.is_open or not o.started_at or not o.ends_at:
        return False
    now = datetime.utcnow()
    return o.started_at <= now + timedelta(seconds=2) and \
        now <= o.ends_at + timedelta(seconds=GRACE_SEC)


@router.post("/api/public/exam/{token}/begin")
def public_begin(token: str, payload: BeginIn, request: Request,
                 db: Session = Depends(get_db)):
    """O'quvchi o'zini tanitadi (ism + rasm) — test boshlanishini
    kutib turadi. Kalit brauzerda saqlanadi."""
    ip = _client_ip(request)
    if not _rate_ok(ip or "?"):
        raise HTTPException(429, "Juda ko'p urinish — birozdan keyin qayta "
                                 "urinib ko'ring")
    o, exam = _public(db, token)
    if not o.is_open or not _exam_open_for_results(exam) or \
            timer_state(o) == "finished":
        raise HTTPException(410, "Test yopilgan")
    student_id, typed, photo = _identify(db, exam, payload.student_id,
                                         payload.name, payload.photo)
    sub = models.ExamSubmission(
        exam_id=exam.id, student_id=student_id, typed_name=typed,
        photo=photo, answers="{}", status="in_progress", ip=ip[:64],
        online_max=o.online_max or 0, sub_key=secrets.token_urlsafe(16))
    db.add(sub)
    db.commit()
    # Ism suv belgisi uchun ham qaytariladi (2026-09-23, Jahongir:
    # "ismiga suv belgi qo'shchi") — skrinshot tarqalsa, kimniki
    # ekani ko'rinib tursin
    return {"ok": True, "key": sub.sub_key, "name": typed or ""}


@router.post("/api/public/exam/{token}/save")
def public_save(token: str, payload: SaveIn, db: Session = Depends(get_db)):
    """Javoblarni oraliqda saqlash — telefon o'chib qolsa ham yo'qolmasin."""
    o, exam = _public(db, token)
    s = _sub_by_key(db, exam, payload.key)
    if s.status == "expelled":
        return {"ok": False, "expelled": True}
    if s.status != "in_progress":
        return {"ok": True, "submitted": True}
    if not _can_answer(o):
        return {"ok": False}
    s.answers = json.dumps({str(k): v for k, v in (payload.answers or {}).items()},
                           ensure_ascii=False)[:20000]
    db.commit()
    return {"ok": True}


@router.post("/api/public/exam/{token}/away")
def public_away(token: str, payload: AwayIn, db: Session = Depends(get_db)):
    """O'quvchi test sahifasidan chiqib qaytdi — qayd qilinadi.
    (2026-09-23, Jahongir: skrinshotning o'zini sezib bo'lmaydi, lekin
    savolni boshqa ilovaga olib chiqish shu yerda ko'rinadi.)"""
    o, exam = _public(db, token)
    s = _sub_by_key(db, exam, payload.key)
    if s.status != "in_progress" or not _can_answer(o):
        return {"ok": True}
    s.away_count = (s.away_count or 0) + 1
    s.away_sec = (s.away_sec or 0) + max(0, min(3600, int(payload.seconds or 0)))
    db.commit()
    limit = o.away_limit
    if limit and s.away_count > limit:
        expel(db, exam, s, f"Sahifadan {s.away_count} marta chiqdi "
                           f"(ruxsat: {limit})")
        return {"ok": True, "away_count": s.away_count, "expelled": True}
    return {"ok": True, "away_count": s.away_count,
            "away_limit": limit, "left": (limit - s.away_count) if limit else None}


@router.post("/api/public/exam/{token}/submit")
def public_submit(token: str, payload: SubmitIn, request: Request,
                  db: Session = Depends(get_db)):
    o, exam = _public(db, token)
    if not _exam_open_for_results(exam):
        raise HTTPException(410, "Test yopilgan")
    if payload.key:
        s = _sub_by_key(db, exam, payload.key)
        if s.status == "expelled":
            return {"ok": False, "expelled": True}
        if s.status == "in_progress":
            if not _can_answer(o):
                # Muhlat o'tib ketgan — saqlangan javoblar bilan yakunlanadi
                answers = _load_dict(s.answers)
            else:
                answers = payload.answers
            _finalize(db, o, exam, s, answers)
        return {"ok": True, "paper_max": o.paper_max or 0,
                "pending": s.status not in ("placed",)}
    # Eski tartib (kalitsiz): faqat test ketayotganda
    ip = _client_ip(request)
    if not _rate_ok(ip or "?"):
        raise HTTPException(429, "Juda ko'p urinish — birozdan keyin qayta "
                                 "urinib ko'ring")
    if not _can_answer(o):
        raise HTTPException(410, "Test yopilgan")
    student_id, typed, photo = _identify(db, exam, payload.student_id,
                                         payload.name, payload.photo)
    sub = models.ExamSubmission(
        exam_id=exam.id, student_id=student_id, typed_name=typed, photo=photo,
        status="in_progress", ip=ip[:64], online_max=o.online_max or 0,
        sub_key=secrets.token_urlsafe(16))
    db.add(sub)
    db.commit()
    status = _finalize(db, o, exam, sub, payload.answers)
    # Ball o'quvchiga ko'rsatilmaydi — examiner tasdiqlagach e'lon
    # qilinadi (2026-09-18)
    return {"ok": True, "paper_max": o.paper_max or 0,
            "pending": status != "placed"}


# ------------------------------------------------ boshlang'ich test bazasi
def seed_templates(db: Session) -> None:
    """Jahongir yuborgan testlar (Step 1 Unit 1 …) bazaga bir marta
    yoziladi. Keyin examinerlar boshlig'i o'zi tahrirlaydi."""
    import exam_bank_seed
    # Tasdiqlash qo'shilishidan OLDINGI linklar natijalari allaqachon
    # guruh testida — ular tasdiqlangan hisoblanadi (bir martalik)
    if not _seed_done(db, "exam_online_publish_legacy_v1"):
        try:
            (db.query(models.ExamOnline)
             .filter(models.ExamOnline.published_at.is_(None))
             .update({models.ExamOnline.published_at: datetime.utcnow(),
                      models.ExamOnline.published_by: "avvalgi tartib"},
                     synchronize_session=False))
            db.commit()
            _seed_mark(db, "exam_online_publish_legacy_v1")
        except Exception:
            db.rollback()
    for key, tpl in exam_bank_seed.TEMPLATES:
        if _seed_done(db, key):
            continue
        exists = db.query(models.ExamTemplate).filter(
            models.ExamTemplate.level == tpl["level"],
            models.ExamTemplate.kind == tpl["kind"],
            models.ExamTemplate.unit_no == tpl.get("unit_no")).first()
        if not exists:
            db.add(models.ExamTemplate(
                level=tpl["level"], kind=tpl["kind"],
                unit_no=tpl.get("unit_no"), title=tpl["title"],
                parts=json.dumps(clean_parts(tpl["parts"]),
                                 ensure_ascii=False),
                paper_max=tpl.get("paper_max", 0), created_by="JonyOS"))
            db.commit()
        _seed_mark(db, key)
    fill_exam_max_from_bank(db)


def fill_exam_max_from_bank(db: Session, key: str = "exam_max_from_bank_v1"):
    """BIR MARTALIK: mavjud imtihonlarning maksimal balini test bazasidagi
    savollar soniga tenglaydi. Faqat natija kiritilmagan, link ochilmagan
    va bekor qilinmagan Unit / Mid / End testlar — natijasi borlarining
    foizi va coini o'zgarib ketmasin."""
    if _seed_done(db, key):
        return 0
    changed = 0
    try:
        linked = {o.exam_id for o in db.query(models.ExamOnline).all()}
        groups = {}
        for ex in (db.query(models.Exam)
                   .filter(models.Exam.kind.in_(("unit", "mid", "end")))
                   .all()):
            if ex.status == "cancelled" or ex.id in linked:
                continue
            if any(not r.absent and (r.score is not None or r.band is not None)
                   for r in ex.results):
                continue
            if ex.group_id not in groups:
                groups[ex.group_id] = db.query(models.Group).get(ex.group_id)
            mx = bank_max(db, groups[ex.group_id], ex.kind, ex.unit_no)
            if mx and ex.max_score != mx:
                ex.max_score = mx
                changed += 1
        db.commit()
        _seed_mark(db, key)
        print(f"[exam-bank] maksimal ball yangilandi: {changed} ta imtihon")
    except Exception as e:  # noqa: BLE001
        db.rollback()
        print(f"[exam-bank] maksimal ball yangilanmadi: {e}")
    return changed
