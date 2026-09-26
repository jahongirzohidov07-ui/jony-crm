"""Auto-extracted from main.py during refactor (split-main). Domain: content."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bisect
import json
from datetime import date, datetime, timedelta
from typing import List, Optional

from fastapi import (APIRouter, Body, Depends, FastAPI, HTTPException,
                     Request)
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

def _content_code(c: models.Content) -> str:
    """CONTENT-JA-2026-0048 — atributsiya shu raqamga bog'lanadi."""
    year = (c.planned_date or c.created_at or datetime.utcnow()).year \
        if not isinstance(c.created_at, type(None)) else date.today().year
    return f"CONTENT-JA-{year}-{c.id:04d}"

def _approver_role(c: models.Content) -> str | None:
    """Kontentni kim tasdiqlashi kerak. Narx yoki aksiya bo'lsa —
    sotuv rahbari, rasmiy bayonot bo'lsa — asoschi."""
    if c.goal == "sales" and (c.promo_code or "aksiya" in (c.message or "").lower()):
        return roles.SALES_HEAD
    return roles.APPROVAL_BY_PILLAR.get(c.pillar or "", roles.SMM_MANAGER)

def _content_warnings(db: Session, c: models.Content,
                      today: date | None = None) -> list:
    """Kontentdagi muammolar. Tizim ularni o'zi topadi — SMM
    eslab qolishi shart emas."""
    today = today or date.today()
    out = []
    if c.status in roles.CONTENT_LIVE or c.status == "cancelled":
        if c.status == "published" and not c.post_url:
            out.append({"key": "no_link", "severity": "warn",
                        "text": "Joylandi, lekin havolasi kiritilmagan"})
        return out

    near = c.planned_date and (c.planned_date - today).days <= 1
    if c.planned_date and c.planned_date < today:
        out.append({"key": "late", "severity": "block",
                    "text": f"Muddat o'tdi ({c.planned_date.isoformat()})"})
    if near and c.status in ("idea", "script") and not (c.script or "").strip():
        out.append({"key": "no_script", "severity": "block",
                    "text": "Chiqish vaqti yaqin, ssenariy tayyor emas"})
    if near and c.status in ("shooting", "editing"):
        out.append({"key": "no_design", "severity": "block",
                    "text": "Bugun chiqishi kerak, material hali tayyor emas"})
    if c.needs_consent and not c.consent_ok:
        out.append({"key": "consent", "severity": "block",
                    "text": "O'quvchi rasmi bor — ota-ona roziligi "
                            "belgilanmagan"})
    if c.status == "ready" and not (c.cta or "").strip():
        out.append({"key": "no_cta", "severity": "warn",
                    "text": "CTA yozilmagan"})
    return out

def _content_out(db: Session, c: models.Content, *, full: bool = False,
                 users: dict | None = None) -> dict:
    users = users if users is not None else {
        u.id: u.full_name for u in db.query(models.User).all()}
    warn = _content_warnings(db, c)
    row = {
        "id": c.id,
        "code": c.content_id or _content_code(c),
        "title": c.title,
        "platform": c.platform,
        "platform_label": roles.PLATFORM_LABELS.get(c.platform or "", "—"),
        "platform_tone": roles.PLATFORM_TONE.get(c.platform or "", "slate"),
        "format": c.fmt,
        "format_label": roles.FORMAT_LABELS.get(c.fmt or "", "—"),
        "pillar": c.pillar,
        "pillar_label": roles.PILLAR_LABELS.get(c.pillar or "", "—"),
        "pillar_tone": roles.PILLAR_TONE.get(c.pillar or "", "slate"),
        "goal": c.goal,
        "goal_label": roles.GOAL_LABELS.get(c.goal or "", "—"),
        "goal_metric": roles.GOAL_METRIC_LABELS.get(
            roles.GOAL_METRIC.get(c.goal or "", ""), "—"),
        "funnel": c.funnel,
        "funnel_label": roles.FUNNEL_LABELS.get(c.funnel or "", "—"),
        "branch": c.branch.name if c.branch else None,
        "branch_id": c.branch_id,
        "course": c.course,
        "campaign_id": c.campaign_id,
        "status": c.status,
        "status_label": roles.CONTENT_STATUS_LABELS.get(c.status, c.status),
        "tone": roles.CONTENT_STATUS_TONE.get(c.status, "slate"),
        "planned_date": (c.planned_date.isoformat()
                         if c.planned_date else None),
        "planned_time": c.planned_time,
        "published_at": (c.published_at.isoformat()
                         if c.published_at else None),
        "owner": users.get(c.owner_id),
        "owner_id": c.owner_id,
        "approver": users.get(c.approver_id),
        "approver_role": _approver_role(c),
        "approver_role_label": roles.UZ_LABELS.get(_approver_role(c) or "", "—"),
        "priority": c.priority,
        "deadline": c.deadline.isoformat() if c.deadline else None,
        "needs_consent": bool(c.needs_consent),
        "consent_ok": bool(c.consent_ok),
        "post_url": c.post_url,
        "warnings": warn,
        "blocked": any(w["severity"] == "block" for w in warn),
    }
    if not full:
        return row

    row.update({
        "audience": c.audience,
        "problem": c.problem, "message": c.message, "hook": c.hook,
        "location": c.location, "participants": c.participants,
        "props": c.props, "duration": c.duration, "music": c.music,
        "design_format": c.design_format, "cta": c.cta,
        "references": c.references,
        "script": c.script, "caption": c.caption,
        "caption_ru": c.caption_ru, "caption_en": c.caption_en,
        "hashtags": c.hashtags, "story_text": c.story_text,
        "on_video_text": c.on_video_text,
        "utm": c.utm, "short_link": c.short_link,
        "promo_code": c.promo_code,
        "post_external_id": c.post_external_id,
        "note": c.note,
        "team": {
            "copywriter": users.get(c.copywriter_id),
            "designer": users.get(c.designer_id),
            "videographer": users.get(c.videographer_id),
            "editor": users.get(c.editor_id),
        },
        "shots": [{
            "id": s.id, "no": s.order_no, "text": s.text,
            "state": s.state, "note": s.note,
        } for s in sorted(c.shots, key=lambda x: x.order_no)],
        "approvals": [{
            "id": a.id, "role": a.role,
            "role_label": roles.UZ_LABELS.get(a.role or "", "—"),
            "decision": a.decision,
            "decision_label": roles.APPROVAL_LABELS.get(a.decision or "", "—"),
            "tone": roles.APPROVAL_TONE.get(a.decision or "", "slate"),
            "comment": a.comment, "quote": a.quote,
            "by": users.get(a.decided_by),
            "date": a.decided_at.isoformat() if a.decided_at else None,
        } for a in sorted(c.approvals, key=lambda x: -x.id)],
        "versions": [{
            "id": v.id, "field": v.field,
            "old": v.old_value, "new": v.new_value,
            "by": v.changed_by,
            "date": v.created_at.isoformat() if v.created_at else None,
        } for v in sorted(c.versions, key=lambda x: -x.id)[:40]],
    })
    return row

def _content_scope(db: Session, user: models.User, branch_id=None):
    q = db.query(models.Content)
    if branch_id:
        q = q.filter(models.Content.branch_id == branch_id)
    elif user.branch_id and user.role not in roles.ORG_WIDE_ROLES:
        q = q.filter((models.Content.branch_id == user.branch_id)
                     | (models.Content.branch_id.is_(None)))
    return q

@router.get("/api/content-meta")
def content_meta(
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.CONTENT_REQUESTER)),
):
    """Kontent uchun barcha ro'yxatlar: status, platforma, maqsad,
    yo'nalish. Frontend ularni qattiq yozib qo'ymaydi."""
    return {
        "statuses": [{"key": k, "label": lbl, "tone": t}
                     for k, lbl, t in roles.CONTENT_STATUSES],
        "flow": roles.CONTENT_FLOW,
        "platforms": [{"key": k, "label": lbl, "tone": t}
                      for k, lbl, t in roles.CONTENT_PLATFORMS],
        "formats": [{"key": k, "label": lbl}
                    for k, lbl in roles.CONTENT_FORMATS],
        "goals": [{"key": k, "label": lbl,
                   "metric": roles.GOAL_METRIC_LABELS.get(m, m)}
                  for k, lbl, m in roles.CONTENT_GOALS],
        "pillars": [{"key": k, "label": lbl, "tone": t, "hint": d}
                    for k, lbl, t, d in roles.CONTENT_PILLARS],
        "funnels": [{"key": k, "label": lbl}
                    for k, lbl in roles.FUNNEL_STAGES],
        "consent": [{"key": k, "label": lbl, "tone": t}
                    for k, lbl, t in roles.CONSENT_STATUSES],
        "idea_statuses": [{"key": k, "label": lbl, "tone": t}
                          for k, lbl, t in roles.IDEA_STATUSES],
        "request_statuses": [{"key": k, "label": lbl, "tone": t}
                             for k, lbl, t in roles.REQUEST_STATUSES],
        "decisions": [{"key": k, "label": lbl, "tone": t}
                      for k, lbl, t in roles.APPROVAL_DECISIONS],
        "plan_target": roles.PLAN_TARGET_PERCENT,
        "can_edit": user.role in roles.SMM_ACCESS,
    }

@router.get("/api/content")
def list_content(
    date_from: str | None = None,
    date_to: str | None = None,
    status: str | None = None,
    platform: str | None = None,
    pillar: str | None = None,
    campaign_id: int | None = None,
    owner_id: int | None = None,
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.CONTENT_REQUESTER)),
):
    """Kontent taqvimi. Sana oralig'i berilsa — o'sha oyning ro'yxati."""
    q = _content_scope(db, user, branch_id)
    if date_from:
        q = q.filter(models.Content.planned_date >= date.fromisoformat(date_from))
    if date_to:
        q = q.filter(models.Content.planned_date <= date.fromisoformat(date_to))
    if status:
        q = q.filter(models.Content.status == status)
    if platform:
        q = q.filter(models.Content.platform == platform)
    if pillar:
        q = q.filter(models.Content.pillar == pillar)
    if campaign_id:
        q = q.filter(models.Content.campaign_id == campaign_id)
    if owner_id:
        q = q.filter(models.Content.owner_id == owner_id)

    rows = q.order_by(models.Content.planned_date,
                      models.Content.planned_time).limit(500).all()
    users = {u.id: u.full_name for u in db.query(models.User).all()}
    out = [_content_out(db, c, users=users) for c in rows]

    # Reja bajarilishi: rejalashtirilganidan nechtasi chiqdi
    planned = [r for r in out if r["planned_date"]]
    published = [r for r in planned if r["status"] in roles.CONTENT_LIVE]
    pct = round(len(published) / len(planned) * 100, 1) if planned else 0.0

    by_status: dict = {}
    for r in out:
        by_status[r["status"]] = by_status.get(r["status"], 0) + 1

    return {
        "rows": out,
        "total": len(out),
        "plan_percent": pct,
        "plan_ok": pct >= roles.PLAN_TARGET_PERCENT,
        "by_status": [{"key": k, "label": roles.CONTENT_STATUS_LABELS.get(k, k),
                       "tone": roles.CONTENT_STATUS_TONE.get(k, "slate"),
                       "count": v}
                      for k, v in sorted(by_status.items(),
                                         key=lambda x: -x[1])],
        "blocked": [r for r in out if r["blocked"]],
    }

@router.post("/api/content")
def create_content(
    payload: schemas.ContentCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.SMM_ACCESS)),
):
    data = payload.model_dump()
    data["needs_consent"] = 1 if data.pop("needs_consent", None) else 0
    c = models.Content(**data, status="idea", created_by=user.full_name)
    c.owner_id = c.owner_id or user.id
    db.add(c)
    db.commit()
    db.refresh(c)
    c.content_id = _content_code(c)
    db.commit()
    return _content_out(db, c, full=True)

@router.get("/api/content/{cid}")
def get_content(
    cid: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.CONTENT_REQUESTER)),
):
    c = db.query(models.Content).get(cid)
    if not c:
        raise HTTPException(404, "Kontent topilmadi")
    return _content_out(db, c, full=True)

_TEXT_FIELDS = ["script", "caption", "caption_ru", "caption_en",
                "hashtags", "story_text", "on_video_text", "hook",
                "message", "cta"]
# Kontent-plan jadvali ustunlari — o'zgarishi tarixga yoziladi
_PLAN_FIELDS = ["title", "planned_date", "planned_time", "platform",
                "audience", "pillar", "funnel", "goal", "fmt", "owner_id",
                "shoot_date", "kpi_target", "proof", "post_url"]

@router.put("/api/content/{cid}")
def update_content(
    cid: int,
    payload: schemas.ContentUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.SMM_ACCESS)),
):
    c = db.query(models.Content).get(cid)
    if not c:
        raise HTTPException(404, "Kontent topilmadi")
    given = payload.model_dump(exclude_unset=True)
    if "title" in given and not (given["title"] or "").strip():
        raise HTTPException(400, "Mavzu bo'sh bo'lmasin")

    for k, v in given.items():
        if k in ("needs_consent", "consent_ok"):
            v = 1 if v else 0
        old = getattr(c, k, None)
        # Matn o'zgarsa eski variant yo'qolmaydi. 2026-09-26: kontent-
        # plan ustunlari ham (SMM menejer "kerakli joylarini" o'zgartiradi
        # — kim, qachon, nimadan nimaga o'zgartirgani tarixda qolsin).
        changed = (str(old) if old is not None else "") != \
            (str(v) if v is not None else "")
        if changed and (k in _TEXT_FIELDS or k in _PLAN_FIELDS):
            db.add(models.ContentVersion(
                content_id=c.id, field=k,
                old_value=str(old) if old is not None else None,
                new_value=str(v) if v is not None else None,
                changed_by=user.full_name))
        # Sana o'zgarsa ko'chish tarixi ham yoziladi (taqvimdagi
        # "Boshqa kunga" bilan bir xil iz)
        if k == "planned_date" and changed:
            db.add(models.ContentMove(
                content_id=c.id, from_date=old, to_date=v,
                reason="Kontent-plandan o'zgartirildi",
                moved_by=user.full_name))
        setattr(c, k, v)
    db.commit()
    return _content_out(db, c, full=True)

@router.post("/api/content/{cid}/status")
def set_content_status(
    cid: int,
    payload: schemas.ContentStatus,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.SMM_ACCESS)),
):
    """Quvurdagi keyingi bosqichga o'tkazish. Tasdiqqa yuborilganda
    tasdiqlovchi O'ZI aniqlanadi."""
    c = db.query(models.Content).get(cid)
    if not c:
        raise HTTPException(404, "Kontent topilmadi")
    if payload.status not in roles.CONTENT_STATUS_LABELS:
        raise HTTPException(400, "Bunday holat yo'q")

    # Roziligi yo'q kontentni joylashga qo'ymaymiz
    if payload.status in ("ready", "published") and c.needs_consent \
            and not c.consent_ok:
        raise HTTPException(400, "O'quvchi roziligi belgilanmagan — "
                                 "joylashga ruxsat yo'q")

    old = c.status
    c.status = payload.status
    if payload.note:
        c.note = payload.note

    if payload.status == "approval":
        role = _approver_role(c)
        exists = (db.query(models.ContentApproval)
                  .filter(models.ContentApproval.content_id == c.id,
                          models.ContentApproval.decision.is_(None)).first())
        if not exists:
            db.add(models.ContentApproval(content_id=c.id, role=role))
        who = (db.query(models.User)
               .filter(models.User.role == role,
                       models.User.is_active == 1).first())
        c.approver_id = who.id if who else None
    db.commit()
    audit.log(db, user, entity="content", action="update", entity_id=c.id,
              entity_label=c.title, old_value=old, new_value=payload.status,
              note="Kontent holati o'zgardi", branch_id=c.branch_id)
    db.commit()
    return _content_out(db, c, full=True)

