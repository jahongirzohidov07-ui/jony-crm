"""Auto-extracted from main.py during refactor (split-main). Domain: timetable."""
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

@router.get("/api/timetable")
def timetable(
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_STAFF, roles.HR_MANAGER)),
):
    """Haftalik dars jadvali: qaysi kun, qaysi vaqt, qaysi guruh,
    qaysi ustoz, qaysi xona. Administrator uchun kunlik ish shu
    jadvaldan boshlanadi."""
    gq = scope_to_branch(db.query(models.Group), models.Group, user, branch_id)
    groups = gq.all()
    rooms = {r.id: r for r in db.query(models.Room).all()}

    counts = {}
    for st in scope_to_branch(db.query(models.Student), models.Student,
                              user, branch_id).all():
        if st.status == "active" and st.group_id:
            counts[st.group_id] = counts.get(st.group_id, 0) + 1

    items = []
    for g in groups:
        days = [d.strip() for d in (g.lesson_days or "").split(",") if d.strip()]
        if not days:
            continue
        room = rooms.get(g.room_id)
        items.append({
            "group_id": g.id, "group": g.name,
            "public_id": g.public_id,
            "subject": g.subject,
            "subject_label": dict(roles.SUBJECTS).get(g.subject or "", ""),
            "level": g.level,
            "level_label": dict(roles.SUBJECT_LEVELS.get(g.subject or "", []))
                           .get(g.level or "", g.level or ""),
            "teacher": g.teacher.full_name if g.teacher else None,
            "branch": g.branch.name if g.branch else None,
            "room": room.name if room else g.room,
            "capacity": _group_capacity(g, rooms),
            "students": counts.get(g.id, 0),
            "days": days,
            "start": g.lesson_time,
            "end": roles.lesson_end_time(g.lesson_time or ""),
            "time_label": roles.lesson_time_range(g.lesson_time),
            "start_date": g.start_date.isoformat() if g.start_date else None,
            "end_date": g.end_date.isoformat() if g.end_date else None,
        })

    # Kun -> vaqt bo'yicha guruhlangan ko'rinish
    by_day = {}
    for it in items:
        for d in it["days"]:
            by_day.setdefault(d, []).append(it)
    for d in by_day:
        by_day[d].sort(key=lambda x: (x["start"] or "99:99", x["group"]))

    # Xona bandligi: bir vaqtda bir xonada ikki guruh bo'lsa - to'qnashuv
    clashes = []
    seen = {}
    for it in items:
        if not it["room"] or not it["start"]:
            continue
        for d in it["days"]:
            key = (d, it["room"], it["start"])
            if key in seen:
                clashes.append({
                    "day": d, "room": it["room"], "time": it["time_label"],
                    "groups": [seen[key], it["group"]],
                })
            else:
                seen[key] = it["group"]

    return {
        "days": [{"key": k, "label": lbl, "short": sh}
                 for k, lbl, sh in roles.WEEKDAYS],
        "by_day": by_day,
        "items": sorted(items, key=lambda x: (x["start"] or "99:99", x["group"])),
        "no_schedule": [{"id": g.id, "name": g.name} for g in groups
                        if not (g.lesson_days or "").strip()],
        "clashes": clashes,
    }

def require_perm(resource: str, action: str = "view"):
    """Endpoint himoyasi. Rol ro'yxatlari o'rniga ishlatiladi -
    shunda asoschi ruxsatni ekrandan o'zgartira oladi."""
    def dep(db: Session = Depends(get_db),
            user: models.User = Depends(get_current_user)):
        if not has_perm(db, user, resource, action):
            raise HTTPException(
                403,
                f"\"{roles.RESOURCE_LABELS.get(resource, resource)}\" bo'limida "
                f"\"{roles.PERM_ACTION_LABELS.get(action, action)}\" "
                f"ruxsatingiz yo'q")
        return user
    return dep

GRID_STEP = 30

def _grid_slots() -> list:
    out = []
    t = GRID_START_MIN
    while t < GRID_END_MIN:
        out.append(f"{t // 60:02d}:{t % 60:02d}")
        t += GRID_STEP
    return out

SUBJECT_HUE = {
    "english": "teal",
    "russian": "violet",
    "korean": "emerald",
    "turkish": "amber",
    "german": "rose",
}

