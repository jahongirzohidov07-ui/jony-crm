"""Auto-extracted from main.py during refactor (split-main). Domain: system."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bisect
from datetime import date, datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy import func, or_, text
from sqlalchemy.orm import Session

import audit
import billing
import migrations
import time as _time

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

@router.get("/api/_bootstrap")
def bootstrap(key: str, db: Session = Depends(get_db)):
    """One-time setup: creates the first admin account on a fresh database.
    Gated by the deploy secret so it's safe to leave live - it no-ops once
    any user exists."""
    if key != SECRET_KEY:
        raise HTTPException(403, "Forbidden")
    if db.query(models.User).count() > 0:
        return {"ok": False, "message": "Already initialized"}
    admin = models.User(
        username="admin",
        password_hash=hash_password("ChangeMe123!"),
        full_name="Administrator",
        role=roles.FOUNDER,
        branch_id=None,
    )
    db.add(admin)
    db.commit()
    return {"ok": True, "message": "Admin user created"}

@router.get("/api/health")
def health(request: Request, db: Session = Depends(get_db), db_check: int = 0):
    """Tiriklik tekshiruvi + BAZA QOROVULI (2026-09-06).

    Jahongir: "har 2 kunda bir vercel o'chib qolyabdi nima qilish
    kerak". Vercel hisobida limit muammosi yo'q (o'tgan oy: 10 soat
    CPU, $4.76 — $20 lik kreditdan ancha past), demak uzilish
    ko'pincha BAZA tomonidan bo'ladi. Ilgari bu yo'l bazaga umuman
    tegmasdi — shuning uchun "sayt ishlayaptimi" degan savolga
    ishonchli javob bermasdi va uzilish IZSIZ o'tib ketardi.

    Endi cron har 5 daqiqada shu yerni chaqirganda:
      · bazaga eng arzon so'rov (SELECT 1) yuboriladi;
      · javob bermasa — ErrorLog ga yoziladi va (Telegram ulangan
        bo'lsa) asoschiga xabar ketadi: qachon, qaysi sabab.
    Shunda keyingi safar "nega o'chdi" degan savolga aniq javob
    bo'ladi — taxmin qilib o'tirilmaydi."""
    t0 = _time.monotonic()
    out = {"status": "ok", "time": datetime.utcnow().isoformat()}
    # BAZAGA TEGISHNI CHEKLASH (2026-09-07, Jahongir: "bir oyda qancha
    # pul ketadi" tekshiruvidan keyin). Neon FAQAT UYG'OQ turgan vaqti
    # uchun pul oladi (o'tgan oy: 207 CU-soat = $21.97) va 5 daqiqa
    # so'rovsiz qolsa o'zi uxlaydi. Shuning uchun bu yo'l bazani
    # BEKORGA uyg'otmasligi kerak: baza faqat CRON chaqirganda (yoki
    # ?db_check=1 bilan qo'lda) tekshiriladi. Oddiy "sayt tirikmi"
    # so'rovi bazaga umuman tegmaydi.
    _ua = (request.headers.get("user-agent") or "").lower()
    if not (db_check or _ua.startswith("vercel-cron/")):
        out["db"] = "skipped"
        out["ms"] = int((_time.monotonic() - t0) * 1000)
        return out
    try:
        db.execute(text("SELECT 1"))
        out["db"] = "ok"
    except Exception as e:
        out["status"] = "db_error"
        out["db"] = type(e).__name__
        try:
            db.rollback()
        except Exception:
            pass
        _health_alarm(db, e)
    out["ms"] = int((_time.monotonic() - t0) * 1000)
    return out


def _health_alarm(db, exc) -> None:
    """Baza javob bermadi — izini qoldiramiz va asoschiga aytamiz."""
    msg = f"{type(exc).__name__}: {exc}"[:900]
    try:
        db.rollback()
    except Exception:
        pass
    try:
        db.add(models.ErrorLog(path="/api/health", method="GET",
                               user_name="qorovul (cron)", detail=msg))
        db.commit()
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass
    try:
        import notify
        if not notify.enabled():
            return
        when = roles.to_local(datetime.utcnow()).strftime("%d.%m.%Y %H:%M")
        text_ = ("JONYOS - BAZA JAVOB BERMAYAPTI\n"
                 f"Vaqt: {when}\n\n{msg}\n\n"
                 "Sayt shu payt ishlamayotgan bo'lishi mumkin. "
                 "Sabab odatda bazada (Neon) — kvota yoki ulanish "
                 "chegarasi.")
        for u in (db.query(models.User)
                  .filter(models.User.role == roles.FOUNDER,
                          models.User.is_active == 1,
                          models.User.telegram_chat_id.isnot(None)).all()):
            notify.send(u.telegram_chat_id, text_)
    except Exception:
        pass

@router.get("/api/reference")
def reference_lists(
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Formalarda tanlanadigan ro'yxatlar: mahallalar, maktablar,
    dars vaqtlari. Qo'lda yozish o'rniga tanlash - shundagina
    statistika chiqadi."""
    bname = None
    bid = branch_id or user.branch_id
    if bid:
        b = db.query(models.Branch).get(bid)
        bname = b.name if b else None
    return {
        "areas": roles.areas_for_branch(bname),
        "schools": roles.SCHOOLS,
        "lesson_times": [
            {"start": t, "end": roles.lesson_end_time(t),
             "label": roles.lesson_time_range(t)}
            for t in roles.LESSON_START_TIMES
        ],
        "lesson_minutes": roles.LESSON_DURATION_MINUTES,
        "exit_types": [{"key": k, "label": lbl, "hint": h}
                       for k, lbl, h in roles.EXIT_TYPES],
        "archive_groups": [{"key": k, "label": lbl, "hint": h}
                           for k, lbl, h in roles.ARCHIVE_GROUPS],
    }

@router.get("/api/cron/daily")
def cron_daily(request: Request, db: Session = Depends(get_db)):
    """Kunlik avtomat ishlar. Vercel Cron chaqiradi (vercel.json).
    CRON_SECRET o'rnatilgan bo'lsa Authorization tekshiriladi; bo'lmasa
    faqat Vercel cron user-agent qabul qilinadi. Qo'lda ham asoschi
    chaqirsa bo'ladi (token bilan)."""
    secret = os.environ.get("CRON_SECRET", "").strip()
    auth_hdr = request.headers.get("authorization", "")
    ua = request.headers.get("user-agent", "")
    ok_call = False
    if secret and auth_hdr == f"Bearer {secret}":
        ok_call = True
    elif ua.startswith("vercel-cron/"):
        ok_call = True
    else:
        # Tizimga kirgan asoschi qo'lda ham ishga tushira oladi
        try:
            tok = auth_hdr.replace("Bearer ", "")
            if tok:
                from jose import jwt as _jwt
                from auth import ALGORITHM as _alg
                payload = _jwt.decode(tok, SECRET_KEY, algorithms=[_alg])
                u = db.query(models.User).filter(
                    models.User.username == payload.get("sub")).first()
                ok_call = bool(u and u.role == roles.FOUNDER)
        except Exception:
            ok_call = False
    if not ok_call:
        raise HTTPException(403, "Ruxsat yo'q")
    _founder_name_fix(db)
    # Kunlik cron - eng katta ulush (Vercel limiti 30 s).
    _ensure_month_charges(db, budget_s=18.0)
    # KUNLIK ZAXIRA (2026-08-15). Asoschining Telegramiga fayl bo'lib
    # boradi. Bot sozlanmagan yoki chat bog'lanmagan bo'lsa jimgina
    # o'tadi - kunlik ish shu sababdan yiqilmasin.
    # Filialsiz qolgan o'quvchini guruhining filialiga biriktirish
    # va guruhsiz "faol" o'quvchini to'g'ri holatga o'tkazish
    try:
        from common import (backfill_student_branches as _bsb,
                            fix_groupless_active as _fga,
                            backfill_student_groups as _bsg)
        _bsb(db)
        _fga(db)
        # Guruh bog'lanishlari (2026-08-17) — bir martalik ko'chirish
        _bsg(db)
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass
    # NOMZOD <-> QUVUR MOSLIGI (2026-08-16, Jahongir: "ishga olish
    # quvuri bilan nomzodlar bo'limi deyarli bir biriga
    # bog'lanmayabdi"). Eski nomuvofiqlar kuniga bir marta
    # to'g'rilanadi — bosqichlar avtomat ergashishi 2026-08-15 da
    # qo'shilgan, undan oldingi yozuvlar turlicha qolgan.
    try:
        from hr_ats import fix_candidate_pipeline as _fcp
        _fcp(db)
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass
    # Sanasi kelgan kurs narxlari qo'llansin (2026-08-15)
    try:
        import courses as _crs
        _crs.apply_due_price_changes(db)
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass
    # KUNIGA BIR MARTA ISHLASHI KERAK BO'LGAN, LEKIN "KIMDIR SAHIFANI
    # OCHSA" ISHLAYDIGAN QOIDALAR (2026-09-06 auditi). Endi ular
    # cron'da ham yuradi — hech kim sahifani ochmasa ham bajariladi.
    # Har biri alohida try: biri yiqilsa qolgani ishlayveradi.
    for _name, _fn in (
        # Ustoz darajasi: ko'tarish/tushirish qoidalari. Ilgari faqat
        # Karyera sahifasi ochilganda ishlardi.
        ("grade_rules", lambda: __import__("hr")._apply_grade_rules(db)),
        # Muddati tugagan / holati o'zgargan chegirmalar
        ("expire_discounts", lambda: _expire_discounts(db)),
        # Ketish xavfi: bayroq + administratorga shoshilinch vazifa
        ("risk_scan", lambda: _risk_scan(db)),
        # Bo'shatilgan support biriktirishlari
        ("stale_support", lambda: _cleanup_stale_support_assignments(db)),
    ):
        try:
            _fn()
        except Exception:
            try:
                db.rollback()
            except Exception:
                pass

    bkp = {}
    try:
        import backup as _bkp
        bkp = _bkp.daily_backup_to_telegram(db)
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass
    return {"ok": True, "ran_at": datetime.utcnow().isoformat(),
            "backup": bkp}

@router.get("/api/search/students")
def global_student_search(q: str, branch_id: int | None = None,
                          db: Session = Depends(get_db),
                          user=Depends(get_current_user)):
    """Tepadagi qidiruv: 3 harfdan boshlab o'quvchilar va potensial
    o'quvchilar (lidlar). Ustoz faqat o'z guruhlaridagilarini ko'radi,
    lidlar unga chiqmaydi. Balans qaytarilmaydi.

    FILIAL DOIRASI (2026-08-18, Jahongir: "kimdur qidirsa o'z
    filialidagi o'quvchilarni chiqarginda, faqat asoschi barcha
    filiallarda turganda yoki boshqa xodim barcha filiallarda turganda
    qidiruv qilsa barcha filiallardagi o'quvchilari chiqarsin").

    Avval asoschi (va boshqa org-wide lavozimlar) tepadagi filial
    tanlagichiga UMUMAN qaramasdi — "Bekobod 2"da turgan bo'lsa ham
    qidiruv butun tarmoqni qaytarardi. Aynan shu chalkashlik keltirib
    chiqargan: Bekobod 2 da qidirilganda Zafar filialidagi boshqa bola
    chiqib, "shu bola muzlab qolibdi" degan xulosa chiqarilgan.

    Endi qoida oddiy va hamma uchun bir xil:
      - tepada aniq filial tanlangan bo'lsa -> faqat o'sha filial;
      - "Barcha filiallar" tanlangan bo'lsa  -> xodim kira oladigan
        barcha filiallar (asoschida - hammasi).
    Xodim o'ziga ruxsat berilmagan filialni so'rasa, baribir faqat
    o'ziniki qaytariladi — tanlagich orqali chetga chiqib bo'lmaydi."""
    if user.role in ("student", "parent"):
        raise HTTPException(403, "Ruxsat yo'q")
    q = (q or "").strip()
    if len(q) < 3:
        return {"students": [], "leads": [], "groups": [],
                "teachers": [], "staff": []}
    like = f"%{q}%"

    # TELEFON BO'YICHA QIDIRUV. Raqamlar bazada "+(998) 90-404-47-48"
    # ko'rinishida saqlanadi — foydalanuvchi esa "904044748" yoki
    # "90 404 47 48" deb yozadi. Shuning uchun ustundagi ortiqcha
    # belgilarni olib tashlab solishtiramiz (Jahongir, 2026-08-13:
    # "global qidiruvda nomer yozsa ham nomer bilan qidirsa ham
    # bo'ladigan qilgin").
    digits = "".join(ch for ch in q if ch.isdigit())

    def _dig(col):
        e = col
        for ch in ("+", "(", ")", "-", " ", "."):
            e = func.replace(e, ch, "")
        return e

    def _phone_match(col):
        if len(digits) < 4:
            return None
        return _dig(col).like(f"%{digits}%")

    # --- FILIAL DOIRASI: bitta joyda hisoblanadi, hamma ro'yxatga
    #     (o'quvchi, lid, guruh, ustoz) bir xil qo'llanadi.
    _org_wide = user.role in tuple(roles.ORG_WIDE_ROLES)
    _mine = _user_branch_ids(db, user)

    def _scope(col):
        """Qidiruv doirasi shartini qaytaradi (yoki None - cheklovsiz)."""
        if branch_id:
            if _org_wide or branch_id in (_mine or []):
                return col == branch_id
            # Ruxsat yo'q filial so'ralgan - o'zinikidan chiqarmaymiz
            return col.in_(_mine or [-1])
        if _org_wide:
            return None
        if _mine:
            return col.in_(_mine)
        if user.branch_id:
            return col == user.branch_id
        return None

    conds = [models.Student.full_name.ilike(like),
             models.Student.phone.ilike(like),
             models.Student.public_id.ilike(like)]
    for c in (_phone_match(models.Student.phone),
              _phone_match(models.Student.parent_phone)):
        if c is not None:
            conds.append(c)
    # ARXIVDAGILAR HAM CHIQADI (Jahongir, 2026-08-13: "tepadagi global
    # qidiruvda qidirganda arxivdagi o'quvchilar ham chiqsin") — ular
    # ro'yxatda "arxivda" deb belgilanadi.
    sq = db.query(models.Student).filter(or_(*conds))
    own_only = user.role in tuple(roles.OWN_GROUPS_ONLY)
    if own_only:
        t = _teacher_of_user(db, user)
        gids = [g.id for g in _cabinet_groups(db, user, t)] if t else []
        sq = sq.filter(models.Student.group_id.in_(gids or [-1]))
    else:
        _c = _scope(models.Student.branch_id)
        if _c is not None:
            sq = sq.filter(_c)
    groups = {g.id: g.name for g in db.query(models.Group).all()}
    st_lbl = {"active": "faol", "trial": "sinovda", "frozen": "muzlatilgan",
              "archived": "arxivda", "left": "ketgan"}
    # Faollar yuqorida, arxivdagilar pastda tursin
    _rows = sq.order_by(models.Student.full_name).limit(24).all()
    _rows.sort(key=lambda x: (x.status in ("archived", "left"),
                              x.full_name or ""))
    students = [{
        "id": s.id, "name": s.full_name,
        "group": groups.get(s.group_id),
        "phone": s.phone,
        "archived": s.status in ("archived", "left"),
        "status_label": st_lbl.get(s.status, s.status),
    } for s in _rows[:10]]

    leads = []
    if not own_only:
        _lconds = [models.Lead.full_name.ilike(like),
                   models.Lead.phone.ilike(like)]
        _lp = _phone_match(models.Lead.phone)
        if _lp is not None:
            _lconds.append(_lp)
        lq = db.query(models.Lead).filter(
            models.Lead.stage.notin_(("converted", "rejected")),
            or_(*_lconds))
        _c = _scope(models.Lead.branch_id)
        if _c is not None:
            lq = lq.filter(_c)
        leads = [{
            "id": l.id, "name": l.full_name, "group": None,
            "status_label": roles.LEAD_STAGE_LABELS.get(l.stage, l.stage),
        } for l in lq.order_by(models.Lead.full_name).limit(6).all()]

    # Guruh, ustoz, xodim ham qidiruvdan topiladi (ustozlarga emas)
    found_groups, found_teachers, found_staff = [], [], []
    if not own_only:
        gq = db.query(models.Group).filter(models.Group.name.ilike(like))
        _c = _scope(models.Group.branch_id)
        if _c is not None:
            gq = gq.filter(_c)
        found_groups = [{"id": g.id, "name": g.name}
                        for g in gq.order_by(models.Group.name)
                        .limit(5).all()]
        tq = db.query(models.Teacher).filter(
            models.Teacher.is_active == 1,
            models.Teacher.full_name.ilike(like))
        _c = _scope(models.Teacher.branch_id)
        if _c is not None:
            tq = tq.filter(_c)
        found_teachers = [{"id": t.id, "name": t.full_name}
                          for t in tq.order_by(models.Teacher.full_name)
                          .limit(5).all()]
        # XODIMLAR QIDIRUVDAN OLIB TASHLANDI (2026-08-18, Jahongir:
        # "qidiruvda xodimlar chiqmasin"). Tepadagi qidiruv kundalik
        # ish uchun — o'quvchi, lid, guruh, ustoz. Xodim qidirish
        # kamdan-kam kerak bo'ladi va uning o'z bo'limi bor; bu yerda
        # turgani natijalarni chalg'itardi (ism-familiyalar aralashib
        # ketardi).
    return {"students": students, "leads": leads, "groups": found_groups,
            "teachers": found_teachers, "staff": found_staff}

@router.get("/api/errors")
def list_errors(limit: int = 50, db: Session = Depends(get_db),
                user=Depends(require_role(roles.FOUNDER))):
    """Kutilmagan server xatolari jurnali. Foydalanuvchilar shikoyat
    qilishini kutmasdan ko'rib turish uchun."""
    rows = (db.query(models.ErrorLog)
            .order_by(models.ErrorLog.created_at.desc())
            .limit(max(1, min(limit, 200))).all())
    return {"errors": [{
        "id": e.id, "path": e.path, "method": e.method,
        "user": e.user_name,
        "detail": (e.detail or "")[-1200:],
        "at": e.created_at.isoformat() if e.created_at else None,
    } for e in rows]}

