"""BARABAN — lidlar testi oxiridagi sovg'a g'ildiragi (2026-09-25).

Jahongir: "yangi lidlar ishlaydigan test bor shu testni bajargan
oquvchiga oxirida baraban chiqishi kerak va barabanda xar xil
sovgalar skidkalar 10-100%gacha coinlar 10-100gacha bo'lishi kerak
aylantirganda bittasiga tushsa shu sovga avtomat unga otishi kerak".

Tasdiqlangan qoidalar (Jahongir: "ha"):
  1. Ehtimolliklar Sozlamalarda (roles.WHEEL_DEFAULT_PRIZES boshlang'ich).
  2. Chegirma FAQAT BIRINCHI OYGA (faollashgan oy).
  3. 70% va 100% tushsa asoschiga darrov Telegram.

QANDAY ISHLAYDI.
  - Sovg'ani SERVER tanlaydi (secrets.SystemRandom) va shu zahoti
    wheel_spins ga yozadi. Telefon faqat animatsiya qiladi: unga
    qaysi bo'lakka tushgani AYTILADI. Aks holda brauzerda o'zgartirib
    100% olish mumkin bo'lardi.
  - BIR LIDGA BIR AYLANTIRISH: lid_id yoki telefon bo'yicha oldingi
    aylantirish bo'lsa, o'shani qaytaradi. Qayta test topshirsa ham
    ikkinchi sovg'a yo'q.
  - Sovg'a lidda "kutib" turadi. Liddan o'quvchi ochilganda:
      tanga     -> darrov CoinEntry (o'quvchi bor, balans bor);
      chegirma  -> FAOLLASHGANDA, o'sha oy uchun models.Discount
                   (kind="wheel", status="active", faqat bir oy).
    Chegirma ODDIY yo'l bilan ishlaydi — mavjud _student_discount_percent
    va _recharge_current_month. Bu yerda yangi pul mantiqi YO'Q.
  - Hech narsa o'chirilmaydi: bo'lak is_active=0 bo'ladi, aylantirish
    qatori har doim qoladi, qo'llanish izi (qaysi chegirma, qaysi
    tanga yozuvi, qachon) shu qatorda.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import secrets
from calendar import monthrange
from datetime import date, datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

import audit
import models
import notify
import roles
from auth import require_role
from database import get_db

router = APIRouter()
_RNG = secrets.SystemRandom()
BY = "Baraban (avtomat)"


# ------------------------------------------------------------ yordamchi
def _tail(v) -> str:
    """Telefonning oxirgi 9 raqami — solishtirish uchun."""
    d = "".join(ch for ch in str(v or "") if ch.isdigit())
    return d[-9:] if len(d) >= 9 else ""


def _month_end(d: date, months: int = 1) -> date:
    """d dan boshlab `months` oy: oxirgi oyning oxirgi kuni."""
    y, m = d.year, d.month + max(int(months), 1) - 1
    while m > 12:
        m -= 12
        y += 1
    return date(y, m, monthrange(y, m)[1])


# ------------------------------------------------------------ bo'laklar
def seed_prizes(db: Session) -> int:
    """Boshlang'ich bo'laklar — bazada bittasi ham bo'lmasa. Keyin
    asoschi Sozlamalardan o'zgartiradi, kod aralashmaydi.

    Marker (wheel_v1) sovuq startda so'rov bo'lmasligi uchun; bo'laklar
    hech qachon o'chirilmagani uchun (is_active=0) marker yetarli."""
    from common import _seed_done, _seed_mark
    if _seed_done(db, "wheel_v1"):
        return 0
    if db.query(models.WheelPrize.id).first() is not None:
        _seed_mark(db, "wheel_v1")
        return 0
    n = 0
    for i, (kind, value, weight, label) in enumerate(
            roles.WHEEL_DEFAULT_PRIZES):
        db.add(models.WheelPrize(kind=kind, value=int(value),
                                 weight=float(weight), label=label,
                                 order_no=i, is_active=1,
                                 updated_by="seed"))
        n += 1
    db.commit()
    _seed_mark(db, "wheel_v1")
    return n


def active_prizes(db: Session) -> list:
    return (db.query(models.WheelPrize)
            .filter(models.WheelPrize.is_active == 1)
            .order_by(models.WheelPrize.order_no, models.WheelPrize.id)
            .all())


