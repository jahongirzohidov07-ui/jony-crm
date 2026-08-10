"""Auto-extracted from main.py during refactor (split-main). Domain: groups_lessons."""
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

_WEEKDAY_INDEX = {"mon": 0, "tue": 1, "wed": 2, "thu": 3,
                  "fri": 4, "sat": 5, "sun": 6}

def _sync_scheduled_lessons(db: Session, group: models.Group,
                            start: date, end: date) -> None:
    """Guruhning dars kunlari ("mon,wed,fri") bo'yicha shu oydagi barcha
    dars kunlarini AVTOMAT yaratadi.

    Har bir darsni qo'lda kiritish shart emas: kunlar tanlangan bo'lsa,
    butun oy jadvali yoqlama qo'yishga tayyor holda chiqadi. Yangi
    yaratilgan darslar held=0 ("rejalashtirilgan") bo'ladi - ular pulga
    ham, ustoz ish haqiga ham kirmaydi, toki yoqlama qo'yilmaguncha.

    Jadval o'zgarsa (masalan juma olib tashlansa) - endi mos kelmaydigan,
    hali yoqlama ham baho ham qo'yilmagan darslar tozalanadi."""
    days = [d.strip() for d in (group.lesson_days or "").split(",") if d.strip()]
    wanted = {_WEEKDAY_INDEX[d] for d in days if d in _WEEKDAY_INDEX}

    existing = (
        db.query(models.Lesson)
        .filter(models.Lesson.group_id == group.id,
                models.Lesson.date >= start, models.Lesson.date <= end)
        .all()
    )
    # DUBL HIMOYASI: ikki parallel so'rov bir kunga ikkita dars
    # yaratib qo'ygan bo'lishi mumkin (3-avgust 2 ta kabi). Yoqlama va
    # bahosi yo'q, o'tkazilmagan nusxa o'chiriladi; ikkalasi ham band
    # bo'lsa - tegilmaydi (pul hujjati).
    by_date = {}
    dup_removed = False
    for ls in sorted(existing, key=lambda l: l.id):
        prev = by_date.get(ls.date)
        if not prev:
            by_date[ls.date] = ls
            continue
        def _busy(l):
            if l.held:
                return True
            return db.query(models.Attendance).filter(
                models.Attendance.lesson_id == l.id).count() > 0
        loser = None
        if not _busy(ls):
            loser = ls
        elif not _busy(prev):
            loser = prev
            by_date[ls.date] = ls
        if loser is not None:
            db.delete(loser)
            dup_removed = True
        else:
            # ikkalasi ham band — qo'l bilan ko'rish kerak, tegmaymiz
            pass
    if dup_removed:
        db.flush()
    existing = list(by_date.values())

    # KO'CHIRILGAN DARSLAR. Ko'chirilgan dars ataylab jadval kunidan
    # tashqariga tushadi (masalan chorshanbadan payshanbaga). Agar shu
    # yerda himoyalanmasa, sahifa qayta ochilganda "jadvalga mos
    # kelmaydi" deb O'CHIRIB yuboriladi, eski kunida esa yangisi
    # paydo bo'ladi — ya'ni ko'chirish bekor bo'lib qoladi.
    moves = db.query(models.LessonReschedule).filter(
        models.LessonReschedule.group_id == group.id,
        models.LessonReschedule.status.in_(roles.RESCHEDULE_DONE)).all()
    protected = {m.lesson_id for m in moves if m.lesson_id}
    vacated = {m.from_date for m in moves}      # bu kunlarda dars yo'q
    landed = {m.to_date for m in moves}
    protected |= {ls.id for ls in existing if ls.date in landed}

    # Guruh boshlangunicha va tugagandan keyin dars bo'lmaydi.
    lo = max(start, group.start_date) if group.start_date else start
    hi = min(end, group.end_date) if group.end_date else end

    changed = False
    if wanted:
        d = lo
        while d <= hi:
            # Bo'shatilgan kunga yangi dars qo'yilmaydi — dars u yerdan
            # ko'chirilgan
            if d.weekday() in wanted and d not in by_date and d not in vacated:
                db.add(models.Lesson(
                    group_id=group.id, teacher_id=group.teacher_id,
                    date=d, held=0, created_by="avtomat"))
                changed = True
            d += timedelta(days=1)

    # Jadvalga mos kelmay qolgan bo'sh darslarni olib tashlaymiz.
    stale = [ls for ls in existing
             if not ls.held and ls.id not in protected
             and (ls.date.weekday() not in wanted
                  or ls.date < lo or ls.date > hi)]
    for ls in stale:
        has_data = (
            db.query(models.Attendance)
            .filter(models.Attendance.lesson_id == ls.id).first()
            or db.query(models.DailyGrade)
            .filter(models.DailyGrade.lesson_id == ls.id).first()
        )
        if not has_data:
            db.delete(ls)
            changed = True

    if changed:
        db.commit()

def _mark_lesson_held(db: Session, lesson: models.Lesson) -> None:
    """Yoqlama yoki baho qo'yilgan dars - o'tilgan dars. Shundan keyingina
    u pulga va ustoz ish haqiga kiradi."""
    if not lesson.held:
        lesson.held = 1

def _group_lessons_in_month(db: Session, group_id: int, year: int, month: int):
    start, end = billing.month_bounds(year, month)
    group = db.query(models.Group).get(group_id)
    if group:
        _sync_scheduled_lessons(db, group, start, end)
    return (
        db.query(models.Lesson)
        .filter(models.Lesson.group_id == group_id,
                models.Lesson.date >= start, models.Lesson.date <= end)
        .order_by(models.Lesson.date)
        .all()
    )

@router.get("/api/groups/{group_id}/attendance", response_model=schemas.AttendanceGrid)
def attendance_grid(
    group_id: int,
    year: int,
    month: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.ATTENDANCE_VIEW)),
):
    """Davomat jadvali: chapda o'quvchilar, tepada shu oydagi dars kunlari."""
    _get_group_in_scope(db, group_id, user)
    students = _group_students(db, group_id)
    lessons = _group_lessons_in_month(db, group_id, year, month)
    lesson_ids = [ls.id for ls in lessons]

    marks, hw = {}, {}
    if lesson_ids:
        rows = db.query(models.Attendance).filter(
            models.Attendance.lesson_id.in_(lesson_ids)
        ).all()
        # true = keldi, false = kelmadi, 2 = kech keldi
        marks = {f"{a.lesson_id}:{a.student_id}":
                 (2 if a.present == 2 else bool(a.present)) for a in rows}
        hw = {f"{a.lesson_id}:{a.student_id}": a.homework
              for a in rows if a.homework is not None}

    return schemas.AttendanceGrid(
        students=[schemas.GridStudent(id=s.id, full_name=s.full_name,
                                      status=s.status) for s in students],
        lessons=[schemas.GridLesson(id=ls.id, date=ls.date, held=ls.held or 0)
                 for ls in lessons],
        marks=marks,
        homework=hw,
        reschedule=_reschedule_box(db, group_id, user,
                                   for_month=date(year, month, 1)),
    )

