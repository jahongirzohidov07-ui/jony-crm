"""GURUH ARXIVI (2026-09-30).

Jahongir: "guruhda o'quvchi qolmagan yoki faol bo'lmagan guruhlarni
arxivga tushirib ko'rinmaydigan qilish funksiyasini qo'sh".

QOIDA. Guruh arxivga faqat unda HOZIRGI o'quvchi qolmaganda tushadi:
faol, sinovdagi yoki muzlatilgan o'quvchi (asosiy guruh ham, qo'shimcha
guruh bog'lanishi ham) bo'lsa — rad etiladi. Muzlatilgan o'quvchi
qaytadi, uning guruhi yashirinib qolmasin.

Avtomat EMAS — ro'yxat taklif qilinadi, odam belgilab tasdiqlaydi:
yangi ochilgan, o'quvchilari endi qo'shilayotgan guruh adashib
yashirinib ketmasin.

ARXIVDA NIMA BO'LADI:
  - guruhlar ro'yxati, tanlagichlar, ustoz/support kabineti va darslar
    jadvalida ko'rinmaydi (GET /api/groups sukut bo'yicha yashiradi);
  - kelajakdagi o'tilmagan (bo'sh) darslar olib tashlanadi, yangisi
    avtomat yaratilmaydi — jadvalda osilib turmasin;
  - support biriktirishlari bo'shatiladi — supportning vaqti band
    ko'rinib, boshqa guruhga qo'yishga to'sqinlik qilmasin;
  - O'CHIRILMAYDI: o'tgan darslar, yo'qlama, baho, to'lovlar joyida;
    "Arxiv" bo'limidan bir bosishda qaytariladi (darslar jadval
    bo'yicha yana o'zi yaratiladi).
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

import audit
import models
import roles
from auth import get_current_user, has_role
from common import _get_group_in_scope, scope_to_branch
from database import get_db

router = APIRouter()

# Hozirgi o'quvchi — shular bor ekan guruh arxivlanmaydi
CURRENT = ("active", "trial", "frozen")


def _can_manage(user=Depends(get_current_user)):
    """Guruhni boshqarish huquqi. Ro'yxat CHAQIRUV paytida o'qiladi:
    entry.py roles.GROUP_MANAGE ga keyin HR ni qo'shadi, import paytida
    olingan nusxa buni ko'rmasdi."""
    if not has_role(user, roles.GROUP_MANAGE):
        raise HTTPException(403, "Bu amal uchun ruxsatingiz yo'q")
    return user


def _current_counts(db: Session, gids: list) -> dict:
    """Guruh -> hozirgi o'quvchilar soni (asosiy + qo'shimcha bog'lanish,
    har o'quvchi bir marta)."""
    if not gids:
        return {}
    seen = {}
    for gid, sid in (db.query(models.Student.group_id, models.Student.id)
                     .filter(models.Student.group_id.in_(gids),
                             models.Student.status.in_(CURRENT)).all()):
        seen.setdefault(gid, set()).add(sid)
    for gid, sid in (db.query(models.StudentGroupLink.group_id,
                              models.StudentGroupLink.student_id)
                     .join(models.Student,
                           models.Student.id
                           == models.StudentGroupLink.student_id)
                     .filter(models.StudentGroupLink.group_id.in_(gids),
                             models.StudentGroupLink.active == 1,
                             models.Student.status.in_(CURRENT)).all()):
        seen.setdefault(gid, set()).add(sid)
    return {gid: len(s) for gid, s in seen.items()}


def _archive_one(db: Session, g, user, note: str) -> dict:
    """Bitta guruhni arxivlaydi. Hozirgi o'quvchi bo'lsa — xato matni."""
    if g.archived_at:
        return {"id": g.id, "name": g.name, "ok": False,
                "reason": "allaqachon arxivda"}
    n = _current_counts(db, [g.id]).get(g.id, 0)
    if n:
        return {"id": g.id, "name": g.name, "ok": False,
                "reason": f"{n} ta o'quvchi bor (faol/sinov/muzlatilgan)"}
    from groups_lessons import _safe_delete_lesson
    today = roles.local_today()
    removed = 0
    for ls in (db.query(models.Lesson)
               .filter(models.Lesson.group_id == g.id,
                       models.Lesson.held == 0,
                       models.Lesson.date > today).all()):
        if _safe_delete_lesson(db, ls):
            removed += 1
    sups = (db.query(models.SupportAssignment)
            .filter(models.SupportAssignment.group_id == g.id).all())
    sup_names = []
    for a in sups:
        u = db.query(models.User).get(a.user_id) if a.user_id else None
        if u is not None:
            sup_names.append(u.full_name)
        db.delete(a)
    g.archived_at = datetime.utcnow()
    g.archived_by = user.full_name
    g.archive_note = (note or "").strip() or None
    audit.log(db, user, entity="group", action="archive", entity_id=g.id,
              entity_label=g.name, field="archived_at",
              new_value="arxivda",
              note=("; ".join(filter(None, [
                  g.archive_note,
                  f"{removed} ta kelajakdagi bo'sh dars olib tashlandi"
                  if removed else None,
                  f"support bo'shatildi: {', '.join(sup_names)}"
                  if sup_names else None]))) or None,
              branch_id=g.branch_id)
    return {"id": g.id, "name": g.name, "ok": True,
            "lessons_removed": removed, "supports_released": sup_names}


