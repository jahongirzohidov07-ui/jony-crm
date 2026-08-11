"""Auto-extracted from main.py during refactor (split-main). Domain: finance."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bisect
from datetime import date, datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, FastAPI, HTTPException, Request
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

def can_see_all_branches(user: models.User) -> bool:
    """Butun tashkilotni ko'radimi yoki bitta filialgami."""
    return user.role in tuple(roles.ORG_WIDE_ROLES) or not user.branch_id

def _get_expense_in_scope(db: Session, expense_id: int, user: models.User) -> models.Expense:
    exp = db.query(models.Expense).get(expense_id)
    if not exp:
        raise HTTPException(404, "Xarajat topilmadi")
    if not _in_user_branches(db, user, exp.branch_id):
        raise HTTPException(403, "Bu xarajat boshqa filialga tegishli")
    return exp

@router.get("/api/expenses", response_model=List[schemas.ExpenseOut])
def list_expenses(
    year: Optional[int] = None,
    month: Optional[int] = None,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(*roles.EXPENSE_ACCESS)),
):
    """Xarajatlar ro'yxati. year/month berilsa - o'sha oy uchun."""
    q = scope_to_branch(db.query(models.Expense), models.Expense, user)
    if year and month:
        start, end = billing.month_bounds(year, month)
        q = q.filter(models.Expense.date >= start, models.Expense.date <= end)
    return q.order_by(models.Expense.date.desc(), models.Expense.id.desc()).all()

@router.post("/api/expenses", response_model=schemas.ExpenseOut)
def create_expense(
    payload: schemas.ExpenseCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(*roles.EXPENSE_ACCESS)),
):
    if payload.category not in roles.EXPENSE_CATEGORIES:
        raise HTTPException(400, "Noto'g'ri xarajat turi")
    if payload.amount <= 0:
        raise HTTPException(400, "Summa noldan katta bo'lishi kerak")

    exp = models.Expense(
        date=payload.date,
        category=payload.category,
        amount=abs(payload.amount),
        note=payload.note,
        branch_id=payload.branch_id if payload.branch_id is not None else user.branch_id,
        # Kanal faqat reklama xarajatida ma'noga ega - CAC shundan chiqadi.
        channel=payload.channel,
        method=payload.method or "cash",
        created_by=user.full_name,
    )
    db.add(exp)
    db.commit()
    db.refresh(exp)
    audit.log(db, user, entity="expense", action="create", entity_id=exp.id,
              entity_label=exp.note or exp.category, field=exp.category,
              new_value=exp.amount, branch_id=exp.branch_id, commit=True)
    return exp

@router.put("/api/expenses/{expense_id}", response_model=schemas.ExpenseOut)
def update_expense(
    expense_id: int,
    payload: schemas.ExpenseUpdate,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(*roles.EXPENSE_ACCESS)),
):
    exp = _get_expense_in_scope(db, expense_id, user)
    data = payload.model_dump(exclude_unset=True)
    if "category" in data and data["category"] not in roles.EXPENSE_CATEGORIES:
        raise HTTPException(400, "Noto'g'ri xarajat turi")
    if "amount" in data:
        if data["amount"] is None or data["amount"] <= 0:
            raise HTTPException(400, "Summa noldan katta bo'lishi kerak")
        data["amount"] = abs(data["amount"])
    audit.log_changes(db, user, entity="expense", obj=exp, changes=data,
                      label_attr="note")
    for k, v in data.items():
        setattr(exp, k, v)
    db.commit()
    db.refresh(exp)
    return exp

@router.delete("/api/expenses/{expense_id}")
def delete_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(*roles.EXPENSE_DELETE)),
):
    exp = _get_expense_in_scope(db, expense_id, user)
    audit.log(db, user, entity="expense", action="delete", entity_id=exp.id,
              entity_label=exp.note or exp.category, field=exp.category,
              old_value=exp.amount, branch_id=exp.branch_id)
    db.delete(exp)
    db.commit()
    return {"ok": True}

@router.post("/api/checks/schedule")
def check_schedule(
    payload: schemas.ScheduleCheck,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_STAFF)),
):
    """Saqlashdan oldin tekshirish - foydalanuvchi xatoni saqlashdan
    oldin ko'radi."""
    problems = _check_schedule(
        db, group_id=payload.group_id, teacher_id=payload.teacher_id,
        room_id=payload.room_id, lesson_days=payload.lesson_days,
        lesson_time=payload.lesson_time)
    return {
        "problems": problems,
        "ok": not problems,
        "blocking": any(p["severity"] == "block" for p in problems),
    }

@router.post("/api/checks/enrolment")
def check_enrolment(
    payload: schemas.EnrolmentCheck,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_STAFF)),
):
    s = db.query(models.Student).get(payload.student_id)
    g = db.query(models.Group).get(payload.group_id)
    if not s or not g:
        raise HTTPException(404, "Topilmadi")
    problems = _check_enrolment(db, s, g)
    return {
        "problems": problems,
        "ok": not problems,
        "blocking": any(p["severity"] == "block" for p in problems),
    }

@router.delete("/api/payments/{payment_id}")
def delete_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FINANCE_ACCESS)),
):
    """Xato kiritilgan yozuvni o'chirish. Balans va hisobotlar shu
    jadvaldan hisoblanadi, shuning uchun o'chirilishi bilan hamma joyda
    avtomatik to'g'rilanadi.

    Avtomatik hisoblangan oylik ("period" belgisi bor) o'chirilmaydi -
    uni Guruh sahifasidan qayta hisoblash kerak, aks holda o'sha oy
    uchun yana hisoblanib, ikki marta tushib qolishi mumkin."""
    p = db.query(models.Payment).get(payment_id)
    if not p:
        raise HTTPException(404, "Yozuv topilmadi")

    s = db.query(models.Student).get(p.student_id)
    if s and not _in_user_branches(db, user, s.branch_id):
        raise HTTPException(403, "Bu o'quvchi boshqa filialga tegishli")

    if p.period:
        # Avto-oylikni faqat ASOSCHI o'chiradi. O'chirilgach shu oy
        # uchun QAYTA hisoblanmaydi (skip belgisi qo'yiladi) — kerak
        # bo'lsa qo'lda "Hisoblash" yozuvi kiritiladi.
        if user.role != roles.FOUNDER:
            raise HTTPException(
                403, "Avtomatik hisoblangan oylikni faqat asoschi "
                     "o'chira oladi")
        if p.kind == "charge":
            db.add(models.ChargeSkip(
                student_id=p.student_id, period=p.period,
                created_by=user.full_name))

    # PUL KIRIMI (to'lov) va refund yozuvini faqat ASOSCHI o'chiradi —
    # kassadagi xato ham asoschi nazorati ostida to'g'rilanadi.
    if p.kind in ("payment", "refund") and user.role != roles.FOUNDER:
        raise HTTPException(
            403, "To'lov (pul kirimi) yozuvini faqat asoschi o'chiradi")

    # Qarzdorlikni o'chirish ("charge" yozuvini olib tashlash) alohida
    # amal - kim qildi, qachon, qancha summani - hammasi yoziladi.
    act = "debt_write_off" if p.kind == "charge" else "payment_cancel"
    audit.log(db, user, entity="payment", action=act, entity_id=p.id,
              entity_label=s.full_name if s else None, field=p.kind,
              old_value=p.amount, new_value=None, note=p.note,
              branch_id=s.branch_id if s else None)
    # To'lov bilan birga uning avtomat coini ham qaytariladi -
    # aks holda xato to'lovdan coin qolib ketardi
    try:
        for ce in db.query(models.CoinEntry).filter(
                models.CoinEntry.source == "pay_ontime",
                models.CoinEntry.ref_id == p.id).all():
            db.delete(ce)
    except Exception:
        pass
    db.delete(p)
    db.commit()
    return {"ok": True}

@router.get("/api/payouts", response_model=List[schemas.TeacherPayoutOut])
def list_payouts(
    year: int,
    month: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(*roles.FINANCE_ACCESS)),
):
    period = f"{year:04d}-{month:02d}"
    q = db.query(models.TeacherPayout).filter(models.TeacherPayout.period == period)
    if user.role not in tuple(roles.ORG_WIDE_ROLES):
        if user.branch_id:
            q = q.join(models.Group).filter(
                _branch_in(db, user, models.Group.branch_id))
    return q.all()

@router.put("/api/payouts/{payout_id}", response_model=schemas.TeacherPayoutOut)
def update_payout(
    payout_id: int,
    payload: schemas.PayoutUpdate,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(*roles.FINANCE_ACCESS)),
):
    payout = db.query(models.TeacherPayout).get(payout_id)
    if not payout:
        raise HTTPException(404, "Yozuv topilmadi")
    old_paid = payout.paid
    payout.paid = int(payload.paid)
    db.commit()
    db.refresh(payout)
    if old_paid != payout.paid:
        # Ustozga pul chiqqan/chiqmaganini belgilaydi - pul harakatiga
        # bevosita bog'liq, shuning uchun kim qachon belgilaganini
        # Audit'da ko'rish kerak (masalan kimdir noto'g'ri "to'landi"
        # deb belgilab qo'ysa, buni keyin tekshirib bo'lishi uchun).
        t = db.query(models.Teacher).get(payout.teacher_id)
        audit.log(
            db, user, entity="teacher_payout", action="update",
            entity_id=payout.id,
            entity_label=f"{t.full_name if t else '?'} — {payout.period}",
            field="To'landimi", old_value=bool(old_paid),
            new_value=bool(payout.paid),
            note=f"{payout.amount:,.0f} so'm".replace(",", " "),
            commit=True)
    return payout

def _refund_out(db, r: "models.RefundRequest") -> dict:
    s = db.query(models.Student).get(r.student_id)
    return {
        "id": r.id, "student_id": r.student_id,
        "student": s.full_name if s else "?",
        "amount": r.amount, "reason": r.reason, "status": r.status,
        "requested_by": r.requested_by, "decided_by": r.decided_by,
        "decided_note": r.decided_note,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }

@router.post("/api/refunds")
def create_refund(payload: schemas.RefundCreate,
                  db: Session = Depends(get_db),
                  user=Depends(require_role(*roles.REFUND_REQUEST))):
    s = db.query(models.Student).get(payload.student_id)
    if not s:
        raise HTTPException(404, "O'quvchi topilmadi")
    amount = roles.money(payload.amount)
    if amount <= 0:
        raise HTTPException(400, "Summa noldan katta bo'lsin")
    if not (payload.reason or "").strip():
        raise HTTPException(400, "Sabab majburiy")
    # Bitta o'quvchiga bitta ochiq so'rov yetadi
    dup = (db.query(models.RefundRequest)
           .filter(models.RefundRequest.student_id == s.id,
                   models.RefundRequest.status == "pending").first())
    if dup:
        raise HTTPException(400, "Bu o'quvchiga ochiq refund so'rovi bor")
    r = models.RefundRequest(
        student_id=s.id, amount=amount, reason=payload.reason.strip(),
        branch_id=s.branch_id, requested_by=user.full_name)
    db.add(r)
    audit.log(db, user, entity="payment", action="refund_request",
              entity_label=s.full_name, new_value=amount,
              note=payload.reason, branch_id=s.branch_id)
    db.commit()
    return {"ok": True, "id": r.id}

