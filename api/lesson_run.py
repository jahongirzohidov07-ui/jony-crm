"""DARS BOSHQARUVI — ustozning bugungi ish oynasi + "Darsni boshlash"
rejimi (2026-09-18, Jahongir).

  * Guruh ↔ daraja/reja bog'lanadi (group_plans): qaysi kurs, keyingi
    dars raqami, oldingi darsdan ko'chgan bosqichlar (carry).
  * /api/teacher/plan-today — bugungi guruhlar: reja mavzusi, oldingi
    darsda tugallanmagan qismlar, uy vazifasini bajarmaganlar, yordam
    kerak o'quvchilar, tekshirishni kutayotgan ishlar.
  * Dars rejimi (lesson_runs): bosqichlar + taymer, bajarilgan qismlar
    belgilanadi, ustozning MAXFIY izohlari; proyektor rejimida javob
    kalitlari va izohlar ko'rinmaydi (frontend). Dars tugallanmasa —
    qolgan bosqichlar keyingi darsga ko'chadi, guruhning haqiqiy
    o'tgan joyi (next_lesson_no) saqlanadi.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

import models
import roles
from auth import require_role
from database import get_db
from common import _get_group_in_scope, _group_students, _teacher_of_user
from liveplay import LEVELS, _lesson, _load_course, is_english_teacher

router = APIRouter()
TEACHER_APP_ROLES = (roles.TEACHER, roles.SUPPORT_TEACHER)


# ---------------------------------------------------------------
#  Yordamchilar
# ---------------------------------------------------------------
def _course_title(course: str) -> str:
    for c, t, cefr in LEVELS:
        if c == course:
            return f"{t} ({cefr})"
    return course


def _course_len(course: str) -> int:
    d = _load_course(course)
    return len(d["lessons"]) if d else 0


def _plan_of(db, group_id: int):
    return db.query(models.GroupPlan).filter(models.GroupPlan.group_id == group_id).first()


def _plan_out(p) -> Optional[dict]:
    if not p:
        return None
    L = None
    try:
        L = _lesson(p.course, p.next_lesson_no)
    except HTTPException:
        pass
    return {"course": p.course, "course_title": _course_title(p.course),
            "next_lesson_no": p.next_lesson_no, "total": _course_len(p.course),
            "next_title": L["title"] if L else None,
            "next_grammar": L.get("grammar_topic") if L else None,
            "next_vocab": L.get("vocab_topic") if L else None,
            "carry": json.loads(p.carry or "[]")}


def _stages_from_plan(L: dict, carry: list) -> list:
    stages = [{"title": f"Ko'chgan: {c}", "min": 8, "desc": "Oldingi darsda tugallanmagan qism — avval shuni yakunlang.",
               "done": False, "carried": True} for c in carry]
    for m, st, desc in L.get("timeline") or []:
        stages.append({"title": st, "min": int(m), "desc": desc, "done": False, "carried": False})
    return stages


def _run_out(db, r, with_plan=True) -> dict:
    stages = json.loads(r.stages or "[]")
    out = {"id": r.id, "lesson_id": r.lesson_id, "group_id": r.group_id, "course": r.course,
           "lesson_no": r.lesson_no, "status": r.status, "current": r.current or 0,
           "stages": stages, "notes": r.notes or "",
           "started_at": r.started_at.isoformat() if r.started_at else None,
           "stage_started_at": r.stage_started_at.isoformat() if r.stage_started_at else None,
           "finished_at": r.finished_at.isoformat() if r.finished_at else None,
           "done_count": sum(1 for s in stages if s.get("done")), "total": len(stages)}
    g = db.query(models.Group).get(r.group_id)
    out["group"] = g.name if g else None
    if with_plan:
        try:
            out["plan"] = _lesson(r.course, r.lesson_no)
        except HTTPException:
            out["plan"] = None
        out["students"] = [{"id": s.id, "name": s.full_name}
                           for s in _group_students(db, r.group_id)
                           if (s.status or "active") in ("active", "trial")]
    return out


def _lesson_in_scope(db, lesson_id: int, user):
    ls = db.query(models.Lesson).get(lesson_id)
    if not ls:
        raise HTTPException(404, "Dars topilmadi")
    _get_group_in_scope(db, ls.group_id, user)
    return ls


# ---------------------------------------------------------------
#  Guruh ↔ reja
# ---------------------------------------------------------------
class PlanIn(BaseModel):
    course: str
    next_lesson_no: int = 1


@router.put("/api/groups/{gid}/plan")
def set_group_plan(gid: int, body: PlanIn, db: Session = Depends(get_db),
                   user=Depends(require_role(*roles.TEACHING_ACCESS))):
    g = _get_group_in_scope(db, gid, user)
    if not _load_course(body.course):
        raise HTTPException(400, "Bu darajaning rejasi hali tayyor emas")
    n = max(1, min(_course_len(body.course), int(body.next_lesson_no or 1)))
    p = _plan_of(db, g.id)
    if not p:
        p = models.GroupPlan(group_id=g.id, course=body.course, next_lesson_no=n, carry="[]")
        db.add(p)
    else:
        if p.course != body.course:
            p.carry = "[]"
        p.course, p.next_lesson_no = body.course, n
    p.updated_by, p.updated_at = user.full_name, datetime.utcnow()
    db.commit()
    return _plan_out(p)


@router.get("/api/groups/{gid}/plan")
def get_group_plan(gid: int, db: Session = Depends(get_db),
                   user=Depends(require_role(*roles.TEACHING_ACCESS))):
    g = _get_group_in_scope(db, gid, user)
    return {"plan": _plan_out(_plan_of(db, g.id)),
            "courses": [{"course": c, "title": f"{t} ({cefr})", "total": _course_len(c)}
                        for c, t, cefr in LEVELS if _load_course(c)]}


# ---------------------------------------------------------------
#  Bugungi ish oynasi
# ---------------------------------------------------------------
@router.get("/api/teacher/plan-today")
def plan_today(day: Optional[str] = None, db: Session = Depends(get_db),
               user=Depends(require_role(*roles.TEACHING_ACCESS))):
    """Bugungi darslar uchun reja qatlami: mavzu, ko'chgan qismlar,
    uy vazifasini bajarmaganlar, yordam kerak o'quvchilar, tekshirish
    kutayotgan ishlar, boshlangan dars (run)."""
    on = date.fromisoformat(day) if day else roles.local_today()
    t = _teacher_of_user(db, user)
    q = db.query(models.Lesson, models.Group).join(models.Group, models.Lesson.group_id == models.Group.id)
    if user.role in TEACHER_APP_ROLES:
        if not t:
            return {"date": on.isoformat(), "items": [], "english": True, "courses": []}
        q = q.filter(models.Group.teacher_id == t.id)
    rows = q.filter(models.Lesson.date == on).order_by(models.Group.lesson_time, models.Group.name).all()
    items = []
    for ls, g in rows:
        p = _plan_of(db, g.id)
        run = (db.query(models.LessonRun).filter(models.LessonRun.lesson_id == ls.id)
               .order_by(models.LessonRun.id.desc()).first())
        # Oxirgi o'tilgan dars: uy vazifasi 0 bo'lganlar + past baholar
        prev = (db.query(models.Lesson).filter(models.Lesson.group_id == g.id, models.Lesson.date < on,
                                               models.Lesson.held == 1)
                .order_by(models.Lesson.date.desc()).first())
        hw_missing, help_needed = [], []
        if prev:
            names = {s.id: s.full_name for s in _group_students(db, g.id)}
            for a in db.query(models.Attendance).filter(models.Attendance.lesson_id == prev.id).all():
                if a.homework == 0 and a.student_id in names:
                    hw_missing.append(names[a.student_id])
            for gr in db.query(models.DailyGrade).filter(models.DailyGrade.lesson_id == prev.id).all():
                if (gr.score or 0) <= 2 and gr.student_id in names:
                    help_needed.append({"name": names[gr.student_id], "why": f"oxirgi baho {gr.score}"})
        st = json.loads(run.stages or "[]") if run else []
        items.append({
            "lesson_id": ls.id, "group_id": g.id, "group": g.name, "level": g.level,
            "time": g.lesson_time, "held": bool(ls.held),
            "plan": _plan_out(p),
            "run": {"id": run.id, "status": run.status,
                    "done": sum(1 for s in st if s.get("done")), "total": len(st)} if run else None,
            "homework_missing": hw_missing,
            "help_needed": help_needed,
            "pending_checks": 0,   # writing/speaking tekshiruvi — keyingi bosqich
        })
    return {"date": on.isoformat(), "items": items, "english": is_english_teacher(db, user),
            "courses": [{"course": c, "title": f"{tt} ({cefr})", "total": _course_len(c)}
                        for c, tt, cefr in LEVELS if _load_course(c)]}


# ---------------------------------------------------------------
#  Dars rejimi
# ---------------------------------------------------------------
class RunUpdate(BaseModel):
    done: Optional[list] = None        # bajarilgan bosqich indekslari (to'liq ro'yxat)
    current: Optional[int] = None
    notes: Optional[str] = None
    restart_timer: Optional[bool] = None


class FinishIn(BaseModel):
    advance: bool = True               # keyingi darsga o'tilsinmi (rejadagi raqam +1)


@router.post("/api/lessons/{lesson_id}/run")
def start_run(lesson_id: int, db: Session = Depends(get_db),
              user=Depends(require_role(*roles.TEACHING_ACCESS))):
    """'Darsni boshlash': mavjud bo'lsa — davom, bo'lmasa reja bo'yicha
    yangi run. Reja bog'lanmagan bo'lsa — 400 (avval guruhga daraja
    tanlanadi)."""
    ls = _lesson_in_scope(db, lesson_id, user)
    run = (db.query(models.LessonRun).filter(models.LessonRun.lesson_id == ls.id)
           .order_by(models.LessonRun.id.desc()).first())
    if run:
        return _run_out(db, run)
    p = _plan_of(db, ls.group_id)
    if not p:
        raise HTTPException(400, "Guruhga daraja/reja bog'lanmagan — avval rejani tanlang")
    L = _lesson(p.course, p.next_lesson_no)
    stages = _stages_from_plan(L, json.loads(p.carry or "[]"))
    run = models.LessonRun(lesson_id=ls.id, group_id=ls.group_id, course=p.course,
                           lesson_no=p.next_lesson_no, stages=json.dumps(stages, ensure_ascii=False),
                           current=0, status="running", started_at=datetime.utcnow(),
                           stage_started_at=datetime.utcnow(), by_user_id=user.id)
    db.add(run)
    db.commit()
    db.refresh(run)
    return _run_out(db, run)


def _run_in_scope(db, rid: int, user):
    r = db.query(models.LessonRun).get(rid)
    if not r:
        raise HTTPException(404, "Dars rejimi topilmadi")
    _get_group_in_scope(db, r.group_id, user)
    return r


@router.get("/api/runs/{rid}")
def get_run(rid: int, db: Session = Depends(get_db),
            user=Depends(require_role(*roles.TEACHING_ACCESS))):
    return _run_out(db, _run_in_scope(db, rid, user))


@router.put("/api/runs/{rid}")
def update_run(rid: int, body: RunUpdate, db: Session = Depends(get_db),
               user=Depends(require_role(*roles.TEACHING_ACCESS))):
    r = _run_in_scope(db, rid, user)
    if r.status == "finished":
        raise HTTPException(400, "Dars yakunlangan")
    stages = json.loads(r.stages or "[]")
    if body.done is not None:
        done = {int(i) for i in body.done}
        for i, s in enumerate(stages):
            s["done"] = i in done
        r.stages = json.dumps(stages, ensure_ascii=False)
    if body.current is not None and 0 <= int(body.current) < len(stages):
        if int(body.current) != (r.current or 0) or body.restart_timer:
            r.stage_started_at = datetime.utcnow()
        r.current = int(body.current)
    if body.notes is not None:
        r.notes = body.notes[:4000]
    db.commit()
    return _run_out(db, r, with_plan=False)


@router.post("/api/runs/{rid}/finish")
def finish_run(rid: int, body: FinishIn, db: Session = Depends(get_db),
               user=Depends(require_role(*roles.TEACHING_ACCESS))):
    """Yakunlash: tugallanmagan bosqichlar keyingi darsga ko'chadi;
    advance=True bo'lsa guruh rejada keyingi darsga o'tadi."""
    r = _run_in_scope(db, rid, user)
    stages = json.loads(r.stages or "[]")
    left = [s["title"].replace("Ko'chgan: ", "", 1) for s in stages if not s.get("done")]
    # salomlashish/uyga vazifa kabi xizmat bosqichlari ko'chmaydi
    skip = ("salomlash", "uyga vazifa", "zaxira", "kahoot", "normativ")
    left = [x for x in left if not any(k in x.lower() for k in skip)][:6]
    p = _plan_of(db, r.group_id)
    if p:
        p.carry = json.dumps(left, ensure_ascii=False)
        if body.advance:
            p.next_lesson_no = min(_course_len(p.course), r.lesson_no + 1)
        p.updated_at = datetime.utcnow()
    r.status, r.finished_at = "finished", datetime.utcnow()
    db.commit()
    return {"ok": True, "carry": left, "next_lesson_no": p.next_lesson_no if p else None,
            "done": sum(1 for s in stages if s.get("done")), "total": len(stages)}