@router.put("/api/lessons/{lesson_id}/attendance")
def save_attendance(
    lesson_id: int,
    payload: schemas.AttendanceBulk,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_ACCESS)),
):
    """Bitta dars kunining butun ustunini saqlaydi."""
    lesson = db.query(models.Lesson).get(lesson_id)
    if not lesson:
        raise HTTPException(404, "Dars topilmadi")
    _get_group_in_scope(db, lesson.group_id, user)

    # SANA QOIDALARI. Yoqlama — pul hujjati (ustoz oyligi shundan
    # chiqadi), shuning uchun qat'iy:
    #   kelajak — hech kimga: bo'lib o'tmagan darsni belgilab
    #             bo'lmaydi;
    #   o'tgan  — faqat asoschi va o'quv bo'limi rahbari: ustoz ham
    #             o'z o'tgan darsini o'zgartira olmaydi;
    #   bugun   — odatdagi tartibda.
    _today = roles.local_today()
    if lesson.date > _today:
        raise HTTPException(
            400, "Hali kelmagan kunga yoqlama qo'yilmaydi — dars "
                 "bo'lib o'tmagan")
    if lesson.date < _today and user.role not in tuple(
            roles.PAST_ATTENDANCE):
        raise HTTPException(
            403, "O'tib ketgan kunning yoqlamasini faqat asoschi va "
                 "o'quv bo'limi rahbari o'zgartira oladi")

    # Muzlatilgan o'quvchiga yoqlama qo'yilmaydi/o'zgartirilmaydi —
    # UI'da bunday qator umuman chiqmaydi (attendance_grid_v2), lekin
    # eski/keshlangan sahifa yoki to'g'ridan-to'g'ri so'rov orqali
    # ham himoyalanadi (2026-08-09, ish haqi hujjati himoyasi).
    _frozen_ids = {
        sid for (sid,) in db.query(models.Student.id).filter(
            models.Student.group_id == lesson.group_id,
            models.Student.status == "frozen").all()
    }

    existing = {
        a.student_id: a
        for a in db.query(models.Attendance).filter(
            models.Attendance.lesson_id == lesson_id).all()
    }
    newly_absent = []   # Telegram: "darsga kelmadi" xabari uchun
    newly_present = []  # Telegram: "darsga keldi" xabari uchun
    newly_late = []     # Telegram: "kech keldi" xabari uchun
    for m in payload.marks:
        if m.student_id in _frozen_ids:
            continue
        # Belgini olib tashlash: o'quvchi "belgilanmagan"ga qaytadi
        # va shu dars uchun oylikka kirmaydi
        if m.remove:
            row = existing.pop(m.student_id, None)
            if row:
                db.delete(row)
            continue
        hw = m.homework if m.homework in (0, 1, 2) else None
        # 1 = keldi, 2 = kech keldi, 0 = kelmadi. Kech kelgan ham
        # KELGAN: davomat foizida sanaladi, faqat jadvalda alohida
        # (soat belgisi bilan) ko'rinadi.
        val = (2 if m.late else 1) if m.present else 0
        row = existing.get(m.student_id)
        prev = (row.present or 0) if row else None
        if val == 0 and prev != 0:
            newly_absent.append(m.student_id)
        elif val == 1 and prev != 1:
            newly_present.append(m.student_id)
        elif val == 2 and prev != 2:
            newly_late.append(m.student_id)
        if row:
            row.present = val
            # Tekshirilmagan bo'lsa eskisiga tegilmaydi — ustoz
            # davomatni tuzatganda homework belgisi yo'qolib qolmasin
            if hw is not None:
                row.homework = hw
        else:
            new_row = models.Attendance(
                lesson_id=lesson_id, student_id=m.student_id,
                present=val, homework=hw,
                created_by=user.full_name)
            db.add(new_row)
            existing[m.student_id] = new_row
    db.flush()

    # Hamma belgi olib tashlangan bo'lsa dars "reja"ga qaytadi —
    # yoqlamasiz dars o'tilgan hisoblanmaydi va pul keltirmaydi
    left = db.query(models.Attendance).filter(
        models.Attendance.lesson_id == lesson_id).count()
    grades_left = db.query(models.DailyGrade).filter(
        models.DailyGrade.lesson_id == lesson_id).count()
    if left or grades_left:
        _mark_lesson_held(db, lesson)
    else:
        lesson.held = 0
    db.commit()

    # Telegram: BUGUNGI davomat haqida ota-onaga xabar (kelmadi/keldi/
    # kech keldi) — faqat YANGI belgilanganlarga, tuzatishlarda qayta
    # ketmaydi (2026-08-09, Jahongir: "darsga keldi degan bildirishnoma,
    # ustoz kech keldi deb belgilasa kech keldi degan bildirishnoma").
    if (newly_absent or newly_present or newly_late) \
            and lesson.date == _today and notify.enabled():
        try:
            g_name = (db.query(models.Group).get(lesson.group_id).name
                      if lesson.group_id else "")
            for sid in newly_absent:
                st = db.query(models.Student).get(sid)
                if st is not None and st.telegram_chat_id:
                    notify.send(
                        st.telegram_chat_id,
                        f"❗ {st.full_name} bugun ({lesson.date:%d.%m}) "
                        f"{g_name} darsiga kelmadi.\nSababini bilsangiz, "
                        "administratorga xabar bering.")
            for sid in newly_present:
                st = db.query(models.Student).get(sid)
                if st is not None and st.telegram_chat_id:
                    notify.send(
                        st.telegram_chat_id,
                        f"✅ {st.full_name} bugun ({lesson.date:%d.%m}) "
                        f"{g_name} darsiga keldi.")
            for sid in newly_late:
                st = db.query(models.Student).get(sid)
                if st is not None and st.telegram_chat_id:
                    notify.send(
                        st.telegram_chat_id,
                        f"🕒 {st.full_name} bugun ({lesson.date:%d.%m}) "
                        f"{g_name} darsiga kech keldi.")
        except Exception:
            pass

    # AVTOMAT XP: kelgani uchun ball va davomat ketma-ketligi.
    # Ustoz hech narsa bosmaydi.
    try:
        _xp_for_attendance(db, lesson, by_user=user)
    except Exception:
        db.rollback()

    # AVTOMAT XP: uy vazifasi uchun. Qoidalar allaqachon bor edi,
    # lekin ularni yoqadigan joy yo'q edi — endi davomat bilan birga
    # belgilanadi va o'zi hisoblanadi.
    try:
        _xp_for_homework(db, lesson, by_user=user)
    except Exception:
        db.rollback()

    # Sinovdagi o'quvchilar: yoqlama qo'yilishi bilan lid "sinovga keldi"
    # bo'ladi, uchinchi darsdan keyin esa o'quvchi AVTOMAT faollashadi.
    activated, touched = [], False
    for m in payload.marks:
        if not m.present:
            continue
        st = db.query(models.Student).get(m.student_id)
        if not st or st.status != "trial":
            continue
        lead = (db.query(models.Lead)
                .filter(models.Lead.converted_student_id == st.id).first())
        if not lead:
            lead = (db.query(models.Lead)
                    .filter(models.Lead.full_name == st.full_name,
                            models.Lead.stage.in_(["trial_scheduled", "no_show",
                                                   "contacted", "new"]))
                    .first())
        if lead and lead.stage != "trial_attended":
            lead.stage = "trial_attended"
            touched = True
        res = _maybe_auto_activate(db, st, user=user)
        if res:
            touched = True
            activated.append({"student_id": st.id, "full_name": st.full_name,
                              **res})
    # Lid bosqichi o'zgargan bo'lsa ham saqlaymiz - faollashish bo'lmasa
    # ham "sinovga keldi" belgisi yo'qolib qolmasligi kerak.
    if touched:
        db.commit()

    # AVTOMUZLATISH: ketma-ket 3 darsga kelmagan o'quvchi muzlatiladi,
    # o'sha 3 kungi yoqlamasi bekor bo'ladi (ustoz oyligidan ham chiqadi)
    # va adminlarga "aloqaga chiqing" vazifasi tushadi.
    try:
        absent_ids = [m.student_id for m in payload.marks
                      if m.present is False and not m.remove]
        for sid in set(absent_ids):
            st = db.query(models.Student).get(sid)
            if not st or st.status != "active":
                continue
            last3 = (db.query(models.Attendance)
                     .join(models.Lesson,
                           models.Lesson.id == models.Attendance.lesson_id)
                     .filter(models.Attendance.student_id == sid,
                             models.Lesson.group_id == lesson.group_id)
                     .order_by(models.Lesson.date.desc(),
                               models.Lesson.id.desc())
                     .limit(roles.AUTO_FREEZE_ABSENCES).all())
            if len(last3) < roles.AUTO_FREEZE_ABSENCES:
                continue
            if any((a.present or 0) != 0 for a in last3):
                continue
            lesson_ids = [a.lesson_id for a in last3]
            for a in last3:
                db.delete(a)
            db.flush()
            for lid_ in lesson_ids:
                ls_ = db.query(models.Lesson).get(lid_)
                if ls_ and not db.query(models.Attendance).filter(
                        models.Attendance.lesson_id == lid_).count():
                    ls_.held = 0
            st.status = "frozen"
            st.frozen_until = None
            st.frozen_note = (f"{roles.AUTO_FREEZE_ABSENCES} darsga "
                              "ketma-ket kelmadi — avtomuzlatildi")
            _freeze_task(db, st, None, st.frozen_note)
            db.commit()
            audit.log(db, None, entity="student", action="auto_freeze",
                      entity_id=st.id, entity_label=st.full_name,
                      note=st.frozen_note, commit=True)
    except Exception:
        db.rollback()

    return {"ok": True, "saved": len(payload.marks), "activated": activated}

