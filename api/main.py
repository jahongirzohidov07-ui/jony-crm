import os, sys

# Vercel's Python serverless runtime loads this file directly by path (not as
# part of the `api` package), so sibling imports below (billing, models, ...)
# fail unless this file's own directory is explicitly on sys.path first. A
# no-op when run locally via `python -m uvicorn main:app` from this directory.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bisect
from datetime import date, datetime, timedelta
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func
from sqlalchemy.orm import Session

import audit
import billing
import models
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
from database import Base, engine, get_db

Base.metadata.create_all(bind=engine)


# ---- Ommaviy ID (STU-000123) ----------------------------------------
# Har bir shaxs va hujjatga bitta o'zgarmas raqam. Telefon yoki ism
# o'zgarsa ham bu qoladi: tarix, shartnoma va to'lov shunga bog'lanadi.
PUBLIC_ID_PREFIX = {
    "student": "STU",
    "parent": "PAR",
    "user": "EMP",
    "lead": "LID",
    "group": "GRP",
    "payment": "PAY",
    "contract": "SHT",
}


def _make_public_id(kind: str, row_id: int) -> str:
    return f"{PUBLIC_ID_PREFIX[kind]}-{row_id:06d}"


def _ensure_public_id(db, kind: str, obj) -> str:
    """Obyektga ommaviy ID beradi (agar hali bo'lmasa). ID ichki
    raqamdan hosil qilinadi - shuning uchun hech qachon takrorlanmaydi."""
    if not getattr(obj, "public_id", None):
        obj.public_id = _make_public_id(kind, obj.id)
    return obj.public_id


def _backfill_public_ids():
    """Ilova ishga tushganda ID'siz qolgan eski yozuvlarni to'ldiradi."""
    from database import SessionLocal
    pairs = [
        ("student", models.Student), ("parent", models.Parent),
        ("user", models.User), ("lead", models.Lead),
        ("group", models.Group), ("payment", models.Payment),
        ("contract", models.Contract),
    ]
    db = SessionLocal()
    try:
        for kind, model in pairs:
            try:
                rows = db.query(model).filter(model.public_id.is_(None)).all()
            except Exception:
                continue
            for r in rows:
                r.public_id = _make_public_id(kind, r.id)
            if rows:
                db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


def _ensure_new_columns():
    """create_all() faqat yo'q jadvalni yaratadi - mavjud jadvalga yangi
    ustun qo'shmaydi. Shuning uchun keyin qo'shilgan ustunlarni shu yerda
    qo'lda qo'shamiz. Har safar ishga tushganda bajariladi, lekin ustun
    allaqachon bo'lsa xatolik e'tiborsiz qoldiriladi - ya'ni takror
    ishlatish xavfsiz."""
    from sqlalchemy import text

    statements = [
        "ALTER TABLE exams ADD COLUMN status VARCHAR DEFAULT 'done'",
        "ALTER TABLE exams ADD COLUMN approved_by VARCHAR",
        "ALTER TABLE exams ADD COLUMN approved_at DATE",
        "ALTER TABLE exams ADD COLUMN retake_of_id INTEGER",
        "ALTER TABLE exams ADD COLUMN note TEXT",
        # Eski imtihonlar allaqachon o'tkazilgan - ular "done".
        "UPDATE exams SET status = 'done' WHERE status IS NULL",
        "ALTER TABLE groups ADD COLUMN room_id INTEGER",
        "ALTER TABLE groups ADD COLUMN capacity INTEGER",
        "ALTER TABLE students ADD COLUMN public_id VARCHAR",
        "ALTER TABLE students ADD COLUMN parent_id INTEGER",
        "ALTER TABLE leads ADD COLUMN public_id VARCHAR",
        "ALTER TABLE groups ADD COLUMN public_id VARCHAR",
        "ALTER TABLE payments ADD COLUMN public_id VARCHAR",
        "ALTER TABLE users ADD COLUMN public_id VARCHAR",
        "ALTER TABLE lessons ADD COLUMN held INTEGER DEFAULT 1",
        # Eski darslar qo'lda kiritilgan - demak ular o'tilgan.
        "UPDATE lessons SET held = 1 WHERE held IS NULL",
        "ALTER TABLE groups ADD COLUMN end_date DATE",
        "ALTER TABLE expenses ADD COLUMN channel VARCHAR",
        "ALTER TABLE expenses ADD COLUMN method VARCHAR",
        "UPDATE expenses SET method = 'cash' WHERE method IS NULL",
        "ALTER TABLE leads ADD COLUMN address VARCHAR",
        "ALTER TABLE leads ADD COLUMN school VARCHAR",
        "ALTER TABLE leads ADD COLUMN grade VARCHAR",
        # "administrator" roli "founder" (Asoschi) deb qayta nomlandi.
        # Bizning markazda "Administrator" - bu sotuv menejeri, tizim
        # egasi emas. Eski hisoblarni yangi kalitga ko'chiramiz.
        "UPDATE users SET role = 'founder' WHERE role = 'administrator'",
        # To'lov qaysi kanal orqali kelgani (naqd/plastik/terminal).
        "ALTER TABLE payments ADD COLUMN method VARCHAR",
        # LTV hisoboti uchun - o'quvchi qachon ketgani.
        "ALTER TABLE students ADD COLUMN left_date DATE",
        # Arxivdagi eski o'quvchilarda ketgan sana yo'q edi; ularni
        # LTV'dan tushib qolmasligi uchun qo'shilgan sana bilan emas,
        # oxirgi ma'lum sana - yaratilgan kun bilan to'ldiramiz.
        "UPDATE students SET left_date = DATE(created_at) "
        "WHERE status = 'archived' AND left_date IS NULL",
        # Ustozlar retention hisoboti uchun.
        "ALTER TABLE teachers ADD COLUMN hired_date DATE",
        "ALTER TABLE teachers ADD COLUMN left_date DATE",
        "ALTER TABLE teachers ADD COLUMN is_active INTEGER DEFAULT 1",
        "UPDATE teachers SET is_active = 1 WHERE is_active IS NULL",
        # Eski ustozlarda ishga kirgan sana yo'q - tizimga qo'shilgan
        # kunni boshlanish nuqtasi deb olamiz.
        "UPDATE teachers SET hired_date = DATE(created_at) WHERE hired_date IS NULL",
        # Adminlar KPI'si uchun fiks oylik.
        "ALTER TABLE users ADD COLUMN fix_salary FLOAT",
        # Guruh: fan, daraja va boshlanish sanasi.
        "ALTER TABLE groups ADD COLUMN subject VARCHAR",
        "ALTER TABLE groups ADD COLUMN level VARCHAR",
        "ALTER TABLE groups ADD COLUMN start_date DATE",
        "ALTER TABLE groups ADD COLUMN lesson_time VARCHAR",
        "ALTER TABLE groups ADD COLUMN lesson_days VARCHAR",
    ]
    for stmt in statements:
        try:
            with engine.begin() as conn:
                conn.execute(text(stmt))
        except Exception:
            pass

    # Imtihon coin qoidasi bo'sh bo'lsa, boshlang'ich jadvalni qo'yamiz -
    # asoschi uni keyin Gamification bo'limidan o'zgartiradi.
    try:
        from sqlalchemy.orm import Session as _S
        with _S(engine) as db:
            if db.query(models.ExamCoinRule).count() == 0:
                for pct, coins in roles.DEFAULT_EXAM_COIN_RULES:
                    db.add(models.ExamCoinRule(min_percent=pct, coins=coins))
                db.commit()

            # Adminlar KPI qoidalari ham xuddi shunday: bir marta
            # seed qilinadi, keyin asoschi o'zgartiradi.
            if db.query(models.KpiCollectionRule).count() == 0:
                for mn, mx, pct, bonus in roles.DEFAULT_KPI_COLLECTION_RULES:
                    db.add(models.KpiCollectionRule(
                        min_students=mn, max_students=mx,
                        min_percent=pct, bonus=bonus))
                db.commit()
            if db.query(models.KpiNewClientRule).count() == 0:
                for cnt, bonus in roles.DEFAULT_KPI_NEW_CLIENT_RULES:
                    db.add(models.KpiNewClientRule(min_clients=cnt, bonus=bonus))
                db.commit()
    except Exception:
        pass


# ---- Ommaviy ID (STU-000123) ----------------------------------------
# Har bir shaxs va hujjatga bitta o'zgarmas raqam. Telefon yoki ism
# o'zgarsa ham bu qoladi: tarix, shartnoma va to'lov shunga bog'lanadi.
PUBLIC_ID_PREFIX = {
    "student": "STU",
    "parent": "PAR",
    "user": "EMP",
    "lead": "LID",
    "group": "GRP",
    "payment": "PAY",
    "contract": "SHT",
}


def _make_public_id(kind: str, row_id: int) -> str:
    return f"{PUBLIC_ID_PREFIX[kind]}-{row_id:06d}"


def _ensure_public_id(db, kind: str, obj) -> str:
    """Obyektga ommaviy ID beradi (agar hali bo'lmasa). ID ichki
    raqamdan hosil qilinadi - shuning uchun hech qachon takrorlanmaydi."""
    if not getattr(obj, "public_id", None):
        obj.public_id = _make_public_id(kind, obj.id)
    return obj.public_id


def backfill_missing_ids(db, kind: str, model) -> None:
    """ID'siz qolgan yozuvlarga ID beradi. Ro'yxat ochilganda
    chaqiriladi: odatda hech nima topmaydi (indeksli bitta so'rov),
    lekin bazaga tashqaridan qo'shilgan yozuv ham ID'siz qolmaydi."""
    try:
        rows = db.query(model).filter(model.public_id.is_(None)).all()
        if not rows:
            return
        for r in rows:
            r.public_id = _make_public_id(kind, r.id)
        db.commit()
    except Exception:
        db.rollback()


def _backfill_public_ids():
    """Ilova ishga tushganda ID'siz qolgan eski yozuvlarni to'ldiradi."""
    from database import SessionLocal
    pairs = [
        ("student", models.Student), ("parent", models.Parent),
        ("user", models.User), ("lead", models.Lead),
        ("group", models.Group), ("payment", models.Payment),
        ("contract", models.Contract),
    ]
    db = SessionLocal()
    try:
        for kind, model in pairs:
            try:
                rows = db.query(model).filter(model.public_id.is_(None)).all()
            except Exception:
                continue
            for r in rows:
                r.public_id = _make_public_id(kind, r.id)
            if rows:
                db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


_ensure_new_columns()
_backfill_public_ids()

app = FastAPI(title="Jony Academy CRM API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten before real deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/_bootstrap")
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


def student_balance(db: Session, student_id: int) -> float:
    total = (
        db.query(func.coalesce(func.sum(models.Payment.amount), 0.0))
        .filter(models.Payment.student_id == student_id)
        .scalar()
    )
    return float(total or 0)


def to_student_out(db: Session, s: models.Student) -> schemas.StudentOut:
    data = schemas.StudentOut.model_validate(s)
    data.balance = student_balance(db, s.id)
    return data


def _sync_student_left_date(s: models.Student):
    """Ketgan sanani statusdan avtomatik chiqaramiz - hech kim uni qo'lda
    kiritmaydi, shuning uchun LTV hisoboti hech qachon "esdan chiqib"
    qolmaydi. "archived" = markazni tark etgan."""
    if s.status == "archived":
        if not s.left_date:
            s.left_date = date.today()
    else:
        # Qaytib keldi - hisobot uni yana faol mijoz deb ko'rsin.
        s.left_date = None


def _sync_teacher_left_date(t: models.Teacher):
    """Ustoz ishdan ketgan/qaytgan sanasini is_active'dan avtomatik olamiz."""
    if not t.hired_date:
        t.hired_date = date.today()
    if t.is_active:
        t.left_date = None
    elif not t.left_date:
        t.left_date = date.today()


def _months_between(start: date, end: date) -> float:
    """Ikki sana orasidagi oylar soni (kasrli). LTV va retention shu
    o'lchovda ko'rsatiladi - "3.5 oy" degani odamga tushunarli."""
    if not start or not end or end < start:
        return 0.0
    return round((end - start).days / 30.44, 1)


def scope_to_branch(query, model, user: models.User, branch_id=None):
    """Filialga bo'yicha cheklash.

    Ikki xil cheklash bor va ular aralashmasligi kerak:
      1) HUQUQ - filialga bog'langan xodim faqat o'z filialini ko'radi.
         Buni hech kim aylanib o'ta olmaydi.
      2) FILTR - butun tashkilotni ko'radigan odam (asoschi, HR, SMM)
         istagan filialni alohida ko'rmoqchi bo'lsa, branch_id beradi.
    """
    if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
        # Huquq cheklovi: o'z filiali. So'ralgan filial boshqa bo'lsa ham
        # baribir o'ziniki qaytadi.
        return query.filter(model.branch_id == user.branch_id)
    if branch_id and hasattr(model, "branch_id"):
        return query.filter(model.branch_id == branch_id)
    return query


# ---------------------------------------------------------------- Auth ----
@app.post("/api/auth/login", response_model=schemas.Token)
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == payload.username).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Login yoki parol noto'g'ri")
    if not user.is_active:
        raise HTTPException(status_code=401, detail="Bu hisob faolsizlantirilgan")
    token = create_access_token({"sub": user.username})
    return schemas.Token(
        access_token=token, role=user.role, full_name=user.full_name, branch_id=user.branch_id
    )


@app.get("/api/auth/me", response_model=schemas.UserOut)
def me(user: models.User = Depends(get_current_user)):
    return user


@app.put("/api/auth/me/password")
def change_own_password(
    payload: schemas.ChangePasswordRequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Joriy parol noto'g'ri")
    if len(payload.new_password) < 6:
        raise HTTPException(
            status_code=400, detail="Yangi parol kamida 6 belgidan iborat bo'lishi kerak"
        )
    user.password_hash = hash_password(payload.new_password)
    db.commit()
    return {"ok": True}


# ----------------------------------------------------------- Branches -----
@app.get("/api/branches", response_model=List[schemas.BranchOut])
def list_branches(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(models.Branch).order_by(models.Branch.name).all()


@app.post("/api/branches", response_model=schemas.BranchOut)
def create_branch(
    payload: schemas.BranchCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(roles.FOUNDER)),
):
    branch = models.Branch(**payload.model_dump())
    db.add(branch)
    db.commit()
    db.refresh(branch)
    return branch


@app.put("/api/branches/{branch_id}", response_model=schemas.BranchOut)
def update_branch(
    branch_id: int,
    payload: schemas.BranchCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(roles.FOUNDER)),
):
    b = db.query(models.Branch).get(branch_id)
    if not b:
        raise HTTPException(404, "Filial topilmadi")
    if not payload.name.strip():
        raise HTTPException(400, "Filial nomini kiriting")
    b.name = payload.name.strip()
    b.address = payload.address
    db.commit()
    db.refresh(b)
    return b


@app.delete("/api/branches/{branch_id}")
def delete_branch(
    branch_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(roles.FOUNDER)),
):
    """Filialni faqat bo'sh bo'lsa o'chirish mumkin - aks holda
    o'quvchi va guruhlar "yetim" qolib ketardi."""
    b = db.query(models.Branch).get(branch_id)
    if not b:
        raise HTTPException(404, "Filial topilmadi")
    for model, nomi in ((models.Student, "o'quvchi"), (models.Group, "guruh"),
                        (models.Teacher, "ustoz"), (models.User, "xodim")):
        n = db.query(model).filter(model.branch_id == branch_id).count()
        if n:
            raise HTTPException(
                400, f"Bu filialda {n} ta {nomi} bor - avval ularni "
                     "boshqa filialga o'tkazing")
    db.delete(b)
    db.commit()
    return {"ok": True}


# --------------------------------------------------------------- Users ----
def _guard_role_assignment(
    requester: models.User, target_role: str, target_branch_id: Optional[int]
):
    """Rol berish - tizimdagi eng xavfli amal, shuning uchun uni faqat
    asoschi bajaradi (roles.USER_ADMIN). Bu yerda yana bir bor tekshiramiz:
    endpoint himoyasi kelajakda kengaytirilib ketsa ham, huquqni oshirib
    yuborishning oldi olinadi."""
    if requester.role != roles.FOUNDER:
        raise HTTPException(403, "Rol belgilash huquqi faqat asoschida")
    if target_role not in roles.ALL_ROLES:
        raise HTTPException(400, "Noto'g'ri rol")


@app.get("/api/users", response_model=List[schemas.UserOut])
def list_users(
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(*roles.STAFF_VIEWERS)),
):
    backfill_missing_ids(db, "user", models.User)
    q = scope_to_branch(db.query(models.User), models.User, user)
    return q.order_by(models.User.full_name).all()


@app.get("/api/users/assignable", response_model=List[schemas.StaffOption])
def list_assignable_staff(
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(*roles.LEAD_ACCESS)),
):
    """Lidga mas'ul qilib biriktirish mumkin bo'lgan xodimlar. /api/users
    faqat HR/adminlar uchun ochiq, shuning uchun SMM manager ham
    ishlata oladigan qisqartirilgan ro'yxat kerak."""
    q = scope_to_branch(db.query(models.User), models.User, user)
    return q.filter(models.User.is_active == 1).order_by(models.User.full_name).all()


@app.post("/api/users", response_model=schemas.UserOut)
def create_user(
    payload: schemas.UserCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(*roles.USER_ADMIN)),
):
    if payload.role not in roles.ALL_ROLES:
        raise HTTPException(400, "Noto'g'ri rol")
    _guard_role_assignment(user, payload.role, payload.branch_id)
    if db.query(models.User).filter(models.User.username == payload.username).first():
        raise HTTPException(400, "Bu login band, boshqasini tanlang")

    new_user = models.User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        role=payload.role,
        branch_id=payload.branch_id,
        fix_salary=payload.fix_salary,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.put("/api/users/{user_id}", response_model=schemas.UserOut)
def update_user(
    user_id: int,
    payload: schemas.UserUpdate,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(*roles.USER_ADMIN)),
):
    target = db.query(models.User).get(user_id)
    if not target:
        raise HTTPException(404, "Foydalanuvchi topilmadi")

    new_role = payload.role if payload.role is not None else target.role
    new_branch_id = (
        payload.branch_id if payload.branch_id is not None else target.branch_id
    )
    _guard_role_assignment(user, new_role, new_branch_id)
    if user.role == roles.BRANCH_MANAGER and target.branch_id != user.branch_id:
        raise HTTPException(403, "Faqat o'z filialingiz xodimlarini tahrirlay olasiz")
    if target.id == user.id and payload.is_active is False:
        raise HTTPException(400, "O'zingizni faolsizlantira olmaysiz")

    # O'zgarishlarni qo'llashdan OLDIN yozib olamiz.
    audit.log_changes(
        db, user, entity="user", obj=target,
        changes={k: v for k, v in payload.model_dump(exclude_unset=True).items()
                 if k != "password"})
    if payload.password:
        audit.log(db, user, entity="user", action="update", entity_id=target.id,
                  entity_label=target.full_name, field="password",
                  note="Parol o'zgartirildi", branch_id=target.branch_id)

    if payload.full_name is not None:
        target.full_name = payload.full_name
    if payload.role is not None:
        target.role = payload.role
    if payload.branch_id is not None:
        target.branch_id = payload.branch_id
    if payload.is_active is not None:
        target.is_active = int(payload.is_active)
    if payload.password:
        target.password_hash = hash_password(payload.password)
    # Fiks oylik - KPI hisobining asosi, shuning uchun uni faqat asoschi
    # (roles.USER_ADMIN) o'zgartira oladi; endpoint allaqachon shu bilan
    # himoyalangan. exclude_unset orqali "berilmagan" va "0 qilindi"
    # holatlarini ajratamiz.
    if "fix_salary" in payload.model_dump(exclude_unset=True):
        target.fix_salary = payload.fix_salary

    db.commit()
    db.refresh(target)
    return target


# ----------------------------------------------------------- Dashboard ----
@app.get("/api/dashboard", response_model=schemas.DashboardStats)
def dashboard(
    db: Session = Depends(get_db), user: models.User = Depends(get_current_user)
):
    student_q = scope_to_branch(db.query(models.Student), models.Student, user)
    active = student_q.filter(models.Student.status == "active").count()
    trial = student_q.filter(models.Student.status == "trial").count()
    frozen = student_q.filter(models.Student.status == "frozen").count()
    groups = scope_to_branch(db.query(models.Group), models.Group, user).count()
    teachers = scope_to_branch(db.query(models.Teacher), models.Teacher, user).count()

    month_start = date.today().replace(day=1)
    all_students = student_q.all()
    student_ids = [s.id for s in all_students]

    month_income = 0.0
    if student_ids:
        month_income = (
            db.query(func.coalesce(func.sum(models.Payment.amount), 0.0))
            .filter(models.Payment.kind == "payment")
            .filter(models.Payment.created_at >= month_start)
            .filter(models.Payment.student_id.in_(student_ids))
            .scalar()
            or 0.0
        )

    # Shu oydagi to'lovlar soni va shundan nechtasi YANGI mijoz
    month_pay_count = 0
    month_new_count = 0
    if student_ids:
        pays = (
            db.query(models.Payment)
            .filter(models.Payment.kind == "payment")
            .filter(models.Payment.created_at >= month_start)
            .filter(models.Payment.student_id.in_(student_ids))
            .all()
        )
        month_pay_count = len(pays)
        firsts = _payment_first_dates(db)
        month_new_count = sum(
            1 for p in pays if firsts.get(p.student_id) == p.created_at
        )

    staff_count = scope_to_branch(
        db.query(models.User), models.User, user
    ).filter(models.User.is_active == 1).count()

    balances = [(s.id, student_balance(db, s.id)) for s in all_students]
    total_debt = sum(b for _, b in balances if b < 0)
    debtor_count = sum(1 for _, b in balances if b < 0)

    return schemas.DashboardStats(
        active_students=active,
        trial_students=trial,
        frozen_students=frozen,
        total_groups=groups,
        total_teachers=teachers,
        month_payment_count=month_pay_count,
        month_new_payment_count=month_new_count,
        staff_count=staff_count,
        month_income=float(month_income),
        total_debt=float(total_debt),
        debtor_count=debtor_count,
    )


@app.get("/api/dashboard/trend")
def dashboard_trend(
    months: int = 6,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Income for each of the last `months` calendar months, scoped to the
    caller's branch the same way /api/dashboard is. Used for the dashboard
    trend chart."""
    student_q = scope_to_branch(db.query(models.Student), models.Student, user)
    student_ids = [s.id for s in student_q.all()]

    today = date.today()
    y, m = today.year, today.month
    periods = []
    for _ in range(max(1, min(months, 24))):
        periods.append((y, m))
        m -= 1
        if m == 0:
            y, m = y - 1, 12
    periods.reverse()

    results = []
    for yy, mm in periods:
        start, end = billing.month_bounds(yy, mm)
        income = 0.0
        if student_ids:
            income = (
                db.query(func.coalesce(func.sum(models.Payment.amount), 0.0))
                .filter(models.Payment.kind == "payment")
                .filter(models.Payment.created_at >= start)
                .filter(models.Payment.created_at < end + timedelta(days=1))
                .filter(models.Payment.student_id.in_(student_ids))
                .scalar()
                or 0.0
            )
        results.append({"period": f"{yy:04d}-{mm:02d}", "income": float(income)})
    return results


@app.get("/api/dashboard/student-growth")
def student_growth(
    window: str = "6m",
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Cumulative enrolled-student count over time, scoped like /api/dashboard.
    `window` picks both the range and the bucket size:
    - "1m":  last 30 days, daily buckets
    - "6m":  last 6 months, monthly buckets (default)
    - "1y":  last 12 months, monthly buckets
    - "all": from the earliest enrollment to today, monthly buckets
    Each point's count is the number of students whose enrolled_date falls
    on or before that bucket's date - i.e. a running total, so the line
    tracks how the student base has grown."""
    student_q = scope_to_branch(db.query(models.Student), models.Student, user)
    dates = sorted(s.enrolled_date for s in student_q.all() if s.enrolled_date)
    today = date.today()
    granularity = "day" if window == "1m" else "month"

    if not dates:
        return {"granularity": granularity, "points": []}

    def count_through(cutoff: date) -> int:
        return bisect.bisect_right(dates, cutoff)

    points = []
    if window == "1m":
        d = today - timedelta(days=29)
        while d <= today:
            points.append({"period": d.isoformat(), "count": count_through(d)})
            d += timedelta(days=1)
    else:
        if window == "1y":
            months_back = 11
        elif window == "all":
            earliest = dates[0]
            months_back = (today.year - earliest.year) * 12 + (today.month - earliest.month)
        else:  # "6m" and any unrecognized value
            months_back = 5
        y, m = today.year, today.month
        periods = []
        for _ in range(months_back + 1):
            periods.append((y, m))
            m -= 1
            if m == 0:
                y, m = y - 1, 12
        periods.reverse()
        for yy, mm in periods:
            _, month_end = billing.month_bounds(yy, mm)
            cutoff = min(month_end, today)
            points.append({"period": f"{yy:04d}-{mm:02d}", "count": count_through(cutoff)})

    return {"granularity": granularity, "points": points}


# --------------------------------------------------------------- Lidlar ----
def _get_lead_in_scope(db: Session, lead_id: int, user: models.User) -> models.Lead:
    lead = db.query(models.Lead).get(lead_id)
    if not lead:
        raise HTTPException(404, "Lid topilmadi")
    if user.role not in tuple(roles.ORG_WIDE_ROLES):
        if user.branch_id and lead.branch_id != user.branch_id:
            raise HTTPException(403, "Bu lid boshqa filialga tegishli")
    return lead


def _validate_lead_fields(source: Optional[str], stage: Optional[str]):
    if source is not None and source not in roles.LEAD_SOURCES:
        raise HTTPException(400, "Noto'g'ri manba")
    if stage is not None and stage not in roles.LEAD_STAGES:
        raise HTTPException(400, "Noto'g'ri bosqich")


@app.get("/api/leads", response_model=List[schemas.LeadOut])
def list_leads(
    stage: Optional[str] = None,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(*roles.LEAD_ACCESS)),
):
    backfill_missing_ids(db, "lead", models.Lead)
    q = scope_to_branch(db.query(models.Lead), models.Lead, user)
    if stage:
        q = q.filter(models.Lead.stage == stage)
    else:
        # O'quvchiga aylangan lid doskada turmaydi - u endi Talabalar
        # bo'limida. Voronka hisobotlari to'g'ridan-to'g'ri bazadan
        # o'qiydi, shuning uchun statistika buzilmaydi.
        q = q.filter(models.Lead.stage != "converted")
    return q.order_by(models.Lead.updated_at.desc(), models.Lead.id.desc()).all()


@app.post("/api/leads", response_model=schemas.LeadOut)
def create_lead(
    payload: schemas.LeadCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(*roles.LEAD_ACCESS)),
):
    if not payload.full_name.strip():
        raise HTTPException(400, "Ism-familiyani kiriting")
    _validate_lead_fields(payload.source, payload.stage)

    # Bosqich berilmasa, manbaga qarab o'zi tanlanadi: tashrif bilan kelgan
    # odam "unga qo'ng'iroq qilish kerak" bosqichini o'tib bo'lgan.
    stage = payload.stage or roles.LEAD_SOURCE_DEFAULT_STAGE.get(payload.source, "new")

    lead = models.Lead(
        full_name=payload.full_name.strip(),
        phone=payload.phone,
        source=payload.source,
        stage=stage,
        address=payload.address,
        school=payload.school,
        grade=payload.grade,
        note=payload.note,
        branch_id=payload.branch_id if payload.branch_id is not None else user.branch_id,
        assigned_user_id=payload.assigned_user_id,
        created_by=user.full_name,
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead


@app.put("/api/leads/{lead_id}", response_model=schemas.LeadOut)
def update_lead(
    lead_id: int,
    payload: schemas.LeadUpdate,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(*roles.LEAD_ACCESS)),
):
    lead = _get_lead_in_scope(db, lead_id, user)
    _validate_lead_fields(payload.source, payload.stage)

    data = payload.model_dump(exclude_unset=True)
    if data.get("stage") == "converted" and not lead.converted_student_id:
        raise HTTPException(
            400,
            "Lidni bu bosqichga qo'lda surib bo'lmaydi - "
            "\"O'quvchiga aylantirish\" tugmasidan foydalaning",
        )
    for k, v in data.items():
        setattr(lead, k, v)
    db.commit()
    db.refresh(lead)
    return lead


@app.delete("/api/leads/{lead_id}")
def delete_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(*roles.FULL_ACCESS)),
):
    lead = _get_lead_in_scope(db, lead_id, user)
    db.delete(lead)
    db.commit()
    return {"ok": True}


@app.post("/api/leads/{lead_id}/convert", response_model=schemas.StudentOut)
def convert_lead(
    lead_id: int,
    payload: schemas.LeadConvertRequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(*roles.LEAD_ACCESS)),
):
    """Lidni haqiqiy o'quvchiga aylantiradi. Lid o'chirilmaydi - bosqichi
    "converted" bo'ladi va yaratilgan o'quvchiga bog'lanadi, shunda
    voronka statistikasi saqlanib qoladi."""
    lead = _get_lead_in_scope(db, lead_id, user)
    if lead.converted_student_id:
        raise HTTPException(400, "Bu lid allaqachon o'quvchiga aylantirilgan")

    # Lidda yig'ilgan qo'shimcha ma'lumot (manzil, maktab, sinf) yo'qolib
    # ketmasligi uchun uni o'quvchining izohiga ko'chiramiz.
    extra = []
    if lead.address:
        extra.append(f"Manzil: {lead.address}")
    if lead.school:
        extra.append(f"Maktab: {lead.school}")
    if lead.grade:
        extra.append(f"Sinf: {lead.grade}")
    if lead.note:
        extra.append(lead.note)
    student_note = " · ".join(extra) if extra else None

    student = models.Student(
        full_name=lead.full_name,
        phone=lead.phone,
        group_id=payload.group_id,
        branch_id=lead.branch_id,
        enrolled_date=payload.enrolled_date or date.today(),
        status="active",
        note=student_note,
    )
    db.add(student)
    db.flush()

    lead.stage = "converted"
    lead.converted_student_id = student.id
    db.commit()
    db.refresh(student)
    return to_student_out(db, student)


