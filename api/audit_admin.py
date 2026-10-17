"""Auto-extracted from main.py during refactor (split-main). Domain: audit_admin."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bisect
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

@router.get("/api/audit")
def audit_list(
    entity: str | None = None,
    entity_id: int | None = None,
    action: str | None = None,
    user_id: int | None = None,
    days: int = 90,
    limit: int = 200,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.AUDIT_VIEW)),
):
    """O'zgarishlar tarixi. Faqat o'qish uchun - hech kim tahrirlay
    yoki o'chira olmaydi."""
    since = datetime.combine(
        date.today() - timedelta(days=max(1, min(days, 730))),
        datetime.min.time())
    q = db.query(models.AuditLog).filter(models.AuditLog.created_at >= since)

    # O'QUVCHI YOZUVLARI KO'RSATILMAYDI (2026-08-21, Jahongir:
    # "auditda o'quvchilarnikini olib tashlagin, uni alohida hisobotlar
    # bolimiga"). Bazadan hech narsa o'chirilmaydi — faqat ro'yxatda
    # chiqmaydi; o'quvchi faoliyati endi Hisobotlar -> Student app
    # bo'limida statistika bo'lib ko'rinadi.
    q = q.filter(or_(models.AuditLog.user_role.is_(None),
                     models.AuditLog.user_role != roles.STUDENT))

    # Filial rahbari faqat o'z filialining tarixini ko'radi.
    if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
        q = q.filter(
            (models.AuditLog.branch_id == user.branch_id)
            | (models.AuditLog.branch_id.is_(None))
        )
    if entity:
        q = q.filter(models.AuditLog.entity == entity)
    if entity_id:
        q = q.filter(models.AuditLog.entity_id == entity_id)
    if action:
        q = q.filter(models.AuditLog.action == action)
    if user_id:
        q = q.filter(models.AuditLog.user_id == user_id)

    rows = (q.order_by(models.AuditLog.created_at.desc(),
                       models.AuditLog.id.desc())
            .limit(max(1, min(limit, 1000))).all())
    return {
        "total": q.count(),
        "rows": [{
            "id": r.id,
            "user_name": r.user_name or r.username,
            "user_role": r.user_role,
            "entity": r.entity,
            "entity_label_type": audit.ENTITIES.get(r.entity, r.entity),
            "entity_id": r.entity_id,
            "entity_label": r.entity_label,
            "action": r.action,
            "action_label": audit.ACTIONS.get(r.action, r.action),
            "field": r.field,
            "old_value": r.old_value,
            "new_value": r.new_value,
            "note": r.note,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        } for r in rows],
    }

@router.get("/api/audit/meta")
def audit_meta(user=Depends(require_role(*roles.AUDIT_VIEW))):
    return {
        "actions": [{"key": k, "label": v} for k, v in audit.ACTIONS.items()],
        "entities": [{"key": k, "label": v} for k, v in audit.ENTITIES.items()],
    }

# YOPIQ FAYLLAR (2026-10-17, "So'z bilish" sertifikatlari, OWNER D3–D4):
# o'quvchi yuklagan sertifikat fayli (Attachment.entity="vocab_cert")
# FAQAT /api/wordbank/certs/... orqali beriladi — u yerda ustoz faqat o'z
# guruhini, filial xodimi o'z filialini ko'radi va tasdiqlanmagan natija
# begonaga chiqmaydi. Umumiy /api/attachments yo'li esa har qanday
# xodimga istalgan id bo'yicha faylni berib, o'chirishga ham ruxsat
# berardi (tarix yo'qolardi). Shu sababli bu yerda ular "yo'q".
_PRIVATE_ENTITIES = {"vocab_cert"}


@router.get("/api/attachments")
def list_attachments(
    entity: str,
    entity_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_STAFF, *roles.HR_ACCESS)),
):
    """Fayl ro'yxati. Ma'lumot og'ir bo'lgani uchun ro'yxatda faqat
    metama'lumot qaytadi - faylning o'zi alohida so'raladi."""
    if entity in _PRIVATE_ENTITIES:
        return []
    rows = (db.query(models.Attachment)
            .filter(models.Attachment.entity == entity,
                    models.Attachment.entity_id == entity_id)
            .order_by(models.Attachment.created_at.desc()).all())
    return [{
        "id": a.id, "kind": a.kind,
        "kind_label": roles.ATTACHMENT_KIND_LABELS.get(a.kind, a.kind),
        "filename": a.filename, "mime": a.mime, "size": a.size,
        "note": a.note, "created_by": a.created_by,
        "created_at": a.created_at.isoformat() if a.created_at else None,
        "is_image": bool(a.mime and a.mime.startswith("image/")),
    } for a in rows]

@router.get("/api/attachments/{aid}")
def get_attachment(
    aid: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_STAFF, *roles.HR_ACCESS)),
):
    """Faylning o'zi - base64 ko'rinishida."""
    a = db.query(models.Attachment).get(aid)
    if not a or a.entity in _PRIVATE_ENTITIES:
        raise HTTPException(404, "Fayl topilmadi")
    return {"id": a.id, "filename": a.filename, "mime": a.mime,
            "size": a.size, "kind": a.kind, "data": a.data}

@router.post("/api/attachments")
def upload_attachment(
    payload: schemas.AttachmentCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_STAFF, *roles.HR_ACCESS)),
):
    import base64
    raw = payload.data
    # "data:image/png;base64,...." ko'rinishida kelsa - kesib olamiz
    if "," in raw and raw.strip().startswith("data:"):
        raw = raw.split(",", 1)[1]
    try:
        size = len(base64.b64decode(raw, validate=False))
    except Exception:
        raise HTTPException(400, "Fayl o'qib bo'lmadi")
    if size > roles.ATTACHMENT_MAX_BYTES:
        mb = roles.ATTACHMENT_MAX_BYTES // (1024 * 1024)
        raise HTTPException(400, f"Fayl juda katta — {mb} MB dan oshmasin")
    if payload.kind not in roles.ATTACHMENT_KIND_LABELS:
        raise HTTPException(400, "Noma'lum fayl turi")
    if payload.entity in _PRIVATE_ENTITIES:
        # sertifikat fayli faqat o'quvchining o'zi yuklaydi (2026-10-17)
        raise HTTPException(400, "Bu turdagi fayl bu yerdan yuklanmaydi")

    a = models.Attachment(
        entity=payload.entity, entity_id=payload.entity_id,
        kind=payload.kind, filename=payload.filename, mime=payload.mime,
        size=size, data=raw, note=payload.note, created_by=user.full_name)
    db.add(a); db.commit(); db.refresh(a)
    audit.log(db, user, entity=payload.entity, action="update",
              entity_id=payload.entity_id, field="attachment",
              new_value=payload.filename, commit=True)
    return {"id": a.id, "size": size}

@router.delete("/api/attachments/{aid}")
def delete_attachment(
    aid: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_STAFF, *roles.HR_ACCESS)),
):
    a = db.query(models.Attachment).get(aid)
    if not a or a.entity in _PRIVATE_ENTITIES:
        # 2026-10-17: sertifikat fayli o'chirilmaydi (D4 — tarix qoladi)
        raise HTTPException(404, "Fayl topilmadi")
    audit.log(db, user, entity=a.entity, action="update", entity_id=a.entity_id,
              field="attachment", old_value=a.filename,
              note="Fayl o'chirildi")
    db.delete(a); db.commit()
    return {"ok": True}

