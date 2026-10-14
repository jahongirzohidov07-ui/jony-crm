"""IKKI FAN — ikkinchi (va keyingi) guruh uchun oylik + 10% chegirma
(2026-10-14).

Jahongir: "bitta o'quvchi 2ta fanga guruhga kelsa skidka bor edi 10%
avtomat bo'lishi kerak". Holmirzaeva Sabina (Rus tili + LOUISIANA 2)
ota-onasi 2 x 540 000 x 90% = 972 000 to'lagan, tizim esa faqat Rus
tilini (540 000) yechgan edi — ikkinchi guruh UMUMAN hisoblanmasdi
(students.student_add_group: "pul qoidasi hali belgilanmagan").

QOIDA:
  * O'quvchining 2 va undan ko'p FAOL guruhi bo'lsa — HAR BIR fanga
    10% chegirma (common._student_discount_percent ga "multi" sifatida
    qo'shiladi, oilaviy va boshqa chegirmalar bilan birga sanaladi,
    umumiy chegara o'zgarmaydi).
  * Asosiy guruh hisobi avvalgidek (period="YYYY-MM").
  * Qo'shimcha guruh hisobi ALOHIDA qator: period="YYYY-MM#g<guruh_id>".
    Shunda oylik dvigatelining "shu oy hisobi bormi?" tekshiruvlari
    (period ==) bu qatorni ko'rmaydi va asosiy hisobga aralashmaydi.
  * Oy o'rtasida qo'shilsa — qo'shilgan kundan oy oxirigacha darslar
    (12 dan oshmaydi); keyingi oylar — to'liq standart oy.
  * Guruhdan chiqsa / muzlatilsa / ketsa — shu oy qatori chiqqan
    kungacha bo'lgan darslarga TUSHIRILADI (hech qachon oshirilmaydi).
  * Qatorlar o'chirilmaydi — summa joyida to'g'rilanadi, audit qoladi.
"""
import re
from datetime import date, timedelta

import models
import roles

BY = "avtomat (2-fan)"
FROM_PERIOD = "2026-10"          # shu oydan boshlab


def key(period: str, gid: int) -> str:
    return f"{period}#g{int(gid)}"


def _period(d: date) -> str:
    return f"{d.year:04d}-{d.month:02d}"


def _month_start(d: date) -> date:
    return d.replace(day=1)


def links(db, sid: int, active_only: bool = True) -> list:
    q = db.query(models.StudentGroupLink).filter(
        models.StudentGroupLink.student_id == sid)
    if active_only:
        q = q.filter(models.StudentGroupLink.active == 1)
    return q.order_by(models.StudentGroupLink.id).all()


def _row(db, sid: int, k: str):
    return (db.query(models.Payment)
            .filter(models.Payment.student_id == sid,
                    models.Payment.period == k,
                    models.Payment.kind == "charge")
            .order_by(models.Payment.id.desc()).first())


def _price(g) -> float:
    """Qo'shimcha fan narxi — guruhning joriy dars narxi (o'quvchidagi
    "qulflangan eski narx" asosiy faniga tegishli)."""
    p = float(getattr(g, "lesson_price", 0) or 0)
    if p <= 0:
        std = int(getattr(g, "standard_lessons_per_month", 0) or 12) or 12
        p = float(getattr(g, "monthly_fee", 0) or 0) / std
    return p


def _lessons_between(db, g, since: date, until: date) -> int:
    """since..until (ikkalasi ham kiradi) oralig'idagi guruh darslari,
    standart oydan oshmaydi."""
    import common as C
    cap = int(getattr(g, "standard_lessons_per_month", 0) or 12) or 12
    if until < since:
        return 0
    rows = C._lessons_left_in_month(db, g.id, since)
    return min(sum(1 for r in rows if r.date <= until), cap)