@router.get("/api/groups/{group_id}/grades", response_model=schemas.AttendanceGrid)
def grades_grid(
    group_id: int,
    year: int,
    month: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.ATTENDANCE_VIEW)),
):
    """Baholash jadvali - davomat bilan bir xil ko'rinish, lekin
    kataklarda 1-5 baho turadi."""
    _get_group_in_scope(db, group_id, user)
    # Davomatdagi bilan bir xil qoida: muzlatilgan o'quvchi baholash
    # jadvalida ham qator bo'lib chiqmasin — u darsga kelmaydi, baho
    # olmaydi (2026-08-09, davomatdagi bilan bir vaqtda tuzatildi).
    students = [s for s in _group_students(db, group_id)
               if s.status != "frozen"]
    lessons = _group_lessons_in_month(db, group_id, year, month)
    lesson_ids = [ls.id for ls in lessons]

    marks = {}
    if lesson_ids:
        rows = db.query(models.DailyGrade).filter(
            models.DailyGrade.lesson_id.in_(lesson_ids)
        ).all()
        marks = {f"{g.lesson_id}:{g.student_id}": g.score for g in rows}

    return schemas.AttendanceGrid(
        students=[schemas.GridStudent(id=s.id, full_name=s.full_name,
                                      status=s.status) for s in students],
        lessons=[schemas.GridLesson(id=ls.id, date=ls.date, held=ls.held or 0)
                 for ls in lessons],
        marks=marks,
    )

@router.put("/api/lessons/{lesson_id}/grades")
def save_grades(
    lesson_id: int,
    payload: schemas.GradeBulk,
    db: Session = Depends(get_db),
    # Akademik baho - faqat o'qituvchilar tarkibi. Kassir yoki sotuv
    # menejeri davomatni ko'rishi mumkin, lekin bahoga tegmaydi.
    user=Depends(require_role(*roles.GRADE_EDIT)),
):
    """Bir darsning baholarini saqlaydi. Har bir baho uchun coin AVTOMAT
    yoziladi: 5 baho = 5 coin. Baho o'zgarsa coin ham o'zgaradi, olib
    tashlansa coin qaytariladi."""
    lesson = db.query(models.Lesson).get(lesson_id)
    if not lesson:
        raise HTTPException(404, "Dars topilmadi")
    _get_group_in_scope(db, lesson.group_id, user)

    for m in payload.marks:
        if m.score is not None and not (
            roles.DAILY_GRADE_MIN <= m.score <= roles.DAILY_GRADE_MAX
        ):
            raise HTTPException(
                400,
                f"Baho {roles.DAILY_GRADE_MIN}-{roles.DAILY_GRADE_MAX} "
                "oralig'ida bo'lishi kerak",
            )

    _mark_lesson_held(db, lesson)

    # Davomatdagi bilan bir xil himoya: muzlatilgan o'quvchiga baho
    # qo'yilmaydi (2026-08-09).
    _frozen_ids = {
        sid for (sid,) in db.query(models.Student.id).filter(
            models.Student.group_id == lesson.group_id,
            models.Student.status == "frozen").all()
    }

    existing = {
        g.student_id: g
        for g in db.query(models.DailyGrade).filter(
            models.DailyGrade.lesson_id == lesson_id).all()
    }
    for m in payload.marks:
        if m.student_id in _frozen_ids:
            continue
        row = existing.get(m.student_id)
        if m.score is None:
            if row:
                _drop_coin_entry(db, "daily", row.id)
                db.delete(row)
            continue
        if row:
            row.score = m.score
        else:
            row = models.DailyGrade(
                lesson_id=lesson_id, student_id=m.student_id,
                score=m.score, created_by=user.full_name)
            db.add(row)
            db.flush()  # coin yozuvi uchun id kerak
        _sync_coin_entry(
            db, student_id=m.student_id, source="daily", ref_id=row.id,
            amount=m.score,
            note=f"Kunlik baho {lesson.date.isoformat()}",
            created_by=user.full_name,
        )
    db.commit()
    return {"ok": True, "saved": len(payload.marks)}

@router.get("/api/groups/{group_id}/exams", response_model=List[schemas.ExamOut])
def list_exams(
    group_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_ACCESS)),
):
    _get_group_in_scope(db, group_id, user)
    exams = (
        db.query(models.Exam)
        .filter(models.Exam.group_id == group_id)
        .order_by(models.Exam.date.desc(), models.Exam.id.desc())
        .all()
    )
    return [_exam_summary(db, e) for e in exams]

@router.post("/api/groups/{group_id}/exams", response_model=schemas.ExamOut)
def create_exam(
    group_id: int,
    payload: schemas.ExamCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_ACCESS)),
):
    _get_group_in_scope(db, group_id, user)
    if payload.kind not in roles.EXAM_KINDS:
        raise HTTPException(400, "Noto'g'ri test turi")
    if payload.kind == "unit":
        if not payload.unit_no or not (1 <= payload.unit_no <= roles.UNIT_COUNT):
            raise HTTPException(
                400, f"Unit raqami 1-{roles.UNIT_COUNT} oralig'ida bo'lishi kerak")
    if payload.kind != "mock" and (not payload.max_score or payload.max_score <= 0):
        raise HTTPException(400, "Maksimal ballni kiriting")

    # Testni TASDIQLASH huquqi bor odam (examiner, asoschi) yaratsa -
    # darrov tasdiqlangan bo'ladi: u baribir keyingi bosishda tasdiqlar
    # edi. Ustoz yaratsa - qoralama bo'lib turadi va examiner ko'radi.
    approver = user.role in tuple(roles.EXAM_APPROVE)
    exam = models.Exam(
        group_id=group_id, kind=payload.kind,
        unit_no=payload.unit_no if payload.kind == "unit" else None,
        title=payload.title, date=payload.date,
        max_score=payload.max_score if payload.kind != "mock" else None,
        status="approved" if approver else "draft",
        approved_by=user.full_name if approver else None,
        approved_at=date.today() if approver else None,
        created_by=user.full_name,
        examiner_id=user.id if user.role in (
            roles.EXAMINER, roles.HEAD_EXAMINER) else None,
    )
    db.add(exam)
    db.commit()
    db.refresh(exam)
    return _exam_summary(db, exam)

