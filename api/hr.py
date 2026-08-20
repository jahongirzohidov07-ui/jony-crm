"""Auto-extracted from main.py during refactor (split-main). Domain: hr."""
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

@router.get("/api/staff/{user_id}/onboarding")
def get_onboarding(
    user_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.HR_ACCESS)),
):
    emp = db.query(models.User).get(user_id)
    if not emp:
        raise HTTPException(404, "Xodim topilmadi")
    rows = _onboarding_rows(db, user_id)
    done = sum(1 for r in rows if r["done"])
    return {
        "user_id": user_id,
        "full_name": emp.full_name,
        "rows": rows,
        "done": done,
        "total": len(rows),
        "percent": round(done / len(rows) * 100) if rows else 0,
        "complete": done == len(rows),
    }

@router.post("/api/staff/{user_id}/onboarding")
def set_onboarding(
    user_id: int,
    payload: schemas.OnboardingUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.HR_ACCESS)),
):
    emp = db.query(models.User).get(user_id)
    if not emp:
        raise HTTPException(404, "Xodim topilmadi")
    # Qadam ro'yxati endi QO'LDA boshqariladi (2026-08-20, Jahongir:
    # "hamma xodimga xar xilda onboarding") - shablon jadvalidagi
    # kalitlar ham qabul qilinadi, standart ro'yxat ham.
    _valid = set(roles.ONBOARDING_KEYS)
    try:
        _OT = getattr(models, "OnboardingTemplate", None)
        if _OT is not None:
            _valid |= {t.key for t in db.query(_OT).all()}
    except Exception:
        pass
    if payload.step not in _valid:
        raise HTTPException(400, "Noto'g'ri qadam")
    row = (db.query(models.OnboardingStep)
           .filter(models.OnboardingStep.user_id == user_id,
                   models.OnboardingStep.step == payload.step).first())
    if not row:
        row = models.OnboardingStep(user_id=user_id, step=payload.step)
        db.add(row)
    row.done = 1 if payload.done else 0
    row.done_at = datetime.utcnow() if payload.done else None
    row.done_by = user.full_name if payload.done else None
    if payload.note is not None:
        row.note = payload.note
    db.commit()
    return get_onboarding(user_id, db, user)

@router.get("/api/staff/{user_id}/events")
def staff_events(
    user_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.HR_ACCESS)),
):
    rows = (db.query(models.StaffEvent)
            .filter(models.StaffEvent.user_id == user_id)
            .order_by(models.StaffEvent.happened_on.desc()).all())
    return {
        "rows": [{
            "id": e.id, "kind": e.kind,
            "kind_label": roles.STAFF_EVENT_LABELS.get(e.kind, e.kind),
            "tone": roles.STAFF_EVENT_TONE.get(e.kind, "neutral"),
            "date": e.happened_on.isoformat() if e.happened_on else None,
            "end_date": e.end_date.isoformat() if e.end_date else None,
            "title": e.title, "note": e.note,
            "score": e.score, "amount": e.amount, "minutes": e.minutes,
            "by": e.created_by,
        } for e in rows],
        "kinds": [{"key": k, "label": lbl, "tone": t}
                  for k, lbl, t in roles.STAFF_EVENTS],
    }

@router.post("/api/staff/{user_id}/events")
def add_staff_event(
    user_id: int,
    payload: schemas.StaffEventCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.HR_ACCESS)),
):
    emp = db.query(models.User).get(user_id)
    if not emp:
        raise HTTPException(404, "Xodim topilmadi")
    if payload.kind not in roles.STAFF_EVENT_LABELS:
        raise HTTPException(400, "Noto'g'ri voqea turi")
    e = models.StaffEvent(
        user_id=user_id, kind=payload.kind,
        happened_on=payload.date or date.today(),
        end_date=payload.end_date, title=payload.title, note=payload.note,
        score=payload.score, amount=payload.amount, minutes=payload.minutes,
        created_by=user.full_name)
    db.add(e); db.commit(); db.refresh(e)
    audit.log(db, user, entity="user", action="update", entity_id=user_id,
              entity_label=emp.full_name, branch_id=emp.branch_id,
              field=roles.STAFF_EVENT_LABELS[payload.kind],
              new_value=payload.title or payload.note or "")
    db.commit()
    return {"id": e.id}

@router.delete("/api/staff/events/{event_id}")
def delete_staff_event(
    event_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.HR_ACCESS)),
):
    e = db.query(models.StaffEvent).get(event_id)
    if not e:
        raise HTTPException(404, "Topilmadi")
    db.delete(e); db.commit()
    return {"ok": True}

@router.get("/api/staff/{user_id}/card")
def staff_card(
    user_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Xodim kartasi. Maosh faqat SALARY_VIEW_ALL huquqi borlarga yoki
    odamning o'ziga ko'rinadi."""
    emp = db.query(models.User).get(user_id)
    if not emp:
        raise HTTPException(404, "Xodim topilmadi")
    if (user.role not in tuple(roles.HR_ACCESS)
            and user.role not in tuple(roles.SALARY_VIEW_ALL)
            and user.id != user_id):
        raise HTTPException(403, "Bu kartani ko'rishga ruxsatingiz yo'q")

    show_salary = (user.role in tuple(roles.SALARY_VIEW_ALL)
                   or user.id == user_id)

    events = (db.query(models.StaffEvent)
              .filter(models.StaffEvent.user_id == user_id).all())
    by_kind = {}
    for e in events:
        by_kind.setdefault(e.kind, []).append(e)

    def count(k):
        return len(by_kind.get(k, []))

    # Ta'til kunlari
    vac_days = 0
    for e in by_kind.get("vacation", []):
        if e.happened_on:
            end = e.end_date or e.happened_on
            vac_days += (end - e.happened_on).days + 1

    late_minutes = sum(e.minutes or 0 for e in by_kind.get("late", []))
    reviews = [e for e in by_kind.get("review", []) if e.score is not None]
    avg_review = round(sum(e.score for e in reviews) / len(reviews), 1) if reviews else None
    bonus_total = sum(e.amount or 0 for e in by_kind.get("bonus", []))

    # Ustoz bo'lsa - guruhlari va o'quvchilari
    teacher = (db.query(models.Teacher)
               .filter(models.Teacher.full_name == emp.full_name).first())
    groups, students = [], 0
    if teacher:
        gs = db.query(models.Group).filter(
            models.Group.teacher_id == teacher.id).all()
        for g in gs:
            n = db.query(models.Student).filter(
                models.Student.group_id == g.id,
                models.Student.status == "active").count()
            students += n
            groups.append({"id": g.id, "name": g.name, "students": n})

    manager = db.query(models.User).get(emp.manager_id) if emp.manager_id else None
    onb = _onboarding_rows(db, user_id)
    onb_done = sum(1 for r in onb if r["done"])

    return {
        "id": emp.id,
        "public_id": emp.public_id,
        "full_name": emp.full_name,
        "username": emp.username,
        "phone": emp.phone,
        "birth_date": emp.birth_date.isoformat() if emp.birth_date else None,
        "photo": emp.photo,
        "role": emp.role,
        "role_label": roles.UZ_LABELS.get(emp.role, emp.role),
        "position": emp.position or roles.UZ_LABELS.get(emp.role, emp.role),
        "branch_id": emp.branch_id,
        "branch": emp.branch.name if emp.branch else None,
        "manager_id": emp.manager_id,
        "manager": manager.full_name if manager else None,
        "hired_date": (emp.hired_date or
                       (emp.created_at.date() if emp.created_at else None)
                       ).isoformat() if (emp.hired_date or emp.created_at) else None,
        "is_active": bool(emp.is_active),
        "exit_type": emp.exit_type,
        "exit_type_label": roles.EXIT_TYPE_LABELS.get(emp.exit_type or "", None),
        "exit_reason": emp.exit_reason,
        "exit_date": emp.exit_date.isoformat() if emp.exit_date else None,
        # Maosh - faqat huquqi borga
        "salary": emp.fix_salary if show_salary else None,
        "salary_hidden": not show_salary,
        "bonus_total": bonus_total if show_salary else None,
        # KPI
        "groups": groups,
        "students": students,
        # Voqealar xulosasi
        "vacation_days": vac_days,
        "absences": count("absence"),
        "late_count": count("late"),
        "late_minutes": late_minutes,
        "trainings": count("training"),
        "reviews": len(reviews),
        "avg_review": avg_review,
        "disciplines": count("discipline"),
        "rewards": count("reward"),
        # Onboarding
        "onboarding": onb,
        "onboarding_done": onb_done,
        "onboarding_total": len(onb),
        "onboarding_percent": round(onb_done / len(onb) * 100) if onb else 0,
    }

def _next_month_start(on: date | None = None) -> date:
    """Keyingi oyning 1-sanasi."""
    on = on or date.today()
    return (date(on.year + 1, 1, 1) if on.month == 12
            else date(on.year, on.month + 1, 1))

def _apply_pending_grades(db: Session) -> int:
    """AVTOMAT: kutib turgan daraja sanasi kelganda o'zi almashadi.
    Ustoz oy o'rtasida hamma shartni bajarsa ham, yangi daraja va yangi
    stavka keyingi oyning 1-sanasidan boshlanadi."""
    today = date.today()
    n = 0
    gm = _grade_map(db)
    for t in (db.query(models.Teacher)
              .filter(models.Teacher.pending_grade.isnot(None)).all()):
        if not t.pending_grade_from or t.pending_grade_from > today:
            continue
        key = t.pending_grade
        t.grade = key
        t.grade_since = t.pending_grade_from
        t.pending_grade = None
        t.pending_grade_from = None
        g = gm.get(key)
        if g:
            _sync_group_rates(db, t, g.rate_per_student or 0)
        n += 1
    if n:
        db.commit()
    return n

def _career_task(db: Session, t: models.Teacher, *, title: str,
                 body: str, priority: str = "normal") -> None:
    """Daraja o'zgargani jimgina o'tib ketmasin — vazifa bo'lib
    ko'rinadi."""
    if db.query(models.Task).filter(models.Task.title == title).first():
        return
    who = (db.query(models.User)
           .filter(models.User.role == roles.ACADEMIC_HEAD,
                   models.User.is_active == 1).first()) or \
          _hr_user(db, t.branch_id)
    task = models.Task(
        title=title, description=body,
        assignee_id=who.id if who else None,
        branch_id=t.branch_id,
        deadline=date.today() + timedelta(days=3),
        priority=priority, source="manual", created_by="Tizim")
    db.add(task)
    db.flush()
    _ensure_public_id(db, "task", task)

_GRADE_RUN_AT: list = [None]

def _apply_grade_rules_throttled(db: Session, minutes: int = 30) -> dict:
    """Har bir so'rovda emas, yarim soatda bir marta. Karyera bo'limi
    ochilganda esa darrov ishlaydi (_apply_grade_rules to'g'ridan-
    to'g'ri chaqiriladi)."""
    now = datetime.utcnow()
    last = _GRADE_RUN_AT[0]
    if last and (now - last).total_seconds() < minutes * 60:
        return {}
    _GRADE_RUN_AT[0] = now
    try:
        return _apply_grade_rules(db)
    except Exception:
        db.rollback()
        return {}

def _apply_grade_rules(db: Session) -> dict:
    """AVTOMAT: mezonlar bajarilgan bo'lsa darajani ko'taradi, oylik
    test o'rtachasi pasaygan bo'lsa tushiradi, natija 50% dan past
    bo'lsa qayta tayyorlashga qo'yadi.

    Hech kim tugma bosmaydi. Lekin har bir o'zgarish tarixga sababi
    va raqamlari bilan yoziladi hamda vazifa bo'lib chiqadi — kerak
    bo'lsa asoschi orqaga qaytara oladi."""
    today = date.today()
    out = {"promoted": 0, "demoted": 0, "remediation": 0, "cleared": 0,
           "activated": 0}
    # Avval kutib turgan darajalar: sanasi kelgani kuchga kiradi
    out["activated"] = _apply_pending_grades(db)
    teachers = (db.query(models.Teacher)
                .filter(models.Teacher.is_active == 1).all())
    if not teachers or not _grade_rows(db):
        return out

    for t in teachers:
        try:
            st = _grade_state(db, t, today)
        except Exception:
            continue

        # --- Qayta tayyorlash muddati tugadimi ---
        if t.remediation_until and t.remediation_until < today:
            t.remediation_until = None
            t.remediation_reason = None
            db.add(models.TeacherGradeEvent(
                teacher_id=t.id, from_grade=t.grade, to_grade=t.grade,
                kind="remediation_done", effective_from=today,
                reason="Qayta tayyorlash muddati tugadi",
                decided_by="Tizim"))
            out["cleared"] += 1

        # --- Natija 50% dan past: yangi guruh yo'q, qayta test ---
        if st["need_remediation"] and not st["in_remediation"]:
            until = today + timedelta(days=roles.REMEDIATION_DAYS)
            t.remediation_until = until
            t.remediation_reason = (
                f"O'quvchilarning atigi {st['pass_rate']}% i bosqichdan "
                f"o'tdi ({roles.REMEDIATION_BELOW}% dan past)")
            db.add(models.TeacherGradeEvent(
                teacher_id=t.id, from_grade=t.grade, to_grade=t.grade,
                kind="remediation", effective_from=today,
                reason=t.remediation_reason,
                pass_rate=st["pass_rate"], decided_by="Tizim"))
            _career_task(
                db, t, priority="high",
                title=(f"Qayta tayyorlash: {t.full_name} — "
                       f"{until.isoformat()}"),
                body=(f"O'quvchilarning {st['pass_rate']}% i bosqichdan "
                      f"o'tdi ({st['pass_results']} ta natija bo'yicha).\n\n"
                      "Hujjat bo'yicha tartib:\n"
                      "1. O'tgan o'quvchilar boshqa ustozga beriladi.\n"
                      "2. O'ta olmaganlarini ustozning o'zi qayta "
                      "tayyorlaydi.\n"
                      f"3. {until.isoformat()} da qayta test.\n"
                      "4. Shundan keyingina yangi guruh ochiladi.\n\n"
                      "Shu muddatgacha tizim bu ustozga yangi guruh "
                      "biriktirishga yo'l qo'ymaydi."))
            out["remediation"] += 1
            continue      # tushirish bilan bir vaqtda bo'lmasin

        # --- Pastga tushirish ---
        if st["should_demote"]:
            gm = _grade_map(db)
            cur = gm.get(t.grade or "")
            to_key = cur.demote_to if cur else None
            if to_key and to_key in gm:
                reason = (f"Oylik test o'rtachasi {st['test_avg']}% — "
                          f"{st['demote_below']}% dan past "
                          f"({st['test_results']} ta natija)")
                _set_grade(db, t, to_key, kind="demote", reason=reason,
                           test_avg=st["test_avg"])
                _career_task(
                    db, t, priority="high",
                    title=(f"Daraja tushdi: {t.full_name} — "
                           f"{gm[to_key].label} ({today.isoformat()})"),
                    body=(f"{reason}\n\n"
                          f"Yangi stavka: {gm[to_key].rate_per_student:,.0f} "
                          "so'm (bir o'quvchidan).\n"
                          "O'tgan oylarning oyligi o'zgarmaydi — eski "
                          "stavkada qoladi.\n\n"
                          "Xato bo'lsa Karyera bo'limidan darajani "
                          "qaytarish mumkin.").replace(",", " "))
                out["demoted"] += 1
                continue

        # --- Ko'tarish ---
        if st["ready"] and st["next_grade"] and not st["in_remediation"]:
            gm = _grade_map(db)
            to_key = st["next_grade"]
            reason = (f"Barcha shartlar bajarildi: o'quvchilarning "
                      f"{st['pass_rate']}% i bosqichdan o'tdi, tajriba "
                      f"{round(st['months'])} oy, sertifikat "
                      f"{t.cert or '—'}")
            # Oy o'rtasida bajarilsa ham yangi daraja KEYINGI OYDAN
            # kuchga kiradi - shunda oy bitta stavkada yopiladi.
            eff = (_next_month_start() if roles.GRADE_EFFECTIVE_NEXT_MONTH
                   else None)
            _set_grade(db, t, to_key, kind="promote", reason=reason,
                       pass_rate=st["pass_rate"], test_avg=st["test_avg"],
                       on=eff)
            _career_task(
                db, t,
                title=(f"Daraja ko'tarildi: {t.full_name} — "
                       f"{gm[to_key].label} ({today.isoformat()})"),
                body=(f"{reason}\n\n"
                      f"Yangi stavka: {gm[to_key].rate_per_student:,.0f} "
                      "so'm (bir o'quvchidan).\n"
                      f"Endi {gm[to_key].min_groups}-"
                      f"{gm[to_key].max_groups} ta guruh olib bora "
                      "oladi.\n\n"
                      "Ustozni tabriklashni unutmang.").replace(",", " "))
            out["promoted"] += 1

    db.commit()
    return out

@router.get("/api/payroll")
def payroll_overview(
    year: int | None = None,
    month: int | None = None,
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FINANCE_ACCESS, *roles.SALARY_VIEW_ALL)),
):
    """Barcha ustozlar bo'yicha oylik. Hech narsa "ishga tushirilmaydi" —
    ro'yxat har safar darslardan qayta hisoblanadi."""
    # Daraja o'zgarishi oylikka ta'sir qiladi - avval qoidalarni
    # yurgizamiz, keyin hisoblaymiz.
    _apply_grade_rules_throttled(db)
    today = date.today()
    y, m = year or today.year, month or today.month
    start, end = billing.month_bounds(y, m)
    period = f"{y:04d}-{m:02d}"

    q = scope_to_branch(db.query(models.Teacher), models.Teacher, user, branch_id)
    teachers = q.filter(models.Teacher.is_active == 1).all()

    rows = []
    for t in teachers:
        e = _teacher_earned(db, t.id, since=start, until=end)
        paid = _teacher_paid(db, t.id, since=start, until=end)
        card_balance = round(_teacher_earned(db, t.id)["amount"]
                             - _teacher_paid(db, t.id), 2)
        if e["amount"] == 0 and paid == 0:
            continue
        rows.append({
            "teacher_id": t.id,
            "full_name": t.full_name,
            "branch": t.branch.name if t.branch else None,
            "lessons": e["lessons"],
            "attendances": e["attendances"],
            "earned": e["amount"],
            "paid": paid,
            "left": round(e["amount"] - paid, 2),
            "balance": card_balance,
            "groups": e["by_group"],
        })
    rows.sort(key=lambda r: -r["earned"])
    return {
        "period": period,
        "rows": rows,
        "teacher_count": len(rows),
        "earned": round(sum(r["earned"] for r in rows), 2),
        "paid": round(sum(r["paid"] for r in rows), 2),
        "left": round(sum(r["left"] for r in rows), 2),
        "kinds": [{"key": k, "label": lbl, "hint": h}
                  for k, lbl, h in roles.TEACHER_PAYMENT_KINDS],
        "can_pay": user.role in tuple(roles.SALARY_PAY),
    }

