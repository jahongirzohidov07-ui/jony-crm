"""NA'MUNALI XODIM — intizom balli (2026-09-16).

Jahongir: "bitta yangi bo'lim och Na'munali xodim degan, u joyga kirganda
Na'munali xodim, Na'munali support, Na'munali examiner bo'limlarga
bo'linsin ... ball ayrilishi va kimga qachon qanday minus yozilgani
shu tizimdagidek aniq tiniq bo'lsin".

Qoidalar roles.CONDUCT_* da. Bu yerda faqat hisob va API."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from collections import defaultdict
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import audit
import models
import roles
import schemas
from auth import require_role
from database import get_db

router = APIRouter()

_STAFF_ROLES = list(dict.fromkeys(roles.STAFF_ROLES + [roles.ADMINISTRATOR]))


def _section_users(db: Session, section: str, branch_id=None) -> list:
    us = (db.query(models.User)
          .filter(models.User.is_active == 1,
                  models.User.role.in_(_STAFF_ROLES))
          .order_by(models.User.full_name).all())
    us = [u for u in us if roles.conduct_section(u.role) == section]
    if branch_id:
        extra = {ub.user_id for ub in db.query(models.UserBranch)
                 .filter(models.UserBranch.branch_id == branch_id).all()}
        us = [u for u in us if u.branch_id == branch_id or u.id in extra]
    return us


def _scored(rows: list) -> list:
    """Yozuvlarga oy ichidagi tartib raqami va ayirilgan ballni qo'yadi.

    Tartib: sana, keyin yozilgan tartibi. Bir xil qoidabuzarlik bir oyda
    takrorlansa jarima oshadi; yangi oyda hisob 1 dan boshlanadi."""
    seq = defaultdict(int)
    out = []
    for v in sorted(rows, key=lambda r: (r.date, r.id)):
        if v.kind == roles.CONDUCT_REPRIMAND:
            nth, pts = None, round(float(v.points or 0), 2)
        else:
            key = (v.user_id, v.kind, v.date.year, v.date.month)
            seq[key] += 1
            nth = seq[key]
            pts = roles.conduct_points(v.kind, nth)
        out.append((v, nth, pts))
    return out


def _entry_out(v, nth, pts, names: dict) -> dict:
    return {
        "id": v.id,
        "user_id": v.user_id,
        "name": names.get(v.user_id, "—"),
        "date": v.date.isoformat(),
        "kind": v.kind,
        "kind_label": roles.CONDUCT_KIND_LABELS.get(v.kind, v.kind),
        "nth": nth,
        "points": pts,
        "note": v.note,
        "created_by": v.created_by,
        "created_at": v.created_at.isoformat() if v.created_at else None,
    }


def _year_rows(db: Session, user_ids: list, year: int) -> list:
    if not user_ids:
        return []
    return (db.query(models.ConductViolation)
            .filter(models.ConductViolation.user_id.in_(user_ids),
                    models.ConductViolation.date >= date(year, 1, 1),
                    models.ConductViolation.date <= date(year, 12, 31))
            .all())


def _rules() -> dict:
    return {
        "start": roles.CONDUCT_START_POINTS,
        "kinds": [{"key": k, "label": lbl, "steps": list(steps)}
                  for k, lbl, steps in roles.CONDUCT_KINDS],
        "reprimand": {"key": roles.CONDUCT_REPRIMAND,
                      "label": roles.CONDUCT_KIND_LABELS[
                          roles.CONDUCT_REPRIMAND],
                      "max": roles.CONDUCT_REPRIMAND_MAX},
        "sanctions": [{"limit": lim, "level": lvl, "teacher": t,
                       "other": o}
                      for lim, lvl, t, o in roles.CONDUCT_SANCTIONS],
    }


def _check_section(user, section: str) -> None:
    if section not in roles.CONDUCT_SECTION_LABELS:
        raise HTTPException(400, "Noto'g'ri bo'lim")
    if section not in roles.conduct_sections_for(user.role):
        raise HTTPException(403, "Bu bo'limga ruxsatingiz yo'q")


@router.get("/api/conduct")
def conduct_board(section: str = "staff", year: int | None = None,
                  month: int | None = None, branch_id: int | None = None,
                  db: Session = Depends(get_db),
                  user=Depends(require_role(*roles.CONDUCT_VIEW))):
    """Bo'lim jadvali: har xodimning qolgan bali, jazosi va shu oyda
    (month=0 bo'lsa — butun yil) kimga qachon qanday minus yozilgani."""
    _check_section(user, section)
    today = roles.local_today()
    y = year or today.year
    m = today.month if month is None else month
    if m < 0 or m > 12:
        raise HTTPException(400, "Noto'g'ri oy")
    users = _section_users(db, section, branch_id)
    names = {u.id: u.full_name for u in users}
    scored = _scored(_year_rows(db, list(names), y))

    branches = {b.id: b.name for b in db.query(models.Branch).all()}
    per_user = defaultdict(lambda: {"year": 0.0, "month": 0.0,
                                    "counts": defaultdict(int)})
    log = []
    for v, nth, pts in scored:
        s = per_user[v.user_id]
        s["year"] += pts
        if not m or v.date.month == m:
            s["month"] += pts
            s["counts"][v.kind] += 1
            log.append(_entry_out(v, nth, pts, names))
    log.sort(key=lambda e: (e["date"], e["id"]), reverse=True)

    rows = []
    for u in users:
        s = per_user[u.id]
        remaining = round(roles.CONDUCT_START_POINTS - s["year"], 2)
        rows.append({
            "user_id": u.id,
            "name": u.full_name,
            "role": u.role,
            "role_label": roles.UZ_LABELS.get(u.role, u.role),
            "branch": branches.get(u.branch_id),
            "year_minus": round(s["year"], 2),
            "period_minus": round(s["month"], 2),
            "remaining": remaining,
            "counts": dict(s["counts"]),
            "sanction": roles.conduct_sanction(remaining, u.role),
        })
    rows.sort(key=lambda r: (r["remaining"], r["name"]))

    allowed = roles.conduct_sections_for(user.role)
    return {
        "section": section,
        "sections": [{"key": k, "label": lbl}
                     for k, lbl in roles.CONDUCT_SECTIONS if k in allowed],
        "year": y,
        "month": m,
        "rows": rows,
        "log": log,
        "rules": _rules(),
        "can_manage": True,
    }


@router.get("/api/conduct/user/{user_id}")
def conduct_user_history(user_id: int, year: int | None = None,
                         db: Session = Depends(get_db),
                         user=Depends(require_role(*roles.CONDUCT_VIEW))):
    """Bitta xodimning yil davomidagi barcha minuslari."""
    u = db.query(models.User).get(user_id)
    sec = roles.conduct_section(u.role) if u else None
    if not sec:
        raise HTTPException(404, "Xodim topilmadi")
    _check_section(user, sec)
    y = year or roles.local_today().year
    scored = _scored(_year_rows(db, [u.id], y))
    names = {u.id: u.full_name}
    items = [_entry_out(v, nth, pts, names) for v, nth, pts in scored]
    items.reverse()
    total = round(sum(p for _, _, p in scored), 2)
    remaining = round(roles.CONDUCT_START_POINTS - total, 2)
    return {
        "user_id": u.id,
        "name": u.full_name,
        "year": y,
        "year_minus": total,
        "remaining": remaining,
        "sanction": roles.conduct_sanction(remaining, u.role),
        "items": items,
    }


@router.post("/api/conduct")
def conduct_add(payload: schemas.ConductIn, db: Session = Depends(get_db),
                user=Depends(require_role(*roles.CONDUCT_VIEW))):
    target = db.query(models.User).get(payload.user_id)
    sec = (roles.conduct_section(target.role)
           if target and target.is_active == 1
           and target.role in _STAFF_ROLES else None)
    if not sec:
        raise HTTPException(404, "Xodim topilmadi")
    _check_section(user, sec)
    kind = payload.kind
    note = (payload.note or "").strip() or None
    points = None
    if kind == roles.CONDUCT_REPRIMAND:
        try:
            points = round(float(payload.points), 2)
        except (TypeError, ValueError):
            points = 0.0
        lim = roles.CONDUCT_REPRIMAND_MAX
        if points == 0 or abs(points) > lim:
            raise HTTPException(400, f"Xayfsan bali 0 bo'lmasin va "
                                     f"±{lim} dan oshmasin")
        if not note:
            raise HTTPException(400, "Xayfsan sababini yozing")
    elif kind not in roles.CONDUCT_STEPS:
        raise HTTPException(400, "Qoidabuzarlik turini tanlang")
    d = payload.date or roles.local_today()
    if d > roles.local_today():
        raise HTTPException(400, "Kelajak sanaga yozib bo'lmaydi")
    v = models.ConductViolation(
        user_id=target.id, date=d, kind=kind, points=points, note=note,
        created_by=user.full_name, created_by_id=user.id)
    db.add(v)
    db.commit()
    db.refresh(v)
    # Javobda haqiqiy ayirilgan ball — foydalanuvchi darhol ko'radi
    month_rows = [r for r in _year_rows(db, [target.id], d.year)
                  if r.date.month == d.month]
    got = next(((n, p) for r, n, p in _scored(month_rows) if r.id == v.id),
               (None, 0.0))
    audit.log(db, user, entity="conduct", action="create",
              entity_id=v.id, entity_label=target.full_name,
              branch_id=target.branch_id,
              field=roles.CONDUCT_KIND_LABELS.get(kind, kind),
              new_value=f"-{got[1]} ball ({d.isoformat()})",
              note=note, commit=True)
    return {"ok": True, "id": v.id, "nth": got[0], "points": got[1]}


@router.delete("/api/conduct/{violation_id}")
def conduct_delete(violation_id: int, db: Session = Depends(get_db),
                   user=Depends(require_role(*roles.CONDUCT_VIEW))):
    v = db.query(models.ConductViolation).get(violation_id)
    if not v:
        raise HTTPException(404, "Yozuv topilmadi")
    target = db.query(models.User).get(v.user_id)
    sec = roles.conduct_section(target.role) if target else "staff"
    _check_section(user, sec or "staff")
    label = target.full_name if target else "—"
    info = (f"{roles.CONDUCT_KIND_LABELS.get(v.kind, v.kind)}, "
            f"{v.date.isoformat()}")
    note = v.note
    db.delete(v)
    db.commit()
    audit.log(db, user, entity="conduct", action="delete",
              entity_id=violation_id, entity_label=label,
              branch_id=target.branch_id if target else None,
              old_value=info, note=note, commit=True)
    return {"ok": True}