@router.get("/api/groups", response_model=List[schemas.GroupOut])
def list_groups(branch_id: Optional[int] = None,
                db: Session = Depends(get_db),
                user=Depends(get_current_user)):
    backfill_missing_ids(db, "group", models.Group)
    q = scope_to_branch(db.query(models.Group), models.Group, user,
                        branch_id)
    groups = q.order_by(models.Group.name).all()
    # STATISTIKA FAQAT FAOL O'QUVCHILAR BO'YICHA: sinovdagi va
    # muzlatilganlar songa qo'shilmaydi.
    counts = dict(
        db.query(models.Student.group_id, func.count(models.Student.id))
        .filter(models.Student.status == "active",
                models.Student.group_id.isnot(None))
        .group_by(models.Student.group_id).all())
    out = []
    for g in groups:
        item = schemas.GroupOut.model_validate(g)
        item.student_count = counts.get(g.id, 0)
        out.append(item)
    return out

@router.get("/api/groups/{group_id}", response_model=schemas.GroupOut)
def get_group(
    group_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)
):
    group = _get_group_in_scope(db, group_id, user)
    item = schemas.GroupOut.model_validate(group)
    item.student_count = db.query(models.Student).filter(
        models.Student.group_id == group.id,
        models.Student.status == "active").count()
    return item

def _validate_group_fields(payload):
    """Fan va daraja bir-biriga mos bo'lishi kerak - rus tilida
    "Step 1" degan daraja yo'q."""
    if payload.subject and payload.subject not in dict(roles.SUBJECTS):
        raise HTTPException(400, "Noto'g'ri fan")
    if payload.level and not roles.level_valid(payload.subject, payload.level):
        raise HTTPException(
            400, "Bu daraja tanlangan fanga tegishli emas")
    if payload.lesson_days:
        bad = [d for d in payload.lesson_days.split(",")
               if d and d not in roles.WEEKDAY_KEYS]
        if bad:
            raise HTTPException(400, "Noto'g'ri dars kuni")

def _resolve_group_rate(db: Session, data: dict):
    """Ustoz stavkasi DARAJADAN avtomat olinadi — guruh ochishda hech
    kim qo'lda kiritmaydi. Ataylab boshqa summa yuborilgan bo'lsa,
    istisno sifatida saqlanadi (rate_manual=1) va daraja o'zgarganda
    unga tegilmaydi."""
    tid = data.get("teacher_id")
    given = data.get("teacher_rate_per_student") or 0
    if not tid:
        return
    t = db.query(models.Teacher).get(tid)
    gm = _grade_map(db)
    grade_rate = 0
    if t and t.grade and t.grade in gm:
        grade_rate = gm[t.grade].rate_per_student or 0
    if not given or abs(given - grade_rate) < 1:
        data["teacher_rate_per_student"] = grade_rate
        data["rate_manual"] = 0
    else:
        data["rate_manual"] = 1

@router.post("/api/groups", response_model=schemas.GroupOut)
def create_group(
    payload: schemas.GroupCreate,
    force: bool = False,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.GROUP_MANAGE)),
):
    _validate_group_fields(payload)
    data = payload.model_dump()
    _raise_if_blocked(
        _check_schedule(db, group_id=None,
                        teacher_id=data.get("teacher_id"),
                        room_id=data.get("room_id"),
                        lesson_days=data.get("lesson_days"),
                        lesson_time=data.get("lesson_time")),
        force=force)
    _resolve_group_rate(db, data)
    group = models.Group(**data)
    db.add(group)
    db.commit()
    db.refresh(group)
    item = schemas.GroupOut.model_validate(group)
    item.student_count = 0
    return item

@router.put("/api/groups/{group_id}", response_model=schemas.GroupOut)
def update_group(
    group_id: int,
    payload: schemas.GroupUpdate,
    force: bool = False,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.GROUP_MANAGE)),
):
    group = db.query(models.Group).get(group_id)
    if not group:
        raise HTTPException(404, "Guruh topilmadi")

    fields = payload.model_dump(exclude_unset=True)
    # Fan va daraja mosligini TEKSHIRISHDAN OLDIN yangi qiymatlarni
    # eskisi bilan qo'shib chiqamiz: faqat darajani yuborganda ham
    # tekshiruv guruhning fanini bilishi kerak.
    merged = schemas.GroupCreate(
        name=fields.get("name", group.name),
        subject=fields.get("subject", group.subject),
        level=fields.get("level", group.level),
        lesson_days=fields.get("lesson_days", group.lesson_days),
    )
    _validate_group_fields(merged)

    # Ustoz, xona yoki vaqt o'zgarayotgan bo'lsa - to'qnashuvni
    # saqlashdan OLDIN tekshiramiz.
    if any(k in fields for k in
           ("teacher_id", "room_id", "lesson_days", "lesson_time")):
        _raise_if_blocked(
            _check_schedule(
                db, group_id=group.id,
                teacher_id=fields.get("teacher_id", group.teacher_id),
                room_id=fields.get("room_id", group.room_id),
                lesson_days=fields.get("lesson_days", group.lesson_days),
                lesson_time=fields.get("lesson_time", group.lesson_time)),
            force=force)

    # Ustoz yoki stavka o'zgarayotgan bo'lsa — darajadan qayta olinadi
    if "teacher_id" in fields or "teacher_rate_per_student" in fields:
        merged_rate = {
            "teacher_id": fields.get("teacher_id", group.teacher_id),
            "teacher_rate_per_student": fields.get(
                "teacher_rate_per_student",
                0 if "teacher_id" in fields
                else group.teacher_rate_per_student),
        }
        _resolve_group_rate(db, merged_rate)
        fields["teacher_rate_per_student"] = \
            merged_rate.get("teacher_rate_per_student", 0)
        if "rate_manual" in merged_rate:
            group.rate_manual = merged_rate["rate_manual"]

    for k, v in fields.items():
        setattr(group, k, v)
    db.commit()
    db.refresh(group)
    item = schemas.GroupOut.model_validate(group)
    item.student_count = db.query(models.Student).filter(
        models.Student.group_id == group.id,
        models.Student.status == "active").count()
    return item

