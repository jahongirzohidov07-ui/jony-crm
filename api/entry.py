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

# =====================================================================
#  SUPPORT VAQTLARI + TELEFON-LOGIN
#  1) Biriktirishda support darsining KUN/VAQTI so'raladi va saqlanadi.
#  2) Jadval asosiy dars vaqtini EMAS, shu belgilangan vaqtni ko'rsatadi.
#  3) Yangi akkaunt: telefon majburiy, login = raqam, parol = jonyjony.
# =====================================================================
import re as _re

from sqlalchemy import inspect as _sa_inspect, text as _sa_text

from auth import hash_password as _hash_pw
from database import engine as _engine

# --- support_assignments jadvaliga ustunlar (idempotent ALTER) ---
try:
    _cols = {c["name"] for c in
             _sa_inspect(_engine).get_columns("support_assignments")}
    with _engine.begin() as _c:
        if "days" not in _cols:
            _c.execute(_sa_text(
                "ALTER TABLE support_assignments ADD COLUMN days VARCHAR"))
        if "start" not in _cols:
            _c.execute(_sa_text(
                "ALTER TABLE support_assignments ADD COLUMN start VARCHAR"))
        if "end" not in _cols:
            _c.execute(_sa_text(
                'ALTER TABLE support_assignments ADD COLUMN "end" VARCHAR'))
except Exception:
    pass


class _SupItem(_BM):
    user_id: int
    days: str | None = None      # "mon,wed"
    start: str | None = None     # "14:00"
    end: str | None = None       # "16:00"


class _GroupSupportsIn2(_BM):
    items: list[_SupItem] | None = None
    user_ids: list[int] | None = None  # eski format ham qabul qilinadi


def _sup_time_ok(it) -> str | None:
    """Vaqt kiritilgan bo'lsa to'g'riligini tekshiradi."""
    if not (it.days or it.start or it.end):
        return None
    if not (it.days and it.start and it.end):
        return "Kun va vaqtni to'liq kiriting (yoki butunlay bo'sh qoldiring)"
    s, e = roles.hhmm_minutes(it.start), roles.hhmm_minutes(it.end)
    if s is None or e is None:
        return "Vaqt SS:DD ko'rinishida bo'lsin, masalan 14:00"
    if e <= s:
        return "Tugash vaqti boshlanishdan keyin bo'lsin"
    return None


def _sup_conflicts2(db: Session, uid: int, it, skip_group_id: int) -> list:
    """Yangi belgilangan vaqt supportning band vaqtlari yoki boshqa
    guruhlardagi BELGILANGAN vaqtlari bilan to'qnashsa — ro'yxat."""
    if not (it.days and it.start and it.end):
        return []
    days = set((it.days or "").split(","))
    s, e = roles.hhmm_minutes(it.start), roles.hhmm_minutes(it.end)
    out = []
    t = (db.query(models.Teacher)
         .filter(models.Teacher.user_id == uid,
                 models.Teacher.is_active == 1).first())
    if t is not None:
        for b in (db.query(models.SupportBusy)
                  .filter(models.SupportBusy.teacher_id == t.id).all()):
            bs, be = roles.hhmm_minutes(b.start), roles.hhmm_minutes(b.end)
            if bs is None or be is None:
                continue
            if days & set((b.days or "").split(",")) and s < be and bs < e:
                out.append(f"Support bu vaqtni BAND deb belgilagan: "
                           f"{b.start}-{b.end} ({b.note or 'sabab yozilmagan'})")
    rows = (db.query(models.SupportAssignment, models.Group)
            .join(models.Group,
                  models.Group.id == models.SupportAssignment.group_id)
            .filter(models.SupportAssignment.user_id == uid,
                    models.SupportAssignment.group_id != skip_group_id)
            .all())
    for a, g in rows:
        if not (a.days and a.start and a.end):
            continue
        os_, oe = roles.hhmm_minutes(a.start), roles.hhmm_minutes(a.end)
        if os_ is None or oe is None:
            continue
        if days & set((a.days or "").split(",")) and s < oe and os_ < e:
            out.append(f"\"{g.name}\" guruhida allaqachon band: "
                       f"{a.start}-{a.end}")
    return out