def charge_extra(db, s, g, since: date, user=None):
    """Qo'shimcha guruh uchun SHU OY hisobi (since dan oy oxirigacha).
    Idempotent: bu oy uchun qator bo'lsa — hech narsa qilmaydi."""
    if s.status != "active" or g is None or g.id == s.group_id:
        return None
    period = _period(since)
    if period < FROM_PERIOD:
        return None
    k = key(period, g.id)
    if _row(db, s.id, k):
        return None
    import billing
    import entry as E
    start, end = billing.month_bounds(since.year, since.month)
    try:
        E.M._sync_scheduled_lessons(db, g, start, end)
    except Exception:
        pass
    n = E._billable_lessons(db, g, max(since, start), start, end)
    if n <= 0:
        return None
    import common as C
    disc = C._student_discount_percent(db, s)
    price = _price(g)
    amount = roles.money(n * price * (100 - disc) / 100)
    if amount <= 0:
        return None
    note = (f"{g.name} — {period}: {n} dars (2-fan"
            + (", standart oy" if n >= E._lesson_cap(g) else "")
            + (f", chegirma {disc:g}%" if disc else "") + ")")
    db.add(models.Payment(
        student_id=s.id, amount=-amount, kind="charge", period=k,
        note=note + f" [dars:{n}]",
        created_by=(user.full_name if user else BY)))
    db.flush()
    return {"group": g.name, "lessons": n, "amount": amount,
            "discount": disc}


def _cut(db, s, row, g, since: date, until: date, unit: float,
         why: str) -> bool:
    """Qatorni since..until darslariga TUSHIRADI (oshirmaydi)."""
    n = _lessons_between(db, g, since, until)
    target = roles.money(n * unit)
    if target >= abs(row.amount) - 0.5:
        return False
    import audit
    old = row.amount
    row.amount = -target
    base = re.sub(r"\s*\[dars:\d+\]", "", row.note or "")
    row.note = (base + f" · {why}: {n} dars, "
                f"{int(abs(old)):,} -> {int(target):,}").replace(",", " ") \
        + f" [dars:{n}]"
    row.updated_at = __import__("datetime").datetime.utcnow()
    audit.log(db, None, entity="payment", action="update", entity_id=row.id,
              entity_label=s.full_name, field="amount", old_value=old,
              new_value=-target, note=f"2-fan: {why}",
              branch_id=s.branch_id)
    return True


def _unit_of(db, s, g, row, primary: bool = False) -> float:
    """Shu qatordagi bitta dars narxi (chegirma bilan) — qatorda
    yozilgan dars soni [dars:N] dan, bo'lmasa joriy hisobdan."""
    m = re.search(r"\[dars:(\d+)\]", row.note or "")
    if m and int(m.group(1)) > 0:
        return abs(row.amount) / int(m.group(1))
    import common as C
    disc = C._student_discount_percent(db, s)
    if primary:
        import billing
        base = billing.student_lesson_price(s, g)
    else:
        base = _price(g)
    return base * (100 - disc) / 100


def cut_extra(db, s, gid: int, until: date, why: str) -> bool:
    """Qo'shimcha guruh qatorini `until` gacha bo'lgan darslarga
    tushirish (guruhdan chiqish / muzlatish / ketish)."""
    period = _period(until)
    row = _row(db, s.id, key(period, gid))
    g = db.query(models.Group).get(int(gid))
    if row is None or g is None:
        return False
    since = _month_start(until)
    ln = (db.query(models.StudentGroupLink)
          .filter(models.StudentGroupLink.student_id == s.id,
                  models.StudentGroupLink.group_id == gid).first())
    if ln and ln.joined_date and ln.joined_date > since:
        since = ln.joined_date
    return _cut(db, s, row, g, since, until, _unit_of(db, s, g, row), why)


def reprice_primary(db, s) -> bool:
    """Asosiy guruhning shu oy hisobiga 2-fan chegirmasini qo'llash
    (mavjud chegirma dvigateli orqali — faqat kamaytiradi, ikki marta
    qo'llamaydi)."""
    try:
        import finance as F
        return bool(F._recharge_current_month(db, s, commit=False))
    except Exception:
        return False


