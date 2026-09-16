"""Auto-extracted from main.py during refactor (split-main). Domain: auth_users."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bisect
from datetime import date, datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request
from fastapi import Response
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
from auth import client_ip as _client_ip
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

def _login_guard(db: Session, username: str, ip: str = ""):
    """Brute-force himoyasi: 15 daqiqada 5 marta xato parol —
    vaqtincha blok. Muvaffaqiyatli kirish hisoblagichni tozalaydi.

    2026-09-06 auditi: ilgari hisob FAQAT login bo'yicha yuritilardi.
    Shunda bitta kompyuterdan turli loginlarga standart parolni
    ("jonyjony") cheksiz sinab ko'rish mumkin edi. Endi BIR IP dan
    kelgan xato urinishlar ham sanaladi (chegara kattaroq — bir
    markazdan bir nechta xodim kiradi, ular xalaqit qilmasin)."""
    since = datetime.utcnow() - timedelta(minutes=roles.LOGIN_WINDOW_MIN)
    fails = db.query(models.LoginAttempt).filter(
        models.LoginAttempt.username == username,
        models.LoginAttempt.success == 0,
        models.LoginAttempt.created_at >= since).count()
    if fails >= roles.LOGIN_MAX_FAILS:
        raise HTTPException(
            429, f"Ko'p noto'g'ri urinish. {roles.LOGIN_WINDOW_MIN} "
                 "daqiqadan keyin qayta urinib ko'ring.")
    if ip:
        ip_fails = db.query(models.LoginAttempt).filter(
            models.LoginAttempt.ip == ip,
            models.LoginAttempt.success == 0,
            models.LoginAttempt.created_at >= since).count()
        if ip_fails >= roles.LOGIN_MAX_FAILS_IP:
            raise HTTPException(
                429, f"Ko'p noto'g'ri urinish. {roles.LOGIN_WINDOW_MIN} "
                     "daqiqadan keyin qayta urinib ko'ring.")

def _login_record(db: Session, username: str, ip: str, success: bool):
    try:
        db.add(models.LoginAttempt(username=username, ip=ip or None,
                                   success=1 if success else 0))
        if success:
            # Muvaffaqiyatdan keyin eski xatolar hisobga kirmasin
            db.query(models.LoginAttempt).filter(
                models.LoginAttempt.username == username,
                models.LoginAttempt.success == 0).delete()
        db.commit()
    except Exception:
        db.rollback()

@router.post("/api/auth/login", response_model=schemas.Token)
def login(payload: schemas.LoginRequest, request: Request,
          db: Session = Depends(get_db)):
    ip = _client_ip(request)
    _login_guard(db, payload.username, ip)
    user = db.query(models.User).filter(models.User.username == payload.username).first()
    # TELEFON-LOGIN MOSLASHUVI (2026-08-10, Jahongir: "apkdan raqam
    # bilan parol kirgizsam ishlamadi"). O'quvchi raqamini +998 bilan,
    # probel/chiziqcha bilan yoki 998siz yozishi mumkin; bazadagi login
    # esa kiritilgan kartadagi ko'rinishga qarab "901234567" yoki
    # "998901234567" bo'ladi. Aniq mos kelmasa, faqat raqamlar olinib
    # ikkala ko'rinish ham sinab ko'riladi. Parol tekshiruvi o'z
    # joyida qoladi - bu shunchaki yozuv shakli moslashuvi.
    if user is None:
        _digits = "".join(ch for ch in (payload.username or "")
                          if ch.isdigit())
        _cands = []
        if len(_digits) >= 7:
            _cands.append(_digits)
            if len(_digits) == 9:
                _cands.append("998" + _digits)
            if len(_digits) == 12 and _digits.startswith("998"):
                _cands.append(_digits[3:])
        for _c in _cands:
            if _c == payload.username:
                continue
            user = (db.query(models.User)
                    .filter(models.User.username == _c).first())
            if user is not None:
                break
    if not user or not verify_password(payload.password, user.password_hash):
        _login_record(db, payload.username, ip, False)
        raise HTTPException(status_code=401, detail="Login yoki parol noto'g'ri")
    if not user.is_active:
        raise HTTPException(status_code=401, detail="Bu hisob faolsizlantirilgan")
    # MUZLATILGAN / CHIQIB KETGAN O'QUVCHI ILOVAGA KIRMAYDI
    # (2026-08-25, Jahongir: "akkaunti muzlatilsa yoki darsdan chiqib
    # ketsa bu appga kirmay qolishi kerak"). Hisob O'CHIRILMAYDI —
    # holat qaytsa kirish o'zi tiklanadi.
    if user.role == roles.STUDENT:
        _st = (db.query(models.Student)
               .filter(models.Student.user_id == user.id).first())
        if _st:
            _why = roles.student_app_block_reason(_st.status)
            if _why:
                _login_record(db, payload.username, ip, True)
                raise HTTPException(status_code=403, detail=_why)
    _login_record(db, payload.username, ip, True)
    token = create_access_token(
        {"sub": user.username},
        minutes=60 * 24 * 60 if payload.remember else None)
    # Oy boshida birinchi kirishda oylik to'lovlar avtomat yechiladi
    try:
        _founder_name_fix(db)
        # Kirish sekinlashmasin: bu yerda faqat 5 soniyalik ulush
        # bajariladi, qolgani keyingi kirishlarda va kunlik cron'da
        # davom etadi (2026-08-14).
        _ensure_month_charges(db, budget_s=5.0)
    except Exception:
        pass
    # STANDART PAROL — MAJBURIY ALMASHTIRISH (2026-09-06).
    # Login = telefon raqami (ochiq ma'lumot), parol esa hisob
    # ochilganda "jonyjony" bo'ladi. Xodim uni almashtirmaguncha
    # hisobiga har kim kirishi mumkin. Endi ilova birinchi ekranda
    # parol so'raydi. O'quvchi/ota-ona bundan mustasno: ularning
    # hisobi avtomat ochiladi va ichida pul/boshqaruv yo'q.
    _must = (user.role not in (roles.STUDENT, roles.PARENT)
             and verify_password(roles.DEFAULT_PASSWORD, user.password_hash))
    return schemas.Token(
        access_token=token, role=user.role, full_name=user.full_name,
        branch_id=user.branch_id, must_change_password=bool(_must),
    )

@router.put("/api/auth/recovery-code")
def set_recovery_code(payload: schemas.RecoverySetIn,
                      db: Session = Depends(get_db),
                      user: models.User = Depends(require_role(roles.FOUNDER))):
    """Asoschi favqulodda tiklash kodini o'rnatadi. Parol unutilsa,
    shu kod bilan tiklanadi — tizim egasiz qolib ketmaydi."""
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(400, "Joriy parol noto'g'ri")
    code = (payload.recovery_code or "").strip()
    if len(code) < 10:
        raise HTTPException(400, "Tiklash kodi kamida 10 belgi bo'lsin")
    user.recovery_hash = hash_password(code)
    db.commit()
    audit.log(db, user, entity="user", action="recovery_set",
              entity_id=user.id, entity_label=user.full_name)
    db.commit()
    return {"ok": True}

@router.post("/api/auth/recover")
def recover_password(payload: schemas.RecoverIn, request: Request,
                     db: Session = Depends(get_db)):
    """Parolni tiklash kodi bilan almashtirish (faqat asoschi hisobi).
    Login himoyasi bilan bir xil blok qoidasi amal qiladi."""
    ip = _client_ip(request)
    _login_guard(db, payload.username, ip)
    user = db.query(models.User).filter(
        models.User.username == payload.username,
        models.User.role == roles.FOUNDER).first()
    if not user or not user.recovery_hash or \
            not verify_password(payload.recovery_code, user.recovery_hash):
        _login_record(db, payload.username, ip, False)
        raise HTTPException(401, "Login yoki tiklash kodi noto'g'ri")
    if not roles.password_ok(payload.new_password):
        raise HTTPException(400, roles.PASSWORD_RULE_TEXT)
    user.password_hash = hash_password(payload.new_password)
    db.commit()
    _login_record(db, payload.username, ip, True)
    audit.log(db, None, entity="user", action="recover",
              entity_id=user.id, entity_label=user.full_name,
              note="parol tiklash kodi bilan almashtirildi")
    db.commit()
    return {"ok": True}

@router.get("/api/auth/me", response_model=schemas.UserOut)
def me(user: models.User = Depends(get_current_user)):
    return user

@router.put("/api/auth/me/password")
def change_own_password(
    payload: schemas.ChangePasswordRequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Joriy parol noto'g'ri")
    if not roles.password_ok(payload.new_password):
        raise HTTPException(status_code=400, detail=roles.PASSWORD_RULE_TEXT)
    user.password_hash = hash_password(payload.new_password)
    db.commit()
    # "recover" (tiklash kodi bilan) va "password_reset" (admin
    # o'rniga majburan) dan farqli - bu yerda foydalanuvchi TIZIMGA
    # KIRGAN holda O'ZI, joriy parolini bilgan holda almashtiryapti.
    # Uchalasi ham xavfsizlik nuqtai nazaridan ahamiyatli va Audit'da
    # bir-biridan ajralib turishi kerak.
    audit.log(db, user, entity="user", action="password_change",
              entity_id=user.id, entity_label=user.full_name,
              note="foydalanuvchi o'z parolini almashtirdi", commit=True)
    return {"ok": True}


def _clean_username(db: Session, name: str, exclude_id: int) -> str:
    """Yangi loginni tekshiradi: qoida va bandlik (katta-kichik harf
    farqsiz — "Ali" va "ali" ikki xil odam bo'lib chalkashmasin)."""
    name = (name or "").strip()
    if not roles.username_ok(name):
        raise HTTPException(400, roles.USERNAME_RULE_TEXT)
    # "demo." bilan boshlanadigan loginlar demo ma'lumot hisoblanadi va
    # demo tozalanganda O'CHIRIB yuboriladi (demo_seed.py). Haqiqiy
    # xodimga bunday login berilsa, akkaunti yo'qolib qolardi.
    if name.lower().startswith("demo."):
        raise HTTPException(400, "\"demo.\" bilan boshlanadigan login "
                                 "faqat demo ma'lumot uchun")
    taken = (db.query(models.User.id)
             .filter(func.lower(models.User.username) == name.lower(),
                     models.User.id != exclude_id).first())
    if taken:
        raise HTTPException(400, "Bu login band, boshqasini tanlang")
    return name


def _renewed_token(request: Request, username: str) -> str:
    """Login o'zgarganda yangi token: token ichida login (sub) turadi.
    Eski tokenning qolgan muddati saqlanadi ("eslab qolish" ham)."""
    minutes = None
    try:
        from jose import jwt as _jwt
        tok = (request.headers.get("authorization") or "").split(" ", 1)[-1]
        exp = _jwt.get_unverified_claims(tok).get("exp")
        if exp:
            left = int((datetime.utcfromtimestamp(exp)
                        - datetime.utcnow()).total_seconds() // 60)
            minutes = max(left, 60)
    except Exception:
        minutes = None
    return create_access_token({"sub": username}, minutes=minutes)


@router.put("/api/auth/me/username")
def change_own_username(
    payload: schemas.ChangeUsernameRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Xodim o'z loginini almashtiradi (2026-09-16, Jahongir: "loginni
    ham har bir xodim va HR edit qila olsin").

    Token ichida login (sub) turadi — shuning uchun almashtirilgach
    yangi token qaytariladi, aks holda odam darhol tizimdan chiqib
    ketardi. Eski token muddati saqlanadi ("eslab qolish" ham)."""
    if user.role in tuple(roles.EXTERNAL_ROLES):
        raise HTTPException(403, "Loginni faqat xodimlar o'zgartiradi")
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(400, "Joriy parol noto'g'ri")
    new = _clean_username(db, payload.new_username, user.id)
    old = user.username
    if new == old:
        raise HTTPException(400, "Yangi login eskisi bilan bir xil")
    token = _renewed_token(request, new)
    user.username = new
    db.commit()
    audit.log(db, user, entity="user", action="update",
              entity_id=user.id, entity_label=user.full_name,
              field="username", old_value=old, new_value=new,
              note="xodim o'z loginini almashtirdi", commit=True)
    return {"ok": True, "username": new, "access_token": token}

def _guard_role_assignment(
    requester: models.User, target_role: str, target_branch_id: Optional[int]
):
    """Rol berish - tizimdagi eng xavfli amal, shuning uchun uni faqat
    asoschi bajaradi (roles.USER_ADMIN). Bu yerda yana bir bor tekshiramiz:
    endpoint himoyasi kelajakda kengaytirilib ketsa ham, huquqni oshirib
    yuborishning oldi olinadi."""
    if target_role not in roles.ALL_ROLES:
        raise HTTPException(400, "Noto'g'ri rol")
    if not roles.can_assign_role(requester.role, target_role):
        raise HTTPException(
            403, "Bu rolni berish huquqi sizda yo'q. Asoschi va filial "
                 "rahbari rollarini faqat asoschi tayinlaydi.")

def _sync_user_roles(db: Session, u: models.User, extra_roles: list):
    """Xodimning QO'SHIMCHA lavozimlari (2026-08-10).

    Asosiy lavozim User.role da qoladi; bu yerda faqat qo'shimchalari.
    Asosiy lavozim tasodifan qo'shimchaga ham yozilib qolmasin —
    o'tkazib yuboriladi."""
    db.query(models.UserRole).filter(
        models.UserRole.user_id == u.id).delete()
    seen = set()
    for r in extra_roles or []:
        r = (r or "").strip()
        if not r or r in seen or r == u.role:
            continue
        if r not in roles.ALL_ROLES:
            continue
        seen.add(r)
        db.add(models.UserRole(user_id=u.id, role=r))


def _sync_user_branches(db: Session, u: models.User, branch_ids: list):
    """Xodimning filiallar ro'yxati: birinchisi asosiy (User.branch_id),
    qolganlari user_branches jadvalida."""
    db.query(models.UserBranch).filter(
        models.UserBranch.user_id == u.id).delete()
    seen = set()
    for bid in branch_ids or []:
        if not bid or bid in seen:
            continue
        seen.add(bid)
        if bid == u.branch_id:
            continue
        db.add(models.UserBranch(user_id=u.id, branch_id=bid))

@router.get("/api/users", response_model=List[schemas.UserOut])
def list_users(
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(
        *(list(roles.STAFF_VIEWERS) + [roles.HEAD_SUPPORT]))),
):
    backfill_missing_ids(db, "user", models.User)
    # 2026-08-12 (Jahongir): filial tanlanganda XODIMLAR ham faqat shu
    # filialniki chiqadi - tepadagi filial tanlagichi hurmat qilinadi
    q = scope_to_branch(db.query(models.User), models.User, user,
                        branch_id)
    # XODIMLAR ro'yxati - o'quvchi va ota-ona akkauntlari bunga
    # kirmaydi (Jahongir: "Xodimlar bo'limida, o'quvchilar ham
    # ko'rinyabdi. nega yoqot ularni"). O'quvchi akkauntlari avtomat
    # ochilgani uchun ro'yxat minglab bo'lib ketgan edi.
    q = q.filter(models.User.role.notin_((roles.STUDENT, roles.PARENT)))
    # Support boshlig'i faqat o'z jamoasini (support teacherlar) va
    # o'zini ko'radi - butun xodimlar ro'yxati unga tegishli emas.
    if user.role == roles.HEAD_SUPPORT:
        q = q.filter((models.User.role == roles.SUPPORT_TEACHER)
                     | (models.User.id == user.id))
    rows = q.order_by(models.User.full_name).all()
    # Ko'p filialli xodimlar: barcha filiallari yorlig'i
    extra_map: dict = {}
    for ub in db.query(models.UserBranch).all():
        extra_map.setdefault(ub.user_id, []).append(ub.branch_id)
    bnames = {b.id: b.name for b in db.query(models.Branch).all()}
    # Ko'p lavozimli xodimlar (2026-08-10)
    role_map: dict = {}
    for ur in db.query(models.UserRole).all():
        role_map.setdefault(ur.user_id, []).append(ur.role)
    out = []
    for u in rows:
        item = schemas.UserOut.model_validate(u)
        ids = ([u.branch_id] if u.branch_id else []) + \
            [b for b in extra_map.get(u.id, []) if b != u.branch_id]
        item.branch_ids = ids
        item.branches_label = ", ".join(
            bnames.get(b, "?") for b in ids) or None
        item.extra_roles = [r for r in role_map.get(u.id, [])
                            if r != u.role]
        out.append(item)
    return out

@router.get("/api/users/assignable", response_model=List[schemas.StaffOption])
def list_assignable_staff(
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(*roles.LEAD_ACCESS)),
):
    """Lidga mas'ul qilib biriktirish mumkin bo'lgan xodimlar. /api/users
    faqat HR/adminlar uchun ochiq, shuning uchun SMM manager ham
    ishlata oladigan qisqartirilgan ro'yxat kerak."""
    q = scope_to_branch(db.query(models.User), models.User, user)
    return q.filter(models.User.is_active == 1).order_by(models.User.full_name).all()

def _smm_new_staff_task(db: Session, emp: models.User) -> None:
    """Yangi xodim — suratga va videoga olish kerak."""
    _make_smm_task(
        db, kind="new_staff",
        title=f"Yangi xodim: {emp.full_name} — surat va video",
        description=(
            f"Lavozimi: {roles.UZ_LABELS.get(emp.role, emp.role)}\n"
            f"Filial: {emp.branch.name if emp.branch else '—'}\n"
            f"Ishga kirgan sana: {(emp.hired_date or date.today()).isoformat()}\n\n"
            "Kerak: profil surati (sayt va Telegram uchun) hamda "
            "qisqa tanishtiruv videosi."),
        branch_id=emp.branch_id)

@router.post("/api/users", response_model=schemas.UserOut)
def create_user(
    payload: schemas.UserCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(*roles.STAFF_EDIT)),
):
    if payload.role not in roles.ALL_ROLES:
        raise HTTPException(400, "Noto'g'ri rol")
    _guard_role_assignment(user, payload.role, payload.branch_id)
    # Filial rahbari faqat o'z filialiga xodim ochadi
    if user.role == roles.BRANCH_MANAGER \
            and not _in_user_branches(db, user, payload.branch_id):
        raise HTTPException(403, "Faqat o'z filialingizga xodim "
                                 "qo'sha olasiz")
    if db.query(models.User).filter(models.User.username == payload.username).first():
        raise HTTPException(400, "Bu login band, boshqasini tanlang")
    if not roles.password_ok(payload.password):
        raise HTTPException(400, roles.PASSWORD_RULE_TEXT)

    # Ko'p filial: birinchisi asosiy bo'ladi
    _bids = payload.branch_ids or []
    _primary = payload.branch_id or (_bids[0] if _bids else None)
    new_user = models.User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        role=payload.role,
        branch_id=_primary,
        fix_salary=payload.fix_salary,
        # Xodim kartasi. Tug'ilgan sana va ishga kirgan sana — tabrik
        # eslatmalarining asosi, shuning uchun boshidanoq yoziladi.
        phone=payload.phone,
        birth_date=payload.birth_date,
        position=payload.position,
        manager_id=payload.manager_id,
        hired_date=payload.hired_date or date.today(),
        photo=payload.photo,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    if _bids:
        _sync_user_branches(db, new_user, _bids)
    if payload.extra_roles:
        _sync_user_roles(db, new_user, payload.extra_roles)
        db.commit()
    # AVTOMAT: SMM'ga yangi xodimni suratga olish vazifasi
    _smm_new_staff_task(db, new_user)
    # O'qituvchi/support bo'lsa — Ustozlar bo'limida ham darhol ko'rinsin
    _ensure_teacher_card(db, new_user)
    db.commit()
    audit.log(db, user, entity="user", action="create",
              entity_id=new_user.id, entity_label=new_user.full_name,
              note=f"Rol: {roles.UZ_LABELS.get(new_user.role, new_user.role)}",
              commit=True)
    return new_user

