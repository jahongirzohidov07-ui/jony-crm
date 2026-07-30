"""Dars-asosidagi to'lov (student billing) va ustoz ish haqi (teacher
payroll) hisoblash mantig'i.

Qoida (Jahongir tavsifi bo'yicha):
- Bitta dars = group.lesson_price (masalan 40 000 so'm).
- Standart oyda group.standard_lessons_per_month (odatda 12) dars uchun
  to'lanadi. Agar oyda shundan ko'p dars o'tilgan bo'lsa (masalan 13-14),
  ortig'i talabaga bepul sovg'a - baribir standart miqdorga qarab
  hisoblanadi (ya'ni min(o'tilgan darslar, standart) bilan cheklanadi).
- Agar talaba oyning yarmida qo'shilgan bo'lsa - faqat uning qo'shilgan
  sanasidan keyin o'tilgan darslar sanaladi (standart bilan cheklangan
  holda), va shunga qarab kamroq hisoblanadi.
- USTOZ ISH HAQI - yoqlamadan hisoblanadi, avtomat:

      bitta yoqlama narxi = teacher_rate_per_student / standard_lessons

  Masalan bir o'quvchidan oyiga 120 000 so'm, oyda 12 dars bo'lsa:
  120 000 / 12 = 10 000 so'm har bir yoqlamadan.

  Ustoz bir darsda 5 o'quvchiga yoqlama qo'ysa - 50 000 so'm oladi.
  Yoqlama yo'q - oylik ham yo'q. Hech kim hech narsani bosmaydi:
  yoqlama qo'yilishi bilan oylik o'zi o'sadi.

  Bo'luvchi HAQIQATDA o'tilgan dars soni emas, STANDART dars soni.
  Aks holda kam dars o'tgan ustozning bir darsi qimmatlashib ketardi
  va oyligi baribir o'zgarmasdi.
"""

import calendar
from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

import models


def month_bounds(year: int, month: int) -> tuple[date, date]:
    start = date(year, month, 1)
    end = date(year, month, calendar.monthrange(year, month)[1])
    return start, end


def held_lessons_query(db: Session, group_id: int, start: date, end: date):
    """Faqat HAQIQATDA o'tilgan darslar. Jadval bo'yicha avtomat
    yaratilgan, lekin hali yoqlama qo'yilmagan darslar (held=0) bu yerga
    kirmaydi - aks holda o'quvchidan bo'lmagan dars uchun pul olingan
    bo'lardi."""
    return db.query(models.Lesson).filter(
        models.Lesson.group_id == group_id,
        models.Lesson.date >= start,
        models.Lesson.date <= end,
        models.Lesson.held == 1,
    )


def held_lessons_count(db: Session, group_id: int, year: int, month: int) -> int:
    start, end = month_bounds(year, month)
    return held_lessons_query(db, group_id, start, end).count()


def billable_lessons_for_student(
    db: Session,
    student: models.Student,
    group: models.Group,
    year: int,
    month: int,
) -> int:
    """Necha dars uchun shu talabadan pul olinishi kerak - guruhning
    standart chegarasi bilan cheklangan, va talaba shu oyga qachon
    qo'shilganini hisobga olgan holda."""
    start, end = month_bounds(year, month)
    effective_start = start
    if student.enrolled_date and student.enrolled_date > start:
        effective_start = student.enrolled_date
    if effective_start > end:
        return 0
    held = held_lessons_query(db, group.id, effective_start, end).count()
    cap = group.standard_lessons_per_month or 12
    return min(held, cap)


def compute_student_charges(
    db: Session, group: models.Group, year: int, month: int
) -> list[dict]:
    """Guruhdagi har bir faol/sinov talaba uchun shu oyning hisob-kitobini
    qaytaradi (Payment yozmaydi - shunchaki hisoblaydi)."""
    students = (
        db.query(models.Student)
        .filter(
            models.Student.group_id == group.id,
            models.Student.status.in_(["active", "trial"]),
        )
        .order_by(models.Student.full_name)
        .all()
    )
    period = f"{year:04d}-{month:02d}"
    out = []
    for s in students:
        billable = billable_lessons_for_student(db, s, group, year, month)
        amount = billable * (group.lesson_price or 0)
        already_charged = (
            db.query(models.Payment)
            .filter(
                models.Payment.student_id == s.id,
                models.Payment.period == period,
                models.Payment.kind == "charge",
            )
            .first()
        )
        out.append(
            {
                "student_id": s.id,
                "student_name": s.full_name,
                "billable_lessons": billable,
                "amount": amount,
                "already_charged": already_charged is not None,
            }
        )
    return out


