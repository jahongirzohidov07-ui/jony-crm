"""Auto-extracted from main.py during refactor (split-main). Domain: hr_ats."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bisect
import json
from datetime import date, datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy import func, or_, text
from sqlalchemy.orm import Session

import audit
import billing
import migrations
import models
import notify
import roles
import schemas
from auth import (
    create_access_token,
    get_current_user,
    hash_password,
    require_role,
    verify_password,
    SECRET_KEY,
)
from database import Base, engine, get_db, SessionLocal
from common import *  # noqa: F401,F403 - shared helpers/state

router = APIRouter()

@router.get("/api/vacancies")
def list_vacancies(
    status: str | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.HR_ACCESS)),
):
    q = scope_to_branch(db.query(models.Vacancy), models.Vacancy, user)
    if status:
        q = q.filter(models.Vacancy.status == status)
    out = []
    for v in q.order_by(models.Vacancy.created_at.desc()).all():
        cands = db.query(models.Candidate).filter(
            models.Candidate.vacancy_id == v.id).all()
        out.append({
            "id": v.id, "title": v.title, "role": v.role,
            "branch_id": v.branch_id,
            "branch": v.branch.name if v.branch else None,
            "headcount": v.headcount, "status": v.status,
            "salary_from": v.salary_from, "salary_to": v.salary_to,
            "description": v.description,
            "created_at": v.created_at.isoformat() if v.created_at else None,
            "candidate_count": len(cands),
            "hired_count": sum(1 for c in cands if c.stage == "hired"),
        })
    return out

@router.post("/api/vacancies")
def create_vacancy(
    payload: schemas.VacancyCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.HR_ACCESS)),
):
    data = payload.model_dump()
    if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
        data["branch_id"] = user.branch_id
    v = models.Vacancy(**data, created_by=user.username)
    db.add(v); db.commit(); db.refresh(v)
    return {"id": v.id}

@router.put("/api/vacancies/{vid}")
def update_vacancy(
    vid: int,
    payload: schemas.VacancyUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.HR_ACCESS)),
):
    v = db.query(models.Vacancy).get(vid)
    if not v:
        raise HTTPException(404, "Vakansiya topilmadi")
    for k, val in payload.model_dump(exclude_unset=True).items():
        setattr(v, k, val)
    # Yopilgan sanani avtomat qo'yamiz - qo'lda eslab qolish shart emas.
    v.closed_at = date.today() if v.status == "closed" else None
    db.commit()
    return {"ok": True}

@router.delete("/api/vacancies/{vid}")
def delete_vacancy(
    vid: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.HR_ACCESS)),
):
    v = db.query(models.Vacancy).get(vid)
    if not v:
        raise HTTPException(404, "Vakansiya topilmadi")
    n = db.query(models.Candidate).filter(models.Candidate.vacancy_id == vid).count()
    if n:
        raise HTTPException(400, f"Bu vakansiyada {n} ta nomzod bor. Avval ularni o'chiring.")
    db.delete(v); db.commit()
    return {"ok": True}

# =====================================================================
#  ARIZA JAVOBLARI — BITTA MANBA (2026-08-15)
#  Jahongir: "qo'lda kiritsa ham shu savollar chiqishi kerak".
#  Ochiq ariza (jonyos.uz/apply) va HR qo'lda kiritadigan forma
#  AYNI savollarni so'raydi va AYNI ko'rinishda saqlaydi — shuning
#  uchun ikkalasi ham shu ikki yordamchidan foydalanadi.
# =====================================================================
_APPLY_FIELDS = ("address", "birth_date", "education", "marital",
                 "socials", "work_duration", "workplaces",
                 "subject", "experience_years")


def _apply_note_lines(get, pos_label: str, is_teacher: bool) -> list:
    """Nomzod kartasidagi o'qiladigan izoh — ikkala yo'lda bir xil."""
    lines = [
        f"LAVOZIM: {pos_label}",
        f"Yashash manzili: {get('address') or '—'}",
        f"Tug'ilgan sana: {get('birth_date') or '—'}",
        f"Ma'lumoti: {get('education') or '—'}",
        f"Oilaviy holati: "
        f"{roles.APPLY_MARITAL_LABELS.get(get('marital'), '—')}",
        f"Ijtimoiy tarmoqlar: {get('socials') or '—'}",
        f"Qancha vaqt ishlamoqchi: {get('work_duration') or '—'}",
    ]
    if is_teacher:
        lines.append(f"Qaysi fandan dars beradi: {get('subject') or '—'}")
    return lines


def _apply_fill(c, get, position: str) -> None:
    """Javoblarni nomzodning ALOHIDA maydonlariga yozadi."""
    c.position = position or None
    c.subject = (get("subject") or None) if position == "teacher" else None
    c.address = get("address") or None
    c.birth_date_text = get("birth_date") or None
    c.education = get("education") or None
    c.marital = get("marital") or None
    c.socials = get("socials") or None
    c.work_duration = get("work_duration") or None
    if get("workplaces"):
        c.workplaces = get("workplaces")
    try:
        v = get("experience_years")
        if v not in (None, ""):
            c.experience_years = float(v)
    except Exception:
        pass


def _open_application(db: Session, c, user=None, note: str = None):
    """Nomzodga ISHGA OLISH QUVURIDA ariza ochadi (2026-08-15,
    Jahongir: "ishga olish quvuri juda zor narsa ekan faqat qo'lda
    nomzod kiritsam bu joyga chiqmayabdi").

    Quvur CandidateApplication jadvalidan o'qiydi. Onlayn ariza uni
    o'zi ochardi, qo'lda kiritilganda esa ochilmasdi — shuning uchun
    qo'lda kiritilgan nomzod quvurda ko'rinmasdi.

    Ochiq arizasi bor bo'lsa ikkinchisini OCHMAYDI."""
    exists = (db.query(models.CandidateApplication)
              .filter(models.CandidateApplication.candidate_id == c.id)
              .first())
    if exists:
        return exists
    today = roles.local_today()
    stage = roles.CANDIDATE_TO_APPLICATION.get(c.stage or "applied", "new")
    a = models.CandidateApplication(
        candidate_id=c.id, vacancy_id=c.vacancy_id,
        branch_id=c.branch_id, stage=stage, stage_since=today,
        source=c.source, note=note,
        owner_id=getattr(user, "id", None))
    if stage in roles.APPLICATION_CLOSED:
        a.closed_at = today
        a.reject_reason = c.reject_reason
    db.add(a)
    db.commit()
    db.refresh(a)
    _ensure_public_id(db, "application", a)
    db.add(models.ApplicationStageLog(
        application_id=a.id, from_stage=None, to_stage=stage,
        days_in_stage=0, by_user_id=getattr(user, "id", None)))
    db.commit()
    return a


def _sync_application_stage(db: Session, c, user=None) -> bool:
    """Nomzodlar ro'yxatida bosqich o'zgarsa QUVUR ham yurishi kerak —
    aks holda bir odam ikki joyda ikki xil bosqichda turardi."""
    want = roles.CANDIDATE_TO_APPLICATION.get(c.stage or "")
    if not want:
        return False
    a = (db.query(models.CandidateApplication)
         .filter(models.CandidateApplication.candidate_id == c.id)
         .order_by(models.CandidateApplication.id.desc()).first())
    if a is None or a.stage == want:
        return False
    today = roles.local_today()
    since = a.stage_since or (a.created_at.date() if a.created_at
                              else today)
    old_stage = a.stage
    a.stage = want
    a.stage_since = today
    if want in roles.APPLICATION_CLOSED:
        a.closed_at = today
        if want == "rejected":
            a.reject_reason = c.reject_reason or a.reject_reason
    else:
        a.closed_at = None
    db.add(models.ApplicationStageLog(
        application_id=a.id, from_stage=old_stage, to_stage=want,
        days_in_stage=(today - since).days,
        note="Nomzodlar ro'yxatidan o'zgartirildi",
        by_user_id=getattr(user, "id", None)))
    return True


def _cand_role(c) -> tuple:
    """Nomzod QAYSI ISHGA kelgan: (asosiy yozuv, fan).

    Uch manba bor va tartib shu (2026-08-15, Jahongir: "BU ROYXATDA
    QAYSI VAKANSIYANI TANLAGANI KO'RINIB TURSIN"):
      1) haqiqiy vakansiyaga bog'langan bo'lsa — vakansiya nomi;
      2) bo'lmasa — o'zi tanlagan lavozim (onlayn arizadan);
      3) ikkalasi ham bo'lmasa — izoh matnidagi "LAVOZIM: ..." qatori
         (eski yozuvlar shu ko'rinishda qolgan).
    Ustoz bo'lsa fan alohida qaytadi — ro'yxatda yonida ko'rinsin.
    """
    label = None
    if getattr(c, "vacancy", None) is not None:
        label = c.vacancy.title
    if not label and c.position:
        label = roles.APPLY_POSITION_LABELS.get(c.position, c.position)
    subject = c.subject or None
    if not label or not subject:
        for line in (c.note or "").splitlines():
            t = line.strip()
            if not label and t.upper().startswith("LAVOZIM:"):
                label = t.split(":", 1)[1].strip() or None
            if not subject and t.lower().startswith(
                    "qaysi fandan dars beradi"):
                v = t.split(":", 1)[1].strip() if ":" in t else ""
                subject = v if v and v != "—" else None
    return label, subject


@router.get("/api/candidates")
def list_candidates(
    vacancy_id: int | None = None,
    stage: str | None = None,
    q: str | None = None,
    position: str | None = None,
    subject: str | None = None,
    source: str | None = None,
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.HR_CANDIDATE_VIEW)),
):
    """Nomzodlar ro'yxati.

    2026-08-15, Jahongir: "keyin filtr ham qoyib bersan shu yerga
    nomzodlar kopayganda topish osonlashadi". Qidiruv ism va telefon
    bo'yicha; qolgan filtrlar birga ishlaydi (VA mantig'i)."""
    qq = scope_to_branch(db.query(models.Candidate), models.Candidate,
                         user, branch_id)
    # O'quv bo'limi rahbariga faqat USTOZ nomzodlari (2026-08-16)
    if _teacher_only(user):
        qq = qq.filter(or_(models.Candidate.position == "teacher",
                           models.Candidate.subject.isnot(None)))
    if vacancy_id:
        qq = qq.filter(models.Candidate.vacancy_id == vacancy_id)
    if stage:
        qq = qq.filter(models.Candidate.stage == stage)
    if position:
        qq = qq.filter(models.Candidate.position == position)
    if source:
        qq = qq.filter(models.Candidate.source == source)
    if subject:
        qq = qq.filter(models.Candidate.subject.ilike(f"%{subject}%"))
    if q and len(q.strip()) >= 2:
        t = q.strip()
        digits = "".join(ch for ch in t if ch.isdigit())
        conds = [models.Candidate.full_name.ilike(f"%{t}%")]
        if len(digits) >= 3:
            # Telefon bazada "+998 90 123 45 67" ko'rinishida ham
            # bo'lishi mumkin - belgilarni olib tashlab solishtiramiz
            clean = models.Candidate.phone
            for ch in (" ", "+", "-", "(", ")"):
                clean = func.replace(clean, ch, "")
            conds.append(clean.ilike(f"%{digits}%"))
        else:
            conds.append(models.Candidate.phone.ilike(f"%{t}%"))
        qq = qq.filter(or_(*conds))
    from sqlalchemy.orm import selectinload as _sel
    qq = qq.options(_sel(models.Candidate.vacancy),
                    _sel(models.Candidate.branch))
    rows = qq.order_by(models.Candidate.created_at.desc()).all()
    return [{
        "id": c.id, "full_name": c.full_name, "phone": c.phone,
        "vacancy_id": c.vacancy_id,
        "vacancy": c.vacancy.title if c.vacancy else None,
        # QAYSI ISHGA kelgani va (ustoz bo'lsa) QAYSI FANDAN
        "role_label": _cand_role(c)[0],
        "position": c.position,
        "position_label": roles.APPLY_POSITION_LABELS.get(
            c.position or "", None),
        "subject": _cand_role(c)[1],
        "stage": c.stage, "source": c.source,
        "branch_id": c.branch_id,
        "branch": c.branch.name if c.branch else None,
        "note": c.note, "reject_reason": c.reject_reason,
        "hired_date": c.hired_date.isoformat() if c.hired_date else None,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "decision": c.decision or "pending",
        "trial_score": c.trial_score,
        "interview_score": c.interview_score,
        "expected_salary": c.expected_salary,
        "language_level": c.language_level,
        "experience_years": c.experience_years,
    } for c in rows]


