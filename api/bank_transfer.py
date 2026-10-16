"""TERMINAL ↔ NAQD O'TKAZMASI (2026-10-16).

Jahongir: terminal (bank) hisobidagi pulni naqdga yechganda bank 1%
komissiya oladi — naqd kassaga sof summa o'zi tushsin; naqdni terminalga
(bankka) topshirish esa to'liq avtomat, komissiyasiz. Keyinroq: "o'quv
markazda ... yechilmaydi, uni olib tashla" — ya'ni faqat shu ikki tur bor,
egasiga foyda yechish turi YO'Q.

Ikki tur:
  withdraw (W) — "Terminaldan naqd yechish": filial, sana, yalpi summa,
      izoh. komissiya = summa × foiz (sozlamada, standart 1%); terminal
      −summa, naqd +sof (sof = summa − komissiya). Komissiya — haqiqiy
      xarajat: BITTA Expense qatori ("Bank komissiyasi (1%)", terminaldan),
      P&L uni bir marta ko'radi. Sof harakatning o'zi daromad ham, xarajat
      ham emas.
  deposit (D) — "Naqdni terminalga topshirish": naqd −summa, terminal
      +summa; P&L ga ta'siri yo'q, komissiya yo'q.

Qoldiq hisoblari (oy boshidagi qoldiq, kassa daftari, kun kassasi)
dashboard.py dagi _bank_moves/_bt_moves orqali o'qiydi — bitta joy.

Huquqlar: kiritish va ko'rish — Pul oqimi bilan bir xil
(roles.BANK_TRANSFER_ACCESS), administrator faqat o'z filialida.
Tahrirlash, o'chirish va qoldiqdan oshiq summani "baribir saqlash" —
roles.BANK_TRANSFER_MANAGE (asoschi/moliya). Foizni o'zgartirish —
roles.BANK_FEE_RATE_EDIT. Har bir yaratish/o'zgartirish/o'chirish
auditga yoziladi.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import date, datetime, timedelta

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session

import audit
import billing
import models
import roles
from auth import has_role, require_role
from database import get_db
from common import _in_user_branches, aggregate_skip_ids, blocked_branch_ids
import dashboard as D

router = APIRouter()

FEE_KEY = "bank_withdraw_fee_percent"
KINDS = tuple(k for k, _ in roles.BANK_TRANSFER_KINDS)


# ------------------------------------------------------------ sozlama ---
def fee_percent(db: Session) -> float:
    """Joriy komissiya foizi (1.0 = 1%). Sozlama bo'lmasa — standart."""
    v = roles.BANK_WITHDRAW_FEE_DEFAULT
    try:
        row = db.query(models.IntegrationSetting).get(FEE_KEY)
        if row is not None and (row.value or "").strip():
            v = float(row.value)
    except (TypeError, ValueError):
        v = roles.BANK_WITHDRAW_FEE_DEFAULT
    return max(0.0, min(float(v), roles.BANK_WITHDRAW_FEE_MAX))


def _calc(kind: str, amount: float, rate: float) -> tuple:
    """(komissiya, sof). Faqat withdraw da komissiya bor."""
    if kind == "withdraw":
        fee = round(amount * rate / 100.0, 2)
        return fee, round(amount - fee, 2)
    return 0.0, round(amount, 2)


def _methods(kind: str) -> tuple:
    return ("terminal", "cash") if kind == "withdraw" else ("cash", "terminal")


# ------------------------------------------------------------- qoldiq ---
class _BranchViewer:
    """Bitta filial qoldig'ini ANIQ hisoblash uchun ichki ko'ruvchi.

    Kiruvchi xodimning filial huquqi alohida tekshiriladi
    (_branch_open); bu yerda esa ko'p filialli administrator
    yoki "barcha filiallar" rejimi tufayli boshqa filial raqami
    aralashib ketmasin — Pul oqimidagi qoldiq bilan aynan bir xil
    so'rovlar, faqat shu filial uchun."""

    def __init__(self, branch_id):
        self.role = roles.FOUNDER
        self.branch_id = branch_id
        self.id = None
        self.username = self.full_name = "kassa-qoldiq"


def branch_balance(db: Session, branch_id: int, on: date) -> dict:
    """`on` kuni OXIRIDAGI qoldiq usullar bo'yicha (CF_OPENING_FROM dan).
    `on` undan oldin bo'lsa qoldiq yuritilmagan — None."""
    if on < D.CF_OPENING_FROM:
        return None
    return D._cf_opening(db, _BranchViewer(branch_id), branch_id,
                         on + timedelta(days=1))


