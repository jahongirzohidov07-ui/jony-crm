"""GURUH BO'YICHA MUZLATISH (2026-10-16).

Jahongir: "2ta guruhi bor o'quvchini bir guruhini muzlatsa ikkinchisi
ham muzlayabdi, ikkalasi alohida alohida muzlatish kerak, funksiyalar
2ta guruhda alohida".

Ilgari muzlatish faqat O'QUVCHI darajasida edi (Student.status =
"frozen") — bitta guruhni to'xtatsa ikkinchisi ham to'xtardi. Endi
bog'lanishning o'z holati bor: StudentGroupLink.status = "frozen".

QOIDA:
  * Faqat FAOL o'quvchida, va boshqa kamida bitta FAOL (pul
    yechiladigan) guruhi qolsagina. Yagona guruh bo'lsa — butun
    o'quvchi muzlatiladi (eski "Muzlatish" menyusi).
  * Muzlagan guruh: ro'yxat/davomat/baholarda chiqmaydi
    (common.in_group, entry._mgx_group_students), pul yechmaydi va
    2-fan 10% ga kirmaydi (common._paid_link_filter).
  * Shu oy hisobi: muzlagan kundan OLDINGI darslar qoladi, qolgani
    tushiriladi (faqat kamaytiradi, audit bilan). Asosiy guruh
    muzlasa — asosiy belgisi boshqa faol guruhga o'tadi: eski asosiy
    qator "#g<eski>" ga, yangi asosiyning "#g" qatori oddiy oylikka
    aylanadi (multi_subject.on_group_removed bilan bir xil).
  * Faollashtirish: tanlangan kundan oy oxirigacha shu guruh darslari
    (multi_subject.topup_extra / charge_extra), keyingi oylar odatdagidek.
  * Qatorlar o'chirilmaydi.
"""
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
import roles
from auth import require_role
from database import get_db

router = APIRouter()

FROZEN = "frozen"


def _ms():
    import multi_subject as MS
    return MS


def _status(ln) -> str:
    return (getattr(ln, "status", None) or "active")


def paid_others(db, s, gid: int) -> list:
    """Shu guruhdan boshqa FAOL (sinovda ham, muzlagan ham emas)
    ochiq guruhlar."""
    rows = (db.query(models.StudentGroupLink)
            .filter(models.StudentGroupLink.student_id == s.id,
                    models.StudentGroupLink.active == 1,
                    models.StudentGroupLink.group_id != int(gid))
            .order_by(models.StudentGroupLink.is_primary.desc(),
                      models.StudentGroupLink.id).all())
    return [l for l in rows if _status(l) not in ("trial", FROZEN)]


def check_freeze(db, s, ln, frm: date, today: date) -> str | None:
    if ln is None or not ln.active:
        return "O'quvchi bu guruhda emas"
    if _status(ln) == FROZEN:
        return "Bu guruh allaqachon muzlatilgan"
    if s.status != "active":
        return ("O'quvchi hozir faol emas — guruh bo'yicha muzlatish faqat "
                "faol o'quvchida")
    if not paid_others(db, s, ln.group_id):
        return ("Bu o'quvchining yagona faol guruhi. Butun o'quvchini "
                "muzlating (⋮ menyu → Muzlatish).")
    if frm > today:
        return "Kelajakdagi sanani tanlab bo'lmaydi"
    if frm < today.replace(day=1):
        return "Muzlatish sanasi joriy oy ichida bo'lsin"
    if ln.joined_date and frm < ln.joined_date:
        return (f"Guruhga qo'shilgan sanadan ({ln.joined_date.isoformat()})"
                " oldin bo'lmaydi")
    return None


def _cut_row_before(db, s, row, g, frm: date, since: date,
                    primary: bool, why: str, unit: float = None) -> bool:
    """Qatorni frm dan OLDINGI darslarga tushiradi (faqat kamaytiradi).
    unit — bitta dars narxi; holat o'zgarishidan OLDIN hisoblab beriladi
    (aks holda 2-fan 10% to'xtab, dars narxi qimmatlashib ketardi)."""
    import re
    MS = _ms()
    m = re.search(r"\[oldin:(\d+)\]", row.note or "")
    if unit is None:
        unit = MS._unit_of(db, s, g, row, primary=primary)
    return MS._cut(db, s, row, g, since, frm - timedelta(days=1),
                   unit, why, prior=int(m.group(1)) if m else 0)