@router.get("/api/career")
def career_map(
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.CAREER_ACCESS)),
):
    """Ustozlarning daraja xaritasi. Ochilgan zahoti avtomat qoidalar
    ham ishlaydi — hech kim tugma bosmaydi."""
    try:
        applied = _apply_grade_rules(db)
    except Exception:
        db.rollback()
        applied = {}

    q = scope_to_branch(db.query(models.Teacher), models.Teacher, user,
                        branch_id)
    teachers = q.filter(models.Teacher.is_active == 1).order_by(
        models.Teacher.full_name).all()

    rows = []
    counts: dict = {}
    for t in teachers:
        st = _grade_state(db, t)
        rows.append(st)
        counts[st["grade"]] = counts.get(st["grade"], 0) + 1

    order = {g: i for i, g in enumerate(roles.GRADE_ORDER)}
    rows.sort(key=lambda r: (-order.get(r["grade"], 0), r["full_name"]))

    return {
        "rows": rows,
        "grades": [_grade_row_out(g, counts) for g in _grade_rows(db)],
        "ready": [r for r in rows if r["ready"]],
        "at_risk": [r for r in rows if r["should_demote"]],
        "remediation": [r for r in rows if r["in_remediation"]],
        "applied": applied,
        "pass_window_months": roles.PASS_WINDOW_MONTHS,
        "test_window_days": roles.TEST_WINDOW_DAYS,
        "min_results": roles.GRADE_MIN_RESULTS,
        "remediation_below": roles.REMEDIATION_BELOW,
        "can_edit": user.role in roles.GRADE_ADMIN,
        "hint": ("Daraja va stavka avtomat o'zgaradi. O'zgargan oyning "
                 "o'zidan boshlab yangi stavka ishlaydi, o'tgan oylar "
                 "eski stavkada qoladi — to'langan oylik qayta "
                 "hisoblanmaydi."),
    }

@router.put("/api/career/grades/{key}")
def update_grade(
    key: str,
    payload: schemas.GradeUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.GRADE_ADMIN)),
):
    """Daraja jadvalini tahrirlash. Hujjatning o'zida "talablar
    o'zgarib turishi mumkin" deb yozilgan — shuning uchun raqamlar
    kodda emas, shu yerda."""
    g = db.query(models.TeacherGrade).filter(
        models.TeacherGrade.key == key).first()
    if not g:
        raise HTTPException(404, "Daraja topilmadi")
    given = payload.model_dump(exclude_unset=True)
    rate_changed = ("rate_per_student" in given
                    and given["rate_per_student"] != g.rate_per_student)
    for k, v in given.items():
        setattr(g, k, v)
    db.commit()

    # Narx o'zgargan bo'lsa - shu darajadagi ustozlarning guruhlariga
    # ham qo'yiladi (qo'lda narx qo'yilganlaridan tashqari).
    touched = 0
    if rate_changed:
        for t in db.query(models.Teacher).filter(
                models.Teacher.grade == key).all():
            touched += _sync_group_rates(db, t, g.rate_per_student or 0)
        db.commit()
    return {"ok": True, "groups_updated": touched}

def _minutes(t: str) -> int | None:
    return roles.time_to_minutes(t)

@router.post("/api/hr/attendance")
def mark_staff_attendance(
    payload: schemas.StaffAttendanceCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.ATTENDANCE_ACCESS)),
):
    emp = db.query(models.User).get(payload.user_id)
    if not emp:
        raise HTTPException(404, "Xodim topilmadi")
    on = payload.date or date.today()

    row = (db.query(models.StaffAttendance)
           .filter(models.StaffAttendance.user_id == emp.id,
                   models.StaffAttendance.work_date == on).first())
    if not row:
        row = models.StaffAttendance(user_id=emp.id, work_date=on,
                                     created_by=user.full_name)
        db.add(row)

    if payload.check_in is not None:
        row.check_in = payload.check_in
    if payload.check_out is not None:
        row.check_out = payload.check_out
    if payload.note is not None:
        row.note = payload.note

    # Kechikish va erta ketish — avtomat
    start = _minutes(roles.WORK_START) or 0
    end = _minutes(roles.WORK_END) or 0
    ci = _minutes(row.check_in or "")
    co = _minutes(row.check_out or "")

    row.late_minutes = (max(0, ci - start - roles.LATE_TOLERANCE_MIN)
                        if ci is not None else 0)
    row.early_minutes = (max(0, end - co) if co is not None else 0)
    row.worked_minutes = (max(0, co - ci) if ci is not None and co is not None
                          else 0)
    db.commit(); db.refresh(row)
    return _attendance_out(row, emp)

def _attendance_out(r: models.StaffAttendance, emp=None) -> dict:
    return {
        "id": r.id,
        "user_id": r.user_id,
        "full_name": emp.full_name if emp else None,
        "date": r.work_date.isoformat() if r.work_date else None,
        "check_in": r.check_in,
        "check_out": r.check_out,
        "late_minutes": r.late_minutes or 0,
        "early_minutes": r.early_minutes or 0,
        "worked_minutes": r.worked_minutes or 0,
        "worked_hours": round((r.worked_minutes or 0) / 60, 1),
        "note": r.note,
    }

@router.get("/api/hr/attendance")
def staff_attendance(
    year: int | None = None,
    month: int | None = None,
    user_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.ATTENDANCE_ACCESS)),
):
    today = date.today()
    y, m = year or today.year, month or today.month
    start, end = billing.month_bounds(y, m)

    staff = db.query(models.User).filter(
        models.User.is_active == 1,
        ~models.User.role.in_(roles.EXTERNAL_ROLES)).all()
    if user_id:
        staff = [u for u in staff if u.id == user_id]
    ids = [u.id for u in staff]

    rows = (db.query(models.StaffAttendance)
            .filter(models.StaffAttendance.user_id.in_(ids or [-1]),
                    models.StaffAttendance.work_date >= start,
                    models.StaffAttendance.work_date <= end).all())

    by_user = {}
    for r in rows:
        by_user.setdefault(r.user_id, []).append(r)

    summary = []
    for u in staff:
        mine = by_user.get(u.id, [])
        late = [r for r in mine if (r.late_minutes or 0) > 0]
        summary.append({
            "user_id": u.id,
            "full_name": u.full_name,
            "role_label": roles.UZ_LABELS.get(u.role, u.role),
            "branch": u.branch.name if u.branch else None,
            "days": len(mine),
            "late_days": len(late),
            "late_minutes": sum(r.late_minutes or 0 for r in mine),
            "early_minutes": sum(r.early_minutes or 0 for r in mine),
            "worked_hours": round(
                sum(r.worked_minutes or 0 for r in mine) / 60, 1),
            "rows": [_attendance_out(r) for r in
                     sorted(mine, key=lambda x: x.work_date or date.min,
                            reverse=True)],
        })
    summary.sort(key=lambda r: -r["late_minutes"])

    return {
        "period": f"{y:04d}-{m:02d}",
        "work_start": roles.WORK_START,
        "work_end": roles.WORK_END,
        "tolerance": roles.LATE_TOLERANCE_MIN,
        "rows": summary,
        "total_late_minutes": sum(r["late_minutes"] for r in summary),
        "staff_with_late": sum(1 for r in summary if r["late_days"] > 0),
    }

