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
    _my_teacher_or_404, get_current_user,
)
import main as M


def _drop_route(path: str, method: str) -> None:
    """Bir xil yo'l qayta e'lon qilinganda eskisini olib tashlaydi —
    main.py yangi versiyada bo'lsa ham, bo'lmasa ham bitta nusxa qoladi.

    2026-08: main.py bo'lindi - domen routerlari endi
    app.include_router(...) orqali ulanadi, shuning uchun
    app.router.routes ichida to'g'ridan-to'g'ri emas, balki
    _IncludedRouter ichiga o'ralgan holda turadi. Shu ichkariga
    ham qarab, mos yo'lni topib olib tashlaymiz - xatti-harakat
    o'zgarmagan, faqat qidiruv chuqurroq."""
    def _matches(r):
        return getattr(r, "path", None) == path and \
            method in (getattr(r, "methods", None) or [])

    keep = []
    for r in app.router.routes:
        if _matches(r):
            continue
        ic = getattr(r, "include_context", None)
        nested = getattr(ic, "included_router", None) if ic else None
        if nested is not None and hasattr(nested, "routes"):
            nested.routes = [nr for nr in nested.routes if not _matches(nr)]
        keep.append(r)
    app.router.routes = keep


# HR menejerga "rahbariyat" sifatida dars ko'chirishni tasdiqlash/
# ko'rish huquqi shu YERDA, faylning ENG BOSHIDA berilishi SHART.
# Sabab: pastroqda (~qator 3040) xuddi shu qo'shimcha bor edi, lekin u
# YETARLI EMAS - Python fayl ichidagi @decorator'larni YUQORIDAN
# PASTGA, YOZUV TARTIBIDA ishga tushiradi va require_role(*ro'yxat)
# ro'yxatni SHU DAQIQADAGI holatida (snapshot) o'qib oladi, keyin
# ro'yxat o'zgarsa ham bu qayta o'qilmaydi. Natijada pastroqdagi
# qo'shimcha faylning YUQORI qismidagi reschedule_decide_v2 (~qator
# 1170) uchun umuman kech qolar edi, GET /api/reschedules
# (groups_lessons.py, main.py orqali - bu esa entry.py o'zining birinchi
# qatoridayoq to'liq import qilib bo'ladi) uchun esa HECH QACHON
# yetib bormas edi - u fayl entry.py ishga tushishidan OLDIN to'liq
# yuklanib bo'ladi. Amalda: HR menejer darsni TO'G'RIDAN-TO'G'RI
# ko'chira olardi (bu tekshiruv unga bog'liq emas edi), lekin
# ustozning kvotadan oshgan so'rovlarini KO'RA ("Bu amal uchun
# ruxsatingiz yo'q") ham, TASDIQLAY ham OLMASDI.
if roles.HR_MANAGER not in roles.RESCHEDULE_APPROVE:
    roles.RESCHEDULE_APPROVE.append(roles.HR_MANAGER)


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
#
#  MUHIM (2026-08-09 topildi): parents.py:parent_view() da qo'shilgan
#  parent_token_expires_at tekshiruvi shu YERGA — haqiqiy ishlaydigan
#  nusxaga — hech qachon ko'chirilmagan ekan. entry.py o'z ustidan
#  BUTUNLAY MUSTAQIL parent_view() yozadi (parents.py'nikini chaqirmay,
#  hammasini qaytadan yozadi) va _drop_route orqali uni almashtiradi —
#  demak parents.py'dagi muddat tekshiruvi HECH QACHON ishlamagan
#  (create_user_v2'da topilgan xuddi shu naqsh). Muddati o'tgan
#  havolalar shu paytgacha baribir ochilaverar edi. Endi shu yerga
#  ham qo'shildi — bu HAQIQIY jonli yo'l.
# =====================================================================
_drop_route("/api/parent/{token}", "GET")


# Ota-onaga ko'rsatiladigan yorliqlar — StudentDetail.tsx (KIND_LABEL)
# va src/lib/payments.ts (PAYMENT_METHODS) bilan bir xil so'zlar.
_PARENT_KIND_LABEL = {
    "payment": "To'lov", "charge": "Hisoblandi",
    "discount": "Chegirma", "refund": "Refund (qaytarildi)",
}
_PARENT_METHOD_LABEL = {
    "cash": "Naqd", "card": "Click",
    "terminal": "Terminal", "other": "Boshqa",
}


@app.get("/api/parent/{token}")
def parent_view(token: str, db: Session = Depends(get_db)):
    from datetime import datetime, timedelta
    from common import _gam_card, _xp_history, _student_ranks
    if not token or len(token) < 10:
        raise HTTPException(404, "Topilmadi")
    s = db.query(models.Student).filter(
        models.Student.parent_token == token).first()
    if not s:
        raise HTTPException(404, "Topilmadi")
    if (s.parent_token_expires_at
            and s.parent_token_expires_at < datetime.utcnow()):
        raise HTTPException(
            404, "Havola muddati tugagan. Administratordan yangi "
                 "havola so'rang.")
    g = db.query(models.Group).get(s.group_id) if s.group_id else None
    today = roles.local_today()
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

    # TO'LOVLAR TARIXI, COIN/XP, O'ZLASHTIRISH VA TEST NATIJALARI
    # (2026-08-09, Jahongir so'radi): avval faqat davomat va jami
    # balans ko'rinardi. MUHIM: bu funksiya haqiqiy jonli yo'l
    # (yuqoridagi izohga qarang — parents.py'dagi nusxa umuman
    # ishlamaydi), shuning uchun yangi qism aynan SHU YERGA
    # qo'shildi. Barchasi faqat shu bitta o'quvchi (s.id) bilan
    # cheklangan.
    pay_rows = (db.query(models.Payment)
                .filter(models.Payment.student_id == s.id)
                .order_by(models.Payment.created_at.desc())
                .limit(30).all())
    payments = [{
        "date": p.created_at.isoformat() if p.created_at else None,
        "amount": p.amount,
        "kind": _PARENT_KIND_LABEL.get(p.kind, p.kind),
        "method": (_PARENT_METHOD_LABEL.get(p.method, p.method)
                  if p.method else None),
        "note": p.note,
    } for p in pay_rows]

    gam = _gam_card(db, s)
    xp_history = [{
        "date": h["date"],
        "amount": h["amount"],
        "label": h["label"],
        "category_label": h["category_label"],
        "tone": h["tone"],
    } for h in _xp_history(db, s.id, limit=15)]

    grade_rows = (db.query(models.DailyGrade, models.Lesson)
                  .join(models.Lesson,
                        models.DailyGrade.lesson_id == models.Lesson.id)
                  .filter(models.DailyGrade.student_id == s.id)
                  .order_by(models.Lesson.date.desc()).limit(20).all())
    daily_grades = [{
        "date": ls.date.isoformat(),
        "score": dg.score,
    } for dg, ls in grade_rows]

    # Faqat TASDIQLANGAN yoki NATIJA KIRITILGAN testlar ko'rinsin —
    # qoralama (draft, hali Examiner tasdiqlamagan) va bekor qilingan
    # ko'rinmasin. TUZATILDI (2026-08-09): ilgari faqat "approved"
    # o'tkazilardi, lekin save_exam_results() natija kiritilgach
    # statusni "done"ga o'zgartiradi (exams.py) — demak haqiqiy
    # kiritilgan natijalar aynan shu holatga o'tgach ko'rinmay
    # qolardi. Endi ikkalasi ham hisobga olinadi.
    exam_rows = (db.query(models.ExamResult, models.Exam)
                 .join(models.Exam,
                       models.ExamResult.exam_id == models.Exam.id)
                 .filter(models.ExamResult.student_id == s.id,
                         models.Exam.status.in_(["approved", "done"]))
                 .order_by(models.Exam.date.desc()).limit(20).all())
    exam_results = [{
        "date": ex.date.isoformat() if ex.date else None,
        "title": ex.title or roles.exam_title(ex.kind, ex.unit_no),
        "score": er.score,
        "max_score": ex.max_score,
        "band": er.band,
        "percent": er.percent,
        "absent": bool(er.absent),
    } for er, ex in exam_rows]

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
        "payments": payments,
        "gamification": gam,
        "xp_history": xp_history,
        "daily_grades": daily_grades,
        "exam_results": exam_results,
        "ranks": _student_ranks(db, s.id),
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
    if user.role == roles.BRANCH_MANAGER \
            and not M._in_user_branches(db, user, payload.branch_id):
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
    # DIQQAT: bu funksiya auth_users.py:create_user()'ni TO'LIQ
    # ALMASHTIRADI (_drop_route yuqorida) - o'sha yerdagi audit.log
    # chaqiruvi bu yo'lda HECH QACHON ishga tushmaydi. Shuning uchun
    # audit yozuvi shu yerda, HAQIQIY ishlaydigan versiyada ham
    # takrorlanadi.
    audit.log(db, user, entity="user", action="create",
              entity_id=new_user.id, entity_label=new_user.full_name,
              note=f"Rol: {roles.UZ_LABELS.get(new_user.role, new_user.role)}",
              commit=True)
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
    """Berilgan yo'l+metodga mos endpoint funksiyasini topadi - pastda
    ko'plab joyda "_orig_xxx = _find_endpoint(...)" qilib asl
    funksiyani ushlab, keyin uni o'z ichida chaqiradigan "_v2" wrapper
    yozish uchun ishlatiladi.

    2026-08: main.py bo'lindi - _drop_route()dagi bilan bir xil sabab
    bilan (routerlar endi _IncludedRouter ichida joylashadi) bu yerda
    ham ichkariga qarab qidirish kerak, aks holda _orig_xxx doim None
    bo'lib, pastdagi "if _orig_xxx is not None:" bloklari sukut bilan
    ishlamay qolar edi (asl route ustidan yozilmasdan, eskisi xizmat
    qilishda davom etardi)."""
    def _matches(r):
        return getattr(r, "path", None) == path and \
            method in (getattr(r, "methods", None) or [])

    for r in app.router.routes:
        if _matches(r):
            return r.endpoint
        ic = getattr(r, "include_context", None)
        nested = getattr(ic, "included_router", None) if ic else None
        if nested is not None:
            for nr in nested.routes:
                if _matches(nr):
                    return nr.endpoint
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


# GET /api/reschedules (rahbariyat ro'yxati) - ilgari umuman
# almashtirilmagan edi, shuning uchun yuqoridagi (fayl boshidagi)
# tuzatish bo'lmasa ham, bo'lsa ham HR menejerga yetib bormas edi -
# main.py to'liq yuklanib bo'lgach (shu jumladan groups_lessons.py'ning
# @router.get("/api/reschedules") qatori) entry.py o'zining BIRINCHI
# qatoridayoq (`from main import ...`) shuni chaqiradi, ya'ni entry.py
# tanasi hali bitta ham qator ishlamasidan turib bu qaror allaqachon
# qabul qilingan bo'lardi.
_cur_reschedules_list = _find_endpoint("/api/reschedules", "GET")

if _cur_reschedules_list is not None:
    _drop_route("/api/reschedules", "GET")

    @app.get("/api/reschedules")
    def reschedules_list_v2(status: str | None = None,
                            db: Session = Depends(get_db),
                            user=Depends(require_role(
                                *roles.RESCHEDULE_APPROVE))):
        return _cur_reschedules_list(status=status, db=db, user=user)


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

# --- Jadval GRID ko'rinishida ham o'zgarishlar banneri ---
_orig_timetable_grid = _find_endpoint("/api/timetable/grid", "GET")

if _orig_timetable_grid is not None:
    _drop_route("/api/timetable/grid", "GET")

    @app.get("/api/timetable/grid")
    def timetable_grid_v2(day: str = "mon",
                          branch_id: int | None = None,
                          db: Session = Depends(get_db),
                          user=Depends(M.require_perm("timetable", "view"))):
        out = _orig_timetable_grid(day=day, branch_id=branch_id,
                                   db=db, user=user)
        try:
            gq = scope_to_branch(db.query(models.Group), models.Group,
                                 user, branch_id)
            gmap = {g.id: g for g in gq.all()}
            gids = set(gmap)
            today = date.today()
            horizon = today + _td(days=30)
            changes = []
            if gids:
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


# =====================================================================
#  OMBOR (kitoblar, qabul qilish, hisobot) + LID MAS'ULI + JAMOAVIY KPI
# =====================================================================
from datetime import datetime as _dt2

from database import SessionLocal as _SessionLocal

# "Admin" deb ikkala rol tushuniladi: sotuv menejeri (Administrator) va
# administrator (qabul). Lidga mas'ul faqat shulardan bo'ladi.
_ADMIN_ROLES = (roles.ADMINISTRATOR, roles.SALES_MANAGER)
_BOOK_KINDS = ("book", "welcome_pack")

# --- stock_moves: "qabul qilib oldim" ustunlari (idempotent ALTER) ---
try:
    _sm_cols = {c["name"]
                for c in _sa_inspect(_engine).get_columns("stock_moves")}
    with _engine.begin() as _con:
        if "accepted_by" not in _sm_cols:
            _con.execute(_sa_text(
                "ALTER TABLE stock_moves ADD COLUMN accepted_by INTEGER"))
        if "accepted_at" not in _sm_cols:
            _con.execute(_sa_text(
                "ALTER TABLE stock_moves ADD COLUMN accepted_at TIMESTAMP"))
except Exception:
    pass


# --- Har filialda standart kitoblar bo'lsin ---
def _seed_books() -> None:
    db = _SessionLocal()
    try:
        defaults = [("Step 1", "book"), ("Step 2", "book"),
                    ("Step 3", "book"), ("Welcome Pack", "welcome_pack"),
                    ("IELTS Introduction", "book"),
                    ("IELTS Foundation", "book"),
                    ("Family and Friends 0", "book"),
                    ("Family and Friends 1", "book"),
                    ("Family and Friends 2", "book"),
                    ("Family and Friends 3", "book"),
                    ("Round-up 0", "book"),
                    ("Round-up 1", "book"),
                    ("Round-up 2", "book"),
                    ("Round-up 3", "book"),
                    ("Round-up 4", "book")]
        added = False
        for b in db.query(models.Branch).all():
            for name, kind in defaults:
                exists = (db.query(models.Consumable)
                          .filter(models.Consumable.branch_id == b.id,
                                  func.lower(models.Consumable.name)
                                  == name.lower())
                          .first())
                if not exists:
                    db.add(models.Consumable(
                        name=name, kind=kind, branch_id=b.id,
                        qty=0, min_qty=0, unit="dona"))
                    added = True
        if added:
            db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


try:
    _seed_books()
except Exception:
    pass


# --- Lidga mas'ul bo'la oladiganlar: faqat adminlar ---
_orig_assignable = _find_endpoint("/api/users/assignable", "GET")

if _orig_assignable is not None:
    _drop_route("/api/users/assignable", "GET")

    @app.get("/api/users/assignable",
             response_model=list[schemas.StaffOption])
    def assignable_v2(db: Session = Depends(get_db),
                      user=Depends(require_role(*roles.LEAD_ACCESS))):
        """Ustoz va examiner mas'ul bo'lmaydi — faqat adminlar."""
        q = scope_to_branch(db.query(models.User), models.User, user)
        return (q.filter(models.User.is_active == 1,
                         models.User.role.in_(_ADMIN_ROLES))
                .order_by(models.User.full_name).all())


# --- Lid yaratish: admin kiritsa mas'ul avtomat o'zi ---
_orig_create_lead2 = _find_endpoint("/api/leads", "POST")

if _orig_create_lead2 is not None:
    _drop_route("/api/leads", "POST")

    @app.post("/api/leads", response_model=schemas.LeadOut)
    def create_lead_v2(payload: schemas.LeadCreate,
                       db: Session = Depends(get_db),
                       user: models.User = Depends(
                           require_role(*roles.LEAD_ACCESS))):
        if user.role in _ADMIN_ROLES:
            payload.assigned_user_id = user.id
        elif payload.assigned_user_id:
            a = db.query(models.User).get(payload.assigned_user_id)
            if not a or a.role not in _ADMIN_ROLES:
                raise HTTPException(
                    400, "Mas'ul xodim faqat administrator bo'la oladi")
        return _orig_create_lead2(payload=payload, db=db, user=user)


# --- Lid tahrirlash: mas'ulsiz lidni admin surse — o'zi mas'ul bo'ladi ---
_orig_update_lead2 = _find_endpoint("/api/leads/{lead_id}", "PUT")

if _orig_update_lead2 is not None:
    _drop_route("/api/leads/{lead_id}", "PUT")

    @app.put("/api/leads/{lead_id}", response_model=schemas.LeadOut)
    def update_lead_v2(lead_id: int, payload: schemas.LeadUpdate,
                       db: Session = Depends(get_db),
                       user: models.User = Depends(
                           require_role(*roles.LEAD_ACCESS))):
        want = getattr(payload, "assigned_user_id", None)
        if want:
            a = db.query(models.User).get(want)
            if not a or a.role not in _ADMIN_ROLES:
                raise HTTPException(
                    400, "Mas'ul xodim faqat administrator bo'la oladi")
        out = _orig_update_lead2(lead_id=lead_id, payload=payload,
                                 db=db, user=user)
        try:
            lead = db.query(models.Lead).get(lead_id)
            if (lead is not None and not lead.assigned_user_id
                    and user.role in _ADMIN_ROLES):
                lead.assigned_user_id = user.id
                db.commit()
                db.refresh(lead)
                out = lead
        except Exception:
            pass
        return out


# --- Marketing (inbox) lidi: filialda bitta admin bo'lsa — avtomat u ---
_orig_msg_lead = _find_endpoint("/api/inbox/{mid}/lead", "POST")

if _orig_msg_lead is not None:
    _drop_route("/api/inbox/{mid}/lead", "POST")

    @app.post("/api/inbox/{mid}/lead")
    def message_to_lead_v2(mid: int, payload: schemas.MessageToLead,
                           db: Session = Depends(get_db),
                           user=Depends(require_role(*roles.INBOX_ACCESS))):
        out = _orig_msg_lead(mid=mid, payload=payload, db=db, user=user)
        try:
            lid = out.get("lead_id") if isinstance(out, dict) else None
            lead = db.query(models.Lead).get(lid) if lid else None
            if lead is not None and not lead.assigned_user_id and lead.branch_id:
                admins = (db.query(models.User)
                          .filter(models.User.is_active == 1,
                                  models.User.role.in_(_ADMIN_ROLES),
                                  models.User.branch_id == lead.branch_id)
                          .all())
                if len(admins) == 1:
                    lead.assigned_user_id = admins[0].id
                    db.commit()
        except Exception:
            pass
        return out


# --- Kitoblar ro'yxati (to'lov oynasi uchun) ---
_INV_BOOK_ROLES = tuple(dict.fromkeys(
    list(roles.INVENTORY_VIEW) + list(_ADMIN_ROLES)))


@app.get("/api/consumables/books")
def list_books_v2(branch_id: int | None = None,
                  db: Session = Depends(get_db),
                  user=Depends(require_role(*_INV_BOOK_ROLES))):
    q = scope_to_branch(db.query(models.Consumable), models.Consumable,
                        user, branch_id)
    rows = (q.filter(models.Consumable.kind.in_(_BOOK_KINDS))
            .order_by(models.Consumable.name).all())
    if not rows:
        # Yangi filial — standart kitoblarni shu yerda ham yaratib olamiz
        _seed_books()
        rows = (q.filter(models.Consumable.kind.in_(_BOOK_KINDS))
                .order_by(models.Consumable.name).all())
    return [{"id": c.id, "name": c.name, "qty": c.qty or 0,
             "unit": c.unit or "dona", "branch_id": c.branch_id}
            for c in rows]


# --- Kitob berish (yangi to'lov bilan): ombordan kamayadi ---
class _GiveBookIn(_BM):
    student_id: int | None = None
    note: str | None = None