def on_group_added(db, s, g, joined: date, user=None) -> dict | None:
    """students.student_add_group dan: qo'shimcha guruh qo'shildi."""
    if g is None or g.id == s.group_id or s.status != "active":
        return None
    res = charge_extra(db, s, g, joined, user)
    reprice_primary(db, s)
    return res


def on_group_removed(db, s, gid: int, was_primary: bool, on: date) -> None:
    """students.student_remove_group dan (detach DAN KEYIN chaqiriladi).

    Qo'shimcha guruhdan chiqsa — uning qatori chiqqan kungacha.
    Asosiy guruhdan chiqsa — asosiy qator chiqqan kungacha, yangi
    asosiy guruhning "#g" qatori esa oddiy oylik qatoriga aylanadi
    (endi u asosiy)."""
    period = _period(on)
    if not was_primary:
        cut_extra(db, s, gid, on, "guruhdan chiqdi")
        return
    old_g = db.query(models.Group).get(int(gid))
    prim = (db.query(models.Payment)
            .filter(models.Payment.student_id == s.id,
                    models.Payment.period == period,
                    models.Payment.kind == "charge")
            .order_by(models.Payment.id.desc()).first())
    if prim is not None and old_g is not None:
        _cut(db, s, prim, old_g, _month_start(on), on,
             _unit_of(db, s, old_g, prim, primary=True),
             "asosiy guruhdan chiqdi")
        # Bu qator endi eski guruhniki — "#g" ga o'tkaziladi
        prim.period = key(period, old_g.id)
    if s.group_id:
        new_row = _row(db, s.id, key(period, s.group_id))
        if new_row is not None:
            new_row.period = period


def daily(db, today: date) -> dict:
    """Kunlik: (1) qo'shimcha guruhlar uchun shu oy hisobi yo'q bo'lsa —
    yozadi va asosiy hisobga 10% qo'llaydi; (2) guruhdan chiqqan /
    muzlagan / ketgan o'quvchining shu oy "#g" qatorini tushiradi.
    Idempotent — necha marta yurgizilsa ham natija bir xil."""
    period = _period(today)
    out = {"charged": 0, "repriced": 0, "cut": 0}
    if period < FROM_PERIOD:
        return out
    month0 = _month_start(today)
    rows = (db.query(models.StudentGroupLink, models.Student)
            .join(models.Student,
                  models.Student.id == models.StudentGroupLink.student_id)
            .filter(models.StudentGroupLink.active == 1,
                    models.Student.status == "active").all())
    by_student: dict = {}
    for ln, s in rows:
        by_student.setdefault(s.id, (s, []))[1].append(ln)
    for sid, (s, lns) in by_student.items():
        if len(lns) < 2 or not s.group_id:
            continue
        for ln in lns:
            if ln.group_id == s.group_id:
                continue
            g = db.query(models.Group).get(ln.group_id)
            since = month0
            if ln.joined_date and ln.joined_date > since:
                since = ln.joined_date
            if since > today:
                continue
            if charge_extra(db, s, g, since):
                out["charged"] += 1
        if reprice_primary(db, s):
            out["repriced"] += 1
    # (2) tushirish
    extra = (db.query(models.Payment)
             .filter(models.Payment.kind == "charge",
                     models.Payment.period.like(period + "#g%")).all())
    for p in extra:
        s = db.query(models.Student).get(p.student_id)
        if s is None:
            continue
        gid = int(p.period.split("#g", 1)[1])
        ln = (db.query(models.StudentGroupLink)
              .filter(models.StudentGroupLink.student_id == s.id,
                      models.StudentGroupLink.group_id == gid).first())
        until, why = None, None
        if ln is not None and not ln.active:
            until, why = (ln.left_date or today), "guruhdan chiqdi"
        elif s.status not in ("active", "trial"):
            until = s.left_date if (s.status != "frozen" and s.left_date) \
                else today
            why = "muzlatildi" if s.status == "frozen" else "ketdi"
        if until is None or _period(until) != period:
            continue
        if cut_extra(db, s, gid, until, why):
            out["cut"] += 1
    db.flush()
    return out
