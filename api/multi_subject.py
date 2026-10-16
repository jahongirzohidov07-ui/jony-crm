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

QO'SHIMCHA QOIDALAR (2026-10-14, Jahongir, egasining so'zi bilan):
  * "O'quvchi oilaviy 10% chegirma bo'lsa 2 fan chegirmasi ishlamaydi" —
    oilaviy bo'lsa 2-fan 10% = 0 (common._multi_subject_percent). Shu
    qoidadan oldin ustma-ust yozilgan joriy oy qatorlari bir marta
    to'g'rilanadi: fix_family_stack (entry, "ms2_family_fix_v1").
  * "O'quvchiga kirib yangi guruh qo'shilsa pul yechmay faol bo'lib
    qolyabdi. Avval qo'shilganda sinovda bo'lishi kerak keyin
    faollashtirilsa pul yechsin" + "Sinovdan faolga o'tganda pul
    yechilishi dars sonidan kelib chiqsin" — guruhi bor o'quvchiga
    qo'shilgan guruh bog'lanishi "trial": pul yo'q, 10% ga kirmaydi.
    Faollashadi: (a) kartadagi "Faollashtirish" (sana tanlanadi), yoki
    (b) shu guruhda 3 ta darsga kelgach avtomat. Pul — faollashgan
    kundan oy oxirigacha shu guruh darslari soni bo'yicha
    (on_group_added), keyin asosiy hisobga 10% mavjud dvigatel orqali.
"""
import re
from datetime import date, datetime, timedelta

import models
import roles

BY = "avtomat (2-fan)"
FROM_PERIOD = "2026-10"          # shu oydan boshlab
TRIAL = "trial"


def key(period: str, gid: int) -> str:
    return f"{period}#g{int(gid)}"


def is_trial(ln) -> bool:
    """Bog'lanish sinovdami (bo'sh status = eski yozuv = faol)."""
    return ln is not None and (getattr(ln, "status", None)
                               or "active") == TRIAL


FROZEN = "frozen"


def is_frozen(ln) -> bool:
    """Faqat SHU guruhda muzlaganmi (2026-10-16, link_freeze.py)."""
    return ln is not None and (getattr(ln, "status", None)
                               or "active") == FROZEN


def _since(ln, month0: date) -> date:
    """Shu oy hisobi qaysi kundan: oy boshi, qo'shilgan yoki
    faollashgan kun — qaysi biri keyin bo'lsa (sinov kunlari
    faollashgandan keyin ham qayta hisoblanmasin)."""
    since = month0
    for d in (getattr(ln, "joined_date", None),
              getattr(ln, "activated_on", None)):
        if d and d > since:
            since = d
    return since


def link_of(db, sid: int, gid: int):
    """O'quvchining shu guruhdagi OCHIQ bog'lanishi."""
    return (db.query(models.StudentGroupLink)
            .filter(models.StudentGroupLink.student_id == sid,
                    models.StudentGroupLink.group_id == int(gid),
                    models.StudentGroupLink.active == 1).first())


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


def quote(db, s, g, since: date, disc: float = None) -> dict:
    """Qo'shimcha guruh hisobi qancha bo'lishi: since dan oy oxirigacha
    darslar (standart oydan oshmaydi) x dars narxi x (1 - chegirma).
    charge_extra ham, "Faollashtirish" oldindan ko'rishi ham SHU
    funksiyadan o'qiydi — ekrandagi raqam va yechilgan pul bir xil."""
    import billing
    import entry as E
    start, end = billing.month_bounds(since.year, since.month)
    try:
        E.M._sync_scheduled_lessons(db, g, start, end)
    except Exception:
        pass
    n = E._billable_lessons(db, g, max(since, start), start, end)
    if disc is None:
        import common as C
        # Fan bo'yicha chegirma (2026-10-16): shu fanniki + barcha fanga
        disc = C._student_discount_percent(db, s, group_id=g.id)
    disc = float(disc or 0)
    price = _price(g)
    amount = roles.money(n * price * (100 - disc) / 100) if n > 0 else 0.0
    return {"period": _period(since), "lessons": n, "price": price,
            "discount": disc, "amount": amount,
            "standard": n >= E._lesson_cap(g)}


