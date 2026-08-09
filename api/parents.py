"""Auto-extracted from main.py during refactor (split-main). Domain: parents."""
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

def _parent_out(p: models.Parent, students: list = None) -> dict:
    return {
        "id": p.id,
        "public_id": p.public_id,
        "full_name": p.full_name,
        "phone": p.phone,
        "phone2": p.phone2,
        "relation": p.relation,
        "address": p.address,
        "workplace": p.workplace,
        "note": p.note,
        "branch_id": p.branch_id,
        "branch": p.branch.name if p.branch else None,
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "students": [{"id": s.id, "public_id": s.public_id,
                      "full_name": s.full_name, "status": s.status}
                     for s in (students or [])],
    }

@router.get("/api/parents")
def list_parents(
    q: str | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_STAFF)),
):
    query = scope_to_branch(db.query(models.Parent), models.Parent, user)
    if q:
        like = f"%{q}%"
        query = query.filter(
            (models.Parent.full_name.ilike(like))
            | (models.Parent.phone.ilike(like))
            | (models.Parent.public_id.ilike(like))
        )
    rows = query.order_by(models.Parent.full_name).all()
    kids = {}
    if rows:
        for st in (db.query(models.Student)
                   .filter(models.Student.parent_id.in_([r.id for r in rows]))
                   .all()):
            kids.setdefault(st.parent_id, []).append(st)
    return [_parent_out(p, kids.get(p.id, [])) for p in rows]

@router.get("/api/parents/{parent_id}")
def get_parent(
    parent_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_STAFF)),
):
    p = db.query(models.Parent).get(parent_id)
    if not p:
        raise HTTPException(404, "Ota-ona topilmadi")
    kids = db.query(models.Student).filter(
        models.Student.parent_id == p.id).all()
    return _parent_out(p, kids)

@router.post("/api/parents")
def create_parent(
    payload: schemas.ParentCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_STAFF)),
):
    data = payload.model_dump()
    if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
        data["branch_id"] = user.branch_id
    p = models.Parent(**data, created_by=user.username)
    db.add(p); db.commit(); db.refresh(p)
    _ensure_public_id(db, "parent", p)
    audit.log(db, user, entity="parent", action="create", entity_id=p.id,
              entity_label=p.full_name, new_value=p.full_name,
              branch_id=p.branch_id)
    db.commit(); db.refresh(p)
    return _parent_out(p)

@router.put("/api/parents/{parent_id}")
def update_parent(
    parent_id: int,
    payload: schemas.ParentUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_STAFF)),
):
    p = db.query(models.Parent).get(parent_id)
    if not p:
        raise HTTPException(404, "Ota-ona topilmadi")
    changes = payload.model_dump(exclude_unset=True)
    # Telefon o'zgarishi alohida amal sifatida yoziladi - eski raqam
    # tarixda qolishi kerak.
    audit.log_changes(db, user, entity="parent", obj=p, changes=changes)
    for k, v in changes.items():
        setattr(p, k, v)
    db.commit(); db.refresh(p)
    return _parent_out(p)

@router.delete("/api/parents/{parent_id}")
def delete_parent(
    parent_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FULL_ACCESS)),
):
    p = db.query(models.Parent).get(parent_id)
    if not p:
        raise HTTPException(404, "Ota-ona topilmadi")
    n = db.query(models.Student).filter(models.Student.parent_id == p.id).count()
    if n:
        raise HTTPException(400, f"Bu ota-onaga {n} ta o'quvchi bog'langan")
    audit.log(db, user, entity="parent", action="delete", entity_id=p.id,
              entity_label=p.full_name, old_value=p.full_name,
              branch_id=p.branch_id)
    db.delete(p); db.commit()
    return {"ok": True}

def _contract_out(c: models.Contract) -> dict:
    return {
        "id": c.id,
        "public_id": c.public_id,
        "student_id": c.student_id,
        "student": c.student.full_name if c.student else None,
        "student_public_id": c.student.public_id if c.student else None,
        "parent_id": c.parent_id,
        "parent": c.parent.full_name if c.parent else None,
        "group_id": c.group_id,
        "group": c.group.name if c.group else None,
        "branch_id": c.branch_id,
        "branch": c.branch.name if c.branch else None,
        "date": c.date.isoformat() if c.date else None,
        "start_date": c.start_date.isoformat() if c.start_date else None,
        "end_date": c.end_date.isoformat() if c.end_date else None,
        "monthly_fee": c.monthly_fee,
        "discount_percent": c.discount_percent,
        "status": c.status,
        "note": c.note,
        "created_by": c.created_by,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }

