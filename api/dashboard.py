"""Auto-extracted from main.py during refactor (split-main). Domain: dashboard."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bisect
import json
from datetime import date, datetime, timedelta, time as dtime
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

@router.get("/api/dashboard", response_model=schemas.DashboardStats)
def dashboard(
    branch_id: int | None = None,
    db: Session = Depends(get_db), user: models.User = Depends(get_current_user)
):
    # 2026-08-12: kartalar ham tepadagi filial tanlagichga bo'ysunadi —
    # avval asoschi Zafarni tanlasa ham butun markaz sonlari chiqardi.
    student_q = scope_to_branch(db.query(models.Student), models.Student,
                                user, branch_id)
    active = student_q.filter(models.Student.status == "active").count()
    trial = student_q.filter(models.Student.status == "trial").count()
    frozen = student_q.filter(models.Student.status == "frozen").count()
    groups = scope_to_branch(db.query(models.Group), models.Group, user,
                             branch_id).count()
    teachers = scope_to_branch(db.query(models.Teacher), models.Teacher,
                               user, branch_id).count()

    month_start = date.today().replace(day=1)
    all_students = student_q.all()
    student_ids = [s.id for s in all_students]

    month_income = 0.0
    if student_ids:
        month_income = (
            db.query(func.coalesce(func.sum(models.Payment.amount), 0.0))
            .filter(models.Payment.kind == "payment")
            .filter(models.Payment.created_at >= month_start)
            .filter(models.Payment.student_id.in_(student_ids))
            .scalar()
            or 0.0
        )

    # Shu oydagi to'lovlar soni va shundan nechtasi YANGI mijoz
    month_pay_count = 0
    month_new_count = 0
    if student_ids:
        pays = (
            db.query(models.Payment)
            .filter(models.Payment.kind == "payment")
            .filter(models.Payment.created_at >= month_start)
            .filter(models.Payment.student_id.in_(student_ids))
            .all()
        )
        month_pay_count = len(pays)
        firsts = _payment_first_dates(db)
        month_new_count = sum(
            1 for p in pays if firsts.get(p.student_id) == p.created_at
        )

    staff_count = scope_to_branch(
        db.query(models.User), models.User, user, branch_id
    ).filter(models.User.is_active == 1).count()

    balances = [(s.id, student_balance(db, s.id)) for s in all_students]
    total_debt = sum(b for _, b in balances if b < 0)
    debtor_count = sum(1 for _, b in balances if b < 0)

    return schemas.DashboardStats(
        active_students=active,
        trial_students=trial,
        frozen_students=frozen,
        total_groups=groups,
        total_teachers=teachers,
        month_payment_count=month_pay_count,
        month_new_payment_count=month_new_count,
        staff_count=staff_count,
        month_income=float(month_income),
        total_debt=float(total_debt),
        debtor_count=debtor_count,
    )

@router.get("/api/dashboard/trend")
def dashboard_trend(
    months: int = 6,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Income for each of the last `months` calendar months, scoped to the
    caller's branch the same way /api/dashboard is. Used for the dashboard
    trend chart."""
    student_q = scope_to_branch(db.query(models.Student), models.Student, user)
    student_ids = [s.id for s in student_q.all()]

    today = date.today()
    y, m = today.year, today.month
    periods = []
    for _ in range(max(1, min(months, 24))):
        periods.append((y, m))
        m -= 1
        if m == 0:
            y, m = y - 1, 12
    periods.reverse()

    results = []
    for yy, mm in periods:
        start, end = billing.month_bounds(yy, mm)
        income = 0.0
        if student_ids:
            income = (
                db.query(func.coalesce(func.sum(models.Payment.amount), 0.0))
                .filter(models.Payment.kind == "payment")
                .filter(models.Payment.created_at >= start)
                .filter(models.Payment.created_at < end + timedelta(days=1))
                .filter(models.Payment.student_id.in_(student_ids))
                .scalar()
                or 0.0
            )
        results.append({"period": f"{yy:04d}-{mm:02d}", "income": float(income)})
    return results

@router.get("/api/dashboard/student-growth")
def student_growth(
    window: str = "6m",
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Cumulative enrolled-student count over time, scoped like /api/dashboard.
    `window` picks both the range and the bucket size:
    - "1m":  last 30 days, daily buckets
    - "6m":  last 6 months, monthly buckets (default)
    - "1y":  last 12 months, monthly buckets
    - "all": from the earliest enrollment to today, monthly buckets
    Har bir nuqta = O'SHA PAYTDA O'QIB YURGAN o'quvchilar soni
    (2026-08-12, Jahongir: "bu yerda faol o'quvchilar hisoblanishi
    kerak edi, nega 2680 bo'lib ketdi" - avval jami ro'yxatga
    olinganlar yig'indisi chizilardi va LC UP'dan import qilingan
    arxiv o'quvchilar grafikni osmonga otvorgan edi).

    Qoida: enrolled_date <= sana VA (ketmagan YOKI left_date > sana).
    Ketgan-u sanasi noma'lum (arxiv, left_date bo'sh) yozuvlar
    grafikka umuman kirmaydi - ular tarixni shishiradi xolos."""
    # Filial tanlagichga bo'ysunadi — kartalar Zafarni ko'rsatsa,
    # grafik ham Zafarni ko'rsatsin (2026-08-12).
    student_q = scope_to_branch(db.query(models.Student), models.Student,
                                user, branch_id)
    starts, ends = [], []
    for s in student_q.all():
        if not s.enrolled_date:
            continue
        if s.left_date is None and (s.status or "") == "archived":
            continue          # qachon ketgani noma'lum - hisobga kirmaydi
        starts.append(s.enrolled_date)
        if s.left_date:
            ends.append(s.left_date)
    starts.sort()
    ends.sort()
    dates = starts            # eng erta sana va bo'shlik tekshiruvi uchun
    today = date.today()
    granularity = "day" if window == "1m" else "month"

    # TARIXIY STATISTIKA: tizimdan oldingi yillar sonlari (Analitika ->
    # Tarix bo'limida kiritilgan) shu grafikka ham qo'shiladi. Sonlar
    # butun markaz bo'yicha, shuning uchun faqat butun tashkilotni
    # ko'radiganlarga aralashtiramiz — filialga bog'langan xodim
    # grafigi buzilmaydi.
    _snaps = []
    # Tarixiy sonlar BUTUN MARKAZ bo'yicha - filial filtrida aralashmaydi
    if branch_id:
        pass
    elif user.role in tuple(roles.ORG_WIDE_ROLES) or not user.branch_id:
        _snaps = (db.query(models.StudentCountSnapshot)
                  .order_by(models.StudentCountSnapshot.date).all())
    _sd = [x.date for x in _snaps]
    _sc = [x.count for x in _snaps]

    def snap_through(cutoff: date) -> int:
        i = bisect.bisect_right(_sd, cutoff)
        return _sc[i - 1] if i else 0

    if not dates and not _snaps:
        return {"granularity": granularity, "points": []}

    def count_through(cutoff: date) -> int:
        live = (bisect.bisect_right(starts, cutoff)
                - bisect.bisect_right(ends, cutoff))
        # O'tmishda jonli baza bo'sh — tarixiy son ustun; hozirda
        # jonli baza to'liq — kattasi olinadi.
        return max(live, snap_through(cutoff))

    points = []
    if window == "1m":
        d = today - timedelta(days=29)
        while d <= today:
            points.append({"period": d.isoformat(), "count": count_through(d)})
            d += timedelta(days=1)
    else:
        if window == "1y":
            months_back = 11
        elif window == "all":
            _cands = ([dates[0]] if dates else []) + ([_sd[0]] if _sd else [])
            earliest = min(_cands)
            months_back = (today.year - earliest.year) * 12 + (today.month - earliest.month)
        else:  # "6m" and any unrecognized value
            months_back = 5
        y, m = today.year, today.month
        periods = []
        for _ in range(months_back + 1):
            periods.append((y, m))
            m -= 1
            if m == 0:
                y, m = y - 1, 12
        periods.reverse()
        for yy, mm in periods:
            _, month_end = billing.month_bounds(yy, mm)
            cutoff = min(month_end, today)
            points.append({"period": f"{yy:04d}-{mm:02d}", "count": count_through(cutoff)})

    return {"granularity": granularity, "points": points}

@router.get("/api/reports/cashflow")
def report_cashflow(
    months: int = 6,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.CASHFLOW_ACCESS)),
):
    """Oxirgi N oy uchun pul oqimi: qancha kirdi (naqd/plastik/terminal
    kesimida), qancha chiqdi (xarajat + ustozlar ish haqi), sof qoldiq."""
    months = max(1, min(months, 24))
    today = date.today()
    rows = []
    for back in range(months - 1, -1, -1):
        y, m = _shift_month(today.year, today.month, -back)
        start, end = billing.month_bounds(y, m)
        period = _period_key(y, m)

        methods = _income_by_method(db, user, start, end)
        income = sum(methods.values())
        exp_total, _ = _expenses_total(db, user, start, end)
        payroll = _payroll_total(db, user, period)

        rows.append({
            "period": period,
            "cash": methods["cash"],
            "card": methods["card"],
            "terminal": methods["terminal"],
            "other": methods["other"],
            "income": income,
            "expenses": exp_total,
            "payroll": payroll,
            "outflow": exp_total + payroll,
            "net": income - exp_total - payroll,
        })

    keys = ["cash", "card", "terminal", "other", "income",
            "expenses", "payroll", "outflow", "net"]
    return {"rows": rows, "totals": {k: sum(r[k] for r in rows) for k in keys}}

@router.get("/api/reports/pnl")
def report_pnl(
    year: int,
    month: int,
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FINANCE_ACCESS)),
):
    """Bir oylik foyda-zarar. Chiqim = qo'lda kiritilgan xarajatlar +
    avtomatik hisoblangan ustozlar ish haqi."""
    start, end = billing.month_bounds(year, month)
    period = _period_key(year, month)

    methods = _income_by_method(db, user, start, end, branch_id)
    income = sum(methods.values())
    exp_total, by_cat = _expenses_total(db, user, start, end, branch_id)
    payroll = _payroll_total(db, user, period, branch_id)
    profit = income - exp_total - payroll

    lines = [{"category": c, "amount": a, "auto": False}
             for c, a in sorted(by_cat.items(), key=lambda kv: -kv[1])]
    if payroll:
        # "auto" - bu qatorni qo'lda kiritish shart emasligini bildiradi.
        lines.append({"category": "teacher_payroll", "amount": payroll, "auto": True})

    return {
        "period": period,
        "income": income,
        "income_by_method": methods,
        "expense_lines": lines,
        "expenses_total": exp_total,
        "payroll_total": payroll,
        "outflow_total": exp_total + payroll,
        "profit": profit,
        "margin": round(profit / income * 100, 1) if income else 0,
    }

@router.get("/api/reports/teacher-payroll")
def report_teacher_payroll(
    year: int,
    month: int,
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FINANCE_ACCESS, *roles.SALARY_VIEW_ALL,
                              roles.TEACHER, roles.SUPPORT_TEACHER)),
):
    """Bir oylik ustozlar ish haqi.

    Manba - YOQLAMA. Hech qanday "hisoblash" tugmasi yo'q: ro'yxat
    har safar darslardan qayta hisoblanadi. Yoqlama tuzatilsa oylik
    ham o'zi to'g'rilanadi.

    "paid" - ustozga haqiqatda berilgan pul (avans + oylik)."""
    period = _period_key(year, month)
    start, end = billing.month_bounds(year, month)

    tq = scope_to_branch(db.query(models.Teacher), models.Teacher,
                         user, branch_id)

    # O'qituvchi faqat O'ZINING oyligini ko'radi - hamkasbining maoshi
    # unga ko'rinmaydi.
    own_only = user.role not in tuple(roles.FINANCE_ACCESS
                                      + roles.SALARY_VIEW_ALL)
    if own_only:
        me = _teacher_of_user(db, user)
        if not me:
            return {"period": period, "rows": [], "teacher_count": 0,
                    "total": 0.0, "paid": 0.0, "unpaid": 0.0,
                    "own_only": True}
        tq = tq.filter(models.Teacher.id == me.id)

    rows = []
    for t in tq.all():
        e = _teacher_earned(db, t.id, since=start, until=end)
        if e["amount"] == 0:
            continue
        paid = _teacher_paid(db, t.id, since=start, until=end)
        rows.append({
            "teacher_id": t.id,
            "full_name": t.full_name,
            "branch": t.branch.name if t.branch else None,
            "groups": [{
                "group_id": g["group_id"],
                "group": g["group"],
                "students": (round(g["attendances"] / g["lessons"])
                             if g["lessons"] else 0),
                "held_lessons": g["lessons"],
                "taught_lessons": g["lessons"],
                "attendances": g["attendances"],
                "rate": g["rate"],
                "rate_per_student_month": g["rate_per_student_month"],
                "standard_lessons": g["standard_lessons"],
                "amount": round(g["amount"], 2),
            } for g in e["by_group"]],
            "students": sum(round(g["attendances"] / g["lessons"])
                            for g in e["by_group"] if g["lessons"]),
            "lessons": e["lessons"],
            "attendances": e["attendances"],
            "amount": e["amount"],
            "paid_amount": paid,
            "left": round(e["amount"] - paid, 2),
        })

    rows.sort(key=lambda r: -r["amount"])
    total = round(sum(r["amount"] for r in rows), 2)
    paid = round(sum(r["paid_amount"] for r in rows), 2)
    return {
        "period": period,
        "rows": rows,
        "total": total,
        "paid": paid,
        "unpaid": round(total - paid, 2),
        "own_only": own_only,
        "teacher_count": len(rows),
    }

@router.get("/api/reports/funnel")
def report_funnel(
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FINANCE_ACCESS)),
):
    """Ikki qismli voronka:

    1) Lid bosqichlari - so'rov kelganidan o'quvchiga aylangunicha qayerda
       yo'qotilyapti.
    2) To'lovdan keyingi oylar - 1-oy, 2-oy ... 12-oy. Qaysi oyda eng ko'p
       o'quvchi ketayotgani shu yerda ko'rinadi.
    """
    # ---- 1. Lid voronkasi -------------------------------------------------
    leads = scope_to_branch(db.query(models.Lead), models.Lead, user, branch_id).all()
    by_stage = {st: 0 for st in roles.LEAD_STAGES}
    for l in leads:
        if l.stage in by_stage:
            by_stage[l.stage] += 1

    total_leads = len(leads)
    # Voronka kümülativ: keyingi bosqichga o'tganlar oldingisini ham bosib
    # o'tgan hisoblanadi.
    order = roles.LEAD_FUNNEL_ORDER
    stages = []
    remaining = total_leads
    for i, st in enumerate(order):
        reached = sum(by_stage[s] for s in order[i:])
        stages.append({
            "stage": st,
            "reached": reached,
            "here_now": by_stage[st],
            "percent": round(reached / total_leads * 100, 1) if total_leads else 0,
            "lost_here": by_stage[st] if st != "converted" else 0,
        })
        remaining = reached
    rejected = by_stage.get("rejected", 0)

    # ---- 2. To'lovdan keyingi oylar --------------------------------------
    students = scope_to_branch(db.query(models.Student), models.Student, user, branch_id).all()
    first_paid = _first_payment_dates(db)
    today = date.today()

    lives = []
    for s in students:
        first = first_paid.get(s.id)
        if not first:
            continue  # hali to'lamagan - voronkaning bu qismiga kirmaydi
        start = first.date()
        end = s.left_date or today
        lives.append({
            "months": _months_between(start, end),
            "churned": s.left_date is not None,
        })

    months = []
    for n in range(1, 13):
        # Natijasi ma'lum bo'lganlar: yo shu oyga yetgan, yo undan oldin ketgan
        survived = sum(1 for l in lives if l["months"] >= n)
        known_lost = sum(1 for l in lives if l["churned"] and l["months"] < n)
        eligible = survived + known_lost
        lost_here = sum(
            1 for l in lives
            if l["churned"] and (n - 1) <= l["months"] < n
        )
        months.append({
            "month": n,
            "eligible": eligible,
            "survived": survived,
            "retention": round(survived / eligible * 100, 1) if eligible else 0,
            "lost": lost_here,
        })

    worst = max(months, key=lambda m: m["lost"]) if months else None
    return {
        "leads": {
            "total": total_leads,
            "stages": stages,
            "rejected": rejected,
        },
        "students": {
            "paying": len(lives),
            "churned": sum(1 for l in lives if l["churned"]),
            "months": months,
            # Eng ko'p o'quvchi yo'qotiladigan oy - asosiy savolga javob
            "worst_month": worst["month"] if worst and worst["lost"] else None,
            "worst_month_lost": worst["lost"] if worst else 0,
        },
    }

@router.get("/api/reports/quality")
def report_quality(
    year: int,
    month: int,
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FINANCE_ACCESS)),
):
    """Ta'lim sifati - imtihon natijalaridan chiqadi.

    Guruh reytingi = shu oydagi imtihonlardagi o'rtacha foiz.
    Ustoz reytingi = uning guruhlari o'rtachasi.
    Filial reytingi = filialdagi guruhlar o'rtachasi.
    Markaz reytingi = hamma guruhlar o'rtachasi.

    Guruhlar teng vaznda olinadi (kattaligiga qarab emas) - aks holda
    bitta katta guruh butun ko'rsatkichni belgilab qo'yardi."""
    start, end = billing.month_bounds(year, month)

    exams = db.query(models.Exam).filter(
        models.Exam.date >= start, models.Exam.date <= end
    ).all()
    groups = {g.id: g for g in scope_to_branch(
        db.query(models.Group), models.Group, user, branch_id).all()}
    teachers = {t.id: t for t in db.query(models.Teacher).all()}
    branches = {b.id: b for b in db.query(models.Branch).all()}

    # Guruh -> natijalar
    per_group = {}
    for e in exams:
        g = groups.get(e.group_id)
        if not g:
            continue
        scored = [r for r in e.results if r.percent is not None and not r.absent]
        if not scored:
            continue
        row = per_group.setdefault(g.id, {
            "group_id": g.id, "group": g.name,
            "subject": g.subject, "level": g.level,
            "teacher_id": g.teacher_id,
            "teacher": teachers[g.teacher_id].full_name
            if g.teacher_id in teachers else None,
            "branch_id": g.branch_id,
            "branch": branches[g.branch_id].name
            if g.branch_id in branches else None,
            "exams": 0, "results": 0, "sum": 0.0,
        })
        row["exams"] += 1
        row["results"] += len(scored)
        row["sum"] += sum(r.percent for r in scored)

    group_rows = []
    for r in per_group.values():
        group_rows.append({**{k: v for k, v in r.items() if k != "sum"},
                           "avg": round(r["sum"] / r["results"], 1)})
    group_rows.sort(key=lambda r: -r["avg"])

    def rollup(key_id, key_name):
        acc = {}
        for r in group_rows:
            k = r[key_id]
            if k is None:
                continue
            a = acc.setdefault(k, {"id": k, "name": r[key_name],
                                   "groups": 0, "sum": 0.0, "exams": 0})
            a["groups"] += 1
            a["sum"] += r["avg"]
            a["exams"] += r["exams"]
        out = [{"id": a["id"], "name": a["name"], "groups": a["groups"],
                "exams": a["exams"], "avg": round(a["sum"] / a["groups"], 1)}
               for a in acc.values()]
        out.sort(key=lambda x: -x["avg"])
        return out

    centre = (round(sum(r["avg"] for r in group_rows) / len(group_rows), 1)
              if group_rows else None)

    return {
        "period": _period_key(year, month),
        "centre": {
            "avg": centre,
            "groups": len(group_rows),
            "exams": sum(r["exams"] for r in group_rows),
            "results": sum(r["results"] for r in group_rows),
        },
        "branches": rollup("branch_id", "branch"),
        "teachers": rollup("teacher_id", "teacher"),
        "groups": group_rows,
    }

@router.get("/api/reports/sales-managers")
def report_sales_managers(
    window: str = "month",
    year: int = None,
    month: int = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FINANCE_ACCESS)),
):
    """Har bir sotuv menejerining sotuv foizi.

    Foiz = o'quvchiga aylangan lidlar / unga biriktirilgan lidlar.
    Davr: oy / 3 oy / 6 oy / 1 yil / butun davr - lid yaratilgan
    sanaga qarab."""
    today = date.today()
    if window == "month":
        y = year or today.year
        m = month or today.month
        start, end = billing.month_bounds(y, m)
        label = _period_key(y, m)
    elif window in ("3m", "6m", "1y"):
        back = {"3m": 3, "6m": 6, "1y": 12}[window]
        sy, sm = _shift_month(today.year, today.month, -(back - 1))
        start, _ = billing.month_bounds(sy, sm)
        end = today
        label = f"{_period_key(sy, sm)} … {_period_key(today.year, today.month)}"
    elif window == "all":
        start, end, label = date(2000, 1, 1), today, "Butun davr"
    else:
        raise HTTPException(400, "Noto'g'ri davr")

    start_dt, end_dt = _utc_window(start, end)

    managers = db.query(models.User).filter(
        models.User.role == roles.SALES_MANAGER)
    if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
        managers = managers.filter(models.User.branch_id == user.branch_id)
    managers = managers.order_by(models.User.full_name).all()

    leads = scope_to_branch(db.query(models.Lead), models.Lead, user).filter(
        models.Lead.created_at >= start_dt,
        models.Lead.created_at <= end_dt,
    ).all()

    by_user = {}
    for l in leads:
        row = by_user.setdefault(l.assigned_user_id, {
            "total": 0, "converted": 0, "rejected": 0, "in_progress": 0})
        row["total"] += 1
        if l.converted_student_id or l.stage == "converted":
            row["converted"] += 1
        elif l.stage == "rejected":
            row["rejected"] += 1
        else:
            row["in_progress"] += 1

    rows = []
    for m_ in managers:
        st = by_user.get(m_.id, {"total": 0, "converted": 0,
                                 "rejected": 0, "in_progress": 0})
        rows.append({
            "user_id": m_.id,
            "full_name": m_.full_name,
            "branch": m_.branch.name if m_.branch else None,
            "active": bool(m_.is_active),
            "leads": st["total"],
            "converted": st["converted"],
            "rejected": st["rejected"],
            "in_progress": st["in_progress"],
            "conversion": round(st["converted"] / st["total"] * 100, 1)
            if st["total"] else 0,
        })
    rows.sort(key=lambda r: (-r["conversion"], -r["converted"]))

    # Biriktirilmagan lidlar - ular hech kimning ko'rsatkichiga kirmaydi,
    # lekin ko'rinib turishi kerak.
    un = by_user.get(None, {"total": 0, "converted": 0})
    total_leads = sum(r["leads"] for r in rows) + un["total"]
    total_conv = sum(r["converted"] for r in rows) + un["converted"]

    return {
        "window": window,
        "label": label,
        "rows": rows,
        "unassigned": un["total"],
        "totals": {
            "leads": total_leads,
            "converted": total_conv,
            "conversion": round(total_conv / total_leads * 100, 1)
            if total_leads else 0,
        },
    }

@router.get("/api/analytics/summary")
def analytics_summary(
    months: int = 12,
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FINANCE_ACCESS)),
):
    """Analitika sahifasi uchun bitta so'rovda hamma raqam:
    oylik kirim/chiqim/foyda, xarajat guruhlari, ustozlar ulushi."""
    # 0 -> butun davr (eng eski yozuvdan bugungacha)
    if months == 0:
        oldest = db.query(func.min(models.Payment.created_at)).scalar()
        oldest_e = db.query(func.min(models.Expense.date)).scalar()
        t = date.today()
        cands = [x.date() if hasattr(x, "date") else x
                 for x in [oldest, oldest_e] if x]
        first = min(cands) if cands else t
        months = max(1, (t.year - first.year) * 12 + (t.month - first.month) + 1)
    months = max(1, min(months, 120))
    today = date.today()

    monthly = []
    group_totals = {}
    category_totals = {}

    for back in range(months - 1, -1, -1):
        y, m = _shift_month(today.year, today.month, -back)
        start, end = billing.month_bounds(y, m)
        period = _period_key(y, m)

        income = sum(_income_by_method(db, user, start, end, branch_id).values())
        exp_total, by_cat = _expenses_total(db, user, start, end, branch_id)
        payroll = _payroll_total(db, user, period, branch_id)

        for cat, amt in by_cat.items():
            category_totals[cat] = category_totals.get(cat, 0) + amt
            grp = roles.EXPENSE_CATEGORY_GROUP.get(cat, "other")
            group_totals[grp] = group_totals.get(grp, 0) + amt
        if payroll:
            group_totals["teacher_salary"] = (
                group_totals.get("teacher_salary", 0) + payroll)

        outflow = exp_total + payroll
        monthly.append({
            "period": period,
            "income": income,
            "expenses": exp_total,
            "payroll": payroll,
            "outflow": outflow,
            "profit": income - outflow,
            # Ustozlarning ulushi - kirimning necha foizi ish haqiga ketdi
            "teacher_share": round(payroll / income * 100, 1) if income else 0,
        })

    total_income = sum(m["income"] for m in monthly)
    total_payroll = sum(m["payroll"] for m in monthly)
    total_expenses = sum(m["expenses"] for m in monthly)
    total_profit = total_income - total_payroll - total_expenses

    groups = sorted(
        [{"key": k, "label": roles.EXPENSE_GROUP_LABELS.get(k, k), "amount": v}
         for k, v in group_totals.items() if v > 0],
        key=lambda g: -g["amount"],
    )
    categories = sorted(
        [{"key": k, "label": roles.EXPENSE_CATEGORY_LABELS.get(k, k),
          "group": roles.EXPENSE_CATEGORY_GROUP.get(k, "other"), "amount": v}
         for k, v in category_totals.items() if v > 0],
        key=lambda c: -c["amount"],
    )

    return {
        "months": monthly,
        "expense_groups": groups,
        "expense_categories": categories,
        "totals": {
            "income": total_income,
            "expenses": total_expenses,
            "payroll": total_payroll,
            "outflow": total_payroll + total_expenses,
            "profit": total_profit,
            "margin": round(total_profit / total_income * 100, 1)
            if total_income else 0,
            "teacher_share": round(total_payroll / total_income * 100, 1)
            if total_income else 0,
        },
    }

def _first_payment_dates(db: Session) -> dict:
    """Har bir o'quvchining eng birinchi to'lov sanasi. Shu sana orqali
    to'lov "yangi" (birinchi marta) yoki "eski" ekani aniqlanadi."""
    rows = (
        db.query(models.Payment.student_id,
                 func.min(models.Payment.created_at))
        .filter(models.Payment.kind == "payment")
        .group_by(models.Payment.student_id)
        .all()
    )
    return {sid: dt for sid, dt in rows}

