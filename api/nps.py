"""NPS so'rovi + imtihon trendi (2026-08-12, Jahongir):

"Ota-ona NPS so'rovi: chorakda bir marta 1 savol ('Tavsiya
qilasizmi? 0-10') - filial va ustoz kesimida sifat o'lchovi.
O'quvchiga ham shu chiqsin platformasida."

"Imtihon natijalari trendi: guruh/ustoz kesimida o'rtacha foizning
oyma-oy o'zgarishi - shuni qosh."
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

import audit
import billing
import models
import roles
import schemas  # noqa: F401
from auth import get_current_user, require_role
from database import get_db
from common import *  # noqa: F401,F403

router = APIRouter()


def _quarter_key(d: date) -> str:
    return f"{d.year}-Q{(d.month - 1) // 3 + 1}"


def _nps_pending(db: Session, student_id: int, who: str) -> bool:
    """Shu chorakda shu rol (student/parent) javob berganmi."""
    qk = _quarter_key(roles.local_today())
    return not (db.query(models.NpsResponse)
                .filter(models.NpsResponse.student_id == student_id,
                        models.NpsResponse.who == who,
                        models.NpsResponse.quarter == qk).count())


@router.get("/api/nps/status")
def nps_status(db: Session = Depends(get_db),
               user=Depends(get_current_user)):
    """O'quvchi/ota-ona uchun: shu chorakda so'rov chiqsinmi."""
    who = None
    s = None
    if user.role == roles.STUDENT:
        who = "student"
        s = _student_of_user(db, user)
    elif user.role == roles.PARENT:
        who = "parent"
        p = (db.query(models.Parent)
             .filter(models.Parent.user_id == user.id).first())
        if p:
            s = db.query(models.Student).get(p.student_id)
    if not who or not s or s.status not in ("active", "frozen", "trial"):
        return {"show": False}
    return {"show": _nps_pending(db, s.id, who),
            "quarter": _quarter_key(roles.local_today()),
            "question": ("Jony Academy'ni do'stlaringizga tavsiya "
                         "qilasizmi? (0 - umuman yo'q, 10 - albatta)")}


# Diqqat: POST/GET /api/nps allaqachon band (gamification'dagi qo'lda
# ustoz reytingi). So'rovnoma javobi shuning uchun /api/nps/answer.
@router.post("/api/nps/answer")
def nps_submit(payload: dict, db: Session = Depends(get_db),
               user=Depends(get_current_user)):
    try:
        score = int(payload.get("score"))
    except Exception:
        raise HTTPException(400, "Ball 0 dan 10 gacha bo'lishi kerak")
    if score < 0 or score > 10:
        raise HTTPException(400, "Ball 0 dan 10 gacha bo'lishi kerak")

    who, s = None, None
    if user.role == roles.STUDENT:
        who = "student"
        s = _student_of_user(db, user)
    elif user.role == roles.PARENT:
        who = "parent"
        p = (db.query(models.Parent)
             .filter(models.Parent.user_id == user.id).first())
        if p:
            s = db.query(models.Student).get(p.student_id)
    if not who or not s:
        raise HTTPException(403, "Bu so'rov o'quvchi/ota-ona uchun")

    qk = _quarter_key(roles.local_today())
    if not _nps_pending(db, s.id, who):
        return {"ok": True, "already": True}

    g = db.query(models.Group).get(s.group_id) if s.group_id else None
    db.add(models.NpsResponse(
        student_id=s.id, who=who, score=score,
        comment=(payload.get("comment") or "").strip()[:500] or None,
        quarter=qk, branch_id=s.branch_id,
        teacher_id=g.teacher_id if g else None))
    db.commit()
    return {"ok": True}


_NPS_VIEW = tuple(dict.fromkeys(
    tuple(roles.FINANCE_ACCESS) + (roles.ACADEMIC_HEAD, roles.HR_MANAGER)))


@router.get("/api/nps/summary")
def nps_summary(quarter: str | None = None,
                branch_id: int | None = None,
                db: Session = Depends(get_db),
                user=Depends(require_role(*_NPS_VIEW))):
    """NPS = tavsiyachilar% (9-10) - tanqidchilar% (0-6)."""
    qk = quarter or _quarter_key(roles.local_today())
    q = db.query(models.NpsResponse).filter(
        models.NpsResponse.quarter == qk)
    if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
        branch_id = user.branch_id
    if branch_id:
        q = q.filter(models.NpsResponse.branch_id == branch_id)
    rows = q.all()

    def _nps(items):
        n = len(items)
        if not n:
            return None
        promo = sum(1 for r in items if r.score >= 9)
        detr = sum(1 for r in items if r.score <= 6)
        return round((promo - detr) / n * 100)

    branches = {b.id: b.name for b in db.query(models.Branch).all()}
    teachers = {t.id: t.full_name for t in db.query(models.Teacher).all()}

    by_branch = {}
    by_teacher = {}
    for r in rows:
        by_branch.setdefault(r.branch_id, []).append(r)
        if r.teacher_id:
            by_teacher.setdefault(r.teacher_id, []).append(r)

    # Mavjud choraklar ro'yxati (tanlash uchun)
    quarters = [x[0] for x in
                db.query(models.NpsResponse.quarter).distinct().all()]
    cur = _quarter_key(roles.local_today())
    if cur not in quarters:
        quarters.append(cur)

    return {
        "quarter": qk,
        "quarters": sorted(quarters, reverse=True),
        "total": len(rows),
        "nps": _nps(rows),
        "avg": (round(sum(r.score for r in rows) / len(rows), 1)
                if rows else None),
        "by_branch": sorted([{
            "branch": branches.get(bid, "—"),
            "count": len(items), "nps": _nps(items),
        } for bid, items in by_branch.items()],
            key=lambda x: -(x["nps"] if x["nps"] is not None else -999)),
        "by_teacher": sorted([{
            "teacher": teachers.get(tid, "—"),
            "count": len(items), "nps": _nps(items),
        } for tid, items in by_teacher.items() if len(items) >= 3],
            key=lambda x: -(x["nps"] if x["nps"] is not None else -999)),
        "comments": [{
            "who": "O'quvchi" if r.who == "student" else "Ota-ona",
            "score": r.score, "comment": r.comment,
        } for r in rows if r.comment][:50],
        "hint": ("NPS = tavsiyachilar (9-10) foizi minus tanqidchilar "
                 "(0-6) foizi. +50 dan yuqori - a'lo, 0 dan past - "
                 "jiddiy signal. Ustoz kesimida kamida 3 javob "
                 "bo'lganda ko'rsatiladi."),
    }


# =====================================================================
#  IMTIHON TRENDI - oyma-oy o'rtacha foiz
# =====================================================================
@router.get("/api/analytics/exam-trend")
def exam_trend(months: int = 12,
               branch_id: int | None = None,
               db: Session = Depends(get_db),
               user=Depends(require_role(*roles.FINANCE_ACCESS))):
    """Guruh/ustoz kesimida o'rtacha imtihon foizining oyma-oy
    o'zgarishi. Faqat hisobga kiradigan (counted) natijalar, retake
    emas - birinchi urinish foizi."""
    months = max(3, min(months or 12, 24))
    today = roles.local_today()
    if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
        branch_id = user.branch_id

    y, m = today.year, today.month
    periods = []
    for _ in range(months):
        periods.append((y, m))
        m -= 1
        if m == 0:
            y, m = y - 1, 12
    periods.reverse()
    start = date(periods[0][0], periods[0][1], 1)

    q = (db.query(models.ExamResult.percent,
                  models.Exam.date,
                  models.Group.teacher_id,
                  models.Group.name)
         .join(models.Exam, models.ExamResult.exam_id == models.Exam.id)
         .join(models.Group, models.Exam.group_id == models.Group.id)
         .filter(models.Exam.date >= start,
                 models.ExamResult.percent.isnot(None),
                 models.ExamResult.absent != 1,
                 (models.ExamResult.counted.is_(None))
                 | (models.ExamResult.counted == 1)))
    if branch_id:
        q = q.filter(models.Group.branch_id == branch_id)
    rows = q.all()

    tnames = {t.id: t.full_name for t in db.query(models.Teacher).all()}

    by_month: dict = {}
    by_teacher_month: dict = {}
    for pct, d, tid, gname in rows:
        key = f"{d.year:04d}-{d.month:02d}"
        by_month.setdefault(key, []).append(pct)
        if tid:
            by_teacher_month.setdefault(tid, {}).setdefault(
                key, []).append(pct)

    trend = []
    for yy, mm in periods:
        key = f"{yy:04d}-{mm:02d}"
        vals = by_month.get(key, [])
        trend.append({
            "period": key,
            "label": f"{roles.UZ_MONTHS[mm - 1][:3]} {yy}",
            "avg": round(sum(vals) / len(vals), 1) if vals else None,
            "count": len(vals),
        })

    # Ustoz kesimi: oxirgi 3 oy vs undan avvalgi 3 oy
    last3 = {f"{y_:04d}-{m_:02d}" for y_, m_ in periods[-3:]}
    prev3 = {f"{y_:04d}-{m_:02d}" for y_, m_ in periods[-6:-3]}
    t_rows = []
    for tid, mp in by_teacher_month.items():
        l_vals = [v for k, vs in mp.items() if k in last3 for v in vs]
        p_vals = [v for k, vs in mp.items() if k in prev3 for v in vs]
        if not l_vals and not p_vals:
            continue
        l_avg = round(sum(l_vals) / len(l_vals), 1) if l_vals else None
        p_avg = round(sum(p_vals) / len(p_vals), 1) if p_vals else None
        t_rows.append({
            "teacher": tnames.get(tid, f"#{tid}"),
            "last3": l_avg, "prev3": p_avg,
            "count3": len(l_vals),
            "delta": (round(l_avg - p_avg, 1)
                      if l_avg is not None and p_avg is not None
                      else None),
            "months": [{
                "period": f"{yy:04d}-{mm:02d}",
                "avg": (round(sum(mp[f"{yy:04d}-{mm:02d}"]) /
                              len(mp[f"{yy:04d}-{mm:02d}"]), 1)
                        if f"{yy:04d}-{mm:02d}" in mp else None),
            } for yy, mm in periods],
        })
    t_rows.sort(key=lambda r: -(r["last3"] if r["last3"] is not None
                                else -999))

    return {
        "months": trend,
        "teachers": t_rows,
        "hint": ("O'rtacha foiz faqat hisobga kiradigan natijalardan "
                 "(retake va imtihon oldidan kelmaganlar kirmaydi). "
                 "O'zgarish: oxirgi 3 oy vs undan avvalgi 3 oy."),
    }