@router.post("/api/content/{cid}/move")
def move_content(
    cid: int,
    payload: schemas.ContentMoveIn,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.SMM_ACCESS)),
):
    """Taqvimda boshqa kunga ko'chirish. Sababsiz ko'chirilmaydi va
    eski sana tarixda qoladi."""
    if not (payload.reason or "").strip():
        raise HTTPException(400, "Ko'chirish sababini yozing")
    c = db.query(models.Content).get(cid)
    if not c:
        raise HTTPException(404, "Kontent topilmadi")
    old = c.planned_date
    db.add(models.ContentMove(content_id=c.id, from_date=old,
                              to_date=payload.planned_date,
                              reason=payload.reason,
                              moved_by=user.full_name))
    c.planned_date = payload.planned_date
    db.commit()

    # Tasdiqlangan kontent sanasi o'zgarsa rahbar bilishi kerak
    if c.status in ("ready", "approval"):
        role = _approver_role(c)
        who = (db.query(models.User)
               .filter(models.User.role == role,
                       models.User.is_active == 1).first())
        if who:
            t = models.Task(
                title=f"Kontent sanasi o'zgardi: {c.title}",
                description=(f"{old} -> {payload.planned_date}\n"
                             f"Sabab: {payload.reason}\n"
                             f"O'zgartirdi: {user.full_name}"),
                assignee_id=who.id, branch_id=c.branch_id,
                deadline=payload.planned_date, priority="normal",
                source="manual", created_by="Tizim")
            db.add(t)
            db.flush()
            _ensure_public_id(db, "task", t)
            db.commit()
    return _content_out(db, c, full=True)

@router.post("/api/content/{cid}/approve")
def approve_content(
    cid: int,
    payload: schemas.ApprovalIn,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Tasdiqlash qarori. Faqat tasdiqlovchi rol yoki asoschi."""
    c = db.query(models.Content).get(cid)
    if not c:
        raise HTTPException(404, "Kontent topilmadi")
    role = _approver_role(c)
    if user.role not in roles.FULL_ACCESS and user.role != role:
        raise HTTPException(403, "Bu kontentni siz tasdiqlamaysiz")
    if payload.decision not in roles.APPROVAL_LABELS:
        raise HTTPException(400, "Noto'g'ri qaror")

    a = (db.query(models.ContentApproval)
         .filter(models.ContentApproval.content_id == c.id,
                 models.ContentApproval.decision.is_(None)).first())
    if not a:
        a = models.ContentApproval(content_id=c.id, role=role)
        db.add(a)
    a.decision = payload.decision
    a.comment = payload.comment
    a.quote = payload.quote
    a.decided_by = user.id
    a.decided_at = datetime.utcnow()

    if payload.decision == "approved":
        c.status = "ready"
    elif payload.decision in ("changes", "info"):
        c.status = "rework"
    elif payload.decision == "rejected":
        c.status = "cancelled"
    db.commit()
    return _content_out(db, c, full=True)

@router.post("/api/content/{cid}/publish")
def publish_content(
    cid: int,
    payload: schemas.ContentPublish,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.SMM_ACCESS)),
):
    """Joylandi deb belgilash. Havolasiz belgilanmaydi — aks holda
    natijani hech qachon o'lchab bo'lmaydi."""
    c = db.query(models.Content).get(cid)
    if not c:
        raise HTTPException(404, "Kontent topilmadi")
    if not (payload.post_url or "").strip():
        raise HTTPException(400, "Post havolasini kiriting")
    if c.needs_consent and not c.consent_ok:
        raise HTTPException(400, "O'quvchi roziligi belgilanmagan")
    c.post_url = payload.post_url
    c.post_external_id = payload.post_external_id
    c.screenshot = payload.screenshot
    c.published_at = payload.published_at or datetime.utcnow()
    c.status = "measuring"
    db.commit()
    return _content_out(db, c, full=True)

@router.post("/api/content/{cid}/shots")
def add_shot(
    cid: int,
    payload: schemas.ShotIn,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.SMM_ACCESS)),
):
    n = (db.query(models.ContentShot)
         .filter(models.ContentShot.content_id == cid).count())
    s = models.ContentShot(content_id=cid, order_no=n + 1,
                           text=payload.text, state="todo")
    db.add(s)
    db.commit()
    return {"ok": True, "id": s.id}

@router.post("/api/content-shots/{sid}")
def set_shot_state(
    sid: int,
    payload: schemas.ShotState,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.SMM_ACCESS)),
):
    s = db.query(models.ContentShot).get(sid)
    if not s:
        raise HTTPException(404, "Topilmadi")
    s.state = payload.state
    s.note = payload.note
    db.commit()
    return {"ok": True}

@router.put("/api/content/{cid}/metrics")
def set_metrics(
    cid: int,
    payload: schemas.MetricIn,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.SMM_ACCESS)),
):
    m = (db.query(models.ContentMetric)
         .filter(models.ContentMetric.content_id == cid).first())
    if not m:
        m = models.ContentMetric(content_id=cid)
        db.add(m)
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(m, k, v)
    m.updated_by = user.full_name
    db.commit()

    # Sifatli engagement: like emas, foydali harakatlar
    w = roles.ENGAGEMENT_WEIGHT_MAP
    score = ((m.likes or 0) * w["like"] + (m.comments or 0) * w["comment"]
             + (m.saves or 0) * w["save"] + (m.shares or 0) * w["share"]
             + (m.dms or 0) * w["dm"])
    er = round(score / m.reach * 100, 2) if m.reach else 0.0
    return {"ok": True, "quality_score": score, "engagement_rate": er}

@router.get("/api/content-ideas")
def list_ideas(
    status: str | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.IDEA_SUBMIT)),
):
    q = db.query(models.ContentIdea)
    if status:
        q = q.filter(models.ContentIdea.status == status)
    rows = q.order_by(models.ContentIdea.created_at.desc()).limit(300).all()
    counts: dict = {}
    for i in db.query(models.ContentIdea).all():
        counts[i.status] = counts.get(i.status, 0) + 1
    return {
        "rows": [{
            "id": i.id, "title": i.title, "description": i.description,
            "pillar": i.pillar,
            "pillar_label": roles.PILLAR_LABELS.get(i.pillar or "", "—"),
            "platform": i.platform,
            "platform_label": roles.PLATFORM_LABELS.get(i.platform or "", "—"),
            "course": i.course, "audience": i.audience,
            "reference": i.reference, "priority": i.priority,
            "status": i.status,
            "status_label": roles.IDEA_STATUS_LABELS.get(i.status, i.status),
            "tone": roles.IDEA_STATUS_TONE.get(i.status, "slate"),
            "author": i.author, "content_id": i.content_id,
            "date": i.created_at.isoformat() if i.created_at else None,
        } for i in rows],
        "counts": counts,
        "can_triage": user.role in roles.SMM_ACCESS,
    }

@router.post("/api/content-ideas")
def add_idea(
    payload: schemas.IdeaCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.IDEA_SUBMIT)),
):
    """G'oyani har qanday xodim yubora oladi. Lekin SMM
    tasdiqlamaguncha kontent rejaga tushmaydi."""
    i = models.ContentIdea(**payload.model_dump(), status="new",
                           author_id=user.id, author=user.full_name)
    db.add(i)
    db.commit()
    return {"ok": True, "id": i.id}

@router.post("/api/content-ideas/{iid}")
def triage_idea(
    iid: int,
    payload: schemas.IdeaStatus,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.SMM_ACCESS)),
):
    i = db.query(models.ContentIdea).get(iid)
    if not i:
        raise HTTPException(404, "G'oya topilmadi")
    if payload.status not in roles.IDEA_STATUS_LABELS:
        raise HTTPException(400, "Bunday holat yo'q")
    i.status = payload.status
    if payload.note:
        i.note = payload.note

    # Qabul qilingan g'oya kontentga aylanadi
    made = None
    if payload.status == "converted" and not i.content_id:
        c = models.Content(
            title=i.title, platform=i.platform, fmt=i.fmt,
            pillar=i.pillar, branch_id=i.branch_id, course=i.course,
            audience=i.audience, references=i.reference,
            message=i.description, status="idea",
            owner_id=user.id, created_by=user.full_name)
        db.add(c)
        db.commit()
        db.refresh(c)
        c.content_id = _content_code(c)
        i.content_id = c.id
        db.commit()
        made = c.id
    db.commit()
    return {"ok": True, "content_id": made}

@router.get("/api/content-requests")
def list_requests(
    status: str | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.CONTENT_REQUESTER)),
):
    q = db.query(models.ContentRequest)
    if status:
        q = q.filter(models.ContentRequest.status == status)
    rows = q.order_by(models.ContentRequest.created_at.desc()).limit(200).all()
    branches = {b.id: b.name for b in db.query(models.Branch).all()}
    teachers = {t.id: t.full_name for t in db.query(models.Teacher).all()}
    counts: dict = {}
    for r in db.query(models.ContentRequest).all():
        counts[r.status] = counts.get(r.status, 0) + 1
    return {
        "rows": [{
            "id": r.id, "requester": r.requester,
            "department": r.from_department,
            "branch": branches.get(r.branch_id, "—"),
            "course": r.course, "goal": r.goal,
            "goal_label": roles.GOAL_LABELS.get(r.goal or "", "—"),
            "offer": r.offer, "group_time": r.group_time,
            "teacher": teachers.get(r.teacher_id),
            "students_needed": r.students_needed,
            "start_date": r.start_date.isoformat() if r.start_date else None,
            "deadline": r.deadline.isoformat() if r.deadline else None,
            "platforms": r.platforms, "approved_price": r.approved_price,
            "cta": r.cta, "status": r.status,
            "status_label": roles.REQUEST_STATUS_LABELS.get(r.status, r.status),
            "tone": roles.REQUEST_STATUS_TONE.get(r.status, "slate"),
            "smm_note": r.smm_note, "campaign_id": r.campaign_id,
            "date": r.created_at.isoformat() if r.created_at else None,
        } for r in rows],
        "counts": counts,
        "can_decide": user.role in roles.SMM_ACCESS,
    }

@router.post("/api/content-requests")
def add_request(
    payload: schemas.RequestCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.CONTENT_REQUESTER)),
):
    """Boshqa bo'lim SMMga tartibli so'rov yuboradi — Telegramdagi
    tartibsiz topshiriq o'rniga."""
    r = models.ContentRequest(
        **payload.model_dump(), status="new",
        from_department=roles.UZ_LABELS.get(user.role, user.role),
        requested_by=user.id, requester=user.full_name)
    db.add(r)
    db.commit()

    smm = _smm_user(db, r.branch_id)
    if smm:
        t = models.Task(
            title=f"SMM so'rovi: {r.course or 'kontent'} — "
                  f"{branch_name(db, r.branch_id)}",
            description=(f"So'ragan: {user.full_name}\n"
                         f"Maqsad: {roles.GOAL_LABELS.get(r.goal or '', '—')}\n"
                         f"Kerak: {r.students_needed or '—'} o'quvchi\n"
                         f"Boshlanish: {r.start_date or '—'}\n"
                         f"Taklif: {r.offer or '—'}"),
            assignee_id=smm.id, branch_id=r.branch_id,
            deadline=r.deadline, priority="high",
            source="manual", created_by="Tizim")
        db.add(t)
        db.flush()
        _ensure_public_id(db, "task", t)
        db.commit()
    return {"ok": True, "id": r.id}

def branch_name(db: Session, bid) -> str:
    if not bid:
        return "—"
    b = db.query(models.Branch).get(bid)
    return b.name if b else "—"

@router.post("/api/content-requests/{rid}")
def decide_request(
    rid: int,
    payload: schemas.RequestDecision,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.SMM_ACCESS)),
):
    r = db.query(models.ContentRequest).get(rid)
    if not r:
        raise HTTPException(404, "So'rov topilmadi")
    r.status = payload.status
    r.smm_note = payload.smm_note

    # Qabul qilingan so'rov kampaniyaga aylanadi
    if payload.status == "accepted" and not r.campaign_id:
        c = models.Campaign(
            name=f"{r.course or 'Kontent'} — {branch_name(db, r.branch_id)}",
            goal=r.goal, course=r.course, branch_id=r.branch_id,
            offer=r.offer, start_date=r.start_date or date.today(),
            end_date=r.deadline, target_leads=r.students_needed,
            owner_id=user.id, is_active=1)
        db.add(c)
        db.commit()
        r.campaign_id = c.id
    db.commit()
    return {"ok": True, "campaign_id": r.campaign_id}