def _collection_bonus(db: Session, students: int, percent: float) -> float:
    """Filialdagi FAOL o'quvchi soni va yig'ish foiziga mos eng katta
    bonus. Hech qanday qator to'g'ri kelmasa - 0 (masalan 50 tagacha
    o'quvchida bonus yo'q)."""
    best = 0.0
    for r in db.query(models.KpiCollectionRule).all():
        if students < r.min_students:
            continue
        if r.max_students is not None and students > r.max_students:
            continue
        if percent + 1e-9 < r.min_percent:
            continue
        best = max(best, r.bonus)
    return best

def _new_client_bonus(db: Session, count: int) -> float:
    """Yangi mijozlar soniga mos eng yuqori pog'ona bonusi."""
    best = 0.0
    for r in db.query(models.KpiNewClientRule).all():
        if count >= r.min_clients:
            best = max(best, r.bonus)
    return best

@router.get("/api/kpi/admins", response_model=schemas.AdminKpiResult)
def admin_kpi(
    year: int,
    month: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.KPI_VIEW)),
):
    start, end = billing.month_bounds(year, month)
    period = _period_key(year, month)
    start_dt, end_dt = _utc_window(start, end)

    admins = db.query(models.User).filter(
        models.User.role == roles.SALES_MANAGER,
        models.User.is_active == 1,
    )
    if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
        admins = admins.filter(models.User.branch_id == user.branch_id)
    admins = admins.order_by(models.User.full_name).all()
    if not admins:
        return schemas.AdminKpiResult(period=period, rows=[])

    first_paid = _first_payment_dates(db)
    students = db.query(models.Student).all()
    student_branch = {s.id: s.branch_id for s in students}

    # Filial ko'rsatkichlarini bir marta hisoblaymiz.
    stats = {}
    for a in admins:
        if a.branch_id in stats:
            continue
        stats[a.branch_id] = {
            "active_students": sum(
                1 for s in students
                if s.branch_id == a.branch_id and s.status == "active"),
            "expected": 0.0, "collected": 0.0,
            "new_clients": set(), "new_revenue": 0.0,
        }

    # "Tushishi kerak" bo'lgan pul - shu oyda hisoblangan summalar.
    # Faqat ESKI o'quvchilar bo'yicha: yangi mijozning birinchi to'lovi
    # yig'ish foiziga kirmaydi, u alohida bonus bilan baholanadi.
    charges = db.query(models.Payment).filter(
        models.Payment.kind == "charge",
        models.Payment.created_at >= start_dt,
        models.Payment.created_at <= end_dt,
    ).all()
    for c in charges:
        st = stats.get(student_branch.get(c.student_id))
        if st is None:
            continue
        first = first_paid.get(c.student_id)
        if first is None or first >= start_dt:
            continue  # hali to'lamagan yoki yangi mijoz
        st["expected"] += abs(c.amount)

    # Haqiqatda tushgan pul.
    pays = db.query(models.Payment).filter(
        models.Payment.kind == "payment",
        models.Payment.created_at >= start_dt,
        models.Payment.created_at <= end_dt,
    ).all()
    for p in pays:
        st = stats.get(student_branch.get(p.student_id))
        if st is None:
            continue
        first = first_paid.get(p.student_id)
        if first is not None and first >= start_dt:
            # Birinchi marta to'lagan - yangi mijoz
            st["new_clients"].add(p.student_id)
            st["new_revenue"] += p.amount
        else:
            st["collected"] += p.amount

    rows = []
    for a in admins:
        st = stats[a.branch_id]
        pct = (round(st["collected"] / st["expected"] * 100, 1)
               if st["expected"] else 0.0)
        col_bonus = _collection_bonus(db, st["active_students"], pct)
        new_count = len(st["new_clients"])
        new_bonus = _new_client_bonus(db, new_count)
        fix = a.fix_salary or 0.0

        # Sotuv menejeri va administrator FAQAT o'zining KPI'sini
        # ko'radi - hamkasbining bonusi unga ko'rinmaydi.
        if (user.role not in tuple(roles.FULL_ACCESS + [roles.FINANCE_DIRECTOR])
                and a.id != user.id):
            continue
        rows.append(schemas.AdminKpi(
            user_id=a.id, full_name=a.full_name, branch_id=a.branch_id,
            branch=a.branch.name if a.branch else None,
            fix_salary=fix,
            active_students=st["active_students"],
            expected=st["expected"], collected=st["collected"],
            collection_percent=pct, collection_bonus=col_bonus,
            new_clients=new_count, new_client_revenue=st["new_revenue"],
            new_client_bonus=new_bonus,
            total=fix + col_bonus + new_bonus,
        ))
    return schemas.AdminKpiResult(period=period, rows=rows)