@router.get("/api/refunds")
def list_refunds(status: str | None = None,
                 student_id: int | None = None,
                 db: Session = Depends(get_db),
                 user=Depends(require_role(*roles.REFUND_VIEW))):
    q = scope_to_branch(db.query(models.RefundRequest),
                        models.RefundRequest, user)
    if status:
        q = q.filter(models.RefundRequest.status == status)
    if student_id:
        q = q.filter(models.RefundRequest.student_id == student_id)
    rows = q.order_by(models.RefundRequest.created_at.desc()).limit(200).all()
    return [_refund_out(db, r) for r in rows]

@router.post("/api/refunds/{rid}/approve")
def approve_refund(rid: int, payload: schemas.RefundDecision,
                   db: Session = Depends(get_db),
                   user=Depends(require_role(*roles.REFUND_APPROVE))):
    r = db.query(models.RefundRequest).get(rid)
    if not r:
        raise HTTPException(404, "So'rov topilmadi")
    if r.status != "pending":
        raise HTTPException(400, "Bu so'rov allaqachon ko'rib chiqilgan")
    if user.role == roles.BRANCH_MANAGER \
            and not _in_user_branches(db, user, r.branch_id):
        raise HTTPException(403, "Boshqa filial so'rovi")
    s = db.query(models.Student).get(r.student_id)
    # Pul qaytdi: balansdan ayriladigan yozuv
    pay = models.Payment(
        student_id=r.student_id, amount=-abs(r.amount), kind="refund",
        method=None,
        note=f"Refund: {r.reason} (so'ragan: {r.requested_by})",
        created_by=user.full_name)
    db.add(pay)
    db.flush()
    r.status = "approved"
    r.decided_by = user.full_name
    r.decided_note = payload.note
    r.decided_at = datetime.utcnow()
    r.payment_id = pay.id
    audit.log(db, user, entity="payment", action="refund_approve",
              entity_id=pay.id, entity_label=s.full_name if s else "",
              new_value=-abs(r.amount), note=r.reason,
              branch_id=r.branch_id)
    db.commit()
    return {"ok": True, "payment_id": pay.id}

@router.post("/api/refunds/{rid}/reject")
def reject_refund(rid: int, payload: schemas.RefundDecision,
                  db: Session = Depends(get_db),
                  user=Depends(require_role(*roles.REFUND_APPROVE))):
    r = db.query(models.RefundRequest).get(rid)
    if not r:
        raise HTTPException(404, "So'rov topilmadi")
    if r.status != "pending":
        raise HTTPException(400, "Bu so'rov allaqachon ko'rib chiqilgan")
    if user.role == roles.BRANCH_MANAGER \
            and not _in_user_branches(db, user, r.branch_id):
        raise HTTPException(403, "Boshqa filial so'rovi")
    r.status = "rejected"
    r.decided_by = user.full_name
    r.decided_note = payload.note
    r.decided_at = datetime.utcnow()
    s = db.query(models.Student).get(r.student_id)
    audit.log(db, user, entity="payment", action="refund_reject",
              entity_label=s.full_name if s else "", new_value=r.amount,
              note=payload.note or r.reason, branch_id=r.branch_id,
              commit=True)
    return {"ok": True}

@router.get("/api/discounts")
def list_discounts(
    student_id: Optional[int] = None,
    status_filter: Optional[str] = None,
    branch_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.DISCOUNT_REQUEST)),
):
    _expire_discounts(db)
    q = db.query(models.Discount)
    if student_id:
        q = q.filter(models.Discount.student_id == student_id)
    if status_filter:
        q = q.filter(models.Discount.status == status_filter)
    rows = q.order_by(models.Discount.created_at.desc()).all()

    # Filial kesimi - o'quvchi orqali
    if branch_id or not can_see_all_branches(user):
        allowed = {s.id for s in scope_to_branch(
            db.query(models.Student), models.Student, user, branch_id).all()}
        rows = [d for d in rows if d.student_id in allowed]

    out = []
    for d in rows:
        item = _discount_out(db, d)
        st = db.query(models.Student).get(d.student_id)
        item["student_name"] = st.full_name if st else "—"
        out.append(item)
    return {
        "rows": out,
        "types": [{"key": k, "label": lbl, "hint": h}
                  for k, lbl, h in roles.DISCOUNT_TYPES],
        "statuses": [{"key": k, "label": lbl}
                     for k, lbl in roles.DISCOUNT_STATUSES],
        "max_percent": roles.MAX_TOTAL_DISCOUNT_PERCENT,
        "can_approve": user.role in roles.DISCOUNT_APPROVE,
        "pending": sum(1 for d in rows if d.status == "pending"),
    }

@router.post("/api/discounts")
def create_discount(
    payload: schemas.DiscountCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.DISCOUNT_REQUEST)),
):
    st = db.query(models.Student).get(payload.student_id)
    if not st:
        raise HTTPException(404, "O'quvchi topilmadi")
    if payload.kind not in roles.DISCOUNT_TYPE_LABELS:
        raise HTTPException(400, "Noto'g'ri chegirma turi")
    if payload.kind in roles.AUTO_DISCOUNT_TYPES:
        raise HTTPException(
            400, "Oilaviy chegirmani tizim o'zi beradi — qo'lda qo'shilmaydi")
    if not (payload.percent or payload.amount):
        raise HTTPException(400, "Chegirma miqdorini kiriting")
    if not (payload.reason or "").strip():
        raise HTTPException(400, "Sabab yozilishi shart")
    if payload.kind == "referral" and not payload.referrer_student_id:
        raise HTTPException(400, "Qaysi do'sti olib kelganini tanlang")
    if payload.kind == "staff_child" and not payload.staff_user_id:
        raise HTTPException(400, "Qaysi xodimning farzandi ekanini tanlang")

    # Jami chegirma chegaradan oshmasin
    now = _student_discount_percent(db, st)
    add = payload.percent or 0
    if not add and payload.amount and st.group and st.group.monthly_fee:
        add = payload.amount / st.group.monthly_fee * 100
    if now + add > roles.MAX_TOTAL_DISCOUNT_PERCENT:
        raise HTTPException(
            400,
            f"Jami chegirma {roles.MAX_TOTAL_DISCOUNT_PERCENT}% dan oshmasligi "
            f"kerak. Hozir {now:.0f}%, siz yana {add:.0f}% qo'shyapsiz.")

    d = models.Discount(
        student_id=payload.student_id,
        kind=payload.kind,
        percent=payload.percent,
        amount=payload.amount,
        reason=payload.reason.strip(),
        start_date=payload.start_date or date.today(),
        end_date=payload.end_date,
        referrer_student_id=payload.referrer_student_id,
        staff_user_id=payload.staff_user_id,
        requested_by=user.full_name,
        status="pending",
    )
    # Tasdiqlash huquqi bor odam o'zi so'rasa - darrov amalda.
    if user.role in roles.DISCOUNT_APPROVE:
        d.status = "active"
        d.approved_by = user.full_name
        d.approved_at = datetime.utcnow()
    db.add(d)
    db.commit()
    db.refresh(d)
    audit.log(db, user, entity="discount", action="create", entity_id=d.id,
              entity_label=st.full_name, branch_id=st.branch_id,
              new_value=f"{roles.DISCOUNT_TYPE_LABELS[d.kind]} "
                        f"{d.percent or d.amount}")
    db.commit()
    return _discount_out(db, d)

@router.post("/api/discounts/{discount_id}/approve")
def approve_discount(
    discount_id: int,
    payload: schemas.DiscountDecision,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.DISCOUNT_APPROVE)),
):
    d = db.query(models.Discount).get(discount_id)
    if not d:
        raise HTTPException(404, "Chegirma topilmadi")
    if d.status not in ("pending", "rejected"):
        raise HTTPException(400, "Bu chegirma allaqachon hal qilingan")
    st = db.query(models.Student).get(d.student_id)
    d.status = "active" if payload.approve else "rejected"
    d.approved_by = user.full_name
    d.approved_at = datetime.utcnow()
    if not payload.approve:
        d.cancelled_reason = payload.reason
    db.commit()
    audit.log(db, user, entity="discount",
              action="approve" if payload.approve else "reject",
              entity_id=d.id, entity_label=st.full_name if st else "—",
              branch_id=st.branch_id if st else None,
              new_value=d.status)
    db.commit()
    return _discount_out(db, d)

@router.post("/api/discounts/{discount_id}/cancel")
def cancel_discount(
    discount_id: int,
    payload: schemas.DiscountDecision,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.DISCOUNT_APPROVE)),
):
    d = db.query(models.Discount).get(discount_id)
    if not d:
        raise HTTPException(404, "Chegirma topilmadi")
    st = db.query(models.Student).get(d.student_id)
    d.status = "cancelled"
    d.cancelled_reason = payload.reason or "Bekor qilindi"
    db.commit()
    audit.log(db, user, entity="discount", action="cancel", entity_id=d.id,
              entity_label=st.full_name if st else "—",
              branch_id=st.branch_id if st else None,
              old_value="active", new_value="cancelled")
    db.commit()
    return _discount_out(db, d)

