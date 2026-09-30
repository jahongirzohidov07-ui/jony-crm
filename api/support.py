"""Auto-extracted from main.py during refactor (split-main). Domain: support."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bisect
from datetime import date, datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, FastAPI, HTTPException, Request
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

@router.get("/api/support/assignments")
def support_assignments(
    user_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.SUPPORT_ACCESS)),
):
    q = db.query(models.SupportAssignment)
    # Support teacher faqat O'ZIGA biriktirilganini ko'radi.
    if user.role == roles.SUPPORT_TEACHER:
        q = q.filter(models.SupportAssignment.user_id == user.id)
    elif user_id:
        q = q.filter(models.SupportAssignment.user_id == user_id)
    return [{
        "id": a.id, "user_id": a.user_id,
        "user": a.user.full_name if a.user else None,
        "group_id": a.group_id,
        "group": a.group.name if a.group else None,
        "student_id": a.student_id,
        "student": a.student.full_name if a.student else None,
        "note": a.note,
    } for a in q.all()]

@router.post("/api/support/assignments")
def add_assignment(
    payload: schemas.SupportAssignmentCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.ACADEMIC_ACCESS)),
):
    if not payload.group_id and not payload.student_id:
        raise HTTPException(400, "Guruh yoki o'quvchi tanlang")
    a = models.SupportAssignment(**payload.model_dump(),
                                 created_by=user.full_name)
    db.add(a); db.commit(); db.refresh(a)
    return {"id": a.id}

@router.delete("/api/support/assignments/{aid}")
def delete_assignment(
    aid: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.ACADEMIC_ACCESS)),
):
    a = db.query(models.SupportAssignment).get(aid)
    if not a:
        raise HTTPException(404, "Topilmadi")
    db.delete(a); db.commit()
    return {"ok": True}

# =====================================================================
#  ORQADA QOLGAN O'QUVCHINI SUPPORTGA BIRIKTIRISH (2026-09-23)
#
#  Jahongir: "o'zlashtirishi orqada qolgan o'quvchini ustoz biriktirib
#  bersa yo'qlamani qanday qo'yadi, u o'quvchiga qanaqa pul oladi".
#
#  Qaror: o'quvchi qo'shimcha pul TO'LAMAYDI (orqada qolgan o'quvchi -
#  ketib qolish arafasidagi o'quvchi, undan pul so'rash uni butunlay
#  yo'qotadi). Support esa bekorga ishlamasin: yakka darsda soat ikki
#  barobar ball beradi (roles.SUPPORT_HOURS_W_SMALL).
#
#  Yo'qlama guruhnikidan ALOHIDA yoziladi (support_attendance) -
#  ustoz oyligiga ham, o'quvchi hisobiga ham tegmaydi.
# =====================================================================
# HR ham biriktira oladi (2026-09-23, Jahongir: "hr qo'sha olsin").
# HR o'quvchi kartasini ochmaydi - uning uchun HR bo'limida alohida
# ro'yxat bor, shuning uchun o'quvchining to'lovi, davomati va
# imtihonlari HR ga ochilmaydi.
SOLO_ASSIGN = list(dict.fromkeys(
    list(roles.ACADEMIC_ACCESS) + [roles.TEACHER, roles.HR_MANAGER]))
SOLO_VIEW = list(dict.fromkeys(
    list(roles.TEACHING_ACCESS) + list(SOLO_ASSIGN)))


def _solo_can_touch(db: Session, user, student) -> bool:
    """Ustoz faqat O'Z guruhidagi o'quvchini biriktira oladi."""
    if user.role != roles.TEACHER:
        return True
    g = (db.query(models.Group).get(student.group_id)
         if student.group_id else None)
    t = _teacher_of_user(db, user)
    return bool(g and t and g.teacher_id == t.id)


def _solo_out(db: Session, a) -> dict:
    u = db.query(models.User).get(a.user_id) if a.user_id else None
    return {
        "id": a.id, "user_id": a.user_id,
        "support": u.full_name if u else None,
        "days": a.days, "start": a.start, "end": a.end,
        "note": a.note, "created_by": a.created_by,
    }


@router.get("/api/students/{sid}/support")
def student_support_get(sid: int, db: Session = Depends(get_db),
                        user=Depends(require_role(*SOLO_VIEW))):
    """O'quvchiga yakka biriktirilgan support(lar)."""
    s = _get_student_in_scope(db, sid, user)
    rows = (db.query(models.SupportAssignment)
            .filter(models.SupportAssignment.student_id == s.id).all())
    sups = [{"id": u.id, "name": u.full_name}
            for u in db.query(models.User)
            .filter(_support_cond(),
                    models.User.is_active == 1)
            .order_by(models.User.full_name).all()]
    return {
        "rows": [_solo_out(db, a) for a in rows],
        "supports": sups,
        "can_edit": (user.role in tuple(SOLO_ASSIGN)
                     and _solo_can_touch(db, user, s)),
        "hint": ("Yakka dars o'quvchiga qo'shimcha pul solmaydi. "
                 "Support belgilangan kunda alohida shug'ullanadi, "
                 "yo'qlamasi guruh yo'qlamasidan alohida yuritiladi."),
    }


