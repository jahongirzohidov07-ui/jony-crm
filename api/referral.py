"""REFERAL DASTURI — "do'stingni olib kel" (2026-08-28).

Jahongir so'radi:
    "Jony Student app uchun referal tizimini qo'shish kerak, ya'ni
     o'quvchiga maxsus link beriladi, shu link orqali uni kimgadur
     tashlasa u o'quvchi ro'yxatdan o'tadi va adminlarga so'rov boradi
     yangi lid bo'lib, lidni obrabotka qilib guruhga qo'yib to'lov
     qilgandan keyin 10% chegirma oladi, 2-do'sti uchun esa 30%,
     3-do'sti uchun esa 50% ... 4-do'sti uchun 75%, 5-do'sti uchun
     100% bo'ladi, ya'ni bitta olib kelsa shu 10% bo'ladi, 2-do'stiga
     esa 30% bo'ladi QO'SHILMAYDI 10+30=40% bo'lmaydi"
    "faqat 1 oy bepul, to'laganlargina hisobga olinadi, 2 oy emas SHU
     OY ichida qilaylik, oilaviy chegirmasi bo'lsa o'sha to'laydigan
     summadan 10% foiz hisoblanib ketaveradi"

YO'L (5 qadam):
    1. O'quvchi ilovada o'z havolasini oladi  ->  /r/JONY-XXXX
    2. Do'st shu sahifada ariza qoldiradi     ->  LID (manba:
       "Do'st taklifi"), adminlarga vazifa boradi
    3. Admin lidni ishlaydi, guruhga qo'yadi  ->  lid o'quvchiga
       aylanadi, referred_by_student_id saqlanadi
    4. Do'st TO'LOV qiladi                    ->  shu yerdagi
       on_payment() ishga tushadi
    5. Taklif qilgan bola chegirma oladi      ->  darajaga qarab
       10/30/50/75/100%, BIR OYGA

UCHTA NOZIK JOY — xato aynan shu yerlarda bo'ladi:

  (a) QO'SHILMAYDI. Daraja oldingisini ALMASHTIRADI. Shuning uchun
      bitta o'quvchining bitta oyiga FAQAT BITTA referal chegirmasi
      bo'ladi: uchinchi do'st kelganda YANGI qator qo'shilmaydi,
      borini yangilaymiz. Aks holda 10+30+50 bo'lib ketardi.

  (b) FOIZ QAYERDAN. Oylik narxdan emas, o'quvchi HAQIQATDA
      TO'LAYDIGAN summadan. Shuning uchun chegirma bazaga FOIZ emas,
      SO'M (amount) bo'lib yoziladi: boshqa chegirmalar ayrilgandan
      keyingi summadan hisoblab. Misol: 500 000, oilaviy 20% ->
      400 000 -> referal 10% -> 40 000 -> bola 360 000 to'laydi.

  (c) OYNA BIR OY. Do'st SHU OY ichida to'lasa hisobga olinadi.
      Sentabrda 2 ta olib kelsa 30%; oktabrda 1 ta olib kelsa yana
      10% (30% qaytmaydi). Shuning uchun hisob har doim OY kesimida.

HECH NARSA O'CHIRILMAYDI: eski oyning chegirmasi tegilmaydi, faqat
JORIY nishon oyning qatori yangilanadi.
"""
import os
import random
import string
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

import models
import roles
from common import (_apply_shop_discounts, _discount_alive,
                    _student_discount_percent, student_balance)

def mask_name(full_name: str) -> str:
    """"Aziz Karimov" -> "Aziz K." — bola do'stlar ro'yxatida
    boshqalarning to'liq ismini ko'rmasin (student_app._mask bilan
    bir xil uslub)."""
    parts = (full_name or "").split()
    if len(parts) < 2:
        return full_name or ""
    return f"{parts[0]} {parts[1][0]}."


# Havola kodi: chalkashadigan belgilar (0/O, 1/I) OLIB TASHLANGAN —
# bola kodni og'zaki aytishi ham mumkin.
_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
_CODE_LEN = 5
_PREFIX = "JONY-"


# =====================================================================
#  1-QADAM — HAVOLA
# =====================================================================

def make_code() -> str:
    return _PREFIX + "".join(random.choice(_ALPHABET) for _ in range(_CODE_LEN))


def ensure_code(db: Session, s: models.Student) -> str:
    """O'quvchining havola kodi. Bo'lmasa — yaratadi va SAQLAYDI.

    Kod bir marta beriladi va O'ZGARMAYDI: bola havolani tarqatib
    yuborgandan keyin u ishlamay qolsa, butun dastur ishonchini
    yo'qotadi."""
    if getattr(s, "ref_code", None):
        return s.ref_code
    for _ in range(30):
        code = make_code()
        if not db.query(models.Student).filter(
                models.Student.ref_code == code).first():
            s.ref_code = code
            db.commit()
            return code
    # 30 marta ham bo'sh kod topilmasa (amalda bo'lmaydi) — id qo'shamiz
    s.ref_code = f"{_PREFIX}{s.id}"
    db.commit()
    return s.ref_code


