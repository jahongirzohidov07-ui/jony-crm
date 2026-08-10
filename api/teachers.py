"""Auto-extracted from main.py during refactor (split-main). Domain: teachers."""
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

def _sync_teacher_branches(db: Session, teacher, branch_ids: list):
    """Ustozning filiallar ro'yxatini yangilaydi. Birinchisi asosiy
    (Teacher.branch_id), qolganlari teacher_branches jadvalида."""
    db.query(models.TeacherBranch).filter(
        models.TeacherBranch.teacher_id == teacher.id).delete()
    seen = set()
    for bid in branch_ids:
        if not bid or bid in seen:
            continue
        seen.add(bid)
        if bid == teacher.branch_id:
            continue
        db.add(models.TeacherBranch(teacher_id=teacher.id, branch_id=bid))

def _teacher_branch_map(db: Session) -> dict:
    """teacher_id -> qo'shimcha filial idlari (teacher_branches dan)."""
    out = {}
    for tb in db.query(models.TeacherBranch).all():
        out.setdefault(tb.teacher_id, []).append(tb.branch_id)
    return out

@router.get("/api/teachers", response_model=List[schemas.TeacherOut])
def list_teachers(branch_id: Optional[int] = None,
                  db: Session = Depends(get_db),
                  user=Depends(get_current_user)):
    # O'Z-O'ZINI TUZATISH: ustoz/support ROLIDAGI hisobga karta
    # ochilmagan bo'lsa (eski yozuvlar, o'tkazib yuborilgan
    # migratsiya), shu yerda ochib yuboramiz — ro'yxat har doim
    # HR bo'limi bilan bir xil bo'ladi.
    _missing = (db.query(models.User)
                .filter(models.User.role.in_((roles.TEACHER,
                                              roles.SUPPORT_TEACHER)),
                        models.User.is_active == 1,
                        ~models.User.id.in_(
                            db.query(models.Teacher.user_id)
                            .filter(models.Teacher.user_id
                                    .isnot(None)))).all())
    if _missing:
        for _u in _missing:
            _ensure_teacher_card(db, _u)
        db.commit()
    extra = _teacher_branch_map(db)
    # Filialga bog'langan xodim: asosiy filiali YOKI qo'shimcha
    # filiallaridan biri unga tegishli ustozlarni ko'radi. Butun
    # tashkilotni ko'radigan xodim filtri (branch_id) ham shu mantiq
    # bilan ishlaydi.
    # IKKI FILIALLI XODIM (2026-08-10): ilgari faqat user.branch_id
    # tekshirilardi — ikki filialda ishlaydigan xodim ikkinchi filial
    # ustozlarini umuman ko'rmasdi. Endi barcha filiallari hisobga
    # olinadi (ro'yxatlar bilan bir xil qoida).
    want_ids = None
    if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
        want_ids = _user_branch_ids(db, user)
    elif branch_id:
        want_ids = [branch_id]
    if want_ids:
        rows = [t for t in db.query(models.Teacher)
                .order_by(models.Teacher.full_name).all()
                if t.branch_id in want_ids
                or any(b in want_ids for b in extra.get(t.id, []))]
    else:
        rows = (db.query(models.Teacher)
                .order_by(models.Teacher.full_name).all())
    # Loginni ko'rsatish uchun bitta so'rov — har bir ustoz uchun alohida
    # so'rov yubormaymiz.
    ids = [t.user_id for t in rows if t.user_id]
    linked = {u.id: u for u in db.query(models.User)
              .filter(models.User.id.in_(ids or [-1])).all()}
    logins = {uid: u.username for uid, u in linked.items()}
    bnames = {b.id: b.name for b in db.query(models.Branch).all()}
    out = []
    for t in rows:
        t.login = logins.get(t.user_id)
        item = schemas.TeacherOut.model_validate(t)
        lu = linked.get(t.user_id)
        item.kind = ("support" if lu and lu.role == roles.SUPPORT_TEACHER
                     else "teacher")
        # Yordamchi o'qituvchi ustozlik darajasi zinasida emas —
        # kartasida adashib daraja qolgan bo'lsa ham ko'rsatilmaydi.
        if item.kind == "support":
            item.grade = None
        all_ids = ([t.branch_id] if t.branch_id else []) + \
            [b for b in extra.get(t.id, []) if b != t.branch_id]
        item.branch_ids = all_ids
        item.branches_label = ", ".join(
            bnames.get(b, "?") for b in all_ids) or None
        out.append(item)
    return out