@router.post("/api/students/{sid}/support")
def student_support_add(sid: int, payload: dict = Body(...),
                        db: Session = Depends(get_db),
                        user=Depends(require_role(*SOLO_ASSIGN))):
    """Ustoz orqada qolgan o'quvchisini supportga biriktiradi."""
    s = _get_student_in_scope(db, sid, user)
    if not _solo_can_touch(db, user, s):
        raise HTTPException(403, "Faqat o'z guruhingizdagi o'quvchini "
                                 "biriktira olasiz")
    if s.status != "active":
        raise HTTPException(400, "Faqat faol o'quvchi biriktiriladi")
    u = db.query(models.User).get(payload.get("user_id") or 0)
    if not u or not _is_support_user(db, u) or not u.is_active:
        raise HTTPException(404, "Support teacher topilmadi")
    if not (payload.get("note") or "").strip():
        raise HTTPException(400, "Sababini yozing — nega orqada qolgan")
    days = (payload.get("days") or "").strip()
    start = (payload.get("start") or "").strip()
    end = (payload.get("end") or "").strip()
    if start and end and roles.hhmm_minutes(start) is not None \
            and roles.hhmm_minutes(end) is not None \
            and roles.hhmm_minutes(end) <= roles.hhmm_minutes(start):
        raise HTTPException(400, "Tugash vaqti boshlanishdan keyin bo'lsin")
    dup = (db.query(models.SupportAssignment)
           .filter(models.SupportAssignment.student_id == s.id,
                   models.SupportAssignment.user_id == u.id).first())
    if dup:
        raise HTTPException(400, "Bu o'quvchi shu supportga allaqachon "
                                 "biriktirilgan")
    a = models.SupportAssignment(
        user_id=u.id, student_id=s.id, days=days or None,
        start=start or None, end=end or None,
        note=payload.get("note"), created_by=user.full_name)
    db.add(a)
    db.commit()
    db.refresh(a)
    audit.log(db, user, entity="student", action="update", entity_id=s.id,
              entity_label=s.full_name, field="Yakka support",
              new_value=u.full_name, note=payload.get("note"),
              branch_id=s.branch_id, commit=True)
    return _solo_out(db, a)


@router.delete("/api/students/{sid}/support/{aid}")
def student_support_del(sid: int, aid: int, db: Session = Depends(get_db),
                        user=Depends(require_role(*SOLO_ASSIGN))):
    s = _get_student_in_scope(db, sid, user)
    if not _solo_can_touch(db, user, s):
        raise HTTPException(403, "Faqat o'z guruhingizdagi o'quvchi")
    a = db.query(models.SupportAssignment).get(aid)
    if not a or a.student_id != s.id:
        raise HTTPException(404, "Biriktirish topilmadi")
    db.delete(a)
    db.commit()
    audit.log(db, user, entity="student", action="update", entity_id=s.id,
              entity_label=s.full_name, field="Yakka support",
              old_value="olib tashlandi", branch_id=s.branch_id,
              commit=True)
    return {"ok": True}