@app.post("/api/consumables/{cid}/give-book")
def give_book_v2(cid: int, payload: _GiveBookIn,
                 db: Session = Depends(get_db),
                 user=Depends(require_role(*_INV_BOOK_ROLES))):
    c = db.query(models.Consumable).get(cid)
    if not c:
        raise HTTPException(404, "Mahsulot topilmadi")
    if (c.qty or 0) < 1:
        raise HTTPException(
            409, f"Omborda yo'q: \"{c.name}\" qoldig'i 0. "
                 "Filial rahbariga ayting — kirim qilinsin.")
    st = (db.query(models.Student).get(payload.student_id)
          if payload.student_id else None)
    note = "Kitob berildi (to'lov bilan)"
    if st:
        note += f": {st.full_name}"
    if payload.note:
        note += f" — {payload.note}"
    db.add(models.StockMove(consumable_id=c.id, delta=-1, reason="out",
                            note=note, created_by=user.full_name))
    c.qty = (c.qty or 0) - 1
    db.commit()
    try:
        M._check_stock(db, c)
        db.commit()
    except Exception:
        pass
    return {"ok": True, "qty": c.qty, "name": c.name}


# --- Qabul qilinmagan kirimlar ---
@app.get("/api/stock-moves/pending")
def pending_stock_moves_v2(branch_id: int | None = None,
                           db: Session = Depends(get_db),
                           user=Depends(require_role(*_INV_BOOK_ROLES))):
    rows = db.execute(_sa_text(
        "SELECT sm.id, sm.delta, sm.note, sm.created_by, sm.created_at, "
        "c.name, c.unit, c.branch_id "
        "FROM stock_moves sm JOIN consumables c ON c.id = sm.consumable_id "
        "WHERE sm.reason = 'in' AND sm.accepted_at IS NULL "
        "ORDER BY sm.created_at DESC")).fetchall()
    if user.role in tuple(roles.ORG_WIDE_ROLES):
        bid = branch_id
    else:
        bid = user.branch_id
    bnames = {b.id: b.name for b in db.query(models.Branch).all()}
    out = []
    for r in rows:
        if bid and r[7] and r[7] != bid:
            continue
        out.append({
            "id": r[0], "qty": abs(r[1] or 0), "note": r[2], "by": r[3],
            "created_at": (r[4].isoformat()
                           if hasattr(r[4], "isoformat") else str(r[4] or "")),
            "name": r[5], "unit": r[6] or "dona",
            "branch": bnames.get(r[7], "—"),
        })
    return {"rows": out,
            "can_accept": user.role in
            ((roles.FOUNDER, roles.BRANCH_MANAGER) + _ADMIN_ROLES)}


# --- Kirimni qabul qilish: filial rahbari, bo'lmasa admin ---
@app.post("/api/stock-moves/{mid}/accept")
def accept_stock_move_v2(mid: int, db: Session = Depends(get_db),
                         user=Depends(require_role(
                             roles.FOUNDER, roles.BRANCH_MANAGER,
                             *_ADMIN_ROLES))):
    row = db.execute(_sa_text(
        "SELECT sm.id, sm.reason, sm.accepted_at, c.branch_id, c.name "
        "FROM stock_moves sm JOIN consumables c ON c.id = sm.consumable_id "
        "WHERE sm.id = :i"), {"i": mid}).fetchone()
    if not row:
        raise HTTPException(404, "Harakat topilmadi")
    if row[1] != "in":
        raise HTTPException(400, "Faqat kirim qabul qilinadi")
    if row[2] is not None:
        raise HTTPException(400, "Bu kirim allaqachon qabul qilingan")
    bid = row[3]
    if (user.role != roles.FOUNDER and user.branch_id and bid
            and user.branch_id != bid):
        raise HTTPException(403, "Bu boshqa filialning ombori")
    if user.role in _ADMIN_ROLES:
        bm = (db.query(models.User)
              .filter(models.User.role == roles.BRANCH_MANAGER,
                      models.User.is_active == 1,
                      models.User.branch_id == bid)
              .first())
        if bm:
            raise HTTPException(
                403, f"Qabul qilishni filial rahbari ({bm.full_name}) "
                     "belgilashi kerak")
    db.execute(_sa_text(
        "UPDATE stock_moves SET accepted_by = :u, accepted_at = :t "
        "WHERE id = :i"),
        {"u": user.id, "t": _dt2.utcnow(), "i": mid})
    db.commit()
    return {"ok": True}


# --- Kitob hisoboti: qaysi filialda nechta qoldi ---
_BOOK_REPORT_ALL = (roles.FOUNDER, roles.FINANCE_DIRECTOR,
                    roles.FACILITY_MANAGER, roles.HR_MANAGER)


@app.get("/api/inventory/book-report")
def book_report_v2(db: Session = Depends(get_db),
                   user=Depends(require_role(
                       *(_BOOK_REPORT_ALL + (roles.BRANCH_MANAGER,))))):
    q = db.query(models.Consumable).filter(
        models.Consumable.kind.in_(_BOOK_KINDS))
    if user.role == roles.BRANCH_MANAGER and user.branch_id:
        q = q.filter(models.Consumable.branch_id == user.branch_id)
    bnames = {b.id: b.name for b in db.query(models.Branch).all()}
    rows = q.all()
    names = sorted({c.name for c in rows})
    per: dict = {}
    for c in rows:
        b = bnames.get(c.branch_id, "Filialsiz")
        per.setdefault(b, {})
        per[b][c.name] = (per[b].get(c.name, 0) or 0) + (c.qty or 0)
    return {
        "books": names,
        "rows": [{"branch": b,
                  "counts": {n: v.get(n, 0) for n in names},
                  "total": sum(v.values())}
                 for b, v in sorted(per.items())],
    }


# --- Adminlar KPI: eski to'lov yig'ish JAMOAVIY (filial bo'yicha) ---
_drop_route("/api/kpi/admins", "GET")


@app.get("/api/kpi/admins", response_model=schemas.AdminKpiResult)
def admin_kpi_v2(year: int, month: int, db: Session = Depends(get_db),
                 user=Depends(require_role(*roles.KPI_VIEW))):
    """Eski to'lovlarni yig'ish — jamoaviy bonus: filialdagi UMUMIY
    yig'ilgan summa bilan o'lchanadi (mas'ul xodimga bo'linmaydi).
    Bir filialda ikkita admin bo'lsa, ikkalasiga ham to'liq bonus.
    Administrator (qabul) roli ham ro'yxatga kiradi."""
    start, end = _billing.month_bounds(year, month)
    period = M._period_key(year, month)
    start_dt, end_dt = M._utc_window(start, end)

    admins = db.query(models.User).filter(
        models.User.role.in_(_ADMIN_ROLES),
        models.User.is_active == 1,
    )
    if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
        admins = admins.filter(models.User.branch_id == user.branch_id)
    admins = admins.order_by(models.User.full_name).all()
    if not admins:
        return schemas.AdminKpiResult(period=period, rows=[])

    first_paid = M._first_payment_dates(db)
    students = db.query(models.Student).all()
    student_branch = {s.id: s.branch_id for s in students}

    stats: dict = {}
    for a in admins:
        if a.branch_id in stats:
            continue
        stats[a.branch_id] = {
            "active_students": sum(
                1 for s in students
                if s.branch_id == a.branch_id and s.status == "active"),
            "expected": 0.0, "collected": 0.0,
            "new_clients": set(), "new_revenue": 0.0,
        }

    charges = db.query(models.Payment).filter(
        models.Payment.kind == "charge",
        models.Payment.created_at >= start_dt,
        models.Payment.created_at <= end_dt,
    ).all()
    for c in charges:
        st = stats.get(student_branch.get(c.student_id))
        if st is None:
            continue
        first = first_paid.get(c.student_id)
        if first is None or first >= start_dt:
            continue
        st["expected"] += abs(c.amount)

    pays = db.query(models.Payment).filter(
        models.Payment.kind == "payment",
        models.Payment.created_at >= start_dt,
        models.Payment.created_at <= end_dt,
    ).all()
    for p in pays:
        st = stats.get(student_branch.get(p.student_id))
        if st is None:
            continue
        first = first_paid.get(p.student_id)
        if first is not None and first >= start_dt:
            st["new_clients"].add(p.student_id)
            st["new_revenue"] += p.amount
        else:
            st["collected"] += p.amount

    rows = []
    for a in admins:
        st = stats[a.branch_id]
        pct = (round(st["collected"] / st["expected"] * 100, 1)
               if st["expected"] else 0.0)
        col_bonus = M._collection_bonus(db, st["active_students"], pct)
        new_count = len(st["new_clients"])
        new_bonus = M._new_client_bonus(db, new_count)
        fix = a.fix_salary or 0.0
        if (user.role not in
                tuple(roles.FULL_ACCESS + [roles.FINANCE_DIRECTOR])
                and a.id != user.id):
            continue
        rows.append(schemas.AdminKpi(
            user_id=a.id, full_name=a.full_name, branch_id=a.branch_id,
            branch=a.branch.name if a.branch else None,
            fix_salary=fix,
            active_students=st["active_students"],
            expected=st["expected"], collected=st["collected"],
            collection_percent=pct, collection_bonus=col_bonus,
            new_clients=new_count, new_client_revenue=st["new_revenue"],
            new_client_bonus=new_bonus,
            total=fix + col_bonus + new_bonus,
        ))
    return schemas.AdminKpiResult(period=period, rows=rows)


# MyProfile ham shu hisobdan foydalanadi
M.admin_kpi = admin_kpi_v2

# =====================================================================
#  RUNTIME ROL OVERRIDE — roles.py fayli katta, o'zgarishlar shu yerda
# =====================================================================
# Audit ro'yxati: moliyachi va bosh examiner chiqadi, HR kiradi.
roles.AUDIT_VIEW[:] = [roles.FOUNDER, roles.BRANCH_MANAGER,
                       roles.HR_MANAGER]
# SMM (kontent so'rovi) — o'quv bo'limi rahbariga kerak emas.
roles.CONTENT_REQUESTER[:] = [r for r in roles.CONTENT_REQUESTER
                              if r != roles.ACADEMIC_HEAD]
# Ruxsat matritsasi (runtime o'qiladi):
try:
    roles.DEFAULT_MATRIX[roles.FINANCE_DIRECTOR].pop("audit", None)
    roles.DEFAULT_MATRIX[roles.HEAD_EXAMINER].pop("audit", None)
    roles.DEFAULT_MATRIX[roles.HR_MANAGER]["audit"] = {"view", "export"}
except Exception:
    pass

# Audit endpointlari dekoratsiya paytida eski ro'yxatni "muhrlab" olgan —
# yangi ro'yxat bilan qayta ulaymiz.
_orig_audit_list = _find_endpoint("/api/audit", "GET")
_orig_audit_meta = _find_endpoint("/api/audit/meta", "GET")

if _orig_audit_list is not None:
    _drop_route("/api/audit", "GET")

    @app.get("/api/audit")
    def audit_list_v2(entity: str | None = None,
                      entity_id: int | None = None,
                      action: str | None = None,
                      user_id: int | None = None,
                      days: int = 90,
                      limit: int = 200,
                      db: Session = Depends(get_db),
                      user=Depends(require_role(
                          roles.FOUNDER, roles.BRANCH_MANAGER,
                          roles.HR_MANAGER))):
        return _orig_audit_list(entity=entity, entity_id=entity_id,
                                action=action, user_id=user_id, days=days,
                                limit=limit, db=db, user=user)

if _orig_audit_meta is not None:
    _drop_route("/api/audit/meta", "GET")

    @app.get("/api/audit/meta")
    def audit_meta_v2(user=Depends(require_role(
            roles.FOUNDER, roles.BRANCH_MANAGER, roles.HR_MANAGER))):
        return _orig_audit_meta(user=user)

# =====================================================================
#  HR MENEJERGA QO'SHIMCHA HUQUQLAR
#  Eski yo'qlama qo'yish, guruh ochish/tahrirlash, o'quvchi qo'shish.
# =====================================================================
_HRM = roles.HR_MANAGER

# O'tgan kun yo'qlamasi — endpoint ichida runtime tekshiriladi:
roles.PAST_ATTENDANCE[:] = [roles.FOUNDER, roles.ACADEMIC_HEAD, _HRM]
# Guruh boshqaruvi ro'yxatiga ham (runtime o'qiydigan joylar uchun):
if _HRM not in roles.GROUP_MANAGE:
    roles.GROUP_MANAGE.append(_HRM)

# Ruxsat matritsasi (Ruxsatlar sahifasida ham to'g'ri ko'rinsin):
try:
    _hrm_m = roles.DEFAULT_MATRIX[roles.HR_MANAGER]
    _hrm_m["students"] = {"view", "create", "edit"}
    _hrm_m["groups"] = {"view", "create", "edit"}
    _hrm_m["attendance"] = {"view", "create", "edit"}
except Exception:
    pass


# Yo'qlama saqlash — HR ham (o'tgan kunlar uchun ham, tepadagi
# PAST_ATTENDANCE ro'yxati orqali):
_orig_save_att = _find_endpoint("/api/lessons/{lesson_id}/attendance",
                                "PUT")

if _orig_save_att is not None:
    _drop_route("/api/lessons/{lesson_id}/attendance", "PUT")

    @app.put("/api/lessons/{lesson_id}/attendance")
    def save_attendance_v2(lesson_id: int,
                           payload: schemas.AttendanceBulk,
                           db: Session = Depends(get_db),
                           user=Depends(require_role(
                               *(tuple(roles.TEACHING_ACCESS) + (_HRM,))))):
        return _orig_save_att(lesson_id=lesson_id, payload=payload,
                              db=db, user=user)


# Dars (yo'qlama kuni) qo'shish — HR ham:
_orig_add_lesson = _find_endpoint("/api/groups/{group_id}/lessons", "POST")

if _orig_add_lesson is not None:
    _drop_route("/api/groups/{group_id}/lessons", "POST")

    @app.post("/api/groups/{group_id}/lessons",
              response_model=schemas.LessonOut)
    def add_lesson_v2(group_id: int, payload: schemas.LessonCreate,
                      db: Session = Depends(get_db),
                      user: models.User = Depends(require_role(
                          *(tuple(roles.TEACHING_STAFF) + (_HRM,))))):
        return _orig_add_lesson(group_id=group_id, payload=payload,
                                db=db, user=user)


# Guruh ochish/tahrirlash — HR ham (junior chegara nazorati saqlanadi):
_cur_create_group = _find_endpoint("/api/groups", "POST")
_cur_update_group = _find_endpoint("/api/groups/{group_id}", "PUT")

if _cur_create_group is not None:
    _drop_route("/api/groups", "POST")

    @app.post("/api/groups")
    def create_group_v3(payload: schemas.GroupCreate,
                        force: bool = False,
                        db: Session = Depends(get_db),
                        user=Depends(require_role(*roles.GROUP_MANAGE))):
        return _cur_create_group(payload=payload, force=force,
                                 db=db, user=user)

if _cur_update_group is not None:
    _drop_route("/api/groups/{group_id}", "PUT")

    @app.put("/api/groups/{group_id}")
    def update_group_v3(group_id: int, payload: schemas.GroupUpdate,
                        force: bool = False,
                        db: Session = Depends(get_db),
                        user=Depends(require_role(*roles.GROUP_MANAGE))):
        return _cur_update_group(group_id=group_id, payload=payload,
                                 force=force, db=db, user=user)


# O'quvchi qo'shish/tahrirlash — HR ham:
_cur_create_student = _find_endpoint("/api/students", "POST")
_cur_update_student = _find_endpoint("/api/students/{student_id}", "PUT")

if _cur_create_student is not None:
    _drop_route("/api/students", "POST")

    @app.post("/api/students", response_model=schemas.StudentOut)
    def create_student_v2(payload: schemas.StudentCreate,
                          force: bool = False,
                          db: Session = Depends(get_db),
                          user=Depends(require_role(
                              *(tuple(roles.TEACHING_STAFF) + (_HRM,))))):
        return _cur_create_student(payload=payload, force=force,
                                   db=db, user=user)

if _cur_update_student is not None:
    _drop_route("/api/students/{student_id}", "PUT")

    @app.put("/api/students/{student_id}",
             response_model=schemas.StudentOut)
    def update_student_v2(student_id: int, payload: schemas.StudentUpdate,
                          force: bool = False,
                          db: Session = Depends(get_db),
                          user=Depends(require_role(
                              *(tuple(roles.TEACHING_STAFF) + (_HRM,))))):
        return _cur_update_student(student_id=student_id, payload=payload,
                                   force=force, db=db, user=user)


# =====================================================================
#  LIDLAR: HAR FILIALNING O'Z HUDUD/MAKTAB RO'YXATI
#  (avval Zafar mahallalari hamma filialga chiqib turardi)
# =====================================================================
import re as _re2

_BEKOBOD1_AREAS = [
    "Metal", "11-mikrarayon", "12-mikrarayon", "13-mikrarayon", "Kirf",
    "Gidrometriya", "Xos", "Taqachi", "Navoiy",
]
_BEKOBOD2_AREAS = [
    "3-mikrarayon", "Semetchi", "Shaxmat", "Semgorodok",
]
_STRETINKO_AREAS = [
    "Stretinko", "Xos", "Navoiy", "20-brigada",
]
roles.BRANCH_AREAS["Bekobod 1"] = _BEKOBOD1_AREAS
roles.BRANCH_AREAS["Bekobod 2"] = _BEKOBOD2_AREAS
roles.BRANCH_AREAS["Stretinko"] = _STRETINKO_AREAS


def _norm_bname(s):
    return _re2.sub(r"[^a-z0-9]+", "", (s or "").lower())


def _areas_for_branch_v2(name):
    """Aniq mos kelmasa ham (masalan "Bekobod-1" yozilsa) filialni
    taniydi — nomlar biroz farqlansa ro'yxat aralashib ketmasin."""
    if name:
        if name in roles.BRANCH_AREAS:
            return roles.BRANCH_AREAS[name]
        key = _norm_bname(name)
        for bname, lst in roles.BRANCH_AREAS.items():
            nb = _norm_bname(bname)
            if nb and (nb == key or nb in key):
                return lst
    # Filial noma'lum - hammasini birlashtirib ko'rsatamiz
    out = []
    for lst in roles.BRANCH_AREAS.values():
        for a in lst:
            if a not in out:
                out.append(a)
    return out


roles.areas_for_branch = _areas_for_branch_v2

# Maktablar: Bekobod 1 va Bekobod 2'da 1-25 + ixtisoslashgan. Boshqa
# filiallarda hozircha umumiy ro'yxat (1-60) qoladi - alohida ro'yxat
# aytilmagan.
_SCHOOLS_1_25 = [f"{i}-maktab" for i in range(1, 26)] + [
    "Ixtisoslashgan maktab"]
_BRANCH_SCHOOLS = {"Bekobod 1": _SCHOOLS_1_25, "Bekobod 2": _SCHOOLS_1_25}


def _schools_for_branch(name):
    if name:
        if name in _BRANCH_SCHOOLS:
            return _BRANCH_SCHOOLS[name]
        key = _norm_bname(name)
        for bname, lst in _BRANCH_SCHOOLS.items():
            if _norm_bname(bname) == key:
                return lst
    return roles.SCHOOLS


_orig_reference = _find_endpoint("/api/reference", "GET")

if _orig_reference is not None:
    _drop_route("/api/reference", "GET")

    @app.get("/api/reference")
    def reference_v2(branch_id: int | None = None,
                     db: Session = Depends(get_db),
                     user: models.User = Depends(get_current_user)):
        bname = None
        bid = branch_id or user.branch_id
        if bid:
            b = db.query(models.Branch).get(bid)
            bname = b.name if b else None
        return {
            "areas": _areas_for_branch_v2(bname),
            "schools": _schools_for_branch(bname),
            "lesson_times": [
                {"start": t, "end": roles.lesson_end_time(t),
                 "label": roles.lesson_time_range(t)}
                for t in roles.LESSON_START_TIMES
            ],
            "lesson_minutes": roles.LESSON_DURATION_MINUTES,
            "exit_types": [{"key": k, "label": lbl, "hint": h}
                           for k, lbl, h in roles.EXIT_TYPES],
            "archive_groups": [{"key": k, "label": lbl, "hint": h}
                               for k, lbl, h in roles.ARCHIVE_GROUPS],
        }