@router.post("/api/billing/month")
def billing_month(
    year: int,
    month: int,
    commit: bool = False,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FINANCE_ACCESS)),
):
    """Oy boshida barcha FAOL o'quvchilardan shu oy uchun to'liq pul
    hisoblaydi (balansdan yechadi).

    Shundan keyin "bu oyda qancha pul tushishi kerak" degan savolga
    javob bor, va administrator qancha yig'ganini foizda ko'rish mumkin.

    commit=False - faqat hisoblab ko'rsatadi, hech narsa yozmaydi."""
    period = _period_key(year, month)
    start, end = billing.month_bounds(year, month)

    students = [s for s in
                scope_to_branch(db.query(models.Student), models.Student, user).all()
                if s.status == "active" and s.group_id]

    rows, created = [], 0
    for s in students:
        g = s.group
        if not g:
            continue
        already = (db.query(models.Payment)
                   .filter(models.Payment.student_id == s.id,
                           models.Payment.period == period,
                           models.Payment.kind == "charge").first())
        # O'quvchi oy o'rtasida qo'shilgan bo'lsa - faqat qolgan darslar
        since = start
        if s.enrolled_date and s.enrolled_date > start:
            since = s.enrolled_date
        lessons = len(_lessons_left_in_month(db, g.id, since)) if since <= end else 0
        disc = _student_discount_percent(db, s)
        amount = lessons * (g.lesson_price or 0) * (100 - disc) / 100

        if commit and not already and amount > 0 \
                and not _charge_skipped(db, s.id, period):
            db.add(models.Payment(
                student_id=s.id, amount=-abs(amount), kind="charge",
                note=f"{g.name} — {period} oyi uchun {lessons} dars"
                     + (f" (chegirma {disc}%)" if disc else ""),
                created_by=user.full_name, period=period))
            created += 1
        rows.append({
            "student_id": s.id, "public_id": s.public_id,
            "full_name": s.full_name, "group": g.name,
            "lessons": lessons, "discount": disc, "amount": round(amount, 2),
            "already_charged": already is not None,
        })

    if commit:
        audit.log(db, user, entity="payment", action="create",
                  entity_label=f"{period} oylik hisob-kitob",
                  new_value=created,
                  note=f"{created} ta o'quvchiga hisoblandi", commit=True)
        db.commit()

    return {
        "period": period,
        "committed": commit,
        "students": len(rows),
        "created": created,
        "expected_total": round(sum(r["amount"] for r in rows), 2),
        "rows": sorted(rows, key=lambda r: r["full_name"]),
    }

@router.get("/api/smm/sales-plan")
def smm_sales_plan_list(
    year: int | None = None,
    month: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*(list(roles.FULL_ACCESS)
                                + [roles.FINANCE_DIRECTOR,
                                   roles.SMM_MANAGER]))),
):
    """Marketolog sotuv rejasi va bonusi - filiallar kesimida.

    Rahbariyat hammasini ko'radi; marketolog faqat o'z filialini
    (o'z panelida ham xuddi shu raqamlar chiqadi)."""
    today = roles.local_today()
    y, m = year or today.year, month or today.month
    q = db.query(models.Branch).order_by(models.Branch.name)
    if user.role == roles.SMM_MANAGER and user.branch_id:
        q = q.filter(models.Branch.id == user.branch_id)
    rows = []
    for b in q.all():
        st = _smm_sales_state(db, b.id, y, m)
        rows.append({"branch_id": b.id, "branch": b.name, **st})
    return {"year": y, "month": m, "rows": rows,
            "scale": [{"min": mn, "bonus": bo, "label": lb}
                      for mn, bo, lb in roles.SMM_SALES_BONUS],
            "can_edit": user.role in tuple(roles.FULL_ACCESS)
            or user.role == roles.FINANCE_DIRECTOR}


@router.put("/api/smm/sales-plan")
def smm_sales_plan_set(
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    user=Depends(require_role(*(list(roles.FULL_ACCESS)
                                + [roles.FINANCE_DIRECTOR]))),
):
    """Filial uchun oylik sotuv rejasini kiritish/yangilash."""
    try:
        branch_id = int(payload.get("branch_id"))
        year = int(payload.get("year"))
        month = int(payload.get("month"))
        amount = float(payload.get("amount") or 0)
    except (TypeError, ValueError):
        raise HTTPException(400, "Maydonlar noto'g'ri")
    if not (1 <= month <= 12) or amount < 0:
        raise HTTPException(400, "Oy yoki summa noto'g'ri")
    row = (db.query(models.SmmSalesPlan)
           .filter(models.SmmSalesPlan.branch_id == branch_id,
                   models.SmmSalesPlan.year == year,
                   models.SmmSalesPlan.month == month).first())
    old = row.amount if row else None
    if row is None:
        row = models.SmmSalesPlan(branch_id=branch_id, year=year,
                                  month=month, created_by=user.full_name)
        db.add(row)
    row.amount = amount
    db.commit()
    b = db.query(models.Branch).get(branch_id)
    audit.log(db, user, entity="plan", action="update",
              entity_label=f"Sotuv rejasi - {b.name if b else branch_id}",
              field=f"{year}-{month:02d}",
              old_value=old, new_value=amount, commit=True)
    return {"ok": True}


@router.get("/api/billing/collection-legacy")
def billing_collection_legacy(
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FINANCE_ACCESS)),
):
    """Eski yillardagi to'lov yig'ilishi arxivi (import qilingan).

    Jahongir eski Google Sheets jadvalidagi reja/fakt raqamlarini
    tizimda ham ko'rinsin dedi. Guruhlash: filial -> yil -> oylar,
    foiz har doim reja/faktdan qayta hisoblanadi."""
    rows = (db.query(models.LegacyCollectionMonth)
            .order_by(models.LegacyCollectionMonth.branch_label,
                      models.LegacyCollectionMonth.year,
                      models.LegacyCollectionMonth.month).all())
    out = {}
    for r in rows:
        blk = out.setdefault(r.branch_label, {}).setdefault(
            r.year, {"months": [], "plan": 0.0, "fact": 0.0})
        blk["months"].append({
            "month": r.month, "plan": r.plan, "fact": r.fact,
            "percent": round(r.fact / r.plan * 100, 1) if r.plan else None,
        })
        blk["plan"] += r.plan
        blk["fact"] += r.fact
    result = []
    for label, years in out.items():
        for year, blk in sorted(years.items()):
            result.append({
                "label": label, "year": year,
                "months": blk["months"],
                "plan": round(blk["plan"], 2),
                "fact": round(blk["fact"], 2),
                "percent": round(blk["fact"] / blk["plan"] * 100, 1)
                if blk["plan"] else None,
            })
    # Yangi yillar tepada, filial nomi bo'yicha barqaror tartib
    result.sort(key=lambda b: (-b["year"], b["label"]))
    return {"blocks": result}


@router.get("/api/billing/collection")
def billing_collection(
    year: int,
    month: int,
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.CASH_ACCESS)),
):
    """To'lovlarni yig'ish foizi - HAR BIR O'QUVCHI bo'yicha alohida.

    Muhim nuqta: bir o'quvchi ortiqcha to'lasa, bu boshqasining qarzini
    yopmaydi. Shuning uchun har bir o'quvchida "qopланgan summa" shu
    oyning hisobidan oshmaydi, ortig'i esa KEYINGI OYGA o'tadi.

    Aks holda "225% bajarildi" degan raqam chiqib, to'lamagan ikki
    o'quvchi ko'rinmay qolardi."""
    period = _period_key(year, month)
    start, end = billing.month_bounds(year, month)
    d0, d1 = _utc_window(start, end)

    sq = scope_to_branch(db.query(models.Student), models.Student, user,
                         branch_id)
    students = sq.all()
    ids = [s.id for s in students]
    if not ids:
        return {"period": period, "charged": 0.0, "collected": 0.0,
                "percent": 0.0, "debt": 0.0, "students": 0,
                "paid_students": 0, "partial_students": 0,
                "unpaid_students": 0, "carry_in": 0.0, "carry_out": 0.0,
                "rows": [], "by_admin": []}

    # DIQQAT: hisoblangan pul qaysi oyga tegishli ekani "period" bilan
    # belgilanadi, yozuv qachon yaratilgani bilan emas. Aprel hisobini
    # may oyida yuritish mumkin - u baribir aprelniki bo'lib qoladi.
    # Haqiqiy pul esa aksincha: qachon kelgani muhim.
    charges, payments, opening = {}, {}, {}
    pay_rows = []

    for p in (db.query(models.Payment)
              .filter(models.Payment.student_id.in_(ids)).all()):
        sid = p.student_id
        if p.kind in ("charge", "discount"):
            per = p.period or (p.created_at.date().isoformat()[:7]
                               if p.created_at else period)
            if per == period:
                sign = 1 if p.kind == "charge" else -1
                charges[sid] = charges.get(sid, 0.0) + sign * abs(p.amount)
            elif per < period:
                # O'tgan davrlarning hisobi - ochilish balansiga kiradi
                opening[sid] = opening.get(sid, 0.0) - abs(p.amount)
        elif p.kind == "payment":
            if d0 <= p.created_at <= d1:
                payments[sid] = payments.get(sid, 0.0) + p.amount
                pay_rows.append(p)
            elif p.created_at < d0:
                opening[sid] = opening.get(sid, 0.0) + p.amount

    by_id = {s.id: s for s in students}
    rows = []
    tot_charged = tot_covered = tot_carry_in = tot_carry_out = 0.0
    paid_n = partial_n = unpaid_n = 0

    for sid in set(list(charges.keys()) + list(payments.keys())):
        ch = max(0.0, charges.get(sid, 0.0))
        pay = payments.get(sid, 0.0)
        carry_in = max(0.0, opening.get(sid, 0.0))     # o'tgan oydan qolgan pul
        old_debt = min(0.0, opening.get(sid, 0.0))     # o'tgan oydan qarz

        available = carry_in + pay
        covered = min(ch, available)                   # shu oyni qoplagani
        left = max(0.0, ch - covered)                  # shu oyda qolgan qarz
        carry_out = max(0.0, available - ch)           # keyingi oyga o'tadi

        if ch <= 0:
            continue
        tot_charged += ch
        tot_covered += covered
        tot_carry_in += carry_in
        tot_carry_out += carry_out

        if left <= 0.01:
            paid_n += 1
            state = "paid"
        elif covered > 0:
            partial_n += 1
            state = "partial"
        else:
            unpaid_n += 1
            state = "unpaid"

        st = by_id.get(sid)
        rows.append({
            "student_id": sid,
            "public_id": st.public_id if st else None,
            "full_name": st.full_name if st else "—",
            "group": st.group.name if st and st.group else None,
            "phone": st.phone if st else None,
            "charged": round(ch, 2),
            "paid": round(pay, 2),
            "carry_in": round(carry_in, 2),
            "covered": round(covered, 2),
            "left": round(left, 2),
            "carry_out": round(carry_out, 2),
            "old_debt": round(abs(old_debt), 2),
            "percent": round(covered / ch * 100, 1) if ch else 0.0,
            "state": state,
        })

    # To'lamaganlar tepada tursin - ular bilan ishlash kerak
    order = {"unpaid": 0, "partial": 1, "paid": 2}
    rows.sort(key=lambda r: (order[r["state"]], -r["left"]))

    # Kim yig'di - administrator kesimida
    by_admin = {}
    for p in pay_rows:
        who = p.created_by or "—"
        by_admin[who] = by_admin.get(who, 0.0) + p.amount
    admins = [{"name": k, "collected": round(v, 2)}
              for k, v in sorted(by_admin.items(), key=lambda kv: -kv[1])]

    return {
        "period": period,
        "charged": round(tot_charged, 2),
        # "collected" - shu oyning hisobiga QO'SHILGAN pul (ortiqchasi emas)
        "collected": round(tot_covered, 2),
        "cash_in": round(sum(p.amount for p in pay_rows), 2),
        "percent": round(tot_covered / tot_charged * 100, 1) if tot_charged else 0.0,
        "debt": round(tot_charged - tot_covered, 2),
        "carry_in": round(tot_carry_in, 2),
        "carry_out": round(tot_carry_out, 2),
        "students": len(rows),
        "paid_students": paid_n,
        "partial_students": partial_n,
        "unpaid_students": unpaid_n,
        "rows": rows,
        "by_admin": admins,
    }

