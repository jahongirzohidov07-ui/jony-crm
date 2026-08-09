"""Auto-extracted from main.py during refactor (split-main). Domain: branches_rooms."""
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

@router.get("/api/branches", response_model=List[schemas.BranchOut])
def list_branches(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(models.Branch).order_by(models.Branch.name).all()

@router.post("/api/branches", response_model=schemas.BranchOut)
def create_branch(
    payload: schemas.BranchCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(roles.FOUNDER)),
):
    branch = models.Branch(**payload.model_dump())
    db.add(branch)
    db.commit()
    db.refresh(branch)
    return branch

@router.put("/api/branches/{branch_id}", response_model=schemas.BranchOut)
def update_branch(
    branch_id: int,
    payload: schemas.BranchCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(roles.FOUNDER)),
):
    b = db.query(models.Branch).get(branch_id)
    if not b:
        raise HTTPException(404, "Filial topilmadi")
    if not payload.name.strip():
        raise HTTPException(400, "Filial nomini kiriting")
    b.name = payload.name.strip()
    b.address = payload.address
    db.commit()
    db.refresh(b)
    return b

@router.delete("/api/branches/{branch_id}")
def delete_branch(
    branch_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(roles.FOUNDER)),
):
    """Filialni faqat bo'sh bo'lsa o'chirish mumkin - aks holda
    o'quvchi va guruhlar "yetim" qolib ketardi."""
    b = db.query(models.Branch).get(branch_id)
    if not b:
        raise HTTPException(404, "Filial topilmadi")
    for model, nomi in ((models.Student, "o'quvchi"), (models.Group, "guruh"),
                        (models.Teacher, "ustoz"), (models.User, "xodim")):
        n = db.query(model).filter(model.branch_id == branch_id).count()
        if n:
            raise HTTPException(
                400, f"Bu filialda {n} ta {nomi} bor - avval ularni "
                     "boshqa filialga o'tkazing")
    db.delete(b)
    db.commit()
    return {"ok": True}

def _room_out(r: models.Room, groups: list = None) -> dict:
    return {
        "id": r.id, "name": r.name, "capacity": r.capacity,
        "branch_id": r.branch_id,
        "branch": r.branch.name if r.branch else None,
        "note": r.note, "active": bool(r.active),
        "groups": [{"id": g.id, "name": g.name} for g in (groups or [])],
    }

@router.get("/api/rooms")
def list_rooms(
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_STAFF)),
):
    q = scope_to_branch(db.query(models.Room), models.Room, user)
    rooms = q.order_by(models.Room.name).all()
    by_room = {}
    for g in db.query(models.Group).filter(models.Group.room_id.isnot(None)).all():
        by_room.setdefault(g.room_id, []).append(g)
    return [_room_out(r, by_room.get(r.id, [])) for r in rooms]

@router.post("/api/rooms")
def create_room(
    payload: schemas.RoomCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.ACADEMIC_ACCESS)),
):
    data = payload.model_dump()
    if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
        data["branch_id"] = user.branch_id
    r = models.Room(**data)
    db.add(r); db.commit(); db.refresh(r)
    audit.log(db, user, entity="room", action="create", entity_id=r.id,
              entity_label=r.name, new_value=r.capacity,
              branch_id=r.branch_id, commit=True)
    return _room_out(r)

@router.put("/api/rooms/{room_id}")
def update_room(
    room_id: int,
    payload: schemas.RoomUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.ACADEMIC_ACCESS)),
):
    r = db.query(models.Room).get(room_id)
    if not r:
        raise HTTPException(404, "Xona topilmadi")
    changes = payload.model_dump(exclude_unset=True)
    audit.log_changes(db, user, entity="room", obj=r, changes=changes,
                      label_attr="name")
    for k, v in changes.items():
        setattr(r, k, v)
    db.commit(); db.refresh(r)
    return _room_out(r)

@router.delete("/api/rooms/{room_id}")
def delete_room(
    room_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.ACADEMIC_ACCESS)),
):
    r = db.query(models.Room).get(room_id)
    if not r:
        raise HTTPException(404, "Xona topilmadi")
    n = db.query(models.Group).filter(models.Group.room_id == room_id).count()
    if n:
        raise HTTPException(400, f"Bu xonada {n} ta guruh bor")
    audit.log(db, user, entity="room", action="delete", entity_id=r.id,
              entity_label=r.name, branch_id=r.branch_id)
    db.delete(r); db.commit()
    return {"ok": True}