# =====================================================================
#  MUZLATILGAN O'QUVCHI YO'QLAMADA HECH KIMGA KO'RINMASIN
#  Yo'qlama - oylik hisoblanadigan hujjat, shuning uchun muzlatilgan
#  o'quvchi ko'rinib, xato yo'qlama qo'yib qo'yilmasin.
#
#  2026-08-09: bu tekshiruv ilgari FAQAT `role == TEACHER` bo'lsa
#  ishlagan — HR menejer, asoschi, filial rahbari va boshqa
#  rollarga muzlatilgan o'quvchi hali ham to'liq qator bo'lib,
#  yoqlama belgisi bilan chiqaverardi (Jahongir skrinshot bilan
#  ko'rsatdi: muzlatilgan o'quvchiga "03 avg" kuni belgi qo'yilgan
#  edi). Sabab (yo'qlama — ish haqi hujjati) ROLGA BOG'LIQ EMAS,
#  shuning uchun endi HAMMA uchun bir xil qo'llanadi.
# =====================================================================
_orig_att_grid = _find_endpoint("/api/groups/{group_id}/attendance", "GET")

if _orig_att_grid is not None:
    _drop_route("/api/groups/{group_id}/attendance", "GET")

    @app.get("/api/groups/{group_id}/attendance",
             response_model=schemas.AttendanceGrid)
    def attendance_grid_v2(group_id: int, year: int, month: int,
                           db: Session = Depends(get_db),
                           user=Depends(require_role(
                               *roles.ATTENDANCE_VIEW))):
        result = _orig_att_grid(group_id=group_id, year=year, month=month,
                                db=db, user=user)
        try:
            data = result.model_dump()
        except AttributeError:
            data = result.dict()
        data["students"] = [s for s in data["students"]
                            if s.get("status") != "frozen"]
        return data


# =====================================================================
#  ADMINISTRATOR ROLLARI BITTA BO'LDI
#  "Administrator" va "Administrator (qabul)" amalda bir xil ish edi.
#  Eski hisoblar sales_manager'ga ko'chiriladi, tanlov ro'yxatidan
#  esa "qabul" varianti olib tashlanadi.
# =====================================================================
roles.UZ_LABELS[roles.ADMINISTRATOR] = "Administrator"
roles.ALL_ROLES[:] = [r for r in roles.ALL_ROLES
                      if r != roles.ADMINISTRATOR]
for _i, _grp in enumerate(roles.ROLE_GROUPS):
    if _grp[0] == "sales":
        roles.ROLE_GROUPS[_i] = (
            _grp[0], _grp[1],
            [r for r in _grp[2] if r != roles.ADMINISTRATOR])


def _merge_admin_roles() -> None:
    """Bir martalik ko'chirish. Takror chaqirilsa hech narsa qilmaydi."""
    db = _SessionLocal()
    try:
        n = (db.query(models.User)
             .filter(models.User.role == roles.ADMINISTRATOR)
             .update({models.User.role: roles.SALES_MANAGER},
                     synchronize_session=False))
        if n:
            db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


try:
    _merge_admin_roles()
except Exception:
    pass


# =====================================================================
#  XODIM OYLIGI: BERILGAN PULNI YOZIB BORISH
#  Ustozlarda TeacherPayment bor, lekin examinerda Ustoz kartasi yo'q.
#  Shuning uchun user_id'ga bog'langan umumiy jadval.
# =====================================================================
from datetime import datetime as _dt  # noqa: E402
from sqlalchemy import Column, DateTime, Float, Integer, String  # noqa: E402
from sqlalchemy import Date as _SaDate  # noqa: E402
from database import Base as _Base, engine as _engine  # noqa: E402

if getattr(models, "StaffSalaryPayment", None) is None:
    class StaffSalaryPayment(_Base):
        """Xodimga HAQIQATDA berilgan pul: oylik, avans yoki tuzatish.

        Ishlab topilgani har oy formuladan qayta hisoblanadi va hech
        qayerda saqlanmaydi; bu jadval faqat kassadan chiqqan pulni
        yozadi. Qoldiq = ishlab topgan - berilgan."""

        __tablename__ = "staff_salary_payments"
        __table_args__ = {"extend_existing": True}

        id = Column(Integer, primary_key=True, index=True)
        user_id = Column(Integer, index=True, nullable=False)
        amount = Column(Float, nullable=False)
        kind = Column(String, default="salary")
        period = Column(String, index=True)
        paid_on = Column(_SaDate, default=date.today)
        method = Column(String, default="cash")
        note = Column(String)
        created_by = Column(String)
        created_at = Column(DateTime, default=_dt.utcnow)

    models.StaffSalaryPayment = StaffSalaryPayment
    try:
        _Base.metadata.create_all(
            bind=_engine, tables=[StaffSalaryPayment.__table__])
    except Exception:
        pass

_SSP = models.StaffSalaryPayment

_SALARY_KINDS = [("salary", "Oylik"), ("advance", "Avans"),
                 ("correction", "Tuzatish")]
_SALARY_KIND_LABELS = dict(_SALARY_KINDS)

# Oyliklarni Moliya bo'limida ko'radigan va to'laydiganlar
_PAYROLL_VIEW = list(dict.fromkeys(
    list(roles.SALARY_PAY) + [roles.HR_MANAGER, roles.ACADEMIC_HEAD,
                              roles.HEAD_EXAMINER, roles.HEAD_SUPPORT]))
_PAYROLL_PAY = list(roles.SALARY_PAY)


def _staff_paid(db: Session, user_id: int, period: str | None = None):
    q = db.query(func.coalesce(func.sum(_SSP.amount), 0.0)).filter(
        _SSP.user_id == user_id)
    if period:
        q = q.filter(_SSP.period == period)
    return round(float(q.scalar() or 0.0), 2)


def _attach_paid(db: Session, data: dict, key: str, period: str) -> dict:
    """Oylik ro'yxatiga "berilgan" va "qoldiq" ustunlarini qo'shadi."""
    for r in data.get("rows", []):
        uid = r.get(key)
        if uid is None:
            continue
        paid = _staff_paid(db, uid, period)
        r["paid"] = paid
        r["left"] = round((r.get("salary") or 0) - paid, 2)
    data["paid_total"] = round(
        sum(r.get("paid", 0) for r in data.get("rows", [])), 2)
    data["left_total"] = round(
        sum(r.get("left", 0) for r in data.get("rows", [])), 2)
    data["kinds"] = [{"key": k, "label": lbl} for k, lbl in _SALARY_KINDS]
    return data


# --- Examiner oyliklari: Moliya ham ko'rsin + berilgan pul ko'rinsin ---
_orig_ex_salary = _find_endpoint("/api/examiners/salary", "GET")

if _orig_ex_salary is not None:
    _drop_route("/api/examiners/salary", "GET")

    @app.get("/api/examiners/salary")
    def examiner_salary_v2(year: int | None = None, month: int | None = None,
                           db: Session = Depends(get_db),
                           user=Depends(require_role(
                               *list(dict.fromkeys(
                                   list(roles.EXAMINER_SALARY_VIEW)
                                   + _PAYROLL_VIEW))))):
        data = _orig_ex_salary(year=year, month=month, db=db, user=user)
        data = _attach_paid(db, data, "user_id", data.get("period", ""))
        data["can_pay"] = user.role in tuple(_PAYROLL_PAY)
        return data


# --- Support teacher oyliklari: xuddi shunday ---
_orig_su_salary = _find_endpoint("/api/support/salary", "GET")

if _orig_su_salary is not None:
    _drop_route("/api/support/salary", "GET")

    @app.get("/api/support/salary")
    def support_salary_v2(year: int | None = None, month: int | None = None,
                          db: Session = Depends(get_db),
                          user=Depends(require_role(
                              *list(dict.fromkeys(
                                  list(roles.SALARY_VIEW_ALL)
                                  + [roles.ACADEMIC_HEAD]
                                  + _PAYROLL_VIEW))))):
        data = _orig_su_salary(year=year, month=month, db=db, user=user)
        # Support teacherda Ustoz kartasi bor — user_id ni topib beramiz
        for r in data.get("rows", []):
            t = db.query(models.Teacher).get(r.get("teacher_id"))
            r["user_id"] = t.user_id if t else None
        data = _attach_paid(db, data, "user_id", data.get("period", ""))
        data["can_pay"] = user.role in tuple(_PAYROLL_PAY)
        return data


@app.post("/api/staff-salary")
def staff_salary_pay(payload: dict, db: Session = Depends(get_db),
                     user=Depends(require_role(*_PAYROLL_PAY))):
    """Xodimga oylik/avans berish. Bitta tugma — bitta yozuv."""
    uid = payload.get("user_id")
    amount = payload.get("amount")
    kind = payload.get("kind") or "salary"
    if not uid:
        raise HTTPException(400, "Xodim tanlanmadi")
    if kind not in _SALARY_KIND_LABELS:
        raise HTTPException(400, "Noto'g'ri to'lov turi")
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        amount = 0.0
    if amount <= 0:
        raise HTTPException(400, "Summani kiriting")
    u = db.query(models.User).get(int(uid))
    if not u:
        raise HTTPException(404, "Xodim topilmadi")
    if (user.role == roles.BRANCH_MANAGER and u.branch_id
            and not M._in_user_branches(db, user, u.branch_id)):
        raise HTTPException(403, "Faqat o'z filialingiz xodimiga "
                                 "oylik bera olasiz")
    period = payload.get("period") or date.today().isoformat()[:7]
    row = _SSP(user_id=u.id, amount=round(amount, 2), kind=kind,
               period=period, paid_on=date.today(),
               method=payload.get("method") or "cash",
               note=payload.get("note"), created_by=user.full_name)
    db.add(row)
    db.commit()
    db.refresh(row)
    audit.log(db, user, entity="user", action="salary_change",
              entity_id=u.id, entity_label=u.full_name,
              branch_id=u.branch_id,
              field=_SALARY_KIND_LABELS[kind],
              new_value=f"{amount:,.0f}".replace(",", " "))
    db.commit()
    return {"ok": True, "id": row.id,
            "paid": _staff_paid(db, u.id, period)}


@app.get("/api/staff-salary")
def staff_salary_list(user_id: int, period: str | None = None,
                      db: Session = Depends(get_db),
                      user=Depends(require_role(*_PAYROLL_VIEW))):
    q = db.query(_SSP).filter(_SSP.user_id == user_id)
    if period:
        q = q.filter(_SSP.period == period)
    rows = q.order_by(_SSP.paid_on.desc(), _SSP.id.desc()).all()
    return {
        "rows": [{"id": r.id, "amount": r.amount, "kind": r.kind,
                  "kind_label": _SALARY_KIND_LABELS.get(r.kind, r.kind),
                  "period": r.period,
                  "date": r.paid_on.isoformat() if r.paid_on else None,
                  "method": r.method, "note": r.note,
                  "created_by": r.created_by} for r in rows],
        "total": round(sum(r.amount for r in rows), 2),
        "can_pay": user.role in tuple(_PAYROLL_PAY),
    }


@app.delete("/api/staff-salary/{row_id}")
def staff_salary_delete(row_id: int, db: Session = Depends(get_db),
                        user=Depends(require_role(*_PAYROLL_PAY))):
    r = db.query(_SSP).get(row_id)
    if not r:
        raise HTTPException(404, "Topilmadi")
    u = db.query(models.User).get(r.user_id)
    audit.log(db, user, entity="user", action="delete", entity_id=r.user_id,
              entity_label=u.full_name if u else "—",
              field="Xodim oyligi",
              old_value=f"{r.amount:,.0f}".replace(",", " "))
    db.delete(r)
    db.commit()
    return {"ok": True}


# =====================================================================
#  SHU OY TO'LOV QILGANLAR RO'YXATI
#  Administrator har kuni "kim to'ladi?" deb so'raydi — endi ro'yxat
#  Moliya bo'limining o'zida turadi. Xarajat va foyda bu yerda YO'Q,
#  shuning uchun administratorga ham ochiq.
# =====================================================================
_PAYLIST_VIEW = list(dict.fromkeys([
    roles.FOUNDER, roles.BRANCH_MANAGER, roles.FINANCE_DIRECTOR,
    roles.ACCOUNTANT, roles.SALES_MANAGER, roles.ADMINISTRATOR,
]))


@app.get("/api/payments/month")
def payments_of_month(year: int | None = None, month: int | None = None,
                      branch_id: int | None = None,
                      db: Session = Depends(get_db),
                      user=Depends(require_role(*_PAYLIST_VIEW))):
    """Bir oyda kelib tushgan to'lovlar — o'quvchi kesimida.

    Yangi mijoz (birinchi to'lovi shu oyda) alohida belgilanadi, chunki
    administrator bonusi eski va yangi to'lov uchun boshqa-boshqa."""
    today = roles.local_today()
    y = year or today.year
    m = month or today.month
    start, end = M.billing.month_bounds(y, m)
    d0, d1 = M._utc_window(start, end)

    q = (db.query(models.Payment, models.Student)
         .join(models.Student,
               models.Payment.student_id == models.Student.id)
         .filter(models.Payment.kind == "payment",
                 models.Payment.created_at >= d0,
                 models.Payment.created_at <= d1))
    if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
        q = q.filter(models.Student.branch_id == user.branch_id)
    elif branch_id:
        q = q.filter(models.Student.branch_id == branch_id)

    first_dates = M._payment_first_dates(db)
    branches = {b.id: b.name for b in db.query(models.Branch).all()}
    method_labels = dict(getattr(roles, "PAYMENT_METHOD_LABELS", {}) or {})

    rows, total, new_sum, old_sum = [], 0.0, 0.0, 0.0
    for p, st in q.all():
        is_new = first_dates.get(st.id) == p.created_at
        total += p.amount
        if is_new:
            new_sum += p.amount
        else:
            old_sum += p.amount
        method = p.method or "cash"
        rows.append({
            "id": p.id,
            "date": p.created_at.date().isoformat() if p.created_at else None,
            "student_id": st.id,
            "student": st.full_name,
            "phone": st.phone,
            "amount": p.amount,
            "method": method,
            "method_label": method_labels.get(method, method),
            "branch": branches.get(st.branch_id) or "—",
            "is_new": is_new,
            "note": p.note,
            "created_by": p.created_by,
        })
    rows.sort(key=lambda r: (r["date"] or "", -r["amount"]), reverse=True)
    return {
        "period": f"{y:04d}-{m:02d}",
        "rows": rows,
        "count": len(rows),
        "students": len({r["student_id"] for r in rows}),
        "total": round(total, 2),
        "new_total": round(new_sum, 2),
        "old_total": round(old_sum, 2),
    }


# =====================================================================
#  LID KIRITISH: TO'LIQ TO'LDIRILSIN, FILIAL O'ZINIKI BO'LSIN
#  Bo'sh mahalla/maktab keyin hisobotni buzadi; filialni qo'lda tanlash
#  esa adashishga olib keladi — xodimning lidi o'z filialiga tushadi.
# =====================================================================
_LEAD_REQUIRED = [
    ("full_name", "Ism-familiya"),
    ("phone", "Telefon"),
    ("address", "Qayerdan (mahalla / tuman)"),
    ("school", "Maktab"),
    ("grade", "Sinf"),
    ("source", "Qayerdan keldi"),
]

_cur_create_lead = _find_endpoint("/api/leads", "POST")

if _cur_create_lead is not None:
    _drop_route("/api/leads", "POST")

    @app.post("/api/leads", response_model=schemas.LeadOut)
    def create_lead_v2(payload: schemas.LeadCreate,
                       db: Session = Depends(get_db),
                       user: models.User = Depends(
                           require_role(*roles.LEAD_ACCESS))):
        missing = []
        for field, label in _LEAD_REQUIRED:
            val = (getattr(payload, field, None) or "")
            if field == "phone":
                digits = "".join(c for c in str(val) if c.isdigit())
                if len(digits) < 9:
                    missing.append(label)
            elif not str(val).strip():
                missing.append(label)
        if missing:
            raise HTTPException(
                400, "Quyidagilar to'ldirilmadi: " + ", ".join(missing))

        # Filiali bor xodim boshqa filialga lid yoza olmaydi
        if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
            payload.branch_id = user.branch_id
        elif not payload.branch_id:
            payload.branch_id = user.branch_id
        if not payload.branch_id:
            raise HTTPException(400, "Filial tanlanmadi")

        return _cur_create_lead(payload=payload, db=db, user=user)


# =====================================================================
#  OYLIK HISOB-KITOB: JADVALNI O'ZI YARATIB, HAMMADAN BIRDAN YECHADI
#  Eski xatolik: dars kunlari faqat kimdir guruh yo'qlamasini ochganda
#  yaratilardi. Yangi guruhda hech kim ochmagan bo'lsa "0 dars" chiqib,
#  hech kimdan pul yechilmasdi. Endi hisoblashdan oldin jadval o'zi
#  to'ldiriladi.
#
#  whole_month=True — o'quvchi oy o'rtasida qo'shilgan bo'lsa ham
#  to'liq oy uchun hisoblanadi (eski o'quvchilarni ro'yxatga endi
#  kiritganda kerak bo'ladi).
# =====================================================================
_drop_route("/api/billing/month", "POST")


@app.post("/api/billing/month")
def billing_month_v2(year: int, month: int, commit: bool = False,
                     whole_month: bool = False,
                     db: Session = Depends(get_db),
                     user=Depends(require_role(*roles.FINANCE_ACCESS))):
    period = M._period_key(year, month)
    start, end = M.billing.month_bounds(year, month)

    students = [s for s in scope_to_branch(
        db.query(models.Student), models.Student, user).all()
        if s.status == "active" and s.group_id]

    # Avval jadvalni to'ldiramiz — har guruh uchun bir marta
    synced = set()
    for s in students:
        g = s.group
        if not g or g.id in synced:
            continue
        synced.add(g.id)
        try:
            M._sync_scheduled_lessons(db, g, start, end)
        except Exception:
            db.rollback()
    if synced:
        db.commit()

    rows, created, no_lesson = [], 0, 0
    for s in students:
        g = s.group
        if not g:
            continue
        already = (db.query(models.Payment)
                   .filter(models.Payment.student_id == s.id,
                           models.Payment.period == period,
                           models.Payment.kind == "charge").first())
        since = start
        if not whole_month and s.enrolled_date and s.enrolled_date > start:
            since = s.enrolled_date
        lessons = (len(M._lessons_left_in_month(db, g.id, since))
                   if since <= end else 0)
        disc = M._student_discount_percent(db, s)
        amount = lessons * (g.lesson_price or 0) * (100 - disc) / 100
        if lessons == 0:
            no_lesson += 1

        if commit and not already and amount > 0 \
                and not M._charge_skipped(db, s.id, period):
            db.add(models.Payment(
                student_id=s.id, amount=-abs(amount), kind="charge",
                note=f"{g.name} — {period} oyi uchun {lessons} dars"
                     + (f" (chegirma {disc}%)" if disc else ""),
                created_by=user.full_name, period=period))
            created += 1
        rows.append({
            "student_id": s.id, "public_id": s.public_id,
            "full_name": s.full_name, "group": g.name,
            "lessons": lessons, "discount": disc,
            "amount": round(amount, 2),
            "already_charged": already is not None,
        })

    if commit:
        audit.log(db, user, entity="payment", action="create",
                  entity_label=f"{period} oylik hisob-kitob",
                  new_value=created,
                  note=f"{created} ta o'quvchiga hisoblandi", commit=True)
        db.commit()

    return {
        "period": period,
        "committed": commit,
        "students": len(rows),
        "created": created,
        "no_lesson": no_lesson,
        "expected_total": round(sum(r["amount"] for r in rows), 2),
        "rows": sorted(rows, key=lambda r: r["full_name"]),
    }