@router.post("/api/teachers", response_model=schemas.TeacherOut)
def create_teacher(
    payload: schemas.TeacherCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.STAFF_VIEWERS)),
):
    data = payload.model_dump()
    branch_ids = data.pop("branch_ids", None) or []
    if branch_ids and not data.get("branch_id"):
        data["branch_id"] = branch_ids[0]
    teacher = models.Teacher(**data)
    # Daraja tanlanmagan bo'lsa - birinchisidan boshlaydi. Stavkasi
    # shu darajadan chiqadi, ya'ni guruh ochishda hech narsa
    # kiritilmasa ham to'g'ri hisoblanadi.
    teacher.grade = teacher.grade or roles.FIRST_GRADE
    teacher.grade_since = teacher.hired_date or date.today()
    _sync_teacher_left_date(teacher)
    db.add(teacher)
    db.commit()
    db.refresh(teacher)
    db.add(models.TeacherGradeEvent(
        teacher_id=teacher.id, from_grade=None, to_grade=teacher.grade,
        kind="set", effective_from=teacher.grade_since,
        reason="Ishga qabul qilindi", decided_by=user.full_name))
    _sync_teacher_branches(db, teacher, branch_ids)
    db.commit()
    return teacher

@router.put("/api/teachers/{teacher_id}", response_model=schemas.TeacherOut)
def update_teacher(
    teacher_id: int,
    payload: schemas.TeacherCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.STAFF_VIEWERS)),
):
    teacher = db.query(models.Teacher).get(teacher_id)
    if not teacher:
        raise HTTPException(404, "O'qituvchi topilmadi")
    given = payload.model_dump(exclude_unset=True)
    new_grade = given.pop("grade", None)
    branch_ids = given.pop("branch_ids", None)
    if branch_ids:
        given["branch_id"] = branch_ids[0]
    for k, v in given.items():
        setattr(teacher, k, v)
    if branch_ids is not None:
        _sync_teacher_branches(db, teacher, branch_ids or [])
    _sync_teacher_left_date(teacher)

    # Daraja o'zgarsa - tarixga yoziladi va guruh stavkalari yangilanadi.
    if new_grade and new_grade != teacher.grade:
        if new_grade not in _grade_map(db):
            raise HTTPException(400, "Bunday daraja yo'q")
        _set_grade(db, teacher, new_grade, kind="set",
                   reason="Qo'lda o'zgartirildi", by=user.full_name)
    db.commit()
    db.refresh(teacher)
    return teacher

@router.delete("/api/teachers/{teacher_id}")
def delete_teacher(
    teacher_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FULL_ACCESS)),
):
    teacher = db.query(models.Teacher).get(teacher_id)
    if not teacher:
        raise HTTPException(404, "O'qituvchi topilmadi")
    db.delete(teacher)
    db.commit()
    return {"ok": True}

@router.get("/api/teachers/{teacher_id}/salary")
def teacher_salary(
    teacher_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.SALARY_SELF_VIEW)),
):
    t = db.query(models.Teacher).get(teacher_id)
    if not t:
        raise HTTPException(404, "Ustoz topilmadi")
    # Ustoz faqat o'zining oyligini ko'radi
    if user.role in (roles.TEACHER, roles.SUPPORT_TEACHER):
        me = _teacher_of_user(db, user)
        if not me or me.id != teacher_id:
            raise HTTPException(403, "Faqat o'z oyligingizni ko'ra olasiz")
    card = _salary_card(db, t)
    card["can_pay"] = user.role in tuple(roles.SALARY_PAY)
    return card