def backfill_candidate_positions(db: Session) -> int:
    """ESKI NOMZODLAR (2026-08-15). Onlayn ariza orqali kelganlarning
    lavozimi va fani faqat IZOH matnida yotardi. Bir marta o'qib,
    alohida maydonlarga ko'chiramiz — shundan keyin filtr ham
    ishlaydi. Idempotent: to'ldirilganiga qayta tegmaydi."""
    from common import _seed_done, _seed_mark
    if _seed_done(db, "cand_answers_v1"):
        return 0
    n = 0
    rev = {lbl.lower(): k for k, lbl in roles.APPLY_POSITIONS}
    mar = {lbl.lower(): k for k, lbl in roles.APPLY_MARITAL}
    # Izohdagi sarlavha -> nomzod maydoni
    MAP = {
        "yashash manzili": "address",
        "tug'ilgan sana": "birth_date_text",
        "ma'lumoti": "education",
        "ijtimoiy tarmoqlar": "socials",
        "qancha vaqt ishlamoqchi": "work_duration",
    }
    for c in db.query(models.Candidate).all():
        label, subject = _cand_role(c)
        changed = False
        if not c.position and label:
            key = rev.get(label.strip().lower())
            if key is None and label.lower().startswith("boshqa"):
                key = "other"
            if key:
                c.position = key
                changed = True
        if not c.subject and subject:
            c.subject = subject[:100]
            changed = True
        for line in (c.note or "").splitlines():
            if ":" not in line:
                continue
            head, val = line.split(":", 1)
            head = head.strip().lower()
            val = val.strip()
            if not val or val == "—":
                continue
            field = MAP.get(head)
            if field and not getattr(c, field, None):
                setattr(c, field, val[:300])
                changed = True
            elif head == "oilaviy holati" and not c.marital:
                k = mar.get(val.lower())
                if k:
                    c.marital = k
                    changed = True
        if changed:
            n += 1
    if n:
        db.commit()
    _seed_mark(db, "cand_answers_v1")
    return n


@router.get("/api/hr/options/{kind}")
def list_hr_options(
    kind: str,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.HR_CANDIDATE_VIEW)),
):
    """Ro'yxat variantlari: kodda yozilganlari + HR qo'shganlari."""
    if kind == "language_level":
        return {"kind": kind, "rows": _language_levels(db)}
    return {"kind": kind, "rows": _custom_options(db, kind)}


@router.post("/api/hr/options/{kind}")
def add_hr_option(
    kind: str,
    payload: dict,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.HR_ACCESS)),
):
    """Ro'yxatga yangi variant qo'shish (2026-08-16).

    Jahongir: "tagidan qo'shadigan qilish kerak til darajasini ...
    ona tili yo boshqa sertifikatlar kiritib bo'lmayabdi".

    Kalit yozilgan matndan hosil qilinadi, shunda baza ichida ham
    o'qish oson bo'ladi ("TOEFL 90+" -> "toefl_90")."""
    label = (payload or {}).get("label", "").strip()
    if not label:
        raise HTTPException(400, "Nomini yozing")
    if len(label) > 60:
        raise HTTPException(400, "Nomi 60 belgidan oshmasin")
    key = "".join(ch if ch.isalnum() else "_" for ch in label.lower())
    key = "_".join(x for x in key.split("_") if x)[:40] or "opt"
    # Dublikat: kodda ham, qo'shilganlar orasida ham bo'lmasin
    have = {o["key"] for o in _language_levels(db)} if kind == "language_level" \
        else {o["key"] for o in _custom_options(db, kind)}
    if key in have:
        raise HTTPException(400, "Bunday variant allaqachon bor")
    row = models.HrOption(kind=kind, key=key, label=label,
                          position=999, active=1,
                          created_by=user.full_name)
    db.add(row); db.commit(); db.refresh(row)
    return {"key": row.key, "label": row.label, "custom": True,
            "id": row.id}


@router.delete("/api/hr/options/{oid}")
def delete_hr_option(
    oid: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.HR_ACCESS)),
):
    """Variantni ro'yxatdan olib tashlash.

    Yozuv O'CHIRILMAYDI, faqat yashiriladi: shu variant tanlangan
    eski nomzod kartalarida nomi ko'rinib turaversin."""
    row = db.query(models.HrOption).get(oid)
    if not row:
        raise HTTPException(404, "Topilmadi")
    row.active = 0
    db.commit()
    return {"ok": True}


@router.get("/api/candidates/filters")
def candidate_filters(db: Session = Depends(get_db),
                      user=Depends(require_role(*roles.HR_ACCESS))):
    """Filtr tanlagichlari uchun ro'yxatlar (2026-08-15).
    Fanlar bazadagi HAQIQIY qiymatlardan yig'iladi — ariza formasida
    fan erkin yoziladi, shuning uchun oldindan aniq ro'yxat yo'q."""
    q = scope_to_branch(db.query(models.Candidate), models.Candidate, user)
    subs, poss = set(), set()
    for c in q.all():
        lab, sub = _cand_role(c)
        if sub:
            subs.add(sub.strip())
        if c.position:
            poss.add(c.position)
    return {
        "positions": [{"key": k, "label": lbl}
                      for k, lbl in roles.APPLY_POSITIONS],
        "used_positions": sorted(poss),
        "subjects": sorted(subs, key=lambda x: x.lower()),
        "sources": [{"key": k, "label": lbl}
                    for k, lbl in roles.CANDIDATE_SOURCES]
        if hasattr(roles, "CANDIDATE_SOURCES") else [],
    }