def charge_extra(db, s, g, since: date, user=None):
    """Qo'shimcha guruh uchun SHU OY hisobi (since dan oy oxirigacha).
    Idempotent: bu oy uchun qator bo'lsa — hech narsa qilmaydi.
    Sinovdagi bog'lanish uchun pul yechilmaydi (2026-10-14)."""
    if s.status != "active" or g is None or g.id == s.group_id:
        return None
    _ln = link_of(db, s.id, g.id)
    if is_trial(_ln) or is_frozen(_ln):
        return None
    period = _period(since)
    if period < FROM_PERIOD:
        return None
    k = key(period, g.id)
    if _row(db, s.id, k):
        return None
    q = quote(db, s, g, since)
    n, disc, amount = q["lessons"], q["discount"], q["amount"]
    if n <= 0 or amount <= 0:
        return None
    note = (f"{g.name} — {period}: {n} dars (2-fan"
            + (", standart oy" if q["standard"] else "")
            + (f", chegirma {disc:g}%" if disc else "") + ")")
    db.add(models.Payment(
        student_id=s.id, amount=-amount, kind="charge", period=k,
        note=note + f" [dars:{n}]",
        created_by=(user.full_name if user else BY)))
    db.flush()
    return {"group": g.name, "lessons": n, "amount": amount,
            "discount": disc}


def _cut(db, s, row, g, since: date, until: date, unit: float,
         why: str, prior: int = 0) -> bool:
    """Qatorni since..until darslariga TUSHIRADI (oshirmaydi).
    prior (2026-10-14) — shu oyda avvalroq (guruhdan chiqib qayta
    qo'shilishdan oldin) shu qatorda hisoblangan darslar [oldin:N];
    ular ham saqlanadi, aks holda ikkinchi chiqishda yo'qolardi."""
    n = _lessons_between(db, g, since, until)
    if prior:
        cap = int(getattr(g, "standard_lessons_per_month", 0) or 12) or 12
        n = min(int(prior) + n, cap)
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
    disc = C._student_discount_percent(
        db, s, group_id=None if primary else g.id)
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
    if ln is not None:
        since = _since(ln, since)     # faollashgan kundan (2026-10-14)
    m = re.search(r"\[oldin:(\d+)\]", row.note or "")
    return _cut(db, s, row, g, since, until, _unit_of(db, s, g, row), why,
                prior=int(m.group(1)) if m else 0)


def reprice_extras(db, s, only=None) -> int:
    """Chegirma o'zgardi (2026-10-16, fan bo'yicha chegirma) — shu oy
    qo'shimcha fan "#g" qatorlari yangi foiz bilan. Faqat KAMAYTIRADI va
    har safar asl narxdan hisoblaydi (chegirma ustiga chegirma yo'q).
    only — bitta fan; bo'sh — barcha qo'shimcha fanlar."""
    import audit
    import common as C
    period = _period(roles.local_today())
    if period < FROM_PERIOD:
        return 0
    n_done = 0
    for ln in links(db, s.id):
        if ln.group_id == s.group_id or is_trial(ln) or is_frozen(ln):
            continue
        if only and ln.group_id != only:
            continue
        g = db.query(models.Group).get(ln.group_id)
        row = _row(db, s.id, key(period, ln.group_id))
        if row is None or g is None:
            continue
        n = _row_lessons(db, s, g, row)
        disc = float(C._student_discount_percent(db, s, group_id=g.id) or 0)
        target = roles.money(n * _price(g) * (100 - disc) / 100)
        if n <= 0 or target >= abs(row.amount or 0) - 0.5:
            continue
        old = row.amount
        row.amount = -target
        base = re.sub(r"\s*\[dars:\d+\]", "", row.note or "")
        row.note = (base + f" · chegirma {disc:g}%: "
                    f"{int(abs(old)):,} -> {int(target):,}").replace(",", " ") \
            + f" [dars:{n}]"
        row.updated_at = datetime.utcnow()
        audit.log(db, None, entity="payment", action="update",
                  entity_id=row.id, entity_label=s.full_name, field="amount",
                  old_value=old, new_value=-target,
                  note=f"2-fan: chegirma {disc:g}% ({g.name})",
                  branch_id=s.branch_id)
        n_done += 1
    db.flush()
    return n_done


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


