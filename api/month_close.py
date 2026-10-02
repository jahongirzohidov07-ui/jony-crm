"""OY YOPILISHI VA P&L (2026-10-02).

Jahongir: "oy oxirida ... shu oy oyliklari, masalan oktabr tugasa oktabr
oxirida ustozlarniki cashflowda paydo bo'lsin, yonida berildi /
berilmadi tursin. Filial rahbari yoki admin cashflowdan beradimi yoki
xarajatdan kiritib oktabr oyiniki deb belgilab bersa yopilsin. Shunda
menga shu oyda qancha foydadaman yoki yo'q bilishim kerak, va P&L
jadval moliyada har oy qancha foyda yoki zarardaligimni ko'rsatib
turishi kerak".

Pul oqimi ikki ko'rinishda:
  * Real vaqt — pul QACHON tushgan/chiqqan bo'lsa (eski ko'rinish).
  * Oy kesimida — to'lov QAYSI OY UCHUN bo'lsa o'sha oyga yoziladi:
    sentabr qarzini 10-oktabrda to'lasa ham sentabr daromadi
    ("qat'iy bir oyda qancha daromad qilyapman").

Qarorlar (Jahongir, 2026-10-02):
  * Ma'muriy xodim oyligi — fiks oylik; adminlar — fiks + KPI bonusi.
  * Oylik qaysi oyniki — beruvchi tanlaydi (period); bo'sh bo'lsa sana oyi.
  * Oy ichida berilgan avans o'sha oy oyligidan ayiriladi.
  * Daromad (oy kesimida) — o'quvchi to'lovi eng eski qarzdorlik oyiga
    yopiladi (FIFO). Oy yechilmagan ortiqcha pul — "oldindan to'lov",
    hech bir oy daromadiga kirmaydi, alohida ko'rsatiladi.
"""
import sys
from datetime import date, datetime, timedelta

from fastapi import Body, Depends, HTTPException
from sqlalchemy.orm import Session

import audit
import billing
import models
import roles
from main import app, get_db, require_role, scope_to_branch
from auth import is_partner_head
import common as C
import dashboard as D
import finance as F


def _E():
    return sys.modules.get("entry")


def _pk(y: int, m: int) -> str:
    return f"{y:04d}-{m:02d}"


def _prev(y: int, m: int):
    return (y - 1, 12) if m == 1 else (y, m - 1)


def _next(y: int, m: int):
    return (y + 1, 1) if m == 12 else (y, m + 1)


def _local_period(dt) -> str:
    if dt is None:
        return ""
    if isinstance(dt, datetime):
        dt = dt + timedelta(hours=roles.TIMEZONE_OFFSET_HOURS)
    return dt.strftime("%Y-%m")


def _eff_bid(db: Session, user, bid):
    """Filialga bog'langan xodim (admin, filial rahbari) faqat o'z
    filialini ko'radi; "barcha filiallar"da — asosiy filiali."""
    if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
        allowed = C._user_branch_ids(db, user)
        return bid if bid and bid in allowed else user.branch_id
    if is_partner_head(user):
        return user.branch_id
    return bid