@router.delete("/api/teacher-payments/{payment_id}")
def delete_teacher_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.SALARY_PAY)),
):
    p = db.query(models.TeacherPayment).get(payment_id)
    if not p:
        raise HTTPException(404, "Topilmadi")
    t = db.query(models.Teacher).get(p.teacher_id)
    audit.log(db, user, entity="teacher", action="delete", entity_id=p.teacher_id,
              entity_label=t.full_name if t else "—",
              field="Ustoz to'lovi",
              old_value=f"{p.amount:,.0f}".replace(",", " "))
    db.delete(p); db.commit()
    return {"ok": True}

def _last_charge_date(db: Session, student_id: int) -> date | None:
    row = (db.query(models.Payment)
           .filter(models.Payment.student_id == student_id,
                   models.Payment.kind == "charge")
           .order_by(models.Payment.created_at.desc()).first())
    return row.created_at.date() if row and row.created_at else None

@router.get("/api/debtors")
def list_debtors(
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.DEBTOR_ACCESS)),
):
    """Qarzdorlar ro'yxati. Eng shoshilinchi tepada: va'dasi o'tib
    ketganlar, keyin eski qarzlar."""
    today = date.today()
    q = scope_to_branch(db.query(models.Student), models.Student, user, branch_id)
    students = q.filter(models.Student.status.in_(["active", "trial", "frozen"])).all()

    # Oxirgi bog'lanish yozuvlari
    contacts: dict[int, models.DebtorContact] = {}
    for c in (db.query(models.DebtorContact)
              .order_by(models.DebtorContact.contacted_on).all()):
        contacts[c.student_id] = c

    rows = []
    for s in students:
        bal = student_balance(db, s.id)
        if bal >= 0:
            continue
        debt = abs(bal)
        since = _last_charge_date(db, s.id) or s.enrolled_date or today
        days = (today - since).days
        key, label, tone = roles.debt_urgency(days)

        c = contacts.get(s.id)
        promised = c.promised_date if c else None
        broken = bool(promised and promised < today)

        rows.append({
            "student_id": s.id,
            "public_id": s.public_id,
            "full_name": s.full_name,
            "phone": s.phone,
            "parent_phone": s.parent_phone,
            "group_id": s.group_id,
            "group": s.group.name if s.group else None,
            "branch": s.branch.name if s.branch else None,
            "status": s.status,
            "debt": round(debt, 2),
            "days": days,
            "urgency": key,
            "urgency_label": label,
            "urgency_tone": tone,
            "last_contact": c.contacted_on.isoformat() if c else None,
            "last_result": c.result if c else None,
            "last_result_label": (roles.DEBT_CONTACT_LABELS.get(c.result, c.result)
                                  if c else None),
            "last_note": c.note if c else None,
            "promised_date": promised.isoformat() if promised else None,
            "promised_amount": c.promised_amount if c else None,
            # Va'dasini buzgan - eng birinchi shunga qo'ng'iroq qilinadi
            "promise_broken": broken,
            "days_since_contact": ((today - c.contacted_on).days
                                   if c and c.contacted_on else None),
        })

    # Tartib: va'dasi buzilgan → bugun va'da qilgan → hech bog'lanilmagan
    # → qarzi kattaroq
    def sort_key(r):
        promise_today = r["promised_date"] == today.isoformat()
        return (
            0 if r["promise_broken"] else 1 if promise_today else
            2 if not r["last_contact"] else 3,
            -r["debt"],
        )
    rows.sort(key=sort_key)

    return {
        "rows": rows,
        "total_debt": round(sum(r["debt"] for r in rows), 2),
        "count": len(rows),
        "broken_promises": sum(1 for r in rows if r["promise_broken"]),
        "due_today": sum(1 for r in rows
                         if r["promised_date"] == today.isoformat()),
        "never_contacted": sum(1 for r in rows if not r["last_contact"]),
        "results": [{"key": k, "label": lbl, "tone": t}
                    for k, lbl, t in roles.DEBT_CONTACT_RESULTS],
    }

@router.post("/api/debtors/contact")
def add_debtor_contact(
    payload: schemas.DebtorContactCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.DEBTOR_ACCESS)),
):
    """"Bog'lanildi" tugmasi. Qachon to'layman deganini yozib qo'yadi —
    ertaga kimga qo'ng'iroq qilish kerakligi shundan chiqadi."""
    s = db.query(models.Student).get(payload.student_id)
    if not s:
        raise HTTPException(404, "O'quvchi topilmadi")
    if payload.result not in roles.DEBT_CONTACT_LABELS:
        raise HTTPException(400, "Noto'g'ri natija")
    if payload.result == "promised" and not payload.promised_date:
        raise HTTPException(400, "Qachonga to'layman deganini yozing")

    c = models.DebtorContact(
        student_id=s.id,
        contacted_on=date.today(),
        promised_date=payload.promised_date,
        promised_amount=payload.promised_amount,
        result=payload.result,
        note=payload.note,
        created_by=user.full_name)
    db.add(c); db.commit()
    audit.log(db, user, entity="student", action="update", entity_id=s.id,
              entity_label=s.full_name, branch_id=s.branch_id,
              field="Qarz bo'yicha bog'lanildi",
              new_value=roles.DEBT_CONTACT_LABELS[payload.result]
              + (f" — {payload.promised_date}" if payload.promised_date else ""))
    db.commit()
    return {"ok": True}

def _work_days(start: date, end: date) -> int:
    """[start, end) oralig'idagi ish kunlari (yakshanba dam)."""
    n, d = 0, start
    while d < end:
        if d.weekday() != 6:
            n += 1
        d += timedelta(days=1)
    return n

def _plan_fakt(db: Session, metric: str, start: date, end: date):
    """Ko'rsatkich fakti [start, end) oralig'ida — tirik ma'lumotdan."""
    if metric == "leads":
        d0, d1 = _utc_window(start, end)
        return db.query(models.Lead).filter(
            models.Lead.created_at >= d0,
            models.Lead.created_at < d1).count()
    if metric == "visits":
        d0, d1 = _utc_window(start, end)
        return db.query(models.Lead).filter(
            models.Lead.created_at >= d0, models.Lead.created_at < d1,
            models.Lead.stage.in_(("trial_attended", "converted"))).count()
    if metric in ("new_payments", "old_payments"):
        d0, d1 = _utc_window(start, end)
        pays = db.query(models.Payment).filter(
            models.Payment.kind == "payment", models.Payment.amount > 0,
            models.Payment.created_at >= d0,
            models.Payment.created_at < d1).all()
        if not pays:
            return 0
        sids = {p.student_id for p in pays}
        firsts = dict(
            db.query(models.Payment.student_id,
                     func.min(models.Payment.created_at))
            .filter(models.Payment.kind == "payment",
                    models.Payment.amount > 0,
                    models.Payment.student_id.in_(sids))
            .group_by(models.Payment.student_id).all())
        new_ids = {sid for sid, first in firsts.items() if first >= d0}
        # Yangi = birinchi to'lovi shu oraliqda; eski = qolgan to'lovlar
        if metric == "new_payments":
            return len(new_ids)
        return len([p for p in pays if p.student_id not in new_ids])
    if metric == "students":
        today = roles.local_today()
        if start <= today < end or (start.year, start.month) == (
                today.year, today.month):
            return db.query(models.Student).filter(
                models.Student.status == "active").count()
        m0 = date(start.year, start.month, 1)
        m1 = date(m0.year + 1, 1, 1) if m0.month == 12 else \
            date(m0.year, m0.month + 1, 1)
        return (db.query(models.Attendance.student_id)
                .join(models.Lesson,
                      models.Lesson.id == models.Attendance.lesson_id)
                .filter(models.Lesson.date >= m0, models.Lesson.date < m1)
                .distinct().count())
    if metric == "revenue":
        d0, d1 = _utc_window(start, end)
        return round(db.query(func.coalesce(
            func.sum(models.Payment.amount), 0)).filter(
            models.Payment.kind == "payment", models.Payment.amount > 0,
            models.Payment.created_at >= d0,
            models.Payment.created_at < d1).scalar() or 0, 0)
    if metric == "expenses":
        return round(db.query(func.coalesce(
            func.sum(models.Expense.amount), 0)).filter(
            models.Expense.date >= start,
            models.Expense.date < end).scalar() or 0, 0)
    if metric == "profit":
        rev = _plan_fakt(db, "revenue", start, end)
        exp = _plan_fakt(db, "expenses", start, end)
        return round((rev or 0) - (exp or 0), 0)
    return None   # online_visits / online_payments — qo'lda ham emas, hozircha yo'q

def _plan_windows(year: int, granularity: str, month: int | None):
    """Davr ustunlari: (label, start, end, oy_kaliti)."""
    wins = []
    if granularity == "month":
        for m in roles.PLAN_MONTHS:
            y = roles.plan_month_year(year, m)
            s = date(y, m, 1)
            e = date(y + 1, 1, 1) if m == 12 else date(y, m + 1, 1)
            wins.append((roles.UZ_MONTHS[m - 1], s, e, m))
    elif granularity == "week":
        y0 = date(year, 9, 1)
        y1 = date(year + 1, 9, 1)
        s = y0
        i = 1
        while s < y1:
            e = min(s + timedelta(days=7 - s.weekday() if i == 1 else 7), y1)
            wins.append((f"Hafta {i}", s, e, s.month))
            s = e
            i += 1
    else:  # day — bitta oy ichida
        m = month or roles.PLAN_MONTHS[0]
        y = roles.plan_month_year(year, m)
        s0 = date(y, m, 1)
        e0 = date(y + 1, 1, 1) if m == 12 else date(y, m + 1, 1)
        d = s0
        while d < e0:
            wins.append((f"{d.day:02d}/{d.month:02d}", d,
                         d + timedelta(days=1), m))
            d += timedelta(days=1)
    return wins

