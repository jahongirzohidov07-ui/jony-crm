"""Auto-extracted from main.py during refactor (split-main). Domain: finance."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bisect
import json
import re
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
    founder_like,
    has_role,
    is_partner_head,
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
    with_teacher: int = 0,
    branch_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(*roles.EXPENSE_ACCESS)),
):
    """Xarajatlar ro'yxati. year/month berilsa - o'sha oy uchun.

    with_teacher=1 (2026-09-16, Jahongir: "ustozni tanlab oylik
    berganimni kiritsam ... ustoz oyligi kategoriyasi ketishi kerak va
    ustozni ismi korinishi kerak"): ustozlarga berilgan pul
    (TeacherPayment) ham "Ustoz oyligi" qatori bo'lib, ismi bilan
    qo'shiladi. Bunday qatorning id si MANFIY — u xarajat jadvalida
    emas, ustozning oylik kartasida turadi (foyda-zararga ikki marta
    tushmasin)."""
    # Tepada tanlangan filial ham hisobga olinadi (2026-09-16)
    q = scope_to_branch(db.query(models.Expense), models.Expense, user,
                        branch_id)
    start = end = None
    if year and month:
        start, end = billing.month_bounds(year, month)
        q = q.filter(models.Expense.date >= start, models.Expense.date <= end)
    rows = q.order_by(models.Expense.date.desc(), models.Expense.id.desc()).all()
    if not with_teacher:
        return rows

    branches = _payroll_branches(db, user, branch_id)
    bmap = {b.id: b for b in db.query(models.Branch).all()}
    teachers = {t.id: t for t in db.query(models.Teacher).all()}
    kinds = {k: lbl for k, lbl, _h in roles.TEACHER_PAYMENT_KINDS}
    tq = db.query(models.TeacherPayment)
    if start and end:
        tq = tq.filter(models.TeacherPayment.paid_on >= start,
                       models.TeacherPayment.paid_on <= end)
    out = [schemas.ExpenseOut.model_validate(e) for e in rows]
    for p in tq.all():
        t = teachers.get(p.teacher_id)
        if t is None:
            continue
        # Pul qaysi filialdan berilgan bo'lsa — o'sha filialniki.
        # Eski yozuvda filial yo'q — ustozning asosiy filiali.
        bid = p.branch_id or t.branch_id
        if branches is not None and bid not in branches:
            continue
        label = kinds.get(p.kind, "oylik").lower()
        out.append(schemas.ExpenseOut(
            id=-p.id, date=p.paid_on, category="teacher_salary",
            amount=p.amount,
            note=f"{t.full_name} — {label}" + (f" · {p.note}" if p.note else ""),
            branch_id=bid,
            branch=(schemas.BranchOut.model_validate(bmap[bid])
                    if bid in bmap else None),
            channel=None, method=p.method, created_by=p.created_by,
            created_at=p.created_at or datetime.utcnow(),
            teacher_id=t.id))
    out.sort(key=lambda e: e.date, reverse=True)
    return out


def _valid_period(p):
    """"YYYY-MM" bo'lsa qaytaradi, aks holda None."""
    import re as _re
    return p if p and _re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", str(p)) else None


def _linked_teacher(db: Session, user_id) -> models.Teacher | None:
    """Xodim akkaunti ustozga bog'langanmi — bog'langan bo'lsa unga
    beriladigan pul USTOZ oyligi (TeacherPayment), ma'muriy xarajat emas."""
    if not user_id:
        return None
    return (db.query(models.Teacher)
            .filter(models.Teacher.user_id == user_id).first())


def _pay_teacher(db: Session, user, teacher_id: int, *, amount: float,
                 on: date, method: str | None, note: str | None,
                 period: str | None, via: str, branch_id=None):
    """Ustozga berilgan pulni oylik kartasiga yozadi — tanlangan
    filialga (common._pay_branch)."""
    if user.role not in tuple(roles.SALARY_PAY):
        raise HTTPException(403, "Oylik berish huquqi yo'q")
    t = db.query(models.Teacher).get(teacher_id)
    if not t:
        raise HTTPException(404, "Xodim topilmadi")
    _check_pay_scope(db, user, teacher=t)
    tp = models.TeacherPayment(
        teacher_id=t.id, amount=abs(amount), kind="salary",
        period=period or roles.default_pay_period(on),
        paid_on=on, method=method or "cash",
        branch_id=_pay_branch(db, user, t, branch_id),
        note=note, created_by=user.full_name)
    db.add(tp); db.commit(); db.refresh(tp)
    audit.log(db, user, entity="teacher", action="salary_change",
              entity_id=t.id, entity_label=t.full_name,
              branch_id=t.branch_id, field="Oylik",
              new_value=f"{abs(amount):,.0f}".replace(",", " "),
              note=via, commit=True)
    # Javob shakli bir xil bo'lishi uchun "soxta" xarajat qaytaramiz
    return schemas.ExpenseOut(
        id=-tp.id, date=tp.paid_on, category="teacher_salary",
        amount=tp.amount, note=f"{t.full_name} — oylik",
        branch_id=tp.branch_id, branch=None, channel=None,
        method=tp.method, created_by=tp.created_by,
        created_at=tp.created_at or datetime.utcnow(),
        teacher_id=t.id)

@router.get("/api/expenses/staff")
def expense_staff_list(
    branch_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(*roles.EXPENSE_ACCESS)),
):
    """OYLIK berish uchun xodimlar ro'yxati — filial kesimida.

    2026-08-12, Jahongir: "oylikni tanlasa shu filial xodimlari chiqib
    kelsin, hammasi, supportdan tortib examiner yoki ustozgacha".

    Ustozlar (support va examiner ham Teacher yozuvida bo'ladi)
    alohida belgilanadi: ularga berilgan pul TeacherPayment jadvaliga
    tushadi va ustozning oylik kartasida ko'rinadi. Qolgan xodimlar
    (administrator, HR, marketolog...) xarajat sifatida yoziladi va
    xodim kartasida ko'rinadi.
    """
    tq = scope_to_branch(db.query(models.Teacher), models.Teacher, user,
                         branch_id)
    tmap = {t.id: t for t in tq.filter(models.Teacher.is_active == 1).all()}
    uq = scope_to_branch(db.query(models.User), models.User, user, branch_id)
    users = uq.filter(models.User.is_active == 1).all()
    # USTOZ HAR DOIM USTOZ BO'LIB CHIQADI (2026-09-16): asosiy filiali
    # boshqa bo'lsa (qo'shimcha filial) yoki akkaunti shu filialda
    # turgan bo'lsa ham. Aks holda u oddiy xodim bo'lib tanlanib,
    # pul "Ma'muriy xodim oyligi"ga tushib qolardi.
    branches = _payroll_branches(db, user, branch_id)
    if branches is not None:
        extra = [tb.teacher_id for tb in db.query(models.TeacherBranch)
                 .filter(models.TeacherBranch.branch_id.in_(list(branches)))]
        for t in (db.query(models.Teacher)
                  .filter(models.Teacher.id.in_(extra or [-1]),
                          models.Teacher.is_active == 1).all()):
            tmap.setdefault(t.id, t)
    for t in (db.query(models.Teacher)
              .filter(models.Teacher.user_id.in_([u.id for u in users] or [-1]),
                      models.Teacher.is_active == 1).all()):
        tmap.setdefault(t.id, t)
    teachers = list(tmap.values())

    rows = []
    linked = set()
    for t in teachers:
        u = db.query(models.User).get(t.user_id) if t.user_id else None
        if u:
            linked.add(u.id)
        rows.append({
            "key": f"t{t.id}",
            "teacher_id": t.id,
            "user_id": t.user_id,
            "name": t.full_name,
            "role": u.role if u else roles.TEACHER,
            "role_label": roles.UZ_LABELS.get(
                u.role if u else roles.TEACHER, "O'qituvchi"),
            "branch": t.branch.name if t.branch else None,
            "to_salary_card": True,
        })
    for u in users:
        if u.id in linked or u.role in (roles.STUDENT, roles.PARENT):
            continue
        rows.append({
            "key": f"u{u.id}",
            "teacher_id": None,
            "user_id": u.id,
            "name": u.full_name or u.username,
            "role": u.role,
            "role_label": roles.UZ_LABELS.get(u.role, u.role),
            "branch": u.branch.name if u.branch else None,
            "to_salary_card": False,
        })
    rows.sort(key=lambda r: (r["role_label"], r["name"]))
    return {"rows": rows}


@router.get("/api/expenses/salary-due")
def expense_salary_due(
    period: str,
    teacher_id: Optional[int] = None,
    user_id: Optional[int] = None,
    branch_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(*roles.EXPENSE_ACCESS)),
):
    """OYLIK SUMMASI AVTOMAT (2026-10-12, Jahongir: "oylik deb ustozni
    tanlaganda summa avtomat oyligidan kelib chiqib paydo bo'lsin,
    xarajat kirituvchi xohlasa o'chirib boshqa yozadi").

    Shu oy uchun hali BERILMAGAN summa (tanlangan filial kesimida):
    ustoz — yo'qlamadan hisoblangan (oy yopilgan bo'lsa muhrdan)
    minus shu filialdan shu oy uchun berilgani; boshqa xodim — fiks
    oylik minus shu oy uchun berilgani. Faqat taklif — hech narsa
    yozilmaydi."""
    period = _valid_period(period)
    if not period:
        raise HTTPException(400, "Oy noto'g'ri")
    y, m = int(period[:4]), int(period[5:7])
    start, end = billing.month_bounds(y, m)
    if teacher_id:
        t = db.query(models.Teacher).get(teacher_id)
        if not t:
            raise HTTPException(404, "Ustoz topilmadi")
        ctx = billing.PayrollContext(db)
        ctx.prefetch([t.id])
        e = _teacher_earned(db, t.id, since=start, until=end, ctx=ctx)
        sl = _seal_rows(db, period, [t.id]).get(t.id)
        if sl is not None:
            try:
                e = {"amount": float(sl.amount or 0),
                     "attendances": int(sl.attendances or 0),
                     "lessons": int(sl.lessons or 0),
                     "by_group": json.loads(sl.groups_json or "[]")}
            except Exception:
                pass
        worked = {getattr(ctx.groups.get(g.get("group_id")), "branch_id",
                          None) for g in e["by_group"]} - {None}
        branches = _payroll_branches(db, user, branch_id)
        eb = _earned_in_branches(e, ctx.groups, branches)
        paid = _teacher_paid_scoped(
            db, t.id, since=start, until=end, ctx=ctx, period=period,
            branches=branches, part=eb["amount"],
            whole=eb["total_amount"], worked=worked)
        earned = round(eb["amount"], 2)
    elif user_id:
        u = db.query(models.User).get(user_id)
        if not u:
            raise HTTPException(404, "Xodim topilmadi")
        earned = round(float(u.fix_salary or 0), 2)
        ex = (db.query(func.coalesce(func.sum(models.Expense.amount), 0.0))
              .filter(models.Expense.staff_user_id == u.id,
                      models.Expense.period == period).scalar() or 0.0)
        # StaffSalaryPayment jadvali entry.py da e'lon qilinadi — u
        # yuklanmagan muhitda (test) shunchaki 0
        _SSP = getattr(models, "StaffSalaryPayment", None)
        ssp = 0.0
        if _SSP is not None:
            try:
                ssp = (db.query(func.coalesce(func.sum(_SSP.amount), 0.0))
                       .filter(_SSP.user_id == u.id, _SSP.period == period)
                       .scalar() or 0.0)
            except Exception:
                db.rollback()
                ssp = 0.0
        paid = round(float(ex) + float(ssp), 2)
    else:
        raise HTTPException(400, "Xodim tanlanmadi")
    due = max(0.0, round(earned - paid, 2))
    return {"period": period, "earned": earned, "paid": paid,
            "due": float(round(due))}