# =====================================================================
#  USTOZ DARAJASI VA STAVKA
#
#  Bir o'quvchidan qancha olishi ustozning DARAJASIDAN chiqadi:
#  Junior 80 000, Middle 100 000, Senior 120 000, Expert 140 000,
#  Head 160 000.
#
#  Eng nozik joyi shu: ustoz bugun ko'tarilsa, O'TGAN OYNING darslari
#  ESKI stavkada qolishi kerak. Aks holda tarix qayta yozilib, allaqachon
#  to'langan oyning summasi o'zgarib ketardi va kassa hisobi buzilardi.
#  Shuning uchun stavka har bir darsning SANASIGA qarab, o'sha kuni
#  kuchda bo'lgan daraja bo'yicha olinadi.
# =====================================================================
def grade_rates(db: Session) -> dict:
    """Daraja -> bir o'quvchidan oylik summa."""
    try:
        return {g.key: (g.rate_per_student or 0)
                for g in db.query(models.TeacherGrade).all()}
    except Exception:
        return {}


def grade_on(db: Session, teacher_id: int, on_date: date) -> Optional[str]:
    """Ustoz SHU SANADA qaysi darajada edi. Tarixda yozuv bo'lmasa -
    hozirgi darajasi."""
    if not teacher_id:
        return None
    try:
        ev = (db.query(models.TeacherGradeEvent)
              .filter(models.TeacherGradeEvent.teacher_id == teacher_id,
                      models.TeacherGradeEvent.effective_from <= on_date,
                      models.TeacherGradeEvent.to_grade.isnot(None))
              .order_by(models.TeacherGradeEvent.effective_from.desc(),
                        models.TeacherGradeEvent.id.desc())
              .first())
        if ev:
            return ev.to_grade
    except Exception:
        pass
    t = db.query(models.Teacher).get(teacher_id)
    return t.grade if t else None


def rate_per_student(db: Session, group: models.Group,
                     teacher_id: Optional[int], on_date: date,
                     rates: Optional[dict] = None) -> float:
    """Ustozga shu guruhning bir o'quvchisidan bir oyga qancha
    to'lanadi — shu sanadagi holat bo'yicha.

    Guruhga ataylab qo'lda narx qo'yilgan bo'lsa (rate_manual), daraja
    unga tegmaydi: istisno holatlar uchun yo'l ochiq qoladi."""
    if getattr(group, "rate_manual", 0):
        return group.teacher_rate_per_student or 0
    if rates is None:
        rates = grade_rates(db)
    v = rates.get(grade_on(db, teacher_id, on_date))
    if v:
        return v
    # Daraja jadvali hali to'lmagan bo'lsa - eski xatti-harakat
    return group.teacher_rate_per_student or 0


def per_attendance_rate(group: models.Group,
                        per_student: Optional[float] = None) -> float:
    """Bitta yoqlama qancha turadi.

    Formula: ustozga bir o'quvchidan bir OY uchun beriladigan summa,
    o'shanday oydagi STANDART dars soniga bo'linadi.

        120 000 / 12 = 10 000

    Muhim: bo'luvchi haqiqatda o'tilgan dars soni EMAS, standart dars
    soni. Aks holda ustoz kam dars o'tsa bir darsning narxi ko'tarilib
    ketardi va oyligi baribir o'zgarmasdi — ya'ni dars o'tmaslikning
    jazosi bo'lmasdi."""
    std = group.standard_lessons_per_month or 12
    if std <= 0:
        return 0.0
    if per_student is None:
        per_student = group.teacher_rate_per_student or 0
    return (per_student or 0) / std


def lesson_rate(db: Session, group: models.Group, lesson: models.Lesson,
                rates: Optional[dict] = None) -> tuple[float, float]:
    """Shu dars uchun (bir yoqlama narxi, bir o'quvchidan oylik summa)."""
    per_student = rate_per_student(db, group, lesson.teacher_id,
                                   lesson.date, rates)
    return per_attendance_rate(group, per_student), per_student


