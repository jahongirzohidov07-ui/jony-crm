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
def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat()}

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
                            fix_groupless_active as _fga)
        _bsb(db)
        _fga(db)
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
def global_student_search(q: str, db: Session = Depends(get_db),
                          user=Depends(get_current_user)):
    """Tepadagi qidiruv: 3 harfdan boshlab o'quvchilar va potensial
    o'quvchilar (lidlar). Ustoz faqat o'z guruhlaridagilarini ko'radi,
    lidlar unga chiqmaydi. Balans qaytarilmaydi."""
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
    elif user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
        sq = sq.filter(_branch_in(db, user, models.Student.branch_id))
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
        if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
            lq = lq.filter(_branch_in(db, user, models.Lead.branch_id))
        leads = [{
            "id": l.id, "name": l.full_name, "group": None,
            "status_label": roles.LEAD_STAGE_LABELS.get(l.stage, l.stage),
        } for l in lq.order_by(models.Lead.full_name).limit(6).all()]

    # Guruh, ustoz, xodim ham qidiruvdan topiladi (ustozlarga emas)
    found_groups, found_teachers, found_staff = [], [], []
    if not own_only:
        gq = db.query(models.Group).filter(models.Group.name.ilike(like))
        if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
            gq = gq.filter(_branch_in(db, user, models.Group.branch_id))
        found_groups = [{"id": g.id, "name": g.name}
                        for g in gq.order_by(models.Group.name)
                        .limit(5).all()]
        tq = db.query(models.Teacher).filter(
            models.Teacher.is_active == 1,
            models.Teacher.full_name.ilike(like))
        if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
            tq = tq.filter(_branch_in(db, user, models.Teacher.branch_id))
        found_teachers = [{"id": t.id, "name": t.full_name}
                          for t in tq.order_by(models.Teacher.full_name)
                          .limit(5).all()]
        if user.role in tuple(roles.STAFF_VIEWERS):
            uq = db.query(models.User).filter(
                models.User.is_active == 1,
                models.User.full_name.ilike(like))
            found_staff = [{
                "id": u.id, "name": u.full_name,
                "status_label": roles.UZ_LABELS.get(u.role, u.role),
            } for u in uq.order_by(models.User.full_name).limit(5).all()]
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