@router.get("/api/expenses/staff-salaries")
def staff_salaries(
    year: Optional[int] = None,
    month: Optional[int] = None,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(
        *roles.FINANCE_ACCESS, *roles.SALARY_VIEW_ALL)),
):
    """Ma'muriy xodimlarga berilgan oyliklar (xarajat sifatida
    yozilganlari). Ustozlarniki bu yerda emas — ular oylik kartasida.

    Jahongir, 2026-08-12: "nargi tomonlardagi joylarda ham oylik
    berilganligi korinsin".
    """
    today = roles.local_today()
    y, m = year or today.year, month or today.month
    start, end = billing.month_bounds(y, m)
    q = scope_to_branch(db.query(models.Expense), models.Expense, user)
    q = q.filter(models.Expense.staff_user_id.isnot(None),
                 models.Expense.date >= start,
                 models.Expense.date <= end)
    if user_id:
        q = q.filter(models.Expense.staff_user_id == user_id)
    rows = []
    for e in q.order_by(models.Expense.date.desc()).all():
        u = db.query(models.User).get(e.staff_user_id)
        rows.append({
            "id": e.id,
            "date": e.date.isoformat(),
            "user_id": e.staff_user_id,
            "name": (u.full_name or u.username) if u else "—",
            "role_label": roles.UZ_LABELS.get(u.role, u.role) if u else "—",
            "amount": e.amount,
            "method": e.method,
            "method_label": roles.PAYMENT_METHOD_LABELS.get(e.method, e.method),
            "branch": e.branch.name if e.branch else None,
            "note": e.note,
            "created_by": e.created_by,
        })
    return {
        "period": f"{y:04d}-{m:02d}",
        "rows": rows,
        "total": round(sum(r["amount"] for r in rows), 2),
        "count": len(rows),
    }


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

    branch_id = (payload.branch_id if payload.branch_id is not None
                 else user.branch_id)

    # Ustozning AKKAUNTI tanlangan bo'lsa ham — bu ustoz oyligi
    # (2026-09-16).
    if payload.staff_user_id and not payload.teacher_id:
        linked = _linked_teacher(db, payload.staff_user_id)
        if linked:
            payload.teacher_id = linked.id
            payload.staff_user_id = None

    # ---- OYLIK: ustozga berilsa, ustozning oylik kartasiga yoziladi.
    # Xarajatlar jadvaliga QO'SHILMAYDI: P&L da ustozlar oyligi
    # TeacherPayment dan allaqachon hisoblanadi, aks holda ikki marta
    # ketardi.
    if payload.teacher_id:
        return _pay_teacher(db, user, payload.teacher_id,
                            amount=payload.amount, on=payload.date,
                            method=payload.method, note=payload.note,
                            period=payload.period,
                            branch_id=branch_id,
                            via="Moliya > Xarajatlar orqali")

    # ---- KITOB/MARKER va boshqa sanaladigan mahsulot: ombor kirimi
    cons = None
    if payload.consumable_id:
        cons = db.query(models.Consumable).get(payload.consumable_id)
        if not cons:
            raise HTTPException(404, "Mahsulot topilmadi")
    elif (payload.new_item_name or "").strip() and payload.category == "book":
        cons = models.Consumable(
            name=payload.new_item_name.strip(), kind="book",
            branch_id=branch_id, qty=0, min_qty=0, unit="dona")
        db.add(cons); db.commit(); db.refresh(cons)

    staff_name = None
    if payload.staff_user_id:
        su = db.query(models.User).get(payload.staff_user_id)
        if not su:
            raise HTTPException(404, "Xodim topilmadi")
        if user.role not in tuple(roles.SALARY_PAY):
            raise HTTPException(403, "Oylik berish huquqi yo'q")
        _check_pay_scope(db, user, staff_user=su)
        staff_name = su.full_name or su.username

    note = payload.note
    if staff_name:
        note = f"{staff_name} — oylik" + (f" · {note}" if note else "")
    if cons:
        qty_txt = f"{payload.qty:g} ta " if payload.qty else ""
        note = f"{qty_txt}{cons.name}" + (f" · {note}" if note else "")

    exp = models.Expense(
        date=payload.date,
        category=payload.category,
        amount=abs(payload.amount),
        note=note,
        branch_id=branch_id,
        # Kanal faqat reklama xarajatida ma'noga ega - CAC shundan chiqadi.
        channel=payload.channel,
        method=payload.method or "cash",
        staff_user_id=payload.staff_user_id,
        period=(_valid_period(payload.period)
                if payload.staff_user_id else None),
        qty=payload.qty,
        consumable_id=cons.id if cons else None,
        created_by=user.full_name,
    )
    db.add(exp)
    db.commit()
    db.refresh(exp)

    # Ombor: sotib olingan mahsulot QOLDIQQA qo'shiladi — "kitob
    # olindi, lekin omborda ko'rinmadi" degan holat bo'lmasin
    # (Jahongir: "bu yoqda oborda ham korinsin keyin").
    if cons and payload.qty:
        db.add(models.StockMove(
            consumable_id=cons.id, delta=abs(payload.qty), reason="in",
            note=f"Xarajatdan: {exp.note or ''}".strip(),
            created_by=user.full_name))
        cons.qty = (cons.qty or 0) + abs(payload.qty)
        if payload.amount and payload.qty:
            cons.unit_price = round(abs(payload.amount) / abs(payload.qty), 2)
        db.commit()
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
    tid = data.pop("teacher_id", None)
    sid = data.pop("staff_user_id", None)
    period = data.pop("period", None)
    if sid and not tid:
        linked = _linked_teacher(db, sid)
        if linked:
            tid, sid = linked.id, None

    # USTOZ OYLIGIGA KO'CHIRISH (2026-09-16): "Ma'muriy xodim oyligi"
    # bo'lib xato kiritilgan pul tahrirlashda ustoz tanlansa — ustozning
    # oylik kartasiga o'tadi, xarajat jadvalidan chiqadi (ikki marta
    # hisoblanmasin). Eski izoh saqlanadi.
    if tid:
        out = _pay_teacher(
            db, user, tid,
            amount=data.get("amount") or exp.amount,
            on=data.get("date") or exp.date,
            method=data.get("method") or exp.method,
            note=data.get("note", exp.note),
            period=period,
            branch_id=data.get("branch_id") or exp.branch_id,
            via=f"Xarajatdan ko'chirildi (#{exp.id})")
        audit.log(db, user, entity="expense", action="delete",
                  entity_id=exp.id, entity_label=exp.note or exp.category,
                  field=exp.category, old_value=exp.amount,
                  branch_id=exp.branch_id,
                  note="Ustoz oyligiga ko'chirildi")
        db.delete(exp)
        db.commit()
        return out
    if sid:
        if user.role not in tuple(roles.SALARY_PAY):
            raise HTTPException(403, "Oylik berish huquqi yo'q")
        su = db.query(models.User).get(sid)
        if not su:
            raise HTTPException(404, "Xodim topilmadi")
        _check_pay_scope(db, user, staff_user=su)
        data["staff_user_id"] = sid
    if (sid or exp.staff_user_id) and _valid_period(period):
        data["period"] = period

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


# ---------------------------------------------------------------
#  QO'SHIMCHA DAROMAD (2026-10-06)
#  Jahongir: "qo'shimcha daromadlar bo'limini qo'shib ber
#  administratorlar qila oladigan bo'lsin, pul oqimida ko'rinishi
#  kerak u ham". O'quvchi to'lovidan tashqari kirim. Pul oqimida
#  (kassa daftari, kun kassasi, kassa qoldig'i, trend) KIRIM bo'ladi.
# ---------------------------------------------------------------
_OI_LABELS = dict(roles.OTHER_INCOME_CATEGORY_DEFS)


def _oi_out(o: models.OtherIncome) -> dict:
    return {
        "id": o.id,
        "date": o.date.isoformat() if o.date else None,
        "category": o.category,
        "category_label": _OI_LABELS.get(o.category, o.category),
        "amount": o.amount,
        "method": o.method or "cash",
        "method_label": roles.PAYMENT_METHOD_LABELS.get(
            o.method or "cash", o.method),
        "note": o.note,
        "branch_id": o.branch_id,
        "branch": o.branch.name if o.branch else None,
        "created_by": o.created_by,
        "created_at": o.created_at.isoformat() if o.created_at else None,
    }


def _oi_clean(data: dict, *, partial: bool) -> dict:
    """Kiritilgan maydonlarni tekshiradi; faqat ruxsat etilganlarini
    qaytaradi."""
    out: dict = {}
    if "category" in data or not partial:
        cat = data.get("category") or "other"
        if cat not in roles.OTHER_INCOME_CATEGORIES:
            raise HTTPException(400, "Noto'g'ri daromad turi")
        out["category"] = cat
    if "amount" in data or not partial:
        try:
            amt = float(data.get("amount") or 0)
        except (TypeError, ValueError):
            raise HTTPException(400, "Summa noto'g'ri")
        if amt <= 0:
            raise HTTPException(400, "Summa noldan katta bo'lishi kerak")
        out["amount"] = round(amt, 2)
    if "method" in data or not partial:
        m = data.get("method") or "cash"
        if m not in roles.PAYMENT_METHODS:
            raise HTTPException(400, "To'lov usuli noto'g'ri")
        out["method"] = m
    if "date" in data or not partial:
        raw = data.get("date")
        try:
            d = date.fromisoformat(raw) if raw else roles.local_today()
        except (TypeError, ValueError):
            raise HTTPException(400, "Sana noto'g'ri (YYYY-MM-DD)")
        if d > roles.local_today():
            raise HTTPException(400, "Kelajakdagi sana bilan kiritib bo'lmaydi")
        out["date"] = d
    if "note" in data:
        out["note"] = (str(data.get("note") or "").strip() or None)
    return out


def _oi_in_scope(db: Session, oid: int, user) -> models.OtherIncome:
    o = db.query(models.OtherIncome).get(oid)
    if not o or o.archived_at is not None:
        raise HTTPException(404, "Daromad yozuvi topilmadi")
    if not _in_user_branches(db, user, o.branch_id):
        raise HTTPException(403, "Bu yozuv boshqa filialga tegishli")
    return o


@router.get("/api/other-incomes")
def list_other_incomes(
    year: Optional[int] = None,
    month: Optional[int] = None,
    branch_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(*roles.OTHER_INCOME_ACCESS)),
):
    """Bir oylik qo'shimcha daromadlar (arxivdagilar kirmaydi)."""
    today = roles.local_today()
    y, m = year or today.year, month or today.month
    start, end = billing.month_bounds(y, m)
    q = (scope_to_branch(db.query(models.OtherIncome), models.OtherIncome,
                         user, branch_id)
         .filter(models.OtherIncome.archived_at.is_(None),
                 models.OtherIncome.date >= start,
                 models.OtherIncome.date <= end))
    rows = [_oi_out(o) for o in q.order_by(models.OtherIncome.date.desc(),
                                           models.OtherIncome.id.desc()).all()]
    by_cat: dict = {}
    for r in rows:
        by_cat[r["category"]] = by_cat.get(r["category"], 0) + r["amount"]
    return {
        "period": f"{y:04d}-{m:02d}",
        "rows": rows,
        "total": round(sum(r["amount"] for r in rows), 2),
        "by_category": [{"category": k, "label": _OI_LABELS.get(k, k),
                         "amount": round(v, 2)}
                        for k, v in sorted(by_cat.items(),
                                           key=lambda kv: -kv[1])],
        "categories": [{"key": k, "label": lbl}
                       for k, lbl in roles.OTHER_INCOME_CATEGORY_DEFS],
        "can_archive": user.role in tuple(roles.OTHER_INCOME_ARCHIVE),
    }


@router.post("/api/other-incomes")
def create_other_income(
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(*roles.OTHER_INCOME_ACCESS)),
):
    data = _oi_clean(payload or {}, partial=False)
    bid = payload.get("branch_id") if payload else None
    if bid in ("", 0):
        bid = None
    if bid is None:
        bid = user.branch_id
    if bid is not None:
        try:
            bid = int(bid)
        except (TypeError, ValueError):
            raise HTTPException(400, "Filial noto'g'ri")
        if not db.query(models.Branch).get(bid):
            raise HTTPException(404, "Filial topilmadi")
        if not _in_user_branches(db, user, bid):
            raise HTTPException(403, "Bu filialga kiritish huquqi yo'q")
    o = models.OtherIncome(**data, branch_id=bid,
                           created_by=user.full_name or user.username)
    db.add(o)
    db.commit()
    db.refresh(o)
    audit.log(db, user, entity="other_income", action="create",
              entity_id=o.id,
              entity_label=o.note or _OI_LABELS.get(o.category, o.category),
              field=o.category, new_value=o.amount, branch_id=o.branch_id,
              commit=True)
    return _oi_out(o)


@router.put("/api/other-incomes/{oid}")
def update_other_income(
    oid: int,
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(*roles.OTHER_INCOME_ACCESS)),
):
    o = _oi_in_scope(db, oid, user)
    data = _oi_clean(payload or {}, partial=True)
    audit.log_changes(db, user, entity="other_income", obj=o, changes=data,
                      label_attr="note")
    for k, v in data.items():
        setattr(o, k, v)
    db.commit()
    db.refresh(o)
    return _oi_out(o)


@router.delete("/api/other-incomes/{oid}")
def archive_other_income(
    oid: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(*roles.OTHER_INCOME_ARCHIVE)),
):
    """O'chirilmaydi — arxivga o'tadi (hisoblardan chiqadi, bazada
    qoladi)."""
    o = _oi_in_scope(db, oid, user)
    o.archived_at = datetime.utcnow()
    o.archived_by = user.full_name or user.username
    audit.log(db, user, entity="other_income", action="delete",
              entity_id=o.id,
              entity_label=o.note or _OI_LABELS.get(o.category, o.category),
              field=o.category, old_value=o.amount, branch_id=o.branch_id,
              note="Arxivga o'tkazildi")
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
    reason: str = "",
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
        # Hamkor markaz rahbari o'z filialida asoschi kabi (2026-09-17)
        if not founder_like(user):
            raise HTTPException(
                403, "Avtomatik hisoblangan oylikni faqat asoschi "
                     "o'chira oladi")
        if p.kind == "charge":
            db.add(models.ChargeSkip(
                student_id=p.student_id, period=p.period,
                created_by=user.full_name))

    # PUL KIRIMI (to'lov) va refund yozuvini faqat ASOSCHI o'chiradi —
    # kassadagi xato ham asoschi nazorati ostida to'g'rilanadi.
    if p.kind in ("payment", "refund") and not founder_like(user):
        raise HTTPException(
            403, "To'lov (pul kirimi) yozuvini faqat asoschi o'chiradi")
    # Balans tuzatishi (2026-09-26) — uni qo'ygan filial rahbari yoki
    # asoschi o'chiradi; aks holda boshqa xodim o'chirib, balansni
    # jimgina orqaga qaytarib qo'yishi mumkin edi.
    if (p.kind == roles.PAYMENT_ADJUST_KIND and not founder_like(user)
            and user.role not in tuple(roles.MONEY_BALANCE_EDIT)):
        raise HTTPException(
            403, "Balans tuzatishini faqat filial rahbari o'chiradi")

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

    # ARXIVGA KO'CHIRAMIZ, YO'Q QILMAYMIZ (2026-08-15).
    # Jahongir'ning qoidasi: "hech narsa o'chmasin". Yozuv
    # payments'dan olinadi (balans va hisobotlar darrov to'g'rilanadi),
    # lekin payments_deleted jadvalida to'liq saqlanib qoladi - kim
    # o'chirgani, qachon va nima sababdan bilan birga. Asoschi kerak
    # bo'lsa bir bosishda qaytaradi.
    try:
        db.add(models.DeletedPayment(
            payment_id=p.id, public_id=p.public_id,
            student_id=p.student_id,
            student_name=s.full_name if s else None,
            branch_id=s.branch_id if s else None,
            amount=p.amount, kind=p.kind, method=p.method, note=p.note,
            period=p.period, created_by=p.created_by,
            created_at=p.created_at,
            entered_at=getattr(p, "entered_at", None),
            client_key=getattr(p, "client_key", None),
            deleted_by=user.full_name,
            reason=(reason or "").strip()[:400] or None))
    except Exception:
        # Arxiv yozilmasa - O'CHIRMAYMIZ ham. Ma'lumot yo'qolgandan
        # ko'ra amal bajarilmagani yaxshi.
        db.rollback()
        raise HTTPException(
            500, "Arxivga yozib bo'lmadi - yozuv o'chirilmadi. "
                 "Qayta urinib ko'ring.")
    db.delete(p)
    db.commit()
    return {"ok": True, "archived": True}