def lesson_student_count(db: Session, lesson: models.Lesson) -> int:
    """Shu darsda ustoz nechta o'quvchi uchun javobgar edi.

    Yoqlamada belgilangan o'quvchilar soni olinadi. O'quvchi kelmagan
    bo'lsa ham sanaladi — chunki u shu dars uchun baribir to'laydi,
    demak ustoz ham haqini oladi.

    Yoqlama umuman qo'yilmagan bo'lsa (masalan faqat baho qo'yilgan),
    O'SHA KUNI guruhda kim bo'lgani sanaladi — bugungi ro'yxat emas.
    Aks holda keyin bir o'quvchi ketsa, o'tgan oyning oyligi ham
    o'zgarib ketardi."""
    n = (db.query(models.Attendance)
         .filter(models.Attendance.lesson_id == lesson.id).count())
    if n:
        return n
    rows = (db.query(models.Student)
            .filter(models.Student.group_id == lesson.group_id).all())
    return sum(
        1 for s in rows
        if (not s.enrolled_date or s.enrolled_date <= lesson.date)
        and (not s.left_date or s.left_date >= lesson.date)
    )


def compute_teacher_payroll(
    db: Session, group: models.Group, year: int, month: int,
    rates: Optional[dict] = None,
) -> list[dict]:
    """Guruh bo'yicha shu oyda kim qancha ish haqi olishini hisoblaydi.

    Ustoz YOQLAMA qo'ygani uchun pul oladi: har bir o'tilgan darsda
    nechta o'quvchi bo'lsa, shuncha marta per_attendance_rate.
    Yoqlama yo'q — oylik ham yo'q.

    Stavka har bir darsning sanasiga qarab olinadi: oy o'rtasida
    ko'tarilgan ustoz eski darslari uchun eski, yangilari uchun yangi
    stavkada oladi."""
    start, end = month_bounds(year, month)
    lessons = held_lessons_query(db, group.id, start, end).all()
    held = len(lessons)
    std = group.standard_lessons_per_month or 12
    if rates is None:
        rates = grade_rates(db)

    student_count = (
        db.query(models.Student)
        .filter(
            models.Student.group_id == group.id,
            models.Student.status.in_(["active", "trial"]),
        )
        .count()
    )

    # Ustoz kesimida: nechta dars o'tdi, nechta yoqlama qo'ydi, qancha
    # ishlab topdi. Stavka dars sanasi bo'yicha olinadi.
    cache: dict = {}
    by_teacher: dict[Optional[int], dict] = {}
    for lesson in lessons:
        if lesson.teacher_id is None:
            continue
        key = (lesson.teacher_id, lesson.date)
        if key not in cache:
            cache[key] = rate_per_student(db, group, lesson.teacher_id,
                                          lesson.date, rates)
        per_student = cache[key]
        rate = per_attendance_rate(group, per_student)
        n = lesson_student_count(db, lesson)

        row = by_teacher.setdefault(lesson.teacher_id, {
            "taught_lessons": 0, "attendances": 0, "amount": 0.0,
            "per_student": per_student, "rate": rate,
        })
        row["taught_lessons"] += 1
        row["attendances"] += n
        row["amount"] += n * rate
        # Oy oxiridagi (eng so'nggi) stavka ko'rsatiladi
        row["per_student"] = per_student
        row["rate"] = rate

    out = []
    for teacher_id, row in by_teacher.items():
        amount = row["amount"]
        out.append(
            {
                "teacher_id": teacher_id,
                "held_lessons": held,
                "taught_lessons": row["taught_lessons"],
                "attendances": row["attendances"],
                "student_count": student_count,
                "rate": row["rate"],
                "rate_per_student_month": row["per_student"],
                "standard_lessons": std,
                # Standartdan ko'p dars o'tilgan bo'lsa - ko'rinib tursin.
                # O'quvchi ortiqcha darsga to'lamaydi, ustoz esa oladi.
                "extra_lessons": max(0, row["taught_lessons"] - std),
                "amount": amount,
                "amount_per_student": (amount / student_count
                                       if student_count else 0.0),
            }
        )
    return out