@router.get("/api/support/solo")
def solo_list(db: Session = Depends(get_db),
              user=Depends(require_role(*SOLO_ASSIGN))):
    """Barcha yakka biriktirmalar — HR bo'limidagi ro'yxat uchun."""
    today = roles.local_today()
    start, end = billing.month_bounds(today.year, today.month)
    rows = (db.query(models.SupportAssignment)
            .filter(models.SupportAssignment.student_id.isnot(None)).all())
    out = []
    for a in rows:
        st = db.query(models.Student).get(a.student_id)
        if not st or not _in_user_branches(db, user, st.branch_id):
            continue
        g = db.query(models.Group).get(st.group_id) if st.group_id else None
        u = db.query(models.User).get(a.user_id) if a.user_id else None
        done = (db.query(models.SupportSession)
                .filter(models.SupportSession.student_id == st.id,
                        models.SupportSession.date >= start,
                        models.SupportSession.date <= end).count())
        out.append({
            "id": a.id, "student_id": st.id, "student": st.full_name,
            "status": st.status,
            "group": g.name if g else None,
            "user_id": a.user_id, "support": u.full_name if u else None,
            "days": a.days, "start": a.start, "end": a.end,
            "note": a.note, "created_by": a.created_by,
            "done": done,
        })
    out.sort(key=lambda r: r["student"])
    sups = [{"id": u.id, "name": u.full_name}
            for u in db.query(models.User)
            .filter(_support_cond(),
                    models.User.is_active == 1)
            .order_by(models.User.full_name).all()]
    return {
        "rows": out, "supports": sups,
        "period": f"{today.year:04d}-{today.month:02d}",
        "hint": ("Yakka dars o'quvchiga pulsiz. Supportga esa bu dars "
                 "3 ta o'quvchilik darsdek hisoblanadi."),
    }


@router.get("/api/support/solo/students")
def solo_student_search(q: str = "", db: Session = Depends(get_db),
                        user=Depends(require_role(*SOLO_ASSIGN))):
    """O'quvchini ism bo'yicha qidirish — faqat biriktirish uchun.

    Bu yerda o'quvchi haqida ism, guruh va filialdan boshqa hech narsa
    berilmaydi: HR ga o'quvchining to'lovi va boshqa ma'lumoti kerak
    emas."""
    term = (q or "").strip()
    if len(term) < 2:
        return {"rows": []}
    qq = (db.query(models.Student)
          .filter(models.Student.status == "active",
                  models.Student.full_name.ilike(f"%{term}%")))
    rows = []
    for s in qq.order_by(models.Student.full_name).limit(40).all():
        if not _in_user_branches(db, user, s.branch_id):
            continue
        g = db.query(models.Group).get(s.group_id) if s.group_id else None
        rows.append({"id": s.id, "name": s.full_name,
                     "group": g.name if g else None})
        if len(rows) >= 20:
            break
    return {"rows": rows}


def _student_attendance_stats(db: Session, sid: int, since: date) -> dict:
    rows = (db.query(models.Attendance, models.Lesson)
            .join(models.Lesson, models.Attendance.lesson_id == models.Lesson.id)
            .filter(models.Attendance.student_id == sid,
                    models.Lesson.date >= since).all())
    marked = len(rows)
    present = sum(1 for a, _l in rows if a.present)
    return {
        "marked": marked, "present": present, "absent": marked - present,
        "percent": round(present / marked * 100, 1) if marked else None,
    }