@router.get("/api/kpi/rules", response_model=schemas.KpiRules)
def get_kpi_rules(
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.KPI_VIEW)),
):
    return schemas.KpiRules(
        collection=db.query(models.KpiCollectionRule).order_by(
            models.KpiCollectionRule.min_students,
            models.KpiCollectionRule.min_percent.desc()).all(),
        new_clients=db.query(models.KpiNewClientRule).order_by(
            models.KpiNewClientRule.min_clients).all(),
    )

@router.put("/api/kpi/rules", response_model=schemas.KpiRules)
def replace_kpi_rules(
    payload: schemas.KpiRulesIn,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.KPI_ADMIN)),
):
    """Qoidalar jadvalini almashtiradi. Faqat asoschi - bu bevosita
    xodimlarning ish haqiga ta'sir qiladi."""
    for r in payload.collection:
        if r.bonus < 0 or not (0 <= r.min_percent <= 100):
            raise HTTPException(400, "Noto'g'ri qiymat")
        if r.max_students is not None and r.max_students < r.min_students:
            raise HTTPException(
                400, "Yuqori chegara quyi chegaradan kichik bo'lmasligi kerak")
    for r in payload.new_clients:
        if r.bonus < 0 or r.min_clients < 0:
            raise HTTPException(400, "Noto'g'ri qiymat")

    db.query(models.KpiCollectionRule).delete()
    db.query(models.KpiNewClientRule).delete()
    for r in payload.collection:
        db.add(models.KpiCollectionRule(
            min_students=r.min_students, max_students=r.max_students,
            min_percent=r.min_percent, bonus=r.bonus))
    for r in payload.new_clients:
        db.add(models.KpiNewClientRule(min_clients=r.min_clients, bonus=r.bonus))
    db.commit()
    return get_kpi_rules(db, user)

@router.get("/api/reports/ltv")
def report_ltv(
    dimension: str = "branch",
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FINANCE_ACCESS)),
):
    """LTV - bitta mijoz o'rtacha qancha vaqt qoladi va shu vaqt ichida
    qancha pul olib keladi. Kesim: filial / ustoz / guruh.

    Ustoz va guruh kesimi o'quvchining HOZIRGI guruhiga qarab bo'linadi -
    guruh almashtirgan o'quvchi oxirgi guruhiga yoziladi."""
    if dimension not in ("branch", "teacher", "group", "subject"):
        raise HTTPException(400, "Noto'g'ri kesim")

    students = scope_to_branch(
        db.query(models.Student), models.Student, user
    ).all()
    if not students:
        return {"dimension": dimension, "rows": [], "overall": None}

    # Har bir o'quvchining haqiqiy to'lovlari (charge emas) bir so'rovda.
    paid_rows = db.query(
        models.Payment.student_id, func.sum(models.Payment.amount)
    ).filter(models.Payment.kind == "payment").group_by(
        models.Payment.student_id
    ).all()
    paid = {sid: amt or 0 for sid, amt in paid_rows}

    groups = {g.id: g for g in db.query(models.Group).all()}
    teachers = {t.id: t for t in db.query(models.Teacher).all()}
    branches = {b.id: b for b in db.query(models.Branch).all()}
    today = date.today()

    buckets = {}
    for s in students:
        if dimension == "branch":
            key = s.branch_id
            label = branches[key].name if key in branches else "Filialsiz"
        elif dimension == "group":
            key = s.group_id
            label = groups[key].name if key in groups else "Guruhsiz"
        elif dimension == "subject":
            g = groups.get(s.group_id)
            key = g.subject if g else None
            label = (roles.SUBJECT_LABELS.get(key or "", None)
                     or "Fan belgilanmagan")
        else:
            g = groups.get(s.group_id)
            key = g.teacher_id if g else None
            label = teachers[key].full_name if key in teachers else "Ustoz biriktirilmagan"

        b = buckets.setdefault(str(key), {
            "key": key, "label": label, "students": 0, "left": 0,
            "total_revenue": 0.0, "total_months": 0.0,
        })
        b["students"] += 1
        b["total_revenue"] += paid.get(s.id, 0)
        b["total_months"] += _months_between(
            s.enrolled_date or today, s.left_date or today
        )
        if s.left_date:
            b["left"] += 1

    rows = []
    for b in buckets.values():
        n = b["students"] or 1
        rows.append({
            "key": b["key"],
            "label": b["label"],
            "students": b["students"],
            "left": b["left"],
            "avg_months": round(b["total_months"] / n, 1),
            "avg_revenue": round(b["total_revenue"] / n),
            "total_revenue": b["total_revenue"],
            # Ketganlar ulushi - qaysi filial/ustozda mijoz ko'proq
            # to'xtab qolayotgani darrov ko'rinsin.
            "churn": round(b["left"] / n * 100, 1),
        })
    rows.sort(key=lambda r: -r["avg_revenue"])

    total_students = sum(r["students"] for r in rows) or 1
    overall = {
        "students": sum(r["students"] for r in rows),
        "left": sum(r["left"] for r in rows),
        "avg_months": round(
            sum(r["avg_months"] * r["students"] for r in rows) / total_students, 1),
        "avg_revenue": round(
            sum(r["total_revenue"] for r in rows) / total_students),
        "total_revenue": sum(r["total_revenue"] for r in rows),
    }
    return {"dimension": dimension, "rows": rows, "overall": overall}

@router.get("/api/reports/teacher-retention")
def report_teacher_retention(
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FINANCE_ACCESS)),
):
    """Ustozlar qancha vaqt ishlab turadi. Ishga kirgan sana ustoz
    yaratilganda avtomatik qo'yiladi, ketgan sana esa "ishlamaydi" deb
    belgilanganda."""
    teachers = scope_to_branch(
        db.query(models.Teacher), models.Teacher, user
    ).all()
    today = date.today()
    year_ago = today - timedelta(days=365)

    rows = []
    for t in teachers:
        hired = t.hired_date or (t.created_at.date() if t.created_at else today)
        rows.append({
            "id": t.id,
            "full_name": t.full_name,
            "branch": t.branch.name if t.branch else None,
            "hired_date": hired.isoformat(),
            "left_date": t.left_date.isoformat() if t.left_date else None,
            "active": bool(t.is_active),
            "months": _months_between(hired, t.left_date or today),
        })
    rows.sort(key=lambda r: -r["months"])

    active = [r for r in rows if r["active"]]
    left = [r for r in rows if not r["active"]]
    # Oxirgi 12 oyda ketganlar / davr boshidagi jamoa hajmi.
    left_12m = [r for r in left if r["left_date"] and r["left_date"] >= year_ago.isoformat()]
    base = len(active) + len(left_12m)

    return {
        "rows": rows,
        "summary": {
            "active": len(active),
            "left": len(left),
            "left_last_12m": len(left_12m),
            "avg_tenure_active": round(
                sum(r["months"] for r in active) / len(active), 1) if active else 0,
            "avg_tenure_left": round(
                sum(r["months"] for r in left) / len(left), 1) if left else 0,
            "turnover_12m": round(len(left_12m) / base * 100, 1) if base else 0,
        },
    }

def _payment_first_dates(db: Session) -> dict:
    """Har bir o'quvchining ENG BIRINCHI to'lov sanasi (id bilan).
    Shu sana bilan mos tushgan to'lov "yangi to'lov", qolganlari "eski"."""
    rows = (
        db.query(models.Payment.student_id,
                 func.min(models.Payment.created_at))
        .filter(models.Payment.kind == "payment")
        .group_by(models.Payment.student_id)
        .all()
    )
    return {sid: dt for sid, dt in rows}

@router.get("/api/reports/cashflow-ledger")
def cashflow_ledger(
    year: int,
    month: int,
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.CASHFLOW_ACCESS)),
):
    """Bir oylik kassa daftari: har bir kirim va chiqim alohida qator.
    Tepasida - Kirim / Chiqim / Kassa jadvali usullar kesimida, va
    yangi/eski to'lovlar soni bilan summasi."""
    start, end = billing.month_bounds(year, month)
    d0, d1 = _utc_window(start, end)

    # --- Kirimlar ---
    pq = (
        db.query(models.Payment, models.Student)
        .join(models.Student, models.Payment.student_id == models.Student.id)
        .filter(models.Payment.kind == "payment",
                models.Payment.created_at >= d0,
                models.Payment.created_at <= d1)
    )
    if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
        pq = pq.filter(_branch_in(db, user, models.Student.branch_id))
    elif branch_id:
        pq = pq.filter(models.Student.branch_id == branch_id)

    first_dates = _payment_first_dates(db)
    branches = {b.id: b.name for b in db.query(models.Branch).all()}

    rows = []
    new_cnt = new_sum = old_cnt = old_sum = 0
    kirim = {m: 0.0 for m in roles.PAYMENT_METHODS}

    for p, st in pq.all():
        method = p.method if p.method in kirim else "cash"
        kirim[method] += p.amount
        is_new = first_dates.get(st.id) == p.created_at
        if is_new:
            new_cnt += 1
            new_sum += p.amount
        else:
            old_cnt += 1
            old_sum += p.amount
        rows.append({
            "id": f"p{p.id}",
            "date": p.created_at.date().isoformat(),
            "amount": p.amount,
            "title": st.full_name,
            "student_id": st.id,
            "method": method,
            "direction": "in",
            "branch": branches.get(st.branch_id) or "—",
            "category": "new_payment" if is_new else "old_payment",
            "note": p.note,
        })

    # --- Chiqimlar ---
    eq = scope_to_branch(db.query(models.Expense), models.Expense, user).filter(
        models.Expense.date >= start, models.Expense.date <= end
    )
    if branch_id and user.role in tuple(roles.ORG_WIDE_ROLES):
        eq = eq.filter(models.Expense.branch_id == branch_id)

    chiqim = {m: 0.0 for m in roles.PAYMENT_METHODS}
    cat_labels = {k: lbl for k, lbl, _ in roles.EXPENSE_CATEGORY_DEFS}
    for e in eq.all():
        method = getattr(e, "method", None) or "cash"
        if method not in chiqim:
            method = "cash"
        chiqim[method] += e.amount
        rows.append({
            "id": f"e{e.id}",
            "date": e.date.isoformat(),
            "amount": e.amount,
            "title": e.note or cat_labels.get(e.category, e.category),
            "student_id": None,
            "method": method,
            "direction": "out",
            "branch": branches.get(e.branch_id) or "—",
            "category": e.category,
            "note": e.note,
        })

    # 2026-08-12 (Jahongir): "Ustozlar oyligi (avtomatik)" degan
    # PROGNOZ qatori olib tashlandi - cashflow REAL KASSA holatini
    # ko'rsatishi kerak. O'rniga faqat HAQIQATDA BERILGAN ustoz
    # oyliklari (TeacherPayment yozuvlari) chiqim bo'lib tushadi.
    period = _period_key(year, month)
    tp_q = (db.query(models.TeacherPayment, models.Teacher)
            .join(models.Teacher,
                  models.TeacherPayment.teacher_id == models.Teacher.id)
            .filter(models.TeacherPayment.paid_on >= start,
                    models.TeacherPayment.paid_on <= end))
    if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
        tp_q = tp_q.filter(_branch_in(db, user, models.Teacher.branch_id))
    elif branch_id:
        tp_q = tp_q.filter(models.Teacher.branch_id == branch_id)
    for tp, t in tp_q.all():
        m_ = getattr(tp, "method", None) or "cash"
        if m_ not in chiqim:
            m_ = "cash"
        chiqim[m_] += tp.amount or 0
        rows.append({
            "id": f"tp{tp.id}",
            "date": tp.paid_on.isoformat() if tp.paid_on
            else end.isoformat(),
            "amount": tp.amount or 0,
            "title": f"Ustoz oyligi: {t.full_name}",
            "student_id": None,
            "method": m_,
            "direction": "out",
            "branch": branches.get(t.branch_id) or "—",
            "category": "teacher_salary",
            "note": getattr(tp, "note", None),
        })

    rows.sort(key=lambda r: (r["date"], r["id"]))

    def block(d):
        return {**d, "total": sum(d.values())}

    kassa = {m: kirim[m] - chiqim[m] for m in roles.PAYMENT_METHODS}

    return {
        "period": period,
        "kirim": block(kirim),
        "chiqim": block(chiqim),
        "kassa": block(kassa),
        "new_payments": {"count": new_cnt, "amount": new_sum},
        "old_payments": {"count": old_cnt, "amount": old_sum},
        "rows": rows,
    }

@router.get("/api/reports/hr-funnel")
def hr_funnel(
    months: int = 12,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.HR_ACCESS)),
):
    """Ishga olish voronkasi: nomzodlar qaysi bosqichda to'xtab qolyapti."""
    months = max(1, min(months, 36))
    since = date.today() - timedelta(days=int(months * 30.44))
    q = scope_to_branch(db.query(models.Candidate), models.Candidate, user).filter(
        models.Candidate.created_at >= datetime.combine(since, datetime.min.time())
    )
    cands = q.all()
    total = len(cands)
    order = roles.CANDIDATE_FUNNEL
    idx = {k: i for i, k in enumerate(order)}

    rejected = [c for c in cands if c.stage == "rejected"]
    stages = []
    for i, key in enumerate(order):
        # Bu bosqichga YETGANLAR = hozir shu yerda yoki undan oldinga o'tgan
        reached = sum(1 for c in cands
                      if c.stage != "rejected" and idx.get(c.stage, -1) >= i)
        here = sum(1 for c in cands if c.stage == key)
        stages.append({
            "stage": key,
            "label": roles.CANDIDATE_STAGE_LABELS[key],
            "reached": reached,
            "stuck_here": here if key != "hired" else 0,
            "percent": round(reached / total * 100, 1) if total else 0.0,
        })

    # Manba kesimida
    by_source = {}
    for c in cands:
        d = by_source.setdefault(c.source, {"total": 0, "hired": 0})
        d["total"] += 1
        if c.stage == "hired":
            d["hired"] += 1
    sources = [{
        "key": k,
        "label": roles.CANDIDATE_SOURCE_LABELS.get(k, k),
        "total": v["total"], "hired": v["hired"],
        "percent": round(v["hired"] / v["total"] * 100, 1) if v["total"] else 0.0,
    } for k, v in sorted(by_source.items(), key=lambda kv: -kv[1]["total"])]

    hired = [c for c in cands if c.stage == "hired" and c.hired_date and c.created_at]
    avg_days = (round(sum((c.hired_date - c.created_at.date()).days
                          for c in hired) / len(hired), 1) if hired else 0.0)

    vq = scope_to_branch(db.query(models.Vacancy), models.Vacancy, user)
    return {
        "total": total,
        "hired": len(hired),
        "rejected": len(rejected),
        "hire_rate": round(len(hired) / total * 100, 1) if total else 0.0,
        "avg_days_to_hire": avg_days,
        "open_vacancies": vq.filter(models.Vacancy.status == "open").count(),
        "stages": stages,
        "sources": sources,
    }

