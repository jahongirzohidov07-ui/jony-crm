"""TADBIRLAR VA TUG'ILGAN KUNLAR (2026-09-14).

Jahongir: "event manager degan lavozim qoshib qoygin eventlarni tashkil
qilish tugilgan kunlar avtomat korinib turishi kerak".

Tug'ilgan kunlar alohida jadvalda saqlanmaydi: o'quvchi va xodim
kartasidagi birth_date dan har so'rovda hisoblanadi. Shunda sana
kartada tuzatilsa, ro'yxat ham darhol to'g'ri bo'ladi — ikki joyni
bir-biriga moslab yurish kerak emas.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import re
from datetime import date

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session

import audit
import models
import roles
from auth import require_role
from database import get_db
from common import scope_to_branch

router = APIRouter()

# O'quvchi ro'yxatda qoladigan holatlar: arxiv va ketganlar tabriklanmaydi.
_STUDENT_GONE = ("archived", "left")
_TIME_RE = re.compile(r"^([01][0-9]|2[0-3]):[0-5][0-9]$")


def _birthday_row(who, obj_id, full_name, sub, branch, phone, born, today):
    nxt = roles.next_occurrence(born, today)
    left = (nxt - today).days
    return {
        "who": who,
        "who_label": "O'quvchi" if who == "student" else "Xodim",
        "id": obj_id,
        "full_name": full_name,
        "sub": sub,
        "branch": branch,
        "phone": phone,
        "date": nxt.isoformat(),
        "date_label": roles.uz_date_full(nxt),
        "days_left": left,
        "today": left == 0,
        "age": nxt.year - born.year,
    }


@router.get("/api/events/birthdays")
def event_birthdays(
    days: int = roles.BIRTHDAY_HORIZON,
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.EVENTS_ACCESS)),
):
    """Yaqinlashayotgan tug'ilgan kunlar: o'quvchilar va xodimlar birga,
    eng yaqini birinchi. Bugun tug'ilganlar alohida sanaladi."""
    today = date.today()
    days = max(0, min(days, 366))

    groups = {g.id: g.name for g in db.query(models.Group.id, models.Group.name).all()}
    branches = {b.id: b.name for b in db.query(models.Branch.id, models.Branch.name).all()}

    students = scope_to_branch(db.query(models.Student), models.Student, user, branch_id).filter(
        models.Student.status.notin_(_STUDENT_GONE)).all()
    staff = scope_to_branch(db.query(models.User), models.User, user, branch_id).filter(
        models.User.is_active == 1,
        models.User.role.notin_(roles.EXTERNAL_ROLES)).all()

    rows = []
    for s in students:
        if not s.birth_date:
            continue
        row = _birthday_row("student", s.id, s.full_name, groups.get(s.group_id),
                            branches.get(s.branch_id), s.phone, s.birth_date, today)
        if row["days_left"] <= days:
            rows.append(row)
    # Xodimning BARCHA filiallari (asosiy + qo'shimcha) — tabriklashda
    # kim qayerda ishlashi ko'rinsin (2026-10-03, Jahongir)
    extra: dict = {}
    for ub in db.query(models.UserBranch).all():
        extra.setdefault(ub.user_id, []).append(ub.branch_id)
    for u in staff:
        if not u.birth_date:
            continue
        bids = [u.branch_id] + [b for b in extra.get(u.id, []) if b != u.branch_id]
        brs = ", ".join(n for n in (branches.get(b) for b in bids if b) if n)
        row = _birthday_row("staff", u.id, u.full_name, roles.UZ_LABELS.get(u.role, u.role),
                            brs or "Barcha filiallar", u.phone, u.birth_date, today)
        if row["days_left"] <= days:
            rows.append(row)
    rows.sort(key=lambda r: (r["days_left"], r["full_name"]))

    return {
        "days": days,
        "rows": rows,
        "today": sum(1 for r in rows if r["today"]),
        "week": sum(1 for r in rows if r["days_left"] <= 7),
        "students": sum(1 for r in rows if r["who"] == "student"),
        "staff": sum(1 for r in rows if r["who"] == "staff"),
        "missing_students": sum(1 for s in students if not s.birth_date),
        "missing_staff": sum(1 for u in staff if not u.birth_date),
    }


def _event_out(e: models.Event) -> dict:
    today = date.today()
    return {
        "id": e.id,
        "title": e.title,
        "kind": e.kind,
        "kind_label": roles.EVENT_KIND_LABELS.get(e.kind, e.kind),
        "event_date": e.event_date.isoformat() if e.event_date else None,
        "date_label": roles.uz_date_full(e.event_date) if e.event_date else None,
        "days_left": (e.event_date - today).days if e.event_date else None,
        "start_time": e.start_time,
        "place": e.place,
        "branch_id": e.branch_id,
        "branch": e.branch.name if e.branch else None,
        "audience": e.audience,
        "budget": e.budget,
        "status": e.status,
        "status_label": roles.EVENT_STATUS_LABELS.get(e.status, e.status),
        "responsible_id": e.responsible_id,
        "responsible": e.responsible.full_name if e.responsible else None,
        "note": e.note,
        "created_by": e.created_by,
    }


