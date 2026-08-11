"""Auto-extracted from main.py during refactor (split-main). Domain: students."""
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

@router.get("/api/students/{student_id}/lead")
def student_lead(
    student_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_STAFF)),
):
    """O'quvchi lidan aylangan bo'lsa - o'sha lidning tarixi.
    Qayerdan kelgani, kim olib kelgani shu yerda ko'rinadi."""
    lead = (
        db.query(models.Lead)
        .filter(models.Lead.converted_student_id == student_id)
        .first()
    )
    if not lead:
        return {"lead": None}
    return {"lead": {
        "id": lead.id,
        "source": lead.source,
        "stage": lead.stage,
        "address": lead.address,
        "school": lead.school,
        "grade": lead.grade,
        "note": lead.note,
        "assigned_user": lead.assigned_user.full_name if lead.assigned_user else None,
        "created_by": lead.created_by,
        "created_at": lead.created_at.isoformat() if lead.created_at else None,
        "updated_at": lead.updated_at.isoformat() if lead.updated_at else None,
    }}

@router.get("/api/students/{student_id}/exams")
def student_exams(
    student_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_STAFF)),
):
    """O'quvchining barcha imtihon natijalari - eng yangisi tepada."""
    rows = (
        db.query(models.ExamResult, models.Exam)
        .join(models.Exam, models.ExamResult.exam_id == models.Exam.id)
        .filter(models.ExamResult.student_id == student_id)
        .order_by(models.Exam.date.desc())
        .all()
    )
    groups = {g.id: g for g in db.query(models.Group).all()}
    out = []
    for r, e in rows:
        g = groups.get(e.group_id)
        out.append({
            "exam_id": e.id, "kind": e.kind, "unit_no": e.unit_no,
            "title": e.title, "date": e.date.isoformat(),
            "max_score": e.max_score,
            "group": g.name if g else None,
            "score": r.score, "band": r.band, "percent": r.percent,
            "coins": r.coins, "absent": bool(r.absent),
        })
    scored = [x for x in out if x["percent"] is not None]
    return {
        "results": out,
        "count": len(scored),
        "avg_percent": round(sum(x["percent"] for x in scored) / len(scored), 1)
        if scored else None,
        "coins": sum(x["coins"] or 0 for x in out),
    }

@router.get("/api/students/{student_id}/attendance")
def student_attendance(
    student_id: int,
    months: int = 6,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_STAFF, roles.HR_MANAGER)),
):
    """O'quvchining davomati va kunlik baholari - oxirgi N oy."""
    months = max(1, min(months, 24))
    today = date.today()
    sy, sm = _shift_month(today.year, today.month, -(months - 1))
    start, _ = billing.month_bounds(sy, sm)

    att = (
        db.query(models.Attendance, models.Lesson)
        .join(models.Lesson, models.Attendance.lesson_id == models.Lesson.id)
        .filter(models.Attendance.student_id == student_id,
                models.Lesson.date >= start)
        .order_by(models.Lesson.date.desc())
        .all()
    )
    grades = {
        g.lesson_id: g.score
        for g in db.query(models.DailyGrade).filter(
            models.DailyGrade.student_id == student_id).all()
    }

    rows = [{
        "date": ls.date.isoformat(),
        "present": bool(a.present),
        "late": a.present == 2,
        "grade": grades.get(ls.id),
        "homework": a.homework,
        "homework_label": roles.HOMEWORK_LABELS.get(a.homework),
        "homework_tone": roles.HOMEWORK_TONE.get(a.homework),
    } for a, ls in att]

    present = sum(1 for r in rows if r["present"])
    scored = [r["grade"] for r in rows if r["grade"]]
    return {
        "rows": rows[:60],
        "marked": len(rows),
        "present": present,
        "absent": len(rows) - present,
        "percent": round(present / len(rows) * 100, 1) if rows else 0,
        "avg_grade": round(sum(scored) / len(scored), 1) if scored else None,
        "homework": _homework_stats(db, student_id, since=start),
    }

@router.get("/api/students/{student_id}/coins", response_model=List[schemas.CoinEntryOut])
def student_coin_history(
    student_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_ACCESS)),
):
    return (
        db.query(models.CoinEntry)
        .filter(models.CoinEntry.student_id == student_id)
        .order_by(models.CoinEntry.created_at.desc(), models.CoinEntry.id.desc())
        .all()
    )

@router.post("/api/students/{student_id}/coins", response_model=schemas.CoinEntryOut)
def add_manual_coins(
    student_id: int,
    payload: schemas.CoinManual,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.COIN_ADMIN)),
):
    """Qo'lda coin berish yoki yechish (tanlov, tadbir, jarima va h.k.)."""
    s = db.query(models.Student).get(student_id)
    if not s:
        raise HTTPException(404, "O'quvchi topilmadi")
    if payload.amount == 0:
        raise HTTPException(400, "Miqdor 0 bo'lishi mumkin emas")
    entry = models.CoinEntry(student_id=student_id, amount=payload.amount,
                             source="manual", note=payload.note,
                             created_by=user.full_name)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry

@router.get("/api/students", response_model=List[schemas.StudentOut])
def list_students(
    q: Optional[str] = None,
    group_id: Optional[int] = None,
    status_filter: Optional[str] = None,
    branch_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    backfill_missing_ids(db, "student", models.Student)
    query = scope_to_branch(db.query(models.Student), models.Student, user,
                            branch_id)
    if q:
        query = query.filter(models.Student.full_name.ilike(f"%{q}%"))
    if group_id:
        query = query.filter(models.Student.group_id == group_id)
    if status_filter:
        query = query.filter(models.Student.status == status_filter)

    # Ustoz faqat O'Z guruhlarining o'quvchilarini ko'radi va balans
    # unga umuman ko'rsatilmaydi: bolaga qarzdorligi orqali emas,
    # o'qishi orqali qaraydi. Pul masalasi — administrator ishi.
    own_only = user.role in tuple(roles.OWN_GROUPS_ONLY)
    if own_only:
        t = _teacher_of_user(db, user)
        gids = [g.id for g in _cabinet_groups(db, user, t)] if t else []
        query = query.filter(models.Student.group_id.in_(gids or [-1]))

    students = query.order_by(models.Student.full_name).all()
    # TEZLIK: balanslar bitta so'rovda (har o'quvchiga alohida so'rov —
    # N+1 — 2-3 ming o'quvchida sahifani sekinlashtirib yuborardi).
    balances = dict(
        db.query(models.Payment.student_id,
                 func.coalesce(func.sum(models.Payment.amount), 0.0))
        .group_by(models.Payment.student_id).all())
    rows = []
    for s in students:
        r = schemas.StudentOut.model_validate(s)
        r.balance = 0.0 if own_only else float(balances.get(s.id, 0) or 0)
        rows.append(r)
    return rows

@router.get("/api/students/{student_id}", response_model=schemas.StudentDetail)
def get_student(
    student_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)
):
    s = db.query(models.Student).get(student_id)
    if not s:
        raise HTTPException(404, "Talaba topilmadi")
    out = schemas.StudentDetail.model_validate(s)
    if user.role in tuple(roles.OWN_GROUPS_ONLY):
        # Ustozga: o'z o'quvchisi bo'lsagina, pulsiz
        if s.group_id:
            _get_group_in_scope(db, s.group_id, user)
        else:
            raise HTTPException(403, "Bu o'quvchi sizga biriktirilmagan")
        out.balance = 0.0
        out.payments = []
        return out
    # FILIAL AUDITI: filialga bog'langan xodim faqat o'z filialini ko'radi
    if not _in_user_branches(db, user, s.branch_id, null_ok=True):
        raise HTTPException(403, "Bu o'quvchi boshqa filialga tegishli")
    out.balance = student_balance(db, s.id)
    out.payments = [schemas.PaymentOut.model_validate(p) for p in s.payments]
    return out