@router.post("/api/teachers/{teacher_id}/payments")
def pay_teacher(
    teacher_id: int,
    payload: schemas.TeacherPaymentCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.SALARY_PAY)),
):
    """Ustozga pul berish. Avans ishlab topilgan puldan oshmaydi —
    aks holda ustoz ketib qolsa pul qaytmaydi."""
    t = db.query(models.Teacher).get(teacher_id)
    if not t:
        raise HTTPException(404, "Ustoz topilmadi")
    if payload.kind not in roles.TEACHER_PAYMENT_LABELS:
        raise HTTPException(400, "Noto'g'ri to'lov turi")
    if not payload.amount or payload.amount <= 0:
        raise HTTPException(400, "Summani kiriting")

    earned = _teacher_earned(db, t.id)["amount"]
    paid = _teacher_paid(db, t.id)
    available = earned - paid
    if payload.kind == "advance" and payload.amount > available:
        raise HTTPException(
            400,
            f"Avans ishlab topilgan puldan ko'p bo'lmasligi kerak. "
            f"Hozirgacha ishlab topgani {earned:,.0f} so'm, olgani "
            f"{paid:,.0f} so'm — bera oladigan summa "
            f"{max(0, available):,.0f} so'm.".replace(",", " "))

    p = models.TeacherPayment(
        teacher_id=t.id, amount=payload.amount, kind=payload.kind,
        period=payload.period or date.today().isoformat()[:7],
        paid_on=payload.date or date.today(),
        method=payload.method, note=payload.note,
        created_by=user.full_name)
    db.add(p); db.commit(); db.refresh(p)
    audit.log(db, user, entity="teacher", action="salary_change",
              entity_id=t.id, entity_label=t.full_name,
              branch_id=t.branch_id,
              field=roles.TEACHER_PAYMENT_LABELS[payload.kind],
              new_value=f"{payload.amount:,.0f}".replace(",", " "))
    db.commit()
    return _salary_card(db, t)

def _teacher_stats(db: Session, months: int = 12,
                   branch_id: int | None = None,
                   user: models.User | None = None) -> list:
    today = date.today()
    y, m = _shift_month(today.year, today.month, -(max(1, months) - 1))
    start, _e = billing.month_bounds(y, m)

    tq = db.query(models.Teacher)
    if user is not None:
        tq = scope_to_branch(tq, models.Teacher, user, branch_id)
    elif branch_id:
        tq = tq.filter(models.Teacher.branch_id == branch_id)
    teachers = tq.all()

    groups = db.query(models.Group).all()
    students = db.query(models.Student).all()
    g_by_teacher: dict[int, list] = {}
    for g in groups:
        if g.teacher_id:
            g_by_teacher.setdefault(g.teacher_id, []).append(g)

    # Imtihon natijalari ustoz kesimida
    exam_by_teacher: dict[int, list] = {}
    exams = db.query(models.Exam).all()
    ex_group = {e.id: e.group_id for e in exams if e.date and e.date >= start}
    if ex_group:
        gmap = {g.id: g.teacher_id for g in groups}
        for r in db.query(models.ExamResult).filter(
                models.ExamResult.exam_id.in_(list(ex_group))).all():
            if r.absent or r.percent is None:
                continue
            tid = gmap.get(ex_group.get(r.exam_id))
            if tid:
                exam_by_teacher.setdefault(tid, []).append(r.percent)

    rows = []
    for t in teachers:
        gs = g_by_teacher.get(t.id, [])
        gids = {g.id for g in gs}
        mine = [s for s in students if s.group_id in gids]
        active = [s for s in mine if s.status == "active"]
        left = [s for s in mine if s.left_date and s.left_date >= start]

        # LTV: o'quvchi o'rtacha necha oy qoladi va qancha pul keltiradi
        spans, revenue = [], 0.0
        for s in mine:
            end_d = s.left_date or today
            if s.enrolled_date:
                spans.append(max(0.0, (end_d - s.enrolled_date).days / 30.4))
            revenue += sum(p.amount for p in
                           db.query(models.Payment).filter(
                               models.Payment.student_id == s.id,
                               models.Payment.kind == "payment").all())
        avg_months = round(sum(spans) / len(spans), 1) if spans else 0.0
        ltv = round(revenue / len(mine), 0) if mine else 0.0

        # Retention: qancha o'quvchi qoldi
        base = len(active) + len(left)
        retention = round(len(active) / base * 100, 1) if base else 0.0

        # Dars sifati: imtihon o'rtachasi
        marks = exam_by_teacher.get(t.id, [])
        quality = round(sum(marks) / len(marks), 1) if marks else None

        # Davomat
        att_rows = (db.query(models.Attendance, models.Lesson)
                    .join(models.Lesson,
                          models.Attendance.lesson_id == models.Lesson.id)
                    .filter(models.Lesson.group_id.in_(gids or [-1]),
                            models.Lesson.date >= start).all()) if gids else []
        marked = len(att_rows)
        present = sum(1 for a, _l in att_rows if a.present)
        attendance = round(present / marked * 100, 1) if marked else None

        rows.append({
            "teacher_id": t.id,
            "full_name": t.full_name,
            "branch": t.branch.name if t.branch else None,
            "branch_id": t.branch_id,
            "is_active": bool(t.is_active),
            "groups": len(gs),
            "students": len(active),
            "left": len(left),
            "quality": quality,
            "retention": retention,
            "ltv": ltv,
            "avg_months": avg_months,
            "attendance": attendance,
        })

    # Umumiy ball: sifat 40%, retention 30%, LTV 20%, davomat 10%
    max_ltv = max([r["ltv"] for r in rows] or [1]) or 1
    for r in rows:
        parts = {
            "quality": (r["quality"] or 50) if r["quality"] is not None else 50,
            "retention": r["retention"],
            "ltv": min(100.0, r["ltv"] / max_ltv * 100),
            "attendance": (r["attendance"]
                           if r["attendance"] is not None else 50),
        }
        r["parts"] = {k: round(v, 1) for k, v in parts.items()}
        r["score"] = round(sum(
            parts[k] * w / 100
            for k, w in roles.TEACHER_SCORE_DEFAULT.items()), 1)

    rows.sort(key=lambda r: -r["score"])
    for i, r in enumerate(rows, 1):
        r["rank"] = i
    return rows

