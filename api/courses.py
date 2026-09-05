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
            "keep_old_for_active": bool(
                getattr(nxt, "keep_old_for_active", 1)),
        } if nxt else None),
        # Nechta o'quvchi ESKI narxda qolgan (2026-08-15)
        "locked_students": (
            db.query(models.Student)
            .filter(models.Student.group_id.in_(
                [g.id for g in groups] or [-1]),
                models.Student.locked_lesson_price.isnot(None))
            .count() if groups else 0),
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


def lock_price_for_active(db: Session, c: models.Course,
                          old_price: float = None,
                          note: str = None) -> int:
    """ESKI NARX HIMOYASI (2026-08-15, Jahongir: "bizda o'qib
    turganlar uchun faol bolib turganlar uchun sentabrdan narx eski
    narxda qoladi faqat yangilar uchun yoki avgust muzlatib keyin
    yana kelganlarga narx oshgan bolishi kerak").

    Narx oshgan KUNI faol bo'lgan o'quvchilarning narxi qulflanadi.
    Muzlatilganlar va chiqib ketganlarga QULF QO'YILMAYDI — qaytib
    kelsa yangi narxda o'qiydi."""
    groups = (db.query(models.Group)
              .filter(models.Group.course_id == c.id).all())
    if not groups:
        return 0
    n = 0
    for g in groups:
        # Har guruhning O'SHA PAYTDAGI narxi qulflanadi — o'quvchi
        # aynan nima to'lab turgan bo'lsa, o'sha qoladi. (Guruhga
        # alohida narx qo'yilgan bo'lishi ham mumkin.)
        price = float(old_price if old_price else (g.lesson_price or 0))
        if price <= 0:
            continue
        rows = (db.query(models.Student)
                .filter(models.Student.group_id == g.id,
                        models.Student.status == "active",
                        models.Student.locked_lesson_price.is_(None)).all())
        for st in rows:
            st.locked_lesson_price = price
            st.locked_price_at = datetime.utcnow()
            st.locked_price_note = (
                note
                or f"{c.name}: narx oshganda eski narx saqlab qolindi")
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
        old_price = c.lesson_price
        # ESKI NARX HIMOYASI — narx ko'tarilishidan OLDIN qulflaymiz
        locked = 0
        if getattr(ch, "keep_old_for_active", 1) \
                and (ch.lesson_price or 0) > (old_price or 0):
            locked = lock_price_for_active(
                db, c, None,
                f"{c.name}: {ch.from_date.isoformat()} dan narx oshdi, "
                "eski narx saqlab qolindi")
        ch.locked_students = locked
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
    keep = (True if payload.keep_old_for_active is None
            else bool(payload.keep_old_for_active))
    ch = models.CoursePriceChange(
        course_id=cid, from_date=payload.from_date,
        lesson_price=payload.lesson_price,
        lessons_per_month=payload.lessons_per_month,
        keep_old_for_active=1 if keep else 0,
        note=payload.note, created_by=user.full_name)
    db.add(ch); db.commit(); db.refresh(ch)
    applied = apply_due_price_changes(db)
    db.refresh(ch)
    locked = ch.locked_students or 0
    audit.log(db, user, entity="course", action="price_plan",
              entity_id=c.id, entity_label=c.name,
              old_value=c.lesson_price, new_value=payload.lesson_price,
              note=f"{payload.from_date.isoformat()} dan",
              branch_id=c.branch_id, commit=True)
    keep_txt = (" Hozirgi FAOL o'quvchilar eski narxda qoladi; "
                "yangi kelganlar va muzlatib qaytganlar yangi narxda."
                if keep else
                " Diqqat: hamma o'quvchi yangi narxga o'tadi.")
    return {"ok": True, "applied_now": bool(applied),
            "locked_students": locked,
            "message": (
                (f"Narx darrov qo'llandi va guruhlarga ko'chdi. "
                 f"{locked} ta o'quvchiga eski narx qulflandi."
                 if applied else
                 f"{payload.from_date.isoformat()} kuni avtomat "
                 "qo'llanadi. Shu kungacha eski narx ishlaydi.")
                + keep_txt)}


@router.post("/api/students/{sid}/price-lock")
def set_student_price_lock(sid: int, payload: schemas.PriceLockIn,
                           db: Session = Depends(get_db),
                           user=Depends(require_role(*roles.FULL_ACCESS))):
    """O'quvchining ESKI NARX qulfini qo'yish yoki ochish.

    Qulf ochilsa o'quvchi joriy (yangi) narxga o'tadi. Bu qo'lda
    aralashuv - shuning uchun auditga yoziladi."""
    st = db.query(models.Student).get(sid)
    if not st:
        raise HTTPException(404, "O'quvchi topilmadi")
    if not _in_user_branches(db, user, st.branch_id, null_ok=True):
        raise HTTPException(403, "Bu o'quvchi boshqa filialga tegishli")
    old = st.locked_lesson_price
    if payload.price and payload.price > 0:
        st.locked_lesson_price = float(payload.price)
        st.locked_price_at = datetime.utcnow()
        st.locked_price_note = (payload.note
                                or f"Qo'lda qo'yildi ({user.full_name})")
    else:
        st.locked_lesson_price = None
        st.locked_price_at = None
        st.locked_price_note = None
    db.commit()
    audit.log(db, user, entity="student", action="price_lock",
              entity_id=st.id, entity_label=st.full_name,
              field="locked_lesson_price", old_value=old,
              new_value=st.locked_lesson_price,
              note=payload.note, branch_id=st.branch_id, commit=True)
    return {"ok": True, "locked_lesson_price": st.locked_lesson_price}


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


