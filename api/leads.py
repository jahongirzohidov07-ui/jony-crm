"""Auto-extracted from main.py during refactor (split-main). Domain: leads."""
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

def _get_lead_in_scope(db: Session, lead_id: int, user: models.User) -> models.Lead:
    lead = db.query(models.Lead).get(lead_id)
    if not lead:
        raise HTTPException(404, "Lid topilmadi")
    if user.role not in tuple(roles.ORG_WIDE_ROLES):
        if user.branch_id and lead.branch_id != user.branch_id:
            raise HTTPException(403, "Bu lid boshqa filialga tegishli")
    return lead

def _validate_lead_fields(source: Optional[str], stage: Optional[str]):
    if source is not None and source not in roles.LEAD_SOURCES:
        raise HTTPException(400, "Noto'g'ri manba")
    if stage is not None and stage not in roles.LEAD_STAGES:
        raise HTTPException(400, "Noto'g'ri bosqich")

@router.get("/api/leads", response_model=List[schemas.LeadOut])
def list_leads(
    stage: Optional[str] = None,
    branch_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(*roles.LEAD_ACCESS)),
):
    backfill_missing_ids(db, "lead", models.Lead)
    q = scope_to_branch(db.query(models.Lead), models.Lead, user, branch_id)
    if stage:
        q = q.filter(models.Lead.stage == stage)
    else:
        # O'quvchiga aylangan lid doskada turmaydi - u endi Talabalar
        # bo'limida. Voronka hisobotlari to'g'ridan-to'g'ri bazadan
        # o'qiydi, shuning uchun statistika buzilmaydi.
        q = q.filter(models.Lead.stage != "converted")
    return q.order_by(models.Lead.updated_at.desc(), models.Lead.id.desc()).all()

@router.post("/api/leads", response_model=schemas.LeadOut)
def create_lead(
    payload: schemas.LeadCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(*roles.LEAD_ACCESS)),
):
    if not payload.full_name.strip():
        raise HTTPException(400, "Ism-familiyani kiriting")
    _validate_lead_fields(payload.source, payload.stage)

    # DUBLIKAT: shu telefon bilan lid yoki o'quvchi allaqachon bormi?
    # Bitta odam ikki marta yozilib ketmasin. "force" bilan baribir
    # qo'shish mumkin (masalan, aka-uka bitta raqamdan yozilsa).
    digits = "".join(ch for ch in (payload.phone or "") if ch.isdigit())
    if digits and len(digits) >= 7 and not payload.force:
        tail = digits[-9:]
        dup_lead = None
        for l in db.query(models.Lead).filter(
                models.Lead.phone.isnot(None),
                models.Lead.stage.notin_(("rejected",))).all():
            d = "".join(ch for ch in (l.phone or "") if ch.isdigit())
            if d and d[-9:] == tail:
                dup_lead = l
                break
        dup_student = None
        if not dup_lead:
            for s in db.query(models.Student).filter(
                    models.Student.status != "archived").all():
                for ph in (s.phone, s.parent_phone):
                    d = "".join(ch for ch in (ph or "") if ch.isdigit())
                    if d and d[-9:] == tail:
                        dup_student = s
                        break
                if dup_student:
                    break
        if dup_lead or dup_student:
            who = dup_lead.full_name if dup_lead else dup_student.full_name
            kind = "lid" if dup_lead else "o'quvchi"
            raise HTTPException(
                409, f"Bu telefon raqami bilan {kind} allaqachon bor: "
                     f"{who}. Bir oila vakilimi (aka-uka / opa-singil) "
                     "yoki raqamni adashib kiritdingizmi? Bir oiladan "
                     "bo'lsa, tasdiqlang — bitta raqam bilan yozilaveradi.")

    # DUBLIKAT (ism bo'yicha): bir xil ism-familiyali lid yoki talaba
    # bo'lsa — adashib qayta kiritishning oldini olamiz. Yangi odam
    # bo'lsa, tasdiqlab kiritaveradi (force).
    if not payload.force:
        nm = " ".join(payload.full_name.split()).lower()
        same_lead = next(
            (l for l in db.query(models.Lead)
             .filter(models.Lead.stage != "rejected").all()
             if " ".join((l.full_name or "").split()).lower() == nm), None)
        same_student = None
        if not same_lead:
            same_student = next(
                (st for st in db.query(models.Student)
                 .filter(models.Student.status != "archived").all()
                 if " ".join((st.full_name or "").split()).lower() == nm),
                None)
        if same_lead or same_student:
            kind = "lid" if same_lead else "talaba"
            raise HTTPException(
                409, f"Bunday ismli {kind} allaqachon bor — adashib "
                     f"qayta kiritib qo'ymayapsizmi? Agar bu boshqa "
                     f"(yangi) odam bo'lsa, tasdiqlang.")

    # Bosqich berilmasa, manbaga qarab o'zi tanlanadi: tashrif bilan kelgan
    # odam "unga qo'ng'iroq qilish kerak" bosqichini o'tib bo'lgan.
    stage = payload.stage or roles.LEAD_SOURCE_DEFAULT_STAGE.get(payload.source, "new")

    lead = models.Lead(
        full_name=payload.full_name.strip(),
        phone=payload.phone,
        source=payload.source,
        stage=stage,
        address=payload.address,
        school=payload.school,
        grade=payload.grade,
        note=payload.note,
        branch_id=payload.branch_id if payload.branch_id is not None else user.branch_id,
        assigned_user_id=payload.assigned_user_id,
        created_by=user.full_name,
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead

@router.put("/api/leads/{lead_id}", response_model=schemas.LeadOut)
def update_lead(
    lead_id: int,
    payload: schemas.LeadUpdate,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(*roles.LEAD_ACCESS)),
):
    lead = _get_lead_in_scope(db, lead_id, user)
    _validate_lead_fields(payload.source, payload.stage)

    data = payload.model_dump(exclude_unset=True)
    if data.get("stage") == "converted" and not lead.converted_student_id:
        raise HTTPException(
            400,
            "Lidni bu bosqichga qo'lda surib bo'lmaydi - "
            "\"O'quvchiga aylantirish\" tugmasidan foydalaning",
        )
    for k, v in data.items():
        setattr(lead, k, v)
    db.commit()
    db.refresh(lead)
    return lead