def fold_on_move(db, s, old_group, new_group, on: date) -> dict | None:
    """Guruh ko'chirish (students.move_student_group / entry._xb_move,
    common._recharge_after_move ichidan) — 2026-10-14.

    O'quvchi ALLAQACHON FAOL qo'shimcha guruhiga ko'chirilsa, shu guruh
    shu oy uchun "#g" qatorida to'liq hisoblangan. Ilgari asosiy qator
    ham "eski guruh + yangi guruh" deb qayta bo'linardi — yangi guruh
    darslari IKKI MARTA yechilardi (1 116 000 so'm, bitta guruhli
    o'quvchidan). Endi asosiy guruhdan chiqishdagi bilan bir xil
    (on_group_removed): eski asosiy qator ko'chgan kungacha bo'lgan
    darslarga tushiriladi va "#g<eski>" ga o'tadi, yangi guruhning "#g"
    qatori asosiy qatorga aylanadi. "#g" qatori bo'lmasa (sinovdagi yoki
    yangi guruh) — None, oddiy qayta bo'lish ishlaydi."""
    if new_group is None or old_group is None \
            or old_group.id == new_group.id:
        return None
    period = _period(on)
    extra = _row(db, s.id, key(period, new_group.id))
    if extra is None:
        return None
    prim = _row(db, s.id, period)
    was = abs(prim.amount or 0) if prim is not None else 0.0
    old_n = 0
    if prim is not None:
        until = on - timedelta(days=1)
        _cut(db, s, prim, old_group, _month_start(on), until,
             _unit_of(db, s, old_group, prim, primary=True),
             "boshqa guruhga ko'chdi")
        old_n = _lessons_between(db, old_group, _month_start(on), until)
        prim.period = key(period, old_group.id)
    extra.period = period
    db.flush()
    m = re.search(r"\[dars:(\d+)\]", extra.note or "")
    return {"old": was, "new": abs(extra.amount or 0),
            "old_lessons": old_n,
            "new_lessons": int(m.group(1)) if m else None,
            "folded": True}


# ---------------------------------------------------------------------
#  SINOVDAGI QO'SHIMCHA GURUH -> FAOL (2026-10-14)
# ---------------------------------------------------------------------

def percent_if_active(db, s, group_id=None) -> float:
    """Sinovdagi guruh faollashsa o'quvchining jami chegirmasi (2-fan
    10% shu guruh bilan sanaladi; oilaviy bo'lsa baribir 0).
    group_id — shu fan uchun (fan bo'yicha chegirma, 2026-10-16)."""
    import common as C
    base = float(C._student_discount_percent(db, s, skip_kinds=("multi",),
                                             group_id=group_id)
                 or 0)
    total = base + C._multi_subject_percent(db, s, plus=1)
    return min(roles.DISCOUNT_ABSOLUTE_CAP, round(total, 2))


def activation_bounds(ln, today: date) -> tuple:
    """Faollashtirish sanasi oralig'i: joriy oy ichida, guruhga
    qo'shilgan kundan oldin emas, bugundan keyin emas."""
    lo = _month_start(today)
    if ln is not None and ln.joined_date and ln.joined_date > lo:
        lo = ln.joined_date
    return lo, today


NOT_ACTIVE_MSG = ("O'quvchi hozir faol emas (sinovda yoki muzlatilgan). "
                  "Avval o'quvchini faollashtiring, keyin bu guruhni")