@router.get("/api/hr/dates")
def hr_dates(
    days: int = roles.STAFF_DATE_HORIZON,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.STAFF_DATES_ACCESS)),
):
    """Yaqinlashayotgan tug'ilgan kunlar va ish yubileylari.
    Ochilgan zahoti yaqin sanalar uchun vazifa ham yaratiladi."""
    _ensure_staff_date_tasks(db, user)
    rows = _staff_dates(db, user, days=max(1, min(days, 366)))

    staff = scope_to_branch(db.query(models.User), models.User, user).filter(
        models.User.is_active == 1).all()
    no_birth = [u.full_name for u in staff if not u.birth_date]
    no_hired = [u.full_name for u in staff if not u.hired_date]

    return {
        "rows": rows,
        "soon": [r for r in rows if r["soon"]],
        "lead_days": roles.STAFF_DATE_LEAD_DAYS,
        "days": days,
        "birthdays": sum(1 for r in rows if r["kind"] == "birthday"),
        "anniversaries": sum(1 for r in rows if r["kind"] == "anniversary"),
        "missing_birth_date": no_birth,
        "missing_hired_date": no_hired,
        "kinds": [{"key": k, "label": lbl, "tone": t}
                  for k, lbl, t in roles.STAFF_DATE_KINDS],
        "hint": (f"Sanaga {roles.STAFF_DATE_LEAD_DAYS} kun qolganda "
                 "HR'ga vazifa avtomat tushadi — tayyor tabrik matni "
                 "bilan. Sana kiritilmagan xodimning tug'ilgan kuni "
                 "eslatilmaydi."),
    }

def _dep_out(db: Session, d: models.Department) -> dict:
    head = db.query(models.User).get(d.head_id) if d.head_id else None
    return {
        "id": d.id, "key": d.key, "name": d.name,
        "description": d.description,
        "head_id": d.head_id, "head": head.full_name if head else None,
        "position": d.position, "is_active": bool(d.is_active),
        "positions": db.query(models.Position).filter(
            models.Position.department_id == d.id,
            models.Position.is_active == 1).count(),
        "employees": db.query(models.User).join(
            models.Position, models.User.position == models.Position.key,
            isouter=True).filter(
            models.Position.department_id == d.id,
            models.User.is_active == 1).count(),
    }

def _pos_out(db: Session, p: models.Position) -> dict:
    d = db.query(models.Department).get(p.department_id) \
        if p.department_id else None
    return {
        "id": p.id, "key": p.key, "name": p.name,
        "department_id": p.department_id,
        "department": d.name if d else None,
        "system_role": p.system_role,
        "role_label": roles.UZ_LABELS.get(p.system_role or "", None),
        "probation_months": p.probation_months,
        "trial_required": bool(p.trial_required),
        "salary_from": p.salary_from, "salary_to": p.salary_to,
        "description": p.description, "requirements": p.requirements,
        "is_active": bool(p.is_active),
        "employees": db.query(models.User).filter(
            models.User.position == p.key,
            models.User.is_active == 1).count(),
    }

@router.get("/api/hr/structure")
def hr_structure(db: Session = Depends(get_db),
                 user=Depends(require_role(*roles.WORKFORCE_VIEW))):
    """Bo'limlar va lavozimlar — HR tizimining tayanchi."""
    deps = db.query(models.Department).order_by(
        models.Department.position, models.Department.id).all()
    poss = db.query(models.Position).order_by(models.Position.id).all()
    return {
        "departments": [_dep_out(db, d) for d in deps],
        "positions": [_pos_out(db, p) for p in poss],
        "roles": [{"key": k, "label": l} for k, l in
                  roles.UZ_LABELS.items()],
        "employment_types": [{"key": k, "label": l}
                             for k, l in roles.EMPLOYMENT_TYPES],
        "can_edit": user.role in roles.HR_FULL,
        "hint": ("Lavozim tizimdagi rolga bog'lanadi — xodim yaratilganda "
                 "roli shundan olinadi, qo'lda tanlanmaydi."),
    }

@router.post("/api/hr/departments")
def hr_dep_add(payload: schemas.DepartmentIn, db: Session = Depends(get_db),
               user=Depends(require_role(*roles.HR_FULL))):
    if not (payload.name or "").strip():
        raise HTTPException(400, "Nom kerak")
    key = payload.key or roles.translit(payload.name).replace(" ", "_")[:30]
    if db.query(models.Department).filter(
            models.Department.key == key).first():
        raise HTTPException(400, "Bu kalit band")
    d = models.Department(**{**payload.model_dump(), "key": key})
    db.add(d); db.commit(); db.refresh(d)
    audit.log(db, user, entity="department", action="create",
              entity_id=d.id, entity_label=d.name, commit=True)
    return _dep_out(db, d)

@router.put("/api/hr/departments/{did}")
def hr_dep_edit(did: int, payload: schemas.DepartmentPatch,
                db: Session = Depends(get_db),
                user=Depends(require_role(*roles.HR_FULL))):
    d = db.query(models.Department).get(did)
    if not d:
        raise HTTPException(404, "Topilmadi")
    for f, v in payload.model_dump(exclude_unset=True).items():
        setattr(d, f, v)
    db.commit()
    audit.log(db, user, entity="department", action="update",
              entity_id=did, entity_label=d.name, commit=True)
    return _dep_out(db, d)

@router.post("/api/hr/positions")
def hr_pos_add(payload: schemas.PositionIn, db: Session = Depends(get_db),
               user=Depends(require_role(*roles.HR_FULL))):
    if not (payload.name or "").strip():
        raise HTTPException(400, "Nom kerak")
    if payload.system_role and payload.system_role not in roles.ALL_ROLES:
        raise HTTPException(400, "Noma'lum rol")
    key = payload.key or roles.translit(payload.name).replace(" ", "_")[:30]
    if db.query(models.Position).filter(models.Position.key == key).first():
        raise HTTPException(400, "Bu kalit band")
    p = models.Position(**{**payload.model_dump(), "key": key})
    db.add(p); db.commit(); db.refresh(p)
    audit.log(db, user, entity="position", action="create",
              entity_id=p.id, entity_label=p.name, commit=True)
    return _pos_out(db, p)

@router.put("/api/hr/positions/{pid}")
def hr_pos_edit(pid: int, payload: schemas.PositionPatch,
                db: Session = Depends(get_db),
                user=Depends(require_role(*roles.HR_FULL))):
    p = db.query(models.Position).get(pid)
    if not p:
        raise HTTPException(404, "Topilmadi")
    data = payload.model_dump(exclude_unset=True)
    if data.get("system_role") and data["system_role"] not in roles.ALL_ROLES:
        raise HTTPException(400, "Noma'lum rol")
    for f, v in data.items():
        setattr(p, f, v)
    db.commit()
    audit.log(db, user, entity="position", action="update",
              entity_id=pid, entity_label=p.name, commit=True)
    return _pos_out(db, p)

def _headcount(db: Session, branch_id, position_key) -> int:
    q = db.query(models.User).filter(models.User.is_active == 1)
    if position_key:
        q = q.filter(models.User.position == position_key)
    if branch_id:
        q = q.filter(models.User.branch_id == branch_id)
    return q.count()

def _teacher_load(db: Session, branch_id=None) -> list[dict]:
    """Ustozlarning yuklamasi: nechta guruh olib boryapti va yana
    nechtasini olishi mumkin."""
    q = db.query(models.Teacher).filter(models.Teacher.is_active == 1)
    if branch_id:
        q = q.filter(models.Teacher.branch_id == branch_id)
    teachers = q.all()
    if not teachers:
        return []

    groups = db.query(models.Group).filter(
        models.Group.teacher_id.isnot(None)).all()
    per_teacher: dict = {}
    for g in groups:
        if getattr(g, "is_active", 1) == 0:
            continue
        per_teacher.setdefault(g.teacher_id, []).append(g)

    grades = {g.key: g for g in db.query(models.TeacherGrade).all()}
    out = []
    for t in teachers:
        mine = per_teacher.get(t.id, [])
        gr = grades.get(t.grade or "")
        limit = t.max_groups or (gr.max_groups if gr else None) \
            or roles.TEACHER_MAX_GROUPS
        pct = round(len(mine) / limit * 100, 1) if limit else 0.0
        key, label, tone = roles.utilization_band(pct)
        br = db.query(models.Branch).get(t.branch_id) if t.branch_id else None
        out.append({
            "teacher_id": t.id, "name": t.full_name,
            "branch": br.name if br else None,
            "branch_id": t.branch_id,
            "grade": t.grade,
            "grade_label": roles.GRADE_LABELS.get(t.grade or "", "—"),
            "groups": len(mine), "max_groups": limit,
            "free_slots": max(0, limit - len(mine)) if limit else 0,
            "percent": pct, "band": key, "band_label": label, "tone": tone,
        })
    out.sort(key=lambda r: -r["percent"])
    return out

def _plan_out(db: Session, p: models.WorkforcePlan) -> dict:
    br = db.query(models.Branch).get(p.branch_id) if p.branch_id else None
    dep = db.query(models.Department).get(p.department_id) \
        if p.department_id else None
    pos = db.query(models.Position).get(p.position_id) \
        if p.position_id else None
    current = _headcount(db, p.branch_id, pos.key if pos else None)
    approved = p.approved_headcount or 0
    gap = approved - current
    return {
        "id": p.id, "year": p.year, "month": p.month, "quarter": p.quarter,
        "branch_id": p.branch_id, "branch": br.name if br else "Umumiy",
        "department_id": p.department_id,
        "department": dep.name if dep else None,
        "position_id": p.position_id, "position": pos.name if pos else None,
        "approved_headcount": approved,
        "current_headcount": current,
        # Bo'shliq har safar qayta hisoblanadi — qo'lda kiritilmaydi
        "gap": gap,
        "over_staffed": gap < 0,
        "planned_hires": p.planned_hires or 0,
        "expected_leaves": p.expected_leaves or 0,
        "expected_groups": p.expected_groups or 0,
        "budgeted_salary": p.budgeted_salary,
        "note": p.note,
        "status": p.status,
        "status_label": roles.PLAN_STATUS_LABELS.get(p.status, "—"),
        "status_tone": roles.PLAN_STATUS_TONE.get(p.status, "slate"),
        "approved_at": p.approved_at.isoformat() if p.approved_at else None,
    }

@router.get("/api/hr/workforce")
def hr_workforce(year: int | None = None, branch_id: int | None = None,
                 db: Session = Depends(get_db),
                 user=Depends(require_role(*roles.WORKFORCE_VIEW))):
    """Shtat rejasi va ustoz yuklamasi."""
    year = year or date.today().year
    q = db.query(models.WorkforcePlan).filter(
        models.WorkforcePlan.year == year)
    if user.role == roles.BRANCH_MANAGER and user.branch_id:
        branch_id = user.branch_id
    if branch_id:
        q = q.filter(models.WorkforcePlan.branch_id == branch_id)
    rows = [_plan_out(db, p) for p in
            q.order_by(models.WorkforcePlan.id).all()]

    load = _teacher_load(db, branch_id)
    bands: dict = {}
    for r in load:
        bands[r["band"]] = bands.get(r["band"], 0) + 1

    gap_total = sum(r["gap"] for r in rows if r["gap"] > 0)
    return {
        "year": year,
        "rows": rows,
        "totals": {
            "approved": sum(r["approved_headcount"] for r in rows),
            "current": sum(r["current_headcount"] for r in rows),
            "gap": gap_total,
            "planned_hires": sum(r["planned_hires"] for r in rows),
            "expected_leaves": sum(r["expected_leaves"] for r in rows),
            "budget": sum(r["budgeted_salary"] or 0 for r in rows),
        },
        "teacher_load": load,
        "load_summary": [
            {"key": k, "label": lbl, "tone": tone,
             "count": bands.get(k, 0)}
            for _c, k, lbl, tone in roles.UTILIZATION_BANDS],
        "free_group_slots": sum(r["free_slots"] for r in load),
        "overloaded": [r for r in load if r["band"] == "over"],
        "statuses": [{"key": k, "label": l, "tone": t}
                     for k, l, t in roles.PLAN_STATUSES],
        "can_edit": user.role in roles.HR_FULL,
        "hint": ("Bo'shliq har safar qayta hisoblanadi: tasdiqlangan "
                 "shtat minus hozirgi faol xodim. Qo'lda kiritilmaydi."),
    }

