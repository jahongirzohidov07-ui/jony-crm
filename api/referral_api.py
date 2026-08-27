"""REFERAL — API yo'llari (2026-08-28).

To'rt tomon:
  OCHIQ (login yo'q)  — do'st ko'radigan marketing sahifasi va ariza
  O'QUVCHI            — o'z havolasi va referallar holati
  XODIM               — kim kimni olib kelgan, voronka
  RAHBAR              — qayta hisoblash tugmasi (xavfsizlik to'ri)

OCHIQ YO'LLARDA MAXFIYLIK: sahifa faqat taklif qilgan bolaning ISMINI
va kursini ko'rsatadi. Telefon, filial ichidagi ma'lumot, boshqa
o'quvchilar — HECH QAYSISI chiqmaydi. Kod noto'g'ri bo'lsa ham sahifa
ochiladi (oddiy ariza formasi bo'lib) — bot kod terib o'quvchi
qidirmasin."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

import audit
import models
import referral
import roles
from auth import get_current_user, require_role
from common import *  # noqa: F401,F403
from database import get_db

router = APIRouter()

_HITS: dict = {}
_MAX_PER_HOUR = 30


def _rate_ok(ip: str) -> bool:
    now = datetime.utcnow()
    hits = [t for t in _HITS.get(ip, []) if (now - t).seconds < 3600]
    hits.append(now)
    _HITS[ip] = hits[-100:]
    return len(hits) <= _MAX_PER_HOUR


# =====================================================================
#  OCHIQ — do'st ko'radigan sahifa
# =====================================================================

@router.get("/api/public/ref/{code}")
def public_ref(code: str, db: Session = Depends(get_db)):
    """Marketing sahifasi uchun ma'lumot. Auth YO'Q.

    Jahongir: "do'stiga yuborgan linkda men Jony Academyda falon
    kursga yozildim, shunaqa shunaqa foydalarni bor ekan deb maqtan"."""
    s = referral.by_code(db, code)
    ok = s is not None and s.status in ("active", "trial", "frozen")
    return {
        "ok": bool(ok),
        "code": (code or "").strip().upper(),
        # Faqat ISM — familiya ham chiqmaydi.
        "inviter": ((s.first_name or (s.full_name or "").split()[0])
                    if ok else None),
        "course": (s.subject or None) if ok else None,
        "branch": (s.branch.name if (ok and s.branch) else None),
    }