@router.get("/api/teachers/{teacher_id}/career")
def teacher_career(
    teacher_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Bitta ustozning karyera kartasi: hozirgi daraja, nima
    yetishmayapti, tarix va o'qish rejasi."""
    t = db.query(models.Teacher).get(teacher_id)
    if not t:
        raise HTTPException(404, "Ustoz topilmadi")
    mine = _teacher_of_user(db, user)
    if user.role not in roles.CAREER_ACCESS and (
            not mine or mine.id != t.id):
        raise HTTPException(403, "Bu ma'lumot sizga ko'rinmaydi")

    st = _grade_state(db, t)
    history = (db.query(models.TeacherGradeEvent)
               .filter(models.TeacherGradeEvent.teacher_id == t.id)
               .order_by(models.TeacherGradeEvent.effective_from.desc(),
                         models.TeacherGradeEvent.id.desc()).all())

    stages = []
    for key, label, _b, _p in roles.STUDY_STAGES:
        items = _study_items(db, t, key)
        stages.append({
            "key": key, "label": label,
            "done": sum(1 for i in items if i.done),
            "total": len(items),
            "items": [{
                "id": i.id, "kind": i.kind, "title": i.title,
                "done": bool(i.done),
                "done_at": i.done_at.isoformat() if i.done_at else None,
                "note": i.note,
            } for i in sorted(items, key=lambda x: (x.kind != "book",
                                                    x.id))],
        })

    return {
        "state": st,
        "grades": [_grade_row_out(g) for g in _grade_rows(db)],
        "history": [{
            "id": e.id,
            "kind": e.kind,
            "kind_label": roles.GRADE_EVENT_LABELS.get(e.kind, e.kind),
            "tone": roles.GRADE_EVENT_TONE.get(e.kind, "slate"),
            "from_grade": e.from_grade,
            "from_label": roles.GRADE_LABELS.get(e.from_grade or ""),
            "to_grade": e.to_grade,
            "to_label": roles.GRADE_LABELS.get(e.to_grade or ""),
            "date": e.effective_from.isoformat() if e.effective_from else None,
            "reason": e.reason,
            "pass_rate": e.pass_rate,
            "test_avg": e.test_avg,
            "rate_before": e.rate_before,
            "rate_after": e.rate_after,
            "decided_by": e.decided_by,
        } for e in history],
        "study": stages,
        "entry": [{"key": k, "text": txt} for k, txt in roles.TEACHER_ENTRY],
        "observations": [_observation_out(db, o) for o in
                         (db.query(models.LessonObservation)
                          .filter(models.LessonObservation.teacher_id == t.id)
                          .order_by(models.LessonObservation.date.desc(),
                                    models.LessonObservation.id.desc())
                          .limit(20).all())],
        "can_edit": user.role in roles.GRADE_ADMIN,
        "is_me": bool(mine and mine.id == t.id),
    }

@router.post("/api/teachers/{teacher_id}/grade")
def set_teacher_grade(
    teacher_id: int,
    payload: schemas.GradeSet,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.GRADE_ADMIN)),
):
    """Darajani qo'lda qo'yish. Avtomat qaror noto'g'ri chiqqan bo'lsa
    shu yerdan qaytariladi."""
    t = db.query(models.Teacher).get(teacher_id)
    if not t:
        raise HTTPException(404, "Ustoz topilmadi")
    if payload.grade not in _grade_map(db):
        raise HTTPException(400, "Bunday daraja yo'q")
    if payload.grade == t.grade:
        return {"ok": True, "changed": False}
    _set_grade(db, t, payload.grade, kind="set",
               reason=payload.reason or "Qo'lda o'zgartirildi",
               by=user.full_name)
    db.commit()
    return {"ok": True, "changed": True,
            "grade": t.grade,
            "label": roles.GRADE_LABELS.get(t.grade, t.grade)}