@router.get("/api/groups/archive-candidates")
def archive_candidates(branch_id: Optional[int] = None,
                       db: Session = Depends(get_db),
                       user=Depends(_can_manage)):
    """Arxivga taklif: hozirgi o'quvchisi qolmagan, arxivda bo'lmagan
    guruhlar. Oxirgi o'tilgan dars ham ko'rsatiladi — qaror berish
    oson bo'lsin."""
    q = scope_to_branch(db.query(models.Group), models.Group, user,
                        branch_id).filter(models.Group.archived_at.is_(None))
    groups = q.order_by(models.Group.name).all()
    counts = _current_counts(db, [g.id for g in groups])
    empty = [g for g in groups if not counts.get(g.id)]
    ids = [g.id for g in empty]
    last = dict(db.query(models.Lesson.group_id, func.max(models.Lesson.date))
                .filter(models.Lesson.group_id.in_(ids or [-1]),
                        models.Lesson.held == 1)
                .group_by(models.Lesson.group_id).all())
    ever = dict(db.query(models.Student.group_id, func.count(models.Student.id))
                .filter(models.Student.group_id.in_(ids or [-1]))
                .group_by(models.Student.group_id).all())
    today = roles.local_today()
    rows = []
    for g in empty:
        ld = last.get(g.id)
        rows.append({
            "id": g.id, "name": g.name,
            "teacher": g.teacher.full_name if g.teacher else None,
            "branch": g.branch.name if g.branch else None,
            "last_lesson": ld.isoformat() if ld else None,
            "idle_days": (today - ld).days if ld else None,
            "past_students": int(ever.get(g.id, 0)),
            "created_at": (g.created_at.date().isoformat()
                           if g.created_at else None),
        })
    # Eng uzoq vaqt dars bo'lmaganlari tepada; umuman dars bo'lmagani
    # (yangi ochilgan bo'lishi mumkin) — oxirida
    rows.sort(key=lambda r: (r["idle_days"] is None,
                             -(r["idle_days"] or 0), r["name"]))
    return {"rows": rows, "total_groups": len(groups)}


class ArchiveIn(BaseModel):
    note: Optional[str] = None


class BulkArchiveIn(BaseModel):
    ids: List[int]
    note: Optional[str] = None


@router.post("/api/groups/{group_id}/archive")
def archive_group(group_id: int, payload: ArchiveIn,
                  db: Session = Depends(get_db),
                  user=Depends(_can_manage)):
    g = _get_group_in_scope(db, group_id, user)
    res = _archive_one(db, g, user, payload.note or "")
    if not res["ok"]:
        db.rollback()
        raise HTTPException(400, f"\"{g.name}\" arxivlanmadi: {res['reason']}")
    db.commit()
    return res


@router.post("/api/groups/archive-bulk")
def archive_bulk(payload: BulkArchiveIn, db: Session = Depends(get_db),
                 user=Depends(_can_manage)):
    """Belgilangan guruhlar. Har biri alohida tekshiriladi: o'quvchisi
    bor guruh o'tkazib yuboriladi va sababi qaytadi."""
    done, skipped = [], []
    for gid in dict.fromkeys(payload.ids or []):
        try:
            g = _get_group_in_scope(db, gid, user)
        except HTTPException as e:
            skipped.append({"id": gid, "name": None, "reason": e.detail})
            continue
        res = _archive_one(db, g, user, payload.note or "")
        (done if res["ok"] else skipped).append(res)
    db.commit()
    return {"archived": done, "skipped": skipped}


@router.post("/api/groups/{group_id}/restore")
def restore_group(group_id: int, db: Session = Depends(get_db),
                  user=Depends(_can_manage)):
    g = _get_group_in_scope(db, group_id, user)
    if not g.archived_at:
        raise HTTPException(400, "Guruh arxivda emas")
    was = g.archived_at
    g.archived_at = None
    g.archived_by = None
    g.archive_note = None
    audit.log(db, user, entity="group", action="restore", entity_id=g.id,
              entity_label=g.name, field="archived_at",
              old_value=was.isoformat(), new_value=None,
              branch_id=g.branch_id)
    db.commit()
    return {"ok": True, "id": g.id, "name": g.name}
