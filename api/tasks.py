"""Auto-extracted from main.py during refactor (split-main). Domain: tasks."""
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

@router.get("/api/tasks")
def list_tasks(
    status_filter: Optional[str] = None,
    assignee_id: Optional[int] = None,
    mine: bool = False,
    branch_id: Optional[int] = None,
    source: Optional[str] = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TASK_ACCESS)),
):
    backfill_missing_ids(db, "task", models.Task)
    q = scope_to_branch(db.query(models.Task), models.Task, user, branch_id)

    # Vazifalarni boshqarish huquqi bo'lmagan odam faqat o'ziga tegishlini
    # ko'radi - boshqalarning vazifasi uni chalg'itmaydi.
    if user.role not in tuple(roles.TASK_MANAGE) or mine:
        q = q.filter((models.Task.assignee_id == user.id)
                     | (models.Task.watcher_id == user.id))
    if assignee_id:
        q = q.filter(models.Task.assignee_id == assignee_id)
    if source:
        q = q.filter(models.Task.source == source)

    rows = [_task_out(db, t) for t in q.all()]
    if status_filter:
        rows = [r for r in rows if r["status"] == status_filter]

    # Muhimi tepada: kechikkan → shoshilinch → yaqin muddat
    rows.sort(key=lambda r: (
        0 if r["overdue"] else 1,
        -r["priority_rank"],
        r["days_left"] if r["days_left"] is not None else 9999,
    ))

    counts = {}
    for t in q.all():
        st = _task_status(t)
        counts[st] = counts.get(st, 0) + 1

    return {
        "rows": rows,
        "counts": counts,
        "statuses": [{"key": k, "label": lbl, "tone": t,
                      "count": counts.get(k, 0)}
                     for k, lbl, t in roles.TASK_STATUSES],
        "priorities": [{"key": k, "label": lbl}
                       for k, lbl, _ in roles.TASK_PRIORITIES],
        "sources": [{"key": k, "label": lbl} for k, lbl in roles.TASK_SOURCES],
        "can_manage": user.role in tuple(roles.TASK_MANAGE),
        "overdue": sum(1 for r in rows if r["overdue"]),
        "open": sum(1 for r in rows if r["status"] not in roles.TASK_CLOSED),
    }

@router.post("/api/tasks")
def create_task(
    payload: schemas.TaskCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TASK_ACCESS)),
):
    if not (payload.title or "").strip():
        raise HTTPException(400, "Vazifa nomini yozing")
    if payload.priority not in roles.TASK_PRIORITY_LABELS:
        raise HTTPException(400, "Noto'g'ri ustuvorlik")
    if payload.source not in roles.TASK_SOURCE_LABELS:
        raise HTTPException(400, "Noto'g'ri manba")

    bid = payload.branch_id
    if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
        bid = user.branch_id

    t = models.Task(
        title=payload.title.strip(),
        description=payload.description,
        assignee_id=payload.assignee_id,
        watcher_id=payload.watcher_id,
        branch_id=bid,
        deadline=payload.deadline,
        priority=payload.priority,
        source=payload.source,
        meeting=payload.meeting,
        checklist=json.dumps([{"text": x, "done": False}
                              for x in (payload.checklist or []) if x.strip()]),
        created_by=user.full_name,
    )
    db.add(t); db.commit(); db.refresh(t)
    _ensure_public_id(db, "task", t)
    audit.log(db, user, entity="task", action="create", entity_id=t.id,
              entity_label=t.title, branch_id=t.branch_id, new_value=t.title)
    db.commit(); db.refresh(t)
    return _task_out(db, t)

@router.put("/api/tasks/{task_id}")
def update_task(
    task_id: int,
    payload: schemas.TaskUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TASK_ACCESS)),
):
    t = db.query(models.Task).get(task_id)
    if not t:
        raise HTTPException(404, "Vazifa topilmadi")
    is_owner = t.assignee_id == user.id or t.watcher_id == user.id
    if user.role not in tuple(roles.TASK_MANAGE) and not is_owner:
        raise HTTPException(403, "Bu vazifa sizga tegishli emas")

    fields = payload.model_dump(exclude_unset=True)

    # Mas'ul odam vazifani boshqasiga o'tkazib yubormasligi kerak -
    # buni faqat rahbar qila oladi.
    if user.role not in tuple(roles.TASK_MANAGE):
        for k in ("assignee_id", "watcher_id", "deadline", "priority",
                  "branch_id"):
            fields.pop(k, None)

    if "status" in fields:
        new = fields["status"]
        if new not in roles.TASK_STATUS_LABELS:
            raise HTTPException(400, "Noto'g'ri status")
        # "Kechikdi" - tizim o'zi qo'yadigan status, qo'lda tanlanmaydi.
        if new == "late":
            raise HTTPException(
                400, "\"Kechikdi\" statusini tizim o'zi qo'yadi")
        # Muddati o'tib bajarilyaptimi - sabab so'raladi.
        if (new == "done" and t.deadline and t.deadline < date.today()
                and not (fields.get("delay_reason") or t.delay_reason)):
            raise HTTPException(
                400, "Muddat o'tgan — kechikish sababini yozing")
        if new == "done":
            fields.setdefault("result", t.result)
            t.done_at = datetime.utcnow()
        elif t.status == "done":
            t.done_at = None

    if "checklist" in fields:
        rows = fields.pop("checklist") or []
        t.checklist = json.dumps([
            {"text": str(r.get("text", "")), "done": bool(r.get("done"))}
            for r in rows if isinstance(r, dict)])

    audit.log_changes(db, user, entity="task", obj=t,
                      changes={k: v for k, v in fields.items()
                               if k in ("status", "assignee_id", "deadline",
                                        "priority")})
    for k, v in fields.items():
        setattr(t, k, v)
    db.commit(); db.refresh(t)
    return _task_out(db, t)

@router.delete("/api/tasks/{task_id}")
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TASK_MANAGE)),
):
    t = db.query(models.Task).get(task_id)
    if not t:
        raise HTTPException(404, "Vazifa topilmadi")
    audit.log(db, user, entity="task", action="delete", entity_id=t.id,
              entity_label=t.title, branch_id=t.branch_id, old_value=t.title)
    db.delete(t); db.commit()
    return {"ok": True}

@router.post("/api/tasks/from-meeting")
def tasks_from_meeting(
    payload: schemas.MeetingDecisions,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TASK_MANAGE)),
):
    """Majlis qarorlarini vazifaga aylantirish. Bir majlisdan 5 ta qaror
    chiqsa - 5 ta vazifa, har biri mas'uli va muddati bilan."""
    if not payload.decisions:
        raise HTTPException(400, "Qarorlar ro'yxati bo'sh")
    made = []
    for d in payload.decisions:
        if not (d.title or "").strip():
            continue
        t = models.Task(
            title=d.title.strip(),
            description=d.description,
            assignee_id=d.assignee_id,
            watcher_id=payload.watcher_id,
            branch_id=payload.branch_id,
            deadline=d.deadline or payload.deadline,
            priority=d.priority or "normal",
            source="meeting",
            meeting=payload.meeting,
            created_by=user.full_name,
        )
        db.add(t); db.flush()
        _ensure_public_id(db, "task", t)
        made.append(t)
    db.commit()
    return {"created": len(made),
            "rows": [_task_out(db, t) for t in made]}