# ----------------------------------------------------------- Xarajatlar ----
def _get_expense_in_scope(db: Session, expense_id: int, user: models.User) -> models.Expense:
    exp = db.query(models.Expense).get(expense_id)
    if not exp:
        raise HTTPException(404, "Xarajat topilmadi")
    if user.role not in tuple(roles.ORG_WIDE_ROLES):
        if user.branch_id and exp.branch_id != user.branch_id:
            raise HTTPException(403, "Bu xarajat boshqa filialga tegishli")
    return exp


@app.get("/api/expenses", response_model=List[schemas.ExpenseOut])
def list_expenses(
    year: Optional[int] = None,
    month: Optional[int] = None,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(*roles.FINANCE_ACCESS)),
):
    """Xarajatlar ro'yxati. year/month berilsa - o'sha oy uchun."""
    q = scope_to_branch(db.query(models.Expense), models.Expense, user)
    if year and month:
        start, end = billing.month_bounds(year, month)
        q = q.filter(models.Expense.date >= start, models.Expense.date <= end)
    return q.order_by(models.Expense.date.desc(), models.Expense.id.desc()).all()


@app.post("/api/expenses", response_model=schemas.ExpenseOut)
def create_expense(
    payload: schemas.ExpenseCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(*roles.FINANCE_ACCESS)),
):
    if payload.category not in roles.EXPENSE_CATEGORIES:
        raise HTTPException(400, "Noto'g'ri xarajat turi")
    if payload.amount <= 0:
        raise HTTPException(400, "Summa noldan katta bo'lishi kerak")

    exp = models.Expense(
        date=payload.date,
        category=payload.category,
        amount=abs(payload.amount),
        note=payload.note,
        branch_id=payload.branch_id if payload.branch_id is not None else user.branch_id,
        # Kanal faqat reklama xarajatida ma'noga ega - CAC shundan chiqadi.
        channel=payload.channel,
        method=payload.method or "cash",
        created_by=user.full_name,
    )
    db.add(exp)
    db.commit()
    db.refresh(exp)
    audit.log(db, user, entity="expense", action="create", entity_id=exp.id,
              entity_label=exp.note or exp.category, field=exp.category,
              new_value=exp.amount, branch_id=exp.branch_id, commit=True)
    return exp


@app.put("/api/expenses/{expense_id}", response_model=schemas.ExpenseOut)
def update_expense(
    expense_id: int,
    payload: schemas.ExpenseUpdate,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(*roles.FINANCE_ACCESS)),
):
    exp = _get_expense_in_scope(db, expense_id, user)
    data = payload.model_dump(exclude_unset=True)
    if "category" in data and data["category"] not in roles.EXPENSE_CATEGORIES:
        raise HTTPException(400, "Noto'g'ri xarajat turi")
    if "amount" in data:
        if data["amount"] is None or data["amount"] <= 0:
            raise HTTPException(400, "Summa noldan katta bo'lishi kerak")
        data["amount"] = abs(data["amount"])
    audit.log_changes(db, user, entity="expense", obj=exp, changes=data,
                      label_attr="note")
    for k, v in data.items():
        setattr(exp, k, v)
    db.commit()
    db.refresh(exp)
    return exp


@app.delete("/api/expenses/{expense_id}")
def delete_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(*roles.FINANCE_ACCESS)),
):
    exp = _get_expense_in_scope(db, expense_id, user)
    audit.log(db, user, entity="expense", action="delete", entity_id=exp.id,
              entity_label=exp.note or exp.category, field=exp.category,
              old_value=exp.amount, branch_id=exp.branch_id)
    db.delete(exp)
    db.commit()
    return {"ok": True}


# ------------------------------------------------- Coin (gamification) ----
# Muhim tamoyil: coin hech qachon qo'lda "qo'shilmaydi". Baho yoki imtihon
# natijasi saqlanishi bilan tegishli CoinEntry avtomat yaratiladi/yangilanadi,
# natija o'chirilsa coin ham qaytariladi. Shuning uchun balans hech qachon
# haqiqatdan uzilib qolmaydi.


def _sync_coin_entry(db: Session, *, student_id: int, source: str, ref_id: int,
                     amount: int, note: str = None, created_by: str = None):
    """Bitta manba uchun bitta coin yozuvini saqlaydi (upsert).
    amount = 0 bo'lsa yozuv butunlay o'chiriladi."""
    entry = (
        db.query(models.CoinEntry)
        .filter(models.CoinEntry.source == source,
                models.CoinEntry.ref_id == ref_id)
        .first()
    )
    if amount == 0:
        if entry:
            db.delete(entry)
        return None
    if entry:
        entry.student_id = student_id
        entry.amount = amount
        entry.note = note
        return entry
    entry = models.CoinEntry(student_id=student_id, amount=amount,
                             source=source, ref_id=ref_id, note=note,
                             created_by=created_by)
    db.add(entry)
    return entry


def _drop_coin_entry(db: Session, source: str, ref_id: int):
    db.query(models.CoinEntry).filter(
        models.CoinEntry.source == source, models.CoinEntry.ref_id == ref_id
    ).delete(synchronize_session=False)


def _coins_for_percent(db: Session, percent: float, kind: str) -> int:
    """Foizdan coin. Avval shu test turiga maxsus qoida qidiriladi,
    topilmasa umumiy (kind=None) qoidalar ishlatiladi."""
    if percent is None:
        return 0
    rules = db.query(models.ExamCoinRule).all()
    scoped = [r for r in rules if r.kind == kind]
    general = [r for r in rules if not r.kind]
    for group in (scoped, general):
        matching = [r for r in group if percent >= r.min_percent]
        if matching:
            # Bir nechta qoida to'g'ri kelsa, eng yuqori bosqichnikini olamiz.
            return max(matching, key=lambda r: r.min_percent).coins
    return 0


def _student_coin_balance(db: Session, student_id: int) -> int:
    total = (
        db.query(func.coalesce(func.sum(models.CoinEntry.amount), 0))
        .filter(models.CoinEntry.student_id == student_id)
        .scalar()
    )
    return int(total or 0)


# -------------------------------------------- Davomat va kunlik baho ----
def _group_students(db: Session, group_id: int):
    return (
        db.query(models.Student)
        .filter(models.Student.group_id == group_id)
        .order_by(models.Student.full_name)
        .all()
    )


# Python'da hafta kuni: 0=Dushanba ... 6=Yakshanba
_WEEKDAY_INDEX = {"mon": 0, "tue": 1, "wed": 2, "thu": 3,
                  "fri": 4, "sat": 5, "sun": 6}


def _sync_scheduled_lessons(db: Session, group: models.Group,
                            start: date, end: date) -> None:
    """Guruhning dars kunlari ("mon,wed,fri") bo'yicha shu oydagi barcha
    dars kunlarini AVTOMAT yaratadi.

    Har bir darsni qo'lda kiritish shart emas: kunlar tanlangan bo'lsa,
    butun oy jadvali yoqlama qo'yishga tayyor holda chiqadi. Yangi
    yaratilgan darslar held=0 ("rejalashtirilgan") bo'ladi - ular pulga
    ham, ustoz ish haqiga ham kirmaydi, toki yoqlama qo'yilmaguncha.

    Jadval o'zgarsa (masalan juma olib tashlansa) - endi mos kelmaydigan,
    hali yoqlama ham baho ham qo'yilmagan darslar tozalanadi."""
    days = [d.strip() for d in (group.lesson_days or "").split(",") if d.strip()]
    wanted = {_WEEKDAY_INDEX[d] for d in days if d in _WEEKDAY_INDEX}

    existing = (
        db.query(models.Lesson)
        .filter(models.Lesson.group_id == group.id,
                models.Lesson.date >= start, models.Lesson.date <= end)
        .all()
    )
    by_date = {ls.date: ls for ls in existing}

    # Guruh boshlangunicha va tugagandan keyin dars bo'lmaydi.
    lo = max(start, group.start_date) if group.start_date else start
    hi = min(end, group.end_date) if group.end_date else end

    changed = False
    if wanted:
        d = lo
        while d <= hi:
            if d.weekday() in wanted and d not in by_date:
                db.add(models.Lesson(
                    group_id=group.id, teacher_id=group.teacher_id,
                    date=d, held=0, created_by="avtomat"))
                changed = True
            d += timedelta(days=1)

    # Jadvalga mos kelmay qolgan bo'sh darslarni olib tashlaymiz.
    stale = [ls for ls in existing
             if not ls.held and (ls.date.weekday() not in wanted
                                 or ls.date < lo or ls.date > hi)]
    for ls in stale:
        has_data = (
            db.query(models.Attendance)
            .filter(models.Attendance.lesson_id == ls.id).first()
            or db.query(models.DailyGrade)
            .filter(models.DailyGrade.lesson_id == ls.id).first()
        )
        if not has_data:
            db.delete(ls)
            changed = True

    if changed:
        db.commit()


def _mark_lesson_held(db: Session, lesson: models.Lesson) -> None:
    """Yoqlama yoki baho qo'yilgan dars - o'tilgan dars. Shundan keyingina
    u pulga va ustoz ish haqiga kiradi."""
    if not lesson.held:
        lesson.held = 1


def _group_lessons_in_month(db: Session, group_id: int, year: int, month: int):
    start, end = billing.month_bounds(year, month)
    group = db.query(models.Group).get(group_id)
    if group:
        _sync_scheduled_lessons(db, group, start, end)
    return (
        db.query(models.Lesson)
        .filter(models.Lesson.group_id == group_id,
                models.Lesson.date >= start, models.Lesson.date <= end)
        .order_by(models.Lesson.date)
        .all()
    )


@app.get("/api/groups/{group_id}/attendance", response_model=schemas.AttendanceGrid)
def attendance_grid(
    group_id: int,
    year: int,
    month: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_ACCESS)),
):
    """Davomat jadvali: chapda o'quvchilar, tepada shu oydagi dars kunlari."""
    _get_group_in_scope(db, group_id, user)
    students = _group_students(db, group_id)
    lessons = _group_lessons_in_month(db, group_id, year, month)
    lesson_ids = [ls.id for ls in lessons]

    marks = {}
    if lesson_ids:
        rows = db.query(models.Attendance).filter(
            models.Attendance.lesson_id.in_(lesson_ids)
        ).all()
        marks = {f"{a.lesson_id}:{a.student_id}": bool(a.present) for a in rows}

    return schemas.AttendanceGrid(
        students=[schemas.GridStudent(id=s.id, full_name=s.full_name,
                                      status=s.status) for s in students],
        lessons=[schemas.GridLesson(id=ls.id, date=ls.date, held=ls.held or 0)
                 for ls in lessons],
        marks=marks,
    )


@app.put("/api/lessons/{lesson_id}/attendance")
def save_attendance(
    lesson_id: int,
    payload: schemas.AttendanceBulk,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_ACCESS)),
):
    """Bitta dars kunining butun ustunini saqlaydi."""
    lesson = db.query(models.Lesson).get(lesson_id)
    if not lesson:
        raise HTTPException(404, "Dars topilmadi")
    _get_group_in_scope(db, lesson.group_id, user)

    existing = {
        a.student_id: a
        for a in db.query(models.Attendance).filter(
            models.Attendance.lesson_id == lesson_id).all()
    }
    for m in payload.marks:
        row = existing.get(m.student_id)
        if row:
            row.present = 1 if m.present else 0
        else:
            db.add(models.Attendance(
                lesson_id=lesson_id, student_id=m.student_id,
                present=1 if m.present else 0, created_by=user.full_name))
    _mark_lesson_held(db, lesson)
    db.commit()

    # Sinovdagi o'quvchilar: yoqlama qo'yilishi bilan lid "sinovga keldi"
    # bo'ladi, uchinchi darsdan keyin esa o'quvchi AVTOMAT faollashadi.
    activated, touched = [], False
    for m in payload.marks:
        if not m.present:
            continue
        st = db.query(models.Student).get(m.student_id)
        if not st or st.status != "trial":
            continue
        lead = (db.query(models.Lead)
                .filter(models.Lead.converted_student_id == st.id).first())
        if not lead:
            lead = (db.query(models.Lead)
                    .filter(models.Lead.full_name == st.full_name,
                            models.Lead.stage.in_(["trial_scheduled", "no_show",
                                                   "contacted", "new"]))
                    .first())
        if lead and lead.stage != "trial_attended":
            lead.stage = "trial_attended"
            touched = True
        res = _maybe_auto_activate(db, st, user=user)
        if res:
            touched = True
            activated.append({"student_id": st.id, "full_name": st.full_name,
                              **res})
    # Lid bosqichi o'zgargan bo'lsa ham saqlaymiz - faollashish bo'lmasa
    # ham "sinovga keldi" belgisi yo'qolib qolmasligi kerak.
    if touched:
        db.commit()

    return {"ok": True, "saved": len(payload.marks), "activated": activated}


@app.get("/api/groups/{group_id}/grades", response_model=schemas.AttendanceGrid)
def grades_grid(
    group_id: int,
    year: int,
    month: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_ACCESS)),
):
    """Baholash jadvali - davomat bilan bir xil ko'rinish, lekin
    kataklarda 1-5 baho turadi."""
    _get_group_in_scope(db, group_id, user)
    students = _group_students(db, group_id)
    lessons = _group_lessons_in_month(db, group_id, year, month)
    lesson_ids = [ls.id for ls in lessons]

    marks = {}
    if lesson_ids:
        rows = db.query(models.DailyGrade).filter(
            models.DailyGrade.lesson_id.in_(lesson_ids)
        ).all()
        marks = {f"{g.lesson_id}:{g.student_id}": g.score for g in rows}

    return schemas.AttendanceGrid(
        students=[schemas.GridStudent(id=s.id, full_name=s.full_name,
                                      status=s.status) for s in students],
        lessons=[schemas.GridLesson(id=ls.id, date=ls.date, held=ls.held or 0)
                 for ls in lessons],
        marks=marks,
    )


@app.put("/api/lessons/{lesson_id}/grades")
def save_grades(
    lesson_id: int,
    payload: schemas.GradeBulk,
    db: Session = Depends(get_db),
    # Akademik baho - faqat o'qituvchilar tarkibi. Kassir yoki sotuv
    # menejeri davomatni ko'rishi mumkin, lekin bahoga tegmaydi.
    user=Depends(require_role(*roles.GRADE_EDIT)),
):
    """Bir darsning baholarini saqlaydi. Har bir baho uchun coin AVTOMAT
    yoziladi: 5 baho = 5 coin. Baho o'zgarsa coin ham o'zgaradi, olib
    tashlansa coin qaytariladi."""
    lesson = db.query(models.Lesson).get(lesson_id)
    if not lesson:
        raise HTTPException(404, "Dars topilmadi")
    _get_group_in_scope(db, lesson.group_id, user)

    for m in payload.marks:
        if m.score is not None and not (
            roles.DAILY_GRADE_MIN <= m.score <= roles.DAILY_GRADE_MAX
        ):
            raise HTTPException(
                400,
                f"Baho {roles.DAILY_GRADE_MIN}-{roles.DAILY_GRADE_MAX} "
                "oralig'ida bo'lishi kerak",
            )

    _mark_lesson_held(db, lesson)

    existing = {
        g.student_id: g
        for g in db.query(models.DailyGrade).filter(
            models.DailyGrade.lesson_id == lesson_id).all()
    }
    for m in payload.marks:
        row = existing.get(m.student_id)
        if m.score is None:
            if row:
                _drop_coin_entry(db, "daily", row.id)
                db.delete(row)
            continue
        if row:
            row.score = m.score
        else:
            row = models.DailyGrade(
                lesson_id=lesson_id, student_id=m.student_id,
                score=m.score, created_by=user.full_name)
            db.add(row)
            db.flush()  # coin yozuvi uchun id kerak
        _sync_coin_entry(
            db, student_id=m.student_id, source="daily", ref_id=row.id,
            amount=m.score,
            note=f"Kunlik baho {lesson.date.isoformat()}",
            created_by=user.full_name,
        )
    db.commit()
    return {"ok": True, "saved": len(payload.marks)}


# ------------------------------------------------------------ Imtihonlar ----
def _exam_in_scope(db: Session, exam_id: int, user: models.User) -> models.Exam:
    exam = db.query(models.Exam).get(exam_id)
    if not exam:
        raise HTTPException(404, "Imtihon topilmadi")
    _get_group_in_scope(db, exam.group_id, user)
    return exam


def _exam_summary(db: Session, exam: models.Exam) -> schemas.ExamOut:
    scored = [r for r in exam.results if r.percent is not None and not r.absent]
    return schemas.ExamOut(
        id=exam.id, group_id=exam.group_id, kind=exam.kind,
        unit_no=exam.unit_no, title=exam.title, date=exam.date,
        max_score=exam.max_score, created_by=exam.created_by,
        created_at=exam.created_at,
        result_count=len([r for r in exam.results if not r.absent]),
        avg_percent=round(sum(r.percent for r in scored) / len(scored), 1)
        if scored else None,
    )


@app.get("/api/groups/{group_id}/exams", response_model=List[schemas.ExamOut])
def list_exams(
    group_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_ACCESS)),
):
    _get_group_in_scope(db, group_id, user)
    exams = (
        db.query(models.Exam)
        .filter(models.Exam.group_id == group_id)
        .order_by(models.Exam.date.desc(), models.Exam.id.desc())
        .all()
    )
    return [_exam_summary(db, e) for e in exams]


@app.post("/api/groups/{group_id}/exams", response_model=schemas.ExamOut)
def create_exam(
    group_id: int,
    payload: schemas.ExamCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_ACCESS)),
):
    _get_group_in_scope(db, group_id, user)
    if payload.kind not in roles.EXAM_KINDS:
        raise HTTPException(400, "Noto'g'ri test turi")
    if payload.kind == "unit":
        if not payload.unit_no or not (1 <= payload.unit_no <= roles.UNIT_COUNT):
            raise HTTPException(
                400, f"Unit raqami 1-{roles.UNIT_COUNT} oralig'ida bo'lishi kerak")
    if payload.kind != "mock" and (not payload.max_score or payload.max_score <= 0):
        raise HTTPException(400, "Maksimal ballni kiriting")

    # Testni TASDIQLASH huquqi bor odam (examiner, asoschi) yaratsa -
    # darrov tasdiqlangan bo'ladi: u baribir keyingi bosishda tasdiqlar
    # edi. Ustoz yaratsa - qoralama bo'lib turadi va examiner ko'radi.
    approver = user.role in tuple(roles.EXAM_APPROVE)
    exam = models.Exam(
        group_id=group_id, kind=payload.kind,
        unit_no=payload.unit_no if payload.kind == "unit" else None,
        title=payload.title, date=payload.date,
        max_score=payload.max_score if payload.kind != "mock" else None,
        status="approved" if approver else "draft",
        approved_by=user.full_name if approver else None,
        approved_at=date.today() if approver else None,
        created_by=user.full_name,
    )
    db.add(exam)
    db.commit()
    db.refresh(exam)
    return _exam_summary(db, exam)


@app.get("/api/exams/{exam_id}", response_model=schemas.ExamDetail)
def get_exam(
    exam_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_ACCESS)),
):
    exam = _exam_in_scope(db, exam_id, user)
    base = _exam_summary(db, exam)
    students = _group_students(db, exam.group_id)
    return schemas.ExamDetail(
        **base.model_dump(),
        results=[schemas.ExamResultOut.model_validate(r) for r in exam.results],
        students=[schemas.GridStudent(id=s.id, full_name=s.full_name,
                                      status=s.status) for s in students],
    )


@app.delete("/api/exams/{exam_id}")
def delete_exam(
    exam_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FULL_ACCESS)),
):
    """Imtihon o'chirilsa, u bergan coinlar ham qaytariladi."""
    exam = _exam_in_scope(db, exam_id, user)
    for r in exam.results:
        _drop_coin_entry(db, "exam", r.id)
    db.delete(exam)
    db.commit()
    return {"ok": True}


@app.put("/api/exams/{exam_id}/results", response_model=schemas.ExamDetail)
def save_exam_results(
    exam_id: int,
    payload: schemas.ExamScoreBulk,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_ACCESS)),
):
    """Ustoz faqat ball (mock uchun band) kiritadi. Foiz avtomat
    hisoblanadi, coin ham qoidaga qarab avtomat beriladi.

    Natija kiritilishi bilan test "o'tkazildi" holatiga o'tadi."""
    exam = _exam_in_scope(db, exam_id, user)
    # Tasdiqlanmagan testga natija kiritilmaydi: aks holda kim nima
    # bilan baholaganini nazorat qilib bo'lmaydi.
    if (exam.status or "done") == "draft":
        raise HTTPException(
            400, "Bu test hali tasdiqlanmagan — avval Examiner tasdiqlashi kerak")
    if exam.status == "cancelled":
        raise HTTPException(400, "Bekor qilingan testga natija kiritilmaydi")
    existing = {r.student_id: r for r in exam.results}

    for m in payload.marks:
        row = existing.get(m.student_id)
        if row is None:
            row = models.ExamResult(exam_id=exam.id, student_id=m.student_id,
                                    created_by=user.full_name)
            db.add(row)
            db.flush()

        row.absent = 1 if m.absent else 0
        row.note = m.note

        if m.absent:
            row.score = None
            row.band = None
            row.percent = None
            row.coins = 0
            _drop_coin_entry(db, "exam", row.id)
            continue

        if exam.kind == "mock":
            if m.band is None:
                raise HTTPException(400, "Mock test uchun band kiriting (0-9)")
            if not (0 <= m.band <= roles.MOCK_MAX_BAND):
                raise HTTPException(400, "Band 0-9 oralig'ida bo'lishi kerak")
            row.band = m.band
            row.score = None
            row.percent = round(m.band / roles.MOCK_MAX_BAND * 100, 1)
        else:
            if m.score is None:
                raise HTTPException(400, "Ballni kiriting")
            if m.score < 0 or m.score > (exam.max_score or 0):
                raise HTTPException(
                    400, f"Ball 0 va {exam.max_score} oralig'ida bo'lishi kerak")
            row.score = m.score
            row.band = None
            row.percent = round(m.score / exam.max_score * 100, 1)

        row.coins = _coins_for_percent(db, row.percent, exam.kind)
        _sync_coin_entry(
            db, student_id=m.student_id, source="exam", ref_id=row.id,
            amount=row.coins,
            note=f"{roles.EXAM_KIND_LABELS.get(exam.kind, exam.kind)}"
                 f" - {row.percent}%",
            created_by=user.full_name,
        )

    if exam.status == "approved":
        exam.status = "done"
    db.commit()
    db.refresh(exam)
    base = _exam_summary(db, exam)
    students = _group_students(db, exam.group_id)
    return schemas.ExamDetail(
        **base.model_dump(),
        results=[schemas.ExamResultOut.model_validate(r) for r in exam.results],
        students=[schemas.GridStudent(id=s.id, full_name=s.full_name,
                                      status=s.status) for s in students],
    )


# ---------------------------------------------------------- Gamification ----
@app.get("/api/coins", response_model=List[schemas.CoinBalance])
def coin_leaderboard(
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_ACCESS)),
):
    """Coin reytingi - kim qancha yig'gan, qanchasini sarflagan."""
    students = scope_to_branch(
        db.query(models.Student), models.Student, user
    ).filter(models.Student.status != "archived").all()
    if not students:
        return []
    ids = [s.id for s in students]

    earned, spent = {}, {}
    rows = db.query(models.CoinEntry).filter(
        models.CoinEntry.student_id.in_(ids)).all()
    for e in rows:
        if e.amount >= 0:
            earned[e.student_id] = earned.get(e.student_id, 0) + e.amount
        else:
            spent[e.student_id] = spent.get(e.student_id, 0) - e.amount

    out = [
        schemas.CoinBalance(
            student_id=s.id, full_name=s.full_name,
            group=s.group.name if s.group else None,
            branch=s.branch.name if s.branch else None,
            earned=earned.get(s.id, 0), spent=spent.get(s.id, 0),
            balance=earned.get(s.id, 0) - spent.get(s.id, 0),
        )
        for s in students
    ]
    out.sort(key=lambda b: -b.balance)
    return out


@app.get("/api/students/{student_id}/lead")
def student_lead(
    student_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_STAFF)),
):
    """O'quvchi lidan aylangan bo'lsa - o'sha lidning tarixi.
    Qayerdan kelgani, kim olib kelgani shu yerda ko'rinadi."""
    lead = (
        db.query(models.Lead)
        .filter(models.Lead.converted_student_id == student_id)
        .first()
    )
    if not lead:
        return {"lead": None}
    return {"lead": {
        "id": lead.id,
        "source": lead.source,
        "stage": lead.stage,
        "address": lead.address,
        "school": lead.school,
        "grade": lead.grade,
        "note": lead.note,
        "assigned_user": lead.assigned_user.full_name if lead.assigned_user else None,
        "created_by": lead.created_by,
        "created_at": lead.created_at.isoformat() if lead.created_at else None,
        "updated_at": lead.updated_at.isoformat() if lead.updated_at else None,
    }}


@app.get("/api/students/{student_id}/exams")
def student_exams(
    student_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_STAFF)),
):
    """O'quvchining barcha imtihon natijalari - eng yangisi tepada."""
    rows = (
        db.query(models.ExamResult, models.Exam)
        .join(models.Exam, models.ExamResult.exam_id == models.Exam.id)
        .filter(models.ExamResult.student_id == student_id)
        .order_by(models.Exam.date.desc())
        .all()
    )
    groups = {g.id: g for g in db.query(models.Group).all()}
    out = []
    for r, e in rows:
        g = groups.get(e.group_id)
        out.append({
            "exam_id": e.id, "kind": e.kind, "unit_no": e.unit_no,
            "title": e.title, "date": e.date.isoformat(),
            "max_score": e.max_score,
            "group": g.name if g else None,
            "score": r.score, "band": r.band, "percent": r.percent,
            "coins": r.coins, "absent": bool(r.absent),
        })
    scored = [x for x in out if x["percent"] is not None]
    return {
        "results": out,
        "count": len(scored),
        "avg_percent": round(sum(x["percent"] for x in scored) / len(scored), 1)
        if scored else None,
        "coins": sum(x["coins"] or 0 for x in out),
    }


@app.get("/api/students/{student_id}/attendance")
def student_attendance(
    student_id: int,
    months: int = 6,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_STAFF)),
):
    """O'quvchining davomati va kunlik baholari - oxirgi N oy."""
    months = max(1, min(months, 24))
    today = date.today()
    sy, sm = _shift_month(today.year, today.month, -(months - 1))
    start, _ = billing.month_bounds(sy, sm)

    att = (
        db.query(models.Attendance, models.Lesson)
        .join(models.Lesson, models.Attendance.lesson_id == models.Lesson.id)
        .filter(models.Attendance.student_id == student_id,
                models.Lesson.date >= start)
        .order_by(models.Lesson.date.desc())
        .all()
    )
    grades = {
        g.lesson_id: g.score
        for g in db.query(models.DailyGrade).filter(
            models.DailyGrade.student_id == student_id).all()
    }

    rows = [{
        "date": ls.date.isoformat(),
        "present": bool(a.present),
        "grade": grades.get(ls.id),
    } for a, ls in att]

    present = sum(1 for r in rows if r["present"])
    scored = [r["grade"] for r in rows if r["grade"]]
    return {
        "rows": rows[:60],
        "marked": len(rows),
        "present": present,
        "absent": len(rows) - present,
        "percent": round(present / len(rows) * 100, 1) if rows else 0,
        "avg_grade": round(sum(scored) / len(scored), 1) if scored else None,
    }


@app.get("/api/students/{student_id}/coins", response_model=List[schemas.CoinEntryOut])
def student_coin_history(
    student_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_ACCESS)),
):
    return (
        db.query(models.CoinEntry)
        .filter(models.CoinEntry.student_id == student_id)
        .order_by(models.CoinEntry.created_at.desc(), models.CoinEntry.id.desc())
        .all()
    )


@app.post("/api/students/{student_id}/coins", response_model=schemas.CoinEntryOut)
def add_manual_coins(
    student_id: int,
    payload: schemas.CoinManual,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.COIN_ADMIN)),
):
    """Qo'lda coin berish yoki yechish (tanlov, tadbir, jarima va h.k.)."""
    s = db.query(models.Student).get(student_id)
    if not s:
        raise HTTPException(404, "O'quvchi topilmadi")
    if payload.amount == 0:
        raise HTTPException(400, "Miqdor 0 bo'lishi mumkin emas")
    entry = models.CoinEntry(student_id=student_id, amount=payload.amount,
                             source="manual", note=payload.note,
                             created_by=user.full_name)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@app.delete("/api/coins/{entry_id}")
def delete_coin_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.COIN_ADMIN)),
):
    """Faqat qo'lda kiritilgan yozuvni o'chirish mumkin - avtomatik
    yozuvlar o'z manbasidan (baho/imtihon) boshqariladi."""
    e = db.query(models.CoinEntry).get(entry_id)
    if not e:
        raise HTTPException(404, "Yozuv topilmadi")
    if e.source != "manual":
        raise HTTPException(
            400,
            "Bu yozuv avtomatik - uni o'zgartirish uchun tegishli bahoni "
            "yoki imtihon natijasini tahrirlang",
        )
    db.delete(e)
    db.commit()
    return {"ok": True}


@app.get("/api/exam-coin-rules", response_model=List[schemas.ExamCoinRuleOut])
def list_coin_rules(
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_ACCESS)),
):
    return db.query(models.ExamCoinRule).order_by(
        models.ExamCoinRule.min_percent.desc()).all()


@app.put("/api/exam-coin-rules", response_model=List[schemas.ExamCoinRuleOut])
def replace_coin_rules(
    payload: List[schemas.ExamCoinRuleIn],
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.COIN_ADMIN)),
):
    """Qoidalar jadvalini butunlay almashtiradi. Eski natijalarga
    ta'sir qilmaydi - faqat bundan keyin kiritiladigan natijalar yangi
    qoida bo'yicha hisoblanadi."""
    for r in payload:
        if r.kind and r.kind not in roles.EXAM_KINDS:
            raise HTTPException(400, "Noto'g'ri test turi")
        if r.coins < 0:
            raise HTTPException(400, "Coin manfiy bo'lmasligi kerak")
    db.query(models.ExamCoinRule).delete()
    for r in payload:
        db.add(models.ExamCoinRule(min_percent=r.min_percent, coins=r.coins,
                                   kind=r.kind))
    db.commit()
    return db.query(models.ExamCoinRule).order_by(
        models.ExamCoinRule.min_percent.desc()).all()


