"""Lesson-level timetable ownership and effective time."""
from fastapi import HTTPException
from sqlalchemy import and_, or_, select
import models
import roles


def lesson_scope(db, user, teacher, group_ids):
    """An accepted substitute owns only that group's lesson on that date."""
    L, S = models.Lesson, models.Substitution
    active_group = L.group_id.in_(select(models.Group.id).where(
        models.Group.archived_at.is_(None)))
    live = or_(L.cancelled == 0, L.cancelled.is_(None))
    if user.role == roles.SUPPORT_TEACHER:
        return and_(live, active_group, L.group_id.in_(group_ids))
    assigned = db.query(S.id).filter(
        S.group_id == L.group_id, S.lesson_date == L.date,
        S.status.in_(["accepted", "done"]),
        S.substitute_teacher_id.isnot(None)).correlate(L)
    mine = assigned.filter(S.substitute_teacher_id == teacher.id).exists()
    return and_(live, active_group, or_(
        mine, and_(L.group_id.in_(group_ids), ~assigned.exists())))


def check_lesson_write(db, user, lesson):
    if lesson.cancelled:
        raise HTTPException(400, "Bekor qilingan darsga yo'qlama yoki baho qo'yilmaydi")
    if user.role == roles.TEACHER:
        from common import _teacher_of_user, _my_groups
        teacher = _teacher_of_user(db, user)
        gids = [g.id for g in _my_groups(db, teacher.id)] if teacher else []
        if not teacher or not db.query(models.Lesson.id).filter(
                models.Lesson.id == lesson.id,
                lesson_scope(db, user, teacher, gids)).first():
            raise HTTPException(403, "Bu sanada dars sizga biriktirilmagan")


def lesson_time(db, lesson, fallback):
    """Only applied moves affect the lesson; pending/rejected moves do not."""
    R = models.LessonReschedule
    move = db.query(R).filter(
        R.group_id == lesson.group_id,
        R.to_date == lesson.date,
        R.status.in_(roles.RESCHEDULE_DONE),
        or_(R.lesson_id == lesson.id, R.lesson_id.is_(None)),
    ).order_by(R.id.desc()).first()
    return move.to_time if move and move.to_time else fallback