# ------------------------------------------------------------ daromad ---
def allocate_income(db: Session, user, bid) -> dict:
    """O'quvchi to'lovlarini oylarga FIFO bilan taqsimlaydi.

    Har o'quvchi uchun: oy bo'yicha qarz = yechilgan (charge) −
    chegirma; to'lovlar vaqt tartibida eng eski ochiq oyni yopadi.
    Qaytariladi: {"periods": {P: {total, by_method, students, pending}},
                  "advance": oy yechilmagan ortiqcha pul,
                  "refunds": {P: qaytarilgan pul (manfiy to'lov)}}"""
    q = (db.query(models.Payment)
         .join(models.Student, models.Payment.student_id == models.Student.id)
         .filter(models.Payment.kind.in_(("payment", "charge", "discount"))))
    q = scope_to_branch(q, models.Student, user, bid)
    by_student: dict = {}
    for p in q.order_by(models.Payment.student_id, models.Payment.created_at,
                        models.Payment.id).all():
        by_student.setdefault(p.student_id, []).append(p)

    periods: dict = {}
    refunds: dict = {}
    advance = 0.0

    def slot(P):
        return periods.setdefault(P, {"total": 0.0, "by_method": {},
                                      "students": set(), "pending": 0.0})

    for sid, ps in by_student.items():
        owed: dict = {}
        pays = []
        for p in ps:
            amt = float(p.amount or 0)
            if p.kind == "payment":
                if amt < 0:
                    P = _local_period(p.created_at)
                    refunds[P] = refunds.get(P, 0.0) + amt
                elif amt > 0:
                    pays.append((amt, p.method or "cash"))
                continue
            P = p.period or _local_period(p.created_at)
            # charge manfiy (qarz), discount musbat (qarzni kamaytiradi)
            owed[P] = owed.get(P, 0.0) - amt
        order = sorted(P for P, v in owed.items() if v > 0.005)
        i = 0
        for amt, method in pays:
            while amt > 0.005 and i < len(order):
                P = order[i]
                take = min(amt, owed[P])
                s = slot(P)
                s["total"] += take
                s["by_method"][method] = s["by_method"].get(method, 0.0) + take
                s["students"].add(sid)
                owed[P] -= take
                amt -= take
                if owed[P] <= 0.005:
                    i += 1
            if amt > 0.005:
                advance += amt
        for P in order:
            if owed[P] > 0.005:
                slot(P)["pending"] += owed[P]
    return {"periods": periods, "advance": round(advance, 2),
            "refunds": refunds}


def _income_of(alloc: dict, P: str) -> dict:
    s = alloc["periods"].get(P)
    ref = round(alloc["refunds"].get(P, 0.0), 2)
    if not s:
        return {"total": ref, "by_method": {}, "students": 0, "pending": 0.0,
                "refunds": ref}
    return {"total": round(s["total"] + ref, 2),
            "by_method": {k: round(v, 2) for k, v in s["by_method"].items()},
            "students": len(s["students"]),
            "pending": round(s["pending"], 2), "refunds": ref}


# ------------------------------------------------------------ oyliklar --
_SSP_ROLES = ("examiner", "head_examiner", "support_teacher", "head_support")