@router.post("/api/students", response_model=schemas.StudentOut)
def create_student(
    payload: schemas.StudentCreate,
    force: bool = False,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_STAFF)),
):
    # DUBLIKAT: bir xil ism-familiyali talaba bo'lsa ogohlantiramiz —
    # adashib ikkinchi karta ochib qo'ymaslik uchun. Yangi (boshqa)
    # odam bo'lsa, tasdiqlab kiritaveradi.
    if not force:
        nm = " ".join((payload.full_name or "").split()).lower()
        same = next(
            (st for st in db.query(models.Student)
             .filter(models.Student.status != "archived").all()
             if " ".join((st.full_name or "").split()).lower() == nm),
            None)
        if same:
            g = db.query(models.Group).get(same.group_id) \
                if same.group_id else None
            joy = f" ({g.name} guruhida)" if g else ""
            raise HTTPException(
                409, f"Bunday ismli talaba allaqachon bor{joy} — "
                     "adashib qayta kiritib qo'ymayapsizmi? Agar bu "
                     "boshqa (yangi) odam bo'lsa, tasdiqlang.")
    data = payload.model_dump()
    if not data.get("enrolled_date"):
        data["enrolled_date"] = date.today()
    s = models.Student(**data)
    db.add(s)
    db.commit()
    db.refresh(s)
    _ensure_public_id(db, "student", s)
    audit.log(db, user, entity="student", action="create", entity_id=s.id,
              entity_label=s.full_name, branch_id=s.branch_id,
              new_value=s.full_name)
    db.commit()
    # AVTOMAT KIRISH HISOBI (2026-08-10, Jahongir so'radi): o'quvchi
    # kiritilishi bilan unga hisob ochiladi — login telefon raqami,
    # parol jonyjony. Alohida "hisob ochish" bosqichi qolmadi.
    # Ota-onaga esa hisob umuman ochilmaydi: u maxsus havola
    # (parent_token) orqali kiradi, u ham shu yerda avtomat turadi.
    _ensure_student_account(db, s)
    db.refresh(s)
    return to_student_out(db, s)

@router.put("/api/students/{student_id}", response_model=schemas.StudentOut)
def update_student(
    student_id: int,
    payload: schemas.StudentUpdate,
    force: bool = False,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_STAFF)),
):
    s = db.query(models.Student).get(student_id)
    if not s:
        raise HTTPException(404, "Talaba topilmadi")
    # Filialga bog'langan xodim boshqa filial o'quvchisini tahrirlamaydi
    if not _in_user_branches(db, user, s.branch_id, null_ok=True):
        raise HTTPException(403, "Bu o'quvchi boshqa filialga tegishli")
    changes = payload.model_dump(exclude_unset=True)

    # Parallel tahrir himoyasi: men ochgan versiyadan keyin boshqa
    # xodim o'zgartirgan bo'lsa — ustidan yozmaymiz.
    expected = changes.pop("expected_updated_at", None)
    if expected is not None:
        server_v = s.updated_at.isoformat() if s.updated_at else ""
        if server_v != expected:
            raise HTTPException(
                409, "Bu kartani shu orada boshqa xodim o'zgartirdi. "
                     "Sahifani yangilab, qaytadan urinib ko'ring.")

    # Yangi guruhga o'tkazilyaptimi - sig'im va daraja tekshiriladi.
    new_gid = changes.get("group_id")
    if new_gid and new_gid != s.group_id:
        g = db.query(models.Group).get(new_gid)
        _raise_if_blocked(_check_enrolment(db, s, g), force=force)
        # O'quvchining darajasi hali yo'q bo'lsa - guruhnikidan olamiz.
        if g and not s.level:
            changes.setdefault("subject", g.subject)
            changes.setdefault("level", g.level)
    # Eski qiymatlar hali joyida turganda yozib olamiz.
    audit.log_changes(db, user, entity="student", obj=s, changes=changes)
    for k, v in changes.items():
        setattr(s, k, v)
    s.updated_at = datetime.utcnow()
    _sync_student_left_date(s)
    db.commit()
    # Hisobi hali yo'q bo'lsa (masalan avval telefon kiritilmagan
    # edi) — endi ochib qo'yamiz. Hisobi bori qayta ochilmaydi.
    _ensure_student_account(db, s)
    db.refresh(s)
    return to_student_out(db, s)

@router.delete("/api/students/{student_id}")
def delete_student(
    student_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FULL_ACCESS)),
):
    s = db.query(models.Student).get(student_id)
    if not s:
        raise HTTPException(404, "Talaba topilmadi")
    audit.log(db, user, entity="student", action="delete", entity_id=s.id,
              entity_label=s.full_name, branch_id=s.branch_id,
              old_value=s.full_name)
    db.delete(s)
    db.commit()
    return {"ok": True}

@router.get("/api/students/{student_id}/payments", response_model=List[schemas.PaymentOut])
def list_payments(
    student_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)
):
    # FILIAL AUDITI: pul tarixi — eng nozik ma'lumot. Ustozga umuman
    # ko'rinmaydi, filialga bog'langan xodimga faqat o'z filiali.
    if user.role in tuple(roles.OWN_GROUPS_ONLY) or \
            user.role in (roles.STUDENT, roles.PARENT):
        raise HTTPException(403, "To'lov tarixi sizga ochiq emas")
    s = db.query(models.Student).get(student_id)
    if not s:
        raise HTTPException(404, "Talaba topilmadi")
    if not _in_user_branches(db, user, s.branch_id, null_ok=True):
        raise HTTPException(403, "Bu o'quvchi boshqa filialga tegishli")
    return (
        db.query(models.Payment)
        .filter(models.Payment.student_id == student_id)
        .order_by(models.Payment.created_at.desc())
        .all()
    )

def _pay_coin(db: Session, s: models.Student,
              payment: models.Payment, today=None) -> None:
    """To'lov sanasiga qarab avtomat coin (Jahongir qoidasi):
    1-5 sana +10, 6-10 sana +5, 11-15 sana +1, 16-oy oxiri 0;
    oldingi oydan QARZ bilan kelib to'lasa (oydan o'tib) -5.

    Oyiga BIR marta: bo'lib-bo'lib to'laganda faqat birinchisiga.
    To'lov o'chirilsa coin ham qaytariladi (finance.delete_payment).
    Eski tizim ham xuddi shu qoidada qo'lda berardi - endi avtomat."""
    if today is None:
        today = roles.local_today()
    # Shu kalendar oyda allaqachon baholanganmi
    month_start = datetime(today.year, today.month, 1)
    if (db.query(models.CoinEntry)
            .filter(models.CoinEntry.student_id == s.id,
                    models.CoinEntry.source == "pay_ontime",
                    models.CoinEntry.created_at >= month_start).first()):
        return
    # Oldingi oylardan qarz: joriy oy avto-hisobini (charge, period=shu
    # oy) chiqarib tashlaganda balans manfiy bo'lsa - o'tgan oy puli
    # hali yopilmagan holda oy o'tib ketgan.
    period = f"{today.year:04d}-{today.month:02d}"
    bal = 0.0
    for p in (db.query(models.Payment)
              .filter(models.Payment.student_id == s.id,
                      models.Payment.id != payment.id).all()):
        if p.kind == "charge" and p.period == period:
            continue
        bal += p.amount or 0
    if bal < -0.5:
        amount, note = -5, "To'lov oydan o'tib qilindi (-5 coin)"
    else:
        d = today.day
        if d <= 5:
            amount, note = 10, "To'lovni 5-sanagacha qildi (+10 coin)"
        elif d <= 10:
            amount, note = 5, "To'lovni 10-sanagacha qildi (+5 coin)"
        elif d <= 15:
            amount, note = 1, "To'lovni 15-sanagacha qildi (+1 coin)"
        else:
            return
    db.add(models.CoinEntry(
        student_id=s.id, amount=amount, source="pay_ontime",
        ref_id=payment.id, note=note, created_by="Avtomat"))