# ------------------------------------------------------------ Sovg'alar ----
@app.get("/api/rewards", response_model=List[schemas.RewardOut])
def list_rewards(
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_ACCESS)),
):
    q = scope_to_branch(db.query(models.Reward), models.Reward, user)
    return q.order_by(models.Reward.cost).all()


@app.post("/api/rewards", response_model=schemas.RewardOut)
def create_reward(
    payload: schemas.RewardCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.COIN_ADMIN)),
):
    if payload.cost <= 0:
        raise HTTPException(400, "Coin narxi 0 dan katta bo'lishi kerak")
    r = models.Reward(
        name=payload.name.strip(), cost=payload.cost,
        value_som=payload.value_som, stock=payload.stock,
        active=1 if payload.active else 0,
        branch_id=payload.branch_id if payload.branch_id is not None
        else user.branch_id,
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


@app.put("/api/rewards/{reward_id}", response_model=schemas.RewardOut)
def update_reward(
    reward_id: int,
    payload: schemas.RewardUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.COIN_ADMIN)),
):
    r = db.query(models.Reward).get(reward_id)
    if not r:
        raise HTTPException(404, "Sovg'a topilmadi")
    data = payload.model_dump(exclude_unset=True)
    if "cost" in data and data["cost"] is not None and data["cost"] <= 0:
        raise HTTPException(400, "Coin narxi 0 dan katta bo'lishi kerak")
    if "active" in data and data["active"] is not None:
        data["active"] = 1 if data["active"] else 0
    for k, v in data.items():
        setattr(r, k, v)
    db.commit()
    db.refresh(r)
    return r


@app.delete("/api/rewards/{reward_id}")
def delete_reward(
    reward_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.COIN_ADMIN)),
):
    r = db.query(models.Reward).get(reward_id)
    if not r:
        raise HTTPException(404, "Sovg'a topilmadi")
    used = db.query(models.RewardRedemption).filter(
        models.RewardRedemption.reward_id == reward_id).count()
    if used:
        # Tarixni buzmaslik uchun o'chirmaymiz, faqat yashiramiz.
        r.active = 0
        db.commit()
        return {"ok": True, "archived": True}
    db.delete(r)
    db.commit()
    return {"ok": True}


@app.post("/api/rewards/redeem", response_model=schemas.RedemptionOut)
def redeem_reward(
    payload: schemas.RedeemRequest,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_ACCESS)),
):
    """Coinni sovg'aga almashtirish. Balans yetmasa rad etiladi."""
    s = db.query(models.Student).get(payload.student_id)
    if not s:
        raise HTTPException(404, "O'quvchi topilmadi")
    r = db.query(models.Reward).get(payload.reward_id)
    if not r or not r.active:
        raise HTTPException(404, "Sovg'a topilmadi")
    if r.stock is not None and r.stock <= 0:
        raise HTTPException(400, "Bu sovg'a tugagan")

    balance = _student_coin_balance(db, s.id)
    if balance < r.cost:
        raise HTTPException(
            400, f"Coin yetarli emas: balans {balance}, kerak {r.cost}")

    red = models.RewardRedemption(student_id=s.id, reward_id=r.id,
                                  coins=r.cost, created_by=user.full_name)
    db.add(red)
    db.flush()
    db.add(models.CoinEntry(student_id=s.id, amount=-r.cost, source="reward",
                            ref_id=red.id, note=r.name,
                            created_by=user.full_name))
    if r.stock is not None:
        r.stock -= 1
    db.commit()
    db.refresh(red)
    return red


@app.delete("/api/rewards/redemptions/{redemption_id}")
def cancel_redemption(
    redemption_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.COIN_ADMIN)),
):
    """Xato berilgan sovg'ani bekor qilish - coin o'quvchiga qaytariladi
    va zaxira tiklanadi."""
    red = db.query(models.RewardRedemption).get(redemption_id)
    if not red:
        raise HTTPException(404, "Yozuv topilmadi")
    _drop_coin_entry(db, "reward", red.id)
    reward = db.query(models.Reward).get(red.reward_id)
    if reward and reward.stock is not None:
        reward.stock += 1
    db.delete(red)
    db.commit()
    return {"ok": True}


@app.get("/api/rewards/redemptions", response_model=List[schemas.RedemptionOut])
def list_redemptions(
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_ACCESS)),
):
    q = db.query(models.RewardRedemption).join(models.Student)
    if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
        q = q.filter(models.Student.branch_id == user.branch_id)
    return q.order_by(models.RewardRedemption.created_at.desc()).limit(200).all()


# ------------------------------------------------------------ Hisobotlar ----
# Barcha moliyaviy hisobotlar bitta manbadan oziqlanadi, shuning uchun
# Dashboard'dagi "shu oy tushum" bilan P&L'dagi "kirim" har doim bir xil
# chiqadi. Kirim = kind="payment" bo'lgan yozuvlar (hisoblangan charge
# emas - u pul emas, qarz).


def _period_key(year: int, month: int) -> str:
    return f"{year:04d}-{month:02d}"


def _shift_month(year: int, month: int, delta: int) -> tuple:
    idx = (year * 12 + (month - 1)) + delta
    return idx // 12, idx % 12 + 1


def _income_by_method(db: Session, user, start: date, end: date,
                      branch_id=None) -> dict:
    """Bir oraliqdagi haqiqiy tushumni to'lov usuli kesimida qaytaradi."""
    q = db.query(models.Payment).join(models.Student).filter(
        models.Payment.kind == "payment",
        models.Payment.created_at >= datetime.combine(start, datetime.min.time()),
        models.Payment.created_at <= datetime.combine(end, datetime.max.time()),
    )
    if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
        q = q.filter(models.Student.branch_id == user.branch_id)
    elif branch_id:
        q = q.filter(models.Student.branch_id == branch_id)

    out = {m: 0.0 for m in roles.PAYMENT_METHODS}
    for p in q.all():
        # Usul belgilanmasdan oldin kiritilgan eski to'lovlar naqd deb
        # hisoblanadi - aks holda ular hisobotdan tushib qolardi.
        out[p.method if p.method in out else "cash"] += p.amount
    return out


def _expenses_total(db: Session, user, start: date, end: date,
                    branch_id=None) -> tuple:
    """(jami, tur bo'yicha lug'at) qaytaradi."""
    q = scope_to_branch(db.query(models.Expense), models.Expense, user,
                        branch_id).filter(
        models.Expense.date >= start, models.Expense.date <= end
    )
    by_cat, total = {}, 0.0
    for e in q.all():
        by_cat[e.category] = by_cat.get(e.category, 0) + e.amount
        total += e.amount
    return total, by_cat


def _payroll_total(db: Session, user, period: str, branch_id=None) -> float:
    """Ustozlar ish haqi - TeacherPayout jadvalidan AVTOMATIK olinadi.
    Uni Xarajatlar bo'limiga qo'lda kiritish shart emas (va kiritilmasligi
    ham kerak - aks holda ikki marta hisoblanadi)."""
    q = db.query(models.TeacherPayout).filter(models.TeacherPayout.period == period)
    if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
        q = q.join(models.Group).filter(models.Group.branch_id == user.branch_id)
    elif branch_id:
        q = q.join(models.Group).filter(models.Group.branch_id == branch_id)
    return sum(p.amount or 0 for p in q.all())


@app.get("/api/reports/cashflow")
def report_cashflow(
    months: int = 6,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FINANCE_ACCESS)),
):
    """Oxirgi N oy uchun pul oqimi: qancha kirdi (naqd/plastik/terminal
    kesimida), qancha chiqdi (xarajat + ustozlar ish haqi), sof qoldiq."""
    months = max(1, min(months, 24))
    today = date.today()
    rows = []
    for back in range(months - 1, -1, -1):
        y, m = _shift_month(today.year, today.month, -back)
        start, end = billing.month_bounds(y, m)
        period = _period_key(y, m)

        methods = _income_by_method(db, user, start, end)
        income = sum(methods.values())
        exp_total, _ = _expenses_total(db, user, start, end)
        payroll = _payroll_total(db, user, period)

        rows.append({
            "period": period,
            "cash": methods["cash"],
            "card": methods["card"],
            "terminal": methods["terminal"],
            "other": methods["other"],
            "income": income,
            "expenses": exp_total,
            "payroll": payroll,
            "outflow": exp_total + payroll,
            "net": income - exp_total - payroll,
        })

    keys = ["cash", "card", "terminal", "other", "income",
            "expenses", "payroll", "outflow", "net"]
    return {"rows": rows, "totals": {k: sum(r[k] for r in rows) for k in keys}}


@app.get("/api/reports/pnl")
def report_pnl(
    year: int,
    month: int,
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FINANCE_ACCESS)),
):
    """Bir oylik foyda-zarar. Chiqim = qo'lda kiritilgan xarajatlar +
    avtomatik hisoblangan ustozlar ish haqi."""
    start, end = billing.month_bounds(year, month)
    period = _period_key(year, month)

    methods = _income_by_method(db, user, start, end, branch_id)
    income = sum(methods.values())
    exp_total, by_cat = _expenses_total(db, user, start, end, branch_id)
    payroll = _payroll_total(db, user, period, branch_id)
    profit = income - exp_total - payroll

    lines = [{"category": c, "amount": a, "auto": False}
             for c, a in sorted(by_cat.items(), key=lambda kv: -kv[1])]
    if payroll:
        # "auto" - bu qatorni qo'lda kiritish shart emasligini bildiradi.
        lines.append({"category": "teacher_payroll", "amount": payroll, "auto": True})

    return {
        "period": period,
        "income": income,
        "income_by_method": methods,
        "expense_lines": lines,
        "expenses_total": exp_total,
        "payroll_total": payroll,
        "outflow_total": exp_total + payroll,
        "profit": profit,
        "margin": round(profit / income * 100, 1) if income else 0,
    }


# --------------------------------------------------- Ustozlar oyligi ----
@app.get("/api/reports/teacher-payroll")
def report_teacher_payroll(
    year: int,
    month: int,
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FINANCE_ACCESS, *roles.SALARY_VIEW_ALL,
                              roles.TEACHER)),
):
    """Bir oylik ustozlar ish haqi - ustoz kesimida jamlangan.
    Manba: guruhlarda hisoblangan TeacherPayout yozuvlari."""
    period = _period_key(year, month)
    q = db.query(models.TeacherPayout).filter(models.TeacherPayout.period == period)
    if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
        q = q.join(models.Group).filter(models.Group.branch_id == user.branch_id)

    # O'qituvchi faqat O'ZINING oyligini ko'radi - hamkasbining maoshi
    # unga ko'rinmaydi.
    own_only = user.role not in tuple(roles.FINANCE_ACCESS + roles.SALARY_VIEW_ALL)
    if own_only:
        me = (db.query(models.Teacher)
              .filter(models.Teacher.full_name == user.full_name).first())
        if not me:
            return {"period": period, "rows": [], "teacher_count": 0,
                    "total": 0.0, "paid": 0.0, "unpaid": 0.0,
                    "own_only": True}
        q = q.filter(models.TeacherPayout.teacher_id == me.id)

    payouts = q.all()

    teachers = {t.id: t for t in db.query(models.Teacher).all()}
    groups = {g.id: g for g in db.query(models.Group).all()}

    by_teacher = {}
    for p in payouts:
        row = by_teacher.setdefault(p.teacher_id, {
            "teacher_id": p.teacher_id,
            "full_name": teachers[p.teacher_id].full_name
            if p.teacher_id in teachers else "—",
            "branch": (teachers[p.teacher_id].branch.name
                       if p.teacher_id in teachers and teachers[p.teacher_id].branch
                       else None),
            "groups": [], "students": 0, "lessons": 0,
            "amount": 0.0, "paid_amount": 0.0,
        })
        row["groups"].append({
            "group_id": p.group_id,
            "group": groups[p.group_id].name if p.group_id in groups else "—",
            "students": p.student_count,
            "held_lessons": p.held_lessons,
            "taught_lessons": p.taught_lessons,
            "amount": p.amount,
            "paid": bool(p.paid),
            "payout_id": p.id,
        })
        row["students"] += p.student_count
        row["lessons"] += p.taught_lessons
        row["amount"] += p.amount or 0
        if p.paid:
            row["paid_amount"] += p.amount or 0

    rows = sorted(by_teacher.values(), key=lambda r: -r["amount"])
    total = sum(r["amount"] for r in rows)
    paid = sum(r["paid_amount"] for r in rows)
    return {
        "period": period,
        "rows": rows,
        "total": total,
        "paid": paid,
        "unpaid": total - paid,
        "own_only": own_only,
        "teacher_count": len(rows),
    }


# -------------------------------------------------------- Sotuv voronkasi ----
@app.get("/api/reports/funnel")
def report_funnel(
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FINANCE_ACCESS)),
):
    """Ikki qismli voronka:

    1) Lid bosqichlari - so'rov kelganidan o'quvchiga aylangunicha qayerda
       yo'qotilyapti.
    2) To'lovdan keyingi oylar - 1-oy, 2-oy ... 12-oy. Qaysi oyda eng ko'p
       o'quvchi ketayotgani shu yerda ko'rinadi.
    """
    # ---- 1. Lid voronkasi -------------------------------------------------
    leads = scope_to_branch(db.query(models.Lead), models.Lead, user, branch_id).all()
    by_stage = {st: 0 for st in roles.LEAD_STAGES}
    for l in leads:
        if l.stage in by_stage:
            by_stage[l.stage] += 1

    total_leads = len(leads)
    # Voronka kümülativ: keyingi bosqichga o'tganlar oldingisini ham bosib
    # o'tgan hisoblanadi.
    order = roles.LEAD_FUNNEL_ORDER
    stages = []
    remaining = total_leads
    for i, st in enumerate(order):
        reached = sum(by_stage[s] for s in order[i:])
        stages.append({
            "stage": st,
            "reached": reached,
            "here_now": by_stage[st],
            "percent": round(reached / total_leads * 100, 1) if total_leads else 0,
            "lost_here": by_stage[st] if st != "converted" else 0,
        })
        remaining = reached
    rejected = by_stage.get("rejected", 0)

    # ---- 2. To'lovdan keyingi oylar --------------------------------------
    students = scope_to_branch(db.query(models.Student), models.Student, user, branch_id).all()
    first_paid = _first_payment_dates(db)
    today = date.today()

    lives = []
    for s in students:
        first = first_paid.get(s.id)
        if not first:
            continue  # hali to'lamagan - voronkaning bu qismiga kirmaydi
        start = first.date()
        end = s.left_date or today
        lives.append({
            "months": _months_between(start, end),
            "churned": s.left_date is not None,
        })

    months = []
    for n in range(1, 13):
        # Natijasi ma'lum bo'lganlar: yo shu oyga yetgan, yo undan oldin ketgan
        survived = sum(1 for l in lives if l["months"] >= n)
        known_lost = sum(1 for l in lives if l["churned"] and l["months"] < n)
        eligible = survived + known_lost
        lost_here = sum(
            1 for l in lives
            if l["churned"] and (n - 1) <= l["months"] < n
        )
        months.append({
            "month": n,
            "eligible": eligible,
            "survived": survived,
            "retention": round(survived / eligible * 100, 1) if eligible else 0,
            "lost": lost_here,
        })

    worst = max(months, key=lambda m: m["lost"]) if months else None
    return {
        "leads": {
            "total": total_leads,
            "stages": stages,
            "rejected": rejected,
        },
        "students": {
            "paying": len(lives),
            "churned": sum(1 for l in lives if l["churned"]),
            "months": months,
            # Eng ko'p o'quvchi yo'qotiladigan oy - asosiy savolga javob
            "worst_month": worst["month"] if worst and worst["lost"] else None,
            "worst_month_lost": worst["lost"] if worst else 0,
        },
    }


# ------------------------------------------------------- Ta'lim sifati ----
@app.get("/api/reports/quality")
def report_quality(
    year: int,
    month: int,
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FINANCE_ACCESS)),
):
    """Ta'lim sifati - imtihon natijalaridan chiqadi.

    Guruh reytingi = shu oydagi imtihonlardagi o'rtacha foiz.
    Ustoz reytingi = uning guruhlari o'rtachasi.
    Filial reytingi = filialdagi guruhlar o'rtachasi.
    Markaz reytingi = hamma guruhlar o'rtachasi.

    Guruhlar teng vaznda olinadi (kattaligiga qarab emas) - aks holda
    bitta katta guruh butun ko'rsatkichni belgilab qo'yardi."""
    start, end = billing.month_bounds(year, month)

    exams = db.query(models.Exam).filter(
        models.Exam.date >= start, models.Exam.date <= end
    ).all()
    groups = {g.id: g for g in scope_to_branch(
        db.query(models.Group), models.Group, user, branch_id).all()}
    teachers = {t.id: t for t in db.query(models.Teacher).all()}
    branches = {b.id: b for b in db.query(models.Branch).all()}

    # Guruh -> natijalar
    per_group = {}
    for e in exams:
        g = groups.get(e.group_id)
        if not g:
            continue
        scored = [r for r in e.results if r.percent is not None and not r.absent]
        if not scored:
            continue
        row = per_group.setdefault(g.id, {
            "group_id": g.id, "group": g.name,
            "subject": g.subject, "level": g.level,
            "teacher_id": g.teacher_id,
            "teacher": teachers[g.teacher_id].full_name
            if g.teacher_id in teachers else None,
            "branch_id": g.branch_id,
            "branch": branches[g.branch_id].name
            if g.branch_id in branches else None,
            "exams": 0, "results": 0, "sum": 0.0,
        })
        row["exams"] += 1
        row["results"] += len(scored)
        row["sum"] += sum(r.percent for r in scored)

    group_rows = []
    for r in per_group.values():
        group_rows.append({**{k: v for k, v in r.items() if k != "sum"},
                           "avg": round(r["sum"] / r["results"], 1)})
    group_rows.sort(key=lambda r: -r["avg"])

    def rollup(key_id, key_name):
        acc = {}
        for r in group_rows:
            k = r[key_id]
            if k is None:
                continue
            a = acc.setdefault(k, {"id": k, "name": r[key_name],
                                   "groups": 0, "sum": 0.0, "exams": 0})
            a["groups"] += 1
            a["sum"] += r["avg"]
            a["exams"] += r["exams"]
        out = [{"id": a["id"], "name": a["name"], "groups": a["groups"],
                "exams": a["exams"], "avg": round(a["sum"] / a["groups"], 1)}
               for a in acc.values()]
        out.sort(key=lambda x: -x["avg"])
        return out

    centre = (round(sum(r["avg"] for r in group_rows) / len(group_rows), 1)
              if group_rows else None)

    return {
        "period": _period_key(year, month),
        "centre": {
            "avg": centre,
            "groups": len(group_rows),
            "exams": sum(r["exams"] for r in group_rows),
            "results": sum(r["results"] for r in group_rows),
        },
        "branches": rollup("branch_id", "branch"),
        "teachers": rollup("teacher_id", "teacher"),
        "groups": group_rows,
    }


# ------------------------------------------------ Sotuv menejerlari ----
@app.get("/api/reports/sales-managers")
def report_sales_managers(
    window: str = "month",
    year: int = None,
    month: int = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FINANCE_ACCESS)),
):
    """Har bir sotuv menejerining sotuv foizi.

    Foiz = o'quvchiga aylangan lidlar / unga biriktirilgan lidlar.
    Davr: oy / 3 oy / 6 oy / 1 yil / butun davr - lid yaratilgan
    sanaga qarab."""
    today = date.today()
    if window == "month":
        y = year or today.year
        m = month or today.month
        start, end = billing.month_bounds(y, m)
        label = _period_key(y, m)
    elif window in ("3m", "6m", "1y"):
        back = {"3m": 3, "6m": 6, "1y": 12}[window]
        sy, sm = _shift_month(today.year, today.month, -(back - 1))
        start, _ = billing.month_bounds(sy, sm)
        end = today
        label = f"{_period_key(sy, sm)} … {_period_key(today.year, today.month)}"
    elif window == "all":
        start, end, label = date(2000, 1, 1), today, "Butun davr"
    else:
        raise HTTPException(400, "Noto'g'ri davr")

    start_dt = datetime.combine(start, datetime.min.time())
    end_dt = datetime.combine(end, datetime.max.time())

    managers = db.query(models.User).filter(
        models.User.role == roles.SALES_MANAGER)
    if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
        managers = managers.filter(models.User.branch_id == user.branch_id)
    managers = managers.order_by(models.User.full_name).all()

    leads = scope_to_branch(db.query(models.Lead), models.Lead, user).filter(
        models.Lead.created_at >= start_dt,
        models.Lead.created_at <= end_dt,
    ).all()

    by_user = {}
    for l in leads:
        row = by_user.setdefault(l.assigned_user_id, {
            "total": 0, "converted": 0, "rejected": 0, "in_progress": 0})
        row["total"] += 1
        if l.converted_student_id or l.stage == "converted":
            row["converted"] += 1
        elif l.stage == "rejected":
            row["rejected"] += 1
        else:
            row["in_progress"] += 1

    rows = []
    for m_ in managers:
        st = by_user.get(m_.id, {"total": 0, "converted": 0,
                                 "rejected": 0, "in_progress": 0})
        rows.append({
            "user_id": m_.id,
            "full_name": m_.full_name,
            "branch": m_.branch.name if m_.branch else None,
            "active": bool(m_.is_active),
            "leads": st["total"],
            "converted": st["converted"],
            "rejected": st["rejected"],
            "in_progress": st["in_progress"],
            "conversion": round(st["converted"] / st["total"] * 100, 1)
            if st["total"] else 0,
        })
    rows.sort(key=lambda r: (-r["conversion"], -r["converted"]))

    # Biriktirilmagan lidlar - ular hech kimning ko'rsatkichiga kirmaydi,
    # lekin ko'rinib turishi kerak.
    un = by_user.get(None, {"total": 0, "converted": 0})
    total_leads = sum(r["leads"] for r in rows) + un["total"]
    total_conv = sum(r["converted"] for r in rows) + un["converted"]

    return {
        "window": window,
        "label": label,
        "rows": rows,
        "unassigned": un["total"],
        "totals": {
            "leads": total_leads,
            "converted": total_conv,
            "conversion": round(total_conv / total_leads * 100, 1)
            if total_leads else 0,
        },
    }


# ---------------------------------------------------------- Analitika ----
@app.get("/api/analytics/summary")
def analytics_summary(
    months: int = 12,
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FINANCE_ACCESS)),
):
    """Analitika sahifasi uchun bitta so'rovda hamma raqam:
    oylik kirim/chiqim/foyda, xarajat guruhlari, ustozlar ulushi."""
    # 0 -> butun davr (eng eski yozuvdan bugungacha)
    if months == 0:
        oldest = db.query(func.min(models.Payment.created_at)).scalar()
        oldest_e = db.query(func.min(models.Expense.date)).scalar()
        t = date.today()
        cands = [x.date() if hasattr(x, "date") else x
                 for x in [oldest, oldest_e] if x]
        first = min(cands) if cands else t
        months = max(1, (t.year - first.year) * 12 + (t.month - first.month) + 1)
    months = max(1, min(months, 120))
    today = date.today()

    monthly = []
    group_totals = {}
    category_totals = {}

    for back in range(months - 1, -1, -1):
        y, m = _shift_month(today.year, today.month, -back)
        start, end = billing.month_bounds(y, m)
        period = _period_key(y, m)

        income = sum(_income_by_method(db, user, start, end, branch_id).values())
        exp_total, by_cat = _expenses_total(db, user, start, end, branch_id)
        payroll = _payroll_total(db, user, period, branch_id)

        for cat, amt in by_cat.items():
            category_totals[cat] = category_totals.get(cat, 0) + amt
            grp = roles.EXPENSE_CATEGORY_GROUP.get(cat, "other")
            group_totals[grp] = group_totals.get(grp, 0) + amt
        if payroll:
            group_totals["teacher_salary"] = (
                group_totals.get("teacher_salary", 0) + payroll)

        outflow = exp_total + payroll
        monthly.append({
            "period": period,
            "income": income,
            "expenses": exp_total,
            "payroll": payroll,
            "outflow": outflow,
            "profit": income - outflow,
            # Ustozlarning ulushi - kirimning necha foizi ish haqiga ketdi
            "teacher_share": round(payroll / income * 100, 1) if income else 0,
        })

    total_income = sum(m["income"] for m in monthly)
    total_payroll = sum(m["payroll"] for m in monthly)
    total_expenses = sum(m["expenses"] for m in monthly)
    total_profit = total_income - total_payroll - total_expenses

    groups = sorted(
        [{"key": k, "label": roles.EXPENSE_GROUP_LABELS.get(k, k), "amount": v}
         for k, v in group_totals.items() if v > 0],
        key=lambda g: -g["amount"],
    )
    categories = sorted(
        [{"key": k, "label": roles.EXPENSE_CATEGORY_LABELS.get(k, k),
          "group": roles.EXPENSE_CATEGORY_GROUP.get(k, "other"), "amount": v}
         for k, v in category_totals.items() if v > 0],
        key=lambda c: -c["amount"],
    )

    return {
        "months": monthly,
        "expense_groups": groups,
        "expense_categories": categories,
        "totals": {
            "income": total_income,
            "expenses": total_expenses,
            "payroll": total_payroll,
            "outflow": total_payroll + total_expenses,
            "profit": total_profit,
            "margin": round(total_profit / total_income * 100, 1)
            if total_income else 0,
            "teacher_share": round(total_payroll / total_income * 100, 1)
            if total_income else 0,
        },
    }


# ------------------------------------------------------- Adminlar KPI ----
# Admin ish haqi = fiks oylik + eski to'lovlarni yig'ish bonusi +
# yangi mijoz bonusi. Bonuslar FILIAL ko'rsatkichi bo'yicha: bir filialda
# ikkita admin bo'lsa, ikkalasi ham to'liq bonusni oladi.


def _first_payment_dates(db: Session) -> dict:
    """Har bir o'quvchining eng birinchi to'lov sanasi. Shu sana orqali
    to'lov "yangi" (birinchi marta) yoki "eski" ekani aniqlanadi."""
    rows = (
        db.query(models.Payment.student_id,
                 func.min(models.Payment.created_at))
        .filter(models.Payment.kind == "payment")
        .group_by(models.Payment.student_id)
        .all()
    )
    return {sid: dt for sid, dt in rows}


def _collection_bonus(db: Session, students: int, percent: float) -> float:
    """Filialdagi FAOL o'quvchi soni va yig'ish foiziga mos eng katta
    bonus. Hech qanday qator to'g'ri kelmasa - 0 (masalan 50 tagacha
    o'quvchida bonus yo'q)."""
    best = 0.0
    for r in db.query(models.KpiCollectionRule).all():
        if students < r.min_students:
            continue
        if r.max_students is not None and students > r.max_students:
            continue
        if percent + 1e-9 < r.min_percent:
            continue
        best = max(best, r.bonus)
    return best


def _new_client_bonus(db: Session, count: int) -> float:
    """Yangi mijozlar soniga mos eng yuqori pog'ona bonusi."""
    best = 0.0
    for r in db.query(models.KpiNewClientRule).all():
        if count >= r.min_clients:
            best = max(best, r.bonus)
    return best


@app.get("/api/kpi/admins", response_model=schemas.AdminKpiResult)
def admin_kpi(
    year: int,
    month: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.KPI_VIEW)),
):
    start, end = billing.month_bounds(year, month)
    period = _period_key(year, month)
    start_dt = datetime.combine(start, datetime.min.time())
    end_dt = datetime.combine(end, datetime.max.time())

    admins = db.query(models.User).filter(
        models.User.role == roles.SALES_MANAGER,
        models.User.is_active == 1,
    )
    if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
        admins = admins.filter(models.User.branch_id == user.branch_id)
    admins = admins.order_by(models.User.full_name).all()
    if not admins:
        return schemas.AdminKpiResult(period=period, rows=[])

    first_paid = _first_payment_dates(db)
    students = db.query(models.Student).all()
    student_branch = {s.id: s.branch_id for s in students}

    # Filial ko'rsatkichlarini bir marta hisoblaymiz.
    stats = {}
    for a in admins:
        if a.branch_id in stats:
            continue
        stats[a.branch_id] = {
            "active_students": sum(
                1 for s in students
                if s.branch_id == a.branch_id and s.status == "active"),
            "expected": 0.0, "collected": 0.0,
            "new_clients": set(), "new_revenue": 0.0,
        }

    # "Tushishi kerak" bo'lgan pul - shu oyda hisoblangan summalar.
    # Faqat ESKI o'quvchilar bo'yicha: yangi mijozning birinchi to'lovi
    # yig'ish foiziga kirmaydi, u alohida bonus bilan baholanadi.
    charges = db.query(models.Payment).filter(
        models.Payment.kind == "charge",
        models.Payment.created_at >= start_dt,
        models.Payment.created_at <= end_dt,
    ).all()
    for c in charges:
        st = stats.get(student_branch.get(c.student_id))
        if st is None:
            continue
        first = first_paid.get(c.student_id)
        if first is None or first >= start_dt:
            continue  # hali to'lamagan yoki yangi mijoz
        st["expected"] += abs(c.amount)

    # Haqiqatda tushgan pul.
    pays = db.query(models.Payment).filter(
        models.Payment.kind == "payment",
        models.Payment.created_at >= start_dt,
        models.Payment.created_at <= end_dt,
    ).all()
    for p in pays:
        st = stats.get(student_branch.get(p.student_id))
        if st is None:
            continue
        first = first_paid.get(p.student_id)
        if first is not None and first >= start_dt:
            # Birinchi marta to'lagan - yangi mijoz
            st["new_clients"].add(p.student_id)
            st["new_revenue"] += p.amount
        else:
            st["collected"] += p.amount

    rows = []
    for a in admins:
        st = stats[a.branch_id]
        pct = (round(st["collected"] / st["expected"] * 100, 1)
               if st["expected"] else 0.0)
        col_bonus = _collection_bonus(db, st["active_students"], pct)
        new_count = len(st["new_clients"])
        new_bonus = _new_client_bonus(db, new_count)
        fix = a.fix_salary or 0.0

        rows.append(schemas.AdminKpi(
            user_id=a.id, full_name=a.full_name, branch_id=a.branch_id,
            branch=a.branch.name if a.branch else None,
            fix_salary=fix,
            active_students=st["active_students"],
            expected=st["expected"], collected=st["collected"],
            collection_percent=pct, collection_bonus=col_bonus,
            new_clients=new_count, new_client_revenue=st["new_revenue"],
            new_client_bonus=new_bonus,
            total=fix + col_bonus + new_bonus,
        ))
    return schemas.AdminKpiResult(period=period, rows=rows)