@router.post("/api/hr/workforce")
def hr_plan_add(payload: schemas.PlanIn, db: Session = Depends(get_db),
                user=Depends(require_role(*roles.HR_FULL))):
    p = models.WorkforcePlan(**payload.model_dump(), created_by=user.id)
    db.add(p); db.commit(); db.refresh(p)
    audit.log(db, user, entity="workforce_plan", action="create",
              entity_id=p.id,
              entity_label=f"{p.year} · {p.approved_headcount} o'rin", commit=True)
    return _plan_out(db, p)

@router.put("/api/hr/workforce/{pid}")
def hr_plan_edit(pid: int, payload: schemas.PlanPatch,
                 db: Session = Depends(get_db),
                 user=Depends(require_role(*roles.HR_FULL))):
    p = db.query(models.WorkforcePlan).get(pid)
    if not p:
        raise HTTPException(404, "Topilmadi")
    data = payload.model_dump(exclude_unset=True)
    new_status = data.get("status")
    if new_status and new_status not in roles.PLAN_STATUS_LABELS:
        raise HTTPException(400, "Noma'lum holat")
    if new_status == "approved" and user.role not in roles.FULL_ACCESS:
        raise HTTPException(403, "Shtat rejasini faqat rahbar tasdiqlaydi")
    for f, v in data.items():
        setattr(p, f, v)
    if new_status == "approved":
        p.approved_by = user.id
        p.approved_at = datetime.utcnow()
    db.commit()
    audit.log(db, user, entity="workforce_plan", action="update",
              entity_id=pid, entity_label=str(p.year), commit=True)
    return _plan_out(db, p)

def _request_out(db: Session, r: models.StaffRequest) -> dict:
    by = db.query(models.User).get(r.requested_by) if r.requested_by else None
    br = db.query(models.Branch).get(r.branch_id) if r.branch_id else None
    dep = db.query(models.Department).get(r.department_id) \
        if r.department_id else None
    pos = db.query(models.Position).get(r.position_id) \
        if r.position_id else None
    repl = db.query(models.User).get(r.replacing_user_id) \
        if r.replacing_user_id else None
    steps = db.query(models.RequestApproval).filter(
        models.RequestApproval.request_id == r.id).order_by(
        models.RequestApproval.id).all()
    today = date.today()
    waiting = None
    if r.status in roles.REQUEST_APPROVERS:
        waiting = [roles.UZ_LABELS.get(x, x)
                   for x in roles.REQUEST_APPROVERS[r.status]]
    return {
        "id": r.id, "public_id": r.public_id,
        "requested_by": by.full_name if by else None,
        "request_date": r.request_date.isoformat() if r.request_date else None,
        "branch_id": r.branch_id, "branch": br.name if br else "Umumiy",
        "department_id": r.department_id,
        "department": dep.name if dep else None,
        "position_id": r.position_id, "position": pos.name if pos else None,
        "headcount": r.headcount or 1,
        "employment_type": r.employment_type,
        "employment_label": roles.EMPLOYMENT_TYPE_LABELS.get(
            r.employment_type or "", "—"),
        "work_schedule": r.work_schedule,
        "needed_from": r.needed_from.isoformat() if r.needed_from else None,
        "days_left": ((r.needed_from - today).days
                      if r.needed_from else None),
        "reason": r.reason,
        "reason_label": roles.REQUEST_REASON_LABELS.get(r.reason or "", "—"),
        "replacing": repl.full_name if repl else None,
        "salary_from": r.salary_from, "salary_to": r.salary_to,
        "requirements": r.requirements, "certificates": r.certificates,
        "experience_years": r.experience_years,
        "duties": r.duties, "kpi_note": r.kpi_note,
        "priority": r.priority,
        "priority_label": roles.PRIORITY_LABELS.get(r.priority or "", "—"),
        "priority_tone": roles.PRIORITY_TONE.get(r.priority or "", "slate"),
        "status": r.status,
        "status_label": roles.REQUEST_STATE_LABELS.get(r.status, "—"),
        "status_tone": roles.REQUEST_STATE_TONE.get(r.status, "slate"),
        "reject_reason": r.reject_reason,
        "vacancy_id": r.vacancy_id,
        "locked": r.status in roles.REQUEST_LOCKED_AFTER,
        "waiting_for": waiting,
        "approvals": [{
            "step": s.step,
            "step_label": roles.REQUEST_STATE_LABELS.get(s.step, s.step),
            "decision": s.decision,
            "by": (db.query(models.User).get(s.decided_by).full_name
                   if s.decided_by else None),
            "at": s.decided_at.isoformat() if s.decided_at else None,
            "note": s.note,
        } for s in steps],
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }

def _can_decide(user, status: str) -> bool:
    allowed = roles.REQUEST_APPROVERS.get(status, [])
    return user.role in allowed

@router.get("/api/hr/staff-requests")
def hr_requests(status: str | None = None, branch_id: int | None = None,
                db: Session = Depends(get_db),
                user=Depends(require_role(*roles.REQUEST_CREATE))):
    q = db.query(models.StaffRequest)
    # Filial rahbari faqat o'z filialining so'rovlarini ko'radi
    if user.role == roles.BRANCH_MANAGER and user.branch_id:
        q = q.filter(_branch_in(db, user, models.StaffRequest.branch_id))
    elif branch_id:
        q = q.filter(models.StaffRequest.branch_id == branch_id)
    if status:
        q = q.filter(models.StaffRequest.status == status)
    rows = [_request_out(db, r) for r in
            q.order_by(models.StaffRequest.id.desc()).limit(300).all()]

    counts: dict = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    return {
        "rows": rows,
        "statuses": [{"key": k, "label": l, "tone": t,
                      "count": counts.get(k, 0)}
                     for k, l, t in roles.STAFF_REQUEST_FLOW],
        "reasons": [{"key": k, "label": l,
                     "needs_replacement": k in roles.REPLACEMENT_REASONS}
                    for k, l, _ in roles.REQUEST_REASONS],
        "priorities": [{"key": k, "label": l, "tone": t, "sla_days": d}
                       for k, l, t, d in roles.REQUEST_PRIORITIES],
        "employment_types": [{"key": k, "label": l}
                             for k, l in roles.EMPLOYMENT_TYPES],
        "waiting_my_decision": sum(
            1 for r in rows if _can_decide(user, r["status"])),
        "hint": ("Tasdiqlanmagan so'rov bo'yicha vakansiya ochilmaydi — "
                 "byudjet og'zaki kelishuvdan himoyalangan."),
    }

@router.post("/api/hr/staff-requests")
def hr_request_add(payload: schemas.StaffRequestIn,
                   db: Session = Depends(get_db),
                   user=Depends(require_role(*roles.REQUEST_CREATE))):
    data = payload.model_dump()
    if data.get("reason") and data["reason"] not in \
            roles.REQUEST_REASON_LABELS:
        raise HTTPException(400, "Noma'lum sabab")
    if data.get("priority") and data["priority"] not in roles.PRIORITY_LABELS:
        raise HTTPException(400, "Noma'lum muhimlik darajasi")
    # O'rinbosar sabablarida kimning o'rniga ekani ko'rsatilishi kerak
    if data.get("reason") in roles.REPLACEMENT_REASONS and \
            not data.get("replacing_user_id"):
        raise HTTPException(
            400, "Bu sababda kimning o'rniga kerakligini ko'rsating")
    if user.role == roles.BRANCH_MANAGER and user.branch_id:
        data["branch_id"] = user.branch_id
    r = models.StaffRequest(**data, requested_by=user.id, status="draft")
    db.add(r); db.commit(); db.refresh(r)
    _ensure_public_id(db, "staff_request", r)
    db.commit()
    audit.log(db, user, entity="staff_request", action="create",
              entity_id=r.id, entity_label=r.public_id, commit=True)
    return _request_out(db, r)

@router.put("/api/hr/staff-requests/{rid}")
def hr_request_edit(rid: int, payload: schemas.StaffRequestPatch,
                    db: Session = Depends(get_db),
                    user=Depends(require_role(*roles.REQUEST_CREATE))):
    r = db.query(models.StaffRequest).get(rid)
    if not r:
        raise HTTPException(404, "Topilmadi")
    if r.status in roles.REQUEST_LOCKED_AFTER:
        raise HTTPException(
            400, "Bu so'rov yopilgan — tahrirlab bo'lmaydi")
    if r.requested_by != user.id and user.role not in roles.HR_FULL:
        raise HTTPException(403, "Faqat o'z so'rovingizni tahrirlaysiz")
    for f, v in payload.model_dump(exclude_unset=True).items():
        setattr(r, f, v)
    db.commit()
    audit.log(db, user, entity="staff_request", action="update",
              entity_id=rid, entity_label=r.public_id, commit=True)
    return _request_out(db, r)

@router.post("/api/hr/staff-requests/{rid}/submit")
def hr_request_submit(rid: int, db: Session = Depends(get_db),
                      user=Depends(require_role(*roles.REQUEST_CREATE))):
    r = db.query(models.StaffRequest).get(rid)
    if not r:
        raise HTTPException(404, "Topilmadi")
    if r.status != "draft":
        raise HTTPException(400, "Faqat qoralamani yuborish mumkin")
    if not r.position_id:
        raise HTTPException(400, "Lavozimni tanlang")
    if not r.reason:
        raise HTTPException(400, "Sababni ko'rsating")
    r.status = "submitted"
    db.commit()
    out = _request_out(db, r)
    _hr_task(db, title=f"Xodim so'rovi: {r.public_id}",
             body=f"{out['position']} · {out['branch']} · "
                  f"{r.headcount} ta. Sabab: {out['reason_label']}.",
             to_roles=roles.REQUEST_APPROVERS["submitted"],
             branch_id=r.branch_id,
             priority="high" if r.priority in ("high", "critical")
                      else "normal")
    db.commit()
    audit.log(db, user, entity="staff_request", action="submit",
              entity_id=rid, entity_label=r.public_id, commit=True)
    return _request_out(db, r)

@router.post("/api/hr/staff-requests/{rid}/approve")
def hr_request_approve(rid: int, payload: schemas.RequestApprovalIn,
                       db: Session = Depends(get_db),
                       user=Depends(get_current_user)):
    r = db.query(models.StaffRequest).get(rid)
    if not r:
        raise HTTPException(404, "Topilmadi")
    if r.status not in roles.REQUEST_NEXT:
        raise HTTPException(400, "Bu bosqichda tasdiqlash mumkin emas")
    if not _can_decide(user, r.status):
        raise HTTPException(403, "Bu bosqichni siz tasdiqlay olmaysiz")

    step = r.status
    r.status = roles.REQUEST_NEXT[step]
    db.add(models.RequestApproval(
        request_id=r.id, step=step, decision="approved",
        decided_by=user.id, note=payload.note))
    db.commit()

    if r.status == "approved":
        _hr_task(db, title=f"Vakansiya oching: {r.public_id}",
                 body="Xodim so'rovi tasdiqlandi — endi vakansiya "
                      "ochish mumkin.",
                 to_roles=roles.HR_FULL, branch_id=r.branch_id)
    else:
        _hr_task(db, title=f"Tasdiq kerak: {r.public_id}",
                 body=f"So'rov {roles.REQUEST_STATE_LABELS[r.status]} "
                      f"bosqichida sizni kutmoqda.",
                 to_roles=roles.REQUEST_APPROVERS.get(r.status, []),
                 branch_id=r.branch_id)
    db.commit()
    audit.log(db, user, entity="staff_request", action="approve",
              entity_id=rid, entity_label=r.public_id,
              field="status", old_value=step, new_value=r.status, commit=True)
    return _request_out(db, r)

@router.post("/api/hr/staff-requests/{rid}/reject")
def hr_request_reject(rid: int, payload: schemas.RequestRejectIn,
                      db: Session = Depends(get_db),
                      user=Depends(get_current_user)):
    r = db.query(models.StaffRequest).get(rid)
    if not r:
        raise HTTPException(404, "Topilmadi")
    if r.status in roles.REQUEST_LOCKED_AFTER:
        raise HTTPException(400, "Bu so'rov allaqachon yopilgan")
    if not _can_decide(user, r.status) and user.role not in roles.FULL_ACCESS:
        raise HTTPException(403, "Bu bosqichni siz rad eta olmaysiz")
    # Rad etishda sabab MAJBURIY — aks holda so'ragan odam nima
    # qilishini bilmaydi
    if not (payload.reason or "").strip():
        raise HTTPException(400, "Rad etish sababini yozing")

    step = r.status
    r.status = "rejected"
    r.reject_reason = payload.reason
    db.add(models.RequestApproval(
        request_id=r.id, step=step, decision="rejected",
        decided_by=user.id, note=payload.reason))
    db.commit()
    if r.requested_by:
        _hr_task_for(db, r.requested_by,
                     title=f"So'rov rad etildi: {r.public_id}",
                     body=payload.reason, branch_id=r.branch_id)
        db.commit()
    audit.log(db, user, entity="staff_request", action="reject",
              entity_id=rid, entity_label=r.public_id,
              note=payload.reason, commit=True)
    return _request_out(db, r)