@router.post("/api/students/{student_id}/payments", response_model=schemas.PaymentOut)
def add_payment(
    student_id: int,
    payload: schemas.PaymentCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.CASH_ACCESS)),
):
    s = db.query(models.Student).get(student_id)
    if not s:
        raise HTTPException(404, "Talaba topilmadi")

    # Pul har doim butun so'm — kasr qoldiqlari yig'ilib ketmasin
    amount = roles.money(payload.amount)
    if payload.kind in ("charge", "discount") and amount > 0:
        # charges/discounts reduce balance, so store as negative internally
        amount = -abs(amount)
    elif payload.kind == "payment":
        amount = abs(amount)

    # To'lov usuli faqat haqiqiy kirim uchun ma'noga ega.
    method = None
    if payload.kind == "payment":
        method = payload.method or "cash"
        if method not in roles.PAYMENT_METHODS:
            raise HTTPException(400, "Noto'g'ri to'lov usuli")

    payment = models.Payment(
        student_id=student_id,
        amount=amount,
        kind=payload.kind,
        method=method,
        note=payload.note,
        created_by=user.full_name,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    _ensure_public_id(db, "payment", payment)

    # Chegirma alohida amal sifatida yoziladi - "kim chegirma berdi"
    # degan savolga javob shu yerdan chiqadi.
    act = "discount" if payload.kind == "discount" else "create"
    audit.log(db, user, entity="payment", action=act, entity_id=payment.id,
              entity_label=s.full_name, field=payload.kind,
              new_value=amount, note=payload.note, branch_id=s.branch_id)
    db.commit()

    # AVTOMAT COIN: to'lov sanasiga qarab (5-sanagacha +10, 10 gacha
    # +5, 15 gacha +1; oydan o'tib kelgan qarz uchun -5).
    if payload.kind == "payment" and amount > 0:
        try:
            _pay_coin(db, s, payment)
            db.commit()
        except Exception:
            db.rollback()

    # AVTOMAT: bu o'quvchini kimdir olib kelgan bo'lsa, o'sha odamning
    # referral chegirmasi shu to'lov bilan yoqiladi.
    if payload.kind == "payment":
        if _activate_referrals(db, student_id):
            db.commit()

    # Sinovdagi o'quvchi to'lov qilsa - 3 ta darsni kutmasdan darrov
    # faollashadi, hisob-kitob birinchi kelgan kunidan boshlanadi.
    if payload.kind == "payment" and s.status == "trial":
        if _maybe_auto_activate(db, s, user=user, paid=True):
            db.commit()

    # AVTOMAT ARXIV: guruhdan qarzdorligicha chiqarilgan o'quvchi
    # qarzini to'liq yopgach o'zi arxivga o'tadi.
    if payload.kind == "payment" and getattr(s, "archive_when_paid", 0) \
            and not s.group_id and student_balance(db, s.id) >= 0:
        s.status = "archived"
        s.archive_when_paid = 0
        _sync_student_left_date(s)
        audit.log(db, user, entity="student", action="auto_archive",
                  entity_id=s.id, entity_label=s.full_name, field="status",
                  new_value="archived",
                  note="Qarz to'liq to'landi — avtomat arxivga o'tdi",
                  branch_id=s.branch_id)
        db.commit()

    # Telegram: ota-onaga chek — to'lov qabul qilindi (bog'langan bo'lsa)
    if payload.kind == "payment" and s.telegram_chat_id:
        try:
            bal = student_balance(db, s.id)
            notify.send(
                s.telegram_chat_id,
                f"✅ To'lov qabul qilindi\n{s.full_name}\n"
                f"Summa: {int(amount):,} so'm".replace(",", " ") +
                f"\nQoldiq balans: {int(bal):,} so'm".replace(",", " ") +
                f"\nQabul qildi: {user.full_name}")
        except Exception:
            pass

    db.refresh(payment)
    return payment

@router.post("/api/students/{student_id}/activate")
def activate_student(
    student_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FREEZE_ROLES)),
):
    """Sinovdagi (yoki muzlatilgan) o'quvchini FAOL qiladi.

    Guruhga qo'shilgan o'quvchi avtomat faol bo'lmaydi - avval sinov
    darsida turadi. Faollashtirish shu tugma orqali, ongli ravishda
    bo'ladi: shundan keyingina u hisob-kitobga to'liq kiradi."""
    s = db.query(models.Student).get(student_id)
    if not s:
        raise HTTPException(404, "O'quvchi topilmadi")
    if s.status == "active":
        raise HTTPException(400, "Bu o'quvchi allaqachon faol")
    old = s.status
    s.status = "active"
    # Faollashgan kun - o'qish boshlangan kun deb hisoblanadi.
    if not s.enrolled_date:
        s.enrolled_date = date.today()
    _sync_student_left_date(s)
    audit.log(db, user, entity="student", action="activate", entity_id=s.id,
              entity_label=s.full_name, field="status",
              old_value=old, new_value="active", branch_id=s.branch_id)
    db.commit()
    return {"ok": True, "status": s.status}

@router.post("/api/students/{student_id}/move-group")
def move_student_group(
    student_id: int,
    payload: schemas.StudentGroupMove,
    force: bool = False,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FREEZE_ROLES)),
):
    """Boshqa guruhga o'tkazadi. group_id bo'sh bo'lsa - guruhdan
    chiqaradi, lekin o'quvchi bazada qoladi (to'lov tarixi saqlanadi)."""
    s = db.query(models.Student).get(student_id)
    if not s:
        raise HTTPException(404, "O'quvchi topilmadi")

    if payload.group_id is None:
        # Guruhdan chiqarish endi ALOHIDA endpoint orqali - sabab
        # majburiy va arxiv qoidalari ishlaydi.
        raise HTTPException(
            400, "Guruhdan chiqarish uchun sabab ko'rsatilishi shart — "
                 "'Guruhdan chiqarish' amalidan foydalaning")

    g = _get_group_in_scope(db, payload.group_id, user)
    if g.id == s.group_id:
        raise HTTPException(400, "O'quvchi allaqachon shu guruhda")
    # Sig'im va daraja mosligi - saqlashdan OLDIN tekshiriladi.
    _raise_if_blocked(_check_enrolment(db, s, g), force=force)
    # Darajasi hali yo'q bo'lsa - guruhnikidan olamiz.
    if not s.level:
        s.subject = s.subject or g.subject
        s.level = g.level
    audit.log(db, user, entity="student", action="group_move", entity_id=s.id,
              entity_label=s.full_name, field="group",
              old_value=s.group.name if s.group else None, new_value=g.name,
              branch_id=s.branch_id)
    s.group_id = g.id
    # Filial guruh bilan birga o'zgaradi - aks holda hisobotlar chalkashadi.
    if g.branch_id:
        s.branch_id = g.branch_id
    db.commit()
    return {"ok": True, "group_id": g.id, "group": g.name}

@router.post("/api/students/{student_id}/remove-from-group")
def remove_student_from_group(
    student_id: int,
    payload: schemas.RemoveFromGroupIn,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FREEZE_ROLES)),
):
    """Guruhdan chiqarish — sabab MAJBURIY (ustozlar nima uchun ketganini
    bilishi uchun). Qoidalar:
      - qarzi YO'Q  -> darhol arxivga tushadi;
      - qarzi BOR   -> arxivga tushmaydi, "guruhsiz" bo'lib faol qoladi;
        qarz to'liq to'langach AVTOMAT arxivga o'tadi."""
    s = db.query(models.Student).get(student_id)
    if not s:
        raise HTTPException(404, "O'quvchi topilmadi")
    if not s.group_id:
        raise HTTPException(400, "O'quvchi hech qaysi guruhda emas")
    reason = (payload.reason or "").strip()
    if len(reason) < 3:
        raise HTTPException(400, "Chiqarish sababi majburiy — "
                                 "kamida bir necha so'z yozing")

    old_group = s.group.name if s.group else None
    bal = student_balance(db, s.id)
    s.group_id = None

    if bal < 0:
        # Qarzdor: arxivga EMAS — ro'yxatda guruhsiz turadi,
        # qarzi yopilgach avtomat arxivlanadi.
        s.archive_when_paid = 1
        debt = int(-bal)
        note = (f"Sabab: {reason} · Qarzi bor "
                f"({debt:,} so'm) — to'langach avtomat arxivga o'tadi"
                .replace(",", " "))
        archived = False
    else:
        s.status = "archived"
        s.archive_when_paid = 0
        _sync_student_left_date(s)
        note = f"Sabab: {reason} · Arxivga o'tkazildi"
        archived = True

    audit.log(db, user, entity="student", action="group_remove",
              entity_id=s.id, entity_label=s.full_name, field="group",
              old_value=old_group, new_value=None, note=note,
              branch_id=s.branch_id)
    db.commit()
    return {"ok": True, "archived": archived,
            "debt": int(-bal) if bal < 0 else 0}