def _branch_open(db: Session, user, bid) -> bool:
    """Bu xodim shu filialda o'tkazma kiritib, qoldig'ini ko'rib, keyin
    uni ro'yxatda topa oladimi (2026-10-16 ko'rik).

    _BranchViewer qoldiqni asoschi nomidan hisoblaydi, shuning uchun
    huquq shu yerda — scope_to_branch qoidasi bilan bir xil:
      - hamkor markaz (Stech) o'z filiali bo'lmasa asoschidan boshqa
        hammaga yopiq (blocked_branch_ids) — moliya direktori va
        buxgalter uning naqd/terminal qoldig'ini ko'rmasin, unga
        kiritmasin;
      - filialga bog'langan xodimga ro'yxat "barcha filiallar"
        yig'indisidan chiqarilgan begona filialni (test/hamkor)
        ko'rsatmaydi — u yerga kiritilgan o'tkazmani keyin topib
        tuzatib bo'lmasdi, shuning uchun kiritish ham yopiq.
    Butun tashkilotni ko'radigan rol filialni tanlasa, ro'yxat uni
    ko'rsatadi (dashboard._bank_moves)."""
    if not _in_user_branches(db, user, bid):
        return False
    if bid in blocked_branch_ids(db, user):
        return False
    if (user.role not in tuple(roles.ORG_WIDE_ROLES)
            and bid in aggregate_skip_ids(db, user)):
        return False
    return True


def _low_point(db: Session, branch_id: int, on: date, src: str,
               give_back: float = 0.0, give_back_from: date | None = None):
    """`src` usulining `on` kunidan BUGUNgacha har kun oxiridagi ENG KAM
    qoldig'i: (summa, kun). `on` CF_OPENING_FROM dan oldin — None
    (qoldiq yuritilmagan).

    2026-10-16 ko'rik: avval faqat `on` kuni oxiri tekshirilardi — o'tgan
    sana tanlansa keyin kiritilgan chiqimlar hisobga olinmay, keyingi
    kunlar va oylar qoldig'i minusga tushardi. Yangi o'tkazma `on` dan
    boshlab har kunni kamaytiradi, shuning uchun eng kam nuqta muhim.
    give_back — tahrirlanayotgan yozuvning o'z eski ta'siri: u
    give_back_from kunidan boshlab qoldiqda allaqachon ayirilgan."""
    bal = branch_balance(db, branch_id, on)
    if bal is None:
        return None

    def back(d):
        return (give_back if give_back_from is not None
                and d >= give_back_from else 0.0)

    run = float(bal.get(src, 0.0))
    low, low_day = run + back(on), on
    today = roles.local_today()
    if today > on:
        moves = D._cf_day_moves(db, _BranchViewer(branch_id), branch_id,
                                on + timedelta(days=1), today)
        for d in sorted(moves):
            run += moves[d].get(src, 0.0)
            if run + back(d) < low - 0.005:
                low, low_day = run + back(d), d
    return round(low, 2), low_day