# =====================================================================
#  TO'LOVNI TUZATISH SO'ROVI (2026-08-15)
#  Jahongir: "sotuv manager tolovni notogri urvordi, shuni ozgartirish
#  qilib sorov yuborsa filial rahbari yoki moliyachiga borsa yoki
#  asoschiga tasdiqlavorsa ozgarsin, chunki shunaqa holat boldi u
#  menga aloqaga chiqadi men uni topaman ozgartiraman vaqt ketadi".
# =====================================================================
def _fix_label(r) -> str:
    k = roles.PAYMENT_FIX_KIND_LABELS.get(r.kind, r.kind)
    if r.kind == "amount":
        return (f"{k}: {abs(r.old_amount or 0):,.0f} -> "
                f"{abs(r.new_amount or 0):,.0f} so'm").replace(",", " ")
    if r.kind == "method":
        return (f"{k}: {roles.PAYMENT_METHOD_LABELS.get(r.old_method or '', '—')}"
                f" -> {roles.PAYMENT_METHOD_LABELS.get(r.new_method or '', '—')}")
    if r.kind == "note":
        return f"{k}: \"{(r.new_note or '')[:60]}\""
    return k


def _notify_fix_approvers(db: Session, r, st) -> None:
    """So'rov jimgina yotib qolmasin — HAR BIR tasdiqlovchiga
    alohida vazifa. Filial rahbariga faqat O'Z filialidagisi."""
    title = f"To'lovni tuzatish so'rovi #{r.id}"
    body = (f"{_fix_label(r)}\n"
            f"O'quvchi: {st.full_name if st else '—'}\n"
            f"Sabab: {r.reason}\n"
            f"So'ragan: {r.requested_by or '—'}\n"
            "Tasdiqlash: Moliya -> \"Tuzatish so'rovlari\" bo'limida.")
    seen = set()
    for role_key in roles.PAYMENT_FIX_APPROVE:
        q = db.query(models.User).filter(models.User.role == role_key,
                                         models.User.is_active == 1)
        if role_key == roles.BRANCH_MANAGER and r.branch_id:
            q = q.filter(models.User.branch_id == r.branch_id)
        for u in q.all():
            if u.id in seen or u.id == r.requested_by_id:
                continue
            seen.add(u.id)
            t = models.Task(
                title=title, description=body, assignee_id=u.id,
                branch_id=r.branch_id,
                deadline=date.today() + timedelta(days=1),
                priority="high", source="manual", created_by="Tizim")
            db.add(t)
            db.flush()
            _ensure_public_id(db, "task", t)
    db.commit()


@router.post("/api/payments/{payment_id}/fix-request")
def request_payment_fix(
    payment_id: int,
    payload: schemas.PaymentFixIn,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.PAYMENT_FIX_REQUEST)),
):
    """Xato kiritilgan to'lovni tuzatish uchun SO'ROV yuborish.

    Tahrirlash huquqi bor xodim (asoschi, moliya direktori, filial
    rahbari) so'rov yubormaydi — u to'g'ridan-to'g'ri tahrirlaydi."""
    p = db.query(models.Payment).get(payment_id)
    if not p:
        raise HTTPException(404, "Yozuv topilmadi")
    st = db.query(models.Student).get(p.student_id)
    if st and not _in_user_branches(db, user, st.branch_id):
        raise HTTPException(403, "Bu o'quvchi boshqa filialga tegishli")
    if payload.kind not in roles.PAYMENT_FIX_KIND_LABELS:
        raise HTTPException(400, "Tuzatish turi noto'g'ri")
    reason = (payload.reason or "").strip()
    if len(reason) < 3:
        raise HTTPException(
            400, "Sababini yozing — tasdiqlovchi shu asosida qaror qiladi")

    open_one = (db.query(models.PaymentFixRequest)
                .filter(models.PaymentFixRequest.payment_id == payment_id,
                        models.PaymentFixRequest.status == "pending")
                .first())
    if open_one:
        raise HTTPException(
            400, "Bu yozuv bo'yicha tasdiq kutayotgan so'rov bor")

    r = models.PaymentFixRequest(
        payment_id=p.id, student_id=p.student_id,
        branch_id=st.branch_id if st else None,
        kind=payload.kind, reason=reason,
        old_amount=p.amount, old_method=p.method,
        requested_by=user.full_name, requested_by_id=user.id)
    if payload.kind == "amount":
        if not payload.amount or payload.amount <= 0:
            raise HTTPException(400, "Yangi summani musbat son bilan yozing")
        sign = -1 if (p.amount or 0) < 0 or p.kind == "charge" else 1
        r.new_amount = sign * abs(round(payload.amount, 0))
    elif payload.kind == "method":
        if payload.method not in roles.PAYMENT_METHODS:
            raise HTTPException(400, "To'lov usuli noto'g'ri")
        if p.kind != "payment":
            raise HTTPException(
                400, "To'lov usuli faqat haqiqiy pul kirimida bo'ladi")
        r.new_method = payload.method
    elif payload.kind == "note":
        if not (payload.note or "").strip():
            raise HTTPException(400, "Yangi izohni yozing")
        r.new_note = payload.note.strip()[:400]

    db.add(r); db.commit(); db.refresh(r)
    _ensure_public_id(db, "payment_fix", r)
    try:
        _notify_fix_approvers(db, r, st)
    except Exception:
        db.rollback()
    audit.log(db, user, entity="payment", action="fix_request",
              entity_id=p.id, entity_label=st.full_name if st else None,
              note=f"{_fix_label(r)} · {reason}",
              branch_id=r.branch_id, commit=True)
    return {"ok": True, "id": r.id,
            "message": ("So'rov yuborildi. Filial rahbari, moliya "
                        "direktori va asoschiga vazifa bo'lib tushdi — "
                        "tasdiqlangach o'zgarish o'zi qo'llanadi.")}


@router.get("/api/payments/fix-requests")
def list_payment_fixes(
    status: str = "pending",
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.PAYMENT_FIX_REQUEST)),
):
    """Tuzatish so'rovlari. Filial rahbari faqat o'z filialini
    ko'radi; so'rov yuborgan xodim o'zinikini ko'radi."""
    q = db.query(models.PaymentFixRequest)
    if status and status != "all":
        q = q.filter(models.PaymentFixRequest.status == status)
    can_approve = user.role in tuple(roles.PAYMENT_FIX_APPROVE)
    if not can_approve:
        q = q.filter(models.PaymentFixRequest.requested_by_id == user.id)
    elif user.role != roles.FOUNDER:
        mine = _user_branch_ids(db, user)
        if mine:
            q = q.filter(or_(
                models.PaymentFixRequest.branch_id.in_(mine),
                models.PaymentFixRequest.branch_id.is_(None)))
    rows = q.order_by(models.PaymentFixRequest.id.desc()).limit(200).all()
    out = []
    for r in rows:
        st = db.query(models.Student).get(r.student_id) \
            if r.student_id else None
        p = db.query(models.Payment).get(r.payment_id)
        out.append({
            "id": r.id, "public_id": r.public_id,
            "payment_id": r.payment_id,
            "payment_exists": p is not None,
            "student_id": r.student_id,
            "student": st.full_name if st else None,
            "branch_id": r.branch_id,
            "kind": r.kind,
            "kind_label": roles.PAYMENT_FIX_KIND_LABELS.get(r.kind, r.kind),
            "what": _fix_label(r),
            "old_amount": r.old_amount, "new_amount": r.new_amount,
            "old_method": r.old_method, "new_method": r.new_method,
            "new_note": r.new_note,
            "reason": r.reason,
            "status": r.status,
            "requested_by": r.requested_by,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "decided_by": r.decided_by,
            "decided_at": r.decided_at.isoformat() if r.decided_at else None,
            "decision_note": r.decision_note,
            "can_approve": can_approve,
        })
    return out


@router.post("/api/payments/fix-requests/{rid}/approve")
def approve_payment_fix(
    rid: int,
    payload: schemas.PaymentFixDecision = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.PAYMENT_FIX_APPROVE)),
):
    """Tasdiqlash — o'zgarish SHU YERDA qo'llanadi. Kim birinchi
    tasdiqlasa, o'sha bajaradi."""
    r = db.query(models.PaymentFixRequest).get(rid)
    if not r:
        raise HTTPException(404, "So'rov topilmadi")
    if r.status != "pending":
        raise HTTPException(400, "Bu so'rov allaqachon ko'rib chiqilgan")
    st = db.query(models.Student).get(r.student_id) if r.student_id else None
    if (user.role == roles.BRANCH_MANAGER
            and not _in_user_branches(db, user, r.branch_id, null_ok=True)):
        raise HTTPException(403, "Bu so'rov boshqa filialga tegishli")
    p = db.query(models.Payment).get(r.payment_id)
    if not p:
        r.status = "rejected"
        r.decided_by = user.full_name
        r.decided_at = datetime.utcnow()
        r.decision_note = "Yozuv topilmadi (o'chirilgan bo'lishi mumkin)"
        db.commit()
        raise HTTPException(400, "To'lov yozuvi topilmadi")

    old_amount, old_method, old_note = p.amount, p.method, p.note
    if r.kind == "amount":
        p.amount = r.new_amount
        p.updated_at = datetime.utcnow()
    elif r.kind == "method":
        p.method = r.new_method
        p.updated_at = datetime.utcnow()
    elif r.kind == "note":
        p.note = r.new_note
        p.updated_at = datetime.utcnow()
    elif r.kind == "delete":
        # O'chirish emas — ARXIVGA ko'chirish (hech narsa yo'qolmaydi)
        db.add(models.DeletedPayment(
            payment_id=p.id, public_id=p.public_id,
            student_id=p.student_id,
            student_name=st.full_name if st else None,
            branch_id=r.branch_id, amount=p.amount, kind=p.kind,
            method=p.method, note=p.note, period=p.period,
            created_by=p.created_by, created_at=p.created_at,
            entered_at=getattr(p, "entered_at", None),
            client_key=getattr(p, "client_key", None),
            deleted_by=f"{user.full_name} (so'rov #{r.id})",
            reason=r.reason))
        if p.period and p.kind == "charge":
            db.add(models.ChargeSkip(
                student_id=p.student_id, period=p.period,
                created_by=user.full_name))
        db.delete(p)

    r.status = "approved"
    r.decided_by = user.full_name
    r.decided_at = datetime.utcnow()
    r.decision_note = (payload.note if payload else None)
    # Barcha tasdiqlovchilardagi vazifalar yopiladi (2026-08-20,
    # Jahongir: "vazifalardan tasdiqlansan vazifa avtomat bajarilgan
    # bo'lsin").
    _close_request_tasks(db, f"To'lovni tuzatish so'rovi #{r.id}",
                         f"Tasdiqlandi ({user.full_name})")
    db.commit()

    audit.log(db, user, entity="payment", action="fix_approve",
              entity_id=r.payment_id,
              entity_label=st.full_name if st else None,
              field=r.kind,
              old_value=(old_amount if r.kind == "amount"
                         else old_method if r.kind == "method"
                         else old_note),
              new_value=(r.new_amount if r.kind == "amount"
                         else r.new_method if r.kind == "method"
                         else r.new_note if r.kind == "note" else "bekor"),
              note=f"So'rov #{r.id}: {r.reason} · so'ragan "
                   f"{r.requested_by}",
              branch_id=r.branch_id, commit=True)
    # So'ragan xodimga xabar
    try:
        if r.requested_by_id:
            t = models.Task(
                title=f"To'lov tuzatildi: {st.full_name if st else ''}",
                description=(f"{_fix_label(r)}\n"
                             f"Tasdiqladi: {user.full_name}"),
                assignee_id=r.requested_by_id, branch_id=r.branch_id,
                deadline=date.today(), priority="normal",
                source="manual", created_by="Tizim")
            db.add(t); db.flush(); _ensure_public_id(db, "task", t)
            db.commit()
    except Exception:
        db.rollback()
    return {"ok": True, "applied": r.kind}


@router.post("/api/payments/fix-requests/{rid}/reject")
def reject_payment_fix(
    rid: int,
    payload: schemas.PaymentFixDecision = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.PAYMENT_FIX_APPROVE)),
):
    r = db.query(models.PaymentFixRequest).get(rid)
    if not r:
        raise HTTPException(404, "So'rov topilmadi")
    if r.status != "pending":
        raise HTTPException(400, "Bu so'rov allaqachon ko'rib chiqilgan")
    r.status = "rejected"
    r.decided_by = user.full_name
    r.decided_at = datetime.utcnow()
    r.decision_note = (payload.note if payload else None)
    _close_request_tasks(db, f"To'lovni tuzatish so'rovi #{r.id}",
                         f"Rad etildi ({user.full_name})")
    db.commit()
    # Auditga (2026-09-18, Jahongir: "hammasi auditda saqlansin") —
    # tasdiqlash kabi rad etish ham iz qoldiradi.
    audit.log(db, user, entity="payment", action="fix_reject",
              entity_id=r.payment_id, entity_label=_fix_label(r),
              field=r.kind, new_value=r.decision_note or "rad etildi",
              commit=True)
    try:
        if r.requested_by_id:
            t = models.Task(
                title=f"To'lov tuzatish so'rovi rad etildi #{r.id}",
                description=(f"{_fix_label(r)}\n"
                             f"Rad etdi: {user.full_name}"
                             + (f"\nIzoh: {r.decision_note}"
                                if r.decision_note else "")),
                assignee_id=r.requested_by_id, branch_id=r.branch_id,
                deadline=date.today(), priority="normal",
                source="manual", created_by="Tizim")
            db.add(t); db.flush(); _ensure_public_id(db, "task", t)
            db.commit()
    except Exception:
        db.rollback()
    return {"ok": True}


@router.get("/api/payments/deleted")
def list_deleted_payments(
    limit: int = 200,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FINANCE_ACCESS)),
):
    """O'chirilgan to'lovlar arxivi. Filial rahbari faqat o'z
    filialidagilarni ko'radi."""
    q = db.query(models.DeletedPayment)
    if user.role != roles.FOUNDER:
        mine = _user_branch_ids(db, user)
        if mine:
            q = q.filter(models.DeletedPayment.branch_id.in_(mine))
    rows = q.order_by(models.DeletedPayment.id.desc()).limit(
        min(max(limit, 1), 1000)).all()
    return [{
        "id": r.id, "payment_id": r.payment_id,
        "public_id": r.public_id,
        "student_id": r.student_id, "student_name": r.student_name,
        "amount": r.amount, "kind": r.kind, "method": r.method,
        "note": r.note, "period": r.period,
        "created_by": r.created_by,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "deleted_by": r.deleted_by,
        "deleted_at": r.deleted_at.isoformat() if r.deleted_at else None,
        "reason": r.reason,
        "restored_at": (r.restored_at.isoformat()
                        if r.restored_at else None),
        "restored_by": r.restored_by,
    } for r in rows]