@router.get("/api/smm/dashboard")
def smm_dashboard(
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.SMM_ACCESS)),
):
    """SMM tizimga kirganda bugungi vaziyat: nima chiqishi kerak, nima
    kechikdi, kimning tasdig'i kutilmoqda va nima xato ketyapti."""
    today = date.today()
    m_start, m_end = billing.month_bounds(today.year, today.month)
    users = {u.id: u.full_name for u in db.query(models.User).all()}

    all_rows = db.query(models.Content).all()
    open_rows = [c for c in all_rows if c.status in roles.CONTENT_OPEN]

    todays = [c for c in open_rows if c.planned_date == today]
    late = [c for c in open_rows
            if c.planned_date and c.planned_date < today]
    waiting = [c for c in all_rows if c.status == "approval"]

    month = [c for c in all_rows
             if c.planned_date and m_start <= c.planned_date <= m_end]
    done = [c for c in month if c.status in roles.CONTENT_LIVE]
    plan_pct = round(len(done) / len(month) * 100, 1) if month else 0.0

    metrics = {m.content_id: m for m in db.query(models.ContentMetric).all()}
    reach = sum((metrics[c.id].reach or 0) for c in month if c.id in metrics)
    eng = 0
    w = roles.ENGAGEMENT_WEIGHT_MAP
    for c in month:
        m = metrics.get(c.id)
        if not m:
            continue
        eng += ((m.likes or 0) * w["like"] + (m.comments or 0) * w["comment"]
                + (m.saves or 0) * w["save"] + (m.shares or 0) * w["share"]
                + (m.dms or 0) * w["dm"])

    # Ogohlantirishlar — tizim o'zi topadi
    alerts = []
    for c in open_rows:
        for wr in _content_warnings(db, c, today):
            alerts.append({
                "content_id": c.id, "title": c.title,
                "key": wr["key"], "severity": wr["severity"],
                "text": wr["text"],
                "planned_date": (c.planned_date.isoformat()
                                 if c.planned_date else None),
            })
    for c in all_rows:
        if c.status == "published" and not c.post_url:
            alerts.append({"content_id": c.id, "title": c.title,
                           "key": "no_link", "severity": "warn",
                           "text": "Joylandi, lekin havolasi kiritilmagan",
                           "planned_date": None})
    if month and plan_pct < roles.PLAN_TARGET_PERCENT:
        alerts.append({"content_id": None, "title": "Kontent rejasi",
                       "key": "plan", "severity": "warn",
                       "text": (f"Reja bajarilishi {plan_pct}% — "
                                f"{roles.PLAN_TARGET_PERCENT}% dan past"),
                       "planned_date": None})

    new_ideas = db.query(models.ContentIdea).filter(
        models.ContentIdea.status == "new").count()
    new_reqs = db.query(models.ContentRequest).filter(
        models.ContentRequest.status == "new").count()

    return {
        "cards": [
            {"key": "today", "label": "Bugungi kontentlar",
             "value": len(todays), "tone": "brand"},
            {"key": "late", "label": "Kechikkan kontentlar",
             "value": len(late), "tone": "bad" if late else "good"},
            {"key": "approval", "label": "Tasdiq kutilayotganlar",
             "value": len(waiting), "tone": "amber" if waiting else "plain"},
            {"key": "ideas", "label": "Yangi g'oyalar",
             "value": new_ideas, "tone": "plain"},
            {"key": "requests", "label": "Yangi so'rovlar",
             "value": new_reqs, "tone": "amber" if new_reqs else "plain"},
            {"key": "reach", "label": "Shu oydagi reach",
             "value": reach, "tone": "plain"},
            {"key": "engagement", "label": "Sifatli engagement",
             "value": eng, "tone": "plain",
             "hint": "like x1, izoh x2, saqlash x3, ulashish x4, DM x5"},
            {"key": "plan", "label": "Kontent reja bajarilishi",
             "value": f"{plan_pct}%",
             "tone": "good" if plan_pct >= roles.PLAN_TARGET_PERCENT
             else "bad"},
        ],
        "today": sorted(
            [_content_out(db, c, users=users) for c in todays],
            key=lambda r: (r["planned_time"] or "99:99")),
        "late": [_content_out(db, c, users=users) for c in late][:20],
        "waiting": [_content_out(db, c, users=users) for c in waiting],
        "alerts": sorted(alerts,
                         key=lambda a: 0 if a["severity"] == "block" else 1),
        "plan_percent": plan_pct,
        "month_planned": len(month),
        "month_done": len(done),
        "hint": ("SMM bo'limi post ishlab chiqaradigan bo'lim emas — "
                 "e'tibor, ishonch, murojaat va sotuv yaratadigan bo'lim."),
    }

def _content_funnel(db: Session, content_ids: list, *,
                    metrics: dict | None = None) -> dict:
    """Bir yoki bir nechta kontent bo'yicha butun voronka."""
    if metrics is None:
        metrics = {m.content_id: m for m in db.query(models.ContentMetric)
                   .filter(models.ContentMetric.content_id.in_(
                       content_ids or [-1])).all()}

    reach = sum((metrics[c].reach or 0) for c in content_ids if c in metrics)
    views = sum((metrics[c].views or 0) for c in content_ids if c in metrics)
    profile = sum((metrics[c].profile_visits or 0)
                  for c in content_ids if c in metrics)
    clicks = sum((metrics[c].link_clicks or 0)
                 for c in content_ids if c in metrics)
    w = roles.ENGAGEMENT_WEIGHT_MAP
    eng = 0
    for c in content_ids:
        m = metrics.get(c)
        if not m:
            continue
        eng += ((m.likes or 0) * w["like"] + (m.comments or 0) * w["comment"]
                + (m.saves or 0) * w["save"] + (m.shares or 0) * w["share"]
                + (m.dms or 0) * w["dm"])

    msgs = (db.query(models.SocialMessage)
            .filter(models.SocialMessage.content_id.in_(content_ids or [-1]))
            .all())
    leads = (db.query(models.Lead)
             .filter(models.Lead.content_id.in_(content_ids or [-1])).all())

    qualified = [l for l in leads
                 if l.stage in roles.QUALIFIED_STAGES or l.phone]
    trial = [l for l in leads if l.stage in ("trial_scheduled", "trial_done",
                                             "negotiation", "won")]
    won = [l for l in leads if l.converted_student_id]

    # Sotuv va tushum: leaddan chiqqan o'quvchining to'lovlari
    sids = [l.converted_student_id for l in won if l.converted_student_id]
    revenue = 0.0
    first_revenue = 0.0
    retained = {d: 0 for d in roles.RETENTION_DAYS}
    today = date.today()
    for sid in sids:
        pays = (db.query(models.Payment)
                .filter(models.Payment.student_id == sid,
                        models.Payment.kind == "payment")
                .order_by(models.Payment.created_at).all())
        revenue += sum(p.amount or 0 for p in pays)
        if pays:
            first_revenue += pays[0].amount or 0
        s = db.query(models.Student).get(sid)
        if not s or not s.enrolled_date:
            continue
        for d in roles.RETENTION_DAYS:
            end = s.left_date or today
            if (end - s.enrolled_date).days >= d:
                retained[d] += 1

    steps = [
        ("reach", reach), ("engagement", eng), ("profile", profile),
        ("click", clicks), ("dm", len(msgs)), ("lead", len(leads)),
        ("qualified", len(qualified)), ("trial", len(trial)),
        ("sale", len(won)), ("retained", retained.get(30, 0)),
    ]
    out_steps = []
    prev = None
    for key, val in steps:
        conv = (round(val / prev * 100, 1) if prev else None)
        out_steps.append({
            "key": key, "label": roles.ATTR_FUNNEL_LABELS[key],
            "value": val, "from_prev": conv,
        })
        prev = val if val else prev

    return {
        "reach": reach, "views": views, "engagement": eng,
        "profile_visits": profile, "link_clicks": clicks,
        "messages": len(msgs), "leads": len(leads),
        "qualified": len(qualified), "trials": len(trial),
        "sales": len(won),
        "revenue": round(revenue, 2),
        "first_revenue": round(first_revenue, 2),
        "retained_30": retained.get(30, 0),
        "retained_90": retained.get(90, 0),
        "funnel": out_steps,
        "lead_rate": (round(len(leads) / len(msgs) * 100, 1)
                      if msgs else 0.0),
        "qualified_rate": (round(len(qualified) / len(leads) * 100, 1)
                           if leads else 0.0),
        "sale_rate": (round(len(won) / len(qualified) * 100, 1)
                      if qualified else 0.0),
    }

@router.get("/api/content/{cid}/attribution")
def content_attribution(
    cid: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.CONTENT_REQUESTER)),
):
    """Bitta kontentning biznes natijasi."""
    c = db.query(models.Content).get(cid)
    if not c:
        raise HTTPException(404, "Kontent topilmadi")
    f = _content_funnel(db, [cid])
    m = (db.query(models.ContentMetric)
         .filter(models.ContentMetric.content_id == cid).first())

    story = (f"{f['reach']:,} ko'rishdan {f['messages']} murojaat, "
             f"{f['qualified']} sifatli lead, {f['sales']} sotuv va "
             f"{round(f['revenue']):,} so'm tushum keldi").replace(",", " ")

    return {
        "content": _content_out(db, c),
        "metrics": {
            "reach": m.reach if m else 0,
            "impressions": m.impressions if m else 0,
            "views": m.views if m else 0,
            "watch_time": m.watch_time if m else 0,
            "completion": m.completion if m else 0,
            "likes": m.likes if m else 0,
            "comments": m.comments if m else 0,
            "saves": m.saves if m else 0,
            "shares": m.shares if m else 0,
            "profile_visits": m.profile_visits if m else 0,
            "link_clicks": m.link_clicks if m else 0,
            "dms": m.dms if m else 0,
        },
        **f,
        "story": story,
        "goal": c.goal,
        "goal_label": roles.GOAL_LABELS.get(c.goal or "", "—"),
        "goal_metric": roles.GOAL_METRIC_LABELS.get(
            roles.GOAL_METRIC.get(c.goal or "", ""), "—"),
        "hint": ("Maqsad qanday bo'lsa, natija ham shunga qarab "
                 "baholanadi. Awareness kontentini sotuv bilan "
                 "o'lchash — noto'g'ri."),
    }

@router.get("/api/smm/attribution")
def smm_attribution(
    months: int = 3,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.CONTENT_REQUESTER)),
):
    """Qaysi kontent ishladi, qaysi biri yo'q — sotuv bo'yicha."""
    since = date.today() - timedelta(days=30 * max(1, months))
    rows = (db.query(models.Content)
            .filter(models.Content.status.in_(roles.CONTENT_LIVE))
            .filter((models.Content.planned_date >= since)
                    | (models.Content.planned_date.is_(None))).all())
    metrics = {m.content_id: m for m in db.query(models.ContentMetric).all()}

    out = []
    for c in rows:
        f = _content_funnel(db, [c.id], metrics=metrics)
        out.append({
            "id": c.id, "code": c.content_id, "title": c.title,
            "platform_label": roles.PLATFORM_LABELS.get(c.platform or "", "—"),
            "pillar": c.pillar,
            "pillar_label": roles.PILLAR_LABELS.get(c.pillar or "", "—"),
            "pillar_tone": roles.PILLAR_TONE.get(c.pillar or "", "slate"),
            "goal_label": roles.GOAL_LABELS.get(c.goal or "", "—"),
            "date": c.planned_date.isoformat() if c.planned_date else None,
            "reach": f["reach"], "engagement": f["engagement"],
            "messages": f["messages"], "leads": f["leads"],
            "qualified": f["qualified"], "sales": f["sales"],
            "revenue": f["revenue"], "retained_30": f["retained_30"],
        })

    total = _content_funnel(db, [c.id for c in rows], metrics=metrics)

    # Yo'nalish kesimida
    by_pillar: dict = {}
    for r in out:
        p = by_pillar.setdefault(r["pillar"] or "—", {
            "pillar": r["pillar"], "label": r["pillar_label"],
            "tone": r["pillar_tone"], "count": 0, "reach": 0,
            "leads": 0, "sales": 0, "revenue": 0.0,
        })
        p["count"] += 1
        p["reach"] += r["reach"]
        p["leads"] += r["leads"]
        p["sales"] += r["sales"]
        p["revenue"] += r["revenue"]

    out.sort(key=lambda r: (-r["revenue"], -r["sales"], -r["leads"]))
    return {
        "rows": out,
        "total": total,
        "by_pillar": sorted(by_pillar.values(),
                            key=lambda r: -r["revenue"]),
        "best": out[:5],
        "weak": [r for r in out if r["reach"] > 0 and r["leads"] == 0][:5],
        "months": months,
        "hint": ("Eng ko'p ko'rilgan kontent eng ko'p pul olib kelmasligi "
                 "mumkin. Shuning uchun ro'yxat tushum bo'yicha "
                 "saralangan."),
    }

@router.get("/api/campaigns")
def list_campaigns(
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.CONTENT_REQUESTER)),
):
    """Kampaniyalar va ularning voronkasi."""
    rows = (db.query(models.Campaign)
            .order_by(models.Campaign.start_date.desc()).limit(100).all())
    branches = {b.id: b.name for b in db.query(models.Branch).all()}
    out = []
    for c in rows:
        cids = [x.id for x in db.query(models.Content)
                .filter(models.Content.campaign_id == c.id).all()]
        f = _content_funnel(db, cids)
        out.append({
            "id": c.id, "name": c.name,
            "goal": c.goal,
            "goal_label": roles.GOAL_LABELS.get(c.goal or "", "—"),
            "course": c.course,
            "branch": branches.get(c.branch_id, "—"),
            "offer": c.offer,
            "start_date": c.start_date.isoformat() if c.start_date else None,
            "end_date": c.end_date.isoformat() if c.end_date else None,
            "contents": len(cids),
            "target_leads": c.target_leads,
            "target_sales": c.target_sales,
            "leads": f["leads"], "qualified": f["qualified"],
            "sales": f["sales"], "revenue": f["revenue"],
            "reach": f["reach"],
            "funnel": f["funnel"],
            "lead_plan_percent": (
                round(f["leads"] / c.target_leads * 100, 1)
                if c.target_leads else None),
            "is_active": bool(c.is_active),
            "conclusion": c.conclusion,
        })
    return {"rows": out}

def _brand_rows(db: Session, section: str | None = None) -> list[dict]:
    q = db.query(models.BrandRule).filter(models.BrandRule.is_active == 1)
    if section:
        q = q.filter(models.BrandRule.section == section)
    rows = q.order_by(models.BrandRule.section,
                      models.BrandRule.position).all()
    return [{
        "id": r.id, "section": r.section, "key": r.key, "title": r.title,
        "value": r.value, "note": r.note, "kind": r.kind,
        "source": r.source,
        "is_filled": (r.source or "") != "PDF",
        "position": r.position,
    } for r in rows]

@router.get("/api/brand")
def brand_book(section: str | None = None, db: Session = Depends(get_db),
               user: models.User = Depends(get_current_user)):
    """Brend kitob. Har bir xodim o'qiy oladi — brend hammaning ishi."""
    rows = _brand_rows(db, section)
    by = {}
    for r in rows:
        by.setdefault(r["section"], []).append(r)
    return {
        "sections": by,
        "source": roles.BRAND_SOURCE,
        "word": roles.BRAND_WORD,
        "primary": roles.BRAND_PRIMARY,
        "secondary": roles.BRAND_SECONDARY,
        "post_colors": roles.BRAND_POST_COLORS,
        "checks": [{"key": k, "label": l} for k, l in roles.BRAND_CHECKS],
        "required": roles.BRAND_CHECK_REQUIRED,
        "gaps": roles.BRAND_GAPS,
        "can_edit": user.role in roles.BRAND_EDIT,
        "hint": ("Brandbook 2023 asos qilib olindi. \"TO'LDIRILDI\" "
                 "belgisi turgan qatorlar PDF'da yo'q edi — ular "
                 "amaliyot uchun qo'shildi, tasdiqlashingiz kerak."),
    }

@router.post("/api/brand")
def brand_add(payload: schemas.BrandRuleIn, db: Session = Depends(get_db),
              user=Depends(require_role(*roles.BRAND_EDIT))):
    row = models.BrandRule(
        section=payload.section, key=payload.key or None,
        title=payload.title, value=payload.value, note=payload.note,
        kind=payload.kind, source="Qo'lda", position=payload.position or 0)
    db.add(row); db.commit(); db.refresh(row)
    audit.log(db, user, entity="brand_rule", action="create",
              entity_id=row.id, entity_label=payload.title)
    return _brand_rows(db, row.section)