@router.get("/api/candidates/{cid}")
def get_candidate(
    cid: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.HR_CANDIDATE_VIEW)),
):
    """Nomzod kartasi - qaror qabul qilish uchun kerak bo'lgan hammasi
    bir ekranda: CV, tajriba, ballar, kuchli va zaif tomonlari."""
    c = db.query(models.Candidate).get(cid)
    if c and _teacher_only(user) and not _is_teacher_candidate(c):
        raise HTTPException(
            403, "Bu nomzod ustoz emas — sizga faqat ustoz nomzodlari "
                 "ko'rinadi.")
    if not c:
        raise HTTPException(404, "Nomzod topilmadi")

    files = (db.query(models.Attachment)
             .filter(models.Attachment.entity == "candidate",
                     models.Attachment.entity_id == cid)
             .order_by(models.Attachment.created_at.desc()).all())

    # Umumiy ball: probniy dars va intervyu o'rtachasi. Ikkalasi ham
    # bo'lmasa - hali baholanmagan.
    scores = [x for x in (c.trial_score, c.interview_score) if x is not None]
    overall = round(sum(scores) / len(scores), 1) if scores else None

    return {
        "id": c.id,
        "full_name": c.full_name,
        "phone": c.phone,
        "vacancy_id": c.vacancy_id,
        "vacancy": c.vacancy.title if c.vacancy else None,
        # Ariza savollari (2026-08-15) — qo'lda kiritilsa ham,
        # havola orqali kelsa ham bir xil joyda
        "role_label": _cand_role(c)[0],
        "position": c.position,
        "position_label": roles.APPLY_POSITION_LABELS.get(
            c.position or "", None),
        "subject": _cand_role(c)[1],
        "address": c.address,
        "birth_date_text": c.birth_date_text,
        "education": c.education,
        "marital": c.marital,
        "marital_label": roles.APPLY_MARITAL_LABELS.get(c.marital or "",
                                                        None),
        "socials": c.socials,
        "work_duration": c.work_duration,
        "stage": c.stage,
        "stage_label": dict(roles.CANDIDATE_STAGES).get(c.stage, c.stage)
                       if hasattr(roles, "CANDIDATE_STAGES") else c.stage,
        "source": c.source,
        "branch_id": c.branch_id,
        "branch": c.branch.name if c.branch else None,
        "note": c.note,
        "reject_reason": c.reject_reason,
        "hired_date": c.hired_date.isoformat() if c.hired_date else None,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        # ---- Karta ----
        "cv": c.cv,
        "experience_years": c.experience_years,
        "workplaces": c.workplaces,
        "certificates": c.certificates,
        "language_level": c.language_level,
        "language_level_label": _language_label(db, c.language_level),
        "native_language": getattr(c, "native_language", None),
        "expected_salary": c.expected_salary,
        "trial_score": c.trial_score,
        "interview_score": c.interview_score,
        "overall_score": overall,
        "strengths": c.strengths,
        "weaknesses": c.weaknesses,
        "reference_note": c.reference_note,
        "decision": c.decision or "pending",
        "decision_label": roles.HIRE_DECISION_LABELS.get(
            c.decision or "pending", "—"),
        "files": [{"id": a.id, "name": a.filename, "kind": a.kind,
                   "size": a.size,
                   "created_at": a.created_at.isoformat() if a.created_at else None}
                  for a in files],
        "language_levels": _language_levels(db),
        "decisions": [{"key": k, "label": lbl}
                      for k, lbl in roles.HIRE_DECISIONS],
    }

def _teacher_only(user) -> bool:
    """O'quv bo'limi rahbariga FAQAT ustoz nomzodlari ko'rinadi
    (2026-08-16). U sinov darsini baholaydi — farrosh yoki
    administrator nomzodini ko'rishi shart emas."""
    return user.role == roles.ACADEMIC_HEAD


def _is_teacher_candidate(c) -> bool:
    pos = (getattr(c, "position", None) or "").lower()
    return pos == "teacher" or bool(getattr(c, "subject", None))


def _custom_options(db: Session, kind: str) -> list:
    """HR qo'lda qo'shgan variantlar."""
    try:
        rows = (db.query(models.HrOption)
                .filter(models.HrOption.kind == kind,
                        models.HrOption.active == 1)
                .order_by(models.HrOption.position, models.HrOption.id).all())
    except Exception:
        return []
    return [{"key": r.key, "label": r.label, "custom": True, "id": r.id}
            for r in rows]


def _language_levels(db: Session) -> list:
    """Kodda yozilganlari + HR qo'shganlari (2026-08-16)."""
    base = [{"key": k, "label": lbl, "custom": False}
            for k, lbl in roles.LANGUAGE_LEVELS]
    have = {x["key"] for x in base}
    return base + [o for o in _custom_options(db, "language_level")
                   if o["key"] not in have]


def _language_label(db: Session, key: str | None) -> str | None:
    """Belgining nomi. Ro'yxatda bo'lmasa — qiymatning o'zi
    ko'rsatiladi, ya'ni eski yozuv ham hech qachon yo'qolmaydi."""
    if not key:
        return None
    lbl = roles.LANGUAGE_LEVEL_LABELS.get(key)
    if lbl:
        return lbl
    for o in _custom_options(db, "language_level"):
        if o["key"] == key:
            return o["label"]
    return key


def _sync_candidate_dates(c: models.Candidate):
    """Bosqichga qarab sanalarni avtomat to'ldiradi/tozalaydi."""
    if c.stage == "hired":
        c.hired_date = c.hired_date or date.today()
        c.closed_date = c.closed_date or date.today()
    elif c.stage == "rejected":
        c.hired_date = None
        c.closed_date = c.closed_date or date.today()
    else:
        c.hired_date = None
        c.closed_date = None

@router.post("/api/candidates")
def create_candidate(
    payload: schemas.CandidateCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.HR_ACCESS)),
):
    data = payload.model_dump()
    if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
        data["branch_id"] = user.branch_id
    # Fan faqat USTOZ uchun ma'noga ega (2026-08-15). Boshqa lavozim
    # tanlangan bo'lsa fan tozalanadi - aks holda "Ingliz tili"
    # filtriga farrosh ham tushib qolardi.
    if data.get("position") and data["position"] != "teacher":
        data["subject"] = None
    # birth_date -> birth_date_text (matn holida saqlanadi)
    if data.get("birth_date") is not None:
        data["birth_date_text"] = data.pop("birth_date")
    else:
        data.pop("birth_date", None)
    free_note = (data.pop("note", None) or "").strip()
    position = data.get("position") or ""

    # ARIZA IZOHI (2026-08-15, Jahongir: "qo'lda kiritsa ham shu
    # savollar chiqishi kerak"). Qo'lda kiritilganda ham kartada
    # AYNI ONLAYN ARIZADAGIDEK o'qiladigan izoh hosil bo'ladi.
    c = models.Candidate(**data, created_by=user.username)
    if position:
        pos_label = roles.APPLY_POSITION_LABELS.get(position, position)
        lines = _apply_note_lines(
            lambda k: getattr(c, "birth_date_text", None)
            if k == "birth_date" else getattr(c, k, None),
            pos_label, position == "teacher")
        lines.append(f"Manba: qo'lda kiritildi ({user.full_name})")
        if free_note:
            lines += ["", free_note]
        c.note = "\n".join(lines)
    else:
        c.note = free_note or None
    _sync_candidate_dates(c)
    db.add(c); db.commit(); db.refresh(c)
    # ISHGA OLISH QUVURIGA ham tushsin (2026-08-15). Ilgari faqat
    # onlayn ariza quvurda ko'rinardi, qo'lda kiritilgani yo'q edi.
    try:
        _open_application(db, c, user,
                          note=f"Qo'lda kiritildi ({user.full_name})")
    except Exception:
        db.rollback()          # quvur ochilmasa ham nomzod saqlansin
    return {"id": c.id}

@router.put("/api/candidates/{cid}")
def update_candidate(
    cid: int,
    payload: schemas.CandidateUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.HR_ACCESS)),
):
    c = db.query(models.Candidate).get(cid)
    if not c:
        raise HTTPException(404, "Nomzod topilmadi")
    before = c.stage
    for k, val in payload.model_dump(exclude_unset=True).items():
        setattr(c, k, val)
    if c.position and c.position != "teacher":
        c.subject = None            # fan faqat ustoz uchun
    _sync_candidate_dates(c)
    # Bosqich o'zgargan bo'lsa QUVUR ham yursin — bir odam ikki joyda
    # ikki xil bosqichda turmasin (2026-08-15).
    if c.stage != before:
        try:
            _sync_application_stage(db, c, user)
        except Exception:
            pass
    db.commit()
    return {"ok": True}

@router.delete("/api/candidates/{cid}")
def delete_candidate(
    cid: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.HR_ACCESS)),
):
    c = db.query(models.Candidate).get(cid)
    if not c:
        raise HTTPException(404, "Nomzod topilmadi")
    db.delete(c); db.commit()
    return {"ok": True}