# =====================================================================
#  SENTABR 2026 NARX QOIDASI (2026-09-05)
#
#  Jahongir: "Avgustda o'qiganlar yani toliq qatnashgan yoki 480 ming
#  tolaganlar uchun narxlar o'zgarishsiz ketadi deganman, sentabrdan
#  yozilganlar uchun esa 540,000dan bo'lishi kerak stretinko filialdan
#  tashqari, IT filialdan tashqari shunaqa, stretinkoda esa barchasi
#  420,000 so'm. Shuning uchun 480ming dagilarni o'zgarishsin
#  qoladiganlar shunaqa bo'lib qolishi kerak bir korib chiqib xato
#  ketganlar bo'lsa togrlab chiqish kerak".
#
#  Jonli bazani tekshirganda (682 ta sentabr hisobi):
#    - 65 ta guruh hamon 40 000/dars (480 000) da — yangi kelganlar
#      ham 480 000 bilan hisoblanardi (1 ta topildi: Ubaydullaev
#      Elmurod, 04.09 da kelgan);
#    - Stretinkoda 2 ta guruh (Stariki, Nevada) 40 000 da — 2 ta
#      o'quvchi 480 000 bilan hisoblangan, 420 000 bo'lishi kerak edi;
#    - 33 ta yangi o'quvchi hali hisoblanmagan — faollashganda
#      GURUH narxi olinadi, demak guruh narxi to'g'ri bo'lishi shart.
#
#  Qoida uch qadamda, TARTIB MUHIM:
#    1) ESKILARNI QULFLASH — 1-sentabrgacha kelgan (yoki avgustda
#       hisoblangan) faol o'quvchilar hozirgi guruh narxida (40 000)
#       qulflanadi. Muzlatilgan/ketganga qulf qo'yilmaydi — qaytsa
#       yangi narxda (mavjud qoida).
#    2) GURUH NARXLARI — Stretinko: 35 000 (420 000); qolgan
#       filiallar: 40 000 -> 45 000 (540 000). Stetch (IT, hamkor)
#       ga tegilmaydi. Boshqa (g'alati) narxdagi guruhlarga
#       tegilmaydi — ular ataylab qo'yilgan bo'lishi mumkin.
#    3) XATO HISOBLARNI TUZATISH — sentabr uchun "standart oy" (12
#       dars, chegirmasiz) hisoblangan, lekin qoida bo'yicha boshqa
#       summa bo'lishi kerak bo'lganlarga FARQ yozuvi qo'shiladi
#       (eski yozuv o'chirilmaydi): yangi o'quvchi 480 000 ->
#       +60 000; Stretinko 480 000 -> -60 000.
#
#  Idempotent (SeedMark), hech narsa o'chirilmaydi, hammasi auditga
#  yoziladi.
# =====================================================================
SEPT_2026_NEW_UNIT = 45000.0       # 540 000 / 12
SEPT_2026_OLD_UNIT = 40000.0       # 480 000 / 12
SEPT_2026_STRETINKO_UNIT = 35000.0 # 420 000 / 12
SEPT_2026_CUTOFF = date(2026, 9, 1)
SEPT_2026_PERIOD = "2026-09"
_SEPT_SKIP_BRANCHES = ("stetch", "stech")   # IT hamkor filial


def _branch_kind(name: str) -> str:
    n = (name or "").strip().lower()
    if n.startswith("stretinko"):
        return "stretinko"
    if n in _SEPT_SKIP_BRANCHES or "stech" in n or "stetch" in n:
        return "skip"
    return "main"


