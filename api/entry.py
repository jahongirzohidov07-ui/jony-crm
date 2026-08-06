"""JonyOS qo'shimcha moduli.

main.py juda katta bo'lib GitHub orqali yangilash vaqtincha imkonsiz
bo'lganda, YANGI endpointlar shu yerda ulanadi. Vercel /api so'rovlarni
shu faylga yo'naltiradi; u main.app ni olib, ustiga qo'shimchalarni
qo'shadi. main.py to'liq yangilanganda bu modul dublikatlarni olib
tashlab, o'z nusxasini qayta o'rnatadi — ikkala holatda ham bir xil
ishlaydi (idempotent).
"""
import os
import sys

# Vercel entry.py ni to'g'ridan-to'g'ri yuklaydi — api/ papkasini
# import yo'liga qo'shmasa, yonidagi modullar (audit, models...) topilmaydi.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import date

from fastapi import Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

import audit
import models
import roles
import schemas
from main import (  # noqa: F401
    app, get_db, require_role, scope_to_branch, _get_group_in_scope,
    _my_teacher_or_404,
)
import main as M


def _drop_route(path: str, method: str) -> None:
    """Bir xil yo'l qayta e'lon qilinganda eskisini olib tashlaydi —
    main.py yangi versiyada bo'lsa ham, bo'lmasa ham bitta nusxa qoladi."""
    keep = []
    for r in app.router.routes:
        if getattr(r, "path", None) == path and \
                method in (getattr(r, "methods", None) or []):
            continue
        keep.append(r)
    app.router.routes = keep


