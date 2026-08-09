"""Auto-extracted from main.py during refactor (split-main). Domain: complaints."""
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

@router.get("/api/complaints")
def list_complaints(
    status: str | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_STAFF)),
):
    q = scope_to_branch(db.query(models.Complaint), models.Complaint, user)
    if status:
        q = q.filter(models.Complaint.status == status)
    return [_complaint_out(c)
            for c in q.order_by(models.Complaint.created_at.desc()).all()]

@router.post("/api/complaints")
def create_complaint(
    payload: schemas.ComplaintCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_STAFF)),
):
    data = payload.model_dump()
    if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
        data["branch_id"] = user.branch_id
    c = models.Complaint(**data, created_by=user.full_name)
    db.add(c); db.commit(); db.refresh(c)
    audit.log(db, user, entity="complaint", action="create", entity_id=c.id,
              entity_label=c.subject, new_value=c.severity,
              branch_id=c.branch_id, commit=True)
    return _complaint_out(c)

@router.put("/api/complaints/{complaint_id}")
def update_complaint(
    complaint_id: int,
    payload: schemas.ComplaintUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_STAFF)),
):
    c = db.query(models.Complaint).get(complaint_id)
    if not c:
        raise HTTPException(404, "Shikoyat topilmadi")
    changes = payload.model_dump(exclude_unset=True)
    audit.log_changes(db, user, entity="complaint", obj=c, changes=changes,
                      label_attr="subject")
    for k, v in changes.items():
        setattr(c, k, v)
    # Yopilgan sana avtomat - qo'lda eslab qolish shart emas.
    c.closed_at = date.today() if c.status == "closed" else None
    db.commit()
    return _complaint_out(c)

@router.delete("/api/complaints/{complaint_id}")
def delete_complaint(
    complaint_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FULL_ACCESS)),
):
    c = db.query(models.Complaint).get(complaint_id)
    if not c:
        raise HTTPException(404, "Shikoyat topilmadi")
    audit.log(db, user, entity="complaint", action="delete", entity_id=c.id,
              entity_label=c.subject, branch_id=c.branch_id)
    db.delete(c); db.commit()
    return {"ok": True}