def prize_out(p) -> dict:
    return {"id": p.id, "kind": p.kind, "value": int(p.value),
            "weight": float(p.weight or 0), "label": p.label or "",
            "order_no": int(p.order_no or 0),
            "is_active": bool(p.is_active)}


def pick_prize(prizes: list):
    """Og'irlik bo'yicha tasodifiy tanlov. Hamma og'irlik 0 bo'lsa —
    teng ehtimol."""
    if not prizes:
        return None
    total = sum(max(float(p.weight or 0), 0.0) for p in prizes)
    if total <= 0:
        return prizes[_RNG.randrange(len(prizes))]
    r = _RNG.random() * total
    acc = 0.0
    for p in prizes:
        acc += max(float(p.weight or 0), 0.0)
        if r < acc:
            return p
    return prizes[-1]


# ------------------------------------------------------------ aylantirish
def find_spin(db: Session, *, lead_id=None, phone=None, token=None):
    """Oldingi aylantirish: lid -> telefon -> havola tartibida."""
    if lead_id:
        sp = (db.query(models.WheelSpin)
              .filter(models.WheelSpin.lead_id == lead_id)
              .order_by(models.WheelSpin.id).first())
        if sp is not None:
            return sp
    t = _tail(phone)
    if t:
        sp = (db.query(models.WheelSpin)
              .filter(models.WheelSpin.phone == t)
              .order_by(models.WheelSpin.id).first())
        if sp is not None:
            return sp
    if token:
        sp = (db.query(models.WheelSpin)
              .filter(models.WheelSpin.session_token == token)
              .order_by(models.WheelSpin.id).first())
        if sp is not None:
            return sp
    return None


def spin_index(prizes: list, spin) -> int:
    """Telefon animatsiyasi uchun: sovg'a ro'yxatning nechanchi
    bo'lagi. Bo'lak keyin o'chirilgan bo'lsa — tur/qiymat bo'yicha."""
    for i, p in enumerate(prizes):
        if spin.prize_id and p.id == spin.prize_id:
            return i
    for i, p in enumerate(prizes):
        if p.kind == spin.prize_kind and int(p.value) == int(spin.prize_value):
            return i
    return -1


def spin_out(db: Session, spin, prizes: list = None) -> dict:
    prizes = active_prizes(db) if prizes is None else prizes
    return {
        "id": spin.id,
        "prize": {"kind": spin.prize_kind, "value": int(spin.prize_value),
                  "label": spin.prize_label or ""},
        "index": spin_index(prizes, spin),
        "spun_at": spin.spun_at.isoformat() if spin.spun_at else None,
        "applied": spin.applied_at is not None,
        "applied_student_id": spin.applied_student_id,
    }


def state_for_session(db: Session, s) -> dict:
    """Test sahifasi uchun: baraban chiqadimi, chiqsa qaysi bo'laklar."""
    prizes = active_prizes(db)
    existing = find_spin(db, lead_id=getattr(s, "lead_id", None),
                         phone=getattr(s, "phone", None),
                         token=getattr(s, "token", None))
    done = getattr(s, "status", None) == "done"
    return {
        "available": bool(done and prizes and existing is None),
        "spun": existing is not None,
        "prizes": [{"kind": p.kind, "value": int(p.value),
                    "label": p.label or ""} for p in prizes],
        "spin": spin_out(db, existing, prizes) if existing else None,
    }


def _founders_tg(db: Session, text: str) -> int:
    n = 0
    try:
        for u in (db.query(models.User)
                  .filter(models.User.role == roles.FOUNDER,
                          models.User.is_active == 1,
                          models.User.telegram_chat_id.isnot(None)).all()):
            if notify.send(u.telegram_chat_id, text):
                n += 1
    except Exception:
        pass
    return n