@router.get("/api/contracts")
def list_contracts(
    student_id: int | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FINANCE_ACCESS)),
):
    q = scope_to_branch(db.query(models.Contract), models.Contract, user)
    if student_id:
        q = q.filter(models.Contract.student_id == student_id)
    if status:
        q = q.filter(models.Contract.status == status)
    return [_contract_out(c)
            for c in q.order_by(models.Contract.date.desc()).all()]

@router.post("/api/contracts")
def create_contract(
    payload: schemas.ContractCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FINANCE_ACCESS)),
):
    st = db.query(models.Student).get(payload.student_id)
    if not st:
        raise HTTPException(404, "O'quvchi topilmadi")
    data = payload.model_dump()
    # Bo'sh qoldirilgan maydonlarni o'quvchidan avtomat to'ldiramiz.
    data["branch_id"] = data.get("branch_id") or st.branch_id
    data["parent_id"] = data.get("parent_id") or st.parent_id
    data["group_id"] = data.get("group_id") or st.group_id
    if not data.get("monthly_fee") and st.group:
        data["monthly_fee"] = st.group.monthly_fee
    c = models.Contract(**data, created_by=user.full_name)
    db.add(c); db.commit(); db.refresh(c)
    _ensure_public_id(db, "contract", c)
    audit.log(db, user, entity="contract", action="create", entity_id=c.id,
              entity_label=st.full_name, new_value=c.monthly_fee,
              branch_id=c.branch_id)
    db.commit(); db.refresh(c)
    return _contract_out(c)

@router.put("/api/contracts/{contract_id}")
def update_contract(
    contract_id: int,
    payload: schemas.ContractUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FINANCE_ACCESS)),
):
    c = db.query(models.Contract).get(contract_id)
    if not c:
        raise HTTPException(404, "Shartnoma topilmadi")
    changes = payload.model_dump(exclude_unset=True)
    audit.log_changes(db, user, entity="contract", obj=c, changes=changes,
                      label_attr="public_id")
    for k, v in changes.items():
        setattr(c, k, v)
    db.commit(); db.refresh(c)
    return _contract_out(c)

@router.delete("/api/contracts/{contract_id}")
def delete_contract(
    contract_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FULL_ACCESS)),
):
    c = db.query(models.Contract).get(contract_id)
    if not c:
        raise HTTPException(404, "Shartnoma topilmadi")
    audit.log(db, user, entity="contract", action="delete", entity_id=c.id,
              entity_label=c.public_id, branch_id=c.branch_id)
    db.delete(c); db.commit()
    return {"ok": True}

@router.delete("/api/talks/{talk_id}")
def delete_talk(
    talk_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FULL_ACCESS)),
):
    t = db.query(models.ParentTalk).get(talk_id)
    if not t:
        raise HTTPException(404, "Topilmadi")
    db.delete(t); db.commit()
    return {"ok": True}

@router.delete("/api/certificates/{cert_id}")
def delete_certificate(
    cert_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.ACADEMIC_ACCESS)),
):
    c = db.query(models.Certificate).get(cert_id)
    if not c:
        raise HTTPException(404, "Topilmadi")
    db.delete(c); db.commit()
    return {"ok": True}

@router.get("/api/parent/{token}")
def parent_view(token: str, db: Session = Depends(get_db)):
    """Ota-ona ko'radigan ochiq sahifa ma'lumoti: davomat, vazifa,
    balans. Faqat o'qish; token orqali bitta o'quvchi."""
    if not token or len(token) < 10:
        raise HTTPException(404, "Topilmadi")
    s = db.query(models.Student).filter(
        models.Student.parent_token == token).first()
    if not s:
        raise HTTPException(404, "Topilmadi")
    g = db.query(models.Group).get(s.group_id) if s.group_id else None
    today = roles.local_today()
    start = today - timedelta(days=45)
    rows = (db.query(models.Attendance, models.Lesson)
            .join(models.Lesson,
                  models.Attendance.lesson_id == models.Lesson.id)
            .filter(models.Attendance.student_id == s.id,
                    models.Lesson.date >= start,
                    models.Lesson.date <= today)
            .order_by(models.Lesson.date.desc()).limit(24).all())
    att = [{
        "date": ls.date.isoformat(),
        "present": int(a.present or 0),   # 1 keldi, 2 kech, 0 kelmadi
        "homework": a.homework,           # 2 bajardi, 1 qisman, 0 yo'q
    } for a, ls in rows]
    bal = student_balance(db, s.id)
    st_lbl = {"active": "faol", "trial": "sinovda",
              "frozen": "muzlatilgan", "archived": "arxivda"}
    return {
        "name": s.full_name,
        "group": g.name if g else None,
        "lesson_time": g.lesson_time if g else None,
        "status": st_lbl.get(s.status, s.status),
        "balance": bal,
        "attendance": att,
        "frozen_until": s.frozen_until.isoformat()
        if s.frozen_until else None,
    }