def by_code(db: Session, code: str):
    """Kod bo'yicha o'quvchi. Katta-kichik harf va bo'sh joy farq qilmaydi."""
    c = (code or "").strip().upper().replace(" ", "")
    if not c:
        return None
    if not c.startswith(_PREFIX):
        c = _PREFIX + c.lstrip("-")
    return (db.query(models.Student)
            .filter(models.Student.ref_code == c).first())


def share_text(s: models.Student, link: str) -> str:
    """Do'stga yuboriladigan tayyor matn (Jahongir: "men Jony
    Academyda falon kursga yozildim, shunaqa shunaqa foydalarni
    bor ekan deb maqtan")."""
    kurs = (s.subject or "ingliz tili").strip()
    ism = (s.first_name or (s.full_name or "").split()[0] or "Men").strip()
    return (
        f"Salom! Men — {ism}. Jony Academyda {kurs} kursida o'qiyapman "
        f"va rostdan zo'r ekan 🔥\n\n"
        f"Nimasi yaxshi:\n"
        f"• Darsdan tashqari Jony Student ilovasi bor — telefonda "
        f"o'ynab so'z yodlayapman, daraja ko'tarilyapti\n"
        f"• Har dars uchun coin yig'iladi, coinga sovg'a va chegirma "
        f"olsa bo'ladi\n"
        f"• Ustozlar tushuntirmaguncha qo'yvormaydi, guruh kichkina\n"
        f"• IELTS va Multilevelga alohida tayyorlov bor\n\n"
        f"Sen ham sinab ko'r — pastdagi havolada ismingni qoldirsang, "
        f"o'zlari qo'ng'iroq qilishadi va BEPUL sinov darsiga "
        f"yozishadi:\n{link}")


# =====================================================================
#  2-QADAM — HISOB (kim, qachon, nechta)
# =====================================================================

def month_key(d: date = None) -> str:
    d = d or roles.local_today()
    return f"{d.year:04d}-{d.month:02d}"


def month_bounds(period: str):
    y, m = int(period[:4]), int(period[5:7])
    first = date(y, m, 1)
    last = (date(y + 1, 1, 1) if m == 12 else date(y, m + 1, 1)) \
        - timedelta(days=1)
    return first, last


def first_payment_date(db: Session, student_id: int):
    """O'quvchining BIRINCHI haqiqiy to'lovi qachon bo'lgan.

    kind="payment" va amount > 0 — hisob (charge, manfiy) va chegirma
    (discount) to'lov emas.

    SANA created_at dan olinadi: bazada u aynan "TO'LOV SANASI"
    (eski sana bilan kiritilganda orqaga suriladi), rostakam
    kiritilish vaqti esa entered_at da alohida turadi."""
    row = (db.query(models.Payment.created_at)
           .filter(models.Payment.student_id == student_id,
                   models.Payment.kind == "payment",
                   models.Payment.amount > 0)
           .order_by(models.Payment.created_at.asc(),
                     models.Payment.id.asc()).first())
    if not row or row[0] is None:
        return None
    v = row[0]
    return v.date() if hasattr(v, "date") else v


def invited(db: Session, referrer_id: int) -> list:
    """Shu o'quvchi olib kelgan HAMMA odam — lid bo'lganlar ham,
    o'quvchiga aylanganlar ham. Ro'yxat ilovada ko'rinadi."""
    out = []
    seen_students = set()

    students = (db.query(models.Student)
                .filter(models.Student.referred_by_student_id == referrer_id)
                .all())
    for st in students:
        seen_students.add(st.id)
        pay = first_payment_date(db, st.id)
        out.append({
            "kind": "student",
            "id": st.id,
            "name": mask_name(st.full_name),
            "stage": "paid" if pay else "enrolled",
            "paid_date": pay.isoformat() if pay else None,
            "period": month_key(pay) if pay else None,
        })

    leads = (db.query(models.Lead)
             .filter(models.Lead.referrer_student_id == referrer_id).all())
    for l in leads:
        if l.converted_student_id and l.converted_student_id in seen_students:
            continue        # allaqachon o'quvchi bo'lib yuqorida bor
        out.append({
            "kind": "lead",
            "id": l.id,
            "name": mask_name(l.full_name),
            "stage": "processing" if l.stage != "new" else "invited",
            "paid_date": None,
            "period": None,
        })
    out.sort(key=lambda r: (r["paid_date"] or "9999", r["name"]))
    return out


