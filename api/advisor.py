"""BIZNES MASLAHATCHI AI + BI STATISTIKA (2026-08-20).

Jahongir: "menga asoschi uchun Biznes maslahatchi AI qoshib ber
ichiga mendagi bor malumotlar platformadan kelib chiqib men bilan
biznes tahlil qila olsin, chuqur tahlillarga asoslanib menga
tavsiyalar bera olsin, analitik bo'limini eng zor BI texnologiyalari
bilan qaror qilishga oson statistikalarini chiroyli pie chart, line
graph yoki boshqa chiroyli shartlar bilan korsatadigan qil".

Ikkala ish bitta faylda, chunki ikkalasi ham BIR XIL raqamlarga
tayanadi: /api/analytics/bi ekranga chizadi, /api/founder/advisor
esa o'sha raqamlarni AI'ga kontekst qilib beradi — maslahatchi
ekranda ko'rinmagan narsani "o'ylab topmaydi"."""

import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

import models
import roles
from database import get_db
from auth import require_role

router = APIRouter()


def _month_keys(n: int = 12) -> list[str]:
    """Oxirgi n oy ro'yxati: ["2025-09", ..., "2026-08"]."""
    t = roles.local_today()
    out = []
    y, m = t.year, t.month
    for _ in range(n):
        out.append(f"{y:04d}-{m:02d}")
        m -= 1
        if m == 0:
            y, m = y - 1, 12
    return list(reversed(out))


def _pay_month(p) -> str:
    """To'lov qaysi oyga tegishli - kiritilgan sana bo'yicha."""
    d = getattr(p, "entered_at", None) or p.created_at
    return f"{d.year:04d}-{d.month:02d}" if d else ""