@router.get("/api/support/teachers")
def support_teacher_list(db: Session = Depends(get_db),
                         user=Depends(require_role(*roles.SUPPORT_ACCESS))):
    """Support teacherlar ro'yxati (faqat id + ism).

    NEGA ALOHIDA YO'L (2026-08-10, Jahongir: "support teacherlar
    ro'yxati o'quv bo'limi rahbarida ko'rinmayabdi"): sahifa ilgari
    GET /api/users ni chaqirardi, u esa STAFF_VIEWERS bilan
    himoyalangan (asoschi, filial rahbari, HR, moliya direktori).
    O'quv bo'limi rahbari va support boshlig'i u ro'yxatda YO'Q,
    shuning uchun 403 olib, tanlagich BO'SH qolardi.

    Butun xodimlar ro'yxatini ochib qo'yish noto'g'ri bo'lardi (u
    yerda oylik ham bor), shuning uchun bu yo'l FAQAT support
    teacherlarning ismini qaytaradi — boshqa hech narsa."""
    q = db.query(models.User).filter(
        _support_cond(),
        models.User.is_active == 1)
    q = scope_to_branch(q, models.User, user)
    rows = q.order_by(models.User.full_name).all()
    return [{"id": u.id, "full_name": u.full_name,
             "branch_id": u.branch_id} for u in rows]


@router.get("/api/support/panel")
def support_panel(
    user_id: int | None = None,
    months: int = 3,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.SUPPORT_ACCESS)),
):
    """Support teacher paneli: biriktirilgan guruhlar va o'quvchilar,
    davomat va uy vazifasi muammolari, ishlash rejasi va natija."""
    since = date.today() - timedelta(days=int(max(1, months) * 30.44))

    aq = db.query(models.SupportAssignment)
    target_id = user.id if user.role == roles.SUPPORT_TEACHER else (user_id or None)
    if target_id:
        aq = aq.filter(models.SupportAssignment.user_id == target_id)
    assigns = aq.all()

    group_ids = {a.group_id for a in assigns if a.group_id}
    direct_ids = {a.student_id for a in assigns if a.student_id}

    sq = db.query(models.Student).filter(
        models.Student.status.in_(["active", "trial"]))
    if group_ids or direct_ids:
        sq = sq.filter(
            (models.Student.group_id.in_(group_ids or [-1]))
            | (models.Student.id.in_(direct_ids or [-1])))
    elif user.role == roles.SUPPORT_TEACHER:
        sq = sq.filter(models.Student.id == -1)   # hech narsa biriktirilmagan
    else:
        sq = scope_to_branch(sq, models.Student, user)
    students = sq.all()

    # Uy vazifasi muammosi - qo'lda qo'yilgan risk signali
    hw = {}
    if students:
        for f in (db.query(models.RiskFlag)
                  .filter(models.RiskFlag.student_id.in_([s.id for s in students]),
                          models.RiskFlag.signal == "no_homework",
                          models.RiskFlag.active == 1).all()):
            hw[f.student_id] = f.note or "belgilangan"

    plans = {}
    if students:
        for p in (db.query(models.SupportPlan)
                  .filter(models.SupportPlan.student_id.in_(
                      [s.id for s in students])).all()):
            plans.setdefault(p.student_id, []).append(p)

    rows, att_problem, hw_problem = [], 0, 0
    for s in students:
        att = _student_attendance_stats(db, s.id, since)
        bad_att = (att["percent"] is not None
                   and att["percent"] < roles.SUPPORT_ATTENDANCE_THRESHOLD)
        bad_hw = s.id in hw
        if bad_att:
            att_problem += 1
        if bad_hw:
            hw_problem += 1
        open_plans = [p for p in plans.get(s.id, []) if p.status == "open"]
        rows.append({
            "student_id": s.id, "public_id": s.public_id,
            "full_name": s.full_name, "status": s.status,
            "group_id": s.group_id,
            "group": s.group.name if s.group else None,
            "phone": s.phone, "parent_phone": s.parent_phone,
            "attendance": att,
            "attendance_problem": bad_att,
            "homework_problem": bad_hw,
            "homework_note": hw.get(s.id),
            "open_plans": [{"id": p.id, "issue": p.issue,
                            "issue_label": roles.SUPPORT_ISSUE_LABELS.get(
                                p.issue, p.issue),
                            "plan": p.plan,
                            "due_date": p.due_date.isoformat()
                                        if p.due_date else None}
                           for p in open_plans],
        })
    # Muammoliligi bo'yicha tartib: eng past davomat yuqorida
    rows.sort(key=lambda r: (r["attendance"]["percent"] is None,
                             r["attendance"]["percent"] or 0))

    # Retention natijasi: biriktirilgan o'quvchilardan qanchasi qoldi
    all_ever = list(students)
    if group_ids:
        all_ever = (db.query(models.Student)
                    .filter(models.Student.group_id.in_(group_ids)).all())
    left = [s for s in all_ever if s.status == "archived"]
    stayed = [s for s in all_ever if s.status in ("active", "trial")]

    done_plans = sum(1 for lst in plans.values()
                     for p in lst if p.status == "done")
    total_plans = sum(len(lst) for lst in plans.values())

    return {
        "user_id": target_id,
        "groups": [{"id": g.id, "name": g.name,
                    "teacher": g.teacher.full_name if g.teacher else None,
                    "students": sum(1 for s in students if s.group_id == g.id)}
                   for g in db.query(models.Group)
                   .filter(models.Group.id.in_(group_ids or [-1])).all()],
        "students": rows,
        "summary": {
            "students": len(rows),
            "attendance_problem": att_problem,
            "homework_problem": hw_problem,
            "threshold": roles.SUPPORT_ATTENDANCE_THRESHOLD,
            "open_plans": sum(len(r["open_plans"]) for r in rows),
            "done_plans": done_plans,
            "plan_success": round(done_plans / total_plans * 100, 1)
                            if total_plans else None,
            "retention": round(len(stayed) / len(all_ever) * 100, 1)
                         if all_ever else None,
            "stayed": len(stayed), "left": len(left),
        },
    }