def spin_for_session(db: Session, s):
    """Aylantirish. (spin, yangi_yaratildimi) qaytaradi. Idempotent."""
    if getattr(s, "status", None) != "done":
        raise HTTPException(409, "Baraban test tugagandan keyin chiqadi")
    existing = find_spin(db, lead_id=getattr(s, "lead_id", None),
                         phone=getattr(s, "phone", None),
                         token=getattr(s, "token", None))
    if existing is not None:
        return existing, False
    prizes = active_prizes(db)
    if not prizes:
        raise HTTPException(409, "Baraban sozlanmagan — sovg'alar yo'q")
    p = pick_prize(prizes)
    spin = models.WheelSpin(
        lead_id=getattr(s, "lead_id", None),
        session_token=getattr(s, "token", None),
        phone=_tail(getattr(s, "phone", None)) or None,
        name=getattr(s, "name", None),
        branch_id=getattr(s, "branch_id", None),
        prize_id=p.id, prize_kind=p.kind, prize_value=int(p.value),
        prize_label=p.label or f"{p.value}",
        spun_at=datetime.utcnow())
    db.add(spin)
    db.flush()
    audit.log(db, None, entity="lead", action="wheel_spin",
              entity_id=spin.lead_id, entity_label=spin.name or "",
              new_value=spin.prize_label,
              note=f"Baraban: {spin.prize_label} tushdi (spin #{spin.id})",
              branch_id=spin.branch_id)
    # Katta chegirma — asoschi darrov bilsin (tasdiqlangan qoida).
    big = ((spin.prize_kind == "discount"
            and int(spin.prize_value) >= roles.WHEEL_NOTIFY_FROM_PERCENT)
           or (spin.prize_kind == "discount_sum"
               and int(spin.prize_value) >= roles.WHEEL_NOTIFY_FROM_SUM))
    if big:
        br = (db.query(models.Branch).get(spin.branch_id)
              if spin.branch_id else None)
        text = ("JONYOS — BARABAN\n\n"
                f"{spin.name or 'Lid'} ({spin.phone or 'telefon yo`q'}) "
                f"barabandan {spin.prize_label} yutdi.\n"
                + (f"Filial: {br.name}\n" if br else "")
                + (f"Lid #{spin.lead_id}\n" if spin.lead_id else "")
                + "\nChegirma o'quvchi faollashganda FAQAT birinchi "
                  "oyga avtomat qo'llanadi.")
        if _founders_tg(db, text):
            spin.notified_at = datetime.utcnow()
    db.commit()
    return spin, True


# ------------------------------------------------------------ qo'llash
def _spin_for_student(db: Session, s):
    """O'quvchiga tegishli aylantirish: bog'langan -> lid -> telefon."""
    sp = (db.query(models.WheelSpin)
          .filter(models.WheelSpin.applied_student_id == s.id)
          .order_by(models.WheelSpin.id).first())
    if sp is not None:
        return sp
    lead = (db.query(models.Lead)
            .filter(models.Lead.converted_student_id == s.id)
            .order_by(models.Lead.id).first())
    if lead is not None:
        sp = find_spin(db, lead_id=lead.id, phone=lead.phone)
        if sp is not None and sp.applied_student_id in (None, s.id):
            return sp
    t = _tail(getattr(s, "phone", None))
    if t:
        sp = (db.query(models.WheelSpin)
              .filter(models.WheelSpin.phone == t,
                      models.WheelSpin.applied_student_id.is_(None))
              .order_by(models.WheelSpin.id).first())
        if sp is not None:
            return sp
    return None