@app.get("/api/kpi/rules", response_model=schemas.KpiRules)
def get_kpi_rules(
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.KPI_VIEW)),
):
    return schemas.KpiRules(
        collection=db.query(models.KpiCollectionRule).order_by(
            models.KpiCollectionRule.min_students,
            models.KpiCollectionRule.min_percent.desc()).all(),
        new_clients=db.query(models.KpiNewClientRule).order_by(
            models.KpiNewClientRule.min_clients).all(),
    )


@app.put("/api/kpi/rules", response_model=schemas.KpiRules)
def replace_kpi_rules(
    payload: schemas.KpiRulesIn,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.KPI_ADMIN)),
):
    """Qoidalar jadvalini almashtiradi. Faqat asoschi - bu bevosita
    xodimlarning ish haqiga ta'sir qiladi."""
    for r in payload.collection:
        if r.bonus < 0 or not (0 <= r.min_percent <= 100):
            raise HTTPException(400, "Noto'g'ri qiymat")
        if r.max_students is not None and r.max_students < r.min_students:
            raise HTTPException(
                400, "Yuqori chegara quyi chegaradan kichik bo'lmasligi kerak")
    for r in payload.new_clients:
        if r.bonus < 0 or r.min_clients < 0:
            raise HTTPException(400, "Noto'g'ri qiymat")

    db.query(models.KpiCollectionRule).delete()
    db.query(models.KpiNewClientRule).delete()
    for r in payload.collection:
        db.add(models.KpiCollectionRule(
            min_students=r.min_students, max_students=r.max_students,
            min_percent=r.min_percent, bonus=r.bonus))
    for r in payload.new_clients:
        db.add(models.KpiNewClientRule(min_clients=r.min_clients, bonus=r.bonus))
    db.commit()
    return get_kpi_rules(db, user)


@app.get("/api/reports/ltv")
def report_ltv(
    dimension: str = "branch",
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FINANCE_ACCESS)),
):
    """LTV - bitta mijoz o'rtacha qancha vaqt qoladi va shu vaqt ichida
    qancha pul olib keladi. Kesim: filial / ustoz / guruh.

    Ustoz va guruh kesimi o'quvchining HOZIRGI guruhiga qarab bo'linadi -
    guruh almashtirgan o'quvchi oxirgi guruhiga yoziladi."""
    if dimension not in ("branch", "teacher", "group"):
        raise HTTPException(400, "Noto'g'ri kesim")

    students = scope_to_branch(
        db.query(models.Student), models.Student, user
    ).all()
    if not students:
        return {"dimension": dimension, "rows": [], "overall": None}

    # Har bir o'quvchining haqiqiy to'lovlari (charge emas) bir so'rovda.
    paid_rows = db.query(
        models.Payment.student_id, func.sum(models.Payment.amount)
    ).filter(models.Payment.kind == "payment").group_by(
        models.Payment.student_id
    ).all()
    paid = {sid: amt or 0 for sid, amt in paid_rows}

    groups = {g.id: g for g in db.query(models.Group).all()}
    teachers = {t.id: t for t in db.query(models.Teacher).all()}
    branches = {b.id: b for b in db.query(models.Branch).all()}
    today = date.today()

    buckets = {}
    for s in students:
        if dimension == "branch":
            key = s.branch_id
            label = branches[key].name if key in branches else "Filialsiz"
        elif dimension == "group":
            key = s.group_id
            label = groups[key].name if key in groups else "Guruhsiz"
        else:
            g = groups.get(s.group_id)
            key = g.teacher_id if g else None
            label = teachers[key].full_name if key in teachers else "Ustoz biriktirilmagan"

        b = buckets.setdefault(str(key), {
            "key": key, "label": label, "students": 0, "left": 0,
            "total_revenue": 0.0, "total_months": 0.0,
        })
        b["students"] += 1
        b["total_revenue"] += paid.get(s.id, 0)
        b["total_months"] += _months_between(
            s.enrolled_date or today, s.left_date or today
        )
        if s.left_date:
            b["left"] += 1

    rows = []
    for b in buckets.values():
        n = b["students"] or 1
        rows.append({
            "key": b["key"],
            "label": b["label"],
            "students": b["students"],
            "left": b["left"],
            "avg_months": round(b["total_months"] / n, 1),
            "avg_revenue": round(b["total_revenue"] / n),
            "total_revenue": b["total_revenue"],
            # Ketganlar ulushi - qaysi filial/ustozda mijoz ko'proq
            # to'xtab qolayotgani darrov ko'rinsin.
            "churn": round(b["left"] / n * 100, 1),
        })
    rows.sort(key=lambda r: -r["avg_revenue"])

    total_students = sum(r["students"] for r in rows) or 1
    overall = {
        "students": sum(r["students"] for r in rows),
        "left": sum(r["left"] for r in rows),
        "avg_months": round(
            sum(r["avg_months"] * r["students"] for r in rows) / total_students, 1),
        "avg_revenue": round(
            sum(r["total_revenue"] for r in rows) / total_students),
        "total_revenue": sum(r["total_revenue"] for r in rows),
    }
    return {"dimension": dimension, "rows": rows, "overall": overall}


@app.get("/api/reports/teacher-retention")
def report_teacher_retention(
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FINANCE_ACCESS)),
):
    """Ustozlar qancha vaqt ishlab turadi. Ishga kirgan sana ustoz
    yaratilganda avtomatik qo'yiladi, ketgan sana esa "ishlamaydi" deb
    belgilanganda."""
    teachers = scope_to_branch(
        db.query(models.Teacher), models.Teacher, user
    ).all()
    today = date.today()
    year_ago = today - timedelta(days=365)

    rows = []
    for t in teachers:
        hired = t.hired_date or (t.created_at.date() if t.created_at else today)
        rows.append({
            "id": t.id,
            "full_name": t.full_name,
            "branch": t.branch.name if t.branch else None,
            "hired_date": hired.isoformat(),
            "left_date": t.left_date.isoformat() if t.left_date else None,
            "active": bool(t.is_active),
            "months": _months_between(hired, t.left_date or today),
        })
    rows.sort(key=lambda r: -r["months"])

    active = [r for r in rows if r["active"]]
    left = [r for r in rows if not r["active"]]
    # Oxirgi 12 oyda ketganlar / davr boshidagi jamoa hajmi.
    left_12m = [r for r in left if r["left_date"] and r["left_date"] >= year_ago.isoformat()]
    base = len(active) + len(left_12m)

    return {
        "rows": rows,
        "summary": {
            "active": len(active),
            "left": len(left),
            "left_last_12m": len(left_12m),
            "avg_tenure_active": round(
                sum(r["months"] for r in active) / len(active), 1) if active else 0,
            "avg_tenure_left": round(
                sum(r["months"] for r in left) / len(left), 1) if left else 0,
            "turnover_12m": round(len(left_12m) / base * 100, 1) if base else 0,
        },
    }


# ------------------------------------------------------------ Teachers ----
@app.get("/api/teachers", response_model=List[schemas.TeacherOut])
def list_teachers(db: Session = Depends(get_db), user=Depends(get_current_user)):
    q = scope_to_branch(db.query(models.Teacher), models.Teacher, user)
    return q.order_by(models.Teacher.full_name).all()


@app.post("/api/teachers", response_model=schemas.TeacherOut)
def create_teacher(
    payload: schemas.TeacherCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.STAFF_VIEWERS)),
):
    teacher = models.Teacher(**payload.model_dump())
    _sync_teacher_left_date(teacher)
    db.add(teacher)
    db.commit()
    db.refresh(teacher)
    return teacher


@app.put("/api/teachers/{teacher_id}", response_model=schemas.TeacherOut)
def update_teacher(
    teacher_id: int,
    payload: schemas.TeacherCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.STAFF_VIEWERS)),
):
    teacher = db.query(models.Teacher).get(teacher_id)
    if not teacher:
        raise HTTPException(404, "O'qituvchi topilmadi")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(teacher, k, v)
    _sync_teacher_left_date(teacher)
    db.commit()
    db.refresh(teacher)
    return teacher


@app.delete("/api/teachers/{teacher_id}")
def delete_teacher(
    teacher_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FULL_ACCESS)),
):
    teacher = db.query(models.Teacher).get(teacher_id)
    if not teacher:
        raise HTTPException(404, "O'qituvchi topilmadi")
    db.delete(teacher)
    db.commit()
    return {"ok": True}


# -------------------------------------------------------------- Groups ----
@app.get("/api/groups", response_model=List[schemas.GroupOut])
def list_groups(db: Session = Depends(get_db), user=Depends(get_current_user)):
    backfill_missing_ids(db, "group", models.Group)
    q = scope_to_branch(db.query(models.Group), models.Group, user)
    groups = q.order_by(models.Group.name).all()
    out = []
    for g in groups:
        item = schemas.GroupOut.model_validate(g)
        item.student_count = len(g.students)
        out.append(item)
    return out


@app.get("/api/groups/{group_id}", response_model=schemas.GroupOut)
def get_group(
    group_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)
):
    group = _get_group_in_scope(db, group_id, user)
    item = schemas.GroupOut.model_validate(group)
    item.student_count = len(group.students)
    return item


def _validate_group_fields(payload):
    """Fan va daraja bir-biriga mos bo'lishi kerak - rus tilida
    "Step 1" degan daraja yo'q."""
    if payload.subject and payload.subject not in dict(roles.SUBJECTS):
        raise HTTPException(400, "Noto'g'ri fan")
    if payload.level and not roles.level_valid(payload.subject, payload.level):
        raise HTTPException(
            400, "Bu daraja tanlangan fanga tegishli emas")
    if payload.lesson_days:
        bad = [d for d in payload.lesson_days.split(",")
               if d and d not in roles.WEEKDAY_KEYS]
        if bad:
            raise HTTPException(400, "Noto'g'ri dars kuni")


@app.post("/api/groups", response_model=schemas.GroupOut)
def create_group(
    payload: schemas.GroupCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FULL_ACCESS)),
):
    _validate_group_fields(payload)
    group = models.Group(**payload.model_dump())
    db.add(group)
    db.commit()
    db.refresh(group)
    item = schemas.GroupOut.model_validate(group)
    item.student_count = 0
    return item


@app.put("/api/groups/{group_id}", response_model=schemas.GroupOut)
def update_group(
    group_id: int,
    payload: schemas.GroupUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FULL_ACCESS)),
):
    group = db.query(models.Group).get(group_id)
    if not group:
        raise HTTPException(404, "Guruh topilmadi")

    fields = payload.model_dump(exclude_unset=True)
    # Fan va daraja mosligini TEKSHIRISHDAN OLDIN yangi qiymatlarni
    # eskisi bilan qo'shib chiqamiz: faqat darajani yuborganda ham
    # tekshiruv guruhning fanini bilishi kerak.
    merged = schemas.GroupCreate(
        name=fields.get("name", group.name),
        subject=fields.get("subject", group.subject),
        level=fields.get("level", group.level),
        lesson_days=fields.get("lesson_days", group.lesson_days),
    )
    _validate_group_fields(merged)

    for k, v in fields.items():
        setattr(group, k, v)
    db.commit()
    db.refresh(group)
    item = schemas.GroupOut.model_validate(group)
    item.student_count = len(group.students)
    return item


@app.delete("/api/groups/{group_id}")
def delete_group(
    group_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FULL_ACCESS)),
):
    group = db.query(models.Group).get(group_id)
    if not group:
        raise HTTPException(404, "Guruh topilmadi")
    db.delete(group)
    db.commit()
    return {"ok": True}


# ------------------------------------------------------------ Students ----
@app.get("/api/students", response_model=List[schemas.StudentOut])
def list_students(
    q: Optional[str] = None,
    group_id: Optional[int] = None,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    backfill_missing_ids(db, "student", models.Student)
    query = scope_to_branch(db.query(models.Student), models.Student, user)
    if q:
        query = query.filter(models.Student.full_name.ilike(f"%{q}%"))
    if group_id:
        query = query.filter(models.Student.group_id == group_id)
    if status_filter:
        query = query.filter(models.Student.status == status_filter)
    students = query.order_by(models.Student.full_name).all()
    return [to_student_out(db, s) for s in students]


@app.get("/api/students/{student_id}", response_model=schemas.StudentDetail)
def get_student(
    student_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)
):
    s = db.query(models.Student).get(student_id)
    if not s:
        raise HTTPException(404, "Talaba topilmadi")
    out = schemas.StudentDetail.model_validate(s)
    out.balance = student_balance(db, s.id)
    out.payments = [schemas.PaymentOut.model_validate(p) for p in s.payments]
    return out


@app.post("/api/students", response_model=schemas.StudentOut)
def create_student(
    payload: schemas.StudentCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_STAFF)),
):
    data = payload.model_dump()
    if not data.get("enrolled_date"):
        data["enrolled_date"] = date.today()
    s = models.Student(**data)
    db.add(s)
    db.commit()
    db.refresh(s)
    _ensure_public_id(db, "student", s)
    audit.log(db, user, entity="student", action="create", entity_id=s.id,
              entity_label=s.full_name, branch_id=s.branch_id,
              new_value=s.full_name)
    db.commit()
    db.refresh(s)
    return to_student_out(db, s)


@app.put("/api/students/{student_id}", response_model=schemas.StudentOut)
def update_student(
    student_id: int,
    payload: schemas.StudentUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_STAFF)),
):
    s = db.query(models.Student).get(student_id)
    if not s:
        raise HTTPException(404, "Talaba topilmadi")
    changes = payload.model_dump(exclude_unset=True)
    # Eski qiymatlar hali joyida turganda yozib olamiz.
    audit.log_changes(db, user, entity="student", obj=s, changes=changes)
    for k, v in changes.items():
        setattr(s, k, v)
    _sync_student_left_date(s)
    db.commit()
    db.refresh(s)
    return to_student_out(db, s)


@app.delete("/api/students/{student_id}")
def delete_student(
    student_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FULL_ACCESS)),
):
    s = db.query(models.Student).get(student_id)
    if not s:
        raise HTTPException(404, "Talaba topilmadi")
    audit.log(db, user, entity="student", action="delete", entity_id=s.id,
              entity_label=s.full_name, branch_id=s.branch_id,
              old_value=s.full_name)
    db.delete(s)
    db.commit()
    return {"ok": True}


# ------------------------------------------------------------ Payments ----
@app.get("/api/students/{student_id}/payments", response_model=List[schemas.PaymentOut])
def list_payments(
    student_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)
):
    return (
        db.query(models.Payment)
        .filter(models.Payment.student_id == student_id)
        .order_by(models.Payment.created_at.desc())
        .all()
    )


@app.post("/api/students/{student_id}/payments", response_model=schemas.PaymentOut)
def add_payment(
    student_id: int,
    payload: schemas.PaymentCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FINANCE_ACCESS)),
):
    s = db.query(models.Student).get(student_id)
    if not s:
        raise HTTPException(404, "Talaba topilmadi")

    amount = payload.amount
    if payload.kind in ("charge", "discount") and amount > 0:
        # charges/discounts reduce balance, so store as negative internally
        amount = -abs(amount)
    elif payload.kind == "payment":
        amount = abs(amount)

    # To'lov usuli faqat haqiqiy kirim uchun ma'noga ega.
    method = None
    if payload.kind == "payment":
        method = payload.method or "cash"
        if method not in roles.PAYMENT_METHODS:
            raise HTTPException(400, "Noto'g'ri to'lov usuli")

    payment = models.Payment(
        student_id=student_id,
        amount=amount,
        kind=payload.kind,
        method=method,
        note=payload.note,
        created_by=user.full_name,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    _ensure_public_id(db, "payment", payment)

    # Chegirma alohida amal sifatida yoziladi - "kim chegirma berdi"
    # degan savolga javob shu yerdan chiqadi.
    act = "discount" if payload.kind == "discount" else "create"
    audit.log(db, user, entity="payment", action=act, entity_id=payment.id,
              entity_label=s.full_name, field=payload.kind,
              new_value=amount, note=payload.note, branch_id=s.branch_id)
    db.commit()

    # Sinovdagi o'quvchi to'lov qilsa - 3 ta darsni kutmasdan darrov
    # faollashadi, hisob-kitob birinchi kelgan kunidan boshlanadi.
    if payload.kind == "payment" and s.status == "trial":
        if _maybe_auto_activate(db, s, user=user, paid=True):
            db.commit()

    db.refresh(payment)
    return payment


@app.delete("/api/payments/{payment_id}")
def delete_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FINANCE_ACCESS)),
):
    """Xato kiritilgan yozuvni o'chirish. Balans va hisobotlar shu
    jadvaldan hisoblanadi, shuning uchun o'chirilishi bilan hamma joyda
    avtomatik to'g'rilanadi.

    Avtomatik hisoblangan oylik ("period" belgisi bor) o'chirilmaydi -
    uni Guruh sahifasidan qayta hisoblash kerak, aks holda o'sha oy
    uchun yana hisoblanib, ikki marta tushib qolishi mumkin."""
    p = db.query(models.Payment).get(payment_id)
    if not p:
        raise HTTPException(404, "Yozuv topilmadi")

    s = db.query(models.Student).get(p.student_id)
    if (
        user.role not in tuple(roles.ORG_WIDE_ROLES)
        and user.branch_id
        and s
        and s.branch_id != user.branch_id
    ):
        raise HTTPException(403, "Bu o'quvchi boshqa filialga tegishli")

    if p.period:
        raise HTTPException(
            400,
            "Avtomatik hisoblangan oylikni o'chirib bo'lmaydi - "
            "guruh sahifasidan qayta hisoblang",
        )

    # Qarzdorlikni o'chirish ("charge" yozuvini olib tashlash) alohida
    # amal - kim qildi, qachon, qancha summani - hammasi yoziladi.
    act = "debt_write_off" if p.kind == "charge" else "payment_cancel"
    audit.log(db, user, entity="payment", action=act, entity_id=p.id,
              entity_label=s.full_name if s else None, field=p.kind,
              old_value=p.amount, new_value=None, note=p.note,
              branch_id=s.branch_id if s else None)
    db.delete(p)
    db.commit()
    return {"ok": True}


# -------------------------------------------------------- Group access ----
def _get_group_in_scope(db: Session, group_id: int, user: models.User) -> models.Group:
    """Fetch a group and 404/403 it the way every lesson/billing/payroll
    endpoint below needs: not found, or outside the caller's branch."""
    group = db.query(models.Group).get(group_id)
    if not group:
        raise HTTPException(404, "Guruh topilmadi")
    if user.role not in tuple(roles.ORG_WIDE_ROLES):
        if user.branch_id and group.branch_id != user.branch_id:
            raise HTTPException(403, "Bu guruh boshqa filialga tegishli")
    return group


# -------------------------------------------------------- Lessons ("yoqlama") ----
@app.get("/api/groups/{group_id}/lessons", response_model=List[schemas.LessonOut])
def list_lessons(
    group_id: int,
    year: int,
    month: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    group = _get_group_in_scope(db, group_id, user)
    start, end = billing.month_bounds(year, month)
    _sync_scheduled_lessons(db, group, start, end)
    return (
        db.query(models.Lesson)
        .filter(models.Lesson.group_id == group.id,
                models.Lesson.date >= start, models.Lesson.date <= end)
        .order_by(models.Lesson.date)
        .all()
    )


@app.post("/api/groups/{group_id}/lessons", response_model=schemas.LessonOut)
def add_lesson(
    group_id: int,
    payload: schemas.LessonCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(*roles.TEACHING_STAFF)),
):
    group = _get_group_in_scope(db, group_id, user)
    # Guruh boshlanmagan kunga yoqlama qo'yib bo'lmaydi - aks holda
    # hisob-kitob ham, davomat ham noto'g'ri chiqadi.
    if group.start_date and payload.date < group.start_date:
        raise HTTPException(
            400,
            f"Guruh {group.start_date.isoformat()} da boshlangan - "
            "undan oldingi kunga yoqlama qo'yib bo'lmaydi")
    existing = (
        db.query(models.Lesson)
        .filter(models.Lesson.group_id == group.id, models.Lesson.date == payload.date)
        .first()
    )
    if existing:
        # Jadval bo'yicha avtomat yaratilgan bo'sh kun bo'lsa - xato
        # bermaymiz, shunchaki "o'tildi" deb belgilaymiz.
        if not existing.held:
            existing.held = 1
            if payload.teacher_id is not None:
                existing.teacher_id = payload.teacher_id
            if payload.note:
                existing.note = payload.note
            db.commit()
            db.refresh(existing)
            return existing
        raise HTTPException(400, "Bu kun uchun allaqachon dars (yoqlama) belgilangan")

    lesson = models.Lesson(
        group_id=group.id,
        teacher_id=payload.teacher_id if payload.teacher_id is not None else group.teacher_id,
        date=payload.date,
        note=payload.note,
        created_by=user.full_name,
    )
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    return lesson


@app.delete("/api/lessons/{lesson_id}")
def delete_lesson(
    lesson_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(*roles.TEACHING_STAFF)),
):
    lesson = db.query(models.Lesson).get(lesson_id)
    if not lesson:
        raise HTTPException(404, "Dars topilmadi")
    _get_group_in_scope(db, lesson.group_id, user)  # branch guard

    # Darsga bog'langan davomat va baholarni ham olib tashlaymiz, aks holda
    # ular "yetim" qolib, bazada bog'liqlik xatosi chiqadi. Baho o'chgani
    # uchun u bergan coin ham qaytariladi.
    for gr in db.query(models.DailyGrade).filter(
        models.DailyGrade.lesson_id == lesson_id
    ).all():
        _drop_coin_entry(db, "daily", gr.id)
        db.delete(gr)
    db.query(models.Attendance).filter(
        models.Attendance.lesson_id == lesson_id
    ).delete(synchronize_session=False)

    db.delete(lesson)
    db.commit()
    return {"ok": True}


# -------------------------------------------------------------- Billing ----
@app.post("/api/groups/{group_id}/billing/run", response_model=schemas.BillingRunResult)
def run_billing(
    group_id: int,
    year: int,
    month: int,
    commit: bool = False,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(*roles.FINANCE_ACCESS)),
):
    group = _get_group_in_scope(db, group_id, user)
    period = f"{year:04d}-{month:02d}"
    charges = billing.compute_student_charges(db, group, year, month)

    results = []
    for c in charges:
        created = False
        if commit and not c["already_charged"] and c["amount"] > 0:
            payment = models.Payment(
                student_id=c["student_id"],
                amount=-abs(c["amount"]),
                kind="charge",
                note=f"{group.name} - {period} oyi uchun {c['billable_lessons']} dars",
                created_by=user.full_name,
                period=period,
            )
            db.add(payment)
            created = True
        results.append(
            schemas.StudentChargeResult(
                student_id=c["student_id"],
                student_name=c["student_name"],
                billable_lessons=c["billable_lessons"],
                amount=c["amount"],
                already_charged=c["already_charged"],
                created=created,
            )
        )
    if commit:
        db.commit()

    return schemas.BillingRunResult(
        period=period,
        held_lessons=billing.held_lessons_count(db, group.id, year, month),
        committed=commit,
        results=results,
    )


# -------------------------------------------------------------- Payroll ----
@app.post("/api/groups/{group_id}/payroll/run", response_model=schemas.PayrollRunResult)
def run_payroll(
    group_id: int,
    year: int,
    month: int,
    commit: bool = False,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(*roles.FINANCE_ACCESS)),
):
    group = _get_group_in_scope(db, group_id, user)
    period = f"{year:04d}-{month:02d}"
    computed = billing.compute_teacher_payroll(db, group, year, month)

    results = []
    for c in computed:
        payout = None
        if commit:
            payout = (
                db.query(models.TeacherPayout)
                .filter(
                    models.TeacherPayout.teacher_id == c["teacher_id"],
                    models.TeacherPayout.group_id == group.id,
                    models.TeacherPayout.period == period,
                )
                .first()
            )
            if not payout:
                payout = models.TeacherPayout(
                    teacher_id=c["teacher_id"], group_id=group.id, period=period
                )
                db.add(payout)
            payout.student_count = c["student_count"]
            payout.held_lessons = c["held_lessons"]
            payout.taught_lessons = c["taught_lessons"]
            payout.amount = c["amount"]
            db.flush()

        results.append(
            schemas.TeacherPayoutOut(
                id=payout.id if payout else None,
                teacher_id=c["teacher_id"],
                group_id=group.id,
                period=period,
                student_count=c["student_count"],
                held_lessons=c["held_lessons"],
                taught_lessons=c["taught_lessons"],
                amount=c["amount"],
                paid=bool(payout.paid) if payout else False,
            )
        )
    if commit:
        db.commit()

    return schemas.PayrollRunResult(period=period, committed=commit, results=results)


@app.get("/api/payouts", response_model=List[schemas.TeacherPayoutOut])
def list_payouts(
    year: int,
    month: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(*roles.FINANCE_ACCESS)),
):
    period = f"{year:04d}-{month:02d}"
    q = db.query(models.TeacherPayout).filter(models.TeacherPayout.period == period)
    if user.role not in tuple(roles.ORG_WIDE_ROLES):
        if user.branch_id:
            q = q.join(models.Group).filter(models.Group.branch_id == user.branch_id)
    return q.all()


@app.put("/api/payouts/{payout_id}", response_model=schemas.TeacherPayoutOut)
def update_payout(
    payout_id: int,
    payload: schemas.PayoutUpdate,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role(*roles.FINANCE_ACCESS)),
):
    payout = db.query(models.TeacherPayout).get(payout_id)
    if not payout:
        raise HTTPException(404, "Yozuv topilmadi")
    payout.paid = int(payload.paid)
    db.commit()
    db.refresh(payout)
    return payout


@app.get("/api/health")
def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat()}


# =====================================================================
#  PUL OQIMI (kassa daftari)  -  Google Sheet ko'rinishida
# =====================================================================
def _payment_first_dates(db: Session) -> dict:
    """Har bir o'quvchining ENG BIRINCHI to'lov sanasi (id bilan).
    Shu sana bilan mos tushgan to'lov "yangi to'lov", qolganlari "eski"."""
    rows = (
        db.query(models.Payment.student_id,
                 func.min(models.Payment.created_at))
        .filter(models.Payment.kind == "payment")
        .group_by(models.Payment.student_id)
        .all()
    )
    return {sid: dt for sid, dt in rows}


@app.get("/api/reports/cashflow-ledger")
def cashflow_ledger(
    year: int,
    month: int,
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FINANCE_ACCESS)),
):
    """Bir oylik kassa daftari: har bir kirim va chiqim alohida qator.
    Tepasida - Kirim / Chiqim / Kassa jadvali usullar kesimida, va
    yangi/eski to'lovlar soni bilan summasi."""
    start, end = billing.month_bounds(year, month)
    d0 = datetime.combine(start, datetime.min.time())
    d1 = datetime.combine(end, datetime.max.time())

    # --- Kirimlar ---
    pq = (
        db.query(models.Payment, models.Student)
        .join(models.Student, models.Payment.student_id == models.Student.id)
        .filter(models.Payment.kind == "payment",
                models.Payment.created_at >= d0,
                models.Payment.created_at <= d1)
    )
    if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
        pq = pq.filter(models.Student.branch_id == user.branch_id)
    elif branch_id:
        pq = pq.filter(models.Student.branch_id == branch_id)

    first_dates = _payment_first_dates(db)
    branches = {b.id: b.name for b in db.query(models.Branch).all()}

    rows = []
    new_cnt = new_sum = old_cnt = old_sum = 0
    kirim = {m: 0.0 for m in roles.PAYMENT_METHODS}

    for p, st in pq.all():
        method = p.method if p.method in kirim else "cash"
        kirim[method] += p.amount
        is_new = first_dates.get(st.id) == p.created_at
        if is_new:
            new_cnt += 1
            new_sum += p.amount
        else:
            old_cnt += 1
            old_sum += p.amount
        rows.append({
            "id": f"p{p.id}",
            "date": p.created_at.date().isoformat(),
            "amount": p.amount,
            "title": st.full_name,
            "student_id": st.id,
            "method": method,
            "direction": "in",
            "branch": branches.get(st.branch_id) or "—",
            "category": "new_payment" if is_new else "old_payment",
            "note": p.note,
        })

    # --- Chiqimlar ---
    eq = scope_to_branch(db.query(models.Expense), models.Expense, user).filter(
        models.Expense.date >= start, models.Expense.date <= end
    )
    if branch_id and user.role in tuple(roles.ORG_WIDE_ROLES):
        eq = eq.filter(models.Expense.branch_id == branch_id)

    chiqim = {m: 0.0 for m in roles.PAYMENT_METHODS}
    cat_labels = {k: lbl for k, lbl, _ in roles.EXPENSE_CATEGORY_DEFS}
    for e in eq.all():
        method = getattr(e, "method", None) or "cash"
        if method not in chiqim:
            method = "cash"
        chiqim[method] += e.amount
        rows.append({
            "id": f"e{e.id}",
            "date": e.date.isoformat(),
            "amount": e.amount,
            "title": e.note or cat_labels.get(e.category, e.category),
            "student_id": None,
            "method": method,
            "direction": "out",
            "branch": branches.get(e.branch_id) or "—",
            "category": e.category,
            "note": e.note,
        })

    # Ustozlar ish haqi - avtomatik chiqim, alohida qator sifatida
    period = _period_key(year, month)
    payroll = _payroll_total(db, user, period)
    if payroll:
        chiqim["cash"] += payroll
        rows.append({
            "id": f"payroll-{period}",
            "date": end.isoformat(),
            "amount": payroll,
            "title": "Ustozlar oyligi (avtomatik)",
            "student_id": None,
            "method": "cash",
            "direction": "out",
            "branch": "—",
            "category": "teacher_salary",
            "note": None,
        })

    rows.sort(key=lambda r: (r["date"], r["id"]))

    def block(d):
        return {**d, "total": sum(d.values())}

    kassa = {m: kirim[m] - chiqim[m] for m in roles.PAYMENT_METHODS}

    return {
        "period": period,
        "kirim": block(kirim),
        "chiqim": block(chiqim),
        "kassa": block(kassa),
        "new_payments": {"count": new_cnt, "amount": new_sum},
        "old_payments": {"count": old_cnt, "amount": old_sum},
        "rows": rows,
    }