def _plan_distribute(kind: str, plans: dict, year: int, win) -> float | None:
    """Oylik rejadan davr rejasini chiqarish.

    flow/money — oy rejasi ish kunlariga teng bo'linadi;
    stock — o'tgan oy darajasidan shu oy maqsadigacha tekis o'sadi."""
    label, s, e, m = win
    if plans.get(m) is None:
        return None
    mv = plans[m]
    y = roles.plan_month_year(year, m)
    m0 = date(y, m, 1)
    m1 = date(y + 1, 1, 1) if m == 12 else date(y, m + 1, 1)
    if s <= m0 and e >= m1:      # butun oy
        return mv
    if kind == "stock":
        pm = 8 if m == 9 else (m - 1 if m != 1 else 12)
        prev = plans.get(pm, mv)
        total = (m1 - m0).days
        done = min((e - m0).days, total)
        return round(prev + (mv - prev) * done / total, 1)
    wd_total = _work_days(m0, m1) or 1
    wd = _work_days(max(s, m0), min(e, m1))
    return round(mv * wd / wd_total, 1)

@router.get("/api/plan")
def get_plan(year: int | None = None, granularity: str = "month",
             month: int | None = None,
             db: Session = Depends(get_db),
             user=Depends(require_role(*roles.PLAN_VIEW))):
    """Reja va fakt — rahbarning bosh jadvali. Har rol o'z bo'limini
    ko'radi, asoschi hammasini."""
    today = roles.local_today()
    year = year or (today.year if today.month >= 9 else today.year - 1)
    if granularity not in ("month", "week", "day"):
        granularity = "month"
    secs = (list(roles.PLAN_SECTION_LABELS)
            if user.role == roles.FOUNDER
            else roles.plan_sections_for(user.role))
    wins = _plan_windows(year, granularity, month)
    targets = db.query(models.PlanTarget).filter(
        models.PlanTarget.year == year).all()
    plan_map = {}
    for t in targets:
        plan_map.setdefault(t.metric, {})[t.month] = t.value
    # SMM sotuv bo'limidan faqat ikkita ko'rsatkichni ko'radi
    smm_extra = (user.role == roles.SMM_MANAGER)
    rows = []
    for key, label, sec, kind, auto in roles.PLAN_METRICS:
        if sec not in secs and not (
                smm_extra and key in roles.PLAN_SMM_EXTRA):
            continue
        plans = plan_map.get(key, {})
        cells = []
        for w in wins:
            wl, s, e, m = w
            fakt = None
            if auto and s <= today:
                fakt = _plan_fakt(db, key, s, min(e, today + timedelta(
                    days=1)) if granularity == "day" else e)
            cells.append({
                "label": wl,
                "plan": _plan_distribute(kind, plans, year, w),
                "fakt": fakt,
                "future": s > today,
            })
        p_vals = [c["plan"] for c in cells if c["plan"] is not None]
        f_vals = [c["fakt"] for c in cells if c["fakt"] is not None]
        if kind == "stock":
            sum_plan = p_vals[-1] if p_vals else None
            sum_fakt = f_vals[-1] if f_vals else None
        else:
            sum_plan = round(sum(p_vals), 0) if p_vals else None
            sum_fakt = round(sum(f_vals), 0) if f_vals else None
        # Bugungacha bo'lgan reja — "shu ketishda" prognozi uchun
        ptd = 0.0
        for w, c in zip(wins, cells):
            wl, ws, we, wm = w
            if we <= today + timedelta(days=1):
                if c["plan"] is not None:
                    ptd = ptd + c["plan"] if kind != "stock" else c["plan"]
            elif ws <= today:
                part = _plan_distribute(kind, plan_map.get(key, {}), year,
                                        (wl, ws, today + timedelta(days=1),
                                         wm))
                if part is not None:
                    ptd = ptd + part if kind != "stock" else part
        percent = round(sum_fakt / sum_plan * 100, 0) \
            if sum_plan and sum_fakt is not None else None
        pace = round(sum_fakt / ptd * 100, 0) \
            if ptd and sum_fakt is not None else None
        rows.append({"metric": key, "label": label, "section": sec,
                     "kind": kind, "auto": auto, "cells": cells,
                     "sum_plan": sum_plan, "sum_fakt": sum_fakt,
                     "percent": percent, "pace": pace})
    return {
        "year": year, "year_label": roles.plan_year_label(year),
        "granularity": granularity, "month": month,
        "months": roles.PLAN_MONTHS,
        "sections": {s: roles.PLAN_SECTION_LABELS[s]
                     for s in (list(secs) + (["sotuv"]
                               if smm_extra and "sotuv" not in secs
                               else []))},
        "columns": [w[0] for w in wins],
        "sundays": [i for i, w in enumerate(wins)
                    if granularity == "day" and w[1].weekday() == 6],
        "rows": rows,
        "can_edit": user.role in tuple(roles.PLAN_EDIT),
        "plan_raw": plan_map,
        "hint": ("Reja yil boshida oy kesimida tuziladi; hafta va kun "
                 "rejasi oydan avtomat taqsimlanadi (yakshanba dam). "
                 "Fakt platformadan o'zi to'ladi."),
    }

@router.get("/api/plan/suggest")
def plan_suggest(year: int, growth: int = roles.PLAN_DEFAULT_GROWTH,
                 db: Session = Depends(get_db),
                 user=Depends(require_role(*roles.PLAN_EDIT))):
    """O'tgan yil fakti + o'sish foizi — yangi reja uchun taklif."""
    growth = max(0, min(100, growth))
    out = {}
    for key, label, sec, kind, auto in roles.PLAN_METRICS:
        if not auto:
            out[key] = {}
            continue
        vals = {}
        for m in roles.PLAN_MONTHS:
            y = roles.plan_month_year(year - 1, m)
            s = date(y, m, 1)
            e = date(y + 1, 1, 1) if m == 12 else date(y, m + 1, 1)
            f = _plan_fakt(db, key, s, e)
            if f:
                vals[m] = round(f * (1 + growth / 100),
                                -3 if kind == "money" else 0)
        out[key] = vals
    return {"year": year, "growth": growth, "suggest": out}

@router.put("/api/plan/{year}")
def save_plan(year: int, payload: schemas.PlanSaveIn,
              db: Session = Depends(get_db),
              user=Depends(require_role(*roles.PLAN_EDIT))):
    """Yillik rejani saqlash (bor oylar ustidan yoziladi)."""
    n = 0
    for it in payload.items:
        if it.metric not in roles.PLAN_METRIC_KEYS or not (
                1 <= it.month <= 12):
            raise HTTPException(400, f"Noto'g'ri ko'rsatkich: {it.metric}")
        row = db.query(models.PlanTarget).filter_by(
            year=year, metric=it.metric, month=it.month).first()
        if row:
            row.value = it.value
        else:
            db.add(models.PlanTarget(year=year, metric=it.metric,
                                     month=it.month, value=it.value,
                                     created_by=user.full_name))
        n += 1
    db.commit()
    audit.log(db, user, entity="plan", action="save", entity_id=year,
              entity_label=roles.plan_year_label(year),
              new_value=f"{n} ta katak", commit=True)
    return {"ok": True, "saved": n}

@router.get("/api/finance/break-even")
def finance_break_even(year: int | None = None, month: int | None = None,
                       branch_id: int | None = None, scope: str = "company",
                       db: Session = Depends(get_db),
                       user=Depends(require_role(*roles.FINANCE_ACCESS))):
    """Zararsizlik nuqtasi: nechta o'quvchida markaz o'zini oqlaydi.

    O'zgarmas xarajatlar (ijara, kommunal, ma'muriy oylik, soliq) —
    o'quvchi bo'lmasa ham to'lanadi. O'zgaruvchan (ustozlar ish haqi,
    reklama, kanstovar va h.k.) — o'quvchi soniga qarab o'sadi.
    Kirim chizig'i umumiy xarajat chizig'ini kesgan joy — zararsizlik."""
    today = roles.local_today()
    y, m = year or today.year, month or today.month
    start, end = billing.month_bounds(y, m)
    period = f"{y:04d}-{m:02d}"

    _tot, by_cat = _expenses_total(db, user, start, end, branch_id)
    fixed = round(sum(a for c, a in by_cat.items()
                      if roles.expense_is_fixed(c)), 0)
    var_exp = round(sum(a for c, a in by_cat.items()
                        if not roles.expense_is_fixed(c)), 0)
    payroll = round(_payroll_total(db, user, period, branch_id) or 0, 0)

    d0, d1 = _utc_window(start, end)
    revenue = round(db.query(func.coalesce(
        func.sum(models.Payment.amount), 0)).filter(
        models.Payment.kind == "payment", models.Payment.amount > 0,
        models.Payment.created_at >= d0,
        models.Payment.created_at < d1).scalar() or 0, 0)

    sq = db.query(models.Student).filter(models.Student.status == "active")
    if branch_id:
        sq = sq.filter(models.Student.branch_id == branch_id)
    students = sq.count()

    # Bir o'quvchidan o'rtacha oylik kirim va o'zgaruvchan xarajat
    if students and revenue:
        price = round(revenue / students, 0)
    else:
        avg_fee = db.query(func.avg(
            models.Group.lesson_price *
            models.Group.standard_lessons_per_month)).scalar()
        price = round(avg_fee or 480000, 0)
    var_per = round((var_exp + payroll) / students, 0) if students else 0

    margin = price - var_per
    breakeven = None
    if margin > 0 and fixed > 0:
        import math
        breakeven = math.ceil(fixed / margin)

    # Grafik nuqtalari: 0 dan (zararsizlikning ~1.6 barobari yoki
    # hozirgi soni + 50) gacha
    n_max = max(200, students + 50,
                int((breakeven or 0) * 1.6) if breakeven else 0)
    step = max(5, round(n_max / 40 / 5) * 5)
    points = []
    n = 0
    while n <= n_max:
        points.append({"n": n,
                       "revenue": round(price * n, 0),
                       "fixed": fixed,
                       "total_cost": round(fixed + var_per * n, 0)})
        n += step

    if scope in ("branch", "course", "group"):
        return _break_even_cards(db, user, scope, y, m, fixed,
                                 var_exp, payroll, students, price)

    return {
        "period": period,
        "fixed": fixed,
        "variable_expenses": var_exp,
        "teacher_payroll": payroll,
        "variable_per_student": var_per,
        "price_per_student": price,
        "unit_margin": margin,
        "students": students,
        "revenue": revenue,
        "breakeven_students": breakeven,
        "safety": round((students - breakeven) / breakeven * 100, 0)
        if breakeven and breakeven > 0 else None,
        "points": points,
        "categories": sorted(
            [{"category": c,
              "label": roles.EXPENSE_CATEGORY_LABELS.get(c, c),
              "amount": round(a, 0),
              "fixed": roles.expense_is_fixed(c)}
             for c, a in by_cat.items() if a],
            key=lambda r: -r["amount"])
        + ([{"category": "teacher_payroll", "label": "Ustozlar ish haqi",
             "amount": payroll, "fixed": False}] if payroll else []),
        "hint": ("O'zgarmas: ijara, kommunal, ma'muriy oylik, soliq. "
                 "O'zgaruvchan: ustozlar ish haqi, reklama, kanstovar va "
                 "boshqalar. Zararsizlik = o'zgarmas / (bir o'quvchi "
                 "narxi - bir o'quvchiga o'zgaruvchan xarajat)."),
    }