@router.put("/api/users/{user_id}", response_model=schemas.UserOut)
def update_user(
    user_id: int,
    payload: schemas.UserUpdate,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(
        *(list(roles.STAFF_EDIT) + [roles.HEAD_SUPPORT]))),
):
    target = db.query(models.User).get(user_id)
    if not target:
        raise HTTPException(404, "Foydalanuvchi topilmadi")

    # Support boshlig'i FAQAT support teacher hisobini to'liq
    # boshqaradi (parol, telefon, faollik...). Boshqa rolga o'tkaza
    # olmaydi va boshqa xodimlarga tegolmaydi (Jahongir: "polniy edit
    # qila olsin har qanday narsasini").
    if user.role == roles.HEAD_SUPPORT:
        if target.role != roles.SUPPORT_TEACHER:
            raise HTTPException(
                403, "Support boshlig'i faqat support teacher "
                     "hisobini tahrirlaydi")
        if payload.role is not None \
                and payload.role != roles.SUPPORT_TEACHER:
            raise HTTPException(
                403, "Support boshlig'i rol o'zgartira olmaydi - "
                     "boshqa lavozimga o'tkazishni o'quv bo'limi "
                     "yoki HR qiladi")

    # Asoschining kartasini faqat asoschining o'zi tahrirlaydi. Aks
    # holda HR asoschining parolini almashtirib yoki uni o'chirib,
    # butun tizimni egallab olishi mumkin bo'lardi.
    # HR hammaning hisobini boshqaradi, LEKIN filial rahbariniki emas:
    # parolini almashtirib filialni egallab olishning oldi olinadi.
    # DIQQAT (2026-09-05): tahrirlash oynasi is_active ni HAR DOIM
    # yuboradi (o'zgarmagan bo'lsa ham). Shuning uchun faqat HAQIQIY
    # o'zgarish tekshiriladi — aks holda HR filial rahbarining
    # telefonini yoki filialini ham tuzata olmasdi.
    _active_change = (payload.is_active is not None
                      and bool(payload.is_active) != bool(target.is_active))
    # Login ham parol kabi kirish kaliti (2026-09-16) — xuddi shu
    # himoyalar ostida turadi.
    _new_username = None
    if payload.username is not None \
            and payload.username.strip() != target.username:
        # O'quvchi/ota-ona logini (telefon raqami) bu yerdan o'zgarmaydi:
        # "kim ilovaga kirgan" statistikasi login bo'yicha yuritiladi.
        if target.role in tuple(roles.EXTERNAL_ROLES):
            raise HTTPException(
                403, "O'quvchi va ota-ona loginini bu yerdan "
                     "o'zgartirib bo'lmaydi")
        _new_username = _clean_username(db, payload.username, target.id)
    if user.role == roles.HR_MANAGER \
            and target.role in (roles.FOUNDER, roles.BRANCH_MANAGER) \
            and (payload.password or _active_change or _new_username):
        raise HTTPException(
            403, "Asoschi va filial rahbari hisobini (login, parol, "
                 "faollik) faqat asoschi boshqaradi")
    if target.role == roles.FOUNDER and user.role != roles.FOUNDER:
        raise HTTPException(403, "Asoschi kartasini faqat asoschi "
                                 "tahrirlaydi")

    new_role = payload.role if payload.role is not None else target.role
    # Ko'p filial berilsa — birinchisi asosiy
    if payload.branch_ids:
        payload.branch_id = payload.branch_ids[0]
    new_branch_id = (
        payload.branch_id if payload.branch_id is not None else target.branch_id
    )
    # Rol yoki filial O'ZGARAYOTGAN bo'lsagina huquq tekshiriladi. Aks
    # holda telefon raqamini tuzatish ham "rol berish" hisoblanib,
    # HR bloklanib qolardi.
    if new_role != target.role:
        _guard_role_assignment(user, new_role, new_branch_id)
    elif new_branch_id != target.branch_id \
            and user.role != roles.HR_MANAGER:
        # Rol o'zgarmayapti, faqat filial. HR uchun bu ERKIN
        # (2026-09-05, Jahongir: "HR bo'limi rahbari xodimlarga filial
        # biriktira olsin") — filial rahbarini ham boshqa filialga
        # o'tkaza oladi, bu unga hech qanday huquq qo'shmaydi.
        # Filial rahbari uchun esa eski tekshiruv qoladi: u faqat
        # o'z filialida, faqat ruxsat etilgan rollarni boshqaradi.
        _guard_role_assignment(user, new_role, new_branch_id)

    # Maosh alohida huquq: filial rahbari xodim kartasini tahrirlaydi,
    # lekin oylik raqamiga tegmaydi.
    if payload.fix_salary is not None \
            and payload.fix_salary != target.fix_salary \
            and user.role not in roles.SALARY_EDIT:
        raise HTTPException(403, "Fiks oylikni o'zgartirish huquqi "
                                 "sizda yo'q")
    if user.role == roles.BRANCH_MANAGER \
            and not _in_user_branches(db, user, target.branch_id):
        raise HTTPException(403, "Faqat o'z filialingiz xodimlarini tahrirlay olasiz")
    if target.id == user.id and payload.is_active is False:
        raise HTTPException(400, "O'zingizni faolsizlantira olmaysiz")

    # O'zgarishlarni qo'llashdan OLDIN yozib olamiz.
    audit.log_changes(
        db, user, entity="user", obj=target,
        changes={k: v for k, v in payload.model_dump(exclude_unset=True).items()
                 if k not in ("password", "username")})
    if _new_username:
        audit.log(db, user, entity="user", action="update",
                  entity_id=target.id, entity_label=target.full_name,
                  field="username", old_value=target.username,
                  new_value=_new_username, note="Login o'zgartirildi",
                  branch_id=target.branch_id)
    if payload.password:
        audit.log(db, user, entity="user", action="update", entity_id=target.id,
                  entity_label=target.full_name, field="password",
                  note="Parol o'zgartirildi", branch_id=target.branch_id)

    # SUPPORT BO'SHATILSA GURUHLARI AVTOMAT BO'SHASIN (2026-08-10).
    # DIQQAT: bu tekshiruv rol va faollik O'ZGARTIRILISHIDAN OLDIN
    # turishi SHART. Pastda target.role allaqachon yangi qiymatga
    # o'tib bo'ladi va "avval support edimi?" degan savolga javob
    # topib bo'lmay qoladi.
    _was_support = target.role == roles.SUPPORT_TEACHER
    _leaving = (payload.is_active is not None
                and target.is_active and not int(payload.is_active))
    _role_changed = (payload.role is not None
                     and payload.role != roles.SUPPORT_TEACHER)
    if _was_support and (_leaving or _role_changed):
        _release_support_groups(
            db, target,
            "ishdan bo'shatildi" if _leaving else "lavozimi o'zgartirildi")

    if payload.full_name is not None:
        target.full_name = payload.full_name
    if _new_username:
        # Token ichida login turadi — xodim keyingi so'rovda qayta
        # kirishi kerak bo'ladi (yangi login bilan). Bu kutilgan holat.
        target.username = _new_username
        # O'z loginini kartadan o'zgartirsa ham tizimdan chiqib
        # ketmasin (2026-09-16): brauzer yangi tokenni shu
        # sarlavhadan olib saqlaydi (src/lib/api.ts).
        if target.id == user.id:
            response.headers["X-New-Token"] = _renewed_token(
                request, _new_username)
    # ESKI LAVOZIM YO'QOLMAYDI (2026-08-29, Jahongir: "menejerdan
    # ustozga o'tgandan keyin almashtira olmay qolibdi").
    #
    # SABAB: tahrirlash oynasi qo'shimcha lavozimlar ro'yxatidan
    # ASOSIY lavozimni chiqarib yuboradi (u ikki marta turmasin
    # uchun). Asosiy lavozim "filial rahbari"dan "ustoz"ga
    # o'zgartirilganda esa ro'yxatda faqat "ustoz" qolgan edi ->
    # filtrdan keyin ro'yxat BO'SH bo'lib ketdi -> odam ustoz
    # kabinetida qamalib qoldi, qaytishga tanlagich yo'q.
    #
    # Endi eski asosiy lavozim AVTOMAT qo'shimchaga o'tadi. Odam
    # lavozimini almashtirganda avvalgisini yo'qotmaydi — ikkalasida
    # ham ishlayveradi (aynan Nodirbek va Go'zalning holati).
    _old_role = target.role
    if payload.role is not None:
        target.role = payload.role
    if payload.branch_id is not None:
        target.branch_id = payload.branch_id
    if payload.is_active is not None:
        was = target.is_active
        target.is_active = int(payload.is_active)
        # USTOZ KARTASI BILAN SINXRON (2026-09-06 auditi). Ilgari
        # xodim hisobi bo'shatilsa ustoz kartasi faol qolaverardi
        # (yoki teskarisi) — Dostonbek holati aynan shundan chiqqan:
        # karta yopiq, akkaunt faol, guruhda osilib qolgan.
        if was != target.is_active:
            try:
                _tc = (db.query(models.Teacher)
                       .filter(models.Teacher.user_id == target.id).first())
                if _tc is not None and int(_tc.is_active or 0) != int(target.is_active):
                    _tc.is_active = int(target.is_active)
                    if not target.is_active:
                        _tc.left_date = _tc.left_date or date.today()
                    else:
                        _tc.left_date = None
            except Exception:
                pass
        # Ishdan bo'shatilganda sana avtomat qo'yiladi va toifasi
        # belgilanmagan bo'lsa "neytral" bo'lib turadi - keyin HR
        # arxivdan o'zgartiradi.
        if was and not target.is_active:
            target.exit_date = target.exit_date or date.today()
            target.exit_type = target.exit_type or "neutral"
        elif not was and target.is_active:
            target.exit_date = None
            target.exit_type = None
            target.exit_reason = None
    if payload.password:
        if not roles.password_ok(payload.password):
            raise HTTPException(400, roles.PASSWORD_RULE_TEXT)
        target.password_hash = hash_password(payload.password)
    # Fiks oylik - KPI hisobining asosi, shuning uchun uni faqat asoschi
    # (roles.USER_ADMIN) o'zgartira oladi; endpoint allaqachon shu bilan
    # himoyalangan. exclude_unset orqali "berilmagan" va "0 qilindi"
    # holatlarini ajratamiz.
    _new_bids = payload.branch_ids
    given = payload.model_dump(exclude_unset=True)
    given.pop("branch_ids", None)
    if "fix_salary" in given:
        target.fix_salary = payload.fix_salary

    # Xodim kartasi maydonlari. exclude_unset — "berilmagan" va
    # "bo'shatildi" holatlarini ajratadi, aks holda tahrirlash oynasida
    # tegilmagan maydon ham tozalanib ketardi.
    for f in ("phone", "birth_date", "position", "manager_id",
              "hired_date", "photo", "exit_type", "exit_reason"):
        if f in given:
            setattr(target, f, given[f])

    # Ko'p filial ro'yxati yuborilgan bo'lsa — sinxronlaymiz
    if _new_bids is not None:
        _sync_user_branches(db, target, _new_bids or [])
    # Qo'shimcha lavozimlar yuborilgan bo'lsa — sinxronlaymiz.
    # Eski asosiy lavozim HAR DOIM ro'yxatga qo'shiladi (yuqoridagi
    # izohga qarang) — brauzer uni yuborishni unutgan bo'lsa ham.
    _extra = list(given.get("extra_roles") or []) \
        if "extra_roles" in given else None
    if _old_role and _old_role != target.role \
            and _old_role in roles.ALL_ROLES:
        if _extra is None:
            _extra = [r.role for r in db.query(models.UserRole)
                      .filter(models.UserRole.user_id == target.id).all()]
        if _old_role not in _extra:
            _extra.append(_old_role)
    if _extra is not None:
        _sync_user_roles(db, target, _extra)

    # Ustoz/support kartasi bilan ikki tomonlama sinxron: ism va
    # faollik ikkala bo'limda bir xil tursin. Rol keyin o'qituvchiga
    # o'zgartirilsa ham karta ochiladi.
    _tcard = _ensure_teacher_card(db, target)
    if _tcard:
        if payload.full_name is not None:
            _tcard.full_name = target.full_name
        if payload.is_active is not None:
            _tcard.is_active = int(target.is_active)
            _sync_teacher_left_date(_tcard)

    db.commit()
    db.refresh(target)
    return target