# =====================================================================
#  HR  -  vakansiya va nomzodlar
# =====================================================================
@app.get("/api/vacancies")
def list_vacancies(
    status: str | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.HR_ACCESS)),
):
    q = scope_to_branch(db.query(models.Vacancy), models.Vacancy, user)
    if status:
        q = q.filter(models.Vacancy.status == status)
    out = []
    for v in q.order_by(models.Vacancy.created_at.desc()).all():
        cands = db.query(models.Candidate).filter(
            models.Candidate.vacancy_id == v.id).all()
        out.append({
            "id": v.id, "title": v.title, "role": v.role,
            "branch_id": v.branch_id,
            "branch": v.branch.name if v.branch else None,
            "headcount": v.headcount, "status": v.status,
            "salary_from": v.salary_from, "salary_to": v.salary_to,
            "description": v.description,
            "created_at": v.created_at.isoformat() if v.created_at else None,
            "candidate_count": len(cands),
            "hired_count": sum(1 for c in cands if c.stage == "hired"),
        })
    return out


@app.post("/api/vacancies")
def create_vacancy(
    payload: schemas.VacancyCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.HR_ACCESS)),
):
    data = payload.model_dump()
    if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
        data["branch_id"] = user.branch_id
    v = models.Vacancy(**data, created_by=user.username)
    db.add(v); db.commit(); db.refresh(v)
    return {"id": v.id}


@app.put("/api/vacancies/{vid}")
def update_vacancy(
    vid: int,
    payload: schemas.VacancyUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.HR_ACCESS)),
):
    v = db.query(models.Vacancy).get(vid)
    if not v:
        raise HTTPException(404, "Vakansiya topilmadi")
    for k, val in payload.model_dump(exclude_unset=True).items():
        setattr(v, k, val)
    # Yopilgan sanani avtomat qo'yamiz - qo'lda eslab qolish shart emas.
    v.closed_at = date.today() if v.status == "closed" else None
    db.commit()
    return {"ok": True}


@app.delete("/api/vacancies/{vid}")
def delete_vacancy(
    vid: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.HR_ACCESS)),
):
    v = db.query(models.Vacancy).get(vid)
    if not v:
        raise HTTPException(404, "Vakansiya topilmadi")
    n = db.query(models.Candidate).filter(models.Candidate.vacancy_id == vid).count()
    if n:
        raise HTTPException(400, f"Bu vakansiyada {n} ta nomzod bor. Avval ularni o'chiring.")
    db.delete(v); db.commit()
    return {"ok": True}


@app.get("/api/candidates")
def list_candidates(
    vacancy_id: int | None = None,
    stage: str | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.HR_ACCESS)),
):
    q = scope_to_branch(db.query(models.Candidate), models.Candidate, user)
    if vacancy_id:
        q = q.filter(models.Candidate.vacancy_id == vacancy_id)
    if stage:
        q = q.filter(models.Candidate.stage == stage)
    return [{
        "id": c.id, "full_name": c.full_name, "phone": c.phone,
        "vacancy_id": c.vacancy_id,
        "vacancy": c.vacancy.title if c.vacancy else None,
        "stage": c.stage, "source": c.source,
        "branch_id": c.branch_id,
        "branch": c.branch.name if c.branch else None,
        "note": c.note, "reject_reason": c.reject_reason,
        "hired_date": c.hired_date.isoformat() if c.hired_date else None,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    } for c in q.order_by(models.Candidate.created_at.desc()).all()]


def _sync_candidate_dates(c: models.Candidate):
    """Bosqichga qarab sanalarni avtomat to'ldiradi/tozalaydi."""
    if c.stage == "hired":
        c.hired_date = c.hired_date or date.today()
        c.closed_date = c.closed_date or date.today()
    elif c.stage == "rejected":
        c.hired_date = None
        c.closed_date = c.closed_date or date.today()
    else:
        c.hired_date = None
        c.closed_date = None


@app.post("/api/candidates")
def create_candidate(
    payload: schemas.CandidateCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.HR_ACCESS)),
):
    data = payload.model_dump()
    if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
        data["branch_id"] = user.branch_id
    c = models.Candidate(**data, created_by=user.username)
    _sync_candidate_dates(c)
    db.add(c); db.commit(); db.refresh(c)
    return {"id": c.id}


@app.put("/api/candidates/{cid}")
def update_candidate(
    cid: int,
    payload: schemas.CandidateUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.HR_ACCESS)),
):
    c = db.query(models.Candidate).get(cid)
    if not c:
        raise HTTPException(404, "Nomzod topilmadi")
    for k, val in payload.model_dump(exclude_unset=True).items():
        setattr(c, k, val)
    _sync_candidate_dates(c)
    db.commit()
    return {"ok": True}


@app.delete("/api/candidates/{cid}")
def delete_candidate(
    cid: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.HR_ACCESS)),
):
    c = db.query(models.Candidate).get(cid)
    if not c:
        raise HTTPException(404, "Nomzod topilmadi")
    db.delete(c); db.commit()
    return {"ok": True}


@app.get("/api/reports/hr-funnel")
def hr_funnel(
    months: int = 12,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.HR_ACCESS)),
):
    """Ishga olish voronkasi: nomzodlar qaysi bosqichda to'xtab qolyapti."""
    months = max(1, min(months, 36))
    since = date.today() - timedelta(days=int(months * 30.44))
    q = scope_to_branch(db.query(models.Candidate), models.Candidate, user).filter(
        models.Candidate.created_at >= datetime.combine(since, datetime.min.time())
    )
    cands = q.all()
    total = len(cands)
    order = roles.CANDIDATE_FUNNEL
    idx = {k: i for i, k in enumerate(order)}

    rejected = [c for c in cands if c.stage == "rejected"]
    stages = []
    for i, key in enumerate(order):
        # Bu bosqichga YETGANLAR = hozir shu yerda yoki undan oldinga o'tgan
        reached = sum(1 for c in cands
                      if c.stage != "rejected" and idx.get(c.stage, -1) >= i)
        here = sum(1 for c in cands if c.stage == key)
        stages.append({
            "stage": key,
            "label": roles.CANDIDATE_STAGE_LABELS[key],
            "reached": reached,
            "stuck_here": here if key != "hired" else 0,
            "percent": round(reached / total * 100, 1) if total else 0.0,
        })

    # Manba kesimida
    by_source = {}
    for c in cands:
        d = by_source.setdefault(c.source, {"total": 0, "hired": 0})
        d["total"] += 1
        if c.stage == "hired":
            d["hired"] += 1
    sources = [{
        "key": k,
        "label": roles.CANDIDATE_SOURCE_LABELS.get(k, k),
        "total": v["total"], "hired": v["hired"],
        "percent": round(v["hired"] / v["total"] * 100, 1) if v["total"] else 0.0,
    } for k, v in sorted(by_source.items(), key=lambda kv: -kv[1]["total"])]

    hired = [c for c in cands if c.stage == "hired" and c.hired_date and c.created_at]
    avg_days = (round(sum((c.hired_date - c.created_at.date()).days
                          for c in hired) / len(hired), 1) if hired else 0.0)

    vq = scope_to_branch(db.query(models.Vacancy), models.Vacancy, user)
    return {
        "total": total,
        "hired": len(hired),
        "rejected": len(rejected),
        "hire_rate": round(len(hired) / total * 100, 1) if total else 0.0,
        "avg_days_to_hire": avg_days,
        "open_vacancies": vq.filter(models.Vacancy.status == "open").count(),
        "stages": stages,
        "sources": sources,
    }


# =====================================================================
#  MARKETING  -  voronka va CAC
# =====================================================================
def _marketing_spend(db: Session, user, start: date, end: date,
                     branch_id=None) -> dict:
    """Kanal kesimida reklama xarajati. Kanal ko'rsatilmagan reklama
    xarajati "other"ga tushadi - shunda umumiy summa hech qachon
    yo'qolmaydi."""
    marketing_cats = [k for k, _, g in roles.EXPENSE_CATEGORY_DEFS
                      if g == "marketing"]
    q = scope_to_branch(db.query(models.Expense), models.Expense, user,
                        branch_id).filter(
        models.Expense.date >= start,
        models.Expense.date <= end,
        models.Expense.category.in_(marketing_cats),
    )
    out = {}
    for e in q.all():
        ch = getattr(e, "channel", None) or "other"
        out[ch] = out.get(ch, 0.0) + e.amount
    return out


@app.get("/api/reports/marketing-funnel")
def marketing_funnel(
    months: int = 6,
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.MARKETING_ACCESS)),
):
    """Kanal bo'yicha voronka: qancha pul ketdi -> qancha lid keldi ->
    qanchasi sinovga keldi -> qanchasi to'lovchi o'quvchiga aylandi.
    Oxirida har bir kanal uchun CAC (bitta mijoz qancha turdi)."""
    # months=0 -> butun davr
    months = 0 if months == 0 else max(1, min(months, 120))
    today = date.today()
    since = (date(2000, 1, 1) if months == 0
             else today - timedelta(days=int(months * 30.44)))
    start = since
    end = today

    spend = _marketing_spend(db, user, start, end, branch_id)

    lq = scope_to_branch(db.query(models.Lead), models.Lead, user, branch_id).filter(
        models.Lead.created_at >= datetime.combine(since, datetime.min.time())
    )
    leads = lq.all()

    order = roles.LEAD_FUNNEL_ORDER
    idx = {k: i for i, k in enumerate(order)}

    # Aylangan lidlarning daromadi - LTV emas, shu paytgacha to'lagani
    conv_ids = [l.converted_student_id for l in leads if l.converted_student_id]
    revenue_by_student = {}
    if conv_ids:
        for sid, total in (db.query(models.Payment.student_id,
                                    func.coalesce(func.sum(models.Payment.amount), 0.0))
                           .filter(models.Payment.kind == "payment",
                                   models.Payment.student_id.in_(conv_ids))
                           .group_by(models.Payment.student_id).all()):
            revenue_by_student[sid] = float(total)

    channels = {}
    for l in leads:
        ch = l.source or "other"
        d = channels.setdefault(ch, {"leads": 0, "trial": 0, "converted": 0,
                                     "rejected": 0, "revenue": 0.0})
        d["leads"] += 1
        pos = idx.get(l.stage, -1)
        if l.stage == "rejected":
            d["rejected"] += 1
        else:
            if pos >= idx["trial_attended"]:
                d["trial"] += 1
            if l.stage == "converted":
                d["converted"] += 1
                d["revenue"] += revenue_by_student.get(l.converted_student_id, 0.0)

    for ch in spend:
        channels.setdefault(ch, {"leads": 0, "trial": 0, "converted": 0,
                                 "rejected": 0, "revenue": 0.0})

    rows = []
    for ch, d in channels.items():
        s = spend.get(ch, 0.0)
        rows.append({
            "channel": ch,
            "label": roles.MARKETING_CHANNEL_LABELS.get(ch, ch),
            "spend": s,
            "leads": d["leads"],
            "trial": d["trial"],
            "converted": d["converted"],
            "rejected": d["rejected"],
            "revenue": round(d["revenue"], 2),
            "conversion": round(d["converted"] / d["leads"] * 100, 1) if d["leads"] else 0.0,
            # CPL - bitta lid qancha turdi, CAC - bitta MIJOZ qancha turdi
            "cpl": round(s / d["leads"], 0) if d["leads"] and s else 0.0,
            "cac": round(s / d["converted"], 0) if d["converted"] and s else 0.0,
            "roi": round((d["revenue"] - s) / s * 100, 1) if s else 0.0,
        })
    rows.sort(key=lambda r: -r["leads"])

    total_spend = sum(spend.values())
    total_leads = sum(d["leads"] for d in channels.values())
    total_conv = sum(d["converted"] for d in channels.values())
    total_rev = sum(d["revenue"] for d in channels.values())

    # Umumiy voronka bosqichlari
    stages = []
    for i, key in enumerate(order):
        reached = sum(1 for l in leads
                      if l.stage != "rejected" and idx.get(l.stage, -1) >= i)
        stages.append({
            "stage": key,
            "label": roles.LEAD_STAGE_LABELS.get(key, key),
            "reached": reached,
            "stuck_here": sum(1 for l in leads if l.stage == key),
            "percent": round(reached / total_leads * 100, 1) if total_leads else 0.0,
        })

    return {
        "months": months,
        "channels": rows,
        "stages": stages,
        "totals": {
            "spend": total_spend,
            "leads": total_leads,
            "converted": total_conv,
            "revenue": round(total_rev, 2),
            "conversion": round(total_conv / total_leads * 100, 1) if total_leads else 0.0,
            "cpl": round(total_spend / total_leads, 0) if total_leads and total_spend else 0.0,
            "cac": round(total_spend / total_conv, 0) if total_conv and total_spend else 0.0,
            "roi": round((total_rev - total_spend) / total_spend * 100, 1) if total_spend else 0.0,
        },
    }


@app.get("/api/analytics/cac")
def analytics_cac(
    months: int = 12,
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FINANCE_ACCESS)),
):
    """Oylar bo'yicha CAC: reklamaga ketgan pul / o'sha oyda BIRINCHI
    marta to'lagan o'quvchilar soni. Pastda LTV/CAC nisbati - 3 dan
    yuqori bo'lsa biznes sog'lom hisoblanadi."""
    if months == 0:
        oldest = db.query(func.min(models.Payment.created_at)).scalar()
        t = date.today()
        first = oldest.date() if oldest else t
        months = max(1, (t.year - first.year) * 12 + (t.month - first.month) + 1)
    months = max(1, min(months, 120))
    today = date.today()

    firsts = _payment_first_dates(db)
    # O'quvchi filiali - filialga bog'langan foydalanuvchi uchun filtr
    sb = {s.id: s.branch_id for s in
          scope_to_branch(db.query(models.Student), models.Student, user, branch_id).all()}

    rows = []
    for back in range(months - 1, -1, -1):
        y, m = _shift_month(today.year, today.month, -back)
        start, end = billing.month_bounds(y, m)
        spend = sum(_marketing_spend(db, user, start, end, branch_id).values())
        new_clients = sum(1 for sid, dt in firsts.items()
                          if sid in sb and start <= dt.date() <= end)
        rows.append({
            "period": _period_key(y, m),
            "spend": spend,
            "new_clients": new_clients,
            "cac": round(spend / new_clients, 0) if new_clients and spend else 0.0,
        })

    total_spend = sum(r["spend"] for r in rows)
    total_new = sum(r["new_clients"] for r in rows)
    cac = round(total_spend / total_new, 0) if total_new and total_spend else 0.0

    # LTV - shu davrda birinchi to'lovini qilganlarning o'rtacha jami to'lovi
    first_start = billing.month_bounds(*[int(x) for x in rows[0]["period"].split("-")])[0]
    cohort = [sid for sid, dt in firsts.items()
              if sid in sb and dt.date() >= first_start]
    ltv = 0.0
    if cohort:
        total = (db.query(func.coalesce(func.sum(models.Payment.amount), 0.0))
                 .filter(models.Payment.kind == "payment",
                         models.Payment.student_id.in_(cohort)).scalar() or 0.0)
        ltv = round(float(total) / len(cohort), 0)

    return {
        "rows": rows,
        "totals": {
            "spend": total_spend,
            "new_clients": total_new,
            "cac": cac,
            "ltv": ltv,
            "ratio": round(ltv / cac, 2) if cac else 0.0,
        },
    }


# =====================================================================
#  IJTIMOIY TARMOQLAR  -  obunachilar soni
# =====================================================================
def _fetch_telegram_followers(handle: str) -> int | None:
    """Ochiq Telegram kanalining obunachilar sonini t.me sahifasidan
    o'qiydi. Token kerak emas - sahifa hammaga ochiq."""
    import re as _re
    import urllib.request
    try:
        req = urllib.request.Request(
            f"https://t.me/{handle}",
            headers={"User-Agent": "Mozilla/5.0 (compatible; JonyCRM/1.0)"},
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            html = r.read().decode("utf-8", "ignore")
    except Exception:
        return None
    m = _re.search(r'tgme_page_extra">([\d\s \xa0,]+)\s*(?:subscribers|members|obuna)',
                   html, _re.I)
    if not m:
        m = _re.search(r'([\d\s \xa0,]{2,})\s*subscribers', html, _re.I)
    if not m:
        return None
    digits = _re.sub(r"\D", "", m.group(1))
    return int(digits) if digits else None


def _fetch_youtube_subscribers(handle: str) -> int | None:
    """YouTube kanalining obunachilar sonini ochiq sahifadan o'qiydi.
    Kanal @handle bilan ochiq bo'lsa token kerak emas."""
    import re as _re
    import urllib.request
    try:
        req = urllib.request.Request(
            f"https://www.youtube.com/@{handle}",
            headers={"User-Agent": "Mozilla/5.0 (compatible; JonyCRM/1.0)",
                     "Accept-Language": "en-US,en;q=0.9"},
        )
        with urllib.request.urlopen(req, timeout=12) as r:
            html = r.read().decode("utf-8", "ignore")
    except Exception:
        return None
    # "subscriberCountText":{"simpleText":"1.2K subscribers"} ko'rinishida
    m = _re.search(r'"subscriberCountText"\s*:\s*\{[^}]*?"(?:simpleText|content)"'
                   r'\s*:\s*"([^"]+)"', html)
    if not m:
        m = _re.search(r'([\d.,]+\s*[KMB]?)\s*subscribers', html, _re.I)
    if not m:
        return None
    txt = m.group(1).strip()
    num = _re.match(r"([\d.,]+)\s*([KMB])?", txt, _re.I)
    if not num:
        return None
    try:
        val = float(num.group(1).replace(",", ""))
    except ValueError:
        return None
    mult = {"K": 1_000, "M": 1_000_000, "B": 1_000_000_000}
    if num.group(2):
        val *= mult.get(num.group(2).upper(), 1)
    return int(val)


def _fetch_instagram_followers() -> int | None:
    """Instagram Graph API. Ishlashi uchun INSTAGRAM_TOKEN va
    INSTAGRAM_USER_ID muhit o'zgaruvchilari kerak (Business/Creator
    akkaunt + Facebook sahifa). Ular bo'lmasa None qaytaradi va
    oxirgi qo'lda kiritilgan qiymat saqlanib qoladi."""
    import json as _json
    import urllib.request
    token = os.getenv("INSTAGRAM_TOKEN")
    uid = os.getenv("INSTAGRAM_USER_ID")
    if not token or not uid:
        return None
    try:
        url = (f"https://graph.facebook.com/v19.0/{uid}"
               f"?fields=followers_count&access_token={token}")
        with urllib.request.urlopen(url, timeout=10) as r:
            data = _json.loads(r.read().decode())
        return int(data.get("followers_count"))
    except Exception:
        return None


def _latest_social(db: Session, platform: str):
    return (db.query(models.SocialStat)
            .filter(models.SocialStat.platform == platform)
            .order_by(models.SocialStat.date.desc(),
                      models.SocialStat.id.desc()).first())


def _save_social(db: Session, platform: str, followers: int, source: str):
    """Kunига bitta yozuv - shu kun uchun bo'lsa yangilanadi."""
    today = date.today()
    row = (db.query(models.SocialStat)
           .filter(models.SocialStat.platform == platform,
                   models.SocialStat.date == today).first())
    if row:
        row.followers = followers
        row.source = source
    else:
        db.add(models.SocialStat(platform=platform, followers=followers,
                                 source=source, date=today))
    db.commit()


@app.get("/api/social")
def social_stats(
    days: int = 90,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    since = date.today() - timedelta(days=max(7, min(days, 730)))

    # HAQIQIY AVTOMATIKA: bugungi o'lchov yo'q bo'lsa - o'zi olib keladi.
    # Ya'ni kuniga bir marta, birinchi ochgan odam uchun yangilanadi va
    # hech kim "Yangilash" tugmasini bosib yurishi shart emas.
    # Xatolik bo'lsa jim o'tadi - dashboard baribir ochilishi kerak.
    try:
        if not _latest_social(db, "telegram") or \
           _latest_social(db, "telegram").date != date.today():
            tg = _fetch_telegram_followers(roles.SOCIAL_HANDLES["telegram"])
            if tg:
                _save_social(db, "telegram", tg, "auto")
        yt_last = _latest_social(db, "youtube")
        if not yt_last or yt_last.date != date.today():
            yt = _fetch_youtube_subscribers(roles.SOCIAL_HANDLES["youtube"])
            if yt:
                _save_social(db, "youtube", yt, "auto")
        ig_last = _latest_social(db, "instagram")
        if os.getenv("INSTAGRAM_TOKEN") and (
            not ig_last or ig_last.date != date.today()
        ):
            ig = _fetch_instagram_followers()
            if ig:
                _save_social(db, "instagram", ig, "auto")
    except Exception:
        pass

    out = {}
    for key, label in roles.SOCIAL_PLATFORMS:
        last = _latest_social(db, key)
        hist = (db.query(models.SocialStat)
                .filter(models.SocialStat.platform == key,
                        models.SocialStat.date >= since)
                .order_by(models.SocialStat.date).all())
        prev = hist[0].followers if len(hist) > 1 else None
        out[key] = {
            "platform": key,
            "label": label,
            "handle": roles.SOCIAL_HANDLES.get(key),
            "followers": last.followers if last else None,
            "source": last.source if last else None,
            "date": last.date.isoformat() if last and last.date else None,
            "growth": (last.followers - prev) if last and prev is not None else None,
            "history": [{"date": h.date.isoformat(), "followers": h.followers}
                        for h in hist],
        }
    return out


@app.post("/api/social/refresh")
def social_refresh(
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.MARKETING_ACCESS)),
):
    """Telegram - avtomat o'qiydi. Instagram - token bo'lsa o'qiydi."""
    result = {}
    tg = _fetch_telegram_followers(roles.SOCIAL_HANDLES["telegram"])
    if tg:
        _save_social(db, "telegram", tg, "auto")
    result["telegram"] = tg

    yt = _fetch_youtube_subscribers(roles.SOCIAL_HANDLES["youtube"])
    if yt:
        _save_social(db, "youtube", yt, "auto")
    result["youtube"] = yt

    ig = _fetch_instagram_followers()
    if ig:
        _save_social(db, "instagram", ig, "auto")
    result["instagram"] = ig
    result["instagram_note"] = (
        None if ig else
        "Instagram uchun rasmiy token kerak (INSTAGRAM_TOKEN + "
        "INSTAGRAM_USER_ID). Hozircha qo'lda kiriting."
    )
    return result


@app.post("/api/social/manual")
def social_manual(
    payload: schemas.SocialManual,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.MARKETING_ACCESS)),
):
    if payload.platform not in dict(roles.SOCIAL_PLATFORMS):
        raise HTTPException(400, "Noma'lum platforma")
    _save_social(db, payload.platform, payload.followers, "manual")
    return {"ok": True}


# =====================================================================
#  Guruhdagi o'quvchi ustidagi amallar (ro'yxatdagi 3 nuqta menyusi)
# =====================================================================
@app.post("/api/students/{student_id}/activate")
def activate_student(
    student_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_STAFF)),
):
    """Sinovdagi (yoki muzlatilgan) o'quvchini FAOL qiladi.

    Guruhga qo'shilgan o'quvchi avtomat faol bo'lmaydi - avval sinov
    darsida turadi. Faollashtirish shu tugma orqali, ongli ravishda
    bo'ladi: shundan keyingina u hisob-kitobga to'liq kiradi."""
    s = db.query(models.Student).get(student_id)
    if not s:
        raise HTTPException(404, "O'quvchi topilmadi")
    if s.status == "active":
        raise HTTPException(400, "Bu o'quvchi allaqachon faol")
    old = s.status
    s.status = "active"
    # Faollashgan kun - o'qish boshlangan kun deb hisoblanadi.
    if not s.enrolled_date:
        s.enrolled_date = date.today()
    _sync_student_left_date(s)
    audit.log(db, user, entity="student", action="activate", entity_id=s.id,
              entity_label=s.full_name, field="status",
              old_value=old, new_value="active", branch_id=s.branch_id)
    db.commit()
    return {"ok": True, "status": s.status}


@app.post("/api/students/{student_id}/move-group")
def move_student_group(
    student_id: int,
    payload: schemas.StudentGroupMove,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_STAFF)),
):
    """Boshqa guruhga o'tkazadi. group_id bo'sh bo'lsa - guruhdan
    chiqaradi, lekin o'quvchi bazada qoladi (to'lov tarixi saqlanadi)."""
    s = db.query(models.Student).get(student_id)
    if not s:
        raise HTTPException(404, "O'quvchi topilmadi")

    if payload.group_id is None:
        old = s.group.name if s.group else None
        audit.log(db, user, entity="student", action="group_remove",
                  entity_id=s.id, entity_label=s.full_name, field="group",
                  old_value=old, new_value=None, branch_id=s.branch_id)
        s.group_id = None
        db.commit()
        return {"ok": True, "group_id": None}

    g = _get_group_in_scope(db, payload.group_id, user)
    if g.id == s.group_id:
        raise HTTPException(400, "O'quvchi allaqachon shu guruhda")
    audit.log(db, user, entity="student", action="group_move", entity_id=s.id,
              entity_label=s.full_name, field="group",
              old_value=s.group.name if s.group else None, new_value=g.name,
              branch_id=s.branch_id)
    s.group_id = g.id
    # Filial guruh bilan birga o'zgaradi - aks holda hisobotlar chalkashadi.
    if g.branch_id:
        s.branch_id = g.branch_id
    db.commit()
    return {"ok": True, "group_id": g.id, "group": g.name}


# =====================================================================
#  OTA-ONALAR
# =====================================================================
def _parent_out(p: models.Parent, students: list = None) -> dict:
    return {
        "id": p.id,
        "public_id": p.public_id,
        "full_name": p.full_name,
        "phone": p.phone,
        "phone2": p.phone2,
        "relation": p.relation,
        "address": p.address,
        "workplace": p.workplace,
        "note": p.note,
        "branch_id": p.branch_id,
        "branch": p.branch.name if p.branch else None,
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "students": [{"id": s.id, "public_id": s.public_id,
                      "full_name": s.full_name, "status": s.status}
                     for s in (students or [])],
    }


@app.get("/api/parents")
def list_parents(
    q: str | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_STAFF)),
):
    query = scope_to_branch(db.query(models.Parent), models.Parent, user)
    if q:
        like = f"%{q}%"
        query = query.filter(
            (models.Parent.full_name.ilike(like))
            | (models.Parent.phone.ilike(like))
            | (models.Parent.public_id.ilike(like))
        )
    rows = query.order_by(models.Parent.full_name).all()
    kids = {}
    if rows:
        for st in (db.query(models.Student)
                   .filter(models.Student.parent_id.in_([r.id for r in rows]))
                   .all()):
            kids.setdefault(st.parent_id, []).append(st)
    return [_parent_out(p, kids.get(p.id, [])) for p in rows]


@app.get("/api/parents/{parent_id}")
def get_parent(
    parent_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_STAFF)),
):
    p = db.query(models.Parent).get(parent_id)
    if not p:
        raise HTTPException(404, "Ota-ona topilmadi")
    kids = db.query(models.Student).filter(
        models.Student.parent_id == p.id).all()
    return _parent_out(p, kids)


@app.post("/api/parents")
def create_parent(
    payload: schemas.ParentCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_STAFF)),
):
    data = payload.model_dump()
    if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
        data["branch_id"] = user.branch_id
    p = models.Parent(**data, created_by=user.username)
    db.add(p); db.commit(); db.refresh(p)
    _ensure_public_id(db, "parent", p)
    audit.log(db, user, entity="parent", action="create", entity_id=p.id,
              entity_label=p.full_name, new_value=p.full_name,
              branch_id=p.branch_id)
    db.commit(); db.refresh(p)
    return _parent_out(p)


@app.put("/api/parents/{parent_id}")
def update_parent(
    parent_id: int,
    payload: schemas.ParentUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_STAFF)),
):
    p = db.query(models.Parent).get(parent_id)
    if not p:
        raise HTTPException(404, "Ota-ona topilmadi")
    changes = payload.model_dump(exclude_unset=True)
    # Telefon o'zgarishi alohida amal sifatida yoziladi - eski raqam
    # tarixda qolishi kerak.
    audit.log_changes(db, user, entity="parent", obj=p, changes=changes)
    for k, v in changes.items():
        setattr(p, k, v)
    db.commit(); db.refresh(p)
    return _parent_out(p)


@app.delete("/api/parents/{parent_id}")
def delete_parent(
    parent_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FULL_ACCESS)),
):
    p = db.query(models.Parent).get(parent_id)
    if not p:
        raise HTTPException(404, "Ota-ona topilmadi")
    n = db.query(models.Student).filter(models.Student.parent_id == p.id).count()
    if n:
        raise HTTPException(400, f"Bu ota-onaga {n} ta o'quvchi bog'langan")
    audit.log(db, user, entity="parent", action="delete", entity_id=p.id,
              entity_label=p.full_name, old_value=p.full_name,
              branch_id=p.branch_id)
    db.delete(p); db.commit()
    return {"ok": True}


# =====================================================================
#  SHARTNOMALAR
# =====================================================================
def _contract_out(c: models.Contract) -> dict:
    return {
        "id": c.id,
        "public_id": c.public_id,
        "student_id": c.student_id,
        "student": c.student.full_name if c.student else None,
        "student_public_id": c.student.public_id if c.student else None,
        "parent_id": c.parent_id,
        "parent": c.parent.full_name if c.parent else None,
        "group_id": c.group_id,
        "group": c.group.name if c.group else None,
        "branch_id": c.branch_id,
        "branch": c.branch.name if c.branch else None,
        "date": c.date.isoformat() if c.date else None,
        "start_date": c.start_date.isoformat() if c.start_date else None,
        "end_date": c.end_date.isoformat() if c.end_date else None,
        "monthly_fee": c.monthly_fee,
        "discount_percent": c.discount_percent,
        "status": c.status,
        "note": c.note,
        "created_by": c.created_by,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }


@app.get("/api/contracts")
def list_contracts(
    student_id: int | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FINANCE_ACCESS)),
):
    q = scope_to_branch(db.query(models.Contract), models.Contract, user)
    if student_id:
        q = q.filter(models.Contract.student_id == student_id)
    if status:
        q = q.filter(models.Contract.status == status)
    return [_contract_out(c)
            for c in q.order_by(models.Contract.date.desc()).all()]


