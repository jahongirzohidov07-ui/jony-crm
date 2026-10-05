"""O'ZLASHTIRISH XARITASI + RAHBAR HISOBOTI (2026-09-18, Jahongir, 5- va 8-bandlar).

  * Har o'quvchi × mavzu/ko'nikma: O'ZLASHTIRDI / YANA MASHQ KERAK /
    HALI TEKSHIRILMAGAN — oxirgisi "bilmaydi" bilan aralashtirilmaydi.
    Dalillar: avtomat topshiriqlar, Kahoot natijalari (kind=kahoot),
    ustoz baholagan writing/speaking.
  * "Qiynalayotganlarga bir bosishda mos qo'shimcha mashq" —
    POST /api/groups/{gid}/mastery/practice.
  * Rahbar hisoboti: guruh reja bo'yicha qayerda, qiyin mavzular, uy
    vazifasi bajarilishi, tekshirish kutayotgan ishlar, yordamga muhtoj
    o'quvchilar, materialning zaif joylari — o'quvchi o'sishi bo'yicha,
    "necha marta kirdi" bo'yicha emas.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

import models
import roles
from auth import require_role
from database import get_db
from common import _get_group_in_scope, _group_students, _teacher_of_user, scope_to_branch
from liveplay import _lesson, _load_course
from assignments import FromPlanIn, send_from_plan

router = APIRouter()
TEACHER_APP_ROLES = (roles.TEACHER, roles.SUPPORT_TEACHER)
MASTER, PRACTICE, UNCHECKED = "mastered", "practice", "unchecked"
THRESH = 0.8
SKILLS = ("vocab", "grammar", "writing", "speaking")


def _status(ratio: Optional[float]) -> str:
    if ratio is None:
        return UNCHECKED
    return MASTER if ratio >= THRESH else PRACTICE


def _evidence(db, group_id: int) -> dict:
    """(student_id, lesson_no, skill) -> [ratio, ...] — barcha dalillar."""
    ev = defaultdict(list)
    rows = (db.query(models.AssignmentSubmission, models.Assignment)
            .join(models.Assignment, models.AssignmentSubmission.assignment_id == models.Assignment.id)
            .filter(models.Assignment.group_id == group_id,
                    models.AssignmentSubmission.status.in_(("graded", "returned"))).all())
    for s, a in rows:
        if s.status == "returned":
            ev[(s.student_id, a.lesson_no, a.skill or "grammar")].append(0.5)
        elif a.auto and s.auto_max:
            ev[(s.student_id, a.lesson_no, a.skill or "grammar")].append(s.auto_score / s.auto_max)
        elif s.teacher_score is not None and a.max_score:
            ev[(s.student_id, a.lesson_no, a.skill or "writing")].append(s.teacher_score / a.max_score)
    games = {g.exam_id: g for g in db.query(models.LiveGame).filter(models.LiveGame.group_id == group_id,
                                                                     models.LiveGame.exam_id.isnot(None)).all()}
    if games:
        for r in db.query(models.ExamResult).filter(models.ExamResult.exam_id.in_(list(games.keys()))).all():
            g = games[r.exam_id]
            if r.percent is not None:
                skill = "vocab" if g.mode in ("vocab", "vocab40") else ("grammar" if g.mode == "grammar" else "mixed")
                ev[(r.student_id, g.lesson_no, skill)].append(r.percent / 100.0)
    return ev


def _best(ev, sid, no, skill) -> Optional[float]:
    vals = list(ev.get((sid, no, skill), []))
    if skill in ("vocab", "grammar"):
        vals += ev.get((sid, no, "mixed"), [])
    return max(vals) if vals else None


@router.get("/api/groups/{gid}/mastery")
def group_mastery(gid: int, db: Session = Depends(get_db), user=Depends(require_role(*roles.TEACHING_ACCESS))):
    g = _get_group_in_scope(db, gid, user)
    plan = db.query(models.GroupPlan).filter(models.GroupPlan.group_id == g.id).first()
    if not plan:
        return {"group": g.name, "group_id": g.id, "plan": None, "students": [], "lessons": [], "cells": {},
                "summary": [], "skills": list(SKILLS), "hard_topics": []}
    course = _load_course(plan.course) or {"lessons": []}
    lessons = [{"no": L["no"], "title": L["title"], "grammar": L.get("grammar_topic"), "vocab": L.get("vocab_topic")}
               for L in course["lessons"] if L["no"] <= max(1, plan.next_lesson_no)]
    studs = [s for s in _group_students(db, g.id) if (s.status or "active") in ("active", "trial")]
    ev = _evidence(db, g.id)
    cells, summary = {}, []
    weak_topics = defaultdict(int)
    for st in studs:
        good, weak, unchecked = [], [], 0
        for L in lessons:
            row = {}
            for sk in SKILLS:
                r = _best(ev, st.id, L["no"], sk)
                stt = _status(r)
                row[sk] = {"status": stt, "ratio": (round(r * 100) if r is not None else None)}
                if stt == UNCHECKED:
                    unchecked += 1
                elif stt == MASTER:
                    good.append((L["no"], sk))
                else:
                    weak.append({"lesson_no": L["no"], "skill": sk, "title": L["title"], "ratio": round(r * 100)})
                    weak_topics[(L["no"], sk)] += 1
            cells[f"{st.id}:{L['no']}"] = row
        parts = []
        if any(sk == "vocab" for _, sk in good) and not any(w["skill"] == "vocab" for w in weak):
            parts.append("so'zlarni biladi")
        vg = [w for w in weak if w["skill"] in ("vocab", "grammar")]
        if vg:
            parts.append("lekin " + ", ".join(f"{w['lesson_no']}-dars ({w['skill']})" for w in vg[:2]) + " da qiynalmoqda")
        ws = [w for w in weak if w["skill"] in ("writing", "speaking")]
        if ws:
            parts.append(", ".join(f"{w['skill']} ({w['lesson_no']}-dars)" for w in ws[:2]) + " ni qayta bajarishi kerak")
        summary.append({"student_id": st.id, "name": st.full_name,
                        "mastered": len(good), "practice": len(weak), "unchecked": unchecked,
                        "text": (", ".join(parts) if parts else
                                 ("hali tekshirilmagan" if not good else "tekshirilganlarning hammasi o'zlashtirilgan")),
                        "weak": weak[:6]})
    hard = sorted(((no, sk, n) for (no, sk), n in weak_topics.items()), key=lambda x: -x[2])[:6]
    return {"group": g.name, "group_id": g.id,
            "plan": {"course": plan.course, "next_lesson_no": plan.next_lesson_no, "total": len(course["lessons"])},
            "students": [{"id": s.id, "name": s.full_name} for s in studs], "lessons": lessons, "skills": list(SKILLS),
            "cells": cells, "summary": summary,
            "hard_topics": [{"lesson_no": no, "skill": sk, "count": n,
                             "title": next((L["title"] for L in lessons if L["no"] == no), "")} for no, sk, n in hard]}


class PracticeIn(BaseModel):
    student_ids: list
    lesson_no: int
    skill: str = "vocab"      # vocab | grammar


@router.post("/api/groups/{gid}/mastery/practice")
def send_practice(gid: int, body: PracticeIn, db: Session = Depends(get_db),
                  user=Depends(require_role(*roles.TEACHING_ACCESS))):
    """Qiynalayotgan o'quvchilarga bir bosishda mos mashq (shaxsiy topshiriq)."""
    g = _get_group_in_scope(db, gid, user)
    plan = db.query(models.GroupPlan).filter(models.GroupPlan.group_id == g.id).first()
    if not plan:
        raise HTTPException(400, "Guruh rejaga bog'lanmagan")
    part = "vocab" if body.skill == "vocab" else "grammar"
    out = []
    for sid in body.student_ids:
        # send_from_plan endi {"created", "skipped"} qaytaradi (2026-09-30)
        out += send_from_plan(g.id, FromPlanIn(course=plan.course, lesson_no=body.lesson_no, parts=[part],
                                               due_days=3, student_ids=[int(sid)]), db, user)["created"]
    return {"sent": len(out), "items": out}