@router.post("/api/payments/deleted/{row_id}/restore")
def restore_deleted_payment(
    row_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(roles.FOUNDER, roles.PARTNER_HEAD)),
):
    """Xato o'chirilgan yozuvni qaytarish. Faqat asoschi (va o'z
    filialida hamkor markaz rahbari, 2026-09-17).

    Bir marta qaytarilgan yozuv ikkinchi marta qaytarilmaydi -
    aks holda bitta to'lov ikki nusxa bo'lib qolardi."""
    r = db.query(models.DeletedPayment).get(row_id)
    if not r:
        raise HTTPException(404, "Arxivda bunday yozuv yo'q")
    if (user.role != roles.FOUNDER
            and r.branch_id not in _user_branch_ids(db, user)):
        raise HTTPException(403, "Bu yozuv boshqa filialga tegishli")
    if r.restored_at:
        raise HTTPException(400, "Bu yozuv allaqachon qaytarilgan")
    if r.student_id and db.query(models.Payment).filter(
            models.Payment.id == r.payment_id).first():
        raise HTTPException(400, "Bu raqamli yozuv allaqachon mavjud")

    p = models.Payment(
        student_id=r.student_id, amount=r.amount, kind=r.kind,
        method=r.method, note=r.note, period=r.period,
        created_by=r.created_by, created_at=r.created_at)
    try:
        p.entered_at = r.entered_at
    except Exception:
        pass
    db.add(p)
    db.flush()
    # Avtomatik oylik o'chirilganda "qayta hisoblanmasin" belgisi
    # qo'yilgan edi - qaytarilganda uni olib tashlaymiz.
    if r.period:
        try:
            db.query(models.ChargeSkip).filter(
                models.ChargeSkip.student_id == r.student_id,
                models.ChargeSkip.period == r.period).delete(
                    synchronize_session=False)
        except Exception:
            pass
    r.restored_at = datetime.utcnow()
    r.restored_by = user.full_name
    db.commit()
    audit.log(db, user, entity="payment", action="restore",
              entity_id=p.id, entity_label=r.student_name,
              field=r.kind, old_value=None, new_value=r.amount,
              note=f"Arxivdan qaytarildi (avval #{r.payment_id})",
              branch_id=r.branch_id, commit=True)
    return {"ok": True, "payment_id": p.id}

@router.get("/api/payouts", response_model=List[schemas.TeacherPayoutOut])
def list_payouts(
    year: int,
    month: int,
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(*roles.FINANCE_ACCESS)),
):
    """Ustoz oyliklari GURUH kesimida yozilgan, guruh esa filialga
    tegishli - shu bois ikki filialda ishlaydigan ustozning oyligi
    har filialda ALOHIDA ko'rinadi (Jahongir, 2026-08-12). Filial
    tanlansa faqat shu filial guruhlari bo'yicha hisoblangan qismi
    chiqadi."""
    period = f"{year:04d}-{month:02d}"
    q = db.query(models.TeacherPayout).filter(models.TeacherPayout.period == period)
    if user.role not in tuple(roles.ORG_WIDE_ROLES):
        if user.branch_id:
            q = q.join(models.Group).filter(
                _branch_in(db, user, models.Group.branch_id))
    elif branch_id:
        q = q.join(models.Group).filter(
            models.Group.branch_id == branch_id)
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
    # filial chegarasi (2026-09-17): hamkor markaz rahbari faqat o'z
    # filiali o'quvchisiga refund so'raydi
    s = _get_student_in_scope(db, payload.student_id, user)
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
        created_by=user.full_name, entered_at=datetime.utcnow())
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
        # Asoschiga 100% gacha ruxsat (2026-08-12), qolganlarga 50%
        "max_percent": (roles.DISCOUNT_ABSOLUTE_CAP
                        if founder_like(user)
                        else roles.MAX_TOTAL_DISCOUNT_PERCENT),
        "can_approve": user.role in roles.DISCOUNT_APPROVE,
        "pending": sum(1 for d in rows if d.status == "pending"),
    }