_drop_route("/api/groups/{group_id}/supports", "GET")


@app.get("/api/groups/{group_id}/supports")
def group_supports_v2(group_id: int,
                      db: Session = Depends(get_db),
                      user=Depends(require_role(*roles.SUPPORT_ASSIGN))):
    g = _get_group_in_scope(db, group_id, user)
    assigned = [{
        "user_id": a.user_id, "days": a.days,
        "start": a.start, "end": a.end,
    } for a in db.query(models.SupportAssignment)
        .filter(models.SupportAssignment.group_id == g.id).all()]
    q = (db.query(models.Teacher)
         .join(models.User, models.User.id == models.Teacher.user_id)
         .filter(models.User.role == roles.SUPPORT_TEACHER,
                 models.Teacher.is_active == 1))
    q = scope_to_branch(q, models.Teacher, user)
    bnames = {b.id: b.name for b in db.query(models.Branch).all()}
    options = [{
        "user_id": t.user_id, "name": t.full_name,
        "branch": bnames.get(t.branch_id),
    } for t in q.order_by(models.Teacher.full_name).all()]
    return {"assigned": assigned, "options": options}


_drop_route("/api/groups/{group_id}/supports", "PUT")


@app.put("/api/groups/{group_id}/supports")
def set_group_supports_v2(group_id: int, payload: _GroupSupportsIn2,
                          force: bool = False,
                          db: Session = Depends(get_db),
                          user=Depends(require_role(*roles.SUPPORT_ASSIGN))):
    g = _get_group_in_scope(db, group_id, user)
    items = payload.items
    if items is None:
        items = [_SupItem(user_id=u) for u in (payload.user_ids or [])]
    seen = set()
    for it in items:
        if it.user_id in seen:
            raise HTTPException(400, "Bitta support ikki marta tanlangan")
        seen.add(it.user_id)
        u = db.query(models.User).get(it.user_id)
        if not u or u.role != roles.SUPPORT_TEACHER:
            raise HTTPException(400, "Faqat support teacherlarni "
                                     "biriktirish mumkin")
        msg = _sup_time_ok(it)
        if msg:
            raise HTTPException(400, msg)
    if not force:
        warns = []
        for it in items:
            warns += _sup_conflicts2(db, it.user_id, it, g.id)
        if warns:
            raise HTTPException(409, " \u2022 ".join(warns[:3]))
    cur = {a.user_id: a for a in
           db.query(models.SupportAssignment)
           .filter(models.SupportAssignment.group_id == g.id).all()}
    want = {it.user_id: it for it in items}
    added = []
    for uid, a in list(cur.items()):
        if uid not in want:
            db.delete(a)
    for uid, it in want.items():
        if uid in cur:
            a = cur[uid]
            a.days, a.start, a.end = it.days, it.start, it.end
        else:
            db.add(models.SupportAssignment(
                user_id=uid, group_id=g.id,
                days=it.days, start=it.start, end=it.end,
                created_by=user.full_name))
            added.append((uid, it))
    for uid, it in added:
        vaqt = f"{it.days or ''} {it.start or ''}-{it.end or ''}".strip(" -")
        M._hr_task_for(
            db, uid,
            title=f"Sizga guruh biriktirildi: {g.name}",
            body=(f"\"{g.name}\" guruhi sizga support sifatida "
                  f"biriktirildi. Dars vaqti: {vaqt or 'kelishiladi'}."),
            branch_id=g.branch_id)
    db.commit()
    label = _group_support_map(db, [g.id]).get(g.id)
    return {"ok": True, "support_label": label}


_drop_route("/api/support-timetable", "GET")


