"""
KURSLAR — filialning narx ro'yxati (2026-08-15).

Jahongir: "sozlamalar ichida kurslar bolimini ochib u yerda kurslarni
yozadi dars vaqti narxini bitta darsga narxini yozadi, shu narxlar
hamma joyga ulanadi va shu boyicha hisob kitob qilinaveradi bizda ham
sentabrdan narxlar oshadi".

NEGA SHUNDAY QURILDI. Butun hisob-kitob (oylik yechish, faollashtirish,
guruh almashtirish, ustoz oyligi) guruhning narxidan o'qiydi — 18 xil
joyda. Ularning hammasini kursga bog'lash katta xavf edi. Shuning
uchun kurs narxi GURUHGA KO'CHIRILADI: hisob mantig'i umuman
o'zgarmaydi, o'tgan oylarning hisobi hech qachon qayta yozilmaydi,
faqat kelgusi hisoblar yangi narxda chiqadi.

SENTABRDAN OSHADIGAN NARX. Narx o'zgarishi SANA bilan qo'yiladi.
Sana kelmagunicha hech narsa o'zgarmaydi; kelganda kunlik ish
narxni kursga va uning guruhlariga ko'chiradi. Bir marta —
applied_at belgisi takrorlanishga yo'l qo'ymaydi.

"O'Z NARXI" BELGISI. Guruhga ataylab boshqa narx qo'yilgan bo'lsa
(price_manual=1), kurs o'zgarishi unga tegmaydi.
"""
import os
import sys
from datetime import date, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import audit
import models
import roles
import schemas
from auth import get_current_user, require_role
from database import get_db
from common import _in_user_branches, _user_branch_ids, scope_to_branch

router = APIRouter()


def _course_out(db: Session, c: models.Course) -> dict:
    groups = (db.query(models.Group)
              .filter(models.Group.course_id == c.id).all())
    nxt = (db.query(models.CoursePriceChange)
           .filter(models.CoursePriceChange.course_id == c.id,
                   models.CoursePriceChange.applied_at.is_(None))
           .order_by(models.CoursePriceChange.from_date).first())
    br = db.query(models.Branch).get(c.branch_id) if c.branch_id else None
    return {
        "id": c.id,
        "branch_id": c.branch_id,
        "branch": br.name if br else None,
        "name": c.name,
        "subject": c.subject,
        "subject_label": roles.SUBJECT_LABELS.get(c.subject or "",
                                                  c.subject),
        "level": c.level,
        "lesson_minutes": c.lesson_minutes,
        "lesson_price": c.lesson_price,
        "lessons_per_month": c.lessons_per_month,
        # Oylik narx — bitta dars narxi x oyiga dars soni
        "monthly_fee": round((c.lesson_price or 0)
                             * (c.lessons_per_month or 0)),
        "active": bool(c.active),
        "note": c.note,
        "groups": len(groups),
        "group_names": [g.name for g in groups][:12],
        "next_change": ({
            "id": nxt.id,
            "from_date": nxt.from_date.isoformat(),
            "lesson_price": nxt.lesson_price,
            "lessons_per_month": nxt.lessons_per_month,
            "note": nxt.note,
        } if nxt else None),
    }


def _push_price_to_groups(db: Session, c: models.Course,
                          by: str = None) -> int:
    """Kurs narxini uning guruhlariga ko'chiradi. "O'z narxi"
    belgilangan guruhga TEGMAYDI."""
    n = 0
    for g in (db.query(models.Group)
              .filter(models.Group.course_id == c.id).all()):
        if getattr(g, "price_manual", 0):
            continue
        changed = False
        if (g.lesson_price or 0) != (c.lesson_price or 0):
            g.lesson_price = c.lesson_price
            changed = True
        if c.lessons_per_month and \
                (g.standard_lessons_per_month or 0) != c.lessons_per_month:
            g.standard_lessons_per_month = c.lessons_per_month
            changed = True
        want_fee = round((c.lesson_price or 0) * (c.lessons_per_month or 0))
        if round(g.monthly_fee or 0) != want_fee:
            g.monthly_fee = want_fee
            changed = True
        if changed:
            n += 1
    if n:
        db.commit()
    return n