@router.get("/api/discounts/overview")
def discounts_overview(
    branch_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.DISCOUNT_REQUEST)),
):
    """CHEGIRMALAR BO'LIMI (2026-09-17, Jahongir: "chegirmalar degan
    bo'limni ham qo'shish kerak ... chegirmadagilar korinishi kerak").

    Hamma chegirmalar bitta ro'yxatda: o'quvchi, guruh, filial, turi,
    miqdori, OYIGA taxminan qancha kamaytirishi, kim so'ragan/tasdiqlagan.
    Filial kesimi o'quvchi orqali. So'rovlar partiyalab (N+1 yo'q)."""
    _expire_discounts(db)
    studs = {s.id: s for s in scope_to_branch(
        db.query(models.Student), models.Student, user, branch_id).all()}
    rows = []
    if studs:
        rows = (db.query(models.Discount)
                .filter(models.Discount.student_id.in_(list(studs)))
                .order_by(models.Discount.created_at.desc()).all())
    gids = {s.group_id for s in studs.values() if s.group_id}
    groups = ({g.id: g for g in db.query(models.Group)
               .filter(models.Group.id.in_(gids))} if gids else {})
    branches = {b.id: b.name for b in db.query(models.Branch).all()}
    refs = {d.referrer_student_id for d in rows if d.referrer_student_id}
    ref_names = ({s.id: s.full_name for s in db.query(models.Student)
                  .filter(models.Student.id.in_(refs))} if refs else {})
    today = roles.local_today()

    def _fee(s, g):
        if not g:
            return 0
        std = g.standard_lessons_per_month or 0
        if s.locked_lesson_price and std:
            return int(s.locked_lesson_price * std)
        return int(g.monthly_fee or (g.lesson_price or 0) * std or 0)

    out = []
    for d in rows:
        s = studs.get(d.student_id)
        g = groups.get(s.group_id) if s and s.group_id else None
        fee = _fee(s, g)
        monthly = (int(d.amount or 0)
                   or int(round(fee * (d.percent or 0) / 100)))
        alive = _discount_alive(d, today)
        out.append({
            "id": d.id,
            "student_id": d.student_id,
            "student_name": s.full_name if s else "—",
            "student_status": s.status if s else None,
            "phone": s.phone if s else None,
            "group_id": g.id if g else None,
            "group": g.name if g else None,
            "branch": branches.get(s.branch_id) if s else None,
            "kind": d.kind,
            "kind_label": roles.DISCOUNT_TYPE_LABELS.get(d.kind, d.kind),
            "percent": d.percent,
            "amount": d.amount,
            "fee": fee,
            "monthly": monthly,
            "reason": d.reason,
            "referrer_name": ref_names.get(d.referrer_student_id),
            "start_date": d.start_date.isoformat() if d.start_date else None,
            "end_date": d.end_date.isoformat() if d.end_date else None,
            "status": d.status,
            "status_label": roles.DISCOUNT_STATUS_LABELS.get(d.status,
                                                             d.status),
            "alive": alive,
            "requested_by": d.requested_by,
            "approved_by": d.approved_by,
            "approved_at": (d.approved_at.isoformat()
                            if d.approved_at else None),
            "cancelled_reason": d.cancelled_reason,
            "created_at": d.created_at.isoformat() if d.created_at else None,
        })
    live = [r for r in out if r["alive"]]
    by_kind = {}
    for r in live:
        k = by_kind.setdefault(r["kind"], {"kind": r["kind"],
                                           "label": r["kind_label"],
                                           "count": 0, "monthly": 0})
        k["count"] += 1
        k["monthly"] += r["monthly"]
    return {
        "rows": out,
        "summary": {
            "students": len({r["student_id"] for r in live}),
            "active": len(live),
            "monthly": sum(r["monthly"] for r in live),
            "pending": sum(1 for r in out if r["status"] == "pending"),
            "by_kind": sorted(by_kind.values(), key=lambda x: -x["monthly"]),
        },
        "types": [{"key": k, "label": lbl}
                  for k, lbl, _h in roles.DISCOUNT_TYPES],
        "statuses": [{"key": k, "label": lbl}
                     for k, lbl in roles.DISCOUNT_STATUSES],
        "can_approve": user.role in roles.DISCOUNT_APPROVE,
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

    # Jami chegirma chegaradan oshmasin.
    #
    # 2026-08-12, Jahongir: "individual ruxsat skidkasida xodim
    # xohlagan foizini yozib sorov jonatishi mumkin va tasdiqlangandan
    # keyingina ishlayveradi". Ya'ni SO'RASH erkin - chegara TASDIQDA
    # ishlaydi. Shuning uchun:
    #   - tasdiqlash huquqi bor odam o'zi yozsa (darrov amalda
    #     bo'ladi) - asoschiga 100%, qolganlariga 50%;
    #   - oddiy xodim SO'ROV yuborsa - 100% gacha yozaveradi, chunki
    #     u baribir tasdiqsiz ishlamaydi.
    can_approve_now = user.role in tuple(roles.DISCOUNT_APPROVE)
    if not can_approve_now:
        cap = roles.DISCOUNT_ABSOLUTE_CAP
    else:
        cap = (roles.DISCOUNT_ABSOLUTE_CAP
               if user.role == roles.FOUNDER
               or (is_partner_head(user)
                   and _in_user_branches(db, user, st.branch_id))
               else roles.MAX_TOTAL_DISCOUNT_PERCENT)
    now = _student_discount_percent(db, st)
    add = payload.percent or 0
    if not add and payload.amount and st.group and st.group.monthly_fee:
        add = payload.amount / st.group.monthly_fee * 100
    if now + add > cap:
        raise HTTPException(
            400,
            f"Jami chegirma {cap:.0f}% dan oshmasligi "
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
        hidden=1 if payload.hidden else 0,
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
    # 2026-08-12, Jahongir: "Chegirma sorovi jonatsa administrator
    # kimlarga vazifa bolib tushadi tasdiqlash, filial rahbari,
    # moliyachiga tushsin". Ilgari so'rov hech kimga bildirilmasdi -
    # administrator yuborardi, javob kelishini kutib o'tirardi.
    if d.status == "pending":
        _notify_discount_approvers(db, d, st)
    # DARHOL AMALDAGI CHEGIRMA — SHU OY HISOBI HAM TO'G'RILANADI
    # (2026-09-25, Jahongir: "10% chegirma yechib olmayabdi").
    # Tasdiqlash huquqi bor odam (asoschi, filial rahbari, moliya
    # direktori) chegirmani O'ZI yozsa, u darrov "active" bo'ladi,
    # lekin oy boshida yechilgan to'liq summa o'z holicha qolardi:
    # tuzatish faqat "Tasdiqlash" tugmasida bor edi. Endi ikkala
    # yo'lda ham bir xil.
    if d.status == "active":
        try:
            _recharge_current_month(db, st)
        except Exception:
            db.rollback()
    audit.log(db, user, entity="discount", action="create", entity_id=d.id,
              entity_label=st.full_name, branch_id=st.branch_id,
              new_value=f"{roles.DISCOUNT_TYPE_LABELS[d.kind]} "
                        f"{d.percent or d.amount}")
    db.commit()
    return _discount_out(db, d)

def _recharge_current_month(db: Session, st: models.Student, *, commit: bool = True) -> bool:
    """Shu oyning AVTOMAT hisob qatorini chegirma bilan qayta yozadi.

    Qator o'chirilmaydi — summa joyida to'g'rilanadi (tizimdagi umumiy
    qoida), eski summa auditda qoladi. Faqat kamaytiradi: chegirma
    berilgani uchun o'quvchidan ortiqcha yechilgani qaytariladi."""
    try:
        import entry as _E
    except Exception:
        return False
    today = roles.local_today()
    period = f"{today.year:04d}-{today.month:02d}"
    g = st.group
    if g is None:
        return False
    rows = (db.query(models.Payment)
            .filter(models.Payment.student_id == st.id,
                    models.Payment.period == period,
                    models.Payment.kind == "charge").all())
    std = int(g.standard_lessons_per_month or 12) or 12
    want = _E._mc_expected(db, st, g, std)
    full = roles.money(_E._billing.student_lesson_price(st, g) * std)
    # Avtomat oylik qator — avvalgidek. Qo'shimcha (2026-09-19,
    # Stretinko: "10% skidka ..."): FAOLLASHTIRISHDA yoki qo'lda yozilgan
    # TO'LIQ standart oy (summa aynan to'liq narx) ham to'g'rilanadi —
    # chegirma faollashtirilgandan KEYIN tasdiqlansa, u hisob chegirmasiz
    # qolib ketardi. Qisman oy yoki boshqa summaga tegilmaydi.
    mc = getattr(_E, "_MC_BY", "")
    p = next((r for r in rows if r.created_by == mc), None)
    if p is None and len(rows) == 1             and abs(abs(rows[0].amount) - full) <= 0.5:
        p = rows[0]
    target = want
    # QISMAN OY (2026-09-25, Jahongir: "10% chegirma yechib
    # olmayabdi"). Oy o'rtasida faollashgan o'quvchining hisobi to'liq
    # oy emas — "faollashgandan 6 dars". Bunday qatorga ilgari UMUMAN
    # tegilmasdi va chegirma o'sha oyda butunlay yo'qolardi.
    #
    # Ikki marta chegirma qo'llamaslik uchun: faqat summa AYNAN
    # (darslar soni x narx) bo'lgan qatorni tuzatamiz. Chegirma
    # allaqachon qo'llangan qator bu hisobga to'g'ri kelmaydi,
    # shuning uchun unga tegilmaydi.
    if p is None and len(rows) == 1:
        r0 = rows[0]
        disc = _student_discount_percent(db, st)
        price = _E._billing.student_lesson_price(st, g)
        since = today.replace(day=1)
        if st.enrolled_date and st.enrolled_date > since:
            since = st.enrolled_date
        try:
            n = min(len(_lessons_left_in_month(db, g.id, since)), std)
        except Exception:
            n = 0
        expect = roles.money(price * n)
        # Bir marta to'g'rilangan qatorda CHEGIRMASIZ asl summa
        # izohda qoladi ("[asos:240000]"). Shunda keyin yana chegirma
        # qo'shilsa, hisob har safar asl summadan qayta olinadi —
        # chegirma ustiga chegirma tushmaydi.
        base = None
        m = re.search(r"\[asos:(\d+)\]", r0.note or "")
        if m:
            base = float(m.group(1))
        elif n > 0 and abs(abs(r0.amount) - expect) <= 0.5:
            base = expect
        if disc > 0 and base:
            p = r0
            target = roles.money(base * (100.0 - disc) / 100.0)
            if not m:
                p.note = (p.note or "") + f" [asos:{int(base)}]"
    if p is None:
        return False
    if target >= abs(p.amount) - 0.5:
        return False
    old_amt = p.amount
    p.amount = -target
    p.note = ((p.note or "") + f" · chegirma qo'llandi: "
              f"{int(abs(old_amt)):,} -> {int(target):,}").replace(",", " ")
    p.updated_at = datetime.utcnow()
    audit.log(db, None, entity="payment", action="update", entity_id=p.id,
              entity_label=st.full_name, field="amount",
              old_value=old_amt, new_value=-target,
              note="Chegirma tasdiqlandi — shu oy hisobi qayta yozildi",
              branch_id=st.branch_id)
    if commit:
        db.commit()
    return True


# =====================================================================
#  ESKI "+PUL" CHEGIRMA QATORLARINI HISOBGA KO'CHIRISH (2026-09-30)
#  Jahongir (Abdullayeva Umida #688): "coinga almashganlarda nimaga
#  hisobida pul bn ko'rinyabdi ... pul ortiqcha ekan qaytaring deyishi
#  mumkin ... oy boshida 480 000 hisoblansa shuni o'zgartirib qo'yadigan
#  bo'lsin".
#
#  Har bir eski "Jony Shop (coin)" / "Do'st taklifi (avtomat)" qatori:
#   * hisob chegirmani ALLAQACHON qo'llagan bo'lsa (IKKI MARTA chegirma) —
#     qator arxivga ko'chadi, balans ortiqcha summaga kamayadi;
#   * qo'llamagan bo'lsa — o'sha oy hisobi shu summaga kamaytiriladi va
#     qator arxivga ko'chadi, balans O'ZGARMAYDI.
#  Hech narsa yo'q qilinmaydi: qator payments_deleted'da to'liq qoladi.
# =====================================================================
_SHOP_ROW_BY = ("Jony Shop (coin)", "Do'st taklifi (avtomat)")
_DISC_AWARE_FROM = datetime(2026, 9, 6)   # avtomat hisob chegirmani qo'llay boshlagan


def _shop_rows_plan(db: Session, apply: bool = False, by: str = "Tizim"):
    rows = (db.query(models.Payment)
            .filter(models.Payment.kind == "discount",
                    models.Payment.created_by.in_(_SHOP_ROW_BY))
            .order_by(models.Payment.id).all())
    out = []
    for r in rows:
        s = db.query(models.Student).get(r.student_id)
        kind = ("app_referral" if (r.created_by or "").startswith("Do'st")
                else "coin_shop")
        D = abs(float(r.amount or 0))
        ch = _pick_period_charge(db, r.student_id, r.period) if r.period \
            else None
        item = {"payment_id": r.id, "student_id": r.student_id,
                "name": s.full_name if s else None, "period": r.period,
                "amount": D, "kind": kind,
                "balance_before": student_balance(db, r.student_id)}
        if ch is None or s is None:
            item["case"] = "hisob_yoq"          # tegilmaydi
            out.append(item)
            continue
        d = (db.query(models.Discount)
             .filter(models.Discount.student_id == r.student_id,
                     models.Discount.kind == kind,
                     models.Discount.period == r.period)
             .order_by(models.Discount.id).first())
        d_at = (d.approved_at or d.created_at) if d else None
        note = ch.note or ""
        inc = False
        if d_at is not None:
            if ch.created_at and ch.created_at >= max(d_at, _DISC_AWARE_FROM):
                inc = True       # hisob chegirmadan keyin, chegirmali yozilgan
            elif ("chegirma qo'llandi" in note and ch.updated_at
                  and ch.updated_at >= d_at):
                inc = True       # keyin chegirma bilan qayta yozilgan
        item["charge_id"] = ch.id
        item["charge_before"] = abs(float(ch.amount or 0))
        item["case"] = "ikki_marta" if inc else "hisobga_kochdi"
        new_charge = item["charge_before"] if inc \
            else roles.money(max(0.0, item["charge_before"] - D))
        item["charge_after"] = new_charge
        item["balance_after"] = roles.money(
            item["balance_before"] - (D if inc else 0))
        if apply:
            what = ("Do'st taklifi chegirmasi" if kind == "app_referral"
                    else "Jony Shop chegirmasi")
            if not inc:
                old = ch.amount
                if "[asos:" not in note:
                    note += f" [asos:{int(item['charge_before'])}]"
                ch.amount = -new_charge
                ch.note = (note + f" · {what}: {int(item['charge_before']):,}"
                           f" -> {int(new_charge):,}").replace(",", " ")
                ch.updated_at = datetime.utcnow()
                audit.log(db, None, entity="payment", action="update",
                          entity_id=ch.id, entity_label=s.full_name,
                          field="amount", old_value=old,
                          new_value=ch.amount,
                          note=f"{what} alohida qatordan hisobning o'ziga "
                               f"ko'chirildi (#{r.id})",
                          branch_id=s.branch_id)
            elif what not in note:
                ch.note = note + f" · {what} hisobda"
            db.add(models.DeletedPayment(
                payment_id=r.id, public_id=r.public_id,
                student_id=r.student_id, student_name=s.full_name,
                branch_id=s.branch_id, amount=r.amount, kind=r.kind,
                method=r.method, note=r.note, period=r.period,
                created_by=r.created_by, created_at=r.created_at,
                entered_at=getattr(r, "entered_at", None),
                client_key=getattr(r, "client_key", None),
                deleted_by=by,
                reason=("Chegirma endi hisobning o'zida ko'rinadi"
                        if not inc else
                        "IKKI MARTA chegirma: hisob chegirmani allaqachon "
                        "qo'llagan edi")))
            db.delete(r)
            db.commit()
            item["balance_after_real"] = student_balance(
                db, item["student_id"])
        out.append(item)
    return out


@router.get("/api/admin/shop-discount-rows")
def shop_discount_rows_plan(db: Session = Depends(get_db),
                            user=Depends(get_current_user)):
    """Faqat ko'rish: nima o'zgarishini ko'rsatadi (asoschi)."""
    if not founder_like(user):
        raise HTTPException(403, "Faqat asoschi")
    return {"rows": _shop_rows_plan(db, apply=False)}


@router.post("/api/admin/shop-discount-rows")
def shop_discount_rows_apply(db: Session = Depends(get_db),
                             user=Depends(get_current_user)):
    if not founder_like(user):
        raise HTTPException(403, "Faqat asoschi")
    res = _shop_rows_plan(db, apply=True, by=user.full_name)
    audit.log(db, user, entity="payment", action="update",
              entity_label="Do'kon chegirmalari hisobga ko'chirildi",
              new_value=len(res),
              note="; ".join(f"{x['name']} {x['period']} {x['case']}"
                             for x in res[:40]), commit=True)
    return {"rows": res}


# =====================================================================
#  "KAM DARS — FARQ QAYTARILDI" QATORLARI (2026-10-02)
#
#  Jahongir: "ba'zi o'quvchilarda 1-oktabrda qanaqadur chegirma bilan
#  pul qo'shilib qolyabdi ... qayerdan bunaqa chegirmalar paydo bo'lib
#  qolyabdi shuni bilish kerak" va "bu qanaqa chegirma va nega
#  berilganligiga bog'liq".
#
#  Manba — avtomat oylik "farq qaytarish" (entry._mc_refund_prev, endi
#  o'chirilgan): oy oxirida o'tilgan darslar standartdan (12) kam
#  sanalsa farq "+summa" chegirma bo'lib yozilardi. Bu yerda HAR BIR
#  qator uchun nega kam sanalgani ko'rsatiladi; asoschi tanlab bekor
#  qiladi (qator payments_deleted'ga ko'chadi, audit yoziladi).
# =====================================================================
_LR_BY = "avtomat (oylik)"
_LR_MARK = "farq qaytarildi"
_LR_RE = __import__("re").compile(r"^(.*?) — (\d{4}-\d{2}): (\d+) dars o'tildi")


def _lr_group_name(note: str) -> str:
    """Hisob izohidagi guruh nomi ("Guruh — 2026-09: ..." yoki eski
    "Guruh - 2026-09 oyi uchun ...")."""
    for sep in (" — ", " - "):
        if sep in (note or ""):
            return note.split(sep, 1)[0].strip()
    return ""


def _lesson_refund_rows(db: Session, user) -> list:
    q = (db.query(models.Payment)
         .filter(models.Payment.kind == "discount",
                 models.Payment.created_by == _LR_BY,
                 models.Payment.note.like("%" + _LR_MARK + "%"))
         .order_by(models.Payment.created_at.desc(), models.Payment.id))
    out = []
    for p in q.all():
        s = db.query(models.Student).get(p.student_id)
        if s is None or not _in_user_branches(db, user, s.branch_id):
            continue
        m = _LR_RE.match(p.note or "")
        rgroup = m.group(1).strip() if m else _lr_group_name(p.note)
        period = p.period or (m.group(2) if m else None)
        counted = int(m.group(3)) if m else None
        charges = (db.query(models.Payment)
                   .filter(models.Payment.student_id == s.id,
                           models.Payment.kind == "charge",
                           models.Payment.period == period).all()
                   if period else [])
        cgroups = sorted({_lr_group_name(c.note) for c in charges} - {""})
        reasons = []
        g = s.group
        std = int((g.standard_lessons_per_month if g else None) or 12) or 12
        if cgroups and rgroup and rgroup.lower() not in \
                {x.lower() for x in cgroups}:
            reasons.append(
                f"Oylik «{', '.join(cgroups)}» guruhi uchun yechilgan, "
                f"qaytarish esa «{rgroup}» guruhi darslari bo'yicha "
                f"sanalgan (o'quvchi guruh almashgan)")
        if period and g is not None:
            y_, mo_ = int(period[:4]), int(period[5:7])
            start, end = billing.month_bounds(y_, mo_)
            ls = (db.query(models.Lesson)
                  .filter(models.Lesson.group_id == g.id,
                          models.Lesson.date >= start,
                          models.Lesson.date <= end,
                          or_(models.Lesson.cancelled.is_(None),
                              models.Lesson.cancelled == 0)).all())
            held = sum(1 for x in ls if x.held)
            unmarked = len(ls) - held
            if unmarked > 0:
                reasons.append(
                    f"«{g.name}» guruhida {unmarked} ta darsga yo'qlama "
                    f"qo'yilmagan — ular \"o'tilmagan\" sanalgan")
            if len(ls) < std:
                reasons.append(
                    f"«{g.name}» guruhida oyda {len(ls)} ta dars "
                    f"rejalashtirilgan (standart {std})")
            if s.enrolled_date and start < s.enrolled_date <= end:
                reasons.append(
                    f"O'quvchi {s.enrolled_date.isoformat()} da qo'shilgan "
                    f"— undan oldingi darslar sanalmagan")
            cut = billing.attendance_cutoff(db, [s.id], g.id).get(s.id)
            if cut is not None and cut < end:
                reasons.append(
                    f"Oxirgi kelgan darsi {cut.isoformat()} — undan "
                    f"keyingi darslar sanalmagan")
        if not reasons:
            reasons.append("Aniq sabab topilmadi — qo'lda ko'rish kerak")
        out.append({
            "payment_id": p.id, "student_id": s.id, "name": s.full_name,
            "branch": s.branch.name if s.branch else None,
            "status": s.status, "period": period,
            "amount": abs(float(p.amount or 0)),
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "refund_group": rgroup, "charged_groups": cgroups,
            "counted_lessons": counted, "standard": std,
            "charged": round(sum(abs(float(c.amount or 0))
                                 for c in charges), 2),
            "balance": student_balance(db, s.id),
            "reasons": reasons, "note": p.note,
        })
    return out


@router.get("/api/admin/lesson-refunds")
def lesson_refund_rows(db: Session = Depends(get_db),
                       user=Depends(get_current_user)):
    """Ko'rish: "kam dars — farq qaytarildi" qatorlari va sabablari."""
    if not founder_like(user):
        raise HTTPException(403, "Faqat asoschi")
    rows = _lesson_refund_rows(db, user)
    return {"rows": rows, "count": len(rows),
            "total": round(sum(r["amount"] for r in rows), 2)}


@router.post("/api/admin/lesson-refunds/cancel")
def lesson_refund_cancel(payload: dict, db: Session = Depends(get_db),
                         user=Depends(get_current_user)):
    """Tanlangan qatorlarni bekor qilish: payments_deleted'ga ko'chadi
    (asoschi bir bosishda qaytara oladi), audit yoziladi. Faqat shu turdagi
    avtomat qatorlarga ishlaydi."""
    if not founder_like(user):
        raise HTTPException(403, "Faqat asoschi")
    ids = [int(x) for x in (payload or {}).get("ids") or []]
    done = _lesson_refund_cancel(db, ids, user)
    return {"cancelled": done, "count": len(done)}


def _lesson_refund_cancel(db: Session, ids, user=None) -> list:
    """Qatorlarni arxivga ko'chiradi. user=None — tizimning bir martalik
    qadami (entry._mc_ensure, 2026-10-02, Jahongir: "kam dars qaytarilgan
    farq bo'lsa bu chegirmalarni olib tashla")."""
    reason = ("Kam dars uchun avtomat qaytarish bekor qilindi — qoida: "
              "oyda dars soni qancha bo'lsa ham to'liq oylik")
    by = user.full_name if user is not None else "Tizim (Jahongir ko'rsatmasi)"
    done = []
    for pid in ids:
        p = db.query(models.Payment).get(pid)
        if (p is None or p.kind != "discount" or p.created_by != _LR_BY
                or _LR_MARK not in (p.note or "")):
            continue
        s = db.query(models.Student).get(p.student_id)
        if s is None or (user is not None
                         and not _in_user_branches(db, user, s.branch_id)):
            continue
        db.add(models.DeletedPayment(
            payment_id=p.id, public_id=p.public_id,
            student_id=p.student_id, student_name=s.full_name,
            branch_id=s.branch_id, amount=p.amount, kind=p.kind,
            method=p.method, note=p.note, period=p.period,
            created_by=p.created_by, created_at=p.created_at,
            entered_at=getattr(p, "entered_at", None),
            client_key=getattr(p, "client_key", None),
            deleted_by=by, reason=reason))
        audit.log(db, user, entity="payment", action="payment_cancel",
                  entity_id=p.id, entity_label=s.full_name, field=p.kind,
                  old_value=p.amount, new_value=None, note=reason,
                  branch_id=s.branch_id)
        db.delete(p)
        done.append({"payment_id": pid, "name": s.full_name,
                     "amount": abs(float(p.amount or 0))})
    db.commit()
    return done


def _lesson_refund_cancel_all(db: Session) -> list:
    """Hamma "kam dars — farq qaytarildi" qatorlari (bir martalik)."""
    ids = [pid for (pid,) in db.query(models.Payment.id)
           .filter(models.Payment.kind == "discount",
                   models.Payment.created_by == _LR_BY,
                   models.Payment.note.like("%" + _LR_MARK + "%")).all()]
    return _lesson_refund_cancel(db, ids, None) if ids else []


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
    # Chegara aynan SHU YERDA ishlaydi: 50% dan oshiq chegirmani
    # faqat asoschi tasdiqlay oladi (so'rash hammaga ochiq).
    if payload.approve and st:
        add = d.percent or 0
        if not add and d.amount and st.group and st.group.monthly_fee:
            add = d.amount / st.group.monthly_fee * 100
        now = _student_discount_percent(db, st)
        _own = (is_partner_head(user)
                and _in_user_branches(db, user, st.branch_id))
        if (now + add > roles.MAX_TOTAL_DISCOUNT_PERCENT
                and user.role != roles.FOUNDER and not _own):
            raise HTTPException(
                400,
                f"Jami chegirma {roles.MAX_TOTAL_DISCOUNT_PERCENT:.0f}% "
                f"dan oshadi ({now:.0f}% + {add:.0f}%) — bunday "
                f"chegirmani faqat asoschi tasdiqlaydi.")
        if now + add > roles.DISCOUNT_ABSOLUTE_CAP:
            raise HTTPException(
                400, f"Jami chegirma {roles.DISCOUNT_ABSOLUTE_CAP:.0f}% "
                     f"dan oshib ketadi")
    d.status = "active" if payload.approve else "rejected"
    d.approved_by = user.full_name
    d.approved_at = datetime.utcnow()
    if not payload.approve:
        d.cancelled_reason = payload.reason
    # Hamma tasdiqlovchidagi "Chegirma so'rovi #N" vazifalari yopiladi
    # (2026-08-20). Ilgari faqat bosgan odamniki yopilardi - qolganlar
    # ro'yxatida ochiq turib qolardi.
    _close_request_tasks(db, f"Chegirma so'rovi #{d.id}",
                         ("Tasdiqlandi" if payload.approve else "Rad etildi")
                         + f" ({user.full_name})")
    db.commit()
    # Oila so'rovi tasdiqlansa - o'quvchilar shu yerda BOG'LANADI.
    # Chegirma foizini keyin tizim o'zi hisoblaydi (aka-uka ketsa
    # o'zi yo'qoladi), shuning uchun qo'lda foiz yozilmaydi.
    if payload.approve and d.kind == "family" and d.referrer_student_id:
        sib = db.query(models.Student).get(d.referrer_student_id)
        if st and sib:
            _do_family_link(db, st, sib, user.username)
    # CHEGIRMA TASDIQLANSA — SHU OY HISOBI DARROV TO'G'RILANADI
    # (2026-09-06). Ilgari tasdiq faqat statusni o'zgartirardi: oy
    # boshida yechilgan to'liq summa o'z holicha qolib, o'quvchi
    # chegirmaga ega bo'lsa ham qarzdor bo'lib turaverardi.
    if payload.approve and st:
        try:
            _recharge_current_month(db, st)
        except Exception:
            db.rollback()
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
        amount = lessons * billing.student_lesson_price(s, g) \
            * (100 - disc) / 100

        if commit and not already and amount > 0 \
                and not _charge_skipped(db, s.id, period):
            db.add(models.Payment(
                student_id=s.id, amount=-abs(amount), kind="charge",
                note=f"{g.name} — {period} oyi uchun {lessons} dars"
                     + (f" (chegirma {disc}%)" if disc else ""),
                created_by=user.full_name, period=period,
                entered_at=datetime.utcnow()))
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
    branch_id: int | None = None,
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

    # 2026-08-27, Jahongir: "har bir filial rejasi va barchasini
    # korsatish kerak". Avval marketolog FAQAT o'z filialini
    # ko'rardi va tepadagi tanlagich ishlamasdi.
    hide = set(hidden_branch_ids(db, user) if branch_id else aggregate_skip_ids(db, user))
    q = db.query(models.Branch).order_by(models.Branch.name)
    if branch_id:
        q = q.filter(models.Branch.id == branch_id)
    rows = []
    for b in q.all():
        if b.id in hide:
            continue
        st = _smm_sales_state(db, b.id, y, m)
        rows.append({"branch_id": b.id, "branch": b.name, **st})

    # JAMI qatori — "barchasini ko'rsatish". Foiz yig'indidan qayta
    # hisoblanadi (filiallar foizining o'rtachasi emas): reja katta
    # filialda bajarilmasa, umumiy foiz ham pasayishi kerak.
    total = None
    if len(rows) > 1:
        plan = sum(float(r.get("plan") or 0) for r in rows)
        fact = sum(float(r.get("fact") or 0) for r in rows)
        total = {
            "branch": "JAMI", "plan": plan, "fact": fact,
            "percent": round(fact / plan * 100, 1) if plan else None,
            "new_payments_count": sum(int(r.get("new_payments_count") or 0)
                                      for r in rows),
            "students_now": sum(int(r.get("students_now") or 0)
                                for r in rows),
        }
    return {"year": y, "month": m, "rows": rows, "total": total,
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

@router.put("/api/teacher-payments/{payment_id}/branch")
def set_teacher_payment_branch(
    payment_id: int,
    payload: schemas.TeacherPaymentBranchIn,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.SALARY_FIX)),
):
    """Ustozga berilgan pulning FILIALINI to'g'rilash (2026-09-16) —
    ilgari asosiy filialga yozilib qolgan yozuvlar uchun."""
    p = db.query(models.TeacherPayment).get(payment_id)
    if not p:
        raise HTTPException(404, "Topilmadi")
    t = db.query(models.Teacher).get(p.teacher_id)
    if t is not None:
        _check_pay_scope(db, user, teacher=t)
    if not db.query(models.Branch).get(payload.branch_id):
        raise HTTPException(404, "Filial topilmadi")
    if (user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id
            and payload.branch_id not in _user_branch_ids(db, user)):
        raise HTTPException(403, "Bu filial sizga tegishli emas")
    old = p.branch_id or (t.branch_id if t else None)
    p.branch_id = payload.branch_id
    db.commit()
    audit.log(db, user, entity="teacher", action="update",
              entity_id=p.teacher_id,
              entity_label=t.full_name if t else "—",
              field="Ustoz to'lovi filiali", old_value=old,
              new_value=payload.branch_id, commit=True)
    return {"ok": True, "branch_id": p.branch_id}


@router.put("/api/teacher-payments/{payment_id}")
def edit_teacher_payment(
    payment_id: int,
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.SALARY_FIX)),
):
    """USTOZ OYLIGI YOZUVINI TAHRIRLASH (2026-10-12, Jahongir: "shu
    rayxonani to'g'rilayman desam xato ketib qolibdi").

    Kassa daftaridagi qalamcha ustoz oyligi qatori uchun ham ishlaydi:
    summa, to'lov usuli va izoh o'zgaradi. Yozuv o'chirilmaydi — eski
    qiymatlar Auditda qoladi."""
    p = db.query(models.TeacherPayment).get(payment_id)
    if not p:
        raise HTTPException(404, "Topilmadi")
    t = db.query(models.Teacher).get(p.teacher_id)
    if t is not None:
        _check_pay_scope(db, user, teacher=t)
    label = t.full_name if t else "—"
    changed = []
    if "amount" in payload and payload["amount"] is not None:
        try:
            amt = round(float(payload["amount"]), 2)
        except (TypeError, ValueError):
            raise HTTPException(400, "Summa noto'g'ri")
        if amt <= 0:
            raise HTTPException(400, "Summani musbat son bilan kiriting")
        if amt != round(float(p.amount or 0), 2):
            changed.append(("Ustoz to'lovi summasi",
                            f"{p.amount:,.0f}".replace(",", " "),
                            f"{amt:,.0f}".replace(",", " ")))
            p.amount = amt
    if payload.get("method"):
        m = str(payload["method"])
        if m != (p.method or "") and m not in roles.PAYMENT_METHOD_LABELS:
            raise HTTPException(400, "Noto'g'ri to'lov usuli")
        if m != (p.method or ""):
            changed.append(("Ustoz to'lovi usuli", p.method, m))
            p.method = m
    if "note" in payload:
        n = (payload.get("note") or None)
        if n != p.note:
            changed.append(("Ustoz to'lovi izohi", p.note, n))
            p.note = n
    db.commit()
    for field, old, new in changed:
        audit.log(db, user, entity="teacher", action="salary_change",
                  entity_id=p.teacher_id, entity_label=label,
                  branch_id=p.branch_id or (t.branch_id if t else None),
                  field=field, old_value=old, new_value=new)
    db.commit()
    return {"ok": True, "id": p.id, "amount": p.amount,
            "method": p.method, "note": p.note}