def _marketing_spend(db: Session, user, start: date, end: date,
                     branch_id=None) -> dict:
    """Kanal kesimida reklama xarajati. Kanal ko'rsatilmagan reklama
    xarajati "other"ga tushadi - shunda umumiy summa hech qachon
    yo'qolmaydi."""
    marketing_cats = [k for k, _, g in roles.EXPENSE_CATEGORY_DEFS
                      if g == "marketing"]
    q = scope_to_branch(db.query(models.Expense), models.Expense, user,
                        branch_id).filter(
        models.Expense.date >= start,
        models.Expense.date <= end,
        models.Expense.category.in_(marketing_cats),
    )
    out = {}
    for e in q.all():
        ch = getattr(e, "channel", None) or "other"
        out[ch] = out.get(ch, 0.0) + e.amount
    return out

@router.get("/api/reports/marketing-funnel")
def marketing_funnel(
    months: int = 6,
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.MARKETING_ACCESS)),
):
    """Kanal bo'yicha voronka: qancha pul ketdi -> qancha lid keldi ->
    qanchasi sinovga keldi -> qanchasi to'lovchi o'quvchiga aylandi.
    Oxirida har bir kanal uchun CAC (bitta mijoz qancha turdi)."""
    # months=0 -> butun davr
    months = 0 if months == 0 else max(1, min(months, 120))
    today = date.today()
    since = (date(2000, 1, 1) if months == 0
             else today - timedelta(days=int(months * 30.44)))
    start = since
    end = today

    spend = _marketing_spend(db, user, start, end, branch_id)

    lq = scope_to_branch(db.query(models.Lead), models.Lead, user, branch_id).filter(
        models.Lead.created_at >= datetime.combine(since, datetime.min.time())
    )
    leads = lq.all()

    order = roles.LEAD_FUNNEL_ORDER
    idx = {k: i for i, k in enumerate(order)}

    # Aylangan lidlarning daromadi - LTV emas, shu paytgacha to'lagani
    conv_ids = [l.converted_student_id for l in leads if l.converted_student_id]
    revenue_by_student = {}
    if conv_ids:
        for sid, total in (db.query(models.Payment.student_id,
                                    func.coalesce(func.sum(models.Payment.amount), 0.0))
                           .filter(models.Payment.kind == "payment",
                                   models.Payment.student_id.in_(conv_ids))
                           .group_by(models.Payment.student_id).all()):
            revenue_by_student[sid] = float(total)

    channels = {}
    for l in leads:
        ch = l.source or "other"
        d = channels.setdefault(ch, {"leads": 0, "trial": 0, "converted": 0,
                                     "rejected": 0, "revenue": 0.0})
        d["leads"] += 1
        pos = idx.get(l.stage, -1)
        if l.stage == "rejected":
            d["rejected"] += 1
        else:
            if pos >= idx["trial_attended"]:
                d["trial"] += 1
            if l.stage == "converted":
                d["converted"] += 1
                d["revenue"] += revenue_by_student.get(l.converted_student_id, 0.0)

    for ch in spend:
        channels.setdefault(ch, {"leads": 0, "trial": 0, "converted": 0,
                                 "rejected": 0, "revenue": 0.0})

    rows = []
    for ch, d in channels.items():
        s = spend.get(ch, 0.0)
        rows.append({
            "channel": ch,
            "label": roles.MARKETING_CHANNEL_LABELS.get(ch, ch),
            "spend": s,
            "leads": d["leads"],
            "trial": d["trial"],
            "converted": d["converted"],
            "rejected": d["rejected"],
            "revenue": round(d["revenue"], 2),
            "conversion": round(d["converted"] / d["leads"] * 100, 1) if d["leads"] else 0.0,
            # CPL - bitta lid qancha turdi, CAC - bitta MIJOZ qancha turdi
            "cpl": round(s / d["leads"], 0) if d["leads"] and s else 0.0,
            "cac": round(s / d["converted"], 0) if d["converted"] and s else 0.0,
            "roi": round((d["revenue"] - s) / s * 100, 1) if s else 0.0,
        })
    rows.sort(key=lambda r: -r["leads"])

    total_spend = sum(spend.values())
    total_leads = sum(d["leads"] for d in channels.values())
    total_conv = sum(d["converted"] for d in channels.values())
    total_rev = sum(d["revenue"] for d in channels.values())

    # Umumiy voronka bosqichlari
    stages = []
    for i, key in enumerate(order):
        reached = sum(1 for l in leads
                      if l.stage != "rejected" and idx.get(l.stage, -1) >= i)
        stages.append({
            "stage": key,
            "label": roles.LEAD_STAGE_LABELS.get(key, key),
            "reached": reached,
            "stuck_here": sum(1 for l in leads if l.stage == key),
            "percent": round(reached / total_leads * 100, 1) if total_leads else 0.0,
        })

    return {
        "months": months,
        "channels": rows,
        "stages": stages,
        "totals": {
            "spend": total_spend,
            "leads": total_leads,
            "converted": total_conv,
            "revenue": round(total_rev, 2),
            "conversion": round(total_conv / total_leads * 100, 1) if total_leads else 0.0,
            "cpl": round(total_spend / total_leads, 0) if total_leads and total_spend else 0.0,
            "cac": round(total_spend / total_conv, 0) if total_conv and total_spend else 0.0,
            "roi": round((total_rev - total_spend) / total_spend * 100, 1) if total_spend else 0.0,
        },
    }

@router.get("/api/analytics/cac")
def analytics_cac(
    months: int = 12,
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FINANCE_ACCESS)),
):
    """Oylar bo'yicha CAC: reklamaga ketgan pul / o'sha oyda BIRINCHI
    marta to'lagan o'quvchilar soni. Pastda LTV/CAC nisbati - 3 dan
    yuqori bo'lsa biznes sog'lom hisoblanadi."""
    if months == 0:
        oldest = db.query(func.min(models.Payment.created_at)).scalar()
        t = date.today()
        first = oldest.date() if oldest else t
        months = max(1, (t.year - first.year) * 12 + (t.month - first.month) + 1)
    months = max(1, min(months, 120))
    today = date.today()

    firsts = _payment_first_dates(db)
    # O'quvchi filiali - filialga bog'langan foydalanuvchi uchun filtr
    sb = {s.id: s.branch_id for s in
          scope_to_branch(db.query(models.Student), models.Student, user, branch_id).all()}

    rows = []
    for back in range(months - 1, -1, -1):
        y, m = _shift_month(today.year, today.month, -back)
        start, end = billing.month_bounds(y, m)
        spend = sum(_marketing_spend(db, user, start, end, branch_id).values())
        new_clients = sum(1 for sid, dt in firsts.items()
                          if sid in sb and start <= dt.date() <= end)
        rows.append({
            "period": _period_key(y, m),
            "spend": spend,
            "new_clients": new_clients,
            "cac": round(spend / new_clients, 0) if new_clients and spend else 0.0,
        })

    total_spend = sum(r["spend"] for r in rows)
    total_new = sum(r["new_clients"] for r in rows)
    cac = round(total_spend / total_new, 0) if total_new and total_spend else 0.0

    # LTV - shu davrda birinchi to'lovini qilganlarning o'rtacha jami to'lovi
    first_start = billing.month_bounds(*[int(x) for x in rows[0]["period"].split("-")])[0]
    cohort = [sid for sid, dt in firsts.items()
              if sid in sb and dt.date() >= first_start]
    ltv = 0.0
    if cohort:
        total = (db.query(func.coalesce(func.sum(models.Payment.amount), 0.0))
                 .filter(models.Payment.kind == "payment",
                         models.Payment.student_id.in_(cohort)).scalar() or 0.0)
        ltv = round(float(total) / len(cohort), 0)

    return {
        "rows": rows,
        "totals": {
            "spend": total_spend,
            "new_clients": total_new,
            "cac": cac,
            "ltv": ltv,
            "ratio": round(ltv / cac, 2) if cac else 0.0,
        },
    }

def _parse_snapshot_date(tok: str):
    """Ikki formatni tushunadi: 2023-01-15 va 15.01.2023."""
    tok = tok.strip()
    try:
        return date.fromisoformat(tok)
    except ValueError:
        pass
    try:
        d, m, y = tok.replace("/", ".").split(".")
        return date(int(y), int(m), int(d))
    except Exception:
        return None

@router.get("/api/stats/history")
def stats_history(db: Session = Depends(get_db),
                  user=Depends(require_role(*roles.FINANCE_ACCESS))):
    """Tarixiy sonlar + bugungi jonli nuqta bitta javobda."""
    rows = (db.query(models.StudentCountSnapshot)
            .order_by(models.StudentCountSnapshot.date).all())
    live = (db.query(models.Student)
            .filter(models.Student.status == "active").count())
    return {
        "rows": [{"id": r.id, "date": r.date.isoformat(),
                  "count": r.count, "note": r.note} for r in rows],
        "today": {"date": roles.local_today().isoformat(), "count": live},
    }

@router.post("/api/stats/history")
def stats_history_add(payload: schemas.SnapshotIn,
                      db: Session = Depends(get_db),
                      user=Depends(require_role(roles.FOUNDER))):
    if payload.count < 0:
        raise HTTPException(400, "Son manfiy bo'lmaydi")
    r = (db.query(models.StudentCountSnapshot)
         .filter(models.StudentCountSnapshot.date == payload.date).first())
    if r:
        # Bir sanaga bitta yozuv: qayta kiritilsa yangilanadi
        r.count = payload.count
        r.note = payload.note or r.note
    else:
        r = models.StudentCountSnapshot(
            date=payload.date, count=payload.count,
            note=payload.note, created_by=user.full_name)
        db.add(r)
    audit.log(db, user, entity="stats", action="update",
              entity_label=str(payload.date), field="student_count",
              new_value=payload.count, note=payload.note)
    db.commit()
    return {"ok": True, "id": r.id}

@router.post("/api/stats/history/bulk")
def stats_history_bulk(payload: schemas.SnapshotBulkIn,
                       db: Session = Depends(get_db),
                       user=Depends(require_role(roles.FOUNDER))):
    """Har qatorda: sana va son (ixtiyoriy izoh). Masalan:
    2023-01-15 480
    01.09.2023 520 yangi o'quv yili"""
    added = updated = 0
    errors = []
    for i, line in enumerate(payload.text.splitlines(), start=1):
        line = line.replace(",", " ").replace(";", " ").strip()
        if not line:
            continue
        parts = line.split()
        d = _parse_snapshot_date(parts[0])
        cnt = None
        if len(parts) >= 2:
            try:
                cnt = int(float(parts[1]))
            except ValueError:
                cnt = None
        if not d or cnt is None or cnt < 0:
            errors.append(f"{i}-qator tushunilmadi: {line[:40]}")
            continue
        note = " ".join(parts[2:]) or None
        r = (db.query(models.StudentCountSnapshot)
             .filter(models.StudentCountSnapshot.date == d).first())
        if r:
            r.count, updated = cnt, updated + 1
            if note:
                r.note = note
        else:
            db.add(models.StudentCountSnapshot(
                date=d, count=cnt, note=note, created_by=user.full_name))
            added += 1
    audit.log(db, user, entity="stats", action="import",
              entity_label="tarixiy sonlar",
              note=f"qo'shildi {added}, yangilandi {updated}")
    db.commit()
    return {"ok": True, "added": added, "updated": updated,
            "errors": errors}

@router.delete("/api/stats/history/{sid}")
def stats_history_delete(sid: int, db: Session = Depends(get_db),
                         user=Depends(require_role(roles.FOUNDER))):
    r = db.query(models.StudentCountSnapshot).get(sid)
    if not r:
        raise HTTPException(404, "Yozuv topilmadi")
    audit.log(db, user, entity="stats", action="delete",
              entity_label=r.date.isoformat(), old_value=r.count)
    db.delete(r)
    db.commit()
    return {"ok": True}

def _today_bounds():
    """Bugungi kunning UTC chegaralari.

    Yozuvlar bazaga UTC vaqtida tushadi, kun esa Toshkent vaqtida
    boshlanadi. Shu farq hisobga olinmasa, tunda (mahalliy 00:00–05:00)
    qabul qilingan to'lov "bugungi tushum"ga tushmay qoladi — asoschi
    ertalab panelni ochib nol ko'radi."""
    t = roles.local_today()
    off = timedelta(hours=roles.TIMEZONE_OFFSET_HOURS)
    return (datetime.combine(t, datetime.min.time()) - off,
            datetime.combine(t, datetime.max.time()) - off)