def apply_for_student(db: Session, s, *, on: Optional[date] = None,
                      user=None, commit: bool = True) -> Optional[dict]:
    """Lidga tushgan sovg'ani o'quvchiga qo'llash. IDEMPOTENT — necha
    marta chaqirilsa ham bir marta qo'llaydi.

    on — faollashish sanasi. Berilsa (faollashtirish yo'li) chegirma
    shu oyga yoziladi. Berilmasa (liddan o'quvchi ochish yo'li) faqat
    tanga; chegirma faollashishni kutadi. O'quvchi allaqachon faol
    bo'lsa — bugungi oy olinadi va shu oy hisobi qayta yoziladi."""
    spin = _spin_for_student(db, s)
    if spin is None:
        return None
    changed = False
    if spin.applied_student_id is None:
        spin.applied_student_id = s.id
        changed = True
    out = {"spin_id": spin.id, "kind": spin.prize_kind,
           "value": int(spin.prize_value), "label": spin.prize_label,
           "coin_entry_id": spin.coin_entry_id,
           "discount_id": spin.discount_id, "did": None}

    if spin.prize_kind == "coin" and spin.coin_entry_id is None:
        ce = models.CoinEntry(
            student_id=s.id, amount=int(spin.prize_value), source="wheel",
            ref_id=spin.id, note=f"Baraban sovg'asi: {spin.prize_label}",
            created_by=BY)
        db.add(ce)
        db.flush()
        spin.coin_entry_id = ce.id
        spin.applied_at = datetime.utcnow()
        audit.log(db, user, entity="student", action="wheel_coins",
                  entity_id=s.id, entity_label=s.full_name,
                  new_value=str(int(spin.prize_value)),
                  note=f"Baraban: {spin.prize_label} tangaga yozildi "
                       f"(spin #{spin.id})",
                  branch_id=s.branch_id)
        out["coin_entry_id"] = ce.id
        out["did"] = "coins"
        changed = True

    if (spin.prize_kind in roles.WHEEL_DISCOUNT_KINDS
            and spin.discount_id is None):
        # Faollashtirish yo'lida (on berilgan) hisob HALI yozilmagan —
        # u chegirmani o'zi hisobga oladi. O'quvchi ALLAQACHON faol
        # bo'lsa (on yo'q) — bugungi oy va shu oy hisobini qayta yozish.
        recharge = False
        if on is None and getattr(s, "status", None) == "active":
            on = roles.local_today()
            recharge = True
        if on is not None:
            first = on
            last = _month_end(on, roles.WHEEL_DISCOUNT_MONTHS)
            # Foizli yoki so'mli (2026-09-26). So'mli chegirma ODDIY
            # yo'l bilan ishlaydi: _student_discount_percent uni guruh
            # oyligiga nisbatan foizga aylantiradi.
            is_sum = spin.prize_kind == "discount_sum"
            d = models.Discount(
                student_id=s.id, kind="wheel",
                percent=None if is_sum else float(int(spin.prize_value)),
                amount=float(int(spin.prize_value)) if is_sum else None,
                reason=(f"Baraban sovg'asi: {spin.prize_label} — faqat "
                        f"{first.strftime('%m.%Y')} oyi (lid testi)"),
                start_date=first, end_date=last, status="active",
                hidden=0, requested_by=BY, approved_by=BY,
                approved_at=datetime.utcnow())
            db.add(d)
            db.flush()
            spin.discount_id = d.id
            spin.applied_at = datetime.utcnow()
            audit.log(db, user, entity="discount", action="create",
                      entity_id=d.id, entity_label=s.full_name,
                      new_value=(f"Baraban {roles.som_short(spin.prize_value)}"
                                 if is_sum
                                 else f"Baraban {int(spin.prize_value)}%"),
                      note=f"Baraban sovg'asi avtomat: {spin.prize_label}, "
                           f"{first.isoformat()} — {last.isoformat()} "
                           f"(spin #{spin.id})",
                      branch_id=s.branch_id)
            out["discount_id"] = d.id
            out["did"] = "discount"
            changed = True
            # Hisob ALLAQACHON yozilgan bo'lsa (o'quvchi oldin
            # faollashgan) — shu oy hisobi qayta yoziladi (summa joyida
            # to'g'rilanadi, qator o'chirilmaydi, audit yoziladi).
            if recharge:
                try:
                    import finance as _fin
                    db.flush()
                    _fin._recharge_current_month(db, s)
                except Exception:
                    pass
    if changed:
        if commit:
            db.commit()
        else:
            db.flush()
    return out


def lead_wheel_out(db: Session, lead) -> Optional[dict]:
    sp = find_spin(db, lead_id=lead.id, phone=lead.phone)
    return spin_out(db, sp) if sp is not None else None


# ------------------------------------------------------------ API (xodim)
class PrizeIn(BaseModel):
    # kind: coin (tanga) | discount (foiz) | discount_sum (so'm)
    id: Optional[int] = None
    kind: str
    value: int
    weight: float = 1.0
    label: Optional[str] = None
    is_active: bool = True
    order_no: int = 0


@router.get("/api/wheel/prizes")
def list_prizes(db: Session = Depends(get_db),
                user=Depends(require_role(*roles.LEAD_ACCESS))):
    """Bo'laklar (faol va o'chirilganlar ham — hech narsa yo'qolmaydi)."""
    seed_prizes(db)
    rows = (db.query(models.WheelPrize)
            .order_by(models.WheelPrize.order_no, models.WheelPrize.id).all())
    tw = sum(max(float(p.weight or 0), 0) for p in rows if p.is_active)
    out = []
    for p in rows:
        d = prize_out(p)
        d["percent"] = (round(max(float(p.weight or 0), 0) * 100 / tw, 1)
                        if (tw and p.is_active) else 0.0)
        out.append(d)
    exp = 0.0
    exp_sum = 0.0
    for p in rows:
        if p.is_active and p.kind == "discount" and tw:
            exp += max(float(p.weight or 0), 0) / tw * int(p.value)
        if p.is_active and p.kind == "discount_sum" and tw:
            exp_sum += max(float(p.weight or 0), 0) / tw * int(p.value)
    return {"prizes": out, "total_weight": tw,
            "expected_discount_percent": round(exp, 1),
            "expected_discount_sum": round(exp_sum),
            "notify_from_sum": roles.WHEEL_NOTIFY_FROM_SUM,
            "notify_from": roles.WHEEL_NOTIFY_FROM_PERCENT,
            "discount_months": roles.WHEEL_DISCOUNT_MONTHS}