@router.put("/api/brand/{rid}")
def brand_edit(rid: int, payload: schemas.BrandRulePatch,
               db: Session = Depends(get_db),
               user=Depends(require_role(*roles.BRAND_EDIT))):
    row = db.query(models.BrandRule).get(rid)
    if not row:
        raise HTTPException(404, "Topilmadi")
    for f, v in payload.model_dump(exclude_unset=True).items():
        setattr(row, f, v)
    # Tahrirlangan qator endi "tasdiqlangan" hisoblanadi
    if (row.source or "").startswith("TO'LDIRILDI"):
        row.source = "Tasdiqlangan"
    db.commit()
    audit.log(db, user, entity="brand_rule", action="update",
              entity_id=rid, entity_label=row.title)
    return _brand_rows(db, row.section)

def _brand_state(db: Session, cid: int) -> dict:
    """Kontentning brend tekshiruvi holati."""
    rows = db.query(models.BrandCheck).filter(
        models.BrandCheck.content_id == cid).all()
    done = {r.key: r for r in rows}
    items = []
    for k, label in roles.BRAND_CHECKS:
        r = done.get(k)
        items.append({
            "key": k, "label": label,
            "ok": bool(r and r.ok),
            "note": r.note if r else None,
            "required": k in roles.BRAND_CHECK_REQUIRED,
            "checked_at": r.checked_at.isoformat() if r and r.checked_at
                          else None,
        })
    missing = [i["label"] for i in items
               if i["required"] and not i["ok"]]
    return {
        "items": items,
        "done": sum(1 for i in items if i["ok"]),
        "total": len(items),
        "blocked": missing,
        "can_publish": not missing,
    }

@router.get("/api/content/{cid}/brand")
def content_brand(cid: int, db: Session = Depends(get_db),
                  user=Depends(require_role(*roles.SMM_ACCESS))):
    if not db.query(models.Content).get(cid):
        raise HTTPException(404, "Topilmadi")
    return _brand_state(db, cid)

@router.post("/api/content/{cid}/brand")
def content_brand_set(cid: int, payload: schemas.BrandCheckIn,
                      db: Session = Depends(get_db),
                      user=Depends(require_role(*roles.SMM_ACCESS))):
    if not db.query(models.Content).get(cid):
        raise HTTPException(404, "Topilmadi")
    if payload.key not in roles.BRAND_CHECK_LABELS:
        raise HTTPException(400, "Noma'lum tekshiruv")
    row = db.query(models.BrandCheck).filter(
        models.BrandCheck.content_id == cid,
        models.BrandCheck.key == payload.key).first()
    if not row:
        row = models.BrandCheck(content_id=cid, key=payload.key)
        db.add(row)
    row.ok = 1 if payload.ok else 0
    row.note = payload.note
    row.checked_by = user.id
    row.checked_at = datetime.utcnow()
    db.commit()
    return _brand_state(db, cid)

def _media_out(db: Session, m: models.MediaAsset,
               today: date | None = None) -> dict:
    today = today or date.today()
    left = None
    if m.consent_until:
        left = (m.consent_until - today).days
    expired = left is not None and left < 0
    consent = "forbidden" if expired else (m.consent or "pending")
    st = db.query(models.Student).get(m.student_id) if m.student_id else None
    br = db.query(models.Branch).get(m.branch_id) if m.branch_id else None
    return {
        "id": m.id, "name": m.name,
        "kind": m.kind or "photo",
        "kind_label": roles.MEDIA_KIND_LABELS.get(m.kind or "photo", "—"),
        "kind_tone": roles.MEDIA_KIND_TONE.get(m.kind or "photo", "slate"),
        "url": m.url, "attachment_id": m.attachment_id,
        "branch": br.name if br else None, "branch_id": m.branch_id,
        "course": m.course,
        "student": st.full_name if st else None,
        "student_id": m.student_id,
        "teacher_id": m.teacher_id,
        "event": m.event,
        "taken_on": m.taken_on.isoformat() if m.taken_on else None,
        "author": m.author, "tags": m.tags,
        "consent": consent,
        "consent_label": roles.CONSENT_LABELS.get(consent, "—"),
        "consent_tone": roles.CONSENT_TONE.get(consent, "slate"),
        "consent_until": m.consent_until.isoformat()
                         if m.consent_until else None,
        "days_left": left,
        "expired": expired,
        "expiring": (left is not None and 0 <= left
                     <= roles.CONSENT_EXPIRY_WARN_DAYS),
        "can_publish": consent not in roles.CONSENT_BLOCKS_PUBLISH,
        "can_download": bool(m.can_download),
    }

@router.get("/api/media")
def media_list(kind: str | None = None, consent: str | None = None,
               q: str | None = None, branch_id: int | None = None,
               publishable: int = 0, db: Session = Depends(get_db),
               user=Depends(require_role(*roles.SMM_ACCESS))):
    query = db.query(models.MediaAsset)
    if user.role == roles.BRANCH_MANAGER and user.branch_id:
        query = query.filter(models.MediaAsset.branch_id == user.branch_id)
    elif branch_id:
        query = query.filter(models.MediaAsset.branch_id == branch_id)
    if kind:
        query = query.filter(models.MediaAsset.kind == kind)
    if consent:
        query = query.filter(models.MediaAsset.consent == consent)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(models.MediaAsset.name.ilike(like),
                                 models.MediaAsset.tags.ilike(like),
                                 models.MediaAsset.event.ilike(like)))
    rows = [_media_out(db, m) for m in
            query.order_by(models.MediaAsset.id.desc()).limit(400).all()]
    if publishable:
        rows = [r for r in rows if r["can_publish"]]
    counts = {}
    for r in rows:
        counts[r["consent"]] = counts.get(r["consent"], 0) + 1
    return {
        "rows": rows,
        "kinds": [{"key": k, "label": l, "tone": t}
                  for k, l, t in roles.MEDIA_KINDS],
        "consents": [{"key": k, "label": l, "tone": t,
                      "count": counts.get(k, 0),
                      "blocks": k in roles.CONSENT_BLOCKS_PUBLISH}
                     for k, l, t in roles.CONSENT_STATUSES],
        "total": len(rows),
        "publishable": sum(1 for r in rows if r["can_publish"]),
        "expiring": sum(1 for r in rows if r["expiring"]),
        "expired": sum(1 for r in rows if r["expired"]),
        "hint": ("Rozilik muddati tugagan material avtomat "
                 "\"taqiqlangan\"ga o'tadi — eski rozilik bilan yangi "
                 "post chiqmaydi."),
    }

@router.post("/api/media")
def media_add(payload: schemas.MediaIn, db: Session = Depends(get_db),
              user=Depends(require_role(*roles.SMM_ACCESS))):
    if not (payload.name or "").strip():
        raise HTTPException(400, "Nom kerak")
    if payload.consent and payload.consent not in roles.CONSENT_LABELS:
        raise HTTPException(400, "Noma'lum rozilik holati")
    m = models.MediaAsset(**payload.model_dump())
    if not m.author:
        m.author = user.full_name
    db.add(m); db.commit(); db.refresh(m)
    audit.log(db, user, entity="media", action="create",
              entity_id=m.id, entity_label=m.name)
    return _media_out(db, m)

@router.put("/api/media/{mid}")
def media_edit(mid: int, payload: schemas.MediaPatch,
               db: Session = Depends(get_db),
               user=Depends(require_role(*roles.SMM_ACCESS))):
    m = db.query(models.MediaAsset).get(mid)
    if not m:
        raise HTTPException(404, "Topilmadi")
    data = payload.model_dump(exclude_unset=True)
    if data.get("consent") and data["consent"] not in roles.CONSENT_LABELS:
        raise HTTPException(400, "Noma'lum rozilik holati")
    old = m.consent
    for f, v in data.items():
        setattr(m, f, v)
    db.commit()
    if data.get("consent") and data["consent"] != old:
        audit.log(db, user, entity="media", action="consent",
                  entity_id=mid, entity_label=m.name,
                  field="consent", old_value=old, new_value=m.consent)
    return _media_out(db, m)

@router.delete("/api/media/{mid}")
def media_delete(mid: int, db: Session = Depends(get_db),
                 user=Depends(require_role(*roles.FULL_ACCESS + [roles.SMM_MANAGER]))):
    m = db.query(models.MediaAsset).get(mid)
    if not m:
        raise HTTPException(404, "Topilmadi")
    audit.log(db, user, entity="media", action="delete",
              entity_id=mid, entity_label=m.name)
    db.delete(m); db.commit()
    return {"ok": True}

def _kb_out(db: Session, a: models.KbArticle) -> dict:
    au = db.query(models.User).get(a.author_id) if a.author_id else None
    stale = False
    ref = a.reviewed_at or (a.updated_at.date() if a.updated_at else None)
    if ref:
        stale = (date.today() - ref).days > roles.KB_REVIEW_MONTHS * 30
    return {
        "id": a.id, "title": a.title,
        "category": a.category,
        "category_label": roles.KB_CATEGORY_LABELS.get(a.category, "—"),
        "category_tone": roles.KB_CATEGORY_TONE.get(a.category, "slate"),
        "body": a.body, "tags": a.tags,
        "author": au.full_name if au else None,
        "views": a.views or 0,
        "is_pinned": bool(a.is_pinned),
        "stale": stale,
        "reviewed_at": ref.isoformat() if ref else None,
        "updated_at": a.updated_at.isoformat() if a.updated_at else None,
    }

@router.get("/api/kb")
def kb_list(category: str | None = None, q: str | None = None,
            db: Session = Depends(get_db),
            user: models.User = Depends(get_current_user)):
    """Bilimlar bazasi — har qanday xodim o'qiy oladi."""
    query = db.query(models.KbArticle).filter(
        models.KbArticle.is_active == 1)
    if category:
        query = query.filter(models.KbArticle.category == category)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(models.KbArticle.title.ilike(like),
                                 models.KbArticle.body.ilike(like),
                                 models.KbArticle.tags.ilike(like)))
    rows = query.order_by(models.KbArticle.is_pinned.desc(),
                          models.KbArticle.id.desc()).all()
    out = [_kb_out(db, a) for a in rows]
    counts = {}
    for a in db.query(models.KbArticle).filter(
            models.KbArticle.is_active == 1).all():
        counts[a.category] = counts.get(a.category, 0) + 1
    return {
        "rows": out,
        "categories": [{"key": k, "label": l, "tone": t,
                        "count": counts.get(k, 0)}
                       for k, l, t in roles.KB_CATEGORIES],
        "stale": sum(1 for r in out if r["stale"]),
        "can_edit": user.role in roles.SMM_ACCESS,
        "review_months": roles.KB_REVIEW_MONTHS,
    }

@router.post("/api/kb")
def kb_add(payload: schemas.KbIn, db: Session = Depends(get_db),
           user=Depends(require_role(*roles.SMM_ACCESS))):
    if not (payload.title or "").strip():
        raise HTTPException(400, "Sarlavha kerak")
    a = models.KbArticle(**payload.model_dump(), author_id=user.id,
                         reviewed_at=date.today())
    db.add(a); db.commit(); db.refresh(a)
    audit.log(db, user, entity="kb_article", action="create",
              entity_id=a.id, entity_label=a.title)
    return _kb_out(db, a)

@router.put("/api/kb/{aid}")
def kb_edit(aid: int, payload: schemas.KbPatch,
            db: Session = Depends(get_db),
            user=Depends(require_role(*roles.SMM_ACCESS))):
    a = db.query(models.KbArticle).get(aid)
    if not a:
        raise HTTPException(404, "Topilmadi")
    for f, v in payload.model_dump(exclude_unset=True).items():
        setattr(a, f, v)
    a.reviewed_at = date.today()
    db.commit()
    audit.log(db, user, entity="kb_article", action="update",
              entity_id=aid, entity_label=a.title)
    return _kb_out(db, a)

@router.post("/api/kb/{aid}/view")
def kb_view(aid: int, db: Session = Depends(get_db),
            user: models.User = Depends(get_current_user)):
    a = db.query(models.KbArticle).get(aid)
    if not a:
        raise HTTPException(404, "Topilmadi")
    a.views = (a.views or 0) + 1
    db.commit()
    return _kb_out(db, a)

def _dim_value(db: Session, c: models.Content, dim: str) -> tuple:
    """Kontentdan kesim qiymatini oladi: (kalit, yorliq)."""
    if dim == "platform":
        return c.platform, roles.PLATFORM_LABELS.get(c.platform, c.platform
                                                     or "—")
    if dim == "format":
        f = c.fmt or roles.format_of(c.platform)
        return f, roles.CONTENT_FORMAT_LABELS.get(f, f or "—")
    if dim == "pillar":
        return c.pillar, roles.PILLAR_LABELS.get(c.pillar, c.pillar or "—")
    if dim == "goal":
        return c.goal, roles.GOAL_LABELS.get(c.goal, c.goal or "—")
    if dim == "course":
        return c.course, c.course or "Ko'rsatilmagan"
    if dim == "branch":
        b = db.query(models.Branch).get(c.branch_id) if c.branch_id else None
        return c.branch_id, b.name if b else "Umumiy"
    if dim == "author":
        u = db.query(models.User).get(c.owner_id) if c.owner_id else None
        return c.owner_id, u.full_name if u else "Biriktirilmagan"
    if dim == "weekday":
        d = c.published_at.date() if c.published_at else c.planned_date
        if not d:
            return None, "—"
        return d.weekday(), roles.UZ_WEEKDAYS[d.weekday()]
    return None, "—"

@router.get("/api/smm/analytics")
def smm_analytics(dim: str = "platform", months: int = 3,
                  branch_id: int | None = None,
                  db: Session = Depends(get_db),
                  user=Depends(require_role(*roles.SMM_ACCESS))):
    if dim not in dict(roles.ANALYTICS_DIMENSIONS):
        raise HTTPException(400, "Noma'lum kesim")
    today = date.today()
    since = today - timedelta(days=months * 30)

    # "Joylangan" — status emas, published_at bo'yicha. Status keyin
    # "natija o'lchanmoqda"ga o'tadi, lekin post joylangancha qoladi.
    q = db.query(models.Content).filter(
        models.Content.published_at.isnot(None),
        models.Content.published_at >= datetime.combine(
            since, datetime.min.time()))
    if user.role == roles.BRANCH_MANAGER and user.branch_id:
        q = q.filter(models.Content.branch_id == user.branch_id)
    elif branch_id:
        q = q.filter(models.Content.branch_id == branch_id)
    contents = q.all()

    groups: dict = {}
    for c in contents:
        key, label = _dim_value(db, c, dim)
        g = groups.setdefault(str(key), {
            "key": key, "label": label, "ids": [], "count": 0,
        })
        g["ids"].append(c.id)
        g["count"] += 1

    rows = []
    for g in groups.values():
        f = _content_funnel(db, g["ids"])
        row = {"key": g["key"], "label": g["label"], "count": g["count"]}
        for k in ("reach", "engagement", "messages", "leads",
                  "qualified", "sales"):
            row[k] = f.get(k, 0)
        row["revenue"] = f.get("revenue", 0.0)
        rows.append(row)
    for r in rows:
        r["per_content_leads"] = round(r["leads"] / r["count"], 1) \
            if r["count"] else 0
        r["per_content_revenue"] = round(r["revenue"] / r["count"]) \
            if r["count"] else 0
        r["lead_rate"] = round(r["leads"] / r["messages"] * 100, 1) \
            if r["messages"] else 0.0
        r["cost_free_score"] = round(r["revenue"] / r["reach"] * 1000, 1) \
            if r["reach"] else 0.0
    rows.sort(key=lambda r: -r["revenue"])

    best = rows[0] if rows else None
    # Ko'p qamrov, kam natija — eng foydali xulosa shu
    trap = None
    if len(rows) > 1:
        by_reach = sorted(rows, key=lambda r: -r["reach"])
        if by_reach[0]["key"] != rows[0]["key"] and by_reach[0]["reach"]:
            trap = {
                "label": by_reach[0]["label"],
                "reach": by_reach[0]["reach"],
                "revenue": by_reach[0]["revenue"],
                "better": rows[0]["label"],
            }

    return {
        "dim": dim,
        "dim_label": dict(roles.ANALYTICS_DIMENSIONS)[dim],
        "dims": [{"key": k, "label": l}
                 for k, l in roles.ANALYTICS_DIMENSIONS],
        "rows": rows,
        "months": months,
        "total_contents": len(contents),
        "best": best,
        "trap": trap,
        "hint": ("Saralash tushum bo'yicha. Qamrov bo'yicha birinchi "
                 "bo'lgan kesim pul bo'yicha birinchi bo'lmasligi "
                 "mumkin — shuni ko'rish uchun shu jadval kerak."),
    }