def salary_rows(db: Session, user, bid, y: int, m: int) -> list:
    """Shu oyning hisoblangan oyliklari — har xodim bitta qator
    (ustoz, examiner, support, ma'muriy xodim), berilgani bilan."""
    P = _pk(y, m)
    start, end = billing.month_bounds(y, m)
    E = _E()
    people: dict = {}

    bnames = {b.id: b.name for b in db.query(models.Branch).all()}

    def person(key, name, branch, uid=None, tid=None):
        if not branch and uid:
            u_ = db.query(models.User).get(uid)
            branch = bnames.get(u_.branch_id) if u_ else None
        r = people.get(key)
        if r is None:
            r = people[key] = {"key": key, "name": name, "branch": branch,
                               "user_id": uid, "teacher_id": tid,
                               "parts": [], "accrued": 0.0}
        if tid and not r["teacher_id"]:
            r["teacher_id"] = tid
        if uid and not r["user_id"]:
            r["user_id"] = uid
        return r

    def add(r, kind, label, amount):
        amount = round(float(amount or 0), 2)
        if amount:
            r["parts"].append({"kind": kind, "label": label,
                               "amount": amount})
            r["accrued"] += amount

    # Ustozlar — yoqlamadan (filial: guruh filiali bo'yicha ulushi)
    tp = D.report_teacher_payroll(year=y, month=m, branch_id=bid, db=db,
                                  user=user)
    for row in tp.get("rows") or []:
        t = db.query(models.Teacher).get(row["teacher_id"])
        uid = t.user_id if t else None
        r = person(f"u{uid}" if uid else f"t{row['teacher_id']}",
                   row["full_name"], row.get("branch"), uid,
                   row["teacher_id"])
        add(r, "teacher", "Ustoz", row.get("amount"))

    # Examinerlar va supportlar — daraja koeffitsiyenti bilan
    if E is not None:
        ex_fn = getattr(E, "examiner_salary_v2", None)
        if ex_fn is not None:
            try:
                d = ex_fn(year=y, month=m, branch_id=bid, db=db, user=user)
                rows = E._apply_grade(db, d.get("rows") or [], "user_id")
            except HTTPException:
                rows = []
            for row in rows:
                if not row.get("user_id"):
                    continue
                r = person(f"u{row['user_id']}",
                           row.get("full_name") or row.get("name") or "—",
                           row.get("branch"), row["user_id"])
                add(r, "examiner", "Examiner", row.get("salary"))
        su_fn = getattr(E, "support_salary_v3", None)
        if su_fn is not None:
            try:
                d = su_fn(year=y, month=m, branch_id=bid, db=db, user=user)
                rows = d.get("rows") or []
            except HTTPException:
                rows = []
            for row in rows:
                uid = row.get("user_id")
                key = f"u{uid}" if uid else f"t{row.get('teacher_id')}"
                r = person(key, row.get("full_name") or row.get("name")
                           or "—", row.get("branch"), uid,
                           row.get("teacher_id"))
                add(r, "support", "Support", row.get("salary"))

    # Ma'muriy xodimlar — fiks; adminlar — fiks + KPI bonusi
    staff = F._budget_staff(db, user, None)
    if bid:
        staff = F._budget_staff_of_branch(db, staff, bid)
    kpi = {}
    try:
        res = D.compute_admin_kpi(db, user, y, m, admin_roles=(
            roles.ADMINISTRATOR, roles.SALES_MANAGER))
        kpi = {k.user_id: k for k in res.rows}
    except Exception:
        kpi = {}
    for s in staff:
        u = db.query(models.User).get(s["user_id"])
        if not u or u.role in ("examiner", "support_teacher"):
            continue
        r = person(f"u{u.id}", s["name"], s.get("branch"), u.id)
        k = kpi.get(u.id)
        if k is not None:
            add(r, "staff", "Fiks", k.fix_salary)
            add(r, "kpi", "KPI bonus",
                (k.collection_bonus or 0) + (k.new_client_bonus or 0))
        else:
            add(r, "staff", "Fiks", s.get("fix_salary"))

    # Berilgan — shu oy UCHUN (period); periodsiz yozuv — sana oyi
    SSP = getattr(models, "StaffSalaryPayment", None)
    for r in people.values():
        paid = 0.0
        if r["teacher_id"]:
            tq = db.query(models.TeacherPayment).filter(
                models.TeacherPayment.teacher_id == r["teacher_id"])
            for p in tq.all():
                pp = p.period or (p.paid_on.strftime("%Y-%m")
                                  if p.paid_on else "")
                if pp != P:
                    continue
                if bid and p.branch_id and p.branch_id != bid:
                    continue
                paid += float(p.amount or 0)
        if r["user_id"]:
            if SSP is not None:
                for p in db.query(SSP).filter(SSP.user_id == r["user_id"],
                                              SSP.period == P).all():
                    paid += float(p.amount or 0)
            eq = db.query(models.Expense).filter(
                models.Expense.staff_user_id == r["user_id"])
            for e in eq.all():
                ep = e.period or (e.date.strftime("%Y-%m") if e.date else "")
                if ep != P:
                    continue
                if bid and e.branch_id and e.branch_id != bid:
                    continue
                paid += float(e.amount or 0)
        r["accrued"] = round(r["accrued"], 2)
        r["paid"] = round(paid, 2)
        r["left"] = round(max(r["accrued"] - paid, 0.0), 2)
        r["status"] = ("paid" if r["accrued"] > 0 and paid >= r["accrued"] - 1
                       else "partial" if paid > 0 else
                       "unpaid" if r["accrued"] > 0 else "paid")
        r["roles"] = " · ".join(dict.fromkeys(x["label"] for x in r["parts"]
                                              if x["kind"] != "kpi"))
    out = [r for r in people.values() if r["accrued"] > 0 or r["paid"] > 0]
    order = {"unpaid": 0, "partial": 1, "paid": 2}
    out.sort(key=lambda r: (order[r["status"]], -r["accrued"], r["name"]))
    return out