def _check_balance(db: Session, user, *, kind: str, branch_id: int,
                   on: date, amount: float, force: bool,
                   give_back: float = 0.0,
                   give_back_from: date | None = None) -> bool:
    """Qoldiqdan oshiq summa — aniq o'zbekcha 400 (ogohlantirish).
    Qoldiq — `on` kunidan bugungacha eng kam qoldiq (_low_point).
    Rahbariyat/moliya force bilan tasdiqlasa o'tadi (True qaytadi —
    "majburan saqlandi" belgisi)."""
    src = _methods(kind)[0]
    lp = _low_point(db, branch_id, on, src, give_back, give_back_from)
    if lp is None:
        return False
    avail, low_day = lp
    if amount <= avail + 0.005:
        return False
    can_force = has_role(user, roles.BANK_TRANSFER_MANAGE)
    if force:
        if can_force:
            return True
        raise HTTPException(403, "Qoldiqdan oshiq summani faqat rahbariyat "
                                 "(asoschi yoki moliya) tasdiqlay oladi")
    src_lbl = "Terminalda" if src == "terminal" else "Naqd kassada"
    act = ("yechib" if kind == "withdraw" else "terminalga topshirib")
    limited = D._cashflow_limited(db, user)
    if limited:
        # Cheklangan filial administratoriga kassa qoldig'i ko'rsatilmaydi
        msg = (f"{src_lbl} {on.strftime('%d.%m.%Y')} holatiga yetarli pul "
               f"yo'q — {D._fmt_som(amount)} so'm {act} bo'lmaydi. "
               "Rahbariyatga murojaat qiling.")
    else:
        if low_day == on:
            msg = (f"{src_lbl} {on.strftime('%d.%m.%Y')} holatiga "
                   f"{D._fmt_som(avail)} so'm bor — {D._fmt_som(amount)} "
                   f"so'm {act} bo'lmaydi.")
        else:
            # Orqa sana: eng kam qoldiq keyingi kunda — keyin kiritilgan
            # chiqimlar tufayli (2026-10-16 ko'rik)
            low_s = low_day.strftime('%d.%m.%Y')
            msg = (f"{src_lbl} {low_s} holatiga (keyingi chiqimlardan "
                   f"so'ng) {D._fmt_som(avail)} so'm qoladi — "
                   f"{on.strftime('%d.%m.%Y')} sanasi bilan "
                   f"{D._fmt_som(amount)} so'm {act} bo'lmaydi, aks holda "
                   f"{low_s} holatiga qoldiq minusga tushadi.")
        msg += (" Baribir saqlash kerak bo'lsa — «Baribir saqlash»ni bosing."
                if can_force else
                " Baribir saqlash kerak bo'lsa — rahbariyat (asoschi yoki "
                "moliya) tasdiqlaydi.")
    raise HTTPException(400, {
        "message": msg, "code": "balance_low", "can_force": can_force,
        "problems": [],
        "method": src, "available": None if limited else avail,
        "low_date": None if limited else low_day.isoformat(),
    })


# -------------------------------------------------------------- yordam --
def _out(t: models.BankCashTransfer, branches: dict | None = None) -> dict:
    bname = None
    if branches is not None:
        bname = branches.get(t.branch_id)
    elif t.branch is not None:
        bname = t.branch.name
    return {
        "id": t.id,
        "kind": t.kind,
        "kind_label": roles.BANK_TRANSFER_KIND_LABELS.get(t.kind, t.kind),
        "date": t.date.isoformat() if t.date else None,
        "branch_id": t.branch_id,
        "branch": bname,
        "amount": t.amount,
        "fee_rate": t.fee_rate,
        "fee": t.fee,
        "net": t.net,
        "from_method": t.from_method,
        "to_method": t.to_method,
        "note": t.note,
        "title": D._bt_title(t),
        "forced": bool(t.forced),
        "fee_expense_id": t.fee_expense_id,
        "created_by": t.created_by,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "updated_by": t.updated_by,
        "updated_at": t.updated_at.isoformat() if t.updated_at else None,
    }


def _amount(raw) -> float:
    try:
        amt = round(float(str(raw).replace(" ", "").replace(",", "")), 2)
    except (TypeError, ValueError):
        raise HTTPException(400, "Summa noto'g'ri")
    if amt <= 0:
        raise HTTPException(400, "Summa noldan katta bo'lishi kerak")
    return amt


def _date(raw, user, db) -> date:
    try:
        d = date.fromisoformat(raw) if raw else roles.local_today()
    except (TypeError, ValueError):
        raise HTTPException(400, "Sana noto'g'ri (YYYY-MM-DD)")
    if d > roles.local_today():
        raise HTTPException(400, "Kelajakdagi sana bilan kiritib bo'lmaydi")
    # Cheklangan filial administratori faqat BUGUNni ko'radi (2026-10-06)
    if D._cashflow_limited(db, user) and d != roles.local_today():
        raise HTTPException(400, "Bu filialda faqat bugungi sana bilan "
                                 "kiritiladi")
    return d


def _fee_note(t) -> str:
    return (f"Bank komissiyasi {float(t.fee_rate or 0):g}% — terminaldan "
            f"naqdga {D._fmt_som(t.amount)}"
            + (f" · {t.note}" if t.note else ""))


def _drop_fee_expense(db: Session, user, exp, action_note: str):
    audit.log(db, user, entity="expense", action="delete",
              entity_id=exp.id, entity_label=exp.note,
              field=exp.category, old_value=exp.amount,
              branch_id=exp.branch_id, note=action_note)
    db.delete(exp)