def cut_before(db, s, ln, row, today: date) -> bool:
    """Kunlik (multi_subject.daily): muzlagan guruhning shu oy "#g"
    qatori muzlagan kundan oldingi darslardan oshmasin."""
    MS = _ms()
    g = db.query(models.Group).get(ln.group_id)
    if g is None:
        return False
    month0 = today.replace(day=1)
    frm = ln.frozen_from or today
    if frm < month0:
        frm = month0
    since = MS._since(ln, month0)
    return _cut_row_before(db, s, row, g, frm, since, False, "muzlatildi")


def freeze_link(db, s, ln, frm: date, until: date = None,
                note: str = None, user=None, auto: bool = False) -> dict:
    """Faqat shu guruhni muzlatadi. Chaqiruvchi commit qiladi."""
    import audit
    import common as C
    MS = _ms()
    g = db.query(models.Group).get(ln.group_id)
    period = MS._period(frm)
    month0 = frm.replace(day=1)
    was_primary = (s.group_id == ln.group_id)
    was_trial = _status(ln) == "trial"
    # Dars narxi holat o'zgarishidan OLDIN (chegirma hali amalda)
    pre_row = (MS._row(db, s.id, period) if was_primary
               else MS._row(db, s.id, MS.key(period, ln.group_id)))
    pre_unit = (MS._unit_of(db, s, g, pre_row, primary=was_primary)
                if (pre_row is not None and g is not None) else None)
    ln.status = FROZEN
    ln.frozen_from = frm
    ln.frozen_until = until
    ln.frozen_note = (note or "").strip() or None
    moved_to = None
    if was_primary:
        ln.is_primary = 0
        others = paid_others(db, s, ln.group_id)
        if others:
            others[0].is_primary = 1
            moved_to = others[0].group_id
    db.flush()
    C.sync_primary_group(db, s)
    db.flush()
    cut = None
    if not was_trial and g is not None:
        if was_primary:
            prim = MS._row(db, s.id, period)
            if prim is not None:
                old = abs(prim.amount or 0)
                _cut_row_before(db, s, prim, g, frm, month0, True,
                                "shu guruh muzlatildi", unit=pre_unit)
                cut = {"old": old, "new": abs(prim.amount or 0)}
                prim.period = MS.key(period, g.id)
            if s.group_id and s.group_id != g.id:
                nr = MS._row(db, s.id, MS.key(period, s.group_id))
                if nr is not None:
                    nr.period = period
        else:
            row = MS._row(db, s.id, MS.key(period, g.id))
            if row is not None:
                old = abs(row.amount or 0)
                _cut_row_before(db, s, row, g, frm, MS._since(ln, month0),
                                False, "shu guruh muzlatildi",
                                unit=pre_unit)
                cut = {"old": old, "new": abs(row.amount or 0)}
    db.flush()
    audit.log(db, user, entity="student",
              action="auto_freeze" if auto else "update",
              entity_id=s.id, entity_label=s.full_name,
              field="Guruh muzlatildi", new_value=g.name if g else None,
              note=(f"Faqat shu guruh, {frm.isoformat()} dan"
                    + (f", {until.isoformat()} gacha" if until else "")
                    + (f". {ln.frozen_note}" if ln.frozen_note else "")
                    + (f". Shu oy hisobi: {int(cut['old'])} -> "
                       f"{int(cut['new'])}" if cut else "")),
              branch_id=s.branch_id)
    return {"group_id": ln.group_id, "group": g.name if g else None,
            "frozen_from": frm.isoformat(),
            "frozen_until": until.isoformat() if until else None,
            "primary_moved_to": moved_to, "charge": cut}