# =====================================================================
#  NARX SIYOSATI: OYIGA 12 DARS = 480 000 SO'M
#  Bitta dars 40 000. Oyda 13-14 dars chiqsa, ortig'i BONUS — mijozdan
#  baribir 12 dars uchun olinadi. Oy o'rtasida qo'shilgan o'quvchi esa
#  faqat qolgan darslari uchun to'laydi (u ham 12 tadan oshmaydi).
#
#  Diqqat: bu faqat O'QUVCHI to'lovi. Ustoz oyligi yo'qlamadan
#  hisoblanadi va bu yerga aloqasi yo'q — tegilmadi.
# =====================================================================
def _lesson_cap(g) -> int:
    return int(getattr(g, "standard_lessons_per_month", None) or 12)


def _billable_lessons(db, g, since, start, end) -> int:
    """Mijozdan haqiqatda olinadigan darslar soni.

    To'liq oy o'qiydigan o'quvchi standart 12 darsni to'laydi — kalendarda
    13 chiqsa ham, 11 chiqsa ham. Oy o'rtasida qo'shilgan (yoki guruhi
    oy o'rtasida ochilgan) bo'lsa — o'sha kundan oy oxirigacha nechta
    dars bo'lsa, shuncha (lekin 12 tadan oshmaydi)."""
    cap = _lesson_cap(g)
    partial = since > start
    if getattr(g, "start_date", None) and g.start_date > start:
        partial = True
    if getattr(g, "end_date", None) and g.end_date < end:
        partial = True
    if not partial:
        return cap
    n = len(M._lessons_left_in_month(db, g.id, since)) if since <= end else 0
    return min(n, cap)


def _charge_note(g, period: str, billable: int, disc: float,
                 prefix: str = "") -> str:
    cap = _lesson_cap(g)
    txt = f"{g.name} — {period}: {prefix}{billable} dars"
    if billable >= cap:
        txt += " (standart oy)"
    if disc:
        txt += f" (chegirma {disc}%)"
    return txt


# --- Faollashtirilganda avtomat yechish ham shu qoidaga bo'ysunsin ---
def _charge_from_activation_v2(db, s, since, user=None):
    """Faollashgan kundan oy oxirigacha — 12 darsdan oshmaydi."""
    if not s.group_id or not s.group:
        return None
    period = M._period_key(since.year, since.month)
    exists = (db.query(models.Payment)
              .filter(models.Payment.student_id == s.id,
                      models.Payment.period == period,
                      models.Payment.kind == "charge").first())
    if exists:
        return None
    if M._charge_skipped(db, s.id, period):
        return None

    start, end = M.billing.month_bounds(since.year, since.month)
    g = s.group
    # Guruh jadvali hali yaratilmagan bo'lsa — o'zi to'ldiradi
    try:
        M._sync_scheduled_lessons(db, g, start, end)
    except Exception:
        pass
    n = _billable_lessons(db, g, since, start, end)
    if n <= 0:
        return None

    price = g.lesson_price or 0
    disc = M._student_discount_percent(db, s)
    amount = n * price * (100 - disc) / 100
    if amount <= 0:
        return None

    db.add(models.Payment(
        student_id=s.id, amount=-abs(amount), kind="charge",
        note=_charge_note(g, period, n, disc, "faollashgandan "),
        created_by=(user.full_name if user else "avtomat"),
        period=period))
    return {"lessons": n, "amount": amount, "discount": disc}


M._charge_from_activation = _charge_from_activation_v2


# --- Oylik hisob-kitob ---
_drop_route("/api/billing/month", "POST")


@app.post("/api/billing/month")
def billing_month_v3(year: int, month: int, commit: bool = False,
                     whole_month: bool = False,
                     db: Session = Depends(get_db),
                     user=Depends(require_role(*roles.FINANCE_ACCESS))):
    period = M._period_key(year, month)
    start, end = M.billing.month_bounds(year, month)

    students = [s for s in scope_to_branch(
        db.query(models.Student), models.Student, user).all()
        if s.status == "active" and s.group_id]

    # Jadvalni avval to'ldiramiz — har guruh uchun bir marta
    synced = set()
    for s in students:
        g = s.group
        if not g or g.id in synced:
            continue
        synced.add(g.id)
        try:
            M._sync_scheduled_lessons(db, g, start, end)
        except Exception:
            db.rollback()
    if synced:
        db.commit()

    rows, created, no_lesson = [], 0, 0
    for s in students:
        g = s.group
        if not g:
            continue
        already = (db.query(models.Payment)
                   .filter(models.Payment.student_id == s.id,
                           models.Payment.period == period,
                           models.Payment.kind == "charge").first())
        since = start
        if not whole_month and s.enrolled_date and s.enrolled_date > start:
            since = s.enrolled_date
        billable = _billable_lessons(db, g, since, start, end)
        disc = M._student_discount_percent(db, s)
        amount = billable * (g.lesson_price or 0) * (100 - disc) / 100
        if billable == 0:
            no_lesson += 1

        if commit and not already and amount > 0 \
                and not M._charge_skipped(db, s.id, period):
            db.add(models.Payment(
                student_id=s.id, amount=-abs(amount), kind="charge",
                note=_charge_note(g, period, billable, disc),
                created_by=user.full_name, period=period))
            created += 1
        rows.append({
            "student_id": s.id, "public_id": s.public_id,
            "full_name": s.full_name, "group": g.name,
            "lessons": billable, "discount": disc,
            "amount": round(amount, 2),
            "already_charged": already is not None,
        })

    if commit:
        audit.log(db, user, entity="payment", action="create",
                  entity_label=f"{period} oylik hisob-kitob",
                  new_value=created,
                  note=f"{created} ta o'quvchiga hisoblandi", commit=True)
        db.commit()

    return {
        "period": period,
        "committed": commit,
        "students": len(rows),
        "created": created,
        "no_lesson": no_lesson,
        "expected_total": round(sum(r["amount"] for r in rows), 2),
        "rows": sorted(rows, key=lambda r: r["full_name"]),
    }


# =====================================================================
#  FAOLLASHTIRISH: SANA SO'RALADI VA O'SHA KUNDAN PUL YECHILADI
#  Administrator "Faollashtirish" bosganda qaysi kundan o'qishni
#  boshlaganini kiritadi. Shu kundan oy oxirigacha nechta dars bo'lsa,
#  40 000 dan ko'paytirib avtomat yechiladi (12 darsdan oshmaydi).
# =====================================================================
_drop_route("/api/students/{student_id}/activate", "POST")


@app.post("/api/students/{student_id}/activate")
def activate_student_v2(student_id: int, payload: dict | None = None,
                        db: Session = Depends(get_db),
                        user=Depends(require_role(*roles.FREEZE_ROLES))):
    s = db.query(models.Student).get(student_id)
    if not s:
        raise HTTPException(404, "O'quvchi topilmadi")
    if s.status == "active":
        raise HTTPException(400, "Bu o'quvchi allaqachon faol")

    on = M.roles.local_today()
    raw = (payload or {}).get("on")
    if raw:
        try:
            on = date.fromisoformat(str(raw)[:10])
        except ValueError:
            raise HTTPException(400, "Sana noto'g'ri")
    if on > M.roles.local_today():
        raise HTTPException(400, "Kelajakdagi sanani tanlab bo'lmaydi")

    old = s.status
    s.status = "active"
    if not s.enrolled_date or s.enrolled_date > on:
        s.enrolled_date = on
    M._sync_student_left_date(s)

    charge = _charge_from_activation_v2(db, s, on, user)

    audit.log(db, user, entity="student", action="activate", entity_id=s.id,
              entity_label=s.full_name, field="status",
              old_value=old, new_value="active", branch_id=s.branch_id,
              note=(f"{on.isoformat()} dan — {charge['lessons']} dars, "
                    f"{charge['amount']:,.0f} so'm".replace(",", " ")
                    if charge else on.isoformat()))
    db.commit()
    return {"ok": True, "status": s.status,
            "activated_on": on.isoformat(), "charge": charge}


@app.get("/api/students/{student_id}/activate-preview")
def activate_preview(student_id: int, on: str | None = None,
                     db: Session = Depends(get_db),
                     user=Depends(require_role(*roles.FREEZE_ROLES))):
    """Faollashtirishdan oldin: shu sanadan qancha pul yechilishini
    ko'rsatadi — administrator tasdiqlashdan oldin ko'rib turadi."""
    s = db.query(models.Student).get(student_id)
    if not s:
        raise HTTPException(404, "O'quvchi topilmadi")
    day = M.roles.local_today()
    if on:
        try:
            day = date.fromisoformat(str(on)[:10])
        except ValueError:
            raise HTTPException(400, "Sana noto'g'ri")
    g = s.group
    if not g:
        return {"lessons": 0, "amount": 0, "discount": 0,
                "already": False, "group": None,
                "hint": "O'quvchi guruhga biriktirilmagan — pul "
                        "hisoblanmaydi."}
    start, end = M.billing.month_bounds(day.year, day.month)
    try:
        M._sync_scheduled_lessons(db, g, start, end)
        db.commit()
    except Exception:
        db.rollback()
    period = M._period_key(day.year, day.month)
    already = (db.query(models.Payment)
               .filter(models.Payment.student_id == s.id,
                       models.Payment.period == period,
                       models.Payment.kind == "charge").first()) is not None
    n = _billable_lessons(db, g, day, start, end)
    disc = M._student_discount_percent(db, s)
    amount = n * (g.lesson_price or 0) * (100 - disc) / 100
    cap = _lesson_cap(g)
    return {
        "lessons": n, "amount": round(amount, 2), "discount": disc,
        "already": already, "group": g.name,
        "lesson_price": g.lesson_price or 0, "cap": cap,
        "hint": ("Bu oy uchun allaqachon hisoblangan — qayta yechilmaydi."
                 if already else
                 f"{n} dars x {(g.lesson_price or 0):,.0f} so'm"
                 .replace(",", " ")
                 + (f" (chegirma {disc}%)" if disc else "")),
    }


# =====================================================================
#  LC UP'DAN ESKI TO'LOVLAR TARIXINI KO'CHIRISH
#  Har bir eski to'lov yoniga o'sha kunning "hisoblangan" yozuvi ham
#  qo'yiladi — natijada BALANS O'ZGARMAYDI. Ya'ni tarix ko'rinadi,
#  lekin bugungi qarz buzilmaydi.
#
#  Barcha yozuvlar izohida "[LC UP]" belgisi turadi — kerak bo'lsa
#  bitta tugma bilan hammasini qaytarib olib tashlash mumkin.
# =====================================================================
_LCUP_TAG = "[LC UP]"
_IMPORT_ROLES = list(dict.fromkeys(
    list(roles.FINANCE_ACCESS) + [roles.FOUNDER]))


def _norm_name(s) -> str:
    t = (s or "").lower().replace("'", "'").replace("`", "'")
    t = _re2.sub(r"[^a-z0-9а-яё ]+", " ", t)
    return " ".join(t.split())


def _phone_tail(s) -> str:
    d = "".join(ch for ch in str(s or "") if ch.isdigit())
    return d[-9:] if len(d) >= 9 else ""


def _parse_money(v) -> float:
    """"480 000", "480,000.00", "480000 so'm" — hammasi 480000 bo'ladi."""
    if v is None:
        return 0.0
    if isinstance(v, (int, float)):
        return float(v)
    t = str(v).strip().replace(" ", " ")
    t = _re2.sub(r"[^0-9,.\-]", "", t)
    if not t:
        return 0.0
    # 1,234.56 -> nuqta kasr; 1.234,56 -> vergul kasr
    if "," in t and "." in t:
        t = (t.replace(",", "") if t.rfind(".") > t.rfind(",")
             else t.replace(".", "").replace(",", "."))
    elif "," in t:
        t = t.replace(",", "" if len(t.split(",")[-1]) == 3 else ".")
    try:
        return float(t)
    except ValueError:
        return 0.0


def _parse_day(v):
    """2026-08-07, 07.08.2026, 07/08/2026 — hammasini tushunadi."""
    if not v:
        return None
    if isinstance(v, date):
        return v
    t = str(v).strip()[:19].replace("T", " ")
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y", "%Y/%m/%d",
                "%d-%m-%Y", "%Y-%m-%d %H:%M:%S", "%d.%m.%Y %H:%M"):
        try:
            return _dt.strptime(t[:len(_dt.now().strftime(fmt))], fmt).date()
        except ValueError:
            continue
    try:
        return date.fromisoformat(t[:10])
    except ValueError:
        return None


_METHOD_WORDS = {
    "cash": ("naqd", "cash", "нал"),
    "card": ("click", "karta", "card", "payme", "uzum", "plastik"),
    "terminal": ("terminal", "терминал", "pos"),
}


def _parse_method(v) -> str:
    t = str(v or "").lower()
    for key, words in _METHOD_WORDS.items():
        if any(w in t for w in words):
            return key
    return "cash"


def _student_index(db, user):
    """Ism va telefon bo'yicha o'quvchi qidirish uchun indeks."""
    q = scope_to_branch(db.query(models.Student), models.Student, user)
    by_name, by_phone = {}, {}
    for s in q.all():
        n = _norm_name(s.full_name)
        if n:
            by_name.setdefault(n, []).append(s)
        for ph in (s.phone, s.parent_phone):
            t = _phone_tail(ph)
            if t:
                by_phone.setdefault(t, []).append(s)
    return by_name, by_phone


# Diqqat: /api/payments/{id} yo'li bilan to'qnashmasin uchun
# alohida prefiks.
@app.post("/api/lcup/payments")
def import_payments(payload: dict, db: Session = Depends(get_db),
                    user=Depends(require_role(*_IMPORT_ROLES))):
    """LC UP eksportidan eski to'lovlarni ko'chiradi.

    commit=false — faqat tekshirib ko'rsatadi, hech narsa yozmaydi."""
    rows = payload.get("rows") or []
    commit = bool(payload.get("commit"))
    if not isinstance(rows, list) or not rows:
        raise HTTPException(400, "Fayldan bironta qator o'qilmadi")
    if len(rows) > 20000:
        raise HTTPException(400, "Bir martada 20 000 qatordan ko'p bo'lmasin")

    by_name, by_phone = _student_index(db, user)
    # Takror importni ushlash uchun: allaqachon bor [LC UP] to'lovlari
    seen = set()
    for p in (db.query(models.Payment)
              .filter(models.Payment.kind == "payment",
                      models.Payment.note.like(f"%{_LCUP_TAG}%")).all()):
        seen.add((p.student_id, p.created_at.date() if p.created_at else None,
                  round(p.amount, 2)))

    out, ok, dup, miss, total = [], 0, 0, 0, 0.0
    for i, r in enumerate(rows):
        name = str(r.get("name") or "").strip()
        amount = _parse_money(r.get("amount"))
        day = _parse_day(r.get("date"))
        phone = _phone_tail(r.get("phone"))

        if not name and not phone:
            continue
        if amount <= 0:
            out.append({"row": i + 1, "name": name, "status": "skip",
                        "reason": "summa yo'q yoki noto'g'ri"})
            continue
        if not day:
            out.append({"row": i + 1, "name": name, "status": "skip",
                        "reason": "sana o'qilmadi"})
            continue

        # Avval ism, keyin telefon; ikkalasi bo'lsa — ikkovi kesishgani
        cands = list(by_name.get(_norm_name(name), []))
        if phone:
            ph = by_phone.get(phone, [])
            both = [s for s in cands if s in ph]
            if both:
                cands = both
            elif not cands:
                cands = list(ph)
        if not cands:
            miss += 1
            out.append({"row": i + 1, "name": name, "date": day.isoformat(),
                        "amount": amount, "status": "not_found",
                        "reason": "bunday o'quvchi topilmadi"})
            continue
        if len(cands) > 1:
            miss += 1
            out.append({"row": i + 1, "name": name, "date": day.isoformat(),
                        "amount": amount, "status": "ambiguous",
                        "reason": f"{len(cands)} ta bir xil ismli o'quvchi "
                                  f"bor — telefon ustunini qo'shing"})
            continue

        s = cands[0]
        key = (s.id, day, round(amount, 2))
        if key in seen:
            dup += 1
            out.append({"row": i + 1, "name": s.full_name,
                        "date": day.isoformat(), "amount": amount,
                        "status": "duplicate",
                        "reason": "bu to'lov allaqachon ko'chirilgan"})
            continue
        seen.add(key)

        method = _parse_method(r.get("method"))
        note = str(r.get("note") or "").strip()
        total += amount
        ok += 1
        out.append({"row": i + 1, "name": s.full_name, "student_id": s.id,
                    "date": day.isoformat(), "amount": amount,
                    "method": method, "status": "ok"})

        if commit:
            when = _dt.combine(day, _dt.min.time())
            tail = f" · {note}" if note else ""
            # To'lov (plyus)
            db.add(models.Payment(
                student_id=s.id, amount=abs(amount), kind="payment",
                method=method, created_at=when, period=None,
                note=f"{_LCUP_TAG} eski to'lov{tail}",
                created_by=user.full_name))
            # O'sha kunning hisoblangani (minus) — balans o'zgarmasin
            db.add(models.Payment(
                student_id=s.id, amount=-abs(amount), kind="charge",
                created_at=when, period=None,
                note=f"{_LCUP_TAG} eski hisob ({day.strftime('%Y-%m')})",
                created_by=user.full_name))

    if commit and ok:
        db.commit()
        audit.log(db, user, entity="payment", action="import",
                  entity_label=f"LC UP: {ok} ta eski to'lov",
                  new_value=ok,
                  note=f"jami {total:,.0f} so'm".replace(",", " "),
                  commit=True)

    return {"committed": commit, "ok": ok, "duplicate": dup,
            "not_found": miss, "total": round(total, 2),
            "rows": out[:500], "shown": min(len(out), 500),
            "all_rows": len(out)}


@app.get("/api/lcup/payments")
def import_payments_stats(db: Session = Depends(get_db),
                          user=Depends(require_role(*_IMPORT_ROLES))):
    """Hozirgacha nechta eski to'lov ko'chirilgan."""
    q = (db.query(models.Payment)
         .filter(models.Payment.kind == "payment",
                 models.Payment.note.like(f"%{_LCUP_TAG}%")))
    rows = q.all()
    return {"count": len(rows),
            "total": round(sum(r.amount for r in rows), 2),
            "first": min((r.created_at.date().isoformat()
                          for r in rows if r.created_at), default=None),
            "last": max((r.created_at.date().isoformat()
                         for r in rows if r.created_at), default=None)}


@app.delete("/api/lcup/payments")
def import_payments_undo(db: Session = Depends(get_db),
                         user=Depends(require_role(roles.FOUNDER))):
    """Ko'chirilgan hammasini qaytarib olib tashlaydi — faqat asoschi."""
    n = (db.query(models.Payment)
         .filter(models.Payment.note.like(f"%{_LCUP_TAG}%"))
         .delete(synchronize_session=False))
    db.commit()
    audit.log(db, user, entity="payment", action="delete",
              entity_label="LC UP importi bekor qilindi",
              old_value=n, commit=True)
    return {"deleted": n}


# =====================================================================
#  HR MENEJERGA YANA UCHTA HUQUQ
#  Dars ko'chirish (kelmagan kunni surish ham shu), coin qo'shish va
#  tahrirlash. Eski yo'qlama allaqachon ochilgan.
#
#  RESCHEDULE_APPROVE'ga HR_MANAGER qo'shish endi faylning ENG
#  BOSHIDA ham bajariladi (qarang: yuqorida, _drop_route() ta'rifidan
#  keyin) - bu yerdagi qator shunchaki xavfsizlik uchun qoldirilgan
#  (if tekshiruvi tufayli ikki marta qo'shib yubormaydi).
# =====================================================================
if _HRM not in roles.RESCHEDULE_APPROVE:
    roles.RESCHEDULE_APPROVE.append(_HRM)
if _HRM not in roles.COIN_ADMIN:
    roles.COIN_ADMIN.append(_HRM)