def apply_due_price_changes(db: Session, on: date = None) -> int:
    """Sanasi kelgan narx o'zgarishlarini qo'llaydi (kunlik ish)."""
    on = on or roles.local_today()
    rows = (db.query(models.CoursePriceChange)
            .filter(models.CoursePriceChange.applied_at.is_(None),
                    models.CoursePriceChange.from_date <= on).all())
    done = 0
    for ch in rows:
        c = db.query(models.Course).get(ch.course_id)
        if c is None:
            ch.applied_at = datetime.utcnow()
            continue
        c.lesson_price = ch.lesson_price
        if ch.lessons_per_month:
            c.lessons_per_month = ch.lessons_per_month
        ch.applied_at = datetime.utcnow()
        db.commit()
        _push_price_to_groups(db, c, "avtomat")
        try:
            audit.log(db, None, entity="course", action="price_change",
                      entity_id=c.id, entity_label=c.name,
                      field="lesson_price", new_value=ch.lesson_price,
                      note=f"{ch.from_date.isoformat()} dan yangi narx"
                           + (f" · {ch.note}" if ch.note else ""),
                      branch_id=c.branch_id, commit=True)
        except Exception:
            db.rollback()
        done += 1
    if rows:
        db.commit()
    return done


@router.get("/api/courses")
def list_courses(branch_id: int | None = None,
                 active: int | None = None,
                 db: Session = Depends(get_db),
                 user=Depends(get_current_user)):
    """Kurslar ro'yxati. Filialga bog'langan xodim faqat o'zinikini
    ko'radi."""
    q = scope_to_branch(db.query(models.Course), models.Course, user,
                        branch_id)
    if active is not None:
        q = q.filter(models.Course.active == (1 if active else 0))
    rows = q.order_by(models.Course.name).all()
    return [_course_out(db, c) for c in rows]


@router.post("/api/courses")
def create_course(payload: schemas.CourseIn,
                  db: Session = Depends(get_db),
                  user=Depends(require_role(*roles.FULL_ACCESS))):
    """Yangi kurs. Filial rahbari faqat O'Z filialiga qo'shadi."""
    bid = payload.branch_id
    if user.role != roles.FOUNDER:
        mine = _user_branch_ids(db, user)
        if bid is None:
            bid = user.branch_id
        if bid not in mine:
            raise HTTPException(403, "Bu filialga kurs qo'sha olmaysiz")
    if not (payload.name or "").strip():
        raise HTTPException(400, "Kurs nomini yozing")
    if (payload.lesson_price or 0) <= 0:
        raise HTTPException(400, "Bitta dars narxini yozing")
    c = models.Course(
        branch_id=bid, name=payload.name.strip(),
        subject=payload.subject, level=payload.level,
        lesson_minutes=payload.lesson_minutes or 90,
        lesson_price=payload.lesson_price,
        lessons_per_month=payload.lessons_per_month or 12,
        active=1 if (payload.active is None or payload.active) else 0,
        note=payload.note, created_by=user.full_name)
    db.add(c); db.commit(); db.refresh(c)
    audit.log(db, user, entity="course", action="create", entity_id=c.id,
              entity_label=c.name, new_value=c.lesson_price,
              branch_id=c.branch_id, commit=True)
    return _course_out(db, c)


@router.put("/api/courses/{cid}")
def update_course(cid: int, payload: schemas.CourseIn,
                  db: Session = Depends(get_db),
                  user=Depends(require_role(*roles.FULL_ACCESS))):
    """Kursni tahrirlash. Narx o'zgarsa — guruhlarga DARROV ko'chadi
    (kelgusi hisoblarga; o'tgan oylar tegilmaydi)."""
    c = db.query(models.Course).get(cid)
    if not c:
        raise HTTPException(404, "Kurs topilmadi")
    if not _in_user_branches(db, user, c.branch_id, null_ok=True):
        raise HTTPException(403, "Bu kurs boshqa filialga tegishli")
    old_price = c.lesson_price
    data = payload.model_dump(exclude_unset=True)
    data.pop("branch_id", None)
    for k, v in data.items():
        if v is not None and hasattr(c, k):
            setattr(c, k, v)
    if payload.active is not None:
        c.active = 1 if payload.active else 0
    if (c.lesson_price or 0) <= 0:
        raise HTTPException(400, "Bitta dars narxini yozing")
    db.commit()
    moved = _push_price_to_groups(db, c, user.full_name)
    if old_price != c.lesson_price:
        audit.log(db, user, entity="course", action="price_change",
                  entity_id=c.id, entity_label=c.name,
                  field="lesson_price", old_value=old_price,
                  new_value=c.lesson_price,
                  note=f"{moved} ta guruhga ko'chirildi",
                  branch_id=c.branch_id, commit=True)
    out = _course_out(db, c)
    out["groups_updated"] = moved
    return out


