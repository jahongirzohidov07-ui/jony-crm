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


def _can_delete(user, v) -> bool:
    """HR hammasini, rahbar faqat o'zi yozganini o'chiradi."""
    return (user.role in tuple(roles.CONDUCT_MANAGE_ALL)
            or v.created_by_id == user.id)


def _entry_out(v, nth, pts, names: dict, user=None) -> dict:
    return {
        "can_delete": bool(user and _can_delete(user, v)),
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


def _check_target(user, target) -> None:
    """Rahbar faqat o'z bo'limidagi oddiy xodimni baholaydi; rahbarlarni
    (o'zini ham) faqat HR baholaydi."""
    if not roles.conduct_can_rate(user.role, target.role):
        raise HTTPException(403, "Bu xodimni faqat HR baholaydi")


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
    users = [u for u in _section_users(db, section, branch_id)
             if roles.conduct_can_rate(user.role, u.role)]
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
            log.append(_entry_out(v, nth, pts, names, user))
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
        "can_import": user.role in tuple(roles.CONDUCT_MANAGE_ALL),
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
    _check_target(user, u)
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
    _check_target(user, target)
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
    if target:
        _check_target(user, target)
    if not _can_delete(user, v):
        raise HTTPException(403, "Bu yozuvni faqat HR yoki uni yozgan "
                                 "rahbar o'chiradi")
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


# ---------------------------------------------------------------------
#  EXCEL'DAN IMPORT (2026-09-16, Jahongir: "Exceldagi ma'lumotlarni ham
#  qo'shib ber"). Faylni brauzer o'qiydi va yozuvlar ro'yxatini yuboradi;
#  server ismlarni xodimlarga moslaydi. Avval apply=false — HR natijani
#  ko'radi va mos kelmagan ismni qo'lda tanlaydi; so'ng apply=true.
#  Qayta import qilinsa, oldin import qilingan yozuvlar TAKRORLANMAYDI.
# ---------------------------------------------------------------------
IMPORT_NOTE = "Excel'dan import"
_APOS = str.maketrans({c: "'" for c in "\u2019\u2018\u02bb\u02bc`\u00b4"})


def _norm_name(s) -> str:
    return " ".join(str(s or "").translate(_APOS).lower().split())


@router.post("/api/conduct/import")
def conduct_import(payload: schemas.ConductImportIn,
                   db: Session = Depends(get_db),
                   user=Depends(require_role(*roles.CONDUCT_MANAGE_ALL))):
    items = payload.items
    if len(items) > 5000:
        raise HTTPException(400, "Bir martada 5000 tadan ko'p yozuv bo'lmasin")
    today = roles.local_today()
    lim = roles.CONDUCT_REPRIMAND_MAX
    for it in items:
        if it.kind == roles.CONDUCT_REPRIMAND:
            if not it.points or abs(it.points) > lim:
                raise HTTPException(400, f"{it.name}: xayfsan bali noto'g'ri")
        elif it.kind not in roles.CONDUCT_STEPS:
            raise HTTPException(400, f"Noma'lum tur: {it.kind}")
        if it.date > today:
            raise HTTPException(400, f"{it.name}: kelajak sana ({it.date})")

    staff = [u for u in db.query(models.User)
             .filter(models.User.is_active == 1,
                     models.User.role.in_(_STAFF_ROLES))
             .order_by(models.User.full_name).all()
             if roles.conduct_section(u.role)]
    by_id = {u.id: u for u in staff}
    by_norm = defaultdict(list)
    for u in staff:
        by_norm[_norm_name(u.full_name)].append(u)
    mapping = {_norm_name(k): v for k, v in (payload.mapping or {}).items()}

    names, resolved = {}, {}
    for it in items:
        key = _norm_name(it.name)
        if not key or key in names:
            if key:
                names[key]["count"] += 1
            continue
        row = {"name": " ".join(str(it.name).split()), "count": 1,
               "user_id": None, "user_name": None, "status": "unmatched"}
        if key in mapping:
            uid = mapping[key]
            if not uid:
                row["status"] = "skipped"
            elif uid in by_id:
                row.update(user_id=uid, user_name=by_id[uid].full_name,
                           status="mapped")
            else:
                raise HTTPException(400, f"{row['name']}: xodim topilmadi")
        else:
            cand = by_norm.get(key, [])
            if len(cand) == 1:
                row.update(user_id=cand[0].id, user_name=cand[0].full_name,
                           status="matched")
            elif len(cand) > 1:
                row["status"] = "ambiguous"
        names[key] = row
        if row["user_id"]:
            resolved[key] = row["user_id"]

    def k_of(uid, kind, d, pts):
        return (uid, kind, d, round(float(pts), 2) if pts is not None else None)

    incoming = defaultdict(int)
    for it in items:
        uid = resolved.get(_norm_name(it.name))
        if uid:
            pts = it.points if it.kind == roles.CONDUCT_REPRIMAND else None
            incoming[k_of(uid, it.kind, it.date, pts)] += 1
    existing = defaultdict(int)
    if resolved:
        for v in (db.query(models.ConductViolation)
                  .filter(models.ConductViolation.user_id.in_(
                      set(resolved.values())),
                      models.ConductViolation.note.like(IMPORT_NOTE + "%"))
                  .all()):
            existing[k_of(v.user_id, v.kind, v.date, v.points)] += 1

    to_add = {k: n - existing[k] for k, n in incoming.items()
              if n > existing[k]}
    total_new = sum(to_add.values())
    already = sum(incoming.values()) - total_new
    added = 0
    if payload.apply and to_add:
        for (uid, kind, d, pts), n in to_add.items():
            for _ in range(n):
                db.add(models.ConductViolation(
                    user_id=uid, date=d, kind=kind, points=pts,
                    note=(IMPORT_NOTE + ": xayfsan"
                          if kind == roles.CONDUCT_REPRIMAND else IMPORT_NOTE),
                    created_by=user.full_name, created_by_id=user.id))
                added += 1
        db.commit()
        audit.log(db, user, entity="conduct", action="import",
                  entity_label="Na'munali xodim",
                  new_value=f"{added} ta yozuv", note=IMPORT_NOTE,
                  commit=True)

    return {
        "names": sorted(names.values(),
                        key=lambda r: (r["status"] in ("matched", "mapped"),
                                       r["name"])),
        "users": [{"id": u.id, "name": u.full_name,
                   "role_label": roles.UZ_LABELS.get(u.role, u.role)}
                  for u in staff],
        "total": len(items),
        "to_add": total_new,
        "already": already,
        "added": added,
        "applied": bool(payload.apply),
    }