try:
    roles.DEFAULT_MATRIX[_HRM]["gamification"] = {"view", "edit"}
except Exception:
    pass

_TEACH_HR = tuple(dict.fromkeys(tuple(roles.TEACHING_ACCESS) + (_HRM,)))

# --- Dars ko'chirish ---
_cur_reschedule = _find_endpoint("/api/groups/{gid}/reschedule", "POST")

if _cur_reschedule is not None:
    _drop_route("/api/groups/{gid}/reschedule", "POST")

    @app.post("/api/groups/{gid}/reschedule")
    def group_reschedule_v2(gid: int, payload: schemas.GroupRescheduleIn,
                            db: Session = Depends(get_db),
                            user=Depends(require_role(*_TEACH_HR))):
        return _cur_reschedule(gid=gid, payload=payload, db=db, user=user)


# --- Coin qo'shish / o'chirish ---
_cur_coin_add = _find_endpoint("/api/students/{student_id}/coins", "POST")
_cur_coin_del = _find_endpoint("/api/coins/{entry_id}", "DELETE")

if _cur_coin_add is not None:
    _drop_route("/api/students/{student_id}/coins", "POST")

    @app.post("/api/students/{student_id}/coins",
              response_model=schemas.CoinEntryOut)
    def add_manual_coins_v2(student_id: int, payload: schemas.CoinManual,
                            db: Session = Depends(get_db),
                            user=Depends(require_role(*roles.COIN_ADMIN))):
        return _cur_coin_add(student_id=student_id, payload=payload,
                             db=db, user=user)

if _cur_coin_del is not None:
    _drop_route("/api/coins/{entry_id}", "DELETE")

    @app.delete("/api/coins/{entry_id}")
    def delete_coin_entry_v2(entry_id: int, db: Session = Depends(get_db),
                             user=Depends(require_role(*roles.COIN_ADMIN))):
        return _cur_coin_del(entry_id=entry_id, db=db, user=user)


# =====================================================================
#  BAHO QO'YISH QOIDALARI QAT'IYLASHDI
#  1) Yo'qlama qo'yilmagan o'quvchiga baho qo'yib bo'lmaydi — aks holda
#     darsga kelmagan bolaga coin tushib ketardi.
#  2) O'tib ketgan kunga baho qo'yish yopiq (yo'qlama bilan bir xil
#     qoida): faqat asoschi, o'quv bo'limi rahbari va HR.
#  3) Hali kelmagan kunga ham baho yo'q.
# =====================================================================
_cur_save_grades = _find_endpoint("/api/lessons/{lesson_id}/grades", "PUT")

if _cur_save_grades is not None:
    _drop_route("/api/lessons/{lesson_id}/grades", "PUT")

    @app.put("/api/lessons/{lesson_id}/grades")
    def save_grades_v2(lesson_id: int, payload: schemas.GradeBulk,
                       db: Session = Depends(get_db),
                       user=Depends(require_role(*roles.GRADE_EDIT))):
        lesson = db.query(models.Lesson).get(lesson_id)
        if not lesson:
            raise HTTPException(404, "Dars topilmadi")
        _get_group_in_scope(db, lesson.group_id, user)

        today = M.roles.local_today()
        if lesson.date > today:
            raise HTTPException(
                400, "Hali kelmagan kunga baho qo'yilmaydi — dars "
                     "bo'lib o'tmagan")
        if lesson.date < today and user.role not in tuple(
                roles.PAST_ATTENDANCE):
            raise HTTPException(
                403, "O'tib ketgan kunga baho qo'yib bo'lmaydi. Kerak "
                     "bo'lsa o'quv bo'limi rahbari yoki HR menejerga "
                     "murojaat qiling")

        # Yo'qlamasi yo'q (yoki kelmagan) o'quvchiga baho yo'q
        att = {a.student_id: (a.present or 0) for a in
               db.query(models.Attendance)
               .filter(models.Attendance.lesson_id == lesson_id).all()}
        for m in payload.marks:
            if m.score is None:
                continue          # bahoni olib tashlash har doim mumkin
            state = att.get(m.student_id)
            if state is None:
                st = db.query(models.Student).get(m.student_id)
                raise HTTPException(
                    400, f"Avval yo'qlama qo'ying — "
                         f"{st.full_name if st else 'o?quvchi'} uchun bu "
                         f"darsda belgi yo'q")
            if state == 0:
                st = db.query(models.Student).get(m.student_id)
                raise HTTPException(
                    400, f"{st.full_name if st else 'O?quvchi'} bu darsga "
                         f"kelmagan — kelmagan o'quvchiga baho ham, coin "
                         f"ham qo'yilmaydi")

        return _cur_save_grades(lesson_id=lesson_id, payload=payload,
                                db=db, user=user)


# --- Baho jadvali: qaysi katakka tegish mumkinligi ham qaytsin ---
_cur_grade_grid = _find_endpoint("/api/groups/{group_id}/grades", "GET")

if _cur_grade_grid is not None:
    _drop_route("/api/groups/{group_id}/grades", "GET")

    @app.get("/api/groups/{group_id}/grades")
    def grade_grid_v2(group_id: int, year: int, month: int,
                      db: Session = Depends(get_db),
                      user=Depends(require_role(*roles.ATTENDANCE_VIEW))):
        res = _cur_grade_grid(group_id=group_id, year=year, month=month,
                              db=db, user=user)
        try:
            data = res.model_dump()
        except AttributeError:
            try:
                data = res.dict()
            except AttributeError:
                data = dict(res)
        ids = [ls["id"] for ls in data.get("lessons", [])]
        present = {}
        if ids:
            for a in (db.query(models.Attendance)
                      .filter(models.Attendance.lesson_id.in_(ids)).all()):
                present[f"{a.lesson_id}:{a.student_id}"] = int(a.present or 0)
        today = M.roles.local_today()
        data["present"] = present
        data["can_past"] = user.role in tuple(roles.PAST_ATTENDANCE)
        data["today"] = today.isoformat()
        return data


# =====================================================================
#  O'QUVCHINI USTOZ TAHRIRLAY OLMASIN
#  Ustoz dars beradi, o'quvchi kartasini esa administrator yuritadi.
#  Ko'rish qoladi, faqat saqlash yopiladi.
# =====================================================================
_NO_EDIT = (roles.TEACHER, roles.SUPPORT_TEACHER)
_STUDENT_EDIT = tuple(r for r in
                      (tuple(roles.TEACHING_STAFF) + (_HRM,))
                      if r not in _NO_EDIT)

_cur_upd_student = _find_endpoint("/api/students/{student_id}", "PUT")

if _cur_upd_student is not None:
    _drop_route("/api/students/{student_id}", "PUT")

    @app.put("/api/students/{student_id}", response_model=schemas.StudentOut)
    def update_student_v3(student_id: int, payload: schemas.StudentUpdate,
                          force: bool = False,
                          db: Session = Depends(get_db),
                          user=Depends(require_role(*_STUDENT_EDIT))):
        return _cur_upd_student(student_id=student_id, payload=payload,
                                force=force, db=db, user=user)


# =====================================================================
#  GURUH VA FILIAL ALMASHTIRISH
#  "Boshqa guruhga o'tkazish" — faqat O'SHA FILIAL ichida. Filialni
#  almashtirish alohida amal: u yerdagi administratorga vazifa tushadi,
#  chunki o'quvchini kutib olish, shartnoma va to'lov unga o'tadi.
# =====================================================================
def _branch_admin(db, branch_id):
    """Filialdagi administrator (bo'lmasa — filial rahbari)."""
    if not branch_id:
        return None
    q = db.query(models.User).filter(models.User.is_active == 1,
                                     models.User.branch_id == branch_id)
    for wanted in (_ADMIN_ROLES, (roles.BRANCH_MANAGER,)):
        u = q.filter(models.User.role.in_(wanted)).order_by(
            models.User.id).first()
        if u:
            return u
    return None


_cur_move_group = _find_endpoint("/api/students/{student_id}/move-group",
                                 "POST")

if _cur_move_group is not None:
    _drop_route("/api/students/{student_id}/move-group", "POST")

    @app.post("/api/students/{student_id}/move-group")
    def move_student_group_v2(student_id: int,
                              payload: schemas.StudentGroupMove,
                              force: bool = False,
                              db: Session = Depends(get_db),
                              user=Depends(require_role(*roles.FREEZE_ROLES))):
        s = db.query(models.Student).get(student_id)
        if not s:
            raise HTTPException(404, "O'quvchi topilmadi")
        if payload.group_id:
            g = db.query(models.Group).get(payload.group_id)
            if g and s.branch_id and g.branch_id and \
                    g.branch_id != s.branch_id:
                raise HTTPException(
                    400, "Bu guruh boshqa filialda. Filialni almashtirish "
                         "uchun \"Boshqa filialga o'tkazish\" amalidan "
                         "foydalaning")
        return _cur_move_group(student_id=student_id, payload=payload,
                               force=force, db=db, user=user)


@app.post("/api/students/{student_id}/move-branch")
def move_student_branch(student_id: int, payload: dict,
                        force: bool = False,
                        db: Session = Depends(get_db),
                        user=Depends(require_role(*roles.FREEZE_ROLES))):
    """O'quvchini boshqa filialga o'tkazadi.

    Guruh tanlansa — o'sha filialdagi guruhga qo'shiladi; tanlanmasa
    guruhsiz o'tadi va yangi filial administratori guruh tanlaydi.
    Ikkala holatda ham u yerdagi administratorga vazifa tushadi."""
    s = db.query(models.Student).get(student_id)
    if not s:
        raise HTTPException(404, "O'quvchi topilmadi")

    bid = payload.get("branch_id")
    if not bid:
        raise HTTPException(400, "Filial tanlanmadi")
    br = db.query(models.Branch).get(int(bid))
    if not br:
        raise HTTPException(404, "Filial topilmadi")
    if s.branch_id == br.id:
        raise HTTPException(400, "O'quvchi allaqachon shu filialda")

    g = None
    gid = payload.get("group_id")
    if gid:
        g = db.query(models.Group).get(int(gid))
        if not g:
            raise HTTPException(404, "Guruh topilmadi")
        if g.branch_id != br.id:
            raise HTTPException(400, "Bu guruh tanlangan filialda emas")
        M._raise_if_blocked(M._check_enrolment(db, s, g), force=force)

    old_branch = s.branch.name if s.branch else "—"
    old_group = s.group.name if s.group else None
    note = str(payload.get("note") or "").strip()

    s.branch_id = br.id
    s.group_id = g.id if g else None
    if g and not s.level:
        s.subject = s.subject or g.subject
        s.level = g.level

    admin = _branch_admin(db, br.id)
    bal = M.student_balance(db, s.id)
    lines = [f"O'quvchi: {s.full_name}",
             f"Qayerdan: {old_branch}"
             + (f" · {old_group}" if old_group else ""),
             f"Guruh: {g.name if g else 'hali tanlanmagan — guruh tanlang'}",
             f"Balans: {bal:,.0f} so'm".replace(",", " ")]
    if note:
        lines.append(f"Izoh: {note}")
    lines.append("")
    lines.append("Kerak: o'quvchini kutib oling, guruhini va dars "
                 "jadvalini tasdiqlang, ota-onasiga xabar bering.")

    task = models.Task(
        title=f"Yangi o'quvchi keldi: {s.full_name} ({old_branch}dan)",
        description="\n".join(lines),
        assignee_id=admin.id if admin else None,
        branch_id=br.id,
        deadline=M.roles.local_today() + M.timedelta(days=2),
        priority="high", source="manual",
        created_by=user.full_name)
    db.add(task)
    db.flush()
    try:
        M._ensure_public_id(db, "task", task)
    except Exception:
        pass

    audit.log(db, user, entity="student", action="group_move",
              entity_id=s.id, entity_label=s.full_name, field="branch",
              old_value=old_branch, new_value=br.name, branch_id=br.id,
              note=note or None)
    db.commit()
    return {"ok": True, "branch_id": br.id, "branch": br.name,
            "group_id": g.id if g else None,
            "group": g.name if g else None,
            "task_for": admin.full_name if admin else None}


# =====================================================================
#  GURUH BOSQICHI: "Step 2 · Unit 7"
#  Administrator guruhga kirganda guruh qayerga yetganini darrov ko'radi.
#  Manba — IMTIHONLAR: natijasi kiritilgan eng oxirgi unit imtihoni.
#  Hech kim qo'lda hech nima kiritmaydi, shuning uchun bu ma'lumot
#  hech qachon eskirmaydi.
# =====================================================================
_UNIT_TOTAL = 12


@app.get("/api/groups/{group_id}/progress")
def group_progress(group_id: int, db: Session = Depends(get_db),
                   user=Depends(require_role(*roles.ATTENDANCE_VIEW))):
    g = _get_group_in_scope(db, group_id, user)

    rows = (db.query(models.Exam)
            .join(models.ExamResult,
                  models.ExamResult.exam_id == models.Exam.id)
            .filter(models.Exam.group_id == group_id,
                    models.Exam.kind == "unit",
                    models.Exam.unit_no.isnot(None),
                    models.ExamResult.score.isnot(None))
            .distinct().all())

    done = sorted({int(e.unit_no) for e in rows if e.unit_no})
    last = None
    for e in rows:
        if last is None or (int(e.unit_no or 0), e.date) > \
                (int(last.unit_no or 0), last.date):
            last = e

    exam_out = None
    if last is not None:
        res = (db.query(models.ExamResult)
               .filter(models.ExamResult.exam_id == last.id,
                       models.ExamResult.score.isnot(None)).all())
        pcts = [r.percent for r in res if r.percent is not None]
        exam_out = {
            "id": last.id,
            "date": last.date.isoformat() if last.date else None,
            "unit_no": int(last.unit_no or 0),
            "title": last.title,
            "students": len(res),
            "avg_percent": (round(sum(pcts) / len(pcts), 1)
                            if pcts else None),
        }

    unit = int(last.unit_no or 0) if last is not None else 0
    lvl = g.level or ""
    return {
        "group_id": g.id,
        "subject": g.subject,
        "level": lvl or None,
        "level_label": roles.LEVEL_LABELS.get(lvl) or (lvl or None),
        "unit": unit,
        "unit_total": _UNIT_TOTAL,
        "next_unit": (unit + 1) if 0 < unit < _UNIT_TOTAL else
                     (1 if unit == 0 else None),
        "done_units": done,
        "percent": round(unit * 100 / _UNIT_TOTAL) if unit else 0,
        "last_exam": exam_out,
    }


# =====================================================================
#  SUPPORT YO'QLAMASI — USTOZNIKIDAN BUTUNLAY ALOHIDA
#
#  Muammo: support ham, ustoz ham BITTA "attendances" jadvaliga
#  yozardi. Support belgi qo'yganda ustozning belgisi ustiga yozilib
#  ketardi — ustoz oyligi ham shundan chiqadi, ya'ni bu pul xatosi edi.
#
#  Yechim: supportning o'z jadvali (support_attendance) va o'z kunlari.
#  Support darsi asosiy dars kuni emas — biriktirishda belgilangan
#  kun/vaqtda o'tadi, shuning uchun kunlar SupportAssignment'dan
#  quriladi. Bu jadvalga hech qanday pul hisob-kitobi bog'lanmagan:
#  ustoz oyligiga ham, o'quvchi hisobiga ham ta'sir qilmaydi.
# =====================================================================
from fastapi import Body  # noqa: E402
from pydantic import BaseModel as _BM  # noqa: E402

if getattr(models, "SupportAttendance", None) is None:
    class SupportAttendance(_Base):
        """Support teacherning o'z seansidagi yo'qlamasi."""

        __tablename__ = "support_attendance"
        __table_args__ = {"extend_existing": True}

        id = Column(Integer, primary_key=True, index=True)
        group_id = Column(Integer, index=True, nullable=False)
        student_id = Column(Integer, index=True, nullable=False)
        date = Column(_SaDate, nullable=False, index=True)
        # 1 = keldi, 2 = kech keldi, 0 = kelmadi
        present = Column(Integer, default=1)
        note = Column(String)
        created_by = Column(String)
        created_at = Column(DateTime, default=_dt.utcnow)
        updated_at = Column(DateTime, default=_dt.utcnow,
                            onupdate=_dt.utcnow)

    models.SupportAttendance = SupportAttendance
    try:
        _Base.metadata.create_all(
            bind=_engine, tables=[SupportAttendance.__table__])
    except Exception:
        pass

_SUPATT = models.SupportAttendance

_SUP_ROLES = (roles.SUPPORT_TEACHER, roles.HEAD_SUPPORT)
_SUP_ATT_EDIT = list(dict.fromkeys(
    list(roles.FULL_ACCESS) + [roles.SUPPORT_TEACHER, roles.HEAD_SUPPORT,
                               roles.ACADEMIC_HEAD, roles.HR_MANAGER]))

_WDX = {"mon": 0, "tue": 1, "wed": 2, "thu": 3,
        "fri": 4, "sat": 5, "sun": 6}


class _SupMark(_BM):
    student_id: int
    present: bool = True
    late: bool = False
    remove: bool = False


class _SupBulk(_BM):
    day: date
    marks: list[_SupMark]


def _month_bounds(year: int, month: int):
    if not (1 <= month <= 12):
        raise HTTPException(400, "Oy 1 dan 12 gacha bo'lsin")
    start = date(year, month, 1)
    end = (date(year + 1, 1, 1) if month == 12
           else date(year, month + 1, 1)) - _td(days=1)
    return start, end


def _support_plan(db: Session, group_id: int):
    """Guruhga biriktirilgan supportlar va ularning kun/vaqti."""
    rows = (db.query(models.SupportAssignment)
            .filter(models.SupportAssignment.group_id == group_id).all())
    out = []
    for a in rows:
        u = db.query(models.User).get(a.user_id) if a.user_id else None
        out.append({
            "user_id": a.user_id,
            "name": u.full_name if u else None,
            "days": [d.strip() for d in (a.days or "").split(",")
                     if d.strip()],
            "start": a.start,
            "end": a.end,
        })
    return out


def _support_dates(db: Session, g, year: int, month: int,
                   only_user: int | None = None):
    start, end = _month_bounds(year, month)
    if getattr(g, "start_date", None) and g.start_date > start:
        start = g.start_date
    if getattr(g, "end_date", None) and g.end_date < end:
        end = g.end_date
    want = set()
    for p in _support_plan(db, g.id):
        if only_user and p["user_id"] != only_user:
            continue
        for d in p["days"]:
            if d in _WDX:
                want.add(_WDX[d])
    if not want or start > end:
        return []
    out, cur = [], start
    while cur <= end:
        if cur.weekday() in want:
            out.append(cur)
        cur += _td(days=1)
    return out


@app.get("/api/groups/{group_id}/support-attendance")
def support_attendance_grid(group_id: int, year: int, month: int,
                            db: Session = Depends(get_db),
                            user=Depends(require_role(
                                *roles.ATTENDANCE_VIEW))):
    g = _get_group_in_scope(db, group_id, user)
    mine = user.id if user.role == roles.SUPPORT_TEACHER else None
    days = _support_dates(db, g, year, month, only_user=mine)

    students = M._group_students(db, group_id)
    if user.role in (roles.TEACHER,) + _SUP_ROLES:
        students = [s for s in students if s.status != "frozen"]

    marks = {}
    if days:
        rows = (db.query(_SUPATT)
                .filter(_SUPATT.group_id == group_id,
                        _SUPATT.date >= days[0],
                        _SUPATT.date <= days[-1]).all())
        for r in rows:
            v = 2 if (r.present or 0) == 2 else bool(r.present)
            marks[f"{r.date.isoformat()}:{r.student_id}"] = v

    plan = _support_plan(db, group_id)
    label = " · ".join(
        f"{p['name'] or 'Support'} ({p['start']}-{p['end']})"
        for p in plan if p["start"] and p["end"]) or None

    return {
        "days": [d.isoformat() for d in days],
        "students": [{"id": s.id, "full_name": s.full_name,
                      "status": s.status} for s in students],
        "marks": marks,
        "plan": plan,
        "label": label,
        "today": roles.local_today().isoformat(),
        "can_edit": user.role in tuple(_SUP_ATT_EDIT),
        "can_past": user.role in tuple(roles.PAST_ATTENDANCE),
        "hint": (None if days else
                 "Support darsining kuni va vaqti belgilanmagan — "
                 "guruh kartasidan supportni biriktirib, kun va "
                 "vaqtini tanlang"),
    }