@router.get("/api/permissions")
def get_permissions(
    db: Session = Depends(get_db),
    user=Depends(require_role(roles.FOUNDER)),
):
    """To'liq matritsa: rol x bo'lim x amal."""
    matrix = {}
    for role in roles.ALL_ROLES:
        matrix[role] = {
            res: sorted(perms_for(db, role, res))
            for res in roles.RESOURCE_KEYS
        }
    changed = {}
    for r in db.query(models.RolePermission).all():
        changed.setdefault(r.role, {}).setdefault(r.resource, []).append(r.action)

    return {
        "roles": [{
            "key": r,
            "label": roles.UZ_LABELS.get(r, r),
            "locked": r == roles.LOCKED_ROLE,
            "external": r in roles.EXTERNAL_ROLES,
        } for r in roles.ALL_ROLES],
        "role_groups": [{"key": k, "label": lbl, "roles": rs}
                        for k, lbl, rs in roles.ROLE_GROUPS],
        "resources": [{"key": k, "label": lbl, "group": g,
                       "secret_hint": roles.SECRET_HINTS.get(k)}
                      for k, lbl, g in roles.RESOURCES],
        "actions": [{"key": k, "label": lbl}
                    for k, lbl in roles.PERM_ACTIONS],
        "matrix": matrix,
        "changed": changed,
    }