@router.get("/api/ceo/today")
def ceo_today(
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.PROFIT_VIEW)),
):
    """Bugungi kun bir ekranda: pul kirdimi, chiqdimi, kim keldi, kim
    ketdi, nima e'tibor talab qiladi.

    Maqsad - raqamlarni sanab chiqish emas, balki bugun nima qilish
    kerakligini ko'rsatish. Shuning uchun oxirida "kritik
    ogohlantirishlar" bo'limi bor."""
    today = date.today()
    d0, d1 = _today_bounds()
    org_wide = user.role in tuple(roles.ORG_WIDE_ROLES)
    my_branch = None if org_wide else user.branch_id

    def scope_students(q):
        return q.filter(models.Student.branch_id == my_branch) if my_branch else q

    # ---- Pul ----
    pq = (db.query(models.Payment)
          .join(models.Student, models.Payment.student_id == models.Student.id)
          .filter(models.Payment.kind == "payment",
                  models.Payment.created_at >= d0,
                  models.Payment.created_at <= d1))
    pq = scope_students(pq)
    payments = pq.all()
    income = sum(p.amount for p in payments)

    eq = db.query(models.Expense).filter(models.Expense.date == today)
    if my_branch:
        eq = eq.filter(models.Expense.branch_id == my_branch)
    expense = sum(e.amount for e in eq.all())

    # ---- Lidlar va sotuv ----
    lq = db.query(models.Lead).filter(models.Lead.created_at >= d0,
                                      models.Lead.created_at <= d1)
    if my_branch:
        lq = lq.filter(models.Lead.branch_id == my_branch)
    new_leads = lq.count()

    tq = db.query(models.Lead).filter(models.Lead.updated_at >= d0,
                                      models.Lead.updated_at <= d1,
                                      models.Lead.stage != "new")
    if my_branch:
        tq = tq.filter(models.Lead.branch_id == my_branch)
    touched_leads = tq.count()

    # Bugun BIRINCHI marta to'lagan o'quvchilar - haqiqiy sotuv
    firsts = _payment_first_dates(db)
    scoped_ids = {s.id for s in scope_students(db.query(models.Student)).all()}
    sales = sum(1 for sid, dt in firsts.items()
                if sid in scoped_ids and dt.date() == today)

    # ---- O'quvchilar ----
    all_students = scope_students(db.query(models.Student)).all()
    active = [s for s in all_students if s.status == "active"]
    debtors = []
    for s in active:
        bal = student_balance(db, s.id)
        if bal < 0:
            debtors.append({"id": s.id, "public_id": s.public_id,
                            "full_name": s.full_name, "balance": bal,
                            "group": s.group.name if s.group else None})
    debtors.sort(key=lambda d: d["balance"])
    total_debt = sum(d["balance"] for d in debtors)

    left_today = [{"id": s.id, "full_name": s.full_name,
                   "group": s.group.name if s.group else None}
                  for s in all_students if s.left_date == today]

    # ---- Davomat (bugungi darslar) ----
    lessons_today = (db.query(models.Lesson)
                     .join(models.Group)
                     .filter(models.Lesson.date == today))
    if my_branch:
        lessons_today = lessons_today.filter(models.Group.branch_id == my_branch)
    lessons_today = lessons_today.all()
    lesson_ids = [l.id for l in lessons_today]
    att_present = att_total = 0
    if lesson_ids:
        for a in (db.query(models.Attendance)
                  .filter(models.Attendance.lesson_id.in_(lesson_ids)).all()):
            att_total += 1
            att_present += 1 if a.present else 0
    unmarked = sum(1 for l in lessons_today if not l.held)

    # ---- Muammoli guruhlar ----
    # To'lishi past (o'quvchi kam) yoki davomat past guruhlar.
    gq = db.query(models.Group)
    if my_branch:
        gq = gq.filter(models.Group.branch_id == my_branch)
    problem_groups = []
    month_start, month_end = billing.month_bounds(today.year, today.month)
    for g in gq.all():
        n = sum(1 for s in all_students
                if s.group_id == g.id and s.status == "active")
        gl = [l for l in db.query(models.Lesson).filter(
            models.Lesson.group_id == g.id,
            models.Lesson.date >= month_start,
            models.Lesson.date <= month_end,
            models.Lesson.held == 1).all()]
        pres = tot = 0
        if gl:
            for a in (db.query(models.Attendance)
                      .filter(models.Attendance.lesson_id.in_([x.id for x in gl]))
                      .all()):
                tot += 1
                pres += 1 if a.present else 0
        att_pct = round(pres / tot * 100, 1) if tot else None
        reasons = []
        if n and n < 6:
            reasons.append(f"atigi {n} o'quvchi")
        if att_pct is not None and att_pct < 70:
            reasons.append(f"davomat {att_pct}%")
        if reasons:
            problem_groups.append({
                "id": g.id, "name": g.name,
                "teacher": g.teacher.full_name if g.teacher else None,
                "students": n, "attendance": att_pct,
                "reasons": reasons,
            })
    problem_groups.sort(key=lambda g: (g["students"], g["attendance"] or 0))

    # ---- Shikoyatlar ----
    cq = db.query(models.Complaint).filter(models.Complaint.status != "closed")
    if my_branch:
        cq = cq.filter(models.Complaint.branch_id == my_branch)
    open_complaints = cq.all()

    # ---- KRITIK OGOHLANTIRISHLAR ----
    # Bu ro'yxat - panelning eng muhim qismi. Har bir qator "bugun
    # nimadir qilish kerak" degani.
    alerts = []

    def alert(level, title, detail, link=None):
        alerts.append({"level": level, "title": title,
                       "detail": detail, "link": link})

    if total_debt < 0:
        big = [d for d in debtors if d["balance"] <= -500_000]
        if big:
            alert("high", f"{len(big)} ta o'quvchida katta qarz",
                  f"Jami {formatless(total_debt)} so'm. Eng kattasi: "
                  f"{big[0]['full_name']} ({formatless(big[0]['balance'])} so'm)",
                  "/students")
        elif debtors:
            alert("normal", f"{len(debtors)} ta qarzdor",
                  f"Jami {formatless(total_debt)} so'm", "/students")

    old_complaints = [c for c in open_complaints
                      if c.created_at
                      and (today - c.created_at.date()).days >= 3]
    if old_complaints:
        alert("high", f"{len(old_complaints)} ta shikoyat 3 kundan beri ochiq",
              old_complaints[0].subject, "/complaints")
    elif open_complaints:
        alert("normal", f"{len(open_complaints)} ta ochiq shikoyat",
              open_complaints[0].subject, "/complaints")

    if unmarked:
        alert("normal", f"{unmarked} ta guruhda bugungi yoqlama qo'yilmagan",
              "Yoqlama qo'yilmasa dars pulga ham, ustoz ish haqiga ham "
              "kirmaydi", "/groups")

    if left_today:
        alert("high", f"Bugun {len(left_today)} o'quvchi ketdi",
              ", ".join(x["full_name"] for x in left_today[:3]), "/students")

    if problem_groups:
        g = problem_groups[0]
        alert("normal", f"{len(problem_groups)} ta muammoli guruh",
              f"{g['name']} — {', '.join(g['reasons'])}", "/groups")

    if new_leads and touched_leads == 0:
        alert("high", f"{new_leads} ta yangi lid, hech biriga bog'lanilmagan",
              "Birinchi soatda bog'lanish konversiyani keskin oshiradi",
              "/leads")

    order = {"high": 0, "normal": 1, "low": 2}
    alerts.sort(key=lambda a: order.get(a["level"], 3))

    return {
        "date": today.isoformat(),
        "scope": "Barcha filiallar" if org_wide else (
            db.query(models.Branch).get(my_branch).name
            if my_branch and db.query(models.Branch).get(my_branch) else "Filial"),
        "money": {
            "income": income,
            "expense": expense,
            "net": income - expense,
            "payment_count": len(payments),
        },
        "sales": {
            "new_leads": new_leads,
            "touched_leads": touched_leads,
            "sales": sales,
        },
        "students": {
            "active": len(active),
            "debtors": len(debtors),
            "total_debt": total_debt,
            "left_today": len(left_today),
            "left_list": left_today[:10],
            "top_debtors": debtors[:10],
        },
        "attendance": {
            "lessons_today": len(lessons_today),
            "unmarked": unmarked,
            "present": att_present,
            "marked": att_total,
            "percent": round(att_present / att_total * 100, 1) if att_total else None,
        },
        "problem_groups": problem_groups[:10],
        "complaints": {
            "open": len(open_complaints),
            "overdue": len(old_complaints),
            "list": [_complaint_out(c) for c in open_complaints[:5]],
        },
        "alerts": alerts,
    }

def formatless(v: float) -> str:
    """Ogohlantirish matni uchun qisqa son: 1 234 567 -> "1.2 mln"."""
    v = abs(v)
    if v >= 1_000_000:
        return f"{v / 1_000_000:.1f} mln"
    if v >= 1_000:
        return f"{round(v / 1_000)} ming"
    return str(int(v))

@router.get("/api/reports/family-discounts")
def family_discounts(
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FINANCE_ACCESS)),
):
    """Oilaviy chegirma olayotgan oilalar. Chegirma avtomat
    hisoblanadi, shuning uchun bu ro'yxat har doim haqiqatga mos."""
    parents = scope_to_branch(db.query(models.Parent), models.Parent, user).all()
    kids = {}
    if parents:
        for s in (db.query(models.Student)
                  .filter(models.Student.parent_id.in_([p.id for p in parents]))
                  .all()):
            kids.setdefault(s.parent_id, []).append(s)

    rows = []
    for p in parents:
        ch = kids.get(p.id, [])
        active = [c for c in ch if c.status == "active"]
        if len(active) < roles.FAMILY_DISCOUNT_MIN_CHILDREN:
            continue
        saved = 0.0
        for c in active:
            fee = c.group.monthly_fee if c.group else 0.0
            saved += fee * roles.FAMILY_DISCOUNT_PERCENT / 100
        rows.append({
            "parent_id": p.id, "public_id": p.public_id,
            "parent": p.full_name, "phone": p.phone,
            "children": [{"id": c.id, "full_name": c.full_name,
                          "status": c.status,
                          "group": c.group.name if c.group else None}
                         for c in ch],
            "active_children": len(active),
            "discount_percent": roles.FAMILY_DISCOUNT_PERCENT,
            "monthly_saved": round(saved, 2),
        })
    rows.sort(key=lambda r: -r["active_children"])
    return {
        "percent": roles.FAMILY_DISCOUNT_PERCENT,
        "min_children": roles.FAMILY_DISCOUNT_MIN_CHILDREN,
        "families": len(rows),
        "monthly_total": round(sum(r["monthly_saved"] for r in rows), 2),
        "rows": rows,
    }

@router.get("/api/reports/marketing-journey")
def marketing_journey(
    months: int = 6,
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.MARKETING_ACCESS)),
):
    """To'liq yo'l: reklama ko'rildi -> bosildi -> murojaat -> bog'lanildi
    -> testga keldi -> sotildi -> 1 oy qoldi -> 3 oy qoldi -> sertifikat.

    Birinchi ikki bosqich reklama kabinetidan qo'lda kiritiladi
    (Marketing -> Reklama ko'rsatkichlari), qolganlari tizimning o'z
    ma'lumotidan avtomat hisoblanadi."""
    months = 0 if months == 0 else max(1, min(months, 120))
    today = date.today()
    since = (date(2000, 1, 1) if months == 0
             else today - timedelta(days=int(months * 30.44)))

    adq = scope_to_branch(db.query(models.AdStat), models.AdStat, user, branch_id)
    if months:
        periods = []
        for back in range(months - 1, -1, -1):
            y, m = _shift_month(today.year, today.month, -back)
            periods.append(_period_key(y, m))
        adq = adq.filter(models.AdStat.period.in_(periods))
    ads = adq.all()

    leads = scope_to_branch(db.query(models.Lead), models.Lead, user, branch_id).filter(
        models.Lead.created_at >= datetime.combine(since, datetime.min.time())
    ).all()

    order = roles.LEAD_FUNNEL_ORDER
    idx = {k: i for i, k in enumerate(order)}

    conv_ids = [l.converted_student_id for l in leads if l.converted_student_id]
    firsts = _payment_first_dates(db)
    students = {}
    if conv_ids:
        students = {s.id: s for s in db.query(models.Student)
                    .filter(models.Student.id.in_(conv_ids)).all()}
    certs = set()
    if conv_ids:
        certs = {c.student_id for c in db.query(models.Certificate)
                 .filter(models.Certificate.student_id.in_(conv_ids)).all()}

    def survived(sid: int, need_months: float) -> bool:
        """Birinchi to'lovdan keyin shuncha oy qoldimi.
        Hali o'qiyotgan bo'lsa - bugungi kungacha; ketgan bo'lsa -
        ketgan kunigacha hisoblanadi."""
        dt = firsts.get(sid)
        st = students.get(sid)
        if not dt or not st:
            return False
        end = st.left_date or today
        return _months_between(dt.date(), end) >= need_months

    def build(ch_leads, ch_ads):
        imp = sum(a.impressions for a in ch_ads)
        clk = sum(a.clicks for a in ch_ads)
        n_leads = len(ch_leads)
        contacted = sum(1 for l in ch_leads
                        if l.stage != "rejected"
                        and idx.get(l.stage, -1) >= idx["contacted"])
        trial = sum(1 for l in ch_leads
                    if l.stage != "rejected"
                    and idx.get(l.stage, -1) >= idx["trial_attended"])
        sold_ids = [l.converted_student_id for l in ch_leads
                    if l.stage == "converted" and l.converted_student_id]
        sold = len(sold_ids)
        m1 = sum(1 for sid in sold_ids if survived(sid, 1))
        m3 = sum(1 for sid in sold_ids if survived(sid, 3))
        cert = sum(1 for sid in sold_ids if sid in certs)
        return {"impressions": imp, "clicks": clk, "leads": n_leads,
                "contacted": contacted, "trial": trial, "sold": sold,
                "month1": m1, "month3": m3, "certificate": cert}

    totals = build(leads, ads)

    # Bosqichlar: har birida oldingisiga nisbatan o'tish foizi
    stages = []
    prev = None
    for key, label, source in roles.MARKETING_JOURNEY:
        v = totals[key]
        stages.append({
            "key": key, "label": label, "source": source,
            "count": v,
            # Oldingi bosqichdan qanchasi o'tdi - eng muhim raqam
            "step_percent": round(v / prev * 100, 1) if prev else None,
            "of_leads": round(v / totals["leads"] * 100, 1)
                        if totals["leads"] else None,
            "lost": max(0, prev - v) if prev is not None else 0,
        })
        prev = v if v else prev

    # Kanal kesimida
    by_channel = {}
    for l in leads:
        by_channel.setdefault(l.source or "other", {"leads": [], "ads": []})
        by_channel[l.source or "other"]["leads"].append(l)
    for a in ads:
        by_channel.setdefault(a.channel, {"leads": [], "ads": []})
        by_channel[a.channel]["ads"].append(a)

    channels = []
    for ch, d in by_channel.items():
        b = build(d["leads"], d["ads"])
        channels.append({
            "channel": ch,
            "label": roles.MARKETING_CHANNEL_LABELS.get(ch, ch),
            **b,
            "ctr": round(b["clicks"] / b["impressions"] * 100, 2)
                   if b["impressions"] else None,
            "click_to_lead": round(b["leads"] / b["clicks"] * 100, 1)
                             if b["clicks"] else None,
            "lead_to_sale": round(b["sold"] / b["leads"] * 100, 1)
                            if b["leads"] else 0.0,
            "retention_1m": round(b["month1"] / b["sold"] * 100, 1)
                            if b["sold"] else None,
            "retention_3m": round(b["month3"] / b["sold"] * 100, 1)
                            if b["sold"] else None,
        })
    channels.sort(key=lambda c: -c["leads"])

    # Eng katta yo'qotish qayerda
    worst = None
    for st in stages[1:]:
        if st["step_percent"] is not None and st["lost"] > 0:
            if worst is None or st["lost"] > worst["lost"]:
                worst = st

    return {
        "months": months,
        "stages": stages,
        "channels": channels,
        "totals": totals,
        "worst_stage": worst,
        "has_ad_data": totals["impressions"] > 0,
    }

@router.get("/api/ceo/branches")
def ceo_branches(
    months: int = 1,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.PROFIT_VIEW)),
):
    """Filiallarni yonma-yon solishtirish.

    Asoschi uchun eng muhim ko'rinish: qaysi filial ko'proq pul
    keltiryapti, qayerda o'quvchi ko'p ketyapti, qayerda guruhlar
    bo'sh turibdi. Har bir ustun bo'yicha eng yaxshi va eng yomon
    filial belgilanadi."""
    months = max(1, min(months, 24))
    today = date.today()
    y, m = _shift_month(today.year, today.month, -(months - 1))
    start, _e = billing.month_bounds(y, m)
    _s, end = billing.month_bounds(today.year, today.month)
    d0, d1 = _utc_window(start, end)

    allowed = _branch_scope_ids(db, user, None)
    bq = db.query(models.Branch)
    if allowed:
        bq = bq.filter(models.Branch.id.in_(allowed))
    branches = bq.order_by(models.Branch.name).all()

    students = db.query(models.Student).all()
    groups = db.query(models.Group).all()
    rooms = {r.id: r for r in db.query(models.Room).all()}
    firsts = _payment_first_dates(db)

    pays = (db.query(models.Payment, models.Student)
            .join(models.Student, models.Payment.student_id == models.Student.id)
            .filter(models.Payment.kind == "payment",
                    models.Payment.created_at >= d0,
                    models.Payment.created_at <= d1).all())
    exps = (db.query(models.Expense)
            .filter(models.Expense.date >= start,
                    models.Expense.date <= end).all())
    leads = (db.query(models.Lead)
             .filter(models.Lead.created_at >= d0).all())
    payouts = {}
    for p in db.query(models.TeacherPayout).all():
        if p.period and start.isoformat()[:7] <= p.period <= end.isoformat()[:7]:
            g = next((x for x in groups if x.id == p.group_id), None)
            if g:
                payouts[g.branch_id] = payouts.get(g.branch_id, 0.0) + (p.amount or 0)

    rows = []
    for b in branches:
        bs = [s for s in students if s.branch_id == b.id]
        active = [s for s in bs if s.status == "active"]
        trial = [s for s in bs if s.status == "trial"]
        left = [s for s in bs if s.left_date and start <= s.left_date <= end]
        income = sum(p.amount for p, st in pays if st.branch_id == b.id)
        expense = sum(e.amount for e in exps if e.branch_id == b.id)
        payroll = payouts.get(b.id, 0.0)
        outflow = expense + payroll
        profit = income - outflow

        bg = [g for g in groups if g.branch_id == b.id]
        cap = seats = 0
        for g in bg:
            c = _group_capacity(g, rooms)
            if c:
                cap += c
                seats += sum(1 for s in active if s.group_id == g.id)
        fill = round(seats / cap * 100, 1) if cap else None

        bl = [l for l in leads if l.branch_id == b.id]
        conv = sum(1 for l in bl if l.stage == "converted")
        new_clients = sum(1 for s in bs
                          if s.id in firsts and start <= firsts[s.id].date() <= end)

        debt = sum(min(0.0, student_balance(db, s.id)) for s in active)

        rows.append({
            "branch_id": b.id, "branch": b.name,
            "active": len(active), "trial": len(trial), "left": len(left),
            "groups": len(bg),
            "income": round(income, 2),
            "expense": round(outflow, 2),
            "profit": round(profit, 2),
            "margin": round(profit / income * 100, 1) if income else 0.0,
            "arpu": round(income / len(active), 0) if active else 0.0,
            "fill": fill,
            "leads": len(bl), "converted": conv,
            "conversion": round(conv / len(bl) * 100, 1) if bl else 0.0,
            "new_clients": new_clients,
            "debt": round(abs(debt), 2),
            "churn": round(len(left) / (len(active) + len(left)) * 100, 1)
                     if (active or left) else 0.0,
        })

    # Har bir ustunda eng yaxshi va eng yomon filial - solishtirish
    # oson bo'lishi uchun.
    def extremes(key, higher_is_better=True):
        vals = [(r["branch_id"], r[key]) for r in rows if r[key] is not None]
        if len(vals) < 2:
            return None, None
        best = (max if higher_is_better else min)(vals, key=lambda x: x[1])
        worst = (min if higher_is_better else max)(vals, key=lambda x: x[1])
        return best[0], worst[0]

    highlight = {}
    for key, better in [("income", True), ("profit", True), ("margin", True),
                        ("fill", True), ("conversion", True), ("arpu", True),
                        ("churn", False), ("debt", False), ("left", False)]:
        b_, w_ = extremes(key, better)
        highlight[key] = {"best": b_, "worst": w_}

    totals = {
        "active": sum(r["active"] for r in rows),
        "trial": sum(r["trial"] for r in rows),
        "left": sum(r["left"] for r in rows),
        "groups": sum(r["groups"] for r in rows),
        "income": round(sum(r["income"] for r in rows), 2),
        "expense": round(sum(r["expense"] for r in rows), 2),
        "profit": round(sum(r["profit"] for r in rows), 2),
        "debt": round(sum(r["debt"] for r in rows), 2),
        "leads": sum(r["leads"] for r in rows),
        "converted": sum(r["converted"] for r in rows),
        "new_clients": sum(r["new_clients"] for r in rows),
    }
    totals["margin"] = (round(totals["profit"] / totals["income"] * 100, 1)
                        if totals["income"] else 0.0)

    rows.sort(key=lambda r: -r["profit"])
    return {"months": months, "period": f"{start.isoformat()} — {end.isoformat()}",
            "rows": rows, "totals": totals, "highlight": highlight}