def _month_expenses(db: Session, user, bid, y: int, m: int,
                    salary_user_ids: set) -> dict:
    """Shu oy xarajatlari (sana bo'yicha). Hisoblangan oyligi bor
    xodimga berilgan oylik xarajati bu yerga KIRMAYDI — u oyliklar
    qatorida hisoblangan summa bilan turadi (ikki marta ayirilmasin)."""
    start, end = billing.month_bounds(y, m)
    q = scope_to_branch(db.query(models.Expense), models.Expense, user,
                        bid).filter(models.Expense.date >= start,
                                    models.Expense.date <= end)
    by_cat: dict = {}
    for e in q.all():
        if e.staff_user_id and e.staff_user_id in salary_user_ids:
            continue
        by_cat[e.category] = by_cat.get(e.category, 0.0) + float(e.amount or 0)
    lines = [{"category": c, "label": roles.EXPENSE_CATEGORY_LABELS.get(c, c),
              "group": roles.EXPENSE_CATEGORY_GROUP.get(c, "other"),
              "amount": round(v, 2)}
             for c, v in sorted(by_cat.items(), key=lambda kv: -kv[1])]
    return {"total": round(sum(by_cat.values()), 2), "lines": lines}


def month_result(db: Session, user, bid, y: int, m: int,
                 alloc: dict | None = None, with_rows=True) -> dict:
    P = _pk(y, m)
    if alloc is None:
        alloc = allocate_income(db, user, bid)
    inc = _income_of(alloc, P)
    sal = salary_rows(db, user, bid, y, m)
    uids = {r["user_id"] for r in sal if r["user_id"]}
    exp = _month_expenses(db, user, bid, y, m, uids)
    s_total = round(sum(r["accrued"] for r in sal), 2)
    s_paid = round(sum(min(r["paid"], r["accrued"]) for r in sal), 2)
    out_total = round(exp["total"] + s_total, 2)
    profit = round(inc["total"] - out_total, 2)
    _s, end = billing.month_bounds(y, m)
    res = {
        "period": P, "year": y, "month": m,
        "title": f"{roles.UZ_MONTHS[m - 1].capitalize()} {y}",
        "closed": end < roles.local_today(),
        "income": inc,
        "expenses": exp,
        "salaries": {"total": s_total, "paid": s_paid,
                     "left": round(s_total - s_paid, 2),
                     "count": len(sal),
                     "unpaid_count": sum(1 for r in sal
                                         if r["status"] != "paid")},
        "outflow": out_total,
        "profit": profit,
        "margin": round(profit / inc["total"] * 100, 1)
        if inc["total"] else 0.0,
    }
    if with_rows:
        res["salary_rows"] = sal
    return res


# ------------------------------------------------------------ route'lar --
_VIEW = list(dict.fromkeys(list(roles.CASHFLOW_ACCESS)
                           + list(roles.FINANCE_ACCESS)))


@app.get("/api/month-close")
def month_close(year: int | None = None, month: int | None = None,
                branch_id: int | None = None, db: Session = Depends(get_db),
                user=Depends(require_role(*_VIEW))):
    """Pul oqimi — oy kesimida: shu oy uchun kelgan daromad, xarajatlar,
    har xodimning hisoblangan oyligi (berildi/berilmadi) va natija."""
    today = roles.local_today()
    if not year or not month:
        year, month = _prev(today.year, today.month)
    bid = _eff_bid(db, user, branch_id)
    res = month_result(db, user, bid, int(year), int(month))
    res["advance"] = allocate_income(db, user, bid)["advance"]
    res["can_pay"] = user.role in tuple(roles.SALARY_PAY)
    # Administrator (moliyaga kirmaydi) — faqat oyliklar ro'yxati:
    # foyda, daromad va xarajatlar unga ko'rinmaydi (P&L ham yopiq).
    res["limited"] = user.role not in tuple(roles.FINANCE_ACCESS)
    if res["limited"]:
        for k in ("income", "expenses", "outflow", "profit", "margin",
                  "advance"):
            res[k] = None
    res["default_pay_period"] = res["period"]
    return res