@router.post("/api/public/ref/{code}/lead")
def public_ref_lead(code: str, payload: dict, request: Request,
                    db: Session = Depends(get_db)):
    """Do'st havola sahifasida ariza qoldirdi -> YANGI LID.

    Jahongir: "u o'quvchi ro'yxatdan o'tadi va adminlarga so'rov
    boradi yangi lid bo'lib"."""
    ip = (request.client.host if request.client else "?") or "?"
    if not _rate_ok(ip):
        raise HTTPException(429, "Juda ko'p so'rov — birozdan keyin "
                                 "urinib ko'ring")

    def _s(key, limit=200):
        return str(payload.get(key) or "").strip()[:limit]

    if _s("hp", 50):                      # honeypot — bot to'ldiradi
        return {"ok": True}

    full_name = " ".join(_s("full_name", 120).split())
    phone = _s("phone", 40)
    digits = "".join(ch for ch in phone if ch.isdigit())
    if len(full_name) < 3:
        raise HTTPException(400, "Ismingizni to'liq yozing")
    if len(digits) < 7:
        raise HTTPException(400, "Telefon raqamini to'g'ri kiriting")

    inviter = referral.by_code(db, code)

    # O'ZINI O'ZI TAKLIF QILISH BO'LMASIN: o'sha raqam bilan.
    if inviter is not None:
        own = "".join(ch for ch in (inviter.phone or "") if ch.isdigit())
        if own and own[-9:] == digits[-9:]:
            raise HTTPException(400, "Bu sizning o'z raqamingiz")

    # TAKROR: shu raqamdan 24 soat ichida ariza kelgan bo'lsa - yangi
    # lid ochilmaydi (odam tugmani ikki marta bosishi mumkin).
    tail = digits[-9:]
    since = datetime.utcnow() - timedelta(hours=24)
    for l in (db.query(models.Lead)
              .filter(models.Lead.created_at >= since).all()):
        d = "".join(ch for ch in (l.phone or "") if ch.isdigit())
        if d and d[-9:] == tail:
            return {"ok": True, "duplicate": True, "lead_id": l.id}

    # ALLAQACHON O'QUVCHIMI: bo'lsa ham ariza qabul qilinadi (odam
    # boshqa kursga yozilmoqchi bo'lishi mumkin), lekin izohda
    # ko'rsatiladi — admin adashib referal deb hisoblamasin.
    already = None
    for st in db.query(models.Student).filter(
            models.Student.status.in_(["active", "trial", "frozen"])).all():
        d = "".join(ch for ch in (st.phone or "") if ch.isdigit())
        if d and d[-9:] == tail:
            already = st
            break

    course = _s("course", 120)
    note = ["Do'st taklifi (Jony Student havolasi)"]
    if inviter is not None:
        note.append(f"Taklif qilgan: {inviter.full_name} "
                    f"({inviter.public_id or inviter.id}), kod {code}")
    else:
        note.append(f"Kod topilmadi: {code}")
    if course:
        note.append(f"Yo'nalish: {course}")
    if _s("note", 500):
        note.append(f"Izoh: {_s('note', 500)}")
    if already is not None:
        note.append(f"DIQQAT: bu raqam allaqachon o'quvchi — "
                    f"{already.full_name}. Referal chegirmasi FAQAT "
                    f"yangi o'quvchi to'lov qilsa beriladi.")

    lead = models.Lead(
        full_name=full_name,
        phone=phone,
        source="app_referral",
        stage=roles.LEAD_SOURCE_DEFAULT_STAGE.get("app_referral", "new"),
        branch_id=(inviter.branch_id if inviter is not None else None),
        referrer_student_id=(inviter.id if (inviter is not None
                                            and already is None) else None),
        note="\n".join(note),
        created_by="Referal havolasi")
    db.add(lead); db.commit(); db.refresh(lead)
    _ensure_public_id(db, "lead", lead)
    db.commit()

    # Adminlarga vazifa — ariza javobsiz qolmasin.
    try:
        kim = inviter.full_name if inviter is not None else "?"
        _hr_task(db,
                 title=(f"Do'st taklifi: {full_name} "
                        f"({lead.public_id or lead.id})"),
                 body=("\n".join(note)
                       + f"\nTelefon: {phone}\n"
                         f"Kim olib keldi: {kim}\n"
                         "Bugunning o'zida qo'ng'iroq qiling — bu "
                         "o'quvchimizning tavsiyasi bilan kelgan odam."),
                 to_roles=[roles.ADMINISTRATOR, roles.SALES_MANAGER,
                           roles.SALES_HEAD, roles.BRANCH_MANAGER],
                 branch_id=lead.branch_id, days=1, priority="high")
        db.commit()
    except Exception:
        db.rollback()

    return {"ok": True, "lead_id": lead.id,
            "public_id": lead.public_id,
            "inviter": (inviter.first_name
                        or (inviter.full_name or "").split()[0])
                       if inviter is not None else None}


# =====================================================================
#  O'QUVCHI — o'z havolasi va holati
# =====================================================================

def _me(db: Session, user: models.User) -> models.Student:
    s = _student_of_user(db, user)
    if not s:
        raise HTTPException(403, "Bu bo'lim faqat o'quvchilar uchun")
    why = roles.student_app_block_reason(s.status)
    if why:
        raise HTTPException(403, why)
    return s


@router.get("/api/student/referral")
def my_referral(request: Request, db: Session = Depends(get_db),
                user=Depends(get_current_user)):
    """Ilovadagi "Do'stingni olib kel" ekrani."""
    s = _me(db, user)
    base = str(request.base_url).rstrip("/") if request else ""
    origin = request.headers.get("origin") or request.headers.get("referer")
    if origin:
        # Brauzer manzili (jonyos.uz) - API manzilidan ishonchliroq
        try:
            from urllib.parse import urlparse
            u = urlparse(origin)
            if u.scheme and u.netloc:
                base = f"{u.scheme}://{u.netloc}"
        except Exception:
            pass
    return referral.state(db, s, base)


# =====================================================================
#  XODIM — kim kimni olib keldi
# =====================================================================