@router.get("/api/support/plans")
def list_plans(
    student_id: int | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.SUPPORT_ACCESS)),
):
    q = db.query(models.SupportPlan)
    if student_id:
        q = q.filter(models.SupportPlan.student_id == student_id)
    if status:
        q = q.filter(models.SupportPlan.status == status)
    if user.role == roles.SUPPORT_TEACHER:
        q = q.filter(models.SupportPlan.user_id == user.id)
    today = date.today()
    return [{
        "id": p.id, "student_id": p.student_id,
        "student": p.student.full_name if p.student else None,
        "user": p.user.full_name if p.user else None,
        "issue": p.issue,
        "issue_label": roles.SUPPORT_ISSUE_LABELS.get(p.issue, p.issue),
        "plan": p.plan,
        "due_date": p.due_date.isoformat() if p.due_date else None,
        "overdue": bool(p.due_date and p.status == "open" and p.due_date < today),
        "status": p.status, "result": p.result,
        "created_at": p.created_at.isoformat() if p.created_at else None,
    } for p in q.order_by(models.SupportPlan.due_date).all()]

@router.post("/api/support/plans")
def create_plan(
    payload: schemas.SupportPlanCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.SUPPORT_ACCESS)),
):
    data = payload.model_dump()
    data["user_id"] = data.get("user_id") or user.id
    p = models.SupportPlan(**data, created_by=user.full_name)
    db.add(p); db.commit(); db.refresh(p)
    audit.log(db, user, entity="student", action="update",
              entity_id=p.student_id, field="support_plan",
              new_value=p.plan[:80], commit=True)
    return {"id": p.id}

@router.put("/api/support/plans/{pid}")
def update_plan(
    pid: int,
    payload: schemas.SupportPlanUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.SUPPORT_ACCESS)),
):
    p = db.query(models.SupportPlan).get(pid)
    if not p:
        raise HTTPException(404, "Reja topilmadi")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(p, k, v)
    p.done_at = date.today() if p.status in ("done", "failed") else None
    db.commit()
    return {"ok": True}