def _fin_month(db: Session, user, y: int, m: int) -> dict:
    """Bir oyning asosiy moliyaviy raqamlari (overview uchun)."""
    start, end = billing.month_bounds(y, m)
    period = f"{y:04d}-{m:02d}"
    methods = _income_by_method(db, user, start, end, None)
    collected = round(sum(methods.values()), 0)
    d0, d1 = _utc_window(start, end)
    disc = abs(db.query(func.coalesce(func.sum(models.Payment.amount), 0))
               .filter(models.Payment.kind == "discount",
                       models.Payment.created_at >= d0,
                       models.Payment.created_at < d1).scalar() or 0)
    refunds = abs(db.query(func.coalesce(func.sum(models.Payment.amount), 0))
                  .filter(models.Payment.kind == "payment",
                          models.Payment.amount < 0,
                          models.Payment.created_at >= d0,
                          models.Payment.created_at < d1).scalar() or 0)
    exp_total, by_cat = _expenses_total(db, user, start, end, None)
    payroll = round(_payroll_total(db, user, period, None) or 0, 0)
    tax = round(sum(a for c, a in by_cat.items()
                    if roles.EXPENSE_CATEGORY_GROUP.get(c) == "tax"), 0)
    fixed = round(sum(a for c, a in by_cat.items()
                      if roles.expense_is_fixed(c)), 0)
    charges = abs(db.query(func.coalesce(func.sum(models.Payment.amount), 0))
                  .filter(models.Payment.kind == "charge",
                          models.Payment.period == period).scalar() or 0)
    net_income = round(collected - refunds, 0)
    total_exp = round(exp_total + payroll, 0)
    return {
        "methods": methods, "collected": collected,
        "discounts": round(disc, 0), "refunds": round(refunds, 0),
        "net_income": net_income,
        "expenses": round(exp_total, 0), "payroll": payroll,
        "total_expenses": total_exp, "tax": tax, "fixed": fixed,
        "operating_profit": round(net_income - (total_exp - tax), 0),
        "net_profit": round(net_income - total_exp, 0),
        "charges": round(charges, 0), "by_cat": by_cat,
    }

@router.get("/api/finance/overview")
def finance_overview(db: Session = Depends(get_db),
                     user=Depends(require_role(roles.FOUNDER,
                                               roles.FINANCE_DIRECTOR))):
    """Asoschi va moliya direktori uchun bosh sahifa: 10 karta, har
    birida joriy summa, oylik reja, bajarilish %, o'tgan oyga farq,
    holat rangi va bosilganda batafsil tarkib."""
    today = roles.local_today()
    y, m = today.year, today.month
    py, pm = (y - 1, 12) if m == 1 else (y, m - 1)
    cur = _fin_month(db, user, y, m)
    prev = _fin_month(db, user, py, pm)

    # Rejalar (Reja va Fakt bo'limidan)
    plan_year = y if m >= 9 else y - 1
    plans = {t.metric: t.value for t in db.query(models.PlanTarget).filter(
        models.PlanTarget.year == plan_year,
        models.PlanTarget.month == m).all()}
    p_rev, p_exp, p_prof = (plans.get("revenue"), plans.get("expenses"),
                            plans.get("profit"))

    # Qarzdorlik: balansi manfiy o'quvchilar
    bal = (db.query(models.Payment.student_id,
                    func.sum(models.Payment.amount))
           .group_by(models.Payment.student_id).all())
    debtors = [(sid, b) for sid, b in bal if (b or 0) < -1000]
    total_debt = round(sum(-b for _, b in debtors), 0)

    # Oy oxiri prognozi
    total_days = (billing.month_bounds(y, m)[1] - billing.month_bounds(
        y, m)[0]).days
    elapsed = max((today - billing.month_bounds(y, m)[0]).days + 1, 1)
    frac = min(elapsed / total_days, 1.0)
    f_rev = round(cur["collected"] / frac, 0)
    f_prof = round(cur["net_profit"] / frac, 0)

    commitment = round(cur["fixed"] + cur["payroll"] / max(frac, 0.2), 0)
    coll_rate = round(cur["collected"] / cur["charges"] * 100, 1) \
        if cur["charges"] else None

    def state(value, plan, lower_better=False, prev_v=None):
        if plan:
            p = value / plan * 100
            if lower_better:
                return "green" if p <= 100 else ("amber" if p <= 110
                                                 else "red")
            return "green" if p >= 100 else ("amber" if p >= 80 else "red")
        if prev_v is not None:
            d = value - prev_v
            if lower_better:
                d = -d
            return "green" if d >= 0 else "amber"
        return "amber"

    mlbl = roles.PAYMENT_METHOD_LABELS

    def card(key, label, sub, value, plan, prev_v, lower=False,
             details=None, unit="so'm"):
        return {
            "key": key, "label": label, "sub": sub,
            "value": round(value, 1) if value is not None else None,
            "plan": plan,
            "plan_pct": round(value / plan * 100, 0)
            if plan and value is not None else None,
            "prev": prev_v,
            "diff": round(value - prev_v, 1)
            if value is not None and prev_v is not None else None,
            "state": state(value or 0, plan, lower, prev_v),
            "details": details or [], "unit": unit,
        }

    cards = [
        card("cash", "Mavjud pul", "Kassa + bank + to'lov tizimlari",
             cur["collected"], None, prev["collected"],
             details=[{"label": mlbl.get(k, k), "value": round(v, 0)}
                      for k, v in cur["methods"].items() if v]),
        card("collected", "Shu oy yig'ilgan pul", "Real tushgan to'lov",
             cur["collected"], p_rev, prev["collected"],
             details=[{"label": "Hisoblangan (charge)",
                       "value": cur["charges"]},
                      {"label": "Yig'ilgan", "value": cur["collected"]}]),
        card("net_income", "Shu oy sof daromad",
             "Chegirma va refunddan keyin", cur["net_income"], p_rev,
             prev["net_income"],
             details=[{"label": "Tushum", "value": cur["collected"]},
                      {"label": "Chegirmalar", "value": -cur["discounts"]},
                      {"label": "Refundlar", "value": -cur["refunds"]}]),
        card("expenses", "Shu oy xarajat", "Tasdiqlangan real xarajat",
             cur["total_expenses"], p_exp, prev["total_expenses"],
             lower=True,
             details=[{"label": roles.EXPENSE_CATEGORY_LABELS.get(c, c),
                       "value": round(v, 0)}
                      for c, v in sorted(cur["by_cat"].items(),
                                         key=lambda kv: -kv[1])[:8]]
             + [{"label": "Ustozlar ish haqi", "value": cur["payroll"]}]),
        card("op_profit", "Operatsion foyda",
             "Asosiy faoliyatdan qolgan foyda", cur["operating_profit"],
             p_prof, prev["operating_profit"],
             details=[{"label": "Sof daromad", "value": cur["net_income"]},
                      {"label": "Operatsion xarajat (soliqsiz)",
                       "value": -(cur["total_expenses"] - cur["tax"])}]),
        card("net_profit", "Sof foyda", "Barcha xarajatlardan keyin",
             cur["net_profit"], p_prof, prev["net_profit"],
             details=[{"label": "Sof daromad", "value": cur["net_income"]},
                      {"label": "Barcha xarajatlar",
                       "value": -cur["total_expenses"]}]),
        card("debt", "Jami qarzdorlik", "Olinishi kerak bo'lgan pul",
             total_debt, None, None, lower=True,
             details=[{"label": "Qarzdor o'quvchilar",
                       "value": len(debtors), "unit": "ta"}]),
        card("collection", "Collection rate",
             "To'lanishi kerak bo'lgan pulning yig'ilgan qismi",
             coll_rate, None, None, unit="%",
             details=[{"label": "Hisoblangan", "value": cur["charges"]},
                      {"label": "Yig'ilgan", "value": cur["collected"]}]),
        card("commitment", "30 kunlik majburiyat",
             "Maosh, ijara, soliq va boshqalar", commitment, None, None,
             lower=True,
             details=[{"label": "O'zgarmas xarajatlar",
                       "value": cur["fixed"]},
                      {"label": "Ustozlar ish haqi (prognoz)",
                       "value": round(cur["payroll"] / max(frac, 0.2), 0)}]),
        card("forecast", "Oy oxiri prognozi",
             "Kutilayotgan tushum va foyda", f_rev, p_rev, None,
             details=[{"label": "Kutilayotgan tushum", "value": f_rev},
                      {"label": "Kutilayotgan sof foyda",
                       "value": f_prof},
                      {"label": "Oy o'tdi",
                       "value": round(frac * 100, 0), "unit": "%"}]),
    ]
    if coll_rate is not None:
        for c in cards:
            if c["key"] == "collection":
                c["state"] = ("green" if coll_rate >= 90 else
                              "amber" if coll_rate >= 70 else "red")
    return {"period": f"{y:04d}-{m:02d}", "cards": cards,
            "hint": ("Rejalar 'Reja va Fakt' bo'limidan olinadi. Rang: "
                     "yashil — reja bajarilmoqda, sariq — 80-100%, "
                     "qizil — orqada. Kartaga bosib tarkibini ko'ring.")}