def check_on(ln, on: date, today: date, s=None) -> str | None:
    """Sana xatosi matni (bo'lmasa None).

    O'quvchi FAOL bo'lmasa (sinov/muzlatilgan) guruh faollashtirilmaydi
    (2026-10-14): ilgari pul yechilmay activated_on yozilardi, keyin
    kunlik jarayon "#g" qatorini shu sanadan — muzlagan yoki o'quvchi
    o'z sinovidagi kunlar bilan — yechardi (121 500 so'mgacha ortiqcha),
    asosiy guruh esa faollashgan/qaytgan kundan hisoblanardi."""
    if s is not None and s.status != "active":
        return NOT_ACTIVE_MSG
    lo, hi = activation_bounds(ln, today)
    if on > hi:
        return "Kelajakdagi sanani tanlab bo'lmaydi"
    if on < _month_start(today):
        return "Faollashtirish sanasi joriy oy ichida bo'lsin"
    if on < lo:
        return (f"Guruhga qo'shilgan sanadan ({lo.isoformat()}) oldin "
                "bo'lmaydi")
    return None


def _row_lessons(db, s, g, row) -> int:
    """Qatorda hisoblangan darslar: [dars:N], bo'lmasa summa / dars
    narxi (eski asosiy qator)."""
    m = re.search(r"\[dars:(\d+)\]", row.note or "")
    if m:
        return int(m.group(1))
    unit = _unit_of(db, s, g, row)
    return int(round(abs(row.amount or 0) / unit)) if unit > 0 else 0


def activation_quote(db, s, g, since: date, disc: float = None) -> dict:
    """Faollashtirishda AYNAN qancha yechiladi (2026-10-14).

    Shu oy uchun "#g" qatori bo'lmasa — quote(). Bo'lsa (guruhdan
    chiqib, shu oyning o'zida qayta qo'shilgan; yoki asosiy guruhdan
    chiqib "#g" ga o'tgan qator) — charge_extra hech narsa yozmasdi va
    o'quvchi oy oxirigacha tekin o'qirdi. Endi shu qatorga since dan
    oy oxirigacha darslar QO'SHILADI, qatordagi darslar bilan birga
    standart oydan oshmaydi. Oldindan ko'rish ham, topup_extra ham
    shu funksiyadan o'qiydi."""
    import entry as E
    q = quote(db, s, g, since, disc=disc)
    q["existing"] = None
    row = _row(db, s.id, key(q["period"], g.id))
    if row is None:
        return q
    cap = E._lesson_cap(g)
    have = min(_row_lessons(db, s, g, row), cap)
    add = max(0, min(q["lessons"], cap - have))
    q["existing"] = {"lessons": have,
                     "amount": roles.money(abs(row.amount or 0))}
    q["lessons"] = add
    q["amount"] = (roles.money(add * q["price"] * (100 - q["discount"])
                               / 100) if add > 0 else 0.0)
    q["standard"] = have + add >= cap
    return q


def topup_extra(db, s, g, since: date, user=None):
    """Mavjud "#g" qatoriga faollashgan kundan oy oxirigacha darslarni
    qo'shadi (activation_quote). Qator o'chirilmaydi, summa joyida
    oshiriladi; [oldin:N] — qayta qo'shilishdan oldingi darslar (keyin
    yana chiqsa cut_extra ularni saqlaydi). Audit yoziladi."""
    import audit
    if s.status != "active" or g is None or g.id == s.group_id:
        return None
    period = _period(since)
    if period < FROM_PERIOD:
        return None
    row = _row(db, s.id, key(period, g.id))
    if row is None:
        return None
    q = activation_quote(db, s, g, since)
    add, amount = q["lessons"], q["amount"]
    if add <= 0 or amount <= 0:
        return None
    have = q["existing"]["lessons"]
    old = row.amount
    new = roles.money(abs(old or 0) + amount)
    base = re.sub(r"\s*\[(?:dars|oldin):\d+\]", "", row.note or "")
    row.amount = -new
    row.note = ((base + f" · {since.strftime('%d.%m')} dan qayta "
                 f"faollashdi: +{add} dars, {int(abs(old or 0)):,} -> "
                 f"{int(new):,}").replace(",", " ")
                + f" [oldin:{have}] [dars:{have + add}]")
    row.updated_at = datetime.utcnow()
    audit.log(db, user, entity="payment", action="update", entity_id=row.id,
              entity_label=s.full_name, field="amount", old_value=old,
              new_value=-new, note=f"2-fan: qayta faollashdi (+{add} dars)",
              branch_id=s.branch_id)
    db.flush()
    return {"group": g.name, "lessons": add, "amount": amount,
            "discount": q["discount"], "topup": True}