def check_unfreeze(db, s, ln, on: date, today: date) -> str | None:
    if ln is None or not ln.active:
        return "O'quvchi bu guruhda emas"
    if _status(ln) != FROZEN:
        return "Bu guruh muzlatilmagan"
    if s.status != "active":
        return ("O'quvchi hozir faol emas — avval o'quvchini "
                "faollashtiring")
    if on > today:
        return "Kelajakdagi sanani tanlab bo'lmaydi"
    if on < today.replace(day=1):
        return "Faollashtirish sanasi joriy oy ichida bo'lsin"
    if ln.frozen_from and on < ln.frozen_from:
        return (f"Muzlatilgan sanadan ({ln.frozen_from.isoformat()}) "
                "oldin bo'lmaydi")
    return None


def unfreeze_link(db, s, ln, on: date, user=None) -> dict:
    """Muzlagan guruhni faollashtiradi va shu kundan oy oxirigacha
    darslar uchun hisob yozadi. Chaqiruvchi commit qiladi."""
    import audit
    import common as C
    MS = _ms()
    g = db.query(models.Group).get(ln.group_id)
    was_from = ln.frozen_from
    ln.status = "active"
    ln.activated_on = on
    ln.frozen_from = None
    ln.frozen_until = None
    ln.frozen_note = None
    db.flush()
    C.sync_primary_group(db, s)
    db.flush()
    charge = None
    if g is not None and s.group_id and s.group_id != g.id:
        if MS._row(db, s.id, MS.key(MS._period(on), g.id)) is not None:
            charge = MS.topup_extra(db, s, g, on, user)
        else:
            charge = MS.charge_extra(db, s, g, on, user)
        MS.reprice_primary(db, s)
    audit.log(db, user, entity="student", action="update",
              entity_id=s.id, entity_label=s.full_name,
              field="Guruh faollashtirildi", old_value="Muzlatilgan",
              new_value=g.name if g else None,
              note=(f"Muzlatilgan: {was_from.isoformat() if was_from else '—'}"
                    f", faol: {on.isoformat()}"
                    + (f", {charge['lessons']} dars uchun "
                       f"{int(charge['amount'])} so'm hisoblandi"
                       if charge else "")),
              branch_id=s.branch_id)
    return {"group_id": ln.group_id, "group": g.name if g else None,
            "on": on.isoformat(), "charge": charge}


# ─── Marshrutlar ─────────────────────────────────────────────────────

def _load(db, sid: int, gid: int, user):
    import students as ST
    s = ST._get_student_in_scope(db, sid, user)
    if not s:
        raise HTTPException(404, "O'quvchi topilmadi")
    ln = _ms().link_of(db, s.id, gid)
    return s, ln


def _date(raw, default: date) -> date:
    if not raw:
        return default
    try:
        return date.fromisoformat(str(raw)[:10])
    except ValueError:
        raise HTTPException(400, "Sana noto'g'ri")


@router.post("/api/students/{sid}/groups/{gid}/freeze")
def freeze_group(sid: int, gid: int, payload: dict = None,
                 db: Session = Depends(get_db),
                 user=Depends(require_role(*roles.FREEZE_ROLES))):
    """Faqat shu guruhni muzlatish (2026-10-16)."""
    payload = payload or {}
    today = roles.local_today()
    s, ln = _load(db, sid, gid, user)
    frm = _date(payload.get("from_date"), today)
    until = _date(payload.get("until"), None) if payload.get("until") \
        else None
    if until is not None and until <= frm:
        raise HTTPException(400, "Muddat muzlatish sanasidan keyin bo'lsin")
    err = check_freeze(db, s, ln, frm, today)
    if err:
        raise HTTPException(400, err)
    res = freeze_link(db, s, ln, frm, until, payload.get("note"), user)
    db.commit()
    return {"ok": True, **res}


@router.post("/api/students/{sid}/groups/{gid}/unfreeze")
def unfreeze_group(sid: int, gid: int, payload: dict = None,
                   db: Session = Depends(get_db),
                   user=Depends(require_role(*roles.FREEZE_ROLES))):
    """Shu guruhda muzlatishni bekor qilish — tanlangan kundan pul."""
    payload = payload or {}
    today = roles.local_today()
    s, ln = _load(db, sid, gid, user)
    on = _date(payload.get("on"), today)
    err = check_unfreeze(db, s, ln, on, today)
    if err:
        raise HTTPException(400, err)
    res = unfreeze_link(db, s, ln, on, user)
    db.commit()
    return {"ok": True, **res}