def apply_sept_2026_pricing(db: Session, today: date = None) -> dict:
    """Yuqoridagi qoidani bir marta qo'llaydi. Qaytaradi: nima qilindi."""
    today = today or roles.local_today()
    out = {"locked": 0, "groups_up": 0, "groups_stretinko": 0,
           "fixed_new": 0, "fixed_stretinko": 0, "skipped_groups": 0}
    branches = {b.id: _branch_kind(b.name) for b in
                db.query(models.Branch).all()}
    groups = db.query(models.Group).all()

    # Avgustda hisoblanganlar — "eski" belgisi uchun
    aug_ids = {sid for (sid,) in db.query(models.Payment.student_id)
               .filter(models.Payment.kind == "charge",
                       models.Payment.period == "2026-08").all()}

    def is_old(st: models.Student) -> bool:
        if st.id in aug_ids:
            return True
        return bool(st.enrolled_date and st.enrolled_date < SEPT_2026_CUTOFF)

    # ---- 1) ESKILARNI QULFLASH (faqat asosiy filiallar) ----
    for g in groups:
        kind = branches.get(g.branch_id, "main")
        if kind != "main":
            continue
        if round(g.lesson_price or 0) != SEPT_2026_OLD_UNIT:
            continue          # 40 000 bo'lmagan guruh — qoidadan tashqari
        for st in (db.query(models.Student)
                   .filter(models.Student.group_id == g.id,
                           models.Student.status == "active",
                           models.Student.locked_lesson_price.is_(None))
                   .all()):
            if not is_old(st):
                continue
            st.locked_lesson_price = SEPT_2026_OLD_UNIT
            st.locked_price_at = datetime.utcnow()
            st.locked_price_note = ("Sentabr 2026: avgustda o'qigan — "
                                    "480 000 saqlab qolindi")
            out["locked"] += 1
    db.flush()

    # ---- 2) GURUH NARXLARI ----
    for g in groups:
        kind = branches.get(g.branch_id, "main")
        cur = round(g.lesson_price or 0)
        if kind == "skip":
            out["skipped_groups"] += 1
            continue
        if kind == "stretinko":
            if cur != SEPT_2026_STRETINKO_UNIT:
                if cur == SEPT_2026_OLD_UNIT:
                    g.lesson_price = SEPT_2026_STRETINKO_UNIT
                    g.monthly_fee = SEPT_2026_STRETINKO_UNIT * (
                        g.standard_lessons_per_month or 12)
                    out["groups_stretinko"] += 1
                else:
                    out["skipped_groups"] += 1
            continue
        # asosiy filiallar
        if cur == SEPT_2026_OLD_UNIT:
            g.lesson_price = SEPT_2026_NEW_UNIT
            g.monthly_fee = SEPT_2026_NEW_UNIT * (
                g.standard_lessons_per_month or 12)
            out["groups_up"] += 1
        elif cur != SEPT_2026_NEW_UNIT:
            out["skipped_groups"] += 1
    db.flush()

    # ---- 3) SENTABR HISOBLARINI TUZATISH ----
    # Faqat ANIQ holat: bitta charge, 12 dars, standart oy, 480 000.
    charges = (db.query(models.Payment, models.Student)
               .join(models.Student,
                     models.Payment.student_id == models.Student.id)
               .filter(models.Payment.kind == "charge",
                       models.Payment.period == SEPT_2026_PERIOD).all())
    by_student: dict = {}
    for p, st in charges:
        by_student.setdefault(st.id, []).append((p, st))
    for sid, items in by_student.items():
        if len(items) != 1:
            continue                      # allaqachon tuzatilgan/bo'lingan
        p, st = items[0]
        if round(abs(p.amount)) != SEPT_2026_OLD_UNIT * 12:
            continue                      # 480 000 emas — chegirma/qisman
        g = st.group
        if g is None:
            continue
        kind = branches.get(g.branch_id, "main")
        if kind == "skip":
            continue
        # Chegirmasi bor o'quvchiga tegmaymiz (summasi 480 000 bo'lsa ham
        # chegirma alohida yozuv bo'lishi mumkin) — qo'lda ko'riladi
        try:
            from common import _student_discount_percent
            if _student_discount_percent(db, st):
                continue
        except Exception:
            pass
        want = None
        why = None
        if kind == "stretinko":
            want = SEPT_2026_STRETINKO_UNIT * 12
            why = "Stretinko: barcha 420 000"
        elif not is_old(st):
            want = SEPT_2026_NEW_UNIT * 12
            why = "sentabrdan kelgan: 540 000"
        if want is None or round(want) == SEPT_2026_OLD_UNIT * 12:
            continue
        # Tizimdagi qoida bilan bir xil (_fz_set, edit_payment): oyning
        # hisoblangan qatori JOYIDA to'g'rilanadi, eski summa auditda
        # qoladi. Ikkinchi qator ochilmaydi — boshqa hisob-kitoblar
        # "bir oyga bitta hisob" deb ishlaydi.
        old_amt = p.amount
        p.amount = -want
        p.note = ((p.note or "") + f" · narx tuzatish ({why}): "
                  f"{int(SEPT_2026_OLD_UNIT * 12):,} -> {int(want):,}"
                  ).replace(",", " ")
        p.updated_at = datetime.utcnow()
        audit.log(db, None, entity="payment", action="update",
                  entity_id=p.id, entity_label=st.full_name,
                  field="amount", old_value=old_amt, new_value=-want,
                  note=f"Sentabr 2026 narx qoidasi: {why}",
                  branch_id=st.branch_id)
        if kind == "stretinko":
            out["fixed_stretinko"] += 1
        else:
            out["fixed_new"] += 1
    db.commit()
    return out