def _rating_weights(db: Session) -> dict:
    """Og'irliklar. Bitta filialda saqlanadi (hammasi uchun bir xil),
    bo'sh bo'lsa standart taqsimot."""
    b = db.query(models.Branch).filter(
        models.Branch.rating_weights.isnot(None)).first()
    if b and b.rating_weights:
        try:
            w = json.loads(b.rating_weights)
            if isinstance(w, dict) and w:
                return {k: float(w.get(k, v))
                        for k, v in roles.BRANCH_RATING_DEFAULT.items()}
        except Exception:
            pass
    return dict(roles.BRANCH_RATING_DEFAULT)

def _scale(value, lo, hi, higher_is_better=True) -> float:
    """Qiymatni 0-100 shkalaga o'tkazadi. lo va hi - kutilgan chegaralar."""
    if value is None:
        return 50.0     # ma'lumot yo'q - o'rtacha deb olamiz
    if hi == lo:
        return 50.0
    x = (value - lo) / (hi - lo) * 100
    x = max(0.0, min(100.0, x))
    return x if higher_is_better else 100.0 - x

@router.get("/api/ceo/branch-rating")
def branch_rating(
    months: int = 3,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.PROFIT_VIEW)),
):
    """Filiallar reytingi. Har bir o'lchov 0-100 balga keltiriladi,
    keyin og'irligiga ko'paytiriladi."""
    base = ceo_branches(months=months, db=db, user=user)
    weights = _rating_weights(db)
    total_w = sum(weights.values()) or 1

    today = date.today()
    y, m = _shift_month(today.year, today.month, -(max(1, months) - 1))
    start, _e = billing.month_bounds(y, m)
    _s, end = billing.month_bounds(today.year, today.month)

    # Akademik natija: filial bo'yicha imtihon o'rtachasi
    academic = {}
    exams = (db.query(models.Exam, models.Group)
             .join(models.Group, models.Exam.group_id == models.Group.id)
             .filter(models.Exam.date >= start, models.Exam.date <= end).all())
    ex_ids = {e.id: g.branch_id for e, g in exams}
    if ex_ids:
        for r in db.query(models.ExamResult).filter(
                models.ExamResult.exam_id.in_(list(ex_ids))).all():
            if r.absent or r.percent is None:
                continue
            bid = ex_ids.get(r.exam_id)
            academic.setdefault(bid, []).append(r.percent)

    # Ota-onalar mamnunligi: shikoyatlar soni (kam bo'lsa yaxshi)
    complaints = {}
    for c in db.query(models.Complaint).all():
        if c.created_at and c.created_at.date() >= start:
            complaints[c.branch_id] = complaints.get(c.branch_id, 0) + 1

    # Operatsion intizom: dars kunlari/vaqti belgilanmagan guruhlar va
    # yopilmagan vazifalar
    sloppy = {}
    for g in db.query(models.Group).all():
        if not g.lesson_days or not g.lesson_time:
            sloppy[g.branch_id] = sloppy.get(g.branch_id, 0) + 1
    late_tasks = {}
    for t in db.query(models.Task).filter(
            ~models.Task.status.in_(roles.TASK_CLOSED)).all():
        if t.deadline and t.deadline < today:
            late_tasks[t.branch_id] = late_tasks.get(t.branch_id, 0) + 1

    rows = []
    for r in base["rows"]:
        bid = r["branch_id"]
        marks = academic.get(bid, [])
        acad = round(sum(marks) / len(marks), 1) if marks else None
        n_active = r["active"] or 1

        # Har bir o'lchov 0-100 ballga
        scores = {
            # Rentabellik -20%..+40% oralig'ida baholanadi
            "finance": _scale(r["margin"], -20, 40),
            # Churn 0..20% - kam bo'lsa yaxshi
            "retention": _scale(r["churn"], 0, 20, higher_is_better=False),
            # Konversiya 0..50%
            "sales": _scale(r["conversion"], 0, 50),
            # Imtihon o'rtachasi 50..90%
            "academic": _scale(acad, 50, 90),
            # Bir o'quvchiga to'g'ri keladigan qarz 0..300 ming
            "debt": _scale(r["debt"] / n_active, 0, 300000,
                           higher_is_better=False),
            # 100 o'quvchiga shikoyat 0..10 ta
            "parents": _scale(complaints.get(bid, 0) / n_active * 100, 0, 10,
                              higher_is_better=False),
            # Tartibsizlik: to'ldirilmagan guruh + kechikkan vazifa
            "discipline": _scale(
                sloppy.get(bid, 0) + late_tasks.get(bid, 0), 0, 10,
                higher_is_better=False),
        }
        total = sum(scores[k] * weights.get(k, 0) for k in scores) / total_w
        key, label = roles.branch_grade(total)
        rows.append({
            "branch_id": bid,
            "branch": r["branch"],
            "score": round(total, 1),
            "grade": key,
            "grade_label": label,
            "scores": {k: round(v, 1) for k, v in scores.items()},
            "raw": {
                "margin": r["margin"], "churn": r["churn"],
                "conversion": r["conversion"], "academic": acad,
                "debt_per_student": round(r["debt"] / n_active),
                "complaints": complaints.get(bid, 0),
                "issues": sloppy.get(bid, 0) + late_tasks.get(bid, 0),
                "active": r["active"], "income": r["income"],
                "profit": r["profit"],
            },
        })
    rows.sort(key=lambda x: -x["score"])
    for i, r in enumerate(rows, 1):
        r["rank"] = i

    return {
        "months": months,
        "period": base["period"],
        "rows": rows,
        "weights": weights,
        "dimensions": [{"key": k, "label": lbl, "weight": weights.get(k, w)}
                       for k, lbl, w in roles.BRANCH_RATING_WEIGHTS],
        "grades": [{"key": k, "label": lbl, "min": lim}
                   for lim, k, lbl in roles.BRANCH_GRADES],
    }

@router.put("/api/ceo/branch-rating/weights")
def set_rating_weights(
    payload: dict,
    db: Session = Depends(get_db),
    user=Depends(require_role(roles.FOUNDER)),
):
    """Og'irliklarni o'zgartirish. Strategiya o'zgarsa - foizlar ham."""
    w = {}
    for k in roles.BRANCH_RATING_DEFAULT:
        try:
            w[k] = max(0.0, float(payload.get(k, roles.BRANCH_RATING_DEFAULT[k])))
        except Exception:
            w[k] = float(roles.BRANCH_RATING_DEFAULT[k])
    if sum(w.values()) <= 0:
        raise HTTPException(400, "Og'irliklar yig'indisi 0 bo'lishi mumkin emas")
    for b in db.query(models.Branch).all():
        b.rating_weights = json.dumps(w)
    db.commit()
    audit.log(db, user, entity="branch", action="update", entity_id=0,
              entity_label="Filial reytingi",
              field="Og'irliklar", new_value=json.dumps(w))
    db.commit()
    return {"weights": w}

@router.get("/api/analytics/geography")
def analytics_geography(
    months: int = 12,
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.LEAD_ACCESS)),
):
    """Qaysi mahalladan va qaysi maktabdan ko'proq o'quvchi kelyapti.

    Reklamani qayerga qo'yish kerakligini shu ko'rsatadi: eng ko'p
    lid keladigan mahalla emas, eng ko'p O'QUVCHIGA aylanadigan
    mahalla muhim."""
    since = (date(2000, 1, 1) if months == 0
             else date.today() - timedelta(days=int(max(1, months) * 30.44)))
    lq = scope_to_branch(db.query(models.Lead), models.Lead, user,
                         branch_id).filter(
        models.Lead.created_at >= datetime.combine(since, datetime.min.time()))
    leads = lq.all()

    def agg(attr: str, known: list):
        acc = {}
        for l in leads:
            v = (getattr(l, attr) or "").strip()
            key = v if v else "—"
            d = acc.setdefault(key, {"leads": 0, "converted": 0})
            d["leads"] += 1
            if l.stage == "converted":
                d["converted"] += 1
        rows = [{
            "name": k, "leads": v["leads"], "converted": v["converted"],
            "conversion": round(v["converted"] / v["leads"] * 100, 1)
                          if v["leads"] else 0.0,
            "known": k in known,
        } for k, v in acc.items()]
        rows.sort(key=lambda r: (-r["converted"], -r["leads"]))
        return rows

    bname = None
    bid = branch_id or user.branch_id
    if bid:
        b = db.query(models.Branch).get(bid)
        bname = b.name if b else None

    areas = agg("address", roles.areas_for_branch(bname))
    schools = agg("school", roles.SCHOOLS)

    return {
        "months": months,
        "total_leads": len(leads),
        "areas": areas,
        "schools": schools,
        "top_area": areas[0] if areas and areas[0]["name"] != "—" else None,
        "top_school": schools[0] if schools and schools[0]["name"] != "—" else None,
        # Ro'yxatdan tanlanmagan, qo'lda yozilgan qiymatlar soni
        "free_text_areas": sum(1 for a in areas if not a["known"] and a["name"] != "—"),
        "free_text_schools": sum(1 for s in schools if not s["known"] and s["name"] != "—"),
    }

def _overhead_per_student_month(db: Session, user, branch_id=None) -> float:
    """Bitta o'quvchining bir oyiga to'g'ri keladigan umumiy xarajat
    (ustoz haqidan tashqari). Oxirgi 12 oyning o'rtachasi."""
    today = date.today()
    y, m = _shift_month(today.year, today.month, -11)
    start, _e = billing.month_bounds(y, m)
    _s, end = billing.month_bounds(today.year, today.month)

    eq = db.query(models.Expense).filter(models.Expense.date >= start,
                                         models.Expense.date <= end)
    if branch_id:
        eq = eq.filter(models.Expense.branch_id == branch_id)
    elif user and user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
        eq = eq.filter(_branch_in(db, user, models.Expense.branch_id))
    total = sum(e.amount or 0 for e in eq.all())

    sq = scope_to_branch(db.query(models.Student), models.Student,
                         user, branch_id) if user else db.query(models.Student)
    active = sq.filter(models.Student.status == "active").count() or 1
    months = 12
    return round(total / months / active, 2)

def _teacher_cost_for_student(db: Session, s: models.Student,
                              groups: dict) -> float:
    """Shu o'quvchi uchun ustozga to'langan pul. Guruhning stavkasi
    va o'quvchi necha oy o'qiganidan chiqadi."""
    g = groups.get(s.group_id)
    if not g:
        return 0.0
    rate = g.teacher_rate_per_student or 0
    months = _months_between(s.enrolled_date or date.today(),
                             s.left_date or date.today())
    return round(rate * months, 2)