@router.delete("/api/teacher-payments/{payment_id}")
def delete_teacher_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.SALARY_FIX)),
):
    p = db.query(models.TeacherPayment).get(payment_id)
    if not p:
        raise HTTPException(404, "Topilmadi")
    t = db.query(models.Teacher).get(p.teacher_id)
    if t is not None:
        _check_pay_scope(db, user, teacher=t)
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

def _debt_by_period(db: Session, student_ids) -> dict:
    """Qarzdor qarzi QAYSI OYLARDAN qolgan (2026-10-03, Jahongir: "oylar
    kesimida tanlash — o'tgan oy, undan oldingi oyda qolib ketgan
    qarzdorlarni ko'rish").

    {student_id: {"2026-09": 540000, ...}}. Balans bilan AYNAN mos:
    har manfiy yozuv (yechilgan oylik, qaytarilgan pul) o'z oyiga qarz;
    oyi ko'rsatilgan chegirma avval o'sha oyni yopadi; qolgan barcha
    musbat pul (to'lovlar) eng eski ochiq oydan boshlab yopadi (FIFO —
    "Pul oqimi → Oy kesimida" bilan bir xil qoida). Qoldiqlar yig'indisi
    = |balans|."""
    ids = list(student_ids)
    out: dict = {}
    if not ids:
        return out
    off = timedelta(hours=roles.TIMEZONE_OFFSET_HOURS)

    def per(p):
        if p.period:
            return p.period
        dt = p.created_at
        if dt is None:
            return ""
        if isinstance(dt, datetime):
            dt = dt + off
        return dt.strftime("%Y-%m")

    for i in range(0, len(ids), 900):
        rows = (db.query(models.Payment)
                .filter(models.Payment.student_id.in_(ids[i:i + 900]))
                .order_by(models.Payment.student_id, models.Payment.id).all())
        by: dict = {}
        for p in rows:
            by.setdefault(p.student_id, []).append(p)
        for sid, ps in by.items():
            owed: dict = {}
            pool = 0.0
            disc = []
            for p in ps:
                amt = float(p.amount or 0)
                if amt < 0:
                    P = per(p)
                    owed[P] = owed.get(P, 0.0) - amt
                elif amt > 0:
                    if p.kind == "discount" and p.period:
                        disc.append((p.period, amt))
                    else:
                        pool += amt
            for P, amt in disc:
                take = min(amt, owed.get(P, 0.0))
                if take > 0:
                    owed[P] -= take
                pool += amt - take
            for P in sorted(owed):
                if pool <= 0.005:
                    break
                take = min(pool, owed[P])
                owed[P] -= take
                pool -= take
            res = {P: round(v, 2) for P, v in owed.items() if v > 0.5}
            if res:
                out[sid] = res
    return out