def _break_even_cards(db: Session, user, scope: str, y: int, m: int,
                      fixed: float, var_exp: float, payroll: float,
                      students_total: int, price_avg: float) -> dict:
    """Filial / kurs / guruh kesimida zararsizlik kartalari.

    O'zgarmas xarajatlar o'quvchi ulushiga qarab taqsimlanadi (filial va
    kursda), guruhda esa guruhlar soniga teng bo'linadi — kichik guruh
    ham o'z ulushini ko'tarishi kerak."""
    start, end = billing.month_bounds(y, m)
    d0, d1 = _utc_window(start, end)
    groups = db.query(models.Group).all()
    studs = db.query(models.Student).filter(
        models.Student.status == "active",
        models.Student.group_id.isnot(None)).all()
    by_group = {}
    for st in studs:
        by_group.setdefault(st.group_id, []).append(st.id)
    n_total = max(students_total, 1)
    other_var_ps = round(var_exp / n_total, 0)      # payrollsiz
    var_ps_full = round((var_exp + payroll) / n_total, 0)
    rooms = {r.id: r for r in db.query(models.Room).all()}

    # O'quvchi bo'yicha tushum (filial/kurs uchun aniqroq)
    pays = (db.query(models.Payment.student_id,
                     func.sum(models.Payment.amount))
            .filter(models.Payment.kind == "payment",
                    models.Payment.amount > 0,
                    models.Payment.created_at >= d0,
                    models.Payment.created_at < d1)
            .group_by(models.Payment.student_id).all())
    pay_by_student = {sid: v for sid, v in pays}
    stud_group = {st.id: st.group_id for st in studs}

    def agg_cards(key_of, label_of):
        buckets = {}
        for g in groups:
            ids = by_group.get(g.id, [])
            if not ids:
                continue
            k = key_of(g)
            if k is None:
                continue
            b = buckets.setdefault(k, {"students": 0, "revenue": 0.0})
            b["students"] += len(ids)
            b["revenue"] += sum(pay_by_student.get(s, 0) for s in ids)
        cards = []
        for k, b in buckets.items():
            n = b["students"]
            share = n / n_total
            fx = round(fixed * share, 0)
            price = round(b["revenue"] / n, 0) if b["revenue"] and n \
                else price_avg
            margin = price - var_ps_full
            be = None
            if margin > 0 and fx > 0:
                import math
                be = math.ceil(fx / margin)
            safety = (n - be) if be is not None else None
            status = "green"
            if be is None or n < (be or 0):
                status = "red"
            elif be and (n - be) / be * 100 < 15:
                status = "amber"
            cards.append({
                "key": str(k), "label": label_of(k),
                "students": n, "breakeven": be, "safety": safety,
                "revenue": round(b["revenue"], 0),
                "breakeven_revenue": round((be or 0) * price, 0)
                if be else None,
                "status": status,
            })
        return sorted(cards, key=lambda c: (
            {"red": 0, "amber": 1, "green": 2}[c["status"]],
            -(c["students"] or 0)))

    if scope == "branch":
        b_names = {b.id: b.name for b in db.query(models.Branch).all()}
        cards = agg_cards(lambda g: g.branch_id,
                          lambda k: b_names.get(k, "Filialsiz"))
    elif scope == "course":
        subj = dict(roles.SUBJECTS)
        cards = agg_cards(
            lambda g: (g.subject or "boshqa", g.level or "-"),
            lambda k: f"{subj.get(k[0], k[0])} · "
                      f"{roles.LEVEL_LABELS.get(k[1], k[1])}")
    else:   # group
        n_groups = max(len([g for g in groups if by_group.get(g.id)]), 1)
        fx_per_group = round(fixed / n_groups, 0)
        cards = []
        # Parallel yarim bo'sh guruhlarni topish uchun
        fill = {}
        for g in groups:
            cap = _group_capacity(g, rooms)
            n = len(by_group.get(g.id, []))
            fill[g.id] = (n / cap * 100) if cap else None
        for g in groups:
            n = len(by_group.get(g.id, []))
            if not n:
                continue
            price = round((g.lesson_price or 40000) *
                          (g.standard_lessons_per_month or 12), 0)
            t_rate = g.teacher_rate_per_student or 0
            margin = price - t_rate - other_var_ps
            be = None
            if margin > 0:
                import math
                be = math.ceil(fx_per_group / margin)
            result = round(n * price - (fx_per_group +
                                        n * (t_rate + other_var_ps)), 0)
            cap = _group_capacity(g, rooms)
            free = (cap - n) if cap else None
            recs = []
            if result < 0:
                if free and free > 0:
                    recs += ["Guruhni to'ldirish",
                             "Reklama so'rovi yaratish"]
                else:
                    recs.append("Jadvalni o'zgartirish")
                twin = [o for o in groups if o.id != g.id
                        and o.branch_id == g.branch_id
                        and o.subject == g.subject and o.level == g.level
                        and by_group.get(o.id)
                        and (fill.get(o.id) or 100) < 60]
                if twin:
                    recs.append(f"Parallel guruh bilan birlashtirish "
                                f"({twin[0].name})")
                if be and n < be / 2:
                    recs.append("Yopish masalasini ko'rib chiqish")
            status = ("red" if result < 0 else
                      "amber" if be and (n - be) / be * 100 < 15
                      else "green")
            cards.append({
                "key": str(g.id), "label": g.name,
                "sub": f"{dict(roles.SUBJECTS).get(g.subject or '', '')} "
                       f"{roles.LEVEL_LABELS.get(g.level or '', '')}".strip(),
                "students": n, "breakeven": be,
                "safety": (n - be) if be is not None else None,
                "monthly_result": result,
                "free": free,
                "potential": round(free * price, 0) if free else 0,
                "price": price, "status": status,
                "recommendations": recs,
            })
        cards = sorted(cards, key=lambda c: (
            {"red": 0, "amber": 1, "green": 2}[c["status"]],
            c["monthly_result"]))
    return {"period": f"{y:04d}-{m:02d}", "scope": scope, "cards": cards,
            "hint": ("O'zgarmas xarajatlar o'quvchi ulushiga qarab "
                     "taqsimlangan; guruhlarda — guruh boshiga teng. "
                     "Sariq — xavfsizlik zaxirasi 15% dan past, "
                     "qizil — zararda.")}

def _month_win(y: int, m: int):
    s = date(y, m, 1)
    e = date(y + 1, 1, 1) if m == 12 else date(y, m + 1, 1)
    return s, e

@router.get("/api/finance/budget")
def finance_budget(year: int | None = None, month: int | None = None,
                   db: Session = Depends(get_db),
                   user=Depends(require_role(*roles.FINANCE_ACCESS))):
    """Budjet: yillik/oylik/filial/bo'lim kesimlari, reja-fakt va yil
    oxiri prognozi. Reja BudgetLine'dan, fakt tirik ma'lumotdan."""
    today = roles.local_today()
    year = year or (today.year if today.month >= 9 else today.year - 1)
    month = month or today.month
    lines = db.query(models.BudgetLine).filter(
        models.BudgetLine.year == year).all()

    def plan_of(m, kind, cat=None, br=None):
        return round(sum(
            l.amount for l in lines
            if l.month == m and l.kind == kind
            and (cat is None or l.category == cat)
            and (br is None or l.branch_id == br)), 0)

    # ---- Yillik: oyma-oy reja va fakt ----
    yearly, ytd_inc, ytd_exp = [], 0.0, 0.0
    rest_inc, rest_exp = 0.0, 0.0
    for m in roles.PLAN_MONTHS:
        yy = roles.plan_month_year(year, m)
        s, e = _month_win(yy, m)
        p_inc = round(sum(l.amount for l in lines
                          if l.month == m and l.kind == "income"), 0)
        p_exp = round(sum(l.amount for l in lines
                          if l.month == m and l.kind == "expense"), 0)
        done = s <= today
        f_inc = _plan_fakt(db, "revenue", s, e) if done else None
        if done:
            et, _bc = _expenses_total(db, user, s, e, None)
            pr = _payroll_total(db, user, f"{yy:04d}-{m:02d}", None) or 0
            f_exp = round(et + pr, 0)
        else:
            f_exp = None
        if done:
            ytd_inc += f_inc or 0
            ytd_exp += f_exp or 0
        else:
            rest_inc += p_inc
            rest_exp += p_exp
        yearly.append({
            "month": m, "label": roles.UZ_MONTHS[m - 1],
            "plan_income": p_inc, "fakt_income": f_inc,
            "plan_expense": p_exp, "fakt_expense": f_exp,
            "plan_profit": round(p_inc - p_exp, 0),
            "fakt_profit": round((f_inc or 0) - (f_exp or 0), 0)
            if done else None,
        })

    # ---- Oylik: tanlangan oy kategoriyalar kesimida ----
    yy = roles.plan_month_year(year, month)
    s, e = _month_win(yy, month)
    _t, by_cat = _expenses_total(db, user, s, e, None)
    payroll = round(_payroll_total(db, user, f"{yy:04d}-{month:02d}",
                                   None) or 0, 0)
    cats = []
    all_cats = set(roles.EXPENSE_CATEGORIES) | set(by_cat) | {
        l.category for l in lines
        if l.month == month and l.kind == "expense" and l.category}
    for c in sorted(all_cats - {None}):
        p = plan_of(month, "expense", cat=c)
        f = round(by_cat.get(c, 0), 0)
        if not p and not f:
            continue
        cats.append({"category": c,
                     "label": roles.EXPENSE_CATEGORY_LABELS.get(c, c),
                     "plan": p, "fakt": f,
                     "pct": round(f / p * 100, 0) if p else None})
    cats.append({"category": "teacher_payroll",
                 "label": "Ustozlar ish haqi (avtomat)",
                 "plan": plan_of(month, "expense", cat="teacher_payroll"),
                 "fakt": payroll,
                 "pct": None})
    inc_fakt = _plan_fakt(db, "revenue", s, min(e, today + timedelta(
        days=1))) if s <= today else 0
    monthly = {
        "month": month, "label": roles.UZ_MONTHS[month - 1],
        "income_plan": plan_of(month, "income"),
        "income_fakt": round(inc_fakt or 0, 0),
        "categories": cats,
    }

    # ---- Filial kesimi (tanlangan oy) ----
    d0, d1 = _utc_window(s, e)
    br_rows = []
    for b in db.query(models.Branch).all():
        f_exp_b = round(db.query(func.coalesce(
            func.sum(models.Expense.amount), 0)).filter(
            models.Expense.branch_id == b.id,
            models.Expense.date >= s, models.Expense.date < e
        ).scalar() or 0, 0)
        f_inc_b = round(db.query(func.coalesce(
            func.sum(models.Payment.amount), 0))
            .join(models.Student,
                  models.Student.id == models.Payment.student_id)
            .filter(models.Student.branch_id == b.id,
                    models.Payment.kind == "payment",
                    models.Payment.amount > 0,
                    models.Payment.created_at >= d0,
                    models.Payment.created_at < d1).scalar() or 0, 0)
        br_rows.append({
            "branch": b.name,
            "plan_income": plan_of(month, "income", br=b.id),
            "fakt_income": f_inc_b,
            "plan_expense": plan_of(month, "expense", br=b.id),
            "fakt_expense": f_exp_b,
        })

    # ---- Bo'lim kesimi (tanlangan oy, xarajat guruhlari) ----
    dep_f = {}
    for c, v in by_cat.items():
        g = roles.EXPENSE_CATEGORY_GROUP.get(c, "other")
        dep_f[g] = dep_f.get(g, 0) + v
    dep_f["teacher_payroll"] = payroll
    dep_rows = []
    for g, lbl in roles.BUDGET_DEPARTMENT_LABELS.items():
        p = round(sum(
            l.amount for l in lines
            if l.month == month and l.kind == "expense" and l.category
            and (roles.EXPENSE_CATEGORY_GROUP.get(l.category, "other") == g
                 or l.category == g)), 0)
        f = round(dep_f.get(g, 0), 0)
        if p or f:
            dep_rows.append({"department": g, "label": lbl,
                             "plan": p, "fakt": f})

    # ---- Yil oxiri prognozi ----
    plan_inc_total = round(sum(r["plan_income"] for r in yearly), 0)
    plan_exp_total = round(sum(r["plan_expense"] for r in yearly), 0)
    fc_inc = round(ytd_inc + rest_inc, 0)
    fc_exp = round(ytd_exp + rest_exp, 0)
    forecast = {
        "ytd_income": round(ytd_inc, 0), "ytd_expense": round(ytd_exp, 0),
        "forecast_income": fc_inc, "forecast_expense": fc_exp,
        "forecast_profit": round(fc_inc - fc_exp, 0),
        "budget_income": plan_inc_total, "budget_expense": plan_exp_total,
        "budget_profit": round(plan_inc_total - plan_exp_total, 0),
    }
    return {
        "year": year, "year_label": roles.plan_year_label(year),
        "months": roles.PLAN_MONTHS, "yearly": yearly, "monthly": monthly,
        "branches": br_rows, "departments": dep_rows,
        "forecast": forecast,
        "can_edit": user.role in tuple(roles.BUDGET_EDIT),
        "expense_categories": [
            {"key": c, "label": roles.EXPENSE_CATEGORY_LABELS[c]}
            for c in roles.EXPENSE_CATEGORIES],
        "hint": ("Reja — budjet qatorlaridan, fakt — tirik ma'lumotdan "
                 "(to'lovlar, xarajatlar, ustozlar ish haqi avtomat). "
                 "Prognoz: o'tgan oylar fakti + qolgan oylar rejasi."),
    }