def paid_count(db: Session, referrer_id: int, period: str = None) -> int:
    """SHU OY ichida to'lagan do'stlar soni.

    Jahongir: "to'laganlargina hisobga olinadi ... SHU OY ichida".
    Ya'ni do'stning BIRINCHI to'lovi shu oyga tushsa — sanaladi."""
    period = period or month_key()
    n = 0
    for r in invited(db, referrer_id):
        if r["kind"] == "student" and r["period"] == period:
            n += 1
    return n


# =====================================================================
#  3-QADAM — CHEGIRMA
# =====================================================================

def _monthly_fee(s: models.Student) -> float:
    """O'quvchining oylik narxi."""
    try:
        if s.group is None:
            return 0.0
        fee = float(s.group.monthly_fee or 0)
        if not fee:
            fee = float((s.group.lesson_price or 0)
                        * (s.group.standard_lessons_per_month or 12))
        return fee
    except Exception:
        return 0.0


def payable_base(db: Session, s: models.Student) -> float:
    """Boshqa chegirmalar ayrilgandan KEYINGI summa.

    Jahongir: "oilaviy chegirmasi bo'lsa o'sha TO'LAYDIGAN SUMMADAN
    10% foiz hisoblanib ketaveradi". Shuning uchun referal foizi
    to'liq narxdan emas, shu bazadan olinadi. O'z chegirmasi
    hisobdan chiqariladi — aks holda halqa hosil bo'lardi."""
    fee = _monthly_fee(s)
    if fee <= 0:
        return 0.0
    other = _student_discount_percent(db, s, skip_kinds=("app_referral",))
    other = max(0.0, min(100.0, float(other or 0)))
    return round(fee * (100.0 - other) / 100.0, 2)


def target_period(db: Session, s: models.Student, on: date = None) -> str:
    """Chegirma QAYSI OYGA tushadi.

    Do'kon chegirmasidagi qoida (2026-08-20, Jahongir tasdiqlagan):
    shu oyga to'lamagan (qarzli) bo'lsa — shu oyga va balans darrov
    o'zgaradi; to'lab bo'lgan bo'lsa — keyingi oyga."""
    return roles.shop_discount_period_by_balance(
        student_balance(db, s.id), on)


def recompute(db: Session, referrer: models.Student, on: date = None,
              commit: bool = True) -> dict:
    """Taklif qilgan o'quvchining chegirmasini QAYTA hisoblaydi.

    Idempotent: necha marta chaqirilsa ham natija bir xil. Yangi
    qator QO'SHMAYDI — nishon oydagi borini YANGILAYDI (Jahongir:
    "qo'shilmaydi 10+30=40% bo'lmaydi")."""
    on = on or roles.local_today()
    count_period = month_key(on)
    n = paid_count(db, referrer.id, count_period)
    pct = roles.referral_percent(n)
    period = target_period(db, referrer, on)
    first, last = month_bounds(period)

    row = (db.query(models.Discount)
           .filter(models.Discount.student_id == referrer.id,
                   models.Discount.kind == "app_referral",
                   models.Discount.period == period).first())

    if n <= 0:
        # Hech kim to'lamagan. HECH NARSA O'CHIRILMAYDI — bor qator
        # bo'lsa "cancelled" bo'ladi (tarix qoladi, balansdan esa
        # tushirilmagan bo'lsa ishlamaydi).
        if row is not None and row.status == "active" \
                and row.applied_at is None:
            row.status = "cancelled"
            row.reason = (row.reason or "") + " | bekor: do'st to'lovi yo'q"
            if commit:
                db.commit()
        return {"level": 0, "percent": 0.0, "amount": 0.0,
                "period": period, "friends": 0}

    base = payable_base(db, referrer)
    amount = round(base * pct / 100.0, 0)
    reason = (f"Do'st taklifi: {count_period} oyida {n} ta do'st to'lov "
              f"qildi -> {pct:.0f}% ({n}-daraja)")

    if row is None:
        row = models.Discount(
            student_id=referrer.id, kind="app_referral",
            percent=None, amount=amount, reason=reason,
            start_date=first, end_date=last, status="active",
            period=period, requested_by="Referal dasturi",
            approved_by="Referal dasturi (avtomat)",
            approved_at=datetime.utcnow())
        db.add(row)
    else:
        # Balansga ALLAQACHON tushgan bo'lsa — summani o'zgartirmaymiz,
        # aks holda pul ikki marta hisoblanardi. Farqi keyingi oyga
        # o'tadi: dvigatel keyingi chaqiriqda yangi oyni oladi.
        if row.applied_at is None:
            row.amount = amount
            row.percent = None
            row.reason = reason
            row.status = "active"
            row.start_date, row.end_date = first, last
    if commit:
        db.commit()
    return {"level": min(n, roles.REFERRAL_MAX_LEVEL), "percent": pct,
            "amount": float(amount), "period": period, "friends": n,
            "base": base}