@app.put("/api/groups/{group_id}/support-attendance")
def save_support_attendance(group_id: int, payload: _SupBulk = Body(...),
                            db: Session = Depends(get_db),
                            user=Depends(require_role(*_SUP_ATT_EDIT))):
    g = _get_group_in_scope(db, group_id, user)
    d = payload.day
    today = roles.local_today()
    if d > today:
        raise HTTPException(
            400, "Hali kelmagan kunga yo'qlama qo'yilmaydi")
    if d < today and user.role not in tuple(roles.PAST_ATTENDANCE):
        raise HTTPException(
            403, "O'tib ketgan kunni faqat asoschi, o'quv bo'limi "
                 "rahbari va HR menejer o'zgartira oladi")

    mine = user.id if user.role == roles.SUPPORT_TEACHER else None
    allowed = set(_support_dates(db, g, d.year, d.month, only_user=mine))
    if d not in allowed:
        raise HTTPException(
            400, "Bu kun support darsi kuni emas — biriktirishda "
                 "belgilangan kunlarga yo'qlama qo'yiladi")

    existing = {r.student_id: r for r in db.query(_SUPATT).filter(
        _SUPATT.group_id == group_id, _SUPATT.date == d).all()}
    for m in payload.marks:
        if m.remove:
            row = existing.pop(m.student_id, None)
            if row is not None:
                db.delete(row)
            continue
        val = (2 if m.late else 1) if m.present else 0
        row = existing.get(m.student_id)
        if row is not None:
            row.present = val
        else:
            row = _SUPATT(group_id=group_id, student_id=m.student_id,
                          date=d, present=val,
                          created_by=user.full_name)
            db.add(row)
            existing[m.student_id] = row
    db.commit()
    return {"ok": True, "date": d.isoformat(),
            "marked": len(existing)}


# --- Ustozning yo'qlamasi supportdan himoyalandi ---
_cur_save_att = _find_endpoint("/api/lessons/{lesson_id}/attendance", "PUT")

if _cur_save_att is not None:
    _drop_route("/api/lessons/{lesson_id}/attendance", "PUT")

    @app.put("/api/lessons/{lesson_id}/attendance")
    def save_attendance_v2(lesson_id: int, payload: schemas.AttendanceBulk,
                           db: Session = Depends(get_db),
                           user=Depends(require_role(*_TEACH_HR))):
        if user.role in _SUP_ROLES:
            raise HTTPException(
                403, "Ustozning yo'qlamasi alohida — unga tegilmaydi. "
                     "O'z yo'qlamangizni \"Support davomati\" "
                     "bo'limidan qo'ying")
        return _cur_save_att(lesson_id=lesson_id, payload=payload,
                             db=db, user=user)


# =====================================================================
#  LC UP IMPORTI: KETGAN (ARXIV) O'QUVCHILARNI HAM QO'SHIB KETSIN
#
#  Muammo: eski to'lovlar tarixida allaqachon ketib bo'lgan o'quvchilar
#  ko'p. Ular yangi tizimga umuman kiritilmagan, shuning uchun import
#  "bunday o'quvchi topilmadi" deb yuz-yuzlab qatorni tashlab ketardi.
#
#  Yechim: "create_missing" belgilansa, topilmagan odam ARXIV
#  o'quvchi sifatida ochiladi (status="archived") va to'lovi o'shanga
#  yoziladi. Ular Arxiv bo'limida ko'rinadi, faol ro'yxatga
#  aralashmaydi va hech qanday oylik/hisob-kitobga kirmaydi.
# =====================================================================
_LCUP_STU_NOTE = f"{_LCUP_TAG} arxivdan ko'chirilgan o'quvchi"

_orig_import_payments = _find_endpoint("/api/lcup/payments", "POST")
_drop_route("/api/lcup/payments", "POST")


def _lcup_new_student(db: Session, user, name: str, phone: str | None,
                      day):
    """Topilmagan odamni arxiv o'quvchi qilib ochadi."""
    s = models.Student(
        full_name=name.strip(),
        phone=(f"998{phone}" if phone and len(phone) == 9 else phone) or None,
        status="archived",
        branch_id=(None if user.role in tuple(roles.ORG_WIDE_ROLES)
                   else user.branch_id),
        enrolled_date=day,
        left_date=day,
        note=_LCUP_STU_NOTE,
    )
    db.add(s)
    db.flush()
    try:
        M._ensure_public_id(db, "student", s)
    except Exception:
        pass
    return s


@app.post("/api/lcup/payments")
def import_payments_v2(payload: dict, db: Session = Depends(get_db),
                       user=Depends(require_role(*_IMPORT_ROLES))):
    rows = payload.get("rows") or []
    commit = bool(payload.get("commit"))
    create_missing = bool(payload.get("create_missing"))
    if not isinstance(rows, list) or not rows:
        raise HTTPException(400, "Fayldan bironta qator o'qilmadi")
    if len(rows) > 20000:
        raise HTTPException(400, "Bir martada 20 000 qatordan ko'p bo'lmasin")

    by_name, by_phone = _student_index(db, user)
    seen = set()
    for p in (db.query(models.Payment)
              .filter(models.Payment.kind == "payment",
                      models.Payment.note.like(f"%{_LCUP_TAG}%")).all()):
        seen.add((p.student_id, p.created_at.date() if p.created_at else None,
                  round(p.amount, 2)))

    # Ko'rib chiqishda (commit=false) hech kim yaratilmaydi — shuning
    # uchun bitta odam necha marta to'lagan bo'lsa ham bir marta
    # sanaladi.
    planned = {}
    out, ok, dup, miss, made, total = [], 0, 0, 0, 0, 0.0

    for i, r in enumerate(rows):
        name = str(r.get("name") or "").strip()
        amount = _parse_money(r.get("amount"))
        day = _parse_day(r.get("date"))
        phone = _phone_tail(r.get("phone"))

        if not name and not phone:
            continue
        if amount <= 0:
            out.append({"row": i + 1, "name": name, "status": "skip",
                        "reason": "summa yo'q yoki noto'g'ri"})
            continue
        if not day:
            out.append({"row": i + 1, "name": name, "status": "skip",
                        "reason": "sana o'qilmadi"})
            continue

        cands = list(by_name.get(_norm_name(name), []))
        if phone:
            ph = by_phone.get(phone, [])
            both = [s for s in cands if s in ph]
            if both:
                cands = both
            elif not cands:
                cands = list(ph)

        new_one = False
        if not cands:
            if not create_missing or not name:
                miss += 1
                out.append({"row": i + 1, "name": name,
                            "date": day.isoformat(), "amount": amount,
                            "status": "not_found",
                            "reason": "bunday o'quvchi topilmadi"})
                continue
            key = _norm_name(name)
            if commit:
                s = _lcup_new_student(db, user, name, phone, day)
                by_name.setdefault(key, []).append(s)
                if phone:
                    by_phone.setdefault(phone, []).append(s)
                cands = [s]
                made += 1
                new_one = True
            else:
                if key not in planned:
                    planned[key] = True
                    made += 1
                total += amount
                ok += 1
                out.append({"row": i + 1, "name": name,
                            "date": day.isoformat(), "amount": amount,
                            "status": "will_create",
                            "reason": "arxiv o'quvchi sifatida ochiladi"})
                continue
        elif len(cands) > 1:
            miss += 1
            out.append({"row": i + 1, "name": name, "date": day.isoformat(),
                        "amount": amount, "status": "ambiguous",
                        "reason": f"{len(cands)} ta bir xil ismli o'quvchi "
                                  f"bor — telefon ustunini qo'shing"})
            continue

        s = cands[0]
        key = (s.id, day, round(amount, 2))
        if key in seen:
            dup += 1
            out.append({"row": i + 1, "name": s.full_name,
                        "date": day.isoformat(), "amount": amount,
                        "status": "duplicate",
                        "reason": "bu to'lov allaqachon ko'chirilgan"})
            continue
        seen.add(key)

        method = _parse_method(r.get("method"))
        note = str(r.get("note") or "").strip()
        total += amount
        ok += 1
        out.append({"row": i + 1, "name": s.full_name, "student_id": s.id,
                    "date": day.isoformat(), "amount": amount,
                    "method": method,
                    "status": "created" if new_one else "ok"})

        if commit:
            when = _dt.combine(day, _dt.min.time())
            tail = f" · {note}" if note else ""
            db.add(models.Payment(
                student_id=s.id, amount=abs(amount), kind="payment",
                method=method, created_at=when, period=None,
                note=f"{_LCUP_TAG} eski to'lov{tail}",
                created_by=user.full_name))
            db.add(models.Payment(
                student_id=s.id, amount=-abs(amount), kind="charge",
                created_at=when, period=None,
                note=f"{_LCUP_TAG} eski hisob ({day.strftime('%Y-%m')})",
                created_by=user.full_name))

    if commit and (ok or made):
        db.commit()
        audit.log(db, user, entity="payment", action="import",
                  entity_label=f"LC UP: {ok} ta eski to'lov"
                               + (f", {made} ta arxiv o'quvchi" if made
                                  else ""),
                  new_value=ok,
                  note=f"jami {total:,.0f} so'm".replace(",", " "),
                  commit=True)

    return {"committed": commit, "ok": ok, "duplicate": dup,
            "not_found": miss, "created": made, "total": round(total, 2),
            "rows": out[:500], "shown": min(len(out), 500),
            "all_rows": len(out)}


# Bekor qilishda import ochgan arxiv o'quvchilar ham ketadi — lekin
# faqat o'zidan boshqa hech qanday izi qolmaganlari.
_drop_route("/api/lcup/payments", "DELETE")


@app.delete("/api/lcup/payments")
def import_payments_undo_v2(db: Session = Depends(get_db),
                            user=Depends(require_role(roles.FOUNDER))):
    n = (db.query(models.Payment)
         .filter(models.Payment.note.like(f"%{_LCUP_TAG}%"))
         .delete(synchronize_session=False))
    db.flush()

    gone = 0
    for s in (db.query(models.Student)
              .filter(models.Student.note == _LCUP_STU_NOTE).all()):
        busy = (db.query(models.Payment)
                .filter(models.Payment.student_id == s.id).count()
                or db.query(models.Attendance)
                .filter(models.Attendance.student_id == s.id).count()
                or db.query(models.ExamResult)
                .filter(models.ExamResult.student_id == s.id).count())
        if busy:
            continue
        db.delete(s)
        gone += 1

    db.commit()
    audit.log(db, user, entity="payment", action="delete",
              entity_label="LC UP importi bekor qilindi",
              old_value=n,
              note=(f"{gone} ta arxiv o'quvchi ham o'chirildi"
                    if gone else None),
              commit=True)
    return {"deleted": n, "students_deleted": gone}


# =====================================================================
#  GURUHGA AVTOMAT NOM: "J/Z - Group 01/25"
#
#  Guruh ochayotgan odam nom o'ylab o'tirmasin. Qoida oddiy:
#    J/Z      — ustozning ism-familiya bosh harflari
#    Group 01 — guruh ochilgan OY (01 = yanvar)
#    /25      — yil (2025)
#  Bir ustozda shu oyda ikkinchi guruh bo'lsa oxiriga "-2" qo'shiladi.
#  Nom oddiy matn bo'lib qoladi — ustoz xohlasa o'zgartiradi, tegmasa
#  avtomat nom ketaveradi.
# =====================================================================
def _initials(full_name: str) -> str:
    parts = [p for p in (full_name or "").replace(".", " ").split() if p]
    letters = [p[0].upper() for p in parts[:2]]
    return "/".join(letters) if letters else "XX"


def _auto_group_name(db: Session, teacher_id=None, when=None) -> str:
    d = when or roles.local_today()
    who = "XX"
    if teacher_id:
        t = db.query(models.Teacher).get(int(teacher_id))
        if t:
            who = _initials(t.full_name)
    base = f"{who} - Group {d.month:02d}/{d.year % 100:02d}"
    taken = {g.name for g in db.query(models.Group)
             .filter(models.Group.name.like(f"{base}%")).all()}
    if base not in taken:
        return base
    n = 2
    while f"{base}-{n}" in taken:
        n += 1
    return f"{base}-{n}"


# Diqqat: /api/groups/{group_id} yo'li allaqachon ro'yxatdan o'tgan va
# "suggest-name" ni raqam deb o'qib yuborardi — shuning uchun alohida
# prefiks.
@app.get("/api/group-name/suggest")
def group_suggest_name(teacher_id: int | None = None,
                       on: date | None = None,
                       db: Session = Depends(get_db),
                       user=Depends(require_role(*roles.GROUP_MANAGE))):
    return {"name": _auto_group_name(db, teacher_id, on)}


_cur_create_group2 = _find_endpoint("/api/groups", "POST")

if _cur_create_group2 is not None:
    _drop_route("/api/groups", "POST")

    @app.post("/api/groups")
    def create_group_v4(payload: schemas.GroupCreate,
                        force: bool = False,
                        db: Session = Depends(get_db),
                        user=Depends(require_role(*roles.GROUP_MANAGE))):
        # Nom bo'sh yuborilsa — o'zi qo'yiladi (frontendda ham
        # oldindan ko'rsatiladi, bu esa ikkinchi himoya).
        if not (payload.name or "").strip():
            payload.name = _auto_group_name(
                db, payload.teacher_id, payload.start_date)
        return _cur_create_group2(payload=payload, force=force,
                                  db=db, user=user)


# =====================================================================
#  SUPPORT SEANSI YO'QLAMA BILAN BIRGA — HAQIQIY SOAT BILAN
#
#  Ilgari support oyligi qo'lda kiritilgan seansdan chiqardi va amalda
#  hamma joyda 1 soat bo'lib qolardi. Aslida asosiy ustoz ko'proq
#  vazifa berganda support 1.5, 2, hatto 3 soat ishlaydi.
#
#  Endi support yo'qlamani qo'yayotganda O'SHA OYNADA "qaysi vaqtdan
#  qaysi vaqtgacha" ni ham kiritadi. Shu ma'lumotdan seans yozuvi
#  avtomat yaratiladi/yangilanadi va oylik aynan shundan hisoblanadi.
#
#  Muhim: KELMAGAN o'quvchi sanalmaydi — seansdagi "o'quvchilar soni"
#  faqat kelganlardan iborat.
# =====================================================================
class _SupBulk2(_BM):
    day: date
    marks: list[_SupMark] = []
    start_time: str | None = None
    end_time: str | None = None


def _sup_teacher_for(db: Session, user, group_id: int):
    """Seans kimning nomiga yoziladi: supportning o'zi, aks holda shu
    guruhga biriktirilgan support."""
    if user.role == roles.SUPPORT_TEACHER:
        return M._teacher_of_user(db, user)
    a = (db.query(models.SupportAssignment)
         .filter(models.SupportAssignment.group_id == group_id).first())
    if a and a.user_id:
        u = db.query(models.User).get(a.user_id)
        if u:
            return M._teacher_of_user(db, u)
    return None


def _sup_plan_time(db: Session, group_id: int, uid=None):
    q = (db.query(models.SupportAssignment)
         .filter(models.SupportAssignment.group_id == group_id))
    if uid:
        q = q.filter(models.SupportAssignment.user_id == uid)
    a = q.first()
    return (a.start, a.end) if a else (None, None)


def _sync_support_session(db: Session, user, g, d, start, end):
    """Kunlik seansni yo'qlamaga qarab yangilaydi."""
    t = _sup_teacher_for(db, user, g.id)
    if t is None:
        return None
    present = (db.query(_SUPATT)
               .filter(_SUPATT.group_id == g.id, _SUPATT.date == d,
                       _SUPATT.present != 0).count())
    row = (db.query(models.SupportSession)
           .filter(models.SupportSession.teacher_id == t.id,
                   models.SupportSession.group_id == g.id,
                   models.SupportSession.date == d).first())

    # Hech kim kelmagan (yoki belgilar olib tashlangan) — seans yo'q
    if present <= 0:
        if row is not None:
            db.delete(row)
        return None

    if not (start and end):
        if row is not None:
            start = start or row.start_time
            end = end or row.end_time
        else:
            ps, pe = _sup_plan_time(db, g.id,
                                    user.id if user.role ==
                                    roles.SUPPORT_TEACHER else None)
            start, end = start or ps, end or pe
    if not (start and end):
        raise HTTPException(
            400, "Dars qaysi vaqtdan qaysi vaqtgacha bo'lganini "
                 "kiriting — oylik shu soatdan hisoblanadi")

    s_min, e_min = roles.hhmm_minutes(start), roles.hhmm_minutes(end)
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
                 f"soatdan oshmaydi — vaqtni tekshiring")

    present = min(present, roles.SUPPORT_SESSION_MAX_STUDENTS)
    if row is None:
        row = models.SupportSession(
            teacher_id=t.id, group_id=g.id, branch_id=g.branch_id,
            date=d, start_time=start, end_time=end, minutes=minutes,
            students_count=present, note="Yo'qlamadan avtomat",
            created_by=user.id)
        db.add(row)
    else:
        row.start_time, row.end_time = start, end
        row.minutes, row.students_count = minutes, present
    return row


_drop_route("/api/groups/{group_id}/support-attendance", "PUT")


@app.put("/api/groups/{group_id}/support-attendance")
def save_support_attendance_v2(group_id: int,
                               payload: _SupBulk2 = Body(...),
                               db: Session = Depends(get_db),
                               user=Depends(require_role(*_SUP_ATT_EDIT))):
    g = _get_group_in_scope(db, group_id, user)
    d = payload.day
    today = roles.local_today()
    if d > today:
        raise HTTPException(
            400, "Hali kelmagan kunga yo'qlama qo'yilmaydi")
    if d < today and user.role not in tuple(roles.PAST_ATTENDANCE):
        raise HTTPException(
            403, "O'tib ketgan kunni faqat asoschi, o'quv bo'limi "
                 "rahbari va HR menejer o'zgartira oladi")

    mine = user.id if user.role == roles.SUPPORT_TEACHER else None
    allowed = set(_support_dates(db, g, d.year, d.month, only_user=mine))
    if d not in allowed:
        raise HTTPException(
            400, "Bu kun support darsi kuni emas — biriktirishda "
                 "belgilangan kunlarga yo'qlama qo'yiladi")

    existing = {r.student_id: r for r in db.query(_SUPATT).filter(
        _SUPATT.group_id == group_id, _SUPATT.date == d).all()}
    for m in payload.marks:
        if m.remove:
            row = existing.pop(m.student_id, None)
            if row is not None:
                db.delete(row)
            continue
        val = (2 if m.late else 1) if m.present else 0
        row = existing.get(m.student_id)
        if row is not None:
            row.present = val
        else:
            row = _SUPATT(group_id=group_id, student_id=m.student_id,
                          date=d, present=val,
                          created_by=user.full_name)
            db.add(row)
            existing[m.student_id] = row
    db.flush()

    ses = _sync_support_session(db, user, g, d,
                                (payload.start_time or "").strip() or None,
                                (payload.end_time or "").strip() or None)
    db.commit()
    return {
        "ok": True, "date": d.isoformat(), "marked": len(existing),
        "session": ({"start": ses.start_time, "end": ses.end_time,
                     "minutes": ses.minutes,
                     "hours": round(ses.minutes / 60, 2),
                     "students": ses.students_count}
                    if ses is not None else None),
    }


# --- Jadval: kunlik seans vaqtlari ham qaytsin ---
_orig_sup_grid = _find_endpoint("/api/groups/{group_id}/support-attendance",
                                "GET")