@router.get("/api/candidates/{cid}/evaluation")
def candidate_evaluation(
    cid: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.OBSERVATION_ACCESS)),
):
    """Nomzodni sinash natijasi: o'z holicha bergan darsi va
    tushuntirilgandan keyingi darsi yonma-yon.

    Eng muhim raqam — IKKALASI ORASIDAGI FARQ. Sust boshlab keskin
    o'sgan odam, yaxshi boshlab qimirlamagandan ko'ra ko'proq narsa
    va'da qiladi: birinchisini o'rgatsa bo'ladi, ikkinchisini yo'q."""
    cand = db.query(models.Candidate).get(cid)
    if not cand:
        raise HTTPException(404, "Nomzod topilmadi")

    rows = (db.query(models.LessonObservation)
            .filter(models.LessonObservation.candidate_id == cid)
            .order_by(models.LessonObservation.attempt,
                      models.LessonObservation.id).all())

    before = next((o for o in rows if o.stage == "before"), None)
    after = next((o for o in rows if o.stage == "coached"), None)

    def brief(o):
        if not o:
            return None
        return _observation_out(db, o)

    delta = None
    band = None
    if before and after:
        delta = round((after.percent or 0) - (before.percent or 0), 1)
        label, tone, advice = roles.growth_band(delta)
        band = {"label": label, "tone": tone, "advice": advice}

    # Mezon-mezon solishtirish: nimani o'rgandi, nima o'zgarmadi
    compare = []
    if before and after:
        crit = {c.id: c for c in db.query(models.RubricCriterion).all()}
        b = {s.criterion_id: s.fact or 0 for s in before.scores}
        a = {s.criterion_id: s.fact or 0 for s in after.scores}
        for cidx in set(list(b) + list(a)):
            c = crit.get(cidx)
            if not c:
                continue
            bv, av = b.get(cidx, 0), a.get(cidx, 0)
            compare.append({
                "criterion_id": cidx, "no": c.order_no, "text": c.text,
                "points": c.points or 0,
                "before": bv, "after": av,
                "delta": round(av - bv, 1),
            })
        compare.sort(key=lambda r: (-r["delta"], r["no"]))

    improved = [r for r in compare if r["delta"] > 0]
    stuck = [r for r in compare
             if r["delta"] <= 0 and r["after"] < (r["points"] or 0)]

    return {
        "candidate_id": cid,
        "full_name": cand.full_name,
        "before": brief(before),
        "after": brief(after),
        "extra": [brief(o) for o in rows if o.stage == "extra"],
        "delta": delta,
        "growth": band,
        "compare": compare,
        "improved": improved[:10],
        "stuck": stuck[:10],
        "pass_score": roles.TEACHER_MIN_SKILL,
        "passed": bool(after and (after.percent or 0)
                       >= roles.TEACHER_MIN_SKILL),
        "stages": [{"key": k, "label": lbl, "tone": t}
                   for k, lbl, t in roles.OBSERVATION_STAGES],
        "next_stage": ("before" if not before
                       else "coached" if not after else "extra"),
        "hint": ("Avval nomzod o'z holicha dars beradi. Keyin mezonlar "
                 "tushuntirilib, qayta baholanadi. Ikkinchi ball emas, "
                 "ORASIDAGI FARQ ko'proq narsani aytadi: odam "
                 "aytilganini qabul qilib o'zgara oladimi."),
    }

def _app_out(db: Session, a: models.CandidateApplication,
             full: bool = False) -> dict:
    c = db.query(models.Candidate).get(a.candidate_id)
    v = db.query(models.Vacancy).get(a.vacancy_id) if a.vacancy_id else None
    br = db.query(models.Branch).get(a.branch_id) if a.branch_id else None
    owner = db.query(models.User).get(a.owner_id) if a.owner_id else None
    today = roles.local_today()

    since = a.stage_since or (a.created_at.date() if a.created_at else today)
    days = (today - since).days
    sla = roles.APPLICATION_SLA.get(a.stage)
    row = {
        "id": a.id,
        "public_id": a.public_id,
        "candidate_id": a.candidate_id,
        "candidate": c.full_name if c else None,
        "phone": c.phone if c else None,
        "vacancy_id": a.vacancy_id,
        "vacancy": v.title if v else None,
        # Vakansiya ochilmagan bo'lsa ham QAYSI ISHGA kelgani
        # ko'rinsin (2026-08-15) — kartada "vakansiyasiz" o'rniga
        # "Ustoz · Ingliz tili" chiqadi.
        "role_label": (v.title if v else (_cand_role(c)[0] if c else None)),
        "subject": (_cand_role(c)[1] if c else None),
        "branch_id": a.branch_id,
        "branch": br.name if br else None,
        "stage": a.stage,
        "stage_label": roles.APPLICATION_LABELS.get(a.stage, a.stage),
        "stage_tone": roles.APPLICATION_TONE.get(a.stage, "slate"),
        "progress": roles.application_progress(a.stage),
        "closed": a.stage in roles.APPLICATION_CLOSED,
        "days_in_stage": days,
        "sla_days": sla,
        # SLA buzilgani — kim uzoq kutib qolganini ko'rsatadi.
        # Nomzod javob kutib charchasa boshqa joyga ketadi.
        "overdue": bool(sla and days > sla
                        and a.stage not in roles.APPLICATION_CLOSED),
        "source": a.source,
        "owner_id": a.owner_id,
        "owner": owner.full_name if owner else None,
        "reject_reason": a.reject_reason,
        "reject_reason_label": roles.REJECT_LABELS.get(a.reject_reason),
        "reject_note": a.reject_note,
        "pool": bool(a.pool),
        "note": a.note,
        "created_at": a.created_at.isoformat() if a.created_at else None,
        "closed_at": a.closed_at.isoformat() if a.closed_at else None,
    }
    if full:
        row["history"] = [{
            "id": h.id,
            "from": h.from_stage,
            "from_label": roles.APPLICATION_LABELS.get(h.from_stage or ""),
            "to": h.to_stage,
            "to_label": roles.APPLICATION_LABELS.get(h.to_stage or ""),
            "days": h.days_in_stage,
            "reason": h.reason,
            "reason_label": roles.REJECT_LABELS.get(h.reason or ""),
            "note": h.note,
            "by": (db.query(models.User).get(h.by_user_id).full_name
                   if h.by_user_id
                   and db.query(models.User).get(h.by_user_id) else None),
            "at": h.created_at.isoformat() if h.created_at else None,
        } for h in db.query(models.ApplicationStageLog).filter(
            models.ApplicationStageLog.application_id == a.id
        ).order_by(models.ApplicationStageLog.id).all()]

        row["interviews"] = [_interview_out(db, i) for i in
                             db.query(models.Interview).filter(
                                 models.Interview.application_id == a.id
                             ).order_by(models.Interview.date).all()]

        cards = db.query(models.Scorecard).filter(
            models.Scorecard.application_id == a.id).all()
        row["scorecards"] = [_scorecard_out(db, s) for s in cards]
        vals = [s.percent for s in cards if s.percent is not None]
        row["avg_percent"] = round(sum(vals) / len(vals), 1) if vals else None
        lbl, tone = roles.scorecard_band(row["avg_percent"])
        row["avg_label"], row["avg_tone"] = lbl, tone
        # Baholovchilar bir xil fikrdami? Tarqoq bo'lsa — muhokama kerak
        recs = [roles.RECOMMENDATION_VALUE.get(s.recommendation)
                for s in cards if s.recommendation]
        row["agreement"] = (
            "bir xil" if recs and max(recs) == min(recs)
            else "tarqoq" if recs and (max(recs) - min(recs)) >= 2
            else "yaqin" if recs else None)
        if c:
            row["candidate_card"] = {
                "experience_years": c.experience_years,
                "language_level": c.language_level,
                "expected_salary": c.expected_salary,
                "cv": c.cv,
                "trial_score": c.trial_score,
                "strengths": c.strengths,
                "weaknesses": c.weaknesses,
            }
    return row

def _interview_out(db: Session, i: models.Interview) -> dict:
    who = (db.query(models.User).get(i.interviewer_id)
           if i.interviewer_id else None)
    return {
        "id": i.id, "public_id": i.public_id,
        "application_id": i.application_id,
        "candidate_id": i.candidate_id,
        "kind": i.kind,
        "kind_label": roles.INTERVIEW_KIND_LABELS.get(i.kind, i.kind),
        "date": i.date.isoformat() if i.date else None,
        "date_text": roles.uz_date_full(i.date),
        "time": i.time,
        "minutes": i.minutes or roles.INTERVIEW_MINUTES.get(i.kind, 30),
        "place": i.place,
        "interviewer_id": i.interviewer_id,
        "interviewer": who.full_name if who else None,
        "status": i.status,
        "status_label": roles.INTERVIEW_STATUS_LABELS.get(i.status,
                                                          i.status),
        "status_tone": roles.INTERVIEW_STATUS_TONE.get(i.status, "slate"),
        "note": i.note,
        "has_scorecard": db.query(models.Scorecard).filter(
            models.Scorecard.interview_id == i.id).first() is not None,
    }

def _scorecard_out(db: Session, s: models.Scorecard) -> dict:
    who = db.query(models.User).get(s.author_id) if s.author_id else None
    try:
        scores = json.loads(s.scores) if s.scores else {}
    except Exception:
        scores = {}
    lbl, tone = roles.scorecard_band(s.percent)
    return {
        "id": s.id,
        "application_id": s.application_id,
        "interview_id": s.interview_id,
        "author_id": s.author_id,
        "author": who.full_name if who else None,
        "scores": scores,
        "percent": s.percent,
        "label": lbl, "tone": tone,
        "recommendation": s.recommendation,
        "recommendation_label": roles.RECOMMENDATION_LABELS.get(
            s.recommendation or ""),
        "recommendation_tone": roles.RECOMMENDATION_TONE.get(
            s.recommendation or "", "slate"),
        "strengths": s.strengths,
        "concerns": s.concerns,
        "note": s.note,
        "filled": len([v for v in scores.values() if v]),
        "total_competencies": len(roles.COMPETENCIES),
        "created_at": s.created_at.isoformat() if s.created_at else None,
    }