@router.delete("/api/leads/{lead_id}")
def delete_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(*roles.FULL_ACCESS)),
):
    lead = _get_lead_in_scope(db, lead_id, user)
    db.delete(lead)
    db.commit()
    return {"ok": True}

@router.post("/api/leads/{lead_id}/convert", response_model=schemas.StudentOut)
def convert_lead(
    lead_id: int,
    payload: schemas.LeadConvertRequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(*roles.LEAD_ACCESS)),
):
    """Lidni haqiqiy o'quvchiga aylantiradi. Lid o'chirilmaydi - bosqichi
    "converted" bo'ladi va yaratilgan o'quvchiga bog'lanadi, shunda
    voronka statistikasi saqlanib qoladi."""
    lead = _get_lead_in_scope(db, lead_id, user)
    if lead.converted_student_id:
        raise HTTPException(400, "Bu lid allaqachon o'quvchiga aylantirilgan")

    # Lidda yig'ilgan qo'shimcha ma'lumot (manzil, maktab, sinf) yo'qolib
    # ketmasligi uchun uni o'quvchining izohiga ko'chiramiz.
    extra = []
    if lead.address:
        extra.append(f"Manzil: {lead.address}")
    if lead.school:
        extra.append(f"Maktab: {lead.school}")
    if lead.grade:
        extra.append(f"Sinf: {lead.grade}")
    if lead.note:
        extra.append(lead.note)
    student_note = " · ".join(extra) if extra else None

    student = models.Student(
        full_name=lead.full_name,
        phone=lead.phone,
        group_id=payload.group_id,
        branch_id=lead.branch_id,
        enrolled_date=payload.enrolled_date or date.today(),
        status="active",
        note=student_note,
        # Kartada ham ko'rinsin — faqat eslatmada qolib ketmasin
        address=lead.address,
        school=lead.school,
        school_grade=lead.grade,
    )
    db.add(student)
    db.flush()

    lead.stage = "converted"
    lead.converted_student_id = student.id
    db.commit()
    db.refresh(student)
    return to_student_out(db, student)

@router.get("/api/sales/panel")
def sales_panel(
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.DEBTOR_ACCESS)),
):
    today = date.today()
    m_start, m_end = billing.month_bounds(today.year, today.month)

    rooms = {r.id: r for r in db.query(models.Room).all()}
    groups = scope_to_branch(db.query(models.Group), models.Group,
                             user, branch_id).all()
    students = scope_to_branch(db.query(models.Student), models.Student,
                               user, branch_id).all()

    # --- To'ldirilishi kerak bo'lgan guruhlar ---
    fill_rows = []
    for g in groups:
        n = sum(1 for s in students
                if s.group_id == g.id and s.status in ("active", "trial"))
        cap = _group_capacity(g, rooms)
        if not cap:
            continue
        pct = round(n / cap * 100, 1)
        band, band_label = roles.fill_band(pct)
        if pct >= 85:
            continue          # to'la guruh - ishlash shart emas
        fill_rows.append({
            "group_id": g.id,
            "group": g.name,
            "teacher": g.teacher.full_name if g.teacher else None,
            "subject_label": roles.SUBJECT_LABELS.get(g.subject or "", None),
            "level_label": roles.LEVEL_LABELS.get(g.level or "", None),
            "days": [d for d in (g.lesson_days or "").split(",") if d],
            "time": g.lesson_time,
            "students": n,
            "capacity": cap,
            "free": cap - n,
            "fill": pct,
            "band": band,
            "band_label": band_label,
        })
    # Eng ko'p bo'sh joyi bor guruh tepada - eng ko'p pul shu yerda
    fill_rows.sort(key=lambda r: (-r["free"], r["fill"]))

    # --- Shu oy ketganlar ---
    left_rows = []
    for s in students:
        if s.left_date and m_start <= s.left_date <= m_end:
            left_rows.append({
                "student_id": s.id,
                "full_name": s.full_name,
                "group": s.group.name if s.group else None,
                "teacher": (s.group.teacher.full_name
                            if s.group and s.group.teacher else None),
                "left_date": s.left_date.isoformat(),
                "months": (round((s.left_date - s.enrolled_date).days / 30.4, 1)
                           if s.enrolled_date else None),
                "balance": round(student_balance(db, s.id), 2),
            })
    left_rows.sort(key=lambda r: r["left_date"], reverse=True)

    return {
        "month": today.isoformat()[:7],
        "fill": {
            "rows": fill_rows[:20],
            "count": len(fill_rows),
            "free_seats": sum(r["free"] for r in fill_rows),
            # Bo'sh joylar qancha pul turadi
            "lost_income": round(sum(
                r["free"] * next((g.monthly_fee or 0) for g in groups
                                 if g.id == r["group_id"])
                for r in fill_rows), 2),
        },
        "left": {
            "rows": left_rows,
            "count": len(left_rows),
        },
    }

