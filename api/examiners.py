"""Auto-extracted from main.py during refactor (split-main). Domain: examiners."""
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

def _exam_out(e: models.Exam, results: list = None) -> dict:
    done = [r for r in (results or []) if not r.absent and r.percent is not None]
    return {
        "id": e.id,
        "group_id": e.group_id,
        "group": e.group.name if e.group else None,
        "teacher": e.group.teacher.full_name
                   if e.group and e.group.teacher else None,
        "branch_id": e.group.branch_id if e.group else None,
        "branch": e.group.branch.name if e.group and e.group.branch else None,
        "kind": e.kind,
        "kind_label": roles.EXAM_KIND_LABELS.get(e.kind, e.kind),
        "unit_no": e.unit_no,
        "title": e.title or examTitleFallback(e),
        "date": e.date.isoformat() if e.date else None,
        "max_score": e.max_score,
        "status": e.status or "draft",
        "status_label": roles.EXAM_STATUS_LABELS.get(e.status or "draft",
                                                     e.status or "draft"),
        "approved_by": e.approved_by,
        "approved_at": e.approved_at.isoformat() if e.approved_at else None,
        "retake_of_id": e.retake_of_id,
        "note": e.note,
        "result_count": len(results or []),
        "avg_percent": round(sum(r.percent for r in done) / len(done), 1)
                       if done else None,
        "absent": sum(1 for r in (results or []) if r.absent),
    }

def examTitleFallback(e: models.Exam) -> str:
    if e.kind == "unit" and e.unit_no:
        return f"Unit {e.unit_no}"
    return roles.EXAM_KIND_LABELS.get(e.kind, e.kind)

@router.get("/api/examiner/exams")
def examiner_exams(
    status: str | None = None,
    branch_id: int | None = None,
    group_id: int | None = None,
    months: int = 6,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.EXAM_VIEW)),
):
    """Imtihon jadvali. Examiner shu yerdan test yaratadi, tasdiqlaydi
    va natijasini kiritadi."""
    since = date.today() - timedelta(days=int(max(1, months) * 30.44))
    q = (db.query(models.Exam).join(models.Group)
         .filter(models.Exam.date >= since))
    allowed = _branch_scope_ids(db, user, branch_id)
    if allowed:
        q = q.filter(models.Group.branch_id.in_(allowed))
    if status:
        q = q.filter(models.Exam.status == status)
    if group_id:
        q = q.filter(models.Exam.group_id == group_id)
    exams = q.order_by(models.Exam.date.desc()).all()

    res = {}
    if exams:
        for r in (db.query(models.ExamResult)
                  .filter(models.ExamResult.exam_id.in_([e.id for e in exams]))
                  .all()):
            res.setdefault(r.exam_id, []).append(r)
    return [_exam_out(e, res.get(e.id, [])) for e in exams]

@router.post("/api/examiner/exams/{exam_id}/approve")
def approve_exam(
    exam_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.EXAM_APPROVE)),
):
    """Testni tasdiqlash. Tasdiqlanmagan testga natija kiritilmaydi -
    shunda o'zboshimchalik bilan qo'yilgan baho bo'lmaydi."""
    e = db.query(models.Exam).get(exam_id)
    if not e:
        raise HTTPException(404, "Imtihon topilmadi")
    if e.status == "approved":
        raise HTTPException(400, "Bu test allaqachon tasdiqlangan")
    e.status = "approved"
    e.approved_by = user.full_name
    e.approved_at = date.today()
    audit.log(db, user, entity="exam", action="update", entity_id=e.id,
              entity_label=e.title or examTitleFallback(e),
              field="status", old_value="draft", new_value="approved",
              commit=True)
    return {"ok": True, "status": e.status}

@router.put("/api/examiner/exams/{exam_id}/status")
def set_exam_status(
    exam_id: int,
    payload: schemas.ExamStatusUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.EXAM_APPROVE)),
):
    e = db.query(models.Exam).get(exam_id)
    if not e:
        raise HTTPException(404, "Imtihon topilmadi")
    if payload.status not in roles.EXAM_STATUS_LABELS:
        raise HTTPException(400, "Noma'lum holat")
    old = e.status
    e.status = payload.status
    if payload.note is not None:
        e.note = payload.note
    audit.log(db, user, entity="exam", action="update", entity_id=e.id,
              entity_label=e.title or examTitleFallback(e), field="status",
              old_value=old, new_value=e.status, commit=True)
    return {"ok": True}