@router.delete("/api/support/plans/{pid}")
def delete_plan(
    pid: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.ACADEMIC_ACCESS)),
):
    p = db.query(models.SupportPlan).get(pid)
    if not p:
        raise HTTPException(404, "Reja topilmadi")
    db.delete(p); db.commit()
    return {"ok": True}

def _range_overlap(a1, a2, b1, b2) -> bool:
    return a1 < b2 and b1 < a2

_WD_UZ = {"mon": "Du", "tue": "Se", "wed": "Chor", "thu": "Pay",
          "fri": "Ju", "sat": "Shan", "sun": "Yak"}

def _days_uz(days: str) -> str:
    return ", ".join(_WD_UZ.get(d, d)
                     for d in (days or "").split(",") if d)

def _support_conflicts(db: Session, teacher_id: int,
                       groups: list) -> list:
    """Yangi biriktirilayotgan guruhlar supportning band vaqtlari yoki
    bir-birlari bilan to'qnashsa — ro'yxat qaytaradi."""
    msgs = []
    busy = (db.query(models.SupportBusy)
            .filter(models.SupportBusy.teacher_id == teacher_id).all())

    def parsed(g):
        if not g.lesson_time or "-" not in (g.lesson_time or ""):
            return None
        s, e = g.lesson_time.split("-", 1)
        s, e = _time_to_min(s), _time_to_min(e)
        if s is None or e is None:
            return None
        days = set((g.lesson_days or "").split(","))
        return s, e, days

    infos = [(g, parsed(g)) for g in groups]
    # 1) band vaqtlar bilan
    for g, p in infos:
        if not p:
            continue
        s, e, days = p
        for b in busy:
            bs, be = _time_to_min(b.start), _time_to_min(b.end)
            if bs is None or be is None:
                continue
            bdays = set((b.days or "").split(","))
            if days & bdays and _range_overlap(s, e, bs, be):
                msgs.append(
                    f"\"{g.name}\" ({_days_uz(g.lesson_days)} "
                    f"{g.lesson_time}) — support bu vaqtni BAND deb "
                    f"belgilagan: {_days_uz(b.days)} {b.start}-{b.end}"
                    + (f" ({b.note})" if b.note else ""))
    # 2) guruhlar bir-biri bilan
    for i in range(len(infos)):
        for j in range(i + 1, len(infos)):
            g1, p1 = infos[i]
            g2, p2 = infos[j]
            if not p1 or not p2:
                continue
            if (p1[2] & p2[2]) and _range_overlap(p1[0], p1[1],
                                                  p2[0], p2[1]):
                msgs.append(
                    f"\"{g1.name}\" va \"{g2.name}\" darslari bir "
                    f"vaqtga to'g'ri keladi ({g1.lesson_time})")
    return msgs

@router.get("/api/support-teachers/salaries")
def support_teacher_salaries(year: int | None = None,
                             month: int | None = None,
                             db: Session = Depends(get_db),
                             user=Depends(require_role(
                                 *roles.FULL_ACCESS, roles.ACADEMIC_HEAD,
                                 roles.HEAD_SUPPORT, roles.HR_MANAGER,
                                 roles.FINANCE_DIRECTOR))):
    """Barcha support teacherlarning shu oy oyligi — ro'yxatda ko'rsatish
    uchun. Formulasiz, faqat yakuniy summa va seans soni."""
    today = roles.local_today()
    y, m = year or today.year, month or today.month
    _ensure_support_cards(db)
    q = (db.query(models.Teacher)
         .join(models.User, models.User.id == models.Teacher.user_id)
         .filter(_support_cond()))
    q = scope_to_branch(q, models.Teacher, user)
    rows = []
    for t in q.all():
        out = _support_month(db, t.id, y, m)
        rows.append({
            "teacher_id": t.id,
            "salary": out.get("salary", 0),
            "session_count": out.get("session_count", 0),
            "hours": out.get("hours", 0),
        })
    return {"period": f"{y:04d}-{m:02d}", "rows": rows}