def _ats_form(db: Session) -> dict:
    """Formalar uchun barcha ro'yxatlar — frontend ularni qattiq
    yozib qo'ymaydi."""
    return {
        "stages": [{"key": k, "label": l, "tone": t, "closed": c,
                    "sla": s}
                   for k, l, t, c, s in roles.APPLICATION_STAGES],
        "flow": roles.APPLICATION_FLOW,
        "reject_reasons": [{"key": k, "label": l,
                            "pool": k in roles.POOL_WORTHY}
                           for k, l in roles.REJECT_REASONS],
        "interview_kinds": [{"key": k, "label": l, "minutes": m}
                            for k, l, m in roles.INTERVIEW_KINDS],
        "interview_statuses": [{"key": k, "label": l, "tone": t}
                               for k, l, t in roles.INTERVIEW_STATUSES],
        "competencies": [{"key": k, "label": l, "group": g, "weight": w}
                         for k, l, g, w in roles.COMPETENCIES],
        "competency_groups": [{"key": k, "label": l}
                              for k, l in roles.COMPETENCY_GROUPS],
        "score_labels": roles.SCORE_LABELS,
        "score_min": roles.SCORE_MIN, "score_max": roles.SCORE_MAX,
        "recommendations": [{"key": k, "label": l, "tone": t}
                            for k, l, t, _v in roles.RECOMMENDATIONS],
        "pass_percent": roles.SCORECARD_PASS,
        "questions": [{"competency": c, "label":
                       roles.COMPETENCY_LABELS.get(c, c), "text": q}
                      for c, q in roles.QUESTION_BANK],
    }

def _find_duplicates(db: Session, name: str | None,
                     phone: str | None) -> list:
    """Bir xil odam ikki marta kiritilmasin. Telefon bo'yicha —
    ismning yozilishi har xil bo'lishi mumkin."""
    key = roles.phone_key(phone)
    since = roles.local_today() - timedelta(days=roles.DUPLICATE_DAYS)
    out = []
    for c in db.query(models.Candidate).all():
        if c.created_at and c.created_at.date() < since:
            continue
        same_phone = key and roles.phone_key(c.phone) == key
        same_name = (name and c.full_name
                     and c.full_name.strip().lower() == name.strip().lower())
        if same_phone or same_name:
            out.append({
                "candidate_id": c.id, "full_name": c.full_name,
                "phone": c.phone, "stage": c.stage,
                "why": "telefon" if same_phone else "ism",
                "applications": db.query(models.CandidateApplication).filter(
                    models.CandidateApplication.candidate_id == c.id).count(),
            })
    return out

@router.get("/api/ats/pipeline")
def ats_pipeline(vacancy_id: int | None = None,
                 branch_id: int | None = None,
                 stage: str | None = None,
                 db: Session = Depends(get_db),
                 user=Depends(require_role(*roles.ATS_VIEW))):
    """Kanban: har bosqichda kim turibdi va kim uzoq kutib qoldi."""
    # Filial tanlanganda FILIALSIZ (umumiy, masalan onlayn ariza)
    # arizalar ham ko'rinadi - aks holda ular "yo'qolib" qolardi
    # (2026-08-12: "quvurda ko'rinmadi" muammosining sababi).
    A = models.CandidateApplication
    if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
        from common import _user_branch_ids
        allowed = _user_branch_ids(db, user)
        q = db.query(A).filter(A.branch_id.in_(allowed or [-1])
                               | A.branch_id.is_(None))
    elif branch_id:
        q = db.query(A).filter((A.branch_id == branch_id)
                               | A.branch_id.is_(None))
    else:
        q = db.query(A)
    if vacancy_id:
        q = q.filter(models.CandidateApplication.vacancy_id == vacancy_id)
    if stage:
        q = q.filter(models.CandidateApplication.stage == stage)
    rows = [_app_out(db, a) for a in
            q.order_by(models.CandidateApplication.id.desc()).limit(500).all()]

    columns = []
    for k in roles.APPLICATION_FLOW:
        items = [r for r in rows if r["stage"] == k]
        columns.append({
            "key": k,
            "label": roles.APPLICATION_LABELS.get(k, k),
            "tone": roles.APPLICATION_TONE.get(k, "slate"),
            "count": len(items),
            "overdue": sum(1 for r in items if r["overdue"]),
            "rows": items[:50],
        })

    closed = [r for r in rows if r["closed"]]
    hired = [r for r in rows if r["stage"] == "hired"]
    # Voronka: har bosqichga yetib kelganlar soni
    seen = {}
    for lg in db.query(models.ApplicationStageLog).all():
        seen.setdefault(lg.to_stage, set()).add(lg.application_id)
    funnel = []
    first = None
    for k in roles.APPLICATION_FLOW:
        n = len(seen.get(k, set())) or sum(
            1 for r in rows if r["stage"] == k)
        if first is None and n:
            first = n
        funnel.append({
            "key": k, "label": roles.APPLICATION_LABELS.get(k, k),
            "count": n,
            "percent": round(n / first * 100, 1) if first else None,
        })

    return {
        "columns": columns,
        "rows": rows,
        "total": len(rows),
        "open": len(rows) - len(closed),
        "hired": len(hired),
        "overdue": sum(1 for r in rows if r["overdue"]),
        "pool": sum(1 for r in rows if r["pool"]),
        "funnel": funnel,
        "vacancies": [{"id": v.id, "title": v.title,
                       "branch_id": v.branch_id}
                      for v in scope_to_branch(
                          db.query(models.Vacancy), models.Vacancy,
                          user).all()],
        **_ats_form(db),
        "hint": ("Bosqich ARIZAGA yoziladi, nomzodga emas — bir odam "
                 "ikki vakansiyaga topshirishi mumkin. Muddati "
                 "o'tganlar qizil: nomzod javob kutib charchasa "
                 "boshqa joyga ketadi."),
    }

@router.get("/api/ats/applications/{aid}")
def ats_application(aid: int, db: Session = Depends(get_db),
                    user=Depends(require_role(*roles.ATS_VIEW))):
    a = db.query(models.CandidateApplication).get(aid)
    if not a:
        raise HTTPException(404, "Ariza topilmadi")
    return {**_app_out(db, a, full=True), **_ats_form(db)}

@router.post("/api/ats/applications")
def ats_application_add(payload: schemas.ApplicationIn,
                        db: Session = Depends(get_db),
                        user=Depends(require_role(*roles.ATS_MANAGE))):
    """Yangi ariza. Dublikat topilsa OGOHLANTIRADI, lekin bloklamaydi
    — haqiqatan boshqa odam bo'lishi ham mumkin."""
    cand = None
    if payload.candidate_id:
        cand = db.query(models.Candidate).get(payload.candidate_id)
        if not cand:
            raise HTTPException(404, "Nomzod topilmadi")
    else:
        if not payload.full_name:
            raise HTTPException(400, "Nomzod ismini yozing")
        dups = _find_duplicates(db, payload.full_name, payload.phone)
        if dups and not payload.force:
            return {"duplicate": True, "candidates": dups,
                    "message": ("Shunday nomzod allaqachon bor. "
                                "Uni tanlang yoki baribir yangisini "
                                "oching.")}
        cand = models.Candidate(
            full_name=payload.full_name.strip(),
            phone=payload.phone,
            branch_id=payload.branch_id or user.branch_id,
            stage="applied", source=payload.source,
            created_by=user.full_name)
        db.add(cand); db.commit(); db.refresh(cand)

    v = db.query(models.Vacancy).get(payload.vacancy_id) \
        if payload.vacancy_id else None
    exists = db.query(models.CandidateApplication).filter(
        models.CandidateApplication.candidate_id == cand.id,
        models.CandidateApplication.vacancy_id == payload.vacancy_id,
        models.CandidateApplication.stage.notin_(
            roles.APPLICATION_CLOSED)).first()
    if exists:
        raise HTTPException(
            400, "Bu nomzodning shu vakansiyaga ochiq arizasi bor")

    today = roles.local_today()
    a = models.CandidateApplication(
        candidate_id=cand.id,
        vacancy_id=payload.vacancy_id,
        branch_id=(payload.branch_id or (v.branch_id if v else None)
                   or cand.branch_id or user.branch_id),
        stage="new", stage_since=today,
        source=payload.source or cand.source,
        owner_id=user.id, note=payload.note,
        created_by=user.id)
    db.add(a); db.commit(); db.refresh(a)
    _ensure_public_id(db, "application", a)
    db.add(models.ApplicationStageLog(
        application_id=a.id, from_stage=None, to_stage="new",
        days_in_stage=0, by_user_id=user.id))
    db.commit(); db.refresh(a)

    audit.log(db, user, entity="application", action="create",
              entity_id=a.id, entity_label=cand.full_name,
              branch_id=a.branch_id,
              new_value=v.title if v else None, commit=True)
    return _app_out(db, a, full=True)