@router.post("/api/students/{student_id}/restore")
def restore_student(
    student_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FREEZE_ROLES)),
):
    """Arxivdagi o'quvchini qayta tiklaydi — o'quvchilar qaytib kelishi
    mumkin. Holati FAOL bo'ladi, guruh esa bo'sh qoladi: keyin qo'lda
    kerakli guruhga qo'shiladi."""
    s = db.query(models.Student).get(student_id)
    if not s:
        raise HTTPException(404, "O'quvchi topilmadi")
    if s.status != "archived":
        raise HTTPException(400, "Bu o'quvchi arxivda emas")
    s.status = "active"
    s.archive_when_paid = 0
    _sync_student_left_date(s)
    audit.log(db, user, entity="student", action="restore", entity_id=s.id,
              entity_label=s.full_name, field="status",
              old_value="archived", new_value="active",
              note="Arxivdan qayta tiklandi", branch_id=s.branch_id)
    db.commit()
    return {"ok": True, "status": s.status}

@router.get("/api/students/{student_id}/talks")
def list_talks(
    student_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_STAFF)),
):
    rows = (db.query(models.ParentTalk)
            .filter(models.ParentTalk.student_id == student_id)
            .order_by(models.ParentTalk.date.desc()).all())
    return [{"id": t.id, "date": t.date.isoformat() if t.date else None,
             "channel": t.channel, "topic": t.topic, "summary": t.summary,
             "outcome": t.outcome, "created_by": t.created_by} for t in rows]

@router.post("/api/students/{student_id}/talks")
def add_talk(
    student_id: int,
    payload: schemas.ParentTalkCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_STAFF)),
):
    data = payload.model_dump()
    data["date"] = data.get("date") or date.today()
    t = models.ParentTalk(student_id=student_id, **data,
                          created_by=user.full_name)
    db.add(t); db.commit(); db.refresh(t)
    audit.log(db, user, entity="student", action="update", entity_id=student_id,
              field="parent_talk", new_value=t.topic, note=t.summary,
              commit=True)
    return {"id": t.id}

@router.get("/api/students/{student_id}/certificates")
def list_certificates(
    student_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_STAFF)),
):
    rows = (db.query(models.Certificate)
            .filter(models.Certificate.student_id == student_id)
            .order_by(models.Certificate.date.desc()).all())
    return [{"id": c.id, "kind": c.kind,
             "kind_label": roles.CERTIFICATE_KIND_LABELS.get(c.kind, c.kind),
             "level": c.level, "score": c.score,
             "date": c.date.isoformat() if c.date else None,
             "note": c.note} for c in rows]

@router.post("/api/students/{student_id}/certificates")
def add_certificate(
    student_id: int,
    payload: schemas.CertificateCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.ACADEMIC_VIEW)),
):
    data = payload.model_dump()
    data["date"] = data.get("date") or date.today()
    c = models.Certificate(student_id=student_id, **data,
                           created_by=user.full_name)
    db.add(c); db.commit(); db.refresh(c)
    audit.log(db, user, entity="student", action="update", entity_id=student_id,
              field="certificate",
              new_value=f"{roles.CERTIFICATE_KIND_LABELS.get(c.kind, c.kind)} "
                        f"{c.level or ''}".strip(), commit=True)
    # AVTOMAT: SMM'ga video olish vazifasi - hamma ma'lumoti bilan
    st = db.query(models.Student).get(student_id)
    if st:
        _smm_achievement_task(
            db, st,
            what=f"{roles.CERTIFICATE_KIND_LABELS.get(c.kind, c.kind)}"
                 + (f" — {c.level}" if c.level else ""),
            detail=(f"Bali: {c.score}" if c.score else ""))
        db.commit()
    return {"id": c.id}

_STATUS_EVENT = {
    "frozen": ("freeze", "O'qish muzlatildi"),
    "archived": ("leave", "O'qishdan chiqdi"),
    "active": ("return", "Qayta tiklandi"),
    "trial": ("trial", "Sinov darsiga o'tdi"),
}

@router.get("/api/students/{student_id}/history")
def student_history(
    student_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_STAFF)),
):
    """O'quvchining butun yo'li: qaysi guruhlarda, qaysi ustozlarda
    o'qigan, necha marta guruh almashtirgan, qancha dars qoldirgan,
    shikoyatlar, ota-ona bilan suhbatlar, muzlatish va qaytish."""
    s = db.query(models.Student).get(student_id)
    if not s:
        raise HTTPException(404, "O'quvchi topilmadi")

    logs = (db.query(models.AuditLog)
            .filter(models.AuditLog.entity == "student",
                    models.AuditLog.entity_id == student_id)
            .order_by(models.AuditLog.created_at).all())

    # --- Guruh va ustoz tarixi ---
    group_moves = [l for l in logs if l.action in ("group_move", "group_remove")]
    groups_seen, teachers_seen, timeline = [], [], []

    def seen(lst, name):
        if name and name not in lst:
            lst.append(name)

    teacher_by_group = {g.name: (g.teacher.full_name if g.teacher else None)
                        for g in db.query(models.Group).all()}

    for l in group_moves:
        seen(groups_seen, l.old_value)
        seen(groups_seen, l.new_value)
        seen(teachers_seen, teacher_by_group.get(l.old_value or ""))
        seen(teachers_seen, teacher_by_group.get(l.new_value or ""))
        _detail = f"{l.old_value or '—'} → {l.new_value or '—'}"
        # Chiqarish sababi tarixda ko'rinadi — ustozlar o'quvchi nega
        # ketganini shu yerdan biladi.
        if l.note:
            _detail += f" · {l.note}"
        timeline.append({
            "date": l.created_at.isoformat() if l.created_at else None,
            "kind": "group",
            "title": "Guruhdan chiqarildi" if l.action == "group_remove"
                     else "Guruh almashtirildi",
            "detail": _detail,
            "by": l.user_name,
        })

    if s.group:
        seen(groups_seen, s.group.name)
        seen(teachers_seen, s.group.teacher.full_name if s.group.teacher else None)

    # --- Holat o'zgarishlari: muzlatish / chiqish / qaytish ---
    freezes = leaves = returns = 0
    for l in logs:
        if l.field != "status" and l.action != "activate":
            continue
        new = l.new_value
        if new not in _STATUS_EVENT:
            continue
        kind, title = _STATUS_EVENT[new]
        # "active" ga qaytish - faqat oldin muzlatilgan/ketgan bo'lsa
        if kind == "return":
            if l.old_value not in ("frozen", "archived"):
                continue
            returns += 1
        elif kind == "freeze":
            freezes += 1
        elif kind == "leave":
            leaves += 1
        timeline.append({
            "date": l.created_at.isoformat() if l.created_at else None,
            "kind": kind, "title": title,
            "detail": f"{l.old_value or '—'} → {new}",
            "by": l.user_name,
        })

    # --- Davomat ---
    att = (db.query(models.Attendance, models.Lesson)
           .join(models.Lesson, models.Attendance.lesson_id == models.Lesson.id)
           .filter(models.Attendance.student_id == student_id).all())
    marked = len(att)
    absent = sum(1 for a, _l in att if not a.present)
    absent_dates = sorted(
        (l.date.isoformat() for a, l in att if not a.present), reverse=True)

    # --- Shikoyatlar ---
    comps = (db.query(models.Complaint)
             .filter(models.Complaint.student_id == student_id)
             .order_by(models.Complaint.created_at.desc()).all())
    for c in comps:
        timeline.append({
            "date": c.created_at.isoformat() if c.created_at else None,
            "kind": "complaint",
            "title": "Shikoyat: " + c.subject,
            "detail": c.resolution or c.body,
            "by": c.created_by,
        })

    # --- Ota-ona suhbatlari ---
    talks = (db.query(models.ParentTalk)
             .filter(models.ParentTalk.student_id == student_id)
             .order_by(models.ParentTalk.date.desc()).all())
    for t in talks:
        timeline.append({
            "date": t.date.isoformat() if t.date else None,
            "kind": "talk",
            "title": "Ota-ona bilan suhbat: " + t.topic,
            "detail": t.summary,
            "by": t.created_by,
        })

    # --- Sertifikatlar ---
    certs = (db.query(models.Certificate)
             .filter(models.Certificate.student_id == student_id).all())
    for c in certs:
        timeline.append({
            "date": c.date.isoformat() if c.date else None,
            "kind": "certificate",
            "title": "Sertifikat: "
                     + roles.CERTIFICATE_KIND_LABELS.get(c.kind, c.kind),
            "detail": c.level or (str(c.score) if c.score else None),
            "by": c.created_by,
        })

    timeline.sort(key=lambda x: x["date"] or "", reverse=True)

    # --- Platformadagi BOSHQA BARCHA amallar (audit) ---
    # Yuqorida maxsus ko'rinishda chiqarilganlari takrorlanmaydi.
    handled = {"group_move", "group_remove"}
    ACTION_UZ = {
        "create": "Yaratildi", "update": "Tahrirlandi",
        "freeze": "Muzlatildi", "auto_freeze": "Avtomuzlatildi",
        "activate": "Faollashtirildi", "to_trial": "Sinovga qaytarildi",
        "to_lead": "Lidga qaytarildi", "archive": "Arxivlandi",
        "delete": "O'chirildi",
        "group_remove": "Guruhdan chiqarildi",
        "group_move": "Guruh almashtirildi",
        "auto_archive": "Qarz to'landi — avtomat arxivlandi",
        "restore": "Arxivdan qayta tiklandi",
    }
    for l in logs:
        if l.action in handled:
            continue
        if l.field == "status" or l.action == "activate":
            pass  # holat o'zgarishlari ham ko'rinsin
        detail = ""
        if l.old_value or l.new_value:
            detail = f"{l.old_value or '—'} → {l.new_value or '—'}"
        if l.note:
            detail = (detail + " · " if detail else "") + l.note
        timeline.append({
            "date": l.created_at.isoformat() if l.created_at else None,
            "kind": "audit",
            "title": ACTION_UZ.get(l.action, l.action)
                     + (f" ({l.field})" if l.field else ""),
            "detail": detail or None,
            "by": l.user_name,
        })
    # To'lov amallari ham shu bolaga tegishli bo'lsa — tarixga
    pay_ids = [pid for (pid,) in db.query(models.Payment.id).filter(
        models.Payment.student_id == student_id).all()]
    if pay_ids:
        for l in (db.query(models.AuditLog)
                  .filter(models.AuditLog.entity == "payment",
                          models.AuditLog.entity_id.in_(pay_ids))
                  .order_by(models.AuditLog.created_at).all()):
            timeline.append({
                "date": l.created_at.isoformat() if l.created_at else None,
                "kind": "payment",
                "title": f"To'lov amali: {l.action}",
                "detail": (l.new_value or "") + (
                    f" · {l.note}" if l.note else "") or None,
                "by": l.user_name,
            })
    timeline.sort(key=lambda e: e["date"] or "", reverse=True)

    return {
        "summary": {
            "groups": groups_seen,
            "group_count": len(groups_seen),
            "teachers": [t for t in teachers_seen if t],
            "group_changes": len([l for l in group_moves
                                  if l.action == "group_move"]),
            "marked_lessons": marked,
            "absences": absent,
            "attendance_percent": round((marked - absent) / marked * 100, 1)
                                  if marked else None,
            "complaints": len(comps),
            "talks": len(talks),
            "certificates": len(certs),
            "freezes": freezes,
            "leaves": leaves,
            "returns": returns,
        },
        "absent_dates": absent_dates[:30],
        "timeline": timeline,
    }