@router.delete("/api/groups/{group_id}")
def delete_group(
    group_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.GROUP_MANAGE)),
):
    """Guruhni o'chirish — asoschi, filial rahbari, o'quv bo'limi rahbari.

    Himoya qoidalari:
      - ichida o'quvchi bo'lsa — avval ko'chirilsin/arxivlansin;
      - yoqlama tarixi bo'lsa — o'chirib BO'LMAYDI (bu ustoz oyligi va
        o'quvchi to'lovining hujjati);
      - bo'sh guruh (xato ochilgan) — darslari bilan birga tozalanadi."""
    group = db.query(models.Group).get(group_id)
    if not group:
        raise HTTPException(404, "Guruh topilmadi")
    if not _in_user_branches(db, user, group.branch_id, null_ok=True):
        raise HTTPException(403, "Bu guruh boshqa filialga tegishli")

    n_students = db.query(models.Student).filter(
        models.Student.group_id == group.id).count()
    if n_students:
        raise HTTPException(
            400, f"Guruhda {n_students} ta o'quvchi bor. Avval ularni "
                 "boshqa guruhga ko'chiring yoki arxivlang — keyin "
                 "guruhni o'chirasiz.")

    lesson_ids = [lid for (lid,) in db.query(models.Lesson.id).filter(
        models.Lesson.group_id == group.id).all()]
    if lesson_ids:
        n_att = db.query(models.Attendance).filter(
            models.Attendance.lesson_id.in_(lesson_ids)).count()
        if n_att:
            raise HTTPException(
                400, "Bu guruhda yoqlama tarixi bor — u ustoz oyligi va "
                     "to'lovlarning hujjati, o'chirib bo'lmaydi. Guruh "
                     "yakunlangan bo'lsa, tugash sanasini qo'yib qo'ying.")
        db.query(models.DailyGrade).filter(
            models.DailyGrade.lesson_id.in_(lesson_ids)).delete(
            synchronize_session=False)
        db.query(models.Lesson).filter(
            models.Lesson.id.in_(lesson_ids)).delete(
            synchronize_session=False)

    # Yordamchi bog'lanishlar ham tozalanadi
    try:
        db.query(models.SupportAssignment).filter(
            models.SupportAssignment.group_id == group.id).delete(
            synchronize_session=False)
    except Exception:
        pass

    audit.log(db, user, entity="group", action="delete",
              entity_id=group.id, entity_label=group.name,
              old_value=group.name, branch_id=group.branch_id)
    db.delete(group)
    db.commit()
    return {"ok": True}

@router.get("/api/groups/{group_id}/lessons", response_model=List[schemas.LessonOut])
def list_lessons(
    group_id: int,
    year: int,
    month: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    group = _get_group_in_scope(db, group_id, user)
    start, end = billing.month_bounds(year, month)
    _sync_scheduled_lessons(db, group, start, end)
    return (
        db.query(models.Lesson)
        .filter(models.Lesson.group_id == group.id,
                models.Lesson.date >= start, models.Lesson.date <= end)
        .order_by(models.Lesson.date)
        .all()
    )

@router.post("/api/groups/{group_id}/lessons", response_model=schemas.LessonOut)
def add_lesson(
    group_id: int,
    payload: schemas.LessonCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(*roles.TEACHING_STAFF)),
):
    group = _get_group_in_scope(db, group_id, user)
    # Guruh boshlanmagan kunga yoqlama qo'yib bo'lmaydi - aks holda
    # hisob-kitob ham, davomat ham noto'g'ri chiqadi.
    if group.start_date and payload.date < group.start_date:
        raise HTTPException(
            400,
            f"Guruh {group.start_date.isoformat()} da boshlangan - "
            "undan oldingi kunga yoqlama qo'yib bo'lmaydi")
    existing = (
        db.query(models.Lesson)
        .filter(models.Lesson.group_id == group.id, models.Lesson.date == payload.date)
        .first()
    )
    if existing:
        # Jadval bo'yicha avtomat yaratilgan bo'sh kun bo'lsa - xato
        # bermaymiz, shunchaki "o'tildi" deb belgilaymiz.
        if not existing.held:
            existing.held = 1
            if payload.teacher_id is not None:
                existing.teacher_id = payload.teacher_id
            if payload.note:
                existing.note = payload.note
            db.commit()
            db.refresh(existing)
            return existing
        raise HTTPException(400, "Bu kun uchun allaqachon dars (yoqlama) belgilangan")

    lesson = models.Lesson(
        group_id=group.id,
        teacher_id=payload.teacher_id if payload.teacher_id is not None else group.teacher_id,
        date=payload.date,
        note=payload.note,
        created_by=user.full_name,
    )
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    return lesson

@router.delete("/api/lessons/{lesson_id}")
def delete_lesson(
    lesson_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(*roles.TEACHING_STAFF)),
):
    lesson = db.query(models.Lesson).get(lesson_id)
    if not lesson:
        raise HTTPException(404, "Dars topilmadi")
    _get_group_in_scope(db, lesson.group_id, user)  # branch guard

    # Darsga bog'langan davomat va baholarni ham olib tashlaymiz, aks holda
    # ular "yetim" qolib, bazada bog'liqlik xatosi chiqadi. Baho o'chgani
    # uchun u bergan coin ham qaytariladi.
    for gr in db.query(models.DailyGrade).filter(
        models.DailyGrade.lesson_id == lesson_id
    ).all():
        _drop_coin_entry(db, "daily", gr.id)
        db.delete(gr)
    db.query(models.Attendance).filter(
        models.Attendance.lesson_id == lesson_id
    ).delete(synchronize_session=False)

    db.delete(lesson)
    db.commit()
    return {"ok": True}

@router.post("/api/groups/{group_id}/billing/run", response_model=schemas.BillingRunResult)
def run_billing(
    group_id: int,
    year: int,
    month: int,
    commit: bool = False,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(*roles.FINANCE_ACCESS)),
):
    group = _get_group_in_scope(db, group_id, user)
    period = f"{year:04d}-{month:02d}"
    charges = billing.compute_student_charges(db, group, year, month)

    results = []
    for c in charges:
        created = False
        if commit and not c["already_charged"] and c["amount"] > 0 \
                and not _charge_skipped(db, c["student_id"], period):
            payment = models.Payment(
                student_id=c["student_id"],
                amount=-abs(c["amount"]),
                kind="charge",
                note=f"{group.name} - {period} oyi uchun {c['billable_lessons']} dars",
                created_by=user.full_name,
                period=period,
            )
            db.add(payment)
            created = True
        results.append(
            schemas.StudentChargeResult(
                student_id=c["student_id"],
                student_name=c["student_name"],
                billable_lessons=c["billable_lessons"],
                amount=c["amount"],
                already_charged=c["already_charged"],
                created=created,
            )
        )
    if commit:
        db.commit()

    return schemas.BillingRunResult(
        period=period,
        held_lessons=billing.held_lessons_count(db, group.id, year, month),
        committed=commit,
        results=results,
    )

@router.post("/api/groups/{group_id}/payroll/run", response_model=schemas.PayrollRunResult)
def run_payroll(
    group_id: int,
    year: int,
    month: int,
    commit: bool = False,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(*roles.FINANCE_ACCESS)),
):
    group = _get_group_in_scope(db, group_id, user)
    period = f"{year:04d}-{month:02d}"
    computed = billing.compute_teacher_payroll(db, group, year, month)

    results = []
    for c in computed:
        payout = None
        if commit:
            payout = (
                db.query(models.TeacherPayout)
                .filter(
                    models.TeacherPayout.teacher_id == c["teacher_id"],
                    models.TeacherPayout.group_id == group.id,
                    models.TeacherPayout.period == period,
                )
                .first()
            )
            if not payout:
                payout = models.TeacherPayout(
                    teacher_id=c["teacher_id"], group_id=group.id, period=period
                )
                db.add(payout)
            payout.student_count = c["student_count"]
            payout.held_lessons = c["held_lessons"]
            payout.taught_lessons = c["taught_lessons"]
            payout.amount = c["amount"]
            db.flush()

        results.append(
            schemas.TeacherPayoutOut(
                id=payout.id if payout else None,
                teacher_id=c["teacher_id"],
                group_id=group.id,
                period=period,
                student_count=c["student_count"],
                held_lessons=c["held_lessons"],
                taught_lessons=c["taught_lessons"],
                amount=c["amount"],
                paid=bool(payout.paid) if payout else False,
            )
        )
    if commit:
        db.commit()

    return schemas.PayrollRunResult(period=period, committed=commit, results=results)