@router.post("/api/teachers/{teacher_id}/remediation")
def clear_remediation(
    teacher_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.GRADE_ADMIN)),
):
    """Qayta test topshirildi — cheklovni olib tashlaymiz."""
    t = db.query(models.Teacher).get(teacher_id)
    if not t:
        raise HTTPException(404, "Ustoz topilmadi")
    t.remediation_until = None
    t.remediation_reason = None
    db.add(models.TeacherGradeEvent(
        teacher_id=t.id, from_grade=t.grade, to_grade=t.grade,
        kind="remediation_done", effective_from=date.today(),
        reason="Qayta test topshirildi", decided_by=user.full_name))
    db.commit()
    return {"ok": True}

@router.post("/api/teachers/{teacher_id}/study/{item_id}")
def mark_study(
    teacher_id: int,
    item_id: int,
    payload: schemas.StudyDone,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Kitob o'qildi / podkast ko'rildi. Ustoz o'zi belgilaydi."""
    item = db.query(models.TeacherStudyItem).get(item_id)
    if not item or item.teacher_id != teacher_id:
        raise HTTPException(404, "Topilmadi")
    mine = _teacher_of_user(db, user)
    if user.role not in roles.CAREER_ACCESS and (
            not mine or mine.id != teacher_id):
        raise HTTPException(403, "Faqat o'zingiznikini belgilay olasiz")
    item.done = 1 if payload.done else 0
    item.done_at = date.today() if payload.done else None
    if payload.note is not None:
        item.note = payload.note
    db.commit()
    return {"ok": True, "done": bool(item.done)}

@router.get("/api/teachers/scoreboard")
def teacher_scoreboard(
    months: int = 12,
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_ACCESS)),
):
    """Ustozlar reytingi: dars sifati, retention, LTV va davomat.

    Ustozning o'ziga ochiq — hamkasblari orasidagi o'rnini ko'rsin.
    Lekin ularning MAOSHI bu yerda yo'q."""
    rows = _teacher_stats(db, months=months, branch_id=branch_id, user=user)
    me = None
    if user.role in (roles.TEACHER, roles.SUPPORT_TEACHER):
        t = _teacher_of_user(db, user)
        if t:
            me = next((r["teacher_id"] for r in rows
                       if r["teacher_id"] == t.id), None)

    def avg(key):
        vals = [r[key] for r in rows if r.get(key) is not None]
        return round(sum(vals) / len(vals), 1) if vals else None

    return {
        "months": months,
        "rows": rows,
        "me": me,
        "count": len(rows),
        "dimensions": [{"key": k, "label": lbl, "weight": w}
                       for k, lbl, w in roles.TEACHER_SCORE_WEIGHTS],
        "averages": {
            "quality": avg("quality"),
            "retention": avg("retention"),
            "ltv": avg("ltv"),
            "attendance": avg("attendance"),
            "avg_months": avg("avg_months"),
            "score": avg("score"),
        },
    }

