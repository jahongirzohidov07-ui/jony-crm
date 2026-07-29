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
- Ustoz "yoqlama qo'ygani" (Lesson yozuvi yaratgani) uchun pul oladi:
  agar guruh bo'yicha group.teacher_rate_per_student (bitta o'quvchidan
  to'liq oy uchun) belgilangan bo'lsa, bitta darsning "narxi" =
  teacher_rate_per_student / (shu oyda haqiqatda o'tilgan darslar soni).
  Ustoz shundan necha darsni o'zi o'tgan (yoqlama qo'ygan) bo'lsa, o'sha
  qadar oladi - agar hammasini o'tgan bo'lsa, to'liq stavkani oladi.
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
    return db.query(models.Lesson).filter(
        models.Lesson.group_id == group_id,
        models.Lesson.date >= start,
        models.Lesson.date <= end,
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


def compute_teacher_payroll(
    db: Session, group: models.Group, year: int, month: int
) -> list[dict]:
    """Guruh bo'yicha shu oyda kim qancha dars o'tgani (Lesson.teacher_id
    bo'yicha guruhlangan) va shunga qarab qancha haq olishi kerakligini
    hisoblaydi. Bir nechta ustoz almashinishi mumkin bo'lgani uchun
    ro'yxat qaytaradi."""
    start, end = month_bounds(year, month)
    lessons = held_lessons_query(db, group.id, start, end).all()
    held = len(lessons)

    student_count = (
        db.query(models.Student)
        .filter(
            models.Student.group_id == group.id,
            models.Student.status.in_(["active", "trial"]),
        )
        .count()
    )

    per_lesson_rate = 0.0
    if held > 0:
        per_lesson_rate = (group.teacher_rate_per_student or 0) / held

    taught_by_teacher: dict[Optional[int], int] = {}
    for lesson in lessons:
        taught_by_teacher[lesson.teacher_id] = (
            taught_by_teacher.get(lesson.teacher_id, 0) + 1
        )

    out = []
    for teacher_id, taught in taught_by_teacher.items():
        if teacher_id is None:
            continue
        amount_per_student = per_lesson_rate * taught
        out.append(
            {
                "teacher_id": teacher_id,
                "held_lessons": held,
                "taught_lessons": taught,
                "student_count": student_count,
                "amount_per_student": amount_per_student,
                "amount": amount_per_student * student_count,
            }
        )
    return out