@router.post("/api/ats/applications/{aid}/move")
def ats_application_move(aid: int, payload: schemas.ApplicationMove,
                         db: Session = Depends(get_db),
                         user=Depends(require_role(*roles.ATS_MANAGE))):
    """Bosqichni o'zgartirish. Har o'zgarish TARIXGA yoziladi —
    voronka tahlili faqat shu tarixdan chiqadi."""
    a = db.query(models.CandidateApplication).get(aid)
    if not a:
        raise HTTPException(404, "Ariza topilmadi")
    if payload.stage not in roles.APPLICATION_LABELS:
        raise HTTPException(400, "Bunday bosqich yo'q")
    if a.stage == payload.stage:
        return _app_out(db, a, full=True)
    if a.stage in roles.APPLICATION_CLOSED \
            and payload.stage in roles.APPLICATION_CLOSED:
        raise HTTPException(400, "Ariza allaqachon yopilgan")

    # Rad etish sababsiz bo'lmaydi: statistika shundan yig'iladi va
    # "nega odam topilmayapti" degan savolga javob beradi
    if payload.stage == "rejected" and not payload.reason:
        raise HTTPException(400, "Rad etish sababini tanlang")

    today = roles.local_today()
    since = a.stage_since or (a.created_at.date() if a.created_at else today)
    old = a.stage

    a.stage = payload.stage
    a.stage_since = today
    if payload.note:
        a.note = payload.note
    if payload.stage == "rejected":
        a.reject_reason = payload.reason
        a.reject_note = payload.note
        # Sabab nomzodda bo'lmasa — talent poolga
        auto_pool = payload.reason in roles.POOL_WORTHY
        a.pool = 1 if (payload.pool
                       if payload.pool is not None else auto_pool) else 0
    if payload.stage in roles.APPLICATION_CLOSED:
        a.closed_at = today

    db.add(models.ApplicationStageLog(
        application_id=a.id, from_stage=old, to_stage=payload.stage,
        days_in_stage=(today - since).days,
        reason=payload.reason, note=payload.note, by_user_id=user.id))

    # Nomzod kartasidagi bosqich ham yangilansin — eski ekranlar
    # ishlashda davom etsin
    cand = db.query(models.Candidate).get(a.candidate_id)
    if cand:
        mapping = {"new": "applied", "screening": "screening",
                   "phone": "interview", "interview": "interview",
                   "task": "demo", "demo": "demo",
                   "reference": "offer", "offer": "offer",
                   "hired": "hired", "rejected": "rejected"}
        if payload.stage in mapping:
            cand.stage = mapping[payload.stage]
        if payload.stage == "hired":
            cand.hired_date = today
        if payload.stage in roles.APPLICATION_CLOSED:
            cand.closed_date = today
    db.commit(); db.refresh(a)

    audit.log(db, user, entity="application", action="move",
              entity_id=a.id,
              entity_label=cand.full_name if cand else None,
              branch_id=a.branch_id,
              old_value=roles.APPLICATION_LABELS.get(old, old),
              new_value=roles.APPLICATION_LABELS.get(payload.stage),
              note=payload.reason, commit=True)
    return _app_out(db, a, full=True)

@router.post("/api/ats/applications/{aid}/pool")
def ats_application_pool(aid: int, payload: schemas.ExamOrderDecision,
                         db: Session = Depends(get_db),
                         user=Depends(require_role(*roles.ATS_MANAGE))):
    """Talent poolga qo'shish yoki chiqarish."""
    a = db.query(models.CandidateApplication).get(aid)
    if not a:
        raise HTTPException(404, "Ariza topilmadi")
    a.pool = 0 if a.pool else 1
    a.pool_note = payload.note
    db.commit()
    audit.log(db, user, entity="application", action="pool",
              entity_id=a.id, new_value="qo'shildi" if a.pool else "chiqarildi",
              commit=True)
    return _app_out(db, a, full=True)

@router.get("/api/ats/interviews")
def ats_interviews(days: int = 14, mine: bool = False,
                   db: Session = Depends(get_db),
                   user=Depends(require_role(*roles.ATS_VIEW))):
    """Yaqin kunlardagi suhbatlar."""
    today = roles.local_today()
    q = db.query(models.Interview).filter(
        models.Interview.date >= today - timedelta(days=2),
        models.Interview.date <= today + timedelta(days=days))
    if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
        q = q.filter(_branch_in(db, user, models.Interview.branch_id))
    if mine:
        q = q.filter(models.Interview.interviewer_id == user.id)
    rows = [_interview_out(db, i) for i in
            q.order_by(models.Interview.date, models.Interview.time).all()]
    return {
        "rows": rows,
        "today": [r for r in rows if r["date"] == today.isoformat()],
        # Suhbat bo'lib o'tgan, lekin baholash varaqasi yo'q —
        # eng ko'p unutiladigan qadam
        "missing_scorecard": [r for r in rows if r["status"] == "done"
                              and not r["has_scorecard"]],
        **_ats_form(db),
    }

@router.post("/api/ats/interviews")
def ats_interview_add(payload: schemas.InterviewIn,
                      db: Session = Depends(get_db),
                      user=Depends(require_role(*roles.ATS_MANAGE))):
    a = db.query(models.CandidateApplication).get(payload.application_id)
    if not a:
        raise HTTPException(404, "Ariza topilmadi")
    if a.stage in roles.APPLICATION_CLOSED:
        raise HTTPException(400, "Yopilgan arizaga suhbat qo'yilmaydi")
    if payload.kind not in roles.INTERVIEW_KIND_LABELS:
        raise HTTPException(400, "Suhbat turi noto'g'ri")
    if payload.date < roles.local_today():
        raise HTTPException(400, "O'tib ketgan sanaga suhbat qo'yilmaydi")

    i = models.Interview(
        application_id=a.id, candidate_id=a.candidate_id,
        branch_id=a.branch_id, kind=payload.kind,
        date=payload.date, time=payload.time,
        minutes=payload.minutes or roles.INTERVIEW_MINUTES.get(payload.kind),
        place=payload.place, room_id=payload.room_id,
        interviewer_id=payload.interviewer_id or user.id,
        status="planned", note=payload.note, created_by=user.id)
    db.add(i); db.commit(); db.refresh(i)
    _ensure_public_id(db, "interview", i)
    db.commit(); db.refresh(i)

    # Suhbat o'tkazuvchiga vazifa — kalendarga qarab yurmasin
    cand = db.query(models.Candidate).get(a.candidate_id)
    if i.interviewer_id and i.interviewer_id != user.id:
        _hr_task_for(db, i.interviewer_id,
                     title=f"Suhbat {i.public_id}",
                     body=(f"{cand.full_name if cand else '—'} — "
                           f"{roles.INTERVIEW_KIND_LABELS.get(i.kind)}. "
                           f"{roles.uz_date_full(i.date)} {i.time or ''}"),
                     branch_id=a.branch_id,
                     days=max(1, (i.date - roles.local_today()).days))
        db.commit()

    audit.log(db, user, entity="interview", action="create",
              entity_id=i.id,
              entity_label=cand.full_name if cand else None,
              branch_id=a.branch_id,
              new_value=f"{roles.uz_date_full(i.date)} {i.time or ''}".strip(),
              commit=True)
    return _interview_out(db, i)

@router.post("/api/ats/interviews/{iid}/status")
def ats_interview_status(iid: int, payload: schemas.InterviewStatusIn,
                         db: Session = Depends(get_db),
                         user=Depends(require_role(*roles.ATS_MANAGE))):
    i = db.query(models.Interview).get(iid)
    if not i:
        raise HTTPException(404, "Suhbat topilmadi")
    if payload.status not in roles.INTERVIEW_STATUS_LABELS:
        raise HTTPException(400, "Holat noto'g'ri")
    i.status = payload.status
    if payload.note:
        i.note = payload.note

    # Nomzod kelmagan bo'lsa — bu ham ma'lumot, arizaga yoziladi
    if payload.status == "no_show":
        a = db.query(models.CandidateApplication).get(i.application_id)
        if a and a.stage not in roles.APPLICATION_CLOSED:
            db.add(models.ApplicationStageLog(
                application_id=a.id, from_stage=a.stage, to_stage=a.stage,
                days_in_stage=0, reason="no_show",
                note="Suhbatga kelmadi", by_user_id=user.id))
    db.commit()
    audit.log(db, user, entity="interview", action="status",
              entity_id=i.id, new_value=payload.status, commit=True)
    return _interview_out(db, i)

@router.get("/api/ats/scorecards/{aid}")
def ats_scorecards(aid: int, db: Session = Depends(get_db),
                   user=Depends(require_role(*roles.ATS_VIEW))):
    a = db.query(models.CandidateApplication).get(aid)
    if not a:
        raise HTTPException(404, "Ariza topilmadi")
    cards = db.query(models.Scorecard).filter(
        models.Scorecard.application_id == aid).all()
    rows = [_scorecard_out(db, s) for s in cards]
    vals = [r["percent"] for r in rows if r["percent"] is not None]
    avg = round(sum(vals) / len(vals), 1) if vals else None
    lbl, tone = roles.scorecard_band(avg)

    # Kompetensiya kesimida o'rtacha — nimada kuchli, nimada zaif
    by_comp = []
    for k, label, grp, w in roles.COMPETENCIES:
        vs = [r["scores"].get(k) for r in rows if r["scores"].get(k)]
        by_comp.append({
            "key": k, "label": label, "group": grp, "weight": w,
            "avg": round(sum(vs) / len(vs), 1) if vs else None,
            "votes": len(vs),
        })
    return {
        "application_id": aid,
        "rows": rows,
        "avg_percent": avg, "avg_label": lbl, "avg_tone": tone,
        "by_competency": by_comp,
        "mine": next((r for r in rows if r["author_id"] == user.id), None),
        **_ats_form(db),
        "hint": ("Har bir suhbatdosh o'z varaqasini alohida "
                 "to'ldiradi. Ballar o'rtachasi emas, FIKRLAR "
                 "TARQOQLIGI muhim: hamma bir xil deganda qaror "
                 "oson, tarqoq bo'lsa muhokama kerak."),
    }

