"""IZOHLAR TARIXI: o'quvchi va lid kartasida (2026-09-15).

Jahongir: "platformaga izoh yozish qo'shib bering 1ta yozsa bo'larkan
lc updaqa yozganlari oldingilari bilan saqlanib turadigan qilib bering
raqamlar bilan ketma ket korinib tursin".

Ilgari kartada bitta "note" maydoni bor edi — yangi izoh eskisining
ustidan yozilardi. Endi har izoh alohida qator: kim, qachon yozgani
bilan, o'chirilmaydi va tahrirlanmaydi, 1, 2, 3... tartibda ko'rinadi.

Jahongir: "keyin muzlatsa aktivlashtirsa o'quvchini kim qilgani
ko'rinmas ekan shuni ham qo'shish kerak". Holat o'zgarishlari alohida
jadvalga yozilmaydi — audit jurnalida allaqachon bor (kim, qachon).
Shu yerda izohlar orasiga o'z vaqti bo'yicha qo'shib ko'rsatiladi.

Eski "note" maydoni o'chirilmaydi: undagi matn ro'yxatda birinchi
"Oldingi izoh" bo'lib chiqadi.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session

import models
import roles
from auth import require_role
from database import get_db
from common import _get_student_in_scope, _in_user_branches

router = APIRouter()

COMMENT_MAX = 4000
STUDENT_COMMENT_ROLES = roles.TEACHING_STAFF + [roles.HR_MANAGER]

# Audit jurnalidagi holat amallari va ularning nomi
STATUS_ACTIONS = {
    "freeze": "Muzlatildi",
    "auto_freeze": "Avtomat muzlatildi",
    "activate": "Faollashtirildi",
    "to_trial": "Sinovga qaytarildi",
    "to_lead": "Lidga qaytarildi",
    "archive": "Arxivlandi",
    "auto_archive": "Avtomat arxivlandi",
    "restore": "Arxivdan qayta tiklandi",
}


def _iso(dt):
    return dt.isoformat() if dt else None


def _comment_row(c: models.Comment, source: str) -> dict:
    return {"kind": "comment", "source": source, "id": c.id, "text": c.text,
            "by": c.author_name, "date": _iso(c.created_at)}


def _legacy_row(text, by, date, source: str) -> dict:
    return {"kind": "legacy", "source": source, "id": None, "text": text,
            "by": by, "date": _iso(date)}


def _numbered(rows: list) -> list:
    # Sanasiz (eski izoh) — eng boshida, qolgani vaqt tartibida
    rows.sort(key=lambda r: (r["date"] is not None, r["date"] or ""))
    for i, r in enumerate(rows, 1):
        r["n"] = i
    return rows


def _comments_of(db: Session, entity: str, entity_id: int):
    return (db.query(models.Comment)
            .filter(models.Comment.entity == entity,
                    models.Comment.entity_id == entity_id)
            .order_by(models.Comment.created_at, models.Comment.id).all())


def _lead_rows(db: Session, lead: models.Lead, source: str) -> list:
    rows = []
    if (lead.note or "").strip():
        rows.append(_legacy_row(lead.note.strip(), lead.created_by,
                                lead.created_at, source))
    rows += [_comment_row(c, source) for c in _comments_of(db, "lead", lead.id)]
    return rows


def _add(db: Session, user: models.User, entity: str, entity_id: int,
         payload: dict) -> models.Comment:
    text = str((payload or {}).get("text") or "").strip()
    if not text:
        raise HTTPException(400, "Izoh matnini yozing")
    if len(text) > COMMENT_MAX:
        raise HTTPException(400, f"Izoh {COMMENT_MAX} belgidan oshmasin")
    c = models.Comment(entity=entity, entity_id=entity_id, text=text,
                       author_id=user.id, author_name=user.full_name)
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


@router.get("/api/students/{student_id}/comments")
def student_comments(
    student_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*STUDENT_COMMENT_ROLES)),
):
    """O'quvchi izohlari + holat o'zgarishlari (kim muzlatdi/faollashtirdi)
    + lid paytidagi izohlar — hammasi bitta raqamlangan ro'yxatda."""
    s = _get_student_in_scope(db, student_id, user)
    rows = []
    if (s.note or "").strip():
        rows.append(_legacy_row(s.note.strip(), None, None, "student"))
    rows += [_comment_row(c, "student") for c in _comments_of(db, "student", s.id)]

    for lead in (db.query(models.Lead)
                 .filter(models.Lead.converted_student_id == s.id).all()):
        rows += _lead_rows(db, lead, "lead")

    logs = (db.query(models.AuditLog)
            .filter(models.AuditLog.entity == "student",
                    models.AuditLog.entity_id == s.id,
                    models.AuditLog.action.in_(list(STATUS_ACTIONS)))
            .order_by(models.AuditLog.created_at).all())
    status_rows = []
    for l in logs:
        status_rows.append({
            "kind": "status", "source": "student", "id": None,
            "action": l.action, "title": STATUS_ACTIONS[l.action],
            "text": l.note or l.new_value or "",
            "by": l.user_name or "Tizim (avtomat)", "date": _iso(l.created_at),
        })
    last = status_rows[-1] if status_rows else None
    return {
        "rows": _numbered(rows + status_rows),
        "can_write": user.role in STUDENT_COMMENT_ROLES,
        "last_status": ({"title": last["title"], "by": last["by"],
                         "date": last["date"]} if last else None),
    }


@router.post("/api/students/{student_id}/comments")
def add_student_comment(
    student_id: int,
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    user=Depends(require_role(*STUDENT_COMMENT_ROLES)),
):
    s = _get_student_in_scope(db, student_id, user)
    return _comment_row(_add(db, user, "student", s.id, payload), "student")


def _lead_in_scope(db: Session, lead_id: int, user: models.User) -> models.Lead:
    lead = db.query(models.Lead).get(lead_id)
    if not lead:
        raise HTTPException(404, "Lid topilmadi")
    if not _in_user_branches(db, user, lead.branch_id):
        raise HTTPException(403, "Bu lid boshqa filialga tegishli")
    return lead


@router.get("/api/leads/{lead_id}/comments")
def lead_comments(
    lead_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.LEAD_ACCESS)),
):
    lead = _lead_in_scope(db, lead_id, user)
    return {"rows": _numbered(_lead_rows(db, lead, "lead")),
            "can_write": True, "last_status": None}


@router.post("/api/leads/{lead_id}/comments")
def add_lead_comment(
    lead_id: int,
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.LEAD_ACCESS)),
):
    lead = _lead_in_scope(db, lead_id, user)
    return _comment_row(_add(db, user, "lead", lead.id, payload), "lead")