@app.post("/api/contracts")
def create_contract(
    payload: schemas.ContractCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FINANCE_ACCESS)),
):
    st = db.query(models.Student).get(payload.student_id)
    if not st:
        raise HTTPException(404, "O'quvchi topilmadi")
    data = payload.model_dump()
    # Bo'sh qoldirilgan maydonlarni o'quvchidan avtomat to'ldiramiz.
    data["branch_id"] = data.get("branch_id") or st.branch_id
    data["parent_id"] = data.get("parent_id") or st.parent_id
    data["group_id"] = data.get("group_id") or st.group_id
    if not data.get("monthly_fee") and st.group:
        data["monthly_fee"] = st.group.monthly_fee
    c = models.Contract(**data, created_by=user.full_name)
    db.add(c); db.commit(); db.refresh(c)
    _ensure_public_id(db, "contract", c)
    audit.log(db, user, entity="contract", action="create", entity_id=c.id,
              entity_label=st.full_name, new_value=c.monthly_fee,
              branch_id=c.branch_id)
    db.commit(); db.refresh(c)
    return _contract_out(c)


@app.put("/api/contracts/{contract_id}")
def update_contract(
    contract_id: int,
    payload: schemas.ContractUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FINANCE_ACCESS)),
):
    c = db.query(models.Contract).get(contract_id)
    if not c:
        raise HTTPException(404, "Shartnoma topilmadi")
    changes = payload.model_dump(exclude_unset=True)
    audit.log_changes(db, user, entity="contract", obj=c, changes=changes,
                      label_attr="public_id")
    for k, v in changes.items():
        setattr(c, k, v)
    db.commit(); db.refresh(c)
    return _contract_out(c)


@app.delete("/api/contracts/{contract_id}")
def delete_contract(
    contract_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FULL_ACCESS)),
):
    c = db.query(models.Contract).get(contract_id)
    if not c:
        raise HTTPException(404, "Shartnoma topilmadi")
    audit.log(db, user, entity="contract", action="delete", entity_id=c.id,
              entity_label=c.public_id, branch_id=c.branch_id)
    db.delete(c); db.commit()
    return {"ok": True}


# =====================================================================
#  SHIKOYATLAR
# =====================================================================
def _complaint_out(c: models.Complaint) -> dict:
    return {
        "id": c.id,
        "student_id": c.student_id,
        "student": c.student.full_name if c.student else None,
        "group_id": c.group_id,
        "group": c.group.name if c.group else None,
        "branch_id": c.branch_id,
        "branch": c.branch.name if c.branch else None,
        "source": c.source,
        "severity": c.severity,
        "subject": c.subject,
        "body": c.body,
        "status": c.status,
        "resolution": c.resolution,
        "assigned_user_id": c.assigned_user_id,
        "assigned_user": c.assigned_user.full_name if c.assigned_user else None,
        "closed_at": c.closed_at.isoformat() if c.closed_at else None,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        # Necha kundan beri ochiq - asoschi panelida shu muhim
        "age_days": (date.today() - c.created_at.date()).days
                    if c.created_at and c.status != "closed" else 0,
    }


@app.get("/api/complaints")
def list_complaints(
    status: str | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_STAFF)),
):
    q = scope_to_branch(db.query(models.Complaint), models.Complaint, user)
    if status:
        q = q.filter(models.Complaint.status == status)
    return [_complaint_out(c)
            for c in q.order_by(models.Complaint.created_at.desc()).all()]


@app.post("/api/complaints")
def create_complaint(
    payload: schemas.ComplaintCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_STAFF)),
):
    data = payload.model_dump()
    if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
        data["branch_id"] = user.branch_id
    c = models.Complaint(**data, created_by=user.full_name)
    db.add(c); db.commit(); db.refresh(c)
    audit.log(db, user, entity="complaint", action="create", entity_id=c.id,
              entity_label=c.subject, new_value=c.severity,
              branch_id=c.branch_id, commit=True)
    return _complaint_out(c)


@app.put("/api/complaints/{complaint_id}")
def update_complaint(
    complaint_id: int,
    payload: schemas.ComplaintUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_STAFF)),
):
    c = db.query(models.Complaint).get(complaint_id)
    if not c:
        raise HTTPException(404, "Shikoyat topilmadi")
    changes = payload.model_dump(exclude_unset=True)
    audit.log_changes(db, user, entity="complaint", obj=c, changes=changes,
                      label_attr="subject")
    for k, v in changes.items():
        setattr(c, k, v)
    # Yopilgan sana avtomat - qo'lda eslab qolish shart emas.
    c.closed_at = date.today() if c.status == "closed" else None
    db.commit()
    return _complaint_out(c)


@app.delete("/api/complaints/{complaint_id}")
def delete_complaint(
    complaint_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FULL_ACCESS)),
):
    c = db.query(models.Complaint).get(complaint_id)
    if not c:
        raise HTTPException(404, "Shikoyat topilmadi")
    audit.log(db, user, entity="complaint", action="delete", entity_id=c.id,
              entity_label=c.subject, branch_id=c.branch_id)
    db.delete(c); db.commit()
    return {"ok": True}


# =====================================================================
#  AUDIT LOG
# =====================================================================
@app.get("/api/audit")
def audit_list(
    entity: str | None = None,
    entity_id: int | None = None,
    action: str | None = None,
    user_id: int | None = None,
    days: int = 90,
    limit: int = 200,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.AUDIT_VIEW)),
):
    """O'zgarishlar tarixi. Faqat o'qish uchun - hech kim tahrirlay
    yoki o'chira olmaydi."""
    since = datetime.combine(
        date.today() - timedelta(days=max(1, min(days, 730))),
        datetime.min.time())
    q = db.query(models.AuditLog).filter(models.AuditLog.created_at >= since)

    # Filial rahbari faqat o'z filialining tarixini ko'radi.
    if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
        q = q.filter(
            (models.AuditLog.branch_id == user.branch_id)
            | (models.AuditLog.branch_id.is_(None))
        )
    if entity:
        q = q.filter(models.AuditLog.entity == entity)
    if entity_id:
        q = q.filter(models.AuditLog.entity_id == entity_id)
    if action:
        q = q.filter(models.AuditLog.action == action)
    if user_id:
        q = q.filter(models.AuditLog.user_id == user_id)

    rows = (q.order_by(models.AuditLog.created_at.desc(),
                       models.AuditLog.id.desc())
            .limit(max(1, min(limit, 1000))).all())
    return {
        "total": q.count(),
        "rows": [{
            "id": r.id,
            "user_name": r.user_name or r.username,
            "user_role": r.user_role,
            "entity": r.entity,
            "entity_label_type": audit.ENTITIES.get(r.entity, r.entity),
            "entity_id": r.entity_id,
            "entity_label": r.entity_label,
            "action": r.action,
            "action_label": audit.ACTIONS.get(r.action, r.action),
            "field": r.field,
            "old_value": r.old_value,
            "new_value": r.new_value,
            "note": r.note,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        } for r in rows],
    }


@app.get("/api/audit/meta")
def audit_meta(user=Depends(require_role(*roles.AUDIT_VIEW))):
    return {
        "actions": [{"key": k, "label": v} for k, v in audit.ACTIONS.items()],
        "entities": [{"key": k, "label": v} for k, v in audit.ENTITIES.items()],
    }


# =====================================================================
#  ASOSCHI PANELI  -  qaror qabul qilish oynasi
# =====================================================================
def _today_bounds():
    t = date.today()
    return (datetime.combine(t, datetime.min.time()),
            datetime.combine(t, datetime.max.time()))


@app.get("/api/ceo/today")
def ceo_today(
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.PROFIT_VIEW)),
):
    """Bugungi kun bir ekranda: pul kirdimi, chiqdimi, kim keldi, kim
    ketdi, nima e'tibor talab qiladi.

    Maqsad - raqamlarni sanab chiqish emas, balki bugun nima qilish
    kerakligini ko'rsatish. Shuning uchun oxirida "kritik
    ogohlantirishlar" bo'limi bor."""
    today = date.today()
    d0, d1 = _today_bounds()
    org_wide = user.role in tuple(roles.ORG_WIDE_ROLES)
    my_branch = None if org_wide else user.branch_id

    def scope_students(q):
        return q.filter(models.Student.branch_id == my_branch) if my_branch else q

    # ---- Pul ----
    pq = (db.query(models.Payment)
          .join(models.Student, models.Payment.student_id == models.Student.id)
          .filter(models.Payment.kind == "payment",
                  models.Payment.created_at >= d0,
                  models.Payment.created_at <= d1))
    pq = scope_students(pq)
    payments = pq.all()
    income = sum(p.amount for p in payments)

    eq = db.query(models.Expense).filter(models.Expense.date == today)
    if my_branch:
        eq = eq.filter(models.Expense.branch_id == my_branch)
    expense = sum(e.amount for e in eq.all())

    # ---- Lidlar va sotuv ----
    lq = db.query(models.Lead).filter(models.Lead.created_at >= d0,
                                      models.Lead.created_at <= d1)
    if my_branch:
        lq = lq.filter(models.Lead.branch_id == my_branch)
    new_leads = lq.count()

    tq = db.query(models.Lead).filter(models.Lead.updated_at >= d0,
                                      models.Lead.updated_at <= d1,
                                      models.Lead.stage != "new")
    if my_branch:
        tq = tq.filter(models.Lead.branch_id == my_branch)
    touched_leads = tq.count()

    # Bugun BIRINCHI marta to'lagan o'quvchilar - haqiqiy sotuv
    firsts = _payment_first_dates(db)
    scoped_ids = {s.id for s in scope_students(db.query(models.Student)).all()}
    sales = sum(1 for sid, dt in firsts.items()
                if sid in scoped_ids and dt.date() == today)

    # ---- O'quvchilar ----
    all_students = scope_students(db.query(models.Student)).all()
    active = [s for s in all_students if s.status == "active"]
    debtors = []
    for s in active:
        bal = student_balance(db, s.id)
        if bal < 0:
            debtors.append({"id": s.id, "public_id": s.public_id,
                            "full_name": s.full_name, "balance": bal,
                            "group": s.group.name if s.group else None})
    debtors.sort(key=lambda d: d["balance"])
    total_debt = sum(d["balance"] for d in debtors)

    left_today = [{"id": s.id, "full_name": s.full_name,
                   "group": s.group.name if s.group else None}
                  for s in all_students if s.left_date == today]

    # ---- Davomat (bugungi darslar) ----
    lessons_today = (db.query(models.Lesson)
                     .join(models.Group)
                     .filter(models.Lesson.date == today))
    if my_branch:
        lessons_today = lessons_today.filter(models.Group.branch_id == my_branch)
    lessons_today = lessons_today.all()
    lesson_ids = [l.id for l in lessons_today]
    att_present = att_total = 0
    if lesson_ids:
        for a in (db.query(models.Attendance)
                  .filter(models.Attendance.lesson_id.in_(lesson_ids)).all()):
            att_total += 1
            att_present += 1 if a.present else 0
    unmarked = sum(1 for l in lessons_today if not l.held)

    # ---- Muammoli guruhlar ----
    # To'lishi past (o'quvchi kam) yoki davomat past guruhlar.
    gq = db.query(models.Group)
    if my_branch:
        gq = gq.filter(models.Group.branch_id == my_branch)
    problem_groups = []
    month_start, month_end = billing.month_bounds(today.year, today.month)
    for g in gq.all():
        n = sum(1 for s in all_students
                if s.group_id == g.id and s.status == "active")
        gl = [l for l in db.query(models.Lesson).filter(
            models.Lesson.group_id == g.id,
            models.Lesson.date >= month_start,
            models.Lesson.date <= month_end,
            models.Lesson.held == 1).all()]
        pres = tot = 0
        if gl:
            for a in (db.query(models.Attendance)
                      .filter(models.Attendance.lesson_id.in_([x.id for x in gl]))
                      .all()):
                tot += 1
                pres += 1 if a.present else 0
        att_pct = round(pres / tot * 100, 1) if tot else None
        reasons = []
        if n and n < 6:
            reasons.append(f"atigi {n} o'quvchi")
        if att_pct is not None and att_pct < 70:
            reasons.append(f"davomat {att_pct}%")
        if reasons:
            problem_groups.append({
                "id": g.id, "name": g.name,
                "teacher": g.teacher.full_name if g.teacher else None,
                "students": n, "attendance": att_pct,
                "reasons": reasons,
            })
    problem_groups.sort(key=lambda g: (g["students"], g["attendance"] or 0))

    # ---- Shikoyatlar ----
    cq = db.query(models.Complaint).filter(models.Complaint.status != "closed")
    if my_branch:
        cq = cq.filter(models.Complaint.branch_id == my_branch)
    open_complaints = cq.all()

    # ---- KRITIK OGOHLANTIRISHLAR ----
    # Bu ro'yxat - panelning eng muhim qismi. Har bir qator "bugun
    # nimadir qilish kerak" degani.
    alerts = []

    def alert(level, title, detail, link=None):
        alerts.append({"level": level, "title": title,
                       "detail": detail, "link": link})

    if total_debt < 0:
        big = [d for d in debtors if d["balance"] <= -500_000]
        if big:
            alert("high", f"{len(big)} ta o'quvchida katta qarz",
                  f"Jami {formatless(total_debt)} so'm. Eng kattasi: "
                  f"{big[0]['full_name']} ({formatless(big[0]['balance'])} so'm)",
                  "/students")
        elif debtors:
            alert("normal", f"{len(debtors)} ta qarzdor",
                  f"Jami {formatless(total_debt)} so'm", "/students")

    old_complaints = [c for c in open_complaints
                      if c.created_at
                      and (today - c.created_at.date()).days >= 3]
    if old_complaints:
        alert("high", f"{len(old_complaints)} ta shikoyat 3 kundan beri ochiq",
              old_complaints[0].subject, "/complaints")
    elif open_complaints:
        alert("normal", f"{len(open_complaints)} ta ochiq shikoyat",
              open_complaints[0].subject, "/complaints")

    if unmarked:
        alert("normal", f"{unmarked} ta guruhda bugungi yoqlama qo'yilmagan",
              "Yoqlama qo'yilmasa dars pulga ham, ustoz ish haqiga ham "
              "kirmaydi", "/groups")

    if left_today:
        alert("high", f"Bugun {len(left_today)} o'quvchi ketdi",
              ", ".join(x["full_name"] for x in left_today[:3]), "/students")

    if problem_groups:
        g = problem_groups[0]
        alert("normal", f"{len(problem_groups)} ta muammoli guruh",
              f"{g['name']} — {', '.join(g['reasons'])}", "/groups")

    if new_leads and touched_leads == 0:
        alert("high", f"{new_leads} ta yangi lid, hech biriga bog'lanilmagan",
              "Birinchi soatda bog'lanish konversiyani keskin oshiradi",
              "/leads")

    order = {"high": 0, "normal": 1, "low": 2}
    alerts.sort(key=lambda a: order.get(a["level"], 3))

    return {
        "date": today.isoformat(),
        "scope": "Barcha filiallar" if org_wide else (
            db.query(models.Branch).get(my_branch).name
            if my_branch and db.query(models.Branch).get(my_branch) else "Filial"),
        "money": {
            "income": income,
            "expense": expense,
            "net": income - expense,
            "payment_count": len(payments),
        },
        "sales": {
            "new_leads": new_leads,
            "touched_leads": touched_leads,
            "sales": sales,
        },
        "students": {
            "active": len(active),
            "debtors": len(debtors),
            "total_debt": total_debt,
            "left_today": len(left_today),
            "left_list": left_today[:10],
            "top_debtors": debtors[:10],
        },
        "attendance": {
            "lessons_today": len(lessons_today),
            "unmarked": unmarked,
            "present": att_present,
            "marked": att_total,
            "percent": round(att_present / att_total * 100, 1) if att_total else None,
        },
        "problem_groups": problem_groups[:10],
        "complaints": {
            "open": len(open_complaints),
            "overdue": len(old_complaints),
            "list": [_complaint_out(c) for c in open_complaints[:5]],
        },
        "alerts": alerts,
    }


def formatless(v: float) -> str:
    """Ogohlantirish matni uchun qisqa son: 1 234 567 -> "1.2 mln"."""
    v = abs(v)
    if v >= 1_000_000:
        return f"{v / 1_000_000:.1f} mln"
    if v >= 1_000:
        return f"{round(v / 1_000)} ming"
    return str(int(v))


# =====================================================================
#  O'QUV BO'LIMI  -  xonalar
# =====================================================================
def _room_out(r: models.Room, groups: list = None) -> dict:
    return {
        "id": r.id, "name": r.name, "capacity": r.capacity,
        "branch_id": r.branch_id,
        "branch": r.branch.name if r.branch else None,
        "note": r.note, "active": bool(r.active),
        "groups": [{"id": g.id, "name": g.name} for g in (groups or [])],
    }


@app.get("/api/rooms")
def list_rooms(
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_STAFF)),
):
    q = scope_to_branch(db.query(models.Room), models.Room, user)
    rooms = q.order_by(models.Room.name).all()
    by_room = {}
    for g in db.query(models.Group).filter(models.Group.room_id.isnot(None)).all():
        by_room.setdefault(g.room_id, []).append(g)
    return [_room_out(r, by_room.get(r.id, [])) for r in rooms]


@app.post("/api/rooms")
def create_room(
    payload: schemas.RoomCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.ACADEMIC_ACCESS)),
):
    data = payload.model_dump()
    if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
        data["branch_id"] = user.branch_id
    r = models.Room(**data)
    db.add(r); db.commit(); db.refresh(r)
    audit.log(db, user, entity="room", action="create", entity_id=r.id,
              entity_label=r.name, new_value=r.capacity,
              branch_id=r.branch_id, commit=True)
    return _room_out(r)


@app.put("/api/rooms/{room_id}")
def update_room(
    room_id: int,
    payload: schemas.RoomUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.ACADEMIC_ACCESS)),
):
    r = db.query(models.Room).get(room_id)
    if not r:
        raise HTTPException(404, "Xona topilmadi")
    changes = payload.model_dump(exclude_unset=True)
    audit.log_changes(db, user, entity="room", obj=r, changes=changes,
                      label_attr="name")
    for k, v in changes.items():
        setattr(r, k, v)
    db.commit(); db.refresh(r)
    return _room_out(r)


@app.delete("/api/rooms/{room_id}")
def delete_room(
    room_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.ACADEMIC_ACCESS)),
):
    r = db.query(models.Room).get(room_id)
    if not r:
        raise HTTPException(404, "Xona topilmadi")
    n = db.query(models.Group).filter(models.Group.room_id == room_id).count()
    if n:
        raise HTTPException(400, f"Bu xonada {n} ta guruh bor")
    audit.log(db, user, entity="room", action="delete", entity_id=r.id,
              entity_label=r.name, branch_id=r.branch_id)
    db.delete(r); db.commit()
    return {"ok": True}


# =====================================================================
#  GURUH TO'LISH KOEFFITSIYENTI
# =====================================================================
def _group_capacity(g: models.Group, rooms: dict) -> int | None:
    """Guruh sig'imi: avval o'zining chekloviga, keyin xona sig'imiga
    qaraydi. Ikkalasi ham yo'q bo'lsa - hisoblab bo'lmaydi."""
    if g.capacity:
        return g.capacity
    r = rooms.get(g.room_id)
    return r.capacity if r else None


@app.get("/api/academic/group-fill")
def group_fill(
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.ACADEMIC_VIEW)),
):
    """Guruh to'lishi = faol o'quvchi / sig'im x 100%.

    Bu markazning eng muhim iqtisodiy ko'rsatkichi: yarim bo'sh guruh
    ustoz vaqtini ham, xona ijarasini ham to'liq yeydi, lekin
    daromadning yarmini beradi."""
    rooms = {r.id: r for r in db.query(models.Room).all()}
    gq = scope_to_branch(db.query(models.Group), models.Group, user, branch_id)
    counts = {}
    for s in scope_to_branch(db.query(models.Student), models.Student, user, branch_id).all():
        if s.status == "active" and s.group_id:
            counts[s.group_id] = counts.get(s.group_id, 0) + 1

    rows, no_capacity = [], []
    for g in gq.all():
        n = counts.get(g.id, 0)
        cap = _group_capacity(g, rooms)
        if not cap:
            no_capacity.append({"id": g.id, "name": g.name})
            continue
        pct = round(n / cap * 100, 1)
        band, band_label = roles.fill_band(pct)
        rows.append({
            "id": g.id, "name": g.name,
            "teacher": g.teacher.full_name if g.teacher else None,
            "branch": g.branch.name if g.branch else None,
            "room": rooms[g.room_id].name if g.room_id in rooms else g.room,
            "students": n, "capacity": cap,
            "percent": pct, "band": band, "band_label": band_label,
            "free_seats": max(0, cap - n),
        })
    rows.sort(key=lambda r: r["percent"])

    total_students = sum(r["students"] for r in rows)
    total_capacity = sum(r["capacity"] for r in rows)
    by_band = {}
    for r in rows:
        by_band[r["band"]] = by_band.get(r["band"], 0) + 1

    return {
        "rows": rows,
        "no_capacity": no_capacity,
        "summary": {
            "groups": len(rows),
            "students": total_students,
            "capacity": total_capacity,
            "percent": round(total_students / total_capacity * 100, 1)
                       if total_capacity else 0.0,
            "free_seats": max(0, total_capacity - total_students),
            "by_band": [
                {"band": k, "label": lbl, "count": by_band.get(k, 0)}
                for _m, k, lbl in roles.GROUP_FILL_BANDS
            ],
        },
    }


# =====================================================================
#  AKADEMIK RISK
# =====================================================================
def _absent_streak(db: Session, student_id: int, group_id: int | None) -> int:
    """Oxirgi darslardan boshlab ketma-ket nechta dars qoldirgan."""
    if not group_id:
        return 0
    lessons = (db.query(models.Lesson)
               .filter(models.Lesson.group_id == group_id,
                       models.Lesson.held == 1)
               .order_by(models.Lesson.date.desc()).limit(12).all())
    if not lessons:
        return 0
    marks = {a.lesson_id: a.present for a in
             db.query(models.Attendance).filter(
                 models.Attendance.student_id == student_id,
                 models.Attendance.lesson_id.in_([l.id for l in lessons])).all()}
    streak = 0
    for l in lessons:
        v = marks.get(l.id)
        if v is None:      # belgilanmagan - zanjir uzilmaydi, lekin sanalmaydi
            continue
        if v:
            break
        streak += 1
    return streak


def _score_trend(db: Session, student_id: int) -> float | None:
    """Oxirgi ikki imtihon farqi (foizda). Manfiy - natija tushgan."""
    rows = (db.query(models.ExamResult)
            .join(models.Exam)
            .filter(models.ExamResult.student_id == student_id,
                    models.ExamResult.percent.isnot(None))
            .order_by(models.Exam.date.desc()).limit(2).all())
    if len(rows) < 2:
        return None
    return round((rows[0].percent or 0) - (rows[1].percent or 0), 1)


def _student_risk(db: Session, s: models.Student, *, today: date,
                  flags_by_student: dict, complaints_by_student: dict,
                  moves_by_student: dict) -> dict:
    """Bitta o'quvchining risk holati. Signallar ikki manbadan:
    avtomat hisoblanadigan (davomat, to'lov, shikoyat, guruh almashish)
    va qo'lda qo'yilgan (ustoz izohi, uy vazifasi)."""
    signals = []

    def add(key, detail=None):
        signals.append({
            "key": key,
            "label": roles.RISK_SIGNAL_LABELS.get(key, key),
            "weight": roles.RISK_SIGNAL_WEIGHT.get(key, 1),
            "detail": detail,
        })

    streak = _absent_streak(db, s.id, s.group_id)
    if streak >= 2:
        add("absent_streak", f"ketma-ket {streak} ta dars")

    bal = student_balance(db, s.id)
    if bal < 0:
        add("payment_late", f"{abs(int(bal)):,} so'm qarz".replace(",", " "))

    n_comp = complaints_by_student.get(s.id, 0)
    if n_comp:
        add("complaint", f"{n_comp} ta shikoyat")

    n_moves = moves_by_student.get(s.id, 0)
    if n_moves >= 2:
        add("group_hopping", f"{n_moves} marta guruh almashtirgan")

    trend = _score_trend(db, s.id)
    if trend is not None and trend <= -10:
        add("score_drop", f"{trend} foiz")
    elif trend is not None and -2 <= trend <= 2:
        # O'sish yo'q - tushmayapti ham, ko'tarilmayapti ham
        add("no_progress", "natija joyida turibdi")

    for f in flags_by_student.get(s.id, []):
        add(f.signal, f.note)

    score = sum(x["weight"] for x in signals)
    level = roles.risk_level(score)
    return {
        "student_id": s.id,
        "public_id": s.public_id,
        "full_name": s.full_name,
        "group_id": s.group_id,
        "group": s.group.name if s.group else None,
        "teacher": s.group.teacher.full_name
                   if s.group and s.group.teacher else None,
        "branch": s.branch.name if s.branch else None,
        "phone": s.phone,
        "score": score,
        "level": level,
        "level_label": roles.RISK_LEVEL_LABELS[level],
        "signals": signals,
    }


@app.get("/api/academic/risk")
def academic_risk(
    level: str | None = None,
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.ACADEMIC_VIEW)),
):
    """Xavfdagi o'quvchilar. Ro'yxat avtomat hisoblanadi - hech kim
    qo'lda 'bu bola ketib qoladi' deb belgilashi shart emas."""
    today = date.today()
    students = [s for s in
                scope_to_branch(db.query(models.Student), models.Student, user, branch_id).all()
                if s.status in ("active", "trial")]
    ids = [s.id for s in students]

    flags_by_student = {}
    complaints_by_student = {}
    moves_by_student = {}
    if ids:
        for f in (db.query(models.RiskFlag)
                  .filter(models.RiskFlag.student_id.in_(ids),
                          models.RiskFlag.active == 1).all()):
            flags_by_student.setdefault(f.student_id, []).append(f)
        for c in (db.query(models.Complaint)
                  .filter(models.Complaint.student_id.in_(ids),
                          models.Complaint.status != "closed").all()):
            complaints_by_student[c.student_id] = (
                complaints_by_student.get(c.student_id, 0) + 1)
        for a in (db.query(models.AuditLog)
                  .filter(models.AuditLog.entity == "student",
                          models.AuditLog.action == "group_move",
                          models.AuditLog.entity_id.in_(ids)).all()):
            moves_by_student[a.entity_id] = moves_by_student.get(a.entity_id, 0) + 1

    rows = [_student_risk(db, s, today=today,
                          flags_by_student=flags_by_student,
                          complaints_by_student=complaints_by_student,
                          moves_by_student=moves_by_student)
            for s in students]
    at_risk = [r for r in rows if r["level"] != "normal"]
    at_risk.sort(key=lambda r: -r["score"])
    if level:
        at_risk = [r for r in at_risk if r["level"] == level]

    counts = {k: 0 for k, _, _, _ in roles.RISK_LEVELS}
    for r in rows:
        counts[r["level"]] = counts.get(r["level"], 0) + 1

    # Ochiq vazifalar - kimga biriktirilgani ko'rinib tursin
    open_tasks = {}
    if ids:
        for t in (db.query(models.RiskTask)
                  .filter(models.RiskTask.student_id.in_(ids),
                          models.RiskTask.status == "open").all()):
            open_tasks.setdefault(t.student_id, []).append({
                "id": t.id, "title": t.title,
                "assigned_user": t.assigned_user.full_name
                                 if t.assigned_user else None,
                "due_date": t.due_date.isoformat() if t.due_date else None,
            })
    for r in at_risk:
        r["tasks"] = open_tasks.get(r["student_id"], [])

    return {
        "total": len(rows),
        "at_risk": len(at_risk),
        "levels": [{"key": k, "label": lbl, "color": color,
                    "count": counts.get(k, 0)}
                   for k, lbl, color, _ in roles.RISK_LEVELS],
        "rows": at_risk,
        "signals": [{"key": k, "label": lbl, "weight": w}
                    for k, lbl, w in roles.RISK_SIGNALS],
    }


@app.post("/api/academic/risk-flags")
def add_risk_flag(
    payload: schemas.RiskFlagCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.ACADEMIC_VIEW)),
):
    if payload.signal not in roles.RISK_SIGNAL_LABELS:
        raise HTTPException(400, "Noma'lum signal")
    f = models.RiskFlag(**payload.model_dump(), created_by=user.full_name)
    db.add(f); db.commit(); db.refresh(f)
    audit.log(db, user, entity="student", action="update",
              entity_id=f.student_id, field="risk",
              new_value=roles.RISK_SIGNAL_LABELS[f.signal],
              note=f.note, commit=True)
    return {"id": f.id}


@app.delete("/api/academic/risk-flags/{flag_id}")
def resolve_risk_flag(
    flag_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.ACADEMIC_VIEW)),
):
    f = db.query(models.RiskFlag).get(flag_id)
    if not f:
        raise HTTPException(404, "Topilmadi")
    f.active = 0
    f.resolved_at = date.today()
    db.commit()
    return {"ok": True}


@app.get("/api/academic/tasks")
def list_risk_tasks(
    status: str | None = "open",
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.ACADEMIC_VIEW)),
):
    q = db.query(models.RiskTask).join(
        models.Student, models.RiskTask.student_id == models.Student.id)
    if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
        q = q.filter(models.Student.branch_id == user.branch_id)
    if status:
        q = q.filter(models.RiskTask.status == status)
    today = date.today()
    return [{
        "id": t.id,
        "student_id": t.student_id,
        "student": t.student.full_name if t.student else None,
        "level": t.level,
        "level_label": roles.RISK_LEVEL_LABELS.get(t.level or "", ""),
        "title": t.title,
        "assigned_user_id": t.assigned_user_id,
        "assigned_user": t.assigned_user.full_name if t.assigned_user else None,
        "due_date": t.due_date.isoformat() if t.due_date else None,
        "overdue": bool(t.due_date and t.status == "open" and t.due_date < today),
        "status": t.status,
        "result": t.result,
        "created_at": t.created_at.isoformat() if t.created_at else None,
    } for t in q.order_by(models.RiskTask.due_date).all()]


@app.post("/api/academic/tasks")
def create_risk_task(
    payload: schemas.RiskTaskCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.ACADEMIC_VIEW)),
):
    t = models.RiskTask(**payload.model_dump(), created_by=user.full_name)
    db.add(t); db.commit(); db.refresh(t)
    audit.log(db, user, entity="student", action="update", entity_id=t.student_id,
              field="risk_task", new_value=t.title,
              note=f"Mas'ul: {t.assigned_user.full_name}" if t.assigned_user else None,
              commit=True)
    return {"id": t.id}