@router.get("/api/debtors")
def list_debtors(
    branch_id: int | None = None,
    period: str | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.DEBTOR_ACCESS)),
):
    """Qarzdorlar ro'yxati. Eng shoshilinchi tepada: va'dasi o'tib
    ketganlar, keyin eski qarzlar."""
    today = date.today()
    q = scope_to_branch(db.query(models.Student), models.Student, user, branch_id)
    # "left" — guruhdan chiqarilgan, lekin qarzi bor: undirish
    # davom etadi (2026-08-15).
    students = q.filter(
        models.Student.status.in_(roles.STUDENT_OPEN_STATUSES)).all()

    # Oxirgi bog'lanish yozuvlari
    contacts: dict[int, models.DebtorContact] = {}
    for c in (db.query(models.DebtorContact)
              .order_by(models.DebtorContact.contacted_on).all()):
        contacts[c.student_id] = c

    # Tezlik: balanslar bitta so'rovda (avval har o'quvchiga alohida)
    _bal = _balances_bulk(db, [s.id for s in students])
    _debtor_ids = [s.id for s in students if _bal.get(s.id, 0) < 0]
    # Aging: balans qachondan beri minusda (2026-08-12, Jahongir:
    # "0-15 / 16-30 / 31-60 / 60+ kun bo'yicha")
    _neg = _neg_since_bulk(db, _debtor_ids)
    # Oxirgi hisoblash sanalari ham bitta so'rovda
    _lc = {}
    if _debtor_ids:
        for i in range(0, len(_debtor_ids), 900):
            for sid, mx in (db.query(models.Payment.student_id,
                                     func.max(models.Payment.created_at))
                            .filter(models.Payment.student_id.in_(
                                        _debtor_ids[i:i + 900]),
                                    models.Payment.kind == "charge")
                            .group_by(models.Payment.student_id).all()):
                if mx is not None:
                    _lc[sid] = mx.date() if hasattr(mx, "date") else mx

    _bp = _debt_by_period(db, _debtor_ids)
    if period and not re.fullmatch(r"\d{4}-\d{2}", period):
        period = None

    rows = []
    for s in students:
        bal = _bal.get(s.id, 0.0)
        if bal >= 0:
            continue
        debt = abs(bal)
        months = _bp.get(s.id) or {}
        if period and period not in months:
            continue
        since = _lc.get(s.id) or s.enrolled_date or today
        days = (today - since).days
        key, label, tone = roles.debt_urgency(days)
        _ns = _neg.get(s.id)
        aging_days = (today - _ns).days if _ns else days
        bucket = _aging_bucket(aging_days)

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
            "aging_days": aging_days,
            "bucket": bucket,
            "urgency": key,
            "urgency_label": label,
            "urgency_tone": tone,
            "last_contact": c.contacted_on.isoformat() if c else None,
            "last_by": c.created_by if c else None,
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
            # Qarz qaysi oylardan (eski oy birinchi)
            "months": [{"period": P, "amount": a}
                       for P, a in sorted(months.items())],
            "period_debt": months.get(period) if period else None,
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

    # Oy tanlagich uchun: har oyda nechta qarzdor, qancha (filial kesimida,
    # oy filtridan oldin)
    _mon: dict = {}
    for s in students:
        if _bal.get(s.id, 0.0) >= 0:
            continue
        for P, a in (_bp.get(s.id) or {}).items():
            m = _mon.setdefault(P, {"period": P, "count": 0, "sum": 0.0})
            m["count"] += 1
            m["sum"] += a

    return {
        "rows": rows,
        "period": period,
        "months": [{"period": m["period"], "count": m["count"],
                    "sum": round(m["sum"], 0)}
                   for m in sorted(_mon.values(), key=lambda m: m["period"],
                                   reverse=True)],
        # Oy tanlansa — faqat o'sha oydan qolgan qarz yig'iladi
        "period_debt": (round(sum(r["period_debt"] or 0 for r in rows), 2)
                        if period else None),
        "total_debt": round(sum(r["debt"] for r in rows), 2),
        "count": len(rows),
        "broken_promises": sum(1 for r in rows if r["promise_broken"]),
        "due_today": sum(1 for r in rows
                         if r["promised_date"] == today.isoformat()),
        "never_contacted": sum(1 for r in rows if not r["last_contact"]),
        "results": [{"key": k, "label": lbl, "tone": t}
                    for k, lbl, t in roles.DEBT_CONTACT_RESULTS],
        # Qarz eskirish (aging) xulosasi - 4 chelak
        "aging": [{
            "key": k, "label": lbl,
            "count": sum(1 for r in rows if r["bucket"] == k),
            "sum": round(sum(r["debt"] for r in rows
                             if r["bucket"] == k), 0),
        } for k, lbl, _lim in DEBT_AGING_BUCKETS],
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

def _avg_check(db: Session, year: int, month: int,
               branch_id: int | None = None):
    """Oyning O'RTACHA CHEKI: tushum / TO'LAGAN O'QUVCHILAR soni.

    Jahongir (2026-08-12): "bir o'quvchi 2 marta bo'lib to'laganligi
    hisobga bitta qilib olinsin" - shuning uchun to'lovlar soni emas,
    DISTINCT o'quvchilar soni olinadi."""
    start, end = billing.month_bounds(year, month)
    d0, d1 = _utc_window(start, end)
    q = (db.query(models.Payment.student_id, models.Payment.amount)
         .join(models.Student,
               models.Payment.student_id == models.Student.id)
         .filter(models.Payment.kind == "payment",
                 models.Payment.amount > 0,
                 models.Payment.created_at >= d0,
                 models.Payment.created_at <= d1))
    if branch_id:
        q = q.filter(models.Student.branch_id == branch_id)
    rows = q.all()
    revenue = round(sum(a for _s, a in rows), 0)
    payers = len({s for s, _a in rows})
    return {"revenue": revenue, "payers": payers,
            "avg_check": round(revenue / payers, 0) if payers else None}


def _avg_check_recent(db: Session, branch_id: int | None = None,
                      months: int = 3):
    """Oxirgi N TO'LIQ oyning umumiy o'rtacha cheki - reja hisoblari
    uchun barqaror asos (joriy chala oy olinmaydi)."""
    today = roles.local_today()
    y, m = today.year, today.month
    tot_rev, tot_payers = 0.0, 0
    for _ in range(months):
        m -= 1
        if m == 0:
            y, m = y - 1, 12
        st = _avg_check(db, y, m, branch_id)
        tot_rev += st["revenue"]
        tot_payers += st["payers"]
    return round(tot_rev / tot_payers, 0) if tot_payers else None


@router.get("/api/reports/avg-check")
def report_avg_check(months: int = 12, branch_id: int | None = None,
                     db: Session = Depends(get_db),
                     user=Depends(require_role(*roles.FINANCE_ACCESS))):
    """O'rtacha chek statistikasi - oylar kesimida (Jahongir,
    2026-08-12). Filial tanlansa shu filial bo'yicha."""
    if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
        branch_id = user.branch_id
    months = max(1, min(24, months))
    today = roles.local_today()
    y, m = today.year, today.month
    out = []
    for _ in range(months):
        st = _avg_check(db, y, m, branch_id)
        out.append({"year": y, "month": m,
                    "label": f"{roles.UZ_MONTHS[m - 1]} {y}", **st})
        m -= 1
        if m == 0:
            y, m = y - 1, 12
    out.reverse()
    return {"rows": out,
            "recent_avg": _avg_check_recent(db, branch_id),
            "hint": ("O'rtacha chek = oy tushumi / to'lagan o'quvchilar "
                     "soni. Bo'lib-bo'lib to'lagan o'quvchi BITTA "
                     "hisoblanadi.")}


def _work_days(start: date, end: date) -> int:
    """[start, end) oralig'idagi ish kunlari (yakshanba dam)."""
    n, d = 0, start
    while d < end:
        if d.weekday() != 6:
            n += 1
        d += timedelta(days=1)
    return n

def _plan_fakt(db: Session, metric: str, start: date, end: date,
               branch_id: int | None = None):
    """Ko'rsatkich fakti [start, end) oralig'ida — tirik ma'lumotdan.

    branch_id berilsa faqat shu filial bo'yicha (2026-08-11, Jahongir:
    "har bir filial uchun alohida reja va fakt"). None = butun markaz."""
    if metric == "leads":
        d0, d1 = _utc_window(start, end)
        q = db.query(models.Lead).filter(
            models.Lead.created_at >= d0,
            models.Lead.created_at < d1)
        if branch_id:
            q = q.filter(models.Lead.branch_id == branch_id)
        return q.count()
    if metric == "visits":
        d0, d1 = _utc_window(start, end)
        q = db.query(models.Lead).filter(
            models.Lead.created_at >= d0, models.Lead.created_at < d1,
            models.Lead.stage.in_(("trial_attended", "converted")))
        if branch_id:
            q = q.filter(models.Lead.branch_id == branch_id)
        return q.count()
    if metric in ("new_payments", "old_payments"):
        d0, d1 = _utc_window(start, end)
        pq = (db.query(models.Payment)
              .join(models.Student,
                    models.Payment.student_id == models.Student.id)
              .filter(models.Payment.kind == "payment",
                      models.Payment.amount > 0,
                      models.Payment.created_at >= d0,
                      models.Payment.created_at < d1))
        if branch_id:
            pq = pq.filter(models.Student.branch_id == branch_id)
        pays = pq.all()
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
            q = db.query(models.Student).filter(
                models.Student.status == "active")
            if branch_id:
                q = q.filter(models.Student.branch_id == branch_id)
            return q.count()
        m0 = date(start.year, start.month, 1)
        m1 = date(m0.year + 1, 1, 1) if m0.month == 12 else \
            date(m0.year, m0.month + 1, 1)
        q = (db.query(models.Attendance.student_id)
             .join(models.Lesson,
                   models.Lesson.id == models.Attendance.lesson_id)
             .filter(models.Lesson.date >= m0, models.Lesson.date < m1))
        if branch_id:
            q = (q.join(models.Group,
                        models.Group.id == models.Lesson.group_id)
                 .filter(models.Group.branch_id == branch_id))
        return q.distinct().count()
    if metric == "revenue":
        d0, d1 = _utc_window(start, end)
        q = (db.query(func.coalesce(func.sum(models.Payment.amount), 0))
             .filter(models.Payment.kind == "payment",
                     models.Payment.amount > 0,
                     models.Payment.created_at >= d0,
                     models.Payment.created_at < d1))
        if branch_id:
            q = (q.join(models.Student,
                        models.Payment.student_id == models.Student.id)
                 .filter(models.Student.branch_id == branch_id))
        return round(q.scalar() or 0, 0)
    if metric == "expenses":
        q = db.query(func.coalesce(
            func.sum(models.Expense.amount), 0)).filter(
            models.Expense.date >= start,
            models.Expense.date < end)
        if branch_id:
            q = q.filter(models.Expense.branch_id == branch_id)
        return round(q.scalar() or 0, 0)
    if metric == "profit":
        rev = _plan_fakt(db, "revenue", start, end, branch_id)
        exp = _plan_fakt(db, "expenses", start, end, branch_id)
        return round((rev or 0) - (exp or 0), 0)
    return None

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
             branch_id: int | None = None,
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
            if founder_like(user)
            else roles.plan_sections_for(user.role))
    wins = _plan_windows(year, granularity, month)
    # FILIAL KESIMI (2026-08-11, Jahongir): har filialga alohida reja.
    # FULL_ACCESS (asoschi, filial rahbari) filial tanlaydi yoki
    # UMUMIY yig'indini ko'radi; qolgan xodimlarga o'z filiali.
    # 2026-08-27, Jahongir: "reja va fakt ham filialga qarab
    # o'zgarishi kerak, har bir filial rejasi va barchasini
    # korsatish kerak."
    #
    # Avval FULL_ACCESS bo'lmagan HAMMA xodimga branch_id majburan
    # o'z filialiga almashtirilardi. Marketolog butun tashkilotni
    # ko'radigan rol bo'lsa ham, tepadagi tanlagich unga umuman
    # ta'sir qilmasdi — "Zafar" tanlansa ham "Maktab" raqami
    # chiqaverardi.
    full_access = user.role in tuple(roles.FULL_ACCESS)
    org_wide = user.role in tuple(roles.ORG_WIDE_ROLES)
    if not (full_access or org_wide) or is_partner_head(user):
        # Hamkor markaz rahbari faqat O'Z markazi rejasini ko'radi
        branch_id = user.branch_id or None
    elif branch_id and branch_id in blocked_branch_ids(db, user):
        # Hamkor markazni ko'rish huquqi yo'q — o'z ko'rinishiga
        # qaytariladi.
        branch_id = user.branch_id or None
    tq = db.query(models.PlanTarget).filter(
        models.PlanTarget.year == year)
    if branch_id:
        tq = tq.filter(models.PlanTarget.branch_id == branch_id)
    targets = tq.all()
    plan_map = {}
    for t in targets:
        d = plan_map.setdefault(t.metric, {})
        # Umumiy rejimda barcha filiallar rejasi YIG'ILADI
        d[t.month] = (d.get(t.month) or 0) + (t.value or 0)

    # AVTOMAT REJALAR (Jahongir, 2026-08-12):
    # 1) TUSHUM rejasi = o'rtacha chek x (yangi + eski to'lovlar
    #    rejasi). O'rtacha chek - oxirgi 3 to'liq oy, to'lagan
    #    o'quvchi bitta hisoblanadi.
    avg_check = _avg_check_recent(db, branch_id)
    _newp = plan_map.get("new_payments", {})
    _oldp = plan_map.get("old_payments", {})
    if avg_check and (_newp or _oldp):
        rev = {}
        for _m in roles.PLAN_MONTHS:
            if _newp.get(_m) is None and _oldp.get(_m) is None:
                continue
            rev[_m] = round(avg_check * ((_newp.get(_m) or 0)
                                         + (_oldp.get(_m) or 0)), 0)
        if rev:
            plan_map["revenue"] = rev
    # 2) XARAJAT rejasi = shu oy BUDJETdagi xarajatlar yig'indisi
    bq = (db.query(models.BudgetLine.month,
                   func.coalesce(func.sum(models.BudgetLine.amount), 0))
          .filter(models.BudgetLine.year == year,
                  models.BudgetLine.kind == "expense"))
    if branch_id:
        bq = bq.filter(models.BudgetLine.branch_id == branch_id)
    _bexp = {m_: v_ for m_, v_ in bq.group_by(models.BudgetLine.month)
             .all() if v_}
    if _bexp:
        plan_map["expenses"] = {m_: round(v_, 0)
                                for m_, v_ in _bexp.items()}
    # 3) FOYDA rejasi = tushum rejasi - xarajat rejasi
    _revp = plan_map.get("revenue", {})
    _expp = plan_map.get("expenses", {})
    if _revp and _expp:
        prof = {}
        for _m in roles.PLAN_MONTHS:
            if _revp.get(_m) is None or _expp.get(_m) is None:
                continue
            prof[_m] = round(_revp[_m] - _expp[_m], 0)
        if prof:
            plan_map["profit"] = prof
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
                    days=1)) if granularity == "day" else e,
                    branch_id)
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
        "can_edit": has_role(user, roles.PLAN_EDIT)
        and branch_id is not None,
        "branch_id": branch_id,
        "avg_check": avg_check,
        "auto_plans": ["revenue", "expenses", "profit"],
        # Filial tanlagichi: butun tashkilotni ko'radigan rollarga
        # ham chiqadi (avval faqat FULL_ACCESS ko'rardi). Yashirin
        # filiallar (hamkor markaz, test) ro'yxatga tushmaydi.
        "branches": ([{"id": b.id, "name": b.name}
                      for b in db.query(models.Branch)
                      .order_by(models.Branch.name).all()
                      if b.id not in set(hidden_branch_ids(db, user))]
                     if (full_access or org_wide)
                     and not is_partner_head(user) else []),
        "is_total": branch_id is None,
        "plan_raw": plan_map,
        "hint": ("Reja yil boshida oy kesimida tuziladi; hafta va kun "
                 "rejasi oydan avtomat taqsimlanadi (yakshanba dam). "
                 "Fakt platformadan o'zi to'ladi."),
    }

@router.get("/api/plan/suggest")
def plan_suggest(year: int, growth: int = roles.PLAN_DEFAULT_GROWTH,
                 branch_id: int | None = None,
                 db: Session = Depends(get_db),
                 user=Depends(require_role(*roles.PLAN_EDIT))):
    """O'tgan yil fakti + o'sish foizi — yangi reja uchun taklif."""
    if is_partner_head(user):
        branch_id = user.branch_id
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
            f = _plan_fakt(db, key, s, e, branch_id)
            if f:
                vals[m] = round(f * (1 + growth / 100),
                                -3 if kind == "money" else 0)
        out[key] = vals
    return {"year": year, "growth": growth, "suggest": out}

