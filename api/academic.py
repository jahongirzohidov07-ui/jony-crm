"""Auto-extracted from main.py during refactor (split-main). Domain: academic."""
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

@router.get("/api/academic/group-fill")
def group_fill(
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.ACADEMIC_VIEW)),
):
    """Guruh to'lishi = faol o'quvchi / sig'im x 100%.

    Bu markazning eng muhim iqtisodiy ko'rsatkichi: yarim bo'sh guruh
    ustoz vaqtini ham, xona ijarasini ham to'liq yeydi, lekin
    daromadning yarmini beradi."""
    rooms = {r.id: r for r in db.query(models.Room).all()}
    gq = scope_to_branch(db.query(models.Group), models.Group, user, branch_id)
    counts = {}
    for s in scope_to_branch(db.query(models.Student), models.Student, user, branch_id).all():
        if s.status == "active" and s.group_id:
            counts[s.group_id] = counts.get(s.group_id, 0) + 1

    rows, no_capacity = [], []
    for g in gq.all():
        n = counts.get(g.id, 0)
        cap = _group_capacity(g, rooms)
        if not cap:
            no_capacity.append({"id": g.id, "name": g.name})
            continue
        pct = round(n / cap * 100, 1)
        band, band_label = roles.fill_band(pct)
        rows.append({
            "id": g.id, "name": g.name,
            "teacher": g.teacher.full_name if g.teacher else None,
            "branch": g.branch.name if g.branch else None,
            "room": rooms[g.room_id].name if g.room_id in rooms else g.room,
            "students": n, "capacity": cap,
            "percent": pct, "band": band, "band_label": band_label,
            "free_seats": max(0, cap - n),
        })
    rows.sort(key=lambda r: r["percent"])

    total_students = sum(r["students"] for r in rows)
    total_capacity = sum(r["capacity"] for r in rows)
    by_band = {}
    for r in rows:
        by_band[r["band"]] = by_band.get(r["band"], 0) + 1

    return {
        "rows": rows,
        "no_capacity": no_capacity,
        "summary": {
            "groups": len(rows),
            "students": total_students,
            "capacity": total_capacity,
            "percent": round(total_students / total_capacity * 100, 1)
                       if total_capacity else 0.0,
            "free_seats": max(0, total_capacity - total_students),
            "by_band": [
                {"band": k, "label": lbl, "count": by_band.get(k, 0)}
                for _m, k, lbl in roles.GROUP_FILL_BANDS
            ],
        },
    }

def _absent_streak(db: Session, student_id: int, group_id: int | None) -> int:
    """Oxirgi darslardan boshlab ketma-ket nechta dars qoldirgan."""
    if not group_id:
        return 0
    lessons = (db.query(models.Lesson)
               .filter(models.Lesson.group_id == group_id,
                       models.Lesson.held == 1)
               .order_by(models.Lesson.date.desc()).limit(12).all())
    if not lessons:
        return 0
    marks = {a.lesson_id: a.present for a in
             db.query(models.Attendance).filter(
                 models.Attendance.student_id == student_id,
                 models.Attendance.lesson_id.in_([l.id for l in lessons])).all()}
    streak = 0
    for l in lessons:
        v = marks.get(l.id)
        if v is None:      # belgilanmagan - zanjir uzilmaydi, lekin sanalmaydi
            continue
        if v:
            break
        streak += 1
    return streak

def _score_trend(db: Session, student_id: int) -> float | None:
    """Oxirgi ikki imtihon farqi (foizda). Manfiy - natija tushgan."""
    rows = (db.query(models.ExamResult)
            .join(models.Exam)
            .filter(models.ExamResult.student_id == student_id,
                    models.ExamResult.percent.isnot(None))
            .order_by(models.Exam.date.desc()).limit(2).all())
    if len(rows) < 2:
        return None
    return round((rows[0].percent or 0) - (rows[1].percent or 0), 1)