@router.post("/api/ats/scorecards")
def ats_scorecard_save(payload: schemas.ScorecardIn,
                       db: Session = Depends(get_db),
                       user=Depends(require_role(*roles.INTERVIEWERS))):
    """Baholash varaqasi. Har suhbatdoshning O'Z varaqasi bo'ladi va
    boshqasinikini o'zgartira olmaydi — aks holda kuchli ovoz
    boshqalarnikini bosib ketardi."""
    a = db.query(models.CandidateApplication).get(payload.application_id)
    if not a:
        raise HTTPException(404, "Ariza topilmadi")

    clean = {}
    for k, v in (payload.scores or {}).items():
        if k not in roles.COMPETENCY_LABELS:
            continue
        if v is None or v == "":
            continue
        try:
            iv = int(v)
        except (TypeError, ValueError):
            raise HTTPException(400, f"{k}: baho butun son bo'lishi kerak")
        if not (roles.SCORE_MIN <= iv <= roles.SCORE_MAX):
            raise HTTPException(
                400, f"Baho {roles.SCORE_MIN} dan {roles.SCORE_MAX} gacha")
        clean[k] = iv
    if payload.recommendation and \
            payload.recommendation not in roles.RECOMMENDATION_LABELS:
        raise HTTPException(400, "Tavsiya noto'g'ri")

    s = db.query(models.Scorecard).filter(
        models.Scorecard.application_id == a.id,
        models.Scorecard.author_id == user.id,
        models.Scorecard.interview_id == payload.interview_id).first()
    if not s:
        s = models.Scorecard(application_id=a.id, author_id=user.id,
                             interview_id=payload.interview_id)
        db.add(s)
    s.scores = json.dumps(clean, ensure_ascii=False)
    # Foiz SERVERDA hisoblanadi — qo'lda yozib bo'lmaydi
    s.percent = roles.scorecard_percent(clean)
    s.recommendation = payload.recommendation
    s.strengths = payload.strengths
    s.concerns = payload.concerns
    s.note = payload.note
    db.commit(); db.refresh(s)

    audit.log(db, user, entity="scorecard", action="save",
              entity_id=s.id, branch_id=a.branch_id,
              new_value=f"{s.percent}% · {payload.recommendation or '—'}",
              commit=True)
    return _scorecard_out(db, s)

@router.get("/api/ats/questions")
def ats_questions(competency: str | None = None,
                  db: Session = Depends(get_db),
                  user=Depends(require_role(*roles.ATS_VIEW))):
    """Savollar bankisi — suhbatdosh nimani so'rashni o'ylab
    o'tirmasin va har nomzodga bir xil savol berilsin."""
    rows = [{"competency": c, "label": roles.COMPETENCY_LABELS.get(c, c),
             "group": roles.COMPETENCY_GROUP.get(c), "text": q}
            for c, q in roles.QUESTION_BANK
            if not competency or c == competency]
    return {
        "rows": rows,
        "competencies": [{"key": k, "label": l, "group": g}
                         for k, l, g, _w in roles.COMPETENCIES],
        "hint": ("Har nomzodga bir xil savol berilsa, javoblarni "
                 "solishtirish mumkin bo'ladi."),
    }

def _offer_out(db: Session, o: models.Offer) -> dict:
    cand = (db.query(models.Candidate).get(o.candidate_id)
            if o.candidate_id else None)
    who = (db.query(models.User).get(o.approved_by)
           if o.approved_by else None)
    return {
        "id": o.id, "public_id": o.public_id,
        "application_id": o.application_id,
        "candidate_id": o.candidate_id,
        "candidate": cand.full_name if cand else None,
        "version": o.version or 1,
        "previous_id": o.previous_id,
        "position": o.position,
        "salary": o.salary,
        "salary_note": o.salary_note,
        "start_date": o.start_date.isoformat() if o.start_date else None,
        "probation_months": o.probation_months,
        "terms": o.terms,
        "status": o.status,
        "status_label": roles.OFFER_LABELS.get(o.status, o.status),
        "status_tone": roles.OFFER_TONE.get(o.status, "slate"),
        "open": o.status in roles.OFFER_OPEN,
        "valid_until": o.valid_until.isoformat() if o.valid_until else None,
        "decline_reason": o.decline_reason,
        "approved_by": who.full_name if who else None,
        "sent_at": o.sent_at.isoformat() if o.sent_at else None,
        "answered_at": o.answered_at.isoformat() if o.answered_at else None,
        "created_at": o.created_at.isoformat() if o.created_at else None,
    }

@router.get("/api/ats/offers")
def offers_list(application_id: int | None = None,
                db: Session = Depends(get_db),
                user=Depends(require_role(*roles.ATS_VIEW))):
    q = scope_to_branch(db.query(models.Offer), models.Offer, user)
    if application_id:
        q = q.filter(models.Offer.application_id == application_id)
    rows = [_offer_out(db, o) for o in
            q.order_by(models.Offer.id.desc()).limit(200).all()]
    return {
        "rows": rows,
        "pending_approval": [r for r in rows if r["status"] == "approval"],
        "statuses": [{"key": k, "label": l, "tone": t}
                     for k, l, t in roles.OFFER_STATUSES],
        "valid_days": roles.OFFER_VALID_DAYS,
        "can_approve": user.role in tuple(roles.OFFER_APPROVE),
        "hint": ("Taklif tasdiqsiz yuborilmaydi — unda pul bor. "
                 "Muzokarada eski taklif o'chirilmaydi, yangi versiya "
                 "ochiladi."),
    }

@router.post("/api/ats/offers")
def offer_create(payload: schemas.OfferIn,
                 db: Session = Depends(get_db),
                 user=Depends(require_role(*roles.OFFER_CREATE))):
    a = db.query(models.CandidateApplication).get(payload.application_id)
    if not a:
        raise HTTPException(404, "Ariza topilmadi")
    if a.stage in roles.APPLICATION_CLOSED and a.stage != "hired":
        raise HTTPException(400, "Yopilgan arizaga taklif berilmaydi")
    if not payload.salary or payload.salary <= 0:
        raise HTTPException(400, "Ish haqini kiriting")

    # Ochiq taklif borligida yangisi ochilmaydi — avval eskisini yoping
    prev = db.query(models.Offer).filter(
        models.Offer.application_id == a.id,
        models.Offer.status.in_(roles.OFFER_OPEN)).first()
    if prev:
        raise HTTPException(
            400, f"Bu arizada ochiq taklif bor ({prev.public_id}). "
                 f"Avval uni yakunlang yoki qaytarib oling.")

    last = (db.query(models.Offer)
            .filter(models.Offer.application_id == a.id)
            .order_by(models.Offer.version.desc()).first())
    o = models.Offer(
        application_id=a.id, candidate_id=a.candidate_id,
        branch_id=a.branch_id,
        version=(last.version + 1) if last else 1,
        previous_id=last.id if last else None,
        position=payload.position, salary=payload.salary,
        salary_note=payload.salary_note,
        start_date=payload.start_date,
        probation_months=payload.probation_months,
        terms=payload.terms,
        status="draft", created_by=user.id)
    db.add(o); db.commit(); db.refresh(o)
    _ensure_public_id(db, "offer", o)
    db.commit(); db.refresh(o)
    audit.log(db, user, entity="offer", action="create",
              entity_id=o.id, branch_id=o.branch_id,
              new_value=f"v{o.version} · {o.salary:,.0f}".replace(",", " "),
              commit=True)
    return _offer_out(db, o)

@router.post("/api/ats/offers/{oid}/action")
def offer_action(oid: int, payload: schemas.OfferAction,
                 db: Session = Depends(get_db),
                 user=Depends(require_role(
                     *(roles.ATS_VIEW + roles.OFFER_APPROVE)))):
    """Taklif holat mashinasi. Chetlab o'tish yo'q: qoralama birdan
    "qabul qilindi" bo'la olmaydi."""
    o = db.query(models.Offer).get(oid)
    if not o:
        raise HTTPException(404, "Taklif topilmadi")

    nxt = roles.offer_next(o.status, payload.action)
    if not nxt:
        raise HTTPException(
            400, f"'{roles.OFFER_LABELS.get(o.status)}' holatidan bu "
                 f"amal bajarilmaydi")

    # Tasdiqlash faqat asoschi/moliya — taklifda pul bor
    if payload.action in ("approve", "reject") and \
            user.role not in tuple(roles.OFFER_APPROVE):
        raise HTTPException(403, "Taklifni faqat rahbariyat tasdiqlaydi")
    if payload.action in ("submit", "send", "withdraw", "accept",
                          "decline", "expire") and \
            user.role not in tuple(roles.OFFER_CREATE):
        raise HTTPException(403, "Ruxsat yo'q")

    o.status = nxt
    now = datetime.utcnow()
    today = roles.local_today()
    if payload.action == "approve":
        o.approved_by = user.id
        o.approved_at = now
    elif payload.action == "send":
        o.sent_at = now
        o.valid_until = today + timedelta(days=roles.OFFER_VALID_DAYS)
    elif payload.action in ("accept", "decline"):
        o.answered_at = now
        if payload.action == "decline":
            o.decline_reason = payload.note
    db.commit(); db.refresh(o)

    # Nomzod qabul qilsa — ariza va nomzod ham "olindi" bo'ladi
    if payload.action == "accept":
        a = db.query(models.CandidateApplication).get(o.application_id)
        if a and a.stage not in roles.APPLICATION_CLOSED:
            since = a.stage_since or today
            db.add(models.ApplicationStageLog(
                application_id=a.id, from_stage=a.stage, to_stage="hired",
                days_in_stage=(today - since).days,
                note=f"Taklif {o.public_id} qabul qilindi",
                by_user_id=user.id))
            a.stage = "hired"
            a.stage_since = today
            a.closed_at = today
            cand = db.query(models.Candidate).get(a.candidate_id)
            if cand:
                cand.stage = "hired"
                cand.hired_date = today
            db.commit()

    audit.log(db, user, entity="offer", action=payload.action,
              entity_id=o.id, branch_id=o.branch_id,
              new_value=roles.OFFER_LABELS.get(nxt),
              note=payload.note, commit=True)
    return _offer_out(db, o)