def _xp_for_attendance(db: Session, lesson: models.Lesson,
                       by_user: models.User | None = None) -> dict:
    """Yoqlama qo'yilganda: kelgani uchun XP va streak."""
    out = {"awarded": 0, "students": 0}
    rows = (db.query(models.Attendance)
            .filter(models.Attendance.lesson_id == lesson.id).all())
    for a in rows:
        if not a.present:
            _break_streak(db, a.student_id, "attendance")
            continue
        r = award_xp(db, student_id=a.student_id,
                     event_code="LESSON_PRESENT", by_user=by_user,
                     lesson_id=lesson.id, source_type="lesson",
                     source_id=lesson.id, on=lesson.date,
                     idempotency_key=f"LESSON_PRESENT:{lesson.id}:{a.student_id}")
        if r.get("ok"):
            out["awarded"] += r["amount"]
            out["students"] += 1
        _bump_streak(db, a.student_id, "attendance", lesson.date,
                     by_user=by_user)
    db.commit()
    return out

def _bump_streak(db: Session, student_id: int, kind: str, on: date,
                 by_user: models.User | None = None) -> int:
    """Ketma-ketlikni oshiradi va bosqich bonusini BIR MARTA beradi."""
    st = (db.query(models.XpStreak)
          .filter(models.XpStreak.student_id == student_id,
                  models.XpStreak.kind == kind).first())
    if not st:
        st = models.XpStreak(student_id=student_id, kind=kind,
                             current=0, longest=0)
        db.add(st)
    if st.last_event_date == on:
        return st.current                # bir kunda ikki marta sanamaymiz
    st.current = (st.current or 0) + 1
    st.longest = max(st.longest or 0, st.current)
    st.last_event_date = on
    db.flush()

    table = (roles.ATTENDANCE_STREAKS if kind == "attendance"
             else roles.HOMEWORK_STREAKS if kind == "homework" else [])
    for need, code in table:
        if st.current != need:
            continue
        seen = (db.query(models.XpStreakMilestone)
                .filter(models.XpStreakMilestone.student_id == student_id,
                        models.XpStreakMilestone.kind == kind,
                        models.XpStreakMilestone.milestone == need).first())
        if seen:
            break
        db.add(models.XpStreakMilestone(
            student_id=student_id, kind=kind, milestone=need))
        award_xp(db, student_id=student_id, event_code=code,
                 by_user=by_user, source_type="streak", on=on,
                 reason=f"Ketma-ket {need} ta",
                 idempotency_key=f"{code}:{student_id}")
        break
    return st.current

def _break_streak(db: Session, student_id: int, kind: str) -> None:
    """Sababsiz qoldirilsa ketma-ketlik uziladi. XP KAMAYTIRILMAYDI —
    shunchaki berilmaydi."""
    st = (db.query(models.XpStreak)
          .filter(models.XpStreak.student_id == student_id,
                  models.XpStreak.kind == kind).first())
    if st and st.current:
        st.current = 0

@router.get("/api/reschedules")
def reschedules_list(status: str | None = None,
                     db: Session = Depends(get_db),
                     user=Depends(require_role(*roles.RESCHEDULE_APPROVE))):
    """Rahbariyat uchun: kim qancha surgan va nimani tasdiqlash kerak."""
    q = db.query(models.LessonReschedule)
    if status:
        q = q.filter(models.LessonReschedule.status == status)
    rows = q.order_by(models.LessonReschedule.id.desc()).limit(200).all()
    out = [_resch_out(db, r) for r in rows]
    if user.role == roles.BRANCH_MANAGER and user.branch_id:
        gids = {g.id for g in db.query(models.Group).filter(
            _branch_in(db, user, models.Group.branch_id)).all()}
        out = [r for r in out if r["group_id"] in gids]

    # Ustoz kesimi — kim ko'p suryapti
    by_teacher: dict = {}
    for r in out:
        if r["status"] not in roles.RESCHEDULE_DONE:
            continue
        by_teacher[r["teacher"]] = by_teacher.get(r["teacher"], 0) + 1
    return {
        "rows": out,
        "pending": sum(1 for r in out if r["status"] == "pending"),
        "by_teacher": sorted(
            [{"teacher": k, "count": v} for k, v in by_teacher.items()],
            key=lambda x: -x["count"]),
        "statuses": [{"key": k, "label": l, "tone": t}
                     for k, l, t in roles.RESCHEDULE_STATUSES],
        "hint": ("Ko'p surish o'quvchining qiziqishini tushiradi. "
                 "Ustoz kesimida qatorlar ko'payib borsa — bu "
                 "suhbatlashadigan signal."),
    }

@router.post("/api/reschedules/{rid}/decide")
def reschedule_decide(rid: int, payload: schemas.RescheduleDecision,
                      db: Session = Depends(get_db),
                      user=Depends(require_role(*roles.RESCHEDULE_APPROVE))):
    r = db.query(models.LessonReschedule).get(rid)
    if not r:
        raise HTTPException(404, "Topilmadi")
    if r.status != "pending":
        raise HTTPException(400, "Bu so'rov bo'yicha qaror qabul qilingan")
    if payload.decision not in ("approved", "rejected"):
        raise HTTPException(400, "Noma'lum qaror")
    if payload.decision == "rejected" and not (payload.note or "").strip():
        raise HTTPException(400, "Rad etish sababini yozing")

    r.status = payload.decision
    r.decided_by = user.id
    r.decided_at = datetime.utcnow()
    r.decision_note = payload.note
    if payload.decision == "approved":
        _apply_reschedule(db, r)
    db.commit()
    audit.log(db, user, entity="lesson_reschedule", action=payload.decision,
              entity_id=rid, note=payload.note, commit=True)
    return _resch_out(db, r)

def _xp_for_homework(db: Session, lesson: models.Lesson,
                     by_user: models.User | None = None) -> None:
    """Uy vazifasi belgilanganda XP va ketma-ketlik.

    Qoidalar (HOMEWORK_COMPLETE, HOMEWORK_PARTIAL va streaklar)
    allaqachon katalogda bor edi — bu yerda ular ishga tushadi."""
    rows = db.query(models.Attendance).filter(
        models.Attendance.lesson_id == lesson.id,
        models.Attendance.homework.isnot(None)).all()
    for a in rows:
        if a.homework == 1:
            award_xp(db, student_id=a.student_id,
                     event_code="HOMEWORK_COMPLETE", by_user=by_user,
                     source_type="lesson", source_id=lesson.id,
                     on=lesson.date, reason="Uy vazifasi bajarildi",
                     idempotency_key=f"HW:{lesson.id}:{a.student_id}")
            _bump_streak(db, a.student_id, "homework", lesson.date,
                         by_user=by_user)
        elif a.homework == 2:
            award_xp(db, student_id=a.student_id,
                     event_code="HOMEWORK_PARTIAL", by_user=by_user,
                     source_type="lesson", source_id=lesson.id,
                     on=lesson.date, reason="Uy vazifasi qisman",
                     idempotency_key=f"HWP:{lesson.id}:{a.student_id}")
        else:
            _break_streak(db, a.student_id, "homework")
    db.commit()