def _student_risk(db: Session, s: models.Student, *, today: date,
                  flags_by_student: dict, complaints_by_student: dict,
                  moves_by_student: dict) -> dict:
    """Bitta o'quvchining risk holati. Signallar ikki manbadan:
    avtomat hisoblanadigan (davomat, to'lov, shikoyat, guruh almashish)
    va qo'lda qo'yilgan (ustoz izohi, uy vazifasi)."""
    signals = []

    def add(key, detail=None):
        signals.append({
            "key": key,
            "label": roles.RISK_SIGNAL_LABELS.get(key, key),
            "weight": roles.RISK_SIGNAL_WEIGHT.get(key, 1),
            "detail": detail,
        })

    streak = _absent_streak(db, s.id, s.group_id)
    if streak >= 2:
        add("absent_streak", f"ketma-ket {streak} ta dars")

    bal = student_balance(db, s.id)
    if bal < 0:
        add("payment_late", f"{abs(int(bal)):,} so'm qarz".replace(",", " "))

    n_comp = complaints_by_student.get(s.id, 0)
    if n_comp:
        add("complaint", f"{n_comp} ta shikoyat")

    n_moves = moves_by_student.get(s.id, 0)
    if n_moves >= 2:
        add("group_hopping", f"{n_moves} marta guruh almashtirgan")

    # AVTOMAT: uy vazifasi endi haqiqiy ma'lumot. Ilgari bu signal
    # faqat qo'lda qo'yilardi va shuning uchun deyarli hech qachon
    # qo'yilmasdi.
    hw = _homework_stats(db, s.id, since=today - timedelta(days=60))
    if hw["enough"] and hw["percent"] is not None \
            and hw["percent"] < roles.HOMEWORK_RISK_PERCENT:
        add("no_homework",
            f"{hw['checked']} tadan {hw['done']} tasi ({hw['percent']}%)")

    trend = _score_trend(db, s.id)
    if trend is not None and trend <= -10:
        add("score_drop", f"{trend} foiz")
    elif trend is not None and -2 <= trend <= 2:
        # O'sish yo'q - tushmayapti ham, ko'tarilmayapti ham
        add("no_progress", "natija joyida turibdi")

    for f in flags_by_student.get(s.id, []):
        add(f.signal, f.note)

    score = sum(x["weight"] for x in signals)
    level = roles.risk_level(score)
    return {
        "student_id": s.id,
        "public_id": s.public_id,
        "full_name": s.full_name,
        "group_id": s.group_id,
        "group": s.group.name if s.group else None,
        "teacher": s.group.teacher.full_name
                   if s.group and s.group.teacher else None,
        "branch": s.branch.name if s.branch else None,
        "phone": s.phone,
        "score": score,
        "level": level,
        "level_label": roles.RISK_LEVEL_LABELS[level],
        "signals": signals,
    }

@router.get("/api/academic/risk")
def academic_risk(
    level: str | None = None,
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.ACADEMIC_VIEW)),
):
    """Xavfdagi o'quvchilar. Ro'yxat avtomat hisoblanadi - hech kim
    qo'lda 'bu bola ketib qoladi' deb belgilashi shart emas."""
    today = date.today()
    students = [s for s in
                scope_to_branch(db.query(models.Student), models.Student, user, branch_id).all()
                if s.status in ("active", "trial")]
    ids = [s.id for s in students]

    flags_by_student = {}
    complaints_by_student = {}
    moves_by_student = {}
    if ids:
        for f in (db.query(models.RiskFlag)
                  .filter(models.RiskFlag.student_id.in_(ids),
                          models.RiskFlag.active == 1).all()):
            flags_by_student.setdefault(f.student_id, []).append(f)
        for c in (db.query(models.Complaint)
                  .filter(models.Complaint.student_id.in_(ids),
                          models.Complaint.status != "closed").all()):
            complaints_by_student[c.student_id] = (
                complaints_by_student.get(c.student_id, 0) + 1)
        for a in (db.query(models.AuditLog)
                  .filter(models.AuditLog.entity == "student",
                          models.AuditLog.action == "group_move",
                          models.AuditLog.entity_id.in_(ids)).all()):
            moves_by_student[a.entity_id] = moves_by_student.get(a.entity_id, 0) + 1

    rows = [_student_risk(db, s, today=today,
                          flags_by_student=flags_by_student,
                          complaints_by_student=complaints_by_student,
                          moves_by_student=moves_by_student)
            for s in students]
    at_risk = [r for r in rows if r["level"] != "normal"]
    at_risk.sort(key=lambda r: -r["score"])
    if level:
        at_risk = [r for r in at_risk if r["level"] == level]

    counts = {k: 0 for k, _, _, _ in roles.RISK_LEVELS}
    for r in rows:
        counts[r["level"]] = counts.get(r["level"], 0) + 1

    # Ochiq vazifalar - kimga biriktirilgani ko'rinib tursin
    open_tasks = {}
    if ids:
        for t in (db.query(models.RiskTask)
                  .filter(models.RiskTask.student_id.in_(ids),
                          models.RiskTask.status == "open").all()):
            open_tasks.setdefault(t.student_id, []).append({
                "id": t.id, "title": t.title,
                "assigned_user": t.assigned_user.full_name
                                 if t.assigned_user else None,
                "due_date": t.due_date.isoformat() if t.due_date else None,
            })
    for r in at_risk:
        r["tasks"] = open_tasks.get(r["student_id"], [])

    return {
        "total": len(rows),
        "at_risk": len(at_risk),
        "levels": [{"key": k, "label": lbl, "color": color,
                    "count": counts.get(k, 0)}
                   for k, lbl, color, _ in roles.RISK_LEVELS],
        "rows": at_risk,
        "signals": [{"key": k, "label": lbl, "weight": w}
                    for k, lbl, w in roles.RISK_SIGNALS],
    }