@router.post("/api/hr/staff-requests/{rid}/cancel")
def hr_request_cancel(rid: int, db: Session = Depends(get_db),
                      user=Depends(require_role(*roles.REQUEST_CREATE))):
    r = db.query(models.StaffRequest).get(rid)
    if not r:
        raise HTTPException(404, "Topilmadi")
    if r.status in roles.REQUEST_LOCKED_AFTER:
        raise HTTPException(400, "Bu so'rov allaqachon yopilgan")
    if r.requested_by != user.id and user.role not in roles.HR_FULL:
        raise HTTPException(403, "Faqat o'z so'rovingizni bekor qilasiz")
    r.status = "cancelled"
    db.commit()
    audit.log(db, user, entity="staff_request", action="cancel",
              entity_id=rid, entity_label=r.public_id, commit=True)
    return _request_out(db, r)

def _vacancy_stats(db: Session, vid: int) -> dict:
    """Vakansiya bo'yicha nomzod voronkasi."""
    cands = db.query(models.Candidate).filter(
        models.Candidate.vacancy_id == vid).all()
    by_stage: dict = {}
    for c in cands:
        by_stage[c.stage] = by_stage.get(c.stage, 0) + 1
    hired = by_stage.get("hired", 0)
    rejected = by_stage.get("rejected", 0)
    total = len(cands)
    reached = lambda keys: sum(by_stage.get(k, 0) for k in keys)
    return {
        "applications": total,
        "by_stage": [{"key": k, "label": lbl, "count": by_stage.get(k, 0)}
                     for k, lbl in roles.CANDIDATE_STAGES],
        "in_progress": total - hired - rejected,
        "hired": hired,
        "rejected": rejected,
        "interviewed": reached(["interview", "demo", "offer", "hired"]),
        "offered": reached(["offer", "hired"]),
        "hire_rate": round(hired / total * 100, 1) if total else 0.0,
        "offer_rate": (round(reached(["offer", "hired"]) / total * 100, 1)
                       if total else 0.0),
    }

def _vacancy_out(db: Session, v: models.Vacancy,
                 with_stats: bool = True) -> dict:
    br = db.query(models.Branch).get(v.branch_id) if v.branch_id else None
    pos = db.query(models.Position).get(v.position_id) \
        if v.position_id else None
    dep = db.query(models.Department).get(v.department_id) \
        if v.department_id else None
    hm = db.query(models.User).get(v.hiring_manager_id) \
        if v.hiring_manager_id else None
    rec = db.query(models.User).get(v.recruiter_id) \
        if v.recruiter_id else None
    today = date.today()
    opened = v.opened_on or (v.created_at.date() if v.created_at else today)
    is_open = v.status in roles.VACANCY_OPEN_STATES
    days_open = (today - opened).days if is_open else (
        ((v.closed_at or today) - opened).days)
    sla = roles.PRIORITY_SLA_DAYS.get(v.priority or "normal", 30)
    out = {
        "id": v.id, "public_id": v.public_id, "title": v.title,
        "role": v.role,
        "position_id": v.position_id, "position": pos.name if pos else None,
        "trial_required": bool(pos.trial_required) if pos else False,
        "department_id": v.department_id,
        "department": dep.name if dep else None,
        "branch_id": v.branch_id, "branch": br.name if br else "Umumiy",
        "hiring_manager": hm.full_name if hm else None,
        "recruiter": rec.full_name if rec else None,
        "headcount": v.headcount or 1,
        "hired_count": v.hired_count or 0,
        "employment_type": v.employment_type,
        "employment_label": roles.EMPLOYMENT_TYPE_LABELS.get(
            v.employment_type or "", "—"),
        "work_schedule": v.work_schedule,
        "salary_from": v.salary_from, "salary_to": v.salary_to,
        "description": v.description, "duties": v.duties,
        "requirements": v.requirements,
        "experience_years": v.experience_years,
        "education": v.education, "language_level": v.language_level,
        "certificates": v.certificates,
        "probation_months": v.probation_months,
        "kpi_note": v.kpi_note,
        "priority": v.priority or "normal",
        "priority_label": roles.PRIORITY_LABELS.get(v.priority or "normal"),
        "priority_tone": roles.PRIORITY_TONE.get(v.priority or "normal",
                                                 "slate"),
        "status": v.status,
        "status_label": roles.VACANCY_STATE_LABELS.get(v.status, v.status),
        "status_tone": roles.VACANCY_STATE_TONE.get(v.status, "slate"),
        "is_open": is_open,
        "opened_on": opened.isoformat(),
        "target_close": v.target_close.isoformat() if v.target_close else None,
        "closed_at": v.closed_at.isoformat() if v.closed_at else None,
        "close_reason": v.close_reason,
        "close_reason_label": roles.CLOSE_REASON_LABELS.get(
            v.close_reason or "", None),
        "days_open": days_open,
        "sla_days": sla,
        # Uzoq ochiq qolgan vakansiya — filial ishlamayotgan degani
        "overdue": is_open and days_open > sla,
        "request_id": v.request_id,
    }
    if with_stats:
        out.update(_vacancy_stats(db, v.id))
    return out

@router.post("/api/hr/staff-requests/{rid}/convert")
def hr_request_convert(rid: int, db: Session = Depends(get_db),
                       user=Depends(require_role(*roles.VACANCY_MANAGE))):
    """Tasdiqlangan so'rovdan vakansiya ochadi."""
    r = db.query(models.StaffRequest).get(rid)
    if not r:
        raise HTTPException(404, "Topilmadi")
    if r.status == "converted":
        raise HTTPException(400, "Bu so'rov bo'yicha vakansiya ochilgan")
    # Asoschi shoshilinch holatda tasdiqsiz ham ocha oladi, lekin bu
    # audit logda ko'rinadi
    if r.status != "approved" and user.role not in roles.FULL_ACCESS:
        raise HTTPException(
            400, "So'rov hali tasdiqlanmagan — vakansiya ochib bo'lmaydi")

    pos = db.query(models.Position).get(r.position_id) \
        if r.position_id else None
    v = models.Vacancy(
        title=pos.name if pos else "Yangi lavozim",
        role=pos.system_role if pos else None,
        position_id=r.position_id,
        department_id=r.department_id,
        branch_id=r.branch_id,
        request_id=r.id,
        headcount=r.headcount or 1,
        employment_type=r.employment_type,
        work_schedule=r.work_schedule,
        salary_from=r.salary_from, salary_to=r.salary_to,
        requirements=r.requirements,
        certificates=r.certificates,
        experience_years=r.experience_years,
        duties=r.duties, kpi_note=r.kpi_note,
        probation_months=pos.probation_months if pos else None,
        priority=r.priority or "normal",
        status="open", opened_on=date.today(),
        target_close=r.needed_from,
        hiring_manager_id=r.requested_by,
        recruiter_id=user.id,
        created_by=user.full_name)
    db.add(v); db.commit(); db.refresh(v)
    _ensure_public_id(db, "vacancy", v)
    r.status = "converted"
    r.vacancy_id = v.id
    db.commit()
    audit.log(db, user, entity="vacancy", action="create",
              entity_id=v.id, entity_label=v.public_id,
              note=f"{r.public_id} so'rovidan"
                   + ("" if r.status == "approved" else " (tasdiqsiz)"))
    return _vacancy_out(db, v)

@router.get("/api/hr/vacancies")
def hr_vacancies(status: str | None = None, branch_id: int | None = None,
                 only_open: int = 0, db: Session = Depends(get_db),
                 user=Depends(require_role(*roles.WORKFORCE_VIEW))):
    q = db.query(models.Vacancy)
    if user.role == roles.BRANCH_MANAGER and user.branch_id:
        q = q.filter(_branch_in(db, user, models.Vacancy.branch_id))
    elif branch_id:
        q = q.filter(models.Vacancy.branch_id == branch_id)
    if status:
        q = q.filter(models.Vacancy.status == status)
    rows = [_vacancy_out(db, v) for v in
            q.order_by(models.Vacancy.id.desc()).limit(300).all()]
    if only_open:
        rows = [r for r in rows if r["is_open"]]

    counts: dict = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    open_rows = [r for r in rows if r["is_open"]]
    return {
        "rows": rows,
        "statuses": [{"key": k, "label": l, "tone": t,
                      "count": counts.get(k, 0)}
                     for k, l, t in roles.VACANCY_STATES],
        "close_reasons": [{"key": k, "label": l}
                          for k, l in roles.VACANCY_CLOSE_REASONS],
        "summary": {
            "open": len(open_rows),
            "critical": sum(1 for r in open_rows
                            if r["priority"] == "critical"),
            "overdue": sum(1 for r in open_rows if r["overdue"]),
            "seats": sum(r["headcount"] - r["hired_count"]
                         for r in open_rows),
            "applications": sum(r["applications"] for r in open_rows),
            "avg_days_open": (round(sum(r["days_open"] for r in open_rows)
                                    / len(open_rows), 1)
                              if open_rows else 0.0),
        },
        "can_edit": user.role in roles.VACANCY_MANAGE,
        "hint": ("Vakansiya belgilangan muddatdan uzoq ochiq qolsa "
                 "ogohlantiriladi: kritik — 7 kun, yuqori — 14, "
                 "oddiy — 30."),
    }

@router.get("/api/hr/vacancies/{vid}")
def hr_vacancy_one(vid: int, db: Session = Depends(get_db),
                   user=Depends(require_role(*roles.WORKFORCE_VIEW))):
    v = db.query(models.Vacancy).get(vid)
    if not v:
        raise HTTPException(404, "Topilmadi")
    if user.role == roles.BRANCH_MANAGER \
            and not _in_user_branches(db, user, v.branch_id):
        raise HTTPException(403, "Bu boshqa filialning vakansiyasi")
    return _vacancy_out(db, v)

@router.put("/api/hr/vacancies/{vid}")
def hr_vacancy_edit(vid: int, payload: schemas.VacancyHrIn,
                    db: Session = Depends(get_db),
                    user=Depends(require_role(*roles.VACANCY_MANAGE))):
    v = db.query(models.Vacancy).get(vid)
    if not v:
        raise HTTPException(404, "Topilmadi")
    data = payload.model_dump(exclude_unset=True)
    if data.get("priority") and data["priority"] not in roles.PRIORITY_LABELS:
        raise HTTPException(400, "Noma'lum muhimlik darajasi")
    for f, val in data.items():
        setattr(v, f, val)
    if data.get("position_id"):
        pos = db.query(models.Position).get(data["position_id"])
        if pos:
            v.role = pos.system_role
            if not v.title:
                v.title = pos.name
    db.commit()
    audit.log(db, user, entity="vacancy", action="update",
              entity_id=vid, entity_label=v.public_id or v.title, commit=True)
    return _vacancy_out(db, v)

@router.post("/api/hr/vacancies/{vid}/status")
def hr_vacancy_status(vid: int, payload: schemas.VacancyStatusIn,
                      db: Session = Depends(get_db),
                      user=Depends(require_role(*roles.VACANCY_MANAGE))):
    v = db.query(models.Vacancy).get(vid)
    if not v:
        raise HTTPException(404, "Topilmadi")
    if payload.status not in roles.VACANCY_STATE_LABELS:
        raise HTTPException(400, "Noma'lum holat")
    closing = payload.status in ("closed", "cancelled", "filled")
    # Yopishda sabab majburiy — "nega yopildi?" savoli keyin
    # javobsiz qolmasin
    if closing and payload.status != "filled" and not payload.close_reason:
        raise HTTPException(400, "Yopish sababini ko'rsating")
    if payload.close_reason and payload.close_reason not in \
            roles.CLOSE_REASON_LABELS:
        raise HTTPException(400, "Noma'lum sabab")

    old = v.status
    v.status = payload.status
    if closing:
        v.closed_at = date.today()
        v.close_reason = payload.close_reason or "filled"
    elif old in ("closed", "cancelled", "filled"):
        # Qayta ochilsa yopilish belgilari tozalanadi
        v.closed_at = None
        v.close_reason = None
        if not v.opened_on:
            v.opened_on = date.today()
    db.commit()
    audit.log(db, user, entity="vacancy", action="status",
              entity_id=vid, entity_label=v.public_id or v.title,
              field="status", old_value=old, new_value=v.status,
              note=payload.note, commit=True)
    return _vacancy_out(db, v)