def _free_login(db: Session, base: str) -> str:
    """Band bo'lmagan login. Takrorlansa oxiriga raqam qo'shiladi."""
    base = (base or "xodim")[:40]
    login = base
    n = 1
    while db.query(models.User).filter(
            models.User.username == login).first():
        n += 1
        login = f"{base}{n}"
    return login

def _account_state(db: Session, t: models.Teacher) -> dict:
    u = db.query(models.User).get(t.user_id) if t.user_id else None
    if not u:
        # Eski yozuvlar: ism bo'yicha topilsa bog'lab qo'yiladi. Lekin
        # o'sha akkaunt BOSHQA ustozga biriktirilgan bo'lsa tegilmaydi
        # — ikki xil odam bitta login bilan kirib, birining oyligini
        # ikkinchisi ko'rib qolishi mumkin.
        cand = (db.query(models.User)
                .filter(models.User.full_name == t.full_name,
                        models.User.role == roles.TEACHER).all())
        taken = {tid for (tid,) in db.query(models.Teacher.user_id)
                 .filter(models.Teacher.user_id.isnot(None)).all()}
        u = next((x for x in cand if x.id not in taken), None)
        if u:
            t.user_id = u.id
            db.commit()
    return {
        "has_account": bool(u),
        "user_id": u.id if u else None,
        "login": u.username if u else None,
        "is_active": bool(u.is_active) if u else False,
        "role": u.role if u else None,
    }

@router.get("/api/teachers/{tid}/account")
def teacher_account(tid: int, db: Session = Depends(get_db),
                    user=Depends(require_role(*roles.ACCOUNT_MANAGE))):
    t = db.query(models.Teacher).get(tid)
    if not t:
        raise HTTPException(404, "Ustoz topilmadi")
    return _account_state(db, t)

@router.post("/api/teachers/{tid}/account")
def teacher_account_create(tid: int, db: Session = Depends(get_db),
                           user=Depends(require_role(*roles.ACCOUNT_MANAGE))):
    """Akkaunt ochadi va login/parolni BIR MARTA qaytaradi."""
    t = db.query(models.Teacher).get(tid)
    if not t:
        raise HTTPException(404, "Ustoz topilmadi")

    st = _account_state(db, t)
    if st["has_account"]:
        raise HTTPException(400, "Bu ustozda akkaunt bor. Parolni "
                                 "yangilash uchun \"Yangi parol\" bosing.")
    if not t.is_active:
        raise HTTPException(400, "Ishdan ketgan ustozga akkaunt "
                                 "ochilmaydi")

    login = _free_login(db, roles.login_from_name(t.full_name))
    password = roles.make_password()
    u = models.User(
        username=login,
        password_hash=hash_password(password),
        full_name=t.full_name,        # ustoz yozuvi bilan bir xil
        role=roles.TEACHER,
        branch_id=t.branch_id,
        phone=t.phone,
        hired_date=t.hired_date,
        # 1, True emas: Postgres'da bu ustun INTEGER — mantiqiy qiymat
        # qabul qilmaydi. SQLite qabul qiladi, shuning uchun xato faqat
        # jonli bazada chiqadi.
        is_active=1,
    )
    db.add(u); db.commit(); db.refresh(u)
    t.user_id = u.id
    db.commit()

    audit.log(db, user, entity="user", action="create", entity_id=u.id,
              entity_label=f"{t.full_name} — ustoz akkaunti",
              note="Avtomat ochildi")
    return {
        "created": True,
        "login": login,
        "password": password,
        "full_name": t.full_name,
        "url": os.environ.get("PUBLIC_URL", "https://jony-crm.vercel.app"),
        "warning": ("Parol shu yerda bir marta ko'rsatiladi. Yopilgach "
                    "uni hech kim — hatto asoschi ham — qayta ko'ra "
                    "olmaydi. Nusxalab ustozga bering."),
        **_account_state(db, t),
    }