@router.get("/api/support/salary")
def support_salary_list(year: int | None = None, month: int | None = None,
                        db: Session = Depends(get_db),
                        user=Depends(require_role(
                            *roles.SALARY_VIEW_ALL, roles.ACADEMIC_HEAD))):
    """Rahbariyat uchun: barcha support teacherlar oyligi bir joyda."""
    today = roles.local_today()
    y, m = year or today.year, month or today.month
    su_users = db.query(models.User).filter(
        _support_cond(),
        models.User.is_active == 1).all()
    rows = []
    for u in su_users:
        t = _teacher_of_user(db, u)
        if not t:
            continue
        d = _support_month(db, t.id, y, m)
        d.pop("sessions", None)
        d["teacher_id"] = t.id
        d["name"] = u.full_name
        rows.append(d)
    rows.sort(key=lambda r: -r["salary"])
    return {
        "period": f"{y:04d}-{m:02d}",
        "rows": rows,
        "total": round(sum(r["salary"] for r in rows), 0),
        "min": roles.SUPPORT_PAY_MIN, "max": roles.SUPPORT_PAY_MAX,
        "hint": ("Oylik seanslardan avtomat: (soat x 0.30 + o'quvchi "
                 "x 0.20 + test koef x 0.50 − jarima ballari) x 10 000, "
                 "chegara 400 000 — 1 500 000."),
        "can_penalize": user.role in tuple(roles.SUPPORT_PENALTY_SET),
    }

@router.post("/api/support-adjustments")
def add_support_adjustment(payload: schemas.SupportAdjustIn,
                           db: Session = Depends(get_db),
                           user=Depends(require_role(
                               *roles.SUPPORT_PENALTY_SET))):
    """Support teacherdan jarima ball ayirish (2026-09-16): sabab majburiy."""
    target = db.query(models.User).get(payload.user_id)
    if not target or not _is_support_user(db, target):
        raise HTTPException(404, "Support teacher topilmadi")
    if not (payload.reason or "").strip():
        raise HTTPException(400, "Sababni yozing — ball sababsiz ayirilmaydi")
    if payload.points <= 0 or payload.points > 500:
        raise HTTPException(400, "Ball 0 dan katta va 500 dan kichik bo'lsin")
    d = payload.date or roles.local_today()
    if d > roles.local_today():
        raise HTTPException(400, "Kelajak sanaga jarima qo'yib bo'lmaydi")
    a = models.SupportAdjustment(
        user_id=target.id, points=round(payload.points, 2),
        reason=payload.reason.strip(), date=d,
        created_by=user.full_name)
    db.add(a)
    db.commit()
    audit.log(db, user, entity="support_adjustment", action="create",
              entity_id=a.id, entity_label=target.full_name,
              branch_id=target.branch_id,
              new_value=f"-{a.points} ball", note=a.reason, commit=True)
    return {"ok": True, "id": a.id}

@router.delete("/api/support-adjustments/{adj_id}")
def delete_support_adjustment(adj_id: int, db: Session = Depends(get_db),
                              user=Depends(require_role(
                                  *roles.SUPPORT_PENALTY_SET))):
    """Xato qo'yilgan jarimani bekor qilish — auditga yoziladi."""
    a = db.query(models.SupportAdjustment).get(adj_id)
    if not a:
        raise HTTPException(404, "Jarima topilmadi")
    target = db.query(models.User).get(a.user_id)
    label, pts, reason = (target.full_name if target else "—",
                          a.points, a.reason)
    db.delete(a)
    db.commit()
    audit.log(db, user, entity="support_adjustment", action="delete",
              entity_id=adj_id, entity_label=label,
              branch_id=target.branch_id if target else None,
              old_value=f"-{pts} ball", note=reason, commit=True)
    return {"ok": True}