# =====================================================================
#  OCHIQ ARIZA FORMASI (2026-08-12, Jahongir): "HR nomzodlarga link
#  tashlasa, nomzod to'ldirsa avtomat bazaga yoziladigan funksiya
#  kerak ishga topshirayotganlar uchun... to'ldirsa HR bo'limi
#  nomzodlar bo'limiga tushsin".
#  LOGINSIZ ishlaydi: https://jonyos.uz/apply
# =====================================================================
# 2026-08-15: ro'yxat roles.py ga ko'chdi — ariza formasi va
# nomzodlar filtri bir manbadan oziqlansin.
_APPLY_POSITIONS = dict(roles.APPLY_POSITIONS)
_APPLY_CERT_REQUIRED = ("teacher", "examiner", "support")
_APPLY_MARITAL = dict(roles.APPLY_MARITAL)


@router.post("/api/apply")
def public_apply(payload: dict, db: Session = Depends(get_db)):
    """Nomzodning o'zi to'ldiradigan ochiq ariza. Auth YO'Q."""
    def _s(key, limit=300):
        return str(payload.get(key) or "").strip()[:limit]

    full_name = _s("full_name", 120)
    phone = _s("phone", 40)
    position = _s("position", 20)
    if len(full_name) < 5:
        raise HTTPException(400, "F.I.Sh to'liq yozilishi kerak")
    if len(phone) < 7:
        raise HTTPException(400, "Telefon raqam noto'g'ri")
    if position not in _APPLY_POSITIONS:
        raise HTTPException(400, "Lavozim tanlanmagan")

    photo = payload.get("photo") or ""
    cert = payload.get("certificate") or ""
    if not (isinstance(photo, str) and photo.startswith("data:image")
            and len(photo) > 100):
        raise HTTPException(400, "Shaxsiy fotosurat yuklanishi shart")
    if len(photo) > 600_000:
        raise HTTPException(400, "Fotosurat juda katta (400KB gacha)")
    if position in _APPLY_CERT_REQUIRED:
        if not (isinstance(cert, str) and cert.startswith("data:")
                and len(cert) > 100):
            raise HTTPException(
                400, "Bu lavozim uchun sertifikat yuklash shart")
        if len(cert) > 4_000_000:
            raise HTTPException(400, "Sertifikat juda katta (3MB gacha)")
    else:
        cert = ""

    # Takror bosishdan himoya: bir xil telefon + ism 24 soat ichida
    day_ago = datetime.utcnow() - timedelta(hours=24)
    dup = (db.query(models.Candidate)
           .filter(models.Candidate.phone == phone,
                   models.Candidate.created_at >= day_ago).count())
    if dup:
        return {"ok": True, "already": True}

    marital = _s("marital", 20)
    other_position = _s("other_position", 100)
    pos_label = _APPLY_POSITIONS[position]
    if position == "other" and other_position:
        pos_label = f"Boshqa: {other_position}"

    note_lines = _apply_note_lines(lambda k: _s(k, 300), pos_label,
                                   position == "teacher")
    note_lines.append("Manba: onlayn ariza (https://jonyos.uz/apply)")

    exp_years = None
    try:
        if payload.get("experience_years") not in (None, ""):
            exp_years = float(payload.get("experience_years"))
    except Exception:
        exp_years = None

    c = models.Candidate(
        full_name=full_name,
        phone=phone,
        stage="applied",
        source="other",
        note="\n".join(note_lines),
        workplaces=_s("workplaces", 1000) or None,
        experience_years=exp_years,
        created_by="Onlayn ariza",
    )
    # 2026-08-15: javoblar ALOHIDA maydonlarga ham yoziladi —
    # ro'yxatda ko'rinadi, filtr qilinadi va keyin tahrirlanadi.
    _apply_fill(c, lambda k: _s(k, 300), position)
    db.add(c)
    db.commit()
    db.refresh(c)

    def _att(data_url: str, kind: str, fname: str):
        # Ko'rish oynasi data ni XOM base64 kutadi (data: prefiksisiz)
        try:
            head, b64 = data_url.split(",", 1)
            mime = head.split(";", 1)[0].split(":", 1)[1]
        except Exception:
            mime, b64 = "application/octet-stream", data_url
        db.add(models.Attachment(
            entity="candidate", entity_id=c.id, kind=kind,
            filename=fname, mime=mime, size=len(b64),
            data=b64, created_by="Onlayn ariza"))

    _att(photo, "photo", f"foto_{c.id}.jpg")
    if cert:
        _att(cert, "certificate", f"sertifikat_{c.id}")
    db.commit()

    # Quvurga ham tushsin (2026-08-12: "arizada topshirib ko'rgandik,
    # quvurda ko'rinmadi") - Ishga olish quvuri CandidateApplication
    # dan o'qiydi, shuning uchun ariza ham ochamiz.
    try:
        a = models.CandidateApplication(
            candidate_id=c.id, vacancy_id=None, branch_id=None,
            stage="new", stage_since=date.today(),
            source="other",
            note=f"Onlayn ariza: {pos_label}")
        db.add(a); db.commit(); db.refresh(a)
        _ensure_public_id(db, "application", a)
        db.add(models.ApplicationStageLog(
            application_id=a.id, from_stage=None, to_stage="new",
            days_in_stage=0))
        db.commit()
    except Exception:
        db.rollback()

    # HR'ga xabar bo'lib tushsin
    try:
        hr_users = (db.query(models.User)
                    .filter(models.User.role == roles.HR_MANAGER,
                            models.User.is_active == 1).all())
        for h in hr_users:
            db.add(models.Task(
                title=f"Yangi nomzod: {full_name}",
                description=(f"{pos_label} lavozimiga onlayn ariza "
                             f"keldi. Tel: {phone}. HR -> Nomzodlar "
                             f"bo'limida ko'ring."),
                assignee_id=h.id,
                deadline=date.today() + timedelta(days=2),
                priority="high", source="manual",
                created_by="Onlayn ariza"))
        db.commit()
    except Exception:
        db.rollback()

    return {"ok": True, "id": c.id}



def backfill_apply_applications(db: Session) -> int:
    """Quvurda ko'rinmayotgan nomzodlarga ariza ochib qo'yadi.

    2026-08-12: onlayn arizadan kelganlar uchun edi.
    2026-08-15 (Jahongir: "qo'lda nomzod kiritsam bu joyga
    chiqmayabdi"): endi MANBADAN QAT'IY NAZAR — qo'lda kiritilgan
    nomzodlar ham quvurga tushadi. Bosqichi nomzod kartasidagidan
    olinadi, ya'ni allaqachon suhbatga chaqirilgani "Yangi ariza"
    ustuniga tushib qolmaydi."""
    from common import _seed_done, _seed_mark
    if _seed_done(db, "apply_backfill_v2"):
        return 0
    made = 0
    for c in db.query(models.Candidate).all():
        has = (db.query(models.CandidateApplication)
               .filter(models.CandidateApplication.candidate_id == c.id)
               .count())
        if has:
            continue
        try:
            _open_application(db, c, None, note="Avvaldan kiritilgan")
            made += 1
        except Exception:
            db.rollback()
    db.commit()
    _seed_mark(db, "apply_backfill_v2")
    return made


def fix_apply_attachments(db: Session) -> int:
    """Onlayn arizadan kelgan fayllar data: prefiksi bilan saqlangan
    edi - rasm ochilmasdi (2026-08-12). Xom base64 ga o'tkazamiz."""
    from common import _seed_done, _seed_mark
    if _seed_done(db, "apply_att_fix_v1"):
        return 0
    fixed = 0
    rows = (db.query(models.Attachment)
            .filter(models.Attachment.created_by == "Onlayn ariza").all())
    for a in rows:
        d = a.data or ""
        if d.startswith("data:"):
            try:
                head, b64 = d.split(",", 1)
                a.mime = head.split(";", 1)[0].split(":", 1)[1]
                a.data = b64
                a.size = len(b64)
                fixed += 1
            except Exception:
                pass
    db.commit()
    _seed_mark(db, "apply_att_fix_v1")
    return fixed
