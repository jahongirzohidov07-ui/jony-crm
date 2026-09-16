"""HR: QORA RO'YXAT (2026-09-16).

Jahongir: "o'quv markaz qora ro'yxatini shakllantir hr bo'limi uchun,
bu bo'limga tushgan nomzodlar boshqa ishga olinmasin".

Bu modulda:
  - find_hit / guard_hire — boshqa modullar ishga olishdan OLDIN
    chaqiradi (hr_ats, entry, teachers, auth_users);
  - hit_map — ro'yxatlarda nomzod yoniga belgi qo'yish uchun;
  - HR uchun API: ro'yxat, qo'shish, chiqarish.
Qoidalar va kalitlar roles.BLACKLIST_* va roles.blacklist_*_key da."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

import audit
import models
import roles
from auth import require_role
from database import get_db

router = APIRouter()


# ------------------------------------------------------------- tanib olish
def active_entries(db: Session) -> list:
    return (db.query(models.HrBlacklist)
            .filter(models.HrBlacklist.is_active == 1).all())


def match(entries: list, full_name=None, phone=None):
    """Mos yozuvni qaytaradi (yoki None).

    Telefon mos kelsa — o'sha odam. Ism mos kelsa ham o'sha odam
    hisoblanadi, FAQAT agar ikkala tomonda ham telefon bo'lib, ular
    farq qilmasa (bir xil ismli boshqa odamni to'sib qo'ymaslik uchun)."""
    pk = roles.blacklist_phone_key(phone)
    nk = roles.blacklist_name_key(full_name)
    if pk:
        for e in entries:
            if e.phone_key and e.phone_key == pk:
                return e
    if nk:
        for e in entries:
            if e.name_key == nk and not (pk and e.phone_key
                                         and e.phone_key != pk):
                return e
    return None


def find_hit(db: Session, full_name=None, phone=None):
    if not (roles.blacklist_phone_key(phone)
            or roles.blacklist_name_key(full_name)):
        return None
    return match(active_entries(db), full_name, phone)


def hit_brief(e) -> Optional[dict]:
    if not e:
        return None
    return {
        "id": e.id,
        "category": e.category,
        "category_label": roles.BLACKLIST_CATEGORY_LABELS.get(
            e.category, e.category),
        "reason": e.reason,
        "added_at": e.created_at.date().isoformat() if e.created_at else None,
        "added_by": e.added_by,
    }


def guard_hire(db: Session, full_name=None, phone=None) -> None:
    """Qora ro'yxatdagi odamni ishga olishni to'xtatadi (403)."""
    e = find_hit(db, full_name, phone)
    if e:
        raise HTTPException(
            403,
            f"{e.full_name} qora ro'yxatda "
            f"({roles.BLACKLIST_CATEGORY_LABELS.get(e.category, e.category)}"
            f": {e.reason}). Uni ishga olib bo'lmaydi. Ro'yxatdan faqat "
            f"HR yoki asoschi sabab yozib chiqara oladi.")


def hit_map(db: Session, people: list) -> dict:
    """[(key, full_name, phone), ...] -> {key: brief}. Bitta so'rov."""
    entries = active_entries(db)
    if not entries:
        return {}
    out = {}
    for key, name, phone in people:
        e = match(entries, name, phone)
        if e:
            out[key] = hit_brief(e)
    return out