def _reschedule_box(db: Session, group_id: int, user: models.User,
                    for_month: date | None = None) -> dict:
    """Sana menyusi uchun: kim ko'chira oladi, qancha imkon qolgan va
    qaysi darslar allaqachon ko'chirilgan."""
    g = db.query(models.Group).get(group_id)
    t = _teacher_of_user(db, user)
    mine = bool(g and t and g.teacher_id == t.id)
    manager = user.role in tuple(roles.RESCHEDULE_APPROVE)

    rows = db.query(models.LessonReschedule).filter(
        models.LessonReschedule.group_id == group_id,
        models.LessonReschedule.status.in_(
            roles.RESCHEDULE_DONE + ["pending"])).all()
    _status_labels = dict(
        (k, l) for k, l, _t in roles.RESCHEDULE_STATUSES)
    by_date = {}
    # TESKARI XARITA: yangi (to_date) sana ustunida "bu dars boshqa
    # kundan ko'chirilgan" belgisi chiqishi uchun (2026-08-09,
    # Jahongir so'radi — ko'chirilgan sana ustida qaysi kundan
    # ko'chirilgani bilinib turishi kerak). Faqat HAQIQATDA
    # qo'llangan (RESCHEDULE_DONE) ko'chirishlar kiradi — "pending"
    # hali biror darsni jismonan ko'chirmagan (_apply_reschedule hali
    # chaqirilmagan), demak to_date'da hali ko'rsatadigan dars yo'q.
    moved_in = {}
    for r in rows:
        by_date[r.from_date.isoformat()] = {
            "id": r.id, "status": r.status,
            "status_label": _status_labels.get(r.status, r.status),
            "to_date": r.to_date.isoformat(),
        }
        if r.status in roles.RESCHEDULE_DONE:
            moved_in[r.to_date.isoformat()] = {
                "id": r.id, "status": r.status,
                "status_label": _status_labels.get(r.status, r.status),
                "from_date": r.from_date.isoformat(),
            }

    box = {
        "can": mine or manager,
        "manager": manager,
        "as_manager": manager and not mine,
        "moved": by_date,
        "moved_in": moved_in,
        "reasons": [{"key": k, "label": l}
                    for k, l in roles.RESCHEDULE_REASONS],
        "min_notice_days": roles.RESCHEDULE_MIN_NOTICE_DAYS,
        "max_shift_days": roles.RESCHEDULE_MAX_SHIFT_DAYS,
        "cannot_cancel": ("Darsni bekor qilib bo'lmaydi — faqat boshqa "
                          "kunga ko'chiriladi."),
        "quota": None,
    }
    if mine:
        # Kvota KO'RILAYOTGAN oy bo'yicha: ustoz avgust jadvalini
        # ochganda avgustning imkonini ko'rishi kerak. Kvota dars oyi
        # bo'yicha sanaladi, shuning uchun bu ikkalasi mos keladi.
        m = for_month or roles.local_today()
        box["quota"] = _reschedule_usage(db, t.id, m)
        box["month"] = m.replace(day=1).isoformat()
        box["hint"] = (
            f"Oyiga {roles.RESCHEDULE_PER_MONTH} marta avtomat ruxsat "
            f"beriladi. Chegaradan oshsa so'rov tasdiqqa ketadi. "
            f"Dars ko'p surilsa o'quvchining qiziqishi tushadi.")
    elif manager:
        box["hint"] = ("Rahbariyat ko'chirishi kvotaga kirmaydi va "
                       "darrov kuchga kiradi.")
    return box

@router.post("/api/groups/{gid}/reschedule")
def group_reschedule(gid: int, payload: schemas.GroupRescheduleIn,
                     db: Session = Depends(get_db),
                     user=Depends(require_role(*roles.TEACHING_ACCESS))):
    """Jadvaldagi sana menyusidan dars ko'chirish.

    Ustoz o'z guruhida kvota bilan, rahbariyat kvotasiz ko'chiradi.
    Ikkalasi ham bitta yozuvga tushadi — kim ko'chirgani ko'rinib
    turadi va tarix bir joyda qoladi.
    """
    g = _get_group_in_scope(db, gid, user)
    t = _teacher_of_user(db, user)
    mine = bool(t and g.teacher_id == t.id)
    manager = user.role in tuple(roles.RESCHEDULE_APPROVE)
    if not (mine or manager):
        raise HTTPException(403, "Bu guruhning darsini ko'chira olmaysiz")

    today = roles.local_today()
    # Rahbariyat/HR menejer darsni ISTALGAN sanaga ko'chira oladi —
    # bugun, kelajak, HATTO o'tib ketgan sanaga ham (masalan, oy
    # oxirini qayta taqsimlash yoki orqada qolgan jadvalni tuzatish
    # uchun, 2026-08-09 so'ralgan). SHU BILAN BIRGA manba darsning
    # o'zi (from_date) ham o'tib ketgan bo'lishi mumkin — masalan,
    # bir kun o'z vaqtida ko'chirilmay qolgan bo'lsa, HR endi uni
    # istalgan kunga surib, keyin o'sha yerda yo'qlama qo'ya oladi
    # (2026-08-09, aynan shu holat so'ralgan). Haqiqiy to'siqlar shu
    # funksiyaning davomida qoladi: shift_days chegarasi (pastda,
    # ikkala tomonga ham amal qiladi) va manba darsning "held"
    # bo'lmasligi — bular ish haqi hisobini himoya qiladi,
    # rahbariyatga ham tegishli. Oddiy ustoz uchun talab o'zgarmadi:
    # qat'iy kelajakdagi sana, manba ham o'tmish bo'lmasligi kerak.
    if not manager and payload.to_date <= today:
        raise HTTPException(400, "Yangi sana kelajakda bo'lishi kerak")
    if payload.to_date == payload.from_date:
        raise HTTPException(400, "Yangi sana eskisidan farq qilishi kerak")
    if not manager and payload.from_date < today:
        raise HTTPException(400, "O'tib ketgan darsni ko'chirib bo'lmaydi")

    ls = db.query(models.Lesson).filter(
        models.Lesson.group_id == gid,
        models.Lesson.date == payload.from_date).first()
    if ls and ls.held:
        raise HTTPException(
            400, "O'tilgan darsni ko'chirib bo'lmaydi — u tarix va "
                 "ish haqi asosi")

    dup = db.query(models.LessonReschedule).filter(
        models.LessonReschedule.group_id == gid,
        models.LessonReschedule.from_date == payload.from_date,
        models.LessonReschedule.status.in_(
            roles.RESCHEDULE_DONE + ["pending"])).first()
    if dup:
        raise HTTPException(400, "Bu dars allaqachon ko'chirilgan yoki "
                                 "so'rov yuborilgan")

    shift = abs((payload.to_date - payload.from_date).days)
    if shift > roles.RESCHEDULE_MAX_SHIFT_DAYS:
        raise HTTPException(
            400, f"Dars ko'pi bilan {roles.RESCHEDULE_MAX_SHIFT_DAYS} "
                 f"kunga ko'chiriladi")

    # Ustoz uchun: ogohlantirish muddati va kvota. Rahbariyatga bu
    # cheklovlar qo'llanmaydi — ular allaqachon tasdiqlovchi.
    within_quota = True
    if mine and not manager:
        notice = (payload.from_date - today).days
        if notice < roles.RESCHEDULE_MIN_NOTICE_DAYS:
            raise HTTPException(
                400, f"Kamida {roles.RESCHEDULE_MIN_NOTICE_DAYS} kun "
                     f"oldin so'ralishi kerak — o'quvchi va ota-onani "
                     f"ogohlantirishga vaqt kerak")
        within_quota = _reschedule_usage(
            db, t.id, payload.from_date)["auto_ok"]

    r = models.LessonReschedule(
        group_id=gid, teacher_id=g.teacher_id or (t.id if t else None),
        from_date=payload.from_date, to_date=payload.to_date,
        from_time=g.lesson_time, to_time=g.lesson_time,
        reason=payload.reason, note=payload.note,
        status="approved" if (manager and not mine) else
               ("auto" if within_quota else "pending"),
        auto_approved=1 if within_quota and not manager else 0,
        requested_by=user.id)
    if manager and not mine:
        r.decided_by = user.id
        r.decided_at = datetime.utcnow()
    db.add(r); db.commit(); db.refresh(r)

    applied = r.status in roles.RESCHEDULE_DONE
    if applied:
        _apply_reschedule(db, r)
        db.commit()
    else:
        # Tasdiq kerak bo'lsa — o'quv bo'limiga vazifa bo'lib boradi
        _hr_task(db, title=f"Dars ko'chirish so'rovi #{r.id}",
                 body=(f"{t.full_name if t else '—'} — {g.name}. "
                       f"{payload.from_date} → {payload.to_date}. "
                       f"Kvota tugagan (oyiga "
                       f"{roles.RESCHEDULE_PER_MONTH} marta), shuning "
                       f"uchun tasdiq kerak."),
                 to_roles=roles.RESCHEDULE_APPROVE,
                 branch_id=g.branch_id, days=1, priority="high")
        db.commit()

    audit.log(db, user, entity="lesson_reschedule", action="create",
              entity_id=r.id, entity_label=g.name,
              new_value=f"{payload.from_date} → {payload.to_date}",
              note=("rahbariyat" if manager and not mine else
                    ("avtomat" if within_quota else "tasdiq kutmoqda")),
              commit=True)

    return {
        "ok": True,
        "id": r.id,
        "status": r.status,
        "applied": applied,
        "message": ("Dars ko'chirildi." if applied else
                    "Kvotadan oshdi — so'rov o'quv bo'limiga yuborildi."),
    }