if _orig_sup_grid is not None:
    _drop_route("/api/groups/{group_id}/support-attendance", "GET")

    @app.get("/api/groups/{group_id}/support-attendance")
    def support_attendance_grid_v2(group_id: int, year: int, month: int,
                                   db: Session = Depends(get_db),
                                   user=Depends(require_role(
                                       *roles.ATTENDANCE_VIEW))):
        data = _orig_sup_grid(group_id=group_id, year=year, month=month,
                              db=db, user=user)
        days = data.get("days") or []
        ses = {}
        if days:
            q = (db.query(models.SupportSession)
                 .filter(models.SupportSession.group_id == group_id,
                         models.SupportSession.date >= date.fromisoformat(
                             days[0]),
                         models.SupportSession.date <= date.fromisoformat(
                             days[-1])))
            if user.role == roles.SUPPORT_TEACHER:
                t = M._teacher_of_user(db, user)
                if t:
                    q = q.filter(models.SupportSession.teacher_id == t.id)
            for r in q.all():
                ses[r.date.isoformat()] = {
                    "start": r.start_time, "end": r.end_time,
                    "minutes": r.minutes,
                    "hours": round((r.minutes or 0) / 60, 2),
                    "students": r.students_count,
                }
        ps, pe = _sup_plan_time(
            db, group_id,
            user.id if user.role == roles.SUPPORT_TEACHER else None)
        data["sessions"] = ses
        data["default_start"] = ps
        data["default_end"] = pe
        data["hours_total"] = round(
            sum(v["minutes"] or 0 for v in ses.values()) / 60, 2)
        data["students_total"] = sum(v["students"] or 0
                                     for v in ses.values())
        return data


# =====================================================================
#  ARXIV O'QUVCHILARNI EXCEL'DAN QO'SHISH
#
#  LC UP'dagi ketgan o'quvchilar ro'yxati bir marta ko'chiriladi.
#  Ular ARXIV holatida ochiladi: faol ro'yxatga, oylikka, hisob-kitobga
#  va yo'qlamaga umuman aralashmaydi — faqat tarix va eski to'lovlar
#  bog'lanadigan karta bo'lib turadi.
#
#  Bir tugma bilan bekor qilinadi (asoschi) — import ochgan, boshqa
#  hech qanday izi yo'q kartalar o'chadi.
# =====================================================================
_ARCH_TAG = "[ARXIV IMPORT]"
_ARCH_IMPORT_ROLES = list(dict.fromkeys(
    list(roles.FULL_ACCESS) + [roles.HR_MANAGER, roles.ACADEMIC_HEAD,
                               roles.ACCOUNTANT, roles.FINANCE_DIRECTOR]))


def _parse_date_any(v):
    """01.02.2024 / 2024-02-01 / 1.2.24 — hammasini o'qiydi."""
    s = str(v or "").strip()
    if not s:
        return None
    s = s.split(" ")[0].replace("/", ".").replace("-", ".")
    parts = [p for p in s.split(".") if p]
    if len(parts) != 3:
        return None
    try:
        a, b, c = (int(p) for p in parts)
    except ValueError:
        return None
    if a > 31:                      # yil oldinda
        y, m, d = a, b, c
    else:
        d, m, y = a, b, c
    if y < 100:
        y += 2000
    try:
        return date(y, m, d)
    except ValueError:
        return None


@app.post("/api/archive/students/import")
def archive_students_import(payload: dict, db: Session = Depends(get_db),
                            user=Depends(require_role(
                                *_ARCH_IMPORT_ROLES))):
    """Excel'dan arxiv o'quvchilar. commit=false — faqat ko'rib chiqish."""
    rows = payload.get("rows") or []
    commit = bool(payload.get("commit"))
    if not isinstance(rows, list) or not rows:
        raise HTTPException(400, "Fayldan bironta qator o'qilmadi")
    if len(rows) > 20000:
        raise HTTPException(400, "Bir martada 20 000 qatordan ko'p bo'lmasin")

    branches = {}
    for b in db.query(models.Branch).all():
        branches[_norm_name(b.name)] = b
    groups = {}
    for g in db.query(models.Group).all():
        groups.setdefault(_norm_name(g.name), g)

    by_name, by_phone = _student_index(db, user)
    my_branch = (None if user.role in tuple(roles.ORG_WIDE_ROLES)
                 else user.branch_id)

    out, ok, dup, bad = [], 0, 0, 0
    planned = set()
    for i, r in enumerate(rows):
        name = str(r.get("name") or "").strip()
        if not name:
            continue
        phone = _phone_tail(r.get("phone"))
        pphone = _phone_tail(r.get("parent_phone"))
        key = _norm_name(name)

        if len(name) < 3:
            bad += 1
            out.append({"row": i + 1, "name": name, "status": "skip",
                        "reason": "ism juda qisqa"})
            continue

        # Allaqachon bormi — ism + telefon bo'yicha
        found = list(by_name.get(key, []))
        if phone:
            ph = by_phone.get(phone, [])
            both = [s for s in found if s in ph]
            found = both or (found if not ph else found)
        if found or (key, phone) in planned:
            dup += 1
            st = found[0] if found else None
            out.append({
                "row": i + 1, "name": name, "status": "duplicate",
                "reason": (f"allaqachon bor ({st.status})" if st
                           else "faylda ikki marta"),
            })
            continue
        planned.add((key, phone))

        b = branches.get(_norm_name(r.get("branch")))
        g = groups.get(_norm_name(r.get("group")))
        bid = (b.id if b else None) or (g.branch_id if g else None) \
            or my_branch
        enrolled = _parse_date_any(r.get("enrolled"))
        left = _parse_date_any(r.get("left"))

        ok += 1
        out.append({
            "row": i + 1, "name": name, "status": "ok",
            "phone": phone or None,
            "branch": (b.name if b else None),
            "group": (g.name if g else None),
            "enrolled": enrolled.isoformat() if enrolled else None,
            "left": left.isoformat() if left else None,
        })

        if commit:
            note = str(r.get("note") or "").strip()
            s = models.Student(
                full_name=name,
                phone=(f"998{phone}" if phone else None),
                parent_phone=(f"998{pphone}" if pphone else None),
                status="archived",
                branch_id=bid,
                group_id=None,          # arxivda guruh bo'lmaydi
                enrolled_date=enrolled,
                left_date=left or roles.local_today(),
                note=(f"{_ARCH_TAG} {note}".strip()
                      + (f" · guruh: {g.name}" if g else "")),
            )
            db.add(s)
            db.flush()
            try:
                M._ensure_public_id(db, "student", s)
            except Exception:
                pass
            by_name.setdefault(key, []).append(s)
            if phone:
                by_phone.setdefault(phone, []).append(s)

    if commit and ok:
        db.commit()
        audit.log(db, user, entity="student", action="import",
                  entity_label=f"Arxiv: {ok} ta o'quvchi",
                  new_value=ok, commit=True)

    return {"committed": commit, "ok": ok, "duplicate": dup,
            "skipped": bad, "rows": out[:500],
            "shown": min(len(out), 500), "all_rows": len(out)}


@app.get("/api/archive/students/import")
def archive_students_import_stats(db: Session = Depends(get_db),
                                  user=Depends(require_role(
                                      *_ARCH_IMPORT_ROLES))):
    q = (db.query(models.Student)
         .filter(models.Student.note.like(f"{_ARCH_TAG}%")))
    rows = q.all()
    return {"count": len(rows),
            "can_undo": user.role == roles.FOUNDER}


@app.delete("/api/archive/students/import")
def archive_students_import_undo(db: Session = Depends(get_db),
                                 user=Depends(require_role(roles.FOUNDER))):
    """Import ochgan kartalarni qaytarib oladi — faqat izi yo'qlarini."""
    gone = kept = 0
    for s in (db.query(models.Student)
              .filter(models.Student.note.like(f"{_ARCH_TAG}%")).all()):
        busy = (db.query(models.Payment)
                .filter(models.Payment.student_id == s.id).count()
                or db.query(models.Attendance)
                .filter(models.Attendance.student_id == s.id).count()
                or db.query(models.ExamResult)
                .filter(models.ExamResult.student_id == s.id).count())
        if busy:
            kept += 1
            continue
        db.delete(s)
        gone += 1
    db.commit()
    audit.log(db, user, entity="student", action="delete",
              entity_label="Arxiv importi bekor qilindi",
              old_value=gone,
              note=(f"{kept} tasida to'lov/yo'qlama bor — saqlab qolindi"
                    if kept else None),
              commit=True)
    return {"deleted": gone, "kept": kept}


# =====================================================================
#  EXAMINER VA SUPPORT DARAJALARI: Volontyor -> Junior -> Middle ->
#  Senior
#
#  Volontyorga OYLIK BERILMAYDI — u tajriba to'plash bosqichi.
#  Qolgan darajalarda hisoblangan oylik koeffitsiyentga ko'paytiriladi.
#  Koeffitsiyentlar bazadan o'qiladi, asoschi istagan payt o'zgartiradi.
# =====================================================================
_GRADE_SEED = [
    ("volunteer", "Volontyor", 0.00, 1),
    ("junior", "Junior", 1.00, 2),
    ("middle", "Middle", 1.15, 3),
    ("senior", "Senior", 1.30, 4),
]
_GRADED_ROLES = (roles.EXAMINER, roles.HEAD_EXAMINER,
                 roles.SUPPORT_TEACHER, roles.HEAD_SUPPORT)
_GRADE_SET = list(dict.fromkeys(
    list(roles.FULL_ACCESS) + [roles.HR_MANAGER, roles.ACADEMIC_HEAD,
                               roles.HEAD_EXAMINER, roles.HEAD_SUPPORT]))

if getattr(models, "StaffGrade", None) is None:
    class StaffGrade(_Base):
        """Xodimning darajasi (examiner / support)."""

        __tablename__ = "staff_grades"
        __table_args__ = {"extend_existing": True}

        id = Column(Integer, primary_key=True, index=True)
        user_id = Column(Integer, index=True, unique=True, nullable=False)
        grade = Column(String, default="volunteer")
        since = Column(_SaDate, default=date.today)
        note = Column(String)
        updated_by = Column(String)
        updated_at = Column(DateTime, default=_dt.utcnow,
                            onupdate=_dt.utcnow)

    class StaffGradeRate(_Base):
        """Daraja koeffitsiyenti. Volontyor = 0 (oylik yo'q)."""

        __tablename__ = "staff_grade_rates"
        __table_args__ = {"extend_existing": True}

        id = Column(Integer, primary_key=True, index=True)
        key = Column(String, unique=True, index=True, nullable=False)
        label = Column(String, nullable=False)
        coef = Column(Float, default=1.0)
        order_no = Column(Integer, default=0)

    models.StaffGrade = StaffGrade
    models.StaffGradeRate = StaffGradeRate
    try:
        _Base.metadata.create_all(
            bind=_engine,
            tables=[StaffGrade.__table__, StaffGradeRate.__table__])
    except Exception:
        pass

_SG = models.StaffGrade
_SGR = models.StaffGradeRate


def _grade_rates(db: Session) -> dict:
    rows = db.query(_SGR).all()
    if not rows:
        try:
            for k, lbl, coef, n in _GRADE_SEED:
                db.add(_SGR(key=k, label=lbl, coef=coef, order_no=n))
            db.commit()
            rows = db.query(_SGR).all()
        except Exception:
            db.rollback()
            rows = []
    out = {r.key: {"key": r.key, "label": r.label,
                   "coef": float(r.coef or 0), "order_no": r.order_no}
           for r in rows}
    for k, lbl, coef, n in _GRADE_SEED:
        out.setdefault(k, {"key": k, "label": lbl, "coef": coef,
                           "order_no": n})
    return out


def _grade_of(db: Session, user_id: int) -> str:
    r = db.query(_SG).filter(_SG.user_id == user_id).first()
    return (r.grade if r and r.grade else "volunteer")


def _apply_grade(db: Session, rows: list, key: str = "user_id") -> list:
    """Ro'yxatdagi har bir xodimga darajani va koeffitsiyentni qo'llaydi."""
    rates = _grade_rates(db)
    for r in rows:
        uid = r.get(key)
        g = _grade_of(db, uid) if uid else "volunteer"
        info = rates.get(g) or rates["volunteer"]
        coef = float(info["coef"])
        base = float(r.get("salary") or 0)
        r["grade"] = g
        r["grade_label"] = info["label"]
        r["grade_coef"] = coef
        r["salary_base"] = round(base, 0)
        r["salary"] = round(base * coef, 0)
        # Qoldiq oylikdan keyin qayta hisoblanadi — aks holda
        # volontyorga 0 so'm oylikda ham "qoldiq" ko'rinib turardi.
        if "paid" in r:
            r["left"] = round(r["salary"] - float(r.get("paid") or 0), 0)
        if coef == 0:
            r["grade_note"] = "Volontyor — oylik berilmaydi"
    return rows


@app.get("/api/staff-grades")
def staff_grades_list(db: Session = Depends(get_db),
                      user=Depends(require_role(*_PAYROLL_VIEW))):
    rates = _grade_rates(db)
    order = sorted(rates.values(), key=lambda x: x["order_no"])
    us = (db.query(models.User)
          .filter(models.User.role.in_(_GRADED_ROLES),
                  models.User.is_active == 1)
          .order_by(models.User.full_name).all())
    us = [u for u in us if user.role in tuple(roles.ORG_WIDE_ROLES)
          or not user.branch_id or u.branch_id == user.branch_id]
    rows = []
    for u in us:
        r = db.query(_SG).filter(_SG.user_id == u.id).first()
        g = (r.grade if r and r.grade else "volunteer")
        rows.append({
            "user_id": u.id, "name": u.full_name,
            "role": roles.UZ_LABELS.get(u.role, u.role),
            "grade": g,
            "grade_label": (rates.get(g) or {}).get("label", g),
            "coef": (rates.get(g) or {}).get("coef", 0),
            "since": r.since.isoformat() if r and r.since else None,
            "note": r.note if r else None,
        })
    return {"grades": order, "rows": rows,
            "can_edit": user.role in tuple(_GRADE_SET),
            "can_edit_rates": user.role == roles.FOUNDER,
            "hint": ("Volontyorga oylik berilmaydi. Junior, Middle va "
                     "Senior darajalarida hisoblangan oylik "
                     "koeffitsiyentga ko'paytiriladi.")}


@app.put("/api/staff-grades/{target_id}")
def staff_grade_set(target_id: int, payload: dict = Body(...),
                    db: Session = Depends(get_db),
                    user=Depends(require_role(*_GRADE_SET))):
    g = str(payload.get("grade") or "").strip()
    rates = _grade_rates(db)
    if g not in rates:
        raise HTTPException(400, "Noto'g'ri daraja")
    u = db.query(models.User).get(target_id)
    if not u:
        raise HTTPException(404, "Xodim topilmadi")
    if u.role not in _GRADED_ROLES:
        raise HTTPException(
            400, "Daraja faqat examiner va support teacherga qo'yiladi")
    row = db.query(_SG).filter(_SG.user_id == u.id).first()
    old = row.grade if row else None
    if row is None:
        row = _SG(user_id=u.id)
        db.add(row)
    row.grade = g
    row.since = roles.local_today()
    row.note = payload.get("note")
    row.updated_by = user.full_name
    db.commit()
    audit.log(db, user, entity="user", action="update", entity_id=u.id,
              entity_label=u.full_name, field="Daraja",
              old_value=old, new_value=rates[g]["label"], commit=True)
    return {"ok": True, "grade": g, "label": rates[g]["label"],
            "coef": rates[g]["coef"]}


@app.put("/api/staff-grades")
def staff_grade_rates_set(payload: dict = Body(...),
                          db: Session = Depends(get_db),
                          user=Depends(require_role(roles.FOUNDER))):
    _grade_rates(db)
    _changed = []  # (row, old_coef) - keyin, commit'dan OLDIN yozib olamiz
    for it in (payload.get("rates") or []):
        k = str(it.get("key") or "")
        row = db.query(_SGR).filter(_SGR.key == k).first()
        if row is None:
            continue
        try:
            c = float(it.get("coef"))
        except (TypeError, ValueError):
            continue
        if c < 0 or c > 5:
            raise HTTPException(400, "Koeffitsiyent 0 dan 5 gacha bo'lsin")
        if c != row.coef:
            _changed.append((row, row.coef))
            row.coef = c
    db.commit()
    # Bu BARCHA xodimlarning oyligini hisoblash formulasiga ta'sir
    # qiladigan global sozlama - FOUNDER'dan boshqa hech kim
    # o'zgartira olmaydi, shuning uchun HAR bir o'zgargan (haqiqatda
    # farq qilgan, no-op emas) koeffitsiyent alohida qayd etiladi.
    for row, old_coef in _changed:
        audit.log(db, user, entity="staff_grade_rate", action="update",
                  entity_id=row.id, entity_label=row.label,
                  field="Koeffitsiyent", old_value=old_coef,
                  new_value=row.coef)
    if _changed:
        db.commit()
    return {"ok": True, "grades": sorted(_grade_rates(db).values(),
                                         key=lambda x: x["order_no"])}


# --- Oylik ro'yxatlariga daraja qo'llanadi ---
_cur_ex_sal = _find_endpoint("/api/examiners/salary", "GET")
_cur_su_sal = _find_endpoint("/api/support/salary", "GET")

if _cur_ex_sal is not None:
    _drop_route("/api/examiners/salary", "GET")

    @app.get("/api/examiners/salary")
    def examiner_salary_v3(year: int | None = None, month: int | None = None,
                           db: Session = Depends(get_db),
                           user=Depends(require_role(
                               *list(dict.fromkeys(
                                   list(roles.EXAMINER_SALARY_VIEW)
                                   + _PAYROLL_VIEW))))):
        data = _cur_ex_sal(year=year, month=month, db=db, user=user)
        rows = _apply_grade(db, data.get("rows") or [], "user_id")
        data["rows"] = rows
        data["total"] = round(sum(r["salary"] for r in rows), 0)
        return data

if _cur_su_sal is not None:
    _drop_route("/api/support/salary", "GET")

    @app.get("/api/support/salary")
    def support_salary_v3(year: int | None = None, month: int | None = None,
                          db: Session = Depends(get_db),
                          user=Depends(require_role(
                              *list(dict.fromkeys(
                                  list(roles.SALARY_VIEW_ALL)
                                  + [roles.ACADEMIC_HEAD]
                                  + _PAYROLL_VIEW))))):
        data = _cur_su_sal(year=year, month=month, db=db, user=user)
        rows = _apply_grade(db, data.get("rows") or [], "user_id")
        data["rows"] = rows
        data["total"] = round(sum(r["salary"] for r in rows), 0)
        return data


# =====================================================================
#  HR KUTUBXONASI (onboarding)
#
#  Yangi xodim ishga kirganda ko'rishi shart bo'lgan video, kitob va
#  fayllar bir joyda turadi. Har bir xodim uchun: nechi foiz ko'rgani
#  va HR "topshirdi" deb belgilagani yoziladi. Daraja ko'tarishda shu
#  ro'yxat mezonlardan biri bo'ladi.
# =====================================================================
_LIB_KINDS = [("video", "Video"), ("book", "Kitob"),
              ("file", "Fayl"), ("link", "Havola")]
_LIB_KIND_LABELS = dict(_LIB_KINDS)
_LIB_MANAGE = list(dict.fromkeys(
    list(roles.FULL_ACCESS) + [roles.HR_MANAGER, roles.ACADEMIC_HEAD,
                               roles.HEAD_EXAMINER, roles.HEAD_SUPPORT]))