@router.post("/api/examiner/exams/{exam_id}/retake")
def create_retake(
    exam_id: int,
    payload: schemas.RetakeCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.EXAM_ACCESS)),
):
    """Qayta imtihon. Asl imtihonga bog'lanadi, shuning uchun
    "qayta topshirdi va yaxshiladi" degan tarix ko'rinib turadi."""
    src = db.query(models.Exam).get(exam_id)
    if not src:
        raise HTTPException(404, "Imtihon topilmadi")
    e = models.Exam(
        group_id=src.group_id, kind=src.kind, unit_no=src.unit_no,
        title=(src.title or examTitleFallback(src)) + " (qayta)",
        date=payload.date or date.today(),
        max_score=src.max_score, status="approved",
        # Qayta imtihon ASL imtihonning o'tish balli bilan olinadi —
        # aks holda bir xil testning ikki urinishi ikki xil chegarada
        # baholanardi (2026-09-10).
        pass_percent=src.pass_percent,
        approved_by=user.full_name, approved_at=date.today(),
        retake_of_id=src.id, note=payload.note,
        created_by=user.full_name)
    db.add(e); db.commit(); db.refresh(e)
    audit.log(db, user, entity="exam", action="create", entity_id=e.id,
              entity_label=e.title, note=f"Qayta imtihon (asli #{src.id})",
              commit=True)
    return _exam_out(e, [])

@router.get("/api/examiner/analysis")
def examiner_analysis(
    months: int = 6,
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.EXAM_VIEW)),
):
    """Imtihon natijalarining uch kesimda tahlili: ustoz, guruh, filial.
    Pastda standartdan ortda qolgan guruhlar va sertifikatga tavsiya."""
    since = date.today() - timedelta(days=int(max(1, months) * 30.44))
    q = (db.query(models.ExamResult, models.Exam, models.Group)
         .join(models.Exam, models.ExamResult.exam_id == models.Exam.id)
         .join(models.Group, models.Exam.group_id == models.Group.id)
         .filter(models.Exam.date >= since,
                 models.ExamResult.absent == 0,
                 models.ExamResult.percent.isnot(None)))
    allowed = _branch_scope_ids(db, user, branch_id)
    if allowed:
        q = q.filter(models.Group.branch_id.in_(allowed))
    rows = q.all()

    teachers = {t.id: t for t in db.query(models.Teacher).all()}
    branches = {b.id: b for b in db.query(models.Branch).all()}

    def agg(key_fn, label_fn):
        acc = {}
        for r, e, g in rows:
            k = key_fn(g)
            if k is None:
                continue
            d = acc.setdefault(k, {"sum": 0.0, "n": 0, "exams": set(),
                                   "students": set()})
            d["sum"] += r.percent
            d["n"] += 1
            d["exams"].add(e.id)
            d["students"].add(r.student_id)
        out = []
        for k, d in acc.items():
            avg = round(d["sum"] / d["n"], 1)
            band, band_label = ("good", "Standartga mos") \
                if avg >= roles.EXAM_STANDARD_PERCENT else ("behind", "Ortda")
            out.append({
                "key": k, "label": label_fn(k), "avg": avg,
                "results": d["n"], "exams": len(d["exams"]),
                "students": len(d["students"]),
                "band": band, "band_label": band_label,
            })
        out.sort(key=lambda x: -x["avg"])
        return out

    by_teacher = agg(lambda g: g.teacher_id,
                     lambda k: teachers[k].full_name if k in teachers else "—")
    by_group = agg(lambda g: g.id,
                   lambda k: next((g.name for _r, _e, g in rows if g.id == k), "—"))
    by_branch = agg(lambda g: g.branch_id,
                    lambda k: branches[k].name if k in branches else "—")

    behind = [g for g in by_group if g["band"] == "behind"]

    # O'quvchi progressi: birinchi va oxirgi natija farqi
    per_student = {}
    for r, e, g in rows:
        per_student.setdefault(r.student_id, []).append((e.date, r.percent))
    progress = []
    names = {s.id: s for s in db.query(models.Student).all()}
    for sid, lst in per_student.items():
        if len(lst) < 2:
            continue
        lst.sort(key=lambda x: x[0])
        first, last = lst[0][1], lst[-1][1]
        st = names.get(sid)
        progress.append({
            "student_id": sid,
            "full_name": st.full_name if st else "—",
            "group": st.group.name if st and st.group else None,
            "first": round(first, 1), "last": round(last, 1),
            "change": round(last - first, 1),
            "exams": len(lst),
            "avg": round(sum(x[1] for x in lst) / len(lst), 1),
        })
    progress.sort(key=lambda x: x["change"])

    # Sertifikatga tavsiya: o'rtachasi yuqori va kamida 2 ta imtihon
    recommend = [p for p in progress
                 if p["avg"] >= roles.CERTIFICATE_RECOMMEND_PERCENT
                 and p["exams"] >= 2]
    recommend.sort(key=lambda x: -x["avg"])

    # Qayta imtihon tavsiyasi: oxirgi natijasi past
    retake = [{"student_id": sid,
               "full_name": names[sid].full_name if sid in names else "—",
               "group": names[sid].group.name
                        if sid in names and names[sid].group else None,
               "percent": round(sorted(lst, key=lambda x: x[0])[-1][1], 1)}
              for sid, lst in per_student.items()
              if sorted(lst, key=lambda x: x[0])[-1][1] < roles.EXAM_RETAKE_BELOW]
    retake.sort(key=lambda x: x["percent"])

    all_avg = (round(sum(r.percent for r, _e, _g in rows) / len(rows), 1)
               if rows else None)
    return {
        "months": months,
        "standard": roles.EXAM_STANDARD_PERCENT,
        "total_results": len(rows),
        "avg": all_avg,
        "by_teacher": by_teacher,
        "by_group": by_group,
        "by_branch": by_branch,
        "behind": behind,
        "progress": progress,
        "recommend_certificate": recommend[:50],
        "recommend_retake": retake[:50],
    }