@router.put("/api/lessons/{lesson_id}/homework")
def set_homework(lesson_id: int, payload: schemas.HomeworkIn,
                 db: Session = Depends(get_db),
                 user=Depends(require_role(*roles.TEACHING_ACCESS))):
    """Uy vazifasi belgisi — yoqlamadan ALOHIDA qo'yiladi.

    Qoida: faqat yoqlama qilingan darsga qo'yiladi (yoqlamasiz dars
    pulga kirmaydi, vazifasi ham bo'lmaydi). O'tgan darslarga qo'yish
    MUMKIN — vazifa keyingi darsda tekshiriladi. Kelajakka bo'lmaydi."""
    lesson = db.query(models.Lesson).get(lesson_id)
    if not lesson:
        raise HTTPException(404, "Dars topilmadi")
    _get_group_in_scope(db, lesson.group_id, user)
    if lesson.date > roles.local_today():
        raise HTTPException(400, "Bo'lib o'tmagan darsga vazifa qo'yilmaydi")
    if payload.homework is not None and payload.homework not in (0, 1, 2):
        raise HTTPException(400, "Vazifa belgisi: 0, 1 yoki 2")
    row = db.query(models.Attendance).filter(
        models.Attendance.lesson_id == lesson_id,
        models.Attendance.student_id == payload.student_id).first()
    if not row:
        raise HTTPException(
            400, "Avval yoqlama belgilang — yoqlamasiz darsga vazifa "
                 "qo'yilmaydi")
    row.homework = payload.homework
    db.commit()
    return {"ok": True}

@router.get("/api/groups/{group_id}/history")
def group_history(group_id: int, db: Session = Depends(get_db),
                  user=Depends(require_role(*roles.TEACHING_ACCESS))):
    """Guruh tarixi: qo'shilishlar, ko'chirilgan darslar,
    o'rinbosarliklar, imtihonlar va boshqa o'zgarishlar."""
    g = _get_group_in_scope(db, group_id, user)
    events = []
    for s in db.query(models.Student).filter(
            models.Student.group_id == group_id).all():
        if s.enrolled_date:
            events.append({"date": s.enrolled_date.isoformat(),
                           "kind": "join", "icon": "user",
                           "text": f"{s.full_name} guruhga qo'shildi"})
        if s.status == "frozen":
            events.append({"date": (s.frozen_until or
                                    roles.local_today()).isoformat(),
                           "kind": "freeze", "icon": "snow",
                           "text": f"{s.full_name} muzlatilgan"
                           + (f" (qaytishi {s.frozen_until.isoformat()})"
                              if s.frozen_until else "")})
    for r in db.query(models.LessonReschedule).filter(
            models.LessonReschedule.group_id == group_id).all():
        events.append({
            "date": (r.from_date or roles.local_today()).isoformat(),
            "kind": "move", "icon": "move",
            "text": f"Dars ko'chirildi: {r.from_date} → {r.to_date}"
                    + (f" ({r.status})" if r.status else "")})
    for sub in db.query(models.Substitution).filter(
            models.Substitution.group_id == group_id).all():
        t = db.query(models.Teacher).get(sub.substitute_teacher_id) \
            if sub.substitute_teacher_id else None
        events.append({
            "date": sub.lesson_date.isoformat() if sub.lesson_date
            else roles.local_today().isoformat(),
            "kind": "sub", "icon": "swap",
            "text": "O'rinbosarlik: "
                    + (t.full_name if t else "ochiq taklif")
                    + f" ({sub.status})"})
    for e in db.query(models.Exam).filter(
            models.Exam.group_id == group_id).all():
        events.append({
            "date": e.date.isoformat(), "kind": "exam", "icon": "exam",
            "text": (e.title or roles.EXAM_KIND_LABELS.get(e.kind, e.kind))
                    + f" — {e.status}"})
    for a in (db.query(models.AuditLog)
              .filter(models.AuditLog.entity == "group",
                      models.AuditLog.entity_id == group_id)
              .order_by(models.AuditLog.id.desc()).limit(40).all()):
        events.append({
            "date": a.created_at.date().isoformat() if a.created_at
            else roles.local_today().isoformat(),
            "kind": "audit", "icon": "edit",
            "text": f"{a.action}: {a.field or ''} "
                    f"{a.old_value or ''} → {a.new_value or ''}".strip()
                    + (f" ({a.user_name})" if a.user_name else "")})
    events.sort(key=lambda e: e["date"], reverse=True)
    return {"group": g.name, "events": events[:120]}

@router.get("/api/groups/{group_id}/notes")
def group_notes(group_id: int, db: Session = Depends(get_db),
                user=Depends(require_role(*roles.TEACHING_ACCESS))):
    """Izoh va chegirma: guruh o'quvchilarining izohi va amaldagi
    chegirmalari. Balans YO'Q — bu pul sahifasi emas."""
    _get_group_in_scope(db, group_id, user)
    rows = []
    _dt_defs = getattr(roles, "DISCOUNT_TYPES", []) or []
    dlbl = {t[0]: t[1] for t in _dt_defs}
    for s in (db.query(models.Student)
              .filter(models.Student.group_id == group_id,
                      models.Student.status != "archived")
              .order_by(models.Student.full_name).all()):
        ds = (db.query(models.Discount)
              .filter(models.Discount.student_id == s.id,
                      models.Discount.status.in_(("approved", "active")))
              .all())
        rows.append({
            "id": s.id, "name": s.full_name, "status": s.status,
            "note": s.note,
            "address": s.address, "school": s.school,
            "school_grade": s.school_grade,
            "discounts": [{
                "kind": dlbl.get(d.kind, d.kind),
                "percent": d.percent, "amount": d.amount,
                "reason": d.reason,
                "until": d.end_date.isoformat() if d.end_date else None,
            } for d in ds],
        })
    return {"students": rows}