# DIQQAT — MANZIL NOMI. "/api/referrals" ALLAQACHON BAND:
# gamification.py da eski QO'LDA yoziladigan referral (kim kimni olib
# kelgani) shu manzilda turibdi. Ikkalasi bir nom olsa, FastAPI
# birinchi ro'yxatdan o'tganini oladi va ikkinchisi JIM o'ladi —
# aynan shunday xato test paytida topildi (403 qaytardi).
# Shuning uchun yangi dastur alohida nomda: /api/referral-program.
@router.get("/api/referral-program")
def referral_report(branch_id: int = None, period: str = None,
                    db: Session = Depends(get_db),
                    user=Depends(require_role(*roles.LEAD_ACCESS))):
    """Referal voronkasi: taklif -> lid -> o'quvchi -> to'lov -> chegirma."""
    period = period or referral.month_key()
    q = scope_to_branch(db.query(models.Student), models.Student,
                        user, branch_id)
    students = q.filter(models.Student.ref_code.isnot(None)).all()

    # Lid va o'quvchilarni bir marta yig'amiz (N+1 bo'lmasin)
    leads = (db.query(models.Lead)
             .filter(models.Lead.referrer_student_id.isnot(None)).all())
    kids = (db.query(models.Student)
            .filter(models.Student.referred_by_student_id.isnot(None)).all())
    by_ref_leads: dict = {}
    for l in leads:
        by_ref_leads.setdefault(l.referrer_student_id, []).append(l)
    by_ref_kids: dict = {}
    for k in kids:
        by_ref_kids.setdefault(k.referred_by_student_id, []).append(k)

    ids = {s.id for s in students}
    rows = []
    for s in students:
        ls = by_ref_leads.get(s.id, [])
        ks = by_ref_kids.get(s.id, [])
        if not ls and not ks:
            continue
        paid = 0
        for k in ks:
            d = referral.first_payment_date(db, k.id)
            if d and referral.month_key(d) == period:
                paid += 1
        rows.append({
            "student_id": s.id,
            "name": s.full_name,
            "public_id": s.public_id,
            "code": s.ref_code,
            "branch": s.branch.name if s.branch else None,
            "leads": len(ls),
            "students": len(ks),
            "paid_this_period": paid,
            "level": min(paid, roles.REFERRAL_MAX_LEVEL),
            "percent": roles.referral_percent(paid),
        })
    # HAR BIR QATORGA ISHLAB TOPILGAN SUMMA. Chegirma qatorining o'z
    # oyi boshqa bo'lishi mumkin (qarzi yo'q bo'lsa KEYINGI oyga
    # tushadi), shuning uchun "shu oyda ishlab topildi" va "shu oyda
    # pul chiqadi" — IKKI XIL raqam. Ikkalasi ham beriladi, aks holda
    # hisobot "5 ta do'st to'lagan, chegirma 0" bo'lib ko'rinardi.
    by_id = {s.id: s for s in students}
    for r in rows:
        s = by_id[r["student_id"]]
        r["earned"] = round(referral.payable_base(db, s)
                            * r["percent"] / 100.0, 0) if r["percent"] else 0.0
    rows.sort(key=lambda r: (-r["paid_this_period"], -r["students"],
                             r["name"]))

    # Chegirmalar — shu oyda BALANSDAN chiqadigani
    ds = (db.query(models.Discount)
          .filter(models.Discount.kind == "app_referral",
                  models.Discount.period == period).all())
    given = [d for d in ds if d.student_id in ids] if branch_id else ds
    return {
        "period": period,
        "rows": rows,
        "totals": {
            "inviters": len(rows),
            "leads": sum(r["leads"] for r in rows),
            "students": sum(r["students"] for r in rows),
            "paid": sum(r["paid_this_period"] for r in rows),
            # shu oyda ISHLAB TOPILGAN (do'stlar shu oyda to'lagan)
            "earned_sum": round(sum(r["earned"] for r in rows), 0),
            # shu oyda BALANSDAN CHIQADIGAN (chegirma qatorining oyi)
            "discount_sum": round(sum(float(d.amount or 0) for d in given), 0),
            "discount_count": len(given),
        },
        "ladder": [{"n": k, "percent": v}
                   for k, v in sorted(roles.REFERRAL_LADDER.items())],
    }


@router.post("/api/referral-program/recompute")
def recompute_all(period: str = None, db: Session = Depends(get_db),
                  user=Depends(require_role(*roles.FULL_ACCESS))):
    """XAVFSIZLIK TO'RI: hamma referal chegirmasini qayta hisoblaydi.

    Odatda kerak bo'lmaydi — chegirma to'lov qabul qilinganda o'zi
    hisoblanadi. Lekin to'lov eski sana bilan kiritilsa yoki qo'lda
    tuzatish bo'lsa, shu tugma hammasini joyiga qo'yadi. Idempotent:
    necha marta bosilsa ham natija bir xil, dubl chiqmaydi."""
    kids = (db.query(models.Student)
            .filter(models.Student.referred_by_student_id.isnot(None)).all())
    ref_ids = sorted({k.referred_by_student_id for k in kids})
    done, changed = 0, 0
    for rid in ref_ids:
        ref = db.query(models.Student).get(rid)
        if ref is None:
            continue
        res = referral.recompute(db, ref)
        done += 1
        if res["friends"] > 0:
            changed += 1
            try:
                _apply_shop_discounts(db, res["period"], kind="app_referral")
            except Exception:
                db.rollback()
    audit.log(db, user, entity="referral", action="recompute",
              note=f"{done} ta taklif qiluvchi qayta hisoblandi")
    db.commit()
    return {"ok": True, "checked": done, "with_discount": changed}