def preview_activation(db, s, ln, on: date, today: date = None) -> dict:
    """"Faollashtirish" oynasi uchun: shu sanadan oy oxirigacha shu
    guruh darslari x narx x (1 - chegirma). Hech narsa yozmaydi."""
    import common as C
    today = today or roles.local_today()
    g = db.query(models.Group).get(ln.group_id)
    disc = percent_if_active(db, s, group_id=ln.group_id)
    q = activation_quote(db, s, g, on, disc=disc)
    lo, hi = activation_bounds(ln, today)
    now_pct = float(C._student_discount_percent(db, s) or 0)
    fam = float(C._family_discount_percent(db, s) or 0)
    return {
        "group_id": g.id, "group": g.name, "on": on.isoformat(),
        "min": lo.isoformat(), "max": hi.isoformat(),
        "period": q["period"], "lessons": q["lessons"],
        "price": q["price"], "discount": q["discount"],
        "amount": q["amount"],
        # Shu oy uchun shu guruh qatori allaqachon bor bo'lsa — unda
        # nechta dars hisoblangani (yuqoridagi summa unga QO'SHILADI).
        "existing": q.get("existing"),
        "family": fam > 0,
        "multi_applies": (C._multi_subject_percent(db, s, plus=1) > 0),
        "primary_discount_now": now_pct,
        "primary_discount_after": disc,
        "error": check_on(ln, on, today, s),
    }


def activate_link(db, s, ln, on: date, reason: str, user=None) -> dict:
    """Sinovdagi bog'lanishni FAOL qiladi va pul yechadi: faollashgan
    kundan oy oxirigacha darslar soni bo'yicha (on_group_added; shu oy
    qatori bor bo'lsa — topup_extra), keyin asosiy guruh hisobiga 10%
    mavjud dvigatel orqali. Faqat FAOL o'quvchi (check_on). Chaqiruvchi
    commit qiladi."""
    import audit
    if s.status != "active":
        raise ValueError(NOT_ACTIVE_MSG)
    g = db.query(models.Group).get(ln.group_id)
    ln.status = "active"
    ln.activated_on = on
    db.flush()
    charge = None
    if s.group_id and g is not None and s.group_id != g.id:
        if _row(db, s.id, key(_period(on), g.id)) is not None:
            charge = topup_extra(db, s, g, on, user)
            reprice_primary(db, s)
        else:
            charge = on_group_added(db, s, g, on, user)
    audit.log(db, user, entity="student", action="update",
              entity_id=s.id, entity_label=s.full_name,
              field="Guruh faollashtirildi", old_value="Sinov",
              new_value=g.name if g else str(ln.group_id),
              note=(f"{reason}. Sana: {on.isoformat()}"
                    + (f", {charge['lessons']} dars uchun "
                       f"{int(charge['amount'])} so'm hisoblandi"
                       if charge else ", pul yechilmadi")),
              branch_id=s.branch_id)
    return {"group_id": ln.group_id, "group": g.name if g else None,
            "activated_on": on.isoformat(), "reason": reason,
            "charge": charge}