DAY_PRESETS = [
    ("odd", "Toq kunlar", ["mon", "wed", "fri"]),
    ("even", "Juft kunlar", ["tue", "thu", "sat"]),
]

@router.get("/api/timetable/grid")
def timetable_grid(
    day: str = "mon",
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_perm("timetable", "view")),
):
    """Xona x vaqt to'ri. day - hafta kuni yoki "odd"/"even"."""
    preset = next((p for p in DAY_PRESETS if p[0] == day), None)
    days = preset[2] if preset else [day]
    if not preset and day not in roles.WEEKDAY_KEYS:
        raise HTTPException(400, "Noto'g'ri kun")

    rooms = scope_to_branch(db.query(models.Room), models.Room,
                            user, branch_id).filter(
        models.Room.active == 1).order_by(models.Room.name).all()
    groups = scope_to_branch(db.query(models.Group), models.Group,
                             user, branch_id).all()
    students = scope_to_branch(db.query(models.Student), models.Student,
                               user, branch_id).all()
    today = date.today()

    # Guruh bo'yicha: o'quvchilar, o'tilgan darslar, o'rtacha yosh
    held = {}
    for gid, cnt in (db.query(models.Lesson.group_id,
                              func.count(models.Lesson.id))
                     .filter(models.Lesson.held == 1)
                     .group_by(models.Lesson.group_id).all()):
        held[gid] = cnt

    # DIQQAT: Group.room - bu ESKI matnli ustun, bog'lanish emas.
    # Xona nomini har doim room_id orqali topamiz.
    room_by_id = {r.id: r for r in db.query(models.Room).all()}

    items, unplaced = [], []
    for g in groups:
        g_days = [d for d in (g.lesson_days or "").split(",") if d]
        start, end = _group_slot(g)
        # Statistika faqat FAOL o'quvchilar bo'yicha
        mine = [s for s in students
                if s.group_id == g.id and s.status == "active"]
        cap = _group_capacity(g, room_by_id)
        ages = [round((today - s.birth_date).days / 365.25, 1)
                for s in mine if s.birth_date]
        avg_age = round(sum(ages) / len(ages), 1) if ages else None

        row = {
            "group_id": g.id,
            "group": g.name,
            "subject": g.subject,
            "subject_label": roles.SUBJECT_LABELS.get(g.subject or "", None),
            "level": g.level,
            "level_label": roles.LEVEL_LABELS.get(g.level or "", None),
            "teacher_id": g.teacher_id,
            "teacher": g.teacher.full_name if g.teacher else None,
            "room_id": g.room_id,
            "room": (room_by_id[g.room_id].name if g.room_id in room_by_id
                     else (g.room or None)),
            "days": g_days,
            "start": start,
            "end": end,
            "time_label": f"{start} - {end}" if start else None,
            "students": len(mine),
            "capacity": cap,
            "fill": round(len(mine) / cap * 100, 1) if cap else None,
            "lessons_held": held.get(g.id, 0),
            "avg_age": avg_age,
            "hue": SUBJECT_HUE.get(g.subject or "", "slate"),
            # To'la yoki juda bo'sh guruhni ko'z ilg'ashi kerak
            "warn": ("full" if cap and len(mine) >= cap
                     else "empty" if cap and len(mine) / cap < 0.5
                     else None),
        }
        if not g_days or not start:
            unplaced.append(row)
            continue
        if not any(d in days for d in g_days):
            continue
        items.append(row)

    slots = _grid_slots()

    def slot_index(t: str) -> int:
        m = roles.time_to_minutes(t)
        if m is None:
            return 0
        return max(0, (m - GRID_START_MIN) // GRID_STEP)

    # Xona bo'yicha joylashtiramiz
    by_room = {r.id: [] for r in rooms}
    no_room = []
    for it in items:
        it["col"] = slot_index(it["start"])
        e = roles.time_to_minutes(it["end"]) or 0
        s0 = roles.time_to_minutes(it["start"]) or 0
        it["span"] = max(1, (e - s0) // GRID_STEP)
        if it["room_id"] in by_room:
            by_room[it["room_id"]].append(it)
        else:
            no_room.append(it)

    # To'qnashuv: bir xonada vaqti kesishgan ikki guruh
    clashes = []
    for rid, rows in by_room.items():
        rows.sort(key=lambda x: x["col"])
        for i in range(len(rows)):
            for j in range(i + 1, len(rows)):
                if roles.ranges_overlap(rows[i]["start"], rows[i]["end"],
                                        rows[j]["start"], rows[j]["end"]):
                    room = next((r for r in rooms if r.id == rid), None)
                    clashes.append({
                        "room": room.name if room else "—",
                        "time": rows[i]["time_label"],
                        "groups": [rows[i]["group"], rows[j]["group"]],
                    })

    # Xona samaradorligi: shu kunda necha soat band
    def busy_hours(rows):
        mins = 0
        for x in rows:
            a = roles.time_to_minutes(x["start"]) or 0
            b = roles.time_to_minutes(x["end"]) or 0
            mins += max(0, b - a)
        return round(mins / 60, 1)

    window = (GRID_END_MIN - GRID_START_MIN) / 60

    return {
        "day": day,
        "day_label": (preset[1] if preset
                      else roles.WEEKDAY_LABELS.get(day, day)),
        "days": days,
        "presets": [{"key": k, "label": lbl, "days": ds}
                    for k, lbl, ds in DAY_PRESETS],
        "weekdays": [{"key": k, "label": lbl, "short": sh}
                     for k, lbl, sh in roles.WEEKDAYS],
        "slots": slots,
        "start": slots[0],
        "step": GRID_STEP,
        "rooms": [{
            "id": r.id,
            "name": r.name,
            "capacity": r.capacity,
            "branch": r.branch.name if r.branch else None,
            "items": by_room.get(r.id, []),
            "busy_hours": busy_hours(by_room.get(r.id, [])),
            "usage": round(busy_hours(by_room.get(r.id, [])) / window * 100, 1),
        } for r in rooms],
        "no_room": no_room,
        "unplaced": unplaced,
        "clashes": clashes,
        "total_groups": len(items),
        "total_students": sum(i["students"] for i in items),
        "can_edit": has_perm(db, user, "timetable", "edit"),
        "can_export": has_perm(db, user, "timetable", "export"),
    }

@router.get("/api/support-timetable")
def support_timetable(day: str = "mon",
                      branch_id: int | None = None,
                      db: Session = Depends(get_db),
                      user=Depends(require_role(
                          *roles.FULL_ACCESS, roles.HEAD_SUPPORT,
                          roles.ACADEMIC_HEAD, roles.HR_MANAGER))):
    """Supportlar bo'yicha alohida jadval: kim qaysi guruhda, qachon
    band. Support manager kimdan so'ramasdan darsni qo'yaveradi."""
    if day not in ("mon", "tue", "wed", "thu", "fri", "sat", "sun"):
        raise HTTPException(400, "Kun noto'g'ri")
    _ensure_support_cards(db)
    q = (db.query(models.Teacher)
         .join(models.User, models.User.id == models.Teacher.user_id)
         .filter(_support_cond(),
                 models.Teacher.is_active == 1))
    q = scope_to_branch(q, models.Teacher, user)
    if branch_id:
        q = q.filter(models.Teacher.branch_id == branch_id)
    bnames = {b.id: b.name for b in db.query(models.Branch).all()}
    rows = []
    for t in q.order_by(models.Teacher.full_name).all():
        blocks = []
        # biriktirilgan guruhlar
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
                "time": g.lesson_time or "",
                "sort": _time_to_min(st) or 0,
                "room": g.room,
            })
        # o'zi belgilagan band vaqtlar
        for b in (db.query(models.SupportBusy)
                  .filter(models.SupportBusy.teacher_id == t.id).all()):
            if day not in (b.days or ""):
                continue
            blocks.append({
                "kind": "busy",
                "label": b.note or "Band (o'zi belgilagan)",
                "time": f"{b.start}-{b.end}",
                "sort": _time_to_min(b.start) or 0,
            })
        blocks.sort(key=lambda x: x["sort"])
        rows.append({
            "teacher_id": t.id, "name": t.full_name,
            "branch": bnames.get(t.branch_id),
            "blocks": blocks,
        })
    return {"day": day, "rows": rows}