def bi_snapshot(db: Session) -> dict:
    """Barcha BI raqamlar bitta so'rovlar to'plamida.

    MUHIM: og'ir jadvallar (payments, students) bir martadan
    o'qiladi va Python'da guruhlanadi — Neon trafigi tejaladi."""
    today = roles.local_today()
    months = _month_keys(12)
    mset = set(months)
    this_m = months[-1]
    last_m = months[-2]
    first_dt = datetime.strptime(months[0] + "-01", "%Y-%m-%d")

    branches = {b.id: b.name for b in db.query(models.Branch).all()}
    partner_ids = {b.id for b in db.query(models.Branch)
                   if getattr(b, "is_partner", 0)}

    students = db.query(
        models.Student.id, models.Student.status,
        models.Student.branch_id, models.Student.enrolled_date,
        models.Student.left_date, models.Student.group_id,
    ).all()
    sid_branch = {s.id: s.branch_id for s in students}
    main_ids = {s.id for s in students
                if s.branch_id not in partner_ids}

    # ---------------- tushum / hisob (12 oy) ----------------
    pays = (db.query(models.Payment)
            .filter(models.Payment.created_at >= first_dt
                    - timedelta(days=40))
            .all())
    rev = {m: 0.0 for m in months}          # kirgan pul
    method = {}                              # shu oy usullari
    branch_rev = {}                          # shu oy filial kesimi
    charges = {m: 0.0 for m in months}       # hisoblangan o'qish haqi
    for p in pays:
        if p.student_id not in main_ids:
            continue
        mk = _pay_month(p)
        if mk not in mset:
            continue
        if p.kind == "payment" and (p.amount or 0) > 0:
            rev[mk] += p.amount
            if mk == this_m:
                method[p.method or "boshqa"] = (
                    method.get(p.method or "boshqa", 0) + p.amount)
                b = branches.get(sid_branch.get(p.student_id), "—")
                branch_rev[b] = branch_rev.get(b, 0) + p.amount
        elif p.kind == "charge" and p.period in mset:
            charges[p.period] += abs(p.amount or 0)

    # ---------------- xarajat + ustoz oyligi ----------------
    exp = {m: 0.0 for m in months}
    for e in db.query(models.Expense).filter(
            models.Expense.date >= first_dt.date()).all():
        if e.branch_id in partner_ids:
            continue
        mk = f"{e.date.year:04d}-{e.date.month:02d}"
        if mk in mset:
            exp[mk] += e.amount or 0
    for po in db.query(models.TeacherPayout).filter(
            models.TeacherPayout.period.in_(months)).all():
        exp[po.period] = exp.get(po.period, 0) + (po.amount or 0)

    # ---------------- o'quvchi oqimi (12 oy) ----------------
    new_m = {m: 0 for m in months}
    left_m = {m: 0 for m in months}
    for s in students:
        if s.branch_id in partner_ids:
            continue
        if s.enrolled_date:
            mk = f"{s.enrolled_date.year:04d}-{s.enrolled_date.month:02d}"
            if mk in mset:
                new_m[mk] += 1
        if s.left_date:
            mk = f"{s.left_date.year:04d}-{s.left_date.month:02d}"
            if mk in mset:
                left_m[mk] += 1
    active_now = sum(1 for s in students
                     if s.status == "active"
                     and s.branch_id not in partner_ids)
    frozen_now = sum(1 for s in students
                     if s.status == "frozen"
                     and s.branch_id not in partner_ids)
    # faol soni trendini oqimdan tiklaymiz (oxiridan orqaga)
    act_trend = []
    run = active_now + frozen_now
    for mk in reversed(months):
        act_trend.append({"month": mk, "value": max(0, run)})
        run -= new_m[mk] - left_m[mk]
    act_trend.reverse()

    # ---------------- qarz ----------------
    bal = dict(db.query(models.Payment.student_id,
                        func.sum(models.Payment.amount))
               .group_by(models.Payment.student_id).all())
    debt_total = 0.0
    debt_branch = {}
    debtors = 0
    for s in students:
        if s.branch_id in partner_ids or s.status == "archived":
            continue
        b = float(bal.get(s.id) or 0)
        if b < -1000:
            debt_total += -b
            debtors += 1
            nm = branches.get(s.branch_id, "—")
            debt_branch[nm] = debt_branch.get(nm, 0) + (-b)

    # ---------------- guruhlar TOP ----------------
    groups = db.query(models.Group).all()
    gcount = {}
    for s in students:
        if s.status == "active" and s.group_id:
            gcount[s.group_id] = gcount.get(s.group_id, 0) + 1
    top_groups = sorted(
        ({"name": g.name,
          "students": gcount.get(g.id, 0),
          "revenue": gcount.get(g.id, 0) * (g.monthly_fee or 0)}
         for g in groups if g.branch_id not in partner_ids),
        key=lambda x: -x["revenue"])[:8]

    # ---------------- lidlar (90 kun) ----------------
    since = today - timedelta(days=90)
    leads = db.query(models.Lead).filter(
        models.Lead.created_at >= datetime.combine(since, datetime.min.time())
    ).all()
    lead_total = len(leads)
    lead_won = sum(1 for l in leads
                   if (l.stage or "") == "converted")

    avg_check = (rev[this_m] / max(1, sum(1 for p in pays
                 if p.kind == "payment" and _pay_month(p) == this_m
                 and p.student_id in main_ids))) if rev[this_m] else 0

    months_lbl = [{"month": m} for m in months]
    return {
        "generated": today.isoformat(),
        "months": months,
        "kpi": {
            "active": active_now,
            "frozen": frozen_now,
            "debtors": debtors,
            "debt_total": round(debt_total),
            "rev_this": round(rev[this_m]),
            "rev_last": round(rev[last_m]),
            "rev_mom": (round((rev[this_m] - rev[last_m])
                              / rev[last_m] * 100, 1)
                        if rev[last_m] else None),
            "profit_this": round(rev[this_m] - exp[this_m]),
            "collection": (round(rev[this_m] / charges[this_m] * 100, 1)
                           if charges[this_m] else None),
            "avg_check": round(avg_check),
            "lead_total_90d": lead_total,
            "lead_won_90d": lead_won,
            "lead_conv": (round(lead_won / lead_total * 100, 1)
                          if lead_total else None),
            "new_this": new_m[this_m],
            "left_this": left_m[this_m],
            "churn": (round(left_m[this_m] / max(1, active_now) * 100, 1)),
        },
        "revenue_by_month": [
            {"month": m, "tushum": round(rev[m]),
             "xarajat": round(exp[m]),
             "foyda": round(rev[m] - exp[m])} for m in months],
        "students_trend": act_trend,
        "flow_by_month": [
            {"month": m, "kelgan": new_m[m], "ketgan": left_m[m]}
            for m in months],
        "branch_revenue": [
            {"name": k, "value": round(v)}
            for k, v in sorted(branch_rev.items(), key=lambda x: -x[1])],
        "method_split": [
            {"name": roles.PAYMENT_METHOD_LABELS.get(k, k), "value": round(v)}
            for k, v in sorted(method.items(), key=lambda x: -x[1])],
        "debt_by_branch": [
            {"name": k, "value": round(v)}
            for k, v in sorted(debt_branch.items(), key=lambda x: -x[1])],
        "top_groups": top_groups,
        "_months_lbl": months_lbl,
    }