def _smm_kpi(db: Session, start: date, end: date,
             branch_id: int | None = None) -> dict:
    q = db.query(models.Content)
    if branch_id:
        q = q.filter(models.Content.branch_id == branch_id)

    planned = q.filter(models.Content.planned_date >= start,
                       models.Content.planned_date <= end).all()
    published = q.filter(
        models.Content.published_at.isnot(None),
        models.Content.published_at >= datetime.combine(
            start, datetime.min.time()),
        models.Content.published_at <= datetime.combine(
            end, datetime.max.time())).all()

    # 1. Reja va intizom
    plan_pct = 0.0
    on_time = 0
    if planned:
        done = [c for c in planned if c.published_at]
        plan_pct = round(len(done) / len(planned) * 100, 1)
        for c in done:
            if c.published_at and c.planned_date and \
                    c.published_at.date() <= c.planned_date:
                on_time += 1
    plan_score = min(plan_pct / roles.PLAN_TARGET_PERCENT, 1.0) * 20

    # Voronka
    pub_ids = [c.id for c in published]
    f_all = _content_funnel(db, pub_ids)
    tot = {k: f_all.get(k, 0) for k in
           ("reach", "engagement", "messages", "leads",
            "qualified", "sales", "revenue")}

    # 2. Sifatli leadlar — oyiga 30 ta mo'ljal
    lead_target = 30 * max((end - start).days / 30, 0.5)
    lead_score = min(tot["qualified"] / lead_target, 1.0) * 25 \
        if lead_target else 0

    # 3. Engagement sifati — qamrovning 3% i mo'ljal
    eng_rate = (tot["engagement"] / tot["reach"] * 100) if tot["reach"] else 0
    eng_score = min(eng_rate / 3.0, 1.0) * 15

    # 4. Sotuv
    sale_rate = (tot["sales"] / tot["leads"] * 100) if tot["leads"] else 0
    sale_score = min(sale_rate / 30.0, 1.0) * 15

    # 5. Inbox — SLA
    msgs = db.query(models.SocialMessage).filter(
        models.SocialMessage.received_at >= datetime.combine(
            start, datetime.min.time()),
        models.SocialMessage.received_at <= datetime.combine(
            end, datetime.max.time())).all()
    answered = [m for m in msgs if m.first_reply_at and not m.off_hours]
    good = 0
    for m in answered:
        mins = (m.first_reply_at - m.received_at).total_seconds() / 60
        if mins <= roles.SLA_ALERT_MINUTES:
            good += 1
    sla_pct = round(good / len(answered) * 100, 1) if answered else 0.0
    inbox_score = (sla_pct / 100) * 10

    # 6. Brend standarti
    ids = [c.id for c in published]
    checks = db.query(models.BrandCheck).filter(
        models.BrandCheck.content_id.in_(ids)).all() if ids else []
    need = len(ids) * len(roles.BRAND_CHECK_REQUIRED)
    have = sum(1 for c in checks
               if c.ok and c.key in roles.BRAND_CHECK_REQUIRED)
    # Kontent joylanmagan bo'lsa 100% berilmaydi — bo'sh oy uchun
    # to'liq ball berish ishlamaganni mukofotlash bo'lardi.
    brand_pct = round(have / need * 100, 1) if need else 0.0
    brand_score = (brand_pct / 100) * 10

    # 7. Yangi formatlar — nechta xil format sinaldi
    fmts = {c.fmt or roles.format_of(c.platform) for c in published}
    exp_score = min(len(fmts) / 4.0, 1.0) * 5

    parts = [
        ("plan", plan_score, 20, f"Reja {plan_pct}% bajarildi"),
        ("leads", lead_score, 25,
         f"{tot['qualified']} sifatli lead (mo'ljal {int(lead_target)})"),
        ("engagement", eng_score, 15,
         f"Engagement {round(eng_rate, 2)}% (mo'ljal 3%)"),
        ("sales", sale_score, 15,
         f"Leaddan sotuvga {round(sale_rate, 1)}% (mo'ljal 30%)"),
        ("inbox", inbox_score, 10, f"SLA {sla_pct}%"),
        ("brand", brand_score, 10,
         f"Brend tekshiruvi {brand_pct}%" if need
         else "Tekshiriladigan kontent yo'q"),
        ("experiment", exp_score, 5, f"{len(fmts)} xil format sinaldi"),
    ]
    total = round(sum(p[1] for p in parts), 1)
    label, tone = roles.kpi_band(total)
    return {
        "score": total, "label": label, "tone": tone,
        "parts": [{
            "key": k, "label": roles.SMM_KPI_LABELS.get(k, k),
            "score": round(s, 1), "max": mx,
            "percent": round(s / mx * 100) if mx else 0,
            "note": note,
        } for k, s, mx, note in parts],
        "plan_percent": plan_pct,
        "on_time": on_time,
        "published": len(published),
        "planned": len(planned),
        "sla_percent": sla_pct,
        "funnel_totals": tot,
    }

@router.get("/api/smm/kpi")
def smm_kpi(months: int = 1, branch_id: int | None = None,
            db: Session = Depends(get_db),
            user=Depends(require_role(*roles.SMM_ACCESS))):
    end = date.today()
    start = end - timedelta(days=months * 30)
    if user.role == roles.BRANCH_MANAGER and user.branch_id:
        branch_id = user.branch_id
    d = _smm_kpi(db, start, end, branch_id)
    d["start"] = start.isoformat()
    d["end"] = end.isoformat()
    d["weights"] = [{"key": k, "label": l, "weight": w}
                    for k, l, w in roles.SMM_KPI_WEIGHTS]
    d["hint"] = ("Har bir mezon o'zi hisoblanadi — hech kim qo'lda "
                 "baho qo'ymaydi. Raqamlar kontent, murojaat va "
                 "sotuvdan kelib chiqadi.")
    return d