@app.put("/api/academic/tasks/{task_id}")
def update_risk_task(
    task_id: int,
    payload: schemas.RiskTaskUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.ACADEMIC_VIEW)),
):
    t = db.query(models.RiskTask).get(task_id)
    if not t:
        raise HTTPException(404, "Vazifa topilmadi")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(t, k, v)
    t.done_at = date.today() if t.status == "done" else None
    db.commit()
    return {"ok": True}


@app.delete("/api/academic/tasks/{task_id}")
def delete_risk_task(
    task_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.ACADEMIC_ACCESS)),
):
    t = db.query(models.RiskTask).get(task_id)
    if not t:
        raise HTTPException(404, "Vazifa topilmadi")
    db.delete(t); db.commit()
    return {"ok": True}


# =====================================================================
#  OTA-ONA SUHBATLARI VA SERTIFIKATLAR
# =====================================================================
@app.get("/api/students/{student_id}/talks")
def list_talks(
    student_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_STAFF)),
):
    rows = (db.query(models.ParentTalk)
            .filter(models.ParentTalk.student_id == student_id)
            .order_by(models.ParentTalk.date.desc()).all())
    return [{"id": t.id, "date": t.date.isoformat() if t.date else None,
             "channel": t.channel, "topic": t.topic, "summary": t.summary,
             "outcome": t.outcome, "created_by": t.created_by} for t in rows]


@app.post("/api/students/{student_id}/talks")
def add_talk(
    student_id: int,
    payload: schemas.ParentTalkCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_STAFF)),
):
    data = payload.model_dump()
    data["date"] = data.get("date") or date.today()
    t = models.ParentTalk(student_id=student_id, **data,
                          created_by=user.full_name)
    db.add(t); db.commit(); db.refresh(t)
    audit.log(db, user, entity="student", action="update", entity_id=student_id,
              field="parent_talk", new_value=t.topic, note=t.summary,
              commit=True)
    return {"id": t.id}


@app.delete("/api/talks/{talk_id}")
def delete_talk(
    talk_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FULL_ACCESS)),
):
    t = db.query(models.ParentTalk).get(talk_id)
    if not t:
        raise HTTPException(404, "Topilmadi")
    db.delete(t); db.commit()
    return {"ok": True}


@app.get("/api/students/{student_id}/certificates")
def list_certificates(
    student_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_STAFF)),
):
    rows = (db.query(models.Certificate)
            .filter(models.Certificate.student_id == student_id)
            .order_by(models.Certificate.date.desc()).all())
    return [{"id": c.id, "kind": c.kind,
             "kind_label": roles.CERTIFICATE_KIND_LABELS.get(c.kind, c.kind),
             "level": c.level, "score": c.score,
             "date": c.date.isoformat() if c.date else None,
             "note": c.note} for c in rows]


@app.post("/api/students/{student_id}/certificates")
def add_certificate(
    student_id: int,
    payload: schemas.CertificateCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.ACADEMIC_VIEW)),
):
    data = payload.model_dump()
    data["date"] = data.get("date") or date.today()
    c = models.Certificate(student_id=student_id, **data,
                           created_by=user.full_name)
    db.add(c); db.commit(); db.refresh(c)
    audit.log(db, user, entity="student", action="update", entity_id=student_id,
              field="certificate",
              new_value=f"{roles.CERTIFICATE_KIND_LABELS.get(c.kind, c.kind)} "
                        f"{c.level or ''}".strip(), commit=True)
    return {"id": c.id}


@app.delete("/api/certificates/{cert_id}")
def delete_certificate(
    cert_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.ACADEMIC_ACCESS)),
):
    c = db.query(models.Certificate).get(cert_id)
    if not c:
        raise HTTPException(404, "Topilmadi")
    db.delete(c); db.commit()
    return {"ok": True}


# =====================================================================
#  O'QUVCHI TARIXI  -  bitta joyda butun yo'l
# =====================================================================
# Holat o'zgarishlarining o'zbekcha nomi.
_STATUS_EVENT = {
    "frozen": ("freeze", "O'qish muzlatildi"),
    "archived": ("leave", "O'qishdan chiqdi"),
    "active": ("return", "Qayta tiklandi"),
    "trial": ("trial", "Sinov darsiga o'tdi"),
}


@app.get("/api/students/{student_id}/history")
def student_history(
    student_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_STAFF)),
):
    """O'quvchining butun yo'li: qaysi guruhlarda, qaysi ustozlarda
    o'qigan, necha marta guruh almashtirgan, qancha dars qoldirgan,
    shikoyatlar, ota-ona bilan suhbatlar, muzlatish va qaytish."""
    s = db.query(models.Student).get(student_id)
    if not s:
        raise HTTPException(404, "O'quvchi topilmadi")

    logs = (db.query(models.AuditLog)
            .filter(models.AuditLog.entity == "student",
                    models.AuditLog.entity_id == student_id)
            .order_by(models.AuditLog.created_at).all())

    # --- Guruh va ustoz tarixi ---
    group_moves = [l for l in logs if l.action in ("group_move", "group_remove")]
    groups_seen, teachers_seen, timeline = [], [], []

    def seen(lst, name):
        if name and name not in lst:
            lst.append(name)

    teacher_by_group = {g.name: (g.teacher.full_name if g.teacher else None)
                        for g in db.query(models.Group).all()}

    for l in group_moves:
        seen(groups_seen, l.old_value)
        seen(groups_seen, l.new_value)
        seen(teachers_seen, teacher_by_group.get(l.old_value or ""))
        seen(teachers_seen, teacher_by_group.get(l.new_value or ""))
        timeline.append({
            "date": l.created_at.isoformat() if l.created_at else None,
            "kind": "group",
            "title": "Guruhdan chiqarildi" if l.action == "group_remove"
                     else "Guruh almashtirildi",
            "detail": f"{l.old_value or '—'} → {l.new_value or '—'}",
            "by": l.user_name,
        })

    if s.group:
        seen(groups_seen, s.group.name)
        seen(teachers_seen, s.group.teacher.full_name if s.group.teacher else None)

    # --- Holat o'zgarishlari: muzlatish / chiqish / qaytish ---
    freezes = leaves = returns = 0
    for l in logs:
        if l.field != "status" and l.action != "activate":
            continue
        new = l.new_value
        if new not in _STATUS_EVENT:
            continue
        kind, title = _STATUS_EVENT[new]
        # "active" ga qaytish - faqat oldin muzlatilgan/ketgan bo'lsa
        if kind == "return":
            if l.old_value not in ("frozen", "archived"):
                continue
            returns += 1
        elif kind == "freeze":
            freezes += 1
        elif kind == "leave":
            leaves += 1
        timeline.append({
            "date": l.created_at.isoformat() if l.created_at else None,
            "kind": kind, "title": title,
            "detail": f"{l.old_value or '—'} → {new}",
            "by": l.user_name,
        })

    # --- Davomat ---
    att = (db.query(models.Attendance, models.Lesson)
           .join(models.Lesson, models.Attendance.lesson_id == models.Lesson.id)
           .filter(models.Attendance.student_id == student_id).all())
    marked = len(att)
    absent = sum(1 for a, _l in att if not a.present)
    absent_dates = sorted(
        (l.date.isoformat() for a, l in att if not a.present), reverse=True)

    # --- Shikoyatlar ---
    comps = (db.query(models.Complaint)
             .filter(models.Complaint.student_id == student_id)
             .order_by(models.Complaint.created_at.desc()).all())
    for c in comps:
        timeline.append({
            "date": c.created_at.isoformat() if c.created_at else None,
            "kind": "complaint",
            "title": "Shikoyat: " + c.subject,
            "detail": c.resolution or c.body,
            "by": c.created_by,
        })

    # --- Ota-ona suhbatlari ---
    talks = (db.query(models.ParentTalk)
             .filter(models.ParentTalk.student_id == student_id)
             .order_by(models.ParentTalk.date.desc()).all())
    for t in talks:
        timeline.append({
            "date": t.date.isoformat() if t.date else None,
            "kind": "talk",
            "title": "Ota-ona bilan suhbat: " + t.topic,
            "detail": t.summary,
            "by": t.created_by,
        })

    # --- Sertifikatlar ---
    certs = (db.query(models.Certificate)
             .filter(models.Certificate.student_id == student_id).all())
    for c in certs:
        timeline.append({
            "date": c.date.isoformat() if c.date else None,
            "kind": "certificate",
            "title": "Sertifikat: "
                     + roles.CERTIFICATE_KIND_LABELS.get(c.kind, c.kind),
            "detail": c.level or (str(c.score) if c.score else None),
            "by": c.created_by,
        })

    timeline.sort(key=lambda x: x["date"] or "", reverse=True)

    return {
        "summary": {
            "groups": groups_seen,
            "group_count": len(groups_seen),
            "teachers": [t for t in teachers_seen if t],
            "group_changes": len([l for l in group_moves
                                  if l.action == "group_move"]),
            "marked_lessons": marked,
            "absences": absent,
            "attendance_percent": round((marked - absent) / marked * 100, 1)
                                  if marked else None,
            "complaints": len(comps),
            "talks": len(talks),
            "certificates": len(certs),
            "freezes": freezes,
            "leaves": leaves,
            "returns": returns,
        },
        "absent_dates": absent_dates[:30],
        "timeline": timeline,
    }


# =====================================================================
#  OILAVIY CHEGIRMA
# =====================================================================
def _family_discount_percent(db: Session, s: models.Student) -> float:
    """Oilaviy chegirma foizi. AVTOMAT: bir ota-onaga bog'langan
    FAOL farzandlar soni chegaradan oshsa - chegirma bor, kamaysa
    o'zidan yo'qoladi. Hech kim qo'lda olib tashlashi shart emas."""
    if not s.parent_id:
        return 0.0
    n = (db.query(models.Student)
         .filter(models.Student.parent_id == s.parent_id,
                 models.Student.status == "active").count())
    if n >= roles.FAMILY_DISCOUNT_MIN_CHILDREN:
        return roles.FAMILY_DISCOUNT_PERCENT
    return 0.0


@app.get("/api/students/{student_id}/pricing")
def student_pricing(
    student_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_STAFF)),
):
    """O'quvchining oylik narxi va unga tegishli chegirmalar."""
    s = db.query(models.Student).get(student_id)
    if not s:
        raise HTTPException(404, "O'quvchi topilmadi")

    base = s.group.monthly_fee if s.group else 0.0
    fam = _family_discount_percent(db, s)

    # Shartnomadagi shaxsiy chegirma (agar bo'lsa)
    contract = (db.query(models.Contract)
                .filter(models.Contract.student_id == student_id,
                        models.Contract.status == "active")
                .order_by(models.Contract.date.desc()).first())
    personal = contract.discount_percent if contract else 0.0
    if contract and contract.monthly_fee:
        base = contract.monthly_fee

    siblings = []
    if s.parent_id:
        siblings = [{"id": x.id, "full_name": x.full_name, "status": x.status}
                    for x in db.query(models.Student).filter(
                        models.Student.parent_id == s.parent_id,
                        models.Student.id != s.id).all()]

    total_pct = min(100.0, fam + personal)
    return {
        "base_fee": base,
        "family_discount": fam,
        "family_min_children": roles.FAMILY_DISCOUNT_MIN_CHILDREN,
        "personal_discount": personal,
        "total_discount": total_pct,
        "final_fee": round(base * (100 - total_pct) / 100, 2),
        "parent_id": s.parent_id,
        "siblings": siblings,
        "active_siblings": sum(1 for x in siblings if x["status"] == "active"),
        # Chegirma qanday paydo bo'lgani va qachon yo'qolishi
        "explanation": (
            f"Oilada {sum(1 for x in siblings if x['status'] == 'active') + (1 if s.status == 'active' else 0)} "
            f"ta faol farzand — {roles.FAMILY_DISCOUNT_PERCENT}% oilaviy chegirma. "
            f"Biri o'qishni to'xtatsa chegirma avtomat yo'qoladi."
            if fam else
            (f"Oilaviy chegirma uchun kamida "
             f"{roles.FAMILY_DISCOUNT_MIN_CHILDREN} ta faol farzand kerak."
             if s.parent_id else
             "Ota-ona biriktirilmagan — oilaviy chegirma hisoblanmaydi.")
        ),
    }


@app.get("/api/reports/family-discounts")
def family_discounts(
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FINANCE_ACCESS)),
):
    """Oilaviy chegirma olayotgan oilalar. Chegirma avtomat
    hisoblanadi, shuning uchun bu ro'yxat har doim haqiqatga mos."""
    parents = scope_to_branch(db.query(models.Parent), models.Parent, user).all()
    kids = {}
    if parents:
        for s in (db.query(models.Student)
                  .filter(models.Student.parent_id.in_([p.id for p in parents]))
                  .all()):
            kids.setdefault(s.parent_id, []).append(s)

    rows = []
    for p in parents:
        ch = kids.get(p.id, [])
        active = [c for c in ch if c.status == "active"]
        if len(active) < roles.FAMILY_DISCOUNT_MIN_CHILDREN:
            continue
        saved = 0.0
        for c in active:
            fee = c.group.monthly_fee if c.group else 0.0
            saved += fee * roles.FAMILY_DISCOUNT_PERCENT / 100
        rows.append({
            "parent_id": p.id, "public_id": p.public_id,
            "parent": p.full_name, "phone": p.phone,
            "children": [{"id": c.id, "full_name": c.full_name,
                          "status": c.status,
                          "group": c.group.name if c.group else None}
                         for c in ch],
            "active_children": len(active),
            "discount_percent": roles.FAMILY_DISCOUNT_PERCENT,
            "monthly_saved": round(saved, 2),
        })
    rows.sort(key=lambda r: -r["active_children"])
    return {
        "percent": roles.FAMILY_DISCOUNT_PERCENT,
        "min_children": roles.FAMILY_DISCOUNT_MIN_CHILDREN,
        "families": len(rows),
        "monthly_total": round(sum(r["monthly_saved"] for r in rows), 2),
        "rows": rows,
    }


# =====================================================================
#  MARKETING: REKLAMA KO'RSATKICHLARI VA TO'LIQ VORONKA
# =====================================================================
@app.get("/api/ad-stats")
def list_ad_stats(
    months: int = 12,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.MARKETING_ACCESS)),
):
    today = date.today()
    periods = []
    for back in range(months - 1, -1, -1):
        y, m = _shift_month(today.year, today.month, -back)
        periods.append(_period_key(y, m))
    q = scope_to_branch(db.query(models.AdStat), models.AdStat, user).filter(
        models.AdStat.period.in_(periods))
    return [{
        "id": a.id, "channel": a.channel,
        "label": roles.MARKETING_CHANNEL_LABELS.get(a.channel, a.channel),
        "period": a.period, "impressions": a.impressions, "clicks": a.clicks,
        "ctr": round(a.clicks / a.impressions * 100, 2) if a.impressions else 0.0,
        "branch_id": a.branch_id, "note": a.note,
    } for a in q.order_by(models.AdStat.period.desc()).all()]


@app.post("/api/ad-stats")
def upsert_ad_stat(
    payload: schemas.AdStatCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.MARKETING_ACCESS)),
):
    """Bir kanal + bir oy uchun bitta yozuv. Qayta yuborilsa
    yangilanadi - takror qator paydo bo'lmaydi."""
    if payload.channel not in roles.MARKETING_CHANNELS:
        raise HTTPException(400, "Noma'lum kanal")
    row = (db.query(models.AdStat)
           .filter(models.AdStat.channel == payload.channel,
                   models.AdStat.period == payload.period).first())
    if row:
        row.impressions = payload.impressions
        row.clicks = payload.clicks
        row.note = payload.note
    else:
        row = models.AdStat(**payload.model_dump(), created_by=user.full_name)
        db.add(row)
    db.commit(); db.refresh(row)
    return {"id": row.id}


@app.delete("/api/ad-stats/{stat_id}")
def delete_ad_stat(
    stat_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.MARKETING_ACCESS)),
):
    a = db.query(models.AdStat).get(stat_id)
    if not a:
        raise HTTPException(404, "Topilmadi")
    db.delete(a); db.commit()
    return {"ok": True}


@app.get("/api/reports/marketing-journey")
def marketing_journey(
    months: int = 6,
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.MARKETING_ACCESS)),
):
    """To'liq yo'l: reklama ko'rildi -> bosildi -> murojaat -> bog'lanildi
    -> testga keldi -> sotildi -> 1 oy qoldi -> 3 oy qoldi -> sertifikat.

    Birinchi ikki bosqich reklama kabinetidan qo'lda kiritiladi
    (Marketing -> Reklama ko'rsatkichlari), qolganlari tizimning o'z
    ma'lumotidan avtomat hisoblanadi."""
    months = 0 if months == 0 else max(1, min(months, 120))
    today = date.today()
    since = (date(2000, 1, 1) if months == 0
             else today - timedelta(days=int(months * 30.44)))

    adq = scope_to_branch(db.query(models.AdStat), models.AdStat, user, branch_id)
    if months:
        periods = []
        for back in range(months - 1, -1, -1):
            y, m = _shift_month(today.year, today.month, -back)
            periods.append(_period_key(y, m))
        adq = adq.filter(models.AdStat.period.in_(periods))
    ads = adq.all()

    leads = scope_to_branch(db.query(models.Lead), models.Lead, user, branch_id).filter(
        models.Lead.created_at >= datetime.combine(since, datetime.min.time())
    ).all()

    order = roles.LEAD_FUNNEL_ORDER
    idx = {k: i for i, k in enumerate(order)}

    conv_ids = [l.converted_student_id for l in leads if l.converted_student_id]
    firsts = _payment_first_dates(db)
    students = {}
    if conv_ids:
        students = {s.id: s for s in db.query(models.Student)
                    .filter(models.Student.id.in_(conv_ids)).all()}
    certs = set()
    if conv_ids:
        certs = {c.student_id for c in db.query(models.Certificate)
                 .filter(models.Certificate.student_id.in_(conv_ids)).all()}

    def survived(sid: int, need_months: float) -> bool:
        """Birinchi to'lovdan keyin shuncha oy qoldimi.
        Hali o'qiyotgan bo'lsa - bugungi kungacha; ketgan bo'lsa -
        ketgan kunigacha hisoblanadi."""
        dt = firsts.get(sid)
        st = students.get(sid)
        if not dt or not st:
            return False
        end = st.left_date or today
        return _months_between(dt.date(), end) >= need_months

    def build(ch_leads, ch_ads):
        imp = sum(a.impressions for a in ch_ads)
        clk = sum(a.clicks for a in ch_ads)
        n_leads = len(ch_leads)
        contacted = sum(1 for l in ch_leads
                        if l.stage != "rejected"
                        and idx.get(l.stage, -1) >= idx["contacted"])
        trial = sum(1 for l in ch_leads
                    if l.stage != "rejected"
                    and idx.get(l.stage, -1) >= idx["trial_attended"])
        sold_ids = [l.converted_student_id for l in ch_leads
                    if l.stage == "converted" and l.converted_student_id]
        sold = len(sold_ids)
        m1 = sum(1 for sid in sold_ids if survived(sid, 1))
        m3 = sum(1 for sid in sold_ids if survived(sid, 3))
        cert = sum(1 for sid in sold_ids if sid in certs)
        return {"impressions": imp, "clicks": clk, "leads": n_leads,
                "contacted": contacted, "trial": trial, "sold": sold,
                "month1": m1, "month3": m3, "certificate": cert}

    totals = build(leads, ads)

    # Bosqichlar: har birida oldingisiga nisbatan o'tish foizi
    stages = []
    prev = None
    for key, label, source in roles.MARKETING_JOURNEY:
        v = totals[key]
        stages.append({
            "key": key, "label": label, "source": source,
            "count": v,
            # Oldingi bosqichdan qanchasi o'tdi - eng muhim raqam
            "step_percent": round(v / prev * 100, 1) if prev else None,
            "of_leads": round(v / totals["leads"] * 100, 1)
                        if totals["leads"] else None,
            "lost": max(0, prev - v) if prev is not None else 0,
        })
        prev = v if v else prev

    # Kanal kesimida
    by_channel = {}
    for l in leads:
        by_channel.setdefault(l.source or "other", {"leads": [], "ads": []})
        by_channel[l.source or "other"]["leads"].append(l)
    for a in ads:
        by_channel.setdefault(a.channel, {"leads": [], "ads": []})
        by_channel[a.channel]["ads"].append(a)

    channels = []
    for ch, d in by_channel.items():
        b = build(d["leads"], d["ads"])
        channels.append({
            "channel": ch,
            "label": roles.MARKETING_CHANNEL_LABELS.get(ch, ch),
            **b,
            "ctr": round(b["clicks"] / b["impressions"] * 100, 2)
                   if b["impressions"] else None,
            "click_to_lead": round(b["leads"] / b["clicks"] * 100, 1)
                             if b["clicks"] else None,
            "lead_to_sale": round(b["sold"] / b["leads"] * 100, 1)
                            if b["leads"] else 0.0,
            "retention_1m": round(b["month1"] / b["sold"] * 100, 1)
                            if b["sold"] else None,
            "retention_3m": round(b["month3"] / b["sold"] * 100, 1)
                            if b["sold"] else None,
        })
    channels.sort(key=lambda c: -c["leads"])

    # Eng katta yo'qotish qayerda
    worst = None
    for st in stages[1:]:
        if st["step_percent"] is not None and st["lost"] > 0:
            if worst is None or st["lost"] > worst["lost"]:
                worst = st

    return {
        "months": months,
        "stages": stages,
        "channels": channels,
        "totals": totals,
        "worst_stage": worst,
        "has_ad_data": totals["impressions"] > 0,
    }


# =====================================================================
#  SINOVDAN FAOL O'QUVCHIGA  -  avtomat o'tish va hisob-kitob
# =====================================================================
def _trial_attendance(db: Session, student_id: int) -> list:
    """Sinovda bo'lgan o'quvchining KELGAN darslari, sana bo'yicha."""
    rows = (db.query(models.Attendance, models.Lesson)
            .join(models.Lesson, models.Attendance.lesson_id == models.Lesson.id)
            .filter(models.Attendance.student_id == student_id,
                    models.Attendance.present == 1)
            .all())
    return sorted((l.date for _a, l in rows))


def _lessons_left_in_month(db: Session, group_id: int, since: date) -> list:
    """Shu kundan (shu kun ham kiradi) oy oxirigacha guruhning dars
    kunlari. Reja ham, o'tilgan ham kiradi: o'quvchi faollashgan kundan
    oy oxirigacha necha darsga pul to'lashi shundan chiqadi."""
    _start, end = billing.month_bounds(since.year, since.month)
    return (db.query(models.Lesson)
            .filter(models.Lesson.group_id == group_id,
                    models.Lesson.date >= since,
                    models.Lesson.date <= end)
            .order_by(models.Lesson.date).all())


def _charge_from_activation(db: Session, s: models.Student, since: date,
                            user=None) -> dict | None:
    """Faollashgan kundan oy oxirigacha nechta dars bo'lsa - shuncha
    pul hisoblanadi va o'quvchi hisobidan yechiladi.

    Balans manfiyga ketishi mumkin - bu ataylab: qarz ko'rinib turishi
    kerak, aks holda administrator kimdan qancha olishini bilmaydi."""
    if not s.group_id or not s.group:
        return None
    period = _period_key(since.year, since.month)
    # Shu oy uchun allaqachon hisoblangan bo'lsa takrorlamaymiz
    exists = (db.query(models.Payment)
              .filter(models.Payment.student_id == s.id,
                      models.Payment.period == period,
                      models.Payment.kind == "charge").first())
    if exists:
        return None

    lessons = _lessons_left_in_month(db, s.group_id, since)
    n = len(lessons)
    if n <= 0:
        return None

    price = s.group.lesson_price or 0
    # Oylik chegirmasi bor bo'lsa - bir darsning narxi ham kamayadi
    disc = _family_discount_percent(db, s)
    amount = n * price * (100 - disc) / 100
    if amount <= 0:
        return None

    db.add(models.Payment(
        student_id=s.id,
        amount=-abs(amount),
        kind="charge",
        note=f"{s.group.name} — {period}: faollashgan kundan {n} dars"
             + (f" (oilaviy chegirma {disc}%)" if disc else ""),
        created_by=(user.full_name if user else "avtomat"),
        period=period,
    ))
    return {"lessons": n, "amount": amount, "discount": disc}


def _activate_student(db: Session, s: models.Student, *, on: date,
                      reason: str, user=None) -> dict:
    """O'quvchini FAOL qiladi va shu kundan oy oxirigacha pul hisoblaydi.

    "on" - faollashish sanasi. Bu odatda o'quvchi BIRINCHI kelgan kuni:
    3 ta sinov darsiga kelgan bo'lsa ham, oldin to'lov qilgan bo'lsa ham
    hisob-kitob birinchi kelgan kunidan boshlanadi."""
    old = s.status
    s.status = "active"
    if not s.enrolled_date or s.enrolled_date > on:
        s.enrolled_date = on
    _sync_student_left_date(s)

    charge = _charge_from_activation(db, s, on, user)

    # Lid ham yopiladi - u endi o'quvchi, doskada turishi shart emas
    lead = (db.query(models.Lead)
            .filter(models.Lead.converted_student_id == s.id).first())
    if not lead:
        lead = (db.query(models.Lead)
                .filter(models.Lead.full_name == s.full_name,
                        models.Lead.stage.notin_(["converted", "rejected"]))
                .first())
    if lead:
        lead.stage = "converted"
        lead.converted_student_id = s.id

    audit.log(db, user, entity="student", action="activate", entity_id=s.id,
              entity_label=s.full_name, field="status",
              old_value=old, new_value="active",
              note=f"{reason}. Faollashish sanasi: {on.isoformat()}"
                   + (f", {charge['lessons']} dars uchun "
                      f"{int(charge['amount'])} so'm hisoblandi" if charge else ""),
              branch_id=s.branch_id)
    return {"activated_on": on.isoformat(), "reason": reason, "charge": charge}


def _maybe_auto_activate(db: Session, s: models.Student, *, user=None,
                         paid: bool = False) -> dict | None:
    """Sinovdagi o'quvchi faollashish shartiga yetdimi.

    Ikki yo'l bor:
      1) sinov darsiga TRIAL_LESSONS_TO_ACTIVATE marta kelgan;
      2) shundan oldin to'lov qilgan.
    Ikkalasida ham faollashish sanasi - BIRINCHI kelgan kun."""
    if s.status != "trial":
        return None
    days = _trial_attendance(db, s.id)
    if paid and days:
        return _activate_student(db, s, on=days[0],
                                 reason="Sinov davrida to'lov qildi", user=user)
    if paid and not days:
        return _activate_student(db, s, on=date.today(),
                                 reason="To'lov qildi", user=user)
    if len(days) >= roles.TRIAL_LESSONS_TO_ACTIVATE:
        return _activate_student(
            db, s, on=days[0],
            reason=f"{roles.TRIAL_LESSONS_TO_ACTIVATE} ta sinov darsiga keldi",
            user=user)
    return None


@app.get("/api/students/{student_id}/trial")
def student_trial_status(
    student_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_STAFF)),
):
    """Sinov holati: nechta darsga keldi, faollashishga qancha qoldi."""
    s = db.query(models.Student).get(student_id)
    if not s:
        raise HTTPException(404, "O'quvchi topilmadi")
    days = _trial_attendance(db, s.id)
    need = roles.TRIAL_LESSONS_TO_ACTIVATE
    return {
        "status": s.status,
        "attended": len(days),
        "need": need,
        "left": max(0, need - len(days)),
        "dates": [d.isoformat() for d in days],
        "first_date": days[0].isoformat() if days else None,
    }


# =====================================================================
#  OYLIK HISOB-KITOB  -  butun markaz bo'yicha
# =====================================================================
@app.post("/api/billing/month")
def billing_month(
    year: int,
    month: int,
    commit: bool = False,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FINANCE_ACCESS)),
):
    """Oy boshida barcha FAOL o'quvchilardan shu oy uchun to'liq pul
    hisoblaydi (balansdan yechadi).

    Shundan keyin "bu oyda qancha pul tushishi kerak" degan savolga
    javob bor, va administrator qancha yig'ganini foizda ko'rish mumkin.

    commit=False - faqat hisoblab ko'rsatadi, hech narsa yozmaydi."""
    period = _period_key(year, month)
    start, end = billing.month_bounds(year, month)

    students = [s for s in
                scope_to_branch(db.query(models.Student), models.Student, user).all()
                if s.status == "active" and s.group_id]

    rows, created = [], 0
    for s in students:
        g = s.group
        if not g:
            continue
        already = (db.query(models.Payment)
                   .filter(models.Payment.student_id == s.id,
                           models.Payment.period == period,
                           models.Payment.kind == "charge").first())
        # O'quvchi oy o'rtasida qo'shilgan bo'lsa - faqat qolgan darslar
        since = start
        if s.enrolled_date and s.enrolled_date > start:
            since = s.enrolled_date
        lessons = len(_lessons_left_in_month(db, g.id, since)) if since <= end else 0
        disc = _family_discount_percent(db, s)
        amount = lessons * (g.lesson_price or 0) * (100 - disc) / 100

        if commit and not already and amount > 0:
            db.add(models.Payment(
                student_id=s.id, amount=-abs(amount), kind="charge",
                note=f"{g.name} — {period} oyi uchun {lessons} dars"
                     + (f" (oilaviy chegirma {disc}%)" if disc else ""),
                created_by=user.full_name, period=period))
            created += 1
        rows.append({
            "student_id": s.id, "public_id": s.public_id,
            "full_name": s.full_name, "group": g.name,
            "lessons": lessons, "discount": disc, "amount": round(amount, 2),
            "already_charged": already is not None,
        })

    if commit:
        audit.log(db, user, entity="payment", action="create",
                  entity_label=f"{period} oylik hisob-kitob",
                  new_value=created,
                  note=f"{created} ta o'quvchiga hisoblandi", commit=True)
        db.commit()

    return {
        "period": period,
        "committed": commit,
        "students": len(rows),
        "created": created,
        "expected_total": round(sum(r["amount"] for r in rows), 2),
        "rows": sorted(rows, key=lambda r: r["full_name"]),
    }