@router.post("/api/academic/risk-flags")
def add_risk_flag(
    payload: schemas.RiskFlagCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.ACADEMIC_VIEW)),
):
    if payload.signal not in roles.RISK_SIGNAL_LABELS:
        raise HTTPException(400, "Noma'lum signal")
    f = models.RiskFlag(**payload.model_dump(), created_by=user.full_name)
    db.add(f); db.commit(); db.refresh(f)
    audit.log(db, user, entity="student", action="update",
              entity_id=f.student_id, field="risk",
              new_value=roles.RISK_SIGNAL_LABELS[f.signal],
              note=f.note, commit=True)
    return {"id": f.id}

@router.delete("/api/academic/risk-flags/{flag_id}")
def resolve_risk_flag(
    flag_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.ACADEMIC_VIEW)),
):
    f = db.query(models.RiskFlag).get(flag_id)
    if not f:
        raise HTTPException(404, "Topilmadi")
    f.active = 0
    f.resolved_at = date.today()
    db.commit()
    return {"ok": True}

@router.get("/api/academic/tasks")
def list_risk_tasks(
    status: str | None = "open",
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.ACADEMIC_VIEW)),
):
    q = db.query(models.RiskTask).join(
        models.Student, models.RiskTask.student_id == models.Student.id)
    if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
        q = q.filter(models.Student.branch_id == user.branch_id)
    if status:
        q = q.filter(models.RiskTask.status == status)
    today = date.today()
    return [{
        "id": t.id,
        "student_id": t.student_id,
        "student": t.student.full_name if t.student else None,
        "level": t.level,
        "level_label": roles.RISK_LEVEL_LABELS.get(t.level or "", ""),
        "title": t.title,
        "assigned_user_id": t.assigned_user_id,
        "assigned_user": t.assigned_user.full_name if t.assigned_user else None,
        "due_date": t.due_date.isoformat() if t.due_date else None,
        "overdue": bool(t.due_date and t.status == "open" and t.due_date < today),
        "status": t.status,
        "result": t.result,
        "created_at": t.created_at.isoformat() if t.created_at else None,
    } for t in q.order_by(models.RiskTask.due_date).all()]

@router.post("/api/academic/tasks")
def create_risk_task(
    payload: schemas.RiskTaskCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.ACADEMIC_VIEW)),
):
    t = models.RiskTask(**payload.model_dump(), created_by=user.full_name)
    db.add(t); db.commit(); db.refresh(t)
    audit.log(db, user, entity="student", action="update", entity_id=t.student_id,
              field="risk_task", new_value=t.title,
              note=f"Mas'ul: {t.assigned_user.full_name}" if t.assigned_user else None,
              commit=True)
    return {"id": t.id}

@router.put("/api/academic/tasks/{task_id}")
def update_risk_task(
    task_id: int,
    payload: schemas.RiskTaskUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.ACADEMIC_VIEW)),
):
    t = db.query(models.RiskTask).get(task_id)
    if not t:
        raise HTTPException(404, "Vazifa topilmadi")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(t, k, v)
    t.done_at = date.today() if t.status == "done" else None
    db.commit()
    return {"ok": True}

@router.delete("/api/academic/tasks/{task_id}")
def delete_risk_task(
    task_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.ACADEMIC_ACCESS)),
):
    t = db.query(models.RiskTask).get(task_id)
    if not t:
        raise HTTPException(404, "Vazifa topilmadi")
    db.delete(t); db.commit()
    return {"ok": True}