@router.put("/api/plan/{year}")
def save_plan(year: int, payload: schemas.PlanSaveIn,
              branch_id: int | None = None,
              db: Session = Depends(get_db),
              user=Depends(require_role(*roles.PLAN_EDIT))):
    """Yillik rejani saqlash (bor oylar ustidan yoziladi).

    2026-08-11 (Jahongir): reja FILIALGA kiritiladi - umumiy jadval
    faqat yig'indi ko'rinish, unga yozib bo'lmaydi."""
    if not branch_id:
        raise HTTPException(
            400, "Avval filialni tanlang - reja har filialga alohida "
                 "kiritiladi")
    if not db.query(models.Branch).get(branch_id):
        raise HTTPException(404, "Filial topilmadi")
    if (user.role != roles.FOUNDER
            and not _in_user_branches(db, user, branch_id)):
        raise HTTPException(403, "Faqat o'z filialingiz rejasini "
                                 "kirita olasiz")
    n = 0
    for it in payload.items:
        # revenue/expenses/profit endi AVTOMAT hisoblanadi - qo'lda
        # kiritilgani jimgina o'tkaziladi (2026-08-12)
        if it.metric in ("revenue", "expenses", "profit"):
            continue
        if it.metric not in roles.PLAN_METRIC_KEYS or not (
                1 <= it.month <= 12):
            raise HTTPException(400, f"Noto'g'ri ko'rsatkich: {it.metric}")
        row = db.query(models.PlanTarget).filter_by(
            year=year, metric=it.metric, month=it.month,
            branch_id=branch_id).first()
        if row:
            row.value = it.value
        else:
            db.add(models.PlanTarget(year=year, metric=it.metric,
                                     month=it.month, value=it.value,
                                     branch_id=branch_id,
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

def _own_branch_ids(db: Session, user):
    """Filialga bog'langan (ORG_WIDE bo'lmagan) xodim uchun uning
    filiallari; butun tashkilotni ko'radiganlarga None (2026-09-17)."""
    if user.role in tuple(roles.ORG_WIDE_ROLES) or not user.branch_id:
        return None
    return _user_branch_ids(db, user) or [-1]


def _pay_scoped(q, own):
    """Payment so'rovini o'quvchi filiali bo'yicha cheklaydi."""
    if own is None:
        return q
    q = q.join(models.Student,
               models.Student.id == models.Payment.student_id)
    return q.filter(models.Student.branch_id.in_(own))


def _fin_month(db: Session, user, y: int, m: int) -> dict:
    """Bir oyning asosiy moliyaviy raqamlari (overview uchun)."""
    own = _own_branch_ids(db, user)
    start, end = billing.month_bounds(y, m)
    period = f"{y:04d}-{m:02d}"
    methods = _income_by_method(db, user, start, end, None)
    collected = round(sum(methods.values()), 0)
    d0, d1 = _utc_window(start, end)
    disc = abs(_pay_scoped(db.query(func.coalesce(
                   func.sum(models.Payment.amount), 0)), own)
               .filter(models.Payment.kind == "discount",
                       models.Payment.created_at >= d0,
                       models.Payment.created_at < d1).scalar() or 0)
    refunds = abs(_pay_scoped(db.query(func.coalesce(
                      func.sum(models.Payment.amount), 0)), own)
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
    charges = abs(_pay_scoped(db.query(func.coalesce(
                      func.sum(models.Payment.amount), 0)), own)
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
                                               roles.FINANCE_DIRECTOR,
                                               roles.PARTNER_HEAD))):
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
    own = _own_branch_ids(db, user)
    _pq = db.query(models.PlanTarget).filter(
        models.PlanTarget.year == plan_year,
        models.PlanTarget.month == m)
    if own is not None:
        _pq = _pq.filter(models.PlanTarget.branch_id.in_(own))
    plans = {}
    for t in _pq.all():
        if own is None:
            plans[t.metric] = t.value
        else:
            plans[t.metric] = (plans.get(t.metric) or 0) + (t.value or 0)
    p_rev, p_exp, p_prof = (plans.get("revenue"), plans.get("expenses"),
                            plans.get("profit"))

    # Qarzdorlik: balansi manfiy o'quvchilar
    bal = (_pay_scoped(db.query(models.Payment.student_id,
                                func.sum(models.Payment.amount)), own)
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

# Budjetda alohida qator bo'lmaydigan rollar: ustozlar (oyligi
# yoqlamadan avtomat), o'quvchi/ota-ona, asoschi ("CEO oyligi"
# alohida kategoriya).
_BUDGET_STAFF_SKIP = {roles.STUDENT, roles.PARENT, roles.FOUNDER,
                      roles.TEACHER}


def _budget_staff(db: Session, user, branch_id=None) -> list:
    """Budjetga bittalab kiritiladigan xodimlar — ustoz bo'lmaganlar
    (administrator, HR, marketolog, buxgalter ...)."""
    uq = scope_to_branch(db.query(models.User), models.User, user, branch_id)
    users = uq.filter(models.User.is_active == 1).all()
    tlinked = {uid for (uid,) in db.query(models.Teacher.user_id).filter(
        models.Teacher.user_id.isnot(None),
        models.Teacher.is_active == 1).all()}
    out = []
    for u in users:
        if u.role in _BUDGET_STAFF_SKIP or u.id in tlinked:
            continue
        out.append({
            "user_id": u.id,
            "category": f"{roles.BUDGET_STAFF_PREFIX}{u.id}",
            "name": u.full_name or u.username,
            "role_label": roles.UZ_LABELS.get(u.role, u.role),
            "branch": u.branch.name if u.branch else None,
            "branch_id": u.branch_id,
            "fix_salary": round(getattr(u, "fix_salary", 0) or 0),
        })
    out.sort(key=lambda r: (r["role_label"], r["name"]))
    return out


def _budget_staff_of_branch(db: Session, staff: list, bid: int) -> list:
    """Tanlangan filial xodimlari. Filialsiz xodim (HR va h.k.) oyligini
    qaysi filialdan olsa, o'sha filialda chiqadi (2026-10-02, Jahongir:
    "HR bilan Marhabo Mamatqulova yo'q ko'rinmay qoldi, bular Zafar
    filialdan oylik olishadi"). Hali hech qayerdan oylik olmagan
    filialsiz xodim yo'qolib qolmasligi uchun har filialda ko'rinadi."""
    ids = [x["user_id"] for x in staff]
    extra = {uid for (uid,) in db.query(models.UserBranch.user_id).filter(
        models.UserBranch.branch_id == bid,
        models.UserBranch.user_id.in_(ids or [-1])).all()}
    paid = {}
    for uid, b in db.query(models.Expense.staff_user_id,
                           models.Expense.branch_id).filter(
            models.Expense.staff_user_id.in_(ids or [-1]),
            models.Expense.branch_id.isnot(None)).distinct().all():
        paid.setdefault(uid, set()).add(b)
    return [x for x in staff
            if x["branch_id"] == bid or x["user_id"] in extra
            or bid in paid.get(x["user_id"], ())
            or (x["branch_id"] is None and not paid.get(x["user_id"]))]


def _budget_split_staff(db: Session, user, start, end, branch_id,
                        by_cat: dict, staff: list) -> dict:
    """Xodimga bog'langan oylik xarajatlarini fakt'da shu xodimning
    "staff:<id>" qatoriga, asoschinikini "CEO oyligi"ga o'tkazadi.
    Jami summa o'zgarmaydi — faqat qaysi qatorga tushishi."""
    ids = {x["user_id"] for x in staff}
    founders = {uid for (uid,) in db.query(models.User.id).filter(
        models.User.role == roles.FOUNDER).all()}
    q = scope_to_branch(db.query(models.Expense), models.Expense, user,
                        branch_id).filter(
        models.Expense.date >= start, models.Expense.date <= end,
        models.Expense.staff_user_id.isnot(None),
        models.Expense.category.in_(roles.EXPENSE_SALARY_CATEGORIES))
    out = dict(by_cat)
    for ex in q.all():
        uid = ex.staff_user_id
        if uid in founders:
            key = "founder_salary"
        elif uid in ids:
            key = f"{roles.BUDGET_STAFF_PREFIX}{uid}"
        else:
            continue
        out[ex.category] = out.get(ex.category, 0) - ex.amount
        if abs(out[ex.category]) < 0.5:
            out.pop(ex.category)
        out[key] = out.get(key, 0) + ex.amount
    return out


def _plan_by_cat(lines, month: int, branch_id=None) -> dict:
    """Formada tahrirlanadigan qatorlar — saqlashda shu branch_id bilan
    yoziladi (asoschi: umumiy, hamkor rahbari: o'z markazi)."""
    out = {}
    for l in lines:
        if (l.month == month and l.kind == "expense" and l.category
                and l.branch_id == branch_id):
            out[l.category] = round(out.get(l.category, 0) + l.amount)
    return out


def _budget_cat_label(db: Session, c: str) -> str:
    if c.startswith(roles.BUDGET_STAFF_PREFIX):
        try:
            u = db.query(models.User).get(int(c[len(roles.BUDGET_STAFF_PREFIX):]))
        except ValueError:
            u = None
        return (u.full_name or u.username) if u else "Xodim oyligi"
    return (roles.BUDGET_TEACHER_CATS.get(c)
            or roles.EXPENSE_CATEGORY_LABELS.get(c, c))


@router.get("/api/finance/budget")
def finance_budget(year: int | None = None, month: int | None = None,
                   branch_id: int | None = None,
                   db: Session = Depends(get_db),
                   user=Depends(require_role(*roles.FINANCE_ACCESS))):
    """Budjet: yillik/oylik/filial/bo'lim kesimlari, reja-fakt va yil
    oxiri prognozi. Reja BudgetLine'dan, fakt tirik ma'lumotdan."""
    today = roles.local_today()
    year = year or (today.year if today.month >= 9 else today.year - 1)
    month = month or today.month
    lines = db.query(models.BudgetLine).filter(
        models.BudgetLine.year == year).all()
    # Hamkor markaz rahbari faqat O'Z markazi budjetini ko'radi
    # (2026-09-17) — Jony Academy raqamlari unga ko'rinmaydi.
    ph_bid = user.branch_id if is_partner_head(user) else None
    if ph_bid:
        lines = [l for l in lines if l.branch_id == ph_bid]
    # FILIAL KESIMI (2026-10-02, Jahongir: "men qaysi filialga kirsam shu
    # filialni budjet rejasini o'zgartira olay va statistika hamma
    # narsalar faqat shu filialniki bo'lsin, barcha filialga kirsam
    # barcha filial ko'rsatilsin"). Tepadagi tanlagichdan keladi.
    bid = ph_bid or branch_id
    if bid and not ph_bid:
        lines = [l for l in lines if l.branch_id == bid]

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
        f_inc = _plan_fakt(db, "revenue", s, e, bid) if done else None
        if done:
            et, _bc = _expenses_total(db, user, s, e, bid)
            pr = _payroll_total(db, user, f"{yy:04d}-{m:02d}",
                                bid) or 0
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
    _t, by_cat = _expenses_total(db, user, s, e, bid)
    payroll = round(_payroll_total(db, user, f"{yy:04d}-{month:02d}",
                                   bid) or 0, 0)
    staff_all = _budget_staff(db, user, ph_bid)
    by_cat = _budget_split_staff(db, user, s, e, bid, by_cat, staff_all)
    staff_names = {f"{roles.BUDGET_STAFF_PREFIX}{x['user_id']}": x["name"]
                   for x in staff_all}
    # Formadagi xodimlar — tepada tanlangan filialniki (2026-10-02,
    # Jahongir: "nega boshqa filial xodimlari chiqyabdi bu yerga").
    staff = (_budget_staff_of_branch(db, staff_all, branch_id)
             if branch_id and not ph_bid else staff_all)
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
                     "label": staff_names.get(c) or _budget_cat_label(db, c),
                     "plan": p, "fakt": f,
                     "pct": round(f / p * 100, 0) if p else None})
    cats.append({"category": "teacher_payroll",
                 "label": "Ustozlar ish haqi (avtomat)",
                 "plan": plan_of(month, "expense", cat="teacher_payroll"),
                 "fakt": payroll,
                 "pct": None})
    inc_fakt = _plan_fakt(db, "revenue", s, min(e, today + timedelta(
        days=1)), bid) if s <= today else 0
    monthly = {
        "month": month, "label": roles.UZ_MONTHS[month - 1],
        "income_plan": plan_of(month, "income"),
        "income_fakt": round(inc_fakt or 0, 0),
        "categories": cats,
    }

    # ---- Filial kesimi (tanlangan oy) ----
    d0, d1 = _utc_window(s, e)
    br_rows = []
    _bq = db.query(models.Branch)
    if bid:
        _bq = _bq.filter(models.Branch.id == bid)
    for b in _bq.all():
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
        g = roles.budget_category_group(c)
        dep_f[g] = dep_f.get(g, 0) + v
    dep_f["teacher_payroll"] = payroll
    dep_rows = []
    for g, lbl in roles.BUDGET_DEPARTMENT_LABELS.items():
        p = round(sum(
            l.amount for l in lines
            if l.month == month and l.kind == "expense" and l.category
            and (roles.budget_category_group(l.category) == g
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
        "can_edit": has_role(user, roles.BUDGET_EDIT),
        # Budjet faqat aniq filial tanlanganda kiritiladi
        "branch_id": bid,
        "can_assign": user.role == roles.FOUNDER,
        "branch_name": (db.query(models.Branch).get(bid).name
                        if bid and db.query(models.Branch).get(bid) else None),
        # Filialsiz (umumiy) eski reja qatorlari — qaysi filialga
        # o'tkazishni asoschi hal qiladi
        "unassigned_lines": (db.query(models.BudgetLine).filter(
            models.BudgetLine.year == year,
            models.BudgetLine.branch_id.is_(None)).count()
            if not ph_bid else 0),
        "expense_categories": [
            {"key": c, "label": roles.EXPENSE_CATEGORY_LABELS[c],
             "group": roles.EXPENSE_CATEGORY_GROUP[c],
             "group_label": roles.EXPENSE_GROUP_LABELS.get(
                 roles.EXPENSE_CATEGORY_GROUP[c], "")}
            for c in roles.EXPENSE_CATEGORIES],
        # Budjet formasida har xodim alohida qator (2026-10-02)
        "staff": staff,
        # Har oyning saqlangan rejasi — forma qaysi oy tanlansa o'shani
        # to'ldiradi: {oy: {"income": .., "expense": {kategoriya: ..}}}
        "plans": {
            str(mm): {
                "income": round(sum(l.amount for l in lines
                                    if l.month == mm and l.kind == "income"
                                    and l.branch_id == bid)),
                "expense": _plan_by_cat(lines, mm, bid),
            } for mm in roles.PLAN_MONTHS},
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
    if (p.kind == roles.PAYMENT_ADJUST_KIND and not founder_like(user)
            and user.role not in tuple(roles.MONEY_BALANCE_EDIT)):
        raise HTTPException(
            403, "Balans tuzatishini faqat filial rahbari o'zgartiradi")
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