@app.get("/api/pnl")
def pnl_table(year: int | None = None, branch_id: int | None = None,
              db: Session = Depends(get_db),
              user=Depends(require_role(*roles.FINANCE_ACCESS))):
    """P&L: o'quv yili (sentabr–avgust) oyma-oy — daromad (oy kesimida),
    xarajatlar, oyliklar (hisoblangan), foyda yoki zarar."""
    today = roles.local_today()
    y0 = year or (today.year if today.month >= 9 else today.year - 1)
    bid = _eff_bid(db, user, branch_id)
    alloc = allocate_income(db, user, bid)
    rows = []
    y, m = y0, 9
    for _ in range(12):
        if billing.month_bounds(y, m)[0] > today:
            break
        r = month_result(db, user, bid, y, m, alloc, with_rows=False)
        rows.append({
            "period": r["period"], "title": r["title"], "closed": r["closed"],
            "income": r["income"]["total"],
            "pending": r["income"]["pending"],
            "expenses": r["expenses"]["total"],
            "salaries": r["salaries"]["total"],
            "salaries_left": r["salaries"]["left"],
            "outflow": r["outflow"], "profit": r["profit"],
            "margin": r["margin"],
        })
        y, m = _next(y, m)
    keys = ("income", "pending", "expenses", "salaries", "salaries_left",
            "outflow", "profit")
    tot = {k: round(sum(r[k] for r in rows), 2) for k in keys}
    tot["margin"] = (round(tot["profit"] / tot["income"] * 100, 1)
                     if tot["income"] else 0.0)
    return {"year": y0, "year_label": roles.plan_year_label(y0),
            "rows": rows, "totals": tot, "advance": alloc["advance"]}


@app.post("/api/month-close/pay")
def month_close_pay(payload: dict = Body(...), db: Session = Depends(get_db),
                    user=Depends(require_role(*roles.SALARY_PAY))):
    """Oy kesimidagi ro'yxatdan oylik berish. Pul QAYSI OY UCHUN
    berilgani (period) bilan yoziladi — o'sha oy qatori yopiladi.

    Qayerga yoziladi (Payroll bo'limidagi bilan bir xil joy):
      ustoz -> TeacherPayment; examiner/support -> StaffSalaryPayment;
      boshqa xodim -> Xarajat (Ma'muriy xodim oyligi)."""
    P = F._valid_period(payload.get("period"))
    key = str(payload.get("key") or "")
    try:
        amount = float(payload.get("amount") or 0)
    except (TypeError, ValueError):
        amount = 0
    if not P or amount <= 0 or len(key) < 2:
        raise HTTPException(400, "Oy, xodim va summani to'g'ri kiriting")
    method = payload.get("method") or "cash"
    if method not in roles.PAYMENT_METHODS:
        method = "cash"
    try:
        on = date.fromisoformat(payload.get("date") or "")
    except ValueError:
        on = roles.local_today()
    note = (payload.get("note") or "").strip() or None
    bid = payload.get("branch_id") or None
    via = f"Pul oqimi > {P} oyliklari"

    if key[0] == "t":
        return F._pay_teacher(db, user, int(key[1:]), amount=amount, on=on,
                              method=method, note=note, period=P, via=via,
                              branch_id=bid)
    if key[0] != "u":
        raise HTTPException(400, "Noto'g'ri xodim")
    su = db.query(models.User).get(int(key[1:]))
    if not su:
        raise HTTPException(404, "Xodim topilmadi")
    C._check_pay_scope(db, user, staff_user=su)
    t = (db.query(models.Teacher)
         .filter(models.Teacher.user_id == su.id).first())
    if su.role in _SSP_ROLES:
        SSP = models.StaffSalaryPayment
        p = SSP(user_id=su.id, amount=amount, kind="salary", period=P,
                paid_on=on, method=method, note=note,
                created_by=user.full_name)
        db.add(p); db.commit()
        audit.log(db, user, entity="user", action="salary_change",
                  entity_id=su.id, entity_label=su.full_name,
                  field="Oylik", new_value=f"{amount:,.0f}".replace(",", " "),
                  note=via, commit=True)
        return {"ok": True, "to": "staff_salary", "id": p.id}
    if t is not None:
        return F._pay_teacher(db, user, t.id, amount=amount, on=on,
                              method=method, note=note, period=P, via=via,
                              branch_id=bid)
    if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
        allowed = C._user_branch_ids(db, user)
        br = int(bid) if bid and int(bid) in allowed else user.branch_id
    else:
        br = int(bid) if bid else su.branch_id
    e = models.Expense(
        date=on, category="admin_salary", amount=amount,
        note=f"{su.full_name or su.username} — oylik ({P})"
             + (f" · {note}" if note else ""),
        branch_id=br, method=method, staff_user_id=su.id, period=P,
        created_by=user.full_name)
    db.add(e); db.commit()
    audit.log(db, user, entity="expense", action="create", entity_id=e.id,
              entity_label=e.note, new_value=f"{amount:,.0f}".replace(",", " "),
              note=via, commit=True)
    return {"ok": True, "to": "expense", "id": e.id}