@router.get("/api/analytics/bi")
def analytics_bi(db: Session = Depends(get_db),
                 user=Depends(require_role(*roles.FINANCE_ACCESS))):
    """BI panel raqamlari — faqat moliyani ko'ra oladiganlarga."""
    return bi_snapshot(db)


# ===================================================================
#  BIZNES MASLAHATCHI (faqat asoschi)
# ===================================================================
_SYSTEM = """Sen "Jony Advisor" - Jony Academy o'quv markazlari
tarmog'i asoschisi Jahongirning shaxsiy biznes maslahatchisisan.
O'zbek tilida, aniq va samimiy gapir. Quyida platformadagi HAQIQIY
raqamlar (JSON). Har javobingda:
1) fikringni aynan shu raqamlarga tayan, raqamni keltir;
2) chuqur tahlil qil: trend, sabab, xavf;
3) 2-3 ta aniq, bajarsa bo'ladigan tavsiya ber;
4) ma'lumot yetmasa - taxmin qilma, qaysi raqam kerakligini ayt.
Javobni qisqa abzatslar bilan yoz, jadval kerak bo'lsa oddiy matnda.
Pul birligi - so'm. Bugungi sana: {today}.

PLATFORMA MA'LUMOTLARI:
{data}
"""


@router.post("/api/founder/advisor")
def founder_advisor(payload: dict = Body(...),
                    db: Session = Depends(get_db),
                    user=Depends(require_role(roles.FOUNDER))):
    """Asoschi bilan biznes suhbat. Tarix mijozdan keladi (student
    speaking'dagi kabi), server esa har safar YANGI raqamlarni
    kontekstga qo'shadi."""
    text = (payload.get("text") or "").strip()
    if not text:
        raise HTTPException(400, "Savol bo'sh")
    history = payload.get("history") or []
    if not isinstance(history, list):
        history = []
    # tarixni chegaralaymiz - token va trafik tejaladi
    history = [
        {"role": ("assistant" if h.get("role") == "assistant" else "user"),
         "content": str(h.get("content", ""))[:1500]}
        for h in history[-16:]
    ]

    snap = bi_snapshot(db)
    snap.pop("_months_lbl", None)
    system = _SYSTEM.format(
        today=roles.local_today().isoformat(),
        data=json.dumps(snap, ensure_ascii=False))

    import student_app as sa
    msgs = history + [{"role": "user", "content": text[:2000]}]
    try:
        reply = sa._ai_reply(system, msgs)
    except TimeoutError:
        raise HTTPException(
            502, "Maslahatchi hozir juda band — bir daqiqadan so'ng "
                 "qayta urinib ko'ring.")
    except Exception as e:
        try:
            db.add(models.ErrorLog(
                path="/api/founder/advisor", method="POST",
                detail=str(e)[:1900], user_name=user.full_name))
            db.commit()
        except Exception:
            db.rollback()
        raise HTTPException(
            502, "Maslahatchi javob bera olmadi. Birozdan so'ng qayta "
                 "urinib ko'ring.")
    return {"reply": reply}