@router.get("/api/analytics/ltv")
def analytics_ltv(
    dimension: str = "overall",
    months: int = 24,
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.LTV_ACCESS)),
):
    """LTV to'liq tahlili.

    VAQT LTV: o'quvchi o'rtacha necha oy qoladi.
    PUL LTV:  o'rtacha qancha to'laydi va qancha sof foyda qoldiradi.

    Kesim: butun markaz / filial / ustoz / fan / guruh."""
    if dimension not in roles.LTV_DIMENSION_LABELS:
        raise HTTPException(400, "Noto'g'ri kesim")

    today = date.today()
    students = scope_to_branch(db.query(models.Student), models.Student,
                               user, branch_id).all()
    if not students:
        return {"dimension": dimension, "rows": [], "overall": None,
                "dimensions": [{"key": k, "label": l}
                               for k, l in roles.LTV_DIMENSIONS]}

    paid = _student_payments(db)
    groups = {g.id: g for g in db.query(models.Group).all()}
    teachers = {t.id: t for t in db.query(models.Teacher).all()}
    branches = {b.id: b for b in db.query(models.Branch).all()}
    overhead = _overhead_per_student_month(db, user, branch_id)

    def bucket_for(s):
        if dimension == "overall":
            return "all", "Butun o'quv markaz"
        if dimension == "branch":
            k = s.branch_id
            return str(k), (branches[k].name if k in branches
                            else "Filialsiz")
        if dimension == "group":
            k = s.group_id
            return str(k), (groups[k].name if k in groups else "Guruhsiz")
        if dimension == "subject":
            g = groups.get(s.group_id)
            k = g.subject if g else None
            return str(k), (roles.SUBJECT_LABELS.get(k or "", None)
                            or "Fan belgilanmagan")
        g = groups.get(s.group_id)
        k = g.teacher_id if g else None
        return str(k), (teachers[k].full_name if k in teachers
                        else "Ustoz biriktirilmagan")

    buckets: dict = {}
    for s in students:
        key, label = bucket_for(s)
        b = buckets.setdefault(key, {
            "key": key, "label": label,
            "students": 0, "active": 0, "left": 0,
            "months_sum": 0.0, "revenue": 0.0, "profit": 0.0,
            "payments": 0, "finished_months": [],
        })
        span = _months_between(s.enrolled_date or today,
                               s.left_date or today)
        rev = paid.get(s.id, {}).get("total", 0.0)
        t_cost = _teacher_cost_for_student(db, s, groups)
        profit = rev - t_cost - overhead * span

        b["students"] += 1
        b["months_sum"] += span
        b["revenue"] += rev
        b["profit"] += profit
        b["payments"] += paid.get(s.id, {}).get("count", 0)
        if s.left_date:
            b["left"] += 1
            b["finished_months"].append(span)
        elif s.status == "active":
            b["active"] += 1

    rows = []
    for b in buckets.values():
        n = b["students"] or 1
        fin = b["finished_months"]
        rows.append({
            "key": b["key"],
            "label": b["label"],
            "students": b["students"],
            "active": b["active"],
            "left": b["left"],
            # --- VAQT LTV ---
            "avg_months": round(b["months_sum"] / n, 1),
            # Faqat KETGANLAR bo'yicha - bu haqiqiy "umr", hali
            # o'qiyotganlar buni pasaytirmaydi
            "finished_avg_months": (round(sum(fin) / len(fin), 1)
                                    if fin else None),
            "longest_months": round(max(fin), 1) if fin else None,
            # --- PUL LTV ---
            "avg_revenue": round(b["revenue"] / n, 0),
            "avg_profit": round(b["profit"] / n, 0),
            "total_revenue": round(b["revenue"], 2),
            "total_profit": round(b["profit"], 2),
            "avg_payments": round(b["payments"] / n, 1),
            # Bir oyda o'rtacha qancha keltiradi
            "revenue_per_month": (round(b["revenue"] / b["months_sum"], 0)
                                  if b["months_sum"] else 0),
            "margin": (round(b["profit"] / b["revenue"] * 100, 1)
                       if b["revenue"] else 0.0),
            "churn": (round(b["left"] / n * 100, 1)),
        })
    rows.sort(key=lambda r: -r["avg_profit"])

    # Umumiy
    tot_students = sum(r["students"] for r in rows) or 1
    tot_months = sum(r["avg_months"] * r["students"] for r in rows)
    tot_rev = sum(r["total_revenue"] for r in rows)
    tot_profit = sum(r["total_profit"] for r in rows)
    overall = {
        "students": tot_students,
        "avg_months": round(tot_months / tot_students, 1),
        "avg_revenue": round(tot_rev / tot_students, 0),
        "avg_profit": round(tot_profit / tot_students, 0),
        "total_revenue": round(tot_rev, 2),
        "total_profit": round(tot_profit, 2),
        "margin": round(tot_profit / tot_rev * 100, 1) if tot_rev else 0.0,
        "overhead_per_month": overhead,
    }

    return {
        "dimension": dimension,
        "dimension_label": roles.LTV_DIMENSION_LABELS[dimension],
        "dimensions": [{"key": k, "label": l}
                       for k, l in roles.LTV_DIMENSIONS],
        "rows": rows,
        "overall": overall,
        "hint": ("Vaqt LTV — o'quvchi o'rtacha necha oy qoladi. "
                 "Pul LTV — shu vaqt ichida qancha to'laydi va "
                 "qancha sof foyda qoldiradi (ustoz haqi va "
                 "xarajat chiqarilgach)."),
    }

@router.get("/api/analytics/churn")
def analytics_churn(
    months: int = 12,
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.LTV_ACCESS)),
):
    """Qaysi guruhdan va qaysi ustozdan ko'p ketyapti — va NEGA."""
    today = date.today()
    y, m = _shift_month(today.year, today.month, -(max(1, months) - 1))
    start, _e = billing.month_bounds(y, m)

    students = scope_to_branch(db.query(models.Student), models.Student,
                               user, branch_id).all()
    groups = {g.id: g for g in db.query(models.Group).all()}
    teachers = {t.id: t for t in db.query(models.Teacher).all()}

    reasons = {}
    for r in db.query(models.LeaveReason).all():
        reasons[r.student_id] = r

    left = [s for s in students if s.left_date and s.left_date >= start]
    active = [s for s in students if s.status == "active"]

    # --- Sabablar ---
    by_reason = {}
    for s in left:
        r = reasons.get(s.id)
        key = r.reason if r else "unknown"
        row = by_reason.setdefault(key, {
            "key": key,
            "label": roles.LEAVE_REASON_LABELS.get(key, key),
            "group": roles.LEAVE_REASON_GROUP.get(key, "unknown"),
            "controllable": key in roles.CONTROLLABLE_REASONS,
            "count": 0, "students": [],
        })
        row["count"] += 1
        if len(row["students"]) < 10:
            row["students"].append(s.full_name)
    reason_rows = sorted(by_reason.values(), key=lambda r: -r["count"])

    # --- Ustoz kesimi ---
    def bucket(items, key_fn, label_fn):
        out = {}
        for s in items:
            k = key_fn(s)
            row = out.setdefault(str(k), {
                "key": k, "label": label_fn(k),
                "left": 0, "active": 0, "reasons": {},
            })
            if s.left_date and s.left_date >= start:
                row["left"] += 1
                r = reasons.get(s.id)
                rk = r.reason if r else "unknown"
                row["reasons"][rk] = row["reasons"].get(rk, 0) + 1
            elif s.status == "active":
                row["active"] += 1
        rows = []
        for r in out.values():
            base = r["left"] + r["active"]
            top = max(r["reasons"].items(), key=lambda x: x[1])[0] \
                if r["reasons"] else None
            rows.append({
                **r,
                "total": base,
                "churn": round(r["left"] / base * 100, 1) if base else 0.0,
                "top_reason": top,
                "top_reason_label": (roles.LEAVE_REASON_LABELS.get(top, None)
                                     if top else None),
                "reasons": [{"key": k, "label": roles.LEAVE_REASON_LABELS.get(k, k),
                             "count": v}
                            for k, v in sorted(r["reasons"].items(),
                                               key=lambda x: -x[1])],
            })
        rows.sort(key=lambda r: (-r["churn"], -r["left"]))
        return [r for r in rows if r["total"] > 0]

    by_teacher = bucket(
        students,
        lambda s: (groups[s.group_id].teacher_id
                   if s.group_id in groups else None),
        lambda k: teachers[k].full_name if k in teachers else "Biriktirilmagan")
    by_group = bucket(
        students,
        lambda s: s.group_id,
        lambda k: groups[k].name if k in groups else "Guruhsiz")

    total_base = len(left) + len(active)
    controllable = sum(r["count"] for r in reason_rows if r["controllable"])
    unknown = sum(r["count"] for r in reason_rows if r["key"] == "unknown")

    return {
        "months": months,
        "period": f"{start.isoformat()} — {today.isoformat()}",
        "left": len(left),
        "active": len(active),
        "churn": round(len(left) / total_base * 100, 1) if total_base else 0.0,
        "reasons": reason_rows,
        "by_teacher": by_teacher,
        "by_group": by_group,
        "controllable": controllable,
        "controllable_percent": (round(controllable / len(left) * 100, 1)
                                 if left else 0.0),
        "unknown": unknown,
        "reason_options": [{"key": k, "label": lbl}
                           for k, lbl, _ in roles.LEAVE_REASONS],
        "hint": ("Bizga bog'liq sabablar — ustoz, natija, raqobatchi, "
                 "jadval. Shularni kamaytirish mumkin."),
    }

@router.get("/api/analytics/romi")
def analytics_romi(
    months: int = 6,
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.MARKETING_ANALYTICS)),
):
    today = date.today()
    y, m = _shift_month(today.year, today.month, -(max(1, months) - 1))
    start, _e = billing.month_bounds(y, m)
    _s, end = billing.month_bounds(today.year, today.month)
    d0 = _utc_window(start, start)[0]

    leads = db.query(models.Lead).filter(models.Lead.created_at >= d0)
    if branch_id:
        leads = leads.filter(models.Lead.branch_id == branch_id)
    elif user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
        leads = leads.filter(_branch_in(db, user, models.Lead.branch_id))
    leads = leads.all()

    # Kanal xarajati: reklama xarajatlari channel bo'yicha
    spend = {}
    eq = db.query(models.Expense).filter(
        models.Expense.date >= start, models.Expense.date <= end,
        models.Expense.category == "ads")
    if branch_id:
        eq = eq.filter(models.Expense.branch_id == branch_id)
    for e in eq.all():
        ch = e.channel or "other"
        spend[ch] = spend.get(ch, 0.0) + (e.amount or 0)

    paid = _student_payments(db)
    students = {s.id: s for s in db.query(models.Student).all()}
    groups = {g.id: g for g in db.query(models.Group).all()}
    overhead = _overhead_per_student_month(db, user, branch_id)

    # Lidni o'quvchiga bog'lash - ism bo'yicha (converted lidlar)
    by_name = {}
    for s in students.values():
        by_name.setdefault(s.full_name.strip().lower(), s)

    by_channel = {}
    for l in leads:
        ch = l.source or "other"
        row = by_channel.setdefault(ch, {
            "key": ch,
            "label": roles.LEAD_SOURCE_LABELS.get(ch, ch)
                     if hasattr(roles, "LEAD_SOURCE_LABELS") else ch,
            "leads": 0, "converted": 0, "revenue": 0.0, "profit": 0.0,
        })
        row["leads"] += 1
        if l.stage == "converted":
            row["converted"] += 1
            s = by_name.get((l.full_name or "").strip().lower())
            if s:
                rev = paid.get(s.id, {}).get("total", 0.0)
                span = _months_between(s.enrolled_date or today,
                                       s.left_date or today)
                cost = _teacher_cost_for_student(db, s, groups) + overhead * span
                row["revenue"] += rev
                row["profit"] += rev - cost

    rows = []
    for r in by_channel.values():
        cost = spend.get(r["key"], 0.0)
        romi = (round((r["profit"] - cost) / cost * 100, 1)
                if cost else (None if r["profit"] == 0 else 9999.0))
        band, band_label, tone = roles.romi_band(romi if romi is not None else 0)
        rows.append({
            **r,
            "spend": round(cost, 2),
            "cac": round(cost / r["converted"], 0) if r["converted"] else None,
            "cpl": round(cost / r["leads"], 0) if r["leads"] else None,
            "conversion": (round(r["converted"] / r["leads"] * 100, 1)
                           if r["leads"] else 0.0),
            "revenue": round(r["revenue"], 2),
            "profit": round(r["profit"], 2),
            "romi": romi,
            "band": band if cost else "unknown",
            "band_label": band_label if cost else "Xarajat kiritilmagan",
            "tone": tone if cost else "slate",
        })
    rows.sort(key=lambda r: -(r["romi"] if r["romi"] is not None else -99999))

    total_spend = sum(r["spend"] for r in rows)
    total_profit = sum(r["profit"] for r in rows)
    return {
        "months": months,
        "period": f"{start.isoformat()} — {end.isoformat()}",
        "rows": rows,
        "total_spend": round(total_spend, 2),
        "total_revenue": round(sum(r["revenue"] for r in rows), 2),
        "total_profit": round(total_profit, 2),
        "romi": (round((total_profit - total_spend) / total_spend * 100, 1)
                 if total_spend else None),
        "no_spend": [r["label"] for r in rows if not r["spend"]],
        "hint": ("ROMI 100% dan yuqori bo'lsa — kanal o'z pulini "
                 "qaytarib, ustiga foyda keltiryapti. Xarajat "
                 "kiritilmagan kanallarda ROMI hisoblanmaydi."),
    }

@router.get("/api/analytics/capacity")
def analytics_capacity(
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.ACADEMIC_VIEW)),
):
    rooms = scope_to_branch(db.query(models.Room), models.Room,
                            user, branch_id).filter(
        models.Room.active == 1).all()
    groups = scope_to_branch(db.query(models.Group), models.Group,
                             user, branch_id).all()
    students = scope_to_branch(db.query(models.Student), models.Student,
                               user, branch_id).all()
    room_by_id = {r.id: r for r in rooms}

    # Haftada nechа soat ochiq: 6 kun x (22:00 - 06:00)
    open_hours_week = 6 * (GRID_END_MIN - GRID_START_MIN) / 60

    rows = []
    for r in rooms:
        mine = [g for g in groups if g.room_id == r.id]
        hours = 0.0
        seats_used = 0
        slots = 0
        for g in mine:
            days = len([d for d in (g.lesson_days or "").split(",") if d])
            a, b = _group_slot(g)
            if a and b:
                dur = ((roles.time_to_minutes(b) or 0)
                       - (roles.time_to_minutes(a) or 0)) / 60
                hours += dur * days
            n = sum(1 for s in students
                    if s.group_id == g.id and s.status in ("active", "trial"))
            seats_used += n
            slots += (r.capacity or 0)
        rows.append({
            "room_id": r.id,
            "name": r.name,
            "branch": r.branch.name if r.branch else None,
            "capacity": r.capacity,
            "groups": len(mine),
            "students": seats_used,
            # O'rin bandligi: guruhlar bo'yicha o'rtacha to'lish
            "seat_usage": round(seats_used / slots * 100, 1) if slots else 0.0,
            # Vaqt bandligi: haftada necha soat band
            "hours_week": round(hours, 1),
            "time_usage": round(hours / open_hours_week * 100, 1),
            "free_seats": max(0, slots - seats_used),
        })
    rows.sort(key=lambda r: r["time_usage"])

    total_cap = sum(r.capacity or 0 for r in rooms)
    total_students = sum(1 for s in students if s.status == "active")
    total_hours = sum(r["hours_week"] for r in rows)
    open_total = open_hours_week * len(rooms) if rooms else 1

    # Bo'sh joyning pul qiymati
    avg_fee = 0.0
    fees = [g.monthly_fee or 0 for g in groups if g.monthly_fee]
    if fees:
        avg_fee = sum(fees) / len(fees)
    lost = sum(r["free_seats"] for r in rows) * avg_fee

    return {
        "rooms": rows,
        "room_count": len(rooms),
        "total_capacity": total_cap,
        "active_students": total_students,
        # Umumiy sig'imdan necha foiz ishlatilyapti
        "seat_usage": (round(total_students / total_cap * 100, 1)
                       if total_cap else 0.0),
        "time_usage": round(total_hours / open_total * 100, 1) if rooms else 0.0,
        "open_hours_week": open_hours_week,
        "free_seats": sum(r["free_seats"] for r in rows),
        "lost_income": round(lost, 2),
        "worst": rows[0]["name"] if rows else None,
        "hint": ("Bo'sh turgan xona — bu ijara puli. Vaqt bandligi "
                 "past xonalarga yangi guruh qo'yish mumkin."),
    }

def _room_seats(r: models.Room) -> int:
    return int(r.capacity or roles.DEFAULT_ROOM_SEATS)