def trial_days(db, sid: int, ln) -> list:
    """Sinovdagi guruhda KELGAN darslar (1 = keldi, 2 = kech keldi),
    faqat SHU guruhda va guruhga qo'shilgan kundan beri."""
    A, L = models.Attendance, models.Lesson
    q = (db.query(L.date).join(A, A.lesson_id == L.id)
         .filter(A.student_id == sid, L.group_id == ln.group_id,
                 A.present.in_((1, 2))))
    if ln.joined_date:
        q = q.filter(L.date >= ln.joined_date)
    return sorted(d for (d,) in q.all())


def maybe_auto_activate_link(db, s, gid: int, today: date = None):
    """Shu guruhda TRIAL_LESSONS_TO_ACTIVATE ta darsga kelgan bo'lsa —
    avtomat faollashtiradi. Sana — shu guruhda birinchi kelgan kuni
    (o'quvchi sinovidagi qoida bilan bir xil), lekin joriy oydan oldin
    emas. Faqat FAOL o'quvchi uchun: sinovdagi o'quvchini o'zining
    qoidasi (common._maybe_auto_activate) faollashtiradi."""
    if s is None or s.status != "active":
        return None
    ln = link_of(db, s.id, gid)
    if not is_trial(ln):
        return None
    days = trial_days(db, s.id, ln)
    need = roles.TRIAL_LESSONS_TO_ACTIVATE
    if len(days) < need:
        return None
    today = today or roles.local_today()
    on = min(max(days[0], _month_start(today)), today)
    return activate_link(db, s, ln, on,
                         reason=f"Shu guruhda {need} ta sinov darsiga keldi")


def daily(db, today: date) -> dict:
    """Kunlik: (0) shu guruhda 3 ta darsga kelgan sinovdagi guruhni
    faollashtiradi; (1) qo'shimcha guruhlar uchun shu oy hisobi yo'q
    bo'lsa — yozadi va asosiy hisobga 10% qo'llaydi (sinovdagi guruh
    o'tkazib yuboriladi); (2) guruhdan chiqqan / muzlagan / ketgan
    o'quvchining shu oy "#g" qatorini tushiradi.
    Idempotent — necha marta yurgizilsa ham natija bir xil."""
    period = _period(today)
    out = {"charged": 0, "repriced": 0, "cut": 0, "activated": 0}
    if period < FROM_PERIOD:
        return out
    month0 = _month_start(today)
    # (0) avtomat faollashtirish (davomat boshqa yo'l bilan kiritilgan
    # bo'lsa ham ushlanadi)
    trial_rows = (db.query(models.StudentGroupLink, models.Student)
                  .join(models.Student,
                        models.Student.id
                        == models.StudentGroupLink.student_id)
                  .filter(models.StudentGroupLink.active == 1,
                          models.StudentGroupLink.status == TRIAL,
                          models.Student.status == "active").all())
    for ln, s in trial_rows:
        if maybe_auto_activate_link(db, s, ln.group_id, today):
            out["activated"] += 1
    rows = (db.query(models.StudentGroupLink, models.Student)
            .join(models.Student,
                  models.Student.id == models.StudentGroupLink.student_id)
            .filter(models.StudentGroupLink.active == 1,
                    models.Student.status == "active").all())
    by_student: dict = {}
    for ln, s in rows:
        by_student.setdefault(s.id, (s, []))[1].append(ln)
    for sid, (s, lns) in by_student.items():
        # Sinovdagi va shu guruhda muzlagan guruh pul yechmaydi va 10%
        # ga kirmaydi
        lns = [ln for ln in lns if not is_trial(ln) and not is_frozen(ln)]
        if len(lns) < 2 or not s.group_id:
            continue
        for ln in lns:
            if ln.group_id == s.group_id:
                continue
            g = db.query(models.Group).get(ln.group_id)
            since = _since(ln, month0)
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
        if ln is not None and ln.active and is_frozen(ln):
            # Faqat shu guruhda muzlagan (2026-10-16): muzlagan kundan
            # oldingi darslar qoladi (idempotent — faqat kamaytiradi)
            try:
                import link_freeze as LF
                if LF.cut_before(db, s, ln, p, today):
                    out["cut"] += 1
            except Exception:
                pass
            continue
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