@router.get("/api/students/{student_id}/discounts")
def student_discounts(
    student_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_STAFF)),
):
    _expire_discounts(db)
    s = db.query(models.Student).get(student_id)
    if not s:
        raise HTTPException(404, "O'quvchi topilmadi")
    rows = (db.query(models.Discount)
            .filter(models.Discount.student_id == student_id)
            .order_by(models.Discount.created_at.desc()).all())
    fam = _family_discount_percent(db, s)
    return {
        "rows": [_discount_out(db, d) for d in rows],
        "family_percent": fam,
        "total_percent": _student_discount_percent(db, s),
        "max_percent": roles.MAX_TOTAL_DISCOUNT_PERCENT,
        "can_approve": user.role in roles.DISCOUNT_APPROVE,
        "types": [{"key": k, "label": lbl, "hint": h}
                  for k, lbl, h in roles.DISCOUNT_TYPES
                  if k not in roles.AUTO_DISCOUNT_TYPES],
    }

@router.get("/api/students/{student_id}/pricing")
def student_pricing(
    student_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_STAFF)),
):
    """O'quvchining oylik narxi va unga tegishli chegirmalar."""
    s = db.query(models.Student).get(student_id)
    if not s:
        raise HTTPException(404, "O'quvchi topilmadi")

    base = s.group.monthly_fee if s.group else 0.0
    fam = _family_discount_percent(db, s)

    # Shartnomadagi shaxsiy chegirma (agar bo'lsa)
    contract = (db.query(models.Contract)
                .filter(models.Contract.student_id == student_id,
                        models.Contract.status == "active")
                .order_by(models.Contract.date.desc()).first())
    personal = contract.discount_percent if contract else 0.0
    if contract and contract.monthly_fee:
        base = contract.monthly_fee

    siblings = []
    if s.parent_id:
        siblings = [{"id": x.id, "full_name": x.full_name, "status": x.status}
                    for x in db.query(models.Student).filter(
                        models.Student.parent_id == s.parent_id,
                        models.Student.id != s.id).all()]

    total_pct = min(100.0, fam + personal)
    return {
        "base_fee": base,
        "family_discount": fam,
        "family_min_children": roles.FAMILY_DISCOUNT_MIN_CHILDREN,
        "personal_discount": personal,
        "total_discount": total_pct,
        "final_fee": round(base * (100 - total_pct) / 100, 2),
        "parent_id": s.parent_id,
        "siblings": siblings,
        "active_siblings": sum(1 for x in siblings if x["status"] == "active"),
        # Chegirma qanday paydo bo'lgani va qachon yo'qolishi
        "explanation": (
            f"Oilada {sum(1 for x in siblings if x['status'] == 'active') + (1 if s.status == 'active' else 0)} "
            f"ta faol farzand — {roles.FAMILY_DISCOUNT_PERCENT}% oilaviy chegirma. "
            f"Biri o'qishni to'xtatsa chegirma avtomat yo'qoladi."
            if fam else
            (f"Oilaviy chegirma uchun kamida "
             f"{roles.FAMILY_DISCOUNT_MIN_CHILDREN} ta faol farzand kerak."
             if s.parent_id else
             "Ota-ona biriktirilmagan — oilaviy chegirma hisoblanmaydi.")
        ),
    }

@router.get("/api/students/{student_id}/trial")
def student_trial_status(
    student_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_STAFF)),
):
    """Sinov holati: nechta darsga keldi, faollashishga qancha qoldi."""
    s = db.query(models.Student).get(student_id)
    if not s:
        raise HTTPException(404, "O'quvchi topilmadi")
    days = _trial_attendance(db, s.id)
    need = roles.TRIAL_LESSONS_TO_ACTIVATE
    return {
        "status": s.status,
        "attended": len(days),
        "need": need,
        "left": max(0, need - len(days)),
        "dates": [d.isoformat() for d in days],
        "first_date": days[0].isoformat() if days else None,
    }