def _fill_rows(db: Session, user: models.User, *, branch_id=None,
               level: str = roles.FILL_DEFAULT_LEVEL) -> dict:
    per_room = roles.FILL_GROUPS.get(level, 4)

    rooms = scope_to_branch(db.query(models.Room), models.Room,
                            user, branch_id).filter(
        models.Room.active == 1).all()
    groups = scope_to_branch(db.query(models.Group), models.Group,
                             user, branch_id).all()
    # Xonalardagi o'quvchilar soni FAQAT FAOLLARDAN olinadi
    students = scope_to_branch(db.query(models.Student), models.Student,
                               user, branch_id).filter(
        models.Student.status == "active").all()
    branches = {b.id: b.name for b in db.query(models.Branch).all()}
    teachers = {t.id: t for t in db.query(models.Teacher).all()}
    grades = {g.key: g for g in db.query(models.TeacherGrade).all()}

    # O'quvchilar guruh kesimida
    per_group: dict = {}
    for s in students:
        if s.group_id:
            per_group[s.group_id] = per_group.get(s.group_id, 0) + 1

    # ---- Xonalar kesimida ----
    room_rows = []
    for r in rooms:
        seats = _room_seats(r)
        cap = seats * per_room
        in_room = [g for g in groups if g.room_id == r.id]
        odd = sum(1 for g in in_room
                  if roles.day_side(_group_days(g)) in ("odd", "mixed"))
        even = sum(1 for g in in_room
                   if roles.day_side(_group_days(g)) in ("even", "mixed"))
        st = sum(per_group.get(g.id, 0) for g in in_room)
        pct = round(st / cap * 100, 1) if cap else 0.0
        label, tone = roles.fill_grade(pct)
        room_rows.append({
            "room_id": r.id, "name": r.name,
            "branch": branches.get(r.branch_id, "—"),
            "branch_id": r.branch_id,
            "seats": seats,
            "capacity": cap,
            "groups": len(in_room),
            "group_slots": per_room,
            "odd_groups": odd, "even_groups": even,
            "students": st,
            "free": max(0, cap - st),
            "percent": pct,
            "label": label, "tone": tone,
        })
    room_rows.sort(key=lambda r: -r["percent"])

    total_cap = sum(r["capacity"] for r in room_rows)
    total_st = sum(r["students"] for r in room_rows)
    # Xonasi biriktirilmagan guruhlardagi o'quvchilar ham bor —
    # ular sig'imga kirmaydi, lekin markazda o'qiyapti. Buni yashirmay
    # alohida ko'rsatamiz, aks holda foiz yolg'on chiqadi.
    no_room = sum(per_group.get(g.id, 0) for g in groups if not g.room_id)

    # ---- Filiallar kesimida ----
    by_branch: dict = {}
    for r in room_rows:
        b = by_branch.setdefault(r["branch_id"], {
            "branch_id": r["branch_id"],
            "name": branches.get(r["branch_id"], "—"),
            "rooms": 0, "capacity": 0, "students": 0, "groups": 0,
        })
        b["rooms"] += 1
        b["capacity"] += r["capacity"]
        b["students"] += r["students"]
        b["groups"] += r["groups"]
    branch_rows = []
    for b in by_branch.values():
        pct = round(b["students"] / b["capacity"] * 100, 1) \
            if b["capacity"] else 0.0
        label, tone = roles.fill_grade(pct)
        branch_rows.append({**b, "percent": pct, "free":
                            max(0, b["capacity"] - b["students"]),
                            "label": label, "tone": tone,
                            "group_slots": b["rooms"] * per_room})
    branch_rows.sort(key=lambda r: -r["percent"])

    # ---- Ustozlar kesimida ----
    # Ustozning sig'imi: darajasi bo'yicha nechta guruh olib bora oladi,
    # har biri o'zi dars beradigan xonaning sig'imicha.
    room_by_id = {r.id: r for r in rooms}
    teacher_rows = []
    for t in teachers.values():
        if t.is_active == 0:
            continue
        mine = [g for g in groups if g.teacher_id == t.id]
        if not mine and branch_id and t.branch_id != branch_id:
            continue
        gr = grades.get(t.grade or "")
        max_groups = (t.max_groups or (gr.max_groups if gr else None)
                      or roles.TEACHER_MAX_GROUPS)
        # O'rtacha xona sig'imi: o'zi ishlaydigan xonalar bo'yicha
        seats_list = [_room_seats(room_by_id[g.room_id])
                      for g in mine if g.room_id in room_by_id]
        seats = (round(sum(seats_list) / len(seats_list)) if seats_list
                 else roles.DEFAULT_ROOM_SEATS)
        cap = max_groups * seats
        st = sum(per_group.get(g.id, 0) for g in mine)
        pct = round(st / cap * 100, 1) if cap else 0.0
        label, tone = roles.fill_grade(pct)
        teacher_rows.append({
            "teacher_id": t.id, "name": t.full_name,
            "branch": branches.get(t.branch_id, "—"),
            "grade": t.grade,
            "grade_label": roles.GRADE_LABELS.get(t.grade or "", "—"),
            "groups": len(mine), "max_groups": max_groups,
            "seats": seats, "capacity": cap, "students": st,
            "free": max(0, cap - st),
            "percent": pct, "label": label, "tone": tone,
        })
    teacher_rows.sort(key=lambda r: -r["percent"])

    percent = round(total_st / total_cap * 100, 1) if total_cap else 0.0
    label, tone = roles.fill_grade(percent)

    # Boshqa darajalarda qanday ko'rinishi
    levels = []
    for key, lbl, g, desc in roles.FILL_LEVELS:
        cap = sum(r["seats"] * g for r in room_rows)
        levels.append({
            "key": key, "label": lbl, "groups_per_room": g,
            "description": desc,
            "capacity": cap,
            "percent": round(total_st / cap * 100, 1) if cap else 0.0,
            "free": max(0, cap - total_st),
            "current": key == level,
        })

    return {
        "level": level,
        "level_label": roles.FILL_LEVEL_LABELS.get(level, level),
        "groups_per_room": per_room,
        "rooms": len(room_rows),
        "capacity": total_cap,
        "students": total_st,
        "students_without_room": no_room,
        "percent": percent,
        "label": label, "tone": tone,
        "free": max(0, total_cap - total_st),
        "group_slots": len(room_rows) * per_room,
        "groups_now": sum(r["groups"] for r in room_rows),
        "levels": levels,
        "by_room": room_rows,
        "by_branch": branch_rows,
        "by_teacher": teacher_rows,
        "hint": ("Sig'im shunday hisoblanadi: bitta xonaga toq kunlari "
                 "2 ta guruh, juft kunlari 2 ta guruh — jami "
                 f"{per_room} ta. Xona {roles.DEFAULT_ROOM_SEATS} "
                 "kishilik bo'lsa, bitta xona "
                 f"{roles.DEFAULT_ROOM_SEATS * per_room} o'quvchi "
                 "sig'diradi."),
    }

@router.get("/api/analytics/fill")
def analytics_fill(
    level: str = roles.FILL_DEFAULT_LEVEL,
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FILL_ACCESS)),
):
    """O'quv markaz qanchaga to'lgan — filial, xona va ustoz kesimida."""
    if level not in roles.FILL_GROUPS:
        level = roles.FILL_DEFAULT_LEVEL
    return _fill_rows(db, user, branch_id=branch_id, level=level)

@router.get("/api/analytics/academic")
def analytics_academic(branch_id: int | None = None,
                       db: Session = Depends(get_db),
                       user=Depends(require_role(*roles.FULL_ACCESS,
                                                 roles.ACADEMIC_HEAD))):
    """Fanlar/darajalar kesimi, top ustozlar va AKADEMIK VORONKA.

    Voronka: Step 1da o'qigan bolalarning nechtasi Step 2, Step 3 va
    IELTS/CEFR gacha yetdi, nechtasi sertifikat natija qildi. Yo'l
    yoqlama tarixidan tiklanadi (qaysi darajadagi guruh darsida
    qatnashgani), shuning uchun eski o'quvchilar ham hisobda."""
    groups = {g.id: g for g in db.query(models.Group).all()}
    sq = db.query(models.Student)
    if branch_id:
        sq = sq.filter(models.Student.branch_id == branch_id)
    students = sq.all()

    active = [s for s in students if s.status == "active" and s.group_id]
    total_a = len(active) or 1
    subj, lvl, teach = {}, {}, {}
    for s in active:
        g = groups.get(s.group_id)
        if not g:
            continue
        subj[g.subject or "boshqa"] = subj.get(g.subject or "boshqa", 0) + 1
        lvl[g.level or "belgilanmagan"] = lvl.get(
            g.level or "belgilanmagan", 0) + 1
        if g.teacher_id:
            teach[g.teacher_id] = teach.get(g.teacher_id, 0) + 1
    t_names = {t.id: t.full_name for t in db.query(models.Teacher).all()}
    subj_lbl = dict(roles.SUBJECTS)

    # Har o'quvchining bosib o'tgan darajalari — yoqlama tarixidan
    rows = (db.query(models.Attendance.student_id, models.Lesson.group_id)
            .join(models.Lesson,
                  models.Lesson.id == models.Attendance.lesson_id)
            .distinct().all())
    path = {}
    for sid, gid in rows:
        g = groups.get(gid)
        if g and g.level:
            path.setdefault(sid, set()).add(g.level)
    for s in students:                      # hali darsi yo'qlar ham
        g = groups.get(s.group_id) if s.group_id else None
        if g and g.level:
            path.setdefault(s.id, set()).add(g.level)

    IELTS = {"step4", "ielts_intro", "ielts_foundation",
             "ielts_graduation", "cefr"}
    cohort = [sid for sid, lv in path.items() if "step1" in lv]
    to2 = [sid for sid in cohort if "step2" in path[sid]]
    to3 = [sid for sid in cohort if "step3" in path[sid]]
    toI = [sid for sid in cohort if path[sid] & IELTS]
    cert_ids = {c.student_id for c in db.query(models.Certificate).all()}
    result = [sid for sid in cohort if sid in cert_ids]
    n0 = len(cohort) or 1

    # Ketish darajasi: arxivlangan o'quvchining OXIRGI darajasi
    order = ["step1", "step2", "step3", "step4", "ielts_intro",
             "ielts_foundation", "ielts_graduation", "cefr"]
    churn = {}
    left_students = [s for s in students if s.status == "archived"]
    for s in left_students:
        lv = path.get(s.id, set())
        last = None
        for k in order:
            if k in lv:
                last = k
        g = groups.get(s.group_id) if s.group_id else None
        last = last or (g.level if g else None) or "belgilanmagan"
        churn[last] = churn.get(last, 0) + 1
    total_left = sum(churn.values()) or 1
    churn_rows = sorted(
        [{"level": k, "label": roles.LEVEL_LABELS.get(k, k),
          "count": v, "percent": round(v / total_left * 100, 1)}
         for k, v in churn.items()], key=lambda r: -r["count"])

    pct = lambda n: round(n / n0 * 100, 1)
    return {
        "subjects": sorted(
            [{"key": k, "label": subj_lbl.get(k, k), "count": v,
              "percent": round(v / total_a * 100, 1)}
             for k, v in subj.items()], key=lambda r: -r["count"]),
        "levels": sorted(
            [{"key": k, "label": roles.LEVEL_LABELS.get(k, k), "count": v,
              "percent": round(v / total_a * 100, 1)}
             for k, v in lvl.items()], key=lambda r: -r["count"]),
        "top_teachers": sorted(
            [{"name": t_names.get(k, "—"), "students": v}
             for k, v in teach.items()], key=lambda r: -r["students"])[:10],
        "active_total": len(active),
        "funnel": [
            {"stage": "Step 1da boshladi", "count": len(cohort),
             "percent": 100.0},
            {"stage": "Step 2ga o'tdi", "count": len(to2),
             "percent": pct(len(to2))},
            {"stage": "Step 3ga o'tdi", "count": len(to3),
             "percent": pct(len(to3))},
            {"stage": "IELTS/CEFRga o'tdi", "count": len(toI),
             "percent": pct(len(toI))},
            {"stage": "Natija qildi (sertifikat)", "count": len(result),
             "percent": pct(len(result))},
        ],
        "churn": churn_rows,
        "churn_worst": churn_rows[0] if churn_rows else None,
        "left_total": len(left_students),
        "geo": _geo_stats(db, branch_id),
        "hint": ("Voronka yoqlama tarixidan tiklanadi: o'quvchi qaysi "
                 "darajadagi guruh darslarida qatnashgan bo'lsa, o'sha "
                 "bosqichdan o'tgan hisoblanadi. Ketish — arxivlangan "
                 "o'quvchining oxirgi darajasi bo'yicha."),
    }

def _geo_stats(db: Session, branch_id=None) -> dict:
    """Lidlar va o'quvchilar qayerdan (manzil) va qaysi maktabdan."""
    def top(rows, n=10):
        agg = {}
        for (v,) in rows:
            v = (v or "").strip()
            if not v:
                continue
            agg[v] = agg.get(v, 0) + 1
        return [{"name": k, "count": c} for k, c in
                sorted(agg.items(), key=lambda kv: -kv[1])[:n]]

    lq = db.query(models.Lead.address)
    lsq = db.query(models.Lead.school)
    sq = db.query(models.Student.address).filter(
        models.Student.status == "active")
    ssq = db.query(models.Student.school).filter(
        models.Student.status == "active")
    if branch_id:
        lq = lq.filter(models.Lead.branch_id == branch_id)
        lsq = lsq.filter(models.Lead.branch_id == branch_id)
        sq = sq.filter(models.Student.branch_id == branch_id)
        ssq = ssq.filter(models.Student.branch_id == branch_id)
    return {
        "lead_addresses": top(lq.all()),
        "lead_schools": top(lsq.all()),
        "student_addresses": top(sq.all()),
        "student_schools": top(ssq.all()),
    }



@router.get("/api/analytics/sources")
def analytics_sources(
    months: int = 12,
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FINANCE_ACCESS)),
):
    """Lid va o'quvchilar QAYERDAN kelgani (pie chart uchun).

    Jahongir (2026-08-12): "Analitika bo'limida lid va o'quvchilar
    qayerdanligini pie chart yordamida ko'rsatilsin".

    O'quvchi manbasi — u aylantirilgan lidning manbasi. Lidsiz (to'g'ridan
    to'g'ri qo'shilgan) o'quvchilar "Lidsiz qo'shilgan" bo'lib chiqadi."""
    today = roles.local_today()
    if months and months > 0:
        start_d = today - timedelta(days=months * 31)
    else:
        start_d = date(2000, 1, 1)
    start_dt = datetime.combine(start_d, dtime(0, 0))

    if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
        branch_id = user.branch_id

    lbl = roles.LEAD_SOURCE_LABELS

    # ---- Lidlar manbasi ----
    lq = (db.query(models.Lead.source, func.count(models.Lead.id))
          .filter(models.Lead.created_at >= start_dt))
    if branch_id:
        lq = lq.filter(models.Lead.branch_id == branch_id)
    leads = [{"key": k or "other", "label": lbl.get(k, k or "Boshqa"),
              "count": int(c)}
             for k, c in lq.group_by(models.Lead.source).all() if c]
    leads.sort(key=lambda r: -r["count"])

    # ---- O'quvchilar manbasi (aylantirilgan lid orqali) ----
    sq = (db.query(models.Student.id, models.Lead.source)
          .outerjoin(models.Lead,
                     models.Lead.converted_student_id == models.Student.id)
          .filter(models.Student.enrolled_date >= start_d))
    if branch_id:
        sq = sq.filter(models.Student.branch_id == branch_id)
    seen: dict = {}
    for sid, src in sq.all():
        # bitta o'quvchiga bir nechta lid ulangan bo'lsa — bittasi yetadi
        if sid in seen and seen[sid]:
            continue
        seen[sid] = src
    s_counts: dict = {}
    for src in seen.values():
        key = src or "__nolead__"
        s_counts[key] = s_counts.get(key, 0) + 1
    students = [{"key": k,
                 "label": ("Lidsiz qo'shilgan" if k == "__nolead__"
                           else lbl.get(k, k)),
                 "count": c} for k, c in s_counts.items() if c]
    students.sort(key=lambda r: -r["count"])

    return {
        "months": months,
        "leads": leads,
        "students": students,
        "total_leads": sum(r["count"] for r in leads),
        "total_students": sum(r["count"] for r in students),
        "hint": ("O'quvchi manbasi — u qaysi liddan aylangani. "
                 "'Lidsiz qo'shilgan' — CRMga to'g'ridan-to'g'ri "
                 "kiritilgan o'quvchilar (manbasi yozilmagan)."),
    }