@app.get("/api/support-timetable")
def support_timetable_v2(day: str = "mon",
                         branch_id: int | None = None,
                         db: Session = Depends(get_db),
                         user=Depends(require_role(
                             *roles.FULL_ACCESS, roles.HEAD_SUPPORT,
                             roles.ACADEMIC_HEAD, roles.HR_MANAGER))):
    """Supportlar jadvali. MUHIM: guruhning ASOSIY dars vaqti emas,
    biriktirishda BELGILANGAN support-dars vaqti ko'rsatiladi."""
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
        arows = (db.query(models.SupportAssignment, models.Group)
                 .join(models.Group,
                       models.Group.id == models.SupportAssignment.group_id)
                 .filter(models.SupportAssignment.user_id == t.user_id)
                 .all())
        for a, g in arows:
            if not (a.days and a.start and a.end):
                continue  # vaqti hali belgilanmagan
            if day not in (a.days or ""):
                continue
            blocks.append({
                "kind": "group", "label": g.name,
                "group_id": g.id,
                "time": f"{a.start}-{a.end}",
                "sort": roles.hhmm_minutes(a.start) or 0,
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
                "sort": roles.hhmm_minutes(b.start) or 0,
            })
        blocks.sort(key=lambda x: x["sort"])
        rows.append({
            "teacher_id": t.id, "name": t.full_name,
            "branch": bnames.get(t.branch_id),
            "blocks": blocks,
        })
    return {"day": day, "rows": rows}


# --------------------------------------------------------------
#  YANGI AKKAUNT: telefon majburiy, login = raqam, parol jonyjony
# --------------------------------------------------------------
class _UserCreate2(schemas.UserCreate):
    username: str | None = None
    password: str | None = None


_drop_route("/api/users", "POST")