def _sync_fee_expense(db: Session, user, t, *, action_note: str):
    """Komissiya xarajatini o'tkazma bilan moslaydi: bor bo'lsa summa/
    sana/izoh yangilanadi, komissiya 0 bo'lsa o'chiriladi, yo'q bo'lsa
    yaratiladi. Har o'zgarish auditga."""
    exp = (db.query(models.Expense).get(t.fee_expense_id)
           if t.fee_expense_id else None)
    fee = round(float(t.fee or 0), 2)
    if fee <= 0:
        # Avval bog'lanish uziladi (flush), keyin xarajat o'chadi —
        # Postgres FK (fee_expense_id -> expenses.id) buzilmasin.
        t.fee_expense_id = None
        db.flush()
        if exp is not None:
            _drop_fee_expense(db, user, exp, action_note)
        return
    if exp is None:
        exp = models.Expense(
            date=t.date, category="bank_fee", amount=fee, method="terminal",
            note=_fee_note(t), branch_id=t.branch_id,
            created_by=user.full_name or user.username)
        db.add(exp)
        db.flush()
        t.fee_expense_id = exp.id
        audit.log(db, user, entity="expense", action="create",
                  entity_id=exp.id, entity_label=exp.note,
                  field="bank_fee", new_value=fee, branch_id=exp.branch_id,
                  note=action_note)
        return
    changes = {"amount": fee, "date": t.date, "note": _fee_note(t),
               "method": "terminal", "branch_id": t.branch_id,
               "category": "bank_fee"}
    audit.log_changes(db, user, entity="expense", obj=exp, changes=changes,
                      label_attr="note", note=action_note)
    for k, v in changes.items():
        setattr(exp, k, v)


def _in_scope(db: Session, tid: int, user) -> models.BankCashTransfer:
    t = db.query(models.BankCashTransfer).get(tid)
    if not t:
        raise HTTPException(404, "O'tkazma topilmadi")
    if not _branch_open(db, user, t.branch_id):
        raise HTTPException(403, "Bu o'tkazma boshqa filialga tegishli")
    return t


def _flags(db: Session, user) -> dict:
    return {
        "can_manage": has_role(user, roles.BANK_TRANSFER_MANAGE),
        "can_force": has_role(user, roles.BANK_TRANSFER_MANAGE),
        "can_edit_rate": has_role(user, roles.BANK_FEE_RATE_EDIT),
    }


# ------------------------------------------------------------ route'lar --
@router.get("/api/bank-transfers")
def list_bank_transfers(
    year: int | None = None,
    month: int | None = None,
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.BANK_TRANSFER_ACCESS)),
):
    """Bir oylik Terminal ↔ naqd o'tkazmalari (eng yangisi tepada).
    Cheklangan filial administratori — faqat bugungilar."""
    today = roles.local_today()
    if D._cashflow_limited(db, user):
        start = end = today
    else:
        y, m = year or today.year, month or today.month
        if not 1 <= m <= 12:
            raise HTTPException(400, "Oy noto'g'ri")
        start, end = billing.month_bounds(y, m)
    branches = {b.id: b.name for b in db.query(models.Branch).all()}
    items = sorted(D._bank_moves(db, user, branch_id, start, end),
                   key=lambda t: (t.date, t.id), reverse=True)
    rows = [_out(t, branches) for t in items]
    w = [r for r in rows if r["kind"] == "withdraw"]
    dep = [r for r in rows if r["kind"] == "deposit"]
    return {
        "period": f"{start.year:04d}-{start.month:02d}",
        "rows": rows,
        "totals": {
            "withdraw": round(sum(r["amount"] for r in w), 2),
            "withdraw_fee": round(sum(r["fee"] for r in w), 2),
            "withdraw_net": round(sum(r["net"] for r in w), 2),
            "deposit": round(sum(r["amount"] for r in dep), 2),
        },
        "fee_percent": fee_percent(db),
        "kinds": [{"key": k, "label": lbl}
                  for k, lbl in roles.BANK_TRANSFER_KINDS],
        **_flags(db, user),
    }


@router.get("/api/bank-transfers/settings")
def bank_transfer_settings(
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.BANK_TRANSFER_ACCESS)),
):
    return {"fee_percent": fee_percent(db),
            "default_percent": roles.BANK_WITHDRAW_FEE_DEFAULT,
            "max_percent": roles.BANK_WITHDRAW_FEE_MAX,
            **_flags(db, user)}


