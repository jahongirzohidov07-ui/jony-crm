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


def _ensure_new_columns():
    """create_all() faqat yo'q jadvalni yaratadi - mavjud jadvalga yangi
    ustun qo'shmaydi. Shuning uchun keyin qo'shilgan ustunlarni shu yerda
    qo'lda qo'shamiz. Har safar ishga tushganda bajariladi, lekin ustun
    allaqachon bo'lsa xatolik e'tiborsiz qoldiriladi - ya'ni takror
    ishlatish xavfsiz."""
    from sqlalchemy import text

    statements = [
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


_ensure_new_columns()

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


def scope_to_branch(query, model, user: models.User):
    """Administrator/HR/SMM (branch_id is None on their account) see every
    branch. Everyone else only sees their own branch's records."""
    if user.role in tuple(roles.ORG_WIDE_ROLES):
        return query
    if user.branch_id:
        return query.filter(model.branch_id == user.branch_id)
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

    balances = [(s.id, student_balance(db, s.id)) for s in all_students]
    total_debt = sum(b for _, b in balances if b < 0)
    debtor_count = sum(1 for _, b in balances if b < 0)

    return schemas.DashboardStats(
        active_students=active,
        trial_students=trial,
        frozen_students=frozen,
        total_groups=groups,
        total_teachers=teachers,
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
    q = scope_to_branch(db.query(models.Lead), models.Lead, user)
    if stage:
        q = q.filter(models.Lead.stage == stage)
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
        created_by=user.full_name,
    )
    db.add(exp)
    db.commit()
    db.refresh(exp)
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


def _group_lessons_in_month(db: Session, group_id: int, year: int, month: int):
    start, end = billing.month_bounds(year, month)
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
        lessons=[schemas.GridLesson(id=ls.id, date=ls.date) for ls in lessons],
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
    db.commit()
    return {"ok": True, "saved": len(payload.marks)}


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
        lessons=[schemas.GridLesson(id=ls.id, date=ls.date) for ls in lessons],
        marks=marks,
    )


@app.put("/api/lessons/{lesson_id}/grades")
def save_grades(
    lesson_id: int,
    payload: schemas.GradeBulk,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.TEACHING_ACCESS)),
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

    exam = models.Exam(
        group_id=group_id, kind=payload.kind,
        unit_no=payload.unit_no if payload.kind == "unit" else None,
        title=payload.title, date=payload.date,
        max_score=payload.max_score if payload.kind != "mock" else None,
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
    hisoblanadi, coin ham qoidaga qarab avtomat beriladi."""
    exam = _exam_in_scope(db, exam_id, user)
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


def _income_by_method(db: Session, user, start: date, end: date) -> dict:
    """Bir oraliqdagi haqiqiy tushumni to'lov usuli kesimida qaytaradi."""
    q = db.query(models.Payment).join(models.Student).filter(
        models.Payment.kind == "payment",
        models.Payment.created_at >= datetime.combine(start, datetime.min.time()),
        models.Payment.created_at <= datetime.combine(end, datetime.max.time()),
    )
    if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
        q = q.filter(models.Student.branch_id == user.branch_id)

    out = {m: 0.0 for m in roles.PAYMENT_METHODS}
    for p in q.all():
        # Usul belgilanmasdan oldin kiritilgan eski to'lovlar naqd deb
        # hisoblanadi - aks holda ular hisobotdan tushib qolardi.
        out[p.method if p.method in out else "cash"] += p.amount
    return out


def _expenses_total(db: Session, user, start: date, end: date) -> tuple:
    """(jami, tur bo'yicha lug'at) qaytaradi."""
    q = scope_to_branch(db.query(models.Expense), models.Expense, user).filter(
        models.Expense.date >= start, models.Expense.date <= end
    )
    by_cat, total = {}, 0.0
    for e in q.all():
        by_cat[e.category] = by_cat.get(e.category, 0) + e.amount
        total += e.amount
    return total, by_cat


def _payroll_total(db: Session, user, period: str) -> float:
    """Ustozlar ish haqi - TeacherPayout jadvalidan AVTOMATIK olinadi.
    Uni Xarajatlar bo'limiga qo'lda kiritish shart emas (va kiritilmasligi
    ham kerak - aks holda ikki marta hisoblanadi)."""
    q = db.query(models.TeacherPayout).filter(models.TeacherPayout.period == period)
    if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
        q = q.join(models.Group).filter(models.Group.branch_id == user.branch_id)
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
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FINANCE_ACCESS)),
):
    """Bir oylik foyda-zarar. Chiqim = qo'lda kiritilgan xarajatlar +
    avtomatik hisoblangan ustozlar ish haqi."""
    start, end = billing.month_bounds(year, month)
    period = _period_key(year, month)

    methods = _income_by_method(db, user, start, end)
    income = sum(methods.values())
    exp_total, by_cat = _expenses_total(db, user, start, end)
    payroll = _payroll_total(db, user, period)
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


@app.post("/api/groups", response_model=schemas.GroupOut)
def create_group(
    payload: schemas.GroupCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FULL_ACCESS)),
):
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
    payload: schemas.GroupCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role(*roles.FULL_ACCESS)),
):
    group = db.query(models.Group).get(group_id)
    if not group:
        raise HTTPException(404, "Guruh topilmadi")
    for k, v in payload.model_dump().items():
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
    for k, v in payload.model_dump(exclude_unset=True).items():
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
    return (
        billing.held_lessons_query(db, group.id, start, end)
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
    existing = (
        db.query(models.Lesson)
        .filter(models.Lesson.group_id == group.id, models.Lesson.date == payload.date)
        .first()
    )
    if existing:
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