def on_payment(db: Session, student: models.Student) -> dict:
    """To'lov qabul qilinganda chaqiriladi.

    Agar TO'LAGAN o'quvchi kimningdir havolasi orqali kelgan bo'lsa —
    o'sha odamning chegirmasi qayta hisoblanadi va balansga tushiriladi.
    HECH QACHON xato tashlamaydi: to'lov qabul qilish bu yerdagi
    muammo tufayli yiqilmasligi kerak."""
    try:
        rid = getattr(student, "referred_by_student_id", None)
        if not rid:
            return {"ok": False, "why": "havoladan kelmagan"}
        ref = db.query(models.Student).get(rid)
        if ref is None or ref.status == "archived":
            return {"ok": False, "why": "taklif qilgan o'quvchi yo'q"}
        res = recompute(db, ref)
        if res["friends"] > 0:
            try:
                _apply_shop_discounts(db, res["period"], kind="app_referral")
            except Exception:
                db.rollback()
        res["ok"] = True
        res["referrer_id"] = ref.id
        res["referrer_name"] = ref.full_name
        return res
    except Exception as e:      # noqa: BLE001 - to'lov yiqilmasin
        try:
            db.rollback()
        except Exception:
            pass
        return {"ok": False, "why": str(e)[:200]}


# =====================================================================
#  4-QADAM — HOLAT (ilovada ko'rinadigan hamma narsa)
# =====================================================================

def state(db: Session, s: models.Student, base_url: str = "") -> dict:
    """O'quvchining referal ekrani uchun to'liq holat.

    Jahongir: "referallar holati ko'rinib turishi kerak"."""
    code = ensure_code(db, s)
    link = f"{(base_url or '').rstrip('/')}/r/{code}" if base_url \
        else f"/r/{code}"
    period = month_key()
    rows = invited(db, s.id)

    this_month = [r for r in rows
                  if r["kind"] == "student" and r["period"] == period]
    waiting = [r for r in rows if r["stage"] in ("invited", "processing",
                                                 "enrolled")]
    other_month = [r for r in rows
                   if r["kind"] == "student" and r["period"]
                   and r["period"] != period]

    n = len(this_month)
    pct = roles.referral_percent(n)
    tgt = target_period(db, s) if n else period
    base = payable_base(db, s)
    amount = round(base * pct / 100.0, 0) if n else 0.0

    # Bo'lib berilgan chegirma (bazadagi haqiqiy qator)
    given = (db.query(models.Discount)
             .filter(models.Discount.student_id == s.id,
                     models.Discount.kind == "app_referral")
             .order_by(models.Discount.id.desc()).all())

    return {
        "code": code,
        "link": link,
        "share_text": share_text(s, link),
        "period": period,
        "level": min(n, roles.REFERRAL_MAX_LEVEL),
        "percent": pct,
        "amount": amount,
        "base": base,
        "target_period": tgt,
        "next_hint": roles.referral_next_hint(n),
        "ladder": [{"n": k, "percent": v}
                   for k, v in sorted(roles.REFERRAL_LADDER.items())],
        "friends": rows,
        "paid_this_month": len(this_month),
        "waiting": len(waiting),
        "paid_other_months": len(other_month),
        "total_invited": len(rows),
        "history": [{
            "period": d.period,
            "amount": float(d.amount or 0),
            "reason": d.reason,
            "status": d.status,
            "applied": bool(d.applied_at),
        } for d in given],
        "rules": [
            "Havolangni do'stingga yubor — u ariza qoldiradi.",
            "Do'sting guruhga qo'shilib TO'LOV qilsa, hisobga olinadi.",
            f"1-do'st {roles.REFERRAL_LADDER[1]:.0f}%, "
            f"2-do'st {roles.REFERRAL_LADDER[2]:.0f}%, "
            f"3-do'st {roles.REFERRAL_LADDER[3]:.0f}%, "
            f"4-do'st {roles.REFERRAL_LADDER[4]:.0f}%, "
            f"5-do'st {roles.REFERRAL_LADDER[5]:.0f}% chegirma.",
            "Foizlar QO'SHILMAYDI — daraja oldingisini almashtiradi.",
            "Hisob har oy yangilanadi: do'st SHU OY ichida to'lashi kerak.",
            "Chegirma 1 oyga beriladi.",
            "Boshqa chegirmang bo'lsa, foiz to'laydigan summangdan olinadi.",
        ],
    }