@router.delete("/api/courses/{cid}")
def delete_course(cid: int, db: Session = Depends(get_db),
                  user=Depends(require_role(*roles.FULL_ACCESS))):
    """Kursni o'chirish. Guruhi bor kurs O'CHIRILMAYDI — arxivlash
    uchun "faol emas" qilib qo'yiladi."""
    c = db.query(models.Course).get(cid)
    if not c:
        raise HTTPException(404, "Kurs topilmadi")
    if not _in_user_branches(db, user, c.branch_id, null_ok=True):
        raise HTTPException(403, "Bu kurs boshqa filialga tegishli")
    n = db.query(models.Group).filter(models.Group.course_id == cid).count()
    if n:
        raise HTTPException(
            400, f"Bu kursda {n} ta guruh bor. Avval guruhlarni boshqa "
                 "kursga o'tkazing yoki kursni \"faol emas\" qiling.")
    db.delete(c); db.commit()
    audit.log(db, user, entity="course", action="delete", entity_id=cid,
              entity_label=c.name, branch_id=c.branch_id, commit=True)
    return {"ok": True}


@router.post("/api/courses/{cid}/price-change")
def schedule_price_change(cid: int, payload: schemas.CoursePriceIn,
                          db: Session = Depends(get_db),
                          user=Depends(require_role(*roles.FULL_ACCESS))):
    """NARXNI SANADAN BOSHLAB OSHIRISH (2026-08-15, Jahongir: "bizda
    ham sentabrdan narxlar oshadi").

    Sana kelmagunicha hech narsa o'zgarmaydi. Sana bugungi yoki
    o'tgan bo'lsa — darrov qo'llanadi."""
    c = db.query(models.Course).get(cid)
    if not c:
        raise HTTPException(404, "Kurs topilmadi")
    if not _in_user_branches(db, user, c.branch_id, null_ok=True):
        raise HTTPException(403, "Bu kurs boshqa filialga tegishli")
    if (payload.lesson_price or 0) <= 0:
        raise HTTPException(400, "Yangi narxni yozing")
    # Shu kurs uchun kutayotgan eski reja bo'lsa - almashtiramiz
    db.query(models.CoursePriceChange).filter(
        models.CoursePriceChange.course_id == cid,
        models.CoursePriceChange.applied_at.is_(None)).delete(
            synchronize_session=False)
    ch = models.CoursePriceChange(
        course_id=cid, from_date=payload.from_date,
        lesson_price=payload.lesson_price,
        lessons_per_month=payload.lessons_per_month,
        note=payload.note, created_by=user.full_name)
    db.add(ch); db.commit(); db.refresh(ch)
    applied = apply_due_price_changes(db)
    audit.log(db, user, entity="course", action="price_plan",
              entity_id=c.id, entity_label=c.name,
              old_value=c.lesson_price, new_value=payload.lesson_price,
              note=f"{payload.from_date.isoformat()} dan",
              branch_id=c.branch_id, commit=True)
    return {"ok": True, "applied_now": bool(applied),
            "message": ("Narx darrov qo'llandi va guruhlarga ko'chdi."
                        if applied else
                        f"{payload.from_date.isoformat()} kuni avtomat "
                        "qo'llanadi. Shu kungacha eski narx ishlaydi.")}


@router.delete("/api/courses/price-change/{chid}")
def cancel_price_change(chid: int, db: Session = Depends(get_db),
                        user=Depends(require_role(*roles.FULL_ACCESS))):
    ch = db.query(models.CoursePriceChange).get(chid)
    if not ch or ch.applied_at:
        raise HTTPException(404, "Rejalashtirilgan o'zgarish topilmadi")
    c = db.query(models.Course).get(ch.course_id)
    if c and not _in_user_branches(db, user, c.branch_id, null_ok=True):
        raise HTTPException(403, "Bu kurs boshqa filialga tegishli")
    db.delete(ch); db.commit()
    return {"ok": True}