def _doc_out(db: Session, d: models.EmployeeDocument) -> dict:
    today = roles.local_today()
    left = (d.expires_on - today).days if d.expires_on else None
    return {
        "id": d.id, "user_id": d.user_id,
        "kind": d.kind,
        "kind_label": roles.DOCUMENT_LABELS.get(d.kind, d.kind),
        "title": d.title, "number": d.number,
        "issued_on": d.issued_on.isoformat() if d.issued_on else None,
        "expires_on": d.expires_on.isoformat() if d.expires_on else None,
        "days_left": left,
        "expired": bool(left is not None and left < 0),
        "expiring": bool(left is not None
                         and 0 <= left <= roles.DOCUMENT_WARN_DAYS),
        "note": d.note,
    }

@router.get("/api/hr/documents")
def hr_documents(user_id: int | None = None,
                 db: Session = Depends(get_db),
                 user=Depends(require_role(*roles.LIFECYCLE_VIEW))):
    """Hujjatlar. Muddati tugayotganlar alohida — HR ularni quvib
    yurmasin, ro'yxat o'zi aytsin."""
    q = db.query(models.EmployeeDocument)
    if user_id:
        q = q.filter(models.EmployeeDocument.user_id == user_id)
    rows = [_doc_out(db, d) for d in
            q.order_by(models.EmployeeDocument.id.desc()).limit(500).all()]
    names = {u.id: u.full_name for u in db.query(models.User).all()}
    for r in rows:
        r["user"] = names.get(r["user_id"])
    return {
        "rows": rows,
        "expiring": [r for r in rows if r["expiring"]],
        "expired": [r for r in rows if r["expired"]],
        "kinds": [{"key": k, "label": l, "expires": k in
                   roles.DOCUMENT_EXPIRES}
                  for k, l, _e in roles.DOCUMENT_KINDS],
        "warn_days": roles.DOCUMENT_WARN_DAYS,
    }

@router.post("/api/hr/documents")
def hr_document_add(payload: schemas.DocumentIn,
                    db: Session = Depends(get_db),
                    user=Depends(require_role(*roles.HR_FULL))):
    if payload.kind not in roles.DOCUMENT_LABELS:
        raise HTTPException(400, "Hujjat turi noto'g'ri")
    if not db.query(models.User).get(payload.user_id):
        raise HTTPException(404, "Xodim topilmadi")
    if payload.kind in roles.DOCUMENT_EXPIRES and not payload.expires_on:
        raise HTTPException(
            400, f"'{roles.DOCUMENT_LABELS[payload.kind]}' uchun amal "
                 f"qilish muddati kiritilishi shart")
    d = models.EmployeeDocument(
        user_id=payload.user_id, kind=payload.kind,
        title=payload.title, number=payload.number,
        issued_on=payload.issued_on, expires_on=payload.expires_on,
        note=payload.note, created_by=user.id)
    db.add(d); db.commit(); db.refresh(d)
    audit.log(db, user, entity="employee_document", action="create",
              entity_id=d.id, new_value=payload.kind, commit=True)
    return _doc_out(db, d)

@router.delete("/api/hr/documents/{did}")
def hr_document_delete(did: int, db: Session = Depends(get_db),
                       user=Depends(require_role(*roles.HR_FULL))):
    d = db.query(models.EmployeeDocument).get(did)
    if not d:
        raise HTTPException(404, "Hujjat topilmadi")
    db.delete(d); db.commit()
    audit.log(db, user, entity="employee_document", action="delete",
              entity_id=did, commit=True)
    return {"ok": True}

def _probation_out(db: Session, p: models.ProbationCheck) -> dict:
    who = db.query(models.User).get(p.by_user_id) if p.by_user_id else None
    return {
        "id": p.id, "user_id": p.user_id, "month_no": p.month_no,
        "decision": p.decision,
        "decision_label": roles.PROBATION_LABELS.get(p.decision),
        "decision_tone": roles.PROBATION_TONE.get(p.decision, "slate"),
        "final": p.decision in roles.PROBATION_FINAL,
        "strengths": p.strengths, "concerns": p.concerns, "note": p.note,
        "by": who.full_name if who else None,
        "at": p.created_at.isoformat() if p.created_at else None,
    }

@router.get("/api/hr/probation/{user_id}")
def hr_probation(user_id: int, db: Session = Depends(get_db),
                 user=Depends(require_role(*roles.LIFECYCLE_VIEW))):
    rows = (db.query(models.ProbationCheck)
            .filter(models.ProbationCheck.user_id == user_id)
            .order_by(models.ProbationCheck.month_no).all())
    out = [_probation_out(db, p) for p in rows]
    return {
        "rows": out,
        "closed": any(r["final"] for r in out),
        "decisions": [{"key": k, "label": l, "tone": t}
                      for k, l, t in roles.PROBATION_DECISIONS],
        "hint": ("Har oy alohida xulosa. Yakuniy qaror (o'tdi/o'tmadi) "
                 "qo'yilgach yozuvlar qulflanadi."),
    }

@router.post("/api/hr/probation")
def hr_probation_add(payload: schemas.ProbationIn,
                     db: Session = Depends(get_db),
                     user=Depends(require_role(*roles.LIFECYCLE_VIEW))):
    if payload.decision not in roles.PROBATION_LABELS:
        raise HTTPException(400, "Qaror noto'g'ri")
    if not db.query(models.User).get(payload.user_id):
        raise HTTPException(404, "Xodim topilmadi")
    done = db.query(models.ProbationCheck).filter(
        models.ProbationCheck.user_id == payload.user_id,
        models.ProbationCheck.decision.in_(roles.PROBATION_FINAL)).first()
    if done:
        raise HTTPException(
            400, "Sinov muddati allaqachon yakunlangan — tarix qayta "
                 "yozilmaydi")
    p = models.ProbationCheck(
        user_id=payload.user_id, month_no=payload.month_no,
        decision=payload.decision, strengths=payload.strengths,
        concerns=payload.concerns, note=payload.note, by_user_id=user.id)
    db.add(p); db.commit(); db.refresh(p)
    audit.log(db, user, entity="probation", action="check",
              entity_id=p.id, new_value=payload.decision, commit=True)
    return _probation_out(db, p)

def _leave_out(db: Session, l: models.LeaveRequest) -> dict:
    u = db.query(models.User).get(l.user_id)
    rep = (db.query(models.Teacher).get(l.replacement_teacher_id)
           if l.replacement_teacher_id else None)
    who = db.query(models.User).get(l.decided_by) if l.decided_by else None
    return {
        "id": l.id, "public_id": l.public_id,
        "user_id": l.user_id, "user": u.full_name if u else None,
        "branch_id": l.branch_id,
        "kind": l.kind, "kind_label": roles.LEAVE_LABELS.get(l.kind),
        "paid": roles.LEAVE_PAID.get(l.kind, False),
        "date_from": l.date_from.isoformat() if l.date_from else None,
        "date_to": l.date_to.isoformat() if l.date_to else None,
        "days": l.days,
        "reason": l.reason,
        "replacement_teacher_id": l.replacement_teacher_id,
        "replacement": rep.full_name if rep else None,
        "replacement_note": l.replacement_note,
        "status": l.status,
        "status_label": roles.LEAVE_STATUS_LABELS.get(l.status),
        "status_tone": roles.LEAVE_STATUS_TONE.get(l.status, "slate"),
        "decided_by": who.full_name if who else None,
        "decision_note": l.decision_note,
        "created_at": l.created_at.isoformat() if l.created_at else None,
    }

@router.get("/api/hr/leaves")
def hr_leaves(status: str | None = None, user_id: int | None = None,
              db: Session = Depends(get_db),
              user=Depends(get_current_user)):
    """Ta'til so'rovlari. Oddiy xodim faqat o'zinikini ko'radi."""
    q = db.query(models.LeaveRequest)
    if user.role not in tuple(roles.LEAVE_APPROVE):
        q = q.filter(models.LeaveRequest.user_id == user.id)
    elif user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
        q = q.filter(_branch_in(db, user, models.LeaveRequest.branch_id))
    if status:
        q = q.filter(models.LeaveRequest.status == status)
    if user_id and user.role in tuple(roles.LEAVE_APPROVE):
        q = q.filter(models.LeaveRequest.user_id == user_id)
    rows = [_leave_out(db, l) for l in
            q.order_by(models.LeaveRequest.id.desc()).limit(200).all()]

    today = roles.local_today()
    return {
        "rows": rows,
        "pending": [r for r in rows if r["status"] == "pending"],
        "today": [r for r in rows if r["status"] == "approved"
                  and r["date_from"] <= today.isoformat()
                  <= r["date_to"]],
        "kinds": [{"key": k, "label": l, "paid": p, "limit_days": d}
                  for k, l, p, d in roles.LEAVE_KINDS],
        "can_approve": user.role in tuple(roles.LEAVE_APPROVE),
        "min_notice_days": roles.LEAVE_MIN_NOTICE_DAYS,
        "hint": ("Ustoz ta'tilga chiqsa darslari egasiz qolmasin — "
                 "o'rinbosar ko'rsatiladi. Kasallikdan tashqari "
                 f"kamida {roles.LEAVE_MIN_NOTICE_DAYS} kun oldin "
                 "so'raladi."),
    }

@router.post("/api/hr/leaves")
def hr_leave_add(payload: schemas.LeaveIn,
                 db: Session = Depends(get_db),
                 user=Depends(get_current_user)):
    target_id = payload.user_id or user.id
    # Birovga so'rov ochish faqat HR/rahbariyatga
    if target_id != user.id and user.role not in tuple(roles.LEAVE_APPROVE):
        raise HTTPException(403, "Faqat o'zingiz uchun so'rov ochasiz")
    target = db.query(models.User).get(target_id)
    if not target:
        raise HTTPException(404, "Xodim topilmadi")
    if payload.kind not in roles.LEAVE_LABELS:
        raise HTTPException(400, "Ta'til turi noto'g'ri")
    if payload.date_to < payload.date_from:
        raise HTTPException(400, "Tugash sanasi boshlanishidan oldin")

    today = roles.local_today()
    days = (payload.date_to - payload.date_from).days + 1
    # Kasallik oldindan rejalashtirimaydi — unga muhlat talabi yo'q
    if payload.kind != "sick":
        if (payload.date_from - today).days < roles.LEAVE_MIN_NOTICE_DAYS:
            raise HTTPException(
                400, f"Kamida {roles.LEAVE_MIN_NOTICE_DAYS} kun oldin "
                     f"so'raladi — o'rinbosar topishga vaqt kerak")

    # Yillik chegara
    limit = roles.LEAVE_LIMIT.get(payload.kind)
    if limit:
        year_start = today.replace(month=1, day=1)
        used = sum((l.days or 0) for l in db.query(models.LeaveRequest)
                   .filter(models.LeaveRequest.user_id == target_id,
                           models.LeaveRequest.kind == payload.kind,
                           models.LeaveRequest.status == "approved",
                           models.LeaveRequest.date_from >= year_start)
                   .all())
        if used + days > limit:
            raise HTTPException(
                400, f"Yillik chegara: {limit} kun. Ishlatilgan: {used}, "
                     f"so'ralayotgan: {days}")

    # Ustoz bo'lsa — o'rinbosarsiz so'rov qabul qilinmaydi
    t = _teacher_of_user(db, target)
    if t and _my_groups(db, t.id) and not payload.replacement_teacher_id:
        raise HTTPException(
            400, "Sizda guruhlar bor — darslarni kim olib turishini "
                 "ko'rsating, aks holda darslar egasiz qoladi")
    if payload.replacement_teacher_id:
        rep = db.query(models.Teacher).get(payload.replacement_teacher_id)
        if not rep or not rep.is_active:
            raise HTTPException(400, "O'rinbosar ustoz topilmadi")
        if t and rep.id == t.id:
            raise HTTPException(400, "O'zingizni o'rinbosar qilib "
                                     "bo'lmaydi")

    l = models.LeaveRequest(
        user_id=target_id, branch_id=target.branch_id,
        kind=payload.kind, date_from=payload.date_from,
        date_to=payload.date_to, days=days, reason=payload.reason,
        replacement_teacher_id=payload.replacement_teacher_id,
        replacement_note=payload.replacement_note,
        status="pending")
    db.add(l); db.commit(); db.refresh(l)
    _ensure_public_id(db, "leave", l)
    db.commit(); db.refresh(l)

    _hr_task(db, title=f"Ta'til so'rovi {l.public_id}",
             body=(f"{target.full_name} — "
                   f"{roles.LEAVE_LABELS.get(payload.kind)}. "
                   f"{roles.uz_date_full(payload.date_from)} — "
                   f"{roles.uz_date_full(payload.date_to)} ({days} kun)."),
             to_roles=roles.LEAVE_APPROVE, branch_id=target.branch_id,
             days=2, priority="high")
    db.commit()
    audit.log(db, user, entity="leave", action="create", entity_id=l.id,
              entity_label=target.full_name,
              new_value=f"{payload.kind} {days} kun", commit=True)
    return _leave_out(db, l)