@router.put("/api/bank-transfers/settings")
def set_bank_transfer_settings(
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.BANK_FEE_RATE_EDIT)),
):
    """Komissiya foizini o'zgartirish — faqat KEYINGI o'tkazmalarga
    ta'sir qiladi (har yozuv o'z foizini saqlaydi)."""
    try:
        v = round(float((payload or {}).get("fee_percent")), 4)
    except (TypeError, ValueError):
        raise HTTPException(400, "Foiz noto'g'ri")
    if v < 0 or v > roles.BANK_WITHDRAW_FEE_MAX:
        raise HTTPException(
            400, f"Foiz 0 dan {roles.BANK_WITHDRAW_FEE_MAX:g} gacha bo'lsin")
    old = fee_percent(db)
    row = db.query(models.IntegrationSetting).get(FEE_KEY)
    if row is None:
        row = models.IntegrationSetting(key=FEE_KEY)
        db.add(row)
    row.value = f"{v:g}"
    row.updated_by = user.full_name or user.username
    row.updated_at = datetime.utcnow()
    audit.log(db, user, entity="settings", action="update", entity_id=0,
              entity_label="Terminaldan naqd yechish",
              field="Bank komissiyasi foizi", old_value=f"{old:g}%",
              new_value=f"{v:g}%")
    db.commit()
    return {"fee_percent": fee_percent(db), **_flags(db, user)}


@router.get("/api/bank-transfers/balance")
def bank_transfer_balance(
    branch_id: int | None = None,
    day: str | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.BANK_TRANSFER_ACCESS)),
):
    """Formada ko'rsatish uchun: shu filialda shu kun oxiridagi naqd va
    terminal qoldig'i. Cheklangan filial administratoriga yopiq."""
    D._deny_if_cashflow_limited(db, user)
    bid = branch_id or user.branch_id
    if not bid:
        return {"tracked": False, "cash": None, "terminal": None}
    if not _branch_open(db, user, bid):
        raise HTTPException(403, "Bu filial qoldig'ini ko'rish huquqi yo'q")
    try:
        on = date.fromisoformat(day) if day else roles.local_today()
    except ValueError:
        raise HTTPException(400, "Sana noto'g'ri (YYYY-MM-DD)")
    bal = branch_balance(db, bid, on)
    if bal is None:
        return {"tracked": False, "cash": None, "terminal": None}
    return {"tracked": True, "date": on.isoformat(), "branch_id": bid,
            "cash": bal.get("cash", 0.0), "terminal": bal.get("terminal", 0.0)}


@router.post("/api/bank-transfers")
def create_bank_transfer(
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.BANK_TRANSFER_ACCESS)),
):
    payload = payload or {}
    kind = payload.get("kind")
    if kind not in KINDS:
        raise HTTPException(400, "Noto'g'ri o'tkazma turi — faqat "
                                 "«Terminaldan naqd yechish» yoki «Naqdni "
                                 "terminalga topshirish»")
    amount = _amount(payload.get("amount"))
    on = _date(payload.get("date"), user, db)
    note = (str(payload.get("note") or "").strip() or None)
    bid = payload.get("branch_id")
    if bid in ("", 0, None):
        bid = user.branch_id
    if not bid:
        raise HTTPException(400, "Filialni tanlang")
    try:
        bid = int(bid)
    except (TypeError, ValueError):
        raise HTTPException(400, "Filial noto'g'ri")
    if not db.query(models.Branch).get(bid):
        raise HTTPException(404, "Filial topilmadi")
    if not _branch_open(db, user, bid):
        raise HTTPException(403, "Bu filialga kiritish huquqi yo'q")

    forced = _check_balance(db, user, kind=kind, branch_id=bid, on=on,
                            amount=amount, force=bool(payload.get("force")))
    rate = fee_percent(db) if kind == "withdraw" else 0.0
    fee, net = _calc(kind, amount, rate)
    src, dst = _methods(kind)
    who = user.full_name or user.username
    t = models.BankCashTransfer(
        kind=kind, date=on, branch_id=bid, amount=amount, fee_rate=rate,
        fee=fee, net=net, from_method=src, to_method=dst, note=note,
        forced=1 if forced else None, created_by=who)
    db.add(t)
    db.flush()
    _sync_fee_expense(db, user, t, action_note=f"Terminal ↔ naqd o'tkazmasi #{t.id}")
    audit.log(db, user, entity="bank_transfer", action="create",
              entity_id=t.id, entity_label=D._bt_title(t), field=kind,
              new_value=amount, branch_id=bid,
              note=(f"komissiya {rate:g}% = {D._fmt_som(fee)}, sof "
                    f"{D._fmt_som(net)}"
                    + ("; qoldiqdan oshiq — rahbariyat tasdig'i bilan"
                       if forced else "")))
    db.commit()
    db.refresh(t)
    return _out(t)


