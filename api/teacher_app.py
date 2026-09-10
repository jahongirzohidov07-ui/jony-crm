"""JONY TEACHER — ustozning O'Z ilovasi (2026-08-10).

Jahongir so'radi: "shunaqa appni ustozlar uchun ham alohida qilib ber,
ular yo'qlama qo'yishi va ularda bor barcha funksiyalar chiqsin."

NEGA ALOHIDA ROUTER: xodimlar paneli (Layout.tsx) kompyuter uchun
qurilgan — ustoz esa darsga telefon bilan kiradi va kuniga bir marta,
tez, YO'QLAMA qo'yadi. Shuning uchun bu yerda ustozning KUNLIK ishi
uchun maxsus, yig'ilgan (aggregated) yo'llar bor: bitta so'rov bilan
"bugun qaysi darslarim bor, kim keldi, kim baholanmagan" degan javob
keladi. Qolgan funksiyalar (kitob/imtihon buyurtma, oylik, natijalar)
ALLAQACHON mavjud yo'llardan ishlaydi — ular qayta yozilmadi,
ilovada shunchaki ochiladi.

YO'QLAMA yozish esa ATAYLAB shu yerda TAKRORLANMAYDI: mavjud
PUT /api/lessons/{id}/attendance ishlatiladi (u yerda sana qoidalari,
muzlatilgan o'quvchi himoyasi, avtomat XP, Telegram xabarnomalari va
oylik hisobi bor). Ikkinchi nusxa yozilsa — shularning bittasi
esdan chiqib, ustoz oyligi noto'g'ri hisoblanib ketishi mumkin edi.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date, datetime, timedelta

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

import billing
import models
import roles
from auth import require_role
from database import get_db
from common import *  # noqa: F401,F403 - shared helpers/state

router = APIRouter()

# Ustoz va support teacher — ikkalasi ham dars o'tadi va yo'qlama
# qo'yadi, shuning uchun ikkalasiga ham ochiq.
TEACHER_APP_ROLES = (roles.TEACHER, roles.SUPPORT_TEACHER)


def _me_teacher(db: Session, user: models.User) -> models.Teacher:
    t = _teacher_of_user(db, user)
    if not t:
        raise HTTPException(
            403, "Bu bo'lim faqat ustozlar uchun. Hisobingiz ustoz "
                 "kartasiga bog'lanmagan — HR ga murojaat qiling.")
    return t


def _my_group_ids(db: Session, user: models.User, t: models.Teacher) -> list:
    return [g.id for g in _cabinet_groups(db, user, t)]


def _lesson_card(db: Session, ls: models.Lesson, g: models.Group,
                 slots=None) -> dict:
    """Bitta dars kartasi: nechta o'quvchi, nechtasi belgilangan.

    VAQT (2026-09-10, Jahongir: "haliyam supportlarni oz darsi vaqti
    emas asosiy dars vaqti korinyabdi"): support uchun kartada
    GURUHNING asosiy dars vaqti emas, support menejer biriktirgan
    seans vaqti turadi. `slots` — common.support_slot_map() natijasi;
    oddiy ustozda None bo'ladi va hech narsa o'zgarmaydi."""
    students = [s for s in (g.students or [])
                if s.status in ("active", "trial")]
    marked = (db.query(func.count(models.Attendance.id))
              .filter(models.Attendance.lesson_id == ls.id).scalar() or 0)
    graded = (db.query(func.count(models.DailyGrade.id))
              .filter(models.DailyGrade.lesson_id == ls.id).scalar() or 0)
    _days, _time, _src, _note = group_time_for(slots, g)
    return {
        "lesson_id": ls.id,
        "group_id": g.id,
        "group": g.name,
        "level": getattr(g, "level", None),
        "time": _time,
        "time_source": _src,
        "time_note": _note,
        "date": ls.date.isoformat(),
        "held": bool(ls.held),
        "students": len(students),
        "marked": int(marked),
        "graded": int(graded),
        "done": int(marked) >= len(students) and len(students) > 0,
    }


@router.get("/api/teacher/today")
def teacher_today(day: str | None = None,
                  db: Session = Depends(get_db),
                  user=Depends(require_role(*TEACHER_APP_ROLES))):
    """BUGUNGI ish: darslar ro'yxati + nima qilinmagani.

    Ustoz ilovani ochishi bilan ko'radigan yagona muhim narsa —
    "bugun nima qilishim kerak". Shuning uchun bitta so'rovda
    hammasi keladi (telefonda har bo'lim uchun alohida so'rov
    yubormaslik kerak — sekin internetda seziladi)."""
    t = _me_teacher(db, user)
    on = date.fromisoformat(day) if day else roles.local_today()
    gids = _my_group_ids(db, user, t)
    slots = support_slot_map(db, user)
    if not gids:
        return {"date": on.isoformat(), "lessons": [], "groups": 0,
                "students": 0, "pending": 0,
                "hint": "Sizga hali guruh biriktirilmagan."}

    rows = (db.query(models.Lesson, models.Group)
            .join(models.Group, models.Lesson.group_id == models.Group.id)
            .filter(models.Lesson.group_id.in_(gids),
                    models.Lesson.date == on)
            .order_by(models.Group.lesson_time, models.Group.name).all())
    lessons = [_lesson_card(db, ls, g, slots) for ls, g in rows]

    # Oxirgi 7 kunda yo'qlamasi qo'yilmagan darslar — ustoz esidan
    # chiqargan bo'lsa ko'rinib tursin (oylik shundan hisoblanadi).
    back = on - timedelta(days=7)
    old_rows = (db.query(models.Lesson, models.Group)
                .join(models.Group,
                      models.Lesson.group_id == models.Group.id)
                .filter(models.Lesson.group_id.in_(gids),
                        models.Lesson.date >= back,
                        models.Lesson.date < on,
                        models.Lesson.held == 0)
                .order_by(models.Lesson.date.desc()).limit(20).all())
    missed = [_lesson_card(db, ls, g, slots) for ls, g in old_rows]

    total_students = (db.query(func.count(models.Student.id))
                      .filter(models.Student.group_id.in_(gids),
                              models.Student.status.in_(("active", "trial")))
                      .scalar() or 0)
    return {
        "date": on.isoformat(),
        "teacher": t.full_name,
        "lessons": lessons,
        "missed": missed,
        "groups": len(gids),
        "students": int(total_students),
        "pending": sum(1 for l in lessons if not l["done"]),
    }


@router.get("/api/teacher/lesson/{lesson_id}")
def teacher_lesson(lesson_id: int,
                   db: Session = Depends(get_db),
                   user=Depends(require_role(*TEACHER_APP_ROLES))):
    """Bitta darsning yo'qlama ekrani uchun hamma narsa.

    Muzlatilgan o'quvchi ro'yxatga UMUMAN kirmaydi (xodimlar
    panelidagi qoida bilan bir xil — ular uchun dars hisoblanmaydi
    va oylikka kirmaydi)."""
    t = _me_teacher(db, user)
    ls = db.query(models.Lesson).get(lesson_id)
    if not ls:
        raise HTTPException(404, "Dars topilmadi")
    if ls.group_id not in _my_group_ids(db, user, t):
        raise HTTPException(403, "Bu dars sizning guruhingiz emas")
    g = db.query(models.Group).get(ls.group_id)

    att = {a.student_id: a for a in db.query(models.Attendance)
           .filter(models.Attendance.lesson_id == ls.id).all()}
    grades = {x.student_id: x for x in db.query(models.DailyGrade)
              .filter(models.DailyGrade.lesson_id == ls.id).all()}

    students = sorted(
        [s for s in (g.students or [])
         if s.status in ("active", "trial")],
        key=lambda s: s.full_name)

    today = roles.local_today()
    editable = ls.date <= today
    why = None
    if ls.date > today:
        why = "Hali bo'lib o'tmagan darsga yo'qlama qo'yilmaydi"
    elif ls.date < today and user.role not in tuple(roles.PAST_ATTENDANCE):
        editable = False
        why = ("O'tib ketgan kunning yo'qlamasini faqat rahbariyat "
               "o'zgartira oladi")

    return {
        "lesson_id": ls.id,
        "group_id": g.id,
        "group": g.name,
        "level": getattr(g, "level", None),
        "date": ls.date.isoformat(),
        # Support uchun bu yerda ham o'z seans vaqti (2026-09-10)
        "time": group_time_for(support_slot_map(db, user), g)[1],
        "editable": editable,
        "readonly_reason": why,
        "students": [{
            "id": s.id,
            "full_name": s.full_name,
            "status": s.status,
            # present: 1 keldi, 2 kech keldi, 0 kelmadi, null belgilanmagan
            "present": (att[s.id].present if s.id in att else None),
            "homework": (att[s.id].homework if s.id in att else None),
            "grade": (grades[s.id].score if s.id in grades else None),
        } for s in students],
    }


@router.get("/api/teacher/week")
def teacher_week(db: Session = Depends(get_db),
                 user=Depends(require_role(*TEACHER_APP_ROLES))):
    """Shu haftaning dars jadvali — kun bo'yicha guruhlangan."""
    t = _me_teacher(db, user)
    gids = _my_group_ids(db, user, t)
    slots = support_slot_map(db, user)
    today = roles.local_today()
    start = today - timedelta(days=today.weekday())
    end = start + timedelta(days=6)
    if not gids:
        return {"start": start.isoformat(), "end": end.isoformat(),
                "days": []}

    rows = (db.query(models.Lesson, models.Group)
            .join(models.Group, models.Lesson.group_id == models.Group.id)
            .filter(models.Lesson.group_id.in_(gids),
                    models.Lesson.date >= start,
                    models.Lesson.date <= end)
            .order_by(models.Lesson.date, models.Group.lesson_time).all())
    by_day: dict = {}
    for ls, g in rows:
        by_day.setdefault(ls.date, []).append(
            _lesson_card(db, ls, g, slots))

    names = ["Dushanba", "Seshanba", "Chorshanba", "Payshanba",
             "Juma", "Shanba", "Yakshanba"]
    days = []
    for i in range(7):
        d = start + timedelta(days=i)
        days.append({
            "date": d.isoformat(),
            "label": names[i],
            "is_today": d == today,
            "lessons": by_day.get(d, []),
        })
    return {"start": start.isoformat(), "end": end.isoformat(),
            "days": days, "teacher": t.full_name}


@router.get("/api/teacher/support-options")
def teacher_support_options(db: Session = Depends(get_db),
                            user=Depends(require_role(*TEACHER_APP_ROLES))):
    """Support seansi uchun tanlovlar: guruhlar va RUXSAT ETILGAN
    soatlar (1 / 1.5 / 2 / 2.5 / 3).

    Chegaralar backend'dan keladi — telefonda qattiq yozib qo'yilsa,
    qoida o'zgarganda ikki joyni yangilash kerak bo'lardi va biri
    esdan chiqib, ekranda ruxsat etilgan, serverda esa rad etiladigan
    variant paydo bo'lardi."""
    t = _me_teacher(db, user)
    gids = _my_group_ids(db, user, t)
    groups = (db.query(models.Group)
              .filter(models.Group.id.in_(gids or [-1]))
              .order_by(models.Group.name).all()) if gids else []
    return {
        # Support seansi uchun tanlov: bu yerda ham GURUHNING dars
        # vaqti emas, supportning o'z biriktirilgan vaqti (2026-09-10).
        "groups": [{"id": g.id, "name": g.name,
                    "lesson_time": group_time_for(
                        support_slot_map(db, user), g)[1]}
                   for g in groups],
        "hour_steps": roles.SUPPORT_SESSION_HOUR_STEPS,
        "min_hours": roles.SUPPORT_SESSION_MIN_HOURS,
        "max_hours": roles.SUPPORT_SESSION_MAX_HOURS,
        "max_students": roles.SUPPORT_SESSION_MAX_STUDENTS,
    }


# =====================================================================
#  LUG'AT UNITLARINI TASDIQLASH (2026-08-11, Jahongir: "ustoz
#  1-unitni topshirdi degan tick qo'ysa unit avtomat 100% bo'lsin")
# =====================================================================

def _teacher_student_or_403(db, user, student_id: int):
    """Ustoz faqat O'Z guruhidagi o'quvchini ko'radi/tasdiqlaydi."""
    t = _me_teacher(db, user)
    gids = _my_group_ids(db, user, t)
    st = db.query(models.Student).get(student_id)
    if not st:
        raise HTTPException(404, "O'quvchi topilmadi")
    if st.group_id not in (gids or []):
        raise HTTPException(403, "Bu o'quvchi sizning guruhingizda emas")
    return st


@router.get("/api/teacher/vocab-students")
def teacher_vocab_students(group_id: int,
                           db: Session = Depends(get_db),
                           user=Depends(require_role(*TEACHER_APP_ROLES))):
    """Guruh o'quvchilari - unit tasdiqlash sahifasi uchun."""
    t = _me_teacher(db, user)
    gids = _my_group_ids(db, user, t)
    if group_id not in (gids or []):
        raise HTTPException(403, "Bu guruh sizniki emas")
    rows = (db.query(models.Student)
            .filter(models.Student.group_id == group_id,
                    models.Student.status.in_(("active", "trial")))
            .order_by(models.Student.full_name).all())
    return {"students": [{"id": x.id, "full_name": x.full_name}
                         for x in rows]}


@router.get("/api/teacher/vocab/{student_id}")
def teacher_vocab_progress(student_id: int, language: str = "en",
                           db: Session = Depends(get_db),
                           user=Depends(require_role(*TEACHER_APP_ROLES))):
    """O'quvchining unit progressi - ustoz ko'zi bilan."""
    st = _teacher_student_or_403(db, user, student_id)
    if language not in ("en", "ru", "de", "ko"):
        language = "en"

    q = db.query(models.VocabWord).filter(models.VocabWord.is_active == 1)
    if language == "en":
        q = q.filter((models.VocabWord.language == "en")
                     | (models.VocabWord.language.is_(None)))
    else:
        q = q.filter(models.VocabWord.language == language)
    words = q.all()
    by_unit = {}
    for w in words:
        by_unit.setdefault(w.topic or "Boshqa", []).append(w.id)
    cnt = dict(db.query(models.VocabAttempt.word_id,
                        func.count(models.VocabAttempt.id))
               .filter(models.VocabAttempt.student_id == st.id,
                       models.VocabAttempt.correct == 1)
               .group_by(models.VocabAttempt.word_id).all())
    passed = {p.unit for p in db.query(models.VocabUnitPass)
              .filter(models.VocabUnitPass.student_id == st.id,
                      models.VocabUnitPass.language == language).all()}

    def unit_no(t):
        try:
            return int(str(t).split()[-1])
        except (ValueError, IndexError):
            return 9999

    units = []
    for topic, ids in by_unit.items():
        n = len(ids)
        l3 = sum(1 for i in ids if cnt.get(i, 0) >= 3)
        is_passed = topic in passed
        units.append({
            "key": topic, "n": n, "learned3": l3,
            "percent": 100 if is_passed
            else (min(99, round(l3 * 99 / n)) if n else 0),
            "passed": is_passed,
        })
    units.sort(key=lambda x: unit_no(x["key"]))
    return {"student": st.full_name, "units": units,
            "language": language}


@router.post("/api/teacher/vocab-pass")
def teacher_vocab_pass(payload: dict = Body(...),
                       db: Session = Depends(get_db),
                       user=Depends(require_role(*TEACHER_APP_ROLES))):
    """Unitni topshirdi (yoki bekor qilish). Auditga yoziladi."""
    student_id = int(payload.get("student_id") or 0)
    unit = str(payload.get("unit") or "").strip()
    language = str(payload.get("language") or "en")
    want = bool(payload.get("passed", True))
    if language not in ("en", "ru", "de", "ko"):
        language = "en"
    if not unit:
        raise HTTPException(400, "Unit ko'rsatilmadi")
    st = _teacher_student_or_403(db, user, student_id)

    row = (db.query(models.VocabUnitPass)
           .filter(models.VocabUnitPass.student_id == st.id,
                   models.VocabUnitPass.unit == unit,
                   models.VocabUnitPass.language == language).first())
    if want and row is None:
        db.add(models.VocabUnitPass(
            student_id=st.id, unit=unit, language=language,
            passed_by=user.id))
        note = f"{unit} topshirildi deb tasdiqlandi"
    elif not want and row is not None:
        db.delete(row)
        note = f"{unit} tasdig'i bekor qilindi"
    else:
        return {"ok": True, "passed": want}
    db.commit()
    try:
        audit.log(db, user, entity="student", action="update",
                  entity_id=st.id, entity_label=st.full_name,
                  field="Lug'at uniti", note=note,
                  branch_id=st.branch_id, commit=True)
    except Exception:
        db.rollback()
    return {"ok": True, "passed": want}


@router.get("/api/teacher/home")
def teacher_home(db: Session = Depends(get_db),
                 user=Depends(require_role(*TEACHER_APP_ROLES))):
    """Bosh ekran: bugungi ish + qisqa ko'rsatkichlar."""
    t = _me_teacher(db, user)
    gids = _my_group_ids(db, user, t)
    slots = support_slot_map(db, user)
    today = roles.local_today()

    students = (db.query(func.count(models.Student.id))
                .filter(models.Student.group_id.in_(gids),
                        models.Student.status.in_(("active", "trial")))
                .scalar() or 0) if gids else 0

    # Shu oyda o'tilgan darslar (oylik shundan chiqadi)
    m_start, m_end = billing.month_bounds(today.year, today.month)
    held = (db.query(func.count(models.Lesson.id))
            .filter(models.Lesson.group_id.in_(gids),
                    models.Lesson.held == 1,
                    models.Lesson.date >= m_start,
                    models.Lesson.date <= m_end)
            .scalar() or 0) if gids else 0

    today_rows = (db.query(models.Lesson, models.Group)
                  .join(models.Group,
                        models.Lesson.group_id == models.Group.id)
                  .filter(models.Lesson.group_id.in_(gids),
                          models.Lesson.date == today)
                  .order_by(models.Group.lesson_time).all()) if gids else []
    lessons = [_lesson_card(db, ls, g, slots) for ls, g in today_rows]

    return {
        "teacher": t.full_name,
        "grade": getattr(t, "grade", None),
        "date": today.isoformat(),
        "groups": len(gids),
        "students": int(students),
        "lessons_this_month": int(held),
        "today": lessons,
        "pending": sum(1 for l in lessons if not l["done"]),
    }