@router.get("/api/archive/students")
def archive_students(
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_STAFF)),
):
    """Ketgan o'quvchilar - pul munosabati bo'yicha uch guruhda.

    Bu shunchaki ro'yxat emas: kimdan pul olish kerakligi va kimga
    qaytarish kerakligi ko'rinib turishi kerak, aks holda ketgan
    o'quvchining qarzi unutilib ketadi."""
    sq = scope_to_branch(db.query(models.Student), models.Student, user,
                         branch_id).filter(models.Student.status == "archived")
    rows = []
    for s in sq.all():
        bal = student_balance(db, s.id)
        if bal < -0.01:
            grp = "debtor"
        elif bal > 0.01:
            grp = "credit"
        else:
            grp = "clear"
        rows.append({
            "id": s.id, "public_id": s.public_id, "full_name": s.full_name,
            "phone": s.phone, "parent_phone": s.parent_phone,
            "group": s.group.name if s.group else None,
            "branch": s.branch.name if s.branch else None,
            "enrolled_date": s.enrolled_date.isoformat() if s.enrolled_date else None,
            "left_date": s.left_date.isoformat() if s.left_date else None,
            "months": (_months_between(s.enrolled_date, s.left_date or date.today())
                       if s.enrolled_date else None),
            "balance": round(bal, 2),
            "amount": round(abs(bal), 2),
            "group_key": grp,
        })
    rows.sort(key=lambda r: (-r["amount"], r["full_name"]))

    groups = []
    for key, label, hint in roles.ARCHIVE_GROUPS:
        part = [r for r in rows if r["group_key"] == key]
        groups.append({
            "key": key, "label": label, "hint": hint,
            "count": len(part),
            "total": round(sum(r["amount"] for r in part), 2),
        })
    return {"groups": groups, "rows": rows, "total": len(rows)}

@router.get("/api/archive/staff")
def archive_staff(
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.STAFF_VIEWERS)),
):
    """Ishdan bo'shagan xodimlar - qanday ajrashilgani bo'yicha.
    Qayta ishga olish masalasida shu ro'yxat hal qiluvchi."""
    q = scope_to_branch(db.query(models.User), models.User, user).filter(
        models.User.is_active == 0)
    rows = [{
        "id": u.id, "kind": "user",
        "public_id": u.public_id, "full_name": u.full_name,
        "username": u.username, "role": u.role,
        "role_label": roles.UZ_LABELS.get(u.role, u.role),
        "branch": u.branch.name if u.branch else None,
        "exit_type": u.exit_type or "neutral",
        "exit_label": roles.EXIT_TYPE_LABELS.get(u.exit_type or "neutral",
                                                 "Neytral"),
        "exit_reason": u.exit_reason,
        "exit_date": u.exit_date.isoformat() if u.exit_date else None,
    } for u in q.all()]
    # Hisob ochilmagan, ishdan ketgan USTOZ KARTALARI ham arxivda
    # ko'rinadi — O'qituvchilar bo'limida "ketgan" bo'lib yotmaydi.
    tq = scope_to_branch(db.query(models.Teacher), models.Teacher,
                         user).filter(models.Teacher.is_active == 0,
                                      models.Teacher.user_id.is_(None))
    for t in tq.all():
        rows.append({
            "id": -t.id, "kind": "teacher", "teacher_id": t.id,
            "public_id": None, "full_name": t.full_name,
            "username": "ustoz kartasi", "role": "teacher",
            "role_label": "O'qituvchi",
            "branch": t.branch.name if t.branch else None,
            "exit_type": "neutral",
            "exit_label": roles.EXIT_TYPE_LABELS.get("neutral", "Neytral"),
            "exit_reason": None,
            "exit_date": t.left_date.isoformat() if t.left_date else None,
        })
    rows.sort(key=lambda r: (r["exit_date"] or "", r["full_name"]), reverse=True)

    groups = []
    for key, label, hint in roles.EXIT_TYPES:
        groups.append({
            "key": key, "label": label, "hint": hint,
            "count": sum(1 for r in rows if r["exit_type"] == key),
        })
    return {"groups": groups, "rows": rows, "total": len(rows)}

@router.put("/api/archive/staff/{user_id}")
def set_exit_type(
    user_id: int,
    payload: schemas.ExitTypeUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.HR_ACCESS)),
):
    u = db.query(models.User).get(user_id)
    if not u:
        raise HTTPException(404, "Xodim topilmadi")
    if payload.exit_type not in roles.EXIT_TYPE_LABELS:
        raise HTTPException(400, "Noma'lum toifa")
    old = u.exit_type
    u.exit_type = payload.exit_type
    u.exit_reason = payload.exit_reason
    if not u.exit_date:
        u.exit_date = date.today()
    audit.log(db, user, entity="user", action="update", entity_id=u.id,
              entity_label=u.full_name, field="exit_type",
              old_value=old, new_value=u.exit_type, note=payload.exit_reason,
              branch_id=u.branch_id, commit=True)
    return {"ok": True}

@router.get("/api/students/{student_id}/debt-contacts")
def student_debt_contacts(
    student_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.DEBTOR_ACCESS)),
):
    rows = (db.query(models.DebtorContact)
            .filter(models.DebtorContact.student_id == student_id)
            .order_by(models.DebtorContact.contacted_on.desc()).all())
    return [{
        "id": c.id,
        "date": c.contacted_on.isoformat() if c.contacted_on else None,
        "result": c.result,
        "result_label": roles.DEBT_CONTACT_LABELS.get(c.result, c.result),
        "tone": roles.DEBT_CONTACT_TONE.get(c.result, "slate"),
        "promised_date": c.promised_date.isoformat() if c.promised_date else None,
        "promised_amount": c.promised_amount,
        "note": c.note,
        "by": c.created_by,
    } for c in rows]

@router.post("/api/students/{student_id}/leave-reason")
def set_leave_reason(
    student_id: int,
    payload: schemas.LeaveReasonCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_STAFF)),
):
    s = db.query(models.Student).get(student_id)
    if not s:
        raise HTTPException(404, "O'quvchi topilmadi")
    if payload.reason not in roles.LEAVE_REASON_LABELS:
        raise HTTPException(400, "Noto'g'ri sabab")
    g = db.query(models.Group).get(s.group_id) if s.group_id else None
    row = models.LeaveReason(
        student_id=s.id, reason=payload.reason, note=payload.note,
        group_id=s.group_id, teacher_id=g.teacher_id if g else None,
        left_date=s.left_date or date.today(),
        created_by=user.full_name)
    db.add(row); db.commit()
    audit.log(db, user, entity="student", action="update", entity_id=s.id,
              entity_label=s.full_name, branch_id=s.branch_id,
              field="Ketish sababi",
              new_value=roles.LEAVE_REASON_LABELS[payload.reason],
              commit=True)
    return {"ok": True}

def _activate_referrals(db: Session, student_id: int) -> int:
    """AVTOMAT: bu o'quvchi to'lov qilgan bo'lsa, uni olib kelgan
    odamning chegirmasini yoqadi."""
    rows = (db.query(models.Discount)
            .filter(models.Discount.kind == "referral",
                    models.Discount.referrer_student_id == student_id,
                    models.Discount.status == "pending").all())
    n = 0
    for d in rows:
        d.status = "active"
        d.approved_by = "Tizim (do'sti to'lov qildi)"
        d.approved_at = datetime.utcnow()
        n += 1
    return n

@router.post("/api/students/{student_id}/link-account")
def link_student_account(
    student_id: int,
    payload: schemas.LinkAccount,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.USER_ADMIN)),
):
    """O'quvchiga kirish hisobi ochish. Shundan keyin u kirib coin
    balansini ko'radi va sovg'a so'ray oladi."""
    s = db.query(models.Student).get(student_id)
    if not s:
        raise HTTPException(404, "O'quvchi topilmadi")
    if db.query(models.User).filter(
            models.User.username == payload.username).first():
        raise HTTPException(400, "Bu login band")
    if not roles.password_ok(payload.password):
        raise HTTPException(400, roles.PASSWORD_RULE_TEXT)

    u = models.User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        full_name=s.full_name,
        role=roles.STUDENT,
        branch_id=s.branch_id,
    )
    db.add(u); db.commit(); db.refresh(u)
    s.user_id = u.id
    db.commit()
    audit.log(db, user, entity="student", action="update", entity_id=s.id,
              entity_label=s.full_name, branch_id=s.branch_id,
              field="Kirish hisobi", new_value=payload.username, commit=True)
    return {"user_id": u.id, "username": u.username}