@router.post("/api/teachers/{tid}/account/reset")
def teacher_account_reset(tid: int, db: Session = Depends(get_db),
                          user=Depends(require_role(*roles.ACCOUNT_MANAGE))):
    """Parolni unutgan bo'lsa — yangisi yasaladi. Login o'zgarmaydi."""
    t = db.query(models.Teacher).get(tid)
    if not t:
        raise HTTPException(404, "Ustoz topilmadi")
    st = _account_state(db, t)
    if not st["has_account"]:
        raise HTTPException(400, "Avval akkaunt oching")
    u = db.query(models.User).get(st["user_id"])
    password = roles.make_password()
    u.password_hash = hash_password(password)
    u.is_active = 1
    db.commit()
    audit.log(db, user, entity="user", action="password_reset",
              entity_id=u.id, entity_label=t.full_name,
              note="Yangi parol yasaldi")
    return {
        "created": False,
        "login": u.username,
        "password": password,
        "full_name": t.full_name,
        "url": os.environ.get("PUBLIC_URL", "https://jony-crm.vercel.app"),
        "warning": ("Eski parol endi ishlamaydi. Yangisini ustozga "
                    "bering — bu oyna yopilgach qayta ko'rinmaydi."),
        **_account_state(db, t),
    }

@router.get("/api/teachers/{teacher_id}/overview")
def teacher_overview(teacher_id: int,
                     db: Session = Depends(get_db),
                     user=Depends(require_role(
                         roles.FOUNDER, roles.ACADEMIC_HEAD))):
    """Asoschi va o'quv bo'limi rahbari ko'radigan umumiy karta:
    oylik va o'sishi, o'quvchilar soni, shartnoma/sertifikat muddati,
    tug'ilgan kun, guruhlar to'lganligi, dars sifati, daraja."""
    t = db.query(models.Teacher).get(teacher_id)
    if not t:
        raise HTTPException(404, "Ustoz topilmadi")
    today = roles.local_today()

    # Oxirgi 6 oy: oylik va o'quvchilar soni
    months = []
    for i in range(5, -1, -1):
        y, m = today.year, today.month - i
        while m <= 0:
            y, m = y - 1, m + 12
        s = date(y, m, 1)
        e = date(y + 1, 1, 1) if m == 12 else date(y, m + 1, 1)
        earned = _teacher_earned(db, t.id, since=s,
                                 until=min(e, today + timedelta(days=1)))
        cnt = (db.query(models.Attendance.student_id)
               .join(models.Lesson,
                     models.Lesson.id == models.Attendance.lesson_id)
               .filter(models.Lesson.teacher_id == t.id,
                       models.Lesson.date >= s, models.Lesson.date < e)
               .distinct().count())
        months.append({"label": f"{roles.UZ_MONTHS[m - 1][:3]} {y}",
                       "salary": round(earned.get("amount", 0), 0),
                       "students": cnt})

    # Guruhlar va to'lganlik
    rooms = {r.id: r for r in db.query(models.Room).all()}
    groups = db.query(models.Group).filter(
        models.Group.teacher_id == t.id).all()
    g_rows, total_cap, total_st = [], 0, 0
    for g in groups:
        cap = _group_capacity(g, rooms)
        st = db.query(models.Student).filter(
            models.Student.group_id == g.id,
            models.Student.status == "active").count()
        g_rows.append({"id": g.id, "name": g.name, "students": st,
                       "capacity": cap,
                       "free": (cap - st) if cap else None,
                       "fill": round(st / cap * 100, 0) if cap else None})
        total_st += st
        if cap:
            total_cap += cap

    # Hujjatlar: shartnoma va sertifikat muddati
    def _doc_left(kind):
        if not t.user_id:
            return None
        d = (db.query(models.EmployeeDocument)
             .filter(models.EmployeeDocument.user_id == t.user_id,
                     models.EmployeeDocument.kind == kind,
                     models.EmployeeDocument.expires_on.isnot(None))
             .order_by(models.EmployeeDocument.expires_on.desc()).first())
        if not d:
            return None
        return {"title": d.title or roles.DOCUMENT_LABELS.get(kind, kind),
                "expires_on": d.expires_on.isoformat(),
                "days_left": (d.expires_on - today).days}

    # Tug'ilgan kun
    bday = None
    if t.birth_date:
        try:
            this = t.birth_date.replace(year=today.year)
        except ValueError:
            this = date(today.year, 3, 1)   # 29-fevral
        passed = this < today
        bday = {"date": t.birth_date.isoformat(),
                "this_year": this.isoformat(),
                "passed": passed,
                "days": (today - this).days if passed
                else (this - today).days}

    # Dars sifati — kuzatuvlar o'rtachasi
    obs = db.query(models.LessonObservation).filter(
        models.LessonObservation.teacher_id == t.id,
        models.LessonObservation.max_total > 0).all()
    quality = round(sum(o.total / o.max_total for o in obs)
                    / len(obs) * 100, 1) if obs else None

    grade_label = None
    if t.grade:
        try:
            grade_label = roles.GRADE_LABELS.get(t.grade, t.grade)
        except AttributeError:
            grade_label = t.grade

    return {
        "id": t.id, "name": t.full_name,
        "months": months,
        "salary_now": months[-1]["salary"] if months else 0,
        "salary_growth": (months[-1]["salary"] - months[-2]["salary"])
        if len(months) >= 2 else 0,
        "students_now": total_st,
        "groups_count": len(groups),
        "groups": g_rows,
        "total_capacity": total_cap or None,
        "total_free": (total_cap - total_st) if total_cap else None,
        "fill_percent": round(total_st / total_cap * 100, 0)
        if total_cap else None,
        "contract": _doc_left("contract"),
        "certificate": _doc_left("certificate") or (
            {"title": t.cert, "expires_on": None, "days_left": None}
            if t.cert else None),
        "birthday": bday,
        "quality_percent": quality,
        "grade": t.grade, "grade_label": grade_label,
        "grade_since": t.grade_since.isoformat() if t.grade_since else None,
    }