@router.put("/api/wheel/prizes")
def save_prizes(payload: List[PrizeIn], db: Session = Depends(get_db),
                user=Depends(require_role(roles.FOUNDER))):
    """Faqat asoschi. Ro'yxatda YO'Q bo'lak o'chirilmaydi — is_active=0."""
    seen = set()
    for i, it in enumerate(payload):
        if it.kind not in ("coin",) + roles.WHEEL_DISCOUNT_KINDS:
            raise HTTPException(400, f"Noto'g'ri tur: {it.kind}")
        if it.kind == "discount" and not (0 < it.value <= 100):
            raise HTTPException(400, "Chegirma 1..100% oralig'ida bo'lsin")
        if it.kind == "discount_sum" and not (
                roles.WHEEL_SUM_MIN <= it.value <= roles.WHEEL_SUM_MAX):
            raise HTTPException(
                400, f"So'm chegirma {roles.som_short(roles.WHEEL_SUM_MIN)}"
                     f" .. {roles.som_short(roles.WHEEL_SUM_MAX)} "
                     f"oralig'ida bo'lsin")
        if it.kind == "coin" and not (0 < it.value <= 10000):
            raise HTTPException(400, "Tanga 1..10000 oralig'ida bo'lsin")
        if it.weight < 0:
            raise HTTPException(400, "Og'irlik manfiy bo'lmaydi")
        p = db.query(models.WheelPrize).get(it.id) if it.id else None
        if p is None:
            p = models.WheelPrize()
            db.add(p)
        p.kind, p.value, p.weight = it.kind, int(it.value), float(it.weight)
        p.label = (it.label or "").strip() or (
            f"{it.value}% chegirma" if it.kind == "discount"
            else f"{roles.som_short(it.value)} chegirma"
            if it.kind == "discount_sum"
            else f"{it.value} tanga")
        p.is_active = 1 if it.is_active else 0
        p.order_no = int(it.order_no or i)
        p.updated_by = user.full_name
        db.flush()
        seen.add(p.id)
    for p in db.query(models.WheelPrize).all():
        if p.id not in seen and p.is_active:
            p.is_active = 0
            p.updated_by = user.full_name
    audit.log(db, user, entity="settings", action="wheel_prizes",
              entity_label="Baraban", note=f"{len(payload)} ta bo'lak")
    db.commit()
    return list_prizes(db=db, user=user)


@router.get("/api/leads/{lead_id}/wheel")
def lead_wheel(lead_id: int, db: Session = Depends(get_db),
               user=Depends(require_role(*roles.LEAD_ACCESS))):
    lead = db.query(models.Lead).get(lead_id)
    if lead is None:
        raise HTTPException(404, "Lid topilmadi")
    return {"lead_id": lead.id, "spin": lead_wheel_out(db, lead)}


@router.get("/api/wheel/spins")
def list_spins(days: int = 30, db: Session = Depends(get_db),
               user=Depends(require_role(roles.FOUNDER,
                                         roles.BRANCH_MANAGER,
                                         roles.SALES_HEAD))):
    """Oxirgi aylantirishlar — kim nima yutdi, qo'llandimi."""
    from datetime import timedelta
    since = datetime.utcnow() - timedelta(days=max(1, min(int(days), 365)))
    rows = (db.query(models.WheelSpin)
            .filter(models.WheelSpin.spun_at >= since)
            .order_by(models.WheelSpin.id.desc()).limit(500).all())
    out = []
    for sp in rows:
        st = (db.query(models.Student).get(sp.applied_student_id)
              if sp.applied_student_id else None)
        out.append({**spin_out(db, sp), "name": sp.name, "phone": sp.phone,
                    "lead_id": sp.lead_id, "branch_id": sp.branch_id,
                    "student": st.full_name if st else None})
    return {"days": days, "spins": out, "count": len(out)}