@router.get("/api/students/{student_id}/gamification")
def student_gamification(
    student_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    s = db.query(models.Student).get(student_id)
    if not s:
        raise HTTPException(404, "O'quvchi topilmadi")
    mine = _student_of_user(db, user)
    if user.role in (roles.STUDENT, roles.PARENT):
        if not mine or mine.id != s.id:
            raise HTTPException(403, "Bu ma'lumot sizga ko'rinmaydi")
    elif user.role not in roles.XP_VIEW:
        raise HTTPException(403, "Ruxsat yo'q")
    return _student_gamification(db, s)

@router.post("/api/students/{student_id}/freeze")
def freeze_student(student_id: int, payload: schemas.FreezeIn,
                   db: Session = Depends(get_db),
                   user=Depends(require_role(*roles.FREEZE_ROLES))):
    """O'quvchini muzlatish. Qaytish sanasi MAJBURIY — shu sanada
    adminlarga 'aloqaga chiqing' vazifasi tushadi."""
    st = db.query(models.Student).get(student_id)
    if not st:
        raise HTTPException(404, "O'quvchi topilmadi")
    if payload.until <= roles.local_today():
        raise HTTPException(400, "Qaytish sanasi kelajakda bo'lishi kerak")
    st.status = "frozen"
    st.frozen_until = payload.until
    st.frozen_note = payload.note
    _freeze_task(db, st, payload.until, payload.note)
    db.commit()
    audit.log(db, user, entity="student", action="freeze",
              entity_id=st.id, entity_label=st.full_name,
              new_value=f"qaytishi: {payload.until.isoformat()}",
              note=payload.note, commit=True)
    return {"ok": True}

@router.post("/api/students/{student_id}/to-trial")
def student_to_trial(student_id: int, db: Session = Depends(get_db),
                     user=Depends(require_role(*roles.FREEZE_ROLES))):
    """Faol o'quvchini sinov darsiga qaytarish."""
    st = db.query(models.Student).get(student_id)
    if not st:
        raise HTTPException(404, "O'quvchi topilmadi")
    if st.status != "active":
        raise HTTPException(400, "Faqat faol o'quvchi sinovga qaytariladi")
    st.status = "trial"
    db.commit()
    audit.log(db, user, entity="student", action="to_trial",
              entity_id=st.id, entity_label=st.full_name, commit=True)
    return {"ok": True}

@router.post("/api/students/{student_id}/to-lead")
def student_to_lead(student_id: int, db: Session = Depends(get_db),
                    user=Depends(require_role(*roles.FREEZE_ROLES))):
    """Faollashtirilmagan (sinovdagi) talabani lidlar doskasiga
    qaytarish."""
    st = db.query(models.Student).get(student_id)
    if not st:
        raise HTTPException(404, "O'quvchi topilmadi")
    if st.status != "trial":
        raise HTTPException(
            400, "Faqat faollashtirilmagan (sinovdagi) talaba lidga "
                 "qaytariladi")
    lead = db.query(models.Lead).filter(
        models.Lead.converted_student_id == st.id).first()
    if lead:
        lead.stage = "trial_scheduled"
        lead.converted_student_id = None
    else:
        db.add(models.Lead(full_name=st.full_name, phone=st.phone,
                           source="other", stage="trial_scheduled",
                           branch_id=st.branch_id,
                           note="O'quvchilar ro'yxatidan qaytarildi",
                           created_by=user.full_name))
    st.status = "archived"
    st.note = ((st.note + " · ") if st.note else "") + "Lidga qaytarildi"
    db.commit()
    audit.log(db, user, entity="student", action="to_lead",
              entity_id=st.id, entity_label=st.full_name, commit=True)
    return {"ok": True}

@router.get("/api/students/{student_id}/purchases")
def student_purchases(student_id: int, db: Session = Depends(get_db),
                      user=Depends(require_role(*roles.TEACHING_STAFF))):
    """Coin do'konidan qilingan xaridlar ro'yxati."""
    if not db.query(models.Student).get(student_id):
        raise HTTPException(404, "O'quvchi topilmadi")
    rewards = {r.id: r for r in db.query(models.Reward).all()}
    rows = (db.query(models.RewardRedemption)
            .filter(models.RewardRedemption.student_id == student_id)
            .order_by(models.RewardRedemption.id.desc()).all())
    ST = {"given": "berildi", "pending": "kutilmoqda",
          "approved": "tasdiqlandi", "rejected": "rad etildi",
          "cancelled": "bekor"}
    return {"purchases": [{
        "id": r.id,
        "reward": rewards[r.reward_id].name
        if r.reward_id in rewards else "—",
        "coins": r.coins,
        "value_som": rewards[r.reward_id].value_som
        if r.reward_id in rewards else None,
        "status": ST.get(r.status, r.status),
        "by_student": bool(r.requested_by_student),
        "date": r.given_at.date().isoformat() if r.given_at else None,
    } for r in rows],
        "total_coins": sum(r.coins or 0 for r in rows
                           if r.status != "rejected")}

@router.get("/api/students/{student_id}/reminders")
def student_reminders(student_id: int, db: Session = Depends(get_db),
                      user=Depends(require_role(*roles.TEACHING_STAFF))):
    rows = (db.query(models.StudentReminder)
            .filter(models.StudentReminder.student_id == student_id)
            .order_by(models.StudentReminder.done,
                      models.StudentReminder.remind_on.is_(None),
                      models.StudentReminder.remind_on,
                      models.StudentReminder.id.desc()).all())
    return {"reminders": [{
        "id": r.id, "text": r.text,
        "remind_on": r.remind_on.isoformat() if r.remind_on else None,
        "done": bool(r.done), "created_by": r.created_by,
        "date": r.created_at.date().isoformat() if r.created_at else None,
        "overdue": bool(r.remind_on and not r.done
                        and r.remind_on <= roles.local_today()),
    } for r in rows]}

@router.post("/api/students/{student_id}/reminders")
def add_student_reminder(student_id: int, payload: schemas.ReminderIn,
                         db: Session = Depends(get_db),
                         user=Depends(require_role(*roles.TEACHING_STAFF))):
    """Eslatma qo'shish. Sana ko'rsatilsa — o'sha kuni admin va sotuv
    menejeriga vazifa tushadi."""
    st = db.query(models.Student).get(student_id)
    if not st:
        raise HTTPException(404, "O'quvchi topilmadi")
    if not (payload.text or "").strip():
        raise HTTPException(400, "Eslatma matnini yozing")
    r = models.StudentReminder(
        student_id=student_id, text=payload.text.strip(),
        remind_on=payload.remind_on, created_by=user.full_name)
    db.add(r)
    if payload.remind_on:
        days = max((payload.remind_on - roles.local_today()).days, 1)
        _hr_task(db, title=f"Eslatma: {st.full_name}",
                 body=f"{payload.text.strip()} — {user.full_name} "
                      f"qoldirgan eslatma.",
                 to_roles=[roles.ADMINISTRATOR, roles.SALES_MANAGER],
                 branch_id=st.branch_id, days=days, priority="normal")
    db.commit()
    audit.log(db, user, entity="student", action="reminder",
              entity_id=st.id, entity_label=st.full_name,
              new_value=payload.text.strip()[:80],
              note=payload.remind_on.isoformat()
              if payload.remind_on else None, commit=True)
    return {"ok": True, "id": r.id}

@router.post("/api/students/{student_id}/reminders/{rid}/toggle")
def toggle_student_reminder(student_id: int, rid: int,
                            db: Session = Depends(get_db),
                            user=Depends(require_role(
                                *roles.TEACHING_STAFF))):
    r = db.query(models.StudentReminder).get(rid)
    if not r or r.student_id != student_id:
        raise HTTPException(404, "Eslatma topilmadi")
    r.done = 0 if r.done else 1
    db.commit()
    return {"ok": True, "done": bool(r.done)}

def _tg_gen_code(db: Session, s: models.Student) -> str:
    if not s.tg_code:
        import secrets as _sec
        s.tg_code = f"S{s.id}{_sec.token_hex(2).upper()}"
        db.commit()
    return s.tg_code

@router.get("/api/students/{student_id}/telegram")
def student_telegram(student_id: int, db: Session = Depends(get_db),
                     user=Depends(require_role(*roles.CASH_ACCESS))):
    """O'quvchi kartasidagi Telegram bo'lagi: ulanganmi, kod qanday."""
    s = db.query(models.Student).get(student_id)
    if not s:
        raise HTTPException(404, "O'quvchi topilmadi")
    if not notify.enabled():
        return {"enabled": False}
    return {
        "enabled": True,
        "linked": bool(s.telegram_chat_id),
        "code": _tg_gen_code(db, s),
        "bot": notify.bot_info(),
    }

@router.post("/api/students/{student_id}/notify-debt")
def notify_debt(student_id: int, db: Session = Depends(get_db),
                user=Depends(require_role(*roles.CASH_ACCESS))):
    """Qarzdorlik eslatmasi — admin tugma bosganda ota-onaga boradi."""
    s = db.query(models.Student).get(student_id)
    if not s:
        raise HTTPException(404, "O'quvchi topilmadi")
    if not s.telegram_chat_id:
        return {"sent": False, "reason": "Telegram ulanmagan"}
    bal = student_balance(db, s.id)
    if bal >= 0:
        return {"sent": False, "reason": "Qarzdorlik yo'q"}
    sent = notify.send(
        s.telegram_chat_id,
        f"💰 Eslatma: {s.full_name} bo'yicha "
        f"{int(-bal):,} so'm to'lov qoldi.".replace(",", " ") +
        "\nMarkazga to'lab ketishingizni so'raymiz. Rahmat!")
    if sent:
        audit.log(db, user, entity="student", action="notify_debt",
                  entity_id=s.id, entity_label=s.full_name,
                  branch_id=s.branch_id, commit=True)
    return {"sent": sent}

def _new_parent_token(s: models.Student) -> None:
    """Yangi (yoki birinchi) ota-ona tokeni + muddatini o'rnatadi.
    Chaqiruvchi commit qiladi."""
    import secrets as _sec
    s.parent_token = _sec.token_urlsafe(16)
    s.parent_token_expires_at = (
        datetime.utcnow()
        + timedelta(days=roles.PARENT_TOKEN_VALIDITY_DAYS))


@router.get("/api/students/{student_id}/parent-link")
def parent_link(student_id: int, db: Session = Depends(get_db),
                user=Depends(require_role(*roles.CASH_ACCESS))):
    """Ota-onaga beriladigan havola. Token taxmin qilib bo'lmaydigan
    tasodifiy satr, roles.PARENT_TOKEN_VALIDITY_DAYS kundan keyin
    muddati tugaydi - kerak bo'lsa /regenerate bilan almashtiriladi.

    Bu endpoint MAVJUD havolani hech qachon bekor qilmaydi (shunchaki
    ko'rish/nusxalash uchun ochilganda ham tasodifan almashtirib
    qo'ymaslik uchun) - faqat token umuman yo'q bo'lsa yaratadi, yoki
    muddat tizimidan OLDINGI eski tokenga (parent_token_expires_at
    NULL) endi ham amal qiladigan muddat belgilaydi."""
    s = db.query(models.Student).get(student_id)
    if not s:
        raise HTTPException(404, "O'quvchi topilmadi")
    if not s.parent_token:
        _new_parent_token(s)
        db.commit()
    elif not s.parent_token_expires_at:
        s.parent_token_expires_at = (
            datetime.utcnow()
            + timedelta(days=roles.PARENT_TOKEN_VALIDITY_DAYS))
        db.commit()
    base = os.environ.get("PUBLIC_URL", "https://jony-crm.vercel.app")
    return {"url": f"{base}/parent/{s.parent_token}",
            "expires_at": s.parent_token_expires_at.isoformat()}


@router.post("/api/students/{student_id}/parent-link/regenerate")
def parent_link_regenerate(student_id: int, db: Session = Depends(get_db),
                           user=Depends(require_role(*roles.CASH_ACCESS))):
    """Eski havolani DARHOL bekor qiladi (endi ishlamaydi) va yangisini
    yaratadi. Token noto'g'ri odamga ketgan yoki muddati tugagan
    bo'lsa ishlatiladi."""
    s = db.query(models.Student).get(student_id)
    if not s:
        raise HTTPException(404, "O'quvchi topilmadi")
    had_old = bool(s.parent_token)
    _new_parent_token(s)
    db.commit()
    audit.log(db, user, entity="student", action="update", entity_id=s.id,
              entity_label=s.full_name, field="Ota-ona havolasi",
              old_value="eski havola bekor qilindi" if had_old else "yo'q edi",
              new_value="yangi havola yaratildi", commit=True)
    base = os.environ.get("PUBLIC_URL", "https://jony-crm.vercel.app")
    return {"url": f"{base}/parent/{s.parent_token}",
            "expires_at": s.parent_token_expires_at.isoformat()}

@router.get("/api/students/{student_id}/pay-link")
def pay_link(student_id: int, amount: float = 0,
             db: Session = Depends(get_db),
             user=Depends(require_role(*roles.CASH_ACCESS))):
    s = db.query(models.Student).get(student_id)
    if not s:
        raise HTTPException(404, "O'quvchi topilmadi")
    payme_id = os.environ.get("PAYME_MERCHANT_ID", "").strip()
    click_m = os.environ.get("CLICK_MERCHANT_ID", "").strip()
    click_s = os.environ.get("CLICK_SERVICE_ID", "").strip()
    if not payme_id and not (click_m and click_s):
        return {"enabled": False}
    amt = roles.money(amount) if amount and amount > 0 \
        else roles.money(-student_balance(db, s.id)
                         if student_balance(db, s.id) < 0 else 0)
    links = {}
    if payme_id and amt > 0:
        import base64 as _b64
        raw = f"m={payme_id};ac.student={s.public_id or s.id};a={int(amt * 100)}"
        links["payme"] = ("https://checkout.paycom.uz/"
                          + _b64.b64encode(raw.encode()).decode())
    if click_m and click_s and amt > 0:
        links["click"] = (
            "https://my.click.uz/services/pay"
            f"?service_id={click_s}&merchant_id={click_m}"
            f"&amount={int(amt)}&transaction_param={s.public_id or s.id}")
    return {"enabled": True, "amount": amt, "links": links}

@router.post("/api/students/import")
def import_students(payload: schemas.StudentImportIn,
                    db: Session = Depends(get_db),
                    user=Depends(require_role(*roles.FREEZE_ROLES))):
    g = db.query(models.Group).get(payload.group_id)
    if not g:
        raise HTTPException(404, "Guruh topilmadi")
    if not _in_user_branches(db, user, g.branch_id, null_ok=True):
        raise HTTPException(403, "Bu guruh boshqa filialga tegishli")

    today = roles.local_today()
    existing = db.query(models.Student).filter(
        models.Student.group_id == g.id).all()
    names = {(s.full_name or "").strip().lower() for s in existing}

    def _status(txt):
        t = (txt or "").strip().lower()
        if "arxiv" in t or "archiv" in t:
            return "archived"
        if "muzlat" in t or "frozen" in t:
            return "frozen"
        if "sinov" in t or "trial" in t:
            return "trial"
        return "active"

    results, created = [], 0
    for r in payload.rows:
        name = (r.full_name or "").strip()
        if not name:
            continue
        if name.lower() in names:
            results.append({"name": name, "status": "skip",
                            "reason": "bu guruhda allaqachon bor"})
            continue
        # DIQQAT: telefon bo'yicha o'tkazib yubormaymiz — aka-uka/opa-
        # singillar bitta (ota-onaning) raqami bilan yoziladi. Haqiqiy
        # dublikatni ism tekshiruvi ushlaydi.

        # LC UP bo'sh tug'ilgan sanaga eksport kunini yozadi — 4
        # yoshdan kichik chiqsa, sana yo'q deb hisoblaymiz.
        bdate = None
        if r.birth_date:
            try:
                bdate = date.fromisoformat(str(r.birth_date)[:10])
                if bdate.year > today.year - 4:
                    bdate = None
            except ValueError:
                bdate = None

        s = models.Student(
            full_name=name,
            phone=(r.phone or "").strip() or None,
            address=(r.address or "").strip() or None,
            birth_date=bdate,
            group_id=g.id,
            branch_id=g.branch_id,
            status=_status(r.status),
            subject=g.subject,
            level=g.level,
            enrolled_date=today,
        )
        db.add(s)
        names.add(name.lower())
        created += 1
        results.append({"name": name, "status": "ok"})
    db.commit()
    audit.log(db, user, entity="student", action="import",
              entity_label=f"{g.name}: {created} ta o'quvchi",
              new_value=created, branch_id=g.branch_id, commit=True)
    return {"created": created, "group": g.name, "results": results}