@router.post("/api/examiner-adjustments")
def add_examiner_adjustment(payload: schemas.ExaminerAdjustIn,
                            db: Session = Depends(get_db),
                            user=Depends(require_role(
                                *roles.EXAMINER_PENALTY_SET))):
    """Qo'lda ball ayirish (ESLATMA): sabab majburiy."""
    target = db.query(models.User).get(payload.user_id)
    if not target or target.role not in (roles.EXAMINER,
                                         roles.HEAD_EXAMINER):
        raise HTTPException(404, "Examiner topilmadi")
    if not (payload.reason or "").strip():
        raise HTTPException(400, "Sababni yozing — ball sababsiz ayirilmaydi")
    if payload.points <= 0 or payload.points > 500:
        raise HTTPException(400, "Ball 0 dan katta va 500 dan kichik bo'lsin")
    a = models.ExaminerAdjustment(
        user_id=target.id, points=round(payload.points, 2),
        reason=payload.reason.strip(),
        date=payload.date or roles.local_today(),
        created_by=user.full_name)
    db.add(a)
    db.commit()
    audit.log(db, user, entity="examiner_adjustment", action="create",
              entity_id=a.id, entity_label=target.full_name,
              new_value=f"-{a.points} ball", note=a.reason, commit=True)
    return {"ok": True, "id": a.id}

@router.delete("/api/examiner-adjustments/{adj_id}")
def delete_examiner_adjustment(adj_id: int, db: Session = Depends(get_db),
                               user=Depends(require_role(
                                   *roles.EXAMINER_PENALTY_SET))):
    """Xato ayirilgan ballni bekor qilish (2026-09-16) — auditga yoziladi."""
    a = db.query(models.ExaminerAdjustment).get(adj_id)
    if not a:
        raise HTTPException(404, "Jarima topilmadi")
    target = db.query(models.User).get(a.user_id)
    label, pts, reason = (target.full_name if target else "—",
                          a.points, a.reason)
    db.delete(a)
    db.commit()
    audit.log(db, user, entity="examiner_adjustment", action="delete",
              entity_id=adj_id, entity_label=label,
              old_value=f"-{pts} ball", note=reason, commit=True)
    return {"ok": True}

@router.get("/api/examiners/salary")
def examiner_salary_list(year: int | None = None, month: int | None = None,
                         db: Session = Depends(get_db),
                         user=Depends(require_role(
                             *roles.EXAMINER_SALARY_VIEW))):
    """Rahbariyat uchun: barcha examinerlar oyligi bir joyda,
    imtihonlari bilan — jarima ham shu yerdan belgilanadi."""
    today = roles.local_today()
    y, m = year or today.year, month or today.month
    ex_users = db.query(models.User).filter(
        models.User.role.in_((roles.EXAMINER, roles.HEAD_EXAMINER)),
        models.User.is_active == 1).order_by(models.User.full_name).all()
    rows = []
    for u in ex_users:
        d = _examiner_month(db, u.id, y, m)
        d["user_id"] = u.id
        d["name"] = u.full_name
        d["role"] = roles.UZ_LABELS.get(u.role, u.role)
        rows.append(d)
    rows.sort(key=lambda r: -r["salary"])
    return {
        "period": f"{y:04d}-{m:02d}",
        "rows": rows,
        "total": round(sum(r["salary"] for r in rows), 0),
        "min": roles.EXAMINER_PAY_MIN, "max": roles.EXAMINER_PAY_MAX,
        "can_penalize": user.role in tuple(roles.EXAMINER_PENALTY_SET),
    }



@router.get("/api/reports/exams-monthly")
def monthly_exam_report(period: str | None = None, branch_id: int | None = None,
                        db: Session = Depends(get_db),
                        user=Depends(require_role(*roles.EXAM_VIEW))):
    from exam_reports import report
    return report(db, user, period, branch_id)


@router.get("/api/teacher/exam-history")
def own_exam_history(period: str | None = None, db: Session = Depends(get_db),
                     user=Depends(require_role(roles.TEACHER))):
    from exam_reports import report
    return report(db, user, period, own=True)