@router.put("/api/finance/budget/{year}")
def save_budget(year: int, payload: schemas.BudgetSaveIn,
                db: Session = Depends(get_db),
                user=Depends(require_role(*roles.BUDGET_EDIT))):
    n = 0
    for it in payload.items:
        if it.kind not in ("income", "expense") or not (1 <= it.month <= 12):
            raise HTTPException(400, "Noto'g'ri budjet qatori")
        row = db.query(models.BudgetLine).filter_by(
            year=year, month=it.month, kind=it.kind,
            category=it.category, branch_id=it.branch_id).first()
        if row:
            row.amount = it.amount
        else:
            db.add(models.BudgetLine(
                year=year, month=it.month, kind=it.kind,
                category=it.category, branch_id=it.branch_id,
                amount=it.amount, created_by=user.full_name))
        n += 1
    db.commit()
    audit.log(db, user, entity="budget", action="save", entity_id=year,
              entity_label=roles.plan_year_label(year),
              new_value=f"{n} ta qator", commit=True)
    return {"ok": True, "saved": n}

@router.get("/api/finance/payment-calendar")
def payment_calendar(year: int | None = None, month: int | None = None,
                     db: Session = Depends(get_db),
                     user=Depends(require_role(*roles.FINANCE_ACCESS))):
    """Oyning to'lov majburiyatlari sanasi bo'yicha + har sanada pul
    yetarliligi. Prognoz: shu kungacha yig'ilgan pul va kunlik o'rtacha
    tushum sur'ati bo'yicha."""
    today = roles.local_today()
    y, m = year or today.year, month or today.month
    s, e = _month_win(y, m)
    dues = db.query(models.PaymentDue).filter(
        models.PaymentDue.active == 1).all()
    items = []
    for dd in dues:
        if dd.recurring and dd.due_day:
            try:
                dt_ = date(y, m, min(dd.due_day, (e - timedelta(
                    days=1)).day))
            except ValueError:
                continue
        elif dd.date and s <= dd.date < e:
            dt_ = dd.date
        else:
            continue
        items.append({"id": dd.id, "date": dt_.isoformat(), "d": dt_,
                      "title": dd.title, "kind": dd.kind,
                      "kind_label": roles.PAYMENT_DUE_LABELS.get(
                          dd.kind, dd.kind),
                      "amount": round(dd.amount, 0),
                      "recurring": bool(dd.recurring),
                      "note": dd.note})
    items.sort(key=lambda r: (r["d"], -r["amount"]))

    # Pul oqimi prognozi
    collected = _plan_fakt(db, "revenue", s, min(
        e, today + timedelta(days=1))) or 0
    exp_so_far, _bc = _expenses_total(db, user, s, min(e, today +
                                                       timedelta(days=1)),
                                      None)
    cash = round(collected - exp_so_far, 0)
    elapsed = max((min(today, e - timedelta(days=1)) - s).days + 1, 1)
    daily = collected / elapsed
    total_due = 0.0
    for it in items:
        d_ = it.pop("d")
        inflow = daily * max((d_ - today).days, 0) if d_ > today else 0
        total_due += it["amount"]
        projected = round(cash + inflow - total_due, 0)
        it["projected_cash"] = projected
        it["enough"] = ("green" if projected >= it["amount"] * 0.5
                        else "amber" if projected >= 0 else "red")
        it["passed"] = d_ < today
    return {
        "period": f"{y:04d}-{m:02d}", "items": items,
        "cash_now": cash, "daily_pace": round(daily, 0),
        "total_due": round(total_due, 0),
        "kinds": [{"key": k, "label": l}
                  for k, l in roles.PAYMENT_DUE_KINDS],
        "can_edit": user.role in tuple(roles.BUDGET_EDIT),
        "hint": ("Har sanada: shu kungacha yig'ilgan pul + kutilayotgan "
                 "tushum (kunlik o'rtacha sur'at) - undan oldingi "
                 "majburiyatlar. Yashil - bemalol yetadi, sariq - zo'rg'a, "
                 "qizil - yetmaydi."),
    }

@router.post("/api/finance/payment-calendar")
def add_payment_due(payload: schemas.PaymentDueIn,
                    db: Session = Depends(get_db),
                    user=Depends(require_role(*roles.BUDGET_EDIT))):
    if not payload.due_day and not payload.date:
        raise HTTPException(400, "Sana yoki har oy kunini kiriting")
    if payload.due_day and not (1 <= payload.due_day <= 31):
        raise HTTPException(400, "Kun 1-31 oralig'ida bo'lsin")
    if payload.amount <= 0:
        raise HTTPException(400, "Summani kiriting")
    dd = models.PaymentDue(
        title=payload.title.strip(), kind=payload.kind,
        due_day=payload.due_day, date=payload.date,
        amount=payload.amount, branch_id=payload.branch_id,
        recurring=1 if (payload.recurring and payload.due_day) else 0,
        note=payload.note, created_by=user.full_name)
    db.add(dd)
    db.commit()
    audit.log(db, user, entity="payment_due", action="create",
              entity_id=dd.id, entity_label=dd.title,
              new_value=f"{dd.amount:,.0f}".replace(",", " "), commit=True)
    return {"ok": True, "id": dd.id}

@router.delete("/api/finance/payment-calendar/{due_id}")
def del_payment_due(due_id: int, db: Session = Depends(get_db),
                    user=Depends(require_role(*roles.BUDGET_EDIT))):
    dd = db.query(models.PaymentDue).get(due_id)
    if not dd:
        raise HTTPException(404, "Topilmadi")
    dd.active = 0
    db.commit()
    audit.log(db, user, entity="payment_due", action="delete",
              entity_id=dd.id, entity_label=dd.title, commit=True)
    return {"ok": True}

@router.put("/api/payments/{payment_id}")
def edit_payment(payment_id: int, payload: schemas.PaymentEditIn,
                 db: Session = Depends(get_db),
                 user=Depends(require_role(*roles.PAYMENT_EDIT))):
    """To'lov yoki hisoblangan (yechib olingan) summani tahrirlash.

    Yozuv O'CHIRILMAYDI, faqat summasi o'zgaradi — eski qiymat auditda
    qoladi. Ishora saqlanadi: hisoblangan (charge) minusligicha,
    to'lov plusligicha qoladi."""
    p = db.query(models.Payment).get(payment_id)
    if not p:
        raise HTTPException(404, "Yozuv topilmadi")
    st = db.query(models.Student).get(p.student_id)
    # Filial rahbari faqat o'z filialini tahrirlaydi
    if (user.role == roles.BRANCH_MANAGER and st
            and not _in_user_branches(db, user, st.branch_id)):
        raise HTTPException(403, "Bu o'quvchi boshqa filialga tegishli")
    if payload.amount <= 0:
        raise HTTPException(400, "Summani musbat son bilan kiriting")
    # Parallel tahrir: boshqa xodim shu orada o'zgartirgan bo'lsa —
    # jimgina ustidan yozmaymiz, 409 bilan ogohlantiramiz.
    if payload.expected_updated_at is not None:
        server_v = p.updated_at.isoformat() if p.updated_at else ""
        if server_v != payload.expected_updated_at:
            raise HTTPException(
                409, "Bu yozuvni shu orada boshqa xodim o'zgartirdi. "
                     "Sahifani yangilab, qaytadan urinib ko'ring.")
    old = p.amount
    sign = -1 if (p.amount or 0) < 0 or p.kind == "charge" else 1
    p.amount = sign * abs(round(payload.amount, 0))
    if payload.note is not None and payload.note.strip():
        p.note = payload.note.strip()
    # TO'LOV USULINI to'g'rilash (Jahongir: "adashib naqd kiritib
    # yuboribmiz aslida u plastikdan edi shuni togrlay olmayabmiz").
    # Faqat haqiqiy pul kirimida ma'noga ega; cashflow hisobotlari
    # avtomat to'g'rilanadi (ular shu maydondan o'qiydi).
    old_method = p.method
    if payload.method is not None and p.kind == "payment":
        if payload.method not in roles.PAYMENT_METHODS:
            raise HTTPException(400, "Noto'g'ri to'lov usuli")
        p.method = payload.method
    p.updated_at = datetime.utcnow()
    db.commit()
    if payload.method is not None and p.kind == "payment" \
            and old_method != p.method:
        audit.log(db, user, entity="payment", action="update",
                  entity_id=p.id,
                  entity_label=st.full_name if st else None,
                  field="To'lov usuli",
                  old_value=old_method, new_value=p.method,
                  branch_id=st.branch_id if st else None, commit=True)
    audit.log(db, user, entity="payment", action="amount_edit",
              entity_id=p.id,
              entity_label=st.full_name if st else None,
              field="amount",
              old_value=f"{old:,.0f}".replace(",", " "),
              new_value=f"{p.amount:,.0f}".replace(",", " "),
              branch_id=st.branch_id if st else None, commit=True)
    return {"ok": True, "amount": p.amount}