def _clean(payload: dict, user: models.User, db: Session) -> dict:
    """Kiritilgan maydonlarni tekshirish. Xato bo'lsa — nima noto'g'ri
    ekanini aniq aytadi."""
    title = str(payload.get("title") or "").strip()[:200]
    if not title:
        raise HTTPException(400, "Tadbir nomini kiriting")
    try:
        on = date.fromisoformat(str(payload.get("event_date") or ""))
    except ValueError:
        raise HTTPException(400, "Tadbir sanasini to'g'ri kiriting (masalan 2026-09-20)")

    kind = payload.get("kind") or "other"
    if kind not in roles.EVENT_KIND_LABELS:
        raise HTTPException(400, "Noma'lum tadbir turi")
    status = payload.get("status") or "planned"
    if status not in roles.EVENT_STATUS_LABELS:
        raise HTTPException(400, "Noma'lum holat")

    start_time = str(payload.get("start_time") or "").strip() or None
    if start_time and not _TIME_RE.match(start_time):
        raise HTTPException(400, "Vaqtni SS:DD ko'rinishida kiriting (masalan 17:00)")

    budget = payload.get("budget")
    if budget in ("", None):
        budget = None
    else:
        try:
            budget = float(budget)
        except (TypeError, ValueError):
            raise HTTPException(400, "Byudjet raqam bo'lishi kerak")
        if budget < 0:
            raise HTTPException(400, "Byudjet manfiy bo'lishi mumkin emas")

    branch_id = payload.get("branch_id") or None
    if user.role not in roles.ORG_WIDE_ROLES and user.branch_id:
        # Filialga bog'langan xodim faqat o'z filiali tadbirini yaratadi
        branch_id = user.branch_id
    elif branch_id is not None and not db.query(models.Branch).get(int(branch_id)):
        raise HTTPException(400, "Bunday filial yo'q")

    responsible_id = payload.get("responsible_id") or None
    if responsible_id is not None:
        r = db.query(models.User).get(int(responsible_id))
        if not r or not r.is_active or r.role in roles.EXTERNAL_ROLES:
            raise HTTPException(400, "Mas'ul xodim topilmadi")

    def text(key, limit):
        v = str(payload.get(key) or "").strip()
        return v[:limit] or None

    return {
        "title": title, "kind": kind, "event_date": on, "start_time": start_time,
        "place": text("place", 200), "audience": text("audience", 200),
        "budget": budget, "status": status,
        "branch_id": int(branch_id) if branch_id else None,
        "responsible_id": int(responsible_id) if responsible_id else None,
        "note": text("note", 4000),
    }


def _event_in_scope(db: Session, user: models.User, eid: int) -> models.Event:
    e = (scope_to_branch(db.query(models.Event), models.Event, user, keep_unset=True)
         .filter(models.Event.id == eid).first())
    if not e:
        raise HTTPException(404, "Tadbir topilmadi")
    return e


@router.get("/api/events")
def list_events(
    branch_id: int | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.EVENTS_ACCESS)),
):
    q = scope_to_branch(db.query(models.Event), models.Event, user, branch_id, keep_unset=True)
    if status:
        q = q.filter(models.Event.status == status)
    rows = q.order_by(models.Event.event_date, models.Event.id).all()
    return {
        "rows": [_event_out(e) for e in rows],
        "kinds": [{"key": k, "label": lbl} for k, lbl in roles.EVENT_KINDS],
        "statuses": [{"key": k, "label": lbl, "tone": t} for k, lbl, t in roles.EVENT_STATUSES],
        "can_manage": user.role in roles.EVENTS_MANAGE,
    }


@router.get("/api/events/staff-options")
def event_staff_options(
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.EVENTS_MANAGE)),
):
    """Mas'ul qilib belgilash mumkin bo'lgan xodimlar."""
    staff = scope_to_branch(db.query(models.User), models.User, user).filter(
        models.User.is_active == 1,
        models.User.role.notin_(roles.EXTERNAL_ROLES)).order_by(models.User.full_name).all()
    return [{"id": u.id, "full_name": u.full_name,
             "role_label": roles.UZ_LABELS.get(u.role, u.role)} for u in staff]


@router.post("/api/events")
def create_event(
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.EVENTS_MANAGE)),
):
    data = _clean(payload, user, db)
    e = models.Event(**data, created_by=user.full_name)
    db.add(e)
    db.commit()
    db.refresh(e)
    audit.log(db, user, entity="event", action="create", entity_id=e.id,
              entity_label=e.title, commit=True)
    return _event_out(e)


@router.put("/api/events/{eid}")
def update_event(
    eid: int,
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.EVENTS_MANAGE)),
):
    e = _event_in_scope(db, user, eid)
    for k, v in _clean(payload, user, db).items():
        setattr(e, k, v)
    db.commit()
    db.refresh(e)
    audit.log(db, user, entity="event", action="update", entity_id=e.id,
              entity_label=e.title, commit=True)
    return _event_out(e)


@router.delete("/api/events/{eid}")
def delete_event(
    eid: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.EVENTS_MANAGE)),
):
    e = _event_in_scope(db, user, eid)
    title = e.title
    db.delete(e)
    db.commit()
    audit.log(db, user, entity="event", action="delete", entity_id=eid,
              entity_label=title, commit=True)
    return {"ok": True}