@router.post("/api/teachers/import")
def import_teachers(payload: schemas.TeacherImportIn,
                    db: Session = Depends(get_db),
                    user=Depends(require_role(*roles.STAFF_VIEWERS))):
    today = roles.local_today()
    existing = db.query(models.Teacher).all()
    names = {(t.full_name or "").strip().lower() for t in existing}
    phones = set()
    for t in existing:
        d = "".join(ch for ch in (t.phone or "") if ch.isdigit())
        if len(d) >= 9:
            phones.add(d[-9:])

    results, created = [], 0
    for r in payload.rows:
        name = (r.full_name or "").strip()
        if not name:
            continue
        digits = "".join(ch for ch in (r.phone or "") if ch.isdigit())
        tail = digits[-9:] if len(digits) >= 9 else None
        if name.lower() in names:
            results.append({"name": name, "status": "skip",
                            "reason": "bu ism allaqachon bor"})
            continue
        if tail and tail in phones:
            results.append({"name": name, "status": "skip",
                            "reason": "bu telefon allaqachon bor"})
            continue

        # Tug'ilgan sana: LC UP bo'sh joyga eksport kunini yozadi —
        # yosh 14 dan kichik chiqsa, sana yo'q deb hisoblaymiz.
        bdate = None
        if r.birth_date:
            try:
                bdate = date.fromisoformat(str(r.birth_date)[:10])
                if bdate.year > today.year - 14:
                    bdate = None
            except ValueError:
                bdate = None

        t = models.Teacher(
            full_name=name,
            phone=r.phone or None,
            branch_id=payload.branch_id,
            birth_date=bdate,
            hired_date=today,
            is_active=1,
            grade=roles.FIRST_GRADE,
            grade_since=today,
        )
        db.add(t)
        db.flush()
        db.add(models.TeacherGradeEvent(
            teacher_id=t.id, from_grade=None, to_grade=t.grade,
            kind="set", effective_from=today,
            reason="Excel'dan import", decided_by=user.full_name))
        names.add(name.lower())
        if tail:
            phones.add(tail)
        created += 1
        results.append({"name": name, "status": "ok",
                        "note": (r.note or "").strip() or None})
    db.commit()
    audit.log(db, user, entity="teacher", action="import",
              entity_label=f"{created} ta ustoz",
              new_value=created, commit=True)
    return {"created": created, "results": results}