@router.put("/api/bank-transfers/{tid}")
def update_bank_transfer(
    tid: int,
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.BANK_TRANSFER_MANAGE)),
):
    """Summa, sana, izoh. Foiz — yozuvning O'Z foizi (sozlama keyin
    o'zgargan bo'lsa ham). Turi va filiali o'zgarmaydi."""
    payload = payload or {}
    t = _in_scope(db, tid, user)
    if "kind" in payload and payload.get("kind") != t.kind:
        raise HTTPException(400, "O'tkazma turini o'zgartirib bo'lmaydi — "
                                 "o'chirib, qaytadan kiriting")
    if payload.get("branch_id") not in (None, "", t.branch_id):
        raise HTTPException(400, "Filialni o'zgartirib bo'lmaydi — "
                                 "o'chirib, qaytadan kiriting")
    new_amount = (_amount(payload["amount"]) if "amount" in payload
                  else t.amount)
    new_date = (_date(payload.get("date"), user, db) if "date" in payload
                else t.date)
    new_note = ((str(payload.get("note") or "").strip() or None)
                if "note" in payload else t.note)
    forced = bool(t.forced)
    if new_amount != t.amount or new_date != t.date:
        # Eski yozuvning o'z ta'siri (terminal/naqddan −summa) qoldiqda
        # o'z sanasidan boshlab allaqachon ayirilgan — o'sha kundan
        # qaytaramiz (2026-10-16 ko'rik: endi bugungacha har kun).
        forced = _check_balance(
            db, user, kind=t.kind, branch_id=t.branch_id, on=new_date,
            amount=new_amount, force=bool(payload.get("force")),
            give_back=float(t.amount or 0),
            give_back_from=(t.date if t.date and t.date >= D.CF_OPENING_FROM
                            else None))
    fee, net = _calc(t.kind, new_amount, float(t.fee_rate or 0))
    changes = {"amount": new_amount, "date": new_date, "note": new_note,
               "fee": fee, "net": net}
    old_title = D._bt_title(t)
    n = 0
    for k, v in changes.items():
        old = getattr(t, k, None)
        if audit._fmt(old) == audit._fmt(v):
            continue
        audit.log(db, user, entity="bank_transfer", action="update",
                  entity_id=t.id, entity_label=old_title, field=k,
                  old_value=old, new_value=v, branch_id=t.branch_id,
                  note=("qoldiqdan oshiq — rahbariyat tasdig'i bilan"
                        if forced and k == "amount" else None))
        setattr(t, k, v)
        n += 1
    t.forced = 1 if forced else None
    if n:
        t.updated_by = user.full_name or user.username
        t.updated_at = datetime.utcnow()
    _sync_fee_expense(db, user, t,
                      action_note=f"Terminal ↔ naqd o'tkazmasi #{t.id} tahrirlandi")
    db.commit()
    db.refresh(t)
    return _out(t)


@router.delete("/api/bank-transfers/{tid}")
def delete_bank_transfer(
    tid: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.BANK_TRANSFER_MANAGE)),
):
    """O'tkazma va uning komissiya xarajati birga o'chadi (auditda
    qoladi) — naqd/terminal qoldig'i va P&L o'zi to'g'rilanadi."""
    t = _in_scope(db, tid, user)
    tid_, title = t.id, D._bt_title(t)
    exp = (db.query(models.Expense).get(t.fee_expense_id)
           if t.fee_expense_id else None)
    audit.log(db, user, entity="bank_transfer", action="delete",
              entity_id=tid_, entity_label=title, field=t.kind,
              old_value=t.amount, branch_id=t.branch_id,
              note=(f"sana {t.date.isoformat() if t.date else '—'}, "
                    f"komissiya {D._fmt_som(t.fee)}"
                    + (f"; izoh: {t.note}" if t.note else "")))
    # Avval o'tkazma (u xarajatga FK bilan bog'langan), keyin komissiyasi
    db.delete(t)
    db.flush()
    if exp is not None:
        _drop_fee_expense(db, user, exp,
                          f"Terminal ↔ naqd o'tkazmasi #{tid_} o'chirildi")
    db.commit()
    return {"ok": True}