@router.get("/api/support-teachers/{teacher_id}/groups")
def support_teacher_groups(teacher_id: int, db: Session = Depends(get_db),
                           user=Depends(require_role(
                               *roles.SUPPORT_ASSIGN))):
    t = db.query(models.Teacher).get(teacher_id)
    if not t or not t.user_id:
        raise HTTPException(404, "Support teacher yoki akkaunti topilmadi")
    gids = {a.group_id for a in db.query(models.SupportAssignment)
            .filter(models.SupportAssignment.user_id == t.user_id,
                    models.SupportAssignment.group_id.isnot(None)).all()}
    gq = db.query(models.Group)
    if t.branch_id:
        gq = gq.filter(models.Group.branch_id == t.branch_id)
    return {"assigned": sorted(gids),
            "groups": [{"id": g.id, "name": g.name}
                       for g in gq.order_by(models.Group.name).all()]}

@router.put("/api/support-teachers/{teacher_id}/groups")
def set_support_teacher_groups(teacher_id: int,
                               payload: schemas.SupportGroupsIn,
                               force: bool = False,
                               db: Session = Depends(get_db),
                               user=Depends(require_role(
                                   *roles.SUPPORT_ASSIGN))):
    """Support teacherni guruhlarga biriktirish — jadvali va
    o'quvchilari shundan chiqadi.

    Supportning O'ZI belgilagan band vaqtiga yoki bir-biriga to'qnash
    guruhlar tanlansa — 409 ogohlantirish qaytadi (force bilan
    o'tkazib yuborish mumkin). Yangi biriktirilgan har bir guruh uchun
    supportga "sizga guruh biriktirildi" xabari tushadi."""
    t = db.query(models.Teacher).get(teacher_id)
    if not t or not t.user_id:
        raise HTTPException(404, "Support teacher yoki akkaunti topilmadi")

    new_ids = {gid for gid in set(payload.group_ids)
               if db.query(models.Group).get(gid)}
    groups = (db.query(models.Group)
              .filter(models.Group.id.in_(new_ids or [-1])).all())

    # TO'QNASHUV: band vaqtlar va bir-biri bilan
    if not force:
        msgs = _support_conflicts(db, t.id, groups)
        if msgs:
            raise HTTPException(409, "DIQQAT — to'qnashuv bor:\n"
                                + "\n".join(f"• {m}" for m in msgs))

    old_ids = {a.group_id for a in
               db.query(models.SupportAssignment)
               .filter(models.SupportAssignment.user_id == t.user_id,
                       models.SupportAssignment.group_id.isnot(None))
               .all()}
    db.query(models.SupportAssignment).filter(
        models.SupportAssignment.user_id == t.user_id,
        models.SupportAssignment.group_id.isnot(None)).delete()
    for gid in new_ids:
        db.add(models.SupportAssignment(
            user_id=t.user_id, group_id=gid,
            created_by=user.full_name))
    db.commit()

    # XABAR: yangi qo'shilgan guruhlar haqida supportning o'ziga
    added = new_ids - old_ids
    for g in groups:
        if g.id not in added:
            continue
        _hr_task_for(
            db, t.user_id,
            title=(f"Yangi guruh biriktirildi: {g.name} "
                   f"({date.today().isoformat()})"),
            body=(f"Sizga \"{g.name}\" guruhi biriktirildi: "
                  f"{_days_uz(g.lesson_days)} kunlari, "
                  f"{g.lesson_time or 'vaqti belgilanmagan'}. "
                  f"Biriktirdi: {user.full_name}"),
            branch_id=g.branch_id, days=1)
    db.commit()

    audit.log(db, user, entity="support_assignment", action="set",
              entity_id=t.id, entity_label=t.full_name,
              new_value=f"{len(new_ids)} ta guruh",
              note=("force" if force else None),
              commit=True)
    return {"ok": True, "added": len(added)}