# ---------------------------------------------------------------
#  RAHBAR HISOBOTI
# ---------------------------------------------------------------
@router.get("/api/reports/learning")
def learning_report(branch_id: Optional[int] = None, db: Session = Depends(get_db),
                    user=Depends(require_role(*roles.TEACHING_ACCESS))):
    q = scope_to_branch(db.query(models.Group), models.Group, user, branch_id)
    if user.role in TEACHER_APP_ROLES:
        t = _teacher_of_user(db, user)
        q = q.filter(models.Group.teacher_id == (t.id if t else -1))
    groups = q.order_by(models.Group.name).all()
    since = roles.local_today() - timedelta(days=28)
    since_dt = datetime.combine(since, datetime.min.time())
    out, weak_all, material = [], defaultdict(int), defaultdict(lambda: [0.0, 0])
    for g in groups:
        plan = db.query(models.GroupPlan).filter(models.GroupPlan.group_id == g.id).first()
        studs = [s for s in _group_students(db, g.id) if (s.status or "active") in ("active", "trial")]
        finished = db.query(models.LessonRun).filter(models.LessonRun.group_id == g.id,
                                                     models.LessonRun.status == "finished").count()
        lessons = (db.query(models.Lesson).filter(models.Lesson.group_id == g.id, models.Lesson.held == 1)
                   .order_by(models.Lesson.date.desc()).limit(4).all())
        hw_done = hw_total = 0
        for ls in lessons:
            for a in db.query(models.Attendance).filter(models.Attendance.lesson_id == ls.id).all():
                if a.homework is not None:
                    hw_total += 1
                    hw_done += 1 if a.homework in (1, 2) else 0
        asg = db.query(models.Assignment).filter(models.Assignment.group_id == g.id,
                                                 models.Assignment.sent_at >= since_dt).all()
        auto_of = {a.id: a.auto for a in asg}
        subs = (db.query(models.AssignmentSubmission)
                .filter(models.AssignmentSubmission.assignment_id.in_([a.id for a in asg] or [-1])).all())
        by_a = defaultdict(set)
        for s in subs:
            if s.status in ("submitted", "graded"):
                by_a[s.assignment_id].add(s.student_id)
        expected = sum(len(json.loads(a.targets or "[]")) for a in asg)
        done_cnt = sum(len(v) for v in by_a.values())
        pending = sum(1 for s in subs if s.status == "submitted" and not auto_of.get(s.assignment_id, 1))
        ev = _evidence(db, g.id)
        need_help = []
        if plan:
            for st in studs:
                weak = 0
                for no in range(1, plan.next_lesson_no + 1):
                    for sk in ("vocab", "grammar"):
                        r = _best(ev, st.id, no, sk)
                        if r is not None and r < THRESH:
                            weak += 1
                            weak_all[(plan.course, no, sk)] += 1
                if weak >= 2:
                    need_help.append({"student_id": st.id, "name": st.full_name, "weak": weak})
        for s in subs:
            a = next((x for x in asg if x.id == s.assignment_id), None)
            if a and a.auto and s.auto_max:
                m = material[(a.course, a.lesson_no, a.kind)]
                m[0] += s.auto_score / s.auto_max
                m[1] += 1
        out.append({
            "group_id": g.id, "group": g.name, "teacher": (g.teacher.full_name if getattr(g, "teacher", None) else None),
            "students": len(studs),
            "plan": ({"course": plan.course, "next_lesson_no": plan.next_lesson_no,
                      "total": len((_load_course(plan.course) or {"lessons": []})["lessons"]),
                      "carry": json.loads(plan.carry or "[]"), "lessons_run": finished} if plan else None),
            "homework_pct": (round(100 * hw_done / hw_total) if hw_total else None),
            "assignments": {"sent": len(asg), "expected": expected, "done": done_cnt,
                            "done_pct": (round(100 * done_cnt / expected) if expected else None),
                            "pending_checks": pending},
            "need_help": need_help,
        })
    hard_out = []
    for (course, no, sk), n in sorted(weak_all.items(), key=lambda kv: -kv[1])[:8]:
        try:
            title = _lesson(course, no)["title"]
        except HTTPException:
            title = ""
        hard_out.append({"course": course, "lesson_no": no, "skill": sk, "students": n, "title": title})
    mat = sorted(((k, v[0] / v[1], v[1]) for k, v in material.items() if v[1] >= 3), key=lambda x: x[1])[:6]
    return {"since": since.isoformat(), "groups": out, "hard_topics": hard_out,
            "material_weak": [{"course": k[0], "lesson_no": k[1], "kind": k[2], "avg_pct": round(avg * 100), "n": n}
                              for k, avg, n in mat],
            "pending_checks": sum(g["assignments"]["pending_checks"] for g in out)}