@router.put("/api/permissions")
def set_permissions(
    payload: schemas.PermissionUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_role(roles.FOUNDER)),
):
    """Bitta katakni o'zgartirish. Asoschining huquqiga tegib
    bo'lmaydi."""
    if payload.role == roles.LOCKED_ROLE:
        raise HTTPException(
            400, "Asoschining huquqini o'zgartirib bo'lmaydi — "
                 "aks holda tizimga kirish yo'li yopilib qoladi")
    if payload.role not in roles.ALL_ROLES:
        raise HTTPException(400, "Noto'g'ri rol")
    if payload.resource not in roles.RESOURCE_KEYS:
        raise HTTPException(400, "Noto'g'ri bo'lim")
    if payload.action not in roles.PERM_ACTION_KEYS:
        raise HTTPException(400, "Noto'g'ri amal")

    # "view" olib tashlansa qolgan amallar ham ma'nosiz qoladi
    row = (db.query(models.RolePermission)
           .filter(models.RolePermission.role == payload.role,
                   models.RolePermission.resource == payload.resource,
                   models.RolePermission.action == payload.action).first())
    if not row:
        row = models.RolePermission(
            role=payload.role, resource=payload.resource,
            action=payload.action)
        db.add(row)
    row.allowed = 1 if payload.allowed else 0
    row.changed_by = user.full_name

    if payload.action == "view" and not payload.allowed:
        # Ko'rish yopilsa — boshqa amallar ham yopiladi
        for a in roles.PERM_ACTION_KEYS:
            if a == "view":
                continue
            other = (db.query(models.RolePermission)
                     .filter(models.RolePermission.role == payload.role,
                             models.RolePermission.resource == payload.resource,
                             models.RolePermission.action == a).first())
            if not other:
                other = models.RolePermission(
                    role=payload.role, resource=payload.resource, action=a)
                db.add(other)
            other.allowed = 0
            other.changed_by = user.full_name
    elif payload.allowed and payload.action != "view":
        # Boshqa amal berilsa — ko'rish avtomat ochiladi
        v = (db.query(models.RolePermission)
             .filter(models.RolePermission.role == payload.role,
                     models.RolePermission.resource == payload.resource,
                     models.RolePermission.action == "view").first())
        if v:
            v.allowed = 1
        elif "view" not in roles.default_perms(payload.role, payload.resource):
            db.add(models.RolePermission(
                role=payload.role, resource=payload.resource,
                action="view", allowed=1, changed_by=user.full_name))

    db.commit()
    _PERM_CACHE["data"] = None
    audit.log(db, user, entity="user", action="role_change", entity_id=0,
              entity_label=roles.UZ_LABELS.get(payload.role, payload.role),
              field=f"{roles.RESOURCE_LABELS[payload.resource]} — "
                    f"{roles.PERM_ACTION_LABELS[payload.action]}",
              new_value="ruxsat berildi" if payload.allowed else "olib tashlandi")
    db.commit()
    return {"perms": sorted(perms_for(db, payload.role, payload.resource))}

@router.post("/api/permissions/reset")
def reset_permissions(
    payload: schemas.PermissionReset,
    db: Session = Depends(get_db),
    user=Depends(require_role(roles.FOUNDER)),
):
    """Standart holatga qaytarish."""
    q = db.query(models.RolePermission)
    if payload.role:
        q = q.filter(models.RolePermission.role == payload.role)
    n = q.delete()
    db.commit()
    _PERM_CACHE["data"] = None
    audit.log(db, user, entity="user", action="role_change", entity_id=0,
              entity_label=roles.UZ_LABELS.get(payload.role or "", "Barcha rollar"),
              field="Ruxsatlar", new_value="standart holatga qaytarildi",
              commit=True)
    return {"reset": n}