@router.post("/api/hr/leaves/{lid}/decide")
def hr_leave_decide(lid: int, payload: schemas.LeaveDecision,
                    db: Session = Depends(get_db),
                    user=Depends(require_role(*roles.LEAVE_APPROVE))):
    l = db.query(models.LeaveRequest).get(lid)
    if not l:
        raise HTTPException(404, "So'rov topilmadi")
    if l.status != "pending":
        raise HTTPException(400, "So'rov allaqachon ko'rilgan")
    if payload.decision not in ("approved", "rejected"):
        raise HTTPException(400, "Qaror noto'g'ri")
    # O'z so'rovini o'zi tasdiqlamaydi
    if l.user_id == user.id:
        raise HTTPException(403, "O'z so'rovingizni o'zingiz "
                                 "tasdiqlay olmaysiz")
    l.status = payload.decision
    l.decided_by = user.id
    l.decided_at = datetime.utcnow()
    l.decision_note = payload.note
    db.commit(); db.refresh(l)

    # Tasdiqlangach ta'til davridagi darslar o'rinbosarga o'tadi
    if payload.decision == "approved" and l.replacement_teacher_id:
        target = db.query(models.User).get(l.user_id)
        t = _teacher_of_user(db, target) if target else None
        if t:
            moved = 0
            for ls in db.query(models.Lesson).filter(
                    models.Lesson.teacher_id == t.id,
                    models.Lesson.held == 0,
                    models.Lesson.date >= l.date_from,
                    models.Lesson.date <= l.date_to).all():
                ls.teacher_id = l.replacement_teacher_id
                ls.note = ((ls.note or "")
                           + f" · o'rinbosar (ta'til {l.public_id})").strip()
                moved += 1
            db.commit()
    audit.log(db, user, entity="leave", action=payload.decision,
              entity_id=l.id, note=payload.note, commit=True)
    return _leave_out(db, l)

@router.get("/api/hr/reviews/{user_id}")
def hr_reviews(user_id: int, db: Session = Depends(get_db),
               user=Depends(require_role(*roles.LIFECYCLE_VIEW))):
    rows = (db.query(models.PerformanceReview)
            .filter(models.PerformanceReview.user_id == user_id)
            .order_by(models.PerformanceReview.id.desc()).all())
    out = []
    for r in rows:
        try:
            scores = json.loads(r.scores) if r.scores else {}
        except Exception:
            scores = {}
        out.append({
            "id": r.id, "period": r.period, "scores": scores,
            "percent": r.percent, "status": r.status,
            "locked": r.status == "final",
            "strengths": r.strengths, "to_improve": r.to_improve,
            "goals": r.goals,
            "finalized_at": (r.finalized_at.isoformat()
                             if r.finalized_at else None),
        })
    return {
        "rows": out,
        "criteria": [{"key": k, "label": l, "weight": w}
                     for k, l, w in roles.REVIEW_CRITERIA],
        "hint": ("Baholash yakunlangach QULFLANADI — tarix qayta "
                 "yozilmaydi."),
    }

@router.post("/api/hr/reviews")
def hr_review_save(payload: schemas.ReviewIn,
                   db: Session = Depends(get_db),
                   user=Depends(require_role(*roles.LIFECYCLE_VIEW))):
    if not db.query(models.User).get(payload.user_id):
        raise HTTPException(404, "Xodim topilmadi")
    clean = {}
    for k, v in (payload.scores or {}).items():
        if k not in roles.REVIEW_LABELS or v is None:
            continue
        iv = int(v)
        if not (1 <= iv <= 5):
            raise HTTPException(400, "Baho 1 dan 5 gacha")
        clean[k] = iv

    r = db.query(models.PerformanceReview).filter(
        models.PerformanceReview.user_id == payload.user_id,
        models.PerformanceReview.period == payload.period).first()
    if r and r.status == "final":
        raise HTTPException(400, "Bu davr yakunlangan — qulflangan "
                                 "baholash o'zgartirilmaydi")
    if not r:
        r = models.PerformanceReview(user_id=payload.user_id,
                                     period=payload.period)
        db.add(r)
    r.scores = json.dumps(clean, ensure_ascii=False)
    r.percent = roles.review_percent(clean)
    r.strengths = payload.strengths
    r.to_improve = payload.to_improve
    r.goals = payload.goals
    r.by_user_id = user.id
    if payload.finalize:
        r.status = "final"
        r.finalized_at = datetime.utcnow()
    db.commit(); db.refresh(r)
    audit.log(db, user, entity="review", action="save", entity_id=r.id,
              new_value=f"{payload.period} · {r.percent}%"
                        + (" · yakunlandi" if payload.finalize else ""),
              commit=True)
    return {"id": r.id, "percent": r.percent, "status": r.status}

@router.get("/api/hr/one-on-ones/{user_id}")
def hr_one_on_ones(user_id: int, db: Session = Depends(get_db),
                   user=Depends(get_current_user)):
    rows = (db.query(models.OneOnOne)
            .filter(models.OneOnOne.user_id == user_id)
            .order_by(models.OneOnOne.id.desc()).all())
    out = []
    for o in rows:
        # MAXFIY 1:1 ni faqat ikkala ishtirokchi o'qiydi — HR ham emas.
        # Ishonch shu bilan quriladi.
        if o.privacy == "private" and user.id not in (o.user_id,
                                                      o.manager_id):
            continue
        mgr = (db.query(models.User).get(o.manager_id)
               if o.manager_id else None)
        out.append({
            "id": o.id, "date": o.date.isoformat() if o.date else None,
            "privacy": o.privacy,
            "manager": mgr.full_name if mgr else None,
            "notes": o.notes, "agreements": o.agreements,
        })
    return {"rows": out,
            "privacy_options": [{"key": k, "label": l}
                                for k, l in roles.ONE_ON_ONE_PRIVACY]}

@router.post("/api/hr/one-on-ones")
def hr_one_on_one_add(payload: schemas.OneOnOneIn,
                      db: Session = Depends(get_db),
                      user=Depends(get_current_user)):
    if not db.query(models.User).get(payload.user_id):
        raise HTTPException(404, "Xodim topilmadi")
    o = models.OneOnOne(
        user_id=payload.user_id, manager_id=user.id,
        date=payload.date or roles.local_today(),
        privacy=payload.privacy if payload.privacy in ("open", "private")
        else "open",
        notes=payload.notes, agreements=payload.agreements)
    db.add(o); db.commit(); db.refresh(o)
    return {"ok": True, "id": o.id}

@router.get("/api/hr/pips")
def hr_pips(db: Session = Depends(get_db),
            user=Depends(require_role(*roles.HR_FULL))):
    rows = db.query(models.Pip).order_by(models.Pip.id.desc()).all()
    names = {u.id: u.full_name for u in db.query(models.User).all()}
    return {"rows": [{
        "id": p.id, "user_id": p.user_id, "user": names.get(p.user_id),
        "reason": p.reason, "goals": p.goals,
        "date_from": p.date_from.isoformat() if p.date_from else None,
        "date_to": p.date_to.isoformat() if p.date_to else None,
        "status": p.status,
        "status_label": roles.PIP_LABELS.get(p.status),
        "outcome_note": p.outcome_note,
    } for p in rows]}

@router.post("/api/hr/pips")
def hr_pip_add(payload: schemas.PipIn, db: Session = Depends(get_db),
               user=Depends(require_role(*roles.HR_FULL))):
    if not db.query(models.User).get(payload.user_id):
        raise HTTPException(404, "Xodim topilmadi")
    open_pip = db.query(models.Pip).filter(
        models.Pip.user_id == payload.user_id,
        models.Pip.status == "active").first()
    if open_pip:
        raise HTTPException(400, "Bu xodimda faol PIP allaqachon bor")
    p = models.Pip(user_id=payload.user_id, reason=payload.reason,
                   goals=payload.goals, date_from=payload.date_from,
                   date_to=payload.date_to, by_user_id=user.id)
    db.add(p); db.commit(); db.refresh(p)
    audit.log(db, user, entity="pip", action="create", entity_id=p.id,
              commit=True)
    return {"ok": True, "id": p.id}

@router.post("/api/hr/pips/{pid}/close")
def hr_pip_close(pid: int, payload: schemas.PipClose,
                 db: Session = Depends(get_db),
                 user=Depends(require_role(*roles.HR_FULL))):
    p = db.query(models.Pip).get(pid)
    if not p:
        raise HTTPException(404, "PIP topilmadi")
    if p.status != "active":
        raise HTTPException(400, "PIP allaqachon yopilgan")
    if payload.status not in ("passed", "failed"):
        raise HTTPException(400, "Yakun noto'g'ri")
    p.status = payload.status
    p.outcome_note = payload.note
    db.commit()
    audit.log(db, user, entity="pip", action=payload.status,
              entity_id=p.id, note=payload.note, commit=True)
    return {"ok": True, "status": p.status}

@router.get("/api/hr/relations/{user_id}")
def hr_relations(user_id: int, db: Session = Depends(get_db),
                 user=Depends(require_role(*roles.HR_FULL))):
    disc = db.query(models.DisciplinaryCase).filter(
        models.DisciplinaryCase.user_id == user_id).order_by(
        models.DisciplinaryCase.id.desc()).all()
    rec = db.query(models.Recognition).filter(
        models.Recognition.user_id == user_id).order_by(
        models.Recognition.id.desc()).all()
    return {
        "discipline": [{
            "id": d.id, "kind": d.kind,
            "kind_label": roles.DISCIPLINE_LABELS.get(d.kind),
            "reason": d.reason,
            "date": d.date.isoformat() if d.date else None,
        } for d in disc],
        "recognition": [{
            "id": r.id, "kind": r.kind,
            "kind_label": roles.RECOGNITION_LABELS.get(r.kind),
            "reason": r.reason, "amount": r.amount,
            "date": r.date.isoformat() if r.date else None,
        } for r in rec],
        "discipline_kinds": [{"key": k, "label": l}
                             for k, l in roles.DISCIPLINE_KINDS],
        "recognition_kinds": [{"key": k, "label": l}
                              for k, l in roles.RECOGNITION_KINDS],
    }

@router.post("/api/hr/discipline")
def hr_discipline_add(payload: schemas.DisciplineIn,
                      db: Session = Depends(get_db),
                      user=Depends(require_role(*roles.HR_FULL))):
    if payload.kind not in roles.DISCIPLINE_LABELS:
        raise HTTPException(400, "Turi noto'g'ri")
    d = models.DisciplinaryCase(
        user_id=payload.user_id, kind=payload.kind,
        reason=payload.reason,
        date=payload.date or roles.local_today(), by_user_id=user.id)
    db.add(d); db.commit()
    audit.log(db, user, entity="discipline", action="create",
              entity_id=d.id, new_value=payload.kind, commit=True)
    return {"ok": True, "id": d.id}

@router.post("/api/hr/recognition")
def hr_recognition_add(payload: schemas.RecognitionIn,
                       db: Session = Depends(get_db),
                       user=Depends(require_role(*roles.HR_FULL))):
    if payload.kind not in roles.RECOGNITION_LABELS:
        raise HTTPException(400, "Turi noto'g'ri")
    r = models.Recognition(
        user_id=payload.user_id, kind=payload.kind,
        reason=payload.reason, amount=payload.amount,
        date=payload.date or roles.local_today(), by_user_id=user.id)
    db.add(r); db.commit()
    audit.log(db, user, entity="recognition", action="create",
              entity_id=r.id, new_value=payload.kind, commit=True)
    return {"ok": True, "id": r.id}

def _offboard_out(db: Session, o: models.Offboarding) -> dict:
    u = db.query(models.User).get(o.user_id)
    try:
        steps = json.loads(o.steps) if o.steps else {}
    except Exception:
        steps = {}
    step_rows = [{"key": k, "label": l, "done": bool(steps.get(k))}
                 for k, l in roles.OFFBOARD_STEPS]
    return {
        "id": o.id, "user_id": o.user_id,
        "user": u.full_name if u else None,
        "last_day": o.last_day.isoformat() if o.last_day else None,
        "reason": o.reason,
        "reason_label": roles.EXIT_LABELS.get(o.reason or ""),
        "ours": (o.reason in roles.EXIT_OURS) if o.reason else None,
        "steps": step_rows,
        "done_count": sum(1 for s in step_rows if s["done"]),
        "total_steps": len(step_rows),
        "exit_notes": o.exit_notes,
        "would_return": (bool(o.would_return)
                         if o.would_return is not None else None),
        "completed": bool(o.completed),
    }