@app.post("/api/users", response_model=schemas.UserOut)
def create_user_v2(payload: _UserCreate2,
                   db: Session = Depends(get_db),
                   user=Depends(require_role(*roles.STAFF_EDIT))):
    digits = _re.sub(r"\D", "", payload.phone or "")
    if len(digits) < 7:
        raise HTTPException(400, "Telefon raqamni kiriting — u login "
                                 "o'rnida ishlatiladi")
    username = (payload.username or "").strip() or digits
    password = payload.password or "jonyjony"
    if payload.role not in roles.ALL_ROLES:
        raise HTTPException(400, "Noto'g'ri rol")
    M._guard_role_assignment(user, payload.role, payload.branch_id)
    if user.role == roles.BRANCH_MANAGER and user.branch_id \
            and payload.branch_id != user.branch_id:
        raise HTTPException(403, "Faqat o'z filialingizga xodim "
                                 "qo'sha olasiz")
    if db.query(models.User).filter(
            models.User.username == username).first():
        raise HTTPException(400, "Bu login band — bu raqam bilan akkaunt "
                                 "allaqachon ochilgan bo'lishi mumkin")
    # Standart "jonyjony" parolga qoida qo'llanmaydi — kirgach
    # o'zgartirish tavsiya etiladi. O'zi kiritgan parol esa tekshiriladi.
    if payload.password and not roles.password_ok(password):
        raise HTTPException(400, roles.PASSWORD_RULE_TEXT)
    _bids = payload.branch_ids or []
    _primary = payload.branch_id or (_bids[0] if _bids else None)
    new_user = models.User(
        username=username,
        password_hash=_hash_pw(password),
        full_name=payload.full_name,
        role=payload.role,
        branch_id=_primary,
        fix_salary=payload.fix_salary,
        phone=payload.phone,
        birth_date=payload.birth_date,
        position=payload.position,
        manager_id=payload.manager_id,
        hired_date=payload.hired_date or date.today(),
        photo=payload.photo,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    if _bids:
        M._sync_user_branches(db, new_user, _bids)
    M._smm_new_staff_task(db, new_user)
    M._ensure_teacher_card(db, new_user)
    db.commit()
    return new_user

# =====================================================================
#  XONALAR FILIALGA QAT'IY BOG'LANADI
#  Har filialning o'z xonalari; ro'yxat filial almashtirgichga bo'ysunadi;
#  yangi xona filialsiz ochilmaydi (filial sig'imi xonalardan chiqadi).
# =====================================================================
_drop_route("/api/rooms", "GET")


@app.get("/api/rooms")
def list_rooms_v2(branch_id: int | None = None,
                  db: Session = Depends(get_db),
                  user=Depends(require_role(*roles.TEACHING_STAFF))):
    q = scope_to_branch(db.query(models.Room), models.Room, user, branch_id)
    rooms = q.order_by(models.Room.name).all()
    by_room = {}
    for g in (db.query(models.Group)
              .filter(models.Group.room_id.isnot(None)).all()):
        by_room.setdefault(g.room_id, []).append(g)
    return [M._room_out(r, by_room.get(r.id, [])) for r in rooms]


_drop_route("/api/rooms", "POST")


@app.post("/api/rooms")
def create_room_v2(payload: schemas.RoomCreate,
                   db: Session = Depends(get_db),
                   user=Depends(require_role(*roles.ACADEMIC_ACCESS))):
    data = payload.model_dump()
    if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
        data["branch_id"] = user.branch_id
    if not data.get("branch_id"):
        raise HTTPException(400, "Xonaning filialini tanlang \u2014 har bir "
                                 "filialning o'z xonalari bo'ladi")
    r = models.Room(**data)
    db.add(r)
    db.commit()
    db.refresh(r)
    audit.log(db, user, entity="room", action="create", entity_id=r.id,
              entity_label=r.name, new_value=r.capacity,
              branch_id=r.branch_id, commit=True)
    return M._room_out(r)

# =====================================================================
#  USTOZ GURUH CHEGARASI: FAQAT ASOSCHI "BARIBIR OCHISH" QILA OLADI
#  Junior 1 ta, Middle 2-3 ta... — chegaradan oshsa: asoschiga
#  ogohlantirish + "baribir saqlash" tugmasi; boshqalarga QAT'IY taqiq.
# =====================================================================
def _find_endpoint(path: str, method: str):
    for r in app.router.routes:
        if getattr(r, "path", None) == path and \
                method in (getattr(r, "methods", None) or []):
            return r.endpoint
    return None


_orig_create_group = _find_endpoint("/api/groups", "POST")
_orig_update_group = _find_endpoint("/api/groups/{group_id}", "PUT")

# Asl tekshiruvda chegara "block" (hech kim o'tolmaydi) edi. Endi u
# "warn"ga tushiriladi — asoschi 409 ogohlantirish oladi va "baribir
# saqlash" qila oladi. Asoschi bo'lmaganlarni esa pastdagi guard
# har qanday holatda 400 bilan to'xtatadi. Qayta tayyorlash (remediation)
# taqig'i esa "chegara" so'zisiz — u block'ligicha qoladi.
_orig_check_teacher_load = M._check_teacher_load


def _check_teacher_load_soft(db, teacher_id, group_id):
    problems = _orig_check_teacher_load(db, teacher_id, group_id)
    for p in problems:
        if p.get("key") == "teacher_overload" and "chegara" in p.get("message", ""):
            p["severity"] = "warn"
    return problems


M._check_teacher_load = _check_teacher_load_soft


def _teacher_limit_guard(db: Session, teacher_id, group_id, user):
    """Chegaradan oshganda asoschi bo'lmaganlarga qattiq taqiq."""
    if not teacher_id or user.role == roles.FOUNDER:
        return
    problems = [p for p in _orig_check_teacher_load(db, teacher_id, group_id)
                if p.get("key") == "teacher_overload"]
    if problems:
        for p in problems:
            p["severity"] = "block"
        raise HTTPException(400, {
            "message": "Mumkin emas: " + problems[0]["message"],
            "problems": problems,
        })


if _orig_create_group is not None:
    _drop_route("/api/groups", "POST")

    @app.post("/api/groups")
    def create_group_v2(payload: schemas.GroupCreate,
                        force: bool = False,
                        db: Session = Depends(get_db),
                        user=Depends(require_role(*roles.GROUP_MANAGE))):
        _teacher_limit_guard(db, payload.teacher_id, None, user)
        return _orig_create_group(payload=payload, force=force,
                                  db=db, user=user)


if _orig_update_group is not None:
    _drop_route("/api/groups/{group_id}", "PUT")

    @app.put("/api/groups/{group_id}")
    def update_group_v2(group_id: int, payload: schemas.GroupUpdate,
                        force: bool = False,
                        db: Session = Depends(get_db),
                        user=Depends(require_role(*roles.GROUP_MANAGE))):
        fields = payload.model_dump(exclude_unset=True)
        if "teacher_id" in fields and fields.get("teacher_id"):
            _teacher_limit_guard(db, fields["teacher_id"], group_id, user)
        return _orig_update_group(group_id=group_id, payload=payload,
                                  force=force, db=db, user=user)

# =====================================================================
#  ASOSCHI DASHBOARDI FILIAL ALMASHTIRGICHGA BO'YSUNADI
#  Tepada filial tanlansa — kartalar va tushum grafigi o'sha filial
#  bo'yicha; "Barcha filiallar"da — umumiy. (Avval doim umumiy edi.)
# =====================================================================
from datetime import timedelta as _td

import billing as _billing


_drop_route("/api/dashboard", "GET")


@app.get("/api/dashboard", response_model=schemas.DashboardStats)
def dashboard_v2(branch_id: int | None = None,
                 db: Session = Depends(get_db),
                 user: models.User = Depends(M.get_current_user)):
    student_q = scope_to_branch(db.query(models.Student), models.Student,
                                user, branch_id)
    active = student_q.filter(models.Student.status == "active").count()
    trial = student_q.filter(models.Student.status == "trial").count()
    frozen = student_q.filter(models.Student.status == "frozen").count()
    groups = scope_to_branch(db.query(models.Group), models.Group,
                             user, branch_id).count()
    teachers = scope_to_branch(db.query(models.Teacher), models.Teacher,
                               user, branch_id).count()

    month_start = date.today().replace(day=1)
    all_students = student_q.all()
    student_ids = [s.id for s in all_students]

    month_income = 0.0
    if student_ids:
        month_income = (
            db.query(func.coalesce(func.sum(models.Payment.amount), 0.0))
            .filter(models.Payment.kind == "payment")
            .filter(models.Payment.created_at >= month_start)
            .filter(models.Payment.student_id.in_(student_ids))
            .scalar()
            or 0.0
        )

    month_pay_count = 0
    month_new_count = 0
    if student_ids:
        pays = (
            db.query(models.Payment)
            .filter(models.Payment.kind == "payment")
            .filter(models.Payment.created_at >= month_start)
            .filter(models.Payment.student_id.in_(student_ids))
            .all()
        )
        month_pay_count = len(pays)
        firsts = M._payment_first_dates(db)
        month_new_count = sum(
            1 for p in pays if firsts.get(p.student_id) == p.created_at
        )

    staff_count = scope_to_branch(
        db.query(models.User), models.User, user, branch_id
    ).filter(models.User.is_active == 1).count()

    balances = [(s.id, M.student_balance(db, s.id)) for s in all_students]
    total_debt = sum(b for _, b in balances if b < 0)
    debtor_count = sum(1 for _, b in balances if b < 0)

    return schemas.DashboardStats(
        active_students=active,
        trial_students=trial,
        frozen_students=frozen,
        total_groups=groups,
        total_teachers=teachers,
        month_payment_count=month_pay_count,
        month_new_payment_count=month_new_count,
        staff_count=staff_count,
        month_income=float(month_income),
        total_debt=float(total_debt),
        debtor_count=debtor_count,
    )


_drop_route("/api/dashboard/trend", "GET")


@app.get("/api/dashboard/trend")
def dashboard_trend_v2(months: int = 6,
                       branch_id: int | None = None,
                       db: Session = Depends(get_db),
                       user: models.User = Depends(M.get_current_user)):
    student_q = scope_to_branch(db.query(models.Student), models.Student,
                                user, branch_id)
    student_ids = [s.id for s in student_q.all()]

    today = date.today()
    y, m = today.year, today.month
    periods = []
    for _ in range(max(1, min(months, 24))):
        periods.append((y, m))
        m -= 1
        if m == 0:
            y, m = y - 1, 12
    periods.reverse()

    results = []
    for yy, mm in periods:
        start, end = _billing.month_bounds(yy, mm)
        income = 0.0
        if student_ids:
            income = (
                db.query(func.coalesce(func.sum(models.Payment.amount), 0.0))
                .filter(models.Payment.kind == "payment")
                .filter(models.Payment.created_at >= start)
                .filter(models.Payment.created_at < end + _td(days=1))
                .filter(models.Payment.student_id.in_(student_ids))
                .scalar()
                or 0.0
            )
        results.append({"period": f"{yy:04d}-{mm:02d}",
                        "income": float(income)})
    return results

# =====================================================================
#  DARS KO'CHIRILDI / O'RINBOSAR — ADMIN VA O'QUV BO'LIMIGA XABAR,
#  JADVALDA KO'RINISH
#  Admin jadvalga qarab yangi o'quvchini noto'g'ri kunga chaqirib
#  qo'ymasligi uchun: (1) har bir tasdiqlangan ko'chirish/o'rinbosarlik
#  administrator va o'quv bo'limi rahbariga vazifa-xabar bo'lib boradi;
#  (2) Dars jadvali sahifasida yaqin kunlardagi o'zgarishlar chiqadi.
# =====================================================================
def _lesson_change_task(db: Session, g, title: str, body: str) -> None:
    """Guruh filialidagi administratorlar va o'quv bo'limi rahbarlariga
    (filialga bog'lanmaganlariga ham) alohida-alohida vazifa-xabar."""
    users = (db.query(models.User)
             .filter(models.User.is_active == 1,
                     models.User.role.in_((roles.ADMINISTRATOR,
                                           roles.ACADEMIC_HEAD)))
             .all())
    for u in users:
        if u.branch_id and g.branch_id and u.branch_id != g.branch_id:
            continue
        t = models.Task(
            title=title, description=body, assignee_id=u.id,
            branch_id=g.branch_id,
            deadline=date.today() + _td(days=2),
            priority="normal", source="manual", created_by="Tizim")
        db.add(t)
        db.flush()
        M._ensure_public_id(db, "task", t)
    db.commit()


_orig_my_resched_add = _find_endpoint("/api/me/reschedules", "POST")
_orig_resched_decide = _find_endpoint("/api/reschedules/{rid}/decide", "POST")
_orig_sub_decide = _find_endpoint("/api/me/substitutions/{sid}/decide", "POST")


if _orig_my_resched_add is not None:
    _drop_route("/api/me/reschedules", "POST")

    @app.post("/api/me/reschedules")
    def my_reschedule_add_v2(payload: schemas.RescheduleIn,
                             db: Session = Depends(get_db),
                             user=Depends(require_role(*roles.SELF_STATS))):
        out = _orig_my_resched_add(payload=payload, db=db, user=user)
        try:
            if out.get("status") == "auto":
                g = db.query(models.Group).get(payload.group_id)
                if g is not None:
                    _lesson_change_task(
                        db, g,
                        title=(f"Dars ko'chirildi: {g.name} "
                               f"{payload.from_date} \u2192 {payload.to_date}"),
                        body=(f"{user.full_name} \"{g.name}\" guruhining "
                              f"{payload.from_date} dagi darsini "
                              f"{payload.to_date} ga ko'chirdi. "
                              f"Sabab: {out.get('reason_label') or payload.reason or '-'}. "
                              f"Yangi o'quvchini jadvalga qarab chaqirishda "
                              f"shuni hisobga oling."))
        except Exception:
            pass
        return out


if _orig_resched_decide is not None:
    _drop_route("/api/reschedules/{rid}/decide", "POST")

    @app.post("/api/reschedules/{rid}/decide")
    def reschedule_decide_v2(rid: int, payload: schemas.RescheduleDecision,
                             db: Session = Depends(get_db),
                             user=Depends(require_role(
                                 *roles.RESCHEDULE_APPROVE))):
        out = _orig_resched_decide(rid=rid, payload=payload, db=db, user=user)
        try:
            if payload.decision == "approved":
                r = db.query(models.LessonReschedule).get(rid)
                g = db.query(models.Group).get(r.group_id) if r else None
                if g is not None:
                    _lesson_change_task(
                        db, g,
                        title=(f"Dars ko'chirildi: {g.name} "
                               f"{r.from_date} \u2192 {r.to_date}"),
                        body=(f"\"{g.name}\" guruhining {r.from_date} dagi "
                              f"darsi {r.to_date} ga ko'chirildi "
                              f"(tasdiqladi: {user.full_name}). "
                              f"Yangi o'quvchini jadvalga qarab chaqirishda "
                              f"shuni hisobga oling."))
        except Exception:
            pass
        return out


if _orig_sub_decide is not None:
    _drop_route("/api/me/substitutions/{sid}/decide", "POST")

    @app.post("/api/me/substitutions/{sid}/decide")
    def my_substitution_decide_v2(sid: int,
                                  payload: schemas.SubstitutionDecision,
                                  db: Session = Depends(get_db),
                                  user=Depends(require_role(
                                      *roles.SELF_STATS))):
        out = _orig_sub_decide(sid=sid, payload=payload, db=db, user=user)
        try:
            if payload.decision == "accepted":
                s = db.query(models.Substitution).get(sid)
                g = db.query(models.Group).get(s.group_id) if s else None
                if g is not None:
                    orig_t = (db.query(models.Teacher)
                              .get(s.original_teacher_id)
                              if s.original_teacher_id else None)
                    _lesson_change_task(
                        db, g,
                        title=(f"O'rinbosar dars o'tadi: {g.name} "
                               f"({s.lesson_date})"),
                        body=(f"\"{g.name}\" guruhining {s.lesson_date} dagi "
                              f"darsini {orig_t.full_name if orig_t else '-'} "
                              f"o'rniga {user.full_name} o'tadi."))
        except Exception:
            pass
        return out


_orig_timetable = _find_endpoint("/api/timetable", "GET")

if _orig_timetable is not None:
    _drop_route("/api/timetable", "GET")

    @app.get("/api/timetable")
    def timetable_v2(branch_id: int | None = None,
                     db: Session = Depends(get_db),
                     user=Depends(require_role(*roles.TEACHING_STAFF,
                                               roles.HR_MANAGER))):
        out = _orig_timetable(branch_id=branch_id, db=db, user=user)
        try:
            gids = {it["group_id"] for it in out.get("items", [])}
            today = date.today()
            horizon = today + _td(days=30)
            changes = []
            if gids:
                gmap = {g.id: g for g in db.query(models.Group)
                        .filter(models.Group.id.in_(gids)).all()}
                rs = (db.query(models.LessonReschedule)
                      .filter(models.LessonReschedule.group_id.in_(gids),
                              models.LessonReschedule.status.in_(
                                  ("auto", "approved")),
                              models.LessonReschedule.to_date >= today,
                              models.LessonReschedule.from_date <= horizon)
                      .all())
                for r in rs:
                    g = gmap.get(r.group_id)
                    t = (db.query(models.Teacher).get(r.teacher_id)
                         if r.teacher_id else None)
                    changes.append({
                        "kind": "move", "group_id": r.group_id,
                        "group": g.name if g else "",
                        "teacher": t.full_name if t else None,
                        "from_date": r.from_date.isoformat(),
                        "to_date": r.to_date.isoformat(),
                        "sort": r.from_date.isoformat(),
                    })
                ss = (db.query(models.Substitution)
                      .filter(models.Substitution.group_id.in_(gids),
                              models.Substitution.status == "accepted",
                              models.Substitution.lesson_date >= today,
                              models.Substitution.lesson_date <= horizon)
                      .all())
                for s in ss:
                    g = gmap.get(s.group_id)
                    ot = (db.query(models.Teacher)
                          .get(s.original_teacher_id)
                          if s.original_teacher_id else None)
                    st = (db.query(models.Teacher)
                          .get(s.substitute_teacher_id)
                          if s.substitute_teacher_id else None)
                    changes.append({
                        "kind": "sub", "group_id": s.group_id,
                        "group": g.name if g else "",
                        "teacher": ot.full_name if ot else None,
                        "substitute": st.full_name if st else None,
                        "date": s.lesson_date.isoformat(),
                        "sort": s.lesson_date.isoformat(),
                    })
            changes.sort(key=lambda x: x["sort"])
            out["changes"] = changes
        except Exception:
            out.setdefault("changes", [])
        return out