# ---------------------------------------------------------------------- API
class BlacklistIn(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    category: str = "other"
    reason: str
    candidate_id: Optional[int] = None
    user_id: Optional[int] = None


class BlacklistRemoveIn(BaseModel):
    reason: str


def _out(e, applied: list | None = None) -> dict:
    return {
        "id": e.id,
        "full_name": e.full_name,
        "phone": e.phone,
        "category": e.category,
        "category_label": roles.BLACKLIST_CATEGORY_LABELS.get(
            e.category, e.category),
        "reason": e.reason,
        "candidate_id": e.candidate_id,
        "user_id": e.user_id,
        "is_active": bool(e.is_active),
        "added_by": e.added_by,
        "created_at": e.created_at.isoformat() if e.created_at else None,
        "removed_by": e.removed_by,
        "removed_at": e.removed_at.isoformat() if e.removed_at else None,
        "remove_reason": e.remove_reason,
        # Ro'yxatga tushgandan keyin qayta ariza topshirganmi
        "applied_again": applied or [],
    }


@router.get("/api/hr/blacklist")
def blacklist_list(status: str = "active", q: str | None = None,
                   db: Session = Depends(get_db),
                   user=Depends(require_role(*roles.BLACKLIST_VIEW))):
    qq = db.query(models.HrBlacklist)
    if status == "active":
        qq = qq.filter(models.HrBlacklist.is_active == 1)
    elif status == "removed":
        qq = qq.filter(models.HrBlacklist.is_active == 0)
    rows = qq.order_by(models.HrBlacklist.created_at.desc()).all()
    if q and q.strip():
        t = q.strip().lower()
        digits = "".join(ch for ch in t if ch.isdigit())
        rows = [e for e in rows
                if t in (e.full_name or "").lower()
                or (len(digits) >= 3 and digits in
                    "".join(ch for ch in (e.phone or "") if ch.isdigit()))]

    # Keyin qayta ariza topshirganlar (manba nomzoddan tashqari)
    cands = db.query(models.Candidate.id, models.Candidate.full_name,
                     models.Candidate.phone,
                     models.Candidate.created_at).all()
    out = []
    for e in rows:
        again = []
        for cid, name, phone, created in cands:
            if cid == e.candidate_id:
                continue
            if e.created_at and created and created < e.created_at:
                continue
            if match([e], name, phone):
                again.append({"id": cid, "full_name": name,
                              "created_at": created.isoformat()
                              if created else None})
        out.append(_out(e, again))
    return {
        "rows": out,
        "categories": [{"key": k, "label": lbl}
                       for k, lbl in roles.BLACKLIST_CATEGORIES],
        "can_manage": user.role in tuple(roles.BLACKLIST_MANAGE),
    }


@router.get("/api/hr/blacklist/check")
def blacklist_check(full_name: str | None = None, phone: str | None = None,
                    db: Session = Depends(get_db),
                    user=Depends(require_role(*roles.BLACKLIST_VIEW))):
    return {"hit": hit_brief(find_hit(db, full_name, phone))}


@router.post("/api/hr/blacklist")
def blacklist_add(payload: BlacklistIn, db: Session = Depends(get_db),
                  user=Depends(require_role(*roles.BLACKLIST_MANAGE))):
    name, phone = payload.full_name, payload.phone
    cand = person = None
    if payload.candidate_id:
        cand = db.query(models.Candidate).get(payload.candidate_id)
        if not cand:
            raise HTTPException(404, "Nomzod topilmadi")
        name, phone = name or cand.full_name, phone or cand.phone
    if payload.user_id:
        person = db.query(models.User).get(payload.user_id)
        if not person:
            raise HTTPException(404, "Xodim topilmadi")
        if person.role in (roles.FOUNDER,) + tuple(roles.EXTERNAL_ROLES):
            raise HTTPException(400, "Bu hisobni qora ro'yxatga qo'shib "
                                     "bo'lmaydi")
        if person.id == user.id:
            raise HTTPException(400, "O'zingizni qora ro'yxatga qo'sha "
                                     "olmaysiz")
        name, phone = name or person.full_name, phone or person.phone
    name = " ".join(str(name or "").split())
    phone = (phone or "").strip() or None
    reason = (payload.reason or "").strip()
    if len(name) < 3:
        raise HTTPException(400, "Ism-familiyani kiriting")
    if not (roles.blacklist_phone_key(phone)
            or roles.blacklist_name_key(name)):
        raise HTTPException(400, "Telefon raqami yoki to'liq ism-familiya "
                                 "(kamida ikki so'z) kerak — aks holda "
                                 "odamni tanib bo'lmaydi")
    if len(reason) < 5:
        raise HTTPException(400, "Sababni aniq yozing")
    if payload.category not in roles.BLACKLIST_CATEGORY_LABELS:
        raise HTTPException(400, "Toifani tanlang")
    dup = find_hit(db, name, phone)
    if dup:
        raise HTTPException(400, f"Bu odam allaqachon qora ro'yxatda "
                                 f"({dup.full_name})")
    e = models.HrBlacklist(
        full_name=name, phone=phone,
        phone_key=roles.blacklist_phone_key(phone),
        name_key=roles.blacklist_name_key(name),
        category=payload.category, reason=reason,
        candidate_id=cand.id if cand else None,
        user_id=person.id if person else None,
        added_by=user.full_name, added_by_id=user.id)
    db.add(e)
    db.commit()
    db.refresh(e)
    audit.log(db, user, entity="hr_blacklist", action="create",
              entity_id=e.id, entity_label=name,
              field=roles.BLACKLIST_CATEGORY_LABELS.get(e.category),
              new_value="qora ro'yxatga qo'shildi", note=reason,
              commit=True)
    return _out(e)


@router.post("/api/hr/blacklist/{eid}/remove")
def blacklist_remove(eid: int, payload: BlacklistRemoveIn,
                     db: Session = Depends(get_db),
                     user=Depends(require_role(*roles.BLACKLIST_MANAGE))):
    e = db.query(models.HrBlacklist).get(eid)
    if not e or not e.is_active:
        raise HTTPException(404, "Faol yozuv topilmadi")
    reason = (payload.reason or "").strip()
    if len(reason) < 5:
        raise HTTPException(400, "Nega chiqarilayotganini yozing")
    e.is_active = 0
    e.removed_by = user.full_name
    e.removed_at = datetime.utcnow()
    e.remove_reason = reason
    db.commit()
    audit.log(db, user, entity="hr_blacklist", action="delete",
              entity_id=e.id, entity_label=e.full_name,
              old_value="qora ro'yxatda", new_value="chiqarildi",
              note=reason, commit=True)
    return _out(e)