@router.get("/api/hr/offboarding")
def hr_offboarding_list(db: Session = Depends(get_db),
                        user=Depends(require_role(*roles.HR_FULL))):
    rows = [_offboard_out(db, o) for o in
            db.query(models.Offboarding).order_by(
                models.Offboarding.id.desc()).limit(100).all()]
    ours = [r for r in rows if r["ours"]]
    return {
        "rows": rows,
        "active": [r for r in rows if not r["completed"]],
        # Ketishlarning qanchasi BIZGA bog'liq — ishlash mumkin
        # bo'lgan yagona qism shu
        "ours_percent": (round(len(ours) / len(rows) * 100, 1)
                         if rows else None),
        "reasons": [{"key": k, "label": l, "ours": o}
                    for k, l, o in roles.EXIT_REASONS],
        "hint": ("Chiqish suhbatining maqsadi — ayblash emas, TIZIMNI "
                 "tuzatish. Sabab bizga bog'liq bo'lsa (ish haqi, "
                 "rahbariyat, yuk) bu keyingi ketishning oldini olish "
                 "imkoni."),
    }

@router.post("/api/hr/offboarding")
def hr_offboard_start(payload: schemas.OffboardIn,
                      db: Session = Depends(get_db),
                      user=Depends(require_role(*roles.HR_FULL))):
    target = db.query(models.User).get(payload.user_id)
    if not target:
        raise HTTPException(404, "Xodim topilmadi")
    if db.query(models.Offboarding).filter(
            models.Offboarding.user_id == payload.user_id,
            models.Offboarding.completed == 0).first():
        raise HTTPException(400, "Bu xodim uchun jarayon allaqachon "
                                 "boshlangan")
    o = models.Offboarding(
        user_id=payload.user_id, branch_id=target.branch_id,
        last_day=payload.last_day, reason=payload.reason,
        steps=json.dumps({"notice": 1}), by_user_id=user.id)
    db.add(o); db.commit(); db.refresh(o)
    audit.log(db, user, entity="offboarding", action="start",
              entity_id=o.id, entity_label=target.full_name,
              new_value=payload.reason, commit=True)
    return _offboard_out(db, o)

@router.post("/api/hr/offboarding/{oid}/update")
def hr_offboard_update(oid: int, payload: schemas.OffboardUpdate,
                       db: Session = Depends(get_db),
                       user=Depends(require_role(*roles.HR_FULL))):
    o = db.query(models.Offboarding).get(oid)
    if not o:
        raise HTTPException(404, "Jarayon topilmadi")
    if o.completed:
        raise HTTPException(400, "Jarayon yakunlangan")
    try:
        steps = json.loads(o.steps) if o.steps else {}
    except Exception:
        steps = {}
    if payload.step:
        if payload.step not in roles.OFFBOARD_LABELS:
            raise HTTPException(400, "Bunday band yo'q")
        steps[payload.step] = 1 if payload.done in (None, True) else 0
        o.steps = json.dumps(steps)
    if payload.exit_notes is not None:
        o.exit_notes = payload.exit_notes
    if payload.would_return is not None:
        o.would_return = 1 if payload.would_return else 0
    if payload.reason is not None:
        o.reason = payload.reason

    # Hammasi bajarilgach jarayon yopiladi va HISOB O'CHIRILADI —
    # ketgan odamning kirishi ochiq qolmasin
    if all(steps.get(k) for k, _l in roles.OFFBOARD_STEPS):
        o.completed = 1
        target = db.query(models.User).get(o.user_id)
        if target and target.role != roles.FOUNDER:
            target.is_active = 0
        t = _teacher_of_user(db, target) if target else None
        if t:
            t.is_active = 0
            t.left_date = o.last_day or roles.local_today()
    db.commit(); db.refresh(o)
    audit.log(db, user, entity="offboarding", action="update",
              entity_id=o.id, new_value=payload.step, commit=True)
    return _offboard_out(db, o)

@router.get("/api/hr/overview")
def hr_overview(db: Session = Depends(get_db),
                user=Depends(require_role(*roles.HR_FULL))):
    today = roles.local_today()
    soon = today + timedelta(days=roles.DOCUMENT_WARN_DAYS)

    staff = db.query(models.User).filter(
        models.User.is_active == 1).count()
    open_vac = db.query(models.Vacancy).filter(
        models.Vacancy.status.in_(tuple(roles.VACANCY_OPEN_STATES))
    ).count() if hasattr(roles, "VACANCY_OPEN_STATES") else 0

    apps = db.query(models.CandidateApplication).all()
    open_apps = [a for a in apps
                 if a.stage not in roles.APPLICATION_CLOSED]
    overdue = 0
    for a in open_apps:
        sla = roles.APPLICATION_SLA.get(a.stage)
        since = a.stage_since or (a.created_at.date()
                                  if a.created_at else today)
        if sla and (today - since).days > sla:
            overdue += 1

    docs_expiring = db.query(models.EmployeeDocument).filter(
        models.EmployeeDocument.expires_on.isnot(None),
        models.EmployeeDocument.expires_on >= today,
        models.EmployeeDocument.expires_on <= soon).count()
    docs_expired = db.query(models.EmployeeDocument).filter(
        models.EmployeeDocument.expires_on.isnot(None),
        models.EmployeeDocument.expires_on < today).count()

    leaves_pending = db.query(models.LeaveRequest).filter(
        models.LeaveRequest.status == "pending").count()
    on_leave = db.query(models.LeaveRequest).filter(
        models.LeaveRequest.status == "approved",
        models.LeaveRequest.date_from <= today,
        models.LeaveRequest.date_to >= today).count()

    interviews_today = db.query(models.Interview).filter(
        models.Interview.date == today,
        models.Interview.status == "planned").count()
    offers_pending = db.query(models.Offer).filter(
        models.Offer.status == "approval").count()
    pips_active = db.query(models.Pip).filter(
        models.Pip.status == "active").count()
    offboardings = db.query(models.Offboarding).filter(
        models.Offboarding.completed == 0).count()

    # Voronka samaradorligi: yollash qancha vaqt oladi
    hired_logs = db.query(models.ApplicationStageLog).filter(
        models.ApplicationStageLog.to_stage == "hired").all()
    tth = []
    for lg in hired_logs:
        a = db.query(models.CandidateApplication).get(lg.application_id)
        if a and a.created_at and lg.created_at:
            tth.append((lg.created_at - a.created_at).days)
    time_to_hire = round(sum(tth) / len(tth), 1) if tth else None

    # Rad sabablari — "nega odam topolmayapmiz"ga javob
    reasons = {}
    for a in apps:
        if a.stage == "rejected" and a.reject_reason:
            reasons[a.reject_reason] = reasons.get(a.reject_reason, 0) + 1

    alerts = []
    if overdue:
        alerts.append({"tone": "red", "text":
                       f"{overdue} ariza SLA muddatidan o'tib ketdi — "
                       f"nomzod kutib charchaydi"})
    if docs_expired:
        alerts.append({"tone": "red", "text":
                       f"{docs_expired} hujjatning muddati O'TGAN"})
    if docs_expiring:
        alerts.append({"tone": "amber", "text":
                       f"{docs_expiring} hujjat muddati "
                       f"{roles.DOCUMENT_WARN_DAYS} kun ichida tugaydi"})
    if leaves_pending:
        alerts.append({"tone": "amber", "text":
                       f"{leaves_pending} ta'til so'rovi javob kutmoqda"})
    if offers_pending:
        alerts.append({"tone": "amber", "text":
                       f"{offers_pending} taklif rahbariyat tasdig'ini "
                       f"kutmoqda"})

    return {
        "cards": [
            {"key": "staff", "label": "Faol xodimlar", "value": staff},
            {"key": "vacancies", "label": "Ochiq vakansiyalar",
             "value": open_vac},
            {"key": "pipeline", "label": "Ochiq arizalar",
             "value": len(open_apps)},
            {"key": "interviews", "label": "Bugungi suhbatlar",
             "value": interviews_today},
            {"key": "on_leave", "label": "Bugun ta'tilda",
             "value": on_leave},
            {"key": "pips", "label": "Faol PIP", "value": pips_active},
            {"key": "offboarding", "label": "Ketish jarayonida",
             "value": offboardings},
            {"key": "tth", "label": "O'rtacha yollash (kun)",
             "value": time_to_hire if time_to_hire is not None else "—"},
        ],
        "alerts": alerts,
        "reject_reasons": [
            {"key": k, "label": roles.REJECT_LABELS.get(k, k),
             "count": v}
            for k, v in sorted(reasons.items(), key=lambda x: -x[1])],
        "hint": ("Bitta ekran: yollash, hujjatlar, ta'til, performance "
                 "va ketish signallari. Qizil — bugun qilinadigan ish."),
    }



def _support_load(db: Session, branch_id=None) -> list[dict]:
    """Supportlarning yuklamasi (2026-08-12, Jahongir: "xuddi shunaqa
    supportlarga ham ko'rinsa zo'r bo'larkan").

    Yuklama = biriktirilgan guruhlar soni (SupportAssignment).
    Norma: roles.SUPPORT_MAX_GROUPS (hozircha bitta umumiy chegara).
    """
    # Support = User roli support_teacher bo'lgan ustoz kartalari
    # (Teacher jadvalida alohida "kind" ustuni yo'q)
    q = (db.query(models.Teacher)
         .join(models.User, models.User.id == models.Teacher.user_id)
         .filter(models.Teacher.is_active == 1,
                 models.User.is_active == 1,
                 models.User.role == roles.SUPPORT_TEACHER))
    if branch_id:
        q = q.filter(models.Teacher.branch_id == branch_id)
    sups = q.all()
    if not sups:
        return []

    # user_id -> biriktirilgan faol guruhlar soni
    per_user: dict = {}
    rows = (db.query(models.SupportAssignment.user_id,
                     models.SupportAssignment.group_id)
            .join(models.Group,
                  models.Group.id == models.SupportAssignment.group_id)
            .all())
    for uid, gid in rows:
        per_user.setdefault(uid, set()).add(gid)

    # daraja yorlig'i (staff_grades)
    grade_of = {}
    try:
        for sg in db.query(models.StaffGrade).all():
            grade_of[sg.user_id] = sg.grade
    except Exception:
        pass
    rate_label = {}
    try:
        for r in db.query(models.StaffGradeRate).all():
            rate_label[r.key] = r.label
    except Exception:
        pass

    limit = roles.SUPPORT_MAX_GROUPS
    out = []
    for t in sups:
        cnt = len(per_user.get(t.user_id, set())) if t.user_id else 0
        pct = round(cnt / limit * 100, 1) if limit else 0.0
        key, label, tone = roles.utilization_band(pct)
        br = db.query(models.Branch).get(t.branch_id) if t.branch_id else None
        gk = grade_of.get(t.user_id, "volunteer")
        out.append({
            "teacher_id": t.id, "name": t.full_name,
            "branch": br.name if br else None,
            "branch_id": t.branch_id,
            "grade": gk,
            "grade_label": rate_label.get(gk, gk.capitalize() if gk else "—"),
            "groups": cnt, "max_groups": limit,
            "free_slots": max(0, limit - cnt),
            "percent": pct, "band": key, "band_label": label, "tone": tone,
        })
    out.sort(key=lambda r: -r["percent"])
    return out


_SUPPORT_LOAD_VIEW = tuple(dict.fromkeys(
    tuple(roles.WORKFORCE_VIEW) + (roles.HEAD_SUPPORT, roles.HR_MANAGER)))


@router.get("/api/hr/support-load")
def hr_support_load(branch_id: int | None = None,
                    db: Session = Depends(get_db),
                    user=Depends(require_role(*_SUPPORT_LOAD_VIEW))):
    """Support yuklamasi — HR, o'quv bo'limi va support manager uchun."""
    if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
        branch_id = branch_id or user.branch_id
    load = _support_load(db, branch_id)
    summary = {}
    for r in load:
        summary[r["band"]] = summary.get(r["band"], 0) + 1
    return {
        "rows": load,
        "summary": [{"key": k, "label": lbl, "tone": tn,
                     "count": summary.get(k, 0)}
                    for _lim, k, lbl, tn in roles.UTILIZATION_BANDS],
        "limit": roles.SUPPORT_MAX_GROUPS,
        "hint": (f"Norma: bitta supportga {roles.SUPPORT_MAX_GROUPS} "
                 "tagacha guruh. Yuklama biriktirilgan guruhlar "
                 "sonidan hisoblanadi."),
    }