if getattr(models, "LibraryItem", None) is None:
    class LibraryItem(_Base):
        """Kutubxona yozuvi: video, kitob, fayl yoki havola."""

        __tablename__ = "library_items"
        __table_args__ = {"extend_existing": True}

        id = Column(Integer, primary_key=True, index=True)
        title = Column(String, nullable=False)
        kind = Column(String, default="video")
        url = Column(String)
        attachment_id = Column(Integer)
        minutes = Column(Integer, default=0)
        description = Column(String)
        # Kimlarga tegishli: rollar ro'yxati. Bo'sh = hammaga.
        target_roles = Column(String)
        required = Column(Integer, default=1)
        order_no = Column(Integer, default=0)
        active = Column(Integer, default=1)
        created_by = Column(String)
        created_at = Column(DateTime, default=_dt.utcnow)

    class LibraryProgress(_Base):
        """Kim nechi foiz ko'rgani va topshirgani."""

        __tablename__ = "library_progress"
        __table_args__ = {"extend_existing": True}

        id = Column(Integer, primary_key=True, index=True)
        item_id = Column(Integer, index=True, nullable=False)
        user_id = Column(Integer, index=True, nullable=False)
        percent = Column(Integer, default=0)
        passed = Column(Integer, default=0)
        passed_at = Column(_SaDate)
        passed_by = Column(String)
        note = Column(String)
        updated_at = Column(DateTime, default=_dt.utcnow,
                            onupdate=_dt.utcnow)

    models.LibraryItem = LibraryItem
    models.LibraryProgress = LibraryProgress
    try:
        _Base.metadata.create_all(
            bind=_engine,
            tables=[LibraryItem.__table__, LibraryProgress.__table__])
    except Exception:
        pass

_LI = models.LibraryItem
_LP = models.LibraryProgress


def _lib_for_role(it, role: str) -> bool:
    t = [x.strip() for x in (it.target_roles or "").split(",") if x.strip()]
    return (not t) or (role in t)


def _lib_out(it, prog=None) -> dict:
    return {
        "id": it.id, "title": it.title, "kind": it.kind,
        "kind_label": _LIB_KIND_LABELS.get(it.kind, it.kind),
        "url": it.url, "attachment_id": it.attachment_id,
        "minutes": it.minutes or 0, "description": it.description,
        "target_roles": [x for x in (it.target_roles or "").split(",") if x],
        "required": bool(it.required), "order_no": it.order_no or 0,
        "active": bool(it.active),
        "percent": (prog.percent or 0) if prog else 0,
        "passed": bool(prog.passed) if prog else False,
        "passed_at": (prog.passed_at.isoformat()
                      if prog and prog.passed_at else None),
        "note": prog.note if prog else None,
    }


@app.get("/api/library")
def library_list(db: Session = Depends(get_db),
                 user=Depends(M.get_current_user)):
    """O'z ro'yxatim + (HR uchun) har bir yozuv bo'yicha umumiy holat."""
    manage = user.role in tuple(_LIB_MANAGE)
    q = db.query(_LI).order_by(_LI.order_no, _LI.id)
    items = [it for it in q.all() if manage or (
        it.active and _lib_for_role(it, user.role))]
    mine = {p.item_id: p for p in db.query(_LP)
            .filter(_LP.user_id == user.id).all()}

    out = []
    for it in items:
        row = _lib_out(it, mine.get(it.id))
        if manage:
            people = db.query(_LP).filter(_LP.item_id == it.id).all()
            row["watchers"] = len(people)
            row["done"] = len([p for p in people if p.passed])
            row["avg_percent"] = (
                round(sum(p.percent or 0 for p in people) / len(people))
                if people else 0)
        out.append(row)

    total = len([r for r in out if r["required"]])
    done = len([r for r in out if r["required"] and r["passed"]])
    return {
        "items": out, "kinds": [{"key": k, "label": l}
                                for k, l in _LIB_KINDS],
        "can_manage": manage,
        "my_total": total, "my_done": done,
        "my_percent": round(done * 100 / total) if total else 0,
        "roles": [{"key": r, "label": roles.UZ_LABELS.get(r, r)}
                  for r in roles.STAFF_ROLES],
    }


@app.post("/api/library")
def library_add(payload: dict = Body(...), db: Session = Depends(get_db),
                user=Depends(require_role(*_LIB_MANAGE))):
    title = str(payload.get("title") or "").strip()
    if not title:
        raise HTTPException(400, "Nomini kiriting")
    kind = str(payload.get("kind") or "video")
    if kind not in _LIB_KIND_LABELS:
        raise HTTPException(400, "Noto'g'ri tur")
    url = str(payload.get("url") or "").strip() or None
    aid = payload.get("attachment_id")
    if not url and not aid:
        raise HTTPException(
            400, "Havola qo'ying yoki fayl yuklang — bittasi bo'lishi kerak")
    it = _LI(
        title=title, kind=kind, url=url,
        attachment_id=int(aid) if aid else None,
        minutes=int(payload.get("minutes") or 0),
        description=str(payload.get("description") or "").strip() or None,
        target_roles=",".join(payload.get("target_roles") or []) or None,
        required=1 if payload.get("required", True) else 0,
        order_no=int(payload.get("order_no") or 0),
        active=1, created_by=user.full_name)
    db.add(it)
    db.commit()
    db.refresh(it)
    audit.log(db, user, entity="user", action="create",
              entity_label=f"Kutubxona: {title}", commit=True)
    return _lib_out(it)


@app.put("/api/library/{item_id}")
def library_edit(item_id: int, payload: dict = Body(...),
                 db: Session = Depends(get_db),
                 user=Depends(require_role(*_LIB_MANAGE))):
    it = db.query(_LI).get(item_id)
    if not it:
        raise HTTPException(404, "Topilmadi")
    for f in ("title", "url", "description"):
        if f in payload:
            setattr(it, f, str(payload.get(f) or "").strip() or None)
    if payload.get("kind") in _LIB_KIND_LABELS:
        it.kind = payload["kind"]
    if "minutes" in payload:
        it.minutes = int(payload.get("minutes") or 0)
    if "order_no" in payload:
        it.order_no = int(payload.get("order_no") or 0)
    if "target_roles" in payload:
        it.target_roles = ",".join(payload.get("target_roles") or []) or None
    if "required" in payload:
        it.required = 1 if payload.get("required") else 0
    if "active" in payload:
        it.active = 1 if payload.get("active") else 0
    if not it.title:
        raise HTTPException(400, "Nomini kiriting")
    db.commit()
    return _lib_out(it)


@app.delete("/api/library/{item_id}")
def library_delete(item_id: int, db: Session = Depends(get_db),
                   user=Depends(require_role(*_LIB_MANAGE))):
    it = db.query(_LI).get(item_id)
    if not it:
        raise HTTPException(404, "Topilmadi")
    db.query(_LP).filter(_LP.item_id == item_id).delete(
        synchronize_session=False)
    name = it.title
    db.delete(it)
    db.commit()
    audit.log(db, user, entity="user", action="delete",
              entity_label=f"Kutubxona: {name}", commit=True)
    return {"ok": True}


@app.put("/api/library/{item_id}/progress")
def library_progress(item_id: int, payload: dict = Body(...),
                     db: Session = Depends(get_db),
                     user=Depends(M.get_current_user)):
    """Xodim o'zi qancha ko'rganini belgilaydi. "Topshirdi" ni HR qo'yadi."""
    it = db.query(_LI).get(item_id)
    if not it:
        raise HTTPException(404, "Topilmadi")
    try:
        pct = int(payload.get("percent"))
    except (TypeError, ValueError):
        raise HTTPException(400, "Foizni kiriting")
    pct = max(0, min(100, pct))
    row = (db.query(_LP)
           .filter(_LP.item_id == item_id, _LP.user_id == user.id).first())
    if row is None:
        row = _LP(item_id=item_id, user_id=user.id)
        db.add(row)
    # Orqaga tushirilmaydi — ko'rilgan ko'rilgan
    row.percent = max(row.percent or 0, pct)
    db.commit()
    return _lib_out(it, row)


@app.get("/api/library/{item_id}/people")
def library_people(item_id: int, db: Session = Depends(get_db),
                   user=Depends(require_role(*_LIB_MANAGE))):
    it = db.query(_LI).get(item_id)
    if not it:
        raise HTTPException(404, "Topilmadi")
    us = (db.query(models.User)
          .filter(models.User.is_active == 1)
          .order_by(models.User.full_name).all())
    us = [u for u in us if u.role in tuple(roles.STAFF_ROLES)
          and _lib_for_role(it, u.role)]
    if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
        us = [u for u in us if u.branch_id == user.branch_id]
    prog = {p.user_id: p for p in db.query(_LP)
            .filter(_LP.item_id == item_id).all()}
    rows = []
    for u in us:
        p = prog.get(u.id)
        rows.append({
            "user_id": u.id, "name": u.full_name,
            "role": roles.UZ_LABELS.get(u.role, u.role),
            "percent": (p.percent or 0) if p else 0,
            "passed": bool(p and p.passed),
            "passed_at": (p.passed_at.isoformat()
                          if p and p.passed_at else None),
            "passed_by": p.passed_by if p else None,
            "note": p.note if p else None,
        })
    return {"item": _lib_out(it), "rows": rows,
            "done": len([r for r in rows if r["passed"]]),
            "total": len(rows)}


@app.put("/api/library/{item_id}/people/{target_id}")
def library_mark(item_id: int, target_id: int, payload: dict = Body(...),
                 db: Session = Depends(get_db),
                 user=Depends(require_role(*_LIB_MANAGE))):
    """HR "topshirdi" deb belgilaydi (yoki belgini olib tashlaydi)."""
    it = db.query(_LI).get(item_id)
    if not it:
        raise HTTPException(404, "Topilmadi")
    u = db.query(models.User).get(target_id)
    if not u:
        raise HTTPException(404, "Xodim topilmadi")
    row = (db.query(_LP)
           .filter(_LP.item_id == item_id, _LP.user_id == target_id).first())
    if row is None:
        row = _LP(item_id=item_id, user_id=target_id)
        db.add(row)
    ok = bool(payload.get("passed"))
    row.passed = 1 if ok else 0
    row.passed_at = roles.local_today() if ok else None
    row.passed_by = user.full_name if ok else None
    if ok:
        row.percent = 100
    if "percent" in payload and not ok:
        try:
            row.percent = max(0, min(100, int(payload["percent"])))
        except (TypeError, ValueError):
            pass
    if "note" in payload:
        row.note = str(payload.get("note") or "").strip() or None
    db.commit()
    audit.log(db, user, entity="user", action="update", entity_id=u.id,
              entity_label=u.full_name, field=f"Kutubxona: {it.title}",
              new_value="topshirdi" if ok else "bekor qilindi",
              commit=True)
    return {"ok": True, "passed": ok, "percent": row.percent}


@app.get("/api/library/person/{target_id}")
def library_person(target_id: int, db: Session = Depends(get_db),
                   user=Depends(M.get_current_user)):
    """Bitta xodimning kutubxona holati — daraja ko'tarishda ko'riladi."""
    if target_id != user.id and user.role not in tuple(_LIB_MANAGE):
        raise HTTPException(403, "Ruxsat yo'q")
    u = db.query(models.User).get(target_id)
    if not u:
        raise HTTPException(404, "Xodim topilmadi")
    prog = {p.item_id: p for p in db.query(_LP)
            .filter(_LP.user_id == target_id).all()}
    items = [it for it in db.query(_LI)
             .order_by(_LI.order_no, _LI.id).all()
             if it.active and _lib_for_role(it, u.role)]
    out = [_lib_out(it, prog.get(it.id)) for it in items]
    need = [r for r in out if r["required"]]
    done = [r for r in need if r["passed"]]
    return {"user_id": u.id, "name": u.full_name,
            "items": out, "total": len(need), "done": len(done),
            "percent": round(len(done) * 100 / len(need)) if need else 0}


# =====================================================================
#  SUPPORT TEACHERNING O'Z DARAJA YO'LI
#
#  Ilgari "Mening yo'lim" sahifasida supportga USTOZNING darajalari
#  (Junior teacher, 80 000 so'm har bir o'quvchidan) ko'rinardi — bu
#  xato edi, chunki supportning bosqichlari ham, talablari ham, oylik
#  hisobi ham butunlay boshqa.
#
#  Oylik hisobi O'ZGARMAYDI: seanslardan chiqadigan formula o'z holida
#  qoladi, ustiga faqat daraja koeffitsiyenti qo'llanadi. Qo'llanmadagi
#  "soatiga 2000 / 3500 / 6000 so'm" raqamlari ishlatilmaydi.
# =====================================================================
_SUP_LADDER = {
    "volunteer": {
        "groups": "—",
        "free_courses": 0,
        "cert": "CEFR B2 53+ yoki IELTS 5.5",
        "note": ("2 oylik sinov bosqichi: oylik berilmaydi va imtiyoz "
                 "yo'q. Kitob va videolarni topshirib boradi."),
    },
    "junior": {
        "groups": "2 ta guruh",
        "free_courses": 1,
        "cert": "CEFR B2 60+ yoki IELTS 6.0",
        "note": "Bitta kurs bepul.",
    },
    "middle": {
        "groups": "3–5 ta guruh",
        "free_courses": 1,
        "cert": "CEFR C1 yoki IELTS 6.5+",
        "note": "Bitta kurs bepul.",
    },
    "senior": {
        "groups": "10 tagacha guruh",
        "free_courses": 2,
        "cert": "CEFR C1 yoki IELTS 7.0+",
        "note": "Ikkita kurs bepul.",
    },
}
_SUP_VOLUNTEER_MONTHS = 2


def _months_since(d) -> float:
    if not d:
        return 0.0
    today = roles.local_today()
    return round((today - d).days / 30.44, 1)


@app.get("/api/me/support-career")
def my_support_career(db: Session = Depends(get_db),
                      user=Depends(M.get_current_user)):
    """Supportning o'z daraja yo'li. Ustoznikidan butunlay alohida."""
    if user.role not in (roles.SUPPORT_TEACHER, roles.HEAD_SUPPORT):
        raise HTTPException(404, "Bu sahifa support teacherlar uchun")

    rates = _grade_rates(db)
    row = db.query(_SG).filter(_SG.user_id == user.id).first()
    cur = (row.grade if row and row.grade else "volunteer")

    levels = []
    for info in sorted(rates.values(), key=lambda x: x["order_no"]):
        extra = _SUP_LADDER.get(info["key"], {})
        levels.append({
            "key": info["key"],
            "label": (info["label"] + " support"
                      if info["key"] != "volunteer" else "Volontyor support"),
            "coef": info["coef"],
            "groups": extra.get("groups", "—"),
            "free_courses": extra.get("free_courses", 0),
            "cert": extra.get("cert"),
            "note": extra.get("note"),
            "paid": info["coef"] > 0,
        })

    # Hozirgi holat
    gids = [a.group_id for a in db.query(models.SupportAssignment)
            .filter(models.SupportAssignment.user_id == user.id,
                    models.SupportAssignment.group_id.isnot(None)).all()]
    today = roles.local_today()
    t = M._teacher_of_user(db, user)
    month = {}
    if t:
        try:
            d = M._support_month(db, t.id, today.year, today.month)
            d.pop("sessions", None)
            month = d
        except Exception:
            month = {}
    base = float(month.get("salary") or 0)
    coef = float((rates.get(cur) or {}).get("coef", 0))

    # Kutubxona — daraja ko'tarishda qaraladigan mezonlardan biri
    lib_done = lib_total = 0
    try:
        prog = {p.item_id: p for p in db.query(_LP)
                .filter(_LP.user_id == user.id).all()}
        for it in db.query(_LI).all():
            if not it.active or not it.required:
                continue
            if not _lib_for_role(it, user.role):
                continue
            lib_total += 1
            p = prog.get(it.id)
            if p and p.passed:
                lib_done += 1
    except Exception:
        pass

    in_grade = _months_since(row.since if row else None)
    return {
        "kind": "support",
        "grade": cur,
        "grade_label": (rates.get(cur) or {}).get("label", cur),
        "coef": coef,
        "since": (row.since.isoformat() if row and row.since else None),
        "months_in_grade": in_grade,
        "months_total": _months_since(user.hired_date),
        "volunteer_months_needed": _SUP_VOLUNTEER_MONTHS,
        "levels": levels,
        "stats": {
            "period": month.get("period"),
            "groups": len(set(gids)),
            "hours": month.get("hours", 0),
            "students": month.get("students", 0),
            "avg_percent": month.get("avg_percent"),
            "salary_base": round(base, 0),
            "salary": round(base * coef, 0),
        },
        "library": {"done": lib_done, "total": lib_total,
                    "percent": (round(lib_done * 100 / lib_total)
                                if lib_total else 0)},
        "formula": month.get("formula"),
        "hint": ("Oylik seanslardan avtomat hisoblanadi, so'ng daraja "
                 "koeffitsiyentiga ko'paytiriladi. Volontyor bosqichida "
                 "oylik berilmaydi."),
    }


# =====================================================================
#  BAZA SXEMASI MODELDAN ORQADA QOLMASIN
#
#  create_all() faqat YO'Q JADVALNI yaratadi — mavjud jadvalga yangi
#  ustun qo'shmaydi. Shuning uchun modelga ustun qo'shilib migratsiya
#  yozilmasa, o'sha jadvalga tegadigan HAR BIR so'rov 500 beradi:
#  dashboard ham, dars jadvali ham, o'quvchilar ro'yxati ham birdan
#  qulaydi. Kod to'g'ri, baza ortda qolgan — tashqaridan qarab sababini
#  topish qiyin, chunki xato ekranda "server xatosi" bo'lib ko'rinadi.
#
#  Shu yerda ilova ishga tushganda tekshiriladi va yetishmagan ustun
#  o'zi qo'shiladi. Faqat NULL bo'la oladigan ustunlar qo'shiladi:
#  NOT NULL ustun ma'lumot bilan to'ldirilishi kerak, uni jimgina
#  qo'shib bo'lmaydi — u ro'yxatga chiqariladi va qo'lda hal qilinadi.
# =====================================================================
def _sync_missing_columns() -> dict:
    from sqlalchemy import inspect as _insp
    from sqlalchemy import text as _txt
    from sqlalchemy.schema import CreateColumn
    from database import Base as _B, engine as _eng

    try:
        insp = _insp(_eng)
        have = set(insp.get_table_names())
    except Exception:
        return {"added": [], "manual": []}

    cols_by_table = {}
    try:                                    # bitta borishda hammasi
        for key, cols in insp.get_multi_columns().items():
            name = key[1] if isinstance(key, tuple) else key
            cols_by_table[name] = {c["name"] for c in cols}
    except Exception:
        cols_by_table = {}

    added, manual = [], []
    for table in _B.metadata.sorted_tables:
        if table.name not in have:
            continue
        known = cols_by_table.get(table.name)
        if known is None:
            try:
                known = {c["name"] for c in insp.get_columns(table.name)}
            except Exception:
                continue
        for col in table.columns:
            if col.name in known or col.primary_key:
                continue
            if (not col.nullable and col.server_default is None
                    and col.default is None):
                manual.append(f"{table.name}.{col.name}")
                continue
            try:
                ddl = str(CreateColumn(col).compile(dialect=_eng.dialect))
                with _eng.begin() as cx:
                    cx.execute(_txt(
                        f'ALTER TABLE "{table.name}" ADD COLUMN {ddl}'))
                added.append(f"{table.name}.{col.name}")
            except Exception as exc:        # noqa: BLE001
                manual.append(f"{table.name}.{col.name} "
                              f"({exc.__class__.__name__})")
    if added:
        print("[schema] yangi ustunlar qo'shildi: " + ", ".join(added))
    if manual:
        print("[schema] qo'lda migratsiya kerak: " + ", ".join(manual))
    return {"added": added, "manual": manual}


_SCHEMA_SYNC = _sync_missing_columns()


@app.get("/api/system/schema-sync")
def system_schema_sync(user=Depends(require_role(*roles.FULL_ACCESS))):
    """Ishga tushganda nima qo'shilgani — xato qidirishda kerak."""
    return {
        "added": _SCHEMA_SYNC.get("added", []),
        "manual": _SCHEMA_SYNC.get("manual", []),
        "hint": ("Bo'sh bo'lsa — baza model bilan mos. \"manual\" "
                 "ro'yxatidagi ustunlar NOT NULL, ularni qo'lda "
                 "to'ldirish kerak."),
    }