# ---------------------------------------------------------------------
#  OILAVIY + 2-FAN USTMA-UST — BIR MARTALIK TUZATISH (2026-10-14)
#
#  Jahongir: "O'quvchi oilaviy 10% chegirma bo'lsa 2 fan chegirmasi
#  ishlamaydi". 91069473 (2-fan) jonli bo'lgandan beri oilaviy
#  chegirmali ikki fanli o'quvchilarga 10% + 10% = 20% yozilgan:
#    * "#g" qatori — yozilganda izohda "chegirma X%" va "[dars:N]";
#    * asosiy qator — reprice_primary (finance._recharge_current_month)
#      uni oilaviy darajadan 20% ga tushirgan.
#  Endi ular to'g'ri summaga (faqat oilaviy + qo'lda berilganlar)
#  QAYTARILADI. Qator o'chirilmaydi — summa joyida, har qatorga audit
#  va bitta umumiy audit (ro'yxat: o'quvchi / eski / yangi).
#  Qayta yurgizilsa hech narsa o'zgarmaydi (belgi + summa tekshiruvi).
# ---------------------------------------------------------------------
FAMFIX_KEY = "ms2_family_fix_v1"
FAMFIX_MARK = "[oila-2fan-fix]"


def _lvl(base: float, pct: float) -> float:
    return roles.money(base * (100.0 - pct) / 100.0)


def _famfix_extra(p, fam: float, multi: float):
    """"#g" qatori: yozilgan foizdan (X) faqat 2-fan ulushi olinadi.
    Qaytaradi: (yangi summa, eski foiz, yangi foiz) yoki None."""
    note = p.note or ""
    if "2-fan" not in note:
        return None
    m_n = re.search(r"\[dars:(\d+)\]", note)
    m_x = re.search(r"chegirma ([\d.]+)%", note)
    if not m_n or not m_x:
        return None
    n, x = int(m_n.group(1)), float(m_x.group(1))
    # Faqat oilaviy VA 2-fan ikkalasi ham tushgan qator
    if n <= 0 or x >= 100 or x < multi + fam - 0.01:
        return None
    new_x = round(x - multi, 2)
    unit = abs(p.amount or 0) / n
    return (roles.money(n * unit * (100 - new_x) / (100 - x)), x, new_x)


def _famfix_primary(db, s, p, correct: float, stacked: float):
    """Asosiy qator: hozirgi summa "ustma-ust" darajada bo'lsagina
    to'g'ri darajadagi summa qaytadi, aks holda None (tegilmaydi)."""
    import billing
    note = p.note or ""
    old = abs(p.amount or 0)
    bases = []
    m = re.search(r"\[asos:(\d+)\]", note)
    if m:
        bases.append(float(m.group(1)))
    g = s.group
    if g is not None:
        try:
            price = billing.student_lesson_price(s, g)
        except Exception:
            price = 0
        std = int(g.standard_lessons_per_month or 12) or 12
        if price:
            bases.append(roles.money(price * std))
            m2 = re.search(r"(\d+) dars", note)
            if m2 and int(m2.group(1)) > 0:
                bases.append(roles.money(price * int(m2.group(1))))
    for b in bases:
        if b > 0 and abs(old - _lvl(b, stacked)) <= 1:
            return _lvl(b, correct)
    # Chegirma dvigateli izohi: "chegirma qo'llandi: A -> B" — B hozirgi
    # summa, A esa aynan 2-fan ulushisiz daraja bo'lsa A ga qaytadi.
    hits = re.findall(r"chegirma qo'llandi: ([\d ]+?) -> ([\d ]+)", note)
    if hits:
        a = float(hits[-1][0].replace(" ", "") or 0)
        b = float(hits[-1][1].replace(" ", "") or 0)
        if abs(b - old) <= 1 and stacked < 100 and \
                abs(a - old * (100 - correct) / (100 - stacked)) <= 2:
            return roles.money(a)
    return None