# =====================================================================
#  MASHQLAR — natijalar, ballar va daraja zinasi
# =====================================================================
def _practice_summary(db: Session, student_id: int) -> dict:
    rows = (db.query(func.count(models.ExerciseResult.id),
                     func.coalesce(func.sum(models.ExerciseResult.total), 0),
                     func.coalesce(func.sum(models.ExerciseResult.correct), 0))
            .filter(models.ExerciseResult.student_id == student_id).one())
    done, total, correct = int(rows[0]), int(rows[1]), int(rows[2])
    per = roles.PRACTICE_POINTS_PER_LEVEL
    idx = min(len(roles.ENG_LEVELS) - 1, correct // per)
    cur = roles.ENG_LEVELS[idx]
    is_last = idx >= len(roles.ENG_LEVELS) - 1
    nxt = None if is_last else roles.ENG_LEVELS[idx + 1]
    in_level = correct - idx * per
    return {
        "done": done, "total": total, "correct": correct,
        "percent": round(correct * 100 / total, 1) if total else 0,
        "points": correct,
        "level": cur,
        "next": None if is_last else {
            "label": nxt["label"], "ielts": nxt["ielts"],
            "cefr": nxt["cefr"],
            "points_left": per - in_level,
            "progress_percent": round(in_level * 100 / per, 1),
        },
        "levels": roles.ENG_LEVELS,
    }


_drop_route("/api/students/{student_id}/exercises", "GET")


@app.get("/api/students/{student_id}/exercises")
def student_exercises(student_id: int,
                      db: Session = Depends(get_db),
                      user=Depends(require_role(*roles.TEACHING_STAFF,
                                                roles.HR_MANAGER))):
    s = db.query(models.Student).get(student_id)
    if not s:
        raise HTTPException(404, "O'quvchi topilmadi")
    rows = (db.query(models.ExerciseResult)
            .filter(models.ExerciseResult.student_id == student_id)
            .order_by(models.ExerciseResult.date.desc(),
                      models.ExerciseResult.id.desc())
            .limit(100).all())
    return {
        "summary": _practice_summary(db, student_id),
        "rows": [{
            "id": r.id,
            "date": r.date.isoformat() if r.date else None,
            "total": r.total, "correct": r.correct,
            "percent": round(r.correct * 100 / r.total, 1) if r.total else 0,
            "topic": r.topic, "created_by": r.created_by,
        } for r in rows],
    }


_drop_route("/api/students/{student_id}/exercises", "POST")


@app.post("/api/students/{student_id}/exercises")
def add_exercise(student_id: int, payload: schemas.ExerciseIn,
                 db: Session = Depends(get_db),
                 user=Depends(require_role(*roles.TEACHING_ACCESS))):
    s = db.query(models.Student).get(student_id)
    if not s:
        raise HTTPException(404, "O'quvchi topilmadi")
    if not (1 <= payload.total <= 500):
        raise HTTPException(400, "Savollar soni 1-500 oralig'ida bo'lsin")
    if not (0 <= payload.correct <= payload.total):
        raise HTTPException(400, "To'g'ri javoblar jami savoldan oshmaydi")
    before = _practice_summary(db, student_id)["level"]["key"]
    r = models.ExerciseResult(
        student_id=student_id, total=payload.total,
        correct=payload.correct,
        topic=(payload.topic or "").strip() or None,
        created_by=user.full_name)
    db.add(r)
    db.commit()
    after = _practice_summary(db, student_id)
    leveled_up = after["level"]["key"] != before
    if leveled_up:
        audit.log(db, user, entity="student", action="practice_level",
                  entity_id=s.id, entity_label=s.full_name,
                  new_value=after["level"]["label"],
                  note="Mashqlar bo'yicha yangi daraja",
                  branch_id=s.branch_id, commit=True)
    return {"ok": True, "summary": after, "leveled_up": leveled_up}


_drop_route("/api/exercises/{rid}", "DELETE")


@app.delete("/api/exercises/{rid}")
def delete_exercise(rid: int, db: Session = Depends(get_db),
                    user=Depends(require_role(*roles.FULL_ACCESS,
                                              roles.ACADEMIC_HEAD))):
    r = db.query(models.ExerciseResult).get(rid)
    if not r:
        raise HTTPException(404, "Yozuv topilmadi")
    db.delete(r)
    db.commit()
    return {"ok": True}


_drop_route("/api/groups/{group_id}/exercises-stats", "GET")


@app.get("/api/groups/{group_id}/exercises-stats")
def group_exercises_stats(group_id: int,
                          db: Session = Depends(get_db),
                          user=Depends(require_role(
                              *roles.TEACHING_ACCESS, roles.HR_MANAGER))):
    g = _get_group_in_scope(db, group_id, user)
    students = (db.query(models.Student)
                .filter(models.Student.group_id == g.id,
                        models.Student.status.in_(("active", "trial")))
                .order_by(models.Student.full_name).all())
    rows = []
    for s in students:
        sm = _practice_summary(db, s.id)
        rows.append({
            "student_id": s.id, "full_name": s.full_name,
            "done": sm["done"], "percent": sm["percent"],
            "points": sm["points"], "level": sm["level"],
            "next": sm["next"],
        })
    return {"group": g.name, "rows": rows, "levels": roles.ENG_LEVELS}


# =====================================================================
#  GURUHLARDA SUPPORT KO'RINISHI
# =====================================================================
def _group_support_map(db: Session, group_ids: list) -> dict:
    if not group_ids:
        return {}
    rows = (db.query(models.SupportAssignment.group_id,
                     models.User.full_name)
            .join(models.User,
                  models.User.id == models.SupportAssignment.user_id)
            .filter(models.SupportAssignment.group_id.in_(group_ids))
            .all())
    m = {}
    for gid, name in rows:
        m.setdefault(gid, []).append(name)
    return {gid: ", ".join(sorted(set(names)))
            for gid, names in m.items()}


_drop_route("/api/groups", "GET")


@app.get("/api/groups", response_model=list[schemas.GroupOut])
def list_groups(branch_id: int | None = None,
                db: Session = Depends(get_db),
                user=Depends(M.get_current_user)):
    M.backfill_missing_ids(db, "group", models.Group)
    q = scope_to_branch(db.query(models.Group), models.Group, user,
                        branch_id)
    groups = q.order_by(models.Group.name).all()
    counts = dict(
        db.query(models.Student.group_id, func.count(models.Student.id))
        .filter(models.Student.status == "active",
                models.Student.group_id.isnot(None))
        .group_by(models.Student.group_id).all())
    sup_map = _group_support_map(db, [g.id for g in groups])
    out = []
    for g in groups:
        item = schemas.GroupOut.model_validate(g)
        item.student_count = counts.get(g.id, 0)
        item.support_label = sup_map.get(g.id)
        out.append(item)
    return out


_drop_route("/api/groups/{group_id}", "GET")


@app.get("/api/groups/{group_id}", response_model=schemas.GroupOut)
def get_group(group_id: int, db: Session = Depends(get_db),
              user=Depends(M.get_current_user)):
    group = _get_group_in_scope(db, group_id, user)
    item = schemas.GroupOut.model_validate(group)
    item.student_count = db.query(models.Student).filter(
        models.Student.group_id == group.id,
        models.Student.status == "active").count()
    item.support_label = _group_support_map(db, [group.id]).get(group.id)
    return item


# =====================================================================
#  SUPPORT SEANSI ASOSIY DARSGA TUSHMASIN
# =====================================================================
_drop_route("/api/me/support-sessions", "POST")


@app.post("/api/me/support-sessions")
def my_support_session_add(payload: schemas.SupportSessionIn,
                           db: Session = Depends(get_db),
                           user=Depends(require_role(
                               roles.SUPPORT_TEACHER,
                               *roles.PAST_ATTENDANCE))):
    t = _my_teacher_or_404(db, user) if user.role == roles.SUPPORT_TEACHER \
        else M._teacher_of_user(db, user)
    if not t:
        raise HTTPException(404, "Ustoz kartasi topilmadi")

    g = db.query(models.Group).get(payload.group_id)
    if not g:
        raise HTTPException(404, "Guruh topilmadi")

    today = roles.local_today()
    d = payload.date or today
    if d > today:
        raise HTTPException(400, "Hali kelmagan kunga seans kiritilmaydi")
    if d < today and user.role not in tuple(roles.PAST_ATTENDANCE):
        raise HTTPException(
            403, "O'tib ketgan kunga faqat asoschi va o'quv bo'limi "
                 "rahbari kirita oladi — darsni o'sha kuni kiriting")

    s_min = roles.hhmm_minutes(payload.start_time)
    e_min = roles.hhmm_minutes(payload.end_time)
    if s_min is None or e_min is None:
        raise HTTPException(400, "Vaqt SS:DD ko'rinishida bo'lsin, "
                                 "masalan 14:30")
    if e_min <= s_min:
        raise HTTPException(400, "Tugash vaqti boshlanishdan keyin "
                                 "bo'lishi kerak")
    minutes = e_min - s_min
    if minutes > roles.SUPPORT_SESSION_MAX_HOURS * 60:
        raise HTTPException(
            400, f"Bitta seans {roles.SUPPORT_SESSION_MAX_HOURS} "
                 f"soatdan oshmaydi — xato kiritmadingizmi?")
    if not (1 <= payload.students_count
            <= roles.SUPPORT_SESSION_MAX_STUDENTS):
        raise HTTPException(
            400, f"O'quvchilar soni 1 dan "
                 f"{roles.SUPPORT_SESSION_MAX_STUDENTS} gacha")

    # ASOSIY DARS bilan to'qnashuv
    wd = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"][d.weekday()]
    if wd in (g.lesson_days or "") and g.lesson_time \
            and "-" in g.lesson_time:
        gs, ge = g.lesson_time.split("-", 1)
        gs, ge = roles.hhmm_minutes(gs), roles.hhmm_minutes(ge)
        if gs is not None and ge is not None \
                and s_min < ge and gs < e_min:
            raise HTTPException(
                400, f"DIQQAT: bu vaqt \"{g.name}\" guruhining ASOSIY "
                     f"darsi bilan bir xil ({g.lesson_time}). Support "
                     f"seansi asosiy darsdan alohida vaqtda bo'ladi — "
                     f"vaqtni tekshirib qayta kiriting.")

    dup = (db.query(models.SupportSession)
           .filter(models.SupportSession.teacher_id == t.id,
                   models.SupportSession.group_id == g.id,
                   models.SupportSession.date == d).first())
    if dup:
        raise HTTPException(400, "Bu kunga bu guruh uchun seans "
                                 "allaqachon kiritilgan")

    row = models.SupportSession(
        teacher_id=t.id, group_id=g.id, date=d,
        start_time=payload.start_time.strip(),
        end_time=payload.end_time.strip(),
        minutes=minutes,
        students_count=payload.students_count,
        note=(payload.note or "").strip() or None,
        created_by=user.full_name)
    db.add(row)
    db.commit()
    return {"ok": True, "id": row.id, "minutes": minutes}


# =====================================================================
#  OTA-ONA PORTALIDA MASHQ DARAJASI
# =====================================================================
_drop_route("/api/parent/{token}", "GET")


@app.get("/api/parent/{token}")
def parent_view(token: str, db: Session = Depends(get_db)):
    if not token or len(token) < 10:
        raise HTTPException(404, "Topilmadi")
    s = db.query(models.Student).filter(
        models.Student.parent_token == token).first()
    if not s:
        raise HTTPException(404, "Topilmadi")
    g = db.query(models.Group).get(s.group_id) if s.group_id else None
    today = roles.local_today()
    from datetime import timedelta
    start = today - timedelta(days=45)
    rows = (db.query(models.Attendance, models.Lesson)
            .join(models.Lesson,
                  models.Attendance.lesson_id == models.Lesson.id)
            .filter(models.Attendance.student_id == s.id,
                    models.Lesson.date >= start,
                    models.Lesson.date <= today)
            .order_by(models.Lesson.date.desc()).limit(24).all())
    att = [{
        "date": ls.date.isoformat(),
        "present": int(a.present or 0),
        "homework": a.homework,
    } for a, ls in rows]
    bal = M.student_balance(db, s.id)
    st_lbl = {"active": "faol", "trial": "sinovda",
              "frozen": "muzlatilgan", "archived": "arxivda"}
    return {
        "name": s.full_name,
        "group": g.name if g else None,
        "lesson_time": g.lesson_time if g else None,
        "status": st_lbl.get(s.status, s.status),
        "balance": bal,
        "attendance": att,
        "frozen_until": s.frozen_until.isoformat()
        if s.frozen_until else None,
        "practice": _practice_summary(db, s.id),
    }

# =====================================================================
#  SUPPORT JADVALIDA GURUHGA O'TISH — bloklarda group_id
# =====================================================================
_drop_route("/api/support-timetable", "GET")


@app.get("/api/support-timetable")
def support_timetable(day: str = "mon",
                      branch_id: int | None = None,
                      db: Session = Depends(get_db),
                      user=Depends(require_role(
                          *roles.FULL_ACCESS, roles.HEAD_SUPPORT,
                          roles.ACADEMIC_HEAD, roles.HR_MANAGER))):
    """Supportlar jadvali: guruh bloki bosilganda guruhga kirish uchun
    group_id ham qaytadi."""
    if day not in ("mon", "tue", "wed", "thu", "fri", "sat", "sun"):
        raise HTTPException(400, "Kun noto'g'ri")
    q = (db.query(models.Teacher)
         .join(models.User, models.User.id == models.Teacher.user_id)
         .filter(models.User.role == roles.SUPPORT_TEACHER,
                 models.Teacher.is_active == 1))
    q = scope_to_branch(q, models.Teacher, user)
    if branch_id:
        q = q.filter(models.Teacher.branch_id == branch_id)
    bnames = {b.id: b.name for b in db.query(models.Branch).all()}
    rows = []
    for t in q.order_by(models.Teacher.full_name).all():
        blocks = []
        gids = [a.group_id for a in
                db.query(models.SupportAssignment)
                .filter(models.SupportAssignment.user_id == t.user_id,
                        models.SupportAssignment.group_id.isnot(None))
                .all()]
        for g in (db.query(models.Group)
                  .filter(models.Group.id.in_(gids or [-1])).all()):
            if day not in (g.lesson_days or ""):
                continue
            st = (g.lesson_time or "").split("-")[0].strip()
            blocks.append({
                "kind": "group", "label": g.name,
                "group_id": g.id,
                "time": g.lesson_time or "",
                "sort": M._time_to_min(st) or 0,
                "room": g.room,
            })
        for b in (db.query(models.SupportBusy)
                  .filter(models.SupportBusy.teacher_id == t.id).all()):
            if day not in (b.days or ""):
                continue
            blocks.append({
                "kind": "busy",
                "label": b.note or "Band (o'zi belgilagan)",
                "time": f"{b.start}-{b.end}",
                "sort": M._time_to_min(b.start) or 0,
            })
        blocks.sort(key=lambda x: x["sort"])
        rows.append({
            "teacher_id": t.id, "name": t.full_name,
            "branch": bnames.get(t.branch_id),
            "blocks": blocks,
        })
    return {"day": day, "rows": rows}

# =====================================================================
#  RO'YXATDAN TURIB SUPPORT BIRIKTIRISH / USTOZ ALMASHTIRISH
#  Guruh kartasiga kirmasdan, Guruhlar ro'yxatining o'zida.
# =====================================================================
from pydantic import BaseModel as _BM


class _GroupSupportsIn(_BM):
    user_ids: list[int] = []


_drop_route("/api/groups/{group_id}/supports", "GET")


@app.get("/api/groups/{group_id}/supports")
def group_supports(group_id: int,
                   db: Session = Depends(get_db),
                   user=Depends(require_role(*roles.SUPPORT_ASSIGN))):
    """Guruhga biriktirilgan supportlar + tanlash uchun ro'yxat."""
    g = _get_group_in_scope(db, group_id, user)
    assigned = [a.user_id for a in
                db.query(models.SupportAssignment)
                .filter(models.SupportAssignment.group_id == g.id).all()]
    q = (db.query(models.Teacher, models.User)
         .join(models.User, models.User.id == models.Teacher.user_id)
         .filter(models.User.role == roles.SUPPORT_TEACHER,
                 models.Teacher.is_active == 1))
    q = scope_to_branch(q, models.Teacher, user)
    bnames = {b.id: b.name for b in db.query(models.Branch).all()}
    options = [{
        "user_id": t.user_id, "name": t.full_name,
        "branch": bnames.get(t.branch_id),
    } for t, u in q.order_by(models.Teacher.full_name).all()]
    return {"assigned": assigned, "options": options}


_drop_route("/api/groups/{group_id}/supports", "PUT")


@app.put("/api/groups/{group_id}/supports")
def set_group_supports(group_id: int, payload: _GroupSupportsIn,
                       force: bool = False,
                       db: Session = Depends(get_db),
                       user=Depends(require_role(*roles.SUPPORT_ASSIGN))):
    """Guruh uchun supportlar to'plamini saqlash. Yangi support
    qo'shilsa unga xabar boradi; band vaqtiga to'qnashsa 409
    ogohlantirish qaytadi (force=true bilan o'tkaziladi)."""
    g = _get_group_in_scope(db, group_id, user)
    want = set(payload.user_ids or [])
    for uid in want:
        u = db.query(models.User).get(uid)
        if not u or u.role != roles.SUPPORT_TEACHER:
            raise HTTPException(400, "Faqat support teacherlarni "
                                     "biriktirish mumkin")
    cur = {a.user_id: a for a in
           db.query(models.SupportAssignment)
           .filter(models.SupportAssignment.group_id == g.id).all()}
    added = sorted(want - set(cur))
    removed = sorted(set(cur) - want)
    if added and not force and hasattr(M, "_support_conflicts"):
        warns = []
        for uid in added:
            t = (db.query(models.Teacher)
                 .filter(models.Teacher.user_id == uid,
                         models.Teacher.is_active == 1).first())
            if t is not None:
                warns += M._support_conflicts(db, t.id, [g])
        if warns:
            raise HTTPException(409, " • ".join(warns[:3]))
    for uid in removed:
        db.delete(cur[uid])
    for uid in added:
        db.add(models.SupportAssignment(
            user_id=uid, group_id=g.id, created_by=user.full_name))
        days = M._days_uz(g.lesson_days) if hasattr(M, "_days_uz") \
            else (g.lesson_days or "")
        M._hr_task_for(
            db, uid,
            title=f"Sizga guruh biriktirildi: {g.name}",
            body=(f"\"{g.name}\" guruhi ({days} {g.lesson_time or ''}) "
                  f"sizga support sifatida biriktirildi."),
            branch_id=g.branch_id)
    db.commit()
    label = _group_support_map(db, [g.id]).get(g.id)
    return {"ok": True, "support_label": label,
            "added": len(added), "removed": len(removed)}