def _period_range(period: str, today: date | None = None):
    today = today or date.today()
    if period == "week":
        start = today - timedelta(days=today.weekday() + 7)
        return start, start + timedelta(days=6)
    if period == "quarter":
        qm = ((today.month - 1) // 3) * 3 + 1
        start = date(today.year, qm, 1) - timedelta(days=1)
        qs = ((start.month - 1) // 3) * 3 + 1
        s = date(start.year, qs, 1)
        e = date(s.year + (1 if qs + 3 > 12 else 0),
                 (qs + 3 - 1) % 12 + 1, 1) - timedelta(days=1)
        return s, e
    first = today.replace(day=1)
    end = first - timedelta(days=1)
    return end.replace(day=1), end

def _build_report(db: Session, start: date, end: date,
                  branch_id: int | None = None) -> dict:
    q = db.query(models.Content).filter(
        models.Content.published_at.isnot(None),
        models.Content.published_at >= datetime.combine(
            start, datetime.min.time()),
        models.Content.published_at <= datetime.combine(
            end, datetime.max.time()))
    if branch_id:
        q = q.filter(models.Content.branch_id == branch_id)
    published = q.all()

    all_ids = [c.id for c in published]
    f_all = _content_funnel(db, all_ids)
    tot = {k: f_all.get(k, 0) for k in
           ("reach", "engagement", "messages", "leads",
            "qualified", "sales", "revenue")}
    rows = []
    for c in published:
        f = _content_funnel(db, [c.id])
        rows.append({
            "id": c.id, "code": c.content_id, "title": c.title,
            "platform_label": roles.PLATFORM_LABELS.get(c.platform,
                                                        c.platform or "—"),
            "pillar_label": roles.PILLAR_LABELS.get(c.pillar, "—"),
            "date": c.published_at.date().isoformat()
                    if c.published_at else None,
            "reach": f.get("reach", 0), "leads": f.get("leads", 0),
            "sales": f.get("sales", 0), "revenue": f.get("revenue", 0.0),
        })
    rows.sort(key=lambda r: -r["revenue"])

    kpi = _smm_kpi(db, start, end, branch_id)

    # Kesimlar
    dims = {}
    for dim in ("platform", "format", "pillar"):
        g = {}
        for c in published:
            key, label = _dim_value(db, c, dim)
            e = g.setdefault(str(key), {"label": label, "ids": [],
                                        "count": 0})
            e["ids"].append(c.id)
            e["count"] += 1
        out = []
        for e in g.values():
            f = _content_funnel(db, e["ids"])
            out.append({"label": e["label"], "count": e["count"],
                        "leads": f.get("leads", 0),
                        "revenue": f.get("revenue", 0.0)})
        dims[dim] = sorted(out, key=lambda r: -r["revenue"])

    # Murojaatlar
    msgs = db.query(models.SocialMessage).filter(
        models.SocialMessage.received_at >= datetime.combine(
            start, datetime.min.time()),
        models.SocialMessage.received_at <= datetime.combine(
            end, datetime.max.time())).all()
    made_lead = sum(1 for m in msgs if m.lead_id)

    funnel = f_all.get("funnel", [])

    # Xulosa matni — odam o'qiydigan tilda
    days = (end - start).days + 1
    lines = []
    lines.append(
        f"{roles.uz_date(start)}–{roles.uz_date_full(end)} "
        f"({days} kun): {len(published)} ta kontent joylandi, "
        f"reja {kpi['plan_percent']}% bajarildi.")
    if tot["reach"]:
        lines.append(
            f"Qamrov {tot['reach']:,}".replace(",", " ") +
            f", {tot['messages']} murojaat, {tot['leads']} lead, "
            f"{tot['sales']} sotuv.")
    if tot["revenue"]:
        lines.append(
            f"Kontentdan kelgan tushum: "
            f"{int(tot['revenue']):,}".replace(",", " ") + " so'm.")
    if rows and rows[0]["revenue"]:
        lines.append(
            f"Eng ko'p pul olib kelgani — \"{rows[0]['title']}\" "
            f"({int(rows[0]['revenue']):,}".replace(",", " ") + " so'm).")
    if msgs:
        lines.append(
            f"{len(msgs)} murojaatdan {made_lead} tasi leadga aylandi, "
            f"SLA {kpi['sla_percent']}%.")
    lines.append(f"SMM KPI: {kpi['score']} ball — {kpi['label']}.")

    weak = [r for r in rows if r["reach"] > 0 and r["leads"] == 0]

    # Tavsiyalar — eng past ball olgan mezondan kelib chiqadi
    tips = []
    worst = sorted(kpi["parts"], key=lambda p: p["percent"])[:2]
    for p in worst:
        if p["percent"] >= 90:
            continue
        tips.append({"about": p["label"], "text": {
            "plan": "Reja bajarilmayapti. Kamroq, lekin bajariladigan "
                    "reja tuzing — bajarilmagan reja rejani o'ldiradi.",
            "leads": "Sifatli lead kam. Har postda aniq bitta harakat "
                     "so'ralganini tekshiring.",
            "engagement": "Engagement past. Birinchi 3 soniya va "
                          "birinchi jumlani kuchaytiring.",
            "sales": "Lead ko'p, sotuv kam. Muammo kontentda emas, "
                     "leadlar bilan ishlashda bo'lishi mumkin.",
            "inbox": "Murojaatlarga kech javob berilyapti. Kuniga 3 "
                     "marta belgilangan vaqt ajrating.",
            "brand": "Kontentlar brend bo'yicha tekshirilmagan. "
                     "Nashrdan oldin ro'yxatni to'ldiring.",
            "experiment": "Bir xil format takrorlanyapti. Oyiga "
                          "kamida bitta yangi format sinang.",
        }.get(p["key"], "")})

    return {
        "start": start.isoformat(), "end": end.isoformat(),
        "days": days,
        "published": len(published),
        "planned": kpi["planned"],
        "plan_percent": kpi["plan_percent"],
        "on_time": kpi["on_time"],
        "totals": tot,
        "funnel": funnel,
        "top": rows[:5],
        "weak": weak[:5],
        "dims": dims,
        "messages": len(msgs),
        "messages_to_lead": made_lead,
        "sla_percent": kpi["sla_percent"],
        "kpi": kpi,
        "summary": "\n".join(lines),
        "tips": tips,
        "sections": [{"key": k, "label": l}
                     for k, l in roles.REPORT_SECTIONS],
    }

@router.get("/api/smm/report")
def smm_report(period: str = "month", start: date | None = None,
               end: date | None = None, branch_id: int | None = None,
               db: Session = Depends(get_db),
               user=Depends(require_role(*roles.SMM_ACCESS))):
    """Hisobotni ko'rib chiqish (hali saqlanmaydi)."""
    if period not in dict(roles.REPORT_PERIODS):
        raise HTTPException(400, "Noma'lum davr")
    if not (start and end):
        start, end = _period_range(period)
    if user.role == roles.BRANCH_MANAGER and user.branch_id:
        branch_id = user.branch_id
    d = _build_report(db, start, end, branch_id)
    d["period"] = period
    d["periods"] = [{"key": k, "label": l} for k, l in roles.REPORT_PERIODS]
    d["saved"] = [{
        "id": r.id, "period": r.period,
        "start": r.start_date.isoformat(), "end": r.end_date.isoformat(),
        "score": r.kpi_score,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    } for r in db.query(models.SmmReport).order_by(
        models.SmmReport.id.desc()).limit(12).all()]
    return d

@router.post("/api/smm/report")
def smm_report_save(payload: schemas.ReportIn, db: Session = Depends(get_db),
                    user=Depends(require_role(*roles.SMM_ACCESS))):
    """Hisobotni saqlaydi — raqamlar muzlatiladi."""
    period = payload.period or "month"
    start, end = (payload.start_date, payload.end_date)
    if not (start and end):
        start, end = _period_range(period)
    branch_id = payload.branch_id
    if user.role == roles.BRANCH_MANAGER and user.branch_id:
        branch_id = user.branch_id
    d = _build_report(db, start, end, branch_id)
    r = models.SmmReport(
        period=period, start_date=start, end_date=end, branch_id=branch_id,
        data=json.dumps(d, ensure_ascii=False, default=str),
        summary=payload.summary or d["summary"],
        kpi_score=d["kpi"]["score"], created_by=user.id)
    db.add(r); db.commit(); db.refresh(r)
    audit.log(db, user, entity="smm_report", action="create",
              entity_id=r.id,
              entity_label=f"{start}–{end} · {d['kpi']['score']} ball")
    return {"id": r.id, "ok": True, **d}

@router.get("/api/smm/report/{rid}")
def smm_report_get(rid: int, db: Session = Depends(get_db),
                   user=Depends(require_role(*roles.SMM_ACCESS))):
    r = db.query(models.SmmReport).get(rid)
    if not r:
        raise HTTPException(404, "Topilmadi")
    d = json.loads(r.data) if r.data else {}
    d["id"] = r.id
    d["period"] = r.period
    d["summary"] = r.summary or d.get("summary")
    d["frozen"] = True
    return d



# =====================================================================
#  KONTENT-PLAN (2026-08-27)
#
#  Jahongir "idealniy kontent plan" deb Excel yubordi va aytdi:
#  "sen ham SMMdagi kontent planni shunaqa qism bo'limilarni bo'lishi
#  kerak va ichiga ssearniysi scriptini yozadigan ham bo'lishi kerak
#  SMM manager kirib shuni kopya qilishga oson bo'lsin, ozgartirishga
#  oson bo'lsin va shu video joylangangandan keyin linkini joylashi
#  kerak link orqali avtomat nechta korildi nechta koment like repost
#  bolgani avtomat hisoboti unga korinsin kuchli tahlil qilsa
#  ob'ladi."
#
#  Uch narsa:
#    /api/smm/plan           — Excel ustunlari tartibida oylik jadval
#    /api/content/{id}/copy  — bir bosishda nusxa (tez to'ldirish)
#    /api/content/{id}/fetch — LINKDAN avtomat natija
#    /api/smm/content-analytics — nima ishlayapti, nima yo'q
# =====================================================================
import content_fetch as _cf


def _plan_row(db: Session, c: models.Content, m=None,
              users: dict | None = None) -> dict:
    """Bitta qator — Jahongir jadvalidagi ustunlar tartibida."""
    if users is None:
        users = {}
        if c.owner_id:
            u = db.query(models.User).get(c.owner_id)
            if u:
                users[c.owner_id] = u.full_name
    d = c.planned_date
    kun = roles.UZ_WEEKDAYS[d.weekday()][:2] if d else None
    er = 0.0
    if m:
        w = roles.ENGAGEMENT_WEIGHT_MAP
        score = ((m.likes or 0) * w["like"] + (m.comments or 0) * w["comment"]
                 + (m.saves or 0) * w["save"] + (m.shares or 0) * w["share"]
                 + (m.dms or 0) * w["dm"])
        base = m.reach or m.views or 0
        er = round(score / base * 100, 2) if base else 0.0
    return {
        "id": c.id, "content_id": c.content_id,
        "date": d.isoformat() if d else None,
        "weekday": kun,
        "time": c.planned_time,
        "platform": c.platform,
        "audience": c.audience,
        "pillar": c.pillar,
        "pillar_label": roles.PILLAR_LABELS.get(c.pillar, c.pillar),
        "funnel": c.funnel,
        "funnel_label": roles.FUNNEL_LABELS.get(c.funnel, c.funnel),
        "goal": c.goal,
        "goal_label": roles.GOAL_LABELS.get(c.goal, c.goal),
        "title": c.title,
        "hook": c.hook,
        "message": c.message,
        "proof": c.proof,
        "fmt": c.fmt,
        "fmt_label": roles.FORMAT_LABELS.get(c.fmt, c.fmt),
        "cta": c.cta,
        "owner": users.get(c.owner_id),
        "owner_id": c.owner_id,
        "shoot_date": c.shoot_date.isoformat() if c.shoot_date else None,
        "status": c.status,
        "status_label": roles.CONTENT_STATUS_LABELS.get(c.status, c.status),
        "status_tone": roles.CONTENT_STATUS_TONE.get(c.status, "slate"),
        # Holat doskasi uchun (2026-09-26): shoshilinch belgisi va
        # ogohlantirishlar (kechikdi, rozilik yo'q...) — so'rovsiz
        "priority": c.priority,
        "warnings": _content_warnings(db, c),
        "kpi_target": c.kpi_target,
        "conclusion": c.conclusion,
        "series": c.series,
        "script": c.script,
        "caption": c.caption,
        "hashtags": c.hashtags,
        "post_url": c.post_url,
        "published_at": (c.published_at.isoformat()
                         if c.published_at else None),
        "metrics": ({
            "views": m.views or 0, "reach": m.reach or 0,
            "likes": m.likes or 0, "comments": m.comments or 0,
            "shares": m.shares or 0, "saves": m.saves or 0,
            "er": er,
            "source": m.source or "manual",
            "fetched_at": m.fetched_at.isoformat() if m.fetched_at else None,
            "note": m.fetch_note,
        } if m else None),
    }


@router.get("/api/smm/plan")
def smm_plan(year: int | None = None, month: int | None = None,
             branch_id: int | None = None, scope: str = "all",
             db: Session = Depends(get_db),
             user=Depends(require_role(*roles.SMM_ACCESS))):
    """Kontent-plan — Excel jadvalining aynan o'zi.

    2026-08-28, Jahongir: "qara men excel fayl qilib yukladim
    sentabrnikini lekin menda ko'rinmayabdi. shu OY TANLASH EMAS,
    eng oldingilari bo'yicha SANA bo'yicha eng yaqinlari bo'yicha
    KETMA-KETLIKDA tursin".

    Shuning uchun endi standart holat — OY FILTRI YO'Q: butun reja
    bitta ro'yxatda, sana bo'yicha. Bugundan boshlanadi (eng
    yaqinlari tepada), o'tgan kunlar pastda teskari tartibda.
    Sabab: SMM menejerga "ertaga nima chiqadi" kerak, "sentabrda
    nima bor edi" emas.

    Oy tanlash kerak bo'lsa scope="month" bilan eski xatti-harakat
    saqlanib qoldi (hisobot va eksport uchun) — hech narsa
    yo'qolmadi."""
    today = roles.local_today()
    y, m = year or today.year, month or today.month
    # keep_unset: filialsiz post UMUMIY kontent — har filialda
    # ko'rinadi. Aks holda Excel'dan yuklangan reja "yo'q" bo'lib
    # qolardi (2026-08-28).
    q = scope_to_branch(db.query(models.Content), models.Content,
                        user, branch_id, keep_unset=True)
    if scope == "month":
        start, end = billing.month_bounds(y, m)
        rows = (q.filter(models.Content.planned_date >= start,
                         models.Content.planned_date <= end)
                .order_by(models.Content.planned_date,
                          models.Content.planned_time).all())
    else:
        rows = q.order_by(models.Content.planned_date,
                          models.Content.planned_time).all()
        # KETMA-KETLIK: bugun va keyingi kunlar OLDINDA (eng yaqini
        # birinchi), o'tganlar ORQADA (eng yaqin o'tgani birinchi).
        # Sanasi yo'qlar eng oxirida - ular hali rejalashtirilmagan.
        kel = [c for c in rows if c.planned_date and c.planned_date >= today]
        otgan = [c for c in rows if c.planned_date and c.planned_date < today]
        sanasiz = [c for c in rows if not c.planned_date]
        otgan.reverse()
        rows = kel + otgan + sanasiz
    mets = {x.content_id: x for x in db.query(models.ContentMetric)
            .filter(models.ContentMetric.content_id
                    .in_([c.id for c in rows] or [-1])).all()}
    uids = {c.owner_id for c in rows if c.owner_id}
    unames = {u.id: u.full_name for u in db.query(models.User)
              .filter(models.User.id.in_(uids or [-1])).all()}
    out = [_plan_row(db, c, mets.get(c.id), unames) for c in rows]
    # Qaysi oylarda post bor — tanlagich uchun (bo'sh oy ko'rsatilmasin)
    oylar = sorted({(c.planned_date.year, c.planned_date.month)
                    for c in rows if c.planned_date}, reverse=True)
    return {
        "year": y, "month": m,
        "scope": scope,
        "month_label": roles.UZ_MONTHS[m - 1],
        "today": today.isoformat(),
        "months": [{"year": yy, "month": mm,
                    "label": f"{roles.UZ_MONTHS[mm - 1]} {yy}",
                    "count": sum(1 for c in rows if c.planned_date
                                 and (c.planned_date.year,
                                      c.planned_date.month) == (yy, mm))}
                   for yy, mm in oylar],
        "rows": out,
        "meta": {
            "platforms": roles.SOCIAL_PLATFORMS,
            "pillars": [{"key": k, "label": lbl, "tone": t, "hint": h}
                        for k, lbl, t, h in roles.CONTENT_PILLARS],
            "funnels": [{"key": k, "label": lbl}
                        for k, lbl in roles.FUNNEL_STAGES],
            "goals": [{"key": k, "label": lbl}
                      for k, lbl, _mm in roles.CONTENT_GOALS],
            "formats": [{"key": k, "label": lbl}
                        for k, lbl in roles.CONTENT_FORMATS],
            "statuses": [{"key": k, "label": lbl, "tone": t}
                         for k, lbl, t in roles.CONTENT_STATUSES],
            # Mas'ul tanlash (2026-09-26): SMM jamoasi + hozir biror
            # postga mas'ul bo'lganlar (ro'yxatdan chiqib qolmasin)
            "owners": [{"id": u.id, "name": u.full_name}
                       for u in db.query(models.User)
                       .filter((models.User.is_active == 1)
                               & (models.User.role.in_(
                                   list(roles.SMM_ACCESS))
                                  | models.User.id.in_(uids or [-1])))
                       .order_by(models.User.full_name).all()],
        },
    }


@router.post("/api/content/{cid}/copy")
def copy_content(cid: int, payload: dict | None = None,
                 db: Session = Depends(get_db),
                 user=Depends(require_role(*roles.SMM_ACCESS))):
    """Kontentni NUSXALASH.

    Jahongir: "kopya qilishga oson bo'lsin". Seriyali kontentda
    (Ustoz-serial №1, №2, №3) faqat mavzu o'zgaradi — qolgani bir
    xil. Nusxa yangi sana bilan ochiladi va holati "G'oya"ga
    qaytadi: bu YANGI ish, tayyor deb belgilanib qolmasin.
    """
    src = db.query(models.Content).get(cid)
    if not src:
        raise HTTPException(404, "Kontent topilmadi")
    p = payload or {}
    new_date = p.get("planned_date")
    c = models.Content(
        title=(p.get("title") or (src.title + " (nusxa)"))[:300],
        platform=src.platform, fmt=src.fmt, pillar=src.pillar,
        goal=src.goal, funnel=src.funnel, audience=src.audience,
        branch_id=src.branch_id, course=src.course,
        campaign_id=src.campaign_id, series=src.series,
        status="idea",
        planned_date=(date.fromisoformat(new_date) if new_date
                      else src.planned_date),
        planned_time=src.planned_time,
        owner_id=src.owner_id, copywriter_id=src.copywriter_id,
        designer_id=src.designer_id, videographer_id=src.videographer_id,
        editor_id=src.editor_id,
        problem=src.problem, message=src.message, hook=src.hook,
        proof=src.proof, location=src.location,
        participants=src.participants, props=src.props,
        duration=src.duration, music=src.music,
        design_format=src.design_format, cta=src.cta,
        references=src.references,
        script=src.script, caption=src.caption,
        hashtags=src.hashtags, story_text=src.story_text,
        on_video_text=src.on_video_text,
        kpi_target=src.kpi_target,
        priority=src.priority, created_by=user.full_name,
        # NUSXAGA KO'CHMAYDIGANLAR: havola, natija, xulosa, e'lon
        # vaqti. Ular AYNAN o'sha postniki edi.
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    # Kod id ma'lum bo'lgandan keyin beriladi (mavjud qoida)
    if not c.content_id:
        c.content_id = _content_code(c)
        db.commit()
    return _plan_row(db, c, None)


@router.post("/api/content/{cid}/fetch")
def fetch_content_metrics(cid: int, db: Session = Depends(get_db),
                          user=Depends(require_role(*roles.SMM_ACCESS))):
    """Post havolasidan natijani AVTOMAT olish.

    Qo'lda kiritilgan raqamlar ustidan yozilmaydi: agar avval qo'lda
    kiritilgan bo'lsa va avtomat 0 qaytarsa, eskisi qoladi.
    """
    c = db.query(models.Content).get(cid)
    if not c:
        raise HTTPException(404, "Kontent topilmadi")
    if not (c.post_url or "").strip():
        raise HTTPException(400, "Avval post havolasini kiriting")

    data, note = _cf.fetch(c.post_url)
    m = (db.query(models.ContentMetric)
         .filter(models.ContentMetric.content_id == cid).first())
    if not m:
        m = models.ContentMetric(content_id=cid)
        db.add(m)
    m.fetch_note = note[:250] if note else None
    m.fetched_at = datetime.utcnow()
    if data:
        for k in ("views", "reach", "likes", "comments", "shares", "saves"):
            v = int(data.get(k) or 0)
            if v:                      # 0 bo'lsa eskisiga tegmaymiz
                setattr(m, k, v)
        m.source = "auto"
        m.updated_by = "avtomat"
    db.commit()
    db.refresh(m)
    return {"ok": bool(data), "note": note,
            "platform": _cf.platform_of(c.post_url),
            "metrics": _plan_row(db, c, m)["metrics"]}


@router.post("/api/smm/fetch-all")
def fetch_all_metrics(year: int | None = None, month: int | None = None,
                      db: Session = Depends(get_db),
                      user=Depends(require_role(*roles.SMM_ACCESS))):
    """E'lon qilingan postlarning natijasini yangilaydi.

    2026-08-28: oy berilmasa — HAMMASI. Kontent-plan endi oy bo'yicha
    emas, sana bo'yicha ketma-ketlikda ko'rsatiladi, shuning uchun
    "Natijalarni yangilash" ham ekrandagi hamma postni qamrashi
    kerak edi (avval jimgina faqat joriy oyni yangilardi)."""
    q = db.query(models.Content).filter(models.Content.post_url.isnot(None))
    if year or month:
        today = roles.local_today()
        y, m = year or today.year, month or today.month
        start, end = billing.month_bounds(y, m)
        q = q.filter(models.Content.planned_date >= start,
                     models.Content.planned_date <= end)
    rows = q.all()
    ok, fail, notes = 0, 0, {}
    for c in rows:
        if not (c.post_url or "").strip():
            continue
        data, note = _cf.fetch(c.post_url)
        met = (db.query(models.ContentMetric)
               .filter(models.ContentMetric.content_id == c.id).first())
        if not met:
            met = models.ContentMetric(content_id=c.id)
            db.add(met)
        met.fetched_at = datetime.utcnow()
        met.fetch_note = note[:250] if note else None
        if data:
            for k in ("views", "reach", "likes", "comments",
                      "shares", "saves"):
                v = int(data.get(k) or 0)
                if v:
                    setattr(met, k, v)
            met.source = "auto"
            met.updated_by = "avtomat"
            ok += 1
        else:
            fail += 1
            notes[note] = notes.get(note, 0) + 1
    db.commit()
    return {"updated": ok, "failed": fail,
            "reasons": [{"note": k, "count": v} for k, v in notes.items()]}


@router.get("/api/smm/content-analytics")
def content_analytics(months: int = 3, branch_id: int | None = None,
                      db: Session = Depends(get_db),
                      user=Depends(require_role(*roles.SMM_ACCESS))):
    """KUCHLI TAHLIL — nima ishlayapti, nima yo'q.

    Jahongir: "kuchli tahlil qilsa ob'ladi."

    Savol "nechta ko'rish bo'ldi" emas. Savol shu: KEYINGI OY NIMANI
    KO'PROQ QILISH KERAK. Shuning uchun har kesim (ustun, format,
    platforma, voronka, hafta kuni, soat) bo'yicha O'RTACHA ko'rish
    va O'RTACHA faollik hisoblanadi — jami emas.

    NEGA O'RTACHA: jami raqam faqat "nechta post qilingani"ni
    ko'rsatadi. 10 ta o'rtacha post 2 ta zo'r postdan ko'p yig'adi
    va noto'g'ri xulosa beradi.

    Kamida 2 ta post bo'lgan kesimlargina taqqoslanadi — bitta
    tasodifiy post butun yo'nalishni "eng zo'r" qilib ko'rsatmasin.
    """
    today = roles.local_today()
    since = today - timedelta(days=30 * max(1, min(months, 12)))
    # keep_unset: filialsiz post UMUMIY kontent — har filialda
    # ko'rinadi. Aks holda Excel'dan yuklangan reja "yo'q" bo'lib
    # qolardi (2026-08-28).
    q = scope_to_branch(db.query(models.Content), models.Content,
                        user, branch_id, keep_unset=True)
    rows = (q.filter(models.Content.planned_date >= since,
                     models.Content.status == "published").all())
    ids = [c.id for c in rows]
    mets = {x.content_id: x for x in db.query(models.ContentMetric)
            .filter(models.ContentMetric.content_id.in_(ids or [-1])).all()}

    w = roles.ENGAGEMENT_WEIGHT_MAP

    def _score(m):
        return ((m.likes or 0) * w["like"] + (m.comments or 0) * w["comment"]
                + (m.saves or 0) * w["save"] + (m.shares or 0) * w["share"]
                + (m.dms or 0) * w["dm"])

    items = []
    for c in rows:
        m = mets.get(c.id)
        if not m:
            continue
        base = m.reach or m.views or 0
        if not base:
            continue
        items.append({
            "id": c.id, "title": c.title,
            "date": c.planned_date.isoformat() if c.planned_date else None,
            "views": m.views or 0, "reach": m.reach or 0,
            "likes": m.likes or 0, "comments": m.comments or 0,
            "shares": m.shares or 0, "saves": m.saves or 0,
            "er": round(_score(m) / base * 100, 2),
            "pillar": c.pillar, "fmt": c.fmt, "platform": c.platform,
            "funnel": c.funnel, "audience": c.audience,
            "weekday": (c.planned_date.weekday()
                        if c.planned_date else None),
            "hour": int((c.planned_time or "0:00").split(":")[0] or 0),
            "url": c.post_url,
        })

    def _cut(key, labels=None):
        agg = {}
        for it in items:
            k = it.get(key)
            if k in (None, ""):
                continue
            d = agg.setdefault(k, {"n": 0, "views": 0, "er": 0.0})
            d["n"] += 1
            d["views"] += it["views"]
            d["er"] += it["er"]
        out = []
        for k, d in agg.items():
            out.append({
                "key": k,
                "label": (labels or {}).get(k, k),
                "count": d["n"],
                "avg_views": round(d["views"] / d["n"]),
                "avg_er": round(d["er"] / d["n"], 2),
            })
        out.sort(key=lambda x: -x["avg_views"])
        return out

    by_pillar = _cut("pillar", roles.PILLAR_LABELS)
    by_fmt = _cut("fmt", roles.FORMAT_LABELS)
    by_platform = _cut("platform")
    by_funnel = _cut("funnel", roles.FUNNEL_LABELS)
    by_day = _cut("weekday", {i: roles.UZ_WEEKDAYS[i] for i in range(7)})
    by_hour = _cut("hour", {h: f"{h:02d}:00" for h in range(24)})

    n = len(items)
    avg_v = round(sum(i["views"] for i in items) / n) if n else 0
    avg_er = round(sum(i["er"] for i in items) / n, 2) if n else 0.0
    top = sorted(items, key=lambda x: -x["views"])[:5]
    weak = sorted(items, key=lambda x: x["views"])[:5]

    # ---- Xulosa: nima qilish kerak -------------------------------
    tips = []

    def _best(rows_, nom, birlik="ko'rish"):
        good = [r for r in rows_ if r["count"] >= 2]
        if len(good) < 2:
            return
        b, wst = good[0], good[-1]
        if b["avg_views"] >= wst["avg_views"] * 1.4:
            tips.append({
                "kind": "good",
                "text": (f"{nom}: «{b['label']}» o'rtacha {b['avg_views']} "
                         f"{birlik} beryapti — «{wst['label']}» dan "
                         f"{round(b['avg_views'] / max(1, wst['avg_views']), 1)} "
                         f"barobar ko'p. Keyingi oyda «{b['label']}» "
                         f"ulushini oshiring."),
            })

    _best(by_pillar, "Kontent ustuni")
    _best(by_fmt, "Format")
    _best(by_day, "Hafta kuni")
    _best(by_platform, "Platforma")

    er_rows = [r for r in by_pillar if r["count"] >= 2]
    if er_rows:
        be = max(er_rows, key=lambda r: r["avg_er"])
        if be["avg_er"] > avg_er * 1.3 and be["avg_er"] > 0:
            tips.append({
                "kind": "good",
                "text": (f"Eng jonli muloqot «{be['label']}» da: faollik "
                         f"{be['avg_er']}% (o'rtacha {avg_er}%). Izoh va "
                         f"ulashish kerak bo'lganda shu yo'nalishdan "
                         f"foydalaning."),
            })

    no_metric = sum(1 for c in rows if c.id not in mets)
    if no_metric:
        tips.append({
            "kind": "warn",
            "text": (f"{no_metric} ta e'lon qilingan postda natija yo'q. "
                     f"Havolani qo'ying va «Natijani yangilash» ni "
                     f"bosing — tahlil shularsiz to'liq emas."),
        })
    if n and n < 5:
        tips.append({
            "kind": "warn",
            "text": ("Taqqoslash uchun ma'lumot hali kam "
                     f"({n} ta post). Xulosa 10-15 postdan keyin "
                     "ishonchli bo'ladi."),
        })

    return {
        "months": months, "count": n,
        "avg_views": avg_v, "avg_er": avg_er,
        "total_views": sum(i["views"] for i in items),
        "by_pillar": by_pillar, "by_format": by_fmt,
        "by_platform": by_platform, "by_funnel": by_funnel,
        "by_weekday": by_day, "by_hour": by_hour,
        "top": top, "weak": weak, "tips": tips,
    }


# =====================================================================
#  EXCEL KONTENT-PLANNI IMPORT QILISH (2026-08-27)
#
#  Jahongir: tayyor Excel bor, uni qo'lda ko'chirish 30 qatorlik ish.
#
#  FAYL BROUZERDA O'QILADI. Sabab: serverda Excel kutubxonasi yo'q
#  va uni qo'shish serverless to'plamini og'irlashtiradi. Brouzerda
#  esa xlsx kutubxonasi allaqachon bor (hisobot yuklab olish uchun).
#  Shuning uchun bu yerga TAYYOR qatorlar keladi.
#
#  IKKI BOSQICH: avval dry_run=1 bilan ko'rib chiqiladi ("nima
#  qo'shiladi, nima o'tkazib yuboriladi"), keyin haqiqiy import.
#  Pul emas, lekin 30 qatorni ko'r-ko'rona bazaga yozish yaxshi
#  odat emas.
#
#  TAKROR QO'SHILMAYDI: shu sana + shu mavzu allaqachon bo'lsa,
#  qator O'TKAZIB YUBORILADI. Import ikki marta bosilsa ham
#  kontent ikkilanmaydi.
# =====================================================================

@router.post("/api/smm/plan/import")
def import_plan(payload: dict = Body(...),
                db: Session = Depends(get_db),
                user=Depends(require_role(*roles.SMM_ACCESS))):
    """{year, month, rows: [...], dry_run: bool, branch_id}

    rows — Excel sarlavhalari bilan: "Sana", "Vaqt", "Platforma",
    "Auditoriya segmenti", "Kontent ustuni", "Voronka bosqichi",
    "Maqsad", "Mavzu", "Hook (1-jumla)", "Asosiy fikr", "Dalil",
    "Format", "CTA", "Mas'ul", "Syomka sanasi", "Kutilayotgan KPI".
    """
    today = roles.local_today()
    y = int(payload.get("year") or today.year)
    m = int(payload.get("month") or today.month)
    dry = bool(payload.get("dry_run"))
    branch_id = payload.get("branch_id") or user.branch_id
    rows = payload.get("rows") or []
    if not isinstance(rows, list):
        raise HTTPException(400, "rows ro'yxat bo'lishi kerak")
    if len(rows) > 200:
        raise HTTPException(400, "Bir martada 200 qatordan ko'p bo'lmasin")

    # DUBL TEKSHIRUVI endi bitta oy bilan chegaralanmaydi: faylda
    # to'liq sana bo'lsa qatorlar boshqa oyga tushishi mumkin.
    # Chegara 13 oy — butun bazani tortmaslik uchun.
    ufq = date(y, m, 1) - timedelta(days=400)
    have = {(c.planned_date, (c.title or "").strip().lower())
            for c in db.query(models.Content)
            .filter(models.Content.planned_date >= ufq).all()}

    def _g(r, *names):
        for n in names:
            for k in r:
                if str(k).strip().lower() == n.strip().lower():
                    v = r[k]
                    return str(v).strip() if v is not None else ""
        return ""

    # OY QAYERDAN OLINADI — 2026-08-28 da tuzatilgan JIDDIY XATO.
    #
    # Jahongir: "qara men excel fayl qilib yukladim SENTABRnikini
    # lekin menda ko'rinmayabdi". Sabab: import oyni FAYLDAN emas,
    # ekrandagi tanlagichdan olardi. U avgustda turgan edi -> sentabr
    # rejasi AVGUSTGA yozilib ketdi va sentabr bo'sh qoldi.
    #
    # Endi tartib shunday:
    #   1) Qatordagi sana TO'LIQ bo'lsa (2026-09-14 yoki Excel
    #      raqamli sanasi) — o'sha sana AYNAN olinadi;
    #   2) faqat kun bo'lsa ("14", "1-sen") — nishon oy qo'llanadi.
    # Ya'ni faylda to'liq sana bo'lsa, tanlagich unga TA'SIR QILMAYDI.
    _EXCEL_EPOCH = date(1899, 12, 30)     # Excel sanani shundan sanaydi

    def _full_date(txt):
        """To'liq sana chiqara olsak — o'shani qaytaradi, aks holda None."""
        t = str(txt or "").strip()
        if not t:
            return None
        # ISO: 2026-09-14 yoki 2026-09-14T00:00:00
        if len(t) >= 10 and t[4] == "-" and t[7] == "-":
            try:
                return date.fromisoformat(t[:10])
            except ValueError:
                pass
        # 14.09.2026 / 14/09/2026
        for sep in (".", "/"):
            parts = t.split(sep)
            if len(parts) == 3 and all(x.strip().isdigit() for x in parts):
                dd, mm, yy = (int(x) for x in parts)
                if yy > 1900 and 1 <= mm <= 12:
                    try:
                        return date(yy, mm, dd)
                    except ValueError:
                        pass
        # Excel raqamli sana (45900 kabi). Faqat ishonchli oraliqda:
        # 40000-60000 ~ 2009-2064. Kichik raqamlar oddiy KUN bo'ladi.
        try:
            n = float(t)
            if 40000 <= n <= 60000:
                return _EXCEL_EPOCH + timedelta(days=int(n))
        except ValueError:
            pass
        return None

    def _day(txt):
        """'1-sen', '14', '2026-09-14' -> oyning kuni."""
        f = _full_date(txt)
        if f is not None:
            return f.day
        t = str(txt or "").strip()
        if not t:
            return None
        digits = ""
        for ch in t:
            if ch.isdigit():
                digits += ch
            elif digits:
                break
        return int(digits) if digits else None

    users_by_name = {}
    for u in db.query(models.User).filter(models.User.is_active == 1).all():
        users_by_name[(u.full_name or "").strip().lower()] = u.id

    plan, skipped, bad = [], [], []
    for i, r in enumerate(rows):
        if not isinstance(r, dict):
            continue
        title = _g(r, "Mavzu", "Post mavzusi", "Title")
        sana_raw = _g(r, "Sana", "Date")
        pd = _full_date(sana_raw)        # faylda to'liq sana bormi?
        if pd is None:
            dnum = _day(sana_raw)
            if not title or not dnum:
                if title or sana_raw:
                    bad.append({"row": i + 1, "why": "sana yoki mavzu yo'q"})
                continue
            try:
                pd = date(y, m, dnum)
            except ValueError:
                bad.append({"row": i + 1, "why": f"{dnum}-kun bu oyda yo'q"})
                continue
        elif not title:
            bad.append({"row": i + 1, "why": "mavzu yo'q"})
            continue
        if (pd, title.strip().lower()) in have:
            skipped.append({"date": pd.isoformat(), "title": title})
            continue

        fmt_raw = _g(r, "Format")
        owner_raw = _g(r, "Mas'ul", "Masul", "Owner")
        oid = None
        for nm, uid in users_by_name.items():
            if nm and nm.split()[0] in owner_raw.lower():
                oid = uid
                break
        sd = _day(_g(r, "Syomka sanasi", "Syomka"))
        item = {
            "title": title[:300],
            "planned_date": pd,
            "planned_time": _g(r, "Vaqt", "Time") or None,
            "platform": _g(r, "Platforma", "Platform") or None,
            "audience": _g(r, "Auditoriya segmenti", "Auditoriya") or None,
            "pillar": roles.import_key(_g(r, "Kontent ustuni"),
                                       roles.IMPORT_PILLARS),
            "funnel": roles.import_key(_g(r, "Voronka bosqichi"),
                                       roles.IMPORT_FUNNELS),
            "goal": roles.import_key(_g(r, "Maqsad"), roles.IMPORT_GOALS),
            "hook": _g(r, "Hook (1-jumla)", "Hook") or None,
            "message": _g(r, "Asosiy fikr", "Message") or None,
            "proof": _g(r, "Dalil", "Proof") or None,
            "fmt": roles.import_format(fmt_raw),
            "cta": _g(r, "CTA") or None,
            "owner_id": oid,
            "owner_raw": owner_raw or None,
            "shoot_date": (date(y, m, sd)
                           if sd and 1 <= sd <= 31 else None),
            "kpi_target": _g(r, "Kutilayotgan KPI", "KPI") or None,
            "fmt_raw": fmt_raw or None,
        }
        plan.append(item)

    if dry:
        return {
            "dry_run": True, "year": y, "month": m,
            "will_add": len(plan), "skipped": len(skipped),
            "bad": bad,
            "preview": [{
                "date": x["planned_date"].isoformat(),
                "time": x["planned_time"], "title": x["title"],
                "pillar": roles.PILLAR_LABELS.get(x["pillar"], "—"),
                "funnel": roles.FUNNEL_LABELS.get(x["funnel"], "—"),
                "fmt": roles.FORMAT_LABELS.get(x["fmt"], x["fmt"]),
                "owner": x["owner_raw"],
                "owner_found": bool(x["owner_id"]),
            } for x in plan[:60]],
            "skipped_rows": skipped[:20],
        }

    made = []
    for x in plan:
        note = None
        if x["fmt_raw"] and x["fmt_raw"].lower() not in (
                roles.FORMAT_LABELS.get(x["fmt"], "") or "").lower():
            # Asl so'z saqlanadi: "Reels-reportaj" degan aniqlik
            # yo'qolmasin.
            note = f"Format (asl matn): {x['fmt_raw']}"
        if x["owner_raw"] and not x["owner_id"]:
            note = ((note + " · ") if note else "") \
                + f"Mas'ul: {x['owner_raw']}"
        c = models.Content(
            title=x["title"], planned_date=x["planned_date"],
            planned_time=x["planned_time"], platform=x["platform"],
            audience=x["audience"], pillar=x["pillar"],
            funnel=x["funnel"], goal=x["goal"], fmt=x["fmt"],
            hook=x["hook"], message=x["message"], proof=x["proof"],
            cta=x["cta"], owner_id=x["owner_id"],
            shoot_date=x["shoot_date"], kpi_target=x["kpi_target"],
            branch_id=branch_id, status="idea", note=note,
            created_by=user.full_name,
        )
        db.add(c)
        made.append(c)
    db.commit()
    for c in made:
        if not c.content_id:
            c.content_id = _content_code(c)
    db.commit()
    return {"added": len(made), "skipped": len(skipped), "bad": bad,
            "year": y, "month": m}


# =====================================================================
#  AVGUST TEST REJASINI YOPISH (2026-09-26)
#
#  Jahongir: "avgust oyidagi kontent plandagi kechikkanlarni olib
#  tashla uni men shunchaki tekshirish uchun qilganman".
#
#  O'CHIRILMAYDI ("hech narsa o'chirilmasin"). Avgust 2026 dagi,
#  hali chiqmagan (ochiq holatdagi) kontentlar "cancelled" holatiga
#  o'tadi: ro'yxat, doska va "Kechikkanlar" ogohlantirishidan chiqadi.
#  Har biriga ContentVersion(field="status") yoziladi — eski holat
#  tarixda turadi, "Holat doskasi"da "Bekor qilinganlar"ni yoqib
#  istalganini qaytarib surish mumkin. Bir martalik (SeedMark).
# =====================================================================
_AUG_TEST_KEY = "smm_aug2026_test_cancel_v1"
_AUG_TEST_NOTE = ("Avgust test rejasi — asoschi so'rovi bilan bekor "
                  "qilindi (2026-09-26). O'chirilmagan.")


def cancel_aug_test_content(db: Session) -> int:
    import common as _cm
    if _cm._seed_done(db, _AUG_TEST_KEY):
        return 0
    n = 0
    try:
        rows = (db.query(models.Content)
                .filter(models.Content.planned_date >= date(2026, 8, 1),
                        models.Content.planned_date <= date(2026, 8, 31),
                        ~models.Content.status.in_(
                            list(roles.CONTENT_LIVE) + ["cancelled"]))
                .all())
        for c in rows:
            db.add(models.ContentVersion(
                content_id=c.id, field="status", old_value=c.status,
                new_value="cancelled", changed_by="Tizim (avgust test)"))
            c.status = "cancelled"
            c.note = ((c.note + "\n") if c.note else "") + _AUG_TEST_NOTE
            n += 1
        db.commit()
    except Exception:
        db.rollback()
        return 0
    try:
        if n:
            audit.log(db, None, entity="content", action="update",
                      note=f"Avgust 2026 test kontent-rejasidan {n} ta "
                           "kechikkan post bekor qilindi (o'chirilmadi)",
                      commit=True)
    except Exception:
        db.rollback()
    _cm._seed_mark(db, _AUG_TEST_KEY)
    return n


# =====================================================================
#  FAVQULODDA O'ZGARISH (2026-09-26)
#
#  Jahongir: "SMM manager ozi ham kontent planga ozgarishlar
#  favqulotta ozgarishlar qosha olsin".
#
#  Bitta tugma, uch xil ish:
#    add    — rejada yo'q shoshilinch post qo'shish (masalan bugunga)
#    move   — mavjud postni boshqa kunga surish
#    cancel — postni bekor qilish (o'chirilmaydi)
#  Sabab MAJBURIY. Hammasi priority="urgent" belgisi, ContentVersion
#  (field="urgent") va audit bilan — keyin "nega reja o'zgardi?"
#  degan savolga javob bor.
# =====================================================================
@router.post("/api/smm/urgent")
def smm_urgent_change(
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.SMM_ACCESS)),
):
    action = (payload.get("action") or "").strip()
    reason = (payload.get("reason") or "").strip()
    if action not in ("add", "move", "cancel"):
        raise HTTPException(400, "Amal: add / move / cancel")
    if len(reason) < 3:
        raise HTTPException(400, "Favqulodda o'zgarish sababini yozing")

    def _d(v):
        try:
            return date.fromisoformat(str(v)[:10]) if v else None
        except ValueError:
            raise HTTPException(400, "Sana noto'g'ri")

    if action == "add":
        title = (payload.get("title") or "").strip()
        if not title:
            raise HTTPException(400, "Post mavzusini yozing")
        pd = _d(payload.get("planned_date")) or roles.local_today()
        # Kontent-plan kalitlari (instagram/telegram/youtube) ham,
        # taqvim kalitlari (ig_reels, ...) ham qabul qilinadi
        platform = payload.get("platform") or "instagram"
        allowed = {k for k, _ in roles.SOCIAL_PLATFORMS} | set(
            roles.PLATFORM_LABELS)
        if platform not in allowed:
            platform = "instagram"
        c = models.Content(
            title=title, planned_date=pd,
            planned_time=(payload.get("planned_time") or None),
            platform=platform, status="idea", priority="urgent",
            branch_id=payload.get("branch_id") or user.branch_id,
            owner_id=user.id, created_by=user.full_name,
            note=f"FAVQULODDA: {reason}")
        db.add(c)
        db.commit()
        db.refresh(c)
        c.content_id = _content_code(c)
        db.add(models.ContentVersion(
            content_id=c.id, field="urgent", old_value=None,
            new_value=f"Qo'shildi: {reason}", changed_by=user.full_name))
        db.commit()
    else:
        cid = payload.get("content_id")
        c = db.query(models.Content).get(int(cid)) if cid else None
        if not c:
            raise HTTPException(404, "Kontent topilmadi")
        if action == "move":
            nd = _d(payload.get("planned_date"))
            if not nd:
                raise HTTPException(400, "Yangi sanani tanlang")
            db.add(models.ContentMove(
                content_id=c.id, from_date=c.planned_date, to_date=nd,
                reason=f"FAVQULODDA: {reason}", moved_by=user.full_name))
            db.add(models.ContentVersion(
                content_id=c.id, field="urgent",
                old_value=c.planned_date.isoformat() if c.planned_date else None,
                new_value=f"Ko'chirildi {nd.isoformat()}: {reason}",
                changed_by=user.full_name))
            c.planned_date = nd
            if payload.get("planned_time"):
                c.planned_time = payload.get("planned_time")
        else:
            db.add(models.ContentVersion(
                content_id=c.id, field="urgent", old_value=c.status,
                new_value=f"Bekor qilindi: {reason}",
                changed_by=user.full_name))
            c.status = "cancelled"
        c.priority = "urgent"
        c.note = ((c.note + "\n") if c.note else "") + f"FAVQULODDA: {reason}"
        db.commit()

    audit.log(db, user, entity="content", action="urgent", entity_id=c.id,
              entity_label=c.title, new_value=action,
              note=f"Favqulodda o'zgarish ({action}): {reason}",
              branch_id=c.branch_id)
    db.commit()
    return _content_out(db, c, full=True)


# =====================================================================
#  HAR VIDEODAN MUROJAAT VA SOTUV (2026-09-26)
#
#  Jahongir: "Har bir videodan nechta odam murojaat qildi, nechta sotuv
#  boldi aniq avtomat hisoblashni yo'lga qoyish kerak".
#
#  Lid qaysi postdan kelgani (Lead.content_id) uch yo'l bilan yoziladi:
#    1) administrator lid ochganda "Qaysi videodan?" ni tanlaydi;
#    2) saytdagi ariza havolasida ?c=<post raqami> yoki
#       utm_content=CONTENT-JA-... yoki promo-kod bo'lsa — avtomat;
#    3) "Murojaatlar"dan lidga aylantirilganda (avvaldan bor).
#  Sotuv = lid o'quvchiga aylangani, tushum = o'sha o'quvchining
#  to'lovlari (kind="payment"). Hammasi BIR NECHTA so'rov bilan —
#  har post uchun alohida so'rov yo'q (Neon trafigi).
# =====================================================================
def attribution_by_content(db: Session, ids: list) -> dict:
    ids = [i for i in ids if i]
    out = {i: {"messages": 0, "leads": 0, "sales": 0, "revenue": 0.0}
           for i in ids}
    if not ids:
        return out
    for cid, n in (db.query(models.SocialMessage.content_id,
                            func.count(models.SocialMessage.id))
                   .filter(models.SocialMessage.content_id.in_(ids))
                   .group_by(models.SocialMessage.content_id).all()):
        out[cid]["messages"] = int(n or 0)
    leads = (db.query(models.Lead.content_id,
                      models.Lead.converted_student_id)
             .filter(models.Lead.content_id.in_(ids)).all())
    sid_to_c = {}
    for cid, sid in leads:
        out[cid]["leads"] += 1
        if sid:
            out[cid]["sales"] += 1
            sid_to_c[sid] = cid
    if sid_to_c:
        for sid, total in (db.query(models.Payment.student_id,
                                    func.sum(models.Payment.amount))
                           .filter(models.Payment.student_id.in_(
                               list(sid_to_c)),
                                   models.Payment.kind == "payment")
                           .group_by(models.Payment.student_id).all()):
            out[sid_to_c[sid]]["revenue"] += float(total or 0)
    for v in out.values():
        v["revenue"] = round(v["revenue"], 2)
    return out


def resolve_content_ref(db: Session, raw: str | None):
    """"123", "CONTENT-JA-2026-0123", promo-kod yoki havoladagi ?c=123
    / utm_content=... -> Content yoki None."""
    s = (raw or "").strip()
    if not s:
        return None
    import re as _re
    m = _re.search(r"[?&](?:c|utm_content)=([^&#\s]+)", s)
    if m:
        s = urllib_unquote(m.group(1))
    if s.isdigit():
        return db.query(models.Content).get(int(s))
    up = s.upper()
    m = _re.match(r"CONTENT-[A-Z]+-\d{4}-(\d+)$", up)
    if m:
        c = (db.query(models.Content)
             .filter(func.upper(models.Content.content_id) == up).first())
        return c or db.query(models.Content).get(int(m.group(1)))
    return (db.query(models.Content)
            .filter(func.upper(models.Content.promo_code) == up).first())


def urllib_unquote(s: str) -> str:
    from urllib.parse import unquote
    return unquote(s or "")


@router.get("/api/leads/content-options")
def lead_content_options(db: Session = Depends(get_db),
                         user=Depends(require_role(*roles.LEAD_ACCESS))):
    """Lid formasidagi "Qaysi videodan?" ro'yxati: oxirgi 60 kunda
    joylangan postlar (yangisi tepada)."""
    since = roles.local_today() - timedelta(days=60)
    rows = (db.query(models.Content)
            .filter(models.Content.planned_date >= since,
                    models.Content.status.in_(list(roles.CONTENT_LIVE)))
            .order_by(models.Content.planned_date.desc(),
                      models.Content.id.desc())
            .limit(120).all())
    return {"rows": [{
        "id": c.id, "title": c.title,
        "date": c.planned_date.isoformat() if c.planned_date else None,
        "platform": c.platform,
        "platform_label": roles.PLATFORM_LABELS.get(c.platform or "", "—"),
        "code": c.content_id or _content_code(c),
    } for c in rows]}


@router.get("/api/smm/per-post")
def smm_per_post(months: int = 3, branch_id: int | None = None,
                 db: Session = Depends(get_db),
                 user=Depends(require_role(*roles.SMM_ACCESS))):
    """Har bir joylangan post: ko'rish, obuna + murojaat, lid, sotuv,
    tushum. Tahlil ekranidagi asosiy jadval."""
    today = roles.local_today()
    since = today - timedelta(days=30 * max(1, min(months, 12)))
    q = scope_to_branch(db.query(models.Content), models.Content,
                        user, branch_id, keep_unset=True)
    rows = (q.filter(models.Content.planned_date >= since,
                     models.Content.status.in_(list(roles.CONTENT_LIVE)))
            .order_by(models.Content.planned_date.desc()).all())
    ids = [c.id for c in rows]
    mets = {x.content_id: x for x in db.query(models.ContentMetric)
            .filter(models.ContentMetric.content_id.in_(ids or [-1])).all()}
    att = attribution_by_content(db, ids)
    out = []
    for c in rows:
        m = mets.get(c.id)
        a = att.get(c.id, {})
        out.append({
            "id": c.id, "title": c.title,
            "code": c.content_id or _content_code(c),
            "date": c.planned_date.isoformat() if c.planned_date else None,
            "platform": c.platform,
            "platform_label": roles.PLATFORM_LABELS.get(c.platform or "", "—"),
            "url": c.post_url,
            "views": (m.views or 0) if m else 0,
            "reach": (m.reach or 0) if m else 0,
            "follows": (getattr(m, "follows", 0) or 0) if m else 0,
            "messages": a.get("messages", 0),
            "leads": a.get("leads", 0),
            "sales": a.get("sales", 0),
            "revenue": a.get("revenue", 0.0),
        })
    tot = {k: sum(r[k] for r in out)
           for k in ("views", "follows", "messages", "leads", "sales",
                     "revenue")}
    return {"rows": out, "totals": tot, "months": months}