def fix_family_stack(db, today: date = None, apply: bool = True) -> list:
    """Oilaviy chegirmali o'quvchilarda 2-fan 10% ustma-ust tushgan
    qatorlarni (FROM_PERIOD .. joriy oy) to'g'ri summaga qaytaradi.
    Chaqiruvchi commit qiladi."""
    import audit
    import common as C
    from sqlalchemy import func
    today = today or roles.local_today()
    cur = _period(today)
    if cur < FROM_PERIOD:
        return []
    L = models.StudentGroupLink
    sids = {sid for (sid,) in db.query(models.Payment.student_id).filter(
        models.Payment.kind == "charge",
        models.Payment.period.like("%#g%"),
        models.Payment.period >= FROM_PERIOD).distinct().all()}
    for (sid,) in (db.query(L.student_id).filter(L.active == 1)
                   .group_by(L.student_id)
                   .having(func.count(L.id) >= 2).all()):
        sids.add(sid)
    multi = float(C.MULTI_SUBJECT_PERCENT)
    done = []
    for sid in sorted(sids):
        s = db.query(models.Student).get(sid)
        if s is None or not s.parent_id:
            continue
        fam = float(C._family_discount_percent(db, s) or 0)
        if fam <= 0:
            continue
        correct = float(C._student_discount_percent(db, s) or 0)
        stacked = min(roles.DISCOUNT_ABSOLUTE_CAP, correct + multi)
        if stacked - correct < 0.01:
            continue
        rows = (db.query(models.Payment)
                .filter(models.Payment.student_id == sid,
                        models.Payment.kind == "charge",
                        models.Payment.period >= FROM_PERIOD)
                .order_by(models.Payment.id).all())
        for p in rows:
            per = p.period or ""
            if per[:7] > cur or FAMFIX_MARK in (p.note or ""):
                continue
            old = abs(p.amount or 0)
            xs = None
            if "#g" in per:
                r = _famfix_extra(p, fam, multi)
                if r is None:
                    continue
                target, x_old, x_new = r
                xs = (x_old, x_new)
            else:
                target = _famfix_primary(db, s, p, correct, stacked)
            if target is None or target <= old + 0.5:
                continue
            item = {"student_id": s.id, "name": s.full_name,
                    "payment_id": p.id, "period": per,
                    "old": roles.money(old), "new": roles.money(target)}
            done.append(item)
            if not apply:
                continue
            old_amt = p.amount
            note = p.note or ""
            m_n = re.search(r"\s*\[dars:\d+\]", note)
            tail = m_n.group(0).strip() if m_n else ""
            base = re.sub(r"\s*\[dars:\d+\]", "", note)
            if xs:
                base = base.replace(f"chegirma {xs[0]:g}%",
                                    f"chegirma {xs[1]:g}%", 1)
            p.note = ((base + f" · oilaviy chegirma bor — 2-fan 10% "
                       f"olib tashlandi: {int(old):,} -> {int(target):,}")
                      .replace(",", " ")
                      + f" {FAMFIX_MARK}" + (f" {tail}" if tail else ""))
            p.amount = -target
            p.updated_at = datetime.utcnow()
            audit.log(db, None, entity="payment", action="update",
                      entity_id=p.id, entity_label=s.full_name,
                      field="amount", old_value=old_amt,
                      new_value=-target,
                      note=("2-fan: oilaviy chegirma bor — 2 fan 10% olib "
                            "tashlandi (bir martalik tuzatish)"),
                      branch_id=s.branch_id)
    if done and apply:
        audit.log(db, None, entity="payment", action="ms2_family_fix",
                  entity_label="Oilaviy + 2-fan: bir martalik tuzatish",
                  new_value=len(done),
                  note=("Jahongir: \"O'quvchi oilaviy 10% chegirma bo'lsa "
                        "2 fan chegirmasi ishlamaydi\". "
                        + "; ".join(f"{d['name']} (#{d['student_id']}, "
                                    f"{d['period']}): {int(d['old'])} -> "
                                    f"{int(d['new'])}" for d in done)))
    db.flush()
    return done