@app.get("/api/billing/collection")
def billing_collection(
    year: int,
    month: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FINANCE_ACCESS)),
):
    """To'lovlarni yig'ish foizi: shu oyda qancha hisoblangan va
    qanchasi haqiqatda tushgan. Administrator KPI'sining asosi."""
    period = _period_key(year, month)
    start, end = billing.month_bounds(year, month)
    d0 = datetime.combine(start, datetime.min.time())
    d1 = datetime.combine(end, datetime.max.time())

    sq = scope_to_branch(db.query(models.Student), models.Student, user)
    ids = [s.id for s in sq.all()]
    if not ids:
        return {"period": period, "charged": 0.0, "collected": 0.0,
                "percent": 0.0, "debt": 0.0, "students": 0, "paid_students": 0,
                "by_admin": []}

    charged = -(db.query(func.coalesce(func.sum(models.Payment.amount), 0.0))
                .filter(models.Payment.kind == "charge",
                        models.Payment.period == period,
                        models.Payment.student_id.in_(ids)).scalar() or 0.0)

    pays = (db.query(models.Payment)
            .filter(models.Payment.kind == "payment",
                    models.Payment.created_at >= d0,
                    models.Payment.created_at <= d1,
                    models.Payment.student_id.in_(ids)).all())
    collected = sum(p.amount for p in pays)
    paid_students = len({p.student_id for p in pays})

    charged_students = {r[0] for r in
                        db.query(models.Payment.student_id)
                        .filter(models.Payment.kind == "charge",
                                models.Payment.period == period,
                                models.Payment.student_id.in_(ids)).all()}

    # Kim yig'di - administrator kesimida
    by_admin = {}
    for p in pays:
        who = p.created_by or "—"
        by_admin[who] = by_admin.get(who, 0.0) + p.amount
    admins = [{"name": k, "collected": round(v, 2),
               "percent": round(v / charged * 100, 1) if charged else 0.0}
              for k, v in sorted(by_admin.items(), key=lambda kv: -kv[1])]

    return {
        "period": period,
        "charged": round(charged, 2),
        "collected": round(collected, 2),
        "percent": round(collected / charged * 100, 1) if charged else 0.0,
        "debt": round(max(0.0, charged - collected), 2),
        "students": len(charged_students),
        "paid_students": paid_students,
        "by_admin": admins,
    }


# =====================================================================
#  FILIALLAR KESIMI  -  solishtirish
# =====================================================================
def _branch_scope_ids(db: Session, user, branch_id: int | None) -> list | None:
    """Foydalanuvchi ko'ra oladigan filiallar. None - hammasi."""
    if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
        return [user.branch_id]
    if branch_id:
        return [branch_id]
    return None


@app.get("/api/ceo/branches")
def ceo_branches(
    months: int = 1,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.PROFIT_VIEW)),
):
    """Filiallarni yonma-yon solishtirish.

    Asoschi uchun eng muhim ko'rinish: qaysi filial ko'proq pul
    keltiryapti, qayerda o'quvchi ko'p ketyapti, qayerda guruhlar
    bo'sh turibdi. Har bir ustun bo'yicha eng yaxshi va eng yomon
    filial belgilanadi."""
    months = max(1, min(months, 24))
    today = date.today()
    y, m = _shift_month(today.year, today.month, -(months - 1))
    start, _e = billing.month_bounds(y, m)
    _s, end = billing.month_bounds(today.year, today.month)
    d0 = datetime.combine(start, datetime.min.time())
    d1 = datetime.combine(end, datetime.max.time())

    allowed = _branch_scope_ids(db, user, None)
    bq = db.query(models.Branch)
    if allowed:
        bq = bq.filter(models.Branch.id.in_(allowed))
    branches = bq.order_by(models.Branch.name).all()

    students = db.query(models.Student).all()
    groups = db.query(models.Group).all()
    rooms = {r.id: r for r in db.query(models.Room).all()}
    firsts = _payment_first_dates(db)

    pays = (db.query(models.Payment, models.Student)
            .join(models.Student, models.Payment.student_id == models.Student.id)
            .filter(models.Payment.kind == "payment",
                    models.Payment.created_at >= d0,
                    models.Payment.created_at <= d1).all())
    exps = (db.query(models.Expense)
            .filter(models.Expense.date >= start,
                    models.Expense.date <= end).all())
    leads = (db.query(models.Lead)
             .filter(models.Lead.created_at >= d0).all())
    payouts = {}
    for p in db.query(models.TeacherPayout).all():
        if p.period and start.isoformat()[:7] <= p.period <= end.isoformat()[:7]:
            g = next((x for x in groups if x.id == p.group_id), None)
            if g:
                payouts[g.branch_id] = payouts.get(g.branch_id, 0.0) + (p.amount or 0)

    rows = []
    for b in branches:
        bs = [s for s in students if s.branch_id == b.id]
        active = [s for s in bs if s.status == "active"]
        trial = [s for s in bs if s.status == "trial"]
        left = [s for s in bs if s.left_date and start <= s.left_date <= end]
        income = sum(p.amount for p, st in pays if st.branch_id == b.id)
        expense = sum(e.amount for e in exps if e.branch_id == b.id)
        payroll = payouts.get(b.id, 0.0)
        outflow = expense + payroll
        profit = income - outflow

        bg = [g for g in groups if g.branch_id == b.id]
        cap = seats = 0
        for g in bg:
            c = _group_capacity(g, rooms)
            if c:
                cap += c
                seats += sum(1 for s in active if s.group_id == g.id)
        fill = round(seats / cap * 100, 1) if cap else None

        bl = [l for l in leads if l.branch_id == b.id]
        conv = sum(1 for l in bl if l.stage == "converted")
        new_clients = sum(1 for s in bs
                          if s.id in firsts and start <= firsts[s.id].date() <= end)

        debt = sum(min(0.0, student_balance(db, s.id)) for s in active)

        rows.append({
            "branch_id": b.id, "branch": b.name,
            "active": len(active), "trial": len(trial), "left": len(left),
            "groups": len(bg),
            "income": round(income, 2),
            "expense": round(outflow, 2),
            "profit": round(profit, 2),
            "margin": round(profit / income * 100, 1) if income else 0.0,
            "arpu": round(income / len(active), 0) if active else 0.0,
            "fill": fill,
            "leads": len(bl), "converted": conv,
            "conversion": round(conv / len(bl) * 100, 1) if bl else 0.0,
            "new_clients": new_clients,
            "debt": round(abs(debt), 2),
            "churn": round(len(left) / (len(active) + len(left)) * 100, 1)
                     if (active or left) else 0.0,
        })

    # Har bir ustunda eng yaxshi va eng yomon filial - solishtirish
    # oson bo'lishi uchun.
    def extremes(key, higher_is_better=True):
        vals = [(r["branch_id"], r[key]) for r in rows if r[key] is not None]
        if len(vals) < 2:
            return None, None
        best = (max if higher_is_better else min)(vals, key=lambda x: x[1])
        worst = (min if higher_is_better else max)(vals, key=lambda x: x[1])
        return best[0], worst[0]

    highlight = {}
    for key, better in [("income", True), ("profit", True), ("margin", True),
                        ("fill", True), ("conversion", True), ("arpu", True),
                        ("churn", False), ("debt", False), ("left", False)]:
        b_, w_ = extremes(key, better)
        highlight[key] = {"best": b_, "worst": w_}

    totals = {
        "active": sum(r["active"] for r in rows),
        "trial": sum(r["trial"] for r in rows),
        "left": sum(r["left"] for r in rows),
        "groups": sum(r["groups"] for r in rows),
        "income": round(sum(r["income"] for r in rows), 2),
        "expense": round(sum(r["expense"] for r in rows), 2),
        "profit": round(sum(r["profit"] for r in rows), 2),
        "debt": round(sum(r["debt"] for r in rows), 2),
        "leads": sum(r["leads"] for r in rows),
        "converted": sum(r["converted"] for r in rows),
        "new_clients": sum(r["new_clients"] for r in rows),
    }
    totals["margin"] = (round(totals["profit"] / totals["income"] * 100, 1)
                        if totals["income"] else 0.0)

    rows.sort(key=lambda r: -r["profit"])
    return {"months": months, "period": f"{start.isoformat()} — {end.isoformat()}",
            "rows": rows, "totals": totals, "highlight": highlight}


# =====================================================================
#  EXAMINER MODULI  -  imtihon nazorati
# =====================================================================
def _exam_out(e: models.Exam, results: list = None) -> dict:
    done = [r for r in (results or []) if not r.absent and r.percent is not None]
    return {
        "id": e.id,
        "group_id": e.group_id,
        "group": e.group.name if e.group else None,
        "teacher": e.group.teacher.full_name
                   if e.group and e.group.teacher else None,
        "branch_id": e.group.branch_id if e.group else None,
        "branch": e.group.branch.name if e.group and e.group.branch else None,
        "kind": e.kind,
        "kind_label": roles.EXAM_KIND_LABELS.get(e.kind, e.kind),
        "unit_no": e.unit_no,
        "title": e.title or examTitleFallback(e),
        "date": e.date.isoformat() if e.date else None,
        "max_score": e.max_score,
        "status": e.status or "draft",
        "status_label": roles.EXAM_STATUS_LABELS.get(e.status or "draft",
                                                     e.status or "draft"),
        "approved_by": e.approved_by,
        "approved_at": e.approved_at.isoformat() if e.approved_at else None,
        "retake_of_id": e.retake_of_id,
        "note": e.note,
        "result_count": len(results or []),
        "avg_percent": round(sum(r.percent for r in done) / len(done), 1)
                       if done else None,
        "absent": sum(1 for r in (results or []) if r.absent),
    }


def examTitleFallback(e: models.Exam) -> str:
    if e.kind == "unit" and e.unit_no:
        return f"Unit {e.unit_no}"
    return roles.EXAM_KIND_LABELS.get(e.kind, e.kind)


@app.get("/api/examiner/exams")
def examiner_exams(
    status: str | None = None,
    branch_id: int | None = None,
    group_id: int | None = None,
    months: int = 6,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.EXAM_VIEW)),
):
    """Imtihon jadvali. Examiner shu yerdan test yaratadi, tasdiqlaydi
    va natijasini kiritadi."""
    since = date.today() - timedelta(days=int(max(1, months) * 30.44))
    q = (db.query(models.Exam).join(models.Group)
         .filter(models.Exam.date >= since))
    allowed = _branch_scope_ids(db, user, branch_id)
    if allowed:
        q = q.filter(models.Group.branch_id.in_(allowed))
    if status:
        q = q.filter(models.Exam.status == status)
    if group_id:
        q = q.filter(models.Exam.group_id == group_id)
    exams = q.order_by(models.Exam.date.desc()).all()

    res = {}
    if exams:
        for r in (db.query(models.ExamResult)
                  .filter(models.ExamResult.exam_id.in_([e.id for e in exams]))
                  .all()):
            res.setdefault(r.exam_id, []).append(r)
    return [_exam_out(e, res.get(e.id, [])) for e in exams]


@app.post("/api/examiner/exams/{exam_id}/approve")
def approve_exam(
    exam_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.EXAM_APPROVE)),
):
    """Testni tasdiqlash. Tasdiqlanmagan testga natija kiritilmaydi -
    shunda o'zboshimchalik bilan qo'yilgan baho bo'lmaydi."""
    e = db.query(models.Exam).get(exam_id)
    if not e:
        raise HTTPException(404, "Imtihon topilmadi")
    if e.status == "approved":
        raise HTTPException(400, "Bu test allaqachon tasdiqlangan")
    e.status = "approved"
    e.approved_by = user.full_name
    e.approved_at = date.today()
    audit.log(db, user, entity="exam", action="update", entity_id=e.id,
              entity_label=e.title or examTitleFallback(e),
              field="status", old_value="draft", new_value="approved",
              commit=True)
    return {"ok": True, "status": e.status}


@app.put("/api/examiner/exams/{exam_id}/status")
def set_exam_status(
    exam_id: int,
    payload: schemas.ExamStatusUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.EXAM_APPROVE)),
):
    e = db.query(models.Exam).get(exam_id)
    if not e:
        raise HTTPException(404, "Imtihon topilmadi")
    if payload.status not in roles.EXAM_STATUS_LABELS:
        raise HTTPException(400, "Noma'lum holat")
    old = e.status
    e.status = payload.status
    if payload.note is not None:
        e.note = payload.note
    audit.log(db, user, entity="exam", action="update", entity_id=e.id,
              entity_label=e.title or examTitleFallback(e), field="status",
              old_value=old, new_value=e.status, commit=True)
    return {"ok": True}


@app.post("/api/examiner/exams/{exam_id}/retake")
def create_retake(
    exam_id: int,
    payload: schemas.RetakeCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.EXAM_ACCESS)),
):
    """Qayta imtihon. Asl imtihonga bog'lanadi, shuning uchun
    "qayta topshirdi va yaxshiladi" degan tarix ko'rinib turadi."""
    src = db.query(models.Exam).get(exam_id)
    if not src:
        raise HTTPException(404, "Imtihon topilmadi")
    e = models.Exam(
        group_id=src.group_id, kind=src.kind, unit_no=src.unit_no,
        title=(src.title or examTitleFallback(src)) + " (qayta)",
        date=payload.date or date.today(),
        max_score=src.max_score, status="approved",
        approved_by=user.full_name, approved_at=date.today(),
        retake_of_id=src.id, note=payload.note,
        created_by=user.full_name)
    db.add(e); db.commit(); db.refresh(e)
    audit.log(db, user, entity="exam", action="create", entity_id=e.id,
              entity_label=e.title, note=f"Qayta imtihon (asli #{src.id})",
              commit=True)
    return _exam_out(e, [])


@app.get("/api/examiner/analysis")
def examiner_analysis(
    months: int = 6,
    branch_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.EXAM_VIEW)),
):
    """Imtihon natijalarining uch kesimda tahlili: ustoz, guruh, filial.
    Pastda standartdan ortda qolgan guruhlar va sertifikatga tavsiya."""
    since = date.today() - timedelta(days=int(max(1, months) * 30.44))
    q = (db.query(models.ExamResult, models.Exam, models.Group)
         .join(models.Exam, models.ExamResult.exam_id == models.Exam.id)
         .join(models.Group, models.Exam.group_id == models.Group.id)
         .filter(models.Exam.date >= since,
                 models.ExamResult.absent == 0,
                 models.ExamResult.percent.isnot(None)))
    allowed = _branch_scope_ids(db, user, branch_id)
    if allowed:
        q = q.filter(models.Group.branch_id.in_(allowed))
    rows = q.all()

    teachers = {t.id: t for t in db.query(models.Teacher).all()}
    branches = {b.id: b for b in db.query(models.Branch).all()}

    def agg(key_fn, label_fn):
        acc = {}
        for r, e, g in rows:
            k = key_fn(g)
            if k is None:
                continue
            d = acc.setdefault(k, {"sum": 0.0, "n": 0, "exams": set(),
                                   "students": set()})
            d["sum"] += r.percent
            d["n"] += 1
            d["exams"].add(e.id)
            d["students"].add(r.student_id)
        out = []
        for k, d in acc.items():
            avg = round(d["sum"] / d["n"], 1)
            band, band_label = ("good", "Standartga mos") \
                if avg >= roles.EXAM_STANDARD_PERCENT else ("behind", "Ortda")
            out.append({
                "key": k, "label": label_fn(k), "avg": avg,
                "results": d["n"], "exams": len(d["exams"]),
                "students": len(d["students"]),
                "band": band, "band_label": band_label,
            })
        out.sort(key=lambda x: -x["avg"])
        return out

    by_teacher = agg(lambda g: g.teacher_id,
                     lambda k: teachers[k].full_name if k in teachers else "—")
    by_group = agg(lambda g: g.id,
                   lambda k: next((g.name for _r, _e, g in rows if g.id == k), "—"))
    by_branch = agg(lambda g: g.branch_id,
                    lambda k: branches[k].name if k in branches else "—")

    behind = [g for g in by_group if g["band"] == "behind"]

    # O'quvchi progressi: birinchi va oxirgi natija farqi
    per_student = {}
    for r, e, g in rows:
        per_student.setdefault(r.student_id, []).append((e.date, r.percent))
    progress = []
    names = {s.id: s for s in db.query(models.Student).all()}
    for sid, lst in per_student.items():
        if len(lst) < 2:
            continue
        lst.sort(key=lambda x: x[0])
        first, last = lst[0][1], lst[-1][1]
        st = names.get(sid)
        progress.append({
            "student_id": sid,
            "full_name": st.full_name if st else "—",
            "group": st.group.name if st and st.group else None,
            "first": round(first, 1), "last": round(last, 1),
            "change": round(last - first, 1),
            "exams": len(lst),
            "avg": round(sum(x[1] for x in lst) / len(lst), 1),
        })
    progress.sort(key=lambda x: x["change"])

    # Sertifikatga tavsiya: o'rtachasi yuqori va kamida 2 ta imtihon
    recommend = [p for p in progress
                 if p["avg"] >= roles.CERTIFICATE_RECOMMEND_PERCENT
                 and p["exams"] >= 2]
    recommend.sort(key=lambda x: -x["avg"])

    # Qayta imtihon tavsiyasi: oxirgi natijasi past
    retake = [{"student_id": sid,
               "full_name": names[sid].full_name if sid in names else "—",
               "group": names[sid].group.name
                        if sid in names and names[sid].group else None,
               "percent": round(sorted(lst, key=lambda x: x[0])[-1][1], 1)}
              for sid, lst in per_student.items()
              if sorted(lst, key=lambda x: x[0])[-1][1] < roles.EXAM_RETAKE_BELOW]
    retake.sort(key=lambda x: x["percent"])

    all_avg = (round(sum(r.percent for r, _e, _g in rows) / len(rows), 1)
               if rows else None)
    return {
        "months": months,
        "standard": roles.EXAM_STANDARD_PERCENT,
        "total_results": len(rows),
        "avg": all_avg,
        "by_teacher": by_teacher,
        "by_group": by_group,
        "by_branch": by_branch,
        "behind": behind,
        "progress": progress,
        "recommend_certificate": recommend[:50],
        "recommend_retake": retake[:50],
    }


# =====================================================================
#  SUPPORT TEACHER MODULI
# =====================================================================
@app.get("/api/support/assignments")
def support_assignments(
    user_id: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.SUPPORT_ACCESS)),
):
    q = db.query(models.SupportAssignment)
    # Support teacher faqat O'ZIGA biriktirilganini ko'radi.
    if user.role == roles.SUPPORT_TEACHER:
        q = q.filter(models.SupportAssignment.user_id == user.id)
    elif user_id:
        q = q.filter(models.SupportAssignment.user_id == user_id)
    return [{
        "id": a.id, "user_id": a.user_id,
        "user": a.user.full_name if a.user else None,
        "group_id": a.group_id,
        "group": a.group.name if a.group else None,
        "student_id": a.student_id,
        "student": a.student.full_name if a.student else None,
        "note": a.note,
    } for a in q.all()]


@app.post("/api/support/assignments")
def add_assignment(
    payload: schemas.SupportAssignmentCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.ACADEMIC_ACCESS)),
):
    if not payload.group_id and not payload.student_id:
        raise HTTPException(400, "Guruh yoki o'quvchi tanlang")
    a = models.SupportAssignment(**payload.model_dump(),
                                 created_by=user.full_name)
    db.add(a); db.commit(); db.refresh(a)
    return {"id": a.id}


@app.delete("/api/support/assignments/{aid}")
def delete_assignment(
    aid: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.ACADEMIC_ACCESS)),
):
    a = db.query(models.SupportAssignment).get(aid)
    if not a:
        raise HTTPException(404, "Topilmadi")
    db.delete(a); db.commit()
    return {"ok": True}


def _student_attendance_stats(db: Session, sid: int, since: date) -> dict:
    rows = (db.query(models.Attendance, models.Lesson)
            .join(models.Lesson, models.Attendance.lesson_id == models.Lesson.id)
            .filter(models.Attendance.student_id == sid,
                    models.Lesson.date >= since).all())
    marked = len(rows)
    present = sum(1 for a, _l in rows if a.present)
    return {
        "marked": marked, "present": present, "absent": marked - present,
        "percent": round(present / marked * 100, 1) if marked else None,
    }


@app.get("/api/support/panel")
def support_panel(
    user_id: int | None = None,
    months: int = 3,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.SUPPORT_ACCESS)),
):
    """Support teacher paneli: biriktirilgan guruhlar va o'quvchilar,
    davomat va uy vazifasi muammolari, ishlash rejasi va natija."""
    since = date.today() - timedelta(days=int(max(1, months) * 30.44))

    aq = db.query(models.SupportAssignment)
    target_id = user.id if user.role == roles.SUPPORT_TEACHER else (user_id or None)
    if target_id:
        aq = aq.filter(models.SupportAssignment.user_id == target_id)
    assigns = aq.all()

    group_ids = {a.group_id for a in assigns if a.group_id}
    direct_ids = {a.student_id for a in assigns if a.student_id}

    sq = db.query(models.Student).filter(
        models.Student.status.in_(["active", "trial"]))
    if group_ids or direct_ids:
        sq = sq.filter(
            (models.Student.group_id.in_(group_ids or [-1]))
            | (models.Student.id.in_(direct_ids or [-1])))
    elif user.role == roles.SUPPORT_TEACHER:
        sq = sq.filter(models.Student.id == -1)   # hech narsa biriktirilmagan
    else:
        sq = scope_to_branch(sq, models.Student, user)
    students = sq.all()

    # Uy vazifasi muammosi - qo'lda qo'yilgan risk signali
    hw = {}
    if students:
        for f in (db.query(models.RiskFlag)
                  .filter(models.RiskFlag.student_id.in_([s.id for s in students]),
                          models.RiskFlag.signal == "no_homework",
                          models.RiskFlag.active == 1).all()):
            hw[f.student_id] = f.note or "belgilangan"

    plans = {}
    if students:
        for p in (db.query(models.SupportPlan)
                  .filter(models.SupportPlan.student_id.in_(
                      [s.id for s in students])).all()):
            plans.setdefault(p.student_id, []).append(p)

    rows, att_problem, hw_problem = [], 0, 0
    for s in students:
        att = _student_attendance_stats(db, s.id, since)
        bad_att = (att["percent"] is not None
                   and att["percent"] < roles.SUPPORT_ATTENDANCE_THRESHOLD)
        bad_hw = s.id in hw
        if bad_att:
            att_problem += 1
        if bad_hw:
            hw_problem += 1
        open_plans = [p for p in plans.get(s.id, []) if p.status == "open"]
        rows.append({
            "student_id": s.id, "public_id": s.public_id,
            "full_name": s.full_name, "status": s.status,
            "group_id": s.group_id,
            "group": s.group.name if s.group else None,
            "phone": s.phone, "parent_phone": s.parent_phone,
            "attendance": att,
            "attendance_problem": bad_att,
            "homework_problem": bad_hw,
            "homework_note": hw.get(s.id),
            "open_plans": [{"id": p.id, "issue": p.issue,
                            "issue_label": roles.SUPPORT_ISSUE_LABELS.get(
                                p.issue, p.issue),
                            "plan": p.plan,
                            "due_date": p.due_date.isoformat()
                                        if p.due_date else None}
                           for p in open_plans],
        })
    # Muammoliligi bo'yicha tartib: eng past davomat yuqorida
    rows.sort(key=lambda r: (r["attendance"]["percent"] is None,
                             r["attendance"]["percent"] or 0))

    # Retention natijasi: biriktirilgan o'quvchilardan qanchasi qoldi
    all_ever = list(students)
    if group_ids:
        all_ever = (db.query(models.Student)
                    .filter(models.Student.group_id.in_(group_ids)).all())
    left = [s for s in all_ever if s.status == "archived"]
    stayed = [s for s in all_ever if s.status in ("active", "trial")]

    done_plans = sum(1 for lst in plans.values()
                     for p in lst if p.status == "done")
    total_plans = sum(len(lst) for lst in plans.values())

    return {
        "user_id": target_id,
        "groups": [{"id": g.id, "name": g.name,
                    "teacher": g.teacher.full_name if g.teacher else None,
                    "students": sum(1 for s in students if s.group_id == g.id)}
                   for g in db.query(models.Group)
                   .filter(models.Group.id.in_(group_ids or [-1])).all()],
        "students": rows,
        "summary": {
            "students": len(rows),
            "attendance_problem": att_problem,
            "homework_problem": hw_problem,
            "threshold": roles.SUPPORT_ATTENDANCE_THRESHOLD,
            "open_plans": sum(len(r["open_plans"]) for r in rows),
            "done_plans": done_plans,
            "plan_success": round(done_plans / total_plans * 100, 1)
                            if total_plans else None,
            "retention": round(len(stayed) / len(all_ever) * 100, 1)
                         if all_ever else None,
            "stayed": len(stayed), "left": len(left),
        },
    }


@app.get("/api/support/plans")
def list_plans(
    student_id: int | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.SUPPORT_ACCESS)),
):
    q = db.query(models.SupportPlan)
    if student_id:
        q = q.filter(models.SupportPlan.student_id == student_id)
    if status:
        q = q.filter(models.SupportPlan.status == status)
    if user.role == roles.SUPPORT_TEACHER:
        q = q.filter(models.SupportPlan.user_id == user.id)
    today = date.today()
    return [{
        "id": p.id, "student_id": p.student_id,
        "student": p.student.full_name if p.student else None,
        "user": p.user.full_name if p.user else None,
        "issue": p.issue,
        "issue_label": roles.SUPPORT_ISSUE_LABELS.get(p.issue, p.issue),
        "plan": p.plan,
        "due_date": p.due_date.isoformat() if p.due_date else None,
        "overdue": bool(p.due_date and p.status == "open" and p.due_date < today),
        "status": p.status, "result": p.result,
        "created_at": p.created_at.isoformat() if p.created_at else None,
    } for p in q.order_by(models.SupportPlan.due_date).all()]


@app.post("/api/support/plans")
def create_plan(
    payload: schemas.SupportPlanCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.SUPPORT_ACCESS)),
):
    data = payload.model_dump()
    data["user_id"] = data.get("user_id") or user.id
    p = models.SupportPlan(**data, created_by=user.full_name)
    db.add(p); db.commit(); db.refresh(p)
    audit.log(db, user, entity="student", action="update",
              entity_id=p.student_id, field="support_plan",
              new_value=p.plan[:80], commit=True)
    return {"id": p.id}


@app.put("/api/support/plans/{pid}")
def update_plan(
    pid: int,
    payload: schemas.SupportPlanUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.SUPPORT_ACCESS)),
):
    p = db.query(models.SupportPlan).get(pid)
    if not p:
        raise HTTPException(404, "Reja topilmadi")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(p, k, v)
    p.done_at = date.today() if p.status in ("done", "failed") else None
    db.commit()
    return {"ok": True}


@app.delete("/api/support/plans/{pid}")
def delete_plan(
    pid: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.ACADEMIC_ACCESS)),
):
    p = db.query(models.SupportPlan).get(pid)
    if not p:
        raise HTTPException(404, "Reja topilmadi")
    db.delete(p); db.commit()
    return {"ok": True}


# =====================================================================
#  FAYL BIRIKTIRISH  (rasm, sertifikat, hujjat)
# =====================================================================
@app.get("/api/attachments")
def list_attachments(
    entity: str,
    entity_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_STAFF, *roles.HR_ACCESS)),
):
    """Fayl ro'yxati. Ma'lumot og'ir bo'lgani uchun ro'yxatda faqat
    metama'lumot qaytadi - faylning o'zi alohida so'raladi."""
    rows = (db.query(models.Attachment)
            .filter(models.Attachment.entity == entity,
                    models.Attachment.entity_id == entity_id)
            .order_by(models.Attachment.created_at.desc()).all())
    return [{
        "id": a.id, "kind": a.kind,
        "kind_label": roles.ATTACHMENT_KIND_LABELS.get(a.kind, a.kind),
        "filename": a.filename, "mime": a.mime, "size": a.size,
        "note": a.note, "created_by": a.created_by,
        "created_at": a.created_at.isoformat() if a.created_at else None,
        "is_image": bool(a.mime and a.mime.startswith("image/")),
    } for a in rows]


@app.get("/api/attachments/{aid}")
def get_attachment(
    aid: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_STAFF, *roles.HR_ACCESS)),
):
    """Faylning o'zi - base64 ko'rinishida."""
    a = db.query(models.Attachment).get(aid)
    if not a:
        raise HTTPException(404, "Fayl topilmadi")
    return {"id": a.id, "filename": a.filename, "mime": a.mime,
            "size": a.size, "kind": a.kind, "data": a.data}


@app.post("/api/attachments")
def upload_attachment(
    payload: schemas.AttachmentCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_STAFF, *roles.HR_ACCESS)),
):
    import base64
    raw = payload.data
    # "data:image/png;base64,...." ko'rinishida kelsa - kesib olamiz
    if "," in raw and raw.strip().startswith("data:"):
        raw = raw.split(",", 1)[1]
    try:
        size = len(base64.b64decode(raw, validate=False))
    except Exception:
        raise HTTPException(400, "Fayl o'qib bo'lmadi")
    if size > roles.ATTACHMENT_MAX_BYTES:
        mb = roles.ATTACHMENT_MAX_BYTES // (1024 * 1024)
        raise HTTPException(400, f"Fayl juda katta — {mb} MB dan oshmasin")
    if payload.kind not in roles.ATTACHMENT_KIND_LABELS:
        raise HTTPException(400, "Noma'lum fayl turi")

    a = models.Attachment(
        entity=payload.entity, entity_id=payload.entity_id,
        kind=payload.kind, filename=payload.filename, mime=payload.mime,
        size=size, data=raw, note=payload.note, created_by=user.full_name)
    db.add(a); db.commit(); db.refresh(a)
    audit.log(db, user, entity=payload.entity, action="update",
              entity_id=payload.entity_id, field="attachment",
              new_value=payload.filename, commit=True)
    return {"id": a.id, "size": size}


@app.delete("/api/attachments/{aid}")
def delete_attachment(
    aid: int,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_STAFF, *roles.HR_ACCESS)),
):
    a = db.query(models.Attachment).get(aid)
    if not a:
        raise HTTPException(404, "Fayl topilmadi")
    audit.log(db, user, entity=a.entity, action="update", entity_id=a.entity_id,
              field="attachment", old_value=a.filename,
              note="Fayl o'chirildi")
    db.delete(a); db.commit()
    return {"ok": True}
